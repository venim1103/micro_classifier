"""Unqualified observation-only heuristic for the synthetic rover profile."""

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np

from interface.protocol import (
    RULES_CATALOGUE_VERSION,
    RULES_QUESTIONS,
    Answer,
    Decision,
    Status,
    decode_decision,
    decode_state,
    encode_state,
)
from sim.labels import stopping_envelope, validate_observation
from sim.rover import (
    Config,
    RoverEnv,
    integrate,
    make_scenario,
    state_from_observation,
    tof_directions,
    write_episode,
)


@dataclass(frozen=True)
class RuleSettings:
    floor_band_m: float = 0.03
    max_age_s: float | None = None
    register_motion: bool = False

    def __post_init__(self):
        if type(self.register_motion) is not bool:
            raise ValueError("motion registration must be an explicit boolean")
        for value in (self.floor_band_m, self.max_age_s):
            if value is None and self.max_age_s is None:
                continue
            try:
                valid = (
                    type(value) in (int, float) and math.isfinite(value) and value >= 0
                )
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError("rule settings must be finite nonnegative numbers")
        if self.floor_band_m is None:
            raise ValueError("floor band is required")


def _registered_columns(observation, config, rays, supported, obstacles):
    tick, captured = observation["tick"], observation["tof_sample_tick"]
    age_ticks = tick - captured
    if (
        config.odometry_latency_ticks
        or observation.get("ego_sample_tick", tick) != tick
        or age_ticks >= config.history_ticks
        or not math.isclose(
            observation["time_s"], tick * config.dt, rel_tol=1e-6, abs_tol=1e-9
        )
    ):
        raise ValueError("registration requires synchronous visible motion history")
    history = np.asarray(observation["history_ego"])
    valid = np.asarray(observation["history_valid"])
    if (
        history.shape != (config.history_ticks, 4)
        or history.dtype.kind not in "iuf"
        or not np.isfinite(history).all()
        or valid.shape != (config.history_ticks,)
        or valid.dtype.kind != "b"
        or not valid[-(age_ticks + 1) :].all()
        or not np.array_equal(history[-1], observation["ego"])
    ):
        raise ValueError("registration history is incomplete or inconsistent")
    motion = history[len(history) - age_ticks :]
    speed_limit = max(config.max_speed, float(np.float32(config.max_speed)))
    turn_limit = max(config.max_turn_rate, float(np.float32(config.max_turn_rate)))
    if (
        (motion[:, 0] < 0).any()
        or (motion[:, 0] > speed_limit).any()
        or (np.abs(motion[:, 1]) > turn_limit).any()
    ):
        raise ValueError("registration motion exceeds the simulated domain")
    position, yaw = np.zeros(2), 0.0
    for sample in motion:
        position, yaw = integrate(
            position, yaw, float(sample[0]), float(sample[1]), config.dt
        )
    cosine, sine = math.cos(yaw), math.sin(yaw)
    points = np.asarray(observation["tof_m"])[..., None] * rays[..., :2]
    current = (points - position) @ np.array([[cosine, -sine], [sine, cosine]])
    distances = np.linalg.norm(current, axis=-1)
    bearings = np.arctan2(current[..., 1], current[..., 0])
    half_view = config.field_of_view / 2
    usable = supported & (distances > 0) & (np.abs(bearings) <= half_view + 1e-12)
    columns = np.rint((half_view - bearings) * 7 / config.field_of_view).astype(int)
    columns = np.clip(columns, 0, 7)
    if not np.bincount(columns[usable], minlength=8).all():
        raise ValueError("registered returns do not support every current column")
    clearances = np.full(8, config.max_range)
    selected = usable & obstacles
    np.minimum.at(clearances, columns[selected], distances[selected])
    return clearances


def decide(observation, *, config=None, settings=None):
    """Return heuristic selections, not geometric labels or calibrated probabilities."""
    config = Config() if config is None else config
    settings = RuleSettings() if settings is None else settings
    if not isinstance(config, Config) or not isinstance(settings, RuleSettings):
        raise TypeError("rules require Config and RuleSettings")
    rejected = Decision(status=Status.REJECT_OUT_OF_DOMAIN)
    try:
        ego, ranges, valid, _ = validate_observation(observation, config)
        state = state_from_observation(observation)
        encode_state(state)
    except (TypeError, ValueError, KeyError, OverflowError):
        return rejected
    rejected = replace(
        rejected, sequence=state.sequence, timestamp_us=state.timestamp_us
    )
    if (
        config.tof_mount_height is None
        or settings.floor_band_m >= config.tof_mount_height
    ):
        return rejected
    maximum_age = settings.max_age_s
    if maximum_age is None:
        maximum_age = (config.latency_ticks + 1) * config.dt
    age = observation["tof_age_s"]
    if (
        observation["tof_sample_tick"] is None
        or age > maximum_age + 1e-12
        or max(state.ages_us[:3]) / 1_000_000 > maximum_age + 1e-12
    ):
        return replace(rejected, status=Status.REJECT_STALE_INPUT)
    rays = tof_directions(0, config)
    heights = config.tof_mount_height + ranges * rays[..., 2]
    supported = valid & (ranges > 0) & (ranges < config.max_range)
    if (
        not supported.any(axis=0).all()
        or (supported & (heights < -settings.floor_band_m)).any()
    ):
        return rejected
    obstacles = supported & (heights > settings.floor_band_m)
    horizontal = ranges * np.linalg.norm(rays[..., :2], axis=-1)
    columns = np.min(np.where(obstacles, horizontal, config.max_range), axis=0)
    if settings.register_motion:
        try:
            columns = _registered_columns(
                observation, config, rays, supported, obstacles
            )
        except (TypeError, ValueError, KeyError, OverflowError):
            return rejected
    sectors = [
        float(np.min(columns[indices]))
        for indices in ([0, 1, 2], [2, 3, 4, 5], [5, 6, 7])
    ]
    speed = min(float(ego[0]), config.max_speed)
    envelope = stopping_envelope(speed, age, config)
    if envelope >= config.max_range:
        return rejected
    bearing = math.atan2(float(ego[3]), float(ego[2]))
    headings = (config.field_of_view / 3, 0, -config.field_of_view / 3)
    candidates = [index for index in (1, 0, 2) if sectors[index] > envelope]
    sector = (
        min(candidates, key=lambda index: abs(bearing - headings[index]))
        if candidates
        else 3
    )
    tier = 0
    for candidate in range(1, 4):
        momentum_speed = max(speed, config.max_speed * candidate / 3)
        if sectors[1] > stopping_envelope(momentum_speed, age, config):
            tier = candidate
    selections = (int(sectors[1] <= envelope), sector, tier)
    answers = tuple(
        Answer(
            question,
            tuple(float(index == selected) for index in range(len(options))),
            selected,
        )
        for (question, (_, options)), selected in zip(
            RULES_QUESTIONS.items(), selections, strict=True
        )
    )
    return replace(rejected, status=Status.OK, answers=answers)


def host_action(state_frame, decision_frame, *, config=None, settings=None):
    """Diagnostic host controller; caller-declared absence/rejection commands braking."""
    config = Config() if config is None else config
    settings = RuleSettings() if settings is None else settings
    stopped = np.zeros(2)
    if decision_frame is None:
        return stopped
    try:
        state = decode_state(state_frame)
        decision = decode_decision(decision_frame)
    except (TypeError, ValueError):
        return stopped
    maximum_age = settings.max_age_s
    if maximum_age is None:
        maximum_age = (config.latency_ticks + 1) * config.dt
    if (
        decision.status != Status.OK
        or decision.catalogue_version != RULES_CATALOGUE_VERSION
        or decision.sequence != state.sequence
        or decision.timestamp_us != state.timestamp_us
        or state.validity & 7 != 7
        or max(state.ages_us[:3]) / 1_000_000 > maximum_age + 1e-12
    ):
        return stopped
    blocked, sector, tier = (answer.selected for answer in decision.answers)
    if sector == 3:
        return stopped
    bearing = math.atan2(state.goal_m[1], state.goal_m[0])
    turn = (
        config.max_turn_rate
        if sector == 0
        else -config.max_turn_rate
        if sector == 2
        else float(np.clip(2 * bearing, -config.max_turn_rate, config.max_turn_rate))
    )
    speed = (
        0.0
        if blocked or abs(bearing) > config.field_of_view / 2
        else min(config.max_speed * tier / 3, math.hypot(*state.goal_m[:2]))
    )
    return np.array([speed, turn])


def wire_step(observation, *, config=None, settings=None):
    """Loop back state and decision frames; no true pose, map or reference answers."""
    from interface.protocol import encode_decision

    state_frame = encode_state(state_from_observation(observation))
    state = decode_state(state_frame)
    module_input = dict(observation)
    module_input["ego"] = np.array(
        [state.velocity_m_s[0], state.angular_velocity_rad_s[2], *state.goal_m[:2]],
        dtype=np.float32,
    )
    module_input["goal_body_m"] = module_input["ego"][2:].copy()
    decision = decide(module_input, config=config, settings=settings)
    decision_frame = encode_decision(decision)
    return (
        host_action(state_frame, decision_frame, config=config, settings=settings),
        state_frame,
        decision_frame,
    )


def _diagnostic_episode(scene, seed, config, settings):
    from sim.navigation import evaluate_synthetic

    env = RoverEnv(config, make_scenario(scene, seed))
    observation, info = env.reset(seed=seed)
    comparisons = {
        name: {"matched": 0, "disagreed": 0, "unknown": 0}
        for name in ("path_blocked", "clear_sector", "speed_tier")
    }
    statuses = {status.name: 0 for status in Status}
    false_clear = 0
    total_reward = 0.0
    records = [
        {
            "kind": "metadata",
            "schema": "micro-classifier/rules-diagnostic/1",
            "allowed_use": "quarantined_heuristic_diagnostics_only",
            "training_approved": False,
            "task_labels": False,
            "seed": seed,
            "scenario": asdict(env.scenario),
            "config": asdict(config),
            "settings": asdict(settings),
            "policy": "observation_only_wire_rules",
        }
    ]
    while not env.done:
        action, state_frame, decision_frame = wire_step(
            observation, config=config, settings=settings
        )
        decision = decode_decision(decision_frame)
        statuses[Status(decision.status).name] += 1
        if decision.status == Status.OK:
            scenario = replace(
                env.scenario, start=(*env.position.tolist(), float(env.yaw))
            )
            reference = evaluate_synthetic(
                scenario,
                speed=env.speed,
                turn_rate=env.turn_rate,
                tof_age_s=observation["tof_age_s"],
                config=config,
                synthetic_test_only=True,
            )["answers"]
            for answer in decision.answers:
                name = next(
                    question.name.lower()
                    for question in RULES_QUESTIONS
                    if question == answer.question_id
                )
                predicted = RULES_QUESTIONS[answer.question_id][1][answer.selected]
                actual = reference[name]
                outcome = (
                    "unknown"
                    if actual is None
                    else "matched"
                    if actual == predicted
                    else "disagreed"
                )
                comparisons[name][outcome] += 1
                false_clear += int(
                    name == "path_blocked" and predicted == "false" and actual == "true"
                )
        following, reward, terminated, truncated, following_info = env.step(action)
        records.append(
            {
                "kind": "transition",
                "observation": observation,
                "state_frame_hex": state_frame.hex(),
                "decision_frame_hex": decision_frame.hex(),
                "action": action,
                "reward": reward,
                "terminated": terminated,
                "truncated": truncated,
                "diagnostic_info": info,
            }
        )
        total_reward += reward
        observation, info = following, following_info
    summary = {
        "kind": "summary",
        "scene": scene,
        "seed": seed,
        "ticks": env.tick,
        "total_reward": total_reward,
        "success": info["success"],
        "collision": info["collision"],
        "timeout": info["timeout"],
        "final_observation": observation,
        "diagnostic_info": info,
        "statuses": statuses,
        "reference_comparisons": comparisons,
        "heuristic_false_clear_vs_reference": false_clear,
    }
    records.append(summary)
    return records, summary


def run_diagnostics(output, report, *, seed=20261020, config=None, settings=None):
    """Eight bounded fresh diagnostic episodes, never a training/evaluation dataset."""
    config = Config() if config is None else config
    settings = RuleSettings() if settings is None else settings
    if not isinstance(config, Config) or not isinstance(settings, RuleSettings):
        raise TypeError("diagnostics require Config and RuleSettings")
    if type(seed) is not int or seed < 0 or config.max_ticks > 400:
        raise ValueError("diagnostics require a nonnegative seed and at most 400 ticks")
    output, report = Path(output).resolve(), Path(report).resolve()
    if (
        output.exists()
        or report.exists()
        or output == report
        or output in report.parents
        or report in output.parents
    ):
        raise ValueError("diagnostic outputs must be fresh and nonoverlapping")
    root = Path(__file__).resolve().parents[1]
    sources = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in (
            "sim/rules.py",
            "sim/rover.py",
            "sim/labels.py",
            "sim/navigation.py",
            "interface/protocol.py",
        )
    }
    output.mkdir(parents=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    episodes = []
    for scene in ("clear", "obstacle", "corridor", "slalom"):
        for offset in range(2):
            records, summary = _diagnostic_episode(
                scene, seed + offset, config, settings
            )
            path = output / f"{scene}-{seed + offset}.jsonl"
            write_episode(path, records)
            episodes.append(
                {
                    **{
                        name: value
                        for name, value in summary.items()
                        if name not in ("kind", "final_observation", "diagnostic_info")
                    },
                    "path": str(path.relative_to(root))
                    if path.is_relative_to(root)
                    else str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "state_frames": summary["ticks"],
                    "decision_frames": summary["ticks"],
                }
            )
    result = {
        "schema": "micro-classifier/rules-diagnostic-report/1",
        "allowed_use": "quarantined_heuristic_diagnostics_only",
        "training_approved": False,
        "task_labels": False,
        "calibrated": False,
        "physical_safety_claim": False,
        "rule_quality_qualified": False,
        "config": asdict(config),
        "settings": asdict(settings),
        "sources": sources,
        "episodes": episodes,
        "totals": {
            "episodes": len(episodes),
            **{
                name: sum(row[name] for row in episodes)
                for name in (
                    "ticks",
                    "success",
                    "collision",
                    "timeout",
                    "heuristic_false_clear_vs_reference",
                )
            },
        },
        "limitations": [
            "One-hot rule outputs are not calibrated probabilities or proof of clearance.",
            "Sparse point rays, Gaussian noise and heuristic floor removal remain unqualified.",
            "No motion compensation; age-bounded returns remain in the acquisition frame.",
            "Oracle comparisons use privileged current truth only after the controller chooses its action.",
            "Eight runs in four existing scene families are not independent task coverage or locked splits.",
            "Caller-declared missing decisions brake; no serial clock, real timeout or target execution was measured.",
            "Decision latency_us is an unmeasured diagnostic placeholder of zero, not measured execution time.",
        ],
    }
    with report.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261020)
    args = parser.parse_args()
    result = run_diagnostics(args.output, args.report, seed=args.seed)
    print(json.dumps(result["totals"], sort_keys=True))


if __name__ == "__main__":
    main()
