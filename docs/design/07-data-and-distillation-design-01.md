## 7. Data and Distillation Design

Task-specific distillation into simpler networks has published support, for
example [Tang et al.][distillation-paper]. This supports the approach, not a
guarantee that a particular micro-student preserves broad teacher capabilities.

### Rules Baseline Admission Brief (Proposed, 2026-11-05)

**One candidate for review, not adoption.** Following §12's priority reset,
propose an explicitly ideal-simulation, coverage-first C1 rules baseline. This
consolidates the existing synthetic results into an admission and evaluation
contract; it does not qualify their sources or numerical allowances. The first
deliverable after approval would be a bounded Python rule-to-wire-to-host trial,
not device emulation, firmware, task labels or a trained model. [Review §145][baseline-admission-review]
records the source observations, open decisions and verification of this brief.
Existing defaults, diagnostic heuristics, targets, wire bytes and quarantine stay
unchanged. The older C1 sections below retain their original scope and evidence.

#### Candidate Sensing and Scene Domain

| Component | Proposed trial profile and admission boundary |
| --- | --- |
| Sensing | The existing experimental C1 ring: eight simultaneous 8x8 point-ray views at yaw offsets 0 through 315 degrees in 45-degree steps, coincident body-centred origins at 0.15 m height, each with 45-degree local field and 22.5-degree downward pitch. This is a virtual information profile, not eight selected devices or continuous angular coverage. |
| Returns | Ideal static first intersections with flat floor, cylinders and outer walls; zero range noise and zero stochastic dropout. Preserve binary32 rounding, ray identity and masks for missing, nonpositive, saturated or unsupported returns. Deliberately injected masks/occlusion are challenges, never synthetic max-range clearance. No Gaussian bound or physical optical/material claim. |
| Timing and retention | Existing 20 Hz decisions, nominal 15 Hz tick-quantized simultaneous captures, two-tick delivery and at most eight consecutive snapshots. Geometric support comes only from the latest supported acquisition; repeated held batches neither refresh age nor add views. Proposed latest-age ceiling: three ticks (0.15 s), preserving the experimental restriction, not adopting a hardware deadline. |
| Motion and goal | Exact, synchronous planar simulator-source evidence for acquisition-to-reference relative translation/heading, current forward speed/yaw rate and FLU body-frame goal. Host values must come from the actual decoded state bytes with known zero ego/goal ages. Exact source values are not automatically exact after binary32 encoding; changed values need a justified enclosure or rejection. |
| Embodiment | Existing fictional circular body radius 0.18 m, forward speed limit 0.6 m/s, acceleration/deceleration 1 m/s² and turn limit 1.5 rad/s. Keep the adopted age-plus-one-tick reaction and separate braking-turn meanings. These are simulation parameters, not physical stopping specifications. |
| Scene envelope | Static flat-floor cylinders with radius 0.05-0.30 m and height 0.05-1.0 m, and the existing axis-aligned 1 m outer walls. Arena axes, dimensions and source-scale provenance must be bound to the input. This previously approved synthetic envelope is proposed for this trial only; no global object restriction or new world-size limit. |
| Unsupported domain | Moving objects, slopes/steps, overhangs, other shapes/material physics, asynchronous scans, nonzero/unqualified range/pose/clock errors and lost source epochs remain unsupported. The 5 mm cylinder alias stays a supported simulator regression but outside this candidate's admitted domain, not a silently removed obstacle. |
| Identity and location | Use a distinct opt-in experimental simulation identity; C1 ranges and retention remain module-local. The 92-byte host state and catalogue-1/model-0 decision tooling remain the transport reference. Runtime/profile versioning must be reviewed before normal adoption; this brief assigns no new numeric wire/profile ID. |

The range ceiling is 4 m, not proof that every relevant object is observable.
Admission must exclude every permitted cylinder-centre cell intersecting the
outer maneuver tube, with the declared radius/height bands and wall bounds.
Finite rays, nominal ring bearings and floor support alone do not meet that
condition. Occlusion may still permit a conclusion when remaining qualified
evidence resolves the entire sweep; otherwise it is unknown. Positive evidence
instead needs an above-floor occupied-return enclosure strictly inside an inner
swept-body disk. Outer-tube membership is never a collision witness.

#### Evidence Owners and Unknown Conditions

| Required premise | Proposed source and missing evidence | Required behavior without it |
| --- | --- | --- |
| Domain and initial body clearance | Reviewed static scene manifest plus independently checked initializer preconditions, without obstacle coordinates or target answers in the rule input. Whether setup attestations are admissible evidence for this simulation trial requires approval. A true fixture flag is not qualification. | Reject admission; absence of an occupied witness cannot prove the current body clear. |
| Continued body clearance | Proposed invariant from an independently admitted launch and every actual host command plus its fallback sweep; reset, unaccounted motion, contact or an expired command invalidates it. This invariant is not implemented or proved by current owner records. | Unknown/rejection until independently re-established; no per-tick oracle refresh. |
| Return and coverage semantics | The declared ideal ray model, full range-rounding/transform enclosures, floor separation and continuous-centre/wall exclusion. Existing C1 tests are conditional evidence, not certified bounds. Missing/occluded rays constrain support rather than imply empty space. | Unknown on any unresolved region relevant to the queried sweep. |
| Acquisition, registration and clocks | Named source owner binds actual batch, acquisition/reference epochs, relative transform and decoded host bytes. Existing fixture record consistency does not qualify native motion, goal transforms or binary32 equivalence. | Stale rejection for missing/over-age delivery; unsupported evidence or epoch/identity gaps reject rather than interpolate. |
| Maneuver and numerical support | Keep two-phase trajectories, source-scale allowances, strict inner/outer distinctions and existing cell/depth/band/segment caps. Qualify only calculations needed by this baseline gate; unrelated arithmetic/identity audits stay deferred. | Unknown on overflow, contact ambiguity, unsupported error, work exhaustion or overlapping goal ranks. Never increase caps or weaken margins to pass. |
| Goal and host execution | Valid decoded body-frame goal aligned to the decision reference, and a separately reviewed exact command/fallback contract. Goal distances are not obtained from world-frame fixture goals at runtime. | Sector unknown for invalid/stale/unresolved goals; no unqualified selected-sector/speed combination reaches actuation. |

Private complete geometry, true trajectory and the [navigation reference][navigation-reference]
belong only to qualification assertions and the separately authorized evaluator,
not the rule, startup chooser or host-command chooser. Domain/setup evidence
must be explicitly scoped, not an oracle supplying a fresh answer under another
name. Records must distinguish conditional fixture consistency, qualified
input evidence, question resolution, admitted command and measured task quality.
No current false qualification flag or undecided audit verdict is promoted.

#### Per-Question Admission

Use the adopted simulation meanings and [C1 question coordinator][c1-prototype-source],
not the old sector-minimum heuristic. All rows also require the evidence above.
"Unknown" is internal absence of an answer, not another option or a fabricated
uniform distribution. A conflict invalidates the entire bundle.

| Question | When it may answer | When it must remain unknown |
| --- | --- | --- |
| `path_blocked` | For the centre maneuver, false needs whole-sweep exclusion; true needs an occupied-return enclosure strictly inside the swept body. Reaction uses the measured current turn; centre braking uses zero turn. | No complete exclusion and no qualified positive witness; unresolved contact/error/work; any clear/blocked or current-body contradiction. |
| `clear_sector` | At nonzero speed, resolve centre/left/right maneuvers first. Braking turns are 0, +1.5 and -1.5 rad/s after the common current-turn reaction. Select the clear endpoint with bound-separated best goal distance; retain the adopted exact symmetric left/right tie favoring left. `none` requires all three blocked. | At rest; any unresolved maneuver or goal/rank; merely no known-clear option; contradictions. A side return or one known-clear sector alone does not suffice. |
| `speed_tier` | Resolve all three centre-braking capacities at `max(current_speed, 0.6*tier/3)` for tiers 1-3. Select the highest clear capacity; tier 0 requires all three blocked. | Any unresolved capacity, including a higher tier; contradictions. Lower requested speed never erases existing momentum, and tier 0 is not unknown. |

#### Wire and Host Admission

The [wire contract][wire-python] already requires catalogue 1, model 0 and mask
7 for `OK`; a full rules decision is 100 bytes. Proposed trial behavior is
`OK` only for three resolved, mutually consistent questions with admitted input
evidence. Partial/unknown results remain rejection diagnostics, never usable
recommendations. Preserve missing/late/CRC-invalid/version/sequence/timestamp
rejection and independent host braking. Proposed status precedence is malformed
or unsupported schema first, stale input next, out-of-domain/unqualified evidence
next, unresolved geometry/ranking as `REJECT_OUT_OF_DOMAIN`, and unexpected
computation failure as `FAULT`; no new status or confidence threshold.

Wire probability policy needs explicit review. Proposed diagnostic encoding is
a degenerate distribution for a deterministic selection, clearly identified as
uncalibrated in the experiment record. Codec-derived Jev confidence, including
unit choice/score confidence for one-hot values, is not correctness probability
or a clearance guarantee and must not control admission. Noul retains its absent
confidence. No unknown is encoded as false, `none`, tier 0 or an invented model.

**Two integration blockers, not simulated successes.** Source inspection shows
that the [existing diagnostic host controller][baseline-host-source] brakes on
rejection, while the C1 coordinator leaves sector unknown at rest. A direct
replacement can therefore remain stopped forever from reset. The same host
controller applies goal-proportional steering for centre and combines a sector
with a centre-only capacity tier; those commands are not necessarily the
reaction/braking sweeps C1 admitted. These are source-level incompatibilities;
no new wire-loop or episode reproducing them was run for this brief.

Proposed default: retain the question meanings and complete-OK rule. Require a
separate host-owned, independently supported startup protocol, with one bounded
launch and explicit fallback, before demanding moving-state module coverage.
The launch cannot consume partial decision selections, private geometry or an
oracle-selected action. Exact launch speed/duration and its clearance evidence
are decisions still needed; moving fixtures alone cannot satisfy reset-to-goal
M2. Include startup, warmup and failed relaunches in end-to-end outcomes, not
silently discard them from the success denominator.

For subsequent motion, require command admission for the actual one-tick
acceleration/yaw command followed by the independent braking fallback. Do not
assume that separately resolved sector and centre-capacity answers qualify their
combination, or that replanning resets reaction/registration error. Unknown,
expired or unqualified command support means braking, even after an `OK`
question frame. The owner, location and interface for this extra guard require
review; the existing host controller is not promoted unchanged. A guard based
on module-local ranges is not silently moved to a sensorless host. Physical
actuation, interlocks and flight fail-safes remain outside this simulation trial.

#### Prospective Evaluation and Failure Gates

**Proposed limits, not approved fixtures or runs.** First an isolated synthetic
integration test increment, reusing existing packages/tests and per-query caps:
at most 24 declared cases across at most eight existing complete scene records,
with no new world coordinates or episodes. Propose at most 48 coordinator
attempts in the new test family per complete focused/default invocation and at
most four such invocations including failures, repairs and the root gate (192
attempts total).
Each retains the existing maximum six named question queries; any future
command-guard executions need their own explicit accounting before approval.
Running existing bounded fixture families in the root gate also requires an
explicitly named regression renewal; the 48/192 limits cover only the new family,
not hidden allowances for old entries. Preserve each family's old controls/caps.
Do not borrow old fixture budgets, unused fifth positions or deferred SC18-v0.
This increment tests the reviewed input/unknown/wire/host contract, not source
qualification by assertion or representative task quality.

Only after the input, startup and command gates pass, propose a separately
approved CPU-only batch of 32 episodes, at most 400 ticks each, with no tuning
or second batch. Sixteen nominal episodes cover clear, obstacle, corridor and
slalom families, four frozen seeds per family. Sixteen challenge episodes cover
the four rows below, four frozen variants each. Exact geometry, seeds, expected
challenge outcomes, initialization and lineage must be reviewed and frozen
before collection; none is generated or assigned here.

| Evaluation stratum | Cases and required discrimination |
| --- | --- |
| Nominal navigation | Clear/obstacle/corridor/slalom with straight and both-sign turning, varied goal headings, speeds/momentum and low/tall in-envelope cylinders. Measure reset-to-goal outcomes and moving-state answers, not only favourable isolated clear fixtures. |
| Spatial and vertical challenge | Mirrored normal-cylinder aliases, the 5 mm out-of-envelope alias, floor-adjacent/rounded heights and foreground occlusion. Preserve original single-view ambiguity; C1 visibility gains are necessary but not universal clearance. Unsupported aliases must not receive admitted clear commands. |
| Temporal and return challenge | Held captures, partial/masked/missing batches, occlusion, late delivery, stale ego/goal, lost history/epochs and asynchronous views. Expect the specific unknown/rejection or justified remaining support, not blanket assumptions of clearance. |
| Numerical and logical challenge | Tangency/near contact, one-segment outer-tube counterexamples, rank overlap/exact tie, invalid domain/body declarations and contradictory evidence; work exhaustion and source-scale/binary32 changes. Keep known negative regressions and all false flags intact. |
| Host and transport challenge | At-rest startup, rejection-to-braking, goal-steered centre mismatch, sector/tier combination, expired command, missing/late/duplicate/out-of-order/corrupt frames and reset. Check actual commands, not merely successful decoding. |

Report per-question answered coverage, complete-OK coverage, admitted-command
coverage and unknown reasons separately. Denominators include every scheduled
tick; also report post-warmup, supported moving-state coverage, with exclusions
listed by reason and family so startup, faults and hard cases cannot disappear.
Supported-moving eligibility must be fixed from domain/input/timing conditions
before inspecting rule outputs. Work exhaustion and unresolved coverage/ranking
remain in that denominator, not retrospective exclusions. Require resolved
reference support for every active option from at least two episodes with
distinct acquisition/input identities; publish answered/rejected counts per
option. Missing options fail bundle qualification, and held-frame repetition
does not satisfy this minimal class-support gate or establish representative
frequency/independence.
Reference-unknown comparisons stay unscored and count as reference coverage
loss, not matches. Report false-clear (`path_blocked=false` against resolved
blocked truth), false-blocked, wrong sector/tier, unsafe command, collision,
success and timeout counts, both conditional on answers and over all exposures.
Held snapshots are not independent samples or added confidence evidence.

Proposed acceptance numbers are engineering review defaults, not measured
achievability, statistical risk budgets or physical safety limits:

- Zero false-clear, false-blocked, wrong resolved sector/tier, unqualified/unsafe
  admitted command or collision in the bounded trial. Any such event stops admission;
  preserve the failing evidence rather than tune or rerun automatically.
- Every declared unsupported/stale/conflict/transport/command-expiry control
  must give its required rejection and host fallback. Unknown is acceptable
  where specified, but does not earn answered coverage or navigation success.
- In each nominal family, at least 80% post-warmup supported moving ticks
  answered per question and at least 60% complete-OK coverage. Also publish
  full-episode and command coverage; always-reject fails regardless of collisions.
- At least three of four nominal episodes succeed in each family; at most one
  timeout per family and zero collisions. Challenge outcomes are assessed against
  frozen expectations, with censored/rejection timeouts disclosed, not successes.
- Record wall-clock decision/command-guard time, peak host memory and actual
  deadline misses. Before a real-time 20 Hz host trial, review a receipt-to-command
  deadline and demonstrate timely admission/fallback; the simulated 0.05 s tick
  alone is not execution-time evidence or an adopted physical deadline.

Preserve the failed heuristic's four successes, two collisions, two timeouts
and 25 false-clear reference comparisons. Its quarantined logs and registered
candidate replay are negative diagnostic baselines, not a new locked cohort.
Use independent complete-geometry assertions only in authorized evaluation;
record source identities, input/frame/command provenance and reference limits.
Metrics may include macro-F1, per-class recall, NLL, Brier and ECE on resolved
reference cases, with unknown denominators and infinite NLL explicit. Degenerate
rule outputs do not acquire calibrated uncertainty because these metrics run.

For this rules-only proposal, request one frozen prospective test cohort, with
synthetic qualification fixtures kept separate; no training or calibration
partition is needed merely to execute deterministic rules. Review source/template
families and exact-input duplicates before accepting any cohort, including shared
reset windows. This does not waive the five-purpose separation for later learned
work or adopt a split. Four scene names are not four independent lineages.
Future selection/tuning requires a separate development cohort and a new holdout
decision, never reuse of this bounded test. New artifacts would remain ignored,
purpose-tagged and non-training; paths/byte budget/retention require run approval.

#### Decisions and Smallest Next Scope

| Decision | Proposed default and approval needed |
| --- | --- |
| D1: claim and input | Review the ideal-simulation C1/latest-relative-batch candidate above as a separate opt-in trial, preserving normal defaults and physical non-qualification. Decide admissible domain/setup, registration/decoded-wire and numerical evidence before any `OK` trial integration. |
| D2: host contract | Preserve at-rest unknown and the complete three-answer contract. Select an independently supported startup and exact command/fallback guard, its owner/location/interface and bounded execution accounting. Without this, only conditional fixture/rejection integration is unblocked, not a closed-loop baseline. |
| D3: output and implementation | Review deterministic diagnostic probability/status policy and the bounded 24-case/eight-scene/48-new-family-attempt/four-invocation test increment, including explicit affected-regression gate renewal. Reuse current helpers/tests; keep the old heuristic/default wire loop unchanged. No episode, native port or source-verdict promotion follows. |
| D4: evaluation | Accept or revise prospective coverage/failure thresholds, independent references, family/duplicate policy and exact 32-episode manifest/resource/retention scope only after D1-D3 gates. This brief requests no collection, labels, data acceptance, split lock or repeat run. |

Recommended next action is a single review of D1-D3, then the smallest approved
source/evidence and wire/host test increment that can falsify this candidate.
Any unresolved source or host obligation remains a named blocker; do not insert
true flags, narrow the targets or restart general audits to make progress appear
complete. ST licence/install and board/ToF readiness remain parallel user-side
M1a/M1b actions. Native/board integration follows its gates; learning/distillation
and M6 remain deferred. Preparing this brief adopts none of these proposals.


#### Conditional C1 Input-to-Wire Rejection Tooling (2026-11-05)

The user approved the brief's recommended bounded conditional input-to-wire/
rejection increment, keeping startup, actuation and episode runs blocked.
That increment is complete. It does not adopt D1's input/source qualifications,
D2's host command policy, runtime probability calibration or D4's evaluation
scope. [Review §146][c1-wire-rejection-review] records actual checks and the
four-position budget, including the failed reporter teardown.

The private `_probe_synthetic_c1_wire_rejection` in the [C1 prototype][c1-prototype-source]
accepts an explicitly synthetic source State, its actual encoded bytes and an
existing relative fixture. Literal synthetic opt-in is required. It validates
the frame through the decoder, binds exact frame bytes to the source and rejects
changed decoded values before any C1 query. This tests correspondence, not the
source's authority: unchanged bytes do not qualify registration, scene/body
declarations or numerical allowances. In particular, encoded 0.6 m/s rounds
above the source value and is rejected, not clamped or granted a new tolerance.
The exact 0.5 m/s fixture reaches conditional questions without changing defaults.

Missing host groups, nonzero ego/goal ages, unsupported/CRC-invalid frames and
source-frame mismatches reject. Existing C1 checks retain invalid goal binding,
unsupported transform/domain/body evidence, missing returns, stale captures,
bounded-work exhaustion and at-rest sector unknown. Candidate summary controls
reject invalid options/status combinations or nonliteral false qualification
flags; a contradiction discards every outer candidate. Injected unexpected
question-evaluation failures are logged and map to empty `FAULT` diagnostics.
This is a bounded fixture path, not a general live input or callback API and
not a universal allocation/publication guarantee.

On ordinary return, it serializes only known candidates as degenerate diagnostic
distributions with catalogue 1/model 0 and echoes a successfully decoded frame.
Nulls omit answers rather than becoming false/`none`/tier 0. Even three resolved
fixture answers remain `REJECT_OUT_OF_DOMAIN`: no `OK` escape hatch exists.
Training, real-input/free-space/numerical/source qualification and host-command
admission remain false. The existing Python host rejects every resulting frame
and caller-declared absence; tests assert braking output without stepping the
rover or claiming physical braking. Codec-derived confidence is unchanged and
uncalibrated; the diagnostic convention is not adopted as runtime uncertainty.

Twenty-four cases reuse two existing complete scenes, within the approved eight-
scene/48-coordinator-attempt/four-invocation ceilings. Each complete new matrix
makes 48 adapter requests, 32 relative-bridge calls and ten coordinator calls,
with two captures; old six-query/per-query bounds remain unchanged. Exact clear/
blocked, partial/rest, held-copy ownership, stale/frame/goal mismatch, missing/
masked input, unknown body/domain/error, work exhaustion, fake-only summary/
conflict/flag/fault and strict opt-in controls pass. Partial or even full
rejection diagnostics round-trip through the codec/stream and never reach host
actuation. This is neither representative option coverage nor M2/task quality.

The required root gate passes 2,269 tests plus the known transformer xfail and
71 existing warnings; changed-file formatting, syntax/editor diagnostics,
whitespace and exact prior source/test AST preservation pass. Normal simulator/
rules/host paths, catalogue/wire/profile defaults, old fixtures and historical
artifacts stay unchanged. All four approved verification positions are spent;
existing root regressions ran only within the approved default-gate renewal.
No further fixture replay, source-gate repeat or unused old budget follows.
Next: decide admissible baseline source evidence and independent startup/actual
command/fallback owner, interface and acceptance checks. Until then no admitted
closed-loop baseline, source-verdict promotion or new task-data run exists.


#### Source and Command Admission Contract (2026-11-06)

**Requirements adopted; not implemented, qualified or authorized to execute.**
The user accepted the recommended requirements-only adoption after the design
preparation in [Review §151][source-command-admission-review]. This fixes the
S1-S5 obligations, simulation-only boundary and candidate startup/map/fallback/
work limits for future scoped work. It does not change the question meanings,
complete catalogue-1/model-0 `OK`, normal profiles, source verdicts or the
completed rejection adapter. The candidate remains an opt-in ideal-simulation
trial with the existing C1 latest synchronized batch, relative inputs and
synthetic cylinder/floor/wall envelope. No evidence is thereby satisfied, no
source/test/run budget is renewed, and no device profile, numerical certificate,
physical safety claim or task-data approval follows.

**Source admission is a record of evidence, not a supplied true flag.** Required
records bind a profile/source revision, immutable configuration identity,
simulation epoch, host sequence/timestamp, exact state-frame bytes, source event,
C1 capture identity/tick, reference tick and predecessor admission identity.
Hashes establish correspondence, not authority. Require all of the following
independently supported rows; missing or inconsistent evidence means unknown.

| Obligation | Required owner/evidence; satisfaction unverified | Stop / invalidation |
| --- | --- | --- |
| S1: Domain and initial body | Separate setup auditor checks the declared static synthetic scene envelope and initial body against the complete fixture, then binds the result to the epoch/configuration. Private geometry stays offline, not in command selection. Later body-clear support requires the preceding admitted sweep and its retained uncertainty. | Unsupported object/floor/wall, absent setup evidence, reset, changed scene or a gap in the predecessor chain invalidates admission. No absence-of-hit or current oracle answer can supply body-clear. |
| S2: Sensor source and coverage | Module-side C1 source retains all eight synchronized virtual views, exact payload/masks, mounting and capture/reference provenance under the existing retention rules. Independent return/coverage checks must support the requested swept region, including occlusion and missing returns. | Mixed epochs/views, missing or unsupported returns, unsupported swept regions or expired retention stay unknown. Keep normal/slender-cylinder, masked and floor/height counterexamples. |
| S3: Host and decoded state | Host state owner supplies the exact source event and encoded frame; the module decodes actual bytes and verifies the event/frame/profile binding, validity and fresh ego/goal groups. Source intervals enclose the actual simulated state, not just the decoded values. | CRC/schema/binding/age failures reject. World goal/pose cannot replace decoded host input or select an action. Source authority is not established by matching bytes. |
| S4: Quantization and numerical/registration error | Independently check exact stored source and binary32 words, enclose their discrepancies, and propagate them with timing, pose, range, arithmetic and motion-implementation allowances into every affected sweep/rank/goal claim. Each allowance needs its declared domain, method, version and remaining gap. | No clamp, guessed epsilon, Gaussian-sigma conversion or unaccepted certificate closes a gap. Unsupported or overlapping bounds abstain; re-planning does not reset accumulated error. |
| S5: Clock and execution identity | Source/guard owners bind capture, reference, host receipt, requested command, application tick and fallback to one epoch and immutable configuration; external qualification must establish the timing/error contract. First candidate keeps fresh host ego/goal requirements. | Missing timing support, delayed application, replay, out-of-order state, changed configuration or epoch expiry invalidates the response. A simulated tick is not a wall-clock deadline. |

S4 is a specific missing baseline gate, not permission to resume general
arithmetic audits or the deferred SC18-v0 process. A future numerical study
would need its own named consumer, independent method and approved bounded
scope; the existing undecided verdicts and false flags do not become evidence.
The old 0.6 m/s rounding rejection must remain. A separately implemented source
profile could admit decoded inputs only with qualified discrepancy enclosures
and their propagation, not by weakening `_probe_synthetic_c1_wire_rejection`
or declaring decoded values equal to the true simulated state. No such profile
or propagation implementation is supplied by this contract.

**Simulation-only interface requirements.** Keep state/decision bytes unchanged.
For this opt-in simulation candidate only, require a separate, explicitly
named in-process request/response boundary; it is not an existing API or UART
message. A future board/transport design needs separate review. The host
proposes a command from decoded state and permitted decision fields; a
module-side guard owns C1 access. The sensorless host receives no raw C1,
private geometry or reference answers. A simulation executor is the sole
consumer of a matching one-use guard response and remains host-owned.
The in-process boundary freezes host-owned command/state fields together with
module-owned C1/reference identities before checking. The host does not choose
a capture or need raw sensor access; the response carries the frozen binding.

| Required record; not implemented | Required content / semantics |
| --- | --- |
| Command request | Unique request ID; exact finite binary64 target speed and yaw-rate words for this host simulation; application tick; `STARTUP` or `NORMAL` control phase; source/profile/config/epoch, host-frame and C1/reference identities; one-tick hold; declared braking fallback. Phase is not a new question or a `mode` label. A normal request also binds the exact complete-`OK` decision bytes. |
| Guard response | Exact request identity/content, source-admission identity, `ADMIT`, `DENY`, `UNKNOWN` or `FAULT`, rejection reason, swept-motion evidence identity and expiry at the requested application tick. Distinguish an established constraint/policy denial from missing or unresolved evidence. Only `ADMIT` with fully supported evidence can authorize that exact request once; status is not a confidence score, collision label or catalogue answer. |
| Executor receipt | Request/response identities, application tick and the exact submitted command; distinguish requested command, acceleration/clipping result and actual applied motion. A changed, duplicate, missing, late or mismatched response cannot authorize a different command. An execution gap invalidates the predecessor chain. |

An `OK` decision alone never admits a command. In `NORMAL`, absent, partial,
rejected or expired question output always causes fallback; a guard response
cannot manufacture missing normal answers. In `STARTUP`, expected at-rest
question unknown/rejection is not an authorization: only the separate supported
setup and dedicated startup permit may admit the one-shot candidate. Fresh
valid host/source evidence is still mandatory. In either phase, state/transport
failure or a missing, denied, unknown, faulty or expired permit means braking,
never partial-selection consumption. The executor serializes check-and-consume
before application, rejects already-consumed IDs and records an application
failure as a gap, not an automatic retry.
Do not silently overload health/task/validity fields or encode a permit in
confidence, a diagnostic selection or an old rejection packet.

Record fallback execution even when no new permit exists. A retained admitted
braking tail supports later body-clear only while the actual actions, timing
and uncertainty stay within that tail; otherwise body-clear becomes unknown
and independent braking continues. Permit expiry cannot authorize a new motion
from an old tail. A new reset/epoch needs new independently supported setup,
not an automatic rearm of the one-shot launch allowance.

**Startup/command requirements for the candidate trial.** After a separately
supported at-rest setup, the host may propose one straight launch: target
speed **0.125 m/s**, yaw rate **0 rad/s**, held for **one configured tick**.
These are simulation-only candidate requirements, not hardware limits, normal
defaults or permission to launch. The independently evidenced guard must admit
its actual sweep and braking tail before application. It needs no partial
sector choice or
oracle-selected launch. Startup is a separate host protocol; sector stays
unknown at rest and the normal complete-`OK` rule is unchanged. No blind launch,
automatic relaunch or exclusion of failed startup from outcomes is permitted.

For `NORMAL`, require a deterministic candidate mapper: left/centre/right
request `+max_turn_rate`/zero/`-max_turn_rate`; forward target is
`max_speed * tier / 3`. Blocked, `none`, tier zero or unusable/expired decision
requests braking. There is no additional goal-proportional centre steering.
This map does not promote [the old host controller][baseline-host-source].
The centre-only capacity answer never qualifies its combination with a side
turn: the separate guard must support the complete proposed command or reject.

The required fallback is a repeatedly issued `(0.0, 0.0)` target, not an
instantaneous stop or a proof that braking space is clear. [The simulator's
actual step][admission-dynamics-source] clips target speed, applies the
acceleration-limited speed update, clips yaw rate and then integrates motion
at the updated speed in bounded segments. Every fallback tick repeats that
discrete update. Guard the whole one-command-tick-plus-braking swept body,
including numerical/registration allowances, not just endpoints or the old
continuous braking formula. Existing C1 question tubes do not constitute an
implemented guard for this new piecewise motion. Unknown braking clearance
must be reported; it does not disable independent braking or imply safe recovery.

Require at most one guard attempt per requested application tick, one command
interval plus **16 modeled braking ticks**, and **128 total motion chords**
per attempt. If supported enclosure/stopping cannot be established inside those
caps, deny the request; do not extend them or retry automatically. These are
candidate work limits, not measured feasibility, latency or renewed allowances.
Actual fail-safe braking continues independently of a search cap. Before any
implementation, separately bound and account every derived coverage/witness/
registration query and all rejected entries; a chord cap is not that ledger.
Existing six-question-query controls and every historical fixture budget stay
unchanged. A fresh test increment and affected-regression renewal need approval.

**Acceptance checks before a usable trial.**

- Independently verify S1-S5 and the request/response/executor join. Tampered
  source/frame/capture/config/epoch, expired/duplicate permits and omitted
  evidence must fail closed; an identity match alone must not qualify a source.
- Preserve the old exact-rounding rejection and at-rest partial diagnostics.
  A future non-exact source needs bounded decoded/source discrepancies propagated
  through the actual command, fallback and question evidence, including both
  signs and near-contact cases; no tolerance relaxation or true-flag shortcut.
- Check a denied startup issues only fallback; an admitted launch is one use,
  one tick and independently guarded, with no `OK` forgery or repeated reset.
  Verify centre steering and side/tier counterexamples against actual requests.
- Independently check the acceleration-limited, piecewise command/braking sweep,
  tangency/occlusion/missing returns, timing gaps, uncertainty and cap exhaustion.
  A whole outer tube containing a hit is not a collision witness; an unsupported
  region is not free space. Preserve all old aliases and failure evidence.
- Review exact request/query/regression budgets and real receipt-to-command/
  fallback timing separately before implementation or real-time integration.
  D4 cohort/threshold/resource approval remains separate; always rejecting or
  passing conditional fixtures cannot satisfy baseline task quality.

**Adoption and remaining gates.** Requirements-only adoption covers S1-S5,
the explicit simulation-only guard boundary, one-shot startup/map/fallback and
work caps. It is not evidence that any owner or implementation satisfies them.
Uniform numerical/registration support, concrete guard implementation/work
accounting and representative evaluation remain missing evidence, not completed
gates. No source, runtime, wire, collection, model/dependency, hardware or run
authorization follows; physical host actuation and fail-safes remain independent.


##### Admission Evidence Dependencies (2026-11-06)

This map clarifies the adopted contract; it accepts no new evidence, profile,
allowance, permit or run. Conditional correspondence and actual admission remain
separate. [The dated gap assessment][admission-gap-review] records current status.

| Obligation | Available conditional prerequisite | Missing evidence / owner | Conservative invalidation |
| --- | --- | --- | --- |
| S1 initial setup | Offline complete-scene/config/epoch content checker and isolated exact-rest startup composition. | Independently supported setup-auditor result with accepted domain/epoch/config provenance; declared content is not admission. | Missing setup, reset, scene/config change or unsupported envelope means unknown; no launch. |
| S1 later body | Command/braking path enclosures and current capture/request/path correspondence under fixture assumptions. | Actually admitted predecessor sweep, retained uncertainty and matching actual execution receipts; no pose/hash/true flag supplies this chain. | Predecessor gap or action/time/error mismatch makes later body unknown; independent braking remains. |
| S2 source/coverage | Recorder-owned cadence/latest delivery and synchronized capture-content/path-prefix checks. | Accepted module-side source/retention authority plus independent return/occlusion/missing-return coverage for the sweep; host cannot select the capture. | Mixed/expired/unsupported source or swept region stays unknown; aliases remain controls. |
| S3 state | Actual decoding, original/source-word discrepancies, normal mapping and current-request source recheck. | Accepted event/frame/profile authority and independent evidence that intervals enclose actual state, including fresh ego/goal. | Invalid/stale/nonplanar/mismatched input rejects; retain exact-rounding rejection and no world-truth steering. |
| S4 allowances | Conditional discrete motion, complete-history discrepancies, path-cell margins and isolated straight-pose rounding composition. | Independently supported range/pose/clock/arithmetic/native-motion bounds for named consumers and accumulated predecessor uncertainty. | Unsupported turns, missing bounds, overlap or cap exhaustion abstain; no guessed error or error reset. |
| S5 timing | Frozen request words/frames/profile/context and nominal tick/expiry matching, without permission. | Accepted capture/reference/receipt/application/fallback timing/epoch contract, with external clock/error qualification. | Tick equality is not a deadline; replay, lateness or epoch/config changes invalidate. |
| Guard/executor | Exact request/capture/path content checks, always UNKNOWN/no permission. | Evidence-supported response, serialized one-use check/consume and actual requested/clipped/applied/fallback receipts. | Missing/denied/unknown/fault/expired response means fallback; duplicate/failed application cannot create a predecessor or rearm. |
| Trial/task quality | Synthetic controls and quarantined historical failure evidence. | Admission gates, separately authorized prospective D4 cohort/criteria/resource scope and independent task evidence. | Always rejecting does not admit a trial, dataset/split or baseline-quality claim. |

The dependency is supported setup and source/error/timing evidence, then a
supported sweep, then one-use execution/receipts, then later-body continuity.
It is not setup-hash to permit or matched pose to body truth. Do not substitute
metadata helpers for missing acceptance evidence. A local ownership prerequisite
may remove caller-selected capture/context without closing S1-S5 or authorizing
execution; all qualification and rejection boundaries remain.


##### Owned Latest-Event Request Content (2026-11-06)

The private `_SyntheticC1SourceRecorder.prepare_normal_request` derives context
from its current State/frame and latest delivered C1 event. The host-facing
inputs to this fixture method are decision bytes, request ID and explicit
fixture error evidence, not capture/epoch/reference selection. It checks source
file correspondence, delivery/epoch/synchronized ticks, freezes event content,
reuses existing normal request/capture checks and rechecks the event before
publication. No new source abstraction or normal controller wiring is added.

Returned request content is owned; raw capture, private scene and reference pose
are not exposed. Every result retains UNKNOWN/no permission and seven false
qualification flags. Actual source/coverage/error/clock/predecessor/executor
acceptance remains missing. Existing declared-context preparation and recorder
event production are unchanged. This method does not consume a permit, advance
the simulator, ensure request-ID uniqueness or establish physical timing.

See [the bounded implementation evidence][owned-event-request-review]. Current-
owner rechecking after advancement is implemented by the private
`recheck_normal_request` method. It takes retained/received request content and
explicit fixture error evidence, never a caller-selected current tick or context.
It matches at the actual owned tick, internally prepares from current owned
State/frame/latest capture, and rechecks source files, event and request content
before publication. Old nominal application ticks expire even when old request
hashes still match. No raw capture, prepared request, permission or execution is
published by rechecking; UNKNOWN and all seven false flags remain.

[The bounded recheck evidence][owned-current-recheck-review] includes actual
recorder advancement and mutations during preparation/final matching. Nominal
expiry remains distinct from qualified clock deadlines or one-use execution.
Owned event preparation now also checks the exact four-field event schema,
canonical epoch/capture ID, supported acquisition cadence and delivery at capture
tick plus the recorder's configured latency. A future capture or inconsistent
event rejects before low-level request preparation. This verifies consistency
with the actual recorder policy, not source authority or external clocks.
[Delivery-integrity evidence][owned-delivery-review] retains the failed controls
and unchanged valid-event output.

The next admission step is independently supported source/coverage and named
S4 numerical/registration/timing evidence, not additional request hashes. Current
conditional tooling supplies no accepted source-admission record, admitted
predecessor sweep or executor receipt. Evidence acceptance and any new
qualification study remain protected; synthetic tests cannot replace them.


##### Source and Consumer Qualification Packet (2026-11-06)

**Prepared candidate, not evidence acceptance or a run approval.** This packet
advances the remaining dependencies after owned request/currentness/delivery
rejection. It names the actual producers and consumers; no new source profile,
allowance, request/response schema, permit, numerical verdict or study scope is
adopted. [The dated packet review][qualification-packet-review] records the
verified code anchors, independent-method gaps and remaining protected actions.
The [actual dynamics/source producer][qualification-dynamics] and
[conditional guard consumers][qualification-consumers] are the code of record.

Retain the adopted candidate values and limits: stored-word dt/acceleration/
speed/yaw/body profile, source/decoded discrepancy, one command tick followed
by at most 16 braking ticks/128 chords, existing retention and whole-body contact
semantics. Do not narrow normal commands to zero yaw just to reuse the isolated
straight-history checker; unsupported past motion remains unknown. The accepted
0.6 m/s binary32 rejection remains until a separately qualified source path
supports and propagates its discrepancy. No tolerance or hard-cap change follows.

| Packet row / named producer | Named consumer / evidence needed | Independent acceptance and failure rule |
| --- | --- | --- |
| Q0 source and setup: offline setup auditor, `_SyntheticC1SourceRecorder.record_tick`, actual host state owner | Request preparation/current recheck plus S1 body and S2 swept-region coverage. Bind supported setup, immutable config/epoch, actual source events, all eight view payloads/masks and retained capture/reference lineage. | Supply independently supported setup/source/return/coverage provenance. Self-consistent metadata is not authority; missing/occluded/unsupported sweep or predecessor means unknown. Current recorder accepts supplied fixture poses/States and is not by itself the actual dynamics owner. |
| Q1 decoded state: `state_from_observation`, State encoder/decoder and exact source-word binder | `_probe_synthetic_c1_state_motion`, history registration and mapped-command sweep. Preserve actual source and decoded speed/yaw/goal values, signed discrepancies, validity and ego/goal ages. | Enclose source-to-decoded error and propagate every affected component. Matching decoded bytes or sampled parity does not qualify actual source state; no clamp or guessed epsilon. |
| Q2 native update and trajectory: `RoverEnv.step` and `integrate` | `_probe_synthetic_c1_discrete_motion` and actual-command path/cell guard. Bound clipping/subtraction/acceleration update before integration, yaw clipping, segment selection/duration, native `sinc`/sin/cos, vector position update and stored-yaw wrapping. | Independent uniform computed-program error evidence plus domain closure for the full command/braking sweep, not only endpoint equality. The ideal rational motion enclosure is a separate reference, not native-error evidence; unsupported operation/path or work bound rejects. Preserve source-scale and accumulated predecessor errors. |
| Q3 capture/reference transformation: C1 acquisition, complete bound State/frame history | `_bound_synthetic_c1_history_registration`, `_check_synthetic_c1_straight_capture_reference_pose` and `_probe_synthetic_c1_owned_capture_request_path`. Separate range/pose/time/source errors from outward reference-rounding and remaining point margin. | Independent pose/range/clock/transform enclosures cover every retained ray prefix and point, including heading lever arms and native transforms. Each contribution is counted once; no zero source error, age-times-current-twist replacement or reset at re-planning. |
| Q4 timing and realized receipt: source/reference owner, future guard and host executor | S5 expiry, one-use response consumption and S1 admitted-predecessor continuity. Require submitted command, clipping result, each actually traversed integration interval, interrupted/collision segment, application/fallback times and error lineage. | Independently qualify clock/receipt/application correspondence, serialized consume and failure gaps. `RoverEnv.step` publishes final `applied_action` after collision may zero velocity; that field alone is not a full realized-motion receipt. No admitted chain from final speed, old tick or request hash. |
| Q5 task-quality release | Complete supported source/guard/executor path, then prospective D4 evaluation against its independent task references and accepted criteria/cohort. | Admission evidence first; separately authorized run/resource/lineage scope next. Always rejecting, unit fixtures, old quarantined logs or token/model fit do not qualify a baseline. |

The packet for each row must contain the exact claim/domain/producer revision,
consumer and propagation rule; independent reference/proof or measurement method;
versioned result and evidence limits; invalidation triggers; and its explicit
acceptance decision. Missing a field leaves that row unsupported. These are
review contents, not a newly implemented record parser or an acceptance token.

Recommended order: supported offline setup and actual source/return authority,
Q1 discrepancies with Q2/Q3 uniform allowances and Q4 clock contract, then an
evidence-supported guard and serialized one-use executor/receipts, then later-body
continuity and Q5 trial. Prepare available evidence independently, but do not
invent uniform bounds, accept undecided certificates, restore models, run a
new qualification study, integrate hardware or launch D4 under routine unit-test
authority. General audits/SC18 and learned work stay deferred. Host fail-safes
remain independent; no actual command execution is authorized by this packet.


##### Opt-In Simulator Realized-Motion Receipts (2026-11-09)

The existing RoverEnv.step accepts a literal capture_motion_receipt boolean,
default false. Only opt-in calls add motion_receipt to info. The owning step
records submitted targets, initial state/config, clipping and acceleration-update
results, nominal dt/segment duration, each attempted start/candidate endpoint and
whether it was committed, plus final state and committed/planned counts. A
collision candidate is recorded as rejected, never as traversed; final zero
speed does not erase earlier committed intervals. Normal physics, outputs and
sensor/odometry RNG state are preserved by bounded paired controls.

Opt-in work is limited to 128 attempted segments, checked before state mutation;
ordinary stepping acquires no new work limit. Nonliteral opt-in, excessive work
or overflowing angle arithmetic rejects without a partial receipt. Payloads
contain owned builtin values and an independent config dictionary; no live
environment/array reference is exposed. All seven qualification/admission/
training flags and fixture_permission_granted remain false.

This supplies Q4 diagnostic content, not qualified clocks, request/application
identity, fallback scheduling, serialized one-use consumption, uniform native
motion error or admitted-predecessor uncertainty lineage. No normal controller,
wire interface, actual-command guard, hardware or task-quality run is wired or
admitted. The [dated receipt checkpoint][realized-receipt-review] retains the
bounded controls, initial missing-keyword failures and required gate results.


##### Owned Simulator Source Reads (2026-11-09)

The existing private C1 recorder optionally reads one exact RoverEnv through
record_environment_tick, requiring literal synthetic_test_only=True. It derives
tick, pose, observation, State and frame internally; callers supply none of those
values. The declared ideal C1 config/scenario must match exactly. The first
successful read binds the actual environment and both RNG objects; foreign owners,
reset/replaced epochs, stale ticks, mixed fixture/simulator recording, source-file
changes or producer/recorder mutation during capture reject before publication.
Capture work is staged on a shallow recorder copy; existing record_tick capture/
delivery/retention semantics remain, but bound streams reject fixture overrides.

An owned dynamics sample retains the original native speed/yaw separately from
the State derived by state_from_observation. That existing exporter has already
converted ego/goal to float32; its values are not recovered native precision or
qualified Q1 source-to-decoded bounds. The next motion-word integration must
preserve that distinction and actual emitted bytes rather than erase rounding
discrepancies. Owned observation mutation does not change the environment.

This is conditional producer/content correspondence, not accepted source/coverage
authority, uniform native/range/pose/clock error, body support, one-use execution
or admitted predecessor lineage. Source reads do not step/reset, query decisions/
guards or write episodes. Existing normal APIs/physics/wire and all qualification
flags stay unchanged. The [owner-read checkpoint][simulator-source-read-review]
records finite synthetic controls, reset-lineage repair and actual gate results.


##### Native Motion Source Words (2026-11-09)

The recorder's actual-owner path now encodes the existing observation State first,
then derives source speed/yaw from the same original native dynamics snapshot.
Their encoding must equal that emitted frame before capture and publication.
Contradictory native/ego words reject without staged events; legacy fixture paths,
normal outputs, source/decoded tolerances and all qualification flags are unchanged.
The existing exact interval binder and motion bridge retain nonzero rounding
discrepancies instead of collapsing both endpoints to the post-float32 word.

Signed zero survives source and wire words. Binary32 0.6 overshoot still exceeds
the motion domain and rejects before motion entries; no clamp or new allowance.
Source goal components remain post-observation, not recovered native goal values.
Original native motion values are not uniform native arithmetic/pose/range/clock
error, source authority, usable permission or admitted predecessor evidence.
The [motion-word checkpoint][native-motion-source-review] records independently
computed Fraction references, bounded inconsistent-ego controls and actual gates.


##### Native Goal Producer Words (2026-11-09)

The rover's existing history producer now retains its already-computed native
goal projection tuple, source tick, position and yaw before discarding precision
in the unchanged float32 observation conversion. No arithmetic order, odometry
draw, delivered history/observation, frame format or motion formula changes.
The actual-owner C1 path copies that private source record, requires exact current
tick/pose words, derives original goal components and preserves actual emitted
bytes. Missing/stale/wrong-pose/inconsistent source rejects before capture; the
existing consecutive/nonwrapping tick preflight remains first.

The exact word binder retains original/decoded goal intervals and signed
discrepancies. This supersedes the earlier post-observation-goal limitation, not
Q2/Q3 numerical/physical error requirements. Retained goal words include original
native projection error; they are not certified world/goal semantics, accepted
pose/range/clock bounds or source authority. Nonideal/delayed C1 profiles remain
unsupported. All qualification/admission flags stay false and no one-use/body/
predecessor permission follows. The [goal-word checkpoint][native-goal-source-review]
retains independent rational controls, failure-order repair and required gate.


##### Diagnostic Receipt Clock Windows (2026-11-09)

The existing opt-in simulator receipt makes at most two standard-library
`time.monotonic_ns()` reads around state transition and observation construction.
Default stepping and receipt preflight rejection make no diagnostic clock reads.
The receipt's `clock` field names the Python monotonic domain and window scope;
its integer begin/end/duration counters are separate from nominal simulator
dt/ticks, State timestamps, UTC, device clocks and executor deadlines. The
reference epoch is unspecified; signed references are not rejected for their
sign. An ordered pair is `observed`, not qualified; OS read errors and
noninteger values are unavailable and backward pairs remain `unknown` with no
elapsed value. Clock faults do not change normal physics, RNG or motion outputs.

This window excludes action validation, receipt preflight/preparation and final
receipt publication/return. It is not complete API latency, effective accuracy,
clock correspondence, a deadline/expiry bound, one-use execution or admission
evidence. `clock.qualified` and all existing admission/qualification flags remain
false. No timing study or clock configuration change follows. The [clock
checkpoint][receipt-clock-review] records the bounded controls and primary source.


##### Producer-Owned Receipt Retention (2026-11-09)

The opt-in simulator retains one private deep copy of its completed receipt
alongside its actual RNG/odometry RNG object references. Returned segment,
configuration and clock dictionaries are separate caller-owned diagnostics.
Reset clears retained data; the next preflight-approved transition clears it
before motion, including when receipt capture is disabled. Preflight rejection
does not invalidate the still-current receipt. Deepcopy of the entire simulator
preserves its internal epoch-reference correspondence, not identity with the
original simulator. Replacing a generator by an equal-state copy is a different
epoch reference, not continued execution identity.

Unexpected failures after transition begins do not roll back motion and cannot
make a previous receipt current. Retention is neither atomic publication nor
adversarial tamper protection, source acceptance, native execution or one-use
permission. One capped receipt is not a measured RAM/stack bound. Actual source
tick/pose/profile linkage still needs its own opt-in consumer. The [retention
checkpoint][receipt-retention-review] records lifecycle and nested ownership
controls; all admission/qualification flags stay false.


##### Opt-In Receipt and Source-Pose Linkage (2026-11-09)

Actual simulator source reading has a literal-false-by-default
`capture_motion_receipt_source` option. When enabled it requires retained
producer RNG/odometry epoch identity and at most 128 receipt segments before
copying; previous/current consecutive ticks, config and exact native initial/
final pose/action words must correspond to the owned source samples. Required
receipt permission/qualification flags and clock qualification remain false.
Staged source capture is followed by snapshot/content and retained-object
identity rechecks before publication. Missing, stale, mismatched, over-budget or
changed data rejects without publishing the staged current/pending source.

Only opted-in snapshots add `motion_receipt` and `receipt_source_epoch`; normal
source State/frame/capture behavior is unchanged. This recorder epoch is not the
unspecified monotonic clock reference. Copy ownership and correspondence are not
atomic publication, adversarial source attestation, numerical/clock bounds,
segment-chain validation, one-use execution or predecessor admission. Consumers
must still independently check the claimed realized segment chain, nominal
duration and evidence before using it; no usable command follows. The [linkage
checkpoint][receipt-source-pose-review] retains failures, controls and limits.


##### Receipt Segment-Chain Consistency (2026-11-09)

Opt-in actual-source receipt ingestion checks the closed receipt root and
segment shapes before copying. Planned/attempted segments remain bounded by the
existing 128 cap; indices and commit flags have exact builtin types. Initial,
successive and final native pose words must form the claimed realized chain.
Completed receipts require all planned segments committed; incomplete receipts
must end in exactly one rejected candidate after any committed prefix. Rejected
candidate endpoints do not become traveled positions. Final action matches the
recorded updated speed/turn for completion or the recorded collision stop.

Nominal duration matches configured dt and the recorded per-segment stored-word
division; neither is elapsed physical time. Recorded swept radius must support
the configured body scalar, not prove sagitta, whole-body clearance or a native
error allowance. The checker neither replays integration nor supplies a permit/
qualified report; actual source epoch/tick/pose binding remains separately
required. All flags remain false. The [chain checkpoint][receipt-chain-review]
records independent structural copy controls, unchanged multi-segment/collision
producer controls, failures and gates, not source/numerical/clock acceptance.


##### Bounded Source-Linked Receipt History (2026-11-09)

The actual-source recorder retains at most eight consecutive opted-in transition
entries. Each owns copied receipt content, original initial/final State words,
the emitted initial/final frames and recorder source epoch. A new entry must
anchor to the recorder's current original State/frame/epoch; the oldest entry
is trimmed at the existing eight-tick history cap. A default source read clears
the receipt window instead of bridging an unrecorded transition. Producer and
latest source-snapshot receipt dictionaries are not aliases of history entries.

History joins the pre/post capture owner binding and is published only with
successful staged source publication. Rejection preserves the existing window,
including externally introduced changes rather than undoing caller mutations.
This is not atomic/adversarial ownership, a setup/body-clear origin, native or
clock qualification, an uncertainty reset, one-use execution or an admitted
predecessor chain. Consumers still need full history and actual-current-source
validation before using retention; trimming does not erase accumulated error
obligations. All qualification/admission flags remain false. The [history
checkpoint][receipt-history-review] records finite retention/gap/copy controls
and preserved style failure, not board/RAM/latency/task-quality evidence.


##### Full Retained History Pairings (2026-11-09)

Opt-in receipt ingestion validates every entry in the old bounded history before
append, then validates the planned window against the newly sampled current
source before staged capture. Each entry requires its matching recorder epoch,
closed original State/frame/tick data, native action correspondence, coherent
receipt chain and literal-false permission/qualification metadata. Consecutive
entries must match original States, frames, ticks and native pose words. The
last entry must match the owning current source's original State/frame/pose/tick;
all receipt configs must match the current declared profile. Existing actual
source/owner post-capture checks still precede publication.

This closes contradictory-old-entry retention, not source attestation: mutually
consistent fabricated records may still match. Reencoding original words binds
emitted frames, not native numerical or physical correctness. The checker does
not validate every clock primitive, accept clock bounds, reset uncertainty,
admit predecessors or issue permission. A later offline reader must recheck
actual producer currentness at read time; ingestion checks are not perpetual
freshness. The [pairing checkpoint][receipt-pairing-review] records bounded
controls and remaining gates; all qualification/admission flags stay false.


##### Read-Time Producer History Snapshots (2026-11-09)

The private source recorder's opt-in `snapshot_receipt_history` reads only its
bound simulator. It accepts no caller current tick/environment/receipt override.
Epoch object identity, current tick and source files must remain unchanged;
fresh native pose/action/goal-source/observation/config/scenario/receipt content
must match the retained source sample. The complete bounded history is checked,
copied, then producer/owner content, object identities and source files are
rechecked before returning `snapshot_available=True`. Stale, missing, unsupported
or changed data yields unknown without history/current-frame publication.

Snapshots are read-only owned diagnostic copies: no step/reset/C1 capture/guard
query or RNG change. The result names an offline source-history use and leaves
all admission/qualification flags false. Availability is not a usable command,
clock/one-use qualification, body-clear origin, native numerical evidence,
admitted predecessor or perpetual freshness. Two-point checks do not guarantee
atomicity against concurrent/adversarial mutation; consumers need their own
currentness/qualification dependencies. The [snapshot checkpoint][receipt-snapshot-review]
records bounded stale/content/mutation controls and remaining source gates.


##### Retained Native Integration Intermediates (2026-11-09)

The simulator integration core accepts an optional empty builtin source
dictionary. It retains copied actual primitive inputs, angle/midpoint, normalized
sinc argument/value, speed-interval product/distance, cos/sin/displacement and
wrapped-heading intermediates from the existing operation order. The default
two-value return and arithmetic output words remain unchanged. These are native
computed values, not independently certified mathematical values or error bounds.

Receipt-enabled transitions retain one separate private integration-source list
with original RNG/odometry-RNG epoch references and transition ticks. Each actual
attempt contributes its own computed source, including a rejected collision
candidate, under the existing 128-attempt cap. Default transitions and reset clear
the cache; rejected preflight leaves the still-current cache unchanged. No receipt
or wire schema changes, extra RNG/clock reads or reported actuation follow.

Producer retention alone does not populate source-recorder, retained-history or
offline snapshot data. Those consumers need actual-producer linkage, content
validation and currentness checks before using it. Retention supplies no native
roundoff, clock, physical, source or command qualification; all existing admission
flags stay false. The [integration-source checkpoint][integration-source-review]
records fixed output-word/primitive-source/ownership compatibility controls,
not numerical proof, board execution, fit, latency or task quality.


##### Actual-Source Integration Ingestion (2026-11-09)

The private source recorder's literal `capture_native_integration_source` option
requires its receipt-source opt-in. It reads the actual producer cache, verifies
RNG epoch references, transition ticks, closed finite builtin native words and
one computed source per actual receipt attempt under the existing 128 cap.
Input pose/action/interval and candidate endpoint words must match the receipt,
including rejected candidates. No integration or primitive arithmetic is replayed.

The temporary source snapshot includes copied integration data in its pre/post
capture binding. Retained cache identity and recorder-owned prior integration
sample also join stability checks before publication. Success stores a separate
owned `_integration_sample`; reads without the option clear it. Existing source,
receipt-history and offline receipt-snapshot schemas remain unchanged. A failed
read does not publish a new sample or undo external mutations.

This is source correspondence, not primitive correctness, native error proof,
adversarial attestation, one-use execution, clock qualification or permission.
Read-time native-source currentness remains a distinct dependency before an
offline numerical consumer can use the copied sample. The
[ingestion checkpoint][integration-ingestion-review] records bounded default/copy/fault/mutation
controls; all qualification/admission flags stay false.


##### Read-Time Native Integration Snapshots (2026-11-09)

The private recorder's strict opt-in `snapshot_native_integration_source` reads
only its bound producer and takes no caller tick/epoch/environment override.
It reuses actual receipt-history currentness and compares fresh native cache
content to the retained integration sample. Each of its two native samples also
reads actual pose/action/goal-source/observation/profile/receipt words. Producer
and cache identities, RNG references and compound owner/source/history bindings
are rechecked before owned native source/current-frame publication.

Missing, stale, unsupported or changed data returns unknown without native
source/current-frame data. No step/reset/capture/integration replay/guard query
or RNG change follows. The diagnostic result leaves all qualification/admission
flags false; availability is not permission, native numerical proof, clock or
one-use qualification, body-clear origin or an admitted predecessor. Two-point
checks are not perpetual freshness or concurrent/adversarial atomicity.
The [native snapshot checkpoint][native-integration-snapshot-review] records
bounded source/owner/history/currentness controls and the final-read repair.


##### Supported Native-Word Arithmetic Discrepancies (2026-11-09)

The private arithmetic probe consumes copied diagnostic native-source words,
not actual-current-source authority. It reuses bounded rational value/binary
operations at at most the existing 4,096-bit source cap. Ten retained stages are
supported: angle and speed-interval products, half-angle division, midpoint
addition, distance product, both displacement products, both position additions
and heading-increment addition. Operand/output hex words retain signed zero;
exact results, observed dyadics and observed-minus-exact dyadics are recorded.

Closed finite native words and at most 128 segments bound ten stages and two
rational binary operations per stage. A copied working source and before/after
input binding detect changed input; unsupported or exhausted work returns
unknown without partial stage publication. No integrate, capture, guard, source
read or physical operation follows. The supplied words may be synthetic or
fabricated; their exact rational relationships do not establish provenance.

Sinc argument/value, cos/sin, pi-constant, heading wrapping and accumulated-motion
obligations remain explicitly unsupported. Local discrepancies are not uniform
native bounds, propagated uncertainty or numerical/source/command qualification.
Consumers still require actual source/currentness and their separate acceptance
dependencies; all qualification/admission flags remain false. The
[arithmetic checkpoint][native-arithmetic-review] records fixed direct Fraction
references, source-field binding, signed-zero/subnormal and work/mutation controls.


##### Current Owned Native Arithmetic Composition (2026-11-09)

The private recorder's strict opt-in `snapshot_native_integration_arithmetic`
accepts no caller source/tick/epoch override. Owned current-native snapshots
bracket one supported arithmetic probe. Its source digest and literal-false
metadata must match; current source/frame/epoch/tick data, producer identity and
compound recorder/source/history content are rechecked before copied publication.
An intervening contradictory source, owner or receipt prevents publication.

Missing, stale, unsupported or exhausted evidence returns unknown without partial
source/frame/arithmetic records. Default source/history/wire APIs are unchanged.
No step/reset/capture/integration replay/guard query or actuation follows. The
result reports only observed local arithmetic discrepancies; source acceptance,
uniform/propagated error, transcendental correctness, clocks, one-use execution
and command admission remain separate. All qualification/admission flags stay
false; matching hashes are not mathematical proof or adversarial attestation.
Consumers still need exact record/source-word validation before relying on those
records. The [composition checkpoint][native-arithmetic-composition-review]
records bounded mutation/binding controls, reboot recovery and the actual gate.


##### Exact Native Arithmetic Record Validation (2026-11-09)

The current-native arithmetic reader checks supported records before publication.
Closed literal-false metadata, exact segment/stage counts and order, source-bound
operand/output hex words, canonical rational pairs and exact observed/exact/
difference relationships must match. Producer and consumer share only the ten
stage extraction definitions; direct source-field/Fraction tests remain separate.
The consumer uses bounded direct rational operations rather than replaying the
producer, and preflights supplied integer/canonical limits before record hashing.

Malformed, inconsistent or exhausted records prevent copied publication. No
existing producer operation/query caps, source/wire APIs or admission flags change.
This establishes only supported local record consistency, not independent source
truth, transcendental or accumulated-motion correctness, uniform uncertainty,
clock/one-use qualification or permission. The
[record checkpoint][native-arithmetic-record-review] preserves bounded rational,
source-word, malformed-pair, preflight-order and compatibility controls.


##### Diagnostic Receipt Clock Consistency (2026-11-09)

Receipt-chain intake checks the closed diagnostic clock domain, scope, primitive
types, status and duration. Exact builtin integer counters with nondecreasing
endpoints require observed status and the exact integer difference; missing or
backward counters require unknown status and no duration. Signed epochs and
equal endpoints remain supported. Existing bounded integer pre-operation work
guards apply; no clock is read by this check, and `qualified` must remain false.

These are retained metadata consistency conditions, not accuracy, resolution,
reference, clock-epoch attestation, wall-time, expiry or one-use guarantees.
Unknown clocks are retained as unknown, not upgraded to observed. The source,
history, native and wire APIs remain unchanged; all admission flags stay false.
Adjacent observed windows still need ordering checks before any offline timing
consumer relies on a retained sequence. The
[clock consistency checkpoint][receipt-clock-consistency-review] records finite
primitive/counter/status/duration controls and remaining S5 dependencies.


##### Adjacent Retained Clock Window Ordering (2026-11-09)

The bounded receipt-history pairing loop rejects an observed window starting
before the immediately preceding observed window ends. Touching and equal
windows, signed epochs and arbitrary coherent gaps remain supported. A missing
or backward unknown window prevents comparison across that gap; later adjacent
observed windows are still checked. No clock is read or uncertainty reset inferred.

This checks retained diagnostic ordering only, not shared physical clock
reference/epoch, accuracy, wall-time, expiry, one-use execution, admission or
an independently supported setup origin. Unknown gaps stay unknown; all flags
remain false, and the source/history/native/wire APIs are unchanged. The
[window checkpoint][receipt-clock-order-review] records bounded copied-history
controls and the remaining source/timing qualification obligations.


##### Native ToF Computation Prerequisites (2026-11-09)

The synthetic `tof_ranges` core accepts an optional empty builtin source
dictionary. It copies the actual native pose, Config and Scenario, computed
world-frame rays, initial floor candidates and final pre-noise native ranges.
Default arithmetic/return values remain unchanged; noise, dropout, clipping,
float32 projection, acquisition cadence, pending delivery and wire fields stay
outside this capture. Legacy planar geometry records no 3D rays or floor
candidates. Native infinities remain missing candidates, not finite enclosures.

Opt-in work is limited to 32 obstacle entries and fixed 8x8 grids; this is a
diagnostic retention limit, not an accepted physical-domain or error bound.
Returned arrays and input dataclasses are detached copies. The record permits
`native_tof_diagnostics_only`; all permission/qualification flags remain false.
Wall/cylinder intermediate proof, selected-hit correctness, range-error bounds,
actual sampling/epoch linkage, source acceptance and command admission remain
separate obligations. Matching copied/fabricated inputs is not source authority.
The [native ToF checkpoint][native-tof-source-review] records finite native-word,
detached-copy, geometry, preflight, cadence and RNG controls.


##### Actual Native ToF Acquisition Cache (2026-11-09)

`RoverEnv.step(capture_native_tof_source=True)` separately opts into the actual
acquisition reached during that transition. Shared finite-pose/32-obstacle
preflight runs before mutation and receipt clock reads. `_sample` supplies its
actual native source dictionary to the ToF core and retains it with the exact
post-noise/dropout/clip float32 sample and validity mask, acquisition tick,
nominal pending delivery tick and original RNG references. The matrix and mask
are detached from pending delivery. No extra geometry replay, RNG draw, source
read or ToF clock read is used; ordinary output and cadence remain unchanged.

Default stepping, reset and opted-in held-acquisition ticks leave no fresh cache;
preflight rejection preserves earlier diagnostic retention. One cache covers
the current fresh acquisition only, not complete scan history. Its acquisition
tick may differ from the delivered sensor tick; pending/delivered-State lineage,
recorder ownership, epochs, timing, range/native error, coverage and source
qualification still require their independent evidence. All inner permission/
qualification flags remain false; this permits no command or admitted chain.
The [sampling checkpoint][native-tof-sampling-review] retains finite acquisition,
output/RNG, held/default/reset, preflight and detached-copy controls.


##### Bounded Fresh Native ToF Intake (2026-11-09)

The adjacent private native-source intake validates the closed fresh ToF cache,
literal-false metadata, original RNG references, exact current native pose and
configuration/scenario, fixed array shapes/dtypes and a unique matching pending
acquisition. It copies native binary64 values to hex-word tuples, sampled binary32
values to uint32 words and masks to boolean tuples; positive infinity remains an
explicit native candidate, not a finite enclosure. No geometry/sample replay,
source read, step/reset, RNG draw or clock is used during intake.

Preflight retains the existing 32-character owner epoch and nonwrapping C1 tick
range; offline latency/pending work is limited to eight entries. Native grids
remain 8x8, directions have three components and obstacles stay capped at32.
These are local diagnostic retention limits, not accepted physical/timing/error
bounds. Missing, already-delivered, nonfresh or mismatched pending evidence rejects.
This single-point copied-content check is not perpetual freshness, enforced
atomicity, source authority, scan/history coverage, selected-hit proof, numerical
qualification or command admission. Recorder opt-in/staging remains separate;
all flags stay false. The [intake checkpoint][native-tof-intake-review] records
bounded copies and mismatch controls without qualifying an acquisition source.


##### Recorder-Owned Fresh Native ToF Retention (2026-11-09)

The bound recorder's separate `record_native_tof_source` operation requires a
literal synthetic opt-in and an already-current original producer/read. It
brackets two bounded intake copies with current producer-content, recorder,
cache/RNG identity and source-file checks; the first returned copy must still
match its original fingerprint before publication. Retention updates only the
private `_tof_sample`, not the current tick, emitted frame or dynamics schema.
Ordinary reads clear that private cache. No geometry replay, step/reset, RNG draw
or clock occurs in this ToF-only operation.

Ordinary `record_environment_tick` remains distinct: its existing staged
`record_tick` may regenerate bounded synthetic C1 views. Those setup/default
views are not the fresh acquisition's native source, delivered-State lineage
or scan coverage. The first failed control exposed this distinction; the
[retention checkpoint][native-tof-retention-review] preserves the failure,
separate-operation repair, copied-result mutation control and finite gates.

Two-point content and identity checks are not perpetual freshness, enforced
atomicity, live-callee/source authority, shared clock/epoch support, one-use
execution, selected-hit correctness, range/native/physical bounds, permission
or admission. Acquisition tick may differ from delivered sensor tick; all flags
remain false. Read-time current-source publication remains separate work.


##### Current Native ToF Source Snapshot (2026-11-09)

The recorder's separate literal-opt-in `snapshot_native_tof_source` copies
retained fresh acquisition words only while two bounded current live intakes
and original producer/recorder/cache/RNG/file/tick/content checks agree. Exact
typed template comparison checks bounded word tuples, metadata keys, native
float hex (including signed zero) and primitive types before hashing retained
data. Oversized words and bool/int aliases reject without hashing a malformed
retained record. The first outgoing copy is checked again before publication.

Unknown omits source and frame. A successful diagnostic includes a detached
source and the original current recorder frame without stepping, reading,
retaining, replaying geometry, drawing RNG or reading clocks. Acquisition tick
can differ from delivered sensor tick; the frame is a current context anchor,
not a claimed source frame for the fresh acquisition. All permission and
qualification flags remain false. Two-point checks are not perpetual freshness,
enforced atomicity, scan/history coverage, selected-hit/range/native/physical
proof, source authority, one-use execution or admission. The
[snapshot checkpoint][native-tof-snapshot-review] records copied-word, prehash,
stale/epoch/cache and late-copy/pose mutation controls and remaining obligations.


##### Bounded Native ToF Acquisition History (2026-11-09)

Explicit fresh-source retention now archives up to eight detached acquisition
records. Native source word layout/work, epoch, profile, false flags and strictly
increasing acquisition ticks are checked before copy/hash. An identical repeated
tick is idempotent; changed repeated words reject. Ordinary reads clear the fresh
cache but preserve the archive. Oldest entries trim only after a fresh append,
not on a held frame or as a source/uncertainty reset. No default capture is added.

The staged archive and copied current source share a closing fingerprint after
the second intake; original and staged histories are layout-preflighted again
before closing hashes/publication. Recorder ownership remains fingerprinted
before first intake, preserving existing mutation rejection. Native word shape
checks bound historical layout only; exact typed matching remains default for
current source equality. The [history checkpoint][native-tof-history-review]
retains the failed ownership regression, repairs and fixed synthetic controls.

Archive presence, order, trimming or duplicate consistency do not qualify scan/
retention coverage, range/native/physical bounds, actual acquisition/delivery/
State correspondence, clocks, one-use execution, source authority or permission.
All flags remain false/no command. A delivered-source consumer still needs its
own complete correspondence and current-source checks; preserved words alone
are not an admitted chain or accepted evidence domain.


##### Retained Native ToF Delivered-Array Correspondence (2026-11-09)

A separate bounded template validates archive layout independently of a fresh
cache or the archive's own untrusted structure. It names fixed native-word/sample/
mask lengths, original epoch/profile/false metadata, ordered acquisitions and
canonical native binary64 hex words. Positive infinity is retained only as a
native range candidate; sampled binary32 words are exact uint32 values. No
geometry/sample reconstruction, clock/RNG/read/retention/step/reset is used.

The adjacent matcher requires a unique retained acquisition at the actual
`sensor_tick`, a reached nominal delivery tick, and exact current delivered ToF
matrix/mask correspondence. A held observation matches the same acquisition,
not another capture. It returns a detached copy or rejects missing/malformed/
changed source content. The [delivery checkpoint][native-tof-delivery-review]
records bounded copied-word/epoch/hex/layout/matrix/mask/held controls.

This checks local native acquisition-to-array correspondence only. It does not
yet establish recorder-currentness/read-time publication, original State/frame
mapping, complete scan/retention coverage, shared clock/epoch/error support,
selected-hit or native/range/physical proof, source authority, one-use execution,
permission or admission. All flags remain false/no usable command; nominal ticks
and consistent words are not accepted source or deadline qualification.


##### Current-Recorder Native ToF Delivery Snapshot (2026-11-09)

The separate private `snapshot_native_tof_delivery(synthetic_test_only=True)`
uses retained acquisitions even after default reads clear the fresh cache. It
preflights the bounded archive before hashing, fingerprints current ownership
before matching, compares the live producer with its original recorder read,
then repeats delivered-word matching and rechecks archive, outgoing copy,
producer/recorder content, original object/RNG identities and source files.

Success supplies a detached acquisition, its delivered `sensor_tick`, current
recorder tick and frame context. A held observation keeps its acquisition ID;
unknown omits source/frame and grants no authority. It does not read/retain/
replay/step/reset, draw RNG values or sample clocks. The [snapshot checkpoint]
[native-tof-delivery-snapshot-review] records finite controls and failed-check
history. All source/numerical/physical/coverage/clock/one-use/permission/admission
flags remain false. This is bounded two-point currentness, not atomic publication,
perpetual freshness or proof of original State/frame mapping. Acquisition/frame
mapping and complete coverage/error/clock qualification remain separate.


##### Native ToF Companion Original-State/Frame Correspondence (2026-11-09)

Delivered ToF belongs to the actual companion observation, not the planar State
wire payload. The private delivery snapshot now checks both original-State/frame
points using the recorder's existing conversion path: project actual observation
ego/goal into State, retain actual native action/goal overrides as the recorder
does, require exact original native State fields, and require both original and
projected encodings to equal the retained original frame. It does not replace
original State/frame or regenerate ToF geometry, draw RNG values or sample clocks.

The [companion-frame checkpoint][native-tof-companion-frame-review] records native
values differing despite identical binary32 wire encoding, changed State fields,
changed valid/CRC frames and late conversion/context controls. Passing this local
mapping check is not acceptance of ToF source/coverage/error/clock/epoch support,
an acquisition-to-every-historic-frame proof, atomic publication, numerical or
physical qualification, one-use execution, permission or admission. All flags
remain false/no usable command. Fresh and held delivery keep the same actual
acquisition identity; native versus projected equality is checked, not assumed.


##### Retained Native ToF Pending-Queue Correspondence (2026-11-09)

A separate private pending-source matcher shares bounded archive-word validation
with delivered-source matching. It checks the actual deque of at most eight
pending samples, ordered unique acquisition IDs, unreached nominal delivery
metadata and exact binary32 sampled words/bool masks against retained native
sources. Every pending entry needs a retained source, and every retained entry
still nominally due must be present in the queue. Missing correspondence in
either direction rejects rather than being rescued by a delivered-source match.

It returns detached entries in queue order, without read/retain/replay/step/reset,
clock sampling or RNG draws. The [pending checkpoint][native-tof-pending-review]
records bounded single/multiple/empty/missing/malformed/word/mask controls. Empty
archive/queue is empty local correspondence only. This helper does not publish
current-recorder evidence, prove complete acquisition/scan/history coverage,
qualify clocks/expiry/epochs or native/range/physical error, or grant source,
one-use execution, permission or admission. All flags remain false/no command.


##### Opt-In Current-Recorder Native ToF Pending Snapshot (2026-11-09)

The private delivered snapshot accepts literal `include_pending_sources=True`.
Its default performs no pending copies/matches and omits that payload. The opt-in
path uses the same bounded primitive queue copier as pending matching, then
matches retained pending sources twice and checks original deque identity,
primitive queue words/masks and the outgoing detached copies. Closing pending
checks follow the second companion-State/frame check. Existing current producer,
recorder/archive/RNG/source-file and delivered-source checks still apply; unknown
omits source, frame and pending payloads together.

The [pending-snapshot checkpoint][native-tof-pending-snapshot-review] records
finite missing-lineage, changed queue/content/identity, late frame-time word,
outgoing-copy, unchanged-default and literal-option controls. No recorder read,
retention, geometry replay, step/reset, clock sampling or RNG draw is performed
by publication. This is two-point current local correspondence, not atomicity,
perpetual freshness, a complete acquisition/history/scan proof, original-read
pending provenance, source/coverage/physical/numerical/clock qualification or
one-use/permission/admission. All flags remain false/no usable command.


##### Original Recorder-Read Native ToF Pending Correspondence (2026-11-09)

The private recorder read accepts literal `capture_native_tof_pending_source=True`.
It copies actual bounded pending words/masks into both producer samples, retains
the original deque identity, and publishes only under existing sample/content/
owner/producer/frame/RNG/source-file rechecks. Default reads clear this optional
evidence. The existing opt-in pending snapshot now requires exact correspondence
to that original read plus the retained queue identity, and preflights its new
primitive evidence before ownership hashing. A resnapshot or matching hash is
not substituted for a missing original read.

The [original-read checkpoint][native-tof-pending-original-read-review] records
detached data, defaults/clearing, missing/tampered evidence, changed identities,
bounded pre-hash rejection and failed-read nonpublication. Ordinary reads still
perform their existing bounded synthetic C1 staging; native pending capture adds
no geometry reconstruction. Snapshot publication remains read/retain/replay/
step/reset/clock/RNG-free. This checks local original-read correspondence only,
not atomicity/perpetual freshness, complete acquisition/retention/history/scan
coverage, physical/native/range/clock/error/source qualification or one-use/
permission/admission. All flags remain false/no usable command.


##### Opt-In Native ToF Acquisition Clock Windows (2026-11-09)

`RoverEnv.step(..., capture_native_tof_timing=True)` requires literal native ToF
source capture as well. Only an actual fresh sample performs two diagnostic
`time.monotonic_ns` reads: before geometry and after sampling/noise/dropout,
pending enqueue and native-source copying. A separate private timing cache names
that actual native-source object, RNG identities and nominal acquisition/delivery
ticks. Default/held/reset paths clear the cache and add no ToF clock reads;
rejected preflight preserves previous evidence. Observations/info and default
source/receipt behavior, physics and RNG outputs remain unchanged.

The [acquisition-clock checkpoint][native-tof-acquisition-clock-review] records
controlled counter/error/unknown/default/held/reset/preflight and paired-receipt
controls, not measured latency samples. Signed reference values are supported;
unavailable/noninteger/backward pairs have unknown duration. Clock qualified and
all source/admission flags remain false. The window excludes preflight, motion,
history/observation construction, final timing publication and return; it is not
complete API latency, sensor exposure, a physical/nominal-clock correspondence,
deadline/error bound, epoch qualification, one-use evidence or permission.
Read-time intake/retention/publication of this timing cache remains separate.


##### Bounded Native ToF Timing-Source Intake (2026-11-09)

A private timing intake validates closed actual-cache metadata and eight false
flags, original native-source/RNG identities, nominal ticks and the caller's
bounded source epoch. It copies clock context around one existing actual native
ToF source intake and rechecks timing/source identities, metadata and outgoing
clock content. A shared bounded diagnostic-clock checker supports only the two
named scopes; the existing motion-receipt wrapper and its policy remain intact.
Signed/unknown windows stay signed/unknown rather than becoming timing bounds.

The [timing-intake checkpoint][native-tof-timing-intake-review] records bounded
missing/malformed/oversize and late cache/metadata/outgoing-copy controls. Intake
does not step/reset, replay geometry, read/retain recorder state, draw RNG values
or take new clock reads. Its detached primitive record is local source/clock
pairing only, not current-owner retention/publication, atomicity/perpetual
freshness, complete acquisition/coverage/history, physical/native/range/error/
clock/epoch qualification, one-use evidence or permission/admission. All flags
and clock qualified remain false/no usable command; clock gaps are not bridged.


##### Recorder-Owned Native ToF Timing Retention (2026-11-09)

Private `record_native_tof_source(..., include_timing=True)` is a separate literal
opt-in, still requiring `synthetic_test_only=True` and the original current
producer/read. It uses two actual timing-source intakes instead of the two
untimed intakes; source/owner/RNG/cache/file/producer checks remain in force.
A separate primitive timing history pairs source epoch/acquisition/delivery IDs
and detached diagnostic clocks with uniquely retained native source entries.
It is bounded by the same eight acquisitions, strictly ordered, preflighted
before ownership hashing, checked before publication and trimmed with source
history. Equal repeats deduplicate; changed repeats reject. Default untimed
retention adds no timing entries; missing timing is not inferred or bridged.

Both histories publish only after closing checks, including original timing
cache identity and staged clock/history content. Failed retention does not publish
staged evidence; external callback mutations are not undone. This neither adds
clock reads nor reruns geometry/ordinary recorder reads/steps/resets. It provides
no public timing snapshot, complete timing/coverage history, atomic/perpetual
freshness, physical/range/error/clock/expiry/one-use/permission qualification,
admitted predecessor or usable command. All qualification flags remain false.
See [timing retention controls and evidence limits][native-tof-timing-retention-review].


##### Retained ToF Timing Delivery Correspondence (2026-11-09)

Private `snapshot_native_tof_delivery(..., include_timing=True)` separately opts
in to retained timing for the actual matched delivered acquisition and, when
requested, every actual matched pending acquisition in queue order. It retains
the existing current-owner/original State/frame/source/queue checks and literal
synthetic-only opt-in. Before ownership hashing it validates the bounded timing
history against retained native sources; epoch/acquisition/delivery IDs must
uniquely agree. After closing frame/pending checks it rechecks original history
identity/content and detached outgoing pairs. Missing, malformed or changed
timing yields unknown with no source/frame/pending/timing payload. Default
snapshots omit timing and do not inspect timing history.

Successful optional `timing` and `pending_timing` entries are detached diagnostic
records only. Held observations use the matched acquisition, not current tick
as a substitute; unknown clock duration/status stays unknown. No geometry,
ordinary recorder read, retention, step/reset or new clock read is introduced.
This establishes no elapsed coverage, physical timing, accepted clock domain,
expiry/one-use/native execution/permission/admission or usable command. All
qualification flags remain false; no atomic or perpetual freshness guarantee.
See [timing delivery controls and limits][native-tof-timing-delivery-review].


##### Bounded Native ToF Floor Division Residuals (2026-11-09)

Private synthetic-only `_native_tof_floor_division_residuals` reports exact
rational differences between recorded native floor candidates and the exact
quotient of recorded binary64 height/vertical direction, not ideal geometric
operands. Inputs are a positive finite builtin height, 192 finite canonical ray
words and 64 canonical finite/positive-infinite candidate words, bounded to 32
characters each. Standard `Fraction` preserves exact values under the existing
4096-bit source budget; output pairs are normalized numerator/denominator tuples.
Each ray retains its index, original vertical/candidate hex words, exact quotient
and signed observed-minus-quotient residual where finite/downward. Missing
downward candidates remain unknown; non-downward rays require positive infinity
and have no quotient/residual. Unsupported shape/words/branches reject.

This consumes supplied words only, with no geometry, source/recorder read,
retention, step/reset, clock or hash. Nonzero residuals are reported, not accepted
against a new tolerance. It neither binds these words to a current producer nor
qualifies direction/trigonometry/normalization, minima/occlusion, binary32 range,
full numerical/physical/coverage/error/clock/permission/admission or usable
commands. All eight flags remain false; no uniform or adopted error allowance.
See [native floor residual controls and limits][native-tof-floor-residual-review].


##### Current-Source Native ToF Floor Residuals (2026-11-09)

Private `snapshot_native_tof_delivery(..., include_floor_residuals=True)` is a
separate literal opt-in. It probes already matched actual delivered and, when
requested, pending native sources after original ownership fingerprinting.
Each diagnostic carries the source epoch/acquisition/delivery IDs; pending
diagnostics preserve matched queue order. It collects all closing probe outputs
after companion State/frame and optional pending/timing checks before bounded
exact word comparisons. Changed ratios, flags, indices and oversized staged
integers reject without hashing residual output. Source/owner/RNG/file/current
checks remain; malformed/missing/changed evidence yields no partial payload.
Default source snapshots skip residual probes and omit their fields.

This composes actual-source correspondence with per-word arithmetic only. Missing
floor candidates remain unknown; no physical, full geometric/range/error/clock/
coverage/native-execution/permission/admission or usable-command qualification
is adopted. All eight flags false, no atomic/perpetual freshness guarantee.
See [source-bound floor controls and limits][native-tof-owned-floor-review].


##### Ideal Native ToF Sampling Residuals (2026-11-09)

Private synthetic-only `_native_tof_sampling_residuals` supports mounted native
returns with positive finite height/range words and zero noise/dropout only.
It consumes 64 canonical finite/positive-infinite pre-noise words, 64 uint32
sample words and 64 builtin masks; nonfinite binary32 samples reject. Expected
validity follows the actual pre-noise finite/strictly-below-ceiling branch;
invalid returns require positive-zero sample words. For valid returns it reports
the exact rational observed-binary32-minus-clipped-native residual, including
zero-noise addition/clipping, original hex/word values and ray identity, under
the existing 4096-bit pair cap. Invalid returns are masked diagnostics with no
range residual, never max-range clearance. Unsupported profile/masks/words reject.

This pure supplied-word calculation does not read/replay the producer, bind a
current owner or decide whether any nonzero residual is acceptable. No rounding
tolerance, ideal ray/geometry/occlusion, complete range/error/coverage, physical/
clock/native-execution/permission/admission or usable command is qualified.
All eight flags remain false. See [sampling residual controls and limits][native-tof-sampling-review].


##### Current-Source Ideal ToF Sampling Composition (2026-11-09)

Private `snapshot_native_tof_delivery(..., include_sampling_residuals=True)`
separately opts into the ideal sampling diagnostic for the already matched
delivered source and requested pending sources. It preserves acquisition/epoch/
delivery IDs and pending order; defaults omit these fields and skip probes.
Only the existing mounted, zero-noise/dropout diagnostic domain is supported.
All closing timing, floor and sampling callees finish before outgoing derived
groups are compared. Retained timing layout is preflighted again before hashing;
residual output is bounded and compared without entering a hash. Malformed,
missing or changed evidence yields unknown without partial source/frame data.

This composes current source correspondence with supplied-word arithmetic, not
an accepted error bound, independently correct rounding, ideal geometry, full
coverage, physical clearance, clock/deadline/one-use or admission qualification.
All eight flags stay false; no atomic or perpetual freshness promise. Recovery,
finite ledgers and controls are in [sampling composition][native-tof-owned-sampling-review].


##### Native ToF Direction Squared-Norm Residuals (2026-11-09)

Private synthetic-only `_native_tof_direction_norm_residuals` independently
consumes 192 finite canonical binary64 direction words, at most 32 characters
each. For each of 64 triples it reports the exact squared norm and signed
squared-norm-minus-one ratio, retaining the original words and ray index.
It uses exact `Fraction` arithmetic with conservative dyadic sum preflight
and the existing 4096-bit pair cap. Unsupported shapes/words or excessive
mixed-exponent work reject; signed zero remains distinct in source words.
Zero and nonunit vectors report discrepancies rather than passing or failing
a new normalization tolerance.

There is no geometry replay, source read, retention, step/reset, clock/RNG or
hash in this helper. It does not bind supplied words to a current recorder,
prove ideal directions/trigonometry/rotations, or adopt numerical, physical,
range, coverage, source, clock, permission or admission qualification. All eight
flags remain false. See [ray-norm controls and limits][native-tof-ray-norm-review].


##### Current-Source Native ToF Ray-Norm Composition (2026-11-09)

Separate literal `include_direction_norm_residuals=True` pairs the bounded
norm diagnostic with matched delivered and requested pending sources and their
epoch/acquisition/delivery IDs. Defaults omit these fields and make no norm
probe calls. All closing floor/sampling/norm/timing callees precede derived
outgoing comparisons, so late changes to an earlier diagnostic or timing pair
reject; staged residuals never enter hashes. Missing, malformed or changed
evidence yields unknown without partial source/frame/diagnostic data.

This establishes local source-word correspondence only, not a normalization
tolerance, ideal-direction/trig/rotation proof, numerical/range/error/coverage/
physical/source/clock/permission/admission qualification or usable command.
All eight flags stay false; no atomic/perpetual freshness guarantee. The
[composition checkpoint][native-tof-owned-norm-review] records bounded controls
and the retained/corrected held-fixture resource overrun.


##### Native ToF Minimum-Candidate Correspondence (2026-11-09)

Separate cold `tof_ranges(..., selection_source={})` retains the actual mounted
minimum reduction's last finite candidate matching each result word, its index,
observed finite equal minima, copied profile/pose and detached pre-noise ranges.
It observes the existing floor, four finite walls and each cylinder's near/far/
top candidates; numeric ties stay explicit even when result words differ by
signed zero. Last matching operand labels do not establish unique causality.
Indices are floor/none=-1, walls0..3 in axis/side order, cylinders0..31 in input
order. The nominal candidate count is at most101, not geometric coverage proof.

Only empty builtin dictionaries are accepted; native and selection dictionaries
must be distinct. Existing finite-input/32-obstacle guards apply and legacy
planar selection capture rejects before geometry. Default/native-source-v1
words and schema stay unchanged; no clock, sampling, RNG, step/reset or recorder
read is introduced by this core trace. It is not yet retained with a fresh
acquisition, delivered/pending source or original recorder State/frame.
All eight flags stay false; no physical hit, unique selection, numerical/range/
coverage/source/clock/permission/admission or usable-command qualification follows.
See [minimum-candidate controls and limits][native-tof-selection-review].


##### Actual Fresh ToF Selection Acquisition Pairing (2026-11-09)

Separate literal `RoverEnv.step(..., capture_native_tof_selection=True)` requires
native-source capture and mounted mode, with type/dependency/pose/obstacle/legacy
preflight before mutation or clock reads. Only a fresh actual sample forwards
the distinct selection dictionary into its existing ToF geometry evaluation.
The private acquisition cache names the original native cache by identity,
original RNG references, tick/nominal delivery and actual raw selection record;
native and selection pre-noise arrays are detached from each other and sampling.

Default/source-only forwarding calls, observation/info/native-source-v1 fields,
noise/dropout/RNG order and source words stay unchanged. Default/held/reset
paths clear selection cache; rejected preflight preserves previous caches.
Selection adds no clock read; optional timing still takes its existing pair and
shares the original native source identity. All flags remain false. This is
fresh acquisition pairing only, not delivered/original State, recorder intake/
retention/publication, unique physical hit, numerical/range/coverage/source/
clock/permission/admission qualification. See [acquisition controls and limits][native-tof-selection-acquisition-review].


##### Bounded Native ToF Selection Intake (2026-11-09)

Separate private intake checks the closed actual fresh selection-acquisition
cache and original native-source/RNG/tick/delivery identities. Two existing
read-only native intakes surround a detached primitive selection copy. Closing
comparisons check both native packets, live cache/profile/pose and staged
selection data. No geometry, source/recorder read, clock or RNG activity is used
to reconstruct missing evidence. The fixed64 entries retain last matching
candidate labels/indices and observed tie ambiguity, with32 obstacles/101 nominal
candidates maximum; input/native pre-noise words use exact binary64 hex copies.
All eight qualification/admission flags remain false. Missing/malformed/stale/
changed evidence rejects without a packet, not an accepted source verdict.

This is bounded point-in-time diagnostic correspondence, not an atomic or
perpetual freshness guarantee, full minimum/intermediate arithmetic proof,
unique physical hit, numerical/coverage/range bound, clock qualification or
permission. Recorder retention, original-read State pairing and delivery
publication are separate prerequisites; defaults and existing schemas stay
unchanged. [Review §225][native-tof-selection-intake-review] records the finite
controls, closing-context follow-up and required root gate.


##### Selected Native ToF Wall-Word Residuals (2026-11-10)

Private synthetic-only `_native_tof_selected_wall_residuals` consumes supplied
canonical position/bounds/ray/range words and fixed64 candidate labels/indices.
For each supplied finite wall selection it reports the exact observed-minus-
`(wall-position_axis)/direction_axis` discrepancy using guarded rational
arithmetic, with at most256 value conversions/192 operations and4096-bit
preflight. Other kinds have no wall quotient; infinite wall words remain
unknown, zero wall denominators and unsupported layouts reject. Original words,
wall index and ray index are retained; all eight flags remain false.

This compares supplied stored operands, not ideal geometry or independently
retained subtraction/division primitives. It does not authenticate a source,
prove candidate masking/minima, cover unselected walls/cylinders or accept a
tolerance, full range/error/coverage, physical clearance, clock, permission or
admission. There is no source/recorder read, geometry/replay, clock or RNG work.
See [wall-word controls and limits][native-tof-wall-word-review].


##### Actual Native ToF Wall Calculation Trace (2026-11-10)

Separate cold `tof_ranges(..., wall_source={})` copies the four actual mounted
wall computations in axis/side order. Each records native numerator, raw
division, altitude/across words, predicate, masked candidate and post-wall
minimum, plus original pose/profile/rays/floor/final ranges. Copies are detached
from native/selection outputs; empty builtin distinct dictionaries and existing
finite-input/32-obstacle preflight apply. Legacy mode rejects before geometry.
Defaults/native-source-v1/selection words and expression order stay unchanged.
There is no added direction, geometry, sampling, RNG/clock or recorder work.

These are actual cold calculation values, not independently correct arithmetic,
physical hits, complete coverage, an adopted error allowance or source/clock/
permission/admission qualification. All eight flags false. Fresh acquisition
pairing, closed intake, recorder retention and delivery remain separate; this
trace is not retroactively reconstructed from final selected words.
See [wall trace controls and limits][native-tof-wall-trace-review].


##### Actual Fresh ToF Wall Acquisition Pairing (2026-11-10)

Separate literal `RoverEnv.step(..., capture_native_tof_wall=True)` requires
native-source capture and mounted mode, with type/dependency/pose/obstacle/legacy
preflight before mutation or clocks. Only the original fresh sample forwards
its separate wall dictionary; the private wall acquisition cache binds the raw
trace to original native-cache/RNG identities and acquisition/nominal-delivery
ticks. Timing and selection opt-ins may coexist against that same native cache.
Default/source-only forwarding calls, observations/info, native-source-v1 and
noise/dropout/RNG order stay unchanged. Default/held/reset clear the wall cache;
rejected preflight preserves previous caches. No additional geometry or clocks.

All eight flags stay false. This establishes local fresh-acquisition pairing,
not closed intake, recorder retention, delivered State, independent arithmetic/
masking/coverage/error/physical correctness, clock qualification, permission or
admission. Missing intermediate data must not be reconstructed from selection
labels. See [wall acquisition controls and limits][native-tof-wall-acquisition-review].


##### Conditional Discrete Motion Core (2026-11-06)

**Implemented and fixture-tested under separate bounded approval; not source
qualification or command admission.** The private increment computes the
conditional command/braking motion required above; it exposes no permit.
The named consumer is the future S4 actual-command sweep guard. Existing C1
enclosure/witness APIs hardwire `_c1_curved_centerline` and its continuous
braking phase; neither accepts an arbitrary acceleration-limited discrete path.
Their current clear/blocked results cannot qualify the new command by relabeling
the trajectory. [Reviews §§152-153][admission-motion-core-review] record the
proposal, separate approval, results and remaining boundary.

**Implemented code boundary.** The private conditional motion producer lives
in the existing C1 diagnostics module, with controls in the existing simulator
tests. It takes explicit artificial motion/configuration/error assumptions and
returns an owned bounded path/enclosure or unknown. Model the acceleration and
clipping update before the command interval, then each zero-target/zero-yaw
braking update until stopped, retaining uncertainty at every tick. Cover the
whole body between vertices, not only endpoints. Keep the one-command-tick,
16-braking-tick and 128-total-chord limits; zero-length phases still count as
attempted ticks. Unsupported bounds, nontermination inside the cap, overflow
or ambiguous evidence must return unknown, not a shorter path or clearance.

This producer supplies conditional mathematical/fixture evidence only. It
does not establish native integration/registration error, S1-S5 satisfaction,
question answers or command admission. All existing qualification/training
flags remain false. No source adapter, request/permit/executor runtime, wire
change, normal controller replacement or C1 geometry-query extension is in
this first proposal. Existing helpers/defaults and their rejection/alias
regressions stay unchanged; later source and path-aware coverage work needs
its own evidence and scope.

| Fixed control groups | Required discrimination |
| --- | --- |
| G01-G04 | Rest launch, moving straight command, acceleration clipping and zero-target braking. The declared supported straight controls must produce a complete conditional enclosure, not all unknown. Check the discrete stopping tail against an independent exact-rational recurrence. |
| G05-G08 | Mirrored nonzero command turns and both signs of a declared source/decoded discrepancy. Require the declared conditional enclosures to retain the full assumed errors through command and braking; no zero-error substitution. Use an independently bounded circular-arc reference for the command interval, not the producer or old continuous-braking helper as its own oracle. |
| G09-G12 | Missing/unsupported error evidence, invalid/nonfinite/boolean inputs, unsupported hold or configuration, and unchanged caller-owned inputs/outputs on rejection. Keep the rejection/unknown outcomes below fixed. |
| G13-G16 | Reduced braking/chord budgets, independent-reference work exhaustion and held-result ownership. Exhaustion cannot publish a partial enclosure, relax a bound, become admitted motion or silently retry. |

**Fixed fixture inputs.** Numeric decimal literals below mean their exact
stored binary64 words, not exact decimal real values. The shared profile is
`dt=0.05`, acceleration `1.0`, maximum speed `0.6`, maximum yaw rate `1.5`,
radius `0.18`, initial body-frame position `(0.0, 0.0)` and yaw `0.0`. Default
input is initial speed `0.5`, target `0.5`, command yaw rate `0.0`, hold one
tick, complete explicit zero-error *artificial* input intervals, 16 braking
ticks, 128 chords and 16 reference terms/16,384-bit intermediates. Each table
row overrides only the stated fields. The mathematical interval model treats
these stored input words as reals; it does not claim that native simulator
operations are exact or that its zero-error fixtures qualify S4.

| ID | Fixed overrides | Expected outcome |
| --- | --- | --- |
| G01 | Initial speed `0.0`, target `0.125` | Complete conditional launch-and-stop enclosure; speed changes before the first movement, not an instant jump to target. |
| G02 | No overrides | Complete constant-command straight enclosure including every discrete braking tick. |
| G03 | Target `1.0` | Complete conditional motion enclosure after the model's target-speed clipping and acceleration limit. This raw out-of-map target is not an allowed NORMAL command or permit. |
| G04 | Initial speed `0.125`, target `0.0` | Complete discrete brake-only enclosure, not instantaneous stop or continuous stopping-distance substitution. |
| G05 | Command yaw rate `1.5` | Complete left-command/straight-braking conditional enclosure. |
| G06 | Command yaw rate `-1.5` | Complete mirrored right-command/straight-braking enclosure; exact reflection of the G05 mathematical intervals must be contained. |
| G07 | Target `0.5`, command yaw rate `0.75`; initial-speed interval from binary64 words `0x3fc999999999999a` through `0x3fc99999a0000000` | Complete conditional enclosure for the full source/decoded interval, including positive binary32 discrepancy, without substituting its midpoint or eliminating it by reaching the target before movement. |
| G08 | Target `0.5`, command yaw rate `-0.75`; initial-speed interval from `0x3fd6666660000000` through `0x3fd6666666666666` | Complete conditional enclosure including the negative binary32 discrepancy through the nonsaturated first update. The word identities are artificial test inputs, not authority to relax source equality. |
| G09 | Error-evidence record absent | Unknown, `error_evidence_missing`, before motion/reference work; a fixture zero cannot be invented. |
| G10 | Initial speed `True`, target positive infinity, command yaw rate NaN | `ValueError` before motion/reference work; no writes to caller-owned data. |
| G11 | Hold two ticks and profile acceleration `0.0` | Unknown, `unsupported_profile_or_hold`; no integration or accepted shorter hold. |
| G12 | Repeat G02 twice; mutate the first returned path after the second return | Both independent enclosures complete; source inputs and the held second result remain unchanged. Two entries count, including ownership checks. |
| G13 | Braking budget zero | Unknown, `braking_budget_exhausted`, with no publishable partial enclosure; independent real braking is not capped by this failed search. |
| G14 | Chord budget zero | Unknown, `chord_budget_exhausted`, before a partial path can be published; no implicit larger budget. |
| G15 | Repeat G05 with independent-reference term budget zero | Reference unknown, `reference_term_budget_exhausted`, supplies no correctness evidence for the producer. No retry or fallback oracle is allowed. |
| G16 | Repeat G02 with independent-reference intermediate cap one bit; hold a preceding owned result | Reference unknown, `reference_integer_budget_exhausted`, before oversized arithmetic; the held result stays unchanged, with no producer admission or hidden reference retry. |

**Producer/reference separation.** The private producer models the
order of `RoverEnv.step` as an ideal discrete recurrence: clip the target, apply
the acceleration-limited speed update, integrate that constant-speed command
interval, then apply zero target/yaw and the same update before each braking
interval. Bound uncertain speeds through the whole recurrence. For a nonzero
command yaw rate, form rational interval sine/cosine enclosures for the short
command arc, then a straight braking tail at its bounded final heading. Exact
rational comparisons and outward conversion must enclose every returned
binary64 endpoint; bound between-vertex sagitta and the full body/error radius.
Do not call the old centreline or claim to enclose native roundoff by this model.
Reserve/check term and integer-growth budgets before arithmetic; use the same
16-term/16,384-bit ceilings for the producer's arc arithmetic as for reference.
An unresolved enclosure returns unknown; no extra terms or guessed epsilon.

The test reference must independently derive the discrete straight recurrence
and integrate the sine/cosine power series directly for the command interval,
including an explicit tail bound. It must not reuse producer coefficients,
interval helpers, polyline, trigonometric results or the old continuous-braking
centreline. Check all interval endpoints, both curved mirrors, complete stopping
and between-vertex/body bounds, not only a nominal endpoint. G07/G08 must
independently establish that their two initial-speed endpoints remain distinct
after the command update and that the enclosure contains both resulting paths;
a saturated single-target path does not exercise discrepancy propagation.
Native arithmetic,
registration and actual-executor discrepancy still need separate S4 evidence;
this bounded ideal reference is neither a proof acceptance nor an alternative
general arithmetic/certificate program. No NF1/owner/typed-join helper is called.

The fixed matrix passed under its separate bounded approval; this is fixture
evidence, not native execution or source qualification. If a later approved
increment cannot meet an expected conditional success, retain that failure and
request a revised scope; do not replace a row, weaken a bound or quietly change
success to unknown. Existing false-clear/near-contact/outer-tube regressions and
the 0.6 m/s decoded-source rejection remain unchanged. No scenes or task data
are created, and no global navigation target is narrowed.

| Bounded fixture ledger | Separately approved limits; results in REVIEW §153 |
| --- | --- |
| New controls | Exactly 16 fixed IDs; at most 32 producer entries and 32 independent-reference entries per complete matrix. Count invalid, early-return, faulted and abandoned entries before work; no unmetered debug/reference calls. |
| Producer work | At most one command interval, 16 modeled braking ticks and 128 chords per entry, plus at most 16 arc-series terms and 16,384-bit integer intermediates, with pre-operation growth guards/capacity reservation. No adaptive cap increase or retry; report attempted ticks/chords/terms separately. |
| Independent reference | At most 16 series terms and 16,384-bit integer intermediates per reference entry, with pre-operation growth guards. Fixed controls passed within these limits; this is not general feasibility or accepted arithmetic proof. Failure stops that control. Do not reuse the unaccepted NF1/typed-join certificates as authority. |
| Geometry/source/runtime entries | Zero new C1 coordinator, exclusion, occupied-witness, capture, relative-input/registration, owner-event, wire-adapter or rover reset/step calls in this family. Zero permit/executor/actuation, tokenizer/model, episode/log-replay or board operations. |
| Verification positions | At most four complete or aborted execution positions, including failed imports/teardowns, focused checks, repairs and a final root gate: at most 128 producer and 128 reference entries total. Three positions used, totaling 54 producer/35 reference entries; the unused fourth is not a follow-on run approval. No fifth position or borrowing from an older scope. |
| Old regression renewal | Exactly one final invocation of the current default suite under unchanged existing per-family controls, including current simulator/C1 and interface regressions; preserve the known QDQ xfail. This one renewal is spent. It is compatibility checking only, not renewal of standalone old experiments, deferred SC18-v0, opt-in native studies or historical report generation. Any further root invocation needs renewed old-regression permission. |
| Resources and artifacts | Serial CPU-only, in-memory synthetic fixtures; no download, dependency, GPU, environment or hardware change. Retain any failed-command evidence in the existing ignored run area; no task log, dataset, new report or artifact cleanup is authorized. Loop/bit caps are work limits, not measured wall-clock/RSS or target-fit evidence. |

The default source gate `python -m pytest -q && ruff check . && git diff --check`
and changed-file formatting passed at the source checkpoint: 2,285 passes,
the known QDQ xfail and 71 existing warnings. That single root renewal is spent;
all old spent positions remain historical, not refunded. No failed test or
relaxed bound was used to obtain this result. Source qualification and later
full-guard derived coverage/witness/registration work are outside the zero-query
motion-core ledger and need separate accounting before their implementation.


##### Conditional Path-Cell Kernel (2026-11-06)

The resumed autonomous workflow implemented an additive spatial prerequisite
for the named actual-command guard, not another arithmetic/identity audit.
The private `_c1_exclude_path_cells` checks an explicitly supplied planar path
tube against declared low-height free prefixes and the existing continuous
cylinder-center/radius-band search. It does not derive a path from the old
continuous braking formula. At most 512 prefixes and 129 path vertices are
accepted; the existing 65,536-cell/12-depth/16-band hard ceilings remain.
Default cell/depth/band limits stay 32,768/10/8. The assumed current body is
the existing 0.18 m disk; absent body-clear evidence or free prefixes stays
unknown. A reduced query bound must not omit any part of the supplied tube.

Whole-cell strict separation and free-prefix containment retain contact,
missing support and work-exhaustion abstention. The kernel's exclusion is only
conditional cylinder geometry; it does not establish wall support, sensor
source/registration errors, the supplied path's relation to actual motion,
numerical certification, S1-S5 satisfaction or command admission. It adds no
public/runtime/wire path. Existing C1 helpers and all prior source/test nodes
are unchanged. [Review §155][path-cell-review] records the twelve fixed
controls, verification and remaining boundary.

The separate fixture-only adapter described below now connects complete
discrete endpoint boxes/body radii to latest C1 prefixes and wall support.
The kernel and adapter retain source/registration/numerical/admission limits;
neither permits episode collection, source qualification or a usable permit.


##### Conditional Discrete-Path and Source-Word Boundaries (2026-11-06)

The private `_probe_synthetic_c1_discrete_path_enclosure` consumes the complete
discrete-motion fixture, not a recomputed continuous path. It requires joined
chords/endpoint boxes, supported work metadata and a terminal zero-speed
interval. Midpoint vertices are usable only after expanding every chord radius
by the complete endpoint-box L1 half-width; the maximum expanded radius encloses
the complete path tube. The latest low-height C1 prefixes enter the path-cell
kernel at most once. Missing body/domain premises, stale/masked captures,
unsupported capture-to-reference motion, malformed motion or exhausted work
remain unknown. No radius, age, dynamics or search tolerance is relaxed.

Axis-aligned wall support is checked separately by rotating the complete path
and prefixes into arena axes and requiring strict prefix support beyond all
path extrema plus the expanded tube radius. This remains an ideal fixture
declaration, not independent return/registration evidence or numerical proof.
The adapter's exclusion has a separate experimental schema and all training,
real-input, free-space, numerical, source, native and command-admission flags
remain false. Existing C1 question/witness/wire/runtime paths are unchanged.

The separate `_bind_synthetic_c1_state_intervals` binds a synthetic source
`State` to the actual encoded host-frame bytes and actual decoded values.
Fresh, valid velocity/angular-velocity/goal groups produce exact source and
decoded dyadics, their ordered closed intervals and signed decoded-minus-source
differences. Signed-zero word metadata is retained. An integer source must be
exactly representable as binary64; malformed/changed frames, stale/missing
groups, unsupported values, encoding overflow or exhausted dyadic arithmetic
stay unknown without partial fields. The local integer ceiling is 4,096 bits
and applies before scaled numerator/difference construction. Encoding a value
onto the wire does not imply that the decoded value equals the source.

This binder exposes conditional source-word discrepancy only. It does not
establish source authority, acquisition clocks, native motion/goal arithmetic,
registration/range bounds, S1-S5 satisfaction or command admission. The decoded
upper endpoint of source speed `0.6` is not clamped to the configured maximum;
later consumers must reject unsupported domains. The old wire helper's changed-
decoded-value rejection remains unchanged. [Review §156][path-source-review]
records the fixed controls, retained failures and separate verification ledgers.

The separate state-to-motion bridge below now propagates the complete speed
interval. Capture-registration propagation remains a separate prerequisite;
preserve complete history and frame identity, not just a current-frame error.


##### Conditional Actual-Frame Motion Bridge (2026-11-06)

The private `_probe_synthetic_c1_state_motion` connects the actual-wire/source-
word binder to the existing discrete-motion producer's two-endpoint
`initial_speed` input. It binds a bounded declared reference tick to the actual
frame's nominal `tick * 50000` microsecond timestamp, requires the rover fixture
task/no faults, and rejects nonplanar source intervals. A source lateral value
that rounds to zero on wire is still nonplanar. Complete speed/yaw-rate
intervals must fit the existing motion domain; decoded `0.6` overshoot is not
clamped. Unsupported command domains reject before motion rather than silently
changing the requested command.

Both source/decoded speed endpoints pass through the acceleration update and
complete discrete braking tail. Explicit position/heading/profile error
evidence remains necessary; a successful source-word binding supplies none of
it. Missing evidence or bounded-work failure stays unknown without partial
geometry. The source-word and motion integer ceilings remain 4,096 and 16,384
bits; the one-command/16-braking-tick/128-chord/16-term limits are unchanged.
Inputs and returned evidence are separately owned. All qualification,
admission and training flags remain false. [Review §157][state-motion-review]
records sixteen controls, both scalar endpoint references and retained failure.

Frame/tick correspondence is not source/event authority, measured clock
synchronization, native execution or a permit. The bridge exposes no runtime
action/wire decision and admits no startup/full guard. The separate history
bound below retains acquisition-to-reference interval-ending source/decoded
frames and explicit timing/profile assumptions. Do not multiply the current
frame's discrepancy by capture age: earlier intervals can differ when current
fields are exact. Passing either prerequisite satisfies none of S1-S5.


##### Conditional Complete-History Registration (2026-11-06)

The private `_bound_synthetic_c1_history_registration` supplies a separate
paired source/decoded-word transform discrepancy. It requires all frames from
the declared acquisition tick through the reference tick, including the
starting anchor; nominal timestamps and consecutive sequences must agree.
At most three past intervals/four complete frames are supported, with existing
4,096-bit source and 16,384-bit arithmetic ceilings. All source words must
remain fresh, planar and within the unchanged motion domain. Missing history,
changed/stale words, unsupported domains or work exhaustion stay unknown
without a partial transform or history publication.

The explicit common-starting-pose, nominal-tick-binding, stored-word-`dt` and
interval-ending-constant-twist declarations are artificial assumptions.
The nominal wire period is 50,000 microseconds; the mathematical interval uses
the existing binary64 `0.05` word. Corresponding ticks do not establish exact
real 1/20-second intervals, clock synchronization or native operation error.
No actual source pose, command dynamics or sensor return is qualified.

For speed/yaw-rate interval widths $\Delta v_j,\Delta\omega_j$, maximum speed
$V_j$ and stored-word interval $d$, begin with $e_0=h_0=s_0=0$ under the explicit
common-start premise and propagate:

$$
\begin{aligned}
h_{j+1} &= h_j+d\Delta\omega_j,\\
e_{j+1} &= e_j+d\left(\Delta v_j+V_jh_j+\tfrac12V_jd\Delta\omega_j\right),\\
s_{j+1} &= s_j+dV_j,\\
E_{\mathrm{point}} &= e_n+(R+s_n)h_n.
\end{aligned}
$$

The rotation inequality $\|u(a)-u(b)\|\leq |a-b|$ bounds the paired translation
and inverse-registration rotation. The complete point/travel lever arm is
necessary: heading discrepancy affects a distant capture point even when
current yaw words are exact. $R$ is an explicitly declared planar point norm
within the existing 4 m fixture domain, not measured range or occupancy.
Exact rational content and outward binary64 upper bounds are owned evidence;
all qualification/admission/training flags remain false. This is conditional
algebra/fixture evidence, not accepted proof or native/physical certification.

[Review §158][history-registration-review] records sixteen controls, earlier
speed/yaw discrepancies with exact current words, independent rational point
references, zero-age/three-interval limits and four spent verification positions.
The separate relative-prefix consumer below now propagates the bound into
cylinder-cell geometry without substituting it for missing native/pose/range/
clock/source evidence or admitting a command. Old exact-pose, question, wire
and normal APIs stay unchanged.


##### Conditional Registered Relative-Prefix Cells (2026-11-06)

The private `_c1_exclude_registered_path_cells` composes the complete history-
word point bound with an explicitly supplied remaining point-error allowance
and the existing numerical guard. Missing remaining-error or decoded-history/
prefix-binding declarations reject; a word-only bound is not total transform
error. The declarations and remaining allowance are fixture assumptions, not
measurement, source authority, native proof or accepted clock/range bounds.
All seven qualification/admission/training flags remain false.

The supplied planar prefixes must have all endpoints inside their declared
capture-point radius relative to their explicitly supplied decoded origin;
the consumer checks this with conservative exact L1 distances. The convex
prefix between endpoints then stays inside the same Euclidean point ball.
Existing 512-prefix/1,024-endpoint, three-interval/four-frame, source/arithmetic
and cell/depth/band hard ceilings remain unchanged. Unsupported limits, missing
body/domain/history/error evidence or exhausted arithmetic/cells stay unknown.

The combined margin is rounded outward before entering the unchanged kernel.
It erodes strict whole-cell free-prefix containment, widens path-relevant cells
and retains contact abstention. A small positive history error is not replaced
by zero or current-frame delta times age. [Review §159][registered-prefix-review]
records the sixteen controls, independently derived decoded fixture origins,
complete conversion allowances, clear-to-unknown 0.05 m error control, ownership
and retained style/probe evidence. Passing conditional cylinder geometry is not
wall support, source qualification or an admitted command.

The separate discrete-path consumer below now applies the same point margins
to relative-prefix and wall support. Keep wall and cylinder support separate;
the supplied path must still enclose actual requested command/braking, with
native/source/timing gates unclosed. No runtime/permit or study is admitted.


##### Conditional Discrete-Path Point Margins (2026-11-06)

The existing private `_probe_synthetic_c1_discrete_path_enclosure` optionally
accepts complete `point_error_evidence`. Omission preserves its default result
shape and geometry. Supplied evidence requires decoded-prefix/history binding,
complete actual source/frame history, its explicit assumptions and nonnegative
remaining point error. Missing evidence rejects; no word-only allowance is
silently treated as total registration/range/pose/native/clock error.

Only low prefixes with both endpoints inside the declared capture-point radius
under exact conservative L1 distance contribute. Unsupported prefixes are
discarded, never extrapolated or assigned a larger radius. Complete history-word
error, remaining point error and the existing numerical prefix guard are summed
rationally and rounded outward into strict wall support and unchanged cylinder
cells. The supplied motion tube remains unchanged by point error. Contact and
missing/unsupported/exhausted evidence stay unknown; all qualification/admission/
training flags remain false and every existing hard ceiling stays unchanged.

[Review §160][path-point-error-review] records sixteen controls and both retained
failed hypotheses: 1 m error loses cylinder exclusion but not wall support, and
zero-age capture is unavailable under two-tick latency. Valid delivered zero-word
discrepancy excludes; the original unavailable capture rejects before prefixes.
The separate composition below now generates motion from the same current
source/frame-history binding and explicit motion/error/profile premises. An
arbitrary supplied path is not actual-command qualification, source authority,
accepted native/physical evidence or a usable guard/permit.


##### Conditional Current-Frame Command Composition (2026-11-06)

The private `_probe_synthetic_c1_command_path_enclosure` owns one bounded complete
point-error history and derives the current source state/actual immutable frame
from its final entry. It generates the requested acceleration-limited command
and discrete braking through the unchanged motion bridge; callers supply no
arbitrary path. The generated motion and same point evidence enter the unchanged
wall/cylinder adapter. Its final registered binding must equal the current motion
binding before the complete conditional result is published.

Missing body/envelope/prefix/history/remaining-error/motion-profile premises,
unsupported command/word/frame/profile domains, work exhaustion or final binding
mismatch stay unknown without partial composition. Complete source/decoded speed
intervals remain enclosed; 0.6 wire overshoot is not clamped. Existing hard limits
remain unchanged. The 0.05 stored fixture tick is not measured clock equality or
an exact real 1/20 assertion. Conditional exclusion retains all seven false
qualification/admission/training flags and supplies no executor or usable permit.

[Review §161][command-path-review] records sixteen controls, independent rational
source/decoded motion endpoints, centre/mirrored commands, rejection stages and
owned repeats. The test-only startup/domain follow-up ([§162][command-path-review])
checks the adopted at-rest 0.125 m/s zero-turn request against exact rest history:
acceleration limits the command to the stored 0.05 m/s word, followed by one
discrete braking tick. The endpoint encloses the product of the two stored 0.05
words, not decimal-exact 0.0025 or measured motion. Missing body support and
excessive requested speed/turn reject without clamping or partial composition.
At-rest sector choice remains unknown; no sector query or normal `OK` is forged.
Source/setup, native/range/pose/clock error, one-use execution/expiry and
representative task quality remain separate; no normal runtime, permit,
actuation or study is admitted. The separate initial-setup content checker below
supplies owned conditional fixture evidence, not permission to set runtime body/
domain flags. Geometry stays offline, never current-frame command selection.


##### Isolated Initial-Setup Content (2026-11-06)

The private `_check_synthetic_c1_initial_setup` is an offline S1 prerequisite,
not an admitted source or guard. It owns the declared static Scenario, canonical
existing C1 config and bounded epoch identity only after checking their literal
types/shapes/profile, existing cylinder radius/height envelope, wall profile and
strict initial circular-body separation. Four wall comparisons and squared-circle
comparisons use guarded exact stored-word rational arithmetic, not a hypot or
guessed epsilon. Tangency/overlap/malformed/missing/unsupported/exhausted evidence
stays unknown and publishes no partial binding; successful content carries owned
config/scene/epoch with typed digests and all seven false flags.

Prototype bounds are 32 obstacle rows, 4096-bit preflight rational growth, a
64-character ASCII scene name and 32 lowercase-hex epoch characters; they are
local fixture-work/representation limits, not new global scene or device
requirements. The check does not attest that a supplied Scenario is authoritative
or complete, measure source/native/range/pose/clock uncertainty, qualify goal/
sector answers, or use current privileged geometry to select commands. It is not
S1 satisfaction, runtime body-clear support or a usable permit. Existing source
auditor guards, aliases, motion/path APIs and hard limits stay unchanged.

[Review §163][initial-setup-review] records sixteen fixed controls and the retained
digest-reference accounting repair. The separate conditional startup consumer
below now rechecks and joins this content; a body/domain flag alone cannot qualify
a runtime source. The launch stays fixed at target 0.125/zero turn; no source
authority, normal `OK`, expiry/one-use executor, actuation or study approval follows.


##### Conditional Initial-Rest Startup Composition (2026-11-06)

The private `_probe_synthetic_c1_startup_path_enclosure` bounds/rechecks the owned
initial-setup record, declared epoch and exact canonical C1 config, requires its
initial pose to match the reference and verifies complete consecutive source/
actual-frame history from tick zero. All source/decoded linear/angular intervals
must be exactly zero under the existing explicit history premises; signed zeros
retain their metadata. Only then does the unchanged command/point-margin consumer
receive derived conditional body/domain results and the fixed 0.125/zero request.
Callers cannot supply an arbitrary command/path or a body-clear flag to this join.

Mismatched setup/digest/epoch/config/pose, missing/changed/nonrest frames, missing
motion/error/profile evidence and work exhaustion stay unknown without partial
startup content. Every existing hard limit and all seven false flags remain.
Reference ticks 0-3 are the local prototype's complete initial-history domain,
not an adopted startup deadline or evidence that simulated ticks meet real timing.
The separately prepared tick-zero captures use the same two static unit scenes;
no old capture timestamp is changed to manufacture delivery or initial history.
Declared correspondence does not attest source authority/completeness, satisfy
S1-S5, qualify native/range/pose/clock error, provide a normal `OK`, one-use permit,
expiry/executor or allow a trial. [Review §164][initial-setup-review] records the
sixteen controls and retained reason-literal failures. No normal controller,
wire, task-data/study or physical behavior changes.

##### Conditional Normal-Command Mapping (2026-11-06)

The private `_map_synthetic_c1_normal_command` in the existing rules module
requires immutable bounded State/Decision bytes, exact current nominal tick/
timestamp correspondence and complete fresh active catalogue-1/model-0 `OK`
selections. It preserves existing host-group/task/fault and RuleSettings/default
age checks, including the unchanged comparison tolerance. Explicit selections,
not argmax or an invented confidence threshold, determine signed maximum left/
right yaw or zero centre yaw and literal `max_speed * tier / 3` target order.
There is no extra goal-bearing steering, distance clipping or runtime wiring.

Blocked/none/tier-zero, unusable frames or unsupported current/profile evidence
return both zero targets with a fallback reason and no partial frame binding.
That is a conditional repeated-braking request candidate, not an instantaneous
stop, verified path, permit or executed action. The existing diagnostic heuristic,
`host_action`, wire loop and every prior rules/diagnostic node are unchanged.
All seven qualification/admission/training flags remain false. Prototype tick/
frame bounds are local content checks, not measured clock/freshness guarantees.
[Review §165][normal-command-map-review] records 24 controls and the retained
import-order-only style failure. No Scene, C1 or geometry query chooses a command.


##### Conditional Mapped-Command Motion (2026-11-06)

The private `_probe_synthetic_c1_normal_state_motion` derives its only command
through the exact-frame normal mapper and feeds it to the unchanged State/word
motion bridge. Its Config must match the existing five-field discrete motion
profile; target/yaw/profile cannot be supplied independently. Both original and
decoded speed endpoints enter the full one-command-tick/repeated-braking enclosure.
The result owns mapped frame content, source intervals, conditional motion and
the exact finite binary64 command words, without a permit or native-error claim.

Existing zero-age, planar-source, complete word interval, error/profile and work
guards remain unchanged. A decoded 0.6 overshoot still rejects, not clips. An
unusable/braking selection or failed source/motion check stays unknown with no
partial mapped/source/motion content; fallback is not qualified braking or an
executed stop. All seven flags remain false. [Review §166][normal-motion-review]
records 24 fixed frame controls, two genuine speed discrepancies and unchanged
independent rational endpoint references. No new Scene/C1/history/geometry query,
normal controller, wire or data/physical behavior change is introduced.


##### Conditional Normal-Request Content (2026-11-06)

The private `_prepare_synthetic_c1_normal_request` derives bound normal motion
internally and owns exact command/fallback words, original-State and motion
fingerprints, actual host/decision frame content, a frozen dataclass Config record,
nominal application tick and one-tick hold. Separate bounded module-context fixture
identifiers/ticks are frozen as declarations, not chosen by a normal host loop or
attested by their hashes. Local identifier/tick/age shapes reuse fixture
conventions, not adopted product formats, real clocks or sensor/source evidence.

Malformed identity/context, reference mismatch or failed mapping/source/motion
returns unknown without partial request/digest. The existing typed fingerprint
preserves content types, not source truth/authority or uniqueness. Every request
reports `declared_module_fixture_only`, request-ID uniqueness unqualified and all
seven qualification/admission/training flags false. No guard response, registry,
executor, raw C1 access, capture selection, wire/runtime integration or physical
behavior is provided. [Review §167][normal-request-review] records sixteen controls,
independent typed-digest/changed-command-bit checks, owned repeat and the retained
Config serialization failure/repaired dataclass snapshot.


##### Conditional Request Matching and Expiry (2026-11-06)

The private `_check_synthetic_c1_normal_request_binding` checks bounded exact
built-in prepared/received record, context, Config, word and metadata shapes
before comparison. It rechecks the retained request fingerprint and compares
complete closed-schema canonical JSON, not a submitted matching hash. Boolean/
integer and integer/float aliases are distinct content. Exact matches at their
nominal application tick report conditional matched content; future/expired or
changed/unsupported requests reject with no partial request binding.

All outcomes retain `guard_status="UNKNOWN"`, permission false and all seven
qualification/admission/training flags false. A caller-retained record is not
source authority, stable-owner evidence, clock qualification, request uniqueness
or a one-use registry. Complete fabricated matching content cannot authorize
execution. [Review §168][normal-request-binding-review] records sixteen controls,
changed-word/frame/epoch/source/Config/ID checks and early/late tick rejection.


##### Conditional Current Request Source Recheck (2026-11-06)

The private `_recheck_synthetic_c1_normal_request_source` first applies the
bounded typed request/currentness matcher, then prepares fresh content from the
current supplied original State/actual State and Decision frames, Config and
motion error assumptions through the existing internally derived-command path.
Fresh content must match the received request. Caller targets, retained hashes
or changed frames cannot substitute for this source/motion recheck.

Receipt/type/expiry rejection stops before preparation. Changed source/frame/
Config/error or work failure stays unknown without partial request/source/motion
binding. Exact fixture correspondence owns only current content fingerprints
and diagnostics; all outcomes retain `UNKNOWN`, permission false/all seven flags
false. Declared context, clock/source authority, ID uniqueness, native error and
full guard/executor qualification remain unresolved.
[Review §169][normal-request-source-review] records sixteen controls, three
mapped sector/tier/speed combinations, substitution/error/budget rejection and
owned repeat. No geometry selects the command and no normal controller is wired.


##### Conditional Current Request/Path Margins (2026-11-06)

The private `_probe_synthetic_c1_current_request_path` rechecks the current
request, requires the separate point-history's last original State/frame to
match that source, and derives command/profile internally. It checks all eight
latest uint32 capture ticks against the declared capture context, then calls the
unchanged command/path consumer and requires its returned current frame and
generated motion fingerprint to match the request. No geometry selects a command;
the complete interval-ending history remains necessary for registration.

Only an explicit ideal C1 fixture Config, conditional body/envelope declarations
and complete point/motion assumptions support these fixture checks. Normal noisy
Config is not stripped or qualified. Changed/expired requests, foreign last
State/frame, a changed capture tick, incomplete history, unsupported error or
domain/body assumptions and unresolved margins do not publish a partial path
binding. Success owns conditional request/path correspondence, always `UNKNOWN`,
permission false/all seven qualification/admission/training flags false.
[Review §170][normal-request-path-review] records sixteen controls on two reused
C1 scenes, all eighty earlier source/312 test nodes exact and unchanged mapper.


##### Conditional Request/C1 Capture Content (2026-11-06)

The private `_check_synthetic_c1_request_capture_content` first matches the typed
request/current tick, then checks the actual ten-key C1 capture record, literal
false flags, exact typed request/capture Config values and four bounded arrays.
An owned full-record fingerprint must match the declared `c1_reference_identity`.
For this private fixture adapter only, that identity denotes the complete latest
capture record, not an accepted product format or qualified registered reference.
Array dtype/shape/bytes are preserved; no normalization or noise stripping occurs.

Changed returns/masks/poses, a single view tick, Config type aliases, unsupported
array types/shapes, nonfinite values, true flags and changed/expired requests
reject without partial capture binding. Matching occupied-fixture content is
still only content correspondence: every output retains `UNKNOWN`, no permission
and all seven qualification/admission/training flags false. The checker performs
no geometric/path query and does not establish actual producer/source authority.
[Review §171][request-capture-review] records sixteen controls on two reused
scenes, prior nodes/mapper exact, and owned repeat.


##### Conditional Owned Capture/Current Request Path (2026-11-06)

The additive private `_probe_synthetic_c1_owned_capture_request_path` first runs
the capture-content checker, then supplies only its owned matching record to the
unchanged current-source/request/path consumer. No caller-selected older history
or second capture selection is accepted. This single-capture restriction is
conservative; it does not change existing history APIs or adopt a product format.
Complete State/frame history, current command/motion, Config/error/profile,
current-body/envelope and nominal-expiry checks remain the existing prerequisites.

Before publishing a conditional exclusion, rehash the consumed owned record and
match capture/path request identity plus path/request motion identity. Input
substitution rejects before path work; later caller mutation cannot alter the
owned record, and consumed-record mutation rejects without partial path binding.
Outputs own their path enclosure and always remain UNKNOWN/no permission/all
seven flags false. [Review §172][owned-capture-path-review] records sixteen reused
controls, prior nodes/mapper exact, no source/runtime/qualification claim.


##### Conditional Straight Capture/Reference Pose (2026-11-06)

The isolated `_check_synthetic_c1_straight_capture_reference_pose` compares
declared current pose against exact rational accumulation of decoded interval-
ending speeds from complete bound State/frame history and stored-word dt. Only
zero capture heading and zero source/decoded historical turns are supported;
other past motion abstains. This is a private conservative subset, not a product
restriction, changed command meaning or curved-motion implementation.

Owned finite/equal-view metadata has fixed uint32 tick and float64 pose shapes.
Existing outward conversion supplies binary64 endpoints enclosing nominal straight
pose, without a new arbitrary tolerance or certified numerical allowance. Shifted
pose, incomplete history, malformed metadata and unsupported assumptions reject.
Outputs own pose/history content and retain UNKNOWN/no permission/all seven flags
false. Metadata correspondence does not bind full capture content, a current
request/source or actual producer/clock/registration authority. [Review §173]
[capture-reference-pose-review] records sixteen controls, prior nodes/mapper exact.


##### Opt-In Capture/Request/Pose Join (2026-11-06)

`_probe_synthetic_c1_owned_capture_request_path` now accepts the explicit literal-
bool `check_straight_reference_pose=False`. Its default diagnostic behavior is
unchanged. Opt-in checks the owned capture against complete bound history and
owns the declared current pose before path work. Unsupported past turn/heading
still abstains, without changing command meanings or the surrounding product.

Compute a rational L1 enclosure between supplied pose and nominal binary64 pose
endpoints, outward-convert it and add only that rounding component to a copied
remaining-point-error record. The full source/registration error remains separately
consumed by the existing path checker. Compare pose/path source bindings and
publish pose metadata only after final owned-capture/request/motion checks pass.
No default/schema/wire/normal controller/threshold or old hard-cap change follows.
[Review §174][checked-pose-path-review] records sixteen controls, the repaired
publication order and lint failure, four spent positions and unchanged defaults.

This remains conditional fixture content, always UNKNOWN/no permission/all seven
flags false. Current-body, source/profile, clock/ray/pose/error/native, one-use
executor, S1-S5 and task-quality evidence are not established by pose/hash matches.
The adopted S1/body/executor dependency map is complete; owned latest-event
preparation and current-owner rechecking now remove caller-selected context/tick.
Actual setup/source/coverage/error/timing and admitted predecessor/executor
evidence remain missing. Advance those dependencies without treating content
matches as qualification; general audits remain deferred. No normal profile/
runtime, usable `OK`, actuation, trial, study or data acceptance follows.


### Dataset Construction

- Define the ground-truth policy and review an evaluation set before generating
  a large teacher-labeled corpus.
- Use representative real inputs or recorded episodes alongside controlled
  synthetic examples. Random telemetry strings alone are not representative.
- Include paraphrases, negation, ambiguity, noisy or missing fields, boundary
  cases, unsupported requests, and out-of-domain inputs.
- Split by source, episode, entity, or template family before augmentation to
  prevent near-duplicate leakage across partitions.
- Keep training, development, quantization calibration, confidence calibration,
  and locked test purposes distinct. Lock test groups before model selection.
- Record dataset versions, split assignments, teacher revision, schema,
  settings, label provenance, and human corrections.
- Build the transfer set from in-domain unlabeled and augmented text (masking,
  word replacement, and n-gram sampling as in
  [Tang et al.][distillation-paper]) labeled by the teacher, not only from the
  human-labeled set. For robot states, build it from logged and simulated
  episodes with sensor-noise, dropout, and latency augmentation.

Begin with a reviewed evaluation/seed set and a manageable labeling pilot.
Hundreds or thousands of reviewed cases and a pilot of roughly 5,000-20,000
representative examples are planning ranges, not universal requirements.
Scale using learning curves and error analysis; the PDF's 150,000-example
figure is not an established minimum.

[baseline-admission-review]: ../../REVIEW.md
[baseline-host-source]: ../../sim/rules.py
[c1-wire-rejection-review]: ../../REVIEW.md
[admission-dynamics-source]: ../../sim/rover.py
[source-command-admission-review]: ../../REVIEW.md
[admission-gap-review]: ../review/171-180.md#176-admission-evidence-gap-mapping-2026-11-06
[owned-event-request-review]: ../review/171-180.md#177-owned-latest-event-request-preparation-2026-11-06
[owned-current-recheck-review]: ../review/171-180.md#178-owned-current-request-rechecking-2026-11-06
[owned-delivery-review]: ../review/171-180.md#179-owned-delivery-integrity-and-qualification-handoff-2026-11-06
[qualification-packet-review]: ../review/171-180.md#180-source-and-consumer-qualification-packet-2026-11-06
[qualification-dynamics]: ../../sim/rover.py
[qualification-consumers]: ../../sim/diagnostics.py
[realized-receipt-review]: ../review/181-182.md#182-opt-in-simulator-realized-motion-receipts-2026-11-09
[simulator-source-read-review]: ../review/183-220.md#183-recorder-reads-from-the-actual-simulator-owner-2026-11-09
[native-motion-source-review]: ../review/183-220.md#184-native-simulator-motion-words-and-emitted-frames-2026-11-09
[native-goal-source-review]: ../review/183-220.md#185-native-goal-producer-words-and-source-pose-2026-11-09
[receipt-clock-review]: ../review/183-220.md#186-diagnostic-monotonic-receipt-windows-2026-11-09
[receipt-retention-review]: ../review/183-220.md#187-producer-owned-receipt-retention-2026-11-09
[receipt-source-pose-review]: ../review/183-220.md#188-opt-in-producer-receipt-and-source-pose-linkage-2026-11-09
[receipt-chain-review]: ../review/183-220.md#189-retained-receipt-segment-chain-consistency-2026-11-09
[receipt-history-review]: ../review/183-220.md#190-bounded-source-linked-receipt-history-2026-11-09
[receipt-pairing-review]: ../review/183-220.md#191-full-retained-source-history-pairing-checks-2026-11-09
[receipt-snapshot-review]: ../review/183-220.md#192-read-time-actual-producer-history-snapshots-2026-11-09
[integration-source-review]: ../review/183-220.md#193-actual-native-integration-source-intermediates-2026-11-09
[integration-ingestion-review]: ../review/183-220.md#194-actual-source-native-integration-cache-ingestion-2026-11-09
[native-integration-snapshot-review]: ../review/183-220.md#195-read-time-actual-native-integration-snapshots-2026-11-09
[native-arithmetic-review]: ../review/183-220.md#196-supported-native-word-arithmetic-discrepancies-2026-11-09
[native-arithmetic-composition-review]: ../review/183-220.md#197-current-owned-native-arithmetic-composition-2026-11-09
[native-arithmetic-record-review]: ../review/183-220.md#198-exact-native-arithmetic-record-validation-2026-11-09
[receipt-clock-consistency-review]: ../review/183-220.md#199-diagnostic-receipt-clock-consistency-2026-11-09
[receipt-clock-order-review]: ../review/183-220.md#200-adjacent-retained-clock-window-ordering-2026-11-09
[native-tof-source-review]: ../review/183-220.md#201-native-tof-input-and-computed-value-retention-2026-11-09
[native-tof-sampling-review]: ../review/183-220.md#202-actual-native-tof-sampling-source-retention-2026-11-09
[native-tof-intake-review]: ../review/183-220.md#203-bounded-fresh-native-tof-source-intake-2026-11-09
[native-tof-retention-review]: ../review/183-220.md#204-recorder-owned-fresh-native-tof-intake-2026-11-09
[native-tof-snapshot-review]: ../review/183-220.md#205-read-time-current-native-tof-source-snapshot-2026-11-09
[native-tof-history-review]: ../review/183-220.md#206-bounded-native-tof-acquisition-history-2026-11-09
[native-tof-delivery-review]: ../review/183-220.md#207-retained-native-tof-delivered-array-correspondence-2026-11-09
[native-tof-delivery-snapshot-review]: ../review/183-220.md#208-current-recorder-native-tof-delivery-snapshot-2026-11-09
[native-tof-companion-frame-review]: ../review/183-220.md#209-native-tof-companion-original-stateframe-correspondence-2026-11-09
[native-tof-pending-review]: ../review/183-220.md#210-retained-native-tof-pending-queue-correspondence-2026-11-09
[native-tof-pending-snapshot-review]: ../review/183-220.md#211-opt-in-current-recorder-native-tof-pending-snapshot-2026-11-09
[native-tof-pending-original-read-review]: ../review/183-220.md#212-original-recorder-read-native-tof-pending-correspondence-2026-11-09
[native-tof-acquisition-clock-review]: ../review/183-220.md#213-opt-in-native-tof-acquisition-clock-windows-2026-11-09
[native-tof-timing-intake-review]: ../review/183-220.md#214-bounded-native-tof-timing-source-intake-2026-11-09
[native-tof-timing-retention-review]: ../review/183-220.md#215-opt-in-recorder-owned-native-tof-timing-retention-2026-11-09
[native-tof-timing-delivery-review]: ../review/183-220.md#216-retained-tof-timing-delivery-correspondence-2026-11-09
[native-tof-floor-residual-review]: ../review/183-220.md#217-bounded-native-tof-floor-division-residuals-2026-11-09
[native-tof-owned-floor-review]: ../review/183-220.md#218-current-source-native-tof-floor-residual-composition-2026-11-09
[native-tof-owned-sampling-review]: ../review/183-220.md#220-current-source-ideal-tof-sampling-composition-2026-11-09
[native-tof-ray-norm-review]: ../review/221-225.md#221-native-tof-direction-squared-norm-residuals-2026-11-09
[native-tof-owned-norm-review]: ../review/221-225.md#222-current-source-native-tof-ray-norm-composition-2026-11-09
[native-tof-selection-review]: ../review/221-225.md#223-native-tof-minimum-candidate-correspondence-2026-11-09
[native-tof-selection-acquisition-review]: ../review/221-225.md#224-actual-fresh-tof-selection-acquisition-pairing-2026-11-09
[native-tof-selection-intake-review]: ../review/221-225.md#225-bounded-native-tof-selection-intake-2026-11-09
[native-tof-wall-word-review]: ../../REVIEW.md#231-selected-native-tof-wall-word-residuals-2026-11-10
[native-tof-wall-trace-review]: ../../REVIEW.md#232-actual-native-tof-wall-calculation-trace-2026-11-10
[native-tof-wall-acquisition-review]: ../../REVIEW.md#233-actual-fresh-tof-wall-acquisition-pairing-2026-11-10
[admission-motion-core-review]: ../../REVIEW.md
[path-cell-review]: ../../REVIEW.md
[path-source-review]: ../../REVIEW.md
[state-motion-review]: ../../REVIEW.md
[history-registration-review]: ../../REVIEW.md
[registered-prefix-review]: ../../REVIEW.md
[path-point-error-review]: ../../REVIEW.md
[command-path-review]: ../../REVIEW.md
[initial-setup-review]: ../../REVIEW.md
[normal-command-map-review]: ../../REVIEW.md
[normal-motion-review]: ../../REVIEW.md
[normal-request-review]: ../../REVIEW.md
[normal-request-binding-review]: ../../REVIEW.md
[normal-request-source-review]: ../../REVIEW.md
[normal-request-path-review]: ../../REVIEW.md
[request-capture-review]: ../../REVIEW.md
[owned-capture-path-review]: ../../REVIEW.md
[capture-reference-pose-review]: ../../REVIEW.md
[checked-pose-path-review]: ../../REVIEW.md
[c1-prototype-source]: ../../sim/diagnostics.py
[navigation-reference]: ../../sim/navigation.py
[wire-python]: ../../interface/protocol.py
[distillation-paper]: https://arxiv.org/abs/1903.12136
