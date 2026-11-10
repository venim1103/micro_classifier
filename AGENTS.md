# Project Agent Workflow

These instructions apply to any AI assistant working in this repository.
Apply them within higher-priority platform, tool and safety requirements; do
not promise capabilities or indefinite turn lifetime that the environment lacks.

**Active continuation rule:** Once the user starts or resumes open-ended project
work, keep executing useful authorized work until the user explicitly stops,
pauses or ends that work. Checkpoints, summaries and commits are progress, not
completion. Apply the final-answer gate in Continuation and Stopping below.

**Standing authority:** Independently scope and complete reversible local
implementation, compatible design choices, bounded synthetic unit fixtures,
required tests, documentation, checkpoint commits and periodic normal upstream
pushes within the agreed plan. Choose recommended defaults and record rationale;
do not ask for routine planning/testing approval or a finish/continue vote.
This supersedes historical routine approval wording, not protected limits,
exhausted experiments or missing qualification evidence. Fresh bounded local
source-recovery and unit/regression checks are delegated even when historical
routine test accounting is missing; preserve unknown attempts, not approval gates.

## Project

micro_classifier builds a Jev-like **robot decision module**: an STM32N6 board
(N657: Cortex-M55 with the Neural-ART NPU) that attaches to a host robot, first
a ground rover and later a mini-drone. On every tick it answers a fixed
catalogue of typed questions (`choice`, `noul`, `score`) with probability
distributions. The active rover pilot is rules-first; a small INT8 student and
distillation from open teachers remain longer-term work, not current capability.
The host's own controller keeps actuation, inner loops, interlocks, and fail-safes.

## Current Work

Read [REVIEW.md][review] §266 for fallback-aware cap relative expressions; §264
records the lossless 251-255 archive and §255 the design-topic relocation. §§231-265
retain wall correspondence and the complete
cold cylinder/acquisition trace with their arithmetic/ownership limits.
§§226-228 preserve earlier interrupted/unknown
attempts and autonomous routine-recovery authority; those attempts are not refunded.
Next implement independent supplied-word cap radial-squared and radius-squared
expressions before cap hit-mask/candidate/minimum and matched-source composition.
Preserve unresolved equal-value/different-word
ties; matching words do not prove geometry, coverage or error.
§§181-191 record workflow, clocks and source ownership. The Q0-Q5
source/named-consumer qualification packet (§180) is prepared, not adopted.
All qualification/admission flags remain false; no usable command is admitted.

Continue this ordered queue, deriving smaller compatible prerequisites when a
release gate is blocked:

1. Retain bounded native ToF acquisition, recorder and delivery correspondence
  as source prerequisites, without adopting numerical or physical bounds. Nominal
  ticks or observed timing do not qualify clocks, one-use execution or permission.
2. Advance independently supported setup/source/coverage/error/timing evidence
  for the named consumers; implement compatible offline prerequisites without
  inventing bounds, accepting claims or starting protected studies.
3. Compose supported request/guard/executor dependencies only as their evidence
  permits. No actuation or admitted predecessor chain follows from matching hashes.

ST licence/tools and board readiness remain user-side blockers; learned work,
D4 task-quality runs and general audits/SC18 remain deferred. Detailed milestones,
failed checks, approvals and spent ledgers belong in [DESIGN.md][design] §12 and
dated [REVIEW.md][review] sections, not here. Replace this short state as it changes.

## Start With Context

- Read Current Work and the newest relevant checkpoint in [REVIEW.md][review]
  before continuing implementation. The root review and [DESIGN.md][design]
  are reading maps; follow chapter links for the relevant numbered scope.
  Use design §§1, 2 and 12 for active scope and gates; consult §4 for teacher
  work, §6 for numerical/architecture work and the relevant §7 subsection for
  sensor, coverage and data work. Do not load entire archives for routine work.
- Check the actual worktree, nearby implementation/tests and applicable local
  instructions. Preserve user changes, including editor settings and untracked
  files. After an interrupted tool call, verify its outcome before repeating it.
- Verify selected environments, cached files, pinned revisions, available tools
  and resource budgets rather than assuming they survived a restart. Reuse
  existing caches and environments; do not duplicate downloads or checkouts.
- Distinguish proposed, approved, implemented, tested, integrated and measured
  work. A historical approval or completed bounded run is not renewed permission.
  Apply the current standing authority to new routine local work; do not treat
  older per-checkpoint approval wording as a reason to ask again or stop.

## Documentation Audience

- [README.md][readme] is the public introduction: capabilities, maturity limits,
  documentation links and licensing. Do not add routine progress updates, test
  counts, commit histories or session handovers. This rule does not request a
  separate cleanup of existing documentation.
- Keep architecture, accepted requirements, contracts and rationale in
  the chapters indexed by [DESIGN.md][design]. Keep changing status,
  discussions, commands/results, failed-check history, evidence limits and
  next-session handovers in dated
  [REVIEW.md][review] updates. Older numbered checkpoints live in its linked
  archives. Preserve failures, approvals, spent ledgers and evidence limits;
  moving a record does not renew authority or qualify its claims.
- Keep root reading maps short; archive whole older sections before exceeding
  about 1,000 lines. Keep individual archive/topic files around 2,500 lines or
  less, rebase local links and preserve historical anchors. New checkpoint
  notes should state the change, actual checks/failures, limits and next action
  without repeating the full prior handoff. These are organization targets,
  not experiment budgets or product requirements.
- Use [.devcontainer/README.md][container-guide] for reusable environment/setup
  instructions. Use existing documents rather than creating new Markdown files
  unless asked. Use reference-style links and check their targets.
- Keep stable workflow rules here. Replace Current Work and task summaries as
  they change rather than appending more historical checkpoints to this file.

## Work Independently

- Do not invoke `vscode_askQuestions` or equivalent agent-controlled
  questionnaire/choice dialogs. Do not spawn subagents unless explicitly requested.
- Own planning and execution: choose the first useful unblocked task, record its
  finite scope/resource budget and exit condition, implement, verify, checkpoint,
  then start the next useful authorized action in the same turn. Missing routine
  planning/testing approval is not a blocker.
- Assistant-written proposals and test plans are not permission gates for work
  already delegated. Do not replace implementation with repeated documentation-
  only budget proposals, approval requests or checkpoint reports. Record the
  bounded routine plan and execute it within the same work slice.
- At material checkpoints or new evidence, reassess the plan and priority queue;
  update compatible choices independently. Apply delivered user corrections
  promptly. Reviews are not new permission gates or reasons for repeated audits.
- Form a falsifiable local hypothesis from the owning code and a nearby test.
  Make the smallest useful edit and immediately run a focused check before
  expanding scope. Reuse existing tests/helpers and avoid unrelated cleanup.
- For an isolated blocker, name the missing evidence, authority, tool or input,
  retain the conservative state, prepare useful prerequisites and continue other
  unblocked work. Diagnose tool failures and use supported alternatives.
- Give concise progress updates: what changed, what was verified and what
  remains. Do not manufacture work merely to keep a turn alive.

## Continuation and Stopping

- Treat an open-ended continuation as active across checkpoints, commits,
  pushes, progress reports, tool notifications, reloads and context compaction.
  Completing one task does not complete the session or require another continue.
- Do not end active work with a routine permission/finish vote. An assistant-
  imposed planning gate or missing routine test ledger is not an all-path blocker;
  use the recovery rules below and take the next useful authorized action.
- During open-ended work, process new user messages delivered by the platform
  before the next slice; apply the newest compatible instructions. Do not claim
  inbox polling or message checks with unavailable tools.
- Determine current user intent from actual user instructions, not an assistant
  recap, generated conversation summary, quoted transcript or historical stop.
  These are context, not new user commands. A recap describing an old pause or
  summary-only request cannot end a subsequently resumed continuation. If the
  latest actual request is unavailable, recover it from available session
  history before deciding to stop; do not invent a stop instruction.
- An explicit current stop, pause or finish request takes priority. Stop safely
  without confirmation; cancel or contain owned work, retain evidence and leave
  a concise handoff. Do not start another slice or delay for unrelated checks,
  commits/pushes or a finish vote. Quoted stop words or a request to stop
  interrupting are not requests to pause project work.
- Stop/finish instructions apply to the current work, not future continued
  sessions. A fresh continue or changed task requires evaluating the latest
  request; do not carry an old finish permission across checkpoints, later turns
  or context loss. After a pause, a status question or terminal notification is
  not permission to resume implementation.
- Respect explicit task boundaries. A standalone documentation-only request,
  review or proposal is not permission to start separate implementation or
  collect data. During an already active continuation, handle a side request
  within its scope, then resume the existing authorized queue unless the user
  explicitly pauses, replaces or limits that continuation. An explicit "only
  update documentation", "review only" or equivalent limit must be honored;
  standing authority never expands that limit or authorizes protected actions.
- Use commentary for checkpoint reports and side-request results during active
  continuation, then execute the next concrete action. Do not issue a checkpoint
  final answer, offer to continue or leave an authorized next step for another turn.
- Use event-based waiting only when a supported tool is actually waiting for
  authorized work or required input; follow its notification protocol. Do not
  use sleep loops, repeated polling, dummy jobs or invented work to keep a turn
  alive. Instructions alone cannot provide background message monitoring.
- If every useful in-scope path is genuinely blocked, or platform/tool limits
  prevent execution, report the exact constraint and pending action; do not
  pretend to remain active. Missing admission evidence, an exhausted experiment
  or an isolated blocker does not end compatible prerequisite work. Do not evade
  protected limits or invent work to avoid stopping.

**Final-answer gate.** Before ending a turn, verify one of these applies:

- The user explicitly stopped, paused or ended the active work.
- A standalone bounded request is complete, with no active continuation to resume,
  or the user explicitly replaced the continuation with that bounded request.
- Every useful authorized path is genuinely blocked after checking compatible
  prerequisites and the remaining agreed queue; identify the precise blockers.
- A higher-priority safety requirement or an actual platform/tool limit prevents
  further work; state the concrete constraint without claiming to remain active.

Otherwise, the next action must be useful authorized work, not a final answer.
A clean worktree, green gate, checkpoint, commit, push, recap or completed side
request is not a stopping reason. This is an instruction-level behavior rule,
not a guarantee of unlimited execution or background message monitoring.

## Verification and Commits

- Prefer bounded synthetic fixtures for routine arithmetic, codec and integration
  checks. Default tests need neither downloads nor a GPU; no implicit inference,
  task-data collection or training.
- Required focused/regression checks for meaningful source changes are delegated.
  Record finite fixture/query counts, attempt/resource caps and failure/cleanup
  plans before execution. Count failures/aborts; retain tolerances, hard work
  limits and per-family controls.
- If historical routine test accounting is missing, mark interrupted/unknown
  attempts as spent/unknown and start a fresh bounded revalidation ledger under
  standing authority. Run the necessary focused and root checks without another
  approval request; never infer a past pass, refund old attempts or treat a new
  ledger as qualification evidence. This does not reopen protected experiments
  or override an explicit user-imposed execution ceiling.
- Distinguish explicit user-imposed hard caps and protected experiment budgets
  from assistant-selected routine test plans. For the latter, diagnose a failure
  before any rerun and document a narrowly revised finite plan when a necessary
  repair or required verification needs it. Do not repeatedly reset budgets for
  unchanged failures, rerun unchanged successful gates, relax fixture/work/safety
  limits or manufacture a new scope to evade a protected cap.
- Old spent experiment ledgers remain historical and are not refunded. Existing
  fixtures may run as unchanged controls in the required regression gate for a
  new source change; this does not authorize standalone old experiments, extra
  study runs or deferred audits. A substantive repair permits another necessary
  check within the recorded scope. Increasing an explicit user-imposed hard cap
  or protected experiment budget still needs explicit authority.
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
  checks for green results. Diagnose before rerunning; substantive repairs permit
  necessary checks within scope. Preserve the known transformer QDQ xfail.
- Do not rerun an unchanged successful gate merely for reassurance. For
  documentation/instruction-only changes, validate scoped content, references,
  local targets and whitespace; state that the code suite was not rerun.
- Scoped checkpoint commits and periodic normal pushes are authorized. Commit
  meaningful verified increments. Review the diff and stage only checkpoint
  files; never include or discard unrelated user work.
- Keep the remote reasonably synchronized by pushing verified checkpoints
  periodically through the current branch's configured upstream, without an
  approval prompt. Check the worktree, branch and tracking state first. If the
  remote advanced, fetch and reconcile conservatively without discarding either
  history; validate affected work before a normal push. Do not force-push,
  silently change remotes or alter credentials/security settings to make it work.
- If synchronization is blocked, retain the local commits, record the precise
  cause/pending action and continue other useful work. Diagnose before retrying;
  do not invent credentials or repeatedly retry an unchanged failed push.
- Use Conventional Commit subjects (`type(scope): imperative summary`, with scope
  optional) and a real bullet body. Branch creation, force-pushes and history
  rewriting still need explicit direction. Never revert another person's changes.

## Protected Boundaries

**Protected boundaries.** Where fresh explicit authorization is absent, choose
not to take the protected action; record the reason and recommended next action
without an approval questionnaire, and continue other useful in-scope work:

- Changes to accepted product requirements, question meanings, metric or
  safety thresholds, frozen interface contracts or physical safety behavior.
  A compatible implementation choice is delegated; a new product/safety
  requirement is not silently adopted by choosing a convenient default.
- New study episodes, task labels/imports, dataset/cohort/split acceptance,
  teacher labeling, training, outcome-driven tuning, or uncertainty/risk-policy
  adoption not covered by a current explicit authorization. Exhausted protected
  run approvals stay exhausted; synthetic unit fixtures are not task data.
- Running third-party model code at a revision the user has not approved; new
  model experiments beyond the exact approved runtime/resource/run scope; new
  or upgraded dependencies; changes to `.devcontainer`.
- Downloads other than approved model revisions, and any download that would
  leave less than about 20 GB of free disk space.
- Deleting files or data you did not create, force-pushing/rewriting git history,
  creating branches/changing remotes, and external account setup, licences,
  payments or contacting people. Normal checkpoint pushes using the existing
  configured upstream are covered by the standing authority above.
- Hardware access/integration or privileged/host-level changes outside the
  agreed scope. Do not alter clocks, networking, TLS/security or privilege
  settings as a testing workaround.

Never convert autonomy into evidence: source qualification, numerical proof,
task quality and physical clearance still require their actual acceptance
evidence; hashes, passing fixtures and agent defaults are not substitutes.
Prepare authorized prerequisites and record the precise protected action,
expected evidence, resource budget and cleanup plan for a future user directive.
Never request passwords, tokens or other secrets. Do not reopen settled choices
without new evidence or a changed claim/domain. After three failed approaches
to the same problem, retain the failures, mark the blocker and switch to other
useful in-scope work rather than repeating the same attempt.

## Rules

- Evidence: cite primary sources and label estimates as estimates. Never present
  unmeasured fit, latency, or accuracy as fact. Scores from different Decision
  Index editions are not comparable.
- Third-party model code: pin/review the full revision and verify its manifest,
  selected environment and current exact run authority. Historical approvals do
  not renew runs. Record approvals/evidence in [REVIEW.md][review]; consult
  [DESIGN.md][design] §4 for teacher contracts and resource limits.
- Never use TypeSafe's hosted Jev outputs for training, labels or tuning,
  autotrust JEV models, or Crivo models for commercial work.
- Never use the GTX 1080 Ti (no BF16). Default RTX A3000 peak reserved GPU memory
  stays below about 11 GiB; normal 9B-class token budget is 2,048. Verify actual
  hardware before use and retain stricter experiment-specific caps. Serialize GPU jobs.
- Dependencies: without explicit authorization, keep the current environment
  and use installed tools. For an authorized dependency change, update
  `.devcontainer/requirements.in` and regenerate both hash locks with the commands in
  [.devcontainer/README.md](.devcontainer/README.md). Never disable TLS
  verification or `--require-hashes`.
- Keep weights, datasets, caches, and ST tools out of git; add ignore rules when
  creating such directories.
- On-device means on-device: never move inference to the host for a feature
  described as running on the module.
- Safety: the module only recommends. No design may let module output or
  silence stop a drone's motors in flight, and host fail-safes stay independent.
- Put Python code in the existing top-level packages by area (`interface/`,
  `sim/`, `teacher/`, `export/`, or an approved new area), C code in `firmware/`,
  and generated data in ignored directories. Reuse local conventions/helpers.
- Environment/setup: [.devcontainer/README.md][container-guide]. Verify selected
  tools/interpreters; the recorded default is Python 3.12 at `/opt/venv`, not an
  assumption that it survived a restart. Model, study and hardware commands are
  opt-in only under current protected authority; GPU-only tests skip without CUDA.

## Leave a Clear Handoff

- At meaningful checkpoints, add a dated [REVIEW.md][review] update with the
  actual change, commands/results, failed-check history, evidence limits,
  artifact retention/cleanup and next concrete action. Update accepted design
  decisions in [DESIGN.md][design] and the concise Current Work here.
- Keep raw logs for long-running authorized jobs in ignored directories. Run
  large-memory/GPU jobs serially, one GPU job at a time, and report measured
  resource use without presenting process counters as hardware guarantees.
- After a restart, verify file sizes/tails and live processes before repeating
  work. Preserve damaged and uncommitted versions before recovery; use bounded
  reads and summaries instead of whole-file diffs or historical log dumps.
  Never clear user/editor caches or attribute a crash to OOM without evidence.
- When the final-answer gate permits a handoff, include commit IDs, verification,
  remaining boundaries and worktree state. Never continue after a stop or pause.

[design]: DESIGN.md
[review]: REVIEW.md
[readme]: README.md
[container-guide]: .devcontainer/README.md
