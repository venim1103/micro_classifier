# Research Review: Jev-like Classifier on STM32N6

Status: Independent review of [DESIGN.md](DESIGN.md) and the repository state.
Review date: 2026-10-13. Update 2 (2026-10-14, §12) covers the robot
decision-module clarification and an external AI analysis; it corrects F1, F2,
and §7.2 in place.
Scope: feasibility, verification of design claims, landscape changes, design
gaps, alternatives, risks, and concrete next steps.

Method:

- Read DESIGN.md, README.md, and the `.devcontainer` setup.
- Re-checked hardware and compiler claims against ST Edge AI Core 4.0.1
  documentation, ST product pages, and ST example projects.
- Re-checked teacher claims against Hugging Face model cards, usage documents,
  configurations, and the published custom model source.
- Established what "Jev" is from TypeSafe's documentation, API reference, and
  customer agreement.
- Surveyed recent open "Jev-style" models, tiny-NLP research, and published
  STM32N6 measurements.
- Ran local arithmetic and an ONNX export/INT8 QDQ check inside the devcontainer.
- After the review, with your approval, implemented and measured an INT8 Vela
  2.0 9B teacher loader on the devcontainer's 12 GB GPU (F2).

Not done, and why:

- No NPU compilation: ST Edge AI Core is not installed (`/opt/st-tools` is empty).
- No board measurement: no hardware attached.
- Teachers other than the INT8 Vela 2.0 9B were not executed: Vela and Decision
  models require `trust_remote_code`, i.e. running third-party Python, which
  needs code review and your approval per release.
- The PDF (Idea0.pdf) is not in the workspace, so PDF-derived statements in the
  design could not be rechecked against their source.

Estimates in this document are labelled as estimates. Everything else is cited.

## 1. Executive Summary

**Verdict.** The design's direction is correct and the document is careful. The
new evidence strengthens its central conclusion:

- **Feasible:** Jev's *interface and decision semantics* (choice, yes/no, score,
  with calibrated probability distributions) over a **fixed, trained question
  catalogue**, served by a small task-specific student (roughly 0.1–1 M
  parameters) entirely from STM32N6 internal SRAM, at sub-millisecond to tens of
  milliseconds per decision.
- **Not feasible:** general Jev behaviour (arbitrary runtime questions, zero-shot)
  inside the N6. The smallest open general "Jev-style" models found are 32 M–150 M
  parameters ([Crivo-32M][crivo-32m], [Crivo-150M][crivo-150m]), at least ~30x the
  design's 1 MiB constant budget even at INT8, and they still degrade sharply on
  unseen domains.

Key findings, by priority:

| # | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | High | TypeSafe's [customer agreement][typesafe-mca] §2.3(b) forbids using Jev outputs to "perform model distillation" or "train a model to imitate" the service | Never use the Jev API as teacher or label source; use open Apache-2.0 teachers; add a licensing gate |
| F2 | High | Teacher landscape changed: Vela 2.0 0.8B was omitted, and the multimodal [Decision 3.0][d3-collection] family (0.6B–26B, Apache-2.0) was published days before this review; the 9B runs on a 12 GB GPU with INT8 weights (measured: 6.6 GiB, no decision changes in a 25-request parity check) | Replace the fixed teacher table with a teacher bake-off; use the INT8 loader in `teacher/` for the 9B |
| F3 | High | Vela 0.3B reads all questions in one bidirectional sequence (no isolation), so a label can depend on the co-asked questions; the decoder teachers isolate questions | Add labeling-contract tests; align teacher input with what the student sees |
| F4 | High | Jev and Vela define `confidence` differently; the design's "top-two margin" statement is Vela-specific | Choose and document the on-device contract explicitly |
| F5 | Medium | NPU efficiency rules matter for 1-D text (line buffer `W x C_in <= 2048`, pooling windows <= 3, Gather in software) | Put embedding, pooling, and heads on the M55; compile two tensor layouts and compare |
| F6 | Medium | 800 MHz CPU / 1 GHz NPU are *overdrive* clocks; nominal is 600 / 800 MHz | Budget latency and energy at nominal clocks |
| F7 | Medium | The question catalogue can be data, not firmware | Freeze a shared NPU trunk; ship per-question heads as versioned blobs |
| F8 | Medium | Boot details missing: signed FSBL/application, weight copy cost, update path | Add to M5; consider ST's runtime-loadable models |
| F9 | Medium | ST's validation projects target the STM32N6570-DK, not the Nucleo | Start M1 on the DK with external memories disabled |
| F10 | Low | DESIGN §11 says no devcontainer exists; it does and passes its smoke tests | Update the design |
| F11 | Strategic | If the target is robotics with a camera, vision is the N6's strength, and decision models fail on direct multi-way motor choices | Revisit modality in M0; decompose control into atomic questions |

Update 2 adds F12-F17 for the robot decision module: the module contract, label
sources per question, closed-loop data, exclusion of Jev-derived teachers, the
two-GPU d3 teacher, and the definition of European sourcing (§12).

Recommended path in one paragraph: resolve M0 (one task, modality, latency,
error costs). Install ST Edge AI Core in the devcontainer and run compile-only
nmapping experiments, which need no board. Build M55-only baselines (rules,
hashed n-grams, pruned static embeddings). Then train a convolutional student on
an NPU-friendly trunk with heads on the M55, distilled from an open teacher
selected by a measured bake-off.

## 2. What "Jev-like" Means

### TypeSafe Jev (the reference)

[Jev][typesafe-models] is TypeSafe's hosted, closed "System One" decision model
(`jev-1.13.0`, alias `jev-latest`). The [API][typesafe-api] takes a `state`
(string, object, or array) and a map of named typed questions:

| Type | Input | Output |
| --- | --- | --- |
| `noul` | yes/no instructions, optional true/false criteria | `noul` = P(yes) |
| `choice` | up to 255 options with descriptions | `choice`, `probabilities` (sum to 1), `confidence` |
| `score` | 2–10 ordered levels | expected level `score`, `legend`, `probabilities`, `confidence` |

Documented properties: text only; 64 k tokens per request; English is the primary
language; the same weights serve every account; "trained with RLCD to return
calibrated decisions"; "Jev ingests the `state` once and evaluates every question
against it in parallel." That last property maps naturally onto a shared encoder
with multiple heads on a microcontroller.

### The open "Jev-style" ecosystem

Several open models implement the SystemOne request/response shape:

- [Vela 2.0][vela-blog] (vLLM Semantic Router and KR Labs): 0.3B encoder, 0.8B,
  4B, 9B hybrids; adds `span` and `set` questions.
- [Decision 3.0][d3-collection] (vLLM Semantic Router): d3-edge 0.6B, d3-lite
  0.9B, d3-nano 2B, d3-mini 5B, d3-flash 8B, d3 26B; text, JSON, images, video.
- [Crivo-150M][crivo-150m] and [Crivo-32M][crivo-32m]: small ModernBERT/Ettin
  encoders with an `[OPT]` readout.
- [autotrust/JEV-35B][jev-35b]: an independent open model; its card states it is
  not affiliated with TypeSafe. Its sibling JEV-27B describes itself as a
  student of TypeSafe Jev 1.13 (Update 2, F15).
- The [Decision Index][decision-index] leaderboard and open kit benchmark these
  models.

### Size ladder: why general Jev cannot fit

| Model | Parameters | Generality evidence | INT8 weights alone |
| --- | --- | --- | --- |
| Crivo-32M | 32 M (12.5 M transformer core) | Decision Index 0.3 public index 25.06 | ~32 MB |
| Crivo-150M | 149 M | Full score 22.21; private new-domain tasks only 9.77 | ~149 MB |
| Vela 2.0 0.3B | ~307 M (196.6 M are embeddings) | Router and safety tasks | ~307 MB |
| d3-edge | 0.59 B | Decision Index 0.3.2 text board 20.2 | ~590 MB |
| Vela 2.0 0.8B | 756 M | Router + broad extraction | ~756 MB |
| d3-flash | 8.39 B | Decision Index 0.3.2 text board 55.8 | ~8.4 GB |
| **STM32N6 design budget** | — | — | **≤ 1 MiB constants, ≤ 3 MiB total SRAM** |

Conclusion: on the N6, "Jev-like" must mean the Jev *contract* (typed questions
in, calibrated distributions out) over a question catalogue trained in advance,
not Jev's open-ended capability. The design already says this; the size ladder
quantifies it.

## 3. Hardware and Toolchain Reality Check

### STM32N657 facts relevant to this project

| Item | Verified value | Source |
| --- | --- | --- |
| CPU | Cortex-M55 up to 800 MHz, Helium, FPU (half/single/double), 32 KB I-cache, 32 KB D-cache, 128 KB DTCM, 64 KB ITCM | [ST product page][st-n657] |
| NPU | Neural-ART up to 1 GHz, "600 GOPS", 288 MAC/cycle | [ST product page][st-n657] |
| NPU units | 4 CONV_ACC (72 8x8 MAC/cycle each, or 18 16x16), 2 POOL, 2 ACTIV, 4 ARITH, 2x5 stream engines, 2 weight-decompression units, epoch controller | [ST NPU concepts][st-concepts] |
| Arithmetic | Integer only, 8/16/24-bit datapaths, no floating point | [ST NPU concepts][st-concepts] |
| SRAM | 4.2 MB contiguous; NPU sees 4 x 448 KB fast NPU RAMs, plus 400 KB FlexMEM, 624 KB, and 1 MB system SRAM; 256 KB NPU-cache RAM usable as normal RAM when the NPU cache is unused | [ST NPU concepts][st-concepts] |
| Flash | None internal; boot from external flash or development mode | [ST getting-started][st-gs-ic] |

Clock modes from [ST's project guide][st-projects]:

| Domain | Normal (VDDCORE 0.8 V) | Overdrive (0.9 V) |
| --- | --- | --- |
| CPU | 600 MHz | 800 MHz |
| NPU | 800 MHz | 1000 MHz |
| NPU RAMs | 800 MHz | 900 MHz |
| CPU RAMs and AXI | 400 MHz | 400 MHz |

### Internal memory map in ST's default memory-pool example

From the [compiler documentation][st-compiler]:

| Region | Base address | Size | Use in ST's example |
| --- | --- | --- | --- |
| FLEXMEM | `0x34000000` | 400 KiB | Firmware; pool size set to 0 |
| AXISRAM1 | `0x34064000` | 624 KiB | Firmware; pool size set to 0 |
| AXISRAM2 | `0x34100000` | 1,024 KiB | NPU pool `cpuRAM2` |
| AXISRAM3–6 | `0x34200000`, `0x34270000`, `0x342E0000`, `0x34350000` | 4 x 448 KiB | NPU pools `npuRAM3–6`, fastest for the NPU |
| xSPI1 (DK) | `0x90000000` | 32 MiB | External RAM; excluded for internal-only |
| xSPI2 | `0x70000000` | 64 MiB | External flash; excluded for internal-only |

Implication: with ST's default split the NPU gets about 2.75 MiB of contiguous
SRAM and the firmware about 1 MiB. The design's budgets (≤ 1 MiB constants,
≤ 512 KiB activations) fit with margin. **For a sub-million-parameter student,
memory is not the binding constraint; task quality is.**

### Operator mapping relevant to text

From the [operator table][st-operators]:

| Operator | Mapping | Consequence |
| --- | --- | --- |
| Conv (1-D/2-D), constant weights | Hardware | Main building block |
| Gemm / MatMul | Hardware only if the second input is constant | Dense layers fine; attention products fall back |
| Gather | Software integer | Embedding lookup belongs on the M55 |
| Softmax | Hardware only with `--expand-softmax`; otherwise software | Keep final probabilities on the M55 |
| GELU, Sigmoid, Tanh | Hardware | Usable activations |
| ReduceMean / ReduceMax | Hardware only if convertible to global pooling | Masked pooling is better done on the M55 |
| GlobalAveragePool / GlobalMaxPool | "Limited window", software fallback | Pooling over long sequences may fall back |
| Div | Software unless the divisor is constant | LayerNorm-style normalization partly falls back |
| InstanceNormalization | Software float | Avoid |
| MaxPool | Decomposed if a window dimension exceeds 3 | Use small windows |

Efficiency rules from the same page: maximum kernel width 6 (stride 1) and height
3; kernels with a dimension of 1 run efficiently; for INT8, feature width times
input channels should be at most 2,048 or the compiler splits work; pooling line
buffers have the same 2,048 limit; avoid prime channel counts; 1x1 convolutions
are most efficient with input channels in multiples of 72–128 and output
channels in multiples of 16–24 (best 24).

### Runtime facts

- Software scheduling of hardware epochs costs roughly 10–15% MCU load; the epoch
  controller reduces it ([concepts][st-concepts]).
- There is no host NPU emulator and bit-exactness is not expected
  ([concepts][st-concepts]).
- Copying about 2 MB of weights from flash to internal RAM took 17–18 ms in ST's
  measurement, i.e. roughly 9 ms/MB ([runtime-loadable models][st-reloc]).
- A tiny model in that ST example ran in 0.218 ms in total, a useful floor for
  fixed overhead.

### Published STM32N6 measurements

| Workload | Result | Source |
| --- | --- | --- |
| Event-camera eye tracking CNN | 385 µs end-to-end, 52 MAC/cycle (≈18% of peak), 155 µJ | [arXiv 2508.13244][eye-tracking] |
| CubeSat image classifiers, pruned INT8 | 3.2–30.4 ms, 0.68–6.45 mJ per inference | [arXiv 2603.20174][cubesat] |
| Speech enhancement split into several NPU graphs | Splitting adds 2.2% latency; M55 policy 26 µs/frame | [arXiv 2609.29867][speech] |
| Line-segment detection | Attention, grid sampling, and normalization lack NPU primitives; decoder attention would need a 39 MB score tensor | [arXiv 2609.25022][nplsd] |
| YOLOv11 with attention | Needed a head-wise attention refactor for the NPU; 2.48 MB footprint, 10 FPS | [arXiv 2607.16222][argo] |
| Learned feature extractor | 9.0 ms, < 1.5 MB; replacing BatchNorm with affine layers improved INT8 robustness | [arXiv 2605.04282][gideon] |
| M55-only small INT8 CNN (ST example) | 1.08 M MAC in 0.986 ms, 0.73 cycles/MAC | [ST project guide][st-projects] |
| GAP9 vs STM32N6 vs IMX500 | N6 had the lowest latency but higher energy than GAP9 | [arXiv 2603.08725][edge-review] |

Derived (not reported directly): 155 µJ over 385 µs and 0.68 mJ over 3.22 ms
imply roughly 0.2–0.4 W while inferring. Treat this as an order of magnitude for
power planning, not a project measurement.

## 4. Verification of DESIGN.md Claims

Legend: ✓ verified, ⚠ correct but incomplete or needs qualification,
✗ incorrect or outdated, ? not verifiable here.

| Claim in DESIGN.md | Status | Evidence and notes |
| --- | --- | --- |
| N6x7 has Neural-ART, N6x5 does not | ✓ | Product page lists the NPU as "STM32N6x7 only" |
| CPU up to 800 MHz, NPU up to 1 GHz, ~600 GOPS | ⚠ | True, but only in overdrive; nominal is 600 / 800 MHz (F6) |
| About 4.2 MB banked SRAM | ✓ | See §3 for the bank map |
| No internal flash; SRAM development load is temporary | ✓ | ST getting-started boot modes |
| Static shapes; INT8 ss/sa per-channel; ONNX QDQ or TFLite | ✓ | [Quantization guide][st-quant] recommends static QDQ, QInt8, per-channel |
| MatMul in hardware needs a constant second input; Gather in software | ✓ | Operator table |
| Profile `--st-neural-art profile-internal-memories-only--default` | ✓ | Built-in profile list and `profile-<tool_profile>` syntax |
| `--expand-softmax` keeps the argmax but not exact probabilities | ✓ | Compiler guide; `--expand-softmax-full` is the more precise option |
| Application must copy SRAM-resident weights | ✓ | [Memory initializers][st-initializers] |
| No host NPU emulator | ✓ | NPU concepts |
| CM55 validation example assumes external-flash weights | ✓ | Project guide: "Weights are necessarily stored in the external flash" |
| `USE_EXTERNAL_MEMORY_DEVICES=0` | ✓ | Project guide (NPU validation project) |
| Vela 0.3B: 22 layers, width 768, intermediate 1,152, 12 heads, vocabulary 256,008 | ✓ | [config.json][vela-03b-config]; total ≈ 306.9 M parameters recomputed |
| Embeddings 196,614,144 parameters (187.5 MiB at 1 byte) | ✓ | Recomputed |
| ≈ 28.2 GOP linear projections for 128 tokens | ✓ | Recomputed: 28.24 GOP |
| Ternary 60.8 MB, 2-bit 76.75 MB for 307 M parameters | ✓ | Arithmetic correct |
| Vela 0.3B Torch path is FP32 only | ⚠ | Correct; also note the official ONNX FP16-encoder path (≤ 0.006 choice-probability difference, no decision changes on 230 rows) |
| Vela 4B ≈ 17 GB FP32 | ✓ | 4.2 B parameters x 4 bytes |
| Vela 9B ≈ 32 GB; loader rejects lower precision; `device_map="auto"` only moves to CUDA | ✓ | [Source][vela-9b-code]; F2 measures the INT8 route on a 12 GB GPU |
| Choice `confidence` is the top-two margin | ⚠ | True for Vela; Jev uses a different formula (F4) |
| Extra span questions and long inputs add sequences | ✓ | Vela usage documents |
| PDF student is ≈ 1.894 M parameters, not 4 M | ? | PDF unavailable; result depends on FFN width (see below) |
| No devcontainer examples in the workspace (DESIGN §11) | ✗ | `.devcontainer` exists with CPU, CUDA/Docker, and Podman/WSL profiles, CA handling, and passing smoke tests |
| Teacher table: 0.3B, 4B, 9B | ⚠ | Missing Vela 0.8B and Decision 3.0 (F2) |
| Task-specific distillation has published support | ✓ | [Tang et al.][tang]: single-layer BiLSTM comparable to ELMo with ~100x fewer parameters and 15x less inference time |

PDF student parameter count, recomputed with PyTorch modules for width 256,
3 layers, vocabulary 1,024, 64 positions, and 5 classes:

| `dim_feedforward` | Parameters |
| --- | --- |
| 512 | 1,861,125 |
| 1,024 | 2,649,093 |
| 2,048 (PyTorch default) | 4,225,029 |

The design's 1.894 M is close to the 512-wide result; the remaining ~33 k could
come from a small extra head or normalization layer. If the PDF code relied on
the `nn.TransformerEncoderLayer` default, its "four million" was correct.
Re-derive from the PDF's actual code before keeping the correction.

## 5. Findings in Detail

### F1 (High): Jev's terms prohibit distillation from Jev

TypeSafe's [Master Customer Agreement][typesafe-mca] (last updated 2026-09-23),
§2.3(b): the customer will not "use the Services or any Output … to perform model
distillation, train a model to imitate the output of the Services, or develop (or
to facilitate the development of) a similar or competing product or service."

Consequences:

- The hosted Jev API cannot be a teacher, label source, or imitation target.
- Even using Jev outputs to select or tune the student is a legal grey area;
  get legal review before any Jev-in-the-loop evaluation.
- Open alternatives exist and are licensed for this use: Vela 2.0 and Decision
  3.0 are Apache-2.0. Corrected in Update 2: this review also listed
  autotrust/JEV-35B, whose weights are Apache-2.0, but the JEV family trains on
  Jev-distilled labels (F15), so it is excluded.
- Crivo models are CC BY-NC 4.0 and therefore unsuitable for commercial use.
- Vela's training data includes CC-BY-SA sources, and the Vela 0.3B tokenizer
  carries Gemma terms. Do not reuse that tokenizer in the student: it is also a
  256 k vocabulary, far too large for the MCU.

Add a licensing gate to M0 and M3 that records the license of each teacher,
dataset, tokenizer, and generated label set.

### F2 (High): Teacher landscape update and selection

| Teacher | Parameters | Inputs | Question isolation | Documented memory | Documented speed | Host fit |
| --- | --- | --- | --- | --- | --- | --- |
| [Vela 2.0 0.3B][vela-03b] | 307 M | Text, 17 languages | No; one bidirectional sequence | ≈ 1.2 GB FP32 parameters (derived) | 0.09 s per full router request (A40) | Laptop GPU or CPU; ONNX path |
| [Vela 2.0 0.8B][vela-08b] | 756 M | Text, 17 languages | Yes ("bundled == single") | ≈ 3 GB FP32 parameters | 0.13 s (A40) | Fits the 12 GB laptop GPU in the devcontainer README |
| Vela 2.0 4B | 4.2 B | Text | Yes | ≈ 17 GB FP32 | 0.40–0.49 s (A40) | One 24 GB GPU, tight |
| Vela 2.0 9B | 7.9 B | Text | Yes | ≈ 32 GB FP32 | 0.60–0.71 s (A40) | 12 GB GPU with the INT8 loader in `teacher/` (measured below); 24 GB GPU with BF16 weights and a similar loader |
| [d3-edge][d3-edge] | 0.59 B | Text, JSON, images, video | Per-question forward passes | 5.2 GiB peak (one request) | 6.6 ms text, 58.6 ms image (MI325X) | Laptop GPU |
| [d3-lite][d3-lite] / [d3-nano][d3-nano] / [d3-mini][d3-mini] | 0.85 / 2.21 / 4.54 B | Multimodal | Same | 5.7 / 9.1 / 14.8 GiB peak (one request) | Not stated | Laptop GPU for lite and nano; mini needs more than 12 GB as released, but about 7.3 GiB of BF16 weights with host-side embeddings (estimate) |
| [d3-flash][d3-flash] | 8.39 B | Multimodal | Same | 23.8 GiB peak (one request) | 19.2 ms text, 166 ms image (MI325X) | 24 GB GPU, borderline as released; about 13.7 GiB of BF16 weights with host-side embeddings, 7.4 GiB with INT8 projections (estimates); planned first teacher on the 12 GB GPU |
| [d3][d3] | 26.09 B | Multimodal | Same | 61.8 GiB peak (one request) | 54.4 ms text, 290 ms image (MI325X) | Two 24 GB GPUs with INT8 projections (planned, §12) |
| [JEV-35B][jev-35b] | 35 B MoE, ~3 B active | Text, images | Not stated | 66.5 GiB BF16; 23.3 GiB NVFP4 | 204 ms median (B200) | Excluded (F15) |

Notes:

- Decision 3.0 model cards were still being updated on the review date. Pin
  revisions and expect churn.
- Prefer teachers with question isolation: labels then do not depend on which
  other questions were asked in the same call.

#### Running the 9B teacher on a 12 GB GPU

An 8-bit 9B fits a 12 GB GPU; it is just not plug-and-play. Update after the
review: the loader below is implemented and measured, with full tables in
[DESIGN.md](DESIGN.md) §4 and the raw
[report](teacher/reports/vela-2.0-9b-int8-g128-rtx-a3000.json).

Why the published path does not fit: the custom `from_pretrained` refuses any
dtype other than FP32, builds and loads the model itself (so Transformers
quantization options such as 8-bit loading never apply), casts every tensor to
FP32, and then moves the whole model to CUDA ([source][vela-9b-code]). That needs
about 32 GB of GPU memory and about as much CPU RAM while loading. No quantized
Vela 2.0 9B was published on Hugging Face as of the review date.

Weight memory, computed from the published [config][vela-9b-config] (hidden size
4,096, 32 layers of which 8 use full attention and 24 Gated DeltaNet, MLP width
12,288, vocabulary 248,320). The config states that backbone Linear and conv1d
weights are stored in BF16 and everything else, including the embedding table,
in FP32.

| Weight format | GPU weight memory |
| --- | --- |
| Official load, all FP32 | 31.8 GB |
| As stored (Linear BF16, rest FP32) | 18.0 GB |
| All BF16 | 15.9 GB |
| INT8 Linear, BF16 embeddings | 9.0 GB |
| INT8 Linear, INT8 embeddings | 8.0 GB |
| INT8 Linear, embeddings kept on the CPU | 7.0 GB |
| GGUF-style Q8_0 (8.5 bits per weight) | 8.5 GB |
| About 4.5 bits per weight, INT8 embeddings | 5.0 GB |

Of the 7.95 B parameters, 6.91 B sit in large backbone projections and 1.02 B in
the embedding table; heads, norms, gates, and convolutions total about 20 M.
Activations are small at teacher-sized inputs: the largest transient (the MLP)
is about 0.04 GiB at 512 tokens and 1.1 GiB at the 16,384-token maximum. The
measured run needed more: about 1.1 GiB for the CUDA context and workspaces, and
peak allocations of 7.1 GiB for short requests, 10.1 GiB at 12.3 k tokens, and
11.2 GiB at 16.3 k tokens. That is 4.6 GiB above the weights, several times the
MLP-only estimate; the FP32 PyTorch Gated DeltaNet kernel is the likely cause
but was not profiled. F3 already requires the teacher to see the student's
short, truncated view, so long-context activations should not arise during
labeling.

Implemented recipe ([teacher/vela_int8.py](teacher/vela_int8.py), weight-only
INT8 with BF16 compute):

1. Build the model skeleton on PyTorch's meta device, then stream tensors one at
   a time from the safetensors files. Peak host memory was 5.1 GiB.
2. Quantize only the large projections: MLP gate/up/down, attention q/k/v/o, and
   Gated DeltaNet `in_proj_qkv`, `in_proj_z`, and `out_proj`, as symmetric INT8
   with one BF16 scale per 128 input columns. Keep conv1d, the
   `in_proj_a`/`in_proj_b` gates, `A_log`, `dt_bias`, norms, and all heads FP32
   as released. Per-row scales doubled the largest probability change (0.029
   versus 0.013) and saved only 0.1 GiB.
3. Dequantize to BF16 right before each matmul in a small custom Linear. FP16
   compute is avoided: Vela states FP16 is not supported, and older bitsandbytes
   LLM.int8() releases cast BF16 activations to FP16.
4. Keep the FP32 embedding table in host RAM and copy only gathered rows to the
   GPU.
5. Leave Vela's tokenizer, rendering, windowing, calibration, and SystemOne
   engine unchanged; only backbone storage changes.

Measured on the devcontainer's RTX A3000 12 GB laptop GPU under WSL2, with
Transformers' PyTorch Gated DeltaNet kernel (flash-linear-attention is not
installed):

| Measurement | Result |
| --- | --- |
| GPU memory after load | 6.6 GiB of parameters (6.44 INT8, 0.10 scales, 0.08 FP32); 7.7 GiB in use with the CUDA context |
| Short SystemOne requests | Median 0.85 s each; 2.0 rows/s batched at a 2,048-token budget |
| Long single inputs | About 1,240 tokens/s up to 12.3 k tokens; 16.3 k tokens exceeded GPU memory and took 85 s |
| INT8 vs streamed BF16 reference, 25 requests, 273 probabilities | Max abs difference 0.013, mean 0.0009; no decision, label, or span changes |
| INT8 and BF16 reference vs the release's recorded outputs | Max abs difference 0.009 and 0.002 |

Validation, revised: instead of a 24 GB GPU or 32 GB of host RAM, the BF16
reference streams the release's stored BF16 projection weights from the
safetensors shards into the same kernels, which is exactly the evaluated
computation. Its 0.002 agreement with the recorded outputs also shows that the
fallback Gated DeltaNet kernel, which the source calls not parity-tested on GPU,
reproduces the release on these examples. Still required before using INT8
labels:

- The same comparison on the project's 300–500-row reviewed set, adding KL
  divergence per question type.
- A calibration re-check: Vela's temperatures and thresholds were fitted on the
  BF16-autocast path.
- The bake-off: judge the INT8 9B like any other teacher, by accuracy, NLL, and
  calibration error against human labels. Parity explains differences; task
  quality decides.

Throughput: the earlier estimate (13.8 GFLOP per token, roughly 0.35–0.7 s per
512-token sequence) matched. Long inputs ran at about 1,240 tokens/s, and short
requests took a median 0.85 s including fixed overheads. At 2 short rows per
second, a 20,000-example pilot takes about 3 hours. Keep the batch budget at
2,048 tokens: at 4,096 the allocator reserved 13.6 GiB, WSL2 spilled to system
memory instead of failing, and throughput fell to 0.63 rows/s.

Why not a GGUF Q8_0 file: llama.cpp could at most run the Qwen3.5 backbone (if
it supports that hybrid architecture). Vela's readout heads, prefix-sharing tree
forward, rendering, and calibration would have to be rebuilt around per-token
hidden states. That is possible, because each question is documented to equal
the single sequence of the shared prefix plus its own block, but it is far more
work than a PyTorch loader for the same roughly 8.5 GB of memory.

4-bit weights (about 5 GB) carry more quality risk; use them only if 8-bit does
not fit, for example with large batches. Teachers that fit 12 GB without
quantization: Vela 0.8B (about 3 GB FP32), d3-edge (5.2 GiB peak), and Vela 4B in
BF16 (about 8.4 GB, also needing a custom loader).

Recommendation: replace the fixed teacher table with a bake-off on the reviewed
evaluation set. Measure accuracy or macro-F1 against human labels, NLL, Brier
score, calibration error, per-class recall, and cost. A larger teacher is not
automatically better for a specific domain, as the design already notes.

### F3 (High): Labeling contract details

1. **Cross-question dependence in Vela 0.3B.** The published
   [layout][vela-03b-config] places all questions before the state in one
   sequence (`<bos> ([Q] q ([O] name: desc)* …)* … [SEP_SCHEMA] ([SEG_role] part)* <eos>`),
   and the [model source][vela-03b-code] calls the encoder with a plain padding
   mask. Every question can therefore attend to every other question. Test single
   versus bundled versus permuted questions; if results differ materially, label
   one question per call or fix and record the bundle.
2. **Teacher-student view alignment.** If the student sees only the first T
   tokens, the teacher must label exactly that truncated text. Otherwise the
   student is trained to predict information it never receives. Crivo-32M's
   recipe does exactly this: "Teacher logits were precomputed once on exactly the
   tokens the student sees (same rendering and truncation)."
3. **Rendering provenance.** Record state serialization (JSON key order),
   question text, option descriptions and order, model revision, calibration
   flags (for example Vela's optional `noul_calibration`), and thresholds.
4. **Store logits where available.** The Vela 0.3B ONNX path returns
   `opt_logits`; logits allow consistent temperature handling during
   distillation.
5. **Option order.** Permute options during labeling and training so neither
   model learns position.
6. **Loss reference.** [Crivo-32M][crivo-32m] used
   `L = 0.5·[CE(gold) + 0.5·Brier(gold)] + 0.5·τ²·KL(teacher_τ ‖ student_τ)`
   with τ = 2 for three or more options and τ = 1 for binary questions, and
   gold-only loss where the teacher is weak. This is a reasonable second
   experiment after the design's temperature-1 baseline.
7. **Transfer set.** [Tang et al.][tang] build distillation data with simple
   augmentation (masking, part-of-speech-guided word replacement, n-gram
   sampling). Label in-domain unlabeled and augmented text with the teacher, not
   only the human-labeled set.

### F4 (High): Define the on-device Jev-compatible contract

The two reference systems compute `confidence` differently:

| Answer type | TypeSafe Jev ([docs][typesafe-confidence]) | Vela 2.0 ([usage][vela-03b-usage]) |
| --- | --- | --- |
| Choice | (p_max − 1/n) / (1 − 1/n) | p_1 − p_2 (top-two margin) |
| Score | max(0, 1 − Σ p_i·\|i − m\| / MAD_uniform), m = mode | "One minus the normalised variance"; 1 − Var(p) / Var(uniform) reproduces Vela's example |
| Noul | None returned; suggests \|2p − 1\| | None returned |

Worked example from Vela's own output, choice probabilities (0.727, 0.217,
0.056): Vela reports 0.51; Jev's formula gives 0.59. Score probabilities
(0.469, 0.336, 0.194): Vela reports 0.118; Jev's formula gives 0.

Recommendation: state in the design which semantics the device implements. If the
goal is drop-in Jev API compatibility, implement TypeSafe's formulas on host and
device. Always return the full `probabilities`, keep Jev's limits (≤ 255 options,
2–10 score levels), report the versioned model ID, and keep the design's rule that
`confidence` is a distribution statistic, not a probability of being correct.

### F5 (Medium): NPU-friendly text trunk

Recommended data path:

```mermaid
flowchart LR
  A["Text or typed state"] --> B["M55: validate, normalize, tokenize"]
  B --> C["M55: INT8 embedding gather into the NPU input buffer"]
  C --> D["Neural-ART: static INT8 conv trunk (Conv + ReLU)"]
  D --> E["M55: masked max/mean pooling over true length"]
  E --> F["M55: per-question heads (versioned blobs)"]
  F --> G["M55: softmax/sigmoid, temperature, confidence, rejection"]
  G --> H["Typed Jev-shaped result"]
```

Why this split:

- Gather is software on the NPU anyway; writing INT8 embeddings straight into the
  input buffer costs only T x d bytes (12 KiB for T = 128, d = 96).
- Masked pooling on the M55 removes padding artifacts exactly and avoids
  global-pooling window limits. Reading a 128 x 128 INT8 feature map is 16 KiB.
- Heads on the M55 cost K x C MACs, microseconds, and make the question catalogue
  replaceable data (F7).
- The NPU graph becomes Conv + ReLU only: static, fully mappable, and simple to
  validate.

Layout experiment. ST's line-buffer rule (`feature width x input channels <= 2048`
for INT8) suggests that `[1, C, 1, T]` with 1x3 kernels splits work when
`T x C > 2048` (for example 128 x 128 = 16,384), while `[1, C, T, 1]` with 3x1
kernels keeps the width at 1. Both kernel shapes have a dimension of 1, which ST
says is efficient. This is a hypothesis; compare epoch counts and estimated
cycles in the compiler reports (`--mapping-recap`, `--csv-file`).

Local check run for this review: both layouts exported from PyTorch at opset 13
and quantized with ONNX Runtime static QDQ (QInt8, per-channel, asymmetric
activations) produce only `Conv`, `QuantizeLinear`, and `DequantizeLinear` nodes,
static input shapes, and per-channel axis 0, which matches ST's documented
requirement. Whether the ST compiler maps them efficiently still needs the tool.

Other trunk guidance: prefer channel counts aligned with the conv units (for
example 96 or 128 inputs and 24, 48, or 96 outputs), avoid prime channel counts,
use kernel widths of 3 or 6 and small dilations, fold BatchNorm, and avoid
LayerNorm and attention in the first version.

### F6 (Medium): Clocks, power, and energy

The headline 800 MHz / 1 GHz figures require overdrive at VDDCORE 0.9 V. Budget
latency at nominal clocks (600 MHz CPU, 800 MHz NPU) and treat overdrive as an
optional gain measured separately for energy and thermals. ST also notes that in
the recommended asynchronous runtime mode the core executes `WFE`; the NPU, NPU
RAMs, and any memories used must stay clocked in low-power modes or inference
never completes.

### F7 (Medium): Make the question catalogue data, not firmware

Freeze a shared trunk on the NPU and store per-question heads as small versioned
blobs evaluated on the M55. To add or change a question:

1. Label in-domain data for the new question with the chosen teacher.
2. Train only the head on frozen trunk features.
3. Calibrate it on held-out data through the deployed numeric path.
4. Pass the same gates as any other release, then ship the blob.

No NPU recompilation is needed. Trunk updates can use ST's
[runtime-loadable model][st-reloc] support (relocatable binaries installed without
reflashing the application) or a normal firmware update.

The limit: frozen features must contain the information a new question needs.
Train the trunk multi-task on a diverse set of in-domain questions. This gives
runtime configurability *within a domain*; it is not zero-shot.

### F8 (Medium): Boot and persistence specifics

- ST's flash boot uses an FSBL, a signed application
  (`STM32_SigningTool_CLI … -t ssbl -hv 2.3`, programmed at `0x70100000` in ST's
  example), and separately programmed network parameters ([ST
  getting-started][st-gs-ic]).
- Copying weights into internal SRAM costs about 9 ms/MB (§3), negligible at
  boot.
- Memory initializers can be C arrays copied by startup code, provided the target
  RAM is enabled and clocked first, or raw images placed by a loader
  ([initializers][st-initializers]).
- The NPU is not TrustZone-aware; isolation uses RIF compartment IDs, and RISAF
  defaults block accesses that are not secure, privileged, CID 1
  ([project guide][st-projects]). Plan RIF/RISAF configuration as part of M5.

### F9 (Medium): Board choice for M1

ST's NPU validation and CM55 validation projects live under
`Projects/STM32N6570-DK/Applications/`, and the runtime-loadable evaluation
environment supports only the STM32N6570-DK ([project guide][st-projects],
[runtime-loadable models][st-reloc]). The NUCLEO-N657X0-Q is supported by ST's
image-classification application but will need porting for the validation
tooling. Start M1 on the DK with `USE_EXTERNAL_MEMORY_DEVICES=0`, then move to the
Nucleo if its form factor is preferred.

### F10 (Low): Housekeeping and numerical parity

- DESIGN §11 is outdated: the devcontainer exists and its README records passing
  CPU and Podman/WSL GPU smoke tests.
- Pin one ST Edge AI Core release. ST's image-classification example uses 4.0.0,
  the design cites 4.0.1 documentation, and mismatched generated code fails with
  "Possible mismatch in ll_aton library used".
- The distro Arm compiler is GCC 13.2.1. The relocatable-model flow builds with
  `arm-none-eabi-gcc` from `PATH`; pin the toolchain ST tests against.
- ST's [quantization guide][st-quant] warns that ONNX Runtime on x86-64 with AVX2
  or AVX-512 can saturate in U8S8 kernels. Treat the host INT8 reference as an
  approximation and check for saturation before attributing mismatches to the
  NPU.
- EmbBERT's reported 8-bit result used weight-only block quantization with FP16
  activations; it is not evidence for full-INT8 NPU deployment.

### F11 (Strategic): Modality and task decomposition

The STM32N6 is a vision-first MCU: its ISP output can be DMA'd into the NPU, and
ST's image-classification examples run in 1–44 ms. Decision 3.0 now offers open
multimodal Jev-style teachers. If the robotics application in the PDF uses a
camera, a vision student answering fixed questions about frames may be a better
fit than text.

The [JEV-35B card][jev-35b] adds a design lesson: in a simulated pick-and-place
task, a binary-decision servo (two binary questions per step: left or right,
above or below) reached 75% success, while "direct choice among 8 motor actions"
scored 0%; the card advises to "decompose control into simple visual questions."
Atomic binary and small choice questions are also the easiest to distill into
tiny heads.

## 6. Feasibility Analysis

### 6.1 Capability tiers

| Tier | Delivers | N6 internal SRAM | Notes |
| --- | --- | --- | --- |
| T0: one fixed question | Jev-shaped answer for one trained question | Credible | Design milestones M1–M4 |
| T1: fixed catalogue, shared trunk, K heads | Many questions per encoder pass, like Jev's "state once" | Credible | Head cost K x C MACs on the M55 |
| T2: host-compiled heads | New in-domain questions without firmware or NPU changes | Credible if trunk features transfer | Each head passes the same gates (F7) |
| T3: fixed-label span tagging | Per-token labels, for example fixed PII types | Credible for lexical labels | Grounded hallucination spans need pairwise reasoning: not credible |
| T4: on-device option scoring | Runtime option text scored on the device | Research | Crivo's `[OPT]` readout is the reference design, but at 32 M+ parameters |
| T5: general zero-shot Jev | Arbitrary questions | Not credible internally | See the external-memory estimate below |

External-memory estimate for T5 (order of magnitude, not measured): a Crivo-32M-
class encoder (12.5 M-parameter core) at 256 tokens needs about 3.2 G MAC of
projections plus about 0.5 G MAC of attention products per question. With
attention on the M55 at ~1.1 G MAC/s, projections on the NPU, and weights streamed
from external flash, this is roughly 0.5–1 s per question, and Crivo-style models
need one sequence per question. Combined with weak new-domain quality, this is a
research stretch only.

### 6.2 Compute and memory for candidate students

Estimates computed for this review. Assumptions: INT8; M55 at 800 MHz and 0.73
cycles/MAC (ST's measured CM55 example; real kernels vary roughly 0.5–2); NPU at
1 GHz with 30–100 effective MAC/cycle (published N6 work reached ~52). Excludes
nepoch overhead, preprocessing, and I/O.

| Candidate | Parameters (INT8) | MACs | Peak activations | M55 only | NPU compute |
| --- | --- | --- | --- | --- | --- |
| A: hashed n-gram bag 16 k x 64 + MLP | 1.06 M (≈ 1.0 MiB) | 0.03 M | ≈ 16 KiB | ≈ 0.02 ms | Not needed |
| B: byte CNN, T = 512, 4 conv blocks with pooling | 155 k | 18.9 M | ≈ 48 KiB | ≈ 17 ms | ≈ 0.19–0.63 ms |
| C: subword CNN, vocabulary 4,096, d = 96, T = 128 | 587 k | 23.6 M | ≈ 32 KiB | ≈ 22 ms | ≈ 0.24–0.79 ms |
| D: transformer d = 128, 2 layers, T = 128 | 937 k | 50.3 M dense + 8.4 M attention | ≈ 112 KiB | ≈ 54 ms | Dense ≈ 0.5–1.7 ms; attention on M55 ≈ 8 ms |
| E: numeric-state MLP 64-256-256-8 | 85 k | 0.08 M | < 1 KiB | ≈ 0.08 ms | Not needed |
| [EmbBERT][embbert] (paper, 256 tokens) | 357 k | ≈ 136 M | ≈ 128 KiB | ≈ 124 ms | Attention-bound |

Observations:

- Memory is comfortable for every candidate. Embedding tables, not layers,
  dominate parameter counts.
- Small CNN students would run in tens of milliseconds on the M55 alone. The NPU
  gives roughly 25–90x on the trunk (compute only), which matters for tight
  deadlines, battery life, or larger trunks, but an M55-only fallback is viable
  for first baselines.
- For transformer students, the software-fallback attention dominates latency
  (Amdahl's law), yet ≈ 10 ms total may still be acceptable. The design's
  "CNN/MLP first, profile transformers" stance is quantitatively sound.

### 6.3 Expected task quality

- [EmbBERT][embbert] (2 MB total memory, FP32 accounting) on narrow tasks
  (TinyNLP): EmbBERT 87.19%, a 10x larger BERT-Tiny 86.99%, an embedder-only model
  86.41%. On pairwise and reasoning tasks (GLUE): EmbBERT 63.50, BERT-Tiny 63.16,
  embedder-only 56.92. Simple models suffice for routing and intent-style
  questions; questions comparing two text parts benefit from token interaction.
- [pQRNN][pqrnn]: 1.3 M INT8 parameters reached AUC 0.963 on civil_comments
  versus 0.976 for a 110 M-parameter BERT, without pretraining. Its projection
  layer hashes tokens to ternary features and has no embedding table.
- [Crivo-150M][crivo-150m]: 27.74 on private same-skill tests, but 9.77 on
  private new-domain tasks. Small decision models do not generalize across
  domains; validate per task.

## 7. Alternatives

### 7.1 Model alternatives

| Option | Runs on | Strengths | Weaknesses | Recommendation |
| --- | --- | --- | --- | --- |
| Rules and keyword logic | M55 | Deterministic, auditable | Brittle with paraphrase | Mandatory baseline (design already requires it) |
| Hashed n-gram linear model (fastText-like) | M55 | No vocabulary file, tiny compute, robust baseline | No word order beyond n-grams | First learned baseline |
| [Model2Vec][model2vec]-style static embeddings, pruned vocabulary and reduced dimension + linear head | M55 | Distilled from sentence encoders; trivial compute | Smallest listed model is 7.5 M parameters; needs vocabulary pruning; inherits the source tokenizer (WordPiece for the listed English models) | Strong baseline after pruning |
| Projection network ([PRADO/pQRNN][pqrnn]) | M55, conv parts on NPU | No embedding table, < 200 k–1.3 M parameters | QRNN recurrence is not NPU-friendly; replace with convolutions | Good fit for the memory budget |
| 1-D CNN student (design's choice) | NPU trunk, M55 rest | Fully mappable, fast | Limited long-range interaction | Primary candidate |
| Tiny transformer / [EmbBERT][embbert] | NPU dense, M55 attention | Better pairwise reasoning | Attention falls back to software | Second candidate if CNN quality fails |
| Ternary / BitNet | — | Smaller storage at rest | The NPU computes INT8: weights occupy INT8 SRAM during inference regardless of storage format | Do not pursue for SRAM savings |
| Binary (ST DQNN) | M55 only | Very small | No NPU path | Not recommended |

The ternary point deserves emphasis: for NPU execution, SRAM holds INT8 weights.
Ternary training could only reduce flash storage, unless ST's hardware weight
decompression (present in the silicon, not exposed in the 4.0.1 documentation
reviewed) becomes usable.

### 7.2 Hardware alternatives

| Option | Relevant facts | When to consider |
| --- | --- | --- |
| STM32N6, internal only (current plan) | §3 | Default |
| STM32N6 with external memory (DK) | External NOR flash and PSRAM; NPU cache for external regions | Larger trunks or T5 research; breaks the internal-only constraint |
| [Alif Ensemble E4][alif-e4] / [E8][alif-e8] | Cortex-M55 up to 400 MHz; three NPUs (E8: Ethos-U85 plus two Ethos-U55; Ethos-U85 has native transformer support per [Arm][ethos-u85]); E4 has "over 15 MB of on-die memory"; E8 adds dual Cortex-A32 | If attention-based students become necessary or more on-die memory is needed; US company, so not a European-sourcing option (corrected in Update 2) |
| [Infineon PSoC Edge E84][psoc-edge-e84] | Cortex-M55 at 400 MHz, Ethos-U55 NPU, up to 6 MB SRAM, CAN-FD | European vendor (Germany); smaller NPU than the N6 |
| [NXP i.MX RT700][nxp-rt700] | Cortex-M33 325 MHz, eIQ Neutron NPU, up to 7.5 MB SRAM | Larger SRAM; European vendor; no Helium |
| Linux-class MPU with NPU and DRAM | Runs 100 M+ parameter decision encoders | If general Jev behaviour is a hard requirement |

### 7.3 System alternatives

- **Cascade with explicit deferral.** The MCU answers confident cases; uncertain
  cases defer to a larger open Jev-style model when a link exists, otherwise to a
  safe fallback. This keeps the primary path on-device while being honest about
  the boundary, consistent with the design's rule against hidden host inference.
- **Feature producer.** The MCU computes typed features or embeddings, and a host
  makes final decisions. This is not on-device classification and must be labeled
  as such.

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation | Earliest test |
| --- | --- | --- | --- | --- |
| Task and ground truth stay undefined | High | Blocks everything | M0 template (§10) | M0 |
| Licensing breach (Jev MCA, share-alike data, Gemma tokenizer, NC models) | Medium | High | Licensing gate; open teachers; own tokenizer | M0 |
| Teacher weak on the domain | Medium | High | Bake-off against human labels (F2) | M3 |
| Label artifacts (bundles, truncation mismatch, option order) | Medium | Medium | Contract tests (F3) | M3 |
| NPU mapping surprises (fallbacks, column splits) | Medium | Medium | Compile-only experiments before training | M1a |
| INT8 hurts rare classes or calibration | Medium | Medium | Per-class checks; QAT fallback; calibrate the deployed path | M4 |
| Hard to debug numerics without an emulator | Medium | Medium | Golden vectors; NPU validation intermediates; host saturation check | M1b |
| Boot, signing, RIF complexity | Medium | Medium | Cold-boot a dummy model early | M1b |
| ST tool or runtime version drift | High | Low–Medium | Pin versions; vendor tools in `.devcontainer/tools` | M1a |
| Overdrive power or thermal limits | Low | Medium | Budget at nominal clocks | M4 |
| Confident wrong answers on out-of-domain inputs | High | High | OOD sets, rejection, deferral, interlocks | M4 |
| Fresh teacher releases change | High | Low | Pin revisions and hashes | M3 |
| INT8 teacher shifts labels or calibration | Low (smoke check found no changes) | Medium | Parity on the reviewed set against the streamed BF16 reference; calibration re-check | M3 |
| Teacher host limits (12 GB GPU, WSL2 memory spill) | Medium | Low | 2,048-token batch budget; flash-linear-attention or a larger GPU for inputs above about 12 k tokens | M3 |
| Teacher trained on Jev outputs | Medium | High | Exclude the JEV family; written data statement for Decision 3.0 (F15) | M0 |
| Student drifts into unseen states in closed loop | High | High | DAgger rounds in simulation, then arena (F14) | M3 |
| Sensor pose or frame differences break transfer between robots | Medium | Medium | Embodiment profiles validated per frame; fixed sensor mounting (F12) | M6 |
| Interface faults (stale, lost, or malformed packets) | Medium | High | Versioned contract, liveness checks, host fail-safes (F12) | M5 |

## 9. Recommended Next Steps

For the robot decision module, §12.5 updates steps 1 and 4.

1. **M0 decisions** using the template in §10.
2. **M1a, compile-only (no board):** install the Linux ST Edge AI Core under
   `.devcontainer/tools/stedgeai`, then compile with
   `profile-internal-memories-only--default`:
   - Layout `[1, C, 1, T]` with 1x3 kernels versus `[1, C, T, 1]` with 3x1.
   - Global pooling inside the graph versus returning feature maps.
   - Gather inside the graph versus M55 embeddings.
   - One transformer block, to quantify software fallback.
   - Record epochs, software operators, pool usage, and estimated cycles.
3. **M1b, board:** STM32N6570-DK, NPU validation project with
   `USE_EXTERNAL_MEMORY_DEVICES=0`, golden vectors, latency at nominal and
   overdrive clocks, and a cold boot with a signed FSBL and application.
4. **Teacher work:** the Vela 2.0 9B release code is pinned and reviewed, and
   the INT8 loader is implemented and smoke-tested (F2). Next: run it on the
   reviewed set, then the bake-off and the question-isolation and truncation
   tests. Other teachers' remote code still needs review and your approval.
5. **Baselines (M55 only):** rules, hashed n-gram linear model, pruned static
   embeddings, evaluated on the locked test set.
6. **Student:** CNN trunk with heads on the M55; supervised versus distilled
   comparison; PTQ; board parity; calibration; rejection curves.

## 10. M0 Decision Template

Updated in Update 2 for the robot pilot; recorded as provisional defaults on
2026-10-14. The user confirmed the recorded defaults on 2026-10-15, with
current implementation restricted to teacher tooling. The original dated
proposal table is retained below; interface contract v0 is not yet frozen.

| Decision | Provisional default (2026-10-14) |
| --- | --- |
| First frame and question bundle in Jev form | Ground rover; per tick: `path_blocked` (noul), `clear_sector` (choice: left, centre, right, none), `speed_tier` (score 0-3), `mode` (choice: explore, approach, avoid, dock, halt) |
| Inputs and sensors | Ego-state from the host (FLU body axes, SI units); 8x8 ToF (`VL53L8CX` model) and an 8-tick history window on the module; camera in a later profile; text only for optional operator commands (English, ≤ 128 UTF-8 bytes) |
| Label source per question | `path_blocked`, `clear_sector`, and `speed_tier` ceiling deterministic from ToF range and speed; `mode` (and perceptual/policy refinements) from reviewed human labels plus Decision 3.0 distributions |
| Confidence semantics | TypeSafe Jev formulas on host and device (`(p_max − 1/n)/(1 − 1/n)` for choice, MAD-based for score, `\|2p − 1\|` for noul), alongside full probabilities |
| Simulator | Minimal Python/NumPy 2-D rover simulator with an 8x8 ToF model, noise, dropouts, latency, and a scripted expert first; PX4 software-in-the-loop with Gazebo later |
| Ground-truth owner and policy | Project lead reviews ambiguous episodes |
| Error costs | A missed obstacle is 20x worse than a false stop |
| Required metrics | `mode` macro-F1 ≥ 0.85 at ≥ 80% coverage; no collisions in the simulator and arena scenario suites |
| Decision rate, latency, and power | 20 Hz; decision within 20 ms of the state packet at nominal clocks (600 MHz CPU / 800 MHz NPU); module below 1 W |
| Host interface and fail-safe | UART at 1 Mbaud with interface contract v0 (CRC-protected binary packets); the rover brakes on rejection or after 150 ms without a decision |
| Memory policy | No external RAM during inference; external flash allowed for boot and initializers |
| Update policy | Heads as signed versioned blobs; trunk via firmware release or ST relocatable model |
| Board and European sourcing | STM32N6570-DK for M1b; vendor and wafer-fab level for the MCU (`STM32N657`) and ToF sensor (`VL53L8CX`), with country of origin recorded per part |
| Commercial use and licensing | Commercial product; Apache-2.0 teachers without Jev-derived labels |

## 11. Suggested Edits to DESIGN.md

Status: applied to DESIGN.md on 2026-10-13, together with the measured INT8
teacher results (DESIGN §4).

- DESIGN §1: add "Hosted Jev as teacher or label source: not permitted by
  TypeSafe's customer agreement" to the capability table.
- DESIGN §3: note nominal versus overdrive clocks; add the memory-pool map; add
  ST's feature-width and pooling rules for 1-D sequences.
- DESIGN §4: add Vela 0.8B and Decision 3.0; replace the teacher table with a
  bake-off plan; add question-isolation and teacher-view alignment requirements;
  note the official Vela 0.3B ONNX FP16 path, the BF16-stored 9B backbone, and
  the INT8 weight-only route that fits the 9B on a 12 GB GPU.
- DESIGN §5: re-derive the PDF student's parameter count from its actual code.
- DESIGN §6: move embedding gather, pooling, and heads to the M55; define the
  confidence formulas explicitly; add the host-compiled heads mechanism.
- DESIGN §8: add the AVX2 saturation caveat to numerical parity; prefer the DK
  for M1.
- DESIGN §9: add EmbBERT, pQRNN/PRADO, Model2Vec, Crivo, and hardware
  alternatives; state that ternary weights do not reduce NPU SRAM use.
- DESIGN §10: add the licensing gate, including Crivo's non-commercial license.
- DESIGN §11: replace with a description of the existing devcontainer.
- DESIGN §12: split M1 into compile-only M1a and board M1b; add modality and
  task decomposition to M0.

## 12. Review Update 2 (2026-10-14): Robot Decision Module

Status: applied to DESIGN.md on 2026-10-14.

Inputs: your clarifications and an external AI analysis ("STM32N6x7 Robot
Project Architecture Review", a Gemini conversation provided as a PDF). Every
claim used here was rechecked against primary sources: model and dataset cards,
the d3 release code (read at revision `fc2d74b`, not executed), and ST,
Infineon, and PX4 documentation. No new measurements were made; estimates are
arithmetic from published configurations.

### 12.1 Clarified scope

- The product is a decision module: an independent "mini-brain" on a
  European-sourced STM32N6x7 that attaches to different robot frames (first a
  land rover, later a mini-drone) and makes the robot's tactical decisions. The
  rest of the robot is a separate concern that the module must support.
- The wire format is open. JSON or text is not required on the device, so the
  design's typed decisions stay.
- Any suitable open teacher is acceptable. Most of the time the teacher host is
  the 12 GB RTX A3000 laptop GPU; a host with two NVLinked RTX 3090s (and an
  unused GTX 1080 Ti) is only occasionally available. The first teacher is
  therefore d3-flash in INT8 on the 12 GB GPU (clarified after the first draft
  of this update), with d3 in INT8 across the 3090s when that host is free.
- Out of scope: a custom flight controller or ESC on an STM32L4R5. The drone
  should run an established flight stack such as PX4 or ArduPilot.

### 12.2 Assessment of the external analysis

Sound and adopted:

- The module decides and the host acts: the host controller keeps inner loops,
  interlocks, and fail-safes, which differ per frame (a rover brakes; a drone
  holds position or lands and never cuts its motors).
- A versioned binary state and decision protocol with an embodiment ID and a
  validity bitmask.
- Information equivalence between teacher and student inputs; numeric and
  spatial student inputs, with text only for optional tags.
- Atomic question bundles per tick, per-embodiment heads on a shared trunk, and
  relocatable trunks per frame.
- DAgger-style closed-loop data collection.
- Decision 3.0 rather than Vela for visual robot decisions (Vela is text only),
  d3's architecture facts, and its two-GPU INT8 memory map.
- The warning about Jev-derived labels in the JEV family (confirmed in F15) and
  leaving the GTX 1080 Ti out of the teacher host.
- Infineon PSoC Edge E84 as a European MCU alternative.

Corrected:

| Claim in the external analysis | Finding | Evidence |
| --- | --- | --- |
| Vela 9B (41.09) compared directly with d3-mini (54.90) | Different Index editions (0.2.1 versus the 0.3 public suite); not comparable | [Vela 9B evaluation][vela-9b-eval]; [d3-mini card][d3-mini] |
| d3 board score 65.45, vision 69.9, new-domain 56.6, and "64.7 / 71.6" | 65.45 is the public-suite score; on the Index 0.3.2 boards d3 has 66.3 (text), 71.3 (vision), and 60.5 (new-domain) | [d3 card][d3] |
| d3-mini "65.87 raw"; d3-flash "57.8-59.0" | Not found on the cards | d3-mini and d3-flash cards |
| d3-mini fits a 12 GB GPU in BF16 | As released, its one-request peak is 14.8 GiB; it fits only with host-side embeddings (about 7.3 GiB of weights, estimate) | [d3-mini card][d3-mini]; config arithmetic |
| d3-flash fits a 3090 comfortably in BF16 | Its peak is 23.8 GiB of 24 GB; it fits with host-side embeddings (about 13.7 GiB of weights) or INT8 (7.4 GiB), estimates | [d3-flash card][d3-flash]; config arithmetic |
| INT8 Vela 9B needs about 9.5 GB | Measured: 6.6 GiB of parameters, 7.7 GiB in use | F2 |
| Keep the CandidateHead in FP32 | Already the case in `teacher/vela_int8.py` | F2 |
| Rent hardware to run JEV-35B in NVFP4 | Contradicts its own note that NVFP4 needs Blackwell (SM100); moot given F15 | [JEV-35B card][jev-35b] |
| NVLink moves split activations in under 50 µs and is needed | A split moves about 25 MB for 8 x 300 tokens: about 1 ms over PCIe 4.0 and less over NVLink, against seconds of compute per pass; NVLink is optional | Estimate |
| A pre-hook on layer 32 places the second stage | d3's `PromptEncoder` passes rotary embeddings and masks built on GPU 0 to every layer; all second-stage layers need the move, and the output must return to the readout's GPU | d3 `d3_runtime.py` |
| Make `backbone.to` a no-op | The runtime calls it only from `D3.to()`; a silent no-op hides placement errors | d3 `d3_runtime.py` |
| Normalize weight names heuristically; inject with `patch.object` | Keys are exactly `language_model.*` and `visual.*`: map them explicitly and fail on leftovers. `backbone_class()` imports `Qwen3_5Model` inside the function, so patch what `D3.__init__` resolves, only during construction, and test it | d3 weight index and runtime |
| Four robot states validate the INT8 teacher | Too few and without a reference; compare with the streamed BF16 reference and recorded outputs on the reviewed set, as for Vela | F2 |
| NPU-friendly operators guarantee 100% NPU offload; about 3 TOPS/W | Only the compiler report establishes mapping (F5); ST's page gives 600 GOPS and no TOPS/W figure | [STM32N657][st-n657] |
| A 128-byte state packet carrying history, a ToF grid, and a mission tag | Its own fields add up to about 600 bytes; keep the history and the ToF sensor on the module | Arithmetic (F12) |
| Teacher labels from high-resolution frames while the student sees 64 x 64 | Privileged information, contrary to its own equivalence rule; label at the student's crop or measure the benefit | F13 |
| Teacher labels for geometric questions | Computable; use deterministic code or simulator ground truth | F13 |
| Hugging Face as a Paris-based European source | Hugging Face is a French-American company based in New York; hosting says nothing about a model's origin | F17 |
| European origin asserted for parts | Needs country-of-origin data per part | F17 |
| PSoC Edge E84 with 5 MB SRAM | Up to 6 MB | [Infineon][psoc-edge-e84] |

### 12.3 New findings

#### F12 (High): Define the module contract before training

The host interface is now part of the model's input definition. Specify module
and host duties, the state and decision packets (versions, embodiment profile,
sequence, timestamps, validity bits, sensor ages, SI units in one body frame,
status codes), liveness, and frame-specific fail-safes in M0. Keep the history
buffer and the perception sensors on the module, so the per-tick packet stays
small. PX4's offboard mode already expects a proof-of-life stream of at least
2 Hz and otherwise runs its configured fail-safe ([PX4][px4-offboard]); a rover
host needs an equivalent watchdog. Applied: DESIGN §2, §6, §8, §12.

#### F13 (High): Choose the label source per question

Geometric questions (an obstacle inside the braking distance, the clearest
sector) are computable from ToF range and speed: label them deterministically
or from simulator ground truth, and often compute them at run time instead of
learning them. Use the teacher for perceptual and semantic questions and
reviewed human labels for policy. Information equivalence covers images too:
d3's processor upscales images below 65,536 pixels, and each 32 x 32-pixel
patch is one token, so teacher accuracy at the student's resolution must be
measured. Applied: DESIGN §4, §6.

#### F14 (High): Collect data in closed loop

A student trained only on expert trajectories drifts into states it never saw
once it steers ([DAgger][dagger]). Plan rounds: seed data, run the student in
simulation, label the visited states, retrain, and then repeat in a safe arena.
PX4 software-in-the-loop with [Gazebo][px4-gazebo] covers rovers and
multicopters. Applied: DESIGN §7, §8, §12.

#### F15 (High): Exclude Jev-derived teachers; get Decision 3.0's data statement

- [JEV-27B-VL][jev-27b-vl] and JEV-27B list [jev-distill-corpus-v3][jev-corpus]
  as training data. Its largest stream, `yuri_v3` (498,010 of 740,957 rows), was
  labeled by "Jev 1.13 via the OpenRouter Decisions API". The JEV-27B card calls
  the model a "student of TypeSafe Jev 1.13", and the JEV-27B-VL card reports a
  KL divergence of about 0.017 from Jev's distributions.
- [JEV-35B][jev-35b] names no training data. It comes from the same publisher
  and family, so its provenance is unresolved.
- Apache-2.0 weights do not settle whether a model trained on Jev outputs
  carries the restriction in TypeSafe's terms (F1). Exclude the family as
  teacher and label source.
- The [Decision paper][decision-paper] states that its documented Sol, Nox, and
  Lux mixtures do not use official Jev predictions as labels, but the Decision
  3.0 cards do not disclose training data. Ask the vLLM Semantic Router team for
  the same statement on Decision 3.0 before commercial use.

Applied: DESIGN §4, §10.

#### F16 (Medium): Teacher selection and the two-3090 plan

Decision 3.0 on the Index 0.3.2 boards (dated 2026-10-12), from the model
cards:

| Model | Parameters | Text board | Vision board | Perception Test | One-request GPU peak |
| --- | --- | --- | --- | --- | --- |
| [d3][d3] | 26.09 B | 66.3 (first of 149) | 71.3 (first of 33) | 77.4 | 61.8 GiB |
| [d3-flash][d3-flash] | 8.39 B | 55.8 | 66.9 | 73.3 | 23.8 GiB |
| [d3-mini][d3-mini] | 4.54 B | 52.6 | 63.2 | 70.3 | 14.8 GiB |
| [d3-nano][d3-nano] | 2.21 B | 38.9 | 54.7 | 63.5 | 9.1 GiB |
| [d3-lite][d3-lite] | 0.85 B | 32.3 | 42.1 | 59.3 | 5.7 GiB |
| [d3-edge][d3-edge] | 0.59 B | 20.2 | 36.6 | 46.6 | 5.2 GiB |

On ERQA (embodied reasoning), autotrust measured d3 at 58.8 in one pass
([JEV-27B-VL card][jev-27b-vl]). On the 12 GB GPU, d3-flash in INT8 (about
7.4 GiB) is the strongest member that fits. Its text backbone has the same
dimensions as Vela 2.0 9B, whose INT8 conversion changed no decisions in the
smoke check (F2). d3-mini fits unquantized in BF16 with host-side embeddings
(about 7.3 GiB), an exact-precision comparison. On the 3090s, d3 needs INT8 as
well: all-BF16 weights (46.2 GiB even with host-side embeddings) leave no room
for activations on 2 x 24 GB, whereas the INT8 split needs about 12 GiB per
card (estimates, DESIGN §4). The sharding corrections are in §12.2. Two more
points from the release code: d3 defines `confidence` as one minus the
normalized entropy, a third formula next to Jev's and Vela's (DESIGN §6), and
its runtime downloads `http(s)` media URLs, so label from local files.
Leaderboards do not measure robot-state questions; the bake-off on reviewed
robot states decides. Estimated labeling cost: about 1.3 s per five-question
state for d3-flash in INT8 on the 12 GB GPU, and 0.4-0.5 s per question for d3
on the 3090s.

#### F17 (Medium): Define "European sourced"

A headquarters location does not establish origin. Define the levels that
matter (vendor, chip design, wafer fab, assembly and test, board components,
software and IP) and collect country-of-origin data per part. Context:
STMicroelectronics, Infineon, and NXP are European vendors; Alif Semiconductor
is a US company; the Cortex-M55 and Ethos NPUs are Arm IP; the Decision 3.0
teachers build on Qwen backbones; and [Mistral Small 3.1][mistral-small]
(Apache-2.0, from France) is an option if a European teacher is ever required.
Drone flights also fall under aviation rules (in the EU, the
[EASA framework][easa-drones]). Applied: DESIGN §9, §10.

### 12.4 Corrections to the first review

- F1 and §2 presented autotrust/JEV-35B as a clean open alternative; see F15.
- §7.2 listed Alif without noting that it is a US company.
- F2 left d3-lite, d3-nano, and d3-mini unchecked; filled in.
- §10's M0 example was a text task; replaced with a rover pilot.

### 12.5 Next steps

1. M0 with the updated template (§10): rover first, interface contract v0,
   sensors, label source per question, simulator, and the European-sourcing
   definition.
2. Teacher: port the INT8 loader to d3-flash on the 12 GB GPU (DESIGN §4) with
   `verify="full"` and a streamed BF16 reference, and compare it with d3-mini in
   BF16. Add d3 on the two 3090s when that host is available, then run the
   bake-off on reviewed robot states.
3. Ask the vLLM Semantic Router team for a training-data statement on Decision
   3.0 (F15).
4. Simulation: a rover scenario in PX4 software-in-the-loop with Gazebo, or an
   equivalent, that logs state packets in the contract format.
5. M1a as before, adding a depth-grid CNN and a small camera CNN to the
   compile-only experiments.

## 13. Tooling Restart Check (2026-10-15)

The user confirmed the recorded M0 defaults, then restricted current work to
teacher tooling. The interface and product implementation remain unfrozen.
After source review, restricted in-process execution of the two approved d3
revisions was approved: no optional HTTP server, video decoding or remote
image URLs. The reviewed inference path contains no subprocess, pickle or
`torch.load` calls. The encoded-video temporary-file path is not used.

The d3-flash INT8 loader passed 10 CPU-only tests (13 repository tests), Ruff
lint and formatting, and a fully hashed offline load plus a two-question
`system_one` call on the RTX A3000. It used 7.416 GiB allocated after load
and peaked at 8.438 GiB reserved. DESIGN §4 records the timing and limits.
Image processing initially needed the missing torchvision dependency; image
parity and INT8-versus-BF16 validation were pending at that smoke checkpoint.
The subsequent results are recorded below. No student, board, compiler,
task-accuracy or safety evidence follows from this teacher smoke test.

### Subsequent Teacher and Simulator Checks (2026-10-15)

The user approved torchvision 0.25.0 with PyTorch 2.10.0. Both hash locks
were regenerated without upgrading existing dependencies. The matching
official CUDA wheel passed TLS/hash verification, `pip check`, an operator
test, and both teachers' actual local-image inference.

The 25-request d3 suite covers text, synthetic rover states and local 64x64
images, with 31 questions and 85 probability values. Flash INT8 versus
streamed BF16: maximum absolute delta 0.019836, mean 0.002114, zero decision
flips. The largest difference was an ambiguous rover score distribution;
its winning level was unchanged. Mini BF16 matched its streamed projection
and GPU-lookup reference exactly. DESIGN §4 and the two JSON reports record
resources and throughput. These smoke fixtures do not establish label quality,
calibration, commercial data clearance or deployability.

The user clarified that a working trainer simulation is needed without
hardware, and approved configurable toy physics, sensor faults/latency,
goal-progress reward and an interim JSONL schema. The implemented CPU-only
environment passes 21 focused tests. A privileged SciPy map-planning expert
completed 32 seeded smoke episodes without collision or timeout. The separate
sensor-only reactive baseline collided in obstacle and slalom scenes. Ground
truth is kept separate from model inputs; neither controller's outputs are
reviewed policy labels. DESIGN §7 records assumptions and limitations. Binary
contract export remains blocked on the unfrozen interface, and no board gate
is satisfied by this work.

Final verification: `python -m pytest -q` passed all 39 CPU tests; `ruff
check .`, changed-file `ruff format --check`, `pip check`, Markdown reference
and local-target checks, and `git diff --check` passed. The two real GPU
validation commands are recorded in README.md and their JSON reports. A fresh
container rebuild, ST compilation and physical-board run were not performed.

## 14. Decision 3.0 Training-Data Statement Request (Draft, 2026-10-15)

Draft for the project lead to send; no contact has been made.

Subject: Decision 3.0 training-data provenance for commercial distillation

Hello vLLM Semantic Router team,

We are evaluating Decision 3.0 as a teacher for a small commercial embedded
robot decision module. Our current candidates are `vllm-sr/d3-flash` revision
`b92769d85908bb3ee737ef9c765e1c08b887aca6` and `vllm-sr/d3-mini` revision
`6d8971f464d6f9d4c5af7d9a8d75f3aa03be4f59`.

The [Decision paper][decision-paper] says the documented Sol, Nox and Lux
mixtures do not use official Jev predictions as labels. Could you confirm
whether the same statement applies to these specific Decision 3.0 releases,
including any upstream models, synthetic labels or intermediate teachers
used to produce them?

In particular, we would appreciate a written statement about any training or
distillation inputs derived directly or indirectly from TypeSafe Jev hosted
outputs, including the autotrust JEV family and Jev-distilled datasets, and
any additional restrictions affecting commercial use of generated teacher
distributions to train and redistribute a separate student. An applicable
data/model provenance document or release-specific statement would help us
complete our review. We understand Apache-2.0 weight licensing alone does
not answer third-party training-data restrictions.

Thank you.

## 15. Provisional Interface Tooling (2026-10-15)

The user requested Conventional Commit subjects for all new commits. The rule
is persisted in AGENTS.md; earlier commits were not rewritten. The user then
approved a provisional host-side contract and simulator export without
freezing physical safety, labeling policy or hardware integration. Student
training and firmware implementation remain outside current scope.

[Python definitions][wire-python] are the single source for little-endian
state/decision codecs and the generated [C offset header][wire-header]. State
frames are 92 bytes; full decisions are 128 bytes; empty rejection/fault is
36 bytes. Versions, sequence, timestamp, validity, ages and CRC are explicit.
Host state excludes module-side ToF/history. Status gates recommendation
usability, while raw distributions and selections remain separate.

The codec validates values, layouts, identities, order and Jev statistics.
It does not enforce physical bounds, staleness, calibration, smoothing,
liveness or actuator fail-safes. Wire options are not reviewed labels. The
[five golden frames][wire-golden] are synthetic fixtures; dummy model ID 1
in the `OK` fixture is not an actual student or deployment claim.

Verification: 62 focused tests passed, including single-byte corruptions,
valid-CRC malformed frames, arbitrary stream boundaries/recovery, golden
round trips and generated-header equality. Host GCC and `arm-none-eabi-gcc`
compile the header; independent host C encoding matches the state golden
bytes. Ruff lint/format and editor diagnostics passed. No dependencies,
board, UART hardware or ST compiler measurement was added. DESIGN.md §2
records the draft and application duties.

### Simulator Contract Export

The approved export is now available via `python -m sim.rover --wire`.
Versioned JSONL logs contain exact state-frame bytes as hex and an explicit
provisional contract manifest, while module-side ToF/history and diagnostic
truth remain separate. FLU planar ego-state/goal and timestamps map to the
same bytes tested by the codecs. Health is invalid/unknown, not fabricated
healthy state. There is no trained model, so no decisions or reviewed labels
are invented. Default logging and exclusive creation remain supported.

Nine new export tests cover input equivalence, isolation from truth/actions/
ToF/history, wraparound, reproducibility, JSONL round trips, invalid samples
and the CLI. Four real wire-enabled episodes at seed 20261015 completed with
the privileged map expert: clear/obstacle/corridor/slalom in 133/140/133/156
ticks, no collision or timeout. All 566 state frames (52,072 bytes) passed
CRC, byte equivalence and stream decoding. DESIGN.md §7 records JSONL hashes.

Final verification: `python -m pytest -q` passed 110 tests; `ruff check .`,
changed-file `ruff format --check`, editor diagnostics and `git diff --check`
passed. No packages were installed, no weights downloaded, no teacher/GPU
inference or student training run, and no ST compilation, physical UART,
firmware integration or board validation performed. Tasks 5 and 7 meet their
approved tooling exits; Task 6 still needs approved computable label
definitions and reviewed mode policy, with simulation-only rules proposed
as the next default rather than physical safety specifications.

[wire-python]: interface/protocol.py
[wire-header]: firmware/include/micro_classifier_protocol.h
[wire-golden]: interface/golden_vectors.json

## 16. M1a Host Preparation (2026-10-15)

The user requested continued autonomous work with periodic local commits.
Task 6 still requires approved label policy, and student training/firmware
remain outside scope. Task 14 explicitly permits script preparation while
ST tools are missing. [CPU tooling][m1a-script] uses existing dependencies,
without package changes, downloads, training or GPU work.

Nine untrained probes cover both 1-D Conv layouts, fixed pooling, Gather,
a numeric MLP, ToF/camera convolutions and a standard transformer block.
Float ONNX and signed per-channel QDQ use fixed shapes and distinct synthetic
calibration/evaluation seeds. Float outputs agree with PyTorch within
4.77e-7 in the [real report][m1a-report]. All 27 artifacts were independently
hash-checked. DESIGN.md §12 records numerical results and the report digest.

Transformer limitations remain explicit. A wrapper keeps the legacy exporter's
optional causal boolean from becoming a tensor; standard shape inference
avoids an ORT symbolic-Reshape assertion. Both float/QDQ execute, but INT8
error exceeds the diagnostic-only 0.15 bound: 0.264466 then 0.245311 in the
unit fixture using 3 then 16 calibration samples, and 0.206992 in the full
16-calibration/8-evaluation run. Stop this tuning path for now. Its numerical
test is explicitly expected to fail; no bound was raised or quality claimed.

Verification: 133 passed plus one expected failure; Ruff lint/format and
editor diagnostics passed. Legacy-exporter deprecation/tracing warnings
remain for a future approved framework upgrade. This is not reviewed
calibration, task accuracy, target parity, SRAM fit, NPU mapping, board latency
or safety evidence. Task 14 and M1a still await real ST compilation. ST primary
documentation requires QDQ through `stedgeai generate`, not directly `atonn`.

[m1a-script]: export/m1a.py
[m1a-report]: export/reports/m1a-cpu-20261015.json

## 17. ST Compiler Orchestration Preparation (2026-10-15)

[Compile tooling][st-compile-script] consumes the host manifest without model
framework imports. Default planning verifies all three ONNX hashes per case,
without processes or output creation. Opt-in `--execute` rechecks inputs and
requires an explicit expected release and available executable. Unknown banners
and prereleases fail closed. Executable SHA-256 and full version/module logs
are retained; hashing the complete vendor installation remains open.

The [ST CLI][st-cli-401] and [compiler primer][st-compiler] route QDQ through
`stedgeai generate` for STM32N6 with the built-in internal-only memory profile.
No direct `atonn`, validation, firmware build, loader or board command is used.
Default pools do not establish the final firmware/NPU partition. Custom
profile/CSV instrumentation and metric parsing await the real release/reports.

Exclusive fresh outputs preserve raw vendor files, logs and a hashed inventory.
A zero exit without the documented generation report and C-info file fails.
Case failures allow independent cases to continue; interruption stops the
matrix. Timeout/interruption kills the POSIX process group and descendants.
Even full generation is only `generated_reports_pending_review`, with M1a,
board and metric acceptance false. Transformer numerical flags remain visible.

Verification: a real nine-case CLI dry plan started no ST process and created
no compiler output. Eighteen mocked runner tests pass; full-suite results are
151 passes plus the known transformer expected failure. Lint/format, editor
diagnostics and doc references pass. Mocks prove no actual vendor compatibility,
NPU mapping, SRAM fit or cycle estimates. No tools, dependencies or licences
were installed/accepted, and no training or board work occurred.

All remaining task-list work is blocked on label-policy approval, data/models,
tooling-only scope, ST software or a board. Task 6's proposed next decision
remains simulation-only computable labels derived from Config, with `mode`
left for human review; that proposal has **not** been approved.

[st-compile-script]: export/st_compile.py
[st-cli-401]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-cli.html

## 18. Simulation Label Policy Draft (2026-10-15)

The user explicitly selected **Approve a policy draft and tests**, not the
alternative allowing simulator label generation, and confirmed that ST tools
remain unavailable. This authorizes a narrow Task 6 preparation increment;
it does not approve reviewed labels, teacher labeling, training, physical
thresholds, deployment or actual ST compilation. §17's historical blocker
statement is superseded only for implementing this draft and its tests.

[Catalogue data][sim-catalogue-draft] preserves the four wire identities and
option order. [Draft code][sim-label-draft] proposes an envelope of radius
plus speed times (ToF age plus one tick), plus squared speed over twice the
Config acceleration. Left/centre/right columns are 0-2/3-4/5-7, with minima
over valid returns and coverage required in every column. Centre clearance
defines the blocked proxy and the four Config-relative speed ceilings;
clearest qualifying sector wins with centre/left/right tie priority.
DESIGN.md §7 records exact formulas, boundaries and limitations for review.

Unavailable/stale samples, missing coverage and beyond-range envelopes cause
explicit abstention, never fabricated clear observations or `none` from
missing data. `mode` always requires human review. Non-finite/malformed or
timestamp-inconsistent observations are rejected. Records are marked
`unreviewed_draft`, `tooling_and_unit_tests_only`, training-disabled and not
physical safety evidence. Canonical policy/config/input hashes and source
hashes track identity. No world truth, future frames, expert actions or
history are read; the simulator CLI, episode logs and wire codecs are unchanged.

Verification: 37 draft tests and all 67 simulator tests pass; full suite:
188 passed plus the existing transformer numerical expected failure. Ruff,
changed-file formatting, editor diagnostics and documentation references pass.
The tests exercise arithmetic, boundaries, sensor masks/ages, orientation,
provenance and no input mutation/leakage. Only unit fixtures were evaluated;
no labeled episode dataset, smoke labeling run, teacher call, training job,
dependency change, ST execution or board action occurred.

Task 6 remains blocked on review of the proposed policy, including its sector
partition, one-tick reaction assumption, freshness/tie rules and tier meanings.
Radial noisy rays do not certify collision-free swept motion, especially when
turning. Proposed next approval is a simulation-only reviewed-policy smoke
suite with `mode` left for human review; it has not been granted. Task 8 still
requires a reviewed catalogue/policy; training and firmware remain out of scope.

[sim-catalogue-draft]: sim/catalogue.json
[sim-label-draft]: sim/labels.py

## 19. Bounded Simulation Label Smoke (2026-10-16)

The user approved the existing draft unchanged for a small seeded simulation
smoke suite, followed by teacher-pipeline tooling tested with **fake teachers
only**. This supersedes §18's generation prohibition only for that bounded
smoke. No live teacher labeling, training, reviewed production dataset,
new dependency, ST execution or hardware action was approved.

The labeler now records the narrower approval in catalogue scope metadata
and offers a separate four-scene smoke CLI. Rules and wire identities did
not change. Exclusive labeled logs remain ignored; `mode` remains absent,
training disabled, and the draft remains unreviewed for production quality.

The [seed-20261016 report][sim-label-smoke-report] records clear/obstacle/
corridor/slalom at 133/141/133/156 ticks, all successful with no collision or
timeout. There are 567 observations, including eight warmup abstentions per
computable question. All 559 usable blocked values are false and all speed
tiers are 3. Sector labels include left/centre/right but no `none`; mode is
human-review/absent for all 567. This explicitly lacks positive-blocked and
lower-speed coverage; it is plumbing evidence, not quality or safety evidence.

All four log hashes, report equality and observation counts were independently
checked. DESIGN.md §7 records the report digest and exact limits. Four new
tests cover exclusive outputs, replay and scope invariants. Full verification:
192 passed plus the known transformer expected failure, 71 simulator tests,
Ruff lint/format and clean editor diagnostics. Task 6 still needs reviewed
training labels and human mode examples; Task 8 host preparation can proceed
with fake teachers but cannot generate genuine teacher labels yet.

[sim-label-smoke-report]: sim/reports/label-smoke-20261016.json

## 20. Fake-Teacher Pipeline Host Tooling (2026-10-16)

The §19 approval now has a [host implementation][teacher-label-pipeline] and
30 [CPU-only tests][teacher-pipeline-tests]. This completes Task 8's approved
tooling portion only. No real adapter, teacher invocation, training dataset,
new dependency, firmware, ST execution or hardware work was added.

Requests deterministically combine the exact simulated host state, current
ToF and complete masked history. Supplied wire frames must match reconstructed
observations; plain logs explicitly synthesize frames. Privileged truth,
expert actions and proxy labels never enter the rendered state. Source-byte,
renderer, catalogue, config and frame hashes retain provenance. The only
question is the ordered `mode` supplement; outputs remain synthetic and require
human review, not a replacement for approved human mode labels.

An exclusive, model-free CLI prepares bounded observation prefixes without
inference. The injected fake-only API validates complete named choice results,
option identities and finite normalized probabilities. SQLite commits each
successful record separately, preserving original probabilities/raw responses
and criteria order. Full request, option order, source and teacher revision,
artifact hash/settings determine cache identity. Reopening revalidates checksums
and answer consistency; interrupted runs reuse committed records. Test identity
metadata is caller-supplied, not verified real-model provenance or a sandbox.
Caches/plans remain ignored; unrelated database schemas are refused.

Two eight-observation prefixes of existing wire-v0 and label-smoke clear logs
were planned without calling a teacher. Maximum state strings were 9,689 and
9,842 characters; DESIGN.md §7 records artifact hashes. Token counts and fit
within the teacher budget remain unverified. The CLI's limit bounds rendered
requests, not source-file memory, and does not audit unselected observations.

Full verification: 222 passed plus the known transformer numerical expected
failure, Ruff lint/changed-file format and clean editor diagnostics. Live
labeling still requires explicit approval, prompt/token-budget checks and
adapter provenance; policy/coverage/human-mode review and locked splits still
block training and evaluation. No quality or physical safety claim follows
from the fake-teacher tests.

[teacher-label-pipeline]: teacher/label_pipeline.py
[teacher-pipeline-tests]: tests/test_label_pipeline.py

## 21. Pipeline Provenance Isolation (2026-10-16)

A focused check found that newly emitted fake-teacher records shared nested
teacher identity/settings with the running batch. Mutating a returned record
therefore changed later provenance/cache keys without changing the teacher.
Two regression cases reproduced this: a fresh start changed later settings;
a cached start lost an expected later cache hit after editing a fresh result.

Each new record now receives an independent identity copy. The same regressions
pass and verify original caller identity, stored provenance and expected cache
hits. All 32 pipeline tests and 224 repository tests pass plus the existing
transformer numerical expected failure; Ruff lint/format and editor diagnostics
are clean. Source-bound keys invalidate when this module changes, as designed.
No model, dataset, policy, dependency, training or hardware scope was expanded.

Only blocked tasks remain under the current approvals. Proposed next scope is
synthetic-fixture CPU evaluation metrics and split-validation tooling, pending
user approval. This would not approve real labels, training, dataset generation,
new metric thresholds or a claim of locked task splits.

## 22. Synthetic Evaluation Preparation (2026-10-16)

The user explicitly selected `Approve synthetic-only evaluation tooling`:
CPU metrics and split-validation fixtures, with live labeling, task datasets
and training still disabled. This supersedes §21's pending approval only for
that tooling. Baseline fitting, actual split locking, deployment thresholds,
dependencies and hardware scope remain unchanged.

The [implementation][teacher-evaluation] computes macro-F1 over all declared
options, per-class recall, natural-log NLL, summed multiclass Brier, equal-width
top-label ECE and inclusive tie-preserving risk/coverage curves. Missing-class
denominators and zero-coverage accuracy/risk are explicit nulls; zero target
probability is infinite NLL, represented as null with a flag rather than
silently clipped. Decimal-edge regression tests reproduced two ECE binning
errors before explicit edge search repaired them. DESIGN.md §7 records all
conventions; none defines a new application rejection rule.

Five-purpose synthetic manifests keep train, development, quantization
calibration, confidence calibration and test distinct. Duplicate sample IDs,
cross-purpose declared input/source/episode/template overlap, wrong scope and
unexpected manifest identity are rejected. Same-purpose groups can repeat.
Declared groups/hashes are not attested against files; no production grouping
contract, representative dataset or actual test lock is claimed.

The exclusive CLI runs only a built-in fixture. Its [report][synthetic-evaluation-report]
records four toy probability rows and five disjoint one-row placeholder
partitions: accuracy 0.75, macro-F1 7/9, Brier 0.395, ECE 0.05. This is
arithmetic/plumbing evidence, not rover accuracy, calibration or coverage.
The report source/environment/input/manifest hashes and exact artifact digest
are recorded in DESIGN.md §7.

Verification: 36 [focused CPU tests][evaluation-tests], 260 repository passes
plus the known transformer numerical expected failure, Ruff lint/changed-file
format and clean editor diagnostics. No teacher call, task dataset generation,
baseline fit, training, download, dependency or hardware action occurred.
Task 9 remains blocked on reviewed task data and locked splits; live labels,
student training, firmware and hardware remain outside this approval.

[teacher-evaluation]: teacher/evaluation.py
[synthetic-evaluation-report]: teacher/reports/evaluation-synthetic-20261016.json
[evaluation-tests]: tests/test_evaluation.py

## 23. Offline Prompt Budget: Measured Blocker (2026-10-16)

The user approved tokenizer/template-only offline preflight using already-
cached approved d3 revisions, explicitly excluding downloads, weights/model
loading, inference, labels and training. The [tool][prompt-budget] verifies
pinned manifest identity and consumed prompt/tokenizer assets, not model
weights or the complete inference package. Only the reviewed pure formatter
runs; model runtime/constructors and loaders are not invoked. Fast-tokenizer
loading is local-only with remote code disabled; answer-code parity is checked.

Complete mode-choice text sequences use the release formatter/chat template,
including question/options/generation prefix, with no truncation or padding.
Reports bind tool source, tokenizer/library assets, request hashes and original
episode/tick provenance. Fake CPU tests cover inclusive ceilings, scope flags,
hash tampering, local-only loading, forbidden model paths, answer-code mismatch,
metadata isolation and exclusive failure reports.

Both [flash][prompt-budget-flash] and [mini][prompt-budget-mini] tokenizers
were run offline with GPUs hidden on sixteen identical requests, eight each
from existing clear wire-v0 and label-smoke prefixes. All sixteen exceed the
2,048-token ceiling: 3,421 minimum, 6,788 wire maximum and 6,936 label-smoke
maximum, identically for both tokenizers. This replaces the earlier unmeasured
budget status with a concrete failure, not a new resource allowance. DESIGN.md
§7 records artifact hashes and scope. Fresh request/tool hashes and count-list
parity were independently verified; no labels were generated.

Verification: 15 [focused tests][prompt-budget-tests], 275 repository passes
plus the known transformer numerical expected failure; Ruff lint/changed-file
format and clean editor diagnostics. No weights/model runtime, inference,
training, download, dependency change or hardware action occurred.

The current renderer is not budget-qualified for live labeling. Proposed
default: keep the ceiling and full input/history unchanged while reviewing a
budget-compatible representation. No automatic rounding, feature removal,
history truncation or budget increase is authorized. Human/policy/data review,
live-label approval and the existing ST/board gates remain unresolved.

[prompt-budget]: teacher/prompt_budget.py
[prompt-budget-flash]: teacher/reports/prompt-budget-d3-flash-20261016.json
[prompt-budget-mini]: teacher/reports/prompt-budget-d3-mini-20261016.json
[prompt-budget-tests]: tests/test_prompt_budget.py

## 24. Lossless Row-Table Draft: Still Over Budget (2026-10-16)

The user approved a separate lossless compact-prompt draft, CPU round-trip
tests and offline comparisons on existing logs. The default renderer, complete
input/history and 2,048-token ceiling must remain unchanged. No inference,
labels, training, downloads, dependency or live-use approval was granted.

The [renderer][teacher-label-pipeline] adds per-request row interning and an
inverse decoder. It reuses only byte-identical JSON numeric/boolean rows,
retaining every literal value, mask, outer/time order and host-state field.
The compact text includes a row-reference legend. The factory verifies exact
canonical-state reconstruction against the original state hash; invalid index
types/ranges or expected-identity mismatches fail. Questions and option order
are unchanged, and separate draft metadata keeps live-use approval false.

The [preflight][prompt-budget] compares forms only with the explicit
`--compare-compact-draft` flag. Both pinned cached tokenizers were run offline
with GPUs hidden on 80 observations: the first 16 from wire-clear and each of
the four existing label-smoke logs. Every input round-trips exactly. Full
prompts take 3,421-10,855 tokens, all over budget; the draft takes 772-9,698,
with **65/80 still over budget**. Only ticks 0-2 fit in every prefix. Both
tokenizers agree, and warm-history requests remain unqualified. These are
bounded-prefix measurements, not whole-episode maxima or model-quality tests.

[Flash][row-draft-flash] and [mini][row-draft-mini] reports bind original and
draft request hashes, episode/tick provenance, exactness and source/asset
identities. All 80 reconstructions and source/request identities were checked
independently; DESIGN.md §7 records per-prefix counts and artifact hashes.

Verification: 42 pipeline and 18 preflight tests, 288 repository passes plus
the known transformer numerical expected failure; Ruff lint/format and editor
diagnostics clean. No weights/model runtime, inference, labels, new episode,
training, download, dependency or hardware action occurred. Row interning helps
startup size but does not solve the live-label budget gate. Keep this draft
opt-in/unreviewed; a further input-strategy and teacher-quality decision is
needed before any promotion. No rounding, feature/history removal or ceiling
increase is authorized by these results.

[row-draft-flash]: teacher/reports/row-draft-budget-d3-flash-20261016.json
[row-draft-mini]: teacher/reports/row-draft-budget-d3-mini-20261016.json

## 25. Typed Float32 Draft: Exact but Still Over Budget (2026-10-16)

The user approved a second offline-only draft using shortest float32
round-trip strings for exactly representable values, CPU tests and cached
tokenizer comparisons. Nonrepresentable rows must stay literal. Complete
original reconstruction, defaults and the 2,048-token ceiling stay unchanged;
no inference, labels, training, downloads, dependencies or live-use approval.

The [codec][teacher-label-pipeline] now offers a separate typed-row schema and
explicit `float32_rows=True` option. An all-float row uses decimal strings only
when casting to binary32 and promoting back reproduces every original canonical
float, including signed zero. Otherwise the entire row stays literal. The
legend requires binary32 parsing; this is not ordinary double-precision parsing
of the shortened decimal and does not reduce binary precision. Exact canonical
reconstruction and original hashes remain checked. The literal-row draft and
default full renderer are unchanged; malformed/nonfinite typed rows fail.

The [preflight][prompt-budget] exposes mutually exclusive comparison flags and
a distinct typed-comparison schema. Offline/GPU-hidden runs used both approved
cached tokenizers on the same 80 existing observations as §24. **All 80 states
round-trip exactly, but 63/80 typed prompts still exceed the unchanged ceiling**.
Both tokenizers agree: 811-6,016 tokens, versus literal rows' 772-9,698. Seventy
typed requests are smaller, but only two extra startup requests fit (tick 3 in
the two clear prefixes). Other scenes fit only ticks 0-2. No sampled
full-eight-tick-history prompt fits; smaller size is not a live-use gate pass.

[Flash][float32-draft-flash] and [mini][float32-draft-mini] reports bind original
and typed request/state identities, source/asset hashes and exactness. All 80
reconstructions and source bindings were independently checked; original state
hashes/counts match §24. DESIGN.md §7 records per-prefix metrics and report
hashes. These are bounded-prefix observations, not whole-episode maxima or
evidence of teacher interpretation/quality.

Verification: 49 pipeline and 21 preflight tests, 298 repository passes plus the
known transformer numerical expected failure; Ruff lint/format and editor
diagnostics clean. No weights/model runtime, inference, labels, new episode,
training, download, dependency or hardware action occurred. Keep both drafts
unreviewed/opt-in, complete inputs and budget unchanged. Live labeling remains
blocked pending an input-strategy and teacher-quality decision; these results
do not authorize rounding, history removal or a larger ceiling.

[float32-draft-flash]: teacher/reports/float32-draft-budget-d3-flash-20261016.json
[float32-draft-mini]: teacher/reports/float32-draft-budget-d3-mini-20261016.json

## 26. Diagnostic Label Coverage, Not Dataset Clearance (2026-10-16)

The user approved CPU-only coverage tooling/tests, at most sixteen diagnostic
simulation episodes plus synthetic fault fixtures, and an unreviewed report.
No rules/defaults, safety policy, input/history or token ceiling may change;
production datasets, live teachers, training, dependencies/downloads and
hardware remain excluded.

The [label CLI][sim-label-draft] adds opt-in `--coverage-study` while keeping
the original smoke mode. A zero-inclusive counter reports every option and
abstention reason. Eight 32-tick diagnostics retain default physics, sensor
faults, latency and full history, overriding only the study horizon (default
400). Seven stationary probes and a map-aware approach/brake script generate
observations; the labeler never receives truth or actions. Metadata marks the
script's privilege and non-expert diagnostic purpose. Twelve current-only
synthetic sector/speed/fault fixtures remain separate from episode counts.

The [seed-20261016 report][sim-label-coverage-report] records **264 observations**:
blocked false/true counts **208/40**, sector left/centre/right/none counts
**88/21/105/34**, and speed tiers 0/1/2/3 counts **36/36/98/78**. Every computable
question abstains on sixteen no-sample warmups; mode abstains on all 264.
There are zero collisions and eight intentional horizon timeouts, with zero
goal completions: this is not a navigation or controller-success evaluation.

All computable options now appear in selected diagnostic scenes, but this does
**not** establish representative coverage or correct ground truth. Thirty-one
blocked positives are from the noisy near-wall stationary case with a clear
starting footprint, and nine from the moving brake probe. Radial noisy proxies
remain unreviewed. Synthetic fixtures separately exercise all options and
no-sample/stale/incomplete-centre/incomplete-sector abstentions; they supply no
mode labels and are neither episode data nor a reviewed task dataset.

Independent verification checked all eight log hashes, 264 relabeled states,
consecutive ticks, option identities, twelve synthetic fixtures and disabled
approval flags. AST comparison confirms the original catalogue/envelope/label
and smoke functions are unchanged; Config defaults, catalogue, wire contract
and prompt tooling were not edited. DESIGN.md §7 records exact counts and
report SHA-256. Logs remain ignored; the shareable report binds their hashes.

Nine new focused checks pass; the repository has 307 passes plus the known
transformer numerical expected failure (80 simulator tests). Ruff lint/changed
format and editor diagnostics pass. No real teacher, training, production
dataset, dependency/download, firmware or board action occurred. Task 6 stays
blocked on policy/data review, and Task 8 live use on the unchanged prompt and
teacher-quality gates. Keep the defaults and training-disabled scope unchanged.

[sim-label-coverage-report]: sim/reports/label-coverage-20261016.json

## Sources

Hardware and tools:

- [STM32N657 product page][st-n657]
- [ST Neural-ART NPU concepts][st-concepts]
- [Neural-ART operators][st-operators] and [compiler][st-compiler]
- [Memory initializers][st-initializers] and [runtime-loadable models][st-reloc]
- [STM32N6 example projects][st-projects] and [quantization guide][st-quant]
- [STM32N6 image-classification getting started][st-gs-ic]

Jev and Jev-style models:

- TypeSafe [API][typesafe-api], [models][typesafe-models],
  [confidence][typesafe-confidence], [customer agreement][typesafe-mca]
- [Vela 2.0 overview][vela-blog]; Vela 0.3B [card][vela-03b],
  [usage][vela-03b-usage], [config][vela-03b-config], [code][vela-03b-code];
  [Vela 0.8B][vela-08b]; Vela 9B [usage][vela-9b-usage], [config][vela-9b-config],
  and [code][vela-9b-code]
- [Decision 3.0 collection][d3-collection], [d3][d3], [d3-flash][d3-flash],
  [d3-mini][d3-mini], [d3-nano][d3-nano], [d3-lite][d3-lite], [d3-edge][d3-edge],
  and the [Decision paper][decision-paper]
- [Crivo-150M][crivo-150m], [Crivo-32M][crivo-32m], [JEV-35B][jev-35b],
  [JEV-27B-VL][jev-27b-vl], [jev-distill-corpus-v3][jev-corpus],
  [Decision Index][decision-index], [Vela 9B evaluation][vela-9b-eval], and
  [Mistral Small 3.1][mistral-small]

Robot integration (Update 2):

- [PX4 offboard mode][px4-offboard], [PX4 Gazebo simulation][px4-gazebo],
  [DAgger][dagger], [Infineon PSoC Edge E84][psoc-edge-e84], and the
  [EASA drone framework][easa-drones]

Methods and measurements:

- [EmbBERT][embbert], [pQRNN/PRADO][pqrnn], [Model2Vec][model2vec],
  [Tang et al.][tang]
- STM32N6 studies: [eye tracking][eye-tracking], [CubeSat][cubesat],
  [speech enhancement][speech], [line segments][nplsd], [ARGO][argo],
  [Gideon][gideon], [edge processor review][edge-review]
- Alternatives: [Arm Ethos-U85][ethos-u85], [Alif E4][alif-e4],
  [Alif E8][alif-e8], [NXP i.MX RT700][nxp-rt700]

[st-n657]: https://www.st.com/en/microcontrollers-microprocessors/stm32n657a0.html
[st-concepts]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-programming-model.html
[st-operators]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-operators.html
[st-compiler]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-compiler.html
[st-initializers]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-memory-initializers.html
[st-reloc]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-reloc-mode.html
[st-projects]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-stm32n6-projects.html
[st-quant]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-quantization.html
[st-gs-ic]: https://github.com/STMicroelectronics/STM32N6-GettingStarted-ImageClassification
[typesafe-api]: https://docs.typesafe.ai/api
[typesafe-models]: https://docs.typesafe.ai/models
[typesafe-confidence]: https://docs.typesafe.ai/confidence
[typesafe-mca]: https://typesafe.ai/legal/mca
[vela-blog]: https://vllm-sr.ai/blog/vela-2-0-open-foundation-routing-models/
[vela-03b]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B
[vela-03b-usage]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/USAGE.md
[vela-03b-config]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/config.json
[vela-03b-code]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/modeling_vela2.py
[vela-08b]: https://huggingface.co/vllm-sr/Vela-2.0-0.8B
[vela-9b-usage]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/USAGE.md
[vela-9b-config]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/config.json
[vela-9b-code]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/modeling_vela2.py
[d3-collection]: https://huggingface.co/collections/vllm-sr/decision-30
[d3-edge]: https://huggingface.co/vllm-sr/d3-edge
[d3-flash]: https://huggingface.co/vllm-sr/d3-flash
[d3]: https://huggingface.co/vllm-sr/d3
[d3-mini]: https://huggingface.co/vllm-sr/d3-mini
[d3-nano]: https://huggingface.co/vllm-sr/d3-nano
[d3-lite]: https://huggingface.co/vllm-sr/d3-lite
[decision-paper]: https://vllm-sr.ai/decision-paper
[jev-27b-vl]: https://huggingface.co/autotrust/JEV-27B-VL
[jev-corpus]: https://huggingface.co/datasets/SargeDev/jev-distill-corpus-v3
[vela-9b-eval]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/EVALUATION.md
[mistral-small]: https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503
[px4-offboard]: https://docs.px4.io/main/en/flight_modes/offboard.html
[px4-gazebo]: https://docs.px4.io/main/en/sim_gazebo_gz/
[dagger]: https://arxiv.org/abs/1011.0686
[psoc-edge-e84]: https://www.infineon.com/products/microcontroller/32-bit-psoc-arm-cortex/32-bit-psoc-edge-arm/psoc-edge-e84
[easa-drones]: https://www.easa.europa.eu/en/the-agency/faqs/drones-uas
[jev-35b]: https://huggingface.co/autotrust/JEV-35B
[crivo-150m]: https://huggingface.co/tardellirs/crivo-150m
[crivo-32m]: https://huggingface.co/tardellirs/crivo-32m
[decision-index]: https://huggingface.co/spaces/multimodalart/jev-decision-index
[embbert]: https://arxiv.org/abs/2502.10001
[pqrnn]: https://research.google/blog/advancing-nlp-with-efficient-projection-based-model-architectures/
[model2vec]: https://github.com/MinishLab/model2vec
[tang]: https://arxiv.org/abs/1903.12136
[eye-tracking]: https://arxiv.org/abs/2508.13244
[cubesat]: https://arxiv.org/abs/2603.20174
[speech]: https://arxiv.org/abs/2609.29867
[nplsd]: https://arxiv.org/abs/2609.25022
[argo]: https://arxiv.org/abs/2607.16222
[gideon]: https://arxiv.org/abs/2605.04282
[edge-review]: https://arxiv.org/abs/2603.08725
[ethos-u85]: https://www.arm.com/products/silicon-ip-cpu/ethos/ethos-u85
[alif-e4]: https://alifsemi.com/ensemble-e4-series/
[alif-e8]: https://alifsemi.com/ensemble-e8-series/
[nxp-rt700]: https://www.nxp.com/products/i.MX-RT700
