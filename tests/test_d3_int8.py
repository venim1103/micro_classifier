import contextlib
import hashlib
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import torch
from safetensors.torch import save_file
from transformers import Qwen3_5Config, Qwen3_5Model

from teacher.d3_int8 import REPO_ID, Teacher, load_backbone, load_engine, verify_package
from teacher.validate_d3_int8 import (
    compare,
    diagnostic_requests,
    fixture_digest,
    mini_experiment_memory_limit,
    stored_reference,
    validate_mini_int8_experiment,
)
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


def test_unapproved_local_manifest_is_rejected_before_import(tmp_path, monkeypatch):
    release_import = Mock()
    monkeypatch.setattr("teacher.d3_int8.release_module", release_import)
    (tmp_path / "MODEL_MANIFEST.json").write_text("{}")
    with pytest.raises(ValueError, match="approved model revision"):
        load_engine(tmp_path, device="cpu")
    release_import.assert_not_called()


@pytest.mark.parametrize(
    "repo_id,experiment,budget,quantized",
    [
        (REPO_ID, False, 2048, True),
        ("vllm-sr/d3-mini", False, 2048, False),
        ("vllm-sr/d3-mini", True, 12288, True),
    ],
)
def test_loader_mini_experiment_is_explicit_and_defaults_unchanged(
    tmp_path, monkeypatch, repo_id, experiment, budget, quantized
):
    from teacher import d3_int8

    raw = b'{"fixture":true}'
    (tmp_path / "MODEL_MANIFEST.json").write_bytes(raw)
    monkeypatch.setitem(
        d3_int8.APPROVED_MANIFESTS, repo_id, hashlib.sha256(raw).hexdigest()
    )
    manifest = {"fixture": True}
    verification = Mock(return_value=manifest)
    backbone = Mock(return_value=object())
    runtime = SimpleNamespace(backbone_class=Mock(), D3=Mock(return_value=object()))
    monkeypatch.setattr(d3_int8, "verify_package", verification)
    monkeypatch.setattr(d3_int8, "load_backbone", backbone)
    monkeypatch.setattr(d3_int8, "release_module", Mock(return_value=runtime))
    options = {"experimental_mini_int8": True} if experiment else {}
    teacher = load_engine(
        tmp_path, device="cpu", repo_id=repo_id, token_budget=budget, **options
    )
    assert teacher.quantized is quantized and teacher.token_budget == budget
    verification.assert_called_once_with(tmp_path)
    backbone.assert_called_once_with(tmp_path, "cpu", quantized=quantized)
    assert runtime.D3.call_args.kwargs["max_length"] == budget
    assert runtime.D3.call_args.kwargs["manifest"] == manifest


@pytest.mark.parametrize(
    "options,error,match",
    [
        ({"token_budget": 2049}, ValueError, "2048"),
        ({"experimental_mini_int8": True}, ValueError, "only approved for d3-mini"),
        (
            {"repo_id": "vllm-sr/d3-mini", "experimental_mini_int8": "yes"},
            TypeError,
            "boolean",
        ),
        (
            {
                "repo_id": "vllm-sr/d3-mini",
                "experimental_mini_int8": True,
                "token_budget": 12289,
            },
            ValueError,
            "12288",
        ),
    ],
)
def test_loader_experiment_rejects_invalid_scope_before_release_import(
    tmp_path, monkeypatch, options, error, match
):
    release = Mock()
    monkeypatch.setattr("teacher.d3_int8.release_module", release)
    with pytest.raises(error, match=match):
        load_engine(tmp_path, **options)
    release.assert_not_called()


@pytest.mark.parametrize("fail", [False, True])
def test_mini_memory_cap_is_enforced_and_restored_without_gpu(monkeypatch, fail):
    cuda = torch.cuda
    monkeypatch.setattr(cuda, "is_available", lambda: True)
    monkeypatch.setattr(cuda, "get_device_capability", lambda device: (8, 6))
    monkeypatch.setattr(
        cuda,
        "get_device_properties",
        lambda device: SimpleNamespace(total_memory=12 * 2**30),
    )
    monkeypatch.setattr(cuda, "mem_get_info", lambda device: (11 * 2**30, 12 * 2**30))
    fractions = [1.0]
    monkeypatch.setattr(
        cuda, "get_per_process_memory_fraction", lambda device: fractions[-1]
    )
    monkeypatch.setattr(cuda, "memory_reserved", lambda device: 0)
    setter = Mock(side_effect=lambda fraction, device: fractions.append(fraction))
    monkeypatch.setattr(cuda, "set_per_process_memory_fraction", setter)
    monkeypatch.setattr(cuda, "reset_peak_memory_stats", Mock())
    try:
        with mini_experiment_memory_limit() as limit:
            assert limit["enforced_cap_bytes"] == 10 * 2**30
            assert setter.call_args.args == (10 / 12, "cuda:0")
            if fail:
                raise RuntimeError("simulated OOM")
    except RuntimeError:
        assert fail
    assert setter.call_args.args == (1.0, "cuda:0")
    assert setter.call_count == 2


def test_mini_memory_cap_rejects_incompatible_gpu_before_allocation(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_capability", lambda device: (6, 1))
    setter = Mock()
    monkeypatch.setattr(torch.cuda, "set_per_process_memory_fraction", setter)
    with pytest.raises(ValueError, match="native BF16"), mini_experiment_memory_limit():
        pytest.fail("incompatible GPU must not enter experiment")
    setter.assert_not_called()


@pytest.mark.parametrize("oom", [False, True])
def test_mini_parity_experiment_is_capped_and_requires_review(
    monkeypatch, oom, tmp_path
):
    from teacher import validate_d3_int8 as validation

    limit = {"enforced_cap_bytes": 10 * 2**30}
    monkeypatch.setattr(
        validation,
        "mini_experiment_memory_limit",
        lambda: contextlib.nullcontext(limit),
    )
    engine = SimpleNamespace(
        image_unavailable=None, runtime_info=lambda: {"fixture": True}
    )
    teacher = SimpleNamespace(
        engine=engine, provenance=lambda: {"storage": "int8-group128"}
    )
    loader = Mock(
        side_effect=torch.OutOfMemoryError("capped OOM") if oom else None,
        return_value=teacher,
    )
    monkeypatch.setattr(validation.d3_int8, "load_engine", loader)
    monkeypatch.setattr(torch.cuda, "memory_allocated", lambda: 4 * 2**30)
    monkeypatch.setattr(torch.cuda, "max_memory_reserved", lambda: 5 * 2**30)
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: False)
    runner = Mock(return_value={"responses": {"fixture": True}})
    monkeypatch.setattr(validation, "run_requests", runner)
    monkeypatch.setattr(
        validation, "stored_reference", lambda *args: contextlib.nullcontext()
    )
    monkeypatch.setattr(validation, "compare", lambda *args: {"decision_flips": 0})
    report = validate_mini_int8_experiment(tmp_path)
    assert report["memory_limit"] == limit
    assert loader.call_args.kwargs["experimental_mini_int8"] is True
    assert not report["training_approved"] and not report["live_labeling_approved"]
    assert not report["context_probe_approved_by_parity"]
    assert report["status"] == ("aborted" if oom else "complete_requires_parity_review")
    assert runner.call_count == (0 if oom else 2)


@pytest.mark.parametrize(
    "reference_parity,failure",
    [
        (False, None),
        (False, "candidate_oom"),
        (True, None),
        (True, "candidate_oom"),
        (True, "reference_oom"),
        (True, "reference_cap"),
    ],
)
def test_mini_context_probe_preserves_full_inputs_and_aborts_without_retry(
    monkeypatch, reference_parity, failure, tmp_path
):
    from teacher import validate_d3_int8 as validation

    short_response = {
        "answers": {
            "mode": {
                "type": "choice",
                "probabilities": {"discarded-a": 0.25, "discarded-b": 0.75},
            }
        },
        "usage": {"input_tokens": 20},
    }
    short_responses = {"short": short_response}
    parity = {
        "schema": "micro-classifier/d3-mini-int8-experiment/1",
        "repo_id": validation.d3_int8.MINI_REPO_ID,
        "revision": validation.d3_int8.APPROVED_REVISIONS[
            validation.d3_int8.MINI_REPO_ID
        ],
        "manifest_sha256": validation.d3_int8.APPROVED_MANIFESTS[
            validation.d3_int8.MINI_REPO_ID
        ],
        "status": "complete_requires_parity_review",
        "token_budget": 2048,
        "fixtures": {"sha256": fixture_digest(diagnostic_requests())},
        "candidate": {"responses": short_responses},
        "reference": {"responses": short_responses},
        "parity": compare(short_responses, short_responses),
    }
    parity_path = tmp_path / "parity.json"
    parity_path.write_text(json.dumps(parity))
    inputs = [
        (
            str(tokens),
            {
                "state": json.dumps(
                    {
                        "module_observation": {"history_valid": [True] * 8},
                        "tokens": tokens,
                    }
                ),
                "questions": {"mode": {"type": "choice"}},
                "source": {"tick": 15},
                "provenance": {},
            },
        )
        for tokens in (3500, 7000, 11000)
    ]
    monkeypatch.setattr(validation, "context_probe_inputs", lambda: inputs)
    monkeypatch.setattr(
        validation,
        "mini_experiment_memory_limit",
        lambda: contextlib.nullcontext({"enforced_cap_bytes": 10 * 2**30}),
    )
    engine = SimpleNamespace(
        prepare=lambda state, questions: SimpleNamespace(
            errors={}, sequences={"mode": [0] * json.loads(state)["tokens"]}
        ),
        max_length=12288,
        runtime_info=lambda: {"fixture": True},
    )
    calls = []
    phases = {"reference": False, "candidate_calls": 0, "reference_calls": 0}

    @contextlib.contextmanager
    def reference_context(*args):
        phases["reference"] = True
        try:
            yield
        finally:
            phases["reference"] = False

    monkeypatch.setattr(validation, "stored_reference", reference_context)
    teacher = SimpleNamespace(
        engine=engine, token_budget=12288, provenance=lambda: {"fixture": True}
    )

    def infer(*, state, questions):
        calls.append((state, questions, teacher.token_budget, engine.max_length))
        assert json.loads(state)["tokens"] <= teacher.token_budget == engine.max_length
        key = "reference_calls" if phases["reference"] else "candidate_calls"
        phases[key] += 1
        if (
            failure == "candidate_oom"
            and key == "candidate_calls"
            and phases[key] == 2
            or failure == "reference_oom"
            and key == "reference_calls"
        ):
            raise torch.OutOfMemoryError("capped fixture OOM")
        probability = 0.7 if phases["reference"] else 0.75
        return {
            "answers": {
                "mode": {
                    "type": "choice",
                    "probabilities": {
                        "discarded-a": 1 - probability,
                        "discarded-b": probability,
                    },
                }
            },
            "usage": {"input_tokens": json.loads(state)["tokens"]},
        }

    teacher.system_one = infer
    loader = Mock(return_value=teacher)
    monkeypatch.setattr(validation.d3_int8, "load_engine", loader)
    monkeypatch.setattr(torch.cuda, "empty_cache", Mock())
    monkeypatch.setattr(torch.cuda, "reset_peak_memory_stats", Mock())
    monkeypatch.setattr(torch.cuda, "synchronize", Mock())
    monkeypatch.setattr(torch.cuda, "memory_allocated", lambda: 4 * 2**30)
    monkeypatch.setattr(
        torch.cuda,
        "max_memory_allocated",
        lambda: (
            (11 if failure == "reference_cap" and phases["reference"] else 5) * 2**30
        ),
    )
    monkeypatch.setattr(torch.cuda, "max_memory_reserved", lambda: 6 * 2**30)
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: False)
    report = validation.validate_mini_context_probe(
        tmp_path, parity_path, reference_parity=reference_parity
    )
    assert report["status"] == (
        "aborted"
        if failure
        else "complete_parity_requires_review"
        if reference_parity
        else "complete_resource_only"
    )
    assert report["responses_discarded"] and report["mode_labels_written"] == 0
    assert "discarded-a" not in json.dumps(
        report
    ) and "probabilities" not in json.dumps(report)
    assert not phases["reference"]
    assert phases["candidate_calls"] == (
        2 if failure == "candidate_oom" else 1 if failure else 6
    )
    assert len(report["cases"]) == (
        4 if failure == "candidate_oom" else 1 if failure else 9
    )
    assert phases["reference_calls"] == (
        1 if failure and reference_parity else 6 if reference_parity else 0
    )
    if reference_parity and not failure:
        assert report["parity"]["compared_values"] == 12
        assert report["parity"]["max_abs_delta"] == pytest.approx(0.05)
        assert report["parity"]["mean_abs_delta"] == pytest.approx(0.05)
        assert report["parity"]["decision_flips"] == 0
        assert report["parity"]["by_type"]["choice"]["questions"] == 6
    if failure:
        assert report["cases"][-1]["active_phase"] == (
            "candidate" if failure == "candidate_oom" else "reference"
        )
    assert all(
        state in [request["state"] for _, request in inputs] for state, _, _, _ in calls
    )
    assert loader.call_args.kwargs["token_budget"] == 12288
    assert [row["tokens"] for row in report["inputs"]] == [3500, 7000, 11000]
    assert (
        report["reviewed_parity_sha256"]
        == hashlib.sha256(parity_path.read_bytes()).hexdigest()
    )


def test_context_parity_summary_weights_values_and_discards_distributions():
    from teacher.validate_d3_int8 import summarize_context_parity

    candidate = {
        "answers": {
            "mode": {
                "type": "choice",
                "probabilities": {"discarded-a": 0.6, "discarded-b": 0.4},
            }
        },
        "usage": {"input_tokens": 4},
    }
    reference = json.loads(json.dumps(candidate))
    reference["answers"]["mode"]["probabilities"] = {
        "discarded-a": 0.4,
        "discarded-b": 0.6,
    }
    score = {
        "answers": {
            "tier": {"type": "score", "probabilities": {"0": 0.2, "1": 0.3, "2": 0.5}}
        },
        "usage": {"input_tokens": 4},
    }
    result = summarize_context_parity(
        [
            {"parity": compare({"row": candidate}, {"row": reference})},
            {"parity": compare({"row": score}, {"row": score})},
            {"status": "budget_rejected"},
        ]
    )
    assert result["compared_values"] == 5
    assert result["decision_flips"] == 1
    assert result["max_abs_delta"] == pytest.approx(0.2)
    assert result["mean_abs_delta"] == pytest.approx(0.08)
    assert result["by_type"]["choice"]["questions"] == 1
    assert result["by_type"]["score"]["questions"] == 1
    assert result["by_type"]["noul"]["compared_values"] == 0
    assert "discarded-a" not in json.dumps(result)
    with pytest.raises(ValueError, match="no context parity"):
        summarize_context_parity([])


def test_context_parity_opt_in_requires_boolean():
    from teacher.validate_d3_int8 import validate_mini_context_probe

    with pytest.raises(TypeError, match="must be a boolean"):
        validate_mini_context_probe(None, None, reference_parity="true")


def test_context_parity_cli_dispatch_is_explicit(monkeypatch, tmp_path):
    from teacher import validate_d3_int8 as validation

    snapshot = tmp_path / "cached"
    parity_path = tmp_path / "review.json"
    output = tmp_path / "fresh.json"
    report = {
        "status": "complete_parity_requires_review",
        "parity": {"decision_flips": 0},
    }
    context = Mock(return_value=report)
    parity = Mock()
    monkeypatch.setattr(validation, "validate_mini_context_probe", context)
    monkeypatch.setattr(validation, "validate_mini_int8_experiment", parity)
    monkeypatch.setattr(torch, "set_num_threads", Mock())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_d3_int8",
            "--mini-int8-context-parity",
            "--repo-id",
            "vllm-sr/d3-mini",
            "--snapshot",
            str(snapshot),
            "--reviewed-parity-report",
            str(parity_path),
            "--output",
            str(output),
        ],
    )
    validation.main()
    assert context.call_args.args == (snapshot, parity_path)
    assert context.call_args.kwargs == {"reference_parity": True}
    parity.assert_not_called()
    assert json.loads(output.read_text()) == report


def test_mini_context_probe_rejects_unreviewed_report_before_gpu(monkeypatch, tmp_path):
    from teacher import validate_d3_int8 as validation

    parity_path = tmp_path / "wrong.json"
    parity_path.write_text("{}")
    loader = Mock()
    monkeypatch.setattr(validation.d3_int8, "load_engine", loader)
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: False)
    report = validation.validate_mini_context_probe(tmp_path, parity_path)
    assert report["status"] == "aborted"
    loader.assert_not_called()
    assert report["cases"] == []


@pytest.mark.parametrize(
    "arguments",
    [
        ["--mini-int8-experiment"],
        ["--mini-int8-experiment", "--snapshot", "cached"],
        ["--mini-int8-experiment", "--repo-id", "vllm-sr/d3-mini"],
        [
            "--mini-int8-context-probe",
            "--repo-id",
            "vllm-sr/d3-mini",
            "--snapshot",
            "cached",
        ],
        ["--reviewed-parity-report", "review.json"],
        ["--mini-int8-experiment", "--mini-int8-context-probe"],
        ["--mini-int8-context-parity"],
        [
            "--mini-int8-context-parity",
            "--repo-id",
            "vllm-sr/d3-mini",
            "--snapshot",
            "cached",
        ],
        ["--mini-int8-context-probe", "--mini-int8-context-parity"],
    ],
)
def test_mini_experiment_cli_rejects_incomplete_scope_before_execution(
    monkeypatch, tmp_path, arguments
):
    from teacher import validate_d3_int8 as validation

    parity = Mock()
    context = Mock()
    monkeypatch.setattr(validation, "validate_mini_int8_experiment", parity)
    monkeypatch.setattr(validation, "validate_mini_context_probe", context)
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_d3_int8", "--output", str(tmp_path / "fresh.json"), *arguments],
    )
    with pytest.raises(SystemExit) as error:
        validation.main()
    assert error.value.code == 2
    parity.assert_not_called()
    context.assert_not_called()


def test_mini_cli_preserves_existing_output_before_execution(monkeypatch, tmp_path):
    from teacher import validate_d3_int8 as validation

    output = tmp_path / "existing.json"
    output.write_text("must remain unchanged")
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_d3_int8", "--output", str(output), "--mini-int8-experiment"],
    )
    with pytest.raises(FileExistsError):
        validation.main()
    assert output.read_text() == "must remain unchanged"


def test_diagnostic_suite_is_fixed_and_covers_types_and_images():
    rows = diagnostic_requests()
    assert len(rows) == len({row["id"] for row in rows}) == 25
    assert sum("images" in row for row in rows) == 4
    assert {
        question["type"] for row in rows for question in row["questions"].values()
    } == {"choice", "noul", "score"}
    assert fixture_digest(rows) == fixture_digest(diagnostic_requests())
    rows[0]["state"] += "changed"
    assert fixture_digest(rows) != fixture_digest(diagnostic_requests())


def test_parity_reports_deltas_and_flips():
    response = {
        "answers": {
            "binary": {"type": "noul", "noul": 0.5},
            "choice": {"type": "choice", "probabilities": {"a": 0.6, "b": 0.4}},
            "score": {"type": "score", "probabilities": {"0": 0.2, "1": 0.8}},
        },
        "usage": {"input_tokens": 4},
    }
    reference = json.loads(json.dumps(response))
    reference["answers"]["binary"]["noul"] = 0.49
    result = compare({"row": response}, {"row": reference})
    assert result["compared_values"] == 6
    assert result["decision_flips"] == result["by_type"]["noul"]["decision_flips"] == 1
    assert result["max_abs_delta"] == pytest.approx(0.01)
    response["answers"]["choice"] = {"type": "choice", "error": "max_length_exceeded"}
    with pytest.raises(ValueError, match="rejected"):
        compare({"row": response}, {"row": reference})


@pytest.mark.parametrize("quantized", [True, False])
def test_stored_reference_is_exact_and_restores_modules(checkpoint, quantized):
    path, original = checkpoint
    model = load_backbone(path, device="cpu", group_size=8, quantized=quantized)
    teacher = Teacher(SimpleNamespace(backbone=model), REPO_ID, quantized, 2048)
    projection = model.language_model.layers[0].mlp.up_proj
    inputs = torch.randn(2, 3, projection.in_features).bfloat16()
    before = projection(inputs)
    ids = torch.tensor([[1, 3, 3]])
    embeddings = model.language_model.embed_tokens(ids)
    with stored_reference(teacher, path):
        assert torch.equal(
            projection(inputs), original.language_model.layers[0].mlp.up_proj(inputs)
        )
        assert torch.equal(model.language_model.embed_tokens(ids), embeddings)
    assert torch.equal(projection(inputs), before)
    assert torch.equal(model.language_model.embed_tokens(ids), embeddings)
