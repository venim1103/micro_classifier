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
- [Checkpoints 296-300][chapter-review-24]
- [Checkpoints 301-305][chapter-review-25]

Checkpoints 306 onward and the source bibliography remain below.
[Cloud harness handoff and restart prompt (§311)][cloud-harness-handoff]
identify the current checkpoint and next bounded work.
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

## 306. Cold Native ToF Return-Postprocessing Capture (2026-11-11)

Begin clean7b50dd3. Hypothesis at _sample owner: append-only postprocessing_source
None keeps exact old sampling branch; opt-in empty builtin dict/native-source/
actual-owner/supported finite profile preflight before clock/geometry/RNG,
retain actual existing noise+dropout draws and raw/noisy/masks/clip/select/float32
store arrays without extra RNG calls/replay or noise-law/error/coverage/timing
adoption. Nine8x8 arrays/sevenfloat arrays448values/twobool128/576array words,
four profile fields; raw unsupported/nonfinite words remain observations not
qualification, all8 flags false. New24 controls in existing test file, <=2sample/
2geometry/2normal/2random/4existing clocks per fixture; two identical seeded-owner
branches/independent operand and uint64/uint32 word parity/masks/pending/RNG-state
oracles, injected synthetic draws/nonfinite words not task data or noise model.
Old source/tests/defaults unchanged outside _sample; Pylance all7 old callers
compatible before new signature. Fresh3 pytest positions first24/60s, sole
necessary repair24/60s, root360s; failures/aborts/unknown spent not refunded,
retain returns-306-* in original recovery directory; serial no source/editor/
formatter tools during tests. Exit COLD source only, no new acquisition/recorder/
delivery/admission/actuation. Next close supported cold-source boundaries before
later independently scoped fresh acquisition ownership.

First24 collection FAILED/0.23s: test insertion at adjacent repeated decorator
boundary left stray empty direction-source header and replaced range-test
decorator. Restore ONLY exact checkpoint17-case range decorator and remove
stray header; retain new cold test and source implementation unchanged. Original
direction-source body preserved. Failed pipeline did not reach closing hashes;
first position spent/log retained not refunded. Same reserved24/60s next, no
assertion/resource/protected cap change.

Repaired24 PASS/9.47s, four source/test hashes stable; root4858 PASS/known QDQ
xfail/71warnings/233.52s, four hashes stable, root Ruff/touched format/whitespace
PASS. All3 initial positions spent. Formatting touched only rover/test; AST
all old tests/cases/imports/methods unchanged outside _sample, old keyword prefix
and three default sampling operations exact. Editor clear; post-signature8
callers/7 compatible plus intentional wrong-owner rejection fixture incompatible.

Narrow diff review exposes missing receiver-alias guard: shared postprocessing
dict can overwrite native/selection/wall/cylinder/direction packet at update.
Add ONLY five-way identity preflight and5 zero-work negative controls, conserve
old24 cases/caps/default behavior. Necessary adjacent source repair plan TWO
fresh routine positions: exact5 aliases/60s, root360s; count failures/aborts/unknown,
no initial-attempt refund/protected renewal/assertion/resource relaxation.
Retain returns-306-aliases-focused-1/root-2; no code suite repeat for documentation.

Exact5 aliases PASS/10.86s and root4863 PASS/known QDQ xfail/71warnings/173.36s;
four hashes stable in each, root Ruff/touched format/whitespace/editor PASS.
All5 pytest positions spent, initial collection failure retained, no abort/refund
or protected renewal. Old tests/cases exact; only new29-case test, same per-case
caps. Cold contract placed in existing chapter02 because ray chapter01 is full;
new map/reference only, prior contracts/requirements/historical records preserved.
No additional native/Arm/sanitizer/board commands beyond required default interface
controls, no dependencies/downloads/model/study/data/actuation/admission work.
No logs/artifacts removed; original recovery directory retains all returns-306-*.
Next bounded supported cold-source closure before independently scoped fresh
acquisition/cache ownership, then intake/retention/delivery only as evidence permits.

## 307. Fresh Native ToF Postprocessing Acquisition Pairing (2026-11-11)

Begin clean61e4151. Hypothesis: append-only literal step flagFalse and sensor
receiverNone route separate cold packet ONLY on actual fresh _sample; acquisition
cache pairs exact native cache/RNG/tick/delivery with existing stored words/mask,
default/held/reset clear, rejected preflight retains prior state before work.
Reuse finite sampling-profile predicate in cold and step paths, no default
operation/RNG/cadence/clock changes. Add postprocessing16 to existing48 acquisition
matrix; three existing invalid-profile cold controls also assert zero-work step
rejection. Same3geometry/1selected/1selection/2existing clocks per acquisition
fixture, <=2 cold calls plus1 zero-work step for three invalid profiles; no extra
fixture/data/model/hardware or admission. Legacy cold/postprocessing supported;
old mounted-only wall/cylinder/direction controls unchanged.
Fresh3 routine pytest positions: first19/60s, sole necessary repair19/60s,
root360s; count failures/aborts/unknown spent, no old-position refund/protected
renewal. Retain returns-307-* original recovery directory, serial tests without
source/editor/formatter tools. Exit acquisition-only/all8false, not typed intake,
recorder/delivery/noise-law/numerical/physical/clock/one-use/admission qualification.

Focused19 PASS/4.75s; root4879 PASS/known QDQ xfail/71warnings/214.43s. Four
source/test hashes stable in both, root Ruff/touched format/whitespace/editor PASS;
only test file formatted. AST exact old methods/imports outside reset/update/
sample/step, old keyword prefixes/None+False defaults/default sampling branch,
old16-case48-mode acquisition and29-case cold names conserved. Shared finite
predicate replaces only duplicate opt-in check; cold cases3 strengthen step
preflight without extra work. Post-signature sensor8/8compatible; sample9 with
one intentional wrong-owner fixture incompatible, step40 with same2 old literal1
motion-receipt rejection fixtures incompatible. Twoof3 pytest positions spent,
no failure/abort/refund; unused repair reserve not follow-on authority. All8flags
false/no usable command. No additional native/Arm/sanitizer/board opt-in command,
dependencies/downloads/model/study/task-data/actuation or noise-law adoption.
Logs retained returns-307-* original recovery directory; no artifact cleanup.
Next whole296-300 archival before further root growth, then bounded closed
postprocessing intake using original/closing cache/native/RNG/profile/pose/
inputs/stored words/masks, unsupported/nonfinite remains unknown.

Documentation checker FAILED literal "no extra work" while record states
"without extra work". Correct matcher only to actual wording; same strict
history/contracts/stable-workflow/reference/anchor/ledger check next. No source,
assertion/resource change or pytest position spent; code gate not rerun.

## 308. Intact Direction Product/Pitch Checkpoint Archival (2026-11-11)

Begin cleancd89b2a/root989. Finite documentation-only plan: one guarded move of
whole296-300 to five-section archive, four chapter01 inbound links and root map
rebased; preserve exact headings/bodies/failures/approvals/spent ledgers/limits.
Reuse prior guarded archival utility pattern, syntax check before sole migration;
retain before snapshots and new one-shot utility in original recovery directory.
Independent byte/heading/local-reference/anchor/remaining-map/Sources/source-test
conservation and whitespace checks, no code-suite rerun or source/qualification/
budget renewal. Next bounded closed postprocessing intake, not floor-division
duplication, numerical/noise-law/source/clock/admission adoption or protected work.

Syntax/sole guarded migration/independent exact archive and remaining root/Sources/
chapter01 bytes PASS; all5 historical headings/anchors and4 inbound links retained,
only separator EOF normalization. Root796/archive208 before result note;
chapter01 stays2500, stable AGENTS/DESIGN/chapter02/source/test bytes unchanged.
Whitespace PASS; no failure, code-suite rerun, source/default/threshold/flag change
or attempt/protected qualification renewal. Original returns-308-review-before/
design-1-before snapshots and archive-review-308.pl kept in recovery directory;
migration DONE, never rerun. No artifacts deleted or new data/model/dependency/
hardware work. Last4879-pass source gate remains prior source evidence, all8false.
Next bounded closed postprocessing intake and original/closing ownership joins.

## 309. Bounded Closed Native ToF Postprocessing Intake (2026-11-11)

Begin cleanbfc50e7. Hypothesis: closed17-key acquisition/21-key trace/4-key inputs,
two metadata snapshots around two existing native intakes and detached outgoing
copy suffice for typed source prerequisites, not noise-law/numerical qualification.
Six64 finite float64 arrays encode canonical hex, stored64 float32 values retain
uint32 words, two64 literal boolean masks; original/closing cache/native/RNG/
profile/pose/input/pre-noise/stored-word/mask joins, no replay/extra draws/clock/
hash/read/retention. Raw unsupported/nonfinite raises unknown-path ValueError;
all8 flags false, no internal mask/arithmetic/noise-law/physical/coverage/clock/
one-use/admission adoption. Extend existing61 intake controls with26 postprocessing
cases including noisy/legacy positives, detached words and early/late mutation
rejection; old family names/caps unchanged. Per new fixture1 existing fresh step/
geometry before poison, <=2 native intakes/two metadata snapshots (768float-word
encodes/128store words/256mask bools), no source/recorder/RNG/clock work in intake.
Fresh3 routine pytest positions first26/60s, sole necessary repair26/60s,
root360s; failures/aborts/unknown spent, no old/protected refund/renewal.
Retain returns-309-* original recovery directory; serialize tests from source/
editor/formatter tools. Exit intake only, then typed bounded history/retention/
delivery as supported, no usable command or protected work.

First26 FAILED4/PASS22/12.48s: late_rng/late_store/late_pose/late_mask all reached
expected intake rejection, then old fixture assertion followed deliberately
replaced RNG reference or expected old mutation-count set (1 != 0). Retain
original RNG object/state and include ONLY four new mutation names in exact
counter assertion; source/helper/old cases/limits unchanged. Failed pipeline
did not reach closing hashes; first position spent/log retained, no refund.
Same reserved26/60s next, no source/tolerance/assertion/resource cap relaxation.

Same26 PASS4.99s; root4905 PASS/knownQDQxfail/71 warnings/180.98s. Successful
focused/root runs retained all four before/after source/test hashes; Ruff root,
changed-file format, whitespace and editor diagnostics PASS. AST conservation
checks retain every old source definition/import/default and exact old61-case
intake expression; only one helper and26 additive controls. Pylance signature
query resolved no callers for new private helper (dynamic fixture lookup), not
static compatibility proof. All3 fresh pytest positions spent; initial failure
and both successful logs retained, no aborted/unknown attempts refunded and no
protected experiment renewed. No additional opt-in C/Arm/sanitizer/board/model/
study/dependency commands; unchanged default interface controls ran in root.
All8 flags false, source correspondence only. Next typed <=8-record postprocessing
history, then recorder retention and delivered/pending composition as supported.

## 310. Typed Bounded Native ToF Postprocessing History (2026-11-11)

Begin cleanfd0d88b. Local hypothesis: closed21-key postprocessing packet may use
neighboring typed history pattern: <=8 ordered builtin-list four-key records,
exact builtin epoch/tick/delivery metadata, unique independently prevalidated
native source pairing, finite canonical six64 float words <=32chars, two64
literal masks and stored64 uint32 words. Profile/pre-noise/stored/final-mask joins
only; no internal arithmetic/noise-law/source/geometry/coverage/error/physical/
clock/one-use/admission qualification and all8 flags false. Unsupported/nonfinite
raw source stays unknown; signed observation words retained, no replay/draw/hash/
clock/intake/read/retention in validator. Extend old67-case matrix by33 controls;
one existing fresh step/geometry/two native intakes before poison per new fixture,
copy/legacy/noisy use8 declared paired records from one actual packet, NOT8 measured
acquisitions. Guard max3072 float decodes/512 storage words/1024 bool masks per
validation; unchanged arithmetic/default/frozen/work/old-family controls.
Fresh3 routine pytest positions first33/60s, sole necessary repair33/60s,
root360s; failures/aborts/unknown spent, no historical/protected refunds/renewals.
Keep returns-310-* in original recovery directory; serialize source-sensitive
checks from editors/formatters. Exit typed history, then opt-in recorder retention
and delivered/pending composition as supported, not protected work/admission.

First33 PASS0.74s/four hashes stable; scoped Ruff/format/editor/AST old definitions,
imports/defaults/exact old67-case prefix PASS. One nearby native archive boundary
read showed storage prevalidation checks uint32 range, not finite IEEE float32
encoding. Retain original guard contract; ONLY new companion guard now rejects
all-ones float32 exponent (raw infinity/NaN) and adds one matching NaN storage
word in native+postprocessing control. This is finite representation preflight,
not noise/clip arithmetic qualification. Narrow routine plan revision: reserved
necessary check34/60s then sole root360s, same3 positions and no old/protected
refund/renewal, new integer bit test within existing512 stored-word count.

Revised34 PASS5.04s/four hashes stable; scoped Ruff/format/editor/AST conservation
PASS. Pylance selected /opt/venv/bin/python; references resolve definition only,
not static caller compatibility proof. Two of three positions spent; root gate
NOT RUN. User paused for today, then requested a WIP commit/push only. Preserve
this unfinished increment as WIP, not a verified source checkpoint or contract
adoption. Resume only after a fresh continuation: check current files and finish
the pending required gate before recorder retention. Logs remain retained;
all8 flags false, no qualification or protected-budget renewal.

**Checkpoint completion (2026-11-12).** Fresh user continuation resumes only this
checkpoint and migration handoff, then pauses. Clean main at pushed f31e833;
current source/test AST matches the WIP and preserves all old definitions/imports/
defaults/67-case prefix. Selected and terminal Python /opt/venv, Python3.12.3;
retained focused logs verified present, no competing test/compiler jobs observed.
Sole reserved root PASS4939/knownQDQxfail/71 warnings/144.93s, all four source/test
hashes stable, root Ruff/changed-file format/whitespace/editor diagnostics PASS.
All3 routine pytest positions now spent; no extra focused run, failure, refund,
dependency/model/study/hardware or additional opt-in C/Arm/sanitizer command.
The unchanged default interface controls ran. Typed history checkpoint complete,
not recorder retention or numerical/physical/source/admission qualification.

## 311. Cloud Harness Handoff and Restart Prompt (2026-11-12)

**Pause boundary.** The user requested completion of the paused checkpoint,
documentation and a prompt before moving Copilot from local to cloud. §310 is
now verified; no postprocessing recorder retention/delivery work was started.
Source revision f31e833 (previously WIP) is the tested source; the documentation
closeout is a descendant on main. Preserve fd0d88b intake and all earlier archives,
failures, spent ledgers and evidence limits. No usable command is admitted; all
eight qualification/permission/training flags remain false.

**Next bounded slice, after a fresh continuation.** Use the existing
`_SyntheticC1SourceRecorder.record_native_tof_source` and initializer in
`sim/diagnostics.py`, and `test_native_tof_wall_retention` in `tests/test_sim.py`.
Recommended compatible option: append literal `include_postprocessing=False`,
with private <=8 native-tick-aligned detached postprocessing records, exact-repeat
deduplication, changed-repeat rejection, oldest trimming and explicit gaps.
Reuse `_sample_simulator_native_tof_postprocessing_source` and
`_check_native_tof_postprocessing_history`, with independent native prevalidation
before companion guards/digests and original/closing cache/native/RNG/profile/
pose/input/history/outgoing-copy checks. Do not replay, draw noise, read/step/reset
or adopt a noise law to retain records. Preserve default keys/operations and old
family budgets. Later use the neighboring retained-direction matcher and
`snapshot_native_tof_delivery` / `test_native_tof_wall_snapshot` for delivered/
pending joins; do not combine that publication into the first retention slice.
Root review is near its 1,000-line organization target. Before further checkpoint
growth, archive whole301-305 using the existing lossless pattern and rebase links;
preserve all historical bodies/anchors/ledgers, never rerun an old migration.

**Portable evidence and environment.** The local Python3.12.3 /opt/venv environment,
Ruff/timeout, Pylance, editor memory and recovery logs are not guaranteed in cloud.
Read committed documents/Git first; verify actual tools/interpreter/dependencies
and budgets there. Missing local logs/tools neither prove a pass nor refund old
attempts; use the documented standing authority for a fresh bounded routine check
if genuinely necessary, not an unchanged successful gate for reassurance.
Local-only `.git/recovery-20261109-PmbQpU/returns-310-*` retains both focused logs,
root log and root hash list; Git does not push these files. No transfer/download
or dependency/environment/security change was performed. Recorded outcomes are
33 PASS0.74s, revised34 PASS5.04s and root4939 PASS144.93s; all3 positions spent.
The four tested source identities (SHA256, unchanged through closeout) are:

```text
sim/diagnostics.py d6b3339ad86cd40f2dd77f98dc1f93a621282f782325556a19c09f38308b88f6
sim/rover.py 836c35ff01e5f29dfb2d859287d7367ce6a3ce5d5b2a414071a10059bf16fc37
interface/protocol.py 54f91345baf73256e4d897d6c415e5d09ea07f85622d063c029259ff6eaa4ff6
tests/test_sim.py af80a51b9f4d3d6fca8ee0d8e4b096fc1c878a7eccfe921a0d8b09d12db81130
```

**Cloud restart prompt.** This is a future user directive, not permission to
resume after the current pause until supplied in the new chat:

```text
Continue micro_classifier from latest main containing REVIEW.md sections 310-311.
Read AGENTS.md, REVIEW.md section 311 and section 310 completion, then DESIGN.md's
postprocessing topic in docs/design/07-data-and-distillation-design-02.md.
The local migration pause ends with this fresh continuation. Do not rely on old
chat/editor memory, local /opt/venv, Pylance or .git/recovery logs being available.
Verify worktree, upstream, current source, installed tools/interpreter and budgets.
Typed postprocessing history is complete: 34 focused controls and root4939 passed;
known QDQ xfail/71 warnings retained, all3 old routine positions spent, all8 flags false.
Next implement ONLY bounded default-off postprocessing recorder retention using
_SyntheticC1SourceRecorder.record_native_tof_source and test_native_tof_wall_retention.
Follow section 311's ownership/prevalidation/dedup/trim/gap and no-replay constraints.
Then reassess separately bounded retained joins and delivered/pending publication.
Choose routine compatible decisions autonomously, record a finite synthetic scope,
make a grounded small edit and immediately run its focused discriminating check.
Before a verified checkpoint, run root pytest/Ruff/diff and changed-file format gates.
Retain failures/unknown attempts; do not refund old studies or weaken assertions/caps.
Do not repeat finished floor-division reports or unchanged green gates for reassurance.
Keep all qualification/admission flags false and raw unsupported/nonfinite source unknown.
No new noise law, bounds, task data/studies/training/models/dependencies/downloads,
.devcontainer/security changes, hardware/ST access, general audits/SC18 or actuation.
Use existing helpers/tests/docs; preserve user changes and historical evidence.
No questionnaires/subagents unless explicitly authorized; follow higher-priority harness rules.
Commit scoped verified increments and normal upstream pushes only when harness permits.
Continue useful authorized work across checkpoints until I explicitly pause or stop.
```

Handoff checks PASS: exact prior review/design/stable workflow conservation,
four tested source hashes, actual next-code anchors, new reference targets and
editor diagnostics. No source edit or repeated successful code gate for closeout.

## 312. Bounded Native ToF Postprocessing Recorder Retention (2026-11-12)

Fresh continuation begins clean main7fc6047, synchronized with origin/main after
fetch. Terminal and Pylance select /opt/venv/bin/python, Python3.12.3; installed
pytest8.4.2, Ruff0.17.0, timeout, host cc and Arm compiler observed. No competing
pytest/Ruff/compiler process observed; historical returns-310 logs exist with
nonzero sizes and all four §311 source hashes match. This verifies current
environment observations, not transferable logs, clocks or qualification.

Before review growth, move whole301-305 to [their archive][chapter-review-25].
Exact bodies including trailing separators, headings, failures and spent ledgers
are conserved; root reading-map changes and four chapter01 references are the only
other migration changes. Archive bodies have no Markdown links requiring rebasing.
Exact written-layout/conservation and four rebased anchors PASS; no old migration
or successful code gate rerun for this archival.

Local hypothesis from the existing recorder: append literal
`include_postprocessing=False`, private native-tick-aligned <=8 detached records,
exact-repeat deduplication, changed-repeat rejection, oldest-native trimming and
explicit absent-companion gaps. Reuse closed intake and typed companion guard;
independent native archive-word validation precedes initial/ownership/staged/
closing companion guards and digests when opted in or retaining prior records.
Original/closing native and companion caches, RNG identities, producer profile/
pose/input, recorder ownership/history identities and detached outgoing copies
must match before committing staged histories. Default has no companion intake;
no snapshot/delivery keys or publication implementation changed.

Extend existing17-case wall/cylinder/direction retention matrix with only17
postprocessing controls; old51 controls and their budgets stay unchanged.
New fixtures retain <=13 geometry calls,14 reads,10 retentions,20 companion
intakes,40 native intakes (combined22),256 binding calls and one late mutation.
Check captured noise words, storage/final-mask joins, all eight false flags,
unchanged RNG states, forbidden read/step/reset/replay/geometry/clock calls,
repeat/gap/trim/budget and native-word rejection before digest.
Fresh initial plan: focused17/60s, sole necessary repair17/60s, root/360s;
failures/aborts/unknown spent, no historical/protected refund or renewal.
Keep raw outputs and four-file hash lists under ignored `.git/returns-312-*`.

First17 FAILED before retention: fixture changed environment noise/dropout while
the recorder profile is fixed. Remove only that fixture override, preserving the
production profile guard. Necessary check FAILED1/PASS16/4.95s: the new paired-word
test incorrectly inserted a direction-only key into the closed postprocessing
trace. Correct only the fixture pairing/expected exact archived-word rejection.
Owning-code inspection also exposes layout-only native prevalidation; add the
existing archive-word guard for postprocessing before companion guards/digests,
not a relaxed assertion or a change to other families. Narrow finite routine
revision adds one necessary17/60s check, retains reserved root/360s; both prior
positions remain spent. Revised17 PASS4.16s, all four hashes stable across all
three checks. Scoped Ruff/changed-file format/whitespace PASS. Pylance signature
check found no resolved call sites, not static proof of every dynamic caller.

Required root `python -m pytest -q && ruff check . && git diff --check`
PASS4956/known QDQ xfail/71 warnings/176.36s; changed-file format PASS and all four
source hashes stable. All four fresh positions spent (two failures, focused pass,
root pass), no abort/refund/renewal. Scoped source/test diff reviewed; Pylance
reports no error/warning diagnostics in either touched Python file.
No code gate rerun for documentation closeout.
This is recorder source correspondence only, not
internal arithmetic/noise-law, geometry/coverage/error/source/physical/clock/
one-use/permission/admission qualification; all eight flags remain false.
No new study/model/dependency/download/hardware or extra native/Arm/sanitizer
opt-in run. Next separately bounded retained-postprocessing matcher, then
delivered/pending publication with original/closing source and owner joins.

## 313. Bounded Retained Native ToF Postprocessing Matching (2026-11-12)

Begin clean pushed7b558e4. Upstream main identity confirmed by ls-remote.
Previous push succeeded despite nonfatal stale credential-store helper paths;
no credential/security/remote configuration changed and no secret inspected.

Separate local hypothesis from retained-direction matcher: prevalidated native
source and typed companion history can use <=8-record unique matching of exact
builtin epoch/acquisition/delivery identities, then a detached copy. Matching
equal-value/different-type metadata is not accepted; missing/ambiguous pairs,
non-builtin list and >8 records reject. This helper assumes prior independent
native archive-word and companion-history prevalidation; it does not replace
those guards, sample source or publish delivered/pending results.

Extend only existing9-case retained-direction matcher fixture with9 postprocessing
controls; original cases/family remain unchanged. Each new fixture uses one fresh
step/geometry, two recorder reads and one retention before poisoning intake/
read/retention/step/reset/replay/clock/hash paths. Match scans <=8 entries/24
typed metadata comparisons, then at most one detached trace copy. Missing/
duplicate/epoch/tick/delivery/typed-tick/budget/tuple rejection and nested outgoing
copy independence leave input records unchanged. Fresh three routine pytest
positions: first9/60s, sole necessary repair9/60s, required root/360s. Failures/
aborts/unknown remain spent; reserve is not follow-on authority, no old refund.
Retain ignored `.git/returns-313-*` output/hash logs; checks serialized.

First9 PASS3.72s, four source/test hashes stable; scoped Ruff/changed format/
whitespace PASS. Required root PASS4965/known QDQ xfail/71 warnings/159.43s,
root Ruff/changed format/whitespace PASS, all four source hashes stable.
Two of three fresh pytest positions spent, no failure/abort/refund; unused repair
is not follow-on authority. Pylance pytest-signature check found no resolved call
sites, not static proof of dynamic callers. No code gate repeated for closeout.
No delivery implementation or
default/public key change, numerical/internal-noise/noise-law/geometry/coverage/
source/error/clock/one-use/physical/permission/admission qualification. All eight
flags remain false; unsupported/nonfinite source stays unknown. No protected
study/model/dependency/download/hardware/extra native/Arm/sanitizer opt-in.
Next independently bounded delivered/pending composition using original/closing
native/source/RNG/profile/pose/input/history/stored-word/mask and outgoing joins.

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
[chapter-review-24]: docs/review/296-300.md
[chapter-review-25]: docs/review/301-305.md
[native-tof-ray-design]: docs/design/07-data-and-distillation-design-01.md#native-tof-ray-generation-prerequisites-2026-11-11
[cloud-harness-handoff]: #311-cloud-harness-handoff-and-restart-prompt-2026-11-12
