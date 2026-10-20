"""Read-only diagnostic source evidence, not family attestation or task data."""

import argparse
import hashlib
import json
from dataclasses import fields
from pathlib import Path

from sim.rover import Config, Scenario
from teacher.label_pipeline import digest

CHUNK_BYTES = 1_048_576


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate metadata JSON key")
        result[key] = value
    return result


def _nonfinite_constant(value):
    raise ValueError("nonfinite metadata JSON constant")


def audit_source(path):
    path = Path(path)
    with path.open("rb") as stream:
        header = stream.readline(CHUNK_BYTES + 1)
        if len(header) > CHUNK_BYTES:
            raise ValueError("metadata header exceeds 1 MiB limit")
        metadata = json.loads(
            header, object_pairs_hook=_unique_object, parse_constant=_nonfinite_constant
        )
        if (
            not isinstance(metadata, dict)
            or metadata.get("schema") != "micro-classifier/sim-episode/1"
            or metadata.get("kind") != "metadata"
        ):
            raise ValueError("source requires simulator episode metadata first")
        config_fields = {field.name for field in fields(Config)}
        if any(
            not isinstance(metadata.get(name), dict)
            or set(metadata[name]) not in allowed
            for name, allowed in (
                ("config", (config_fields, config_fields - {"tof_rate_hz"})),
                ("scenario", ({field.name for field in fields(Scenario)},)),
            )
        ):
            raise ValueError(
                "complete declared configuration/scenario fields are required"
            )
        try:
            config = Config.from_record(metadata["config"])
            scenario = Scenario(**metadata["scenario"])
            scenario.validate(config)
        except (TypeError, KeyError) as error:
            raise ValueError("invalid declared configuration/scenario") from error
        if not isinstance(scenario.name, str) or not scenario.name:
            raise ValueError("declared scene name must be a nonempty string")
        seed, policy = metadata.get("seed"), metadata.get("policy")
        if seed is not None and (type(seed) is not int or seed < 0):
            raise ValueError("declared seed must be a nonnegative integer or absent")
        if policy is not None and (not isinstance(policy, str) or not policy):
            raise ValueError("declared policy must be a nonempty string or absent")
        file_hash = hashlib.sha256(header)
        size, lines, final = len(header), header.count(b"\n"), header[-1:]
        for chunk in iter(lambda: stream.read(CHUNK_BYTES), b""):
            file_hash.update(chunk)
            size += len(chunk)
            lines += chunk.count(b"\n")
            final = chunk[-1:]
        lines += final != b"\n"
    return {
        "path": str(path),
        "episode_sha256": file_hash.hexdigest(),
        "byte_count": size,
        "line_count": lines,
        "metadata_sha256": digest(metadata),
        "config_sha256": digest(metadata["config"]),
        "scenario_sha256": digest(metadata["scenario"]),
        "geometry_sha256": digest(
            {key: value for key, value in metadata["scenario"].items() if key != "name"}
        ),
        "declared_scene_name": scenario.name,
        "declared_seed": seed,
        "declared_policy": policy,
        "source_family": None,
        "template_family": None,
        "reviewed": False,
        "partition": None,
        "allowed_use": "diagnostic_only",
    }


def audit_sources(paths):
    paths = list(paths)
    if not 1 <= len(paths) <= 16:
        raise ValueError("audit requires 1-16 existing diagnostic sources")
    sources = [audit_source(path) for path in paths]
    comparisons = []
    for criterion in (
        "episode_sha256",
        "config_sha256",
        "geometry_sha256",
        "declared_scene_name",
    ):
        buckets = {}
        for index, source in enumerate(sources):
            buckets.setdefault(source[criterion], []).append(index)
        for identity, indices in sorted(buckets.items()):
            if len(indices) > 1:
                comparisons.append(
                    {
                        "criterion": criterion,
                        "identity": identity,
                        "source_indices": indices,
                    }
                )
    return {
        "schema": "micro-classifier/diagnostic-provenance-audit/1",
        "allowed_use": "diagnostic_metadata_review_preparation_only",
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "audit_scope": "byte_identity_and_declared_metadata_only",
        "body_validation_performed": False,
        "reviewer_input": False,
        "training_approved": False,
        "reviewed_dataset": False,
        "task_cohort_accepted": False,
        "split_locked": False,
        "all_sources_quarantined": True,
        "accepted_family_assignments": 0,
        "actual_annotations": 0,
        "mode_labels": 0,
        "teacher_calls": 0,
        "source_count": len(sources),
        "distinct_episode_count": len({source["episode_sha256"] for source in sources}),
        "sources": sources,
        "candidate_comparisons": comparisons,
        "limitations": [
            "Metadata is declared, not attested source/template lineage.",
            "Matches are candidate similarities, never accepted family/cohort/split assignments.",
            "Byte/JSON inequality does not prove independence; mirrors, rotations and variants need review.",
            "Geometry identity excludes the name but preserves exact values and obstacle ordering.",
            "Only the metadata header is parsed; observation/action/label bodies are not validated or reproduced.",
            "All source bytes are hashed; 16-file admission does not bound total input I/O.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = audit_sources(args.episode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "source_count",
                    "distinct_episode_count",
                    "accepted_family_assignments",
                    "actual_annotations",
                    "teacher_calls",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
