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

Checkpoints 261 onward and the source bibliography remain below.
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

## 261. Supplied-Word Cylinder Side-Altitude Expression (2026-11-10)

Checkpoint `08015e2` pushed/clean. Native altitude is height+effective_distance*up
with finite raw distance used, otherwise +0. Local hypothesis: bounded exact
unrounded supplied-word expression and observed-minus-exact ratios, preserving
raw/effective words and fallback branch. Product is not separately captured;
no isolated multiplication/addition rounding/FMA or geometric claim follows.
<=32 cylinders/64 rays/two sides,8385 canonical words/32 characters, finite
height/rays, other words non-NaN, existing4096-bit rational ceiling, <=8257
value calls/12288 binary operations/4096 entries. Nonfinite observations unknown;
original signed words retained without host zero-tie adoption. No intake/read/
hash/retention/replay/clock/RNG or matched-source composition.

31 bounded synthetic controls, independent Fraction oracle <=12288 operations;
actual nonempty setup <=1 geometry/selected intake,2 native intakes, otherwise
no acquisition. ±inf distance fallback and deliberate fallback-result mismatch,
negative distance/up, rounded/subnormal/large/nonfinite altitude, max32/empty and
malformed/work ceilings. Three pytest positions including failures/aborts:
first31/60 seconds, one necessary repair reserve, final root/300 seconds;
retain `cylinder-261-*` logs. No old refunds/protected runs/task data/dependencies/
hardware. All eight flags false, no primitive/FMA/uniform/numerical/physical/
source/geometry/coverage/clock/one-use/permission/admission or usable command.
Side mask/candidate correspondence remains next, independent of geometry.

First31 passed,2902 deselected,0.52 s. Required root3856 passed,1 known
transformer QDQ xfailed,71 warnings,86.87 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. AST proves only new side-
altitude helper/test added; all prior source/test nodes intact, no existing
signature changed. Two of three pytest positions used, no failures/aborts;
unused reserve is not follow-on authority. Logs `cylinder-261-focused-1.log`/
`cylinder-261-root-1.log` retained under recovery directory. No additional
C/Arm/sanitizer/board opt-in gates ran.

Actual nonempty/max32/empty controls, finite/±inf-distance zero fallback,
deliberate fallback-result mismatch, signed-zero/negative distance/up,
rounded/subnormal/large/nonfinite altitude and malformed/work rejection agree
with independent Fraction oracle within caps, leaving input/tick/RNG unchanged.
All eight flags false, no primitive/FMA/uniform/numerical/physical/source/
geometry/coverage/clock/one-use/permission/admission or usable command. Next
side hit-mask/candidate correspondence: stored-word predicates separately from
selection using observed hit, not a geometric intersection claim.

## 262. Supplied-Word Cylinder Side Mask/Candidate Correspondence (2026-11-10)

Checkpoint `34ec07e` pushed/clean. Native side hit is conjunction of stored-word
discriminant>=0, distance>=0, altitude>=0, altitude<=top; candidate is observed
hit?distance:+inf. Hypothesis: report mask correspondence independently from
candidate selection based on observed hit, not a geometric intersection claim.
<=32 cylinders/64 rays/two sides,14368 canonical words/32 characters and4096
literal bools. Finite tops, other words non-NaN, candidates exclude -inf, as
nearby wall diagnostic. <=4096 entries/16384 operand predicates/8192 mask and
candidate comparisons. No rational work/intake/read/hash/retention/replay/clock/
RNG or matched-source composition. Candidate signed-zero word mismatch retained;
matching hit=True/+inf candidate is not a finite intersection.

35 bounded synthetic controls, same predicate/comparison oracle caps; actual
nonempty setup <=1 geometry/selected intake,2 native intakes, otherwise none.
Four predicate boundary/false controls, nonfinite operands, independent mask/
candidate faults, signed-zero word mismatch, max32/empty and typed preflight.
Input/tick/RNG preserved. Three pytest positions including failures/aborts:
first35/60 seconds, one necessary repair reserve, final root/300 seconds;
retain `cylinder-262-*` logs. No old refunds/protected runs/task data/dependencies/
hardware. All eight flags false, no primitive/uniform/numerical/physical/source/
geometry/coverage/clock/one-use/permission/admission or usable command. Minimum
word correspondence remains next, preserving equal-value/different-word ties.

First35 passed,2933 deselected,2.95 s. Required root3891 passed,1 known
transformer QDQ xfailed,71 warnings,87.18 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. AST proves only new side
mask/candidate helper/test added; all prior source/test nodes intact, no existing
signature changed. Two of three pytest positions used, no failures/aborts;
unused reserve is not follow-on authority. Logs `cylinder-262-focused-1.log`/
`cylinder-262-root-1.log` retained under recovery directory. No additional
C/Arm/sanitizer/board opt-in gates ran.

Actual nonempty/max32/empty controls, four stored predicates/boundaries, separate
mask/candidate faults and counts, signed-zero word mismatch, nonfinite operands
and typed rejection agree with independent operand comparisons within caps,
leaving input/tick/RNG unchanged. Matching hit=True/+inf candidate is explicitly
word correspondence only, not a finite/geometric intersection. All eight flags
false, no primitive/uniform/numerical/physical/source/geometry/coverage/clock/
one-use/permission/admission or usable command. Next conservative side-minimum
word correspondence from captured observed predecessor/candidate/result, with
equal-value/different-word tie semantics unresolved.

## 263. Supplied-Word Cylinder Side Minimum Correspondence (2026-11-10)

Checkpoint `f389c68` pushed/clean. Native side minimum consumes captured observed
predecessor and candidate; report numeric minimum and word correspondence
without recomputing a preceding result. Strict lower operand or identical words
select known expected word. Equal-value/different-word ties remain unresolved
when numeric minimum matches; a wrong numeric value remains mismatch even on
such ties. No NumPy/host signed-zero tie semantics or geometry adopted.
<=32 cylinders/64 rays/two sides,12288 canonical finite/+inf words/32 characters,
4096 entries/20480 helper operand-word comparisons, aggregate counts separate.
No rational work/intake/read/hash/retention/replay/clock/RNG or composition.

30 bounded synthetic controls, <=32768 oracle comparisons; actual nonempty
setup <=1 geometry/selected intake,2 native intakes, otherwise none. Each
selection/identical or signed-zero tie/wrong numeric or word result, observed
predecessor independent of wrong preceding result, finite extremes/+inf,
max32/empty and typed preflight; input/tick/RNG preserved. Three pytest positions
including failures/aborts: first30/60 seconds, one necessary repair reserve,
final root/300 seconds; retain `cylinder-263-*` logs. No old refunds/protected
runs/task data/dependencies/hardware. All eight flags false, no primitive/
uniform/numerical/physical/source/geometry/coverage/clock/one-use/permission/
admission or usable command. Next standalone top/cap offset and guarded-division
expressions before cap hit-mask/candidate/minimum and matched-source composition.

First30 passed,2968 deselected,2.89 s. Required root3921 passed,1 known
transformer QDQ xfailed,71 warnings,87.14 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. AST proves only new side
minimum helper/test added; all prior source/test nodes intact, no existing
signature changed. Two of three pytest positions used, no failures/aborts;
unused reserve is not follow-on authority. Logs `cylinder-263-focused-1.log`/
`cylinder-263-root-1.log` retained under recovery directory. No additional
C/Arm/sanitizer/board opt-in gates ran.

Actual nonempty/max32/empty controls, strict/identical selections, both signed
zero tie orders, wrong numeric even on tie, strict value-correct/wrong-word
result, independent observed predecessor, finite extremes/+inf and typed
rejection agree with bounded independent oracle, input/tick/RNG unchanged.
All eight flags false, no primitive/uniform/numerical/physical/source/geometry/
coverage/clock/one-use/permission/admission or usable command. Next standalone
top/cap offset then guarded division. Archive whole251-255 losslessly before
further root review growth, retaining all ledgers and rebasing local targets.

## 264. Supplied-Word Cylinder Top Offset Expression (2026-11-10)

Checkpoint `c8bf911` pushed/clean. Native `top_offset = top - height` feeds cap
division and is captured as top numerator. Hypothesis: standalone exact supplied
top-minus-mount target and observed-minus-exact residual, not geometric/top
clearance. Finite operands, non-NaN observations; observed +/-inf retains exact
target but unknown residual; signed-zero words retained without tie adoption.
<=32 cylinders/65 canonical words/32 characters,4096-bit rational ceiling,
shared mount value <=65 value calls/64 binary operations/32 entries.
Preflight all words before rational work; exhaustion rejects without result.

31 bounded synthetic controls, <=64 oracle operations; actual nonempty setup
<=1 geometry/selected intake,2 native intakes, otherwise none. Exact/rounded/
perturbed/negative/signed-zero/subnormal/large/overflow target/nonfinite result,
max32/empty and typed/ingress/binary cap rejection; input/tick/RNG preserved.
Three pytest positions including failures/aborts: first31/60 seconds, one
necessary repair reserve, final root/300 seconds; retain `cylinder-264-*` logs.
No old refunds/protected runs/task data/dependencies/hardware. All eight flags
false, no primitive uniform/numerical/physical/source/geometry/coverage/clock/
one-use/permission/admission or usable command. Next standalone cap division
with `up != 0` bypass before relative/radial/mask/candidate/minimum prerequisites.

Whole251-255 archived verbatim in `docs/review/251-255.md`, four design targets
rebased; originals `cylinder-264-review-before.md`/`cylinder-264-design-before.md`
and guarded one-shot `archive-264.py` retained in recovery directory. Archive
check passed, root789/archive204 lines before this record; whitespace including
staged archive passed. Historical failures/ledgers/Sources preserved, no code
gate rerun for document migration. Do not rerun successful migration utility.

First offset check1 failed/30 passed,2998 deselected,0.79 s: actual exact oracle
and reported residual agreed at -1/36028797018963968, but extra test assertion
incorrectly assumed native fixture subtraction had zero residual. Repair only
that expectation: actual scalar subtraction word is checked exactly, synthetic
zero/nonzero controls and exact rational assertions retained. No production
change/tolerance relaxation; one extra actual scalar oracle operation remains
inside64 cap. Failure retained, repair uses recorded second pytest position.

Same31 passed,2998 deselected,2.95 s. Required root3952 passed,1 known
transformer QDQ xfailed,71 warnings,88.31 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. AST proves only new top
offset helper/test added; all prior source/test nodes intact, no existing
signature changed. All three pytest positions spent including failed first
expectation; no aborts or further rerun. Logs `cylinder-264-focused-{1,2}.log`/
`cylinder-264-root-1.log`/`cylinder-264-archive-1.log` retained under recovery
directory. No additional C/Arm/sanitizer/board opt-in gates ran.

Actual scalar word and exact nonzero residual, cancellation/perturbation, signed
zero words, finite extremes/overflow exact target/nonfinite unknown, max32/empty,
closed preflight before rational work and ingress/binary ceiling failures
verified within65 values/64 binary/64 oracle limits; input/tick/RNG unchanged.
No primitive uniform/numerical/physical/source/geometry/coverage/clock/one-use/
permission/admission or usable command. All eight flags false. Next cap guarded
division using supplied top-offset/up/distance, preserving raw words and explicit
zero-up positive-infinity bypass before relative/radial/selection prerequisites.

Whole-section byte checks and prior REVIEW/Sources/design/stable AGENTS
conservation passed; nine changed-context local targets valid, no stale root
251-255 anchor targets in searched unignored Markdown. Final root849/design2341/
archive204 lines. Original backups and all failed/passing logs retained.

## 265. Guarded Supplied-Word Cylinder Top Division (2026-11-10)

Checkpoint `02c9f57` pushed/clean. Native cap divide uses `up != 0`, including
negative finite up, unlike side horizontal-positive guard. Hypothesis: preflight
all zero-up outputs as literal +inf before rational work; elsewhere supplied
finite numerator/up exact quotient and observed-minus-exact residual. Nonfinite
numerator/distance explicit unknown; bypass no quotient/residual. Raw signed
zero words retained; matching infinity is not a finite/geometric intersection.
<=32 cylinders/64 rays/2272 canonical words/32 characters,4096-bit rational
ceiling, shared up/numerator <=2144 values/4096 binary operations/2048 entries.
No intake/read/hash/retention/replay/clock/RNG or composition. All eight flags
false; no primitive uniform/numerical/physical/source/geometry/coverage/clock/
one-use/permission/admission or usable command.

35 bounded synthetic controls, <=4096 oracle operations; actual nonempty setup
<=1 geometry/selected intake,2 native intakes, otherwise none. Positive/negative/
mixed up, both signed-zero bypasses/nonfinite numerator bypass, late invalid
branch before rational work, rounded/perturbed/finite extremes/nonfinite unknown,
max32/empty and typed/work rejection. Input/tick/RNG preserved. Three pytest
positions including failures/aborts: first35/60 seconds, one necessary repair
reserve, final root/300 seconds; retain `cylinder-265-*` logs. No old refunds/
protected runs/task data/dependencies/hardware. Next supplied-word relative
expression with explicit nonfinite-distance zero fallback, before radial/mask/
candidate/minimum and matched-source prerequisites.

First35 passed,3029 deselected,0.47 s. Required root3987 passed,1 known
transformer QDQ xfailed,71 warnings,88.60 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. AST proves only new top
division helper/test added; all prior source/test nodes intact, no existing
signature changed. Two of three pytest positions used, no failures/aborts;
unused reserve is not follow-on authority. Logs `cylinder-265-focused-1.log`/
`cylinder-265-root-1.log` retained under recovery directory. No additional
C/Arm/sanitizer/board opt-in gates ran.

Actual nonempty/max32/empty controls, positive/negative/mixed up, both signed
zero bypasses/nonfinite numerator bypass (zero rational work), late invalid
branch before rational work, signed words/rounded/perturbed/finite extremes/
nonfinite unknown and typed/work rejection verified within caps, input/tick/RNG
unchanged. Max32 reaches2144 values/4096 binary+oracle operations; source limit
remains4096 bits. No primitive uniform/numerical/physical/source/geometry/
coverage/clock/one-use/permission/admission or usable command. All eight flags
false. Next combined relative expression offset + effective_distance*horizontal
ray, raw nonfinite distance -> +0. Products are uncaptured: no isolated multiply/
add/FMA rounding claim, before radial and selection/source prerequisites.

## 266. Supplied-Word Cylinder Top Relative Expression (2026-11-10)

Checkpoint `2d5056a` pushed/clean. Native relative is offset + effective_distance
times horizontal ray, raw nonfinite distance -> +0. Hypothesis: report each axis
unrounded supplied-word combined expression and observed-minus-exact residual,
explicit raw/effective words and fallback; nonfinite observation unknown residual.
Products are uncaptured: no isolated multiply/add/FMA rounding claim. Finite
offsets/rays, other words non-NaN, signed-zero words retained without tie adoption.
<=32 cylinders/64 rays/two axes/6400 canonical words/32 characters,4096-bit
rational ceiling, shared horizontal/offset/effective values <=6336 values/
12288 binary operations/4096 entries. All words preflight before rational work;
budget exhaustion rejects without result. No intake/read/hash/retention/replay/
clock/RNG or composition. All eight flags false, no primitive uniform/numerical/
physical/source/geometry/coverage/clock/one-use/permission/admission or usable command.

35 bounded synthetic controls, <=12288 oracle operations; actual nonempty setup
<=1 geometry/selected intake,2 native intakes, otherwise none. Both axes/mixed
finite and +/-inf distance fallback, signed words/rounded/perturbed/cancellation/
finite extremes/overflow exact target/nonfinite unknown, max32/empty and typed/
ingress/binary exhaustion before result. Input/tick/RNG preserved. Three pytest
positions including failures/aborts: first35/60 seconds, one necessary repair
reserve, final root/300 seconds; retain `cylinder-266-*` logs. No old refunds/
protected runs/task data/dependencies/hardware. Next independent supplied-word
radial-squared and radius-squared prerequisites before cap selection/composition.

First35 passed,3064 deselected,4.03 s. Required root4022 passed,1 known
transformer QDQ xfailed,71 warnings,98.02 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. AST proves only new top
relative helper/test added; all prior source/test nodes intact, no existing
signature changed. Two of three pytest positions used, no failures/aborts;
unused reserve is not follow-on authority. Logs `cylinder-266-focused-1.log`/
`cylinder-266-root-1.log` retained under recovery directory. No additional
C/Arm/sanitizer/board opt-in gates ran.

Actual nonempty/max32/empty controls, both axes/mixed finite and nonfinite
distance fallback, raw/effective signed words, rounded/perturbed/cancellation/
finite extremes/overflow exact target/nonfinite unknown and typed/ingress/binary
rejection verified within caps, input/tick/RNG unchanged. Max32 reaches6336
values/12288 binary+oracle operations; source ceiling remains4096 bits. All eight
flags false, no isolated multiply/add/FMA rounding, primitive uniform/numerical/
physical/source/geometry/coverage/clock/one-use/permission/admission or usable
command. Next independently report relative.x^2+relative.y^2 and radius^2 from
supplied words, keeping cap radial predicate and candidate selection separate.

## 267. Independent Supplied-Word Cylinder Cap Square Expressions (2026-11-10)

Checkpoint `915807f` pushed/clean. Native cap radial sum of relative squares and
radius square feed a separate comparison. Hypothesis: report supplied-word
unrounded relative.x^2+relative.y^2 and radius^2 in separate entry groups,
observed-minus-exact residuals; nonfinite observation explicit unknown residual.
Finite supplied relative/radius operands, signed words retained without tie
adoption. Negative radius can match arithmetic but does not prove geometry.
Intermediate relative squares uncaptured: no isolated multiply/add/FMA rounding
claim for combined radial expression. <=32 cylinders/64 rays/6208 canonical
words/32 characters,4096-bit rational ceiling, <=6208 values/8256 binary
operations/2048 radial+32 radius entries. All words preflight before rational
work; exhaustion rejects without result. No predicate/selection/composition,
intake/read/hash/retention/replay/clock/RNG. All eight flags false, no primitive
uniform/numerical/physical/source/geometry/coverage/clock/one-use/permission/
admission or usable command.

31 bounded synthetic controls, <=8256 oracle operations; actual nonempty setup
<=1 geometry/selected intake,2 native intakes, otherwise none. Separate radial/
radius faults, signed/negative-radius words, rounding/subnormal/finite extremes/
overflow exact targets/nonfinite unknown, max32/empty and typed/ingress/binary
rejection. Input/tick/RNG preserved. Three pytest positions including failures/
aborts: first31/60 seconds, one necessary repair reserve, final root/300 seconds;
retain `cylinder-267-*` logs. No old refunds/protected runs/task data/dependencies/
hardware. Next cap stored-word hit-mask/candidate correspondence independently
from arithmetic/geometry qualification, then conservative minimum words.

First31 passed,3099 deselected,0.63 s. Required root4053 passed,1 known
transformer QDQ xfailed,71 warnings,99.95 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. AST proves only new cap
square helper/test added; all prior source/test nodes intact, no existing
signature changed. Two of three pytest positions used, no failures/aborts;
unused reserve is not follow-on authority. Logs `cylinder-267-focused-1.log`/
`cylinder-267-root-1.log` retained under recovery directory. No additional
C/Arm/sanitizer/board opt-in gates ran.

Actual nonempty/max32/empty controls, independent radial/radius faults, negative
radius arithmetic (not geometry), signed words/rounding/subnormal/finite extremes/
overflow exact targets/nonfinite unknown and typed/ingress/binary rejection
verified within caps, input/tick/RNG unchanged. Max32 reaches6208 values/8256
binary+oracle operations; source ceiling remains4096 bits. All eight flags false,
no isolated relative-square multiply/add/FMA rounding, primitive uniform/
numerical/physical/source/geometry/coverage/clock/one-use/permission/admission or
usable command. Next cap stored predicates (distance>=0 and radial<=radius^2)
separately from observed-hit candidate selection and conservative minimum words.
Archive whole256-260 losslessly before further root review growth.

## 268. Supplied-Word Cylinder Cap Mask/Candidate Correspondence (2026-11-10)

Checkpoint `2cc5766` pushed/clean. Native cap hit is distance>=0 and stored
radial<=stored radius^2; candidate uses observed hit?raw distance:+inf.
Hypothesis: report predicates/hit correspondence separately from observed-hit
candidate word selection, not arithmetic or geometric validity. All operands
non-NaN, including raw +/-inf; candidates finite/+inf only. Signed-zero candidate
word changes are separate mismatches; hit=True/+inf and inf<=inf matches do not
prove a finite/geometric intersection. Negative squared operands can match
comparison but not geometry. <=32 cylinders/64 rays/6176 canonical words/32
characters,2048 literal bools/entries,4096 predicates/4096 consistency checks.
No rational work/intake/read/hash/retention/replay/clock/RNG or composition. All
eight flags false, no primitive uniform/numerical/physical/source/geometry/
coverage/clock/one-use/permission/admission or usable command.

35 bounded synthetic controls, same predicate/consistency oracle caps; actual
nonempty setup <=1 geometry/selected intake,2 native intakes, otherwise none.
Separate mask/candidate faults (both observed-hit directions), zero-boundary/
signed-zero words, infinities/nonphysical squared operands/max32/empty and typed
rejection. Input/tick/RNG preserved. Three pytest positions including failures/
aborts: first35/60 seconds, one necessary repair reserve, final root/300 seconds;
retain `cylinder-268-*` logs. No old refunds/protected runs/task data/dependencies/
hardware. Next conservative cap minimum words from captured observed predecessor/
candidate/result, preserving equal-value/different-word ties.

Whole256-260 archived verbatim in `docs/review/256-260.md`, five design targets
rebased; originals `cylinder-268-review-before.md`/`cylinder-268-design-before.md`
and guarded one-shot `archive-268.py` retained in recovery directory. Archive
check passed, root786/archive206 lines before this record; whitespace including
staged archive passed. Historical failures/ledgers/Sources preserved, no code
gate rerun for document migration. Do not rerun successful migration utility.

First35 passed,3130 deselected,0.53 s. Required root4088 passed,1 known
transformer QDQ xfailed,71 warnings,93.33 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. AST proves only new cap
mask/candidate helper/test added; all prior source/test nodes intact, no existing
signature changed. Two of three pytest positions used, no failures/aborts;
unused reserve is not follow-on authority. Logs `cylinder-268-focused-1.log`/
`cylinder-268-root-1.log`/`cylinder-268-archive-1.log` retained under recovery
directory. No additional C/Arm/sanitizer/board opt-in gates ran.

Actual nonempty/max32/empty controls, both predicate boundaries, separate mask/
candidate faults (both observed-hit directions), signed-zero word mismatch,
nonfinite/nonphysical squared operands and typed rejection verified within caps,
input/tick/RNG unchanged. Matching hit=True/+inf/inf<=inf and negative squared
comparisons remain word correspondence only, not finite/geometric intersection
or arithmetic validity. All eight flags false, no primitive uniform/numerical/
physical/source/geometry/coverage/clock/one-use/permission/admission or usable
command. Next conservative cap-minimum words from captured observed predecessor/
candidate/result, preserving equal-value/different-word ties without host adoption.

Whole-section byte checks and prior REVIEW/Sources/design/stable AGENTS
conservation passed; ten changed-context local targets valid, no stale root
256-260 anchor targets in searched unignored Markdown. Originals/logs retained.

## 269. Supplied-Word Cylinder Cap Minimum Correspondence (2026-11-10)

Checkpoint `84f8bfa` pushed/clean. Native cap minimum consumes captured observed
predecessor/candidate; hypothesis: independently report numeric minimum and word
correspondence without reconstructing a preceding result. Strict lower operand
or identical words select known word; equal-value/different-word ties unresolved
when numeric minimum matches, wrong numeric value remains mismatch even on ties.
No host signed-zero tie semantics adopted. <=32 cylinders/64 rays/6144 canonical
finite/+inf words/32 characters,2048 entries/10240 helper operand-word comparisons,
aggregate counts separate. No rational work/intake/read/hash/retention/replay/
clock/RNG or composition. All eight flags false, no primitive uniform/numerical/
physical/source/geometry/coverage/clock/one-use/permission/admission or usable command.

31 bounded synthetic controls, <=16384 oracle comparisons; actual nonempty
setup <=1 geometry/selected intake,2 native intakes, otherwise none. Both strict
selections/identical or signed-zero ties/wrong numeric or word results for both
strict selections, captured predecessor independent of bad earlier result,
finite extremes/+inf/max32/empty and typed preflight; input/tick/RNG preserved.
Three pytest positions including failures/aborts: first31/60 seconds, one
necessary repair reserve, final root/300 seconds; retain `cylinder-269-*` logs.
No old refunds/protected runs/task data/dependencies/hardware. Next bounded
captured cylinder stage-chain word correspondence before source composition;
minimum ties and all numerical/geometry/qualification limits remain unresolved.

First31 passed,3165 deselected,0.72 s. Required root4119 passed,1 known
transformer QDQ xfailed,71 warnings,97.07 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. AST proves only new cap
minimum helper/test added; all prior source/test nodes intact, no existing
signature changed. Two of three pytest positions used, no failures/aborts;
unused reserve is not follow-on authority. Logs `cylinder-269-focused-1.log`/
`cylinder-269-root-1.log` retained under recovery directory. No additional
C/Arm/sanitizer/board opt-in gates ran.

Actual nonempty/max32/empty controls, both strict selections/identical or signed
zero ties, wrong numeric even on tie, strict value-correct/wrong-word results for
both selections, independent captured predecessor, finite extremes/+inf and
typed rejection verified within caps, input/tick/RNG unchanged. All eight flags
false, no primitive uniform/numerical/physical/source/geometry/coverage/clock/
one-use/permission/admission or usable command. Next bounded captured stage-chain
word correspondence: side/top predecessor to preceding observed minimum,
post-wall start and final pre-noise ranges, without minimum recomputation,
tie resolution or numerical/geometry/source qualification.

## 270. Captured Cylinder Stage-Chain Word Correspondence (2026-11-10)

Checkpoint `1e2696e` pushed/clean. Native owning path passes post-wall ranges to
near side, far side, cap, next cylinder and finally pre-noise ranges. Hypothesis:
each captured predecessor should match preceding observed result words, without
recomputing or correcting any minimum. Empty path compares post-wall/pre-noise.
Signed-zero word differences remain faults, not adopted minimum tie semantics.
Coherent non-minimal chain may match wiring, not operation correctness.

Finite routine plan: 36 synthetic controls, <=32 cylinders/64 rays/12416 canonical
finite/+inf words/32 characters; <=6144 stage entries plus64 final entries/6208
helper word comparisons, aggregate counts separate, <=6208 oracle comparisons.
Actual empty/one/two fixtures each <=1 geometry/selected intake,2 native intakes
(family <=3/3/6); other controls no setup work. Broken wall/side/top/inter-cylinder/
final links, one bad after affecting only next link, signed zeros, non-minimal
coherent/extremes/max32/empty and typed preflight; input/tick/both RNGs unchanged.
No diagnostic intake/read/hash/retention/replay/clock/rational work or composition.
Three pytest positions including failures/aborts: first36/60 seconds, one
necessary repair reserve, final root/300 seconds; retain `cylinder-270-*` logs.
No historical refunds/protected studies/task data/dependencies/hardware. All eight
flags false; words do not establish numerical/physical/geometry/coverage/source/
clock/one-use/permission/admission or usable command. Next supported retained
cylinder composition without turning matching chain words into qualification.

First36 passed,3196 deselected,3.44 s. Required root4155 passed,1 known
transformer QDQ xfailed,71 warnings,99.77 s; root Ruff, changed-file format check
and whitespace passed. Editor/Pylance syntax clear. AST proves only new stage
chain helper/test added; all prior source/test nodes intact, no existing
signature changed. Two of three pytest positions used, no failures/aborts;
unused reserve is not follow-on authority. Logs `cylinder-270-focused-1.log`/
`cylinder-270-root-1.log` retained under recovery directory. No additional
C/Arm/sanitizer/board opt-in gates ran.

Actual empty/one/two chains match; broken boundary words and signed-zero word
changes report independently. Bad observed after affects next link only;
coherent non-minimal chain matches wiring without minimum proof. All eight flags
false, input/tick/RNG preserved. Next bounded matched retained cylinder selection
reports, retaining original epoch/tick/delivery and closing comparisons; no
source/numerical/physical/geometry/coverage/clock/one-use/permission/admission.

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
