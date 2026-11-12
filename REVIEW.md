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
- [Checkpoints 306-310][chapter-review-26]

Checkpoints 311 onward and the source bibliography remain below.
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

## 314. Closed Native ToF Postprocessing Delivery Publication (2026-11-12)

Begin clean pushed9e8d6d5. Local hypothesis from the existing direction snapshot:
append literal `include_postprocessing=False`; compose separately retained traces
against exact delivered and optional pending native acquisition identities.
Independent native archive-word validation precedes original/ownership/copy/
closing companion guards and digests, including after closing frame and pending
queue callbacks. Recheck typed original/closing companion histories, detached
outputs, stored words and final masks before publishing. Existing producer/RNG/
profile/pose/input/frame/pending-queue ownership checks remain in place.
Missing/ambiguous/unsupported/nonfinite or changed source returns the existing
explicit unknown reason, without source/frame/companion publication. Default
adds no postprocessing keys or intake/matcher calls; no sensor replay or new draw.

Extend only existing24-case wall/cylinder/direction snapshot matrix with24
postprocessing cases; old168 controls/budgets remain unchanged. Per new fixture:
<=4 steps,5 reads,3 retentions/geometries,6 companion/other-wall/timing/selection/
norm matches,2 pending matches,4 queue copies,2 frame checks,64 bindings and one
late mutation. Capture and retain at most three actual fresh acquisitions before
poisoning intake/read/retention/replay/step/reset/clock/geometry paths. Check exact
delivered/pending identities and stored-word/mask joins, detached copies, held/
delivered-only/default output keys, prehash native/canonical/budget rejection,
closing native-input removal and late outgoing/owner/history/queue/report changes.
No new arithmetic report or numerical/noise-law adoption is added.

Fresh three routine positions: first24/60s, sole necessary repair24/60s,
required root/360s; failures/aborts/unknown spent, no historical/protected refund.
Keep ignored `.git/returns-314-*` outputs/hashes, serialize source-sensitive
checks. First24 PASS5.64s, all four hashes stable; scoped Ruff/changed format/
whitespace PASS. Pylance signature check found no resolved call sites, not
static proof of every dynamic caller. Required root PASS4989/known QDQ xfail/
71 warnings/158.08s; root Ruff/changed format/whitespace PASS, all four source
hashes stable. Scoped diff reviewed; all previous module/recorder nodes, API
defaults and old168-case prefix conserved in AST. Two of three fresh positions
spent, no failure/abort/refund; unused repair is not follow-on authority.
No successful code gate repeated for documentation closeout.

All eight flags remain false; raw unsupported/nonfinite source stays unknown.
Matching traces/words are not internal noise/dropout/clip arithmetic, probability,
geometry/coverage/error/source/physical/clock/one-use/permission/admission proof.
No new study/model/dependency/download/hardware/extra native/Arm/sanitizer opt-in.
Next reassess independently supported native postprocessing operation/operand
correspondence, retaining source observations rather than adopting a noise law.

## 315. Supplied-Word Native ToF Noise-Addition Discrepancies (2026-11-12)

Begin clean pusheded54793. Actual cold sampler owner copies pre-noise grid and
the existing normal draw around `grid += noise`; no new sample/draw or replacement
distribution is needed to report supplied-word addition discrepancies.
Standalone helper reuses bounded `_C1CommandArithmetic`: three builtin64-word
tuples, <=32char canonical words, finite supplied operands, raw +/-inf observation
unknown and NaN/unsupported rejection before rational work. Unchanged1..4096bit
ceiling, <=192 float decodes/value conversions,128 binary operations and64 entries.
Report exact unrounded supplied sum, observed raw noisy word and signed rational
residual; preserve signed words and unresolved equal-value/different-word ties.
No NumPy primitive/rounding proof, uniform error bound, noise law or qualification.

Add24 bounded standalone controls: one actual cold sample/geometry with only
existing draws before poison, exact/rounded/mismatched/subnormal/large finite/
cancellation/signed-zero words, raw +/-inf unknown, malformed canonical/builtin/
shape/word/bit budgets and16bit work-limit rejection. Independent Fraction
oracle <=128 operations. No intake/read/retention/replay/step/reset/sample/hash/
clock/geometry during helper calls. Prior helpers/defaults/tests unchanged.
Fresh three routine positions: focused24/60s, sole necessary repair24/60s,
required root/360s; failure/abort/unknown spent, no old/protected refund/renewal.
Retain ignored `.git/returns-315-*` output/hash logs; serialize checks.

First FAILED1/PASS23/3.81s: actual fixture passed config/scenario positionally to
the keyword-only `_sample` owner. Verify exact owner signature and remove only
the two unsupported arguments; no source/oracle/assertion/cap change. Necessary
24 PASS3.11s, all four hashes stable for both. Scoped Ruff/changed format/
whitespace PASS. Pylance workspace-symbol lookup returned no new helper match;
runtime/AST evidence is authoritative here, not an inferred editor fact.
Required root PASS5013/known QDQ xfail/71 warnings/153.24s; root Ruff/changed
format/whitespace PASS, all four source hashes stable. All three fresh positions
spent (one fixture failure, focused/root passes), no abort/refund/renewal.
Scoped diff reviewed; all prior source/test module AST and defaults exact.
New reference target/anchor PASS; no successful code gate repeated for closeout.

All eight flags remain false; raw unsupported/nonfinite source remains unknown
for qualification. This standalone report is not retained delivered/pending
arithmetic composition, internal dropout/clip/cast proof, probability/noise-law/
geometry/coverage/error/source/physical/clock/one-use/permission/admission proof.
No new study/model/dependency/download/hardware/extra native/Arm/sanitizer opt-in.
Next separately bounded original/closing retained noise-addition report joins.

## 316. Intact Postprocessing Checkpoint and Topic Relocation (2026-11-12)

Begin clean pushedf73b9ab. Before further growth, move whole306-310 to
[their archive][chapter-review-26], preserving exact bodies, separators, headings,
failures, approvals, spent/unknown ledgers and pause/WIP/completion boundaries.
No archive-body links require rebasing; four live postprocessing checkpoint
references now target the archive. Root map allocation and remaining bodies
are conserved, not a renewed test/experiment budget or qualification.

Relocate the complete151-line postprocessing topic from chapter02 to existing
chapter03 without changing its body. Preserve every old topic/subtopic anchor
in chapter02 as a link to its unchanged chapter03 section; retain old reference
definitions, copy only missing topic definitions and verify any existing
definition agrees. Existing chapter03 is an exact prefix, no unrelated topic
body changed. DESIGN's direct postprocessing reading-map target now selects
chapter03. Exact written-layout, all eight retained heading anchors, new/rebased
local targets and whitespace PASS; four tested source hashes remain unchanged.
Resulting review/chapter02/chapter03 sizes before this note:757/2391/2244 lines.
Original documents and migration utility retained in session artifact storage,
not a portable Git log. No code suite, old migration, experiment or successful
source gate rerun. All qualification/admission flags remain false.
Next bounded original/closing retained noise-addition report composition.

## 317. Matched Native ToF Noise-Addition Reports (2026-11-12)

Begin clean pushedadd441d. Separate local hypothesis: append literal default-off
`include_postprocessing_noise_addition_residuals`, requiring postprocessing
inclusion. Reuse standalone supplied-word sum reporting against original/closing
retained delivered and optional pending traces. Native/typed companion
prevalidation precedes report construction, including after closing frame/queue
callbacks; final original/closing word, history identity, report-content and
output-binding checks precede publication. Supplied operands and raw words are
unchanged; no source correction or adopted noise/rounding/error law.

Extend existing24-case snapshot matrix with24 report-mode cases and three literal/
dependency controls. Original192 controls/defaults and per-family work caps
remain unchanged. New report scope <=6 calls/1,152 value conversions/768 binary
operations; independent Fraction oracle <=384 operations,64 entries/report,
unchanged32char/1..4096bit bounds. Existing four-step/five-read/three-acquisition/
geometry/retention fixture limits and original/closing late-mutation controls
stay in force. Check report IDs/operands/observations/exact sums/residuals, absent
default keys, nested output detachment and unknown-with-no-partial-publication.

Fresh three routine positions: focused27/60s, sole necessary repair27/60s,
required root/360s; failures/aborts/unknown spent, no old/protected refund or
renewal. Keep ignored `.git/returns-317-*` outputs/hashes; checks serialized.
First27 PASS5.71s/192 deselected, all four source hashes stable; scoped Ruff/
changed format/whitespace PASS. Pylance signature check found no resolved call
sites, not static proof of every dynamic caller. Required root PASS5040/
known QDQ xfail/71 warnings/157.05s; root Ruff/changed format/whitespace PASS,
all four source hashes stable. Scoped source/test diff and AST conservation
PASS for old module/recorder/default/test nodes and old192-case prefix;
new reference target/anchor PASS. Two of three fresh positions spent, no
failure/abort/refund; unused repair is not follow-on authority.
No successful code gate repeated for documentation closeout.

All eight flags remain false. Observed raw unsupported/nonfinite source remains
unknown; matching reports do not qualify native primitive/FMA/rounding/error/
noise-law/dropout/clip/cast/geometry/coverage/source/clock/one-use/physical/
permission/admission. No new study/model/dependency/download/hardware/extra
native/Arm/sanitizer opt-in. Next independently supported supplied-word dropout
comparison/mask correspondence, without probability-law or threshold adoption.

## 318. Supplied-Word Native ToF Dropout Mask Correspondence (2026-11-12)

Begin clean pushedab124f1. Actual sampler captures the existing dropout draw
around `valid &= dropout >= config.dropout`. Standalone helper compares supplied
draw/threshold words and literal prior/observed masks; no draw or distribution
model is needed. Reuse the observed profile's existing finite0..1 dropout field,
not a new threshold. Finite draw values outside0..1 remain comparisons, not
clamped or rejected by an invented RNG law. Raw +/-inf draw words remain unknown
even when the prior mask is false; NaN/unsupported metadata rejects explicitly.

Closed builtin64-word tuple and two64 literal boolean masks; <=32char canonical
words,65 word decodes,64 predicate/mask comparisons and64 entries. Preserve raw
signed words and report expected mask, observed mask, mismatch/unknown counts;
matching values do not resolve different-word ties or qualify the comparator.
Add24 bounded controls for actual/keep/drop/equality/prior-mask/mismatch/signed
zero/finite out-of-range/raw nonfinite words, typed masks, closed tuple/word/
profile preflight. One actual cold sample/geometry with only existing normal/
dropout draws before poisoning intake/read/retention/replay/step/reset/sample/
hash/clock/geometry paths; <=64 independent Fraction-oracle comparisons.
All prior helper/default/test nodes remain unchanged.

Fresh three routine positions: focused24/60s, sole necessary repair24/60s,
required root/360s; failures/aborts/unknown spent, no historical/protected refund.
Retain ignored `.git/returns-318-*` outputs/hashes, serialize checks.
First24 PASS3.43s, all four source hashes stable; scoped Ruff/changed format/
whitespace PASS. Required root PASS5064/known QDQ xfail/71 warnings/156.51s;
root Ruff/changed format/whitespace PASS, all four source hashes stable.
Scoped diff/AST and new reference target/anchor checks PASS; all prior module/
default/test nodes exact. Two of three fresh positions spent, no failure/abort/
refund; unused repair is not follow-on authority. No code gate repeated for
documentation closeout.

All eight flags remain false; source unknowns remain unknown. This is standalone
supplied-word/mask correspondence, not native execution, noise/probability law,
numerical/error/clip/cast/geometry/coverage/source/clock/one-use/physical/
permission/admission qualification. No new study/model/dependency/download/
hardware/extra native/Arm/sanitizer opt-in. Next original/closing retained
dropout-mask report joins, without changing source or adopting a probability law.

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
[chapter-review-26]: docs/review/306-310.md
[native-tof-ray-design]: docs/design/07-data-and-distillation-design-01.md#native-tof-ray-generation-prerequisites-2026-11-11
[cloud-harness-handoff]: #311-cloud-harness-handoff-and-restart-prompt-2026-11-12
