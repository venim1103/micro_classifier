# Architecture Improvements & Technical Review

This document provides a comprehensive architectural assessment and actionable improvement plan for the `micro-classifier` repository. It synthesizes findings across sensor simulation, prompt token budgeting, embedded C stack optimization, and NPU compilation export.

---

## 1. Executive Summary & Architectural Strengths

The repository exhibits rigorous engineering standards and defensive design principles across its host-side tooling, protocol codecs, and reference microkernel implementations:
* **Strict Epistemic & Safety Hygiene:** Quarantined evaluation runs, anti-leakage record hashes, and explicit non-claim boundaries (`sim/reports/rules-baseline-20261020.json`, `teacher/provenance.py`) prevent conflating synthetic fixture tests with physical robot certification.
* **Defensive C11 Design:** Zero dynamic heap allocation (`firmware/micro_classifier_heads.c`), absence of packed-struct undefined behavior (using explicit byte-offset reading/writing in `firmware/micro_classifier_codec.c`), atomic output semantics, and robust stream re-synchronization (`mc_v0_stream_flush`).
* **Mathematical Rigor in Geometric Probes:** Compensated partial-sum accumulation (Kahan/Neumaier style summation in `add_partial`) and strict IEEE-754 binary32/binary64 assertions guarantee reproducible reference calculations.

---

## 2. Improvement Area 1: Breaking the 2,048-Token Teacher Prompt Wall (`teacher/`)

### Diagnosis
Serializing an 8-tick window of 8x8 ToF grids plus state history into prompt contexts for models like `d3-flash` and `d3-mini` easily exceeds the 2,048-token ceiling. Even with lossless row-table representations and exact binary32 decimal drafts (`teacher/prompt_budget.py`, `teacher/label_pipeline.py`), verbose string representations cause severe BPE token fragmentation. Furthermore, longer-context INT8 quantization caused decision flips compared to streamed BF16 (`REVIEW.md §31`).

### Concrete Code Fixes
* **Hardware-Aligned Integer Quantization (mm/cm):** Replace arbitrary binary32 string round-tripping in prompts with canonical integer millimeters (`0–4000`, matching physical VL53L8CX sensor outputs) and compact status codes. This cuts BPE token splitting by ~70% while remaining lossless relative to physical hardware.
* **Schema-Level Held-Frame Deduplication:** Since ToF captures at 15 Hz inside a 20 Hz decision loop (`REVIEW.md §73`), approximately 2 of every 8 history ticks are held duplicates where only `tof_age_s` advances. Introduce an explicit schema reference (`same_as_slot`) for held captures to eliminate redundant range payload serialization.

---

## 3. Improvement Area 2: Resolving Sensor Coverage & Observability Dead-Zones (`sim/`)

### Diagnosis
As analyzed in `REVIEW.md §§75–77`, `sim/rules.py`, and `sim/rover.py`, 25 false-clears occurred during baseline evaluation. Synthetic counterexamples proved that identical 8-tick histories can have opposite turning-clearance truths due to blind spots between infinitesimal point-rays and edge cases at the `0.03m` floor band threshold.

### Concrete Code Fixes
* **Frustum / Solid-Angle Zone Footprints vs. Pinhole Rays:** Upgrade `sim/rover.py` from infinitesimal point-rays to volumetric 8x8 zone cones (`~5.6°×5.6°` per zone on the VL53L8CX) so normal cylindrical obstacles cannot slip between rays or vanish at the floor band edge.
* **Observable-Frustum Clearance Contract:** Redefine `clear_sector` so sectors sweeping outside the union of observed/registered frustums over the braking horizon explicitly output unknown/abstain (`Status.REJECT_OUT_OF_DOMAIN`), closing observability blind spots.

---

## 4. Improvement Area 3: Cortex-M55 Stack Footprint & Floating-Point Optimization (`firmware/` & `interface/`)

### Diagnosis
The C affine head evaluator (`firmware/micro_classifier_heads.c`) allocates a large single-function stack frame (~2,176–2,200 bytes reported by `interface/build_audit.py` at `-O0`/`-O2`/`-Os`) containing partial-sum expansion arrays. Additionally, reliance on binary64 (`double`) intermediates and `-lm` across head and math routines creates unnecessary soft-float dependencies on Cortex-M55.

### Concrete Code Fixes
* **Stack Reduction (<128B):** Replace large stack-allocated partial-sum expansion arrays with either an explicit caller-supplied scratch struct or register-level compensated summation to eliminate RTOS stack-overflow risk on STM32N6.
* **Cortex-M55 Helium (MVE) & NPU Alignment:** Separate the host `fp64` reference oracle path from the target Cortex-M55 path, ensuring target builds remain strictly `fp32` or fixed-point (`q7`/`q15`) without pulling in soft/scalar double `libm` routines.

---

## 5. Improvement Area 4: Repository DX & Documentation Restructuring (`README.md`)

### Diagnosis
`README.md` currently reads like a chronological audit log (~3,500 words with repeated scope disclaimers in every section) and lacks standard GitHub repository metadata and visual architecture flowcharts.

### Concrete Code Fixes
* **Mermaid Architecture Diagram:** Add a clean architecture diagram depicting the Host Controller $\leftrightarrow$ UART (`mc_v0_codec`) $\leftrightarrow$ STM32N6 Module (`mc_v0_state_history` + ToF + Rules/NPU Student) and offline Teacher/Sim distillation loop.
* **Verification & Qualification Status Matrix:** Provide a consolidated summary table to replace repetitive per-section disclaimers, while archiving historical experiment logs into `REVIEW.md` or collapsible `<details>` blocks.

---

## 6. Prioritized Action Roadmap

1. **PR 1:** Implement integer millimetric ToF encoding in `teacher/prompt_budget.py` and `teacher/label_pipeline.py` to break the 2,048 token wall.
2. **PR 2:** Add `same_as_slot` held-frame deduplication to prompt schemas.
3. **PR 3:** Upgrade `sim/rover.py` point rays to volumetric 8x8 zone cones (`~5.6°×5.6°`) and update `sim/rules.py` clearance contracts.
4. **PR 4:** Refactor `firmware/micro_classifier_heads.c` stack allocation to use caller-supplied scratch buffers (<128B stack frame).
5. **PR 5:** Restructure `README.md` with Mermaid architecture diagrams and a unified verification matrix.
