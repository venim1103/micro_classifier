import json
import math
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from sim.labels import draft_catalogue, draft_labels, stopping_envelope
from sim.rover import (
    Config,
    RoverEnv,
    Scenario,
    ScriptedExpert,
    integrate,
    json_value,
    make_scenario,
    ray_ranges,
    rollout,
    state_from_observation,
    swept_collision,
    with_wire_frames,
    write_episode,
)


def test_draft_catalogue_matches_wire_types_options_and_review_gate():
    from interface.protocol import CATALOGUE_VERSION, QUESTIONS, QuestionId

    catalogue = draft_catalogue()
    assert catalogue["catalogue_version"] == CATALOGUE_VERSION
    assert catalogue["review_status"] == "unreviewed_draft"
    assert catalogue["allowed_use"] == "tooling_and_unit_tests_only"
    assert not catalogue["physical_safety_claim"]
    assert len(catalogue["questions"]) == len(QUESTIONS)
    for row in catalogue["questions"]:
        identity = QuestionId(row["id"])
        kind, options = QUESTIONS[identity]
        assert (row["name"], row["type"], row["options"]) == (
            identity.name.lower(),
            kind.name.lower(),
            list(options),
        )


def test_draft_envelope_matches_config_arithmetic_and_age_monotonicity():
    config = Config()
    assert stopping_envelope(0.6, 0.1, config) == pytest.approx(0.45)
    assert stopping_envelope(0, 0.1, config) == config.radius
    assert stopping_envelope(0.6, 0.15, config) > stopping_envelope(0.6, 0.1, config)
    assert stopping_envelope(0.3, 0.1, config) < stopping_envelope(0.6, 0.1, config)


@pytest.mark.parametrize(
    "speed,age",
    [(-1, 0), (1, 0), (0, -1), (float("nan"), 0), (0, float("inf")), (True, 0)],
)
def test_draft_envelope_rejects_invalid_values(speed, age):
    with pytest.raises((TypeError, ValueError)):
        stopping_envelope(speed, age, Config())


@pytest.fixture
def draft_observation():
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset(seed=5)
    observation["tof_m"] = np.full((8, 8), 2.0)
    return config, observation


def test_draft_clear_observation_is_serializable_and_unreviewed(draft_observation):
    config, observation = draft_observation
    result = draft_labels(observation, config)
    assert result["review_status"] == "unreviewed_draft"
    assert not result["training_approved"] and not result["physical_safety_claim"]
    assert result["answers"]["path_blocked"]["value"] == "false"
    assert result["answers"]["clear_sector"]["value"] == "centre"
    assert result["answers"]["speed_tier"]["value"] == "3"
    assert result["answers"]["mode"]["value"] is None
    assert result["answers"]["mode"]["reason"] == "human_review_required"
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    assert draft_labels(observation, config) == result


@pytest.mark.parametrize(
    "offset,blocked", [(0, "true"), (-1e-6, "true"), (1e-6, "false")]
)
def test_draft_obstacle_boundary_is_inclusive(draft_observation, offset, blocked):
    config, observation = draft_observation
    observation["ego"] = np.array([0.3, 0, 4, 0])
    boundary = stopping_envelope(0.3, 0, config)
    observation["tof_m"][:, 3:5] = boundary + offset
    assert (
        draft_labels(observation, config)["answers"]["path_blocked"]["value"] == blocked
    )


@pytest.mark.parametrize("tier", [0, 1, 2, 3])
def test_draft_speed_tiers_have_config_relative_meanings(draft_observation, tier):
    config, observation = draft_observation
    boundary = stopping_envelope(config.max_speed * tier / 3, 0, config)
    observation["tof_m"][:, 3:5] = boundary + 1e-6
    assert draft_labels(observation, config)["answers"]["speed_tier"]["value"] == str(
        tier
    )


def test_draft_sector_orientation_ties_and_none_are_distinct(draft_observation):
    config, observation = draft_observation
    observation["tof_m"][:, 3:] = 1
    assert (
        draft_labels(observation, config)["answers"]["clear_sector"]["value"] == "left"
    )
    observation["tof_m"][:, 5:] = 3
    assert (
        draft_labels(observation, config)["answers"]["clear_sector"]["value"] == "right"
    )
    observation["tof_m"][:] = 0.1
    assert (
        draft_labels(observation, config)["answers"]["clear_sector"]["value"] == "none"
    )


def test_draft_partial_masks_do_not_invent_clearance(draft_observation):
    config, observation = draft_observation
    observation["tof_valid"][0, 0] = False
    observation["tof_m"][0, 0] = 0
    assert (
        draft_labels(observation, config)["answers"]["clear_sector"]["value"]
        == "centre"
    )
    observation["tof_valid"][:, 0] = False
    observation["tof_m"][:, 0] = 0
    answers = draft_labels(observation, config)["answers"]
    assert answers["clear_sector"]["value"] is None
    assert answers["path_blocked"]["value"] == "false"
    assert answers["speed_tier"]["value"] == "3"
    observation["tof_valid"][:, 3] = False
    observation["tof_m"][:, 3] = 0
    answers = draft_labels(observation, config)["answers"]
    assert answers["path_blocked"]["value"] is None
    assert answers["speed_tier"]["value"] is None


def test_draft_warmup_and_stale_samples_abstain(draft_observation):
    warmup, _ = RoverEnv().reset()
    result = draft_labels(warmup)
    assert all(answer["value"] is None for answer in result["answers"].values())
    config, observation = draft_observation
    observation["tick"] = 2
    observation["tof_age_s"] = 2 * config.dt
    result = draft_labels(observation, config)
    assert result["answers"]["path_blocked"]["reason"] == "stale_tof"


def test_draft_ignores_privileged_fields_and_never_mutates_inputs(draft_observation):
    config, observation = draft_observation
    original = deepcopy(observation)
    first = draft_labels(observation, config)
    np.testing.assert_equal(observation, original)
    observation.update(
        ground_truth={"collision": True}, expert_action=[0, 1], future=[42]
    )
    observation["history_ego"][:] = 1000
    assert draft_labels(observation, config) == first


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema", "unknown"),
        ("tick", True),
        ("tof_sample_tick", 1),
        ("tof_age_s", 0.1),
        ("ego", [float("nan"), 0, 0, 0]),
        ("ego", [1, 0, 0, 0]),
        ("tof_m", np.full((8, 8), -1)),
        ("tof_m", np.full((8, 8), float("inf"))),
        ("tof_valid", np.ones((8, 8))),
    ],
)
def test_draft_rejects_malformed_observations(draft_observation, field, value):
    config, observation = draft_observation
    observation[field] = value
    with pytest.raises(ValueError):
        draft_labels(observation, config)


def test_draft_accepts_simulator_float32_speed_limit(draft_observation):
    config, observation = draft_observation
    observation["ego"][0] = config.max_speed
    assert float(observation["ego"][0]) > config.max_speed
    assert draft_labels(observation, config)["answers"]["speed_tier"]["value"] == "3"


@pytest.mark.parametrize("tier", [1, 2, 3])
def test_draft_speed_boundary_requires_strict_clearance(draft_observation, tier):
    config, observation = draft_observation
    fraction = draft_catalogue()["rules"]["speed_fractions"][tier]
    observation["tof_m"][:, 3:5] = stopping_envelope(
        config.max_speed * fraction, 0, config
    )
    assert draft_labels(observation, config)["answers"]["speed_tier"]["value"] == str(
        tier - 1
    )


def test_draft_freshness_boundary_is_inclusive(draft_observation):
    config, observation = draft_observation
    observation["tick"] = 1
    observation["tof_age_s"] = config.dt
    assert (
        draft_labels(observation, config)["answers"]["path_blocked"]["value"] == "false"
    )


def test_draft_beyond_sensor_envelope_abstains_instead_of_claiming_blocked():
    config = Config(max_range=0.2, noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    observation["ego"][0] = config.max_speed
    result = draft_labels(observation, config)
    for name in ("path_blocked", "clear_sector", "speed_tier"):
        assert result["answers"][name]["value"] is None
        assert result["answers"][name]["reason"] == "envelope_outside_sensor_range"


def test_draft_config_and_input_provenance_change_independently(draft_observation):
    from dataclasses import replace

    config, observation = draft_observation
    first = draft_labels(observation, config)
    changed = draft_labels(observation, replace(config, radius=0.2))
    assert changed["config_sha256"] != first["config_sha256"]
    assert changed["input_sha256"] == first["input_sha256"]
    observation["tof_m"][0, 0] = 1
    changed = draft_labels(observation, config)
    assert changed["config_sha256"] == first["config_sha256"]
    assert changed["input_sha256"] != first["input_sha256"]
    assert changed["catalogue_sha256"] == first["catalogue_sha256"]
    assert changed["labeler_sha256"] == first["labeler_sha256"]


def test_draft_rejects_nonzero_invalid_cells_and_missing_fields(draft_observation):
    config, observation = draft_observation
    observation["tof_valid"][0, 0] = False
    with pytest.raises(ValueError, match="must contain zero"):
        draft_labels(observation, config)
    del observation["tof_m"]
    with pytest.raises(ValueError, match="missing required"):
        draft_labels(observation, config)


def test_rays_hit_nearest_obstacle_and_wall():
    ranges = ray_ranges(
        [1, 2],
        np.array([0, math.pi / 2, math.pi]),
        ((3, 2, 0.5), (4, 2, 0.5)),
        (6, 6),
        4,
    )
    assert ranges == pytest.approx([1.5, 4, 1])


def test_parallel_and_tangent_rays_remain_finite():
    ranges = ray_ranges([1, 2], np.array([0, math.pi / 2]), ((3, 3, 1),), (6, 6), 4)
    assert ranges == pytest.approx([2, 4])
    assert np.isfinite(ranges).all()


def test_swept_collision_prevents_tunneling_and_checks_arena_boundary():
    assert swept_collision([1, 2], [5, 2], 0.2, ((3, 2, 0.1),), (6, 6))
    assert not swept_collision([1, 1], [5, 1], 0.2, ((3, 2, 0.1),), (6, 6))
    assert swept_collision([1, 1], [0.1, 1], 0.2, (), (6, 6))


def test_constant_twist_integrates_straight_and_curved_motion():
    position, yaw = integrate([1, 1], 0, 1, 0, 1)
    assert position == pytest.approx([2, 1])
    assert yaw == 0
    position, yaw = integrate([1, 1], 0, 1, math.pi / 2, 1)
    assert position == pytest.approx([1 + 2 / math.pi, 1 + 2 / math.pi])
    assert yaw == pytest.approx(math.pi / 2)


def test_reset_is_seeded_with_stable_shapes_and_no_ground_truth_leak():
    env = RoverEnv()
    first, _ = env.reset(seed=4)
    second, _ = env.reset(seed=4)
    assert first.keys() == second.keys()
    for key in first:
        np.testing.assert_equal(first[key], second[key])
    assert first["tof_m"].shape == (8, 8)
    assert first["history_tof_m"].shape == (8, 8, 8)
    assert first["history_ego"].shape == (8, 4)
    assert first["history_valid"].sum() == 1
    assert "ground_truth" not in first


def test_latency_dropout_and_sensor_timestamp_are_explicit():
    env = RoverEnv(Config(noise_std=0, dropout=0, latency_ticks=2))
    observation, _ = env.reset()
    assert not observation["tof_valid"].any()
    assert observation["tof_sample_tick"] is None
    observation, *_ = env.step([0, 0])
    assert not observation["tof_valid"].any()
    observation, *_ = env.step([0, 0])
    assert observation["tof_valid"].all()
    assert observation["tof_sample_tick"] == 0
    assert observation["tof_age_s"] == pytest.approx(0.1)
    dropped, _ = RoverEnv(Config(dropout=1, latency_ticks=0)).reset()
    assert not dropped["tof_valid"].any()
    assert np.isfinite(dropped["tof_m"]).all()


def test_actions_are_bounded_and_invalid_action_does_not_advance():
    env = RoverEnv()
    with pytest.raises(ValueError, match="finite"):
        env.step([float("nan"), 0])
    assert env.tick == 0
    observation, *_ = env.step([100, 100])
    assert observation["ego"][0] == pytest.approx(
        env.config.acceleration * env.config.dt
    )
    assert observation["ego"][1] == pytest.approx(env.config.max_turn_rate)


def test_goal_timeout_collision_and_reset_semantics():
    env = RoverEnv(scenario=Scenario(goal=(1.1, 3)))
    _, reward, terminated, truncated, info = env.step([0, 0])
    assert terminated and not truncated and info["success"] and reward > 0
    with pytest.raises(RuntimeError, match="reset"):
        env.step([0, 0])
    env = RoverEnv(Config(max_ticks=1))
    _, _, terminated, truncated, info = env.step([0, 0])
    assert not terminated and truncated and info["timeout"]
    env = RoverEnv(
        Config(dt=1, max_speed=5, acceleration=100), Scenario(obstacles=((3, 3, 0.2),))
    )
    _, reward, terminated, _, info = env.step([5, 0])
    assert terminated and info["collision"] and reward < 0
    assert info["ground_truth"]["position_m"] == pytest.approx([1, 3])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"dt": 0},
        {"dropout": 2},
        {"latency_ticks": -1},
        {"history_ticks": 1.5},
        {"noise_std": float("nan")},
    ],
)
def test_invalid_simulation_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)


def test_episode_logs_are_reproducible_and_never_overwritten(tmp_path):
    env = RoverEnv(Config(max_ticks=3), make_scenario("obstacle", 5))
    env.reset(seed=5)
    records, summary = rollout(env)
    duplicate, _ = rollout(env)
    assert json.dumps(records, default=json_value) == json.dumps(
        duplicate, default=json_value
    )
    assert summary["timeout"] and summary["ticks"] == 3
    path = tmp_path / "episode.jsonl"
    write_episode(path, records)
    decoded = [json.loads(line) for line in path.read_text().splitlines()]
    assert decoded[0]["schema"] == "micro-classifier/sim-episode/1"
    assert len(decoded) == 5
    with pytest.raises(FileExistsError):
        write_episode(path, records)


def test_scripted_expert_reaches_clear_goal_and_handles_missing_sensor():
    env = RoverEnv()
    observation, _ = env.reset()
    assert np.array_equal(ScriptedExpert(env)(observation), [0, 0])
    _, summary = rollout(env)
    assert summary["success"] and not summary["collision"]


@pytest.mark.parametrize("name", ["clear", "obstacle", "corridor", "slalom"])
def test_scenarios_are_seeded_valid_and_roll_out_without_nonfinite_values(name):
    scenario = make_scenario(name, 12)
    assert scenario == make_scenario(name, 12)
    env = RoverEnv(Config(max_ticks=10), scenario)
    records, _ = rollout(env)
    json.dumps(records, default=json_value, allow_nan=False)


@pytest.mark.parametrize("name", ["obstacle", "slalom"])
def test_map_expert_completes_obstacle_scenarios_without_collision(name):
    records, summary = rollout(RoverEnv(scenario=make_scenario(name, 0)))
    assert records[0]["privileged_expert"]
    assert summary["success"] and not summary["collision"]


def test_wire_export_encodes_current_host_inputs_and_unknown_health():
    from interface.protocol import UINT32_MAX, decode_state, encode_state

    records, _ = rollout(RoverEnv(Config(max_ticks=3)))
    exported = with_wire_frames(records)
    assert exported[0]["wire_contract"]["state_frame_bytes"] == 92
    assert not exported[0]["wire_contract"]["decision_frames"]
    assert exported[0]["privileged_expert"]
    for original, entry in zip(records, exported, strict=True):
        assert "state_frame_hex" not in original
        assert "decision_frame_hex" not in entry
        if "observation" not in entry:
            assert "state_frame_hex" not in entry
            continue
        frame = bytes.fromhex(entry["state_frame_hex"])
        packet = decode_state(frame)
        observation = entry["observation"]
        assert packet.sequence == observation["tick"]
        assert packet.timestamp_us == round(observation["time_s"] * 1_000_000)
        assert packet.velocity_m_s == pytest.approx((observation["ego"][0], 0, 0))
        assert packet.angular_velocity_rad_s == pytest.approx(
            (0, 0, observation["ego"][1])
        )
        assert packet.goal_m == pytest.approx((*observation["goal_body_m"], 0))
        assert packet.validity == 7
        assert packet.ages_us == (0, 0, 0, UINT32_MAX, UINT32_MAX)
        assert packet.battery_fraction == packet.faults == 0
        assert encode_state(packet) == frame


def test_wire_state_excludes_truth_action_tof_and_history():
    records, _ = rollout(RoverEnv(Config(max_ticks=2)))
    changed = deepcopy(records)
    for record in changed:
        if "observation" in record:
            record["info"]["ground_truth"] = {"unrelated": 12345}
            observation = record["observation"]
            observation["tof_m"][:] = 99
            observation["history_ego"][:] = 99
            observation["tof_age_s"] = 99
        if "action" in record:
            record["action"][:] = 99
    original = with_wire_frames(records)
    altered = with_wire_frames(changed)
    assert [entry.get("state_frame_hex") for entry in original] == [
        entry.get("state_frame_hex") for entry in altered
    ]


def test_wire_log_export_is_reproducible_and_json_round_trips(tmp_path):
    from interface.protocol import decode_state

    records, _ = rollout(RoverEnv(Config(max_ticks=3)))
    first = with_wire_frames(records)
    second = with_wire_frames(records)
    assert json.dumps(first, default=json_value) == json.dumps(
        second, default=json_value
    )
    path = tmp_path / "wire.jsonl"
    write_episode(path, first)
    decoded = [json.loads(line) for line in path.read_text().splitlines()]
    assert decoded[0]["wire_contract"]["provisional"]
    assert len([row for row in decoded if "state_frame_hex" in row]) == 4
    for row in decoded:
        if "state_frame_hex" in row:
            decode_state(bytes.fromhex(row["state_frame_hex"]))
    with pytest.raises(FileExistsError):
        write_episode(path, second)


def test_wire_counters_wrap_without_losing_observation_timing():
    from interface.protocol import UINT32_MAX

    observation, _ = RoverEnv().reset()
    observation["tick"] = UINT32_MAX + 3
    observation["time_s"] = (UINT32_MAX + 101) / 1_000_000
    packet = state_from_observation(observation)
    assert packet.sequence == 2
    assert packet.timestamp_us == 100


@pytest.mark.parametrize(
    "changes", [{"tick": -1}, {"tick": True}, {"time_s": float("nan")}, {"ego": [0, 0]}]
)
def test_wire_export_rejects_invalid_observation(changes):
    observation, _ = RoverEnv().reset()
    observation.update(changes)
    with pytest.raises(ValueError):
        state_from_observation(observation)


def test_wire_cli_exports_real_frames(tmp_path, monkeypatch, capsys):
    from sim.rover import main

    config = tmp_path / "config.json"
    config.write_text(json.dumps({"max_ticks": 3}))
    monkeypatch.setattr(
        "sys.argv",
        ["sim.rover", "--wire", "--output", str(tmp_path), "--config", str(config)],
    )
    main()
    summary = json.loads(capsys.readouterr().out)
    assert summary["ticks"] == 3 and summary["timeout"]
    rows = [json.loads(line) for line in Path(summary["path"]).read_text().splitlines()]
    assert rows[0]["wire_contract"]["protocol_version"] == 0
    assert len(bytes.fromhex(rows[0]["state_frame_hex"])) == 92
