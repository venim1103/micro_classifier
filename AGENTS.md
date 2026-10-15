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

## Current State (2026-10-15)

Keep this section and the Task List current; a new session resumes from them.

- Design plus INT8 Vela 2.0 9B and d3-flash teacher loaders
  ([teacher/vela_int8.py](teacher/vela_int8.py),
  [teacher/d3_int8.py](teacher/d3_int8.py)) and both validators, plus d3-mini
  BF16 support and a working CPU-only rover trainer environment in
  [sim/rover.py](sim/rover.py). No student, reviewed dataset, firmware,
  ST compiler report, or board measurement exists yet.
- M0 scope defaults for the ground-rover pilot were confirmed by the user on
  2026-10-15 (DESIGN.md §2 and REVIEW.md §10): four per-tick questions
  (`path_blocked`, `clear_sector`, `speed_tier`, `mode`), ego-state plus an
  on-module 8x8 ToF grid and an 8-tick history window, TypeSafe Jev confidence
  formulas, a minimal 2-D Python/NumPy simulator first, and UART at 1 Mbaud.
- ST Edge AI Core and STM32CubeProgrammer are not installed, so NPU compilation
  (M1a) waits until the user places them in `.devcontainer/tools`. No board is
  attached.
- Approved by the user: running the Vela 2.0 9B release code at revision
  `068425bb145c05884a98b870c219047da22d9aea` (2026-10-13).
- Approved by the user (2026-10-15): download `vllm-sr/d3-flash` at
  `b92769d85908bb3ee737ef9c765e1c08b887aca6` and `vllm-sr/d3-mini` at
  `6d8971f464d6f9d4c5af7d9a8d75f3aa03be4f59` (about 26 GB together), and run
  their release code after reading it. Stop and ask before execution if the
  review finds subprocesses, pickle/`torch.load`, or network access beyond the
  Hugging Face Hub and the documented media URLs.
- d3-flash GPU smoke passed on the RTX A3000: 7.416 GiB allocated after load,
  8.438 GiB peak reserved, two text questions answered in 7.12 s. Full
  25-request text/state/local-image validation subsequently passed: maximum
  probability delta 0.019836, mean 0.002114, zero flips over 31 questions;
  d3-mini BF16 matched its streamed reference exactly. Reports are in
  `teacher/reports/`; this is parity evidence, not teacher-quality clearance.
- User confirmation after restart (2026-10-15): the recorded M0 defaults are
  accepted. Current work covers teacher tooling and, per the latest
  clarification, a working simulation environment for trainer development
  without hardware. Do not claim board validation or freeze the detailed
  interface or physical safety parameters. Student training and firmware
  remain outside this tooling-first scope.
- Approved after source review (2026-10-15): in-process inference at the two
  pinned d3 revisions only. Exclude the optional HTTP server, all videos
  (including their temporary-file decoder), and remote image URLs. Require
  full manifest hashing. No subprocess, pickle, or `torch.load` calls were
  found in the reviewed inference path.
- Approved by the user (2026-10-15): add torchvision 0.25.0 to match PyTorch
  2.10.0 for d3 image processing; update both dependency hash locks and install
  the matching official wheel with TLS and hash verification enabled.
- Installed matching torchvision 0.25.0+cu128 with hashes and TLS; both locks
  regenerated without upgrading existing packages. `pip check`, compiled
  operator check and both teachers' local-image inference passed. A complete
  container rebuild has not been performed after this change.
- User approved configurable simulation-only defaults on 2026-10-15: 20 Hz,
  radius 0.18 m, max speed 0.6 m/s, acceleration 1 m/s², turn rate 1.5 rad/s;
  planar 45-degree 8x8 ToF, 4 m range, 0.02 m noise, 2% zone dropout,
  two-tick latency and eight history ticks. Reward: goal-distance progress
  minus 0.01/tick, plus 10 for success, minus 10 for collision, 400-tick limit.
  These are not physical safety specifications. Interim versioned JSONL logs
  are approved until the wire contract exists. DESIGN.md §7 records limits.
- Simulator tooling passes 21 focused tests and a 32-episode seeded smoke
  suite (32 successes, no collisions/timeouts) with the privileged map-aware
  expert. The sensor-only reactive baseline collided in obstacle/slalom
  scenes and is not an expert or deployment candidate. No training was run.

## Task List

Work top to bottom. When a task meets its exit condition, mark it `[x]` and add
a one-line result. Mark a task `[blocked: reason]` while it waits on the user or
on missing tools, and continue with the next unblocked task.

1. [x] M0 scope: ask the M0 questions from REVIEW.md §10 in one batch, each with
   a proposed default, and record the answers in DESIGN.md §2 and REVIEW.md
   §10. Use the defaults for unanswered items, marked as provisional.
  Result: Recorded defaults on 2026-10-14; user confirmed them on 2026-10-15.
  Current implementation remains restricted to teacher tooling.
2. [x] d3-flash INT8 loader `teacher/d3_int8.py`, with unit tests that need no
   download or GPU. Exit: it loads on the 12 GB GPU and answers `system_one`
   requests.
  Result (2026-10-15): 10 d3 tests (13 total), lint and format passed;
  fully verified offline GPU load and two-question text inference succeeded.
3. [x] `teacher/validate_d3_int8.py`: INT8 against a streamed BF16 reference on
   about 25 requests covering every question type, text and small local
   images, and synthetic rover states. Exit: a JSON report in
   `teacher/reports/` and measured results in DESIGN.md §4.
  Result (2026-10-15): 25 requests, 31 questions, 85 probabilities; max/mean
  delta 0.019836/0.002114, no flips; JSON report and measured limits recorded.
4. [x] d3-mini in BF16 with host-side embeddings, validated the same way. Exit:
   a report and a d3-flash versus d3-mini comparison in DESIGN.md §4.
  Result (2026-10-15): identical 25-request suite; exact BF16-reference parity,
  7.368 GiB after load, 1.845 s median request; report and comparison recorded.
5. [blocked: detailed wire contract outside current tooling-first scope]
  Interface contract v0 (DESIGN.md §2): one packet definition with Python
   encoding and decoding, a C header, a CRC, golden byte vectors, and
   round-trip tests.
6. [blocked: physical thresholds and reviewed label policy unspecified]
  Rover question catalogue v0 as data (types, options, and label source per
   question) and deterministic labelers for the computable questions.
7. [blocked: contract-format log export awaits Task 5] The simulator chosen
  in M0 (accepted default: a minimal Python/NumPy 2-D
   rover simulator now, PX4 with Gazebo later), with an 8x8 ToF model, noise,
   dropouts, latency, a scripted expert, and episode logs in the contract
   format.
  Partial result (2026-10-15): working reset/step environment, seeded scenes,
  sensor faults/latency/history, reward, two controllers, exclusive JSONL logs,
  PNG rendering, 21 tests and 32 smoke episodes. No binary contract claim.
8. [blocked: input contract, catalogue and reviewed labeling policy pending]
  Teacher labeling pipeline: deterministic rendering of state packets for
   the teacher, cached and resumable labeling, and provenance (revision,
   settings, and hashes).
9. [blocked: no reviewed task dataset or locked splits] Baselines (rules and a classical model) and the evaluation suite
   (macro-F1, per-class recall, NLL, Brier score, calibration error, and
   coverage curves) on locked splits.
10. [blocked: training outside current tooling scope; dataset pending]
  Student: a small convolutional or MLP trunk over the state history and
    the ToF grid with per-question heads; supervised versus distilled
    comparison (M3).
11. [blocked: no trained student] Closed-loop evaluation in the simulator and one DAgger round.
12. [blocked: no trained student] Static ONNX export, INT8 QDQ PTQ, float versus INT8 parity, calibration
    on the deployed path, and golden vectors for the firmware (M4, host side).
13. [blocked: firmware outside current tooling scope; contract pending]
  Firmware library in C for the Cortex-M55 without the ST HAL: packet
    parsing, history buffer, heads, softmax, confidence, and rejection; host
    unit tests against the golden vectors and an `arm-none-eabi-gcc` build.
14. [blocked: ST Edge AI Core not installed] M1a compile-only experiments
    (DESIGN.md §12); prepare the scripts so they run once the tools exist.
15. [blocked: no board] M1b board bring-up and measurements.
16. [x] Draft a request to the vLLM Semantic Router team for a Decision 3.0
    training-data statement (REVIEW.md F15) for the user to send.
  Result (2026-10-15): draft in REVIEW.md §14; nothing sent, no account used.

## Autonomy and Escalation

Work through the Task List autonomously. Do not stop for status updates or
routine confirmations: finish a task, verify it, commit it, and start the next.

Ask the user first, batching questions and proposing a default, for:

- Product decisions: requirements, M0 items, metric thresholds, safety
  behaviour, and changes to accepted decisions in DESIGN.md or to a frozen
  interface contract.
- Running third-party model code at a revision the user has not approved; new
  or upgraded dependencies; changes to `.devcontainer`.
- Downloads other than approved model revisions, and any download that would
  leave less than about 20 GB of free disk space.
- Deleting files or data you did not create, pushing or rewriting git history,
  and anything involving accounts, licences, payments, or contacting people.

When a task is blocked, record the question in the Task List and continue with
the next unblocked task. After three failed approaches to the same problem,
record what was tried and move on.

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
- Third-party model code: pin the full revision and read the code before running
  it. Running a release needs the user's approval for that exact revision;
  record approvals in Current State.
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
  Use Conventional Commit subjects from now on:
  `<type>(optional-scope): imperative summary`, for example
  `feat(sim): add seeded episode replay`. Choose an appropriate standard type:
  `feat`, `fix`, `test`, `docs`, `refactor`, `perf`, `build`, `ci`, `chore`,
  `style`, or `revert`. Keep the existing bullet body convention. Do not
  rewrite older commits merely to add a type prefix.

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

- Loop: take the first unblocked task, restate its exit condition, implement
  it, verify it (tests, lint, and a real run where possible), record
  measurements and decisions in DESIGN.md, commit locally, and update the Task
  List and Current State. Then continue with the next task.
- Run jobs longer than about 10 minutes in the background with logs in an
  ignored directory, and work on CPU tasks meanwhile. Run one GPU job at a time.
- Put new Python code in top-level packages by area (for example `interface/`,
  `sim/`, `student/`, and `export/`), C code in `firmware/`, and generated data
  in ignored directories.
- When only blocked tasks remain, or at the end of a session, report what
  changed, how it was verified (commands and results), open questions with
  proposed defaults, and the next step.
