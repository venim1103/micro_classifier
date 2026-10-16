"""CPU diagnostics for synthetic fixtures, not reviewed task evaluation."""

import argparse
import hashlib
import json
import platform
import re
from pathlib import Path

import numpy as np

PURPOSES = (
    "train",
    "development",
    "quantization_calibration",
    "confidence_calibration",
    "test",
)
GROUP_KEYS = ("source", "episode", "template")


def _digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def evaluate_synthetic(labels, probabilities, *, options, ece_bins=10):
    if not isinstance(options, (list, tuple)) or len(options) < 2:
        raise ValueError("declare at least two ordered options")
    if any(not isinstance(option, str) or not option for option in options):
        raise ValueError("option identities must be nonempty strings")
    if len(set(options)) != len(options):
        raise ValueError("option identities must be unique")
    options = list(options)
    if type(ece_bins) is not int or ece_bins < 1:
        raise ValueError("ECE bin count must be a positive integer")
    labels = np.asarray(labels)
    probabilities = np.asarray(probabilities)
    if labels.ndim != 1 or labels.size == 0 or labels.dtype.kind not in "iu":
        raise ValueError("labels must be a nonempty vector of integer option indices")
    if (labels < 0).any() or (labels >= len(options)).any():
        raise ValueError("label index is outside the declared option order")
    if (
        probabilities.shape != (len(labels), len(options))
        or probabilities.dtype.kind not in "iuf"
    ):
        raise ValueError(
            "probabilities must have one numeric row per label and column per option"
        )
    probabilities = probabilities.astype(np.float64)
    labels = labels.astype(np.int64)
    if (
        not np.isfinite(probabilities).all()
        or (probabilities < 0).any()
        or (probabilities > 1).any()
    ):
        raise ValueError("probabilities must be finite and within [0,1]")
    if not np.allclose(probabilities.sum(axis=1), 1, rtol=0, atol=1e-6):
        raise ValueError(
            "probability rows must sum to one; no renormalization is applied"
        )
    prediction = probabilities.argmax(axis=1)
    correct = prediction == labels
    confidence = probabilities.max(axis=1)
    confusion = np.bincount(
        labels * len(options) + prediction, minlength=len(options) ** 2
    ).reshape(len(options), len(options))
    support = confusion.sum(axis=1)
    predicted = confusion.sum(axis=0)
    classes = []
    for index, option in enumerate(options):
        true_positive = int(confusion[index, index])
        denominator = int(support[index] + predicted[index])
        classes.append(
            {
                "option": option,
                "support": int(support[index]),
                "predicted": int(predicted[index]),
                "precision": true_positive / int(predicted[index])
                if predicted[index]
                else None,
                "recall": true_positive / int(support[index])
                if support[index]
                else None,
                "f1": 2 * true_positive / denominator if denominator else 0.0,
            }
        )
    target_probability = probabilities[np.arange(len(labels)), labels]
    zero_targets = int(np.count_nonzero(target_probability == 0))
    residual = probabilities.copy()
    residual[np.arange(len(labels)), labels] -= 1
    edges = np.arange(ece_bins + 1, dtype=np.float64) / ece_bins
    bin_ids = np.minimum(
        np.searchsorted(edges, confidence, side="right") - 1, ece_bins - 1
    )
    counts = np.bincount(bin_ids, minlength=ece_bins)
    confidence_sums = np.bincount(bin_ids, weights=confidence, minlength=ece_bins)
    correct_sums = np.bincount(bin_ids, weights=correct, minlength=ece_bins)
    bins = []
    ece = 0.0
    for index, count in enumerate(counts):
        accuracy = float(correct_sums[index] / count) if count else None
        mean_confidence = float(confidence_sums[index] / count) if count else None
        if count:
            ece += int(count) / len(labels) * abs(accuracy - mean_confidence)
        bins.append(
            {
                "lower": float(edges[index]),
                "upper": float(edges[index + 1]),
                "count": int(count),
                "accuracy": accuracy,
                "mean_confidence": mean_confidence,
            }
        )
    curve = [
        {
            "threshold": None,
            "accepted": 0,
            "coverage": 0.0,
            "accuracy": None,
            "risk": None,
        }
    ]
    order = np.argsort(-confidence, kind="stable")
    sorted_confidence = confidence[order]
    correct_totals = np.cumsum(correct[order])
    ends = (
        np.flatnonzero(np.r_[sorted_confidence[:-1] != sorted_confidence[1:], True]) + 1
    )
    for accepted in ends:
        accuracy = float(correct_totals[accepted - 1] / accepted)
        curve.append(
            {
                "threshold": float(sorted_confidence[accepted - 1]),
                "accepted": int(accepted),
                "coverage": int(accepted) / len(labels),
                "accuracy": accuracy,
                "risk": 1 - accuracy,
            }
        )
    return {
        "schema": "micro-classifier/synthetic-evaluation/1",
        "allowed_use": "synthetic_fixture_tests_only",
        "synthetic": True,
        "training_approved": False,
        "task_quality_claim": False,
        "options": options,
        "sample_count": len(labels),
        "input_sha256": _digest(
            {
                "labels": labels.tolist(),
                "probabilities": probabilities.tolist(),
                "options": options,
            }
        ),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "accuracy": float(correct.mean()),
        "confusion_matrix": confusion.tolist(),
        "per_class": classes,
        "missing_classes": [
            option for option, count in zip(options, support, strict=True) if not count
        ],
        "macro_f1": sum(row["f1"] for row in classes) / len(options),
        "macro_f1_policy": "all_declared_options_zero_division_0",
        "nll": None if zero_targets else float(-np.log(target_probability).mean()),
        "nll_is_infinite": bool(zero_targets),
        "zero_target_probability_count": zero_targets,
        "brier": float(np.square(residual).sum(axis=1).mean()),
        "brier_policy": "mean_sum_over_options",
        "ece": ece,
        "ece_bins": bins,
        "ece_policy": "equal_width_top_label_probability_left_closed_last_includes_1",
        "coverage_curve": curve,
        "coverage_policy": "max_probability_at_least_threshold_include_all_ties",
        "argmax_tie_policy": "first_declared_option",
    }


def validate_synthetic_splits(manifest, *, expected_sha256=None):
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"schema", "synthetic", "training_approved", "partitions"}
        or manifest["schema"] != "micro-classifier/synthetic-splits/1"
        or manifest["synthetic"] is not True
        or manifest["training_approved"] is not False
    ):
        raise ValueError(
            "only the training-disabled synthetic split schema is supported"
        )
    partitions = manifest["partitions"]
    if not isinstance(partitions, dict) or set(partitions) != set(PURPOSES):
        raise ValueError("declare all five distinct data purposes")
    sample_ids = set()
    owners = {}
    counts = {}
    for purpose in PURPOSES:
        rows = partitions[purpose]
        if not isinstance(rows, list) or not rows:
            raise ValueError("each synthetic partition requires nonempty fixture rows")
        unique_groups = {name: set() for name in GROUP_KEYS}
        inputs = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {
                "sample_id",
                "input_sha256",
                "groups",
            }:
                raise ValueError(
                    "split rows require sample_id, input_sha256 and groups"
                )
            sample_id = row["sample_id"]
            if not isinstance(sample_id, str) or not sample_id.strip():
                raise ValueError("sample identity must be a nonempty string")
            if sample_id in sample_ids:
                raise ValueError("duplicate sample identity")
            sample_ids.add(sample_id)
            checksum = row["input_sha256"]
            if not isinstance(checksum, str) or not re.fullmatch(
                r"[a-f0-9]{64}", checksum
            ):
                raise ValueError("fixture input SHA-256 must be a full lowercase hash")
            groups = row["groups"]
            if not isinstance(groups, dict) or set(groups) != set(GROUP_KEYS):
                raise ValueError("declare source, episode and template groups")
            identities = {"input_sha256": checksum, **groups}
            for name, identity in identities.items():
                if not isinstance(identity, str) or not identity.strip():
                    raise ValueError("group identities must be nonempty strings")
                key = (name, identity)
                if key in owners and owners[key] != purpose:
                    raise ValueError(f"cross-partition {name} overlap")
                owners[key] = purpose
                if name in unique_groups:
                    unique_groups[name].add(identity)
            inputs.add(checksum)
        counts[purpose] = {
            "samples": len(rows),
            "unique_inputs": len(inputs),
            "groups": {name: len(values) for name, values in unique_groups.items()},
        }
    checksum = _digest(manifest)
    if expected_sha256 is not None and expected_sha256 != checksum:
        raise ValueError("synthetic manifest hash differs from expected identity")
    return {
        "schema": "micro-classifier/synthetic-split-audit/1",
        "allowed_use": "synthetic_fixture_tests_only",
        "synthetic": True,
        "training_approved": False,
        "locked_task_splits": False,
        "group_identities_verified": False,
        "manifest_sha256": checksum,
        "partitions": counts,
    }


def synthetic_smoke_report():
    manifest = {
        "schema": "micro-classifier/synthetic-splits/1",
        "synthetic": True,
        "training_approved": False,
        "partitions": {
            purpose: [
                {
                    "sample_id": f"test/{purpose}",
                    "input_sha256": _digest({"fixture": purpose}),
                    "groups": {name: f"test/{purpose}/{name}" for name in GROUP_KEYS},
                }
            ]
            for purpose in PURPOSES
        },
    }
    return {
        "schema": "micro-classifier/synthetic-evaluation-smoke/1",
        "fixture_id": "test/metric-arithmetic-v1",
        "synthetic": True,
        "training_approved": False,
        "task_quality_claim": False,
        "locked_task_splits": False,
        "live_teacher_calls": 0,
        "training_runs": 0,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "environment": {"python": platform.python_version(), "numpy": np.__version__},
        "metrics": evaluate_synthetic(
            [0, 1, 2, 2],
            [[0.8, 0.1, 0.1], [0.2, 0.6, 0.2], [0.1, 0.7, 0.2], [0.1, 0.2, 0.7]],
            options=["first", "second", "third"],
            ece_bins=2,
        ),
        "split_audit": validate_synthetic_splits(manifest),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run built-in synthetic evaluation fixtures only."
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = synthetic_smoke_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                "synthetic": True,
                "training_approved": False,
                "task_quality_claim": False,
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
