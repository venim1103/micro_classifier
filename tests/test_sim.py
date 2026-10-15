import json
import math

import numpy as np
import pytest

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
    swept_collision,
    write_episode,
)


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
