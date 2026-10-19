import ctypes
import hashlib
import json
import math
import os
import random
import shutil
import signal
import struct
import subprocess
import sys
import zlib
from dataclasses import replace
from pathlib import Path

import pytest

from interface import build_audit, native_verify
from interface.native_verify import (
    CAnswer,
    CDecision,
    CHeadInput,
    CPacket,
    CPacketHandler,
    CState,
    CStateHistory,
    CStateWindow,
    CStream,
    build_native,
)
from interface.protocol import (
    CRC,
    HEADER,
    QUESTIONS,
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


@pytest.fixture(scope="module")
def c_codec(tmp_path_factory):
    if shutil.which("cc") is None:
        pytest.skip("host C compiler unavailable")
    codec, _ = build_native(tmp_path_factory.mktemp("c-codec"))
    return codec


def c_buffer(frame):
    return (ctypes.c_uint8 * len(frame)).from_buffer_copy(frame)


def c_state_from_python(packet):
    state = CState()
    for name, field_type in CState._fields_:
        value = getattr(packet, name)
        if issubclass(field_type, ctypes.Array):
            value = field_type(*value)
        setattr(state, name, value)
    return state


def c_decision_from_python(packet):
    decision = CDecision()
    for name in (
        "sequence",
        "timestamp_us",
        "latency_us",
        "status",
        "model_version",
        "catalogue_version",
    ):
        setattr(decision, name, getattr(packet, name))
    for answer in packet.answers:
        decision.answer_mask |= 1 << (answer.question_id - 1)
        target = decision.answers[answer.question_id - 1]
        target.question_id = answer.question_id
        target.answer_type = QUESTIONS[answer.question_id][0]
        target.selected = answer.selected
        target.option_count = len(answer.probabilities)
        target.probabilities[: target.option_count] = answer.probabilities
        target.confidence = float("nan")
    return decision


def c_encoded_frame(codec, source):
    encoder = (
        codec.mc_v0_encode_state
        if isinstance(source, CState)
        else codec.mc_v0_encode_decision
    )
    output = c_buffer(b"\xa5" * 130)
    target = ctypes.cast(ctypes.byref(output, 1), ctypes.POINTER(ctypes.c_uint8))
    written = ctypes.c_size_t(999)
    original = bytes(source)
    assert encoder(ctypes.byref(source), target, 128, ctypes.byref(written)) == 0
    assert 0 < written.value <= 128
    assert bytes(output[:1]) + bytes(output[1 + written.value :]) == b"\xa5" * (
        130 - written.value
    )
    assert bytes(source) == original
    return bytes(output[1 : 1 + written.value])


def test_c_history_empty_and_initial_sample(c_codec):
    history = CStateHistory.from_buffer_copy(b"\xa5" * ctypes.sizeof(CStateHistory))
    c_codec.mc_v0_state_history_init(ctypes.byref(history))
    assert bytes(history) == bytes(ctypes.sizeof(CStateHistory))
    window = CStateWindow()
    assert (
        c_codec.mc_v0_state_history_snapshot(
            ctypes.byref(history), ctypes.byref(window)
        )
        == 0
    )
    assert window.valid_mask == 0
    assert all(
        bytes(sample) == bytes(ctypes.sizeof(CState)) for sample in window.samples
    )
    state = c_state_from_python(State(sequence=42))
    original = bytes(state)
    assert (
        c_codec.mc_v0_state_history_push(ctypes.byref(history), ctypes.byref(state))
        == 0
    )
    assert bytes(state) == original
    assert (
        c_codec.mc_v0_state_history_snapshot(
            ctypes.byref(history), ctypes.byref(window)
        )
        == 0
    )
    assert window.valid_mask == 0x80
    assert all(
        bytes(sample) == bytes(ctypes.sizeof(CState)) for sample in window.samples[:7]
    )
    assert c_encoded_frame(c_codec, window.samples[7]) == encode_state(
        State(sequence=42)
    )


def test_c_history_wraparound_and_explicit_gaps(c_codec):
    history = CStateHistory()
    c_codec.mc_v0_state_history_init(ctypes.byref(history))
    expected = [None] * 8
    for tick in range(32):
        packet = (
            None if tick % 3 == 1 else State(sequence=tick, timestamp_us=tick * 50000)
        )
        if packet is None:
            assert c_codec.mc_v0_state_history_gap(ctypes.byref(history)) == 0
        else:
            source = c_state_from_python(packet)
            assert (
                c_codec.mc_v0_state_history_push(
                    ctypes.byref(history), ctypes.byref(source)
                )
                == 0
            )
        expected = expected[1:] + [packet]
        window = CStateWindow()
        original = bytes(history)
        assert (
            c_codec.mc_v0_state_history_snapshot(
                ctypes.byref(history), ctypes.byref(window)
            )
            == 0
        )
        assert bytes(history) == original
        assert window.valid_mask == sum(
            1 << index for index, sample in enumerate(expected) if sample is not None
        )
        for index, sample in enumerate(expected):
            if sample is None:
                assert bytes(window.samples[index]) == bytes(ctypes.sizeof(CState))
            else:
                assert c_encoded_frame(c_codec, window.samples[index]) == encode_state(
                    sample
                )


@pytest.mark.parametrize(
    "changes",
    [
        {"goal_m": (float("nan"), 0, 0)},
        {"validity": 32},
        {"task_id": 2},
        {"ages_us": (UINT32_MAX,) * 5},
        {"validity": 0, "ages_us": (UINT32_MAX,) * 5, "faults": 1},
    ],
)
def test_c_history_invalid_state_does_not_advance(c_codec, changes):
    history = CStateHistory()
    c_codec.mc_v0_state_history_init(ctypes.byref(history))
    state = c_state_from_python(State())
    assert c_codec.mc_v0_validate_state(ctypes.byref(state)) == 0
    assert (
        c_codec.mc_v0_state_history_push(ctypes.byref(history), ctypes.byref(state))
        == 0
    )
    state = c_state_from_python(replace(State(), **changes))
    original = bytes(history)
    assert c_codec.mc_v0_validate_state(ctypes.byref(state)) != 0
    assert (
        c_codec.mc_v0_state_history_push(ctypes.byref(history), ctypes.byref(state))
        != 0
    )
    assert bytes(history) == original


def test_c_history_slot_presence_is_separate_from_sensor_validity(c_codec):
    history = CStateHistory()
    c_codec.mc_v0_state_history_init(ctypes.byref(history))
    packet = State(validity=0, ages_us=(UINT32_MAX,) * 5)
    state = c_state_from_python(packet)
    assert (
        c_codec.mc_v0_state_history_push(ctypes.byref(history), ctypes.byref(state))
        == 0
    )
    window = CStateWindow()
    assert (
        c_codec.mc_v0_state_history_snapshot(
            ctypes.byref(history), ctypes.byref(window)
        )
        == 0
    )
    assert window.valid_mask == 0x80
    assert window.samples[7].validity == 0
    assert c_encoded_frame(c_codec, window.samples[7]) == encode_state(packet)
    for _ in range(8):
        assert c_codec.mc_v0_state_history_gap(ctypes.byref(history)) == 0
    assert (
        c_codec.mc_v0_state_history_snapshot(
            ctypes.byref(history), ctypes.byref(window)
        )
        == 0
    )
    assert window.valid_mask == 0
    assert all(
        bytes(sample) == bytes(ctypes.sizeof(CState)) for sample in window.samples
    )


def test_c_history_preserves_values_without_ordering_and_owns_copies(c_codec):
    history = CStateHistory()
    c_codec.mc_v0_state_history_init(ctypes.byref(history))
    prototype = State(
        validity=31,
        ages_us=(UINT32_MAX - 1,) * 5,
        velocity_m_s=(-0.0, 2**-149, (2 - 2**-23) * 2**127),
        angular_velocity_rad_s=(1, -2, 3),
        goal_m=(-4, 5, 6),
        battery_fraction=0.5,
        faults=UINT32_MAX,
    )
    packets = [
        replace(prototype, sequence=sequence, timestamp_us=stamp)
        for sequence, stamp in (
            (UINT32_MAX, UINT32_MAX),
            (0, 0),
            (0, 2),
            (UINT32_MAX - 1, 1),
        )
    ]
    for packet in packets:
        source = c_state_from_python(packet)
        original = bytes(source)
        assert (
            c_codec.mc_v0_state_history_push(
                ctypes.byref(history), ctypes.byref(source)
            )
            == 0
        )
        assert bytes(source) == original
        ctypes.memset(ctypes.byref(source), 0xA5, ctypes.sizeof(source))
    window = CStateWindow()
    original = bytes(history)
    assert (
        c_codec.mc_v0_state_history_snapshot(
            ctypes.byref(history), ctypes.byref(window)
        )
        == 0
    )
    assert window.valid_mask == 0xF0
    assert [c_encoded_frame(c_codec, sample) for sample in window.samples[4:]] == [
        encode_state(packet) for packet in packets
    ]
    ctypes.memset(ctypes.byref(window), 0xA5, ctypes.sizeof(window))
    assert bytes(history) == original
    c_codec.mc_v0_state_history_init(ctypes.byref(history))
    assert bytes(history) == bytes(ctypes.sizeof(CStateHistory))


def test_c_history_null_arguments_leave_objects_unchanged(c_codec):
    history = CStateHistory()
    c_codec.mc_v0_state_history_init(ctypes.byref(history))
    state = c_state_from_python(State())
    window = CStateWindow.from_buffer_copy(b"\xa5" * ctypes.sizeof(CStateWindow))
    original_history, original_window = bytes(history), bytes(window)
    assert c_codec.mc_v0_validate_state(None) != 0
    assert c_codec.mc_v0_state_history_push(None, ctypes.byref(state)) != 0
    assert c_codec.mc_v0_state_history_push(ctypes.byref(history), None) != 0
    assert c_codec.mc_v0_state_history_gap(None) != 0
    assert c_codec.mc_v0_state_history_snapshot(None, ctypes.byref(window)) != 0
    assert c_codec.mc_v0_state_history_snapshot(ctypes.byref(history), None) != 0
    c_codec.mc_v0_state_history_init(None)
    assert bytes(history) == original_history
    assert bytes(window) == original_window


@pytest.mark.parametrize("cursor", [8, 9, 255])
def test_c_history_rejects_damaged_cursor_without_writes(c_codec, cursor):
    history = CStateHistory()
    c_codec.mc_v0_state_history_init(ctypes.byref(history))
    history.next = cursor
    source = c_state_from_python(State())
    window = CStateWindow.from_buffer_copy(b"\xa5" * ctypes.sizeof(CStateWindow))
    original_history, original_window = bytes(history), bytes(window)
    assert (
        c_codec.mc_v0_state_history_push(ctypes.byref(history), ctypes.byref(source))
        != 0
    )
    assert c_codec.mc_v0_state_history_gap(ctypes.byref(history)) != 0
    assert (
        c_codec.mc_v0_state_history_snapshot(
            ctypes.byref(history), ctypes.byref(window)
        )
        != 0
    )
    assert bytes(history) == original_history
    assert bytes(window) == original_window


def test_c_history_seeded_operations_match_python_window(c_codec):
    generator = random.Random(20261019)
    history, window = CStateHistory(), CStateWindow()
    c_codec.mc_v0_state_history_init(ctypes.byref(history))
    expected = [None] * 8
    for _ in range(1024):
        operation = generator.randrange(16)
        if operation == 0:
            c_codec.mc_v0_state_history_init(ctypes.byref(history))
            expected = [None] * 8
        elif operation < 5:
            assert c_codec.mc_v0_state_history_gap(ctypes.byref(history)) == 0
            expected = expected[1:] + [None]
        else:
            validity = generator.randrange(32)
            vectors = [
                tuple(generator.randrange(-32768, 32769) / 256 for _ in range(3))
                if validity & (1 << group)
                else (0, 0, 0)
                for group in range(3)
            ]
            packet = State(
                sequence=generator.getrandbits(32),
                timestamp_us=generator.getrandbits(32),
                validity=validity,
                ages_us=tuple(
                    generator.randrange(UINT32_MAX)
                    if validity & (1 << group)
                    else UINT32_MAX
                    for group in range(5)
                ),
                velocity_m_s=vectors[0],
                angular_velocity_rad_s=vectors[1],
                goal_m=vectors[2],
                battery_fraction=generator.getrandbits(23) / 2**23
                if validity & 8
                else 0,
                faults=generator.getrandbits(32) if validity & 16 else 0,
            )
            source = c_state_from_python(packet)
            if operation == 5:
                source.battery_fraction = float("inf")
                original = bytes(history)
                assert (
                    c_codec.mc_v0_state_history_push(
                        ctypes.byref(history), ctypes.byref(source)
                    )
                    != 0
                )
                assert bytes(history) == original
            else:
                assert (
                    c_codec.mc_v0_state_history_push(
                        ctypes.byref(history), ctypes.byref(source)
                    )
                    == 0
                )
                expected = expected[1:] + [encode_state(packet)]
            ctypes.memset(ctypes.byref(source), 0xA5, ctypes.sizeof(source))
        original = bytes(history)
        assert (
            c_codec.mc_v0_state_history_snapshot(
                ctypes.byref(history), ctypes.byref(window)
            )
            == 0
        )
        assert bytes(history) == original
        assert window.valid_mask == sum(
            1 << index for index, frame in enumerate(expected) if frame is not None
        )
        for sample, frame in zip(window.samples, expected, strict=True):
            if frame is None:
                assert bytes(sample) == bytes(ctypes.sizeof(CState))
            else:
                assert c_encoded_frame(c_codec, sample) == frame
        ctypes.memset(ctypes.byref(window), 0xA5, ctypes.sizeof(window))
        assert bytes(history) == original


@pytest.mark.parametrize(
    "logits",
    [
        (0, 0),
        (1000, 1000, -1000, -1000),
        (0, 0, 0, 0, 0),
        (3.4028234663852886e38, -3.4028234663852886e38),
        (-3, 1, 2, -1),
    ],
)
def test_c_math_softmax_matches_stable_reference(c_codec, logits):
    source = (ctypes.c_float * len(logits))(*logits)
    original = bytes(source)
    output = (ctypes.c_float * 7)(*([42] * 7))
    assert c_codec.mc_v0_softmax(source, len(source), output, len(output)) == 0
    maximum = max(source)
    weights = [math.exp(value - maximum) for value in source]
    expected = [weight / sum(weights) for weight in weights]
    assert list(output[: len(source)]) == pytest.approx(expected, abs=5e-8, rel=1e-7)
    assert sum(output[: len(source)]) == pytest.approx(1, abs=1e-6)
    assert list(output[len(source) :]) == [42] * (7 - len(source))
    assert bytes(source) == original


@pytest.mark.parametrize(
    "logit", [-3.4028234663852886e38, -1000, -1, -0.0, 1, 1000, 3.4028234663852886e38]
)
def test_c_math_sigmoid_matches_two_logit_softmax(c_codec, logit):
    output = (ctypes.c_float * 3)(42, 42, 42)
    reference = (ctypes.c_float * 2)()
    source = (ctypes.c_float * 2)(0, logit)
    assert c_codec.mc_v0_sigmoid(logit, output, 3) == 0
    assert c_codec.mc_v0_softmax(source, 2, reference, 2) == 0
    assert list(output[:2]) == list(reference)
    assert output[2] == 42


@pytest.mark.parametrize("question", list(QUESTIONS))
def test_c_math_confidence_matches_existing_codec(c_codec, question):
    count = len(QUESTIONS[question][1])
    packet = Decision(answers=(Answer(question, (1 / count,) * count, count - 1),))
    answer = c_decision_from_python(packet).answers[question - 1]
    confidence = ctypes.c_double(42)
    assert (
        c_codec.mc_v0_answer_confidence(ctypes.byref(answer), ctypes.byref(confidence))
        == 0
    )
    assert confidence.value == pytest.approx(-1 if question == 1 else 0, abs=2e-8)
    assert c_encoded_frame(c_codec, c_decision_from_python(packet)) == encode_decision(
        packet
    )


@pytest.mark.parametrize("count", [2, 4, 5])
@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf")])
def test_c_math_rejects_nonfinite_logits_without_output_writes(c_codec, count, invalid):
    output = (ctypes.c_float * 7)(*([42] * 7))
    original = bytes(output)
    for position in range(count):
        source = (ctypes.c_float * count)(*range(count))
        source[position] = invalid
        before = bytes(source)
        assert c_codec.mc_v0_softmax(source, count, output, 7) != 0
        assert bytes(output) == original
        assert bytes(source) == before
    assert c_codec.mc_v0_sigmoid(invalid, output, 7) != 0
    assert bytes(output) == original


@pytest.mark.parametrize("count", [0, 1, 3, 6, 255, ctypes.c_size_t(-1).value])
def test_c_math_rejects_unsupported_counts_without_access(c_codec, count):
    source = (ctypes.c_float * 1)(0)
    output = (ctypes.c_float * 1)(42)
    assert c_codec.mc_v0_softmax(source, count, output, 1) != 0
    assert output[0] == 42


def test_c_math_capacity_and_null_arguments(c_codec):
    for count in (2, 4, 5):
        source = (ctypes.c_float * count)(*range(count))
        for capacity in range(8):
            output = (ctypes.c_float * 7)(*([42] * 7))
            before = bytes(output)
            result = c_codec.mc_v0_softmax(source, count, output, capacity)
            assert (result == 0) == (capacity >= count)
            if result:
                assert bytes(output) == before
            else:
                assert list(output[count:]) == [42] * (7 - count)
            output[:] = [42] * 7
            result = c_codec.mc_v0_sigmoid(1, output, capacity)
            assert (result == 0) == (capacity >= 2)
            if result:
                assert bytes(output) == before
            else:
                assert list(output[2:]) == [42] * 5
    output[:] = [42] * 7
    assert c_codec.mc_v0_softmax(None, 5, output, 7) != 0
    assert c_codec.mc_v0_softmax(source, 5, None, 7) != 0
    assert c_codec.mc_v0_sigmoid(1, None, 7) != 0
    assert list(output) == [42] * 7
    confidence = ctypes.c_double(42)
    answer = c_decision_from_python(
        Decision(answers=(Answer(2, (0.25,) * 4, 3),))
    ).answers[1]
    assert c_codec.mc_v0_answer_confidence(None, ctypes.byref(confidence)) != 0
    assert c_codec.mc_v0_answer_confidence(ctypes.byref(answer), None) != 0
    assert confidence.value == 42


def test_c_math_confidence_rejects_all_invalid_metadata_without_writes(c_codec):
    answer = c_decision_from_python(
        Decision(answers=(Answer(2, (0.25,) * 4, 3),))
    ).answers[1]
    answer.probabilities[4] = float("nan")
    for field, valid_values in (
        ("question_id", {2}),
        ("answer_type", {2}),
        ("option_count", {4}),
        ("selected", {0, 1, 2, 3}),
    ):
        initial = getattr(answer, field)
        for value in range(256):
            setattr(answer, field, value)
            confidence = ctypes.c_double(42)
            before = bytes(answer)
            result = c_codec.mc_v0_answer_confidence(
                ctypes.byref(answer), ctypes.byref(confidence)
            )
            assert (result == 0) == (value in valid_values)
            assert confidence.value == (0 if result == 0 else 42)
            assert bytes(answer) == before
        setattr(answer, field, initial)


@pytest.mark.parametrize(
    "probabilities",
    [
        (float("nan"), 0.25, 0.25, 0.25),
        (float("inf"), 0, 0, 0),
        (-float("inf"), 0, 0, 0),
        (-0.1, 0.6, 0.5, 0),
        (1.1, 0, 0, 0),
        (0, 0, 0, 0),
        (0.25, 0.25, 0.25, 0.2),
    ],
)
def test_c_math_confidence_rejects_invalid_probabilities(c_codec, probabilities):
    answer = c_decision_from_python(
        Decision(answers=(Answer(2, probabilities, 3),))
    ).answers[1]
    before = bytes(answer)
    confidence = ctypes.c_double(42)
    assert (
        c_codec.mc_v0_answer_confidence(ctypes.byref(answer), ctypes.byref(confidence))
        != 0
    )
    assert confidence.value == 42
    assert bytes(answer) == before


@pytest.mark.parametrize(
    "probabilities",
    [
        (0.5, 0.5, 0, 0),
        (0.25, 0.25, 0.25, 0.25),
        (0, 0.5, 0.5, 0),
        (0, 0, 0.5, 0.5),
        (0, 0.25, 0.5, 0.25),
    ],
)
def test_c_math_score_confidence_uses_first_raw_mode_not_selected(
    c_codec, probabilities
):
    packet = Answer(3, probabilities, 3)
    answer = c_decision_from_python(Decision(answers=(packet,))).answers[2]
    confidence = ctypes.c_double(42)
    assert (
        c_codec.mc_v0_answer_confidence(ctypes.byref(answer), ctypes.byref(confidence))
        == 0
    )
    assert confidence.value == packet.confidence


@pytest.mark.parametrize("count", [2, 4, 5])
def test_c_math_softmax_shift_and_permutation(c_codec, count):
    values = (-2, -0.5, 0, 1, 3)[:count]
    results = []
    for logits in (values, tuple(value + 1024 for value in values), values[::-1]):
        source = (ctypes.c_float * count)(*logits)
        output = (ctypes.c_float * count)()
        assert c_codec.mc_v0_softmax(source, count, output, count) == 0
        results.append(list(output))
    assert results[1] == results[0]
    assert results[2][::-1] == pytest.approx(results[0], abs=5e-8, rel=1e-7)


def test_c_math_seeded_probabilities_confidence_and_wire_parity(c_codec):
    generator = random.Random(20261019)
    largest = struct.unpack("<f", bytes.fromhex("ffff7f7f"))[0]
    special = (
        -largest,
        -1000,
        -100,
        -1,
        -(2**-149),
        -0.0,
        0,
        2**-149,
        1,
        100,
        1000,
        largest,
    )
    frames, packets = [], []
    for iteration in range(250):
        answers = []
        for question, (_, options) in QUESTIONS.items():
            count = len(options)
            logits = [
                generator.choice(special)
                if iteration % 2
                else generator.randrange(-4096, 4097) / 32
                for _ in options
            ]
            if question == 1:
                logits[0] = 0
            source = (ctypes.c_float * count)(*logits)
            original = bytes(source)
            output = (ctypes.c_float * count)()
            if question == 1:
                assert c_codec.mc_v0_sigmoid(source[1], output, count) == 0
            else:
                assert c_codec.mc_v0_softmax(source, count, output, count) == 0
            maximum = max(source)
            weights = [math.exp(value - maximum) for value in source]
            expected = [weight / sum(weights) for weight in weights]
            assert list(output) == pytest.approx(expected, abs=5e-8, rel=1e-7)
            assert all(math.isfinite(value) and 0 <= value <= 1 for value in output)
            assert sum(output) == pytest.approx(1, abs=1e-6)
            assert bytes(source) == original
            packet = Answer(question, tuple(output), generator.randrange(count))
            native = c_decision_from_python(Decision(answers=(packet,))).answers[
                question - 1
            ]
            confidence = ctypes.c_double(42)
            assert (
                c_codec.mc_v0_answer_confidence(
                    ctypes.byref(native), ctypes.byref(confidence)
                )
                == 0
            )
            assert confidence.value == pytest.approx(
                packet.confidence, abs=2e-15, rel=0
            )
            answers.append(packet)
        packet = Decision(sequence=iteration, answers=tuple(answers))
        frame = c_encoded_frame(c_codec, c_decision_from_python(packet))
        assert frame == encode_decision(packet)
        received = CDecision()
        assert (
            c_codec.mc_v0_decode_decision(
                c_buffer(frame), len(frame), ctypes.byref(received)
            )
            == 0
        )
        assert c_encoded_frame(c_codec, received) == frame
        frames.append(frame)
        packets.append(decode_decision(frame))
    wire = b"".join(frames)
    assert FrameDecoder().feed(wire) == packets
    stream = CStream()
    c_codec.mc_v0_stream_init(ctypes.byref(stream))
    assert (
        feed_c_stream(
            c_codec,
            stream,
            (wire[offset : offset + 31] for offset in range(0, len(wire), 31)),
        )
        == packets
    )
    assert stream.used == stream.rejected_frames == 0


def assembly_fixture():
    metadata = native_verify.native_decision(full_decision())
    inputs = (CHeadInput * 4)()
    storage = []
    for index, rows in enumerate((1, 4, 4, 5)):
        features = (ctypes.c_float * 2)(1, -0.5)
        weights = (ctypes.c_float * (2 * rows))(
            *(column / 8 for column in range(2 * rows))
        )
        biases = (ctypes.c_float * rows)(*(row / 4 for row in range(rows)))
        inputs[index] = CHeadInput(features, 2, weights, len(weights), biases, rows)
        storage.extend((features, weights, biases))
    return metadata, inputs, storage


@pytest.mark.parametrize("status", list(Status))
def test_c_assembly_matches_primitive_path_and_preserves_metadata(c_codec, status):
    metadata, inputs, storage = assembly_fixture()
    metadata.status = status
    before = [bytes(value) for value in (metadata, inputs, *storage)]
    expected = CDecision.from_buffer_copy(bytes(metadata))
    for index, rows in enumerate((1, 4, 4, 5)):
        head = inputs[index]
        logits = (ctypes.c_float * rows)()
        assert (
            c_codec.mc_v0_dense_head(
                head.features,
                head.feature_count,
                head.weights,
                head.weight_count,
                head.biases,
                head.bias_count,
                rows,
                logits,
                rows,
            )
            == 0
        )
        probabilities = expected.answers[index].probabilities
        if index == 0:
            assert c_codec.mc_v0_sigmoid(logits[0], probabilities, 2) == 0
        else:
            assert c_codec.mc_v0_softmax(logits, rows, probabilities, rows) == 0
    output = CDecision()
    assert (
        c_codec.mc_v0_assemble_decision(
            ctypes.byref(metadata), inputs, 4, ctypes.byref(output)
        )
        == 0
    )
    assert native_verify.native_frame(c_codec, output) == native_verify.native_frame(
        c_codec, expected
    )
    assert [bytes(value) for value in (metadata, inputs, *storage)] == before
    assert [answer.selected for answer in output.answers] == [
        answer.selected for answer in metadata.answers
    ]
    assert output.answers[0].confidence == -1


def assert_assembly_failure(c_codec, metadata, inputs, storage, expected):
    output = CDecision()
    ctypes.memset(ctypes.byref(output), 0xA5, ctypes.sizeof(output))
    before = [bytes(value) for value in (metadata, inputs, output, *storage)]
    assert (
        c_codec.mc_v0_assemble_decision(
            ctypes.byref(metadata), inputs, 4, ctypes.byref(output)
        )
        == expected
    )
    assert [bytes(value) for value in (metadata, inputs, output, *storage)] == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", 6),
        ("status", 65535),
        ("model_version", 0),
        ("catalogue_version", 1),
        ("answer_mask", 0),
        ("answer_mask", 7),
        ("answer_mask", 65535),
    ],
)
def test_c_assembly_rejects_metadata_before_head_access(c_codec, field, value):
    metadata, _inputs, storage = assembly_fixture()
    setattr(metadata, field, value)
    assert_assembly_failure(c_codec, metadata, (CHeadInput * 4)(), storage, 6)


@pytest.mark.parametrize("index", range(4))
@pytest.mark.parametrize(
    "field,value",
    [("question_id", 0), ("answer_type", 0), ("option_count", 0), ("selected", 255)],
)
def test_c_assembly_rejects_answer_metadata(c_codec, index, field, value):
    metadata, inputs, storage = assembly_fixture()
    setattr(metadata.answers[index], field, value)
    assert_assembly_failure(c_codec, metadata, inputs, storage, 6)


@pytest.mark.parametrize("count", [0, 1, 3, 5, ctypes.c_size_t(-1).value])
def test_c_assembly_rejects_head_count_before_access(c_codec, count):
    metadata, inputs, _storage = assembly_fixture()
    output = CDecision()
    before = bytes(output)
    assert (
        c_codec.mc_v0_assemble_decision(
            ctypes.byref(metadata), inputs, count, ctypes.byref(output)
        )
        == 1
    )
    assert bytes(output) == before


@pytest.mark.parametrize("field", [0, 1, 3])
def test_c_assembly_rejects_null_arguments(c_codec, field):
    metadata, inputs, _storage = assembly_fixture()
    output = CDecision()
    arguments = [ctypes.byref(metadata), inputs, 4, ctypes.byref(output)]
    arguments[field] = None
    assert c_codec.mc_v0_assemble_decision(*arguments) == 1


@pytest.mark.parametrize("index", range(4))
@pytest.mark.parametrize(
    "field",
    ["feature_count", "weight_count", "bias_count", "features", "weights", "biases"],
)
def test_c_assembly_rejects_bad_head_inputs_atomically(c_codec, index, field):
    metadata, inputs, storage = assembly_fixture()
    if field == "feature_count":
        inputs[index].feature_count = 257
    elif field.endswith("count"):
        setattr(inputs[index], field, getattr(inputs[index], field) - 1)
    else:
        setattr(inputs[index], field, ctypes.POINTER(ctypes.c_float)())
    expected = 2 if field in ("weight_count", "bias_count") else 1
    assert_assembly_failure(c_codec, metadata, inputs, storage, expected)


@pytest.mark.parametrize("index", range(4))
@pytest.mark.parametrize("storage_index", range(3))
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_c_assembly_nonfinite_late_failures_are_atomic(
    c_codec, index, storage_index, value
):
    metadata, inputs, storage = assembly_fixture()
    storage[3 * index + storage_index][-1] = value
    assert_assembly_failure(c_codec, metadata, inputs, storage, 6)


@pytest.mark.parametrize("index", range(4))
def test_c_assembly_head_overflow_is_atomic(c_codec, index):
    metadata, inputs, storage = assembly_fixture()
    maximum = struct.unpack("<f", bytes.fromhex("ffff7f7f"))[0]
    storage[3 * index][0] = maximum
    storage[3 * index + 1][0] = maximum
    assert_assembly_failure(c_codec, metadata, inputs, storage, 6)


def test_c_assembly_ignores_input_probabilities_and_clears_unused_output(c_codec):
    metadata, inputs, _storage = assembly_fixture()
    for answer in metadata.answers:
        answer.probabilities[:] = [float("nan")] * 5
    output = CDecision()
    assert (
        c_codec.mc_v0_assemble_decision(
            ctypes.byref(metadata), inputs, 4, ctypes.byref(output)
        )
        == 0
    )
    for answer in output.answers:
        assert all(math.isfinite(value) for value in answer.probabilities)
        assert list(answer.probabilities[answer.option_count :]) == [0] * (
            5 - answer.option_count
        )
    native_verify.native_frame(c_codec, output)


def test_c_assembly_verifier_is_reproducible_and_opt_in(c_codec, tmp_path):
    first = native_verify.verification_evidence(c_codec, cases=16, assembly=True)
    assert first == native_verify.verification_evidence(
        c_codec, cases=16, assembly=True
    )
    assert first["assembled_decisions"] == 16
    assert (
        first["result_sha256"]
        != native_verify.verification_evidence(c_codec, cases=16)["result_sha256"]
    )
    report = native_verify.run_verification(
        tmp_path / "report.json", tmp_path / "work", cases=8, assembly=True
    )
    assert report["scope"]["assembly_reference"] is True
    assert report["evidence"]["assembled_decisions"] == 8
    assert not report["scope"]["model_loaded"]


@pytest.mark.parametrize("assembly", [0, 1, None, "yes"])
def test_c_assembly_verifier_rejects_implicit_opt_in(tmp_path, assembly):
    with pytest.raises(ValueError, match="boolean"):
        native_verify.run_verification(
            tmp_path / "report.json", tmp_path / "work", cases=1, assembly=assembly
        )
    assert not list(tmp_path.iterdir())


def test_c_assembly_verifier_rejects_native_failure(c_codec, monkeypatch):
    monkeypatch.setattr(c_codec, "mc_v0_assemble_decision", lambda *_arguments: 6)
    with pytest.raises(ValueError, match="C decision assembly"):
        native_verify.verification_evidence(c_codec, cases=1, assembly=True)


def test_c_head_row_major_affine_and_spare_capacity(c_codec):
    features = (ctypes.c_float * 3)(1, 2, 3)
    weights = (ctypes.c_float * 9)(2, 0, -1, -1, 1, 2, 0, 0, 0)
    biases = (ctypes.c_float * 3)(1, -2, 4)
    output = (ctypes.c_float * 5)(42, 42, 42, 42, 42)
    originals = [bytes(array) for array in (features, weights, biases)]
    assert (
        c_codec.mc_v0_dense_head(features, 3, weights, 9, biases, 3, 3, output, 5) == 0
    )
    assert list(output) == [0, 5, 4, 42, 42]
    assert [bytes(array) for array in (features, weights, biases)] == originals


def test_c_head_retains_small_cancellation_residual(c_codec):
    largest = struct.unpack("<f", bytes.fromhex("ffff7f7f"))[0]
    features = (ctypes.c_float * 3)(largest, 1, largest)
    weights = (ctypes.c_float * 3)(largest, 1, -largest)
    biases = (ctypes.c_float * 1)(0)
    output = (ctypes.c_float * 1)(42)
    assert (
        c_codec.mc_v0_dense_head(features, 3, weights, 3, biases, 1, 1, output, 1) == 0
    )
    assert output[0] == 1


def test_c_head_retains_nested_cancellation_residual(c_codec):
    features = (ctypes.c_float * 5)(2**120, 2**60, 1, 2**60, 2**120)
    weights = (ctypes.c_float * 5)(2**120, 2**60, 1, -(2**60), -(2**120))
    biases = (ctypes.c_float * 1)(0)
    output = (ctypes.c_float * 1)(42)
    assert (
        c_codec.mc_v0_dense_head(features, 5, weights, 5, biases, 1, 1, output, 1) == 0
    )
    assert (
        output[0]
        == math.fsum(
            float(value) * weight
            for value, weight in zip(features, weights, strict=True)
        )
        == 1
    )


@pytest.mark.parametrize("residual", [1, -1, 2**-149, -(2**-149)])
def test_c_head_shuffled_multiscale_cancellation(c_codec, residual):
    generator = random.Random(20261019)
    terms = [
        (2.0**exponent, sign * 2.0**exponent)
        for exponent in (-120, -60, 0, 60, 120)
        for sign in (-1, 1)
    ] + [(residual, 1)]
    for _ in range(32):
        generator.shuffle(terms)
        features = (ctypes.c_float * 256)(*(value for value, _ in terms))
        weights = (ctypes.c_float * 256)(*(value for _, value in terms))
        bias = (ctypes.c_float * 1)(0)
        output = (ctypes.c_float * 1)(42)
        assert (
            c_codec.mc_v0_dense_head(features, 256, weights, 256, bias, 1, 1, output, 1)
            == 0
        )
        assert output[0] == residual


def test_c_head_later_row_overflow_leaves_all_output_unchanged(c_codec):
    largest = struct.unpack("<f", bytes.fromhex("ffff7f7f"))[0]
    features = (ctypes.c_float * 2)(largest, largest)
    weights = (ctypes.c_float * 4)(1, -1, 1, 1)
    biases = (ctypes.c_float * 2)(0, 0)
    output = (ctypes.c_float * 3)(42, 42, 42)
    before = bytes(output)
    assert (
        c_codec.mc_v0_dense_head(features, 2, weights, 4, biases, 2, 2, output, 3) != 0
    )
    assert bytes(output) == before


@pytest.mark.parametrize(
    "feature_count,output_count",
    [
        (0, 1),
        (257, 1),
        (1, 0),
        (1, 6),
        (ctypes.c_size_t(-1).value, 1),
        (1, ctypes.c_size_t(-1).value),
    ],
)
def test_c_head_rejects_dimensions_before_access(c_codec, feature_count, output_count):
    source = (ctypes.c_float * 1)(1)
    output = (ctypes.c_float * 1)(42)
    assert (
        c_codec.mc_v0_dense_head(
            source, feature_count, source, 1, source, 1, output_count, output, 1
        )
        != 0
    )
    assert output[0] == 42


@pytest.mark.parametrize("field", [0, 2, 4, 7])
def test_c_head_null_arguments(c_codec, field):
    source = (ctypes.c_float * 1)(1)
    output = (ctypes.c_float * 1)(42)
    arguments = [source, 1, source, 1, source, 1, 1, output, 1]
    arguments[field] = None
    assert c_codec.mc_v0_dense_head(*arguments) != 0
    assert output[0] == 42


@pytest.mark.parametrize("field", [3, 5, 8])
def test_c_head_short_buffers(c_codec, field):
    features = (ctypes.c_float * 2)(1, 2)
    weights = (ctypes.c_float * 4)(1, 2, 3, 4)
    biases = (ctypes.c_float * 2)(0, 0)
    output = (ctypes.c_float * 2)(42, 42)
    arguments = [features, 2, weights, 4, biases, 2, 2, output, 2]
    arguments[field] -= 1
    assert c_codec.mc_v0_dense_head(*arguments) != 0
    assert list(output) == [42, 42]


@pytest.mark.parametrize("storage", ["features", "weights", "biases"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_c_head_rejects_nonfinite_at_every_position(c_codec, storage, value):
    for position in range({"features": 3, "weights": 15, "biases": 5}[storage]):
        arrays = {
            "features": (ctypes.c_float * 3)(1, 2, 3),
            "weights": (ctypes.c_float * 15)(*range(15)),
            "biases": (ctypes.c_float * 5)(*range(5)),
        }
        arrays[storage][position] = value
        before = [bytes(array) for array in arrays.values()]
        output = (ctypes.c_float * 5)(42, 42, 42, 42, 42)
        assert (
            c_codec.mc_v0_dense_head(
                arrays["features"],
                3,
                arrays["weights"],
                15,
                arrays["biases"],
                5,
                5,
                output,
                5,
            )
            != 0
        )
        assert list(output) == [42] * 5
        assert [bytes(array) for array in arrays.values()] == before


@pytest.mark.parametrize("feature_count", [1, 2, 3, 8, 32, 256])
@pytest.mark.parametrize("output_count", [1, 2, 3, 4, 5])
def test_c_head_dimensions_match_exact_dyadic_reference(
    c_codec, feature_count, output_count
):
    generator = random.Random(feature_count * 100 + output_count)
    features = (ctypes.c_float * feature_count)(
        *(generator.randrange(-32, 33) / 16 for _ in range(feature_count))
    )
    weights = (ctypes.c_float * (feature_count * output_count))(
        *(
            generator.randrange(-32, 33) / 32
            for _ in range(feature_count * output_count)
        )
    )
    biases = (ctypes.c_float * output_count)(
        *(generator.randrange(-16, 17) / 16 for _ in range(output_count))
    )
    output = (ctypes.c_float * output_count)()
    assert (
        c_codec.mc_v0_dense_head(
            features,
            feature_count,
            weights,
            len(weights),
            biases,
            output_count,
            output_count,
            output,
            output_count,
        )
        == 0
    )
    expected = [
        ctypes.c_float(
            math.fsum(
                [
                    biases[row],
                    *(
                        float(features[column]) * weights[row * feature_count + column]
                        for column in range(feature_count)
                    ),
                ]
            )
        ).value
        for row in range(output_count)
    ]
    assert list(output) == expected


def test_c_head_ignores_trailing_storage(c_codec):
    features = (ctypes.c_float * 2)(2, float("nan"))
    weights = (ctypes.c_float * 2)(3, float("nan"))
    biases = (ctypes.c_float * 2)(1, float("nan"))
    output = (ctypes.c_float * 2)(42, 42)
    assert (
        c_codec.mc_v0_dense_head(features, 1, weights, 2, biases, 2, 1, output, 2) == 0
    )
    assert list(output) == [7, 42]


@pytest.mark.parametrize("optimization", ["-O0", "-O2", "-Os"])
@pytest.mark.parametrize("assembly", [False, True])
def test_native_build_optimization_parity(c_codec, tmp_path, optimization, assembly):
    codec, record = build_native(tmp_path, optimization=optimization)
    assert optimization in record["argv"]
    assert native_verify.verification_evidence(
        codec, cases=8, assembly=assembly
    ) == native_verify.verification_evidence(c_codec, cases=8, assembly=assembly)


@pytest.mark.parametrize("optimization", ["-O3", "-Ofast", "-O2 -ffast-math", None])
def test_native_build_rejects_unapproved_optimization(tmp_path, optimization):
    with pytest.raises(ValueError, match="optimization"):
        build_native(tmp_path, optimization=optimization)
    assert not list(tmp_path.iterdir())


def test_build_audit_parsers_preserve_meaning():
    assert build_audit.parse_sections(
        "object.o  :\nsection size addr\n.text 7 0\n.bss 3 0\nTotal 10\n"
    ) == [
        {"name": ".text", "bytes": 7, "address": 0},
        {"name": ".bss", "bytes": 3, "address": 0},
    ]
    assert build_audit.parse_undefined("exp U\nweak w\n") == [
        {"name": "exp", "type": "U"},
        {"name": "weak", "type": "w"},
    ]
    assert build_audit.parse_undefined("") == []
    stack = build_audit.parse_stack(
        "file:name.c:10:2:func\t16\tstatic\nother.c:3:1:dynamic_func\t8\tdynamic,bounded\n"
    )
    assert stack[0] == {
        "source": "file:name.c",
        "line": 10,
        "column": 2,
        "function": "func",
        "bytes": 16,
        "qualifier": "static",
    }
    assert stack[1]["qualifier"] == "dynamic,bounded"


@pytest.mark.parametrize(
    "kind,text",
    [
        ("sections", ""),
        ("sections", "o :\nsection size addr\n.text 1 0\nTotal 2"),
        ("sections", "o :\nsection size addr\n.text 1 0\n.text 1 0\nTotal 2"),
        ("sections", "o :\nsection size addr\n.text -1 0\nTotal -1"),
        ("undefined", "function T 1 2"),
        ("undefined", "exp U\nexp U"),
        ("stack", ""),
        ("stack", "f.c:1:1:f\t-1\tstatic"),
        ("stack", "f.c:1:1:f\t8\tunknown"),
        ("stack", "f.c:0:1:f\t8\tstatic"),
        ("stack", "f.c:1:1:f\t8\tstatic\nf.c:1:1:f\t8\tstatic"),
    ],
)
def test_build_audit_rejects_malformed_tool_evidence(kind, text):
    with pytest.raises(ValueError):
        getattr(build_audit, f"parse_{kind}")(text)


@pytest.mark.parametrize("assembly", [False, True])
def test_build_audit_real_matrix(tmp_path, c_codec, assembly):
    if any(shutil.which(name) is None for name in build_audit.TOOLS.values()):
        pytest.skip("reference build-audit tools unavailable")
    output, work = tmp_path / "report.json", tmp_path / "build"
    report = build_audit.run_audit(output, work, cases=8, assembly=assembly)
    assert json.loads(output.read_text()) == report
    assert len(report["objects"]) == 6 * len(native_verify.SOURCES)
    assert len(report["host_runs"]) == 3
    assert len({run["evidence"]["result_sha256"] for run in report["host_runs"]}) == 1
    assert report["scope"]["arm_compile_only"]
    assert not report["scope"]["full_stack_bound"]
    assert report["scope"].get("assembly_reference", False) is assembly
    expected = native_verify.verification_evidence(c_codec, cases=8, assembly=assembly)
    assert all(run["evidence"] == expected for run in report["host_runs"])
    for row in report["objects"]:
        assert row["stack_usage"] and row["sections"]
        if row["target"] == "arm":
            assert row["elf"] == {"class_bits": 32, "machine": 40, "type": "REL"}
    for name, record in report["artifacts"].items():
        assert native_verify.file_record(work / name) == record


@pytest.mark.parametrize(
    "cases,seed", [(0, 1), (1025, 1), (True, 1), (1, -1), (1, 2**32), (1, True)]
)
def test_build_audit_bad_configuration_creates_nothing(tmp_path, cases, seed):
    with pytest.raises(ValueError):
        build_audit.run_audit(
            tmp_path / "report.json", tmp_path / "work", cases=cases, seed=seed
        )
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "kind",
    [
        "same",
        "report_inside",
        "work_inside",
        "existing_report",
        "existing_work",
        "report_symlink",
        "work_symlink",
    ],
)
def test_build_audit_rejects_output_paths_before_tools(tmp_path, monkeypatch, kind):
    report, work = tmp_path / "report.json", tmp_path / "work"
    if kind == "same":
        work = report
    elif kind == "report_inside":
        report = work / "report.json"
    elif kind == "work_inside":
        work = report / "work"
    elif kind == "existing_report":
        report.write_text("original")
    elif kind == "existing_work":
        work.mkdir()
    elif kind.endswith("symlink"):
        (report if kind == "report_symlink" else work).symlink_to(tmp_path / "missing")
    before = list(tmp_path.iterdir())

    def forbidden(_name):
        pytest.fail("preflight must reject before invoking tools")

    monkeypatch.setattr(native_verify, "compiler_identity", forbidden)
    with pytest.raises((ValueError, FileExistsError)):
        build_audit.run_audit(report, work, cases=1)
    assert list(tmp_path.iterdir()) == before
    if kind == "existing_report":
        assert report.read_text() == "original"


def test_build_audit_missing_tool_creates_nothing(tmp_path, monkeypatch):
    monkeypatch.setitem(
        build_audit.TOOLS, "arm_cc", "micro-classifier-missing-compiler"
    )
    with pytest.raises(FileNotFoundError):
        build_audit.run_audit(tmp_path / "report.json", tmp_path / "work", cases=1)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("assembly", [False, True])
def test_build_audit_failed_native_verification_has_no_report(
    tmp_path, monkeypatch, assembly
):
    def fail(*_arguments, **_keywords):
        assert _keywords["assembly"] is assembly
        raise ValueError("injected verification failure")

    monkeypatch.setattr(native_verify, "verification_evidence", fail)
    output, work = tmp_path / "report.json", tmp_path / "work"
    with pytest.raises(ValueError, match="injected"):
        build_audit.run_audit(output, work, cases=1, assembly=assembly)
    assert not output.exists()
    assert (work / "O0/host-verification/build.json").is_file()


@pytest.mark.parametrize("failure", ["exit", "timeout", "launch"])
def test_build_audit_command_failures_keep_diagnostics(tmp_path, monkeypatch, failure):
    def fail(command, **_keywords):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(
                command, 120, output=b"partial out", stderr=b"partial err"
            )
        if failure == "launch":
            raise OSError("injected launch failure")
        return subprocess.CompletedProcess(command, 7, "partial out", "partial err")

    monkeypatch.setattr(native_verify, "run_command", fail)
    output = tmp_path / "command.json"
    with pytest.raises((OSError, subprocess.SubprocessError)):
        build_audit.run_logged(["not-executed"], output)
    record = json.loads(output.read_text())
    assert record["argv"] == ["not-executed"]
    if failure != "launch":
        assert record["stdout"] == "partial out"
        assert record["stderr"] == "partial err"
    else:
        assert "launch_error" in record


@pytest.mark.skipif(sys.platform != "linux", reason="Linux /proc descendant check")
@pytest.mark.parametrize("mode", ["timeout", "interrupted", "parent_exited"])
def test_build_audit_timeout_terminates_descendants(tmp_path, monkeypatch, mode):
    original_popen = subprocess.Popen

    def launch(*arguments, **keywords):
        process = original_popen(*arguments, **keywords)
        communicate = process.communicate

        def bounded_communicate(*arguments, **keywords):
            if keywords.get("timeout") == 120:
                keywords["timeout"] = 1
                if mode == "interrupted":
                    try:
                        return communicate(*arguments, **keywords)
                    except subprocess.TimeoutExpired:
                        raise KeyboardInterrupt from None
            return communicate(*arguments, **keywords)

        process.communicate = bounded_communicate
        return process

    monkeypatch.setattr(build_audit.subprocess, "Popen", launch)
    command = [
        sys.executable,
        "-c",
        """
import os
import sys
read_fd, write_fd = os.pipe()
child = os.fork()
if child:
    print(child, flush=True)
    print('fixture-ready', file=sys.stderr, flush=True)
    if sys.argv[1] == 'parent_exited':
        os._exit(0)
os.read(read_fd, 1)
""",
        mode,
    ]
    descendant = None
    try:
        expected = (
            KeyboardInterrupt if mode == "interrupted" else subprocess.TimeoutExpired
        )
        with pytest.raises(expected) as caught:
            build_audit.run_logged(command, tmp_path / "command.json")
        descendant = int(build_audit.diagnostic_text(caught.value.stdout).strip())
        record = json.loads((tmp_path / "command.json").read_text())
        assert record["stdout"] == f"{descendant}\n"
        assert record["stderr"] == "fixture-ready\n"
        assert record["interrupted" if mode == "interrupted" else "timed_out"] is True
        status = Path(f"/proc/{descendant}/stat")
        running = (
            status.exists() and status.read_text().rsplit(")", 1)[1].split()[0] != "Z"
        )
        assert not running, "timed-out command left a running descendant"
    finally:
        if descendant is not None:
            try:
                os.kill(descendant, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_native_command_preserves_output_and_closed_stdin():
    result = native_verify.run_command(
        [
            sys.executable,
            "-c",
            "import sys; print(repr(sys.stdin.read())); print('diagnostic', file=sys.stderr)",
        ]
    )
    assert result.returncode == 0
    assert result.stdout == "''\n"
    assert result.stderr == "diagnostic\n"


@pytest.mark.parametrize("check", [False, True])
def test_native_command_nonzero_preserves_diagnostics(check):
    command = [
        sys.executable,
        "-c",
        "import sys; print('out'); print('err', file=sys.stderr); sys.exit(7)",
    ]
    if check:
        with pytest.raises(subprocess.CalledProcessError) as caught:
            native_verify.run_command(command, check=True)
        result = caught.value
    else:
        result = native_verify.run_command(command, check=False)
    assert result.returncode == 7
    assert result.stdout == "out\n" and result.stderr == "err\n"


@pytest.mark.parametrize(
    "kind", ["not_elf", "truncated", "wrong_machine", "not_relocatable", "big_endian"]
)
def test_build_audit_rejects_wrong_elf_identity(tmp_path, kind):
    data = bytearray(52)
    data[:7] = b"\x7fELF\x01\x01\x01"
    struct.pack_into("<HH", data, 16, 1, 40)
    if kind == "not_elf":
        data[0] = 0
    elif kind == "truncated":
        data = data[:20]
    elif kind == "wrong_machine":
        struct.pack_into("<H", data, 18, 62)
    elif kind == "not_relocatable":
        struct.pack_into("<H", data, 16, 2)
    else:
        data[5] = 2
    path = tmp_path / "object.o"
    path.write_bytes(data)
    with pytest.raises(ValueError):
        build_audit.elf_identity(path, "arm")


def lightweight_audit(monkeypatch, tmp_path):
    monkeypatch.setattr(build_audit, "OPTIMIZATIONS", ("-O0", "-O2"))
    tool = tmp_path / "compiler"
    tool.write_bytes(b"unchanged tool")
    identity = {
        "path": str(tool),
        "version": "fake-only",
        **native_verify.file_record(tool),
    }
    monkeypatch.setattr(native_verify, "compiler_identity", lambda _name: identity)
    monkeypatch.setattr(
        native_verify,
        "build_native",
        lambda *_arguments, **_keywords: (None, {"argv": []}),
    )
    monkeypatch.setattr(
        native_verify,
        "verification_evidence",
        lambda *_arguments, **_keywords: {"result_sha256": "0" * 64},
    )
    monkeypatch.setattr(
        build_audit, "inspect_object", lambda *_arguments: {"fake_only": True}
    )
    return tool


@pytest.mark.parametrize("assembly", [False, True])
@pytest.mark.parametrize("kind", ["source", "tool", "optimization", "artifact_symlink"])
def test_build_audit_drift_and_mismatch_cannot_produce_report(
    tmp_path, monkeypatch, kind, assembly
):
    tool = lightweight_audit(monkeypatch, tmp_path)
    calls = 0
    original = build_audit.audit_sources()

    def sources():
        nonlocal calls
        calls += 1
        if calls > 1 and kind == "source":
            return {"changed": {"bytes": 0, "sha256": "0" * 64}}
        if calls > 1 and kind == "tool":
            tool.write_bytes(b"changed tool")
        return original

    monkeypatch.setattr(build_audit, "audit_sources", sources)
    if kind == "optimization":
        digests = iter(("0" * 64, "1" * 64))
        monkeypatch.setattr(
            native_verify,
            "verification_evidence",
            lambda *_arguments, **_keywords: {"result_sha256": next(digests)},
        )
    if kind == "artifact_symlink":

        def inspect(directory, *_arguments):
            directory.symlink_to(tool)
            return {"fake_only": True}

        monkeypatch.setattr(build_audit, "inspect_object", inspect)
    output = tmp_path / "report.json"
    with pytest.raises(ValueError):
        build_audit.run_audit(output, tmp_path / "work", cases=1, assembly=assembly)
    assert not output.exists()


def test_build_audit_native_compile_failure_retains_command(tmp_path, monkeypatch):
    lightweight_audit(monkeypatch, tmp_path)

    def fail(*_arguments, **_keywords):
        raise subprocess.CalledProcessError(
            9, ["fake-cc", "-O0"], output="compile output", stderr="compile failure"
        )

    monkeypatch.setattr(native_verify, "build_native", fail)
    output, work = tmp_path / "report.json", tmp_path / "work"
    with pytest.raises(subprocess.CalledProcessError):
        build_audit.run_audit(output, work, cases=1)
    assert not output.exists()
    record = json.loads((work / "O0/host-verification/failure.json").read_text())
    assert record["argv"] == ["fake-cc", "-O0"]
    assert record["stderr"] == "compile failure"


def test_build_audit_interrupted_native_compile_has_no_success_report(
    tmp_path, monkeypatch
):
    lightweight_audit(monkeypatch, tmp_path)

    def fail(*_arguments, **_keywords):
        raise native_verify.CommandInterrupted(
            ["fake-cc", "-O0"], "partial out", "partial err"
        )

    monkeypatch.setattr(native_verify, "build_native", fail)
    output, work = tmp_path / "report.json", tmp_path / "work"
    with pytest.raises(KeyboardInterrupt):
        build_audit.run_audit(output, work, cases=1)
    assert not output.exists()
    record = json.loads((work / "O0/host-verification/failure.json").read_text())
    assert record["interrupted"] is True
    assert record["argv"] == ["fake-cc", "-O0"]
    assert record["stdout"] == "partial out" and record["stderr"] == "partial err"


@pytest.mark.parametrize("assembly", [False, True])
def test_build_audit_cli_under_python_optimization(tmp_path, assembly):
    if any(shutil.which(name) is None for name in build_audit.TOOLS.values()):
        pytest.skip("reference build-audit tools unavailable")
    output = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-O",
            "-m",
            "interface.build_audit",
            *(["--assembly-reference"] if assembly else []),
            "--cases",
            "1",
            "--output",
            str(output),
            "--work-dir",
            str(tmp_path / "work"),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    assert json.loads(result.stdout) == {
        "status": "reference_build_checks_passed",
        "objects": 6 * len(native_verify.SOURCES),
        "host_runs": 3,
    }
    report = json.loads(output.read_text())
    assert not report["scope"]["board_executed"]
    assert report["scope"].get("assembly_reference", False) is assembly
    if assembly:
        assert all(
            run["evidence"]["assembled_decisions"] == 1 for run in report["host_runs"]
        )


@pytest.mark.parametrize("assembly", [0, 1, None, "yes"])
def test_build_audit_rejects_implicit_assembly_before_tools(
    tmp_path, monkeypatch, assembly
):
    def forbidden(_name):
        pytest.fail("invalid assembly mode must reject before invoking tools")

    monkeypatch.setattr(native_verify, "compiler_identity", forbidden)
    with pytest.raises(ValueError, match="boolean"):
        build_audit.run_audit(
            tmp_path / "report.json", tmp_path / "work", cases=1, assembly=assembly
        )
    assert not list(tmp_path.iterdir())


def test_native_verifier_seeded_reproducibility_and_scope(c_codec, tmp_path):
    first = native_verify.verification_evidence(c_codec, cases=16, seed=20261019)
    assert first == native_verify.verification_evidence(
        c_codec, cases=16, seed=20261019
    )
    assert (
        first["result_sha256"]
        != native_verify.verification_evidence(c_codec, cases=16, seed=20261020)[
            "result_sha256"
        ]
    )
    assert first["question_outputs"] == 64
    assert first["frames"] == 32
    assert {row["feature_count"] for row in first["cases"]} == {
        1,
        2,
        3,
        8,
        32,
        64,
        128,
        256,
    }
    report = native_verify.run_verification(
        tmp_path / "report.json", tmp_path / "work", cases=2
    )
    assert json.loads((tmp_path / "report.json").read_text()) == report
    assert report["scope"] == {
        "synthetic_only": True,
        "training_enabled": False,
        "task_data": False,
        "model_loaded": False,
        "board_executed": False,
        "safety_qualified": False,
        "target_runtime_qualified": False,
    }
    assert report["build"]["sources"] == native_verify.source_records()


@pytest.mark.parametrize(
    "cases,seed", [(0, 1), (1025, 1), (True, 1), (1, -1), (1, 2**32), (1, True)]
)
def test_native_verifier_rejects_configuration_before_creation(tmp_path, cases, seed):
    with pytest.raises(ValueError):
        native_verify.run_verification(
            tmp_path / "report.json", tmp_path / "work", cases=cases, seed=seed
        )
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("kind", ["same", "report_inside", "work_inside"])
def test_native_verifier_rejects_containing_paths_before_creation(tmp_path, kind):
    report = tmp_path / "report.json"
    work = (
        report
        if kind == "same"
        else report / "work"
        if kind == "work_inside"
        else tmp_path
    )
    if kind == "report_inside":
        work = tmp_path / "work"
        report = work / "report.json"
    with pytest.raises(ValueError):
        native_verify.run_verification(report, work, cases=1)
    assert not list(tmp_path.iterdir())


def test_native_verifier_existing_outputs_are_not_overwritten(tmp_path):
    report = tmp_path / "report.json"
    report.write_text("original")
    with pytest.raises(FileExistsError):
        native_verify.run_verification(report, tmp_path / "work", cases=1)
    assert report.read_text() == "original"
    assert not (tmp_path / "work").exists()
    work = tmp_path / "existing"
    work.mkdir()
    library = work / "native.so"
    library.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        native_verify.build_native(work)
    assert library.read_bytes() == b"original"


@pytest.mark.parametrize("which", ["report", "work"])
def test_native_verifier_rejects_symlinks(tmp_path, which):
    report, work = tmp_path / "report.json", tmp_path / "work"
    path = report if which == "report" else work
    path.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="symlinks"):
        native_verify.run_verification(report, work, cases=1)
    assert path.is_symlink()
    assert not (tmp_path / "missing").exists()


def test_native_verifier_missing_compiler_creates_nothing(tmp_path):
    with pytest.raises(FileNotFoundError):
        native_verify.run_verification(
            tmp_path / "report.json",
            tmp_path / "work",
            cases=1,
            compiler="micro-classifier-missing-compiler",
        )
    assert not list(tmp_path.iterdir())


def test_native_verifier_native_failure_is_not_accepted(c_codec, monkeypatch):
    monkeypatch.setattr(c_codec, "mc_v0_dense_head", lambda *_arguments: 6)
    with pytest.raises(ValueError, match="affine arithmetic"):
        native_verify.verification_evidence(c_codec, cases=1)


def test_native_verifier_failed_run_has_no_success_report(tmp_path, monkeypatch):
    def fail(*_arguments, **_keywords):
        raise ValueError("injected failure")

    monkeypatch.setattr(native_verify, "verification_evidence", fail)
    with pytest.raises(ValueError, match="injected failure"):
        native_verify.run_verification(
            tmp_path / "report.json", tmp_path / "work", cases=1
        )
    assert not (tmp_path / "report.json").exists()
    assert (tmp_path / "work/native.so").exists()


def test_native_verifier_source_drift_is_rejected(tmp_path, monkeypatch):
    initial = native_verify.source_records()
    calls = 0

    def records():
        nonlocal calls
        calls += 1
        return (
            initial
            if calls == 1
            else {**initial, "changed": {"sha256": "0" * 64, "bytes": 0}}
        )

    monkeypatch.setattr(native_verify, "source_records", records)
    with pytest.raises(ValueError, match="changed during compilation"):
        native_verify.build_native(tmp_path)


@pytest.mark.parametrize("assembly", [False, True])
def test_native_verifier_cli_works_under_python_optimization(tmp_path, assembly):
    output = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-O",
            "-m",
            "interface.native_verify",
            *(["--assembly-reference"] if assembly else []),
            "--cases",
            "2",
            "--output",
            str(output),
            "--work-dir",
            str(tmp_path / "work"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["status"] == "synthetic_checks_passed"
    report = json.loads(output.read_text())
    assert report["evidence"]["question_outputs"] == 8
    assert report["scope"].get("assembly_reference", False) is assembly
    evidence = dict(report["evidence"])
    digest = evidence.pop("result_sha256")
    assert (
        digest
        == hashlib.sha256(
            json.dumps(
                evidence, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
    )


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
    source = c_state_from_python(expected)
    original = bytes(source)
    encoded = c_buffer(b"\xa5" * 128)
    written = ctypes.c_size_t(999)
    assert (
        c_codec.mc_v0_encode_state(
            ctypes.byref(source), encoded, len(encoded), ctypes.byref(written)
        )
        == 0
    )
    assert bytes(encoded[: written.value]) == frame
    assert bytes(encoded[written.value :]) == b"\xa5" * (128 - len(frame))
    assert bytes(source) == original


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


def test_c_codec_state_encode_capacity_and_null_arguments(c_codec):
    source = c_state_from_python(State())
    output = c_buffer(b"\xa5" * 130)
    written = ctypes.c_size_t(999)
    original = bytes(output)
    target = ctypes.cast(ctypes.byref(output, 1), ctypes.POINTER(ctypes.c_uint8))
    for capacity in range(92):
        assert (
            c_codec.mc_v0_encode_state(
                ctypes.byref(source), target, capacity, ctypes.byref(written)
            )
            != 0
        )
        assert bytes(output) == original
        assert written.value == 999
    assert c_codec.mc_v0_encode_state(None, target, 128, ctypes.byref(written)) != 0
    assert (
        c_codec.mc_v0_encode_state(
            ctypes.byref(source), None, 128, ctypes.byref(written)
        )
        != 0
    )
    assert c_codec.mc_v0_encode_state(ctypes.byref(source), target, 128, None) != 0
    assert bytes(output) == original and written.value == 999
    assert (
        c_codec.mc_v0_encode_state(
            ctypes.byref(source), target, 92, ctypes.byref(written)
        )
        == 0
    )
    assert written.value == 92
    assert bytes(output[1:93]) == encode_state(State())
    assert bytes(output[:1]) + bytes(output[93:]) == b"\xa5" * 38


@pytest.mark.parametrize(
    "changes",
    [
        {"validity": 32},
        {"task_id": 2},
        {"ages_us": (UINT32_MAX,) * 5},
        {"ages_us": (0,) * 5},
        {"goal_m": (float("nan"), 0, 0)},
        {"velocity_m_s": (float("inf"), 0, 0)},
        {"faults": 1},
        {"validity": 31, "ages_us": (0,) * 5, "battery_fraction": 1.1},
    ],
)
def test_c_codec_state_encode_rejects_invalid_without_writes(c_codec, changes):
    packet = replace(State(), **changes)
    with pytest.raises(ProtocolError):
        encode_state(packet)
    source = c_state_from_python(packet)
    original_source = bytes(source)
    output = c_buffer(b"\xa5" * 128)
    written = ctypes.c_size_t(999)
    assert (
        c_codec.mc_v0_encode_state(
            ctypes.byref(source), output, len(output), ctypes.byref(written)
        )
        != 0
    )
    assert bytes(output) == b"\xa5" * 128
    assert written.value == 999 and bytes(source) == original_source


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
    source = c_decision_from_python(expected)
    original = bytes(source)
    encoded = c_buffer(b"\xa5" * 128)
    written = ctypes.c_size_t(999)
    assert (
        c_codec.mc_v0_encode_decision(
            ctypes.byref(source), encoded, len(encoded), ctypes.byref(written)
        )
        == 0
    )
    assert bytes(encoded[: written.value]) == frame
    assert bytes(encoded[written.value :]) == b"\xa5" * (128 - len(frame))
    assert bytes(source) == original


@pytest.mark.parametrize("status", list(Status))
def test_c_codec_decision_encode_all_subsets(c_codec, status):
    for mask in range(16):
        packet = replace(
            full_decision(),
            status=status,
            answers=tuple(
                answer
                for answer in full_decision().answers
                if mask & (1 << (answer.question_id - 1))
            ),
        )
        if status == Status.OK and mask != 15:
            continue
        source = c_decision_from_python(packet)
        original = bytes(source)
        output = c_buffer(b"\xa5" * 128)
        written = ctypes.c_size_t(999)
        assert (
            c_codec.mc_v0_encode_decision(
                ctypes.byref(source), output, len(output), ctypes.byref(written)
            )
            == 0
        )
        frame = bytes(output[: written.value])
        assert frame == encode_decision(packet)
        assert decode_decision(frame) == packet
        assert bytes(source) == original
        assert bytes(output[written.value :]) == b"\xa5" * (128 - len(frame))


def test_c_codec_decision_encode_capacity_and_null_arguments(c_codec):
    for packet in (Decision(), full_decision()):
        source = c_decision_from_python(packet)
        frame = encode_decision(packet)
        output = c_buffer(b"\xa5" * 130)
        target = ctypes.cast(ctypes.byref(output, 1), ctypes.POINTER(ctypes.c_uint8))
        written = ctypes.c_size_t(999)
        original = bytes(output)
        for capacity in range(len(frame)):
            assert (
                c_codec.mc_v0_encode_decision(
                    ctypes.byref(source), target, capacity, ctypes.byref(written)
                )
                != 0
            )
            assert bytes(output) == original and written.value == 999
        assert (
            c_codec.mc_v0_encode_decision(None, target, 128, ctypes.byref(written)) != 0
        )
        assert (
            c_codec.mc_v0_encode_decision(
                ctypes.byref(source), None, 128, ctypes.byref(written)
            )
            != 0
        )
        assert (
            c_codec.mc_v0_encode_decision(ctypes.byref(source), target, 128, None) != 0
        )
        assert bytes(output) == original and written.value == 999
        assert (
            c_codec.mc_v0_encode_decision(
                ctypes.byref(source), target, len(frame), ctypes.byref(written)
            )
            == 0
        )
        assert written.value == len(frame)
        assert bytes(output[1 : 1 + written.value]) == frame
        assert bytes(output[:1]) + bytes(output[1 + written.value :]) == b"\xa5" * (
            130 - len(frame)
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", 6),
        ("catalogue_version", 1),
        ("model_version", 0),
        ("answer_mask", 16),
        ("answer_mask", 7),
        ("question_id", 2),
        ("answer_type", 2),
        ("selected", 2),
        ("option_count", 0),
        ("option_count", 255),
        ("probability", float("nan")),
        ("probability", float("inf")),
        ("probability", -0.1),
        ("probability", 0.8),
    ],
)
def test_c_codec_decision_encode_rejects_invalid_without_writes(c_codec, field, value):
    source = c_decision_from_python(full_decision())
    if field == "probability":
        source.answers[0].probabilities[0] = value
    elif field in {name for name, _ in CAnswer._fields_}:
        setattr(source.answers[0], field, value)
    else:
        setattr(source, field, value)
    original_source = bytes(source)
    output = c_buffer(b"\xa5" * 128)
    written = ctypes.c_size_t(999)
    assert (
        c_codec.mc_v0_encode_decision(
            ctypes.byref(source), output, len(output), ctypes.byref(written)
        )
        != 0
    )
    assert bytes(output) == b"\xa5" * 128
    assert written.value == 999 and bytes(source) == original_source


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
        assert c_encoded_frame(c_codec, c_state_from_python(packet)) == frame


@pytest.mark.parametrize("compiler", ["cc", "arm-none-eabi-gcc"])
@pytest.mark.parametrize(
    "source_name",
    [
        "micro_classifier_codec.c",
        "micro_classifier_history.c",
        "micro_classifier_math.c",
        "micro_classifier_heads.c",
        "micro_classifier_assembly.c",
    ],
)
def test_c_codec_compiles_to_host_and_cortex_m55_objects(
    tmp_path, compiler, source_name
):
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
            str(ROOT / "firmware" / source_name),
            "-o",
            str(tmp_path / "codec.o"),
        ],
        capture_output=True,
        check=True,
    )


@pytest.mark.parametrize("flag", ["-ffast-math", "-ffinite-math-only"])
@pytest.mark.parametrize(
    "source_name",
    [
        "micro_classifier_codec.c",
        "micro_classifier_math.c",
        "micro_classifier_heads.c",
        "micro_classifier_assembly.c",
    ],
)
def test_c_codec_rejects_fast_math_build(tmp_path, flag, source_name):
    if shutil.which("cc") is None:
        pytest.skip("host C compiler unavailable")
    result = subprocess.run(
        [
            "cc",
            "-std=c11",
            flag,
            "-I",
            str(HEADER_PATH.parent),
            "-c",
            str(ROOT / "firmware" / source_name),
            "-o",
            str(tmp_path / "unsafe.o"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "fast math is unsupported" in result.stderr


@pytest.mark.parametrize(
    "constant,original,changed",
    [
        ("PROFILE_VERSION", 0, 1),
        ("MODE_OPTION_COUNT", 5, 6),
        ("MAX_FRAME_SIZE", 128, 129),
    ],
)
def test_c_codec_requires_review_when_contract_layout_changes(
    tmp_path, constant, original, changed
):
    if shutil.which("cc") is None:
        pytest.skip("host C compiler unavailable")
    header = HEADER_PATH.read_text()
    old = f"#define MC_V0_{constant} UINT32_C({original})"
    assert old in header
    (tmp_path / HEADER_PATH.name).write_text(
        header.replace(old, f"#define MC_V0_{constant} UINT32_C({changed})")
    )
    shutil.copyfile(
        HEADER_PATH.parent / "micro_classifier_codec.h",
        tmp_path / "micro_classifier_codec.h",
    )
    result = subprocess.run(
        [
            "cc",
            "-std=c11",
            "-I",
            str(tmp_path),
            "-c",
            str(ROOT / "firmware/micro_classifier_codec.c"),
            "-o",
            str(tmp_path / "changed-contract.o"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "static assertion failed" in result.stderr


def feed_c_stream(codec, stream, chunks):
    captured = []

    def capture(packet, context):
        captured.append((bytes(packet.contents), context))

    callback = CPacketHandler(capture)
    for chunk in chunks:
        assert (
            codec.mc_v0_stream_feed(
                ctypes.byref(stream), c_buffer(chunk), len(chunk), callback, 0x1234
            )
            == 0
        )
        assert 0 <= stream.used < 128
    packets = []
    for data, context in captured:
        assert context == 0x1234
        packet = CPacket.from_buffer_copy(data)
        if packet.kind == 1:
            values = {}
            for name, _ in CState._fields_:
                value = getattr(packet.body.state, name)
                values[name] = (
                    tuple(value) if isinstance(value, ctypes.Array) else value
                )
            packets.append(State(**values))
        else:
            assert packet.kind == 2
            decision = packet.body.decision
            packets.append(
                Decision(
                    sequence=decision.sequence,
                    timestamp_us=decision.timestamp_us,
                    latency_us=decision.latency_us,
                    status=decision.status,
                    model_version=decision.model_version,
                    catalogue_version=decision.catalogue_version,
                    answers=tuple(
                        Answer(
                            answer.question_id,
                            tuple(answer.probabilities)[: answer.option_count],
                            answer.selected,
                        )
                        for index, answer in enumerate(decision.answers)
                        if decision.answer_mask & (1 << index)
                    ),
                )
            )
    return packets


def test_c_codec_stream_all_golden_chunk_boundaries(c_codec):
    wire = b"noiseM" + b"".join(bytes.fromhex(vector["hex"]) for vector in GOLDEN)
    expected = FrameDecoder().feed(wire)
    assert len(expected) == len(GOLDEN)
    for boundary in range(len(wire) + 1):
        stream = CStream()
        c_codec.mc_v0_stream_init(ctypes.byref(stream))
        assert (
            feed_c_stream(c_codec, stream, (wire[:boundary], wire[boundary:]))
            == expected
        )
        assert stream.used == stream.rejected_frames == 0
    stream = CStream()
    c_codec.mc_v0_stream_init(ctypes.byref(stream))
    assert (
        feed_c_stream(
            c_codec, stream, (wire[index : index + 1] for index in range(len(wire)))
        )
        == expected
    )
    assert stream.used == 0


def test_c_codec_stream_recovers_each_corrupted_golden_byte(c_codec):
    recovery = encode_state(State(sequence=123)) + encode_decision(
        Decision(sequence=124)
    )
    for vector in GOLDEN:
        original = bytes.fromhex(vector["hex"])
        for index in range(len(original)):
            broken = bytearray(original)
            broken[index] ^= 1
            wire = broken + b"\x00" * 128 + recovery
            expected_stream = FrameDecoder()
            expected = expected_stream.feed(wire)
            stream = CStream()
            c_codec.mc_v0_stream_init(ctypes.byref(stream))
            assert feed_c_stream(c_codec, stream, (wire,)) == expected
            assert [packet.sequence for packet in expected[-2:]] == [123, 124]
            assert stream.rejected_frames == expected_stream.rejected_frames
            assert stream.used == 0


def test_c_codec_stream_rejects_valid_crc_semantic_and_length_faults(c_codec):
    faults = []
    for offset, code, value in (
        (3, "B", 3),
        (4, "H", 65535),
        (8, "H", 2),
        (44, "f", float("nan")),
    ):
        frame = bytearray(encode_state(State()))
        struct.pack_into("<" + code, frame, offset, value)
        faults.append(with_crc(frame))
    frame = bytearray(encode_decision(full_decision()))
    struct.pack_into("<f", frame, 52, 0.5)
    faults.append(with_crc(frame))
    wire = b"noise".join(faults) + encode_state(State(sequence=5))
    reference = FrameDecoder()
    expected = reference.feed(wire)
    stream = CStream()
    c_codec.mc_v0_stream_init(ctypes.byref(stream))
    assert feed_c_stream(c_codec, stream, (wire,)) == expected == [State(sequence=5)]
    assert stream.rejected_frames == reference.rejected_frames >= len(faults)


def test_c_codec_stream_drains_nested_packets_after_one_final_byte(c_codec):
    candidate = bytearray(128)
    candidate[: HEADER.size] = HEADER.pack(b"MC", 0, 2, 104, 0, 1, 0, 0, 0)
    candidate[20:56] = encode_decision(Decision(sequence=1))
    candidate[56:92] = encode_decision(Decision(sequence=2))
    stream = CStream()
    c_codec.mc_v0_stream_init(ctypes.byref(stream))
    assert feed_c_stream(c_codec, stream, (candidate[:-1],)) == []
    assert feed_c_stream(c_codec, stream, (candidate[-1:],)) == [
        Decision(sequence=1),
        Decision(sequence=2),
    ]
    assert stream.rejected_frames == 1
    assert stream.used == 0


def test_c_codec_stream_noise_saturation_and_explicit_reset(c_codec):
    stream = CStream()
    c_codec.mc_v0_stream_init(ctypes.byref(stream))
    assert feed_c_stream(c_codec, stream, (b"M" * 100000,)) == []
    assert stream.used == 1
    c_codec.mc_v0_stream_init(ctypes.byref(stream))
    frame = encode_state(State())
    assert feed_c_stream(c_codec, stream, (frame[:30],)) == []
    assert stream.used == 30
    c_codec.mc_v0_stream_init(ctypes.byref(stream))
    assert stream.used == stream.rejected_frames == 0
    broken = bytearray(frame)
    broken[-1] ^= 1
    stream.rejected_frames = UINT32_MAX
    assert feed_c_stream(c_codec, stream, (broken + frame,)) == [State()]
    assert stream.rejected_frames == UINT32_MAX
    c_codec.mc_v0_stream_init(None)


def test_c_codec_stream_bad_arguments_do_not_consume_input(c_codec):
    stream = CStream()
    c_codec.mc_v0_stream_init(ctypes.byref(stream))
    captured = []
    callback = CPacketHandler(
        lambda packet, context: captured.append(bytes(packet.contents))
    )
    frame = c_buffer(encode_state(State()))
    original = bytes(stream)
    assert c_codec.mc_v0_stream_feed(None, frame, len(frame), callback, None) != 0
    assert c_codec.mc_v0_stream_feed(ctypes.byref(stream), None, 1, callback, None) != 0
    assert (
        c_codec.mc_v0_stream_feed(
            ctypes.byref(stream), frame, len(frame), CPacketHandler(), None
        )
        != 0
    )
    assert bytes(stream) == original
    assert c_codec.mc_v0_stream_feed(ctypes.byref(stream), None, 0, callback, None) == 0
    stream.used = 128
    invalid = bytes(stream)
    assert (
        c_codec.mc_v0_stream_feed(
            ctypes.byref(stream), frame, len(frame), callback, None
        )
        != 0
    )
    assert bytes(stream) == invalid
    assert captured == []


@pytest.mark.parametrize(
    "offset,delta,accepted",
    [
        (40, 16, True),
        (40, 17, False),
        (40, -16, True),
        (40, -17, False),
        (52, 66, True),
        (52, 67, False),
        (52, -67, True),
        (52, -68, False),
    ],
)
def test_c_codec_probability_and_confidence_tolerance_edges(
    c_codec, offset, delta, accepted
):
    frame = bytearray(encode_decision(full_decision()))
    bits = struct.unpack_from("<I", frame, offset)[0]
    struct.pack_into("<I", frame, offset, bits + delta)
    frame = with_crc(frame)
    if accepted:
        decode_decision(frame)
    else:
        with pytest.raises(ProtocolError):
            decode_decision(frame)
    output = CDecision()
    assert (
        c_codec.mc_v0_decode_decision(c_buffer(frame), len(frame), ctypes.byref(output))
        == 0
    ) == accepted


def test_c_codec_seeded_valid_crc_differential(c_codec):
    generator = random.Random(20261019)
    accepted = rejected = 0
    for _ in range(2000):
        vector = generator.choice(GOLDEN)
        frame = bytearray.fromhex(vector["hex"])
        for _ in range(generator.randrange(1, 5)):
            frame[generator.randrange(len(frame) - 4)] = generator.randrange(256)
        frame = with_crc(frame)
        if vector["kind"] == "state":
            python_decode, native_decode, output = (
                decode_state,
                c_codec.mc_v0_decode_state,
                CState(),
            )
        else:
            python_decode, native_decode, output = (
                decode_decision,
                c_codec.mc_v0_decode_decision,
                CDecision(),
            )
        try:
            python_decode(frame)
        except ProtocolError:
            expected = False
            rejected += 1
        else:
            expected = True
            accepted += 1
        result = native_decode(c_buffer(frame), len(frame), ctypes.byref(output))
        assert (result == 0) == expected
    assert accepted > 0 and rejected > 0


def test_c_codec_seeded_mixed_stream_differential(c_codec):
    generator = random.Random(20261019)
    chunks = []
    for index in range(120):
        frame = bytearray.fromhex(generator.choice(GOLDEN)["hex"])
        if index % 3:
            frame[generator.randrange(len(frame))] ^= 0x80
            if index % 3 == 2:
                frame = with_crc(frame)
        chunks.append(generator.randbytes(generator.randrange(32)) + frame)
    wire = b"".join(chunks) + b"\x00" * 128 + encode_state(State(sequence=9))
    reference = FrameDecoder()
    stream = CStream()
    c_codec.mc_v0_stream_init(ctypes.byref(stream))
    offset = count = 0
    while offset < len(wire):
        size = generator.randrange(1, 80)
        chunk = wire[offset : offset + size]
        expected = reference.feed(chunk)
        assert feed_c_stream(c_codec, stream, (chunk,)) == expected
        count += len(expected)
        assert bytes(stream.buffer[: stream.used]) == bytes(reference.buffer)
        assert stream.rejected_frames == reference.rejected_frames
        offset += size
    assert count > 1
    assert stream.used == 0


@pytest.mark.parametrize("kind", ["state", "decision"])
def test_c_codec_seeded_bidirectional_round_trips(c_codec, kind):
    generator = random.Random(20261019)
    frames, packets = [], []

    def finite_float32():
        bits = generator.getrandbits(32)
        if bits & 0x7F800000 == 0x7F800000:
            bits ^= 0x00800000
        return struct.unpack("<f", struct.pack("<I", bits))[0]

    for _ in range(500):
        if kind == "state":
            validity = generator.randrange(32)
            vectors = [
                tuple(finite_float32() for _ in range(3))
                if validity & (1 << group)
                else (0, 0, 0)
                for group in range(3)
            ]
            packet = State(
                sequence=generator.getrandbits(32),
                timestamp_us=generator.getrandbits(32),
                validity=validity,
                ages_us=tuple(
                    generator.randrange(UINT32_MAX)
                    if validity & (1 << group)
                    else UINT32_MAX
                    for group in range(5)
                ),
                velocity_m_s=vectors[0],
                angular_velocity_rad_s=vectors[1],
                goal_m=vectors[2],
                battery_fraction=generator.random() if validity & 8 else 0,
                faults=generator.getrandbits(32) if validity & 16 else 0,
            )
            source = c_state_from_python(packet)
            expected = encode_state(packet)
            python_decode, native_decode, received = (
                decode_state,
                c_codec.mc_v0_decode_state,
                CState(),
            )
        else:
            status = generator.choice(list(Status))
            mask = 15 if status == Status.OK else generator.randrange(16)
            answers = []
            for question, (_, options) in QUESTIONS.items():
                if not mask & (1 << (question - 1)):
                    continue
                weights = [generator.randrange(33) for _ in options]
                weights[generator.randrange(len(options))] += 1
                total = sum(weights)
                answers.append(
                    Answer(
                        question,
                        tuple(weight / total for weight in weights),
                        generator.randrange(len(options)),
                    )
                )
            packet = Decision(
                sequence=generator.getrandbits(32),
                timestamp_us=generator.getrandbits(32),
                latency_us=generator.getrandbits(32),
                status=status,
                model_version=generator.randrange(1, 65536)
                if status == Status.OK
                else generator.randrange(65536),
                answers=tuple(answers),
            )
            source = c_decision_from_python(packet)
            expected = encode_decision(packet)
            python_decode, native_decode, received = (
                decode_decision,
                c_codec.mc_v0_decode_decision,
                CDecision(),
            )
        frame = c_encoded_frame(c_codec, source)
        assert frame == expected
        assert native_decode(c_buffer(frame), len(frame), ctypes.byref(received)) == 0
        assert c_encoded_frame(c_codec, received) == frame
        frames.append(frame)
        packets.append(python_decode(expected))
    wire = b"".join(frames)
    assert FrameDecoder().feed(wire) == packets
    stream = CStream()
    c_codec.mc_v0_stream_init(ctypes.byref(stream))
    assert (
        feed_c_stream(
            c_codec,
            stream,
            (wire[offset : offset + 17] for offset in range(0, len(wire), 17)),
        )
        == packets
    )
    assert stream.used == stream.rejected_frames == 0


@pytest.mark.parametrize("offset,delta", [(36, 1), (36, -1), (52, 66), (52, -67)])
def test_c_codec_encode_canonicalizes_received_confidence(c_codec, offset, delta):
    canonical = encode_decision(full_decision())
    frame = bytearray(canonical)
    bits = struct.unpack_from("<I", frame, offset)[0]
    struct.pack_into("<I", frame, offset, bits + delta)
    frame = with_crc(frame)
    assert frame != canonical
    expected = encode_decision(decode_decision(frame))
    source = CDecision()
    assert (
        c_codec.mc_v0_decode_decision(c_buffer(frame), len(frame), ctypes.byref(source))
        == 0
    )
    assert c_encoded_frame(c_codec, source) == expected == canonical


def test_c_codec_encode_ignores_absent_slots_and_unused_probability_storage(c_codec):
    packet = Decision(answers=(Answer(1, (0.75, 0.25), 1),))
    source = c_decision_from_python(packet)
    for index in (1, 2, 3):
        ctypes.memset(ctypes.byref(source.answers[index]), 0xA5, ctypes.sizeof(CAnswer))
    source.answers[0].probabilities[2:] = [float("nan"), float("inf"), -1]
    assert c_encoded_frame(c_codec, source) == encode_decision(packet)


def test_c_codec_address_and_undefined_sanitizers(tmp_path):
    if shutil.which("cc") is None:
        pytest.skip("host C compiler unavailable")
    declarations = []
    for index, vector in enumerate(GOLDEN):
        values = ",".join(str(value) for value in bytes.fromhex(vector["hex"]))
        declarations.append(f"static const uint8_t vector_{index}[] = {{{values}}};")
    pointers = ",".join(f"vector_{index}" for index in range(len(GOLDEN)))
    sizes = ",".join(f"sizeof(vector_{index})" for index in range(len(GOLDEN)))
    source = '#include "micro_classifier_assembly.h"\n#include "micro_classifier_heads.h"\n#include "micro_classifier_math.h"\n#include "micro_classifier_history.h"\n#include <assert.h>\n#include <float.h>\n#include <math.h>\n#include <stdlib.h>\n#include <string.h>\n'
    source += "\n".join(declarations)
    source += f"\nstatic const uint8_t *const frames[] = {{{pointers}}};\n"
    source += f"static const size_t lengths[] = {{{sizes}}};\n"
    source += r"""
static void receive(const mc_v0_packet *packet, void *context) {
    size_t *count = context;
    assert(packet->kind == MC_V0_KIND_STATE || packet->kind == MC_V0_KIND_DECISION);
    ++*count;
}
static void check_history(void) {
    mc_v0_state_history history;
    mc_v0_state_window window;
    mc_v0_state expected[8] = {{0}};
    mc_v0_state zero = {0};
    mc_v0_state state = {0};
    uint8_t present[8] = {0};
    unsigned char before[sizeof(history)];
    unsigned char output_before[sizeof(window)];
    state.task_id = MC_V0_TASK_GOAL_REACHING;
    for (size_t group = 0; group < 5; ++group) {
        state.ages_us[group] = MC_V0_UNKNOWN_AGE_US;
    }
    mc_v0_state_history_init(&history);
    for (uint32_t iteration = 0; iteration < 1024; ++iteration) {
        unsigned operation = iteration % 19;
        state.sequence = UINT32_MAX - iteration;
        state.timestamp_us = iteration % 3 ? iteration * 10 : 0;
        state.validity = iteration % 2 ? MC_V0_VALID_VELOCITY : 0;
        state.ages_us[0] = state.validity ? iteration : MC_V0_UNKNOWN_AGE_US;
        state.velocity_m_s[0] = state.validity ? (float)iteration / 64.0f : -0.0f;
        if (operation == 0) {
            mc_v0_state_history_init(&history);
            memset(expected, 0, sizeof(expected));
            memset(present, 0, sizeof(present));
        } else if (operation == 4) {
            mc_v0_state bad = state;
            bad.goal_m[0] = NAN;
            memcpy(before, &history, sizeof(history));
            assert(mc_v0_state_history_push(&history, &bad) == MC_V0_ERROR_STATE);
            assert(memcmp(before, &history, sizeof(history)) == 0);
        } else {
            memmove(expected, expected + 1, 7 * sizeof(expected[0]));
            memmove(present, present + 1, 7 * sizeof(present[0]));
            if (operation < 4) {
                assert(mc_v0_state_history_gap(&history) == MC_V0_HISTORY_OK);
                memset(&expected[7], 0, sizeof(expected[7]));
                present[7] = 0;
            } else {
                assert(mc_v0_state_history_push(&history, &state) == MC_V0_HISTORY_OK);
                expected[7] = state;
                present[7] = 1;
            }
        }
        memcpy(before, &history, sizeof(history));
        assert(mc_v0_state_history_snapshot(&history, &window) == MC_V0_HISTORY_OK);
        assert(memcmp(before, &history, sizeof(history)) == 0);
        unsigned mask = 0;
        for (size_t index = 0; index < 8; ++index) {
            if (present[index]) {
                uint8_t actual_frame[MC_V0_STATE_FRAME_SIZE];
                uint8_t expected_frame[MC_V0_STATE_FRAME_SIZE];
                size_t actual_written = 0, expected_written = 0;
                assert(mc_v0_encode_state(&window.samples[index], actual_frame, sizeof(actual_frame), &actual_written) == MC_V0_ENCODE_OK);
                assert(mc_v0_encode_state(&expected[index], expected_frame, sizeof(expected_frame), &expected_written) == MC_V0_ENCODE_OK);
                assert(actual_written == expected_written);
                assert(memcmp(actual_frame, expected_frame, actual_written) == 0);
                mask |= 1u << index;
            } else {
                assert(memcmp(&window.samples[index], &zero, sizeof(zero)) == 0);
            }
        }
        assert(window.valid_mask == mask);
        memset(&window, 0xA5, sizeof(window));
        assert(memcmp(before, &history, sizeof(history)) == 0);
    }
    for (unsigned cursor = 8; cursor < 256; ++cursor) {
        history.next = (uint8_t)cursor;
        memcpy(before, &history, sizeof(history));
        memset(&window, 0xA5, sizeof(window));
        memcpy(output_before, &window, sizeof(window));
        assert(mc_v0_state_history_push(&history, &state) == MC_V0_ERROR_ARGUMENT);
        assert(mc_v0_state_history_gap(&history) == MC_V0_ERROR_ARGUMENT);
        assert(mc_v0_state_history_snapshot(&history, &window) == MC_V0_ERROR_ARGUMENT);
        assert(memcmp(before, &history, sizeof(history)) == 0);
        assert(memcmp(output_before, &window, sizeof(window)) == 0);
    }
    mc_v0_state_history_init(&history);
    memcpy(before, &history, sizeof(history));
    assert(mc_v0_validate_state(NULL) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_state_history_push(NULL, &state) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_state_history_push(&history, NULL) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_state_history_gap(NULL) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_state_history_snapshot(NULL, &window) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_state_history_snapshot(&history, NULL) == MC_V0_ERROR_ARGUMENT);
    mc_v0_state_history_init(NULL);
    assert(memcmp(before, &history, sizeof(history)) == 0);
}
static void check_math(void) {
    static const size_t counts[] = {2, 4, 5};
    static const float invalid[] = {NAN, INFINITY, -INFINITY};
    for (size_t group = 0; group < 3; ++group) {
        size_t count = counts[group];
        float *logits = malloc(count * sizeof(*logits));
        assert(logits != NULL);
        for (size_t index = 0; index < count; ++index) {
            logits[index] = index % 2 ? -FLT_MAX : FLT_MAX;
        }
        unsigned char source_before[5 * sizeof(float)];
        memcpy(source_before, logits, count * sizeof(*logits));
        for (size_t capacity = 0; capacity <= count + 1; ++capacity) {
            size_t bytes = capacity * sizeof(float);
            float *output = malloc(bytes ? bytes : 1);
            assert(output != NULL);
            memset(output, 0xA5, bytes);
            mc_v0_result result = mc_v0_softmax(logits, count, output, capacity);
            assert((result == MC_V0_MATH_OK) == (capacity >= count));
            if (result == MC_V0_MATH_OK) {
                double total = 0.0;
                for (size_t index = 0; index < count; ++index) {
                    assert(isfinite(output[index]) && output[index] >= 0 && output[index] <= 1);
                    total += output[index];
                }
                assert(fabs(total - 1.0) <= 1e-6);
            }
            size_t start = result == MC_V0_MATH_OK ? count * sizeof(float) : 0;
            for (size_t offset = start; offset < bytes; ++offset) {
                assert(((unsigned char *)output)[offset] == 0xA5);
            }
            memset(output, 0xA5, bytes);
            result = mc_v0_sigmoid(FLT_MAX, output, capacity);
            assert((result == MC_V0_MATH_OK) == (capacity >= 2));
            if (result == MC_V0_MATH_OK) {
                assert(output[0] == 0.0f && output[1] == 1.0f);
            }
            start = result == MC_V0_MATH_OK ? 2 * sizeof(float) : 0;
            for (size_t offset = start; offset < bytes; ++offset) {
                assert(((unsigned char *)output)[offset] == 0xA5);
            }
            assert(memcmp(source_before, logits, count * sizeof(*logits)) == 0);
            free(output);
        }
        for (size_t position = 0; position < count; ++position) {
            for (size_t kind = 0; kind < 3; ++kind) {
                float output[5] = {42, 42, 42, 42, 42};
                logits[position] = invalid[kind];
                assert(mc_v0_softmax(logits, count, output, 5) == MC_V0_ERROR_DECISION);
                assert(mc_v0_sigmoid(invalid[kind], output, 5) == MC_V0_ERROR_DECISION);
                for (size_t index = 0; index < 5; ++index) {
                    assert(output[index] == 42);
                }
                memcpy(logits, source_before, count * sizeof(*logits));
            }
        }
        free(logits);
    }
    float logits[5] = {0};
    float output[5] = {42, 42, 42, 42, 42};
    for (size_t count = 0; count < 256; ++count) {
        memset(output, 0xA5, sizeof(output));
        mc_v0_result result = mc_v0_softmax(logits, count, output, 5);
        assert((result == MC_V0_MATH_OK) == (count == 2 || count == 4 || count == 5));
        if (result != MC_V0_MATH_OK) {
            for (size_t offset = 0; offset < sizeof(output); ++offset) {
                assert(((unsigned char *)output)[offset] == 0xA5);
            }
        }
    }
    memset(output, 0xA5, sizeof(output));
    assert(mc_v0_softmax(logits, SIZE_MAX, output, 5) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_softmax(NULL, 5, output, 5) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_softmax(logits, 5, NULL, 5) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_sigmoid(0, NULL, 5) == MC_V0_ERROR_ARGUMENT);
    for (size_t offset = 0; offset < sizeof(output); ++offset) {
        assert(((unsigned char *)output)[offset] == 0xA5);
    }
    mc_v0_answer answer = {0};
    answer.question_id = MC_V0_QUESTION_CLEAR_SECTOR;
    answer.answer_type = MC_V0_TYPE_CHOICE;
    answer.option_count = 4;
    answer.selected = 3;
    answer.confidence = NAN;
    for (size_t index = 0; index < 4; ++index) {
        answer.probabilities[index] = 0.25f;
    }
    answer.probabilities[4] = NAN;
    uint8_t *metadata[] = {&answer.question_id, &answer.answer_type, &answer.option_count, &answer.selected};
    const uint8_t initial[] = {MC_V0_QUESTION_CLEAR_SECTOR, MC_V0_TYPE_CHOICE, 4, 3};
    for (size_t field = 0; field < 4; ++field) {
        for (unsigned value = 0; value < 256; ++value) {
            *metadata[field] = (uint8_t)value;
            unsigned char before[sizeof(answer)];
            memcpy(before, &answer, sizeof(answer));
            double confidence = 42;
            int valid = field == 3 ? value < 4 : value == initial[field];
            mc_v0_result result = mc_v0_answer_confidence(&answer, &confidence);
            assert((result == MC_V0_MATH_OK) == valid);
            assert(confidence == (valid ? 0.0 : 42.0));
            assert(memcmp(before, &answer, sizeof(answer)) == 0);
        }
        *metadata[field] = initial[field];
    }
    double confidence = 42;
    assert(mc_v0_answer_confidence(NULL, &confidence) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_answer_confidence(&answer, NULL) == MC_V0_ERROR_ARGUMENT);
    assert(confidence == 42);
}
static void check_heads(void) {
    const size_t dimensions[] = {1, 3, 256};
    for (size_t shape = 0; shape < 3; ++shape) {
        size_t count = dimensions[shape];
        float *features = malloc(count * sizeof(float));
        assert(features != NULL);
        for (size_t index = 0; index < count; ++index) {
            features[index] = 1;
        }
        for (size_t rows = 1; rows <= 5; ++rows) {
            for (unsigned field = 0; field < 3; ++field) {
                size_t required = field == 0 ? count * rows : rows;
                for (size_t length = 0; length <= required + 1; ++length) {
                    size_t weight_count = field == 0 ? length : count * rows;
                    size_t bias_count = field == 1 ? length : rows;
                    size_t capacity = field == 2 ? length : rows;
                    float *weights = malloc(weight_count ? weight_count * sizeof(float) : 1);
                    float *biases = malloc(bias_count ? bias_count * sizeof(float) : 1);
                    float *output = malloc(capacity ? capacity * sizeof(float) : 1);
                    assert(weights != NULL && biases != NULL && output != NULL);
                    for (size_t index = 0; index < weight_count; ++index) {
                        weights[index] = index < count * rows ? 1.0f : NAN;
                    }
                    for (size_t index = 0; index < bias_count; ++index) {
                        biases[index] = index < rows ? 0.25f : NAN;
                    }
                    for (size_t index = 0; index < capacity; ++index) {
                        output[index] = 42;
                    }
                    mc_v0_result result = mc_v0_dense_head(features, count, weights, weight_count, biases, bias_count, rows, output, capacity);
                    assert((result == MC_V0_HEAD_OK) == (length >= required));
                    for (size_t index = 0; index < capacity; ++index) {
                        assert(output[index] == (result == MC_V0_HEAD_OK && index < rows ? (float)count + 0.25f : 42.0f));
                    }
                    free(output);
                    free(biases);
                    free(weights);
                }
            }
        }
        free(features);
    }
    float features[256] = {0}, weights[256] = {0}, bias = 0, output = 42;
    features[0] = 0x1p120f; weights[0] = 0x1p120f;
    features[1] = 0x1p60f; weights[1] = 0x1p60f;
    features[2] = 1; weights[2] = 1;
    features[3] = 0x1p60f; weights[3] = -0x1p60f;
    features[4] = 0x1p120f; weights[4] = -0x1p120f;
    assert(mc_v0_dense_head(features, 256, weights, 256, &bias, 1, 1, &output, 1) == MC_V0_HEAD_OK);
    assert(output == 1);
    float overflowing_features[2] = {FLT_MAX, FLT_MAX};
    float overflowing_weights[4] = {1, -1, 1, 1};
    float biases[2] = {0, 0}, outputs[2] = {42, 42};
    assert(mc_v0_dense_head(overflowing_features, 2, overflowing_weights, 4, biases, 2, 2, outputs, 2) == MC_V0_ERROR_DECISION);
    assert(outputs[0] == 42 && outputs[1] == 42);
    const float invalid[] = {NAN, INFINITY, -INFINITY};
    for (size_t kind = 0; kind < 3; ++kind) {
        for (size_t field = 0; field < 3; ++field) {
            float source[3] = {1, 1, 0};
            source[field] = invalid[kind];
            output = 42;
            assert(mc_v0_dense_head(source, 1, source + 1, 1, source + 2, 1, 1, &output, 1) == MC_V0_ERROR_DECISION);
            assert(output == 42);
        }
    }
    float one = 1;
    output = 42;
    assert(mc_v0_dense_head(NULL, 1, &one, 1, &one, 1, 1, &output, 1) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_dense_head(&one, 1, NULL, 1, &one, 1, 1, &output, 1) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_dense_head(&one, 1, &one, 1, NULL, 1, 1, &output, 1) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_dense_head(&one, 1, &one, 1, &one, 1, 1, NULL, 1) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_dense_head(&one, SIZE_MAX, &one, 1, &one, 1, 1, &output, 1) == MC_V0_ERROR_ARGUMENT);
    assert(mc_v0_dense_head(&one, 1, &one, 1, &one, 1, SIZE_MAX, &output, 1) == MC_V0_ERROR_ARGUMENT);
    assert(output == 42);
}
static void assembly_result(const mc_v0_decision *metadata, const mc_v0_head_input *inputs,
                            mc_v0_result expected) {
    mc_v0_decision *output = malloc(sizeof(*output));
    unsigned char before[sizeof(*output)], metadata_before[sizeof(*metadata)];
    unsigned char inputs_before[4 * sizeof(*inputs)];
    assert(output != NULL);
    memset(output, 0xA5, sizeof(*output));
    memcpy(before, output, sizeof(before));
    memcpy(metadata_before, metadata, sizeof(metadata_before));
    memcpy(inputs_before, inputs, sizeof(inputs_before));
    assert(mc_v0_assemble_decision(metadata, inputs, 4, output) == expected);
    assert(memcmp(metadata_before, metadata, sizeof(metadata_before)) == 0);
    assert(memcmp(inputs_before, inputs, sizeof(inputs_before)) == 0);
    if (expected != MC_V0_ASSEMBLY_OK) {
        assert(memcmp(before, output, sizeof(before)) == 0);
    } else {
        uint8_t frame[MC_V0_MAX_FRAME_SIZE];
        size_t written = 0;
        assert(output->status == metadata->status && output->model_version == metadata->model_version);
        for (size_t question = 0; question < 4; ++question) {
            assert(output->answers[question].selected == metadata->answers[question].selected);
        }
        assert(mc_v0_encode_decision(output, frame, sizeof(frame), &written) == MC_V0_ENCODE_OK);
        assert(written == MC_V0_MAX_FRAME_SIZE);
    }
    free(output);
}
static void check_assembly(void) {
    const uint8_t counts[4] = {2, 4, 4, 5};
    const uint8_t types[4] = {MC_V0_TYPE_NOUL, MC_V0_TYPE_CHOICE, MC_V0_TYPE_SCORE, MC_V0_TYPE_CHOICE};
    const size_t dimensions[3] = {1, 3, 256};
    mc_v0_decision metadata = {0};
    metadata.status = MC_V0_STATUS_FAULT;
    metadata.model_version = 1;
    metadata.answer_mask = 15;
    for (size_t question = 0; question < 4; ++question) {
        metadata.answers[question].question_id = (uint8_t)(question + 1);
        metadata.answers[question].answer_type = types[question];
        metadata.answers[question].option_count = counts[question];
        metadata.answers[question].selected = (uint8_t)(counts[question] - 1);
        metadata.answers[question].confidence = NAN;
        for (size_t option = 0; option < 5; ++option) {
            metadata.answers[question].probabilities[option] = NAN;
        }
    }
    for (size_t shape = 0; shape < 3; ++shape) {
        size_t count = dimensions[shape];
        float *features = malloc(count * sizeof(float));
        mc_v0_head_input *inputs = malloc(4 * sizeof(*inputs));
        assert(features != NULL && inputs != NULL);
        for (size_t index = 0; index < count; ++index) {
            features[index] = 1;
        }
        for (size_t question = 0; question < 4; ++question) {
            size_t rows = question == 0 ? 1 : counts[question];
            float *weights = calloc(count * rows, sizeof(float));
            float *biases = calloc(rows, sizeof(float));
            assert(weights != NULL && biases != NULL);
            inputs[question] = (mc_v0_head_input){features, count, weights, count * rows, biases, rows};
        }
        assembly_result(&metadata, inputs, MC_V0_ASSEMBLY_OK);
        for (size_t question = 0; question < 4; ++question) {
            mc_v0_head_input original = inputs[question];
            size_t rows = question == 0 ? 1 : counts[question];
            for (size_t field = 0; field < 2; ++field) {
                size_t required = field == 0 ? count * rows : rows;
                for (size_t length = 0; length <= required + 1; ++length) {
                    float *short_buffer = malloc(length ? length * sizeof(float) : 1);
                    assert(short_buffer != NULL);
                    for (size_t index = 0; index < length; ++index) {
                        short_buffer[index] = index < required ? 0 : NAN;
                    }
                    if (field == 0) {
                        inputs[question].weights = short_buffer;
                        inputs[question].weight_count = length;
                    } else {
                        inputs[question].biases = short_buffer;
                        inputs[question].bias_count = length;
                    }
                    assembly_result(&metadata, inputs, length < required ? MC_V0_ERROR_LENGTH : MC_V0_ASSEMBLY_OK);
                    inputs[question] = original;
                    free(short_buffer);
                }
            }
            const float invalid[3] = {NAN, INFINITY, -INFINITY};
            float *targets[3] = {features, (float *)original.weights, (float *)original.biases};
            for (size_t field = 0; field < 3; ++field) {
                float saved = targets[field][0];
                for (size_t kind = 0; kind < 3; ++kind) {
                    targets[field][0] = invalid[kind];
                    assembly_result(&metadata, inputs, MC_V0_ERROR_DECISION);
                }
                targets[field][0] = saved;
            }
            features[0] = FLT_MAX;
            ((float *)original.weights)[0] = FLT_MAX;
            assembly_result(&metadata, inputs, MC_V0_ERROR_DECISION);
            features[0] = 1;
            ((float *)original.weights)[0] = 0;
            inputs[question].feature_count = 0;
            assembly_result(&metadata, inputs, MC_V0_ERROR_ARGUMENT);
            inputs[question].feature_count = SIZE_MAX;
            assembly_result(&metadata, inputs, MC_V0_ERROR_ARGUMENT);
            inputs[question] = original;
            for (unsigned value = 0; value < 256; ++value) {
                metadata.answers[question].option_count = (uint8_t)value;
                assembly_result(&metadata, inputs, value == counts[question] ? MC_V0_ASSEMBLY_OK : MC_V0_ERROR_DECISION);
            }
            metadata.answers[question].option_count = counts[question];
            for (unsigned value = 0; value < 256; ++value) {
                metadata.answers[question].selected = (uint8_t)value;
                assembly_result(&metadata, inputs, value < counts[question] ? MC_V0_ASSEMBLY_OK : MC_V0_ERROR_DECISION);
            }
            metadata.answers[question].selected = (uint8_t)(counts[question] - 1);
        }
        for (size_t length = 0; length <= 5; ++length) {
            mc_v0_head_input *short_inputs = malloc(length ? length * sizeof(*short_inputs) : 1);
            assert(short_inputs != NULL);
            for (size_t index = 0; index < length; ++index) {
                short_inputs[index] = inputs[index % 4];
            }
            mc_v0_decision output;
            memset(&output, 0xA5, sizeof(output));
            assert(mc_v0_assemble_decision(&metadata, short_inputs, length, &output) ==
                   (length == 4 ? MC_V0_ASSEMBLY_OK : MC_V0_ERROR_ARGUMENT));
            free(short_inputs);
        }
        mc_v0_decision output;
        assert(mc_v0_assemble_decision(NULL, inputs, 4, &output) == MC_V0_ERROR_ARGUMENT);
        assert(mc_v0_assemble_decision(&metadata, NULL, 4, &output) == MC_V0_ERROR_ARGUMENT);
        assert(mc_v0_assemble_decision(&metadata, inputs, 4, NULL) == MC_V0_ERROR_ARGUMENT);
        for (size_t question = 0; question < 4; ++question) {
            free((void *)inputs[question].weights);
            free((void *)inputs[question].biases);
        }
        free(inputs);
        free(features);
    }
}
int main(void) {
    check_assembly();
    check_heads();
    check_math();
    check_history();
    mc_v0_state state;
    mc_v0_decision decision;
    mc_v0_stream stream;
    size_t received = 0;
    uint32_t seed = UINT32_C(20261019);
    assert(mc_v0_crc32(NULL, 0) == 0);
    mc_v0_stream_init(&stream);
    for (size_t index = 0; index < sizeof(lengths) / sizeof(lengths[0]); ++index) {
        if (frames[index][MC_V0_HEADER_KIND_OFFSET] == MC_V0_KIND_STATE) {
            assert(mc_v0_decode_state(frames[index], lengths[index], &state) == MC_V0_DECODE_OK);
        } else {
            assert(mc_v0_decode_decision(frames[index], lengths[index], &decision) == MC_V0_DECODE_OK);
        }
        for (size_t capacity = 0; capacity <= lengths[index] + 1; ++capacity) {
            uint8_t *encoded = malloc(capacity ? capacity : 1);
            assert(encoded != NULL);
            memset(encoded, 0xA5, capacity);
            size_t written = SIZE_MAX;
            mc_v0_result result;
            if (frames[index][MC_V0_HEADER_KIND_OFFSET] == MC_V0_KIND_STATE) {
                result = mc_v0_encode_state(&state, encoded, capacity, &written);
            } else {
                result = mc_v0_encode_decision(&decision, encoded, capacity, &written);
            }
            if (capacity < lengths[index]) {
                assert(result != MC_V0_ENCODE_OK && written == SIZE_MAX);
                for (size_t offset = 0; offset < capacity; ++offset) {
                    assert(encoded[offset] == 0xA5);
                }
            } else {
                assert(result == MC_V0_ENCODE_OK && written == lengths[index]);
                assert(memcmp(encoded, frames[index], written) == 0);
                if (capacity > written) {
                    assert(encoded[written] == 0xA5);
                }
            }
            free(encoded);
        }
        for (size_t length = 0; length <= lengths[index] + 1; ++length) {
            uint8_t *data = malloc(length ? length : 1);
            assert(data != NULL);
            memset(data, 0, length);
            memcpy(data, frames[index], length < lengths[index] ? length : lengths[index]);
            mc_v0_result result;
            if (frames[index][MC_V0_HEADER_KIND_OFFSET] == MC_V0_KIND_STATE) {
                result = mc_v0_decode_state(data, length, &state);
            } else {
                result = mc_v0_decode_decision(data, length, &decision);
            }
            assert((result == MC_V0_DECODE_OK) == (length == lengths[index]));
            assert(mc_v0_stream_feed(&stream, data, length, receive, &received) == MC_V0_DECODE_OK);
            assert(stream.used < MC_V0_MAX_FRAME_SIZE);
            free(data);
        }
    }
    for (size_t iteration = 0; iteration < 4096; ++iteration) {
        size_t length = iteration % 257;
        uint8_t *data = malloc(length ? length : 1);
        assert(data != NULL);
        for (size_t index = 0; index < length; ++index) {
            seed ^= seed << 13;
            seed ^= seed >> 17;
            seed ^= seed << 5;
            data[index] = (uint8_t)seed;
        }
        (void)mc_v0_decode_state(data, length, &state);
        (void)mc_v0_decode_decision(data, length, &decision);
        assert(mc_v0_stream_feed(&stream, data, length, receive, &received) == MC_V0_DECODE_OK);
        assert(stream.used < MC_V0_MAX_FRAME_SIZE);
        free(data);
    }
    memset(&decision, 0, sizeof(decision));
    decision.status = MC_V0_STATUS_FAULT;
    decision.answer_mask = 1;
    decision.answers[0].question_id = MC_V0_QUESTION_PATH_BLOCKED;
    decision.answers[0].answer_type = MC_V0_TYPE_NOUL;
    decision.answers[0].probabilities[0] = 0.75f;
    decision.answers[0].probabilities[1] = 0.25f;
    for (unsigned count = 0; count < 256; ++count) {
        uint8_t encoded[MC_V0_MAX_FRAME_SIZE];
        memset(encoded, 0xA5, sizeof(encoded));
        size_t written = SIZE_MAX;
        decision.answers[0].option_count = (uint8_t)count;
        mc_v0_result result = mc_v0_encode_decision(&decision, encoded, sizeof(encoded), &written);
        assert((result == MC_V0_ENCODE_OK) == (count == MC_V0_PATH_BLOCKED_OPTION_COUNT));
        if (result != MC_V0_ENCODE_OK) {
            assert(written == SIZE_MAX);
            for (size_t offset = 0; offset < sizeof(encoded); ++offset) {
                assert(encoded[offset] == 0xA5);
            }
        } else {
            assert(written == 52);
        }
    }
    received = 0;
    mc_v0_stream_init(&stream);
    for (size_t index = 0; index < sizeof(lengths) / sizeof(lengths[0]); ++index) {
        assert(mc_v0_stream_feed(&stream, frames[index], lengths[index], receive, &received) == MC_V0_DECODE_OK);
    }
    assert(received == sizeof(lengths) / sizeof(lengths[0]));
    assert(stream.used == 0);
    return 0;
}
"""
    executable = tmp_path / "codec-sanitized"
    subprocess.run(
        [
            "cc",
            "-std=c11",
            "-O1",
            "-g",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer",
            "-fno-pie",
            "-no-pie",
            "-I",
            str(HEADER_PATH.parent),
            "-x",
            "c",
            "-",
            str(ROOT / "firmware/micro_classifier_codec.c"),
            str(ROOT / "firmware/micro_classifier_history.c"),
            str(ROOT / "firmware/micro_classifier_math.c"),
            str(ROOT / "firmware/micro_classifier_heads.c"),
            str(ROOT / "firmware/micro_classifier_assembly.c"),
            "-o",
            str(executable),
            "-lm",
        ],
        input=source,
        text=True,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        check=True,
        env={
            **os.environ,
            "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1",
            "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1",
        },
    )
