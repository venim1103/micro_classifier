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


### Decisions Required Before Scaffolding

Recorded as provisional defaults on 2026-10-14 ([REVIEW.md](../../REVIEW.md) §10) so
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

[wire-codec-api]: ../../firmware/include/micro_classifier_codec.h
[wire-codec-source]: ../../firmware/micro_classifier_codec.c
[state-history-api]: ../../firmware/include/micro_classifier_history.h
[state-history-source]: ../../firmware/micro_classifier_history.c
[wire-python]: ../../interface/protocol.py
[wire-header]: ../../firmware/include/micro_classifier_protocol.h
[wire-golden]: ../../interface/golden_vectors.json
[jev-35b]: https://huggingface.co/autotrust/JEV-35B
[px4-offboard]: https://docs.px4.io/main/en/flight_modes/offboard.html
[mavlink]: https://mavlink.io/en/
[dronecan]: https://dronecan.github.io/
[rep-103]: https://www.ros.org/reps/rep-0103.html
