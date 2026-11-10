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

Checkpoints 241 onward and the source bibliography remain below.
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

## 241. Native ToF Wall Projection Expression Residuals (2026-11-10)

Checkpoint `7450fb2` pushed/clean. Actual wall trace retains altitude/across
results but not intermediate products. Local hypothesis: diagnose each against
the exact unrounded supplied-word base+distance*direction expression after the
native nonfinite-distance zero fallback. This is a combined-expression residual,
not an isolated multiplication/addition rounding result, FMA claim, uniform
allowance, independent geometry/coverage/source qualification or admission.

Twenty bounded controls with unchanged parent fixtures; only actual-word case
uses one setup acquisition/geometry/closed wall intake with two native intakes.
Each case one helper call,963 canonical words<=32 characters,256 paired entries,
at most1283 guarded conversions/1536 guarded operations under existing4096-bit
cap. Independent fixture oracle at most1536 Fraction operations. During helper
no source intake/read/retention/step/reset/replay/clock/RNG. Three pytest positions
including failures/aborts: first20/60 seconds, one necessary repair/control
reserve, final root/300 seconds. Retain `wall-241-*` logs in existing local
recovery directory. All eight flags false, no old ledger refund or new study/
task data/model/dependency/download/native/hardware action. Preserve signed/raw
words; nonfinite observed projections leave residual unknown, not finite bounds.

First20 passed,2499 deselected,3.18 s. Focused Ruff/format/whitespace passed.
Required root:3442 passed,1 known transformer QDQ xfailed,71 warnings,104.32 s;
root Ruff, changed-file format check and whitespace passed. Two of three pytest
positions used, no failure/abort; unused reserve is not follow-on authority.
Editor diagnostics clear. AST comparison proves exactly one new helper/test;
every previous source/test node remains unchanged. No additional C/Arm/sanitizer/
board opt-in gates ran; host checks do not qualify firmware/hardware. Logs
retained, no cleanup/deletion or new dependency/download/model/study/hardware.

Actual-word fixture uses one fresh captured wall packet; other inputs are
declared synthetic. Signed/raw words and explicit nonfinite-distance fallback
are preserved; discrepancy reporting is not acceptance of changed arithmetic.
All eight flags false, no primitive roundoff/FMA/uniform-error or independent
masking/geometry/coverage/physical/source/clock/permission/admission qualification.
Next compose projection diagnostics with matched delivered/pending wall records
and original IDs, before independently supported mask/selection prerequisites.

## 242. Matched Native ToF Wall Projection Diagnostics (2026-11-10)

Checkpoint `7b6cc4f` pushed/clean. Local hypothesis: an independent literal
projection opt-in requiring matched wall publication can reuse the projection
helper under original epoch/acquisition/delivery IDs, alone or with offset/
division and other companions. All closing probes precede typed live-history
and outgoing comparisons. Default skips projection; unknown omits partial data.
No primitive-product/addition rounding, FMA, uniform allowance or qualification.

Extend the existing snapshot test, not another setup fixture: original18-case
family keeps4680 conversions/3120 operations/1536 oracle operations; new20-case
projection family includes dedicated late-projection and projection-only controls
with at most12378 conversions/12336 guarded operations/6144 Fraction oracle
operations. Common caps unchanged:4 setup steps,3 geometry/retentions,5 recorder
reads,6 setup clocks only with companions; at most6 of each diagnostic/matcher,
2 pending/4 queue/2 frame/64 bindings,4096-bit rational cap. No source intake/
read/retention/step/reset/replay/clock/RNG during snapshot. Three pytest positions
counting failures/aborts: first38/60 seconds, one necessary repair/control reserve,
final root/300 seconds. Retain `wall-242-*` logs in existing recovery directory.
All eight flags false, no old ledger refund or study/task data/model/dependency/
download/native/hardware action. New family adds work; old family caps unchanged.

First38 passed,2501 deselected,10.93 s, including all18 original cases with their
original caps and20 projection cases. Focused Ruff/format/whitespace passed.
Required root:3462 passed,1 known transformer QDQ xfailed,71 warnings,90.01 s;
root Ruff, changed-file format check and whitespace passed. Two of three pytest
positions used, no failure/abort; unused reserve is not follow-on authority.
Editor diagnostics clear. AST comparison confines changes to the existing
delivery snapshot and its existing integration test; all other source/test nodes
unchanged. No additional C/Arm/sanitizer/board opt-in gates ran; host checks are
not firmware/hardware capability. Logs retained, no cleanup/deletion.

Projection-only and combined paths use original matched record IDs; default
skips the new helper and unknown carries no partial data. Deliberate late
projection/companion/history mutations reject. All eight flags false, no adopted
primitive rounding/FMA/uniform error or geometry/coverage/physical/source/clock/
permission/admission qualification. Next independently check stored hit-mask
comparisons and candidate selection against captured distance/altitude/across
words and supplied native limits, without claiming physical intersections.

## 243. Native ToF Wall Mask/Candidate Word Correspondence (2026-11-10)

Checkpoint `c579ecc` pushed/clean. Local hypothesis: independently report whether
stored hit bits match the five native comparisons on supplied distance/altitude/
across/limit words, and whether candidate words match selection using the
observed hit bit. Keeping these checks separate distinguishes mask discrepancies
from candidate-copy discrepancies. `hit=True` plus+inf candidate is possible
under the native comparisons; it is not a finite physical intersection claim.

Twenty-one bounded controls with unchanged parent fixtures; only actual-word
case uses one setup acquisition/geometry/closed wall intake with two native
intakes. One helper call per case,1027 canonical words<=32 characters,256 strict
builtin hit bits/records,1280 predicate comparisons plus512 consistency checks;
fixture oracle at most1280 predicates. No source intake/read/retention/step/reset/
geometry/replay/clock/RNG or rational arithmetic during diagnostics. Three
pytest positions counting failures/aborts: first21/60 seconds, one necessary
repair/control reserve, final root/300 seconds. Retain `wall-243-*` logs in
existing recovery directory. All eight flags false, no adopted physical limits,
source/geometry/coverage/numerical/clock/permission/admission or usable command;
no old ledger refund or study/task data/model/dependency/download/hardware action.

First21 passed,2539 deselected,4.03 s. Focused Ruff/format/whitespace passed.
Required root:3483 passed,1 known transformer QDQ xfailed,71 warnings,113.87 s;
root Ruff, changed-file format check and whitespace passed. Two of three pytest
positions used, no failure/abort; unused reserve is not follow-on authority.
Editor diagnostics clear. AST comparison proves exactly one new helper/test;
all previous arithmetic/source/delivery/test nodes unchanged. No additional
C/Arm/sanitizer/board opt-in gates ran; host checks do not qualify hardware or
firmware. Logs retained, no cleanup/deletion or new dependencies/studies/models.

Actual-word fixture covers a fresh captured packet; other words are declared
synthetic. Mask and candidate discrepancies remain separate; signed-zero
candidate word changes reject correspondence even when numerically equal.
`hit=True` with+inf candidate is recorded without claiming a finite intersection.
All eight flags false, no adopted physical limits or source/geometry/coverage/
numerical/clock/permission/admission or usable command. Next advance supplied
per-wall minimum operand/result words, leaving equal-value/different-word ties
unknown rather than adopting unsupported host-specific tie semantics.

## 244. Native ToF Wall Minimum Word Correspondence (2026-11-10)

Checkpoint `145e134` pushed/clean. Local hypothesis: each wall minimum can be
checked against its supplied candidate and actual observed predecessor (floor
for wall0, previous observed wall minimum thereafter). Strict selection and
equal identical words support word correspondence. Equal-value/different-word
ties remain unresolved; wrong numeric values still mismatch. Do not adopt host
signed-zero tie semantics, propagate a reconstructed predecessor or infer final
cylinder/scene coverage, source/numerical/physical qualification or admission.

Twenty-three bounded controls with unchanged parent fixtures; only actual-word
case uses one setup acquisition/geometry/closed wall intake with two native
intakes. One helper call per case,576 canonical words<=32 characters,256 records,
at most1280 numerical/word comparison checks; fixture oracle same1280 ceiling.
No source intake/read/retention/step/reset/geometry/replay/clock/RNG or rational
arithmetic during diagnostics. Three pytest positions counting failures/aborts:
first23/60 seconds, one necessary repair/control reserve, final root/300 seconds.
Retain `wall-244-*` logs in existing recovery directory. All eight flags false;
no old ledger refund or study/task data/model/dependency/download/hardware action.

First23 passed,2560 deselected,2.65 s. Focused Ruff/format/whitespace passed.
Required root:3506 passed,1 known transformer QDQ xfailed,71 warnings,104.01 s;
root Ruff, changed-file format check and whitespace passed. Two of three pytest
positions used, no failure/abort; unused reserve is not follow-on authority.
Editor diagnostics clear. AST comparison proves exactly one new helper/test;
all previous arithmetic/source/delivery/test nodes unchanged. No additional
C/Arm/sanitizer/board opt-in gates ran; host checks do not qualify hardware or
firmware. Logs retained, no cleanup/deletion or new dependencies/studies/models.

The actual-word fixture uses one fresh wall packet; other words are declared
synthetic. Wrong upstream observations remain the next operation's recorded
operand rather than a reconstructed value. Strict signed-word mismatches and
unresolved equal-value ties remain distinct. All eight flags false, no adopted
tie semantics, uniform error, geometry/coverage/physical/source/clock/permission/
admission or usable command. Next compose mask/candidate/minimum diagnostics
with matched delivered/pending records and original IDs, preserving unknown ties
and finishing closing probes before payload comparisons.

Checkpoint administration: piping the diff through `head` under `pipefail`
stopped before staging. Verified HEAD/index unchanged; resume staging directly,
without repeating successful code gates or refunding any attempt.

## 245. Matched Native ToF Wall Selection Diagnostics (2026-11-10)

Checkpoint `3b6e6e8` pushed/clean. Local hypothesis: a separate literal-bool
wall-selection diagnostic opt-in can derive mask/candidate/minimum checks from
each matched delivered/pending wall record, preserving original three IDs and
unresolved word ties. Requires wall inclusion, skips by default. Collect closing
probes before typed live-history and outgoing comparisons; unknown omits payload.

Extend the existing38-case matrix without increasing either old family's caps.
New23-case family uses same setup<=4 steps/5 reads/3 geometry+retentions/6 setup
clocks when combined; snapshot<=6 each matcher/diagnostic,2 pending matchers,
4 queue copies/2 frame checks/64 bindings. Existing projection caps12378 rational
values/12336 operations/6144 oracle operations remain; new mask/minimum helpers
add no rational work. Each pair <=1603 canonical words,512 entries and existing
fixed predicate/word checks. All old fixture caps/unknown attempts unchanged.
Three pytest positions counting failures/aborts: first61 controls/60 seconds,
one necessary repair reserve, final root/300 seconds. Retain `wall-245-*` logs.
No read/retention/intake/step/reset/replay/clock/RNG during snapshot, no studies,
new dependencies/downloads/models/hardware. All eight flags false, no geometry,
coverage, physical/source/clock/numerical/permission/admission or usable command.

First invocation:18 failed,43 passed,2545 deselected,28.86 s. New probe used
nonexistent `inputs.bounds_m`; the existing closed packet and mask control use
`inputs.scenario.bounds`. Repair that lookup only and rerun the same61 controls
within the reserve. All38 original cases passed; failure/position/log retained,
no schema/cap/assertion/tolerance change or historical attempt refund.

Same61 passed,2545 deselected,11.58 s. Focused Ruff/format/whitespace passed.
Required root:3529 passed,1 known transformer QDQ xfailed,71 warnings,91.51 s;
root Ruff, changed-file format check and whitespace passed. All three pytest
positions spent including first failure; no abort. Editor diagnostics clear;
AST proves only owning snapshot and existing integration matrix changed, all
other source/test nodes intact. Pylance resolved no method call sites: no static
compatibility claim; runtime controls cover callers. No additional C/Arm/
sanitizer/board opt-in gates ran; host checks do not qualify firmware/hardware.

Moved all14 complete wall design sections and their14 reference definitions
byte-for-byte from chapter01 into existing chapter02; source pointer/root map
now locate them. Immediate conservation check passed, both original chapters
retained under `wall-245-design-{1,2}-before.md` in the recovery directory.
Chapter01 was2496 lines; relocation leaves2240 and chapter02 2321 before this
checkpoint's new section. No old evidence/ledgers/Sources or accepted contracts
changed; no successful code gate rerun for documentation. Logs/backups retained.

All eight flags false, no adopted uniform/native error, geometry/coverage,
physical/source/clock/permission/admission or usable command. Wall operation
correspondence does not cover the final cylinder/scene reduction. Next advance
actual cylinder arithmetic/source prerequisites without replay or qualification.

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
