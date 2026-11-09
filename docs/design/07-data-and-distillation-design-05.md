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



The approved prototype objective is goal reaching without collision: reward
is decrease in goal distance in meters, minus 0.01 per tick, plus 10 for
success (within 0.25 m) or minus 10 for collision. These are adjustable trainer
signals, not validated robot policy, firmware interlocks, or label definitions.

The map-aware scripted expert intentionally has privileged map/pose access;
episode metadata marks this. It is a simulator reference, not a source of
reviewed student targets. A sensor-only reactive baseline remains selectable
and collided in the initial obstacle and slalom rollouts. The map reference
subsequently completed all four scene families over seeds 0-7: 32 successes,
zero collisions and zero timeouts. For seed 0, clear/obstacle/corridor/slalom
finished in 133/141/133/156 ticks. These smoke results validate tooling only,
not safety, robustness to the real world, or the eventual student's quality.

The CLI writes new JSONL episodes and optional headless PNG trajectories under
ignored `sim/episodes/`. It never overwrites existing logs. Logs carry seed,
full scenario/configuration, policy privilege, rewards, input observations and
separate diagnostic truth under `micro-classifier/sim-episode/1`. Repeated
seed/configuration episodes are tested for deterministic equality in this
environment. The JSONL container remains a simulation schema, not UART bytes.
The user subsequently approved provisional contract export (§2). `--wire`
adds a `micro-classifier/sim-wire/0` manifest and exact CRC-protected state
frame bytes, hex-encoded, for every observation including reset. Default
logging remains available without wire fields. No existing episode is
rewritten or overwritten.

The exporter maps current planar forward velocity to FLU X, yaw rate to
angular FLU Z, and body-frame goal to FLU X/Y, with constrained planar axes
zero. Sample sequence is tick modulo 2^32; sample timestamp is rounded
microseconds modulo 2^32. The three simulated groups have age zero. Battery
and host fault state are **unknown**, not healthy: invalid bits, zero values,
unknown ages. ToF/dropout/age/history remain separately logged module-side
inputs. True pose, actions and privileged map information never enter the
host state frame. With no model, the exporter does not invent decision frames,
rejection results or reviewed labels. No physical safety policy is frozen.

Wire-export checks add nine tests, giving 30 simulator tests and 62 contract
tests. Four real wire-enabled map-expert episodes at seed 20261015 succeeded
with no collisions/timeouts. Every frame passed CRC/decode, byte equivalence
to current inputs and concatenated stream decoding; 566 frames, 52,072 bytes.
Recorded logs remain ignored under `sim/episodes/wire-v0-smoke/`:

| Scenario | Ticks | State frames | Episode JSONL SHA-256 |
| --- | --- | --- | --- |
| clear | 133 | 134 | `6d574743a4ac4fb4ee01338631735941b0a07486b0ec1031bf6c58f47755d731` |
| obstacle | 140 | 141 | `f07626df0211e6d3444d23ac0cb5cb1b7d3d41381a2a5ad1ac2b6282cf72a872` |
| corridor | 133 | 134 | `b4d066d2ffc0c0eab1c9e543835c3614dbf91bbc51966089e6a0c2a93ca5f1fa` |
| slalom | 156 | 157 | `8264ea5f83235608ecb059fedc9b3129ffdb01856c1021f6a47eff550a962b97` |

These are simulator/codec tooling checks, not closed-loop student evaluation,
reviewed supervision, safety evidence or physical UART measurements.

A student trained only on logged or scripted trajectories meets states it never
saw once its own decisions steer the robot. Collect data in rounds, as in
[DAgger][dagger]:

1. Seed with teleoperation, scripted experts, and simulator rollouts, labeled
   per §4.
2. Train a student, then run it in simulation and afterwards in a safe arena,
   with the host's fail-safes active.
3. Log every state packet, decision, rejection, and high-entropy tick on the
   module (SD card or external flash), label the visited states, retrain, and
   repeat.

Simulate first: PX4 software-in-the-loop with [Gazebo][px4-gazebo] covers both
rovers and multicopters. Model sensor noise, latency, and dropouts, and keep
real-world episodes for the locked test set; simulator success alone passes no
gate.

### Simulation Label Policy Draft (2026-10-15)

The user approved **a policy draft and tests only**, not generation of labeled
episodes, teacher labeling, student training or deployment. The [catalogue
data][sim-catalogue-draft] and [draft implementation][sim-label-draft] retain
`unreviewed_draft`, `tooling_and_unit_tests_only`, no training approval and no
physical safety claim. Wire catalogue version 0 and its ordered option identities
are unchanged. This does not complete Task 6's reviewed-policy requirement.

The draft consumes only current observation ego-state, ToF ranges/masks, tick,
sample tick and age. It never reads world geometry, collision/success truth,
expert actions, future frames or history. Its proposed stopping-envelope proxy is

$$
d(v,\tau)=r+v(\tau+\Delta t)+\frac{v^2}{2a},
$$

where radius, tick duration and acceleration/deceleration come from `Config`,
speed is the observed forward speed, and age is the observed ToF age. The
extra one-tick reaction term is a **draft assumption**, not measured latency.
At the default maximum speed 0.6 m/s and age 0.1 s, this gives 0.45 m.
Freshness follows the existing simulation baseline's Config-derived limit:
age at most `(latency_ticks + 1) * dt`. Sample age must agree with its ticks.
Float32 roundoff at configured motion/range limits is accepted; the envelope
uses at most the nominal Config speed, not a larger invented speed limit.

Columns 0-2 are left, 3-4 centre and 5-7 right; columns run from positive to
negative body bearing. Each column needs at least one valid row; its minimum
valid return is used. A sector minimum exists only with coverage in every
column. Missing masked cells must be zero, as in the simulator schema.

| Question | Proposed sensor-proxy rule |
| --- | --- |
| `path_blocked` | Centre minimum at or below the current-speed envelope gives true; strictly above gives false |
| `clear_sector` | Among sector minima strictly above that envelope, pick the greatest; exact ties prefer centre, left, right; `none` means all sectors are observed but none qualifies |
| `speed_tier` | Greatest tier whose candidate-speed envelope is strictly below centre minimum; tiers map to 0, 1/3, 2/3 and full Config.max_speed; fallback is tier 0 |
| `mode` | Always absent with `human_review_required`; never infer policy mode from expert actions or deterministic proxies |

Unknown is distinct from `none`, false or tier 0. Warmup without a sample,
staleness or a current envelope reaching/exceeding sensor range causes all
three computable questions to abstain. Missing centre coverage abstains for
`path_blocked`/`speed_tier`; any missing sector coverage abstains for
`clear_sector`. Malformed, non-finite, out-of-range or inconsistent observations
are rejected. Returned option indices match the catalogue, not model outputs.

The record includes canonical catalogue/config/input SHA-256 and labeler-source
SHA-256, full Config, explicit reasons and measured sector minima. Extra
privileged fields do not change it; inputs are not mutated. No probabilities,
model decision frames or automatic episode-export integration are added.

These are radial sensor proxies, **not collision ground truth**. Sparse planar
rays, a limited field of view, censored maximum-range returns, unbounded Gaussian
noise, turning motion and stale geometry preclude a free swept-footprint or
physical safety claim. Tier zero is a draft label, not an interlock or a motor
command. The host's independent fail-safes are untouched. Review these exact
assumptions before any labeled dataset or teacher-labeling pipeline uses them.

Verification: 37 new draft tests; all 67 simulator tests and 188 repository
tests pass, plus the previously known transformer numerical expected failure.
Checks cover wire-option parity, hand arithmetic, strict/inclusive boundaries,
left/right orientation, masking, warmup/staleness, out-of-range abstention,
provenance changes, no privileged-data leakage and input immutability. Lint,
changed-file formatting and editor diagnostics pass. No labeling run, training,
new dependency, ST execution, firmware or hardware work occurred.

#### Bounded Simulation Smoke Approval (2026-10-16)

The user subsequently approved the unchanged draft for a **small seeded smoke
suite and fake-teacher pipeline tests only**. Catalogue scope metadata records
this date and keeps live teacher labeling/training disabled. `unreviewed_draft`
still means no training/production-quality approval; `allowed_use` now names
the simulation-smoke/pipeline-test scope. No rule or wire identity was changed.

`python -m sim.labels` runs exactly clear/obstacle/corridor/slalom with one
seed, retaining original observations and separate diagnostic truth. Labels
consume only observations; `mode` remains absent. Exclusive new logs under
ignored `sim/episodes/` and an optional shareable report prevent accidental
replacement of evidence. No training or real teacher invocation is connected.

The [recorded report][sim-label-smoke-report] at seed 20261016 has four
successful scenes, zero collisions/timeouts and 567 labeled observations:

| Scene | Ticks | Observations |
| --- | --- | --- |
| clear | 133 | 134 |
| obstacle | 141 | 142 |
| corridor | 133 | 134 |
| slalom | 156 | 157 |

Each computable question abstains for two warmup observations per scene.
All 559 remaining `path_blocked` values are false and all speed tiers are 3;
sector counts span left/centre/right, with no `none` cases. `mode` abstains
on all 567 observations. These privileged-expert trajectories lack positive
blocked/lower-tier coverage and are **not a balanced or reviewed dataset**.
They validate labeling plumbing, not proxy accuracy, calibration or safety.

All four log hashes and observation counts were independently verified against
the shareable report and its ignored copy. Report SHA-256:
`4ebfe308d8cc8070d543d314ca1621ea59a5e6fe441ef0b47e5d791ab972aee8`.
Four additional tests cover replay, no-mode/no-training invariants, log hashes,
exclusive outputs and invalid seeds. Verification: 71 simulator tests,
192 repository passes plus the known transformer expected failure; lint,
changed-file format and editor diagnostics clean. Task 6 still needs review
for training data, coverage and human mode labels. Task 8 preparation is
approved only with fake teachers; real labeling remains gated.

#### Diagnostic Coverage Study (2026-10-16)

The user approved **CPU-only coverage tooling/tests, at most 16 diagnostic
episodes plus synthetic fault fixtures, and an unreviewed smoke report**.
No production dataset, live teacher, training, dependency/download, physical
safety change or input/history/token-budget change was approved. Accepted
defaults and label rules remain unchanged; this does not clear Task 6 review.

The [label CLI][sim-label-draft] adds explicit `--coverage-study`; without it,
the original four-scene smoke path is unchanged. The study runs eight episodes:
open hold, four wall-clearance holds, left/right wall views and a straight
approach/brake probe. Only the study's time horizon is overridden to 32 ticks
from Config's default 400, retaining default physics, noise, dropout, latency
and history. Stationary probes are not navigation experts; the brake probe uses
privileged wall distance solely to generate observations. Labels still consume
only observations, with truth and actions separate. Script privilege and
diagnostic/training-disabled scope are explicit in episode metadata.

A zero-inclusive coverage summary lists each option, missing options, answered
counts and abstentions by reason. Twelve synthetic current-observation fixtures
(four sector, four speed and four fault cases) are embedded separately in the
report, never pooled with episode coverage. They are artificial rule exercises,
not complete-history episodes, reviewed labels or task-distribution samples.

The [measured report][sim-label-coverage-report], seed 20261016, contains eight
episodes and 264 observations. All episodes avoid collision and intentionally
reach the 32-tick horizon; none reaches its goal. These are **not navigation
success rates or evidence of a safe controller**.

| Question | Episode Option Counts in Catalogue Order | Abstentions |
| --- | --- | --- |
| `path_blocked` | false: 208; true: 40 | 16 no-sample warmups |
| `clear_sector` | left: 88; centre: 21; right: 105; none: 34 | 16 no-sample warmups |
| `speed_tier` | 0: 36; 1: 36; 2: 98; 3: 78 | 16 no-sample warmups |
| `mode` | All five options: 0 | 264 human-review-required |

All computable options occur in these selected episodes, unlike the earlier
expert smoke, but **representative coverage and proxy accuracy remain unproven**.
Thirty-one blocked positives come from the noisy stationary near-wall case,
whose true starting footprint is clear; nine occur in the moving brake probe.
Sensor-proxy positives are not independently reviewed obstacle ground truth.
The twelve separate synthetic fixtures exercise no-sample, stale, incomplete
centre-column and incomplete side-sector abstentions, plus every computable
option; `mode` remains absent for all twelve. They do not cover every possible
fault/configuration or establish a label policy suitable for training.

All eight ignored JSONL log hashes, consecutive ticks, 264 recomputed labels and
option identities were independently checked, as were the twelve fixtures and
false approval flags. An AST comparison against the preceding commit confirms
that `draft_catalogue`, `stopping_envelope`, `draft_labels` and `smoke_suite` are
unchanged. Config defaults, catalogue, wire contract and prompt renderer were
not edited. Report SHA-256:
`612d3a7251a2021ffaf24c80030de669fb72929abb37fc5b0b99bba4f670224f`.

Verification: nine new focused coverage checks, 80 simulator tests and 307
repository passes plus the known transformer numerical expected failure; Ruff
lint/changed-file format and editor diagnostics clean. Tests cover zero counts,
separate abstentions, empty inputs, deterministic replay, complete relabeling,
bounded runs, origin separation, no-mode/no-training invariants, CLI opt-in,
existing-output protection, invalid seeds and smoke-approval rejection. No real
teacher, reviewed dataset, training, dependency/download, firmware or hardware
action occurred. Training-label review, human mode labels, representative task
data and the unchanged 2,048-token live-teacher gate remain pending.

### Proposed Label and Evaluation Review (2026-10-16)

The user approved **decision preparation only**: a label-policy/evaluation-set
proposal and an offline prompt-cost study using existing logs and approved
cached tokenizers. This section is a proposal, not acceptance of new targets,
labels, datasets, splits, thresholds, training or inputs. All previous gates
and accepted defaults remain unchanged.

#### Targets Requiring Review

The [catalogue][sim-catalogue-draft] specifies reproducible sensor proxies, not
independently reviewed task truth. The proposed review should distinguish:

| Question | What Existing Labels Measure | What They Do Not Establish |
| --- | --- | --- |
| `path_blocked` | A noisy centre-sector minimum compared with the draft envelope | Obstruction of the robot's swept footprint or collision risk |
| `clear_sector` | Greatest qualifying radial sector minimum, with fixed ties | A collision-free, goal-directed steering action |
| `speed_tier` | Config-derived straight-line ceiling proxy, with tier-0 fallback | A physical speed limit, stop interlock or guaranteed safe action |
| `mode` | No labels; human review is required | An agreed, observable distinction between all five behaviour options |

**Proposed default:** retain the three proxy definitions for diagnostic
conformance only until their intended training roles and independent task
targets are reviewed. Agreement with the deterministic labeler measures
imitation of that algorithm; it must not be reported as obstacle accuracy or
proof that learning improves on computing the rule directly.

The five `mode` options remain `explore`, `approach`, `avoid`, `dock`, `halt`.
Their operational meanings and precedence are not defined by the catalogue.
The current simulated input provides ego-state, goal displacement and ToF
history, not explicit exploration/docking intent, a docking marker or measured
host health. An identical observation may be consistent with different intended
modes under different mission policies. This is an unresolved identifiability
question, not evidence that every possible mode definition is unlearnable.

**Proposed default:** keep mode absent until the user defines decisions that
reviewers can distinguish from the accepted inputs. Do not infer it from the
expert's actions, privileged simulator state or an unrecorded mission phase.
Allow reviewer abstention for insufficient observation, ambiguous intent or
disagreement rather than forcing one of five options. Abstention is review
metadata, not a new wire option. Adding mission intent, changing options or
reducing the task would require a separate interface/product decision.

#### Evaluation-Set Proposal

No records or assignments are generated or locked by this proposal:

1. Define each target, its allowed evidence and abstention conditions before
  collecting or annotating data. Keep sensor-proxy agreement, reviewed task
  labels and simulator diagnostic truth as distinct evidence sources.
2. Review complete student-visible current input plus the eight-tick history.
  Keep privileged truth separate for diagnostic audit; do not use information
  unavailable to the student to force a semantic mode label. Reviewers should
  initially be blind to teacher and proxy suggestions to reduce anchoring.
3. Cover ordinary runs, boundary clearances, braking/turning, sensor faults,
  warmup, ambiguity and out-of-domain cases. Existing expert and selected
  diagnostic trajectories are useful audit cases, not a representative cohort
  or an approved task dataset. Real pilot data remains a later requirement.
4. Group whole episodes and related source/template families before windowing
  or augmentation. Nearby frames share history, and changing a seed alone
  does not establish independence. Variants/mirrors of one parent scene stay
  in the same group; exact duplicate inputs must not cross purposes.
5. Keep training, development, quantization calibration, confidence calibration
  and final test purposes separate. Record original hashes, group lineage,
  catalogue/input/config versions and reviewer provenance. Freeze an attested
  manifest before model selection; the synthetic split checker alone neither
  attests the inputs nor locks a task test set.
6. Report class support, abstention/disagreement and existing metrics without
  claiming quality for absent classes. Compare a learned model against direct
  rules and a classical baseline on reviewed task targets, not solely against
  the same rules used to generate its supervision. Thresholds and cohort size
  require review; no new acceptance values are selected here.

The next product review must resolve the three proxies' roles, observable mode
semantics, permitted reviewer evidence and the cohort/grouping policy. Until
then, Tasks 6/9 remain blocked on review/data, and student training and live
teacher labeling remain unapproved. M1a is independently blocked on the absent
approved ST toolchain; this proposal does not replace deployment proof.

#### Accepted Review Boundaries (2026-10-16)

The user subsequently made these explicit decisions:

1. **Targets remain unaccepted.** Define independent navigation truth before
  adopting task targets. The existing three rules remain diagnostic proxies,
  not accepted sensor-proxy training targets; mode remains unlabeled.
2. **Observation-only review policy is adopted.** Human review may use only the
  complete student-visible current input and history. Abstain when that evidence
  is insufficient; exclude privileged truth, actions and teacher/proxy suggested
  answers. This adopts review boundaries, not actual annotations or a real-review
  import path. An accepted target definition and further approval are still
  needed before collection.
3. **Diagnostic-only quarantine and grouping review are adopted.** All current
  logs remain diagnostic-only. Retain episode identities, leave unknown families
  unresolved and review source/template families before accepting any task
  cohort or split. This is not a completed family review, representative cohort,
  dataset approval, split assignment or locked test set.

These decisions supersede only the earlier undecided review-evidence and
diagnostic-quarantine policy questions. They do not approve new inputs/options,
numeric thresholds, physical safety parameters, inference, labels or training.

The following definition checklist is still open, not an adopted target policy:

| Question | Navigation Definition Still Needed |
| --- | --- |
| `path_blocked` | Which continuation/path and time horizon; swept footprint and clearance criterion; when missing spatial evidence requires abstention |
| `clear_sector` | Whether clear means observed radial space or a reachable turn; role of goal alignment, tie-breaking and `none` versus insufficient evidence |
| `speed_tier` | What each tier recommends over which horizon and motion assumptions; how unknown clearance affects review, without treating a tier as a physical safety interlock |
| `mode` | Observable meanings and precedence of the five options without inventing mission intent, docking evidence or host-health inputs |

No horizon, margin, tier meaning or mode precedence is selected here. If a
candidate definition cannot be established from the permitted input, reviewers
must abstain rather than silently consult privileged maps, expert actions or
future outcomes. A different evidence policy or added input requires another
explicit decision. Tasks 6/9 still wait on target definitions and actual reviewed
data/cohort evidence; approved review boundaries alone do not clear those gates.

#### Concrete Navigation-Target Draft (Unaccepted, 2026-10-16)

The user approved this concrete proposal and **synthetic-only checks**, not
target adoption, labels, data generation, input/default changes or training.
This candidate replaces neither the catalogue nor its three diagnostic rules.
It describes geometric navigation questions separately from the evidence a
human could establish using only the accepted input. Mode stays unlabeled.

**Candidate maneuver model.** Use current FLU forward speed $v$, yaw rate
$\omega_0$, ToF age $A$, and the existing simulation Config values: tick
$\Delta t=0.05$ s, radius $r=0.18$ m, acceleration/deceleration magnitude
$a=1$ m/s², maximum speed 0.6 m/s and turn rate 1.5 rad/s. These are simulation
numbers, not measured braking capabilities or accepted physical safety limits.
For a hypothetical braking maneuver, propose:

$$
\begin{aligned}
	au &= A+\Delta t, & T_v &= \tau+v/a,\\
s_v(t) &= \max(0, v-a\max(0,t-\tau)),\\
\psi_u(t) &= \omega_0\min(t,\tau)+u\max(0,t-\tau),\\
q_u(t) &= \int_0^t s_v(z)(\cos\psi_u(z),\sin\psi_u(z))\,dz.
\end{aligned}
$$

Start at the current body origin with yaw zero. During the reaction allowance
retain measured yaw rate; while braking use candidate $u=0$ (centre), $+1.5$
(left), or $-1.5$ rad/s (right). Compare the **entire** swept radius-$r$ disk
for $0\leq t\leq T_v$ against occupied space, not a ray minimum or endpoint.
Using age in this future allowance is a candidate design choice; delayed
measurements still need registration to the current frame, not direct reuse as
current geometry. The integral and complete curved-sweep evaluator are not
implemented. This model is not a description of the host's actual commands.

For zero yaw, the centre sweep is a capsule of centreline length
$D=v(A+\Delta t)+v^2/(2a)$. With the example age 0.10 s, nominal speeds
0.2/0.4/0.6 m/s give $D=0.05/0.14/0.27$ m and horizons 0.35/0.55/0.75 s.
Those examples are checked arithmetically; no new freshness limit is selected.
Propose contact, including tangency, as blocked and strict positive clearance
as clear, with no extra geometric margin in these idealized fixtures. The
existing simulator counts circle tangency as collision but permits exact wall
contact; adopting the proposed target convention would require an independent
wall-boundary oracle. No simulator collision rule is changed here.

**Candidate answers, conditional on adequate evidence:**

| Question | Proposed Meaning | Abstention or Limitation |
| --- | --- | --- |
| `path_blocked` | Does the centre braking sweep intersect occupied space? `false` requires the entire sweep to have strict clearance | Alternative worlds consistent with the input that disagree require abstention; no ray hit is not a clear-space certificate |
| `clear_sector` | Among fully classified left/centre/right braking sweeps, choose a clear one whose endpoint minimizes distance to the observed goal; exact ties prefer centre, left, right. `none` means all three are established blocked | Any unknown sweep abstains rather than producing `none`; at zero speed the directions degenerate, so abstain instead of inferring a turn from an arbitrary tie |
| `speed_tier` | For tiers 1/2/3, test the centre maneuver at reference speed $\max(v,0.6k/3)$ for tier $k$, then choose the highest established clear tier when all three are classified. If all are blocked, tier 0 requests reduction/stop | Reference speeds are counterfactual capacity tests, not instantaneous speed changes or proof of containment of every real trajectory. Unknown is not tier 0; tier 0 does not assert a collision-free stop |
| `mode` | Remain absent; this proposal does not define a five-way task target | Exploration/approach intent, docking identity and host-health meaning are not observable merely from a goal vector and ToF. Meanings, precedence or additional inputs still need explicit review |

The tier fractions reuse the existing nominal fractions, but the proposed
geometric meanings are not adoption of the old sensor proxies. Lower requested
speed must not erase current momentum. Goal-distance ranking is only a proposed
comparison of these finite maneuvers, not route planning, guaranteed reachability
or permission to execute any command. Starting from rest needs a separately
reviewed motion-start definition; none is invented here.

**Evidence and unknown space.** The geometry above defines an ideal-world
candidate, not permission for a reviewer to inspect a map. Actual review still
uses only complete student-visible input/history and must abstain when that
input cannot establish an answer. No accepted surface interpolation, minimum
obstacle size, bounded noise/error, dynamic-obstacle model, measurement-frame
registration or statistical decision threshold is supplied by this proposal.
Gaussian noise standard deviation is not a hard error bound. Therefore it
does not certify negative/clear labels from the current sparse ray model.
Accepting such assumptions or changing inputs would require explicit review.

Ten [synthetic checks][sim-tests] pass without episode generation or persistence.
Two pairs of artificial circular-obstacle worlds have **identical complete
rendered input**, including eight valid ego/ToF-history ticks with two-tick
sensor latency, but opposite centre-sweep collision results. One obstacle is
between rays; another is outside the viewed region but within the swept body.
Both starting footprints are collision-free. This demonstrates ambiguity for
those inputs even with noise/dropout disabled, not that every navigation input
is ambiguous. Other cases check whole-sweep circle contact, the three nominal
distance/horizon examples and two lower-speed momentum counterexamples.

The tests reuse existing ray/collision/rendering helpers, not an independent
physics engine. They do not qualify curved sweeps, goal ranking, uncertainty
bounds or a production labeler. Ninety simulator tests and 388 repository tests
pass plus the known transformer expected failure; lint/format/editor and doc
checks pass. Simulator, catalogue/rules, interface, renderer and review runtime
files are unchanged. No observation from current logs was relabeled, and no
report, task dataset, split, inference, training or hardware action occurred.
Tasks 6/9 remain blocked: review these candidate meanings and unresolved
observability/model choices before target adoption or actual annotation.


#### Synthetic Navigation Reference (Simulation Scope Adopted, 2026-10-16)

The user adopted the preceding first-three geometric meanings **for simulation**
and approved an isolated CPU-only oracle with artificial fixtures. This
supersedes the draft's unaccepted/implementation status only in that scope.
Unknown or numerically unresolved cases abstain, at-rest sector choice abstains,
mode remains unlabeled, and contact includes tangency. No physical safety,
observation-based evidence model, reviewed dataset, episode labeling, real
annotation/import, split, inference or training approval is implied. Existing
proxy rules, accepted inputs/defaults and token ceiling are unchanged.

The [reference][navigation-reference] exposes `evaluate_synthetic(Scenario,
speed=..., synthetic_test_only=True, ...)` using complete artificial geometry.
It accepts neither observation dictionaries nor episode paths, performs no
rollout or file I/O and provides no CLI/cache/data-export path. The explicit
opt-in is a caller scope assertion, not attestation that geometry is synthetic.
Every result is tagged artificial-geometry-only, synthetic, training-disabled,
not a reviewed dataset and not a physical safety claim; mode is always absent.
The output is not a new wire contract or a substitute for the blind-review path.

Straight zero-yaw trajectories use analytic capsules. Curved trajectories split
reaction and braking phases, integrate velocity with midpoint quadrature and
query complete chord sweeps against inflated circles and arena boundaries.
For a segment of duration $h$, speed bounded by $v$, angular rate $\omega$ and
phase deceleration $a_p$, the exact-arithmetic bounds used are:

$$
M_2=a_p+v|\omega|,\qquad M_3=2a_p|\omega|+v\omega^2,
\qquad E\leftarrow E+M_3h^3/24+\varepsilon_{fp},
\qquad \delta=E+M_2h^2/8.
$$

An intersection using radius $r-\delta$ establishes a blocked sweep; separation
using $r+\delta$ establishes clearance. Otherwise it is numerically unknown.
Initial/analytic contacts use the strict reference convention, including wall
contact; the simulator's original wall behavior is unchanged. The floating-point
term is an engineering allowance based on coordinate scale, **not verified
interval arithmetic or a formal numerical certificate**. Analytic endpoints
also retain a nonzero roundoff allowance. These ideal-geometry results are not
calibrated probabilities, sensor uncertainty bounds or physical guarantees.

Steps are at most 0.02 s with a local chord-deviation target of $10^{-5}$ m;
that target is not a global position-error limit or a new physical margin.
Each maneuver admits at most 4,096 segments; the caller can lower that cap.
Budget exhaustion or nonfinite/unresolved numerical bounds return unknown.
Endpoint error intervals participate in goal ranking: overlapping candidates
abstain unless an exact model symmetry establishes the left/right tie, which
prefers left. Other unresolved ties abstain rather than inventing precision.
No unknown maneuver becomes `none` or tier 0. Current speed is retained in every
tier reference; at-rest sector choice abstains as explicitly adopted.

Twenty-five added oracle cases pass, bringing the simulator suite to 115 and
the repository to 413 passes plus the known transformer expected failure.
Tests cover all tiers, open/blocked/rest scenes, goal ranking, exact mirror
ties, numerical ambiguity, bounded computation, invalid input/scope rejection,
and strict wall contact. Three turn-rate cases compare endpoints with separate
64-point Gauss-Legendre quadrature. The earlier identical-full-input artificial
world pairs now also produce opposite ideal `path_blocked` answers, confirming
that the oracle does not solve the real-input observability gate. Lint/format,
editor diagnostics and doc checks pass. No existing log/report/packet was
changed or relabeled, and no episode or task dataset was generated.

Task 6 now has adopted simulation meanings for three questions and a synthetic
reference, but still lacks reviewed observation-to-target evidence/labels and
observable mode semantics. Task 9 still lacks reviewed cohorts/data and locked
splits. M1a/board gates remain separate. The reference is not promoted into the
simulator, existing labeler, teacher pipeline or review ingestion.

Follow-up (2026-10-16, REVIEW.md §38): two orientation-equivalence regressions
at finite initial yaw +/-1e16 exposed lost small turn increments and about
0.0236 m endpoint disagreement, well above the reported numerical allowances.
The oracle now starts from atan2(sin(yaw), cos(yaw)), preserving the represented
direction while allowing small angular updates. Positive/negative large-heading
cases now match equivalent bounded headings within endpoint allowances. The
simulator and input contract are unchanged; this is a reference numerical
repair, not a safety or evidence qualification. All 117 simulator tests and
433 repository tests pass plus the known transformer expected failure, with
clean lint/format/editor/doc checks. No existing artifact was regenerated.


#### Synthetic Ray-Witness Feasibility (2026-10-16)

The user approved a CPU-only synthetic prototype/checks with **no use on
existing logs or actual annotations**. This study explores positive evidence
for the adopted straight braking footprint, not a production labeler or new
sensor uncertainty policy. Existing proxy rules, inputs/history/defaults, token
ceiling and diagnostic quarantine remain unchanged.

The separate `probe_synthetic_ray_witness` function in the
[navigation module][navigation-reference] accepts eight artificial planar
ranges and a boolean validity mask. It requires explicit synthetic-test opt-in,
zero declared sensor noise, zero acquisition latency and age, and zero measured
turn rate. These conditions model exact rays already in the current body frame;
they are caller-supplied fixture assumptions, not registration or calibration
performed by this function. They do not alter the normal noisy/delayed simulator.
No observation dictionary, episode reader, history reduction or pipeline adapter
was introduced. The eight-ray fixture is not a change to the 8x8 student input.

For speed $v$, the centreline ends at $D=v\Delta t+v^2/(2a)$. At the existing
eight horizontal ray angles $\theta_i$, a finite unmasked range $z_i$ defines
$p_i=(z_i\cos\theta_i,z_i\sin\theta_i)$. A point strictly inside the swept
disk capsule, beyond a scale-based floating-point allowance, is a positive
synthetic collision witness. Exact/numerically close boundary contact abstains
rather than changing the adopted contact semantics. A saturated maximum range
is not treated as a surface return; masked zero padding cannot create an origin
hit. No positive witness means **unknown**, never clear or `path_blocked=false`.

The only output statuses are `blocked_witness` and `unknown`, with column
indices/reasons and artificial-only, training-disabled, real-input-unqualified,
no-physical-safety metadata. Unsupported noise, unregistered delay/latency,
curved motion and numerical scale abstain. The floating-point allowance is an
engineering safeguard, not verified interval arithmetic, a physical margin or
a noise confidence threshold. The opt-in and Config values do not attest that
supplied rays really are exact or registered. The function does not emit wire
decisions, mode labels, reviewer assessments, datasets or calibrated probabilities.

Twenty-nine artificial cases pass. Three scene/ray comparisons with the adopted
geometric oracle include a visible blocked witness, clear geometry with probe
unknown, and hidden blocked geometry with probe unknown. This confirms that
unknown cannot be read as clearance; it is not a universal proof or measured
task accuracy. Other checks cover strict numerical boundaries, partial/missing
masks, saturation inside the footprint, unsupported assumptions, explicit scope,
input validation, immutability and normal-default abstention. No rollout,
existing-log read or persisted data artifact was used for this study.

All 146 simulator tests and 462 repository tests pass plus the known transformer
expected failure; lint/format/editor/doc checks pass. Simulator, proxy/catalogue,
interface, renderer, teacher/review/provenance paths and historical reports are
unchanged. No episode, task annotation/dataset/split, inference, training,
dependency/download or hardware work occurred. Task 6 still needs reviewed
sensor uncertainty/registration evidence and observation-to-target labels; this
restricted positive witness neither qualifies real inputs nor supplies negative
labels. Mode semantics and actual family/cohort/data gates also remain open.

#### Synthetic Bounded-Error Draft (2026-10-16)

The user approved a CPU-only bounded-error draft and synthetic checks, with
**no existing-log use** or adoption of an uncertainty/registration policy.
`probe_synthetic_bounded_ray_witness` is a separate additive diagnostic in the
[navigation module][navigation-reference]. It reuses the unchanged exact-probe
validation and rejection guards: normal noise/default latency, nonzero age and
curved motion still abstain. Artificial zero-noise/current-frame fixtures may
add deterministic residual errors; this is not a conversion of Gaussian noise
standard deviation to a hard bound or registration performed by the code.

For nominal ray point $p_i=z_i d_i$, the **assumed** true registered hit is
$q_i=t+R(\eta)(z_i+\delta)d_i$, where
$|\delta|\leq\epsilon_z$, $\|t\|\leq\epsilon_t$ and
$|\eta|\leq\epsilon_\psi\leq\pi$. Bounds must be explicitly supplied,
finite and nonnegative; booleans are rejected. Under this fixture model:

$$
\|q_i-p_i\|\leq
u_i=\epsilon_z+\epsilon_t+
2(z_i+\epsilon_z)\sin(\epsilon_\psi/2).
$$

The candidate range interval must remain strictly positive and below saturation:
$z_i-\epsilon_z>0$ and $z_i+\epsilon_z<z_{max}$. Let $S$ be the adopted
straight-braking centreline and $r$ its footprint radius. A sufficient positive
criterion is $d(p_i,S)+u_i<r-\varepsilon_{fp}$: the entire assumed error ball
lies strictly inside the swept footprint. The argument uses the triangle
inequality and the distance-to-segment Lipschitz property in exact arithmetic.
The floating-point allowance is an engineering safeguard, not a formal verified
interval bound. Error-ball contact, unsupported intervals, larger uncertainty
or absent nominal witnesses yield unknown, never clear or negative labels.

This draft bounds only the declared hit-location model. It does not bound
ego-state/dynamics, footprint error, obstacle motion, missed surfaces or sensor
outliers. Supplied bounds are caller assumptions, not measurement, provenance
attestation or probability coverage. The new schema records assumed bounds and
candidate point-error radii; results remain artificial-only, training-disabled,
real-input-unqualified and without physical safety claims. No CLI, log reader,
observation adapter, wire decision, mode label or data exporter is added.

Twenty-six new cases pass. Tests exercise each error component independently,
strict error-ball contact, unsupported range intervals, invalid bounds, inherited
scope/default/age/curve rejection and nonmutation. A finite 72-point perturbation
grid lies within the predicted error ball and footprint for one positive fixture;
this is a sampled cross-check, not universal testing or a calibration result.
The original exact probe and all existing oracle functions/signatures are
AST-identical to the prior commit. All 172 simulator tests and 488 repository
tests pass plus the known transformer expected failure; lint/format/editor/doc
checks pass. No existing log, episode, annotation/data/split, inference, training,
dependency/download, hardware action, input/history/default/token change or
historical artifact modification occurred. Task 6 still needs reviewed physical
uncertainty/registration and target evidence; Tasks 6/9 are not cleared by this
assumed-set calculation. Negative/clear evidence and mode remain unresolved.

#### Evidence-Qualification Plan (Proposed, 2026-10-16)

The user approved **documentation only**: a plan for qualifying range error and
frame registration, not measurements, an implemented adapter or adoption of an
uncertainty policy. The following stages and evidence records are proposals for
review. No numeric bound, sampling budget, confidence level, acceptable failure
rate or physical operating domain is selected. Current synthetic APIs and their
noise/latency/age/curve rejection remain unchanged.

1. **Specify the claim and domain before collection.** Distinguish simulator
  model checks from physical sensor qualification; neither establishes the
  other. Propose an explicit sensor/firmware/configuration identity, mounting
  transform, units, supported range/material/incidence/lighting/temperature and
  motion conditions, validity/saturation meanings and excluded cases. Review
  whether each zone supplies a surface point compatible with the assumed planar
  ray model. Zone angular extent, mixed returns or out-of-plane surfaces cannot
  silently be reduced to a centre ray or hidden in a range residual. Unsupported
  hit existence or geometry remains unknown until a compatible evidence model
  is separately reviewed; no 8x8-to-eight-ray adapter is authorized here.
2. **Plan independent range references.** A proposed measurement record retains
  raw readings/masks/status, acquisition identifiers, sensor settings, fixture
  geometry/pose and its independent reference uncertainty, calibration versions,
  operator/procedure identity and raw-file/tool hashes. Establish the same
  surface/zone association before comparing a reading with a reference distance.
  Reference tolerance and alignment error belong in the proposed error budget;
  a residual against an uncertain reference is not sensor error alone. Include
  proposed near-range, saturation, dropout, mixed-surface and adverse-condition
  cases, retaining failures rather than deleting them. No reference instrument,
  scene, sample count, acquisition or hardware run is selected or approved.
3. **Define acquisition-to-decision registration.** Propose separate exposure or
  integration timing (including per-zone skew if applicable), acquisition time,
  delivery time and decision/reference time. Record clock identities, units,
  offset/drift/synchronization uncertainty, wrap/gap handling and timestamp
  semantics; a tick index, receipt time or nominal two-tick delay alone is not
  proof of acquisition time. In a static-world rigid-transform proposal, map a
  hit from sensor frame $S$ at acquisition $t_a$ to body frame $B_r$ at reference
  $t_r$ using mounting extrinsics and independently referenced body motion:

  $$
  p_{B_r}=T_{B_r\leftarrow W}(t_r)
  T_{W\leftarrow B_a}(t_a)T_{B_a\leftarrow S}p_S.
  $$

  Here $W$ is the proposed reference frame and $B_a$ the acquisition body frame;
  these are qualification evidence, not newly available student inputs. Account
  for extrinsic, timing and motion-estimation residuals without double counting.
  Endpoint poses or integrated velocities alone do not bound unobserved motion
  between timestamps. Unknown timestamps, gaps, unsupported turning or moving
  surfaces remain unresolved. No transform is implemented and no delayed frame
  may be made admissible merely by declaring zero age/latency/noise in Config.
4. **Choose the uncertainty claim explicitly.** A finite residual maximum is
  only an observed maximum, not a universal deterministic bound. A Gaussian
  sigma is not a hard support limit. An empirical tail/quantile proposal would
  need reviewed coverage/confidence, dependence, sample-size and outlier
  conventions; it must not be inserted into the deterministic witness formula
  and described as certainty. For a proposed deterministic enclosure, identify
  the external assumptions supporting every component and the detectable
  domain violations. Retain unmodeled or undetectable outliers as unresolved
  evidence, not presumed removable faults. Decide how any per-zone/per-frame
  claims combine across a tick/history before making an aggregate claim.
5. **Separate fitting, qualification and task evidence.** Propose reviewing
  source/template/device/session/fixture lineage before independent qualification
  groups or any partition are accepted; repeated zones/ticks are not independent
  trials. Preserve untouched reference records and a separately versioned bound
  derivation, then evaluate proposed limits on independently held-out conditions
  without tuning on failures. Record support, exclusions, violations, missingness
  and reference uncertainty, not just successful witnesses. No family, cohort,
  split or sample is assigned here, and current diagnostic logs stay quarantined.
  Privileged metrology/pose evidence belongs only to qualification, not blind
  human review or teacher/student inputs; it does not create task labels.
6. **Review model coverage and authorize release separately.** Even qualified
  hit-location error would not qualify the braking capsule: speed/ego-state,
  reaction/dynamics, deceleration, footprint and obstacle-motion assumptions
  remain separate from this draft's error ball. A proposed acceptance record
  would bind claim/domain, evidence and tool hashes, reference uncertainties,
  derivation, independent results, unresolved failures and reviewer decisions
  to a version. Requalification triggers would include changed mounting,
  sensor/firmware/settings, time base, motion model or operating domain. These
  are proposed review items, not an accepted physical-safety specification.

**Decisions still required before execution or adoption:** which claim/domain
and independent references to use; what collection scope and lineage groups to
approve; any numeric limits, uncertainty coverage and failure/abstention policy;
and whether a separately reviewed evidence model/adapter is compatible with the
accepted inputs and target. Proposed default: keep current abstention and
quarantine until those decisions and evidence are reviewed. Any collection,
hardware work, log application, implementation, label/data/split acceptance or
training requires its own approval. This plan does not qualify real inputs,
clear/negative evidence, mode, Task 6 or Task 9.

#### Synthetic Point-Registration Reference (2026-10-16)

The user separately approved a CPU-only synthetic registration reference and
tests after the documentation-only plan. `register_synthetic_points` in the
[navigation module][navigation-reference] is an isolated static-world planar
transform, not a sensor/observation adapter or qualification of that plan.
It accepts a nonempty array of artificial sensor-frame $(x,y)$ points, explicit
mounting/acquisition/reference poses $(x,y,\psi)$ in metres/radians, and explicit
acquisition/reference times in seconds in one assumed fixture time base. All
three poses are required; no mounting, world pose or timestamp is inferred from
the current student input/history. Explicit synthetic-only opt-in is checked
before reading inputs. Assumptions are caller-supplied, not attestation.

The mounting pose maps sensor to acquisition body; acquisition/reference poses
map those body frames to the same artificial world frame. For corresponding
rotations/translations, the reference computes:

$$
p_{B_r}=R_r^T R_a(R_s p_S+t_s)+R_r^T(t_a-t_r).
$$

Here $t_s,t_a,t_r$ are translation vectors, not the scalar timestamps in the
preceding plan. Relative body translation is formed before rotating, avoiding
the needless loss of small local points in a large common world-coordinate
offset. Each yaw is evaluated separately with sine/cosine rather than subtracting
large angles. This does not recover precision already lost in supplied poses
or provide a certified floating-point error enclosure.

Missing timing or poses returns `unknown` with no transformed points. Malformed,
boolean or nonfinite numeric data and reference time preceding acquisition are
rejected; nonfinite computed coordinates return numerical unknown. Successful
output is `registered_fixture`, with detached reference-frame points, supplied
times, elapsed time and explicit static-world/exact-pose/instantaneous-acquisition
assumptions. No motion is integrated or extrapolated from elapsed time, and no
clock synchronization, skew, exposure interval, outlier, surface association or
moving-object uncertainty is qualified. The supplied common time base and
consistency of the exact fixture poses are not independently verified.

Results stay artificial-only, training-disabled, real-input-unqualified and
without physical safety claims. There is no range/mask or 8x8 adapter, CLI,
episode/history reader, error-ball propagation, witness/label, mode output,
wire decision or data exporter. The function is not called by either witness
probe: their normal-noise, delayed/aged and curved-motion abstention is unchanged.
The previous exact/bounded probes and all existing oracle functions/signatures
are AST-identical to the prior commit. Transforming a fixture does not authorize
zeroing Config noise/latency/age or feeding real/delayed observations to them.

Thirty-six new tests cover six hand-computed identity/translation/rotation/mount
fixtures, composition/inversion, a large common-coordinate offset, large-heading
equivalence, missing/invalid evidence, scope, overflow, detached outputs and
unchanged witness rejection. All 208 simulator tests and 524 repository tests
pass plus the known transformer expected failure; Ruff lint/changed-file format,
editor diagnostics and documentation reference/local-target/whitespace checks
pass. No existing log was processed, new study episode or persisted data artifact
was created, or task label/data/split, live teacher, training, dependency/download
or hardware action occurred. Inputs/history/defaults/token ceiling and quarantine
stay unchanged. Physical uncertainty/registration, target evidence, negative/clear
evidence, mode and actual family/cohort/task data remain unqualified; Tasks 6/9
and the independent ST/board gates are not cleared.

Registration validation follow-up (2026-10-16): seven oversized-integer
point/pose/timestamp cases reproduced an `OverflowError` escaping the documented
`ValueError` rejection contract. Scalar and array conversions now reject
unrepresentable numeric inputs as `ValueError` and check finiteness after
binary64 conversion. Representable-input geometry, signatures, missing-evidence
behavior and witness guards are unchanged. All 22 numeric-rejection cases,
215 simulator tests and 531 repository tests pass plus the known transformer
expected failure; lint/format/editor/doc checks pass. No scope, policy, input,
default, data, dependency or hardware change accompanies this repair.

#### Synthetic Registration Error Propagation (2026-10-16)

The user separately approved CPU-only synthetic point/pose uncertainty
propagation and analytic/perturbation tests. This is an assumed-error geometry
study, not physical qualification, adoption of uncertainty limits or permission
to process observations/logs. The separate `register_synthetic_bounded_points`
API reuses exact registration for nominal geometry and all existing input/scope
guards, without changing that API or integrating either witness probe.

Inputs retain the explicit artificial points, three poses and timestamps from
the exact reference. A required `point_error_m` bounds the Euclidean displacement
of each sensor-frame point. Required `pose_error_bounds` has exactly the keys
`sensor_pose`, `acquisition_pose`, `reference_pose`; each row has exactly
`translation_m` (Euclidean translation error) and `heading_rad` (absolute
angular error, at most pi). Every bound is explicitly supplied, finite and
nonnegative, not boolean, and representable as binary64. These are simultaneous
caller assumptions, not measurements, probability coverage or Gaussian-sigma
conversions. No temporal error is inferred from elapsed time.

Let nominal sensor point be $p$, mounted acquisition-body point
$b=R_s p+t_s$ and registered reference-body point
$q=R_r^T(R_a b+t_a-t_r)$. With point error $\epsilon_p$, translation errors
$\epsilon_s,\epsilon_a,\epsilon_r$ and heading errors
$\eta_s,\eta_a,\eta_r$, the proposed exact-arithmetic displacement enclosure is:

$$
U=\epsilon_p+\epsilon_s+\epsilon_a+\epsilon_r
 +2\|p\|\sin(\eta_s/2)
 +2\|b\|\sin(\eta_a/2)
 +2\|q\|\sin(\eta_r/2).
$$

Changing one transform at a time, applying the triangle inequality and using
rotation norm preservation gives this sufficient enclosure whenever all assumed
component bounds hold. It does not require statistical independence. The three
rotations have distinct lever arms: reference-heading error rotates the entire
relative displacement, not just the original sensor point. Unknown real joint
coverage is not established by this algebra. Floating-point evaluation is
explicitly **not certified**; no interval implementation or physical margin is
introduced. Lost input precision, clock/skew/exposure, moving surfaces, actual
return geometry and braking/state/dynamics/footprint errors remain unqualified.

Successful `bounded_fixture` output contains nominal points, per-point radii,
detached assumed bounds and bounded-error assumptions, not an exact-pose claim.
Its `bound_semantics` is `assumed_model_exact_arithmetic`, with
`floating_point_certified=false`; training/real-input/physical-safety flags stay
false. Missing nominal poses/timing stays unknown; malformed bounds are rejected
and nonfinite enclosures return numerical unknown without points/radii. Zero
assumed errors produce zero algebraic radii, not numerical certification. No
clear/negative labels, witnesses, CLI, range/observation/log adapter, data export
or change to normal noisy/delayed/curved-input rejection is enabled.

Thirty new tests pass: zero-error parity, all seven error components, distinct
translated lever arms, 864 perturbations checked by independent scalar frame
composition, bounds/input/scope rejection, missing nominal evidence, enclosure
overflow and detached results. The finite perturbation grid is a cross-check,
not a universal numerical proof or real-error measurement. All seven existing
navigation functions/signatures are AST-identical to the preceding repair
commit. All 245 simulator tests and 561 repository tests pass plus the known
transformer expected failure; lint/format/editor/doc checks pass. No existing
log, new study episode, persisted data artifact, task labels/data/splits, live
teacher/training, dependency/download or hardware action occurred. Current
inputs/history/defaults/token ceiling and quarantine are unchanged. Tasks 6/9
still need reviewed real uncertainty/registration/target evidence, mode and
accepted family/cohort/task data; ST/board gates remain independent.

#### Synthetic Registered-Point Witness Study (2026-10-16)

The user approved the complete CPU-only synthetic registration-to-positive-
witness work package: implementation, integration tests, independent geometric
checks and documentation. This expands only artificial reference tooling, not
the observation/log pipeline, physical qualification or uncertainty-policy
adoption. `probe_synthetic_registered_witness` in the
[navigation module][navigation-reference] calls bounded registration on the
explicit artificial points, mounting/body poses, timestamps and error bounds.
It does not consume an editable cached result or infer these inputs from logs.

Obstacle membership must be explicitly assumed with
`assume_obstacle_points=True`; absent/false membership yields unknown. This is
fixture occupancy, not observed surface association or attestation. Current
speed, straight motion, footprint and braking dynamics are also exact fixture
assumptions. Config's normal noise and latency still reject, and nonzero current
turn rate abstains. Malformed types, motion limits and inherited registration/
bound validation are rejected. No default, existing exact/ray API or noisy/
delayed sensor input is promoted. Nonzero artificial acquisition-to-reference
elapsed time can be used with the supplied static-world fixture poses; that is
not clock/exposure qualification or permission to zero real-input age/latency.

For registered nominal point $q_i$ and assumed displacement radius $U_i$, let
$S=[0,D]\times\{0\}$ with $D=v\Delta t+v^2/(2a)$. A sufficient geometric
positive criterion is $d(q_i,S)+U_i<r-\varepsilon_{fp,i}$: the entire assumed
obstacle-location ball lies strictly inside the straight swept footprint. No
witness, boundary contact or unsupported/numerically unresolved evidence means
**unknown**, never clear or a negative task label. At rest, $D=0$ tests only the
current footprint. One supported positive can suffice despite other unknown
points; there is no free-space inference or complete-obstacle-coverage claim.

The numerical allowance is an engineering scale guard, not certified interval
arithmetic, measured uncertainty or a physical safety margin. It includes raw
point coordinates and all pose translations as well as registered coordinates,
braking distance, radius and assumed error. Two exact-rational regressions
exposed why output scale alone is insufficient: floating evaluation of
$10^{16}+1-10^{16}$ produced zero rather than the exact one-metre displacement,
creating a nominal near-origin witness. The new probe now returns numerical
unknown in both coordinate-axis cases. Existing registration arithmetic is
unchanged and remains explicitly uncertified; large common world offsets may
conservatively cause this stricter witness guard to abstain even when nominal
relative-coordinate arithmetic is stable.

The only statuses are `blocked_witness` and `unknown`, with point indices,
nominal points/error radii, assumed bounds/timing, braking distance and numerical
allowances. Output stays artificial-only, training-disabled, real-input-
unqualified and without physical safety or floating-point certification. It is
not a wire decision, `path_blocked` label, reviewer suggestion, data exporter,
CLI, range/8x8 adapter or actual registration-evidence validator. Reference
timestamps, static obstacle membership, all error enclosures and exact motion/
footprint assumptions still need real evidence before any separately approved
real-input design; no clock, moving-object or braking uncertainty is qualified.

Forty-one new tests pass. Three independent swept-world comparisons cover a
visible blocked witness, clear-but-unknown and hidden-blocked-but-unknown. Across
three headings, 2,592 separately scalar-composed point/pose perturbations remain
within their assumed enclosures and collide with the independently evaluated
world-frame sweep. These are finite artificial cross-checks, not representative
data, universal numerical proofs or physical measurements. Other cases cover
whole-ball contact, required occupancy, missing/malformed evidence, scope,
immutability, overflow, mixed known/unknown points, at rest and the two exact-
rational cancellation regressions. All eight pre-existing navigation functions/
signatures are AST-identical to the prior commit. All 286 simulator tests and
602 repository tests pass plus the known transformer expected failure; lint,
changed-file format, editor diagnostics and doc checks pass.

No existing log, new study episode, persisted data artifact, task annotation/
dataset/split, live teacher/training, dependency/download or hardware action
occurred. Inputs/history/defaults/token ceiling and quarantine stay unchanged.
Tasks 6/9 still require reviewed real uncertainty/registration/target evidence,
mode and accepted family/cohort/task data; ST/board gates remain independent.

#### Bounded Sensor Diagnostics (2026-10-19)

The user approved this complete CPU-only package on 2026-10-16: diagnostic
tooling/tests, at most four new 32-tick simulation prefixes, a non-label report
and audit. [The isolated collector][sensor-diagnostics] subclasses the existing
simulator's sampling hook without changing its source, Config, student-visible
observations/history or RNG draws. Acquisition tick/time/pose and noiseless
eight-ray references are privileged diagnostics, kept outside observations.
The reference pose is the current simulator pose; the mounting is the existing
coincident planar sensor model. This is not physical registration metrology,
independent reference evidence or a new observation-to-witness adapter.

The deterministic `diagnostic_turn_schedule/1` commands max speed and one-third
max turn rate, positive before tick 16 and negative thereafter. It is neither
an expert nor a navigation baseline. The separate 32-tick collection limit
leaves Config's 400-tick environment limit unchanged. Reset observations count;
actual early termination is retained, while horizon stops are explicitly
censored rather than fabricated timeouts or successes. Fresh output paths,
source/file/observation hashes, full Config/Scenario, seeds and runtime versions
are recorded; family groups/partitions remain unresolved and training disabled.

The [study report][sensor-diagnostics-report] uses seeds 20261019-20261022 for
clear, obstacle, corridor and slalom respectively. Three prefixes stopped
censored at tick 32; slalom collided at tick 31. No goals or environment
timeouts occurred. There are 131 complete observations, including eight
no-delivery warmups and 123 delivered captures. None is a task label.

Range residuals subtract acquisition-frame noiseless model ranges from delivered
float32 values only when a zone is valid, strictly unclipped and has an uncensored
reference surface. Across 3,535 selected zones, observed mean/RMS/max absolute
residuals are 0.000155043/0.0199296/0.0687828 m. There are 672 invalid zones
(including 512 from no-delivery warmups), 2,108 valid clipped zones and 4,177
valid reference-censored zones. Exclusion counters overlap; conditioning biases
the residual distribution, and repeated vertical zones/related captures are
not independent trials. No Gaussian-sigma conversion, fitted/accepted hard
bound, tail-coverage probability or representative-domain claim follows.

For 451 surface-ray columns, noiseless acquisition-to-current-frame point
displacement without registration has observed max 0.184372 m. A shared-model
pose-transform round trip has max 8.88178e-16 m; delivery-age consistency error
has max 1.38778e-16 s. These are software arithmetic checks, not measured clock,
range or registration accuracy. They do not qualify normal noisy/delayed input
for synthetic witness APIs, which are never invoked by this tool.

All file/source/observation hashes, counters, acquisition poses/ticks, scalar
ray-circle/boundary intersections, residuals and pose-displacement arithmetic
were independently checked on CPU without more study episodes. Report SHA-256:
`e560c16d326a6d19c75ff6135ad32df881ab43374f023a34e77e8762b250f3bc`.
Eighteen new tests cover seeded observation/RNG parity at zero/one/two-tick
latency, no-delivery/dropout/noiseless residuals, detached references, limits,
censoring versus real termination, fresh outputs and hashes. Full gate: 304
simulator tests, 620 repository passes plus the known transformer expected
failure; lint, touched-file format, editor diagnostics and documentation checks
pass. Base simulator/navigation, proxies, inputs/history/defaults/token ceiling
and historical artifacts remain unchanged. No task annotation/dataset/split,
accepted family/bounds, live teacher/training, dependency/download or hardware
action occurred. All logs stay quarantined; Tasks 6/9 and ST/board gates remain
blocked on their existing real evidence/data and tool requirements.

Output-path follow-up (2026-10-19, REVIEW.md §47): a report path that was an
ancestor of the episode directory passed the original one-way containment
check, allowing directory creation and collection before report creation failed.
The collector now rejects equal/ancestor/descendant resolved destinations before
any mkdir or collection. Three spy-backed regressions generate no episodes;
all 307 simulator tests and 623 repository tests pass plus the known transformer
expected failure, with lint/format/editor/doc gates clean. No study was rerun
and no historical artifact changed. The report's source hashes describe its
original export at `73a61e8`, not this repaired source. No evidence, policy,
input/default, label/data or hardware gate changed.


#### Simulation-Only Task-Data Protocol Proposal (Unaccepted, 2026-10-19)

The user approved **drafting this protocol only**, not adopting it or executing
collection, packet export, reference evaluation, annotation, split assignment or
training. Call this proposal `sim-task-data-protocol/draft-1`. It preserves the
already-adopted first-three simulation meanings, observation-only human review
with abstention, current-log quarantine and source/template-family review.
Mode remains unlabeled. No physical-domain claim, uncertainty bound, input,
history, Config value, teacher representation or 2,048-token ceiling changes.

**Candidate readiness pilot, not a training/evaluation cohort.** The following
quantities and procedure are proposals requiring explicit approval; they are
not new execution authorization or sample-size/quality requirements:

| Item | Proposed Value | Constraint |
| --- | --- | --- |
| New diagnostic episodes | Eight: two each of clear/obstacle/corridor/slalom | Normal Config, including the 400-tick limit; no existing log is promoted |
| Seed schedule | `20261020 + 2 * scene_index + repeat`, indices starting at zero | Seeds and repeated runs are not independent families |
| Controller | Existing privileged map-aware `ScriptedExpert` | Actions, controller identity and map remain private audit evidence, never reviewer suggestions or labels |
| Candidate review windows | Tick 0, tick 7, tick 15 and the final available tick from each episode | At most 32 unique complete windows; remove duplicates, skip nonexistent ticks, never pad or retry |
| Termination | Preserve actual success/collision/environment timeout | A failed or short episode is retained, not replaced to fill a quota |
| Initial status | Diagnostic-only, unreviewed, training-disabled | No accepted family, purpose, task label or mode label |

Four windows per episode give an upper bound, not a promise of 32 packets or
class coverage. Complete native eight-tick histories/masks/ages must be retained;
startup windows keep their real missing history. Select windows by the declared
ticks, not teacher/proxy answers, geometric truth or a desired class balance.
Do not claim that the existing prefix exporter implements this proposed sampler.
No new sampler, collector adapter or real-review importer is implemented here.

**Separate evidence bundles.** A future source audit would retain original
file/observation hashes, full Config/Scenario, generator and controller revision/
hash, seed, episode identity, parent template and transformation lineage. Exact
geometry matches, mirrored/perturbed layouts, common parent templates and
overlapping histories must be reviewed together. Metadata access is for source
auditors, not blind task reviewers. An independently approved diagnostic oracle
comparison could retain privileged geometry and numerical-unknown results in
this private bundle only; no existing synthetic API is authorized for log use.

The proposed reviewer projection contains only an opaque review ID and the
complete student-visible input/history, with a protected provenance mapping in
the audit bundle. No scene/map, future frame, termination reason, capture-truth
pose/range, controller action, proxy/teacher/oracle answer or mission-intent hint
may be used to force a label. Current fake-only validators and historical blank
packets are preparation evidence, not a claim that this projection or actual
annotation/import is ready. Any required tooling needs separate approval.

**Per-question evidence checklist.** Human evidence sufficiency and independent
geometric target truth are different objects. Matching an oracle is insufficient
if the permitted input cannot distinguish contradictory worlds. Before actual
annotation, review must explicitly accept a simulation-only claim/domain and
its range/return-membership, acquisition-to-current registration, uncertainty,
motion/footprint and spatial-coverage evidence. Current normal Gaussian noise
is not a finite error bound; a residual maximum from the four-prefix study is
not a bound either. No such evidence or convention is adopted by this proposal.

| Question | Proposed Admission Rule Under the Already-Adopted Meaning |
| --- | --- |
| `path_blocked=true` | A supported occupied point/region must intersect the centre braking footprint under the accepted evidence/uncertainty model; noisy unregistered returns alone do not qualify |
| `path_blocked=false` | The whole swept disk must have established strict clearance; absent hits, a clear ray or no observed collision are insufficient |
| `clear_sector` | All three sweeps must be classified before goal-distance ranking; `none` requires all three established blocked; unknown evidence or rest requires abstention |
| `speed_tier` | All three momentum-preserving centre capacity tests must be classified; unknown is not tier 0, and tier 0 does not certify a safe stop |
| `mode` | No annotation; operational intent/precedence remains unresolved |

The existing alias fixtures in this section demonstrate that even complete
eight-tick inputs can correspond to opposite geometric outcomes. A proposed
evidence model must address those counterexamples, restrict its claim/domain
explicitly or abstain; extra seeds, privileged adjudication and an oracle
export cannot remove the information gap. If no admitted labels remain, the
readiness result is **not ready**, not permission to force proxy/geometry labels
or silently broaden reviewer inputs. No negative/clear evidence path is
qualified by the existing positive-only synthetic witness tools.

**Candidate review procedure.** Propose two independent human first passes per
admitted window, each recording a class or explicit per-question abstention,
an evidence rationale and reviewer/procedure versions. This reviewer count is
unaccepted, not a staffing commitment. A later adjudicator sees the same allowed
input and original rationales, not hidden truth/suggestions. Disagreement remains
recorded; unresolved disagreement abstains. Proposed reason categories include
missing history, unknown spatial coverage, unsupported return/range evidence,
unknown registration, unsupported motion assumptions, numerical ambiguity and
reviewer disagreement. These are review metadata, not added wire options.
Report raw reviewed/admitted/abstained/disputed counts and per-class support;
do not infer task accuracy, representative coverage or a confidence threshold.

**Family and five-purpose gate.** At most four scene-parent candidates exist
in this pilot; common generator/geometry evidence may merge them further. Thus
it cannot by itself supply five nonempty disjoint family-level purposes:
training, development, quantization calibration, confidence calibration and
test. Do not manufacture a fifth group by changing a seed, renaming a scene or
splitting nearby windows. All family assignments remain null until review, and
all purpose assignments remain null until a separately approved cohort/split
design has enough reviewed groups. Proposed counts here neither guarantee
independence nor satisfy the production leakage/attestation gate. The existing
synthetic split validator does not attest real files or lock task splits.

**Required decisions and exits, in order:**

1. Accept/modify the intended simulation-only claim/domain and admissible
  evidence/uncertainty conventions, without changing human evidence boundaries.
  If adequate evidence is unavailable, retain abstention and stop before labels.
2. Review the proposed parent-template lineage and explicitly authorize any
  new collection scope, including episode/controller/seed/horizon limits. The
  eight-episode pilot above is not authorized by approval to draft this document.
3. Separately approve any source-audit/reviewer-projection tooling, private
  oracle comparison and blank export; verify complete inputs and provenance
  before approving actual human review/import. No oracle answer becomes a
  reviewer suggestion or automatic task label.
4. Review actual evidence, annotations/abstentions and source-family decisions
  before accepting any task cohort. Do not retroactively promote current
  quarantined logs or replace missing labels with diagnostic proxies.
5. Approve and attest a separate five-purpose manifest before model selection,
  with whole reviewed source/episode/template groups and exact-input duplicates
  confined to one purpose. Neither this pilot nor a hash alone locks a test set.
6. Obtain explicit baseline/training and live-teacher approvals separately.
  Retain normal teacher/input defaults and unresolved mode semantics. ST M1a
  deployment proof remains independent; no large labeling job is approved here.

This protocol is a reviewable readiness proposal, not completion of Tasks 6/9.
All current artifacts remain diagnostic-only and all actual task labels, cohort/
family assignments, splits, inference and training remain unapproved. The first
pending decision is the simulation-only evidence claim/domain, not another
synthetic implementation or an assumption that collecting more data qualifies it.

#### Readiness-Only Pilot (Separately Approved, 2026-10-19)

After the proposal above, the user explicitly approved the **complete CPU-only
readiness package**: tooling/tests, up to eight fresh normal-Config episodes and
32 blank review windows, source audit, verification, documentation and commits.
The claim is limited to simulator/provenance/blank-projection readiness. This
supersedes only the proposal's execution restriction for that bounded package,
not its unaccepted task-data protocol or evidence/uncertainty conventions. No
actual annotation/import, cohort/family/split acceptance, oracle/witness use,
inference/training, dependency/download or hardware action is authorized.

[The separate coordinator][readiness-tool] reuses the unchanged rollout,
full-state renderer, strict blank-packet validation and declared-metadata audit.
It fixes the four scenes and two repeats, seeds 20261020-20261027, normal Config
including 400 ticks, and existing map-aware `ScriptedExpert`. No CLI override
can expand episode count, Config or controller. Selection keeps existing ticks
0/7/15/final, skips missing ticks and deduplicates within each source, never
pads, retries or selects by target/proxy/teacher class. Every observed input is
renderer-validated; this is not full independent action/truth-body validation.

The blind artifact contains opaque UUID-based IDs, exact complete validated
state, catalogue questions and blank assessments, with strict unreviewed/
training-disabled flags. It omits source identities, group metadata, maps,
actions, future outcomes and suggested answers. System-random shuffling does
not consume simulator RNG. The separate private artifact retains validated
original packets and the ID-to-source mapping, exact-input match evidence and
metadata audit. Files are created exclusively with mode 0600 and episode output
directory mode 0700. Only the blind artifact is reviewer input; source logs,
audit and the report contain privileged metadata. Separation/permissions are
not anonymity against recognizable input or access by the same user. All fresh
destinations must be distinct and noncontaining before collection starts.

The [readiness report][readiness-report] records the single bounded run:

| Scene | Seeds | Final Ticks | Outcomes |
| --- | --- | --- | --- |
| clear | 20261020, 20261021 | 133, 133 | Two successes |
| obstacle | 20261022, 20261023 | 138, 140 | Two successes |
| corridor | 20261024, 20261025 | 133, 133 | Two successes |
| slalom | 20261026, 20261027 | 156, 156 | Two successes |

There are 1,130 reset-inclusive observations, no collisions/timeouts/retries,
32 blank projections and 24 complete-history projections. These privileged
controller outcomes are not task labels, representative navigation accuracy or
deployment evidence. Sources/artifacts stay ignored and quarantined; no actual
human review, mode label or task annotation was produced.

**Leakage finding:** the 32 selected windows have only 25 distinct complete
rendered states. All eight reset states are exactly equal, linking every source
through one eight-member selected-input match group. If all these windows and
whole episodes were retained in a future accepted cohort, the adopted no-cross-
purpose exact-input rule would require these episodes to share one purpose.
No family merge or purpose assignment is accepted here, and no warmup window
was silently removed to manufacture a split. Three exact declared-geometry pairs
(clear/corridor/slalom) and four scene-name pairs are further candidate evidence,
not independence proof. Even the four proposed scene-parent candidates were
already insufficient for five nonempty family-separated purposes.

CPU auditing independently checked all eight file/source hashes, canonical
selected-state and binary-frame hashes, actual outcome/contiguous-tick counts,
complete rolling histories/masks, selected line/tick mappings, strict blank
fields, source separation, permissions, duplicate groups and artifact hashes.
The initial host-state audit comparison used Python list/tuple equality across
JSON/codec representations; canonical JSON verified exact values with no artifact
or source repair. Report SHA-256:
`41298178a15979d83eaab354f60a37a6202cd23a6e23789c65eaa0905cc42559`.
Twenty new readiness tests cover exact projection, mutation/scope rejection,
window selection, normal-input limits, no-collection path preflight and fake-only
fixed-run integration. Full gate: 643 repository passes plus the known transformer
expected failure; 101 pipeline tests, lint/format/editor/doc checks pass.

Selection repair (2026-10-19): four synthetic regressions showed that an
observation prefix without a closing summary, or with a mismatched or noninteger
summary tick, was accepted as a final-window source. The selector now requires a
final summary whose strict integer tick matches the last rendered observation.
This syntactic completion guard is not full action/truth-body attestation; the
generic prefix-capable renderer is unchanged. All 24 readiness tests and 105
pipeline tests pass; full gate: 667 passes plus the known transformer expected
failure, with clean lint/format/editor checks. No collection or artifact was
regenerated. The historical report's exporter hashes still describe the original
`dc77a44` version, not this repair; its recorded run evidence is unchanged.

The readiness package is complete and its eight-episode allowance exhausted.
No target evidence, uncertainty bound or real-input registration/coverage model
is qualified; all first-three task annotations still require admissible evidence
and separately authorized review, while mode remains undefined/unlabeled. No
current or new log is promoted to task data, and Tasks 6/9 plus ST/board gates
remain blocked. Next review must resolve the intended simulation-only evidence
claim/domain and any genuinely separate future cohort design, not equate more
seeds, successful privileged rollouts or oracle agreement with task readiness.


#### Gaussian Range-Coverage Proposal (Unaccepted, 2026-10-19)

The user approved this **simulation-only proposal and synthetic checks**, not
policy adoption, a runtime adapter, use on existing logs or any new collection.
No failure budget, confidence/quality threshold or task-label rule is selected.
Normal noise/defaults, input/history, token ceiling and existing witness guards
are unchanged. In particular, a probabilistic proposal does not turn Gaussian
sigma or an observed residual maximum into a deterministic error bound.

**Assumed model and scope.** The [sampler source][simulator-range-source] adds
64 Gaussian values to the repeated eight-ray frame, then applies dropout,
clipping and float32 storage. For the mathematical draft, let the computed
capped noiseless range be $z_i\in[0,R]$ and assume each innovation has marginal
$\eta_i\sim\mathcal N(0,\sigma^2)$, with the normal Config's $\sigma=0.02$ m.
This is an ideal stochastic simulation assumption, not physical calibration or
certification of a pseudorandom floating-point generator; a fixed-seed run is
deterministic. A computed ray range is not independently qualified exact-world
geometry. All geometry/return/numerical issues remain separate claim assumptions.

For a **prospectively fixed** maximum of $N$ innovations and proposed total
failure allowance $0<\alpha<1$, define

$$
b(\alpha,N)=\sigma\Phi^{-1}\!\left(1-\frac{\alpha}{2N}\right),\qquad
E=\bigcap_{i=1}^{N}\{|\eta_i|\le b\}.
$$

The union bound gives
$\Pr(E^c)\le\sum_{i=1}^N\Pr(|\eta_i|>b)=\alpha$ in this exact assumed model.
No independence is needed for that inequality. Test-local arithmetic uses the
equivalent lower-tail expression
`-sigma * NormalDist().inv_cdf(alpha / (2 * N))`, avoiding subtraction from one.
This is not a public API, validated numeric enclosure or adopted risk rule;
unsupported/underflowing/nonfinite arithmetic would need explicit rejection in
any separately approved implementation, not silent zero width or truncation.

The following are **illustrative calculations at unaccepted $\alpha=0.01$**,
not measurements, suggested physical margins or accepted operational defaults:

| Prospective Claim Unit | Conservative Maximum Draws | Formula Half-Width |
| --- | --- | --- |
| One capture | 64 | 0.0756184 m |
| One preselected eight-capture history | 512 | 0.0854037 m |
| One normal-Config episode, reset plus at most 400 ticks | 25,664 | 0.101479 m |
| Eight such episodes, one shared allowance | 205,312 | 0.109119 m |

Eight planar rays do **not** mean eight noise draws: each repeated vertical
zone receives its own innovation. Copied histories are not new independent
evidence. Counts must cover all relevant unique innovations conservatively,
including potentially masked/clipped frames, rather than refunding risk after
filtering outcomes. The 512 count is appropriate only for the specified fixed
window/model, not arbitrary data-dependent choice among episode windows.

**Selection and stopping.** The final tick, an extreme residual or a favorable
window may be chosen using observed data. Reusing a fixed-window allowance at
an adaptively selected time does not establish episode-wide coverage. A
prospective episode/study-wide maximum permits a uniform bound even when later
subsetting, without claiming conditional coverage of the subset. Do not plug
the observed stopping count into a smaller budget after collection, choose
$\alpha$ from observed maxima, tune a rule on test outcomes or multiply
successive probabilities without a reviewed dependence model. For an independent
64-coordinate toy example only, 1% pointwise failures give
$1-(1-0.01)^{64}=0.4744035$ probability of at least one failure, not 1%.

**Clipping, masks and numerical allowance.** Ideal interval projection onto
$[0,R]$ is nonexpansive, so on $E$,
$|\operatorname{clip}(z_i+\eta_i,0,R)-z_i|\le b$.
If a separately justified numerical allowance $\delta_i$ covers storage and all
required computation error, an interval radius would be $b+\delta_i$. A
candidate surface test must require a valid zone and the **untruncated** interval
strictly inside $(0,R)$. Intersecting every interval with $[0,R]$ and then
declaring a surface would misinterpret censoring. Missing/masked zeros, saturated
returns and interval contact remain unknown, never clear or a fabricated hit.

The synthetic grid checks final float32 rounding with the conservative default
range allowance $\tfrac12\operatorname{ulp}_{32}(4)=2.38419\times10^{-7}$ m.
This is not a complete binary64 addition/raycast/transcendental/PRNG error bound,
formal floating-point certification or a real sensor uncertainty limit. The
source uses numerical ray arithmetic; none of its geometric error is qualified
by a final-cast check. Outside $E$, even a censored $z_i=R$ can produce an
apparently interior return through a finite-probability negative innovation;
no finite Gaussian interval is an absolute guarantee.

**Coverage is not label confidence.** A uniform range-error event, combined
with independently justified geometry/registration/membership/motion evidence,
could support a future sufficient-positive argument with an explicit range-
failure contribution. This draft supplies none of those other qualifications.
It does not prove $\Pr(\text{blocked}\mid\text{observed input})\ge1-\alpha$,
precision among positive outputs, calibrated teacher confidence or physical
safety. In an abstract all-negative toy detector selecting only a rare
one-sided error event, the unconditional error rate is small while **every
selected positive is false**. That counterexample is not a module classifier.

Any future claim needs an explicit ledger for range innovations, numerical/ray
error, surface association, acquisition/reference registration and timing,
state/motion/footprint uncertainty and dynamic-world assumptions. Contributions
may be union-bounded only under justified models; unknown entries are not zero.
Positive-only conditional evidence still does not establish whole-sweep free
space, sector ranking or capacity tiers. Existing identical-input geometric
aliases and reviewer-evidence restrictions remain, with mode unlabeled.

Twenty [model-free checks][sim-tests] cover 12 tail-budget combinations, budget
counts/monotonicity, 126 finite clipping/float32 grid points across three example
allowances, masking, a beyond-interval counterexample, selected-positive error
and pointwise-selection failure. No Monte Carlo, study episode, log or teacher
was used; these finite arithmetic checks do not certify the model universally.
All 327 simulator tests and 663 repository tests pass plus the known transformer
expected failure; lint/format/editor/doc gates pass. Only tests/docs changed;
runtime sources and all prior artifacts/hashes are unchanged.

The next genuine decision is the simulation-only claim/domain, its prospective
unit and failure convention, followed by independent evidence for the missing
ledger entries and separately approved tooling/application. No example
$\alpha$, count or width is adopted here. Keep abstention, quarantine and all
Task 6/9, training and ST/board gates in force; no labels or real-input
qualification follow from this proposal.

Subsequent explicit review (2026-10-19, REVIEW.md §51): the user chose **keep
the convention unaccepted; retain strict abstention**. No illustrative failure
budget or prospective claim unit was adopted. This confirms the existing
evidence boundary, not new collection, runtime implementation, log application,
task annotation, physical qualification or training approval. Further progress
requires a new claim/domain or evidence decision; do not repeatedly re-ask the
same risk-choice question merely because autonomous work was requested.


#### Diagnostic Source-Provenance Audit (2026-10-16)

The user approved CPU-only audit tooling, synthetic tests and a read-only run
over at most 16 existing diagnostic logs, producing a non-label evidence report.
This is preparation for source/template-family review, not that review's
acceptance or a task cohort/split. Current-log quarantine remains controlling;
privileged scene metadata remains separate audit evidence, never reviewer input.

The [audit tool][provenance-audit] accepts 1-16 explicit source paths before
opening any source. It requires the simulator metadata header and complete
declared Config/Scenario fields; missing fields are rejected rather than filled
from defaults. The header must fit within 1 MiB and contain finite JSON without
duplicate object keys. All file bytes are hashed in bounded-memory chunks;
source count does not bound total I/O. Observation/action/label bodies are not
parsed or validated, and text-line counts are not reviewed sample counts.
No input source is written, and CLI output must be fresh.

Each row records file/metadata/config/scenario identities, exact declared
geometry identity excluding its name, optional declared seed/policy and source
size/line count. Raw observation, truth, action and label contents are not
reproduced. The tool separately compares file, config, geometry and scene-name
equality. These are **candidate comparisons**, not accepted groups, and are not
merged transitively. Geometry preserves JSON values/types and obstacle ordering;
mirrors, rotations, reordering and near variants are not normalized. Inequality
therefore establishes neither independence nor different lineage. Declared
metadata is not authenticated parent/template provenance. Source/template
families and partitions stay null and unreviewed in every row.

The real offline/GPU-hidden run read eight existing coverage probes, four
label-smoke logs and four wire-smoke logs: 16 distinct file hashes, 22,245,926
bytes and 1,413 text lines. It found no byte-duplicate group, two config-match
groups, three geometry-match groups and four scene-name-match groups. Exact
geometry repeats across open-hold/clear smoke/clear wire, corridor smoke/wire
and slalom smoke/wire. The obstacle smoke/wire names match without an exact
geometry match. These findings demonstrate why distinct file hashes or seeds
cannot be treated as independent evaluation groups; they do not determine the
complete family graph. All file/metadata/config/scenario/geometry identities
and comparison memberships were independently recomputed on CPU.

The [evidence report][provenance-audit-report] has SHA256
`67527a5a2de38726dd3539467ba9f8f95b3b11634f7c14f20907ea63aa1d2ef3`;
tool SHA256 `d530cc49cb6ebc08ca072851c8a636d23028cc4cee01781cf416c41db3fceb09`.
It records zero accepted family assignments, annotations, mode labels or teacher
calls. Every source remains diagnostic-only, with no accepted task cohort,
reviewed dataset, partition or split lock. Eighteen new synthetic cases pass;
54 evaluation/provenance tests and 431 repository passes plus the known
transformer expected failure, with clean lint/format/editor/doc checks.
Existing simulation, proxies, geometry oracle, input/defaults, review packets
and renderer paths are unchanged. No episode, task data, annotation, inference,
training, download/dependency or hardware action occurred. Task 9 still needs
actual family/cohort review and reviewed task data; this audit alone cannot
promote any quarantined log into an accepted purpose.


### Teacher-Pipeline Host Preparation (2026-10-16)

The [host pipeline][teacher-label-pipeline] completes Task 8's approved
**fake-teacher tooling portion**, not live teacher integration or dataset
approval. Its only question is the catalogue's `mode` choice supplement;
the three sensor proxies stay separate and every mode output requires human
review. No proxy formulas, wire identities or simulator CLI were changed.

Rendering reconstructs the exact simulated host state and checks any embedded
CRC-protected frame against it. Plain episode logs instead synthesize that
frame explicitly. The deterministic JSON state preserves decoded FLU fields,
current ToF/masks/age and all eight masked history slots without rounding or
silent truncation. Shape, finiteness, masking, padding and current-slot parity
are checked. Ground truth, actions, scenario geometry and existing labels are
excluded. Catalogue/config/renderer/frame hashes accompany the request; episode
requests also carry source-byte hashes, line numbers, ticks and frame origin.

`python -m teacher.label_pipeline --episode ... --output ... --limit 8` writes
an exclusive request plan for a bounded observation prefix. It never loads
a model, invokes an adapter or emits teacher labels. Persistent plans/cache
data belong under ignored `teacher/cache/`. Planning reads a snapshot of the
whole source file for hashing; the limit bounds rendered observations, not
input-file memory or a complete episode audit.

The Python `label_requests` API accepts an injected test double only under an
explicit `fake_test_only`, `test/` identity with full revision/artifact hash
strings and JSON settings. These are caller-supplied test identifiers, not
attestation of third-party weights or a sandbox. No live adapter is wired in.
SQLite commits each validated response independently. Keys bind the full
request, explicit option order, teacher identity/settings and pipeline source
hash. Stored JSON preserves criteria order, raw response values and unrounded
probabilities; reload checks checksums, identity, scope and normalized answers.
Invalid/error responses never become cache successes. Changed identities or
inputs miss the cache; interrupted batches reuse completed records. Unknown
database schemas and conflicting writes are refused rather than migrated.
All records are synthetic and training-disabled, with human review required.

Two model-free runs selected eight observations each from the recorded clear
wire-v0 and label-smoke logs. Maximum state-string lengths were 9,689 and 9,842
characters, respectively. These are **not token counts**: full-history prompt
fit within the accepted teacher budget is unverified and must be checked before
any separately approved live use. Ignored request-plan SHA-256 values:

- Wire prefix: `a602dfe5adc26a5b691f338ed604ff98b68bdf54f32d7736459506bfc64b810f`.
- Label-smoke prefix: `4284f0697ae969d677e61e29959461bb1228631166def67ceefe693a2d6d3696`.

Verification: 30 [focused CPU tests][teacher-pipeline-tests], 222 repository
passes plus the existing transformer numerical expected failure, Ruff lint,
changed-file formatting and clean editor diagnostics. No real teacher call,
GPU job, download, dependency change, training or hardware action occurred.
Prompt quality, live adapter provenance, token-budget fit, reviewed mode labels
and training-dataset quality remain gated; Task 6 remains blocked.

Follow-up provenance check (2026-10-16): a returned fresh record shared the
batch's nested teacher identity, so consumer edits to that record's settings
changed later provenance/cache keys. Each new record now receives an independent
identity copy. Two regressions first reproduced the defect with fresh/cached
starts, then passed after the one-line fix. All 32 pipeline tests and 224
repository tests pass plus the known transformer expected failure; lint,
changed-file format and editor diagnostics pass. Existing plan hashes above
describe the earlier artifacts; source-bound keys invalidate on this code change.
No real teacher, training, new dependency or change to approval gates occurred.

### Blind Human-Review Preparation (2026-10-16)

The user approved CPU-only preparation for at most 32 existing observations,
not annotations, accepted targets, reviewed datasets or split assignments.
[Review tooling][blind-review-tool] reuses the unchanged full renderer in a
separate module, preserving existing request/cache source identities. Packets
contain the exact structured student-visible state, source line/tick/frame
origin and hashes, plus question IDs/types/options and blank assessments.
Teacher/proxy suggestions, rule formulas, privileged truth and actions are not
included. Mode remains unlabeled and the three rules remain diagnostic proxies.

Packet identities bind their complete contents; state and config hashes and
catalogue options are checked. Reconstructing the observation through the
existing renderer rechecks shapes, numeric values, masks, history padding,
host-frame parity and provenance. The observation schema and existing host
timestamp restore required encoder metadata; no new sensor value or clock is
invented. Source hashes and test identities are consistency checks, not source
attestation or anonymity. Known episode identity is retained; source/template
families and partition assignments are explicitly unresolved and unreviewed.

The CLI accepts repeated existing `--episode` paths and a per-episode `--limit`,
refusing more than 32 total requested records, duplicate source bytes, reused
output/report paths or an existing destination. Limits bound selected rendered
observations, not source-file memory or full-log validation. Packet and summary
schemas are distinct. `normalize_review_fixture` accepts only an explicit
fake-test opt-in and `test/` reviewer identity, preserves abstention reasons and
rejects mode labels. It cannot import an accepted human annotation or promote
anything to a reviewed/training dataset. The test identity is not authentication.

The bounded offline/GPU-hidden run exported clear/obstacle smoke-log ticks 0-15:
32 blank packets from two existing episodes, including 18 full-eight-tick
histories. Zero annotations, mode labels or teacher calls; no partition or
source/template-family review was fabricated. All 32 exact states, complete
input/source/frame provenance and packet hashes were independently audited on
CPU. The 1,238,526-byte packet file stays ignored under `teacher/cache/`, SHA256
`eb0a1d087965fa970a0632adf69e8d715fdb6747a3accfcd9dff992655b8d7f2`.
The [non-label evidence report][blind-review-report] has SHA256
`4795fe33d996109a4276014b33e171350bb084ae615b8ecaec424da900d5f112`.

Twenty-eight added cases pass; 77 pipeline tests and 374 repository passes plus
the known transformer expected failure. Ruff/format/editor diagnostics and
evidence/doc checks pass. Existing renderer, catalogue/rules, simulator and
teacher paths are unchanged; no download, dependency, inference, training or
hardware work. The real run used existing logs only; temporary synthetic unit
fixtures are not study episodes or a task cohort. Tasks 6/9 still require target
definitions, permitted review evidence, family/cohort review and actual reviewed
data. Neither a target policy nor a representative evaluation set is adopted.

Follow-up (2026-10-16, REVIEW.md §33): four failing regressions reproduced
Python equality accepting `true`/`1.0` for question ID `1` and `0`/`0.0` for
grouping `reviewed: false`, even with recomputed packet IDs. Fixed metadata
comparisons now use existing canonical JSON encoding, rejecting those JSON-type
aliases without changing valid packet output or policy. The 81 pipeline tests
and 378 repository tests pass plus the known transformer expected failure;
lint/format/editor diagnostics pass. All 32 existing blank packets validate
unchanged and their recorded file hash still matches. Neither artifact was
regenerated; the earlier tool hash identifies the exporter at generation time,
not the current validator. No target/data/annotation/training gate is cleared.


### Offline Prompt-Budget Preflight (2026-10-16)

The user separately approved [offline tokenizer-only checks][prompt-budget]
using already-cached approved d3 assets, without downloads, weight/model
loading, inference, labels or training. This supersedes the earlier unmeasured
prompt-length status, not the live-labeling prohibition or 2,048-token ceiling.

The tool checks the pinned manifest identity and hashes consumed tokenizer,
configuration and prompt assets. This is **not full model-package verification**:
weights are not read or verified, and full verification remains mandatory for
any separately approved inference. Only the reviewed standard-library formatter
is loaded from a private copy of its verified source; `d3_runtime` and model
constructors are not imported/called. Local fast-tokenizer loading disables
remote code and requires local files; answer codes/token IDs must match the
pinned decision config. Tokenizer/library versions and asset hashes are retained.

For the current choice-only mode request, formatting matches the release's
text-only preparation path, including system/user turns, question, answer codes,
chat template and generation prefix. Counts use no added special tokens,
padding or truncation. The CLI bounds observations per episode and writes an
exclusive report, returning 1 when any prompt exceeds the existing ceiling.
It does not mutate requests, grant live-label approval or run a decision model.

With offline flags and GPUs hidden, both approved cached tokenizers counted
the same sixteen complete requests: the first eight observations each from
the existing clear wire-v0 and label-smoke logs. **Every sampled prompt exceeds
2,048 tokens** for both teachers:

| Tokenizer | Minimum | Wire Maximum | Label-Smoke Maximum | Over Budget |
| --- | --- | --- | --- | --- |
| d3-flash, pinned revision | 3,421 | 6,788 | 6,936 | 16/16 |
| d3-mini, pinned revision | 3,421 | 6,788 | 6,936 | 16/16 |

The [flash report][prompt-budget-flash] SHA-256 is
`f907ff133f2c4cd1e5eea903bc341e5b9b3d1b0b643a3de1f02f81a5b91b99be`;
the [mini report][prompt-budget-mini] SHA-256 is
`505a2476f166928fef02bfff90d7fe97d095db55758c46353284925be84e6627`.
Tool-source hashes and all request digests were independently checked against
fresh rendering; the token-count lists match across tokenizers. These are
bounded-prefix measurements, not maximum lengths over complete episodes.

The current full-history JSON renderer is therefore **not budget-qualified
for live use**. Do not silently truncate, round inputs, remove history/features
or raise the ceiling. A budget-compatible representation needs review before
changing the accepted input/tooling path; teacher quality would still require
separately approved live evaluation. Keep the current budget/input definitions
unchanged while that decision is pending.

Verification: 15 [focused CPU tests][prompt-budget-tests], 275 repository
passes plus the known transformer expected failure; lint, changed-file format
and editor diagnostics pass. No model weights/runtime, inference, labels,
training, dependency change, download or hardware action occurred.

### Lossless Row-Table Draft (2026-10-16)

The user approved a **separate lossless compact-prompt draft, CPU tests and
offline comparisons on existing logs only**. No default renderer, input/history,
token ceiling, live-labeling permission, dependency or hardware scope changed.
This is not approval to round values, remove features or shorten the history.

The [renderer][teacher-label-pipeline] now offers `compact_request_draft`.
It interns byte-identical innermost numeric/boolean rows in a per-request table,
replacing repeated rows with zero-based indexes while preserving outer/time
order. A visible legend describes expansion; unchanged metadata and host state
remain in the text. Numbers are not reformatted or rounded, and JSON keys keep
booleans, integers, signed zero and float spellings distinct during interning.
`expand_compact_state` reconstructs the original canonical state byte for byte;
the factory verifies this against the original SHA-256 before returning. An
expected original hash can also detect valid-looking but altered references.
The default `prepare_request` output remains the full representation. Questions,
option order, source/frame/config provenance and training-disabled scope persist;
separate draft metadata binds codec source and original state identity.

The existing [offline preflight][prompt-budget] adds an explicit
`--compare-compact-draft` flag. Without it, behavior is unchanged. The comparison
counts complete released prompts for both forms and makes no assumption that
the draft is shorter. Reports retain per-request source/tick, both request
hashes/counts and exact reconstruction checks; they never approve live use.

Both cached approved tokenizers were compared offline with GPUs hidden on the
first 16 observations of five existing logs: clear wire-v0 and clear, obstacle,
corridor and slalom label-smoke. **All 80 inputs reconstruct exactly, but the
draft still fails the unchanged 2,048-token ceiling for 65/80 requests**:

| Existing Prefix | Draft Fits | Draft Maximum Tokens |
| --- | --- | --- |
| wire clear | 3/16 | 6,892 |
| label-smoke clear | 3/16 | 7,042 |
| label-smoke obstacle | 3/16 | 8,891 |
| label-smoke corridor | 3/16 | 8,794 |
| label-smoke slalom | 3/16 | 9,698 |

Counts match between tokenizers. Only ticks 0-2 fit in every prefix; none of
the later selected requests does. Full-state counts span 3,421-10,855 (80/80
fail); draft counts span 772-9,698. These bounded prefixes include warm history,
but are not whole-episode maxima, teacher-quality results or a deployment test.
Exact round trips and all original/draft source identities were independently
recomputed from the unchanged logs.

[Flash comparison][row-draft-flash] SHA-256:
`c68c07722ec806bbb0979f9edb3136946c5595aa93539bd1857912d7a3f45b92`.
[Mini comparison][row-draft-mini] SHA-256:
`adc2b9c4ac4433353d0f0d8b1e90dc1656526e535b9cd10c0db6ebfa629d26d0`.

Verification: 42 pipeline and 18 preflight focused tests; 288 repository
passes plus the known transformer numerical expected failure, Ruff lint/format
and clean editor diagnostics. Tests cover cold/warm noisy masked histories,
numeric/type preservation, invalid references, mutation isolation, unchanged
defaults and a tokenizer fixture where the draft is worse. No inference,
weights/model runtime, labels, new episode, training, download or dependency
action occurred. This draft does **not** solve the live-use budget gate; keep
it unreviewed and opt-in pending a separate input-strategy/quality decision.

### Exact Typed Float32 Draft (2026-10-16)

The user approved a second **offline-only lossless draft, CPU tests and cached
tokenizer comparisons**. The default renderer, full input/history, 2,048-token
ceiling and all live-use restrictions remain unchanged. This does not approve
precision reduction, inference, labels, training, downloads or dependencies.

The [row codec][teacher-label-pipeline] accepts `float32_rows=True` only as an
explicit option, producing a separate `sim-teacher-state-row-f32-draft/1` schema.
An all-float row is encoded as `{"f32":[decimal strings]}` only if every value
is exactly representable as IEEE-754 binary32, including its signed zero.
Otherwise the entire row stays literal. Each string is the shorter of NumPy's
unique positional/scientific float32 spellings. The visible legend requires
parsing it as binary32 before promoting to the original Python float, not as an
ordinary JSON numeric value. Thus `0.6000000238418579` can use typed string
`"0.6"` without changing the reconstructed value, while `1.0000000000000002`
and `1e-300` remain literal. The factory still verifies byte-identical original
canonical-state reconstruction and its SHA-256; row interning preserves type,
outer/time order, masks and full history. No physical input precision changed.

The [preflight][prompt-budget] adds mutually exclusive
`--compare-float32-draft` and `--compare-compact-draft` modes. With neither flag,
the original full-state preflight remains unchanged. Typed reports carry a
distinct comparison schema, representation schema, source/asset/request hashes
and exactness checks; every approval flag remains false.

Both already-cached pinned tokenizers were run offline with GPUs hidden on the
same five 16-observation prefixes as the literal-row comparison. **All 80 states
reconstruct exactly, but 63/80 prompts still exceed 2,048 tokens**:

| Existing Prefix | Typed Draft Fits | Typed Draft Maximum Tokens |
| --- | --- | --- |
| wire clear | 4/16 | 4,356 |
| label-smoke clear | 4/16 | 4,442 |
| label-smoke obstacle | 3/16 | 5,487 |
| label-smoke corridor | 3/16 | 5,364 |
| label-smoke slalom | 3/16 | 6,016 |

Typed counts span 811-6,016 and match between tokenizers. Seventy requests are
shorter than the literal-row draft, but only two additional requests fit: tick
3 in the two clear prefixes. All other fits remain ticks 0-2; no sampled
full-eight-tick-history request fits. Original full-state counts and state hashes
match the earlier comparison. Independent checks recomputed every typed request
identity, exact reconstruction and source binding from the unchanged logs.
These are bounded-prefix results, not whole-episode maxima or evidence that a
teacher interprets typed strings correctly. The live-use budget gate is unsolved.

[Flash typed comparison][float32-draft-flash] SHA-256:
`a34f4205ed26e737a66ff6fd4bff3578252a8622a6db52b879dde95e051d20bf`.
[Mini typed comparison][float32-draft-mini] SHA-256:
`9cdf30672cebe06841123204d5499fba7c8704243b56cc4c56f8583d1139b4d4`.

Verification: 49 pipeline and 21 preflight tests, 298 repository passes plus the
known transformer numerical expected failure; Ruff lint/changed-file format and
editor diagnostics clean. Tests cover exact float32 extremes/subnormals, signed
zero, literal fallback for nonrepresentable values, malformed typed rows, noisy
masked histories and explicit CLI opt-in. No weights/model runtime, inference,
labels, new episode, training, download, dependency or hardware action occurred.
Keep both drafts opt-in/unreviewed and the accepted input/budget unchanged;
further input-strategy and teacher-quality decisions require separate review.

### Offline Prompt-Cost Decision Study (2026-10-16)

The second approved decision-preparation task measures **existing inputs and
representations only**, with cached tokenizers and CPU tests. It does not
generate task labels/data, invent another encoding, remove input/history,
raise the 2,048-token ceiling or approve inference/training. The default
renderer, both lossless codecs and accepted policy remain unchanged.

The [preflight][prompt-budget] adds explicit `--profile-input-costs`, mutually
exclusive with both comparison flags. It profiles the unchanged full, literal
row and typed float32 forms. Each form is counted as a complete released prompt;
the existing default path and complete-request budget checks are preserved.
The CLI summary refers to full/default prompts; each form has its own result.

Standalone state text and JSON fields are tokenized separately for diagnosis.
Each fragment includes its own field key/braces and a text hash. **These counts
are not additive, removal-savings estimates, lower bounds or valid request
budgets**: BPE boundaries and wrapper contexts differ. No fragment is rendered
as a teacher request or substituted for a full input. Reports carry original
and representation request/state/source identities, exact reconstructions,
asset hashes, false inference/training approvals and this interpretation.

Both pinned cached tokenizers were run offline with GPUs hidden on the same
80 observations used in the preceding comparisons (five 16-observation
prefixes). All complete/state/field counts match between models. Complete
prompt ranges and failures reproduce the prior evidence:

| Form | Complete Tokens | Over 2,048 | Full-Eight-Tick-History Fits |
| --- | --- | --- | --- |
| full/default | 3,421-10,855 | 80/80 | 0/45 |
| literal rows | 772-9,698 | 65/80 | 0/45 |
| typed float32 rows | 811-6,016 | 63/80 | 0/45 |

The 45 fully populated history windows have these **standalone diagnostic**
field counts; the table does not partition or sum to the full prompt:

| Form / Field | Standalone Tokens |
| --- | --- |
| full `history_tof_m` | 4,771-8,432 |
| full current `tof_m` | 624-1,074 |
| full `history_ego` | 272-601 |
| full `history_tof_valid` | 598 |
| literal `row_table` | 4,562-8,876 |
| typed float32 `row_table` | 2,635-5,131 |
| either row form `history_tof_m` references | 192 |

This suggests numeric contents, not just question/chat wording, drive token
pressure in these forms. It is not a proof that another lossless encoding
cannot fit, that dropping a field saves its standalone count, or that any
representation is understandable to a teacher. No model-quality test occurred.

#### Strategy Choices Still Requiring Review

| Possible Direction | Decision/Evidence Needed Before Use |
| --- | --- |
| Promote an existing exact draft at 2,048 | Current sampled full-history failures prevent promotion; semantic quality is unmeasured |
| Try another exact encoding | Separate draft approval, exact reconstruction and complete-prompt counts, then task-quality evidence; no predicted saving is claimed |
| Use derived summaries or a visual representation | Review any information/precision/input-policy change and teacher/student consistency; no such change is approved |
| Change context budget, hardware or teacher | Explicit resource/revision/licence approvals and measured memory/throughput plus task quality; advertised context length does not prove fit |

**Proposed default:** keep full inputs/history and the existing ceiling. Resolve
the proposed mode/target review first, then select an input/resource strategy
against reviewed task needs. Do not enlarge a labeling job or assume that
further wording cleanup alone clears the gate. If the agreed pilot requires
only computable rules, evaluate their direct value before assuming distillation
is necessary. This recommendation is not an accepted product change.

[Flash cost study][input-cost-flash] SHA-256:
`dfb4dc0bd5078787457425c694986251b2c148aa2055a6539a538d660e80b96c`.
[Mini cost study][input-cost-mini] SHA-256:
`beb69510c75fe8447622226980bb8a5de0882d6411549ba71c427376944d20be`.

Independent verification retokenized every complete/state/field string and
recomputed request/fragment/source hashes: 240 representation rows and 160 exact
draft round trips per model. Existing full/typed counts and original state
identities match the prior reports. Seven new tests pass; 77 focused
pipeline/preflight tests and 314 repository passes plus the known transformer
numerical expected failure; Ruff lint/changed-file format and editor diagnostics
clean. No new episodes, task labels/dataset, model weights/runtime, inference,
training, download/dependency or hardware action occurred.

### Quantization and Confidence

Perform static INT8 PTQ with representative calibration inputs, following
[ONNX Runtime's quantization guidance][ort-quantization] and ST's supported
scheme. Use per-channel weight quantization and standard QDQ operations.
Avoid runtime-specific fused contrib operators unless ST explicitly supports
their exported representation.

Compare floating-point and quantized errors. Introduce QAT only if PTQ fails
the task acceptance criteria. Retest padding, small logits, boundary examples,
and rare classes after quantization.

Fit confidence calibration using the quantized/deployed path and separate
held-out data. [Temperature scaling][calibration-paper] is a simple starting
point, not a guarantee of reliability under distribution shift. Evaluate
negative log-likelihood, Brier score, calibration error, and selective
error-versus-coverage curves alongside task metrics.

[sinc-binding-identity-review]: ../../REVIEW.md
[sinc-compile-comparison-review]: ../../REVIEW.md
[sinc-structural-protocol-review]: ../../REVIEW.md
[sim-tests]: ../../tests/test_sim.py
[navigation-reference]: ../../sim/navigation.py
[sensor-diagnostics]: ../../sim/diagnostics.py
[sensor-diagnostics-report]: ../../sim/reports/sensor-diagnostics-20261019.json
[readiness-tool]: ../../teacher/readiness.py
[readiness-report]: ../../teacher/reports/readiness-pilot-20261019.json
[simulator-range-source]: ../../sim/rover.py
[provenance-audit]: ../../teacher/provenance.py
[provenance-audit-report]: ../../teacher/reports/provenance-audit-20261016.json
[blind-review-tool]: ../../teacher/review.py
[blind-review-report]: ../../teacher/reports/review-preparation-20261016.json
[sim-catalogue-draft]: ../../sim/catalogue.json
[sim-label-draft]: ../../sim/labels.py
[sim-label-smoke-report]: ../../sim/reports/label-smoke-20261016.json
[sim-label-coverage-report]: ../../sim/reports/label-coverage-20261016.json
[teacher-label-pipeline]: ../../teacher/label_pipeline.py
[teacher-pipeline-tests]: ../../tests/test_label_pipeline.py
[prompt-budget]: ../../teacher/prompt_budget.py
[prompt-budget-flash]: ../../teacher/reports/prompt-budget-d3-flash-20261016.json
[prompt-budget-mini]: ../../teacher/reports/prompt-budget-d3-mini-20261016.json
[prompt-budget-tests]: ../../tests/test_prompt_budget.py
[row-draft-flash]: ../../teacher/reports/row-draft-budget-d3-flash-20261016.json
[row-draft-mini]: ../../teacher/reports/row-draft-budget-d3-mini-20261016.json
[float32-draft-flash]: ../../teacher/reports/float32-draft-budget-d3-flash-20261016.json
[float32-draft-mini]: ../../teacher/reports/float32-draft-budget-d3-mini-20261016.json
[input-cost-flash]: ../../teacher/reports/input-cost-d3-flash-20261016.json
[input-cost-mini]: ../../teacher/reports/input-cost-d3-mini-20261016.json
[calibration-paper]: https://proceedings.mlr.press/v70/guo17a.html
[ort-quantization]: https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html
[px4-gazebo]: https://docs.px4.io/main/en/sim_gazebo_gz/
[dagger]: https://arxiv.org/abs/1011.0686
