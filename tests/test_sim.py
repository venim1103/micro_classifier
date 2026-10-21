import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from sim.labels import (
    answer_coverage,
    coverage_suite,
    draft_catalogue,
    draft_labels,
    smoke_suite,
    stopping_envelope,
    validate_observation,
)
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
    tof_directions,
    tof_ranges,
    with_wire_frames,
    write_episode,
)


def test_tof_floor_and_missing_returns_follow_synthetic_mount():
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    floor_distance = 0.15 / math.sin(config.field_of_view / 2)
    np.testing.assert_allclose(observation["tof_m"][-1], floor_distance, rtol=1e-6)
    assert observation["tof_valid"][-1].all()
    assert not observation["tof_valid"][0].any()
    assert not observation["tof_m"][0].any()


def test_tof_synthetic_rays_are_unit_length_and_pitch_is_positive_down():
    from dataclasses import replace

    config = Config()
    rays = tof_directions(0, config)
    np.testing.assert_allclose(np.linalg.norm(rays, axis=-1), 1, atol=1e-15)
    assert (rays[:, 0, 1] > 0).all() and (rays[:, -1, 1] < 0).all()
    assert (rays[0, :, 2] > 0).all() and (rays[-1, :, 2] < 0).all()
    down = tof_directions(0, replace(config, tof_mount_pitch=math.pi / 4))
    assert (down[..., 2] < 0).all()
    np.testing.assert_allclose(
        tof_directions(math.pi / 2, config)[..., 0], -rays[..., 1], atol=1e-15
    )


@pytest.mark.parametrize("side", [-1, 1])
def test_full_synthetic_history_can_hide_a_normal_cylinder_from_a_turning_sweep(side):
    from sim.navigation import evaluate_synthetic
    from teacher.label_pipeline import prepare_request

    config = Config(noise_std=0, dropout=0)
    speed, turn = 0.6, side * 1.5
    current_tick = 23
    scenes = [
        Scenario(start=(2, 2, 0), goal=(5, 2)),
        Scenario(
            start=(2, 2, 0), goal=(5, 2), obstacles=((2.3, 2 + side * 0.47, 0.3),)
        ),
    ]
    captures = (0, 2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20, 22, 23)
    rendered, references = [], []
    for scene in scenes:
        scene.validate(config)
        ego_history, tof_history, valid_history = [], [], []
        for tick in range(current_tick - config.history_ticks + 1, current_tick + 1):
            position, yaw = integrate(
                [2, 2], 0, speed, turn, (tick - current_tick) * config.dt
            )
            assert not swept_collision(
                position, position, config.radius, scene.obstacles, scene.bounds
            )
            delta = np.asarray(scene.goal) - position
            cosine, sine = math.cos(yaw), math.sin(yaw)
            ego_history.append(
                [
                    speed,
                    turn,
                    cosine * delta[0] + sine * delta[1],
                    -sine * delta[0] + cosine * delta[1],
                ]
            )
            sample_tick = max(
                capture
                for capture in captures
                if capture <= tick - config.latency_ticks
            )
            capture_position, capture_yaw = integrate(
                [2, 2], 0, speed, turn, (sample_tick - current_tick) * config.dt
            )
            ranges = tof_ranges(capture_position, capture_yaw, scene, config)
            valid = np.isfinite(ranges) & (ranges < config.max_range)
            tof_history.append(np.where(valid, ranges, 0).astype(np.float32))
            valid_history.append(valid)
        ego_history = np.asarray(ego_history, dtype=np.float32)
        tof_history = np.asarray(tof_history)
        valid_history = np.asarray(valid_history)
        observation = {
            "schema": "micro-classifier/sim-observation/1",
            "tick": current_tick,
            "time_s": current_tick * config.dt,
            "ego": ego_history[-1],
            "goal_body_m": ego_history[-1, 2:],
            "tof_m": tof_history[-1],
            "tof_valid": valid_history[-1],
            "tof_age_s": (current_tick - sample_tick) * config.dt,
            "tof_sample_tick": sample_tick,
            "history_ego": ego_history,
            "history_tof_m": tof_history,
            "history_tof_valid": valid_history,
            "history_valid": np.ones(config.history_ticks, dtype=bool),
        }
        rendered.append(prepare_request(observation, config=config)["state"])
        references.append(
            evaluate_synthetic(
                scene,
                speed=speed,
                turn_rate=turn,
                tof_age_s=observation["tof_age_s"],
                config=config,
                synthetic_test_only=True,
            )["answers"]["path_blocked"]
        )
    assert rendered[0] == rendered[1]
    assert references == ["false", "true"]


@pytest.mark.parametrize("side", [-1, 1])
def test_synthetic_c1_capture_distinguishes_normal_history_aliases(side):
    from sim.diagnostics import capture_synthetic_c1_views

    scene = Scenario(
        start=(2, 2, 0), goal=(5, 2), obstacles=((2.3, 2 + side * 0.47, 0.3),)
    )
    empty = Scenario(start=scene.start, goal=scene.goal)
    differences = 0
    for capture_tick in (14, 15, 16, 16, 18, 19, 20, 20):
        position, yaw = integrate(
            [2, 2], 0, 0.6, side * 1.5, (capture_tick - 23) * 0.05
        )
        settings = {
            "pose_m_rad": [*position, yaw],
            "capture_tick": capture_tick,
            "synthetic_test_only": True,
        }
        first = capture_synthetic_c1_views(empty, **settings)
        second = capture_synthetic_c1_views(scene, **settings)
        assert second["tof_m"].shape == (8, 8, 8)
        assert second["tof_m"].dtype == np.float32
        assert second["free_space_qualified"] is False
        assert second["training_approved"] is False
        assert "scenario" not in second
        differences += np.count_nonzero(
            (first["tof_m"] != second["tof_m"])
            | (first["tof_valid"] != second["tof_valid"])
        )
    assert differences == 317


@pytest.fixture
def c1_history():
    from sim.diagnostics import capture_synthetic_c1_views

    records = []
    for tick in (14, 15, 16, 16, 18, 19, 20, 20):
        position, yaw = integrate([2, 2], 0, 0.6, 0, (tick - 23) * 0.05)
        records.append(
            capture_synthetic_c1_views(
                Scenario(start=(2, 2, 0)),
                pose_m_rad=[*position, yaw],
                capture_tick=tick,
                synthetic_test_only=True,
            )
        )
    return records


def test_synthetic_c1_history_registers_without_qualifying_free_space(c1_history):
    from sim.diagnostics import inspect_synthetic_c1_history

    result = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        synthetic_test_only=True,
    )
    assert result["status"] == "registered_fixture"
    assert result["unique_capture_count"] == 6
    assert result["latest_age_ticks"] == 3
    assert result["free_space_qualified"] is False
    assert result["real_input_qualified"] is False
    valid = result["point_valid"].copy()
    assert result["points_body_m"].shape == (8, 8, 8, 3)
    assert np.all(result["points_body_m"][~valid] == 0)
    result["point_valid"][:] = False
    assert np.any(c1_history[-1]["tof_valid"])
    shifted = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[3, 2, 0],
        synthetic_test_only=True,
    )
    assert shifted["points_body_m"][valid, 0] == pytest.approx(
        result["points_body_m"][valid, 0] - 1
    )
    rotated = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, math.pi / 2],
        synthetic_test_only=True,
    )
    assert rotated["points_body_m"][valid, 0] == pytest.approx(
        result["points_body_m"][valid, 1]
    )
    assert rotated["points_body_m"][valid, 1] == pytest.approx(
        -result["points_body_m"][valid, 0]
    )


def test_synthetic_c1_preserves_the_complete_slender_alias(c1_history):
    from sim.diagnostics import capture_synthetic_c1_views
    from sim.navigation import evaluate_synthetic

    scene = Scenario(start=(2, 2, 0), goal=(5, 2), obstacles=((2.4, 2, 0.005),))
    for record in c1_history:
        other = capture_synthetic_c1_views(
            scene,
            pose_m_rad=record["capture_poses_m_rad"][0],
            capture_tick=int(record["capture_ticks"][0]),
            synthetic_test_only=True,
        )
        assert np.array_equal(record["tof_m"], other["tof_m"])
        assert np.array_equal(record["tof_valid"], other["tof_valid"])
    answers = [
        evaluate_synthetic(
            world,
            speed=0.6,
            turn_rate=0,
            tof_age_s=0.15,
            synthetic_test_only=True,
        )["answers"]["path_blocked"]
        for world in (Scenario(start=scene.start), scene)
    ]
    assert answers == ["false", "true"]


def test_synthetic_c1_downward_views_reveal_the_near_low_fixture():
    from sim.diagnostics import capture_synthetic_c1_views

    empty = Scenario(start=(2, 2, 0))
    scene = Scenario(
        start=empty.start, obstacles=((2.21, 2, 0.02),), obstacle_heights=(0.05,)
    )
    settings = {"pose_m_rad": [2, 2, 0], "capture_tick": 0, "synthetic_test_only": True}
    first = capture_synthetic_c1_views(empty, **settings)
    second = capture_synthetic_c1_views(scene, **settings)
    assert np.count_nonzero(first["tof_m"] != second["tof_m"]) == 4
    for index in range(8):
        assert np.array_equal(
            tof_ranges([2, 2], index * math.pi / 4, empty, Config()),
            tof_ranges([2, 2], index * math.pi / 4, scene, Config()),
        )


def test_synthetic_c1_masks_ranges_rounding_to_the_ceiling(monkeypatch):
    from sim.diagnostics import capture_synthetic_c1_views

    monkeypatch.setattr(
        "sim.diagnostics.tof_ranges",
        lambda *args: np.full((8, 8), np.nextafter(4.0, 0)),
    )
    record = capture_synthetic_c1_views(
        Scenario(),
        pose_m_rad=[2, 2, 0],
        capture_tick=0,
        synthetic_test_only=True,
    )
    assert not np.any(record["tof_valid"])
    assert np.all(record["tof_m"] == 0)


@pytest.mark.parametrize(
    "field,value",
    [
        ("noise_std", 0.02),
        ("dropout", 0.02),
        ("odometry_position_error", 0.02),
        ("odometry_heading_error", 0.01),
        ("odometry_latency_ticks", 1),
        ("tof_mount_height", None),
        ("field_of_view", math.pi / 3),
        ("tof_rate_hz", None),
        ("latency_ticks", 1),
        ("dt", 0.1),
        ("history_ticks", 4),
    ],
)
def test_synthetic_c1_rejects_unqualified_profiles(field, value):
    from sim.diagnostics import capture_synthetic_c1_views

    config = Config(**{"noise_std": 0, "dropout": 0, field: value})
    with pytest.raises(ValueError, match="profile"):
        capture_synthetic_c1_views(
            Scenario(),
            pose_m_rad=[2, 2, 0],
            capture_tick=0,
            config=config,
            synthetic_test_only=True,
        )


@pytest.mark.parametrize(
    "pose,tick",
    [
        ([2, 2, np.nan], 0),
        ([2, 2, np.inf], 0),
        ([2, 2], 0),
        ([True, False, True], 0),
        ([2, 2, 10**400], 0),
        ([True, 2, 0], 0),
        ([2, 2, 0], True),
        ([2, 2, 0], -1),
        ([2, 2, 0], 2**32),
        ([2, 2, 0], 1),
    ],
)
def test_synthetic_c1_capture_rejects_malformed_pose_or_tick(pose, tick):
    from sim.diagnostics import capture_synthetic_c1_views

    with pytest.raises(ValueError):
        capture_synthetic_c1_views(
            Scenario(),
            pose_m_rad=pose,
            capture_tick=tick,
            synthetic_test_only=True,
        )


@pytest.mark.parametrize(
    "fault",
    [
        "schema",
        "scope",
        "extra_truth",
        "config",
        "view_tick",
        "view_pose",
        "range_nan",
        "range_ceiling",
        "mask_type",
        "shape",
        "held_changed",
        "empty",
        "too_many",
        "old",
        "future",
        "off_cadence",
        "no_support",
    ],
)
def test_synthetic_c1_history_rejects_unsupported_evidence(c1_history, fault):
    from sim.diagnostics import inspect_synthetic_c1_history

    record = c1_history[-1]
    if fault == "schema":
        record["schema"] = "micro-classifier/sim-observation/1"
    elif fault == "scope":
        record["free_space_qualified"] = 0
    elif fault == "extra_truth":
        record["scenario"] = {}
    elif fault == "config":
        record["config"]["noise_std"] = 0.02
    elif fault == "view_tick":
        record["capture_ticks"][0] += 1
    elif fault == "view_pose":
        record["capture_poses_m_rad"][0, 0] += 0.1
    elif fault == "range_nan":
        record["tof_m"][0, 0, 0] = np.nan
    elif fault == "range_ceiling":
        record["tof_valid"][0, 0, 0] = True
        record["tof_m"][0, 0, 0] = 4
    elif fault == "mask_type":
        record["tof_valid"] = record["tof_valid"].astype(np.uint8)
    elif fault == "shape":
        record["tof_m"] = record["tof_m"][0]
    elif fault == "held_changed":
        row, column = np.argwhere(record["tof_valid"][0])[0]
        record["tof_m"][0, row, column] += np.float32(0.001)
    elif fault == "empty":
        c1_history.clear()
    elif fault == "too_many":
        c1_history.append(record)
    elif fault == "old":
        c1_history = [c1_history[0]]
    elif fault == "future":
        c1_history = [record]
        record["capture_ticks"][:] = 23
    elif fault == "off_cadence":
        c1_history = [record]
        record["capture_ticks"][:] = 21
    elif fault == "no_support":
        c1_history = [record]
        record["tof_valid"][:] = False
        record["tof_m"][:] = 0
    result = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["points_body_m"] is None
    assert result["free_space_qualified"] is False


@pytest.mark.parametrize("opt_in", [False, None, 1, "true"])
def test_synthetic_c1_requires_explicit_opt_in(opt_in):
    from sim.diagnostics import capture_synthetic_c1_views, inspect_synthetic_c1_history

    with pytest.raises(ValueError, match="synthetic_test_only"):
        capture_synthetic_c1_views(
            object(), pose_m_rad=None, capture_tick=None, synthetic_test_only=opt_in
        )
    with pytest.raises(ValueError, match="synthetic_test_only"):
        inspect_synthetic_c1_history(
            object(),
            reference_tick=None,
            reference_pose_m_rad=None,
            synthetic_test_only=opt_in,
        )


@pytest.mark.parametrize("config", [False, 0, {}, "ideal"])
def test_synthetic_c1_rejects_non_config_arguments(config):
    from sim.diagnostics import capture_synthetic_c1_views

    with pytest.raises(ValueError, match="Config instance"):
        capture_synthetic_c1_views(
            Scenario(),
            pose_m_rad=[2, 2, 0],
            capture_tick=0,
            config=config,
            synthetic_test_only=True,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("reference_tick", True),
        ("reference_tick", -1),
        ("reference_tick", 2**32),
        ("max_age_ticks", True),
        ("max_age_ticks", -1),
        ("max_age_ticks", 9),
        ("reference_pose_m_rad", [2, 2, np.nan]),
        ("reference_pose_m_rad", [True, 2, 0]),
    ],
)
def test_synthetic_c1_rejects_malformed_reference(c1_history, field, value):
    from sim.diagnostics import inspect_synthetic_c1_history

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "synthetic_test_only": True,
        field: value,
    }
    with pytest.raises(ValueError):
        inspect_synthetic_c1_history(c1_history, **settings)


def test_synthetic_c1_is_not_a_normal_input(c1_history):
    from teacher.label_pipeline import prepare_request

    assert Config().tof_mount_pitch == 0
    assert Config().noise_std == 0.02
    assert Config().history_ticks == 8
    with pytest.raises(ValueError):
        prepare_request(c1_history[-1], config=Config())


def test_synthetic_c1_low_segments_stop_before_surfaces(c1_history):
    from sim.diagnostics import _c1_low_free_segments, inspect_synthetic_c1_history

    result = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        synthetic_test_only=True,
    )
    config = Config(**c1_history[-1]["config"])
    segments, guard = _c1_low_free_segments(
        c1_history[-1],
        result,
        [2, 2, 0],
        config,
    )
    assert len(segments) > 0
    assert segments.shape[1:] == (2, 3)
    assert np.all(segments[..., 2] > 0)
    assert np.all(segments[..., 2] < 0.05)
    assert np.all(segments[:, 0, 2] > segments[:, 1, 2])
    assert guard > 0
    shifted = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[3, 2, 0],
        synthetic_test_only=True,
    )
    other, _ = _c1_low_free_segments(c1_history[-1], shifted, [3, 2, 0], config)
    assert other[..., 0] == pytest.approx(segments[..., 0] - 1)
    assert other[..., 1:] == pytest.approx(segments[..., 1:])


def test_synthetic_c1_enclosure_excludes_empty_straight_fixture(c1_history):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    result = probe_synthetic_c1_enclosure(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "excluded_under_fixture_assumptions", result
    assert result["fixture_enclosure_excluded"] is True
    assert result["sweep_enclosure_radius_m"] == pytest.approx(0.48)
    assert result["cells_checked"] <= 32768
    assert result["free_space_qualified"] is False
    assert result["numerically_certified"] is False


@pytest.mark.parametrize("radius", [0.05, 0.30])
@pytest.mark.parametrize("height", [0.05, 1.0])
@pytest.mark.parametrize("turn", [-1.5, 0, 1.5])
def test_synthetic_c1_enclosure_never_clears_blocked_envelope_fixtures(
    radius, height, turn
):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    scene = Scenario(
        start=(2, 2, 0),
        goal=(5, 2),
        obstacles=((2.2 + radius, 2, radius),),
        obstacle_heights=(height,),
    )
    records = []
    for tick in (14, 15, 16, 16, 18, 19, 20, 20):
        position, yaw = integrate([2, 2], 0, 0.6, turn, (tick - 23) * 0.05)
        records.append(
            capture_synthetic_c1_views(
                scene,
                pose_m_rad=[*position, yaw],
                capture_tick=tick,
                synthetic_test_only=True,
            )
        )
    reference = evaluate_synthetic(
        scene,
        speed=0.6,
        turn_rate=turn,
        tof_age_s=0.15,
        synthetic_test_only=True,
    )
    assert reference["answers"]["path_blocked"] == "true"
    result = probe_synthetic_c1_enclosure(
        records,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown"
    assert result["fixture_enclosure_excluded"] is False
    assert result["cells_checked"] <= 32768
    from sim.diagnostics import _c1_low_free_segments, inspect_synthetic_c1_history

    inspected = inspect_synthetic_c1_history(
        records,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        synthetic_test_only=True,
    )
    segments, _ = _c1_low_free_segments(
        records[-1],
        inspected,
        [2, 2, 0],
        Config(**records[-1]["config"]),
    )
    center = np.array([0.2 + radius, 0])
    for start, end in segments[..., :2]:
        step = end - start
        fraction = np.clip(np.dot(center - start, step) / np.dot(step, step), 0, 1)
        assert np.linalg.norm(center - start - fraction * step) > radius


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("max_cells", 0, "cell_budget_exhausted"),
        ("max_depth", 0, "unexcluded_center_cell"),
        ("current_body_clear", False, "current_body_clear_not_established"),
        ("current_body_clear", 1, "current_body_clear_not_established"),
        ("current_body_clear", "true", "current_body_clear_not_established"),
        ("controlled_envelope", False, "controlled_envelope_not_established"),
        ("controlled_envelope", 1, "controlled_envelope_not_established"),
        ("controlled_envelope", "true", "controlled_envelope_not_established"),
        ("reference_pose_m_rad", [3, 2, 0], "unsupported_capture_to_reference_motion"),
    ],
)
def test_synthetic_c1_enclosure_preserves_unknown_on_missing_support(
    c1_history, field, value, reason
):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "speed": 0.6,
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
        field: value,
    }
    result = probe_synthetic_c1_enclosure(c1_history, **settings)
    assert result["status"] == "unknown"
    assert result["reason"] == reason
    assert result["fixture_enclosure_excluded"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("speed", True),
        ("speed", np.nan),
        ("speed", np.inf),
        ("speed", -0.1),
        ("speed", 0.7),
        ("max_cells", True),
        ("max_cells", -1),
        ("max_cells", 65537),
        ("max_depth", True),
        ("max_depth", -1),
        ("max_depth", 13),
        ("radius_bands", True),
        ("radius_bands", 0),
        ("radius_bands", 17),
        ("synthetic_test_only", 1),
        ("synthetic_test_only", False),
    ],
)
def test_synthetic_c1_enclosure_rejects_malformed_controls(c1_history, field, value):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "speed": 0.6,
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
        field: value,
    }
    with pytest.raises(ValueError):
        probe_synthetic_c1_enclosure(c1_history, **settings)


def test_synthetic_c1_enclosure_does_not_attest_the_object_domain(c1_history):
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure

    outside_domain = Scenario(start=(2, 2, 0), obstacles=((2.4, 2, 0.005),))
    records = [
        capture_synthetic_c1_views(
            outside_domain,
            pose_m_rad=record["capture_poses_m_rad"][0],
            capture_tick=int(record["capture_ticks"][0]),
            synthetic_test_only=True,
        )
        for record in c1_history
    ]
    for original, other in zip(c1_history, records, strict=True):
        assert np.array_equal(original["tof_m"], other["tof_m"])
    result = probe_synthetic_c1_enclosure(
        records,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        speed=0.6,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["fixture_enclosure_excluded"] is True
    assert result["radius_interval_m"] == [0.05, 0.30]
    assert (
        result["assumptions"]["envelope_membership_independently_established"] is True
    )
    assert result["real_input_qualified"] is False
    assert result["free_space_qualified"] is False


def test_synthetic_c1_enclosure_keeps_stale_or_malformed_history_unknown(c1_history):
    from sim.diagnostics import probe_synthetic_c1_enclosure

    settings = {
        "reference_tick": 23,
        "reference_pose_m_rad": [2, 2, 0],
        "speed": 0.6,
        "current_body_clear": True,
        "controlled_envelope": True,
        "synthetic_test_only": True,
    }
    for records in ([], [c1_history[0]], c1_history * 2):
        result = probe_synthetic_c1_enclosure(records, **settings)
        assert result["status"] == "unknown"
        assert result["fixture_enclosure_excluded"] is False


def test_synthetic_c1_enclosure_cannot_clear_a_near_wall():
    from sim.diagnostics import capture_synthetic_c1_views, probe_synthetic_c1_enclosure
    from sim.navigation import evaluate_synthetic

    scene = Scenario(start=(5.7, 2, 0), goal=(4, 2))
    records = []
    for tick in (14, 15, 16, 16, 18, 19, 20, 20):
        position, yaw = integrate([5.7, 2], 0, 0.6, 0, (tick - 23) * 0.05)
        records.append(
            capture_synthetic_c1_views(
                scene,
                pose_m_rad=[*position, yaw],
                capture_tick=tick,
                synthetic_test_only=True,
            )
        )
    result = probe_synthetic_c1_enclosure(
        records,
        reference_tick=23,
        reference_pose_m_rad=scene.start,
        speed=0.6,
        current_body_clear=True,
        controlled_envelope=True,
        synthetic_test_only=True,
    )
    assert result["reason"] == "axis_aligned_wall_support_incomplete"
    assert result["fixture_enclosure_excluded"] is False
    assert (
        evaluate_synthetic(
            scene,
            speed=0.6,
            turn_rate=0,
            tof_age_s=0.15,
            synthetic_test_only=True,
        )["answers"]["path_blocked"]
        == "true"
    )


def test_synthetic_c1_enclosure_has_independent_sampled_center_support(c1_history):
    from sim.diagnostics import _c1_low_free_segments, inspect_synthetic_c1_history

    result = inspect_synthetic_c1_history(
        c1_history,
        reference_tick=23,
        reference_pose_m_rad=[2, 2, 0],
        synthetic_test_only=True,
    )
    segments, _ = _c1_low_free_segments(
        c1_history[-1],
        result,
        [2, 2, 0],
        Config(**c1_history[-1]["config"]),
    )
    checked = 0
    for radius in (0.05, 0.133, 0.30):
        for horizontal in np.linspace(-0.78, 0.78, 19):
            for vertical in np.linspace(-0.78, 0.78, 19):
                center = np.array([horizontal, vertical])
                distance = np.linalg.norm(center)
                if not 0.18 + radius < distance <= 0.48 + radius:
                    continue
                separations = []
                for start, end in segments[..., :2]:
                    step = end - start
                    fraction = np.clip(
                        np.dot(center - start, step) / np.dot(step, step), 0, 1
                    )
                    separations.append(np.linalg.norm(center - start - fraction * step))
                assert min(separations) < radius
                checked += 1
    assert checked > 100


def test_floor_rules_ignore_floor_without_claiming_calibrated_probabilities():
    from interface.protocol import QuestionId, Status, decode_decision, encode_decision
    from sim.rules import decide

    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    decision = decide(observation, config=config)
    assert decision.status == Status.OK
    assert decision.catalogue_version == 1 and decision.model_version == 0
    assert [answer.question_id for answer in decision.answers] == list(QuestionId)[:3]
    assert [answer.selected for answer in decision.answers] == [0, 1, 3]
    assert len(encode_decision(decision)) == 100
    assert decode_decision(encode_decision(decision)) == decision


@pytest.fixture
def motion_rule_observation():
    config = Config(noise_std=0, dropout=0, latency_ticks=2)
    observation, _ = RoverEnv(Config(noise_std=0, dropout=0, latency_ticks=0)).reset()
    observation.update(tick=3, time_s=0.15, tof_sample_tick=0, tof_age_s=0.15)
    observation["ego"] = np.array([0.6, 0, 4, 0], dtype=np.float32)
    observation["goal_body_m"] = observation["ego"][2:].copy()
    observation["history_valid"][-4:] = True
    observation["history_ego"][-4:] = observation["ego"]
    observation["tof_valid"][3, 3] = True
    observation["tof_m"][3, 3] = 0.53
    return config, observation


def test_motion_registered_rules_shift_old_hits_before_stopping_check(
    motion_rule_observation,
):
    from sim.rules import RuleSettings, decide

    config, observation = motion_rule_observation
    original = decide(observation, config=config)
    registered = decide(
        observation, config=config, settings=RuleSettings(register_motion=True)
    )
    assert original.status == registered.status == 0
    assert original.answers[0].selected == 0
    assert registered.answers[0].selected == 1
    assert registered.answers[2].selected == 0


@pytest.mark.parametrize("turn", [0.0, -0.1, 0.1])
def test_motion_registered_rules_match_independent_interval_composition(
    motion_rule_observation, turn
):
    from sim.rules import _registered_columns

    config, observation = motion_rule_observation
    observation["ego"][1] = turn
    observation["history_ego"][-4:] = observation["ego"]
    ranges = observation["tof_m"]
    rays = tof_directions(0, config)
    supported = observation["tof_valid"] & (ranges > 0) & (ranges < config.max_range)
    obstacles = supported & (config.tof_mount_height + ranges * rays[..., 2] > 0.03)
    columns = _registered_columns(observation, config, rays, supported, obstacles)
    angle = float(observation["ego"][1]) * 3 * config.dt
    speed = float(observation["ego"][0])
    translation = (
        np.array([speed * 3 * config.dt, 0])
        if not angle
        else speed
        / float(observation["ego"][1])
        * np.array([math.sin(angle), 1 - math.cos(angle)])
    )
    hit = float(ranges[3, 3]) * rays[3, 3, :2] - translation
    expected_distance = math.hypot(*hit)
    expected_bearing = math.atan2(hit[1], hit[0]) - angle
    column = round(
        (config.field_of_view / 2 - expected_bearing) * 7 / config.field_of_view
    )
    assert columns[column] == pytest.approx(expected_distance, abs=1e-12)
    assert np.count_nonzero(columns < config.max_range) == 1


@pytest.mark.parametrize(
    "defect",
    [
        "missing_history",
        "shape",
        "dtype",
        "mask_dtype",
        "gap",
        "current_mismatch",
        "nan",
        "speed",
        "negative_speed",
        "turn",
        "short_window",
        "clock",
        "delayed_config",
        "delayed_metadata",
    ],
)
def test_motion_registered_rules_reject_unsupported_motion(
    motion_rule_observation, defect
):
    from dataclasses import replace

    from interface.protocol import Status
    from sim.rules import RuleSettings, decide

    config, observation = motion_rule_observation
    if defect == "missing_history":
        del observation["history_ego"]
    elif defect == "shape":
        observation["history_ego"] = np.zeros((8, 3))
    elif defect == "dtype":
        observation["history_ego"] = observation["history_ego"].astype(str)
    elif defect == "mask_dtype":
        observation["history_valid"] = observation["history_valid"].astype(int)
    elif defect == "gap":
        observation["history_valid"][-2] = False
    elif defect == "current_mismatch":
        observation["history_ego"][-1, 0] = 0
    elif defect in ("nan", "speed", "negative_speed", "turn"):
        value = {"nan": float("nan"), "speed": 2, "negative_speed": -1, "turn": 2}[
            defect
        ]
        observation["history_ego"][-2, int(defect == "turn")] = value
    elif defect == "short_window":
        config = replace(config, history_ticks=2)
    elif defect == "clock":
        observation["time_s"] = 0.16
    elif defect == "delayed_config":
        config = replace(config, odometry_latency_ticks=1)
    else:
        observation.update(ego_sample_tick=2, ego_age_s=0.05)
    decision = decide(
        observation, config=config, settings=RuleSettings(register_motion=True)
    )
    assert decision.status == Status.REJECT_OUT_OF_DOMAIN and not decision.answers


def test_motion_registered_rules_reject_turns_without_current_column_support(
    motion_rule_observation,
):
    from interface.protocol import Status
    from sim.rules import RuleSettings, decide, wire_step

    config, observation = motion_rule_observation
    observation["ego"][:2] = [0, 1.5]
    observation["history_ego"][-4:] = observation["ego"]
    settings = RuleSettings(register_motion=True)
    assert decide(observation, config=config).status == Status.OK
    assert (
        decide(observation, config=config, settings=settings).status
        == Status.REJECT_OUT_OF_DOMAIN
    )
    action, *_ = wire_step(observation, config=config, settings=settings)
    np.testing.assert_array_equal(action, [0, 0])


def test_motion_registered_rules_are_detached_and_ignore_privileged_fields(
    motion_rule_observation,
):
    from sim.rules import RuleSettings, decide

    config, observation = motion_rule_observation
    before = json.dumps(observation, default=json_value, sort_keys=True)
    settings = RuleSettings(register_motion=True)
    expected = decide(observation, config=config, settings=settings)
    assert json.dumps(observation, default=json_value, sort_keys=True) == before
    observation.update(
        ground_truth={"position_m": [99, 99]},
        action=[99, 99],
        labels={"path_blocked": False},
    )
    assert decide(observation, config=config, settings=settings) == expected


@pytest.mark.parametrize("value", [None, 0, 1, "true", np.bool_(True)])
def test_motion_registered_rules_require_an_explicit_boolean(value):
    from sim.rules import RuleSettings

    with pytest.raises(ValueError):
        RuleSettings(register_motion=value)


def test_motion_registered_rules_zero_age_preserves_original_decision():
    from sim.rules import RuleSettings, decide

    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    before = json.dumps(observation, default=json_value, sort_keys=True)
    assert decide(
        observation, config=config, settings=RuleSettings(register_motion=True)
    ) == decide(observation, config=config)
    assert json.dumps(observation, default=json_value, sort_keys=True) == before


@pytest.mark.parametrize(
    "defect,status",
    [
        ("missing", 2),
        ("stale", 2),
        ("column", 3),
        ("zero", 3),
        ("masked_nonzero", 3),
        ("below_floor", 3),
        ("legacy", 3),
        ("bad_age", 3),
    ],
)
def test_floor_rules_reject_unsupported_evidence(defect, status):
    from dataclasses import replace

    from sim.rules import decide

    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    if defect == "missing":
        observation["tof_sample_tick"] = None
        observation["tof_valid"][:] = False
        observation["tof_m"][:] = 0
    elif defect == "stale":
        observation.update(tick=2, time_s=0.1, tof_age_s=0.1)
    elif defect == "column":
        observation["tof_valid"][:, 3] = False
        observation["tof_m"][:, 3] = 0
    elif defect == "zero":
        observation["tof_m"][:] = 0
    elif defect == "masked_nonzero":
        observation["tof_m"][0, 0] = 1
    elif defect == "below_floor":
        observation["tof_m"][-1, 0] = 1
    elif defect == "legacy":
        config = replace(config, tof_mount_height=None)
    else:
        observation["tof_age_s"] = float("nan")
    packet = decide(observation, config=config)
    assert packet.status == status and not packet.answers


def test_floor_rules_obstacle_momentum_and_privileged_fields_are_independent():
    from sim.rules import decide

    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    observation["ego"][0] = 0.6
    observation["tof_valid"][3, 3] = True
    observation["tof_m"][3, 3] = 0.35
    first = decide(observation, config=config)
    assert [answer.selected for answer in first.answers][::2] == [1, 0]
    observation.update(
        ground_truth={"position_m": [99, 99]},
        action=[99, 99],
        labels={"path_blocked": False},
    )
    assert decide(observation, config=config) == first


@pytest.mark.parametrize(
    "defect", ["absent", "crc", "sequence", "timestamp", "rejected"]
)
def test_floor_rules_host_brakes_on_missing_or_invalid_decisions(defect):
    from dataclasses import replace

    from interface.protocol import Status, decode_decision, encode_decision
    from sim.rules import host_action, wire_step

    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset()
    action, state_frame, frame = wire_step(observation, config=config)
    assert action[0] > 0
    packet = decode_decision(frame)
    if defect == "absent":
        frame = None
    elif defect == "crc":
        frame = frame[:-1] + bytes([frame[-1] ^ 1])
    elif defect == "sequence":
        frame = encode_decision(replace(packet, sequence=1))
    elif defect == "timestamp":
        frame = encode_decision(replace(packet, timestamp_us=1))
    else:
        frame = encode_decision(
            replace(packet, status=Status.REJECT_STALE_INPUT, answers=())
        )
    np.testing.assert_array_equal(
        host_action(state_frame, frame, config=config), [0, 0]
    )


@pytest.mark.parametrize(
    "settings",
    [
        {"floor_band_m": -1},
        {"floor_band_m": None},
        {"max_age_s": True},
        {"max_age_s": float("nan")},
        {"floor_band_m": 10**400},
    ],
)
def test_floor_rule_settings_reject_invalid_values(settings):
    from sim.rules import RuleSettings

    with pytest.raises(ValueError):
        RuleSettings(**settings)


def test_floor_rules_diagnostics_are_bounded_private_and_exclusive(tmp_path):
    from interface.protocol import decode_decision, decode_state
    from sim.rules import run_diagnostics

    output, report = tmp_path / "episodes", tmp_path / "report.json"
    result = run_diagnostics(output, report, config=Config(max_ticks=2))
    assert result["totals"]["episodes"] == 8
    assert result["totals"]["ticks"] == 16
    assert not result["training_approved"] and not result["task_labels"]
    assert not result["rule_quality_qualified"] and not result["calibrated"]
    for path in output.glob("*.jsonl"):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        assert rows[0]["policy"] == "observation_only_wire_rules"
        for row in rows[1:-1]:
            state = decode_state(bytes.fromhex(row["state_frame_hex"]))
            decision = decode_decision(bytes.fromhex(row["decision_frame_hex"]))
            assert state.sequence == decision.sequence
            assert "ground_truth" not in row["observation"]
            assert "reference_comparisons" not in row
    with pytest.raises(ValueError, match="fresh"):
        run_diagnostics(output, report)


@pytest.mark.parametrize("direction", ["equal", "report_parent", "output_parent"])
def test_floor_rules_diagnostic_paths_reject_before_collection(
    tmp_path, monkeypatch, direction
):
    from sim import rules

    def unexpected(*args):
        raise AssertionError("must reject before collection")

    monkeypatch.setattr(rules, "_diagnostic_episode", unexpected)
    output, report = tmp_path / "output", tmp_path / "output"
    if direction == "report_parent":
        output = report / "nested"
    elif direction == "output_parent":
        report = output / "nested.json"
    with pytest.raises(ValueError, match="nonoverlapping"):
        rules.run_diagnostics(output, report)
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("top", [0.05, 0.5, 1.0])
def test_tof_capped_cylinder_first_hit_satisfies_analytic_surface(top):
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    scene = Scenario(obstacles=((3.0, 3.0, 0.5),), obstacle_heights=(top,))
    ranges = tof_ranges(np.array(scene.start[:2]), 0, scene, config)
    rays = tof_directions(0, config)
    row, column = (4, 3) if top == 0.05 else (3, 3)
    point = np.array([1, 3, 0.15]) + ranges[row, column] * rays[row, column]
    if top == 0.05:
        assert point[2] == pytest.approx(top)
        assert np.linalg.norm(point[:2] - [3, 3]) < 0.5
    else:
        assert np.linalg.norm(point[:2] - [3, 3]) == pytest.approx(0.5)
        assert 0 < point[2] < top
    assert ranges[row, column] < config.max_range


def test_tof_low_obstacles_and_tall_obstacles_have_different_row_visibility():
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    scenes = [
        Scenario(obstacles=((3, 3, 0.5),), obstacle_heights=(top,))
        for top in (0.05, 1.0)
    ]
    observations = [RoverEnv(config, scene).reset()[0] for scene in scenes]
    assert not observations[0]["tof_valid"][0, 3]
    assert observations[1]["tof_valid"][0, 3]
    assert observations[0]["tof_m"][4, 3] > observations[1]["tof_m"][4, 3]


def test_tof_geometry_rotates_with_yaw_without_changing_returns():
    config = Config()
    scenes = [
        Scenario(start=(3, 3, 0), obstacles=((4, 3, 0.3),)),
        Scenario(start=(3, 3, math.pi / 2), obstacles=((3, 4, 0.3),)),
    ]
    ranges = [
        tof_ranges(np.array(scene.start[:2]), scene.start[2], scene, config)
        for scene in scenes
    ]
    np.testing.assert_allclose(*ranges, rtol=1e-13, atol=1e-13)


def test_tof_finite_wall_does_not_continue_beyond_its_arena_edge():
    config = Config(tof_mount_pitch=-math.pi / 4, wall_height=0.1)
    scene = Scenario()
    ranges = tof_ranges(np.array(scene.start[:2]), 0, scene, config)
    assert np.isinf(ranges).all()


def test_tof_legacy_planar_sampling_preserves_values_masks_and_rng():
    config = Config(tof_mount_height=None, tof_rate_hz=None, latency_ticks=0)
    env = RoverEnv(config)
    observation, _ = env.reset(seed=42)
    rng = np.random.default_rng(42)
    for _ in range(4):
        angles = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)
        ranges = ray_ranges(
            env.position,
            angles,
            env.scenario.obstacles,
            env.scenario.bounds,
            config.max_range,
        )
        grid = np.broadcast_to(ranges, (8, 8)).copy()
        grid += rng.normal(0, config.noise_std, grid.shape)
        valid = rng.random((8, 8)) >= config.dropout
        expected = np.where(valid, np.clip(grid, 0, config.max_range), 0).astype(
            np.float32
        )
        np.testing.assert_array_equal(observation["tof_m"], expected)
        np.testing.assert_array_equal(observation["tof_valid"], valid)
        assert rng.bit_generator.state == env.rng.bit_generator.state
        observation, *_ = env.step((0, 0))


def test_odometry_delay_holds_an_old_estimate_and_exports_its_age():
    from interface.protocol import decode_state, encode_state

    config = Config(odometry_latency_ticks=1, latency_ticks=0)
    env = RoverEnv(config)
    initial, _ = env.reset(seed=4)
    first, *_ = env.step((0.6, 0.4))
    np.testing.assert_array_equal(first["ego"], initial["ego"])
    assert first["ego_sample_tick"] == 0
    assert first["ego_age_s"] == pytest.approx(config.dt)
    second, *_ = env.step((0.6, 0.4))
    assert second["ego"][0] == pytest.approx(config.acceleration * config.dt)
    assert second["ego_sample_tick"] == 1
    np.testing.assert_array_equal(second["history_ego"][-1], second["ego"])
    state = decode_state(encode_state(state_from_observation(second)))
    assert state.ages_us[:3] == (50_000, 50_000, 50_000)
    assert state.velocity_m_s[0] == pytest.approx(second["ego"][0])


@pytest.mark.parametrize(
    "position_error,heading_error", [(0.02, 0), (0, math.radians(2))]
)
def test_odometry_synthetic_errors_are_bounded_and_do_not_change_physics_or_tof(
    position_error, heading_error
):
    from dataclasses import replace

    config = Config(
        odometry_position_error=position_error, odometry_heading_error=heading_error
    )
    noisy, ideal = (
        RoverEnv(config),
        RoverEnv(replace(config, odometry_position_error=0, odometry_heading_error=0)),
    )
    observation, _ = noisy.reset(seed=42)
    reference, _ = ideal.reset(seed=42)
    assert not np.array_equal(observation["ego"], reference["ego"])
    for _ in range(12):
        np.testing.assert_array_equal(observation["tof_m"], reference["tof_m"])
        np.testing.assert_array_equal(observation["tof_valid"], reference["tof_valid"])
        if position_error:
            assert (
                np.linalg.norm(observation["goal_body_m"] - reference["goal_body_m"])
                <= position_error + 1e-6
            )
        else:
            assert np.linalg.norm(observation["goal_body_m"]) == pytest.approx(
                np.linalg.norm(reference["goal_body_m"]), abs=1e-6
            )
            difference = math.atan2(*observation["goal_body_m"][::-1]) - math.atan2(
                *reference["goal_body_m"][::-1]
            )
            assert abs(difference) <= heading_error + 1e-6
        observation, *outcome, info = noisy.step((0.3, 0.2))
        reference, *expected, reference_info = ideal.step((0.3, 0.2))
        assert outcome == expected
        np.testing.assert_array_equal(
            info["ground_truth"]["position_m"],
            reference_info["ground_truth"]["position_m"],
        )
        assert noisy.rng.bit_generator.state == ideal.rng.bit_generator.state


def test_odometry_combined_errors_reset_and_read_without_extra_rng():
    config = Config(
        odometry_position_error=0.02,
        odometry_heading_error=math.radians(2),
        odometry_latency_ticks=1,
    )
    env = RoverEnv(config)
    snapshots = []
    for _ in range(2):
        observation, _ = env.reset(seed=42)
        sequence = []
        for _ in range(10):
            before = deepcopy(env.odometry_rng.bit_generator.state)
            np.testing.assert_array_equal(env._observation()["ego"], observation["ego"])
            assert env.odometry_rng.bit_generator.state == before
            sequence.append(json.dumps(observation, default=json_value, sort_keys=True))
            observation, *_ = env.step((0.3, 0.4))
        snapshots.append(sequence)
    assert snapshots[0] == snapshots[1]
    assert "position_m" not in observation and "yaw_rad" not in observation


@pytest.mark.parametrize(
    "settings",
    [
        {"odometry_position_error": -0.01},
        {"odometry_position_error": float("inf")},
        {"odometry_heading_error": -0.01},
        {"odometry_heading_error": math.pi + 0.01},
        {"odometry_heading_error": float("nan")},
        {"odometry_latency_ticks": -1},
        {"odometry_latency_ticks": 0.5},
        {"odometry_position_error": 10**400},
    ],
)
def test_odometry_rejects_invalid_configuration(settings):
    with pytest.raises(ValueError):
        Config(**settings)


@pytest.mark.parametrize(
    "changes",
    [
        {"ego_sample_tick": 0},
        {"ego_age_s": 0.05},
        {"ego_sample_tick": False, "ego_age_s": 0},
        {"ego_sample_tick": 1.0, "ego_age_s": 0},
        {"ego_sample_tick": -1, "ego_age_s": 0.1},
        {"ego_sample_tick": 2, "ego_age_s": 0},
        {"ego_sample_tick": 0, "ego_age_s": True},
        {"ego_sample_tick": 0, "ego_age_s": float("nan")},
        {"ego_sample_tick": 0, "ego_age_s": 10**400},
        {"ego_sample_tick": 0, "ego_age_s": 0},
        {"ego_sample_tick": 0, "ego_age_s": -0.05},
        {"ego_sample_tick": 0, "ego_age_s": 1e308, "time_s": 1e308},
    ],
)
def test_odometry_wire_export_rejects_malformed_age(changes):
    env = RoverEnv()
    observation, *_ = env.step((0, 0))
    observation.update(changes)
    with pytest.raises(ValueError):
        state_from_observation(observation)


@pytest.mark.parametrize(
    "settings",
    [
        {"tof_mount_height": 0},
        {"tof_mount_height": -0.1},
        {"tof_mount_height": float("inf")},
        {"tof_mount_pitch": math.pi / 2},
        {"tof_mount_pitch": -math.pi / 2},
        {"wall_height": 0},
        {"obstacle_height": -1},
    ],
)
def test_tof_geometry_rejects_invalid_configuration(settings):
    with pytest.raises(ValueError):
        Config(**settings)


@pytest.mark.parametrize(
    "heights", [(0,), (-1,), (True,), (float("nan"),), (float("inf"),), (0.1, 0.2)]
)
def test_tof_geometry_rejects_invalid_obstacle_heights(heights):
    with pytest.raises(ValueError):
        RoverEnv(scenario=Scenario(obstacles=((3, 3, 0.2),), obstacle_heights=heights))


@pytest.mark.parametrize("obstacle", [(2.4, 2.0, 0.01), (2.1, 2.185, 0.01)])
def test_navigation_proposal_full_ray_history_can_hide_a_swept_collision(obstacle):
    from sim.navigation import evaluate_synthetic
    from teacher.label_pipeline import prepare_request

    config = Config(noise_std=0, dropout=0)
    position = np.array([2.0, 2.0])
    bounds = (6.0, 6.0)
    angles = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)
    free_history, obstructed_history = [], []
    for offset in range(config.history_ticks):
        past = position - np.array(
            [
                (config.history_ticks - 1 - offset + config.latency_ticks)
                * config.max_speed
                * config.dt,
                0,
            ]
        )
        free_history.append(ray_ranges(past, angles, (), bounds, config.max_range))
        obstructed_history.append(
            ray_ranges(past, angles, (obstacle,), bounds, config.max_range)
        )
    np.testing.assert_array_equal(free_history, obstructed_history)
    assert not swept_collision(position, position, config.radius, (obstacle,), bounds)
    age = config.latency_ticks * config.dt
    stopping_distance = config.max_speed * (age + config.dt) + config.max_speed**2 / (
        2 * config.acceleration
    )
    end = position + np.array([stopping_distance, 0])
    assert not swept_collision(position, end, config.radius, (), bounds)
    assert swept_collision(position, end, config.radius, (obstacle,), bounds)

    ego_history = np.array(
        [
            [
                config.max_speed,
                0,
                3 + (config.history_ticks - 1 - offset) * config.max_speed * config.dt,
                0,
            ]
            for offset in range(config.history_ticks)
        ],
        dtype=np.float32,
    )
    states = []
    for history in (free_history, obstructed_history):
        tof_history = np.repeat(
            np.asarray(history, dtype=np.float32)[:, None, :], 8, axis=1
        )
        observation = {
            "schema": "micro-classifier/sim-observation/1",
            "tick": 15,
            "time_s": 15 * config.dt,
            "ego": ego_history[-1],
            "goal_body_m": ego_history[-1, 2:],
            "tof_m": tof_history[-1],
            "tof_valid": np.ones((8, 8), dtype=bool),
            "tof_age_s": age,
            "tof_sample_tick": 15 - config.latency_ticks,
            "history_ego": ego_history,
            "history_tof_m": tof_history,
            "history_tof_valid": np.ones((8, 8, 8), dtype=bool),
            "history_valid": np.ones(config.history_ticks, dtype=bool),
        }
        states.append(prepare_request(observation, config=config)["state"])
    assert states[0] == states[1]
    settings = {
        "speed": config.max_speed,
        "tof_age_s": age,
        "config": config,
        "synthetic_test_only": True,
    }
    clear_reference = evaluate_synthetic(
        Scenario(start=(2.0, 2.0, 0.0), goal=(5.0, 2.0)), **settings
    )
    blocked_reference = evaluate_synthetic(
        Scenario(start=(2.0, 2.0, 0.0), goal=(5.0, 2.0), obstacles=(obstacle,)),
        **settings,
    )
    assert clear_reference["answers"]["path_blocked"] == "false"
    assert blocked_reference["answers"]["path_blocked"] == "true"


@pytest.mark.parametrize("offset,blocked", [(-1e-6, True), (0, True), (1e-6, False)])
def test_navigation_proposal_circle_contact_counts_across_the_whole_sweep(
    offset, blocked
):
    start, end = (2.0, 2.0), (3.0, 2.0)
    radius = 0.125
    obstacles = ((2.5, 2.25 + offset, 0.125),)
    bounds = (6.0, 6.0)
    assert not swept_collision(start, start, radius, obstacles, bounds)
    assert not swept_collision(end, end, radius, obstacles, bounds)
    assert swept_collision(start, end, radius, obstacles, bounds) == blocked


@pytest.mark.parametrize("tier,distance", [(1, 0.05), (2, 0.14), (3, 0.27)])
def test_navigation_proposal_nominal_stopping_candidates(tier, distance):
    config = Config()
    speed = config.max_speed * tier / 3
    age = config.latency_ticks * config.dt
    reaction = age + config.dt
    assert reaction == pytest.approx(0.15)
    assert speed * reaction + speed**2 / (2 * config.acceleration) == pytest.approx(
        distance
    )
    assert reaction + speed / config.acceleration == pytest.approx(0.15 + tier * 0.2)


@pytest.mark.parametrize("requested_tier", [1, 2])
def test_navigation_proposal_lower_request_does_not_erase_current_momentum(
    requested_tier,
):
    config = Config()
    position = np.array([2.0, 2.0])
    obstacles, bounds = ((2.35, 2.0, 0.02),), (6.0, 6.0)
    requested_speed = config.max_speed * requested_tier / 3
    current_speed = config.max_speed
    reaction = (config.latency_ticks + 1) * config.dt
    distances = [
        speed * reaction + speed**2 / (2 * config.acceleration)
        for speed in (requested_speed, max(current_speed, requested_speed))
    ]
    assert not swept_collision(
        position, position + [distances[0], 0], config.radius, obstacles, bounds
    )
    assert swept_collision(
        position, position + [distances[1], 0], config.radius, obstacles, bounds
    )


@pytest.mark.parametrize(
    "point", [(0.125, 2.0), (5.875, 2.0), (2.0, 0.125), (2.0, 5.875)]
)
def test_synthetic_navigation_reference_and_simulator_include_wall_contact(point):
    from sim.navigation import _touches

    radius, bounds = 0.125, (6.0, 6.0)
    assert swept_collision(point, point, radius, (), bounds)
    assert _touches(point, point, radius, (), bounds)
    assert not _touches((0.126, 2.0), (0.126, 2.0), radius, (), bounds)


def test_synthetic_navigation_reference_requires_opt_in_and_no_observation_input():
    from sim.navigation import evaluate_synthetic

    with pytest.raises(ValueError, match="synthetic-test-only"):
        evaluate_synthetic(Scenario(), speed=0.3)
    with pytest.raises(TypeError, match="not observations"):
        evaluate_synthetic({}, speed=0.3, synthetic_test_only=True)


@pytest.mark.parametrize(
    "goal,expected",
    [((5.0, 3.0), "centre"), ((5.0, 4.0), "left"), ((5.0, 2.0), "right")],
)
def test_synthetic_navigation_reference_open_geometry_goal_ranking(goal, expected):
    from sim.navigation import evaluate_synthetic

    result = evaluate_synthetic(
        Scenario(goal=goal), speed=0.6, tof_age_s=0.1, synthetic_test_only=True
    )
    assert result["answers"] == {
        "path_blocked": "false",
        "clear_sector": expected,
        "speed_tier": "3",
        "mode": None,
    }
    assert result["synthetic"] and not result["training_approved"]
    assert not result["reviewed_dataset"] and not result["physical_safety_claim"]
    assert result["mode_labels"] == 0
    json.dumps(result, allow_nan=False)


def test_synthetic_navigation_reference_at_rest_and_blocked_are_distinct():
    from sim.navigation import evaluate_synthetic

    stopped = evaluate_synthetic(Scenario(), speed=0, synthetic_test_only=True)
    assert stopped["answers"]["path_blocked"] == "false"
    assert stopped["answers"]["clear_sector"] is None
    obstacle = Scenario(obstacles=((1.3, 3.0, 0.1),))
    moving = evaluate_synthetic(
        obstacle, speed=0.6, tof_age_s=0.1, synthetic_test_only=True
    )
    assert moving["answers"] == {
        "path_blocked": "true",
        "clear_sector": "none",
        "speed_tier": "0",
        "mode": None,
    }


def test_synthetic_navigation_reference_budget_exhaustion_abstains():
    from sim.navigation import evaluate_synthetic

    result = evaluate_synthetic(
        Scenario(),
        speed=0.4,
        turn_rate=0.7,
        tof_age_s=0.1,
        max_segments=1,
        synthetic_test_only=True,
    )
    assert all(answer is None for answer in result["answers"].values())
    assert all(row["status"] == "unknown" for row in result["maneuvers"].values())


@pytest.mark.parametrize(
    "field,value",
    [
        ("speed", True),
        ("speed", -1),
        ("speed", 0.7),
        ("turn_rate", 2),
        ("tof_age_s", -1),
        ("tof_age_s", float("nan")),
        ("max_segments", True),
        ("max_segments", 4097),
    ],
)
def test_synthetic_navigation_reference_rejects_invalid_inputs(field, value):
    from sim.navigation import evaluate_synthetic

    settings = {"speed": 0.3, "synthetic_test_only": True, field: value}
    with pytest.raises(ValueError):
        evaluate_synthetic(Scenario(), **settings)


@pytest.mark.parametrize("turn_rate", [-0.7, 0.0, 0.7])
def test_synthetic_navigation_reference_curved_endpoints_match_high_order_quadrature(
    turn_rate,
):
    from sim.navigation import evaluate_synthetic

    scenario, config = Scenario(), Config()
    speed, reaction = 0.6, 0.15
    result = evaluate_synthetic(
        scenario,
        speed=speed,
        turn_rate=turn_rate,
        tof_age_s=0.1,
        synthetic_test_only=True,
    )
    nodes, weights = np.polynomial.legendre.leggauss(64)
    for name, angular_rate in (
        ("centre", 0),
        ("left", config.max_turn_rate),
        ("right", -config.max_turn_rate),
    ):
        endpoint = np.array(scenario.start[:2], dtype=float)
        yaw = scenario.start[2]
        for duration, angular, deceleration in (
            (reaction, turn_rate, 0),
            (speed / config.acceleration, angular_rate, config.acceleration),
        ):
            times = (nodes + 1) * duration / 2
            headings = yaw + angular * times
            velocity = (speed - deceleration * times)[:, None] * np.stack(
                [np.cos(headings), np.sin(headings)], axis=1
            )
            endpoint += duration / 2 * np.sum(weights[:, None] * velocity, axis=0)
            yaw += angular * duration
        row = result["maneuvers"][name]
        assert row["status"] == "clear"
        assert (
            np.linalg.norm(endpoint - row["endpoint_m"])
            <= row["endpoint_error_bound_m"] + 1e-12
        )


@pytest.mark.parametrize("yaw", [1e16, -1e16])
def test_synthetic_navigation_reference_large_heading_preserves_small_turns(yaw):
    from sim.navigation import evaluate_synthetic

    bounded_yaw = math.atan2(math.sin(yaw), math.cos(yaw))
    settings = {
        "speed": 0.6,
        "turn_rate": 0.7,
        "tof_age_s": 0.1,
        "synthetic_test_only": True,
    }
    large = evaluate_synthetic(Scenario(start=(1.0, 3.0, yaw)), **settings)
    bounded = evaluate_synthetic(Scenario(start=(1.0, 3.0, bounded_yaw)), **settings)
    for name, reference in bounded["maneuvers"].items():
        actual = large["maneuvers"][name]
        assert actual["status"] == reference["status"] == "clear"
        assert math.dist(actual["endpoint_m"], reference["endpoint_m"]) <= (
            actual["endpoint_error_bound_m"]
            + reference["endpoint_error_bound_m"]
            + 1e-12
        )
    assert large["answers"] == bounded["answers"]


@pytest.mark.parametrize("field", ["speed", "turn_rate", "tof_age_s"])
@pytest.mark.parametrize("value", [10**400, -(10**400)])
def test_synthetic_navigation_rejects_unrepresentable_motion(field, value):
    from sim.navigation import evaluate_synthetic, probe_synthetic_ray_witness

    settings = {"speed": 0.6, "synthetic_test_only": True, field: value}
    with pytest.raises(ValueError, match="finite"):
        evaluate_synthetic(Scenario(), **settings)
    with pytest.raises(ValueError, match="finite"):
        probe_synthetic_ray_witness(np.full(8, 0.3), np.ones(8, dtype=bool), **settings)


def test_synthetic_navigation_reference_unresolved_goal_ranking_abstains():
    from sim.navigation import evaluate_synthetic

    settings = {"speed": 0.6, "tof_age_s": 0.1, "synthetic_test_only": True}
    result = evaluate_synthetic(Scenario(), **settings)
    goal = tuple(
        (
            np.asarray(result["maneuvers"]["centre"]["endpoint_m"])
            + result["maneuvers"]["left"]["endpoint_m"]
        )
        / 2
    )
    unresolved = evaluate_synthetic(Scenario(goal=goal), **settings)
    assert all(row["status"] == "clear" for row in unresolved["maneuvers"].values())
    assert unresolved["answers"]["clear_sector"] is None


def test_synthetic_navigation_reference_symmetric_turn_tie_prefers_left():
    from sim.navigation import evaluate_synthetic

    result = evaluate_synthetic(
        Scenario(obstacles=((1.47, 3.0, 0.02),)),
        speed=0.6,
        tof_age_s=0.1,
        synthetic_test_only=True,
    )
    assert result["maneuvers"]["centre"]["status"] == "blocked"
    assert (
        result["maneuvers"]["left"]["status"]
        == result["maneuvers"]["right"]["status"]
        == "clear"
    )
    assert result["answers"]["clear_sector"] == "left"


@pytest.mark.parametrize(
    "gap,tier", [(0.025, "0"), (0.09, "1"), (0.2, "2"), (0.35, "3")]
)
def test_synthetic_navigation_reference_tier_capacity_and_current_momentum(gap, tier):
    from sim.navigation import evaluate_synthetic

    scenario = Scenario(obstacles=((1.19 + gap, 3.0, 0.01),))
    result = evaluate_synthetic(
        scenario, speed=0, tof_age_s=0.1, synthetic_test_only=True
    )
    assert result["answers"]["speed_tier"] == tier
    if tier == "2":
        moving = evaluate_synthetic(
            scenario, speed=0.6, tof_age_s=0.1, synthetic_test_only=True
        )
        assert moving["answers"]["speed_tier"] == "0"


def test_synthetic_navigation_reference_curved_contact_uncertainty_is_not_none():
    from sim.navigation import evaluate_synthetic

    settings = {"speed": 0.6, "tof_age_s": 0.1, "synthetic_test_only": True}
    empty = evaluate_synthetic(Scenario(), **settings)
    endpoint = np.asarray(empty["maneuvers"]["left"]["endpoint_m"])
    centre = endpoint + 0.19 * np.array([math.sin(0.9), -math.cos(0.9)])
    scene = Scenario(obstacles=((*centre, 0.01),))
    result = evaluate_synthetic(scene, **settings)
    assert result["maneuvers"]["left"]["status"] == "unknown"
    assert result["answers"]["clear_sector"] is None


@pytest.mark.parametrize(
    "distance,status", [(0.3, "blocked_witness"), (0.8, "unknown"), (4.0, "unknown")]
)
def test_synthetic_ray_probe_has_positive_witness_but_never_infers_clear(
    distance, status
):
    from sim.navigation import probe_synthetic_ray_witness

    ranges, valid = np.full(8, 4.0), np.ones(8, dtype=bool)
    ranges[3] = distance
    original = ranges.copy()
    result = probe_synthetic_ray_witness(
        ranges,
        valid,
        speed=0.6,
        config=Config(noise_std=0, latency_ticks=0),
        synthetic_test_only=True,
    )
    assert result["status"] == status
    assert result["synthetic"] and not result["training_approved"]
    assert not result["real_input_qualified"] and not result["physical_safety_claim"]
    assert result["witness_columns"] == ([3] if status == "blocked_witness" else [])
    np.testing.assert_array_equal(ranges, original)


def test_synthetic_ray_probe_normal_defaults_abstain():
    from sim.navigation import probe_synthetic_ray_witness

    result = probe_synthetic_ray_witness(
        np.full(8, 0.3), np.ones(8, dtype=bool), speed=0.6, synthetic_test_only=True
    )
    assert (
        result["status"] == "unknown" and result["reason"] == "noise_model_unqualified"
    )


@pytest.mark.parametrize(
    "obstacle,oracle_answer,probe_status",
    [
        ((1.35, 3.0, 0.04), "true", "blocked_witness"),
        ((1.6, 3.0, 0.04), "false", "unknown"),
        ((1.25, 3.195, 0.02), "true", "unknown"),
    ],
)
def test_synthetic_ray_probe_corresponds_to_geometry_without_proving_clear(
    obstacle, oracle_answer, probe_status
):
    from sim.navigation import evaluate_synthetic, probe_synthetic_ray_witness

    config = Config(noise_std=0, latency_ticks=0)
    scene = Scenario(obstacles=(obstacle,))
    angles = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)
    ranges = ray_ranges(
        scene.start[:2], angles, scene.obstacles, scene.bounds, config.max_range
    )
    probe = probe_synthetic_ray_witness(
        ranges,
        np.ones(8, dtype=bool),
        speed=0.6,
        config=config,
        synthetic_test_only=True,
    )
    reference = evaluate_synthetic(
        scene, speed=0.6, config=config, synthetic_test_only=True
    )
    assert probe["status"] == probe_status
    assert reference["answers"]["path_blocked"] == oracle_answer


@pytest.mark.parametrize(
    "offset,status", [(-1e-6, "blocked_witness"), (0, "unknown"), (1e-6, "unknown")]
)
def test_synthetic_ray_probe_boundary_requires_strict_interior(offset, status):
    from sim.navigation import probe_synthetic_ray_witness

    config = Config(noise_std=0, latency_ticks=0)
    angle = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)[3]
    distance = 0.6 * config.dt + 0.6**2 / (2 * config.acceleration)
    contact = distance * math.cos(angle) + math.sqrt(
        config.radius**2 - distance**2 * math.sin(angle) ** 2
    )
    ranges, valid = np.zeros(8), np.zeros(8, dtype=bool)
    ranges[3], valid[3] = contact + offset, True
    result = probe_synthetic_ray_witness(
        ranges, valid, speed=0.6, config=config, synthetic_test_only=True
    )
    assert result["status"] == status


def test_synthetic_ray_probe_missing_mask_cannot_create_origin_witness():
    from sim.navigation import probe_synthetic_ray_witness

    result = probe_synthetic_ray_witness(
        np.zeros(8),
        np.zeros(8, dtype=bool),
        speed=0.6,
        config=Config(noise_std=0, latency_ticks=0),
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown" and result["witness_columns"] == []


@pytest.mark.parametrize(
    "settings,reason",
    [
        ({"config": Config(noise_std=0)}, "registration_unqualified"),
        ({"tof_age_s": 0.1}, "registration_unqualified"),
        ({"turn_rate": 0.1}, "curved_reference_not_supported"),
    ],
)
def test_synthetic_ray_probe_unqualified_assumptions_abstain(settings, reason):
    from sim.navigation import probe_synthetic_ray_witness

    arguments = {
        "speed": 0.6,
        "config": Config(noise_std=0, latency_ticks=0),
        "synthetic_test_only": True,
        **settings,
    }
    result = probe_synthetic_ray_witness(
        np.full(8, 0.3), np.ones(8, dtype=bool), **arguments
    )
    assert result["status"] == "unknown" and result["reason"] == reason


@pytest.mark.parametrize("opt_in", [False, None, 1])
def test_synthetic_ray_probe_requires_explicit_scope_before_reading_inputs(opt_in):
    from sim.navigation import probe_synthetic_ray_witness

    with pytest.raises(ValueError, match="synthetic-test-only"):
        probe_synthetic_ray_witness(
            object(), object(), speed=0.6, synthetic_test_only=opt_in
        )


@pytest.mark.parametrize(
    "defect",
    [
        "speed",
        "bool_speed",
        "age",
        "turn",
        "shape",
        "bool_ranges",
        "nonfinite",
        "range",
        "mask",
        "invalid_padding",
    ],
)
def test_synthetic_ray_probe_rejects_malformed_artificial_input(defect):
    from sim.navigation import probe_synthetic_ray_witness

    ranges, valid = np.full(8, 0.3), np.ones(8, dtype=bool)
    settings = {
        "speed": 0.6,
        "config": Config(noise_std=0, latency_ticks=0),
        "synthetic_test_only": True,
    }
    if defect == "speed":
        settings["speed"] = 1
    elif defect == "bool_speed":
        settings["speed"] = True
    elif defect == "age":
        settings["tof_age_s"] = -1
    elif defect == "turn":
        settings["turn_rate"] = float("nan")
    elif defect == "shape":
        ranges = np.full((8, 8), 0.3)
    elif defect == "bool_ranges":
        ranges = np.ones(8, dtype=bool)
    elif defect == "nonfinite":
        ranges[0] = float("inf")
    elif defect == "range":
        ranges[0] = 5
    elif defect == "mask":
        valid = np.ones(8)
    else:
        valid[0] = False
    with pytest.raises(ValueError):
        probe_synthetic_ray_witness(ranges, valid, **settings)


def test_synthetic_ray_probe_saturation_inside_footprint_is_not_a_surface_hit():
    from sim.navigation import probe_synthetic_ray_witness

    config = Config(noise_std=0, latency_ticks=0, max_range=0.3)
    result = probe_synthetic_ray_witness(
        np.full(8, config.max_range),
        np.ones(8, dtype=bool),
        speed=0.6,
        config=config,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown" and result["witness_columns"] == []


def test_synthetic_ray_probe_unresolved_numerical_scale_abstains():
    from sim.navigation import probe_synthetic_ray_witness

    config = Config(noise_std=0, latency_ticks=0, radius=1e-16)
    result = probe_synthetic_ray_witness(
        np.full(8, 0.3),
        np.ones(8, dtype=bool),
        speed=0.6,
        config=config,
        synthetic_test_only=True,
    )
    assert result["status"] == "unknown" and result["reason"] == "numerical_unknown"


@pytest.mark.parametrize(
    "error,status",
    [(0.0, "blocked_witness"), (0.01, "blocked_witness"), (0.2, "unknown")],
)
def test_bounded_ray_probe_uncertainty_can_remove_but_not_create_witnesses(
    error, status
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid = np.zeros(8), np.zeros(8, dtype=bool)
    ranges[3], valid[3] = 0.3, True
    result = probe_synthetic_bounded_ray_witness(
        ranges,
        valid,
        speed=0.6,
        range_error_m=error,
        translation_error_m=error,
        heading_error_rad=error,
        config=Config(noise_std=0, latency_ticks=0),
        synthetic_test_only=True,
    )
    assert result["status"] == status
    assert result["witness_columns"] == ([3] if status == "blocked_witness" else [])
    assert result["synthetic"] and not result["training_approved"]
    assert not result["real_input_qualified"] and not result["physical_safety_claim"]
    json.dumps(result, allow_nan=False)


def test_bounded_ray_probe_does_not_qualify_normal_defaults():
    from sim.navigation import probe_synthetic_bounded_ray_witness

    result = probe_synthetic_bounded_ray_witness(
        np.full(8, 0.3),
        np.ones(8, dtype=bool),
        speed=0.6,
        range_error_m=0.01,
        translation_error_m=0.01,
        heading_error_rad=0.01,
        synthetic_test_only=True,
    )
    assert (
        result["status"] == "unknown" and result["reason"] == "noise_model_unqualified"
    )


@pytest.fixture
def bounded_ray_fixture():
    ranges, valid = np.zeros(8), np.zeros(8, dtype=bool)
    ranges[3], valid[3] = 0.3, True
    return (
        ranges,
        valid,
        {
            "speed": 0.6,
            "range_error_m": 0.01,
            "translation_error_m": 0.01,
            "heading_error_rad": 0.01,
            "config": Config(noise_std=0, latency_ticks=0),
            "synthetic_test_only": True,
        },
    )


def test_bounded_ray_probe_sampled_perturbations_respect_error_ball_and_footprint(
    bounded_ray_fixture,
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    original = deepcopy((ranges, valid, settings))
    result = probe_synthetic_bounded_ray_witness(ranges, valid, **settings)
    assert result["status"] == "blocked_witness"
    angle = np.linspace(
        settings["config"].field_of_view / 2, -settings["config"].field_of_view / 2, 8
    )[3]
    nominal = ranges[3] * np.array([math.cos(angle), math.sin(angle)])
    distance = settings["speed"] * settings["config"].dt + settings["speed"] ** 2 / (
        2 * settings["config"].acceleration
    )
    for radial in (-settings["range_error_m"], 0, settings["range_error_m"]):
        for heading in (
            -settings["heading_error_rad"],
            0,
            settings["heading_error_rad"],
        ):
            for direction in np.linspace(0, 2 * math.pi, 8, endpoint=False):
                translation = settings["translation_error_m"] * np.array(
                    [math.cos(direction), math.sin(direction)]
                )
                point = (ranges[3] + radial) * np.array(
                    [math.cos(angle + heading), math.sin(angle + heading)]
                ) + translation
                assert (
                    np.linalg.norm(point - nominal)
                    <= result["point_error_bound_m"][3] + 1e-12
                )
                assert (
                    math.hypot(point[0] - np.clip(point[0], 0, distance), point[1])
                    < settings["config"].radius
                )
    np.testing.assert_array_equal(ranges, original[0])
    np.testing.assert_array_equal(valid, original[1])
    assert settings == original[2]
    result["assumed_error_bounds"]["range_error_m"] = 1
    assert settings == original[2]


@pytest.mark.parametrize(
    "field,value",
    [("range_error_m", 0.2), ("translation_error_m", 0.2), ("heading_error_rad", 1.0)],
)
def test_bounded_ray_probe_each_error_component_can_remove_a_witness(
    bounded_ray_fixture, field, value
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    result = probe_synthetic_bounded_ray_witness(
        ranges, valid, **{**settings, field: value}
    )
    assert result["status"] == "unknown" and result["witness_columns"] == []


@pytest.mark.parametrize(
    "offset,status", [(-1e-6, "blocked_witness"), (0, "unknown"), (1e-6, "unknown")]
)
def test_bounded_ray_probe_error_ball_contact_abstains(
    bounded_ray_fixture, offset, status
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    angle = np.linspace(
        settings["config"].field_of_view / 2, -settings["config"].field_of_view / 2, 8
    )[3]
    distance = settings["speed"] * settings["config"].dt + settings["speed"] ** 2 / (
        2 * settings["config"].acceleration
    )
    separation = math.hypot(
        ranges[3] * math.cos(angle) - distance, ranges[3] * math.sin(angle)
    )
    result = probe_synthetic_bounded_ray_witness(
        ranges,
        valid,
        **{
            **settings,
            "range_error_m": 0,
            "heading_error_rad": 0,
            "translation_error_m": settings["config"].radius - separation + offset,
        },
    )
    assert result["status"] == status


@pytest.mark.parametrize("radial_error", [0.05, 0.3])
def test_bounded_ray_probe_unsupported_range_interval_stays_unknown(
    bounded_ray_fixture, radial_error
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    result = probe_synthetic_bounded_ray_witness(
        ranges,
        valid,
        **{
            **settings,
            "range_error_m": radial_error,
            "config": Config(noise_std=0, latency_ticks=0, max_range=0.35),
        },
    )
    assert result["status"] == "unknown" and result["witness_columns"] == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("range_error_m", -0.1),
        ("range_error_m", True),
        ("range_error_m", float("nan")),
        ("range_error_m", 10**400),
        ("range_error_m", -(10**400)),
        ("translation_error_m", None),
        ("translation_error_m", -0.1),
        ("translation_error_m", float("inf")),
        ("translation_error_m", 10**400),
        ("translation_error_m", -(10**400)),
        ("heading_error_rad", math.pi + 1e-6),
        ("heading_error_rad", -0.1),
        ("heading_error_rad", False),
        ("heading_error_rad", 10**400),
        ("heading_error_rad", -(10**400)),
    ],
)
def test_bounded_ray_probe_rejects_invalid_assumed_bounds(
    bounded_ray_fixture, field, value
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    with pytest.raises(ValueError):
        probe_synthetic_bounded_ray_witness(ranges, valid, **{**settings, field: value})


def test_bounded_ray_probe_scope_checked_before_inputs(bounded_ray_fixture):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    _, _, settings = bounded_ray_fixture
    with pytest.raises(ValueError, match="synthetic-test-only"):
        probe_synthetic_bounded_ray_witness(
            object(), object(), **{**settings, "synthetic_test_only": 1}
        )


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"config": Config(noise_std=0)}, "registration_unqualified"),
        ({"tof_age_s": 0.1}, "registration_unqualified"),
        ({"turn_rate": 0.1}, "curved_reference_not_supported"),
    ],
)
def test_bounded_ray_probe_cannot_override_unqualified_assumptions(
    bounded_ray_fixture, override, reason
):
    from sim.navigation import probe_synthetic_bounded_ray_witness

    ranges, valid, settings = bounded_ray_fixture
    result = probe_synthetic_bounded_ray_witness(
        ranges, valid, **{**settings, **override}
    )
    assert result["status"] == "unknown" and result["reason"] == reason


@pytest.fixture
def registration_fixture():
    return {
        "points": [[1.0, 0.0], [0.0, 1.0]],
        "sensor_pose": [0.0, 0.0, 0.0],
        "acquisition_pose": [0.0, 0.0, 0.0],
        "reference_pose": [0.0, 0.0, 0.0],
        "acquisition_time_s": 1.0,
        "reference_time_s": 1.1,
        "synthetic_test_only": True,
    }


@pytest.mark.parametrize(
    "poses,expected",
    [
        ({}, [[1, 0], [0, 1]]),
        ({"sensor_pose": [0.25, -0.5, 0]}, [[1.25, -0.5], [0.25, 0.5]]),
        ({"reference_pose": [1, 0, 0]}, [[0, 0], [-1, 1]]),
        ({"reference_pose": [0, 0, math.pi / 2]}, [[0, -1], [1, 0]]),
        ({"acquisition_pose": [0, 0, math.pi / 2]}, [[0, 1], [-1, 0]]),
        (
            {
                "sensor_pose": [0.5, 0, math.pi / 2],
                "acquisition_pose": [2, 4, 0],
                "reference_pose": [2, 3, math.pi / 2],
            },
            [[2, -0.5], [1, 0.5]],
        ),
    ],
)
def test_registration_reference_analytic_fixtures(
    registration_fixture, poses, expected
):
    from sim.navigation import register_synthetic_points

    result = register_synthetic_points(**{**registration_fixture, **poses})
    assert result["status"] == "registered_fixture"
    np.testing.assert_allclose(result["reference_points_m"], expected, atol=1e-14)
    assert result["elapsed_s"] == pytest.approx(0.1)
    assert result["synthetic"] and not result["training_approved"]
    assert not result["real_input_qualified"] and not result["physical_safety_claim"]
    assert all(result["assumptions"].values())
    assert "labels" not in result and "witness_columns" not in result
    json.dumps(result, allow_nan=False)


def test_registration_reference_composition_and_inverse(registration_fixture):
    from sim.navigation import register_synthetic_points

    first, middle, last = [1, 2, 0.3], [-1, 3, -0.4], [2, -2, 0.8]
    first_to_middle = register_synthetic_points(
        **{**registration_fixture, "acquisition_pose": first, "reference_pose": middle}
    )
    composed = register_synthetic_points(
        **{
            **registration_fixture,
            "points": first_to_middle["reference_points_m"],
            "acquisition_pose": middle,
            "reference_pose": last,
        }
    )
    direct = register_synthetic_points(
        **{**registration_fixture, "acquisition_pose": first, "reference_pose": last}
    )
    np.testing.assert_allclose(
        composed["reference_points_m"], direct["reference_points_m"], atol=1e-14
    )
    inverse = register_synthetic_points(
        **{
            **registration_fixture,
            "points": first_to_middle["reference_points_m"],
            "acquisition_pose": middle,
            "reference_pose": first,
        }
    )
    np.testing.assert_allclose(
        inverse["reference_points_m"], registration_fixture["points"], atol=1e-14
    )


def test_registration_reference_common_large_offset_preserves_local_points(
    registration_fixture,
):
    from sim.navigation import register_synthetic_points

    result = register_synthetic_points(
        **{
            **registration_fixture,
            "points": [[0.125, -0.25]],
            "sensor_pose": [0.25, 0.5, 0],
            "acquisition_pose": [1e16, -1e16, 0],
            "reference_pose": [1e16, -1e16, 0],
        }
    )
    np.testing.assert_array_equal(result["reference_points_m"], [[0.375, 0.25]])


@pytest.mark.parametrize("heading", [1e16, -1e16])
def test_registration_reference_large_heading_matches_bounded_orientation(
    registration_fixture, heading
):
    from sim.navigation import register_synthetic_points

    poses = {
        "sensor_pose": [0.5, -0.25, heading],
        "acquisition_pose": [1, 2, -heading],
        "reference_pose": [2, 3, heading],
    }
    actual = register_synthetic_points(**{**registration_fixture, **poses})
    bounded = {
        name: [*pose[:2], math.atan2(math.sin(pose[2]), math.cos(pose[2]))]
        for name, pose in poses.items()
    }
    expected = register_synthetic_points(**{**registration_fixture, **bounded})
    np.testing.assert_allclose(
        actual["reference_points_m"], expected["reference_points_m"], atol=1e-14
    )


@pytest.mark.parametrize(
    "field,reason",
    [
        ("acquisition_time_s", "missing_timing"),
        ("reference_time_s", "missing_timing"),
        ("sensor_pose", "missing_pose"),
        ("acquisition_pose", "missing_pose"),
        ("reference_pose", "missing_pose"),
    ],
)
def test_registration_reference_missing_evidence_stays_unknown(
    registration_fixture, field, reason
):
    from sim.navigation import register_synthetic_points

    result = register_synthetic_points(**{**registration_fixture, field: None})
    assert result["status"] == "unknown" and result["reason"] == reason
    assert result["reference_points_m"] is None
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "field,value",
    [
        ("points", [[True, 0]]),
        ("points", [[1, float("nan")]]),
        ("points", [[1, 2, 3]]),
        ("points", [1, 2]),
        ("points", []),
        ("sensor_pose", [0, 0]),
        ("sensor_pose", [0, 0, float("inf")]),
        ("acquisition_pose", [0, True, 0]),
        ("reference_pose", [0, 0, "0"]),
        ("acquisition_time_s", True),
        ("acquisition_time_s", -1),
        ("reference_time_s", float("nan")),
        ("reference_time_s", float("inf")),
        ("reference_time_s", "1.1"),
        ("reference_time_s", 0.5),
        ("points", [[10**400, 0]]),
        ("points", [[-(10**400), 0]]),
        ("sensor_pose", [0, 0, 10**400]),
        ("acquisition_pose", [10**400, 0, 0]),
        ("reference_pose", [-(10**400), 0, 0]),
        ("acquisition_time_s", 10**400),
        ("reference_time_s", 10**400),
    ],
)
def test_registration_reference_rejects_invalid_evidence(
    registration_fixture, field, value
):
    from sim.navigation import register_synthetic_points

    with pytest.raises(ValueError):
        register_synthetic_points(**{**registration_fixture, field: value})


@pytest.mark.parametrize("opt_in", [False, None, 1, "yes"])
def test_registration_reference_requires_scope_before_inputs(
    registration_fixture, opt_in
):
    from sim.navigation import register_synthetic_points

    with pytest.raises(ValueError, match="synthetic-test-only"):
        register_synthetic_points(
            **{
                **registration_fixture,
                "points": object(),
                "synthetic_test_only": opt_in,
            }
        )


def test_registration_reference_numerical_overflow_stays_unknown(registration_fixture):
    from sim.navigation import register_synthetic_points

    result = register_synthetic_points(
        **{
            **registration_fixture,
            "acquisition_pose": [1e308, 0, 0],
            "reference_pose": [-1e308, 0, 0],
        }
    )
    assert result["status"] == "unknown" and result["reason"] == "numerical_unknown"
    assert result["reference_points_m"] is None
    json.dumps(result, allow_nan=False)


def test_registration_reference_is_detached_and_does_not_qualify_witnesses(
    registration_fixture, bounded_ray_fixture
):
    from sim.navigation import (
        probe_synthetic_bounded_ray_witness,
        register_synthetic_points,
    )

    original = deepcopy(registration_fixture)
    result = register_synthetic_points(**registration_fixture)
    result["reference_points_m"][0][0] = 100
    result["assumptions"]["static_world"] = False
    assert registration_fixture == original
    ranges, valid, settings = bounded_ray_fixture
    for override, reason in (
        ({"config": Config()}, "noise_model_unqualified"),
        ({"config": Config(noise_std=0)}, "registration_unqualified"),
        ({"tof_age_s": 0.1}, "registration_unqualified"),
        ({"turn_rate": 0.1}, "curved_reference_not_supported"),
    ):
        probe = probe_synthetic_bounded_ray_witness(
            ranges, valid, **{**settings, **override}
        )
        assert probe["status"] == "unknown" and probe["reason"] == reason


@pytest.fixture
def bounded_registration_fixture(registration_fixture):
    return {
        **registration_fixture,
        "point_error_m": 0.0,
        "pose_error_bounds": {
            name: {"translation_m": 0.0, "heading_rad": 0.0}
            for name in ("sensor_pose", "acquisition_pose", "reference_pose")
        },
    }


def test_bounded_registration_zero_errors_match_exact_reference(
    bounded_registration_fixture,
):
    from sim.navigation import register_synthetic_bounded_points

    result = register_synthetic_bounded_points(**bounded_registration_fixture)
    assert result["status"] == "bounded_fixture"
    assert result["reference_points_m"] == bounded_registration_fixture["points"]
    assert result["point_error_bound_m"] == [0.0, 0.0]
    assert not result["floating_point_certified"]
    assert result["bound_semantics"] == "assumed_model_exact_arithmetic"
    assert result["synthetic"] and not result["training_approved"]
    assert not result["real_input_qualified"] and not result["physical_safety_claim"]
    assert "labels" not in result and "witness_columns" not in result
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "pose,field",
    [(None, "point_error_m")]
    + [
        (name, field)
        for name in ("sensor_pose", "acquisition_pose", "reference_pose")
        for field in ("translation_m", "heading_rad")
    ],
)
def test_bounded_registration_each_component_has_analytic_effect(
    bounded_registration_fixture, pose, field
):
    from sim.navigation import register_synthetic_bounded_points

    settings = deepcopy(bounded_registration_fixture)
    if pose is None:
        settings[field] = 0.1
    else:
        settings["pose_error_bounds"][pose][field] = 0.1
    result = register_synthetic_bounded_points(**settings)
    expected = 2 * math.sin(0.05) if field == "heading_rad" else 0.1
    np.testing.assert_allclose(result["point_error_bound_m"], [expected, expected])


def test_bounded_registration_heading_errors_use_distinct_lever_arms(
    bounded_registration_fixture,
):
    from sim.navigation import register_synthetic_bounded_points

    settings = deepcopy(bounded_registration_fixture)
    settings.update(
        points=[[1, 0]],
        sensor_pose=[0.5, 0, 0],
        acquisition_pose=[1, 0, 0],
        point_error_m=0.01,
    )
    for name, translation, heading in (
        ("sensor_pose", 0.02, 0.01),
        ("acquisition_pose", 0.03, 0.02),
        ("reference_pose", 0.04, 0.03),
    ):
        settings["pose_error_bounds"][name] = {
            "translation_m": translation,
            "heading_rad": heading,
        }
    result = register_synthetic_bounded_points(**settings)
    expected = 0.1 + 2 * math.sin(0.005) + 3 * math.sin(0.01) + 5 * math.sin(0.015)
    assert result["reference_points_m"] == [[2.5, 0.0]]
    assert result["point_error_bound_m"] == pytest.approx([expected])
    assert "exact_fixture_poses" not in result["assumptions"]
    assert result["assumptions"]["bounded_point_and_pose_errors"]


def test_bounded_registration_sampled_perturbations_fit_declared_enclosure(
    bounded_registration_fixture,
):
    from itertools import product

    from sim.navigation import register_synthetic_bounded_points

    settings = deepcopy(bounded_registration_fixture)
    settings.update(
        points=[[1, 0.5], [-0.4, 0.2]],
        sensor_pose=[0.3, -0.2, 0.4],
        acquisition_pose=[1, 2, -0.3],
        reference_pose=[-2, 0.5, 0.6],
        point_error_m=0.01,
    )
    names = ("sensor_pose", "acquisition_pose", "reference_pose")
    for index, name in enumerate(names):
        settings["pose_error_bounds"][name] = {
            "translation_m": 0.02 + 0.01 * index,
            "heading_rad": 0.01 + 0.01 * index,
        }
    original = deepcopy(settings)
    result = register_synthetic_bounded_points(**settings)

    def transform(point, pose):
        cosine, sine = math.cos(pose[2]), math.sin(pose[2])
        return np.array(
            [
                cosine * point[0] - sine * point[1] + pose[0],
                sine * point[0] + cosine * point[1] + pose[1],
            ]
        )

    checked = 0
    for heading_signs in product((-1, 0, 1), repeat=3):
        for direction, point_direction in product(range(4), repeat=2):
            perturbed = {}
            for index, name in enumerate(names):
                pose, errors = settings[name], settings["pose_error_bounds"][name]
                angle = (direction + index) * math.pi / 2
                perturbed[name] = [
                    pose[0] + errors["translation_m"] * math.cos(angle),
                    pose[1] + errors["translation_m"] * math.sin(angle),
                    pose[2] + heading_signs[index] * errors["heading_rad"],
                ]
            angle = point_direction * math.pi / 2
            for index, point in enumerate(settings["points"]):
                displaced = np.asarray(point) + settings["point_error_m"] * np.array(
                    [math.cos(angle), math.sin(angle)]
                )
                body = transform(displaced, perturbed["sensor_pose"])
                world = transform(body, perturbed["acquisition_pose"])
                reference = perturbed["reference_pose"]
                relative = world - reference[:2]
                actual = transform(relative, [0, 0, -reference[2]])
                separation = np.linalg.norm(
                    actual - result["reference_points_m"][index]
                )
                assert separation <= result["point_error_bound_m"][index] + 1e-12
                checked += 1
    assert checked == 864
    assert settings == original
    result["assumed_error_bounds"]["point_error_m"] = 100
    result["reference_points_m"][0][0] = 100
    assert settings == original


@pytest.mark.parametrize(
    "defect",
    [
        "missing_pose",
        "extra_pose",
        "missing_component",
        "extra_component",
        "wrong_container",
        "wrong_row",
        "negative_point",
        "boolean_point",
        "overflow_point",
        "nan_translation",
        "overflow_translation",
        "boolean_translation",
        "infinite_heading",
        "negative_heading",
        "large_heading",
    ],
)
def test_bounded_registration_rejects_malformed_bounds(
    bounded_registration_fixture, defect
):
    from sim.navigation import register_synthetic_bounded_points

    settings = deepcopy(bounded_registration_fixture)
    rows = settings["pose_error_bounds"]
    if defect == "missing_pose":
        del rows["reference_pose"]
    elif defect == "extra_pose":
        rows["extra"] = rows["reference_pose"].copy()
    elif defect == "missing_component":
        del rows["sensor_pose"]["heading_rad"]
    elif defect == "extra_component":
        rows["sensor_pose"]["extra"] = 0
    elif defect == "wrong_container":
        settings["pose_error_bounds"] = []
    elif defect == "wrong_row":
        rows["sensor_pose"] = []
    elif defect.endswith("point"):
        settings["point_error_m"] = {
            "negative_point": -0.1,
            "boolean_point": True,
            "overflow_point": 10**400,
        }[defect]
    elif defect.endswith("translation"):
        rows["sensor_pose"]["translation_m"] = {
            "nan_translation": float("nan"),
            "overflow_translation": 10**400,
            "boolean_translation": False,
        }[defect]
    else:
        rows["reference_pose"]["heading_rad"] = {
            "infinite_heading": float("inf"),
            "negative_heading": -0.1,
            "large_heading": math.pi + 1e-6,
        }[defect]
    with pytest.raises(ValueError):
        register_synthetic_bounded_points(**settings)


@pytest.mark.parametrize("field", ["acquisition_time_s", "reference_pose"])
def test_bounded_registration_missing_nominal_evidence_stays_unknown(
    bounded_registration_fixture, field
):
    from sim.navigation import register_synthetic_bounded_points

    result = register_synthetic_bounded_points(
        **{**bounded_registration_fixture, field: None}
    )
    assert result["status"] == "unknown"
    assert (
        result["reference_points_m"] is None and result["point_error_bound_m"] is None
    )
    json.dumps(result, allow_nan=False)


def test_bounded_registration_nonfinite_enclosure_stays_unknown(
    bounded_registration_fixture,
):
    from sim.navigation import register_synthetic_bounded_points

    settings = deepcopy(bounded_registration_fixture)
    for row in settings["pose_error_bounds"].values():
        row["translation_m"] = 1e308
    result = register_synthetic_bounded_points(**settings)
    assert result["status"] == "unknown" and result["reason"] == "numerical_unknown"
    assert (
        result["reference_points_m"] is None and result["point_error_bound_m"] is None
    )
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("opt_in", [False, 1])
def test_bounded_registration_checks_scope_before_inputs(
    bounded_registration_fixture, opt_in
):
    from sim.navigation import register_synthetic_bounded_points

    with pytest.raises(ValueError, match="synthetic-test-only"):
        register_synthetic_bounded_points(
            **{
                **bounded_registration_fixture,
                "points": object(),
                "synthetic_test_only": opt_in,
            }
        )


@pytest.fixture
def registered_witness_fixture(bounded_registration_fixture):
    return {
        **deepcopy(bounded_registration_fixture),
        "points": [[0.3, 0.0]],
        "point_error_m": 0.01,
        "speed": 0.6,
        "assume_obstacle_points": True,
        "config": Config(noise_std=0, latency_ticks=0),
    }


@pytest.mark.parametrize(
    "point,error,status",
    [
        ([0.3, 0], 0.01, "blocked_witness"),
        ([0.3, 0], 0.1, "unknown"),
        ([1, 1], 0.01, "unknown"),
    ],
)
def test_registered_witness_requires_entire_error_ball_inside(
    registered_witness_fixture, point, error, status
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, "points": [point], "point_error_m": error}
    )
    assert result["status"] == status
    assert result["witness_indices"] == ([0] if status == "blocked_witness" else [])
    assert result["braking_distance_m"] == pytest.approx(0.21)
    assert result["synthetic"] and not result["training_approved"]
    assert not result["real_input_qualified"] and not result["physical_safety_claim"]
    assert not result["floating_point_certified"]
    assert "labels" not in result and "path_blocked" not in result
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "offset,status", [(-1e-6, "blocked_witness"), (0, "unknown"), (1e-6, "unknown")]
)
def test_registered_witness_error_ball_contact_abstains(
    registered_witness_fixture, offset, status
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, "points": [[0.1, 0.17 + offset]]}
    )
    assert result["status"] == status


@pytest.mark.parametrize(
    "override,reason",
    [
        ({"assume_obstacle_points": False}, "obstacle_membership_unqualified"),
        ({"config": None}, "noise_model_unqualified"),
        ({"config": Config(noise_std=0)}, "registration_unqualified"),
        ({"turn_rate": 0.1}, "curved_reference_not_supported"),
        ({"reference_pose": None}, "missing_pose"),
        ({"acquisition_time_s": None}, "missing_timing"),
    ],
)
def test_registered_witness_unsupported_evidence_stays_unknown(
    registered_witness_fixture, override, reason
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, **override}
    )
    assert result["status"] == "unknown" and result["reason"] == reason
    assert result["witness_indices"] == []
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "field,value,exception",
    [
        ("speed", -0.1, ValueError),
        ("speed", 0.7, ValueError),
        ("speed", True, TypeError),
        ("speed", float("nan"), ValueError),
        ("speed", 10**400, ValueError),
        ("turn_rate", 2.0, ValueError),
        ("turn_rate", float("inf"), ValueError),
        ("turn_rate", False, TypeError),
        ("assume_obstacle_points", 1, TypeError),
        ("assume_obstacle_points", None, TypeError),
        ("assume_obstacle_points", "yes", TypeError),
    ],
)
def test_registered_witness_rejects_malformed_motion_or_membership(
    registered_witness_fixture, field, value, exception
):
    from sim.navigation import probe_synthetic_registered_witness

    with pytest.raises(exception):
        probe_synthetic_registered_witness(
            **{**registered_witness_fixture, field: value}
        )


@pytest.mark.parametrize("opt_in", [False, 1])
def test_registered_witness_scope_precedes_inputs(registered_witness_fixture, opt_in):
    from sim.navigation import probe_synthetic_registered_witness

    with pytest.raises(ValueError, match="synthetic-test-only"):
        probe_synthetic_registered_witness(
            **{
                **registered_witness_fixture,
                "points": object(),
                "synthetic_test_only": opt_in,
            }
        )


def test_registered_witness_one_positive_survives_other_unknown_points(
    registered_witness_fixture,
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, "points": [[1e16, 0], [0.3, 0]]}
    )
    assert result["status"] == "blocked_witness" and result["witness_indices"] == [1]
    unknown = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, "points": [[1e16, 0]]}
    )
    assert unknown["status"] == "unknown" and unknown["reason"] == "numerical_unknown"


@pytest.mark.parametrize(
    "point,obstacles,collision,status",
    [
        ([0.4, 0], ((3.4, 3, 0.001),), True, "blocked_witness"),
        ([1.1, 1], ((4.1, 4, 0.001),), False, "unknown"),
        ([1.1, 1], ((4.1, 4, 0.001), (3.4, 3, 0.001)), True, "unknown"),
    ],
)
def test_registered_witness_independent_world_geometry(
    registered_witness_fixture, point, obstacles, collision, status
):
    from sim.navigation import probe_synthetic_registered_witness

    settings = {
        **registered_witness_fixture,
        "points": [point],
        "acquisition_pose": [3, 3, 0],
        "reference_pose": [3.1, 3, 0],
    }
    result = probe_synthetic_registered_witness(**settings)
    config = settings["config"]
    distance = settings["speed"] * config.dt + settings["speed"] ** 2 / (
        2 * config.acceleration
    )
    assert (
        swept_collision((3.1, 3), (3.1 + distance, 3), config.radius, obstacles, (6, 6))
        is collision
    )
    assert result["status"] == status
    assert result["acquisition_time_s"] < result["reference_time_s"]
    np.testing.assert_allclose(
        result["reference_points_m"], [[point[0] - 0.1, point[1]]]
    )


@pytest.mark.parametrize("heading", [-math.pi / 3, 0, math.pi / 3])
def test_registered_witness_perturbed_world_points_all_collide(
    registered_witness_fixture, heading
):
    from itertools import product

    from sim.navigation import probe_synthetic_registered_witness

    settings = deepcopy(registered_witness_fixture)
    settings.update(
        points=[[0.35, 0]],
        point_error_m=0.003,
        sensor_pose=[0.05, 0, 0.1],
        acquisition_pose=[3, 3, heading],
        reference_pose=[
            3 + 0.1 * math.cos(heading),
            3 + 0.1 * math.sin(heading),
            heading,
        ],
    )
    names = ("sensor_pose", "acquisition_pose", "reference_pose")
    for name in names:
        settings["pose_error_bounds"][name] = {
            "translation_m": 0.002,
            "heading_rad": 0.003,
        }
    result = probe_synthetic_registered_witness(**settings)
    assert result["status"] == "blocked_witness" and result["witness_indices"] == [0]
    config = settings["config"]
    distance = settings["speed"] * config.dt + settings["speed"] ** 2 / (
        2 * config.acceleration
    )

    def transform(point, pose):
        cosine, sine = math.cos(pose[2]), math.sin(pose[2])
        return np.array(
            [
                point[0] * cosine - point[1] * sine + pose[0],
                point[0] * sine + point[1] * cosine + pose[1],
            ]
        )

    checked = 0
    for signs in product((-1, 0, 1), repeat=3):
        for direction, point_direction in product(range(8), range(4)):
            poses = {}
            for index, name in enumerate(names):
                pose = settings[name]
                angle = (direction + index) * math.pi / 4
                poses[name] = [
                    pose[0] + 0.002 * math.cos(angle),
                    pose[1] + 0.002 * math.sin(angle),
                    pose[2] + 0.003 * signs[index],
                ]
            angle = point_direction * math.pi / 2
            point = np.asarray(settings["points"][0]) + 0.003 * np.array(
                [math.cos(angle), math.sin(angle)]
            )
            body = transform(point, poses["sensor_pose"])
            world = transform(body, poses["acquisition_pose"])
            reference = poses["reference_pose"]
            actual = transform(world - reference[:2], [0, 0, -reference[2]])
            error = np.linalg.norm(actual - result["reference_points_m"][0])
            assert error <= result["point_error_bound_m"][0] + 1e-12
            start = np.asarray(reference[:2])
            end = start + distance * np.array(
                [math.cos(reference[2]), math.sin(reference[2])]
            )
            assert swept_collision(start, end, config.radius, ((*world, 1e-6),), (6, 6))
            checked += 1
    assert checked == 864


def test_registered_witness_association_is_required_by_default(
    registered_witness_fixture,
):
    from sim.navigation import probe_synthetic_registered_witness

    settings = dict(registered_witness_fixture)
    del settings["assume_obstacle_points"]
    result = probe_synthetic_registered_witness(**settings)
    assert (
        result["status"] == "unknown"
        and result["reason"] == "obstacle_membership_unqualified"
    )


def test_registered_witness_inputs_and_results_are_detached(registered_witness_fixture):
    from sim.navigation import probe_synthetic_registered_witness

    original = deepcopy(registered_witness_fixture)
    result = probe_synthetic_registered_witness(**registered_witness_fixture)
    result["reference_points_m"][0][0] = 100
    result["assumed_error_bounds"]["point_error_m"] = 100
    result["assumptions"]["obstacle_membership"] = False
    result["witness_indices"].clear()
    assert registered_witness_fixture == original
    assert probe_synthetic_registered_witness(**registered_witness_fixture)[
        "witness_indices"
    ] == [0]


def test_registered_witness_nonfinite_braking_distance_abstains(
    registered_witness_fixture,
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{
            **registered_witness_fixture,
            "speed": 1e308,
            "config": Config(max_speed=1e308, noise_std=0, latency_ticks=0),
        }
    )
    assert result["status"] == "unknown" and result["reason"] == "numerical_unknown"
    assert result["braking_distance_m"] is None
    json.dumps(result, allow_nan=False)


def test_registered_witness_invalid_config_is_rejected(registered_witness_fixture):
    from sim.navigation import probe_synthetic_registered_witness

    with pytest.raises(TypeError, match="Config"):
        probe_synthetic_registered_witness(
            **{**registered_witness_fixture, "config": object()}
        )


def test_registered_witness_cannot_bypass_registration_bound_validation(
    registered_witness_fixture,
):
    from sim.navigation import probe_synthetic_registered_witness

    settings = deepcopy(registered_witness_fixture)
    settings["pose_error_bounds"]["reference_pose"]["heading_rad"] = float("nan")
    with pytest.raises(ValueError):
        probe_synthetic_registered_witness(**settings)


@pytest.mark.parametrize("axis", [0, 1])
def test_registered_witness_source_cancellation_cannot_create_positive(
    registered_witness_fixture, axis
):
    from fractions import Fraction

    from sim.navigation import probe_synthetic_registered_witness

    point, mounting, reference = [0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    point[axis], mounting[axis], reference[axis] = 1e16, 1.0, 1e16
    exact = Fraction(point[axis]) + Fraction(mounting[axis]) - Fraction(reference[axis])
    assert exact == 1
    obstacle = [3.0, 3.0, 1e-6]
    obstacle[axis] += float(exact)
    assert not swept_collision((3, 3), (3.21, 3), 0.18, (obstacle,), (6, 6))
    result = probe_synthetic_registered_witness(
        **{
            **registered_witness_fixture,
            "points": [point],
            "sensor_pose": mounting,
            "reference_pose": reference,
            "point_error_m": 0.0,
        }
    )
    assert result["reference_points_m"] == [[0.0, 0.0]]
    assert result["status"] == "unknown" and result["reason"] == "numerical_unknown"
    assert result["witness_indices"] == []


@pytest.mark.parametrize(
    "point,status", [([0.1, 0], "blocked_witness"), ([0.3, 0], "unknown")]
)
def test_registered_witness_at_rest_uses_current_footprint_only(
    registered_witness_fixture, point, status
):
    from sim.navigation import probe_synthetic_registered_witness

    result = probe_synthetic_registered_witness(
        **{**registered_witness_fixture, "speed": 0.0, "points": [point]}
    )
    assert result["braking_distance_m"] == 0.0
    assert result["status"] == status


@pytest.fixture
def gaussian_draft_half_width():
    from statistics import NormalDist

    def half_width(failure_budget, maximum_draws):
        return -Config().noise_std * NormalDist().inv_cdf(
            failure_budget / (2 * maximum_draws)
        )

    return half_width


@pytest.mark.parametrize("failure_budget", [0.1, 0.01, 0.001])
@pytest.mark.parametrize("maximum_draws", [64, 512, 25664, 205312])
def test_gaussian_coverage_draft_union_bound_arithmetic(
    gaussian_draft_half_width, failure_budget, maximum_draws
):
    half_width = gaussian_draft_half_width(failure_budget, maximum_draws)
    marginal_failure = math.erfc(half_width / (Config().noise_std * math.sqrt(2)))
    assert marginal_failure > 0
    assert maximum_draws * marginal_failure == pytest.approx(failure_budget, rel=1e-12)


def test_gaussian_coverage_draft_budget_counts_and_monotonicity(
    gaussian_draft_half_width,
):
    from itertools import pairwise

    config = Config()
    budgets = [
        64,
        64 * config.history_ticks,
        64 * (config.max_ticks + 1),
        8 * 64 * (config.max_ticks + 1),
    ]
    assert budgets == [64, 512, 25664, 205312]
    widths = [gaussian_draft_half_width(0.01, count) for count in budgets]
    assert all(earlier < later for earlier, later in pairwise(widths))
    assert gaussian_draft_half_width(0.001, budgets[-1]) > widths[-1]


@pytest.mark.parametrize("failure_budget", [0.1, 0.01, 0.001])
def test_gaussian_coverage_draft_clipping_and_float32_surface_filter(
    gaussian_draft_half_width, failure_budget
):
    config = Config()
    error = gaussian_draft_half_width(failure_budget, 512)
    quantization = float(np.spacing(np.float32(config.max_range))) / 2
    for reference in (0.0, 0.001, 0.1, 2.0, 3.99, config.max_range):
        for fraction in (-1, -0.75, -0.25, 0, 0.25, 0.75, 1):
            observed = float(
                np.float32(np.clip(reference + fraction * error, 0, config.max_range))
            )
            assert abs(observed - reference) <= error + quantization + 1e-14
            if (
                observed - error - quantization > 0
                and observed + error + quantization < config.max_range
            ):
                assert 0 < reference < config.max_range


def test_gaussian_coverage_draft_masked_zero_has_no_surface_information():
    config = Config()
    observed = [
        float(np.where(False, reference, 0)) for reference in (0, 1, config.max_range)
    ]
    assert observed == [0, 0, 0]


def test_gaussian_coverage_draft_finite_interval_can_fail_outside_event(
    gaussian_draft_half_width,
):
    config = Config()
    error = gaussian_draft_half_width(0.01, 64)
    observed = float(np.float32(config.max_range - 2 * error))
    assert 0 < observed - error < observed + error < config.max_range
    assert abs(observed - config.max_range) > error
    assert math.erfc(2 * error / (config.noise_std * math.sqrt(2))) > 0


def test_gaussian_coverage_draft_rare_errors_do_not_bound_selected_precision(
    gaussian_draft_half_width,
):
    config = Config()
    error = gaussian_draft_half_width(0.01, 1)
    false_positive_probability = (
        math.erfc(error / (config.noise_std * math.sqrt(2))) / 2
    )
    selected_probability = false_positive_probability
    assert 0 < false_positive_probability < 0.01
    assert false_positive_probability / selected_probability == 1


def test_gaussian_coverage_draft_pointwise_budget_fails_after_selection(
    gaussian_draft_half_width,
):
    config = Config()
    maximum_draws = 64
    pointwise_width = gaussian_draft_half_width(0.01, 1)
    pointwise_failure = math.erfc(pointwise_width / (config.noise_std * math.sqrt(2)))
    joint_failure = -math.expm1(maximum_draws * math.log1p(-pointwise_failure))
    assert joint_failure > 0.4
    assert gaussian_draft_half_width(0.01, maximum_draws) > pointwise_width


@pytest.mark.parametrize(
    "config",
    [
        Config(),
        Config(latency_ticks=0),
        Config(noise_std=0, dropout=0, latency_ticks=1),
    ],
)
def test_sensor_diagnostic_trace_preserves_observations_and_rng(config):
    from sim.diagnostics import DiagnosticRoverEnv, diagnostic_sample

    plain, traced = RoverEnv(config), DiagnosticRoverEnv(config)
    plain_observation, plain_info = plain.reset(seed=20261019)
    observation, info = traced.reset(seed=20261019)
    actions = [(0.6, 0), (0.6, 0.4), (0.2, -0.3), (0, 0)]
    for action in actions:
        assert json.dumps(
            observation, default=json_value, sort_keys=True
        ) == json.dumps(plain_observation, default=json_value, sort_keys=True)
        assert json.dumps(info, default=json_value, sort_keys=True) == json.dumps(
            plain_info, default=json_value, sort_keys=True
        )
        assert traced.rng.bit_generator.state == plain.rng.bit_generator.state
        sample = diagnostic_sample(traced, observation)
        assert "diagnostic" not in observation and sample["diagnostic"]["privileged"]
        assert not sample["diagnostic"]["training_approved"]
        assert not sample["diagnostic"]["real_input_qualified"]
        assert not sample["diagnostic"]["physical_safety_claim"]
        if traced.tick < traced.config.latency_ticks:
            assert sample["diagnostic"]["status"] == "no_delivery"
        else:
            capture = sample["diagnostic"]["delivered_capture"]
            assert capture["tick"] == observation["tof_sample_tick"]
            assert capture["tick"] <= traced.tick - traced.config.latency_ticks
            assert sample["diagnostic"]["age_consistency_error_s"] == pytest.approx(0)
        plain_observation, plain_reward, plain_done, plain_timeout, plain_info = (
            plain.step(action)
        )
        observation, reward, done, timeout, info = traced.step(action)
        assert (reward, done, timeout) == (plain_reward, plain_done, plain_timeout)
    assert list(traced.capture_trace) == [0, 2, 3, 4]
    traced.reset(seed=20261019)
    assert list(traced.capture_trace) == [0]


def test_sensor_diagnostic_trace_noiseless_residual_and_detached_capture():
    from sim.diagnostics import DiagnosticRoverEnv, diagnostic_sample

    env = DiagnosticRoverEnv(
        Config(noise_std=0, dropout=0), make_scenario("obstacle", seed=1)
    )
    env.reset(seed=1)
    for _ in range(3):
        observation, *_ = env.step((0.6, 0))
    sample = diagnostic_sample(env, observation)
    diagnostic = sample["diagnostic"]
    residuals = [
        value
        for row in diagnostic["range_residual_m"]
        for value in row
        if value is not None
    ]
    assert residuals
    assert max(map(abs, residuals)) < 1e-6
    assert (
        max(
            value
            for value in diagnostic["unregistered_surface_displacement_m"]
            if value is not None
        )
        > 0
    )
    assert (
        max(
            value
            for value in diagnostic["noiseless_registration_roundtrip_error_m"]
            if value is not None
        )
        < 1e-12
    )
    diagnostic["delivered_capture"]["pose_m_rad"][0] = 100
    diagnostic["delivered_capture"]["noiseless_ranges_m"][0][0] = 100
    assert env.capture_trace[env.sensor_tick]["pose_m_rad"][0] != 100
    assert env.capture_trace[env.sensor_tick]["noiseless_ranges_m"][0][0] != 100
    json.dumps(sample, default=json_value, allow_nan=False)


def test_sensor_diagnostic_trace_rejects_mismatched_owner_or_tick():
    from sim.diagnostics import DiagnosticRoverEnv, diagnostic_sample

    env = DiagnosticRoverEnv()
    observation, _ = env.reset(seed=1)
    with pytest.raises(TypeError):
        diagnostic_sample(RoverEnv(), observation)
    with pytest.raises(ValueError):
        diagnostic_sample(env, {**observation, "tick": 1})


def test_sensor_diagnostic_collection_is_bounded_and_censored():
    from dataclasses import asdict

    from sim.diagnostics import collect_diagnostic_episode, summarize_diagnostics

    records, summary = collect_diagnostic_episode("obstacle", seed=20261019, ticks=3)
    assert records[0]["config"] == asdict(Config())
    assert (
        records[0]["reference_independence"]
        == "shared_simulator_geometry_and_ray_model"
    )
    assert not records[0]["task_labels"] and not records[0]["physical_metrology"]
    assert summary["ticks"] == 3 and summary["observations"] == 4
    assert summary["censored"] and not summary["environment_timeout"]
    assert not summary["success"] and not summary["collision"]
    statistics = summarize_diagnostics(records)
    assert (
        statistics["observations"] == 4 and statistics["no_delivery_observations"] == 2
    )
    assert statistics["range_residual_m"]["count"] > 0
    assert statistics["age_consistency_error_s"]["observed_max_abs_s"] < 1e-12
    assert all(
        "diagnostic" not in record["observation"]
        for record in records
        if record["kind"] == "sample"
    )


@pytest.mark.parametrize(
    "settings",
    [
        {"ticks": 0},
        {"ticks": 33},
        {"ticks": True},
        {"seed": -1},
        {"seed": True},
        {"scenes": []},
        {"scenes": ["clear"] * 5},
        {"scenes": ["clear", "clear"]},
        {"scenes": ["unknown"]},
    ],
)
def test_sensor_diagnostic_study_rejects_out_of_scope_before_writing(
    tmp_path, settings
):
    from sim.diagnostics import run_diagnostic_study

    output, report = tmp_path / "episodes", tmp_path / "report.json"
    with pytest.raises(ValueError):
        run_diagnostic_study(output, report, **{"seed": 1, "ticks": 1, **settings})
    assert not output.exists() and not report.exists()


def test_sensor_diagnostic_study_fresh_outputs_hashes_and_empty_statistics(tmp_path):
    import hashlib
    from dataclasses import asdict

    from sim.diagnostics import run_diagnostic_study

    output, destination = tmp_path / "episodes", tmp_path / "report.json"
    report = run_diagnostic_study(
        output, destination, seed=1, ticks=1, scenes=["clear"]
    )
    assert json.loads(destination.read_text()) == report
    assert not report["accepted_bounds"] and not report["locked_splits"]
    assert report["task_labels"] == report["accepted_family_assignments"] == 0
    assert report["diagnostics"]["range_residual_m"]["count"] == 0
    assert report["diagnostics"]["range_residual_m"]["observed_max_abs_m"] is None
    episode = report["episodes"][0]
    data = Path(episode["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == episode["sha256"]
    assert len(data) == episode["bytes"]
    rows = [json.loads(line) for line in data.splitlines()]
    assert rows[0]["config"] == asdict(Config())
    observations = b"".join(
        (
            json.dumps(row["observation"], sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        for row in rows
        if row["kind"] == "sample"
    )
    assert hashlib.sha256(observations).hexdigest() == episode["observation_sha256"]
    with pytest.raises(FileExistsError):
        run_diagnostic_study(output, tmp_path / "other-report.json", seed=1)
    with pytest.raises(FileExistsError):
        run_diagnostic_study(tmp_path / "other-episodes", destination, seed=1)
    with pytest.raises(ValueError):
        run_diagnostic_study(
            tmp_path / "nested", tmp_path / "nested" / "report.json", seed=1
        )


@pytest.mark.parametrize("layout", ["same", "report_inside", "report_ancestor"])
def test_sensor_diagnostic_study_rejects_overlapping_outputs_before_collection(
    tmp_path, monkeypatch, layout
):
    from sim.diagnostics import run_diagnostic_study

    root = tmp_path / "study"
    output, report = {
        "same": (root, root),
        "report_inside": (root, root / "report.json"),
        "report_ancestor": (root / "episodes", root),
    }[layout]
    monkeypatch.setattr(
        "sim.diagnostics.collect_diagnostic_episode",
        lambda *args, **kwargs: pytest.fail(
            "collection started before path validation"
        ),
    )
    with pytest.raises(ValueError):
        run_diagnostic_study(output, report, seed=1)
    assert not root.exists()


def test_sensor_diagnostic_trace_all_dropout_is_not_zero_residual_evidence():
    from sim.diagnostics import DiagnosticRoverEnv, diagnostic_sample

    env = DiagnosticRoverEnv(Config(dropout=1), make_scenario("obstacle", seed=1))
    for _ in range(2):
        observation, *_ = env.step((0, 0))
    sample = diagnostic_sample(env, observation)["diagnostic"]
    assert sample["status"] == "delivered" and sample["invalid_zones"] == 64
    assert sample["valid_surface_zones"] == 0
    assert all(value is None for row in sample["range_residual_m"] for value in row)


def test_sensor_diagnostic_collection_preserves_real_termination(monkeypatch):
    from sim.diagnostics import collect_diagnostic_episode

    monkeypatch.setattr(
        "sim.diagnostics.make_scenario",
        lambda *args: Scenario(goal=(1.05, 3.0)),
    )
    _, summary = collect_diagnostic_episode("clear", seed=1, ticks=32)
    assert summary["ticks"] == 1 and summary["observations"] == 2
    assert summary["success"] and not summary["collision"]
    assert not summary["censored"] and not summary["environment_timeout"]
    assert summary["stop_reason"] == "environment_end"


def test_draft_catalogue_matches_wire_types_options_and_review_gate():
    from interface.protocol import CATALOGUE_VERSION, QUESTIONS, QuestionId

    catalogue = draft_catalogue()
    assert catalogue["catalogue_version"] == CATALOGUE_VERSION
    assert catalogue["review_status"] == "unreviewed_draft"
    assert catalogue["allowed_use"] == "simulation_smoke_and_pipeline_tests_only"
    assert catalogue["scope_approval"]["simulation_smoke"]
    assert not catalogue["scope_approval"]["live_teacher_labeling"]
    assert not catalogue["scope_approval"]["training"]
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
    [
        (-1, 0),
        (1, 0),
        (0, -1),
        (float("nan"), 0),
        (0, float("inf")),
        (True, 0),
        (10**400, 0),
        (0, 10**400),
    ],
)
def test_draft_envelope_rejects_invalid_values(speed, age):
    with pytest.raises((TypeError, ValueError)):
        stopping_envelope(speed, age, Config())


@pytest.fixture
def draft_observation():
    config = Config(noise_std=0, dropout=0, latency_ticks=0)
    observation, _ = RoverEnv(config).reset(seed=5)
    observation["tof_m"] = np.full((8, 8), 2.0)
    observation["tof_valid"] = np.ones((8, 8), dtype=bool)
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


def test_observation_validation_does_not_read_catalogue_or_source(
    draft_observation, monkeypatch
):
    from sim import labels

    def unexpected_catalogue():
        raise AssertionError("input validation must not compute proxy labels")

    monkeypatch.setattr(labels, "draft_catalogue", unexpected_catalogue)
    config, observation = draft_observation
    ego, ranges, valid, envelope = validate_observation(observation, config)
    np.testing.assert_equal(ego, observation["ego"])
    np.testing.assert_equal(ranges, observation["tof_m"])
    np.testing.assert_equal(valid, observation["tof_valid"])
    assert envelope == config.radius


def test_draft_file_cache_preserves_ownership_and_invalidates_edits(
    draft_observation, tmp_path, monkeypatch
):
    from sim import labels

    source = tmp_path / "labels.py"
    catalogue_path = tmp_path / "catalogue.json"
    catalogue = draft_catalogue()
    source.write_bytes(b"fixture labeler source\n")
    catalogue_path.write_text(json.dumps(catalogue))
    monkeypatch.setattr(labels, "__file__", str(source))
    original_read = Path.read_bytes
    reads = []

    def read_bytes(path):
        reads.append(path)
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    config, observation = draft_observation
    first = draft_labels(observation, config)
    assert draft_labels(observation, config) == first
    assert reads.count(source) == reads.count(catalogue_path) == 1
    draft_catalogue()["questions"][0]["options"][0] = "modified"
    assert draft_catalogue() == catalogue
    replacement = b"replacement fixture source\n"
    source.write_bytes(replacement)
    updated = draft_labels(observation, config)
    assert updated["labeler_sha256"] == hashlib.sha256(replacement).hexdigest()
    assert updated["labeler_sha256"] != first["labeler_sha256"]
    assert reads.count(source) == 2
    catalogue["policy_id"] += "-fixture"
    catalogue_path.write_text(json.dumps(catalogue))
    assert draft_labels(observation, config)["policy_id"] == catalogue["policy_id"]
    assert reads.count(catalogue_path) == 2


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


def test_label_coverage_preserves_zero_options_and_separates_abstentions(
    draft_observation,
):
    config, observation = draft_observation
    stale = deepcopy(observation)
    stale.update(tick=4, tof_age_s=4 * config.dt)
    warmup = deepcopy(observation)
    warmup.update(tof_sample_tick=None, tof_age_s=config.dt)
    warmup["tof_valid"][:] = False
    warmup["tof_m"][:] = 0
    labels = [draft_labels(value, config) for value in (observation, stale, warmup)]
    original = deepcopy(labels)
    coverage = answer_coverage(iter(labels))
    assert coverage["path_blocked"] == {
        "option_counts": {"false": 1, "true": 0},
        "answered": 1,
        "abstained": 2,
        "abstention_counts": {"stale_tof": 1, "no_tof_sample": 1},
        "missing_options": ["true"],
        "all_options_observed": False,
    }
    assert coverage["mode"]["answered"] == 0
    assert coverage["mode"]["abstention_counts"] == {"human_review_required": 3}
    assert coverage["speed_tier"]["missing_options"] == ["0", "1", "2"]
    assert all(row["answered"] + row["abstained"] == 3 for row in coverage.values())
    assert labels == original


def test_label_coverage_empty_input_does_not_claim_coverage():
    coverage = answer_coverage([])
    for question in draft_catalogue()["questions"]:
        row = coverage[question["name"]]
        assert row["missing_options"] == question["options"]
        assert row["answered"] == row["abstained"] == 0
        assert not row["all_options_observed"]


def test_label_coverage_study_is_bounded_reproducible_and_keeps_origins_separate(
    tmp_path,
):
    import hashlib

    output = tmp_path / "coverage"
    report = coverage_suite(output, seed=17)
    replay = coverage_suite(tmp_path / "replay", seed=17)
    assert report["cases"] == replay["cases"]
    assert report["synthetic_fixtures"] == replay["synthetic_fixtures"]
    assert len(report["cases"]) == 8 <= report["episode_limit"] == 16
    assert report["episode_observation_count"] == 8 * 33
    assert report["default_config"] == Config().__dict__
    assert report["config"] == {**Config().__dict__, "max_ticks": 32}
    assert report["config_overrides"] == {"max_ticks": 32}
    for flag in (
        "training_approved",
        "live_teacher_labeling_approved",
        "physical_safety_claim",
        "representative_task_coverage_claim",
        "policy_review_passed",
    ):
        assert not report[flag]
    for case in report["cases"]:
        path = output / case["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == case["sha256"]
        records = [json.loads(line) for line in path.read_text().splitlines()]
        assert records[0]["diagnostic_only"] and not records[0]["training_approved"]
        assert records[0]["policy_purpose"] == "coverage_probe_not_navigation_expert"
        config = Config(**report["config"])
        labels = [
            draft_labels(row["observation"], config)
            for row in records
            if "observation" in row
        ]
        assert labels == [
            row["simulation_label"] for row in records if "observation" in row
        ]
        assert answer_coverage(labels) == case["coverage"]
        assert not case["summary"]["collision"] and case["summary"]["timeout"]
    for case in report["synthetic_fixtures"]:
        assert case["origin"] == "synthetic_current_observation_only"
        assert case["label"] == draft_labels(case["observation"], config)
    assert len(report["synthetic_fixtures"]) == 12
    for name in ("path_blocked", "clear_sector", "speed_tier"):
        assert report["synthetic_coverage"][name]["all_options_observed"]
    assert report["episode_coverage"]["mode"]["answered"] == 0
    assert report["synthetic_coverage"]["mode"]["answered"] == 0
    assert report["synthetic_coverage"]["path_blocked"]["abstention_counts"] == {
        "no_tof_sample": 1,
        "stale_tof": 1,
        "incomplete_centre_coverage": 1,
    }
    assert (
        report["synthetic_coverage"]["clear_sector"]["abstention_counts"][
            "incomplete_sector_coverage"
        ]
        == 2
    )
    assert json.loads((output / "report.json").read_text()) == report
    with pytest.raises(FileExistsError):
        coverage_suite(output)


@pytest.mark.parametrize("seed", [-1, True, 2**63])
def test_label_coverage_study_rejects_invalid_seed_before_creating_output(
    tmp_path, seed
):
    output = tmp_path / "invalid-coverage"
    with pytest.raises(ValueError, match="seed"):
        coverage_suite(output, seed=seed)
    assert not output.exists()


@pytest.mark.parametrize("coverage", [False, True])
def test_label_coverage_cli_is_opt_in_and_preserves_default_smoke(
    tmp_path, monkeypatch, capsys, coverage
):
    from sim.labels import main

    called = []

    def run(output, *, seed):
        called.append((output, seed))
        return (
            {"episode_coverage": {"probe": True}}
            if coverage
            else {"all_scenes_succeeded": True}
        )

    def forbidden(*args, **kwargs):
        pytest.fail("nonselected smoke mode must not execute")

    monkeypatch.setattr("sim.labels.coverage_suite", run if coverage else forbidden)
    monkeypatch.setattr("sim.labels.smoke_suite", forbidden if coverage else run)
    output = tmp_path / "episodes"
    report_path = tmp_path / "report.json"
    arguments = [
        "labels",
        "--output",
        str(output),
        "--report",
        str(report_path),
        "--seed",
        "23",
    ]
    if coverage:
        arguments.append("--coverage-study")
    monkeypatch.setattr("sys.argv", arguments)
    main()
    assert called == [(output, 23)]
    summary = json.loads(capsys.readouterr().out)
    assert not summary["training_approved"]
    key = "episode_coverage" if coverage else "all_scenes_succeeded"
    assert summary[key] == json.loads(report_path.read_text())[key]
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2 and len(called) == 1


def test_label_coverage_study_requires_smoke_approval_before_output(
    tmp_path, monkeypatch
):
    catalogue = draft_catalogue()
    catalogue["scope_approval"]["simulation_smoke"] = False
    monkeypatch.setattr("sim.labels.draft_catalogue", lambda: catalogue)
    output = tmp_path / "not-approved"
    with pytest.raises(ValueError, match="not approved"):
        coverage_suite(output)
    assert not output.exists()


def test_label_smoke_is_repeatable_exclusive_and_never_labels_mode(tmp_path):
    import hashlib

    config = Config(max_ticks=3)
    output = tmp_path / "smoke"
    report = smoke_suite(output, seed=7, config=config)
    replay = smoke_suite(tmp_path / "replay", seed=7, config=config)
    assert report["cases"] == replay["cases"]
    assert len(report["cases"]) == 4
    assert not report["training_approved"]
    assert not report["live_teacher_labeling_approved"]
    for row in report["cases"]:
        path = output / row["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
        records = [json.loads(line) for line in path.read_text().splitlines()]
        for record in records:
            if "observation" in record:
                labels = record["simulation_label"]
                assert labels == draft_labels(record["observation"], config)
                assert labels["answers"]["mode"]["value"] is None
        assert row["answer_counts"]["mode"] == {"abstain:human_review_required": 4}
    with pytest.raises(FileExistsError):
        smoke_suite(output, config=config)


@pytest.mark.parametrize("seed", [-1, True, 2**63])
def test_label_smoke_rejects_invalid_seed_before_creating_output(tmp_path, seed):
    output = tmp_path / "invalid"
    with pytest.raises(ValueError, match="seed"):
        smoke_suite(output, seed=seed)
    assert not output.exists()


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


def test_observation_reads_do_not_advance_or_expose_history():
    env = RoverEnv()
    observation, _ = env.reset(seed=4)
    for tick in range(env.config.history_ticks + 2):
        rng_state = deepcopy(env.rng.bit_generator.state)
        repeated = env._observation()
        assert len(env.history) == min(tick + 1, env.config.history_ticks)
        assert env.rng.bit_generator.state == rng_state
        for name, value in observation.items():
            np.testing.assert_equal(repeated[name], value)
        for value in repeated.values():
            if isinstance(value, np.ndarray):
                value[:] = 0
        detached = env._observation()
        for name, value in observation.items():
            np.testing.assert_equal(detached[name], value)
        observation, *_ = env.step((0.1, 0.1))


def test_latency_dropout_and_sensor_timestamp_are_explicit():
    env = RoverEnv(Config(noise_std=0, dropout=0, latency_ticks=2))
    observation, _ = env.reset()
    assert not observation["tof_valid"].any()
    assert observation["tof_sample_tick"] is None
    observation, *_ = env.step([0, 0])
    assert not observation["tof_valid"].any()
    observation, *_ = env.step([0, 0])
    assert observation["tof_valid"].any()
    assert not observation["tof_valid"][0].any()
    assert observation["tof_sample_tick"] == 0
    assert observation["tof_age_s"] == pytest.approx(0.1)
    dropped, _ = RoverEnv(Config(dropout=1, latency_ticks=0)).reset()
    assert not dropped["tof_valid"].any()
    assert np.isfinite(dropped["tof_m"]).all()


def test_tof_rate_delivers_pending_frames_without_a_new_capture():
    env = RoverEnv(Config(noise_std=0, dropout=0))
    observation, _ = env.reset()
    delivered = [observation["tof_sample_tick"]]
    ages = [observation["tof_age_s"]]
    for _ in range(8):
        observation, *_ = env.step((0, 0))
        delivered.append(observation["tof_sample_tick"])
        ages.append(observation["tof_age_s"])
    assert delivered == [None, None, 0, 0, 2, 3, 4, 4, 6]
    assert ages[2:] == pytest.approx([0.1, 0.15, 0.1, 0.1, 0.1, 0.15, 0.1])


def test_tof_rate_holds_measurements_without_consuming_rng():
    env = RoverEnv(Config(latency_ticks=0))
    observation, _ = env.reset(seed=42)
    before = deepcopy(env.rng.bit_generator.state)
    held, *_ = env.step((0, 0))
    assert env.rng.bit_generator.state == before
    np.testing.assert_array_equal(held["tof_m"], observation["tof_m"])
    np.testing.assert_array_equal(held["tof_valid"], observation["tof_valid"])
    assert held["tof_sample_tick"] == 0
    assert held["tof_age_s"] == pytest.approx(env.config.dt)


@pytest.mark.parametrize(
    "dt,rate,captures",
    [
        (0.05, 15, [0, 2, 3, 4, 6, 7, 8]),
        (0.05, 10, [0, 2, 4, 6, 8]),
        (0.1, 10, list(range(9))),
        (0.3, 2, [0, 2, 4, 5, 7]),
        (1.0, 15, list(range(9))),
    ],
)
def test_tof_rate_phase_and_reset_are_deterministic(dt, rate, captures):
    from sim.diagnostics import DiagnosticRoverEnv

    env = DiagnosticRoverEnv(Config(dt=dt, tof_rate_hz=rate, latency_ticks=0))
    sequences = []
    for _ in range(2):
        observation, _ = env.reset(seed=42)
        sequence = [json.dumps(observation, default=json_value, sort_keys=True)]
        for _ in range(8):
            observation, *_ = env.step((0, 0))
            sequence.append(json.dumps(observation, default=json_value, sort_keys=True))
        assert list(env.capture_trace) == captures
        sequences.append(sequence)
    assert sequences[0] == sequences[1]


def test_tof_rate_legacy_config_loading_keeps_per_tick_sampling():
    from dataclasses import asdict

    record = asdict(Config())
    assert record.pop("tof_rate_hz") == 15
    legacy = Config.from_record(record)
    assert legacy.tof_rate_hz is None
    env = RoverEnv(legacy)
    env.reset(seed=42)
    for tick in range(1, 9):
        observation, *_ = env.step((0, 0))
        expected = tick - legacy.latency_ticks
        assert observation["tof_sample_tick"] == (expected if expected >= 0 else None)
    assert Config.from_record(asdict(Config())) == Config()


@pytest.mark.parametrize("rate", [0, -1, 15.1, 20, float("inf"), float("nan"), True])
def test_tof_rate_rejects_unsupported_configuration(rate):
    with pytest.raises(ValueError):
        Config(tof_rate_hz=rate)


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
        {"dt": 10**400},
        {"max_speed": -(10**400)},
        {"noise_std": 10**400},
    ],
)
def test_invalid_simulation_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)


@pytest.mark.parametrize("field", Config.__dataclass_fields__)
@pytest.mark.parametrize("value", [False, True])
def test_boolean_simulation_configuration_is_rejected(field, value):
    with pytest.raises(ValueError, match="finite"):
        Config(**{field: value})


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
