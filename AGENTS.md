# Agent Instructions

These instructions apply to any AI assistant working in this repository.

## Project

micro_classifier builds a Jev-like **robot decision module**: an STM32N6 board
(N657: Cortex-M55 with the Neural-ART NPU) that attaches to a host robot, first
a ground rover and later a mini-drone. On every tick it answers a fixed
catalogue of typed questions (`choice`, `noul`, `score`) with probability
distributions, using a small INT8 student distilled from open teacher models.
The host's own controller keeps actuation, inner loops, interlocks, and
fail-safes.

Documents of record:

- [DESIGN.md](DESIGN.md): architecture, decisions, budgets, gates, and
  milestones (§12). Read §1, §2, §4, §6, and §12 before any task.
- [REVIEW.md](REVIEW.md): evidence and findings. §12 is the latest update, and
  §10 is the M0 decision template.

## Current State (2026-10-14)

- Design only, plus an INT8 Vela 2.0 9B teacher loader
  ([teacher/vela_int8.py](teacher/vela_int8.py)) and its validator. No student,
  dataset, firmware, ST compiler report, or board measurement exists yet.
- M0 decisions are open; REVIEW.md §10 holds a rover example to confirm or
  replace with the user.
- ST Edge AI Core and STM32CubeProgrammer are not installed, so NPU compilation
  (M1a) waits until the user places them in `.devcontainer/tools`. No board is
  attached.

Priorities, in order:

1. The d3-flash INT8 teacher on the 12 GB GPU (DESIGN.md §4).
2. M0 decisions with the user.
3. A robot-state request format, a small reviewed evaluation seed, and a
   simulator scenario (DESIGN.md §7).
4. M1a compile-only experiments once the ST tools are installed.

## Hardware

- Default: this dev container on a laptop RTX A3000 12 GB under WSL2 and
  Podman. Beyond physical VRAM, WSL2 spills to system memory instead of failing,
  and throughput fell about 3x when that happened. Keep peak reserved GPU memory
  below about 11 GiB and the batch token budget at 2,048 for 9B-class models.
- Occasionally: a host with two NVLinked RTX 3090s. Check `nvidia-smi` rather
  than assuming it. Never use the GTX 1080 Ti (no BF16).

## Teachers

- First teacher: Decision 3.0 d3-flash (`vllm-sr/d3-flash`, revision
  `b92769d85908bb3ee737ef9c765e1c08b887aca6`) with INT8 weight-only projections:
  about 7.4 GiB on the GPU, with BF16 embeddings in host RAM. Its text backbone
  has the same dimensions as Vela 2.0 9B, so port `teacher/vela_int8.py` and
  reuse its INT8 pieces rather than copying them.
- Compare it with d3-mini (`vllm-sr/d3-mini`, revision
  `6d8971f464d6f9d4c5af7d9a8d75f3aa03be4f59`) in BF16 with host-side
  embeddings, and with d3 (26B) in INT8 across the 3090s when available. Vela
  2.0 9B in INT8 remains available for text-only operator questions.
- Never use TypeSafe's hosted Jev API outputs for training, labels, or tuning
  (customer agreement §2.3(b)), autotrust JEV models (trained on Jev-distilled
  labels), or Crivo models for commercial work (CC BY-NC 4.0).
- d3 runtime facts, from reading the release code:
  - Entry points: `D3.from_pretrained(path, revision=..., device=...,
    verify=...)`, then `system_one(state=..., questions=..., images=...,
    videos=...)`.
  - `D3.__init__` loads the backbone through `backbone_class()`, which imports
    `Qwen3_5Model` inside the function, with `dtype=torch.bfloat16` and
    `device_map={"": device}`; `linearize_patch_embed` then rewrites the vision
    patch embedding. Inject the INT8 backbone at that loading step only.
  - `D3.logits` embeds token IDs that are already on the GPU, and
    `PromptEncoder` runs the layer loop itself (`noncausal_full_attention`). A
    host-side embedding must accept GPU IDs and return GPU BF16 activations.
  - The readout is `readout.safetensors`, `[255, hidden]` in FP32, with
    temperature 1.0. `confidence` is 1 − H(p)/ln n for choice and score.
  - Weight keys are `language_model.*` and `visual.*`. `verify="fast"` hashes
    only files up to 64 MiB, so use `verify="full"`. The runtime downloads
    `http(s)` media URLs: pass local files or arrays only. Each 32 x 32-pixel
    patch is one token, and images below 65,536 pixels are upscaled.
  - `d3_fast.py` is ROCm-only. Without flash-linear-attention (not installed)
    the PyTorch reference kernels run.
- Validate every quantized teacher against a streamed BF16 reference (see
  `stored_bf16_weights` in `teacher/vela_int8.py`): maximum and mean |Δp|,
  decision flips per question type, memory, and throughput. INT8 Vela 9B reached
  a maximum |Δp| of 0.013 with no flips; investigate anything clearly worse.

## Rules

- Evidence: cite primary sources and label estimates as estimates. Never present
  unmeasured fit, latency, or accuracy as fact. Scores from different Decision
  Index editions are not comparable.
- Third-party model code: pin the full revision, read the code before running
  it, and ask the user before executing a newly downloaded release for the first
  time. Tell the user before downloads above about 5 GB.
- Dependencies: ask first, add them to `.devcontainer/requirements.in`, and
  regenerate both hash locks with the commands in
  [.devcontainer/README.md](.devcontainer/README.md). Never disable TLS
  verification or `--require-hashes`.
- Keep weights, datasets, caches, and ST tools out of git; add ignore rules when
  creating such directories.
- On-device means on-device: never move inference to the host for a feature
  described as running on the module.
- Safety: the module only recommends. No design may let module output or
  silence stop a drone's motors in flight, and host fail-safes stay independent.
- Documentation: record decisions and measurements in DESIGN.md and add dated
  review updates to REVIEW.md rather than rewriting its history. Do not create
  new Markdown files unless asked. Use reference-style links and check that
  every reference resolves.
- Ask the user for product decisions, with a proposed default, instead of
  inventing requirements.
- Git: small, focused commits with a one-line summary and a bullet body. Never
  push, force-push, or rewrite history without the user's approval.

## Commands

- Tests: `python -m pytest -q`. Tests must run without downloads or a GPU; skip
  GPU-only checks when CUDA is unavailable.
- Lint and format: `ruff check .` and `ruff format --check <changed files>`.
  There is no project Ruff configuration, and `.devcontainer/smoke.py` is not
  yet formatted; leave it unless asked.
- Container checks: `python .devcontainer/smoke.py` (add `--network` for TLS).
- INT8 Vela validation:
  `python -m teacher.validate_vela_int8 --output teacher/reports/<name>.json`.
- Environment: Python 3.12 virtual environment at `/opt/venv` with PyTorch and
  Transformers (Qwen3.5 support built in).

## Way of Working

- Work milestone by milestone (DESIGN.md §12). Before a task, state its
  milestone and exit condition and propose a short plan; for larger changes,
  wait for the user's go-ahead.
- After a task, report what changed, how it was verified (commands and
  results), open questions, and the next step.
