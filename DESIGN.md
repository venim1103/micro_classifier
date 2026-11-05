# Micro Classifier Design

Status: Proposed design; host-side teacher tooling started (§4).  
Research date: 2026-10-13; revised after the independent [review](REVIEW.md) and
its second update (2026-10-14).  
Target: STM32N6 with Neural-ART, initially an N657 development board.

This document records the feasibility findings, recommended architecture, and
validation plan for a Jev-like embedded decision module: an STM32N6 board that
answers a fixed catalogue of typed questions for a host robot (§2). It
incorporates the final student-distillation discussion in the user-provided
Idea0.pdf, approximately pages 163-189, research into published Vela and
Decision implementations and ST tooling, and the corrections from
[REVIEW.md](REVIEW.md), which holds the detailed evidence.

Hardware and software constraints below are source-verified. Architecture,
memory budgets, and milestone gates are proposals, not measured results or
approved product requirements unless explicitly confirmed in §2. Project
measurements cover teacher precision/resources (§4) and synthetic simulator
smoke episodes (§7). No
student training, ST compiler execution, firmware build, or physical-board
benchmark has been performed.

## 1. Decision Summary

**Current pilot decision (2026-10-20):** the user approved a rules-first rover
with `path_blocked`, `clear_sector` and `speed_tier`, excluding `mode` from the
active catalogue. The complete three-question host contract is implemented
below; the existing sensor proxies are still diagnostic, not qualified runtime
rules. Correct the sensor/scene model before data collection. Learned predictive
and camera questions, a student and distillation remain future work, not a
requirement to imitate these rules. REVIEW.md §72 records the decisions and
verification. The broader learned architecture below remains the long-term
direction, not evidence of a trained or deployed model.

Build a modular decision module: an STM32N6 board that attaches to a host robot
(first a ground rover, later a mini-drone) and answers a fixed catalogue of
typed questions about the robot's state and surroundings on every tick. Train
its micro-student on reviewed examples, on deterministic or simulator labels
where the answer is computable, and on genuine decision distributions from an
open teacher for perceptual and semantic questions (Decision 3.0 d3-flash in
INT8 on the 12 GB development GPU first, confirmed by a measured bake-off).
Start with static INT8 inference and shared trunks of operators that map
efficiently to Neural-ART: convolution and ReLU. Use the Cortex-M55 for bounded
preprocessing, the per-question heads, probability calculation, calibration,
and rejection. The host's own controller keeps actuation, inner control loops,
interlocks, and fail-safe behaviour.

Do not start by compressing an existing Vela model into ternary weights or by
assuming the PDF's small transformer will execute entirely on the NPU. First
prove export, quantization, hardware mapping, and internal-memory deployment
with a minimal model. Then establish task accuracy and the benefit of
distillation before expanding functionality.

| Capability | Feasibility assessment |
| --- | --- |
| Known tasks, fixed labels, typed results and probabilities | Credible initial scope |
| Tactical decisions for a host robot at 10-50 Hz from ego-state and on-module perception (ToF, camera) | Credible; the module recommends, the host acts and keeps its fail-safes |
| Low-level control (motor commands, attitude or rate loops) | Out of scope; stays on the host controller (§2) |
| One module on several robot frames | Credible as versioned embodiment profiles, each validated on its own frame (§6) |
| Several known tasks sharing an encoder | Credible after single-task validation |
| Runtime-defined options within a bounded domain | Research extension; requires option-conditioned training |
| New in-domain questions as host-trained heads on a frozen trunk | Credible if trunk features transfer; each head passes the same gates (§6) |
| Arbitrary new questions, rubrics, and broad world knowledge | Not a credible first target in a few megabytes |
| Direct Vela 2.0 or Decision 3.0 execution in internal SRAM | Outside the memory budget; the smallest open general Jev-style model found, [Crivo-32M][crivo-32m], is about 30x the constant budget |
| Hosted Jev API as teacher, label source, or imitation target | Not permitted: TypeSafe's [customer agreement][typesafe-mca] §2.3(b) forbids distillation and imitation |

Preserving an API shape is not preserving the teacher's capability. The first
version must explicitly reject unsupported task IDs, schema versions, or
options instead of implying general Jev or Vela compatibility.

## 2. Goals, Boundaries, and Open Requirements

### Goals

- Execute the deployed classifier offline on the microcontroller, without a
  hidden host-side encoder or cloud inference dependency.
- Return structured decisions and useful probability distributions without
  generating text tokens.
- Establish reproducible data, teacher labeling, training, export, firmware,
  and target validation workflows.
- Prove memory placement and end-to-end latency rather than infer them from
  parameter counts or advertised peak NPU throughput.
- Make unsupported inputs and uncertainty explicit, with application-defined
  rejection and fallback behaviour.
- Serve as a frame-agnostic decision module for host robots: a versioned
  binary interface, per-frame embodiment profiles, and explicit rejection that
  the host maps to its own fail-safe.

### Initial Non-Goals

- General-purpose language generation or reproducing all Vela functionality.
- On-device training or online weight updates.
- A new ternary runtime, a general BitNet port, or custom attention kernels.
- Flight or motor-control firmware, or treating a learned classifier as a
  safety-certified controller. The module integrates with the host's controller
  (on a drone, an established flight stack such as PX4 or ArduPilot).
- Assuming a European-headquartered supplier proves the origin of every die,
  assembly step, or board component.

### System Role and Module Interface

The deployed STM32N6 board is a decision module, not a robot controller.

| Layer | Owner | Responsibilities |
| --- | --- | --- |
| Decision module (STM32N6) | This project | Validate state packets, run the student on ego-state and on-module perception, return typed decisions, distributions, confidence, and an explicit status |
| Host frame controller | The robot frame (rover MCU, drone flight controller) | Inner control loops, actuation, hard limits, geofences, interlocks, and the frame's own fail-safe on rejection or timeout |

Interface contract, fixed in M0 and versioned with every release:

- Transport: UART with DMA first; CAN-FD (the N6 has three FDCAN controllers)
  or SPI if needed. Keep decision semantics independent of the transport. For
  PX4 or ArduPilot hosts, a thin adapter maps decisions to [MAVLink][mavlink] or
  [DroneCAN][dronecan] messages.
- State packet, host to module, every tick: protocol, schema, and embodiment
  profile versions; sequence number and timestamp; a validity bitmask and
  per-field sensor ages; ego-state in one documented body frame and SI units
  (PX4 uses FRD body axes, ROS uses FLU per [REP 103][rep-103]); goal vector;
  health (battery, faults); an enumerated task ID. The module keeps the short
  history window itself, so each packet carries only the current sample.
- Decision packet, module to host: sequence echo, latency, status (`OK`,
  `REJECT_LOW_CONFIDENCE`, `REJECT_STALE_INPUT`, `REJECT_OUT_OF_DOMAIN`,
  `REJECT_UNSUPPORTED_SCHEMA`, `FAULT`), per-question distributions and
  selections, confidence, and model and catalogue versions.
- Liveness: the host treats a missing or late decision packet as a rejection.
  PX4 already enforces this for offboard control: it needs a proof-of-life
  stream of at least 2 Hz and runs its configured fail-safe when the stream
  stops ([PX4 offboard mode][px4-offboard]).
- Fail-safes stay frame-specific on the host: a rover brakes to a stop; a
  multicopter must never cut its motors and instead holds position or lands
  under its flight controller.
- Perception sensors that define the student's input (camera, multizone ToF)
  belong on the module with a fixed mounting pose per embodiment profile,
  because their placement changes the input distribution. The host supplies
  ego-state over the bus.

### Provisional Host-Side Contract v0 (2026-10-15)

The user approved this **draft** as host-side tooling, including codecs, a C
header, CRC, golden vectors and simulator export. It does not freeze hardware,
physical thresholds, label policy, calibration, smoothing or fail-safes.
[Python definitions][wire-python] are the single source of truth. The generated
[C header][wire-header] contains byte offsets, not packed structs. [Golden
frames][wire-golden] are synthetic fixtures, not predictions or reviewed labels.

All integers are unsigned little-endian; floats are little-endian IEEE-754
binary32. No implicit alignment or padding. The 20-byte header is:

| Offset | Field | Encoding |
| --- | --- | --- |
| 0 | Magic | Two bytes `MC` |
| 2 | Protocol version | u8, 0 |
| 3 | Kind | u8, state=1 or decision=2 |
| 4 | Payload length | u16, excludes header/CRC |
| 6 | Schema version | u16, 0 |
| 8 | Embodiment profile ID | u16, ground rover=1 |
| 10 | Profile version | u16, 0 |
| 12 | Sequence | u32, echoed by decision |
| 16 | Host sample timestamp | u32 microseconds, echoed by decision |

The four-byte trailer is CRC-32/ISO-HDLC over header and payload, including
magic/length, serialized as little-endian u32. Reflected polynomial
`0xedb88320`, initial/final XOR `0xffffffff`; ASCII `123456789` has check value
`0xcbf43926`. CRC detects corruption, not authentication or malicious forgery.

State payload offsets are relative to payload start:

| Offset | Field | Encoding and meaning |
| --- | --- | --- |
| 0 | Validity | u16, bits 0-4: velocity, angular velocity, goal, battery, faults |
| 2 | Task ID | u16, goal reaching=1; others rejected |
| 4 | Sensor ages | Five u32 microsecond ages, validity-group order |
| 24 | Linear velocity | Three f32, FLU body X/Y/Z, m/s |
| 36 | Angular velocity | Three f32, FLU body X/Y/Z, rad/s |
| 48 | Goal displacement | Three f32, FLU body X/Y/Z, m |
| 60 | Battery fraction | f32 in [0,1], not volts |
| 64 | Host fault flags | u32; physical bit meanings still pending |

State payload is 68 bytes; full frame is **92 bytes**. Invalid groups must
carry zero values and age `0xffffffff` (unknown); valid groups require known
ages. Values must be finite and representable as binary32. Unknown validity
bits and unsupported task/schema/profile versions are rejected. Physical
range and stale-data limits remain profile-policy work. ToF, its ages/masks,
and the history window stay on the module, not in host UART frames.

Decision payload starts with u32 processing latency in microseconds, u16
status, u16 model version, u16 catalogue version, and u16 answer mask: a
12-byte prefix. Latency is complete input receipt to response framing, not
host-to-host elapsed time. Model version 0 means no model; whether it can
accompany `OK` depends on the catalogue below. Catalogue 1 is the active
rules-only pilot; catalogue 0 is retained for legacy compatibility. Status values 0-5 are `OK`,
`REJECT_LOW_CONFIDENCE`, `REJECT_STALE_INPUT`, `REJECT_OUT_OF_DOMAIN`,
`REJECT_UNSUPPORTED_SCHEMA`, `FAULT`. Default construction yields `FAULT`.

Answer-mask bit `question_id - 1` indicates an answer; present answers occur
in ascending ID order. Each answer has an eight-byte prefix: u8 question ID,
u8 type (`noul`=1, `choice`=2, `score`=3), u8 selected option index, u8 option
count, f32 confidence; followed by count f32 probabilities. Wire identities
follow the legacy catalogue 0 bundle, not a reviewed training-label catalogue:

| ID | Question | Ordered options |
| --- | --- | --- |
| 1 | `path_blocked` | false, true |
| 2 | `clear_sector` | left, centre, right, none |
| 3 | `speed_tier` | 0, 1, 2, 3 |
| 4 | `mode` | explore, approach, avoid, dock, halt |

Probabilities are not renormalized by the codec: finite, in [0,1], sum within
1e-6 of one. Choice/score confidence uses the TypeSafe Jev formulas (§6) on
serialized probabilities; ties choose the first raw mode. Noul confidence is
absent, represented by -1, not NaN. Received confidence must match within
2e-6. Expected score is the probability-weighted level. A selected option may
differ from raw argmax for future smoothing; no smoothing policy is implemented.

For legacy catalogue 0, `OK` requires all four answers and a nonzero model version. Rejection/fault
may contain a subset or none for diagnostics; **its selections are not usable
recommendations**. Full decisions are **128 bytes**; empty rejection/fault
frames are 36 bytes. Golden model ID 1 is synthetic, not an installed model.

#### Active Rules Catalogue 1 (Approved, 2026-10-20)

The user approved the three-question contract milestone and the rules-first
pilot direction. Catalogue 1 contains only IDs 1-3 with the same types, options,
confidence and ordering above. `OK` requires mask `0x7`. Every status requires
model version **0**, explicitly identifying no trained model; the pair
`(catalogue_version=1, model_version=0)` denotes the rules path. No fictitious
model ID or five-option mode distribution is needed. Rejections/faults permit
subsets or no answers, but never mode or a nonzero model version. Their answers
remain unusable recommendations. This tuple declares provenance, not algorithm
attestation, calibrated probabilities or safety qualification.

Python `Decision` defaults to catalogue 1 and `FAULT`, not `OK`. In the
[registry][wire-python], `RULES_QUESTIONS` is the active catalogue and
`CATALOGUES` selects definitions by version. Existing `QUESTIONS` and
`CATALOGUE_VERSION` retain their legacy meaning for diagnostic tools. C callers
explicitly set `MC_V0_RULES_CATALOGUE_VERSION`, `MC_V0_RULES_MODEL_VERSION` and
`MC_V0_RULES_ANSWER_MASK`. Zero-initialized C metadata remains legacy catalogue
0, not an implicit active-catalogue selection. Consumers must check the catalogue
and status before treating a decoded packet as an active-pilot result.

Full rules decisions are **100 bytes**; empty faults/rejections remain 36 bytes
and state frames 92 bytes. Header/schema/profile versions, CRC, field offsets,
legacy frame bytes and the 128-byte stream capacity are unchanged. Historical
goldens and reports remain byte-identical; four-head synthetic assembly/verifier
fixtures explicitly select catalogue 0 and cannot emit rules-catalogue frames.
The existing `sim/catalogue.json` is still the historical diagnostic proxy draft,
not the active runtime catalogue or a promoted task label source.

All 640 interface tests pass, including 123 new cases, exact constructed rules
bytes, all six statuses and sixteen masks, C/Python round trips/streams, idle
recovery, rejected-output atomicity and model/version confusion. Native ASan/
UBSan covers rules frames, exact capacities and truncations; host/hard-float
Cortex-M55 objects and generated header parity pass. The full offline suite has
1,301 passes plus the known transformer xfail; lint, changed-file formatting and
editor diagnostics pass. This resolves F19 for the active contract, not Task 6's
rule/evidence qualification, an M2 baseline, firmware integration or deployment.
No task data, study, labels, model inference/training or hardware action occurred.

`FrameDecoder.feed` accepts byte chunks, bounds retained framing data, rejects
corrupt/unsupported frames and resynchronizes on magic. The transport owner
calls `FrameDecoder.flush()` on a chosen inter-byte timeout to recover complete
valid frames behind incomplete candidates before discarding remaining fragments.
Do not reset first. Flush preserves rejection counters; no timing threshold or
new framing format is imposed here. Missing/late decisions, duplicates,
out-of-order packets and gaps remain application duties. Sequence and timestamp
wrap modulo 2^32; compare
time differences modularly within less than half that range and use sequence
echo plus host receipt time. Timestamp wrap is about 71.6 minutes, not a
wall-clock timestamp. Independent frame-specific host fail-safes still apply.

At 1 Mbaud **assuming 8N1**, 92+128 bytes cost a calculated 2.2 ms of line
time, excluding inference, buffering, scheduling and host handling. This is
not measured latency. All 62 focused tests pass, including header equality,
host/Arm GCC compilation and independent C state serialization matching a
golden frame. Header syntax checks are not firmware or ST NPU validation.

#### Host-Only C Codec (Approved, 2026-10-19)

The user separately approved portable host-only C parsing, CRC and bounded stream
recovery, host/golden tests, Arm compile checks where available, documentation
and local commits. This does not authorize board integration, broader firmware
runtime, dependencies, physical/evidence-policy changes, labels/training or an
interface freeze. The existing byte contract and generated constants remain
unchanged.

The [C11 codec API][wire-codec-api] and [implementation][wire-codec-source]
decode state and decision frames using explicit little-endian reads and
`memcpy` for float bits, without packed casts, allocation or HAL. Caller outputs
are written only on success; native structs are not wire layouts. State guards
match Python validity/age/zero/finite/health rules. Decision guards preserve
fixed ordering, all status/subset rules, separate selections, full distributions,
first-mode tie handling and existing probability/confidence tolerances. A valid
rejection/fault packet remains unusable as a recommendation. CRC is corruption
detection, not authentication; stale/range/timeout/sequence and fail-safe policy
stay outside the codec. Binary32 float, at least binary64 double precision and
non-fast-math compilation are required.

Core verification: all five golden frames, all 32 state-validity combinations,
float32 extremes/signed zero, decision subsets/ties/nonbinary fractions, byte
corruption, truncation, invalid layouts/values and unchanged failed outputs pass.
There are 46 new C checks, 108 interface tests and 713 repository passes plus
the known transformer expected failure; lint/format pass. Host GCC 13.3 and
Arm GCC 13.2 compile real objects, the latter with `-mcpu=cortex-m55 -mthumb`.
This is neither a linked firmware build nor target execution, timing, memory-fit
or physical-safety evidence. The approved stream follow-up is recorded below;
history, heads/inference, application rejection and hardware remain gated.

Stream completion (2026-10-19): `mc_v0_stream_init` and `mc_v0_stream_feed` use a
128-byte framing buffer plus fixed metadata, no allocation, and callbacks for
all complete validated packets. Bad framing/CRC/semantics are discarded with
bytewise magic recovery; rejected-candidate counts saturate at `UINT32_MAX`.
The callback packet is borrowed until callback return: copy any retained data.
Serialize access to each stream; callbacks must not feed/flush/reset that stream.
Feed success means the chunk was processed, not that a packet or recommendation
was produced. For caller-declared idle recovery, use `mc_v0_stream_flush` with
the callback and context, matching Python's flush behavior above. Init remains
a full stream reset and clears counters. No timeout threshold is adopted.

Additional checks cover every two-chunk split and bytewise delivery of all five
goldens, single-bit corruption in each golden byte, impossible/unsupported and
semantic faults, two nested packets released after one final corrupt-candidate
byte, 100,000 noise bytes, counter saturation, resets and invalid arguments.
Python and C agree on 2,000 seeded CRC-repaired mutations and packet/buffer/
counter results throughout a seeded mixed stream. Eight binary32 tolerance-edge
cases agree. ASan/UBSan pass exact-size golden prefixes/extra bytes and 4,096
random buffers. Compile-time guards reject changed v0 version/capacity
assumptions and fast/finite-only math; these force codec review, not an interface
freeze. All 67 C checks, 129 interface tests and 734 repository tests pass plus
the known transformer expected failure; host/Cortex-M55 object, lint/format/
editor gates pass. These finite checks are not formal memory, numerical, WCET
or physical-safety certification. The approved host-C package is complete with
no linked firmware, hardware execution, study/log generation, annotation,
inference/training, dependency/download or evidence-policy change.

Review repairs (2026-10-19, REVIEW.md §71) add idle flushing without changing
the wire layout, golden frames or 128-byte C buffer. Python encoding also checks
probability sums after binary32 rounding and rejects oversized numeric inputs
with `ProtocolError`. Host and Arm tests include recovery, native sanitizers and
explicit hard-float ABI attributes. Historical object-size reports retain their
original soft-float flags and are not sizing evidence for the corrected build.

Encoder extension (separately approved, 2026-10-19): the user approved caller-
buffer C state/decision encoding, Python/golden round trips, host/sanitizer/Arm
checks, documentation and local commits only. `mc_v0_encode_state` and
`mc_v0_encode_decision` share state validation, fixed answer schema, prefix rules
and confidence arithmetic with decoding. They build a fixed temporary frame,
then copy exactly the encoded length and set `written` on success; failures
leave both caller outputs and source unchanged. No packed structs, allocation,
HAL, wire/default/policy change or interface freeze is introduced.

The caller supplies valid nonoverlapping source, destination and length objects
and a truthful writable capacity. All pointers must be nonnull, even for zero
capacity; no size-query mode is provided. Success is `MC_V0_ENCODE_OK` (the same
zero value as decode success); errors preserve the existing numeric values.
State is 92 bytes; decisions are 36-128 bytes according to the answer mask.
Present answer IDs/types/counts/selections must match the fixed schema. Input
confidence is ignored and recomputed from binary32 probabilities, like Python;
absent answer slots are ignored. Accepted noncanonical received confidence may
therefore canonicalize on re-encoding, not reproduce the original frame bytes.

Core verification: all five existing goldens encode exactly, every supported
decision status/subset matches Python, and short capacity/null/invalid-input
cases preserve buffers, lengths and sources. Thirty new tests, 97 C checks,
159 interface tests and 764 repository passes plus the known transformer expected
failure; lint/format and real host/Cortex-M55 object compilation pass. Encoder-
specific sanitizer and seeded round-trip completion is recorded below.
No linked firmware, board execution, task data, teacher inference,
training, dependency/download, licence or hardware action is authorized.

Encoder verification completed (2026-10-19): encoding now covers all 32 validity
masks and float32 extremes/signed zero, plus 500 seeded synthetic wire states
and 500 decisions. C output exactly matches Python; native decode/re-encode and
both chunked stream paths recover the same canonical packets. Four accepted
noncanonical confidence inputs canonicalize identically to Python. Poisoned
absent slots and unused probability storage do not enter serialized frames.
Caller-buffer canaries include unaligned byte destinations and unchanged
source objects.

The ASan/UBSan harness now tests actual output allocations from zero capacity
through each golden frame's length plus one, preserving bytes/length on short
capacity, matching exact bytes on success and not writing spare capacity.
All 256 u8 option-count values are exercised against the fixed noul layout;
unsupported counts fail without output writes. Existing decoder/stream native
checks, including 4,096 random buffers, continue passing. All 104 C checks,
166 interface tests and 771 repository tests pass plus the known transformer
expected failure; real host/Cortex-M55 objects and lint/format/editor gates pass.
These finite checks are not formal memory/numerical certification, WCET, SRAM
fit or board-runtime evidence. The approved encoder package is complete using
artificial protocol fixtures only, not simulator episodes, task data, live
teachers, training, dependencies or hardware. Broader firmware gates remain.

[wire-codec-api]: firmware/include/micro_classifier_codec.h
[wire-codec-source]: firmware/micro_classifier_codec.c

#### Host-Only State History (Approved, 2026-10-19)

The user separately approved an eight-tick host-state C reference, explicit
caller-declared gaps, synthetic tests, host/sanitizer/Arm checks, documentation
and local commits. The [history API][state-history-api] and
[source][state-history-source] store copied validated native host states in a
fixed ring, without allocation or HAL. This is not ToF history, tensor packing,
an observation adapter, inference or deployed firmware. No timeout, sequence
ordering, interpolation, physical threshold, wire/default or interface freeze
is adopted. The caller determines tick boundaries and calls push or gap once
for each chosen tick; the library never infers missing ticks from metadata.

`mc_v0_state_history_init` clears the ring. Push uses the shared
`mc_v0_validate_state` contract validator: invalid states fail without mutation
or advancement; a null state is an error, not an implicit gap. Explicit gap
insertion advances one slot and clears its stored value/presence. Snapshot
copies eight slots oldest-to-newest, with bit 0 oldest and bit 7 newest in
`valid_mask`. Initial/unfilled and explicit-gap slots are zero placeholders,
not valid state packets; always consult the mask. Slot presence differs from
the state's own sensor-validity bits: a received all-unknown state is present.
Values, sensor ages, sequence and timestamp are not aged, normalized, reordered
or interpreted. Duplicate/backward/wrapped counters are preserved, not accepted
as fresh or policy-qualified merely because they were stored.

Initialize before use, do not alter internal fields, serialize access and use
valid nonoverlapping source/history/snapshot objects. Snapshot/source changes
cannot mutate retained history. Nonnull operations return `MC_V0_HISTORY_OK`
(zero) on success; argument or validation errors leave affected outputs/history
unchanged. Init accepts null as a no-op, like the stream initializer. Existing
codec error numbers, state-validation rules, byte format and all golden frames
are unchanged; the validator is newly exposed for sharing rather than duplicated.

Core checks: 13 history cases cover warmup masks, repeated wraparound, explicit
gaps, zero placeholders, invalid-state atomicity, separate presence/sensor masks,
float32 extremes/signed zero, source/snapshot ownership, reset, null arguments
and damaged cursors. Both sources compile to host and Cortex-M55 objects.
The completed follow-up adds a 1,024-operation seeded comparison against an
independent Python queue, with resets, gaps, rejected pushes and exact serialized
state comparisons at every snapshot. Native ASan/UBSan passes a further 1,024
mixed history operations, copy/mask checks, null arguments and all 248 invalid
uint8 cursor values (8-255), with unchanged history/output on rejection, alongside
existing codec safety checks. All 120 C checks, 182 interface tests and 787
repository tests pass plus the known transformer expected failure; lint/format,
editor diagnostics, documentation checks and host/Cortex-M55 objects pass.
REVIEW.md §§57-58 record the core checkpoint and completion. These finite checks
are not timing, SRAM-fit or formal memory-safety evidence. The approved package
is complete, not authorization for linked firmware, board execution, physical/
stale-data qualification, complete student input history, task data, model
runtime/training, dependencies or hardware action.

[state-history-api]: firmware/include/micro_classifier_history.h
[state-history-source]: firmware/micro_classifier_history.c

### Decisions Required Before Scaffolding

Recorded as provisional defaults on 2026-10-14 ([REVIEW.md](REVIEW.md) §10) so
host-side scaffolding can proceed. The user confirmed these defaults on
2026-10-15, while restricting current implementation to teacher tooling.
The original proposal wording below is retained for traceability; detailed
hardware interface and physical safety parameters remain unfrozen. The
provisional host-side byte contract above was subsequently approved as tooling.

| Requirement | Current status |
| --- | --- |
| First robot frame, task, question bundle, and ground-truth policy | Updated 2026-10-20: rules-first ground rover, three questions (`path_blocked` noul, `clear_sector` choice, `speed_tier` score 0-3), active catalogue 1; mode excluded and learned questions deferred. Privileged simulator truth permitted in principle for geometric/predictive targets, with no data-generation approval (REVIEW.md §72). |
| Input modality and sensor set: ego-state, multizone ToF, camera, text | Provisional default: FLU ego-state from the host plus an on-module 8x8 ToF grid (`VL53L8CX` model) and an 8-tick history window first; camera in a later profile; text only for optional operator commands |
| Languages and maximum input length (text branch only) | Provisional default: English only for optional operator command strings, at most 128 UTF-8 bytes; enumerated task IDs preferred in v0 |
| Fixed task catalogue versus runtime-defined questions | Provisional default: fixed per-profile question catalogue stored as versioned head blobs (§6) |
| Whether external RAM is forbidden | Provisional default: no external RAM during inference (`internal-memories-only--default`) |
| Whether external flash for boot/storage is allowed | Provisional default: external flash allowed for cold boot and weight/head initializers; separate from inference memory |
| Decision rate, end-to-end latency, and power, derived from the frame's speed and stopping distance (§8) | Provisional default: 20 Hz decision rate, at most 20 ms end-to-end latency from state packet to decision packet at nominal clocks (600 MHz CPU / 800 MHz NPU), below 1 W module power |
| Required per-class recall, error costs, and rejection coverage | Missed obstacle 20x worse than a false stop and zero collisions in simulator/arena scenario suites remain provisional gates; the earlier `mode` macro-F1 ≥ 0.85 at ≥ 80% coverage is dormant because mode is excluded from the active pilot, not replaced with an invented threshold. |
| Host interface: bus, protocol, and host stack (custom MCU, PX4, ArduPilot) | Provisional default: UART at 1 Mbaud with CRC-protected binary interface contract v0; rover brakes on rejection or after 150 ms without a decision |
| Simulator for closed-loop data and tests (§7) | Provisional default: minimal Python/NumPy 2-D rover simulator with an 8x8 ToF model, noise, dropouts, latency, and a scripted expert first; PX4 software-in-the-loop with Gazebo later |
| Board selection and any component-origin requirements | Provisional default: STM32N6570-DK for M1b (§12), with `USE_EXTERNAL_MEMORY_DEVICES=0` |
| European sourcing: vendor, design, fab, assembly, components, or software provenance (§10) | Provisional default: vendor and wafer-fab level for the primary MCU (`STM32N657`) and ToF sensor (`VL53L8CX`), with country of origin recorded per part |
| Confidence semantics: TypeSafe Jev or Vela formulas (§6) | Provisional default: TypeSafe Jev formulas on host and device, alongside full probability distributions |
| Commercial use and licence constraints (§10) | Provisional default: commercial product; Apache-2.0 teachers without Jev-derived labels |
| Devcontainer and certificate trust | Resolved: `.devcontainer` (§11) |

The target application is now a robot decision module (clarified on
2026-10-14). Decompose control into atomic yes/no or small-choice questions:
the [JEV-35B card][jev-35b] reports 75% success in a simulated pick-and-place
task for two binary questions per step, against 0% for a direct choice among
eight motor actions. The first task should still be small enough to label
reliably and important enough to make the pilot useful.

## 3. Verified Hardware and Compiler Constraints

### STM32N6

The [STM32N6 family][st-family] includes Cortex-M55 devices with Helium/MVE.
N6x7 variants include Neural-ART; N6x5 variants do not. The
[STM32N657][st-n657] offers a CPU up to 800 MHz, an NPU up to 1 GHz, and
advertised NPU performance around 600 GOPS. Peak throughput is not an
application latency guarantee. Those clocks need overdrive (VDDCORE 0.9 V);
nominal clocks are 600 MHz for the CPU and 800 MHz for the NPU
([ST project guide][st-projects]). Budget latency and energy at nominal clocks
and measure overdrive separately. In ST's recommended asynchronous runtime mode
the core waits in `WFE`, so the NPU, NPU RAMs, and every memory the model uses
must stay clocked in low-power modes.

ST advertises approximately 4.2 MB of contiguous embedded SRAM, organized in
banks. Firmware, stacks, input/output buffers, model constants, activations,
runtime objects, and compiler-generated control data compete for memory. Bank
accessibility, alignment, bandwidth, and security configuration also matter.

STM32N6 has no internal user flash. As described in ST's
[boot example][st-boot], SRAM-loaded development operation is temporary.
Standalone cold boot needs persistent storage or an external loader. Therefore:

- Internal-SRAM inference can avoid external RAM and external weight reads
  during inference.
- External flash may still store firmware and model initializers for boot.
- A debugger-loaded SRAM demo is not proof of a standalone product.
- If all external persistent storage is forbidden, the boot/loading requirement
  must be resolved separately; volatile SRAM cannot retain the application.

### Neural-ART Mapping

The [ST Edge AI Core 4.0.1 operator documentation][st-operators] describes
static input/output shapes and efficient INT8 weights plus INT8 activations.
Supported formats include tensor-oriented ONNX QDQ and fully integer TFLite.
The documented quantization scheme uses symmetric signed weights, asymmetric
signed activations, per-channel weight scales, and per-tensor activation scales.

| Operation or feature | Deployment implication |
| --- | --- |
| Quantized convolution and dense layers with constant weights | Strong initial building blocks |
| Quantized ReLU and supported pooling | Suitable subject to shape/window constraints |
| `MatMul` / `BATCH_MATMUL` | Hardware mapping requires a constant second input |
| Attention score and value products | Variable operands require software fallback, if available |
| Embedding lookup / `Gather` | Software integer mapping |
| Floating-point operations | CPU execution rather than direct NPU execution |
| Dynamic shapes or weight-only quantization | Not the intended efficient deployment path |
| ONNX importer accepts an operator | Does not establish NPU acceleration |

An unsupported hardware operator may use a CPU implementation or cause
compilation failure. Inspect the generated mapping and actual target profiling;
do not assume all fallback paths are available or inexpensive.

The compiler's pooling, broadcasting, kernel, and feature-width constraints
must inform model layout. Even supported operations can be decomposed into
multiple epochs and perform differently from their nominal operation count.

For 1-D text, the documented efficiency rules are concrete: kernels up to 6
wide (stride 1) and 3 high; kernels with a dimension of 1 run efficiently; for
INT8, feature width times input channels should stay at or below 2,048 or the
compiler splits the work, and pooling line buffers share that limit; MaxPool
windows above 3 are decomposed; prime channel counts should be avoided. A
`[1, C, 1, T]` layout with 1x3 kernels exceeds the limit at T = 128 and
C = 128, whereas `[1, C, T, 1]` with 3x1 kernels keeps the width at 1. Compile
both and compare epochs and estimated cycles (§12, M1a).

### Memory Placement and Initialization

The [Neural-ART compiler][st-compiler] provides an
`internal-memories-only--default` profile. Default profiles can permit external
flash and RAM, so default compilation does not prove the proposed constraint.

ST's default memory-pool example splits internal SRAM as follows:

| Region | Size | Use in ST's example |
| --- | --- | --- |
| FLEXMEM and AXISRAM1 | 400 KiB + 624 KiB | Firmware |
| AXISRAM2 | 1,024 KiB | NPU pool |
| AXISRAM3-6 | 4 x 448 KiB | NPU pools, fastest for the NPU |

That leaves about 2.75 MiB for inference and 1 MiB for firmware, enough for the
budgets in §8. For a sub-million-parameter student, memory is not the binding
constraint; task quality is.

The following is documented prospective syntax, not a command already run:

```sh
stedgeai generate -m student_int8.onnx --target stm32n6 \
  --st-neural-art profile-internal-memories-only--default
```

The final application needs a memory-pool configuration and linker layout with
disjoint firmware and inference regions. Check all generated initializers and
control blobs, not only the activation allocation. The `--st-neural-art` option
is essential to select the NPU compilation path rather than M55-only code.

ST's [initializer documentation][st-initializers] makes the application
responsible for copying/loading SRAM-resident weights before inference.
Memory must be enabled and clocked before initialization. Startup loading,
cache maintenance, NPU permissions, RIF/RISAF configuration, and reserved memory
ranges are part of the design, not incidental firmware details.

Use the generated bindings and matching LL_ATON/STAI runtime from one pinned
tool delivery. Do not transplant the PDF's legacy `ai_network_run` example or
handwritten activation allocation into an NPU deployment without validating
the generated contract.

There is no documented host NPU emulator that replaces numerical validation of
the generated implementation on a physical board. The
[NPU validation project][st-projects] and AiRunner provide an appropriate
starting point. The supplied CM55 validation example assumes external-flash
weights and is not a ready-made internal-SRAM CPU comparison.

## 4. Vela Feasibility and Teacher Selection

### Direct Deployment Does Not Fit

The [Vela 0.3B configuration][vela-small-config] uses ModernBERT with 22 layers,
hidden width 768, intermediate width 1,152, 12 attention heads, and a vocabulary
of 256,008 entries.

| Calculation | Result | Limit of the estimate |
| --- | --- | --- |
| Embedding parameters: 256,008 x 768 | 196,614,144 | Embedding table only |
| Embedding storage with one byte per parameter | 196.6 MB / 187.5 MiB | Excludes the rest of the model and quantization metadata |
| Dense packed ternary estimate for 307M parameters | About 60.8 MB | Ideal packing at log2(3) bits/value; excludes all overhead |
| Two-bit packing for 307M parameters | 76.75 MB | Excludes scales, activations, and runtime |
| Linear projections for 128 tokens | About 28.2 GOP | Counts multiply and add separately; excludes attention products and heads |

The ternary estimate assumes a dense representation of arbitrary ternary
values. It is not a claim that every possible sparse or entropy-coded network
has the same storage lower bound. Nevertheless, no validated compression path
has been established that brings these Vela models into the proposed SRAM
budget while retaining their behaviour.

The appropriate route is task-specific distillation into a different
architecture, not a promise of near-lossless compression of the full teacher.

### Use the Real Decision Interface

Vela's [usage documentation][vela-small-usage] and
[implementation][vela-small-code] describe schema-conditioned questions and
options. The initial teacher adapter should use the documented
`system_one(state=..., questions=...)` interface and cache named distributions;
Decision 3.0's runtime exposes the same call with optional `images` and
`videos`. Never use the hosted TypeSafe Jev API as teacher or label source: its
[customer agreement][typesafe-mca] §2.3(b) forbids using outputs to "perform
model distillation" or "train a model to imitate" the service.

- Preserve option identities and ordering, task/schema versions, model
  revision, calibration flags, thresholds, and teacher settings.
- Label exactly the input the student sees: the same rendering, field order,
  and truncation. Otherwise the student learns to predict information it never
  receives.
- Vela 0.3B reads all questions of a call in one bidirectional sequence, so a
  label can depend on the co-asked questions. The decoder members (0.8B, 4B,
  9B) isolate each question ("bundled == single"), and Decision 3.0 encodes each
  question as its own sequence. Test single, bundled, and permuted questions
  before trusting bundled labels, and permute option order during labeling and
  training.
- Use separate teacher and student preprocessing. Student token IDs cannot be
  passed directly to the teacher's tokenizer-dependent model inputs.
- Cache probabilities, and logits where available, at full numerical precision
  rather than rounded presentation strings.
- In Vela, choice `confidence` is the top-two probability margin; TypeSafe Jev
  and Decision 3.0 use other formulas (§6). None is a calibrated probability of
  correctness.
- Additional span questions and long-input windows can require additional
  sequences; one API call is not necessarily one forward pass.
- Span outputs are predictions, not proof of a causal explanation or safety.

### Teacher Candidates, Host Memory, and Precision

| Teacher | Verified reference behaviour | Proposed use |
| --- | --- | --- |
| Vela 2.0 0.3B | Torch reference loads FP32; the official ONNX FP16-encoder path changed choice probabilities by at most 0.006, with no decision changes, on its 230 parity rows; no question isolation | Pipeline pilot and baseline, with bundle-sensitivity tests |
| [Vela 2.0 0.8B][vela-08b] | About 3 GB FP32 parameter memory; isolated questions | Fits the 12 GB laptop GPU unmodified; bake-off candidate |
| Vela 2.0 4B | About 17 GB FP32 parameter memory, plus runtime allocations | One 24 GB GPU with bounded context and batch size |
| Vela 2.0 9B | About 32 GB FP32 with the published loader; backbone projections are stored in BF16; text only | INT8 weight-only loader in `teacher/` fits the 12 GB laptop GPU (measured below); text and operator-command questions |
| [Decision 3.0][d3-collection]: d3-edge 0.59B, d3-lite 0.85B, d3-nano 2.21B, d3-mini 4.54B, d3-flash 8.39B, [d3][d3-card] 26.09B | Apache-2.0; text, JSON, images, and video; one question per sequence; Index 0.3.2 text board 20.2, 32.3, 38.9, 52.6, 55.8, and 66.3; one-request GPU peaks 5.2, 5.7, 9.1, 14.8, 23.8, and 61.8 GiB; training data not disclosed | Primary candidates for the robot module: d3-flash in INT8 on the 12 GB GPU first and d3-mini in BF16 as an exact-precision comparison (below); d3 in INT8 on two RTX 3090s when that host is available |
| autotrust JEV models (JEV-27B, JEV-27B-VL, JEV-35B) | Apache-2.0 weights, but [JEV-27B-VL][jev-27b-vl] trains on a [corpus][jev-corpus] whose main stream holds labels distilled from TypeSafe Jev 1.13; JEV-35B names no training data | Excluded as teachers and label sources (§10) |

The [4B][vela-medium-usage] and [9B][vela-large-usage] GPU paths use BF16
backbone autocast while retaining FP32 parameters and decision components.
Autocast does not make parameter storage BF16.

The inspected [9B custom loader][vela-large-code] rejects lower parameter
loading precision, ignores Transformers quantization options, and its
`device_map="auto"` moves the model to CUDA rather than implementing standard
Accelerate multi-GPU sharding. Two NVLinked 3090s do not automatically become
one pooled memory device. No quantized Vela 2.0 9B has been published, and a
GGUF route would have to rebuild Vela's heads, prefix-sharing forward, and
calibration around a generic backbone.

#### INT8 Vela 2.0 9B on a 12 GB GPU (measured)

[teacher/vela_int8.py](teacher/vela_int8.py) changes only how the weights are
stored. It builds the release model without materializing weights and stores the
ten large projections of every layer (MLP gate/up/down, attention q/k/v/o, Gated
DeltaNet `in_proj_qkv`, `in_proj_z`, `out_proj`) as symmetric INT8 with one
BF16 scale per 128 input columns, expanded to BF16 just before each matmul.
Gates, convolutions, norms, and heads stay FP32 as released, and the FP32
embedding table stays in host RAM. The release's own tokenizer, rendering,
calibration, and SystemOne engine run unchanged from the pinned revision.

[teacher/validate_vela_int8.py](teacher/validate_vela_int8.py) compares it with
a BF16 reference that streams the release's stored BF16 weights through the same
kernels, which is the evaluated computation without 32 GB of memory, and with
the outputs the release recorded for its README examples. Results on an RTX
A3000 12 GB laptop GPU under WSL2, using Transformers' PyTorch Gated DeltaNet
kernel ([full report](teacher/reports/vela-2.0-9b-int8-g128-rtx-a3000.json)):

| Measurement | Result |
| --- | --- |
| GPU memory after load | 6.6 GiB of parameters; 7.7 GiB in use including the CUDA context |
| Host memory | 3.8 GiB FP32 embedding table; 5.1 GiB peak process RSS |
| Per request, 21 short SystemOne requests | Median 0.85 s, maximum 2.1 s |
| Batched labeling, 72 short rows, 2,048-token budget | 2.0 rows/s; 8.7 GiB peak reserved |
| One long input | 8.2 k tokens in 6.8 s; 12.3 k tokens in 9.9 s; 16.3 k tokens in 85 s because memory spilled (below) |

| Comparison | Values | Max abs probability difference | Mean | Changed decisions, labels, or span offsets |
| --- | --- | --- | --- | --- |
| INT8 vs BF16 reference: 25 requests, 52 question blocks, all question types, both span heads | 273 | 0.013 | 0.0009 | 0 |
| INT8 vs recorded release outputs | 35 | 0.009 | 0.0011 | 0 |
| BF16 reference vs recorded release outputs | 35 | 0.002 | 0.0003 | 0 |

Raw head logits moved by 0.015 on average (p99 0.067) for questions and by
0.063 (p99 0.28) for span cells. One scale per output row instead of one per
128 columns doubled the largest probability change to 0.029; the group scales
cost 0.1 GiB.

Operating limits and open items:

- Keep the batch token budget at 2,048 on a 12 GB GPU; larger budgets gained at
  most 15% even when they fit. At 4,096 the default allocator reserved
  13.6 GiB; under WSL2 the driver then spills to system memory instead of
  failing, and throughput fell to 0.63 rows/s. Expandable allocator segments
  avoided that (9.9 GiB reserved) but crashed with
  `CUDA driver error: device not ready` once a 16 k-token input exceeded GPU
  memory.
- Single inputs above about 12 k tokens exceed the 12 GB GPU with this kernel.
  The release's evaluated GPU kernel, flash-linear-attention, is not installed;
  adding it means updating `requirements.in` and regenerating the hash locks.
- This is a smoke-level check on 25 requests. Before using INT8 labels, repeat
  the comparison on the project's 300-500-row reviewed set, re-check
  calibration (Vela fitted its temperatures on the BF16 path), and judge the
  INT8 9B in the bake-off like any other teacher.

#### Decision 3.0 d3-flash on the 12 GB GPU (loader measured; parity pending)

Measured on 2026-10-15 with the fully hashed approved revision
`b92769d85908bb3ee737ef9c765e1c08b887aca6`, using
[teacher/d3_int8.py](teacher/d3_int8.py), PyTorch reference Gated DeltaNet,
SDPA, batch size 1 and a 2,048-token per-question ceiling:

| Measurement | Result |
| --- | --- |
| Full manifest hashing plus INT8 load | 190.46 s |
| GPU allocated / reserved after load | 7.416 / 7.436 GiB |
| Two short text questions, noul and choice | 207 total input tokens in 7.12 s, including first-call overhead |
| Peak GPU reserved through that request | 8.438 GiB |
| Download-free CPU regression tests | 10 d3 tests; 13 repository tests passed; Ruff lint and changed-file formatting passed |

The text smoke call returned obstacle probability 0.000760 and selected
`advance` with probability 0.997250 for a synthetic clear-path sentence.
These are functional checks, not accuracy or quantization-parity evidence.
Image processing failed to initialize because torchvision is absent; image
support and the INT8-versus-streamed-BF16 comparison remain unverified.
The adapter excludes remote media, all video inputs, and the optional server.
All consumed model files must be covered by the required manifest, and every
listed file is SHA-256 checked before the release runtime is imported.

#### d3-flash and d3-mini validation (measured 2026-10-15)

[teacher/validate_d3_int8.py](teacher/validate_d3_int8.py) now compares both
teachers with stored BF16 projections and GPU lookup of the used embedding
rows. The INT8 path reuses `stored_bf16_weights` with a one-weight GPU cache;
the mini reference streams the same projections from disk. Other computation
and release prompts/readout are unchanged. Approved snapshot manifest digests
are pinned in the loader, including when a local directory is supplied.
The approved torchvision 0.25.0 dependency resolved the initial image blocker.

Both runs used the identical hashed suite of 25 requests: ten text, eleven
synthetic rover JSON states and four local 64x64 images, covering 31 questions
(12 choice, 12 noul, 7 score). Noul probabilities are expanded into both
Bernoulli outcomes, giving 85 compared values. These are diagnostic fixtures,
not reviewed labels. The processor upscales the small images as released.

| Measurement | d3-flash INT8 group-128 | d3-mini BF16 |
| --- | --- | --- |
| GPU allocated after load | 7.416 GiB | 7.368 GiB |
| Candidate pass peak reserved, excluding load | 7.623 GiB | 7.568 GiB |
| Candidate pass wall time, including first-call overhead | 74.84 s | 43.62 s |
| Median request latency | 3.292 s | 1.845 s |
| Candidate questions per second, batch size 1 | 0.414 | 0.711 |
| Maximum / mean absolute probability delta vs own BF16 reference | 0.019836 / 0.002114 | 0 / 0 |
| Changed argmax levels/choices or noul decisions at 0.5 | 0 of 31 | 0 of 31 |

Full reports: [d3-flash](teacher/reports/d3-flash-int8-g128-rtx-a3000.json)
and [d3-mini](teacher/reports/d3-mini-bf16-rtx-a3000.json). Flash maximum
deltas by type were 0.002598 (choice), 0.014132 (noul), and 0.019836 (score).
The largest score shift was `rover-02`, level 0: INT8 0.417293 versus BF16
0.397457; level 1 remained the winner (0.476685 versus 0.492474). This
exceeds Vela's earlier 0.013 smoke maximum on a different suite and is not a
universal quantization tolerance. Investigate on the reviewed task set before
using production labels or relying on calibration. No teacher quality winner
can be selected from numerical parity or this synthetic suite.

Streamed-reference throughput includes disk and host/device transfer overhead
and must not be presented as resident BF16 inference speed. The mini result
checks this host-embedding/streamed-projection adapter, not an independently
reimplemented model. Neither test measures board fit, task accuracy, energy,
or commercial training-data provenance.

The two RTX 3090s below are rarely available, so the 12 GB RTX A3000 is the
default teacher host. d3-flash (revision `b92769d`) is the strongest Decision
3.0 member that fits it: its text backbone has exactly the dimensions of the
measured Vela 2.0 9B (32 layers, 8 attention and 24 Gated DeltaNet; hidden size
4,096; MLP width 12,288; vocabulary 248,320), plus a 0.46B vision encoder.
Computed from the published configurations:

| Configuration | GPU weights | Host RAM |
| --- | --- | --- |
| d3-flash, INT8 group-128 projections, other tensors BF16, FP32 readout | 7.4 GiB | 1.9 GiB BF16 embeddings |
| d3-flash, all BF16 | 13.7 GiB: does not fit | 1.9 GiB |
| d3-mini (revision `6d8971f`), all BF16 as evaluated | 7.3 GiB | 1.2 GiB |
| d3-mini, INT8 projections | 4.0 GiB | 1.2 GiB |

INT8 Vela 9B on the same backbone held 6.6 GiB of parameters and peaked at
8.7 GiB reserved with a 2,048-token batch budget, so d3-flash in INT8 should
leave room for activations below the WSL2 spill point; measure it. Port
[teacher/vela_int8.py](teacher/vela_int8.py) as in the two-GPU list below,
without the split: one device, no hooks. d3-flash and d3-mini ship the same
`d3_runtime.py`, which differs from the reviewed d3 copy in one docstring line.
Compare d3-flash in INT8 with d3-mini in BF16 in the bake-off: if the smaller
model labels robot states as well, it avoids quantization altogether.

Throughput estimate, not measured: INT8 Vela 9B processed about 1,200 tokens/s
on this GPU for long inputs, and d3 encodes every question as its own sequence,
so five 300-token questions take about 1.3 s per state, or about 7 hours for
20,000 states, before images.

#### Bounded d3-mini INT8 Parity (2026-10-16)

The user approved cached-only inference at the pinned mini revision, first on
the unchanged 25-request/31-question diagnostic suite at 2,048 tokens, with a
10 GiB PyTorch allocator cap. Full manifest hashing preceded release imports.
The [measured report][mini-int8-parity-report] has SHA256
`7d6e9d9480de5077aa93911f310bcb4bfd499fb3b7fb62c707ae59f882beabe7`.
INT8 group-128 versus streamed BF16 produced maximum/mean probability deltas
0.0154966/0.00157733 across 85 values, with zero decision flips. Maximum deltas
by question type were choice 0.0007394, noul 0.0068570 and score 0.0154966.

On the RTX A3000, load took 52.58 s with 4.006 GiB allocated afterward and
4.699 GiB peak reserved during loading. Candidate requests took 20.42 s total,
0.522 s median, with 4.149 GiB peak allocated/4.334 GiB reserved. The streamed
reference took 84.31 s, 2.104 s median, with 4.170/4.406 GiB peak
allocated/reserved. Timings include cold-start effects and reference streaming;
they are not task throughput forecasts. The allocator cap excludes driver and
other native allocations. No OOM or cap failure occurred.

This parity review supports the separately approved resource-only continuation
at 4,096/8,192/12,288 tokens; no new quality threshold is adopted. It does not
qualify task labels, longer contexts or teacher accuracy. Normal d3-mini remains
BF16/2,048; mini INT8 is an explicit experimental opt-in. Inputs, history,
representations and normal preflight limits are unchanged. No dataset, training,
download, dependency or hardware action occurred. Full suite: 326 passes plus
the known transformer expected failure; lint, format and diagnostics pass.

[mini-int8-parity-report]: teacher/reports/d3-mini-int8-parity-capped-20261016.json

#### Bounded Full-Input Context Resources (2026-10-16)

After reviewing the parity above, the approved resource-only continuation used
the same pinned/full-verified mini INT8 package and 10 GiB PyTorch cap. Three
unchanged full-renderer inputs came from existing logs: wire-clear ticks 0/15
and label-smoke slalom tick 15. They contain 3,421/7,616/10,705 tokens, with
one/eight/eight valid history ticks. Original state, question, source, renderer,
frame and complete token-sequence hashes are in the [resource report][mini-context-report],
SHA256 `07b9522e945bacbad9534d835c684e8c4fcde505cb279e5c9c26bf64109224e7`.
An independent CPU-only cached-tokenizer audit reproduced every token ID and
input/provenance hash. No field, history slot or precision was removed.

| Explicit ceiling | Startup clear | Warm clear | Warm slalom |
| --- | --- | --- | --- |
| 4,096 | 6.935 s | rejected | rejected |
| 8,192 | 2.519 s | 5.301 s | rejected |
| 12,288 | 2.087 s | 4.847 s | 7.328 s |

All six admitted cases completed; three over-budget cases were skipped without
truncation. Largest measured peaks were 6.478 GiB allocated/7.313 GiB reserved
on the RTX A3000. Loading used 4.006 GiB afterward/4.699 GiB peak reserved.
No OOM/cap failure occurred. These single observations include cold-start and
cache effects, not controlled throughput or worst-case measurements. The largest
actual sequence was 10,705 tokens; a 12,288 ceiling is not evidence that an
actual 12,288-token sequence fits or that every future input fits.

Response distributions were checked for valid numeric shape/range, then discarded;
the report contains no answer values or mode labels. This is resource evidence,
not longer-context BF16 parity, teacher comprehension, mode semantics, task
accuracy, latency qualification or live-labeling approval. No dataset, training,
new episode, dependency/download or hardware action occurred. Normal mini stays
BF16/2,048, full inputs/history and both exact drafts are unchanged. Live-use
strategy and task targets/data still require review; the normal budget gate is
not cleared. Ten additional tests pass; 37 d3 checks, 336 repository passes plus
the known transformer expected failure; Ruff/format/editor diagnostics clean.

[mini-context-report]: teacher/reports/d3-mini-context-resource-capped-20261016.json

#### Bounded Longer-Context Numerical Parity (2026-10-16)

The user separately approved INT8-versus-streamed-BF16 comparison on the same
three existing full inputs at the same experimental ceilings, retaining only
numeric deltas/flips, timings, memory and provenance. Full cached mini package
verification and the 10 GiB PyTorch cap remained mandatory. The [parity report][mini-context-parity-report]
has SHA256 `f2f14d97b76ef5447ebe59b3dd2a2281487da69e97bcba640a74636462d519c4`.
The complete input/token/provenance hashes match the preceding resource run and
were independently reproduced on CPU with the approved cached tokenizer.

| Existing input | Tokens | Admitted ceilings | Maximum absolute delta | Decision flips |
| --- | --- | --- | --- | --- |
| Startup clear | 3,421 | 4,096 / 8,192 / 12,288 | 0.0202917 | 0 at each ceiling |
| Warm clear | 7,616 | 8,192 / 12,288 | 0.0206704 | 1 at each ceiling |
| Warm slalom | 10,705 | 12,288 | 0.0101652 | 0 |

Six comparisons covered 30 probability values: maximum/weighted mean delta
0.0206704/0.00752864 and two flips. These are the original five-option `mode`
choice question only, not noul/score coverage. Repeated ceilings reuse the same
three observations: both flips are the same warm-clear input at two ceilings,
not two independent examples. No actual 12,288-token input was tested. Three
over-budget cases were rejected without truncation; no OOM/cap failure occurred.

Peak allocated/reserved across both phases was 6.498/7.313 GiB. Candidate times
were 2.335-5.683 s for startup, 4.833-5.675 s for warm clear, and 7.190 s for
warm slalom; reference times were 2.795-3.482/5.554-6.032/8.125 s respectively.
These single observations include cold-start/cache effects and BF16 weight
streaming, not controlled throughput comparisons or resident-BF16 forecasts.

**Review:** numerical execution fits, but argmax parity does not hold on all
three selected inputs. The larger delta than the short suite is on different
inputs, not proof of a context-length trend. Answer values and margins were
discarded; no selected class, margin diagnosis, correctness or teacher winner
is inferred. Do not promote this INT8 path to labels or claim calibrated/task
quality. Mode stays unlabeled; no new threshold or default/input/history/draft
change is adopted. No dataset, training, new episode, dependency/download or
hardware action occurred. Ten added tests; 47 d3 checks and 346 repository
passes plus the known transformer expected failure; lint/format/diagnostics
and evidence/doc audits pass.

[mini-context-parity-report]: teacher/reports/d3-mini-context-parity-capped-20261016.json

#### Decision 3.0 d3 on Two RTX 3090s (when available)

When it is available, a second host with two NVLinked RTX 3090s (2 x 24 GB) can
run the flagship d3 for the bake-off and for relabeling hard cases. Leave its
GTX 1080 Ti out: the d3 runtime accepts only BF16, which Pascal lacks in
hardware. Run d3 in INT8, split by layers across both cards.
All-BF16 weights do not fit (46.2 GiB even with the embedding table on the
host), so the reference for validation must stream weights as the Vela
validator does.

Computed from d3's published configuration (64 layers: 48 Gated DeltaNet and
16 gated attention; hidden size 5,120; MLP width 17,408):

| Part | Placement | Memory |
| --- | --- | --- |
| Large projections (MLP; attention q/k/v/o; Gated DeltaNet `in_proj_qkv`, `in_proj_z`, `out_proj`), INT8 with BF16 group-128 scales | Layers 0-31 on GPU 0, 32-63 on GPU 1 | 23.0 GiB in total |
| Vision encoder (0.46B), norms, gates, convolutions | BF16 as released; vision encoder on GPU 0 | 0.9 GiB |
| Token embeddings (1.27B) | Host RAM, BF16 | 2.4 GiB |
| Readout (255 x 5,120) | GPU 0, FP32 as released | 5 MB |

That leaves about 11 GiB per card for activations and the CUDA context. Port
[teacher/vela_int8.py](teacher/vela_int8.py) with these differences:

- Keep every unquantized tensor in BF16: d3's evaluated path is pure BF16 with
  an FP32 readout, unlike Vela's FP32-parameter autocast path.
- d3 runs `noncausal_full_attention` through its own `PromptEncoder` loop,
  which passes rotary embeddings and masks built on the first GPU to every
  layer as keyword arguments. Move inputs on every second-GPU layer (a
  per-layer pre-hook with keyword arguments, or Accelerate's device hooks) and
  move the final hidden state back to the readout's GPU; a hook on only the
  first second-GPU layer fails at the next one. The split transfers one
  activation tensor per pass, so NVLink helps but is not required.
- `D3.__init__` loads its backbone with `from_pretrained(...,
  device_map={"": device})`, and the release's AutoModel path (`modeling_d3`)
  rejects multi-device maps. Replace only that loading step with the INT8
  sharded backbone, keep the runtime's prompts, readout, and temperature
  unchanged, and never call `D3.to()` on the sharded model.
- The release's fast path (`d3_fast.py`) is for ROCm; on CUDA, install
  [flash-linear-attention][fla] instead of using the PyTorch reference kernel,
  which needed several GiB of temporaries for long Vela inputs.
- `verify="fast"` hashes only files up to 64 MiB and size-checks the weight
  shards; hash once with `verify="full"` after download. The runtime also
  downloads `http(s)` image and video URLs, so label from local files or arrays.
- Validate as for Vela: INT8 against the streamed BF16 reference on robot-state
  and general requests, reporting probability differences and decision flips
  per question type.

Throughput estimate, not measured: about 49 GFLOP per token, so a 300-token
question costs about 15 TFLOP. At 30-40 TFLOPS sustained across the pipeline
that is 0.4-0.5 s per question, or 10-14 hours for 20,000 states with five
questions each, before images. Each 32 x 32-pixel image patch adds one input
token, so label from the student's crop rather than full-resolution frames.

Choose the teacher with a bake-off on the reviewed evaluation set: accuracy or
macro-F1 against human labels, NLL, Brier score, calibration error, per-class
recall, and labeling cost. A larger teacher is not automatically a better
labeling source for a specific domain, and leaderboard scores on different
Index versions are not comparable (Vela's 41.09 is on Index 0.2.1, Decision
3.0's scores on 0.3.2).

### Label Sources for Robot Decisions

Use the cheapest label source that is correct for each question:

| Question kind | Example | Label source |
| --- | --- | --- |
| Computable from the module's own inputs | Obstacle inside the braking envelope from ToF range and speed; clearest sector of a depth grid | Deterministic code or simulator ground truth; often better computed on the M55 at run time than learned |
| Perceptual or semantic | Person or animal ahead; traversable surface; docking station visible | Teacher distributions (Decision 3.0) on the module's own camera frames, checked against reviewed labels |
| Policy or preference | Which behaviour mode suits the task and state | Reviewed human labels and scripted experts; teacher labels only as a measured supplement |

The teacher input must carry the same information as the student input: render
each recorded state packet deterministically into the teacher's state text and
pass the same camera frame at the student's crop. d3's image processor upscales
frames below 65,536 pixels (256 x 256), so measure teacher quality at the
student's resolution in the bake-off. A teacher that sees more (higher
resolution, future frames, privileged simulator state) can still help, as in
[Learning by Cheating][lbc], but only where the decision is inferable from the
student's input and the benefit is measured.

## 5. Audit of the PDF's Final Proposal

The final proposal's teacher-student direction is useful, but its illustrative
code and performance claims are not an implementation baseline.

| Finding | Consequence | Design response |
| --- | --- | --- |
| Labeling code substitutes `torch.randn(..., 5)` for teacher logits | No meaningful teacher supervision | Capture real, schema-aligned Vela distributions |
| Assumes a generic CLS classifier or guessed teacher forward API | Incorrect readout and labeling contract | Start with the documented public decision interface |
| Mixes teacher and student tokenization assumptions | Token IDs do not carry the same meaning | Preprocess the original input independently for each model |
| Padding is not properly masked or handled | Predictions can depend on padding rather than content | Specify and test padding, pooling, length, and missingness behaviour |
| Representation projection is omitted from the optimizer/DDP handling | Alignment parameters do not train or synchronize correctly | Omit alignment initially; include all trainable parameters if later added |
| Fixed five-class head is described as a general decision model | It cannot score arbitrary runtime options | Advertise a bounded task catalogue; option-conditioned models are a later experiment |
| Weight size is treated as proof of deployment | Ignores activations, fallback, runtime, and layout | Require compiler reports, linker checks, and board validation |
| Transformer NPU mapping is assumed | Dynamic attention products require CPU work | Prefer CNN/MLP first; profile any transformer alternative |
| SRAM operation is equated with no external boot storage | SRAM contents disappear after power loss | Separate boot storage from inference placement |
| Softmax is equated with trustworthy confidence | Normalization does not establish calibration | Calibrate deployed outputs and evaluate rejection behaviour |
| Latency, power, training duration, and accuracy are presented as guarantees | No supporting project measurement | Treat these as unknown until measured |

For the shown width-256, three-block student with vocabulary 1,024, 64 positions,
and five output classes, the parameter count depends on the feed-forward width,
which must be re-derived from the PDF's actual code. Recomputed with PyTorch
modules, it is 1.86 million with `dim_feedforward=512`, 2.65 million with 1,024,
and 4.23 million with PyTorch's default of 2,048, in which case the PDF's "four
million" is correct. An all-INT8 raw-parameter estimate is 1.8-4.0 MiB, but
normalization values, biases, quantization metadata, compiler layout, and
activations can add substantial memory. This calculation does not prove fit.

The PDF's 0.08-GOP estimate for a 128-token Vela 0.3B input is also inconsistent
with the approximately 28.2-GOP linear-projection calculation above. Neither
operation count can establish target latency without mapping and measurement.

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
[REVIEW.md](REVIEW.md) §6.2 put small CNN students at tens of milliseconds on
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

[decision-math-api]: firmware/include/micro_classifier_math.h
[decision-math-source]: firmware/micro_classifier_math.c

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

[head-reference-api]: firmware/include/micro_classifier_heads.h
[head-reference-source]: firmware/micro_classifier_heads.c
[native-verifier]: interface/native_verify.py
[native-head-report]: interface/reports/native-heads-20261019.json

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

[reference-build-audit]: interface/build_audit.py
[reference-build-audit-report]: interface/reports/reference-build-audit-20261019.json

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

[assembly-api]: firmware/include/micro_classifier_assembly.h
[assembly-source]: firmware/micro_classifier_assembly.c
[assembly-report]: interface/reports/native-assembly-20261019.json

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

[assembly-build-report]: interface/reports/assembly-build-audit-20261019.json

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

## 7. Data and Distillation Design

Task-specific distillation into simpler networks has published support, for
example [Tang et al.][distillation-paper]. This supports the approach, not a
guarantee that a particular micro-student preserves broad teacher capabilities.

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
[sim/rover.py](sim/rover.py) implements the accepted minimal Python/NumPy
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

[controlled-arithmetic-review]: REVIEW.md

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

[controlled-arithmetic-prototype-tests]: tests/test_sim.py

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

[controlled-arithmetic-dossier-review]: REVIEW.md

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

[arithmetic-trusted-base-review]: REVIEW.md

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

[arithmetic-paper-review]: REVIEW.md

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

[arithmetic-compatibility-review]: REVIEW.md

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

[controlled-owner-contract-review]: REVIEW.md

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

[controlled-owner-prototype-review]: REVIEW.md

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

[controlled-candidate-audit-review]: REVIEW.md

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

[controlled-candidate-auditor-review]: REVIEW.md

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

[native-gap-plan-review]: REVIEW.md

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

[sinc-contract-review]: REVIEW.md

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

[sinc-prototype-review]: REVIEW.md

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

[sinc-correctness-review]: REVIEW.md

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

[sinc-bridge-review]: REVIEW.md

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

[sinc-path-review]: REVIEW.md

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

[sinc-route-review]: REVIEW.md

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

[sinc-cell-review]: REVIEW.md

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

[sinc-word-review]: REVIEW.md

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

[sinc-word-proof-review]: REVIEW.md

[c1-motion-source]: sim/rover.py
[c1-prototype-source]: sim/diagnostics.py
[floor-rules]: sim/rules.py
[floor-rules-report]: sim/reports/rules-baseline-20261020.json

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

[sim-tests]: tests/test_sim.py

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

[navigation-reference]: sim/navigation.py

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

[sensor-diagnostics]: sim/diagnostics.py
[sensor-diagnostics-report]: sim/reports/sensor-diagnostics-20261019.json

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

[readiness-tool]: teacher/readiness.py
[readiness-report]: teacher/reports/readiness-pilot-20261019.json

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

[simulator-range-source]: sim/rover.py

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

[provenance-audit]: teacher/provenance.py
[provenance-audit-report]: teacher/reports/provenance-audit-20261016.json

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

[blind-review-tool]: teacher/review.py
[blind-review-report]: teacher/reports/review-preparation-20261016.json

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

## 8. Deployment Budget and Validation Gates

### Proposed Initial Budgets

| Resource | Planning target |
| --- | --- |
| Compiled model constants, including metadata and biases | At most 1 MiB |
| Peak activation/scratch allocation | At most 512 KiB |
| Complete peak internal SRAM use | At most 3 MiB |
| External RAM / external model reads during inference | None for the proposed internal-memory milestone |
| Decision rate and end-to-end latency | Derived per frame: the distance travelled during one decision period plus latency must fit inside the stopping or avoidance margin (a rover at 0.5 m/s and 20 Hz moves 2.5 cm per tick); measured at nominal clocks |
| Energy | To be agreed from the frame's power budget |

The total SRAM gate includes firmware-resident data/code, stacks, preprocessing,
I/O, runtime state, control blobs, initialized model data, and temporary copies.
The difference between total advertised memory and these targets is headroom,
not automatically usable contiguous space in every bank.

These targets can change only through an explicit design decision supported by
task quality and compiler evidence. They are not claims that an untrained
architecture already meets them.

### Acceptance Gates

| Gate | Required evidence |
| --- | --- |
| Export and mapping | Static supported graph; generated reports identify all CPU fallback |
| Internal-memory placement | No external inference pools; compiler allocation agrees with linker reservations |
| Complete memory fit | Peak application memory, stack use, and temporary buffers meet the agreed budget |
| Numerical parity | Golden preprocessing and outputs compared across float host, INT8 host, and target |
| Task quality | Agreed human-ground-truth metrics and per-class/error-cost requirements on a locked test set |
| Distillation benefit | Controlled comparison against supervised-only and simpler non-neural baselines |
| Confidence and rejection | Agreed error/coverage behaviour, including ambiguous and out-of-domain inputs |
| Timing and energy | Board measurements include preprocessing, fallback, probability calculation, and I/O |
| Persistence | Cold boot loads the correct firmware and matching model initializers without a debugger |
| Robustness | Invalid inputs, stale data, unsupported schemas, timeouts, and inference failure follow application policy |
| Interface contract | Malformed, stale, out-of-order, and missing packets are handled as specified; a silent module triggers the host's fail-safe |
| Closed-loop behaviour | Scenario suites in simulation and then in an arena: collisions, rejections, oscillation, and task completion within agreed limits |

Define numerical tolerances and class-change expectations explicitly rather
than assume bit-exactness across backends. ST's
[quantization guide][st-quant] warns that ONNX Runtime on x86-64 with AVX2 or
AVX-512 can saturate in U8S8 kernels, so treat the host INT8 reference as an
approximation and check for saturation before attributing a mismatch to the
NPU. Measure latency distributions and, where the application needs one, a
defensible worst-case deadline. NPU kernel time alone is not end-to-end
decision latency.

ST's NPU and CM55 validation projects target the STM32N6570-DK, so M1b starts
there; its NPU validation example supports
`USE_EXTERNAL_MEMORY_DEVICES=0` for an internal-only development check.
Separately validate the intended production boot flow, including any permitted
external flash, instead of confusing development loading with cold boot.

## 9. Toolchain and Component Ownership

| Responsibility | Initial tooling or component |
| --- | --- |
| Teacher adapter | Pinned open-teacher revision and its published decision interface; [teacher/vela_int8.py](teacher/vela_int8.py) for Vela 2.0 9B on a 12 GB GPU; an INT8 d3-flash loader for the same GPU is planned, with a two-GPU d3 variant later (§4) |
| Dataset and evaluation | Versioned examples, split manifests, reviewed policy labels, metrics |
| Simulation and closed-loop tests | PX4 software-in-the-loop with Gazebo or an equivalent rover simulator; scenario suites and episode logging |
| Module protocol | One packet definition shared by firmware and host tools; MAVLink or DroneCAN adapters for PX4 or ArduPilot hosts |
| Student training | PyTorch, single-GPU initially |
| Model export | Static standard ONNX graph with compiler-compatible operators/opset |
| Quantization | ONNX Runtime static INT8 QDQ; QAT only when needed |
| NPU generation | Pinned ST Edge AI Core / Neural-ART delivery |
| Embedded integration | STM32CubeN6 HAL/BSP, generated bindings, matching LL_ATON/STAI |
| Build and programming | Arm GNU toolchain, make/CMake as appropriate, STM32CubeProgrammer, ST-LINK |
| Target validation | ST NPU validation/AiRunner and task-specific test harness |
| Embedded API | Bounded preprocessing, decision semantics, rejection and application integration |

Keep host labeling/training/export and embedded preprocessing/runtime ownership
clear. A host HTTP wrapper can be added later, but must not perform the actual
encoder inference for an allegedly on-device classifier.

### Alternatives

- [ST Model Zoo services][st-modelzoo]: reuse relevant quantization, benchmark,
  and board bring-up patterns. It is not a turnkey Vela-to-micro NLP pipeline;
  pin a tool/runtime combination tested by the selected example.
- [CMSIS-NN][cmsis-nn]: useful M55/Helium CPU baseline and portability option;
  it does not replace Neural-ART acceleration.
- [LiteRT Micro][litert-micro]: useful small MCU interpreter; not an automatic
  N6 NPU optimizer or a way to make an oversized model fit.
- [Microsoft BitNet][bitnet]: its documented runtime is not a drop-in
  STM32N6/Neural-ART backend. Evaluate low-bit work only after INT8 succeeds.
  Ternary or 2-bit weights would not reduce NPU SRAM use: the NPU computes in
  INT8, so weights occupy INT8 SRAM during inference whatever the storage format.
- [ST DQNN support][st-dqnn]: documented binary/INT8 CPU configurations do not
  establish arbitrary ternary NPU execution. Storage precision, arithmetic
  support, and actual mapping are separate questions.
- Simpler students to compare against: hashed n-gram linear models,
  [Model2Vec][model2vec]-style pruned static embeddings, projection networks
  ([PRADO/pQRNN][pqrnn], with no embedding table), and [EmbBERT][embbert]
  (357 k parameters) if pairwise reasoning needs attention.
- Other hardware, if attention-based students or more SRAM become necessary.
  From European vendors: [Infineon PSoC Edge E84][psoc-edge-e84] (Germany;
  Cortex-M55 with an Ethos-U55 NPU, up to 6 MB SRAM, CAN-FD) and
  [NXP i.MX RT700][nxp-rt700] (Netherlands; up to 7.5 MB SRAM).
  [Alif Ensemble E8][alif-e8] adds an Ethos-U85 with transformer support but
  comes from a US company. [REVIEW.md](REVIEW.md) §7 and §12 compare these
  options.
- A European teacher, if teacher provenance becomes a requirement: open-weight
  Mistral AI models (France), such as [Mistral Small 3.1][mistral-small]
  (Apache-2.0, image input). They generate text, so a decision readout over
  option-token probabilities and its calibration would have to be built and
  validated first.

## 10. Safety, Security, and Reproducibility

For robotics or another consequential application, keep deterministic
interlocks, watchdogs, stale-sensor checks, and motor control independent of ML.
A classifier can recommend a behaviour; its probability must not be the sole
permission to move or proof that an action is safe. On a drone, the flight
controller owns stabilization, geofences, and the fail-safe (hold or land); no
module output or silence may stop the motors in flight. Flight tests must
follow the operator's aviation rules (in the EU, the
[EASA drone framework][easa-drones]).

Schedule inference so it cannot block required control deadlines. Handle
invalid data, missing data, model/runtime mismatches, low confidence, timeout,
and inference errors explicitly. A neural model's low-confidence threshold is
not a complete out-of-domain detector; test rejection against realistic unknown
inputs and add explicit domain checks where available.

Pin and inspect Hugging Face custom code before using `trust_remote_code`.
Prefer safe tensor serialization where supported, and record model, tokenizer,
schema, and compiled-artifact hashes. Firmware and memory initializers must be
distributed as a compatible versioned set. Head blobs and trunks are executable
configuration: sign them, verify them at boot with the N6's secure boot and
cryptography, and reject unknown versions at run time. The INT8 teacher loader
imports the Vela 2.0 9B release code from one pinned revision, reviewed before
execution (no subprocess, network, pickle, or `torch.load` use); its downloaded
files matched the release's SHA256SUMS.

Review model, tokenizer, dataset, generated-label, remote API, and ST tool
licenses separately, through a licensing gate at M0 and M3 that records the
license of each teacher, dataset, tokenizer, and generated label set:

- Hosted Jev outputs must not be used for distillation, imitation, or a
  competing product ([TypeSafe customer agreement][typesafe-mca] §2.3(b)). Get
  legal review before any Jev-in-the-loop evaluation.
- Models trained on Jev outputs carry that risk into their labels. autotrust's
  JEV-27B and JEV-27B-VL train on a [corpus][jev-corpus] whose main stream holds
  labels distilled from Jev 1.13, and JEV-35B names no training data. Exclude
  the JEV family as teachers and label sources.
- Vela 2.0 and Decision 3.0 are Apache-2.0. Vela's training data includes
  CC-BY-SA sources, and the Vela 0.3B tokenizer carries additional Gemma terms;
  do not reuse that tokenizer in the student (its 256 k vocabulary is far too
  large anyway). The [Decision paper][decision-paper] states that its documented
  training mixtures do not use official Jev predictions as labels; the Decision
  3.0 cards disclose no training data, so obtain the same statement for 3.0 in
  writing before commercial use.
- Crivo models are CC BY-NC 4.0 and unsuitable for commercial use.

Privacy requirements also determine whether remote teacher labeling is
permissible.

Do not claim a wholly European supply chain from the processor vendor's
headquarters. Define "European sourced" in M0 at the levels that matter: vendor,
chip design, wafer fabrication, assembly and test, board components, and
software and IP (the Cortex-M55 is Arm IP, and Decision 3.0 builds on Qwen
backbones). Obtain country-of-origin data per part from suppliers, including
memory, sensors, and debug hardware; a headquarters location proves none of
these.

## 11. Development Container

The `.devcontainer` directory provides the host environment; its
[README](.devcontainer/README.md) is the reference.

- Profiles: CPU (default), CUDA with Docker, and CUDA with Podman on WSL2, all
  on Ubuntu 24.04 with a Python 3.12 virtual environment at `/opt/venv`.
- Dependencies come from `requirements.in` through hash-locked CPU and CUDA lock
  files, installed with `--require-hashes`.
- Host CA certificates are exported at build time and imported into the system
  trust store. Python, Requests, curl, and Node use that bundle; TLS
  verification is never disabled.
- Tools include PyTorch, Transformers, ONNX, ONNX Runtime, the distro
  `arm-none-eabi-gcc` 13.2.1, CMake, Ninja, GDB, pytest, and Ruff.
- ST Edge AI Core, STM32CubeProgrammer, and an optional vendor GCC are not
  included. After accepting their licenses, place the Linux distributions in
  the ignored `.devcontainer/tools` directory, mounted at `/opt/st-tools`; until
  then no NPU compilation is possible. Pin one ST Edge AI Core release for
  compiler and runtime: mismatched generated code fails with "Possible mismatch
  in ll_aton library used".
- A named cache volume keeps Hugging Face, pip, uv, and ccache data across
  rebuilds; the Vela 2.0 9B snapshot needs about 18 GB of it.
- `smoke.py` checks CA trust, Cortex-M55/Helium compilation, a training step on
  CPU or CUDA, ONNX export with INT8 QDQ quantization, and Qwen3.5
  availability. It passed on the CPU and Podman/WSL GPU profiles.

Remaining direction: split teacher and student/export environments only if
framework requirements conflict, grant only the device access board work needs
(ST-LINK, serial), and add flash-linear-attention to the locks if a teacher
needs inputs above about 12 k tokens or runs on the two-GPU d3 host (§4).

## 12. Implementation Milestones

Current critical-path checkpoint (2026-11-05, REVIEW.md §123): the active
three-question rules contract resolves F19, not M2 task quality. The remaining
critical step is F21 sensor/scene evidence qualification before data collection,
then a qualified closed-loop rules baseline. Privileged simulator truth is permitted in principle
for future geometric/predictive labels, never as student input. Observation-only
human review remains for semantic/real-world data; all existing logs stay
quarantined. This does not approve collection, label import, splits, training,
Gaussian risk budgets or a sensor/hardware safety claim. Fictional mounting and
opt-in ego-error assumptions are now approved for implementation/tests (§7,
REVIEW.md §74), not representative data or physical qualification. ST tool install,
teacher provenance request and board procurement remain user-side actions.
The nominal 15 Hz acquisition/variable-age portion of F21 is now implemented
(§7, REVIEW.md §73), followed by synthetic floor/height returns and opt-in ego
errors/delay (§74). Remaining gates are reviewed scene coverage, sensor fidelity
and a qualified floor-aware rules baseline, not more reference-math tooling.
The first heuristic wire baseline is now measured (§7, REVIEW.md §75): four
successes, two collisions, two timeouts and 25 clear/blocked reference mismatches.
It remains unqualified; further collection or evidence-policy changes need review.
The registered candidate also remains unqualified (§76). Full-input aliases
demonstrate normal cylinders hidden from turning sweeps even with ideal inputs.
Following the user's coverage-first choice, the C1 prototype and controlled
synthetic qualification now include continuous-center exclusion, ideal occlusion
checks, an optional straight capsule and an explicit two-phase curved tube
(§7; REVIEW.md §§78-84). These are conditional fixture results, not an adopted
runtime sensor/input profile or task-quality clearance. Independent domain/
return/error evidence, required numerical qualification and representative task
quality remain open. Do not collect task diagnostics or integrate the prototype
merely because its synthetic checks pass.
The one-segment allowance and outer-versus-inner evidence checks are complete
(§7; REVIEW.md §85). The user then approved a separate staged positive-witness/
question-level synthetic package (§86). Both stages now pass (§87): conditional
occupied-return witnesses and conservative three-question candidate admission.
The bounded package is complete, not a qualified runtime question baseline.
The approved object envelope, no-collection/runtime boundaries and physical/
numerical/task-quality gates remain unchanged.
A design-only C1 input/evidence proposal is now prepared (§7; REVIEW.md §88).
It recommends a module-local latest-batch/relative-frame boundary, identifies
missing registration/domain/body evidence and specifies a separate bounded
synthetic compatibility package. That package was separately approved and is
now complete (§89), with conservative source-scale and arena-axis preservation.
No runtime profile, evidence source, collection or integration is qualified or
adopted by either the design draft or its synthetic compatibility checks.
The design-only simulation-first source plan is now prepared (§7; REVIEW.md
§90). It separates candidate input from private truth, proposes exact payload/
event binding and invalidation, and limits any next audit to source consistency,
not task decisions. The subsequently approved audit package is now complete
in `04492d7` / `d483d14` (§91): 32 cases, 31 audit calls, three reused scenes
and zero audit coordinator queries. It checks declared records, not producer authority or live
input qualification. The proposed producer-owned synthetic recorder is not
approved by the audit's completion. The separately approved private recorder is
now complete in `76aa712` (§92), with 16 cases, three reused scenes and zero
decision queries. Its owned event/binding records are fixture provenance, not
physical or dynamics qualification. The separately approved tests-only conditional
composition is now complete in `0c3de54` (§93): 16 cases, four reused scenes,
eight coordinator calls and at most six motions per call. Source and existing
tests remain unchanged; oracle-assisted fixture admission is not runtime policy.
The separately approved design-only motion-source contract is now prepared
(§7; REVIEW.md §94): a proposed bounded constant-twist owner, interval-ending
host semantics, independent arithmetic evidence and distinct motion/wire
verdicts. It is not adopted as a normal input contract. A four-scene/16-case,
zero-query private prototype was separately approved and is now complete in
`fe21517` (§95). It owns bounded events and provides independent zero-heading
straight reference bounds; curves/rotated headings and changed wire/goal values
remain unresolved. No normal profile/runtime adoption or source qualification
follows. The separately approved design-only curved/rotated reference contract
is now prepared (§96): exact rational integral/tail, distinct clocks and circular
heading conventions, separate implementation-error evidence and conservative
three-way comparison. It is not adopted as a normal input or producer-error
contract. The separately approved reference-only helper is complete in
`1bb89fe` (§97), with 16 cases, four reused scenes and zero question queries.
It encloses mathematical references only; old motion/source verdicts and all
qualification flags remain unchanged. The separately approved design-only
primitive-error evidence plan is now prepared (§98), with ten proposed operation
rows, supported-domain/evidence identity requirements, accumulated-error and
goal-only normalization rules. It adopts no allowance and qualifies no primitive.
The separately approved ten-row read-only implementation identity/source audit
is complete (§99): current project/wrapper/native identities and specific gaps,
not uniform primitive-error guarantees or producer qualification. The separately
approved same-row primary-source review is complete (§100), identifying scalar,
wrapper/dispatch semantics and accuracy-policy limits without numerical runs
or source-package acquisition. Matching-build/FP/domain and uniform-error
qualification still remain. The separately approved documentation-only protocol
preparation is complete (§101): worksheet fields, Q0-Q5 gates and ten proof/stop
rows, accounting/invalidation and proposed acceptance controls. No gate was
adopted or executed and no primitive allowance was justified. The separately
approved CPython P1-P3/P7 correspondence dossier is complete (§102): exact public
applied source/build metadata and float-slot text agreement, but no installed
source-to-executable, specialization/compiled-path or FP/error qualification.
Packaging sysconfig flag rewriting and differing build/runtime glibc package
versions are explicit evidence limits. Next proposed, not approved: same-row
static source/executable path inspection, five named entries/64 KiB extraction
cap, no numerical/producer run, acquisition, environment change, proof/code/bound
adoption, collection or integration. That separately approved static package is
now complete (§103): named API mappings and source specialization alternatives,
not bound float/generated/live paths or numerical qualification. Next proposed,
not approved: a design-only controlled-arithmetic alternative for the same four
rows in the private synthetic producer, with compatibility/cost/proof/stop checks;
no implementation, adoption, numeric/fixture run, acquisition or integration.
That separately approved design-only proposal is now prepared (§104): explicit
word/RN64/remainder semantics, four traces, compatibility/tradeoffs and proof/
cost/stop checks. Its separately approved isolated prototype is now complete
(§105): exact word/RN64 operations and four traces with independent literal
fixtures, rejection and atomic stops. This is not producer adoption/parity,
numerical qualification or owner/runtime integration. Its separately approved
design-only dossier is now prepared (§106): eleven conditional correctness,
work/trusted-base/stop obligations, four-row closure and a paper acceptance
sequence. Its separately approved bounded local trusted-base review is now
complete (§107): Fraction rational paths and integer-header boundaries, not
native/build/live/work qualification. Its separately approved paper review is
complete (§108): eight conditional D0/R1-R5/O0/T0 derivations, including canonical
pairs and raw-residue representability under the declared profile, not accepted
proof or qualification. Its separately approved twelve-case scalar/trace
comparison is complete (§109): exact word/sign/correction agreement, not
all-domain/native/work qualification or runtime integration. Its separately
approved design-only owner contract is prepared (§110): word ingress/four-cell
consumers, distinct lane/event/clock/seal identity and staged-publication/work
gates, not adoption or qualification. Its separately approved private candidate
and bounded tests are complete (§111): eight reused cases/four scenes, sixteen
constructor attempt positions, 112 published events per complete invocation;
all old module AST nodes and qualification flags remain unchanged. Binding is
not independent motion/source/wire evidence. Its separately approved design-only
audit contract is prepared (§112): eight boundaries/eight future gates, four
anchor/content cases, noncircular trace and bounded event/codec/history checks;
native motion/relative transforms and source authority remain unresolved.
No auditor or numerical/fixture run occurred in that design-only scope. The
separately approved private auditor/tests are complete (§113): eight reused
cases/four scenes, eight constructors/64 published events and 32 auditor attempts
per complete invocation. Independent declared trace/event/codec/capture/copy
relations are checked without producer arithmetic or native replay; source
authority/native motion/goal/relative transforms remain unresolved. All old
module ASTs/defaults/flags/verdicts stay unchanged. The separately approved
design-only native gap/exit plan is prepared (§114): eight NF0-NF7 consumer rows,
four distinct evidence claims and six paper exit checks, not numerical/native
qualification. The separately approved design-only NF1 sinc contract and paper
feasibility argument are prepared (§115): exact stored-word target, signed zero,
real-pi Machin brackets, even-series remainder, conditional domain/work/width
derivations and isolated boundary. Its separately approved private helper/tests
are complete (§116) under the 32/8-term, 65,536-bit, twelve-position/24-attempt
limits. All old module ASTs/flags/verdicts remain unchanged; mathematical
enclosure is not installed-sinc accuracy or motion/source qualification. The
2,137-pass source gate plus known xfail is recorded, not task-quality evidence.
The separately approved design-only conditional review is prepared (§117):
ten SR0-SR9 obligations, decoder/interval/series derivations and a paper ledger,
not accepted proof or resource/native qualification. Stable global bindings,
counter coverage, ordinary-return publication and W0/TB0 remain explicit limits.
No source/test/run/flag/verdict change. The separately approved design-only
NF1 native-error bridge contract is prepared (§118): nine NB0-NB8 obligations,
recorded wrapper order, branch-specific symbolic error decomposition, conservative
comparison rules and six paper acceptance checks. No installed path/FP/error
evidence or allowance is refreshed/adopted. The separately approved read-only
five-row installed-path dossier is complete (§119), with a conservative 35,758
inspected text bytes within the 65,536-byte cap. File identities/source routes
are refreshed only as stated; selected loops/IFUNC, full build/FP contract and
uniform errors remain unqualified. No target import, native comparison, source/
test or verdict change. The separately approved design-only closure-route brief
is prepared (§120): native-error qualification versus a separate partial
mathematical RN64 candidate, with whole-cell/parity rules, cap/reuse limits and
eight decision gates. Recommend candidate design work only; neither route,
replacement, error/work allowance nor total completion is adopted. The subsequent
interval-to-word certificate/work preparation was separately approved and is
complete (§121): exact-cell search/verification, guarded work ledger, separate
interval/word claims and ten
acceptance obligations, with no route/proof/allowance adoption or source/test run.
The separately approved private prototype/tests are complete (§122): 28 cases,
24 word/17 enclosure/32 direct-cell/38 total-cell entries per complete new-entry
matrix, unchanged old ASTs and a fresh 2,165-pass gate plus known xfail. No
proof/allowance, native/source/work or consumer promotion.
The separately approved paper review is complete (§123): ten CW obligations,
conditional search/guard/publication arguments, attempted-work ledger and
trusted-base limits; no proof/error/work allowance or qualification acceptance.
Next proposed, not approved: design-only certificate verification/trusted-base
closure plan, not implementation, import/fixture/run, native inspection,
source acquisition, consumer integration or allowance/promotion.
All broader gates stay unchanged.

| Milestone | Deliverable | Exit condition |
| --- | --- | --- |
| M0: Scope | Module role and first frame (rover proposed), interface contract v0, sensor set, question bundle with a label source per question, simulator, rejection policy, confidence semantics, licensing gate, European-sourcing definition, board | Open product decisions resolved for the pilot; control tasks decomposed into atomic questions |
| M1a: Compile-only proof, no board | ST Edge AI Core installed; minimal CNN/MLP export, INT8 QDQ, and NPU generation for both 1-D layouts, pooling and Gather placements, and one transformer block | Reports record epochs, software fallback, pool usage, and estimated cycles |
| M1b: Board proof | STM32N6570-DK NPU validation with external memories disabled, golden vectors, timing at nominal and overdrive clocks, signed cold boot of a dummy model | Mapping and complete memory fit proven; target output comparison recorded |
| M2: Task-quality proof | Reviewed evaluation set, representative simulated and real pilot data, deterministic and supervised baselines | Bounded task has measurable value against simpler alternatives |
| M3: Distillation proof | Teacher bake-off on reviewed robot states (d3-flash in INT8 and d3-mini in BF16 on the 12 GB GPU; d3 in INT8 on two RTX 3090s when available), genuine cached teacher distributions, controlled student comparison, one closed-loop data round in simulation | Teacher supervision improves the chosen task or has a documented reason to retain it |
| M4: Quantized validation | PTQ/QAT decision, target parity, calibration, locked test, closed-loop scenario suite | Agreed quality, rejection, memory, timing, and energy gates met |
| M5: Host integration | Rover host integration over the interface contract, boot loading, fail-safe mapping, arena tests | Cold boot, interface robustness, and closed-loop arena gates verified |
| M6: Second embodiment | Mini-drone profile on an established flight stack (PX4 offboard or equivalent), or more tasks or bounded runtime-option scoring | Each profile or capability independently meets the same gates |

Use an untrained model and synthetic tensors only for export, mapping, and
timing smoke tests in M1a and M1b; they say nothing about classification
accuracy. Do not commit to a large labeling job before this deployment proof.

### M1a Host Preparation (Measured 2026-10-15)

Task 14's script preparation can proceed without ST tools. [Host tooling][m1a-script]
exports nine untrained CPU probes, not a student: temporal Conv in
`[1,96,128,1]`/`[1,96,1,128]` layouts, matching average-pooling variants, an
MLP over 32 synthetic values, 2x8x8 ToF and 3x64x64 camera probes, embedding
Gather before the height Conv, and one PyTorch transformer block (width 32,
four heads, eight positions). These are compiler experiments, not frozen
architecture/input profiles. Equivalent layouts share weights and logical
data. Pool/Gather outside the graph is for eventual M55 preprocessing, not
a hidden deployed host encoder.

All models are CPU-resident, eval-only and gradients disabled. ONNX checker
and fixed positive input/output shapes gate opset 13 exports; the transformer
uses opset 17. The legacy exporter is intentionally selected for compatibility
and emits deprecation warnings. Signed INT8 QDQ uses symmetric per-channel
weights and asymmetric activations on Conv/Gemm/MatMul; other operators may
stay floating point. This is not a fully integer transformer claim. Standard
ONNX shape inference avoids an ORT symbolic-Reshape assertion.

The [real report][m1a-report] uses weight seed 0, 16 synthetic calibration
samples at seed 1 and eight evaluation samples at seed 2. These are not
representative calibration, reviewed labels or locked task splits. Software
versions, source/array/artifact hashes, shapes and operators are preserved.
All 27 ONNX artifacts were hash-verified under ignored
`export/artifacts/m1a-cpu-20261015/`. Report SHA-256:
`5b5b37e51c92e7ea26de7f75a6a10d094753ad9c46925f26f47f047071207804`.
Maximum float ONNX versus PyTorch difference was 4.77e-7.

| Probe | Parameters | QDQ vs Float Max Abs Error | RMSE |
| --- | --- | --- | --- |
| temporal height / width | 10,440 each | 0.059484 | 0.001650 |
| height / width plus pool | 10,440 each | 0.001655 | 0.000309 |
| state MLP | 2,368 | 0.071372 | 0.007670 |
| ToF | 10,872 | 0.001434 | 0.000364 |
| camera | 11,088 | 0.001964 | 0.000372 |
| Gather inside | 35,016 | 0.018142 | 0.003246 |
| transformer | 8,544 | **0.206992** | 0.010153 |

The 0.15 maximum-error diagnostic is a test-only plumbing bound, **not an
approved task-quality threshold**. The transformer exceeds it; no INT8
numerical qualification follows. Another seeded fixture also failed at
0.264466 with three calibration samples and 0.245311 with 16. Stop this tuning
path for now: retain the expected numerical failure rather than increasing
the bound. Float export and QDQ execution do succeed.

Verification: 133 repository tests passed plus one explicit transformer
expected failure; Ruff lint/changed-file formatting and editor diagnostics
passed. No new dependencies, downloads, training or GPU job. Actual ST
generation, epoch/fallback/pool/cycle reports and full memory fit are blocked
on the absent pinned ST toolchain; M1a is **not passed**. No target parity,
latency, energy, firmware or board validation follows from host export.

#### ST Compile Runner Preparation (2026-10-15)

[The runner][st-compile-script] consumes the host manifest. Read-only planning
checks schema, safe unique case names and all artifact hashes. Execution is
opt-in, rechecks plan/input identity, requires an exact ST release and fresh
output root, and records executable SHA-256 and `--version`/`--tools-version`
logs. This hashes the executable, **not the complete vendor installation**.
It does not download tools, accept licences or assume unknown versions work.

Commands follow the [ST 4.0.1 CLI][st-cli-401] and [compiler primer][st-npu-primer-401]:
`stedgeai generate --model <QDQ> --target stm32n6 --st-neural-art
profile-internal-memories-only--default`, with separate output/workspace paths
and verbosity 2. QDQ never goes directly to `atonn`. Vendor internal-only pools
are not our final SRAM/linker partition. No validation, loader, flashing or
board command is used; generated probe code is not firmware integration.

Case failures preserve logs and allow other cases to proceed; interruption
stops the matrix. A POSIX process-group timeout prevents orphaned compiler
descendants. Raw files are retained and hashed; symlinks are recorded without
following them. A zero exit also requires the documented generation report
and C-info JSON. Success is only `generated_reports_pending_review`, with M1a,
board and metric-review flags false. Actual epoch/fallback/pool/cycle fields
must be reviewed from real reports; no parser fabricates them. Custom profile/
CSV instrumentation waits for the supplied release and its actual output.

Verification: a real nine-case CLI dry plan invoked no ST process and created
no compiler output. Eighteen mocked runner tests cover tampering, reuse,
version rejection, launch failure, missing reports, nonzero exits, timeouts,
interruption and matrix continuation. The full suite has 151 passes plus
the known transformer expected failure; lint/format and editor checks pass.
Mocks are not vendor compatibility or compilation evidence. ST tools and
Task 14's actual M1a exit remain blocked.

Start M1b on the [STM32N6570-DK][st-dk]: ST's NPU and CM55 validation projects
and its runtime-loadable model environment target that board. The discovery kit
includes external flash and PSRAM, so verify that examples are not silently
relying on them during the internal-memory milestone. The
[NUCLEO-N657X0-Q][st-nucleo] remains a suitable compact prototype once the
validation tooling is ported.

Stop or revisit the design if a simpler rules-based model already solves the
task, the small student cannot meet reviewed task quality, or required CPU
fallback makes the agreed latency/memory budget unattainable. Move to a larger
target or revise the capability requirement explicitly rather than relabel an
off-device dependency as microcontroller inference.

## 13. Evidence and Limitations

Primary evidence consists of ST hardware/tool documentation and published Vela
model cards, configurations, and custom source. General distillation and
calibration references support methods rather than predict this project's
performance. The PDF is a source of requirements and hypotheses, not benchmark
evidence.

Research is dated 2026-10-13 and 2026-10-14. Some upstream URLs follow mutable
`main` branches; pin tested revisions and tool deliveries during
implementation. Project measurements are the teacher checks in §4 and synthetic
simulation smoke episodes in §7.
No compiler report, hardware timing, energy measurement, training result,
calibration result, closed-loop test, or supply-chain audit currently exists
for this project.

### Hardware and Deployment Sources

- [STM32N6 family overview][st-family] and [STM32N657 product information][st-n657].
- [STM32N6 boot example and modes][st-boot].
- [Neural-ART supported operators, ST Edge AI Core 4.0.1][st-operators].
- [Neural-ART compiler, profiles, and options][st-compiler].
- [Memory initializer placement and startup responsibilities][st-initializers].
- [STM32N6 validation projects and configuration][st-projects].
- [ST quantization guide][st-quant] and [runtime-loadable models][st-reloc].
- [NUCLEO-N657X0-Q][st-nucleo] and [STM32N6570-DK][st-dk].
- [VL53L8CX multizone ToF sensor][vl53l8cx].
- [Infineon PSoC Edge E84][psoc-edge-e84], [Alif Ensemble E8][alif-e8], and
  [NXP i.MX RT700][nxp-rt700].

### Robot Integration Sources

- [PX4 offboard mode][px4-offboard] and [PX4 Gazebo simulation][px4-gazebo].
- [MAVLink][mavlink], [DroneCAN][dronecan], and [REP 103 units and frames][rep-103].
- [EASA drone framework][easa-drones].
- [DAgger, Ross et al.][dagger] and [Learning by Cheating, Chen et al.][lbc].

### Model and Method Sources

- [Vela 0.3B model card][vela-small-card], [configuration][vela-small-config],
  [usage][vela-small-usage], and [custom implementation][vela-small-code].
- [Vela 4B usage and memory requirements][vela-medium-usage].
- [Vela 9B usage and memory requirements][vela-large-usage] and
  [custom loader/inference implementation][vela-large-code].
- [Vela 0.8B][vela-08b], [Decision 3.0][d3-collection] and the
  [d3 model card][d3-card], [Decision paper][decision-paper],
  [flash-linear-attention][fla], [Crivo-32M][crivo-32m], and
  [Mistral Small 3.1][mistral-small].
- [JEV-35B][jev-35b], [JEV-27B-VL][jev-27b-vl], and its
  [training corpus][jev-corpus].
- TypeSafe [customer agreement][typesafe-mca] and
  [confidence definitions][typesafe-confidence].
- [EmbBERT][embbert], [PRADO/pQRNN][pqrnn], and [Model2Vec][model2vec].
- [Task-specific language-model distillation, Tang et al.][distillation-paper].
- [PyTorch knowledge distillation tutorial][pytorch-distillation].
- [Temperature calibration, Guo et al.][calibration-paper].
- [ONNX Runtime quantization guidance][ort-quantization].
- [ST Model Zoo services][st-modelzoo], [CMSIS-NN][cmsis-nn],
  [LiteRT Micro][litert-micro], [BitNet][bitnet], and [ST DQNN support][st-dqnn].

[st-family]: https://www.st.com/en/microcontrollers-microprocessors/stm32n6-series.html
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
[sim-label-coverage-report]: sim/reports/label-coverage-20261016.json
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
[input-cost-flash]: teacher/reports/input-cost-d3-flash-20261016.json
[input-cost-mini]: teacher/reports/input-cost-d3-mini-20261016.json
[st-npu-primer-401]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-compiler.html
[st-n657]: https://www.st.com/en/microcontrollers-microprocessors/stm32n657a0.html
[st-boot]: https://github.com/STMicroelectronics/STM32N6-GettingStarted-ImageClassification#boot-modes
[st-operators]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-operators.html
[st-compiler]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-compiler.html
[st-initializers]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-memory-initializers.html
[st-projects]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-stm32n6-projects.html
[st-nucleo]: https://www.st.com/en/evaluation-tools/nucleo-n657x0-q.html
[st-dk]: https://www.st.com/en/evaluation-tools/stm32n6570-dk.html
[vela-small-card]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B
[vela-small-config]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/config.json
[vela-small-usage]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/USAGE.md
[vela-small-code]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/modeling_vela2.py
[vela-medium-usage]: https://huggingface.co/vllm-sr/Vela-2.0-4B/blob/main/USAGE.md
[vela-large-usage]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/USAGE.md
[vela-large-code]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/modeling_vela2.py
[distillation-paper]: https://arxiv.org/abs/1903.12136
[pytorch-distillation]: https://docs.pytorch.org/tutorials/beginner/knowledge_distillation_tutorial.html
[calibration-paper]: https://proceedings.mlr.press/v70/guo17a.html
[ort-quantization]: https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html
[st-modelzoo]: https://github.com/STMicroelectronics/stm32ai-modelzoo-services
[cmsis-nn]: https://github.com/ARM-software/CMSIS-NN
[litert-micro]: https://developers.google.com/edge/litert/microcontrollers/overview
[bitnet]: https://github.com/microsoft/BitNet
[st-dqnn]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-dqnn-support.html
[st-quant]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-quantization.html
[st-reloc]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-reloc-mode.html
[vela-08b]: https://huggingface.co/vllm-sr/Vela-2.0-0.8B
[d3-collection]: https://huggingface.co/collections/vllm-sr/decision-30
[crivo-32m]: https://huggingface.co/tardellirs/crivo-32m
[jev-35b]: https://huggingface.co/autotrust/JEV-35B
[typesafe-mca]: https://typesafe.ai/legal/mca
[typesafe-confidence]: https://docs.typesafe.ai/confidence
[embbert]: https://arxiv.org/abs/2502.10001
[pqrnn]: https://research.google/blog/advancing-nlp-with-efficient-projection-based-model-architectures/
[model2vec]: https://github.com/MinishLab/model2vec
[alif-e8]: https://alifsemi.com/ensemble-e8-series/
[nxp-rt700]: https://www.nxp.com/products/i.MX-RT700
[d3-card]: https://huggingface.co/vllm-sr/d3
[decision-paper]: https://vllm-sr.ai/decision-paper
[fla]: https://github.com/fla-org/flash-linear-attention
[mistral-small]: https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503
[jev-27b-vl]: https://huggingface.co/autotrust/JEV-27B-VL
[jev-corpus]: https://huggingface.co/datasets/SargeDev/jev-distill-corpus-v3
[vl53l8cx]: https://www.st.com/en/imaging-and-photonics-solutions/vl53l8cx.html
[psoc-edge-e84]: https://www.infineon.com/products/microcontroller/32-bit-psoc-arm-cortex/32-bit-psoc-edge-arm/psoc-edge-e84
[px4-offboard]: https://docs.px4.io/main/en/flight_modes/offboard.html
[px4-gazebo]: https://docs.px4.io/main/en/sim_gazebo_gz/
[mavlink]: https://mavlink.io/en/
[dronecan]: https://dronecan.github.io/
[rep-103]: https://www.ros.org/reps/rep-0103.html
[easa-drones]: https://www.easa.europa.eu/en/the-agency/faqs/drones-uas
[dagger]: https://arxiv.org/abs/1011.0686
[lbc]: https://arxiv.org/abs/1912.12294
