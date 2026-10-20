import json
from copy import deepcopy

import numpy as np
import pytest

from interface.protocol import encode_state
from sim.rover import (
    Config,
    RoverEnv,
    rollout,
    state_from_observation,
    with_wire_frames,
    write_episode,
)
from teacher.label_pipeline import (
    LabelCache,
    compact_request_draft,
    episode_requests,
    expand_compact_state,
    label_requests,
    main,
    plan_episode,
    prepare_request,
)


@pytest.fixture
def sample():
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset(seed=2)
    return config, observation


def test_request_preparation_uses_label_free_observation_validation(
    sample, monkeypatch
):
    from teacher import label_pipeline

    original = label_pipeline.validate_observation
    validated = []

    def validate(observation, config):
        validated.append(observation)
        return original(observation, config)

    monkeypatch.setattr(label_pipeline, "validate_observation", validate)
    config, observation = sample
    prepared = prepare_request(observation, config=config)
    assert len(validated) == 1 and validated[0] is observation
    assert prepared["allowed_use"] == "fake_teacher_pipeline_tests_only"


def test_legacy_episode_rate_is_preserved_by_readers(tmp_path):
    from teacher.provenance import audit_source
    from teacher.review import make_review_packet, validate_review_packet

    config = Config(max_ticks=1, latency_ticks=0, tof_rate_hz=None)
    records, _ = rollout(RoverEnv(config), policy=lambda observation: (0, 0))
    del records[0]["config"]["tof_rate_hz"]
    path = tmp_path / "legacy-fixture.jsonl"
    write_episode(path, records)
    requests = list(episode_requests(path))
    assert len(requests) == 2
    assert all(row["provenance"]["config"]["tof_rate_hz"] is None for row in requests)
    assert (
        json.loads(requests[-1]["state"])["module_observation"]["tof_sample_tick"] == 1
    )
    for request in requests:
        validate_review_packet(make_review_packet(request))
    assert (
        audit_source(path)["episode_sha256"] == requests[0]["source"]["episode_sha256"]
    )


def review_request(sample):
    config, observation = sample
    prepared = prepare_request(observation, config=config)
    prepared["source"] = {
        "episode_sha256": "2" * 64,
        "tick": 0,
        "line": 1,
        "frame_origin": "synthesized_from_observation",
    }
    return prepared


def test_readiness_projection_preserves_input_and_hides_private_lineage(sample):
    from teacher.readiness import project_review_packet, validate_projection
    from teacher.review import make_review_packet

    packet = make_review_packet(review_request(sample))
    original = deepcopy(packet)
    projection = project_review_packet(packet, "1" * 32)
    assert projection["state"] == packet["state"]
    assert projection["assessments"] == packet["assessments"]
    assert set(projection).isdisjoint(
        {"source", "input_provenance", "grouping", "packet_id"}
    )
    assert packet["source"]["episode_sha256"] not in json.dumps(projection)
    assert packet == original
    validate_projection(projection, packet)
    projection["state"]["module_observation"]["tof_m"][0][0] = 123
    assert packet == original
    with pytest.raises(ValueError):
        validate_projection(projection, packet)


@pytest.mark.parametrize("defect", ["answer", "scope", "numeric_scope", "extra", "id"])
def test_readiness_projection_rejects_answers_scope_and_private_fields(sample, defect):
    from teacher.readiness import project_review_packet, validate_projection
    from teacher.review import make_review_packet

    packet = make_review_packet(review_request(sample))
    projection = project_review_packet(packet, "1" * 32)
    if defect == "answer":
        projection["assessments"]["mode"]["label"] = "dock"
    elif defect == "scope":
        projection["training_approved"] = True
    elif defect == "numeric_scope":
        projection["training_approved"] = 0
    elif defect == "extra":
        projection["source"] = packet["source"]
    else:
        projection["review_id"] = "clear-scene"
    with pytest.raises(ValueError):
        validate_projection(projection, packet)


@pytest.mark.parametrize(
    "final_tick,expected",
    [(0, [0]), (1, [0, 1]), (7, [0, 7]), (15, [0, 7, 15]), (20, [0, 7, 15, 20])],
)
def test_readiness_window_selection_deduplicates_skips_and_keeps_final(
    tmp_path, final_tick, expected
):
    from dataclasses import asdict

    from teacher.readiness import select_review_requests

    env = RoverEnv()
    observation, _ = env.reset(seed=1)
    records = [
        {
            "schema": "micro-classifier/sim-episode/1",
            "kind": "metadata",
            "config": asdict(env.config),
            "observation": observation,
        }
    ]
    for _ in range(final_tick):
        observation, *_ = env.step((0, 0))
        records.append({"kind": "transition", "observation": observation})
    records.append({"kind": "summary", "ticks": final_tick})
    path = tmp_path / "fixture.jsonl"
    write_episode(path, records)
    requests = select_review_requests(path)
    assert [row["source"]["tick"] for row in requests] == expected
    assert all(
        json.loads(row["state"])["module_observation"]["history_valid"][-1]
        for row in requests
    )


@pytest.mark.parametrize(
    "closing_record",
    [
        None,
        {"kind": "summary", "ticks": 1},
        {"kind": "summary", "ticks": False},
        {"kind": "summary", "ticks": 0.0},
    ],
)
def test_readiness_selection_requires_matching_final_summary(tmp_path, closing_record):
    from dataclasses import asdict

    from teacher.readiness import select_review_requests

    observation, _ = RoverEnv().reset(seed=1)
    records = [
        {
            "schema": "micro-classifier/sim-episode/1",
            "kind": "metadata",
            "config": asdict(Config()),
            "observation": observation,
        }
    ]
    if closing_record is not None:
        records.append(closing_record)
    path = tmp_path / "incomplete-fixture.jsonl"
    write_episode(path, records)
    with pytest.raises(ValueError, match="summary"):
        select_review_requests(path)


@pytest.mark.parametrize("defect", ["empty", "too_long", "config"])
def test_readiness_selection_rejects_non_normal_sources(monkeypatch, defect):
    from dataclasses import asdict

    from teacher.readiness import select_review_requests

    rows = [
        {
            "source": {"tick": 401 if defect == "too_long" else 0},
            "provenance": {"config": asdict(Config())},
        }
    ]
    if defect == "empty":
        rows = []
    elif defect == "config":
        rows[0]["provenance"]["config"]["max_ticks"] = 32
    monkeypatch.setattr("teacher.readiness.episode_requests", lambda path: iter(rows))
    with pytest.raises(ValueError):
        select_review_requests("fake-source")


@pytest.mark.parametrize(
    "defect", ["same", "inside", "ancestor", "existing", "parent_file"]
)
def test_readiness_paths_reject_before_environment_creation(
    tmp_path, monkeypatch, defect
):
    from teacher.readiness import run_readiness_pilot

    paths = [
        tmp_path / name
        for name in ("episodes", "blind.json", "audit.json", "report.json")
    ]
    if defect == "same":
        paths[2] = paths[1]
    elif defect == "inside":
        paths[2] = paths[0] / "audit.json"
    elif defect == "ancestor":
        paths[0] = paths[2] / "episodes"
    elif defect == "existing":
        paths[1].touch()
    else:
        paths[2].touch()
        paths[3] = paths[2] / "report.json"
        paths[2] = tmp_path / "other-audit.json"
    monkeypatch.setattr(
        "teacher.readiness.RoverEnv",
        lambda *args: pytest.fail("simulation started before path validation"),
    )
    with pytest.raises((ValueError, FileExistsError, NotADirectoryError)):
        run_readiness_pilot(*paths)
    assert not paths[0].exists()


def test_readiness_fake_rollouts_obey_fixed_scope_and_private_mapping(
    tmp_path, monkeypatch
):
    import hashlib
    import stat
    from dataclasses import asdict

    from teacher.readiness import run_readiness_pilot, validate_projection

    seeds = []

    def fake_rollout(env):
        seeds.append(env.seed)
        observation, _ = env.reset(seed=env.seed)
        summary = {
            "kind": "summary",
            "ticks": 0,
            "success": False,
            "collision": False,
            "timeout": False,
        }
        records = [
            {
                "schema": "micro-classifier/sim-episode/1",
                "kind": "metadata",
                "seed": env.seed,
                "policy": "fake_fixture",
                "config": asdict(env.config),
                "scenario": asdict(env.scenario),
                "observation": observation,
            },
            summary,
        ]
        return records, summary

    monkeypatch.setattr("teacher.readiness.rollout", fake_rollout)
    paths = [
        tmp_path / name
        for name in ("episodes", "blind.json", "audit.json", "report.json")
    ]
    report = run_readiness_pilot(*paths)
    assert seeds == list(range(20261020, 20261028))
    assert report["config"] == asdict(Config())
    assert report["episode_count"] == report["projection_count"] == 8
    assert report["distinct_selected_inputs"] == 1
    assert report["exact_input_match_group_sizes"] == [8]
    assert report["max_sources_sharing_selected_input"] == 8
    assert (
        report["actual_annotations"]
        == report["mode_labels"]
        == report["teacher_calls"]
        == 0
    )
    assert not report["uncertainty_qualified"] and not report["task_cohort_accepted"]
    blind, audit = json.loads(paths[1].read_text()), json.loads(paths[2].read_text())
    private = {row["review_id"]: row["packet"] for row in audit["mappings"]}
    for projection in blind["projections"]:
        validate_projection(projection, private[projection["review_id"]])
        assert projection["review_id"] not in json.dumps(report)
    for key, path in (
        ("blind_artifact", paths[1]),
        ("private_audit_artifact", paths[2]),
    ):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == report[key]["sha256"]
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert json.loads(paths[3].read_text()) == report
    with pytest.raises(FileExistsError):
        run_readiness_pilot(*paths)


def test_blind_review_packet_preserves_input_without_suggestions(sample):
    from teacher.label_pipeline import canonical
    from teacher.review import make_review_packet, validate_review_packet

    prepared = review_request(sample)
    original = deepcopy(prepared)
    prepared["teacher_suggestion"] = "SECRET"
    prepared["proxy_suggestion"] = "SECRET"
    packet = make_review_packet(prepared)
    assert canonical(packet["state"]) == original["state"]
    assert packet["source"] == original["source"]
    assert packet["input_provenance"] == original["provenance"]
    assert all(row["label"] is None for row in packet["assessments"].values())
    assert packet["grouping"]["source_family"] is None
    assert packet["grouping"]["template_family"] is None
    assert packet["grouping"]["partition"] is None
    assert "SECRET" not in json.dumps(packet)
    assert packet == make_review_packet(prepared)
    validate_review_packet(packet)
    packet["input_provenance"]["config"]["radius"] = 5
    assert prepared["provenance"] == original["provenance"]


@pytest.mark.parametrize(
    "defect", ["answer", "privileged", "source", "state", "split", "scope", "extra"]
)
def test_review_packet_rejects_tampering_even_with_recomputed_id(sample, defect):
    from teacher.label_pipeline import digest
    from teacher.review import make_review_packet, validate_review_packet

    packet = make_review_packet(review_request(sample))
    if defect == "answer":
        packet["assessments"]["mode"]["label"] = "dock"
    elif defect == "privileged":
        packet["state"]["module_observation"]["ground_truth"] = "SECRET"
    elif defect == "source":
        packet["source"]["tick"] += 1
    elif defect == "state":
        packet["state"]["host_state"]["sequence"] += 1
    elif defect == "split":
        packet["grouping"]["partition"] = "test"
    elif defect == "scope":
        packet["training_approved"] = True
    else:
        packet["suggestion"] = "SECRET"
    packet["packet_id"] = digest(
        {key: value for key, value in packet.items() if key != "packet_id"}
    )
    with pytest.raises(ValueError):
        validate_review_packet(packet)


@pytest.mark.parametrize(
    "field,value",
    [("question_id", True), ("question_id", 1.0), ("reviewed", 0), ("reviewed", 0.0)],
)
def test_review_packet_rejects_numeric_metadata_aliases(sample, field, value):
    from teacher.label_pipeline import digest
    from teacher.review import make_review_packet, validate_review_packet

    packet = make_review_packet(review_request(sample))
    if field == "question_id":
        packet["questions"][0]["id"] = value
    else:
        packet["grouping"]["reviewed"] = value
    packet["packet_id"] = digest(
        {key: item for key, item in packet.items() if key != "packet_id"}
    )
    with pytest.raises(ValueError):
        validate_review_packet(packet)


@pytest.mark.parametrize("defect", ["padding", "range_shape", "motion"])
def test_review_rehashing_does_not_bypass_renderer_validation(sample, defect):
    import hashlib

    from teacher.label_pipeline import canonical, digest
    from teacher.review import make_review_packet, validate_review_packet

    packet = make_review_packet(review_request(sample))
    observation = packet["state"]["module_observation"]
    if defect == "padding":
        observation["history_tof_m"][0][0][0] = 1.0
    elif defect == "range_shape":
        observation["tof_m"][0].pop()
    else:
        observation["history_ego"][-1][0] = 1.0
    packet["state_sha256"] = hashlib.sha256(
        canonical(packet["state"]).encode()
    ).hexdigest()
    packet["packet_id"] = digest(
        {key: value for key, value in packet.items() if key != "packet_id"}
    )
    with pytest.raises(ValueError, match="renderer validation"):
        validate_review_packet(packet)


def fake_review_fixture(packet):
    return {
        "schema": "micro-classifier/fake-review-fixture/1",
        "packet_id": packet["packet_id"],
        "reviewer": {"kind": "fake_test_only", "id": "test/reviewer"},
        "assessments": {
            row["name"]: {
                "label": None if row["name"] == "mode" else row["options"][0],
                "abstention_reason": "policy_undefined"
                if row["name"] == "mode"
                else None,
                "notes": "synthetic format fixture",
            }
            for row in packet["questions"]
        },
    }


def test_fake_review_is_explicit_isolated_and_keeps_mode_unlabeled(sample):
    from teacher.review import make_review_packet, normalize_review_fixture

    packet = make_review_packet(review_request(sample))
    fixture = fake_review_fixture(packet)
    original = deepcopy(fixture)
    with pytest.raises(ValueError, match="explicit fake"):
        normalize_review_fixture(packet, fixture)
    result = normalize_review_fixture(packet, fixture, fake_test_only=True)
    assert result["synthetic"] and not result["training_approved"]
    assert not result["reviewed_dataset"]
    assert result["assessments"]["mode"]["label"] is None
    result["assessments"]["path_blocked"]["notes"] = "changed"
    assert fixture == original
    assert all(row["label"] is None for row in packet["assessments"].values())


@pytest.mark.parametrize(
    "defect",
    ["real", "identity", "mode", "option", "reason", "missing", "notes", "numeric"],
)
def test_fake_review_rejects_real_identity_and_invalid_assessments(sample, defect):
    from teacher.review import make_review_packet, normalize_review_fixture

    packet = make_review_packet(review_request(sample))
    fixture = fake_review_fixture(packet)
    if defect == "real":
        fixture["reviewer"]["kind"] = "human"
    elif defect == "identity":
        fixture["packet_id"] = "0" * 64
    elif defect == "mode":
        fixture["assessments"]["mode"].update(label="dock", abstention_reason=None)
    elif defect == "option":
        fixture["assessments"]["path_blocked"]["label"] = "unknown"
    elif defect == "reason":
        fixture["assessments"]["mode"]["abstention_reason"] = None
    elif defect == "missing":
        del fixture["assessments"]["clear_sector"]
    elif defect == "notes":
        fixture["assessments"]["mode"]["notes"] = 5
    else:
        fixture["assessments"]["speed_tier"]["label"] = 0
    with pytest.raises(ValueError):
        normalize_review_fixture(packet, fixture, fake_test_only=True)


@pytest.mark.parametrize("limit", [0, -1, 33, True, 1.5])
def test_review_preparation_rejects_bad_bounds_before_source_reads(limit):
    from teacher.review import prepare_review

    with pytest.raises(ValueError, match="1-32"):
        prepare_review(["not-opened"], limit=limit)


@pytest.mark.parametrize("wire", [False, True])
def test_review_bundle_cli_is_bounded_blank_model_free_and_exclusive(
    tmp_path, monkeypatch, wire
):
    import hashlib
    import sys

    from teacher.review import main as review_main
    from teacher.review import prepare_review, validate_review_packet

    records, _ = rollout(RoverEnv(Config(max_ticks=2)))
    source = tmp_path / "episode.jsonl"
    write_episode(source, with_wire_frames(records) if wire else records)
    original = source.read_bytes()
    output, report_path = tmp_path / "packets.json", tmp_path / "report.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "review",
            "--episode",
            str(source),
            "--limit",
            "2",
            "--output",
            str(output),
            "--report",
            str(report_path),
        ],
    )
    review_main()
    bundle = json.loads(output.read_text())
    report = json.loads(report_path.read_text())
    assert report["schema"] == "micro-classifier/blind-review-preparation-report/1"
    assert bundle["schema"] == "micro-classifier/blind-review-bundle/1"
    assert bundle["packet_count"] == 2 and bundle["source_episode_count"] == 1
    assert (
        bundle["teacher_calls"]
        == bundle["actual_annotations"]
        == bundle["mode_labels"]
        == 0
    )
    assert not bundle["locked_task_splits"] and not bundle["training_approved"]
    assert (
        report["packet_file_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    )
    for packet in bundle["packets"]:
        validate_review_packet(packet)
        assert (
            packet["source"]["episode_sha256"] == hashlib.sha256(original).hexdigest()
        )
    assert source.read_bytes() == original
    with pytest.raises(FileExistsError):
        review_main()
    with pytest.raises(ValueError, match="duplicate source"):
        prepare_review([source, source])
    with pytest.raises(ValueError, match="1-32"):
        prepare_review([source] * 5, limit=8)
    assert "ground_truth" not in output.read_text()
    assert "probabilities" not in output.read_text()


def test_review_cli_preserves_existing_report_before_any_source_read(
    tmp_path, monkeypatch
):
    import sys

    from teacher.review import main as review_main

    output, report = tmp_path / "fresh.json", tmp_path / "existing.json"
    report.write_text("existing report")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "review",
            "--episode",
            "not-opened",
            "--output",
            str(output),
            "--report",
            str(report),
        ],
    )
    with pytest.raises(FileExistsError):
        review_main()
    assert report.read_text() == "existing report"
    assert not output.exists()


def test_render_preserves_host_sensor_history_and_question_order(sample):
    config, observation = sample
    frame = encode_state(state_from_observation(observation))
    request = prepare_request(observation, config=config, state_frame=frame)
    payload = json.loads(request["state"])
    assert payload["host_state"]["velocity_m_s"] == [0, 0, 0]
    assert (
        payload["module_observation"]["history_tof_m"]
        == observation["history_tof_m"].tolist()
    )
    assert (
        payload["module_observation"]["tof_valid"] == observation["tof_valid"].tolist()
    )
    assert (
        list(request["questions"]["mode"]["criteria"])
        == request["option_order"]["mode"]
    )
    assert request["allowed_use"] == "fake_teacher_pipeline_tests_only"
    assert not request["training_approved"] and not request["token_budget_verified"]
    assert request == prepare_request(observation, config=config)


def test_render_excludes_privileged_values_and_does_not_mutate_inputs(sample):
    config, observation = sample
    original = deepcopy(observation)
    first = prepare_request(observation, config=config)
    np.testing.assert_equal(original, observation)
    observation.update(
        info={"ground_truth": "SECRET"},
        action=[1, 2],
        simulation_label={"mode": "dock"},
    )
    assert prepare_request(observation, config=config) == first
    assert "SECRET" not in first["state"] and "simulation_label" not in first["state"]


def test_compact_draft_is_exact_nonmutating_and_keeps_default_renderer(sample):
    config, observation = sample
    request = prepare_request(observation, config=config)
    original = deepcopy(request)
    compact = compact_request_draft(request)
    assert (
        expand_compact_state(
            compact["state"],
            expected_sha256=compact["representation"]["original_state_sha256"],
        )
        == request["state"]
    )
    assert compact["questions"] == request["questions"]
    assert compact["option_order"] == request["option_order"]
    assert compact["provenance"] == request["provenance"]
    assert request == original == prepare_request(observation, config=config)
    assert compact["representation"]["review_status"] == "unreviewed_draft"
    assert not compact["representation"]["live_use_approved"]
    assert not compact["training_approved"] and not compact["token_budget_verified"]
    assert len(compact["state"]) < len(request["state"])
    assert compact == compact_request_draft(request)
    compact["questions"]["mode"]["instructions"] = "changed"
    assert request == original


def test_compact_draft_preserves_float_digits_signed_zero_and_boolean_types(sample):
    config, observation = sample
    request = prepare_request(observation, config=config)
    payload = json.loads(request["state"])
    payload["module_observation"]["history_ego"][0] = [
        0.6000000238418579,
        -0.0,
        1.0000000000000002,
        1e-300,
    ]
    request["state"] = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    compact = compact_request_draft(request)
    assert expand_compact_state(compact["state"]) == request["state"]
    rows = json.loads(compact["state"])["row_table"]
    assert any(row == payload["module_observation"]["history_ego"][0] for row in rows)
    assert any(row and type(row[0]) is bool for row in rows)
    assert any(row and type(row[0]) is not bool for row in rows)


@pytest.mark.parametrize("float32_rows", [False, True])
@pytest.mark.parametrize(("history_ticks", "dropout"), [(1, 0.0), (8, 0.25)])
def test_compact_roundtrip_through_warm_noisy_masked_history(
    history_ticks, dropout, float32_rows
):
    config = Config(history_ticks=history_ticks, dropout=dropout, max_ticks=12)
    env = RoverEnv(config)
    observation, _ = env.reset(seed=11)
    for _ in range(12):
        original = prepare_request(observation, config=config)
        compact = compact_request_draft(original, float32_rows=float32_rows)
        assert expand_compact_state(compact["state"]) == original["state"]
        assert compact["option_order"] == original["option_order"]
        observation, _, _, _, _ = env.step([0.2, 0.1])


def test_compact_float32_rows_are_exact_and_fallback_without_precision_loss(sample):
    config, observation = sample
    request = prepare_request(observation, config=config)
    payload = json.loads(request["state"])
    exact = [
        0.6000000238418579,
        -0.0,
        float(np.finfo(np.float32).smallest_subnormal),
        float(np.finfo(np.float32).max),
    ]
    nonrepresentable = [1.0000000000000002, 1e-300, 1e300, 0.0]
    payload["module_observation"]["history_ego"][0] = exact
    payload["module_observation"]["history_ego"][1] = nonrepresentable
    request["state"] = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    original = deepcopy(request)
    compact = compact_request_draft(request, float32_rows=True)
    encoded = json.loads(compact["state"])
    assert (
        expand_compact_state(
            compact["state"],
            expected_sha256=compact["representation"]["original_state_sha256"],
        )
        == request["state"]
    )
    assert {"f32": ["0.6", "-0", "1e-45", "3.4028235e+38"]} in encoded["row_table"]
    assert nonrepresentable in encoded["row_table"]
    assert compact["representation"]["schema"].endswith("row-f32-draft/1")
    assert not compact["representation"]["live_use_approved"]
    assert request == original
    assert json.loads(compact_request_draft(request)["state"])["schema"].endswith(
        "row-draft/1"
    )


@pytest.mark.parametrize("bad_value", ["nan", "inf", "not-a-number", 0.6])
def test_compact_float32_decoder_rejects_invalid_typed_rows(sample, bad_value):
    config, observation = sample
    compact = compact_request_draft(
        prepare_request(observation, config=config), float32_rows=True
    )
    payload = json.loads(compact["state"])
    row = next(row for row in payload["row_table"] if isinstance(row, dict))
    row["f32"][0] = bad_value
    with pytest.raises(ValueError):
        expand_compact_state(json.dumps(payload))


@pytest.mark.parametrize(
    "defect",
    ["negative", "boolean", "out_of_range", "schema", "value", "double_compact"],
)
def test_compact_draft_rejects_bad_references_and_identity_mismatches(sample, defect):
    config, observation = sample
    compact = compact_request_draft(prepare_request(observation, config=config))
    payload = json.loads(compact["state"])
    if defect == "double_compact":
        with pytest.raises(ValueError, match="canonical full-state"):
            compact_request_draft(compact)
        return
    if defect in ("negative", "boolean", "out_of_range"):
        payload["module_observation"]["tof_m"][0] = {
            "negative": -1,
            "boolean": True,
            "out_of_range": len(payload["row_table"]),
        }[defect]
    elif defect == "schema":
        payload["schema"] = "unknown"
    else:
        payload["host_state"]["sequence"] += 1
    with pytest.raises(ValueError):
        expand_compact_state(
            json.dumps(payload),
            expected_sha256=compact["representation"]["original_state_sha256"],
        )


def test_render_rejects_wire_mismatch(sample):
    from dataclasses import replace

    config, observation = sample
    state = replace(state_from_observation(observation), sequence=123)
    with pytest.raises(ValueError, match="disagree"):
        prepare_request(observation, config=config, state_frame=encode_state(state))


@pytest.mark.parametrize(
    "defect", ["missing", "shape", "mask", "current", "padding", "nan"]
)
def test_render_rejects_invalid_history(sample, defect):
    config, observation = sample
    if defect == "missing":
        del observation["history_ego"]
    elif defect == "shape":
        observation["history_ego"] = np.zeros((1, 4))
    elif defect == "mask":
        observation["history_valid"] = observation["history_valid"].astype(int)
    elif defect == "current":
        observation["history_ego"][-1, 0] = 0.1
    elif defect == "padding":
        observation["history_ego"][0, 0] = 0.1
    else:
        observation["history_ego"][0, 0] = np.nan
    with pytest.raises(ValueError):
        prepare_request(observation, config=config)


class FakeTeacher:
    def __init__(self, fail_on=None):
        self.calls = 0
        self.fail_on = fail_on

    def system_one(self, *, state, questions):
        self.calls += 1
        if self.calls == self.fail_on:
            raise RuntimeError("simulated interruption")
        options = list(questions["mode"]["criteria"])
        return {
            "answers": {
                "mode": {
                    "type": "choice",
                    "probabilities": dict(
                        zip(options, [0.1, 0.2, 0.3, 0.15, 0.25], strict=True)
                    ),
                }
            },
            "usage": {"fake": True},
        }


@pytest.fixture
def fake_identity():
    return {
        "kind": "fake_test_only",
        "model_id": "test/fake",
        "revision": "0" * 40,
        "artifact_sha256": "1" * 64,
        "settings": {"temperature": 1.0, "token_budget": 2048},
    }


def test_cache_reuse_preserves_full_precision_and_fake_scope(
    sample, fake_identity, tmp_path
):
    config, observation = sample
    request = prepare_request(observation, config=config)
    teacher = FakeTeacher()
    path = tmp_path / "labels.sqlite3"
    with LabelCache(path) as cache:
        first, repeated = list(
            label_requests(
                [request, request], teacher=teacher, identity=fake_identity, cache=cache
            )
        )
        assert not first["cache_hit"] and repeated["cache_hit"]
        assert first["record"] == repeated["record"]
        assert (
            list(repeated["record"]["request"]["questions"]["mode"]["criteria"])
            == request["option_order"]["mode"]
        )
        assert teacher.calls == 1
        record = first["record"]
        assert record["synthetic"] and not record["training_approved"]
        assert record["answers"]["mode"]["human_review_required"]
        assert record["answers"]["mode"]["probabilities"] == [0.1, 0.2, 0.3, 0.15, 0.25]
    with LabelCache(path) as cache:
        assert next(
            label_requests(
                [request], teacher=teacher, identity=fake_identity, cache=cache
            )
        )["cache_hit"]
    assert teacher.calls == 1


@pytest.mark.parametrize("first_cached", [False, True])
def test_returned_records_cannot_mutate_batch_identity(
    sample, fake_identity, tmp_path, first_cached
):
    config, observation = sample
    request = prepare_request(observation, config=config)
    following = deepcopy(request)
    following["state"] += " "
    expected_identity = deepcopy(fake_identity)
    teacher = FakeTeacher()
    with LabelCache(tmp_path / "cache.sqlite3") as cache:
        if first_cached:
            list(
                label_requests(
                    [request], teacher=teacher, identity=fake_identity, cache=cache
                )
            )
        batch = label_requests(
            [request, following, following],
            teacher=teacher,
            identity=fake_identity,
            cache=cache,
        )
        first = next(batch)
        assert first["cache_hit"] is first_cached
        first["record"]["teacher"]["settings"]["temperature"] = 0.25
        second = next(batch)
        assert second["record"]["teacher"] == expected_identity
        second["record"]["teacher"]["settings"]["token_budget"] = 1
        third = next(batch)
        assert third["cache_hit"]
        assert third["record"]["teacher"] == expected_identity
        assert cache.get(first["record"]["cache_key"])["teacher"] == expected_identity
        assert cache.get(second["record"]["cache_key"])["teacher"] == expected_identity
    assert teacher.calls == 2
    assert fake_identity == expected_identity


@pytest.mark.parametrize(
    "change", ["revision", "weights", "settings", "state", "options"]
)
def test_cache_identity_covers_revision_settings_inputs_and_option_order(
    sample, fake_identity, tmp_path, change
):
    config, observation = sample
    request = prepare_request(observation, config=config)
    teacher = FakeTeacher()
    with LabelCache(tmp_path / "cache.sqlite3") as cache:
        first = next(
            label_requests(
                [request], teacher=teacher, identity=fake_identity, cache=cache
            )
        )
        if change == "revision":
            fake_identity["revision"] = "2" * 40
        elif change == "weights":
            fake_identity["artifact_sha256"] = "3" * 64
        elif change == "settings":
            fake_identity["settings"]["temperature"] = 0.9
        elif change == "state":
            request["state"] += " "
        else:
            options = list(reversed(request["option_order"]["mode"]))
            request["option_order"]["mode"] = options
            request["questions"]["mode"]["criteria"] = dict.fromkeys(options)
        second = next(
            label_requests(
                [request], teacher=teacher, identity=fake_identity, cache=cache
            )
        )
        assert not second["cache_hit"] and teacher.calls == 2
        assert first["record"]["cache_key"] != second["record"]["cache_key"]


def test_interrupted_batch_resumes_without_relabeling_completed_entries(
    sample, fake_identity, tmp_path
):
    config, observation = sample
    first = prepare_request(observation, config=config)
    second = deepcopy(first)
    second["state"] += " "
    teacher = FakeTeacher(fail_on=2)
    path = tmp_path / "resume.sqlite3"
    with LabelCache(path) as cache, pytest.raises(RuntimeError, match="interruption"):
        list(
            label_requests(
                [first, second], teacher=teacher, identity=fake_identity, cache=cache
            )
        )
    with LabelCache(path) as cache:
        results = list(
            label_requests(
                [first, second], teacher=teacher, identity=fake_identity, cache=cache
            )
        )
        assert [result["cache_hit"] for result in results] == [True, False]
    assert teacher.calls == 3


@pytest.mark.parametrize("defect", ["nan", "sum", "option", "type", "error"])
def test_invalid_fake_response_never_enters_cache(
    sample, fake_identity, tmp_path, defect
):
    from types import SimpleNamespace

    config, observation = sample
    request = prepare_request(observation, config=config)
    response = FakeTeacher().system_one(
        state=request["state"], questions=request["questions"]
    )
    answer = response["answers"]["mode"]
    if defect == "nan":
        answer["probabilities"]["explore"] = float("nan")
    elif defect == "sum":
        answer["probabilities"]["explore"] = 0.5
    elif defect == "option":
        answer["probabilities"]["unknown"] = answer["probabilities"].pop("explore")
    elif defect == "type":
        answer["type"] = "noul"
    else:
        answer["error"] = "rejected"
    teacher = SimpleNamespace(system_one=lambda **kwargs: response)
    with LabelCache(tmp_path / "cache.sqlite3") as cache:
        with pytest.raises(ValueError):
            list(
                label_requests(
                    [request], teacher=teacher, identity=fake_identity, cache=cache
                )
            )
        assert (
            cache.connection.execute("SELECT count(*) FROM labels").fetchone()[0] == 0
        )


def test_real_teacher_identity_is_rejected_before_any_call(
    sample, fake_identity, tmp_path
):
    config, observation = sample
    fake_identity["kind"] = "live"
    teacher = FakeTeacher()
    with (
        LabelCache(tmp_path / "cache.sqlite3") as cache,
        pytest.raises(ValueError, match="fake-test"),
    ):
        list(
            label_requests(
                [prepare_request(observation, config=config)],
                teacher=teacher,
                identity=fake_identity,
                cache=cache,
            )
        )
    assert teacher.calls == 0


def test_cache_detects_corruption_and_refuses_unrelated_databases(
    sample, fake_identity, tmp_path
):
    import sqlite3

    config, observation = sample
    request = prepare_request(observation, config=config)
    with LabelCache(tmp_path / "cache.sqlite3") as cache:
        result = next(
            label_requests(
                [request], teacher=FakeTeacher(), identity=fake_identity, cache=cache
            )
        )
        cache.connection.execute("UPDATE labels SET payload='{}'")
        with pytest.raises(ValueError, match="checksum"):
            cache.get(result["record"]["cache_key"])
    path = tmp_path / "unrelated.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE unrelated (value TEXT)")
    with pytest.raises(ValueError, match="refusing"):
        LabelCache(path)


@pytest.mark.parametrize("wire", [False, True])
def test_episode_plan_and_fake_label_cache_end_to_end(tmp_path, fake_identity, wire):
    import hashlib

    config = Config(max_ticks=2)
    records, _ = rollout(RoverEnv(config))
    if wire:
        records = with_wire_frames(records)
    path = tmp_path / "episode.jsonl"
    write_episode(path, records)
    original = path.read_bytes()
    plan = plan_episode(path)
    assert plan["request_count"] == 3 and plan["live_teacher_calls"] == 0
    assert not plan["training_approved"] and not plan["token_budget_verified"]
    assert plan == plan_episode(path)
    assert len(list(episode_requests(path, limit=1))) == 1
    for tick, request in enumerate(plan["requests"]):
        source = request["source"]
        assert source["episode_sha256"] == hashlib.sha256(original).hexdigest()
        assert source["tick"] == tick and source["line"] == tick + 1
        assert source["frame_origin"].startswith("embedded" if wire else "synthesized")
        assert (
            "ground_truth" not in request["state"]
            and "simulation_label" not in request["state"]
        )
    teacher = FakeTeacher()
    with LabelCache(tmp_path / "cache.sqlite3") as cache:
        first = list(
            label_requests(
                plan["requests"], teacher=teacher, identity=fake_identity, cache=cache
            )
        )
        second = list(
            label_requests(
                episode_requests(path),
                teacher=teacher,
                identity=fake_identity,
                cache=cache,
            )
        )
        assert not any(result["cache_hit"] for result in first)
        assert all(result["cache_hit"] for result in second)
        assert teacher.calls == 3
    assert path.read_bytes() == original


@pytest.mark.parametrize("defect", ["metadata", "wire", "missing_wire", "tick"])
def test_episode_plan_rejects_invalid_inputs(tmp_path, defect):
    records, _ = rollout(RoverEnv(Config(max_ticks=1)))
    records = with_wire_frames(records)
    if defect == "metadata":
        records[0]["schema"] = "unknown"
    elif defect == "wire":
        records[1]["state_frame_hex"] = records[0]["state_frame_hex"]
    elif defect == "missing_wire":
        del records[1]["state_frame_hex"]
    else:
        records[1]["observation"]["tick"] = 3
    path = tmp_path / "invalid.jsonl"
    write_episode(path, records)
    with pytest.raises(ValueError):
        plan_episode(path)


def test_plan_cli_is_bounded_model_free_and_exclusive(tmp_path, monkeypatch, capsys):
    records, _ = rollout(RoverEnv(Config(max_ticks=1)))
    episode = tmp_path / "episode.jsonl"
    output = tmp_path / "plan.json"
    write_episode(episode, records)
    monkeypatch.setattr(
        "sys.argv",
        [
            "label_pipeline",
            "--episode",
            str(episode),
            "--output",
            str(output),
            "--limit",
            "1",
        ],
    )
    main()
    summary = json.loads(capsys.readouterr().out)
    plan = json.loads(output.read_text())
    assert summary["request_count"] == 1 and summary["live_teacher_calls"] == 0
    assert (
        list(plan["requests"][0]["questions"]["mode"]["criteria"])
        == plan["requests"][0]["option_order"]["mode"]
    )
    with pytest.raises(FileExistsError):
        main()
