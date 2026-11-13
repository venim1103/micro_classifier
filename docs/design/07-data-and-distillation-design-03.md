#### Controlled Scalar Arithmetic Candidate (2026-11-03)

The user approved this design-only proposal preparation ([review §104][controlled-arithmetic-review]),
not implementation, numerical execution or adoption. The candidate is an
isolated private synthetic per-step arithmetic trace for P1-P3/P7, not a
replacement for `integrate`, the owner, the mathematical reference or runtime
rules. Recommended candidate: exact integer/rational operations on supplied
binary64 words, followed by explicitly specified round-to-nearest, ties-to-even
(`RN64`) at every original scalar rounding point. This defines proposed new
arithmetic semantics; it does not assert installed CPython/libm equivalence.

**Local hypothesis and static check.** A bit-pattern trace can make these four
rounding/branch operations explicit without purporting to qualify their caller
or opaque downstream primitives. The cheap documentation check must find
exactly four ordered row traces, distinct rounded operands, signed-zero and
remainder correction requirements, no owner/event update or downstream-row
qualification, and unchanged source/tests. No arithmetic fixture is executed.

`r`, `omega`, `d`, `pi_bits` and `two_bits` below are supplied finite binary64
words; `two_bits` represents the exact integer literal 2. `value` denotes exact
signed rational decoding, with a separate zero-sign tag. Operation names refer
to exact arithmetic before `RN64`, not Python float calls. Constant/source
binding and conversion into/out of these words remain separate obligations.

| Row | Proposed Ordered Trace | Compatibility/Stop Obligation |
| --- | --- | --- |
| P1 | `a=RN64(mul(omega,d))` | Keep the exact stored binary-step duration, not nominal `1/20`; reject unsupported input/packing evidence rather than applying a pose update. |
| P2 | `half=RN64(div(a,two_bits)); m=RN64(add(r,half))` | Round the division before addition; neither fuse nor substitute the ideal angle. |
| P3 | `b_q=RN64(mul(two_bits,pi_bits)); q=RN64(div(a,b_q))` | Bind the stored pi word, positive denominator and both rounding points; retain real-pi/argument error separately for later P4/P5 composition. |
| P7 | `x_1=RN64(add(r,a)); x=RN64(add(x_1,pi_bits)); b_r=RN64(mul(two_bits,pi_bits)); t=trunc(value(x)/value(b_r)); rho=value(x)-t*value(b_r); z=RN64(rho,zero_sign_of_x); u=fix_divisor_sign(z,b_r); r_next=RN64(sub(u,pi_bits))` | The quotient is exact truncation toward zero, not a rounded float division or negative floor division. `fix_divisor_sign` returns divisor-signed zero for zero residue, rounds `z+b_r` for negative nonzero residue, otherwise preserves `z`. |

P3/P7 retain their separate denominator occurrences; no constant hoisting or
shared intermediate is implied. The remainder path keeps the staged fmod-like
residue/sign-correction schedule, not a fused real-pi Euclidean wrap. A rounded
corrected residue may equal the stored period; do not clamp it to zero or
force a half-open heading interval. Current circular-reference branching and
unknown behavior remain separate. P4-P6 and G1-G3, float/NumPy boundary codecs,
source/wire ownership, full-motion error, physical and task-quality gates are
**not qualified** by this candidate. No code, bound, flag or verdict changes.

**Word boundary and proposed arithmetic kernel.** Accept only nonboolean
unsigned 64-bit integer words with an explicitly declared binary64 layout:
one sign bit, eleven exponent bits and 52 fraction bits. Reject all-one exponent
fields (NaNs/infinities), unsupported formats, malformed evidence and resource
preflight failure. Do not coerce arbitrary Python/NumPy values, strip signed
zero, infer source authority or accept an input merely because it can round-trip
through the wire. A future ingress/egress adapter must separately bind original
stored binary64 bytes, immutable constant words and output bit preservation.
This document does not capture or attest those words from the current process.

For normal fields $E,F$ and sign $s$, exact decoding is
$(-1)^s(2^{52}+F)2^{E-1075}$; for exponent field zero it is
$(-1)^s F2^{-1074}$. These are mathematical values represented by integer
pairs, not floating-power instructions. Keep zero's sign as a tag, not just
rational value zero.
Exact addition/subtraction/multiplication/division operate on integer numerator/
denominator pairs, with positive denominator. Division by zero is unsupported.
No float conversion, NumPy, libm, floating `log`/`round`, ambient rounding-mode
change or contracted/fused operation is part of the proposed kernel.

For a nonzero exact magnitude, determine its binary exponent by integer
bit-length/comparison, not a floating logarithm. Choose the binary64 lattice
quantum from that exponent, floored at subnormal spacing $2^{-1074}$. Use integer
quotient/remainder after exact scaling to that quantum; increment the quotient
when twice the remainder exceeds the denominator, or at equality when the
quotient is odd. Normalize a significand carry and pack the word exactly.
Normal/subnormal transitions, tie carries and the maximum-finite transition
must be proved, not handled by a float conversion. A rounded nonfinite result
stops unsupported, without publishing a partial trace or updating any owner.
An exact nonzero result rounded to zero retains its sign.

Specify zero rules independently: multiplication/division use operand-sign XOR;
addition of two negative zeros returns negative zero, while other zero additions
and exact nonzero cancellation return positive zero under this proposed mode.
Subtraction flips the right operand's sign, including zero, before applying the
addition rules. Exact rational evaluation alone is insufficient to infer these
tags. Source input zeros, underflow-to-zero and cancellation are distinct cases.

This is a narrow arithmetic specification, not a general soft-float library or
a claim about the current hardware mode. A vetted bit-exact library is another
possible implementation route, requiring separate source/licence/dependency
review; an IEEE remainder operation is not automatically Python `%`/fmod.
The integer-only route still trusts integer operations, memory/control flow,
bit packing and source/compiler identity. It reduces four FP-kernel dependency
questions; it does not waive Q0-Q5 or create a qualified implementation.

**Remainder and interval alternatives.** The proposed staged P7 default computes
the quotient's magnitude with unsigned integer division and applies its sign
for truncation toward zero; negative `//` is not that operation. It forms the
exact fmod-like residue from the *rounded* `x` and *rounded* positive `b_r`.
Residue representability and zero sign are proof obligations for this algorithm,
not inherited from a libm comment or sampled parity. Round/correct/pack in the
listed order, including `u==b_r` and the subsequent subtraction.

An independent rational Euclidean residue using the stored period can help
check algebraic sign/quotient relations, but any equivalence to the staged
rounding path must be demonstrated, not assumed. A real-pi interval wrap is
instead an ideal circular-reference object: uncertain period/quotient or a cut
requires all supported branches, not selection of a scalar nearest the observed
heading. It is not a replacement producer and must not alter `1bb89fe` or its
verdicts. Similarly, rounding an entire unfactored row once is a different
candidate from preserving every source rounding point.

**Compatibility levels and alternatives.** These are choices for review,
not an adopted configuration, dependency or replacement.

| Route | Benefit | Limitation/Proposed Use |
| --- | --- | --- |
| A: integer/rational RN64 bit trace | Explicit finite-format arithmetic, evaluation order and remainder branches, without these four native FP dispatch kernels. | Recommended first isolated prototype candidate. A new implementation/trusted base must be verified; byte equality with installed CPython is not promised. |
| B: retain installed CPython arithmetic | Preserves today's producer code and artifacts without migration. | Remains the current default. Needs actual dispatch/build/FP/domain/uniform-error evidence; further wrapper inspection alone does not supply it. |
| C: rational/interval reference only | Mathematical target/branch evidence with explicit uncertainty and no producer change. | Retain as independent reference evidence. It neither attests the installed producer nor defines a unique controlled binary64 result. |

Bit-format and literal-2 compatibility are different from preserving each
source rounding point, matching a newly specified finite arithmetic contract,
bit-for-bit agreement with the installed old producer, or full pose/State/wire
compatibility. Test/report these levels separately. Do not use disagreement
between A/B as proof that either is wrong until B's contract is independently
qualified; source-order agreement alone is not byte parity. No candidate
outputs may be spliced into current events, snapshots, cached bindings or logs.

**Composition, closure and cost.** A future trace worksheet, not a runtime
schema, names source/constant words, row/cell order, exact operand/result values,
zero tags, rounded output words, rational rounding evidence and stop reasons.
Operand rounding is propagated before each cell's own error. P3's stored-pi
and argument contribution enters P4/P5 composition once; no sinc cancellation
or exact-one-at-zero claim is unlocked. P7 retains circular real-pi comparison,
not bare wrapped subtraction. The existing same-stored-pose local errors and
seed-based recurrence remain requirements; held receipts do not reset error.
G1 still normalizes only the current goal, not the next motion heading, and G2/
G3 still compare against the same stored pose without adding ideal-pose error
again. Binary-step and nominal clocks are not merged.

Whole-row trace admission retains the private finite twist/heading/duration and
eight-event/seven-advance profile, without inventing a smaller scene envelope.
Kernel format correctness alone does not prove computed-domain closure for
these rows or any downstream primitive. Each divisor, exponent shift, integer
quotient/remainder, carry and materialized intermediate needs a derived work/
storage preflight. Repeated rounding bounds word-valued state, not every temporary
integer. Do not borrow the reference's 65,536-bit cap as a producer cost guarantee.
Missing cap/domain evidence yields unsupported, not a larger budget or clamp.

The listed four-row trace has ten unconditional RN64 calls and one additional
call on the negative nonzero remainder-correction branch. This is an analytic
operation count, not a benchmark; exact integer division and large temporaries
can be much more expensive than native arithmetic. No time, allocation/stack,
firmware fit, NPU or task-quality measurement is claimed. An eventual host-only
prototype and board implementation would have independent evidence/budgets.

**Proof and acceptance checks, proposed and unexecuted.** Prove exact word
decode/encode, integer arithmetic/quotient signs, nearest-lattice rounding,
ties-to-even, carry/normal/subnormal/overflow transitions and every zero-sign
rule. Bind the implementation/trusted base and independently derived finite
working-integer bounds. Literal bit fixtures and a separate rational/lattice
argument must supply expected results, not the new rounder or existing FP calls
as their own oracle. Shared integer infrastructure remains an explicit trust
assumption; samples do not prove a uniform producer-error bound.

Checks must cover signed zeros/cancellation, both tie parities, subnormal
underflow and normal transitions, division/multiply exponent extremes, invalid
words/denominators, quotient sign, remainder zero and period-rounding cuts,
source-order versus fused-row differences, constant/word binding, wrong row
dependencies and preflight/atomic stop behavior. An interval branch ambiguity
must abstain. Owner/source/wire and all ten old qualification flags/verdicts
must be unchanged; a passed isolated trace cannot qualify P4-P6/G1-G3 or become
a new label, dataset or physical-clearance claim.

**Exit and next permission.** This preparation exits with a concrete word/
rounding/remainder contract, four ordered traces, three route tradeoffs,
compatibility levels, cost uncertainties and proof/stop checks. Nothing is
implemented, run, adopted or bounded numerically by completing the document.
Recommended next bounded package, **not approved**: an isolated private
word/RN64/exact-operation and four-trace prototype with synthetic literal unit
tests only, reusing the existing diagnostic/test files. Candidate fixture caps are
64 distinct primitive vectors and 32 distinct row-trace cases,
no owner advances, question queries,
scene/episode/log use, old-record adapter, integrations or proof/allowance/flag
promotion. Test expectations need independent bit/rational derivations and
focused/default source gates; no external package or GPU is required by the
candidate. Gate invocations reuse those cases and report execution counts
separately, never as independent cohorts. These counts authorize no run here
and are not representative data
or a uniform certification plan. Separate prototype approval and later numerical
qualification/adoption remain necessary. All present approvals are exhausted.


#### Isolated Controlled Arithmetic Prototype (2026-11-03)

The user separately approved the isolated prototype proposed in §104, including
literal fixtures and focused/default gates ([review §105][controlled-arithmetic-review]).
The implementation in [the existing diagnostics module][c1-prototype-source]
does not adopt the candidate as the producer or qualify installed CPython.
Private word decoding and RN64 helpers use exact standard-library `Fraction`
and integers, with separate zero signs, ties-to-even neighbor selection,
subnormal/carry handling and unsupported overflow/division/work-limit stops.
No float, NumPy or libm operation is part of these helpers.

`_trace_synthetic_binary64_rows` requires literal `synthetic_test_only=True`,
declared binary64 format and exact supplied constant words:
duration `0x3fa999999999999a`, pi `0x400921fb54442d18`, two `0x4000000000000000`.
It retains the existing finite heading/twist profile, with no repeated-step,
owner, snapshot, source-record, episode or wire adapter. These literals are a
prototype contract, not an attestation of current stored bytes or clock facts.
It emits exactly P1/P2/P3/P7 with named operand/result/rounding-error cells and
ten unconditional rounded cells, plus the negative-residue correction cell.
P3 and P7 keep separate period cells. P7 truncates the exact quotient toward
zero, preserves dividend-zero sign before divisor-sign correction and keeps a
corrected residue equal to the period. Unsupported evidence or late arithmetic
failure returns no partial rows. All qualification/training flags remain false.

The independent integer preflight ceiling is 4,096 bits, not the mathematical
reference's 65,536-bit budget or a measured allocation/time limit. Decoded finite
word numerators and denominators need at most 1,024 and 1,075 bits. Conservative
cross-product counts give at most 2,100/2,150 bits for exact add/subtract operands,
2,048/2,150 for multiplication and 2,099/2,099 for division. Quantum scaling
adds at most 1,074 numerator or 971 denominator bits. A rounding-error difference
needs at most 3,175 numerator and 3,225 denominator bits by those same counts.
The profile's residue quotient truncates to zero or one; its arithmetic does not
add unbounded quotient growth. The rounder checks input/scaled lengths before
materializing shifts, and compares remainder with its complement rather than
doubling it. These are conservative structural arguments, not a completed
implementation proof, uniform numerical certificate, CPU cost or firmware fit.
Integer/Fraction/GCD/packing/control-flow semantics remain trusted-base evidence
obligations; arbitrary direct rational inputs may stop at the preflight boundary.

[Literal tests][controlled-arithmetic-prototype-tests] cover word/zero/rounding
and operation boundaries, the four ordered traces, rejection and atomic stops.
Expected words were derived without the prototype or native FP, using exact
rational binary search; durable tests check literal outputs and independent
neighbor-distance/tie inequalities. The period-rounding cut and a midpoint
fusion counterexample remain explicit. These fixtures do not attest old-producer
parity or establish all-domain correctness. Old diagnostic/test functions are
AST-identical; module source identities naturally change without regenerating
historical logs, reports or cache records. P4-P6/G1-G3, full motion/goal/source/
wire evidence, old flags/verdicts and helper `1bb89fe` stay unchanged.

The bounded prototype package is complete, not integrated/adopted/qualified.
Next recommended, not approved: a design-only correctness/work-bound dossier
for these four helpers and the same four rows, with exact lattice/zero/remainder
invariants, trusted-base and stop obligations. No new fixtures, numerical runs,
dependencies, owner/query/log adapter, allowance or qualification promotion.
All Task 6/9, physical/task-quality, teacher and ST/board gates remain separate.


#### Controlled Arithmetic Correctness Dossier (2026-11-03)

The user approved this design-only dossier for the four private helpers and
P1/P2/P3/P7 ([review §106][controlled-arithmetic-dossier-review]), not source
changes, new fixtures, numerical execution or qualification. The baseline is
`9b4000e`. This is a conditional mathematical/source worksheet: every claim
below requires its named trusted-base and implementation-correspondence
obligations. No row is declared proved, adopted or Q0-Q5-qualified by preparation.
The earlier 92 fixture checks remain historical evidence, not a new proof run.

The local hypothesis is that exact rational/lattice reasoning can separate
format correctness, rounded finite results, zero semantics, overflow and
work/stop claims without implying installed-producer parity or a runtime bound.
The cheap check is static correspondence to the four unchanged helper bodies
and the existing neighbor/zero/exception tests, not arithmetic evaluation.

| Obligation | Owning Helper | Conditional Invariant/Discriminating Check |
| --- | --- | --- |
| D0 | `_synthetic_binary64_value` | Exact built-in integer word, finite exponent field; decode the normal/subnormal mathematical value and retain the independent sign of zero. Fraction reduction preserves the value but cannot recover zero sign. |
| R1 | `_synthetic_rn64` | For positive magnitude and denominator, bit-length difference plus one exact comparison gives the floor binary exponent. Check the positive/negative shift branches separately, including a correction from zero to minus one. |
| R2 | `_synthetic_rn64` | With quantum `max(exponent-52,-1074)`, quotient/remainder give adjacent lattice candidates. Compare remainder with its complement; increment above half, or at half only for an odd coefficient. |
| R3 | `_synthetic_rn64` | A carry to `2**53` is renormalized once. Subnormal coefficients below `2**52`, the first normal coefficient and exponent-field packing preserve the selected value and sign. |
| R4 | `_synthetic_rn64` | Overflow uses the finite-format carry threshold, not nearest among finite words alone. Check early exponent rejection and the final all-one exponent rejection independently. |
| R5 | `_synthetic_rn64` / `_synthetic_binary64_operation` | Exact zero uses an explicit valid tag; nonzero underflow keeps its own sign. Addition, subtraction and multiplication/division have distinct tag rules, not a single rational-zero convention. |
| O0 | `_synthetic_binary64_operation` | The named exact operation precedes RN64; returned error is decoded rounded value minus that exact result. Operand rounding and upstream error are not hidden inside this local ratio. |
| T0 | `_trace_synthetic_binary64_rows` | P1/P2/P3/P7 keep source-ordered cells, two separate periods, exact quotient truncation, remainder sign correction and final subtraction. The worksheet is not an owner/pose/source/wire adapter. |
| W0 | all four helpers | Materialized expression lengths, integer/Fraction implementation work and live object bytes are distinct. A 4,096-bit check alone is neither a time bound nor protection against already-materialized oversized caller inputs. |
| S0 | `_trace_synthetic_binary64_rows` | Only the caught ValueError path returns an unsupported result with empty rows. Opt-in rejection raises; allocation/interruption/unexpected exceptions are not converted into safety-qualified abstention. |
| TB0 | all four helpers | Bind integer, Fraction/GCD, packing, comparison/shift, source/interpreter and exception semantics before promoting any conditional argument. No native CPython FP-path equivalence is inferred. |

For R1, let $N,D>0$ and $e_0=\operatorname{bitlen}(N)-\operatorname{bitlen}(D)$.
The source compares $N$ with $D2^{e_0}$ when $e_0\ge0$, or $N2^{-e_0}$ with
$D$ otherwise, and subtracts one exactly when the left side is smaller.
The required result is $2^e\le N/D<2^{e+1}$. These are rational comparisons,
not floating logarithms or runtime observations.

For R2, set $q=\max(e-52,-1074)$ and choose integers $A,B>0$ such that
$A/B=(N/D)2^{-q}$. Integer division gives $A=KB+R$, $0\le R<B$.
Comparing $R$ with $B-R$ is equivalent to comparing $2R$ with $B$, without
materializing the doubled remainder. Prove that the increment/odd rule chooses
the nearest lattice point, with ties to even, before invoking R3/R4 packing.

For R4, the maximum finite magnitude is $M=(2^{53}-1)2^{971}$ and its
overflow midpoint is $H=M+2^{970}=(2^{54}-1)2^{970}$. Magnitudes at or above
$H$ must stop unsupported; do not pretend a nearest-finite-only search defines
this decision. The conceptual next value $2^{1024}$ explains the carry/tie,
but is not a supported output word. Existing finite-neighbor tests exclude
that upper candidate, so they cannot discharge R4 on their own.

**Branch completion and zero tags.** R3 must partition magnitudes below half
the least subnormal, at that half, within the subnormal lattice, at the first
normal transition, within normal binades and at the overflow midpoint. The
early `exponent < -1075` branch is strictly below half; equality still reaches
quotient/tie selection. A selected zero retains the nonzero exact result's
sign. Before increment the normal coefficient is below `2**53`; the possible
single carry is renormalized before packing. A subnormal carry to `2**52`
must instead encode the minimum normal. No float conversion supplies this proof.

R5 requires the following source-specific tag ledger, including subtraction
of signed zeros. Two negative exact zeros add to negative zero; other exact
zero additions and nonzero cancellation give positive zero. Subtraction flips
the right value and sign before that same rule. Multiplication and supported
division use operand-sign XOR. Division by either signed zero is unsupported.
The operation worksheet's `zero_sign` is the exact-zero fallback tag, not a
replacement for the sign of a nonzero result. It is ignored by RN64 for nonzero
numerators. Neither a rational equality nor an adjacent-magnitude check proves
these tags, and the supplied tag's validity is not caller/source authority.

O0 separately requires exact operation semantics, reduction and positive
denominators. Its error ratio is local to the *already rounded* supplied words.
It is not the total seed-to-cell error, a runtime allowance or a claim that the
installed old producer has that error. Preserve the previous same-stored-pose
and seed-based accounting, both clocks and once-only stored-pi/argument error
composition; P4-P6/G1-G3 and `1bb89fe` remain outside the dossier's proof claim.

**Four-row dependency and remainder worksheet.** This is not a new trace schema
or API. T0 requires the following exact dependencies, not just named output rows.

| Row | Conditional Source-Order Obligation | Closure/Stop Obligation |
| --- | --- | --- |
| P1 | Round supplied turn times supplied binary-step duration to `a`. | Literal duration is positive and below `1/16`; it is not nominal `1/20` or newly attested stored bytes. |
| P2 | Divide rounded `a` by literal two, round `half`, then add supplied heading and round `m`. | An exact unfactored half-angle expression is a different producer; finite closure depends on R1-R5. |
| P3 | Separately round two times stored pi to `b_q`; divide rounded `a` by it and round `q`. | Prove the denominator is positive and exact doubling is representable; do not inherit P4/P5 or real-pi error qualification. |
| P7 | Round heading plus `a`, then plus stored pi; separately round its period, truncate the exact quotient, form and round the signed residue, correct sign and finally subtract pi. | Prove quotient/domain closure and each rounding point; zero/sign correction, `u==b_r` and circular-reference cuts cannot be replaced by floor division, clamping or a fused wrap. |

Let the stored pi value be $p$, duration be $d$, and reaction turn be $\omega$.
D0 and the literal words must establish $3<p<4$, $0<d<1/16$, literal two,
$|r|\le p$ and $|\omega|\le3/2$. Conditional on RN64 monotonicity and exact
representable endpoint preservation, $|a|\le3/32$ and the first rounded sum
lies in $[-5,5]$. The next rounded sum $x$ lies in $[-2,9]$; exact doubling
gives $b_r=b_q=2p>6$. Thus $-1<x/b_r<2$ and truncation toward zero yields
only zero or one. The two cells stay distinct despite that equality. These
deliberately loose rational intervals require no new scene or numerical sample.
They are a conditional closure argument to review, not qualified domain bounds.

For the residue, prove $\rho=x-tb_r$, $|\rho|<b_r$ and the dividend sign for
nonzero residue. Truncation must use magnitude division and then restore sign.
D0/RN64 exactness must cover residue representability or retain a nonzero local
residue-rounding error; do not assume representability from successful fixtures.
At zero, RN64 initially preserves the dividend sign, then correction uses the
divisor's zero sign. Negative nonzero residue adds the period and rounds; this
can produce `u==b_r`. Positive residue is unchanged. The final subtraction has
its own rounding/zero rule. Prove these cases before claiming staged remainder
semantics, never installed fmod equivalence or a half-open real-pi result.

**Expression-size ledger, not a resource certificate.** Let bit length refer
to integer magnitude, with zero length zero and a positive denominator. The
following are conservative unreduced arithmetic counts conditional on exact
integer/Fraction semantics; they bound values, not internal allocator objects.

| Stage | Numerator/Comparison Bits | Denominator Bits | Derivation/Remaining Obligation |
| --- | --- | --- | --- |
| D0 finite-word decode | 1,024 | 1,075 | At most 53 significand bits and a 971-bit positive shift, or denominator `2**1074`; reduction cannot enlarge values. |
| O0 add/subtract | 2,100 | 2,150 | Two cross-products of at most 2,099 bits plus one sum carry; denominator product. |
| O0 multiply | 2,048 | 2,150 | Products of two decoded numerators/denominators; internal GCD work remains a trusted-base question. |
| O0 divide | 2,099 | 2,099 | Cross numerator/denominator products with a nonzero right operand; normalize sign. |
| R1 exponent comparison | at most 4,096 on either side | not a new ratio | After input preflight, the shifted side's bit length equals the larger original bit length. This shift precedes the later quantum preflight. |
| R2 quantum scaling of a word operation | at most 3,174 | at most 3,121 | Add at most 1,074 numerator or 971 denominator bits; direct rational calls instead obey their own 4,096-bit scaled preflight. |
| R2 quotient/remainder/tie | coefficient at most 54 before carry normalization | scaled divisor at most 4,096 | Remainder and complement fit the divisor; one increment and one carry, not an unbounded coefficient loop. |
| O0/T0 local rounding error | at most 3,175 | at most 3,225 | Difference between decoded rounded word and exact operation/residue; cross-products plus one sum carry. |
| T0 quotient/residue | quotient-ratio 2,099; residue numerator 2,100 | quotient-ratio 2,099; residue denominator 2,150 | Conditional trace closure bounds truncated quotient to zero/one before multiplication by the period. |

The decode/operation paths have structural bounds before they call the rounder;
they do not dynamically preflight each Fraction internal allocation. R1's
comparison shift is justified by its own matching-bit-length argument, not
retroactively by R2's later guard. RN64 checks rational lengths before `abs`
and quantum-scaled lengths before their shifts. Arbitrary oversized integers
may already exist at ingress: these checks do not bound their construction,
caller storage or parsing. Prove reduction, GCD/division and intermediate
materialization separately rather than equating a guarded returned pair with
every implementation temporary.

The trace has ten or eleven rounded worksheets and bounded source-level
control flow, but those counts are not time, Python allocation or stack bounds.
Live fractions, operand/error tuples, cell dictionaries, retained lists/rows,
temporary division/GCD objects, interpreter frames and object overhead require
a separate materialization/work model. A 4,096-bit integer ceiling and the
reference's 65,536-bit ceiling neither measure nor certify that model. No new
deadline, memory budget, Cortex-M55 fit or hardware implementation is adopted.

**Trusted base and stop model.** TB0 must distinguish mathematical assumptions
from their actual implementation/correspondence evidence. Bind the four source
bodies, mutable cap/global/helper bindings and immutable literal contract;
then the selected interpreter's integer shifts/comparisons/division, Fraction
normalization/arithmetic/GCD, tuple/dictionary construction and exception
behavior. The local Git identities in REVIEW.md §106 bind text only, not
installed interpreter instructions, live bindings or authenticated build lineage.
No fresh interpreter/native-library identity or stdlib source audit occurred.

S0 proves only externally published result atomicity on the existing ValueError
path: its returned rows are empty and no owner/event/log mutation path exists.
Partly built local cells may have existed before the catch; this is not rollback
of allocations or every exception. `MemoryError`, interruption and unexpected
exceptions propagate; they are not converted into a safety-qualified unknown.
The strict opt-in guard raises before the result is created. Binding mutation,
side-effecting replacement helpers or a different caller are outside the assumed
proof domain, not silently protected by these checks. No host fallback or
physical failure policy is changed.

**Candidate acceptance sequence, not executed or adopted.**

1. Freeze the exact helper text, word/constant/domain contract, source-cell
  dependency graph, zero tags, overflow midpoint and exception set. Any mismatch
  invalidates the worksheet instead of reusing a historical test result.
2. Review D0/R1-R5/O0/T0 by branch, including RN monotonicity, representable
  endpoints, carry, exact-zero versus underflow and P7 truncation/correction.
  An unclosed lemma remains an explicit obligation, not a fixture-derived proof.
3. Review W0/TB0 at each materialization boundary. Choose explicit trust
  assumptions or bind already-local implementation evidence; missing source,
  compiler/live correspondence, internal work or byte costs stay unresolved.
4. Map the existing literal/neighbor/fault fixtures to those obligations without
  running or enlarging them. Neighbor samples do not prove overflow, zero tags,
  all-domain correctness, rare exceptions or internal work. Any future execution
  needs a separate bounded approval; old 64/32 permission is exhausted.
5. Record independent paper review outcomes per obligation, assumptions and
  unresolved dependencies. Even a later accepted conditional theorem does not
  promote Q0-Q5, primitive allowances, old producer parity, owner integration,
  full motion/goal/wire qualification, physical clearance or task-data approval.

Recommended default: retain the isolated prototype and unchanged unqualified/
abstaining producer paths. This preparation is complete, not proof acceptance.
Next recommended, **not approved**: bounded read-only trusted-base/source
correspondence review for these same helpers, at most three already-local
implementation files and 64 KiB cumulative extracted text, including failed/
diagnostic reads. Missing integer/GCD implementation or interpreter/build
correspondence remains a gap. No acquisition/download, runtime import,
disassembly, new fixture/numerical run, source edit, dependency, proof/allowance/
flag promotion or owner/query/log adapter; no general interpreter audit. All
Task 6/9, numerical/physical/task-quality, teacher assets and ST/board gates stay.


#### Local Arithmetic Trusted-Base Review (2026-11-03)

The user separately approved the bounded read-only follow-up to §106
([review §107][arithmetic-trusted-base-review]). It inspects already-local
Fraction source and two integer headers, not runtime imports, a numerical run
or a general interpreter audit. It changes neither the four private helpers
nor the eleven conditional obligations, old flags/verdicts or `1bb89fe`.
The following is static source correspondence, not accepted correctness,
compiled/live-path binding, resource evidence or Q0-Q5 qualification.

| Surface | Visible Correspondence | Remaining Trust/Stop Obligation |
| --- | --- | --- |
| F0: exact-int constructor | `Fraction.__new__` accepts two exact integer arguments, rejects zero denominator, uses `math.gcd`, normalizes denominator sign and divides the pair by the GCD. | Object allocation occurs first; integer/GCD semantics and exceptions remain trusted. No signed-zero tag survives rational zero alone. |
| F1: internal pair constructor | `_from_coprime_ints` allocates and stores the supplied numerator/denominator without another GCD or sign check. | Its documented reduced-positive-denominator invariant must come from the callers; the constructor does not enforce it. |
| F2: operator selection | Generated forward operators use rational algorithms for Fraction operands and convert integer operands through Fraction. Reverse operators admit Rational operands. Float/complex fallback branches also exist. | Their exclusion is conditional on the helpers' exact types and stable bindings, not a whole-module FP-free claim or observed dispatch. |
| F3: arithmetic | `_add`/`_sub` reduce denominator factors; `_mul`/`_div` cross-cancel using GCD before products. Division rejects zero numerator in its divisor and restores denominator sign. | Check zero/cancellation, positive denominators and coprimality before trusting F1. Integer division/GCD bodies and internal work remain unbound. |
| F4: predicates/unary/properties | Rational comparisons use cross-products; boolean conversion uses the numerator; unary negative/absolute return internal pairs; numerator/denominator properties expose stored integers. | Canonical integer pairs and type bindings are prerequisites. Float comparison, formatting/hash/conversion and arbitrary subclasses are not qualified. |
| I0: integer boundary | Local headers declare GCD, shifts and bit-count-related interfaces and show selectable 15/30-bit digits with an `lv_tag` structure. | Declarations/comments are not the integer/GCD implementations, selected configuration, compiled ABI, live dispatch or memory/time bounds. |

`math.gcd` is an integer dependency, not evidence that these paths call native
floating arithmetic. Conversely, the presence of an integer-only branch does
not authenticate its loaded module, compiled callee or ambient replacement
bindings. Selected-editor interpreter and local file/hash/package metadata
are distinct from runtime module origin and bytecode/build correspondence.
No checked header may be substituted for a linked integer implementation.

**Helper-to-source correspondence.** Under unchanged exact type/class/global
bindings, `_synthetic_binary64_value` constructs Fraction from two integers;
its positive denominator goes through F0. RN64 itself uses builtin integer
bit lengths, shifts, division/remainder and comparisons. It does not call
Fraction's `__round__`, fraction `divmod`, decimal formatting or the header's
`_PyLong_DivmodNear`. Similar names/tie comments do not bind those native APIs
to the executed integer operators.

The named operation `sub` first negates the right Fraction and then performs
addition; its exact path is F4 unary negation plus F3 `_add`, not automatically
Fraction `_sub`. Actual `_sub` remains relevant to rounded-minus-exact error
ratios and the trace's residue subtraction. Multiplication/division use F3
`_mul`/`_div`; the trace's integer-times-period uses the Rational reverse
operator and the exact single-int Fraction constructor. Its quotient truncation
is explicit integer magnitude division, not Fraction `__trunc__` or floor wrap.

F0 performs one GCD after allocating its object; the exact single-int constructor
stores denominator one directly. F3 add/subtract have one GCD and a conditional
second GCD; multiply/supported divide have two. Unary/pair construction does
not revalidate with another GCD. Per-cell error subtraction and predicates are
additional work beyond ten/eleven RN64 calls. Source-level call counts do not
bound GCD/division iterations, intermediate allocations, runtime or stack.

For normalized inputs, denominator-GCD reduction, cross-cancellation and
sign restoration are compatible with the dossier's unreduced product counts.
That is a conditional source correspondence, not a proved implementation
bound. Comparisons materialize cross-products too. Check those, error subtraction
and internal pair construction separately; a bound on a returned reduced pair
is not a bound on every native temporary. F1's reduced-positive-denominator
precondition must survive zero/cancellation and all callers. Slots/comments
alone do not enforce canonicality or prevent mutation of stored attributes.

The header evidence remains a declaration/representation boundary. GCD's
declaration mentions use by `mathmodule.c`, but neither that wrapper nor
integer/GCD/shift/division body was inspected. Selectable 15/30-bit digits are
not a measured configured digit size. The representation prose still uses
`ob_size` terminology beside the actual `lv_tag` structure; do not derive a
live ABI, sign layout or memory recipe from that prose. No linked/compiled
configuration or full object-materialization/allocator model is established.

Fraction constructor/division zero checks raise `ZeroDivisionError`, not the
trace's caught `ValueError`. The helper's right-zero guard and literal positive
period exclude those cases only under the stated invariants. Object allocation,
integer operations and unexpected/replaced bindings may still fail outside
that catch. S0's published-result atomicity and the unchanged host failure
policy are not enlarged by this review.

**Remaining evidence and next permission.** The bounded review is complete;
text identities and package ownership are not authenticated build provenance,
observed module origin, loaded bytecode, closure selection or native correspondence.
No imported module or instruction path was inspected, and neither the eleven
obligations nor Q0-Q5 is promoted. W0/TB0 and all native/internal-work claims stay
open. The already-local text was inspected without acquisition or execution;
unused file/text allowance is not permission for a further audit.

Next recommended, **not approved**: a paper-only conditional partial-correctness
review of the eight named D0/R1-R5/O0/T0 obligations, using the recorded helper/
Fraction correspondence and explicit exact-integer/GCD/canonical-input/stable-
binding assumptions. Check rounding/zero/overflow and the P7 zero/one quotient
and residue-representability cases. Record each conditional lemma, gap or
counterargument without accepting implementation qualification or native trust.
No extra implementation-text extraction, runtime import, acquisition, source
edit, fixture/numerical run, dependency, allowance/flag promotion or integration.
This is not renewed permission for three files/64 KiB, a runtime work proof,
owner/query/log adapter, physical/task-quality or Task 6/9 completion. Default
remains unchanged/unqualified/abstaining; teacher and ST/board gates stay separate.


#### Conditional Arithmetic Paper Review (2026-11-03)

Following §107, the user approved continuing the proposed eight-obligation
paper-only partial-correctness review ([review §108][arithmetic-paper-review]).
This records conditional derivations, not accepted proof or implementation
qualification. It uses the recorded four-helper contract and Fraction source
correspondence; no additional implementation text, runtime import, arithmetic
execution or fixture is needed. Earlier dossier/source reviews remain historical.

**Assumptions and success boundary.** Assume exact builtin integer comparison,
bit lengths, shifts, division/remainder and nonnegative mathematical GCD;
canonical Fraction pairs with positive denominators; unchanged exact types,
literal words, helper/global bindings and rounding/control-flow correspondence.
Assume allocation and selected operations complete normally. Do not authenticate
any native/build/live implementation by assuming these mathematical semantics.
The conclusion concerns a returned supported result, not guaranteed return for
every mathematical input. Input and scaled-bit guards may stop otherwise finite
values; no new domain/admission rule or completeness claim follows.

The Fraction normalization prerequisite can be separated from that native trust.
For reduced pairs $n_1/d_1,n_2/d_2$, let $g=\gcd(d_1,d_2)$, $s=d_1/g$,
$v=d_2/g$. Addition/subtraction forms $t=n_1v\mathbin{\pm}n_2s$ over
$sgv$. Since $\gcd(s,v)=1$ and the input pairs are reduced,
$\gcd(t,s)=\gcd(t,v)=1$; only $\gcd(t,g)$ can remain to cancel.
This justifies the recorded conditional second-GCD reduction, including zero:
if $t=0$, those equalities force $s=v=1$, and cancellation leaves denominator
one. Cross-cancellation in multiplication removes $\gcd(n_1,d_2)$ and
$\gcd(n_2,d_1)$ before products. Division by nonzero $n_2$ instead removes
$\gcd(n_1,n_2)$ and $\gcd(d_1,d_2)$, then restores denominator sign.
The remaining numerator/denominator cross-pairs are coprime. Unary negation/
absolute value preserve canonicality. These are value/invariant arguments under
the assumptions, not proofs of integer/GCD code, mutation resistance or work.

| Obligation | Conditional Paper Outcome | Still Outside the Conclusion |
| --- | --- | --- |
| D0 | Finite fields decode the exact dyadic value; rational zero has an independent word-sign tag. | Word/source authority and native shifts/constructor binding. |
| R1 | Bit lengths plus the recorded exact comparison select the floor exponent in both shift branches. | Native bit-length/shift/division correctness and progress. |
| R2 | Quotient/remainder and the complement/odd rule select nearest-even on the relevant lattice. | Guard completeness, instruction/FP-path equivalence and execution evidence. |
| R3 | Zero, subnormal/minimum-normal transition and single normal carry pack the selected value. | Actual builtin packing/code correspondence and allocation behavior. |
| R4 | Early high exponent and final exponent carry reject the overflow midpoint and larger magnitudes. | Accepting overflow semantics or qualifying finite-neighbor tests as proof. |
| R5 | Exact-zero fallback tags, nonzero-underflow signs and per-operation zero rules remain distinct. | Caller/source authority, every-exception abstention or host fallback policy. |
| O0 | Canonical rational operations precede rounding; decoded-rounded minus exact is a local error. | Old-producer parity, propagated allowance, native/work qualification. |
| T0 | Ordered cells have conditional finite closure; quotient zero/one makes the raw residue representable. | Adoption, full-motion/goal/wire evidence, integration or qualification flags. |

**D0 and exponent selection.** Write the sign as $S$, the exponent field as
$E$, and the 52-bit fraction field as $F$. For finite fields the decoded value is

$$
V(S,E,F)=(-1)^S
\begin{cases}
F2^{-1074}, & E=0,\\
(2^{52}+F)2^{E-1075}, & 1\le E\le2046.
\end{cases}
$$

Positive power-of-two denominators and exact shifts realize that value; GCD
reduction preserves it. The $E=F=0$ pair represents zero but loses its sign,
so $S$ must remain separate. All-one exponent fields remain unsupported.

For R1 let $N,D>0$, $l_N=\operatorname{bitlen}(N)$,
$l_D=\operatorname{bitlen}(D)$ and $e_0=l_N-l_D$. The defining bit intervals give
$2^{e_0-1}<N/D<2^{e_0+1}$. The recorded shift comparison tests exactly
$N/D<2^{e_0}$ without a floating logarithm, even when $e_0<0$.
If true, choose $e=e_0-1$; otherwise choose $e=e_0$. Both choices satisfy
$2^e\le N/D<2^{e+1}$. In particular $e_0=0$ can legitimately correct to
$e=-1$; it is not a special unhandled negative-shift case.

**R2/R3: nearest-even and packing.** Put $q=\max(e-52,-1074)$ and scale the
magnitude to $A/B=(N/D)2^{-q}$. Exact division gives $A=KB+R$ with
$0\le R<B$. The distances to coefficients $K,K+1$ are $R/B$ and
$(B-R)/B$. Increment exactly when $R>B-R$, or at equality for odd $K$.
This selects the even coefficient at a tie without doubling the remainder.
On a normal binade, coefficients run from $2^{52}$ to below $2^{53}$;
below the first normal, the lattice is the fixed $2^{-1074}$ subnormal grid.
Below a binade's lower endpoint a smaller-grid candidate cannot be closer to
a magnitude already at or above that endpoint than the endpoint itself.

For $e<-1075$ the magnitude is strictly below half the least subnormal and
rounds to zero. At $e=-1075$ the tie still reaches quotient selection; coefficient
zero is even. In subnormal scaling a carry to $2^{52}$ encodes the first normal.
In normal scaling at most one increment can reach $2^{53}$; replace that
coefficient by $2^{52}$ and increment $q$ once, preserving the selected value.
Otherwise the fraction field is the coefficient minus $2^{52}$ and the exponent
field is $q+1075$; subnormal coefficients instead retain exponent field zero.
A zero coefficient retains the separately selected sign.

The same ordered lattice/midpoint partition gives nondecreasing decoded RN64
values, conditional on successful guarded results. Every representable finite
endpoint is preserved because its coefficient has zero remainder. These two
lemmas justify interval endpoint reasoning below; they do not remove guard
rejections or make a claim about native floating-point modes.

**R4/R5: overflow and sign cases.** At the top binade the maximum finite value
is $M=(2^{53}-1)2^{971}$ and the midpoint to conceptual $2^{1024}$ is
$H=(2^{54}-1)2^{970}$. Below $H$ the rounded coefficient stays finite; at $H$
the odd maximum coefficient ties to the even carry. That carry makes exponent
field 2047 and stops unsupported. Larger magnitudes in this binade do likewise;
$e>1023$ already implies magnitude at least $2^{1024}$ and the early stop.
Reflecting magnitude preserves these conclusions for negative inputs. This is
not nearest among finite words alone, and does not rely on a sampled neighbor.

An exact-zero rational uses its valid supplied fallback tag. A nonzero rational
rounded to zero instead uses its own sign, not that fallback. Addition gives
negative exact zero only for two negative zero operands; opposite zeros and
nonzero cancellation give positive zero. Subtraction flips the right sign/value
before that rule, so negative zero minus positive zero remains negative zero,
while negative zero minus negative zero becomes positive zero. Multiplication
and supported division use sign XOR. Either signed-zero divisor is unsupported.
These rules concern the mathematical successful path; S0 is not strengthened.

**O0 and ordered finite closure.** Conditional canonical-pair arithmetic makes
the exact operation correct before RN64. The emitted error ratio is therefore
$V(w_{\mathrm{rounded}})-v_{\mathrm{exact}}$ for the supplied already-rounded
words, never a seed-to-cell or old-producer allowance. Named subtraction is
negation then addition; its error/residue subtraction uses the separately
recorded rational subtraction path. Neither is fused with another cell.

D0's literal-field inequalities give $3<p<4$, $0<d<1/16$ and exact two.
Under the declared $|r|\le p$, $|\omega|\le3/2$ profile, monotonicity and
representable endpoints give $|a|\le3/32$, $|\mathrm{half}|\le3/64$ and
$m\in[-5,5]$. Halving need not be exact for tiny subnormal $a$.
Doubling $p$ is exact and representable: both separately computed periods
$b_q,b_r$ equal $b=2p\in(6,8)$ without merging their cells.
P3 has $|q|\le1/64$. P7's first sum lies in $[-5,5]$ and its next rounded
sum $x$ in $[-2,9]$. Thus $-1<x/b<2$, so magnitude division with sign
restoration truncates to $t=0$ or $t=1$. These are paper intervals for supported
traces, not changed runtime bounds, input admission or full-motion certification.

**T0: raw residue representability and correction.** For $t=0$, the exact
residue $\rho=x$ is already a finite word value. For $t=1$, $b\le x\le9$.
Since $p$ is in binade $[2,4)$, $b$ is an integer multiple of $2^{-50}$.
Here $x$ is in binade $[4,8)$ or $[8,16)$, so it too is a multiple of
$2^{-50}$ (the latter binade has twice that spacing). Hence

$$
\rho=x-b=k2^{-50},\qquad 0\le\rho<3,\qquad 0\le k<3\,2^{50}<2^{53}.
$$

Every nonzero such coefficient has at most 53 significant bits and an exponent
far above underflow; leading-zero normalization gives an exact finite binary64
word. Thus raw-residue RN64 preserves its mathematical value in both quotient
cases, and its local error ratio is conditionally zero. This closes the recorded
representability lemma on this profile only; it does not promote an error bound,
flag, native remainder claim or acceptance of the eight obligations.

At exact zero, raw rounding retains the dividend tag, then correction selects
the positive divisor's zero tag. A negative nonzero residue occurs only when
$t=0$ and $x<0$; adding $b$ and rounding is still a distinct operation. Its
exact sum can lie sufficiently close to $b$ to round to $u=b$, including the
even-coefficient midpoint case. Positive residue is unchanged. Consequently
$0\le u\le b$, not a guaranteed half-open interval. The final separate
subtraction/rounding gives $r_{\mathrm{next}}\in[-p,p]$, permitting $+p$;
do not clamp, use floor-wrap, or substitute real pi. P1/P2/P3/P7 retain ten
unconditional rounding cells and the one conditional negative-residue correction.

**Outcome and next permission.** Eight conditional derivations are recorded;
none is accepted implementation proof. The canonical-pair, monotonicity and
profile-specific residue lemmas depend on the explicit assumptions. W0/TB0,
allocation/progress, every-exception semantics, old producer parity and Q0-Q5
remain open. Both binary/nominal clocks, stored-pi/argument error counted once,
seed-based accounting, P4-P6/G1-G3, `1bb89fe` and all old flags/bounds/verdicts stay.

Next recommended, **not approved**: bounded synthetic tests-only comparison of
the same four ordered scalar expressions against the controlled trace, using
at most twelve reused literal trace cases. Report exact word/sign/correction
agreement or discrepancy; do not loosen assertions or infer all-domain parity.
Reuse the existing test file/helpers and run focused/default source-test gates
only under that separate approval. No production source change, owner advance,
question query, scene/log adapter, new episode/data, integration, dependency/
acquisition, native/work/allowance/flag promotion or physical/ST/board claim.
Default remains unchanged, unqualified and abstaining where evidence is missing.


#### Bounded Scalar/Trace Compatibility (2026-11-03)

The user separately approved §108's tests-only comparison on at most twelve
reused literal trace cases ([review §109][arithmetic-compatibility-review]).
Native scalar expressions retain the current integrator's multiplication,
integer-two division/period expressions and ordered modulo wrap. Binary64
struct round-trips bind the supplied words to builtin floats and the stored
duration/pi/two literals. Direct `math.fmod` supplies a raw-residue comparison;
Python `%` supplies the corrected value. Neither requires running the integrator,
motion owner, sinc/trigonometric body, question coordinator or a log adapter.

All eleven intermediate words per case agree exactly with both the previously
recorded literals and the controlled trace. Signed-zero/correction tags agree,
and the raw-residue error ratios are zero on these cases. The period-reaching
negative correction and positive/negative-pi endpoints remain represented;
there is no clamping or half-open wrap assertion. This is bounded compatibility
evidence for the selected interpreter and reused inputs, not independent data,
all-domain parity, accepted proof, instruction/FP-state binding or native/work
qualification. Source, defaults, old flags/bounds/verdicts and `1bb89fe` stay.

**Next proposed scope, not approved:** prepare a design-only opt-in private
synthetic-owner arithmetic contract. Candidate word ingress would bind stored
heading/twist and the literal constants, mapping P1/P2/P3/P7 to angle/midpoint/
sinc argument/next heading while preserving the remaining operations and both
clocks. A separately identified candidate lane must never inherit old ownership,
wire, motion or qualification verdicts merely from these twelve comparisons.
Specify candidate provenance, unsupported/exception/atomic-advance rules and
work/acceptance gates before any implementation; no silent native fallback or
per-input outcome-driven producer selection. Leaving the helper isolated is
the retained alternative/default. No owner/source/wire edit, fixture/episode
run, runtime import, integration, allowance/flag promotion or Task 6/9 claim is
authorized by that proposed preparation. All numerical/physical/task-quality,
teacher-asset and ST/board gates remain separate.


#### Proposed Controlled-Arithmetic Owner Contract (2026-11-03)

The user approved this design-only preparation following §109
([review §110][controlled-owner-contract-review]), not implementation, owner
execution or adoption. Proposed default: leave the normal integrator and
`_SyntheticC1MotionOwner` unchanged and keep the controlled helper isolated.
An experimental candidate would be a separately identified private lane,
fixed at construction, never a per-input fallback or a new runtime profile.

| Contract Boundary | Proposed Candidate Requirement | Unchanged Limit / Stop |
| --- | --- | --- |
| C0: ingress | Bind exact stored heading/twist words, literal duration/pi/two and finite position/speed to one copied fixture seed/epoch. | No current-goal atan2 heading substitution, silent coercion, caller-supplied next pose or input/log adapter. |
| C1: arithmetic | P1/P2/P3/P7 feed angle, midpoint, sinc argument and next stored heading in source order; remaining native operations stay identified. | Do not merge periods, fuse cells, clamp period-reaching correction or infer full-motion error qualification. |
| C2: event binding | Bind each candidate trace's inputs/output words to the previous event, interval-ending twist, next pose/State/frame and both clocks. | Candidate ownership, source/wire and motion evidence are distinct, not inherited old verdicts. |
| C3: publication | Prepare arithmetic, capture/delivery/history, State/frame and a complete next owner ledger without mutating the retained candidate root; publish only after validation. | Existing `_record` updates the recorder before appending its event: calling it does not establish a transaction or all-exception rollback. |
| C4: audit | Retain a fresh candidate identity/anchor; reject foreign/stale/re-signed/mixed-lane records and keep all qualification flags false. | Do not feed a renamed candidate to the old strict motion/checker schema or reuse a legacy seal. |
| C5: work/failure | Keep eight-event/nonwrapping bounds and explicit unsupported/exception/work acceptance gates. | W0/TB0, allocations/native paths, time/live memory and physical/task quality remain open; no silent native fallback. |

The local hypothesis is that trace correctness alone cannot authenticate the
old owner's event/capture publication boundary. The nearby source shows
`advance` computing a pose, `_record` producing the host frame, then recorder
mutation followed by owner-list append and seal invalidation. A future candidate
needs an explicit preparation/publication design rather than assuming that
sequence is atomic. This is a static contract requirement, not a newly tested
failure or a requested repair of the old owner.

**Candidate identity and ingress, proposed only.** Use an additive private
candidate rather than a switch inside the old owner or integrator. Suggested
lane/model labels are `experimental_controlled_binary64_owner_v1` and
`constant_twist_controlled_binary64_candidate_v1`; neither is a wire/catalogue
version or adopted runtime profile. Require literal `synthetic_test_only=True`
and fix the lane for its lifetime. Copy the Scenario/seed; retain one planar
speed/turn and a fresh candidate epoch, source identities and private seal.
Callers request only the next tick after construction, never a next pose, goal,
trace, timestamp, source/capture record or producer selection.

The seed/previous heading and fixed turn must have exact finite binary64 words,
nonboolean builtin integer word storage and the helpers' unchanged bounds.
Round-trip conversion into the remaining native scalar/array path must preserve
those words, including signed zero. Native finite position/speed use an explicit
binary64 scalar/array contract and existing fixture limits, not wire-decoded
binary32 substitutes. Reject unsupported types/widths/constants/domain evidence
instead of silently coercing or truncating it. Bind `duration_word`, `pi_word`,
`two_word` to `0x3FA999999999999A`, `0x400921FB54442D18`,
`0x4000000000000000`. The stored event heading, not `_record`'s goal-frame
atan2 normalization, is the next step's input. These checks establish declared
word correspondence only, not actual source authority or TB0.

| Trace Result | Proposed Position/Motion Consumer | Residual Unqualified Path |
| --- | --- | --- |
| P1 `a` | Interval angle; bind to fixed turn and binary-step duration. | Do not recompute a native angle for a competing position path. |
| P2 `m` | `math.cos(m)` and `math.sin(m)` for the position increment. | Both libm calls, argument/domain error and native vector arithmetic remain unqualified. |
| P3 `q` | `np.sinc(q)` in the existing ordered speed-times-duration-times-sinc expression. | sinc's internal pi/sin/division and remaining multiplications are not replaced or certified. |
| P7 `r_next` | Next stored event heading, with its exact word and correction trace. | Current-goal atan2/sin/cos/subtraction, State encoding and float32 round-trip remain separate. |

Retain source-ordered native distance/vector operations, world-coordinate
position and source-scale guards. Do not call the old integrator for position
and then overwrite only yaw: that would leave native midpoint/argument
production active. No recentering, dtype/promotion assumption, error allowance,
floor/cylinder/sensor change or new physical range is adopted. P4-P6/G1-G3 and
all complete-motion/goal bounds stay unresolved; mixed controlled/native is
the candidate's declared arithmetic kind, not a fully controlled integrator.

**Proposed private records and clock binding.** The candidate outer bundle
must have a new allowed-use/schema/model identity, not an extended legacy
motion dictionary that an old reader might accept after fields are removed.
Its retained seal covers lane/epoch, source/calibration identities, seed/twist,
constant words, events and their private prepared capture/State/frame evidence.
Source identities must cover candidate/helper, remaining native computation,
capture and encoding source paths; text hashes are not authenticated native
build/live binding. Any future source-file change needs fresh owner identities,
not historical log/report regeneration or seal reuse.

Each interval-ending event binds previous pose/heading words, fixed twist,
next tick, full ordered trace and next stored pose/heading word. Bind its goal
State and actual encoded host-frame bytes too. Keep declared source ownership,
arithmetic support, source/wire correspondence and mathematical motion evidence
as separate fields. All training, real-input, free-space, numerical-certification
and producer-parity qualification flags remain false. A candidate record or
successful word trace cannot inherit `consistent_under_fixture_assumptions`,
legacy motion-consistency or source/wire status from an unrelated old seal.

The seed event is explicitly seed-only, with no fabricated preceding interval
or advance trace. Count it within the eight-event limit. Require consecutive
nonwrapping ticks, existing `tick*50000` frame time and seed tick at most 85899.
Keep the two mathematical elapsed clocks separate: $(k-k_0)d$ for exact stored
binary $d$ and $(k-k_0)/20$ nominal seconds. Do not reset accumulated reference
error on snapshot, capture receipt or frame encoding. The unchanged capture
cadence, two-tick delivery/held history and acquisition-to-event pose binding
remain source evidence, not a new sampling policy or physical sensor claim.

**Preparation/publication state machine.** A proposed advance has four stages:

1. Check tick/event capacity, source/lane identity, previous-word binding and
  fixed constants/profile without changing the retained root or seal.
2. Prepare a supported word trace, native next position, next stored heading,
  finite/domain checks and complete State/frame in private temporary state.
3. Prepare capture/delivery/history and a complete next event ledger against a
  copied/staged recorder state using the same candidate epoch. The active owner,
  recorder and seal must not be used as scratch state. The existing mutating
  `_record`/`record_tick` pair cannot simply be called on the active candidate.
4. Validate all cross-bindings, then publish one completed retained root under
  serialized access and invalidate the previous seal on successful advance.
  A later snapshot creates a fresh seal for that completed root only.

Prepublication unsupported/ValueError rejection must leave event count, pose,
capture queue/history and existing seal unchanged; it is not a fallback to
native arithmetic. Unexpected/allocation/interruption failures propagate, not
universal safety-qualified abstention. If publication may have begun, the
caller must discard that owner/epoch rather than trust an old seal or retry an
ambiguous advance. This is a conditional staged-publication contract, not a
proved single-assignment/VM atomicity or memory-rollback guarantee. Side-effecting
replacement helpers/capture factories, mutable private state and concurrent
calls are outside the assumed domain. Native staging must never gain authority
merely because an earlier trace succeeded.

**Audit and acceptance gates, not executed.** Candidate audits require their
own strict outer schema/retained anchor and field/source/event/frame bindings.
Reject stale, foreign, re-signed, truncated and mixed-lane records. The old
checker has an exact key/model contract; do not strip tags or rename candidate
data to make it pass. `1bb89fe` remains a mathematical reference, not candidate
ownership or full-motion proof. No reference/query/coordinator adapter is adopted.

| Gate | Future Discriminating Check | Failure / Evidence Limit |
| --- | --- | --- |
| A0 | Verify legacy/default APIs and ASTs, wire/catalogue/scenes, old guards/flags/verdicts and historical artifacts remain unchanged. | Source-keyed identities may naturally change after future additive code; do not regenerate historical evidence. |
| A1 | Exact-word/scalar/constants/previous-event binding, including signed zero and rejected ingress. | A coercion or goal-normalized heading mismatch rejects before publication. |
| A2 | Each position/heading step consumes the bound P1/P2/P3/P7 outputs once, preserving the residual native order. | Partial yaw-only substitution, period fusion or native fallback fails the contract. |
| A3 | Compare declared reused fixtures against ordinary scalar steps and independent literal trace cells, retaining pi endpoints. | Sample agreement is not all-domain parity or full-motion error evidence; diagnose discrepancies. |
| A4 | Inject preparation failures and verify pose, event/capture/history and seal preservation; distinguish ambiguous publication. | Do not weaken S0, catch every exception as unsupported or promise rollback without evidence. |
| A5 | Seed plus consecutive intervals stays within eight events/nonwrapping clock limits; captures bind acquisition/delivery poses. | Missing interval, copied current pose or merged nominal/binary time rejects. |
| A6 | Candidate audit rejects foreign/stale/re-signed/mixed-lane event/State/frame records; old readers reject candidate bundles. | No borrowed ownership/source/wire/motion verdict or automatic reference adaptation. |
| A7 | Count constructor attempts/events/captures/trace/audit calls including failed attempts; run focused/default source gates. | Counts/4,096-bit preflight are not time/live memory/allocator or hardware-fit bounds. |

W0/TB0, object materialization/native GCD/division/FP/build correspondence and
source/return/physical/task-quality qualification remain open. A fixture-only
prototype may expose those gaps but cannot adopt a deadline, live-allocation
allowance or safety policy. No teacher assets, ST tools or board action follows.

**Alternatives and next permission.** Retain isolation now. An additive candidate
with staged-root publication is the recommended experimental route if separately
approved: it exposes four-cell substitution without changing the old owner.
Changing the legacy owner/integrator, sharing a new rollback mechanism across
them, or selecting producers per input has a wider compatibility/provenance
blast radius and is not recommended or approved here.

Next proposed, **not approved**: implement that private candidate and bounded
synthetic tests only, at most eight declared motion-fixture cases using four
already-used complete scenes, at most sixteen owner constructor attempts
(candidate plus legacy controls, including failures), and eight events per owner
including the seed (at most 128 published owner events). Reuse existing arithmetic
literals/fault evidence and mutated copies of those records, no new world/study
episodes. Instrument the new slice; repeated focused/default gates reuse the
same cases, while existing default-suite fixtures remain separately identified.
Keep old APIs/ASTs/defaults/guards/verdicts and all qualification flags unchanged.
No question queries, reference/coordinator/log adapter, data/labels, scene/domain
change, runtime/wire adoption, dependency/acquisition, tuning, risk/allowance/
proof promotion or hardware run. No prototype, fixture or numerical execution
is authorized by the completed design-only package.


#### Private Controlled-Arithmetic Owner Prototype (2026-11-03)

The user separately approved the preceding bounded candidate/test package;
its implementation is recorded in [review §111][controlled-owner-prototype-review].
`_SyntheticC1ControlledMotionOwner` is additive and private, with literal
synthetic opt-in, finite builtin binary64 position/speed, exact heading/turn
words, copied Scenario/seed and a fresh recorder epoch. The experimental lane
and model names above are used only for this candidate, not adopted wire,
catalogue, runtime or physical contracts. All previous module AST nodes,
helpers, owners, integrator, checker/reference APIs and flags are unchanged.

Each interval uses the previous stored heading word and the fixed literal
duration/pi/two. P1 angle remains bound inside the full trace; P2 midpoint feeds
native cos/sin, P3 argument feeds native sinc and P7 output supplies the next
stored heading. Native distance/vector/position, libm/sinc and current-goal
arithmetic remain explicitly unqualified. No old-integrator/yaw-only fallback,
period fusion, clamping, recentering or new allowance is introduced.

Advance prepares trace, pose, State/frame, recorder/capture/history and event
ledger on private staged state. The staged current pose/State/frame must match
the event before publishing one completed root. A successful advance clears
the old seal; snapshot stages a recorder copy and binds the complete candidate,
including source/calibration identities, words, traces and actual frame bytes.
Tick timestamps remain nonwrapping; frame sequence uses the existing 16-bit
wrap. Seed counts within eight events; binary duration and nominal 1/20-second
time remain distinct and snapshots do not replace the seed. Capture cadence,
two-tick delivery and held data remain unchanged.

Preparation errors leave the retained root/seal intact; unexpected failures
propagate. An exception in the publication boundary marks the owner discarded
and rethrows, after which snapshot/audit/advance reject. This is conditional
staging under serialized use and stable helpers, not universal rollback, VM
atomicity, live-allocation/deadline or physical safety evidence.

The strict candidate audit compares the current retained typed digest and source
file identities. `candidate_binding_matches` and `supported_declared_word_trace`
mean owned receipt/declared support, not an independent arithmetic replay or
complete motion/source/wire consistency check. Source and wire stay unqualified,
motion stays unresolved, and all five qualification flags stay false. Old readers
reject the candidate schema; no adapter or borrowed legacy verdict is introduced.

Eight declared tests reuse four complete scenes and existing arithmetic literal
rows. Seven candidate/legacy pairs plus two rejected constructors use sixteen
attempt positions and 112 published events per completed invocation, each owner
bounded at eight events including seed. Tests compare 56 poses/States/frames,
literal first-interval words, actual midpoint/sinc consumers, stored words,
clock/capture/hold binding, rejected ingress/records and preparation/publication
faults. Focused/default repetitions use the same cases, not independent cohorts;
failed attempts and cumulative activity are recorded separately in §111.

The bounded package is complete, not numerical/native/work/physical/task-quality
qualification, task labels or runtime integration. Isolation remains the default.
Next proposed, not approved: a design-only independent candidate consistency-audit
contract for event/trace/source/frame/clock evidence and its stop conditions;
no additional imports, fixtures, adapter, implementation, risk/allowance/proof
promotion or integration. W0/TB0, Task 6/9, teacher assets and ST/board gates stay.


#### Proposed Independent Candidate Audit Contract (2026-11-03)

The user approved design-only preparation after §111
([review §112][controlled-candidate-audit-review]), not an auditor implementation,
numerical/fixture run or qualification. The local hypothesis
is that a matching retained digest establishes receipt but cannot independently
check the relations inside that receipt. The current candidate audit compares
outer keys/flags, source identities and its retained digest; it does not replay
trace cells, event links, State/frame values or capture clocks. The proposed
default keeps that audit, all old APIs/verdicts/flags and isolation unchanged.

An additive private auditor would separate a caller-supplied trusted ownership
anchor from independently checked content. A re-signed internally inconsistent
copy can have a valid self-digest without either ownership or consistency.
Never obtain the expected ownership anchor from the submitted bundle itself;
content consistency alone cannot authenticate a producer or live source.

| Proposed Check | Independent Relation / Required Input | Stop / Evidence Limit |
| --- | --- | --- |
| IA0: anchor | Externally retained expected lane/model/epoch/source identities and digest, distinct from submitted content. | Missing anchor leaves ownership unresolved; a copied/self-digest is not authority. |
| IA1: schema | Exact nested keys, builtin nonboolean integers/finite words, typed pose/State/frame and bounded record sizes. | Reject unsupported types/shape before copying, hashing or arithmetic; no new work allowance. |
| IA2: trace | Reconstruct ordered P1/P2/P3/P7 rational operands, RN64 cells, truncated residue and sign correction independently of producer helpers. | Unsupported/error stops; no accepted native/TB0/proof or full-motion claim. |
| IA3: events | Seed-only first event, consecutive nonwrapping ticks, previous/next pose words, fixed twist/constants and stored heading linkage. | No goal-normalized heading substitution, omitted interval or snapshot-based reset. |
| IA4: State/frame | Event State and actual frame match source current State/frame, sequence/timestamp/twist and explicit binary32 conversion. | Binary64-to-wire differences are reported separately, not hidden by tolerance or coercion. |
| IA5: clocks | Separate binary-step and nominal elapsed time; acquisition/delivery/hold reference the existing event ledger and epoch. | No merged clocks, changed cadence/latency or inferred missing event. |
| IA6: source scope | Check declared capture/history/relative-input relationships without recapturing geometry or qualifying returns. | Missing ledger/capture evidence stays unresolved; no physical/source authority or clearance inference. |
| IA7: result | Distinct ownership, trace, event, frame and source-clock statuses, all qualification flags false. | No old-verdict borrowing, candidate runtime adoption, query/reference/log adapter or universal rollback. |

This initial matrix is preparation only. Proposed acceptance checks must
distinguish an unchanged owned receipt, a self-re-signed inconsistent copy,
consistent but unowned data, and incomplete evidence; hashes cannot substitute
for independently computed relations. No new importer, implementation,
fixture, primitive allowance, risk policy, task data or hardware work is
authorized by this design package. W0/TB0 and numerical/physical/task-quality
qualification remain open.

**Proposed boundary and ownership assumptions.** A separate private
`_audit_synthetic_controlled_candidate` would take the existing bundle, an
optional externally retained expected anchor and literal synthetic opt-in.
This is a suggested function boundary, not a new implemented API or schema.
It must not construct/advance an owner, call the candidate's `audit` or producer
trace/RN64 helpers, recapture geometry, query questions or parse a log. Existing
public State codecs may be reused for codec correspondence only; standard-library
integer/Fraction operations share the still-unqualified trusted base.

The trusted caller may retain lane/model/epoch, source/calibration identities,
reference tick and digest from its own authorized snapshot receipt at issuance.
It must not derive the expected anchor from a later submitted copy. Invalidate
the anchor after successful advance, source change or ambiguous publication;
if currentness cannot be established under serialized access, ownership stays
unresolved. No new generation counter, anchor exporter or lifetime policy is
adopted. Matching a digest means matching that caller's anchor, not independent
source authority, genuine capture history or a current live binding.

| Submitted Record | Anchor Relation | Content Relation | Proposed Interpretation |
| --- | --- | --- | --- |
| Unchanged owned snapshot | Matches a separately current anchor | Checked relations pass | Receipt plus bounded consistency only, never qualification. |
| Re-signed inconsistent copy | Does not match the retained anchor | At least one checked relation fails | Report both facts; do not stop semantic checking merely because self-hashing succeeds. |
| Consistent copy without trusted anchor | Unknown | Checked relations pass | Consistent declared data, ownership unresolved. |
| Owned but incomplete evidence | Matches | Some relations lack required evidence | Preserve checked statuses; completeness remains unresolved, never fabricate missing values. |

A stale/mismatched anchor cannot become current by re-signing or by resetting the
seed at snapshot time. Ownership mismatch and content inconsistency are distinct:
an unowned record is not necessarily arithmetically inconsistent. Do not accept
an anchor submitted through the same untrusted path as proof of authority.

**Independent trace obligations, proposed.** Decode finite words by sign,
exponent and significand using integer/rational mathematics, separately tracking
signed zero. Verify exact constant words and the unchanged heading/turn profile;
do not use native float arithmetic as the rounding oracle. Require exactly four
ordered rows, eleven intermediate words and ten unconditional rounded cells,
plus the conditional negative-residue addition cell. Check names, operations,
operand linkage, canonical positive-denominator ratios, zero tags, words,
rounding-error ratios and correction status, not just the final heading.

For each arithmetic cell, independently derive its exact rational result and
check the claimed finite RN64 word against the declared rounding rule, including
adjacent midpoint/tie parity, subnormal/zero signs, carry and overflow stop.
This is a future verifier obligation, not a new correctness derivation or accepted
proof. The truncated quotient, exact raw residue and subsequent sign/zero
correction are separate. Keep the two period cells separately linked, preserve
the period-reaching correction and both stored pi endpoints; no floor-remainder
substitution or clamping. Conditional §108 closure/raw-residue facts cannot replace
checking the submitted worksheet or authorize an allowance.

**Event, frame and source-clock relations.** Check exact nested keys and types
against the existing private candidate record, rather than stripping fields into
a legacy motion schema. Seed has no preceding trace; event count includes it and
stays at most eight. Tick/word/pose/trace links, seed pose, fixed twist/constants,
last source reference tick/pose and epoch must agree. Bind prior stored heading,
never goal-normalized heading. The Scenario's declared start need not equal the
separately supplied seed pose: that was not a constructor requirement and must
not silently become a new scene restriction.

Check each event's State encoding against its actual frame, last-event/source
State and frame correspondence, sequence `(tick & 0xFFFF)` and nonwrapping
timestamp `tick*50000`. A valid codec projection may change binary64 State fields
to binary32. Report those changed fields separately; decode/encode correspondence
is not equality with the original scalar, independent codec verification or
wire-input qualification. No numerical tolerance, signed-zero normalization or
JSON boolean/integer alias is introduced to hide a discrepancy.

Derive nominal elapsed time from the original seed as `(tick-seed_tick)/20` and
binary elapsed as `(tick-seed_tick)*stored_duration`; neither overwrites the
other. Check existing capture eligibility (`tick == 0 or tick % 4 != 1`), shared
view acquisition tick/pose, two-tick delivery, source epoch/reference tick and
the latest eligible delivered capture for each exposed snapshot tick. Repeated
held records retain the same capture ID and identical typed capture bytes while
snapshot tick advances. Captures must link to existing ledger events; missing
seed/interval evidence stays unresolved, not inferred from current pose.

Only delivered/held history is exposed by the current recorder snapshot. Its
pending queue is not exported: do not claim pending capture completeness or
invent warmup deliveries. Bound exposed history at eight and arrays to the
existing eight-view shapes/dtypes. Relative history copies of capture ticks,
ranges and masks must match the corresponding private source entries, preserving
dtype/shape/order and masked-zero conventions. Native relative poses/body goal,
source-scale guards and ideal ray/return correctness remain outside this checker;
unknown relative status remains unknown. No recapture, native transform replay,
source-scale relaxation, physical metrology or negative/clearance inference.

**Result and failure contract, proposed.** Return separate ownership-anchor,
schema, trace, event-link, codec-projection, capture-clock and copied-input statuses
with checked counts/reasons and an explicit list of unverified relations. Use
`consistent_checked_relations`, `inconsistent_record` or `unresolved_evidence`
for content, and distinct anchor match/mismatch/unresolved outcomes. All training,
real-input, free-space, numerical-certification and producer-parity flags remain
false; native-motion/goal/relative-transform and source-authority verdicts remain
unresolved. No aggregate success becomes a question answer or old consistency
verdict. Receipt-only results from §111 remain unchanged.

Preflight record/list/array shapes, finite word/type limits and the existing
4,096-bit rational ceiling before copying, hashing or arithmetic. Ratios need
canonical builtin integer fields and a positive denominator. Oversized/malformed
or unsupported evidence stops the affected check with explicit reasons; do not
change old bounds or supply native fallback. Input objects already allocated by
the caller, intermediate allocator behavior, time/live memory and W0/TB0 are
not bounded by this preflight. The proposed auditor has no retained publication
state: it does not mutate owner/recorder/anchor/input and propagates allocation,
interruption or unexpected failures rather than claiming universal abstention
or rollback. Source-file hashes still cannot attest native builds/live bindings.

| Proposed Gate | Future Discriminating Check | Required Limit |
| --- | --- | --- |
| AC0 | Preserve all old module ASTs/APIs/defaults/flags/verdicts/artifacts and receipt-only behavior. | Additive private checker only; no adopted schema/adapter. |
| AC1 | Exercise all four anchor/content quadrants and stale/foreign/self-re-signed records. | Trusted expected anchor is separate and currentness explicit. |
| AC2 | Reject bool/float aliases, wrong keys/dtypes/shapes, oversized ratios/lists and missing evidence. | Preflight before traversal/copy/hash/work; old bounds unchanged. |
| AC3 | Independently check each literal/corrupted trace cell, signed zero, residue/correction and row order. | No producer trace/RN64 oracle or accepted native/proof claim. |
| AC4 | Check seed/event/previous-word/twist and both elapsed clocks without reset. | Eight events/nonwrapping timestamps; sequence wrap stays separate. |
| AC5 | Separate exact frame bytes, codec projection and reported binary32 changed fields. | No widened tolerance or hidden precision/type conversion. |
| AC6 | Check exposed capture/delivery/hold and copied relative ticks/ranges/masks, including incomplete history. | No pending-queue claim, recapture, transform/return/physical qualification. |
| AC7 | Verify nonmutation, explicit failure results and bounded activity; run focused/default gates. | No owner advancement inside auditor, question/reference/coordinator/log use or flag promotion. |

**Exit, tradeoff and next permission.** The design-only contract is prepared;
IA0-IA7 and AC0-AC7 are unexecuted requirements, not an implemented auditor or
accepted numerical/source evidence. A separate checker is preferred to extending
the receipt audit: it exposes shared trusted-base/native gaps and avoids changing
old acceptance. Reusing the producer trace as an oracle would be cheaper but
circular; replaying native dynamics/geometry would exceed this proposed scope.
Isolation remains the default.

Next proposed, **not approved**: additive private auditor/tests only, at most
eight reused motion cases/four already-used complete scenes, sixteen constructor
attempt positions including failures/legacy controls, eight events each including
seed (128 published events maximum), and at most 32 auditor attempts including
failed checks per completed invocation. Reuse literal worksheets and mutated
record copies; count constructors/events/captures/traces/audits, with repeated
focused/default gates using the same cases and existing suite controls separate.
No new world/study episode/data, query/reference/coordinator/log adapter,
native motion/transform/geometry replay, dependency/acquisition, runtime/wire
adoption, tuning, risk/proof/allowance/qualification promotion or hardware run.
No implementation, imports or numerical/fixture execution follows from this
completed design-only scope.


#### Private Independent Candidate Auditor (2026-11-03)

The user separately approved the bounded auditor/tests proposed above;
[review §113][controlled-candidate-auditor-review] records implementation,
verification and limits. `_audit_synthetic_controlled_candidate` is an additive
private opt-in checker, not a runtime consumer or adopted input schema. The old
receipt audit, owners, arithmetic helpers, references, defaults, bounds and
qualification flags remain unchanged. Isolation remains the default.

An optional caller-retained anchor carries currentness, lane/model/epoch,
source/calibration identities, reference tick and digest. The caller must obtain
it at authorized issuance, not from a later untrusted copy, and invalidate it
after advance/source change/ambiguous publication. Matching means correspondence
to that declared current anchor, not independent source authority or a fresh
live-source attestation. Missing currentness remains unresolved. Self-re-signing
does not suppress semantic checks or turn a mismatched anchor into ownership.

The checker preflights bounded builtin/array records, exact nested keys and
typed State/trace data before hashing and semantic replay. Its private structural
ceilings are ten nesting levels, at most 24 mapping entries, eleven non-array
sequence elements, eight events/history entries, finite existing eight-view
array shapes/dtypes, 64-character strings, existing maximum frame size and the
4,096-bit integer/rational ceiling. These are supported-record preconditions,
not global scene restrictions, new numerical allowances or allocator/time/live
memory bounds. Word width and ratio sizes precede rational decoding/GCD work;
unsupported evidence stops explicitly. Unexpected/allocation/interruption errors
are not universally converted into success, abstention or rollback.

Independent integer/Fraction relations check the four ordered trace rows,
operand/exact/error ratios, finite claimed words, adjacent midpoints/tie parity,
signed zero, truncated residue and sign correction. No producer arithmetic
helper or owner audit is used as the oracle. Separate periods, period-reaching
correction and both pi endpoints remain intact. Seed/event/previous stored
words, fixed twist/constants and nominal versus binary elapsed clocks are
linked without resetting at snapshot. Standard-library integer/Fraction and
native/work trusted-base gaps remain; this is not accepted proof or all-domain
qualification.

Actual event State/frame bytes and last source State/frame are checked through
the existing codecs. Binary32 changed fields are reported by tick, separately
from exact frame correspondence. Exposed delivery/hold records link to eligible
ledger captures and poses with two-tick latency; repeated capture IDs preserve
typed capture bytes. Relative acquisition ticks/ranges/masks must be exact typed
copies, including masked positive zero. No pending queue, native motion/goal/
relative transform, source-scale calculation or ray geometry is replayed.

Results separate ownership, schema, trace, event, codec, capture and copied-input
statuses, checked counts, reasons and explicit unverified relations. Owned but
incomplete issued history preserves checked trace/codec results and remains
unresolved. All five qualification flags stay false. Native motion/goal/relative
transforms, returns, pending completeness, source authority and W0/TB0 stay
unqualified; no aggregate is a question answer, old verdict or Task 6/9 exit.

The eight reused cases/four existing scenes use eight constructor positions,
64 published events including seeds and 32 auditor attempts per complete
invocation, within the approved sixteen/eight/32 caps. Tests forbid producer,
owner, source-audit, transform and query paths inside the auditor, preserve
receipt-only behavior and check nonmutation. These finite controls do not
exhaust all malformed inputs or establish independent codec/native proof.
No new primitive corpus, world/study episode, log/data adapter, runtime/wire
adoption, dependency/acquisition, risk/proof/allowance promotion or hardware run.
The bounded approval is exhausted. Next proposed, not approved: design-only
gap/exit planning for remaining native position/goal and relative-transform
evidence; no further implementation, extraction or fixture execution follows.


#### Native Arithmetic Gap and Exit Plan (2026-11-04)

After reboot, the user's continuation approved the design-only follow-up offered
at §113; [review §114][native-gap-plan-review] records that scope. This is a
proposal, not native replay, arithmetic implementation, an accepted error bound
or promotion of the private candidate. Source/tests, old verdicts and all five
qualification flags remain unchanged. Isolation stays the recommended default.

**Local hypothesis.** The checked P1/P2/P3/P7 words do not constrain every
native consumer result: a consistent declared trace is not a bound on native
position, current goal or relative transforms. The nearby source confirms that
`advance` consumes words 2/4/10 as midpoint/sinc argument/stored heading, then
computes distance and position natively. `_prepare_event` normalizes heading
only for the current goal. The relative mapper separately uses vector trig and
row-vector matrix products. Their unverified relations must not disappear behind
the auditor's `consistent_checked_relations` result.

| Gap | Existing Consumer / Bound Input | Required Exit Evidence / Stop |
| --- | --- | --- |
| NF0: boundary | Word-to-native midpoint, argument and next heading; builtin speed and literal `0.05`; native-to-word coordinates/State fields. | Bind signed-zero bits, exact duration/constant words, conversions, actual scalar/array dtype/shape and evaluation order. Record correspondence is not live FP/build qualification. |
| NF1: sinc | `np.sinc(argument)` at the stored P3 word, not an ideal unrounded argument. | Cover the complete normalized-sinc wrapper, zero/tiny substitution, pi multiplication, sine and division on the computed domain. Shared-library replay or a sampled maximum is not a uniform local-error bound. |
| NF2: motion | `speed * 0.05 * sinc`, scalar cos/sin at the stored P2 midpoint, then NumPy coordinate products/additions from the previous stored pose. | Bind rounding/promotion/contraction, coordinate scale/cancellation and finite intermediates. Compose local sinc/trig/rounding and P2/P3 input errors once; missing evidence leaves motion unresolved. |
| NF3: goal heading | Scalar `atan2(sin(r), cos(r))` for current stored `r`, followed by scalar cos/sin. | Bound norm separation, quadrants/cuts and circular error for the actual wrapper/domain. This heading never replaces the stored motion heading or becomes another propagated state update. |
| NF4: goal components | Inferred goal-array subtraction from current stored position; scalar product/sum expressions into `State.goal_m`. | Preserve actual goal dtype and each arithmetic/conversion step, goal lever arm and cancellation. A same-stored-pose target does not add accumulated world-position error again. Wire projection is a separate later conversion. |
| NF5: relative poses | Captured/reference stored poses; vector heading normalization and difference, row-vector translation/rotation, then vector heading normalization again. | Bind every slot to its acquisition/reference events, vector dtype/shape/path, matrix reduction order, branch and circular enclosure. No scalar/vector bit-equality assumption or native transform replay is implied. |
| NF6: relative goal/arena | `(goal-reference[:2]) @ rotation`, `fixture_arena_yaw_rad=-yaw`, versus the owner's different scalar goal expression. | Specify the common real target and separate implementation errors. Last-bit disagreement alone is not geometric inconsistency; agreement is not an error bound. Do not copy one result over the other or introduce a tolerance to hide it. |
| NF7: source scale | Max/abs reductions over original reference, goal, capture poses and derived relative values; existing scale guard. | Preserve source-coordinate magnitude and the original guard even after translation/rotation. A small relative result cannot erase cancellation risk or qualify the scale computation, ray returns or source authority. |

**Claim ladder and acceptance.** Four distinct future claims are proposed:

1. Declared-record consistency: retain §113's exact checked relations and explicit
  unverified list; it already exists and is not expanded by this plan.
2. Same-environment execution compatibility: independently written expressions
  could compare selected native outputs, but still share Python/NumPy/libm and
  need fresh implementation/FP identity after reboot. Producer/mapper calls are
  not independent checkers, and different scalar/vector expressions need not
  be bit-identical. This claim would remain diagnostic, not numerical accuracy.
3. Independent mathematical enclosures: a rational/interval reference with
  justified remainder/domain evidence can enclose an exact mathematical target.
  A point inside an enclosure shows compatibility only; a point outside the
  bare ideal enclosure is not a faulty implementation without a separately
  justified implementation-error allowance. Never fit that allowance to residuals.
4. Qualified computed-program enclosure: bind actual implementation/FP paths,
  prove uniform local errors and computed-domain closure, and compose them
  through NF0-NF7 with independently reviewed reference uncertainty. W0/TB0,
  source authority, physical error, task quality and runtime adoption remain
  separate gates even if this numerical claim eventually closes.

The recommended next direction is an isolated mathematical NF1 prerequisite,
not another native replay batch. A proposed rational sinc enclosure would take
the exact stored argument word, enclose real pi and the entire-function sinc
series with explicit interval/remainder justification, and handle both signed
zeros without assuming the installed wrapper returns exact one. It would expose
only mathematical bounds or unresolved evidence. It would not measure or bound
the installed wrapper's deviation, certify `np.sinc`, consume owners/logs, or
replace a producer operation. Existing `1bb89fe` remains mathematical reference
evidence, not a candidate-owner adapter or installed-primitive guarantee.

**Next proposed permission, not approved:** a design-only NF1 enclosure contract
and feasibility argument, including exact target, zero/nonzero branches, series
remainder/domain closure, rational work limits, reuse of existing mathematical
helpers versus a separate private boundary, and discriminating acceptance/stop
checks. Prepare the specification before requesting implementation or numerical
execution; no term count, precision/work allowance or prototype API is adopted
here. This is the first unresolved dependency in NF2, not completion of motion
qualification. Alternatives are retaining isolation with no arithmetic work, or
a separately approved shared-library compatibility study; the latter cannot
close NF1's independent accuracy obligation.

**Paper exit checks.** NX0-NX5 below are review checks for this plan, not executed
numerical gates or an accepted proof:

| Check | Required Content / Discriminating Stop |
| --- | --- |
| NX0 | All eight NF rows map to current consumers and explicit missing evidence; checked trace words are never called native accuracy. |
| NX1 | The four claims remain separate; no shared replay, sample maximum, interval overlap or source hash is promoted to a uniform guarantee. |
| NX2 | Preserve previous stored pose/heading, original seed and separate binary/nominal clocks; G1/NF3 remains goal-only. |
| NX3 | Local same-stored-pose errors, propagated trajectory errors and current goal/relative errors are not double-counted. Both sides of a relative transform and circular cuts need their own evidence. |
| NX4 | Keep codec changes, source scale/guards, missing/pending captures, return membership and source authority separate; no inferred completeness or scalar/vector bit equality. |
| NX5 | Scope is documentation only; source/tests/defaults/bounds/flags/verdicts, `1bb89fe` and old artifacts remain unchanged. Every later read/run/code/integration scope needs separate authorization. |


#### Proposed NF1 Rational Sinc Enclosure Contract (2026-11-04)

The user approved this design-only NF1 contract/feasibility preparation after
§114 ([review §115][sinc-contract-review]). Nothing below implements a helper,
accepts a proof/error allowance or renews any fixture execution scope. The
recommended boundary is a separate private word-only mathematical reference;
the producer, old rational reference and independent auditor remain unchanged.

**Target and input boundary (SC0).** Given an exact finite binary64 word,
decode its signed rational value $q$ by integer significand/exponent arithmetic.
Require a builtin nonboolean unsigned 64-bit integer and literal synthetic
opt-in, not a coerced float/NumPy scalar, array, trace, owner or log record.
The proposed local domain is $|q|\le 1/64$, checked exactly on that input; this
is not a new global producer/sensor restriction or an assertion that every
future P3 result belongs to it. Missing domain closure stays unresolved.

Conditional paper closure uses the declared $|\mathrm{turn}|\le3/2$ and exact
duration word $0<d<1/16$. Monotonic RN64 and representability of $3/32$ give
$|a|=|\operatorname{RN64}(\mathrm{turn}\,d)|\le3/32$.
The positive pi word exceeds three and its doubling is exactly representable,
so the separately rounded P3 period $b_q$ exceeds six. Therefore
$|a/b_q|\le1/64$; monotonic RN64 and representability of $1/64$ close the
stored-word domain too. This is conditional on the trace's rounding/domain
obligations, not new source authority, installed-wrapper evidence or approval
to run traces. The helper must still check its submitted word independently.

The target is the real-pi normalized function at this **stored** argument:

$$
F(q)=\begin{cases}1,&q=0,\\
\sin(\pi q)/(\pi q),&q\ne0.\end{cases}
$$

Both zero words retain their original word/sign metadata and have the exact
mathematical enclosure $[1,1]$; no pi construction or division is necessary.
This does not say installed `np.sinc` returns exactly one on either word: its
wrapper's tiny substitution and native arithmetic remain NF1 implementation
gaps. For nonzero input, do not replace $q$ by the ideal unrounded P3 argument,
cancel its rounded period against wrapper pi, or divide an interval by $q$.
P3 argument error versus the ideal trajectory is a separate later composition.

**Independent real-pi enclosure (SC1).** A new local rational construction may
reuse the mathematical identity of `1bb89fe`, not its owner-shaped interface
or a successful old result. For $d\in\{5,239\}$ define

$$
A_m(d)=\sum_{k=0}^{m-1}\frac{(-1)^k}{(2k+1)d^{2k+1}},\qquad
e_m(d)=\frac{1}{(2m+1)d^{2m+1}}.
$$

The alternating arctangent series gives $[A_m,A_m+e_m]$ for even $m$ and
$[A_m-e_m,A_m]$ for odd $m$. Let these intervals be $[a_d,b_d]$. Machin's
identity, with its quadrant justified independently as in the earlier paper
reference, gives

$$
\pi\in[p_L,p_U]=[16a_5-4b_{239},\;16b_5-4a_{239}].
$$

For the identity's branch, set $\alpha=\arctan(1/5)$ and
$\beta=\arctan(1/239)$. Exact tangent addition gives
$\tan(2\alpha)=5/12$, $\tan(4\alpha)=120/119$ and
$\tan(4\alpha-\beta)=1$. Since $0<\beta<\alpha<1/5$ and
$3<\pi$, the angle satisfies $0<4\alpha-\beta<4/5<\pi/2$.
It is therefore $\pi/4$, not another tangent branch; no floating phase or
installed atan2 selects the identity.

Require ordered rational endpoints and the exact bracket $3<p_L\le p_U<4$;
unsupported construction/bracket/work stops unresolved, never substitutes
binary64 `math.pi`. Shared standard-library integer/Fraction/GCD behavior
remains an unqualified trusted base, not independent native/build proof.

**Even-power interval and remainder (SC2).** With nonzero exact $q$, form
$T=[q^2p_L^2,q^2p_U^2]$. SC0/SC1 give
$0\le T_L\le T_U\le1/256$. Evaluate

$$
f(t)=\sum_{k=0}^{\infty}\frac{(-1)^k t^k}{(2k+1)!},\qquad F(q)=f((\pi q)^2).
$$

For $0\le t\le1/256$, consecutive absolute terms have ratio
$t/((2k+2)(2k+3))\le1/1536<1$, hence decrease to zero. For $N\ge1$
included terms, $P_N(t)=\sum_{k=0}^{N-1}(-1)^kt^k/(2k+1)!$ and the uniform
next-term magnitude is $U_N=T_U^N/(2N+1)!$. The remainder interval is
$E_N=[0,U_N]$ for even $N$ and $E_N=[-U_N,0]$ for odd $N$. Count included
terms, not polynomial degree; the first omitted factorial is $(2N+1)!$.

Compute a rational interval $H_N\supseteq\{P_N(t):t\in T\}$ by Horner
evaluation with exact coefficients and interval operations: each multiplication
uses the minimum/maximum of all four endpoint products. Repeated occurrences
of $T$ are correlated in the target; ordinary interval evaluation may overbound
them but must not assume independence, endpoint monotonicity or shrink the hull.
Return $H_N+E_N$ as the exact rational enclosure. The $N=1$ paper sentinel is
$[1-T_U/6,1]$. Evenness gives identical enclosures for $q$ and $-q$ without
changing either original word. No native sine, sinc, pi, float division or
floating endpoint conversion is a mathematical oracle.

**Proposed finite-work configuration (SC3).** Candidate defaults are 32 terms
per arctangent, eight included sinc terms and 65,536 bits per rational numerator/
denominator, including intermediates. These are proposed private host-reference
limits, not an accepted new budget or a change to the old 4,096-bit arithmetic/
audit cap or the old motion-reference limits. In this configuration the sinc
polynomial ends at degree seven in $t$, and its remainder is $[0,T_U^8/17!]$.
There is no outcome-driven refinement, extra precision, term escalation or
fallback to native arithmetic.

Preflight integer/word types and operand sizes before shifts, products, sums,
denominator inversion or coefficient/power construction; validate canonical
positive-denominator pairs. Use guarded incremental products, not unchecked
large powers/factorials followed only by a final-size test. Every rational
operation checks conservative numerator/denominator growth before the operation
and canonical result size afterward. All coefficient degrees and loop bounds
are fixed before arithmetic. Input objects already allocated by the caller,
GCD internals, allocator cost, elapsed time/live RAM and W0/TB0 are not bounded
by this preflight. A finite input in SC0's domain may still stop on work; no
all-domain successful-completion or measured-resource claim is proposed.

There is a concrete nonzero paper feasibility subdomain, without claiming
runtime qualification: let the decoded dyadic denominator $Q\le2^{128}$.
For the fixed Machin construction, the common-denominator witnesses
$D_d=d^{65}\prod_{k=0}^{32}(2k+1)$ enclose every partial sum and next term.
Using $5<2^3$, $239<2^8$ and $2k+1<2^7$ gives
$D_5<2^{426}$, $D_{239}<2^{751}$ and $M=D_5D_{239}<2^{1177}$.
Both pi endpoints' canonical denominators divide $M$. Both squared-argument
denominators divide $D=(QM)^2<2^{2610}$; use 2,700 bits as a coarse bound.
Horner's endpoint denominators divide $D^7\,15!$, while the tail and final
sum endpoints divide $D^8\,17!$. Even looser per-operation accounting gives
at most $7(2700)+8(60)=19380$ denominator bits before the final sum and
$8(2700)+85=21685$ for the tail, using $15!<2^{60}$ and $17!<2^{85}$.
Thus guarded final cross-products/sums need fewer than 42,000 bits before
canonicalization. The shared denominator tightens canonical final endpoints
back below 21,700 bits; ordered-endpoint comparison products stay below 44,000.
Nested Horner intervals have absolute endpoints below two, so numerator/carry
headroom fits these rounded-up bounds too. Incremental Machin/coefficient
construction is smaller. This argues headroom below SC3's proposed cap for
this subdomain under exact canonical arithmetic, not an accepted work proof
for an unwritten program, integer/GCD internals or all binary64 denominators.

Width also has a paper bound, not a native error allowance. Let
$\delta p=p_U-p_L=16e_{32}(5)+4e_{32}(239)$ and
$\Delta T=T_U-T_L\le8q^2\delta p\le\delta p/512$.
The Horner width recurrence satisfies $w_{j+1}\le2\Delta T+T_Uw_j$,
starting at zero; all nested magnitudes are below two. Hence the final width is at most
$3\Delta T+U_8\le3\delta p/512+2^{-64}/17!$.
No decimal residual/accuracy measurement or tuned stopping target is inferred.

**Boundary, reuse and failure result (SC4).** Suggested name:
`_enclose_synthetic_sinc_word(q_word, *, synthetic_test_only=False)`, not an
implemented or adopted API. Reusing the whole old motion helper would require
fabricated motion records and conflate scopes. Extracting its nested helpers
would change old ASTs. Recommended: a separate small bounded local decoder,
Machin construction and interval kernel, reusing standard-library exact
rationals and existing literal-test conventions rather than producer helpers.
This deliberately shares the integer trusted base, not a producer-call oracle.
Do not refactor, invoke or strip tags into the old reference/auditor/owner.

Proposed results carry original word, exact decoded ratio/sign, target/domain,
zero-versus-series branch, candidate configuration, exact interval endpoints
and reason/counts. Successful nonzero results also expose pi, squared-argument,
polynomial and signed remainder intervals for independent checking. Mathematical
status is enclosed or unresolved, never a motion/source/wire verdict; all five
training/real-input/free-space/numerical-certification/producer-parity flags stay
false. Zero may omit unused interval stages explicitly. On supported input/work
failure, publish no partial enclosure. Literal-opt-in failure raises; allocation,
interruption or unexpected failures propagate rather than claiming universal
abstention/rollback. There is no retained mutable state or input mutation.
Use canonical positive-denominator integer pairs for exact result intervals;
do not make binary64 display endpoints, JSON, files or persistence part of this
private boundary. The $N=1$ sentinel and odd-count signs are paper/kernel
controls, not permission for caller-selected configurations or extra helper runs.

**Acceptance and feasibility (SC5-SC7).** These are future discriminating
requirements, not executed tests or an accepted mathematical derivation:

| Check | Proposed Requirement / Stop |
| --- | --- |
| SC5: independent controls | Pin both zero words, finite-word decoding/domain/type rejection, evenness, Machin endpoint signs, exact factorial coefficients and the $N=1$ sentinel. Check interval multiplication/series-tail parity independently, not by calling the producer or another invocation of the same reference as its oracle. |
| SC6: work and nonmutation | Pin fixed loop/configuration values, pre-operation and post-canonical growth stops, explicit unresolved results with no partial interval, strict opt-in and unchanged inputs/old module ASTs. Subnormal/tiny words cannot silently become zero; work rejection is allowed, native substitution is not. |
| SC7: evidence separation | Separate sampled mathematical enclosure checks from universal proof and installed-wrapper error. A native output outside the bare mathematical interval is not a qualified implementation fault without justified implementation error; an overlap is not qualification. No motion/goal/relative/source/codec/owner adapter, allowance or runtime consumer. |

The construction is feasible on paper without division by a small input or an
external arbitrary-precision dependency: fixed finite rational polynomials,
positive-domain alternating tails and conservative interval propagation suffice
under the stated mathematical/trusted-base assumptions. Width and successful
completion within SC3 remain unmeasured; conservative hulls/work stops may be
unhelpful and are not permission to increase budgets. This is a prerequisite
reference, not closure of NF1's installed-primitive accuracy or NF2-NF7.

**Next proposed, not approved:** an isolated private prototype/tests in the
existing diagnostic/test modules, preserving every old AST/API/bound/flag/verdict.
Suggested cap: twelve reused literal word-case positions and at most 24 helper
attempts including rejections per complete invocation, with no owner construction,
advance, capture, producer trace call or question/reference/log adapter. Reuse
the twelve existing trace sheets' stored word at index four without recomputing
the trace, plus existing input-word/type/work fault patterns within those same
case positions and attempt cap. Repeated focused/default gates reuse these
positions; old suite controls remain separate and must not be presented as new
NF1 fixtures. These caps are proposed, not executed or approved. No new primitive
corpus, scene, episode, data, native comparison, dependency/acquisition, integration,
precision escalation or qualification promotion. A later approval must explicitly
accept or revise SC3's proposed configuration and these case/attempt caps before
any import, prototype or numerical fixture execution. Current design-only work
authorizes none of them; isolation remains the default.


#### Private NF1 Rational Sinc Prototype Complete (2026-11-04)

The user separately approved the isolated helper/tests offered at §115, including
32 arctangent terms, eight sinc terms, a 65,536-bit rational cap, twelve reused
word-case positions and at most 24 helper attempts per complete invocation.
[Review §116][sinc-prototype-review] records implementation and verification.
That approval applies only to this private prototype/configuration/test scope,
not an accepted proof, native accuracy/error allowance, source authority or
runtime consumer. The preceding design draft is retained as historical context.

The [diagnostic prototype][c1-prototype-source] now contains the separate
`_enclose_synthetic_sinc_word` and its private `_SYNTHETIC_SINC_BITS` limit.
Every prior module AST node is unchanged. No producer arithmetic helper,
motion reference, owner, auditor, recorder, relative mapper or question path
calls or is refactored into it. Literal synthetic opt-in and exact finite
builtin u64 ingress precede independent integer word decoding; sign metadata
distinguishes both zero words even though their rational value is zero.
Both zero words yield the mathematical interval `[1,1]` without constructing pi.

The nonzero path constructs rational 32-term alternating arctangent brackets,
combines them with Machin's identity, checks the real-pi bracket, encloses the
squared argument and evaluates the eight-term even polynomial by four-product
Horner interval multiplication. The nonnegative remainder after eight terms is
`[0,T_U**8/17!]`. Exact canonical integer-pair stages expose arctangent, pi,
squared argument, coefficients, polynomial and remainder separately. No native
sinc/trigonometry/float oracle, tiny substitution, endpoint rounding, persistence
or owner/reference/log adapter is used. Domain/work failures remain unresolved
with no partial enclosure; opt-in failure raises, and unexpected/allocation
errors propagate. Successful and rejected results keep all five qualification
flags false and native-sinc/motion statuses explicitly unresolved.

Incremental powers/factorials, rational arithmetic and endpoint comparisons
preflight conservative operand growth; canonical results are checked afterward.
Returned operation counts and canonical-result bit counts describe checked
arithmetic, not elapsed time/live RAM, allocator/GCD internals, W0/TB0, universal
completion or a computed-program enclosure. Subnormal inputs are decoded exactly
or rejected on work, never replaced with the zero target. There is no adaptive
term/precision increase or fallback. The old 4,096-bit arithmetic/auditor limit,
old mathematical reference, normal defaults and verdicts are unchanged.

One twelve-case test reads stored q at index four of the existing literal
sheets without producing traces. Each completed invocation asserts exactly
two helper attempts per position: 13 enclosed results (six zero/seven series,
including reflection), eight unresolved results and three expected exceptions.
Independent exact partial sums, coefficients, expanded endpoint polynomials,
the one-term bracket, remainder and symbolic width checks use only those cases.
Native/producer/owner paths are forbidden; strict word/domain/opt-in, minimum-
subnormal early-work rejection, late canonical-result rejection, allocation
failure propagation, separate results and false flags are covered. These are
bounded synthetic arithmetic fixtures, not a new corpus or task data/proof.

The full source gate passes 2,137 tests plus the known transformer xfail and
71 existing warnings; focused checks, lint, changed-file format, editor diagnostics
and old-AST preservation pass (§116). No C/runtime source change or additional
opt-in sanitizer/Arm/hardware run; default-suite legacy controls remain separate.
This approved package is complete and exhausted. Next proposed, not approved:
design-only conditional correctness/work-obligation review of this helper's
decoder, Machin/series intervals, guards and result semantics. No new import,
fixture run, extraction, consumer/native comparison, allowance/proof acceptance,
integration, dependency/acquisition, data or qualification promotion follows.
NF1 native accuracy, NF2-NF7, source authority and broader task gates stay open.


#### NF1 Conditional Correctness and Work Review (2026-11-04)

The user separately approved the design-only review offered at §116;
[review §117][sinc-correctness-review] records its scope and checks. The object
is `_enclose_synthetic_sinc_word` at the §116 source identity, not an installed
native sinc, a consumer or a new implementation. No project import, fixture,
arithmetic execution, source extraction or accepted proof/allowance follows.
The source/test files were reread after an edit notification; the actual Git
baseline is clean `4606b15` with no current source/test diff.

**Disposition.** No algebraic mismatch was identified in the reviewed local
path under SR0's assumptions. SR1-SR6 support conditional partial correctness
of a normally returned mathematical enclosure. SR7 supports only specific
algebraic size guards and a paper operation ledger; SR8 supports ordinary-return
semantics, not universal rollback. SR9 retains isolation. These are paper review
outcomes, not accepted proofs, runtime guarantees or closure of W0/TB0, native
accuracy, source authority or the numerical/physical/task-quality gates.

| Obligation | Conditional Outcome / Remaining Boundary |
| --- | --- |
| SR0: stable semantics and identities | Assume builtin integer semantics, exact canonical Fraction arithmetic/comparisons and terminating allocation/GCD operations, ordinary serialized execution, fixed helper/global bindings and the declared 65,536-bit cap. No installed/build/live trusted-base proof is supplied. |
| SR1: word/domain/zero | Exact builtin nonboolean u64/finite rejection precedes decoding; normalized/subnormal formulas and both signed-zero words have the intended stored-rational target. No producer-word authenticity or source-domain admission follows. |
| SR2: scalar and interval kernel | Exact add/multiply/positive-divisor inversion and guarded comparisons preserve rational semantics; four-product hulls enclose products, including negative Machin scaling. No generic public rational kernel is adopted. |
| SR3: Machin construction | The 32-step odd-power/partial-sum invariant gives an even-term lower endpoint and positive next term; the earlier tangent/quadrant identity transfers the two brackets to real pi. A passed numeric bracket alone would not prove this identity. |
| SR4: squared argument and coefficients | Positive pi, squared q and exact domain give ordered nonnegative T; the degree loop stores exactly eight sinc coefficients and leaves 17! as the tail divisor. No floating underflow/tiny substitution. |
| SR5: Horner inclusion | Natural interval induction encloses the same scalar polynomial for every t in T; repeated occurrences are correlated, so endpoint-only polynomial checks do not replace this argument. |
| SR6: remainder, width and evenness | Decreasing even-series terms yield a nonnegative tail beginning at index eight and the prior symbolic width bound; the squared target gives evenness, with original word/sign retained. Not an installed-library error bound. |
| SR7: finite guards and work | Direct algebraic growth checks, fixed loops and conditional denominator headroom are justified below. Counters exclude constructors/comparisons and hidden runtime work; no universal completion, time/live-RAM or native-work bound. |
| SR8: rejection and publication | Supported rejection returns no enclosure/stages; only local input metadata/work may remain. Success stages are assembled before update. Unexpected/allocation/interruption errors propagate; no claim that an interrupted local dict update rolls back. |
| SR9: evidence and consumers | Five flags remain false and native-sinc/motion statuses unresolved. Results are mutable declarations, not attestations; no source/owner/trace/codec/relative/runtime consumer or promotion. |

**SR0-SR2: decoding and arithmetic.** Let exponent field $e$, fraction field
$f$ and sign $s$ come from the finite submitted word. The code uses
$m=f+2^{52}$ when $e>0$, otherwise $m=f$, with
$p=e-1075$ when $e>0$, otherwise $p=-1074$. Thus
$q=(-1)^s m2^p$ has the normal binary64 formula, or the subnormal
$(-1)^sf2^{-1074}$. Exact canonicalization cannot turn a nonzero significand
into zero. Only the two zero words have zero value; their separate sign remains
in metadata. The domain check applies to this decoded value, not ideal motion.
The raw shifts are preflighted; fixed word masks/constants and already allocated
caller integers are not a general allocation boundary.

For canonical operands with positive denominator, addition preflights
$\max(N_L+D_R,N_R+D_L)+1$ numerator bits and $D_L+D_R$ denominator bits;
multiplication preflights $N_L+N_R$ and $D_L+D_R$. Here N/D are operand bit
lengths, not values. These bound naive cross-products/sums; canonical reduction
cannot enlarge their magnitudes. `divide` in this program inverts only positive
65 or factorial divisors, never q or an interval containing zero. Comparisons
preflight the two cross-product bit sums, including the final interval-order
check. Exact semantics and implementation scratch costs of Fraction/GCD remain
assumed rather than inferred from these formulas. `abs(value)` preserves operand
bit sizes but its internal construction is not counted by `bounded`.

**SR3-SR4: loop invariants.** At the start of arctangent iteration k,

$$
\mathrm{odd\_power}=d^{-(2k+1)},\qquad
\mathrm{partial}=\sum_{j=0}^{k-1}\frac{(-1)^j}{(2j+1)d^{2j+1}}.
$$

One coefficient/product/add and multiplication by $d^{-2}$ preserve this
invariant. After 32 iterations (last Python index 31), the power is $d^{-65}$;
division by 65
gives the correct first omitted positive magnitude, not degree 63 or 67.
Alternating terms decrease to zero for both d values. Multiplication by the
negative constant -4 reverses that component's endpoints through the generic
four-product hull. Together with the already specified Machin quadrant argument
this encloses real pi; the explicit `3 < p_L <= p_U < 4` check is an additional
stop, not an oracle. Consequently $0<T_L\le T_U\le1/256$ for accepted nonzero q;
the absent lower-bound check is supplied by these invariants, not a new guard.

After degree j of the coefficient loop, `factorial` is j! (with 0!=1).
Odd j=1,3,...,15 append $(-1)^{(j-1)/2}/j!$, exactly coefficients k=0,...,7.
The loop continues to j=17, so its final factorial is 17!, not 15! or 16!.
All powers/factorials grow incrementally through guarded multiplication.

**SR5-SR6: enclosure closure.** Starting with $[c_7,c_7]$, the seven Horner
steps compute $I_k=[c_k,c_k]+T I_{k+1}$. The minimum/maximum of all four
endpoint products contains each product of members of the two intervals.
Induction therefore contains $\sum_{k=0}^7 c_k t^k$ for every one fixed
$t\in T$, without asserting that independently chosen t values are the same.
For this domain, successive absolute sinc-series terms have ratio at most
$1/1536<1$, hence the alternating tail after the eight included terms is
$[0,T_U^8/17!]$. The eight-step `tail_power` loop starts at one and produces
exactly $T_U^8$. Adding that interval gives a conditional enclosure of F(q).
The test's endpoint expansions/sentinel/width checks are finite controls, not
this quantified induction or an independent trusted base.

For the earlier width claim, all nested Horner magnitudes remain below two
since $|c_k|\le1$ and $T_U\le1/256$. With zero initial width,
$w_{k}\le2\Delta T+T_Uw_{k+1}$ gives polynomial width below $3\Delta T$;
adding the tail gives at most $3\delta p/512+2^{-64}/17!$ as previously stated.
Squaring q makes the complete mathematical result even; zero words retain their
metadata and exact unit interval separately. Neither width nor symmetry is a
bound on wrapper pi multiplication, native sine/division or zero substitution.

**SR7: algebraic work ledger, not measurements.** Under SR0 and complete
nonzero success, the source-level `rational_operations` increments are:

| Phase | Conditional Add/Multiply Counter Increments |
| --- | --- |
| Two arctangent brackets | 2(1 + 32(3) + 1 + 1) = 198 |
| Machin endpoint products and sums | 8 + 2 = 10 |
| q square, two pi squares and squared-argument hull | 1 + 2 + 4 = 7 |
| Factorials and eight coefficient divisions | 17 + 8 = 25 |
| Seven Horner interval products/sums | 7(4 + 2) = 42 |
| Eight tail products and final division | 8 + 1 = 9 |
| Final enclosure addition | 2 |
| Total | 293 |

Division increments once via multiplication; its reciprocal construction is not
another increment. On the same path there are conditionally 116 calls to the
nested `rational` constructor and 66 to `compare`, not reflected in that counter.
The constructor count decomposes as
$2+2+2(1+32+1+1)+4+3+1+(17+8+8)+1=116$: input/domain, unit/zero,
two arctangent loops, Machin constants, pi checks, series-domain constant,
factorial/coefficient/reciprocal constructions and the final tail reciprocal.
The comparison count is $1+12+3+6+1+42+1=66$: input-domain, Machin hulls,
pi checks, squared-argument hull, series-domain, Horner hulls and final order.
These are paper counts from fixed loops, not executed or instrumented results,
and not counts of all Fraction/integer allocations. Zero success has no
add/multiply increments but still decodes, constructs rationals and compares.
A rejected operation may increment before its canonical result fails the guard.
`max_result_bits` is the maximum canonical size that passed `bounded`, not the
largest attempted result, pre-reduction integer, comparison product or live RAM.
For example, zero still reaches construction of the $2^{1074}$ raw denominator
before Fraction reduces its value to $0/1$. That raw integer is 1,075 bits and
is not recorded as a canonical-result peak. The zero shortcut skips pi/series,
not decoding/normalization work; this observation is symbolic, not a measurement.

The previous common-denominator argument applies conditionally to dyadic
$Q\le2^{128}$: coefficient factorials divide 15!, both T endpoints' denominators
divide $(QM)^2$, Horner endpoints divide $D^7 15!$ and final endpoints divide
$D^8 17!$. Thus the earlier coarse 42,000-bit direct-arithmetic and 44,000-bit
comparison headroom is consistent with the guards on this subdomain under exact
canonical arithmetic. It is not a new all-binary64 completion claim or proof of
the integer implementation, and is not extended by sampling. Bounded logical
loops do not bound GCD/allocator/native internals or make an interrupted run a
supported return. W0/TB0 remain open.

One binding assumption is important: `configuration` snapshots the cap once,
but `preflight` reads `_SYNTHETIC_SINC_BITS` each time and Fraction is a module
binding. Concurrent mutation/monkeypatching is outside SR0; returned configuration
is not an immutable enforcement/identity token. The existing failure tests
deliberately change those bindings and check rejection/propagation only. This
review does not repair, freeze or authorize runtime reliance on those globals.

**SR8-SR9: exit and evidence.** Every supported early return precedes insertion
of `interval`/`stages`. In the nonzero success call, Python evaluates `pairs`
and the complete stage dictionary before invoking `result.update`; no later
preflight can then turn it into a caught work-limit rejection. If construction
or dict update itself fails unexpectedly, the invocation raises rather than
returning a partial success; no universal local rollback is asserted. Input is
a builtin immutable word, output containers are fresh local objects and there
is no persistence. Returned dictionaries can be changed by callers: a status,
flag or exact-looking interval is not source authority or proof on its own.
The mathematical target, stored-word authenticity, native implementation error,
and composition into motion remain four distinct obligations.

**Exit and next permission.** This conditional paper review is prepared, not
proof/allowance acceptance. No source/test/budget/flag/verdict change, helper
invocation or renewed fixture scope occurred; isolation remains the default.
Next proposed, not approved: design-only NF1 native-error bridge contract,
separating the stored-word real-pi target from the installed wrapper's computed
program, zero/tiny branches, missing primitive evidence and conservative future
comparison semantics. No external/source acquisition or extraction, new import,
execution/native comparison, adapter, integration, error allowance or promotion
would follow from preparing that contract. All broader gates stay open.


#### NF1 Native-Error Bridge Contract Draft (2026-11-04)

The user separately approved the design-only contract proposed in §117;
[review §118][sinc-bridge-review] records this preparation. This is a candidate
evidence contract, not its adoption, an implementation or a numerical comparison.
It uses the already recorded §99/§100 wrapper description, not a new inspection
of installed NumPy, a source extraction or a refreshed environment identity.
The rational helper and all native consumers remain separate and unchanged.

**Claim and owning boundary.** Let q be the exact finite binary64 value decoded
from the submitted P3 word, with $|q|\le1/64$, and let F(q) be the §115 real-pi
normalized-sinc target, including F(0)=1. NF1 would concern the exact stored
output O of the identified wrapper at that same q, not an ideal unrounded angle,
an inferred scalar conversion or a complete motion step. Authenticating the
word and establishing the actual dtype/shape/dispatch remain prerequisites.
Neither a checked trace nor the helper's interval supplies them automatically.

The recorded wrapper is `x=np.asanyarray(x)`;
`y=pi*where(x==0,1.0e-20,x)`; `return sin(y)/y`. Therefore its conditional
real-binary64 stage model is:

$$
z=\begin{cases} e,&x=0,\\q,&x\ne0,\end{cases}\qquad
a=c z,\qquad y=\operatorname{mul}_{\rm native}(c,z),\qquad
s=\operatorname{sin}_{\rm native}(y),\qquad
O=\operatorname{div}_{\rm native}(s,y).
$$

Here c/e denote the exact values of the wrapper's stored pi/tiny constants,
not real pi, decimal-exact $10^{-20}$ or newly selected constants. The model
requires exact conversion x=q and proved selection/promotion to this real
binary64 path; it is not inferred just from the expression or annotations.
No actual bit pattern, selected kernel, FP state or error bound is refreshed
by this draft. Result extraction must preserve the stored value exactly or
be a separately accounted conversion, never a silently discarded NF1 error.
Exact selection is an obligation, not a measured fact: if the actual comparison
treats a nonzero subnormal as zero, the nonzero z=q model is not established.
That selection effect needs its own branch evidence or a stop; do not silently
charge it as multiplication error under the wrong selected operand.

| Obligation | Required Evidence / Missing-Evidence Stop |
| --- | --- |
| NB0: input and identity | Bind exact P3 word, source/epoch/currentness, helper/configuration identity and wrapper/constants/build/loaded-image identities. Historical hashes or copied declarations are not present source authority. |
| NB1: conversion and selection | Establish asanyarray dtype/shape, comparison and where selection/promotion, exact x=q and the actual c/e values. Unsupported scalar/0-D/subclass/complex or converted inputs stop this real-binary64 contract, without changing accepted inputs. |
| NB2: zero and tiny | Both input zero signs take the tiny-constant branch before pi multiplication; nonzero subnormals do not take that branch merely because they are small. A computed zero y is not resubstituted by this expression. Cover underflow/FTZ, finite results and division separation or stop. |
| NB3: multiplication | Bind the actual ordered pi product and a justified absolute error over its reachable branch domain, including signed zero/subnormal/overflow behavior. No generic RN64 assumption from the controlled trace. |
| NB4: sine | Bind the selected scalar/ufunc/libm route and an independent uniform sine-error contract over every reachable y. A NumPy target label, another sine call, a policy goal or sampled maximum does not close it. |
| NB5: division and output | Establish nonzero denominator, finite sine/quotient, division rounding and return representation/extraction. Missing near-zero or conversion evidence stops the output claim. |
| NB6: real target and bridge | Keep c-versus-real-pi error, zero substitution, product/sine/division errors and reference uncertainty separate; use the conditional decomposition below. SR0-SR9 remain assumptions, not an accepted trusted base. |
| NB7: comparison and classification | Bind exact stored O and independent R to the same word/domain; distinguish conditional consistency, inconsistency and unresolved overlap. No inferred allowance, zero-error conclusion from membership, nearest-endpoint fit or automatic certification. |
| NB8: composition and lifetime | Keep P3 argument error, NF2 products/trig/motion, accumulated state error, goal/relative transforms and wire conversions outside this local result. Evidence invalidates on relevant identity/path/FP/domain changes; all five flags and native statuses remain unchanged. |

**Branch-complete conditional error argument.** Define the continuous real
function $H(t)=\int_0^1\cos(ut)\,du$, so H(0)=1 and H(t)=sin(t)/t otherwise.
Thus F(q)=H(pi q), whereas the exact-arithmetic surrogate of this wrapper is
H(cz). They need not be equal, even before native rounding. For an interval
containing the segment between a and y with $|t|\le B$, differentiation under
this bounded integral gives $|H'(t)|\le\min(1/2,B/3)$: use respectively
$|\sin(ut)|\le1$ and $|\sin(ut)|\le u|t|$. This avoids a false singular
sensitivity argument at q=0; it does not bound the native sine implementation.

Suppose separately justified evidence supplies finite nonnegative absolute
bounds $\delta_m,\delta_s,\delta_d$ for $|y-a|$,
$|s-\sin(y)|$ and $|O-s/y|$, and a justified $\eta>0$ with $|y|\ge\eta$.
With $L_B=\min(1/2,B/3)$, exact real algebra then gives

$$
|O-F(q)|\le
\delta_d+\delta_s/\eta+L_B\delta_m+A(q),\qquad
A(q)=|H(cz)-H(\pi q)|.
$$

For nonzero q, a separately justified segment bound $B_c$ between cq and pi q
gives $A(q)\le\min(1/2,B_c/3)|q|\,|c-\pi|$. Real-pi enclosures may bound
the constant discrepancy, but the c identity and all native errors stay separate.
For either input zero word, $z=e$ and the elementary inequality
$|1-\cos(t)|\le t^2/2$ gives $A(0)\le(ce)^2/6$. Do not assign zero artifact
or exact O=1 from F(0)=1. Each segment/domain and each error bound needs its
own evidence; this is a symbolic implication, not chosen numeric allowances.

A reachable nonzero q with y=0 makes the quotient decomposition unavailable;
that branch is unresolved, not a limit evaluation or a second tiny substitution.
An interval crossing zero must be split with complete branch coverage and
proved denominator separation, or remain unresolved. Even when y is separated,
an absolute sine bound divided by a tiny eta can be uninformative. Relative or
correlated bounds could improve it only with their own independent contract.
No subnormal/tiny inputs are excluded by a new cutoff and no FP modes are changed.
Uniform evidence must cover the whole declared domain; a per-word argument is
only per-word. No global positive eta or uniform allowance is inferred here.

**Conservative future comparison, not a checker.** Under the independently
justified reference assumptions let $R=[l,u]$, with $l\le u$, contain F(q), and O be the
exact decoded finite native output. Its possible absolute error is enclosed by

$$
d_{\min}=\max(l-O,0,O-u),\qquad
d_{\max}=\max(|O-l|,|O-u|).
$$

For a separately supported candidate allowance $\varepsilon\ge0$, whole
containment $R\subseteq[O-\varepsilon,O+\varepsilon]$, equivalently
$d_{\max}\le\varepsilon$, supports conditional consistency for this word.
Strict separation $d_{\min}>\varepsilon$ supports inconsistency of the bound
evidence bundle/candidate claim, not attribution to a particular primitive.
Every other case remains unresolved, including boundary overlap when the upper
error bound exceeds epsilon. This is the symmetric-error specialization of
§101's R within O-E rule, not permission to change that protocol or a checker.

O inside R only makes the lower bound zero; it does not generally make the
upper bound zero. An exact unit reference for a zero word similarly does not
predict O or qualify unmeasured zero behavior. Missing NB0-NB6 evidence prevents
either a supported pass or a numerical inconsistency claim; an unsupported
output remains unresolved. Comparisons would use exact/outward arithmetic with
independent uncertainty accounted for, never rounded nearest-endpoint residuals.
Reference refinement requires its own approved method/budget; epsilon cannot
be fitted to a result, widened for containment or inferred from reference width.
No finite comparisons establish a uniform implementation bound by themselves.

**Composition boundary.** If q* is the ideal unrounded P3 argument, a later
qualified P5 argument would add the distinct $|F(q)-F(q^*)|$ term once, using
a justified domain/sensitivity argument. It must not also charge that argument
uncertainty inside the local NF1 error above. Multiplication by speed/duration,
midpoint trig, coordinate arithmetic, inherited pose error, goal transforms and
wire conversion each retain their own ordered obligations. A local consistent
comparison cannot update owner/auditor verdicts, reference bounds or flags.

**Paper acceptance checks and exit.** The contract would require BC0 exact
word/target/output identities; BC1 both zeros and nonzero subnormal branches
without an input cutoff; BC2 separated-denominator/finite error decomposition;
BC3 explicit missing-evidence stops; BC4 containment/separation/overlap and
inside-reference countercases; BC5 once-only composition and invalidation.
These are review requirements, not executed fixtures, a callable schema or
accepted proof. Default disposition remains unresolved native evidence and
isolation; no primitive now has a supported allowance from this draft.

Next proposed, not approved: a bounded read-only NF1 path-evidence gap dossier
using current already-installed files/metadata only. Proposed ceiling: five
rows (wrapper/constants, input/result routing, multiply/divide paths, sine/libm
path, execution-contract evidence gaps), at most 65,536 bytes of inspected
source/metadata text including failed/diagnostic reads, and no persisted raw
artifact. It could refresh identity and locate missing evidence, not prove
actual dispatch/FP state, primitive accuracy or native work. No imports, dynamic
loads, numerical/fixture/native comparison, acquisition/extraction, dependencies,
implementation, integration or allowance/qualification adoption is implied.
Even that read-only investigation needs separate approval; this contract's
design-only scope is exhausted when the documentation checks/commit complete.


#### NF1 Installed-Path Dossier Boundary (2026-11-04)

The user separately approved §118's five-row, at-most-65,536-byte read-only
investigation; [review §119][sinc-path-review] records commands, inspected
windows, file identities, failures and the conservative 35,758-byte charge.
Only already-installed files and static ELF metadata were inspected. No target
import, dynamic load, configuration evaluation, numerical/native comparison,
acquisition, implementation or environment change occurred.

WP0-WP4 cover wrapper/constants, input/result routing, multiply/divide paths,
sine/libm and execution-contract gaps. The wrapper/core/libm/header hashes
match §99; routing/build-file identities are also recorded. The source still
selects the tiny constant before the pi product, with named umath/numeric
imports and a compiled-core where decorator. ELF imports/dependencies and a
libm sine IFUNC are declarations, not an observed selected loop or resolver.
The inspected math header supplies declarations, not uniform sine errors.
Generated build information is not complete compiler/FP evidence. Absent
implementation sources at three checked paths do not establish global absence.

This refreshes only the stated file/source-description evidence. It does not
attest live constants/bindings, dtype/promotion/selection/output routing, loaded
library resolution, current process FP state, build/source correspondence,
uniform primitive errors, domain closure or native work. Historical current
dispatch/loaded-image observations are not renewed. NB0-NB8 therefore remain
unclosed; the conditional bridge is not a supported implementation allowance.
All five flags, native statuses, mathematical helper, source/test APIs, bounds,
old verdicts and isolation default stay unchanged. No runtime/data approval.

The bounded investigation is complete and exhausted. Next proposed, not
approved: design-only NF1 closure-route decision brief comparing continued
native qualification with a separately identified controlled mathematical
candidate. It would specify attainable claims, evidence costs, branch/domain/
work stops, compatibility limits and acceptance gates, not adopt a replacement,
acquire sources, import/run targets, authorize code/fixtures or integrate/promote
a consumer. Physical/task-quality, source/work, teacher assets and ST/board
gates remain open; unused inspection budget is not renewed permission.


#### NF1 Closure-Route Decision Brief (2026-11-04)

The user separately approved §119's design-only comparison;
[review §120][sinc-route-review] records its preparation and verification.
This compares attainable claims, not adopted implementations or qualifications.
No installed-source inspection, target import, numerical/fixture/native run,
acquisition, dependency, code/test change or consumer integration occurs.

**Recommendation for review, not adoption.** Keep every existing path isolated
and every qualification flag false. Prefer a separate controlled-candidate
design contract as the next bounded preparation, rather than presume that more
identity inspection or sampled native agreement will close a uniform error
claim. Continue native qualification only with a separately approved route to
the missing implementation/build/FP/error evidence. Neither route currently
qualifies NF1, source authority, native work, full motion or Task 6/9.

| Decision Aspect | Route N: Qualify Existing Native Sinc | Route C: Separate Controlled Mathematical Candidate |
| --- | --- | --- |
| Local claim | Bound the identified wrapper's exact stored output O against real-pi F(q) at the same authenticated stored q. | Produce a finite binary64 word RN64(F(q)) only when a conditional exact enclosure certifies that one rounding cell. This is a new program/claim, not native parity. |
| Preserved behavior | Keeps asanyarray/selection, stored-pi product, sine/division, tiny substitution, output/promotion and selected native order. | Keeps the mathematical stored-word target, domain and input sign identity; deliberately does not implement the wrapper's stored-pi/tiny program or inferred dtype behavior. |
| Evidence needed | Close NB0-NB8: loaded-path/build correspondence, actual FP contract, reachable branches and uniform primitive errors, plus independent reference/composition evidence. | Close the enclosure and integer cell-checker's correctness/trusted-base/work obligations, domain/word binding and partial-return semantics. No installed sine claim follows. |
| Availability/cost | Matching sources/builds and uniform contracts are not supplied by §119. Obtaining/reviewing them or running path/FP checks needs a new exact scope; availability and effort are unmeasured. | Existing private enclosure can be a producer dependency, not an independent proof/oracle. A separately bounded integer rounding-cell component and its own checks are still absent. Time/RAM/completion are unmeasured. |
| Compatibility | Supported local error would concern that exact version/path/domain, not arbitrary future environments or the whole trajectory. | Output words, output representation and supported/unresolved cases may differ from native behavior. No relabeling of old records, transparent replacement or wire/runtime adoption. |
| Remaining costs | Reference/trusted-base/source authority and NF2-NF7 still need their own evidence even if local sine is qualified. | Integer/Fraction/GCD/allocation and publication evidence remain; native products/trig/motion/goal/relative paths outside this local candidate stay unqualified. No embedded-port or firmware-fit claim. |

Deferring both routes is the current operational default, not a third heuristic
or a permission to collect data. Route C's proposed preference is for isolated
design work, not permission to change what an existing owner computes.

**Concrete candidate for discussion.** Proposed identity:
`controlled_mathematical_sinc_rn64_candidate_v0`, host-only and private. Input
would be a literal synthetic opt-in and one exact builtin nonboolean u64 q word;
the target remains F(0)=1 and otherwise sin(pi q)/(pi q), $|q|\le1/64$.
The proposed finite success value is RN64(F(q)), round-to-nearest/ties-to-even,
not an endpoint approximation, native output, confidence or error allowance.
No API/schema/identity is adopted here.

1. Validate word/type/finite/domain evidence without coercing an unsupported
  input; retain both input zero signs. Missing authenticity remains a separate
  source obligation even when a supplied word is well formed.
2. Obtain the existing private 32/8-term mathematical enclosure under its
  unchanged 65,536-bit limit and SR0-SR9 assumptions. Treat unresolved work/
  domain or unexpected exceptions according to their existing semantics;
  do not extend terms/precision, replace a tiny nonzero q or use native fallback.
3. For either zero word, the mathematical target permits the unit output word
  `0x3ff0000000000000`, retaining the original q word/sign as metadata. This
  does not establish that the unmeasured native wrapper returns that word.
4. For nonzero q, require an ordered finite positive rational interval R. A
  proposed integer-only search would locate endpoint rounding cells in the
  ordered positive binary64 lattice, with at most 64 bisection iterations per
  endpoint. No rational-to-float coercion or unproved endpoint clipping.
5. Accept a proposed finite word w only if the entire closed R lies in its
  exact ties-to-even cell. Endpoint words agreeing is sufficient only after
  the endpoint map and its monotonicity are justified; retain the cell witness
  and recheck whole-interval containment rather than trust a guessed word.
6. If endpoints map differently, a boundary/tie is unresolved, a required
  neighbor is unsupported or any preflight fails, return unresolved with no
  candidate word. No nearest-endpoint choice, precision retry, cap increase,
  silent fallback or partially published result. Exceptions are not universal
  rollback; partial function support does not mean partial output publication.
7. Keep fresh candidate-local identity/input/interval/cell evidence separate
  from owner/auditor records. Every qualification flag remains false; native
  compatibility, source/motion/work and consumer eligibility stay unresolved.
  Nothing is persisted/exported or consumed by existing code.

**Cell and work boundary.** For a positive finite interior word w with two
supported finite neighbors, let their exact values be $v_-,v,v_+$ and
$m_-=(v_-+v)/2$, $m_+=(v+v_+)/2$. Its cell has those midpoint boundaries;
each boundary belongs to w exactly when w's significand is even. For odd w,
both boundaries are open. Consequently, with $R=[l,u]$, equality at either
boundary is allowed only for even w; strict containment works for both parities.
This covers unequal neighbor spacing at an exponent transition, rather than
assuming one symmetric ulp width. Unsupported lattice edge/overflow cases stop.
The mathematical target is positive near one on the declared domain; this
does not authorize clipping an enclosure to a guessed range or skipping checks.

The proposed search bound is a logical limit, not a verified implementation,
instruction count or elapsed-time/RAM guarantee. Constructing exact dyadic
neighbors/midpoints and comparing them with R requires its own pre-operation
and post-result guards. Even if each midpoint is small, cross-products with
large enclosure numerators/denominators can exceed a cap. Such a case must
remain unresolved; successful enclosure construction is not successful rounding.
The existing `_synthetic_rn64` has a 4,096-bit ceiling, not the enclosure's
65,536-bit one. Do not feed arbitrary enclosure endpoints through it, raise
its global limit or refactor it under the guise of reuse. A proposed separate
cell component could use a candidate-local ceiling no greater than 65,536 bits,
subject to its own contract/review. This is not a newly adopted work budget or
an all-binary64 completion guarantee. W0/TB0 and stable-binding assumptions stay.

Sharing the existing enclosure/Fraction stack does not create an independent
reference for this candidate. Future checks would need independently derived
literal cell boundaries/expected words and reviewed mathematical inclusion,
not self-comparison or a call to the same native sine. No such check runs here.

**Compatibility and composition stops.** Route N's conditional error bound
and Route C's proposed rounded mathematical word are different claims. An
enclosure width, candidate rounding cell or finite parity sample cannot be
reinterpreted as a uniform bound for the old wrapper. No native pi/tiny branch
is canceled algebraically or declared exact. Subnormal nonzero q remains a
nonzero exact input even when a proved rounded mathematical result could be one.
At no point does a candidate word authenticate its P3 source or bind a current
event. A different local sinc program would need a separate consumer identity,
once-only P3-argument composition and a reviewed NF2 motion recurrence before
any later integration. Goals, relative transforms, wire and old artifacts keep
their existing meanings; the current owner/reference/auditor remain unchanged.

**Decision and acceptance gates.** DR0 fixes which claim is sought and whether
partial success is acceptable; no total-function guarantee is presumed. DR1
requires exact source/input/target/version identity and independent evidence
classification. DR2 requires the route-specific proof: NB0-NB8 for N, or
enclosure/cell/zero/tie/monotonicity obligations for C. DR3 closes branch/domain
coverage and explicit rejection/exception semantics, without a new tiny cutoff.
DR4 establishes the selected work/guard contract and separately scoped resource
evidence; finite loops and counters alone do not close it. DR5 requires focused
independent fixture controls and applicable source gates in a separately approved
implementation scope. DR6 reviews compatibility, invalidation and once-only
composition without changing old consumers. DR7 requires explicit proof/error/
adoption/integration approval; a design choice or passing prototype does not
promote any flag, native claim, physical clearance or task-quality result.

**Next proposed, not approved:** design-only Route C interval-to-word
certificate contract and conditional work argument. Specify the exact cell
search/verification boundary, finite-neighbor/tie and ambiguity cases, candidate
local preflight/call limits, publication semantics, independent acceptance
controls and old-helper nonmutation. This would not adopt Route C or its
numeric/work limits, implement/call it, acquire sources, run native/fixture
comparisons, integrate a consumer or approve any proof/allowance. This decision
brief's design-only scope is exhausted on documentation verification/commit;
isolation remains the default and all broader gates remain open.

[controlled-arithmetic-review]: ../../REVIEW.md
[controlled-arithmetic-prototype-tests]: ../../tests/test_sim.py
[controlled-arithmetic-dossier-review]: ../../REVIEW.md
[arithmetic-trusted-base-review]: ../../REVIEW.md
[arithmetic-paper-review]: ../../REVIEW.md
[arithmetic-compatibility-review]: ../../REVIEW.md
[controlled-owner-contract-review]: ../../REVIEW.md
[controlled-owner-prototype-review]: ../../REVIEW.md
[controlled-candidate-audit-review]: ../../REVIEW.md
[controlled-candidate-auditor-review]: ../../REVIEW.md
[native-gap-plan-review]: ../../REVIEW.md
[sinc-contract-review]: ../../REVIEW.md
[sinc-prototype-review]: ../../REVIEW.md
[sinc-correctness-review]: ../../REVIEW.md
[sinc-bridge-review]: ../../REVIEW.md
[sinc-path-review]: ../../REVIEW.md
[sinc-route-review]: ../../REVIEW.md
[c1-prototype-source]: ../../sim/diagnostics.py

### Native ToF Cylinder Computation Prerequisites (2026-11-10)

<a id="actual-cylinder-sidetop-calculation-stages-2026-11-10"></a>
<a id="actual-fresh-cylinder-acquisition-pairing-2026-11-10"></a>
<a id="bounded-closed-cylinder-intake-2026-11-10"></a>
<a id="typed-cylinder-history-prehash-guard-2026-11-10"></a>
<a id="explicit-cylinder-recorder-retention-2026-11-10"></a>
<a id="delivered-and-pending-cylinder-correspondence-2026-11-10"></a>
<a id="supplied-word-cylinder-offset-discrepancies-2026-11-10"></a>
<a id="supplied-word-cylinder-projection-expressions-2026-11-10"></a>
<a id="supplied-horizontal-squared-ray-expression-2026-11-10"></a>
<a id="supplied-word-cylinder-discriminant-expression-2026-11-10"></a>
<a id="supplied-word-cylinder-root-squared-consistency-2026-11-10"></a>
<a id="supplied-word-cylinder-side-numerator-expressions-2026-11-10"></a>
<a id="supplied-word-cylinder-side-division-residuals-2026-11-10"></a>
<a id="supplied-word-cylinder-side-altitude-expression-2026-11-10"></a>
<a id="supplied-word-cylinder-side-maskcandidate-correspondence-2026-11-10"></a>
<a id="supplied-word-cylinder-side-minimum-correspondence-2026-11-10"></a>
<a id="supplied-word-cylinder-top-offset-expression-2026-11-10"></a>
<a id="guarded-supplied-word-cylinder-top-division-2026-11-10"></a>
<a id="supplied-word-cylinder-top-relative-expression-2026-11-10"></a>
<a id="independent-supplied-word-cylinder-cap-square-expressions-2026-11-10"></a>
<a id="supplied-word-cylinder-cap-maskcandidate-correspondence-2026-11-10"></a>
<a id="supplied-word-cylinder-cap-minimum-correspondence-2026-11-10"></a>
<a id="captured-cylinder-stage-chain-word-correspondence-2026-11-10"></a>
<a id="matched-retained-cylinder-selection-reports-2026-11-10"></a>
<a id="matched-retained-cylinder-offset-residuals-2026-11-10"></a>
<a id="matched-retained-cylinder-projection-residuals-2026-11-10"></a>

The complete topic continues in the [cylinder topic chapter][native-tof-cylinder-topic].

[native-tof-cylinder-topic]: 07-data-and-distillation-design-05.md#native-tof-cylinder-computation-prerequisites-2026-11-10

#### Native ToF Return-Postprocessing Prerequisites (2026-11-11)

The cold [native sampler][c1-motion-source] accepts an append-only
`postprocessing_source=None` keyword. Its default branch retains the original
noise addition, dropout mask, clip/select and float32 cast. Opt-in requires an
empty builtin dictionary, native capture, actual owner and supported finite
sampling profile; its receiver must differ from native/selection/wall/cylinder/
direction receivers before geometry, RNG or optional clock work.

The separate `micro-classifier/native-tof-postprocessing-source/1` packet copies
the actual existing normal and dropout draws, pre-noise/noisy ranges, both
validity masks, clipped/selected ranges and stored float32 ranges. Nine8x8 arrays
contain384 float64 values,64 float32 values and128 booleans; four declared profile
fields retain max range, noise standard deviation, dropout and mount height.
No extra draw, replay, replacement noise law or changed sensor operation is
introduced. Captured operands, intermediate words and masks are observations,
not a probabilistic or physical model, error allowance or corrected geometry.

Cold capture alone is not acquisition, recorder history or delivered/pending
publication qualification. Raw unsupported/nonfinite source
stays unknown for qualification; matching words do not adopt numerical, coverage,
clock, one-use, physical or command-admission evidence. All eight qualification/
permission/training flags remain false. [The checkpoint][native-tof-postprocessing-review]
retains bounded controls, actual failed checks and next source prerequisite.

#### Fresh Native ToF Postprocessing Acquisition (2026-11-11)

The append-only `capture_native_tof_postprocessing=False` step flag requires
literal booleans and native capture. Actual-owner/native inputs and the same
finite postprocessing profile are checked before state mutation or clock work.
Sensor routing passes a distinct cold receiver only to an actual fresh sample;
the separate `micro-classifier/native-tof-postprocessing-acquisition/1` cache
joins that packet to the exact native cache, original RNG identities and nominal
acquisition/delivery ticks. Its stored float32 words and final validity mask
correspond to the native pending sample, not an already delivered observation.
Default, source-only, held and reset paths clear the new cache; rejected preflight
preserves prior state. Existing noise/dropout draws, cadence and optional two
clock reads are unchanged. Legacy cold/postprocessing capture remains supported,
without broadening the mounted-only wall/cylinder/direction interfaces.

This is source ownership only, not typed intake, recorder retention, delivery or
numerical/noise-law/coverage/physical/clock/one-use/admission qualification. All
eight flags remain false; [the acquisition checkpoint][native-tof-postprocessing-acquisition-review]
retains finite controls, measured check outcomes and outstanding evidence.

#### Closed Native ToF Postprocessing Intake (2026-11-11)

The separate [offline intake][c1-prototype-source] validates the closed acquisition,
trace and input layouts before copying six finite float64 8x8 arrays as canonical
hex words, two literal boolean masks and the stored float32 uint32 words. Two
metadata snapshots bracket two existing native intakes; original/closing cache,
RNG identities, profile, pose, inputs and detached outgoing words must match.
Pre-noise ranges join the native geometry output, and stored words/final mask join
the same pending native sample. Legacy and noisy profiles remain observations.
Unsupported/nonfinite raw source raises the unknown-path rejection, not corrected
values or an adopted noise distribution. No replay, extra draws, clock, digest,
recorder retention or numerical evaluation is introduced.

This closed correspondence is not internal noise-addition/dropout/clip arithmetic
proof, probability, numerical/geometry/coverage/source/physical/clock/one-use or
admission qualification. All eight flags remain false. Typed bounded history and
recorder/delivery joins are still separate prerequisites; [the intake checkpoint][native-tof-postprocessing-intake-review]
retains actual failed checks, finite accounting and next action.

#### Typed Native ToF Postprocessing History (2026-11-12)

The [offline validator][c1-prototype-source] accepts at most eight ordered builtin
list records with exactly `source_epoch`, `tick`, `delivery_tick`, `postprocessing`.
The native history must be independently prevalidated before this companion guard.
Each record requires one exact epoch/acquisition/delivery pairing, the closed
21-key trace, unchanged profile and pre-noise/stored-word/final-mask correspondence.
Six 64-word arrays use finite canonical float hex strings of at most 32 characters;
two masks require literal booleans, and 64 uint32 storage words must have finite
IEEE binary32 encoding. Signed observation words are preserved. Maximum work is
3,072 float-word decodes, 512 stored-word checks and 1,024 mask elements for eight
records, not a measured CPU/RAM bound. The validator does not replay, draw noise,
hash, read, clock or retain records.

Legacy/noisy profiles remain observations; internal noise/dropout/clip arithmetic,
probability, geometry/coverage/error/source/physical/clock/one-use and admission
qualification remain unproved. All eight flags are false. Recorder retention and
delivered/pending composition remain separate next prerequisites. [Checkpoint §310][native-tof-postprocessing-history-review]
retains checks, accounting and the paused-WIP-to-completion history.

#### Native ToF Postprocessing Recorder Retention (2026-11-12)

The separate [offline recorder][c1-prototype-source] accepts append-only literal
`include_postprocessing=False`. Opt-in retains detached four-key postprocessing
records aligned with at most eight retained native acquisition ticks. Exact
repeats deduplicate; changed repeats reject. Oldest native trimming removes the
corresponding companion records, while acquisitions retained without this option
leave explicit companion gaps rather than synthesized traces.

Native archive words are independently prevalidated before companion guards and
digests whenever postprocessing is requested or prior companion records exist.
Original/closing intake, native and companion cache identities, RNG identities,
producer profile/pose/input, recorder ownership/history identities and detached
outgoing words must agree before staged histories replace the originals.
Default performs no postprocessing intake. No sensor replay, extra RNG draw,
read/step/reset, clock or delivery publication is added.

This is retained source correspondence, not internal noise/dropout/clip arithmetic,
probability, numerical/geometry/coverage/error/source/physical/clock/one-use or
admission qualification. All eight flags remain false; raw unsupported/nonfinite
source rejects as unknown. Retained matching and delivered/pending publication
remain separate prerequisites. [Checkpoint §312][native-tof-postprocessing-retention-review]
retains finite controls, failures and accounting.

#### Bounded Retained ToF Postprocessing Matching (2026-11-12)

The [offline matcher][c1-prototype-source] requires an independently prevalidated
native source and typed postprocessing history. It scans at most eight builtin
list records for one exact typed epoch/acquisition/delivery identity match;
missing or ambiguous pairs reject. The selected record is detached, including
its nested input metadata. This helper neither replaces native/companion guards
nor samples, hashes, reads, retains or publishes source records.

This is a retained identity/copy prerequisite only. Delivery publication and
numerical/noise-law/geometry/coverage/error/source/physical/clock/one-use/admission
qualification are separate; all eight flags remain false.
[Checkpoint §313][native-tof-postprocessing-match-review] retains finite checks.

#### Closed ToF Postprocessing Delivery Publication (2026-11-12)

The [offline delivery snapshot][c1-prototype-source] appends literal
`include_postprocessing=False`. Opt-in publishes detached `postprocessing` and,
only with pending-source inclusion, `pending_postprocessing` records joined to
exact typed native epoch/acquisition/delivery identities. Stored float32 words
and final validity masks match the corresponding delivered or pending samples.

Native archive-word prevalidation precedes original/ownership/copy/closing
companion guards and digests, including after closing frame/queue callbacks.
Original/closing histories, detached outputs and existing producer/RNG/profile/
pose/input/frame/pending-queue ownership checks must agree. Missing, unsupported,
nonfinite or changed records return explicit unknown with no partial publication.
Default output keys/operations are unchanged; no intake, replay or RNG draw is
introduced. These are source observations, not arithmetic/noise-law/numerical/
geometry/coverage/error/physical/clock/one-use/admission qualification; all eight
flags remain false. [Checkpoint §314][native-tof-postprocessing-delivery-review]
retains finite controls and evidence limits.

#### Supplied-Word ToF Noise-Addition Discrepancies (2026-11-12)

The standalone [offline helper][c1-prototype-source] compares 64 observed noisy
words against exact unrounded sums of supplied finite pre-noise/draw words.
It preserves signed/raw words and reports nonfinite observations as unknown;
canonical builtin-word and bounded rational preflight reject unsupported inputs.
No noise distribution, primitive rounding/error bound or qualification is
adopted; all eight flags remain false. Retained report joins are separate.
[Checkpoint §315][native-tof-noise-addition-review] retains bounds and failures.

#### Matched ToF Noise-Addition Reports (2026-11-12)

The [offline snapshot][c1-prototype-source] appends literal default-off
`include_postprocessing_noise_addition_residuals`, requiring postprocessing
inclusion. It reports supplied-word sum discrepancies for retained delivered
and optional pending traces only after original/closing native/companion,
history identity, word, report-content and detached output-binding checks.
Prevalidation also follows closing frame/queue callbacks. Default keys are
unchanged; malformed or changed evidence remains explicit unknown without
partial publication. No noise/rounding/error law or qualification is adopted;
all eight flags remain false. [Checkpoint §317][native-tof-noise-addition-match-review]
retains bounds and controls.

#### Supplied-Word ToF Dropout Mask Correspondence (2026-11-12)

The standalone [offline helper][c1-prototype-source] compares supplied dropout
draw/threshold words and literal before/after masks for64 cells. It retains
signed words, reports mismatch/unknown counts, and keeps nonfinite draw
observations unknown. Existing profile threshold validation is retained;
no finite draw interval or probability law is adopted. Canonical builtin-word/
mask preflight rejects unsupported metadata; all eight flags remain false.
This is not comparator/native/physical qualification. Retained report joins
remain separate; [checkpoint §318][native-tof-dropout-review] retains bounds.

#### Matched ToF Dropout Reports (2026-11-12)

The [offline snapshot][c1-prototype-source] appends literal default-off
`include_postprocessing_dropout_diagnostics`, requiring postprocessing inclusion.
Original/closing native/companion prevalidation, history identities, words,
report content and detached output bindings precede delivered/pending report
publication. Default keys remain unchanged and changed/unsupported evidence
returns explicit unknown without partial output. No draw interval, probability
law, threshold or qualification is adopted; all eight flags remain false.
[Checkpoint §319][native-tof-dropout-match-review] retains bounds and controls.

#### Supplied-Word ToF Clip/Selection Correspondence (2026-11-12)

The standalone [offline helper][c1-prototype-source] compares supplied noisy,
clipped and selected words against declared clamp values and the observed
clipped-or-zero selection input. It does not correct upstream operands or
predict native zero-sign words. Nonfinite source remains unknown; canonical
builtin-word/literal-mask and existing max-range preflight rejects unsupported
metadata. Signed-word ties remain unresolved, all eight flags false; no native
primitive/rounding/error/noise law is adopted. Retained joins are separate.
[Checkpoint §320][native-tof-clip-selection-review] retains bounds and controls.

#### Matched Native ToF Clip/Selection Reports (2026-11-12)

Literal default-off clip/select report inclusion requires postprocessing.
Delivered/optional pending reports use matched retained operands, original/
closing native/companion guards and source/history/report/output joins before
publication. Changed or unsupported joins publish explicit unknown without
partial fields. Detached reports preserve observed operands, raw nonfinite
unknowns and zero-word ties; all eight flags remain false. No rounding, noise
law, primitive/error bound or qualification follows from value/word matching.
[Checkpoint §321][native-tof-clip-selection-match-review] records controls.

#### Supplied-Word ToF Selected/Storage Residuals (2026-11-12)

The standalone [offline helper][c1-prototype-source] decodes supplied finite
builtin uint32 storage words using the existing sampling view and reports exact
stored-minus-selected residuals. Canonical selected +/-inf remains unknown;
unsupported words/metadata reject explicitly. Numerical and decoded-word
equality remain separate; signed-zero ties are not normalized. No native cast
word is predicted or rounding/error law adopted; all eight flags remain false.
Retained joins are separate. [Checkpoint §323][native-tof-storage-review]
records the bounded controls and evidence limits.

#### Matched Native ToF Selected/Storage Reports (2026-11-12)

Literal default-off storage-report inclusion requires postprocessing.
Delivered/optional pending reports use original/closing native/companion guards,
retained source/history/word/mask/report/output joins and detached supplied
residuals before publication. Changed or unsupported joins publish explicit
unknown without partial fields. Numerical and decoded-word equality stay
separate; no cast law/error bound or qualification is adopted, all eight flags
false. [Checkpoint §324][native-tof-storage-match-review] records the controls.

#### Cold Native Goal Computation Source (2026-11-12)

The actual [goal producer][c1-motion-source] accepts default-off
`goal_source=None`: an empty builtin cold receiver, actual owner/profile,
supported finite input/dtype preflight before state/RNG work. It copies actual
world-goal dtype, used position/delta/cosine/sine, native goal and stored float32
pair without changing the legacy goal cache or calculations. Used operands may
include existing odometry draws; no noise/trig/cast law is adopted. Computed raw
nonfinite values stay explicit unknown, all eight flags false. Acquisition,
typed intake/retention/delivery and source/numerical/physical/clock/admission
qualification are separate. [Checkpoint §325][native-goal-cold-source-review]
retains bounds, actual fixture/source failures and necessary repairs.

#### Native Goal Computation Acquisition Pairing (2026-11-12)

Literal default-off `capture_native_goal_computation=False` prevalidates actual
owner/profile and supported inputs before step state/RNG/clock work. One actual
history production supplies a separate private acquisition cache retaining
legacy native-source identity, both actual RNG identities, cold computation,
tick and nominal odometry delivery tick. Reset/default steps clear the cache;
goal acquisition is independent of fresh/held ToF. Existing public outputs,
native goal cache/calculations and draws remain unchanged. Raw computed
nonfinite source stays unknown, all eight flags false. No noise/trig/cast law,
clock/one-use or source/numerical/physical/admission qualification follows;
closed intake, retention and delivered/pending joins are separate.
[Checkpoint §326][native-goal-acquisition-review] retains the bounded controls.

#### Closed Native Goal Computation Intake (2026-11-12)

The acquisition carrier retains actual true-pose words, a fixed Config snapshot
and Scenario identity separately from noisy used operands. The offline sampler
closes original/closing owner/cache/native/RNG/profile/pose/input/tick/delivery/
ego/history/stored-word bindings before one detached supported packet. Existing
C1 tick encoding and <=8 queue/history/nominal-latency budgets bound work, not
clocks or physical error. Inferred world dtype and exact integer/canonical
float64 words remain distinct; stored float32 words are observed uint32 views.
Unsupported/changed/nonfinite source rejects explicitly without partial output,
retaining raw unknown source. No replay, noise/trig/cast law or qualification;
all eight flags false. Typed history, recorder retention and publication remain
separate. [Checkpoint §327][native-goal-intake-review] records the controls.

#### Typed Bounded Native Goal Computation History (2026-11-12)

Four-key records retain the complete closed intake packet. Current and <=8
saved packets receive independent closed type/finite-word validation before
epoch/profile/world-input/order joins. Exact signed/unsigned world integers,
inferred dtype, canonical float64 signs and finite builtin uint32 storage words
are preserved; native/true-pose/yaw bindings and all eight false flags remain
required. Existing Config validation requires all fields, not silent defaults.
Unsupported/nonfinite data and unresolved word mismatches reject explicitly.
No noise/trig/cast/error law or source/physical/clock/execution/admission
qualification follows. Recorder retention and publication remain separate.
[Checkpoint §329][native-goal-history-review] records work limits and controls.

#### Default-Off Native Goal Recorder Retention (2026-11-12)

The [offline recorder][c1-prototype-source] has independent literal default-off
goal inclusion: disabled work is a no-op, enabled work needs a current bound C1
producer. Retained raw words are prevalidated before intake/digests; original/
closing owner/cache/native/RNG/profile/pose/input/current-frame/history/stored/
source-file joins precede changing <=8 detached records. Exact repeats dedup,
changed repeats reject; native-tick trimming preserves skipped gaps, including
expired-row trimming on a repeat. No replay/draw/trig/clock/geometry, publication
or numerical/noise/physical/source/clock/execution/admission qualification;
all eight flags false. [Checkpoint §330][native-goal-retention-review] records
the finite controls and necessary fixture/closing-guard repairs.

#### Exact Retained Native Goal Matching (2026-11-12)

A four-key typed target's epoch/tick/delivery and two finite builtin uint32
goal words are validated independently before <=8 typed retained records.
One unique exact epoch/tick/delivery match and exact storage words permit a
detached record; unsupported/missing/ambiguous/nonfinite/word-tie targets
reject explicitly. No numerical equality normalization, source/geometry/
error/clock/execution/physical/admission qualification or publication follows;
all eight flags false. [Checkpoint §331][native-goal-match-review] records
bounded controls; closed delivered/pending publication remains separate.

#### Closed Default-Off Native Goal Delivery (2026-11-12)

Independent literal default-off inclusion publishes only a delivered-goal
diagnostic joined to its actual encoded State frame and <=8 independently
validated retained records. Exact first-two float32 goal words are matched
without zero normalization; the unchanged three-component State encoder
binds the full planar frame. Original/closing owner/cache/native/RNG/profile/
pose/input/history/dynamics/source-file/output joins close before publication,
including owner closure after the last producer observation. Missing,
unsupported, changed or nonfinite correspondence returns explicit unknown
without partial epoch/tick/frame/goal fields.
Current tuple/State/frame and dynamics dictionary layouts prevalidate before
indexing or consumption. The final closed native-source intake follows the
last producer observation and optional report calculation, so late in-place
source/pose mutations fail closed without another intake or broader catches.
Retention uses the same final-observation-before-source-closure order.

The frozen C1 profile has zero odometry latency; this delivered-only method
does not create a positive-latency/pending domain. Pending publication remains
separate and unsupported here. <=2 intakes/views/matches/file checks, <=12
digests and <=8 retained records; no replay/draw/trig/clock/geometry/actuation
or source/numerical/error/physical/clock/execution/one-use/admission adoption.
All eight flags false. [Checkpoint §332][native-goal-delivery-review] preserves
actual failures, repairs, controls and limits.

#### Supplied-Word Native Goal Delta Discrepancies (2026-11-12)

Two supplied inferred float64/int64/uint64 world words minus finite canonical
used-position words define the exact unrounded comparison to observed delta.
Validated integer operands retain their exact <=64-bit value without generic
float conversion. The residual includes any conversion discrepancy; it is not
a NumPy coercion/rounding law or an error bound. Canonical observed infinity
retains raw words and finite exact difference with explicit unknown residual;
unsupported/NaN operands reject without partial output or mutation. Zero
signs remain raw supplied words, not inferred signs or normalized ties.
<=2 entries/6 word decodes/4 binary operations/6 value conversions and the
existing <=4096-bit arithmetic cap. All eight flags false; no source/geometry/
noise/numerical/physical/clock/execution/one-use/admission adoption.
[Checkpoint §333][native-goal-delta-review] preserves controls and failures;
retained matching/report publication remains separate.

#### Matched Retained Native Goal Delta Reports (2026-11-13)

Literal default-off `include_goal_delta_residuals` requires goal computation
inclusion. Independently typed retained world/used-position/delta words feed
the supplied-word helper; detached reports carry exact source epoch/tick/
delivery labels. Original/closing source/operand/report/output and recorder
ownership joins must close before publication. Changed or unsupported joins
return explicit unknown without partial frame/goal/report fields.
<=2 reports/4 entries/12 word decodes/12 rational values/8 binary operations,
with the existing intake/view/match/file/digest caps unchanged. No replay/
extra RNG/trig/clock/geometry work, positive-latency/pending domain or rounding/
noise/error bound is adopted; all eight qualification flags remain false.
[Checkpoint §336][native-goal-review] records the completed gate and the
final-source/malformed-owner repairs, preserving [the WIP pause][native-goal-wip].

#### Supplied-Word Native Goal Expression Residuals (2026-11-13)

The supplied consumed coefficient pair `(c,s)` and observed delta `(dx,dy)`
define exact unrounded `c*dx+s*dy` and `-s*dx+c*dy` comparisons to final native
components. Do not recompute delta, infer yaw trigonometry, normalize coefficients
or adopt a noise/rounding/geometry/error law. Canonical finite inputs prevalidate;
observed infinity retains raw words with unknown residual, unsupported/NaN
inputs reject without mutation. Signed words are not normalized.
<=2 entries/6 decodes/6 rational values/8 binary operations and the existing
<=4096-bit arithmetic cap; all eight flags false, no qualification follows.
[Checkpoint §337][native-goal-expression-review] records controls and limits.

#### Matched Retained Native Goal Expression Reports (2026-11-13)

Independent literal default-off expression inclusion requires goal computation.
Exact retained consumed coefficients/delta/native components and source epoch/
tick/delivery labels feed detached reports. Original/closing source/operand/
report/output joins close before publication; unsupported or changed joins
return explicit unknown without partial fields. Final source intake follows
both reports and the last observation. <=2 reports/family, unchanged source/
digest caps; combined delta/expression <=24 values/24 binary operations.
No trig/noise/rounding/geometry/error adoption, all eight flags false.
[Checkpoint §339][native-goal-expression-match-review] records actual controls.

#### Supplied Native and Stored Goal-Word Correspondence (2026-11-13)

Two canonical supplied native components and finite builtin uint32 stored
words define decoded observed binary32-minus-native residuals, not casting
predictions. Numerical equality and decoded-word equality are independent;
signed-zero ties remain unresolved. Native infinity retains raw words with
unknown residual/equalities; unsupported/NaN/nonfinite storage rejects without
mutation under the closed-history word preflight. <=2 entries/decodes/views,
4 rational values/2 subtractions and the existing <=4096-bit cap; all eight
flags false, no law/error/geometry/source/execution/physical/admission adoption.
[Checkpoint §340][native-goal-storage-review] preserves controls and limits.

[native-goal-storage-review]: ../../REVIEW.md#340-supplied-native-and-stored-goal-word-correspondence-2026-11-13
[native-goal-expression-match-review]: ../../REVIEW.md#339-matched-retained-native-goal-expression-reports-2026-11-13
[native-goal-expression-review]: ../../REVIEW.md#337-supplied-word-native-goal-expression-residuals-2026-11-13
[native-goal-review]: ../../REVIEW.md#336-current-state-review-and-native-goal-boundary-repairs-2026-11-13
[native-goal-wip]: ../../REVIEW.md#335-matched-native-goal-delta-reports-wip-and-pause-2026-11-12
[native-goal-delta-review]: ../../REVIEW.md#333-supplied-word-native-goal-delta-discrepancies-2026-11-12
[native-goal-delivery-review]: ../../REVIEW.md#332-closed-default-off-native-goal-delivery-2026-11-12
[c1-motion-source]: ../../sim/rover.py
[native-goal-match-review]: ../../REVIEW.md#331-exact-retained-native-goal-matching-2026-11-12
[native-goal-retention-review]: ../review/326-330.md#330-default-off-native-goal-recorder-retention-2026-11-12
[native-goal-history-review]: ../review/326-330.md#329-typed-bounded-native-goal-computation-history-2026-11-12
[native-goal-intake-review]: ../review/326-330.md#327-closed-native-goal-computation-intake-2026-11-12
[native-goal-acquisition-review]: ../review/326-330.md#326-native-goal-computation-acquisition-pairing-2026-11-12
[native-tof-noise-addition-review]: ../review/311-315.md#315-supplied-word-native-tof-noise-addition-discrepancies-2026-11-12
[native-tof-noise-addition-match-review]: ../review/316-320.md#317-matched-native-tof-noise-addition-reports-2026-11-12
[native-tof-dropout-review]: ../review/316-320.md#318-supplied-word-native-tof-dropout-mask-correspondence-2026-11-12
[native-tof-dropout-match-review]: ../review/316-320.md#319-matched-native-tof-dropout-reports-2026-11-12
[native-tof-clip-selection-review]: ../review/316-320.md#320-supplied-word-native-tof-clipselection-correspondence-2026-11-12
[native-tof-clip-selection-match-review]: ../review/321-325.md#321-matched-native-tof-clipselection-reports-2026-11-12
[native-tof-storage-review]: ../review/321-325.md#323-supplied-word-native-tof-selectedstorage-residuals-2026-11-12
[native-tof-storage-match-review]: ../review/321-325.md#324-matched-native-tof-selectedstorage-reports-2026-11-12
[native-goal-cold-source-review]: ../review/321-325.md#325-cold-native-goal-computation-source-2026-11-12
[native-tof-postprocessing-acquisition-review]: ../review/306-310.md#307-fresh-native-tof-postprocessing-acquisition-pairing-2026-11-11
[native-tof-postprocessing-delivery-review]: ../review/311-315.md#314-closed-native-tof-postprocessing-delivery-publication-2026-11-12
[native-tof-postprocessing-history-review]: ../review/306-310.md#310-typed-bounded-native-tof-postprocessing-history-2026-11-11
[native-tof-postprocessing-intake-review]: ../review/306-310.md#309-bounded-closed-native-tof-postprocessing-intake-2026-11-11
[native-tof-postprocessing-match-review]: ../review/311-315.md#313-bounded-retained-native-tof-postprocessing-matching-2026-11-12
[native-tof-postprocessing-retention-review]: ../review/311-315.md#312-bounded-native-tof-postprocessing-recorder-retention-2026-11-12
[native-tof-postprocessing-review]: ../review/306-310.md#306-cold-native-tof-return-postprocessing-capture-2026-11-11
