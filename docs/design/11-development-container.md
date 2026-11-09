## 11. Development Container

The `.devcontainer` directory provides the host environment; its
[README](../../.devcontainer/README.md) is the reference.

- Profiles: CPU (default), CUDA with Docker, and CUDA with Podman on WSL2, all
  on Ubuntu 24.04 with a Python 3.12 virtual environment at `/opt/venv`.
- Dependencies come from `requirements.in` through hash-locked CPU and CUDA lock
  files, installed with `--require-hashes`.
- Host CA certificates are exported at build time and imported into the system
  trust store. Python, Requests, curl, and Node use that bundle; TLS
  verification is never disabled.
- Tools include PyTorch, Transformers, ONNX, ONNX Runtime, the distro
  `arm-none-eabi-gcc` 13.2.1, CMake, Ninja, GDB, pytest, and Ruff.
- ST Edge AI Core, STM32CubeProgrammer, and an optional vendor GCC are not
  included. After accepting their licenses, place the Linux distributions in
  the ignored `.devcontainer/tools` directory, mounted at `/opt/st-tools`; until
  then no NPU compilation is possible. Pin one ST Edge AI Core release for
  compiler and runtime: mismatched generated code fails with "Possible mismatch
  in ll_aton library used".
- A named cache volume keeps Hugging Face, pip, uv, and ccache data across
  rebuilds; the Vela 2.0 9B snapshot needs about 18 GB of it.
- `smoke.py` checks CA trust, Cortex-M55/Helium compilation, a training step on
  CPU or CUDA, ONNX export with INT8 QDQ quantization, and Qwen3.5
  availability. It passed on the CPU and Podman/WSL GPU profiles.

Remaining direction: split teacher and student/export environments only if
framework requirements conflict, grant only the device access board work needs
(ST-LINK, serial), and add flash-linear-attention to the locks if a teacher
needs inputs above about 12 k tokens or runs on the two-GPU d3 host (§4).

