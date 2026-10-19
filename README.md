# micro_classifier

A Jev-like decision module for robots on an STM32N6: typed decisions from a
small student model distilled from open teachers. Design and feasibility
findings: [DESIGN.md](DESIGN.md).

Independent research review of the design: [REVIEW.md](REVIEW.md).

## Teacher tooling

[teacher/d3_int8.py](teacher/d3_int8.py) loads the approved Decision 3.0
d3-flash revision with INT8 text projections, or d3-mini in BF16. Both keep
BF16 embeddings in host RAM, fully authenticate the package manifest, and
restrict requests to text/JSON and local images. A native BF16-capable CUDA
GPU is required for the measured validation path. Videos, the release HTTP
server, and remote media are excluded.

```python
from teacher import d3_int8

teacher = d3_int8.load_engine()  # pinned d3-flash; downloads only if needed
result = teacher.system_one(
		state="The path ahead is clear.",
		questions={"blocked": {"type": "noul", "instructions": "Is the path blocked?"}},
)
```

Run the fixed 25-request text, rover-state and local-image diagnostic suite:

```sh
python -m teacher.validate_d3_int8 --output teacher/reports/d3-flash-local.json
python -m teacher.validate_d3_int8 --repo-id vllm-sr/d3-mini \
	--output teacher/reports/d3-mini-local.json
```

These checks establish numerical parity and resource use, not task accuracy
or commercial training-data clearance. See [DESIGN.md](DESIGN.md) §4 for the
measured results and [REVIEW.md](REVIEW.md) F15 for the provenance question.

[teacher/vela_int8.py](teacher/vela_int8.py) runs the Vela 2.0 9B teacher on a
12 GB CUDA GPU with INT8 weight-only projections (DESIGN §4). It downloads a
pinned, reviewed revision (about 18 GB) into the Hugging Face cache and imports
that release's Python code.

```python
from teacher import vela_int8

engine = vela_int8.load_engine()  # GPU parameters: 6.6 GiB
engine.system_one(state="...", questions={...})
```

Validate against the release's BF16 weights and recorded outputs, and measure
memory and speed (writes a JSON report):

```sh
python -m teacher.validate_vela_int8 --output teacher/reports/<name>.json
```

The separately approved mini INT8 parity experiment requires an already-cached
pinned snapshot and enforces a 10 GiB PyTorch allocator cap. It aborts rather
than retrying OOM, and requires a fresh output path:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m teacher.validate_d3_int8 \
	--repo-id vllm-sr/d3-mini --snapshot /path/to/already-cached/mini/snapshot \
	--mini-int8-experiment --output teacher/reports/mini-int8-local.json
```

This phase stays at 2,048 tokens. Normal mini remains BF16; this opt-in is not
live-labeling approval or a change to normal token limits. The cap excludes
driver/native allocations. See [REVIEW.md](REVIEW.md) §29 for measured results.

After reviewing that parity report, the separately approved resource-only phase
uses three fixed existing full inputs at 4,096/8,192/12,288 ceilings. It writes
resource and input/token hashes only, discards answers, and stops on OOM/cap
failure without retry. The existing ignored simulation logs must be present:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m teacher.validate_d3_int8 \
	--repo-id vllm-sr/d3-mini --snapshot /path/to/already-cached/mini/snapshot \
	--mini-int8-context-probe \
	--reviewed-parity-report teacher/reports/d3-mini-int8-parity-capped-20261016.json \
	--output teacher/reports/mini-context-local.json
```

Selected warm inputs ran within the experimental resource envelope, not the
normal 2,048-token limit. Neither longer-context quality nor mode labels are
approved; normal defaults/input/history are unchanged. See
[REVIEW.md](REVIEW.md) §30 for measured limits and exclusions.

The separately approved longer-context parity phase uses the same inputs and
ceilings, comparing INT8 with streamed BF16. It saves only deltas/flips,
resource measurements and provenance, not response values:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m teacher.validate_d3_int8 \
	--repo-id vllm-sr/d3-mini --snapshot /path/to/already-cached/mini/snapshot \
	--mini-int8-context-parity \
	--reviewed-parity-report teacher/reports/d3-mini-int8-parity-capped-20261016.json \
	--output teacher/reports/mini-context-parity-local.json
```

The measured warm-clear input changed its selected option at both admitted
ceilings. This is numerical diagnostic evidence, not task accuracy or mode-label
approval. Normal defaults and input/history remain unchanged; see
[REVIEW.md](REVIEW.md) §31 for the finding and review gates.

CPU unit tests: `python -m pytest tests`.

## Host-Only C Protocol Tooling

The [C11 API][c-codec-api] and [source][c-codec-source] decode the provisional
state/decision wire format, encode caller-buffer frames, calculate CRC-32 and
recover frames from byte chunks,
reusing the generated constants and existing golden vectors. They use fixed
native outputs, no allocation/HAL or packed-wire casts. Failed direct decodes
leave outputs unchanged. The library is host-tested and compiles to Cortex-M55
objects, not linked board firmware.

```sh
python -m pytest -q tests/test_interface.py
```

Call `mc_v0_decode_state` or `mc_v0_decode_decision` with a readable byte buffer,
its exact frame length and a native output pointer; check for `MC_V0_DECODE_OK`
before reading the output. Decision answer slots use `question_id - 1`; only
slots selected by `answer_mask` are present. A successfully decoded rejection/
fault is **not a usable recommendation**. The CRC function requires readable
bytes for its length; null data is permitted only at length zero. No physical
range, stale-data, timeout, ordering or fail-safe policy is imposed. Use binary32
float and binary64-or-better double precision; fast/finite-only math builds are
unsupported. Changed protocol version/capacity assumptions require codec updates.

Initialize `mc_v0_stream` with `mc_v0_stream_init`, then pass each byte chunk,
a nonnull callback and context to `mc_v0_stream_feed`. A zero-length chunk may
have null data. Feed success means processing succeeded; only callbacks deliver
validated packets, possibly none or several. The callback packet is borrowed
only until it returns; copy anything retained. Serialize access to each stream,
and do not feed/reset it from its callback. The framing buffer is 128 bytes plus
fixed metadata. `rejected_frames` counts rejected candidates, not noise bytes,
and saturates at `UINT32_MAX`. On a transport-chosen timeout, init discards
partial input and clears counters; no threshold is imposed by this library.

The test suite includes golden/stream parity, sanitizer checks, seeded malformed
fixtures, tolerance edges and host/Arm compilation. DESIGN.md §2 and REVIEW.md
§§53-56 record the host-only authorization and verification limits.

For encoding, pass a native state/decision, writable destination, capacity and
length pointer to `mc_v0_encode_state` or `mc_v0_encode_decision`. All pointers
must be nonnull and the source, destination and length objects must not overlap.
There is no size-query mode. Check `MC_V0_ENCODE_OK` before using output; failure
leaves the source, destination and length unchanged. Only the returned byte
count is written on success, leaving remaining capacity untouched. State frames
are 92 bytes; decision frames are 36-128 bytes. An empty fault can be encoded as:

```c
#include "micro_classifier_codec.h"

mc_v0_result encode_fault(uint8_t *frame, size_t capacity, size_t *written) {
	const mc_v0_decision decision = {.status = MC_V0_STATUS_FAULT};
	return mc_v0_encode_decision(&decision, frame, capacity, written);
}
```

For decisions, initialize the prefix and mask-selected answer slots. Present
IDs/types/counts/selections are checked; absent slots are ignored. Input
`confidence` is ignored and derived from the binary32 probabilities, matching
Python. Re-encoding accepted noncanonical confidence may change its bytes.
Encoding a diagnostic or fault packet does not make it a usable recommendation.
The completed checks include exact-capacity native sanitizers, all validity
masks and 1,000 seeded synthetic cross-language round trips. They are host/
compile evidence, not board runtime or safety qualification; board integration
and broader firmware remain outside scope.

[c-codec-api]: firmware/include/micro_classifier_codec.h
[c-codec-source]: firmware/micro_classifier_codec.c

## Host-Only C State History

The [eight-slot history API][state-history-api] and [source][state-history-source]
retain validated host-state samples and explicit caller-declared gaps. They are
a host-tested reference, not complete ToF/student history or board firmware.

Initialize `mc_v0_state_history` with `mc_v0_state_history_init`. For each caller-
chosen tick, call `mc_v0_state_history_push` with a native state or explicitly
call `mc_v0_state_history_gap`. Invalid pushes do not modify or advance history;
null state is an error, never a gap. Obtain a copied `mc_v0_state_window` with
`mc_v0_state_history_snapshot`. Operations return `MC_V0_HISTORY_OK` on success;
init(null) is a no-op. The shared `mc_v0_validate_state` applies the unchanged
wire-state validation rules independently of framing.

Snapshot order is oldest-to-newest: mask bit 0 is oldest, bit 7 newest. Unfilled
and gap slots are zero placeholders; consult `valid_mask` before using a sample.
A present state's sensor-validity mask can still be zero. States, source ages,
sequence and timestamps are copied unchanged. No timeout, sequence rejection,
automatic gap insertion, interpolation, normalization or safety policy is added.
Callers must initialize, leave internal fields alone, serialize access and keep
source/history/output objects valid and nonoverlapping. Copies are detached.

```sh
python -m pytest -q tests/test_interface.py -k 'c_history or c_codec'
```

Core host/Cortex-M55 compile checks pass; seeded and native sanitizer follow-ups
are next. DESIGN.md §2 and REVIEW.md §57 record approval and limitations. No ToF/
tensor packing, inference or board integration is included.

[state-history-api]: firmware/include/micro_classifier_history.h
[state-history-source]: firmware/micro_classifier_history.c

## Simulation Label Policy Draft

The [catalogue][sim-catalogue-draft] and [labeler][sim-label-draft] are approved
for **simulation smoke and fake-teacher pipeline tests only**. They propose deterministic
observation-only proxies for `path_blocked`, `clear_sector` and `speed_tier`,
with explicit abstention; `mode` always awaits human review. Every result is
unreviewed and training-disabled, with catalogue/config/input/source hashes.
The formulas and limitations await review in [DESIGN.md](DESIGN.md) §7.

```sh
python -m pytest -q tests/test_sim.py -k draft
```

Run the approved four-scene smoke suite into a new ignored directory:

```sh
python -m sim.labels --output sim/episodes/my-label-smoke \
	--report sim/reports/my-label-smoke.json --seed 20261016
```

The [recorded smoke][sim-label-smoke-report] has 567 observations and four
successful scenes, but no positive-blocked or lower-speed examples. Results
remain training-disabled, not a reviewed dataset or safety evidence. `mode`
is always unlabeled; real teacher labeling and training remain unapproved.
The original simulator CLI and wire export are unchanged.

Run the separately approved bounded diagnostic study into a new directory:

```sh
python -m sim.labels --coverage-study --output sim/episodes/my-label-coverage \
	--report sim/reports/my-label-coverage.json --seed 20261016
python -m pytest -q tests/test_sim.py -k label_coverage
```

The [recorded study][sim-label-coverage-report] contains eight 32-tick episodes
with 264 observations: both blocked values, every sector option and every speed
tier occur. Twelve synthetic option/fault fixtures are reported separately;
`mode` is always absent. Physics/sensor defaults and label rules are unchanged;
only the diagnostic horizon is shortened from 400 ticks. These selected probes
and artificial faults are **not representative data, reviewed labels or safety
evidence**. Eight intentional horizon timeouts are not navigation results.
No training or live teacher ran. See DESIGN.md §7 and REVIEW.md §26 for limits.

## Synthetic Navigation Reference

The [ideal-geometry reference][navigation-reference] implements the three
adopted **simulation-only** navigation meanings on artificial fixtures:

```python
from sim.navigation import evaluate_synthetic
from sim.rover import Scenario

result = evaluate_synthetic(
	Scenario(), speed=0.6, tof_age_s=0.1, synthetic_test_only=True
)
```

This is not an observation or episode labeler. It reads no logs and exports no
data. Results are synthetic and training-disabled; mode remains absent. Numeric
ambiguity and computation exhaustion abstain rather than claiming clearance.
The opt-in is not source attestation, and numerical allowances are not formal
certificates or physical limits. Existing proxies/defaults are unchanged. Real
annotations, task datasets/splits, inference and training remain unapproved;
reviewed observation-to-target evidence is still missing. See REVIEW.md §36.

The separate `probe_synthetic_ray_witness` API tests eight artificial exact rays
for a positive straight-braking witness only. Missing hits never mean clear;
normal noisy/delayed defaults, curves and numeric ambiguity abstain. It is not
a real-input model, log labeler or observation adapter; exactness/registration
are fixture assumptions. No existing logs or annotations were used. See
REVIEW.md §39 for the feasibility study and its limits.

The separate `probe_synthetic_bounded_ray_witness` draft accepts explicit
artificial range/translation/heading bounds and requires their entire error
ball inside the stopping footprint. Bounds are caller assumptions, not measured
limits or Gaussian-noise confidence levels. Existing exact-probe/default guards
remain unchanged; no logs, real labels or data production are enabled. See
REVIEW.md §40 for the synthetic-only model and remaining evidence gaps.

`register_synthetic_points` separately checks static planar frame composition
with supplied artificial mounting/body poses and acquisition/reference times.
Missing evidence stays unknown; transformed fixtures do not qualify physical
registration or enable delayed/noisy witness inputs. See REVIEW.md §42 for the
synthetic-only reference and tests; no observation/log adapter is provided.

`register_synthetic_bounded_points` additionally propagates explicit artificial
point/pose error assumptions. Its algebraic radii are not measured limits or
certified floating-point bounds and do not enable witness labels or real-input
use. REVIEW.md §44 records the model, checks and remaining qualification gates.

`probe_synthetic_registered_witness` separately tests whole assumed obstacle-
location balls against the straight braking footprint, using artificial point/
pose inputs and explicit obstacle membership. It yields only a conditional
positive witness or unknown, not clear/negative labels or qualified real input.
REVIEW.md §45 records independent geometry and numerical-cancellation checks.

[navigation-reference]: sim/navigation.py

## Bounded Sensor Diagnostics

[The CPU-only collector][sensor-diagnostics] retains acquisition poses/times
and noiseless simulator references separately from unchanged student observations.
It enforces at most four scenes and 32 ticks, leaves normal Config unchanged and
marks horizon stops censored. Outputs must be fresh; logs remain quarantined.

[The approved four-prefix study][sensor-diagnostics-report] contains 131
observations: three censored 32-tick horizons and a slalom collision at tick 31.
The turn-schedule policy is diagnostic-only, not an expert. Conditional residuals
exclude clipped/missing/reference-censored zones; observed maxima are not hard
bounds. Shared-model transforms are software checks, not independent physical
metrology or real-input qualification. No witness, label, dataset, reviewed
cohort/split or training path is enabled. See DESIGN.md §7 and REVIEW.md §46.

[sensor-diagnostics]: sim/diagnostics.py
[sensor-diagnostics-report]: sim/reports/sensor-diagnostics-20261019.json

## Simulation Readiness Pilot

[The separately approved coordinator][readiness-tool] ran eight normal-Config
episodes and exported 32 blank full-input projections, with private lineage
separate from the blind bundle. Only the blind bundle is reviewer input; source
logs, mapping and report contain privileged metadata. Opaque IDs and file
permissions do not guarantee anonymity. No real annotation/import is enabled.

[The report][readiness-report] records 1,130 observations and eight privileged-
controller successes. The 32 projections contain 25 distinct inputs: all eight
reset windows match exactly. These sources cannot be distributed across five
purposes with those windows retained under the duplicate-input rule. No task
labels, evidence qualification, accepted family/cohort/split or training resulted;
all artifacts remain quarantined. See DESIGN.md §7 and REVIEW.md §49.

[readiness-tool]: teacher/readiness.py
[readiness-report]: teacher/reports/readiness-pilot-20261019.json

## Diagnostic Source-Provenance Audit

The [bounded audit][provenance-audit] compares identities and declared metadata
from 1-16 existing diagnostic logs without changing them:

```sh
CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m teacher.provenance \
	--episode sim/episodes/label-smoke-20261016/clear.jsonl \
	--episode sim/episodes/wire-v0-smoke/clear-20261015.jsonl \
	--output teacher/reports/my-provenance-audit.json
```

Output must be fresh. Only metadata is parsed; all bytes are hashed, but body
observations/actions/labels are not validated or reproduced. Similarity matches
are candidate evidence, never accepted families, cohorts or splits. All logs
remain diagnostic-only, with unresolved lineage. The [16-source report][provenance-audit-report]
found three repeated-geometry groups despite distinct file hashes. It does not
establish independence or promote a task dataset. See REVIEW.md §37 for limits.

[provenance-audit]: teacher/provenance.py
[provenance-audit-report]: teacher/reports/provenance-audit-20261016.json

## Blind Human-Review Preparation

The [CPU-only review tooling][blind-review-tool] exports blank packets from
existing logs. It preserves full state/history and provenance without teacher,
proxy, truth or action suggestions. The three rules remain diagnostic-only;
mode is unlabeled. Source/template families and partitions remain unresolved.

```sh
CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m teacher.review \
	--episode sim/episodes/label-smoke-20261016/clear.jsonl \
	--episode sim/episodes/label-smoke-20261016/obstacle.jsonl --limit 16 \
	--output teacher/cache/my-review-packets.json \
	--report teacher/reports/my-review-preparation.json
```

`--limit` applies per episode; at most 32 records may be requested in total.
Both output paths must be fresh. Full packets stay in ignored `teacher/cache/`;
the optional report contains counts and hashes, not annotations. The [recorded
run][blind-review-report] prepared 32 blank packets, including 18 full histories,
with no annotations or teacher calls. Hashes provide consistency, not anonymity
or reviewer attestation. Python review normalization is fake-test-only and
rejects mode labels; real annotation/import, target acceptance, reviewed task
datasets, locked splits and training remain unapproved. See REVIEW.md §32.

[blind-review-tool]: teacher/review.py
[blind-review-report]: teacher/reports/review-preparation-20261016.json

## Teacher-Pipeline Host Tooling

The [request planner and cache API][teacher-label-pipeline] are approved for
**fake-teacher tests only**. The planner preserves host state, current ToF and
full masked history, checking any embedded wire frames. Truth, actions and
proxy labels are excluded. Its only question is the human-review `mode`
supplement, not teacher replacement of the three deterministic sensor proxies.

Prepare a bounded plan from an existing simulator episode, without loading or
calling any teacher:

```sh
python -m teacher.label_pipeline \
	--episode sim/episodes/wire-v0-smoke/clear-20261015.jsonl \
	--output teacher/cache/my-request-plan.json --limit 8
python -m pytest -q tests/test_label_pipeline.py
```

The input may be a plain simulator log or a `--wire` log. Outputs must be new;
plans/cache data under `teacher/cache/` are ignored. The Python `LabelCache`
and `label_requests` APIs support injected test doubles, strict probability
validation and transactional resume with source/revision/settings hashes.
The [tests][teacher-pipeline-tests] show fake-only use. There is no live-model
CLI path. Every cached answer is synthetic, training-disabled and requires
human review. Token-budget fit and genuine label quality remain unverified;
full history is not silently truncated. See DESIGN.md §7 and REVIEW.md §20.

The [offline prompt preflight][prompt-budget] uses only the approved cached
tokenizer/prompt assets, never weights or inference:

```sh
HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES="" python -m teacher.prompt_budget \
	--episode sim/episodes/wire-v0-smoke/clear-20261015.jsonl \
	--output teacher/reports/my-prompt-budget.json --limit 8
```

It includes complete question/chat overhead, checks pinned asset hashes, and
refuses downloads, remote tokenizer code, truncation and budget increases.
`--repo-id vllm-sr/d3-mini` selects the other approved cached tokenizer.
Outputs must be new; exit 1 means prompts exceed the 2,048-token ceiling.
The recorded [flash][prompt-budget-flash]/[mini][prompt-budget-mini] runs each
found all 16 sampled prompts over budget (3,421-6,936 tokens). **The current
renderer is not budget-qualified for live use.** Input/representation review
is needed; no automatic trimming or larger budget is approved. See REVIEW.md §23.

An opt-in **lossless row-table draft** can be compared without changing the
default renderer. It reuses identical rows and verifies exact reconstruction,
preserving every input value and history slot:

```sh
HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES="" python -m teacher.prompt_budget \
	--episode sim/episodes/wire-v0-smoke/clear-20261015.jsonl \
	--output teacher/reports/my-row-draft-comparison.json --limit 16 \
	--compare-compact-draft
```

The recorded [flash][row-draft-flash]/[mini][row-draft-mini] comparisons cover
80 existing observations with exact round trips, but 65/80 draft prompts still
exceed 2,048 tokens, reaching 9,698. Only startup ticks 0-2 fit. The draft remains
unreviewed, opt-in and **not qualified for live labeling**; no inference or
training was run. See DESIGN.md §7 and REVIEW.md §24 for limits.

A second, separately opt-in **exact typed float32 draft** uses short decimal
strings only for rows whose values reconstruct identically through binary32;
all other rows stay literal. It does not reduce input precision:

```sh
HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES="" python -m teacher.prompt_budget \
	--episode sim/episodes/wire-v0-smoke/clear-20261015.jsonl \
	--output teacher/reports/my-float32-draft-comparison.json --limit 16 \
	--compare-float32-draft
```

The [flash][float32-draft-flash]/[mini][float32-draft-mini] results reconstruct
all 80 sampled states exactly, but **63/80 still exceed 2,048 tokens** (811-6,016).
Only two additional startup requests fit; no sampled full-eight-tick-history
request fits. Neither draft is approved for live use or teacher-quality claims.
The comparison flags and cost-study flag below are mutually exclusive; omitting
all three retains the full-renderer preflight. See DESIGN.md §7 and REVIEW.md §25.
No inference or training was run.

An offline cost study diagnoses the three existing forms without creating a
new representation or changing any input:

```sh
HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES="" python -m teacher.prompt_budget \
	--episode sim/episodes/wire-v0-smoke/clear-20261015.jsonl \
	--output teacher/reports/my-input-cost-study.json --limit 16 \
	--profile-input-costs
```

The [flash][input-cost-flash]/[mini][input-cost-mini] studies reproduce the
complete-prompt results on 80 existing inputs; none of the 45 full-history
inputs fits in any form. Isolated full ToF-history fields cost 4,771-8,432
tokens; typed row tables 2,635-5,131. **Standalone field counts are not additive,
removal savings, lower bounds or request budgets.** They never replace complete
inputs. CLI summary/exit status refer to full/default prompts; each form has
its own budget results. No teacher or training runs. See REVIEW.md §27-28 for
the unaccepted target/evaluation proposal and input-strategy decisions.

## Synthetic Evaluation Tooling

[CPU-only metrics and split checks][teacher-evaluation] are approved for
synthetic fixtures only. The CLI runs a built-in arithmetic fixture, not
episode logs, real labels or trained models:

```sh
python -m teacher.evaluation --output teacher/reports/my-synthetic-evaluation.json
python -m pytest -q tests/test_evaluation.py
```

Outputs must be new. The [recorded report][synthetic-evaluation-report] is
plumbing evidence, not robot accuracy or a locked dataset. The Python API
provides explicit ordered-class macro-F1/recall, NLL, Brier, ECE and tied
risk/coverage curves. Split checks reject declared group/input overlap across
five separate purposes; identifiers/hashes are not attested against files.
Missing classes and infinite NLL are explicit, with no silent normalization
or clipping. See DESIGN.md §7 and REVIEW.md §22 for conventions and limits.
Real evaluation, baseline fitting and training remain gated.

## M1a Host Probes

[CPU preparation tooling][m1a-script] exports nine **untrained** fixed-shape
probes: equivalent temporal Conv layouts, in/out-of-graph pooling and Gather,
a numeric MLP, 8x8 ToF and 64x64 camera Conv probes, and a transformer block.
It checks float ONNX against PyTorch and runs signed INT8 QDQ on separate
seeded synthetic evaluation inputs. No training, teacher or board is needed.

```sh
python -m export.m1a --output export/artifacts/my-run \
	--report export/reports/my-run.json
python -m pytest -q tests/test_export.py
```

Output directories/reports must be new. ONNX artifacts are ignored; JSON
reports include hashes, shapes, operators and numerical error. The [recorded
CPU run][m1a-report] prepared nine cases; the transformer exceeds the diagnostic
INT8 error bound and is explicitly unqualified. Its test remains an expected
failure, not a loosened tolerance. Synthetic inputs are not deployment
calibration or task data. ST compilation, memory fit, latency and board gates
remain unmeasured; see [DESIGN.md](DESIGN.md) §12 and [REVIEW.md](REVIEW.md) §16.

[Compiler orchestration][st-compile-script] is **dry-run by default**:

```sh
python -m export.st_compile \
	--manifest export/artifacts/my-run/manifest.json \
	--output export/artifacts/my-st-run --expected-version 4.0.1
```

Planning verifies input hashes but invokes nothing and creates no output.
The version is a documented CLI example, not an installed-tool claim. Once
the approved licensed toolchain is supplied, select it with
`--executable /actual/path/to/stedgeai` and add `--execute`. The runner checks
the exact release, uses the built-in internal-only profile, and retains raw
logs/reports and a hashed `result.json` inventory in a fresh output directory.
Timeout/interruption kills the POSIX process group (`--timeout`, default 600
seconds per command). No board command is invoked. Success is only
`generated_reports_pending_review`, not M1a acceptance or full firmware fit.
See [REVIEW.md](REVIEW.md) §17 for unverified vendor/toolchain limitations.

## Provisional Interface Tooling

[Python codecs][wire-python] provide little-endian, CRC-protected state and
decision frames with explicit validity, ages, versions, statuses and full
probability distributions. State frames are 92 bytes; full decision frames
are 128 bytes. ToF and history stay on the module, not in host UART frames.

```python
from interface.protocol import State, decode_state, encode_state

packet = State(sequence=42, timestamp_us=50000, goal_m=(4.0, 0.0, 0.0))
assert decode_state(encode_state(packet)) == packet
```

Regenerate the [C byte-offset header][wire-header] from the Python definitions:

```sh
python -m interface.protocol --write-header firmware/include/micro_classifier_protocol.h
python -m pytest -q tests/test_interface.py
```

[Golden vectors][wire-golden] are synthetic codec fixtures, not model outputs
or reviewed labels. This is a host-side draft: no physical safety thresholds,
trained student, firmware integration or board validation. See
[DESIGN.md](DESIGN.md) §2 for the byte specification and application duties.

## Hardware-Free Simulation

[sim/rover.py](sim/rover.py) provides a CPU-only, seeded `RoverEnv` with
`reset`/`step`, bounded rover dynamics, 8x8 ToF noise/dropouts/latency, eight
ticks of masked history, rewards and explicit episode termination. It uses
the existing NumPy and SciPy dependencies; no board or teacher is needed.

```sh
python -m sim.rover --scenario obstacle --seed 0 --episodes 4 --render
python -m sim.rover --scenario slalom --seed 7 --wire
```

This writes new JSONL episodes and trajectory PNGs under the ignored
`sim/episodes/` directory, refusing to overwrite existing logs. Scenarios are
`clear`, `obstacle`, `corridor`, and `slalom`. Use a new seed or output
directory for another run. If the container's Matplotlib cache is read-only,
set `MPLCONFIGDIR=/tmp/micro-classifier-matplotlib` for rendering.

```python
from sim.rover import RoverEnv

env = RoverEnv()
observation, info = env.reset(seed=7)
observation, reward, terminated, truncated, info = env.step([0.3, 0.0])
```

Actions are desired forward speed in m/s and turn rate in rad/s. Observations
exclude true pose and world geometry; those appear separately in `info`.
The default scripted expert is deliberately map-aware and privileged. Its
actions are not reviewed training labels. `--policy reactive` selects a
sensor-only baseline known to collide in obstacle scenes.

Physics, sensor and reward defaults are configurable simulation assumptions,
not hardware measurements or physical safety limits. The ToF grid repeats
2-D rays vertically, not a full VL53L8CX model. `--wire` adds a provisional
contract manifest and exact CRC-protected `state_frame_hex` for every current
observation, including reset. Decode with `decode_state(bytes.fromhex(...))`.
The wire fields use FLU velocity/yaw rate and goal; battery/fault health remains
unknown. ToF/history stay in separate module-side observation fields, not the
host packet. No decision frames or reviewed labels are fabricated.
The simulation JSONL container remains separately versioned. See
[DESIGN.md](DESIGN.md) §7 for limits and the recorded smoke results.

[wire-python]: interface/protocol.py
[wire-header]: firmware/include/micro_classifier_protocol.h
[wire-golden]: interface/golden_vectors.json
[m1a-script]: export/m1a.py
[sim-catalogue-draft]: sim/catalogue.json
[sim-label-draft]: sim/labels.py
[sim-label-smoke-report]: sim/reports/label-smoke-20261016.json
[sim-label-coverage-report]: sim/reports/label-coverage-20261016.json
[teacher-label-pipeline]: teacher/label_pipeline.py
[teacher-pipeline-tests]: tests/test_label_pipeline.py
[teacher-evaluation]: teacher/evaluation.py
[synthetic-evaluation-report]: teacher/reports/evaluation-synthetic-20261016.json
[prompt-budget]: teacher/prompt_budget.py
[prompt-budget-flash]: teacher/reports/prompt-budget-d3-flash-20261016.json
[prompt-budget-mini]: teacher/reports/prompt-budget-d3-mini-20261016.json
[row-draft-flash]: teacher/reports/row-draft-budget-d3-flash-20261016.json
[row-draft-mini]: teacher/reports/row-draft-budget-d3-mini-20261016.json
[float32-draft-flash]: teacher/reports/float32-draft-budget-d3-flash-20261016.json
[float32-draft-mini]: teacher/reports/float32-draft-budget-d3-mini-20261016.json
[input-cost-flash]: teacher/reports/input-cost-d3-flash-20261016.json
[input-cost-mini]: teacher/reports/input-cost-d3-mini-20261016.json
[m1a-report]: export/reports/m1a-cpu-20261015.json
[st-compile-script]: export/st_compile.py
