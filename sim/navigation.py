"""Ideal-geometry reference for synthetic tests, never an observation labeler."""

import math
from numbers import Real

import numpy as np

from sim.rover import Config, Scenario, swept_collision

NUMERICAL_TOLERANCE_M = 1e-5


def _touches(start, end, radius, obstacles, bounds):
    start, end = np.asarray(start), np.asarray(end)
    return bool(
        np.any(np.minimum(start, end) <= radius)
        or np.any(np.maximum(start, end) >= np.asarray(bounds) - radius)
        or swept_collision(start, end, radius, obstacles, bounds)
    )


def _sweep(scenario, config, speed, current_turn, turn, age, max_segments):
    position = np.array(scenario.start[:2], dtype=float)
    yaw = math.atan2(math.sin(scenario.start[2]), math.cos(scenario.start[2]))
    reaction = age + config.dt
    braking = speed / config.acceleration
    distance = speed * reaction + 0.5 * speed * braking
    if not math.isfinite(reaction + braking) or not math.isfinite(distance):
        return {
            "status": "unknown",
            "endpoint_m": None,
            "endpoint_error_bound_m": None,
            "segments": 0,
        }
    if current_turn == turn == 0 or speed == 0:
        end = position + distance * np.array([math.cos(yaw), math.sin(yaw)])
        blocked = _touches(
            position, end, config.radius, scenario.obstacles, scenario.bounds
        )
        return {
            "status": "blocked" if blocked else "clear",
            "endpoint_m": end.tolist(),
            "endpoint_error_bound_m": 64
            * np.finfo(float).eps
            * max(1.0, *map(abs, scenario.bounds)),
            "segments": 1,
        }
    if _touches(position, position, config.radius, scenario.obstacles, scenario.bounds):
        return {
            "status": "blocked",
            "endpoint_m": None,
            "endpoint_error_bound_m": None,
            "segments": 0,
        }
    phases = ((reaction, current_turn, 0.0), (braking, turn, config.acceleration))
    plans = []
    total_segments = 0
    for duration, angular_rate, deceleration in phases:
        acceleration_bound = deceleration + speed * abs(angular_rate)
        if not math.isfinite(acceleration_bound):
            return {
                "status": "unknown",
                "endpoint_m": None,
                "endpoint_error_bound_m": None,
                "segments": 0,
            }
        step = (
            min(0.02, math.sqrt(8 * NUMERICAL_TOLERANCE_M / acceleration_bound))
            if acceleration_bound
            else 0.02
        )
        if step == 0 or duration > (max_segments - total_segments) * step:
            return {
                "status": "unknown",
                "endpoint_m": None,
                "endpoint_error_bound_m": None,
                "segments": 0,
            }
        count = max(1, math.ceil(duration / step))
        total_segments += count
        if total_segments > max_segments:
            return {
                "status": "unknown",
                "endpoint_m": None,
                "endpoint_error_bound_m": None,
                "segments": 0,
            }
        plans.append((duration / count, count, angular_rate, deceleration))
    coordinate_scale = max(
        1.0,
        *map(abs, scenario.bounds),
        *(abs(value) for obstacle in scenario.obstacles for value in obstacle),
    )
    roundoff = 64 * np.finfo(float).eps * coordinate_scale
    error, segments, unresolved = 0.0, 0, False
    for seconds, count, angular_rate, deceleration in plans:
        for _ in range(count):
            midpoint_speed = max(0, speed - deceleration * seconds / 2)
            midpoint_yaw = yaw + angular_rate * seconds / 2
            end = position + seconds * midpoint_speed * np.array(
                [math.cos(midpoint_yaw), math.sin(midpoint_yaw)]
            )
            quadrature = (
                (
                    2 * deceleration * abs(angular_rate)
                    + speed * angular_rate * angular_rate
                )
                * seconds**3
                / 24
            )
            sagitta = (deceleration + speed * abs(angular_rate)) * seconds**2 / 8
            error += quadrature + roundoff
            margin = error + sagitta
            segments += 1
            if not math.isfinite(margin) or margin >= config.radius:
                return {
                    "status": "unknown",
                    "endpoint_m": None,
                    "endpoint_error_bound_m": None,
                    "segments": segments,
                }
            if _touches(
                position,
                end,
                config.radius - margin,
                scenario.obstacles,
                scenario.bounds,
            ):
                return {
                    "status": "blocked",
                    "endpoint_m": None,
                    "endpoint_error_bound_m": None,
                    "segments": segments,
                }
            unresolved |= _touches(
                position,
                end,
                config.radius + margin,
                scenario.obstacles,
                scenario.bounds,
            )
            position, yaw = end, yaw + angular_rate * seconds
            speed = max(0, speed - deceleration * seconds)
    return {
        "status": "unknown" if unresolved else "clear",
        "endpoint_m": position.tolist(),
        "endpoint_error_bound_m": error,
        "segments": segments,
    }


def _rank_clear(scenario, maneuvers, current_turn):
    clear = [name for name, row in maneuvers.items() if row["status"] == "clear"]
    if not clear:
        return "none"
    distances = {
        name: math.dist(maneuvers[name]["endpoint_m"], scenario.goal) for name in clear
    }
    best = min(clear, key=distances.__getitem__)
    upper = distances[best] + maneuvers[best]["endpoint_error_bound_m"]
    contenders = [
        name
        for name in clear
        if distances[name] - maneuvers[name]["endpoint_error_bound_m"] <= upper
    ]
    if len(contenders) == 1:
        return best
    lateral_goal = np.dot(
        np.asarray(scenario.goal) - scenario.start[:2],
        [-math.sin(scenario.start[2]), math.cos(scenario.start[2])],
    )
    if set(contenders) == {"left", "right"} and current_turn == 0 and lateral_goal == 0:
        return "left"
    return None


def evaluate_synthetic(
    scenario,
    *,
    speed,
    turn_rate=0.0,
    tof_age_s=0.0,
    config=None,
    synthetic_test_only=False,
    max_segments=4096,
):
    """Evaluate complete artificial geometry, not student-visible sensor evidence."""
    if synthetic_test_only is not True:
        raise ValueError("explicit synthetic-test-only use is required")
    config = Config() if config is None else config
    if not isinstance(config, Config) or not isinstance(scenario, Scenario):
        raise TypeError(
            "synthetic reference requires Config and Scenario, not observations"
        )
    scenario.validate(config)
    for name, value in (
        ("speed", speed),
        ("turn_rate", turn_rate),
        ("tof_age_s", tof_age_s),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(value)
        ):
            raise ValueError(f"{name} must be finite numeric data")
    if (
        not 0 <= speed <= config.max_speed
        or abs(turn_rate) > config.max_turn_rate
        or tof_age_s < 0
    ):
        raise ValueError("motion/age exceeds synthetic reference limits")
    if type(max_segments) is not int or not 1 <= max_segments <= 4096:
        raise ValueError("max_segments must be an integer from 1 to 4096")
    maneuvers = {
        name: _sweep(
            scenario,
            config,
            float(speed),
            float(turn_rate),
            turn,
            float(tof_age_s),
            max_segments,
        )
        for name, turn in (
            ("centre", 0.0),
            ("left", config.max_turn_rate),
            ("right", -config.max_turn_rate),
        )
    }
    tiers = {
        str(tier): _sweep(
            scenario,
            config,
            max(float(speed), config.max_speed * tier / 3),
            float(turn_rate),
            0.0,
            float(tof_age_s),
            max_segments,
        )
        for tier in (1, 2, 3)
    }
    centre = maneuvers["centre"]["status"]
    sector = None
    if speed > 0 and all(row["status"] != "unknown" for row in maneuvers.values()):
        sector = _rank_clear(scenario, maneuvers, turn_rate)
    tier_answer = None
    if all(row["status"] != "unknown" for row in tiers.values()):
        tier_answer = max(
            (name for name, row in tiers.items() if row["status"] == "clear"),
            default="0",
            key=int,
        )
    return {
        "schema": "micro-classifier/synthetic-navigation-reference/1",
        "allowed_use": "artificial_geometry_tests_only",
        "synthetic": True,
        "training_approved": False,
        "reviewed_dataset": False,
        "physical_safety_claim": False,
        "mode_labels": 0,
        "numerical_tolerance_m": NUMERICAL_TOLERANCE_M,
        "max_segments_per_maneuver": max_segments,
        "answers": {
            "path_blocked": None
            if centre == "unknown"
            else str(centre == "blocked").lower(),
            "clear_sector": sector,
            "speed_tier": tier_answer,
            "mode": None,
        },
        "maneuvers": maneuvers,
        "tier_references": tiers,
    }
