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

Checkpoints 231 onward and the source bibliography remain below.
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

## 231. Selected Native ToF Wall-Word Residuals (2026-11-10)

Checkpoint `41176d4` normally pushed/clean. Actual wall candidates compute native
subtraction then division. Local hypothesis: an independent offline diagnostic
can compare a supplied selected-wall word with the exact quotient of supplied
stored wall/position/direction words, without replay or claiming correct geometry.
It reports the combined arithmetic discrepancy, not separate primitive errors,
source authentication, uniform error, masking/minimum correctness or a tolerance.

Finite sixteen cloned controls, one fresh step/selection capture and one bounded
intake each; afterwards zero source/recorder read, retention, step/reset, geometry,
RNG/clock work. Per diagnostic at most 260 canonical words of at most 32 chars,
64 labels/indices, 256 guarded rational values/192 operations at existing 4096-bit
cap. Independent integer-pair oracle at most 128 Fraction constructions and 640
fixed arithmetic operations. Existing parent/source caps unchanged; no study,
model/GPU/data/dependency/download/hardware/firmware or physical-bound adoption.
All eight flags false. Three initial pytest positions: focused sixteen/60 seconds,
one necessary repair reserve, final root/300 seconds; failures/aborts count.
Attempt 1 now launches `test_native_tof_selected_wall_residuals`; raw output:
`.git/recovery-20261109-PmbQpU/wall-231-focused-1.log`. Preserve failures before
repair, no previous standalone scope or successful gate is renewed.

Attempt 1: sixteen passed, 2324 deselected, 2.24 s. Local control review found the
actual-source case lacked an explicit nonempty selected-wall assertion and setup
counts were implicit. Add that assertion, exact per-selected-word guarded-work
counts, one geometry/intake setup count and unchanged inputs/RNG state controls.
Use reserved attempt 2 for this necessary control strengthening rather than a
failure repair; no failure/abort or protected budget change. Retain its output in
`wall-231-focused-2.log` beside attempt 1; root position remains unused.

Attempt 2: sixteen passed, 2324 deselected, 3.08 s. Actual selected-wall coverage,
four axis/side mappings, independent integer-pair quotients/discrepancies, exact/
rounded/signed-zero/subnormal/largest-finite words, no-wall/infinite branches,
strict opt-in/schema rejection and reduced arithmetic budget controls passed.
Changed-file format/lint and editor diagnostics passed. Final position: root
3263 passed/known transformer QDQ one xfailed/71 warnings, 70.90 s; root Ruff,
diff/changed-file format passed. Log `wall-231-root-1.log` retained with both
focused outputs; all three positions used, no failure/abort, no reported skip.
No extra opt-in C/Arm/sanitizer/board/model/study gate; this is Python-only offline
word arithmetic. Source snapshots/defaults and native geometry are unchanged.
The actual control uses one original fresh capture, not geometry inside the
helper; declared extreme controls are supplied arithmetic, not physical scenes.
Next retain actual discarded wall calculation intermediates separately as useful
evidence permits, rather than presenting these supplied-word ratios as measured
primitive errors, a current-source binding, complete coverage or qualification.
All eight flags remain false; no physical bound or accepted requirement changes.

Whole historical §§221-225 moved verbatim into the reading-map archive, retaining
failures/spent ledgers and rebasing inbound links; root bibliography definitions
remain unchanged except its new archive pointer. Root now below 800 lines.
Mechanical utility and pre-move review retained in the existing local recovery
directory. AST ownership proves only one new helper/test, all previous nodes
unchanged. Stable workflow, thirteen changed local targets/anchors and editor
diagnostics passed. No code gate repeated for documentation or archival.

First pre-commit staged whitespace check rejected the new archive's blank EOF;
no commit/push ran. Add a bibliography footer after the verbatim section bytes,
then recheck staged whitespace, section conservation and its additional link.
This documentation failure does not consume or renew a pytest position.
The first footer edit retained the old blank after the new footer; both its
conservation assertion and staged whitespace check failed. Exact tail inspection
identified that one extra blank outside the preserved sections; remove only it
before the final conservation/whitespace recheck. No commit/push ran.
That manual EOF patch still left the blank on disk: the third conservation
check failed. Read-only byte comparison confirmed one exact historical copy
and only the footer EOF difference. A one-file mechanical trailing-newline
normalization then passed exact section-plus-footer conservation and staged/
unstaged whitespace checks; fourteen changed local references in total.

## 232. Actual Native ToF Wall Calculation Trace (2026-11-10)

Checkpoint `68c5d5d` pushed/clean. Selected supplied-word discrepancies do not
retain the actual discarded wall division/masking/minimum intermediates. Local
hypothesis: a separate cold empty builtin `wall_source` can copy those actual
values during the original geometry evaluation without changing default/native/
selection output words. It rejects aliasing and unsupported mounted/input paths
before geometry. It does not forward into fresh acquisitions or source delivery,
adopt physical/numerical bounds, prove masking/coverage or admit a command.
All eight flags false, existing 32-obstacle/64-ray domain unchanged.

First reversible source probe: at most two geometry evaluations, four detached
wall records, original default parity and false flags; 60 seconds. Passed; log
`wall-232-probe-1.log` retained in existing local recovery directory. No source/
recorder/step/reset/clock/model/study/data/dependency/download/hardware action.
Now add sixteen synthetic unit cases: at most two geometry evaluations each,
zero for rejection, and one intercepted evaluation with at most101 divides/
100 candidate masks/100 minima. Four wall records retain 4*64*5 float values,
4*64 booleans, original ray/floor/final word copies and fixed metadata; no added
geometry, RNG or clock. Independent altitude/across comparisons are at most
eight fixed64 arrays. Two focused pytest positions/60 seconds each (one reserve
for necessary controls/repair), then one required root/300 seconds; failures and
aborts count, prior ledgers untouched. First focused output `wall-232-focused-1.log`.

First focused: nine failed/seven passed, 2340 deselected, 5.13 s. All valid cases
reached the same fixture defect: the detachment mutation overwrote one staged
wall minimum before the next wall's predecessor comparison. Keep every lineage
assertion and move mutation after all four comparisons; reserve position reruns
the unchanged sixteen cases. No source repair, tolerance/cap relaxation or old
ledger refund; output `wall-232-focused-2.log`, root remains unused.

Second focused: sixteen passed, 2340 deselected, 2.62 s. Intercepted original
division/mask/minimum operands/results agree word-for-word with trace copies;
default/native/selection words, four-wall order, predecessor lineage, occluded
and zero-denominator/signed-zero paths,32-obstacle bound, detached mutations and
alias/legacy/invalid preflight controls passed. No forbidden operation ran.
Ruff format/lint and editor diagnostics passed. Final root3279 passed/known
transformer QDQ one xfailed/71 warnings,86.52 s; root Ruff/diff and changed-file
format passed, no reported skip. Pylance all20 resolved callers compatible.
All three pytest positions spent including the first focused failure; separate
initial probe retained, no abort. Logs remain in the local recovery directory.
No additional opt-in C/Arm/sanitizer/board/model/study gate; this changes Python
simulation tracing, not firmware, source qualification or actuation.

AST ownership: only `tof_ranges` changes and one new test; all other source/test
nodes remain exact. Original numeric expression order remains subtraction then
division; the numerator is named once rather than recomputed for the trace.
The current helper retains actual operands/results, not their independent
correctness, physical wall hits, complete coverage or acceptable error. All
eight flags false. Next pair the separate trace with the original fresh native
acquisition without extra geometry/RNG/clock work, then add bounded closed-cache
intake/retention only as evidence permits. No current-source or delivery claim
follows from this cold trace; accepted limits and existing schemas unchanged.
Prior checkpoint/Sources/design/stable-workflow preservation, new local target/
anchor, final owning-function diff and whitespace passed. Root823 lines; no
code gate repeated for documentation. Only the five scoped files are staged.

## 233. Actual Fresh ToF Wall Acquisition Pairing (2026-11-10)

Checkpoint `3ae989b` pushed/clean. Local hypothesis: a separate literal wall
capture opt-in can forward the existing cold trace dictionary through the
original fresh sample and cache it against the original native/RNG/tick/delivery
identities, preserving default forwarding and RNG/geometry/clock order. Preflight
rejects missing native dependency, legacy/invalid flags/pose/budget before
mutation. Default/held/reset paths clear the wall cache; all eight flags false.
It does not retain/publish a recorder source, establish complete coverage/error/
physical/clock evidence or admit commands. No new bounds/contracts are adopted.

First reversible probe: two fresh `RoverEnv` constructions and one step each,
at most four geometry evaluations total, zero clock/recorder/source intake;
existing64/32/4wall shape caps. Compare outputs/RNG/native identity and trace
word parity within60 seconds; retain `wall-233-probe-1.log` in the existing local
recovery directory. Further finite unit controls/root gate follow only after
this direct probe; failures/aborts retained, old budgets are not renewed.

First probe failed: default rate held acquisition at tick1, so indexing the
expected fresh cache raised TypeError. This exposes a probe-profile mistake,
not evidence of failed fresh forwarding. No source change; retry once with the
existing every-tick `tof_rate_hz=None` synthetic profile and the same two
constructions/one step each/four geometry maximum. Retain the failed log and
`wall-233-probe-2.log`; this does not qualify a clock or change product defaults.

Second probe passed: counted four geometry calls, zero clocks and original
native/RNG/acquisition identity, output and RNG parity with nonzero noise/dropout.
Now sixteen cloned acquisition controls, at most three step attempts/one reset
each and three geometry evaluations including baseline/reset, one original wall
capture; timing/combined-selection cases permit two controlled clock reads, all
others zero. No recorder read/intake/retention, replay or new task data. Fixed
64ray/four-wall/32obstacle caps unchanged. Three pytest positions including
failure/abort: focused16/60 seconds, one necessary repair/control reserve, final
required root/300 seconds. Preserve logs `wall-233-focused-1.log` onward; old
spent/unknown ledgers remain, no model/GPU/hardware/dependency/study action.

First sixteen passed, 2356 deselected,0.33 s. Original wall dictionary/native/
RNG/acquisition IDs, output/info/native-word/RNG parity with noise/dropout,
timing/selection coexistence, copied-word detachment and default/source-only/
held/reset clearing passed. Strict flag/dependency/legacy/pose/obstacle preflight
preserves prior cache identities and both RNG states; setup limits held, old
fixture counters zero. Changed-file format/lint and editor diagnostics passed.
Required root3295 passed/known transformer QDQ one xfailed/71 warnings,100.83 s;
root Ruff/diff and changed-file format passed, no reported skip. Two of three
pytest positions used/no pytest failure or abort; unused reserve is not follow-on
scope. The separately failed held-tick probe remains spent with both probe logs.
No additional opt-in C/Arm/sanitizer/board/model/study gate or task artifact.

Pylance `_update_sensor` all5 and refreshed `_sample` all5 resolved callers
compatible. Initial stale post-format positions for sample/step resolved no
calls, so were not compatibility evidence. Refreshed step40 resolved/38 compatible
plus the same two intentional `capture_motion_receipt=1` negatives at159/299;
no new resolved production incompatibility claimed. AST ownership confines
changes to reset/update/sample/step and exactly one new test; all other nodes
unchanged. Defaults retain their old forwarding calls; wall capture adds no
geometry or RNG/clock operation. It pairs actual raw wall words locally, not
correct geometry, physical clearance, clock/deadline/one-use or source admission.
All eight flags false, accepted requirements and native-source-v1 unchanged.
Next bounded read-only closed-cache intake with original native ownership,
typed shape/work preflight and closing context/copy checks; do not reconstruct
missing wall intermediates from final range words or publish to the recorder yet.
Prior checkpoint/Sources/design/stable-workflow preservation, new local target/
anchor, final four-method diff and whitespace passed; no code gate repeated for
documentation. Only the five scoped source/test/design/workflow/review files.

## 234. Bounded Native ToF Wall Intake (2026-11-10)

Checkpoint `361bfba` pushed/clean. Local hypothesis: closed wall-cache preflight,
two existing read-only native intakes and closing exact primitive comparisons
can copy the actual four-wall intermediates without replay, clocks or recorder
read/retention. Validate root/trace/entry keysets and builtin types, fixed four
walls, exact64-array shapes/dtypes, flags and original cache/native/RNG/tick/
delivery IDs before producing detached canonical words. Closing checks include
live profile/pose, source/cache identities and staged output. This does not
prove arithmetic/masking/geometry/coverage, source authority or command admission;
all eight flags false, no physical/numerical bound or accepted requirement change.

Sixteen cloned synthetic cases, one original step/trace each; at most two native
intakes, zero geometry/step/reset/recorder/source read/retention/RNG/clock/hash
after setup. Four wall entries: each five64 float arrays/one64 builtin mask,
three scalar words and fixed indices; ray192/floor64/final64 words. Two bounded
metadata passes, at most3224 float-hex conversions/512 bool copies plus existing
bounded input profile copies; existing64/32/4096 source caps unchanged. Three
pytest positions counting failures/aborts: first16/60 seconds, one necessary
control/repair reserve, final root/300 seconds. Preserve logs in the existing
recovery directory starting `wall-234-focused-1.log`; no old ledger refunds,
studies/data/model/GPU/dependencies/downloads/firmware/Arm/board/hardware work.

First sixteen passed,2372 deselected,2.25 s. Control review found late-mutation
cases did not explicitly require their injected mutation to execute. Add an
exact mutation count without changing cases/source/work caps, then use the
reserved focused position for the necessary strengthened check. Retain first
output and `wall-234-focused-2.log`; root position remains unused, no failure
or abort so far. Old successful gates/standalone budgets are not renewed.

Strengthened same sixteen passed,2372 deselected,2.59 s. Every late source,
trace, profile, cache and outgoing-copy mutation was explicitly counted and
rejected. Fixed-array/index/mask/budget/flag/missing/epoch/native-identity
preflight controls require zero native intakes; actual copies retain original
hex/mask words and detached inputs/native output. Both RNG states and tick
unchanged; no forbidden operation or parent-fixture counter used. Style/format
and editor diagnostics passed. Required root3311 passed/known transformer QDQ
one xfailed/71 warnings,75.58 s; root Ruff/diff and changed-file format passed,
no reported skip. All three pytest positions used, no failure/abort. Raw logs
retained locally; no extra opt-in C/Arm/sanitizer/board/model/study gate or task
artifact. This Python diagnostic does not establish linked firmware/board fit.

AST ownership proves exactly one new intake helper/test, all previous nodes
unchanged. No existing signature/schema/default or accepted bound changed.
All eight flags remain false. Metadata/word correspondence does not prove that
the original wall computations were numerically/geometrically correct, adopt
physical/source/clock/permission/admission evidence or admit a command. Next
bounded optional recorder retention may pair these copied wall diagnostics with
already retained original native acquisition IDs, preserving owner/read/context
checks and no replay, before any separate delivery publication.
Prior checkpoint/Sources/design/stable-workflow preservation, new local target/
anchor, final helper diff and whitespace passed. Root942 lines; no code gate
repeated for documentation. Only the five scoped checkpoint files are staged.

## 235. Bounded Native ToF Wall-History Preflight (2026-11-10)

Checkpoint `13e3f75` pushed/clean. Recorder retention hashes history, so a
typed canonical wall-history gate is a local prerequisite before adding the
wall retention opt-in. Hypothesis: the existing bounded native-history pairing
and word-copy pattern can reject unsupported wall layouts before hashing,
without regenerating any intermediate. This first increment validates only;
it does not yet retain or publish walls, qualify source/geometry/coverage/error/
physical/clock evidence or admit commands. All eight flags remain false.

Sixteen synthetic controls: one setup step/intake each (two existing native
intakes inside that setup); thereafter zero intake/recorder/read/retention/
geometry/step/reset/clock/RNG/hash. Wall history/source list at most8, strictly
ordered/unique IDs paired to existing prevalidated native entries. Each four-wall
trace fixed5*64 arrays and64 builtin masks; canonical strings<=32, at most12896
new scalar/array hex decodes per validator and existing bounded common/source
word comparisons. Exact false flags/common input/ray/floor/final words and
axis/side/scalar identity words required; unsupported/overflow hex rejects.
Three pytest positions: first16/60 seconds, one necessary repair/control reserve,
required root/300 seconds; failure/abort counts. Preserve `wall-235-focused-1.log`
in the existing local recovery directory; no study/model/data/dependency/board/
hardware/download/protected-bound changes or old-ledger refund.

First sixteen passed,2388 deselected,2.51 s. Positive case originally checked
one entry; strengthen it to eight declared synthetic paired IDs carrying the
same captured native words, exercising the maximum without extra geometry or
intake. These are unit metadata clones, not additional actual acquisitions or
qualification evidence. Same sixteen/caps and reserve focused position; retain
`wall-235-focused-2.log`, root remains unused, no failure/abort so far.

Strengthened sixteen passed,2388 deselected,2.51 s. Eight declared paired entries
pass; oversized/non-list/order/duplicate/epoch/missing-pair/delivery/flag/shape/
noncanonical/overflow/index/mask/profile/ray mismatches reject. Inputs remain
unchanged and no forbidden operation or parent-fixture counter used. Changed-
file format/lint and editor diagnostics passed. Required root3327 passed/known
transformer QDQ one xfailed/71 warnings,71.89 s; root Ruff/diff and changed-file
format passed, no reported skip. All three pytest positions used/no failure or
abort; logs retained in the existing local recovery directory. No extra opt-in
C/Arm/sanitizer/board/model/study gate or task artifact.

AST ownership: exactly one new validator/test, all previous nodes unchanged.
This consumes prevalidated native source history and bounded canonical copied
wall words, not arbitrary source payloads or proof of actual additional reads.
No recorder behavior, defaults/schema, accepted requirement or bound changed.
All eight flags false, no physical/source/numerical/clock/permission/admission
qualification. Next wire this prehash validator into bounded optional recorder
wall retention, preserve deduplication/trim/owner/cache/output checks and reject
unsupported evidence without replay or delivery publication.
Whole historical §§226-230 moved verbatim through the reading map; all failures,
unknown/spent ledgers and autonomy corrections retained. Bibliography unchanged
except its archive pointer; one inbound recovery link rebased. Mechanical
utility/pre-move review retained locally. Exact prior section/design/stable-
workflow conservation, four changed local targets/anchors, final helper diff
and whitespace passed. Root below800 lines; no code suite rerun for documents.

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
