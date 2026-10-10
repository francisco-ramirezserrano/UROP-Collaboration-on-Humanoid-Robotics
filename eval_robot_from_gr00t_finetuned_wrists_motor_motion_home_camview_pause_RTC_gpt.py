#!/usr/bin/env python3
"""
motor_motion.py

GR00T motor deployment with Async Real-Time Chunking (RTC) support.
Includes Millisecond Timing Diagnostics and fully asynchronous camera processing.
"""

import sys
import time
import threading
import select
import termios
import tty
import queue
import concurrent.futures
from typing import Any, Dict, Tuple, Optional

import numpy as np
import cv2
from multiprocessing.sharedctypes import SynchronizedArray

from lerobot.configs import parser
from gr00t.policy.server_client import PolicyClient

from unitree_lerobot.eval_robot.make_robot_wrists import (
    setup_image_client,
    setup_robot_interface,
    process_images_and_observations,
)
from unitree_lerobot.eval_robot.utils.utils import EvalRealConfig, to_list, to_scalar

import logging_mp
logging_mp.basic_config(level=logging_mp.INFO)
logger_mp = logging_mp.get_logger(__name__)

# ==========================
# ALIGNMENT CONSTANTS
# ==========================
HOME_POSE_ARM = np.array([
    0.16115,  0.05523, -0.15136, -0.06010,  0.32241, -0.28107,  0.17412, 
    0.03867, -0.06847,  0.02136,  0.19261, -0.03371, -0.46092,  0.08771  
], dtype=np.float32)

HOME_POSE_HANDS = np.array([
   -1.03133,  0.79071,  0.00086, -0.14362,  0.00012, -0.08944,  0.00012, 
   -1.00288, -0.72569, -0.00033, -0.00100, -0.00100, -0.00100, -0.00100  
], dtype=np.float32)

HOME_MOVE_DURATION = 3.0 

# ==========================
# DEPLOYMENT CONSTANTS
# ==========================
MAX_CHUNKS = -1  
ENABLE_HANDS = True
MODEL_H, MODEL_W = 480, 640

POLICY_HOST = "127.0.0.1"
POLICY_PORT = 5555
LANG_INSTRUCTION = "pick up the pear and place it on the plate"

USE_EMA = True
EMA_ALPHA_ARM = 0.25
EMA_ALPHA_HAND = 0.25

WATCHDOG_ENABLE = True
WATCHDOG_ARM_MAX_ABS = 0.80
WATCHDOG_HAND_MAX_ABS = 2.00

MOTION_TRY_SWITCHER = True
KEEP_BASE_STATIONARY = True
BASE_ZERO_CMD_HZ = 5.0

# ==========================
# RTC DEPLOYMENT CONSTANTS
# ==========================
PREDICT_HORIZON = 32
INFERENCE_RTC_OVERLAP_STEPS = 16
EXECUTION_STEPS = PREDICT_HORIZON - INFERENCE_RTC_OVERLAP_STEPS
ASYNC_DISPATCH_OFFSET = 6 
BOUNDARY_BLEND_STEPS = 4

def _bgr_to_rgb(img_bgr: np.ndarray) -> np.ndarray:
    return img_bgr[..., ::-1].copy()

def _resize_hw(img: np.ndarray, h: int, w: int) -> np.ndarray:
    if img is None: return None
    current_h, current_w = img.shape[:2]
    if current_h == h and current_w == w: return img
    if current_h == 720 and current_w == 1280:
        start_x = (1280 - 960) // 2
        cropped = img[:, start_x:start_x+960]
        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_AREA)
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)

def _read_dex3_state(ee_shared_mem: Dict[str, Any], ee_dof: int) -> Tuple[np.ndarray, np.ndarray]:
    if not ee_shared_mem or "state" not in ee_shared_mem:
        return np.zeros((ee_dof,), np.float32), np.zeros((ee_dof,), np.float32)
    with ee_shared_mem["lock"]:
        full = np.array(ee_shared_mem["state"][:], dtype=np.float32)
    if full.size < 2 * ee_dof: return np.zeros((ee_dof,), np.float32), np.zeros((ee_dof,), np.float32)
    return full[:ee_dof], full[ee_dof: 2 * ee_dof]

def _write_dex3_cmd(ee_shared_mem: Dict[str, Any], left_cmd: np.ndarray, right_cmd: np.ndarray):
    if not ee_shared_mem: return
    if isinstance(ee_shared_mem["left"], SynchronizedArray):
        ee_shared_mem["left"][:] = to_list(left_cmd)
        ee_shared_mem["right"][:] = to_list(right_cmd)
    elif hasattr(ee_shared_mem["left"], "value") and hasattr(ee_shared_mem["right"], "value"):
        ee_shared_mem["left"].value = to_scalar(left_cmd)
        ee_shared_mem["right"].value = to_scalar(right_cmd)

class KeyWatcher:
    def __init__(self):
        self.armed = threading.Event()
        self.home = threading.Event()
        self.stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._fd = None
        self._old = None
        self._enabled = False

    def start(self):
        if not sys.stdin.isatty():
            logger_mp.warning("[KeyWatcher] stdin is not a TTY; auto-arming. Use Ctrl+C to stop.")
            self.armed.set()
            self._enabled = False
            return
        self._fd = sys.stdin.fileno()
        self._old = termios.tcgetattr(self._fd)
        tty.setcbreak(self._fd)
        self._enabled = True
        self._thread.start()

    def _run(self):
        try:
            while not self.stop.is_set():
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not r: continue
                ch = sys.stdin.read(1)
                if not ch: continue
                c = ch.lower()
                
                if c == "r":
                    if not self.armed.is_set():
                        self.armed.set()
                        logger_mp.info("🟢 ARMED (pressed 'r'). Starting policy loop.")
                elif c == "p":
                    if self.armed.is_set():
                        self.armed.clear()
                        logger_mp.info("⏸️ PAUSED (pressed 'p'). Inference stopped.")
                elif c == "h":
                    if not self.home.is_set() and not self.armed.is_set():
                        self.home.set()
                        logger_mp.info("🔵 HOMING (pressed 'h'). Moving to start pose.")
                elif c == "q":
                    logger_mp.info("🔴 STOP (pressed 'q').")
                    self.stop.set()
                    break
        except Exception as e:
            logger_mp.info(f"[KeyWatcher] Exception: {e}")
            self.stop.set()

    def stop_and_restore(self):
        try:
            self.stop.set()
            if self._enabled and self._thread.is_alive():
                self._thread.join(timeout=1.0)
        finally:
            if self._enabled and self._fd is not None and self._old is not None:
                try: termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old)
                except Exception: pass

class DashboardViewer:
    def __init__(self):
        self.q = queue.Queue(maxsize=2)
        self.running = True
        self.thread = threading.Thread(target=self._view_loop, daemon=True)
        self.thread.start()

    def update(self, images_dict):
        if not self.q.full(): self.q.put(images_dict)

    def _add_label(self, img, text):
        if img is None: return np.zeros((MODEL_H, MODEL_W, 3), dtype=np.uint8)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        labeled = img_bgr.copy()
        cv2.rectangle(labeled, (0, 0), (MODEL_W, 40), (0, 0, 0), -1)
        cv2.putText(labeled, text, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        return labeled

    def _view_loop(self):
        cv2.namedWindow("GR00T Live Dashboard", cv2.WINDOW_NORMAL)
        while self.running:
            try:
                images = self.q.get(timeout=0.1)
                left_high = self._add_label(images.get("cam_left_high"), "cam_left_high")
                right_high = self._add_label(images.get("cam_right_high"), "cam_right_high")
                left_wrist = self._add_label(images.get("cam_left_wrist"), "cam_left_wrist")
                right_wrist = self._add_label(images.get("cam_right_wrist"), "cam_right_wrist")
                
                top_row = np.hstack((left_high, right_high))
                bottom_row = np.hstack((left_wrist, right_wrist))
                grid = np.vstack((top_row, bottom_row))
                
                display = cv2.resize(grid, (0, 0), fx=0.7, fy=0.7)
                cv2.imshow("GR00T Live Dashboard", display)
                cv2.waitKey(1)
            except queue.Empty: continue
            except Exception as e: logger_mp.warning(f"Dashboard error: {e}")
        cv2.destroyAllWindows()

    def stop(self):
        self.running = False
        if self.thread.is_alive(): self.thread.join(timeout=1.0)

def _cleanup_image_info(image_info: Dict[str, Any]):
    for c in image_info.get("clients", []):
        try: c.running = False
        except Exception: pass
    for t in image_info.get("threads", []):
        try:
            if t.is_alive(): t.join(timeout=1.0)
        except Exception: pass
    for shm in image_info.get("shm_resources", []):
        try: shm.close()
        except Exception: pass
        try: shm.unlink()
        except Exception: pass

def _maybe_setup_motion_mode(cfg: EvalRealConfig) -> Tuple[Optional[Any], Optional[Any]]:
    if not MOTION_TRY_SWITCHER: return None, None
    motion = bool(getattr(cfg, "motion", False))

    try:
        xr_path = "/media/data_18tb/workspace/xr_teleoperate"
        if xr_path not in sys.path: sys.path.append(xr_path)
    except Exception: pass

    try: from teleop.utils.motion_switcher import MotionSwitcher, LocoClientWrapper  
    except Exception as e:
        return None, None

    motion_switcher, loco = None, None
    try: motion_switcher = MotionSwitcher()
    except Exception as e: pass

    if motion_switcher is not None:
        if motion:
            try: motion_switcher.Exit_Debug_Mode()
            except Exception: pass
        else:
            try: motion_switcher.Enter_Debug_Mode()
            except Exception: pass

    if motion:
        try: loco = LocoClientWrapper()
        except Exception: pass

    return motion_switcher, loco

def _maybe_base_zero(loco: Optional[Any], now: float, last_sent: float) -> float:
    if loco is None or not KEEP_BASE_STATIONARY: return last_sent
    period = 1.0 / float(BASE_ZERO_CMD_HZ) if BASE_ZERO_CMD_HZ > 0 else 0.0
    if period <= 0 or (now - last_sent) < period: return last_sent
    try:
        loco.Move(0.0, 0.0, 0.0)
        return now
    except Exception:
        try:
            loco.Damp()
            return now
        except Exception: return last_sent

def go_to_home_pose(arm_ctrl, arm_ik, ee_shared_mem, ee_dof, target_arm, target_hands, duration, arm_dof, keys):
    logger_mp.info(f"Starting smooth interpolation to Home Pose over {duration}s...")
    start_arm_q = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float32).reshape(-1)[:arm_dof]
    
    if ee_dof > 0 and ee_shared_mem:
        lh_cur, rh_cur = _read_dex3_state(ee_shared_mem, ee_dof)
        start_hands_q = np.concatenate([lh_cur, rh_cur])
    else: start_hands_q = target_hands 
        
    hz = 50.0
    steps = int(duration * hz)
    for step in range(steps):
        if keys.stop.is_set() or keys.armed.is_set():
            logger_mp.warning("🛑 Homing aborted by stop/arm signal!")
            break
            
        alpha = step / float(steps)
        current_arm_target = start_arm_q + alpha * (target_arm - start_arm_q)
        tau = arm_ik.solve_tau(current_arm_target)
        arm_ctrl.ctrl_dual_arm(current_arm_target, tau)
        
        if ee_dof > 0 and ee_shared_mem:
            current_hands_target = start_hands_q + alpha * (target_hands - start_hands_q)
            _write_dex3_cmd(ee_shared_mem, current_hands_target[:ee_dof], current_hands_target[ee_dof:])
        time.sleep(1.0 / hz)
        
    logger_mp.info("✅ Home Pose reached.")


@parser.wrap()
def motor_motion(cfg: EvalRealConfig):
    image_info = setup_image_client(cfg)
    robot = setup_robot_interface(cfg)
    motion_switcher, loco = _maybe_setup_motion_mode(cfg)

    arm_ctrl = robot["arm_ctrl"]
    arm_ik = robot["arm_ik"]
    ee_shared_mem = robot.get("ee_shared_mem", {})
    arm_dof = int(robot["arm_dof"])
    ee_dof = int(robot.get("ee_dof", 0))
    expected_dim = arm_dof + (2 * ee_dof if cfg.ee else 0)

    p = PolicyClient(host=POLICY_HOST, port=POLICY_PORT)
    assert p.ping(), f"GR00T server not reachable on {POLICY_HOST}:{POLICY_PORT}"
    mc = p.get_modality_config()

    skey = mc["state"].modality_keys[0]
    lkey = mc["language"].modality_keys[0]
    akey = mc["action"].modality_keys[0]

    keys = KeyWatcher()
    keys.start()
    dashboard = DashboardViewer()
    time.sleep(0.8)

    logger_mp.info("🟡 SAFE MODE: press 'h' to HOME, 'r' to RUN, 'p' to PAUSE, 'q' to STOP.")

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = None
    predicted_action = None

    prev_arm_cmd = prev_lh_cmd = prev_rh_cmd = None
    
    period = 1.0 / float(cfg.frequency)
    chunks_done = 0
    last_base_cmd_t = 0.0

    # ---------------------------------------------------------
    # BACKGROUND TASK: Image capture + Processing + Inference
    # ---------------------------------------------------------
    def background_infer_task(prev_action=None):
        t_start_cap = time.perf_counter()
        
        obs_dict, current_arm_q = process_images_and_observations(image_info, arm_ctrl)
        video_payload = {}
        raw_dashboard_images = {} 
        
        for cam_key in mc["video"].modality_keys:
            full_key = f"observation.images.{cam_key}"
            if full_key in obs_dict and obs_dict[full_key] is not None:
                img_tensor = obs_dict[full_key]
                img = img_tensor.numpy() if hasattr(img_tensor, "numpy") else np.asarray(img_tensor)
                img = np.asarray(img, dtype=np.uint8)
                processed_img = _bgr_to_rgb(_resize_hw(img, MODEL_H, MODEL_W))
                video_payload[cam_key] = processed_img[None, None]
                raw_dashboard_images[cam_key] = processed_img
            else:
                video_payload[cam_key] = np.zeros((1, 1, MODEL_H, MODEL_W, 3), dtype=np.uint8)
                raw_dashboard_images[cam_key] = np.zeros((MODEL_H, MODEL_W, 3), dtype=np.uint8)

        dashboard.update(raw_dashboard_images)

        proprio = np.zeros((expected_dim,), dtype=np.float32)
        arm_q = np.asarray(current_arm_q, dtype=np.float32).reshape(-1)[:arm_dof]
        proprio[:arm_dof] = arm_q

        if cfg.ee and ee_dof > 0:
            lh_state, rh_state = _read_dex3_state(ee_shared_mem, ee_dof)
            proprio[arm_dof:arm_dof + ee_dof] = lh_state
            proprio[arm_dof + ee_dof:arm_dof + 2 * ee_dof] = rh_state

        obs = {
            "video": video_payload,
            "state": {skey: proprio[None, None]},
            "language": {lkey: [[LANG_INSTRUCTION]]},
        }

        if prev_action is not None and chunks_done > 0:
            original_shape = prev_action[akey].shape
            pad_action = np.zeros(original_shape, dtype=prev_action[akey].dtype)
            valid_action = prev_action[akey][:, PREDICT_HORIZON - INFERENCE_RTC_OVERLAP_STEPS:PREDICT_HORIZON, :]
            pad_action[:, :INFERENCE_RTC_OVERLAP_STEPS, :] = valid_action
            obs['action'] = {akey: pad_action}
            
        t_end_cap = time.perf_counter()
        
        t_start_inf = time.perf_counter()
        chunk, _ = p.get_action(obs)
        t_end_inf = time.perf_counter()
        
        return chunk, (t_end_cap - t_start_cap), (t_end_inf - t_start_inf)

    try:
        while not keys.stop.is_set() and (MAX_CHUNKS < 0 or chunks_done < MAX_CHUNKS):
            if keys.home.is_set() and not keys.armed.is_set():
                if cfg.send_real_robot:
                    go_to_home_pose(arm_ctrl, arm_ik, ee_shared_mem, ee_dof, HOME_POSE_ARM, HOME_POSE_HANDS, HOME_MOVE_DURATION, arm_dof, keys)
                keys.home.clear() 
            
            if not keys.armed.is_set():
                # Just pump the dashboard to keep it alive
                obs_dict, _ = process_images_and_observations(image_info, arm_ctrl)
                prev_arm_cmd = prev_lh_cmd = prev_rh_cmd = None
                predicted_action = None 
                future = None
                last_base_cmd_t = _maybe_base_zero(loco, time.time(), last_base_cmd_t)
                time.sleep(0.05)
                continue

            last_base_cmd_t = _maybe_base_zero(loco, time.time(), last_base_cmd_t)

            # ==========================
            # ASYNC INFERENCE RESOLUTION
            # ==========================
            if future is None:
                chunk, t_cap, t_inf = background_infer_task(predicted_action)
                predicted_action = chunk
                wait_time = 0.0
            else:
                wait_start = time.perf_counter()
                chunk, t_cap, t_inf = future.result()
                wait_time = time.perf_counter() - wait_start
                predicted_action = chunk

            ctrl = np.asarray(chunk[akey], dtype=np.float32)  
            exec_horizon = min(int(ctrl.shape[1]), EXECUTION_STEPS)
            chunks_done += 1
            chunk_start_arm_anchor = prev_arm_cmd.copy() if prev_arm_cmd is not None else None
            chunk_start_lh_anchor = prev_lh_cmd.copy() if prev_lh_cmd is not None else None
            chunk_start_rh_anchor = prev_rh_cmd.copy() if prev_rh_cmd is not None else None
            # --- Control Execution Loop ---
            step_times = []
            next_t = time.perf_counter()
            
            for t in range(exec_horizon):
                step_start = time.perf_counter()
                
                if keys.stop.is_set() or not keys.armed.is_set():
                    break
                    
                # ==========================
                # ASYNC INFERENCE DISPATCH
                # ==========================
                if t == exec_horizon - ASYNC_DISPATCH_OFFSET:
                    future = executor.submit(background_infer_task, predicted_action)

                last_base_cmd_t = _maybe_base_zero(loco, time.time(), last_base_cmd_t)
                u = ctrl[0, t]
                current_arm_q = np.asarray(arm_ctrl.get_current_dual_arm_q(), dtype=np.float32).reshape(-1)[:arm_dof]
                target_arm = u[:arm_dof].copy()

                if ENABLE_HANDS and cfg.ee and ee_dof > 0:
                    lh_target = u[arm_dof:arm_dof + ee_dof].copy()
                    rh_target = u[arm_dof + ee_dof:arm_dof + 2 * ee_dof].copy()
                    lh_cur, rh_cur = _read_dex3_state(ee_shared_mem, ee_dof)
                else:
                    lh_target = rh_target = lh_cur = rh_cur = None

                if WATCHDOG_ENABLE:
                    arm_delta = np.abs(target_arm - current_arm_q)
                    if float(arm_delta.max()) > WATCHDOG_ARM_MAX_ABS:
                        logger_mp.error(f"🛑 WATCHDOG: arm delta too large max={float(arm_delta.max()):.3f}")
                        keys.stop.set()
                        break

		if USE_EMA and prev_arm_cmd is not None:
		    arm_cmd = (1.0 - EMA_ALPHA_ARM) * prev_arm_cmd + EMA_ALPHA_ARM * target_arm
		else:
		    arm_cmd = target_arm

		if lh_target is not None:
		    if USE_EMA and prev_lh_cmd is not None:
			lh_cmd = (1.0 - EMA_ALPHA_HAND) * prev_lh_cmd + EMA_ALPHA_HAND * lh_target
			rh_cmd = (1.0 - EMA_ALPHA_HAND) * prev_rh_cmd + EMA_ALPHA_HAND * rh_target
		    else:
			lh_cmd, rh_cmd = lh_target, rh_target
		else:
		    lh_cmd = rh_cmd = None

		# Extra smoothing only at chunk boundaries
		if chunks_done > 1 and t < BOUNDARY_BLEND_STEPS and chunk_start_arm_anchor is not None:
		    alpha = float(t + 1) / float(BOUNDARY_BLEND_STEPS)
		    arm_cmd = (1.0 - alpha) * chunk_start_arm_anchor + alpha * arm_cmd

		    if lh_cmd is not None and chunk_start_lh_anchor is not None and chunk_start_rh_anchor is not None:
			lh_cmd = (1.0 - alpha) * chunk_start_lh_anchor + alpha * lh_cmd
			rh_cmd = (1.0 - alpha) * chunk_start_rh_anchor + alpha * rh_cmd

		prev_arm_cmd = arm_cmd.copy()
		if lh_cmd is not None:
		    prev_lh_cmd, prev_rh_cmd = lh_cmd.copy(), rh_cmd.copy()

                if cfg.send_real_robot:
                    tau = arm_ik.solve_tau(arm_cmd)
                    arm_ctrl.ctrl_dual_arm(arm_cmd, tau)
                    if lh_cmd is not None:
                        _write_dex3_cmd(ee_shared_mem, lh_cmd, rh_cmd)

                next_t += period
                sleep_for = next_t - time.perf_counter()
                if sleep_for > 0: time.sleep(sleep_for)
                else: next_t = time.perf_counter()
                
                step_times.append(time.perf_counter() - step_start)

# ==========================
            # PRINT MILLISECOND DIAGNOSTICS
            # ==========================
            if len(step_times) > 0:
                avg_step = np.mean(step_times) * 1000
                max_step = np.max(step_times) * 1000
            else:
                avg_step, max_step = 0.0, 0.0

            logger_mp.info(
                f"\n📊 --- Chunk {chunks_done} Timings ---\n"
                f"   📸 Obs Capture (Async) : {t_cap*1000:.1f} ms\n"
                f"   🧠 GPU Inference (Async): {t_inf*1000:.1f} ms\n"
                f"   ⏳ GPU Wait (Starvation): {wait_time*1000:.1f} ms\n"
                f"   ⚙️ Avg Control Step    : {avg_step:.1f} ms (Target ~33.3 ms)\n"
                f"   ⚠️ Max Control Step    : {max_step:.1f} ms\n"
                "------------------------------------"
            )

    except KeyboardInterrupt:
        logger_mp.info("KeyboardInterrupt: stopping.")
    finally:
        executor.shutdown(wait=False)
        if loco is not None:
            try: loco.Damp()
            except Exception: pass
        
        dashboard.stop()
        keys.stop_and_restore()
        try: _cleanup_image_info(image_info)
        except Exception: pass
        logger_mp.info("🧹 Terminal restored. Exiting.")

if __name__ == "__main__":
    motor_motion()
