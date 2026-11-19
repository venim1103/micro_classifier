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
- [Checkpoints 403-407][chapter-review-48]
- [Checkpoints 408-412][chapter-review-49]
- [Checkpoints 413-417][chapter-review-50]

Checkpoints 418 onward remain below. The original source bibliography is linked
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

[Complete unchanged checkpoint][review-403-407-preserved-0] is preserved in the archive.

## 404. Closed Native Goal Owner Prevalidation (2026-11-17)

[Complete unchanged checkpoint][review-403-407-preserved-1] is preserved in the archive.

## 405. Closed Current ToF Post-Observation Owners (2026-11-17)

[Complete unchanged checkpoint][review-403-407-preserved-2] is preserved in the archive.

## 406. Bounded Native Recorder Owner Poses (2026-11-17)

[Complete unchanged checkpoint][review-403-407-preserved-3] is preserved in the archive.

## 407. Owning Intake Owner Prevalidation (2026-11-17)

[Complete unchanged checkpoint][review-403-407-preserved-4] is preserved in the archive.

## 408. Intact Owner Preflight Checkpoint Archival (2026-11-17)

[Complete unchanged checkpoint][review-408-412-preserved-0] is preserved in the archive.

## 409. Closed Receipt and Integration Snapshot Owner Preflight (2026-11-17)

[Complete unchanged checkpoint][review-408-412-preserved-1] is preserved in the archive.

## 410. Closed Initial Source and Startup Owner Preflight (2026-11-17)

[Complete unchanged checkpoint][review-408-412-preserved-2] is preserved in the archive.

## 411. Closed Opted-In Request Owner Preflight (2026-11-17)

[Complete unchanged checkpoint][review-408-412-preserved-3] is preserved in the archive.

## 412. Intact Initial Source and Receipt Topic Relocation (2026-11-17)

[Complete unchanged checkpoint][review-408-412-preserved-4] is preserved in the archive.

## 413. Closed Initial Retention Owner Word Joins (2026-11-17)

[Complete unchanged checkpoint][review-413-417-preserved-0] is preserved in the archive.

## 414. Fresh Named Queue Evidence and Tool Blockers (2026-11-17)

[Complete unchanged checkpoint][review-413-417-preserved-1] is preserved in the archive.

## 415. Bounded Receipt History Prehash Validation (2026-11-17)

[Complete unchanged checkpoint][review-413-417-preserved-2] is preserved in the archive.

## 416. Closed Owning Intake History Root Hashes (2026-11-17)

[Complete unchanged checkpoint][review-413-417-preserved-3] is preserved in the archive.

## 417. Closed Post-Observation History Consumption (2026-11-17)

[Complete unchanged checkpoint][review-413-417-preserved-4] is preserved in the archive.

## 418. Intact History Checkpoints and Named Input Blockers (2026-11-17)

From clean pushed2c1d02e, one30s guarded transform/three original snapshots move
whole408-412 checkpoints to the linked archive. Exact144-line body, all five
historical root headings/anchors, three inverse layouts, four chapter01/06
targets and148 original first-definition meanings PASS. Root981->864 lines before
this note; failures, spent positions and evidence limits are preserved.
Scoped references/targets/anchors, whitespace and all four417 tested hashes
PASS. Documentation-only; no code suite rerun. Latest root remains6498/known QDQ1
xfail/77 warnings209.46s, with Ruff/format/syntax/whitespace and scoped controls.

Rechecked actual design §§1/12 and S1-S5/Q0-Q5 dependencies after the bounded
history-root trace. All identified intake/reader root prehash and first-consumption
gaps are closed; no further concrete compatible edit is identified in that trace.
Q0 independent setup/source/return/coverage, Q1 propagated actual-state error,
Q2 uniform full-command native/accumulated error, Q3 pose/range/time/transform and
Q4 qualified clock/application/serialized one-use/receipt/predecessor inputs remain
absent. Conditional tools cannot supply their acceptance or a command permit.
stedgeai/stm32ai/STM32_Programmer_CLI are not on PATH; cc/arm-none-eabi-gcc are.
Licence/tools/board work stays user-side; new qualification studies, SC18/general
audits, D4/learned/model/dependency/download/hardware work remain protected/deferred.

Eight flags false, guard UNKNOWN. Current blockers are actual independent inputs/
authority, not routine approval/accounting or a permanent no-prerequisite claim.
Next is an independently supported named packet or concrete compatible issue,
not more completed reports, dummy work or an unchanged green gate. Session layouts/
transform and .git logs remain nonportable; committed bodies/controls carry the
handoff without renewing authority or qualifying metadata.

## 419. Closed Original Native ToF History Sampling (2026-11-18)

Fresh actual continuation from clean pushede1de171 verified main/upstream0:0,
terminal Python3.12.3 at /opt/venv/bin/python, Ruff0.17.0 and361GiB available.
Host/Arm compilers remain present; ST executables absent. The native-ToF
retainer validated base acquisition history at entry but fingerprinted it only
after the first producer observation/intake. Unlike timing/auxiliary history,
valid-shape deletion or older sample-word mutation could become its baseline.
Move that existing digest before the first observation beside timing's digest.

Finite4 synthetic repro/repaired controls<=60s, nearby retention controls<=60s,
one root<=360s, syntax/format/AST/hash/links. Fresh/dedup x deletion/older word
mutation:4FAIL5.54s (silent success), then4PASS1.27s. Two bounded prior captures
at4/6 and optional fresh8 use existing source fixtures. Existing140PASS9.19s,
including optional trace families, dedup/trim/gap and owner-layout controls.
Two observations/intakes and64 digests remain the default ceilings; no replay/
clock/RNG draw, partial recorder publication or rollback of external mutation.

Required root `python -m pytest -q --durations=10 && ruff check . &&
git diff --check`, one360s wrapper PASS6502/known QDQ1 xfail/77 warnings183.53s,
then Ruff/whitespace PASS. Pylance syntax, changed format, exact source AST after
only existing-digest relocation, unchanged signatures/all previous test AST and
four tested hashes PASS. No code change to source arithmetic, fixture defaults,
intake/report/copy/digest counts, work limits, retention gaps or qualification.

Eight flags false, guard UNKNOWN; independent Q0-Q4 inputs remain absent and
protected boundaries unchanged. Local .git logs/hash bracket are nonportable;
committed controls retain results and spent positions. Next trace corresponding
current/delivered snapshots' original acquisition-history joins; this is the same
named source path, not a general audit or another numerical report.

## 420. Closed Current ToF Original History Joins (2026-11-18)

From clean pushed3c15a9f, the corresponding current-source snapshot also
fingerprinted base history only after its first producer observation/intake.
Its existing current snapshot test now clears the archive or mutates a sample
word during the first observation:2FAIL5.12s (false availability), then2PASS0.59s.
Reuse the existing independent history template before observing, move the
existing layout check/hash there, and retain later exact live-source matching.
Delivered snapshots already establish owner/base/optional-history fingerprints
before first observation; no delivery code change or new report follows.

Finite2 repro/repaired controls<=60s, existing nearby selectors<=60s, one
root<=360s and syntax/format/AST/hash/links. Existing current/delivered/pending/
layout/history74PASS4.09s, including malformed retained-word prehash rejection.
Original2 observations/intakes/64 digests, unknown without partial source/frame,
false flags, external mutation retention and unchanged tick/RNG remain checked.
The only new helper call constructs the already-bounded independent template;
no observation/intake/copy/digest/report or source arithmetic call is added.

Required root `python -m pytest -q --durations=10 && ruff check . &&
git diff --check`, one360s wrapper PASS6504/known QDQ1 xfail/77 warnings194.45s,
then Ruff/whitespace PASS. Pylance syntax, changed format, exact source/template/
layout/hash delta, unchanged signatures/every other source/test function and four
tested hashes PASS. Local .git logs/hash bracket are nonportable; committed
controls preserve actual results and spent positions. Eight flags false,
guard UNKNOWN; no independent Q0-Q4 acceptance or protected action.
Next trace this current reader's original owner-context binding, which still
follows its first sample; do not broaden to unrelated audits or invent evidence.

## 421. Closed Current ToF Original Owner Contexts (2026-11-18)

From clean pushed66e8a86, this current-source reader's first observation could
change recorder binding/profile before its original owner fingerprint. Two new
cases in the existing snapshot test:2FAIL5.75s (false availability), then
2PASS1.02s after moving that existing digest before the first observation.
An independent bounded layout check of the retained source precedes that hash,
preserving unsupported retained-word rejection before owner serialization.

Finite2 repro/repaired controls<=60s, related owner/prehash controls<=60s, one
root<=360s and syntax/format/AST/hash/links. First related89:4FAIL/85PASS3.93s.
Moving the digest had also moved its cheap mid-read owner validation; four
phase1 current/frame/age/vector controls then rejected only after observation2.
Do not weaken those assertions. Reuse the shared actual-current preflight and
original tuple-identity check at the old binding point. Revised necessary
four failed controls/new2 PASS6/0.63s; related89PASS2.74s. All original fail-fast
semantics,2 observations/intakes/64 digests, unknown-without-partial source/frame,
false flags, external mutation retention and unchanged tick/RNG remain.

Required root `python -m pytest -q --durations=10 && ruff check . &&
git diff --check`, one360s wrapper PASS6506/known QDQ1 xfail/77 warnings173.55s,
then Ruff/whitespace PASS. Pylance syntax, changed format, exact source/preflight/
owner-move/mid-read-guard AST delta, unchanged signatures/every other source/test
function and four tested hashes PASS. No new observation/native read/copy/digest/
report/math/RNG/clock, work cap, domain or qualification. Eight flags false,
guard UNKNOWN; independent Q0-Q4 inputs remain absent.

Local .git logs/hash bracket are nonportable; committed controls preserve all
failures, repairs and spent positions. Next prevalidate this same reader's closing
history before hashing, then archive whole413-417 before further review growth.

## 422. Closed Current ToF History Prehash and Intact Checkpoints (2026-11-18)

From clean pushedd16119c, the same current-source reader hashed closing history
without revalidating its layout after the final observation/intake. Two added
nine-entry/ndarray9 closing roots hit the prehash spy:2FAIL4.43s, then2PASS0.58s.
Reuse its existing independent template/layout predicate immediately before
closing hashes. No new sample/intake/copy/digest/report, work cap or domain.
Finite2 repro/repaired controls<=60s, nearby selectors<=60s, one root<=360s
and syntax/format/AST/hash/links. Existing current/history/delivery/pending
66PASS3.48s. Unknown omits source/frame, false flags and2 observations/intakes/
64 digests remain, with no replay/RNG/clock or mutation rollback.

Required root `python -m pytest -q --durations=10 && ruff check . &&
git diff --check`, one360s wrapper PASS6508/known QDQ1 xfail/77 warnings199.20s,
then Ruff/whitespace PASS. Pylance syntax, changed format, exact one-call source
AST delta, unchanged signatures/every other source/test function and four
tested hashes PASS. Local .git logs retain all spent positions; no gate rerun.

Before adding this note, one30s guarded transform/two original snapshots archive
whole413-417 intact: exact156-line body, all five root headings/anchors, two inverse
layouts, four chapter06 targets and154 original first-definition meanings PASS.
Root984->855 lines before this note. Scoped link/target/anchor/whitespace checks
and unchanged422 tested hashes PASS; no code suite rerun for documentation.
Session layouts/transform and local logs remain nonportable; committed contracts,
controls and complete archived failures/ledgers preserve the portable handoff.

Rechecked actual priority map and Q0-Q5 packet after this original/closing native
ToF source trace. No further concrete compatible issue identified in that trace.
Q0 independent setup/source/return/coverage, Q1 propagated actual-state error,
Q2 uniform full-command native/accumulated error, Q3 pose/range/time/transform and
Q4 qualified clock/application/serialized one-use/receipt/predecessor inputs remain
absent. ST executables remain off PATH; licence/tools/board work stays user-side.
Protected qualification studies/SC18/general audits/D4/learned/dependencies/
downloads/hardware are not substitute work. Eight flags false, guard UNKNOWN.
Next is actual independent named evidence or a concrete compatible issue, not
more report/hash packages, routine approval or an unchanged green gate.

## 423. Prehash Validation for Closing ToF Delivery Traces (2026-11-19)

Fresh continuation from clean pushed512d909, main/upstream0:0, verified terminal
Python3.12.3, Ruff0.17.0 and362GiB available. Final observation could expand a
retained selection/wall/cylinder/direction/postprocessing list in place, reaching
its individual closing fingerprint before bounded owner validation. Timing
already preflights its live retained list and is unchanged. The final repair
defers exactly those five comparisons until after the unchanged late compound
preflight. Output/identity checks, default mode, sample/match/copy/digest sites
and work ceilings stay intact.

Finite focused controls/related selectors<=60s each, roots<=360s each. Five
nine-entry observation repros FAIL4.95s; first repair5PASS0.82s, related366PASS
44.60s and root6513/known QDQ1 xfail/77 warnings223.91s with Ruff/whitespace PASS.
Inspection found that moving preflight earlier lost protection after the final
dynamics refresh. Five new controls at that boundary FAIL4.35s on the first
repair. Revised plan defers the hashes instead, preserves the late guard and
requires fresh focused/related/root gates. Final10PASS0.94s, related366PASS36.21s;
root `python -m pytest -q --durations=10 && ruff check . && git diff --check`
PASS6518/known QDQ1 xfail/77 warnings187.75s, then Ruff/whitespace PASS.

Pylance syntax, changed format, exact five comparison moves/unchanged original
test AST, tested hashes and scoped reference PASS. Unknown has no partial
payload, retains all eight false flags and leaves externally changed histories
untouched. No replay, extra RNG, clocks, new report or independent acceptance.
Guard UNKNOWN; Q0-Q4 and user-side ST boundaries remain as in422. Local logs
retain spent checks and are nonportable. Continue only on a concrete compatible
source issue or independently supported named evidence.

## 424. Preflight Live ToF Histories Before Retention Staging (2026-11-19)

From clean pushed555771c, the first observation could replace any of six
optional histories after owner preflight but before the retainer copied entries.
The staged-list check rejected too late. Move the six redundant entry checks
to after the first live intake and base history layout check, before staging.
Original and closing owner preflights remain. Capture-option defaults, gaps,
deduplication and trimming stay unchanged.

Finite6 repro/repaired controls<=60s, nearby selectors<=60s, one root<=360s.
Nine-entry replacements reached forbidden deepcopy in all six families:
6FAIL4.41s. The first focused chain stopped at formatting before pytest; only a
blank line was missing. Repaired6PASS0.68s, prior144PASS8.34s. Invalid history
exits after one observation/intake with no publication or mutation rollback.
Required root `python -m pytest -q --durations=10 && ruff check . &&
git diff --check` PASS6524/known QDQ1 xfail/77 warnings183.54s, then
Ruff/whitespace PASS. Pylance syntax, changed format, exact six validator moves,
unchanged prior test AST, tested hashes and scoped reference PASS.

No sample/intake/copy/digest/report or work cap added; no replay, extra RNG,
clock or qualification. All eight flags false, guard UNKNOWN. Local logs
retain spent checks and are nonportable. The remaining queue still requires
independently supported named evidence or another concrete compatible issue;
no tool, hardware or study scope follows.

## 425. Preflight Retention History After Final Refresh (2026-11-19)

From clean pushed530000f, the closing ToF retainer validated both histories before
its final dynamics word refresh and inside the compound owner check, but hashed
the base and timing histories individually before that last check. Move the
existing compound owner comparison ahead of those two hashes. Both reject
unsupported refreshed roots before serialization; staged publication is unchanged.

Finite2 repro/repaired controls<=60s, nearby selectors<=60s and one root<=360s.
Nine-entry replacements after the final refresh reached the direct digest in
both cases:2FAIL4.27s, then2PASS0.59s. Prior142PASS8.30s. Two observations,
two native intakes and existing digest ceilings remain, without partial
publication, rollback, replay, clock or RNG changes. Required root
`python -m pytest -q --durations=10 && ruff check . && git diff --check`
PASS6526/known QDQ1 xfail/77 warnings180.84s, then Ruff/whitespace PASS.
Pylance syntax, changed format, exact comparison move, unchanged existing
test AST, tested hashes and scoped reference PASS.

Eight flags false, guard UNKNOWN. No new bounds, samples, reports or qualification.
Local logs retain all spent checks. Next trace the corresponding delivery
base/timing hashes downstream of the final refresh.

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
[chapter-review-48]: docs/review/403-407.md
[chapter-review-49]: docs/review/408-412.md
[chapter-review-50]: docs/review/413-417.md
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
[review-403-407-preserved-0]: docs/review/403-407.md#403-intact-state-checkpoints-and-original-sources-2026-11-17
[review-403-407-preserved-1]: docs/review/403-407.md#404-closed-native-goal-owner-prevalidation-2026-11-17
[review-403-407-preserved-2]: docs/review/403-407.md#405-closed-current-tof-post-observation-owners-2026-11-17
[review-403-407-preserved-3]: docs/review/403-407.md#406-bounded-native-recorder-owner-poses-2026-11-17
[review-403-407-preserved-4]: docs/review/403-407.md#407-owning-intake-owner-prevalidation-2026-11-17
[review-408-412-preserved-0]: docs/review/408-412.md#408-intact-owner-preflight-checkpoint-archival-2026-11-17
[review-408-412-preserved-1]: docs/review/408-412.md#409-closed-receipt-and-integration-snapshot-owner-preflight-2026-11-17
[review-408-412-preserved-2]: docs/review/408-412.md#410-closed-initial-source-and-startup-owner-preflight-2026-11-17
[review-408-412-preserved-3]: docs/review/408-412.md#411-closed-opted-in-request-owner-preflight-2026-11-17
[review-408-412-preserved-4]: docs/review/408-412.md#412-intact-initial-source-and-receipt-topic-relocation-2026-11-17
[review-413-417-preserved-0]: docs/review/413-417.md#413-closed-initial-retention-owner-word-joins-2026-11-17
[review-413-417-preserved-1]: docs/review/413-417.md#414-fresh-named-queue-evidence-and-tool-blockers-2026-11-17
[review-413-417-preserved-2]: docs/review/413-417.md#415-bounded-receipt-history-prehash-validation-2026-11-17
[review-413-417-preserved-3]: docs/review/413-417.md#416-closed-owning-intake-history-root-hashes-2026-11-17
[review-413-417-preserved-4]: docs/review/413-417.md#417-closed-post-observation-history-consumption-2026-11-17
