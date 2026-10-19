"""Bounded simulation readiness preparation, never task labels or training data."""

import argparse
import hashlib
import json
import os
import platform
import random
import re
import uuid
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import numpy as np

from sim.diagnostics import SCENES
from sim.rover import Config, RoverEnv, make_scenario, rollout, write_episode
from teacher.label_pipeline import canonical, episode_requests
from teacher.provenance import audit_sources
from teacher.review import make_review_packet, validate_review_packet


def project_review_packet(packet, review_id):
    """Strip private lineage while preserving the validated complete student input."""
    validate_review_packet(packet)
    if (
        not isinstance(review_id, str)
        or re.fullmatch(r"[a-f0-9]{32}", review_id) is None
    ):
        raise ValueError("review ID must be an opaque 32-character hexadecimal value")
    return {
        "schema": "micro-classifier/readiness-blind-projection/1",
        "review_id": review_id,
        "allowed_use": "quarantined_readiness_preparation_only",
        "review_status": "unreviewed",
        "training_approved": False,
        "task_labels_approved": False,
        "split_locked": False,
        **{
            name: deepcopy(packet[name])
            for name in ("state", "questions", "assessments")
        },
    }


def validate_projection(projection, packet):
    if not isinstance(projection, dict):
        raise TypeError("blind projection must be an object")
    expected = project_review_packet(packet, projection.get("review_id"))
    if canonical(projection) != canonical(expected):
        raise ValueError("blind projection differs from its validated blank source")


def select_review_requests(path):
    """Retain declared ticks and the actual final input, never pad or class-select."""
    selected, last = {}, None
    for request in episode_requests(path):
        tick = request["source"]["tick"]
        if tick > Config().max_ticks or canonical(
            request["provenance"]["config"]
        ) != canonical(asdict(Config())):
            raise ValueError("readiness requires normal Config and at most 400 ticks")
        if tick in (0, 7, 15):
            selected[tick] = request
        last = request
    if last is None:
        raise ValueError("readiness episode contains no observations")
    selected[last["source"]["tick"]] = last
    return [selected[tick] for tick in sorted(selected)]


def _fresh_paths(paths):
    paths = [Path(path) for path in paths]
    for path in paths:
        if path.exists() or path.is_symlink():
            raise FileExistsError(path)
        for parent in path.parents:
            if parent.exists() and not parent.is_dir():
                raise NotADirectoryError(parent)
    resolved = [path.resolve() for path in paths]
    for index, path in enumerate(resolved):
        for other in resolved[index + 1 :]:
            if path.is_relative_to(other) or other.is_relative_to(path):
                raise ValueError("readiness destinations must not overlap")
    return paths


def _write_private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_readiness_pilot(episode_dir, blind_path, audit_path, report_path):
    """Run the approved fixed eight-episode, at-most-32-blank-window package."""
    episode_dir, blind_path, audit_path, report_path = _fresh_paths(
        (episode_dir, blind_path, audit_path, report_path)
    )
    episode_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
    projections, mappings, episodes = [], [], []
    input_matches = {}
    for scene_index, scene in enumerate(SCENES):
        for repeat in range(2):
            seed = 20261020 + 2 * scene_index + repeat
            env = RoverEnv(Config(), make_scenario(scene, seed))
            env.reset(seed=seed)
            records, summary = rollout(env)
            records[0].update(
                allowed_use="quarantined_readiness_preparation_only",
                training_approved=False,
                task_labels_approved=False,
                reviewed=False,
                source_family=None,
                template_family=None,
                partition=None,
            )
            path = episode_dir / f"{scene}-{repeat}.jsonl"
            write_episode(path, records)
            requests = select_review_requests(path)
            if requests[-1]["source"]["tick"] != summary["ticks"]:
                raise ValueError("readiness summary and final observation disagree")
            for request in requests:
                packet = make_review_packet(request)
                review_id = uuid.uuid4().hex
                projection = project_review_packet(packet, review_id)
                validate_projection(projection, packet)
                projections.append(projection)
                mappings.append({"review_id": review_id, "packet": packet})
                input_matches.setdefault(packet["state_sha256"], []).append(
                    {
                        "review_id": review_id,
                        "episode_sha256": packet["source"]["episode_sha256"],
                        "tick": packet["source"]["tick"],
                    }
                )
            episodes.append(
                {
                    "path": path.as_posix(),
                    "scene": scene,
                    "repeat": repeat,
                    "seed": seed,
                    "summary": summary,
                    "selected_ticks": [
                        request["source"]["tick"] for request in requests
                    ],
                    "observation_count": summary["ticks"] + 1,
                }
            )
    if len(projections) > 32 or len({row["review_id"] for row in projections}) != len(
        projections
    ):
        raise ValueError("readiness projection cap or opaque-ID uniqueness failed")
    random.SystemRandom().shuffle(projections)
    provenance = audit_sources([episode["path"] for episode in episodes])
    matches = [
        {"state_sha256": identity, "members": members}
        for identity, members in sorted(input_matches.items())
        if len(members) > 1
    ]
    blind = {
        "schema": "micro-classifier/readiness-blind-bundle/1",
        "allowed_use": "quarantined_readiness_preparation_only",
        "review_status": "unreviewed",
        "training_approved": False,
        "task_labels_approved": False,
        "actual_annotations": 0,
        "mode_labels": 0,
        "projections": projections,
    }
    audit = {
        "schema": "micro-classifier/readiness-private-audit/1",
        "reviewer_input": False,
        "training_approved": False,
        "provenance_audit": provenance,
        "mappings": mappings,
        "exact_input_matches": matches,
    }
    blind_hash = _write_private_json(blind_path, blind)
    audit_hash = _write_private_json(audit_path, audit)
    root = Path(__file__).resolve().parents[1]
    sources = (
        "teacher/readiness.py",
        "teacher/review.py",
        "teacher/label_pipeline.py",
        "teacher/provenance.py",
        "sim/diagnostics.py",
        "sim/rover.py",
        "sim/labels.py",
        "sim/catalogue.json",
        "interface/protocol.py",
    )
    report = {
        "schema": "micro-classifier/readiness-pilot-report/1",
        "protocol": "sim-task-data-protocol/draft-1-readiness-only",
        "claim": "simulator_provenance_and_blank_projection_readiness_only",
        "allowed_use": "quarantined_readiness_preparation_only",
        "reviewer_input": False,
        "training_approved": False,
        "task_labels_approved": False,
        "task_cohort_accepted": False,
        "uncertainty_qualified": False,
        "real_input_qualified": False,
        "physical_safety_claim": False,
        "locked_task_splits": False,
        "accepted_family_assignments": 0,
        "actual_annotations": 0,
        "mode_labels": 0,
        "teacher_calls": 0,
        "candidate_scene_parent_count": len(SCENES),
        "sufficient_for_five_purposes": False,
        "episode_count": len(episodes),
        "observation_count": sum(row["observation_count"] for row in episodes),
        "projection_count": len(projections),
        "full_history_projection_count": sum(
            all(row["state"]["module_observation"]["history_valid"])
            for row in projections
        ),
        "distinct_selected_inputs": len(input_matches),
        "exact_input_match_group_sizes": sorted(len(row["members"]) for row in matches),
        "max_sources_sharing_selected_input": max(
            len({row["episode_sha256"] for row in members})
            for members in input_matches.values()
        ),
        "observation_renderer_validation_performed": True,
        "full_action_truth_body_validation_performed": False,
        "config": asdict(Config()),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "source_sha256": {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in sources
        },
        "episodes": episodes,
        "provenance_audit": provenance,
        "blind_artifact": {"path": blind_path.as_posix(), "sha256": blind_hash},
        "private_audit_artifact": {"path": audit_path.as_posix(), "sha256": audit_hash},
        "limitations": [
            "All source episodes, projections and metadata remain quarantined; no task dataset or annotations.",
            "Only the blind bundle is reviewer input; report, source logs and audit mapping are private diagnostic evidence.",
            "Opaque IDs, shuffle and file permissions are separation aids, not anonymity against recognizable inputs or the same user.",
            "Exact input matches and declared-geometry similarities are evidence, not accepted family assignments or independence proof.",
            "Privileged map-aware controller outcomes are not labels, an operational controller or representative task-quality evidence.",
            "No uncertainty/registration/spatial-coverage qualification, oracle/witness application, real-review import or training path.",
        ],
    }
    _write_private_json(report_path, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-dir", type=Path, required=True)
    parser.add_argument("--blind-output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run_readiness_pilot(
        args.episode_dir, args.blind_output, args.audit_output, args.report
    )
    print(
        json.dumps(
            {
                name: report[name]
                for name in (
                    "episode_count",
                    "observation_count",
                    "projection_count",
                    "distinct_selected_inputs",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
