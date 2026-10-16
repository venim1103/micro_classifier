"""Simulation request/cache tooling; only injected fake teachers are enabled."""

import argparse
import hashlib
import json
import math
import re
import sqlite3
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import numpy as np

from interface.protocol import decode_state, encode_state
from sim.labels import digest, draft_catalogue, draft_labels
from sim.rover import Config, state_from_observation


def prepare_request(observation, *, config=None, state_frame=None):
    config = Config() if config is None else config
    draft_labels(observation, config)
    expected_frame = encode_state(state_from_observation(observation))
    frame = expected_frame if state_frame is None else bytes(state_frame)
    state = decode_state(frame)
    if frame != expected_frame:
        raise ValueError("host frame and simulation observation disagree")
    if not np.array_equal(observation["ego"][2:], observation["goal_body_m"]):
        raise ValueError("ego and body-frame goal disagree")
    shapes = {
        "history_ego": (config.history_ticks, 4),
        "history_tof_m": (config.history_ticks, 8, 8),
        "history_tof_valid": (config.history_ticks, 8, 8),
        "history_valid": (config.history_ticks,),
    }
    history = {}
    for name, shape in shapes.items():
        if name not in observation:
            raise ValueError(f"missing {name}")
        values = np.asarray(observation[name])
        boolean = name in ("history_tof_valid", "history_valid")
        kinds = "b" if boolean else "iuf"
        if values.shape != shape or values.dtype.kind not in kinds:
            raise ValueError(f"invalid {name} shape or dtype")
        if not np.isfinite(values).all():
            raise ValueError(f"non-finite {name}")
        history[name] = values
    if not history["history_valid"][-1]:
        raise ValueError("current history slot must be valid")
    for historical, current in (
        ("history_ego", "ego"),
        ("history_tof_m", "tof_m"),
        ("history_tof_valid", "tof_valid"),
    ):
        if not np.array_equal(history[historical][-1], observation[current]):
            raise ValueError("current observation and history disagree")
    if (history["history_tof_m"][~history["history_tof_valid"]] != 0).any():
        raise ValueError("masked history ranges must be zero")
    maximum = max(config.max_range, float(np.float32(config.max_range)))
    if (history["history_tof_m"] < 0).any() or (
        history["history_tof_m"] > maximum
    ).any():
        raise ValueError("history ranges exceed simulation limits")
    missing = ~history["history_valid"]
    if any(
        (history[name][missing] != 0).any()
        for name in shapes
        if name != "history_valid"
    ):
        raise ValueError("unavailable history must be zero and masked")
    catalogue = draft_catalogue()
    mode = next(row for row in catalogue["questions"] if row["name"] == "mode")
    payload = {
        "schema": "micro-classifier/sim-teacher-state/1",
        "axes": "FLU",
        "units": "metres, seconds, radians",
        "host_state": asdict(state),
        "module_observation": {
            "tick": observation["tick"],
            "tof_m": np.asarray(observation["tof_m"]).tolist(),
            "tof_valid": np.asarray(observation["tof_valid"]).tolist(),
            "tof_age_s": float(observation["tof_age_s"]),
            "tof_sample_tick": observation["tof_sample_tick"],
            **{name: value.tolist() for name, value in history.items()},
        },
    }
    return {
        "schema": "micro-classifier/teacher-request/1",
        "state": json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ),
        "questions": {
            "mode": {
                "type": "choice",
                "instructions": "Which high-level rover behavior mode best matches the observed goal-reaching state?",
                "criteria": dict.fromkeys(mode["options"]),
            }
        },
        "option_order": {"mode": mode["options"]},
        "provenance": {
            "config": asdict(config),
            "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "catalogue_sha256": digest(catalogue),
            "config_sha256": digest(asdict(config)),
            "state_frame_sha256": hashlib.sha256(frame).hexdigest(),
        },
        "allowed_use": "fake_teacher_pipeline_tests_only",
        "training_approved": False,
        "token_budget_verified": False,
    }


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


COMPACT_SCHEMA = "micro-classifier/sim-teacher-state-row-draft/1"
FLOAT32_COMPACT_SCHEMA = "micro-classifier/sim-teacher-state-row-f32-draft/1"
ROW_FIELDS = {
    "tof_m": 1,
    "tof_valid": 1,
    "history_ego": 1,
    "history_tof_m": 2,
    "history_tof_valid": 2,
}
ROW_ENCODING = (
    "In module_observation, tof_m, tof_valid and history_ego contain zero-based "
    "row_table indexes. history_tof_m and history_tof_valid contain lists of "
    "row indexes, one list per history slot. Expand each index to its complete "
    "row. Outer order and masks are unchanged; last history slot is current. "
    "All original numbers and booleans are preserved without rounding."
)
FLOAT32_ROW_ENCODING = ROW_ENCODING + (
    ' A row encoded as {"f32":[decimal strings]} contains IEEE-754 binary32 '
    "values: parse those strings as binary32, then promote exactly to the "
    "original float. Other rows are literal JSON. No binary precision is changed."
)


def _float32_row_draft(row):
    if not row or any(type(value) is not float for value in row):
        return deepcopy(row)
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        values = np.asarray(row, dtype=np.float32)
    if not np.isfinite(values).all() or canonical(
        [float(value) for value in values]
    ) != canonical(row):
        return deepcopy(row)
    return {
        "f32": [
            min(
                (
                    np.format_float_positional(value, unique=True, trim="-"),
                    np.format_float_scientific(
                        value, unique=True, trim="-", exp_digits=1
                    ),
                ),
                key=len,
            )
            for value in values
        ]
    }


def expand_compact_state(state, *, expected_sha256=None):
    payload = json.loads(state)
    encodings = {
        COMPACT_SCHEMA: ROW_ENCODING,
        FLOAT32_COMPACT_SCHEMA: FLOAT32_ROW_ENCODING,
    }
    if (
        payload.get("schema") not in encodings
        or payload.get("row_encoding") != encodings[payload["schema"]]
    ):
        raise ValueError("unsupported compact state draft")
    rows = payload.pop("row_table")
    if not isinstance(rows, list):
        raise TypeError("row table must contain arrays")
    decoded_rows = []
    for row in rows:
        if isinstance(row, list):
            decoded_rows.append(row)
        elif (
            payload["schema"] == FLOAT32_COMPACT_SCHEMA
            and isinstance(row, dict)
            and set(row) == {"f32"}
            and isinstance(row["f32"], list)
            and len(row["f32"]) in (4, 8)
            and all(isinstance(text, str) for text in row["f32"])
        ):
            with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                values = np.asarray(row["f32"], dtype=np.float32)
            if not np.isfinite(values).all():
                raise ValueError("typed rows require finite float32 values")
            decoded_rows.append([float(value) for value in values])
        else:
            raise ValueError("invalid literal or typed row")

    def expand(value, depth):
        if depth:
            if not isinstance(value, list):
                raise ValueError("row references require nested arrays")
            return [expand(item, depth - 1) for item in value]
        if type(value) is not int or not 0 <= value < len(rows):
            raise ValueError("invalid row reference")
        return deepcopy(decoded_rows[value])

    for name, depth in ROW_FIELDS.items():
        payload["module_observation"][name] = expand(
            payload["module_observation"][name], depth
        )
    payload.pop("row_encoding")
    payload["schema"] = "micro-classifier/sim-teacher-state/1"
    expanded = canonical(payload)
    if (
        expected_sha256 is not None
        and hashlib.sha256(expanded.encode()).hexdigest() != expected_sha256
    ):
        raise ValueError("reconstructed state differs from its original identity")
    return expanded


def compact_request_draft(request, *, float32_rows=False):
    validate_request(request)
    if type(float32_rows) is not bool:
        raise TypeError("float32_rows must be a boolean")
    original = request["state"]
    payload = json.loads(original)
    if (
        payload.get("schema") != "micro-classifier/sim-teacher-state/1"
        or canonical(payload) != original
    ):
        raise ValueError("compact draft requires the canonical full-state renderer")
    rows = []
    indexes = {}

    def intern(value, depth):
        if depth:
            return [intern(item, depth - 1) for item in value]
        key = canonical(value)
        if key not in indexes:
            indexes[key] = len(rows)
            rows.append(deepcopy(value))
        return indexes[key]

    for name, depth in ROW_FIELDS.items():
        payload["module_observation"][name] = intern(
            payload["module_observation"][name], depth
        )
    schema = FLOAT32_COMPACT_SCHEMA if float32_rows else COMPACT_SCHEMA
    payload["schema"] = schema
    payload["row_table"] = (
        [_float32_row_draft(row) for row in rows] if float32_rows else rows
    )
    payload["row_encoding"] = FLOAT32_ROW_ENCODING if float32_rows else ROW_ENCODING
    result = deepcopy(request)
    result["state"] = canonical(payload)
    original_hash = hashlib.sha256(original.encode()).hexdigest()
    if expand_compact_state(result["state"], expected_sha256=original_hash) != original:
        raise ValueError("compact state failed exact reconstruction")
    result["representation"] = {
        "schema": schema,
        "review_status": "unreviewed_draft",
        "live_use_approved": False,
        "original_state_sha256": original_hash,
        "codec_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    return result


def validate_identity(identity):
    required = {"kind", "model_id", "revision", "settings", "artifact_sha256"}
    if not isinstance(identity, dict) or set(identity) != required:
        raise ValueError(
            "teacher identity requires kind, model, revision, settings and hash"
        )
    if identity["kind"] != "fake_test_only" or not identity["model_id"].startswith(
        "test/"
    ):
        raise ValueError("only explicit fake-test teacher identities are enabled")
    if not re.fullmatch(r"[a-f0-9]{40}", identity["revision"]):
        raise ValueError("teacher revision must be a full 40-character identity")
    if not re.fullmatch(r"[a-f0-9]{64}", identity["artifact_sha256"]):
        raise ValueError("teacher artifact SHA-256 is required")
    if not isinstance(identity["settings"], dict):
        raise TypeError("teacher settings must be a dictionary")
    canonical(identity)


def validate_request(request):
    if request.get("schema") != "micro-classifier/teacher-request/1":
        raise ValueError("unsupported teacher request schema")
    if (
        request.get("allowed_use") != "fake_teacher_pipeline_tests_only"
        or request.get("training_approved") is not False
    ):
        raise ValueError("request is not restricted to fake-teacher tests")
    if set(request["questions"]) != {"mode"}:
        raise ValueError("only the human-review mode supplement is supported")
    question = request["questions"]["mode"]
    options = request["option_order"]["mode"]
    expected = next(
        row["options"]
        for row in draft_catalogue()["questions"]
        if row["name"] == "mode"
    )
    if (
        question["type"] != "choice"
        or len(options) != len(expected)
        or set(options) != set(expected)
    ):
        raise ValueError("mode type or option identities differ from the catalogue")
    if list(question["criteria"]) != options:
        raise ValueError("criteria and explicit option order disagree")
    canonical(request)


def normalize_response(request, response):
    if (
        not isinstance(response, dict)
        or not isinstance(response.get("answers"), dict)
        or set(response["answers"]) != {"mode"}
    ):
        raise ValueError("teacher response must answer exactly mode")
    answer = response["answers"]["mode"]
    options = request["option_order"]["mode"]
    if (
        not isinstance(answer, dict)
        or "error" in answer
        or answer.get("type") != "choice"
    ):
        raise ValueError("teacher rejected mode or returned the wrong type")
    probabilities = answer.get("probabilities", {})
    if not isinstance(probabilities, dict) or set(probabilities) != set(options):
        raise ValueError("teacher option identities differ")
    values = [probabilities[option] for option in options]
    if any(
        type(value) not in (int, float)
        or not math.isfinite(value)
        or not 0 <= value <= 1
        for value in values
    ):
        raise ValueError("teacher probabilities must be finite numeric values in [0,1]")
    if not math.isclose(sum(values), 1, rel_tol=0, abs_tol=1e-6):
        raise ValueError("teacher probabilities must sum to one")
    canonical(response)
    return {
        "mode": {
            "type": "choice",
            "options": options,
            "probabilities": values,
            "selected_index": max(range(len(values)), key=values.__getitem__),
            "human_review_required": True,
        }
    }


class LabelCache:
    """Single-writer SQLite cache; each validated record commits independently."""

    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        try:
            version = self.connection.execute("PRAGMA user_version").fetchone()[0]
            tables = self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            if version == 0 and not tables:
                with self.connection:
                    self.connection.execute(
                        "CREATE TABLE labels (cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL)"
                    )
                    self.connection.execute("PRAGMA user_version=1")
            elif version != 1 or tables != [("labels",)]:
                raise ValueError("unrecognized cache schema; refusing to modify it")
            columns = self.connection.execute("PRAGMA table_info(labels)").fetchall()
            if [row[1] for row in columns] != ["cache_key", "payload", "sha256"]:
                raise ValueError("cache columns differ from the supported schema")
        except Exception:
            self.connection.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.connection.close()

    def get(self, key):
        row = self.connection.execute(
            "SELECT payload, sha256 FROM labels WHERE cache_key=?", (key,)
        ).fetchone()
        if row is None:
            return None
        payload, checksum = row
        if hashlib.sha256(payload.encode()).hexdigest() != checksum:
            raise ValueError("cached record checksum mismatch")
        record = json.loads(payload)
        identity = {
            "request": record["request"],
            "teacher": record["teacher"],
            "pipeline_sha256": record["source_sha256"],
        }
        if record.get("cache_key") != key or digest(identity) != key:
            raise ValueError("cached request identity mismatch")
        if (
            record.get("schema") != "micro-classifier/fake-teacher-record/1"
            or record.get("training_approved") is not False
            or record.get("synthetic") is not True
        ):
            raise ValueError("cached record has invalid scope or schema")
        validate_identity(record["teacher"])
        validate_request(record["request"])
        if (
            normalize_response(record["request"], record["raw_response"])
            != record["answers"]
        ):
            raise ValueError("cached normalized answers disagree with raw response")
        return record

    def put(self, record):
        payload = json.dumps(record, separators=(",", ":"), allow_nan=False)
        checksum = hashlib.sha256(payload.encode()).hexdigest()
        with self.connection:
            existing = self.get(record["cache_key"])
            if existing is not None and existing != record:
                raise ValueError("conflicting cache record; refusing to overwrite")
            self.connection.execute(
                "INSERT OR IGNORE INTO labels VALUES (?, ?, ?)",
                (record["cache_key"], payload, checksum),
            )


def label_requests(requests, *, teacher, identity, cache):
    validate_identity(identity)
    identity = deepcopy(identity)
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for request in requests:
        validate_request(request)
        request = deepcopy(request)
        key = digest(
            {"request": request, "teacher": identity, "pipeline_sha256": source_hash}
        )
        record = cache.get(key)
        hit = record is not None
        if record is None:
            response = teacher.system_one(
                state=request["state"], questions=deepcopy(request["questions"])
            )
            record = {
                "schema": "micro-classifier/fake-teacher-record/1",
                "cache_key": key,
                "request": request,
                "teacher": deepcopy(identity),
                "answers": normalize_response(request, response),
                "raw_response": deepcopy(response),
                "synthetic": True,
                "training_approved": False,
                "source_sha256": source_hash,
            }
            cache.put(record)
        yield {"cache_hit": hit, "record": record}


def episode_requests(path, *, limit=None):
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("request limit must be a positive integer")
    raw = Path(path).read_bytes()
    source_hash = hashlib.sha256(raw).hexdigest()
    lines = raw.splitlines()
    if not lines:
        raise ValueError("episode is empty")
    metadata = json.loads(lines[0])
    if (
        metadata.get("schema") != "micro-classifier/sim-episode/1"
        or metadata.get("kind") != "metadata"
    ):
        raise ValueError("episode must start with versioned simulation metadata")
    config = Config(**metadata["config"])
    wire = "wire_contract" in metadata
    count = 0
    for line_number, line in enumerate(lines, 1):
        record = json.loads(line)
        if "observation" not in record:
            if record.get("kind") != "summary":
                raise ValueError("unexpected episode record without observation")
            continue
        observation = record["observation"]
        if observation["tick"] != count:
            raise ValueError("episode observations must be contiguous from reset")
        encoded = record.get("state_frame_hex")
        if wire and encoded is None:
            raise ValueError("wire episode is missing an embedded host frame")
        frame = bytes.fromhex(encoded) if encoded is not None else None
        request = prepare_request(observation, config=config, state_frame=frame)
        request["source"] = {
            "episode_sha256": source_hash,
            "line": line_number,
            "tick": observation["tick"],
            "frame_origin": "embedded"
            if encoded is not None
            else "synthesized_from_observation",
        }
        yield request
        count += 1
        if limit is not None and count >= limit:
            break


def plan_episode(path, *, limit=8):
    requests = list(episode_requests(path, limit=limit))
    return {
        "schema": "micro-classifier/teacher-request-plan/1",
        "allowed_use": "fake_teacher_pipeline_tests_only",
        "training_approved": False,
        "live_teacher_calls": 0,
        "token_budget_verified": False,
        "request_count": len(requests),
        "max_state_characters": max(
            (len(request["state"]) for request in requests), default=0
        ),
        "requests": requests,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Prepare bounded request plans only; no model execution."
    )
    parser.add_argument("--episode", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    plan = plan_episode(args.episode, limit=args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(plan, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {name: value for name, value in plan.items() if name != "requests"},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
