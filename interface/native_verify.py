"""Host-only bindings and synthetic verification; never a deployment runtime."""

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import random
import shutil
import signal
import struct
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from interface.protocol import (
    QUESTIONS,
    Answer,
    Decision,
    FrameDecoder,
    State,
    decode_decision,
    decode_state,
    encode_decision,
    encode_state,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCES = tuple(
    ROOT / "firmware" / f"micro_classifier_{name}.c"
    for name in ("codec", "history", "math", "heads")
)
HEADERS = tuple(
    ROOT / "firmware/include" / f"micro_classifier_{name}.h"
    for name in ("protocol", "codec", "history", "math", "heads")
)


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


class CStateHistory(ctypes.Structure):
    _fields_ = [
        ("samples", CState * 8),
        ("valid_mask", ctypes.c_uint8),
        ("next", ctypes.c_uint8),
    ]


class CStateWindow(ctypes.Structure):
    _fields_ = [("samples", CState * 8), ("valid_mask", ctypes.c_uint8)]


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


class CBody(ctypes.Union):
    _fields_ = [("state", CState), ("decision", CDecision)]


class CPacket(ctypes.Structure):
    _fields_ = [("kind", ctypes.c_uint8), ("body", CBody)]


class CStream(ctypes.Structure):
    _fields_ = [
        ("buffer", ctypes.c_uint8 * 128),
        ("used", ctypes.c_size_t),
        ("rejected_frames", ctypes.c_uint32),
    ]


CPacketHandler = ctypes.CFUNCTYPE(None, ctypes.POINTER(CPacket), ctypes.c_void_p)


def file_record(path):
    data = Path(path).read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def source_records():
    paths = (*SOURCES, *HEADERS, Path(__file__), ROOT / "interface/protocol.py")
    return {str(path.relative_to(ROOT)): file_record(path) for path in paths}


class CommandInterrupted(KeyboardInterrupt):
    def __init__(self, command, stdout, stderr):
        super().__init__("native tool command interrupted")
        self.cmd = command
        self.stdout = stdout
        self.stderr = stderr


def run_command(command, *, cwd=None, env=None, timeout=120, check=True):
    if os.name != "posix":
        raise ValueError("native tool execution requires POSIX process groups")
    with subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except BaseException as error:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
            if isinstance(error, subprocess.TimeoutExpired):
                error.output = stdout
                error.stderr = stderr
            elif isinstance(error, KeyboardInterrupt):
                raise CommandInterrupted(command, stdout, stderr) from error
            raise
    result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    if check:
        result.check_returncode()
    return result


def compiler_identity(compiler):
    executable = shutil.which(compiler)
    if executable is None:
        raise FileNotFoundError(f"compiler unavailable: {compiler}")
    executable = str(Path(executable).resolve())
    version = run_command([executable, "--version"])
    return {
        "path": executable,
        **file_record(executable),
        "version": version.stdout.strip(),
    }


def bind_native(path):
    codec = ctypes.CDLL(str(path))
    byte_pointer = ctypes.POINTER(ctypes.c_uint8)
    float_pointer = ctypes.POINTER(ctypes.c_float)
    signatures = {
        "mc_v0_crc32": (ctypes.c_uint32, [byte_pointer, ctypes.c_size_t]),
        "mc_v0_validate_state": (ctypes.c_int, [ctypes.POINTER(CState)]),
        "mc_v0_answer_confidence": (
            ctypes.c_int,
            [ctypes.POINTER(CAnswer), ctypes.POINTER(ctypes.c_double)],
        ),
        "mc_v0_softmax": (
            ctypes.c_int,
            [float_pointer, ctypes.c_size_t, float_pointer, ctypes.c_size_t],
        ),
        "mc_v0_sigmoid": (
            ctypes.c_int,
            [ctypes.c_float, float_pointer, ctypes.c_size_t],
        ),
        "mc_v0_dense_head": (
            ctypes.c_int,
            [
                float_pointer,
                ctypes.c_size_t,
                float_pointer,
                ctypes.c_size_t,
                float_pointer,
                ctypes.c_size_t,
                ctypes.c_size_t,
                float_pointer,
                ctypes.c_size_t,
            ],
        ),
        "mc_v0_state_history_init": (None, [ctypes.POINTER(CStateHistory)]),
        "mc_v0_state_history_push": (
            ctypes.c_int,
            [ctypes.POINTER(CStateHistory), ctypes.POINTER(CState)],
        ),
        "mc_v0_state_history_gap": (ctypes.c_int, [ctypes.POINTER(CStateHistory)]),
        "mc_v0_state_history_snapshot": (
            ctypes.c_int,
            [ctypes.POINTER(CStateHistory), ctypes.POINTER(CStateWindow)],
        ),
        "mc_v0_decode_state": (
            ctypes.c_int,
            [byte_pointer, ctypes.c_size_t, ctypes.POINTER(CState)],
        ),
        "mc_v0_decode_decision": (
            ctypes.c_int,
            [byte_pointer, ctypes.c_size_t, ctypes.POINTER(CDecision)],
        ),
        "mc_v0_encode_state": (
            ctypes.c_int,
            [
                ctypes.POINTER(CState),
                byte_pointer,
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_size_t),
            ],
        ),
        "mc_v0_encode_decision": (
            ctypes.c_int,
            [
                ctypes.POINTER(CDecision),
                byte_pointer,
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_size_t),
            ],
        ),
        "mc_v0_stream_init": (None, [ctypes.POINTER(CStream)]),
        "mc_v0_stream_feed": (
            ctypes.c_int,
            [
                ctypes.POINTER(CStream),
                byte_pointer,
                ctypes.c_size_t,
                CPacketHandler,
                ctypes.c_void_p,
            ],
        ),
    }
    for name, (return_type, arguments) in signatures.items():
        function = getattr(codec, name)
        function.argtypes = arguments
        function.restype = return_type
    return codec


def build_native(directory, *, compiler="cc", optimization="-O2"):
    if optimization not in ("-O0", "-O2", "-Os"):
        raise ValueError("native optimization must be -O0, -O2 or -Os")
    directory = Path(directory).resolve()
    if not directory.is_dir():
        raise ValueError("native build requires an existing output directory")
    library = directory / "native.so"
    if library.exists() or library.is_symlink():
        raise FileExistsError("native library output must be fresh")
    identity = compiler_identity(compiler)
    sources = source_records()
    command = [
        identity["path"],
        "-std=c11",
        optimization,
        "-Wall",
        "-Wextra",
        "-Werror",
        "-pedantic",
        "-shared",
        "-fPIC",
        "-I",
        str(ROOT / "firmware/include"),
        *(str(path) for path in SOURCES),
        "-o",
        str(library),
        "-lm",
    ]
    result = run_command(command)
    if (
        source_records() != sources
        or file_record(identity["path"])["sha256"] != identity["sha256"]
    ):
        raise ValueError("native build source or compiler changed during compilation")
    record = {
        "compiler": identity,
        "argv": command,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "sources": sources,
        "library": {"path": str(library), **file_record(library)},
    }
    return bind_native(library), record


def require(condition, message):
    if not condition:
        raise ValueError(f"native verification failed: {message}")


def float_bytes(values):
    return struct.pack(f"<{len(values)}f", *values)


def native_state(packet):
    state = CState()
    for name, field_type in CState._fields_:
        value = getattr(packet, name)
        setattr(
            state,
            name,
            field_type(*value) if issubclass(field_type, ctypes.Array) else value,
        )
    return state


def native_decision(packet):
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


def native_frame(codec, packet):
    output = (ctypes.c_uint8 * 129)(*([0xA5] * 129))
    written = ctypes.c_size_t(0)
    function = (
        codec.mc_v0_encode_state
        if isinstance(packet, CState)
        else codec.mc_v0_encode_decision
    )
    require(
        function(ctypes.byref(packet), output, 128, ctypes.byref(written)) == 0,
        "native frame encode",
    )
    require(
        36 <= written.value <= 128 and output[written.value] == 0xA5,
        "frame size/spare byte",
    )
    return bytes(output[: written.value])


def validate_configuration(cases, seed):
    if type(cases) is not int or not 1 <= cases <= 1024:
        raise ValueError("synthetic cases must be an integer in [1,1024]")
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("synthetic seed must be an unsigned 32-bit integer")


def verification_evidence(codec, *, cases=128, seed=20261019):
    validate_configuration(cases, seed)
    generator = random.Random(seed)
    rows, frames, packets = [], [], []
    max_logit_error = max_probability_error = max_confidence_error = 0.0
    expected_history = [None] * 8
    history, window = CStateHistory(), CStateWindow()
    codec.mc_v0_state_history_init(ctypes.byref(history))
    for case in range(cases):
        count = (1, 2, 3, 8, 32, 64, 128, 256)[case % 8]
        features = (ctypes.c_float * count)(
            *(generator.randrange(-32, 33) / 16 for _ in range(count))
        )
        fixture_digest = hashlib.sha256(float_bytes(features))
        logit_digest = hashlib.sha256()
        answers = []
        for question, (_, options) in QUESTIONS.items():
            output_count = 1 if question == 1 else len(options)
            weights = (ctypes.c_float * (count * output_count))(
                *(
                    generator.randrange(-32, 33) / 32
                    for _ in range(count * output_count)
                )
            )
            biases = (ctypes.c_float * output_count)(
                *(generator.randrange(-16, 17) / 16 for _ in range(output_count))
            )
            fixture_digest.update(struct.pack("<III", question, count, output_count))
            fixture_digest.update(float_bytes(weights))
            fixture_digest.update(float_bytes(biases))
            before = tuple(bytes(value) for value in (features, weights, biases))
            logits = (ctypes.c_float * output_count)()
            require(
                codec.mc_v0_dense_head(
                    features,
                    count,
                    weights,
                    len(weights),
                    biases,
                    output_count,
                    output_count,
                    logits,
                    output_count,
                )
                == 0,
                "affine arithmetic",
            )
            expected = [
                ctypes.c_float(
                    math.fsum(
                        [
                            biases[row],
                            *(
                                float(features[column]) * weights[row * count + column]
                                for column in range(count)
                            ),
                        ]
                    )
                ).value
                for row in range(output_count)
            ]
            require(
                float_bytes(logits) == float_bytes(expected),
                "exact bounded dyadic head reference",
            )
            require(
                tuple(bytes(value) for value in (features, weights, biases)) == before,
                "head input preservation",
            )
            max_logit_error = max(
                max_logit_error,
                *(
                    abs(actual - reference)
                    for actual, reference in zip(logits, expected, strict=True)
                ),
            )
            logit_digest.update(float_bytes(logits))
            probabilities = (ctypes.c_float * len(options))()
            reference_logits = [0.0, logits[0]] if question == 1 else list(logits)
            if question == 1:
                result = codec.mc_v0_sigmoid(logits[0], probabilities, len(options))
            else:
                result = codec.mc_v0_softmax(
                    logits, output_count, probabilities, len(options)
                )
            require(result == 0, "normalization")
            maximum = max(reference_logits)
            unnormalized = [math.exp(value - maximum) for value in reference_logits]
            reference_probabilities = [
                value / sum(unnormalized) for value in unnormalized
            ]
            for actual, reference in zip(
                probabilities, reference_probabilities, strict=True
            ):
                require(math.isfinite(actual) and 0 <= actual <= 1, "probability range")
                error = abs(actual - reference)
                require(
                    error <= 5e-8 + 1e-7 * abs(reference),
                    "test-only normalization tolerance",
                )
                max_probability_error = max(max_probability_error, error)
            require(abs(sum(probabilities) - 1) <= 1e-6, "probability sum")
            selected = max(range(len(options)), key=probabilities.__getitem__)
            answer = Answer(question, tuple(probabilities), selected)
            native = native_decision(Decision(answers=(answer,))).answers[question - 1]
            confidence = ctypes.c_double()
            require(
                codec.mc_v0_answer_confidence(
                    ctypes.byref(native), ctypes.byref(confidence)
                )
                == 0,
                "confidence validation",
            )
            error = abs(confidence.value - answer.confidence)
            require(error <= 2e-15, "shared confidence parity")
            max_confidence_error = max(max_confidence_error, error)
            answers.append(answer)
        state = State(
            sequence=case, timestamp_us=case, goal_m=(features[0], features[-1], 0)
        )
        decision = Decision(sequence=case, timestamp_us=case, answers=tuple(answers))
        pair = []
        for packet, native, encoder, decoder, native_decoder in (
            (
                state,
                native_state(state),
                encode_state,
                decode_state,
                codec.mc_v0_decode_state,
            ),
            (
                decision,
                native_decision(decision),
                encode_decision,
                decode_decision,
                codec.mc_v0_decode_decision,
            ),
        ):
            frame = native_frame(codec, native)
            require(frame == encoder(packet), "exact Python/native frame bytes")
            received = type(native)()
            data = (ctypes.c_uint8 * len(frame)).from_buffer_copy(frame)
            require(
                native_decoder(data, len(frame), ctypes.byref(received)) == 0
                and native_frame(codec, received) == frame,
                "native frame round trip",
            )
            pair.append(frame)
            frames.append(frame)
            packets.append(decoder(frame))
        if case % 37 == 0:
            codec.mc_v0_state_history_init(ctypes.byref(history))
            expected_history = [None] * 8
        if case % 11 == 4:
            require(
                codec.mc_v0_state_history_gap(ctypes.byref(history)) == 0,
                "explicit history gap",
            )
            expected_history = expected_history[1:] + [None]
        else:
            source = native_state(state)
            require(
                codec.mc_v0_state_history_push(
                    ctypes.byref(history), ctypes.byref(source)
                )
                == 0,
                "history push",
            )
            expected_history = expected_history[1:] + [pair[0]]
        before = bytes(history)
        require(
            codec.mc_v0_state_history_snapshot(
                ctypes.byref(history), ctypes.byref(window)
            )
            == 0,
            "history snapshot",
        )
        require(bytes(history) == before, "snapshot preserves history")
        require(
            window.valid_mask
            == sum(
                1 << index
                for index, frame in enumerate(expected_history)
                if frame is not None
            ),
            "chronological history mask",
        )
        for sample, frame in zip(window.samples, expected_history, strict=True):
            require(
                bytes(sample) == bytes(ctypes.sizeof(CState))
                if frame is None
                else native_frame(codec, sample) == frame,
                "history copy/placeholder",
            )
        rows.append(
            {
                "case": case,
                "feature_count": count,
                "input_sha256": fixture_digest.hexdigest(),
                "logits_sha256": logit_digest.hexdigest(),
                "frames_sha256": hashlib.sha256(b"".join(pair)).hexdigest(),
            }
        )
    wire = b"".join(frames)
    decoder = FrameDecoder()
    require(
        decoder.feed(wire) == packets and not decoder.buffer, "Python combined stream"
    )
    stream, received_frames, callback_errors = CStream(), [], []
    codec.mc_v0_stream_init(ctypes.byref(stream))

    @CPacketHandler
    def receive(packet, _context):
        try:
            require(packet.contents.kind in (1, 2), "callback packet kind")
            body = packet.contents.body
            received_frames.append(
                native_frame(
                    codec, body.state if packet.contents.kind == 1 else body.decision
                )
            )
        except (ValueError, TypeError, OSError, ctypes.ArgumentError) as error:
            callback_errors.append(str(error))

    for offset in range(0, len(wire), 137):
        chunk = wire[offset : offset + 137]
        data = (ctypes.c_uint8 * len(chunk)).from_buffer_copy(chunk)
        require(
            codec.mc_v0_stream_feed(
                ctypes.byref(stream), data, len(chunk), receive, None
            )
            == 0,
            "native mixed stream",
        )
    require(not callback_errors, f"callback errors: {callback_errors}")
    require(
        received_frames == frames and stream.used == stream.rejected_frames == 0,
        "native combined stream parity",
    )
    evidence = {
        "seed": seed,
        "synthetic_cases": cases,
        "question_outputs": cases * 4,
        "logits": cases * 14,
        "probabilities": cases * 15,
        "frames": len(frames),
        "max_logit_abs_error_vs_binary32_reference": max_logit_error,
        "max_probability_abs_error_vs_double_reference": max_probability_error,
        "max_confidence_abs_error": max_confidence_error,
        "wire_sha256": hashlib.sha256(wire).hexdigest(),
        "cases": rows,
    }
    payload = json.dumps(
        evidence, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return {**evidence, "result_sha256": hashlib.sha256(payload).hexdigest()}


def run_verification(output, work_dir, *, cases=128, seed=20261019, compiler="cc"):
    validate_configuration(cases, seed)
    output, work_dir = Path(output).expanduser(), Path(work_dir).expanduser()
    if output.is_symlink() or work_dir.is_symlink():
        raise ValueError("verification outputs must not be symlinks")
    output, work_dir = output.resolve(), work_dir.resolve()
    if output.exists() or work_dir.exists():
        raise FileExistsError("verification report and work directory must be fresh")
    if (
        output == work_dir
        or output.is_relative_to(work_dir)
        or work_dir.is_relative_to(output)
    ):
        raise ValueError("report and work directory must not contain each other")
    if shutil.which(compiler) is None:
        raise FileNotFoundError(f"compiler unavailable: {compiler}")
    work_dir.mkdir(parents=True)
    codec, build = build_native(work_dir, compiler=compiler)
    evidence = verification_evidence(codec, cases=cases, seed=seed)
    require(
        source_records() == build["sources"], "source stability through verification"
    )
    report = {
        "schema": "micro-classifier/native-synthetic-verification/1",
        "created_at": datetime.now(UTC).isoformat(),
        "status": "synthetic_checks_passed",
        "scope": {
            "synthetic_only": True,
            "training_enabled": False,
            "task_data": False,
            "model_loaded": False,
            "board_executed": False,
            "safety_qualified": False,
            "target_runtime_qualified": False,
        },
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "byteorder": sys.byteorder,
        },
        "build": build,
        "evidence": evidence,
        "limits": [
            "bounded artificial dyadic fixtures only",
            "not a trained model or production head/blob format",
            "not numerical or memory-safety certification",
            "not task accuracy, calibration, timing, SRAM-fit or board evidence",
            "compiler driver hash is not complete toolchain/library attestation",
            "sanitizer and Arm checks are separate pytest gates, not this CLI",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--cases", type=int, default=128)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--compiler", default="cc")
    arguments = parser.parse_args(argv)
    try:
        report = run_verification(
            arguments.output,
            arguments.work_dir,
            cases=arguments.cases,
            seed=arguments.seed,
            compiler=arguments.compiler,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f"native verification failed: {error}\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "result_sha256": report["evidence"]["result_sha256"],
                "synthetic_cases": report["evidence"]["synthetic_cases"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
