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

Checkpoints 236 onward and the source bibliography remain below.
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

## 236. Bounded Native ToF Wall Recorder Retention (2026-11-10)

Checkpoint `61e3a44` pushed/clean. Local hypothesis: a separate literal wall
retention opt-in can stage typed wall records with already matched original
native acquisition IDs, deduplicate equal repeats and trim against the existing
eight-entry native window. Existing typed native/selection/timing checks remain;
wall layout preflight precedes ownership/outgoing hashes. Collect all closing
wall/selection/timing probes before companion comparisons, recheck typed live/
staged histories and owner/producer/cache/history identity before one final
assignment. This does not publish delivery, qualify sources/geometry/coverage/
physical/numerical/clock/permission or admit commands; all eight flags false.

Sixteen synthetic controls with original parent fixtures unchanged. Per case
at most13 geometry evaluations/14 ordinary recorder reads/10 retention attempts,
20 wall intakes/40 native intakes (combined timing+selection case instead at
most10 native),256 binding calls; only combined capture uses two setup clocks.
During retention zero recorder reads/step/reset/geometry/replay/clock/RNG. Fixed
8native/8wall/4wall-candidate/64ray and canonical word caps unchanged. Three
pytest positions counting failures/aborts: first16/60 seconds, one necessary
control/repair reserve, final root/300 seconds. Preserve logs starting
`wall-236-focused-1.log` in the local recovery directory; no study/model/data/
dependency/download/firmware/Arm/board/hardware work or old ledger refund.

First sixteen passed,2404 deselected,1.93 s. Integration review found the
native-history entry guard checks layout rather than canonical common words;
wall-history common-word equality alone could therefore hash a jointly changed
noncanonical native/wall word. Add canonical ray/floor/final word validation to
the owning wall-history helper and one prehash binding-count regression. The
same maximum12896 parse cap covers the added common-word checks. Narrowly revise
the reserved focused position to17 retention+16 affected layout controls (33),
same60 seconds and per-case resource caps; final root position unchanged.
This is necessary shared-guard repair, not a standalone rerun of235 or an old
ledger refund. Retain `wall-236-focused-2.log`; no failure/abort so far.

Strengthened affected33 passed,2388 deselected,4.03 s, including the joint-word
prehash rejection. Formatting then Ruff stopped on SIM102 in the moved nested
selection guard; no format-check/root command ran after that lint failure.
Manually merge only the equivalent short-circuit guard, then rerun the same
focused style check before the unused final root position. Retain this style
failure; no pytest position is refunded or new standalone run authorized.

Equivalent guard repair passed the same focused Ruff/format/whitespace checks.
Final required root gate:3344 passed,1 known transformer QDQ xfailed,71 warnings,
71.05 s; root Ruff, changed-file format check and whitespace passed. All three
pytest positions spent, no pytest failure/abort; the separate lint failure is
retained above. Editor diagnostics clear. Pylance resolved no retention callers;
this is not static compatibility evidence. Runtime controls cover the new
keyword and combined path. AST comparison confines production changes to
initialization, retention and the shared canonical-word guard, plus one new
test; all other source/test nodes unchanged. No additional C/Arm/sanitizer/board
opt-in gates ran; these Python controls are not firmware or hardware evidence.

Optional wall retention now implements the stated deduplication/window/closing
checks. Default avoids live wall intake; unknown/missing evidence is not filled
by a hash or nominal tick. Logs retained, no cleanup/deletion or new artifacts
outside the ignored local recovery directory. All eight flags false, no adopted
bound, source/geometry/coverage/clock/permission/admission or usable command.
Next wire optional correspondence into the existing current-owner delivered/
pending snapshot, matching all three IDs and omitting partial payload on unknown.

## 237. Native ToF Wall Delivered/Pending Correspondence (2026-11-10)

Checkpoint `7def694` pushed/clean. Local hypothesis: the existing current-owner
delivery snapshot can optionally match retained wall records to each delivered/
pending source by epoch/acquisition/delivery IDs, with typed prehash guards and
detached copies. Default must avoid wall history/intake. Collect closing wall,
selection, timing, arithmetic and pending queue probes before outgoing payload
comparisons; missing/changed evidence returns unknown without partial payload.
No geometry, native recapture, new recorder read/retention, clocks or RNG.

Twenty-one bounded synthetic controls, unchanged parent fixtures: per case at
most4 setup steps,3 geometry evaluations/retentions,5 recorder reads and6 setup
clocks only with combined companions. Snapshot at most6 wall/selection/timing/
direction-norm probes each,2 pending matchers/4 queue copies/2 frame checks,
64 bindings, zero forbidden source-intake/read/retention/step/reset/geometry/
clock calls. Existing8-history/4-wall/64-ray/canonical-word/rational work caps
unchanged. Three pytest positions including failures/aborts: first21/60 seconds,
one necessary repair/control reserve, final root/300 seconds. Preserve logs
`wall-237-focused-1.log`, reserve and root in the existing local recovery
directory. This is fresh routine integration, not renewed old studies/ledgers.
All eight flags false; no numerical/geometry/coverage/physical/source/clock/
permission/admission qualification, dependencies/downloads/model/hardware work.

First21 passed,2421 deselected,5.40 s. Closing-order review found the last wall
matcher could mutate an owned history after its earlier preflight. Move/repeat
the live native/timing/selection/wall guards after the final queue-copy probe,
before any closing structured payload hashes. Strengthen the reserved control
position to24 cases (same60 seconds and per-case caps), adding oversized live
wall/selection/timing mutations at the final wall matcher and requiring no
subsequent binding hash. Final root position unchanged; no failure/abort or old
ledger refund. Retain `wall-237-focused-2.log` for this necessary repair check.

Strengthened24 passed,2421 deselected,5.09 s; late history-budget guards reject
before another binding hash. Flatten the moved pending guard with equivalent
short-circuit `and` before focused formatting/lint and the final root gate.
No failure/abort so far; both focused positions spent, root remains unused.

Focused Ruff/format/whitespace passed. Required root:3368 passed,1 known
transformer QDQ xfailed,71 warnings,71.16 s; root Ruff, changed-file format check
and whitespace passed. All three pytest positions spent, no failures/aborts.
Editor diagnostics clear. AST ownership comparison found only the existing
delivery snapshot changed, one new bounded wall matcher and one new test; all
other production/test nodes unchanged. Runtime callers cover the new keyword;
no static compatibility claim or additional C/Arm/sanitizer/board opt-in gates.
The host/root results are not linked firmware or hardware evidence.

Detached delivered/pending wall records now use original source IDs, with live
prehash guards and late outgoing checks. Default ignores wall history; unknown
omits all partial source/frame/companions. Logs retained, no cleanup/deletion;
all eight flags false, no adopted numerical/physical bound, source/geometry/
coverage/clock/permission/admission qualification or usable command. Next advance
independently supported wall-operation arithmetic from the actual captured
operand/result words, without confusing per-evaluation residuals with accepted
rounding bounds, scene coverage or independent geometry proof.

## 238. Native ToF Wall Offset Word Residuals (2026-11-10)

Checkpoint `213eae3` pushed/clean. Actual cold wall capture records the scalar
`wall - position[axis]` result separately from division. Local hypothesis: a
pure bounded helper can report its exact supplied-word subtraction and signed
observed-minus-exact residual for four walls, preserving original words and
leaving nonfinite observed offsets unknown. This isolates an operation-word
discrepancy, not independent source binding, correct rounding, a uniform error
allowance, wall division/masking/geometry/coverage or physical clearance proof.

Sixteen synthetic controls with unchanged parent fixtures; only the actual-word
case performs one setup step/geometry evaluation/closed wall intake (two native
intakes). All others use declared synthetic words without acquisitions. One
helper call per case,12 canonical words of at most32 characters,4 entries,
at most12 guarded rational conversions/8 guarded operations,4096-bit cap.
During diagnostics no source intake/recorder read/retention/step/reset/geometry/
clock/RNG activity. Three pytest positions including failures/aborts: first16/
60 seconds, one necessary repair/control reserve, final root/300 seconds.
Retain `wall-238-focused-1.log`, reserve and root in the existing local recovery
directory. All eight flags false; no study/task data/model/dependency/download/
firmware/Arm/board/hardware work or renewed old ledger/qualification authority.

First focused position failed collection (unclosed parametrization),0.31 s;
no cases ran and the position is spent. Actual file sizes/tails were complete.
The overly broad insertion anchor displaced five lines of an unrelated original
test header, rather than truncating the file. Preserve the malformed test file
as `wall-238-boundary-before.py` in the local recovery directory; restore exactly
the five original header/import lines and remove the dangling partial header.
Use the reserved same16/60-second focused check after this local repair; final
root position unchanged. No old interrupted attempts refunded or limits relaxed.

Repaired same16 passed,2445 deselected,2.60 s. Focused Ruff/format/whitespace
passed. Required root:3384 passed,1 known transformer QDQ xfailed,71 warnings,
78.69 s; root Ruff, changed-file format check and whitespace passed. All three
pytest positions spent, including the collection failure; no abort. Editor
diagnostics clear. AST comparison proves exactly one new helper/test, with every
prior production/test node unchanged, including the repaired original header.
No additional C/Arm/sanitizer/board opt-in gates ran; host checks do not qualify
firmware/hardware. Original and malformed versions/logs retained; no deletion.

Finite supplied subtraction residuals are now computed exactly; deliberately
changed words are reported as discrepancies, not accepted as correct rounding.
Actual-word fixture uses one fresh captured wall source; other words are declared
synthetic, not measured acquisitions. All eight flags false, no adopted uniform
bound, geometry/coverage/source/clock/physical/permission/admission or usable
command. Next independently check the captured numerator-to-distance division
operation, preserving zero-denominator branch and nonfinite-result unknowns;
do not fold subtraction and division into an unsupported single rounding claim.

## 239. Native ToF Wall Division Word Residuals (2026-11-10)

Checkpoint `c68a098` pushed/clean. Local hypothesis: use the actual separately
captured numerator, matching ray-axis and raw distance words to diagnose the
division independently of subtraction and hit selection. Four walls/64 rays
produce256 supplied-word records. Zero direction requires initialized+inf and
has no quotient; nonfinite numerator/distance leaves residual unknown, while
finite operands permit an exact rational quotient. No combined-rounding claim,
accepted error bound, source/geometry/coverage/physical/clock/admission follows.

Twenty bounded controls with unchanged parent fixtures; only actual-word case
uses one setup acquisition/geometry/closed wall intake with two native intakes.
Each case one helper call,452 canonical words<=32 characters,256 records,
at most768 guarded conversions/512 operations under existing4096-bit cap. No
source intake/read/retention/step/reset/replay/clock/RNG during diagnostics.
Three pytest positions counting failures/aborts: first20/60 seconds, one necessary
repair/control reserve, final root/300 seconds. Retain `wall-239-focused-1.log`,
reserve/root in existing local recovery directory. All eight flags false, no
old ledger refund or study/task-data/model/dependency/download/native/hardware
work. Use a unique complete original test header as insertion anchor after238.

First20 passed,2461 deselected,3.27 s. Focused Ruff/format/whitespace passed.
Required root:3404 passed,1 known transformer QDQ xfailed,71 warnings,75.87 s;
root Ruff, changed-file format check and whitespace passed. Two of three pytest
positions used, no failure/abort; unused reserve is not follow-on authority.
Editor diagnostics clear. AST comparison proves exactly one new helper/test;
all previous nodes unchanged. No additional C/Arm/sanitizer/board opt-in gates
ran; host controls do not establish firmware/hardware capability. Logs retained,
no cleanup/deletion or new dependency/download/model/study/hardware activity.

Actual-word fixture covers a fresh captured numerator/ray/raw-distance packet;
other inputs are declared synthetic. Unknown nonfinite outcomes and zero-
direction non-divisions remain distinct. All eight flags false, no adopted
correct-rounding/combined/uniform error claim or source/geometry/coverage/
physical/clock/permission/admission qualification. Next compose both separate
offset/division diagnostics with matched delivered/pending wall records and
original IDs, closing all companion probes before comparisons; do not infer
source qualification or correct scene geometry from word correspondence.

## 240. Matched Native ToF Wall Arithmetic Diagnostics (2026-11-10)

Checkpoint `872afa9` pushed/clean. Local hypothesis: an independent literal
wall-residual opt-in requiring matched wall publication can compose the existing
separate subtraction/division helpers with original epoch/acquisition/delivery
IDs. Initial and closing probes precede outgoing comparisons; live typed guards
remain after the final probe. Default skips arithmetic, missing/changed evidence
returns unknown without partial payload. Per-word residuals are not adopted
rounding bounds, independent geometry/coverage/source qualification or admission.

Eighteen bounded controls, unchanged parent fixtures: per case at most4 setup
steps,3 geometry evaluations/retentions,5 recorder reads and6 setup clocks only
with companions. Snapshot at most6 offset/division/wall/selection/timing/norm
probes each,2 pending matchers/4 queue copies/2 frame checks/64 bindings; arithmetic
at most4680 guarded conversions/3120 operations under unchanged4096-bit cap.
Independent fixture quotient/residual oracle at most1536 Fraction operations.
No source intake/read/retention/step/reset/geometry/clock/RNG during snapshot.
Three pytest positions including failures/aborts: first18/60 seconds, one
necessary repair/control reserve, final root/300 seconds. Retain `wall-240-*`
logs in existing local recovery directory. All eight flags false, no old ledger
refund or new study/task data/model/dependency/download/native/hardware action.

First18 passed,2481 deselected,5.37 s. Focused Ruff/format/whitespace passed.
Required root:3422 passed,1 known transformer QDQ xfailed,71 warnings,78.00 s;
root Ruff, changed-file format check and whitespace passed. Two of three pytest
positions used, no failure/abort; unused reserve is not follow-on authority.
Editor diagnostics clear. AST comparison confines changes to the existing
delivery snapshot plus one new integration test; all prior helpers/tests remain
unchanged. No additional C/Arm/sanitizer/board opt-in gates ran; host/root checks
are not linked firmware/hardware capability. Logs retained, no cleanup/deletion.

Matched diagnostics now use actual retained wall words/original IDs with
independent fixture quotient/residual checks. Deliberately changed outputs and
late companion/history changes reject, not become accepted arithmetic. Default
skips the new helpers; missing/budget-exhausted evidence leaves no partial
payload. All eight flags false, no adopted uniform error/geometry/coverage/
source/physical/clock/permission/admission or usable command. Next advance
supported altitude/across and mask/selection prerequisites from captured words.
Archive whole231-235 verbatim and rebase their five design references to keep
the root map short; retain the pre-move review and mechanical utility locally.

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
