# gr00t/eval/run_gr00t_server_trt.py

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import importlib.util
import logging
from typing import Literal

from gr00t.data.embodiment_tags import EmbodimentTag
from gr00t.policy.gr00t_policy import Gr00tPolicy
from gr00t.policy.replay_policy import ReplayPolicy
from gr00t.policy.server_client import PolicyServer
import torch
import tyro

DEFAULT_MODEL_SERVER_PORT = 5555

# ==============================================================================
# TensorRT Injection Logic (Extracted from standalone benchmark)
# ==============================================================================

class TensorRTDiTWrapper:
    """Wrapper for TensorRT DiT engine."""

    def __init__(self, engine_path: str, device: int = 0):
        import tensorrt as trt
        self.device = device
        if torch.cuda.is_available():
            torch.cuda.init()
            torch.cuda.set_device(device)
        else:
            raise RuntimeError("CUDA not available for TensorRT")

        self.trt_logger = trt.Logger(trt.Logger.WARNING)
        self.runtime = trt.Runtime(self.trt_logger)
        with open(engine_path, "rb") as f:
            self.engine = self.runtime.deserialize_cuda_engine(f.read())
        if self.engine is None:
            raise RuntimeError(f"Failed to load TensorRT engine from {engine_path}")
        self.context = self.engine.create_execution_context()
        print(f"[TensorRT] Engine successfully loaded from {engine_path}")

    def __call__(self, sa_embs, vl_embs, timestep, image_mask=None, backbone_attention_mask=None):
        sa_embs = sa_embs.to(f"cuda:{self.device}").contiguous()
        vl_embs = vl_embs.to(f"cuda:{self.device}").contiguous()
        timestep = timestep.to(f"cuda:{self.device}").contiguous() 

        if image_mask is not None:
            image_mask = image_mask.to(f"cuda:{self.device}").contiguous()
        if backbone_attention_mask is not None:
            backbone_attention_mask = backbone_attention_mask.to(f"cuda:{self.device}").contiguous()

        self.context.set_input_shape("sa_embs", sa_embs.shape)
        self.context.set_input_shape("vl_embs", vl_embs.shape)
        self.context.set_input_shape("timestep", timestep.shape)
        if image_mask is not None:
            self.context.set_input_shape("image_mask", image_mask.shape)
        if backbone_attention_mask is not None:
            self.context.set_input_shape("backbone_attention_mask", backbone_attention_mask.shape)

        self.context.set_tensor_address("sa_embs", sa_embs.data_ptr())
        self.context.set_tensor_address("vl_embs", vl_embs.data_ptr())
        self.context.set_tensor_address("timestep", timestep.data_ptr())
        if image_mask is not None:
            self.context.set_tensor_address("image_mask", image_mask.data_ptr())
        if backbone_attention_mask is not None:
            self.context.set_tensor_address("backbone_attention_mask", backbone_attention_mask.data_ptr())

        output_shape = self.context.get_tensor_shape("output")
        output = torch.empty(tuple(output_shape), dtype=torch.bfloat16, device=f"cuda:{self.device}")
        self.context.set_tensor_address("output", output.data_ptr())

        success = self.context.execute_async_v3(torch.cuda.current_stream().cuda_stream)
        if not success:
            raise RuntimeError("TensorRT inference failed")
        return output

def replace_dit_with_tensorrt(policy: Gr00tPolicy, trt_engine_path: str, device: int = 0):
    """Replace the DiT forward method with TensorRT inference."""
    trt_dit = TensorRTDiTWrapper(trt_engine_path, device=device)

    def trt_forward(
        hidden_states, encoder_hidden_states, timestep,
        encoder_attention_mask=None, return_all_hidden_states=False,
        image_mask=None, backbone_attention_mask=None,
    ):
        output = trt_dit(
            sa_embs=hidden_states, vl_embs=encoder_hidden_states, timestep=timestep,
            image_mask=image_mask, backbone_attention_mask=backbone_attention_mask,
        )
        if return_all_hidden_states:
            raise RuntimeError("TensorRT only returns final output. Check config.")
        return output

    policy.model.action_head.model.forward = trt_forward
    # Force-disable clipping for RTC compatibility
    policy.processor.clip_outliers = False
    policy.processor.state_action_processor.clip_outliers = False
    
    print("[TensorRT] PyTorch DiT head replaced with TensorRT Engine.")


# ==============================================================================
# Server Configuration and Execution
# ==============================================================================

@dataclass
class ServerConfig:
    model_path: str | None = None
    embodiment_tag: EmbodimentTag = EmbodimentTag.NEW_EMBODIMENT
    device: str = "cuda"
    dataset_path: str | None = None
    modality_config_path: str | None = None
    execution_horizon: int | None = None
    host: str = "127.0.0.1"
    port: int = DEFAULT_MODEL_SERVER_PORT
    strict: bool = True
    use_sim_policy_wrapper: bool = False
    
    # NEW ARGUMENTS FOR TENSORRT
    inference_mode: Literal["pytorch", "tensorrt"] = "pytorch"
    trt_engine_path: str | None = None

def _import_py(path: str):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"modality_config_path does not exist: {path}")
    name = f"_gr00t_modality_{os.path.splitext(os.path.basename(path))[0]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import python file: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod) 
    return mod

def _load_modality_configs(config: ServerConfig):
    from gr00t.configs.data.embodiment_configs import MODALITY_CONFIGS
    tag_key = config.embodiment_tag.value
    if config.modality_config_path:
        mpath = config.modality_config_path
        if mpath.endswith(".py"):
            _import_py(mpath)
            if tag_key not in MODALITY_CONFIGS:
                raise KeyError(f"Embodiment '{tag_key}' not registered after importing {mpath}.")
            return MODALITY_CONFIGS[tag_key]
        with open(mpath, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError("Failed to parse modality JSON") from e

    if tag_key not in MODALITY_CONFIGS:
        raise KeyError(f"Embodiment '{tag_key}' not registered.")
    return MODALITY_CONFIGS[tag_key]

def main(config: ServerConfig):
    print("Starting GR00T inference server...")
    print(f"  Embodiment tag: {config.embodiment_tag}")
    print(f"  Model path: {config.model_path}")
    print(f"  Mode: {config.inference_mode.upper()}")
    
    if config.inference_mode == "tensorrt" and not config.trt_engine_path:
        raise ValueError("Must provide --trt-engine-path when running in tensorrt mode.")

    if config.model_path is not None:
        if config.model_path.startswith("/") and not os.path.exists(config.model_path):
            raise FileNotFoundError(f"Model path {config.model_path} does not exist")

        # 1. Load the Base PyTorch Policy
        policy = Gr00tPolicy(
            embodiment_tag=config.embodiment_tag,
            model_path=config.model_path,
            device=config.device,
            strict=config.strict,
        )

        # 2. Inject TensorRT if requested
        if config.inference_mode == "tensorrt":
            # Extract device ID (e.g. 'cuda:0' -> 0)
            dev_id = int(config.device.split(":")[1]) if ":" in config.device else 0
            replace_dit_with_tensorrt(policy, config.trt_engine_path, device=dev_id)

    elif config.dataset_path is not None:
        modality_configs = _load_modality_configs(config)
        policy = ReplayPolicy(
            dataset_path=config.dataset_path,
            modality_configs=modality_configs,
            execution_horizon=config.execution_horizon,
            strict=config.strict,
        )
    else:
        raise ValueError("Either model_path or dataset_path must be provided")

    if config.use_sim_policy_wrapper:
        from gr00t.policy.gr00t_policy import Gr00tSimPolicyWrapper
        policy = Gr00tSimPolicyWrapper(policy)

    server = PolicyServer(
        policy=policy,
        host=config.host,
        port=config.port,
    )

    try:
        server.run()
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    cfg = tyro.cli(ServerConfig)
    main(cfg)
