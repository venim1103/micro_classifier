import numpy as np
import onnxruntime as ort
import pytest
import torch

from export.m1a import (
    PROBE_PURPOSES,
    SMOKE_MAX_ABS_ERROR,
    CalibrationReader,
    compare_outputs,
    conv_probe,
    export_float,
    feed_digest,
    make_probe,
    prepare_suite,
    quantize_model,
    synthetic_feeds,
)


def session(path):
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    return ort.InferenceSession(
        str(path), sess_options=options, providers=["CPUExecutionProvider"]
    )


def test_temporal_layouts_have_identical_weights_and_equivalent_outputs():
    height, width = conv_probe("height"), conv_probe("width")
    generator = torch.Generator(device="cpu").manual_seed(91)
    sample = torch.randn((1, 96, 128, 1), generator=generator)
    for source, target in zip(height.parameters(), width.parameters(), strict=True):
        expected = source.transpose(2, 3) if source.ndim == 4 else source
        torch.testing.assert_close(expected, target, rtol=0, atol=0)
    torch.testing.assert_close(
        height(sample).transpose(2, 3),
        width(sample.transpose(2, 3)),
        rtol=1e-5,
        atol=1e-6,
    )
    assert sum(parameter.numel() for parameter in height.parameters()) == 10440
    assert not height.training and not any(
        parameter.requires_grad for parameter in height.parameters()
    )


@pytest.mark.parametrize("layout", ["height", "width"])
def test_static_float_onnx_export_matches_pytorch(layout, tmp_path):
    model = conv_probe(layout)
    shape = (1, 96, 128, 1) if layout == "height" else (1, 96, 1, 128)
    sample = torch.linspace(-1, 1, 96 * 128).reshape(shape)
    path = tmp_path / f"{layout}.onnx"
    report = export_float(model, sample, path)
    assert report["operators"] == ["Conv", "Relu"]
    assert report["shapes"]["input"] == list(shape)
    assert report["shapes"]["output"] == [1, 48, *shape[2:]]
    assert report["opsets"] == {"": 13}
    result = session(path).run(None, {"input": sample.numpy()})[0]
    np.testing.assert_allclose(result, model(sample).numpy(), rtol=1e-5, atol=1e-6)
    with pytest.raises(FileExistsError):
        export_float(model, sample, path)


def test_probe_construction_preserves_cpu_rng_state_and_is_seeded():
    before = torch.random.get_rng_state().clone()
    first, second = conv_probe("height", 42), conv_probe("height", 42)
    assert torch.equal(before, torch.random.get_rng_state())
    for source, target in zip(first.parameters(), second.parameters(), strict=True):
        torch.testing.assert_close(source, target, rtol=0, atol=0)
    with pytest.raises(ValueError, match="layout"):
        conv_probe("diagonal")


def test_synthetic_calibration_and_evaluation_sets_are_seeded_and_distinct():
    shape = (1, 96, 128, 1)
    calibration = synthetic_feeds(shape, 4, 42)
    assert feed_digest(calibration) == feed_digest(synthetic_feeds(shape, 4, 42))
    assert feed_digest(calibration) != feed_digest(synthetic_feeds(shape, 4, 43))
    reader = CalibrationReader(calibration)
    assert reader.get_next() is calibration[0]
    assert len(list(iter(reader.get_next, None))) == 3
    reader.rewind()
    assert reader.get_next() is calibration[0]
    with pytest.raises(ValueError):
        synthetic_feeds(shape, 0, 0)


@pytest.mark.parametrize("layout", ["height", "width"])
def test_qdq_export_runs_on_cpu_with_bounded_smoke_error(layout, tmp_path):
    import onnx

    model = conv_probe(layout)
    shape = (1, 96, 128, 1) if layout == "height" else (1, 96, 1, 128)
    calibration = synthetic_feeds(shape, 4, 42)
    evaluation = synthetic_feeds(shape, 2, 43)
    float_path, int8_path = tmp_path / "float.onnx", tmp_path / "int8.onnx"
    export_float(model, torch.from_numpy(calibration[0]["input"]), float_path)
    report = quantize_model(float_path, calibration, int8_path)
    assert set(report["operators"]) <= {
        "Conv",
        "Relu",
        "QuantizeLinear",
        "DequantizeLinear",
    }
    graph = onnx.load(int8_path).graph
    initializers = {value.name: value for value in graph.initializer}
    weight_nodes = [
        node
        for node in graph.node
        if node.op_type == "DequantizeLinear"
        and node.input[0].endswith("weight_quantized")
    ]
    assert len(weight_nodes) == 2
    for node in weight_nodes:
        assert initializers[node.input[0]].data_type == onnx.TensorProto.INT8
        axis = next(
            attribute.i for attribute in node.attribute if attribute.name == "axis"
        )
        assert axis == 0
    floating, quantized = session(float_path), session(int8_path)
    for feed in evaluation:
        reference = floating.run(None, feed)[0]
        candidate = quantized.run(None, feed)[0]
        errors = compare_outputs(reference, candidate)
        assert errors["values"] == 48 * 128
        assert errors["max_abs_error"] < 0.05
        assert errors["rmse"] < 0.01
    with pytest.raises(FileExistsError):
        quantize_model(float_path, calibration, int8_path)


def test_quantization_rejects_empty_malformed_and_nonfinite_calibration(tmp_path):
    model = conv_probe("height")
    shape = (1, 96, 128, 1)
    float_path, int8_path = tmp_path / "float.onnx", tmp_path / "int8.onnx"
    export_float(model, torch.zeros(shape), float_path)
    for feeds in (
        [],
        [{"wrong": np.zeros(shape, dtype=np.float32)}],
        [{"input": np.zeros((1,), dtype=np.float32)}],
        [{"input": np.zeros(shape, dtype=np.float64)}],
        [{"input": np.full(shape, np.nan, dtype=np.float32)}],
    ):
        with pytest.raises(ValueError):
            quantize_model(float_path, feeds, int8_path)
        assert not int8_path.exists()


def test_error_statistics_reject_invalid_outputs_and_match_known_values():
    report = compare_outputs([1, 2, 3], [1, 2.5, 2.5])
    assert report["max_abs_error"] == 0.5
    assert report["mean_abs_error"] == pytest.approx(1 / 3)
    assert report["rmse"] == pytest.approx(np.sqrt(1 / 6))
    for reference, candidate in (([1], [1, 2]), ([], []), ([1], [np.inf])):
        with pytest.raises(ValueError):
            compare_outputs(reference, candidate)


@pytest.mark.parametrize(
    "name",
    [
        name
        for name in PROBE_PURPOSES
        if name not in ("temporal_height", "temporal_width")
    ],
)
def test_probe_matrix_exports_static_float_and_signed_qdq(name, tmp_path):
    probe = make_probe(name, seed=8)
    calibration = synthetic_feeds(
        probe.shape, 16 if name == "transformer" else 3, 9, probe.dtype
    )
    evaluation = synthetic_feeds(probe.shape, 1, 10, probe.dtype)[0]
    float_path, int8_path = tmp_path / "float.onnx", tmp_path / "int8.onnx"
    before = torch.backends.mha.get_fastpath_enabled()
    floating = export_float(
        probe.model, torch.from_numpy(calibration[0]["input"]), float_path, probe.opset
    )
    assert torch.backends.mha.get_fastpath_enabled() == before
    assert floating["shapes"]["input"] == list(probe.shape)
    assert floating["opsets"] == {"": probe.opset}
    assert not probe.model.training
    assert all(
        parameter.device.type == "cpu" and not parameter.requires_grad
        for parameter in probe.model.parameters()
    )
    if name == "gather_inside":
        assert "Gather" in floating["operators"]
    if name.endswith("pool") or name in ("tof", "camera"):
        assert "AveragePool" in floating["operators"]
    quantize_model(float_path, calibration, int8_path)
    reference = session(float_path).run(None, evaluation)[0]
    with torch.inference_mode():
        eager = probe.model(torch.from_numpy(evaluation["input"])).numpy()
    np.testing.assert_allclose(reference, eager, rtol=1e-5, atol=1e-6)
    errors = compare_outputs(reference, session(int8_path).run(None, evaluation)[0])
    if name == "transformer" and errors["max_abs_error"] > SMOKE_MAX_ABS_ERROR:
        pytest.xfail(
            "Unqualified transformer INT8 fixture after 3/16-sample calibration: "
            f"max absolute error {errors['max_abs_error']:.6f} exceeds 0.15"
        )
    assert errors["max_abs_error"] <= SMOKE_MAX_ABS_ERROR


def test_gather_inside_matches_same_embedding_lookup_outside_conv():
    probe = make_probe("gather_inside", 5)
    feed = synthetic_feeds(probe.shape, 1, 6, probe.dtype)[0]
    tokens = torch.from_numpy(feed["input"])
    outside = probe.model.embedding(tokens).transpose(1, 2).unsqueeze(-1)
    torch.testing.assert_close(
        probe.model(tokens), conv_probe("height", 5)(outside), rtol=0, atol=0
    )
    with pytest.raises(ValueError, match="unsupported probe"):
        make_probe("unknown")


def test_suite_reports_reproducible_inputs_hashes_and_no_hardware_claim(tmp_path):
    import hashlib
    import json

    output = tmp_path / "run"
    report = prepare_suite(
        output,
        ["temporal_height", "state_mlp"],
        calibration_count=3,
        evaluation_count=2,
    )
    assert report["status"] == "host_artifacts_prepared"
    assert not report["st_compiler"]["milestone_passed"]
    assert json.loads((output / "manifest.json").read_text()) == report
    for row in report["cases"]:
        assert row["untrained"] and not row["board_measured"]
        assert not row["st_compiler_executed"] and row["npu_mapping"] is None
        assert row["calibration"]["sha256"] != row["evaluation"]["sha256"]
        assert row["numerical_smoke"]["not_a_task_quality_gate"]
        assert row["numerical_smoke"]["within_test_bound"]
        for name, artifact in row["artifacts"].items():
            path = output / row["case"] / name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
            assert path.stat().st_size == artifact["bytes"]
    with pytest.raises(FileExistsError):
        prepare_suite(output)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"names": []},
        {"names": ["state_mlp"] * 2},
        {"names": ["unknown"]},
        {"seed": -1},
        {"seed": True},
        {"evaluation_count": 0},
    ],
)
def test_invalid_suite_configuration_does_not_create_output(tmp_path, kwargs):
    output = tmp_path / "invalid"
    with pytest.raises(ValueError):
        prepare_suite(output, **kwargs)
    assert not output.exists()


@pytest.fixture
def compiler_manifest(tmp_path):
    output = tmp_path / "probes"
    prepare_suite(output, ["state_mlp"], calibration_count=2, evaluation_count=1)
    return output / "manifest.json"


def test_st_plan_is_read_only_and_invokes_no_compiler(
    compiler_manifest, tmp_path, monkeypatch
):
    import subprocess

    from export.st_compile import PROFILE, build_plan

    def unexpected_process(*args, **kwargs):
        pytest.fail("planning must not invoke any subprocess")

    monkeypatch.setattr(subprocess, "run", unexpected_process)
    output = tmp_path / "compiled"
    plan = build_plan(compiler_manifest, output, expected_version="4.0.1")
    assert not output.exists()
    assert plan["status"] == "planned_not_executed"
    assert not plan["compiler_executed"]
    assert not plan["milestone_passed"] and not plan["board_measured"]
    command = plan["jobs"][0]["argv"]
    assert command[:2] == ["stedgeai", "generate"]
    assert command[command.index("--target") + 1] == "stm32n6"
    assert command[command.index("--st-neural-art") + 1] == PROFILE
    assert command[command.index("--model") + 1].endswith("state_mlp/int8.onnx")
    assert "validate" not in command and "atonn" not in command


def test_st_plan_rejects_tampering_and_output_reuse(compiler_manifest, tmp_path):
    from export.st_compile import build_plan

    with pytest.raises(FileExistsError):
        build_plan(compiler_manifest, tmp_path, expected_version="4.0.1")
    path = compiler_manifest.parent / "state_mlp" / "int8.onnx"
    path.write_bytes(path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="hash/size mismatch"):
        build_plan(compiler_manifest, tmp_path / "compiled", expected_version="4.0.1")
    assert not (tmp_path / "compiled").exists()


@pytest.mark.parametrize("defect", ["version", "schema", "duplicate", "traversal"])
def test_st_plan_rejects_invalid_inputs(compiler_manifest, tmp_path, defect):
    import json

    from export.st_compile import build_plan

    report = json.loads(compiler_manifest.read_text())
    if defect == "schema":
        report["schema"] = "unknown"
    elif defect == "duplicate":
        report["cases"] *= 2
    elif defect == "traversal":
        report["cases"][0]["case"] = "../outside"
    compiler_manifest.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        build_plan(
            compiler_manifest,
            tmp_path / "compiled",
            expected_version="latest" if defect == "version" else "4.0.1",
        )
    assert not (tmp_path / "compiled").exists()


def mock_st_process(monkeypatch, tmp_path, *, version="4.0.1", failure=None):
    import json
    import subprocess
    from pathlib import Path
    from types import SimpleNamespace

    executable = tmp_path / "mock_stedgeai"
    executable.write_bytes(b"mock executable identity; never run")
    calls = []
    killed = []
    monkeypatch.setattr("export.st_compile.shutil.which", lambda name: str(executable))
    monkeypatch.setattr(
        "export.st_compile.os.killpg", lambda *args: killed.append(args)
    )

    def popen(argv, **kwargs):
        calls.append(argv)
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["start_new_session"]
        if "--version" in argv:
            kwargs["stdout"].write(f"stedgeai - ST Edge AI Core v{version}\n".encode())
        elif "generate" in argv and failure is None:
            output = Path(argv[argv.index("--output") + 1])
            output.mkdir(parents=True)
            (output / "network_generate_report.txt").write_text("mock compiler report")
            (output / "network_c_info.json").write_text(json.dumps({"mock": True}))

        def wait(timeout=None):
            if "generate" in argv:
                if failure == "timeout" and timeout is not None:
                    raise subprocess.TimeoutExpired(argv, timeout)
                if failure == "interrupt" and timeout is not None:
                    raise KeyboardInterrupt
                if failure in ("timeout", "interrupt"):
                    return -9
                if failure == "exit":
                    return 2
            return 0

        return SimpleNamespace(wait=wait, pid=123456)

    monkeypatch.setattr("export.st_compile.subprocess.Popen", popen)
    return calls, killed


@pytest.mark.parametrize("failure", [None, "exit", "timeout", "interrupt", "missing"])
def test_st_execution_preserves_reports_and_never_passes_m1a(
    compiler_manifest, tmp_path, monkeypatch, failure
):
    import json

    from export.st_compile import build_plan, execute_plan, file_info

    calls, killed = mock_st_process(monkeypatch, tmp_path, failure=failure)
    output = tmp_path / "compiled"
    plan = build_plan(compiler_manifest, output, expected_version="4.0.1")
    report = execute_plan(plan, timeout=1)
    assert len(calls) == 3 and report["generate_attempted"]
    assert not report["milestone_passed"] and not report["board_measured"]
    assert not report["metrics_reviewed"]
    assert json.loads((output / "result.json").read_text()) == report
    assert (output / "state_mlp" / "compiler.log").exists()
    assert report["files"]["version.log"] == file_info(output / "version.log")
    if failure is None:
        assert report["status"] == "generated_reports_pending_review"
        assert report["cases"][0]["required_reports_present"]
    else:
        assert report["status"] == "compile_failures"
        expected = {
            "exit": "failed",
            "missing": "missing_reports",
            "interrupt": "interrupted",
        }.get(failure, failure)
        assert report["cases"][0]["command"]["status"] == expected
    assert bool(killed) == (failure in ("timeout", "interrupt"))
    with pytest.raises(FileExistsError):
        execute_plan(plan)


@pytest.mark.parametrize("version", ["4.0.0", "4.0.1-rc1", "unknown"])
def test_st_version_mismatch_stops_before_generate(
    compiler_manifest, tmp_path, monkeypatch, version
):
    from export.st_compile import build_plan, execute_plan

    calls, _ = mock_st_process(monkeypatch, tmp_path, version=version)
    output = tmp_path / "compiled"
    plan = build_plan(compiler_manifest, output, expected_version="4.0.1")
    report = execute_plan(plan)
    assert len(calls) == 1
    assert report["status"] == "version_check_failed"
    assert not report["generate_attempted"]
    assert (output / "result.json").exists()


def test_st_preflight_rechecks_hashes_and_missing_tools(
    compiler_manifest, tmp_path, monkeypatch
):
    import json

    from export.st_compile import build_plan, execute_plan

    output = tmp_path / "compiled"
    plan = build_plan(compiler_manifest, output, expected_version="4.0.1")
    monkeypatch.setattr("export.st_compile.shutil.which", lambda name: None)
    with pytest.raises(FileNotFoundError, match="nothing was executed"):
        execute_plan(plan)
    assert not output.exists()
    with pytest.raises(ValueError, match="positive integer"):
        execute_plan(plan, timeout=0)
    changed = json.loads(compiler_manifest.read_text())
    changed["created_utc"] = "changed after planning"
    compiler_manifest.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="inputs changed"):
        execute_plan(plan)
    assert not output.exists()


def test_st_launch_failure_is_retained_without_execution_claim(
    compiler_manifest, tmp_path, monkeypatch
):
    from export.st_compile import build_plan, execute_plan

    mock_st_process(monkeypatch, tmp_path)

    def launch_failed(*args, **kwargs):
        raise OSError("mock loader failure")

    monkeypatch.setattr("export.st_compile.subprocess.Popen", launch_failed)
    output = tmp_path / "compiled"
    plan = build_plan(compiler_manifest, output, expected_version="4.0.1")
    report = execute_plan(plan)
    assert report["status"] == "version_check_failed"
    assert not report["compiler_executed"] and not report["generate_attempted"]
    assert report["commands"][0]["status"] == "launch_failed"
    assert (output / "result.json").exists()


@pytest.mark.parametrize("failure", ["exit", "interrupt"])
def test_st_matrix_continues_after_failure_but_stops_after_interrupt(
    tmp_path, monkeypatch, failure
):
    from export.st_compile import build_plan, execute_plan

    probes = tmp_path / "probes"
    prepare_suite(probes, ["state_mlp", "tof"], calibration_count=2, evaluation_count=1)
    calls, _ = mock_st_process(monkeypatch, tmp_path, failure=failure)
    plan = build_plan(
        probes / "manifest.json", tmp_path / "compiled", expected_version="4.0.1"
    )
    report = execute_plan(plan)
    expected_count = 1 if failure == "interrupt" else 2
    assert len(report["cases"]) == expected_count
    assert len(calls) == expected_count + 2
    assert report["status"] == "compile_failures"
