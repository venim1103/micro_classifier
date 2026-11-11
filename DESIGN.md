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


## Reading Map

Historical wording and evidence limits are preserved in topic chapters.
Read the relevant chapter and newest checkpoint, not the entire archive.

- [2. Goals, Boundaries, and Open Requirements][chapter-design-00]
- [3. Verified Hardware and Compiler Constraints][chapter-design-01]
- [4. Vela Feasibility and Teacher Selection][chapter-design-02]
- [5. Audit of the PDF's Final Proposal][chapter-design-03]
- [6. Proposed Student Architecture][chapter-design-04]
- [7. Data and Distillation Design][chapter-design-05]
- [Native ToF Wall Computation Prerequisites (2026-11-10)][native-tof-wall-design]
- [Native ToF Cylinder Computation Prerequisites (2026-11-10)][native-tof-cylinder-design]
- [Native ToF Ray-Generation Prerequisites (2026-11-11)][native-tof-ray-design]
- [Native ToF Return-Postprocessing Prerequisites (2026-11-11)][native-tof-postprocessing-design]
- [Synthetic Evaluation Tooling (2026-10-16)][chapter-design-06]
- [Controlled Scalar Arithmetic Candidate (2026-11-03)][chapter-design-07]
- [NF1 Interval-to-Word Certificate Contract (2026-11-04)][chapter-design-08]
- [NF1 Process-Local Binding Identity Evidence Boundary (2026-11-05)][chapter-design-09]
- [8. Deployment Budget and Validation Gates][chapter-design-10]
- [9. Toolchain and Component Ownership][chapter-design-11]
- [10. Safety, Security, and Reproducibility][chapter-design-12]
- [11. Development Container][chapter-design-13]
- [12. Implementation Milestones][chapter-design-14]
- [13. Evidence and Limitations][chapter-design-15]
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

[crivo-32m]: https://huggingface.co/tardellirs/crivo-32m
[typesafe-mca]: https://typesafe.ai/legal/mca
[chapter-design-00]: docs/design/02-goals-boundaries-and-open-requirements.md
[chapter-design-01]: docs/design/03-verified-hardware-and-compiler-constraints.md
[chapter-design-02]: docs/design/04-vela-feasibility-and-teacher-selection.md
[chapter-design-03]: docs/design/05-audit-of-the-pdfs-final-proposal.md
[chapter-design-04]: docs/design/06-proposed-student-architecture.md
[chapter-design-05]: docs/design/07-data-and-distillation-design-01.md
[chapter-design-06]: docs/design/07-data-and-distillation-design-02.md
[chapter-design-07]: docs/design/07-data-and-distillation-design-03.md
[chapter-design-08]: docs/design/07-data-and-distillation-design-04.md
[chapter-design-09]: docs/design/07-data-and-distillation-design-04.md#nf1-process-local-binding-identity-evidence-boundary-2026-11-05
[chapter-design-10]: docs/design/08-deployment-budget-and-validation-gates.md
[chapter-design-11]: docs/design/09-toolchain-and-component-ownership.md
[chapter-design-12]: docs/design/10-safety-security-and-reproducibility.md
[chapter-design-13]: docs/design/11-development-container.md
[chapter-design-14]: docs/design/12-implementation-milestones.md
[chapter-design-15]: docs/design/13-evidence-and-limitations.md
[native-tof-wall-design]: docs/design/07-data-and-distillation-design-02.md#native-tof-wall-computation-prerequisites-2026-11-10
[native-tof-cylinder-design]: docs/design/07-data-and-distillation-design-05.md#native-tof-cylinder-computation-prerequisites-2026-11-10
[native-tof-ray-design]: docs/design/07-data-and-distillation-design-01.md#native-tof-ray-generation-prerequisites-2026-11-11
[native-tof-postprocessing-design]: docs/design/07-data-and-distillation-design-02.md#native-tof-return-postprocessing-prerequisites-2026-11-11
