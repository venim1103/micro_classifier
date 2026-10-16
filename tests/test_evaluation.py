import hashlib
import json
from copy import deepcopy

import numpy as np
import pytest

from teacher.evaluation import (
    PURPOSES,
    evaluate_synthetic,
    main,
    validate_synthetic_splits,
)


@pytest.fixture
def arithmetic_fixture():
    return [0, 1, 2, 2], [
        [0.8, 0.1, 0.1],
        [0.2, 0.6, 0.2],
        [0.1, 0.7, 0.2],
        [0.1, 0.2, 0.7],
    ]


def test_metrics_match_hand_computed_multiclass_values(arithmetic_fixture):
    labels, probabilities = arithmetic_fixture
    report = evaluate_synthetic(
        labels, probabilities, options=["a", "b", "c"], ece_bins=2
    )
    assert report["confusion_matrix"] == [[1, 0, 0], [0, 1, 0], [0, 1, 1]]
    assert report["accuracy"] == 0.75
    assert [row["recall"] for row in report["per_class"]] == [1, 1, 0.5]
    assert report["macro_f1"] == pytest.approx(7 / 9)
    assert report["nll"] == pytest.approx(-np.log([0.8, 0.6, 0.2, 0.7]).mean())
    assert report["brier"] == pytest.approx(0.395)
    assert report["ece"] == pytest.approx(0.05)
    assert report["ece_bins"][0]["count"] == 0
    assert report["ece_bins"][0]["accuracy"] is None
    assert (
        report["synthetic"]
        and not report["training_approved"]
        and not report["task_quality_claim"]
    )
    json.dumps(report, allow_nan=False)


def test_coverage_keeps_confidence_ties_together(arithmetic_fixture):
    labels, probabilities = arithmetic_fixture
    report = evaluate_synthetic(labels, probabilities, options=["a", "b", "c"])
    curve = report["coverage_curve"]
    assert [row["accepted"] for row in curve] == [0, 1, 3, 4]
    assert [row["coverage"] for row in curve] == [0, 0.25, 0.75, 1]
    assert [row["threshold"] for row in curve] == [None, 0.8, 0.7, 0.6]
    assert curve[2]["risk"] == pytest.approx(1 / 3)
    assert curve[-1]["risk"] == 0.25
    assert curve[0]["accuracy"] is None and curve[0]["risk"] is None


def test_absent_classes_and_zero_probability_are_not_hidden():
    report = evaluate_synthetic([0], [[0, 1]], options=["a", "b"])
    assert report["nll"] is None and report["nll_is_infinite"]
    assert report["zero_target_probability_count"] == 1
    assert report["brier"] == 2
    assert report["missing_classes"] == ["b"]
    assert report["per_class"][1]["recall"] is None
    assert report["macro_f1"] == 0
    assert report["ece"] == 1
    json.dumps(report, allow_nan=False)


def test_perfect_predictions_include_missing_options_in_macro_f1():
    report = evaluate_synthetic([0, 0], [[1, 0], [1, 0]], options=["a", "b"])
    assert report["accuracy"] == 1 and report["macro_f1"] == 0.5
    assert report["nll"] == 0 and report["brier"] == 0 and report["ece"] == 0
    assert report["per_class"][1]["precision"] is None
    assert [row["accepted"] for row in report["coverage_curve"]] == [0, 2]


@pytest.mark.parametrize(
    ("confidence", "bins", "expected_bin"),
    [(0.58, 50, 29), (0.29, 100, 29), (0.6, 10, 6), (1.0, 10, 9)],
)
def test_ece_internal_edges_are_left_closed(confidence, bins, expected_bin):
    probabilities = [[confidence, *([(1 - confidence) / 3] * 3)]]
    report = evaluate_synthetic(
        [0], probabilities, options=["a", "b", "c", "d"], ece_bins=bins
    )
    assert report["ece_bins"][expected_bin]["count"] == 1
    assert sum(row["count"] for row in report["ece_bins"]) == 1


def test_option_permutation_preserves_scalar_metrics_and_inputs(arithmetic_fixture):
    labels, probabilities = arithmetic_fixture
    original = deepcopy(probabilities)
    first = evaluate_synthetic(labels, probabilities, options=["a", "b", "c"])
    permutation = [2, 0, 1]
    permuted = np.asarray(probabilities)[:, permutation]
    remapped = [permutation.index(label) for label in labels]
    second = evaluate_synthetic(remapped, permuted, options=["c", "a", "b"])
    for name in ("accuracy", "macro_f1", "nll", "brier", "ece"):
        assert first[name] == pytest.approx(second[name])
    assert first["input_sha256"] != second["input_sha256"]
    assert probabilities == original
    tied = evaluate_synthetic([1], [[0.5, 0.5]], options=["a", "b"])
    assert tied["confusion_matrix"] == [[0, 0], [1, 0]]


@pytest.mark.parametrize(
    "defect",
    [
        "empty",
        "labels_shape",
        "float_label",
        "bool_label",
        "label_range",
        "columns",
        "nan",
        "negative",
        "sum",
        "options",
        "bins",
    ],
)
def test_invalid_metric_inputs_are_rejected(defect):
    labels, probabilities, options, bins = [0], [[0.8, 0.2]], ["a", "b"], 10
    if defect == "empty":
        labels, probabilities = [], []
    elif defect == "labels_shape":
        labels = [[0]]
    elif defect == "float_label":
        labels = [0.0]
    elif defect == "bool_label":
        labels = [False]
    elif defect == "label_range":
        labels = [2]
    elif defect == "columns":
        probabilities = [[1.0]]
    elif defect == "nan":
        probabilities = [[float("nan"), 0.2]]
    elif defect == "negative":
        probabilities = [[1.2, -0.2]]
    elif defect == "sum":
        probabilities = [[0.7, 0.2]]
    elif defect == "options":
        options = ["a", "a"]
    else:
        bins = True
    with pytest.raises(ValueError):
        evaluate_synthetic(labels, probabilities, options=options, ece_bins=bins)


@pytest.fixture
def split_fixture():
    return {
        "schema": "micro-classifier/synthetic-splits/1",
        "synthetic": True,
        "training_approved": False,
        "partitions": {
            purpose: [
                {
                    "sample_id": f"fixture/{purpose}",
                    "input_sha256": hashlib.sha256(purpose.encode()).hexdigest(),
                    "groups": {
                        name: f"{purpose}/{name}"
                        for name in ("source", "episode", "template")
                    },
                }
            ]
            for purpose in PURPOSES
        },
    }


def test_split_checks_are_deterministic_nonmutating_and_not_real_locks(split_fixture):
    original = deepcopy(split_fixture)
    report = validate_synthetic_splits(split_fixture)
    assert report == validate_synthetic_splits(
        split_fixture, expected_sha256=report["manifest_sha256"]
    )
    assert set(report["partitions"]) == {
        "train",
        "development",
        "quantization_calibration",
        "confidence_calibration",
        "test",
    }
    assert all(row["samples"] == 1 for row in report["partitions"].values())
    assert not report["locked_task_splits"] and not report["group_identities_verified"]
    assert not report["training_approved"] and report["synthetic"]
    assert split_fixture == original
    json.dumps(report, allow_nan=False)


def test_groups_and_duplicate_inputs_can_repeat_only_within_one_partition(
    split_fixture,
):
    repeated = deepcopy(split_fixture["partitions"]["train"][0])
    repeated["sample_id"] = "extra"
    split_fixture["partitions"]["train"].append(repeated)
    counts = validate_synthetic_splits(split_fixture)["partitions"]["train"]
    assert counts == {
        "samples": 2,
        "unique_inputs": 1,
        "groups": {"source": 1, "episode": 1, "template": 1},
    }


@pytest.mark.parametrize(
    "defect",
    [
        "sample",
        "input",
        "source",
        "episode",
        "template",
        "missing_purpose",
        "unknown_purpose",
        "empty",
        "scope",
        "training",
        "hash",
        "groups",
    ],
)
def test_split_overlap_and_invalid_declarations_are_rejected(split_fixture, defect):
    train = split_fixture["partitions"]["train"][0]
    test = split_fixture["partitions"]["test"][0]
    if defect == "sample":
        test["sample_id"] = train["sample_id"]
    elif defect == "input":
        test["input_sha256"] = train["input_sha256"]
    elif defect in ("source", "episode", "template"):
        test["groups"][defect] = train["groups"][defect]
    elif defect == "missing_purpose":
        del split_fixture["partitions"]["confidence_calibration"]
    elif defect == "unknown_purpose":
        split_fixture["partitions"]["extra"] = []
    elif defect == "empty":
        split_fixture["partitions"]["test"] = []
    elif defect == "scope":
        split_fixture["synthetic"] = False
    elif defect == "training":
        split_fixture["training_approved"] = True
    elif defect == "hash":
        test["input_sha256"] = "bad-hash"
    else:
        del test["groups"]["episode"]
    with pytest.raises(ValueError):
        validate_synthetic_splits(split_fixture)


def test_expected_manifest_hash_detects_changes(split_fixture):
    checksum = validate_synthetic_splits(split_fixture)["manifest_sha256"]
    split_fixture["partitions"]["test"][0]["groups"]["template"] = "changed"
    with pytest.raises(ValueError, match="manifest hash"):
        validate_synthetic_splits(split_fixture, expected_sha256=checksum)


def test_synthetic_smoke_cli_records_arithmetic_and_refuses_overwrite(
    tmp_path, monkeypatch, capsys
):
    output = tmp_path / "report.json"
    monkeypatch.setattr("sys.argv", ["evaluation", "--output", str(output)])
    main()
    summary = json.loads(capsys.readouterr().out)
    report = json.loads(output.read_text())
    assert summary["synthetic"] and not summary["task_quality_claim"]
    assert report["metrics"]["brier"] == pytest.approx(0.395)
    assert report["metrics"]["macro_f1"] == pytest.approx(7 / 9)
    assert report["live_teacher_calls"] == 0 and report["training_runs"] == 0
    assert not report["locked_task_splits"]
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        main()
    assert output.read_bytes() == original
