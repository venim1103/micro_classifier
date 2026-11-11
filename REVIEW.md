# Research Review: Jev-like Classifier on STM32N6

Status: Independent review of [DESIGN.md](DESIGN.md) and the repository state.
Review date: 2026-10-13. Update 2 (2026-10-14, §12) covers the robot
decision-module clarification and an external AI analysis; it corrects F1, F2,
and §7.2 in place. Update 3 (2026-10-19, §70) is a whole-repository code,
design and process review. Section 71 records the subsequent independent code
repairs; product decisions remain deferred.
Scope: feasibility, verification of design claims, landscape changes, design
gaps, alternatives, risks, and concrete next steps.

Method:

- Read DESIGN.md, README.md, and the `.devcontainer` setup.
- Re-checked hardware and compiler claims against ST Edge AI Core 4.0.1
  documentation, ST product pages, and ST example projects.
- Re-checked teacher claims against Hugging Face model cards, usage documents,
  configurations, and the published custom model source.
- Established what "Jev" is from TypeSafe's documentation, API reference, and
  customer agreement.
- Surveyed recent open "Jev-style" models, tiny-NLP research, and published
  STM32N6 measurements.
- Ran local arithmetic and an ONNX export/INT8 QDQ check inside the devcontainer.
- After the review, with your approval, implemented and measured an INT8 Vela
  2.0 9B teacher loader on the devcontainer's 12 GB GPU (F2).

Not done, and why:

- No NPU compilation: ST Edge AI Core is not installed (`/opt/st-tools` is empty).
- No board measurement: no hardware attached.
- Teachers other than the INT8 Vela 2.0 9B were not executed: Vela and Decision
  models require `trust_remote_code`, i.e. running third-party Python, which
  needs code review and your approval per release.
- The PDF (Idea0.pdf) is not in the workspace, so PDF-derived statements in the
  design could not be rechecked against their source.

Estimates in this document are labelled as estimates. Everything else is cited.


## Reading Map

Historical wording and evidence limits are preserved in topic chapters.
Read the relevant chapter and newest checkpoint, not the entire archive.

- [Checkpoints 1-41][chapter-review-00]
- [Checkpoints 42-78][chapter-review-01]
- [Checkpoints 79-102][chapter-review-02]
- [Checkpoints 103-122][chapter-review-03]
- [Checkpoints 123-146][chapter-review-04]
- [Checkpoints 147-170][chapter-review-05]
- [Checkpoints 171-180][chapter-review-06]
- [Checkpoints 181-182][chapter-review-07]
- [Checkpoints 183-220][chapter-review-08]
- [Checkpoints 221-225][chapter-review-09]
- [Checkpoints 226-230][chapter-review-10]
- [Checkpoints 231-235][chapter-review-11]
- [Checkpoints 236-240][chapter-review-12]
- [Checkpoints 241-245][chapter-review-13]
- [Checkpoints 246-250][chapter-review-14]
- [Checkpoints 251-255][chapter-review-15]
- [Checkpoints 256-260][chapter-review-16]
- [Checkpoints 261-265][chapter-review-17]
- [Checkpoints 266-270][chapter-review-18]
- [Checkpoints 271-275][chapter-review-19]
- [Checkpoints 276-280][chapter-review-20]

Checkpoints 281 onward and the source bibliography remain below.
## Recovery and Document Layout (2026-11-09)

Following the user's reported crash, the live review was a 262,527-byte exact
prefix of checkpoint `c226192`; the test file preserved a 7,223-byte local
selection-retention insertion followed by a truncated checkpoint prefix. The
source edit was complete. Preserved all five live context/source files under
`.git/recovery-20261109-PmbQpU/`, then mechanically appended only verified missing
checkpoint tails. The local source and test edits remain uncommitted; syntax
compilation passed. No interrupted experiment result or full gate is inferred.

Current read-only observations: 16 GiB available memory, no swap in use; the
current container reports zero OOM/OOM-kill events and a peak of 5,403,422,720
bytes. These counters do not cover a previous container or establish the crash
cause. Workspace storage is 21 MiB, the user cache 65 MiB, Git 132 MiB; disk has
328 GiB free. No cache, setting, security control or user file was deleted.

Lossless reorganization: the former 13,046-line design is a 111-line reading map
plus 16 topic chapters; the former 18,389-line review is a short recent-checkpoint
view plus nine numbered archives. Every original section and bibliography
definition is retained. Relative links are rebased, historical heading aliases
preserved, and pre-existing conflicting reference definitions retain Markdown's
first-definition behavior. This reduces routine context reads; it is not proof
that document size caused OOM or that crashes are fixed.

Validation: the first local-only migration dry run rejected a pre-existing
conflicting reference label without changing project documents. After preserving
all definitions, the dry run and written-layout check passed: 30 Markdown files,
no new broken local target/anchor; one existing unresolved target is unchanged.
Section allocation conservation and whitespace checks passed. No code suite was
rerun for this documentation change. Recovery snapshots, complete pre-migration
documents and the migration/check utility remain in the local recovery directory.

After the split, editor reads still showed pre-migration review text while
terminal reads showed the written layout. Validation therefore uses the on-disk
files; a stale editor buffer must not overwrite the recovered layout. This
discrepancy is recorded without claiming it explains the original interruption.

Next: verify the interrupted selection-retention increment with its original
finite fixture limits, counting the interruption rather than assuming success.
All qualification/admission flags remain false. Future checkpoints belong here
briefly, with whole older sections moved through the reading map rather than
repeated historical handoffs.

## 281. Matched Retained Cylinder Top-Offset Residuals (2026-11-11)

Resumed clean/synchronized `08b7559`; selected editor/terminal interpreter
`/opt/venv/bin/python`, terminal Python3.12.3. Prior top-offset patch rejection
and interrupted outcome were verified clean before the user's pause; no retained
281 test log or successful source/test execution inferred. Historical spent and
unknown attempts remain unchanged. Fresh routine checks below use standing authority.

Hypothesis: default-off literal `include_cylinder_top_offset_residuals` requiring
`include_cylinder=True` composes captured mount height/top/scalar cap numerator
through the unchanged supplied-word difference helper. Matched delivered/pending
identities and independent closing checks remain, no corrected upstream values.
Cheapest discriminator: existing23-case snapshot family expanded to ninth mode,
207 cases, exact top-minus-height oracle with scalar observation handling.

Fresh bounded routine ledger: <=3 pytest invocations, focused then required root
plus one diagnosed-repair reserve,300 s each. Root `python -m pytest -q && ruff
check . && git diff --check`, changed Python format check. Fixture <=4steps/5reads/
3geometries/3retentions/6active-helper+cylinder matches/2pending matches/64digests.
New mode <=9696 values/11202 binary operations/12 oracle operations; prior eight
caps unchanged. Combined control adds previous eight arithmetic helpers and chain
<=6each. No snapshot intake/read/retain/step/reset/replay/clock; tick/frame/RNG
preserved. Existing helper <=32 cylinders/65 words/32 entries/65 values/64 binary
operations,4096-bit ceiling unchanged; <=18 original/closing invocations across
delivered/<=8 pending records. Explicit21-bit observed scalar numerator in16-bit
work-limit control. Preserve failures/unknown attempts; diagnose before rerun,
no protected experiment or old refund. No additional C/Arm/sanitizer/board opt-ins,
dependencies, models or task data.

Focused207 passed/3260 deselected,32.22 s. Required root4390 passed,1 known
transformer QDQ xfailed,71 warnings,156.50 s; root Ruff, changed-file format and
whitespace passed. Editor/Pylance syntax clean; AST confirms only snapshot and
existing arithmetic family changed, previous defaults/23 cases conserved. Pylance
signature query found no call sites, not compatibility proof. Two of three pytest
positions used, no failure/abort; unused reserve is not follow-on authority.
Logs `cylinder-281-focused-1.log`/`cylinder-281-root-1.log` retained under recovery
directory; no additional C/Arm/sanitizer/board opt-in gates ran.

Exact scalar difference, nonzero/unknown residual, default skipped work, detached
output, matched delivered/pending identity, closing suppression and forced bit
exhaustion verified. Prior eight caps unchanged. All eight flags false; no uniform/
numerical/physical/source/geometry/coverage/clock/one-use/permission/admission or
usable command. Next whole271-275 archive then matched guarded top division.

## 282. Matched Retained Cylinder Top-Division Residuals (2026-11-11)

Whole271-275 archive moved verbatim (228 lines), root769 lines, four chapter05
references rebased; exact prior sections/bibliography and six local targets passed,
whitespace passed. One guarded migration/check,30 s cap, no failure/abort; originals/
script/log retained under recovery directory. Code suite not rerun for docs-only
archive; do not repeat successful migration or renew historical evidence authority.

Hypothesis: default-off literal `include_cylinder_top_division_residuals` requiring
`include_cylinder=True` composes captured up-ray/scalar cap numerator/distance
words through the unchanged guarded helper. Matched delivered/pending identities
and independent closing checks remain, no corrected upstream values. Zero up
requires observed +inf/no quotient, including signed zero. Cheapest discriminator:
existing23-case snapshot family in ten modes,230 cases, exact numerator/up oracle.
New copy control supplies negative-zero up and +inf distance at one retained ray;
matching branch words do not establish geometry or ray qualification.

Fresh bounded routine ledger: <=3 pytest invocations, focused then required root
plus one diagnosed-repair reserve,300 s each. Root `python -m pytest -q && ruff
check . && git diff --check`, changed Python format check. Fixture <=4steps/5reads/
3geometries/3retentions/6active-helper+cylinder matches/2pending matches/64digests.
New mode <=10470 values/11970 binary operations/768 oracle operations; prior nine
caps unchanged. Combined control adds previous nine arithmetic helpers and chain
<=6each. No snapshot intake/read/retain/step/reset/replay/clock; tick/frame/RNG
preserved. Existing helper <=32 cylinders/2272 words/2048 entries/2144 values/4096
binary operations,4096-bit ceiling unchanged; <=18 original/closing invocations
across delivered/<=8 pending records. Explicit21-bit observed distance in16-bit
work-limit control. Preserve failures/unknown attempts; diagnose before rerun,
no protected experiment or old refund. No additional C/Arm/sanitizer/board opt-ins,
dependencies, models or task data.

First focused229 passed/1 failed/3260 deselected,36.82 s: copy fixture's ray
mutation disagreed with paired retained native rays, correctly rejected by the
unchanged strict history guard. Repair only synthetic fixture to align the native
and cylinder copies of that supplied ray word; retain guard, all flags false and
no geometric/source qualification. Same230 controls rerun using diagnosed-repair
reserve; then required root uses final original pytest position. First failure
log retained, no failure erased/refunded, no abort.

Implemented separate default-off literal option, original/closing delivered and
pending guarded reports, strict outgoing comparison before publication. Fixture
repair aligns paired supplied words only, does not qualify a ray/source/scene.
Repaired same230 focused passed,3260 deselected,45.68 s. Required root4413 passed,
one known transformer QDQ xfail,71 warnings,148.69 s. Ruff root lint, changed-file
format, whitespace/editor/Pylance syntax and AST scope/default/23-case conservation
passed; primitive helper/history guard and all other methods/functions unchanged.
Pylance signature query found no call sites, not compatibility proof. All three
pytest positions spent including first failure, no abort, no further repeat.
Logs `cylinder-282-focused-{1,2}.log`, `cylinder-282-root-1.log`, archive originals/
utility/log retained under `.git/recovery-20261109-PmbQpU`; no cleanup required.

All eight qualification/admission flags remain false; nonfinite observations
unknown, signed words preserved, matching +inf bypass is not a finite intersection.
No geometry/coverage/source/error/clock/one-use/permission or usable command; no
additional C/Arm/sanitizer/board opt-in gates ran. Next compose supplied cap-relative
words with explicit raw nonfinite-distance/+0 fallback, then independent cap-square
arithmetic. Preserve matched identities, closing checks and unresolved word ties.

## 283. Matched Retained Cylinder Top-Relative Residuals (2026-11-11)

Hypothesis: default-off literal `include_cylinder_top_relative_residuals` requiring
`include_cylinder=True` composes captured offset/horizontal-ray/raw cap distance/
relative words through the unchanged combined-expression helper. Matched delivered/
pending identities and independent closing probes retain raw nonfinite-distance
word and explicit effective +0 fallback, not a corrected upstream quotient.
Cheapest discriminator: existing23-case family in eleven modes,253 controls,
independent exact supplied-word two-axis oracle; copy supplies +inf distance and
corresponding offset relative words, no ray/source/geometry qualification.

Fresh bounded routine ledger: <=3 pytest invocations, focused then required root
plus one diagnosed-repair reserve,300 s each. Root `python -m pytest -q && ruff
check . && git diff --check`, changed Python format check. Fixture <=4steps/5reads/
3geometries/3retentions/6active-helper+cylinder matches/2pending matches/64digests.
New mode <=12402 values/14274 binary operations/2304 oracle operations; prior ten
caps unchanged. Combined control includes previous ten arithmetic helpers and
selection chain <=6each. Existing helper <=32 cylinders/6400 words/4096 entries/
6336 values/12288 binary operations,4096-bit ceiling unchanged; <=18 original/
closing invocations across delivered/<=8 pending records. Explicit21-bit observed
relative in16-bit work-limit control. No snapshot intake/read/retain/step/reset/
replay/clock; tick/frame/both RNGs preserved. Preserve failures/unknown attempts,
diagnose before rerun, no old refund/protected experiment or additional C/Arm/
sanitizer/board opt-ins. No dependency/model/task-data/hardware changes. All eight
flags false; no isolated primitive/FMA, uniform error/geometry/coverage/source/
clock/one-use/permission/admission or usable command.

Implemented separate default-off literal option, delivered/pending reports and
independent closing computations with strict outgoing checks before publication.
Focused253 passed,3260 deselected,40.15 s. Required root4436 passed,one known
transformer QDQ xfail,71 warnings,147.68 s; Ruff root lint, changed-file format,
whitespace/editor and AST scope/default/23-case/ten-mode-cap conservation passed.
Primitive helpers/history guards and all other methods/functions unchanged. Two
of three pytest positions spent, no failure/abort; unused reserve is not follow-on
authority. Logs `cylinder-283-focused-1.log`, `cylinder-283-root-1.log` retained
under `.git/recovery-20261109-PmbQpU`, no cleanup or successful-gate repeat required.
No additional C/Arm/sanitizer/board opt-in gates ran, no qualification/admission
flags changed. Next independent captured cap radial/radius-square expression
residuals with matched original/closing identities; preserve supplied operands,
nonfinite unknowns and unresolved equal-value/different-word minimum ties.

## 284. Matched Retained Cylinder Cap-Square Residuals (2026-11-11)

Hypothesis: default-off literal `include_cylinder_top_radial_residuals` requiring
`include_cylinder=True` composes captured relative/radius/radial-squared/radius-
squared words through the unchanged independent two-family helper. Delivered/
pending identities and independent closing probes compare both families before
publication; no corrected upstream words or mask decision. Cheapest discriminator:
existing23-case family in twelve modes,276 controls, independent exact square
oracles for both families; late delivered radial and pending radius mutations
must suppress publication. Copy supplies signed-zero relative/radial words only;
residual/nonfinite/malformed/work controls alter both observed square families.

Fresh bounded routine ledger: <=3 pytest invocations, focused then required root
plus one diagnosed-repair reserve,300 s each. Root `python -m pytest -q && ruff
check . && git diff --check`, changed Python format check. Fixture <=4steps/5reads/
3geometries/3retentions/6active-helper+cylinder matches/2pending matches/64digests.
New mode <=13566 values/15822 binary operations/1548 oracle operations; prior eleven
caps unchanged. Combined control includes previous eleven arithmetic helpers and
selection chain <=6each. Existing helper <=32 cylinders/6208 words/2048 radial+
32 radius entries/6208 values/8256 binary operations,4096-bit ceiling unchanged;
<=18 original/closing invocations across delivered/<=8 pending records. Finite
relative/radius operands; nonfinite observed squares retain unknown residuals.
Explicit21-bit observed squares in16-bit work-limit control. No snapshot intake/
read/retain/step/reset/replay/clock; tick/frame/both RNGs preserved. Preserve
failures/unknown attempts; diagnose before rerun, no old refund/protected experiment.
All eight flags false, no isolated radial primitive/FMA or uniform error/geometry/
coverage/source/clock/one-use/permission/admission or usable command. No dependency/
model/task-data/hardware changes or additional C/Arm/sanitizer/board opt-ins.

First focused259 passed/17 failed/3260 deselected,59.14 s: new probe/fixtures
misnamed retained `radial_squared_m2` as `radial_m2`, causing KeyError or malformed
new copy layout. Actual retained schema and existing selection probe confirmed
the correct key. Repair only five new accesses, no helper/schema/guard/cap changes.
Same276 controls rerun using diagnosed-repair reserve, then final original pytest
position for required root. First failure log retained, no refund/abort.

Repaired same276 focused passed,3260 deselected,47.42 s. Formatting/lint/editor
and AST scope/default/23-case/eleven-cap conservation passed; helpers/history
guards and all other methods/functions unchanged. First root4457 passed/2 failed,
one known transformer QDQ xfail,71 warnings,165.04 s: unchanged selection held
rejected delivery identity and missing-delivered rejected retention identity.
Both original guards remained; traceback test source displayed `???`. Actual
files complete/tails intact, diff scoped to intended work. Source/test mtimes
08:14:33 fall inside approximate root interval ending log mtime08:15:31 minus
reported165.04 s. This supports concurrent source-write interference, not proven
writer attribution or a waived guard. No source regression inferred away.

Original three pytest positions all spent, both failed logs retained, no abort.
Diagnosed fresh bounded routine revalidation under standing authority: <=2 pytest
invocations, unchanged two failed selection controls then one required root,
300 s each. No parallel tools/formatter/editor calls during either run; hash all
three source-identity files plus tests before/after each and reject changed hashes.
No new fixtures, old caps/guards/ceilings unchanged, no repeat after unchanged
failure or successful gate. Retain outputs in distinct revalidation logs; no old
refund or numerical/source/clock/permission/admission qualification.

Two failed selection controls revalidated2 passed,0.79 s; sole fresh root4459
passed,one known transformer QDQ xfail,71 warnings,150.31 s. All four source/test
hashes unchanged before/after each run; root Ruff lint, changed-file format and
whitespace passed. Original three plus fresh two positions all spent, no abort;
no additional retry. Guard failures retained, writer/cause not proven by later
pass. Logs `cylinder-284-focused-{1,2}.log`, `cylinder-284-root-1.log`,
`cylinder-284-selection-revalidation-1.log`, `cylinder-284-root-revalidation-1.log`
retained under `.git/recovery-20261109-PmbQpU`; no cleanup required.

Implemented matched default-off two-family report option with strict original/
closing delivered/pending comparison. All eight flags remain false, no usable
command or geometry/coverage/error/source/clock/one-use/permission/admission
claim; no additional C/Arm/sanitizer/board opt-in gates ran. Next reassess the
supported cross-path native-ToF acquisition/recorder/delivery prerequisites;
retain supplied operands, raw nonfinite unknowns and unresolved word ties.

## 285. Matched Native Wall-to-Cylinder Boundary Prerequisite (2026-11-11)

Local hypothesis: captured fourth-wall `minimum_after_m` words are copied as
cylinder `post_wall_ranges_m` at the native stage boundary. Existing combined
wall/cylinder delivered/pending snapshot control supplies the cheapest exact-word
discriminator, with no extra acquisitions or geometry. First small reversible
edit adds that assertion only; matching words are not geometry/error/coverage or
source/clock/one-use/permission/admission qualification.

Fresh bounded routine ledger: <=3 pytest invocations, first existing48-case wall/
cylinder snapshot family, then smallest necessary boundary integration controls
if supported, then required root,300 s each. Existing per-case <=4steps/5reads/
3retentions/3geometries/6matcher/2pending/4queue/2frame/64digests and existing
combined <=6timing/selection/direction-norm/other-wall/clock caps unchanged. No
new snapshot read/retain/step/reset/replay/clock or rational boundary work. Source-
sensitive pytest serial, no parallel edits/formatter/editor tools; source/test
hashes before/after. Preserve failures/aborts/old spent ledgers; a blocked boundary
does not authorize geometry/source/error/timing/admission claims or protected runs.
No new dependencies/models/task-data/hardware or C/Arm/sanitizer/board opt-in gates.

Initial48 focused controls passed,3488 deselected,11.23 s; source/test hashes
unchanged. First integration patch rejected signature context; verified no source
or new test edits landed, no pytest position spent. Corrected owning signature/
preflight contexts. Supported next edit adds default-off literal boundary report
requiring both traces, paired original/closing delivered/pending identities and
strict outgoing checks. Pure helper <=128 canonical range words<=32chars/64
equality comparisons/64 entries+64 count inspections, no rational work; <=18
original/closing calls across delivered/<=8 pending. Separate20-control matrix
reuses existing source fixture, <=4steps/5reads/3retentions/3geometries/6each
boundary/wall/cylinder matches/2pending/64digests, <=384 conservative boundary
and192 oracle comparisons. No new fixture/data/environment; default/literal/
dependency/missing/malformed, mismatches/signed zero, late reports/source/owner/
budget and detached output covered. Stable mismatches report correspondence only;
all eight flags false, minimum word ties remain unresolved.

First20 integration controls7 passed/13 failed,3536 deselected,21.20 s: closing
boundary probe was inserted after closing wall but before closing cylinder match,
raising UnboundLocalError. Nearby closing owner confirms order. Repair only probe
placement after both traces/all arithmetic closing reports, before closing queue
and final typed/source/outgoing checks. First failure retained, no guard/cap change.
Narrowly revised assistant-selected routine ledger: original last pytest position
reassigned to same20 repaired focus; one additional required-root position, total
<=4 invocations at300 s each, no new controls or protected-budget renewal. No
unchanged rerun after failure; root permitted only after repaired focus passes.

Repaired20 integration controls passed,3536 deselected,5.55 s. Required root4479
passed,known transformer QDQ xfail/71 warnings,175.15 s. Source/test hashes unchanged
across both checks; Ruff root lint/changed-file format/whitespace/editor and AST
prior-helper/method/default/48-case-decorator conservation passed. All four routine
positions spent including failure, no abort; no further repeat. Logs
`cylinder-285-boundary-focus-1.log`, `cylinder-285-integration-focus-{1,2}.log`,
`cylinder-285-root-1.log` retained under `.git/recovery-20261109-PmbQpU`.
All eight flags false, no geometry/error/coverage/source/clock/permission/admission
or usable command; no additional C/Arm/sanitizer/board opt-ins ran. Next examine
actual native ray-generation source prerequisites; squared-norm correspondence
alone is not ray geometry or a numerical allowance. No cleanup required.

## 286. Native Ray-Generation Source Prerequisite (2026-11-11)

Checkpoint48e95ad pushed/clean. Existing tof_directions computes linspace/grid,
three NumPy cosine/two sine evaluations, pitch/yaw libm pairs and combined
rotations. Hypothesis: cold empty-dictionary source can retain original results
without extra trig/geometry/clock/RNG work or changing default output words/order.
Pylance all11 existing callers compatible; selected interpreter /opt/venv/bin/python.
16 bounded synthetic controls plus existing direction/norm control; <=2 generator
calls/24 named array-trig-stack calls per case, preflight failures before those
calls. <=13 copied arrays/904 words plus9 finite-input/effective/trig scalar words
per cold source; no primitive-product or numerical/physical bound adoption.
<=3 routine pytest positions: first17 focused/60 s, one necessary repair/60 s,
required root/300 s. Count failures/aborts, retain rays-286-* logs, no old refund
or protected study/dependency/hardware work; all eight flags remain false.

Before further root growth, whole276-280 sections moved mechanically to archive,
five design references rebased. Exact prior section/Sources/design conservation
and whitespace passed, no code gate rerun for migration. Root743/archive257 lines.
Originals rays-286-{review,design}-before.md retained in existing recovery directory.

First17 controls passed,3555 deselected,0.39 s with stable source/test hashes.
Fixture review found raw_nonfinite hook targeted call7 but actual NumPy up sine
is call6 (12 named calls per generation); fixture-only repair uses index6 modulo12
and asserts actual NaNs in retained sine/rays. Add grid/sensor/pitch word oracles
from captured original calls, <=6 arrays/384 word comparisons per valid case,
without new generator/trig calls. Use sole reserved same17 focused position;
original pass retained, not nonfinite-coverage evidence. Producer unchanged.

Strengthened17 controls passed,3555 deselected,4.98 s; root4495 passed,known
transformer QDQ xfail/71 warnings,181.77 s. All four source/test hashes stable
across both; root Ruff lint/changed format/whitespace/editor passed. AST only
tof_directions plus one new16-case test changed; all other source/test nodes
conserved. Pylance all12 resolved callers compatible after change. All3 routine
positions spent, no failure/abort/refund. Log rays-286-focused-{1,2}.log and
rays-286-root-1.log retained in existing recovery directory; no cleanup required.
Archive body text conserved with single EOF newline; five moved design targets
and root map checked before checkpoint. All eight flags false; no trig accuracy,
geometry/coverage/error/source/clock/one-use/permission/admission or usable command.
No additional C/Arm/sanitizer/board opt-ins ran. Next pair cold direction source
with actual tof_ranges rays before fresh acquisition; no reconstructed trig.

## 287. Cold Native Ray-to-ToF Source Pairing (2026-11-11)

Checkpointc5ea09e pushed/clean. Hypothesis: same actual tof_ranges ray evaluation
can populate separate cold direction trace with generation, original native
context, floor and final pre-noise words, preserving default calls and all four
existing source schemas. Pylance all25 original callers compatible. Opt-in empty
distinct builtin direction_source requires mounted rays; no reconstructed trig.
17 synthetic cold controls, <=2 geometry/2 ray/2 one-cylinder root calls per case,
16 copied arrays/1224 words plus<=9 ray scalars and existing bounded native input
context; <=32 cylinders/64 rays unchanged, no clock/RNG/acquisition/recorder work.
<=3 routine pytest positions: first17/60 s, one necessary repair17/60 s, required
root/300 s; count failures/aborts, retain rays-287-* logs, no old refund/protected
study/dependency/hardware. All eight flags false; no geometry/trig-error/source/
coverage/clock/one-use/permission/admission or usable command. Fresh acquisition
and bounded intake/retention/delivery pairing still separate prerequisites.

First focused invocation failed collection,0.40 s: insertion patch accidentally
removed existing test_native_tof_direction_source header, leaving body intact.
Restore only that exact original header; no old fixture/body/source change.
Failure retained rays-287-focused-1.log; after-hash comparison not reached, no
stable-hash claim for that invocation. Use sole same17 repair position next,
then required root only after success; first collection failure remains spent.

Repaired-header invocation9 passed/8 failed,3572 deselected,11.59 s. Scenario.start
is (x,y,yaw), while existing native ToF guard requires position shape(2,); new
fixture supplied all three. Repair ONLY fixture start[:2] and assert invalid-case
rejection reasons so unmounted control cannot pass at the wrong guard. Both
failures retained; source guard unchanged, no stable-hash claim for failed runs.
Narrowly revised assistant-selected routine ledger: original last/root position
reassigned to same17 repaired focus/60 s; one additional required-root/300 s,
total4 positions. Original two remain spent; no unchanged failed rerun, protected
budget/cap renewal, new controls or relaxed work limits. Root after focus success.

Native-position-repaired invocation16 passed/1 failed,3572 deselected,8.14 s:
raw_nonfinite fixture incorrectly expected NaN final ranges. Actual retained
rays NaN make floor downward/hit predicates false; wall/cylinder candidates and
final ranges remain +inf through existing guarded selection. Nearby native wall
predicate/np.where owner confirms this. Repair ONLY expectation to require raw
NaN rays AND +inf floor/final words; all prior word parity assertions preserved,
no producer/mask/tolerance changes or finite-intersection claim. Third failure
retained, failed-run after-hash not reached. Narrow diagnosed routine revision:
existing fourth position becomes same17 repaired focus/60 s; sole additional
required-root/300 s is position5. All three prior positions remain spent; no
unchanged failed rerun, new cases/work-limit increase or protected renewal.

Fourth focused17 passed,3572 deselected,7.03 s, source/test hashes stable. Formatter
changed only touched Python files; focused Ruff failed PLC0206 in new fixture
native dictionary loop. Mechanical fixture-only .items()/value repair, no assertion
or source change. Chained AST/root had not run; same scoped lint/AST next, no
extra standalone pytest or spent-position refund. Style failure retained here.

Same scoped lint/changed format/AST/editor passed after style repair; all old
source/test nodes/defaults including restored old header conserved. Pylance
all26 resolved callers compatible. Required root4512 passed,known transformer
QDQ xfail/71 warnings,159.61 s; all four hashes stable, root lint/format/whitespace
passed. All5 pytest positions spent including three failures; no abort/refund.
Logs rays-287-focused-{1,2,3,4}.log and rays-287-root-1.log retained in existing
recovery directory, no cleanup required. All eight flags false; raw NaN ray/+inf
range correspondence is not finite geometry/trig-error/source/coverage/clock/
one-use/permission/admission. No extra C/Arm/sanitizer/board opt-ins. Next fresh
acquisition pairing through existing native cache; held output is not new source.

## 288. Fresh Native Ray-to-ToF Acquisition Pairing (2026-11-11)

Checkpointba2ae14 pushed/clean. Hypothesis: existing fresh native sensor phase can
retain cold direction trace alongside original cache without extra geometry,
noise/dropout/clock work. Separate literal step capture_native_tof_direction=False
requires native capture/mounted rays; private direction acquisition pairs
original native object/RNG references/nominal acquisition+delivery tick. Default,
held and reset clear; rejected preflight preserves. No source qualification.
Reuse old16-case acquisition matrix as wall/cylinder/direction families=48,
prior32 scenarios/caps conserved. <=3 geometries/1 selected trace/1 selection/
2 existing timed-clock reads per case, no new sampling or clock; unchanged32
cylinders/64 rays/16-array1224-word cold trace. <=3 routine pytest positions:
first48/60 s, one necessary repair48/60 s, required root/300 s, count failures/
aborts/unknowns; retain rays-288-* logs, no refunds/protected studies/dependencies/
hardware. All eight flags false, no geometry/error/source/clock/one-use/admission;
bounded intake/retention/delivery and numerical/physical evidence still separate.
First patch rejected reset context; worktree clean/no partial edits/no pytest
spent. Nearby reset pending-deque and actual if-capture-clock anchors corrected.

First48 controls passed,3557 deselected,0.77 s; root4528 passed,known transformer
QDQ xfail/71 warnings,158.45 s. All four source/test hashes stable across both;
root Ruff lint/changed format/whitespace/editor passed. AST only reset/update/
sample/step and existing acquisition matrix changed, all prior other nodes/defaults
and16-case decorator conserved. Sensor methods7 compatible callers each; step
38of40 compatible/same two intentional receipt=1 negatives159/299. Twoof3 pytest
positions used, no test failure/abort/refund; unused reserve not follow-on authority.
Logs rays-288-focused-1.log/root-1.log retained in existing recovery directory;
no cleanup. All eight flags false; no geometry/coverage/error/source/clock/one-use/
permission/admission or usable command. No additional C/Arm/sanitizer/board opt-ins.
Next bounded closed direction-source intake before recorder retention/delivery;
raw unsupported/nonfinite source stays unknown, no reconstructed trig.

## Sources

Hardware and tools:

- [STM32N657 product page][st-n657]
- [ST Neural-ART NPU concepts][st-concepts]
- [Neural-ART operators][st-operators] and [compiler][st-compiler]
- [Memory initializers][st-initializers] and [runtime-loadable models][st-reloc]
- [STM32N6 example projects][st-projects] and [quantization guide][st-quant]
- [STM32N6 image-classification getting started][st-gs-ic]

Jev and Jev-style models:

- TypeSafe [API][typesafe-api], [models][typesafe-models],
  [confidence][typesafe-confidence], [customer agreement][typesafe-mca]
- [Vela 2.0 overview][vela-blog]; Vela 0.3B [card][vela-03b],
  [usage][vela-03b-usage], [config][vela-03b-config], [code][vela-03b-code];
  [Vela 0.8B][vela-08b]; Vela 9B [usage][vela-9b-usage], [config][vela-9b-config],
  and [code][vela-9b-code]
- [Decision 3.0 collection][d3-collection], [d3][d3], [d3-flash][d3-flash],
  [d3-mini][d3-mini], [d3-nano][d3-nano], [d3-lite][d3-lite], [d3-edge][d3-edge],
  and the [Decision paper][decision-paper]
- [Crivo-150M][crivo-150m], [Crivo-32M][crivo-32m], [JEV-35B][jev-35b],
  [JEV-27B-VL][jev-27b-vl], [jev-distill-corpus-v3][jev-corpus],
  [Decision Index][decision-index], [Vela 9B evaluation][vela-9b-eval], and
  [Mistral Small 3.1][mistral-small]

Robot integration (Update 2):

- [PX4 offboard mode][px4-offboard], [PX4 Gazebo simulation][px4-gazebo],
  [DAgger][dagger], [Infineon PSoC Edge E84][psoc-edge-e84], and the
  [EASA drone framework][easa-drones]

Code, design and process review (Update 3):

- [VL53L8CX product page][vl53l8cx-page] and [ULD driver API][vl53l8cx-uld],
  [GCC Arm options][gcc-arm-options], [COBS][cobs], and
  [Learning by Cheating][lbc]

Methods and measurements:

- [EmbBERT][embbert], [pQRNN/PRADO][pqrnn], [Model2Vec][model2vec],
  [Tang et al.][tang]
- STM32N6 studies: [eye tracking][eye-tracking], [CubeSat][cubesat],
  [speech enhancement][speech], [line segments][nplsd], [ARGO][argo],
  [Gideon][gideon], [edge processor review][edge-review]
- Alternatives: [Arm Ethos-U85][ethos-u85], [Alif E4][alif-e4],
  [Alif E8][alif-e8], [NXP i.MX RT700][nxp-rt700]

[lbc]: https://arxiv.org/abs/1912.12294
[vl53l8cx-page]: https://www.st.com/en/imaging-and-photonics-solutions/vl53l8cx.html
[vl53l8cx-uld]: https://github.com/stm32duino/VL53L8CX/blob/main/src/vl53l8cx_api.h
[gcc-arm-options]: https://gcc.gnu.org/onlinedocs/gcc/ARM-Options.html
[cobs]: https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing
[st-n657]: https://www.st.com/en/microcontrollers-microprocessors/stm32n657a0.html
[st-concepts]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-programming-model.html
[st-operators]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-operators.html
[st-compiler]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-compiler.html
[st-initializers]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-memory-initializers.html
[st-reloc]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-reloc-mode.html
[st-projects]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-stm32n6-projects.html
[st-quant]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-quantization.html
[st-gs-ic]: https://github.com/STMicroelectronics/STM32N6-GettingStarted-ImageClassification
[typesafe-api]: https://docs.typesafe.ai/api
[typesafe-models]: https://docs.typesafe.ai/models
[typesafe-confidence]: https://docs.typesafe.ai/confidence
[typesafe-mca]: https://typesafe.ai/legal/mca
[vela-blog]: https://vllm-sr.ai/blog/vela-2-0-open-foundation-routing-models/
[vela-03b]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B
[vela-03b-usage]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/USAGE.md
[vela-03b-config]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/config.json
[vela-03b-code]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/modeling_vela2.py
[vela-08b]: https://huggingface.co/vllm-sr/Vela-2.0-0.8B
[vela-9b-usage]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/USAGE.md
[vela-9b-config]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/config.json
[vela-9b-code]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/modeling_vela2.py
[d3-collection]: https://huggingface.co/collections/vllm-sr/decision-30
[d3-edge]: https://huggingface.co/vllm-sr/d3-edge
[d3-flash]: https://huggingface.co/vllm-sr/d3-flash
[d3]: https://huggingface.co/vllm-sr/d3
[d3-mini]: https://huggingface.co/vllm-sr/d3-mini
[d3-nano]: https://huggingface.co/vllm-sr/d3-nano
[d3-lite]: https://huggingface.co/vllm-sr/d3-lite
[decision-paper]: https://vllm-sr.ai/decision-paper
[jev-27b-vl]: https://huggingface.co/autotrust/JEV-27B-VL
[jev-corpus]: https://huggingface.co/datasets/SargeDev/jev-distill-corpus-v3
[vela-9b-eval]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/EVALUATION.md
[mistral-small]: https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503
[px4-offboard]: https://docs.px4.io/main/en/flight_modes/offboard.html
[px4-gazebo]: https://docs.px4.io/main/en/sim_gazebo_gz/
[dagger]: https://arxiv.org/abs/1011.0686
[psoc-edge-e84]: https://www.infineon.com/products/microcontroller/32-bit-psoc-arm-cortex/32-bit-psoc-edge-arm/psoc-edge-e84
[easa-drones]: https://www.easa.europa.eu/en/the-agency/faqs/drones-uas
[jev-35b]: https://huggingface.co/autotrust/JEV-35B
[crivo-150m]: https://huggingface.co/tardellirs/crivo-150m
[crivo-32m]: https://huggingface.co/tardellirs/crivo-32m
[decision-index]: https://huggingface.co/spaces/multimodalart/jev-decision-index
[embbert]: https://arxiv.org/abs/2502.10001
[pqrnn]: https://research.google/blog/advancing-nlp-with-efficient-projection-based-model-architectures/
[model2vec]: https://github.com/MinishLab/model2vec
[tang]: https://arxiv.org/abs/1903.12136
[eye-tracking]: https://arxiv.org/abs/2508.13244
[cubesat]: https://arxiv.org/abs/2603.20174
[speech]: https://arxiv.org/abs/2609.29867
[nplsd]: https://arxiv.org/abs/2609.25022
[argo]: https://arxiv.org/abs/2607.16222
[gideon]: https://arxiv.org/abs/2605.04282
[edge-review]: https://arxiv.org/abs/2603.08725
[ethos-u85]: https://www.arm.com/products/silicon-ip-cpu/ethos/ethos-u85
[alif-e4]: https://alifsemi.com/ensemble-e4-series/
[alif-e8]: https://alifsemi.com/ensemble-e8-series/
[nxp-rt700]: https://www.nxp.com/products/i.MX-RT700
[chapter-review-00]: docs/review/001-041.md
[chapter-review-01]: docs/review/042-078.md
[chapter-review-02]: docs/review/079-102.md
[chapter-review-03]: docs/review/103-122.md
[chapter-review-04]: docs/review/123-146.md
[chapter-review-05]: docs/review/147-170.md
[chapter-review-06]: docs/review/171-180.md
[chapter-review-07]: docs/review/181-182.md
[chapter-review-08]: docs/review/183-220.md
[chapter-review-09]: docs/review/221-225.md
[chapter-review-10]: docs/review/226-230.md
[chapter-review-11]: docs/review/231-235.md

[wire-python]: interface/protocol.py
[wire-header]: firmware/include/micro_classifier_protocol.h
[wire-golden]: interface/golden_vectors.json
[m1a-script]: export/m1a.py
[m1a-report]: export/reports/m1a-cpu-20261015.json
[st-compile-script]: export/st_compile.py
[st-cli-401]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-cli.html
[sim-catalogue-draft]: sim/catalogue.json
[sim-label-draft]: sim/labels.py
[sim-label-smoke-report]: sim/reports/label-smoke-20261016.json
[teacher-label-pipeline]: teacher/label_pipeline.py
[teacher-pipeline-tests]: tests/test_label_pipeline.py
[teacher-evaluation]: teacher/evaluation.py
[synthetic-evaluation-report]: teacher/reports/evaluation-synthetic-20261016.json
[evaluation-tests]: tests/test_evaluation.py
[prompt-budget]: teacher/prompt_budget.py
[prompt-budget-flash]: teacher/reports/prompt-budget-d3-flash-20261016.json
[prompt-budget-mini]: teacher/reports/prompt-budget-d3-mini-20261016.json
[prompt-budget-tests]: tests/test_prompt_budget.py
[row-draft-flash]: teacher/reports/row-draft-budget-d3-flash-20261016.json
[row-draft-mini]: teacher/reports/row-draft-budget-d3-mini-20261016.json
[float32-draft-flash]: teacher/reports/float32-draft-budget-d3-flash-20261016.json
[float32-draft-mini]: teacher/reports/float32-draft-budget-d3-mini-20261016.json
[sim-label-coverage-report]: sim/reports/label-coverage-20261016.json
[input-cost-flash]: teacher/reports/input-cost-d3-flash-20261016.json
[input-cost-mini]: teacher/reports/input-cost-d3-mini-20261016.json
[mini-int8-parity]: teacher/reports/d3-mini-int8-parity-capped-20261016.json
[mini-context-resource]: teacher/reports/d3-mini-context-resource-capped-20261016.json
[mini-context-parity]: teacher/reports/d3-mini-context-parity-capped-20261016.json
[blind-review-tool]: teacher/review.py
[blind-review-report]: teacher/reports/review-preparation-20261016.json
[sensor-diagnostics]: sim/diagnostics.py
[sensor-diagnostics-report]: sim/reports/sensor-diagnostics-20261019.json
[readiness-tool]: teacher/readiness.py
[readiness-report]: teacher/reports/readiness-pilot-20261019.json
[wire-codec-api]: firmware/include/micro_classifier_codec.h
[wire-codec-source]: firmware/micro_classifier_codec.c
[state-history-api]: firmware/include/micro_classifier_history.h
[state-history-source]: firmware/micro_classifier_history.c
[decision-math-api]: firmware/include/micro_classifier_math.h
[decision-math-source]: firmware/micro_classifier_math.c
[head-reference-api]: firmware/include/micro_classifier_heads.h
[head-reference-source]: firmware/micro_classifier_heads.c
[native-verifier]: interface/native_verify.py
[native-head-report]: interface/reports/native-heads-20261019.json
[reference-build-audit]: interface/build_audit.py
[reference-build-audit-report]: interface/reports/reference-build-audit-20261019.json
[assembly-api]: firmware/include/micro_classifier_assembly.h
[assembly-source]: firmware/micro_classifier_assembly.c
[assembly-report]: interface/reports/native-assembly-20261019.json
[assembly-build-report]: interface/reports/assembly-build-audit-20261019.json
[review70-rover]: sim/rover.py
[review70-navigation]: sim/navigation.py
[review70-d3]: teacher/d3_int8.py
[lbc]: https://arxiv.org/abs/1912.12294
[vl53l8cx-page]: https://www.st.com/en/imaging-and-photonics-solutions/vl53l8cx.html
[vl53l8cx-uld]: https://github.com/stm32duino/VL53L8CX/blob/main/src/vl53l8cx_api.h
[gcc-arm-options]: https://gcc.gnu.org/onlinedocs/gcc/ARM-Options.html
[cobs]: https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing
[floor-rules]: sim/rules.py
[floor-rules-report]: sim/reports/rules-baseline-20261020.json
[primitive-integrator]: sim/rover.py
[primitive-owner]: sim/diagnostics.py
[primitive-cpython-float]: https://github.com/python/cpython/blob/v3.12.3/Objects/floatobject.c
[primitive-numpy-sinc]: https://github.com/numpy/numpy/blob/v2.2.6/numpy/lib/_function_base_impl.py
[primitive-cpython-math]: https://github.com/python/cpython/blob/v3.12.3/Modules/mathmodule.c
[primitive-python-math-doc]: https://docs.python.org/3.12/library/math.html
[primitive-numpy-sinc-doc]: https://numpy.org/doc/2.2/reference/generated/numpy.sinc.html
[primitive-numpy-asarray-doc]: https://numpy.org/doc/2.2/reference/generated/numpy.asarray.html
[primitive-numpy-promotion-doc]: https://numpy.org/doc/2.2/reference/arrays.promotion.html
[primitive-numpy-scalar]: https://github.com/numpy/numpy/blob/v2.2.6/numpy/_core/src/umath/scalarmath.c.src
[primitive-numpy-arithmetic]: https://github.com/numpy/numpy/blob/v2.2.6/numpy/_core/src/umath/loops_arithm_fp.dispatch.c.src
[primitive-numpy-trig]: https://github.com/numpy/numpy/blob/v2.2.6/numpy/_core/src/umath/loops_trigonometric.dispatch.cpp
[primitive-glibc-errors]: https://sourceware.org/glibc/manual/2.39/html_node/Errors-in-Math-Functions.html
[primitive-glibc-sincos]: https://github.com/bminor/glibc/blob/glibc-2.39/sysdeps/x86_64/fpu/multiarch/s_sin.c
[primitive-glibc-selector]: https://github.com/bminor/glibc/blob/glibc-2.39/sysdeps/x86_64/fpu/multiarch/ifunc-avx-fma4.h
[primitive-ubuntu-python]: https://launchpad.net/ubuntu/+source/python3.12/3.12.3-1ubuntu0.17
[primitive-ubuntu-glibc]: https://launchpad.net/ubuntu/+source/glibc/2.39-0ubuntu8.4
[primitive-protocol-design]: DESIGN.md
[cpython-correspondence-build]: https://launchpad.net/~ubuntu-security-proposed/+archive/ubuntu/ppa/+build/33562858
[cpython-correspondence-changes]: https://launchpadlibrarian.net/875581834/python3.12_3.12.3-1ubuntu0.17_amd64.changes
[cpython-correspondence-buildinfo]: https://launchpadlibrarian.net/875581836/python3.12_3.12.3-1ubuntu0.17_amd64.buildinfo
[cpython-correspondence-applied]: https://git.launchpad.net/ubuntu/+source/python3.12/commit/?id=f641d3123029c88838179c83a972bc2be28e6e60
[cpython-correspondence-series]: https://git.launchpad.net/ubuntu/+source/python3.12/plain/debian/patches/series?h=applied/3.12.3-1ubuntu0.17
[cpython-correspondence-float]: https://git.launchpad.net/ubuntu/+source/python3.12/tree/Objects/floatobject.c?id=f641d3123029c88838179c83a972bc2be28e6e60
[cpython-correspondence-math]: https://git.launchpad.net/ubuntu/+source/python3.12/tree/Modules/mathmodule.c?id=f641d3123029c88838179c83a972bc2be28e6e60
[cpython-correspondence-pymath]: https://git.launchpad.net/ubuntu/+source/python3.12/tree/Include/pymath.h?id=f641d3123029c88838179c83a972bc2be28e6e60
[cpython-correspondence-rules]: https://git.launchpad.net/ubuntu/+source/python3.12/plain/debian/rules?id=f641d3123029c88838179c83a972bc2be28e6e60
[cpython-static-cases]: https://git.launchpad.net/ubuntu/+source/python3.12/tree/Python/generated_cases.c.h?id=f641d3123029c88838179c83a972bc2be28e6e60
[controlled-arithmetic-design]: DESIGN.md
[arithmetic-prototype]: sim/diagnostics.py
[arithmetic-tests]: tests/test_sim.py
[arithmetic-dossier-design]: DESIGN.md
[arithmetic-trusted-design]: DESIGN.md
[arithmetic-paper-design]: DESIGN.md
[scalar-compatibility-tests]: tests/test_sim.py
[controlled-owner-contract-design]: DESIGN.md
[controlled-owner-prototype-design]: DESIGN.md
[controlled-candidate-audit-design]: DESIGN.md
[controlled-auditor-source]: sim/diagnostics.py
[controlled-auditor-tests]: tests/test_sim.py
[native-gap-plan-design]: DESIGN.md
[sinc-contract-design]: DESIGN.md
[sinc-prototype-design]: DESIGN.md
[sinc-correctness-design]: DESIGN.md
[sinc-bridge-design]: DESIGN.md
[sinc-path-design]: DESIGN.md
[sinc-route-design]: DESIGN.md
[sinc-cell-design]: DESIGN.md
[sinc-word-design]: DESIGN.md
[sinc-word-proof-design]: DESIGN.md
[sinc-certificate-plan-design]: DESIGN.md
[sinc-cell-check-design]: DESIGN.md
[sinc-checker-paper-design]: DESIGN.md
[sinc-bind-contract-design]: DESIGN.md
[sinc-bind-budget-design]: DESIGN.md
[sinc-bind-implementation-design]: DESIGN.md
[sinc-bind-paper-design]: DESIGN.md
[sinc-composition-design]: DESIGN.md
[sinc-composition-prototype-design]: DESIGN.md
[sinc-composition-paper-design]: DESIGN.md
[sinc-target-contract-design]: DESIGN.md
[sinc-target-prototype-design]: DESIGN.md
[sinc-target-paper-design]: DESIGN.md
[sinc-target-join-design]: DESIGN.md
[sinc-target-join-prototype-design]: DESIGN.md
[sinc-target-join-paper-design]: DESIGN.md
[sinc-join-worksheet-design]: DESIGN.md
[sinc-binding-identity-design]: DESIGN.md
[sinc-compile-comparison-design]: DESIGN.md
[sinc-structural-protocol-design]: DESIGN.md
[priority-reset-design]: DESIGN.md
[baseline-admission-design]: DESIGN.md
[c1-wire-rejection-source]: sim/diagnostics.py
[concurrent-architecture-review]: docs/review/147-170.md#149-standalone-review-removal-2026-11-05
[architecture-validation-source]: docs/review/147-170.md#149-standalone-review-removal-2026-11-05
[architecture-prompt-source]: teacher/label_pipeline.py
[architecture-rover-source]: sim/rover.py
[architecture-arm-build]: interface/build_audit.py
[architecture-head-source]: firmware/micro_classifier_heads.c
[architecture-head-tests]: tests/test_interface.py
[architecture-head-audit]: interface/reports/reference-build-audit-20261019.json
[architecture-row-budget]: teacher/reports/float32-draft-budget-d3-mini-20261016.json
[architecture-context-parity]: teacher/reports/d3-mini-context-parity-capped-20261016.json
[architecture-public-readme]: README.md
[architecture-validation-plan]: DESIGN.md
[architecture-sensor-spec]: https://www.st.com/en/imaging-and-photonics-solutions/vl53l8cx.html
[source-command-admission-design]: DESIGN.md
[admission-requirements-design]: DESIGN.md
[discrete-motion-source]: sim/diagnostics.py
[discrete-motion-tests]: tests/test_sim.py
[autonomy-workflow]: AGENTS.md
[path-cell-source]: sim/diagnostics.py
[path-cell-tests]: tests/test_sim.py
[path-source-implementation]: sim/diagnostics.py
[path-source-controls]: tests/test_sim.py
[state-motion-source]: sim/diagnostics.py
[state-motion-controls]: tests/test_sim.py
[history-registration-source]: sim/diagnostics.py
[history-registration-controls]: tests/test_sim.py
[registered-prefix-source]: sim/diagnostics.py
[registered-prefix-controls]: tests/test_sim.py
[path-point-error-source]: sim/diagnostics.py
[path-point-error-controls]: tests/test_sim.py
[command-path-source]: sim/diagnostics.py
[command-path-controls]: tests/test_sim.py
[continuation-workflow]: AGENTS.md#continuation-and-stopping
[admission-dependencies]: docs/design/07-data-and-distillation-design-01.md#admission-evidence-dependencies-2026-11-06
[python-monotonic-clock-doc]: https://docs.python.org/3.12/library/time.html#time.monotonic_ns
[st-n657]: https://www.st.com/en/microcontrollers-microprocessors/stm32n657a0.html
[st-concepts]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-programming-model.html
[st-operators]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-operators.html
[st-compiler]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-compiler.html
[st-initializers]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-memory-initializers.html
[st-reloc]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-reloc-mode.html
[st-projects]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-stm32n6-projects.html
[st-quant]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-quantization.html
[st-gs-ic]: https://github.com/STMicroelectronics/STM32N6-GettingStarted-ImageClassification
[typesafe-api]: https://docs.typesafe.ai/api
[typesafe-models]: https://docs.typesafe.ai/models
[typesafe-confidence]: https://docs.typesafe.ai/confidence
[typesafe-mca]: https://typesafe.ai/legal/mca
[vela-blog]: https://vllm-sr.ai/blog/vela-2-0-open-foundation-routing-models/
[vela-03b]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B
[vela-03b-usage]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/USAGE.md
[vela-03b-config]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/config.json
[vela-03b-code]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/modeling_vela2.py
[vela-08b]: https://huggingface.co/vllm-sr/Vela-2.0-0.8B
[vela-9b-usage]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/USAGE.md
[vela-9b-config]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/config.json
[vela-9b-code]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/modeling_vela2.py
[d3-collection]: https://huggingface.co/collections/vllm-sr/decision-30
[d3-edge]: https://huggingface.co/vllm-sr/d3-edge
[d3-flash]: https://huggingface.co/vllm-sr/d3-flash
[d3]: https://huggingface.co/vllm-sr/d3
[d3-mini]: https://huggingface.co/vllm-sr/d3-mini
[d3-nano]: https://huggingface.co/vllm-sr/d3-nano
[d3-lite]: https://huggingface.co/vllm-sr/d3-lite
[decision-paper]: https://vllm-sr.ai/decision-paper
[jev-27b-vl]: https://huggingface.co/autotrust/JEV-27B-VL
[jev-corpus]: https://huggingface.co/datasets/SargeDev/jev-distill-corpus-v3
[vela-9b-eval]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/EVALUATION.md
[mistral-small]: https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503
[px4-offboard]: https://docs.px4.io/main/en/flight_modes/offboard.html
[px4-gazebo]: https://docs.px4.io/main/en/sim_gazebo_gz/
[dagger]: https://arxiv.org/abs/1011.0686
[psoc-edge-e84]: https://www.infineon.com/products/microcontroller/32-bit-psoc-arm-cortex/32-bit-psoc-edge-arm/psoc-edge-e84
[easa-drones]: https://www.easa.europa.eu/en/the-agency/faqs/drones-uas
[jev-35b]: https://huggingface.co/autotrust/JEV-35B
[crivo-150m]: https://huggingface.co/tardellirs/crivo-150m
[crivo-32m]: https://huggingface.co/tardellirs/crivo-32m
[decision-index]: https://huggingface.co/spaces/multimodalart/jev-decision-index
[embbert]: https://arxiv.org/abs/2502.10001
[pqrnn]: https://research.google/blog/advancing-nlp-with-efficient-projection-based-model-architectures/
[model2vec]: https://github.com/MinishLab/model2vec
[tang]: https://arxiv.org/abs/1903.12136
[eye-tracking]: https://arxiv.org/abs/2508.13244
[cubesat]: https://arxiv.org/abs/2603.20174
[speech]: https://arxiv.org/abs/2609.29867
[nplsd]: https://arxiv.org/abs/2609.25022
[argo]: https://arxiv.org/abs/2607.16222
[gideon]: https://arxiv.org/abs/2605.04282
[edge-review]: https://arxiv.org/abs/2603.08725
[ethos-u85]: https://www.arm.com/products/silicon-ip-cpu/ethos/ethos-u85
[alif-e4]: https://alifsemi.com/ensemble-e4-series/
[alif-e8]: https://alifsemi.com/ensemble-e8-series/
[nxp-rt700]: https://www.nxp.com/products/i.MX-RT700
[chapter-review-12]: docs/review/236-240.md
[chapter-review-13]: docs/review/241-245.md
[chapter-review-14]: docs/review/246-250.md
[chapter-review-15]: docs/review/251-255.md
[chapter-review-16]: docs/review/256-260.md
[chapter-review-17]: docs/review/261-265.md
[chapter-review-18]: docs/review/266-270.md
[chapter-review-19]: docs/review/271-275.md
[chapter-review-20]: docs/review/276-280.md
