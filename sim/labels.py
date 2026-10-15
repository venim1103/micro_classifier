"""Unreviewed sensor-proxy label draft for tooling and unit tests only."""

import hashlib
import json
import math
from dataclasses import asdict
from numbers import Real
from pathlib import Path

import numpy as np

from sim.rover import Config


def draft_catalogue():
    return json.loads(Path(__file__).with_name("catalogue.json").read_text())


def stopping_envelope(speed, age_s, config=None):
    config = Config() if config is None else config
    for name, value in (("speed", speed), ("age", age_s)):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a finite number")
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be nonnegative and finite")
    if speed > config.max_speed:
        raise ValueError("speed exceeds simulation Config.max_speed")
    distance = (
        config.radius
        + speed * (age_s + config.dt)
        + speed**2 / (2 * config.acceleration)
    )
    if not math.isfinite(distance):
        raise ValueError("stopping envelope must be finite")
    return distance


def digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def draft_labels(observation, config=None):
    config = Config() if config is None else config
    if not isinstance(config, Config):
        raise TypeError("config must be a simulator Config")
    if observation.get("schema") != "micro-classifier/sim-observation/1":
        raise ValueError("unsupported observation schema")
    required = {"ego", "tof_m", "tof_valid", "tick", "tof_sample_tick", "tof_age_s"}
    if not required.issubset(observation):
        raise ValueError("observation is missing required fields")
    ego = np.asarray(observation["ego"])
    ranges = np.asarray(observation["tof_m"])
    valid = np.asarray(observation["tof_valid"])
    for name, values, shape in (("ego", ego, (4,)), ("ToF", ranges, (8, 8))):
        if values.shape != shape or values.dtype.kind not in "iuf":
            raise ValueError(f"{name} requires numeric values with shape {shape}")
        if not np.isfinite(values).all():
            raise ValueError(f"{name} values must be finite")
    if valid.shape != (8, 8) or valid.dtype.kind != "b":
        raise ValueError("ToF validity requires an 8x8 boolean mask")
    limits = {
        name: max(value, float(np.float32(value)))
        for name, value in (
            ("speed", config.max_speed),
            ("turn", config.max_turn_rate),
            ("range", config.max_range),
        )
    }
    if not 0 <= ego[0] <= limits["speed"] or abs(ego[1]) > limits["turn"]:
        raise ValueError("ego motion exceeds simulation limits")
    if (ranges < 0).any() or (ranges > limits["range"]).any():
        raise ValueError("ToF ranges exceed simulation limits")
    if (ranges[~valid] != 0).any():
        raise ValueError("invalid ToF cells must contain zero")
    tick = observation["tick"]
    sample_tick = observation["tof_sample_tick"]
    if type(tick) is not int or tick < 0:
        raise ValueError("tick must be a nonnegative integer")
    if sample_tick is not None and (
        type(sample_tick) is not int or not 0 <= sample_tick <= tick
    ):
        raise ValueError("invalid ToF sample tick")
    if sample_tick is None and valid.any():
        raise ValueError("valid ToF requires a known sample tick")
    age = observation["tof_age_s"]
    speed = min(float(ego[0]), config.max_speed)
    envelope = stopping_envelope(speed, age, config)
    if sample_tick is not None and not math.isclose(
        age, (tick - sample_tick) * config.dt, rel_tol=1e-6, abs_tol=1e-9
    ):
        raise ValueError("ToF age and sample tick disagree")
    catalogue = draft_catalogue()
    rules = catalogue["rules"]
    columns = np.min(np.where(valid, ranges, np.inf), axis=0)
    sectors = {}
    for name, indices in rules["sector_columns"].items():
        values = columns[indices]
        sectors[name] = float(np.min(values)) if np.isfinite(values).all() else None
    answers = {
        row["name"]: {
            "selected": None,
            "value": None,
            "reason": "human_review_required",
            "label_source": row["label_source"],
        }
        for row in catalogue["questions"]
    }
    options = {row["name"]: row["options"] for row in catalogue["questions"]}

    def assign(name, value, reason):
        answers[name].update(
            value=value,
            selected=options[name].index(value) if value is not None else None,
            reason=reason,
        )

    unavailable = None
    if sample_tick is None:
        unavailable = "no_tof_sample"
    elif age > (config.latency_ticks + 1) * config.dt + 1e-12:
        unavailable = "stale_tof"
    elif envelope >= config.max_range:
        unavailable = "envelope_outside_sensor_range"
    if unavailable:
        for name in ("path_blocked", "clear_sector", "speed_tier"):
            assign(name, None, unavailable)
    else:
        centre = sectors["centre"]
        if centre is None:
            for name in ("path_blocked", "speed_tier"):
                assign(name, None, "incomplete_centre_coverage")
        else:
            assign(
                "path_blocked",
                "true" if centre <= envelope else "false",
                "sensor_proxy",
            )
            tier = 0
            for index, fraction in enumerate(rules["speed_fractions"]):
                if centre > stopping_envelope(config.max_speed * fraction, age, config):
                    tier = index
            assign("speed_tier", str(tier), "sensor_proxy")
        if any(value is None for value in sectors.values()):
            assign("clear_sector", None, "incomplete_sector_coverage")
        else:
            candidates = [
                name for name in rules["sector_tie_order"] if sectors[name] > envelope
            ]
            selected = (
                max(candidates, key=sectors.__getitem__) if candidates else "none"
            )
            assign("clear_sector", selected, "sensor_proxy")
    inputs = {
        "tick": tick,
        "ego": ego.tolist(),
        "tof_m": ranges.tolist(),
        "tof_valid": valid.tolist(),
        "tof_age_s": float(age),
        "tof_sample_tick": sample_tick,
    }
    settings = asdict(config)
    return {
        "schema": "micro-classifier/sim-label-draft/1",
        "review_status": "unreviewed_draft",
        "allowed_use": "tooling_and_unit_tests_only",
        "training_approved": False,
        "physical_safety_claim": False,
        "policy_id": catalogue["policy_id"],
        "catalogue_sha256": digest(catalogue),
        "labeler_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "config": settings,
        "config_sha256": digest(settings),
        "input_sha256": digest(inputs),
        "tick": tick,
        "answers": answers,
        "evidence": {"envelope_m": envelope, "sector_min_m": sectors},
    }
