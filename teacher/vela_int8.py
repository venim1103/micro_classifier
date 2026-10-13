"""Vela 2.0 9B teacher with INT8 weight-only projections, sized for a 12 GB CUDA GPU.

The release loader holds all 7.95 B parameters in FP32 (about 32 GB). The computation
the release evaluates is: bf16 autocast for the backbone matmuls (the stored projection
weights are bf16), FP32 norms, gates and heads, and FP32 token embeddings. This loader
keeps that computation and changes only how the ten large projections of every layer
are stored: symmetric INT8 with one bf16 scale per group of input columns, expanded to
bf16 just before each matmul (W8A16). The FP32 embedding table stays in host RAM and
only the looked-up rows are copied to the GPU.

The release's own Python files (modeling_vela2.py, vela2_inference.py) are imported from
the snapshot, so only the pinned, reviewed revision is executed.
"""

from __future__ import annotations

import contextlib
import functools
import importlib
import json
import sys
from pathlib import Path

import torch
import torch.nn.functional as F
from safetensors import safe_open
from torch import nn

REPO_ID = "vllm-sr/Vela-2.0-9B"
REVISION = "068425bb145c05884a98b870c219047da22d9aea"
RELEASE_FILES = [
    "config.json",
    "calibration.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "model.safetensors.index.json",
    "*.safetensors",
    "configuration_vela2.py",
    "modeling_vela2.py",
    "vela2_inference.py",
    "card_examples.json",
]
QUANTIZED_LINEARS = frozenset(
    {
        "mlp.gate_proj",
        "mlp.up_proj",
        "mlp.down_proj",
        "self_attn.q_proj",
        "self_attn.k_proj",
        "self_attn.v_proj",
        "self_attn.o_proj",
        "linear_attn.in_proj_qkv",
        "linear_attn.in_proj_z",
        "linear_attn.out_proj",
    }
)
EMBEDDING_KEY = "backbone.embed_tokens.weight"


def download(revision: str = REVISION) -> Path:
    """Fetch the pinned release into the Hugging Face cache and return its directory."""
    from huggingface_hub import snapshot_download

    return Path(
        snapshot_download(REPO_ID, revision=revision, allow_patterns=RELEASE_FILES)
    )


def release_modules(path: Path):
    """Import (configuration_vela2, modeling_vela2, vela2_inference) from a release."""
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    names = ("configuration_vela2", "modeling_vela2", "vela2_inference")
    return tuple(importlib.import_module(name) for name in names)


def quantize_int8(
    weight: torch.Tensor, group_size: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """Symmetric INT8 values and one bf16 scale per `group_size` input columns."""
    rows, columns = weight.shape
    if columns % group_size:
        raise ValueError(f"{columns} columns are not divisible by {group_size}")
    groups = weight.float().reshape(rows, columns // group_size, group_size)
    scale = groups.abs().amax(-1) / 127
    scale = scale.clamp_min(torch.finfo(torch.bfloat16).tiny).to(torch.bfloat16)
    values = torch.round(groups / scale.float()[..., None]).clamp_(-127, 127)
    return values.to(torch.int8).reshape(rows, columns), scale


class Int8Linear(nn.Module):
    """Bias-free linear layer with INT8 weights; the matmul itself runs in bf16."""

    def __init__(self, in_features, out_features, group_size, device=None):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.group_size = group_size
        shape = (out_features, in_features)
        self.register_buffer(
            "weight_int8", torch.empty(shape, dtype=torch.int8, device=device)
        )
        self.register_buffer(
            "scale",
            torch.empty(
                out_features,
                in_features // group_size,
                dtype=torch.bfloat16,
                device=device,
            ),
        )
        # Set by stored_bf16_weights(): returns the release's bf16 weight instead.
        self.reference_weight = None

    @torch.no_grad()
    def load(self, weight: torch.Tensor) -> None:
        if tuple(weight.shape) != (self.out_features, self.in_features):
            raise ValueError(f"weight shape {tuple(weight.shape)} does not match")
        values, scale = quantize_int8(
            weight.to(self.weight_int8.device), self.group_size
        )
        self.weight_int8.copy_(values)
        self.scale.copy_(scale)

    def dequantized_weight(self) -> torch.Tensor:
        groups = self.weight_int8.view(self.out_features, -1, self.group_size)
        weight = groups * self.scale[..., None]
        return weight.view(self.out_features, self.in_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.reference_weight is None:
            weight = self.dequantized_weight()
        else:
            weight = self.reference_weight()
        return F.linear(x.to(torch.bfloat16), weight)

    def extra_repr(self) -> str:
        return (
            f"in_features={self.in_features}, out_features={self.out_features}, "
            f"group_size={self.group_size}"
        )


class HostEmbedding(nn.Module):
    """Token embeddings kept in host RAM; looked-up rows move to the ids' device."""

    def __init__(self):
        super().__init__()
        # A plain attribute, so Module.to() and parameters() leave it on the host.
        self.weight_host = None

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        return F.embedding(ids.cpu(), self.weight_host).to(ids.device)


def _weight_map(path: Path) -> dict[str, str]:
    index = json.loads((path / "model.safetensors.index.json").read_text())
    return index["weight_map"]


def load_model(path, device="cuda", group_size=128):
    """Release model with INT8 projections on `device` and embeddings in host RAM.

    group_size=0 uses one scale per output row.
    """
    path = Path(path)
    configuration, modeling, _ = release_modules(path)
    config = configuration.Vela2DecoderConfig.from_pretrained(str(path))
    quantized = {}
    with torch.device("meta"), modeling._no_init():
        model = modeling.Vela2DecoderModel(config)
        for name, module in list(model.named_modules()):
            parts = name.split(".", 3)
            if parts[:2] != ["backbone", "layers"] or len(parts) < 4:
                continue
            if parts[3] not in QUANTIZED_LINEARS:
                continue
            if module.bias is not None:
                raise ValueError(f"{name} has a bias")
            replacement = Int8Linear(
                module.in_features,
                module.out_features,
                group_size or module.in_features,
            )
            parent, child = name.rsplit(".", 1)
            setattr(model.get_submodule(parent), child, replacement)
            quantized[f"{name}.weight"] = replacement
    backbone = model.backbone
    backbone.embed_tokens = HostEmbedding()
    model.to_empty(device=device)
    # Non-persistent rotary buffers are computed from the config, not loaded.
    rotary = type(backbone.rotary_emb)(config=backbone.config)
    backbone.rotary_emb = rotary.to(device)

    parameters = dict(model.named_parameters())
    loaded = set()
    weight_map = _weight_map(path)
    with torch.no_grad():
        for shard in sorted(set(weight_map.values())):
            with safe_open(str(path / shard), framework="pt") as tensors:
                for key in tensors.keys():  # noqa: SIM118 (not iterable)
                    tensor = tensors.get_tensor(key)
                    if key == EMBEDDING_KEY:
                        backbone.embed_tokens.weight_host = tensor.float()
                    elif key in quantized:
                        quantized[key].load(tensor)
                    elif key in parameters and parameters[key].shape == tensor.shape:
                        parameters[key].copy_(tensor)
                    else:
                        raise KeyError(f"unexpected tensor {key} in {shard}")
                    loaded.add(key)
    expected = set(parameters) | set(quantized) | {EMBEDDING_KEY}
    missing = sorted(expected - loaded)
    if missing:
        raise KeyError(f"{len(missing)} missing tensors, first: {missing[:5]}")
    model.requires_grad_(False).eval()
    model._vela2_dir = str(path)
    if torch.device(device).type == "cuda":
        torch.cuda.empty_cache()
    return model


def load_engine(path=None, device="cuda", group_size=128, token_budget=2048):
    """The INT8 model inside the release's engine (SystemOne and shortcut APIs).

    A 2048-token batch budget keeps a 12 GB GPU inside its physical memory. Larger
    budgets can push the allocator past it; under WSL2 the driver then spills to
    system memory instead of failing, which was 3-9x slower in our runs.
    """
    path = Path(path) if path else download()
    model = load_model(path, device, group_size)
    _, _, inference = release_modules(path)
    return inference.Vela2(
        str(path),
        device=device,
        amp_bf16=True,
        token_budget=token_budget,
        model=model,
    )


@contextlib.contextmanager
def stored_bf16_weights(model, path, cache_size=8):
    """Run the quantized projections with the release's stored bf16 weights instead.

    Weights are streamed from the safetensors shards per matmul and a few are cached on
    the GPU, so this reproduces the evaluated computation without 32 GB of memory.
    """
    path = Path(path)
    weight_map = _weight_map(path)
    shards = {
        name: safe_open(str(path / name), framework="pt")
        for name in set(weight_map.values())
    }

    @functools.lru_cache(maxsize=cache_size)
    def fetch(key, device):
        return shards[weight_map[key]].get_tensor(key).to(device)

    modules = {
        f"{name}.weight": module
        for name, module in model.named_modules()
        if isinstance(module, Int8Linear)
    }
    for key, module in modules.items():
        module.reference_weight = functools.partial(
            fetch, key, module.weight_int8.device
        )
    try:
        yield model
    finally:
        for module in modules.values():
            module.reference_weight = None
        fetch.cache_clear()
