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

[wire-codec-api]: ../../firmware/include/micro_classifier_codec.h
[wire-codec-source]: ../../firmware/micro_classifier_codec.c
[state-history-api]: ../../firmware/include/micro_classifier_history.h
[state-history-source]: ../../firmware/micro_classifier_history.c
[mini-int8-parity-report]: ../../teacher/reports/d3-mini-int8-parity-capped-20261016.json
[mini-context-report]: ../../teacher/reports/d3-mini-context-resource-capped-20261016.json
[mini-context-parity-report]: ../../teacher/reports/d3-mini-context-parity-capped-20261016.json
[decision-math-api]: ../../firmware/include/micro_classifier_math.h
[decision-math-source]: ../../firmware/micro_classifier_math.c
[head-reference-api]: ../../firmware/include/micro_classifier_heads.h
[head-reference-source]: ../../firmware/micro_classifier_heads.c
[native-verifier]: ../../interface/native_verify.py
[native-head-report]: ../../interface/reports/native-heads-20261019.json
[reference-build-audit]: ../../interface/build_audit.py
[reference-build-audit-report]: ../../interface/reports/reference-build-audit-20261019.json
[assembly-api]: ../../firmware/include/micro_classifier_assembly.h
[assembly-source]: ../../firmware/micro_classifier_assembly.c
[assembly-report]: ../../interface/reports/native-assembly-20261019.json
[assembly-build-report]: ../../interface/reports/assembly-build-audit-20261019.json
[baseline-admission-review]: ../../REVIEW.md
[baseline-host-source]: ../../sim/rules.py
[c1-wire-rejection-review]: ../../REVIEW.md
[admission-dynamics-source]: ../../sim/rover.py
[source-command-admission-review]: ../../REVIEW.md
[admission-gap-review]: ../review/171-180.md#176-admission-evidence-gap-mapping-2026-11-06
[owned-event-request-review]: ../review/171-180.md#177-owned-latest-event-request-preparation-2026-11-06
[owned-current-recheck-review]: ../review/171-180.md#178-owned-current-request-rechecking-2026-11-06
[owned-delivery-review]: ../review/171-180.md#179-owned-delivery-integrity-and-qualification-handoff-2026-11-06
[qualification-packet-review]: ../review/171-180.md#180-source-and-consumer-qualification-packet-2026-11-06
[qualification-dynamics]: ../../sim/rover.py
[qualification-consumers]: ../../sim/diagnostics.py
[realized-receipt-review]: ../review/181-182.md#182-opt-in-simulator-realized-motion-receipts-2026-11-09
[simulator-source-read-review]: ../review/183-220.md#183-recorder-reads-from-the-actual-simulator-owner-2026-11-09
[native-motion-source-review]: ../review/183-220.md#184-native-simulator-motion-words-and-emitted-frames-2026-11-09
[native-goal-source-review]: ../review/183-220.md#185-native-goal-producer-words-and-source-pose-2026-11-09
[receipt-clock-review]: ../review/183-220.md#186-diagnostic-monotonic-receipt-windows-2026-11-09
[receipt-retention-review]: ../review/183-220.md#187-producer-owned-receipt-retention-2026-11-09
[receipt-source-pose-review]: ../review/183-220.md#188-opt-in-producer-receipt-and-source-pose-linkage-2026-11-09
[receipt-chain-review]: ../review/183-220.md#189-retained-receipt-segment-chain-consistency-2026-11-09
[receipt-history-review]: ../review/183-220.md#190-bounded-source-linked-receipt-history-2026-11-09
[receipt-pairing-review]: ../review/183-220.md#191-full-retained-source-history-pairing-checks-2026-11-09
[receipt-snapshot-review]: ../review/183-220.md#192-read-time-actual-producer-history-snapshots-2026-11-09
[integration-source-review]: ../review/183-220.md#193-actual-native-integration-source-intermediates-2026-11-09
[integration-ingestion-review]: ../review/183-220.md#194-actual-source-native-integration-cache-ingestion-2026-11-09
[native-integration-snapshot-review]: ../review/183-220.md#195-read-time-actual-native-integration-snapshots-2026-11-09
[native-arithmetic-review]: ../review/183-220.md#196-supported-native-word-arithmetic-discrepancies-2026-11-09
[native-arithmetic-composition-review]: ../review/183-220.md#197-current-owned-native-arithmetic-composition-2026-11-09
[native-arithmetic-record-review]: ../review/183-220.md#198-exact-native-arithmetic-record-validation-2026-11-09
[receipt-clock-consistency-review]: ../review/183-220.md#199-diagnostic-receipt-clock-consistency-2026-11-09
[receipt-clock-order-review]: ../review/183-220.md#200-adjacent-retained-clock-window-ordering-2026-11-09
[native-tof-source-review]: ../review/183-220.md#201-native-tof-input-and-computed-value-retention-2026-11-09
[native-tof-sampling-review]: ../review/183-220.md#202-actual-native-tof-sampling-source-retention-2026-11-09
[native-tof-intake-review]: ../review/183-220.md#203-bounded-fresh-native-tof-source-intake-2026-11-09
[native-tof-retention-review]: ../review/183-220.md#204-recorder-owned-fresh-native-tof-intake-2026-11-09
[native-tof-snapshot-review]: ../review/183-220.md#205-read-time-current-native-tof-source-snapshot-2026-11-09
[native-tof-history-review]: ../review/183-220.md#206-bounded-native-tof-acquisition-history-2026-11-09
[native-tof-delivery-review]: ../review/183-220.md#207-retained-native-tof-delivered-array-correspondence-2026-11-09
[native-tof-delivery-snapshot-review]: ../review/183-220.md#208-current-recorder-native-tof-delivery-snapshot-2026-11-09
[native-tof-companion-frame-review]: ../review/183-220.md#209-native-tof-companion-original-stateframe-correspondence-2026-11-09
[native-tof-pending-review]: ../review/183-220.md#210-retained-native-tof-pending-queue-correspondence-2026-11-09
[native-tof-pending-snapshot-review]: ../review/183-220.md#211-opt-in-current-recorder-native-tof-pending-snapshot-2026-11-09
[native-tof-pending-original-read-review]: ../review/183-220.md#212-original-recorder-read-native-tof-pending-correspondence-2026-11-09
[native-tof-acquisition-clock-review]: ../review/183-220.md#213-opt-in-native-tof-acquisition-clock-windows-2026-11-09
[native-tof-timing-intake-review]: ../review/183-220.md#214-bounded-native-tof-timing-source-intake-2026-11-09
[native-tof-timing-retention-review]: ../review/183-220.md#215-opt-in-recorder-owned-native-tof-timing-retention-2026-11-09
[native-tof-timing-delivery-review]: ../review/183-220.md#216-retained-tof-timing-delivery-correspondence-2026-11-09
[native-tof-floor-residual-review]: ../review/183-220.md#217-bounded-native-tof-floor-division-residuals-2026-11-09
[native-tof-owned-floor-review]: ../review/183-220.md#218-current-source-native-tof-floor-residual-composition-2026-11-09
[native-tof-sampling-review]: ../review/183-220.md#219-ideal-native-tof-sampling-residuals-2026-11-09
[native-tof-owned-sampling-review]: ../review/183-220.md#220-current-source-ideal-tof-sampling-composition-2026-11-09
[native-tof-ray-norm-review]: ../review/221-225.md#221-native-tof-direction-squared-norm-residuals-2026-11-09
[native-tof-owned-norm-review]: ../review/221-225.md#222-current-source-native-tof-ray-norm-composition-2026-11-09
[native-tof-selection-review]: ../review/221-225.md#223-native-tof-minimum-candidate-correspondence-2026-11-09
[native-tof-selection-acquisition-review]: ../review/221-225.md#224-actual-fresh-tof-selection-acquisition-pairing-2026-11-09
[native-tof-selection-intake-review]: ../review/221-225.md#225-bounded-native-tof-selection-intake-2026-11-09
[admission-motion-core-review]: ../../REVIEW.md
[path-cell-review]: ../../REVIEW.md
[path-source-review]: ../../REVIEW.md
[state-motion-review]: ../../REVIEW.md
[history-registration-review]: ../../REVIEW.md
[registered-prefix-review]: ../../REVIEW.md
[path-point-error-review]: ../../REVIEW.md
[command-path-review]: ../../REVIEW.md
[initial-setup-review]: ../../REVIEW.md
[normal-command-map-review]: ../../REVIEW.md
[normal-motion-review]: ../../REVIEW.md
[normal-request-review]: ../../REVIEW.md
[normal-request-binding-review]: ../../REVIEW.md
[normal-request-source-review]: ../../REVIEW.md
[normal-request-path-review]: ../../REVIEW.md
[request-capture-review]: ../../REVIEW.md
[owned-capture-path-review]: ../../REVIEW.md
[capture-reference-pose-review]: ../../REVIEW.md
[checked-pose-path-review]: ../../REVIEW.md
[controlled-arithmetic-review]: ../../REVIEW.md
[controlled-arithmetic-prototype-tests]: ../../tests/test_sim.py
[controlled-arithmetic-dossier-review]: ../../REVIEW.md
[arithmetic-trusted-base-review]: ../../REVIEW.md
[arithmetic-paper-review]: ../../REVIEW.md
[arithmetic-compatibility-review]: ../../REVIEW.md
[controlled-owner-contract-review]: ../../REVIEW.md
[controlled-owner-prototype-review]: ../../REVIEW.md
[controlled-candidate-audit-review]: ../../REVIEW.md
[controlled-candidate-auditor-review]: ../../REVIEW.md
[native-gap-plan-review]: ../../REVIEW.md
[sinc-contract-review]: ../../REVIEW.md
[sinc-prototype-review]: ../../REVIEW.md
[sinc-correctness-review]: ../../REVIEW.md
[sinc-bridge-review]: ../../REVIEW.md
[sinc-path-review]: ../../REVIEW.md
[sinc-route-review]: ../../REVIEW.md
[sinc-cell-review]: ../../REVIEW.md
[sinc-word-review]: ../../REVIEW.md
[sinc-word-proof-review]: ../../REVIEW.md
[sinc-certificate-plan-review]: ../../REVIEW.md
[sinc-cell-check-review]: ../../REVIEW.md
[sinc-checker-paper-review]: ../../REVIEW.md
[sinc-bind-contract-review]: ../../REVIEW.md
[sinc-bind-budget-review]: ../../REVIEW.md
[sinc-bind-implementation-review]: ../../REVIEW.md
[sinc-bind-paper-review]: ../../REVIEW.md
[sinc-composition-contract-review]: ../../REVIEW.md
[sinc-composition-prototype-review]: ../../REVIEW.md
[sinc-composition-paper-review]: ../../REVIEW.md
[sinc-target-contract-review]: ../../REVIEW.md
[sinc-target-prototype-review]: ../../REVIEW.md
[sinc-target-paper-review]: ../../REVIEW.md
[sinc-target-join-review]: ../../REVIEW.md
[sinc-target-join-prototype-review]: ../../REVIEW.md
[sinc-target-join-paper-review]: ../../REVIEW.md
[sinc-join-worksheet-review]: ../../REVIEW.md
[sinc-binding-identity-review]: ../../REVIEW.md
[sinc-compile-comparison-review]: ../../REVIEW.md
[sinc-structural-protocol-review]: ../../REVIEW.md
[c1-motion-source]: ../../sim/rover.py
[c1-prototype-source]: ../../sim/diagnostics.py
[floor-rules]: ../../sim/rules.py
[floor-rules-report]: ../../sim/reports/rules-baseline-20261020.json
[sim-tests]: ../../tests/test_sim.py
[navigation-reference]: ../../sim/navigation.py
[sensor-diagnostics]: ../../sim/diagnostics.py
[sensor-diagnostics-report]: ../../sim/reports/sensor-diagnostics-20261019.json
[readiness-tool]: ../../teacher/readiness.py
[readiness-report]: ../../teacher/reports/readiness-pilot-20261019.json
[simulator-range-source]: ../../sim/rover.py
[provenance-audit]: ../../teacher/provenance.py
[provenance-audit-report]: ../../teacher/reports/provenance-audit-20261016.json
[blind-review-tool]: ../../teacher/review.py
[blind-review-report]: ../../teacher/reports/review-preparation-20261016.json
[priority-reset-review]: ../../REVIEW.md
[architectural-improvement-review]: ../../REVIEW.md
[public-doc-readme]: ../../README.md
[st-family]: https://www.st.com/en/microcontrollers-microprocessors/stm32n6-series.html
[wire-python]: ../../interface/protocol.py
[wire-header]: ../../firmware/include/micro_classifier_protocol.h
[wire-golden]: ../../interface/golden_vectors.json
[m1a-script]: ../../export/m1a.py
[m1a-report]: ../../export/reports/m1a-cpu-20261015.json
[st-compile-script]: ../../export/st_compile.py
[st-cli-401]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-cli.html
[sim-catalogue-draft]: ../../sim/catalogue.json
[sim-label-draft]: ../../sim/labels.py
[sim-label-smoke-report]: ../../sim/reports/label-smoke-20261016.json
[sim-label-coverage-report]: ../../sim/reports/label-coverage-20261016.json
[teacher-label-pipeline]: ../../teacher/label_pipeline.py
[teacher-pipeline-tests]: ../../tests/test_label_pipeline.py
[teacher-evaluation]: ../../teacher/evaluation.py
[synthetic-evaluation-report]: ../../teacher/reports/evaluation-synthetic-20261016.json
[evaluation-tests]: ../../tests/test_evaluation.py
[prompt-budget]: ../../teacher/prompt_budget.py
[prompt-budget-flash]: ../../teacher/reports/prompt-budget-d3-flash-20261016.json
[prompt-budget-mini]: ../../teacher/reports/prompt-budget-d3-mini-20261016.json
[prompt-budget-tests]: ../../tests/test_prompt_budget.py
[row-draft-flash]: ../../teacher/reports/row-draft-budget-d3-flash-20261016.json
[row-draft-mini]: ../../teacher/reports/row-draft-budget-d3-mini-20261016.json
[float32-draft-flash]: ../../teacher/reports/float32-draft-budget-d3-flash-20261016.json
[float32-draft-mini]: ../../teacher/reports/float32-draft-budget-d3-mini-20261016.json
[input-cost-flash]: ../../teacher/reports/input-cost-d3-flash-20261016.json
[input-cost-mini]: ../../teacher/reports/input-cost-d3-mini-20261016.json
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
