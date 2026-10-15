import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import torch
from safetensors.torch import save_file
from transformers import Qwen3_5Config, Qwen3_5Model

from teacher.d3_int8 import REPO_ID, Teacher, load_backbone, verify_package
from teacher.vela_int8 import HostEmbedding, Int8Linear


@pytest.fixture
def checkpoint(tmp_path):
    config = Qwen3_5Config(
        text_config={
            "hidden_size": 32,
            "intermediate_size": 64,
            "num_hidden_layers": 2,
            "num_attention_heads": 4,
            "num_key_value_heads": 2,
            "head_dim": 8,
            "vocab_size": 64,
            "layer_types": ["linear_attention", "full_attention"],
            "linear_key_head_dim": 8,
            "linear_value_head_dim": 8,
            "linear_num_key_heads": 4,
            "linear_num_value_heads": 4,
        },
        vision_config={
            "depth": 1,
            "hidden_size": 32,
            "intermediate_size": 64,
            "num_heads": 4,
            "out_hidden_size": 32,
            "patch_size": 2,
            "temporal_patch_size": 2,
            "spatial_merge_size": 2,
            "num_position_embeddings": 16,
            "deepstack_visual_indexes": [],
        },
    )
    torch.manual_seed(3)
    original = Qwen3_5Model(config).to(dtype=torch.bfloat16).eval()
    config.save_pretrained(tmp_path)
    weights = original.state_dict()
    save_file(weights, tmp_path / "model.safetensors")
    index = {"weight_map": {key: "model.safetensors" for key in weights}}
    (tmp_path / "model.safetensors.index.json").write_text(json.dumps(index))
    return tmp_path, original


@pytest.mark.parametrize("quantized", [True, False])
def test_streamed_backbone_matches_stored_weights(checkpoint, quantized):
    path, original = checkpoint
    model = load_backbone(path, device="cpu", group_size=8, quantized=quantized)
    assert isinstance(model.language_model.embed_tokens, HostEmbedding)
    assert torch.equal(
        model.language_model.embed_tokens(torch.tensor([[1, 3]])),
        original.language_model.embed_tokens(torch.tensor([[1, 3]])),
    )
    for name, parameter in model.named_parameters():
        assert parameter.dtype == torch.bfloat16
        assert not parameter.requires_grad
        assert torch.equal(parameter, original.get_parameter(name))
    projections = [
        (name, module)
        for name, module in model.named_modules()
        if isinstance(module, Int8Linear)
    ]
    assert len(projections) == (13 if quantized else 0)
    for name, module in projections:
        inputs = torch.randn(2, 3, module.in_features).bfloat16()
        expected = original.get_submodule(name)(inputs)
        error = (module(inputs).float() - expected.float()).norm()
        assert error / expected.float().norm() < 0.03
    reference_rotary = {
        "language_model.rotary_emb": type(original.language_model.rotary_emb)(
            config=original.language_model.config
        ),
        "visual.rotary_pos_emb": type(original.visual.rotary_pos_emb)(
            original.config.vision_config
        ),
    }
    for name, buffer in model.named_buffers():
        if "rotary" in name:
            parent, child = name.rsplit(".", 1)
            assert torch.equal(buffer, reference_rotary[parent].get_buffer(child))
            assert buffer.dtype == torch.float32
            assert torch.isfinite(buffer).all()


@pytest.mark.parametrize("change", ["missing", "unexpected"])
def test_loader_rejects_incorrect_weight_index(checkpoint, change):
    path, _ = checkpoint
    index_path = path / "model.safetensors.index.json"
    index = json.loads(index_path.read_text())
    if change == "missing":
        index["weight_map"].pop(next(iter(index["weight_map"])))
    else:
        index["weight_map"]["unknown.weight"] = "model.safetensors"
    index_path.write_text(json.dumps(index))
    with pytest.raises(KeyError, match="weight index mismatch"):
        load_backbone(path, device="cpu", group_size=8)


def test_loader_rejects_invalid_quantization_group(checkpoint):
    path, _ = checkpoint
    with pytest.raises(ValueError, match="invalid group size"):
        load_backbone(path, device="cpu", group_size=7)


def test_manifest_is_required_and_all_listed_files_are_hashed(tmp_path):
    with pytest.raises(FileNotFoundError):
        verify_package(tmp_path)
    hashes = {}
    for name in (
        "d3_runtime.py",
        "d3_format.py",
        "d3_fast.py",
        "d3_kernels.py",
        "config.json",
        "decision_config.json",
        "readout.safetensors",
        "tokenizer.json",
        "tokenizer_config.json",
        "preprocessor_config.json",
        "chat_template.jinja",
    ):
        content = name.encode()
        (tmp_path / name).write_bytes(content)
        hashes[name] = hashlib.sha256(content).hexdigest()
    index = json.dumps({"weight_map": {"weight": "readout.safetensors"}}).encode()
    (tmp_path / "model.safetensors.index.json").write_bytes(index)
    hashes["model.safetensors.index.json"] = hashlib.sha256(index).hexdigest()
    manifest = {"schema": "d3-package-manifest/1", "files_sha256": hashes}
    (tmp_path / "MODEL_MANIFEST.json").write_text(json.dumps(manifest))
    assert verify_package(tmp_path) == manifest
    omitted = dict(hashes)
    omitted.pop("readout.safetensors")
    (tmp_path / "MODEL_MANIFEST.json").write_text(
        json.dumps({**manifest, "files_sha256": omitted})
    )
    with pytest.raises(ValueError, match="required model files"):
        verify_package(tmp_path)
    (tmp_path / "MODEL_MANIFEST.json").write_text(json.dumps(manifest))
    (tmp_path / "d3_format.py").write_text("modified")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_package(tmp_path)


@pytest.mark.parametrize(
    "media", ["https://example.org/image.png", "file:///tmp/a.png"]
)
def test_remote_media_is_rejected_before_release_code_runs(media):
    engine = Mock()
    teacher = Teacher(engine, REPO_ID, True, 2048)
    with pytest.raises(ValueError, match="only local images"):
        teacher.system_one(state="test", questions={}, images=[media])
    engine.prepare.assert_not_called()


def test_video_inputs_are_rejected_before_release_code_runs():
    engine = Mock()
    teacher = Teacher(engine, REPO_ID, True, 2048)
    with pytest.raises(ValueError, match="video inputs are disabled"):
        teacher.system_one(state="test", questions={}, videos=["local.mp4"])
    engine.prepare.assert_not_called()


def test_token_budget_is_checked_before_inference():
    engine = Mock()
    engine.prepare.return_value = SimpleNamespace(lengths={}, sequences={"q": [0] * 9})
    teacher = Teacher(engine, REPO_ID, True, 8)
    with pytest.raises(ValueError, match="token budget"):
        teacher.system_one(state="test", questions={"q": {"type": "noul"}})
    engine.run.assert_not_called()
