#### NF1 Interval-to-Word Certificate Contract (2026-11-04)

The user separately approved §120's design-only contract/work preparation;
[review §121][sinc-cell-review] records scope and checks. This refines the
proposed `controlled_mathematical_sinc_rn64_candidate_v0`, not Route C adoption,
an implemented API, an accepted proof or an error/resource allowance. No helper
call, word evaluation, fixture/native run, installed inspection or acquisition
occurs. Existing producers, helpers, flags, verdicts and consumers stay unchanged.

**Local hypothesis and trust boundary.** A first-true search over ordered exact
upper cell midpoints, followed by endpoint and whole-interval verification,
could yield a sound partial word result under the existing enclosure assumptions.
It need not round arbitrary enclosure fractions with the old 4,096-bit helper.
The discriminating paper checks are monotonicity/tie ownership, a strictly
shrinking search interval, explicit edge rejection and complete guarded work
accounting. A counterexample to any of these invalidates the candidate contract,
not the old native program. The following argument is conditional, not accepted
numerical certification or native parity.

A pure interval component establishes only cell containment; the separate word
entry must bind it to F(q)'s direct enclosure. Synthetic component controls
confer no such binding. Its two endpoints are fixed canonical integer-pair
tuples with exact builtin nonboolean integer components, positive denominators
and bounded sizes; invalid pairs are rejected before arithmetic or coercion.

**Entry and enclosure binding.** Proposed private word entry requires literal
synthetic opt-in and an exact builtin nonboolean u64 q word, retaining both zero
signs. Invalid opt-in raises ValueError; malformed/nonfinite/out-of-domain words
produce unresolved evidence, not coercion. At most one existing §116 enclosure
call is permitted per entry, including zero; no retries, increased terms/caps or
native fallback. A word entry may enter the interval component at most once;
zero takes no such entry. The enclosure's strict domain $|q|\le1/64$,
32/8-term configuration and 65,536-bit limit remain unchanged. Consume only
that direct local call's exact canonical interval and matching input/sign/
configuration metadata, not a supplied log, claimed certificate or old owner
record. Missing or inconsistent binding stops. Stable Fraction/global bindings
and SR0-SR9 remain assumptions, not facts
established by a configuration snapshot. Canonical-pair validation and interval
ordering are guarded before arithmetic; a success status alone is insufficient.

Both input zeros require the exact mathematical interval [1,1] and permit the
existing unit word `0x3ff0000000000000`; keep the original q/sign in evidence.
This branch has no cell search and claims nothing about native tiny substitution.
A nonzero q, even subnormal, remains nonzero. Its enclosure must be ordered,
strictly positive and have bounded canonical integer pairs; never clip it to a
guessed near-one range. Unsupported evidence produces no candidate word.

**Exact lattice and cells.** Let M be the largest positive finite binary64 word,
`0x7fefffffffffffff`. Eligible output words satisfy $1\le w<M$; M itself is a
search sentinel, not an eligible result. Neighbor words $w-1,w,w+1$ must decode
as exact finite nonnegative dyadics; zero is supported only as a neighbor value.
No infinity, negative word or zero output cell is supplied. This deliberately
partial support is not a new cutoff on q or a claim that the target underflows.
An integer-only local decoder uses fraction bits f and exponent bits e:

$$
D(0)=0,\qquad
D(w)=\begin{cases}
f/2^{1074},&e=0,\\
(2^{52}+f)2^{e-1075},&1\le e\le2046.
\end{cases}
$$

Guard shifts and numerator/denominator construction before allocation; do not
call old round/decoder/operation/trace, owner, auditor or native helpers. This is
a proposed separate decoder, not a refactor or a claim of independent evidence.
For eligible w define $L_w=(D(w-1)+D(w))/2$ and
$U_w=(D(w)+D(w+1))/2$. A boundary belongs to w exactly when its significand is
even, equivalently its word's low bit is zero. Thus both boundaries are closed
for even w and open for odd w. Subnormal/normal and exponent transitions retain
actual unequal adjacent spacings; no symmetric-ulp shortcut is permitted.

**Endpoint search and final certificate.** For a positive exact endpoint x use
the predicate $P_x(w)=(x<U_w)\lor(x=U_w\land w\text{ even})$. Exact decoded values
and their upper midpoints strictly increase with eligible word order. Therefore
P is monotone: it cannot revert to false; equality assigns the shared midpoint
to the even of two adjacent words. Seek its first true eligible word with
integer indices lo=1 and hi=M. M is never decoded/tested as a candidate, but
may be decoded as the finite upper neighbor of M-1. While lo<hi, choose
$j=\lfloor(lo+hi)/2\rfloor$; true replaces hi by j, false
replaces lo by j+1. Maintain that eligible indices below lo are false and those
at/above hi are true. If lo=M, no supported cell was found: unresolved.

Each endpoint result must also pass its full lower and upper cell inequalities;
the first true word can still fail the lower boundary at the unsupported low
edge. Run at most one search for each of l,u. Different words mean unresolved.
For a common w, freshly reconstruct both neighbors/midpoints and verify all of
the closed enclosure $[l,u]$: $l>L_w$ and $u<U_w$, allowing equality separately
at either boundary only for even w. An odd word cannot own a singleton midpoint
tie; its adjacent even word can when that full cell is supported. An interval
crossing a boundary rejects, regardless of its midpoint or width. Recheck
parity, eligibility and finite neighbor identity; endpoint agreement does not
replace this witness. Each full-cell reconstruction decodes its three dyadics
once and reuses the central value for both midpoints. Each predicate/boundary
test uses one guarded three-way rational comparison, reusing that result for
strictness and equality/parity rather than recomputing comparison products.

Conditional soundness follows from F(q) belonging to the direct enclosure and
that entire enclosure belonging to this one exact rounding cell. Monotonicity
and tie ownership identify the endpoint words, not the truth of enclosure
membership. The cell checker must not claim to prove F(q) inclusion or native
accuracy. Ambiguity, unsupported edges, missing evidence or a guard failure
returns unresolved; no guessed word, fitted tolerance or adaptive refinement.

**Candidate-local guards and conditional work argument.** Propose a separate
cell ceiling C=65,536 bits, never higher than the enclosure limit; it is not
adopted here. Do not change either old 4,096/65,536-bit global limit. Canonical
integer pairs have positive denominators and components at most C bits. Before
each left shift, product, sum, denominator doubling or comparison cross-product,
use conservative bit-length bounds: shift adds its count, product adds operand
lengths, sum adds one to their maximum. Compare two guarded products directly,
without an unnecessary unbounded difference. Midpoint addition and halving must
guard every unreduced intermediate before Fraction construction/GCD, then check
canonical results. No cancellation or later reduction excuses an oversized raw
operation. Guards may conservatively reject valid mathematical values.

Word/index/parity operations stay bounded by the fixed u64 lattice; endpoint
pair checks, canonicalization, interval-order comparison and publication are
also part of the work contract, not invisible free setup. No unbounded input
sequence, decimal parsing, rational-to-float conversion, full search transcript,
cache or persistence is proposed. A candidate-local ceiling snapshot does not
by itself qualify Python allocation/GCD, arbitrary mutable bindings or work.

For the search, hi-lo starts below $2^{63}$ and each iteration reduces it to at
most its floor-half. Under exact bounded-index execution at most 63 iterations
suffice; retain §120's conservative proposed cap of 64 per endpoint, checked
before every attempt. Exhaustion stops unresolved rather than extending it.
The paper cell upper ledger, including a final reconstruction and a separately
counted enclosure dependency, is:

| Work Item | Proposed Per-Entry Maximum | Included Boundary |
| --- | --- | --- |
| Existing enclosure entry | 1 | Zero or nonzero; its separate SR/work obligations remain. |
| Endpoint search iterations | 128 | Two searches, at most 64 attempts each. |
| Exact dyadic word decodes | 265 | Two per search attempt, three per endpoint verification, three final. |
| Exact midpoint constructions | 134 | One per attempt, two per endpoint verification, two final. |
| Rational comparisons | 135 | One per attempt, two per endpoint verification, two final, one interval-order check. |

These are conditional upper-level call counts, not measured counters, primitive
instruction/constructor counts, a live-memory bound or an elapsed-time deadline.
Each midpoint/compare includes its guarded raw operations and canonicalization;
each decode includes its guarded shifts. Metadata/type/sign/size/GCD checks and
result construction must be accounted separately, not misreported as covered by
135 comparisons. The enclosure's existing paper ledger is not folded into this
one or rerun. W0/TB0, runtime/library correspondence and resource qualification
stay open. Passing the enclosure does not guarantee that cell cross-products
fit C, that allocation terminates successfully or that a nonzero word publishes.

**Publication and compatibility.** Proposed successful local evidence contains
the distinct candidate identity, q/sign and direct enclosure/configuration
binding, candidate word and neighbor words/exact dyadics, exact L/U, tie closure,
whole-interval comparison outcomes and bounded attempted-work metadata. Build
fresh owned canonical pairs/containers, never alias helper/owner records. Publish
one complete result only after all checks; do not mutate old evidence. An
unresolved result omits the output word and cell certificate; bounded reason,
input identity and attempted-work metadata may remain. Counters do not imply
successful publication, and unexpected/allocation/interruption errors propagate:
this is not universal rollback or a guarantee of any return.

All five flags remain false: training_approved, real_input_qualified,
free_space_qualified, numerically_certified and producer_parity_qualified.
Native sinc/source/motion/work and consumer eligibility remain unresolved even
on a candidate-word return. No error allowance, old-record retagging, owner/
auditor/reference/log adapter, wire/CLI/runtime adoption or embedded-fit claim.
P3 argument error, NF2 recurrence, goals and relative transforms remain separate.

**Independent acceptance controls.** Before any proposed implementation is
accepted, require these ten obligations:

- CW0: exact q/direct-enclosure binding and separate pure-cell claim.
- CW1: integer decoder and finite-neighbor order.
- CW2: monotone first-true search and shrinking-index invariants.
- CW3: both tie parities and unequal transition spacing.
- CW4: closed whole-interval containment and edge rejection.
- CW5: zero and nonzero-subnormal separation.
- CW6: raw/preflight/postcanonical guards and search exhaustion.
- CW7: owned publication, attempted-work and exception semantics.
- CW8: independent expected-cell controls, not a shared truth oracle.
- CW9: preservation/non-adoption and resource/trusted-base limits.

No obligation closes merely because it appears in this contract.
Future controls must construct exact literal dyadics/midpoints independently
from bit-field mathematics and specify
expected words before candidate evaluation, not use candidate helpers, native
sine or the same enclosure as an independent truth oracle. Mocked intervals can
test cell mechanics, never establish their inclusion of F(q).

**Next proposed, not approved:** a bounded isolated private prototype/tests in
the existing diagnostics/test files, not a consumer or accepted Route C. Proposed
per complete focused invocation: twelve reused q-literal positions, at most 24
word entries/24 enclosure calls; sixteen independent pure-cell controls with at
most 32 direct cell entries. Including nested word calls, at most 56 total cell
entries. No owner/event/trace/query/reference/log/native call or new scene. Any
implementation approval must explicitly include these fixture/call limits and
normal source gates; it does not accept a proof, numeric/work allowance, native
compatibility or qualification. No such code, fixture derivation/evaluation or
gate run occurs here. Isolation remains the default; this design-only scope is
exhausted after documentation verification and a local checkpoint.


#### NF1 Isolated Word Candidate Prototype (2026-11-05)

The user separately approved §121's bounded private implementation/tests and
normal source gates; [review §122][sinc-word-review] records evidence and limits.
This implements a partial candidate, not adoption of Route C, an accepted proof,
native accuracy/error/work allowance or consumer qualification.

Additive private `_certify_synthetic_sinc_cell` in [diagnostics][c1-prototype-source]
checks fixed canonical integer-pair endpoints against one exact ties-to-even
cell. Separate `_candidate_synthetic_sinc_word` binds at most one direct call to
the unchanged enclosure and, for nonzero q, at most one cell entry. Both zero
signs require [1,1] and return the mathematical unit word without cell search.
Malformed/nonfinite/out-of-domain words, inconsistent direct metadata, unsupported
cell edges/straddles and work limits stay unresolved; unexpected allocation errors
propagate. No old function/global cap, owner, input, wire or artifact is changed.

The new cell-only constants default to 65,536 bits and 64 endpoint steps. Strict
configuration validation prevents expansion beyond those prototype limits;
mid-call changes reject. Raw shifts/products/sums/doubling/cross-products are
guarded before Fraction construction, with canonical checks afterward. Exact
upper-midpoint first-true searches assign ties to even words. M is excluded as
a candidate but remains a finite upper neighbor of M-1. Endpoint full-cell checks
and fresh whole-interval verification reuse three dyadic values and three-way
comparisons, retaining neighbor/boundary/parity/order evidence. No float/native
fallback, clipping, precision retry, cache, persistence or full search transcript.

Fresh owned successful evidence is distinct from unresolved results, which omit
the word/cell certificate. Five qualification flags remain false; source/native
sinc/motion/work and consumer eligibility remain unresolved on every return.
Direct declared binding does not authenticate a producer source or independently
prove the shared enclosure. Logical/attempt counters do not measure primitive
work, totality, time, live memory or firmware fit. Native motion/goals/relative
transforms, W0/TB0 and SR/CW proof obligations remain open; `1bb89fe` stays.

Two tests reuse twelve q-literal positions and sixteen independently derived
pure-cell controls. Per complete new-entry matrix they make 24 word attempts,
17 enclosure entries, 32 direct and six nested cell entries (38 total), below
the approved 24/24/32/56 limits. Zero/sign, even/odd and exponent-transition
ties, subnormal/normal and extreme finite edges, straddles, canonical/type
rejection, preflight/change/exhaustion, owned results and allocation propagation
are checked. Poisoned old/native/owner paths and source AST checks guard isolation.
Independent cell expectations establish cell mechanics, not F(q) truth or native
parity. Every old source/test top-level AST node is retained in order.

Focused 28-case matrices and the required root gate pass; the fresh source gate
is 2,165 passes plus the known transformer xfail and 71 existing warnings. Lint,
changed-file format and editor diagnostics pass; the failed initial format check
is retained in review. No additional opt-in native/sanitizer/Arm or board gate,
new scene, collection, labels, dependency, teacher experiment or integration.

Next proposed, not approved: design-only conditional correctness/publication/work
review of the two private helpers against CW0-CW9, including trusted-base and
attempt-counter limits. No new import/fixture/run, source change, native inspection,
consumer/adapter integration or proof/error/work allowance/qualification adoption.
The bounded prototype scope is exhausted; isolation remains the default.


#### NF1 Word Candidate Correctness and Work Review (2026-11-05)

The user separately approved §122's design-only paper review;
[review §123][sinc-word-proof-review] records evidence and verification. Current
source/test identities match §122 despite an editor change notification. No
source/test change, target import, fixture/native run or proof/error/work allowance
acceptance occurs. The default remains isolation and all five flags remain false.

**Conditional outcome.** Under exact builtin integer operations, faithful
Fraction/copy semantics, stable serialized module bindings, terminating
allocation/GCD and the unchanged SR0-SR9 enclosure assumptions, the local
cell algorithm has no identified algebraic mismatch with its partial contract.
That statement is a paper outcome, not accepted proof, actual native/library
correspondence, a total function, source authority or representative task quality.
The word result additionally requires the direct bound enclosure to contain F(q).
Cell containment alone cannot establish that premise or the old native output.

| Obligation | Conditional Derivation From Current Code | Residual Stop |
| --- | --- | --- |
| CW0 | Word/type/finite/domain checks and strict q/sign/ratio/configuration/branch matching precede a cell call; zero requires exact [1,1]. | Direct local calls and matching metadata do not authenticate source or immutable bindings. |
| CW1 | Finite word decoding uses exact significand and power; subnormal spacing and actual adjacent words are retained. | Integer/Fraction implementation correspondence is assumed; unsupported zero/M output cells reject. |
| CW2 | Increasing upper midpoints make the first-true predicate monotone; lo/hi updates strictly shrink the index distance. | Allocation/errors or guard exhaustion can stop before a word; no all-input completion claim. |
| CW3 | Equality in the upper predicate belongs only to an even low bit; final lower/upper equality uses the same parity. | A tie at an unsupported neighboring output cell is unresolved, not clipped. |
| CW4 | Each endpoint is checked against both boundaries; agreeing words are followed by a fresh closed whole-interval check. | A small width, agreeing sampled points or enclosure status does not replace the witness. |
| CW5 | Both zero signs decode to exact zero and retain q/sign; nonzero subnormals follow the enclosure/cell route. | Mathematical unit output is not a statement about native tiny substitution. |
| CW6 | Conservative raw shift/product/sum/doubling/cross-product guards precede construction, with canonical postchecks and fixed step limits. | Conservative rejection is allowed; GCD/allocation/binding behavior remains a trusted-base obligation. |
| CW7 | Word/certificate fields are attached only on ordinary successful return; mutable records are freshly constructed/copied. | Unexpected exceptions propagate; partial dictionary construction is not universal rollback. |
| CW8 | Existing pure-cell controls have independent dyadic/expected-word derivations and corrupted metadata controls. | Those finite historical checks are not complete domain proof, independent F(q) truth or renewed run permission. |
| CW9 | Existing caps, functions, tests, owner/reference/default/wire meanings remain unchanged; all flags/status limits are explicit. | Native motion/goals/relative transforms, W0/TB0 and later adoption/consumer gates remain open. |

**Search and cells.** For exact ordered finite dyadics D(w), adjacent upper
midpoints increase strictly. For endpoint x, false means x is above that upper
boundary or is an odd-word equality; true means it belongs at/below the upper
boundary with the tie assigned to even. Eligible indices below lo remain false,
and those at/above hi remain true. The virtual M sentinel is not evaluated as a
candidate, but numeric word M is decoded as M-1's finite upper neighbor. Each
iteration halves the remaining distance; the stated 64-step cap is conservative
relative to the conditional 63-step index argument.

The first true result can still be outside the lower boundary at the unsupported
low edge, so full endpoint checks are necessary. Final containment of [l,u]
uses both exact boundaries, including equality only for even w. Thus every real
value in that closed interval has the same nearest/ties-even word, provided
the finite-neighbor/cell mathematics and faithful operations hold. Applying this
to F(q) additionally requires its enclosure inclusion; no native error follows.

**Guard and counter ledger.** Cell configuration accepts builtin integer limits
only, at most 65,536 bits/64 steps. Preflight compares current globals with the
entry snapshot; this rejects observed changes, not arbitrary concurrency or
mutation of Fraction/function bindings. Shift bounds use significand length plus
nonnegative shift and denominator length; midpoint guards cover both raw products,
their sum and doubled denominator; comparison guards cover both products without
forming a difference. Canonical validation cannot excuse an oversized raw result.

The conservative cell-only attempt ledger remains 128 search iterations,
265 dyadic decodes, 134 midpoints and 135 three-way rational comparisons. At most
401 counted rational constructions follow from two endpoint constructors plus
the decode/midpoint calls. This is a paper upper-level ledger, not measurement.
Strict pair/type/size checks, canonical comparisons, integer comparisons,
preflight, copies, metadata and result building remain separate work.

`search_iterations` increments before decoding; `dyadic_decodes` increments
before finite-word/shift rejection; midpoint/compare counts increment after
preflight but before raw evaluation; rational construction counts increment
before Fraction and its postcheck. These count attempted stages, not published
results. `max_result_bits` records only canonical results that passed checks,
not unreduced, rejected, concurrently live or total allocated storage. Successful
enclosure construction need not imply that later cell products fit the cap.
No counter/loop argument certifies elapsed time, memory fit or native work.

The word wrapper has separate fixed-u64 setup: q shifts construct components
no larger than 1,075 bits before reduction, plus domain comparison and copying.
It does not call the cell preflight for that setup. This is a distinct logical
size bound, not an extension of the configurable cell guard/counter coverage.
Its enclosure and cell entry counters increment before calls and do not count
all inner work. The zero branch omits cell configuration/search; no cell-limit
or native-return guarantee is inferred from a zero success.

**Publication and trusted base.** Unresolved ordinary returns omit the output
word/certificate while retaining permitted input/work metadata. The successful
cell certificate retains exact neighbor/boundary/interval/parity/order evidence;
the word wrapper copies it and its direct interval. Fresh mutable containers are
distinct; immutable int/tuple sharing is harmless under their assumed semantics.
Allocation/interruption/unexpected exceptions can prevent any return, including
during final copying/publication. Nothing is persisted or consumed by old code.

Word binding checks validate the recorded shape/types/values, not arbitrary
untrusted helper substitution. In particular, the wrapper relies on the stable
local cell function's returned status/certificate rather than running a second
independent checker; copied evidence and matching identities are not a proof of
live code correspondence. Fraction/GCD/deepcopy and installed native/runtime
paths stay unqualified. This review neither widens a helper contract nor repairs
source, promotes a flag or accepts Route C.

**Next proposed, not approved:** design-only candidate certificate verification
and trusted-base closure plan. Specify independently checked publication content,
producer/checker separation, exact claims, rejection/binding/work boundaries and
acceptance gates before implementation, imports/runs, source acquisition, native
inspection, consumer integration or proof/error/work allowance adoption. No
checker or new fixture scope follows from this completed paper review.


#### NF1 Certificate Verification and Trusted-Base Closure Plan (2026-11-05)

The user separately approved §123's design-only plan preparation;
[review §124][sinc-certificate-plan-review] records the scope and checks. This
is a concrete proposed verification boundary, not a checker implementation,
accepted schema/proof/allowance, Route C adoption or permission for new runs.
Current source/tests and five false flags remain unchanged; isolation stays default.

**Four separate claims.** Proposed V-cell verifies that supplied exact interval
content lies wholly in a supplied eligible mathematical rounding cell. V-bind
checks declared q/sign/ratio/target/configuration/branch and interval correspondence
between separately captured records. V-target additionally needs independent
accepted evidence that F(q) is in that interval. V-live additionally needs
source/build/runtime/binding correspondence, with work/resource qualification
kept distinct. Passing V-cell cannot imply V-bind, V-target or V-live; matching
hashes/metadata cannot imply source authority or mathematical inclusion.

**Proposed pure-cell boundary.** First propose an isolated private content checker
in the existing diagnostics/test files, not a call from the word wrapper, owner,
auditor, reference, wire, CLI or runtime. It accepts only a literal synthetic opt-in
and the current eight-field cell certificate, not an arbitrary producer object or
an enclosing word result. The permitted keys are `word`, `interval`, `neighbors`,
`boundaries`, `closed_ties`, `lower_order`, `upper_order` and
`whole_interval_contained`. The schema is defined by that exact eight-key set.

Require an exact builtin dict/key set and bounded builtin string keys before
lookup/copy, fixed tuple lengths, nonboolean builtin word/order integers and exact
boolean tie/containment fields. Validate seven canonical rational pairs: two
interval endpoints, three neighbor values, two boundaries. Components must be
builtin nonboolean integers with positive denominators and at most 65,536 bits
before canonical/GCD work. Reject noncanonical pairs, extra/missing fields,
numeric aliases, unexpected object types or unsupported configuration; never
execute user conversion/copy hooks, parse decimal/JSON or persist an input.
Already allocated caller input and concurrent mutation are not bounded by entry
guards. Serialize ownership, validate and copy fixed fields into a fresh bounded
snapshot before verification; no temporal/source-authenticity claim follows.

Eligible w remains 1 through M-1. Independently decode w-1,w,w+1 from bit-field
mathematics, retaining zero as a neighbor and M as a finite upper neighbor. Do
not call the producer decoder/search/cell/enclosure, old RN64 helper or native
sine. Compare supplied neighbor words and canonical values to those reconstructed
values; recompute both adjacent midpoints with guarded exact arithmetic. Verify
the supplied boundary pairs, parity boolean and order integers against these
recomputations. Require positive ordered [l,u] and complete lower/upper inclusion,
with both ties closed only for even w. `whole_interval_contained=True` must match
recomputed containment. Producer success status is outside this interface and
is never an acceptance predicate.

The zero word-candidate certificate is a different three-field shape and is
outside this first pure-cell interface. A future V-bind plan must separately
check both signed q zeros, exact [1,1], unit word and zero branch; nonzero
subnormal q may never be rewritten to zero. Rejecting that shape here does not
invalidate the old mathematical zero branch or qualify its native substitute.

**Independent arithmetic and work.** Proposed default is separate guarded
integer-pair decoding/midpoint/cross-product logic, not producer helper reuse.
Canonicalization/GCD remains an explicit trusted-base dependency; this plan
selects no installed library/source qualification. Existing independent test
dyadic utilities may construct expected fixture content, not serve as the checker
or as independent F(q) truth. No endpoint search or enclosure retry is needed.
The paper checking ledger is three decodes, two midpoint recomputations and
three three-way rational comparisons (interval order and two containment orders),
plus seven input canonical-pair checks and separately accounted neighbor/boundary/
metadata equality, parity, snapshot and publication work. Raw operations must
fit the separate checker ceiling before evaluation; later reduction cannot
excuse an oversized intermediate. Propose an internal checker limit defaulting
to 65,536 bits, accepting only exact builtin nonboolean integers from 1 through
65,536. Snapshot/recheck before guarded operations; invalid/increased limits or
observed changes stop unresolved. No search/precision-retry knob is needed.
Do not raise the old 4,096/65,536-bit limits.
Counts and passed canonical sizes are not primitive/native/time/RAM bounds.

**Proposed report, not a producer retag.** Build fresh diagnostic-only content
evidence after complete verification, with a distinct identity such as
`synthetic_cell_certificate_content_check_v0`, independent recomputed interval/
neighbors/boundaries/parity/orders and separate attempted-work metadata. Reject
or unresolved reports omit a verified certificate; unexpected allocation/
interruption errors propagate. Do not mutate incoming/old records or adopt an
output word for any consumer. All five flags stay false; native/source/motion/
work/consumer status limits stay unresolved even on verified content. No global
proof or live-code attestation follows from a new report identity.

**Closure sequence and acceptance gates.** None of these gates is accepted or
closed by this plan:

| Gate | Required Evidence or Decision | Stop Until Present |
| --- | --- | --- |
| VC0 | Explicitly approve the isolated pure-cell interface, exact key/shape/type/size rules and bounded test/run scope. | No implementation or fixture execution from design approval. |
| VC1 | Independent decoder/midpoint/cross-product/canonical arguments and whole-interval/tie/edge derivation. | No shared producer success/status/expected word as truth oracle. |
| VC2 | Fixed snapshot, raw/precanonical guards, canonical postchecks and fresh publication/exception controls. | No arbitrary-object hooks, unlimited allocation, concurrency or universal rollback claim. |
| VC3 | Reused independent pure-cell controls plus tampered word/neighbor/boundary/parity/order/interval/flag/type cases. | Reject inconsistent content; finite cases do not prove a whole domain. |
| VC4 | Historical AST/caps/flags/default/wire preservation and focused/default gates under separate approval. | No owner/word-wrapper/adapter/consumer integration or qualification promotion. |
| VC5 | Separately captured complete enclosure evidence and exact V-bind contract, including zero and interval correspondence. | Current word metadata is not a complete independently checked enclosure transcript. |
| VC6 | Independent SR inclusion/correctness obligations, accepted mathematical target/domain and trusted arithmetic premises. | V-cell/V-bind cannot establish F(q) inclusion or native error. |
| VC7 | Exact source/build/runtime/live-binding correspondence for every trusted component, with change/requalification policy. | Source hashes, frozen records or private names do not establish live authority. |
| VC8 | Separately approved primitive-work/allocation/GCD/resource evidence and downstream claim/consumer decision. | Logical counters, host tests or conditional paper proof do not certify time/RAM/board fit. |

Proposed CT0-CT5 tracking rows remain unresolved and do not rename or close the
older W0/TB0 obligations. All acquisition/import/run/implementation actions below
require separate bounded approval; preparing this table approves none of them.

| Row / Exact Claim | Assumed Semantics and Available Evidence | Missing Closure / Change Trigger |
| --- | --- | --- |
| CT0 / integer arithmetic and guards | Exact builtin shifts/products/sums/comparisons/bit lengths; §123's conditional derivation and current AST identity, not live primitive evidence. | Accepted arithmetic/guard argument plus implementation correspondence and separate work evidence; reconsider on interpreter/build/operation/cap change. |
| CT1 / canonicalization and GCD | Canonical signed numerator/positive denominator with faithful terminating reduction; current Fraction dependency is assumed, not qualified. | Canonical/GCD correctness, exact library/build/live mapping and separately bounded allocation/work; reconsider on reduction implementation/runtime/domain/cap change. |
| CT2 / snapshot and publication | Builtin shape/type checks, serialized ownership, fresh fixed-field copying and exception propagation; historical ownership cases are finite controls. | Explicit ownership/no-hook argument and permitted runtime/publication/resource evidence, not atomicity or general rollback; reconsider on copy/container/concurrency/entry-boundary change. |
| CT3 / independent cell content | Independent bit-field/neighbor/midpoint/whole-interval logic; eight current fields are known, but no checker exists. | Separately approved checker plus independent derivation/tamper controls and preserved isolation; shared integer/GCD runtime still depends on CT0/CT1, reconsider on schema/algorithm/helper reuse change. |
| CT4 / mathematical inclusion and binding | F(q) at stored q, signed-zero separation and unchanged SR enclosure premises; direct statuses/metadata and cell cases do not establish inclusion. | Complete V-bind evidence and independently accepted SR inclusion/target argument, not native parity; reconsider on target/domain/q decoding/series/configuration/enclosure change. |
| CT5 / live source/runtime authority and resources | Current source/test file identities match §122, not loaded-code/build/library or caller/source authority. | Versioned source/build/live-binding chain, requalification policy and separate W0/resource evidence under approved scope; reconsider on interpreter/library/build/binding/input/consumer change. |

No installed inspection, source-package acquisition, numerical study, library
replacement or resource threshold is approved here. Closing one component on
paper would still not close other rows, V-target/V-live or any consumer gate.

**Proposed default and next permission.** Complete V-cell first while V-bind,
V-target, V-live and resource claims remain unresolved. Next proposed, not approved:
the isolated private pure-cell checker/tests only, sixteen reused control positions
and at most 32 checker attempts per complete focused invocation, plus normal
source gates. Construct expected records independently; no new word/enclosure/
producer-cell calls in the new tests. Existing default regression gates separately
execute their unchanged historical controls; this needs explicit approval, not
automatic renewal of exhausted §122 scopes. No new q position/scene/data, binding/
target checker, native run/inspection, acquisition, consumer integration or proof/
allowance/qualification adoption. Implementation approval must include those
limits; the present design-only scope ends with document checks and a local commit.


#### NF1 Isolated Cell Certificate Checker (2026-11-05)

The user separately approved §124's isolated checker/tests, sixteen reused
positions/at most 32 attempts per complete focused invocation and normal source
gates. [Review §125][sinc-cell-check-review] records implementation, executions
and limits. This is bounded synthetic content verification, not V-bind/V-target/
V-live implementation, accepted proof/allowance, Route C adoption or integration.

Additive private `_check_synthetic_cell_certificate` in
[diagnostics][c1-prototype-source] accepts exactly the eight certificate fields,
literal opt-in, builtin nonboolean word/order integers, exact boolean claims and
fixed builtin dict/string/tuple shapes. It checks seven capped canonical pairs,
rejects input hooks/subclasses and creates a fresh fixed-field snapshot. Separate
`_SYNTHETIC_CELL_CHECK_BITS` defaults to 65,536; invalid/increased or observed
changed limits stop unresolved. Existing caps and all old functions stay intact.
Caller input allocation/serialized ownership and faithful runtime bindings remain
assumptions, not qualified concurrency, allocation or source evidence.

Independent integer-pair arithmetic reconstructs three neighbors using bit-field
division, two guarded exact midpoints and three three-way comparisons. Supplied
neighbor values, boundaries, parity/order/containment claims must match independent
recomputations and complete positive closed-interval inclusion. M is excluded as
an output but remains the finite upper neighbor of M-1; both supported tie parities,
subnormal/normal spacing and unsupported edges are preserved. No search, producer/
word/enclosure/old-RN64/native call, float conversion, retry, cache or persistence.
Fraction canonicalization/GCD is a shared assumed runtime dependency, not producer
helper reuse or closed CT0/CT1 evidence. The three-field zero word certificate
is outside this eight-field content interface; no q/enclosure binding is checked.

Successful diagnostic reports have distinct content-check identity, freshly
recomputed certificate/work containers and false qualification flags. Ordinary
unresolved reports omit a verified certificate; unexpected allocation/interruption
errors propagate. No producer status is consumed. Whole-interval inclusion here
concerns supplied contents, not independent F(q) truth or live-source authority.
Attempt counts include seven input canonical checks, three decodes, two midpoints,
three comparisons and at most twelve Fraction constructions. Accepted canonical
bit sizes do not measure raw/rejected/live allocation, primitive work, time or RAM.

One test reuses sixteen positions with independently derived contents and expected
outcomes, exactly two checker attempts each. A complete matrix gives 12 verified,
17 unresolved and three exceptions; new tests call no producer/cell/word/enclosure,
owner/reference/native path. Tampered values/boundaries/parity/order/flags, numeric
aliases, noncanonical/oversized inputs, hostile dict hooks, cap changes/exhaustion,
fresh outputs and MemoryError propagation are controlled. No new q, scene or data.
All previous source/test top-level AST nodes remain identical and ordered.

Focused checks and the required root gate pass: 2,181 tests plus the known
transformer xfail/71 existing warnings. Scoped lint/format/editor/Pylance syntax
and post-format old-AST checks pass; the initial format failure and VS Code test
discovery mismatch are preserved in review. No extra opt-in native/sanitizer/Arm,
GPU/teacher/board or installed-source requalification; no dependencies/collection/
labels/training/consumer use. Native motion/goals/relative transforms, source/work,
SR/VC/CT/W0/TB0 obligations and Task 6/9 remain unresolved; `1bb89fe` stays.

Next proposed, not approved: design-only conditional correctness/publication/work
review of the new checker against VC1-VC4/CT0-CT3. No new imports/fixtures/runs,
source changes, binding/target/live checker, native inspection/acquisition,
consumer integration or proof/error/work allowance/qualification promotion.
The separately approved implementation scope is exhausted; isolation stays default.


#### NF1 Cell Checker Correctness and Work Review (2026-11-05)

The user separately approved §125's design-only checker review;
[review §126][sinc-checker-paper-review] records evidence and checks. Current
source/test identities still match §125. No code change, target import, new
fixture/helper/native run, acquisition or accepted proof/error/work allowance.
Five flags remain false; V-bind/V-target/V-live and consumer use stay absent.

**Conditional conclusion.** No local algebraic mismatch is identified under
faithful exact builtin operations and Fraction canonicalization, stable module/
builtin bindings, serialized caller ownership through snapshot and successful
allocation/reduction. A verified ordinary return then describes an eligible
word whose exact cell contains the entire supplied positive closed interval.
This is not accepted proof, live correspondence, a total-return guarantee,
independent F(q) inclusion, native parity or task/physical qualification.

The following CCR0-CCR9 are paper obligations, not adopted gates or new flags:

| Obligation / Existing Boundary | Conditional Argument From Current Code | Unclosed Premise or Stop |
| --- | --- | --- |
| CCR0 / VC1, CT0, CT3 | Eight distinct builtin string keys from an eight-key allowed set imply exact coverage; strict builtin shape/type checks exclude numeric aliases and conversion/copy hooks. | Caller allocation, builtin correspondence and serialized key/value stability are assumed, not bounded or authenticated. |
| CCR1 / VC2, CT1 | Seven pairs have positive denominators, builtin integer components, raw cap checks and equality to canonical Fraction output before semantic acceptance. | Faithful terminating GCD/canonicalization and allocation are not qualified by input types or pair equality alone. |
| CCR2 / VC1, CT0, CT3 | Division by the significand radix reconstructs finite bit fields; actual adjacent words preserve zero/subnormal/normal/exponent-transition values. | Fixed word arithmetic is exact by premise; zero/M are neighbors only, never eligible outputs. |
| CCR3 / VC1, CT0 | Midpoints use the two guarded cross-products, their sum and doubled positive denominator, with canonical postchecks. | Raw conservative rejection is permitted; reduction cannot excuse an oversized intermediate. |
| CCR4 / VC1, CT0, CT3 | Two guarded comparison products give each three-way order; ordered positive endpoints and both exact cell inequalities imply whole-interval inclusion. | Supplied interval truth is not enclosure truth; a failed bound/order stops unresolved. |
| CCR5 / VC1, CT3 | Actual neighbor/boundary values, even parity, both order fields and true containment marker must match reconstruction. | Producer status and three-field zero word records are outside this interface; no clipping or tie reassignment to unsupported cells. |
| CCR6 / VC2, CT0 | Separate cap validation/rechecks and raw/precanonical/postcanonical guards stop detected limit changes or oversized rational stages. | No immutable global/runtime, concurrency or full setup/resource contract is established. |
| CCR7 / VC2, CT2 | Fixed-field snapshot and fresh recomputed result/work dictionaries have no shared mutable caller container under the stated ownership premise. | Some scalar fields are reread from the caller; snapshot is not an atomic read or enforcement of ownership. |
| CCR8 / VC2, CT0-CT2 | Attempt counters follow their actual guard/constructor boundaries; only complete ordinary success attaches a certificate. | Max canonical bits omits rejected/raw/live storage; unexpected errors can prevent any return, including publication. |
| CCR9 / VC3-VC4, CT3 | Historical independent/tamper controls and unchanged old ASTs/caps/flags support their bounded cases and isolation. | Finite controls, hashes and private names do not close CT0-CT3, proof/totality or downstream qualification. |

**Decoder and containment derivation.** Eligible w lies between 1 and M-1;
w-1,w,w+1 therefore lie between zero and the largest positive finite word M.
For exponent e and remainder h from division by $2^{52}$, the nonzero-exponent
branch reconstructs $(2^{52}+h)2^{e-1075}$; the zero-exponent branch gives
$h2^{-1074}$. Fraction reduction preserves those exact dyadics by assumption.
Actual adjacent values, rather than an assumed uniform spacing, determine both
midpoints. Neighbor word M is allowed only as M-1's finite upper neighbor.

Positive denominators make the ordering of the two comparison products the exact
rational order. The interval-order check and lower positivity precede neighbor
and boundary verification. For reconstructed boundaries L,U, require l>L and
u<U, with equality at either boundary allowed only for even w. Every x in [l,u]
then meets the same cell inequalities. Equality at an odd boundary or an
unsupported neighboring cell is unresolved, never a guessed output word. Matching
claimed order/parity/true fields verifies internal content consistency only.

**Guard partition.** Raw input-pair shapes/types/sizes are checked for all seven
pairs before snapshot and before Fraction work. Canonical equality checks use
the fixed immutable pairs retained from that input; semantic interval reads use
the snapshot. Under serialized ownership those agree; the code does not establish
an atomic snapshot or prevent mutation between the earlier scalar type checks
and later scalar rereads. No source/temporal identity or adversarial runtime claim.

Rational preflight covers argument component sizes, shifted significand and power
denominator, midpoint product/sum/doubling bounds and both comparison products.
Canonical outputs are type/sign/size checked after construction. Sum bounds add
one to the maximum product bound, and doubled-denominator bounds include the
additional shift. Conservative overestimates can reject mathematically valid
small reduced values; this is an allowed partial stop, not a precision fallback.

Word eligibility comparisons, neighbor/index arithmetic, radix/divmod/exponent
setup, scalar parity/order checks, key sets, containers, snapshot and publication
are separate from rational preflight. After eligibility, word-lattice values are
bounded by the fixed u64 domain and radix constants, not by a reduced checker cap.
Already allocated arbitrary caller integers/strings/containers and the work of
early rejection are not an input-allocation or constant-time bound. A cap snapshot
and later equality checks do not make Fraction/builtin bindings immutable or close
CT0/CT1/CT2/W0/TB0, installed correspondence or primitive/native work.

**Attempt and publication ledger.** Per entry the conditional upper-level ledger
remains seven canonical-pair checks, three dyadic decodes, two midpoints, three
three-way rational comparisons and twelve Fraction constructions. Input checking
accounts for seven constructions, neighbor decoding three, midpoint reduction two;
key/type/equality/parity/snapshot/result work is not hidden inside three comparisons.
There is no search, enclosure call or precision retry to count.

Canonical-pair counts increment before the rational preflight; Fraction counts
increment after that preflight but before construction/postcheck. Decode counts
increment before divmod or its later guard. Midpoint/compare counts increment
after their raw preflight and before raw evaluation. `max_result_bits` records
only canonical outputs passing postchecks, not raw/rejected/concurrently live
or aggregate allocations. These are conditional attempted-stage counts, not
measured primitive instructions, native work, elapsed time or memory fit.

Successful ordinary publication follows semantic verification and a final
configuration preflight. Fresh mutable dictionaries are independent; sharing
immutable builtin int/tuple values is harmless under faithful semantics. Ordinary
CheckStop/unresolved paths attach no verified certificate. Unexpected/allocation/
interruption errors propagate, including during final result construction, so
neither complete return nor universal rollback is guaranteed. No old report,
producer status, owner/wire/runtime record or qualification flag is mutated.

**Outcome and next permission.** VC1-VC4/CT0-CT3 remain unaccepted; the conditional
arguments and §125's finite tests are evidence to review, not closure. Old caps,
helpers, `1bb89fe`, native motion/goals/relative transforms and Task 6/9 stay.
Next proposed, not approved: design-only V-bind evidence/interface contract for
separately captured candidate and complete enclosure records. Specify exact
q/sign/ratio/configuration/branch/interval correspondence, separate zero handling,
bounded rejection/work/publication and independent evidence requirements. No
binding/target/live checker, import/new fixture/run/source edit, native inspection/
acquisition, integration or proof/error/work allowance/qualification promotion.
Isolation remains default; this review ends with document checks and a local commit.


#### NF1 V-bind Evidence and Interface Contract (2026-11-05)

The user separately approved §126's design-only V-bind contract preparation;
[review §127][sinc-bind-contract-review] records checks and limits. This is a
proposal, not record capture, a checker, accepted evidence or implementation
permission. Source/tests and all old helpers/caps/flags remain unchanged. No
target import, fixture/helper/native run, installed inspection or acquisition.

**Claim and proposed default.** V-bind means exact declared correspondence
between a separately specified stored q word, a complete candidate record and
a separately captured complete enclosure record. Matching records do not prove
that either came from a particular invocation, that F(q) lies in the interval,
that the word is its rounding result or that a native program agrees. V-cell
content, V-target inclusion, V-live authority and actual resource work remain
distinct. Keep all five flags false and every consumer ineligible.

Propose a private, explicitly synthetic-only three-input boundary: expected
q_word, candidate_record and enclosure_record. Do not obtain expected q from
either record, call any producer/enclosure/cell/checker/owner/native helper,
or capture a record inside verification. Status/reason/identity strings select
an exact schema/profile only; they are not truth or origin evidence. Reject
unresolved/partial/unknown-version records rather than completing them from
defaults, copied binding metadata or a successful cell status. No existing
helper/signature or record is changed by this proposal.

**Complete input profile.** Use exact builtin dicts, bounded builtin string
keys (at most 32 characters), exact key sets, bounded literal selector strings,
fixed tuples, one exact two-item builtin endpoint list and nonboolean builtin
integers/booleans as applicable. No coercion, arbitrary-object traversal,
conversion/copy hooks, JSON/decimal parsing, pickle,
deepcopy, import, persistence or cache. Serialize caller ownership until raw
validation and a fresh fixed-field snapshot finish; this is a premise, not an
atomic-read or thread-safety guarantee. Validate all supplied pair shapes/types/
positive denominators/raw sizes before canonicalization or snapshot publication.

| Record | Exact Required Successful Shape | Binding Rule / Missing Evidence |
| --- | --- | --- |
| Candidate | Current 23 root fields: identity, allowed_use, status, reason, target, q_word; five false flags; native_sinc_status, motion_status, source_status, native_work_status, consumer_status; work, sign, q_ratio, configuration, interval, certificate, enclosure_binding. | Require the current candidate/profile literals and ineligible/unresolved limits; no invented root branch or complete enclosure payload. |
| Complete enclosure | Current 20 root fields: allowed_use, status, reason, target, domain_ratio, configuration, q_word; five false flags; native_sinc_status, motion_status; work, q_ratio, sign, branch, interval, stages. | No identity/source/consumer fields are currently emitted here; never fill those omissions as authority. |
| Configuration | Exact arctangent_terms, sinc_terms, rational_bit_limit with nonboolean builtin values 32, 8, 65,536. | Compare candidate and enclosure independently to this profile; a lower verifier cap does not rewrite producer configuration. |
| Small candidate binding | Exact q_word, sign, q_ratio. | Must equal expected decoded q and both complete records; this three-field object is not the enclosure transcript. |
| Series stages | Exact arctangent, pi, squared_argument, coefficients, polynomial, remainder. Arctangent is two two-endpoint intervals; pi/squared_argument/polynomial/remainder each two endpoints; coefficients exactly eight pairs. | Twenty stage pairs must be present, canonical and shape/order-valid; this does not replay or prove the series/real-pi inclusion argument. |
| Zero stages / certificate | Empty stages; exact three-key certificate word, interval, branch with unit word, [1,1] and zero. | Separate from the eight-field V-cell interface; signed q zeros retain distinct words/signs even though the canonical q ratio is (0,1). |
| Series certificate | Exact current eight-key cell shape with seven canonical pairs, eligible output word and fixed neighbor/order/tie/containment types. | Certificate interval equals both root intervals; full cell recomputation is separate V-cell work, not claimed by V-bind. |
| Declared work | Enclosure work has rational_operations/max_result_bits. Candidate work has enclosure_entries/cell_entries/enclosure, plus cell only for series. Cell has seven keys: search_iterations, endpoint_iterations, dyadic_decodes, midpoint_constructions, rational_comparisons, rational_constructions, max_result_bits. | Endpoint_iterations is an exact two-item builtin list of nonnegative counts at most 64 each, summing to search_iterations; snapshot it independently. Other counts are exact builtin nonnegative bounded integers. Exact copied enclosure-work equality is a declaration, not execution/capture/resource evidence. |

All successful profile strings, fixed statuses and false flags must match their
current branch-specific literals exactly, with builtin type checks before
equality. Reject numeric aliases, missing/extra stages, partial records, unknown
selectors, changed configuration, noncanonical pairs or inconsistent copies.
Domain_ratio is exactly (1,64). No qualification is inferred from matching
allowed_use/status/reason, file digests or a claimed work counter.

**Independent q and correspondence.** Independently decode the expected exact
builtin u64 word: reject exponent 2047; retain its stored sign; reconstruct the
finite dyadic and canonical signed numerator/positive denominator with guarded
integer-pair mathematics. For stored sign s, exponent e and fraction h, the
zero-exponent value is $(-1)^s h2^{-1074}$; otherwise it is
$(-1)^s(2^{52}+h)2^{e-1075}$. Preserve the stored sign separately from the
canonical ratio. Both signed zeros produce (0,1), not the same stored
word/sign. Nonzero subnormal q is never rewritten to zero. Require the absolute
decoded value within 1/64, matching target/domain/profile and exact word/sign/
canonical-ratio equality in the candidate, enclosure and small binding.

Infer the branch from this independent q value, not a candidate root branch
(none exists). For series require the enclosure branch/reason and full stage
shape, positive ordered common interval, and exact equality with the candidate
root and certificate interval. Order both arctangent intervals, pi, squared
argument, polynomial and remainder intervals without evaluating their claimed
mathematical relationship. Reject a reversed interval, not clip it. For zero
require both roots/certificate to have [1,1], empty stages, the exact unit word
and zero certificate branch; no V-cell call or fabricated eight-field record.
Candidate enclosure_entries is one and cell_entries is zero/one for zero/series.
Require candidate's copied enclosure work to equal the complete enclosure work.

Even a fabricated but mutually consistent full tuple can satisfy declared
correspondence. It is not capture authenticity, independent enclosure inclusion
or source authority. A same-valued interval, unchanged digest or even-sinc
symmetry cannot excuse a different expected q/sign/word. A later composition
must bind any V-cell evidence to this exact certificate content, not just its
status or output word; that composition is not adopted or implemented here.

**Bounded checking and publication proposal.** Separate verifier ceiling L
defaults to 65,536 bits; require an exact nonboolean builtin integer from 1
through 65,536, snapshot and recheck before guarded stages/final publication.
Invalid/increased/observed changed limits stop unresolved, with no precision
retry or change to old caps. Preflight q shifts/power denominators, raw pair
canonicalization and both products for every rational order/domain comparison;
postcheck canonical component types/signs/sizes. Later cancellation cannot
excuse an oversized raw operation. Special exact-zero decoding may avoid a
large unreduced zero denominator; it may not collapse a nonzero subnormal.

The proposed per-entry ledger is at most 35 input-pair canonical checks for
series (11 candidate, 24 enclosure), or ten for zero (six candidate, four
enclosure); one independent q decode/canonical construction; eight guarded
order/domain comparisons for series (seven interval orders plus domain), or
two for zero. Thus at most 36/11 counted Fraction constructions if used for
canonicalization. Count duplicate supplied pairs even when equal; metadata,
fixed word/radix/key setup, equality, snapshot and publication are separate.
Declared producer work is not verifier work; require bounded builtin u64 counts
and maximum canonical bits at most the declared producer cap, not measured RAM.
The endpoint list is separately shape/type/bound checked and copied; it is not
a scalar count or rational pair. Its consistency check does not prove execution.
Attempt counters precede their own evaluation after applicable guards; retained
max bits counts only accepted canonical outputs. GCD/allocation, early rejection
of already allocated caller objects, totality, primitive/native/time/RAM work
and live binding correctness remain unqualified CT0-CT2/CT5/W0/TB0 premises.

Publish a fresh diagnostic-only record with a distinct proposed identity such
as `synthetic_sinc_declared_binding_check_v0`, retained expected q/sign/ratio,
branch/profile/common interval, exact certificate snapshot and separate attempted
verifier-work metadata. Describe success only as `verified_declared_sinc_binding`,
never certified rounding/enclosure/native/source/work or accepted proof. Five
flags stay false, native/motion/source/work unresolved and consumer ineligible.
Ordinary rejection omits verified binding/certificate content; unexpected/
allocation/interruption errors propagate, including during publication. No
input/old record mutation or universal return/rollback guarantee.

**Independent evidence and decision gates.** Preparing these gates closes none:

| Gate | Required Evidence / Decision | Stop Until Present |
| --- | --- | --- |
| VB0 / VC5 interface | Approve the exact profile, separate inputs, zero path, limits and a separately bounded capture/checker/test scope. | Design approval is not record acquisition, imports, fixture execution or code approval. |
| VB1 / capture completeness | Separate owned candidate and complete enclosure snapshots for a prospectively declared expected q; exact schema/source identities and capture/attempt lineage. | Current small binding/work copies and matching hashes are not a transcript or same-invocation proof. |
| VB2 / input ownership | Fixed builtin schemas, raw guards, serialized snapshot and fresh publication/exception argument. | No hooks, unlimited allocation, atomicity or universal rollback claim. |
| VB3 / independent correspondence | Independent q/sign/ratio/domain/branch and exact profile/interval/certificate/work-copy argument, including signed zeros/subnormals. | Producer status, common expected builder or matching endpoints is not an independent oracle. |
| VB4 / negative controls | Separately approved reused positions with swapped q/sign/config/interval/stages/zero shape/type/canonical/cap/ownership/allocation controls. | No fixtures or capture now; equal plausible forged records must not be advertised as target/live evidence. |
| VB5 / preservation and work | Existing ASTs/caps/flags/defaults/wire preserved; separate attempted/capture budgets, source gates and trusted-base work argument. | Bounded logical counts do not close CT0-CT2/CT5/W0/TB0 or actual resources. |
| VB6 / V-cell composition | Separately approved exact-content binding to independently checked cell evidence, or explicit zero mathematical path. | No producer/checker status alone, word-only join or implicit integration. |
| VB7 / V-target | Independent SR/real-pi inclusion and accepted target/domain/arithmetic premises for this exact q/profile/transcript. | Structural full stages and declared binding do not prove F(q) inclusion or native parity. |
| VB8 / V-live and consumer | Versioned capture/source/build/runtime/live-binding authority, requalification and resource/downstream decisions. | No hash, frozen record, paper argument or host fixture qualifies actual native work, motion, goals, relative transforms or a consumer. |

Proposed default is isolation with V-bind/V-target/V-live/resource acceptance
still absent. Next proposed, not approved: design-only capture/evidence/attempt-budget
protocol for these separate records, including explicit reused-position,
producer/capture/verifier entry counts, failure/retry accounting and retention.
No capture/checker/import/new fixture/run/source edit, native inspection/
acquisition, adapter/consumer integration or proof/error/work allowance/Route C/
totality/qualification adoption follows. Task 6/9, source completeness/authority,
teacher assets and ST/board remain blocked. This scope ends with document checks
and a local commit, not closure of VC5/CT4 or permission to acquire evidence.


#### NF1 V-bind Capture and Attempt-Budget Protocol (2026-11-05)

The user separately approved §127's design-only capture/evidence/budget protocol;
[review §128][sinc-bind-budget-review] records checks. This prepares a concrete
future bounded package, not capture/checker implementation, fixture execution,
accepted evidence, a resource allowance or qualification. No source/test change,
target import/helper/native run, installed inspection, acquisition or integration.

**Local hypothesis and proposed default.** A single owned in-memory capture pool
per invocation can provide separate complete candidate/enclosure inputs for the
§127 declared-correspondence checker, while recording every attempted source
entry and never implying same-invocation enclosure provenance. Reuse only the
twelve existing literal positions at `_ARITHMETIC_TRACE_LITERALS[i][2][4]`,
for i=0..11. Positions are not twelve distinct q words or independent evidence;
duplicates and both stored signed zeros retain their original slot identities.
Do not evaluate a trace/owner/reference to recover q, select by output quality,
replace rejected slots, alter defaults or introduce a new q/scene/cohort.

Propose a private checker in the existing diagnostics module and one capture
fixture plus one sixteen-position test in the existing simulator test file.
No new module, CLI, report format or persistent capture/cache is needed. All
old AST nodes, signatures, caps, defaults, wire, reports and logs must remain
unchanged. Helper isolation and the five false flags remain the default.

**Capture sequence and exact origin labels.** In one serialized, non-worker
invocation, freeze the prospective twelve-slot input manifest before any producer
entry: position, exact existing q word, expected profile and source/test file
identities. Verify unchanged old configuration (32/8/65,536; cell step limit 64)
and available original fixture bindings; do not repair drift by rewriting caps.
These identities/bindings are assumptions and declared lineage, not V-live proof.

For each slot in fixed order, reserve one candidate entry, call the unchanged
candidate once with literal synthetic opt-in, then reserve one direct companion
enclosure entry and call the unchanged enclosure once for the same expected q.
The candidate may itself enter enclosure once and cell at most once; account for
those as nested entries, never hide them as capture setup. The direct record is
labelled companion_direct, not candidate_callee or the same invocation's actual
enclosure transcript. The candidate's small binding/work copies cannot supply
missing stages or prove that the companion was its callee. Intercepting callee
payloads, changing owner/recorder paths or claiming same-event provenance is not
part of this proposed package; that alternative needs a separate contract.

Before retaining a successful pair, raw-check exact §127 full schemas, sizes and
fixed containers, including the producer's seven-key cell work and two-item
endpoint list. Then create owned fixed-field snapshots with no arbitrary-object
conversion/copy hooks. Candidate and companion snapshots must be independent
from producer objects, each other, fixture consumers and per-control mutation
copies. Preserve every complete stage and declared work field; no clipping,
rounding, status retagging or partial-record enrichment. Producer work remains
declared metadata, not capture instrumentation or primitive resource evidence.

Retain a bounded slot/attempt/status/reason marker for unresolved/malformed
returns; do not retain arbitrary raw objects or publish them as complete pairs.
Never refill that slot or collect an alternative q. Unexpected capture/allocation/
interruption failure aborts pool construction, preserves spent-entry markers
where available and cannot trigger automatic rebuilding for each test. Partial
setup is not a valid reusable pool. No universal marker/publication guarantee
after allocation failure; unexpected errors propagate.
Pool eligibility requires all twelve complete pairs; a missing/failed pair fails
setup before verifier entries, never skips or reassigns a control.

**Reservation and invocation ledger.** Reserve before delegation, consume once
even on opt-in rejection, unresolved return, downstream exception or snapshot
failure; never refund a producer entry because no record was published. A denied
reservation makes no target call and is a separate diagnostic event, not a hidden
successful entry or counter reset. Abort on a denied/ambiguous budget request.
The budgets below count the new package only; existing default regression
controls require explicit separate gate approval and their own historical limits.

| New-Package Quantity / Per Invocation | Proposed Hard Ceiling | Accounting Boundary |
| --- | --- | --- |
| Prospective literal slots / pool setup | Twelve slots / one setup attempt. | Freeze before calls; duplicates count separately, no retry/refill/worker multiplication. |
| Candidate entries | 12 | One reservation per slot, including failed/unresolved calls; no second candidate call in a verifier control. |
| Enclosure entries | 24 | At most twelve candidate-nested plus twelve companion-direct entries, separately labelled. |
| Cell-producer entries | 12 | Candidate-nested only; zero may consume none, no independent cell/word/checker run for capture. |
| Full-record snapshot attempts | 24 | At most one candidate and one companion snapshot per slot; partial/failed snapshots consume attempts, not permission to recapture. |
| Declared-binding checker entries | 32 | Sixteen control positions, exactly two requested checker entries each; single selected control uses two. |
| Existing V-cell/owner/reference/native/trace/log adapter entries | Zero from the new package. | Poison after pool setup; no implicit V-cell composition or F(q)/native replay. |

Guard and instrument the candidate, nested/direct enclosure and nested cell
entries before any call. Keep original callable references and origin counters
separate; fixture wrapper faithfulness/runtime correspondence is assumed, not
qualified. A failed setup must be cached as failure or end the invocation, not
re-enter producers on later parametrized controls. Do not use parallel workers,
rerun plugins, multiple pools, cross-process caches or resumed partial pools.
Each new process/test invocation gets a fresh explicitly budgeted pool, not a
free retry. Record reserved entries, outcomes, snapshot attempts and checker
attempts separately from returned producer/verifier logical work counters.

Propose one single-control focused check, one complete sixteen-control matrix
and one required root source gate. Allow at most two additional executions only
after a diagnosed substantive local repair, for the same focused check and/or
required gate; never repeat an unchanged successful gate. Thus at most five
new-package invocations, each with the ceilings above, not five automatically
authorized runs. Aggregate conservative ceilings are 60 candidate, 120 enclosure,
60 nested cell, 120 snapshot and 160 binding-checker entries. Actual selected/
failed invocations may use less; retain exact counts and all failures, do not
report ceilings as observed work. Additional execution needs fresh bounded
approval; after three failed approaches, record the blocker and stop that work.
Static lint/format/AST/reference checks and zero-execution discovery are recorded
separately, not numerical/helper execution or a successful behavior check.

**Sixteen-control draft.** Reuse the twelve captured positions for these named
control slots; duplicate selection for later slots is deliberate. Each slot
first checks an owned baseline pair, then makes one bounded altered/exception/
repeat request. Baseline expectations come from independently decoded expected
q and explicit §127 correspondence rules, not producer status as a truth oracle.
The fixed BC0..BC15 pool-index mapping is
`(0, 1, 2, 3, 4, 5, 6, 1, 8, 9, 10, 11, 7, 1, 2, 3)`.
It covers all twelve positions; BC7 uses the negative stored zero.

| Control Position | Second Request / Required Observation |
| --- | --- |
| BC0 | Literal opt-in false raises; entry remains spent. |
| BC1 | Integer opt-in alias raises; entry remains spent. |
| BC2 | Swap a companion with a different existing stored q/sign; reject even if values/intervals coincide. |
| BC3 | Sign numeric alias; reject before accepting correspondence. |
| BC4 | Configuration type/profile mismatch; no cap/term normalization. |
| BC5 | Root/certificate interval mismatch using retained existing content; reject. |
| BC6 | Missing/extra stage shape; no transcript completion or inclusion claim. |
| BC7 | Wrong signed-zero branch/certificate shape; no fabricated eight-field zero cell. |
| BC8 | Hostile builtin-container subclass/type control; no conversion/copy hooks. |
| BC9 | Noncanonical rational pair; equality after reduction cannot excuse input. |
| BC10 | Raw oversized pair; reject before canonicalization. |
| BC11 | Reduced separate verifier cap; bounded unresolved, old caps intact. |
| BC12 | Increased/invalid verifier cap; no new allowance. |
| BC13 | Observed mid-call verifier-cap change; stop before publication. |
| BC14 | Injected allocation failure; propagate without a verified record or recapture. |
| BC15 | Owned repeat and independent input/report/work/list mutation; saved baseline/pool remain unchanged. |

Cases cover named anchors, not every field/branch combination or mathematical
domain. Domain/flag/work/neighbor/selector tamper variants and any further
coverage require a separately budgeted follow-up if these sixteen cannot expose
them. Do not hide extra checker calls in fixture builders, assertions, helpers,
ownership repeats or exception probes. Reuse existing independent dyadic/test
utilities for expected content; the checker calls none of those or producers.
Poison prohibited paths after setup; snapshot pool originals before mutations,
restore scoped patches and keep each control's mutable copies separate. No
actual fixtures or expected record values are generated by this design work.

**Retention, acceptance and next permission.** Keep future capture payloads only
in the invocation's owned synthetic fixture memory, released on teardown;
no task labels, dataset, cohort, persistent exporter, cache or log application.
Retain bounded counts/source identities/outcomes/failed-check history in the
existing review checkpoint; preserve existing reports/logs, do not regenerate
them. No deletion of unrelated/user data, dependency/download or hardware work.

Before a future source commit, require the focused behavior check, complete
matrix, default root pytest/lint/whitespace gate, changed-file format/editor
checks and historical AST/cap/flag/default/wire preservation. Default gates
include their unchanged legacy fixture controls only under explicit approval;
no additional native/sanitizer/Arm/GPU/teacher/board requalification follows.
Capture counts/file identities/frozen records and the sixteen controls do not
close VB1/VB3/VB5/VC5/CT4, V-target/V-live or actual resource/consumer claims.

The user's follow-up separately approves the next bounded part after this
protocol is finished: the isolated private in-memory capture fixture,
declared-binding checker and sixteen reused controls, only under this twelve-slot/
12-candidate/24-enclosure/12-nested-cell/24-snapshot/32-checker per-invocation
protocol, at most five budgeted verification/repair invocations and normal source
gates. No new q/scene, callee interception, V-cell/owner/reference/native/adapter
integration, persistent artifact or proof/error/work allowance/Route C/totality/
qualification adoption. Old helpers and `1bb89fe` stay; Task 6/9, native motion/
goals/relative transforms, source completeness/authority, teacher assets and
ST/board remain blocked. Present approval ends at document checks/local commit.


#### NF1 Isolated Declared-Binding Checker (2026-11-05)

The user's §128 follow-up approved the bounded private capture/checker/sixteen-
control package. [Review §129][sinc-bind-implementation-review] records execution
and failures. One private 65,536-bit limit and checker were added; every old
source/test AST node and order is preserved. There is no runtime/wire/owner/
reference/V-cell/native/adapter integration or qualification promotion.

The checker accepts only literal synthetic opt-in, expected finite builtin u64 q
and §127's exact full record profiles. It independently decodes signed q, checks
canonical pairs/domain/configuration/branch/common interval/work-copy consistency
and stage interval ordering, then publishes fresh diagnostic-only correspondence.
All raw pair guards precede Fraction work. Candidate-work keys are validated
before lookup, following a reproduced hostile-key failure and repair. Fixed
validated containers bound snapshot traversal under serialized caller ownership;
this is not an atomic snapshot, immutable binding or universal return guarantee.
Unexpected/allocation/interruption errors propagate. No producer/checker/native
call occurs inside verification; no interval/series/cell inclusion is inferred.

The in-memory module fixture captures twelve candidates, twelve nested and twelve
companion-direct enclosures, six nested cells and twenty-four snapshots per tested
invocation. Origin-labelled attempt markers are distinct from declared work.
All twelve full pairs are required; worker execution is rejected. No callee
payload interception, same-invocation transcript claim, persistent capture or
task dataset. Control copies/report/work/endpoint-list mutations leave pool and
saved baseline unchanged. Sixteen cases request exactly two checker entries each:
17 verified, 12 unresolved and three exceptions per complete matrix. These are
finite synthetic correspondence controls, not source authority or target quality.

All five allowed source invocations were spent: BC0 pass, BC8 hostile-key failure,
same BC8 repair pass, complete matrix pass and root gate pass. Checker entries
were 2/2/2/32/32 (70 total); capture totals 60 candidate/120 enclosure/30 nested
cell/120 snapshots. No extra capture/checker execution remains authorized. Final
gate: 2,197 passes, known xfail, 71 existing warnings; lint/changed-file format/
editor/old-AST checks pass. No additional opt-in C/native/Arm/sanitizer/model/board
gate or environment qualification. The five flags remain false; native/motion/
source/work unresolved and every consumer ineligible. `1bb89fe` stays unchanged.

Declared correspondence still permits mutually consistent fabricated records.
V-cell exact-content composition, V-target inclusion, V-live/capture authority,
CT0-CT2/CT4-CT5/W0/TB0/resource and Task 6/9 claims remain unaccepted. Counts and
maximum accepted canonical bits are not primitive/native/time/RAM fit evidence.
Next concrete prerequisite is a conditional guard/snapshot/publication/work
review of this exact checker before considering wider evidence use; no further
capture/run, integration or proof/error/work allowance/Route C/totality/qualification
is approved by completing the bounded source package. Isolation remains default.


#### NF1 Declared-Binding Conditional Review (2026-11-05)

The autonomous continuation prepares the same-checker conditional review identified
in §129, using the committed source/test text at `9869129` only. This is routine
paper preparation, not an accepted proof, correspondence claim, trusted-base
qualification or renewed source execution. [Review §130][sinc-bind-paper-review]
records static checks. The five source invocations remain exhausted; all source,
tests, caps, flags, consumers and historical evidence stay unchanged.

**Conditional Claim.** Assuming faithful builtin arithmetic/container operations,
faithful terminating Fraction canonicalization, stable runtime bindings, serialized
caller ownership and successful allocation/ordinary return, a verified result
establishes the exact declared correspondence described in §127. It does not
establish that supplied stages enclose F(q), that certificate neighbors/boundaries/
ties are correct, or that any producer/capture/native/live source is authoritative.
Matching fabricated records remain admissible to this deliberately weaker claim.

| Obligation | Local Conditional Argument | Unclosed Premise / Claim Limit |
| --- | --- | --- |
| BR0 / VB2 interface | Literal opt-in and a separate exact builtin integer limit precede verification; invalid/increased limits return unresolved with no certificate. Exact dict length plus distinct allowed builtin string keys gives exact key coverage. | Builtin/runtime correctness and caller allocations are assumed; this does not bound all rejected-object or setup work. |
| BR1 / VB2 no-hook boundary | Types/shapes precede nested lookups, equality, arithmetic and fixed-schema copying. Candidate-work shape precedes its enclosure lookup; both copied enclosure-work dictionaries and integer leaves precede equality. | BC8 establishes its finite hostile-key regression only. Stable keys/values and serialized ownership are required; no concurrent or malicious-runtime guarantee. |
| BR2 / VB3 canonical inputs | Every supplied pair has exact builtin integer leaves, positive denominator and raw component guards before any Fraction call; canonical equality rejects reducible aliases. | Fraction/GCD termination/correctness, allocation and installed/live correspondence remain CT1/TB0 premises. |
| BR3 / VB3 independent q | Finite u64 fields independently select sign/zero/series and the guarded dyadic; expected q is not read from either record. Absolute q must be at most 1/64 and both records/small binding match word/sign/canonical ratio. | Both zero words retain distinct signs and ratio (0,1); a nonzero subnormal is not zero. Exact integer decoding is assumed, not native floating-point qualification. |
| BR4 / VB3 declared correspondence | Exact profile/branch/domain/common-interval/certificate-interval/work-copy checks and ordered series intervals establish those declarations. Zero additionally requires empty stages, unit word and [1,1]. | Series arithmetic, pi inclusion, coefficient truth and cell neighbor/boundary/parity/order truth are not recomputed; containment/status fields are not evidence of those claims. |
| BR5 / VB2 guarded work | Raw pair guards, q shift/denominator guards, canonical postchecks and cross-product size sums precede the corresponding rational operations. The separate limit is rechecked through guarded stages and immediately before publication. | This detects observed changes, not temporary change-and-restoration or immutable bindings. Fixed word/key/metadata/copy work is outside the rational cap. |
| BR6 / VB2 snapshot | Fixed validated schemas terminate owned traversal under the ownership premise. Dict/list copies are fresh; immutable builtin leaves/tuples may safely share values. The returned certificate is separately copied. | Validation rereads caller fields and canonicalizes collected original immutable pairs after copying; no atomic snapshot or enforced ownership. Allocation/interruption may prevent completion. |
| BR7 / VB5 attempted ledger | Input canonical attempts, one q decode, guarded comparisons and Fraction attempts are counted at their actual stage boundaries; max_result_bits records accepted canonical outputs only. | Duplicate supplied pairs count separately. Rejected raw/products, GCD internals, caller/copy/publication objects and elapsed/native/RAM work are not measured by these counters. |
| BR8 / VB2 publication | BindingStop returns only unresolved metadata/work; successful ordinary publication attaches a fresh diagnostic certificate after final preflight. Unexpected/allocation/interruption exceptions propagate. | No universal return, rollback or exception-atomic runtime claim. No source input mutation is prescribed under faithful bindings. |
| BR9 / VB4-VB5 isolation | §129's bounded controls and exact preserved old ASTs/caps establish their recorded finite checks. Five flags remain false and every consumer stays ineligible. | Finite tests/file identities/private names do not accept VB2/VB3/VB5, CT0-CT2/CT4-CT5, W0/TB0, proof/allowance/totality or any downstream qualification. |

**Paper Ledger.** Series candidate fields contribute eleven supplied pairs:
q ratio, two root endpoints, seven certificate pairs and one small-binding ratio.
The enclosure contributes twenty-four: q ratio, two root endpoints, domain and
twenty stage pairs. Zero contributes six candidate plus four enclosure pairs.
Thus complete successful paths have 35/10 canonical-pair attempts, one dyadic
decode, 36/11 Fraction attempts and 8/2 comparisons. Series comparisons are domain,
common interval and six stage interval orders; zero has domain and common interval.
This is an exact conditional logical ledger, not new measurement or total cost.

Raw validation collects all pairs before fixed-schema copying or canonicalization.
Each canonical attempt precedes its rational call; each guarded rational/comparison
attempt precedes its own evaluation after preflight. Conservative comparison
guards use the sums of operand component bit lengths before both products; later
cancellation/reduction does not excuse a rejected raw size. For any finite u64 q,
the independent unreduced dyadic needs at most 1,024 numerator or 1,075 denominator
bits, checked before its shift/power construction. Exact zero instead constructs
(0,1); it does not construct the large zero denominator or alter nonzero semantics.

Fixed word masks/bounds, key sets/profile/result setup precede these guards and are
not governed by the rational limit. Metadata endpoint counts are separately bounded
builtin integers; two counts at most 64 sum to search_iterations, not witnessed
execution. Snapshot/publication and duplicate immutable value traversal are bounded
by the accepted fixed schema, not by a certified stack/RAM/time/runtime allowance.
Initial/final file identities are not loaded-code or callee authority. The fixture's
companion-direct enclosure is a distinct call, not a candidate-callee transcript.

**Decision Brief.** Recommend retaining isolation and no accepted claim for now.
The narrow candidate for review is declared correspondence under the assumptions
above, with all five flags false and no V-cell/V-target/V-live/resource/consumer
promotion. Its benefit is separating structural evidence from mathematical/live
claims; its cost is that internally consistent fabrications remain admissible and
runtime/trusted-base work is still assumed. Accepting stronger language would need
different evidence, not merely accepting this paper ledger or repeating fixtures.

Proposed acceptance checks are: review BR0-BR9 against these exact source identities;
accept or reject each CT0-CT2 ownership/arithmetic/exception premise explicitly;
retain exact-content separation from V-cell and SR inclusion; define permitted
source/runtime/resource evidence and requalification triggers; and record a narrowly
worded claim decision without changing flags or consumers. These are unaccepted
review gates, not execution permission. No new capture/checker run, integration,
native/source acquisition or proof/error/work allowance/Route C/totality adoption.
Task 6/9, native motion/goals/relative transforms, source completeness/authority,
teacher assets and ST/board remain blocked. A broader composition or evidence
package needs its own decision; the exhausted source approval cannot supply it.


#### NF1 Exact-Content Composition Contract (2026-11-05)

The user explicitly selected design-only V-cell composition preparation after
§130. [Review §131][sinc-composition-contract-review] records this approval and
checks. This proposes a separate private composition boundary, not implementation,
integration, a new run allowance or adoption of any claim. Existing helpers/caps/
flags/source/tests stay unchanged; §129's five source invocations remain exhausted.

**Candidate Claim and Default.** For a series input, combine declared q/profile/
interval correspondence with independently checked whole-cell certificate content.
The proposed diagnostic claim is only that the same supplied interval/certificate
passed both checks under their faithful-arithmetic/runtime/ownership premises.
Even correct cell contents plus matching fabricated enclosure stages do not prove
that F(q) is in that interval. V-target/SR inclusion, V-live/callee authority,
resources and consumers remain separate. Recommend continued isolation, not
accepting this composition claim or promoting any qualification flag.
Proposed source surface is one additive private `_check_synthetic_sinc_composition`
and `_SYNTHETIC_COMPOSITION_BITS`, not an owner, adapter or production API. Its
three inputs are the retained expected q and complete candidate/enclosure records.

**Inputs and Ownership.** Propose expected_q_word, complete candidate_record and
complete enclosure_record, with literal synthetic opt-in. No external precomputed
binding/cell reports or consumer/owner/log/reference inputs. Retain §127's complete
23/20-field input schemas, producer profile 32/8/65,536 and exact zero/series
certificate shapes. Validate fixed builtin keys/types/lengths/raw sizes before
lookup/equality/copy; take owned fixed-field snapshots under serialized ownership.
Do not use unrestricted traversal/deepcopy, coercion, JSON, digest-only equality,
producer re-execution or arbitrary verifier callbacks in the proposed private
boundary. The current source identities are version anchors, not live attestation.

The binding check's successful output has 23 fields: its sixteen fixed diagnostic
fields plus q_word, sign, q_ratio, branch, profile, interval and certificate.
The cell check's successful output has seventeen: its sixteen fixed diagnostic
fields plus certificate. It has no root q_word, word or interval. Require exact
current identity/allowed-use/status/reason, configuration/work shapes, five false
flags and unresolved native/motion/source/work/ineligible consumer fields in each.
Never infer compatible profiles from equal root counts or a success string.
Binding work has canonical_pair_checks, dyadic_decodes, rational_comparisons,
rational_constructions and max_result_bits; cell work additionally has
midpoint_recomputations. Neither is the seven-field producer-cell work profile.
Binding selectors remain synthetic_sinc_declared_binding_check_v0 /
isolated_synthetic_declared_binding_only / verified_declared_sinc_binding /
declared_correspondence_only. Cell selectors remain
synthetic_cell_certificate_content_check_v0 /
isolated_synthetic_cell_content_check_only / verified_synthetic_cell_content /
independent_exact_cell_content_only. Their configuration is exactly
rational_bit_limit; binding additionally carries the separate producer profile.

| Boundary | Proposed Sequence / Required Join | Stop or Missing Evidence |
| --- | --- | --- |
| J0 / entry | Validate opt-in and a separate fixed-shape composition configuration before any checker entry; retain independently supplied finite q, owned complete input snapshots and all applicable raw-copy/binding/cell limits before the binding call. Zero cell configuration is not applicable. | No cap increase, fallback, refill, retries, arbitrary callbacks or producer capture inside composition. |
| J1 / binding | Reserve one nonrefundable binding attempt; call the existing declared-binding checker once on those snapshots. Require its complete exact success profile and typed q/sign/ratio/branch/profile/interval/certificate correspondence to the owned inputs. | Unresolved, unsupported/malformed output or observed binding-limit change stops before a cell entry. A profile/status string is not authority. |
| J2 / exact zero | Independently retained zero q requires both signed-word/sign distinctions, canonical (0,1), empty enclosure stages and exact three-field unit-word/[1,1]/zero certificate. Cell attempts remain zero. | Do not fabricate an eight-field cell certificate or describe the uncalled cell checker as verified. Proposed status checked_declared_zero_binding is separate. |
| J3 / series cell | Revalidate the separately retained cell-check limit after binding; reserve at most one cell attempt and call the existing pure-cell checker on an independently owned copy of the exact eight-field binding certificate. | Never pass the small enclosure binding, a root word, a different interval or a previously saved cell report. No cell call for rejected binding or zero. |
| J4 / typed exact content | After fixed schema/type/raw-size validation, compare every certificate field from the owned input, binding output, cell input and recomputed cell output. The interval also equals both root intervals and the binding interval. | Equal words/statuses/hashes or Python equality on unchecked numeric aliases is insufficient; any differing neighbor, boundary, parity, order, interval or flag rejects. |
| J5 / configuration and work | Keep composition, binding and cell limits distinct; producer profile remains unchanged. Recheck applicable saved limits after calls and before final publication, preserving separate attempted-work reports. | No summed/raised rational ceiling, overwritten configuration, deduplicated canonical checks or inferred primitive/native/RAM/time allowance. |
| J6 / publication | Publish fresh diagnostic-only composition evidence only after the entire applicable join. Proposed series status checked_declared_binding_and_cell_content; zero uses J2. Retain q/sign/branch, exact interval/certificate and separately copied work/entry metadata. | Ordinary stop omits composed certificate/evidence. Unexpected/allocation/interruption exceptions propagate; no universal return or rollback/atomicity claim. |
| J7 / isolation | Five flags always false; native/motion/source/work unresolved and consumer ineligible, including on either proposed success branch. No old result retagging or owner/runtime/wire/default change. | No accepted proof, Route C, totality, V-target/V-live/resource or downstream consumer use follows from composition. |

The typed certificate projection uses a fixed order: word, interval, neighbors,
boundaries, closed_ties, lower_order, upper_order, whole_interval_contained.
Check exact builtin dict/string/tuple shapes and nonboolean integer leaves, exact
boolean claims, positive denominators and raw size limits before projection/equality.
Canonicality is established in the checker calls under their premises and retained
only through exact typed content equality; the join performs no additional reduction
or normalization. Series has seven rational pairs; zero's separate profile
has no neighbors/boundaries. Do not canonicalize away changed contents, drop fields,
join only on q/word, substitute a successful status or accept stale external reports.
This is an interface proposal; no new projection/checker function is implemented.

**Conditional Composition and Work.** If the two independent checker arguments
are later accepted under explicit shared CT0-CT2/TB0 premises, exact content binding
connects their statements about one supplied certificate. Only a separately accepted
SR/target inclusion argument for this exact q/profile/complete enclosure could then
connect F(q) to that cell. That implication is conditional paper reasoning, not
proof acceptance, a native-sinc bound or current qualification. The signed-zero
branch does not borrow the eight-field content interface or attest source authority.

Complete successful series paths would perform at most one binding and one content
check: 42 input canonical attempts (35 plus seven), four dyadic decodes, two midpoint
recomputations, eleven comparisons and 48 Fraction attempts (36 plus twelve).
Zero would perform one binding check only: ten canonical attempts, one decode,
two comparisons, eleven Fraction attempts and no midpoint/cell attempt. Count the
seven duplicate certificate pairs twice; do not share producer/canonical results
to erase independence. These are proposed conditional logical ledgers, not runs,
primitive work or measured resources. The new projection/copy/metadata/publication
work needs a separate fixed-schema argument and is not covered by these counts.

Propose an independent composition raw-copy ceiling of 65,536 bits, exact builtin
nonboolean 1..65,536; no Fraction/float/native arithmetic in the join itself.
The binding and cell checkers retain their own limits and guards. A lower limit
may reject; it does not rewrite the 32/8/65,536 producer profile. A zero branch
does not enter the cell checker: report its limit/work as not applicable, not
as executed/verified. Observed mutation rejects, but temporary change/restoration,
runtime binding fidelity, caller allocation, concurrent ownership, GCD, exception
publication and stack/time/RAM remain unqualified assumptions or evidence gaps.
Proposed fresh report identity is synthetic_sinc_composition_check_v0, allowed_use
isolated_synthetic_sinc_composition_check_only, with the separate J2/J6 statuses
or unresolved_synthetic_sinc_composition. Retain explicit configurations for the
raw-copy/binding/applicable cell limits, the producer profile, and attempted entry
counts with separately copied binding/cell work. For zero, cell configuration/work
is not applicable and its entry count zero; for rejection, no composed certificate.
Return no consumer decision, calibrated confidence, free-space or task label.

**Unaccepted Gates.** CJ0-CJ7 require separate decisions/evidence: exact input/
output/zero profiles and J0-J7; raw/typed exact-content ownership and stop argument;
independent correspondence/cell and conditional target-premise separation; cap/
attempt/setup/copy/publication work; bounded reused negative/exception controls;
old AST/cap/flag/default/wire preservation and source gates; accepted source/runtime/
resource evidence policy; and an explicit narrowly worded claim/consumer decision.
Preparing this contract closes none of VB6/VC5/CT3-CT5 or W0/TB0 and approves no run.

| Gate | Required Separate Evidence / Decision |
| --- | --- |
| CJ0 | Approve the exact J0-J7 input/output/zero/series interface, not a runtime API. |
| CJ1 | Review typed exact-content/raw-guard/snapshot/no-hook/stop-publication arguments under explicit ownership premises. |
| CJ2 | Review independent V-bind/V-cell reasoning and retain separate, unaccepted SR/V-target inclusion premises. |
| CJ3 | Review three distinct limits, entry accounting and separate setup/copy/publication/runtime work. |
| CJ4 | Approve the fixed reused CC0-CC15 variants/map and bounded synthetic execution, with finite evidence limits. |
| CJ5 | Preserve old ASTs/caps/flags/defaults/wire/artifacts and approve affected focused/default source gates. |
| CJ6 | Decide admissible source/runtime/live/resource evidence and requalification triggers; hashes/counts alone are insufficient. |
| CJ7 | Explicitly accept or reject a narrowly worded claim and any later consumer use; no promotion through a diagnostic status. |

**Bounded Future Proposal, Not Approval.** Reuse the twelve §129 q positions and
sixteen control slots, two composition attempts per case (at most 32), with
positive controls plus strict opt-in/type/raw/cap/snapshot faults, rejected-binding
no-cell controls, both-zero no-cell controls, same-word/different-content joins,
neighbor/boundary/parity/order/interval changes, malformed returned profiles,
observed cap changes, allocation/interruption propagation and owned result/work
mutation. Proposed CC0-CC15 mapping to existing positions is
`(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 6, 7, 8, 9)`.
Slots 0-5 are zero and 6-11 series, from the stored literal table, not a new trace
run. All twelve pool positions remain required; repeated q values are not
independent inputs or quality evidence. Each case has one ordinary control plus
exactly one second composition request; no hidden third request for assertions.

| Control / Existing Position | Proposed Second Request / Required Outcome |
| --- | --- |
| CC0 / 0 | False opt-in raises before any checker; ordinary positive zero uses no cell. |
| CC1 / 1 | Integer opt-in raises; ordinary negative zero retains its sign and uses no cell. |
| CC2 / 2 | Delete candidate certificate; raw input rejection has no cell entry. |
| CC3 / 3 | Opposite-zero expected word/sign rejects correspondence, not a same-ratio join. |
| CC4 / 4 | Replace candidate-work enclosure key with the existing BC8 hostile-key pattern; reject before its equality hook. |
| CC5 / 5 | Increased composition limit rejects without modifying old caps. |
| CC6 / 6 | Replace certificate center-neighbor word with its stored lower-neighbor word; independent cell check rejects. |
| CC7 / 7 | Swap certificate boundary endpoints; independent cell check rejects, preserving reflected series q. |
| CC8 / 8 | Replace lower_order with its float alias; reject before unchecked equality. |
| CC9 / 9 | A scoped cell-return hook changes one interval endpoint while keeping word/status; exact join rejects. |
| CC10 / 10 | A scoped binding-return hook deletes profile; stop before cell entry. |
| CC11 / 11 | A scoped cell-return hook adds a root word; exact profile validation rejects. |
| CC12 / 6 | Reduced composition raw limit rejects without reduction/refinement/retry. |
| CC13 / 7 | A scoped binding-return hook changes the cell limit to one; observed configuration change stops publication. |
| CC14 / 8 | A scoped cell-check hook raises MemoryError; propagate without publishing composition. |
| CC15 / 9 | Repeat plus independent input/result/certificate/work mutation preserves the saved result and pool. |

Tests may use scoped synthetic monkeypatches for malformed checker outputs/cap/
exception faults; that does not add a non-test callback interface or qualify
runtime bindings. One fault variant per second request is fixed before approval;
the listed alias/error categories are not permission for extra requests or vectors.
The fixed CC14 variant exercises allocation failure, not interruption; the latter
remains a required propagation contract with no new executed/control evidence.

Before any execution, a separate approval must explicitly renew affected fixture/
checker matrices and default regressions, not extend the exhausted old allowance.
Proposed ceilings per invocation, including failed/partial setup and root gate:

| Named Affected Entries | Proposed Maximum | Accounting Boundary |
| --- | --- | --- |
| Capture-fixture candidate / enclosure / nested producer cell / snapshots | 12 / 24 / 12 / 24 | Reuse one complete owned twelve-slot pool; enclosure splits at most twelve nested plus twelve companion-direct. No callee interception/refill/persistence. |
| New composition entries | 32 | Reserve before delegation, including opt-in failures, rejected inputs, exceptions and retries; no refunded slots. |
| Binding checker | 64 | At most 32 from new composition plus 32 from the renewed existing binding matrix if run; no hidden assertion/building calls. |
| Pure-cell checker | 64 | At most 32 from new composition plus 32 from the renewed existing content matrix if run; zero/rejected binding adds none. |

Propose at most five invocation positions total, including probes/failed repairs/
default gate: conservative totals 60/120/60/120 captures, 160 composition, 320
binding and 320 pure-cell entries. Nested producer-cell and independent pure-cell
entries stay different categories. Other unchanged default regressions require
their explicit historical gate scope; these named ceilings are not an exhaustive
root-suite resource claim. Serial execution only, complete owned pools or abort,
no worker/refill/replacement/new download; payloads invocation-memory-only. Approval
must confirm this control map, exact fault variants and counters before execution.

Next decision: approve/modify this bounded private prototype and affected-gate
renewal, or retain design-only isolation. Nothing here authorizes implementation,
project imports/capture/checker/fixture/native runs, acquisition, integration,
data/teacher/training, proof/error/work allowance or qualification. Task 6/9,
native motion/goals/relative transforms, source completeness/authority, teacher
assets and ST/board remain blocked; no product or risk-policy choice is adopted.


#### NF1 Private Composition Prototype (2026-11-05)

The user separately approved §131's offered private prototype, fixed CC0-CC15
map/faults, affected checker/default gates and five-invocation limit. This adopts
only that implementation/test scope, not a correspondence, cell, target, live,
resource or consumer claim. [Review §132][sinc-composition-prototype-review]
records executions, retained failures and evidence limits.

`_check_synthetic_sinc_composition` and `_SYNTHETIC_COMPOSITION_BITS` implement
the isolated J0-J7 boundary. Exact builtin input schemas/raw guards precede owned
copies and checker delegation. Applicable independent caps are saved before the
binding call, checked after each call and again before publication. One binding
entry; series alone may enter the pure-cell checker once. All eight certificate
fields and all supplied/binding root intervals join by typed exact equality.
Zero retains its separate three-field unit certificate, with no cell entry and
cell configuration/work None. No Fraction, floating/native arithmetic, producer,
owner, query, reference, capture or consumer path is added inside composition.

The fresh diagnostic report uses synthetic_sinc_composition_check_v0 /
isolated_synthetic_sinc_composition_check_only and the §131 zero/series/unresolved
statuses. Its three configuration fields distinguish raw-copy, binding and
applicable cell limits; five work fields retain composition/binding/cell entries
and separately copied binding/cell work. Ordinary stops omit the composed
certificate; unexpected/allocation/interruption errors propagate. Five flags stay
false, native/motion/source/work unresolved and consumer ineligible. Stable
bindings, serialized caller ownership and faithful runtime arithmetic remain
premises, not enforced atomicity, authority or universal successful return.

Sixteen fixed controls reuse the twelve existing pool positions, exactly two
composition requests each. Test-only accounting wrappers preserve original
checker introspection. The renewed full matrix reserves 32 composition, 57 binding
and 48 pure-cell attempts; those checker totals include both old 32-entry matrices
and the injected pre-body allocation failure. The shared capture fixture uses
12 candidates, 24 enclosures (12 nested/12 companion-direct), six nested producer
cells and 24 snapshots. Named entry counts are not complete root-suite/helper work
or native resources; early invocation totals without printed ledgers are identified
as source-derived in the review. Conditional series arithmetic ledger assertions
retain 35+7 canonical checks, 1+3 decodes, two midpoints, 8+3 comparisons and
36+12 Fraction attempts; they do not certify GCD/runtime/copy/publication cost.

All five invocation positions are spent. The source gate passes 2,213 tests plus
the known transformer xfail and 71 existing warnings; lint, changed-file format,
editor syntax/diagnostics, whitespace and every old module AST/order pass.
Source/test Git blobs: `278a0bf4c424d9090e9a02cd72554c91f395be7b` /
`952d8644261ac619db8aee3e132772bf3b0fd5b9`.
Old helpers/caps/defaults/wire/artifacts and `1bb89fe` remain unchanged.

Next authorized preparation is a same-helper conditional correctness/work review
and concrete claim/premise/evidence brief, without imports, fixtures or new runs.
No sixth capture/checker execution, acquisition, native/owner/adapter/consumer
integration, proof/error/work allowance, Route C/totality/qualification or task-data
adoption follows. CJ0-CJ7 proof/evidence/consumer acceptance remains unclosed;
bounded interface/control/gate execution is not blanket acceptance of those gates.


#### NF1 Composition Correctness and Work Review (2026-11-05)

Autonomous next-part preparation after §132 reviews the same committed helper,
not a new execution or proof/claim acceptance. [Review §133][sinc-composition-paper-review]
records the conditional argument and decision brief. Source checkpoint `cbac6d8`,
both tested source identities and five exhausted invocation positions stay intact.
The default remains isolated diagnostic use with no accepted composition claim.

**Conditional Statement.** Given faithful exact builtin operations, the separately
reviewed binding/cell checkers, stable function/configuration bindings, serialized
caller ownership and ordinary successful allocation, a successful series return
connects the two checker statements to the same supplied certificate/interval.
It does not prove that the supplied enclosure contains F(q). Zero returns only
the separately checked declared zero binding; it does not invoke or borrow the
eight-field cell theorem. No mathematical target, installed np.sinc equivalence,
live/callee authority, numerical allowance or consumer eligibility follows.

| Obligation | Conditional Same-Helper Argument | Premise / Remaining Limit |
| --- | --- | --- |
| CO0 / entry and caps | Literal opt-in precedes delegation. All applicable caps are exact nonboolean integers in 1..65,536, retained before binding; invalid/increased configurations stop. Zero cell cap is not applicable. | Configuration reads are serialized assumptions, not an atomic snapshot or a cap on all work. |
| CO1 / fixed raw schemas | Root/key/string/container types, lengths and nonboolean integer leaves are checked before owned traversal or content equality. Exact key-type checks short-circuit before membership; both complete input schemas precede copying. | Builtin behavior and no concurrent mutation are premises. Input validation has its own range/key/size work; raw cap does not bound pre-existing object allocation. |
| CO2 / ownership | Only fixed-schema dict/tuple/list contents are copied. Mutable work lists/dicts become fresh; rational/word/string/bool leaves are immutable. Original certificate/interval/ratio content is retained before delegation. | Validation-to-copy and later rereads are not synchronized against caller races; no general snapshot atomicity or live-source authentication. |
| CO3 / declared binding | One reserved binding entry uses the owned records. Exact 23-field success/16-field unresolved schemas, selectors, false flags, work/configuration and typed q/sign/ratio/branch/profile/certificate/interval are validated before joins. | This reuses the conditional V-bind argument, not an independent proof of declared stages or faithful callee selection. |
| CO4 / zero separation | Exact expected zero words retain their signs; the successful binding establishes canonical zero ratio and the three-field unit/[1,1]/zero certificate. No cell attempt, limit or work is claimed. | This does not qualify the installed wrapper's tiny-substitution branch or any nonzero word as zero. |
| CO5 / series cell | Saved applicable cell cap is rechecked, then one entry is reserved. An owned eight-field binding certificate enters the existing independent cell checker; exact seventeen-field success/profile/work is required. | V-cell content correctness and runtime fidelity remain conditional; a test return hook is not production authentication. |
| CO6 / exact join | Typed validated original/binding/cell-input/cell-output certificates compare equal across all eight fields. Original/binding and both supplied root intervals agree. Canonicality established by each checker is retained by exact content equality, not extra reduction. | Equal words/statuses/hashes are insufficient. Original retained intervals/ratios are immutable; mutable reports require serialized stable checker behavior, not a universal no-hook theorem. |
| CO7 / work and live guards | Binding/cell attempts increment before delegation; applicable caps are rechecked after each call and immediately before ordinary publication. Work is separately copied, never merged into a larger cap. | Temporary mutation/restoration, primitive/GCD/runtime work and all allocations are not observed or certified by these checks. |
| CO8 / publication and stops | No composed certificate is added until the final successful join. Only CompositionStop is caught; unexpected, MemoryError and interruption errors propagate. A returned unresolved result may retain partial attempted-work metadata, not partial composed evidence. | Local dictionary construction/update may fail; no universal return, rollback or externally enforced atomicity. Fixed CC14 tests MemoryError, not interruption. |
| CO9 / claim separation | Both success branches keep five false flags and native/motion/source/work unresolved, consumer ineligible. All old helpers/caps/defaults/wire/1bb89fe are unchanged. | Accepted CT/SR/target/live/resource/consumer evidence and explicit claim adoption are still absent; correct cells can join fabricated consistent stages. |

**Separate Ledgers.** Under those premises, complete series has one binding/one
cell entry; 35+7 canonical-pair attempts, 1+3 dyadic decodes, two midpoints,
8+3 comparisons and 36+12 Fraction attempts. Zero has one binding/no cell;
ten canonical attempts, one decode, no midpoint, two comparisons and eleven
Fraction attempts. The join adds no Fraction construction, reduction or float
arithmetic. Do not remove duplicate certificate checks to make a smaller ledger.
The actual §132 test-entry/capture counters are a different accounting layer.
Reported checker work is copied, not independently measured native primitive cost.

Fixed schemas bound traversal depth and field counts under the premises; they do
not bound GCD cost, Python integer/storage/runtime internals, caller allocation,
total live objects, stack/RAM/time or successful completion. Separate entry setup,
integer range/bit_length checks, key-set construction, metadata equality, copying,
report construction and final publication remain outside the rational-operation
ledger. max_result_bits belongs to accepted canonical checker outputs, not peak
raw/intermediate memory or a whole-composition resource measurement. Three limits
remain distinct; no sum, raise, retry, precision refinement or new work allowance.

**Concrete Decision Brief.** Candidate A/default: retain isolation and accept no
claim; no new source/runtime/evidence policy is needed to keep abstention. Candidate
B: explicitly review and accept only the conditional declared-correspondence plus
cell-content statement above, separately specifying CT0-CT2/ownership/exception
premises and admissible identity/runtime evidence. Benefit is a narrowly named
diagnostic statement; cost is unresolved assumptions and no target/live/consumer
benefit. Neither candidate authorizes another run or promotes flags.

Before B, proposed paper acceptance checks are: exact zero/series/profile scope;
CO0-CO9 guard/ownership/call/publication review against the pinned source; explicit
shared builtin/Fraction/GCD/function-binding/configuration/serialized-caller premise
decisions; separate logical/attempted/resource ledgers and exception evidence limits;
and explicit narrowly worded claim recording with all exclusions. Source/schema/
cap/profile/callee/runtime/ownership-policy changes invalidate that review and
require affected-gate renewal or new admissible evidence, never automatic reuse.
Git hashes pin bytes, not loaded function identity, selected environment or authority.

For a stronger F(q)-to-cell statement, a separate same-q/32/8/profile target-inclusion
argument and faithful complete stage generation are still required; V-bind alone
checks declared correspondence. Native/live use additionally needs its own selected
path/FP/uniform-error/source authority and resource/consumer evidence. These are
precise missing decisions, not authorization for a target checker, transcript,
acquisition, native run, owner/adapter integration or another fixture budget.
CJ1-CJ3 conditional preparation is complete; proof/CT/W0/TB0/claim acceptance and
CJ6-CJ7 evidence/consumer decisions remain unclosed. Recommend A now.


#### NF1 Target-Inclusion Content Contract (2026-11-05)

The user explicitly authorized the next **design-only target-inclusion contract**,
keeping claims unaccepted and the execution budget exhausted. [Review §134][sinc-target-contract-review]
records that decision. This defines independent mathematical-content evidence and
a bounded future proposal, not a checker, run, acquisition, integration or proof.
Source checkpoint `cbac6d8` and latest document checkpoint `203019f` remain the
anchors; the existing five false flags, helpers/caps and `1bb89fe` are unchanged.

**Target and Evidence Boundary.** The target is the real-pi normalized sinc at
the independently retained finite stored binary64 q, with exact zero target one:

$$
F(q)=\begin{cases}1,&q=0,\\ \sin(\pi q)/(\pi q),&q\ne0.\end{cases}
$$

The domain remains exact |q| <= 1/64, not an ideal motion argument, rounded native
pi product or a float approximation. Both zero words retain distinct word/sign
metadata; a nonzero subnormal is never classified as zero. Proposed private input
is only expected_q_word plus one complete 20-field enclosure record and literal
synthetic opt-in. No candidate/cell/native/owner/log inputs, external successful
target report, producer re-execution, capture or arbitrary verifier callback.
Proposed source surface is additive `_check_synthetic_sinc_target_content` and
`_SYNTHETIC_TARGET_CHECK_BITS`; this design implements neither.

A fabricated record that exactly matches an independently justified mathematical
construction can support its conditional mathematical contents without proving
that the original producer ran. Conversely, matching q/profile/interval between
two fabricated records does not establish inclusion. The proposed checker must
reconstruct every mathematical stage independently; status, hashes, work counters,
source identities and the final interval alone cannot substitute for that argument.
Expected-q source authority and selected/runtime arithmetic fidelity stay separate.

**Exact Input and Independent Reconstruction.** Retain the existing complete
enclosure schema, target/domain selectors, producer profile 32/8/65,536, exact
q/sign/q_ratio/branch, five false flags, native/motion statuses and two-field
declared producer work. Validate builtin keys/types/lengths/raw sizes before
lookup/copy/equality; collect and canonical-check all 24 series rational pairs or
four zero pairs. Take fixed-schema owned snapshots under explicit serialized
ownership. Decode expected q independently with guarded integer dyadic arithmetic;
never call the old decoder, reference, enclosure, binding, cell or composition
helper. No float conversion, NumPy/math trig, native oracle or hidden refinement.

| Boundary | Proposed Mathematical Check | Missing Evidence / Stop |
| --- | --- | --- |
| TV0 / entry and records | Literal opt-in; exact 20-field input profile, raw guards and owned snapshot before arithmetic/equality; retain local checker limits separately from the declared producer profile. | Malformed/unsupported profiles, keys, types or sizes stop; no caller hooks or unrestricted deepcopy. |
| TV1 / q and zero | Independent finite u64 signed dyadic decoding, exact domain, typed equality to declared q/sign/ratio; both zero words require empty stages and interval [1,1]. | Nonzero is never zero; opposite-zero word/sign rejects even when ratios match. Native tiny substitution remains outside this target. |
| TV2 / canonical evidence | Independently check every input rational pair with positive denominator and exact canonical equality before using stages; preserve typed interval ordering. | Numeric aliases, noncanonical or oversized pairs reject, not normalize into acceptable evidence. Shared integer/Fraction/GCD semantics remain premises. |
| TV3 / arctangent stages | For each d=5,239 reconstruct the explicit 32-term finite sum and its positive next magnitude d^-65/65; require exact equality to both declared endpoints. | Do not call/reuse producer partials, operation helpers or recorded counters as an oracle. Bounds need the alternating-series argument, not samples. |
| TV4 / real pi | Independently apply 16*A5 - 4*A239 with negative endpoint reversal, require exact declared pi interval and 3 < pL <= pU < 4. | The Machin identity/quadrant justification is a separate mathematical premise; merely passing the numeric pi bracket is insufficient. |
| TV5 / squared argument and coefficients | Reconstruct T=[q^2*pL^2,q^2*pU^2], require exact declared T and 0 < TL <= TU <= 1/256 for series. Independently reconstruct coefficients (-1)^k/(2k+1)! for k=0..7 and 17! tail divisor. | No rounded pi, zero underflow, substituted q or producer factorial state. Guard integer powers/factorials before construction. |
| TV6 / whole polynomial | Starting from [c7,c7], independently reconstruct seven interval Horner steps with four-product hulls and exact endpoint addition; require exact declared polynomial interval. | Endpoint samples alone do not establish whole-interval inclusion; retain the quantified interval induction rather than assuming unproved monotonicity. |
| TV7 / tail and final interval | Reconstruct [0,TU^8/17!] and its exact sum with the polynomial interval; require exact remainder and complete root interval. | Eight included terms give a positive first omitted tail. Wrong sign/order/denominator or merely overlapping/wider arbitrary intervals reject this fixed-content profile. |
| TV8 / publication and correspondence | Publish only complete fresh owned q/profile/interval/all-stage evidence after every check and final saved-limit recheck; zero has its separate success status. | Ordinary stop omits all target evidence; unexpected/allocation/interruption errors propagate. No universal return or rollback. |
| TV9 / limits and claims | Independent guarded operations/counters, stable bindings and serialized ownership; five flags false, native/motion/source/work unresolved and consumer ineligible. | No accepted proof, source authority, uniform native error, work/resource allowance, totality, Route C or consumer qualification. |

For d=5,239 the independently specified endpoints are

$$
S_d=\sum_{k=0}^{31}\frac{(-1)^k}{(2k+1)d^{2k+1}},\qquad
A_d=[S_d,S_d+1/(65d^{65})].
$$

The explicit finite-sum specification differs from trusting the producer's
odd-power recurrence; its implementation must still guard power/denominator/sum
construction and share no producer arithmetic helper. The two brackets plus the
conditional Machin identity enclose real pi. Interval Horner induction encloses
the same scalar polynomial for every t in T; the alternating tail is nonnegative
after indices 0..7. These obligations inherit no accepted SR/CT/W0/TB0 proof.
Exact reconstruction rejects changed stages even if word/status/interval or a
separate cell certificate still looks compatible. It is deliberately stricter
than a general arbitrary-enclosure inclusion verifier; no broader profile is adopted.

**Proposed Result and Work Profiles.** Fixed diagnostic root has sixteen fields:
identity/allowed_use/status/reason/configuration/work, the five existing false
flags and the five unresolved/ineligible native/motion/source/work/consumer fields.
Complete success adds nine fields: q_word, sign, q_ratio, target, domain_ratio,
branch, profile, interval and stages (25 total). It carries no word/cell certificate
or decision. Proposed identity synthetic_sinc_target_content_check_v0 and allowed
use isolated_synthetic_sinc_target_content_check_only; series status
checked_declared_mathematical_sinc_content, zero
checked_declared_mathematical_zero_content, otherwise
unresolved_synthetic_sinc_target_content. These are proposed diagnostic statuses,
not accepted target or numerical certification. Unsupported returns retain only
fixed configuration/attempted work, not a partial target interval/stage bundle.

Propose a separate exact nonboolean raw/rational bit limit 1..65,536, default
65,536, snapshotted before any canonical construction and rechecked at each
preflight/postcheck and final publication; no change to old limits or producer
profile. Additional fixed attempt ceilings are 256 guarded integer power/factorial
steps, 512 rational constructions, 512 add/multiply/division operations and 256
rational comparisons. Reserve before each attempted construction/operation; no
refund, retry, precision increase or cap sum. The five configuration keys are
rational_bit_limit, integer_power_steps_limit, rational_constructions_limit,
rational_operations_limit and rational_comparisons_limit. Work has seven keys:
canonical_pair_checks, dyadic_decodes, integer_power_steps, rational_constructions,
rational_operations, rational_comparisons and max_result_bits. Canonical checks
include their constructors; explicit powers/factorials have separate accounting.
These are conservative proposed logical ceilings, not a validated ledger, success
guarantee or resource bound. Precise guard/counter/phase decomposition and rejection
headroom require a separate correctness/work review before any allowance adoption.

Count one integer_power_steps attempt before each guarded integer multiplication
used to build d powers or factorials; fixed q masks/shifts and denominator
cross-products have separate raw guards, not hidden power steps. Build TU^8 by
eight guarded rational multiplications, not an opaque Fraction power. Count every
explicit rational constructor, including input canonical checks and reciprocal
construction; internal GCD/allocator work is excluded, not described as zero.
Count every add/multiply/division attempt; if division delegates to a reciprocal
constructor and multiply, charge those nested attempts too. Each three-way rational
comparison is charged once before guarded cross-products; interval selection may
not silently erase comparisons. No reuse of producer/canonical results to hide work.

Raw shifts, cross-products, sums, powers, factorials, reciprocal construction,
interval selection and canonical results require preflight/postchecks; fixed-u64
setup/key/traversal/copy/publication/caller/GCD/runtime work remains separate.
max_result_bits covers accepted canonical results only. Stable function/Fraction/
configuration bindings, successful allocation and serialized copying are premises,
not temporary-mutation detection, enforced ownership or live/build attestation.

**Future Composition and Unaccepted Gates.** A later separately approved join
would have to bind the same retained expected q, producer profile, complete owned
enclosure stages and exact root interval to both target-content and current
composition statements. No status/word/digest-only or stale external-report join.
The current composition API stays unchanged and accepts no target report; this
proposal adds no orchestrator, consumer, owner or adapter. Under separately accepted
checker/math/runtime premises, target inclusion plus whole-interval cell containment
could imply the mathematical RN64 word; it would still not imply native parity,
source authority, task quality or resources. No such implication is adopted here.

| Gate | Required Separate Review / Decision |
| --- | --- |
| TI0 | Exact TV0-TV9/input/output/zero profiles, without treating the interface as a runtime API. |
| TI1 | Independent decode/canonical/raw-guard/fixed-copy/ownership argument and shared arithmetic assumptions. |
| TI2 | Quantified finite-sum/Machin/Horner/tail correctness and exact-content target-inclusion argument. |
| TI3 | Complete attempted-work/bit-guard/construction/comparison/publication ledger; no inferred resource allowance. |
| TI4 | Fixed TS0-TS15 map/faults, five-position budget and explicit affected/default gate renewal. |
| TI5 | Preserve old AST/cap/flag/default/wire/artifacts; any later target-to-cell join needs its own contract/approval. |
| TI6 | Explicit shared CT/SR/trusted-base/runtime/ownership/admissible-evidence decisions and requalification triggers. |
| TI7 | Narrowly worded mathematical claim acceptance and a separate consumer decision, with native/source/resource exclusions. |

None is closed by this design preparation. Interface/prototype permission is
separate from mathematical/trusted-base/claim acceptance and later consumer use.

**Fixed Bounded Future Proposal, Not Approval.** Reuse the complete twelve-slot
§132 capture fixture and sixteen target controls with mapping
`(0,1,2,3,4,5,6,7,8,9,10,11,6,7,8,9)`, exactly two target attempts per case.
One ordinary control plus one fixed second request; no hidden third call/variants.
The pool includes repeated zero/series q values, not twelve independent inputs.

| Control | Proposed Second Request / Required Outcome |
| --- | --- |
| TS0 / 0 | False opt-in raises before arithmetic. |
| TS1 / 1 | Integer opt-in raises; ordinary negative zero preserves its sign. |
| TS2 / 2 | Missing root interval rejects with no target evidence. |
| TS3 / 3 | Opposite-zero expected word rejects despite equal zero ratio. |
| TS4 / 4 | Replace producer-work rational_operations key with a same-hash hostile key; reject before its equality hook. |
| TS5 / 5 | Increase target bit limit to 65,537; reject without altering old caps. |
| TS6 / 6 | Replace pi lower endpoint with (3,1); independent stage reconstruction rejects. |
| TS7 / 7 | Reverse the first arctangent interval; reject while preserving original series q/sign. |
| TS8 / 8 | Add one to the first negative coefficient by adding its denominator to its numerator; canonical but wrong coefficient rejects. |
| TS9 / 9 | Add one to both polynomial endpoints as canonical pairs; ordered but wrong stage rejects. |
| TS10 / 10 | Add one to the remainder upper endpoint as a canonical pair; wrong tail rejects. |
| TS11 / 11 | Add one to both root interval endpoints as canonical pairs; ordered wrong final interval rejects. |
| TS12 / 6 | Reduce target bit limit to one; guard rejection, no refinement/retry. |
| TS13 / 7 | Scoped constructor hook changes target cap after the first reserved constructor; observed mutation rejects without publication. |
| TS14 / 8 | Scoped first-constructor hook raises MemoryError; propagate, count attempt, publish nothing. |
| TS15 / 9 | Repeat plus independent input/result/stage/work mutations preserves saved result and pool. |

Test-only hooks are not a runtime callback interface. TS14 covers MemoryError,
not interruption; interruption remains a propagation requirement without new
executed evidence. A later approval must explicitly renew the old affected
composition/binding/cell and default matrices, not reuse an exhausted allowance.
Per invocation named maxima: capture 12 candidate/24 enclosure/12 nested producer
cell/24 snapshots; 32 new target entries, 32 existing composition entries, 64
binding and 64 pure-cell entries. At most five invocation positions including
failed probes/repairs/root gate: 60/120/60/120 capture maxima, 160 target/160
composition/320 binding/320 pure-cell. Existing unchanged root controls are a
separate explicitly renewed historical gate, not an exhaustive resource ledger.
Complete owned pool or abort; reserve before delegation, no refunds/workers/refill/
replacement/new q/scene/callee interception/persistent capture. No producer call
inside the proposed target checker. Payloads would remain invocation-memory-only.

Next decision: approve/modify the private target-content prototype, exact TS map/
faults/limits and affected-gate renewal, or retain design-only isolation. No source
edit/import/fixture/target/native/model run, acquisition/dependency/data, claim/
proof/error/work allowance/Route C/totality/consumer adoption follows. Task 6/9,
native motion/goals/relative transforms, source completeness/authority/work, teacher
assets, physical/task quality and ST/board remain unresolved and unchanged.


#### NF1 Private Target-Content Prototype (2026-11-05)

The user explicitly approved §134's private prototype, fixed TS0-TS15 map/faults,
local limits and renewed affected/default gates under the five-invocation ceiling,
keeping claims unaccepted. [Review §135][sinc-target-prototype-review] records the
implementation and actual four-position ledger. The fifth position was not needed;
completion does not authorize another unchanged gate or a different source slice.
Old §129/§132 allowances remain separately exhausted.

`_check_synthetic_sinc_target_content` is additive and private; it accepts only
expected q plus the complete enclosure record and literal synthetic opt-in. The
separate `_SYNTHETIC_TARGET_CHECK_BITS` defaults to 65,536. Old helper ASTs/order,
limits, wire, defaults and artifacts are unchanged. No producer, decoder, owner,
binding, cell, composition or native-trig helper is used by this checker.

Fixed builtin schema/raw guards precede owned copying and rational reconstruction.
All 24 series/four zero pairs must already be canonical. Expected q is independently
decoded, including sign and both zeros, and compared to the exact domain/record.
For series, explicit powers form each 32-term arctangent sum and positive 65th-power
tail; independent Machin endpoint reversal reconstructs pi. Independent q-squared/
pi-squared products, factorials through 17!, eight coefficients, seven four-product
interval Horner steps and eight rational tail multiplications reconstruct every
stage and the final interval exactly. Zero requires empty stages and [1,1]. A
consistent fabricated record may match these contents without attesting execution.

The fixed root is 16 fields on unresolved results and 25 on success, with separate
zero/series status. Five configuration fields and seven work fields retain §134's
limits: 256 power/factorial steps, 512 constructions, 512 rational operations and
256 comparisons. Reservations precede attempted operations, including nested
division/reciprocal/multiply work. Guarded raw arithmetic and canonical results
have preflight/postchecks; saved-bit-limit changes reject before publication.
Only the private ordinary stop is caught. Allocation/interruption/unexpected
errors propagate; no universal return, transaction or resource claim follows.

| Successful Branch | Canonical Pairs | Decodes | Power Steps | Constructions | Rational Operations | Comparisons |
| --- | --- | --- | --- | --- | --- | --- |
| Zero | 4 | 1 | 0 | 5 | 0 | 2 |
| Series | 24 | 1 | 147 | 230 | 131 | 57 |

These checked logical ledgers apply to the fixed reused controls, not complete
Python/GCD/allocator work, measured resources or certified all-domain completion.
The sixteen controls use the approved map and exactly two requests each; one
ordinary request plus its fixed opt-in/key/zero/stage/cap/allocation/copy fault.
Full affected matrices pass with 32 target/32 composition/57 binding/48 pure-cell
attempts, reusing one complete twelve-slot capture. No target-to-cell orchestration,
external-report input, runtime adoption or candidate consumer was added.

Five flags remain false; native/motion/source/work statuses are unresolved and
consumer ineligible. TV/TI mathematical, trusted-base, source, work/resource and
claim decisions remain separate and unaccepted. Next authorized preparation is
the same-helper conditional correctness/work review and concrete claim/premise/
evidence decision brief, with no imports or additional fixture/helper execution.
Any later join needs its own typed-content contract and explicit approval. No
Route C, totality, numerical/physical/task qualification, collection, teacher,
dependency or hardware approval; Task 6/9 and all broader gates stay blocked.


#### NF1 Target-Content Conditional Correctness and Work Review (2026-11-05)

Following the approved private prototype and autonomous continuation, this
same-helper paper review prepares conditional arguments and a concrete decision
brief. [Review §136][sinc-target-paper-review] records the exact `3f7d299` source
anchor, static checks and unchanged §135 gate. No project import, new fixture,
helper/native execution, source edit, evidence acquisition or claim adoption.
The unused fifth §135 position is not spent on another successful gate.

**Conditional Statement, Not Acceptance.** Fix a builtin finite stored word w
whose exact signed dyadic q satisfies |q| <= 1/64, a complete fixed-schema record,
and literal synthetic opt-in. Assume exact builtin integer/container operations,
Fraction canonicalization/GCD, stable selected helper/configuration bindings,
serialized input ownership, successful ordinary allocation/publication, and the
real-pi Machin/alternating-series/interval facts below. If this pinned private
helper returns its complete checked success profile, its owned interval I is
exactly the independently reconstructed interval and F(q) lies in I. Both zero
words preserve their signs and have I=[1,1]. This is a conditional content argument,
not an accepted proof, faithful loaded-code attestation, producer execution,
source authority, totality, native parity or consumer qualification.

| Obligation | Conditional Source / Mathematical Argument | Premise or Limit Still Open |
| --- | --- | --- |
| TC0 / entry and limits | Literal opt-in precedes all target work. Exact nonboolean bit limit lies in 1..65,536; four local logical ceilings stay fixed. Invalid configuration returns only fixed unresolved metadata. | Global configuration reads and trusted local bindings are not an atomic snapshot or universal temporary-mutation detector. |
| TC1 / raw schema and canonicality | Builtin key types short-circuit before membership; complete root/profile/work/stage shapes and builtin integer pairs precede owned traversal. Four/24 canonical pair checks require exact Fraction equality, not normalization of an invalid input into acceptance. | Shared builtin/GCD behavior, validation-to-copy serialization and pre-existing input allocation remain premises. |
| TC2 / q and zero | Finite signed u64 decode is independent; guarded shifts retain nonzero subnormals. Exact q/sign/domain correspondence and empty zero stages/unit interval reject opposite-zero aliases. | Expected-word source authority is absent; sign preservation is metadata, not an installed wrapper tiny-branch qualification. |
| TC3 / arctangents | Guarded powers d^0..d^65 and explicit 32-term sum reconstruct each A_d. For d=5,239 alternating terms decrease; the first omitted positive 1/(65*d^65) encloses atan(1/d) above its partial sum. Exact stage equality is required. | The quantified alternating-series theorem and exact guarded arithmetic are assumptions to review, not observed accuracy from test samples. |
| TC4 / pi | Conditional Machin identity pi=16*atan(1/5)-4*atan(1/239), with its quadrant justification, gives endpoint reversal for the negative term. Exact declared pi and 3<pL<=pU<4 are checked. | The numerical bracket alone does not prove Machin's identity or a native pi constant/error bound. |
| TC5 / squared argument and coefficients | Since pi bounds are positive, q²*[pL²,pU²] contains (pi*q)². Exact domain/ordering/positivity and TU<=1/256 are checked. Factorials 1..17 independently give eight (-1)^k/(2k+1)! coefficients and 17! divisor. | No floating underflow, rounded q/pi or producer factorial state is admitted; raw and canonical guards are not all-domain completion evidence. |
| TC6 / whole polynomial | For every t in T, four exact endpoint products enclose interval multiplication. Starting at [c7,c7], seven such hulls plus coefficient addition inductively enclose the same scalar polynomial, with exact declared polynomial equality. | Endpoint samples alone are not this quantified argument. Dependency overestimation may widen the enclosure but does not license arbitrary wider input profiles. |
| TC7 / remainder and final interval | Sinc's real-pi even series in t has decreasing magnitudes on 0<t<=1/256. After indices 0..7 the tail is nonnegative and at most t^8/17!<=TU^8/17!. Eight guarded rational multiplications, reciprocal/division and endpoint sums reconstruct the exact remainder and root interval. | Alternating-tail and analytic sinc identities remain mathematical premises; no accepted uniform native error or floating arithmetic certification follows. |
| TC8 / correspondence and publication | Every declared stage/root must equal independent canonical contents. Only after final guards are the nine success fields and copied work published; zero and series are separate. Only TargetStop is caught; unexpected/allocation/interruption errors propagate. | Dict/tuple construction/update can fail. No enforced atomic publication, universal return/rollback or interruption test evidence; TS14 is MemoryError only. |
| TC9 / work and claim separation | Reservations precede constructors/operations, including division's reciprocal and multiply. Saved-bit-limit preflight/postchecks reject observed changes; no cap sums, raises, refunds or retries. False flags and unresolved/ineligible statuses persist. | Setup/copy/raw guards/GCD/runtime/allocator/caller work and transient mutation are outside counters. No proof/resource/Route C/totality/source/consumer acceptance. |

**Logical Work Decomposition.** Keep the actual source counters distinct from
§135's fixture/checker entry ledger and from all resource costs. Guards may stop
before a constructor/operation is reserved; that guard work is separate, not zero.
An entered constructor is reserved before Fraction, including a constructor that
raises MemoryError. Successful zero uses four canonical constructors plus one
decode constructor, no powers/rational operations, and root-order/domain comparisons.
It is not a fabricated eight-field cell result or nonzero approximation.

| Series Phase | Constructions | Rational Operations | Comparisons | Power Steps |
| --- | --- | --- | --- | --- |
| Canonical input and q decode | 25 | 0 | 8 | 0 |
| Two arctangent sums and endpoints | 132 | 66 | 0 | 130 |
| Machin pi bracket | 6 | 6 | 3 | 0 |
| Squared argument | 5 | 5 | 3 | 0 |
| Coefficients / factorials | 8 | 0 | 0 | 17 |
| Seven whole-interval Horner steps | 42 | 42 | 42 | 0 |
| Eight tail products and division | 10 | 10 | 0 | 0 |
| Final interval sums/order | 2 | 2 | 1 | 0 |
| Total | 230 | 131 | 57 | 147 |

The initial eight comparisons are one root-order, six supplied-stage order and
one domain comparison. Each Horner hull constructs four products and two sums,
and charges six selection comparisons; do not replace its whole interval with
samples or omit selection work. Each arctangent has 32 term constructors, 32 sum
constructors, one tail constructor and one endpoint-sum constructor. Tail division
charges its own operation plus reciprocal constructor and multiply, hence two
constructions/two operations in addition to eight tail products. These conditional
finite-control ledgers agree with the fixed assertions, not independent measurement
of Python primitive/runtime cost or proof of successful completion over the domain.

Guard sizes cover accepted raw/canonical operands/results; max_result_bits covers
accepted canonical outputs only. The observed 13,146-bit maximum is not a maximum
over all q, raw intermediates, peak live memory or a smaller certified cap. Preflight
bit-length checks, fixed u64 masks/shifts, integer denominator products, key sets,
string/metadata equality, traversal, copying, report setup/publication, call overhead,
Fraction/GCD internals and allocations remain separate. No time/stack/RAM/native-work
budget or all-domain success bound is inferred from 256/512/512/256 ceilings.

**Concrete Decision Brief.** A/default: retain private isolation and accept no
claim; abstention and all false/unresolved flags remain unchanged. B: explicitly
accept only the conditional F(q)-in-I/content statement above for the pinned helper,
after reviewing TC0-TC9 and deciding the mathematical/builtin/Fraction/GCD/stable-
binding/serialized-ownership/exception premises and admissible implementation evidence.
B yields a narrowly worded mathematical diagnostic statement, not a source/runtime
or consumer benefit. No claim has been accepted by preparing this alternative.

Before B, proposed acceptance checks are exact word/domain/zero/input/success scope;
the finite-sum/Machin/positive-square/Horner/tail arguments; complete guard/counter/
canonical/publication and exception review; explicit shared-premise and evidence
decisions; separate logical/attempted/resource ledgers; and exact recording of the
narrow claim and exclusions. Source/schema/profile/cap/runtime/canonicalization/
ownership or mathematical-premise changes invalidate the review and need separate
affected-gate/evidence decisions. Hashes identify bytes, not selected loaded code,
environment, source authority or trustworthy sensor inputs.

A later F(q)-to-word claim still needs its own same-q/profile/full-stage/root
interval typed join with the existing binding/cell composition, plus separate
accepted premises for every helper. No word/status/hash-only or external stale-report
join is adequate. A design-only join contract is a concrete possible next task,
not an implemented orchestrator, renewed fixture budget or claim/Route C adoption.
Native/live use separately needs selected-path/FP/uniform-error/source-completeness/
authority/resource/consumer evidence. No acquisition, code, imports, new runs, owner/
adapter/log/data/teacher/dependency/hardware work follows. Recommend A; review and
explicit claim/premise/evidence or next design-only scope decisions remain blocked.


#### NF1 Target-to-Cell Typed Join Contract (2026-11-05)

The user explicitly approved this next **design-only** contract after §136,
keeping claims unaccepted and authorizing no code or runs. [Review §137][sinc-target-join-review]
records the actual clean `320ef85` baseline and unchanged tested source. This is
a candidate interface/guard/publication/budget contract, not an implementation,
execution renewal, mathematical claim, Route C adoption or consumer qualification.

**Boundary and Conditional Meaning.** Proposed additive private helper
`_check_synthetic_sinc_target_cell_join(expected_q_word, candidate_record,
enclosure_record, *, synthetic_test_only=False)` and separate
`_SYNTHETIC_TARGET_JOIN_BITS`, default 65,536. Inputs are the complete existing
23-field candidate and 20-field enclosure, not external target/composition reports,
word/status/digest attestations, an owner, log, callback or oracle. Retain exact
expected finite u64 q, sign and typed complete records. Domain and target remain
real-pi sinc at stored q, |q|<=1/64. Both zeros stay separate; nonzero subnormals
cannot enter the zero branch. Old helpers, ASTs/order/caps, defaults, wire and
artifacts must remain unchanged; current composition accepts no target report.

The candidate certificate alone is not target evidence, and the composition report
has no stages. The join must retain the original complete enclosure stages/root
and candidate certificate before either call. Proposed order: one target-content
call, then at most one existing composition call. Each gets independent owned
copies of the retained records; neither receives a previous callee's mutable input
or an external report. The join calls no producer, decoder, Fraction/native trig,
reference, owner or adapter, and no binding/cell checker directly. Composition
retains its existing single binding and series-only cell calls.

Under separately accepted TC/CO/binding/cell/math/runtime/ownership premises,
successful series could connect F(q) in I to the exact certificate's whole-interval
RN64 cell. Zero could connect F(0)=1 to the separately checked unit word and
declared zero binding, without claiming a pure-cell check. Neither implication is
adopted here. No installed native sinc parity, source authority, model/task quality,
resource/totality or consumer benefit follows from a diagnostic join profile.

| Boundary | Proposed Check / Join | Stop or Unaccepted Premise |
| --- | --- | --- |
| TJ0 / entry and retained limits | Literal opt-in; exact finite u64 expected q and complete builtin input profiles. Snapshot distinct join-raw, target, composition-raw, binding and applicable cell limits before any call; all active values exact nonboolean ints in 1..65,536. | Invalid/increased/malformed limits stop without delegation. Zero cell limit is None/not read, not a checked zero or borrowed series limit. |
| TJ1 / guarded ownership | Validate every key/type/length/raw integer/string selector, work/certificate/stage container before copying or equality. Retain owned candidate/enclosure, original certificate, interval, stages, ratio/domain/branch/profile and expected word/sign. Build separate target and composition input copies. | No unrestricted deepcopy, caller hooks, shared mutable callee inputs or concurrent-caller snapshot guarantee. Serialized ownership/builtin behavior remain premises. |
| TJ2 / target call | Reserve one target entry before direct delegation to the existing target-content checker. Recheck all active limits after return. Validate exact current 25-field success or 16-field unresolved profile before lookup/copy/join; unresolved stops before composition. | Target's conditional math/trusted-base proof and selected loaded-call identity remain unaccepted. Fixed report shape or counters are not authenticity. |
| TJ3 / target correspondence | Exact expected q/sign/ratio/domain/target/branch/profile/root interval/all six series stages, or empty zero stages, match retained enclosure. Revalidate target-input schema and compare its complete owned contents to the retained enclosure after the call. | Changed stages with unchanged interval/word/status reject. Persistent callee-input mutation rejects; temporary mutation/restoration or faithful execution is not certified. |
| TJ4 / composition call | Only after complete target correspondence reserve one composition entry. Use independent candidate/enclosure copies. Recheck all active limits; validate current 23-field success or 16-field unresolved composition profile and nested configuration/work. | Composition's declared binding and independent cell argument remain conditional. No direct extra binding/cell call or target oracle. |
| TJ5 / full typed series join | Retained input certificate, composition-input certificate and returned composition certificate agree across all eight fields. Root interval equals retained enclosure, target and composition intervals, and certificate interval. Typed q/sign/ratio/branch/32-8 profile agree throughout. | Word/status/hash-only equality, normalized numeric aliases, partial certificates, stale reports and a different interval with the same word reject. |
| TJ6 / zero and post-call inputs | Zero certificate has exactly word/interval/branch, word 0x3FF0000000000000, interval [1,1], branch zero. Composition has binding entry one, cell entry zero, cell work None. Revalidate both composition-input schemas and compare complete contents to retained records. | No eight-field pure-cell fiction, cell-cap read, midpoint/neighbor claim or nonzero-to-zero substitution. Mutated work/stages/inputs cannot bypass the retained joins. |
| TJ7 / work and limits | Target and composition attempt/work remain distinct, nested binding/cell work retained separately. Saved limits rechecked before/after each call and immediately before publication; no raising, summing, retry, refund or hidden refinement. | Reported logical work is not independently measured runtime cost; setup/guard/copy/GCD/allocation/caller work and transient mutation stay outside counters. |
| TJ8 / publication and errors | Publish complete fresh owned target/stage/certificate evidence only after both successful profiles, all exact joins and final limit checks. Ordinary private join stops omit all evidence; unexpected/allocation/interruption errors propagate. | No universal return, rollback or enforced atomic update. Successful allocation and stable selected functions/ownership remain premises. |
| TJ9 / claim separation | Five false flags and native/motion/source/work unresolved, consumer ineligible; no target-to-cell adoption by this design. Zero and series have separately named diagnostic statuses. | Mathematical/proof/CT/SR/native/source/work/resource/totality/Route C/consumer decisions remain separate; Task 6/9 and hardware/data gates stay blocked. |

**Exact Report Profiles.** Target success is currently 25 fields: sixteen fixed
diagnostic keys plus q_word/sign/q_ratio/target/domain_ratio/branch/profile/interval/
stages. Its reason is independent_declared_stage_content_only; zero and series
statuses are checked_declared_mathematical_zero_content and
checked_declared_mathematical_sinc_content. Work has seven exact fields and
configuration five. Require the saved target bit limit and fixed 256/512/512/256
ceilings; typed success counts retain §136's zero/series ledger. max_result_bits
is bounded by that saved cap, not asserted equal to a sampled maximum.

Composition success is currently 23 fields: the same sixteen diagnostic keys plus
q_word/sign/q_ratio/branch/profile/interval/certificate, no stages/target/domain.
Its status/reason is checked_declared_zero_binding/declared_zero_binding_only or
checked_declared_binding_and_cell_content/declared_binding_and_exact_cell_content_only.
Configuration has raw_copy_bit_limit/binding_bit_limit/cell_bit_limit, exactly
matching the saved applicable limits. Work has composition_entries/binding_entries/
cell_entries/binding/cell; success has 1/1/0 or 1/1/1 entries. Binding work is five
fields, series cell work six; zero cell is exactly None. Preserve their existing
canonical/decode/comparison/construction/midpoint schemas and typed success ledgers.
No producer cell-work schema or fabricated root word/interval may be substituted.

All returned records require builtin exact key sets/types, selectors, false flags,
unresolved/ineligible statuses and guarded integer/rational/container leaves before
equality or owned traversal, including revalidated post-call input records. A
callee success is necessary, not sufficient; original all-stage/root/certificate
content correspondence is the join's obligation. An unresolved callee may contribute
owned attempted-work metadata but no partial target/certificate/stage evidence.

Proposed new fixed root has sixteen diagnostic fields: identity/allowed_use/status/
reason/configuration/work, five false flags and five unresolved/ineligible statuses.
Success adds ten: q_word/sign/q_ratio/target/domain_ratio/branch/profile/interval/
stages/certificate (26 total), never a root word or decision. Proposed identity
synthetic_sinc_target_cell_join_v0, allowed use
isolated_synthetic_sinc_target_cell_join_only. Proposed series status
checked_conditional_sinc_target_cell_content; zero
checked_conditional_zero_target_binding; otherwise
unresolved_synthetic_sinc_target_cell_join. These are proposed diagnostic names,
not accepted mathematical or native rounding claims.

Configuration has five keys: raw_copy_bit_limit/target_bit_limit/
composition_bit_limit/binding_bit_limit/cell_bit_limit. Work has five keys:
join_entries/target_entries/composition_entries/target/composition. A complete
success has entries 1/1/1, with fresh target work and existing composition work
including its binding/cell work. The raw join cap cannot relax any callee limit;
each active cap is snapshotted and rechecked independently. Zero cell configuration
is None. Counters reserve before delegation, including failed attempts, with no
refund or counters masquerading as native/trusted-base/resource evidence.

| Gate | Required Separate Review / Decision |
| --- | --- |
| JI0 | Exact TJ/input/25-target/23-composition/26-join/zero profiles and post-call raw guards. |
| JI1 | Owned immutable evidence and separate callee copies; precise typed full-stage/root/eight-field or zero certificate join. |
| JI2 | Conditional TC/CO/binding/cell/math/runtime premises and F(q)-to-cell implication; no native or source authority claim. |
| JI3 | Independent limits, reserved delegation, nested work/profile guards and publication/exception argument. |
| JI4 | Fixed JX controls/map/faults, fixture ordering/counter protocol and explicit affected/default gate renewal. |
| JI5 | Preserve old source/test ASTs/caps/defaults/wire/artifacts and all false/unresolved/ineligible flags. |
| JI6 | Shared canonicalization/builtin/selected binding/ownership/math/evidence and requalification decisions. |
| JI7 | Explicit narrow claim acceptance and separate consumer decision, if ever sought; no implicit Route C/resource/totality adoption. |

**Fixed Future Prototype Proposal, Not Approval.** Reuse the complete existing
twelve-slot capture and the exact map `(0,1,2,3,4,5,6,7,8,9,10,11,6,7,8,9)`.
Sixteen join controls, exactly two join attempts each: ordinary plus one fixed
second request; no hidden third attempt or variant. Old direct target/composition/
binding/pure-cell matrices and the default root gate require explicit renewal.

| Control / Slot | Fixed Second Request / Required Outcome |
| --- | --- |
| JX0 / 0 | False opt-in raises before any target/composition call. |
| JX1 / 1 | Integer opt-in raises; ordinary negative zero retains sign, no cell attempt. |
| JX2 / 2 | Remove enclosure stages key; raw-schema rejection before either call. |
| JX3 / 3 | Flip expected zero sign bit; reject equal-ratio/opposite-word input before delegation. |
| JX4 / 4 | Replace candidate-work enclosure key with a same-hash hostile key; reject before equality hook/delegation. |
| JX5 / 5 | Set join-raw limit to 65,537; configuration rejection without changing old limits. |
| JX6 / 6 | Target return hook changes only pi lower stage endpoint to (3,1); retain root interval/status, reject before composition. |
| JX7 / 7 | Target return hook adds certificate key to its 25-field report; schema rejection before composition. |
| JX8 / 8 | Target hook mutates its owned input pi after successful target calculation, returns unchanged success; post-call input join rejects before composition. |
| JX9 / 9 | Composition return hook changes certificate lower boundary to (1,1), retaining word/root interval; full eight-field join rejects. |
| JX10 / 10 | Composition return hook adds stages key to its 23-field report; schema rejection. |
| JX11 / 11 | Target return hook changes saved binding cap to one; reject after target and before composition. |
| JX12 / 6 | Set join-raw bit limit to one; guarded rejection without refinement/delegation. |
| JX13 / 7 | Composition return hook changes saved target cap to one; post-call/final live-limit rejection. |
| JX14 / 8 | Scoped target-delegation hook raises MemoryError before original target body; reserve attempt, propagate, no composition/evidence. |
| JX15 / 9 | Repeat, then independent input/output/stage/certificate/nested-work mutations preserve saved first result and pool; no third request. |

Hooks are bounded test-only controls, not a runtime callback/report interface.
JX14 tests attempted target delegation/MemoryError, not original target-body work,
interruption or transaction guarantees. No producer/capture/cell-producer interception
inside the join, extra q/scenes, new truth or persistent payloads.

Future new counting fixture must own call-family wrappers before the old target
and composition fixtures activate, and place the new join matrix before their
direct matrices in each named invocation and default collection. Reuse one shared
capture; reserve before every actual target/composition/binding/pure-cell delegation.
New outer totals distinguish join-induced and old direct entries. Keep the old
target fixture's 32 direct-entry and old binding/cell wrappers' 64-entry caps
unchanged. Install new family wrappers first; the old fixtures then wrap those
wrappers for their old direct subsets. The first join matrix runs before those
old subset wrappers activate. No bypass through __wrapped__, uncounted helper,
refill, fixture reset, worker or ordering after old
direct fixtures are already active. If ordering/complete pool/counter ownership
cannot be established, abort; revise the proposal explicitly rather than raise a cap.

Per complete invocation proposed named ceilings: 32 join/64 target/64 composition/
96 binding/96 pure-cell. Existing direct target/composition account for 32 each;
join nested calls account for at most 32 each. Binding/cell include all nested and
direct entries, not just successful bodies. Capture remains 12 candidate/24
enclosure/12 nested producer-cell/24 snapshots. At most five invocation positions,
including failed probes/repairs/root gate: 160 join/320 target/320 composition/
480 binding/480 pure-cell, capture 60/120/60/120. These ceilings are an unapproved
counter proposal, not observed telemetry, success headroom or resource qualification.
Existing default controls are separately renewed historical gates, not an exhaustive
whole-root/native-work ledger. Failure/cancellation spends entries/positions without
replacement; payloads remain invocation-memory-only.

For a complete successful series join, target logical work is 24 canonical checks/
1 decode/147 power steps/230 constructions/131 rational operations/57 comparisons;
composition remains 42 canonical checks/4 decodes/2 midpoints/48 constructions/
11 comparisons across binding/cell, with one binding/one cell entry. Zero target
is 4/1/0/5/0/2; composition is ten canonical checks/one decode/eleven constructions/
two comparisons and one binding/no cell. Do not replace either nested ledger by
the other or add their bit limits. The join's own raw validation/copy/equality/
publication and all runtime/allocator work are separate, not zero. No Fraction/
native arithmetic is added by the proposed join and no complete resource bound
is inferred from these conditional logical counts or future entry ceilings.

Next decision: approve/modify this bounded private join prototype with the exact
JX map/faults/limits/fixture-order protocol and affected/default gate renewal, or
retain design-only isolation. No implementation/import/run/budget renewal or
claim/premise/proof/allowance/Route C/totality/consumer adoption follows here.
Old §129/§132 budgets remain exhausted and the unused §135 fifth position is not
spent or transferred. Task 6/9, native motion/goals/relative transforms, source
completeness/authority/work, physical/task evidence, teacher assets, dependency/
data and ST/board gates remain unchanged and blocked.


#### NF1 Private Target-to-Cell Join Prototype (2026-11-05)

The user approved §137's private join prototype, exact JX map/faults/caps/counter
protocol and affected/default gates under five new invocation positions, retaining
unaccepted claims. [Review §138][sinc-target-join-prototype-review] records four
used positions and the unused fifth. Old §129/§132 allowances stay exhausted;
§135's unused position was not borrowed. No further unchanged gate is planned.

The additive private `_check_synthetic_sinc_target_cell_join` retains distinct
join/target/composition/binding/applicable-cell limits before delegation. Its
separate raw cap defaults to 65,536. Complete builtin candidate23/enclosure20
guards precede fixed owned snapshots; retained original stages/root/certificate
and independently owned target/composition inputs are never external reports.
One reserved target call precedes at most one reserved composition call. Exact
25/23-field reports, their work/configuration, all expected q/profile/stage/root
and full certificate content are checked and snapshotted. Both callee inputs are
revalidated and compared to retained complete contents after their calls.

The sole final publication has 26 complete diagnostic fields; unresolved results
have only sixteen fixed fields. Zero has separate status and exact unit/[1,1]/zero
certificate, no cell call/work/limit claim. Series retains the eight-field cell
certificate. Saved limits are checked after calls and before publication. Only
JoinStop is caught; unexpected/allocation/interruption errors propagate. No
Fraction, producer, decoder, native trig, owner/reference/log adapter or direct
binding/cell call is added; composition's existing nested calls remain unchanged.

New family wrappers activate before old target/composition fixtures, with the
join matrix first. The old fixtures wrap them for old direct subsets; all old
ASTs/order/caps remain exact. An observer of the existing old reservation journal
records its injected pre-body cell MemoryError, already reserved by that old
wrapper but not delegated to the inner family wrapper. This reconciles attempted
entries, never invokes another helper, raises an old cap, resets a fixture or
bypasses __wrapped__. Its scoped marker is removed at teardown; standalone old
tests without the join fixture do not activate the observer's dependencies.

All sixteen fixed JX controls use exactly two join attempts and one shared capture.
The final full-matrix ledger is 32 joins, 57 target, 52 composition, 77 binding,
62 pure-cell attempts. Join-induced entries are 25/20/20/14; old subsets are
32/32/57/48. One old pure-cell reservation is pre-body MemoryError, not an original
checker-body execution. Capture uses 12 candidate, 24 enclosure, six actual nested
producer-cell entries and 24 snapshots. These are diagnostic attempted-entry
ledgers, not all root-suite execution, native/resource evidence or new task data.

Five flags false; native/motion/source/work unresolved and consumer ineligible.
The join implements conditional-content plumbing, not mathematical/proof/Route C/
totality/source/native/resource or consumer claim acceptance. Current defaults,
wire, artifacts, quarantine and `1bb89fe` are preserved. Next authorized preparation
is the same-helper conditional correctness/publication/work and claim/premise/
evidence decision review, without project imports or additional runs. No runtime/
owner/wire integration, task collection/labels, teacher/dependency or hardware
authorization; Task 6/9 and all broader qualification gates remain blocked.


#### NF1 Target-to-Cell Conditional Correctness and Work Review (2026-11-05)

Following §138's approved private prototype and autonomous continuation, this
same-helper review prepares a conditional argument and decision brief only.
[Review §139][sinc-target-join-paper-review] pins `8bf26d3`, records static checks
and preserves the four-position ledger and 2,245-pass source gate. No project
import, helper/fixture/native execution, new source edit, acquisition or adoption.
The unused fifth position is not spent on reassurance or transferred to new work.

**Conditional Statement.** Fix a builtin finite stored word u, its exact signed
dyadic q with |q|<=1/64, complete candidate23/enclosure20 records, and literal
synthetic opt-in. Assume faithful builtin integer/container operations, exact
Fraction/GCD canonicalization, stable selected helper/configuration bindings,
serialized input/report ownership, ordinary successful allocation/publication,
and the mathematical/partial-correctness premises of the target (§136), declared
binding (§130), pure-cell (§126) and composition (§133) reviews. If the pinned
join returns its complete 26-field checked success, its published interval I
contains F(q), and I is contained in the exact binary64 ties-even cell C(w) of its
certificate word w. Hence RN64(F(q))=w. For either signed zero, F(0)=1 and w is the
positive unit word; sign remains q metadata, not a signed sinc output or native
tiny-branch result. No claim/premise/proof acceptance is implied by this review.

The implication is transitive whole-interval containment, not an empirical
word match, status/hash inference or endpoint-sampling argument. Unsupported or
straddling cells, invalid domain/configuration/content and ordinary guard stops
remain unresolved. A supported success implication does not promise success or
return for every finite q, an installed NumPy result, physical evidence or a
qualified consumer. The join calls existing checkers; it does not independently
rederive their mathematical theorems or attest their selected live implementations.

| Obligation | Conditional Local Argument | Premise or Limit Still Open |
| --- | --- | --- |
| JO0 / entry and limits | Literal opt-in precedes setup. Four always-active and one series-only limits are retained before delegation; exact nonboolean values lie in 1..65,536. Zero's cell limit is None and not read. Invalid configuration returns fixed unresolved metadata. | Multiple reads are not atomic or a detector for a transient change restored between checks. Stable bindings/serialized execution remain assumptions. |
| JO1 / schema before traversal | Complete builtin candidate/enclosure/profile/work/stage/certificate shapes and integer/string/bool leaves precede ownership/cross-record equality. Hostile work keys stop before lookup/membership equality hooks. | Raw pair shape is not canonicality or mathematical content; later faithful checkers supply those obligations. Input allocation and container implementation remain trusted. |
| JO2 / retained content and independent inputs | Original certificate/stages/root/ratio are retained from owned records. Target and composition receive distinct owned inputs; no external report is an API input. Initial ratio/root/work correspondence fixes the submitted content. | Validation-to-copy and report ownership are serialized premises, not enforced concurrency control or source authenticity. Producer work metadata is declared, not authenticated execution. |
| JO3 / target before composition | Target attempt is reserved before its call, followed by live-limit checks, exact 25-field report/work/config guards and independent report ownership. Post-call target input schema and full content must match retained enclosure; q/sign/profile/domain/target/all stages/root must join exactly. | §136's mathematical and trusted-base conclusions are conditional. A complete report with matching counters is not independent live-callee authority or a substitute for them. |
| JO4 / composition correspondence | At most one composition attempt follows accepted target content. Exact 23-field report/nested work/config is validated and owned; both composition inputs are revalidated and equal retained candidate/enclosure. Expected q/sign/ratio/profile/root and complete certificate equality are required. | Existing binding/cell premises and selected callees remain unaccepted. No source anchor, producer transcript, native oracle or runtime consumer is added. |
| JO5 / target-to-cell implication | Target provides F(q) in I. Composition's same full certificate/root gives I in C(w), using pure-cell neighbors, midpoints, parity/ties/orders and whole-interval containment. Equality of all linked intervals yields RN64(F(q))=w. | The real-pi analytic/interval and exact ties-even-cell arguments must be explicitly reviewed/accepted separately; structural equality alone cannot prove either theorem. |
| JO6 / zero separation | Exact expected word and sign joins retain both zeros; target has [1,1]/empty stages and composition has unit/[1,1]/zero certificate. No pure-cell call, work or cap is claimed. | Sign is input metadata. Mathematical F(0)=1 does not qualify the installed wrapper's tiny substitution, floating divide or source evidence. |
| JO7 / publication and exceptions | Final live checks precede fresh success content/work publication. Ordinary JoinStop returns only sixteen fixed metadata fields, never stages/certificate. Unexpected/allocation/interruption errors propagate. Callee reports/work are owned before later use. | No universal return/rollback/transaction guarantee or arbitrary side-effect suppression. JX14 injects MemoryError before target body, not interruption or every publication allocation site. |
| JO8 / attempted entries and harness | Join reserves target/composition entries before calls; composition keeps its own binding/cell reservations. New family wrappers precede old wrappers; old direct subsets stay separate. Legacy pre-body cell MemoryError was already reserved by the old wrapper and reconciled from its journal. | Bookkeeping is not original-body telemetry; late reconciliation does not move the old reservation in time. No fixture refill, old cap increase, wrapper bypass or resource evidence. |
| JO9 / work and claim separation | Successful report counts are exact profiles; zero/series limits and nested work remain separate. No new Fraction work is performed in the join, no sum of caps/retry/refund/precision escalation. Five false flags and unresolved/ineligible statuses persist. | Setup/raw/copy/equality/caller/GCD/runtime/allocator and live work are not measured. JI/CT/W0/TB0, native/source/resource/totality/Route C and consumer acceptance stay open. |

**Conditional Successful Work Ledger.** These sums describe logical counters of
one ordinary successful path through faithful existing helpers, not §138's family
attempts, all default-suite execution or primitive/native/resource work. Constructors
are reserved before Fraction calls; rejected preflight work and exceptions may
leave only a prefix or no returned report. Composition includes binding plus the
series-only pure-cell checker. Do not count those nested paths twice.

| Branch / Component | Canonical Pair Checks | Dyadic Decodes | Power Steps | Fraction Constructions | Target Rational Operations | Rational Comparisons | Midpoint Recomputation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Series target | 24 | 1 | 147 | 230 | 131 | 57 | 0 |
| Series composition, binding + cell | 42 | 4 | 0 | 48 | 0 | 11 | 2 |
| Series combined | 66 | 5 | 147 | 278 | 131 | 68 | 2 |
| Zero target | 4 | 1 | 0 | 5 | 0 | 2 | 0 |
| Zero composition, binding only | 10 | 1 | 0 | 11 | 0 | 2 | 0 |
| Zero combined | 14 | 2 | 0 | 16 | 0 | 4 | 0 |

The zero/series path reserves one join, one target, one composition and one binding;
series additionally reserves one pure-cell entry. The join itself adds no Fraction
constructor, decode, midpoint, power or numerical rational operation counter.
Its tuple/key/integer guards, immutable comparisons, owned traversal, nested report
validation and fresh publication are still work, not free or bounded by that table.
Composition's zero in the target-operation column means no counter of that kind,
not no integer arithmetic: its decodes/midpoints/cross-products/GCD still occur.

Binding series36 plus cell12 gives composition48 constructors; zero binding11.
Target147 power steps are130 arctangent powers plus17 factorial steps. Its 131
operation count is separate from 57 comparisons and 230 constructors (§136).
The full entry ledger retains join-induced25/20/20/14 versus old32/32/57/48;
one old cell reservation never entered the original body. Printed aggregate cell186
versus journal-supported187 in §138 remains historical, not rewritten telemetry.

The separate five limits are not summed into a memory or arithmetic allowance.
The raw join cap also guards metadata integers; reduction can reject a valid
larger-profile record before delegation. max_result_bits covers accepted canonical
outputs of callees only; the observed target maximum13,146 is not all-domain,
raw/live/intermediate/peak RAM or a smaller certified cap. Stable builtin/Fraction/
GCD/code selections, allocation, input/callee-report ownership and serialized
execution remain shared premises. No new installed-source inspection or measurement.

**Concrete Decision Brief.** A/default: retain isolation and accept no claim,
including the implication above; all flags/statuses and absent eligible consumer
remain. B: separately accept only the explicitly conditional stored-word
RN64(F(q))=certificate-word/content statement for this pinned private join, after
reviewing JO0-JO9 and each upstream mathematical/builtin/Fraction/GCD/binding/
ownership/exception premise and deciding admissible implementation evidence.
Neither route approves source/native/runtime/physical/consumer use or changes flags.

Before B, proposed acceptance checks are the exact finite-word/domain/profile/
input/success/zero scope; target reconstruction/real-pi/tail and pure-cell tie
arguments; complete raw guard/owned post-call/certificate/root/limit/publication
review; independent selected-implementation and shared-premise decisions; separate
logical/attempt/resource ledgers; and a recorded narrow claim with exclusions.
Source/schema/profile/cap/runtime/canonicalization/helper-selection/ownership/math
changes invalidate this review and require separate affected-evidence/gate decisions,
not automatic reruns. Hashes pin bytes, not loaded code, source authority or sensors.

If claim decisions are deferred, a concrete next design-only candidate is one
JO0-JO9/upstream-premise and admissible-evidence worksheet in these existing records:
map each conditional dependency, proposed accept/stop/invalidation condition and
remaining evidence gap using existing project records only. No installed-source
refresh, imports, fixtures/runs, acquisition, code or claim adoption. Exit: every
obligation has a named premise/evidence boundary and explicit undecided verdict;
no counters, hashes or historical tests promoted to proof. This preparation is
proposed, not authorized by the completed review; isolation remains the default.

This review exhausts the authorized same-helper preparation. Only explicit claim/
premise/admissible-evidence decisions, or a separately approved next design-only
scope, remain. Recommend A; no new code, imports/runs, acquisition, native/source/
work/resources/consumer integration, owner/wire/log/data/teacher/dependency/hardware
work follows. Task 6/9 and all broader qualification gates remain blocked.


#### NF1 Join Premise and Admissible-Evidence Worksheet (2026-11-05)

The user explicitly approved §139's next design-only worksheet: JO0-JO9/upstream
premises, candidate admissible evidence and proposed accept/stop/invalidation
conditions, using existing project records only. [Review §140][sinc-join-worksheet-review]
records the clean `78328d2` baseline, scoped checks and unchanged §138 source gate.
This prepares a decision, not evidence/claim adoption or a source/runtime change.

**Scope and Status.** The sole candidate conclusion is §139's conditional
stored-word RN64(F(q))=certificate-word/content statement, with its exact finite
q/domain/profile/success/zero scope and exclusions. Five upstream families below
cover all dependencies used by that argument; JO rows reference them explicitly.
Every verdict is **undecided**. Candidate evidence is either an already-recorded
argument/test/identity with stated limits, or a proposed future review criterion,
not newly obtained evidence or permission to obtain it. No proposed accept condition
is met or adopted merely because this worksheet exists.

| Premise Family | Existing Project Record / Candidate Evidence | Proposed Accept Condition | Stop / Invalidation Boundary | Verdict |
| --- | --- | --- | --- | --- |
| U0 / mathematical target | §136 TC0-TC9: exact signed dyadic/domain/zero, decreasing arctangent sums, Machin identity/quadrant, positive squared interval, factorials, whole Horner enclosure and alternating-tail/root argument; §135 fixed tests are supporting controls only. | Explicitly decide each quantified mathematical/partial-correctness premise, or retain it as an openly assumed premise of the narrow implication. Samples/brackets alone cannot establish those theorems. | Missing analytic or guard/canonicality premise blocks an accepted unconditional conclusion; q/profile/kernel/theorem changes require a new decision. No native error follows. | undecided |
| U1 / declared binding | §130 BR0-BR9 and §129: exact builtin finite q/sign/ratio/domain/profile/canonical pairs and complete record correspondence, including zero; fixture companions are owned declared records, not a producer transcript. | Explicitly accept only conditional declared correspondence under its guarded integer/Fraction/GCD assumptions; distinguish expected-word content from its authority. | Hash or copied report cannot replace correspondence; mutated schema/q/profile/canonicalization/ownership invalidates it. No source execution/authority inference. | undecided |
| U2 / exact cell | §126 CCR0-CCR9 and §125: complete eight-field series certificate, three neighbor decodes, exact midpoints/order/parity/ties and whole interval containment; zero three-field certificate is outside that checker. | Decide the exact finite-neighbor/ties-even-cell partial-correctness argument and its integer/Fraction assumptions, not just endpoint tests or the reported word. | Unsupported/straddling cell or missing boundary/parity/canonical premise stops the implication; word/certificate/cap/decoder changes invalidate it. No search totality. | undecided |
| U3 / composition | §133 CO0-CO9 and §132: one binding, series-only cell, complete typed original/binding/cell-input/cell-output certificate and common interval, separate saved caps and owned publication. | Accept only the conditional composition of U1/U2 and complete content joins with its input/report/helper/publication premises explicit. | External stale report, missing join or unresolved callee blocks accepted composition; helper/profile/schema/cap/ownership change invalidates it. Zero remains no-cell. | undecided |
| U4 / shared execution and work base | §107 historical trusted-base dossier plus §126/130/133/136/139: builtin integer/container and Fraction/GCD semantics, stable selected helpers/configuration, serialized ownership, ordinary allocation/publication, exception prefixes; §138 byte IDs/gates identify checked source, not live selections. | Decide which assumptions are explicit conditions of the narrow theorem and what independent correspondence/ownership evidence would be admissible for any stronger implementation claim. No such new evidence is obtained here. | Missing live/native/allocator/source authority leaves stronger claims blocked; runtime/binding/GCD/copy/cap/publication changes invalidate correspondence. Counts/max bits never become RAM/time/native-work proof. | undecided |

U0-U3's source reasoning depends on U4 where it invokes builtin/Fraction/GCD,
ownership, helper selection and ordinary completion. U3 also depends on U1 and
series-only U2. Historical §107 provenance/text observations are not refreshed
loaded-image/ABI/build/FP evidence; no installed file is inspected by this worksheet.
The distinction between an explicit conditional assumption and established evidence
must remain in any eventual claim. Accepting a theorem conditional on U4 does not
demonstrate U4 for an actual process, sensor or robot.

| Join Obligation / Dependencies | Existing Candidate Evidence | Proposed Accept Condition | Stop / Invalidation Boundary | Verdict |
| --- | --- | --- | --- | --- |
| JO0 / U4 | §138/139 source/AST: literal opt-in, separate saved five limits and zero cell None; fixed JX5/11/12/13 limit controls. | Decide exact entry/applicable-limit/stable-read scope; require all active saved-limit checks, not a sum of caps. | Missing limit/type/live check stops; transient changes between reads remain outside detection. Opt-in/configuration/serialization changes invalidate review. | undecided |
| JO1 / U0,U1,U2,U4 | Complete root/profile/work/stage/certificate raw builtin guards precede copy/equality; JX2/4 missing-stage/hostile-work-key controls. | Accept only raw shape/hook rejection plus later U1/U0/U2 canonical/content checks, not shape as mathematical evidence. | Missing nested guard or nonbuiltin leaf stops; container/schema/canonicalization changes invalidate. Pre-existing allocation is not counted work. | undecided |
| JO2 / U1,U4 | Retained original records and separate target/composition copies; JX15 saved-result/input/work mutation checks. | Decide validation-to-copy and private serialized ownership conditions, distinguishing retained contents from source authenticity. | Aliasing/concurrent mutation or absent complete snapshot blocks the stronger ownership claim; copy/ownership/helper changes invalidate. | undecided |
| JO3 / U0,U4 | Target-first reserved call, exact report/work/config and owned post-call stage/root/input joins; JX6/7/8/14 controls. | Combine accepted or explicitly assumed U0/U4 with exact same-q/profile/domain/all-stage/root content and post-call input checks. | Unresolved/missing/mutated target report/input stops composition; matching counters alone cannot repair a missing premise. Target/helper/math/profile changes invalidate. | undecided |
| JO4 / U1,U2,U3,U4 | Composition report owned; both inputs and complete certificate/root match retained originals; JX9/10 boundary/schema controls. | Combine U3 and applicable U1/U2/U4 with all same-q/profile/root/eight-field or zero joins. | Word/status/hash-only, stale report or input mutation stops; changed composition/binding/cell/schema invalidates. No eligible consumer emerges. | undecided |
| JO5 / U0,U2,U3,U4 | §139 transitive F(q)-in-I-in-C(w) argument; exact linked intervals and full certificate checks in §138. | Explicitly accept the conditional implication only if each upstream premise/condition is named; retain exact ties/parity/whole-cell and success-only scope. | Missing target or cell theorem blocks accepted RN64 conclusion; sample agreement cannot fill it. Target/cell/rounding meaning changes invalidate. | undecided |
| JO6 / U0,U1,U3,U4 | Signed zero metadata, empty stages, unit/[1,1]/zero certificate and no cell work/cap; JX1/3 controls. | Decide mathematical F(0)=1, expected sign and no-cell branch without inferring a signed output or native tiny substitution. | Zero/subnormal/sign/profile aliases stop; changed zero definition/checker branching invalidates. U2 is not invoked on zero. | undecided |
| JO7 / U3,U4 | Complete 26-field update after final live checks; sixteen-field ordinary stops; owned reports; only JoinStop caught. | Accept only ordinary successful publication and propagating exceptional prefixes, with no universal return/rollback/side-effect guarantee. | Unexpected/allocation/interruption means no promised report; JX14 is not coverage of every site. Publication/catch/copy semantics changes invalidate. | undecided |
| JO8 / U4 | §138 first-installed family wrappers, disjoint join/old phases, old primary reservation journal and pre-body reconciliation; exact old AST/caps. | Decide named attempted-entry accounting only; preserve printed-versus-derived totals and old reservation timing. | Missing reservation/order/journal correspondence blocks ledger acceptance; new calls/refill/wrapper bypass/cap changes invalidate. No original-body or resource telemetry inferred. | undecided |
| JO9 / U0,U1,U2,U3,U4 | §139 conditional zero/series sums, nested paths counted once, unchanged five flags/unresolved statuses and retained source gate. | Decide logical/profile counters separately from attempted entries and resource/evidence/consumer claims; no bit-cap sum or measured-cost claim. | Omitted setup/GCD/allocator/live work blocks resource conclusions; ledger/profile/cap/qualification changes invalidate. Larger success scope or flags need separate approval. | undecided |

**Admissibility Boundaries.** Byte IDs identify the exact local source/text; they
are not authenticated loaded helper/Fraction/GCD selections. Fixed synthetic tests
exercise only the stated cases and exception sites, not quantified mathematics,
native error, physical domain, source completeness or all-domain termination.
Paper algebra and AST checks support a reviewable conditional argument; they are
not machine-checked proofs or accepted evidence policies. The attempted journal
and successful work table answer different questions; neither measures resources.

Any later decision must explicitly say whether it accepts a conditional premise,
an evidence type for a named claim, or the narrow conclusion. These are distinct
decisions; none implies the others or changes source/flags. If a premise stays
undecided, the corresponding stronger conclusion remains unaccepted; retaining an
assumption explicitly permits discussion of the conditional argument only, not
actual process qualification. No automatic adoption, relabeling or new execution.

**Exit and Remaining Decision.** U0-U4 and JO0-JO9 all have explicit dependencies,
candidate evidence/limits, proposed accept/stop/invalidation criteria and undecided
verdicts. The approved design-only preparation is complete. Default/recommendation
remains private isolation and no claim/premise/evidence-policy adoption. The next
missing input is an explicit named premise/admissible-evidence/claim decision or
a separately authorized concrete evidence direction, not more routine code or
an unchanged gate. Native/source/work/resources/consumer and Task 6/9/physical/
task-quality/teacher assets/ST-board stay blocked; no data, runtime, teacher,
dependency, hardware or acquisition authority follows from the worksheet.


#### NF1 Process-Local Binding Identity Evidence Boundary (2026-11-05)

The user kept claims unaccepted and separately approved a bounded U4 identity-only
audit: one process importing diagnostics to record four checker/Fraction bindings
and source hashes, no checker calls/fixtures/numerical comparison or claim adoption.
A second, corrective identity-only process was separately approved after the first
probe's metaclass assertion failed. [Review §141][sinc-binding-identity-review]
records both attempts and the successful metadata, not a renewed source gate.

The evidence boundary is an identified process's module namespace, function/code
metadata, source-file and marshalled-code-object digests, Fraction module binding
and metaclass, plus repeated binding/file-hash checks across its metadata span.
These distinct observations are not interchangeable: a source hash identifies
file bytes, a code-object digest identifies a Python-version/path-sensitive
serialization, and object IDs distinguish references within that process only.
Reported filename/origin/loader and absent __wrapped__ attribute do not establish
source-to-loaded-code correspondence or absence of arbitrary interception.

Canonical class identity is not an exact-metaclass requirement: the observed
Fraction binding is fractions.Fraction with abc.ABCMeta. A probe must report its
metaclass rather than assume builtin type; this is an audit correction, not a
change to any checker guard or arithmetic contract. No Fraction constructor or
checker is explicitly invoked by the metadata snippets. Imports execute normal
module/dependency initialization; that is not an all-transitive-call work audit.

Matching references/hashes at two observation points do not detect every transient
mutation, enforce serialized ownership, guarantee future stability or authenticate
runtime selection. They do not prove integer/Fraction/GCD semantics, compiled/native
paths, arithmetic/tie/target correctness, source authority/completeness, termination,
resource fit, physical inputs or consumer eligibility. The join's own binding was
not one of the four inspected function rows. U4 and all JO/upstream verdicts remain
undecided; five flags false and unresolved/ineligible statuses are unchanged.

Both explicitly allowed identity attempts are spent. No further import/snapshot,
source-to-code comparison, numerical/checker/fixture run, source acquisition or
integration follows automatically. The next input is a named premise/evidence/claim
decision or separately approved concrete evidence action; isolation remains default.
Existing task/data/teacher/dependency/hardware gates and §138's source gate stay.


#### NF1 Historical Code-Object Digest Comparison Boundary (2026-11-05)

Following §141, the user separately approved one compile-only process and four
comparisons against its historical code-object digests. The scope is compilation
of the unchanged, pinned diagnostics bytes, not execution of that module or a new
live-binding snapshot. [Review §142][sinc-compile-comparison-review] records the
settings and all four unequal digests; the one-process approval is spent.

The local correspondence hypothesis was that compiling the same source bytes
with the recorded filename under the same reported Python version would reproduce
the four historical serializations. It did not under this attempt's explicit
flags=0, dont_inherit=True and optimize=0 settings. Source/version/filename/first-line
agreement does not substitute for digest equality; no digest-match correspondence
claim is available from this result. A completed comparison is not a passed match.

Unequal marshalled-code-object digests alone do not identify a semantic difference,
wrong source, substitution, corruption or a specific serialization cause. §141 did
not record the full compilation/load/serialization conditions needed to establish
cross-process comparability. No historical code-object bytes or structural fields
were reconstructed, and no new live object was imported or compared. A hypothesis
about serialization, interning, compiler conditions or loading remains unverified.

Any disambiguation must have a separately approved scope, comparison representation,
attempt budget and explicit outcome/stop conditions. It must distinguish structural
code comparison from runtime authority and mathematical correctness; neither can be
adopted through a changed digest method or a successful metadata comparison alone.
No automatic retry, normalization, source change, renewed source gate or claim
adoption follows. All fifteen verdicts remain undecided, the five flags false,
consumer ineligible and broader native/source/work/task/data/hardware gates unchanged.


#### NF1 Proposed Same-Process Structural Comparison Protocol (2026-11-05)

After §142's four unequal historical digests, the user approved **design-only
protocol preparation**, using existing project records. No import, compilation,
fixture, installed-source refresh, method execution or claim adoption is approved.
[Review §143][sinc-structural-protocol-review] records this preparation. The proposed
SC18-v0 representation and future budgets below are not adopted acceptance criteria.

**Question and distinct outcomes.** In a separately approved future process, do the
four fixed §141 checker bindings and corresponding freshly compiled code objects
agree in every declared SC18-v0 field and typed constant? A complete equality result
would establish only agreement in that representation at the observed points.
It would not identify why §141/§142 marshal digests differ, reconstruct historical
objects, establish full interpreter-object equality, prove source authority or
mathematical semantics, or qualify U4. A difference identifies a bounded field path,
not automatically a runtime defect. Unsupported, incomplete or unstable evidence
is a separate unresolved outcome, never equality. Historical unequal digests stay.

**Fixed objects and process plan, not permission.** Propose one explicit diagnostics
import and one compilation in one CPU-only `/opt/venv/bin/python` process; no checker
calls or deliberate Fraction construction. Normal module/dependency initialization
executes on import and is not zero work or an all-transitive no-constructor claim.
Retain only the four exact FunctionType bindings from §141: target content,
composition, declared binding and pure-cell certificate; the join is outside scope.
Require their module namespace and code references, source file and filename, and
first lines 669/1057/1487/1873 to match the declared profile. The source profile stays
271,168 bytes/SHA256 be7f30a1559ef0c49d3992c923788c12a1c9e9d56718a44c1190837649aa5057,
reported Python3.12.3/GCC13.3.0, source filename from §142; no new provenance claim.
Record launch/load settings and compile with flags0/dont_inherit=True/optimize0.
Compile the pinned bytes but never execute that compiled module; select exactly
one top-level code constant for each fixed name. No extra root, fixture or retry.

**SC18-v0 field set.** Check exactly these eighteen proposed public CodeType fields
in this order, including nested code constants. Field availability and exact types
must be checked in the future process; they were not all inspected in §§141-142.

| Field Group | Required Fields | Required Types |
| --- | --- | --- |
| Counts/Flags | co_argcount, co_posonlyargcount, co_kwonlyargcount, co_nlocals, co_stacksize, co_flags | Exact nonboolean integers |
| Instructions/Constants | co_code, co_consts | Exact bytes; exact tuple of supported typed constants |
| Names/Locals | co_names, co_varnames | Exact tuples of exact strings |
| Location/Identity | co_filename, co_name, co_qualname, co_firstlineno | Exact strings; exact nonboolean integer |
| Location/Exception Tables | co_linetable, co_exceptiontable | Exact bytes |
| Closure Names | co_freevars, co_cellvars | Exact tuples of exact strings |

Private/adaptive VM storage, object addresses, reference counts, interning state,
globals/closure values, derived position iterators and execution behaviour are not
represented. Excluding them limits the claim; it does not prove them irrelevant.
No CodeType equality, function evaluation, disassembly or marshal digest is used
as a substitute for the eighteen fields. Missing/type-invalid fields stop; no
field dropping, alternate representation or inferred default to obtain equality.

**Typed constant representation.** Propose exact-builtin None/Ellipsis/bool/int/
float/complex/str/bytes/tuple/frozenset plus exact CodeType only. Each has a distinct
type tag and length-delimited payload; bool never aliases int. Integers use sign
and bounded magnitude bytes, floats their binary64 bits including signed zero/NaN
payload, complex two such components, strings UTF-8 with surrogatepass, and bytes
their literal payload. None/Ellipsis have distinct singleton tags. Tuples preserve
order and every occurrence; frozensets sort the complete tagged child encodings
lexicographically, retaining multiplicity/cardinality of encoded elements rather
than merging equal encodings. Code constants recurse through the same eighteen
fields. Fixed field order and explicit container lengths prevent ambiguity.
Propose one-byte tags and eight-byte payload lengths; container payloads are
successive complete child encodings, with cardinality derived by parsing to the
declared payload end. Code payloads have exactly eighteen ordered field encodings.
No additional uncharged field-name, count or framing bytes are permitted. Integer
payload charges include its sign byte; bool, float and complex charges include
their complete one/eight/sixteen-byte payloads, respectively.
Unsupported constants, cycles or incomplete encoding stop without repr/str fallback,
numeric conversion, approximate comparison, pointer-based equality or normalization.
Repeated aliases are charged per occurrence; their alias graph is not represented.

**Proposed attempted-work ledger and guards.** One nonrefundable process/import
position, one compile attempt, eight root-snapshot attempts (four loaded/four
compiled) and at most four pair-comparison entries. Reserve each before its phase;
failure/interruption consumes it, with no second process/compile or fallback.
Use one combined 8,192 node-visit budget across snapshots and comparisons, depth64,
65,536 bits per integer, 1,048,576 charged leaf-payload bytes, 64 retained difference
paths and 65,536 retained-report bytes. These are proposed stop limits, not measured
fit, deadlines or proof of bounded compiler/import/GCD/allocator/native work.
Source bytes and compiler storage are outside the leaf-payload count, explicitly.

Charge each visit before recursion. Guard integer bit length before magnitude
conversion; bytes length before copying; a conservative four-bytes-per-character
string allowance before encoding. Charge complex's two float payloads and every
container occurrence. Permit tag/length overhead only within an additional
9-bytes-per-visited-node encoding allowance; the combined visit cap also covers
field-value encoding. Reserve complete child encodings before frozenset sorting
or concatenation. Compare typed payload bytes exactly, not Python hashes/digests.
Report paths as fixed field names and bounded indices, not unbounded constants.
If difference/report capacity is exhausted, stop unresolved rather than silently
truncate a complete-comparison claim. No partial positive certificate is published.

**Publication, acceptance and stops.** Capture all eight supported root snapshots
before comparison. Retain original live bindings/code references and source bytes;
recheck bindings/code references/file hash after snapshots and before publication.
Only after complete comparisons and final guards may a fresh report say equal or
different for each pair, with full declared field/type coverage and attempted ledger.
Two-point identity checks still cannot detect transient mutation, enforce ownership
or future stability. Unexpected errors/MemoryError/interruption stop without a
successful report; no automatic repair run. Malformed profiles, source/version drift,
missing/duplicate roots, unsupported types/cycles, cap exhaustion or observed binding/
code/source change stop unresolved. Preserve bounded failure/outcome history.

Future review must separately approve this representation, limits, runner and one
process/import/compile position before execution. An equality report would accept
neither U4 nor any mathematical/native/source/resource/consumer claim; a difference
would authorize no code repair by itself. Keep all fifteen verdicts undecided, five
flags false, consumer ineligible and existing task/physical/data/hardware gates.
Propose ordinary session output plus existing evidence documents, no persistent
probe/cache artifact or raw constant dump, no download or cleanup. Preparation and
documentation validation do not renew any exhausted evidence or source-test budget.




#### Supplied Native Motion-Update Word Prerequisites (2026-11-13)

These separate motion-word diagnostics adopt neither NF1 certificate premises
nor historical study/run authority. All qualification flags remain false.

##### Supplied Pre-Integration Speed-Update Words (2026-11-13)

The private `_native_speed_update_residuals` compares five canonical supplied
binary64 words: prior speed, observed clipped target, Config acceleration/dt
and observed updated speed. Exact prior+clamp(target-prior,+/-acceleration*dt)
is an unrounded reference, not a prediction of native intermediate rounding
or branch choice. Its signed observed-minus-reference residual preserves the
raw words, including zero signs; a nonfinite updated speed remains unknown.
Finite operands and positive acceleration/dt use the existing Config domain.
Literal synthetic permission, <=5 decodes/values, four rational operations,
two growth-checked comparisons and the existing4096-bit cap bound the work.

Existing actual motion receipts already contain these operands; this adds no
capture, source read, replay, RNG, trig, clock or controller change. Submitted
target/yaw clipping is separate. Supplied words alone prove neither source
ownership nor uniform/propagated native error, timing, physical or command
qualification. Eight flags remain false. The [checkpoint][native-speed-update-review]
records direct/actual-word controls and the required gate.


##### Supplied Target and Yaw Clipping Words (2026-11-13)

The private `_native_action_clipping_diagnostics` compares six canonical
submitted/profile/observed words for the existing speed [0,max_speed] and yaw
[-max_turn_rate,max_turn_rate] clamps. Numeric equality and unique equal-value
word-candidate correspondence remain separate; different zero-word candidates
stay unresolved, not an inferred native selection or normalization law.
Canonical nonfinite action/output is unknown per component; malformed/NaN words
and nonfinite/nonpositive existing Config limits reject without mutation.

Literal synthetic permission and <=6 decodes/2 entries/4 min-max comparisons/
6 candidate and2 observed numeric equalities/2 builtin dyadic ratios bound the
work, with <=3 candidate words per entry and no rational engine. Actual receipts
already contain all operands: no capture, read, replay, RNG, trig, clock or
controller change. This is not source/uniform-error/physical/command acceptance;
eight flags stay false. The [checkpoint][native-action-clipping-review] preserves
the direct/actual-word controls, work limits and required gate.


##### Supplied Captured-Interval Division Words (2026-11-13)

The private `_native_interval_division_residuals` compares exact supplied
nominal duration divided by observed builtin planned_segments1..128 with
the captured native interval. This does not recompute segment selection.
Canonical positive finite duration follows existing Config; raw nonfinite
observed interval is unknown, while malformed/NaN words reject without mutation.
Raw duration/count/interval and signed observed-minus-exact ratio remain explicit.
Literal synthetic permission, <=2 decodes/3 rational values/one division/one
subtraction and the existing4096-bit cap bound the work. Existing receipts and
native integration input joins already retain the operands; no source/controller
change or replay/RNG/trig/clock follows. This is not a native rounding law,
uniform motion error or qualified duration/clock; eight flags stay false.
The [checkpoint][native-interval-division-review] records controls and the gate.


##### Current Receipt Motion-Update Composition (2026-11-13)

The owned receipt-history reader's literal default-off
`include_native_motion_update` uses its current actual receipt, not a caller
source override. Original/closing supplied clipping/speed-update reports bind
copied inputs, epoch/transition ticks/receipt digest and the current frame.
Changed owner/source/history/report or unsupported/nonfinite input is unknown
without partial payload. Equal-value zero-word candidate ties remain unresolved.
All eight flags stay false; local discrepancies are not accepted native bounds.

Producer observations precede sampled words; final producer sampling follows
all reports and precedes final owner closure. Current layout guards reject
before consumption. Original <=2 observations/one history validation/32 digests
remain; <=2 reports per family preserve their individual work limits. Default
payload/report work is unchanged, with no replay/capture/RNG/trig/clock/guard
or controller change. The [checkpoint][current-motion-update-review] records the
two reproduced closure failures, controls, fixture repairs and required gate.


##### Current Receipt Interval Composition (2026-11-13)

The current receipt reader's independent literal default-off
`include_native_interval_division` needs no motion-update inclusion.
Interval-only/both modes bind detached supplied quotient reports to current
epoch/transition ticks/receipt digest/frame. Original/closing metadata/operand/
output checks precede final producer sampling and owner closure. Changed,
unsupported or nonfinite evidence is unknown without partial fields.
Default/motion-only report shape and work stay unchanged.

<=2 interval reports/4 decodes/6 rational values/4 arithmetic operations keep
the individual arithmetic cap; original2 observations/one history check/
32 digests remain. No replay/capture/RNG/trig/clock/guard query or source/
controller change follows. Eight flags false; segment selection, uniform error,
clocks, physical permission and admission are separate. The
[checkpoint][current-interval-division-review] records modes, mutations and gate.

[sinc-cell-review]: ../../REVIEW.md
[sinc-word-review]: ../../REVIEW.md
[sinc-word-proof-review]: ../../REVIEW.md
[sinc-certificate-plan-review]: ../../REVIEW.md
[sinc-cell-check-review]: ../../REVIEW.md
[sinc-checker-paper-review]: ../../REVIEW.md
[sinc-bind-contract-review]: ../../REVIEW.md
[sinc-bind-budget-review]: ../../REVIEW.md
[sinc-bind-implementation-review]: ../../REVIEW.md
[sinc-bind-paper-review]: ../../REVIEW.md
[sinc-composition-contract-review]: ../../REVIEW.md
[sinc-composition-prototype-review]: ../../REVIEW.md
[sinc-composition-paper-review]: ../../REVIEW.md
[sinc-target-contract-review]: ../../REVIEW.md
[sinc-target-prototype-review]: ../../REVIEW.md
[sinc-target-paper-review]: ../../REVIEW.md
[sinc-target-join-review]: ../../REVIEW.md
[sinc-target-join-prototype-review]: ../../REVIEW.md
[sinc-target-join-paper-review]: ../../REVIEW.md
[sinc-join-worksheet-review]: ../../REVIEW.md
[c1-prototype-source]: ../../sim/diagnostics.py
[sinc-binding-identity-review]: ../../REVIEW.md
[sinc-compile-comparison-review]: ../../REVIEW.md
[sinc-structural-protocol-review]: ../../REVIEW.md
[current-motion-update-review]: ../../REVIEW.md#345-closed-current-receipt-motion-update-reports-2026-11-13
[native-action-clipping-review]: ../../REVIEW.md#343-supplied-target-and-yaw-clipping-correspondence-2026-11-13
[native-interval-division-review]: ../../REVIEW.md#346-supplied-captured-interval-division-residuals-2026-11-13
[current-interval-division-review]: ../../REVIEW.md#349-closed-current-receipt-interval-reports-2026-11-13
[native-speed-update-review]: ../../REVIEW.md#342-supplied-pre-integration-speed-update-residuals-2026-11-13
