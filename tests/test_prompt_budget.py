import hashlib
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from sim.rover import Config, RoverEnv, rollout, write_episode
from teacher.label_pipeline import compact_request_draft, prepare_request
from teacher.prompt_budget import (
    ASSET_NAMES,
    compare_compact_requests,
    count_requests,
    load_prompt_assets,
    main,
    verify_prompt_assets,
)


@pytest.fixture
def prepared_request():
    config = Config()
    observation, _ = RoverEnv(config).reset(seed=2)
    return prepare_request(observation, config=config)


@pytest.fixture
def fake_assets():
    calls = []

    def tokenize(texts, **settings):
        calls.append(settings)
        return {"input_ids": [list(range(len(text))) for text in texts]}

    def render(tokenizer, state, question, codes):
        return state + "|question-and-chat-overhead"

    return SimpleNamespace(
        tokenizer=tokenize,
        formatter=SimpleNamespace(render=render),
        codes=["A", "B", "C", "D", "E"],
        provenance={"kind": "fake_test_only"},
        calls=calls,
    )


@pytest.mark.parametrize("budget", [3, 4])
def test_complete_prompt_count_and_inclusive_budget_without_mutation(
    prepared_request, fake_assets, budget
):
    prepared_request["state"] = ""
    fake_assets.formatter.render = lambda *args: "abcd"
    original = deepcopy(prepared_request)
    report = count_requests([prepared_request], assets=fake_assets, budget=budget)
    assert report["results"][0]["tokens"] == {"mode": 4}
    assert report["all_fit"] is (budget == 4)
    assert report["over_budget_count"] == (budget == 3)
    assert report["inference_calls"] == 0 and not report["model_weights_loaded"]
    assert not report["live_labeling_approved"] and not report["training_approved"]
    assert fake_assets.calls == [
        {"add_special_tokens": False, "truncation": False, "padding": False}
    ]
    assert (
        prepared_request == original and not prepared_request["token_budget_verified"]
    )
    json.dumps(report, allow_nan=False)


def test_preflight_includes_prompt_overhead_and_rejects_empty_batches(
    prepared_request, fake_assets
):
    prepared_request["state"] = "x"
    report = count_requests([prepared_request], assets=fake_assets)
    assert report["max_tokens"] > len(prepared_request["state"])
    with pytest.raises(ValueError, match="at least one"):
        count_requests([], assets=fake_assets)


@pytest.mark.parametrize("budget", [True, 0, 2049])
def test_preflight_cannot_raise_existing_token_ceiling(
    prepared_request, fake_assets, budget
):
    with pytest.raises(ValueError, match="budget"):
        count_requests([prepared_request], assets=fake_assets, budget=budget)
    assert not fake_assets.calls


def test_invalid_scope_is_rejected_before_tokenization(prepared_request, fake_assets):
    prepared_request["training_approved"] = True
    with pytest.raises(ValueError, match="fake-teacher"):
        count_requests([prepared_request], assets=fake_assets)
    assert not fake_assets.calls


@pytest.mark.parametrize("sequences", [[], [[]], [[1], [2]]])
def test_bad_tokenizer_output_is_rejected(prepared_request, fake_assets, sequences):
    fake_assets.tokenizer = lambda *args, **kwargs: {"input_ids": sequences}
    with pytest.raises(ValueError, match="sequences"):
        count_requests([prepared_request], assets=fake_assets)


def test_asset_hashes_are_required_before_any_release_code_execution(tmp_path):
    hashes = {}
    for name in ASSET_NAMES:
        raw = b"fixture asset; never executed"
        (tmp_path / name).write_bytes(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    manifest = {"schema": "d3-package-manifest/1", "files_sha256": hashes}
    raw = json.dumps(manifest).encode()
    (tmp_path / "MODEL_MANIFEST.json").write_bytes(raw)
    checksum = hashlib.sha256(raw).hexdigest()
    verified, source = verify_prompt_assets(tmp_path, expected_manifest_sha256=checksum)
    assert verified == hashes and source == b"fixture asset; never executed"
    with pytest.raises(ValueError, match="manifest identity"):
        verify_prompt_assets(tmp_path, expected_manifest_sha256="0" * 64)
    (tmp_path / "d3_format.py").write_text("raise RuntimeError('must not execute')")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_prompt_assets(tmp_path, expected_manifest_sha256=checksum)


def test_report_metadata_is_detached_from_inputs(prepared_request, fake_assets):
    prepared_request["source"] = {"tick": 0}
    report = count_requests([prepared_request], assets=fake_assets)
    report["assets"]["kind"] = "changed"
    report["results"][0]["source"]["tick"] = 1
    assert fake_assets.provenance == {"kind": "fake_test_only"}
    assert prepared_request["source"] == {"tick": 0}


@pytest.mark.parametrize("float32_rows", [False, True])
def test_compact_comparison_checks_exactness_without_qualifying_live_use(
    prepared_request, fake_assets, float32_rows
):
    original = deepcopy(prepared_request)
    report = compare_compact_requests(
        [prepared_request], assets=fake_assets, float32_rows=float32_rows
    )
    row = report["results"][0]
    assert row["original_tokens"]["mode"] > row["compact_tokens"]["mode"]
    assert row["exact_roundtrip"] and report["exact_roundtrip_count"] == 1
    assert not report["live_labeling_approved"] and not report["training_approved"]
    assert report["review_status"] == "unreviewed_draft"
    assert report["inference_calls"] == 0 and not report["model_weights_loaded"]
    assert prepared_request == original
    report["assets"]["kind"] = "changed"
    assert fake_assets.provenance["kind"] == "fake_test_only"
    json.dumps(report, allow_nan=False)


def test_cli_float32_draft_uses_explicit_typed_comparison(
    prepared_request, tmp_path, fake_assets, monkeypatch, capsys
):
    output = tmp_path / "float32-comparison.json"
    monkeypatch.setattr(
        "teacher.prompt_budget.episode_requests",
        lambda *args, **kwargs: [prepared_request],
    )
    monkeypatch.setattr(
        "teacher.prompt_budget.load_prompt_assets", lambda **kwargs: fake_assets
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "prompt_budget",
            "--episode",
            "unused.jsonl",
            "--output",
            str(output),
            "--compare-float32-draft",
        ],
    )
    status = main()
    summary = json.loads(capsys.readouterr().out)
    report = json.loads(output.read_text())
    assert (
        report["schema"]
        == "micro-classifier/lossless-float32-prompt-comparison-draft/1"
    )
    assert report["representation_schema"].endswith("row-f32-draft/1")
    assert report["exact_roundtrip_count"] == summary["request_count"] == 1
    assert status == (0 if report["all_fit"] else 1)
    assert not report["live_labeling_approved"] and not report["training_approved"]


def test_cli_comparison_drafts_are_mutually_exclusive(tmp_path, monkeypatch):
    output = tmp_path / "report.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "prompt_budget",
            "--episode",
            "unused.jsonl",
            "--output",
            str(output),
            "--compare-compact-draft",
            "--compare-float32-draft",
        ],
    )
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2 and not output.exists()


def test_comparison_never_assumes_compact_is_shorter(prepared_request, fake_assets):
    compact_state = compact_request_draft(prepared_request)["state"]

    def tokenize(texts, **settings):
        return {
            "input_ids": [
                list(range(2049 if compact_state in text else 1)) for text in texts
            ]
        }

    fake_assets.tokenizer = tokenize
    report = compare_compact_requests([prepared_request], assets=fake_assets)
    assert report["original_all_fit"] and not report["all_fit"]
    assert report["original_max_tokens"] == 1 and report["max_tokens"] == 2049


@pytest.mark.parametrize("wrong_codes", [False, True])
def test_asset_loader_is_local_only_and_never_loads_a_model(
    tmp_path, monkeypatch, wrong_codes
):
    from transformers import AutoTokenizer

    from teacher import d3_int8

    source = b"FORMAT_ID = 'fixture-format'\ndef answer_codes(tokenizer):\n    return ['A'], [1]\n"
    config = {
        "prompt": "d3",
        "format_id": "fixture-format",
        "codes": ["A"],
        "token_ids": [2 if wrong_codes else 1],
    }
    hashes = {}
    for name in ASSET_NAMES:
        raw = (
            source
            if name == "d3_format.py"
            else json.dumps(config).encode()
            if name == "decision_config.json"
            else b"{}"
        )
        if name == "d3_runtime.py":
            raw = b"raise RuntimeError('runtime must not be imported')"
        (tmp_path / name).write_bytes(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    raw = json.dumps(
        {"schema": "d3-package-manifest/1", "files_sha256": hashes}
    ).encode()
    (tmp_path / "MODEL_MANIFEST.json").write_bytes(raw)
    monkeypatch.setitem(
        d3_int8.APPROVED_MANIFESTS, d3_int8.REPO_ID, hashlib.sha256(raw).hexdigest()
    )

    class LocalTokenizer:
        is_fast = True
        pad_token_id = 0

        def __call__(self, text, **settings):
            return {"input_ids": [1]}

    def load_tokenizer(path, **settings):
        assert path == str(tmp_path)
        assert settings == {
            "local_files_only": True,
            "trust_remote_code": False,
            "use_fast": True,
        }
        return LocalTokenizer()

    def forbidden(*args, **kwargs):
        pytest.fail("model/runtime/weight path must not be called")

    monkeypatch.setattr(AutoTokenizer, "from_pretrained", load_tokenizer)
    for name in ("load_engine", "load_backbone", "release_module", "verify_package"):
        monkeypatch.setattr(d3_int8, name, forbidden)
    if wrong_codes:
        with pytest.raises(ValueError, match="answer codes"):
            load_prompt_assets(snapshot=tmp_path)
    else:
        assets = load_prompt_assets(snapshot=tmp_path)
        assert assets.codes == ["A"]
        assert not assets.provenance["model_weights_loaded"]
        assert assets.provenance["files_sha256"] == hashes


def test_cli_records_over_budget_without_labels_and_is_exclusive(
    tmp_path, fake_assets, monkeypatch, capsys
):
    records, _ = rollout(RoverEnv(Config(max_ticks=1)))
    episode = tmp_path / "episode.jsonl"
    output = tmp_path / "report.json"
    write_episode(episode, records)
    monkeypatch.setattr(
        "teacher.prompt_budget.load_prompt_assets", lambda **kwargs: fake_assets
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "prompt_budget",
            "--episode",
            str(episode),
            "--output",
            str(output),
            "--limit",
            "1",
        ],
    )
    assert main() == 1
    summary = json.loads(capsys.readouterr().out)
    report = json.loads(output.read_text())
    assert summary["request_count"] == 1 and summary["over_budget_count"] == 1
    assert not report["all_fit"] and not report["live_labeling_approved"]
    assert not report["training_approved"] and report["inference_calls"] == 0
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        main()
    assert output.read_bytes() == original


def test_cli_compact_draft_is_explicit_opt_in(
    tmp_path, fake_assets, monkeypatch, capsys
):
    records, _ = rollout(RoverEnv(Config(max_ticks=1)))
    episode = tmp_path / "episode.jsonl"
    output = tmp_path / "comparison.json"
    write_episode(episode, records)
    monkeypatch.setattr(
        "teacher.prompt_budget.load_prompt_assets", lambda **kwargs: fake_assets
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "prompt_budget",
            "--episode",
            str(episode),
            "--output",
            str(output),
            "--limit",
            "1",
            "--compare-compact-draft",
        ],
    )
    status = main()
    summary = json.loads(capsys.readouterr().out)
    report = json.loads(output.read_text())
    assert report["schema"] == "micro-classifier/lossless-prompt-comparison-draft/1"
    assert status == (0 if report["all_fit"] else 1)
    assert summary["request_count"] == report["exact_roundtrip_count"] == 1
    assert not report["live_labeling_approved"]
