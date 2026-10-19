"""Host-only bindings and synthetic verification; never a deployment runtime."""

import ctypes
import hashlib
import shutil
import subprocess
from pathlib import Path

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


def compiler_identity(compiler):
    executable = shutil.which(compiler)
    if executable is None:
        raise FileNotFoundError(f"compiler unavailable: {compiler}")
    executable = str(Path(executable).resolve())
    version = subprocess.run(
        [executable, "--version"],
        text=True,
        capture_output=True,
        check=True,
        timeout=120,
    )
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


def build_native(directory, *, compiler="cc"):
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
        "-O2",
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
    subprocess.run(command, capture_output=True, text=True, check=True, timeout=120)
    if (
        source_records() != sources
        or file_record(identity["path"])["sha256"] != identity["sha256"]
    ):
        raise ValueError("native build source or compiler changed during compilation")
    record = {
        "compiler": identity,
        "argv": command,
        "sources": sources,
        "library": {"path": str(library), **file_record(library)},
    }
    return bind_native(library), record
