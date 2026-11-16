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

Checkpoints 361 onward and the source bibliography remain below.
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

Begin clean pushed38ab59e. One bounded explicit-workspace compatibility probe of
actual initial setup/frame and delivered startup history fails IndexError before
consumer entry: history empty. A narrow actual-layout diagnostic PASS shows C1
ToF latency2,current0,history0,latestNone,pending delivery[2]. Goal odometry latency0
is a different source; do not generalize it or retimestamp/implicitly advance.
Both finite probe positions remain spent; no native/command consumer ran.

Implement separate strict opt-in retain_initial_setup_source: at most one
detached complete initial snapshot, original pinned producer/owner RNG identities,
exact supported metadata and original/copy/closing source/setup/frame/profile
joins. Exact repeated content deduplicates without replacement; wrong/stale/
changed content rejects and preserves prior published data except external
mutations, which are not rolled back. Ordinary intake/snapshot output unchanged.

Fresh12 controls/60s, one necessary repair reserve12/60s, root/360s. First12
PASS4.09s/5006 deselected, root PASS5941/known QDQ1 xfail/77 warnings199.41s.
Root Ruff/whitespace/four tested hashes/exact default-empty slot/unrelated
source/control AST PASS. Changed format rejects two new wrapped lines; existing
formatter repairs them, final format PASS; no repeated green focused controls.
Per call<=2 initial reads/4 observations/2 setup audits/84 digests; duplicates
are bounded separately. RNG states unchanged, forbidden calls0. All positions
spent; no fixture/work/safety limit relaxed.

All eight flags false; no replay/draw/capture/clock/model/study/dependency/download/
native/Arm/hardware work. One private snapshot is not accepted setup/geometry/
coverage/error/timing or measured memory fit, a reset receipt, current initial
state, later delivery or an admitted predecessor. Ignored `.git/returns-361-*`
focused/root/hash logs retained; tool-returned compatibility/layout evidence is
summarized here, not assumed portable editor memory. Next implement bounded
retained initial-source reading before conditional later-delivery consumption.

## 362. Bounded Retained Initial Source Reading (2026-11-16)

Begin clean pushedcbc52f7. Add strict opt-in snapshot_retained_initial_setup_source
for one actual tick0 record under its actual current owner. Share exact initial
metadata/source/frame validation with retention and unchanged original owner-word
predicate with initial reading. Close original/copy/closing retained source and
current dynamics/pose/native State/frame/profile, source files and pinned producer/
owner RNG references. Full owned dynamics closure preserves optional intake groups;
basic current sampling projects only its existing seven fields. Output separately
labels initial/current tick/frame; all eight flags stay false.

Fresh18 controls/60s, one necessary repair reserve18/60s, root/360s. First18
PASS4.35s/5018 deselected; exact owner-word predicate/unrelated source/control AST
PASS. Fixture preparation uses one retained initial environment and exactly two
at-rest receipt steps for one actual delivered environment, not study episodes.
Read bounds: two observations/64 digests/no setup auditor, replay, capture, draw
or clock. Original/closing equal-state RNG replacement, malformed owners, stale
pose, retained/copy/frame/flag mutations and detached output covered. Ruff PASS;
format rejects new wraps, formatter repairs them, final format/whitespace PASS;
no repeated green focused gate.

First root tool interrupted: no live tool session or pytest/timeout/tee process
remains;5549-byte log ends around82% with NUL tail. It is spent/unknown, not a
pass, successful chain exit or refunded position. Four tested source hashes and
format/whitespace still PASS. Fresh required recovery root/360s with separate
hash/log PASS5959/known QDQ1 xfail/77 warnings209.56s; root Ruff/whitespace/four
hashes PASS. Both root positions retained separately; no protected allowance or
assertion/work limit changed.

No accepted setup/geometry/coverage/error/clock, later exact-rest/delivery,
reset receipt, one-use executor or admitted predecessor follows. No native/Arm/
model/study/dependency/download/hardware action. Ignored `.git/returns-362-*`
focused/interrupted/root/recovery/hash records retained, never assumed portable.
Next trace conditional later delivery and complete owned initial-rest State/frame
history without inventing missing accepted evidence.

## 363. Conditional Owned Initial-Rest Startup (2026-11-16)

Begin clean pushed82d04b7. Fresh bounded compatibility probe PASS0.195267s:
actual retained initial source/current receipts available, native State sequences
0/1/2, unchanged consumer conditionally excludes fixed startup with work1 setup/
3 rest/1 command; all seven consumer flags false. Zero fixture error/margin/history
premises are assumptions, not evidence acceptance.

Implement strict opt-in probe_initial_startup_path deriving actual owned initial
setup/epoch/pose, delivered tick0 C1 event and complete State/frame history from
validated live receipts. No caller setup/capture/tick/pose/frame/history override.
Keep existing conditional point/error/profile premises, fixed request, exact-rest
rejection and all source/clock/geometry/error/admission limits. Original/copied/
closing source/receipt/event/evidence/report bindings and pinned epoch references
must close before detached publication. All eight flags false, guard UNKNOWN.

Fresh16/60s, necessary fixture repair<=16/60s, root360s. First16:8 PASS/8 FAIL18.58s,
overbroad global math monkeypatch catches existing history inspection's reference
tof_directions -> math.cos, not producer replay. Read owning code; fixture-only
repair counts one existing inspection/eight source=None reference directions.
Producer step/reset/integration/ToF acquisition/capture/clock/collection still
forbidden; no reference/native-transform law adopted. Rerun only failed8:
PASS5.47s/5044 deselected. Fresh actualtick3/rejectedtick4 endpoints2/60s
PASS4.80s/5052 deselected. Fixture preparation totals five bounded receipt steps:
two original at-rest, two additional moving controls, one additional upper-domain
at-rest; not study episodes. First required root PASS5977/known QDQ1 xfail/
77 warnings198.51s; hashes/style/unrelated source/API/default/consumer/control AST
PASS. No unchanged green focused gate repeated.

Before checkpoint, a concrete consumer-input closure question exposes introduced
false success: derived State/frame evidence or detached capture mutates after
consumer return without binding recheck. Two controls FAIL5.61s/5054 deselected.
Bind both copied consumer inputs before work and after closing live source reads;
necessary repair2/60s PASS0.84s/5054 deselected. Substantive-repair root360s
PASS5979/known1 xfail/77 warnings185.89s; root Ruff/changed format/whitespace/fresh
four-hash bracket PASS. Both root/failure positions remain spent; no tolerance,
assertion or safety/work threshold relaxed.

Bounds per join: two retained/two receipt reads/eight observations/two history
checks/one setup audit/one consumer/256 digests, existing command/path/cell limits.
No native/Arm/model/study/dependency/download/hardware action or admitted launch.
Ignored `.git/returns-363-*` focused/failure/repair/endpoint/root/hash evidence
retained separately. Next reassess named source/coverage/native-error prerequisites,
not a matching-hash permit, repeated successful gate or general audit.

## 364. Intact Initial Source Checkpoint Archival (2026-11-16)

Begin clean pushed24afbe0. Move whole356-360 blocks/headings/separators intact,
preserving actual intake closure, both introduced initial-reader faults and all
first/repair/root/spent positions, consumer metadata failures, actual renewed
continuation and prior archival ledgers. Five original root anchors and three
chapter01 references remain/rebase; body blocks contain no reference or inline
links needing copied definitions. One bounded exact whole-block/header/topic/
nine-target/anchor/four-tested-hash/whitespace check PASS. No code or green suite
rerun. Root remains below1,000 lines. Two original snapshots and bulk utility stay
in the session folder, not assumed portable evidence. Next investigate a named Q2
supplied-word normalization quotient prerequisite; do not relabel the later
period word as a captured earlier divisor, extend the existing ten-stage contract,
adopt pi/trig/sinc laws or invent a uniform error bound.

## 365. Supplied Normalization Division Residuals (2026-11-16)

Begin clean pushed1006705. Q2 native integration retains angle and normalized
sinc argument, but the divisor expression's earlier word is not separately
captured; later period_rad must not be relabeled as that capture. Add only a
standalone supplied-angle/divisor/argument quotient comparison using existing
bounded _C1CommandArithmetic. No pi/normalization/sinc/trig law or native replay.
Existing ten-stage integration source/arithmetic/unsupported contracts unchanged.

Fresh16/60s, one necessary repair reserve16/60s, root360s. First16 PASS4.59s/
5056 deselected; root PASS5995/known QDQ1 xfail/77 warnings215.68s. Root Ruff/
changed format/whitespace/four tested hashes/all prior source/API/default/consumer/
control AST PASS. No failed or repeated green gate. Finite work exactly3 values/
2 binary operations with existing4096-bit growth cap and32-character canonical
words. Direct Fraction oracles cover nonzero residual, negative words, opposite
zero words and subnormal quotient underflow. Zero divisor/malformed/overlong/
permission/budget faults raise; canonical raw infinities/nan stay unknown with
both ratios None and zero arithmetic, not a success fallback.

All eight flags false; no consumed-divisor identity, accepted source/numerical/
geometry/error/clock or admission follows. No native/Arm/model/study/dependency/
download/hardware action. Ignored `.git/returns-365-*` focused/root/hash evidence
retained. Next trace independently supportable native source correspondence; no
later-period substitution, duplicate integration report or guessed error bound.

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
[native-tof-ray-design]: docs/design/07-data-and-distillation-design-01.md#native-tof-ray-generation-prerequisites-2026-11-11
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
