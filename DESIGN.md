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
approved product requirements. The only project measurement so far is a
precision and resource check of the INT8 Vela 2.0 9B teacher loader (§4). No
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

### Decisions Required Before Scaffolding

| Requirement | Current status |
| --- | --- |
| First robot frame, task, question bundle, and ground-truth policy | Proposed: ground rover with atomic per-tick questions ([REVIEW.md](REVIEW.md) §10); unconfirmed |
| Input modality and sensor set: ego-state, multizone ToF, camera, text | Proposed: ego-state and an 8x8 ToF grid first, camera next; text only for operator commands |
| Languages and maximum input length (text branch only) | Unspecified |
| Fixed task catalogue versus runtime-defined questions | Unspecified |
| Whether external RAM is forbidden | Unspecified; internal-memory inference proposed |
| Whether external flash for boot/storage is allowed | Unspecified; separate from inference memory |
| Decision rate, end-to-end latency, and power, derived from the frame's speed and stopping distance (§8) | Unspecified |
| Required per-class recall, error costs, and rejection coverage | Unspecified |
| Host interface: bus, protocol, and host stack (custom MCU, PX4, ArduPilot) | Unspecified; UART first proposed |
| Simulator for closed-loop data and tests (§7) | Unspecified; PX4 software-in-the-loop with Gazebo is one candidate |
| Board selection and any component-origin requirements | Unspecified; STM32N6570-DK proposed for M1b (§12) |
| European sourcing: vendor, design, fab, assembly, components, or software provenance (§10) | Unspecified; each level needs its own evidence |
| Confidence semantics: TypeSafe Jev or Vela formulas (§6) | Unspecified |
| Commercial use and licence constraints (§10) | Unspecified |
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

#### Decision 3.0 d3-flash on the 12 GB GPU (planned, first teacher)

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
implementation. The only project measurement is the INT8 teacher check in §4.
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
