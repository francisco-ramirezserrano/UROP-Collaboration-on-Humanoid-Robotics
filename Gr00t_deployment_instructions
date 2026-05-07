Instructions to record/finetune/deploy GR00T VLA (N1.6):

step 0) turn on robot, ensure hands initialize properly, wait for debug mode, put robot in walking mode, ssh into robot, activate image, start-teleimager

step 1) record episodes:
conda activate tv
cd /media/data_18tb/workspace/xr_teleoperate/teleop
(tv) csail@drl-7:/media/data_18tb/workspace/xr_teleoperate/teleop$ python teleop_hand_and_arm.py   --input-mode hand   --display-mode immersive   --arm G1_29   --ee dex3   --img-server-ip 192.168.123.164   --network-interface enp6s0   --motion   --record   --task-dir "$DATASET_DIR"   --task-name "pick pear onto plate"   --task-goal "Pick up the pear and place it on the plate."   --task-desc "Teleoperated pear pick-and-place dataset on Unitree G1_29 with Dex3. Narrow-domain collection with fixed scene and consistent setup."   --task-steps "1. Start from home pose; 2. Reach to the pear; 3. Grasp the pear; 4. Lift the pear; 5. Move above the plate; 6. Place the pear on the plate; 7. Release; 8. Retract."

step 2) convert episodes:

cd /media/data_18tb/workspace/unitree_IL_lerobot
conda activate unitree_lerobot_gr00t

# Point to the directory so the script sees the 'pick_pear_onto_plate' folder
RAW_DATA_DIR="/media/data_18tb/workspace/xr_teleoperate/teleop/utils/data/pear_on_plate_v1_2026_03_21"
REPO_ID="unitreerobotics/pear_on_plate_v1"

# Run your ZED conversion script
python unitree_lerobot/utils/convert_ZED_to_lerobot.py \
    --raw-dir "$RAW_DATA_DIR" \
    --repo-id "$REPO_ID" \
    --robot-type "Unitree_G1_Dex3"
    
step 3) review episodes manually:

cd /media/data_18tb/workspace/unitree_IL_lerobot
conda activate unitree_lerobot_gr00t

lerobot-dataset-viz \
    --repo-id unitreerobotics/pear_on_plate_v1 \
    --episode-index 1
    
step 4) run diagnostics to check for missing frames, should be fine if waited to save fully before recording new episode:

cd ~
conda activate unitree_lerobot_gr00t

cat << 'EOF' > diagnostic_audit.py
import cv2
import os
import pandas as pd

base_dir = "/media/data_18tb/workspace/model_weights/lerobot/unitreerobotics/pear_on_plate_v1"
cameras = ["cam_left_high", "cam_right_high", "cam_left_wrist", "cam_right_wrist"]

print("-" * 50)
print("🎬 VIDEO CHUNK FRAME COUNTS")
print("-" * 50)

vid_frames = {}
for cam in cameras:
    path = f"{base_dir}/videos/observation.images.{cam}/chunk-000/file-000.mp4"
    if os.path.exists(path):
        cap = cv2.VideoCapture(path)
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        vid_frames[cam] = count
        cap.release()
        print(f"✅ {cam:<16}: {count} frames")
    else:
        print(f"❌ {cam:<16}: FILE NOT FOUND")

print("\n" + "-" * 50)
print("📊 METADATA (PARQUET) FRAME COUNT")
print("-" * 50)

pq_path = f"{base_dir}/data/train-00000-of-00001.parquet"
if os.path.exists(pq_path):
    df = pd.read_parquet(pq_path)
    pq_frames = len(df)
    print(f"✅ Parquet expects  : {pq_frames} frames")
else:
    print("❌ Parquet file missing!")

print("\n" + "-" * 50)
print("🎯 DIAGNOSIS")
print("-" * 50)

try:
    if all(count == pq_frames for count in vid_frames.values()):
        print("🎉 PERFECT MATCH! No dropped frames detected.")
        print("You are safe to purge your manually tagged episodes and train!")
    else:
        print("🚨 MISMATCH DETECTED! The SVT encoder dropped frames.")
except Exception:
    pass

EOF

python diagnostic_audit.py 2>/dev/null

step 5) use lerobot tools to remove bad episodes:
see doc here: https://huggingface.co/docs/lerobot/using_dataset_tools
conda activate unitree_lerobot_gr00t

lerobot-edit-dataset \
    --repo_id unitreerobotics/pear_on_plate_v1 \
    --new_repo_id unitreerobotics/pear_on_plate_v1_curated \
    --operation.type delete_episodes \
    --operation.episode_indices "[0, 12, 13, 23, 24, 45, 51, 54, 64, 71, 74, 102, 103, 112, 115, 124]"

step 6) convert:
cd /media/data_18tb/workspace/gr00t/Isaac-GR00T
python scripts/lerobot_conversion/convert_v3_to_v2.py   --repo-id unitreerobotics/pear_on_plate_v1_curated   --root /media/data_18tb/workspace/model_weights/lerobot

step 7) move to cluster:

scp -r /media/data_18tb/workspace/model_weights/lerobot/unitreerobotics/pear_on_plate_v1_curated \
  framser@orcd-login.mit.edu:/orcd/pool/004/framser/GROOT/datasets/

Step 8: Prepare Metadata (modality.json)

The GR00T-LeRobot format requires a meta/modality.json file to map the raw data arrays to robot components. If your new task uses the same robot configuration as a previous one, you can copy the metadata.
Bash

# On the Cluster:
# Copy modality metadata from a known working G1 task to the new pear task
cp /orcd/pool/004/framser/GROOT/datasets/bottle_plate_wood_curated/meta/modality.json \
   /orcd/pool/004/framser/GROOT/datasets/pear_on_plate_v1_curated/meta/

Checklist: * Ensure proprio and control indices (e.g., 0–28) match your robot's DOF.

    Verify camera names in the video section match the folders in videos/chunk-000/.

Step 9: Define and Register Modality Configs

To test different performance profiles (Action Horizons of 8, 16, or 32) and control types (Absolute vs. Relative), create specific Python configuration files.

Important: For Relative control, you must explicitly link the action to the state by adding state_key="proprio" to the ActionConfig.
Bash

# Example for 8-step Relative Horizon
# Save as: examples/G1Dex3/wrist-action8-Relative.py

from gr00t.configs.data.embodiment_configs import register_modality_config
from gr00t.data.types import ModalityConfig, ActionConfig, ActionRepresentation, ActionType, ActionFormat, EmbodimentTag

config = {
    "video": ModalityConfig(
        delta_indices=[0],
        modality_keys=["cam_left_high", "cam_right_high", "cam_left_wrist", "cam_right_wrist"],
    ),
    "state": ModalityConfig(delta_indices=[0], modality_keys=["proprio"]),
    "action": ModalityConfig(
        delta_indices=list(range(0, 8)), # 8-step horizon for low latency
        modality_keys=["control"],
        action_configs=[
            ActionConfig(
                rep=ActionRepresentation.RELATIVE, 
                type=ActionType.NON_EEF,
                format=ActionFormat.DEFAULT,
                state_key="proprio", # Required for Relative math
            )
        ],
    ),
    "language": ModalityConfig(delta_indices=[0], modality_keys=["task"]),
}

# Registering the config under the NEW_EMBODIMENT tag
register_modality_config(config, embodiment_tag=EmbodimentTag.NEW_EMBODIMENT)

Step 10: Generate Dataset Statistics (The "Horizon Lock")

Before training, you must run the stats script. This looks at your dataset through the lens of your chosen config and generates meta/relative_stats.json.

    Note: If you change your horizon (e.g., from 8 to 16), you must re-run this step before launching the new training.

Python

# Run via a targeted Python snippet to bypass environment/library conflicts
import importlib.util
from pathlib import Path
from gr00t.data.stats import main
from gr00t.data.types import EmbodimentTag

# 1. Load your specific config
cfg_path = Path("examples/G1Dex3/wrist-action8-Relative.py")
spec = importlib.util.spec_from_file_location("tmp_cfg", cfg_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# 2. Generate stats
main(
    "/orcd/pool/004/framser/GROOT/datasets/pear_on_plate_v1_curated",
    EmbodimentTag.NEW_EMBODIMENT,
)

Step 11: Launch Finetuning
(base) [framser@login005 G1Dex3]$ srun -p mit_normal_gpu --gres=gpu:1 --cpus-per-task=8 --mem=64G --time=02:00:00 --pty bash
srun: job 10946249 queued and waiting for resources
srun: job 10946249 has been allocated resources
(base) [framser@node4103 G1Dex3]$ # Load Modules
(base) [framser@node4103 G1Dex3]$ module load cuda/12.4.0 miniforge/25.11.0-0 git-lfs
(base) [framser@node4103 G1Dex3]$ 
(base) [framser@node4103 G1Dex3]$ # Setup environment
(base) [framser@node4103 G1Dex3]$ source ~/.bashrc
(base) [framser@node4103 G1Dex3]$ conda activate isaac-groot
(isaac-groot) [framser@node4103 G1Dex3]$ 
(isaac-groot) [framser@node4103 G1Dex3]$ # Paths and Libraries
(isaac-groot) [framser@node4103 G1Dex3]$ export ROOT=/orcd/pool/004/framser/GROOT
(isaac-groot) [framser@node4103 G1Dex3]$ export LD_LIBRARY_PATH=/home/framser/.conda/envs/isaac-groot/lib:$LD_LIBRARY_PATH
(isaac-groot) [framser@node4103 G1Dex3]$ cd /orcd/pool/004/framser/GROOT/code/Isaac-GR00T
(isaac-groot) [framser@node4103 Isaac-GR00T]$ python gr00t/data/stats.py \

(isaac-groot) [framser@node4103 datasets]$ cd /orcd/pool/004/framser/GROOT/code/Isaac-GR00T
(isaac-groot) [framser@node4103 Isaac-GR00T]$ 
(isaac-groot) [framser@node4103 Isaac-GR00T]$ uv run python -m gr00t.experiment.launch_finetune \
>     --base-model-path /orcd/pool/004/framser/GROOT/models/GR00T-N1.6-3B \
>     --dataset-path /orcd/pool/004/framser/GROOT/datasets/pear_on_plate_v1_curated_h8_rel \
>     --embodiment-tag NEW_EMBODIMENT \
>     --modality-config-path examples/G1Dex3/wrist-action8-Relative.py \
>     --num-gpus 1 \
>     --output-dir /orcd/pool/004/framser/GROOT/runs/pear_8rel_smoke_test \
>     --max-steps 2000 \
>     --save-steps 500 \
>     --global-batch-size 32 \
>     --color-jitter-params brightness 0.3 contrast 0.4 saturation 0.5 hue 0.08 \
>     --dataloader-num-workers 4

Step 12: Copy Finetuned Checkpoint & Metadata from Cluster

To run evaluations or deploy the model locally, you need to pull both the trained weights and the dataset metadata from the cluster. Crucially, we exclude the optimizer.pt file to save ~12GB of transfer time, as it is only needed if you plan to resume training.
Bash

# 1. Create the local destination folder for the checkpoint
mkdir -p /media/data_18tb/workspace/model_weights/runs/pear_8rel_smoke_test/checkpoint-2000

# 2. Pull the model weights and config files (ignoring the heavy optimizer/scheduler files)
scp framser@orcd-login.mit.edu:/orcd/pool/004/framser/GROOT/runs/pear_8rel_smoke_test/checkpoint-2000/*.{json,safetensors,yaml} \
  /media/data_18tb/workspace/model_weights/runs/pear_8rel_smoke_test/checkpoint-2000/

# 3. Pull the corrected dataset metadata (modality.json, tasks.jsonl, and relative stats)
scp -r framser@orcd-login.mit.edu:/orcd/pool/004/framser/GROOT/datasets/pear_on_plate_v1_curated/meta/* \
  /media/data_18tb/workspace/model_weights/lerobot/unitreerobotics/pear_on_plate_v1_curated/meta/

Step 13: Open-Loop Evaluation (Sanity Check)

Before deploying the model to the physical robot, run an open-loop evaluation to ensure the predicted trajectories match the recorded ground truth.
Bash

# Navigate to the correct GR00T code repository
cd /media/data_18tb/workspace/gr00t/Isaac-GR00T

# Create a folder for the output plots
mkdir -p /media/data_18tb/workspace/gr00t/eval_results/pear_8rel_eval

# Run the evaluation script
uv run python gr00t/eval/open_loop_eval_v2.py \
    --dataset-path /media/data_18tb/workspace/model_weights/lerobot/unitreerobotics/pear_on_plate_v1_curated \
    --embodiment-tag NEW_EMBODIMENT \
    --model-path /media/data_18tb/workspace/model_weights/runs/pear_8rel_smoke_test/checkpoint-2000 \
    --traj-ids 0 \
    --steps 1000 \
    --action-horizon 8 \
    --save-plot-path /media/data_18tb/workspace/gr00t/eval_results/pear_8rel_eval/ep0_checkpoint_2000




BONUS step 14 replay an episode:
without MOTION MODE
python unitree_lerobot/eval_robot/replay_robot.py     --repo_id="local_dataset"     --root="/media/data_18tb/workspace/model_weights/lerobot/unitreerobotics/pear_on_plate_v1_curated_v3.0"     --episodes=0     --frequency=30     --arm="G1_29"     --ee="dex3"     --visualization=false
WITH MOTION MODE
python unitree_lerobot/eval_robot/replay_robot.py \
  --repo_id="local_dataset" \
  --root="/media/data_18tb/workspace/model_weights/lerobot/unitreerobotics/pear_on_plate_v1_curated_v3.0" \
  --episodes=0 \
  --frequency=30 \
  --arm="G1_29" \
  --ee="dex3" \
  --motion=true \
  --visualization=false



