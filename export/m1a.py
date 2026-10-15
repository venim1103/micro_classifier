"""Prepare untrained, static-shape M1a compiler experiments on the CPU."""

import argparse
import hashlib
import json
import platform
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch
from onnxruntime.quantization import (
    CalibrationDataReader,
    QuantFormat,
    QuantType,
    quant_pre_process,
    quantize_static,
)
from torch import nn

OPSET = 13
SMOKE_MAX_ABS_ERROR = 0.15
PROBE_PURPOSES = {
    "temporal_height": "3x1 Conv, temporal height; pool/Gather outside the graph",
    "temporal_width": "1x3 Conv, temporal width; equivalent weights and logical data",
    "temporal_height_pool": "Temporal height with fixed average pooling in graph",
    "temporal_width_pool": "Temporal width with fixed average pooling in graph",
    "state_mlp": "Small numeric MLP, synthetic state-history-sized input",
    "tof": "Two-channel 8x8 spatial Conv probe, not a sensor normalization contract",
    "camera": "RGB 64x64 Conv probe, not an approved camera input profile",
    "gather_inside": "Embedding Gather before the height Conv; compare with temporal_height",
    "transformer": "One small transformer block; mapping/fallback deliberately unknown",
}


@dataclass(frozen=True)
class Probe:
    model: nn.Module
    shape: tuple[int, ...]
    dtype: str = "float32"
    opset: int = OPSET


def conv_probe(layout, seed=0):
    """Equivalent temporal convolutions in height and width orientations."""
    if layout not in ("height", "width"):
        raise ValueError("layout must be height or width")
    kernel = (3, 1) if layout == "height" else (1, 3)
    padding = (1, 0) if layout == "height" else (0, 1)
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(seed)
        model = nn.Sequential(
            nn.Conv2d(96, 24, kernel, padding=padding, device="cpu"),
            nn.ReLU(),
            nn.Conv2d(24, 48, kernel, padding=padding, device="cpu"),
            nn.ReLU(),
        )
    return model.requires_grad_(False).eval()


class GatherConv(nn.Module):
    def __init__(self, seed):
        super().__init__()
        self.convs = conv_probe("height", seed)
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(seed)
            self.embedding = nn.Embedding(256, 96, device="cpu")

    def forward(self, tokens):
        embedded = self.embedding(tokens).transpose(1, 2).unsqueeze(-1)
        return self.convs(embedded)


def make_probe(name, seed=0):
    if name not in PROBE_PURPOSES:
        raise ValueError(f"unsupported probe: {name}")
    if name.startswith("temporal_"):
        layout = "height" if name.startswith("temporal_height") else "width"
        shape = (1, 96, 128, 1) if layout == "height" else (1, 96, 1, 128)
        model = conv_probe(layout, seed)
        if name.endswith("_pool"):
            model = nn.Sequential(model, nn.AvgPool2d(shape[2:]))
        return Probe(model.eval(), shape)
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(seed)
        if name == "state_mlp":
            model = nn.Sequential(
                nn.Linear(32, 48, device="cpu"),
                nn.ReLU(),
                nn.Linear(48, 16, device="cpu"),
            )
            shape = (1, 32)
        elif name in ("tof", "camera"):
            channels, size, stride = (2, 8, 1) if name == "tof" else (3, 64, 2)
            model = nn.Sequential(
                nn.Conv2d(channels, 24, 3, stride=stride, padding=1, device="cpu"),
                nn.ReLU(),
                nn.Conv2d(24, 48, 3, stride=2, padding=1, device="cpu"),
                nn.ReLU(),
                nn.AvgPool2d(size // stride // 2),
            )
            shape = (1, channels, size, size)
        elif name == "gather_inside":
            model = GatherConv(seed)
            return Probe(model.requires_grad_(False).eval(), (1, 128), "int64")
        else:
            model = nn.Sequential(
                nn.TransformerEncoderLayer(
                    d_model=32,
                    nhead=4,
                    dim_feedforward=64,
                    dropout=0,
                    activation="relu",
                    batch_first=True,
                    device="cpu",
                )
            )
            return Probe(model.requires_grad_(False).eval(), (1, 8, 32), opset=17)
    return Probe(model.requires_grad_(False).eval(), shape)


def graph_info(path):
    """Check the graph and require fixed, positive input/output dimensions."""
    model = onnx.load(path)
    onnx.checker.check_model(model, full_check=True)
    shapes = {}
    for value in (*model.graph.input, *model.graph.output):
        dimensions = value.type.tensor_type.shape.dim
        if not dimensions or any(
            dimension.WhichOneof("value") != "dim_value" or dimension.dim_value <= 0
            for dimension in dimensions
        ):
            raise ValueError(f"dynamic or nonpositive shape: {value.name}")
        shapes[value.name] = [dimension.dim_value for dimension in dimensions]
    return {
        "shapes": shapes,
        "operators": sorted({node.op_type for node in model.graph.node}),
        "opsets": {entry.domain: entry.version for entry in model.opset_import},
        "initializer_bytes": sum(
            len(value.raw_data) for value in model.graph.initializer
        ),
    }


def export_float(model, sample, path, opset=OPSET):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fastpath = torch.backends.mha.get_fastpath_enabled()
    try:
        torch.backends.mha.set_fastpath_enabled(False)
        torch.onnx.export(
            model,
            (sample,),
            str(path),
            input_names=["input"],
            output_names=["output"],
            opset_version=opset,
            dynamo=False,
            external_data=False,
        )
    finally:
        torch.backends.mha.set_fastpath_enabled(fastpath)
    return graph_info(path)


def synthetic_feeds(shape, count, seed, dtype="float32"):
    """Seeded smoke tensors only, never representative calibration data."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("sample count must be a positive integer")
    if dtype not in ("float32", "int64"):
        raise ValueError("unsupported probe input dtype")
    generator = np.random.default_rng(seed)
    return [
        {
            "input": (
                generator.uniform(-1, 1, size=shape).astype(np.float32)
                if dtype == "float32"
                else generator.integers(0, 256, size=shape, dtype=np.int64)
            )
        }
        for _ in range(count)
    ]


def feed_digest(feeds):
    digest = hashlib.sha256()
    for feed in feeds:
        for name, array in sorted(feed.items()):
            digest.update(name.encode("utf-8"))
            digest.update(str((array.dtype.str, array.shape)).encode("ascii"))
            digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


class CalibrationReader(CalibrationDataReader):
    def __init__(self, feeds):
        self.feeds = feeds
        self.rewind()

    def get_next(self):
        return next(self.iterator, None)

    def rewind(self):
        self.iterator = iter(self.feeds)


def cpu_session(path):
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    options.enable_mem_pattern = False
    return ort.InferenceSession(
        str(path), sess_options=options, providers=["CPUExecutionProvider"]
    )


def quantize_model(float_path, feeds, path):
    """Static signed INT8 QDQ with per-channel weights and no custom ops."""
    path = Path(path)
    prepared = path.with_name(path.stem + ".prepared.onnx")
    if path.exists() or prepared.exists():
        raise FileExistsError(path if path.exists() else prepared)
    if not feeds:
        raise ValueError("calibration feeds must not be empty")
    session = cpu_session(float_path)
    inputs = session.get_inputs()
    if len(inputs) != 1 or inputs[0].name != "input":
        raise ValueError("probe requires one named input")
    expected_dtype = np.float32 if inputs[0].type == "tensor(float)" else np.int64
    for feed in feeds:
        if set(feed) != {"input"}:
            raise ValueError("calibration feed must contain exactly input")
        sample = feed["input"]
        if sample.shape != tuple(inputs[0].shape) or sample.dtype != expected_dtype:
            raise ValueError("calibration feed shape or dtype mismatch")
        if not np.isfinite(sample).all():
            raise ValueError("non-finite calibration sample")
    path.parent.mkdir(parents=True, exist_ok=True)
    quant_pre_process(
        float_path, prepared, skip_optimization=True, skip_symbolic_shape=True
    )
    quantize_static(
        prepared,
        path,
        CalibrationReader(feeds),
        quant_format=QuantFormat.QDQ,
        per_channel=True,
        activation_type=QuantType.QInt8,
        weight_type=QuantType.QInt8,
        op_types_to_quantize=["Conv", "Gemm", "MatMul"],
        calibration_providers=["CPUExecutionProvider"],
        extra_options={"ActivationSymmetric": False, "WeightSymmetric": True},
    )
    report = graph_info(path)
    if not {"QuantizeLinear", "DequantizeLinear"}.issubset(report["operators"]):
        raise ValueError("quantization did not produce a QDQ graph")
    return report


def compare_outputs(reference, candidate):
    reference, candidate = np.asarray(reference), np.asarray(candidate)
    if reference.shape != candidate.shape or not reference.size:
        raise ValueError("output shape mismatch or empty output")
    if not np.isfinite(reference).all() or not np.isfinite(candidate).all():
        raise ValueError("non-finite output")
    delta = np.abs(reference.astype(np.float64) - candidate.astype(np.float64))
    return {
        "max_abs_error": float(delta.max()),
        "mean_abs_error": float(delta.mean()),
        "rmse": float(np.sqrt(np.mean(delta**2))),
        "values": delta.size,
    }


def prepare_case(name, directory, *, seed=0, calibration_count=16, evaluation_count=8):
    """Create a new synthetic case directory, retaining all evidence on failure."""
    probe = make_probe(name, seed)
    calibration = synthetic_feeds(probe.shape, calibration_count, seed + 1, probe.dtype)
    evaluation = synthetic_feeds(probe.shape, evaluation_count, seed + 2, probe.dtype)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    float_path, int8_path = directory / "float.onnx", directory / "int8.onnx"
    floating = export_float(
        probe.model, torch.from_numpy(calibration[0]["input"]), float_path, probe.opset
    )
    quantized = quantize_model(float_path, calibration, int8_path)
    float_session, int8_session = cpu_session(float_path), cpu_session(int8_path)
    eager_outputs, float_outputs, int8_outputs = [], [], []
    for feed in evaluation:
        with torch.inference_mode():
            eager = probe.model(torch.from_numpy(feed["input"])).numpy()
        reference = float_session.run(None, feed)[0]
        candidate = int8_session.run(None, feed)[0]
        np.testing.assert_allclose(reference, eager, rtol=1e-5, atol=1e-6)
        compare_outputs(reference, candidate)
        eager_outputs.append(eager.ravel())
        float_outputs.append(reference.ravel())
        int8_outputs.append(candidate.ravel())
    float_error = compare_outputs(
        np.concatenate(eager_outputs), np.concatenate(float_outputs)
    )
    int8_error = compare_outputs(
        np.concatenate(float_outputs), np.concatenate(int8_outputs)
    )
    artifacts = {}
    for path in (float_path, int8_path.with_name("int8.prepared.onnx"), int8_path):
        artifacts[path.name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
    report = {
        "schema": "micro-classifier/m1a-case/1",
        "case": name,
        "purpose": PROBE_PURPOSES[name],
        "status": "host_artifacts_prepared",
        "untrained": True,
        "seed": seed,
        "parameter_count": sum(
            parameter.numel() for parameter in probe.model.parameters()
        ),
        "input_dtype": probe.dtype,
        "calibration": {
            "source": "synthetic_uniform_smoke_only",
            "seed": seed + 1,
            "samples": calibration_count,
            "sha256": feed_digest(calibration),
        },
        "evaluation": {
            "source": "separate_synthetic_seed_not_a_task_split",
            "seed": seed + 2,
            "samples": evaluation_count,
            "sha256": feed_digest(evaluation),
        },
        "float_graph": floating,
        "qdq_graph": quantized,
        "float_vs_pytorch": float_error,
        "qdq_vs_float": int8_error,
        "numerical_smoke": {
            "test_only_max_abs_bound": SMOKE_MAX_ABS_ERROR,
            "within_test_bound": int8_error["max_abs_error"] <= SMOKE_MAX_ABS_ERROR,
            "not_a_task_quality_gate": True,
        },
        "artifacts": artifacts,
        "st_compiler_executed": False,
        "npu_mapping": None,
        "board_measured": False,
    }
    with (directory / "report.json").open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return report


def prepare_suite(
    directory, names=None, *, seed=0, calibration_count=16, evaluation_count=8
):
    names = list(PROBE_PURPOSES) if names is None else list(names)
    if (
        not names
        or len(names) != len(set(names))
        or any(name not in PROBE_PURPOSES for name in names)
    ):
        raise ValueError("probe names must be known, nonempty and unique")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**63 - 2:
        raise ValueError("seed must be a nonnegative integer below 2^63 - 2")
    for count in (calibration_count, evaluation_count):
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("sample counts must be positive integers")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    cases = [
        prepare_case(
            name,
            directory / name,
            seed=seed,
            calibration_count=calibration_count,
            evaluation_count=evaluation_count,
        )
        for name in names
    ]
    report = {
        "schema": "micro-classifier/m1a-host/1",
        "created_utc": datetime.now(UTC).isoformat(),
        "status": "host_artifacts_prepared",
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "onnx": onnx.__version__,
            "onnxruntime": ort.__version__,
            "numpy": np.__version__,
            "execution_provider": "CPUExecutionProvider",
        },
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "quantization": {
            "format": "QDQ",
            "activation_type": "QInt8",
            "weight_type": "QInt8",
            "weight_per_channel": True,
            "weight_symmetric": True,
            "activation_symmetric": False,
            "selected_operators": ["Conv", "Gemm", "MatMul"],
            "other_operators_may_remain_float": True,
            "standard_static_shape_inference": True,
        },
        "cases": cases,
        "st_compiler": {"status": "not_run", "milestone_passed": False},
        "limitations": [
            "Untrained random probes and synthetic calibration, not task models or datasets.",
            "CPU float/QDQ execution is not ST mapping, SRAM fit, target parity or latency.",
            "Numerical smoke bounds are diagnostic only, not approved quality thresholds.",
            "No training, board access, firmware integration or teacher inference.",
            "Compile through the ST front end, not atonn directly; pin its release first.",
        ],
    }
    with (directory / "manifest.json").open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("export/artifacts/m1a"))
    parser.add_argument("--case", action="append", choices=tuple(PROBE_PURPOSES))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--calibration-samples", type=int, default=16)
    parser.add_argument("--evaluation-samples", type=int, default=8)
    parser.add_argument(
        "--report", type=Path, help="also write a new shareable JSON report"
    )
    args = parser.parse_args()
    if args.report and args.report.exists():
        parser.error("report already exists; choose a new path")
    try:
        report = prepare_suite(
            args.output,
            args.case,
            seed=args.seed,
            calibration_count=args.calibration_samples,
            evaluation_count=args.evaluation_samples,
        )
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x") as stream:
            json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
    print(
        json.dumps(
            {
                "manifest": str(args.output / "manifest.json"),
                "prepared_cases": len(report["cases"]),
                "outside_numerical_smoke_bound": [
                    row["case"]
                    for row in report["cases"]
                    if not row["numerical_smoke"]["within_test_bound"]
                ],
                "st_compiler_executed": False,
                "milestone_passed": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
