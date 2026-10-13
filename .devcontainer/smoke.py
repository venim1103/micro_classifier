import argparse
import json
import os
import shutil
import ssl
import subprocess
import tempfile
import urllib.request
from importlib.metadata import version
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch
from onnxruntime.quantization import (
    CalibrationDataReader,
    QuantFormat,
    QuantType,
    quantize_static,
)
from onnxruntime.quantization.shape_inference import quant_pre_process
from transformers import ModernBertConfig, ModernBertModel, Qwen3_5Config


class CalibrationReader(CalibrationDataReader):
    def __init__(self):
        generator = np.random.default_rng(42)
        self.samples = iter(
            {"features": generator.normal(size=(1, 8, 16)).astype(np.float32)}
            for sample_index in range(20)
        )

    def get_next(self):
        return next(self.samples, None)


def check_certificates():
    bundle = Path("/etc/ssl/certs/ca-certificates.crt")
    for variable in (
        "SSL_CERT_FILE",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
        "NODE_EXTRA_CA_CERTS",
    ):
        if os.environ.get(variable) != str(bundle):
            raise RuntimeError(f"{variable} must use the system CA bundle")
    if not bundle.is_file() or ssl.create_default_context().cert_store_stats()["x509_ca"] == 0:
        raise RuntimeError("The system CA trust store is empty or missing")


def check_arm_compiler(directory):
    compiler = shutil.which("arm-none-eabi-gcc")
    if compiler is None:
        raise RuntimeError("arm-none-eabi-gcc is missing")
    source = directory / "cortex_m55_probe.c"
    source.write_text(
        "#include <arm_mve.h>\n"
        "int32x4_t add_vectors(int32x4_t left, int32x4_t right) {\n"
        "    return vaddq_s32(left, right);\n"
        "}\n",
        encoding="ascii",
    )
    subprocess.run(
        [
            compiler,
            "-mcpu=cortex-m55",
            "-mthumb",
            "-mfloat-abi=hard",
            "-O2",
            "-c",
            str(source),
            "-o",
            str(directory / "cortex_m55_probe.o"),
        ],
        check=True,
    )


def check_models(directory):
    torch.manual_seed(42)
    torch.set_num_threads(2)
    device = os.environ.get("MICRO_CLASSIFIER_DEVICE", "cpu")
    if device not in {"cpu", "cuda"}:
        raise RuntimeError("MICRO_CLASSIFIER_DEVICE must be cpu or cuda")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("The CUDA profile requires working NVIDIA GPU passthrough")

    model = torch.nn.Sequential(
        torch.nn.Conv1d(8, 16, 3, padding=1),
        torch.nn.ReLU(),
        torch.nn.AvgPool1d(2),
        torch.nn.Flatten(),
        torch.nn.Linear(128, 3),
    ).to(device)
    features = torch.randn(1, 8, 16, device=device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    loss = torch.nn.functional.cross_entropy(
        model(features), torch.tensor([1], device=device)
    )
    loss.backward()
    optimizer.step()

    model = model.cpu().eval()
    features = features.cpu()
    float_path = directory / "student_float.onnx"
    prepared_path = directory / "student_prepared.onnx"
    quantized_path = directory / "student_int8.onnx"
    torch.onnx.export(
        model,
        features,
        str(float_path),
        input_names=["features"],
        output_names=["logits"],
        opset_version=17,
        dynamo=False,
    )
    onnx.checker.check_model(onnx.load(float_path))
    session = ort.InferenceSession(str(float_path), providers=["CPUExecutionProvider"])
    feed = {"features": features.detach().numpy()}
    float_output = session.run(None, feed)[0]
    with torch.no_grad():
        expected = model(features).numpy()
    np.testing.assert_allclose(float_output, expected, rtol=1e-4, atol=1e-5)

    quant_pre_process(str(float_path), str(prepared_path), skip_optimization=True)
    quantize_static(
        str(prepared_path),
        str(quantized_path),
        CalibrationReader(),
        quant_format=QuantFormat.QDQ,
        activation_type=QuantType.QInt8,
        weight_type=QuantType.QInt8,
        per_channel=True,
        extra_options={"ActivationSymmetric": False, "WeightSymmetric": True},
    )
    quantized = onnx.load(quantized_path)
    onnx.checker.check_model(quantized)
    if not any(node.op_type == "QuantizeLinear" for node in quantized.graph.node):
        raise RuntimeError("Static INT8 QDQ export did not contain quantization nodes")
    session = ort.InferenceSession(str(quantized_path), providers=["CPUExecutionProvider"])
    quantized_output = session.run(None, feed)[0]
    np.testing.assert_allclose(quantized_output, float_output, rtol=0.2, atol=0.1)

    config = ModernBertConfig(
        vocab_size=32,
        pad_token_id=0,
        bos_token_id=1,
        eos_token_id=2,
        cls_token_id=1,
        sep_token_id=2,
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=1,
        num_attention_heads=2,
        max_position_embeddings=32,
    )
    config._attn_implementation = "eager"
    with torch.no_grad():
        hidden = ModernBertModel(config).eval()(torch.tensor([[1, 2, 3, 4]])).last_hidden_state
    if hidden.shape != (1, 4, 16):
        raise RuntimeError("ModernBERT architecture smoke test failed")
    if Qwen3_5Config().model_type != "qwen3_5":
        raise RuntimeError("Qwen3.5 configuration is unavailable")

    return {
        "device": device,
        "cuda_runtime": torch.version.cuda,
        "gpu": torch.cuda.get_device_name() if device == "cuda" else None,
        "float_max_error": float(np.max(np.abs(float_output - expected))),
        "int8_max_error": float(np.max(np.abs(quantized_output - float_output))),
    }


def check_network():
    import requests

    for address in (
        "https://pypi.org/simple/pip/",
        "https://huggingface.co/api/models/vllm-sr/Vela-2.0-0.3B",
    ):
        with urllib.request.urlopen(address, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTPS check failed: {address}")
        response = requests.get(address, timeout=30)
        response.raise_for_status()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", action="store_true")
    options = parser.parse_args()
    check_certificates()
    with tempfile.TemporaryDirectory(prefix="micro-classifier-smoke-") as temporary:
        directory = Path(temporary)
        check_arm_compiler(directory)
        results = check_models(directory)
    if options.network:
        check_network()
    results["versions"] = {
        package: version(package)
        for package in ("torch", "transformers", "onnx", "onnxruntime", "numpy")
    }
    results["optional_st_tools"] = {
        command: shutil.which(command)
        for command in ("stedgeai", "STM32_Programmer_CLI")
    }
    print(json.dumps(results, indent=2))
    print("Container smoke checks passed; no pretrained model or firmware was downloaded.")


if __name__ == "__main__":
    main()
