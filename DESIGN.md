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
host-to-host elapsed time. Model version 0 means no model and cannot accompany
`OK`. Catalogue version is 0. Status values 0-5 are `OK`,
`REJECT_LOW_CONFIDENCE`, `REJECT_STALE_INPUT`, `REJECT_OUT_OF_DOMAIN`,
`REJECT_UNSUPPORTED_SCHEMA`, `FAULT`. Default construction yields `FAULT`.

Answer-mask bit `question_id - 1` indicates an answer; present answers occur
in ascending ID order. Each answer has an eight-byte prefix: u8 question ID,
u8 type (`noul`=1, `choice`=2, `score`=3), u8 selected option index, u8 option
count, f32 confidence; followed by count f32 probabilities. Wire identities
follow the existing §6 bundle, not a reviewed training-label catalogue:

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

`OK` requires all four answers and a nonzero model version. Rejection/fault
may contain a subset or none for diagnostics; **its selections are not usable
recommendations**. Full decisions are **128 bytes**; empty rejection/fault
frames are 36 bytes. Golden model ID 1 is synthetic, not an installed model.

`FrameDecoder.feed` accepts byte chunks, bounds retained framing data, rejects
corrupt/unsupported frames and resynchronizes on magic. The transport owner
must discard a partial decoder on inter-byte timeout; no timing threshold is
imposed here. Missing/late decisions, duplicate/out-of-order packets and gaps
remain application duties. Sequence and timestamp wrap modulo 2^32; compare
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
Serialize access to each stream; callbacks must not feed/reset that same stream.
Feed success means the chunk was processed, not that a packet or recommendation
was produced. The transport owner calls init to discard partial data on its
chosen timeout; init also clears counters. No timeout threshold is adopted.

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
| First robot frame, task, question bundle, and ground-truth policy | Provisional default: ground rover with four per-tick questions (`path_blocked` noul, `clear_sector` choice, `speed_tier` score 0-3, `mode` choice); deterministic labels for geometry/speed ceiling, reviewed human labels plus Decision 3.0 distributions for `mode` ([REVIEW.md](REVIEW.md) §10) |
| Input modality and sensor set: ego-state, multizone ToF, camera, text | Provisional default: FLU ego-state from the host plus an on-module 8x8 ToF grid (`VL53L8CX` model) and an 8-tick history window first; camera in a later profile; text only for optional operator commands |
| Languages and maximum input length (text branch only) | Provisional default: English only for optional operator command strings, at most 128 UTF-8 bytes; enumerated task IDs preferred in v0 |
| Fixed task catalogue versus runtime-defined questions | Provisional default: fixed per-profile question catalogue stored as versioned head blobs (§6) |
| Whether external RAM is forbidden | Provisional default: no external RAM during inference (`internal-memories-only--default`) |
| Whether external flash for boot/storage is allowed | Provisional default: external flash allowed for cold boot and weight/head initializers; separate from inference memory |
| Decision rate, end-to-end latency, and power, derived from the frame's speed and stopping distance (§8) | Provisional default: 20 Hz decision rate, at most 20 ms end-to-end latency from state packet to decision packet at nominal clocks (600 MHz CPU / 800 MHz NPU), below 1 W module power |
| Required per-class recall, error costs, and rejection coverage | Provisional default: missed obstacle 20x worse than a false stop; `mode` macro-F1 ≥ 0.85 at ≥ 80% coverage; zero collisions in simulator and arena scenario suites |
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
All 169 C checks, 231 interface tests and 836 repository tests pass plus the
known transformer expected failure; lint/format pass. Seeded full-path parity
and native math sanitizer coverage are the next approved checks, not claimed
by this checkpoint. No timing, SRAM-fit, target execution, calibration, task
quality or physical safety evidence follows. Existing wire/goldens, normal
inputs/defaults, mode abstention, quarantine and all data/hardware gates stay.

[decision-math-api]: firmware/include/micro_classifier_math.h
[decision-math-source]: firmware/micro_classifier_math.c

Per-tick decisions can oscillate near a decision boundary. Apply hysteresis or
a minimum dwell time to mode and steering selections on the module, document it
in the interface contract, and report raw distributions alongside smoothed
selections. Smoothing adds latency, so validate it in closed loop (§7).

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
| Ground rover | `path_blocked` (noul, deterministic from ToF range and speed), `clear_sector` (choice: left, centre, right, none), `speed_tier` (score 0-3), `mode` (choice: explore, approach, avoid, dock, halt) |
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
physical specifications: 20 Hz, 0.18 m circular rover radius, 0.6 m/s forward
speed limit, 1 m/s² acceleration/deceleration, 1.5 rad/s turn limit; 45-degree
planar ToF, 4 m range, 0.02 m independent Gaussian noise, 2% independent
zone dropout, two-tick delivery latency, eight history ticks, and 400-tick
episode limit. The eight vertical rows repeat planar rays before noise and
dropouts; this is not VL53L8CX emulation. Constant-twist motion is checked
against swept inflated obstacles, including a conservative curved-path margin.
Invalid commands are rejected, bounded commands are reported, and collision
terminates the simulation instead of permitting tunneling through obstacles.

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
