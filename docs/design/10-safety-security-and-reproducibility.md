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

[typesafe-mca]: https://typesafe.ai/legal/mca
[decision-paper]: https://vllm-sr.ai/decision-paper
[jev-corpus]: https://huggingface.co/datasets/SargeDev/jev-distill-corpus-v3
[easa-drones]: https://www.easa.europa.eu/en/the-agency/faqs/drones-uas
