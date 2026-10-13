# Development Container

This setup adapts the structure and certificate flow from the adjacent
embedded-Jev project. It supplies the host-side ML/export environment and basic
Arm build/debug tools for the STM32N6 classifier. It does not download teacher
weights, vendor SDKs, or licensed ST applications automatically.

## Profiles

| Configuration                                       | Use                                                                          |
| --------------------------------------------------- | ---------------------------------------------------------------------------- |
| [CPU](devcontainer.json)                            | Default; Python training/export and embedded tools without a GPU requirement |
| [CUDA / Docker](gpu/devcontainer.json)              | NVIDIA host with Docker and NVIDIA Container Toolkit                         |
| [CUDA / Podman / WSL](gpu-podman/devcontainer.json) | The reference project's WSL2 passthrough with Podman/NVIDIA CDI              |

All profiles target Linux x86-64 and use the same Ubuntu 24.04 base, Python 3.12
virtual environment, firmware tools, cache layout, and certificate handling.
The CUDA profiles install PyTorch's CUDA 12.8 runtime wheels instead of the CPU
build. They do not install a host NVIDIA driver or a full CUDA toolkit with
`nvcc`. Optional custom teacher kernels are not part of this initial setup.

The Podman/WSL profile preserves the example's key passthrough settings:

- NVIDIA CDI: `--device nvidia.com/gpu=all`.
- WSL GPU device: `--device /dev/dxg`.
- Read-only `/usr/lib/wsl` mount and `LD_LIBRARY_PATH=/usr/lib/wsl/lib`.
- `NVIDIA_VISIBLE_DEVICES=all` and compute/utility capabilities.
- `--security-opt label=disable`, as in the reference configuration.

This profile is WSL-specific, not a generic native-Linux Podman configuration.
The host needs a working Windows NVIDIA/WSL driver and a configured NVIDIA CDI
device. Host `nvidia-smi` must work before container GPU access can work. The
standard Docker profile uses `--gpus all` instead of WSL-specific device mounts.
Neither profile uses `--privileged`.

## Start the Environment

Open the project folder in VS Code and use **Dev Containers: Reopen in
Container** for the default CPU configuration. Configure the Dev Containers
extension's `dev.containers.dockerPath` to `podman` on a Podman host.

The CLI can start a specific profile without replacing the default:

```sh
devcontainer up --workspace-folder "$PWD" --docker-path podman \
  --buildkit never --gpu-availability none
```

For this WSL/Podman host:

```sh
devcontainer up --workspace-folder "$PWD" \
  --config "$PWD/.devcontainer/gpu-podman/devcontainer.json" \
  --docker-path podman --buildkit never --gpu-availability all
```

For an NVIDIA-enabled Docker host:

```sh
devcontainer up --workspace-folder "$PWD" \
  --config "$PWD/.devcontainer/gpu/devcontainer.json" \
  --gpu-availability all
```

After a CLI launch, use **Dev Containers: Attach to Running Container** and
open `/workspaces/micro_classifier`. The container runs development commands as
`vscode`, and the Python interpreter is `/opt/venv/bin/python`.

The initialization script prepares the CA bundle and creates the local tools
mount before the image build. A raw `podman build` or `docker build` must first
run `bash .devcontainer/prepare-build.sh`.

## Certificate Trust

[prepare-build.sh](prepare-build.sh) exports public host trust certificates
from macOS keychains, Windows root stores when available, or a Linux system
bundle. The Dockerfile splits the bundle into individual certificates, validates
them with OpenSSL, and imports them into Ubuntu's system CA store before apt or
Python dependency installation.

Python/OpenSSL, Requests, curl, and Node use the same system trust bundle via
`SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, and
`NODE_EXTRA_CA_CERTS`. `uv` uses native/system TLS trust. Package installation
continues to verify TLS and package hashes; there are no trusted-host or
certificate-verification bypasses.

To use an explicit approved PEM bundle, set this on the host before launch:

```sh
export MICRO_CLASSIFIER_CA_BUNDLE=/absolute/path/to/approved-ca-bundle.pem
```

The script rejects bundles containing private keys. Generated CA exports and
temporary export files are ignored by Git because enterprise issuer information
can identify the organization. Do not redistribute images containing enterprise
roots without approval. A changed host trust store requires an image rebuild;
certificates are a build-time snapshot, not a live host mount.

Base-image pulls use the host container engine's trust store, before the
Dockerfile can import roots. Configure engine trust separately if a registry
pull fails behind TLS inspection. Host proxy requirements also need to be set
for the engine and build environment; do not put credentials in these files.

## Installed Tools and Dependencies

- PyTorch, Transformers, Hugging Face Hub, Datasets, Accelerate, and safetensors.
- NumPy, SciPy, scikit-learn, and Matplotlib for data and evaluation.
- ONNX, ONNX Runtime, and ONNX Script for static export and INT8 QDQ work.
- `arm-none-eabi-gcc`, binutils, Newlib, `gdb-multiarch`, CMake, Ninja, and ccache.
- libusb, USB utilities, PyUSB, and pyserial for later board integration.
- pytest, Ruff, ShellCheck, Git, and Git LFS.

VS Code includes Python/Pylance, C/C++, CMake Tools, and Cortex-Debug support.
The distro Arm compiler is a baseline validated for a Cortex-M55/Helium object
build, not a guarantee of compatibility with every future ST SDK/example.

The dependency input is [requirements.in](requirements.in). The exact CPU and
CUDA environments are recorded in [requirements.lock](requirements.lock) and
[gpu/requirements.lock](gpu/requirements.lock), including transitive hashes.
The Dockerfile supplies the matching PyTorch wheel index and installs with
`--require-hashes`, then runs `pip check`.

To deliberately refresh locks inside an existing container:

```sh
uv pip compile .devcontainer/requirements.in --torch-backend cpu \
  --python-version 3.12 --python-platform x86_64-unknown-linux-gnu \
  --generate-hashes --output-file .devcontainer/requirements.lock

uv pip compile .devcontainer/requirements.in --torch-backend cu128 \
  --python-version 3.12 --python-platform x86_64-unknown-linux-gnu \
  --generate-hashes --output-file .devcontainer/gpu/requirements.lock
```

Do not add `--emit-index-url`: that lockfile option overrides pip's additional
PyTorch index. Use the pinned `uv==0.8.22` shipped in the container, review the
lock changes, rebuild, and rerun the smoke checks.

The named cache volume persists Hugging Face, pip, uv, and ccache data across
rebuilds. Generated weights and datasets are not included in the image.

## User-Supplied ST Tools

The ignored local directory `.devcontainer/tools` is mounted read-only at
`/opt/st-tools`. Add Linux distributions of tools there only after accepting
their licenses. The expected layout is:

```text
tools/
  stedgeai/
    Utilities/linux/stedgeai
  STM32CubeProgrammer/
    bin/STM32_Programmer_CLI
  arm-gnu/
    bin/arm-none-eabi-gcc
```

The optional Arm toolchain is for a vendor-recommended GCC release when needed.
The ST paths and this optional toolchain are on `PATH`.
`STEDGEAI_CORE_DIR` and `STM32_CUBE_PROGRAMMER_DIR` identify the expected
installation roots. Preserve executable permissions and verify tool versions.
Install tool packages on the host rather than writing into the read-only mount.

STEdgeAI-Core/Neural-ART, STM32CubeProgrammer, STM32CubeN6, matching generated
runtime code, and a physical board are still required for actual NPU generation,
flashing, and performance validation. Keep compiler, runtime, and SDK versions
compatible. The devcontainer does not circumvent vendor license acceptance or
download access requirements.

The base profiles do not expose arbitrary USB or serial devices. For later
board work, attach the device to WSL where applicable, configure host access
permissions, and grant only the required container device access. Adding libusb
does not itself make an ST-LINK visible inside a container.

## Validation

[smoke.py](smoke.py) runs on container creation without downloading pretrained
models. It checks:

- System CA configuration and a nonempty trust store.
- Cortex-M55/Helium compilation through an MVE intrinsic.
- A small CNN training step on the selected CPU or CUDA device.
- Static ONNX export, ONNX Runtime parity, and INT8 QDQ quantization/inference.
- A tiny local ModernBERT forward pass and Qwen3.5 configuration availability.
- Package versions and availability of optional ST executables.

The CUDA profile fails if `torch.cuda.is_available()` is false; it does not
silently use CPU for its training check. ONNX Runtime remains CPU-based for the
export/quantization reference in both profiles.

The smoke test deliberately uses the legacy exporter with static ONNX opset 17
for this compatibility probe. Its PyTorch deprecation warning does not imply
an export failure. Synthetic smoke inputs are not classification-quality data
or proof of STM32N6 NPU deployment.

After attaching to a container, run the optional live TLS checks and lint:

```sh
python .devcontainer/smoke.py --network
shellcheck .devcontainer/prepare-build.sh
ruff check .devcontainer/smoke.py
```

The network option verifies PyPI and the public Hugging Face model metadata
endpoint through both Python's standard library and Requests, with verification
enabled. It does not download teacher weights. If a post-create check failed
and its fixture is repaired, rerun this command explicitly; the CLI may reuse
the existing container without repeating the hook.

## Verified Status (2026-10-13)

| Profile or check                                             | Result                                                             |
| ------------------------------------------------------------ | ------------------------------------------------------------------ |
| CPU build and training/export/INT8/M55 smoke                 | Passed                                                             |
| Podman/WSL GPU build and CUDA training smoke                 | Passed on NVIDIA RTX A3000 12 GB Laptop GPU, driver 595.95         |
| Python and Requests HTTPS verification                       | Passed from both CPU and GPU containers                            |
| Certificate bootstrap, invalid-input guard, ShellCheck, Ruff | Passed                                                             |
| Standard Docker GPU runtime                                  | Configured, not tested on this Podman host                         |
| ST compiler, programmer, physical-board inference            | Not installed or tested; user-supplied tools and hardware required |

Tested Python package versions: PyTorch 2.10.0+cpu or 2.10.0+cu128,
Transformers 5.19.0, ONNX 1.23.2, ONNX Runtime 1.31.0, and NumPy 2.2.6.
The GPU runtime reports CUDA 12.8. These checks establish the development
environment, not Vela teacher parity or STM32N6 task accuracy/performance.
