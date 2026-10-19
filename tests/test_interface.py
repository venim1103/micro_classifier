import ctypes
import json
import shutil
import struct
import subprocess
import zlib
from dataclasses import replace
from pathlib import Path

import pytest

from interface.protocol import (
    CRC,
    HEADER,
    STATE,
    UINT32_MAX,
    Answer,
    Decision,
    FrameDecoder,
    ProtocolError,
    QuestionId,
    State,
    Status,
    c_header,
    decode_decision,
    decode_state,
    encode_decision,
    encode_state,
)


def with_crc(frame):
    return frame[:-4] + CRC.pack(zlib.crc32(frame[:-4]))


def test_crc_and_state_layout():
    assert zlib.crc32(b"123456789") == 0xCBF43926
    assert HEADER.size == 20
    assert STATE.size == 68
    state = State(sequence=UINT32_MAX, timestamp_us=UINT32_MAX, goal_m=(4.0, 1.0, 0.0))
    frame = encode_state(state)
    assert len(frame) == 92
    assert frame[:4] == b"MC\x00\x01"
    assert decode_state(frame) == state
    assert encode_state(decode_state(frame)) == frame


def test_crc_rejects_every_single_byte_corruption():
    frame = encode_state(State())
    for index in range(len(frame)):
        changed = bytearray(frame)
        changed[index] ^= 1
        with pytest.raises(ProtocolError, match="CRC"):
            decode_state(changed)


@pytest.mark.parametrize("length", [0, 1, 19, 20, 91, 93, 184])
def test_partial_or_concatenated_frames_are_not_silently_accepted(length):
    frame = (encode_state(State()) * 2)[:length]
    with pytest.raises(ProtocolError, match="length"):
        decode_state(frame)


@pytest.mark.parametrize("offset", [0, 2, 3, 4, 6, 8, 10])
def test_unsupported_header_rejected_even_with_valid_crc(offset):
    frame = bytearray(encode_state(State()))
    frame[offset] ^= 0x80
    with pytest.raises(ProtocolError):
        decode_state(with_crc(frame))


@pytest.mark.parametrize(
    "changes",
    [
        {"sequence": -1},
        {"sequence": True},
        {"timestamp_us": 2**32},
        {"task_id": 2},
        {"validity": 32},
        {"ages_us": (0, 0, 0, 0, 0)},
        {"ages_us": (UINT32_MAX,) * 5},
        {"goal_m": (float("nan"), 0, 0)},
        {"velocity_m_s": (1e100, 0, 0)},
        {"goal_m": (0, 0)},
        {"battery_fraction": 0.5},
        {"faults": 1},
    ],
)
def test_invalid_state_rejected_before_encoding(changes):
    with pytest.raises(ProtocolError):
        encode_state(replace(State(), **changes))


def test_nonfinite_received_values_rejected_after_crc_check():
    frame = bytearray(encode_state(State()))
    struct.pack_into("<f", frame, HEADER.size + 24, float("inf"))
    with pytest.raises(ProtocolError, match="non-finite"):
        decode_state(with_crc(frame))


def test_unknown_fields_are_explicit_and_valid_health_round_trips():
    unknown = decode_state(encode_state(State()))
    assert unknown.validity == 7
    assert unknown.ages_us[3:] == (UINT32_MAX, UINT32_MAX)
    healthy = State(
        validity=31, ages_us=(0, 1, 2, 3, 4), battery_fraction=0.5, faults=4
    )
    assert decode_state(encode_state(healthy)) == healthy


def full_decision():
    return Decision(
        sequence=42,
        timestamp_us=50000,
        latency_us=2000,
        status=Status.OK,
        model_version=1,
        answers=(
            Answer(QuestionId.PATH_BLOCKED, (0.75, 0.25), 0),
            Answer(QuestionId.CLEAR_SECTOR, (0.25, 0.5, 0.125, 0.125), 0),
            Answer(QuestionId.SPEED_TIER, (0.125, 0.125, 0.5, 0.25), 2),
            Answer(QuestionId.MODE, (0.125, 0.5, 0.125, 0.125, 0.125), 1),
        ),
    )


def test_decision_round_trip_preserves_distributions_and_separate_selections():
    decision = full_decision()
    frame = encode_decision(decision)
    assert len(frame) == 128
    assert decode_decision(frame) == decision
    assert encode_decision(decode_decision(frame)) == frame
    assert decision.answers[1].selected == 0
    assert decision.answers[1].probabilities.index(0.5) == 1


def test_jev_confidence_is_not_entropy_or_top_two_margin():
    assert Answer(1, (0.75, 0.25), 0).confidence == -1
    assert Answer(2, (0.25, 0.5, 0.125, 0.125), 1).confidence == pytest.approx(1 / 3)
    assert Answer(3, (0.125, 0.125, 0.5, 0.25), 2).confidence == 0.375
    assert Answer(3, (0.25,) * 4, 0).confidence == 0
    assert Answer(3, (0, 0, 0, 1), 3).confidence == 1


@pytest.mark.parametrize("status", list(Status))
def test_status_packets_are_explicit_and_default_is_fault(status):
    packet = replace(full_decision(), status=status)
    assert decode_decision(encode_decision(packet)).status == status
    if status != Status.OK:
        empty = Decision(status=status)
        assert len(encode_decision(empty)) == 36
        assert decode_decision(encode_decision(empty)) == empty
    assert Decision().status == Status.FAULT


@pytest.mark.parametrize(
    "changes",
    [
        {"answers": ()},
        {"answers": full_decision().answers[::-1]},
        {"answers": (full_decision().answers[0],) * 4},
        {"answers": (Answer(1, (0.75, 0.75), 0),)},
        {"answers": (Answer(1, (float("nan"), 0), 0),)},
        {"answers": (Answer(2, (0.25,) * 4, 4),)},
        {"answers": (Answer(2, (0.5, 0.5), 1),)},
        {"model_version": 0},
        {"status": 6},
        {"catalogue_version": 1},
        {"latency_us": -1},
    ],
)
def test_invalid_decisions_are_rejected(changes):
    with pytest.raises(ProtocolError):
        encode_decision(replace(full_decision(), **changes))


def test_received_answers_are_checked_even_if_crc_is_valid():
    frame = bytearray(encode_decision(full_decision()))
    for offset in (30, 32, 33, 34, 35, 36, 40):
        changed = frame.copy()
        changed[offset] ^= 0x80
        with pytest.raises(ProtocolError):
            decode_decision(with_crc(changed))
    for index in range(len(frame)):
        changed = frame.copy()
        changed[index] ^= 1
        with pytest.raises(ProtocolError, match="CRC"):
            decode_decision(changed)


def test_stream_handles_all_chunk_boundaries_noise_and_consecutive_packets():
    packets = (State(), full_decision(), Decision())
    wire = (
        encode_state(packets[0])
        + encode_decision(packets[1])
        + encode_decision(packets[2])
    )
    for boundary in range(len(wire) + 1):
        stream = FrameDecoder()
        decoded = stream.feed(b"noiseM" + wire[:boundary]) + stream.feed(
            wire[boundary:]
        )
        assert decoded == list(packets)
        assert not stream.buffer


def test_stream_recovers_after_corruption_and_impossible_length():
    broken = bytearray(encode_state(State()))
    broken[-1] ^= 1
    oversized = bytearray(encode_state(State()))
    struct.pack_into("<H", oversized, 4, 65535)
    stream = FrameDecoder()
    assert stream.feed(broken + oversized + encode_state(State(sequence=2))) == [
        State(sequence=2)
    ]
    assert stream.rejected_frames >= 2
    assert stream.feed(b"M" * 100000) == []
    assert len(stream.buffer) <= 1


def test_wire_round_trip_is_exact_for_non_binary_fractions():
    packet = replace(
        full_decision(),
        answers=(
            Answer(1, (0.9, 0.1), 0),
            Answer(2, (0.1, 0.2, 0.3, 0.4), 3),
            Answer(3, (0.1, 0.2, 0.3, 0.4), 3),
            Answer(4, (0.1, 0.2, 0.3, 0.1, 0.3), 2),
        ),
    )
    frame = encode_decision(packet)
    assert encode_decision(decode_decision(frame)) == frame


ROOT = Path(__file__).resolve().parents[1]
HEADER_PATH = ROOT / "firmware/include/micro_classifier_protocol.h"
GOLDEN = json.loads((ROOT / "interface/golden_vectors.json").read_text())["vectors"]


@pytest.mark.parametrize("vector", GOLDEN, ids=lambda vector: vector["name"])
def test_golden_byte_vectors(vector):
    fields = vector["fields"].copy()
    if vector["kind"] == "state":
        for name, value in fields.items():
            if isinstance(value, list):
                fields[name] = tuple(value)
        packet = State(**fields)
        encode, decode = encode_state, decode_state
    else:
        if "answers" in fields:
            fields["answers"] = tuple(
                Answer(
                    answer["question_id"],
                    tuple(answer["probabilities"]),
                    answer["selected"],
                )
                for answer in fields["answers"]
            )
        packet = Decision(**fields)
        encode, decode = encode_decision, decode_decision
    frame = bytes.fromhex(vector["hex"])
    assert encode(packet) == frame
    assert decode(frame) == packet


def test_generated_header_matches_single_source_definition():
    assert HEADER_PATH.read_text() == c_header()


@pytest.mark.parametrize("compiler", ["cc", "arm-none-eabi-gcc"])
def test_header_compiles_without_packed_structs_or_hal(compiler):
    if shutil.which(compiler) is None:
        pytest.skip(f"{compiler} unavailable")
    subprocess.run(
        [
            compiler,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-fsyntax-only",
            "-x",
            "c",
            "-",
        ],
        input=f'#include "{HEADER_PATH}"\n_Static_assert(MC_V0_MAX_FRAME_SIZE == 128, "frame bound");\n',
        text=True,
        capture_output=True,
        check=True,
    )


def test_independent_c_encoding_matches_state_golden(tmp_path):
    if shutil.which("cc") is None:
        pytest.skip("host C compiler unavailable")
    source = r"""
#include "micro_classifier_protocol.h"
#include <stdio.h>
#include <string.h>
_Static_assert(sizeof(float) == 4, "binary32 required by fixture");
static void put16(uint8_t *target, uint16_t value) {
    target[0] = (uint8_t)value;
    target[1] = (uint8_t)(value >> 8);
}
static void put32(uint8_t *target, uint32_t value) {
    for (unsigned index = 0; index < 4; ++index) {
        target[index] = (uint8_t)(value >> (8 * index));
    }
}
static void put_float(uint8_t *target, float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    put32(target, bits);
}
static uint32_t crc32(const uint8_t *data, unsigned length) {
    uint32_t crc = MC_V0_CRC_INITIAL;
    for (unsigned index = 0; index < length; ++index) {
        crc ^= data[index];
        for (unsigned bit = 0; bit < 8; ++bit) {
            crc = (crc >> 1) ^ ((crc & 1) ? MC_V0_CRC_POLYNOMIAL_REFLECTED : 0);
        }
    }
    return crc ^ MC_V0_CRC_XOR_OUT;
}
int main(void) {
    uint8_t frame[MC_V0_STATE_FRAME_SIZE] = {0};
    uint8_t *payload = frame + MC_V0_HEADER_SIZE;
    frame[0] = MC_V0_MAGIC_0;
    frame[1] = MC_V0_MAGIC_1;
    frame[MC_V0_HEADER_PROTOCOL_VERSION_OFFSET] = MC_V0_PROTOCOL_VERSION;
    frame[MC_V0_HEADER_KIND_OFFSET] = MC_V0_KIND_STATE;
    put16(frame + MC_V0_HEADER_PAYLOAD_SIZE_OFFSET, MC_V0_STATE_PAYLOAD_SIZE);
    put16(frame + MC_V0_HEADER_PROFILE_ID_OFFSET, MC_V0_PROFILE_ID);
    put32(frame + MC_V0_HEADER_SEQUENCE_OFFSET, 42);
    put32(frame + MC_V0_HEADER_TIMESTAMP_US_OFFSET, 50000);
    put16(payload + MC_V0_STATE_VALIDITY_OFFSET, MC_V0_VALID_VELOCITY | MC_V0_VALID_ANGULAR_VELOCITY | MC_V0_VALID_GOAL);
    put16(payload + MC_V0_STATE_TASK_ID_OFFSET, MC_V0_TASK_GOAL_REACHING);
    put32(payload + MC_V0_STATE_AGES_US_OFFSET + 12, MC_V0_UNKNOWN_AGE_US);
    put32(payload + MC_V0_STATE_AGES_US_OFFSET + 16, MC_V0_UNKNOWN_AGE_US);
    put_float(payload + MC_V0_STATE_VELOCITY_M_S_OFFSET, 0.5f);
    put_float(payload + MC_V0_STATE_ANGULAR_VELOCITY_RAD_S_OFFSET + 8, 0.25f);
    put_float(payload + MC_V0_STATE_GOAL_M_OFFSET, 4.0f);
    put_float(payload + MC_V0_STATE_GOAL_M_OFFSET + 4, 1.0f);
    put32(frame + MC_V0_STATE_FRAME_SIZE - MC_V0_CRC_SIZE, crc32(frame, MC_V0_STATE_FRAME_SIZE - MC_V0_CRC_SIZE));
    for (unsigned index = 0; index < sizeof(frame); ++index) {
        printf("%02x", (unsigned)frame[index]);
    }
    return 0;
}
"""
    executable = tmp_path / "encode_golden"
    subprocess.run(
        [
            "cc",
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-I",
            str(HEADER_PATH.parent),
            "-x",
            "c",
            "-",
            "-o",
            str(executable),
        ],
        input=source,
        text=True,
        capture_output=True,
        check=True,
    )
    result = subprocess.run(
        [str(executable)], text=True, capture_output=True, check=True
    )
    assert result.stdout == GOLDEN[0]["hex"]


class CState(ctypes.Structure):
    _fields_ = [
        ("sequence", ctypes.c_uint32),
        ("timestamp_us", ctypes.c_uint32),
        ("validity", ctypes.c_uint16),
        ("task_id", ctypes.c_uint16),
        ("ages_us", ctypes.c_uint32 * 5),
        ("velocity_m_s", ctypes.c_float * 3),
        ("angular_velocity_rad_s", ctypes.c_float * 3),
        ("goal_m", ctypes.c_float * 3),
        ("battery_fraction", ctypes.c_float),
        ("faults", ctypes.c_uint32),
    ]


class CAnswer(ctypes.Structure):
    _fields_ = [
        ("question_id", ctypes.c_uint8),
        ("answer_type", ctypes.c_uint8),
        ("selected", ctypes.c_uint8),
        ("option_count", ctypes.c_uint8),
        ("confidence", ctypes.c_float),
        ("probabilities", ctypes.c_float * 5),
    ]


class CDecision(ctypes.Structure):
    _fields_ = [
        ("sequence", ctypes.c_uint32),
        ("timestamp_us", ctypes.c_uint32),
        ("latency_us", ctypes.c_uint32),
        ("status", ctypes.c_uint16),
        ("model_version", ctypes.c_uint16),
        ("catalogue_version", ctypes.c_uint16),
        ("answer_mask", ctypes.c_uint16),
        ("answers", CAnswer * 4),
    ]


@pytest.fixture(scope="module")
def c_codec(tmp_path_factory):
    if shutil.which("cc") is None:
        pytest.skip("host C compiler unavailable")
    library = tmp_path_factory.mktemp("c-codec") / "codec.so"
    subprocess.run(
        [
            "cc",
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-shared",
            "-fPIC",
            "-I",
            str(HEADER_PATH.parent),
            str(ROOT / "firmware/micro_classifier_codec.c"),
            "-o",
            str(library),
        ],
        capture_output=True,
        check=True,
    )
    codec = ctypes.CDLL(str(library))
    codec.mc_v0_crc32.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
    codec.mc_v0_crc32.restype = ctypes.c_uint32
    codec.mc_v0_decode_state.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(CState),
    ]
    codec.mc_v0_decode_state.restype = ctypes.c_int
    codec.mc_v0_decode_decision.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(CDecision),
    ]
    codec.mc_v0_decode_decision.restype = ctypes.c_int
    return codec


def c_buffer(frame):
    return (ctypes.c_uint8 * len(frame)).from_buffer_copy(frame)


def test_c_codec_crc(c_codec):
    for data in (b"", b"123456789", bytes(range(256))):
        assert c_codec.mc_v0_crc32(c_buffer(data), len(data)) == zlib.crc32(data)


@pytest.mark.parametrize(
    "vector",
    [vector for vector in GOLDEN if vector["kind"] == "state"],
    ids=lambda vector: vector["name"],
)
def test_c_codec_state_golden(c_codec, vector):
    frame = bytes.fromhex(vector["hex"])
    expected = decode_state(frame)
    output = CState()
    assert (
        c_codec.mc_v0_decode_state(c_buffer(frame), len(frame), ctypes.byref(output))
        == 0
    )
    for name, _ in CState._fields_:
        actual = getattr(output, name)
        if isinstance(actual, ctypes.Array):
            actual = tuple(actual)
        assert actual == getattr(expected, name)


def test_c_codec_state_corruption_and_failed_output(c_codec):
    frame = encode_state(State())
    output = CState.from_buffer_copy(b"\xa5" * ctypes.sizeof(CState))
    original = bytes(output)
    for index in range(len(frame)):
        changed = bytearray(frame)
        changed[index] ^= 1
        assert (
            c_codec.mc_v0_decode_state(
                c_buffer(changed), len(changed), ctypes.byref(output)
            )
            != 0
        )
        assert bytes(output) == original
    for length in range(len(frame)):
        assert (
            c_codec.mc_v0_decode_state(c_buffer(frame), length, ctypes.byref(output))
            != 0
        )
        assert bytes(output) == original


@pytest.mark.parametrize(
    "offset,code,value",
    [
        (0, "H", 32),
        (2, "H", 2),
        (4, "I", UINT32_MAX),
        (16, "I", 0),
        (24, "f", float("nan")),
        (36, "f", float("inf")),
        (48, "f", float("-inf")),
        (60, "f", 0.5),
        (64, "I", 1),
    ],
)
def test_c_codec_rejects_semantically_invalid_state(c_codec, offset, code, value):
    frame = bytearray(encode_state(State()))
    struct.pack_into("<" + code, frame, HEADER.size + offset, value)
    frame = with_crc(frame)
    with pytest.raises(ProtocolError):
        decode_state(frame)
    output = CState()
    assert (
        c_codec.mc_v0_decode_state(c_buffer(frame), len(frame), ctypes.byref(output))
        != 0
    )


def test_c_codec_state_null_arguments(c_codec):
    frame = c_buffer(encode_state(State()))
    output = CState()
    assert c_codec.mc_v0_decode_state(None, len(frame), ctypes.byref(output)) != 0
    assert c_codec.mc_v0_decode_state(frame, len(frame), None) != 0


@pytest.mark.parametrize(
    "vector",
    [vector for vector in GOLDEN if vector["kind"] == "decision"],
    ids=lambda vector: vector["name"],
)
def test_c_codec_decision_golden(c_codec, vector):
    frame = bytes.fromhex(vector["hex"])
    expected = decode_decision(frame)
    output = CDecision()
    assert (
        c_codec.mc_v0_decode_decision(c_buffer(frame), len(frame), ctypes.byref(output))
        == 0
    )
    for name in (
        "sequence",
        "timestamp_us",
        "latency_us",
        "status",
        "model_version",
        "catalogue_version",
    ):
        assert getattr(output, name) == getattr(expected, name)
    assert output.answer_mask == sum(
        1 << (answer.question_id - 1) for answer in expected.answers
    )
    for answer in expected.answers:
        actual = output.answers[answer.question_id - 1]
        assert actual.question_id == answer.question_id
        assert actual.selected == answer.selected
        assert (
            tuple(actual.probabilities)[: actual.option_count] == answer.probabilities
        )
        assert actual.confidence == pytest.approx(answer.confidence, abs=2e-6)


def test_c_codec_decision_subsets_ties_and_nonbinary_fractions(c_codec):
    for status in Status:
        for mask in range(16):
            answers = tuple(
                answer
                for answer in full_decision().answers
                if mask & (1 << (answer.question_id - 1))
            )
            packet = replace(full_decision(), status=status, answers=answers)
            if status == Status.OK and mask != 15:
                continue
            frame = encode_decision(packet)
            output = CDecision()
            assert (
                c_codec.mc_v0_decode_decision(
                    c_buffer(frame), len(frame), ctypes.byref(output)
                )
                == 0
            )
            assert output.answer_mask == mask
            assert output.status == status
    for probabilities in ((0.25,) * 4, (0.1, 0.2, 0.3, 0.4), (0.5, 0.5, 0, 0)):
        for question in (2, 3):
            packet = Decision(answers=(Answer(question, probabilities, 3),))
            frame = encode_decision(packet)
            expected = decode_decision(frame).answers[0]
            output = CDecision()
            assert (
                c_codec.mc_v0_decode_decision(
                    c_buffer(frame), len(frame), ctypes.byref(output)
                )
                == 0
            )
            actual = output.answers[question - 1]
            assert actual.selected == 3
            assert actual.confidence == pytest.approx(expected.confidence, abs=2e-6)


@pytest.mark.parametrize(
    "offset,code,value",
    [
        (24, "H", 6),
        (26, "H", 0),
        (28, "H", 1),
        (30, "H", 16),
        (30, "H", 7),
        (32, "B", 2),
        (33, "B", 2),
        (34, "B", 2),
        (35, "B", 255),
        (36, "f", 0),
        (36, "f", float("nan")),
        (40, "f", -0.1),
        (40, "f", float("inf")),
        (40, "f", 0.8),
        (52, "f", 0.5),
        (76, "f", float("inf")),
    ],
)
def test_c_codec_rejects_invalid_decision(c_codec, offset, code, value):
    frame = bytearray(encode_decision(full_decision()))
    struct.pack_into("<" + code, frame, offset, value)
    frame = with_crc(frame)
    with pytest.raises(ProtocolError):
        decode_decision(frame)
    output = CDecision.from_buffer_copy(b"\xa5" * ctypes.sizeof(CDecision))
    original = bytes(output)
    assert (
        c_codec.mc_v0_decode_decision(c_buffer(frame), len(frame), ctypes.byref(output))
        != 0
    )
    assert bytes(output) == original


def test_c_codec_decision_corruption_lengths_and_null_arguments(c_codec):
    frame = encode_decision(full_decision())
    output = CDecision.from_buffer_copy(b"\xa5" * ctypes.sizeof(CDecision))
    original = bytes(output)
    for index in range(len(frame)):
        changed = bytearray(frame)
        changed[index] ^= 1
        assert (
            c_codec.mc_v0_decode_decision(
                c_buffer(changed), len(changed), ctypes.byref(output)
            )
            != 0
        )
        assert bytes(output) == original
    for length in range(len(frame)):
        assert (
            c_codec.mc_v0_decode_decision(c_buffer(frame), length, ctypes.byref(output))
            != 0
        )
        assert bytes(output) == original
    assert c_codec.mc_v0_decode_decision(None, 0, ctypes.byref(output)) != 0
    assert c_codec.mc_v0_decode_decision(c_buffer(frame), len(frame), None) != 0


@pytest.mark.parametrize("offset", [0, 2, 3, 4, 6, 8, 10])
def test_c_codec_rejects_unsupported_headers_with_valid_crc(c_codec, offset):
    for packet, encode, decode, output in (
        (State(), encode_state, c_codec.mc_v0_decode_state, CState()),
        (full_decision(), encode_decision, c_codec.mc_v0_decode_decision, CDecision()),
    ):
        frame = bytearray(encode(packet))
        frame[offset] ^= 0x80
        frame = with_crc(frame)
        assert decode(c_buffer(frame), len(frame), ctypes.byref(output)) != 0


def test_c_codec_all_state_validity_groups_and_binary32_extremes(c_codec):
    for validity in range(32):
        packet = State(
            sequence=UINT32_MAX,
            timestamp_us=UINT32_MAX,
            validity=validity,
            ages_us=tuple(
                UINT32_MAX - 1 if validity & (1 << group) else UINT32_MAX
                for group in range(5)
            ),
            velocity_m_s=(2**-149, -0.0, (2 - 2**-23) * 2**127)
            if validity & 1
            else (-0.0, 0, 0),
            angular_velocity_rad_s=(-1.5, 0.25, 0.5) if validity & 2 else (0, 0, 0),
            goal_m=(4, -2, 0) if validity & 4 else (0, 0, 0),
            battery_fraction=1 if validity & 8 else 0,
            faults=UINT32_MAX if validity & 16 else 0,
        )
        frame = encode_state(packet)
        expected = decode_state(frame)
        output = CState()
        assert (
            c_codec.mc_v0_decode_state(
                c_buffer(frame), len(frame), ctypes.byref(output)
            )
            == 0
        )
        for name, _ in CState._fields_:
            actual = getattr(output, name)
            if isinstance(actual, ctypes.Array):
                actual = tuple(actual)
            assert actual == getattr(expected, name)
        assert struct.pack("<3f", *output.velocity_m_s) == struct.pack(
            "<3f", *expected.velocity_m_s
        )


@pytest.mark.parametrize("compiler", ["cc", "arm-none-eabi-gcc"])
def test_c_codec_compiles_to_host_and_cortex_m55_objects(tmp_path, compiler):
    if shutil.which(compiler) is None:
        pytest.skip(f"{compiler} unavailable")
    flags = ["-mcpu=cortex-m55", "-mthumb"] if compiler == "arm-none-eabi-gcc" else []
    subprocess.run(
        [
            compiler,
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            *flags,
            "-I",
            str(HEADER_PATH.parent),
            "-c",
            str(ROOT / "firmware/micro_classifier_codec.c"),
            "-o",
            str(tmp_path / "codec.o"),
        ],
        capture_output=True,
        check=True,
    )


def test_c_codec_rejects_fast_math_build(tmp_path):
    if shutil.which("cc") is None:
        pytest.skip("host C compiler unavailable")
    result = subprocess.run(
        [
            "cc",
            "-std=c11",
            "-ffast-math",
            "-I",
            str(HEADER_PATH.parent),
            "-c",
            str(ROOT / "firmware/micro_classifier_codec.c"),
            "-o",
            str(tmp_path / "unsafe.o"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "fast math is unsupported" in result.stderr
