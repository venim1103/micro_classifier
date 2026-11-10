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

Checkpoints 246 onward and the source bibliography remain below.
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

## 246. Actual Native ToF Cylinder Quadratic Trace (2026-11-10)

Checkpoint `938646c` pushed/clean. Local hypothesis: an optional cold trace can
retain the actual existing horizontal squared norm and per-cylinder offset,
projection, discriminant and clamped-square-root results without reevaluating
them or changing first-return words. No acquisition/recorder path is wired yet.
Require empty separate builtin dict, mounted finite native pose/actual profile
and existing32-obstacle cap before geometry; detach retained arrays/inputs and
preserve all eight false flags. Capture post-wall and final pre-noise arrays as
context, not cylinder side/top arithmetic or final scene geometry proof.

Twenty-one bounded synthetic controls, <=2 geometry/direction evaluations each
(baseline/traced), <=32 intercepted roots and100 candidate minima for the traced
call; <=32 fixed64-ray quadratic oracle checks. Max-obstacle case reuses one
declared cylinder32 times, not independent episodes/task data. No step/reset/
clock/RNG, source replay, rational arithmetic, dependencies/downloads/models or
hardware. Three pytest positions including failures/aborts: first21/60 seconds,
one necessary repair reserve, final root/300 seconds. Retain `cylinder-246-*`
logs in existing recovery directory; old budgets/unknown attempts unchanged.

First21 passed,2606 deselected,2.50 s. Focused Ruff/format/whitespace passed.
Required root:3550 passed,1 known transformer QDQ xfailed,71 warnings,89.08 s;
root Ruff, changed-file format check and whitespace passed. Two of three pytest
positions used, no failure/abort; unused reserve is not follow-on authority.
Editor diagnostics clear; AST proves only `tof_ranges` and one new test changed,
all other source/test nodes intact. Pylance after formatting reports all24
resolved `tof_ranges` call sites compatible. No additional C/Arm/sanitizer/board
opt-in gates ran; host checks do not qualify linked firmware or hardware.

Controls intercept the actual roots and reductions, check copied quadratic
words against the original expressions, compare baseline/traced first returns,
and test detachment and bounded preflight rejection. Synthetic degenerate rays
are unit fixtures, not a sensor domain or task cohort. Logs retained, no cleanup
or acquisition/recorder changes. All eight flags false, no adopted numerical/
physical/source/clock/coverage/geometry/permission/admission evidence or usable
command. Next retain actual side/top calculation stages; a quadratic-only trace
and matching final words do not establish the missing cylinder reduction chain.

## 247. Actual Native ToF Cylinder Side/Top Trace (2026-11-10)

Checkpoint `971e33d` pushed/clean. Local hypothesis: naming the existing side
numerator, top offset and radial sum permits copying actual side/top operands,
distances, projections, masks, candidates and predecessor/result minima without
changing numerical order or first returns. Preserve the cold-only bounded trace,
strict preflight/defaults and eight false flags; no acquisition wiring yet.

Extend the existing21 controls with two declared valid side/top ray cases;
23 controls, unchanged <=2 geometry/directions,32 roots/obstacle oracle records,
100 minima/candidates and101 divisions intercepted for traced call. Added fixed
64-ray side/top correspondence and detachment checks, not new episodes, sensor
domain or geometry/error qualification. Three pytest positions including
failures/aborts: first23/60 seconds, one necessary repair reserve, final root/
300 seconds. Retain `cylinder-247-*` logs, no old attempt refund. No step/reset/
clock/RNG/replay/study/task data/model/dependency/download/hardware action.

First invocation:2 failed,21 passed,2606 deselected,3.49 s. Both newly declared
valid-hit fixtures assumed start(2,2), while actual `Scenario.start` defaults
to(1,3). Set the fixture's intended start explicitly; no production repair,
predicate/limit/tolerance relaxation or extra scenario family. Existing21
controls passed. Retain failure/log/position; rerun same23 within reserve.

Same23 passed,2606 deselected,2.91 s; focused Ruff/format/whitespace passed.
Required root:3552 passed,1 known transformer QDQ xfailed,71 warnings,87.53 s;
root Ruff, changed-file format check and whitespace passed. All three pytest
positions spent including first failure; no abort. Editor diagnostics clear;
AST proves only `tof_ranges` and existing cylinder matrix changed, all other
source/test nodes intact. Signature unchanged from §246's24 compatible callers.
No additional C/Arm/sanitizer/board opt-in gates ran; host checks do not qualify
firmware/hardware. Logs retained, no cleanup or extra source acquisition.

Actual intercepted divisions/candidates/minima match copied side/top records;
quadratic/post-wall/cylinder/final lineage and bitwise baseline parity hold for
these bounded fixtures. Valid-hit declarations are not physical sensor evidence
or coverage/error qualification. All eight flags false, no geometry, uniform
error, physical/source/clock/permission/admission or usable command. Next pair
the complete trace with actual fresh native acquisition, then closed intake/
retention; no held tick or matching word substitutes for original source IDs.

## 248. Actual Fresh ToF Cylinder Acquisition Pairing (2026-11-10)

Checkpoint `9a0a1a8` pushed/clean. Local hypothesis: cylinder capture can follow
the owning fresh wall path, forwarding one dict through existing update/sample
and pairing it to original native cache/RNG/tick/delivery identities. Literal
bool opt-in requires native mounted source; preflight before mutation/clocks.
Default/held/reset clears cache, rejected preflight preserves previous caches.
No additional geometry, RNG or clock reads; wall/selection/timing coexist.

Reuse original16 wall acquisition controls and caps unchanged, add independent
16-case cylinder family with same<=3 geometry/1 trace/1 selection/2 timing reads.
Three pytest positions including failures/aborts: first32/60 seconds, one
necessary repair reserve, final root/300 seconds. Retain `cylinder-248-*` logs.
No recorder/intake/study/task-data/model/dependency/download/hardware action;
all eight flags false, no geometry/coverage/error/source/clock/permission or
admission qualification. Old unknown/spent attempts are not refunded.

First32 passed,2613 deselected,3.16 s. Nearby fixture inspection confirms the
shared parent has no obstacles. Strengthen only cloned cylinder-family setup
with one declared cylinder, require nonempty side/top records and mutate a side
copy in detachment control. Parent and original wall family remain unchanged;
no extra acquisition or higher case/work cap. Reuse reserve for same32 controls.

Strengthened same32 passed,2613 deselected,2.74 s; focused Ruff/format/whitespace
passed. Required root:3568 passed,1 known transformer QDQ xfailed,71 warnings,
86.56 s; root Ruff, changed-file format check and whitespace passed. All three
pytest positions spent, no failures/aborts. Editor diagnostics clear; AST proves
only reset/update/sample/step and existing acquisition matrix changed, all other
source/test nodes intact. Pylance reports6 compatible callers each for update/
sample; step38 of40 compatible with the same2 intentional invalid receipt-bool
tests at159/299. No additional C/Arm/sanitizer/board opt-in gates ran.

Archived complete236-240 byte-for-byte into `docs/review/236-240.md`, rebased5
design references and updated root map. Immediate conservation passed; original
root retained as `cylinder-248-review-before.md` under recovery directory. Root
was beyond1000 lines; after move764 before this final record. No old evidence,
failures, ledgers or source bibliography removed or renewed; logs/backups remain.

Actual nonempty trace, native sample and companions share original acquisition
IDs with no extra geometry/clock/RNG; successful copy mutation cannot alter
native words. These are bounded synthetic controls, not source/geometry/coverage/
uniform error/physical/clock/permission/admission qualification. All eight flags
false and no usable command. Next closed cylinder intake with typed fixed shapes,
canonical detached words and closing source/cache/profile/output checks; no replay.

## 249. Bounded Native ToF Cylinder Intake (2026-11-10)

Checkpoint `a8ead88` pushed/clean. Local hypothesis: closed typed acquisition/
trace/cylinder/side/top layouts and fixed arrays can be detached to canonical
words, bracketed by two existing native intakes and closing cache/RNG/profile/
pose/content/output checks. No geometry replay, hashing, recorder read or clock.
Up to32 cylinders, each two sides/one top, fixed64-ray arrays; each metadata
pass <=45696 canonical array/entry words plus6144 builtin mask booleans. Inputs
remain under the existing native template/profile budget; no arithmetic proof.

Reuse original16 wall-intake cases/caps and add23 cylinder cases including
malformed side/top/type controls and max32 repeated declared cylinders. One
setup step/geometry, <=2 native intakes per case; existing parent ledgers remain
unchanged. Three pytest positions including failures/aborts: first39/60 seconds,
one necessary repair reserve, final root/300 seconds. Retain `cylinder-249-*`
logs, no old attempt refund/study/task-data/model/dependency/download/hardware.
All eight flags false, no geometry/coverage/error/source/clock/permission or
admission qualification and no usable command.

First39 passed,2629 deselected,3.42 s; original16 wall cases unchanged in scope.
Required root3591 passed,1 known transformer QDQ xfailed,71 warnings,82.82 s;
root Ruff, changed-file format check and whitespace passed. Editor diagnostics
clear. AST proves one added intake helper and only the existing intake matrix
changed; all prior source/test nodes remain. No prior signature changed. Two
of three pytest positions used, no failures/aborts; unused reserve is not
follow-on authority. `cylinder-249-focused-1.log`/`cylinder-249-root-1.log`
retained under the recovery directory. No additional C/Arm/sanitizer/board
opt-in gates ran.

Successful max32 and nonempty copies preserve original IDs/words and are
detached; malformed layout, oversized/count/type/nonfinite controls reject
before native intake and late mutations reject without publishing a result.
All eight flags false, no source/geometry/coverage/numerical/physical/clock/
permission/admission qualification and no usable command. Next typed cylinder
history prehash validation, then explicit recorder retention. No replay or
automatic source adoption follows from matching words.

## 250. Typed Cylinder History Prehash Guard (2026-11-10)

Checkpoint `453deeb` pushed/clean. Local hypothesis: use the paired, already
validated native history to build closed cylinder trace/stage shapes, then
reject malformed/noncanonical/overlong words and inconsistent native IDs or
declared operands before hashing. Exact builtin lists <=8 each, strictly
increasing ticks and unique epoch/tick/delivery pair; <=32 cylinders each with
two ordered sides/cap and fixed64-ray flattened tuples. At max8x32, <=365568
float-word parses (each <=32 characters) plus49152 literal mask booleans; no
source intake/copy/hash/read/retention/replay/clock/RNG in the guard.

Reuse original16 wall history cases/caps, add26 cylinder controls including
8x32 typed records, malformed side/top, nonfinite/range/word budgets and source
list caps. One setup step/geometry and <=2 setup native intakes per case before
patching all source/read/hash/replay hooks forbidden. Parent ledgers unchanged.
Three pytest positions including failures/aborts: first42/60 seconds, one
necessary repair reserve, final root/300 seconds; retain `cylinder-250-*`
logs. No old refunds, protected studies, task data, dependencies or hardware.
All eight flags false; no geometry/coverage/error/source/clock/permission or
admission qualification and no usable command. Recorder wiring remains next.

First42 passed,2652 deselected,3.85 s. Required root3617 passed,1 known
transformer QDQ xfailed,71 warnings,123.49 s; root Ruff, changed-file format
check and whitespace passed. Editor diagnostics clear. AST proves one added
history guard and only existing history matrix changed; all prior source/test
nodes intact. No prior signature changed. Two of three pytest positions used,
no failures/aborts; unused reserve is not follow-on authority. Logs
`cylinder-250-focused-1.log`/`cylinder-250-root-1.log` retained under recovery
directory. No additional C/Arm/sanitizer/board opt-in gates ran.

Max8x32 retained shapes pass without mutating either supplied history; malformed
words/stages/IDs/budgets fail without any source intake/hash/read/recorder/
geometry/clock activity inside the guard. Synthetic cloned IDs are unit fixtures,
not fresh acquisition or one-use/timing/physical evidence. All eight flags false,
no source/geometry/coverage/uniform error/numerical/physical/clock/permission/
admission qualification and no usable command. Next explicit cylinder retention
using this guard before history hash, then delivery correspondence.

## 251. Explicit Cylinder Recorder Retention (2026-11-10)

Checkpoint `5c54dc7` pushed/clean. Local hypothesis: mirror existing explicit
wall retention with literal `include_cylinder=False`, typed cylinder guards
before every history hash, original cache/history identities and closing source/
entry/producer/owner checks, then commit all staged histories together. Cylinder
history follows native retained ticks (<=8); default ignores cold cylinder cache
and no source read/step/replay/clock occurs inside retention. Delivery remains
separate work. Reuse original17 wall cases unchanged in scope and caps, add17
cylinder cases on a cloned one-cylinder scene with a new standard recorder.

Per case <=13 setup geometries,14 setup reads,10 retention calls,20 selected
intakes,40 native intakes (combined originalwall10/newcylinder14 with wall/
selection/timing),256 binding checks and only2 setup clocks in combined cases.
Each cylinder intake retains <=32/fixed64-ray bounds; each typed guard <=8x32
retained entries, at most6 guards per successful retention. No relaxation of
old caps or numerical assertions. Three pytest positions including failures/
aborts: first34/60 seconds, one necessary repair reserve, final root/300 seconds;
retain `cylinder-251-*` logs. No old refunds, protected runs, data, dependencies
or hardware. All eight flags false, no qualification/admission or usable command.

First34 passed,2677 deselected,6.59 s. Focused Ruff/format/whitespace and editor
diagnostics passed; AST proves only recorder constructor/retention and existing
retention matrix changed. Pylance resolved no callers at formatted retention
position13027:8 (zero-based), so no static compatibility evidence is claimed.

First required root failed:1 failed,3633 passed,1 known transformer QDQ xfailed,
71 warnings,94.83 s. Unchanged interface timeout descendant test raced between
`/proc/89124/stat` `exists()` and `read_text()`; FileNotFoundError at test1923,
not a retention assertion. No source/test repair or assertion/limit relaxation.
Root Ruff/format/whitespace after `&&` did not run in that invocation. Preserve
`cylinder-251-root-1.log` and the spent position. Narrow revised routine plan:
use the one remaining third pytest position for required-root revalidation once
with the same300-second cap; no separate isolated rerun, no new protected work.
If the unchanged failure recurs, retain it as a root-checkpoint blocker rather
than repeat it or modify unrelated code. Earlier successful focused gate is not
rerun for reassurance.

Required root revalidation passed:3634 passed,1 known transformer QDQ xfailed,
71 warnings,91.18 s; root Ruff, changed-file format check and whitespace passed.
All three pytest positions spent: first focused pass, root failure, root pass;
no aborts. `cylinder-251-focused-1.log`/`cylinder-251-root-{1,2}.log` retained
under recovery directory. Successful revalidation does not fix or erase the
unchanged `/proc` test race. No additional C/Arm/sanitizer/board opt-in gates ran.

Nonempty cylinder retention, defaults, duplicate equality/changed-word rejection,
tick trimming/gaps, prehash canonical failures, late/cache/history/output/owner
mutations and wall/selection/timing coexistence pass within stated caps. Parent
ledgers unchanged. All eight flags false, no source/geometry/coverage/uniform
error/numerical/physical/clock/one-use/permission/admission qualification and no
usable command. Next detached delivered/pending cylinder matching with closing
retained-history/cache/output checks; no publication is implied by retention.

## 252. Delivered and Pending Cylinder Correspondence (2026-11-10)

Checkpoint `e4e69c0` pushed/clean. Local hypothesis: separate literal
`include_cylinder=False` matches one retained record for each delivered/pending
native original epoch/tick/delivery, validates typed copies before hashing,
then closes matching/history/producer/output checks before publication. Default
skips cylinder history; no acquisition replay, intake, recorder read or clock.
Unknown must omit source/frame and all companion payloads. At most8 typed
cylinder guards per successful snapshot, each <=8x32 word/mask budgets.

Reuse original24 wall snapshot cases/caps, add24 cylinder cases with a cloned
one-cylinder scene/new standard recorder. Setup <=4 steps,5 reads,3 geometry/
retentions,6 setup clocks only combined; each retention's prior bounds unchanged.
Snapshot <=6 each selected/wall/selection/timing/arithmetic matchers,2 pending
matchers,4 queue copies,2 frame checks,64 binding checks; no new rational work.
Three pytest positions including failures/aborts: first48/60 seconds, one
necessary repair reserve, final root/300 seconds; retain `cylinder-252-*` logs.
No old refunds/protected runs/task data/dependencies/hardware. All eight flags
false; no geometry/coverage/error/source/clock/permission/admission or usable
command. Matching words preserve, rather than resolve, unequal-word value ties.

First48 passed,2687 deselected,8.92 s. Required root3658 passed,1 known
transformer QDQ xfailed,71 warnings,90.29 s; root Ruff, changed-file format
check and whitespace passed. Editor diagnostics clear. AST proves one added
matcher, only delivery snapshot and existing snapshot matrix changed; all other
source/test nodes intact. Pylance resolved no callers at formatted snapshot
position13529:8 (zero-based), so no static compatibility evidence. Two of three
pytest positions used, no failures/aborts; unused reserve is not follow-on
authority. Logs `cylinder-252-focused-1.log`/`cylinder-252-root-1.log` retained
under recovery directory. No additional C/Arm/sanitizer/board opt-in gates ran.

Delivered/pending and held/original IDs, nonempty detached copies, defaults,
literal flags, missing pairs, typed/canonical/oversize controls, late retained/
outgoing/owner/companion mutations and prehash late-budget rejection pass within
stated caps. Parent ledgers unchanged. All eight flags false, no source/geometry/
coverage/numerical/physical/uniform error/clock/one-use/permission/admission
qualification and no usable command. Next independent supplied-word cylinder
offset discrepancies; no fresh sampling or uniform error bound follows.

## 253. Supplied-Word Cylinder Offset Discrepancies (2026-11-10)

Checkpoint `37aa5b0` pushed/clean. Local hypothesis: exact supplied position-minus-
centre differences and observed-minus-exact residuals can be reported per axis
without source intake/replay or adopting primitive/uniform error bounds. Canonical
word preflight <=130 builtin strings (each <=32 characters), two finite position
words and <=32 finite centre/observed-offset pairs. Observed infinities retain
exact operand difference but unknown residual; signed-zero words retained, no
tie semantics inferred. Existing4096-bit rational ceiling, <=192 value calls and
128 binary operations,64 entries; no source/recorder read/hash/geometry/clock/RNG.

Reuse original16 wall offset controls/caps, add21 cylinder cases including actual
nonempty intake, empty/max32, word/count/type budgets and matching Fraction oracle.
Only actual case has <=1 setup geometry/selected intake,2 native intakes; parent
ledgers unchanged. Oldwall12value/8binary caps stay; newcyl192/128 plus <=128
independent oracle operations. Three pytest positions including failures/aborts:
first37/60 seconds, one necessary repair reserve, final root/300 seconds; retain
`cylinder-253-*` logs. No old refunds/protected runs/task data/dependencies/hardware.
All eight flags false, no geometry/coverage/numerical/physical/source/clock/
permission/admission qualification and no usable command. No composition yet.

First37 passed,2719 deselected,3.26 s. Required root3679 passed,1 known
transformer QDQ xfailed,71 warnings,92.42 s; root Ruff, changed-file format check
and whitespace passed. Editor diagnostics clear. AST proves one added offset
helper and only existing offset matrix changed; all prior source/test nodes
intact, no existing signature changed. Two of three pytest positions used, no
failures/aborts; unused reserve is not follow-on authority. Logs
`cylinder-253-focused-1.log`/`cylinder-253-root-1.log` retained under recovery
directory. No additional C/Arm/sanitizer/board opt-in gates ran.

Actual nonempty words, exact/rounded/mismatched/signed-zero/subnormal/large/
infinite cases, empty/max32 and preflight/work-budget rejection agree with
independent Fraction oracle within stated caps, leaving inputs/tick/RNG unchanged.
All eight flags false, no geometry/coverage/source/uniform error/numerical/
physical/clock/one-use/permission/admission qualification or usable command.
Next supplied-word cylinder projection-expression discrepancy; intermediate
product words are not captured, so isolated multiply/add/FMA claims remain absent.

## 254. Supplied-Word Cylinder Projection Expressions (2026-11-10)

Checkpoint `867f44b` pushed/clean. Root review991 lines: archived whole241-245
byte-for-byte in `docs/review/241-245.md`, rebased5 design references/map. Exact
conservation passed; root now785 before this record. Originals retained as
`cylinder-254-{review,design}-before.md` in recovery directory. No old evidence,
failed checks, ledgers or source bibliography removed, renewed or refunded.

Local hypothesis: bounded exact supplied offset.x*ray.x + offset.y*ray.y and
observed-minus-unrounded discrepancy can be reported independently. Intermediate
products are not captured, so no isolated multiply/add/FMA or uniform error
claim. Canonical preflight <=2304 builtin words,32 characters each, <=32 offset
pairs/64 rays; finite offsets/rays, non-NaN observations may be infinite (unknown
residual). Existing4096-bit rational ceiling, <=2240 value calls/8192 binary
operations,2048 entries. No intake/read/hash/retention/replay/clock/RNG in helper.

22 synthetic cases in existing test file, including actual nonempty source,
empty/max32, Fraction oracle <=8192 operations and malformed/work budgets. Actual
setup <=1 geometry/selected intake,2 native intakes; parent ledgers unchanged.
Three pytest positions including failures/aborts: first22/60 seconds, one
necessary repair reserve, final root/300 seconds; retain `cylinder-254-*` logs.
No protected runs/task data/dependencies/hardware. All eight flags false, no
source/geometry/coverage/numerical/physical/clock/permission/admission or usable
command. No matched-source composition or clock bound follows.

First22 passed,2756 deselected,3.08 s. Required root3701 passed,1 known
transformer QDQ xfailed,71 warnings,87.85 s; root Ruff, changed-file format check
and whitespace passed. Editor diagnostics clear. AST proves only new projection
helper/test added; all prior source/test nodes intact, no existing signature
changed. Two of three pytest positions used, no failures/aborts; unused reserve
is not follow-on authority. Logs `cylinder-254-focused-1.log`/
`cylinder-254-root-1.log` retained under recovery directory. No additional
C/Arm/sanitizer/board opt-in gates ran.

Actual nonempty words, rounded/mismatched/signed-zero/subnormal/large/infinite
observations, empty/max32 and preflight/work-budget rejection agree with
independent Fraction oracle within caps, leaving input/tick/RNG unchanged. All
eight flags false, no source/geometry/coverage/isolated primitive/FMA/uniform
error/numerical/physical/clock/one-use/permission/admission qualification or usable
command. Next independently bounded quadratic/stage prerequisites; before the
design topic exceeds2500 lines, losslessly relocate complete cylinder topic into
an existing adjacent chapter with reading-map/target conservation checks.

## 255. Lossless Cylinder Design Topic Relocation (2026-11-10)

Checkpoint `d4016e5` pushed/clean. Chapter02 had2492 lines before additional
cylinder stages. Existing adjacent chapter03 had2050 lines and room for the
complete topic. Moved the whole cylinder prerequisite section and nine reference
definitions byte-for-byte, appended after existing chapter03 topics to avoid
changing their heading ownership. Both chapters share a directory, so those
relative targets remain unchanged; root design reading map points to chapter03,
and chapter02 has a short pointer. Immediate conservation passed; chapters02/03
were2339/2204 lines before the pointer. Originals retained as
`cylinder-255-design-{2,3}-before.md`/`cylinder-255-map-before.md` in recovery
directory. No evidence, failures, ledgers or source/test code changed or renewed.

Documentation-only: validate moved/new local targets, exact topic/definition/
prior-content conservation and whitespace; do not rerun successful code suite.
Eight flags remain false; no numerical/source/physical/clock/permission/admission
qualification or usable command. Next bounded horizontal squared-ray expression
diagnostic as a cylinder quadratic prerequisite, preserving combined-expression
limitations and the original4096-bit rational ceiling.

Actual checks passed: complete topic/nine definitions byte-exact, prior chapter/
map/checkpoint/Sources/stable instructions conserved,11 local targets/anchors
valid, no stale old cylinder target in tracked/unignored Markdown, whitespace
clear. Only five docs changed; final chapters02/03 are2343/2204 lines. Code suite
not rerun; §254 remains latest actual source gate. No failed/aborted check.

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
