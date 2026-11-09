## 9. Toolchain and Component Ownership

| Responsibility | Initial tooling or component |
| --- | --- |
| Teacher adapter | Pinned open-teacher revision and its published decision interface; [teacher/vela_int8.py](../../teacher/vela_int8.py) for Vela 2.0 9B on a 12 GB GPU; an INT8 d3-flash loader for the same GPU is planned, with a two-GPU d3 variant later (§4) |
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
  comes from a US company. [REVIEW.md](../../REVIEW.md) §7 and §12 compare these
  options.
- A European teacher, if teacher provenance becomes a requirement: open-weight
  Mistral AI models (France), such as [Mistral Small 3.1][mistral-small]
  (Apache-2.0, image input). They generate text, so a decision readout over
  option-token probabilities and its calibration would have to be built and
  validated first.

[st-modelzoo]: https://github.com/STMicroelectronics/stm32ai-modelzoo-services
[cmsis-nn]: https://github.com/ARM-software/CMSIS-NN
[litert-micro]: https://developers.google.com/edge/litert/microcontrollers/overview
[bitnet]: https://github.com/microsoft/BitNet
[st-dqnn]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-dqnn-support.html
[embbert]: https://arxiv.org/abs/2502.10001
[pqrnn]: https://research.google/blog/advancing-nlp-with-efficient-projection-based-model-architectures/
[model2vec]: https://github.com/MinishLab/model2vec
[alif-e8]: https://alifsemi.com/ensemble-e8-series/
[nxp-rt700]: https://www.nxp.com/products/i.MX-RT700
[mistral-small]: https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503
[psoc-edge-e84]: https://www.infineon.com/products/microcontroller/32-bit-psoc-arm-cortex/32-bit-psoc-edge-arm/psoc-edge-e84
