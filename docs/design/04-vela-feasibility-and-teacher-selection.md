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

[teacher/vela_int8.py](../../teacher/vela_int8.py) changes only how the weights are
stored. It builds the release model without materializing weights and stores the
ten large projections of every layer (MLP gate/up/down, attention q/k/v/o, Gated
DeltaNet `in_proj_qkv`, `in_proj_z`, `out_proj`) as symmetric INT8 with one
BF16 scale per 128 input columns, expanded to BF16 just before each matmul.
Gates, convolutions, norms, and heads stay FP32 as released, and the FP32
embedding table stays in host RAM. The release's own tokenizer, rendering,
calibration, and SystemOne engine run unchanged from the pinned revision.

[teacher/validate_vela_int8.py](../../teacher/validate_vela_int8.py) compares it with
a BF16 reference that streams the release's stored BF16 weights through the same
kernels, which is the evaluated computation without 32 GB of memory, and with
the outputs the release recorded for its README examples. Results on an RTX
A3000 12 GB laptop GPU under WSL2, using Transformers' PyTorch Gated DeltaNet
kernel ([full report](../../teacher/reports/vela-2.0-9b-int8-g128-rtx-a3000.json)):

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
[teacher/d3_int8.py](../../teacher/d3_int8.py), PyTorch reference Gated DeltaNet,
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

[teacher/validate_d3_int8.py](../../teacher/validate_d3_int8.py) now compares both
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

Full reports: [d3-flash](../../teacher/reports/d3-flash-int8-g128-rtx-a3000.json)
and [d3-mini](../../teacher/reports/d3-mini-bf16-rtx-a3000.json). Flash maximum
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
[teacher/vela_int8.py](../../teacher/vela_int8.py) as in the two-GPU list below,
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
[teacher/vela_int8.py](../../teacher/vela_int8.py) with these differences:

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

[mini-int8-parity-report]: ../../teacher/reports/d3-mini-int8-parity-capped-20261016.json
[mini-context-report]: ../../teacher/reports/d3-mini-context-resource-capped-20261016.json
[mini-context-parity-report]: ../../teacher/reports/d3-mini-context-parity-capped-20261016.json
[vela-small-config]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/config.json
[vela-small-usage]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/USAGE.md
[vela-small-code]: https://huggingface.co/vllm-sr/Vela-2.0-0.3B/blob/main/modeling_vela2.py
[vela-medium-usage]: https://huggingface.co/vllm-sr/Vela-2.0-4B/blob/main/USAGE.md
[vela-large-usage]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/USAGE.md
[vela-large-code]: https://huggingface.co/vllm-sr/Vela-2.0-9B/blob/main/modeling_vela2.py
[vela-08b]: https://huggingface.co/vllm-sr/Vela-2.0-0.8B
[d3-collection]: https://huggingface.co/collections/vllm-sr/decision-30
[typesafe-mca]: https://typesafe.ai/legal/mca
[d3-card]: https://huggingface.co/vllm-sr/d3
[fla]: https://github.com/fla-org/flash-linear-attention
[jev-27b-vl]: https://huggingface.co/autotrust/JEV-27B-VL
[jev-corpus]: https://huggingface.co/datasets/SargeDev/jev-distill-corpus-v3
[lbc]: https://arxiv.org/abs/1912.12294
