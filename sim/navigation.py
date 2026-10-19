"""Synthetic navigation diagnostics, never an observation or episode labeler."""

import math
from numbers import Real

import numpy as np

from sim.rover import Config, Scenario, swept_collision

NUMERICAL_TOLERANCE_M = 1e-5


def _finite_float(value, name):
    try:
        number = (
            float(value)
            if not isinstance(value, bool) and isinstance(value, Real)
            else math.nan
        )
    except OverflowError as error:
        raise ValueError(f"{name} must be finite numeric data") from error
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite numeric data")
    return number


def register_synthetic_points(
    points,
    *,
    sensor_pose,
    acquisition_pose,
    reference_pose,
    acquisition_time_s,
    reference_time_s,
    synthetic_test_only=False,
):
    """Transform artificial static points with assumed exact instantaneous poses."""
    if synthetic_test_only is not True:
        raise ValueError("explicit synthetic-test-only use is required")
    result = {
        "schema": "micro-classifier/synthetic-point-registration/1",
        "allowed_use": "artificial_static_point_registration_tests_only",
        "synthetic": True,
        "training_approved": False,
        "real_input_qualified": False,
        "physical_safety_claim": False,
        "status": "unknown",
        "reason": "missing_timing",
        "reference_points_m": None,
        "acquisition_time_s": None,
        "reference_time_s": None,
        "elapsed_s": None,
        "assumptions": {
            "static_world": True,
            "exact_fixture_poses": True,
            "instantaneous_acquisition": True,
        },
    }
    for name, value in (
        ("acquisition_time_s", acquisition_time_s),
        ("reference_time_s", reference_time_s),
    ):
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, Real) or value < 0:
            raise ValueError(f"{name} must be finite nonnegative numeric data")
        result[name] = _finite_float(value, name)
    if acquisition_time_s is None or reference_time_s is None:
        return result
    if reference_time_s < acquisition_time_s:
        raise ValueError("reference time must not precede acquisition time")
    result["elapsed_s"] = float(reference_time_s) - float(acquisition_time_s)
    if sensor_pose is None or acquisition_pose is None or reference_pose is None:
        result["reason"] = "missing_pose"
        return result
    arrays = {}
    for name, value in (
        ("points", points),
        ("sensor_pose", sensor_pose),
        ("acquisition_pose", acquisition_pose),
        ("reference_pose", reference_pose),
    ):
        raw = np.asarray(value, dtype=object)
        shape_valid = (
            raw.ndim == 2 and raw.shape[0] > 0 and raw.shape[1] == 2
            if name == "points"
            else raw.shape == (3,)
        )
        if not shape_valid or any(
            isinstance(number, bool) or not isinstance(number, Real)
            for number in raw.flat
        ):
            raise ValueError(f"{name} requires finite numeric planar data")
        try:
            numeric = np.asarray(raw, dtype=float)
        except OverflowError as error:
            raise ValueError(f"{name} requires finite numeric planar data") from error
        if not np.isfinite(numeric).all():
            raise ValueError(f"{name} requires finite numeric planar data")
        arrays[name] = numeric
    rotations = {}
    for name in ("sensor_pose", "acquisition_pose", "reference_pose"):
        yaw = arrays[name][2]
        cosine, sine = math.cos(yaw), math.sin(yaw)
        rotations[name] = np.array([[cosine, -sine], [sine, cosine]])
    with np.errstate(over="ignore", invalid="ignore"):
        body_points = (
            arrays["points"] @ rotations["sensor_pose"].T + arrays["sensor_pose"][:2]
        )
        relative_rotation = (
            rotations["reference_pose"].T @ rotations["acquisition_pose"]
        )
        displacement = (
            arrays["acquisition_pose"][:2] - arrays["reference_pose"][:2]
        ) @ rotations["reference_pose"]
        registered = body_points @ relative_rotation.T + displacement
    if not np.isfinite(registered).all():
        result["reason"] = "numerical_unknown"
        return result
    result.update(
        status="registered_fixture",
        reason="assumed_static_exact_planar_poses",
        reference_points_m=registered.tolist(),
    )
    return result


def register_synthetic_bounded_points(
    points,
    *,
    point_error_m,
    pose_error_bounds,
    sensor_pose,
    acquisition_pose,
    reference_pose,
    acquisition_time_s,
    reference_time_s,
    synthetic_test_only=False,
):
    """Propagate assumed geometric errors, not measured registration uncertainty."""
    baseline = register_synthetic_points(
        points,
        sensor_pose=sensor_pose,
        acquisition_pose=acquisition_pose,
        reference_pose=reference_pose,
        acquisition_time_s=acquisition_time_s,
        reference_time_s=reference_time_s,
        synthetic_test_only=synthetic_test_only,
    )
    pose_names = ("sensor_pose", "acquisition_pose", "reference_pose")
    if not isinstance(pose_error_bounds, dict) or set(pose_error_bounds) != set(
        pose_names
    ):
        raise ValueError("pose_error_bounds requires all three artificial poses")
    raw_bounds = {"point_error_m": point_error_m}
    for name in pose_names:
        row = pose_error_bounds[name]
        if not isinstance(row, dict) or set(row) != {"translation_m", "heading_rad"}:
            raise ValueError(f"{name} requires translation_m and heading_rad bounds")
        raw_bounds.update({f"{name}_{field}": value for field, value in row.items()})
    bounds = {}
    for name, value in raw_bounds.items():
        if isinstance(value, bool) or not isinstance(value, Real) or value < 0:
            raise ValueError(f"{name} must be finite nonnegative numeric data")
        bound = _finite_float(value, name)
        if name.endswith("heading_rad") and bound > math.pi:
            raise ValueError(f"{name} is outside the artificial error domain")
        bounds[name] = bound
    result = {
        **baseline,
        "schema": "micro-classifier/synthetic-bounded-point-registration/1",
        "allowed_use": "artificial_bounded_point_registration_tests_only",
        "assumed_error_bounds": bounds,
        "point_error_bound_m": None,
        "bound_semantics": "assumed_model_exact_arithmetic",
        "floating_point_certified": False,
        "assumptions": {
            "static_world": True,
            "instantaneous_acquisition": True,
            "bounded_point_and_pose_errors": True,
        },
    }
    if baseline["status"] != "registered_fixture":
        return result
    sensor_points = np.asarray(points, dtype=float)
    mounting = np.asarray(sensor_pose, dtype=float)
    cosine, sine = math.cos(mounting[2]), math.sin(mounting[2])
    with np.errstate(over="ignore", invalid="ignore"):
        body_points = (
            sensor_points @ np.array([[cosine, sine], [-sine, cosine]]) + mounting[:2]
        )
    radii = []
    for sensor_point, body_point, reference_point in zip(
        sensor_points, body_points, baseline["reference_points_m"]
    ):
        radius = bounds["point_error_m"] + sum(
            bounds[f"{name}_translation_m"] for name in pose_names
        )
        for name, point in zip(pose_names, (sensor_point, body_point, reference_point)):
            radius += (
                2 * math.sin(bounds[f"{name}_heading_rad"] / 2) * math.hypot(*point)
            )
        if not math.isfinite(radius):
            result.update(
                status="unknown", reason="numerical_unknown", reference_points_m=None
            )
            return result
        radii.append(radius)
    result.update(
        status="bounded_fixture",
        reason="assumed_static_point_and_pose_errors",
        point_error_bound_m=radii,
    )
    return result


def probe_synthetic_registered_witness(
    points,
    *,
    speed,
    point_error_m,
    pose_error_bounds,
    sensor_pose,
    acquisition_pose,
    reference_pose,
    acquisition_time_s,
    reference_time_s,
    assume_obstacle_points=False,
    turn_rate=0.0,
    config=None,
    synthetic_test_only=False,
):
    """Probe artificial registered obstacle balls, never real sensor evidence."""
    registered = register_synthetic_bounded_points(
        points,
        point_error_m=point_error_m,
        pose_error_bounds=pose_error_bounds,
        sensor_pose=sensor_pose,
        acquisition_pose=acquisition_pose,
        reference_pose=reference_pose,
        acquisition_time_s=acquisition_time_s,
        reference_time_s=reference_time_s,
        synthetic_test_only=synthetic_test_only,
    )
    config = Config() if config is None else config
    if not isinstance(config, Config):
        raise TypeError("synthetic registered probe requires Config")
    if type(assume_obstacle_points) is not bool:
        raise TypeError("obstacle membership requires a boolean fixture assumption")
    motion = {}
    for name, value in (("speed", speed), ("turn_rate", turn_rate)):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be finite numeric data")
        motion[name] = _finite_float(value, name)
    if (
        not 0 <= motion["speed"] <= config.max_speed
        or abs(motion["turn_rate"]) > config.max_turn_rate
    ):
        raise ValueError("registered probe motion exceeds synthetic limits")
    result = {
        **registered,
        "schema": "micro-classifier/synthetic-registered-witness/1",
        "allowed_use": "artificial_registered_witness_tests_only",
        "status": "unknown",
        "witness_indices": [],
        "braking_distance_m": None,
        "numerical_allowance_m": None,
        "speed_m_s": motion["speed"],
        "turn_rate_rad_s": motion["turn_rate"],
        "assumptions": {
            **registered["assumptions"],
            "obstacle_membership": assume_obstacle_points,
            "exact_fixture_motion_and_footprint": True,
        },
    }
    if registered["status"] != "bounded_fixture":
        return result
    if not assume_obstacle_points:
        result["reason"] = "obstacle_membership_unqualified"
        return result
    if config.noise_std != 0:
        result["reason"] = "noise_model_unqualified"
        return result
    if config.latency_ticks != 0:
        result["reason"] = "registration_unqualified"
        return result
    if motion["turn_rate"] != 0:
        result["reason"] = "curved_reference_not_supported"
        return result
    distance = motion["speed"] * config.dt + motion["speed"] * motion["speed"] / (
        2 * config.acceleration
    )
    if not math.isfinite(distance):
        result["reason"] = "numerical_unknown"
        return result
    result["braking_distance_m"] = distance
    result["numerical_allowance_m"] = []
    source_points = np.asarray(points, dtype=float)
    pose_scale = max(
        abs(float(value))
        for pose in (sensor_pose, acquisition_pose, reference_pose)
        for value in np.asarray(pose, dtype=float)[:2]
    )
    unresolved = False
    for index, (point, error) in enumerate(
        zip(registered["reference_points_m"], registered["point_error_bound_m"])
    ):
        allowance = (
            128
            * np.finfo(float).eps
            * max(
                1.0,
                config.radius,
                distance,
                pose_scale,
                abs(source_points[index, 0]),
                abs(source_points[index, 1]),
                abs(point[0]),
                abs(point[1]),
                error,
            )
        )
        result["numerical_allowance_m"].append(float(allowance))
        separation = math.hypot(point[0] - min(max(point[0], 0.0), distance), point[1])
        if allowance >= config.radius or not math.isfinite(separation + error):
            unresolved = True
            continue
        if separation + error < config.radius - allowance:
            result["witness_indices"].append(index)
    result["reason"] = "numerical_unknown" if unresolved else "no_robust_witness"
    if result["witness_indices"]:
        result.update(
            status="blocked_witness",
            reason="assumed_registered_ball_inside_braking_footprint",
        )
    return result


def probe_synthetic_ray_witness(
    ranges,
    valid,
    *,
    speed,
    tof_age_s=0.0,
    turn_rate=0.0,
    config=None,
    synthetic_test_only=False,
):
    """Probe eight artificial exact rays; a positive witness never certifies free space."""
    if synthetic_test_only is not True:
        raise ValueError("explicit synthetic-test-only use is required")
    config = Config() if config is None else config
    if not isinstance(config, Config):
        raise TypeError("synthetic ray probe requires Config")
    for name, value in (
        ("speed", speed),
        ("tof_age_s", tof_age_s),
        ("turn_rate", turn_rate),
    ):
        _finite_float(value, name)
    if (
        not 0 <= speed <= config.max_speed
        or tof_age_s < 0
        or abs(turn_rate) > config.max_turn_rate
    ):
        raise ValueError("ray probe motion/age exceeds synthetic limits")
    ranges, valid = np.asarray(ranges), np.asarray(valid)
    if (
        ranges.shape != (8,)
        or ranges.dtype.kind not in "iuf"
        or not np.isfinite(ranges).all()
        or (ranges < 0).any()
        or (ranges > config.max_range).any()
    ):
        raise ValueError("synthetic ranges require eight finite values within range")
    if valid.shape != (8,) or valid.dtype.kind != "b" or (ranges[~valid] != 0).any():
        raise ValueError(
            "synthetic masks require eight booleans and zero invalid ranges"
        )
    result = {
        "schema": "micro-classifier/synthetic-ray-witness/1",
        "allowed_use": "artificial_ray_feasibility_tests_only",
        "synthetic": True,
        "training_approved": False,
        "real_input_qualified": False,
        "physical_safety_claim": False,
        "status": "unknown",
        "reason": "no_positive_witness",
        "witness_columns": [],
    }
    if config.noise_std != 0:
        result["reason"] = "noise_model_unqualified"
        return result
    if tof_age_s != 0 or config.latency_ticks != 0:
        result["reason"] = "registration_unqualified"
        return result
    if turn_rate != 0:
        result["reason"] = "curved_reference_not_supported"
        return result
    distance = float(speed) * config.dt + float(speed) * float(speed) / (
        2 * config.acceleration
    )
    allowance = (
        128 * np.finfo(float).eps * max(1.0, config.max_range, distance, config.radius)
    )
    if (
        not math.isfinite(distance)
        or not math.isfinite(allowance)
        or allowance >= config.radius
    ):
        result["reason"] = "numerical_unknown"
        return result
    angles = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)
    points = ranges[:, None] * np.stack((np.cos(angles), np.sin(angles)), axis=1)
    distances = np.hypot(
        points[:, 0] - np.clip(points[:, 0], 0, distance), points[:, 1]
    )
    witnesses = (
        valid & (ranges < config.max_range) & (distances < config.radius - allowance)
    )
    result["witness_columns"] = np.flatnonzero(witnesses).tolist()
    if result["witness_columns"]:
        result.update(
            status="blocked_witness", reason="strictly_inside_braking_footprint"
        )
    return result


def probe_synthetic_bounded_ray_witness(
    ranges,
    valid,
    *,
    speed,
    range_error_m,
    translation_error_m,
    heading_error_rad,
    tof_age_s=0.0,
    turn_rate=0.0,
    config=None,
    synthetic_test_only=False,
):
    """Probe assumed artificial error sets, not measured sensor uncertainty."""
    config = Config() if config is None else config
    baseline = probe_synthetic_ray_witness(
        ranges,
        valid,
        speed=speed,
        tof_age_s=tof_age_s,
        turn_rate=turn_rate,
        config=config,
        synthetic_test_only=synthetic_test_only,
    )
    bounds = {
        "range_error_m": range_error_m,
        "translation_error_m": translation_error_m,
        "heading_error_rad": heading_error_rad,
    }
    for name, value in bounds.items():
        bounds[name] = _finite_float(value, name)
        if value < 0:
            raise ValueError(f"{name} must be finite nonnegative numeric data")
    if heading_error_rad > math.pi:
        raise ValueError("heading_error_rad must not exceed pi")
    bounds = {name: float(value) for name, value in bounds.items()}
    result = {
        **baseline,
        "schema": "micro-classifier/synthetic-bounded-ray-witness/1",
        "allowed_use": "artificial_bounded_ray_tests_only",
        "assumed_error_bounds": bounds,
        "point_error_bound_m": [None] * 8,
    }
    if baseline["status"] != "blocked_witness":
        return result
    result.update(status="unknown", reason="no_robust_witness", witness_columns=[])
    ranges = np.asarray(ranges, dtype=float)
    distance = float(speed) * config.dt + float(speed) ** 2 / (2 * config.acceleration)
    angles = np.linspace(config.field_of_view / 2, -config.field_of_view / 2, 8)
    for column in baseline["witness_columns"]:
        nominal = float(ranges[column])
        lower, upper = (
            nominal - bounds["range_error_m"],
            nominal + bounds["range_error_m"],
        )
        if not math.isfinite(upper) or lower <= 0 or upper >= config.max_range:
            continue
        error = (
            bounds["range_error_m"]
            + bounds["translation_error_m"]
            + 2 * math.sin(bounds["heading_error_rad"] / 2) * upper
        )
        if not math.isfinite(error):
            continue
        allowance = (
            128
            * np.finfo(float).eps
            * max(1.0, config.max_range, distance, config.radius, upper, error)
        )
        point = nominal * np.array([math.cos(angles[column]), math.sin(angles[column])])
        separation = math.hypot(point[0] - np.clip(point[0], 0, distance), point[1])
        result["point_error_bound_m"][column] = error
        if separation + error < config.radius - allowance:
            result["witness_columns"].append(column)
    if result["witness_columns"]:
        result.update(
            status="blocked_witness",
            reason="assumed_error_ball_inside_braking_footprint",
        )
    return result


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
        _finite_float(value, name)
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
