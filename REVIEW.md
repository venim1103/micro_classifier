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
- [Checkpoints 281-285][chapter-review-21]

Checkpoints 286 onward and the source bibliography remain below.
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

## 289. Ray-Source Design Topic Relocation (2026-11-11)

Checkpoint006e699 pushed/clean. Before further chapter05 growth beyond2497lines,
moved three whole ray-generation/cold-pair/fresh-acquisition contracts and three
same-folder reference definitions intact to existing chapter01. Old three05
heading aliases remain reachable through [ray-generation design][native-tof-ray-design].
Initial move checks conserved exact prior chapter01, complete topic/ref bytes
and unrelated chapter05 bytes; whitespace passed. Chapter01 now2289/05 now2465
lines. No source/test/default/gate/qualification/threshold change or code-suite
repeat; prior4528-pass root remains source checkpoint, not numerical evidence.
Originals rays-289-design-{1,5}-before.md retained under existing recovery directory;
no cleanup required. Next bounded closed direction-source intake using original
native acquisition/cache/RNG pairing; raw unsupported/nonfinite remains unknown.

Final six local targets/anchors, three old aliases, complete topic/ref/prior
chapter/review/Sources/stable workflow and unchanged source/test bytes passed.

## 290. Bounded Closed Native Direction-Source Intake (2026-11-11)

Resumed clean ee37df3, Python3.12.3/opt/venv/Ruff verified, selected editor same.
Hypothesis: existing two-native-intake/original+closing cache checks can copy closed
direction acquisition/trace/generation while rejecting unsupported/nonfinite raw
generation before native intake. Fixed17/16/30 root fields, 13 generation arrays/
904 words+5 result scalars+4 input scalars plus3 range arrays/320 words; two
metadata copies, canonical binary64 hex<=32chars, existing bounded native context.
No arithmetic, hash, replay, recorder, step/reset, geometry or clock in intake;
all eight flags false, no trig/geometry/source/coverage/error/one-use/admission.
Reuse existing39 wall/cylinder controls plus22 direction controls=61, one existing
fixture acquisition per case, <=2 native intakes/one late mutation, old caps unchanged.
<=3 routine pytest positions: first61/60 s, one necessary repair61/60 s, required
root/300 s; count failure/abort/unknown, retain rays-290-* logs in existing recovery
directory, no spent/protected budgets refunded. Retention/delivery remain next.

First focused invocation failed collection0.81 s: appended direction case-list
had a separating comma, creating unsupported unary +list. Repair ONLY decorator
concatenation; source unchanged, no cases ran. rays-290-focused-1.log retained,
attempt spent, failed-run after-hash comparison not reached. Same61 next under
sole repair position; no cap/assertion changes or protected-budget renewal.

Same61 passed/3566deselected/4.61 s, original39 case expressions conserved;
two native intakes and poisoned hash/recorder/replay/step/reset/geometry/clock
paths bounded, late generation/cache/profile/source/outgoing mutations exercised.
Four source/test hashes stable for pass. Ruff formatted ONLY two touched Python
files; scoped lint/format/whitespace/editor checks clear, AST all prior source/
test definitions and old39 decorator controls conserved. Sole new helper plus
existing matrix changes; no prior defaults/schema changes. Required root
`python -m pytest -q && ruff check . && git diff --check` passed4550/known QDQ
xfail/71warnings/246.39 s, four source/test hashes stable; touched format check
also passed. All3 pytest positions spent, first collection failure retained;
no aborted/refunded/qualified attempt, logs rays-290-{focused-1,focused-2,root-1}
in original recovery directory, no new data/download/dependency/study/hardware.
No C/Arm/sanitizer/board opt-in gates ran for this simulator-only change.
Closed copies reject unsupported/nonfinite observations rather than rewriting
them, retain supplied finite word identities and all eight flags false. This is
NOT trig/geometry/numerical-error/source/coverage/clock/one-use/physical/permission/
admission evidence. Recorder retention and delivery remain absent for direction.
Next fixed-shape typed direction-history validation, then opt-in recorder and
delivered/pending original+closing correspondence; unresolved word ties remain.

## 291. Typed Native Direction-History Validation (2026-11-11)

Begin clean/synchronized2d38c60 under existing routine authority. Hypothesis:
fixed-shape typed direction records can join an existing validated native history
without replay, preserving raw finite supplied generation words and signed zero.
<=8 ordered records/<=8 native records, <=64 pair inspections, per record16
arrays/1224 words+5 result scalars and4 input scalars; schema/flags/native context/
generation input/effective pitch/ray joins, canonical strings<=32chars, no rational
work, hashes/intake/recorder/replay/step/reset/geometry/clocks. Generation trig/
component words are structurally checked ONLY, not recalculated or geometrically
qualified. All eight flags false, no source/numerical/physical/permission/admission.
Existing42 controls conserved plus24 direction=66, <=8 bounded detached synthetic
record copies, one fixture acquisition/two native intakes BEFORE poison hooks.
<=3 routine pytest positions: first66/60 s, one necessary repair66/60 s, root/300 s;
retain rays-291-* logs in original recovery directory, count all failure/abort/
unknown, no budget refunds/new studies/dependencies/data. Next recorder retention.

First66 passed/3585deselected/3.45 s with four source/test hashes stable. Local
review found legacy native source could hit float(None) before mounted rejection;
repair moves that rejection BEFORE expected generation construction. Add one
legacy-source control, reserve67/60 s replaces66/60 s, overall3 positions stays.
Existing42 and new24 controls unchanged; no failed/refunded/qualified attempt or
protected cap increase, same slice's necessary guard+one fixture repair only.

Repaired67 passed/3585deselected/1.85 s, four source/test hashes stable; all new
direction metadata/shape/canonical/nonfinite/native+generation pairing/legacy
cases and signed-zero preservation exercised, unchanged42 expression prefix
conserved by AST. Source all previous definitions conserved; sole new validator
and existing matrix changed. Ruff formatted only two touched Python files;
lint/format/whitespace/editor diagnostics clear. Required root
`python -m pytest -q && ruff check . && git diff --check` passed4575/known QDQ
xfail/71warnings/145.48 s, hashes of diagnostics/rover/protocol/test_sim stable;
touched format check also passed. All3 pytest positions spent, no failed/aborted/
refunded attempt; rays-291-{focused-1,focused-2,root-1} logs retained in original
recovery directory. No downloads/dependencies/studies/task data/hardware/C/Arm/
sanitizer/board opt-in gates for this simulator-only increment. Native history
is independently validated by its existing owner before this companion join;
source-list8 cap is not standalone native-history qualification. Direction words
remain supplied and structurally bounded, NOT recalculated trig/geometry/error/
coverage/source/clock/one-use/physical/permission/admission evidence; all8 flags
false. Synthetic8 record copies are NOT eight measured acquisitions. Next opt-in
recorder-owned direction history, original+closing cache/history/input pairing,
then delivered/pending correspondence. No usable command is admitted.

## 292. Whole Cylinder Checkpoint Archive (2026-11-11)

Clean/synchronized afb6c8e, root982 lines; move whole281–285 before further source
checkpoint growth. Existing archive pattern, no body inline/reference links to
rebase, exactly5 chapter05 references. Preserve originals in existing recovery
directory rays-292-{review-before,design-5-before}.md, no overwritten backups.
First mechanical relocation failed Perl compilation at ambiguous `$1[...]`
interpolation: cmp verified BOTH live docs unchanged, no archive created, clean
worktree, failure retained here/transcript. Only `${1}` interpolation repair;
second guarded relocation succeeded. New273-line archive retains all five
historical bodies/anchors/failures/approvals/spent/unknown/evidence-limit text
exactly with single EOF newline (separator whitespace normalization only).
Root reading map/source bibliography and chapter05 bytes conserved except
intended map/5 reference edits; five local targets/anchors, archive whitespace,
four source/test bytes against HEAD and git diff --check passed. Root712 lines
before this note, no code gate rerun; last source gate4575/known QDQ xfail remains
§291 evidence, not a fresh archival test result. No budgets/studies/qualification
renewed, all8 flags false, no permission/admission. Next opt-in recorder-owned
direction history, then delivered/pending original+closing correspondence.

## 293. Recorder-Owned Native Direction History (2026-11-11)

Begin clean58452f2. Hypothesis: default-off literal include_direction extends
existing native recorder companion ownership/copy/closing checks without replay.
<=8 native+direction records, fixed validated generation fields, retained-tick
trim/idempotent exact repeat, original+closing cache/RNG/producer/profile/history
identity and binding; all8 qualification/admission flags stay false. No additional
geometry/noise/clock during retention, no source/geometry/numerical/physical proof.
Reuse unchanged17-case retention matrix with old wall/cylinder34 controls plus
direction17=51. Per case<=13 geometries/14 reads/10 retentions/20 direction intakes/
40 native intakes/256 bindings/one late mutation. Direction combined includes all
four prior companions, exactly18 native intakes/2 existing clock reads; prior
wall10/cylinder14 combined caps and every old per-case limit stay unchanged.
Three routine pytest positions first51/60s, sole necessary repair51/60s, root/300s;
count failed/aborted/unknown attempts, retain rays-293-* logs in original recovery
directory, no protected budget renewal/new data/studies/dependencies/hardware.
Next delivered/pending matching, not qualification or an admitted command.

First51 passed/3618deselected/4.53s with four source/test hashes stable. Existing
17 case names and two wall/cylinder families conserved; direction original/closing
cache/history/output/owner mutation controls, empty default, literal bool, missing
source, exact duplicate/changed repeat, canonical paired-word rejection before
bindings, retained-tick gap/8-record trim exercised. Combined direction+timing+
selection+wall+cylinder exactly18 native intakes/2 existing clock reads, old10/14
controls unchanged. Ruff formatted ONLY two touched Python files; scoped lint/
format/whitespace/editor diagnostics clear. AST all prior source functions/recorder
methods except init+record_native_tof_source conserved; append-only keyword default
include_direction=False, all old defaults/case names/families unchanged. Internal
ownership/candidate binding includes direction history; not a source qualification
or frozen wire change. Required root `python -m pytest -q && ruff check . && git diff
--check` passed4592/known QDQ xfail/71warnings/145.19s, source/test hashes stable;
touched format check passed. Two of3 routine pytest positions spent, unused
repair reserve is not follow-on authority; no failure/abort/refund. Logs
rays-293-{focused-1,root-1} retained in original recovery directory, no new data/
dependencies/downloads/studies/hardware/C/Arm/sanitizer/board gates. Supplied raw
finite words retained, unsupported/nonfinite unknown; all8 flags false. No trig/
geometry/source/coverage/numerical/error/clock/one-use/physical/permission/admission
qualification, no usable command. Next retained direction delivered/pending joins
and opt-in original+closing publication; current snapshots do not expose direction.

Clarification: the preceding native-control limit means no ADDITIONAL C/Arm/
sanitizer/board opt-in commands beyond the required root gate; it does not claim
default interface/native controls were omitted from that gate.

## 294. Bounded Retained Native Direction Join (2026-11-11)

Begin clean e9666ed. Nearby wall matcher selects one prevalidated record by
epoch/acquisition/delivery identifiers then deep-copies it. Direction join keeps
that precondition (independently validated source/history), explicitly caps the
builtin history at8 and compares exact typed identity words, <=24 inspections.
One detached selected trace; no revalidation/replay/intake/recorder/hash/geometry/
clocks or geometry/source/numerical/physical/permission/admission qualification.
Nine bounded synthetic controls, per fixture one fresh step/two producer reads/
one retention/two direction intakes/four native intakes before poison hooks;
native context/canonical generation prevalidated, negative identity/cap mutations
are join controls ONLY, not accepted source history. Existing fixtures/caps stay.
Three routine pytest positions: first9/60s, sole necessary repair9/60s, root/300s;
retain rays-294-* logs in original recovery directory, count failure/abort/unknown,
no refunds/protected studies/data/dependencies/hardware. All8 flags false, no
usable command. Next opt-in original+closing delivered/pending publication.

Nine passed/3669deselected/0.87s, four source/test hashes stable; nested detachment,
missing/ambiguous/identity/type/cap controls exercised, poison hooks zero. Ruff
formatted only touched test file, both touched Python format/lint/whitespace/
editor checks clear; AST all prior source/test definitions/defaults/cases unchanged.
Required root `python -m pytest -q && ruff check . && git diff --check` passed4601/
known QDQ xfail/71warnings/264.42s, four hashes stable, touched format check passed.
Two of3 pytest positions spent, unused repair reserve NOT follow-on authority;
no failure/abort/refund. Logs rays-294-{focused-1,root-1} retained in existing
recovery directory; no data/downloads/dependencies/studies/hardware or additional
C/Arm/sanitizer/board opt-in commands. Matcher selects prevalidated records only,
not a standalone source/history validator. No sensor/geometry/numerical/coverage/
error/clock/one-use/physical/permission/admission evidence, all8 flags remain false.
Delivered/pending snapshots still lack direction publication; compose original/
closing history and input checks next without treating hash/word joins as proof.

## 295. Delivered/Pending Native Direction Snapshot (2026-11-11)

Begin clean dbcaa15. Hypothesis: append-only literal include_direction=False can
compose the bounded retained join into original+closing delivered/pending native
source/frame/queue checks. Typed native+direction history before hashes and after
all closing traces; history identity/input binding, outgoing typed copies and
original/closing full-word correspondence, <=8 records/192 ray/64 range words,
fixed finite generation fields. No new geometry/intake/recorder/read/replay/clock,
no canonical correction/numerical/source/physical/permission/admission; all8 false.
Reuse unchanged24-case snapshot family old48 controls plusdirection24=72. Same
per-case<=4steps/5reads/3retentions/3geometries/6clocks BEFORE snapshot, <=6 selected
and other-wall/selection/timing/norm matches, 2pending matches/4queue copies/2frame
checks/64bindings/one late mutation, <=2 actual pending records. Default output
keys/options unchanged; optional direction payload only after full closing success.
Three routine pytest positions first72/60s, sole necessary repair72/60s, root/360s
(prior root264.42s observed; fresh assistant-selected wall-time budget, no program
deadline/work/assertion/protected cap change). Count failures/aborts/unknown,
retain rays-295-* logs, no refunds/protected studies/data/dependencies/hardware.
Next supported ray-word prerequisites only, not numerical or physical adoption.

First72 passed/3630deselected/9.30s, four source/test hashes stable; all prior48
controls and24 case names/caps conserved, direction default output keys absent,
held/delivered-only/pending identity, typed/canonical words, detached payloads,
late history/output/owner/arithmetic/selection/timing/pending mutations exercised.
Late over-budget histories rejected before further binding, no payloads on unknown;
native input/frame/queue original+closing checks retained, no extra replay/clock.
Ruff formatted ONLY two touched Python files, lint/format/whitespace/editor clear;
AST all prior definitions/methods except snapshot_native_tof_delivery conserved,
append-only include_direction=False and all old defaults/case names/families.
Required root `python -m pytest -q && ruff check . && git diff --check` passed4625/
known QDQ xfail/71warnings/148.28s, four hashes stable, touched format passed.
Two of3 pytest positions spent, unused repair reserve NOT follow-on authority;
no failed/aborted/refunded attempt. Logs rays-295-{focused-1,root-1} retained in
original recovery directory, no new data/downloads/dependencies/studies/hardware/
additional native/Arm/sanitizer/board opt-in commands. Raw unsupported/nonfinite
generation remains unknown; no corrected observations, all8 flags false. Native
direction capture/intake/typed history/ownership/delivered+pending publication
are now source-word prerequisites, NOT uniform trig/error/coverage/clock/one-use/
physical clearance/source/permission/admission qualification. Matching words and
squared-norm correspondence do not prove ray geometry; equal-value/different-word
ties remain unresolved. Next bounded supplied-word sensor-component product
discrepancies using unchanged exact arithmetic limits; no physical/numerical
bounds or qualification adopted, no learned/board/study work reopened.

## 296. Supplied-Word Native Direction Products (2026-11-11)

Begin clean5037cd3. Existing projection residual helper establishes canonical
word/finite-operand/unknown-nonfinite-observation/exact-rational pattern. Direction
helper reports observed forward/left minus supplied elevation cosine*azimuth
cosine/sine, six64-word builtin tuples/384 decodes,128 entries, <=384 value
conversions/256 binary operations/256 independent oracle operations, <=32char
canonical words/unchanged1..4096bit ceiling. One actual cold generation only in
actual fixture, no geometry/intake/read/retention/replay/trig/clock/hash in helper.
Raw +/-inf observations remain unknown/unchanged, NaN/unsupported operands reject;
signed words retained, exact value ratios do NOT resolve different-word zero ties.
22 synthetic controls, existing helper/tests/defaults unchanged; no primitive/FMA/
trig/uniform-error/source/geometry/coverage/clock/physical/permission/admission
qualification, all8 flags false. Three routine pytest positions first22/60s,
sole necessary repair22/60s, required root/360s. Count failures/aborts/unknown,
retain rays-296-* logs, no refund/protected data/studies/dependencies/hardware.
Next compose supported product reports against original+closing retained traces,
without correcting observed words or adopting numerical/physical bounds.

First22 passed/3702deselected/0.52s, four source/test hashes stable. Ruff formatted
only two touched Python files then I001 rejected missing standard/local import
blank line in new test. Repair ONLY import separation, no assertion/source change;
lint pipeline stopped before format/whitespace/AST commands, no pytest consumed
or successful AST check inferred. Same scoped style/conservation checks next.

Import-only repair passed scoped lint/format/whitespace/AST; all prior source/test
definitions/defaults/cases conserved, sole product helper/new22-control function
added. Editor diagnostics clear. Actual cold generation, rounded mismatch,
underflow/subnormal/large finite, signed-zero words, +/-inf unknown observations,
canonical/builtin/shape/word/bit rejection and16bit work-limit controls exercised;
<=384 value/256 binary/256 oracle caps, no forbidden operations. Required root
`python -m pytest -q && ruff check . && git diff --check` passed4647/known QDQ
xfail/71warnings/153.99s, four source/test hashes stable, touched format passed.
Two of3 pytest positions spent, no test failure/abort/refund; failed I001 style
pipeline retained above, unused test reserve NOT follow-on authority. Logs
rays-296-{focused-1,root-1} retained in original recovery directory, no new data/
downloads/dependencies/studies/hardware/additional native/Arm/sanitizer/board
opt-in commands. Supplied operands/observations remain unchanged; NaN/unsupported
reject, +/-inf observation raw/unknown, equal-value/different-word ties unresolved.
All8 flags false, no geometry/trig/primitive/FMA/uniform-error/source/coverage/
clock/one-use/physical/permission/admission qualification. Standalone product
diagnostic NOT yet paired to retained delivery; next original+closing delivered/
pending composition without correcting words or adopting numerical/physical bounds.

## 297. Matched Native Direction Product Reports (2026-11-11)

Begin clean719cc90. Hypothesis: append-only literal product-report option requiring
include_direction=True composes the standalone bounded product helper from original
and closing retained generation words, with typed copies/input/history/ID/binding
checks and no corrected upstream values. Strengthen native-history prevalidation
before closing direction parse and final companion checks; missing native inputs
after closing frame callback must be unknown, not unchecked lookup. All8 false,
no geometry/trig/primitive/FMA/uniform-error/source/coverage/clock/physical/
permission/admission adoption. Existing24-case matrix72 controls conserved plus
new direction-products24=96, three option/dependency controls=99. Old per-case
4steps/5reads/3retentions/3geometries/6matches/2pending/4queue/2frame/64bindings/
one late-mutation caps unchanged; product<=6calls/2304value/1536binary and independent
oracle<=768ops, 4096bit ceiling unchanged. Count product arithmetic only while
helper active; existing norm controls/caps remain. Original/closing reports have
<=128 entries/source; no intake/replay/trig/geometry/clock during snapshot.
Three routine pytest positions first99/60s, sole necessary repair99/60s, root/360s;
retain rays-297-* logs, count failed/aborted/unknown attempts, no refunds/protected
data/studies/dependencies/hardware. Next source-word prerequisites only, no bounds.

First99 passed/3652deselected/13.26s with four hashes stable: existing72 modes
and24 names/caps conserved, new product mode reports original+closing delivered/
pending128-entry observations with exact independent oracles, mutated sensor
product/outgoing diagnostic/late missing native input rejected. Append-only literal
product flag/dependency three controls passed; old modes leave product keys absent.
Product<=6calls/2304values/1536binary, oracle<=768 operations; old matching/digest/
frame/queue/norm counters unchanged, no forbidden replay/intake/clock. Ruff formatted
only two touched Python files; lint/format/whitespace/editor clear. AST all prior
source methods except snapshot_native_tof_delivery and old test definitions except
existing snapshot matrix conserved; old defaults/case names/modes unchanged.
Required root `python -m pytest -q && ruff check . && git diff --check` passed4674/
known QDQ xfail/71warnings/162.51s, four source/test hashes stable; touched format
passed. Two of3 pytest positions spent, no failure/abort/refund; unused repair
reserve NOT follow-on authority. Logs rays-297-{focused-1,root-1} retained in
original recovery directory, no data/downloads/dependencies/studies/hardware or
additional native/Arm/sanitizer/board opt-in commands. Product reports paired to
actual retained generation words, source identities and closing trace checks, not
corrected or qualified. Unsupported/nonfinite raw source stays unknown, all8 flags
false; equal-value/different-word ties unresolved. No trig/geometry/primitive/FMA/
uniform-error/source/coverage/clock/one-use/physical/permission/admission proof.
Next bounded supplied-word pitch-rotation combined-expression discrepancies, then
matched composition only as supported; no numerical/physical bounds adopted.

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
[chapter-review-21]: docs/review/281-285.md
[native-tof-ray-design]: docs/design/07-data-and-distillation-design-01.md#native-tof-ray-generation-prerequisites-2026-11-11
