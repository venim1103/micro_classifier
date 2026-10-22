"""Privileged simulator sensor diagnostics, never task labels or physical metrology."""

import argparse
import hashlib
import json
import math
import platform
from copy import deepcopy
from dataclasses import asdict, replace
from itertools import pairwise
from pathlib import Path

import numpy as np

from sim.rover import (
    Config,
    RoverEnv,
    json_value,
    make_scenario,
    tof_directions,
    tof_ranges,
    write_episode,
)

SCENES = ("clear", "obstacle", "corridor", "slalom")
C1_SCHEMA = "micro-classifier/synthetic-c1-views/1"


def _c1_config(config):
    if config is not None and not isinstance(config, Config):
        raise ValueError("C1 config must be a Config instance")
    config = replace(
        config or Config(noise_std=0, dropout=0), tof_mount_pitch=math.pi / 8
    )
    if (
        config.field_of_view != math.pi / 4
        or config.tof_mount_height != 0.15
        or config.dt != 0.05
        or config.latency_ticks != 2
        or config.tof_rate_hz != 15
        or config.history_ticks != 8
        or any(
            (
                config.noise_std,
                config.dropout,
                config.odometry_position_error,
                config.odometry_heading_error,
                config.odometry_latency_ticks,
            )
        )
    ):
        raise ValueError("C1 requires its declared ideal geometry/timing/error profile")
    return config


def _c1_array(value, shape, kinds="iuf"):
    array = np.asarray(value)
    if array.shape != shape or array.dtype.kind not in kinds:
        raise ValueError("invalid C1 array shape or numeric type")
    if kinds != "b" and any(
        isinstance(item, (bool, np.bool_))
        for item in np.asarray(value, dtype=object).flat
    ):
        raise ValueError("C1 numeric evidence must not contain booleans")
    if not np.all(np.isfinite(array)) or np.any(np.abs(array) > np.finfo(float).max):
        raise ValueError("C1 arrays must be finite")
    return array


def capture_synthetic_c1_views(
    scenario, *, pose_m_rad, capture_tick, config=None, synthetic_test_only=False
):
    """Create an isolated ideal fixture, never a normal simulator observation."""
    if synthetic_test_only is not True:
        raise ValueError("C1 capture requires synthetic_test_only=True")
    config = _c1_config(config)
    if type(capture_tick) is not int or not 0 <= capture_tick <= 0xFFFFFFFF:
        raise ValueError("C1 capture tick must be a u32 integer")
    if capture_tick and capture_tick * 3 // 4 == (capture_tick - 1) * 3 // 4:
        raise ValueError("C1 capture tick does not follow nominal acquisition cadence")
    pose = _c1_array(pose_m_rad, (3,)).astype(float)
    scenario.validate(config)
    ranges = np.stack(
        [
            tof_ranges(pose[:2], pose[2] + index * math.pi / 4, scenario, config)
            for index in range(8)
        ]
    )
    valid = np.isfinite(ranges) & (ranges > 0) & (ranges < config.max_range)
    with np.errstate(over="ignore", invalid="ignore"):
        stored = np.where(valid, ranges, 0).astype(np.float32)
    valid &= np.isfinite(stored) & (stored > 0) & (stored < config.max_range)
    stored[~valid] = 0
    return {
        "schema": C1_SCHEMA,
        "allowed_use": "synthetic_visibility_fixtures_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "config": asdict(config),
        "capture_ticks": np.full(8, capture_tick, dtype=np.uint32),
        "capture_poses_m_rad": np.tile(pose, (8, 1)),
        "tof_m": stored,
        "tof_valid": valid,
    }


def inspect_synthetic_c1_history(
    history,
    *,
    reference_tick,
    reference_pose_m_rad,
    max_age_ticks=3,
    config=None,
    synthetic_test_only=False,
):
    """Inspect bounded declared-exact fixtures; endpoints never qualify free volume."""
    if synthetic_test_only is not True:
        raise ValueError("C1 inspection requires synthetic_test_only=True")
    config = _c1_config(config)
    if (
        type(reference_tick) is not int
        or not 0 <= reference_tick <= 0xFFFFFFFF
        or type(max_age_ticks) is not int
        or not 0 <= max_age_ticks <= 8
    ):
        raise ValueError("C1 reference/age ticks require bounded integers")
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    result = {
        "schema": "micro-classifier/synthetic-c1-inspection/1",
        "allowed_use": "synthetic_visibility_fixtures_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "status": "unknown",
        "reason": "unsupported_history",
        "points_body_m": None,
        "point_valid": None,
        "unique_capture_count": 0,
        "assumed_max_age_ticks": max_age_ticks,
    }
    if not isinstance(history, (list, tuple)) or not 1 <= len(history) <= 8:
        return result
    previous = None
    unique = set()
    try:
        for index, record in enumerate(history):
            if not isinstance(record, dict) or set(record) != {
                "schema",
                "allowed_use",
                "training_approved",
                "real_input_qualified",
                "free_space_qualified",
                "config",
                "capture_ticks",
                "capture_poses_m_rad",
                "tof_m",
                "tof_valid",
            }:
                return result
            if (
                record["schema"] != C1_SCHEMA
                or record["allowed_use"] != result["allowed_use"]
                or any(
                    record[key] is not False
                    for key in (
                        "training_approved",
                        "real_input_qualified",
                        "free_space_qualified",
                    )
                )
                or json.dumps(record["config"], sort_keys=True, allow_nan=False)
                != json.dumps(asdict(config), sort_keys=True, allow_nan=False)
            ):
                return result
            ticks = _c1_array(record["capture_ticks"], (8,), "iu")
            poses = _c1_array(record["capture_poses_m_rad"], (8, 3))
            ranges = _c1_array(record["tof_m"], (8, 8, 8), "f")
            valid = _c1_array(record["tof_valid"], (8, 8, 8), "b")
            tick = int(ticks[0])
            snapshot_tick = reference_tick - len(history) + 1 + index
            if (
                not np.all(ticks == tick)
                or tick > 0xFFFFFFFF
                or tick > snapshot_tick - config.latency_ticks
                or (tick != 0 and tick * 3 // 4 == (tick - 1) * 3 // 4)
                or not np.all(poses == poses[0])
                or ranges.dtype != np.float32
                or np.any(valid & ((ranges <= 0) | (ranges >= config.max_range)))
                or np.any(~valid & (ranges != 0))
            ):
                return result
            if previous is not None and (
                tick < previous[0]
                or (
                    tick == previous[0]
                    and not all(
                        np.array_equal(first, second)
                        for first, second in zip(
                            (poses, ranges, valid), previous[1:], strict=True
                        )
                    )
                )
            ):
                return result
            previous = tick, poses, ranges, valid
            unique.add(tick)
    except (TypeError, ValueError, OverflowError):
        return result
    result["unique_capture_count"] = len(unique)
    age = reference_tick - tick
    result["latest_age_ticks"] = age
    if age > max_age_ticks:
        result["reason"] = "stale_capture"
        return result
    directions = np.stack(
        [tof_directions(index * math.pi / 4, config) for index in range(8)]
    )
    points = ranges[..., None].astype(float) * directions
    points[..., 2] += config.tof_mount_height
    acquired_yaw = math.atan2(math.sin(poses[0, 2]), math.cos(poses[0, 2]))
    reference_yaw = math.atan2(math.sin(reference[2]), math.cos(reference[2]))
    cosine, sine = (
        math.cos(acquired_yaw - reference_yaw),
        math.sin(acquired_yaw - reference_yaw),
    )
    reference_cosine, reference_sine = math.cos(reference_yaw), math.sin(reference_yaw)
    with np.errstate(over="ignore", invalid="ignore"):
        points[..., :2] = points[..., :2] @ np.array(
            [[cosine, sine], [-sine, cosine]]
        ) + (poses[0, :2] - reference[:2]) @ np.array(
            [[reference_cosine, -reference_sine], [reference_sine, reference_cosine]]
        )
    if not np.all(np.isfinite(points)) or not np.any(valid):
        result["reason"] = "unsupported_points"
        return result
    result.update(
        status="registered_fixture",
        reason="declared_exact_static_assumptions_only",
        points_body_m=np.where(valid[..., None], points, 0),
        point_valid=valid.copy(),
    )
    return result


def _c1_low_free_segments(record, inspection, reference_pose_m_rad, config):
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    pose = record["capture_poses_m_rad"][0]
    cosine, sine = math.cos(reference[2]), math.sin(reference[2])
    origin = np.array(
        [
            *((pose[:2] - reference[:2]) @ np.array([[cosine, -sine], [sine, cosine]])),
            config.tof_mount_height,
        ]
    )
    ranges, valid = record["tof_m"], inspection["point_valid"]
    directions = np.divide(
        inspection["points_body_m"] - origin,
        ranges[..., None],
        out=np.zeros((8, 8, 8, 3)),
        where=valid[..., None],
    )
    guard = (
        256
        * np.finfo(float).eps
        * max(1.0, config.max_range, *np.abs(reference), *np.abs(pose))
    )
    downward = -directions[..., 2]
    near = (
        np.divide(
            config.tof_mount_height - 0.05,
            downward,
            out=np.full((8, 8, 8), np.inf),
            where=downward > 0,
        )
        + guard
    )
    floor = np.divide(
        config.tof_mount_height,
        downward,
        out=np.full((8, 8, 8), -np.inf),
        where=downward > 0,
    )
    lower_range = np.nextafter(ranges, np.float32(0)).astype(float)
    far = np.minimum(lower_range, floor) - guard
    selected = valid & (downward > 0) & (far > near)
    starts = origin + near[selected, None] * directions[selected]
    ends = origin + far[selected, None] * directions[selected]
    return np.stack((starts, ends), axis=1), guard


def _c1_curved_centerline(speed, turn_rate, age, config, pieces, braking_turn_rate=0.0):
    position = np.zeros(2)
    points, yaw, error, deviation = [position.copy()], 0.0, 0.0, 0.0
    roundoff = 64 * np.finfo(float).eps * max(1.0, config.max_range)
    for duration, deceleration, angular_rate in (
        (age + config.dt, 0.0, turn_rate),
        (speed / config.acceleration, config.acceleration, braking_turn_rate),
    ):
        if duration == 0:
            continue
        seconds = duration / pieces
        for _ in range(pieces):
            midpoint_speed = max(0, speed - deceleration * seconds / 2)
            midpoint_yaw = yaw + angular_rate * seconds / 2
            position = position + seconds * midpoint_speed * np.array(
                [math.cos(midpoint_yaw), math.sin(midpoint_yaw)]
            )
            error += (
                2 * deceleration * abs(angular_rate) + speed * angular_rate**2
            ) * seconds**3 / 24 + roundoff
            deviation = max(
                deviation, (deceleration + speed * abs(angular_rate)) * seconds**2 / 8
            )
            points.append(position.copy())
            speed = max(0, speed - deceleration * seconds)
            yaw += angular_rate * seconds
    return np.asarray(points), error + deviation


def probe_synthetic_c1_enclosure(
    history,
    *,
    reference_tick,
    reference_pose_m_rad,
    speed,
    turn_rate=None,
    curved_segments=0,
    braking_turn_rate=None,
    current_body_clear=False,
    controlled_envelope=False,
    max_cells=32768,
    max_depth=10,
    radius_bands=8,
    config=None,
    synthetic_test_only=False,
):
    """Exclude a declared fixture disk, straight capsule or bounded curved tube."""
    if synthetic_test_only is not True:
        raise ValueError("C1 enclosure requires synthetic_test_only=True")
    config = _c1_config(config)
    speed = float(_c1_array([speed], (1,))[0])
    if not 0 <= speed <= config.max_speed:
        raise ValueError("C1 speed is outside the simulated motion limits")
    if turn_rate is not None:
        turn_rate = float(_c1_array([turn_rate], (1,))[0])
        if abs(turn_rate) > config.max_turn_rate:
            raise ValueError("C1 turn rate is outside the simulated motion limits")
    if type(curved_segments) is not int or not 0 <= curved_segments <= 128:
        raise ValueError("C1 curved segments require an integer from zero through 128")
    curved = curved_segments > 0
    if curved and turn_rate is None:
        raise ValueError("C1 curved enclosure requires a declared turn rate")
    if braking_turn_rate is not None:
        braking_turn_rate = float(_c1_array([braking_turn_rate], (1,))[0])
        if abs(braking_turn_rate) > config.max_turn_rate:
            raise ValueError(
                "C1 braking turn rate is outside the simulated motion limits"
            )
        if not curved:
            raise ValueError("C1 braking turn declaration requires the curved opt-in")
    if curved and braking_turn_rate is None:
        braking_turn_rate = 0.0
    for value, lower, upper in (
        (max_cells, 0, 65536),
        (max_depth, 0, 12),
        (radius_bands, 1, 16),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError("C1 enclosure work limits require bounded integers")
    result = {
        "schema": "micro-classifier/synthetic-c1-enclosure/1",
        "allowed_use": "controlled_synthetic_qualification_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "status": "unknown",
        "reason": "current_body_clear_not_established",
        "fixture_enclosure_excluded": False,
        "cells_checked": 0,
        "radius_interval_m": [0.05, 0.30],
        "height_interval_m": [0.05, 1.0],
        "assumed_current_body_clear": current_body_clear is True,
        "assumed_controlled_envelope": controlled_envelope is True,
        "assumptions": {
            "static_floor_supported_cylinders": True,
            "axis_aligned_arena_walls_height_m": 1.0,
            "declared_exact_pose_and_first_return_model": True,
            "envelope_membership_independently_established": controlled_envelope
            is True,
            "declared_speed_and_reference_braking_model": True,
        },
    }
    if curved:
        result.update(
            schema="micro-classifier/synthetic-c1-curved-enclosure/1",
            assumed_turn_rate_rad_s=turn_rate,
            assumed_braking_turn_rate_rad_s=braking_turn_rate,
            assumed_segments_per_phase=curved_segments,
        )
        result["assumptions"]["declared_reaction_and_braking_turns"] = True
    elif turn_rate is not None:
        result.update(
            schema="micro-classifier/synthetic-c1-straight-enclosure/1",
            assumed_turn_rate_rad_s=turn_rate,
        )
        result["assumptions"]["straight_reaction_and_braking"] = turn_rate == 0
    inspection = inspect_synthetic_c1_history(
        history,
        reference_tick=reference_tick,
        reference_pose_m_rad=reference_pose_m_rad,
        config=config,
        synthetic_test_only=True,
    )
    if inspection["status"] != "registered_fixture":
        result["reason"] = inspection["reason"]
        return result
    if turn_rate is not None and turn_rate != 0 and not curved:
        result["reason"] = "unsupported_straight_maneuver"
        return result
    if current_body_clear is not True:
        return result
    if controlled_envelope is not True:
        result["reason"] = "controlled_envelope_not_established"
        return result
    if (
        config.radius,
        config.acceleration,
        config.max_speed,
        config.max_turn_rate,
        config.max_range,
        config.wall_height,
    ) != (0.18, 1, 0.6, 1.5, 4, 1):
        result["reason"] = "unsupported_dynamics_or_wall_profile"
        return result
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    record = history[-1]
    pose = record["capture_poses_m_rad"][0]
    age = inspection["latest_age_ticks"] * config.dt
    yaw_delta = math.atan2(math.sin(pose[2]), math.cos(pose[2])) - math.atan2(
        math.sin(reference[2]), math.cos(reference[2])
    )
    yaw_delta = math.atan2(math.sin(yaw_delta), math.cos(yaw_delta))
    motion_guard = (
        256 * np.finfo(float).eps * max(1.0, *np.abs(reference), *np.abs(pose))
    )
    if (
        math.hypot(float(pose[0]) - reference[0], float(pose[1]) - reference[1])
        > config.max_speed * age + motion_guard
        or abs(yaw_delta) > config.max_turn_rate * age + motion_guard
    ):
        result["reason"] = "unsupported_capture_to_reference_motion"
        return result
    segments, guard = _c1_low_free_segments(record, inspection, reference, config)
    result["free_segment_count"] = len(segments)
    if not len(segments):
        result["reason"] = "no_low_height_free_segments"
        return result
    distance = speed * (age + config.dt) + speed * speed / (2 * config.acceleration)
    body_bound = config.radius + distance + guard
    straight = turn_rate is not None and not curved
    if curved:
        curve_points, curve_error = _c1_curved_centerline(
            speed, turn_rate, age, config, curved_segments, braking_turn_rate
        )
        tube_radius = config.radius + curve_error + guard
        body_bound += curve_error
        curve_starts, curve_steps = curve_points[:-1], np.diff(curve_points, axis=0)
        curve_squared = np.sum(curve_steps * curve_steps, axis=1)
        result.update(
            curved_centerline_body_m=curve_points.tolist(),
            centerline_error_allowance_m=curve_error,
            curved_tube_radius_m=tube_radius,
        )
    elif straight:
        result.update(
            straight_centerline_length_m=distance,
            capsule_radius_m=config.radius + guard,
        )
    else:
        result["sweep_enclosure_radius_m"] = body_bound
    cosine, sine = math.cos(reference[2]), math.sin(reference[2])
    world_relative = segments[..., :2].reshape(-1, 2) @ np.array(
        [[cosine, sine], [-sine, cosine]]
    )
    wall_tip = distance * np.array([cosine, sine]) if straight else np.zeros(2)
    wall_radius = config.radius + guard if straight else body_bound
    wall_min = np.minimum(0, wall_tip) - wall_radius - guard
    wall_max = np.maximum(0, wall_tip) + wall_radius + guard
    if curved:
        world_curve = curve_points @ np.array([[cosine, sine], [-sine, cosine]])
        wall_min = world_curve.min(axis=0) - tube_radius - guard
        wall_max = world_curve.max(axis=0) + tube_radius + guard
    if not (
        np.all(world_relative.min(axis=0) < wall_min)
        and np.all(world_relative.max(axis=0) > wall_max)
    ):
        result["reason"] = "axis_aligned_wall_support_incomplete"
        return result
    starts = segments[:, 0, :2]
    steps = segments[:, 1, :2] - starts
    squared = np.sum(steps * steps, axis=1)
    radii = np.linspace(0.05, 0.30, radius_bands + 1)
    for lower, upper in pairwise(radii):
        extent = body_bound + upper + guard
        pending = [(0.0, 0.0, extent, 0)]
        while pending:
            if result["cells_checked"] >= max_cells:
                result["reason"] = "cell_budget_exhausted"
                return result
            center_x, center_y, half, depth = pending.pop()
            result["cells_checked"] += 1
            center = np.array([center_x, center_y])
            norm, cell_radius = math.hypot(center_x, center_y), math.sqrt(2) * half
            if norm - cell_radius > extent + guard:
                continue
            if curved:
                curve_relative = center - curve_starts
                curve_fractions = np.divide(
                    np.sum(curve_relative * curve_steps, axis=1),
                    curve_squared,
                    out=np.zeros_like(curve_squared),
                    where=curve_squared > 0,
                )
                curve_residual = (
                    curve_relative
                    - np.clip(curve_fractions, 0, 1)[:, None] * curve_steps
                )
                curve_separation = float(np.linalg.norm(curve_residual, axis=1).min())
                if curve_separation - cell_radius > tube_radius + upper + guard:
                    continue
            if (
                straight
                and math.hypot(center_x - min(max(center_x, 0), distance), center_y)
                - cell_radius
                > config.radius + upper + 2 * guard
            ):
                continue
            if norm + cell_radius < config.radius + lower - guard:
                continue
            relative = center - starts
            fractions = np.divide(
                np.sum(relative * steps, axis=1),
                squared,
                out=np.zeros_like(squared),
                where=squared > 0,
            )
            residual = relative - np.clip(fractions, 0, 1)[:, None] * steps
            separation = float(np.linalg.norm(residual, axis=1).min())
            if separation + cell_radius < lower - guard:
                continue
            if depth >= max_depth:
                result.update(
                    reason="unexcluded_center_cell",
                    unresolved_cell={
                        "center_m": center.tolist(),
                        "half_width_m": half,
                        "radius_interval_m": [float(lower), float(upper)],
                    },
                )
                return result
            child = half / 2
            pending.extend(
                (
                    center_x + horizontal * child,
                    center_y + vertical * child,
                    child,
                    depth + 1,
                )
                for horizontal in (-1, 1)
                for vertical in (-1, 1)
            )
    result.update(
        status="excluded_under_fixture_assumptions",
        reason="all_allowed_cylinder_centers_and_axis_aligned_walls_excluded_from_curved_tube"
        if curved
        else "all_allowed_cylinder_centers_and_axis_aligned_walls_excluded_from_straight_capsule"
        if straight
        else "all_allowed_cylinder_centers_and_axis_aligned_walls_excluded",
        fixture_enclosure_excluded=True,
    )
    return result


def probe_synthetic_c1_occupied_witness(
    history,
    *,
    reference_tick,
    reference_pose_m_rad,
    speed,
    turn_rate,
    braking_turn_rate=0.0,
    curved_segments=16,
    controlled_envelope=False,
    config=None,
    synthetic_test_only=False,
):
    """Probe occupied returns inside a declared maneuver, never its outer tube."""
    if synthetic_test_only is not True:
        raise ValueError("C1 witness requires synthetic_test_only=True")
    config = _c1_config(config)
    speed, turn_rate, braking_turn_rate = map(
        float, _c1_array([speed, turn_rate, braking_turn_rate], (3,))
    )
    if not (
        0 <= speed <= config.max_speed
        and abs(turn_rate) <= config.max_turn_rate
        and abs(braking_turn_rate) <= config.max_turn_rate
    ):
        raise ValueError("C1 witness motion exceeds the simulated limits")
    if type(curved_segments) is not int or not 1 <= curved_segments <= 128:
        raise ValueError("C1 witness requires one through 128 segments per phase")
    result = {
        "schema": "micro-classifier/synthetic-c1-occupied-witness/1",
        "allowed_use": "controlled_synthetic_qualification_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "status": "unknown",
        "reason": "controlled_envelope_not_established",
        "fixture_blocked_witness": False,
        "fixture_current_body_witness": False,
        "witness_indices": [],
        "assumed_controlled_envelope": controlled_envelope is True,
        "assumed_turn_rate_rad_s": turn_rate,
        "assumed_braking_turn_rate_rad_s": braking_turn_rate,
        "assumed_segments_per_phase": curved_segments,
        "assumptions": {
            "declared_exact_pose_and_first_return_model": True,
            "static_floor_supported_cylinders_and_axis_aligned_walls": True,
            "range_rounding_and_transform_allowances_only": True,
            "declared_reaction_and_braking_turns": True,
        },
    }
    inspection = inspect_synthetic_c1_history(
        history,
        reference_tick=reference_tick,
        reference_pose_m_rad=reference_pose_m_rad,
        config=config,
        synthetic_test_only=True,
    )
    if inspection["status"] != "registered_fixture":
        result["reason"] = inspection["reason"]
        return result
    if controlled_envelope is not True:
        return result
    if (
        config.radius,
        config.acceleration,
        config.max_speed,
        config.max_turn_rate,
        config.max_range,
        config.wall_height,
    ) != (0.18, 1, 0.6, 1.5, 4, 1):
        result["reason"] = "unsupported_dynamics_or_wall_profile"
        return result
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    record = history[-1]
    pose = record["capture_poses_m_rad"][0]
    age = inspection["latest_age_ticks"] * config.dt
    guard = (
        256
        * np.finfo(float).eps
        * max(1.0, config.max_range, *np.abs(reference), *np.abs(pose))
    )
    yaw_delta = math.atan2(math.sin(pose[2]), math.cos(pose[2])) - math.atan2(
        math.sin(reference[2]), math.cos(reference[2])
    )
    yaw_delta = math.atan2(math.sin(yaw_delta), math.cos(yaw_delta))
    if (
        math.hypot(float(pose[0]) - reference[0], float(pose[1]) - reference[1])
        > config.max_speed * age + guard
        or abs(yaw_delta) > config.max_turn_rate * age + guard
    ):
        result["reason"] = "unsupported_capture_to_reference_motion"
        return result
    if guard >= config.radius:
        result["reason"] = "unsupported_numerical_scale"
        return result
    ranges = record["tof_m"]
    lower = np.nextafter(ranges, np.float32(0)).astype(float)
    upper = np.nextafter(ranges, np.float32(np.inf)).astype(float)
    errors = np.maximum(ranges.astype(float) - lower, upper - ranges) + guard
    points = inspection["points_body_m"]
    occupied = (
        inspection["point_valid"]
        & (points[..., 2] - errors > guard)
        & (points[..., 2] + errors < config.wall_height - guard)
    )
    result["occupied_return_count"] = int(np.count_nonzero(occupied))
    if not np.any(occupied):
        result["reason"] = "no_qualified_occupied_returns"
        return result
    centerline, curve_error = _c1_curved_centerline(
        speed, turn_rate, age, config, curved_segments, braking_turn_rate
    )
    differences = points[occupied][:, None, :2] - centerline[None, :, :]
    distances = np.hypot(differences[..., 0], differences[..., 1])
    support_at_vertices = (
        distances + errors[occupied, None] + curve_error + guard < config.radius
    )
    supported = np.any(support_at_vertices, axis=1)
    result.update(
        reason="no_strict_inner_footprint_witness",
        centerline_error_allowance_m=curve_error,
        occupied_point_error_upper_m=float(errors[occupied].max()),
        fixture_current_body_witness=bool(np.any(support_at_vertices[:, 0])),
        witness_indices=np.argwhere(occupied)[supported].tolist(),
    )
    if np.any(supported):
        result.update(
            status="blocked_under_fixture_assumptions",
            reason="occupied_return_enclosure_inside_maneuver_body",
            fixture_blocked_witness=True,
        )
    return result


def probe_synthetic_c1_questions(
    history,
    *,
    reference_tick,
    reference_pose_m_rad,
    speed,
    turn_rate,
    fixture_goal_m,
    current_body_clear=False,
    controlled_envelope=False,
    curved_segments=16,
    max_cells=32768,
    max_depth=10,
    radius_bands=8,
    config=None,
    synthetic_test_only=False,
):
    """Combine conditional C1 evidence into fixture-only candidate values."""
    if synthetic_test_only is not True:
        raise ValueError("C1 question feasibility requires synthetic_test_only=True")
    config = _c1_config(config)
    speed, turn_rate = map(float, _c1_array([speed, turn_rate], (2,)))
    goal = _c1_array(fixture_goal_m, (2,)).astype(float)
    reference = _c1_array(reference_pose_m_rad, (3,)).astype(float)
    if not 0 <= speed <= config.max_speed or abs(turn_rate) > config.max_turn_rate:
        raise ValueError("C1 question motion exceeds the simulated limits")
    for value, lower, upper in (
        (curved_segments, 1, 128),
        (max_cells, 0, 65536),
        (max_depth, 0, 12),
        (radius_bands, 1, 16),
    ):
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError("C1 question work controls require bounded integers")
    result = {
        "schema": "micro-classifier/synthetic-c1-question-feasibility/1",
        "allowed_use": "controlled_synthetic_qualification_only",
        "training_approved": False,
        "real_input_qualified": False,
        "free_space_qualified": False,
        "numerically_certified": False,
        "status": "unknown",
        "reason": "current_body_clear_not_established",
        "candidate_values": {
            "path_blocked": None,
            "clear_sector": None,
            "speed_tier": None,
        },
        "fixture_goal_m": goal.tolist(),
        "queries": {},
        "unique_motion_queries": 0,
    }
    inspection = inspect_synthetic_c1_history(
        history,
        reference_tick=reference_tick,
        reference_pose_m_rad=reference,
        config=config,
        synthetic_test_only=True,
    )
    if inspection["status"] != "registered_fixture":
        result["reason"] = inspection["reason"]
        return result
    if current_body_clear is not True:
        return result
    if controlled_envelope is not True:
        result["reason"] = "controlled_envelope_not_established"
        return result
    cache = {}
    motions = [
        ("centre", speed, 0.0),
        ("left", speed, config.max_turn_rate),
        ("right", speed, -config.max_turn_rate),
        *[
            (f"tier_{tier}", max(speed, config.max_speed * tier / 3), 0.0)
            for tier in (1, 2, 3)
        ],
    ]
    for name, query_speed, braking_turn in motions:
        key = query_speed, braking_turn
        if key not in cache:
            settings = {
                "reference_tick": reference_tick,
                "reference_pose_m_rad": reference,
                "speed": query_speed,
                "turn_rate": turn_rate,
                "braking_turn_rate": braking_turn,
                "curved_segments": curved_segments,
                "controlled_envelope": True,
                "config": config,
                "synthetic_test_only": True,
            }
            exclusion = probe_synthetic_c1_enclosure(
                history,
                current_body_clear=True,
                max_cells=max_cells,
                max_depth=max_depth,
                radius_bands=radius_bands,
                **settings,
            )
            witness = probe_synthetic_c1_occupied_witness(history, **settings)
            clear = exclusion["fixture_enclosure_excluded"] is True
            blocked = witness["fixture_blocked_witness"] is True
            contradictory = (clear and blocked) or witness[
                "fixture_current_body_witness"
            ]
            cache[key] = {
                "status": "contradiction"
                if contradictory
                else "clear"
                if clear
                else "blocked"
                if blocked
                else "unknown",
                "speed_m_s": query_speed,
                "braking_turn_rate_rad_s": braking_turn,
                "exclusion": exclusion,
                "witness": witness,
            }
        result["queries"][name] = deepcopy(cache[key])
    result["unique_motion_queries"] = len(cache)
    states = {name: row["status"] for name, row in result["queries"].items()}
    if "contradiction" in states.values():
        result.update(
            status="inconsistent_fixture_evidence",
            reason="contradictory_fixture_evidence",
        )
        return result
    candidates = result["candidate_values"]
    candidates["path_blocked"] = {"clear": "false", "blocked": "true"}.get(
        states["centre"]
    )
    sector_names = ("centre", "left", "right")
    if speed > 0 and all(states[name] != "unknown" for name in sector_names):
        clear_names = [name for name in sector_names if states[name] == "clear"]
        if not clear_names:
            candidates["clear_sector"] = "none"
        else:
            yaw = math.atan2(math.sin(reference[2]), math.cos(reference[2]))
            cosine, sine = math.cos(yaw), math.sin(yaw)
            with np.errstate(over="ignore", invalid="ignore"):
                relative_goal = (goal - reference[:2]) @ np.array(
                    [[cosine, -sine], [sine, cosine]]
                )
            if np.all(np.isfinite(relative_goal)):
                distances, errors = {}, {}
                guard = (
                    256
                    * np.finfo(float).eps
                    * max(1.0, *np.abs(goal), *np.abs(reference))
                )
                for name in clear_names:
                    row = result["queries"][name]
                    points, allowance = _c1_curved_centerline(
                        speed,
                        turn_rate,
                        inspection["latest_age_ticks"] * config.dt,
                        config,
                        curved_segments,
                        row["braking_turn_rate_rad_s"],
                    )
                    distances[name] = math.dist(points[-1], relative_goal)
                    errors[name] = allowance + guard
                if all(math.isfinite(value) for value in distances.values()):
                    best = min(clear_names, key=distances.__getitem__)
                    upper = distances[best] + errors[best]
                    contenders = [
                        name
                        for name in clear_names
                        if distances[name] - errors[name] <= upper
                    ]
                    if len(contenders) == 1:
                        candidates["clear_sector"] = best
                    elif (
                        set(contenders) == {"left", "right"}
                        and turn_rate == 0
                        and relative_goal[1] == 0
                    ):
                        candidates["clear_sector"] = "left"
    tier_names = ("tier_1", "tier_2", "tier_3")
    if all(states[name] != "unknown" for name in tier_names):
        candidates["speed_tier"] = str(
            max(
                (tier for tier in (1, 2, 3) if states[f"tier_{tier}"] == "clear"),
                default=0,
            )
        )
    count = sum(value is not None for value in candidates.values())
    result.update(
        status="resolved_under_fixture_assumptions"
        if count == 3
        else "partial_fixture_evidence"
        if count
        else "unknown",
        reason="conditional_candidate_values_only"
        if count
        else "unresolved_fixture_evidence",
    )
    return result


class DiagnosticRoverEnv(RoverEnv):
    """Keep acquisition references outside the unchanged student observations."""

    def reset(self, *, seed=0):
        self.capture_trace = {}
        return super().reset(seed=seed)

    def _sample(self):
        ranges = np.minimum(
            tof_ranges(self.position, self.yaw, self.scenario, self.config),
            self.config.max_range,
        )
        capture = {
            "tick": self.tick,
            "time_s": self.tick * self.config.dt,
            "pose_m_rad": [*self.position.tolist(), float(self.yaw)],
            "noiseless_ranges_m": (
                ranges[0] if self.config.tof_mount_height is None else ranges
            ).tolist(),
            "ray_geometry": "legacy_planar"
            if self.config.tof_mount_height is None
            else "synthetic_floor_cylinders_8x8",
        }
        super()._sample()
        self.capture_trace[self.tick] = capture


def diagnostic_sample(env, observation):
    """Compare delivered ranges with shared-model truth, not independent evidence."""
    if not isinstance(env, DiagnosticRoverEnv):
        raise TypeError("diagnostic sample requires a traced simulator")
    if (
        observation["tick"] != env.tick
        or observation["tof_sample_tick"] != env.sensor_tick
    ):
        raise ValueError("diagnostic observation does not match simulator tick")
    reference_pose = [*env.position.tolist(), float(env.yaw)]
    capture = env.capture_trace.get(env.sensor_tick)
    diagnostic = {
        "privileged": True,
        "allowed_use": "quarantined_simulator_diagnostics_only",
        "training_approved": False,
        "real_input_qualified": False,
        "physical_safety_claim": False,
        "status": "no_delivery" if capture is None else "delivered",
        "reference_time_s": env.tick * env.config.dt,
        "reference_pose_m_rad": reference_pose,
        "delivered_capture": None if capture is None else deepcopy(capture),
        "valid_surface_zones": 0,
        "invalid_zones": int((~observation["tof_valid"]).sum()),
        "valid_clipped_zones": 0,
        "valid_reference_censored_zones": 0,
        "range_residual_m": None,
        "age_consistency_error_s": None,
        "unregistered_surface_displacement_m": None,
        "noiseless_registration_roundtrip_error_m": None,
    }
    if capture is not None:
        ranges = np.broadcast_to(np.asarray(capture["noiseless_ranges_m"]), (8, 8))
        observed, valid = observation["tof_m"], observation["tof_valid"]
        surface = (ranges > 0) & (ranges < env.config.max_range)
        unclipped = (observed > 0) & (observed < env.config.max_range)
        selected = valid & unclipped & surface
        diagnostic["valid_surface_zones"] = int(selected.sum())
        diagnostic["valid_clipped_zones"] = int((valid & ~unclipped).sum())
        diagnostic["valid_reference_censored_zones"] = int((valid & ~surface).sum())
        diagnostic["range_residual_m"] = [
            [
                float(observed[row, column] - ranges[row, column])
                if selected[row, column]
                else None
                for column in range(8)
            ]
            for row in range(8)
        ]
        sensor_points = (ranges[..., None] * tof_directions(0, env.config)).reshape(
            -1, 3
        )
        surface = surface.ravel()
        if env.config.tof_mount_height is None:
            sensor_points, surface = sensor_points[:8], surface[:8]
        acquisition_pose = capture["pose_m_rad"]
        cosine, sine = math.cos(acquisition_pose[2]), math.sin(acquisition_pose[2])
        world = (
            sensor_points[:, :2] @ np.array([[cosine, sine], [-sine, cosine]])
            + acquisition_pose[:2]
        )
        cosine, sine = math.cos(reference_pose[2]), math.sin(reference_pose[2])
        rotation = np.array([[cosine, -sine], [sine, cosine]])
        registered = (world - reference_pose[:2]) @ rotation
        restored = registered @ rotation.T + reference_pose[:2]
        diagnostic["unregistered_surface_displacement_m"] = [
            float(np.linalg.norm(sensor_points[column, :2] - registered[column]))
            if surface[column]
            else None
            for column in range(len(surface))
        ]
        diagnostic["noiseless_registration_roundtrip_error_m"] = [
            float(np.linalg.norm(restored[column] - world[column]))
            if surface[column]
            else None
            for column in range(len(surface))
        ]
        diagnostic["age_consistency_error_s"] = float(
            observation["tof_age_s"] - (observation["time_s"] - capture["time_s"])
        )
    return {"kind": "sample", "observation": observation, "diagnostic": diagnostic}


def collect_diagnostic_episode(scene, *, seed, ticks=32):
    """Collect a bounded diagnostic prefix without changing Config's horizon."""
    if scene not in SCENES:
        raise ValueError("diagnostic scene must be a known simulator scene")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("diagnostic seed must be a nonnegative integer")
    if isinstance(ticks, bool) or not isinstance(ticks, int) or not 1 <= ticks <= 32:
        raise ValueError("diagnostic collection requires 1 to 32 ticks")
    env = DiagnosticRoverEnv(Config(), make_scenario(scene, seed))
    observation, info = env.reset(seed=seed)
    records = [
        {
            "kind": "metadata",
            "schema": "micro-classifier/sensor-diagnostic-episode/1",
            "seed": seed,
            "scene": scene,
            "config": asdict(env.config),
            "scenario": asdict(env.scenario),
            "tick_limit": ticks,
            "policy": "diagnostic_turn_schedule/1",
            "policy_description": "Max-speed command; +max_turn_rate/3 before tick 16, negative thereafter.",
            "allowed_use": "quarantined_simulator_diagnostics_only",
            "training_approved": False,
            "reviewed": False,
            "family_group": None,
            "partition": None,
            "reference_independence": "shared_simulator_geometry_and_ray_model",
            "physical_metrology": False,
            "task_labels": False,
        },
        diagnostic_sample(env, observation),
    ]
    terminated = truncated = False
    for _ in range(ticks):
        action = [
            env.config.max_speed,
            env.config.max_turn_rate / 3 * (1 if env.tick < 16 else -1),
        ]
        observation, _, terminated, truncated, info = env.step(action)
        records.append(diagnostic_sample(env, observation))
        if terminated or truncated:
            break
    summary = {
        "kind": "summary",
        "ticks": env.tick,
        "observations": env.tick + 1,
        "collision": bool(info["collision"]),
        "success": bool(info["success"]),
        "environment_timeout": bool(truncated),
        "censored": not (terminated or truncated),
        "stop_reason": "environment_end"
        if terminated or truncated
        else "diagnostic_horizon",
    }
    records.append(summary)
    return records, summary


def _statistics(values):
    values = np.asarray(values, dtype=float)
    return {
        "count": int(values.size),
        "mean_m": float(values.mean()) if values.size else None,
        "rms_m": float(np.sqrt(np.mean(values * values))) if values.size else None,
        "observed_max_abs_m": float(np.max(np.abs(values))) if values.size else None,
    }


def summarize_diagnostics(records):
    """Summarize conditional observed values, never fit or accept error bounds."""
    samples = [record["diagnostic"] for record in records if record["kind"] == "sample"]
    residuals, ages, displacement, roundtrip = [], [], [], []
    for sample in samples:
        if sample["range_residual_m"] is not None:
            residuals.extend(
                value
                for row in sample["range_residual_m"]
                for value in row
                if value is not None
            )
        if sample["age_consistency_error_s"] is not None:
            ages.append(sample["age_consistency_error_s"])
        for name, destination in (
            ("unregistered_surface_displacement_m", displacement),
            ("noiseless_registration_roundtrip_error_m", roundtrip),
        ):
            if sample[name] is not None:
                destination.extend(value for value in sample[name] if value is not None)
    return {
        "observations": len(samples),
        "no_delivery_observations": sum(
            sample["status"] == "no_delivery" for sample in samples
        ),
        "invalid_zones": sum(sample["invalid_zones"] for sample in samples),
        "valid_clipped_zones": sum(sample["valid_clipped_zones"] for sample in samples),
        "valid_reference_censored_zones": sum(
            sample["valid_reference_censored_zones"] for sample in samples
        ),
        "exclusion_counters_overlap": True,
        "range_residual_m": _statistics(residuals),
        "age_consistency_error_s": {
            "count": len(ages),
            "observed_max_abs_s": max(map(abs, ages), default=None),
        },
        "unregistered_surface_displacement_m": _statistics(displacement),
        "noiseless_registration_roundtrip_error_m": _statistics(roundtrip),
    }


def _observation_digest(records):
    digest = hashlib.sha256()
    for record in records:
        if record["kind"] == "sample":
            digest.update(
                (
                    json.dumps(
                        record["observation"],
                        default=json_value,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    )
                    + "\n"
                ).encode()
            )
    return digest.hexdigest()


def run_diagnostic_study(output_dir, report_path, *, seed, ticks=32, scenes=SCENES):
    """Write at most four fresh diagnostic prefixes and a non-label report."""
    scenes = tuple(scenes)
    if (
        not 1 <= len(scenes) <= 4
        or len(set(scenes)) != len(scenes)
        or any(scene not in SCENES for scene in scenes)
    ):
        raise ValueError("study requires 1 to 4 distinct known scenes")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("diagnostic seed must be a nonnegative integer")
    if isinstance(ticks, bool) or not isinstance(ticks, int) or not 1 <= ticks <= 32:
        raise ValueError("diagnostic collection requires 1 to 32 ticks")
    output_dir, report_path = Path(output_dir), Path(report_path)
    if (
        output_dir.exists()
        or output_dir.is_symlink()
        or report_path.exists()
        or report_path.is_symlink()
    ):
        raise FileExistsError("diagnostic outputs must be fresh")
    resolved_output, resolved_report = output_dir.resolve(), report_path.resolve()
    if resolved_report.is_relative_to(
        resolved_output
    ) or resolved_output.is_relative_to(resolved_report):
        raise ValueError("report and diagnostic episode directory must not overlap")
    output_dir.mkdir(parents=True, exist_ok=False)
    episodes, all_records = [], []
    for index, scene in enumerate(scenes):
        records, summary = collect_diagnostic_episode(
            scene, seed=seed + index, ticks=ticks
        )
        path = output_dir / f"{scene}.jsonl"
        write_episode(path, records)
        episodes.append(
            {
                "path": path.as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
                "observation_sha256": _observation_digest(records),
                "scene": scene,
                "seed": seed + index,
                "summary": summary,
                "diagnostics": summarize_diagnostics(records),
            }
        )
        all_records.extend(records)
    report = {
        "schema": "micro-classifier/sensor-diagnostic-study/1",
        "allowed_use": "quarantined_simulator_diagnostics_only",
        "training_approved": False,
        "real_input_qualified": False,
        "physical_safety_claim": False,
        "physical_metrology": False,
        "reviewed": False,
        "accepted_bounds": False,
        "task_labels": 0,
        "accepted_family_assignments": 0,
        "locked_splits": False,
        "reference_independence": "shared_simulator_geometry_and_ray_model",
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "source_sha256": {
            "sim/diagnostics.py": hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest(),
            "sim/rover.py": hashlib.sha256(
                Path(__file__).with_name("rover.py").read_bytes()
            ).hexdigest(),
        },
        "episodes": episodes,
        "diagnostics": summarize_diagnostics(all_records),
        "limitations": [
            "Software-model diagnostics, not independent physical metrology or task truth.",
            "Residuals exclude missing, clipped and reference-censored zones; this selection biases noise statistics.",
            "Repeated vertical zones and temporally related captures are not independent trials.",
            "Round-trip consistency shares transforms/reference geometry; it is not measured registration accuracy.",
            "Observed maxima are not hard error bounds or probabilistic coverage claims.",
            "Horizon stops are censored; no navigation-success or physical safety qualification.",
            "No witness application, labels, accepted cohort/splits, teacher or student training.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--ticks", type=int, default=32)
    args = parser.parse_args(argv)
    report = run_diagnostic_study(
        args.output_dir, args.report, seed=args.seed, ticks=args.ticks
    )
    print(
        json.dumps(
            {
                "episodes": len(report["episodes"]),
                "observations": report["diagnostics"]["observations"],
            }
        )
    )


if __name__ == "__main__":
    main()
