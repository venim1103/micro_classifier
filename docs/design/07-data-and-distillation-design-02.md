### Native ToF Wall Computation Prerequisites (2026-11-10)

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


##### Bounded Native ToF Wall Intake (2026-11-10)

Separate private intake checks the closed actual wall-acquisition cache,
original native-cache/RNG/tick/delivery identities and a bounded typed trace:
four axis/side entries,64-element float arrays/masks and scalar native words.
Two existing read-only native intakes surround a detached canonical-word copy.
Closing checks compare original native/ray/floor/final words, live profile/pose,
cache identities and staged output. Invalid/missing/changed evidence rejects,
without geometry replay, recorder read/retention, clock/RNG activity or hash.
Raw division/altitude/across infinities are diagnostic words, not finite hits;
unsupported layouts/NaNs reject. All eight flags remain false.

This establishes bounded point-in-time word correspondence, not an atomic or
perpetual freshness guarantee, independently correct wall arithmetic/masking/
geometry, complete coverage/error, physical clearance, clock/source/permission/
admission qualification or usable commands. Recorder retention and delivery
publication remain separate. See [wall intake controls and limits][native-tof-wall-intake-review].


##### Bounded Native ToF Wall-History Preflight (2026-11-10)

Private `_check_native_tof_wall_history` preflights at most eight copied wall
records against existing prevalidated native history. It requires strictly
ordered unique epoch/acquisition/delivery IDs, one native match, exact metadata/
false flags/common input/ray/floor/final words and four typed axis/side entries.
Fixed64 array/mask lengths and builtin types are checked before canonical
binary64 hex decoding; strings are at most32 characters, overflow/NaN/unsupported
range words reject. Scalar wall/position words match the native profile/pose;
variable intermediate words remain diagnostics, not accepted arithmetic.

This is a prehash layout gate, not recorder retention or delivery publication.
It uses no native intake, geometry/replay, recorder read, clock/RNG or hash.
All eight flags remain false; no numerical/geometric/coverage/error/physical/
source/clock/permission/admission qualification or usable command follows.
See [wall-history controls and limits][native-tof-wall-history-review].


##### Bounded Native ToF Wall Recorder Retention (2026-11-10)

Separate `record_native_tof_source(include_wall=True)` retains detached wall
words under the original epoch/acquisition/delivery IDs. Typed preflight,
including canonical common ray/floor/final words, precedes structured history
hashing. Equal repeats deduplicate; changed repeats reject. Wall records trim
only against the existing eight-entry native window; missing capture stays a
gap. Closing wall/selection/timing probes precede their comparisons, followed
by live/staged typed history, owner/producer/cache and wall-history identity
checks before publication. Timing and selection can coexist. Default retention
does not consume the optional live wall cache or replay geometry/read clocks.

All eight flags stay false. This retains bounded diagnostic words, not delivery
publication, independently correct arithmetic/masking/geometry, complete coverage,
uniform error bounds, physical clearance, clock/source/permission/admission
qualification or usable commands. See [retention controls and limits][native-tof-wall-retention-review].


##### Native ToF Wall Delivered/Pending Correspondence (2026-11-10)

Optional `snapshot_native_tof_delivery(include_wall=True)` publishes detached
wall records for the matched delivered source and, when requested, each pending
source. All three epoch/acquisition/delivery IDs must match uniquely. Typed
canonical history checks precede ownership/payload hashes. Closing native/frame,
timing, arithmetic, selection, wall and queue probes precede outgoing comparisons;
live histories are preflighted again after the last probe. Identity/content or
output changes and missing/mispaired records yield unknown with no partial
source/frame/companion payload. Default snapshots do not consume wall history.

No wall intake, geometry recapture, recorder read/retention, RNG or clock is
performed. Held delivery is not a new acquisition. All eight flags remain false;
this is bounded diagnostic correspondence, not independent arithmetic/masking/
geometry/coverage/error/physical correctness, clock/source/permission/admission
qualification or usable commands. See [wall delivery controls and limits][native-tof-wall-delivery-review].


##### Native ToF Wall Offset Word Residuals (2026-11-10)

Private `_native_tof_wall_offset_residuals` takes four declared canonical
wall/position/observed-numerator word triples. Guarded exact rational subtraction
reports the supplied-operand difference and signed observed-minus-exact residual,
preserving original words including signed zero. Finite operands are required;
nonfinite observed offsets retain the exact difference but leave the residual
unknown. Shape/type/length/canonicality and the existing4096-bit rational cap
are checked. The fixed four-entry path uses at most12 value conversions/eight
guarded operations, without source intake, replay, hashing or RNG/clock reads.

All eight flags stay false. Per-word residuals are not source correspondence,
correct-rounding certification, uniform error allowance, wall-division/masking/
geometry/coverage/physical proof or permission/admission. See [offset controls and limits][native-tof-wall-offset-review].


##### Native ToF Wall Division Word Residuals (2026-11-10)

Private `_native_tof_wall_division_residuals` takes four supplied numerator
words,192 ray-component words and four64-word raw distance arrays. For each
declared wall/ray axis, finite operands yield an exact rational quotient; finite
observations yield a separate signed observed-minus-quotient residual. Signed
input words are preserved. Zero directions require initialized+inf and are not
divisions. Nonfinite numerators/results remain unknown rather than finite
residuals.452 canonical words<=32 characters,256 entries and existing4096-bit
rational guards bound the path to at most768 value conversions/512 operations.

No source intake, replay, hashing or RNG/clock occurs. All eight flags stay false;
this isolates division from subtraction but does not bind source ownership,
certify correct rounding, adopt a combined/uniform error allowance or establish
masking/geometry/coverage/physical/permission/admission. See [division controls and limits][native-tof-wall-division-review].


##### Matched Native ToF Wall Arithmetic Diagnostics (2026-11-10)

Separate `snapshot_native_tof_delivery(include_wall_residuals=True)` requires
`include_wall=True` and composes the existing offset/division helpers from each
matched delivered/pending wall record. Both diagnostics retain original epoch/
acquisition/delivery IDs; subtraction and division residuals remain distinct.
All closing arithmetic/companion/queue probes precede outgoing comparisons and
typed live-history preflight. Missing/changed evidence yields unknown without
partial source/frame/companion data. Default snapshots skip these diagnostics.

No source intake, replay, recorder read/retention, RNG or clocks are added.
Existing four-wall/64-ray/canonical-word/rational caps remain. All eight flags
stay false: point-in-time correspondence and per-word arithmetic do not certify
correct rounding, adopt a combined/uniform error allowance or establish full
altitude/across/masking/geometry/coverage/physical/source/clock/permission/
admission qualification. See [matched arithmetic controls and limits][native-tof-wall-arithmetic-review].


##### Native ToF Wall Projection Expression Residuals (2026-11-10)

Private `_native_tof_wall_projection_residuals` compares supplied altitude/across
results with the exact unrounded base+distance*direction expression. Nonfinite
raw distance selects the native zero fallback; original raw/effective/base/ray/
observed words and branch identity are retained. Finite observed results get
signed discrepancies; nonfinite results leave residual unknown. Four walls/
64 rays bound963 canonical words,256 paired entries,1283 conversions and1536
guarded operations under the existing4096-bit rational cap. No source intake,
replay, recorder read/retention, hashing or RNG/clock occurs.

Intermediate products are not captured: these are combined-expression residuals,
not isolated multiply/add rounding results or an FMA claim. All eight flags stay
false; no accepted uniform allowance, masking/geometry/coverage/physical/source/
clock/permission/admission or usable command follows. See [projection controls and limits][native-tof-wall-projection-review].


##### Matched Native ToF Wall Projection Diagnostics (2026-11-10)

Separate `include_wall_projection_residuals=True` on the delivery snapshot
requires matched wall publication. It attaches projection diagnostics to original
epoch/acquisition/delivery IDs for delivered and optional pending records, alone
or alongside offset/division and timing/selection/arithmetic companions. Closing
probes complete before live-history/output checks; missing/changed evidence
yields unknown without partial data. Default skips projection work. No source
intake/replay, recorder read/retention, RNG or clocks are added.

The original arithmetic integration controls retain their original resource
caps; projection cases have separately bounded added work. All eight flags stay
false. Product words remain uncaptured; matched combined-expression residuals do
not certify primitive roundoff, FMA, uniform error, masking/geometry/coverage/
physical/source/clock/permission/admission. See [matched projection controls and limits][native-tof-wall-projection-match-review].


##### Native ToF Wall Mask/Candidate Word Correspondence (2026-11-10)

Private `_native_tof_wall_mask_candidate_diagnostics` reports whether stored hit
bits match five comparisons on supplied distance/altitude/across and finite
limit words. Candidate-copy checks separately use the observed hit bit, not the
recomputed bit, distinguishing mask discrepancies from selection discrepancies.
Original words and signed-zero differences are retained. Fixed four-wall/64-ray
input bounds1027 canonical words/256 builtin bools and256 records/1280 predicates;
no rational arithmetic, source intake, replay, hashing or RNG/clock occurs.

Mismatch reporting does not accept altered words. Native comparisons can yield
`hit=True` with an infinite candidate; matching this is not a finite intersection
or independently correct geometry. All eight flags stay false; no physical-limit/
coverage/numerical/source/clock/permission/admission qualification follows.
See [mask/candidate controls and limits][native-tof-wall-mask-candidate-review].


##### Native ToF Wall Minimum Word Correspondence (2026-11-10)

Private `_native_tof_wall_minimum_diagnostics` checks each wall result against
its supplied candidate and observed predecessor (floor first, then the previous
observed wall minimum). Strict selection and identical input words support exact
word checks. Equal-value/different-word ties remain unresolved; incorrect numeric
values still mismatch. Separate value/word/unresolved counts preserve signed-zero
distinctions without adopting host tie semantics or reconstructing predecessors.
Four walls/64 rays bound576 canonical words/256 records/1280 comparison checks;
no rational arithmetic, source intake, replay, hashing or RNG/clock occurs.

All eight flags stay false. Per-operation word correspondence is not final
cylinder/scene coverage, correct geometry, uniform error, physical/source/clock/
permission/admission qualification. See [minimum controls and limits][native-tof-wall-minimum-review].


##### Matched Native ToF Wall Selection Diagnostics (2026-11-10)

Private recorder delivery snapshots accept separate literal-bool
`include_wall_selection_diagnostics=False`, requiring `include_wall=True`.
Each matched delivered/pending record's original epoch/acquisition/delivery IDs
join separate `mask_candidate` and `minimum` diagnostics. Default skips both;
selection-only composition requires no offset/division/projection arithmetic.
Equal-value/different-word minimum ties remain unresolved, not host tie claims.

Initial/closing probes precede typed live-history and outgoing comparisons.
Late mutations reject the whole snapshot without partial source/frame/companion
payload; successful copies are detached. Fixed existing history/word/work caps
remain; neither matching words nor hashes qualify geometry, finite intersections,
coverage, physical/native error, clocks, permission or admission. Eight flags
remain false. See [matched selection controls and limits][native-tof-wall-selection-match-review].


### Native ToF Cylinder Computation Prerequisites (2026-11-10)

Optional cold `tof_ranges(..., cylinder_source={})` retains actual horizontal
squared norms and each cylinder's offset, projection, discriminant and root
arrays from the existing evaluation. Empty builtin dictionary must be separate
from native/selection/wall outputs; actual finite mounted source inputs and the
existing32-obstacle cap are checked before geometry. Detached inputs/rays,
post-wall minimum and final pre-noise arrays retain calculation context.
Default evaluation order and first-return words remain unchanged; no replay,
clock or RNG is introduced. Fresh-acquisition pairing is documented below;
recorder wiring remains separate work.

This describes the quadratic portion; side/top stages are documented below.
Matching raw words is not correct
intersections, geometry/coverage, primitive or uniform error, physical/source/
clock/native/permission/admission qualification. All eight flags remain false.
See [quadratic trace controls and limits][native-tof-cylinder-trace-review].


#### Actual Cylinder Side/Top Calculation Stages (2026-11-10)

The same cold trace additionally copies each near/far side's original division
numerator/result, altitude, hit mask, candidate and predecessor/result minimum.
Top-cap records retain actual offset/division, relative vector, squared radial
sum/radius, hit/candidate and minima. Named scalar/array intermediates preserve
the original expression order. The per-cylinder side tuple then top record
links the actual post-wall result to final pre-noise ranges, without replay or
host-specific word-tie adoption. All arrays/inputs are detached; default output
words and existing32-obstacle/64-ray/preflight limits remain unchanged.

Recorder retention, acquisition pairing and closed intake
are documented below. Observed-stage correspondence is not geometry, coverage, primitive or
uniform error, physical/source/clock/native/permission/admission qualification;
all eight flags remain false. See [side/top controls and limits][native-tof-cylinder-stages-review].


#### Actual Fresh Cylinder Acquisition Pairing (2026-11-10)

`RoverEnv.step(capture_native_tof_cylinder=False)` is a separate literal-bool
opt-in requiring native source capture and mounted rays. Preflight precedes
mutation and clocks. Only fresh sampling forwards the original trace dict,
pairing native cache/RNG identities and acquisition/delivery ticks; held/default/
reset clears it and rejected preflight preserves previous caches. The old default
forwarding path is unchanged. Wall/selection/timing can accompany the same sample
without extra geometry, RNG or clock reads. Delivery correspondence is documented
below; nominal IDs/timing and matching words do not qualify source,
geometry, coverage, numerical/physical error, clocks, permission or admission.
Eight flags remain false. See [acquisition controls and limits][native-tof-cylinder-acquisition-review].


#### Bounded Closed Cylinder Intake (2026-11-10)

`_sample_simulator_native_tof_cylinder_source` requires exact builtin acquisition/
trace/entry/stage dictionaries and tuple counts, <=32 paired obstacle entries,
two ordered sides and one cap each, exact float64/bool array shapes and original
native/RNG identities. Before any native intake it rejects malformed layouts,
nonliteral flags, NaNs, nonfinite declared operands/rays and negative-infinite
candidate/range words. Two native intakes bracket canonical detached word copies;
closing checks cover cache/native/RNG identity, template/pose/input/output words,
copied content, ticks and declared centre/radius/top operands. Per metadata pass
<=45696 float words plus6144 mask booleans; no new arithmetic/replay/hash/clock/
RNG/recorder read. This is diagnostic ownership/copy validation, not arithmetic,
geometry, coverage, source, clock, permission or admission qualification. All eight
flags false. Delivery correspondence is documented below. See
[actual controls and gate][native-tof-cylinder-intake-review].


#### Typed Cylinder History Prehash Guard (2026-11-10)

`_check_native_tof_cylinder_history` checks exact builtin history/source lists
of at most eight entries, strictly increasing ticks and unique epoch/tick/delivery
pairing against already validated native history. Closed copied trace shapes
allow at most32 cylinders each with two ordered sides and one cap, fixed64-ray
flat tuples and literal bool masks/flags. Declared centre/radius/top, inputs,
rays and final ranges must match native words. Other words are canonical hex,
at most32 characters, non-NaN; declared operands/rays are finite and candidate/
range slots exclude negative infinity. At max8x32, <=365568 float-word parses
and49152 mask booleans. The guard does not intake/copy/hash/read/retain/replay or
use clocks/RNG, and does not qualify source/geometry/coverage/error/clock/
permission/admission. All eight flags false, including when it returns `None`.
Recorder wiring is documented below. See [controls and limits][native-tof-cylinder-history-review].


#### Explicit Cylinder Recorder Retention (2026-11-10)

`record_native_tof_source(include_cylinder=False)` is a separate literal-bool
opt-in, retaining detached closed-intake words with original epoch/tick/delivery
IDs. Typed guards precede history hashing; staged cylinder entries are limited
to the native history's at most eight retained ticks. Equal repeated words are
idempotent, changed repeats reject. Closing checks cover original cache/history
identities and entry/native/producer/owner words before any staged commit.
The default skips cold cylinder intake and all companions can coexist without
additional geometry, recorder read or clock. At most six typed-cylinder guards
per successful retention; each has the existing8x32 word/mask budgets. Delivery
publication is documented below. This does not certify source/geometry/coverage/
roundoff/uniform error/clocks/one-use execution/permission/admission; eight flags
remain false. See [actual checks, failure and limits][native-tof-cylinder-retention-review].


#### Delivered and Pending Cylinder Correspondence (2026-11-10)

`snapshot_native_tof_delivery(include_cylinder=False)` is a separate literal-bool
opt-in. After typed preflight, one detached cylinder record matches each delivered/
pending native epoch/tick/delivery pair; copied records are typed before hashing.
Closing probes and guards check original history identity, retained/native/output
words, pending queue, current frame and producer/owner context before publication.
Outputs are `cylinder` and optional `pending_cylinder`; unknown omits source,
frame and all companion payloads. Default skips cylinder history, with wall/
selection/timing/direction-norm companions available independently. At most eight
typed-cylinder guards per successful snapshot, each with existing8x32 budgets;
no acquisition intake, geometry replay, recorder read or new clock/RNG activity.
Matching words do not resolve unequal-word value ties or prove source, geometry,
coverage, roundoff, physical error, clock, one-use execution, permission or
admission. Eight flags remain false. See [actual controls and gate][native-tof-cylinder-delivery-review].


#### Supplied-Word Cylinder Offset Discrepancies (2026-11-10)

`_native_tof_cylinder_offset_residuals` reports exact supplied position-minus-centre
ratios and observed-minus-exact residuals for both axes of <=32 cylinders. Builtin
canonical word preflight <=130 strings,32 characters each; position/centre are
finite and non-NaN observations may be infinite (unknown residual, exact operand
difference retained). Existing4096-bit rational ceiling, <=192 value calls and128
binary operations,64 entries; no source/recorder read, hash, replay, clock or RNG.
Signed-zero words retained without inferring tie semantics. Report remains
standalone: no matched-source composition, isolated primitive/uniform error bound,
geometry, coverage, source, numerical/physical/clock/permission/admission proof.
Eight flags false. See [actual controls and gate][native-tof-cylinder-offset-review].


### Synthetic Evaluation Tooling (2026-10-16)

The user approved [CPU evaluation tooling][teacher-evaluation] with synthetic
fixtures only. This prepares part of Task 9; it does not approve task datasets,
live teacher labels, baseline fitting, student training or locked task splits.
No deployment/acceptance threshold or physical safety rule was changed.

`evaluate_synthetic` requires explicit ordered option identities and integer
label indices, rejecting malformed/nonfinite probabilities rather than
renormalizing them. Reports identify their synthetic scope and input/source
hashes. Metric conventions are explicit:

- Macro-F1 includes every declared option, assigning undefined class F1 zero;
  absent-class recall/precision are null where their denominators vanish.
- NLL uses natural logarithms with no epsilon clipping. A zero target
  probability yields JSON null plus an explicit infinite-NLL flag/count.
- Brier is mean per-example sum of squared probability errors over options,
  not additionally divided by option count.
- ECE uses configurable equal-width bins of maximum class probability,
  left-closed/right-open except the final bin includes one. Explicit edge
  search avoids decimal multiplication rounding into the preceding bin.
- Argmax ties choose the first declared option. Coverage/risk curves accept
  all confidence ties together with maximum probability at least the threshold;
  zero-coverage accuracy/risk are null. This is not the wire Jev-confidence
  formula and does not select a deployment rejection threshold.

`validate_synthetic_splits` requires five distinct nonempty purposes: training,
development, quantization calibration, confidence calibration and test. Sample
IDs are globally unique; declared input hashes and source/episode/template
groups cannot cross purposes. Groups may repeat within a purpose. An optional
expected canonical manifest SHA-256 detects changes. These identifiers/hashes
are supplied fixture metadata, not verified files, approved grouping policy,
production schema or a real test lock; output says `locked_task_splits=false`.
It does not create split assignments, fit models or operate on episode logs.

`python -m teacher.evaluation --output ...` runs built-in toy fixtures only,
writing a new report exclusively. The [recorded report][synthetic-evaluation-report]
checks a four-row, three-option arithmetic fixture (accuracy 0.75, macro-F1
7/9, Brier 0.395, two-bin ECE 0.05) and five separate one-row placeholder
partitions. These values demonstrate arithmetic, **not robot task quality**.
Report SHA-256:
`a4436830a3b687d36fc7ca4130da87bda72c65d6460e4d2859b24c7ac73a94bf`.

Verification: 36 [focused tests][evaluation-tests], 260 repository passes plus
the known transformer expected failure; Ruff lint/changed-file format and
editor diagnostics pass. No real teacher call, task dataset, model fit,
training, dependency change, download or hardware action occurred. Task 9's
baselines/evaluation remain blocked on reviewed data and genuinely locked splits.

### Training Baselines and Loss

Train a supervised-only student and an otherwise comparable distilled student.
Human-reviewed labels take precedence over teacher mistakes. Teacher agreement
is a useful diagnostic, not the primary definition of correctness.

Start with temperature 1 and combine supervised task loss with distribution
matching. For categorical outputs, the distillation term is
KL(teacher distribution || student distribution). Use Bernoulli/BCE-style
objectives for binary or independent-label outputs instead of categorical KL.

If temperature-based distillation is later used, soften both distributions
consistently and use the appropriate temperature scaling of the loss. Do not
divide only student logits while leaving teacher probabilities unchanged.
The [PyTorch tutorial][pytorch-distillation] provides a reference implementation
for the standard formulation. A reasonable second experiment is the
[Crivo-32M][crivo-32m] recipe:
L = 0.5·[CE(gold) + 0.5·Brier(gold)] + 0.5·τ²·KL(teacher_τ ‖ student_τ), with
τ = 2 for three or more options, τ = 1 for binary questions, and gold-only loss
where the teacher is weak.

Use evaluation mode and no gradient tracking for the teacher. Cache labels so
student experiments do not repeatedly depend on expensive teacher inference.
Begin without hidden-state matching; if it demonstrably helps later, include
the projection parameters in the optimizer and any distributed training state.

### Closed-Loop Data and Simulation

#### Hardware-Free Trainer Environment (2026-10-15)

The user explicitly confirmed simulation-first development without hardware.
[sim/rover.py](../../sim/rover.py) implements the accepted minimal Python/NumPy
planar rover environment, with a SciPy Dijkstra scripted reference. Its
`reset(seed=...)` returns an observation and diagnostic info; `step` takes
desired forward speed and yaw rate, returning observation, scalar reward,
termination, time-limit truncation and info. Observation tensors include
ego-state and body-frame goal, delayed noisy ToF with validity and age, and
eight masked history ticks. True pose and world geometry are not model inputs.

User-approved, configurable **simulation-only assumptions**, not measured
physical specifications: 20 Hz decisions, nominal 15 Hz ToF acquisition
(updated 2026-10-20 below), 0.18 m circular rover radius, 0.6 m/s forward
speed limit, 1 m/s² acceleration/deceleration, 1.5 rad/s turn limit; 45-degree
horizontal/vertical angular ToF grid, 4 m range, 0.02 m independent Gaussian noise, 2% independent
zone dropout, two-tick delivery latency, eight history ticks, and 400-tick
episode limit. The initial model repeated planar rays vertically; the current
fictional floor/cylinder profile is specified below. Neither is VL53L8CX
emulation. Constant-twist motion is checked
against swept inflated obstacles, including a conservative curved-path margin.
Invalid commands are rejected, bounded commands are reported, and collision
terminates the simulation instead of permitting tunneling through obstacles.

#### Sensor Acquisition Cadence (2026-10-20)

The approved F21 direction now has a first implemented correction: `Config`
defaults to `tof_rate_hz=15.0`, distinct from the unchanged `dt=0.05` decision
period. The scheduler uses rational decimal periods to avoid cumulative phase
drift, captures at the first decision tick at/after a nominal deadline and
delivers queued frames every tick, even without a new capture. A held frame
retains its values, mask and capture tick; its reported age grows and no extra
noise/dropout RNG draws occur. Histories still advance every decision tick.

At defaults, capture ticks begin 0, 2, 3, 4, 6, 7, 8; with two-tick latency,
delivered sample ticks begin null, null, 0, 0, 2, 3, 4, 4, 6. Warm ages are
0.10 or 0.15 s. This is a nominal cadence quantized to decision ticks:
capture intervals can be 0.05 or 0.10 s, not a physical minimum inter-frame
period of 1/15 s. No continuous-time exposure, sub-tick pose interpolation,
clock uncertainty or hardware acquisition timing is qualified. Slower decision
loops collapse multiple deadlines to one current capture, never catch-up bursts.

Explicit rates must be in (0,15] Hz. `None` denotes legacy per-tick acquisition;
stored-source readers use `Config.from_record`, mapping an absent rate to that
legacy behavior. New metadata includes the rate. The provenance validator accepts
exact complete old/new config field sets, not arbitrary missing/unknown fields.
The CLI's partial `--config` overrides use current defaults; use an explicit
null rate to replay old cadence. Historical logs/reports remain unchanged and
retain their original exporter hashes. Source-keyed request identities change
under the existing cache scheme; no historical packet/cache/report is migrated
or requalified by this code change.

Eighteen new synthetic cases cover captures/delivery/ages, held RNG, varied
decision periods, reset determinism, invalid rates and legacy request/provenance
readers. All 1,319 repository tests pass plus the known transformer xfail; lint,
changed-file format, editor diagnostics and existing native/Arm gates pass.
REVIEW.md §73 records the transient unrelated cleanup-test failure and rerun.
No study episode, teacher/model run, labels/data or hardware action occurred.
At that checkpoint the remaining geometry/error assumptions were unspecified;
the follow-up below records their adoption for synthetic implementation only.

#### Synthetic Geometry and Ego Errors (2026-10-20)

The user approved this fictional configurable profile, not measured hardware:
the sensor is centered horizontally at `tof_mount_height=0.15` m above a flat
z=0 floor with `tof_mount_pitch=0` rad, floor-supported obstacle cylinders
of `obstacle_height=0.5` m and arena walls of `wall_height=1.0` m. Optional
`Scenario.obstacle_heights` supplies one positive height per obstacle; an empty
tuple uses the Config default. Low/tall artificial checks use 0.05/1.0 m.
Rover collision/dynamics stay planar: any obstacle footprint remains collidable,
regardless of its sensor-visible height; no body height/ground clearance,
overhang, terrain, step-climbing or 3-D motion is modeled.

`tof_directions` uses eight uniformly spaced azimuths and elevations spanning
the configured 45-degree field in each dimension, upper-to-lower rows and
left-to-right columns. Positive pitch points downward. These are ideal angular
point rays, not measured zone footprints, device intrinsics or integrated
multitarget histograms. Each ray selects the nearest nonnegative floor, finite
wall face, cylinder side or top-cap intersection. Missing surfaces and ranges
at/above the 4 m ceiling are invalid/zero, not valid clear space. Existing
Gaussian range noise and dropout apply only after determining surface support;
noise-clipped supported returns may still saturate. Reflectance, sunlight,
multipath, material response and device return-status codes remain unmodeled.

Synthetic odometry is opt-in: `odometry_position_error=0` m,
`odometry_heading_error=0` rad and `odometry_latency_ticks=0` by default.
Nonzero position error samples independent uniform points in a disk of the
declared radius; heading error is independent uniform on plus/minus the declared
angle. The approved test profile uses 0.02 m and 2 degrees, with one-tick delay.
These are artificial injected errors, not physical bounds, a drift/bias model,
measured calibration or an adopted Gaussian risk budget. Errors affect the
body-frame goal derived from estimated pose; speed/yaw-rate retain their ideal
values from the same queued sample. A separate seeded RNG leaves world motion,
reward/collision results and ToF faults unchanged. Reads consume no RNG.

Delay holds the initialized tick-0 estimate during startup, then delivers queued
ego samples; no extrapolation or temporal compensation occurs. With nonzero
delay, observations add paired `ego_sample_tick`/`ego_age_s` metadata. Histories
record the delivered values each decision tick; array shapes remain unchanged.
The wire exporter puts the same age on velocity, angular velocity and goal in
the existing fields. It rejects inconsistent/nonfinite/unrepresentable ages
instead of marking old values fresh. Battery/fault health stays unknown.
Full render/review checks preserve exactly these two optional input fields,
still reject privileged fields, and do not create labels or promote scope.

Stored-source compatibility is explicit: `Config.from_record` maps an absent
mounting-height field to `None` (legacy planar rays), and an absent rate to
`None` (legacy per-tick capture). Missing error fields retain ideal defaults.
Exact complete pre-cadence, cadence, geometry-only and current metadata schemas
are accepted, not arbitrary partial declarations. CLI partial config overrides
use current defaults; replaying original sensor behavior explicitly requires
null mounting height and null rate. Historical logs/reports/goldens and the
diagnostic catalogue are untouched; source-keyed cache identities change normally.

Shared-model diagnostics now trace matching 8x8 ranges for the synthetic profile
(eight repeated rays for legacy mode), with explicit geometry tags and deep
copies. Registration diagnostic arrays cover 64 rays for the new profile, eight
for legacy mode. These references share simulator geometry, not independent
metrology. No prior diagnostic study/report was regenerated.

Geometry commit `1293c4e` passed 1,350 tests plus the known transformer xfail;
odometry commit `059cff7` passes 1,382 plus that xfail. The 63 added cases include
analytic floor/side/top hits, low/tall visibility, yaw/pitch, exact legacy RNG
replay, bounded errors, physics/sensor independence, reset, wire-age rejection
and three historical reader eras. Lint, changed-file format, editor diagnostics,
native sanitizers and hard-float Arm checks pass. Only ephemeral test fixtures
were generated, not study episodes, labels/datasets/splits or model runs.

At the geometry checkpoint, collection and heuristic settings remained unapproved.
The following bounded diagnostic approval does not qualify the sensor or rules.

#### Floor-Aware Heuristic Wire Baseline (2026-10-20)

The user approved a host-only observation-based heuristic and wire-loop tests,
a configurable 0.03 m floor band/default `(latency_ticks + 1) * dt` age limit
(0.15 s), and eight fresh diagnostic episodes: four existing scenes times seeds
20261020/20261021, at most 400 ticks each. These are diagnostic settings, not
physical error/safety bounds, a Gaussian risk convention or changed targets.
[The heuristic][floor-rules] is implemented in `05a94f8`; legacy proxy formulas
remain unchanged. It uses no true pose, world geometry, actions or target labels.

Hits are projected to height; supported above-band hits give horizontal column
minima. Each column must have a positive unsaturated supported hit. Columns with
support but no above-band obstacle get max-range working clearance: an optimistic
heuristic, not evidence that missing/occluded rays or swept volume are clear.
Below-floor outliers, unsupported geometry, stale/absent or inconsistent inputs
reject. No motion compensation is performed. Sector/bearing and momentum speed
heuristics differ from the oracle's curved-sweep and at-rest semantics. Complete
catalogue-1/model-0 one-hot answers and Jev statistics are not calibrated confidence;
`OK` admits heuristic inputs, not geometric correctness or physical safety.

The Python loop encodes/decodes state and decision frames. The diagnostic host
checks status, catalogue, sequence/timestamp echo and ego ages; rejection,
caller-declared absence, corruption or mismatch commands simulated braking.
This is not linked C firmware, a real transport timeout or a new deployed
fail-safe. Zero decision latency is an unmeasured placeholder, not a benchmark.

The approved run used normal Config and the fixed baseline with no tuning.
Oracle comparisons used private current truth after choosing actions, never
controller inputs or task labels. Logs stay ignored/quarantined. [The report][floor-rules-report]
records config/settings, source/log hashes, statuses and private aggregates:

| Scene | Seed 20261020 | Seed 20261021 | Clear / Reference-Blocked Events (By Seed) |
| --- | --- | --- | --- |
| clear | success, 138 ticks | success, 138 ticks | 0 / 0 |
| obstacle | timeout, 400 ticks | timeout, 400 ticks | 5 / 4 |
| corridor | success, 138 ticks | success, 138 ticks | 0 / 0 |
| slalom | collision, 41 ticks | collision, 40 ticks | 8 / 8 |

Total: 1,433 ticks, four successes, two collisions, two timeouts and 25 false-clear
reference events. These are correlated diagnostics, not independent error rates
or locked evaluation evidence. Saved-evidence audit checked all eight hashes,
2,866 wire frames, identities, ages, summaries and independently accumulated
reference aggregates without baseline/controller calls or more collection.
The audit reused the geometric oracle, not independently measured physical truth.

Twenty-four new tests cover floor handling, rejection/support, momentum,
privileged-field independence, host braking, settings and output preflight.
Full gate: 1,406 passed plus the known transformer xfail; lint, changed-file
format, editor diagnostics, native sanitizers and hard-float Arm checks pass.
No historical log/report/golden was rewritten. REVIEW.md §75 records the result.
This failed heuristic remains diagnostic-only. F21/M2 need reviewed handling of
missing/occluded evidence, representative scenes and qualified rules. The eight-run
authorization is exhausted; no tuning or second batch followed. No task labels,
cohort/split acceptance, training, dependencies, ST/licence or hardware approval.

#### Opt-In Motion Registration (2026-10-21)

Following read-only inspection of the frozen failures, the user approved an
opt-in registration candidate, synthetic tests and existing-log diagnostics
only. `RuleSettings(register_motion=True)` in `ebdb9d8` uses the visible ego
history convention: sample t contains the applied speed/yaw rate over the
interval ending at t. It composes planar motion from acquisition to current
tick, transforms supported hits into the current body frame and rebins nearest
column bearings within the configured view. The floor band, age gate, original
default, target definitions and optimistic floor-only working clearance remain
unchanged. This is host Python diagnostic logic, not an embedded runtime.

Registration requires complete finite synchronous history covering capture
through the current sample, matching current ego data and valid simulated
motion. Missing/malformed/gapped history, inconsistent timing, delayed odometry
without per-history acquisition times, or unsupported current columns reject.
This neither fills missing space nor proves clearance of a swept rover body.
It assumes the simulator's interval-motion convention, not measured real
odometry accuracy, static-scene qualification or a physical error budget.

On all 1,433 frozen observations, the default path reproduces the original
decision frames byte-for-byte. The opt-in candidate admits 220 frames, rejects
1,213 and has four false-clear/six false-blocked private reference comparisons.
Three of the old 25 false-clears become blocked, 20 reject and two stay clear;
two additional false-clears occur. These selected replay counts are not a
comparable task error rate or a candidate closed-loop success/collision result.
No new episodes or tuning followed. The original report/logs remain unchanged.
Twenty-six synthetic cases and the full gate pass: 1,432 tests plus the known
transformer xfail, lint/format/editor/native sanitizer/hard-float Arm checks.
REVIEW.md §76 records provenance and limitations. Missing/occluded-space policy,
swept-volume evidence, representative scenes and physical qualification still
block F21/M2; no collection, labels, training or hardware scope was opened.

#### Coverage Requirements and Observability (2026-10-21)

`a673056` supplies two mirrored artificial counterexamples using the current
floor/cylinder model, 45-degree field, nominal 15 Hz capture, two-tick delivery
and complete eight-tick history. Noise/dropout are zero and ego state is ideal.
At current pose (2,2,0), speed 0.6 m/s and turn rate +/-1.5 rad/s, a cylinder
at (2.3, 2+/-0.47) with radius 0.3 m/default height 0.5 m remains unseen in
every delivered history frame. Current/history ego, ToF values/masks/ages and
the entire rendered host/module input are identical to the world without it,
but the adopted curved-braking reference answers blocked versus clear.
The constructed history is at tick 23, after cruise speed can be reached;
retained historical poses do not overlap the obstacle. These are fixtures,
not validated reset-to-current rollouts, new episodes, labels or representative
task-frequency measurements.

Consequently, neither thresholds, registration nor an input-only learner can
always identify the correct world from this input. A probabilistic answer may
represent ambiguity but cannot create the missing evidence; no prior or calibrated
risk is established here. This does not prove all inputs ambiguous or all sensing
designs inadequate. The earlier narrow-ray examples and these normal-cylinder
examples must remain distinct from a universal impossibility claim.

The user selected **coverage-first design requirements** before another runtime
baseline. Existing geometric targets, input/wire shapes and defaults remain in
force. No wider FoV, extra sensor, obstacle-size bound, scan/mapper, longer
history or physical operating restriction is selected by this decision.

| Coverage Requirement | Evidence a Concrete Candidate Must Supply |
| --- | --- |
| Full motion footprint | Account for the circular body's reaction/braking sweep under each claimed straight/turning maneuver, including its side extent, not just forward sector minima or center rays. |
| Spatial support | Explain which occupied and free regions follow from actual observations; eight supported bearings or floor-only returns do not certify the space between/behind rays. State any minimum object size/shape/height assumptions explicitly for review. |
| Vertical compatibility | Show how the chosen mounting/view and return model observe permitted low/tall obstacles and separate floor support from obstacle/free-space evidence. Do not silently exempt objects using the 0.03 m diagnostic floor band. |
| Time and motion | Identify acquisition times, delivery/ego ages, transform uncertainty and retention for every observation used. Scanning or accumulating views must account for body motion and changing/occluded evidence, not assume old views are current. |
| Return/error qualification | Treat missing, clipped, occluded, unsupported or unqualified returns as unknown. Define sensor status/material/scene and error evidence before using observations as clearance support; sigma is not a hard bound and the Gaussian risk convention stays unaccepted. |
| Retained information and contract | State what extra observations or retained state make the aliased worlds distinguishable and where they live. Any sensor, history/map, tensor, wire/profile or timing-contract change needs separate approval and versioning review. |

For a proposed candidate, first demonstrate the added information on the mirrored
aliases without privileged geometry entering the decision input. Then test other
blind regions and the declared scene/obstacle envelope; fixing these two pairs
is necessary evidence, not general coverage qualification. A proposed admission
criterion is that unresolved allowed worlds intersecting the claimed sweep stay
unknown/rejected, rather than inheriting max-range clearance. This criterion is
for evidence-policy review, not a runtime change or a newly adopted quantitative
risk/safety threshold. Always rejecting may preserve uncertainty, but cannot
alone satisfy M2's useful task-quality requirement.

Next decision: a concrete sensing/retention candidate plus declared domain,
time/error evidence and qualification method. Only then consider a separate
implementation or collection authorization. No devices were chosen or purchased,
no numerical hardware coverage/safety limits frozen, no data accepted and no
additional run authorized. Two new regressions pass with the full 1,434-test
gate plus the known transformer xfail. REVIEW.md §77 records the decision.

#### C1: Simultaneous Multi-View Coverage Candidate (Draft, 2026-10-21)

**Proposal, not adoption or implementation.** To make §77's coverage-first
direction concrete, first evaluate an artificial eight-view ring with bounded
pose/time-tagged retention. Do not select or purchase eight physical devices.
The purpose is to expose what information is still missing before selecting
hardware or proposing qualified rules. Existing simulator defaults, observation
schemas, UART bytes, geometric targets and both diagnostic heuristics stay intact.

| Candidate Component | Proposed Artificial Configuration |
| --- | --- |
| View geometry | Eight copies of the existing 8x8 point-ray grid, centered at body yaw offsets 0, 45, 90, 135, 180, 225, 270 and 315 degrees. Each uses the existing 45-degree local angular field, centered horizontally at height 0.15 m, with 22.5-degree downward pitch. Coincident optical origins are a simplifying fixture, not a buildable mounting claim. |
| Coordinate convention | Apply the actual pitch/yaw rotation in `tof_directions`, not independent additions to azimuth and elevation. The nominal ring is not a proof of continuous angular support or of device zone footprints. |
| Timing | All eight views share an acquisition pose/tick in the first ideal calculation, nominal 15 Hz tick-quantized capture and two-tick delivery at 20 Hz decisions. This assumes synchronization; it is not measured bus/exposure timing. A sequential physical scan is a separate candidate, not implicitly equivalent. |
| Retention | At most eight decision snapshots, each retaining all eight views, masks, acquisition identity and associated pose/time evidence. Repeated held acquisitions do not create new viewpoints or independent samples. A longer history or persistent occupancy map is not part of this first proposal. |
| Evidence use | Keep ray endpoints, missing returns and any explicitly justified along-ray information separate. Unsupported volume stays unknown; do not give floor-only, masked, saturated, occluded or old regions max-range clearance. A hit is not automatically a blocked witness for the complete maneuver. |
| Initial domain | Static, floor-supported artificial cylinders and finite walls over the existing flat floor; first use exact poses and zero range noise/dropout. Check the existing 0.05/0.5/1 m height fixtures and normal-cylinder aliases. These are test conditions, not accepted minimum obstacle dimensions or a physical operating envelope. |
| Information boundary | A separate experimental module-side multi-view representation would be required; the present single 8x8 observation cannot carry the proposal. No tensor, renderer, cache identity, state/decision codec or profile version is changed by this draft. |

The downward tilt is a candidate for near-floor visibility, not a declared cure
for low obstacles. Finite vertical and horizontal rays can still miss slender
objects; nearer surfaces can occlude farther ones. Any usable negative/clear
claim must address those allowed objects and the swept body, not just distinguish
the two existing counterexamples. Until a scene/return/error envelope supports
such a claim, the proposed result for unsupported regions is unknown, not clear.
This remains an evidence-policy proposal, not a newly deployed rejection rule.

At the current maximum speed, age 0.15 s and decision period 0.05 s, the
reference's reaction time is 0.20 s, braking time 0.60 s and centerline path
length 0.30 m. Adding the 0.18 m body radius gives a conservative 0.48 m radial
enclosure of the swept body about its initial center. That is a useful geometric
check region, not a sensor range requirement: an obstacle outside it can extend
into it, and sensing/registration uncertainty is not included. The 0.80 s
reaction/braking horizon is not the input-history duration or a stale-data limit.
Do not extrapolate these figures to delayed ego estimates or physical braking.

For a transparent storage estimate, eight snapshots of 512 binary32 ranges use
16,384 bytes, plus 4,096 bytes for one-byte-per-ray masks and 256 bytes for one
u32 acquisition tick per view/snapshot: 20,736 bytes before ego/pose/error data,
mounting calibration, container/alignment overhead, workspace and copies.
This is eight times the range/mask payload of the current eight-slot single-view
arrays, not measured embedded RAM fit. A synchronized bundle's range/mask payload
is 2,560 bytes; at nominal 15 Hz it is 38,400 bytes/s before framing/status or
bus overhead. This is a representation calculation, not I2C/UART bandwidth,
device throughput or NPU feasibility evidence.

Alternatives remain visible rather than silently adopted: three forward/side
views are cheaper but leave a rear-side information boundary for turning sweeps;
rotating one view reduces simultaneous hardware but adds scan age, ego-motion
and moving-scene assumptions. A wider single imager may avoid inter-view timing
but needs its own near-field, angular-resolution, material and error evidence.
Longer history alone does not add views when the rover never observes a region.
The proposed default is the artificial simultaneous ring as a diagnostic
information study, not a hardware recommendation or a narrower target.

Read-only calculations using the existing ray/intersection functions now give
the following bounded results. Differences count binary32 range/mask entries,
not independent detections, calibrated confidence or task accuracy:

| Artificial Comparison | Original / Level Layout | C1 Tilted Ring |
| --- | --- | --- |
| Each mirrored normal-cylinder history from §77 | No differences in the original single view | 317 changed entries among 4,096 view/history entries, for each mirror |
| Radius 0.02 m, height 0.05 m cylinder at (2.21,2), current pose (2,2,0) | No differences with eight level views | Four changed entries among 512 current-view entries |
| Radius 0.005 m, height 0.5 m cylinder at (2.4,2), straight-moving constructed history | Not needed as a control for this C1 limit | No differences in all eight views/history slots, while the straight-braking reference changes from clear to blocked |

The delivered capture ticks in the eight history slots are
14, 15, 16, 16, 18, 19, 20, 20: six distinct acquisitions, not eight independent
views in time. The small-cylinder history uses the same tick/capture convention
as §77 but zero turn; no reset-to-current rollout was validated. The near-floor
comparison is a current-pose fixture only, not a delivered-history or closed-loop
result. All calculations use noiseless ideal geometry; no new source API, study
episode, artifact or task label was produced.

**Decision consequence:** C1 separates the original normal-cylinder aliases
but is insufficient for an unrestricted clearance claim under the current
positive-radius cylinder model. Do not promote it to a clear/blocked heuristic
or quietly exclude the 5 mm fixture. A minimum obstacle envelope or a qualified
volume-observation model would require an explicit product/evidence decision;
until then unresolved cases must remain unknown in any proposed evaluator.
The recommended next scope is a separate, opt-in synthetic visibility prototype
retaining both successes and misses, not deployment or a new closed-loop batch.
Approval must explicitly cover its experimental multi-view representation;
the present single-view observation and profile do not become multi-view by
reusing their identifiers. Any later approved prototype must enforce
per-view timing and error provenance, reject unsupported evidence, preserve
legacy defaults/bytes and disclose input/profile changes before integration.
No episodes, labels, model run, new dependency or hardware action follows from
preparing this candidate. Results and the precise next approval belong in
REVIEW.md rather than being presented as adopted architecture here.

#### C1 Synthetic Visibility Prototype (2026-10-21)

The user separately approved the synthetic prototype and experimental
representation only. `a3df1f5` adds `capture_synthetic_c1_views` and
`inspect_synthetic_c1_history` in [sim/diagnostics.py][c1-prototype-source].
Both require the literal `synthetic_test_only=True`. There is no controller,
dataset, wire or normal observation adapter, and no episode-running CLI.
This implements fixture tooling, not adoption of C1 as a sensor or rules baseline.

Captures use schema `micro-classifier/synthetic-c1-views/1`, eight fixed yaw
offsets and the proposed 22.5-degree pitch. They declare their complete Config,
eight acquisition ticks/poses and 8x8x8 binary32 ranges with boolean masks.
Only the declared ideal profile is supported: no range noise/dropout or ego
error/delay, fixed 45-degree local field and 0.15 m height, nominal 15 Hz capture,
20 Hz decision clock, two-tick delivery and eight-slot history. Stored ranges
must remain positive, finite and below the ceiling after binary32 conversion;
rounding to the ceiling invalidates and zeroes the corresponding sample.
World geometry and target answers are not included in the bundle.

Inspection accepts at most eight consecutive decision snapshots. It checks the
experimental identity and scope, exact configuration metadata, nominal capture
cadence, complete simultaneous view poses/ticks, delivery eligibility, ordered
acquisitions, unchanged repeated captures, strict range/mask consistency and
the latest age. `max_age_ticks=3` is an explicit artificial fixture assumption,
configurable from zero to eight, not an accepted hardware freshness rule.
Old snapshots do not extend this limit. Only the latest supported endpoints
are registered into the supplied reference body frame; this is not accumulated
free space, an occupancy map or a method for filling historical blind regions.

Success is tagged `registered_fixture` under declared exact static assumptions;
unsupported evidence stays `unknown` with no points. Both outcomes retain
`training_approved=False`, `real_input_qualified=False` and
`free_space_qualified=False`. These flags are declarations and guards, not
attestation that arbitrary caller-supplied poses or metadata are true. No
`clear`/`blocked` decision, label, calibrated confidence or qualified free-volume
claim is produced. Physical mounting, noise/errors, asynchronous scans,
moving scenes and actual clocks remain outside qualification.

Sixty-one bounded tests reproduce the normal mirrors, near-floor gain and
complete slender-cylinder alias; check registration, malformed/unsupported
inputs and held/stale/mismatched data; and demonstrate that the normal renderer
rejects this experimental representation. All 1,495 repository tests pass plus
the known transformer xfail; REVIEW.md §79 records actual checks and repairs.
Original diagnostic/simulator function bodies, inputs/defaults and historical
wire/golden/report meanings remain unchanged.

The controlled-envelope option originally proposed here was subsequently approved
for synthetic qualification only, as recorded below. The unrestricted simulator
and original 5 mm fixture remain supported. This is not a physical minimum-size
claim or adoption of that domain for the active runtime.

#### Controlled Synthetic C1 Enclosure Exclusion (2026-10-21)

The user agreed to the preceding scoped request for synthetic-only clearance
qualification with cylinder radii 0.05-0.30 m, heights 0.05-1.0 m, existing 1 m
outer arena walls, static flat-floor scenes and unchanged motion/question
meanings. No new episodes, physical deployment, risk policy or runtime integration
was requested or approved. The envelope is an explicit fixture precondition;
missing returns cannot establish its membership.

`d1ad3a2` adds `probe_synthetic_c1_enclosure` to the existing experimental
[diagnostics module][c1-prototype-source]. In addition to literal
`synthetic_test_only=True`, callers must declare `current_body_clear=True` and
`controlled_envelope=True`. Omitting either yields unknown. The collision-free
body condition matches a valid synthetic start, not an inference from a blind
near-field region. Both declarations and the supplied speed are trusted fixture
assumptions, not attested sensor facts or new host safety interlocks.

The observation-only calculation uses the existing bounded C1 history inspector
and **only the latest supported acquisition**. It does not consume a Scenario,
world obstacle list, bounds, target answer or privileged collision result.
For each supported ray, it retains the segment strictly below 0.05 m and above
the floor, ending before both the floor and the preceding representable binary32
range. A scale-aware floating-point allowance shrinks the interval. Under the
declared exact first-return model, an allowed floor-supported cylinder whose
footprint covers any point of that segment would have interrupted the ray; such
center placements are inconsistent with the observation. Neither a floor point
alone nor the absence of a return supplies this exclusion.

Let the latest age be a, decision period dt, declared speed v, deceleration A
and body radius b. The adopted reference's centerline path length is
L = v*(a+dt) + v*v/(2*A). A disk of radius b+L about the current center encloses
the entire circular-body reaction/braking sweep for any permitted turn direction;
there is no endpoint-only or straight-sector substitution. Numerical allowances
expand the enclosure. The fixed 0.6 m/s, age-0.15 s fixture gives b+L = 0.48 m
before that expansion. A failure to exclude this deliberately larger region
does not establish collision of a particular maneuver.

To cover **continuous** cylinder placements rather than just a sampled grid:

- Partition the entire allowed radius interval into adjacent bands [r0,r1].
  All potentially colliding centers lie within the sweep enclosure expanded by
  r1. Centers strictly within b+r0 are inconsistent with the separately declared
  collision-free current body.
- Cover the remaining center region by square cells. For center c and
  half-diagonal q, distance to a ray segment is 1-Lipschitz, so
  distance(c,segment)+q < r0 excludes every center in that cell for every radius
  in the band. Strict margins preserve contact cases as unresolved.
- Subdivide cells that cannot yet be excluded. Any unresolved depth-limited
  cell or exhausted global cell budget returns unknown; success requires no
  remaining cell in any radius band. The default eight bands, depth ten and
  32,768 checked cells are work limits, not safety tolerances. Hard maxima are
  sixteen bands, depth twelve and 65,536 cells.
- For the declared axis-aligned rectangular arena, low-height free points must
  extend beyond the body enclosure in both directions of both world axes.
  Convexity then puts all four outer walls outside that enclosure. This does
  not qualify arbitrary internal walls, overhangs, nonconvex rooms or terrain.

The result is `excluded_under_fixture_assumptions` with
`fixture_enclosure_excluded=True`, or `unknown`. It is not a robot `OK`, clear/
blocked answer, probability, calibrated confidence, task label or accepted map.
`free_space_qualified`, `real_input_qualified`, `training_approved` and
`numerically_certified` all remain false. The geometric argument is conditional;
the scale-aware allowances are not a formally certified interval-arithmetic
implementation or a physical uncertainty bound. Existing single-view inputs,
C1 capture/inspection APIs, heuristics, wire and default Config are unchanged.

Forty-three new bounded cases include a conditionally excluded empty moving
fixture; twelve blocked cases spanning minimum/maximum radii and heights with
straight/left/right braking; a near-wall blocked reference; strict declarations,
stale/budget/control rejection; direct cylinder/free-segment separation; and an
independently computed sampled-center cross-check. The sampled cross-check is
not the continuous-coverage argument. The 5 mm-radius alias still produces the
same observations as the empty case, demonstrating that falsely declaring the
domain can invalidate the conditional conclusion. It is preserved, not relabeled.

All 104 C1 cases and 1,538 repository tests pass plus the known transformer xfail.
REVIEW.md §80 records verification, failed-check repairs and limits. This is
ideal controlled-fixture exclusion evidence, not completion of F21/M2 or the
three-question rules baseline. Independent domain/return/error evidence,
numerical certification where required, useful maneuver-specific coverage and
representative task evaluation remain open; no collection or deployment follows.

#### C1 Missing-Return and Turning-Frame Checks (2026-10-21)

The controlled object envelope does not make partial return coverage sufficient
for clearance. Constructed missing-data fixtures now pair an empty scene with a
blocked scene for each combination of 0.05/0.30 m cylinder radius and 0.05/1.0 m
height. Each pair shares acquisition poses/ticks and configuration; only rays
whose valid ranges agree in both worlds are retained. Nonempty valid support
remains in every snapshot, but all delivered range/mask histories become
identical. The blocked reference remains blocked for straight, left and right
braking. The unchanged exclusion probe returns identical unknown results for
both members, rather than inferring free space through the missing rays.

These are bounded artificial missing-data fixtures, not evidence that the ideal
zero-dropout capture producer emits these masks, not a physical occluder model,
and not measured dropout rates or probabilities. No missingness policy or sensor
profile is adopted. They pin the existing rule that unsupported rays supply no
free prefix. Counting remaining valid rays, assuming independent missingness or
filling gaps from the other world would not resolve the identical-input pair.

Fifteen additional positive cases use five headings and straight/left/right
acquisition motion, including crossings of the principal heading boundary.
The empty fixture still excludes the same 0.48 m all-turn enclosure under the
original work limits. This checks useful registration paths that blocked-only
cases cannot establish; it is not a maneuver-specific algorithm or quality
evaluation. `a3124f9` changes tests only. REVIEW.md §81 records 123 C1 passes,
1,557 repository passes plus the known xfail and restart recovery. All prior
assumptions, qualification flags and runtime/data gates remain unchanged.

#### C1 Geometric Occlusion and Straight Capsule (2026-10-21)

The ideal first-return model now has explicit occlusion checks, not just
constructed missing masks. A 0.5 m-tall foreground cylinder hides either a
0.05 m or 1.0 m-tall background cylinder across the bounded history, although
the background is visible by itself. Independent ray/circle entry arithmetic
checks a foreground return, and direct segment/circle distances keep every
claimed low-height free prefix outside both footprints. Lowering the foreground
to 0.05 m exposes the tall background to an upper ray. These are finite ideal
geometry fixtures, not physical optical/occlusion qualification or an
opposite-task-answer alias. REVIEW.md §82 records the evidence and limits.

The experimental `probe_synthetic_c1_enclosure` additionally accepts optional
`turn_rate=0` for the adopted reference's **straight reaction and straight
braking** case. Omission or `None` preserves the original all-turn disk and
result schema. Any finite nonzero turn request within the motion limits,
including a near-zero one, stays unknown; invalid, nonfinite or out-of-range
declarations raise ValueError.
The supplied zero is a trusted fixture declaration for both phases, not a turn
estimate derived from poses or proof of future control behavior. No geometric
question definition, runtime input or accepted physical profile changes.

For this case the centerline is the body-frame segment S from (0,0) to (L,0),
where L = v*(age+dt) + v*v/(2*A), and the swept circular body is its radius-b
capsule. The continuous center-cell exclusion remains bounded over the same
entire cylinder-radius interval. In addition to the previous tests, a cell with
center c and half-diagonal q can be discarded when
`distance(c,S)-q > b+r1+2*guard`, because no cylinder of radius at most r1 in
that cell can intersect the expanded capsule. The square search still covers
the original bounding disk, so the smaller query region is not clipped out.
Free-prefix exclusion and the independent current-body-clear assumption are
otherwise unchanged. Strict inequalities and the same work/depth limits retain
unknown for unresolved cells.

The declared arena-wall check uses the capsule's world-axis extrema: project
its endpoint to p, then require supported free points beyond
`min(0,p)-b` and `max(0,p)+b`, with outward numerical allowances. This is still
conditional on the existing axis-aligned rectangular outer walls. The margins
remain implementation allowances, not certified floating-point or physical
error bounds.

Straight results use the distinct experimental schema
`micro-classifier/synthetic-c1-straight-enclosure/1`, with
`straight_centerline_length_m`, `capsule_radius_m` and the declared turn rate.
They deliberately omit `sweep_enclosure_radius_m`: a successful capsule result
must not be interpreted as excluding the old disk. The status is still
`excluded_under_fixture_assumptions` or unknown, never a robot question answer.
Training, real-input, free-space qualification and numerical-certification flags
remain false. The normal renderer, sensor captures, wire and heuristic are
unchanged; no runtime consumer or task-label path was added.

The first useful capsule fixtures contain a cylinder behind the rover: the
straight geometric reference is clear and the capsule can be excluded, while
the larger default disk remains unknown. Rotated positives, forward-wall and
near-contact blocked cases, missing-return aliases, strict declarations and
default compatibility are recorded in REVIEW.md §83. This advances only the
straight conditional synthetic case. Curved maneuver-specific coverage,
independent domain/return/error evidence, numerical certification where needed
and representative task evaluation remain open; integration and collection
remain outside this qualification scope.

#### C1 Two-Phase Curved Tube (2026-10-21)

Within the same controlled synthetic envelope, the experimental probe now
accepts `curved_segments=1..128` together with a declared `turn_rate` for
reaction and optional `braking_turn_rate` for braking. Each phase has its own
constant angular rate within the existing +/-1.5 rad/s limits. Omitted braking
turn means zero: this matches the adopted centre maneuver, which keeps the
current turn through reaction and then brakes straight. Explicit +/-1.5 braking
turns match the existing left/right maneuvers. These are declarations, not
predictions inferred from acquisition poses or qualification of future control.
No target meaning changes. Without the explicit positive segment count the
old disk/straight behavior remains unchanged; a braking-turn declaration without
that opt-in rejects rather than silently selecting a different query.

The body-frame centerline uses midpoint integration over reaction duration
`age+dt` and braking duration `v/A`, retaining at most `2*curved_segments+1`
points. For a step of duration h, initial speed u, deceleration a and angular
rate w, the second-derivative bound on velocity gives midpoint endpoint error
at most `(2*a*abs(w)+u*w*w)*h**3/24` in exact arithmetic. The position curve's
deviation from its chord is at most `(a+u*abs(w))*h*h/8`. Summed endpoint
allowances plus the maximum chord allowance and implementation roundoff margins
give E. The polyline P expanded by `b+E+guard` encloses the declared reference
sweep under these assumptions. This is an algebraic construction with numerical
allowances, not certified floating-point arithmetic or a physical error bound.

The continuous cylinder-center search uses the existing full radius bands,
low-height free prefixes and independently declared current-body clearance.
For a cell center c and half-diagonal q, the additional outside test is
`distance(c,P)-q > b+E+r1+2*guard`. Distance to the union of polyline segments
is 1-Lipschitz, so the whole cell is excluded, not merely its sampled center.
The bounding square expands by E, and world-axis wall extrema come from all
polyline vertices expanded by `b+E` and numerical margins. Thus neither the
cylinder search nor the wall check substitutes the narrower straight capsule.
Existing cell/depth/radius limits and strict unknown-on-exhaustion remain.

Curved results use `micro-classifier/synthetic-c1-curved-enclosure/1`, declaring
both phase rates and segments per phase, with `curved_centerline_body_m`,
`centerline_error_allowance_m` and `curved_tube_radius_m`. Neither the disk-radius
nor straight-length field is present. A conditional exclusion concerns only the
declared maneuver, not every turn or the whole disk. Training, real-input,
free-space qualification and numerical-certification flags remain false.

REVIEW.md §84 records independent quadrature checks, rotated clear maneuvers,
straight-clear/curved-blocked cylinders and side walls, masked/blocked unknowns,
strict controls and finite compatibility evidence. The default runtime sensor,
observation, heuristic, wire and geometric oracle remain unchanged. Independent
domain/return/error evidence, numerical certification where required and
representative task quality still gate integration and collection; this is not
a complete three-question rules baseline.

#### Approved C1 Synthetic Question-Level Package (2026-10-22)

The user explicitly approved both stages below, with Stage B conditional on
Stage A's checks passing (REVIEW.md §86). This is a separate, host-only
synthetic evidence prototype, not
a runtime replacement or new target definition. The approved cylinder/height/
floor/wall envelope and ideal acquisition assumptions would stay unchanged.
REVIEW.md §85 records the completed prerequisite checks and the pending scope
proposal as it stood then; §86 supersedes its approval-blocked status. Both
stages are implemented below; REVIEW.md §87 records the completed bounded
package, not runtime adoption or task-quality clearance.

**Stage A: positive occupied-point evidence.** An outer tube can exclude a
collision when every allowed obstacle is excluded from it. Membership of a
point in that same tube cannot establish collision: it may lie outside the
actual swept body. Clear-world counterexamples now preserve this distinction.
A candidate blocked witness instead needs both:

- Independently justified obstacle membership under the declared ideal model.
  Use only a valid, nonsaturated latest first return whose complete transformed
  height enclosure is strictly above the floor and within the declared object/
  wall domain. Floor-adjacent, masked, missing or unsupported returns abstain.
  Nominal positive height alone is not enough. Bound the float32 range rounding
  interval and transformation allowance; do not substitute Gaussian sigma,
  posterior confidence or a new physical uncertainty policy.
- Strict containment of the complete registered XY hit enclosure within a
  body disk at a declared maneuver time. For nominal hit p with assumed radius
  e and numerical center q with trajectory allowance E, require
  `distance(p,q)+e+E+guard < b`. Vertices with bounded endpoint error provide
  the first candidate times. This deliberately shrinks the admissible region;
  `distance(p,q) < b+E` is not a blocked witness. If the bound cannot be
  justified, remain unknown; sampling times affects completeness, not permission
  to infer occupancy or clearance from missing witnesses.

All such evidence would remain conditional on the artificial return, pose,
motion and domain declarations, not certified arithmetic or real sensing.
Clearance still needs the existing independent current-body-clear declaration.
Any incompatible witness, exclusion or declaration must report a contradiction
and abstain, not silently prioritize one conclusion. No new input is accepted
merely because privileged fixture geometry could supply it.

**Stage B: question-level feasibility.** A separately opted-in diagnostic
coordinator would combine exclusion, blocked witnesses and unknown, preserving
the adopted geometric meanings and separate reaction/braking rates. The
geometry oracle is permitted only in test assertions, never as evidence input.
Fixture-only goal coordinates would be explicitly declared for sector-ranking
checks, not added to the normal module input or claimed available on-device.

| Question | Conservative candidate admission |
| --- | --- |
| `path_blocked` | Centre maneuver: an exclusion supports false, an occupied-point witness supports true; absent or contradictory evidence stays unknown. |
| `clear_sector` | At rest, abstain. Initially require all three maneuver states resolved; choose only the adopted bound-separated goal ranking or its existing exact left/right tie convention. Overlapping/unresolved ranks abstain. `none` requires all three blocked, not merely no known-clear option. |
| `speed_tier` | Query each existing momentum-preserving speed `max(current_speed, max_speed*tier/3)` with centre braking. Initially require all three capacity states resolved, then select the highest clear tier; zero requires all three blocked. An unknown higher tier cannot be silently turned into a lower maximum. |

Candidate values would be diagnostic-only, not calibrated probabilities,
catalogue/wire decisions, accepted task labels or a complete baseline. `mode`
remains absent. All training, real-input, free-space and numerical-certification
flags stay false. The normal rules, codecs, defaults, input/history and existing
artifacts must remain unchanged. No controller, exporter or log adapter belongs
to this candidate scope.

**Approved bounded work and checks:** at most 32 distinct hand-constructed
geometry fixtures, CPU-only and ephemeral; invalid-input and arithmetic tests
may reuse them. Keep the existing per-query work/segment/depth limits and at
most six maneuver/capacity queries per fixture. Require visible blocked
witnesses and clear exclusions against resolved independent references, both
outer-tube counterexamples to abstain as blocked evidence, floor/rounded-height
and missing-return abstention, contradiction rejection, all-option unknown
propagation, at-rest/tie handling and momentum cases. Reuse current tests and
helpers; run focused checks, default gates and compatibility checks before local
commits. No episode rollout, collection, persistence of task data, split,
teacher/inference/training, dependency/download, risk adoption, runtime/wire
integration or hardware work would be authorized.

**Adopted sequence:** Stage A first and Stage B only after its focused
checks pass, within this single synthetic-only package. If Stage A cannot
justify its hit/trajectory enclosures, record that blocker and do not manufacture
question answers. This implementation scope is distinct from the already-approved
object envelope; neither sensor adoption nor physical qualification is requested.

Stage A is implemented in the opt-in `probe_synthetic_c1_occupied_witness`.
It reuses the strict latest-history inspection and motion/profile rejection.
One full neighboring float32 step on either side of a stored range, plus the
existing source-scale transform guard, encloses rounding and supplies a
conservative isotropic point allowance. Only complete height enclosures
strictly between floor and wall-height limits count as occupied returns.
The complete XY point allowance plus the existing trajectory allowance and
guard must fit strictly inside the body radius at a centerline vertex. That
trajectory allowance includes chord deviation as well as endpoint error, so
the vertex check can reject more than necessary; it never expands the positive
support region. Excessive numerical scale stays unknown. These remain
assumption-based implementation allowances, not certified numerical bounds,
measured errors or a newly accepted uncertainty/risk policy.

The separate `micro-classifier/synthetic-c1-occupied-witness/1` result reports
`blocked_under_fixture_assumptions` or unknown, occupied count, witness view/
row/column indices and point/trajectory allowances. It never emits clear or
question probabilities. All qualification/training flags remain false. Existing
exclusion, capture and runtime APIs are unchanged. REVIEW.md §86 records the
above-floor rounding counterexample, visible blocked and unsupported evidence
checks; those results alone were not completion of Stage B or a runtime baseline.

Stage B is implemented in the separate opt-in `probe_synthetic_c1_questions`
in the [diagnostic prototype][c1-prototype-source]. It accepts C1 history,
declared reference motion, literal body-clear/domain assumptions and explicit
`fixture_goal_m`, never a Scenario or oracle answer. Its separate
`micro-classifier/synthetic-c1-question-feasibility/1` result contains the three
candidate values, per-query exclusion/witness evidence, named-query statuses
and a unique-motion count. There are six named queries: centre/left/right and
the three adopted momentum-preserving tier capacities. Repeated speed/braking
pairs reuse evaluation but return independent nested evidence copies. Existing
per-query cell, depth, radius-band and segment caps are unchanged.

The table's conservative admission rules are implemented without adding a
probability, `mode`, codec decision or controller. Sector endpoints use the
shared bounded centerline and source-scale goal/reference allowance; overlapping
distance intervals abstain except for the existing exact symmetric left/right
tie rule. At rest, sector choice remains unknown. Unknown capacity states do
not establish a maximum tier. A clear exclusion and blocked witness for the
same query invalidate the complete bundle. Stage A also exposes a boolean
`fixture_current_body_witness` when strict support occurs at the initial
centerline vertex; a positive result contradicts the required body-clear
declaration and likewise suppresses every candidate. Absence of that flag is
not independent proof that the body is clear. Existing Stage A fields retain
their meaning, with exact canonical regression comparisons recorded in §87.

Resolved results are `resolved_under_fixture_assumptions`; partial evidence
retains per-question nulls, and detected conflicts report
`inconsistent_fixture_evidence` with all candidates null. Training, real-input,
free-space and numerical-certification flags remain false. The approved bounded
package is complete, but does not adopt C1 as a runtime sensing/input profile,
qualify physical/numerical bounds or establish representative question quality.
Further collection, task data or integration still needs separate authorization.

#### C1 Input and Evidence Qualification Proposal (2026-10-22)

**Runtime design not adopted.** After the completed synthetic package, the user
approved preparation of this proposal, then separately its bounded synthetic
input-compatibility implementation (REVIEW.md §89). Neither approval adopts a
runtime schema, sensor purchase or measurement campaign. Keep the active host
state/decision contract, single-view observations, question meanings, approved
synthetic envelope and strict abstention unchanged. The candidate below is a
reviewable boundary for a future module-local input, not an adapter already
available in the [diagnostic prototype][c1-prototype-source]. REVIEW.md §88
records scope, source checks and the decision needed to advance it.

**Proposed default: synchronized latest-batch evidence.** Retain the artificial
eight-view geometry as a reference candidate only. Require one complete,
identified batch with a common acquisition time and qualified relative poses;
reject partial or asynchronous batches rather than treating a scan as
simultaneous. Repeated delivery of a held batch does not refresh its acquisition
time or add support. Preserve the existing at-most-eight-snapshot validation
boundary for future compatibility checks, but use only the latest supported
acquisition for geometric evidence. Do not adopt a temporal free-space map,
longer history, point merging or an older-batch fallback. This limits the proof
obligation and retained evidence, at the cost of rejecting regions that older
views might have helped resolve. Removing old snapshots from the existing
prototype would itself be a separate reviewed implementation change.

| Logical Input | Proposed Owner and Qualification Obligation |
| --- | --- |
| 512 raw ranges and validity/status | Module-local acquisition; preserve per-ray identity, units, range ceiling and distinction between an occupied return and missing/clipped/unsupported evidence. A vendor status-to-validity mapping needs its own return-process evidence. |
| View geometry and calibration identity | Versioned module/embodiment configuration; ray directions, origins, mounting and their uncertainty must match the qualified profile. The current coincident-origin ring is not a buildable mount or device-zone model. |
| Batch identity, acquisition and delivery times | Acquisition owner plus a documented mapping to the decision clock; simultaneous means established timing, not eight equal caller-supplied integers. Missing synchronization evidence rejects the synchronized candidate. |
| Acquisition-to-reference transform | A named ego/motion source with clock, translation and heading uncertainty, including dropouts/resets. The current fixture's exact world poses are not available from the UART state packet and must not be silently imported from simulator truth. |
| Current speed, yaw rate and body-frame goal | Existing valid host state groups, with their ages and FLU convention (§2). Align each to the same decision reference; do not substitute the current world-frame `fixture_goal_m` argument or treat aged odometry as current. |
| Maneuver/embodiment parameters | Reviewed profile, including body footprint, braking model and separate reaction/braking turns. These are declared hypothetical maneuvers, not inferred promises about host actuation or physical stopping capability. |
| Domain membership and current-body clearance | Independent evidence with a stated owner, scope, validity interval and failure behavior. Neither can be established by an unexplained true flag or by absence of a C1 blocked witness. Until qualified, no complete runtime bundle is admitted. |

The current UART already carries velocity, yaw rate and a body-frame goal,
not absolute acquisition/reference poses or C1 images. Prefer a module-local
relative transform and body-frame goal boundary for a future prototype, with
an explicit qualified source rather than a new absolute-pose requirement.
Integrating host velocities is not exact registration: accumulated uncertainty,
missing history, host/module clock mapping and resets must be accounted for.
No such estimator or clock protocol is selected here. If adequate registration
cannot be established with current inputs, return to profile/contract review;
do not add fields, assume zero drift or move the decision calculation to the host.

**Qualification sequence and exits.** Apply the existing evidence-qualification
plan below to this candidate, rather than treating synthetic success as sensor
qualification. Each later executable or collection stage needs explicit scope.

1. **Input/evidence boundary review:** agree the logical fields, owners, timing
  reference and supported claim. Trace every argument currently supplied by a
  fixture to an admissible source or an explicit unresolved dependency. Exit:
  no world geometry, oracle answer, world-frame fixture goal or unexplained
  body-clear/domain flag can enter a proposed runtime evidence path.
2. **Isolated synthetic compatibility proposal:** specify, before implementing,
  equivalence checks between an explicitly declared relative transform/body
  goal and the old exact-pose/world-goal fixtures. Include common translation/
  rotation, held/delayed data, time resets, inconsistent view/calibration
  identities, invalid host groups and transform uncertainty. Exit: preserved
  candidate semantics and legacy bytes, with unknown for unsupported evidence;
  equivalence would still not qualify the source of those inputs.
3. **Return/domain/registration evidence review:** choose a physical or explicitly
  ideal-simulation claim and admissible independent references, collection
  conditions, error treatment and lineage. Real devices need zone/return,
  material, interference, timing and mounting evidence, not point-ray analogy.
  Exit: justified occupied-return and free-prefix enclosures plus independently
  established domain/body preconditions. No Gaussian failure convention or
  numeric physical bounds are adopted by this plan.
4. **Numerical and bounded-runtime review:** justify transformations, float32
  rounding, floor separation, whole-cell exclusion, inner witnesses and goal
  ranking, including overflow/tangency and contradiction abstention. Size the
  full workspace, retained evidence and copies; establish applicable target
  timing and exhaustion behavior before integration. Exit: a named numerical
  claim and measured applicable resource evidence, not just host test passes.
5. **Representative task-quality protocol:** prospectively define scene/domain
  diversity, failure/abstention categories, independent cohort lineage and
  useful coverage/quality gates. Preserve the 5 mm out-of-envelope alias and
  occluded/missing-return unknowns. Exit: an approved evaluation protocol before
  collection, followed by actual reviewed evidence under a separate approval;
  the earlier 32-fixture package and eight diagnostic runs are not renewed.
6. **Integration decision:** only after the relevant exits, decide whether to
  adopt a versioned input/profile and qualified rule path. Separately resolve
  partial-candidate rejection under the complete three-answer contract; do not
  fabricate one-hot confidence or serialize unknown as `none`/tier zero. Host
  actuation and fail-safes remain independent; no linked firmware or board work
  is authorized by passing an earlier stage.

**Resource worksheet, not a budget or measurement.** At the current Python
array dtypes, one prototype batch's range/mask/tick/pose arrays contain
`512*4 + 512*1 + 8*4 + 8*3*8 = 2,784` bytes; eight stored snapshots contain
22,272 bytes (21.75 KiB), before Config, objects, alignment, copies or workspace.
The earlier 20,736-byte estimate omitted poses and remains a range/mask/tick
subtotal. Packing masks to 64 bytes and sharing one binary32 pose and u32 tick
would give `2,048 + 64 + 12 + 4 = 2,128` bytes per synchronized batch before
status, calibration, uncertainty and framing. That is an alternative encoding
estimate, not a selected format, qualified pose precision or UART requirement;
on-module sensor traffic is not the host state frame.

Retained range bytes alone do not bound algorithm memory. At the coordinator's
default 16 segments per phase there are at most 33 centerline vertices; a
512-return by 33-vertex XY float64 difference array alone contains 270,336 bytes,
before distances, masks and expression temporaries. A future bounded native
design could stream comparisons instead, but no such port, stack/RAM fit or
latency is established. Six queries at the existing default 32,768-cell cap
permit up to 196,608 searched cells per decision before reuse; that is a work
limit, not evidence of meeting a 20 Hz deadline. Do not reduce caps or numerical
allowances simply to claim fit, or assume a data-layout change removes the cost.

**Alternatives and decision for review.** A sequential scan or accumulated map
may reduce sensor count or improve coverage, but adds view-age, ego uncertainty,
scene-change and retention proof obligations that the current implementation
does not handle. A physical simultaneous ring avoids scan accumulation but
requires buildable mounting, synchronization and multi-device optical evidence.
A wider single sensor changes resolution, returns and near-field coverage and
needs a fresh information study. Recommend the latest-batch, relative-frame
boundary for an isolated synthetic input-compatibility prototype first, with
trusted declarations still visibly fixture-only. Approval would need to specify
that bounded prototype and its checks; it would not adopt C1, qualify real
inputs, reopen collection or authorize runtime/wire integration. If the missing
domain/body/registration evidence has no credible owner, do not pursue that
candidate as a runtime solution merely because its synthetic answers resolve.

**Approved bounded implementation authorization (2026-10-22):** an isolated,
CPU-only synthetic relative-frame/body-goal compatibility prototype and tests.
Use at most 16 already-existing complete scene records and 64 paired old/new
coordinator comparisons, with no new scene coordinates, starts, goals or object
heights. Numerical frame changes operate on copies of existing input records,
not new Scenarios or collected histories. Keep at most six maneuver/capacity
queries per call and existing work limits. Reuse current tests/helpers; do not
add a CLI, output artifact, log adapter, normal observation consumer or native
runtime port. This was a separate bounded package, not reuse of an exhausted
approval; the implementation and checks are now complete below.

The proposed logical boundary carries raw ranges/masks, fixed-profile identity,
batch/reference timing, acquisition origin/heading relative to the reference
body, body-frame goal, speed and reaction turn. Current-body/domain declarations
remain explicitly synthetic preconditions, not new host flags. Keep ideal
exact-transform assumptions; nonzero or unqualified transform/time/return errors
remain unsupported rather than borrowing the deterministic witness argument.
Any arithmetic allowance needed when converting old fixture coordinates must
retain its source-scale provenance. Small normalized coordinates cannot justify
discarding cancellation/rounding uncertainty or weakening the old source guard.
If that allowance cannot be justified, abstain and record the non-equivalence.

Acceptance checks should cover common coordinate translation/rotation, held and
delayed batches, invalid/aged goals and motion groups, timestamp gaps/resets,
mismatched view/profile identity, large-coordinate cancellation, near ties and
contradictions. Compare candidate values and admission/conflict statuses with
the old fixture path where numerical support is equivalent; world-coordinate
trace fields need not match. A normalization alone must not create a positive
clear/blocked conclusion from previously unsupported numerical evidence.
Legacy functions/defaults/bytes and existing tests remain unchanged; synthetic
goals and oracle comparisons stay test-only. Passing would establish input
compatibility only, not the provenance or physical qualification of that input.

#### C1 Synthetic Relative Input Compatibility (2026-10-22)

The separately approved bounded package is implemented in
`prepare_synthetic_c1_relative_input` and `probe_synthetic_c1_relative_questions`
in the [diagnostic prototype][c1-prototype-source]. Both require explicit
synthetic opt-in and retain false training/real-input/free-space/numerical-
certification flags. The first function converts existing exact fixtures into
independently owned raw range/mask arrays, capture ticks, acquisition poses
relative to a reference body, a fixture body-frame goal and profile metadata.
It does not observe motion, estimate poses or create new sensing evidence.

Two additional fixture dependencies must survive a coordinate change: the
declared arena axes relative to the body, because the wall exclusion assumes
axis-aligned walls, and the original coordinate scale used by numerical guards.
The relative record carries `fixture_arena_yaw_rad` and
`numerical_source_scale`; neither is an attested runtime source. Missing or
inconsistent provenance rejects. Ordinary common-translation and quarter-turn
coordinate copies are tested without creating a transformed Scenario. Arbitrary
wall orientations are not newly qualified by this coordinate test.

The query function accepts only a synthetic `State`-shaped fixture. Existing
wire validation checks its structure, then the prototype requires planar motion,
the three valid velocity/angular/goal groups with zero ages, exact goal binding
and the artificial sample timestamp `reference_tick*50000` microseconds.
Nonzero transform, heading or clock error remains unsupported. These are ideal
fixture restrictions, not a selected physical freshness/clock policy or an
integration of the live host transport. Binary32 wire-decoding equivalence,
clock wrapping and real ego-estimator behavior are not qualified by these tests.

To reuse every legacy geometric function unchanged, the bridge reconstructs a
canonical axis-aligned computational frame. Its power-of-two translation is
at least four times the retained numerical source scale, so small relative
coordinates do not erase the older source-scale guards. It rejects excessive
scale before the embedding and retains strict bounded capture-motion checks.
Sector ranking uses the supplied body-frame goal directly, so rounding in the
canonical embedding cannot manufacture the exact left/right tie convention.
This is a conservative implementation allowance and tested compatibility
construction, not a floating-point enclosure certificate or a new uncertainty
policy. It can abstain more often than the old fixture path; no universal
equivalence or claim of improved evidence follows.

Schemas `micro-classifier/synthetic-c1-relative-input/1` and
`micro-classifier/synthetic-c1-relative-questions/1` are experimental only.
The query result contains candidate values, conditional evidence and numerical
provenance; no probabilities, wire decision, controller, log consumer or exporter
is added. All legacy source/test nodes, defaults, bytes and artifacts remain
unchanged. REVIEW.md §89 records 64 new checks, 13 reused complete scene records,
30 paired comparisons and at most six unique motion queries per call. This
completes the approved package, not the independent clock/registration/arena-axis,
domain/body-clear, return-process, numerical, resource or task-quality gates.

#### Simulation-First C1 Evidence-Source Plan (2026-10-22)

**Approved preparation only; all mechanisms below are proposals.** Following
REVIEW.md §89, the user approved a design-only, simulation-first qualification
plan for registration, timing, arena axes and domain/body clearance. This adds
no source provider, evidence schema, audit implementation, fixture run or
runtime path. REVIEW.md §90 records this preparation and its approval boundary.
The proposed claim is deliberately narrow: consistency of a named
ideal-simulator source with one declared fixture input and its preconditions.
It is not physical metrology, numerical certification, independent task truth
or qualification of the current live host input. The earlier general evidence
plan still applies; this section specifies the missing source and binding work.

**Two separate evidence lanes.** Candidate-side records contain only the
already-proposed raw ranges/masks, timing, relative registration, body-frame
goal and explicitly declared fixture provenance. Private qualification records
may contain complete Scenario geometry, exact source poses, simulator event
times and independent reference calculations. Bind them for an audit, but
never merge the private fields into the candidate input, student/teacher
renderer or blind human-review packet. Matching hashes establish identity,
not correct physics, a truthful sensor, independent lineage or admissible data.
No accepted family/cohort/split is created by a successful source comparison.

| Evidence | Proposed Ideal-Simulation Source and Cross-Check | Unresolved Beyond That Claim |
| --- | --- | --- |
| Relative registration | Named capture/reference event poses from the fixture source; independently compose the relative transform in the private audit and compare its declared numerical enclosure with the candidate record. Retain source coordinate scale, axes, units and transform direction. | Shared simulator truth is not an ego estimator or physical pose reference. Reusing the converter as its own reference is circular. Nonzero transform uncertainty is unsupported by the current query API. |
| Timing | A private source event ledger binds acquisition identity, delivery event, host sample and decision reference to one simulator clock epoch and tick period. Check the complete held/delivery sequence, not just equal timestamps. | Nominal cadence, receipt time or an age-zero State alone does not establish a clock mapping. No physical synchronization, drift model or timestamp-wrap convention is selected. |
| Arena axes | Declared rectangular Scenario axes in the private reference frame, composed into the same reference body frame as the relative input. Cross-check sign, units and reference-pose identity. | A fixture yaw is not localization against a physical arena. Arbitrary walls, rotated scene geometry and an unknown arena frame remain outside the existing wall exclusion claim. |
| Controlled domain | Private inspection of all declared fixture objects and boundaries against the already-approved static flat-floor cylinder/wall envelope, including omitted, hidden and occluded objects. | C1 rays cannot certify that no out-of-envelope object exists. A domain audit is oracle-assisted qualification metadata, not observation evidence or an adopted restriction on normal simulator objects. |
| Current-body clearance | Private independent contact-inclusive circle/cylinder and boundary comparison at the exact reference event, retaining uncertainty/tangency as unresolved where applicable. | Absence of an occupied witness is not clearance. Conditioning acceptance on privileged body truth is oracle-assisted admission and cannot be reported as an autonomous observation-only baseline. |
| Goal/motion and return model | Exact source state/frame values, versioned ideal ray/first-return configuration and source identities bind the input to the audit. Check supplied body-goal and motion against that record without exposing target answers. | The source shares simulator geometry; this does not validate device zones, materials, optics, braking capability, real odometry or task labels. |

**Proposed binding record, private to qualification.** Identify the source
revision and relevant code/configuration identities, fixture identity, clock
epoch, capture batch and reference event. Bind the exact candidate payload,
host frame, profile/calibration identity and private reference record. Include
per-array shape, dtype, byte order and an explicit contiguous traversal order before
hashing range/mask/tick/relative-pose arrays; do not rely on Python equality of
booleans/integers, approximate float equality or mutable dictionary identity.
Bind the supplied numerical scale and arithmetic allowance as provenance too.
Invalidate the binding on any changed payload or dependency. These are proposed
record semantics, not newly allocated fields in the experimental input or wire.

The host frame means the exact binary32 bytes and the values obtained from
decoding those bytes, not the higher-precision State object passed to an encoder.
The current relative prototype calls `encode_state` for validation but continues
using the original object; §89 therefore established no decoding equivalence.
A future audit must retain both sides of a round trip and any goal/motion change.
If exact fixture goal binding or an existing bound no longer holds, report the
mismatch/unresolved evidence rather than rounding the goal, widening a tolerance
or declaring the decoded state interchangeable. No wire adapter is authorized.

**Lifecycle and failure rules for review.** A held batch keeps its original
acquisition identity/time and byte-identical raw ranges, masks and source
acquisition pose. Relative poses may change with the reference event; recompute
and bind them to that event without rewriting acquisition evidence. A new
delivery is not a fresh exposure. Repeated payload bytes under another source,
clock epoch or calibration do not inherit a binding. Reject mixed-view clocks,
reference-event substitution, configuration drift, timestamp reversal and
missing delivery lineage. After a reset or wrap, require a newly reviewed epoch
mapping and rebind every dependency; do not join across it by numeric proximity.
No interpolation, older-batch fallback, persistent occupancy map or host-state
freshness policy is adopted. The artificial `tick*50000` mapping fits a u32 host
timestamp only through tick 85,899; tick 85,900 exceeds it. That arithmetic fact
does not define modular ordering or qualify reset/wrap handling.

**Audit outcomes are not decision outcomes.** A proposed source-consistent
verdict means only that the bound ideal fixture records match their declared
references under stated assumptions. An inconsistent verdict retains which
dependency failed; unresolved means a required source, allowance or independent
reference is missing. All three remain training-disabled, real-input-unqualified
and numerically uncertified. A private domain/body audit may veto a proposed
claim, but cannot manufacture a clear/blocked answer, replace unknown or satisfy
the existing query's literal preconditions by silently injecting oracle flags.
Any future experiment using oracle-assisted admission must name and report that
conditioning separately, including rejections; it cannot establish observation-
only runtime coverage or representative task quality.

**Acceptance and stopping conditions.** Before implementing an audit, review
the evidence lane/owner matrix and binding semantics. A bounded audit prototype
should demonstrate a matching record and mutations of each bound dependency,
including identical payload/different lineage, valid wire encoding with changed
decoded values, held-record tampering, clock-epoch substitution, reversed frame
composition, arena-axis mismatch and source-scale loss. It must also retain
body-contact/domain failures privately, with no truth in candidate-side output
and no coordinator/teacher/training calls. Independent reference arithmetic
cannot call the producer/converter being audited. Matching records alone do
not qualify numerical bounds; uncertainty without a justified enclosure remains
unresolved. Stop at a precise source/claim mismatch rather than inventing an
error budget, removing out-of-envelope fixtures or outcome-driven tuning.

**Recommended next bounded scope, not yet approved:** a CPU-only, private
synthetic source-binding audit helper and tests, using at most eight already-
existing complete scene records and 32 audit cases, with zero coordinator
queries. Reuse current packages/test helpers, source records and scalar geometry
references; no new Scenario geometry, episode, log replay, persisted artifact,
CLI, schema adoption, normal input consumer, collection or runtime integration.
The output would be diagnostic source consistency and explicit missing-evidence
reasons only, not labels or decisions. An audit passing would complete that
bounded tooling scope, not approve the source model for deployment. Physical
qualification still requires a separately reviewed sensor/reference/collection
direction; the settled synthetic envelope and strict abstention do not change.

#### Private C1 Source-Binding Audit (2026-10-22)

The user separately approved the preceding bounded helper/test package. It is
complete through `04492d7` and `d483d14`; REVIEW.md §91 supersedes the plan's
implementation-blocked status for that package only. Two private functions in the
[diagnostic prototype][c1-prototype-source] add no CLI, public/deployed schema,
normal input consumer or decision path. `_c1_source_binding_digest` binds typed
candidate, State, exact host-frame bytes and private-source records. Numeric
array/scalar dtype, shape, byte order and C-order bytes survive hashing; Python
boolean/integer aliases,
NumPy scalars, zero-dimensional arrays and different lineages remain distinct.
The expected digest is caller-supplied, not a signature or an attestation.

`_audit_synthetic_c1_source_binding` requires literal synthetic opt-in and checks
that binding before comparing the declared records. It validates the existing
ideal profile, clock/reference epoch, acquisition/capture identities, delivery
and snapshot sequence, per-view clocks and held-capture identity/bytes. Scalar
frame composition independently checks relative poses, goal and arena axes
without calling the capture producer, inspector or converter. These comparisons
require exact agreement; arithmetic disagreement stays unresolved, with no new
tolerance, uncertainty budget or claim of certified numerical enclosure. Source
scale must be retained. The private geometry check rejects unsupported cylinder/
wall domains and unresolved reference-body clearance, including near contact.
It neither repairs an input nor supplies body/domain flags to a coordinator.

The host State is actually encoded and decoded, and the exact bytes must match
the separately supplied private host frame. Any changed floating field is
reported by name and remains unresolved, including the tested `0.6` velocity
and a goal offset below binary32 resolution. No value is rounded to force goal
binding, no speed limit is widened and the old relative query is unchanged.
Returned information is limited to audit status/reason, binding digest, changed
field names and false training/real-input/free-space/numerical-certification
flags. No Scenario, ranges, poses, target answer or decision candidate is returned.

The package has 32 new cases: one typed-identity case and 31 audit cases/calls,
using three complete scene records already present in neighboring tests. Several
controls recompute the digest after mutation to exercise the independent checks,
not merely hash rejection. An instrumented 35-check combined run verifies those
scene identities, the 32-case/31-call count and zero audit coordinator queries.
Every pre-existing source/test AST node is unchanged. The full gate passes
1,941 tests plus the known transformer xfail; REVIEW.md §91 records details.

**Evidence limit:** producer/calibration identities, events, poses and state
are still separately declared fixture records, not sealed producer-owned
evidence. Matching records do not prove that the named source emitted them,
that the private geometry is complete, that ranges follow its return process,
or that a physically consistent dynamics history generated the state. Private
domain/body checks cannot be promoted into autonomous observation-only admission.
No physical clock/registration, wire-input equivalence for changed values,
numerical certification, task cohort/quality, collection or runtime integration
is qualified. This completes and exhausts the bounded audit approval.

**Next candidate, not approved:** a producer-owned, private synthetic source
recorder, limited to four reused complete scenes and 16 source-record cases,
zero coordinator queries, no new geometry, episode/log replay or persistence.
It would bind actual fixture capture/reference events and source identities
instead of test-authored identity strings, remaining separate from candidate
input and normal simulator/wire behavior. Any such implementation needs its own
approval; it would still not establish physical sources or resolve binary32
input uncertainty. No automatic continuation, input adoption or deployment follows.

#### Private C1 Fixture Source Recorder (2026-10-22)

The user separately approved the preceding four-scene/16-case recorder package.
It is complete in `76aa712`; REVIEW.md §92 supersedes that proposal's blocked
status for this bounded prototype only. `_SyntheticC1SourceRecorder` in the
[diagnostic prototype][c1-prototype-source] requires literal synthetic opt-in
and owns a copied Scenario, explicit fixture tick/pose/State events and their
encoded host frames. It calls the existing ideal capture producer on acquisition
ticks, records delivery and held snapshots, and retains at most eight delivered
history entries. Under the supported consecutive-tick cadence, tests observe at
most two pending captures. No RoverEnv rollout, normal consumer, CLI, persistent
record format or public/deployed schema is added.

Recorder-created epochs and capture IDs distinguish acquisitions from held data
and other recorder instances. Local hashes of the diagnostics, rover and protocol
source files replace test-authored producer strings; the ideal configuration's
typed digest supplies profile identity. Those hashes identify on-disk files,
not authenticated loaded code or a physical calibration. The epoch is a local
identifier, not clock synchronization evidence. Poses and State remain explicit
fixture inputs, not measured or dynamically inferred state. This is process-local
provenance bookkeeping, not a security boundary against arbitrary in-process code.

Snapshots copy candidate-side input separately from private source geometry,
events, frame bytes and source-file identities. The recorder retains the current
binding independently of returned dictionaries and passes its own anchor to the
existing private audit. Re-signing a changed candidate/private record or manifest
does not replace that anchor. A successful new tick invalidates the old seal;
another snapshot is required for the new reference event. Repeated snapshots of
one unchanged event retain the same binding. Foreign bundles and source-file
drift reject. Missing deliveries, gaps/reversal, boolean ticks, overflowing fixture
timestamps and timestamp mismatches cannot create a fresh admissible record.
No wrapping, interpolation, reset continuity or physical clock policy is adopted.

All audit qualification flags remain false. Body/domain truth stays in private
records; candidate-side input receives neither Scenario geometry nor the file
manifest. Audit consumption does not recapture or rerun registration producers,
and it makes no decision queries. Binary32 changes and unsupported domain/body
evidence remain unresolved through the unchanged audit. No goal is rounded,
limit widened, evidence assumed from missing rays or runtime rule changed.

Sixteen new cases use three complete pre-existing scenes. The instrumented
19-check combined run verifies that reuse and zero decision queries; its actual
in-memory work is 80 successful explicit fixture ticks, 60 capture batches and
21 returned snapshots across 18 bindings, including paired ownership/reference
controls and repeated snapshots. These are unit fixtures, not collected episodes
or representative samples. All pre-existing source/test AST nodes are unchanged.
The full gate passes 1,957 tests plus the known transformer xfail (§92).

**Remaining boundary and next candidate, not approved:** tests-only bounded
recorder-to-audit-to-question-feasibility compatibility, at most four reused
complete scenes and 16 cases, at most six unique motions per coordinator call.
Only source-consistent fixture cases would reach the question checks. Literal
body/domain declarations must be explicitly identified as oracle-assisted
fixture admission, not inferred sensor evidence or a runtime policy. Keep private
geometry out of the candidate input; preserve unknown/conflict outcomes. No new
geometry, rollout/log replay, persistence, runtime/source implementation, input
adoption, physical uncertainty policy or data/quality claim is proposed. This
would test composition only; actual pose/motion, physical sensing/clock/arena/
domain/body evidence, numerical/resource and task-quality gates remain open.

#### Tests-Only C1 Recorder Composition (2026-10-22)

The user separately approved that bounded tests-only package. It is complete
in `0c3de54`; REVIEW.md §93 supersedes the preceding composition-blocked status
only for those checks. One parameterized test adds 16 cases over four complete
pre-existing scenes. Runtime source and every pre-existing test AST node remain
unchanged. The test harness audits the recorder-owned snapshot before calling
the existing relative question wrapper; it is not an implemented runtime
admission pipeline. Private Scenario, source manifests and frame records stay
out of the candidate-side call. Literal body/domain declarations are explicitly
oracle-assisted fixture conditioning, never inferred observation-only evidence.

Ten source-consistent cases reach the question wrapper; eight reach its
coordinator, seven using four unique motions and one using the maximum six.
Matching exclusion/witness calls verify caching and the per-call bound. Six
resolved cases agree with the existing synthetic geometric reference. Missing
literal declarations and zero-cell budgets remain unknown; an explicitly
injected contradictory witness clears all candidates rather than overriding
clear evidence. The conflict is a test fault, not an observed sensor result.
Six source-rejected cases make zero question calls: binary32 change, unsupported
domain, body contact, re-signed candidate mutation, stale reference and foreign
ownership. Held data retain acquisition identity and time across reference ticks.
All training/real-input/free-space/numerical-certification flags remain false.

Instrumented transient work is 70 successful explicit fixture ticks, 53 capture
batches and 19 returned snapshots, with no episode, log replay or persisted
source/audit artifact. These are hand-authored fixtures, not dynamically verified
trajectories or representative task cases. In particular, owned capture poses
and a declared host velocity do not establish that one motion process produced
both. The full gate passes 1,973 tests plus the known transformer xfail (§93).

**Next candidate, not approved:** design-only fixture motion-source contract.
Specify pose/tick/host-velocity and angular-rate ownership and binding, held
acquisition versus current-reference semantics, and independent straight/turn/
held controls and inconsistent-history rejection checks. Keep binary32-changing
States unresolved; propose no rounding or uncertainty policy. No implementation,
new geometry, rollout/log replay, persistence, input/profile adoption, collection
or runtime integration. This would refine the unresolved motion row of the
existing source plan, not repeat the completed source-binding/ownership work
or qualify physical sensing, numerical bounds or task quality.

#### Proposed C1 Fixture Motion-Source Contract (2026-10-22)

**Design-only preparation approved; contract and implementation not adopted.**
REVIEW.md §94 records this refinement of the source plan's unresolved motion
row. The proposed claim is that one private fixture owner produced the seed,
poses, acquisition/reference events and host motion from one named ideal
kinematic model. It is not a claim of physical dynamics, measured odometry,
collision-free motion, braking capability or qualified runtime input. The
existing recorder and §93 composition checks do not establish this claim.

**Recommended first model:** one constant planar twist per bounded fixture
epoch, using the existing [constant-twist integrator][c1-motion-source] for
production only. This isolates pose/host-motion causality without adopting the
larger environment's control and termination model. An owner copies one existing
Scenario and owns an explicit seed tick/pose, fixed forward speed and yaw rate,
ideal profile and epoch.
After seeding, callers cannot supply replacement poses, host motion, goal
vectors or timestamps. The owner derives each pose and original fixture State,
then supplies them to the unchanged private recorder. Other protocol fields
remain explicit validated fixture settings, not a new host or freshness policy.
Bind seed/model/version, exact twist values, event order, State, encoded bytes
and the recorder's event/binding identity; returned copies cannot replace the
owner's retained anchor. File hashes still do not attest loaded code or physics.

| Event | Proposed Meaning and Owner | Required Check |
| --- | --- | --- |
| Seed `k0` | Owner-declared initial pose and constant twist at one clock origin; no preceding trajectory is claimed. | Literal fixture opt-in, finite supported planar values and profile identity. Initial nonzero speed is not an acceleration-from-rest result. |
| Advance to `k` | Consecutive nonwrapping tick, one interval after `k-1`; apply the owned twist, then capture/reference the resulting pose. | State at `k` names the twist applied during `(k-1, k]`, not a target command, finite-difference estimate or next-interval promise. |
| Acquisition `c` | Existing ideal cadence produces all eight views at the owner's pose at `c`. | Exact event identity, synchronized view ticks, acquisition pose and raw payload stay bound. No backward pose inference from a later State. |
| Delivery/hold at `k` | Existing two-tick delivery and held snapshots; reference pose continues advancing. | Receipt is not exposure. Held capture ID/time/pose/ranges/masks stay fixed; relative registration changes with the reference. |
| Host sample at `k` | Owner emits forward FLU velocity, z yaw rate, body-frame goal and `k*50000` microseconds from that same event. | Zero fixture ego ages and existing planar/validity rules; preserve original State, exact frame bytes and decoded values separately. |

The interval-ending convention follows the non-collision kinematic portion of
`RoverEnv.step`, which selects applied motion before integration and records
the incremented tick afterward. The proposed owner is **not** a RoverEnv
adapter: it omits target-speed clipping, acceleration ramps, collision stopping,
reward, termination and sensor/ego faults. Those omissions define its narrow
kinematic claim, not revised simulator or robot dynamics. A varying-twist or
action-driven provider is an alternative only after a separate model/transition
contract; do not mix profiles or infer acceleration from this first model.

For pose `p=(x,y)` and heading `theta`, the defining equations use elapsed
model time from the seed, not the absolute host timestamp:

$$
\dot p(s)=v\,(\cos\theta(s),\sin\theta(s)),\qquad
\dot\theta(s)=\omega,\qquad s_k=(k-k_0)/20.
$$

The clock truth is integer microseconds; the integrator's binary64 `dt=0.05`
is not exactly the rational `1/20`. Retain both rather than silently identifying
them. Require seed and all later ticks in `0..85899`, with a new owner/epoch
instead of wrapping or joining reset histories. Heading comparisons must respect
equivalent orientations across the wrap boundary, without discarding source
scale or admitting unsupported large-yaw arithmetic. Fixed-world Scenario goal
is privately transformed at each current
pose; a held ToF frame does not hold the current goal or host sample fixed.

**Independent checker, not producer self-comparison.** A future private checker
must reconstruct from seed and total elapsed ticks without calling `integrate`,
the motion owner, recorder, capture producer or relative converter as its
reference. Straight motion can use exact rational arithmetic plus explicit
enclosures of time conversion and binary64 operations. Curved motion needs an
independent scalar integral with justified truncation and roundoff enclosures;
agreement of two floating answers or sampled residuals is not an enclosure.
Compare every retained event, not just the last endpoint; check both world
translation and orientation and independently bind host speed/rate to the
governing interval. Missing arithmetic evidence is unresolved, never a guessed
epsilon, numerical certification or a newly adopted error/risk policy.
Negative reference controls must include a freshly owner-bound, deliberately
fault-injected producer result, so a reference mismatch is not tested only as
digest rejection. That test mechanism does not permit caller re-signing to
replace the owner's retained anchor.

**Separate verdicts:** ownership/event consistency, kinematic-reference evidence
and the existing source/wire audit must remain distinguishable. A source-owner
match alone cannot establish the mathematical trajectory. Conversely, motion
evidence cannot waive `host_round_trip_changed` or exact goal registration.
Even binary32-exact speeds/rates can yield a nonrepresentable moving or rotated
body goal. Retain the original and decoded values and report that source audit
unresolved; do not round a goal, change geometry, widen a bound or substitute
decoded motion to obtain admission. No positive curved-motion qualification is
available without its independent enclosure. All outcomes remain diagnostic,
training-disabled, real-input-unqualified and numerically uncertified, with
zero question queries in the first proposed prototype. Domain/current-body
checks stay private and oracle-assisted; none of these verdicts creates their
literal declarations or overrides an unknown/conflict question outcome.

**Proposed 16-case acceptance matrix, not executed:**

| Case | Required Discriminating Check |
| --- | --- |
| Seed/stationary | No invented pre-seed history; zero twist leaves pose fixed. |
| Straight | Owner's pose and host speed share an interval; independent rational/enclosure reference. |
| Left curve | Positive yaw rate binds pose/host/captures; missing enclosure stays unresolved. |
| Right curve | Mirrored negative yaw rate, with the same evidence requirements. |
| Moving reference/held capture | Acquisition identity/time/pose and raw bytes stay fixed while reference and goal advance. |
| Heading wrap | Equivalent orientations do not become a spurious full revolution. |
| Stationary pose/nonzero speed | Freshly bound injected producer fault fails the independent translation check. |
| Wrong pose/yaw | Displaced or wrong-sign rotated event fails the reference comparison. |
| Wrong host twist | Host speed/rate cannot name a different interval or target command. |
| Gap/reversal | Missing or reversed tick is not interpolated or silently joined. |
| Epoch substitution | Numerically matching ticks from another origin do not inherit continuity. |
| Rewritten hold | New receipt/reference cannot refresh acquisition metadata. |
| Goal binding | Current body goal must correspond to the same owned pose and fixed world goal. |
| Wire round trip | Changed original/decoded fields retain the existing unresolved verdict. |
| Missing numerical evidence | Matching floating outputs alone cannot produce positive motion qualification. |
| Foreign/re-signed copies | Another owner or a recomputed caller digest cannot replace the retained anchor. |

Positive controls must satisfy their stated evidence level, with curved or
wire-unresolved controls remaining so. Rejected requests cannot advance owner
state/seal where applicable; private geometry must not enter candidate input.
These are future requirements, not tests, passed results or quality thresholds.

**Next bounded implementation candidate, not approved:** an additive private
constant-twist fixture owner and independent diagnostic checker, at most four
reused complete scenes, 16 cases, two owners per case and eight consecutive ticks
per owner (at most 256 successful fixture ticks), zero question queries.
Keep existing recorders/APIs and historical fixtures unchanged;
do not claim positive curved qualification without the enclosure above. No new
geometry, RoverEnv episode/log replay, persistence, CLI, normal input/wire/profile
adoption, collection, labels or runtime integration. Recommended default remains
no implementation until that distinct package is approved. The design-only
approval is exhausted when this contract and handoff are recorded.

#### Private C1 Motion Owner and Checker (2026-10-22)

The user separately approved the preceding bounded private prototype. It is
complete in `fe21517`; REVIEW.md §95 supersedes the implementation-blocked
status only for that package, not normal input adoption or numerical/physical
qualification. `_SyntheticC1MotionOwner` and `_check_synthetic_c1_motion` in the
[diagnostic prototype][c1-prototype-source] are additive private tooling. All
pre-existing source/test AST nodes are unchanged. No question, episode, normal
input consumer, CLI, persistence, model or runtime path is added.

The owner copies its seed/Scenario, fixes one supported planar twist and derives
at most eight consecutive events, host State and frame bytes. After construction,
callers supply only the next tick, not replacement pose/motion/goal/timestamp.
It uses the existing integrator for production and the unchanged private recorder
for capture/delivery/hold ownership. Snapshots copy the motion ledger and private
source bundle and retain an independent outer anchor. Foreign, stale, re-signed
or malformed returned records cannot replace that anchor. Invalid advances,
including a ninth tick, do not advance the event or invalidate an existing seal.

The independent checker never uses the motion producer, integrator, recorder,
capture or relative converter as its reference. It checks every retained event's
clock, State twist and encoded frame, then binds current reference and acquired
poses to those events. Positive reference evidence is deliberately limited to
zero yaw rate and zero seed heading. Exact `Fraction` arithmetic and directed
binary64 endpoint conversion enclose the speed/time product, rational `v/20`
clock interpretation and successive coordinate additions; body-goal subtraction
is similarly enclosed. This is bounded diagnostic arithmetic under the stated
binary64/zero-heading operations, not whole-program numerical certification or
a physical error bound. No sampled tolerance or guessed epsilon is used.

Nonzero turn or seed heading remains `unresolved_motion_evidence`: no independent
trigonometric/integral enclosure has been implemented. Heading-wrap controls
verify event generation and preserve that unresolved verdict, not positive curved
qualification. Ownership consistency, motion evidence and the old source/wire
audit remain separate. A freshly owner-bound stalled producer can pass the old
source audit yet fail the motion reference; conversely, straight motion can pass
the reference and still have `host_round_trip_changed` for its current goal.
No goal is rounded, decoded State substituted or old guard weakened. Private
domain/body checks remain oracle-assisted, never candidate-side runtime evidence.

Sixteen new cases reuse four complete scenes and make zero question queries.
The final instrumented pass measures 17 owners, eight successful ticks each (136 total),
102 capture batches, 21 returned snapshots, 19 owner audits and 15 independent
checks. Audit calls include five motion-consistent, six motion-inconsistent,
four motion-unresolved and four outer-ownership rejections. Repeated snapshots
and foreign/stale/malformed controls explain why audit count is not case count.
These are in-memory fixtures, not episodes, representative task data or physical
dynamics. All training/real-input/free-space/numerical-certification flags remain
false. The full gate passes 1,989 tests plus the known transformer xfail (§95).

**Next candidate, not approved:** design-only independent reference-enclosure
contract for curved and nonzero-heading motion. Specify the mathematical quantity,
seed-relative versus absolute time, angle wrapping, justified truncation/roundoff
bounds, fault controls and unresolved behavior; retain separate exact wire/goal
admission. No code, fixture run, new dependency, geometry, rollout/log replay,
persistence, normal input/profile adoption, collection or runtime integration.
The completed owner/checker scope is exhausted and does not authorize that work
or qualify numerical, physical, resource or representative task-quality gates.

#### Independent Curved/Rotated Reference Contract Draft (2026-10-22)

The user's continuation approved preparation of this **design-only** contract
(REVIEW.md §96), not its adoption, implementation or execution. The owner,
checker, tests and source/wire guards in `fe21517` remain unchanged. Recommended
default: first construct a bounded, independent rational reference; do not turn
an enclosed mathematical endpoint into positive evidence about NumPy/libm,
physical motion, a question answer or runtime admission.

**Reference quantity and clocks.** Interpret the finite stored seed coordinates,
heading, speed and yaw rate as exact binary rational numbers. For event offset
`n=k-k0`, with `0<=n<=7`, enclose the ideal constant-twist solution

$$
\Theta(s)=\theta_0+\omega s,\qquad
p(s)=p_0+v\int_0^s
  (\cos(\theta_0+\omega u),\sin(\theta_0+\omega u))\,du.
$$

Produce separately identified references for `s_us=n/20` and `s_64=n*d`, where
`d` is the exact rational value of stored binary64 `0.05`. Neither is absolute
`k*50000` time; the latter remains the host clock/epoch binding. Do not choose
whichever reference fits the observed endpoint. The clock discrepancy has
derived componentwise bounds `v*n*abs(d-1/20)` for translation and
`abs(omega)*n*abs(d-1/20)` for unwrapped heading. These are arithmetic terms,
not new sensor, risk or physical uncertainty budgets. Keep both reference
records and account for this discrepancy explicitly in any later comparison.

**Independent rational integral.** Proposed fixed order is `N=32`, not an
outcome-tuned precision setting. For `f=sin` or `cos`, use

$$
T_f(z)=\sum_{j=0}^{N-1} a_{f,j}z^j,\qquad
a_{f,j}=f^{(j)}(0)/j!,\qquad
|f(z)-T_f(z)|\le |z|^N/N!.
$$

The derivative cycle at zero gives exact coefficients in `0,+1/j!,-1/j!`;
the real derivatives have absolute value at most one, giving the Lagrange
remainder above. Integrate each term exactly, without division by yaw rate:

$$
I_j(s)=\sum_{\ell=0}^j {j\choose\ell}
 h^{j-\ell}\omega^\ell\frac{s^{\ell+1}}{\ell+1},\qquad
Q_f(s)=v\sum_{j=0}^{N-1}a_{f,j}I_j(s).
$$

Here `h` denotes the exact stored seed heading `theta0`.

For `A=max(abs(theta0),abs(theta0+omega*s))<=4`, each displacement component
is enclosed by `Q_f(s) +/- v*s*A**N/N!`. The affine phase reaches its largest
absolute value at an endpoint, so this bound covers the entire integration
interval. The current seed/twist/seven-interval domain fits that phase limit;
check it exactly rather than relying on a rounded estimate. Add exact seed
coordinates to the enclosure; large common offsets must not remove allowances.
Zero speed/time gives exact zero displacement. Zero or arbitrarily small yaw
rate needs no special quotient, sinc approximation or cancellation workaround.

All coefficients, integrals, tails and interval endpoints remain rational.
Any optional binary64 presentation converts each endpoint outward and retains
the exact interval as authority; it cannot shrink the interval used to decide.
Proposed hard limits are eight events, two clock branches, 32 Taylor terms and
65,536 bits for each rational numerator/denominator, including intermediates.
Preflight operand sizes before allocation; unsupported growth, domain, shape,
nonfinite input or exhausted work yields unresolved, not automatic refinement.
These are proposed host-tool limits, not measured time/memory or MCU budgets.

**Heading and wrap.** Preserve unwrapped `Theta(s)` as the mathematical
quantity. A stored heading is compared on the circle, not by subtracting wrapped
numbers across `+pi/-pi`. For a future circular comparison, independently enclose
real pi using `pi=16*atan(1/5)-4*atan(1/239)` with alternating rational arctangent
partial sums and their next-term bounds. The identity follows the tangent
addition formula with the quadrant fixed by `3<pi<4`. Proposed 32 terms per
arctangent are fixed; integer wrap branches must be justified with these bounds,
not selected by a floating remainder. Retain both adjacent branches at a cut;
if more branches or insufficient separation are needed, remain unresolved.
The producer's binary64 `math.pi`, rounded modulo operations and normalization
are not exact real-pi reduction. A matching wrapped value alone is not evidence
that the implemented reduction or `atan2(sin(yaw),cos(yaw))` is bounded.

**Implementation evidence is a separate prerequisite.** The current integrator
forms a rounded step angle and midpoint, evaluates `np.sinc(angle/(2*math.pi))`
and `math.cos`/`math.sin`, multiplies/adds coordinates, then wraps heading.
The owner also normalizes yaw and rotates the fixed world goal. A rational
ideal reference does not bound these library operations automatically. A future
operation ledger must identify actual operand domains, binary64 rounding and
underflow behavior, NumPy/libm implementation/version and independently supported
absolute error bounds for sinc, trig and atan2, including normalization/modulo
branches. Repeated pose/heading errors propagate from the seed through every
step; a fresh exact reference at each step must not reset accumulated error.
Documented supported primitive bounds, not guessed one-ulp assumptions or
agreement with another call to the same library, must justify each allowance.
Without them, report the mathematical enclosure separately and retain
`unresolved_motion_evidence`; do not silently assume correct rounding.

If a later independently justified allowance `E>=0` exists for a scalar target
whose reference is `R=[L,U]`, use conservative three-way comparison of stored
value `y`: consistent only if the **whole** reference satisfies
`R subset [y-E,y+E]`; inconsistent only if those intervals are disjoint;
otherwise unresolved. Mere overlap is not a positive check. Apply the rule to
each position component and supported circular-heading branch, for every
retained event. Report the binary-step-time and nominal-clock lanes separately;
the nominal allowance must additionally include the derived clock discrepancy.
No allowance or positive curved comparison is adopted by this draft. Existing
zero-heading straight checks remain unchanged, not routed through the new draft.

**Goal and source binding.** Independently enclose `R(-r)*(g-p_stored)` from
the same stored event pose/heading `r` and private fixed world goal `g`, using
rational sine/cosine bounds and exact subtraction/products. This is a separate
goal-transform reference, not a goal inferred from a different ideal pose.
Actual normalization/trig/operation allowances are still required to compare
the original State. The old source audit must independently retain its exact
original/decoded State and frame checks. No rounded goal, decoded substitution,
new geometry or widened guard may erase `host_round_trip_changed`. Acquisition
and held-reference lineage, retained owner anchor, body/domain assumptions and
all false qualification flags stay unchanged; no reference can manufacture
candidate-side evidence or override an unknown/conflict question.

**Proposed acceptance checks, not executed:**

| Control | Discriminating Requirement |
| --- | --- |
| Seed/stationary | Exact seed and zero displacement, no pre-seed motion. |
| Rotated straight | Nonzero heading, zero turn; independent constant-direction integral identity. |
| Left curve | Positive-turn reference encloses the integral with the stated analytic tail. |
| Right curve | Exact reflection identity at zero seed heading, not a second producer comparison. |
| Tiny nonzero turn | No division by yaw rate; preserve convergence to the straight limit. |
| Two clocks | Seed-relative nominal and binary-step references stay distinct, with derived discrepancy. |
| Wrap in either direction | Adjacent real-pi branches retained; no spurious full-turn error or nearest-fit branch. |
| Held capture | Old acquisition event/bytes stay fixed while current reference and goal move. |
| Freshly bound wrong position | Deliberate producer fault outside justified bounds rejects, not merely a digest mismatch. |
| Freshly bound wrong yaw | Wrong sign/phase is distinguished when supported allowances separate it; otherwise unresolved. |
| Goal transform | Same stored pose/world goal, independent rotation enclosure and separate normalization evidence. |
| Wire difference | Original/decoded goal or twist changes still fail the unchanged source audit. |
| Missing primitive evidence | Reference can be enclosed while motion stays unresolved; matching outputs do not pass. |
| Interval boundary/overlap | Whole-reference containment, disjointness and ambiguous overlap take distinct verdicts. |
| Domain/work/input limits | Oversized rationals, unsupported phase, malformed/nonfinite values and caps fail closed. |
| Foreign/stale record | Retained anchors/epochs and acquisition identity cannot be replaced by caller signing. |

A proof/operation ledger and independently checked coefficients/remainders are
required; sampled quadrature residuals may diagnose but cannot replace a bound.
Negative motion controls must reach the reference after genuine owner binding.
Without supported producer allowances their required verdict is unresolved,
not an invented inconsistent/consistent result. No checks in this table ran.

**Next package proposed, not approved:** a private rational-reference helper and
16 synthetic-only checks in the existing diagnostic/test files, at most four
complete reused scenes, two owners per case and eight ticks per owner (256
successful fixture ticks per matrix pass), zero question queries. Return exact
translation/heading/goal references or an explicit unresolved reason; do not
modify the existing owner/checker, recorder, verdicts or prior test functions.
No positive curved-motion admission, operation-error policy, dependency, new
geometry, episodes/log replay, persistence, normal input/profile change,
collection or integration. Keep all prior AST nodes unchanged. Source checks
and the normal offline gate would follow only a separate implementation approval.
Alternative: first qualify primitive implementation bounds, which needs its own
evidence/tool/domain scope; it is not authorized here. This design preparation
is complete and exhausted, not permission to implement either alternative.

#### Private Rational Motion Reference Complete (2026-10-22)

The user separately approved the bounded reference-only package, completed in
`1bb89fe` (REVIEW.md §97). `_reference_synthetic_c1_motion` is an additive
private helper in the [diagnostic prototype][c1-prototype-source], with literal
synthetic opt-in. Every pre-existing source/test AST node is unchanged. The
owner, motion checker, recorder, source audit, question paths and normal
simulator/wire/input defaults are not modified or integrated with this helper.

The helper returns exact `Fraction` position intervals for both seed-relative
clock lanes, exact unwrapped heading, independently enclosed circular branches,
and body-goal intervals from the supplied stored pose and fixed world goal.
It uses the 32-term rational integral/analytic tail and Machin pi construction
above. No integrator, capture, converter, sinc or floating trigonometric result
is used as its reference. Input/domain/event bounds and conservative preflight
checks enforce the fixed eight-event/two-clock/32-term/65,536-bit work limits;
unsupported records or arithmetic growth return an unresolved reference with
no partial clock output. Those limits are host-tool controls, not measured
memory/time guarantees or embedded resource qualification.

`enclosed_mathematical_reference` means only that the declared mathematical
quantity is enclosed. `motion_status` remains `unresolved_motion_evidence` for
every helper result, and all qualification flags remain false. The helper does
not authenticate ownership, State content or frame bytes. Foreign or deliberately
faulty motion records can still define mathematical references; the unchanged
owner/source audit and missing primitive-error evidence are separate. Injected
wrong-position/yaw records lie outside the bare reference in the new controls,
but are not thereby newly rejected as qualified producer comparisons. No guessed
allowance, positive curved-motion admission or source/wire relaxation is added.

Sixteen tests reuse four complete scenes. One final instrumented pass measures
17 owners, 136 successful ticks, 102 captures, 18 snapshots, 33 owner audits and
32 helper calls: 21 enclosed references, eight unresolved references and three
expected opt-in exceptions. At most two owners occur in a case, with eight ticks
per owner and zero question queries. Exact higher-order endpoint identities
cross-check translation independently of the binomial integral; separate goal
and reflection/clock/wrap controls preserve the reference/source distinction.
Partial-overlap assertions exercise the proposed interval logic as rational
identities, not a newly adopted comparison API or error policy. These bounded
fixtures are not task data, physical evidence or numerical certification.

The full source gate passes 2,005 tests plus the known transformer xfail (§97).
The package is complete and exhausted. Next proposed, not approved: design-only
primitive-error evidence/operation-ledger plan for the existing integrator and
goal normalization, specifying required evidence, domains, accumulated-error
propagation, invalidation and unresolved outcomes. No new primitive allowance,
code, fixture run, dependency, collection or runtime integration is implied.

#### Primitive-Error Evidence Plan Draft (2026-11-03)

The user's continuation approved this **design-only** preparation (REVIEW.md
§98), not adoption of bounds, an implementation, a fixture run or qualification.
The current [integrator][c1-motion-source] and private owner/reference/checker
in the [diagnostic prototype][c1-prototype-source] remain unchanged. Recommended
default: keep every unsupported primitive row unresolved. A rational enclosure
of the ideal motion is independent mathematical evidence, not evidence that a
particular installed NumPy/libm path obeys a numerical error guarantee.

**Claim and evidence identity.** A future ledger must name the exact operation,
real target, input domain, units, dtype/shape, rounding points, evidence source
and result interval. Distinguish an assumed contract, an independently justified
implementation bound and an observed residual; only the second can support an
implemented error allowance. A sampled maximum is not a uniform bound and
agreement with another call into the same library is not independent evidence.
No error numbers, acceptance tolerance, risk budget or confidence level is
selected here. Numerical consistency remains distinct from source ownership,
wire equivalence, physical error and task-quality qualification.

Evidence must bind project/source revisions, actual loaded Python and NumPy
modules, native libraries and dispatched paths, platform/ABI, build options,
dtype/shape and floating-point state. Version strings/file hashes alone do not
prove which implementation ran or its error. Record any FMA/contraction,
extended intermediates, vector dispatch, rounding mode and gradual-underflow/
flush-to-zero behavior that affects the claim. An installed source inspection
or formal/vendor bound must cover the actual wrapper and kernel/domain, not
just a function with a similar name. These identities are requirements for a
future authorized audit, not verified properties of the restarted environment.
Do not modify floating-point mode, clocks, libraries or host settings to fit them.

**Source-bound operation ledger, proposed:** `d` denotes the exact binary64
value of `0.05`, `pi64` the exact binary64 constant and `r` a stored heading.
`fl` below identifies a required verified rounding enclosure, not an assumed
correctly-rounded machine operation. Preserve the source's evaluation order.

| Row | Current Expression and Real Target | Required Evidence and Domain |
| --- | --- | --- |
| P1 | `a=fl(omega*d)`; exact target `omega*d`. | Owned finite twist/profile and scalar multiplication rounding; include subnormal/zero cases. |
| P2 | `m=fl(r+fl(a/2))`; target `r+omega*d/2`. | Division/addition and propagated angle error; midpoint domain comes from the stored-heading and prior-error enclosure. |
| P3 | `q=fl(a/fl(2*pi64))`; target `(omega*d)/(2*pi)`. | Constant error, multiplication/division, positive denominator enclosure and each input error; real pi comes from the independent rational reference. |
| P4 | `s=np.sinc(q)`; target `sin(pi*q)/(pi*q)`, with value 1 at zero. | Actual normalized-sinc wrapper/kernel, dtype/shape and any zero/small-argument branch; treat as opaque until its complete bound or decomposition is supported. |
| P5 | `D=fl(fl(v*d)*s)`; target `v*d*sinc((omega*d)/(2*pi))`. | Product rounding, propagated sinc/argument/constant error and finite-result checks; no unproved cancellation of the wrapper's pi with P3. |
| P6 | `cos(m), sin(m)` and `p+ D*(cos(m),sin(m))`. | Scalar libm trig bounds plus actual NumPy coordinate multiplication/addition and array dtype/dispatch; retain coordinate magnitude and cancellation. |
| P7 | `(r+a+pi64) % (2*pi64) - pi64`; target circular `r+omega*d`. | Each addition/subtraction, real-pi discrepancy, floating remainder semantics/branch and accumulated heading error; no bare wrapped subtraction. |
| G1 | `h=atan2(sin(r),cos(r))`; target orientation equivalent to `r`. | Both trig bounds, atan2 kernel/quadrant/cut and norm bounded away from zero; ambiguous branches stay unresolved. |
| G2 | `delta=g-p_stored`; `cos(h),sin(h)`. | Same owned world goal/stored pose, subtraction rounding and normalization/trig propagation; not a substituted ideal pose. |
| G3 | `(delta_x*cos(h)+delta_y*sin(h), delta_y*cos(h)-delta_x*sin(h))`. | Every product/sum and any verified contraction, goal lever arm and cancellation; original State and decoded frame remain separate. |

For supported scalar rounding, use exact-operation interval endpoints and a
verified rounding enclosure, including signed zero and underflow. A relative
normal-number bound alone is insufficient near zero. Overflow, unsupported
mode, nonfinite intermediate or missing dtype/dispatch evidence yields
unresolved. Propagate operand uncertainty before adding the operation's own
error; keep constant, input, primitive and rounding contributions separately
identified so none is omitted or counted twice.

**Domain closure.** Begin with the existing private profile: exact stored
`v` between zero and binary64 `0.6`, `abs(omega)<=1.5`, seed heading bounded by
binary64 pi, at most seven advances and nonwrapping tick/epoch binding. These
are fixture assumptions, not physical specifications. Derive operand ranges
from each supplied record and prior supported error intervals; ideal midpoint
or endpoint bounds alone do not establish domains for the computed program.
For coordinates and goal differences retain the declared finite scene/pose
scale and accumulated error, not a newly imposed world-size ceiling. Require
closed domains for small sinc arguments, denominator separation, wrap cuts,
atan2 quadrants and near-zero/cancellation cases. If an interval leaves a
primitive's supported domain or needs unsupported branches, stop unresolved;
do not clamp, select the branch nearest the observed answer or tune the domain
after inspecting outcomes.

**Repeated-error propagation.** Let `H_k` bound circular stored-heading error
relative to the ideal binary-step-clock trajectory and `P_k` bound each world
position component. Let `Lh_k` and `Lp_k` be independently justified local step
errors, comparing the actual step against exact constant-twist motion started
from that same stored pose, for the same exact owned twist and `d`. Then a
candidate conservative recurrence is

$$
H_{k+1} \le H_k + Lh_k,\qquad
P_{k+1} \le P_k + v d H_k + Lp_k.
$$

The heading flow is an isometry on the circle and each displacement component
has heading sensitivity at most `v*d`, from the integral of unit-speed trig.
The local terms must already include supported rounding, sinc/trig, constant
and wrap error; separate additional terms would be needed for uncertain twist
or time, which are not approved by this fixed-twist claim. Start at exact owned
seed equality only when established by the source record; never restart at
zero error on a later stored event or held receipt. At a wrap cut retain all
supported circular branches; there is no Lipschitz claim for bare wrapped
coordinates. A failed local row prevents a finite supported accumulated bound.

Owner goal normalization G1 does **not** feed the next motion step: that step
uses the event's stored pose heading. Keep G1-G3 as a separate current-event
transform bound, not a repeated motion-state update. Its error is amplified by
the world-goal-to-stored-position lever arm. The existing goal reference is
relative to the same stored pose; adding `P_k` again would change that target.
A separate claim relative to ideal world pose would need explicitly derived
position/heading terms, and is not automatically adopted. For the nominal
clock lane additionally retain the existing exact `n*abs(d-1/20)` translation/
heading discrepancy; do not fit one clock or fold it silently into libm error.

**Admission, invalidation and proof obligations.** A future evidence record
needs a row-by-row proof/contract citation, domains, composed formulas, branch
conditions, implementation identity and explicit unresolved reasons. Uniform
primitive guarantees or an independently checked decomposition are candidate
routes; a bounded independent high-precision run could diagnose only unless
its reference uncertainty and domain coverage are justified. Installing such
a reference library, downloading sources or running a numeric study needs
separate approval. No dependency or new evidence run is requested by this plan.

Invalidate dependent rows on changed code, wrappers/native builds/dispatch,
dtype/shape, FP state, domain, epoch/model, goal/coordinate scale or missing
provenance. Do not carry successful rows across a restart based on a version
string, file hash or historical pass alone. Any later comparison still requires
whole-reference containment for a positive result, disjointness for a supported
inconsistency and unresolved for mere overlap. No comparison may weaken the old
owner anchor, original/decoded State/frame checks or `host_round_trip_changed`.
Keep all existing qualification flags false unless a separate qualification
scope explicitly adopts and justifies a stronger claim.

Proposed acceptance obligations, **not executed**, cover every ledger row and
its domain, zero/tiny/normal/subnormal and nonfinite branches, cancellation and
large common offsets, real-pi/wrap/atan2 cuts, seed-to-seven-step propagation,
goal-only normalization, both clocks, missing or invalidated evidence, overlap
classification and source/wire separation. Freshly bound producer faults must
be discriminated by supported bounds, not just digest mismatch; absent bounds
must preserve unresolved rather than inventing a rejection or pass.

**Next proposed package, not approved:** a bounded read-only implementation
identity/source audit of the current environment, mapping P1-P7/G1-G3 to actual
Python/NumPy/native paths and available primary-source guarantees. At most ten
ledger rows, no numerical/model/fixture execution, new dependency/download,
persisted raw artifact or implementation change; report missing paths/guarantees
explicitly in the existing documents. This could resolve identity questions,
not prove primitive errors or adopt an allowance. Alternative: separately
approve a specific supported reference/tool and numerical evidence scope after
identity/domain review. No collection, runtime integration or physical/task-
quality approval follows. This design-only preparation is complete and exhausted.

**Separately approved read-only audit outcome (2026-11-03):** REVIEW.md §99
records all ten project/wrapper/native mappings, inspected file/build identities
and explicit remaining gaps for the selected environment. This is identity
evidence only: actual scalar/short-array loops, libm IFUNC implementations,
live FP state, matching implementation/build sources and independent uniform
error guarantees remain unqualified. In the installed wrapper P4 substitutes
`1.0e-20` at zero before sin/divide, rather than assigning exactly one; any
later supported decomposition must cover that branch. G2 infers the world-goal
array dtype and needs conversion/promotion evidence, not a newly adopted dtype
or coordinate ceiling. No primitive allowance, producer experiment, source/test
change or numerical verdict occurred. The bounded audit is exhausted; a
same-ten-row primary-source review is proposed, not approved (§99), with no
checkout/package download, dependency, numerical execution or implementation.
Runtime, collection, input adoption and physical/task-quality gates stay closed.

**Separately approved primary-source review outcome (2026-11-03):** REVIEW.md
§100 completes the same ten-row review of official release-source/documentation
pages. CPython scalar operations and `%` sign correction, goal-only atan2
branches, NumPy sinc zero substitution, scalar/promotion paths and short-array
fallback conditions are now cited. Tagged NumPy double sin/cos dispatch calls
scalar libm; an AVX2 target label does not establish vector trig. Glibc's accuracy
goals and known-test maxima do not provide uniform producer-error bounds.
Maintained manuals, upstream tags and installed Ubuntu/manylinux builds remain
distinct; source/build correspondence, actual FP behavior and computed-domain
closure are still unqualified. No allowance, code/test change or numerical run
occurred, and old verdicts/flags remain unchanged. This review is exhausted.
Next proposed, not approved: a documentation-only same-row qualification
protocol specifying the missing build/FP/reference/domain evidence and stop
conditions, without package acquisition, environment changes, numerical studies,
implementation or bound adoption. Collection/runtime and broader gates stay closed.

#### Primitive Qualification Protocol Draft (2026-11-03)

The user's continuation approved this documentation-only preparation
(REVIEW.md §101), not the protocol's adoption or execution. It refines the
existing ten-row plan using §§99-100's identity/source findings; it does not
replace the [integrator][c1-motion-source],
[owner/reference/checker][c1-prototype-source] or their verdicts. Proposed
default: require the following evidence before recommending any allowance.
No row is qualified by this draft, and no numeric tolerance is selected.

**Proposed evidence worksheet, not a runtime schema.** Each row would carry
its exact expression/operation order, real local target, units, operand bit
patterns and dtype/shape, domain with branch coverage, implementation identity,
reference/proof identity and uncertainty, error formula and dependencies,
evidence classification, unresolved reason and invalidation conditions.
Classifications distinguish assumptions, source descriptions, independently
justified uniform bounds and diagnostic residuals. Empty evidence is not zero
error; a hash or finite residual is not a uniform bound. Any later worksheet
exporter, checker, package acquisition or evidence run needs separate approval.

**Ordered evidence gates, proposed and not executed:**

1. **Q0: Claim and input binding.** Name the existing private constant-twist
  model, exact binary-step duration, seed/epoch and at most eight consecutive
  events (seven advances), exact stored twist and pose, owned scene/goal and
  same-stored-pose local target. Keep the nominal clock separate. Characterize
  actual conversions rather than assuming Scenario annotations coerce values.
  An unsupported stored goal representation remains unresolved, not silently
  cast to a newly adopted dtype or excluded by a new input restriction.
2. **Q1: Source/build/path correspondence.** Bind current project bytes,
  CPython scalar/math wrappers, NumPy generated scalar/ufunc/fixup paths and
  versioned libm implementations to loaded images and the applicable patched
  source/build records. Record compiler/ABI/options and conversion paths.
  Upstream tags and latest Ubuntu changelog entries alone cannot close this
  gate. NumPy target metadata is not a trace of the selected short-array loop
  or libm IFUNC. Missing correspondence stops claims about that implementation.
3. **Q2: Execution arithmetic contract.** Establish the relevant process-local
  rounding direction, intermediate precision, contraction/FMA and subnormal/
  signed-zero/overflow behavior for every selected path. Bind evidence to the
  producer execution and invalidate it when those properties can change.
  Neither float_info.rounds nor an earlier inspector process establishes this
  contract. Do not change FP mode or environment to make the claim succeed.
4. **Q3: Independent uniform error argument.** For basic arithmetic/conversion,
  enclose exact operations and justified rounding under Q1/Q2, including
  absolute near-zero/underflow error. For sinc/trig/atan2/remainder, require a
  supported uniform contract or independently checked complete decomposition,
  including range reduction and exceptional branches. Existing rational
  integral/pi enclosures can supply real targets, not implementation errors.
  A second call through the same libm is not independent; a high-precision
  reference would need its own justified uncertainty and provenance. Sampled
  agreement, glibc goals and known-test maxima remain diagnostic only.
5. **Q4: Computed-domain closure and composition.** Propagate prior input/error
  intervals through the ordered program before invoking each row's argument.
  Cover every reachable branch and conversion, denominator/norm separation,
  cancellation, source scale and wrap cuts. Compose supported local errors
  into the existing seed-based recurrence; do not reset on later stored events
  or held receipts. A domain escape or missing upstream row stops dependent
  bounds, not unrelated bookkeeping or already-established source identity.
6. **Q5: Review and separate adoption.** Record exactly which claim, domain and
  implementation the evidence supports, independent checking and unresolved
  obligations. A completed proof dossier is a recommendation, not automatic
  checker integration, numerical certification, physical qualification or
  runtime/data approval. Any adoption or implementation requires a separate
  explicit scope and its applicable regression gates.

**Row-specific proof/check matrix, not executed:** the real targets and
expressions remain those of the ten-row ledger above. This matrix makes the
required argument and failure boundary explicit, without inventing allowances.

| Row | Required Proof or Check | Stop Condition |
| --- | --- | --- |
| P1 | Exact stored omega-duration product and supported C-double rounding, including signed zero/subnormal results. | Missing scalar build/FP contract, overflow or uncovered product domain. |
| P2 | Ordered division/addition enclosure, including P1 input error and midpoint cancellation. | Any division/addition or propagated midpoint branch outside its proved domain. |
| P3 | Independent real-pi enclosure, exact stored pi identity, ordered denominator multiplication/division and P1 error. | Nonseparated denominator, missing constant/rounding evidence or unsupported argument interval. |
| P4 | Complete asanyarray/comparison/where/pi-product/sine/division argument at the exact stored q; include both signed zeros, the tiny substitution and nonzero small arguments. | Missing scalar/0-D/conversion or libm path evidence, uncovered zero/subnormal branch or unproved division; never assign one from the definition alone. |
| P5 | Exact speed-duration product and actual NumPy result/promotion route; compose P3 argument uncertainty and P4 local error once. | Unproved sinc result type or product rounding, or duplicated/omitted argument/constant contribution. |
| P6 | Scalar math conversion/trig enclosures plus selected real length-two coordinate products/additions at retained source scale. | Missing installed loop/IFUNC/FP evidence or unsupported coordinate magnitude/cancellation; an AVX2 label is insufficient. |
| P7 | Ordered additions, versioned fmod, sign correction/signed zero and final subtraction with real-pi and inherited angle error; retain circular branch sets. | Uncovered remainder/cut branch, unproved sign-correction arithmetic or reliance on bare wrapped subtraction. |
| G1 | Converted stored heading, both trig enclosures, norm separation and complete atan2 wrapper/quadrant/cut argument. | Possible zero norm or unproved conversion/kernel/cut; never feed this goal-only normalization into the motion recurrence. |
| G2 | Actual goal array inference/promotion, same stored position subtraction and G1-to-trig error propagation. | Unsupported stored goal dtype/conversion, scale or subtraction/trig domain; the pose cast does not qualify goal arithmetic. |
| G3 | Ordered promoted component products/sums, any narrowing to Python float, cancellation and goal lever arm. | Missing conversion/contraction/error evidence or adding accumulated ideal-position error to the same-stored-pose target. |

**Error accounting and proposed comparison.** P4's local error compares its
output at the exact stored q with real normalized sinc at that q. P3 then
relates q to the ideal angle; P5 must not charge that argument uncertainty
twice. Similarly, local step errors start from the same stored pose; the
existing accumulated position/heading recurrence adds inherited motion error
once. G1-G3 concern the current stored-pose goal transform, not an ideal-pose
goal. Conversion to wire binary32 and host-round-trip verdicts stay separate.

For a future comparison, let R enclose the independent real target and let E
be a supported implementation-error set in the same units. For exact stored
result O, the compatible real-target set is O-E. Whole-reference containment
R within O-E supports consistency under that candidate claim; disjointness
supports inconsistency of that claim; mere overlap stays unresolved. Use
circular sets and all supported branches for angles. Missing Q0-Q4 evidence
permits neither a supported pass nor a numerical inconsistency claim. Refine
reference uncertainty only within a separately authorized method/budget; never
enlarge E, discard branches or select the nearest reference to get containment.
This proposed rule does not modify the existing checker or its classifications.

**Invalidation and acceptance checks, proposed only.** Invalidate dependent
proofs on source/build/dispatch, dtype/shape/conversion, FP contract, domain,
seed/epoch/twist/time or goal/source-scale changes. A restart needs current
evidence binding, not a historical gate rerun treated as provenance. Planned
controls cover missing/changed evidence, zero/tiny/subnormal/cancellation,
wrap/atan2 branches, inferred goal types, both clocks, seven-step accumulation,
same-stored-pose goal accounting, containment/disjointness/overlap and freshly
bound producer faults that an actual supported argument must discriminate.
No fixtures, residuals, proof tools, sample counts or future execution budget
are selected or run by this preparation.

**Exit and next authorization.** This package exits with the worksheet fields,
six ordered gates, exactly ten proof/stop rows, accounting rules and invalidation/
acceptance controls documented; it does not exit with qualified primitives.
All current rows and qualification flags remain unresolved/unchanged. The next
recommended bounded candidate is a read-only CPython correspondence dossier
for P1-P3/P7: inspect already-installed identity/build metadata and official
public patch/build pages for the exact Ubuntu source package and amd64 build.
Record whether those records bind the current scalar/remainder paths; report
gaps rather than assuming equivalence. This candidate is not approved here;
no package/archive download, install, environment change, numerical/fixture
execution, code change, bound adoption or integration follows. If those pages
cannot establish correspondence, stop with that precise missing evidence before
proposing source acquisition or another proof route. Task 6/9, physical,
representative task-quality and hardware gates remain independent and blocked.

**CPython correspondence outcome (REVIEW.md §102).** The separately approved
read-only P1-P3/P7 dossier identifies the exact public Ubuntu applied source
and amd64 build metadata. Applied `Objects/floatobject.c` agrees textually with
upstream v3.12.3, including all five relevant scalar/remainder slots. This is
source-text evidence only: public archive checksums and matching local package
records do not independently bind the installed executable to that build.
Packaging rules define sysconfig flag rewriting and distinct static/shared/LTO
paths, so reported flags are not a per-object compile record. Generic versus
specialized dispatch and current fmod resolution remain unresolved. The public
build's glibc development version differs from the installed runtime package;
neither declaration supplies a live libm/FP contract or uniform error theorem.
This result completes the dossier, not Q1 or any numerical qualification gate.
The protocol, all ten error rows, old verdicts/flags, code/bounds and helper
`1bb89fe` mathematical-only scope remain unchanged.

Next proposed, not approved: same-four-row static CPython path inspection using
the pinned official generated-interpreter pages and existing executable symbols/
disassembly tools, capped at five named entry points and 64 KiB of extracted
disassembly, with missing mappings reported as gaps. No executed-path claim
follows from static possibilities. No numerical/fixture/producer execution,
debug/source/package acquisition, dependency/FP-mode change, proof/code/bound
adoption, collection or integration is included. All approved scopes are
exhausted; independent physical/task-quality/data/runtime gates remain blocked.

**Static path outcome (REVIEW.md §103).** The separately approved bounded
P1-P3/P7 review maps five public numeric APIs to the unchanged executable,
not the float-slot, generated-case or live-dispatch implementation. Exact
generated source describes direct exact-float add/subtract/multiply cases and
generic table dispatch; those alternatives need not pass through the inspected
APIs. Compiled cases, indirect callees, pi/conversion/result-storage and FP/
uniform-error/domain evidence remain unbound. Missing local symbols or nearest
export labels cannot be replaced by guessed mappings. No qualification gate,
allowance, producer/reference, protocol or old verdict/flag was changed.

Next proposed, not approved: a design-only controlled-arithmetic alternative for
these same four rows in the private synthetic motion producer. Compare explicit
binary64 rounding and rational/interval remainder branches against retaining
CPython dispatch, with compatibility/cost uncertainties, proof and stop checks.
No implementation/adoption, integrator/reference change, bounds, dependencies,
numerical/fixture execution, collection or runtime integration follows. All
approved scopes are exhausted; physical/task-quality/data/hardware gates remain.

[c1-motion-source]: ../../sim/rover.py
[c1-prototype-source]: ../../sim/diagnostics.py
[floor-rules]: ../../sim/rules.py
[floor-rules-report]: ../../sim/reports/rules-baseline-20261020.json
[teacher-evaluation]: ../../teacher/evaluation.py
[synthetic-evaluation-report]: ../../teacher/reports/evaluation-synthetic-20261016.json
[evaluation-tests]: ../../tests/test_evaluation.py
[pytorch-distillation]: https://docs.pytorch.org/tutorials/beginner/knowledge_distillation_tutorial.html
[crivo-32m]: https://huggingface.co/tardellirs/crivo-32m
[native-tof-wall-word-review]: ../review/231-235.md#231-selected-native-tof-wall-word-residuals-2026-11-10
[native-tof-wall-trace-review]: ../review/231-235.md#232-actual-native-tof-wall-calculation-trace-2026-11-10
[native-tof-wall-acquisition-review]: ../review/231-235.md#233-actual-fresh-tof-wall-acquisition-pairing-2026-11-10
[native-tof-wall-intake-review]: ../review/231-235.md#234-bounded-native-tof-wall-intake-2026-11-10
[native-tof-wall-history-review]: ../review/231-235.md#235-bounded-native-tof-wall-history-preflight-2026-11-10
[native-tof-wall-retention-review]: ../review/236-240.md#236-bounded-native-tof-wall-recorder-retention-2026-11-10
[native-tof-wall-delivery-review]: ../review/236-240.md#237-native-tof-wall-deliveredpending-correspondence-2026-11-10
[native-tof-wall-offset-review]: ../review/236-240.md#238-native-tof-wall-offset-word-residuals-2026-11-10
[native-tof-wall-division-review]: ../review/236-240.md#239-native-tof-wall-division-word-residuals-2026-11-10
[native-tof-wall-arithmetic-review]: ../review/236-240.md#240-matched-native-tof-wall-arithmetic-diagnostics-2026-11-10
[native-tof-wall-projection-review]: ../../REVIEW.md#241-native-tof-wall-projection-expression-residuals-2026-11-10
[native-tof-wall-projection-match-review]: ../../REVIEW.md#242-matched-native-tof-wall-projection-diagnostics-2026-11-10
[native-tof-wall-mask-candidate-review]: ../../REVIEW.md#243-native-tof-wall-maskcandidate-word-correspondence-2026-11-10
[native-tof-wall-minimum-review]: ../../REVIEW.md#244-native-tof-wall-minimum-word-correspondence-2026-11-10
[native-tof-wall-selection-match-review]: ../../REVIEW.md#245-matched-native-tof-wall-selection-diagnostics-2026-11-10
[native-tof-cylinder-trace-review]: ../../REVIEW.md#246-actual-native-tof-cylinder-quadratic-trace-2026-11-10
[native-tof-cylinder-stages-review]: ../../REVIEW.md#247-actual-native-tof-cylinder-sidetop-trace-2026-11-10
[native-tof-cylinder-acquisition-review]: ../../REVIEW.md#248-actual-fresh-tof-cylinder-acquisition-pairing-2026-11-10
[native-tof-cylinder-intake-review]: ../../REVIEW.md#249-bounded-native-tof-cylinder-intake-2026-11-10
[native-tof-cylinder-history-review]: ../../REVIEW.md#250-typed-cylinder-history-prehash-guard-2026-11-10
[native-tof-cylinder-retention-review]: ../../REVIEW.md#251-explicit-cylinder-recorder-retention-2026-11-10
[native-tof-cylinder-delivery-review]: ../../REVIEW.md#252-delivered-and-pending-cylinder-correspondence-2026-11-10
[native-tof-cylinder-offset-review]: ../../REVIEW.md#253-supplied-word-cylinder-offset-discrepancies-2026-11-10
