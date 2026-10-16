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

CPU unit tests: `python -m pytest tests`.

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
[m1a-report]: export/reports/m1a-cpu-20261015.json
[st-compile-script]: export/st_compile.py
