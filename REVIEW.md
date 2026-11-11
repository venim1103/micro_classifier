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
- [Checkpoints 286-290][chapter-review-22]
- [Checkpoints 291-295][chapter-review-23]

Checkpoints 296 onward and the source bibliography remain below.
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

## 298. Supplied-Word Native Direction Pitch Expressions (2026-11-11)

Begin clean acce2c9. Local hypothesis: captured pitch cosine/sine and sensor
forward/up words suffice for exact combined forward=c*f+s*u and up=c*u-s*f
discrepancies against observed pitched words, not isolated multiply/add/FMA/trig
or geometry proof. Reuse bounded rational owner and canonical word guards;
two scalar/four64-word tuples=258 decodes/values, <=512binary/128entries,
4096bit ceiling unchanged. First cheap check27 synthetic controls incl one cold
generation capture before poison, exact Fraction oracle<=512ops, cancellation/
rounded/subnormal/signedzero/largefinite/raw +/-inf unknown and preflight/type/
shape/canonical/budget guards. No replay/intake/hash/recorder/step/reset/trig/clock
in helper; all8 flags false, supplied words retained, no corrected outputs.
Three routine pytest positions first27/60s, sole necessary repair27/60s, root/360s;
failures/aborts/unknowns spent, no refund/protected experiment renewal. Retain
rays-298-* in original recovery directory; no dependencies/data/studies/hardware.
Exit verified standalone report only, then compatible matched composition;
raw unsupported/nonfinite source unknown, no bounds or word-tie resolution.

First focused collection failed0.41s with IndentationError: a function jump plus
repeated decorator replacement landed at old cylinder-selection parameter block,
not the intended projection boundary; no cases ran, after-hash pipeline not reached.
Diff diagnosed exact displaced old names; restore only original selection decorator,
keep additive pitch test at that boundary, source helper unchanged. First position
spent; sole reserved same27 focused repair next, no refund or cap relaxation.

Same27 passed/3751deselected/0.55s, four hashes stable. Scoped Ruff format/lint/
format-check/whitespace/editor clear; AST exact conservation of every previous
source/test top-level node, including all old selection names/decorators. First
root failed6/4695passed/known QDQ xfail/71warnings/307.06s: unchanged cylinder
selection missing_pending/flag/dependency/late_side_mask/late_side_minimum/
late_top_mask failed during setup retention/read with producer/recorder/source-
file changes; pitch controls passed. One explicit source-files mismatch guard,
others compound original/closing identity/binding guards; not pitch arithmetic
failure. Failed && pipeline did NOT run closing hash/lint/format/whitespace.
Post-failure source/test intact and old ASTs still exact; diagnostic/test mtimes
12:01:31.849763/12:01:32.087415 lie within log birth11:58:55.667651 to
modify12:04:03.025048 UTC interval. Supports overlapping writes, NOT writer,
precise cause or qualified clock evidence. No source/old assertion repair or
tolerance/work/fixture/safety relaxation. Background terminal notification exit1
recovered; one output retrieval found already-cleaned ID, no live job or retry.
All original3 pytest positions spent incl collection/root failures, no refunds.
Fresh necessary stable-source revalidation under standing routine authority:
exact six failed controls<=60s once, then required root<=360s once, two added
positions only, same source/test unchanged, serial/no concurrent editor/format/
source tools while pytest. Retain rays-298-failed-controls-1/root-2 logs and
original failures; no protected study/audit/model/dependency/hardware renewal.

Stable-source six setup controls passed/3772deselected/1.40s, then required root
`python -m pytest -q && ruff check . && git diff --check` passed4701/known QDQ
xfail/71warnings/183.06s; four hashes stable and touched format-check passed.
All five pytest positions spent, both failures retained, no abort/refund/cap or
old-definition/assertion change. Logs rays-298-{focused-1,focused-2,root-1,
failed-controls-1,root-2} kept in original recovery directory, no new data/study/
dependency/hardware/additional native/Arm/sanitizer/board opt-in commands.
Standalone128-entry pitch report only; all8 false, raw +/-inf unknown, no corrected
words/trig/primitive/FMA/uniform-error/geometry/source/coverage/clock/one-use/
physical/permission/admission proof. Next archive intact286-290 before further
root growth, then original+closing retained delivered/pending pitch composition.

## 299. Intact Ray Checkpoint Archival (2026-11-11)

Begin clean167bf77/root998lines. One guarded mechanical move: complete286-290
sections to linked199-line archive, four chapter01 references rebased and one
root-owned ray-design definition copied/rebased for289; root map now291 onward.
Pre-execution utility syntax passed; literal reading-map spaces tightened before
execution, same syntax/move/conservation/whitespace passed, no migration failure.
Complete headings/bodies/failures/approvals/spent ledgers conserved, only separator
EOF whitespace normalized. Root806/chapter01=2419 before this note. Original
rays-299-review-before.md/design-1-before.md and one-shot archive-review-299.pl
retained in original recovery directory; relocation DONE, do not rerun.
No source/test/default/qualification/threshold change or code-suite rerun;
independent exact five bodies/remaining review/Sources/design bytes, four inbound
anchors/copied ray target and unchanged source/test bytes passed; whitespace clear.
last4701-pass gate remains source evidence only. Next bounded original+closing
retained delivered/pending pitch-expression composition, all8 false/no bounds.

## 300. Matched Native Direction Pitch Reports (2026-11-11)

Begin cleanf780917. Hypothesis: append-only literal default-off pitch option,
requiring include_direction=True, composes standalone supplied-word pitch helper
on original+closing retained delivered/pending generation words and IDs; closing
reports/history/input/frame/queue/owner/output checks precede publication. All8
false, no trig/FMA/uniform-error/geometry/source/coverage/clock/physical/admission.
Existing24names/96snapshot+3dependency controls conserved, new pitch24+3=126;
combined new mode also selects product report. Old caps/defaults preserved:
4steps/5reads/3retentions/3geometries/6matches/2pending/4queue/2frame/64bindings,
one late mutation. Separate pitch<=6helpers/1548values/3072binary/1536oracle;
product old6/2304/1536/768 unchanged, norm forwarded separately, 4096bits unchanged.
New mutations target observed pitched_up, scalar pitch_cosine and outgoing report;
no replay/intake/trig/recorder/step/reset/clock in snapshot. Pylance no resolved
method callers, not static compatibility proof; runtime controls/default-prefix
conservation discriminate. Fresh3 routine pytest positions first126/60s, sole
necessary repair126/60s, required root/360s; failures/aborts/unknown spent, no
refund/protected study/model/dependency/hardware/audit renewal. Retain rays-300-*
logs, serial pytest/no simultaneous source/formatter/editor tools. Exit matched
pitch diagnostics only, then remaining supported supplied-word yaw prerequisites.

First126 passed/3679deselected/18.89s, four hashes stable; old96 modes/24 names/
three dependencies preserved, new pitch24/three dependency controls and combined
product+pitch report validated by independent exact oracles. Delivered/pending/
held/default word identities, detached outputs, scalar cosine/observed pitched_up/
outgoing-report mutations and unknown/no-payload rejection exercised, no extra
source reads/trig/recorder/clocks. Separate pitch1548values/3072binary/1536oracle
and old product/norm/call/binding/queue/frame caps unchanged. Ruff formatted only
two touched Python files; lint/format/whitespace/editor/AST old definitions and
methods/default-prefix/decorators/caps conserved. Required root
`python -m pytest -q && ruff check . && git diff --check` passed4728/known QDQ
xfail/71warnings/186.11s; four hashes stable, touched format-check passed. Twoof3
pytest positions spent/no failure/abort/refund, unused repair NOT follow-on
authority. Logs rays-300-{focused-1,root-1} retained in original recovery directory.
No data/studies/models/dependencies/hardware/additional native/Arm/sanitizer/board
opt-in commands; all8 false, unsupported/nonfinite raw source unknown, supplied
word ties unresolved, no corrected values or geometry/trig/primitive/FMA/uniform-
error/source/coverage/clock/one-use/physical/permission/admission proof. Scoped
documentation checker first rejected recorded "126 passed" through its own
contradictory literal matcher; corrected checker requires actual count/time
strings, same scoped history/reference/byte/whitespace check passed, no
source/assertion/cap change or pytest position spent. Next
bounded supplied-word yaw-expression discrepancies, then matched composition.

## 301. Supplied-Word Native Direction Yaw Expressions (2026-11-11)

Begin clean6296742. Hypothesis from actual tof_directions owner: two horizontal
unrounded expressions c*f-s*l and s*f+c*l using supplied yaw cosine/sine,
pitched_forward/sensor_left and observed world x/y words. Add standalone helper,
no source/predecessor/trig/geometry/primitive/FMA/uniform error qualification or
up passthrough claim. Same literal opt-in, canonical builtin scalars/four64-word
tuples <=32chars, finite operands/observed +/-inf unknown, early preflight before
rational work; unchanged1..4096bits/258decode-values/512binary/128entries. Reuse
old27 pitch cases with separate yaw mode=54, old names/caps/defaults retained;
one actual direction generation per actual mode, forbidden intake/read/hash/
recorder/step/reset/trig/replay/clock, independent <=512 Fraction oracle. All8
false, no data/model/study/dependency/hardware/extra native opt-in/audit renewal.
Fresh3 routine pytest positions first54/60s, sole necessary repair54/60s, root/
360s; failures/aborts/unknown spent not refunded, retain rays-301-* logs, serial
pytest/no concurrent formatter/source/editor tools. Exit standalone horizontal
yaw only, next original+closing matched retained composition as supported.

First54 passed/3778deselected/4.68s; four hashes stable, old27 pitch controls,
exact supplied operands/residuals, raw +/-inf unknowns/cancellation, malformed
preflight and hard arithmetic/forbidden-call counters passed. Only new yaw
helper and existing pitch-test mode changed; old source/defaults/test names/
decorator/parameter prefix conserved in AST. Touched format/lint/whitespace/
editor clear, Pylance yaw definition+one test selection only; changed pytest
signature no resolved callers, not static compatibility proof.

First required root FAILED2/4753passed/known QDQ xfail/71warnings/188.81s:
unchanged wall_cylinder_boundary_snapshot late_cylinder/malformed fail in setup
retention producer/recorder compound closing guard, before yaw reporting. Current
source/test parse and every prior owner/boundary AST exact. Reused shell before
value equals current four hashes, not a persisted start record or proof of
in-run stability; failed pipeline did not reach closing hashes/lint/format/diff.
diagnostics/test mtimes12:45:11.607112/12:45:11.751112 inside root log
birth12:43:44.299127--modify12:46:53.362060 UTC support possible overlapping
rewrite, NOT writer/cause/clock/source qualification; exact failed guard limb
unknown. Preserve failed root, no damaged file recovery/source/cap/assertion fix.
Two original pytest positions spent. Diagnose then reallocate unused routine
54-repair position to ONLY these two controls/60s and add ONE necessary root
revalidation/360s under standing routine authority: fresh finite two-step
recovery, four total positions if complete, no old refund/protected renewal.
Retain rays-301-failed-controls-1/root-2; serialize, no source/formatter/editor
tools during either check, unchanged fixtures/assertions/limits/all8 false.

Recovery exact2 passed/0.92s then required root
`python -m pytest -q && ruff check . && git diff --check` passed4755/known QDQ
xfail/71warnings/175.44s; four hashes stable for both, touched format-check passed.
All four positions spent, failed root preserved, no abort/refund/tolerance/cap/
source/guard change; passing recovery does not establish the failed guard limb,
writer/cause, in-run source immutability or clocks. Logs rays-301-focused-1,
root-1,failed-controls-1,root-2 retained in original recovery directory; no extra
data/study/model/dependency/hardware/additional native/Arm/sanitizer/board opt-in
or general audit. Helper remains horizontal supplied-word expression diagnostics
only, no trig/geometry/up-passthrough/primitive/FMA/uniform-error/source/coverage/
clock/one-use/physical/permission/admission proof or usable command, all8 false.
Next matched yaw reports against original+closing retained delivered/pending
cosine/sine/pitched_forward/sensor_left/world x/y words and typed identities.

## 302. Matched Native Direction Yaw Reports (2026-11-11)

Begin clean9e6eeab. Hypothesis: append-only literal default-off yaw report option
requires include_direction=True; compose standalone yaw on original+closing
retained delivered/pending scalar/array words and typed IDs, closed x/y strided
slices only after native/direction preflight, final history/owner/input/frame/
queue/copy/report-binding checks before publish. No up-passthrough/primitive/
FMA/trig/uniform-error/geometry/source/coverage/clock/one-use/admission; all8 false.
Preserve old120snapshot+6dependency controls, new yaw24+3=153; combined yaw also
product+pitch+norm with separate old counters. Old4steps/5reads/3retentions/
3geometries/6matches/2pending/4queue/2frame/64bindings/one late mutation unchanged;
yaw separate6helpers/1548values/3072binary/1536oracle, same1..4096bits. Scalar
yaw_cosine, final world-x and outgoing-yaw report late mutations discriminate;
unknown omits every payload/default keys unchanged/detached. Pylance no resolved
method callers NOT static compatibility proof. Fresh3 routine pytest positions
first153/60s, sole necessary repair153/60s, root360s; count failures/aborts/unknown
as spent, no refund or old reserved position/protected renewal. Logs rays-302-*
retained original recovery directory; serial no source/editor/formatter tools
during checks. Exit matched horizontal yaw only, then bounded final-up word
passthrough prerequisites as supported, never ray geometry/error qualification.

First153 passed/3706deselected/18.76s, four hashes stable; old120 modes/24names/
six dependencies preserved, new yaw24+3 including combined product/pitch/yaw/
norm and separate counters, supplied-word Fraction oracles/IDs/detachment,
held/delivered-only/default and late world-x/scalar/outgoing-report rejection
passed. Old source methods/default prefix/test names/case decorators/modes/
dependency prefix conserved in AST, touched format/lint/whitespace/editor clear.
Required root `python -m pytest -q && ruff check . && git diff --check`
passed4782/known QDQ xfail/71warnings/152.91s; four hashes stable, touched
format-check passed. Twoof3 pytest positions spent/no failure/abort/refund,
unused repair NOT follow-on authority. Logs rays-302-{focused-1,root-1} retained
in original recovery directory, no source/guard/tolerance/cap relaxation or
data/study/model/dependency/hardware/additional native/Arm/sanitizer/board opt-in/
general audit; all8 false, unsupported/nonfinite source unknown, supplied ties
unresolved, no corrected values/up-passthrough/primitive/FMA/trig/uniform-error/
geometry/source/coverage/clock/one-use/physical/permission/admission proof or
usable command. Next archive whole291--295 with links/history/limits intact
before root growth, then bounded final-up word-copy prerequisite as supported.

## 303. Intact Direction Checkpoint Archival (2026-11-11)

Clean/synchronized e8f482e, root963lines. Guarded one-shot mechanical move of
whole291--295 to185-line archive, exact five bodies/headings/failures/approvals/
spent/unknown/limits; separator EOF normalized only, no body links to rebase.
Four chapter01 inbound references and new root map target/definition rebased,
all five historical anchors retained; remaining root/Sources/design bytes exact
except intended map/four references. Preserve rays-303-{review-before,
design-1-before}.md and archive-review-303.pl in original recovery directory,
no overwritten backups. `perl -c` then sole guarded relocation and independent
body/map/bibliography/design/source-byte conservation passed; four targets/
anchors/root-map/no-stale-links and git diff --check passed. Root781lines before
this note/chapter01=2468, four source/test files byte-identical to checkpoint.
No code suite rerun/fixture/query/data/model/study/dependency/hardware/additional
native/Arm/sanitizer/board/audit commands, no budgets/refunds/qualification
renewed; last4782-pass gate remains source evidence only, all8 false/no admission.
Migration DONE, do not repeat. Next bounded final-up supplied-word copy
correspondence, then matched original+closing retained composition as supported,
not ray geometry/trig/uniform-error/source/clock/one-use/physical qualification.

## 304. Supplied-Word Native Direction Up Copies (2026-11-11)

Begin cleanf0a88eb. Hypothesis from actual stack producer: pitched_up copied to
world z; standalone canonical two64-word builtin tuple checker, <=128decodes/
64strict word comparisons/64finite value comparisons, <=32chars, no rational.
Report raw exact words separately from three-valued copy correspondence: finite
identical words match, finite differing values mismatch, equal-value/different-
word signed-zero ties and any +/-inf operands/observations unknown even when raw
words match. Unsupported/NaN/overbudget preflight rejects before comparisons.
All8 flags false/no trig/geometry/error/source/coverage/clock/one-use/physical/
permission/admission claim. New25 bounded controls in existing test file with
existing fixture, one actual generation per actual case then poison intake/read/
hash/recorder/step/reset/trig/replay/clock/rational; old tests/defaults untouched.
Fresh3 routine pytest positions first25/60s, sole necessary repair25/60s, root/
360s; count failure/abort/unknown spent, no refund/protected renewal. Retain
rays-304-* in original recovery directory, serial no source/formatter/editor
tools during tests. Exit standalone word-copy only, next retained original+
closing delivered/pending binding as supported, not qualified ray geometry.

First25 passed/3859deselected/3.67s, four hashes stable. Actual captured up/z,
finite matches/mismatches, both signed-zero tie orders, matching negative zero,
subnormal/negative/maxfinite and source/observed/same/opposed infinities exercised;
raw identical inf still unknown. Canonical/type/shape/NaN/word-budget preflight
rejected before comparisons; <=64 strict comparisons and forbidden calls zero,
inputs/output detached. Every old definition/import/default/decorator/test/case
conserved in AST, only helper+new test added; touched format/lint/whitespace/
editor clear. Pylance two helper callers, normal True compatible and intentional
literal1 negative opt-in incompatible at test line29868, expected guard fixture
not a compatibility repair or static all-caller pass.
Required root `python -m pytest -q && ruff check . && git diff --check`
passed4807/known QDQ xfail/71warnings/153.07s; four hashes stable, touched
format-check passed. Twoof3 pytest positions spent/no failure/abort/refund,
unused repair NOT follow-on authority; logs rays-304-{focused-1,root-1} retained
in original recovery directory. No source/guard/tolerance/cap relaxation/data/
study/model/dependency/hardware/additional native/Arm/sanitizer/board opt-in/
general audit, no corrected upstream values/trig/geometry/uniform-error/source/
coverage/clock/one-use/physical/permission/admission proof or usable command,
all8 flags false. Next original+closing retained delivered/pending final-up
word-copy composition with default-off include_direction dependency.

## 305. Matched Native Direction Up-Copy Reports (2026-11-11)

Begin clean746fd94. Hypothesis: append-only literal default-off final-up copy
option requires include_direction=True; original+closing typed retained
delivered/pending pitched_up/world-z words and IDs to existing helper, final
history/input/frame/queue/owner/copied-report binding before publication.
Same unknown/nonfinite/equal-value-different-word limits/all8 false, no
trig/geometry/error/source/coverage/clock/one-use/physical/permission/admission.
Preserve old144snapshot+9dependency controls; new up24+3=180, combined all
product/pitch/yaw/up/norm with old independent arithmetic counters/caps.
Same4steps/5reads/3retentions/3geometries/6matches/2pending/4queue/2frame/
64bindings/one late mutation; <=6up helpers/384strict comparisons/768decodes,
no up rational work, old1..4096bit guard unchanged for arithmetic families.
Late pitched-up/final-z/outgoing-up mutations, default keys absent/unknown
omits every payload/detached copies. Pylance no resolved method callers NOT
static compatibility proof. Fresh3 pytest positions first180/60s, sole
necessary repair180/60s, root360s; count failed/aborted/unknown spent, no
refund/protected renewal. Retain rays-305-* original recovery directory,
serial no source/formatter/editor tools during tests. Exit matched word-copy
only; reassess supported ray-to-ToF source prerequisites, all qualification false.

First180 FAILED5/175passed/3731deselected/24.96s: new test mode flag named up
was shadowed by the pre-existing pitch oracle's Fraction local up, triggering
up payload assertions in pitch copy/held/delivered-only/combined and yaw combined
modes. New up mode itself and source implementation were not failing. Repair
ONLY introduced bool flag to up_copy, retaining every old oracle/case/assertion/
helper/recorder/counter/cap. Failed pipeline did not reach closing hashes; failed
log retained, first position spent not refunded. Same reserved180/60s check next,
no scope or protected-budget change.

Repaired180 passed/3731deselected/21.33s, four hashes stable. Old144 modes/
24names/nine dependencies and every old oracle/cap preserved; new up24+3 and
combined product/pitch/yaw/up/norm validated with separate counters, actual
up/z words/IDs/zero mismatch+unknown counts, delivered-only/held/default,
late pitched-up/final-z/outgoing flags and detached/unknown-no-payload checks.
AST all old imports/definitions/methods/default keyword prefix/case decorators/
mode/dependency prefixes conserved except planned snapshot/two matrices;
touched format/lint/whitespace/editor clear. Required root
`python -m pytest -q && ruff check . && git diff --check` passed4834/known QDQ
xfail/71warnings/156.02s; four hashes stable, touched format-check passed.
All3 pytest positions spent, first5-failure log retained, no abort/refund/
source/guard/tolerance/cap repair, only new test bool rename. Logs rays-305-
{focused-1,focused-2,root-1} retained original recovery directory. All8 false;
no data/studies/models/dependencies/hardware/additional native/Arm/sanitizer/
board opt-in/audit, no corrected values/trig/geometry/uniform-error/source/
coverage/clock/one-use/physical/permission/admission proof or usable command.
Reassessment: floor guarded division already has standalone+matched reports,
do not duplicate. Next bounded cold return-postprocessing capture at actual
_sample owner: noise/dropout draws, masks, clip/select/store words with no extra
RNG calls/replay or noise-law/error/coverage/timing adoption; source-only first.

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
[chapter-review-22]: docs/review/286-290.md
[chapter-review-23]: docs/review/291-295.md
[native-tof-ray-design]: docs/design/07-data-and-distillation-design-01.md#native-tof-ray-generation-prerequisites-2026-11-11
