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
- [Checkpoints 311-315][chapter-review-27]
- [Checkpoints 316-320][chapter-review-28]
- [Checkpoints 321-325][chapter-review-29]
- [Checkpoints 326-330][chapter-review-30]
- [Checkpoints 331-335][chapter-review-31]
- [Checkpoints 336-340][chapter-review-32]
- [Checkpoints 341-345][chapter-review-33]
- [Checkpoints 346-350][chapter-review-34]
- [Checkpoints 351-355][chapter-review-35]
- [Checkpoints 356-360][chapter-review-36]
- [Checkpoints 361-365][chapter-review-37]
- [Checkpoints 366-370][chapter-review-38]
- [Checkpoints 371-375][chapter-review-39]
- [Checkpoints 376-380][chapter-review-40]
- [Checkpoints 381-385][chapter-review-41]
- [Checkpoints 386-390][chapter-review-42]
- [Checkpoints 391-394][chapter-review-43]
- [Checkpoints 395-396][chapter-review-44]
- [Checkpoints 397-398][chapter-review-45]
- [Checkpoints 399-400][chapter-review-46]
- [Checkpoints 401-402][chapter-review-47]

Checkpoints 403 onward remain below. The original source bibliography is linked
under Sources.
[Original cloud harness handoff (§311)][cloud-harness-handoff] preserves
restart context; the newest checkpoint identifies next bounded work.
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

[Complete unchanged checkpoint][review-311-315-preserved-0] is preserved in the archive.

## 312. Bounded Native ToF Postprocessing Recorder Retention (2026-11-12)

[Complete unchanged checkpoint][review-311-315-preserved-1] is preserved in the archive.

## 313. Bounded Retained Native ToF Postprocessing Matching (2026-11-12)

[Complete unchanged checkpoint][review-311-315-preserved-2] is preserved in the archive.

## 314. Closed Native ToF Postprocessing Delivery Publication (2026-11-12)

[Complete unchanged checkpoint][review-311-315-preserved-3] is preserved in the archive.

## 315. Supplied-Word Native ToF Noise-Addition Discrepancies (2026-11-12)

[Complete unchanged checkpoint][review-311-315-preserved-4] is preserved in the archive.

## 316. Intact Postprocessing Checkpoint and Topic Relocation (2026-11-12)

[Complete unchanged checkpoint][review-316-320-preserved-0] is preserved in the archive.

## 317. Matched Native ToF Noise-Addition Reports (2026-11-12)

[Complete unchanged checkpoint][review-316-320-preserved-1] is preserved in the archive.

## 318. Supplied-Word Native ToF Dropout Mask Correspondence (2026-11-12)

[Complete unchanged checkpoint][review-316-320-preserved-2] is preserved in the archive.

## 319. Matched Native ToF Dropout Reports (2026-11-12)

[Complete unchanged checkpoint][review-316-320-preserved-3] is preserved in the archive.

## 320. Supplied-Word Native ToF Clip/Selection Correspondence (2026-11-12)

[Complete unchanged checkpoint][review-316-320-preserved-4] is preserved in the archive.

## 321. Matched Native ToF Clip/Selection Reports (2026-11-12)

[Complete unchanged checkpoint][review-321-325-preserved-0] is preserved in the archive.

## 322. Intact Retention and Delivery Checkpoint Archival (2026-11-12)

[Complete unchanged checkpoint][review-321-325-preserved-1] is preserved in the archive.

## 323. Supplied-Word Native ToF Selected/Storage Residuals (2026-11-12)

[Complete unchanged checkpoint][review-321-325-preserved-2] is preserved in the archive.

## 324. Matched Native ToF Selected/Storage Reports (2026-11-12)

[Complete unchanged checkpoint][review-321-325-preserved-3] is preserved in the archive.

## 325. Cold Native Goal Computation Source (2026-11-12)

[Complete unchanged checkpoint][review-321-325-preserved-4] is preserved in the archive.

## 326. Native Goal Computation Acquisition Pairing (2026-11-12)

[Complete unchanged checkpoint][review-326-330-preserved-0] is preserved in the archive.

## 327. Closed Native Goal Computation Intake (2026-11-12)

[Complete unchanged checkpoint][review-326-330-preserved-1] is preserved in the archive.

## 328. Intact Goal-Prerequisite Review Archival (2026-11-12)

[Complete unchanged checkpoint][review-326-330-preserved-2] is preserved in the archive.

## 329. Typed Bounded Native Goal Computation History (2026-11-12)

[Complete unchanged checkpoint][review-326-330-preserved-3] is preserved in the archive.

## 330. Default-Off Native Goal Recorder Retention (2026-11-12)

[Complete unchanged checkpoint][review-326-330-preserved-4] is preserved in the archive.

## 331. Exact Retained Native Goal Matching (2026-11-12)

[Complete unchanged checkpoint][review-331-335-preserved-0] is preserved in the archive.

## 332. Closed Default-Off Native Goal Delivery (2026-11-12)

[Complete unchanged checkpoint][review-331-335-preserved-1] is preserved in the archive.

## 333. Supplied-Word Native Goal Delta Discrepancies (2026-11-12)

[Complete unchanged checkpoint][review-331-335-preserved-2] is preserved in the archive.

## 334. Intact Native Goal Prerequisite Checkpoint Archival (2026-11-12)

[Complete unchanged checkpoint][review-331-335-preserved-3] is preserved in the archive.

## 335. Matched Native Goal Delta Reports WIP and Pause (2026-11-12)

[Complete unchanged checkpoint][review-331-335-preserved-4] is preserved in the archive.

## 336. Current-State Review and Native Goal Boundary Repairs (2026-11-13)

[Complete unchanged checkpoint][review-336-340-preserved-0] is preserved in the archive.

## 337. Supplied-Word Native Goal Expression Residuals (2026-11-13)

[Complete unchanged checkpoint][review-336-340-preserved-1] is preserved in the archive.

## 338. Intact Goal Ownership Checkpoint Archival (2026-11-13)

[Complete unchanged checkpoint][review-336-340-preserved-2] is preserved in the archive.

## 339. Matched Retained Native Goal Expression Reports (2026-11-13)

[Complete unchanged checkpoint][review-336-340-preserved-3] is preserved in the archive.

## 340. Supplied Native and Stored Goal-Word Correspondence (2026-11-13)

[Complete unchanged checkpoint][review-336-340-preserved-4] is preserved in the archive.

## 341. Matched Retained Goal Storage Reports (2026-11-13)

[Complete unchanged checkpoint][review-341-345-preserved-0] is preserved in the archive.

## 342. Supplied Pre-Integration Speed-Update Residuals (2026-11-13)

[Complete unchanged checkpoint][review-341-345-preserved-1] is preserved in the archive.

## 343. Supplied Target and Yaw Clipping Correspondence (2026-11-13)

[Complete unchanged checkpoint][review-341-345-preserved-2] is preserved in the archive.

## 344. Intact Goal Delivery Checkpoint Archival (2026-11-13)

[Complete unchanged checkpoint][review-341-345-preserved-3] is preserved in the archive.

## 345. Closed Current Receipt Motion-Update Reports (2026-11-13)

[Complete unchanged checkpoint][review-341-345-preserved-4] is preserved in the archive.

## 346. Supplied Captured-Interval Division Residuals (2026-11-13)

[Complete unchanged checkpoint][review-346-350-preserved-0] is preserved in the archive.

## 347. Intact Motion-Word Contract Relocation (2026-11-13)

[Complete unchanged checkpoint][review-346-350-preserved-1] is preserved in the archive.

## 348. Intact Reviewed Goal-Expression Checkpoint Archival (2026-11-13)

[Complete unchanged checkpoint][review-346-350-preserved-2] is preserved in the archive.

## 349. Closed Current Receipt Interval Reports (2026-11-13)

[Complete unchanged checkpoint][review-346-350-preserved-3] is preserved in the archive.

## 350. Supplied Unrounded Segment-Count Comparison (2026-11-13)

[Complete unchanged checkpoint][review-346-350-preserved-4] is preserved in the archive.

## 351. Closed Current Segment-Selection Reports (2026-11-13)

[Complete unchanged checkpoint][review-351-355-preserved-0] is preserved in the archive.

## 352. Native Integration Closing-Observation Repairs (2026-11-13)

[Complete unchanged checkpoint][review-351-355-preserved-1] is preserved in the archive.

## 353. Intact Motion and Goal Checkpoint Archival (2026-11-13)

[Complete unchanged checkpoint][review-351-355-preserved-2] is preserved in the archive.

## 354. Closed Live-Receipt Owned Request Joins (2026-11-13)

[Complete unchanged checkpoint][review-351-355-preserved-3] is preserved in the archive.

## 355. Checked Remaining Acceptance Blockers (2026-11-13)

[Complete unchanged checkpoint][review-351-355-preserved-4] is preserved in the archive.

## 356. Actual Intake Closing-Observation Repairs (2026-11-13)

[Complete unchanged checkpoint][review-356-360-preserved-0] is preserved in the archive.

## 357. Intact Motion Checkpoint Archival (2026-11-13)

[Complete unchanged checkpoint][review-356-360-preserved-1] is preserved in the archive.

## 358. Closed Actual Initial-Tick Setup Correspondence (2026-11-13)

[Complete unchanged checkpoint][review-356-360-preserved-2] is preserved in the archive.

## 359. Closed Initial Setup Report Consumer Metadata (2026-11-13)

[Complete unchanged checkpoint][review-356-360-preserved-3] is preserved in the archive.

## 360. Intact Source and Consumer Checkpoint Archival (2026-11-13)

[Complete unchanged checkpoint][review-356-360-preserved-4] is preserved in the archive.

## 361. Bounded Initial Source Retention (2026-11-13)

[Complete unchanged checkpoint][review-361-365-preserved-0] is preserved in the archive.

## 362. Bounded Retained Initial Source Reading (2026-11-16)

[Complete unchanged checkpoint][review-361-365-preserved-1] is preserved in the archive.

## 363. Conditional Owned Initial-Rest Startup (2026-11-16)

[Complete unchanged checkpoint][review-361-365-preserved-2] is preserved in the archive.

## 364. Intact Initial Source Checkpoint Archival (2026-11-16)

[Complete unchanged checkpoint][review-361-365-preserved-3] is preserved in the archive.

## 365. Supplied Normalization Division Residuals (2026-11-16)

[Complete unchanged checkpoint][review-361-365-preserved-4] is preserved in the archive.

## 366. Closed Current Later-Period Comparisons (2026-11-16)

[Complete unchanged checkpoint][review-366-370-preserved-0] is preserved in the archive.

## 367. Actual Consumed Normalization Divisor Retention (2026-11-16)

[Complete unchanged checkpoint][review-366-370-preserved-1] is preserved in the archive.

## 368. Intact Initial Source Checkpoint Archival (2026-11-16)

[Complete unchanged checkpoint][review-366-370-preserved-2] is preserved in the archive.

## 369. Closed Actual-Consumed Quotient Joins (2026-11-16)

[Complete unchanged checkpoint][review-366-370-preserved-3] is preserved in the archive.

## 370. Actual Heading Shift and Return Operand Retention (2026-11-16)

[Complete unchanged checkpoint][review-366-370-preserved-4] is preserved in the archive.

## 371. Supplied Heading Shift and Return Residuals (2026-11-16)

[Complete unchanged checkpoint][review-371-375-preserved-0] is preserved in the archive.

## 372. Intact Normalization Checkpoint Archival (2026-11-16)

[Complete unchanged checkpoint][review-371-375-preserved-1] is preserved in the archive.

## 373. Closed Current Heading-Offset Reports (2026-11-16)

[Complete unchanged checkpoint][review-371-375-preserved-2] is preserved in the archive.

## 374. Closed Default Native Reader Epoch Identities (2026-11-16)

[Complete unchanged checkpoint][review-371-375-preserved-3] is preserved in the archive.

## 375. Closed Owning Receipt Epoch Identities (2026-11-16)

[Complete unchanged checkpoint][review-371-375-preserved-4] is preserved in the archive.

## 376. Intact Heading and Receipt Checkpoint Archival (2026-11-16)

[Complete unchanged checkpoint][review-376-380-preserved-0] is preserved in the archive.

## 377. Closed Live Request Consumer Epochs (2026-11-16)

[Complete unchanged checkpoint][review-376-380-preserved-1] is preserved in the archive.

## 378. Supplied Heading Remainder Word Residuals (2026-11-16)

[Complete unchanged checkpoint][review-376-380-preserved-2] is preserved in the archive.

## 379. Closed Current Heading Remainder Joins (2026-11-16)

[Complete unchanged checkpoint][review-376-380-preserved-3] is preserved in the archive.

## 380. Intact Native-Word Topic Relocation (2026-11-16)

[Complete unchanged checkpoint][review-376-380-preserved-4] is preserved in the archive.

## 381. Intact Consumer and Remainder Checkpoint Archival (2026-11-16)

[Complete unchanged checkpoint][review-381-385-preserved-0] is preserved in the archive.

## 382. Fresh Remaining Evidence Blockers (2026-11-16)

[Complete unchanged checkpoint][review-381-385-preserved-1] is preserved in the archive.

## 383. Closed Current Native ToF Source Sampling (2026-11-16)

[Complete unchanged checkpoint][review-381-385-preserved-2] is preserved in the archive.

## 384. Closed Native ToF Delivery Report Work (2026-11-17)

[Complete unchanged checkpoint][review-381-385-preserved-3] is preserved in the archive.

## 385. Closed Fresh Native ToF Retention Sampling (2026-11-17)

[Complete unchanged checkpoint][review-381-385-preserved-4] is preserved in the archive.

## 386. Intact Source Pipeline Checkpoint Archival (2026-11-17)

[Complete unchanged checkpoint][review-386-390-preserved-0] is preserved in the archive.

## 387. Closed Native Goal Dynamics Sampling (2026-11-17)

[Complete unchanged checkpoint][review-386-390-preserved-1] is preserved in the archive.

## 388. Current Source Queue Evidence Blockers (2026-11-17)

[Complete unchanged checkpoint][review-386-390-preserved-2] is preserved in the archive.

## 389. Closed Composed Native And Receipt Cache Identities (2026-11-17)

[Complete unchanged checkpoint][review-386-390-preserved-3] is preserved in the archive.

## 390. Closed Live Request Receipt Cache Identity (2026-11-17)

[Complete unchanged checkpoint][review-386-390-preserved-4] is preserved in the archive.

## 391. Closed Conditional Startup Receipt Cache Identity (2026-11-17)

[Complete unchanged checkpoint][review-391-394-preserved-0] is preserved in the archive.

## 392. Intact Composed Source Checkpoint Archival (2026-11-17)

[Complete unchanged checkpoint][review-391-394-preserved-1] is preserved in the archive.

## 393. Closed Owning Intake Original And Final Sampling (2026-11-17)

[Complete unchanged checkpoint][review-391-394-preserved-2] is preserved in the archive.

## 394. Closed Post-Native Receipt And Pending Copies (2026-11-17)

[Complete unchanged checkpoint][review-391-394-preserved-3] is preserved in the archive.

## 395. Intact Owning Intake Checkpoint Archival (2026-11-17)

[Complete unchanged checkpoint][review-395-396-preserved-0] is preserved in the archive.

## 396. Closed Native-ToF Retention Owner Layouts (2026-11-17)

[Complete unchanged checkpoint][review-395-396-preserved-1] is preserved in the archive.

## 397. Intact Retention/Layout Checkpoint Archival (2026-11-17)

[Complete unchanged checkpoint][review-397-398-preserved-0] is preserved in the archive.

## 398. Closed Native-ToF Snapshot Owner Layouts (2026-11-17)

[Complete unchanged checkpoint][review-397-398-preserved-1] is preserved in the archive.

## 399. Intact Snapshot Ownership Checkpoint Archival (2026-11-17)

[Complete unchanged checkpoint][review-399-400-preserved-0] is preserved in the archive.

## 400. Fixed Native-ToF Owner Frame Extents (2026-11-17)

[Complete unchanged checkpoint][review-399-400-preserved-1] is preserved in the archive.

## 401. Intact Frame Boundary Checkpoint Archival (2026-11-17)

[Complete unchanged checkpoint][review-401-402-preserved-0] is preserved in the archive.

## 402. Codec State Prevalidation Before ToF Owner Copying (2026-11-17)

[Complete unchanged checkpoint][review-401-402-preserved-1] is preserved in the archive.

## 403. Intact State Checkpoints and Original Sources (2026-11-17)

From clean pushed7e9f189, one30s whole401-402 transform/two snapshots PASS body/inverse
root/topic conservation; two historical headings/one chapter01 target remain intact.
Then one30s whole Sources relocation with a third snapshot preserves all432 ordered
definitions and the full bibliography, rebasing local targets only. Root Sources
heading remains;141 root-used labels retain their exact first targets/order.
Exact inverse/path/first-definition checks PASS; root989->653 lines before this note.
This avoids repeated two-checkpoint churn without dropping ledgers or old anchors.
Scoped references/whitespace/four402 hashes PASS; no code change or suite rerun.
Latest gate6297/known QDQ1 xfail/77 warnings231.44s; scripts/layouts remain in session
files and logs in .git. This neither adds sources nor accepts evidence/permissions.
Next bounded goal-source State/frame preflight; all flags false, guard UNKNOWN.

## 404. Closed Native Goal Owner Prevalidation (2026-11-17)

From clean pushed6bb2273, named goal retention/delivery still copied malformed
nested State and hashed unsupported frame extents before rejection, including
closing owners. Reuse unchanged codec validate_state and the existing92-byte
HEADER+STATE+CRC ABI, not a new State rule/bound or frame checksum/content claim.
Four preflights/four extent checks now precede owner asdict/digests; original/
closing identities, zero-latency domain, disabled no-op and eight report
combinations remain unchanged. No new encoding/intake/copy/digest/arithmetic.

Finite plan24/repaired24/related82<=60s each and one root<=360s; prior spent
positions remain spent. First24 FAIL34.67s at pre-copy/prehash spies. First
repaired24 FAIL16.54s only in the final history assertion: strict word-copy
comparison intentionally rejects list roots, even []/[], unlike tuples used
by existing retention controls. Test-only tuple repair preserves exact words;
necessary24 PASS5.08s. Prior82 PASS2.20s/168 deselected, including six snapshot
cases across all eight report modes. <=2 observations/intakes/matches/12 digests;
history identity/words and both RNG states stay unchanged on rejection.

One360s root `python -m pytest -q --durations=10 && ruff check . && git diff --check`
PASS6321/known QDQ1 xfail/77 warnings207.15s, then Ruff/whitespace PASS.
Format/Pylance syntax/signature/AST/call/hash/reference checks PASS. Only two
method bodies and one24-case test change; added four validate_state/four len/two
type calls, other call censuses unchanged. Root includes existing host/sanitizer/
Arm controls; no C/runtime edit or firmware/board/fit/physical qualification.
Logs/hashes remain in .git; no temporary data/downloads or new study. All flags
false, guard UNKNOWN. Next trace remaining named source/consumer prerequisites;
accepted Q0-Q4 setup/source/coverage/error/clock/one-use inputs remain absent.

## 405. Closed Current ToF Post-Observation Owners (2026-11-17)

From clean pushedc876ab5, current-source ownership still copied State after early
preflight without revalidation. Six actual cases exposed first-observation empty
current IndexError/frame91 hashing and first/closing ages6/velocity4 copying.
Frozen State permits mutable nested sequences; prepared list-valued State encodes
to the unchanged original frame before mutation. Tuple identity alone is not
nested State validity. Ownership now pins the already prevalidated immutable
current tuple, then reuses validate_state before each owner copy. Fixed tuple/
State/frame layout/extent are inherited from that pin; no new wire rule or bound.

Finite plan first10/repaired10/related74<=60s and one root<=360s; earlier query/
matrix proposals were narrowed before execution. First10 FAIL13.91s: six actual
current repros and four delivery preparation errors at held/no-capture ticks.
Existing non-None capture guard repaired the setup; necessary delivery-only4
FAIL6.37s/6 deselected at expected observations (actual0), since pending publication
also needs explicit original pending capture. Both attempts remain spent.
Further owning-code trace shows delivery already encode-validates companion State
before asdict after both observations and requires exact tuple words. Caller-
injected list vectors do not satisfy that reader; no third attempt or delivery
edit. Removed those four unsupported cases, keeping six demonstrated current
regressions. Six repaired PASS4.72s; prior74 PASS2.20s, including unchanged delivery.
<=2 observations/intakes/64 digests; exact history words/identities and both RNG
states remain unchanged; explicit unknown omits source/frame/epoch/tick.

One360s root `python -m pytest -q --durations=10 && ruff check . && git diff --check`
PASS6327/known QDQ1 xfail/77 warnings213.85s, Ruff/whitespace PASS. Pylance syntax2/
format/AST/signature/call/hash/reference checks PASS. Only current-source body/
one6-case test change; +1 validate_state/+1 ValueError; no new intake/encoding/
copy/digest/arithmetic calls. Logs/hashes retained in .git; no data/downloads or
qualification. All flags false/guard UNKNOWN. Next bounded owner-pose serialization
trace on these named paths; missing independent Q0-Q4 inputs remain unaccepted.

## 406. Bounded Native Recorder Owner Poses (2026-11-17)

From clean pushed8dd4404, bounded source trace confirms record_tick constructs a
detached three-coordinate native pose via unchanged _c1_array(...,(3,)) and float
copy. Yet five native retention/current/delivery owners sent arbitrary array
extents or non-array replacements to the generic binder. Original/closing owner
pose now uses one shared guard: exact native ndarray first, then existing C1
array shape/type/finite predicate. Shape rejects before object conversion; valid
metadata validation remains three coordinates. Generic binder/predicate stay
unchanged. This restores the existing producer shape, not a physical/numerical
bound, pose truth, transform or permitted-command claim.

Finite25/repaired25/related94<=60s each and one root<=360s; earlier spent
positions remain spent. First25 FAIL31.55s at prehash spies across five paths:
initial/closing2/4-element arrays plus initial list replacement. Repaired25
PASS1.44s; prior94 PASS2.62s/208 deselected, including eight goal report modes.
Delivery uses existing four-tick pending fixture/original capture/held-source
guard, not the rejected405 mutable-State fixture. <=4 preparation ticks and
<=2 observations/per-family intakes/matches; goal12/ToF64 digests unchanged.
History identity/exact words and both RNG states stay unchanged on rejection;
no partial outgoing source/frame/goal/pending/epoch/tick.

One360s root `python -m pytest -q --durations=10 && ruff check . && git diff --check`
PASS6352/known QDQ1 xfail/77 warnings203.20s, Ruff/whitespace PASS. Pylance syntax2/
format/AST/signature/call/hash/reference checks PASS. One four-line shared guard,
five owner bodies/one25-case test only; +1 guard call per body, other encoding/
intake/deepcopy/digest/report call censuses unchanged. Reused metadata validation
is not a new native expression stage. Logs/hashes retained in .git; no study,
data/dependency/download or C/runtime/board work. All flags false/guard UNKNOWN.
Next trace owning intake current-owner pre-copy/serialization correspondence;
independent accepted Q0-Q4 setup/source/coverage/error/clock/one-use inputs remain absent.

## Sources

[Complete original bibliography and reference definitions][original-review-sources].

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
[chapter-review-27]: docs/review/311-315.md
[chapter-review-28]: docs/review/316-320.md
[chapter-review-29]: docs/review/321-325.md
[chapter-review-30]: docs/review/326-330.md
[chapter-review-31]: docs/review/331-335.md
[chapter-review-32]: docs/review/336-340.md
[chapter-review-33]: docs/review/341-345.md
[chapter-review-34]: docs/review/346-350.md
[chapter-review-35]: docs/review/351-355.md
[chapter-review-36]: docs/review/356-360.md
[chapter-review-37]: docs/review/361-365.md
[chapter-review-38]: docs/review/366-370.md
[chapter-review-39]: docs/review/371-375.md
[chapter-review-40]: docs/review/376-380.md
[chapter-review-41]: docs/review/381-385.md
[chapter-review-42]: docs/review/386-390.md
[chapter-review-43]: docs/review/391-394.md
[chapter-review-44]: docs/review/395-396.md
[chapter-review-45]: docs/review/397-398.md
[chapter-review-46]: docs/review/399-400.md
[chapter-review-47]: docs/review/401-402.md
[cloud-harness-handoff]: docs/review/311-315.md#311-cloud-harness-handoff-and-restart-prompt-2026-11-12
[review-311-315-preserved-0]: docs/review/311-315.md#311-cloud-harness-handoff-and-restart-prompt-2026-11-12
[review-311-315-preserved-1]: docs/review/311-315.md#312-bounded-native-tof-postprocessing-recorder-retention-2026-11-12
[review-311-315-preserved-2]: docs/review/311-315.md#313-bounded-retained-native-tof-postprocessing-matching-2026-11-12
[review-311-315-preserved-3]: docs/review/311-315.md#314-closed-native-tof-postprocessing-delivery-publication-2026-11-12
[review-311-315-preserved-4]: docs/review/311-315.md#315-supplied-word-native-tof-noise-addition-discrepancies-2026-11-12
[review-316-320-preserved-0]: docs/review/316-320.md#316-intact-postprocessing-checkpoint-and-topic-relocation-2026-11-12
[review-316-320-preserved-1]: docs/review/316-320.md#317-matched-native-tof-noise-addition-reports-2026-11-12
[review-316-320-preserved-2]: docs/review/316-320.md#318-supplied-word-native-tof-dropout-mask-correspondence-2026-11-12
[review-316-320-preserved-3]: docs/review/316-320.md#319-matched-native-tof-dropout-reports-2026-11-12
[review-316-320-preserved-4]: docs/review/316-320.md#320-supplied-word-native-tof-clipselection-correspondence-2026-11-12
[review-321-325-preserved-0]: docs/review/321-325.md#321-matched-native-tof-clipselection-reports-2026-11-12
[review-321-325-preserved-1]: docs/review/321-325.md#322-intact-retention-and-delivery-checkpoint-archival-2026-11-12
[review-321-325-preserved-2]: docs/review/321-325.md#323-supplied-word-native-tof-selectedstorage-residuals-2026-11-12
[review-321-325-preserved-3]: docs/review/321-325.md#324-matched-native-tof-selectedstorage-reports-2026-11-12
[review-321-325-preserved-4]: docs/review/321-325.md#325-cold-native-goal-computation-source-2026-11-12
[review-326-330-preserved-0]: docs/review/326-330.md#326-native-goal-computation-acquisition-pairing-2026-11-12
[review-326-330-preserved-1]: docs/review/326-330.md#327-closed-native-goal-computation-intake-2026-11-12
[review-326-330-preserved-2]: docs/review/326-330.md#328-intact-goal-prerequisite-review-archival-2026-11-12
[review-326-330-preserved-3]: docs/review/326-330.md#329-typed-bounded-native-goal-computation-history-2026-11-12
[review-326-330-preserved-4]: docs/review/326-330.md#330-default-off-native-goal-recorder-retention-2026-11-12
[review-331-335-preserved-0]: docs/review/331-335.md#331-exact-retained-native-goal-matching-2026-11-12
[review-331-335-preserved-1]: docs/review/331-335.md#332-closed-default-off-native-goal-delivery-2026-11-12
[review-331-335-preserved-2]: docs/review/331-335.md#333-supplied-word-native-goal-delta-discrepancies-2026-11-12
[review-331-335-preserved-3]: docs/review/331-335.md#334-intact-native-goal-prerequisite-checkpoint-archival-2026-11-12
[review-331-335-preserved-4]: docs/review/331-335.md#335-matched-native-goal-delta-reports-wip-and-pause-2026-11-12
[review-336-340-preserved-0]: docs/review/336-340.md#336-current-state-review-and-native-goal-boundary-repairs-2026-11-13
[review-336-340-preserved-1]: docs/review/336-340.md#337-supplied-word-native-goal-expression-residuals-2026-11-13
[review-336-340-preserved-2]: docs/review/336-340.md#338-intact-goal-ownership-checkpoint-archival-2026-11-13
[review-336-340-preserved-3]: docs/review/336-340.md#339-matched-retained-native-goal-expression-reports-2026-11-13
[review-336-340-preserved-4]: docs/review/336-340.md#340-supplied-native-and-stored-goal-word-correspondence-2026-11-13
[review-341-345-preserved-0]: docs/review/341-345.md#341-matched-retained-goal-storage-reports-2026-11-13
[review-341-345-preserved-1]: docs/review/341-345.md#342-supplied-pre-integration-speed-update-residuals-2026-11-13
[review-341-345-preserved-2]: docs/review/341-345.md#343-supplied-target-and-yaw-clipping-correspondence-2026-11-13
[review-341-345-preserved-3]: docs/review/341-345.md#344-intact-goal-delivery-checkpoint-archival-2026-11-13
[review-341-345-preserved-4]: docs/review/341-345.md#345-closed-current-receipt-motion-update-reports-2026-11-13
[review-346-350-preserved-0]: docs/review/346-350.md#346-supplied-captured-interval-division-residuals-2026-11-13
[review-346-350-preserved-1]: docs/review/346-350.md#347-intact-motion-word-contract-relocation-2026-11-13
[review-346-350-preserved-2]: docs/review/346-350.md#348-intact-reviewed-goal-expression-checkpoint-archival-2026-11-13
[review-346-350-preserved-3]: docs/review/346-350.md#349-closed-current-receipt-interval-reports-2026-11-13
[review-346-350-preserved-4]: docs/review/346-350.md#350-supplied-unrounded-segment-count-comparison-2026-11-13
[review-351-355-preserved-0]: docs/review/351-355.md#351-closed-current-segment-selection-reports-2026-11-13
[review-351-355-preserved-1]: docs/review/351-355.md#352-native-integration-closing-observation-repairs-2026-11-13
[review-351-355-preserved-2]: docs/review/351-355.md#353-intact-motion-and-goal-checkpoint-archival-2026-11-13
[review-351-355-preserved-3]: docs/review/351-355.md#354-closed-live-receipt-owned-request-joins-2026-11-13
[review-351-355-preserved-4]: docs/review/351-355.md#355-checked-remaining-acceptance-blockers-2026-11-13
[review-356-360-preserved-0]: docs/review/356-360.md#356-actual-intake-closing-observation-repairs-2026-11-13
[review-356-360-preserved-1]: docs/review/356-360.md#357-intact-motion-checkpoint-archival-2026-11-13
[review-356-360-preserved-2]: docs/review/356-360.md#358-closed-actual-initial-tick-setup-correspondence-2026-11-13
[review-356-360-preserved-3]: docs/review/356-360.md#359-closed-initial-setup-report-consumer-metadata-2026-11-13
[review-356-360-preserved-4]: docs/review/356-360.md#360-intact-source-and-consumer-checkpoint-archival-2026-11-13
[review-361-365-preserved-0]: docs/review/361-365.md#361-bounded-initial-source-retention-2026-11-13
[review-361-365-preserved-1]: docs/review/361-365.md#362-bounded-retained-initial-source-reading-2026-11-16
[review-361-365-preserved-2]: docs/review/361-365.md#363-conditional-owned-initial-rest-startup-2026-11-16
[review-361-365-preserved-3]: docs/review/361-365.md#364-intact-initial-source-checkpoint-archival-2026-11-16
[review-361-365-preserved-4]: docs/review/361-365.md#365-supplied-normalization-division-residuals-2026-11-16
[review-366-370-preserved-0]: docs/review/366-370.md#366-closed-current-later-period-comparisons-2026-11-16
[review-366-370-preserved-1]: docs/review/366-370.md#367-actual-consumed-normalization-divisor-retention-2026-11-16
[review-366-370-preserved-2]: docs/review/366-370.md#368-intact-initial-source-checkpoint-archival-2026-11-16
[review-366-370-preserved-3]: docs/review/366-370.md#369-closed-actual-consumed-quotient-joins-2026-11-16
[review-366-370-preserved-4]: docs/review/366-370.md#370-actual-heading-shift-and-return-operand-retention-2026-11-16
[review-371-375-preserved-0]: docs/review/371-375.md#371-supplied-heading-shift-and-return-residuals-2026-11-16
[review-371-375-preserved-1]: docs/review/371-375.md#372-intact-normalization-checkpoint-archival-2026-11-16
[review-371-375-preserved-2]: docs/review/371-375.md#373-closed-current-heading-offset-reports-2026-11-16
[review-371-375-preserved-3]: docs/review/371-375.md#374-closed-default-native-reader-epoch-identities-2026-11-16
[review-371-375-preserved-4]: docs/review/371-375.md#375-closed-owning-receipt-epoch-identities-2026-11-16
[review-376-380-preserved-0]: docs/review/376-380.md#376-intact-heading-and-receipt-checkpoint-archival-2026-11-16
[review-376-380-preserved-1]: docs/review/376-380.md#377-closed-live-request-consumer-epochs-2026-11-16
[review-376-380-preserved-2]: docs/review/376-380.md#378-supplied-heading-remainder-word-residuals-2026-11-16
[review-376-380-preserved-3]: docs/review/376-380.md#379-closed-current-heading-remainder-joins-2026-11-16
[review-376-380-preserved-4]: docs/review/376-380.md#380-intact-native-word-topic-relocation-2026-11-16
[review-381-385-preserved-0]: docs/review/381-385.md#381-intact-consumer-and-remainder-checkpoint-archival-2026-11-16
[review-381-385-preserved-1]: docs/review/381-385.md#382-fresh-remaining-evidence-blockers-2026-11-16
[review-381-385-preserved-2]: docs/review/381-385.md#383-closed-current-native-tof-source-sampling-2026-11-16
[review-381-385-preserved-3]: docs/review/381-385.md#384-closed-native-tof-delivery-report-work-2026-11-17
[review-381-385-preserved-4]: docs/review/381-385.md#385-closed-fresh-native-tof-retention-sampling-2026-11-17
[review-386-390-preserved-0]: docs/review/386-390.md#386-intact-source-pipeline-checkpoint-archival-2026-11-17
[review-386-390-preserved-1]: docs/review/386-390.md#387-closed-native-goal-dynamics-sampling-2026-11-17
[review-386-390-preserved-2]: docs/review/386-390.md#388-current-source-queue-evidence-blockers-2026-11-17
[review-386-390-preserved-3]: docs/review/386-390.md#389-closed-composed-native-and-receipt-cache-identities-2026-11-17
[review-386-390-preserved-4]: docs/review/386-390.md#390-closed-live-request-receipt-cache-identity-2026-11-17
[review-391-394-preserved-0]: docs/review/391-394.md#391-closed-conditional-startup-receipt-cache-identity-2026-11-17
[review-391-394-preserved-1]: docs/review/391-394.md#392-intact-composed-source-checkpoint-archival-2026-11-17
[review-391-394-preserved-2]: docs/review/391-394.md#393-closed-owning-intake-original-and-final-sampling-2026-11-17
[review-391-394-preserved-3]: docs/review/391-394.md#394-closed-post-native-receipt-and-pending-copies-2026-11-17
[review-395-396-preserved-0]: docs/review/395-396.md#395-intact-owning-intake-checkpoint-archival-2026-11-17
[review-395-396-preserved-1]: docs/review/395-396.md#396-closed-native-tof-retention-owner-layouts-2026-11-17
[review-397-398-preserved-0]: docs/review/397-398.md#397-intact-retentionlayout-checkpoint-archival-2026-11-17
[review-397-398-preserved-1]: docs/review/397-398.md#398-closed-native-tof-snapshot-owner-layouts-2026-11-17
[review-399-400-preserved-0]: docs/review/399-400.md#399-intact-snapshot-ownership-checkpoint-archival-2026-11-17
[review-399-400-preserved-1]: docs/review/399-400.md#400-fixed-native-tof-owner-frame-extents-2026-11-17
[review-401-402-preserved-0]: docs/review/401-402.md#401-intact-frame-boundary-checkpoint-archival-2026-11-17
[review-401-402-preserved-1]: docs/review/401-402.md#402-codec-state-prevalidation-before-tof-owner-copying-2026-11-17
[original-review-sources]: docs/review/sources.md#sources
