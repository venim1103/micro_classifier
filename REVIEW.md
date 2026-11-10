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

Checkpoints 271 onward and the source bibliography remain below.
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

## 271. Matched Retained Cylinder Selection Reports (2026-11-10)

Checkpoint `12ac061` pushed/clean. Existing delivered/pending cylinder matcher
already preserves epoch/acquisition/delivery identities and typed original and
closing ownership/pair checks. Hypothesis: opt-in composition can report supported
side/cap mask-candidate/minimum and captured-chain diagnostics on those matched
words, with independent closing recomputation before publishing. Default-off
literal `include_cylinder_selection_diagnostics` requires `include_cylinder=True`.
No numerical residual composition or qualification/admission follows.

Finite routine plan: 28 synthetic integration controls, each <=4 steps/5 recorder
reads/3 geometries/3 retentions; <=6 calls each of five reports and cylinder matcher,
2 pending matches/64 binding digests, no runtime source intake/read/retain/step/
reset/replay/clock/rational calls. Setup bounds include held path, empty/one/two
cylinders; unchanged <=8 retained/<=8 pending/<=32 cylinders/64 rays/32-character
words. At API limits <=18 calls per report across original/closing delivered and
pending records, <=18496 entries per composed record; aggregate counts separate.
Fixtures verify default/dependency/held/delivered-only/detachment, independent
mask/candidate/minimum/chain faults and unresolved ties, missing/malformed records,
late report/pending/native/cylinder/owner/budget changes fail closed. Three pytest
positions including failures/aborts: first28/60 seconds, one necessary repair
reserve, final root/300 seconds; retain `cylinder-271-*` logs. No old refunds or
protected studies/task data/dependencies/hardware. All eight flags false, no
numerical/physical/source/geometry/coverage/clock/one-use/permission/admission or
usable command. Pylance caller query returned no sites, not compatibility proof;
existing keyword-only defaults and required root controls remain the check.

First integration invocation11 failed,17 passed,3232 deselected,12.90 s.
Closing comparator intentionally supports closed dict/tuple/scalar values, not
lists; standalone chain report uses lists. Diagnosed from owning comparator and
report return shapes. Repair only new snapshot boundary: convert chain entry/
final-entry containers to tuples; do not broaden comparator, weaken closing
checks or change standalone helper. Remaining necessary repair invocation and
root remain within recorded three positions; failure retained, no refunds.

Same28 controls passed,3232 deselected,5.54 s after boundary repair. Required
root4183 passed,1 known transformer QDQ xfailed,71 warnings,116.84 s; root Ruff,
changed-file format check and whitespace passed. Editor/Pylance syntax clear.
AST confines source changes to delivery snapshot method/new test; all other nodes
and pre-existing parameters preserved. All three pytest positions spent including
first failure; no aborts. Logs `cylinder-271-focused-1.log`/`-focused-2.log`/
`-root-1.log` retained under recovery directory. No additional C/Arm/sanitizer/
board opt-in gates ran.

All28 controls within caps: default calls none of five reports, matched original/
closing delivered/pending identities retained, missing/malformed and late report/
source/owner/budget changes suppress snapshot; stable mismatches remain reports,
not qualification. Detachment, held delivery and unresolved ties verified, input
tick/frame/both RNGs preserved. All eight flags false; no numerical/physical/
source/geometry/coverage/clock/one-use/permission/admission or usable command.
Next bounded matched supplied-word cylinder offset residuals, keeping geometric
error bounds and protected source/numerical/physical acceptance unresolved.

## 272. Matched Retained Cylinder Offset Residuals (2026-11-10)

Checkpoint `635483a` pushed/clean. Root review977 lines before growth; one guarded
10-second whole-section migration archived261-265 verbatim,237 archive lines,
five design references rebased, root747 lines. Originals and successful one-shot
`archive-272.py`/`cylinder-272-archive-1.log` retained under recovery directory;
do not rerun utility. Whitespace including staged new archive passed. Historical
ledgers/failed checks/unknown attempts preserved, not renewed or refunded.

Local hypothesis: matched supplied position/centre/offset words can feed existing
exact-rational difference diagnostic with original epoch/tick/delivery identities
and independent closing recomputation. Literal default-off
`include_cylinder_offset_residuals` requires `include_cylinder=True`. No adopted
geometric error bound or primitive uniform/source/numerical/physical proof.
Existing <=32 cylinders/130 words/64 entries/192 values/128 binary operations per
helper,4096-bit ceiling unchanged; <=18 invocations per helper across original/
closing delivered/<=8 pending records. Unknown observation residual stays unknown.

Finite routine plan: 23 synthetic controls, each <=4 steps/5 recorder reads/3
geometries/3 retentions; <=6 offset/matcher calls,2 pending matches/64 digests,
72 rational values/48 binary operations/48 exact oracle operations; optional
selection composition <=6 calls each of its five existing helpers. No runtime
intake/read/retain/step/reset/replay/clock; empty/one/two fixtures, held/delivered/
default/dependency/detachment, actual exact residuals, unknown infinite observation,
missing/malformed, late output/pending/native/cylinder/owner/budget and arithmetic
exhaustion. Input tick/frame/both RNGs preserved. Three pytest positions including
failures/aborts: first23/60 seconds, one necessary repair reserve, final root/300
seconds; retain `cylinder-272-*` logs. No protected studies/task data/dependencies/
hardware, all eight flags false, no geometry/coverage/source/numerical/physical/
clock/one-use/permission/admission or usable command. Next independently supported
matched projection arithmetic without inventing numerical or physical bounds.

First23 passed,3260 deselected,9.17 s. Required root4206 passed,1 known
transformer QDQ xfailed,71 warnings,107.25 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. Caller query returned no
sites, not static compatibility proof. AST confines changes to snapshot method/
new test, preserving all other nodes and pre-existing parameters. Two of three
pytest positions used, no failures/aborts; unused reserve is not follow-on
authority. Logs `cylinder-272-focused-1.log`/`cylinder-272-root-1.log` retained
under recovery directory. No additional C/Arm/sanitizer/board opt-in gates ran.

Exact rational oracle matches actual supplied words, altered finite observation
reports nonzero discrepancy, infinite observation remains unknown,16-bit control
exhausts conservatively. Default skips offset/rational work; matched delivered/
pending, late changes, detachment, optional selection composition and tick/frame/
RNG preservation verified. All eight flags false; no uniform geometric error or
source/numerical/physical/coverage/clock/one-use/permission/admission evidence.

Whole-section byte checks and prior REVIEW/Sources/design/stable AGENTS
conservation passed; eight changed local targets valid, no stale root261-265
anchor targets in searched unignored Markdown. Originals/logs retained.

## 273. Matched Retained Cylinder Projection Residuals (2026-11-10)

Checkpoint `48c5ea6` pushed/clean. Existing supplied-word projection helper owns
unrounded two-term horizontal dot-product discrepancy, not isolated primitive
rounding. Hypothesis: matched original/closing cylinder records can compose this
report with original epoch/acquisition/delivery identities under existing closing
checks. Literal default-off `include_cylinder_projection_residuals` requires
`include_cylinder=True`; default does no projection arithmetic. <=32 cylinders/
2304 words/2048 entries/2240 values/8192 binary operations per helper,4096-bit
ceiling unchanged; <=18 invocations across original/closing delivered/<=8 pending
records. Nonfinite observation residual stays unknown; nonfinite supplied offsets
remain unsupported. No uniform error bound/numerical/physical/source proof.

Finite routine plan: reuse23-case offset family in offset/projection modes,46
controls, preserving offset72 values/48 binary/48 oracle caps. Projection fixtures
<=1560 values/3072 binary/3072 exact oracle operations; per mode <=4 steps/5 reads/
3 geometries/3 retentions/6 active-helper/cylinder calls/2 pending matches/64
digests; optional existing selection helpers and offset helper <=6 calls each.
No runtime intake/read/retain/step/reset/replay/clock. Empty/one/two fixtures,
default/held/delivered/dependency/detachment, actual exact residuals/infinite
observation, malformed/missing/late outputs/sources/owner/budget and bit exhaustion;
combined projection+offset+selection preserves separate reports and all flags.
Three pytest positions including failures/aborts: first46/60 seconds, one necessary
repair reserve, final root/300 seconds; retain `cylinder-273-*` logs. No historical
refunds/protected studies/task data/dependencies/hardware; all eight flags false,
no geometry/coverage/source/numerical/physical/clock/one-use/permission/admission or
usable command. Next matched horizontal-norm arithmetic as an independent report.

First46 passed,3260 deselected,10.23 s. Required root4229 passed,1 known
transformer QDQ xfailed,71 warnings,180.44 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. Caller query returned no
sites, not static compatibility proof. AST confines changes to snapshot method/
existing arithmetic test family, preserving original23 cases and all other nodes/
existing snapshot parameters. Two of three pytest positions used, no failures/
aborts; unused reserve is not follow-on authority. Logs `cylinder-273-focused-1.log`/
`cylinder-273-root-1.log` retained under recovery directory. No additional C/Arm/
sanitizer/board opt-in gates ran.

Both exact oracles match supplied words, altered observations remain discrepancies,
nonfinite observation residuals remain unknown and16-bit control exhausts
conservatively. Default skips projection work; combined offset/projection/selection
reports preserve separate meanings, original/closing delivery identities and
tick/frame/RNG. Late changes suppress snapshots, stable mismatch does not qualify
geometry. All eight flags false, no primitive uniform/numerical/physical/source/
coverage/clock/one-use/permission/admission evidence or usable command. Next
independent matched horizontal-norm report; monitor chapter03 size before growth.

## 274. Lossless Cylinder Design-Topic Relocation (2026-11-10)

Checkpoint `03728a1` pushed/clean. Chapter03 at2486 lines before further contracts;
existing chapter04 at2196 cannot hold intact435-line cylinder topic within the
about2500-line organization target. Existing chapter05 at2016 can. One bounded
10-second guarded migration moved the complete cylinder topic to chapter05
verbatim, preserving all prior destination text, source prefix, references and
27 historical heading anchors at the old location. Two incoming targets updated;
same-directory relative topic references need no rebasing. New chapter03/05 sizes
2083/2452 lines. No accepted requirements or evidence meanings changed.

Original four documents and successful one-shot `relocate-274.py`/
`cylinder-274-relocation-1.log` retained under recovery directory; do not rerun
utility. Immediate written byte checks and whitespace passed. Finite documentation
scope: one migration and scoped content/anchor/local-target conservation; no
source edits, project imports, fixtures, arithmetic, root/style tests, downloads,
dependencies, model/hardware or protected studies. Unchanged successful code gate
not rerun. All eight flags remain false; historical failures/unknown/spent ledgers
unchanged. Next independent matched horizontal-norm report using the existing
bounded helper, no numerical/source/physical/coverage/clock/permission/admission.

Independent conservation passed: whole topic byte-exact, prior chapter03 prefix/
chapter05 entirety and root REVIEW/Sources/stable AGENTS intact, only intended
incoming pointer changes. All27 historical heading anchors preserved and30
moved/changed local targets valid. Whitespace passed; code suite not rerun.

## 275. Matched Retained Cylinder Horizontal-Norm Residuals (2026-11-10)

Checkpoint `a9c453e` pushed/clean. Existing shared64-ray squared horizontal norm
helper owns unrounded supplied-word sum-of-squares discrepancy, not geometry or
isolated primitive rounding. Hypothesis: matched original/closing cylinder
records compose that shared report even with zero cylinders, retaining original
epoch/acquisition/delivery identities and all closing checks. Literal default-off
`include_cylinder_horizontal_norm_residuals` requires `include_cylinder=True`.
Existing256 words/64 entries/192 values/256 binary operations per helper,
4096-bit ceiling unchanged; <=18 invocations across original/closing delivered/
<=8 pending records. Nonfinite observation residual stays unknown.

Finite routine plan: reuse23-case arithmetic family in offset/projection/norm
modes,69 controls. Unchanged offset72 values/48 binary/48 oracle caps; unchanged
projection1560 values/3072 binary+oracle caps. New norm fixtures <=2352 values/
3096 binary/1536 exact oracle operations including combined existing projection/
offset/selection reports; <=6 calls each included helper. Per mode <=4 steps/
5 reads/3 geometries/3 retentions/6 cylinder matches/2 pending matches/64 digests,
no runtime intake/read/retain/step/reset/replay/clock. Empty/one/two fixtures,
exact actual oracles, default/dependency/held/delivered/detachment, nonzero or
unknown observed residual, missing/malformed/late output/pending/native/cylinder/
owner/budget and bit exhaustion; preserve tick/frame/both RNGs. Three pytest
positions including failures/aborts: first69/60 seconds, one necessary repair
reserve, final root/300 seconds; retain `cylinder-275-*` logs. No historical refunds/
protected studies/task data/dependencies/hardware; all eight flags false, no
uniform/numerical/physical/source/geometry/coverage/clock/one-use/permission/
admission or usable command. Next independent matched discriminant arithmetic.

First69 passed,3260 deselected,12.35 s. Required root4252 passed,1 known
transformer QDQ xfailed,71 warnings,113.14 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. Caller query returned no
sites, not static compatibility proof. AST confines changes to snapshot method/
existing arithmetic family; original23 cases and all other nodes/existing
snapshot parameters preserved. Two of three pytest positions used, no failures/
aborts; unused reserve is not follow-on authority. Logs `cylinder-275-focused-1.log`/
`cylinder-275-root-1.log` retained under recovery directory. No additional C/Arm/
sanitizer/board opt-in gates ran.

Actual shared norm oracle matches even with zero cylinders; nonzero/unknown
observed residuals, unchanged old-mode caps, combined independent reports,
default skipped work, late-change suppression, conservative bit exhaustion and
tick/frame/RNG preservation verified. All eight flags false; no uniform/numerical/
physical/source/geometry/coverage/clock/one-use/permission/admission evidence or
usable command. Next matched discriminant discrepancy as an independent report.

## 276. Matched Retained Cylinder Discriminant Residuals (2026-11-10)

Checkpoint `d74dbd5` pushed/clean. Existing supplied-word helper owns unrounded
projection^2-horizontal_squared*(offset norm-radius^2) discrepancy, not isolated
primitive or geometry qualification. Hypothesis: matched original/closing cylinder
records can compose that report with original epoch/acquisition/delivery identities
and all existing closing checks. Literal default-off
`include_cylinder_discriminant_residuals` requires `include_cylinder=True`.
Existing <=32 cylinders/4256 words/2048 entries/4256 values/8352 binary operations
per helper,4096-bit ceiling unchanged; <=18 invocations across original/closing
delivered/<=8 pending records. Nonfinite observation residual stays unknown;
unsupported nonfinite supplied operands still reject conservatively.

Finite routine plan: reuse23-case arithmetic family in four modes,92 controls;
prior mode caps unchanged. New discriminant fixtures <=3522 values/4662 binary/
3132 exact oracle operations including combined existing norm/projection/offset/
selection reports, <=6 calls each included helper. Per mode <=4 steps/5 reads/3
geometries/3 retentions/6 cylinder matches/2 pending matches/64 digests, no runtime
intake/read/retain/step/reset/replay/clock. Empty/one/two fixtures, exact base/dot/
discriminant oracles, default/dependency/held/delivered/detachment, nonzero or
unknown observed residual, missing/malformed/late output/pending/native/cylinder/
owner/budget and bit exhaustion; preserve tick/frame/both RNGs. Three pytest
positions including failures/aborts: first92/60 seconds, one necessary repair
reserve, final root/300 seconds; retain `cylinder-276-*` logs. No historical refunds/
protected studies/task data/dependencies/hardware; all eight flags false, no
uniform/numerical/physical/source/geometry/coverage/clock/one-use/permission/
admission or usable command. Next independent matched root-squared consistency.

First92 passed,3260 deselected,26.53 s. Initial required root1 failed,4274
passed,1 known transformer QDQ xfailed,71 warnings,138.56 s. Failure is unchanged
`test_build_audit_timeout_terminates_descendants[timeout]`, test line1923:
`status.exists()` then `/proc/171341/stat` read raised `ProcessLookupError` as
the descendant disappeared. Primary log retains the traceback; this is the same
exists/read race family retained in §251, not a discriminant failure or proof of
a fixed cleanup test. No unrelated source/test edit, tolerance/assertion change
or old-budget refund. Root Ruff/format/diff tail did not execute after failure;
narrow style and editor/Pylance syntax already passed. Caller query returned no
sites, not compatibility proof; AST preserves original23 cases and all nodes/
parameters outside the changed snapshot method and arithmetic family.

Narrow routine-plan revision: use the one unused necessary-repair reserve for
one required root revalidation/300 seconds plus original style/diff gates. Three
pytest positions total unchanged, first focus and failed root spent, no extra
focused invocation or retry beyond this remaining position. Retain both root
logs, diagnose any new failure; no protected experiments or additional opt-ins.

Single remaining root revalidation4275 passed,1 known transformer QDQ xfailed,
71 warnings,123.90 s; root Ruff, changed-file format check and whitespace passed.
Unrelated audit source/test confirmed unchanged. All three pytest positions
spent including failed root, no aborts; no further check position or historical
refund. Logs `cylinder-276-focused-1.log`/`cylinder-276-root-1.log`/
`cylinder-276-root-2.log` retained under recovery directory. Successful
revalidation does not fix or erase the race. No additional C/Arm/sanitizer/board
opt-in gates ran.

Exact supplied-word discriminant oracle, nonzero/unknown observed residuals,
unchanged prior mode caps, combined independent reports, default skipped work,
late-change suppression, conservative bit exhaustion and tick/frame/RNG preserved.
All eight flags false; no uniform/numerical/physical/source/geometry/coverage/
clock/one-use/permission/admission or usable command. Next independent matched
root-squared consistency; archive whole266-270 before further root-review growth.

## 277. Matched Retained Cylinder Root-Squared Consistency (2026-11-10)

Whole266-270 archive moved verbatim (234 lines), root752 lines, five chapter05
references rebased; exact previous sections/bibliography and eight local targets
passed, whitespace passed. One guarded migration/check invocation,30 s cap,
no failure/abort; originals/script/log retained under recovery directory.
Code suite not rerun for the archive. Do not rerun successful migration utility.

Hypothesis: default-off literal `include_cylinder_root_squared_residuals` requiring
`include_cylinder=True` composes the existing supplied-root-squared minus clamped
supplied-discriminant helper with matched delivered/pending identities and closing
checks. Negative-root status is separate from squared residual; matching squares
do not certify sqrt rounding or geometry. Cheapest discriminator: same23-case
snapshot family expanded to fifth mode,115 cases, exact independent oracle.

Fresh bounded routine ledger under standing authority: <=3 pytest invocations,
focused then root plus one diagnosed-repair reserve,300 s each; default root
`python -m pytest -q && ruff check . && git diff --check`, changed Python format
check. Fixture <=4steps/5reads/3geometries/3retentions/6active-helper+cylinder
matches/2pending matches/64digests. Root mode <=4290 values/5430 binary operations/
768 oracle operations; prior four caps unchanged. Combined control additionally
calls offset/projection/norm/discriminant/chain <=6each. No snapshot intake/read/
retain/step/reset/replay/clock; tick/frame/RNG preserved. Existing helper <=32
cylinders/4096 words/2048 entries/4096 values/4096 binary operations,4096-bit
ceiling unchanged; <=18 helper calls per API bound. Preserve failures and unknown
historical attempts; diagnose before any rerun, no protected run or old refund.
No additional C/Arm/sanitizer/board opt-ins, dependencies, models or task data.

First focused114 passed/1 failed/3260 deselected,40.68 s: root `work_limit`
expected unknown, but unchanged scene arithmetic fit the reduced16-bit budget.
This invalid test expectation is not production budget enforcement failure.
Repair only root-mode work-limit fixture: explicit21-bit supplied root `2**20`
before applying16-bit monkeypatch, without changing production4096-bit ceiling,
prior mode caps or tolerances. Same115 controls rerun using the diagnosed-repair
reserve; one required root invocation then exhausts the original three positions.
First failure log retained; no failure erased/refunded, no abort.

Repaired focused115 passed/3260 deselected,21.07 s. Changed Python formatted/
lint passed; editor/Pylance syntax clean. Auxiliary AST check first stopped at
incorrect public class-name lookup (`StopIteration`); corrected only checker
to actual `_SyntheticC1SourceRecorder` owner. AST then confirms only snapshot
and existing arithmetic test family changed, previous keyword defaults and23
cases preserved. Pylance signature query found no call sites, not compatibility
proof. Selected editor and terminal interpreter both `/opt/venv/bin/python`,
Python3.12.3 terminal. Required root invocation remains within original ledger.

Required root4298 passed,1 known transformer QDQ xfailed,71 warnings,136.19 s;
root Ruff, whitespace and changed-file format checks passed. All three pytest
positions spent including first focused failure, no abort. Logs
`cylinder-277-focused-1.log`/`cylinder-277-focused-2.log`/
`cylinder-277-root-1.log` and archive log/script/originals retained under recovery
directory. No additional C/Arm/sanitizer/board opt-in gates ran.

Default skipped work, delivered-only/pending/empty/two-cylinder identity, exact
squared oracle, negative-root/nonfinite statuses, detached outputs, late change
suppression and forced bit exhaustion verified; prior four modes/caps preserved.
All eight flags false; no sqrt-rounding certification, uniform/numerical/physical/
source/geometry/coverage/clock/one-use/permission/admission or usable command.
Next independent matched side-numerator arithmetic, not corrected upstream words.

## 278. Matched Retained Cylinder Side-Numerator Residuals (2026-11-10)

Whole historical NF1 identity/digest/proposed-protocol scopes (186 lines) moved
unchanged from chapter05 to adjacent chapter04; three old heading anchors retained,
three review references carried unchanged and reading-map pointer updated. Prior
chapter04/source remainder/map conserved, seven local targets and whitespace
passed; chapter04 2387/chapter05 2331 lines. One guarded migration/check,30 s cap,
no failure/abort; originals/script/log retained under recovery directory. No code
suite for docs-only move, no historical NF1/SC18 imports or runs/claim adoption.

Hypothesis: default-off literal `include_cylinder_side_numerator_residuals`
requiring `include_cylinder=True` composes captured projection/root and ordered
near/far numerator words through the unchanged supplied-word helper. Matched
delivered/pending identities and independent closing checks remain; no corrected
upstream words. Cheapest discriminator: existing23-case snapshot family in six
modes,138 cases; independent exact `-projection +/- root` oracle for both sides.

Fresh bounded routine ledger under standing authority: <=3 pytest invocations,
focused then required root plus one diagnosed-repair reserve,300 s each. Root
`python -m pytest -q && ruff check . && git diff --check`, changed Python format
check. Fixture <=4steps/5reads/3geometries/3retentions/6active-helper+cylinder
matches/2pending matches/64digests. New mode <=5832 values/7350 binary operations/
2304 oracle operations; prior five caps unchanged. Combined control adds previous
five arithmetic helpers and chain <=6each. No snapshot intake/read/retain/step/
reset/replay/clock; tick/frame/RNG preserved. Existing helper <=32 cylinders/8192
words/4096 entries/8193 values/10240 binary operations,4096-bit ceiling unchanged;
<=18 original/closing invocations across delivered/<=8 pending records. Explicit
21-bit observed numerator in16-bit work-limit control; do not assume scene alone
exhausts reduced arithmetic. Preserve failures/unknown historical attempts; diagnose
before rerun, no protected experiment or old refund. No additional C/Arm/sanitizer/
board opt-ins, dependencies, models or task data.

Focused138 passed/3260 deselected,32.67 s. Required root4321 passed,1 known
transformer QDQ xfailed,71 warnings,185.20 s; root Ruff, changed-file format and
whitespace passed. Editor/Pylance syntax clean; AST confirms only snapshot and
existing arithmetic family changed, prior defaults/23 cases conserved. Pylance
signature query found no call sites, not compatibility proof. Two of three pytest
positions used, no failure/abort; unused reserve is not follow-on authority.
Logs `cylinder-278-focused-1.log`/`cylinder-278-root-1.log` and relocation script/
originals/log retained under recovery directory; no additional C/Arm/sanitizer/
board opt-in gates ran.

Both side signs/ordered observed words and exact oracle, nonzero/unknown residuals,
default skipped work, detached output, identity/closing suppression and forced bit
exhaustion verified. Prior five caps unchanged. All eight flags false; no isolated
primitive/FMA or uniform error, geometry/physical/source/coverage/clock/one-use/
permission/admission or usable command. Next matched guarded side-division arithmetic.

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
