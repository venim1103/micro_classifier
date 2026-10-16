"""Pinned Decision 3.0 teachers with host embeddings and optional INT8 storage."""

from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import sys
import threading
import types
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

import torch
from safetensors import safe_open

from teacher.vela_int8 import QUANTIZED_LINEARS, HostEmbedding, Int8Linear

REPO_ID = "vllm-sr/d3-flash"
MINI_REPO_ID = "vllm-sr/d3-mini"
MINI_EXPERIMENT_MAX_TOKENS = 12288
REVISION = "b92769d85908bb3ee737ef9c765e1c08b887aca6"
APPROVED_REVISIONS = {
    REPO_ID: REVISION,
    "vllm-sr/d3-mini": "6d8971f464d6f9d4c5af7d9a8d75f3aa03be4f59",
}
APPROVED_MANIFESTS = {
    REPO_ID: "0be31669e11877df13bb99aa3b0c088bed2e01f0ca44d2ff10dbbb1441272629",
    "vllm-sr/d3-mini": "7adae8e93f8e8e7d90108e88a1121530ede64de79eff8fd8f1af3f4528824fca",
}
EMBEDDING_KEY = "language_model.embed_tokens.weight"
CONSTRUCTION_LOCK = threading.Lock()


def download(repo_id: str = REPO_ID) -> Path:
    """Fetch only an approved full revision, retaining at least 20 GiB free."""
    from huggingface_hub import constants, snapshot_download

    revision = APPROVED_REVISIONS[repo_id]
    cache = Path(constants.HF_HUB_CACHE)
    existing = next(item for item in (cache, *cache.parents) if item.exists())
    if shutil.disk_usage(existing).free < (20 + 27) * 1024**3:
        raise OSError("download requires 27 GiB headroom plus 20 GiB free")
    return Path(snapshot_download(repo_id, revision=revision))


def verify_package(path: Path) -> dict:
    """Require and fully hash the package manifest before importing release code."""
    path = Path(path)
    manifest = json.loads((path / "MODEL_MANIFEST.json").read_text())
    if manifest.get("schema") != "d3-package-manifest/1":
        raise ValueError("unsupported package manifest schema")
    hashes = manifest.get("files_sha256")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("package manifest must contain file hashes")
    required = {
        "d3_runtime.py",
        "d3_format.py",
        "d3_fast.py",
        "d3_kernels.py",
        "config.json",
        "decision_config.json",
        "model.safetensors.index.json",
        "readout.safetensors",
        "tokenizer.json",
        "tokenizer_config.json",
        "preprocessor_config.json",
        "chat_template.jinja",
    }
    if not required <= hashes.keys():
        raise ValueError("package manifest does not cover required model files")
    index = json.loads((path / "model.safetensors.index.json").read_text())
    if not set(index["weight_map"].values()) <= hashes.keys():
        raise ValueError("package manifest does not cover weight shards")
    for name, expected in hashes.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe manifest path: {name}")
        with (path / relative).open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch: {name}")
    return manifest


def release_module(path: Path):
    """Import only the reviewed runtime under a snapshot-specific package name."""
    name = "_micro_d3_" + hashlib.sha256(str(path.absolute()).encode()).hexdigest()[:16]
    if name not in sys.modules:
        package = types.ModuleType(name)
        package.__path__ = [str(path.absolute())]
        sys.modules[name] = package
    return importlib.import_module(f"{name}.d3_runtime")


def load_backbone(path, device="cuda", group_size=128, quantized=True):
    """Stream a Qwen3.5 checkpoint; only large text projections become INT8."""
    from transformers import Qwen3_5Config, Qwen3_5Model

    path = Path(path)
    config = Qwen3_5Config.from_pretrained(str(path), local_files_only=True)
    config._attn_implementation = "sdpa"
    replacements = {}
    with torch.device("meta"):
        model = Qwen3_5Model(config).to(dtype=torch.bfloat16)
        if quantized:
            for name, module in list(model.named_modules()):
                parts = name.split(".", 3)
                if parts[:2] != ["language_model", "layers"] or len(parts) < 4:
                    continue
                if parts[3] not in QUANTIZED_LINEARS:
                    continue
                if module.bias is not None:
                    raise ValueError(f"{name} has a bias")
                if group_size < 1 or module.in_features % group_size:
                    raise ValueError(f"invalid group size {group_size} for {name}")
                replacement = Int8Linear(
                    module.in_features, module.out_features, group_size
                )
                parent, child = name.rsplit(".", 1)
                setattr(model.get_submodule(parent), child, replacement)
                replacements[f"{name}.weight"] = replacement
    model.language_model.embed_tokens = HostEmbedding()
    parameters = dict(model.named_parameters())
    index = json.loads((path / "model.safetensors.index.json").read_text())
    weight_map = index["weight_map"]
    expected = set(parameters) | set(replacements) | {EMBEDDING_KEY}
    if set(weight_map) != expected:
        raise KeyError(
            f"weight index mismatch: missing={sorted(expected - set(weight_map))[:5]}, "
            f"unexpected={sorted(set(weight_map) - expected)[:5]}"
        )
    model.to_empty(device=device)
    text = model.language_model
    text.rotary_emb = type(text.rotary_emb)(config=text.config, device=device)
    vision = model.visual
    with torch.device(device):
        vision.rotary_pos_emb = type(vision.rotary_pos_emb)(config.vision_config)
    parameters = dict(model.named_parameters())
    loaded = set()
    with torch.no_grad():
        for shard in sorted(set(weight_map.values())):
            if Path(shard).name != shard:
                raise ValueError(f"unsafe weight shard path: {shard}")
            with safe_open(str(path / shard), framework="pt") as tensors:
                for key in sorted(tensors.keys()):
                    if key not in weight_map or weight_map[key] != shard:
                        raise KeyError(f"unexpected tensor {key} in {shard}")
                    tensor = tensors.get_tensor(key)
                    if key == EMBEDDING_KEY:
                        if tuple(tensor.shape) != (
                            config.text_config.vocab_size,
                            config.text_config.hidden_size,
                        ):
                            raise ValueError("embedding shape does not match config")
                        text.embed_tokens.weight_host = tensor.to(torch.bfloat16)
                    elif key in replacements:
                        replacements[key].load(tensor)
                    elif parameters[key].shape == tensor.shape:
                        parameters[key].copy_(tensor)
                    else:
                        raise ValueError(f"weight shape mismatch: {key}")
                    loaded.add(key)
    if loaded != expected:
        raise KeyError(f"missing tensors: {sorted(expected - loaded)[:5]}")
    model.requires_grad_(False).eval()
    if torch.device(device).type == "cuda":
        torch.cuda.empty_cache()
    return model


class Teacher:
    """In-process teacher restricted to local images and a bounded token budget."""

    def __init__(self, engine, repo_id, quantized, token_budget):
        self.engine = engine
        self.repo_id = repo_id
        self.quantized = quantized
        self.token_budget = token_budget

    def system_one(self, *, state, questions, images=None, videos=None):
        if videos:
            raise ValueError("video inputs are disabled in this adapter")
        if images is not None and not isinstance(images, (list, tuple)):
            raise ValueError("images must be a list of local paths or PIL images")
        for image in images or []:
            if isinstance(image, (str, Path)) and urlsplit(str(image)).scheme:
                raise ValueError("only local images are allowed; URLs are disabled")
        prepared = self.engine.prepare(state, questions, images=images)
        lengths = list(prepared.lengths.values()) or [
            len(sequence) for sequence in prepared.sequences.values()
        ]
        if lengths and max(lengths) > self.token_budget:
            raise ValueError(f"request exceeds {self.token_budget}-token budget")
        probabilities, tokens = self.engine.run(prepared)
        return self.engine.respond(prepared, probabilities, tokens)

    def provenance(self):
        return {
            **self.engine.provenance(),
            "repo_id": self.repo_id,
            "revision": APPROVED_REVISIONS[self.repo_id],
            "storage": "int8-group128" if self.quantized else "bfloat16",
            "embedding_storage": "host-bfloat16",
            "token_budget": self.token_budget,
            "local_media_only": True,
            "videos_enabled": False,
        }


def load_engine(
    path=None,
    device="cuda",
    repo_id=REPO_ID,
    token_budget=2048,
    *,
    experimental_mini_int8=False,
):
    """Keep the release prompts/readout unchanged; inject only its backbone load."""
    if repo_id not in APPROVED_REVISIONS:
        raise ValueError(f"unapproved model: {repo_id}")
    if type(experimental_mini_int8) is not bool:
        raise TypeError("experimental_mini_int8 must be a boolean")
    if experimental_mini_int8 and repo_id != MINI_REPO_ID:
        raise ValueError("INT8 context experiment is only approved for d3-mini")
    limit = MINI_EXPERIMENT_MAX_TOKENS if experimental_mini_int8 else 2048
    if type(token_budget) is not int or not 1 <= token_budget <= limit:
        raise ValueError(f"token_budget must be between 1 and {limit}")
    path = Path(path) if path is not None else download(repo_id)
    with (path / "MODEL_MANIFEST.json").open("rb") as stream:
        manifest_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if manifest_digest != APPROVED_MANIFESTS[repo_id]:
        raise ValueError("manifest does not match the approved model revision")
    manifest = verify_package(path)
    quantized = repo_id == REPO_ID or experimental_mini_int8
    with CONSTRUCTION_LOCK:
        runtime = release_module(path)
        backbone = load_backbone(path, device, quantized=quantized)
        factory = types.SimpleNamespace(
            from_pretrained=lambda *args, **kwargs: backbone
        )
        with patch.object(runtime, "backbone_class", return_value=factory):
            engine = runtime.D3(
                path,
                device=device,
                batch_size=1,
                manifest=manifest,
                max_length=token_budget,
                model_name=repo_id,
            )
    return Teacher(engine, repo_id, quantized, token_budget)
