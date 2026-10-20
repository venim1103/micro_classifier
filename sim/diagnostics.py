"""Privileged simulator sensor diagnostics, never task labels or physical metrology."""

import argparse
import hashlib
import json
import math
import platform
from copy import deepcopy
from dataclasses import asdict
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
