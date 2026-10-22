# Project Agent Workflow

These instructions apply to any AI assistant working in this repository.

## Project

micro_classifier builds a Jev-like **robot decision module**: an STM32N6 board
(N657: Cortex-M55 with the Neural-ART NPU) that attaches to a host robot, first
a ground rover and later a mini-drone. On every tick it answers a fixed
catalogue of typed questions (`choice`, `noul`, `score`) with probability
distributions. The active rover pilot is rules-first; a small INT8 student and
distillation from open teachers remain longer-term work, not current capability.
The host's own controller keeps actuation, inner loops, interlocks, and fail-safes.

Documents of record:

- [DESIGN.md][design]: architecture, accepted decisions, contracts, budgets and
  milestones (§12).
- [REVIEW.md][review]: dated decisions, evidence, failed checks and handovers.
  §70 is the whole-repository review; newer checkpoints supersede historical
  descriptions where explicitly stated.

## Start With Context

- Read Current State and the newest relevant checkpoint in [REVIEW.md][review]
  before continuing implementation. Use [DESIGN.md][design] §§1, 2 and 12 for
  active scope and gates; read §4 for teacher work, §6 for numerical/architecture
  work and §7 for sensor, coverage and data work before editing those areas.
- Check the actual worktree, nearby implementation/tests and applicable local
  instructions. Preserve user changes, including editor settings and untracked
  files. After an interrupted tool call, verify its outcome before repeating it.
- Verify selected environments, cached files, pinned revisions, available tools
  and resource budgets rather than assuming they survived a restart. Reuse
  existing caches and environments; do not duplicate downloads or checkouts.
- Distinguish proposed, approved, implemented, tested, integrated and measured
  work. A historical approval or completed bounded run is not renewed permission.

## Documentation Audience

- [README.md][readme] is the public introduction: capabilities, maturity limits,
  documentation links and licensing. Do not add routine progress updates, test
  counts, commit histories or session handovers. This rule does not request a
  separate cleanup of existing documentation.
- Keep architecture, accepted requirements, contracts and rationale in
  [DESIGN.md][design]. Keep changing status, discussions, commands/results,
  failed-check history, evidence limits and next-session handovers in dated
  [REVIEW.md][review] updates. Preserve earlier failures and historical evidence.
- Use [.devcontainer/README.md][container-guide] for reusable environment/setup
  instructions. Use existing documents rather than creating new Markdown files
  unless asked. Use reference-style links and check their targets.
- Keep stable workflow rules here. Replace Current State and task summaries as
  they change rather than appending more historical checkpoints to this file.

## Work Independently

- The user prefers autonomous implementation within the agreed scope. Make
  routine implementation, regression-test, formatting and local verification
  decisions without asking for permission at every step.
- Work through the first unblocked task, finish its exit condition, verify it,
  record a useful checkpoint, commit locally and continue with the next approved
  task. A progress report or completed commit is not itself a reason to stop.
- If implementation needs a product decision, finish the already-authorized
  prerequisites first. Within an approved design-only scope, prepare a concrete
  candidate, tradeoffs, assumptions, proposed default and acceptance checks for
  review. Do not stop at a generic "design review needed" when that proposal is
  still authorized work. Preparing a proposal does not authorize adopting it,
  changing the runtime or collecting data.
- Keep edits small and local. Form a concrete, falsifiable hypothesis from the
  owning code and a nearby test; make the smallest useful edit and immediately
  run a focused check before expanding scope. Reuse existing tests/helpers and
  avoid unrelated cleanup, peripheral tooling or repeated audits merely to fill
  time while the critical path is blocked.
- Mark a blocked task with the precise missing decision/tool/input, then continue
  with other genuinely unblocked work. When only approval-blocked work remains,
  ask a small, batched question with a recommendation instead of inventing scope.
- Give concise progress updates: what changed, what was verified and what
  remains. Do not spawn subagents unless the user explicitly requests delegation.
- Respect requests to pause, stop or finish for the day. A terminal notification,
  status question or documentation-only request does not authorize resuming
  paused implementation or starting a different pilot task.

## Verification and Commits

- Prefer bounded synthetic fixtures for routine arithmetic, codec and integration
  checks. Default tests must need neither downloads nor a GPU and must not
  implicitly start model inference, task-data collection or training.
- After a substantive edit, run the cheapest behavior-scoped check first. Before
  each source checkpoint commit, run focused checks for the changed behavior and
  the default gate from the repository root:

```sh
python -m pytest -q && ruff check . && git diff --check
```

- Run `ruff format --check <changed Python files>` as well. Leave unrelated
  formatting alone, including `.devcontainer/smoke.py`.
- For C/native/runtime changes, ensure the applicable Python/C parity, host,
  ASan/UBSan and Cortex-M55 hard-float compilation controls actually ran; use
  the existing interface tests and documented opt-in gates. Report skips and
  missing prerequisites accurately. Host tests and Arm objects are not linked
  firmware, board execution, stack/memory-fit or task-quality evidence.
- Do not relax tolerances, assertions, deadlines, token/tensor bounds or safety
  checks to obtain green results. Diagnose a failed check before rerunning it;
  a substantive repair permits a new focused check and gate. Preserve the known
  transformer QDQ xfail rather than adjusting its bound.
- Do not rerun an unchanged successful gate merely for reassurance. For
  documentation/instruction-only changes, validate scoped content, references,
  local targets and whitespace; state that the code suite was not rerun.
- Scoped local checkpoint commits are authorized. Commit meaningful tested
  increments periodically, not every probe and not only at the end of a large
  task. Review the diff and stage only files belonging to that checkpoint.
- Use Conventional Commit subjects (`type(scope): imperative summary`, with scope
  optional) and a real bullet body. Do not push, create branches or rewrite
  history unless explicitly requested. Never revert another person's changes.

## Current State (2026-10-22)

Keep this section and the Task List concise and current; a new session resumes
from them. Historical details below are reference material, not new approvals.

- Latest approved package complete: `76aa712` adds the private producer-owned
  C1 fixture recorder (DESIGN.md §7 / REVIEW.md §92): 16 cases, three reused
  complete scenes, zero decision queries and unchanged pre-existing AST nodes.
  It owns copied acquisition/delivery/reference records and a retained audit
  anchor; source-file/profile hashes and generated epochs replace caller labels.
  This is in-memory fixture provenance, not loaded-code attestation, dynamics,
  physical clock/pose/domain/body evidence or qualified runtime input.
  All bounded approvals are exhausted. The next proposal, not approved, is
  tests-only recorder/audit/question compatibility: four reused scenes / 16
  cases / at most six unique motions per coordinator call, explicitly oracle-
  assisted fixture admission, no new geometry/rollouts/persistence/runtime code.
  Numerical/task-quality, collection and integration gates remain open; no
  profile/input adoption or further implementation follows automatically.
  No background job is running; no runtime integration or collection is authorized.
- Latest decisions and results: REVIEW.md §§72-92 supersede conflicting historical
  pilot descriptions below. The user confirmed the decision brief and approved
  autonomous implementation and focused local commits, not pushing.
- The active pilot is rules-first: `path_blocked`, `clear_sector`, `speed_tier`.
  `mode` is absent from the active catalogue and stays unlabeled. Learned
  prediction/camera questions and distillation are deferred.
- Contract milestone complete in `c78925d`: Python decisions default to rules
  catalogue 1, model version 0 (no trained model), complete mask 7, 100-byte full
  frames. Python/C enforce all three answers for OK and reject mode/model claims.
  Legacy catalogue 0, four-head synthetic references and old golden/report bytes
  remain supported and unchanged in meaning; they are not the active pilot.
- Full offline gate: 1,957 passes plus the known transformer xfail, 640 interface
  checks; lint/changed-file format/editor diagnostics, native sanitizers and
  hard-float Arm compilation pass. No deployment or task-quality result follows.
- Privileged simulator truth is now permitted in principle for geometric and
  predictive targets, never as student input. Observation-only human review
  remains for semantic/real-world data. Existing logs stay quarantined; no label,
  collection, split, training or Gaussian risk-budget approval is implied.
- F21 cadence correction complete in `71713ea`: new Config defaults to nominal
  15 Hz ToF acquisition with 20 Hz decisions. Captures are tick-quantized;
  pending delivery/age updates occur each tick and held frames consume no RNG.
  `Config.from_record` preserves legacy per-tick sampling when rate is absent.
  Eighteen new cases cover timing/reset and legacy request/provenance readers.
  No historical log/report was regenerated; source-keyed caches naturally change.
- User approved a fictional configurable profile plus implementation/tests only:
  centered 0.15 m level ToF, flat floor, 0.5 m cylinders and 1 m walls; low/tall
  artificial fixtures. `1293c4e` implements 8x8 point rays with floor/top/side
  returns and masks missing/out-of-range rays. This is not a device emulator.
- Opt-in synthetic odometry errors/delay complete in `059cff7`: tests use a
  0.02 m position-error disk, +/-2 degree heading error and one-tick delay.
  Defaults stay ideal/zero-delay; a separate RNG leaves sensor faults/physics
  unchanged. Delayed ego ages use existing wire fields; input tensor/wire shapes
  stay unchanged. Exact historical metadata schemas preserve legacy replay.
- User approved a separate observation-only heuristic, a configurable 0.03 m
  floor band/default 0.15 s age limit and eight diagnostic wire-loop episodes.
  `05a94f8` implements `sim/rules.py`; one-hot selections are not calibrated
  confidence or proof of clearance. Host-only Python, not embedded firmware.
- Bounded run complete: 4 successes, 2 collisions, 2 timeouts; 25 heuristic clear
  outputs disagreed with blocked geometric references. All 2,866 wire frames,
  eight log hashes and private comparison aggregates audited. Report:
  `sim/reports/rules-baseline-20261020.json`; logs stay ignored/quarantined.
  The eight-run approval is exhausted; no tuning or second batch occurred.
- Approved tests/read-only follow-up: `ebdb9d8` adds opt-in
  `RuleSettings(register_motion=True)`; default remains the original heuristic.
  Complete synchronous ego history registers/rebins delayed hits; gaps, delayed
  odometry and lost current-column support reject. All 1,433 saved default
  decisions reproduce byte-for-byte. Candidate replay admits only 220 frames:
  four false-clears (two new), six false-blocked and 1,213 rejections. Of the old
  25 false-clears, three become blocked, 20 reject and two remain clear. This is
  not quality clearance or candidate closed-loop evidence; no tuning/new runs.
- `a673056` adds mirrored full-history aliases: the current ideal sensor/ego
  input is byte-identical with/without a normal 0.3 m-radius cylinder, yet the
  curved-braking geometric answer differs. This is not just a noise, small-object
  or registration problem; a deterministic input-only method cannot distinguish
  these pairs. Abstention remains necessary where evidence is ambiguous.
- User chose coverage-first design work, not a third heuristic or narrower
  targets. DESIGN.md §7 / REVIEW.md §77 define coverage requirements; no new
  FoV, sensor, scene-size limits, history/map format or input change is adopted.
  C1 draft is now prepared (REVIEW.md §78): eight simultaneous virtual views
  with 22.5-degree downward pitch distinguish the normal aliases, but still
  miss a 5 mm-radius cylinder on the straight braking path. Not an adopted
  sensor, schema, minimum object size or qualified clearance method.
  User approved the synthetic prototype only; `a3df1f5` adds explicit opt-in
  C1 captures and bounded history inspection in `sim/diagnostics.py`, with
  experimental-only data, endpoint registration and no free-space/decision
  qualification. Sixty-one new tests preserve both gains and the slender alias;
  existing APIs/defaults/normal inputs/wire are unchanged (REVIEW.md §79).
  User then approved synthetic-only qualification with radii 0.05-0.30 m and
  heights 0.05-1.0 m in static flat-floor scenes with existing outer walls.
  `d1ad3a2` adds a bounded conditional all-turn sweep-enclosure exclusion;
  exact low-height ray prefixes exclude continuous cylinder-center cells, not
  just samples. Independent envelope membership and a collision-free current
  body must be explicitly declared. Forty-three new cases preserve unknown
  blocked/budget/stale cases and the out-of-envelope alias (REVIEW.md §80).
  This is not numerical certification, physical clearance, a complete rules
  baseline or global restriction of simulator objects. Runtime/wire/defaults
  are unchanged. Domain/return/error evidence and task-quality gates remain;
  no collection, integration, risk-budget or hardware approval follows.
  Missing-return aliases stay unknown and clear turning frames pass (§81).
  `e6488f2` adds ideal geometric occlusion/prefix checks with a height contrast
  (§82), not physical optical evidence. `562e3d2` adds explicit `turn_rate=0`
  capsule exclusion with a separate experimental result schema (§83); defaults
  remain the old disk. Rear-obstacle straight-clear fixtures now exclude, while
  nonzero turns, blocked/masked/wall/near-contact cases stay unknown. Fifty new
  cases, 18 exact default comparisons and resolved-caller checks pass. The zero
  turn is a declaration for both reaction and braking, not an inferred fact;
  neither the surrounding disk nor any curved maneuver is qualified by it.
  `65fecf0` adds separate opt-in curved tubes with declared reaction and braking
  rates (§84). Omitted braking turn means zero, matching the centre reference;
  explicit left/right braking also passes. The whole-cell search and wall bounds
  expand a bounded polyline by its numerical allowance. All 160 new cases,
  36 exact disk/straight comparisons and 23 resolved callers pass; default paths
  stay unchanged. This is conditional ideal evidence, not numerical certification,
  physical clearance, a complete question bundle or runtime integration.
  `cc7f961` and `afd0f0f` add eight one-segment counterexamples (§85): actual
  collisions outside the unexpanded polyline stay unknown, and occupied points
  inside an outer tube do not imply collision. Runtime/bounds remain unchanged.
  The user then approved the staged package in DESIGN.md §7 (§86). `d82fca3`
  adds Stage A occupied-return witnesses: complete above-floor rounding/transform
  enclosures and strict inner-body containment, never outer-tube membership.
  All 37 new cases pass, including low cylinders and rounded-floor abstention.
  `5c643f7` completes Stage B (§87): conservative three-question candidates,
  fixture-only goals, unknown/conflict abstention and 30 new cases. Both stages
  remain synthetic-only, not numerical/physical certification, runtime rules,
  representative task quality or completion of Task 6/9.
- Remaining F21/M2 work: missing/occluded-return evidence, representative scene
  envelope/diversity and sensor/rule qualification. Keep both this unsuccessful
  heuristic and the unchanged legacy proxies diagnostic-only. No task labels,
  accepted dataset/splits, training, Gaussian risk policy or hardware approval.
- ST tools remain absent and no board is attached. User-side licence/install,
  procurement and sending the existing teacher provenance request remain pending.
  No teacher/model run, accepted task dataset or trained student exists.
- User-authorized cache cleanup removed the three pinned teacher packages;
  reports, quarantined logs and the environment remain. Teacher/tokenizer work
  needs asset restoration and manifest verification; old offline cache checks
  must not be assumed still valid. More disk space renews no experiment approval.

### Historical Checkpoints

- Design plus INT8 Vela 2.0 9B and d3-flash teacher loaders
  ([teacher/vela_int8.py](teacher/vela_int8.py),
  [teacher/d3_int8.py](teacher/d3_int8.py)) and both validators, plus d3-mini
  BF16 support and a working CPU-only rover trainer environment in
  [sim/rover.py](sim/rover.py). No student, reviewed dataset, linked board
  firmware, ST compiler report or board measurement exists yet.
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
  stay review/data-blocked; the offline prompt-cost result is recorded below.
- Offline decision-preparation cost study is complete in
  `teacher/prompt_budget.py --profile-input-costs`: the same 80 existing inputs
  with both cached pinned tokenizers, full/literal/typed-float32 forms only.
  Complete counts reproduce 80/65/63 over-budget failures; all 45 full-history
  inputs fail in each form. Standalone warm ToF-history fields cost 4,771-8,432
  tokens; typed row tables 2,635-5,131. Fragment counts are explicitly nonadditive,
  not savings/lower bounds or valid request budgets; none is used as a request.
  Reports: `teacher/reports/input-cost-d3-{flash,mini}-20261016.json`; all 240
  representation rows and 160 exact draft round trips per model independently
  audited, including full/state/field retokenization and provenance hashes.
  Seven new tests; 77 focused pipeline/preflight checks, 314 repository passes
  plus the known transformer expected failure, lint/format/diagnostics clean.
  DESIGN.md §7 and REVIEW.md §28 record limits and still-unaccepted strategy
  choices. No new episode, task labels/dataset, inference/model runtime,
  training, dependency/download or hardware action. Both approved preparation
  tasks are complete; mode/target, representative-data and input-strategy review
  remain pending. ST tools are still absent; full inputs/history/ceiling unchanged.

- Approved (2026-10-16): a bounded d3-mini INT8 experiment at pinned revision
  `6d8971f464d6f9d4c5af7d9a8d75f3aa03be4f59`, cached files/full manifest
  verification only. First compare INT8 with streamed BF16 on the existing
  diagnostic suite at 2,048 tokens. Continue only after reviewing those results
  to an opt-in full-input resource probe at 4,096/8,192/12,288, with a 10 GiB
  PyTorch allocation cap and abort on OOM/cap failure. Keep normal 2,048 limits,
  inputs/history and all draft representations unchanged. No live labeling,
  dataset, training, dependency/download or hardware-integration approval.
  User reconfirmed `mode` remains unlabeled pending observable semantics.

- Bounded mini INT8 parity completed (2026-10-16): full cached package verified;
  unchanged 25 requests/31 questions/85 probabilities, maximum/mean delta
  0.0154966/0.00157733 versus streamed BF16, zero flips. Allocated after load:
  4.006 GiB; peak reserved load/candidate/reference: 4.699/4.334/4.406 GiB under
  the 10 GiB PyTorch cap, with no OOM. Report:
  `teacher/reports/d3-mini-int8-parity-capped-20261016.json`. The parity review
  supports the already-approved resource-only continuation, not task accuracy,
  labels or a new quality threshold. Normal mini stays BF16/2,048; INT8 is
  explicit opt-in. Twelve new CPU tests; 27 d3 checks, full suite 326 passes
  plus known transformer expected failure; lint/format/diagnostics clean.
  DESIGN.md §4 and REVIEW.md §29 record limits. Resource continuation is below.

- Approved resource-only continuation completed (2026-10-16): three existing
  unchanged full inputs (startup clear, warm clear, warm slalom), 3,421/7,616/
  10,705 tokens with one/eight/eight valid history ticks, tested against
  4,096/8,192/12,288 ceilings. Six admitted cases completed; three budget
  rejections, no truncation/OOM/cap failure. Largest peaks: 6.478 GiB allocated,
  7.313 GiB reserved under the 10 GiB PyTorch cap. All answer values discarded;
  zero mode labels. Report: `teacher/reports/d3-mini-context-resource-capped-20261016.json`;
  complete input/token/provenance hashes independently checked on CPU. No actual
  12,288-token sequence, longer-context BF16 parity or task quality was tested.
  Both approved stages are complete; normal BF16/2,048 and inputs/history/drafts
  unchanged. No live labeling, dataset, training, new episode, dependency/download
  or hardware work. Ten new tests; 37 d3 checks, full suite 336 passes plus the
  known transformer expected failure; lint/format/diagnostics clean. DESIGN.md
  §4 and REVIEW.md §30 record limits. Live-use strategy/targets/data still need
  review, mode stays unlabeled, and ST tools/board remain unavailable.

- Approved (2026-10-16): bounded longer-context INT8-versus-streamed-BF16 parity
  on the same three existing full inputs at 4,096/8,192/12,288 ceilings, using
  only the fully verified cached pinned mini package and the 10 GiB PyTorch cap.
  Abort the whole run on OOM/cap failure; retain only numeric deltas/flips,
  timing, memory and provenance, discarding answer values. Mode stays unlabeled;
  normal BF16/2,048 defaults, inputs/history and drafts unchanged. No task
  labels/dataset, training, download, dependency or hardware approval.

- Bounded longer-context parity completed (2026-10-16): same three full inputs
  and exact token/provenance hashes as the resource probe. Six admitted INT8/
  streamed-BF16 comparisons, three budget rejections, no truncation/OOM/cap
  failure. Across 30 values, max/weighted mean delta 0.0206704/0.00752864 and
  two flips: the same warm-clear observation at 8,192/12,288, not two distinct
  examples. Startup and warm slalom had no flips. Peak allocated/reserved:
  6.498/7.313 GiB. Report: `teacher/reports/d3-mini-context-parity-capped-20261016.json`;
  all answer values discarded, zero mode labels. No argmax-parity or task-
  quality clearance; only three distinct choice inputs, not noul/score or an
  actual 12,288-token sequence. Ten new tests; 47 d3 checks, 346 repository
  passes plus known transformer expected failure; lint/format/diagnostics and
  CPU evidence audits pass. DESIGN.md §4 and REVIEW.md §31 record findings.
  Normal BF16/2,048, full inputs/history and drafts remain unchanged. No live
  labeling, task dataset, training, new episode, dependency/download or hardware
  work. Next review: target/data and input/teacher strategy; keep mode unlabeled
  and current defaults meanwhile. ST tools/board remain unavailable.

- Approved (2026-10-16): CPU-only blind human-review preparation on at most
  32 existing observations, preserving full student-visible input/history and
  source/group provenance. Add blank packets, strict format validators and
  fake-reviewer tests only. Keep the three rules diagnostic proxies and mode
  unlabeled. No actual annotations/reviewed dataset, locked task splits,
  teacher inference, training, new episodes, dependencies/downloads, hardware
  work or changes to accepted defaults.

- Blind review preparation completed (2026-10-16) in `teacher/review.py`, reusing
  the unchanged full renderer without invalidating its source/cache identities.
  The bounded CPU-only run exported 32 blank packets from existing clear and
  obstacle smoke ticks 0-15; 18 full histories, two known episode identities.
  All states/source/frame/provenance and hashes independently audited. No
  teacher/proxy suggestions, truth/actions, annotations or mode labels; family
  groups and partitions remain unresolved. Packet data stays ignored under
  `teacher/cache/`; evidence: `teacher/reports/review-preparation-20261016.json`.
  Strict renderer-backed packet validation and fake-only review format tests
  reject mode labels and any scope promotion. Twenty-eight new cases; 77 pipeline
  tests, full suite 374 passes plus known transformer expected failure; lint,
  format/editor diagnostics and audits pass. DESIGN.md §7 and REVIEW.md §32.
  Tasks 6/9 still await target/evidence/cohort review and actual reviewed data;
  no training, inference, download/dependency, hardware or accepted-default change.

- Review-validator follow-up (2026-10-16): four reproduced regressions showed
  Python equality accepting boolean/float question IDs and numeric unreviewed
  flags after packet rehashing. Fixed metadata now uses existing canonical JSON
  comparisons to preserve JSON types. All 81 pipeline tests and 378 repository
  tests pass plus the known transformer expected failure; lint, changed-file
  format and editor diagnostics pass. All 32 unchanged historical blank packets
  pass the stricter validator and their recorded file hash matches. No packet or
  report was regenerated; old tool hashes describe the original export version.
  DESIGN.md §7 and REVIEW.md §33 record the repair. No policy, labels, dataset,
  splits, inputs/defaults, inference, training, dependency or hardware change.

- Explicit policy decisions (2026-10-16): user kept navigation targets
  unaccepted pending independent definitions; the three rules stay diagnostic
  proxies and mode stays unlabeled. User adopted observation-only human review
  of complete student-visible input/history, with abstention and no privileged
  truth, actions or teacher/proxy suggestions. User also adopted diagnostic-only
  quarantine for all current logs and source/template-family review before any
  task cohort or split acceptance. This is policy adoption only, not actual
  annotations/import, reviewed data, family assignments, split locks, changed
  inputs/thresholds, inference or training. DESIGN.md §7 and REVIEW.md §34 record
  the answers and remaining per-question definition checklist. Do not re-ask
  the adopted evidence/quarantine questions; target definitions and actual
  reviewed cohort/data remain blocked.

- Approved (2026-10-16): prepare a concrete simulation-only navigation-target
  proposal and synthetic-only checks. Candidate definitions and parameters are
  unaccepted; keep current proxy rules, inputs, defaults and token limits
  unchanged. No episode generation, annotations/task dataset, inference,
  training, download/dependency or hardware work. Target adoption and real-data
  use still require review; observation-only abstention and current-log
  quarantine remain adopted.

- Concrete navigation-target proposal completed (2026-10-16), unaccepted:
  DESIGN.md §7 and REVIEW.md §35 specify candidate reaction/braking sweeps,
  goal-ranked turn options, momentum-preserving speed-capacity tiers and mode
  abstention. Ten synthetic checks include two artificial world pairs with
  identical complete rendered eight-tick input/history but opposite swept-body
  collision results. No actual log, episode, label or dataset was generated.
  Other cases pin circle contact and nominal stopping/momentum arithmetic.
  Ninety simulator tests, 388 repository passes plus known transformer expected
  failure; lint/format/editor and doc checks pass. Runtime source, catalogue,
  inputs/defaults, token limits and all original artifacts are unchanged.
  Curved-sweep/ranking execution and evidence/uncertainty models are not
  implemented or qualified; at-rest direction semantics still need review.
  Tasks 6/9 remain blocked on adoption/independent target evidence and actual
  reviewed data. No inference, training, dependency/download or hardware work.

- Approved (2026-10-16): adopt the first three proposed geometric meanings for
  simulation and implement an isolated CPU-only ideal-geometry reference with
  artificial-fixture tests only. Unknown/numerically unresolved cases abstain;
  at-rest sector choice abstains, mode stays unlabeled, contact includes tangency.
  No physical-safety claim or real-input evidence qualification. Keep existing
  proxies, input/defaults and token limits unchanged; no episode generation,
  actual annotations/datasets/splits, inference, training, dependency/download
  or hardware work. This does not approve an observation/episode labeler.

- Synthetic reference completed (2026-10-16) in `sim/navigation.py` after
  explicit simulation-semantics adoption. Requires synthetic-only opt-in and
  complete artificial Scenario geometry; no observation/log/CLI labeling path.
  Analytic straight sweeps, bounded curved integration/chord checks, endpoint
  error-aware ranking and numerical abstention; at-rest sector abstains, mode
  stays absent. Twenty-five oracle cases plus the ten draft checks pass; 115
  simulator tests and 413 repository passes plus known transformer expected
  failure; lint/format/editor/doc checks pass. Gauss-Legendre endpoint checks
  and the existing exact-input geometry aliases pass. Numerical floating-point
  allowances are not formal certification or sensor uncertainty bounds.
  Existing runtime/proxies, inputs/defaults, token limits and artifacts are
  unchanged. No episodes, actual labels/dataset/splits, inference, training,
  dependency/download or hardware work. DESIGN.md §7 and REVIEW.md §36.
  Tasks 6/9 remain blocked on reviewed target evidence/labels, mode semantics
  and actual reviewed cohort/data. Do not re-ask first-three simulation adoption
  or the already-adopted reviewer-evidence/quarantine policy questions.

- Approved (2026-10-16): bounded CPU-only provenance-audit tooling and a read-only
  run over at most 16 existing diagnostic logs, plus synthetic tests and a
  non-label evidence report. Compare file/metadata/config and declared
  scene/template evidence only; unknown lineage stays unresolved and all logs
  remain quarantined. Privileged metadata is separate diagnostic evidence, not
  reviewer input. No accepted family/cohort/split assignments, episodes,
  annotations/dataset, inference, training, downloads/dependencies, hardware or
  default/input changes.

- Diagnostic provenance audit completed (2026-10-16) in `teacher/provenance.py`:
  bounded metadata-only tooling and 18 synthetic cases, then an approved
  read-only run on 16 existing logs (22,245,926 bytes; 1,413 lines). All file,
  metadata/config/scenario/geometry hashes and comparisons independently audited.
  Distinct file hashes still share three exact declared-geometry match groups
  and four scene-name groups; these are candidate evidence, not family acceptance
  or independence proof. Two config-match groups; no byte-duplicate group.
  Report: `teacher/reports/provenance-audit-20261016.json`. All source/template
  families/partitions remain unresolved, logs quarantined, zero annotations or
  accepted family assignments. Body observations/actions/labels are neither
  validated nor reproduced. All 54 evaluation/provenance tests and 431 repository
  tests pass plus the known transformer expected failure; lint/format/editor/doc
  checks pass. DESIGN.md §7 and REVIEW.md §37. No dataset, episode, inference,
  training, dependency/download, hardware or accepted-input/default change.
  Tasks 6/9 still await reviewed target evidence/mode and actual family/cohort/data.

- Synthetic-oracle numerical repair (2026-10-16): two reproduced regressions
  showed small yaw increments lost at initial headings +/-1e16, producing about
  0.0236 m endpoint disagreement between equivalent orientations. The reference
  now bounds its initial yaw with atan2(sin(yaw), cos(yaw)) before accumulating
  turns. Both cases pass; 117 simulator tests and 433 repository passes plus the
  known transformer expected failure; lint/format/editor/doc checks pass.
  Existing simulator, inputs/defaults, semantics and artifacts are unchanged.
  DESIGN.md §7 and REVIEW.md §38 record the repair. No label/data, inference,
  training, dependency/download or hardware action; Tasks 6/9 remain blocked.

- Approved (2026-10-16): CPU-only synthetic ray-witness feasibility prototype
  and artificial checks only, with no use on existing logs or annotations.
  Exact current-frame hits may support a straight-braking blocked witness;
  missing hits never imply clear. Noise, unregistered delay, unsupported curves
  and numerical ambiguity abstain. Zero noise/current-frame assumptions are
  artificial fixtures, not accepted-default changes or real-input qualification.
  Keep proxies, inputs/history/token limits unchanged; no episodes, datasets,
  splits, inference, training, downloads/dependencies or hardware work.

- Synthetic ray-witness study completed (2026-10-16) in `sim/navigation.py`:
  explicit artificial-only opt-in, eight exact current-frame rays, straight
  braking footprint and positive-only witnesses. Missing/masked/saturated hits
  never imply clear; noise, delay/latency, curves and numerical ambiguity
  abstain. Normal defaults remain unqualified and unchanged. Twenty-nine new
  checks include visible blocked, clear-but-unknown and hidden-blocked-but-unknown
  geometry comparisons; no existing logs, rollout or data artifact used.
  All 146 simulator tests and 462 repository passes plus known transformer
  expected failure; lint/format/editor/doc checks pass. DESIGN.md §7 and
  REVIEW.md §39 record limitations: no real-input qualification, negative labels,
  calibration or physical claim. No task labels/dataset/splits, inference,
  training, dependency/download or hardware action. Tasks 6/9 remain blocked on
  reviewed uncertainty/registration/target evidence, mode and actual cohort/data.

- Approved (2026-10-16): CPU-only synthetic bounded-error draft and checks,
  with no existing-log use. Explore explicit artificial range, translation and
  heading-error bounds for positive witnesses only; bounds are fixture
  assumptions, not measurements or Gaussian-sigma conversions. Preserve the
  exact-ray API and normal-default rejection. No uncertainty-policy adoption,
  real-input qualification, negative/clear labels, inputs/history/token changes,
  episodes, annotations/dataset/splits, inference/training, dependency/download
  or hardware work.

- Synthetic bounded-error draft completed (2026-10-16): separate additive
  `probe_synthetic_bounded_ray_witness` accepts explicit artificial range,
  translation and heading-error bounds, then requires the complete assumed
  hit-location error ball strictly inside the braking footprint. Bounds are
  assumptions, not measurements, Gaussian-sigma conversions or an adopted
  uncertainty policy. No clear/negative labels; unsupported evidence abstains.
  The exact probe and all existing oracle functions/signatures are AST-identical
  to the prior commit; normal-default/age/curve rejection remains unchanged.
  Twenty-six new cases include a 72-point perturbation cross-check; 172 simulator
  tests and 488 repository passes plus known transformer expected failure, with
  clean lint/format/editor/doc checks. No existing logs, rollouts, artifacts,
  labels/dataset/splits, inference/training, dependency/download or hardware work;
  inputs/history/defaults/token limits unchanged. DESIGN.md §7 and REVIEW.md §40.
  Task 6 still needs reviewed uncertainty/registration/target evidence and mode;
  Task 9 still needs accepted families/cohort and reviewed task data/splits.

- Approved and completed (2026-10-16): documentation-only range-error and
  frame-registration evidence-qualification plan in DESIGN.md §7 and REVIEW.md
  §41. Six proposed stages cover domain/ray compatibility, independent reference
  uncertainty and provenance, acquisition-to-reference timing/transforms,
  deterministic versus empirical uncertainty/outliers, independent qualification
  lineage and versioned acceptance/requalification. No bounds, sample counts,
  confidence/failure levels, equipment, groups or physical domain are selected.
  No policy adoption, measurements, code/adapter, log use, labels/data/splits,
  inference/training, dependencies/downloads or hardware work. Current synthetic
  rejection, inputs/history/defaults/token ceiling and quarantine stay unchanged.
  Doc reference/local-target/whitespace/scope checks pass; the last code gate
  remains 488 passes plus the known expected failure, not newly rerun evidence.
  Task 6 still needs reviewed claim/domain, references/collection authorization,
  actual uncertainty/registration/target evidence and mode; Task 9 still needs
  accepted family/cohort review and reviewed task data/splits.

- Approved and completed (2026-10-16): CPU-only synthetic static-point frame
  registration reference/tests in `sim/navigation.py`, with explicit artificial
  mounting/acquisition/reference poses and times. No observation/range/log
  adapter, extrapolation, clock/error qualification, witness/label or exporter.
  Missing evidence/overflow stays unknown; successful `registered_fixture`
  results are assumption-tagged, training-disabled and real-input-unqualified.
  Relative-coordinate composition preserves local points under a large common
  world offset. All prior navigation functions/signatures are AST-identical;
  normal-noise/default-latency/age/curve witness rejection remains unchanged.
  Thirty-six new cases; 208 simulator tests, 524 repository passes plus known
  transformer expected failure; lint/format/editor/doc checks pass. DESIGN.md §7
  and REVIEW.md §42 record scope/limits. No existing-log application, study
  episodes, task labels/data/splits, live teachers/training, dependency/download
  or hardware action; inputs/history/defaults/token ceiling/quarantine unchanged.
  Tasks 6/9 still require reviewed real uncertainty/registration/target evidence,
  mode and actual accepted family/cohort/task data; ST/board gates remain blocked.

- Registration validation repair (2026-10-16): seven oversized-integer point,
  pose and timestamp regressions reproduced escaped `OverflowError`; conversion
  boundaries now consistently reject unrepresentable evidence with `ValueError`.
  All 22 rejection cases, 215 simulator tests and 531 repository tests pass plus
  the known transformer expected failure; lint/format/editor/doc checks pass.
  DESIGN.md §7 and REVIEW.md §43 record the repair. No signature, transform,
  witness guard, scope/policy, data, input/default, dependency or hardware change;
  Tasks 6/9 and ST/board gates remain blocked.

- Approved and completed (2026-10-16): separate CPU-only synthetic registration
  error propagation in `register_synthetic_bounded_points`, with explicit point
  and mounting/acquisition/reference translation/heading-error assumptions.
  Distinct rotation lever arms and translation-error sums give an algebraic
  enclosure, not measured uncertainty or certified floating-point bounds. No
  exact-pose claim, witness integration, observation/log/range adapter, temporal
  qualification or label/data exporter. All seven prior navigation functions/
  signatures are AST-identical to the repair commit; existing rejection stays.
  Thirty new cases include 864 independently composed perturbations; 245
  simulator tests and 561 repository passes plus known transformer expected
  failure; lint/format/editor/doc checks pass. DESIGN.md §7 and REVIEW.md §44.
  No log application, study episodes, task labels/data/splits, live teachers/
  training, dependencies/downloads or hardware; inputs/history/defaults/token
  ceiling/quarantine unchanged. Tasks 6/9 still need reviewed real uncertainty/
  registration/target evidence, mode and accepted family/cohort/task data; ST/
  board gates remain blocked. Bounds are assumptions, not policy adoption.

- Approved and completed (2026-10-16): full CPU-only synthetic registered-point
  positive-witness package in `probe_synthetic_registered_witness`. Explicit
  artificial obstacle membership, bounded point/pose registration and exact
  motion/footprint assumptions only; whole-ball strict containment or unknown,
  never clear/negative labels. Default noise/latency and current turns abstain;
  all eight existing navigation functions/signatures are AST-identical. Source-
  scale numerical guards repair two exact-rational cancellation false positives;
  no numerical certification or physical qualification. Forty-one new cases,
  three independent world comparisons and 2,592 scalar/world perturbation checks;
  286 simulator tests, 602 repository passes plus known transformer expected
  failure; lint/format/editor/doc checks pass. DESIGN.md §7 and REVIEW.md §45.
  No existing logs, study episodes, persisted data artifacts, task labels/data/
  splits, live teachers/training, dependencies/downloads or hardware. No input/
  history/default/token/quarantine change, observation/range adapter, wire/CLI or
  data exporter. Task 6 still needs reviewed real uncertainty/registration/target
  evidence and mode; Task 9 still needs accepted family/cohort/task data/splits.
  ST/board gates remain blocked; all bounds/occupancy are fixture assumptions.

- Approved (2026-10-16) and completed (2026-10-19): CPU-only bounded sensor
  diagnostic tooling/tests in `sim/diagnostics.py` and four new prefixes of at
  most 32 ticks, preserving normal Config (including the 400-tick environment
  limit), student observations and RNG behavior. Privileged capture/reference
  poses, times and noiseless ranges stay separate; references share simulator
  geometry, not independent physical metrology. Seed 20261019 plus scene index:
  clear/obstacle/corridor were censored at 32 ticks; slalom collided at tick 31.
  The turn-schedule controller is diagnostic-only, not an expert. 131 observations,
  eight no-delivery warmups; all four file/observation/source hashes and scalar
  ray/pose/residual checks audited. Report:
  `sim/reports/sensor-diagnostics-20261019.json`. Conditional observed range RMS
  0.0199296 m and maximum absolute residual 0.0687828 m over 3,535 selected zones
  are not accepted error bounds or coverage claims. Clipped/missing/censored
  exclusions and shared-model dependence remain explicit. Eighteen new cases;
  304 simulator tests, 620 repository passes plus known transformer expected
  failure; lint/format/editor/doc checks pass. DESIGN.md §7 and REVIEW.md §46.
  No witness application, task labels/dataset/splits, accepted bounds/families,
  inference/training, dependency/download or hardware work; inputs/history,
  defaults/token ceiling/quarantine unchanged. Tasks 6/9 and ST/board remain blocked.

- Diagnostic output-path repair (2026-10-19): a no-collection regression proved
  that a report path ancestral to the episode directory passed preflight and
  started collection before failing at report creation. Resolved paths now
  reject equality or containment in either direction before mkdir/collection.
  Three regression cases pass; 307 simulator tests and 623 repository passes
  plus the known transformer expected failure; lint/format/editor/doc gates
  pass. No new study episode or historical report/log regeneration; the report's
  source hashes remain those of the original `73a61e8` export. DESIGN.md §7 and
  REVIEW.md §47 record the repair. Scope/data/default/input and Task 6/9 gates
  are unchanged; `.devcontainer/tools` is still empty.

- Approved and completed (2026-10-19): documentation-only concrete simulation
  task-data protocol proposal in DESIGN.md §7 and REVIEW.md §48. Unaccepted
  candidate: eight future normal-Config readiness episodes, two per scene,
  deterministic seeds and at most 32 unique full-input blank review windows;
  no collection, packet export, oracle/log adapter, annotation/import or data
  acceptance occurred. Proposed independent human review uses observation-only
  evidence with abstention; private diagnostic truth cannot force task labels.
  Explicit positive/negative/sector/tier admission checklists expose remaining
  uncertainty/registration/spatial-coverage gates. At most four candidate scene
  groups cannot satisfy five independent purposes; no family/split assignments.
  All numeric/procedural choices remain proposals, not adopted requirements.
  Mode stays unlabeled, current logs quarantined, inputs/defaults unchanged.
  Doc/reference/local-target/scope checks pass; 623 passes plus the known expected
  failure remain the last code gate, not newly rerun proposal evidence. Next
  decision: accept/modify the simulation-only claim/domain and admissible evidence
  conventions before collection or labels. Tasks 6/9 and ST/board stay blocked.

- Approved and completed (2026-10-19): full CPU-only readiness package in
  `teacher/readiness.py`: fixed eight fresh normal-Config episodes, at most
  32 blank full-input projections, private source audit, tests, run and evidence
  verification. This authorizes simulator/provenance/projection readiness only,
  not protocol-wide adoption or label/uncertainty qualification. Seeds 20261020-
  20261027: eight successes, no collisions/timeouts, 1,130 observations; 32 blank
  projections, 24 full histories, 25 distinct selected inputs. All eight reset
  states match exactly: retaining them would force these episodes into one
  purpose under the no-cross-purpose exact-input rule, not accept a family.
  Three repeated declared-geometry pairs and four scene-name pairs are candidate
  metadata evidence only. Report: `teacher/reports/readiness-pilot-20261019.json`.
  Eight logs and both packet artifacts stay ignored/quarantined; only the blind
  bundle is reviewer input. Opaque random IDs/shuffling and mode-0600 audit files
  separate private lineage, not guarantee anonymity. All source/artifact/frame
  hashes, histories, selections, blankness and match groups audited on CPU.
  Twenty new readiness tests; 101 pipeline tests, 643 repository passes plus
  the known transformer expected failure; lint/format/editor/doc checks pass.
  DESIGN.md §7 and REVIEW.md §49 record scope and limits. No actual annotations/
  import, dataset/family/split acceptance, bounds, oracle/witness use, inference/
  training, dependencies/downloads or hardware. Inputs/history/defaults/token
  ceiling unchanged. Task 6 still needs admissible target evidence and mode;
  Task 9 still needs reviewed cohort/data and splits. Both bounded run approvals
  are exhausted; no further study episodes without approval. ST/board blocked.

- Approved and completed (2026-10-19): simulation-only Gaussian coverage
  proposal and 20 model-free synthetic checks, no log application or new study
  episodes. DESIGN.md §7 and REVIEW.md §50 derive a simultaneous marginal-normal
  union bound for a prospectively declared draw budget, without independence.
  Examples use 64/512/25,664/205,312 draws; all failure budgets and claim units
  remain unaccepted. Clipping/final float32 checks and rare-error/selection
  counterexamples distinguish model coverage from posterior confidence or
  precision among selected positives. Numerical/ray, registration, motion and
  return-membership evidence remain unqualified; no runtime API or witness guard
  changed. All 327 simulator tests and 663 repository tests pass plus the known
  transformer expected failure; lint/format/editor/doc gates pass. No existing
  log/artifact used or regenerated, labels/data/splits, live teacher/training,
  dependency/download or hardware action. Inputs/history/defaults/token ceiling,
  quarantine and Task 6/9 gates unchanged. Next decision: accept/modify a
  simulation-only claim unit/domain and failure convention before implementation
  or application; proposed default remains no adopted risk budget and abstention.

- Explicit user decision (2026-10-19): keep the Gaussian range-failure convention
  unaccepted and retain strict abstention (DESIGN.md §7, REVIEW.md §51). Neither
  illustrative budget was adopted. No runtime API/application, new collection,
  task labels, evidence qualification or training is unlocked. All remaining
  Task List items remain blocked; do not re-ask the same risk-choice question
  without a new claim/domain or evidence direction from the user.

- Readiness selection repair (2026-10-19): four synthetic regressions reproduced
  admission of a missing or mismatched closing summary, including boolean/float
  tick aliases. The selector now requires a final summary with a strict integer
  tick matching the last rendered observation. All 24 readiness checks and 667
  repository tests pass plus the known transformer expected failure; lint,
  format and editor diagnostics pass. Historical readiness artifacts/report and
  their original exporter hashes remain unchanged; no study was rerun. DESIGN.md
  §7 and REVIEW.md §52 record the repair. No evidence-policy, input/default,
  label/data, collection, training or hardware scope change; all gates remain.

- Approved (2026-10-19): host-only portable C protocol parsing, CRC and bounded
  stream recovery against the unchanged provisional wire format/golden vectors,
  host tests, Arm compile checks where available, documentation and local commits.
  No board integration, broader firmware runtime, dependencies, labels/training,
  policy or interface freeze is authorized. Core decoding is implemented in
  `firmware/micro_classifier_codec.c`: strict state/decision validation, fixed
  native outputs, no packed-wire casts/allocation/HAL and unchanged outputs on
  failure. All five golden frames and 46 new C checks pass; 108 interface tests,
  713 repository passes plus the known transformer expected failure. Host GCC
  13.3 and Arm GCC 13.2 produce objects, including Cortex-M55 compilation;
  fast-math builds are rejected. Lint/format pass. Stream recovery was the next
  approved portion at this core checkpoint, not completed Task 13. DESIGN.md
  §2 and REVIEW.md §53 record the approval and core limits.

- Approved host-C package completed (2026-10-19): allocation-free callback stream
  recovery now retains a 128-byte framing buffer plus fixed metadata, validates
  before delivery and saturates rejected-candidate counts. Caller owns timeout
  reset and serialized stream access; callback packets are borrowed only until
  callback return. All golden chunk splits and byte-corruption recovery, nested
  packets, resets/arguments and tolerance boundaries pass. C/Python agree on
  2,000 seeded CRC-repaired mutations and mixed-stream packets/buffers/counters;
  ASan/UBSan pass exact short buffers and 4,096 random buffers. Contract-drift and
  nonfinite-math build guards pass. All 67 C checks, 129 interface tests and 734
  repository tests pass plus the known transformer expected failure; real host/
  Cortex-M55 objects, lint/format/editor/doc gates pass. DESIGN.md §2 and
  REVIEW.md §54 record the limits. No linked firmware/board execution, timing,
  memory-fit, data/labels, inference/training, dependency, licence or policy work.
  This exhausts the approved package, not Task 13's broader firmware gates.

- Approved (2026-10-19): extend host-only C tooling with caller-buffer state/
  decision encoders and Python/golden round-trip tests, host/sanitizer/Arm checks,
  documentation and local commits. No interface freeze, transport/history/
  inference runtime, board integration, data/labels/training, dependencies or
  policy changes. Core encoders now share validation/schema/confidence with the
  decoders, use fixed temporary frames and write output/length only on success.
  Decision input confidence is ignored and recomputed from binary32 probabilities;
  mask-selected metadata is validated. Thirty new tests pass; all 97 C checks,
  159 interface tests and 764 repository tests pass plus the known transformer
  expected failure, with clean lint/format. Encoder-specific sanitizer and
  seeded round-trip follow-ups were next at this core checkpoint.
  DESIGN.md §2 and REVIEW.md §55 record the approval and core limits.

- Approved encoder extension completed (2026-10-19): all 32 state-validity masks,
  float32 extremes/signed zero and 500 synthetic states plus 500 synthetic
  decisions encode exactly like Python and round-trip through native decoders
  and both streams. Four accepted noncanonical confidence cases canonicalize
  like Python; absent/unused storage is not serialized. ASan/UBSan pass actual
  output allocations from zero through each golden length plus one, and all
  256 option-count values, alongside existing decoder/stream checks. All 104 C
  checks, 166 interface tests and 771 repository tests pass plus the known
  transformer expected failure; host/Cortex-M55 objects, lint/format/editor/doc
  gates pass. DESIGN.md §2 and REVIEW.md §56 record finite-test limits. No
  simulator/log/data generation, teacher inference/training, dependency/licence,
  linked firmware or board action occurred. This completes the approved encoder
  package; broader Task 13 and all other data/hardware gates remain blocked.

- Approved (2026-10-19): host-only C eight-tick state-history reference with
  explicit caller-declared gaps, synthetic tests, host/sanitizer/Arm checks,
  documentation and local commits. Preserve validated host states; export
  oldest-to-newest with leading invalid slots and masks. No inferred timeout,
  ordering, interpolation or safety policy, ToF/tensor packing, inference,
  board integration, data/labels/training, dependencies or interface freeze.
  Core in `firmware/micro_classifier_history.c` shares the existing codec state
  validator; rejected pushes do not advance history, and gaps are explicit.
  Thirteen history tests and two additional compile checks pass: 119 C checks,
  181 interface tests and 786 repository passes plus the known transformer
  expected failure; lint/format and host/Cortex-M55 objects pass. Seeded history
  and native sanitizer follow-ups remain approved work. DESIGN.md §2 and
  REVIEW.md §57 record the bounded scope and core limits.

- Approved state-history package completed (2026-10-19): 1,024 seeded synthetic
  operations match an independent Python eight-slot queue, including resets,
  gaps, rejected states and exact serialized retained values. Native ASan/UBSan
  passes 1,024 mixed operations, masks/copies and all 248 out-of-range uint8
  cursors with no writes on rejection, plus null arguments and existing codec
  safety checks. All 120 C checks, 182 interface tests and 787 repository tests
  pass plus the known transformer expected failure; host/Cortex-M55 objects,
  lint/format/editor/doc gates pass. DESIGN.md §2 and REVIEW.md §58 record the
  finite-test limits. This exhausts the host-only state-history approval, not
  broader Task 13: no ToF/tensor packing, ordering/freshness/safety policy,
  linked firmware/board execution, episode/log/data generation or application,
  inference/training, dependency/download, licence or accepted-default change.

- Approved (2026-10-19): host-only C decision-math primitives and complete
  synthetic verification: stable softmax/sigmoid for existing question sizes,
  shared unchanged Jev confidence, Python parity/failure tests, host/sanitizer/
  Arm checks, documentation and local commits. No heads/model, calibration,
  thresholds/smoothing/rejection policy, ToF/tensors, linked firmware/board,
  data/labels/training, dependencies or interface freeze. Core normalization is
  in `firmware/micro_classifier_math.c`; public guarded confidence reuses the
  codec's exact existing arithmetic. Forty-five math checks and four extra
  compile/unsafe-math checks pass: 169 C checks, 231 interface and 836 repository
  tests plus the known transformer expected failure; lint/format and host/
  Cortex-M55 objects pass. Seeded parity/native math sanitizers remain approved
  follow-up work. DESIGN.md §6 and REVIEW.md §59 record the core and limits.

- Approved decision-math package completed (2026-10-19): 1,000 synthetic
  question outputs across 250 fault-status packets match Python normalization,
  shared confidence, exact encoded frames, native round trips and both stream
  decoders. Shift/permutation fixtures pass. Native ASan/UBSan checks exact
  input/output allocations, capacities, nonfinite inputs, unsupported counts,
  all metadata byte values, nulls and unchanged rejected outputs. All 173 C
  checks, 235 interface tests and 840 repository tests pass plus the known
  transformer expected failure; host/Cortex-M55 objects, unsafe-math guards,
  lint/format/editor/doc gates pass. DESIGN.md §6 and REVIEW.md §60 record the
  finite-check limits. This exhausts the numeric reference approval, not Task
  13's broader firmware/runtime scope. No model/heads, calibration, thresholds,
  smoothing/rejection policy, data/labels/training, dependencies/downloads,
  linked firmware/board, evidence-policy or accepted-default change occurred.

- Approved (2026-10-19): complete host-only synthetic C head-reference and
  reproducible verifier package, including artificial weights/features, numeric/
  confidence/wire integration tests, invalid/overflow/atomicity checks, native
  sanitizers, host/Arm builds, evidence report, documentation and local commits.
  No trained model, production blob format, architecture/input changes, ToF/
  tensor packing, timing/rejection/safety policy, real logs/labels/task data,
  training, dependencies/downloads or linked board firmware/hardware. Core in
  `firmware/micro_classifier_heads.c` uses row-major binary32 weights and
  compensated double accumulation, bounds of 256 features/five rows and atomic
  output. These are reference limits, not an adopted student architecture.
  Shared ABI/build bindings moved from tests into `interface/native_verify.py`.
  All 233 C checks, 295 interface tests and 900 repository tests pass plus the
  known transformer expected failure; lint/format and host/Cortex-M55 objects
  pass. Standalone verifier/report and head-specific native sanitizers remain
  approved work. DESIGN.md §6 and REVIEW.md §61 record the core and boundaries.

- Approved synthetic-head/verifier package completed (2026-10-19): CPU-only CLI
  `interface/native_verify.py` ran 1,024 artificial cases, 4,096 question outputs,
  14,336 logits, 15,360 probabilities and 2,048 frames. All 1,024 input/logit/frame
  digests and 225,280 wire bytes were independently reconstructed in Python;
  source/compiler/library/result hashes match. Report:
  `interface/reports/native-heads-20261019.json`. Maximum checked logit/confidence
  errors were zero; probability error 2.9798811e-8 versus double reference, not
  model-quality evidence. Reproduced nested cancellation was repaired with a
  fixed partial-sum expansion; 128 shuffled multi-scale variants and native
  ASan/UBSan pass. Scratch is 257 doubles plus five floats, not measured stack/
  SRAM fit. All 61 head cases, 18 verifier cases and four extra build cases pass:
  238 C checks, 318 interface tests and 923 repository passes plus known
  transformer expected failure; lint/format, host/Cortex-M55 objects, unsafe-math,
  editor/doc/evidence gates pass. DESIGN.md §6 and REVIEW.md §62 record limits.
  This exhausts the approved artificial package, not broader Task 13. No trained/
  production heads, task data/labels/splits, simulator/log use, model runtime/
  training, dependencies, linked firmware/board, accepted inputs/defaults or
  safety-policy change occurred.

- Approved (2026-10-19): complete offline host/Arm build-audit package for the
  four existing C reference modules at `-O0/-O2/-Os`, synthetic host parity,
  object sections/dependencies, compiler-reported per-function stack, raw logs,
  hashes, strict outputs, tests, a bounded run/independent audit, docs and local
  commits. No target link/execution, new budgets, architecture/input/policy,
  production heads, logs/data/labels, inference/training, dependencies/downloads,
  ST/licence or board work. Core in `interface/build_audit.py` builds 24 objects
  and three synthetic host libraries; all three agree in the eight-case test.
  Forty-two audit and seven build-helper checks pass; all 367 interface tests,
  972 repository tests plus known transformer expected failure, lint/format,
  editor diagnostics and existing native sanitizers pass. Full 1,024-case per-
  optimization run and independent evidence audit remain approved follow-up.
  DESIGN.md §6 and REVIEW.md §63 record core scope, not board-fit evidence.

- Approved build-audit package completed (2026-10-19): all 24 host/Arm objects
  and three 1,024-case host verifications passed at `-O0/-O2/-Os`. Each host run
  exactly matches the prior independently audited 1,024-case evidence, not three
  independent cohorts. All 153 artifacts, source/tool hashes, object ELF section/
  symbol tables, stack records and command logs independently checked. Report:
  `interface/reports/reference-build-audit-20261019.json`. Arm summed `.text`:
  7,234/4,636/3,850 bytes; dense-head compiler stack: 2,176/2,192/2,200 bytes.
  These are unlinked objects/individual stack frames, not full runtime/call-chain
  bounds or memory-fit evidence; software-double/libm/memory helpers remain
  unresolved per object. All `.data/.bss` are zero, not zero RAM: caller buffers,
  state/history, stack and runtime are excluded. Last code gate: 972 passes plus
  known transformer expected failure, 367 interface checks; lint/format/editor,
  native sanitizer and doc/evidence gates pass. No C/wire/golden or historical
  report change. DESIGN.md §6 and REVIEW.md §64 record completion and limits.
  Approval exhausted; production/data/runtime/ST/board and all other gates stay.

- Native process-cleanup repair (2026-10-19): a real synthetic timeout regression
  reproduced a live compiler-style descendant after its parent was killed.
  Shared POSIX `interface/native_verify.py` command execution now starts an
  isolated session, kills the group on timeout/interruption/communication errors,
  drains output and reaps the direct command. Compiler identity, host builds and
  audit object tools share it; interrupted audit builds retain diagnostics and
  cannot write success. Seven new cases include timeout, interruption and an
  exited leader with a pipe-holding child, plus normal/nonzero command semantics.
  All 374 interface tests and 979 repository tests pass plus known transformer
  expected failure; lint/format and existing native sanitizer gates pass.
  Historical reports/artifacts and C/wire/input/default/policy stay unchanged;
  their recorded source hashes describe the original exporters, not this repair.
  DESIGN.md §6 and REVIEW.md §65 record limits. No new study, model/data/training,
  dependency/download, ST/licence, linked firmware or hardware scope is opened.

- Approved (2026-10-19): complete host-only synthetic four-head C assembly,
  tests/sanitizers, host/Arm checks, reproducible evidence, docs and local commits.
  `firmware/micro_classifier_assembly.c` composes existing affine, normalization,
  confidence and wire validation without changing them. Caller status/selections
  remain explicit; full four-answer metadata is validated before head access,
  and failure leaves output unchanged. No production model/blob, ToF/tensors,
  architecture/input or freshness/rejection/safety policy, real logs/task data,
  collection, training, dependencies, ST/licence, linked target or board work.
  All 102 assembly cases, six verifier checks, optimization/CLI and native
  ASan/UBSan checks pass; 490 interface and 1,095 repository passes plus known
  transformer expected failure, lint/format/editor diagnostics and host/Arm
  objects pass. Default verifier evidence remains the primitive path; assembly
  is separately opt-in. Current build audit includes five modules/30 objects;
  historical 24-object reports remain unchanged. Full 1,024-case assembly run
  and independent evidence audit remain approved work. DESIGN.md §6 and
  REVIEW.md §66 record the core checkpoint, not broader Task 13 completion.

- Approved assembly package completed (2026-10-19): opt-in CPU CLI verified
  1,024 artificial decisions, 4,096 question outputs, 14,336 logits, 15,360
  probabilities and 2,048 frames. Every input/logit/frame row and all 225,280
  wire bytes were independently reconstructed without native/verifier calls;
  all 13 source identities, compiler/library/result hashes and historical report
  hashes match. All six statuses and 2,840 nonargmax caller selections survive.
  Report: `interface/reports/native-assembly-20261019.json`; raw build ignored
  under `.runs/native-assembly-20261019/`. Checked logit/confidence errors zero,
  probability error 2.9798811e-8 versus double; fixtures reuse prior artificial
  head inputs, not independent task cohorts or quality evidence. Last code gate
  remains 1,095 passes plus known transformer expected failure, 490 interface
  tests; no code changed after the run. DESIGN.md §6 and REVIEW.md §67 record
  completion and finite-test limits. Approval exhausted; no production models/
  blobs, tensor/trunk/ToF adapter, policy, task labels/data/splits, collection,
  training, dependencies, ST/licence, target link/execution or board work.
  All broader gates, inputs/defaults/token ceiling and quarantine stay unchanged.

- Approved (2026-10-19): complete host-only assembly build-audit package:
  opt-in assembly verification at `-O0/-O2/-Os`, all five modules' host/Arm
  object sections/dependencies/per-function stack, 1,024 synthetic cases per
  optimization, independent fresh-evidence audit, docs and local commits.
  `interface/build_audit.py --assembly-reference` now forwards the strict boolean
  opt-in and marks scope; default primitive evidence remains unchanged. Eleven
  new cases cover both real matrices/optimized-Python CLIs, failed verification,
  drift/mismatch and pre-tool implicit-opt-in rejection. All 57 audit checks,
  501 interface and 1,106 repository tests pass plus known transformer expected
  failure; lint/format/editor diagnostics and all ten resolved caller signatures
  pass. Full bounded run/audit remains approved follow-up. DESIGN.md §6 and
  REVIEW.md §68 record the core checkpoint. No C/model/input/policy change,
  target linking/execution, real logs/data/labels/collection/training,
  dependencies/downloads, ST/licence or board action is approved or performed.

- Approved assembly build-audit package completed (2026-10-19): 30 host/Arm
  objects and three opt-in 1,024-case host verifications pass at `-O0/-O2/-Os`.
  Every complete host evidence object matches the prior independently audited
  assembly baseline, not three independent cohorts. All 189 artifacts, 14
  source/eight tool identities, raw ELF sections/undefined symbols, stack rows
  and command logs independently checked. Report:
  `interface/reports/assembly-build-audit-20261019.json`. Arm summed `.text` is
  7,876/4,896/4,078 bytes; assembly's own reported stack is 376/352/344 bytes
  (`static`), excluding callees/runtime. Host assembly is 480/464/432 bytes with
  `dynamic,bounded` qualifiers, not all-static or full-stack evidence. All
  object `.data/.bss` are zero, not zero RAM or memory fit. Last code gate:
  1,106 passes plus known transformer expected failure, 501 interface tests;
  lint/format/editor/signature/native sanitizer gates pass. DESIGN.md §6 and
  REVIEW.md §69 record completion and limits. Approval exhausted; no source
  changed after run, historical reports unchanged, and no target link/execution,
  budgets, policy/input, production models, task labels/data/collection/training,
  dependencies/downloads, ST/licence or board scope is opened.

- Whole-repository code, design and process review (2026-10-19, REVIEW.md §70):
  findings F18-F36 with proposed defaults; review only, nothing approved or
  changed in code, reports or defaults. Top items: no rover v0 question needs
  learning or the teacher (F18); undefined `mode` blocks every `OK` (F19);
  simulated ToF and proxies do not match the VL53L8CX, whose 8x8 mode is limited
  to 15 Hz (F21); Arm checks used the soft-float ABI (F22); framing can drop
  frames after line noise (F23); most recent work is off the critical path and
  this file has become an append-only log (F33-F34). Next: the user decisions
  and actions in §70.7, then the sequence in §70.8.

- User-approved independent fixes (2026-10-19, REVIEW.md §71): F22-F25/F30
  repaired; 1,178 tests pass plus the known transformer expected failure.
  Idle recovery now uses Python/C stream flush before discarding fragments;
  hard-float Arm checks, native sanitizers, lint/format and diagnostics pass.
  Wire bytes and historical reports remain unchanged. Product decisions, data,
  policy, ST and board gates remain deferred; no task is newly unblocked.

## Task List

Work top to bottom. When a task meets its exit condition, mark it `[x]` and add
a one-line result. Mark a task `[blocked: reason]` while it waits on the user or
on missing tools, and continue with the next unblocked task.

Current checkpoint: [DESIGN.md][design] §7 / [REVIEW.md][review] §92 complete the
approved private recorder in `76aa712`: 16 cases / three reused scenes / zero
decision queries; 1,957 passes plus known xfail. It seals producer-owned fixture
events, not physical/dynamics evidence or observation-only runtime admission.
The next candidate, not approved, is tests-only conditional recorder/audit/question
composition: four reused scenes / 16 cases / at most six motions per call, no new
geometry/rollouts/persistence/runtime code. No collection, input/profile adoption
or integration follows automatically. Task 6/9, physical/numerical/task-quality
evidence, teacher assets and ST/board remain blocked. No background job or cleanup.

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
6. [blocked: qualified floor-aware rules/evidence and representative scene envelope pending]
  Rover question catalogue v0 as data (types, options, and label source per
   question) and deterministic labelers for the computable questions.
  Current result (2026-10-20, REVIEW.md §72): active rules catalogue 1 excludes
  mode; the complete three-answer Python/C contract passes 123 new tests. Legacy
  diagnostic catalogue/proxies remain unchanged and unqualified, not deployed
  rules. Privileged simulation truth is permitted in principle, but no labels,
  collection or data acceptance occurred. Next: specify and correct F21 before
  implementing/qualifying the actual rules baseline; mode no longer blocks this
  pilot. The older entries below are historical, not renewed approval requests.
  Follow-up (REVIEW.md §73): nominal 15 Hz capture/variable delivered ages now
  replace per-decision sampling; legacy stored configs retain original behavior.
  Follow-up (REVIEW.md §74): user approved fictional geometry and opt-in ego
  errors/delay for implementation/tests only; floor/cylinder returns, missing
  masks and age-aware state export pass 63 new cases (1,382 total). No dataset,
  physical qualification or revised proxy rules; actual rules remain pending.
  Follow-up (REVIEW.md §75): separate floor-aware heuristic/wire loop and the
  approved eight diagnostics completed (4 success/2 collision/2 timeout; 25
  false-clear reference comparisons). Not qualified runtime rules or labels;
  reviewed evidence/scene requirements still block completion. No more collection.
  Follow-up (2026-10-21, REVIEW.md §76): approved opt-in registration/tests and
  frozen-log diagnostics are complete. High rejection and four false-clears
  remain; the default/report are unchanged and no new trajectory was collected.
  Follow-up (REVIEW.md §77): ideal full-input aliases now cover normal-sized
  cylinders and turning sweeps. User selected coverage-first design; requirements
  are recorded, but no sensing/input redesign or collection is authorized yet.
  Follow-up (REVIEW.md §78): concrete C1 ring/retention candidate and read-only
  geometry/resource checks are documented. It separates normal aliases but keeps
  a slender-cylinder alias; prototype/representation approval remains pending.
  Follow-up (REVIEW.md §79): separately approved synthetic C1 prototype complete
  in `a3df1f5`, 61 new cases, with unchanged normal inputs/defaults/wire. Still no
  qualified clearance or adopted object envelope; further work needs that review.
  Follow-up (REVIEW.md §80): user approved the controlled synthetic envelope;
  `d1ad3a2` adds conditional continuous-center exclusion with 43 new cases. Not
  certified, measured, integrated or task-qualified; old aliases remain intact.
  Qualification (REVIEW.md §§81-83): masked aliases stay unknown and
  ideal geometric occlusion/prefix checks pass. `562e3d2` adds opt-in zero-turn
  capsule exclusion, including straight-clear rear-obstacle fixtures; the
  default disk remains unchanged. No physical return process, curved maneuver,
  complete question bundle or runtime integration is qualified.
  Latest qualification (REVIEW.md §84): `65fecf0` adds explicit curved tubes for
  separate reaction/braking turns, with centre/left/right reference comparisons
  and 160 new cases. Default disk/straight results match exactly in 36 checks.
  Unknown blocked/masked/wall/budget outcomes remain; physical evidence, numerical
  certification, representative task quality and integration are still blocked.
  Prerequisite checks (REVIEW.md §85): eight one-segment counterexamples
  pass in `cc7f961`/`afd0f0f`, with no runtime or bound change. A concrete
  positive-witness/question-feasibility proposal was prepared, not then approved.
  Latest scope/result (REVIEW.md §§86-87): the approved package is complete;
  Stage A `d82fca3` adds 37 cases and Stage B `5c643f7` adds 30. The full gate
  passes 1,845 tests plus the known xfail. Candidate question feasibility is
  conditional synthetic evidence, not runtime/data approval or task completion.
  Next proposal (REVIEW.md §88): a latest-batch/relative-frame input boundary
  and qualification sequence are prepared, not adopted. Its separate bounded
  synthetic compatibility implementation was subsequently approved and completed
  in `cfb76f3` (§89), within 13 reused scenes / 30 pairs. All 64 new checks and
  1,909 repository tests plus known xfail pass; this does not qualify the input
  sources, live wire, runtime rules, physical bounds or representative task quality.
  Source plan (REVIEW.md §90): the approved design-only simulation-first plan is
  prepared. Exact payload/event binding and private truth separation are proposed;
  its bounded audit helper/tests were subsequently approved and completed in
  `04492d7` / `d483d14` (§91), with 32 cases and no audit coordinator queries.
  This verifies declared records, not source authority, physical inputs or
  complete task rules.
  Source recorder (REVIEW.md §92): separately approved `76aa712` adds owned
  fixture events, source-file identities and a retained binding. All 16 cases
  pass without decision queries; three scenes are reused. Not physical source
  qualification, dynamics evidence or runtime integration. Composition is proposed,
  not approved; the prior audit and recorder scopes are exhausted.
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
  Decision-preparation result (2026-10-16): DESIGN.md §7 and REVIEW.md §27
  propose proxy-vs-task targets, mode observability/reviewer abstention and
  grouped five-purpose evaluation. No definitions, labels or splits adopted.
  Review-preparation result (2026-10-16): 32 blind blank packets and fake-review
  format tests now available (REVIEW.md §32). Still no accepted target policy,
  actual annotations or reviewed cohort; mode stays unlabeled, rules diagnostic.
  Policy update (2026-10-16, REVIEW.md §34): observation-only review and current-log
  diagnostic quarantine are adopted. Navigation targets remain unaccepted; define
  path/horizon/footprint, sector decision meaning, tier meaning and observable
  mode semantics before annotation. No proxy-task target or training approval.
  Concrete-draft result (2026-10-16, REVIEW.md §35): candidate maneuver-based
  definitions and ten synthetic checks complete, not target acceptance. Complete
  input aliases with different geometric outcomes expose an observability gate;
  keep abstention, existing rules diagnostic-only and mode unlabeled. Review
  geometry/evidence assumptions and at-rest direction semantics before adoption.
  Synthetic-reference result (2026-10-16, REVIEW.md §36): user adopted the first
  three geometric meanings for simulation only; isolated artificial-geometry
  oracle and 25 new checks complete. Existing proxies remain diagnostic-only;
  sparse real-input evidence is unqualified, mode unlabeled, no annotation or
  dataset approval. Task 6 is not complete merely because a geometry oracle exists.
  Evidence-study result (2026-10-16, REVIEW.md §39): synthetic exact current-frame
  rays can give a positive straight-sweep witness; absence of one is unknown.
  The prototype rejects normal noisy/delayed assumptions and does not label logs
  or qualify real input. Reviewed uncertainty/registration and actual target
  evidence/labels remain missing; mode stays unlabeled.
  Bounded-error draft (2026-10-16, REVIEW.md §40): assumed artificial range/pose
  bounds can preserve or remove positive witnesses; they are not measured error
  limits, real-input qualification or negative/clear evidence. No current log
  was processed and no uncertainty policy or label/data approval was adopted.
  Evidence-plan result (2026-10-16, REVIEW.md §41): documentation-only proposed
  measurement/registration/qualification stages are complete. Claim/domain,
  references, collection approval and numeric uncertainty/failure conventions
  remain undecided; no measurements, model/adapter implementation, policy or
  real-input qualification occurred. Existing abstention/quarantine stay in force.
  Registration-reference result (2026-10-16, REVIEW.md §42): isolated artificial
  static-point frame arithmetic and 36 cases pass; supplied exact poses/times
  are assumptions, not physical evidence. No observation/log adapter or witness
  integration, uncertainty-policy adoption or real-data qualification occurred.
  Registration-error result (2026-10-16, REVIEW.md §44): separate artificial
  point/pose error propagation and 30 cases pass, including 864 perturbations.
  The algebraic enclosure neither measures uncertainty nor qualifies clocks,
  registration or real inputs; exact APIs and all witness rejection stay intact.
  Registered-witness study (2026-10-16, REVIEW.md §45): complete artificial
  registration-to-positive containment checks, including 41 cases and 2,592
  perturbed-world checks. No task label, default-input qualification, physical
  uncertainty policy or observation/log adapter; negative/clear evidence remains
  unsupported. This does not clear the reviewed evidence/data gate.
  Sensor-diagnostic result (2026-10-19, REVIEW.md §46): four bounded normal-config
  prefixes and privileged shared-model capture references audited, including one
  collision and three censored horizons. These quarantined software diagnostics
  are neither physical uncertainty/registration qualification nor target labels;
  mode and actual reviewed evidence/data remain blocked.
  Protocol proposal (2026-10-19, REVIEW.md §48): explicit per-question evidence
  admission/abstention and a proposed eight-episode readiness pilot are documented,
  not adopted or executed. Next question: what simulation-only claim/domain and
  evidence/uncertainty conventions are acceptable? Proposed default is to keep
  strict abstention and all current boundaries until that review; no collection,
  task labels or training are approved by the documentation-only scope.
  Readiness-only follow-up (2026-10-19, REVIEW.md §49): user separately approved
  the complete eight-episode/32-blank-projection package; run/audit complete.
  All data remain quarantined, uncertainty/registration/spatial-coverage evidence
  unqualified and mode unlabeled. No task annotations, labels or training. The
  next substantive decision remains an admissible simulation-only target-evidence
  claim/domain, not more unapproved collection or automatic oracle labels.
  Coverage proposal (2026-10-19, REVIEW.md §50): simultaneous Gaussian range
  coverage and selection pitfalls are documented/tested only. No claim unit,
  failure budget or uncertainty policy was adopted; registration/membership/
  motion/space evidence still blocks labels, and mode remains absent.
  Explicit follow-up (2026-10-19, REVIEW.md §51): user kept the risk convention
  unaccepted and strict abstention in force; no additional implementation or
  application is approved by the general request to continue autonomously.
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
  Cost-study follow-up: existing full/literal/typed forms profiled on the same
  80 states; no sampled full-history request fits. Numeric payload dominates
  the isolated diagnostics, which are not additive or removal estimates.
  REVIEW.md §28 documents the decision options; live use remains blocked.
  Resource-only follow-up (2026-10-16): capped mini INT8 parity and three full-
  input context probes are complete (DESIGN.md §4, REVIEW.md §§29–30). Selected
  warm inputs run under experimental ceilings, not the normal 2,048 limit.
  Answers were discarded; mode and real labeling remain unapproved. No normal
  budget, input-strategy or teacher-quality gate is cleared by resource fit.
  Longer-context parity follow-up (2026-10-16): approved bounded comparison
  completed, with the same warm-clear input flipping at two ceilings; maximum
  delta 0.0206704. REVIEW.md §31 records the numerical limitation, not labeling
  clearance. Decision needed: reviewed targets/data and input/teacher strategy;
  proposed default remains BF16/2,048 with no mode labels. No pipeline promotion.
9. [blocked: no reviewed task dataset or locked splits] Baselines (rules and a classical model) and the evaluation suite
   (macro-F1, per-class recall, NLL, Brier score, calibration error, and
   coverage curves) on locked splits.
  Current diagnostic result (2026-10-20, REVIEW.md §75): an observation-only
  heuristic now closes the wire loop on eight quarantined simulation episodes,
  with collisions/timeouts and geometric disagreements. This is not a locked
  evaluation cohort, task-quality clearance, classical-model fit or calibration.
  Approved (2026-10-16): CPU-only metric and split-validation
  tooling with synthetic fixtures only; no real labeling, training, dataset
  generation, metric-threshold changes or claim of locked task splits.
  Partial result (2026-10-16): synthetic metric arithmetic, five-purpose declared
  leakage/hash checks and exclusive built-in smoke report implemented; 36 focused
  tests, 260 repository passes plus the known expected failure. No baseline was
  fitted, task dataset generated or real split locked. DESIGN.md §7, REVIEW.md §22.
  Review-preparation follow-up (2026-10-16): provenance-bound blank packets and
  fake-only validators complete; all family-group reviews and split assignments
  remain pending. Decide targets, allowed reviewer evidence and cohort policy
  before annotation or locked evaluation; no baseline fit or training approval.
  Policy update (2026-10-16, REVIEW.md §34): reviewer evidence and diagnostic-log
  quarantine are adopted; source/template families must be reviewed before task
  cohort/split acceptance. Actual family reviews, targets, reviewed task data and
  all split assignments remain pending. No cohort or split was locked.
  Provenance-audit result (2026-10-16, REVIEW.md §37): 16 current diagnostic logs
  now have independently checked identity/declared-geometry evidence, including
  repeated geometry across differently hashed files. No family was accepted or
  cohort/split assigned; body validity and task truth are not established.
  Protocol proposal (2026-10-19, REVIEW.md §48): the proposed readiness pilot has
  at most four scene-parent candidates, insufficient for five distinct family-
  separated purposes and possibly fewer after lineage review. Family/cohort/
  split acceptance and actual reviewed task data remain pending; no assignments.
  Readiness result (2026-10-19, REVIEW.md §49): 32 blank projections include one
  exact reset-input group shared across all eight fresh episodes. With all these
  windows retained, the adopted duplicate-input rule prevents distributing the
  episodes across five purposes; no split, family or task cohort was accepted.
10. [blocked: training outside current tooling scope; dataset pending]
  Student: a small convolutional or MLP trunk over the state history and
    the ToF grid with per-question heads; supervised versus distilled
    comparison (M3).
11. [blocked: no trained student] Closed-loop evaluation in the simulator and one DAgger round.
12. [blocked: no trained student] Static ONNX export, INT8 QDQ PTQ, float versus INT8 parity, calibration
    on the deployed path, and golden vectors for the firmware (M4, host side).
13. [blocked: only host-side C reference tooling approved; firmware runtime out of scope]
  Firmware library in C for the Cortex-M55 without the ST HAL: packet
    parsing, history buffer, heads, softmax, confidence, and rejection; host
    unit tests against the golden vectors and an `arm-none-eabi-gcc` build.
  Tooling result (2026-10-19): approved portable host-only C parsing/CRC and
  bounded callback stream recovery are complete. All 67 C checks pass, including
  golden vectors, sanitizer/differential tests and real Cortex-M55 object
  compilation (REVIEW.md §§53-54). History, heads, inference/rejection policy,
  linked firmware and board integration remain outside this approval; the
  contract stays provisional and the full task remains blocked.
  Encoding result (2026-10-19): separately approved host C encoders and their
  sanitizer/bidirectional checks are complete (REVIEW.md §§55-56). Thirty-seven
  additional cases; all 104 C checks, 166 interface tests and real Cortex-M55
  object compilation pass. No broader firmware, input/policy or hardware
  authorization is implied; the full task stays blocked.
  State-history result (2026-10-19): separately approved eight-tick host-only
  reference complete with explicit gaps, masks and exact copied states. Fourteen
  history checks plus two additional host/Arm compile cases pass; 1,024 seeded
  Python-queue operations and native ASan/UBSan checks pass (REVIEW.md §§57-58).
  All 120 C checks and 182 interface tests pass. No ToF/tensor, ordering/freshness,
  inference or linked-board runtime is authorized; broader Task 13 stays blocked.
  Decision-math result (2026-10-19): separately approved softmax/sigmoid and
  shared confidence reference complete; 49 math checks plus four new build
  cases pass, including 1,000 seeded synthetic outputs/250 wire packets and
  native ASan/UBSan boundaries (REVIEW.md §§59-60). All 173 C checks, 235
  interface tests and host/Cortex-M55 objects pass. No model, calibration,
  safety/rejection policy or linked runtime gate is opened.
  Synthetic-head result (2026-10-19): separately approved artificial affine
  reference/verifier complete, including repaired nested cancellation, native
  sanitizers and independently audited 1,024-case/4,096-question CLI report
  (REVIEW.md §§61-62). There are 61 head and 18 verifier cases plus four new
  build checks; 238 C checks, 318 interface tests and 923 repository passes plus
  known expected failure. Production heads, training, input/runtime/policy and
  board gates stay blocked; diagnostic bounds do not freeze architecture.
  Build-audit result (2026-10-19): separately approved host/Arm inspection and
  optimization parity package complete (REVIEW.md §§63-64): 24 objects, three
  identical 1,024-case host results and all 153 artifacts independently audited.
  Forty-nine new checks; 972 repository passes plus known expected failure. No
  target link, full stack bound, memory-fit clearance or new resource budget;
  broader firmware/runtime/data/ST/board gates remain blocked.
  Maintenance (2026-10-19): reproduced/fixed native compiler descendant survival
  on timeout; shared POSIX process-group cleanup and seven regressions pass,
  979 repository passes plus known expected failure (REVIEW.md §65). No historical
  report regeneration or broader firmware/data/hardware gate change.
  Assembly result (2026-10-19): separately approved host-only four-head composition
  and opt-in verifier complete (REVIEW.md §§66-67), with explicit caller status/
  selections and atomic rejection. All 490 interface and 1,095 repository tests
  pass plus known expected failure. Native sanitizers, host/Arm and optimization
  checks pass; the 1,024-case report and all 225,280 wire bytes were independently
  audited. This exhausts the approved synthetic package. No production/runtime,
  task-data, input/policy or hardware gate is opened.
  Assembly audit result (2026-10-19): separately approved opt-in assembly mode
  and full bounded audit complete (REVIEW.md §§68-69). Eleven new cases; 1,106
  full suite passes plus known expected failure, 501 interface checks. All 30
  objects, three 1,024-case results and 189 artifacts independently audited;
  host assembly retains bounded-dynamic qualifiers. Approval exhausted;
  no resource budget, target link/runtime, data/policy or hardware gate changed.
  Maintenance (2026-10-19, REVIEW.md §71): idle frame recovery, numeric validation
  and explicit hard-float Arm checks repaired; broader runtime remains blocked.
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

The autonomous workflow above does not waive these approval boundaries. Ask
first, batching related decisions and proposing a default, for:

- Product decisions: requirements, M0 items, metric thresholds, safety
  behaviour, and changes to accepted decisions in DESIGN.md or to a frozen
  interface contract. Draft alternatives and acceptance checks first when that
  preparation is already within scope; do not silently adopt the proposal.
- New study episodes, task labels/imports, dataset/cohort/split acceptance,
  teacher labeling, training, outcome-driven tuning, or uncertainty/risk-policy
  adoption not covered by a current explicit authorization. Exhausted bounded
  run approvals stay exhausted; synthetic unit fixtures are not task data.
- Running third-party model code at a revision the user has not approved; new
  model experiments beyond the exact approved runtime/resource/run scope; new
  or upgraded dependencies; changes to `.devcontainer`.
- Downloads other than approved model revisions, and any download that would
  leave less than about 20 GB of free disk space.
- Deleting files or data you did not create, pushing or rewriting git history,
  and anything involving accounts, licences, payments, or contacting people.
- Hardware access/integration or privileged/host-level changes outside the
  agreed scope. Do not alter clocks, networking, TLS/security or privilege
  settings as a testing workaround.

Prepare authorized prerequisites before asking. Explain the precise action,
expected evidence, resource budget and cleanup plan where relevant; never ask
for passwords, tokens or other secrets. Do not re-ask settled decisions without
new evidence or a new claim/domain. After three failed approaches to the same
problem, record what was tried and the blocker, then move to other approved work.

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
- Documentation: follow the audience split above. Accepted design/contract
  changes belong in DESIGN.md; changing measurements, decisions under discussion
  and handovers in dated REVIEW.md updates. Do not rewrite review history.
- Put Python code in the existing top-level packages by area (`interface/`,
  `sim/`, `teacher/`, `export/`, or an approved new area), C code in `firmware/`,
  and generated data in ignored directories. Reuse local conventions/helpers.

## Commands

- Tests: `python -m pytest -q`. Tests must run without downloads or a GPU; skip
  GPU-only checks when CUDA is unavailable.
- Lint and format: `ruff check .` and `ruff format --check <changed files>`.
  There is no project Ruff configuration, and `.devcontainer/smoke.py` is not
  yet formatted; leave it unless asked.
- Container checks: `python .devcontainer/smoke.py` (add `--network` for TLS).
- INT8 Vela validation:
  `python -m teacher.validate_vela_int8 --output teacher/reports/<name>.json`.
  This is an opt-in model run, not part of the default gate or automatic approval
  to repeat a historical experiment. Check current authorization first.
- Environment: Python 3.12 virtual environment at `/opt/venv` with PyTorch and
  Transformers (Qwen3.5 support built in).

## Leave a Clear Handoff

- At meaningful checkpoints, add a dated [REVIEW.md][review] update with the
  actual change, commands/results, failed-check history, evidence limits,
  artifact retention/cleanup and next concrete action. Update accepted design
  decisions in [DESIGN.md][design] and the concise Current State/Task List here.
- Keep raw logs for long-running authorized jobs in ignored directories. Run
  large-memory/GPU jobs serially, one GPU job at a time, and report measured
  resource use without presenting process counters as hardware guarantees.
- When done or genuinely blocked, report the outcome, commit IDs, verification,
  remaining boundaries and worktree state. Do not end an otherwise unblocked
  implementation task merely by proposing its next routine step, and do not
  continue into the next implementation slice after a stop or pause request.

[design]: DESIGN.md
[review]: REVIEW.md
[readme]: README.md
[container-guide]: .devcontainer/README.md
