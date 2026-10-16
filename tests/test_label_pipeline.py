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


@pytest.mark.parametrize(("history_ticks", "dropout"), [(1, 0.0), (8, 0.25)])
def test_compact_roundtrip_through_warm_noisy_masked_history(history_ticks, dropout):
    config = Config(history_ticks=history_ticks, dropout=dropout, max_ticks=12)
    env = RoverEnv(config)
    observation, _ = env.reset(seed=11)
    for _ in range(12):
        original = prepare_request(observation, config=config)
        compact = compact_request_draft(original)
        assert expand_compact_state(compact["state"]) == original["state"]
        assert compact["option_order"] == original["option_order"]
        observation, _, _, _, _ = env.step([0.2, 0.1])


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
