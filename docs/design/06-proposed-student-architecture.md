## 6. Proposed Student Architecture

### Initial Data Path

```text
Host state packet: ego-state, goal, health, task ID    On-module sensors: ToF grid, camera
        |                                                       |
        v                                                       v
M55: validate schema, profile, ranges, and sensor ages; normalize; update history buffer
        |
        v
Neural-ART: static INT8 trunks (Conv + ReLU) for state history, depth grid, and camera
            frames from the ISP; optional text-tag branch
        |
        v
M55: fuse and pool features; per-question heads of the active profile -> logits
        |
        v
M55: softmax/sigmoid, temperature, confidence, smoothing, rejection policy
        |
        v
Decision packet -> host controller (actuation, interlocks, fail-safes)
```

Start with approximately 0.25-1 million parameters and one task. Increase model
size only when learning curves and controlled comparisons demonstrate a need.
The compiled memory footprint, not the training parameter count, controls fit.

Heads cost K x C MACs, microseconds on the M55, and keep the NPU graphs static
Conv + ReLU trunks that are simple to map and validate. Estimates in
[REVIEW.md](../../REVIEW.md) §6.2 put small CNN students at tens of milliseconds on
the M55 alone, so an M55-only baseline is viable; measure whether the camera
trunk needs the NPU.

### Text Branch

Use the text branch only for operator commands or mission text that cannot be
enumerated; enumerated task IDs are simpler to validate. Gather is a software
operator on Neural-ART anyway, and writing INT8 embeddings straight into the
input buffer costs only T x d bytes (12 KiB for T = 128 and d = 96). Masked
pooling on the M55 removes padding effects exactly and avoids global-pooling
window limits.

Use a compact learned embedding, convolutional blocks with constant weights,
ReLU, supported pooling, and a dense head. A 1D convolution can be represented
using a singleton spatial dimension; final layout must be compiler-tested.

Compare byte-level encoding with a small domain tokenizer. Byte encoding
reduces vocabulary and firmware tokenizer complexity but increases sequence
length, especially for multilingual text. A small tokenizer reduces sequence
length but needs a matching embedded implementation and vocabulary tables.

Specify Unicode/byte handling, normalization, separators, padding IDs, maximum
length, pooling masks, and overlength policy. Do not silently truncate away a
negation or essential field. Python and firmware preprocessing need shared
golden input/output examples.

Prefer channel counts aligned with the convolution units (for example 96 or
128 inputs and 24, 48, or 96 outputs), kernel widths of 3 or 6 with small
dilations, folded BatchNorm, and no LayerNorm or attention in the first
version. Keep the compiler's software Gather as the fallback if the M55 gather
measures worse; do not create a custom kernel upfront.

### Numeric and Temporal Branch

Pass numeric ego-state directly: one body frame, SI units, bounded per-profile
normalization, validity flags, and sensor ages. Keep the history window (for
example 8-16 ticks) in a ring buffer on the module and feed it as a
`[1, C, T, 1]` tensor to a small 1-D convolution, or use an MLP when
instantaneous state suffices. Mark dropped or late packets as gaps instead of
interpolating silently.

Do not encode deterministic thresholds and arithmetic as natural-language
strings unnecessarily. Range checks, stale-data detection, geometric checks
such as braking distance, and hard safety conditions belong in application
logic. Reject non-finite or invalid values before inference.

### Spatial and Vision Branches

An 8x8 multizone ToF grid ([VL53L8CX][vl53l8cx]: 4x4 or 8x8 zones, up to
400 cm, a 60 Hz frame-rate capability; confirm the rate at 8x8 in the
datasheet) is a 64-value depth image; a few small convolutions or an MLP
process it, and a four-frame history is 256 values. For a camera branch,
the N6's ISP can feed the NPU by DMA; start from small CNNs at 64x64 to 128x128
input and measure the vision trunk against the §8 budgets early, because it
will dominate them. Mount sensors identically on every unit of an embodiment
profile, or the student sees a different input distribution.

### Decision Semantics

| Output type | Model and training semantics |
| --- | --- |
| Mutually exclusive choice | Categorical logits, softmax, categorical supervision |
| Binary decision | Binary logit/sigmoid, Bernoulli supervision |
| Independent set membership | Per-label logits/sigmoid, independent binary supervision |
| Ordered score | Distribution over ordered levels with explicit level meanings |

For an ordinal score, a useful reported value is the expected level under the
predicted distribution. Do not describe it as a universal confidence score.
Do not apply one categorical softmax to labels that can be true independently.

The application-facing result should include task and schema versions, status,
selected label(s) or score, the probability distribution, and an explicit
rejection reason when applicable. Keep Jev's limits: at most 255 options and
2-10 score levels.

The reference systems define `confidence` differently, so the device must
implement one definition explicitly:

| Answer type | TypeSafe Jev ([definition][typesafe-confidence]) | Vela 2.0 | Decision 3.0 |
| --- | --- | --- | --- |
| Choice | (p_max − 1/n) / (1 − 1/n) | p_1 − p_2, the top-two margin | 1 − H(p) / ln n, with H the Shannon entropy |
| Score | max(0, 1 − Σ p_i·\|i − m\| / MAD_uniform), m = mode | One minus the normalized variance, 1 − Var(p) / Var(uniform) | 1 − H(p) / ln n |
| Noul | None returned; \|2p − 1\| suggested | None returned | None returned |

For Vela's own example choice distribution (0.727, 0.217, 0.056), Vela reports
0.51, Jev's formula gives 0.59, and Decision 3.0's gives 0.34. For drop-in Jev
API compatibility, implement TypeSafe's formulas on host and device. Either
way, `confidence` is a distribution statistic and must not be renamed as
probability of correctness.

Export logits initially and calculate the small final softmax/sigmoid on M55.
ST's [compiler documentation][st-compiler] notes that `--expand-softmax` can
preserve the winning class while changing probabilities; full expansion is
another option but is not bit-true either. Calibrate and validate the actual
deployed output path regardless of where probability calculation runs.

Per-tick decisions can oscillate near a decision boundary. Apply hysteresis or
a minimum dwell time to mode and steering selections on the module, document it
in the interface contract, and report raw distributions alongside smoothed
selections. Smoothing adds latency, so validate it in closed loop (§7).

#### Host-Only Decision Math (Approved, 2026-10-19)

The user separately approved host-only stable softmax/sigmoid, shared existing
Jev confidence, synthetic parity/failure tests, host/sanitizer/Arm checks,
documentation and local commits. This authorizes numeric reference tooling,
not heads/model execution, calibration, thresholds, smoothing/rejection policy,
ToF/tensors, linked firmware/board work, labels/data/training, dependencies or
an interface freeze. The [math API][decision-math-api] and
[source][decision-math-source] use standard C `exp` with bounded fixed temporary
arrays, no allocation or HAL. Link math users with the platform math library
(`-lm` in host tests); Arm object compilation alone does not establish a usable
linked target math runtime.

`mc_v0_softmax` accepts finite binary32 logits for only 2, 4 or 5 options, uses
maximum subtraction and double intermediates, then emits binary32 probabilities.
`mc_v0_sigmoid` accepts one finite binary logit and emits `[false, true]`, using
a sign-stable expression equivalent to softmax of `[0, logit]`. Capacities count
float elements, not bytes. Outputs are written only on success and exactly for
the requested options; unused capacity remains untouched. All pointers must be
nonnull; callers supply valid nonoverlapping objects and truthful lengths and
capacities. No size-query mode, arbitrary option count, temperature or calibration
is added. Finite extreme logits may saturate/underflow to exact one/zero; there
is no probability floor or second normalization after binary32 rounding.

The newly public `mc_v0_answer_confidence` stays in the codec and shares its
unchanged arithmetic with encoding/decoding. It validates fixed question ID,
type/count/selected metadata and finite probabilities in [0,1] with the existing
1e-6 sum tolerance before writing a double result. Choice/score retain the first
raw mode and ignore the selection for calculation; noul returns absent `-1`.
Input confidence and unused probability cells are ignored. Null pointers,
unsupported softmax counts, short capacities and invalid numeric/schema inputs
return existing argument/length/decision errors without output writes;
`MC_V0_MATH_OK` aliases zero without renumbering existing errors. These numeric
errors do not choose a robot rejection/fallback policy or output a recommendation.
Binary32 float, at least binary64 intermediate precision/range and non-fast-math
builds are required; no cross-platform bit-exact `libm` promise is made.

Core verification: 45 math checks cover stable equal/extreme/nontrivial logits,
sigmoid equivalence, existing confidence/first-mode rules, all 256 values of
each metadata byte, invalid probabilities, unsupported counts, capacities,
nulls and output/source preservation. Four extra build cases compile math with
host GCC 13.3 and Cortex-M55 Arm GCC 13.2 and reject fast/finite-only math.
Completion adds fixed shift/permutation checks and 1,000 seeded synthetic
question outputs across 250 fault-status packets. Binary32 probabilities match
Python stable scalar references under the existing test-only absolute/relative
assertions (5e-8/1e-7), not an adopted model-quality tolerance. Shared confidence
matches Python; C frames exactly match Python bytes and round-trip through
native decoding/re-encoding and both chunked stream paths. Native ASan/UBSan
passes exact input/output allocations, short/full/spare capacities, every
nonfinite input position, unsupported counts including `SIZE_MAX`, all metadata
byte values and null/unchanged-output guards, alongside prior codec/history
checks. All 173 C checks, 235 interface tests and 840 repository tests pass plus
the known transformer expected failure; host/Cortex-M55 objects, unsafe-math
guards, lint/format/editor and documentation checks pass. REVIEW.md §§59-60
record core and completion. These finite checks establish no formal numerical/
memory guarantee, cross-platform bit identity, timing, SRAM-fit, target execution,
calibration, task quality or physical safety. This completes the approved
numeric reference package only. Wire/goldens, normal inputs/defaults, mode
abstention, quarantine and all other data/hardware/runtime gates stay unchanged.


#### Host-Only Synthetic Head Reference (Approved, 2026-10-19)

The user approved a complete host-only artificial-head reference and reproducible
verifier package: bounded caller-buffer arithmetic, artificial weight/feature
fixtures, existing probability/confidence/wire integration, synthetic Python
parity and rejection/overflow/atomicity tests, native sanitizers, host/Arm builds,
an evidence report, documentation and local commits. No trained model, production
head/blob format, student architecture/input change, ToF/tensor packing, robot
timing/rejection/safety policy, real log/label/task-data use, training, dependency/
download, linked firmware or hardware work is approved.

The [head API][head-reference-api] and [source][head-reference-source] compute a
row-major affine map from binary32 features, weights and biases to binary32
logits. Diagnostic limits are 1-256 features and 1-5 rows, not a frozen trunk
width, deployed head shape or blob representation. Weights use consecutive rows,
with `feature_count` values per row; biases have one value per row. All lengths
and capacity count float elements. Extra weight/bias capacity and trailing
feature storage are ignored, not serialized. Inputs must be finite. The initial
single-correction sum failed a nested-scale cancellation fixture (zero instead
of the exact unit residual). A fixed partial-sum expansion now preserves it and
128 shuffled multi-scale variants, including signed minimum-subnormal residuals.
Scratch is 257 doubles plus five floats, not measured stack/SRAM fit or a target-
optimized INT8 kernel. Final nonfinite/out-of-binary32-range values fail before
the float cast. Underflow is allowed; no universal correct rounding/error bound
is claimed.

All pointers must be nonnull and reference valid nonoverlapping objects with
truthful lengths. Dimensions are bounded before multiplying lengths. Rejection
leaves output unchanged, including when a later row fails; success copies only
the requested rows and leaves spare capacity untouched. Inputs are not modified.
Existing argument/length/decision errors are reused, and `MC_V0_HEAD_OK` aliases
zero without renumbering them. The caller chooses any later normalization or
selection; no recommendation/status or robot policy is inferred by this API.
Binary32 and at least binary64 arithmetic/range and non-fast-math builds are
required. There is no HAL, allocation, model loading or board integration.

[Shared host bindings][native-verifier] now own the existing ctypes ABI and a
fixed native compiler command, reused by tests. Builds reject reused library
outputs and record source/header/compiler-driver/library hashes with pre/post
source and compiler checks. These are local provenance checks, not attestation
of the complete compiler toolchain, math library or environment. The completed
CPU-only CLI accepts 1-1,024 artificial cases and an unsigned seed, uses fresh
noncontaining report/build paths and writes success only after all checks.
Configuration, existing/dangling-symlink paths and missing compilers reject before
creation; failed later checks may retain build artifacts but no success report.
Runtime checks are explicit exceptions, tested under `python -O`. Result digests
exclude timestamps/build paths, not a promise of identical whole reports/binaries.

Completion: 61 head cases cover row order, selected dimension combinations,
lengths/nulls/nonfinite inputs, ignored storage, copies, cancellation and overflow.
Native ASan/UBSan tests actual feature/weight/bias/output allocations at 1/3/256
features and all 1-5 rows, short-to-spare capacities, ignored tails, cancellation,
later-row overflow and null/nonfinite rejection, alongside prior native checks.
Eighteen verifier cases cover reproducibility, strict scope/configuration,
reuse/containment/symlinks, missing compiler, source drift, injected failures,
report hash and optimized-Python CLI execution. Four new build checks pass.
All 238 C checks, 318 interface tests and 923 repository tests pass plus known
transformer expected failure; host/Cortex-M55 objects, unsafe-math guards,
lint/format/editor and documentation checks pass.

The [actual report][native-head-report] uses seed 20261019 and 1,024 artificial
cases: feature counts 1/2/3/8/32/64/128/256, 4,096 question outputs, 14,336 logits,
15,360 probabilities and 2,048 state/fault-decision frames. Fixture argmax is not
a runtime selection policy. Head features are generated arrays, not packed
state/history; separate history/stream checks do not define an observation or
tensor adapter. All 1,024 input/logit/frame hashes and 225,280 wire bytes were
independently regenerated in Python without native calls; source/compiler/
library/result hashes match. Maximum checked logit/confidence errors were zero;
probability error was 2.9798810863290726e-8 versus double reference. These bounded
dyadic fixtures are not task-quality/calibration or arbitrary-input qualification.
Report SHA256: `0dcf13896d3aa1f21f9133e8a28b2381f7109fb1f454b9044db83492fe8267ab`;
result SHA256: `7f24377c218560fc4a81b49458b971203f8b48819fd7f45b01e8a2b2dc30a76f`.
Sanitizer/Arm gates are separate pytest evidence, not actions by this CLI.
This completes the approved package, not formal numerical/memory safety, timing,
SRAM fit, target execution, trained heads/blob format, task data, model runtime/
training, input/policy or other hardware gates. REVIEW.md §§61-62 records limits.


#### Offline Reference Build Audit (Approved, 2026-10-19)

The user approved the complete CPU-only build-audit package: the four unchanged
C reference modules at `-O0/-O2/-Os`, synthetic host parity, Cortex-M55 object
inspection, compiler-reported per-function stack usage, raw evidence/hashes,
strict fresh outputs, tests, a bounded run/independent audit, documentation and
local commits. This does not approve target linking/execution, production heads,
new budgets, architecture/input/history/default/policy changes, ToF/tensors,
simulator/log/task-data/label use, inference/training, dependencies/downloads,
ST/licence actions or board work.

The [audit CLI][reference-build-audit] uses the already-installed host and Arm
GCC/binutils. It builds three host libraries and executes the existing artificial
head/probability/confidence/wire/history verifier with identical cases and seed.
The complete canonical evidence must agree across optimization levels. Separate
objects for both targets and the original four sources produced a 24-object matrix using
`-fstack-usage`; Arm adds `-mcpu=cortex-m55 -mthumb`, without linking or running.
Little-endian relocatable ELF identity is checked; Arm must be ELF32/machine ARM.
GNU `size` SysV section rows, `nm` undefined symbols and tab-delimited GCC `.su`
records are parsed strictly, retaining qualifiers and rejecting malformed rows,
duplicates and inconsistent totals. Raw `readelf` headers/sections/architecture
attributes, all object command outputs, compiler diagnostics, objects and `.su`
files remain available in the ignored work directory. The report records source,
tool-driver and every artifact byte count/SHA256, flags and source/tool stability.

Report/work paths must be fresh and noncontaining, with direct symlinks rejected
before tools or creation; missing tools also reject before creation. Failed
checks write no success report, though partial artifacts remain. Command launch,
nonzero exit and timeout diagnostics are retained. Optimized Python uses the
same explicit validation, not removable assertions. Local fresh-path checks are
not a concurrent adversarial filesystem boundary; driver hashes do not attest
assemblers, linkers, runtime libraries or the complete toolchain.

Core verification: 42 audit checks plus seven native optimization checks pass,
including a real eight-case matrix, strict preflight/parsers, failures, drift,
cross-optimization mismatch, artifact symlinks and `python -O` CLI. All 367
interface tests and 972 repository tests pass plus the known transformer expected
failure; lint/format/editor diagnostics and existing native sanitizer checks pass.
The full 1,024-case-per-optimization evidence run/independent audit is next,
not claimed by these test fixtures. REVIEW.md §63 records this checkpoint.

Completion (2026-10-19): the [bounded report][reference-build-audit-report] records
all 24 objects and three host runs at seed 20261019, each with the same 1,024
artificial cases, 4,096 question outputs and 2,048 frames (225,280 frame bytes).
All three complete evidence objects equal the prior hash-pinned independently
audited head report, including all 1,024 input/logit/frame rows and canonical
result `7f24377c218560fc4a81b49458b971203f8b48819fd7f45b01e8a2b2dc30a76f`.
These are repeated fixtures, not three independent task cohorts. Maximum checked
logit/confidence errors stay zero and probability error 2.9798810863290726e-8.

| Target | Optimization | Summed `.text` Bytes | Summed `.rodata` Bytes | Dense-Head Reported Stack Bytes |
| --- | --- | --- | --- | --- |
| Host GCC 13.3 | `-O0` | 11,287 | 200 | 2,240 |
| Host GCC 13.3 | `-O2` | 6,961 | 176 | 2,144 |
| Host GCC 13.3 | `-Os` | 4,959 | 176 | 2,144 |
| Cortex-M55 GCC 13.2 | `-O0` | 7,234 | 8 | 2,176 |
| Cortex-M55 GCC 13.2 | `-O2` | 4,636 | 8 | 2,192 |
| Cortex-M55 GCC 13.2 | `-Os` | 3,850 | 8 | 2,200 |

Text/rodata totals sum the four separate reference objects, not linked images.
All reported stack qualifiers were `static`, which does not bound callees or
the full stack. All objects report zero `.data/.bss`; caller-owned state/history,
buffers, stack and runtime still consume RAM and are not counted by those zeros.
Per-object undefined symbols include the cross-module validator, `exp`, memory
helpers and Arm software-double helpers (`__aeabi_*`); host objects also refer
to `__stack_chk_fail`. No deployed ABI/math runtime is selected or qualified.

The independent audit read ELF section/symbol tables directly with standard
binary structures, separate from production CLI parsers, and compared every
reported section size/address and undefined symbol. It independently reconstructed
all `.su` records, checked all command exits/flags and Cortex-M55 attributes, all
12 source/eight tool identities and every one of 153 raw artifact hashes. All
three host results match the prior independently reconstructed baseline. Report
SHA256: `e08de9ddabbd4c038752bd13b318cf10f6b19c472cc912de64061fd488ba9351`.
Raw artifacts stay ignored in `.runs/reference-build-audit-20261019/`. No source
changed after the run; the last code gate remains 972 passes plus the known
transformer expected failure, not newly run board evidence. Documentation and
evidence checks pass. REVIEW.md §64 records completion; this exhausts the package.

Per-function stack numbers are compiler output, not call-chain/full-program
bounds: external callees, interrupts/runtime, inlining and dynamic qualifiers
must remain explicit. Section listings include metadata and unlinked/duplicate
helpers, not deployed ROM/RAM or SRAM-fit measurements. Undefined symbols are
per-object requirements, not a linked dependency closure. No resource threshold,
target math qualification, timing, formal numerical/memory guarantee or physical
safety claim is adopted. Other Tasks 6/9/13/ST/board gates remain unchanged.

Maintenance (2026-10-19): a real synthetic parent/child regression showed that
`subprocess.run` killed only the timed-out command and left its child running.
The shared native command runner now requires POSIX process groups, starts a
new session with closed stdin, captures output and kills the command's group
on timeout, interruption or communication failure before draining output and
reaping the direct command. Compiler/version checks, host shared builds and
audit object tools use it. Timeout output is preserved; interruption remains a
`KeyboardInterrupt` subclass with command/stdout/stderr diagnostics. Audit logs
record interruption, and interrupted host builds cannot publish a success report.
This is cleanup of cooperating processes in that group, not containment of
arbitrary programs that escape it or a whole descendant-tree sandbox.

Seven new cases include real Linux `/proc` checks for timeout, interruption and
an exited leader whose child holds the output pipe, plus command output/closed
stdin, checked/unchecked nonzero exits and interrupted-build failure reporting.
All 374 interface and 979 repository tests pass plus known transformer expected
failure; lint/format and existing native sanitizer/host/Arm gates pass. No new
study or report was generated: historical evidence and exporter hashes remain
unchanged, not silently reassigned to the repaired tools. REVIEW.md §65 records
this fix; no C/wire, accepted input/default/policy, data/training, dependency,
ST/licence, linked firmware or hardware boundary changed.


#### Host-Only Synthetic Decision Assembly (Approved, 2026-10-19)

The user approved the complete host-only synthetic assembly package: bounded
caller-buffer composition of the four existing heads, strict metadata/dimension
validation and atomic failure, Python parity, native sanitizers, host/Arm object
checks, reproducible synthetic evidence, documentation and local commits.
This does not authorize trained/production models or blob formats, trunk/ToF/
tensor preprocessing, architecture/input changes, freshness/threshold/smoothing/
fallback policy, real logs/task labels/datasets/splits, simulator collection,
real-model inference/training, dependencies/downloads, ST/licence actions,
target linking/execution or board integration. Broader Task 13 remains blocked.

The [assembly API][assembly-api] and [source][assembly-source] accept a complete
four-answer `mc_v0_decision` metadata object and exactly four `mc_v0_head_input`
descriptors, ordered by question ID. Each descriptor has its own feature vector,
row-major weights and biases with float-element lengths. Existing reference
limits remain 1-256 features and rows 1/4/4/5; these are not an architecture or
production format. Callers supply initialized, valid, nonoverlapping objects and
truthful lengths; pointer validity/aliasing are preconditions, not runtime checks.

The full answer mask must be 15, including for non-OK status. Prefix/question/
selection metadata passes the unchanged codec validation before any head buffer
is read. Existing affine and sigmoid/softmax primitives compute probabilities;
the unchanged encoder/decoder canonicalizes confidence and unused storage before
publishing output. Metadata probability/confidence storage is ignored. Caller
status, selected indices, sequence, timestamp, latency and versions are preserved,
not inferred or made safe by assembly. In particular, selections need not be
argmax, and fault-status choices are not usable recommendations. Existing error
values are reused; output remains byte-for-byte unchanged on failure, and inputs
are never mutated under the pointer preconditions. The implementation allocates
no heap and uses fixed temporary native/frame/logit storage; no stack/call-chain,
timing or SRAM-fit claim follows.

The [verifier][native-verifier] has a separate `--assembly-reference` opt-in.
It retains the ordinary primitive evidence path by default. Artificial assembly
fixtures cycle all six statuses and all option selections, independently of
argmax, with synthetic model version 1. Complete metadata is added to fixture
hashes. C-assembled frames must exactly match Python frames based on separately
checked affine/normalization primitives; source preservation, confidence, history
and both streams remain checked. These fixtures are not robot-selection policy.
Both modes are checked under `python -O` and host `-O0/-O2/-Os`.

Core gate: 102 assembly cases and six verifier checks, actual-allocation native
ASan/UBSan, all selection/count byte values, short buffers, nonfinite/overflow,
metadata preflight and late-head atomic failures pass. All 490 interface and
1,095 repository tests pass plus the known transformer expected failure;
lint/format/editor diagnostics and host/Cortex-M55 objects pass. The shared
build audit now includes five sources, hence 30 objects; its historical 24-object
report and all prior source hashes remain historical evidence, not an assembly
resource measurement. The approved 1,024-case run/independent audit was next
at this core checkpoint.
REVIEW.md §66 records this core checkpoint and boundaries.

Completion (2026-10-19): the [assembly report][assembly-report] records 1,024
artificial decisions, 4,096 question outputs, 14,336 logits, 15,360 probabilities
and 2,048 frames. All six caller statuses occur (171 each for 0-3, 170 each for
4-5), with all selections represented and 2,840 nonargmax choices preserved.
Every input/logit/frame digest and all 225,280 wire bytes were independently
reconstructed using scalar Python, explicit binary structures and CRC, without
native or verifier calls. All 13 source records, compiler-driver identity/version,
library ELF/hash and canonical result hash match. Old firmware/protocol sources
and historical head/build-audit report hashes remain unchanged.

Maximum checked logit/confidence errors are zero; probability error versus double
is 2.9798810863290726e-8. Feature/weight/bias fixtures match the prior head study;
new caller metadata does not create an independent task cohort or quality claim.
Report SHA256: `bfc9495aaa796dc0c105367b91a7bdac446532f2b68091c84c971224424caf7d`;
result SHA256: `a8dbd4a71ee81cfc4e06747a44b36fd254b320a406be4abd66e88b70f95d4221`.
Raw host build stays ignored in `.runs/native-assembly-20261019/`; sanitizer/Arm
gates are separate tests, not CLI target actions. No code changed after the run;
the last full gate remains 1,095 passes plus the known transformer expected
failure, not a new board measurement. REVIEW.md §67 records completion. The
approved synthetic package is exhausted; all production/data/policy/ST/board
gates and accepted inputs/history/defaults/token limits remain unchanged.


#### Assembly Build Audit (Approved, 2026-10-19)

The user separately approved the complete host-only assembly audit: explicit
assembly mode in the existing [build audit][reference-build-audit], 1,024
synthetic cases at each of `-O0/-O2/-Os`, all five reference modules' host and
Cortex-M55 objects, section/dependency/per-function-stack evidence, independent
audit of fresh outputs, documentation and local commits. No target linking/
execution, production model, architecture/input/policy change, real logs/task
data/labels/splits, simulator collection, training, dependencies/downloads,
ST/licence or board action is authorized. All other gates remain unchanged.

`--assembly-reference` forwards the strict boolean opt-in to the unchanged
assembly verifier for every host optimization, and marks report scope. Default
primitive verification remains unchanged. Complete canonical evidence must match
across all three runs. The existing source/tool stability, fresh/noncontaining
output, raw diagnostic, object inspection and artifact hashing checks are reused;
failed verification, source/tool drift and cross-optimization mismatch still
cannot publish success. No C or wire behavior is changed.

Core gate: eleven new cases extend the real matrix and optimized-Python CLI to
both modes, check exact standalone-verifier parity and failure forwarding, and
exercise drift/mismatch plus strict pre-tool opt-in rejection. All 57 audit
checks, 501 interface and 1,106 repository tests pass plus known transformer
expected failure. Lint/format/editor diagnostics and all ten Pylance-resolved
call signatures pass; existing native sanitizers and host/Arm gates pass.
The full 1,024-case-per-optimization run and independent evidence audit were
next at this core checkpoint, not represented by the small test matrices. REVIEW.md §68 records this
checkpoint. Compiler stack frames exclude callees/interrupts/runtime; unlinked
sections and undefined symbols are not a deployed image, full memory/dependency
bound, accepted budget or target math/physical-safety qualification.

Completion (2026-10-19): the [assembly build report][assembly-build-report]
records all 30 host/Arm objects and three complete 1,024-case host verifications.
Each evidence object exactly matches the prior independently audited assembly
report, including 4,096 question outputs, all 1,024 input/logit/frame rows and
225,280 wire bytes. These are repeated artificial fixtures, not three independent
task cohorts. Canonical result remains
`a8dbd4a71ee81cfc4e06747a44b36fd254b320a406be4abd66e88b70f95d4221`.
Maximum checked logit/confidence errors remain zero; probability error remains
2.9798810863290726e-8 versus double reference, not task-quality evidence.

| Target | Optimization | Summed `.text` Bytes | Summed `.rodata*` Bytes | Assembly Reported Stack Bytes | Assembly Qualifier |
| --- | --- | --- | --- | --- | --- |
| Host GCC 13.3 | `-O0` | 12,362 | 204 | 480 | `dynamic,bounded` |
| Host GCC 13.3 | `-O2` | 7,591 | 180 | 464 | `dynamic,bounded` |
| Host GCC 13.3 | `-Os` | 5,428 | 180 | 432 | `dynamic,bounded` |
| Cortex-M55 GCC 13.2 | `-O0` | 7,876 | 8 | 376 | `static` |
| Cortex-M55 GCC 13.2 | `-O2` | 4,896 | 8 | 352 | `static` |
| Cortex-M55 GCC 13.2 | `-Os` | 4,078 | 8 | 344 | `static` |

Section sums cover five unlinked objects; assembly stack is its own compiler
record, not the dense-head or codec/math callees. Dense-head Arm records stay
2,176/2,192/2,200 bytes. All remaining functions report `static`; none report
unbounded `dynamic`. These qualifiers do not bound a whole call chain or total
RAM. All object `.data/.bss` are zero while caller objects/buffers, stack,
libraries, interrupts and runtime remain excluded. Undefined symbols retain
cross-module/libm/memory/software-double requirements, not a linked closure.

All 189 raw artifacts, 14 source/eight tool identities, compiler/library hashes,
every ELF section/undefined-symbol table, GCC stack row and command exit/flags
were independently checked without production parsers. Host evidence matches
the hash-pinned, independently reconstructed prior baseline. An audit-only
all-static assumption was corrected after observing the host assembly's raw
`dynamic,bounded` records; no exporter or artifact repair was needed.
Report SHA256: `1326101be0f51c4e6443afee940b6c90cfece4b9bf07eb5f1cd9b6ebb80d5ba9`.
Raw artifacts remain ignored in `.runs/assembly-build-audit-20261019/`.

No code changed after the run; the last full gate remains 1,106 passes plus
known transformer expected failure, 501 interface checks, lint/format/editor/
signature and native sanitizer gates. Historical reports retain original source
hashes. REVIEW.md §69 records completion, exhausting this approved package.
No target linking/execution, full stack/SRAM fit, new budget, task data/model/
training, policy/input/default or ST/board gate is cleared.


### Question Catalogue and Embodiment Profiles

Freeze a shared trunk on the NPU and store per-question heads as small,
versioned blobs evaluated on the M55. Adding or changing an in-domain question
then means: label in-domain data from the question's label source (§4), train
only the head on frozen trunk features, calibrate it through the deployed
numeric path, pass the same gates, and ship the blob. No NPU recompilation is
needed; trunk updates use ST's [runtime-loadable models][st-reloc] or a
firmware update. This works only if the frozen features carry what the new
question needs, so train the trunk multi-task on diverse in-domain questions.
It is configurability within a domain, not zero-shot behaviour.

An embodiment profile bundles everything frame-specific: input schema and
normalization, sensor mounting poses, the question catalogue and its heads,
calibration, rejection thresholds, smoothing, and the host's mapping from
rejections to fail-safes. Profiles that share inputs can share a trunk;
otherwise compile one trunk per profile and load it at boot. Each profile
passes the gates on its own frame. Heads and trunks are executable
configuration: sign them and verify them at boot (§10).

| Profile | Example question bundle per tick |
| --- | --- |
| Ground rover | Active rules catalogue 1: `path_blocked` (noul), `clear_sector` (choice: left, centre, right, none), `speed_tier` (score 0-3). Actual rules still require sensor/evidence qualification; mode is excluded. |
| Mini-drone | `path_blocked` (noul), `clear_direction` (choice, including up and down), `mode` (choice: advance, avoid, hover, return, land) |

### Later Option-Conditioned Extension

A runtime-option model must encode the state, question, and candidate
descriptions as model inputs and score each candidate. Merely changing JSON
around a fixed-class head does not add this capability.

Train with candidate-order permutations, appropriate masking, bounded question
and option lengths, and held-out tasks/options. Account for repeated candidate
encoding and multiple invocations in memory and latency measurements. Claim
zero-shot capability only after evaluation on genuinely unseen schemas and
options, not paraphrases of training labels. Crivo's `[OPT]` readout is a
published reference design, at 32 million parameters and above.

[decision-math-api]: ../../firmware/include/micro_classifier_math.h
[decision-math-source]: ../../firmware/micro_classifier_math.c
[head-reference-api]: ../../firmware/include/micro_classifier_heads.h
[head-reference-source]: ../../firmware/micro_classifier_heads.c
[native-verifier]: ../../interface/native_verify.py
[native-head-report]: ../../interface/reports/native-heads-20261019.json
[reference-build-audit]: ../../interface/build_audit.py
[reference-build-audit-report]: ../../interface/reports/reference-build-audit-20261019.json
[assembly-api]: ../../firmware/include/micro_classifier_assembly.h
[assembly-source]: ../../firmware/micro_classifier_assembly.c
[assembly-report]: ../../interface/reports/native-assembly-20261019.json
[assembly-build-report]: ../../interface/reports/assembly-build-audit-20261019.json
[st-compiler]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-compiler.html
[st-reloc]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-reloc-mode.html
[typesafe-confidence]: https://docs.typesafe.ai/confidence
[vl53l8cx]: https://www.st.com/en/imaging-and-photonics-solutions/vl53l8cx.html
