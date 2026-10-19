"""Draft sensor proxies; approved for simulation smoke and pipeline tests only."""

import argparse
import hashlib
import json
import math
import platform
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import UTC, datetime
from functools import lru_cache
from numbers import Real
from pathlib import Path

import numpy as np

from sim.rover import (
    Config,
    RoverEnv,
    Scenario,
    json_value,
    make_scenario,
    rollout,
    write_episode,
)


@lru_cache(maxsize=4)
def _cached_file_snapshot(path, _identity):
    content = path.read_bytes()
    return content, hashlib.sha256(content).hexdigest()


def _file_snapshot(path):
    metadata = path.stat()
    identity = (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
        metadata.st_size,
    )
    return _cached_file_snapshot(path, identity)


def draft_catalogue():
    content, _ = _file_snapshot(Path(__file__).with_name("catalogue.json"))
    return json.loads(content)


def stopping_envelope(speed, age_s, config=None):
    config = Config() if config is None else config
    for name, value in (("speed", speed), ("age", age_s)):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a finite number")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite or value < 0:
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


def validate_observation(observation, config=None):
    """Validate current simulator input without computing proxy labels or provenance."""
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
    return ego, ranges, valid, envelope


def draft_labels(observation, config=None):
    config = Config() if config is None else config
    ego, ranges, valid, envelope = validate_observation(observation, config)
    tick = observation["tick"]
    sample_tick = observation["tof_sample_tick"]
    age = observation["tof_age_s"]
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
        "allowed_use": catalogue["allowed_use"],
        "training_approved": False,
        "physical_safety_claim": False,
        "policy_id": catalogue["policy_id"],
        "catalogue_sha256": digest(catalogue),
        "labeler_sha256": _file_snapshot(Path(__file__))[1],
        "config": settings,
        "config_sha256": digest(settings),
        "input_sha256": digest(inputs),
        "tick": tick,
        "answers": answers,
        "evidence": {"envelope_m": envelope, "sector_min_m": sectors},
    }


def answer_coverage(labels):
    catalogue = draft_catalogue()
    counts = {row["name"]: Counter() for row in catalogue["questions"]}
    reasons = {name: Counter() for name in counts}
    for record in labels:
        for name, answer in record["answers"].items():
            if answer["value"] is None:
                reasons[name][answer["reason"]] += 1
            else:
                counts[name][answer["value"]] += 1
    summary = {}
    for row in catalogue["questions"]:
        name = row["name"]
        options = {option: counts[name][option] for option in row["options"]}
        missing = [option for option, count in options.items() if not count]
        summary[name] = {
            "option_counts": options,
            "answered": sum(options.values()),
            "abstained": sum(reasons[name].values()),
            "abstention_counts": dict(reasons[name]),
            "missing_options": missing,
            "all_options_observed": not missing,
        }
    return summary


def smoke_suite(output, *, seed=20261016, config=None):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer between zero and 2**63 - 1")
    config = Config() if config is None else config
    if not isinstance(config, Config):
        raise TypeError("config must be a simulator Config")
    catalogue = draft_catalogue()
    if not catalogue.get("scope_approval", {}).get("simulation_smoke"):
        raise ValueError("simulation smoke is not approved by this catalogue")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    cases = []
    for name in ("clear", "obstacle", "corridor", "slalom"):
        env = RoverEnv(config, make_scenario(name, seed))
        env.reset(seed=seed)
        records, summary = rollout(env)
        counts = {row["name"]: Counter() for row in catalogue["questions"]}
        labeled = []
        for record in records:
            entry = dict(record)
            if "observation" in entry:
                labels = draft_labels(entry["observation"], config)
                entry["simulation_label"] = labels
                for question, answer in labels["answers"].items():
                    key = answer["value"]
                    if key is None:
                        key = "abstain:" + answer["reason"]
                    counts[question][key] += 1
            if entry["kind"] == "metadata":
                entry["label_scope"] = catalogue["scope_approval"]
                entry["training_approved"] = False
            labeled.append(entry)
        path = output / f"{name}.jsonl"
        write_episode(path, labeled)
        cases.append(
            {
                "scene": name,
                "file": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
                "summary": summary,
                "answer_counts": {key: dict(value) for key, value in counts.items()},
            }
        )
    report = {
        "schema": "micro-classifier/sim-label-smoke/1",
        "created_utc": datetime.now(UTC).isoformat(),
        "seed": seed,
        "config": asdict(config),
        "catalogue_sha256": digest(catalogue),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "simulator_sha256": hashlib.sha256(
            Path(__file__).with_name("rover.py").read_bytes()
        ).hexdigest(),
        "environment": {"python": platform.python_version(), "numpy": np.__version__},
        "allowed_use": catalogue["allowed_use"],
        "training_approved": False,
        "live_teacher_labeling_approved": False,
        "physical_safety_claim": False,
        "cases": cases,
        "all_scenes_succeeded": all(row["summary"]["success"] for row in cases),
    }
    with (output / "report.json").open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return report


class _CoverageProbe:
    def __init__(self, env, approach):
        self.env = env
        self.approach = approach
        self.braking = False

    def __call__(self, observation):
        config = self.env.config
        if not self.approach:
            return (0.0, 0.0)
        speed = min(float(observation["ego"][0]), config.max_speed)
        clearance = self.env.scenario.bounds[0] - self.env.position[0]
        stop = config.radius + speed**2 / (2 * config.acceleration)
        if clearance <= stop + config.max_speed * config.dt + config.noise_std:
            self.braking = True
        return (0.0 if self.braking else config.max_speed, 0.0)


def _coverage_fixtures(config):
    age = config.latency_ticks * config.dt
    base = {
        "schema": "micro-classifier/sim-observation/1",
        "tick": config.latency_ticks + 2,
        "tof_sample_tick": 2,
        "tof_age_s": age,
        "ego": np.array([0.0, 0.0, 4.0, 0.0]),
        "tof_m": np.full((8, 8), config.max_range),
        "tof_valid": np.ones((8, 8), dtype=bool),
    }
    cases = []
    for selected in ("left", "centre", "right", "none"):
        observation = deepcopy(base)
        observation["tof_m"][:] = config.radius / 2
        if selected != "none":
            columns = draft_catalogue()["rules"]["sector_columns"][selected]
            observation["tof_m"][:, columns] = config.max_range
        cases.append((f"sector-{selected}", observation))
    fractions = draft_catalogue()["rules"]["speed_fractions"]
    for tier in range(4):
        lower = stopping_envelope(config.max_speed * fractions[tier], age, config)
        upper = (
            stopping_envelope(config.max_speed * fractions[tier + 1], age, config)
            if tier < 3
            else config.max_range
        )
        observation = deepcopy(base)
        observation["tof_m"][:] = (lower + upper) / 2
        cases.append((f"speed-tier-{tier}", observation))
    for name in ("no-sample", "stale", "missing-centre-column", "missing-left-column"):
        observation = deepcopy(base)
        if name == "no-sample":
            observation["tof_sample_tick"] = None
            observation["tof_valid"][:] = False
            observation["tof_m"][:] = 0
        elif name == "stale":
            observation["tof_sample_tick"] = 0
            observation["tof_age_s"] = observation["tick"] * config.dt
        else:
            column = 3 if name == "missing-centre-column" else 0
            observation["tof_valid"][:, column] = False
            observation["tof_m"][:, column] = 0
        cases.append((name, observation))
    return cases


def coverage_suite(output, *, seed=20261016):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer between zero and 2**63 - 1")
    config = replace(Config(), max_ticks=32)
    catalogue = draft_catalogue()
    if not catalogue.get("scope_approval", {}).get("simulation_smoke"):
        raise ValueError("simulation smoke is not approved by this catalogue")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    age = config.latency_ticks * config.dt
    envelopes = [
        stopping_envelope(config.max_speed * fraction, age, config)
        for fraction in catalogue["rules"]["speed_fractions"]
    ]
    distances = {
        "near": config.radius + config.noise_std / 2,
        "tier1": (envelopes[1] + envelopes[2]) / 2 + config.noise_std,
        "tier2": (envelopes[2] + envelopes[3]) / 2 + config.noise_std,
        "clear": envelopes[3] + config.max_speed / 3,
    }
    scenes = [(Scenario(name="open-hold"), False)]
    for name, distance in distances.items():
        scenes.append(
            (
                Scenario(
                    name=f"wall-{name}-hold",
                    start=(6 - distance, 3.0, 0.0),
                    goal=(1.0, 3.0),
                ),
                False,
            )
        )
    for side, sign in (("left", 1), ("right", -1)):
        scenes.append(
            (
                Scenario(
                    name=f"wall-{side}-hold",
                    start=(
                        6 - distances["tier2"],
                        3.0,
                        sign * config.field_of_view / 3,
                    ),
                    goal=(1.0, 3.0),
                ),
                False,
            )
        )
    scenes.append(
        (
            Scenario(
                name="wall-approach-brake", start=(5.2, 3.0, 0.0), goal=(1.0, 3.0)
            ),
            True,
        )
    )
    cases, episode_labels = [], []
    for index, (scene, approach) in enumerate(scenes):
        env = RoverEnv(config, scene)
        env.reset(seed=seed + index)
        records, summary = rollout(env, _CoverageProbe(env, approach))
        labels = []
        for record in records:
            if "observation" in record:
                record["simulation_label"] = draft_labels(record["observation"], config)
                labels.append(record["simulation_label"])
            if record["kind"] == "metadata":
                record.update(
                    training_approved=False,
                    diagnostic_only=True,
                    privileged_diagnostic_policy=approach,
                    policy_purpose="coverage_probe_not_navigation_expert",
                )
        path = output / f"{scene.name}.jsonl"
        write_episode(path, records)
        episode_labels.extend(labels)
        cases.append(
            {
                "scene": scene.name,
                "file": path.name,
                "seed": seed + index,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
                "summary": summary,
                "observation_count": len(labels),
                "coverage": answer_coverage(labels),
            }
        )
    fixtures = []
    for name, observation in _coverage_fixtures(config):
        fixtures.append(
            {
                "name": name,
                "origin": "synthetic_current_observation_only",
                "observation": json.loads(json.dumps(observation, default=json_value)),
                "label": draft_labels(observation, config),
            }
        )
    report = {
        "schema": "micro-classifier/sim-label-coverage-draft/1",
        "created_utc": datetime.now(UTC).isoformat(),
        "seed": seed,
        "review_status": "unreviewed_draft",
        "allowed_use": catalogue["allowed_use"],
        "training_approved": False,
        "live_teacher_labeling_approved": False,
        "physical_safety_claim": False,
        "representative_task_coverage_claim": False,
        "policy_review_passed": False,
        "default_config": asdict(Config()),
        "config": asdict(config),
        "config_overrides": {"max_ticks": 32},
        "episode_limit": 16,
        "catalogue_sha256": digest(catalogue),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "simulator_sha256": hashlib.sha256(
            Path(__file__).with_name("rover.py").read_bytes()
        ).hexdigest(),
        "environment": {"python": platform.python_version(), "numpy": np.__version__},
        "cases": cases,
        "episode_observation_count": len(episode_labels),
        "episode_coverage": answer_coverage(episode_labels),
        "synthetic_fixtures": fixtures,
        "synthetic_coverage": answer_coverage(row["label"] for row in fixtures),
        "limitations": [
            "Selected diagnostic scenes and artificial current-only fixtures are not task-distribution data.",
            "Near-wall positives can arise from sensor noise, not actual footprint obstruction.",
            "Stationary probes and a map-aware brake script are not navigation experts.",
            "Duration-limit timeouts are intentional; these are not goal-success evaluations.",
            "Mode remains absent for every observation; labels are not reviewed or training-approved.",
        ],
    }
    with (output / "report.json").open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--seed", type=int, default=20261016)
    parser.add_argument(
        "--coverage-study",
        action="store_true",
        help="run eight diagnostic episodes and separate synthetic coverage fixtures",
    )
    args = parser.parse_args()
    if args.report and args.report.exists():
        parser.error("report already exists; choose a new path")
    try:
        report = (coverage_suite if args.coverage_study else smoke_suite)(
            args.output, seed=args.seed
        )
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open("x") as stream:
                json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
                stream.write("\n")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "output": str(args.output),
                **(
                    {"episode_coverage": report["episode_coverage"]}
                    if args.coverage_study
                    else {"all_scenes_succeeded": report["all_scenes_succeeded"]}
                ),
                "training_approved": False,
            }
        )
    )
    if not args.coverage_study and not report["all_scenes_succeeded"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
