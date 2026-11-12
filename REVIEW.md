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

Checkpoints 316 onward and the source bibliography remain below.
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

## 319. Matched Native ToF Dropout Reports (2026-11-12)

Begin clean pushed89bdbef. Append literal default-off
`include_postprocessing_dropout_diagnostics`, requiring postprocessing inclusion.
Reuse the standalone supplied-word threshold/prior-mask comparison against
original/closing retained delivered and optional pending traces. Existing
native/typed companion prevalidation follows closing frame/queue callbacks
before report construction; final history identity, word, report-content and
detached output bindings must agree before publication. No new draw, finite
draw interval, threshold, probability/noise law or correction is adopted.

Extend existing24-case snapshot matrix with24 dropout-report cases and three
literal/dependency controls; old216 cases/defaults and source/matcher/fixture
caps stay unchanged. New scope <=6 dropout reports/390 word decodes/384 predicate
comparisons; independent Fraction oracle <=192 comparisons. Combined control
also uses existing additive reports within unchanged six-call/1,152-value/
768-binary/384-oracle caps. Check report identities/raw draw/threshold words/
prior/observed/expected masks, mismatch/unknown counts, detached outputs,
default key absence and late unknown-with-no-partial-publication.

Fresh three routine positions: focused27/60s, sole necessary repair27/60s,
required root/360s; failures/aborts/unknown spent, no historical/protected refund.
Retain ignored `.git/returns-319-*` outputs/hashes; serialize checks.
First27 PASS5.71s/216 deselected, all four source hashes stable; scoped Ruff/
changed format/whitespace PASS. Required root PASS5091/known QDQ xfail/
71 warnings/159.13s; root Ruff/changed format/whitespace PASS, all four source
hashes stable. Scoped diff/AST and reference checks PASS for prior module/
recorder/default/test nodes and old216-case prefix. Two of three fresh positions
spent, no failure/abort/refund; unused repair is not follow-on authority.
No successful code gate repeated for documentation closeout.

All eight flags remain false; raw unsupported/nonfinite source remains unknown.
This is matched source/word/mask content, not native comparator execution,
probability/noise-law, clip/cast/numerical/error/geometry/coverage/source/clock/
one-use/physical/permission/admission qualification. No new study/model/
dependency/download/hardware/extra native/Arm/sanitizer opt-in.
Next independently supported supplied-word clip/select correspondence;
preserve raw nonfinite unknowns and equal-value/different-word ties.

## 320. Supplied-Word Native ToF Clip/Selection Correspondence (2026-11-12)

Begin clean pushed ae0e3fd. Actual sampler captures
`clipped = np.clip(grid, 0, config.max_range)` and
`selected = np.where(valid, clipped, 0)` before the float32 cast.
Standalone helper compares supplied noisy/clipped/selected words and a literal
mask against declared clamp values and selected raw-word inputs. Use observed
clipped operands for selection, never corrected upstream values. Existing
positive finite max-range field is supplied, not a new bound/threshold.
Raw nonfinite in any stage keeps the whole comparison unknown; NaN/unsupported
metadata rejects. Preserve all signed words and equal-value/different-word ties
without predicting NumPy zero signs or adopting native rounding/primitive laws.

Three builtin64-word tuples and64 literal masks,<=32char canonical words,
193 decodes,256 value comparisons,128 raw-word comparisons and64 entries.
Add24 bounded actual/inside/outside/boundary/independent-stage-mismatch/masked/
zero-tie/raw-nonfinite/typed-word/mask/profile controls; independent Fraction
oracle <=128 clamp comparisons. One actual cold sample/geometry with only
existing normal/dropout draws before poisoning intake/read/retention/replay/
step/reset/sample/hash/clock/geometry calls. Prior helpers/defaults/tests exact.

Fresh three routine positions: focused24/60s, sole necessary repair24/60s,
required root/360s; failures/aborts/unknown spent, no old/protected refund.
Retain ignored `.git/returns-320-*` outputs/hashes; serialize checks.
First24 PASS3.43s, all four hashes stable; scoped Ruff/changed format/whitespace
PASS. Required root PASS5115, known QDQ1 xfail/71 warnings/159.39s;
root Ruff/changed format/whitespace and all four hashes PASS.
Both executed positions spent; repair reserve unused, not follow-on authority.

All eight flags remain false. Standalone pointwise value/word correspondence is
not native primitive/rounding/cast/noise-law/numerical/error/geometry/coverage/
source/clock/one-use/physical/permission/admission qualification. No new study/
model/dependency/download/hardware/extra native/Arm/sanitizer opt-in.
Next bounded original/closing retained clip/select report joins.

## 321. Matched Native ToF Clip/Selection Reports (2026-11-12)

Begin clean pushed6acd424. Literal default-off
`include_postprocessing_clip_selection_diagnostics` requires postprocessing
inclusion. Delivered/optional pending reports use matched retained noisy/
clipped/selected/mask/input words after independent native/companion guards.
Original/closing native/RNG/profile/pose/input/frame/history/queue/stored-word/
mask/report/output joins precede publication. Detached reports carry exact
typed source epoch/tick/delivery labels; unsupported or changed joins publish
explicit unknown without partial fields. Observed clipped operands and raw
nonfinite unknowns/zero-word ties remain unchanged, all eight flags false.

Reuse24 snapshot cases plus3 literal/dependency cases. Before execution owning
fixture inspection corrected the two-source estimate: delivered+<=2 pending,
original/closing<=6 reports,<=1158 decodes/1536 value/768 raw-word comparisons,
384 entries; independent Fraction oracle<=384 clamp comparisons. Existing
producer/RNG/geometry/clock/retention/frame/binding and addition/dropout/
selection/timing/arithmetic controls stay unchanged; combined case includes
prior reports without more producer work. No old/protected budget refund.

Fresh focused27/60s, sole necessary repair27/60s, root/360s positions.
First27 PASS6.04s with240 unselected; four hashes stable, scoped Ruff/
changed format/whitespace PASS. Root PASS5142, known QDQ1 xfail/71 warnings/
160.18s; root Ruff/changed format/whitespace and all four hashes PASS.
Both executed positions spent; repair unused, not follow-on authority.
Ignored `.git/returns-321-*`
outputs/hashes retained. Pylance before/after resolved no dynamic callers,
not static compatibility proof. No replay/extra RNG/study/model/dependency/
download/hardware/native/Arm/sanitizer opt-in or law/threshold adoption.
Value/word matches are not numerical/error/source/geometry/coverage/clock/
one-use/physical/permission/admission qualification.

Next preserve whole checkpoints311-315 before root review growth, then
independent supplied selected-float64/stored-float32 correspondence; do not
silently adopt a rounding model or normalize signed words.

## 322. Intact Retention and Delivery Checkpoint Archival (2026-11-12)

Begin clean pushedafe8848. Move whole311-315, including cloud prompt/pause,
failures, approvals, spent ledgers, bodies, headings and separators, to
[their archive][chapter-review-27]. Preserve five old root heading anchors
as archive links; rebase eight chapter02/03 references and the cloud-handoff
reading-map link. Keep historical prompt words unchanged, not fresh authority.
Copy the one required archive reference definition with its relative target.

First mechanical preflight FAILED before any write: inherited no-body-links
guard rejected section312's existing archive reference. Diagnose its one label;
sole bounded structural repair copies/rebases its definition, not the body.
Revised migration/conservation PASS, four tested source hashes unchanged;
local targets/anchors and whitespace PASS. Both positions spent, no old or
protected refund. Root726 lines before this note, archive273; no code edit,
code suite/native/Arm/sanitizer rerun, new study/model/dependency/download/
hardware action or qualification/law adoption. Local snapshots/utility retained
in session files, portable evidence in Git documents.

Next independent bounded selected-float64/stored-float32 supplied-word
correspondence. Preserve raw words/unknowns, not a rounding model or bound.

## 323. Supplied-Word Native ToF Selected/Storage Residuals (2026-11-12)

Begin clean pushed644bec6. Actual sampler captures selected float64 input and
stored float32 result of `selected.astype(np.float32)`. Standalone helper
reuses the existing sampling report's uint32-to-float32 view, not its ideal-
sampling policy. Preserve closed-history finite builtin uint32 storage
preflight and supplied canonical selected words; raw selected +/-inf reports
unknown, unsupported/NaN metadata explicitly rejects. Report exact decoded
stored-minus-supplied-selected residuals, numerical equality and decoded-word
equality separately. Do not predict stored rounding/cast words or adopt a cast
law, numerical/error bound or qualify zero-word ties. All eight flags false.

Two builtin64-word tuples; selected canonical words<=32char,64 selected decodes/
64 storage views,128 rational values/64 subtractions/64 entries,1..4096-bit
hard bound. Add24 cold-actual/exact/signed residual/zero-tie/subnormal/extreme/
raw-nonfinite/typed-word/shape/storage/rational-budget controls; independent
struct decode and Fraction oracle<=64 subtractions. Only one existing-draw
actual capture/geometry before poisoning intake/read/retain/step/reset/replay/
hash/clock/geometry paths; RNG/odometry state and inputs unchanged thereafter.

Fresh focused24/60s, sole necessary repair24/60s, required root/360s positions.
First24 PASS3.40s with all four hashes stable; root PASS5166, known QDQ1 xfail/
71 warnings/160.61s. Root/scoped Ruff, changed format/whitespace and all four
hashes PASS. Both executed positions spent; repair unused, not follow-on authority.
Ignored `.git/returns-323-*` outputs/hashes retained; no historical/protected
refund, new dependency/download/model/study/hardware/native/Arm/sanitizer opt-in.
Pointwise supplied residuals and matching words are not rounding-law/native
primitive/source/geometry/coverage/clock/one-use/physical/admission evidence.
Next separately bounded original/closing retained storage report joins.

## 324. Matched Native ToF Selected/Storage Reports (2026-11-12)

Begin clean pushed3a21002. Literal default-off
`include_postprocessing_storage_residuals` requires postprocessing inclusion.
Delivered/optional pending reports use detached matched selected/storage words
after independent native/companion guards. Original/closing native/RNG/profile/
pose/input/frame/history/queue/stored-word/mask/report/output joins precede
publication; changed/unsupported joins publish explicit unknown without partial
fields. Preserve observed residuals, typed epoch/tick/delivery labels and zero-
word ties without predicting native cast words or adopting a rounding/error
law. Raw unsupported/nonfinite source remains unknown, all eight flags false.

Reuse24 snapshot cases+3 literal/dependency controls, including changed selected
source and outgoing storage report; combined mode includes prior postprocessing
reports within unchanged producer/report caps. Original/closing<=6 reports,
384 entries/768 word decodes/768 rational values/384 subtractions; independent
struct/Fraction oracle<=192 subtractions, existing 4096-bit limit unchanged.
No replay/extra RNG/old or protected refund/new dependency/download/model/
study/hardware/native/Arm/sanitizer opt-in or safety/qualification change.

Fresh focused27/60s, sole necessary repair27/60s, required root/360s.
First27 PASS5.92s with264 unselected, all four hashes stable. Root PASS5193,
known QDQ1 xfail/71 warnings/164.24s; root/scoped Ruff, changed format/
whitespace and four hashes PASS. Both positions spent; repair reserve unused,
not follow-on authority.
Ignored `.git/returns-324-*` outputs/hashes retained. Pylance before/after
resolved no dynamic callers, not static compatibility evidence.
Source matches/residuals are not numerical/error/source/geometry/coverage/
clock/one-use/physical/permission/admission qualification.

Next reassess independently supported setup/source/coverage/error/timing
prerequisites and guarded request/executor dependencies in design§12; missing
qualification alone is not a reason to stop compatible prerequisite work.

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
[native-tof-ray-design]: docs/design/07-data-and-distillation-design-01.md#native-tof-ray-generation-prerequisites-2026-11-11
[cloud-harness-handoff]: docs/review/311-315.md#311-cloud-harness-handoff-and-restart-prompt-2026-11-12
[review-311-315-preserved-0]: docs/review/311-315.md#311-cloud-harness-handoff-and-restart-prompt-2026-11-12
[review-311-315-preserved-1]: docs/review/311-315.md#312-bounded-native-tof-postprocessing-recorder-retention-2026-11-12
[review-311-315-preserved-2]: docs/review/311-315.md#313-bounded-retained-native-tof-postprocessing-matching-2026-11-12
[review-311-315-preserved-3]: docs/review/311-315.md#314-closed-native-tof-postprocessing-delivery-publication-2026-11-12
[review-311-315-preserved-4]: docs/review/311-315.md#315-supplied-word-native-tof-noise-addition-discrepancies-2026-11-12
