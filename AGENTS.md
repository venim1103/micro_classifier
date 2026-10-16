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
- [REVIEW.md](REVIEW.md): evidence and findings. §27 is the latest update, and
  §10 is the M0 decision template.

## Current State (2026-10-16)

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
- Approved by the user (2026-10-15): provisional host-side interface contract
  v0, including Python codecs, CRC, C header, golden vectors and simulator
  export. This expands tooling scope only; do not freeze physical safety,
  labeling policy or hardware integration. Student training and firmware
  implementation remain outside scope; the C header alone is not firmware.
- Contract tooling in `interface/protocol.py` passes 62 focused tests: strict
  state/decision codecs, five golden frames, bounded stream recovery, generated
  header parity, host/Arm GCC syntax checks and independent C state encoding.
  State/full-decision frames are 92/128 bytes. DESIGN.md §2 specifies this
  unfrozen draft; synthetic golden decisions are not labels or model outputs.
- Simulator `--wire` exports exact host state frames alongside module-side
  observations, with unknown health and no fabricated decisions/labels.
  All 110 repository tests pass (30 simulator, 62 interface, 18 teacher).
  Four seeded wire smoke scenes succeeded without collision/timeout; all
  566 emitted frames were verified. No new dependencies, training or hardware
  run. DESIGN.md §7 and REVIEW.md §15 record hashes and limits.
- Task 14 host preparation in `export/m1a.py` now exports nine untrained
  static-shape probes, signed per-channel INT8 QDQ and CPU comparisons.
  The real nine-case run and 27 artifact hashes are recorded in
  `export/reports/m1a-cpu-20261015.json` and DESIGN.md §12. Generated ONNX is
  ignored. There are 133 passing tests plus one expected transformer INT8
  numerical failure (max error 0.207 in the real run, versus the diagnostic
  0.15 bound). Do not describe that transformer as numerically qualified.
  No training/GPU job; actual ST tools and board gates remain blocked.
- `export/st_compile.py` prepares read-only ST plans and opt-in exact-version
  execution, with fresh outputs, hash rechecks, raw logs/reports and process-
  group cleanup. A real nine-case dry plan invoked no ST or output creation.
  Eighteen mocked runner checks pass; 151 repository tests pass plus the known
  transformer expected failure. Actual vendor compatibility, mapping metrics
  and M1a are unverified. No install, licence action, firmware integration or
  board command. REVIEW.md §17 records limits; the 4.0.1 CLI example is not an
  installation approval.
- User approved a simulation-only policy **draft and tests** on 2026-10-15,
  not episode label generation, teacher labeling or training; ST tools remain
  unavailable. `sim/catalogue.json` and `sim/labels.py` implement unreviewed
  observation-only proxies with Config-derived envelopes, explicit abstention,
  option parity and provenance. `mode` is always left for human review. The
  simulator CLI and wire contract are unchanged; no dataset was generated.
  All 67 simulator tests pass (37 draft-policy tests); full suite: 188 passed
  plus the known transformer expected failure. DESIGN.md §7 and REVIEW.md §18
  record the exact proposed formulas and limitations. Task 6 awaits review.
- User approved the unchanged draft for a four-scene seeded simulation smoke
  and teacher-pipeline tooling with fake-teacher tests on 2026-10-16. Live
  teacher labeling, training, production datasets and hardware remain excluded.
  `python -m sim.labels` records that scope and writes exclusive smoke logs.
  Seed 20261016: four successes, no collisions/timeouts, 567 observations;
  eight warmup abstentions per computable question, `mode` absent for all 567.
  All usable blocked labels are false and speed tiers are 3: no positive-class
  or low-speed coverage claim. Report: `sim/reports/label-smoke-20261016.json`;
  all four log hashes verified. Full suite: 192 passed plus the known expected
  transformer failure; 71 simulator tests. DESIGN.md §7 and REVIEW.md §19.
- Task 8 host tooling in `teacher/label_pipeline.py` renders matching simulated
  host frames, current ToF and full masked history without truth/actions/labels.
  A model-free CLI plans bounded episode prefixes; fake-only injected mode
  responses use transactional SQLite caching, full-request/identity/source
  hashes, strict validation and interruption-safe resume. Thirty focused tests
  pass; full suite: 222 passed plus the known transformer expected failure.
  Two real-log eight-observation plans invoked no teacher; maximum state text
  lengths were 9,689/9,842 characters, not measured token counts. Cache data and
  plans are ignored. Live adapters/labeling, reviewed human mode labels and
  training remain unapproved; the tokenizer-only follow-up below measures
  prompt-budget failure. DESIGN.md §7 and
  REVIEW.md §20 record the tooling-only exit and limits.
- Follow-up provenance fix (2026-10-16): returned fake-teacher records no
  longer share nested identity/settings with the running batch. Two reproduced
  regressions now pass for both fresh and cached starts; 32 pipeline tests,
  224 repository passes plus the known transformer expected failure. Lint,
  format and editor diagnostics pass. No approval boundary or label rule changed.
- User approved synthetic-only evaluation tooling on 2026-10-16. The CPU-only
  `teacher/evaluation.py` reports macro-F1, per-class recall, NLL, Brier, ECE
  and tie-preserving coverage curves with explicit conventions. Five-purpose
  fixture manifests reject cross-partition declared input/source/episode/template
  overlap; identifiers/hashes are not attested and no task split is locked.
  Thirty-six focused tests pass; full suite: 260 passed plus the known expected
  transformer failure. Built-in toy report:
  `teacher/reports/evaluation-synthetic-20261016.json`. No real label, task
  dataset, model fit, training, dependency, download or hardware action occurred.
  Actual Task 9 evaluation/baselines remain blocked on reviewed data and splits.
- Approved (2026-10-16): offline prompt/token-budget checks using only already-
  cached approved d3 tokenizer/template files; no downloads, weight/model loading,
  inference, labels or training. This does not approve live labeling or a new
  token ceiling. Prompt/tokenizer asset verification is distinct from full
  model-package verification, which remains mandatory for approved inference.
- `teacher/prompt_budget.py` now verifies pinned prompt/tokenizer assets,
  answer-code parity and exact complete text-prompt counts without truncation.
  Offline/GPU-hidden runs used both approved cached tokenizers on the same
  sixteen observations (eight each from existing wire/smoke clear logs).
  All sixteen fail the 2,048-token budget for both models: 3,421-6,936 tokens.
  Reports are `teacher/reports/prompt-budget-d3-{flash,mini}-20261016.json`.
  No weights/model runtime, inference, labels, download or training occurred.
  Fifteen focused tests pass; full suite: 275 passed plus the known expected
  transformer failure; lint/format/editor diagnostics pass. DESIGN.md §7 and
  REVIEW.md §23 record this measured live-use blocker, not a budget increase.
- Approved (2026-10-16): a separate lossless compact-prompt draft, CPU round-trip
  tests and offline comparisons on existing logs only. Keep the default renderer,
  complete input/history and 2,048-token ceiling unchanged. No inference, labels,
  training, download, dependency or live-use approval. Every original value must
  reconstruct exactly; shorter prompts alone do not establish teacher quality.
- Lossless row-table draft in `teacher/label_pipeline.py` is opt-in only;
  `teacher/prompt_budget.py --compare-compact-draft` compares unchanged full
  requests with exact row-table reconstructions. Offline runs counted 80 existing
  observations per approved tokenizer: 80 exact round trips, but 65/80 draft
  prompts still exceed 2,048 tokens (772-9,698 versus full 3,421-10,855).
  Only ticks 0-2 fit in each of five selected log prefixes; warm-history use
  remains unqualified. Both tokenizers agree. No values/history/defaults/budget
  changed, and no model/inference/labels/training ran. Focused slice: 60 tests;
  full suite: 288 passed plus the known expected transformer failure; lint,
  format and diagnostics clean. DESIGN.md §7 and REVIEW.md §24 record limits.
- Approved (2026-10-16): a second offline-only draft using shortest float32
  round-trip decimal strings for exactly representable values. Non-float32 rows
  must remain literal; original reconstruction, defaults and budget stay
  unchanged. This is lossless typed encoding, not reduced precision. No live
  use, inference, labels, training, downloads or dependencies are approved.

- The typed float32 row draft is separately opt-in through
  `teacher/prompt_budget.py --compare-float32-draft`. All 80 existing sampled
  states reconstruct exactly for both cached tokenizers, but 63/80 still exceed
  2,048 tokens (811-6,016). Only two additional startup requests fit compared
  with literal rows; no sampled full-history request fits. Nonrepresentable
  rows remain literal, including signed-zero/exponent-sensitive regression
  cases. Full suite: 298 passed plus the known transformer expected failure;
  70 focused pipeline/preflight tests, lint/format and diagnostics clean.
  Reports: `teacher/reports/float32-draft-budget-d3-{flash,mini}-20261016.json`.
  DESIGN.md §7 and REVIEW.md §25 record exactness, hashes and limits. No model
  runtime, inference, labels, training, download, dependency or hardware action.

- Approved (2026-10-16): CPU-only diagnostic coverage tooling/tests, at most
  16 simulation episodes plus synthetic fault fixtures, and an unreviewed smoke
  report. Keep label rules, simulator defaults, inputs/history and token ceiling
  unchanged. No production dataset, live teachers, training, downloads,
  dependencies, physical safety changes or deployment approval.

- Diagnostic coverage study at seed 20261016 completed eight 32-tick episodes
  (264 observations) plus twelve separate synthetic option/fault fixtures.
  Episode counts cover both blocked values (208 false/40 true), all four sector
  options and speed tiers (36/36/98/78); each computable question has 16 warmup
  abstentions. `mode` is absent throughout. No collisions; eight intentional
  horizon timeouts, not navigation failures/success evidence. Thirty-one blocked
  positives are from a stationary noisy near-wall probe; representative coverage
  and proxy accuracy remain unproven. Only the diagnostic horizon overrides
  Config (32 versus 400); rule/catalogue/original smoke function ASTs unchanged.
  Report: `sim/reports/label-coverage-20261016.json`, all eight ignored log hashes
  and 264 labels independently verified. Nine new tests; 80 simulator tests and
  307 repository passes plus the known transformer expected failure; lint,
  changed-file format and diagnostics clean. DESIGN.md §7 and REVIEW.md §26.
  No live teachers, reviewed dataset, training, dependency or hardware work.

- Approved (2026-10-16): both decision-preparation tasks: an unaccepted
  label-policy/evaluation-set proposal and a CPU-only offline prompt-cost study
  on existing logs/approved cached tokenizers. No task labels/datasets, split
  lock, accepted rules/defaults/input changes, live teachers, training,
  downloads/dependencies or ST licence actions.
- DESIGN.md §7 and REVIEW.md §27 now propose review of proxy-vs-task truth,
  observable mode semantics/reviewer abstention and episode/source/template
  grouping across five evaluation purposes. Nothing is adopted or labeled;
  no assignments or thresholds were created. Mode remains absent. Tasks 6/9
  stay review/data-blocked; offline prompt-cost study is the next approved step.

## Task List

Work top to bottom. When a task meets its exit condition, mark it `[x]` and add
a one-line result. Mark a task `[blocked: reason]` while it waits on the user or
on missing tools, and continue with the next unblocked task.

1. [x] M0 scope: ask the M0 questions from REVIEW.md §10 in one batch, each with
   a proposed default, and record the answers in DESIGN.md §2 and REVIEW.md
   §10. Use the defaults for unanswered items, marked as provisional.
  Result: Recorded defaults on 2026-10-14; user confirmed them on 2026-10-15.
  Tooling now includes teachers, simulation and provisional host codecs.
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
5. [x]
  Interface contract v0 (DESIGN.md §2): one packet definition with Python
   encoding and decoding, a C header, a CRC, golden byte vectors, and
   round-trip tests.
  Result (2026-10-15): approved provisional host-side contract, 62 focused
  tests, generated C offsets and five golden frames; no hardware freeze.
6. [blocked: reviewed training labels not approved; smoke-only policy accepted]
  Rover question catalogue v0 as data (types, options, and label source per
   question) and deterministic labelers for the computable questions.
  Partial result (2026-10-15): approved draft/test-only tooling now includes
  a versioned JSON catalogue and deterministic sensor proxies, 37 focused tests,
  explicit unreviewed/training-disabled metadata and no generated dataset.
  Smoke result (2026-10-16): user approved unchanged rules for a bounded smoke
  suite and fake-teacher pipeline tests; four seeded scenes succeeded and all
  567 observation labels/hashes checked. Training-dataset review, positive-class
  coverage, human `mode` labels and physical safety remain pending.
  Diagnostic result (2026-10-16): approved bounded coverage tooling ran eight
  episodes and twelve separate synthetic fixtures with unchanged rules. All
  computable options appear in the selected episodes, including 40 blocked and
  36 tier-0 outputs; 264 observations, no mode labels. These selected probes and
  artificial faults are not representative data or reviewed ground truth.
  Task 6 remains blocked on policy/dataset review, not option-counter plumbing.
7. [x] The simulator chosen
  in M0 (accepted default: a minimal Python/NumPy 2-D
   rover simulator now, PX4 with Gazebo later), with an 8x8 ToF model, noise,
   dropouts, latency, a scripted expert, and episode logs in the contract
   format.
  Partial result (2026-10-15): working reset/step environment, seeded scenes,
  sensor faults/latency/history, reward, two controllers, exclusive JSONL logs,
  PNG rendering, 21 tests and 32 smoke episodes. No binary contract claim.
  Result (2026-10-15): provisional state frames exported with `--wire`, 30
  simulator tests, four successful scene runs and 566 verified frames. JSONL
  embeds wire bytes as hex; no model decisions, reviewed labels or board claim.
8. [x]
  Teacher labeling pipeline host tooling: deterministic rendering of state packets for
   the teacher, cached and resumable labeling, and provenance (revision,
   settings, and hashes).
  Approved (2026-10-16): implement host tooling with fake-teacher CPU tests
  only. Do not call real teachers or claim a reviewed training dataset.
  Result (2026-10-16): deterministic full-history requests, bounded model-free
  plans and mode-only fake response/cache/resume API; 30 focused tests, 222
  repository passes plus the known expected failure. Live labeling remains
  blocked on approval, reviewed labels, adapter provenance and token-budget
  validation; this completes only the approved host-tooling portion.
  Tokenizer-only follow-up (2026-10-16): completed offline preflight, 15 focused
  tests; all 16 sampled prompts exceed 2,048 tokens for both pinned tokenizers.
  Live use remains blocked on a reviewed budget-compatible representation.
  Proposed default: keep the budget and full input/history unchanged; review
  representation before any compaction, rounding, feature removal or live use.
  Approved draft-only follow-up: exact row-table representation and offline
  comparison implemented; 65/80 sampled draft prompts still fail the unchanged
  ceiling. Not a live-use approval or solved prompt-budget gate. Keep the
  default full renderer and input/history unchanged pending further review.
  Typed float32 follow-up: approved exact typed strings with literal fallback,
  tests and offline comparison only. All 80 sampled states reconstruct exactly;
  63/80 still fail. This does not clear live use or full-history prompt budgets.
  Proposed default remains unchanged input/history and ceiling, both drafts
  opt-in/unreviewed, pending an input-strategy and teacher-quality decision.
9. [blocked: no reviewed task dataset or locked splits] Baselines (rules and a classical model) and the evaluation suite
   (macro-F1, per-class recall, NLL, Brier score, calibration error, and
   coverage curves) on locked splits.
  Approved (2026-10-16): CPU-only metric and split-validation
  tooling with synthetic fixtures only; no real labeling, training, dataset
  generation, metric-threshold changes or claim of locked task splits.
  Partial result (2026-10-16): synthetic metric arithmetic, five-purpose declared
  leakage/hash checks and exclusive built-in smoke report implemented; 36 focused
  tests, 260 repository passes plus the known expected failure. No baseline was
  fitted, task dataset generated or real split locked. DESIGN.md §7, REVIEW.md §22.
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
  Partial result (2026-10-15): nine synthetic float/QDQ CPU probes and hashed
  report ready; 23 focused tests pass plus one expected transformer numerical
  failure. Actual ST mapping/epochs/memory/cycles and M1a exit remain blocked.
  Preparation result (2026-10-15): dry-run/default and opt-in ST orchestration
  ready; 18 mocked runner tests and a real nine-case no-process plan verified.
  Supply an approved licensed ST release next; inspect actual reports before
  release-specific metric parsing or custom CSV instrumentation.
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
