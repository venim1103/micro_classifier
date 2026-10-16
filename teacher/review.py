"""CPU-only blind review preparation; no task labels or real reviews are enabled."""

import argparse
import hashlib
import json
import re
from copy import deepcopy
from dataclasses import fields
from pathlib import Path

import numpy as np

from interface.protocol import State
from sim.rover import Config
from teacher.label_pipeline import (
    canonical,
    digest,
    draft_catalogue,
    episode_requests,
    prepare_request,
    validate_request,
)

PACKET_SCHEMA = "micro-classifier/blind-review-packet/1"
ALLOWED_USE = "unreviewed_blind_review_preparation_only"
OBSERVATION_FIELDS = {
    "tick",
    "tof_m",
    "tof_valid",
    "tof_age_s",
    "tof_sample_tick",
    "history_ego",
    "history_tof_m",
    "history_tof_valid",
    "history_valid",
}


def review_questions():
    return [
        {key: deepcopy(question[key]) for key in ("id", "name", "type", "options")}
        for question in draft_catalogue()["questions"]
    ]


def blank_assessments():
    return {
        row["name"]: {"label": None, "abstention_reason": None, "notes": ""}
        for row in review_questions()
    }


def make_review_packet(request):
    validate_request(request)
    state = json.loads(request["state"])
    if canonical(state) != request["state"]:
        raise ValueError("review requires the unchanged canonical full state")
    packet = {
        "schema": PACKET_SCHEMA,
        "allowed_use": ALLOWED_USE,
        "review_status": "unreviewed",
        "training_approved": False,
        "task_labels_approved": False,
        "split_locked": False,
        "state": state,
        "state_sha256": hashlib.sha256(request["state"].encode()).hexdigest(),
        "source": deepcopy(request["source"]),
        "input_provenance": deepcopy(request["provenance"]),
        "grouping": {
            "episode_sha256": request["source"]["episode_sha256"],
            "source_family": None,
            "template_family": None,
            "reviewed": False,
            "partition": None,
        },
        "questions": review_questions(),
        "assessments": blank_assessments(),
    }
    packet["packet_id"] = digest(packet)
    validate_review_packet(packet)
    return packet


def validate_review_packet(packet):
    expected_keys = {
        "schema",
        "allowed_use",
        "review_status",
        "training_approved",
        "task_labels_approved",
        "split_locked",
        "state",
        "state_sha256",
        "source",
        "input_provenance",
        "grouping",
        "questions",
        "assessments",
        "packet_id",
    }
    if not isinstance(packet, dict) or set(packet) != expected_keys:
        raise ValueError("unexpected review packet fields")
    if (
        packet["schema"] != PACKET_SCHEMA
        or packet["allowed_use"] != ALLOWED_USE
        or packet["review_status"] != "unreviewed"
        or any(
            packet[name] is not False
            for name in ("training_approved", "task_labels_approved", "split_locked")
        )
    ):
        raise ValueError("review preparation scope cannot be promoted")
    if canonical(packet["questions"]) != canonical(review_questions()) or canonical(
        packet["assessments"]
    ) != canonical(blank_assessments()):
        raise ValueError("review packets must contain only blank catalogue assessments")
    state = packet["state"]
    if (
        not isinstance(state, dict)
        or set(state) != {"schema", "axes", "units", "host_state", "module_observation"}
        or state["schema"] != "micro-classifier/sim-teacher-state/1"
        or state["axes"] != "FLU"
        or state["units"] != "metres, seconds, radians"
        or set(state["host_state"]) != {field.name for field in fields(State)}
        or set(state["module_observation"]) != OBSERVATION_FIELDS
    ):
        raise ValueError("review state contains unsupported or privileged fields")
    if hashlib.sha256(canonical(state).encode()).hexdigest() != packet["state_sha256"]:
        raise ValueError("review state hash mismatch")
    source = packet["source"]
    if (
        not isinstance(source, dict)
        or set(source) != {"episode_sha256", "line", "tick", "frame_origin"}
        or not isinstance(source["episode_sha256"], str)
        or re.fullmatch(r"[a-f0-9]{64}", source["episode_sha256"]) is None
        or type(source["line"]) is not int
        or source["line"] < 1
        or type(source["tick"]) is not int
        or source["tick"] < 0
        or source["tick"] != state["module_observation"]["tick"]
        or source["frame_origin"] not in ("embedded", "synthesized_from_observation")
    ):
        raise ValueError("review source provenance is invalid")
    if canonical(packet["grouping"]) != canonical(
        {
            "episode_sha256": source["episode_sha256"],
            "source_family": None,
            "template_family": None,
            "reviewed": False,
            "partition": None,
        }
    ):
        raise ValueError("family/grouping review and split assignments remain pending")
    provenance = packet["input_provenance"]
    hashes = {
        "renderer_sha256",
        "catalogue_sha256",
        "config_sha256",
        "state_frame_sha256",
    }
    if (
        not isinstance(provenance, dict)
        or set(provenance) != hashes | {"config"}
        or any(
            not isinstance(provenance[key], str)
            or re.fullmatch(r"[a-f0-9]{64}", provenance[key]) is None
            for key in hashes
        )
        or provenance["catalogue_sha256"] != digest(draft_catalogue())
        or provenance["config_sha256"] != digest(provenance["config"])
    ):
        raise ValueError("review input provenance is invalid")
    if packet["packet_id"] != digest(
        {key: value for key, value in packet.items() if key != "packet_id"}
    ):
        raise ValueError("review packet identity mismatch")
    try:
        observation = deepcopy(state["module_observation"])
        observation["schema"] = "micro-classifier/sim-observation/1"
        observation["time_s"] = state["host_state"]["timestamp_us"] / 1_000_000
        for name in (
            "tof_m",
            "tof_valid",
            "history_ego",
            "history_tof_m",
            "history_tof_valid",
            "history_valid",
        ):
            observation[name] = np.asarray(observation[name])
        observation["ego"] = observation["history_ego"][-1]
        observation["goal_body_m"] = observation["ego"][2:]
        rebuilt = prepare_request(observation, config=Config(**provenance["config"]))
        if rebuilt["state"] != canonical(state) or rebuilt["provenance"] != provenance:
            raise ValueError("rendered state/provenance mismatch")
    except (ValueError, TypeError, KeyError, IndexError) as error:
        raise ValueError("review state failed renderer validation") from error


def normalize_review_fixture(packet, fixture, *, fake_test_only=False):
    if fake_test_only is not True:
        raise ValueError("only explicit fake-review format tests are enabled")
    validate_review_packet(packet)
    if (
        not isinstance(fixture, dict)
        or set(fixture) != {"schema", "packet_id", "reviewer", "assessments"}
        or fixture["schema"] != "micro-classifier/fake-review-fixture/1"
        or fixture["packet_id"] != packet["packet_id"]
    ):
        raise ValueError("fake review schema or packet identity mismatch")
    reviewer = fixture["reviewer"]
    if (
        not isinstance(reviewer, dict)
        or set(reviewer) != {"kind", "id"}
        or reviewer["kind"] != "fake_test_only"
        or not isinstance(reviewer["id"], str)
        or re.fullmatch(r"test/[a-zA-Z0-9_.-]+", reviewer["id"]) is None
    ):
        raise ValueError("real reviewer identities are not enabled")
    assessments = fixture["assessments"]
    if not isinstance(assessments, dict) or set(assessments) != set(
        packet["assessments"]
    ):
        raise ValueError("fake review must cover the exact catalogue")
    for question in packet["questions"]:
        row = assessments[question["name"]]
        if (
            not isinstance(row, dict)
            or set(row) != {"label", "abstention_reason", "notes"}
            or not isinstance(row["notes"], str)
        ):
            raise ValueError("invalid fake review assessment fields")
        if row["label"] is None:
            if row["abstention_reason"] not in (
                "insufficient_observation",
                "policy_undefined",
                "reviewer_disagreement",
            ):
                raise ValueError("fake abstention requires an explicit reason")
        elif (
            question["name"] == "mode"
            or type(row["label"]) is not str
            or row["label"] not in question["options"]
            or row["abstention_reason"] is not None
        ):
            raise ValueError(
                "mode remains unlabeled; other fake labels must match options"
            )
    canonical(fixture)
    return {
        **deepcopy(fixture),
        "synthetic": True,
        "allowed_use": "fake_review_format_tests_only",
        "training_approved": False,
        "reviewed_dataset": False,
    }


def prepare_review(episodes, *, limit=8):
    episodes = list(episodes)
    if (
        type(limit) is not int
        or limit < 1
        or not episodes
        or len(episodes) * limit > 32
    ):
        raise ValueError(
            "review preparation requires 1-32 records across nonempty episodes"
        )
    packets, seen_sources = [], set()
    for episode in episodes:
        requests = list(episode_requests(episode, limit=limit))
        if not requests:
            raise ValueError("review source contains no observations")
        source = requests[0]["source"]["episode_sha256"]
        if source in seen_sources:
            raise ValueError("duplicate source episodes are not separate review groups")
        seen_sources.add(source)
        packets.extend(make_review_packet(prepared) for prepared in requests)
    return {
        "schema": "micro-classifier/blind-review-bundle/1",
        "allowed_use": ALLOWED_USE,
        "review_status": "unreviewed",
        "training_approved": False,
        "task_labels_approved": False,
        "locked_task_splits": False,
        "actual_annotations": 0,
        "mode_labels": 0,
        "teacher_calls": 0,
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "packet_count": len(packets),
        "source_episode_count": len(seen_sources),
        "family_group_review_complete": False,
        "packets": packets,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", type=Path, action="append", required=True)
    parser.add_argument(
        "--limit", type=int, default=8, help="maximum records per episode; 32 total"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    paths = [args.output, *([args.report] if args.report is not None else [])]
    if len({path.resolve() for path in paths}) != len(paths):
        raise ValueError("packet output and report must be separate files")
    for path in paths:
        if path.exists():
            raise FileExistsError(path)
    bundle = prepare_review(args.episode, limit=args.limit)
    raw = json.dumps(bundle, indent=2, allow_nan=False) + "\n"
    report = {key: value for key, value in bundle.items() if key != "packets"}
    report.update(
        schema="micro-classifier/blind-review-preparation-report/1",
        packet_file_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        full_history_packet_count=sum(
            all(packet["state"]["module_observation"]["history_valid"])
            for packet in bundle["packets"]
        ),
        packet_evidence=[
            {key: packet[key] for key in ("packet_id", "source", "state_sha256")}
            for packet in bundle["packets"]
        ],
        limitations=[
            "Blank preparation packets, not annotations or an approved task dataset.",
            "Teacher/proxy suggestions and privileged fields excluded; hashes are not anonymity.",
            "Known episode identity is retained; source/template families and partitions unresolved.",
            "Content hashes and test identities are consistency checks, not reviewer attestation.",
            "Record limits bound rendered observations, not source-file memory or full-log validation.",
        ],
    )
    writes = [(args.output, raw)]
    if args.report is not None:
        writes.append(
            (args.report, json.dumps(report, indent=2, allow_nan=False) + "\n")
        )
    for path, content in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            stream.write(content)
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "packet_evidence"},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
