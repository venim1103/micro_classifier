"""Provisional rover wire contract v0, with explicit little-endian fields."""

import argparse
import math
import struct
import zlib
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from pathlib import Path

MAGIC = b"MC"
PROTOCOL_VERSION = 0
SCHEMA_VERSION = 0
PROFILE_ID = 1
PROFILE_VERSION = 0
UINT32_MAX = 0xFFFFFFFF

HEADER_FIELDS = (
    ("magic", "2s"),
    ("protocol_version", "B"),
    ("kind", "B"),
    ("payload_size", "H"),
    ("schema_version", "H"),
    ("profile_id", "H"),
    ("profile_version", "H"),
    ("sequence", "I"),
    ("timestamp_us", "I"),
)
STATE_FIELDS = (
    ("validity", "H"),
    ("task_id", "H"),
    ("ages_us", "5I"),
    ("velocity_m_s", "3f"),
    ("angular_velocity_rad_s", "3f"),
    ("goal_m", "3f"),
    ("battery_fraction", "f"),
    ("faults", "I"),
)
HEADER = struct.Struct("<" + "".join(code for _, code in HEADER_FIELDS))
STATE = struct.Struct("<" + "".join(code for _, code in STATE_FIELDS))
CRC = struct.Struct("<I")
DECISION_FIELDS = (
    ("latency_us", "I"),
    ("status", "H"),
    ("model_version", "H"),
    ("catalogue_version", "H"),
    ("answer_mask", "H"),
)
ANSWER_FIELDS = (
    ("question_id", "B"),
    ("answer_type", "B"),
    ("selected", "B"),
    ("option_count", "B"),
    ("confidence", "f"),
)
DECISION = struct.Struct("<" + "".join(code for _, code in DECISION_FIELDS))
ANSWER = struct.Struct("<" + "".join(code for _, code in ANSWER_FIELDS))
CATALOGUE_VERSION = 0


class Kind(IntEnum):
    STATE = 1
    DECISION = 2


class Status(IntEnum):
    OK = 0
    REJECT_LOW_CONFIDENCE = 1
    REJECT_STALE_INPUT = 2
    REJECT_OUT_OF_DOMAIN = 3
    REJECT_UNSUPPORTED_SCHEMA = 4
    FAULT = 5


class Validity(IntFlag):
    VELOCITY = 1
    ANGULAR_VELOCITY = 2
    GOAL = 4
    BATTERY = 8
    FAULTS = 16


class AnswerType(IntEnum):
    NOUL = 1
    CHOICE = 2
    SCORE = 3


class QuestionId(IntEnum):
    PATH_BLOCKED = 1
    CLEAR_SECTOR = 2
    SPEED_TIER = 3
    MODE = 4


QUESTIONS = {
    QuestionId.PATH_BLOCKED: (AnswerType.NOUL, ("false", "true")),
    QuestionId.CLEAR_SECTOR: (AnswerType.CHOICE, ("left", "centre", "right", "none")),
    QuestionId.SPEED_TIER: (AnswerType.SCORE, ("0", "1", "2", "3")),
    QuestionId.MODE: (
        AnswerType.CHOICE,
        ("explore", "approach", "avoid", "dock", "halt"),
    ),
}
MAX_DECISION_PAYLOAD = DECISION.size + sum(
    ANSWER.size + 4 * len(options) for _, options in QUESTIONS.values()
)
MAX_FRAME_SIZE = HEADER.size + max(STATE.size, MAX_DECISION_PAYLOAD) + CRC.size


class ProtocolError(ValueError):
    """Malformed or unsupported frame; never a usable recommendation."""


@dataclass(frozen=True)
class State:
    sequence: int = 0
    timestamp_us: int = 0
    validity: int = 7
    task_id: int = 1
    ages_us: tuple[int, ...] = (0, 0, 0, UINT32_MAX, UINT32_MAX)
    velocity_m_s: tuple[float, ...] = (0.0, 0.0, 0.0)
    angular_velocity_rad_s: tuple[float, ...] = (0.0, 0.0, 0.0)
    goal_m: tuple[float, ...] = (0.0, 0.0, 0.0)
    battery_fraction: float = 0.0
    faults: int = 0


@dataclass(frozen=True)
class Answer:
    question_id: int
    probabilities: tuple[float, ...]
    selected: int

    @property
    def confidence(self):
        """Jev statistic, not calibrated correctness; -1 means absent for noul."""
        kind, _ = QUESTIONS[self.question_id]
        probabilities = self.probabilities
        count = len(probabilities)
        mode = max(range(count), key=probabilities.__getitem__)
        if kind == AnswerType.NOUL:
            return -1.0
        if kind == AnswerType.CHOICE:
            return max(0.0, (probabilities[mode] - 1 / count) / (1 - 1 / count))
        deviation = sum(
            probability * abs(index - mode)
            for index, probability in enumerate(probabilities)
        )
        uniform = sum(abs(index - mode) for index in range(count)) / count
        return max(0.0, 1 - deviation / uniform)


@dataclass(frozen=True)
class Decision:
    sequence: int = 0
    timestamp_us: int = 0
    latency_us: int = 0
    status: int = Status.FAULT
    model_version: int = 0
    catalogue_version: int = CATALOGUE_VERSION
    answers: tuple[Answer, ...] = ()


def unsigned(value, bits, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProtocolError(f"{name} must be an unsigned {bits}-bit integer")
    if not 0 <= value < 2**bits:
        raise ProtocolError(f"{name} must be an unsigned {bits}-bit integer")


def finite(values):
    try:
        if not all(math.isfinite(value) for value in values):
            raise ProtocolError("non-finite state value")
    except TypeError as error:
        raise ProtocolError("state values must be numeric") from error


def validate_state(state):
    unsigned(state.sequence, 32, "sequence")
    unsigned(state.timestamp_us, 32, "timestamp_us")
    unsigned(state.validity, 16, "validity")
    unsigned(state.task_id, 16, "task_id")
    unsigned(state.faults, 32, "faults")
    if state.validity & ~31 or state.task_id != 1:
        raise ProtocolError("unsupported validity bits or task ID")
    vectors = (state.velocity_m_s, state.angular_velocity_rad_s, state.goal_m)
    if len(state.ages_us) != 5 or any(len(vector) != 3 for vector in vectors):
        raise ProtocolError("state requires five ages and three 3-D vectors")
    groups = (*vectors, (state.battery_fraction,), (state.faults,))
    for index, (age, values) in enumerate(zip(state.ages_us, groups, strict=True)):
        unsigned(age, 32, "sensor age")
        finite(values)
        if state.validity & (1 << index):
            if age == UINT32_MAX:
                raise ProtocolError("valid field cannot have unknown age")
        elif age != UINT32_MAX or any(value != 0 for value in values):
            raise ProtocolError("invalid fields require zero values and unknown age")
    if not 0 <= state.battery_fraction <= 1:
        raise ProtocolError("battery fraction must be in [0, 1]")


def encode_frame(kind, sequence, timestamp_us, payload):
    unsigned(sequence, 32, "sequence")
    unsigned(timestamp_us, 32, "timestamp_us")
    header = HEADER.pack(
        MAGIC,
        PROTOCOL_VERSION,
        kind,
        len(payload),
        SCHEMA_VERSION,
        PROFILE_ID,
        PROFILE_VERSION,
        sequence,
        timestamp_us,
    )
    frame = header + payload
    return frame + CRC.pack(zlib.crc32(frame))


def decode_frame(frame, kind, payload_size):
    if len(frame) != HEADER.size + payload_size + CRC.size:
        raise ProtocolError("incorrect frame length")
    if zlib.crc32(frame[: -CRC.size]) != CRC.unpack(frame[-CRC.size :])[0]:
        raise ProtocolError("CRC mismatch")
    magic, protocol, actual_kind, size, schema, profile, version, sequence, stamp = (
        HEADER.unpack(frame[: HEADER.size])
    )
    if magic != MAGIC:
        raise ProtocolError("incorrect magic")
    if (protocol, schema, profile, version) != (
        PROTOCOL_VERSION,
        SCHEMA_VERSION,
        PROFILE_ID,
        PROFILE_VERSION,
    ):
        raise ProtocolError("unsupported protocol, schema or profile")
    if actual_kind != kind or size != payload_size:
        raise ProtocolError("incorrect packet kind or payload length")
    return sequence, stamp, frame[HEADER.size : -CRC.size]


def encode_state(state):
    validate_state(state)
    try:
        payload = STATE.pack(
            state.validity,
            state.task_id,
            *state.ages_us,
            *state.velocity_m_s,
            *state.angular_velocity_rad_s,
            *state.goal_m,
            state.battery_fraction,
            state.faults,
        )
    except (OverflowError, struct.error) as error:
        raise ProtocolError("state value cannot be represented on wire") from error
    return encode_frame(Kind.STATE, state.sequence, state.timestamp_us, payload)


def decode_state(frame):
    sequence, timestamp_us, payload = decode_frame(frame, Kind.STATE, STATE.size)
    values = STATE.unpack(payload)
    state = State(
        sequence,
        timestamp_us,
        values[0],
        values[1],
        values[2:7],
        values[7:10],
        values[10:13],
        values[13:16],
        values[16],
        values[17],
    )
    validate_state(state)
    return state


def validate_answer(answer):
    unsigned(answer.question_id, 8, "question_id")
    unsigned(answer.selected, 8, "selected")
    if answer.question_id not in QUESTIONS:
        raise ProtocolError("unsupported question ID")
    _, options = QUESTIONS[answer.question_id]
    if len(answer.probabilities) != len(options) or answer.selected >= len(options):
        raise ProtocolError("incorrect option count or selection")
    finite(answer.probabilities)
    if any(not 0 <= value <= 1 for value in answer.probabilities) or not math.isclose(
        sum(answer.probabilities), 1.0, rel_tol=0, abs_tol=1e-6
    ):
        raise ProtocolError("probabilities must be in [0, 1] and sum to one")


def validate_decision(decision):
    unsigned(decision.sequence, 32, "sequence")
    unsigned(decision.timestamp_us, 32, "timestamp_us")
    unsigned(decision.latency_us, 32, "latency_us")
    unsigned(decision.status, 16, "status")
    unsigned(decision.model_version, 16, "model_version")
    unsigned(decision.catalogue_version, 16, "catalogue_version")
    if decision.status not in tuple(Status):
        raise ProtocolError("unsupported decision status")
    if decision.catalogue_version != CATALOGUE_VERSION:
        raise ProtocolError("unsupported catalogue version")
    identifiers = []
    for answer in decision.answers:
        validate_answer(answer)
        identifiers.append(answer.question_id)
    if identifiers != sorted(set(identifiers)):
        raise ProtocolError("answers must have unique ascending question IDs")
    if decision.status == Status.OK and (
        identifiers != list(QUESTIONS) or decision.model_version == 0
    ):
        raise ProtocolError("OK requires all four answers and a nonzero model version")


def encode_decision(decision):
    validate_decision(decision)
    mask = sum(1 << (answer.question_id - 1) for answer in decision.answers)
    payload = DECISION.pack(
        decision.latency_us,
        decision.status,
        decision.model_version,
        decision.catalogue_version,
        mask,
    )
    for answer in decision.answers:
        kind, options = QUESTIONS[answer.question_id]
        probabilities = struct.pack("<" + "f" * len(options), *answer.probabilities)
        wire_answer = Answer(
            answer.question_id,
            struct.unpack("<" + "f" * len(options), probabilities),
            answer.selected,
        )
        payload += (
            ANSWER.pack(
                answer.question_id,
                kind,
                answer.selected,
                len(options),
                wire_answer.confidence,
            )
            + probabilities
        )
    return encode_frame(
        Kind.DECISION, decision.sequence, decision.timestamp_us, payload
    )


def decode_decision(frame):
    size = len(frame) - HEADER.size - CRC.size
    if not DECISION.size <= size <= MAX_DECISION_PAYLOAD:
        raise ProtocolError("incorrect decision frame length")
    sequence, timestamp_us, payload = decode_frame(frame, Kind.DECISION, size)
    latency, status, model, catalogue, mask = DECISION.unpack(payload[: DECISION.size])
    if mask & ~15:
        raise ProtocolError("unsupported answer mask")
    offset = DECISION.size
    answers = []
    for question_id, (expected_kind, options) in QUESTIONS.items():
        if not mask & (1 << (question_id - 1)):
            continue
        end = offset + ANSWER.size + 4 * len(options)
        if end > len(payload):
            raise ProtocolError("truncated answer")
        identifier, kind, selected, count, confidence = ANSWER.unpack(
            payload[offset : offset + ANSWER.size]
        )
        if (identifier, kind, count) != (question_id, expected_kind, len(options)):
            raise ProtocolError("unsupported question layout or order")
        probabilities = struct.unpack(
            "<" + "f" * count, payload[offset + ANSWER.size : end]
        )
        answer = Answer(identifier, probabilities, selected)
        validate_answer(answer)
        if not math.isclose(confidence, answer.confidence, rel_tol=0, abs_tol=2e-6):
            raise ProtocolError("confidence does not match the distribution")
        answers.append(answer)
        offset = end
    if offset != len(payload):
        raise ProtocolError("unexpected trailing answer bytes")
    decision = Decision(
        sequence, timestamp_us, latency, status, model, catalogue, tuple(answers)
    )
    validate_decision(decision)
    return decision


class FrameDecoder:
    """Bounded UART-style framing; corruption is discarded, never acted upon."""

    def __init__(self):
        self.buffer = bytearray()
        self.rejected_frames = 0

    def feed(self, data):
        packets = []
        for start in range(0, len(data), MAX_FRAME_SIZE):
            self.buffer.extend(data[start : start + MAX_FRAME_SIZE])
            while self.buffer:
                position = self.buffer.find(MAGIC)
                if position < 0:
                    self.buffer[:] = (
                        self.buffer[-1:] if self.buffer[-1:] == MAGIC[:1] else b""
                    )
                    break
                del self.buffer[:position]
                if len(self.buffer) < HEADER.size:
                    break
                header = HEADER.unpack(self.buffer[: HEADER.size])
                kind, size = header[2], header[3]
                bounded = (kind == Kind.STATE and size == STATE.size) or (
                    kind == Kind.DECISION
                    and DECISION.size <= size <= MAX_DECISION_PAYLOAD
                )
                if not bounded:
                    self.rejected_frames += 1
                    del self.buffer[0]
                    continue
                length = HEADER.size + size + CRC.size
                if len(self.buffer) < length:
                    break
                frame = bytes(self.buffer[:length])
                try:
                    packet = (
                        decode_state(frame)
                        if kind == Kind.STATE
                        else decode_decision(frame)
                    )
                except ProtocolError:
                    self.rejected_frames += 1
                    del self.buffer[0]
                else:
                    packets.append(packet)
                    del self.buffer[:length]
        return packets


def c_header():
    """Generate constants and byte offsets, not native/packed C structs."""
    lines = [
        "#ifndef MICRO_CLASSIFIER_PROTOCOL_H",
        "#define MICRO_CLASSIFIER_PROTOCOL_H",
        "#include <limits.h>",
        "#include <stdint.h>",
        "#if CHAR_BIT != 8",
        '#error "Protocol requires eight-bit bytes"',
        "#endif",
    ]
    constants = {
        "PROVISIONAL": 1,
        "PROTOCOL_VERSION": PROTOCOL_VERSION,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "PROFILE_ID": PROFILE_ID,
        "PROFILE_VERSION": PROFILE_VERSION,
        "CATALOGUE_VERSION": CATALOGUE_VERSION,
        "TASK_GOAL_REACHING": 1,
        "MAGIC_0": MAGIC[0],
        "MAGIC_1": MAGIC[1],
        "HEADER_SIZE": HEADER.size,
        "CRC_SIZE": CRC.size,
        "CRC_POLYNOMIAL_REFLECTED": 0xEDB88320,
        "CRC_INITIAL": UINT32_MAX,
        "CRC_XOR_OUT": UINT32_MAX,
        "UNKNOWN_AGE_US": UINT32_MAX,
        "STATE_PAYLOAD_SIZE": STATE.size,
        "STATE_FRAME_SIZE": HEADER.size + STATE.size + CRC.size,
        "DECISION_PREFIX_SIZE": DECISION.size,
        "ANSWER_PREFIX_SIZE": ANSWER.size,
        "DECISION_MAX_PAYLOAD_SIZE": MAX_DECISION_PAYLOAD,
        "MAX_FRAME_SIZE": MAX_FRAME_SIZE,
    }
    for name, value in constants.items():
        lines.append(f"#define MC_V0_{name} UINT32_C({value})")
    for group, fields in (
        ("HEADER", HEADER_FIELDS),
        ("STATE", STATE_FIELDS),
        ("DECISION", DECISION_FIELDS),
        ("ANSWER", ANSWER_FIELDS),
    ):
        offset = 0
        for name, code in fields:
            lines.append(
                f"#define MC_V0_{group}_{name.upper()}_OFFSET UINT32_C({offset})"
            )
            offset += struct.calcsize("<" + code)
    for group, enumeration in (
        ("KIND", Kind),
        ("STATUS", Status),
        ("VALID", Validity),
        ("TYPE", AnswerType),
        ("QUESTION", QuestionId),
    ):
        for member in enumeration:
            lines.append(
                f"#define MC_V0_{group}_{member.name} UINT32_C({member.value})"
            )
    for question_id, (_, options) in QUESTIONS.items():
        name = QuestionId(question_id).name
        lines.append(f"#define MC_V0_{name}_OPTION_COUNT UINT32_C({len(options)})")
        for index, option in enumerate(options):
            lines.append(f"#define MC_V0_{name}_{option.upper()} UINT32_C({index})")
    lines.extend(["#endif", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-header", type=Path, required=True)
    args = parser.parse_args()
    args.write_header.parent.mkdir(parents=True, exist_ok=True)
    args.write_header.write_text(c_header())


if __name__ == "__main__":
    main()
