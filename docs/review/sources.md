# Original Review Source Bibliography

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

Code, design and process review (Update 3):

- [VL53L8CX product page][vl53l8cx-page] and [ULD driver API][vl53l8cx-uld],
  [GCC Arm options][gcc-arm-options], [COBS][cobs], and
  [Learning by Cheating][lbc]

Methods and measurements:

- [EmbBERT][embbert], [pQRNN/PRADO][pqrnn], [Model2Vec][model2vec],
  [Tang et al.][tang]
- STM32N6 studies: [eye tracking][eye-tracking], [CubeSat][cubesat],
  [speech enhancement][speech], [line segments][nplsd], [ARGO][argo],
  [Gideon][gideon], [edge processor review][edge-review]
- Alternatives: [Arm Ethos-U85][ethos-u85], [Alif E4][alif-e4],
  [Alif E8][alif-e8], [NXP i.MX RT700][nxp-rt700]

[lbc]: https://arxiv.org/abs/1912.12294
[vl53l8cx-page]: https://www.st.com/en/imaging-and-photonics-solutions/vl53l8cx.html
[vl53l8cx-uld]: https://github.com/stm32duino/VL53L8CX/blob/main/src/vl53l8cx_api.h
[gcc-arm-options]: https://gcc.gnu.org/onlinedocs/gcc/ARM-Options.html
[cobs]: https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing
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
[chapter-review-00]: 001-041.md
[chapter-review-01]: 042-078.md
[chapter-review-02]: 079-102.md
[chapter-review-03]: 103-122.md
[chapter-review-04]: 123-146.md
[chapter-review-05]: 147-170.md
[chapter-review-06]: 171-180.md
[chapter-review-07]: 181-182.md
[chapter-review-08]: 183-220.md
[chapter-review-09]: 221-225.md
[chapter-review-10]: 226-230.md
[chapter-review-11]: 231-235.md

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
[sim-label-coverage-report]: ../../sim/reports/label-coverage-20261016.json
[input-cost-flash]: ../../teacher/reports/input-cost-d3-flash-20261016.json
[input-cost-mini]: ../../teacher/reports/input-cost-d3-mini-20261016.json
[mini-int8-parity]: ../../teacher/reports/d3-mini-int8-parity-capped-20261016.json
[mini-context-resource]: ../../teacher/reports/d3-mini-context-resource-capped-20261016.json
[mini-context-parity]: ../../teacher/reports/d3-mini-context-parity-capped-20261016.json
[blind-review-tool]: ../../teacher/review.py
[blind-review-report]: ../../teacher/reports/review-preparation-20261016.json
[sensor-diagnostics]: ../../sim/diagnostics.py
[sensor-diagnostics-report]: ../../sim/reports/sensor-diagnostics-20261019.json
[readiness-tool]: ../../teacher/readiness.py
[readiness-report]: ../../teacher/reports/readiness-pilot-20261019.json
[wire-codec-api]: ../../firmware/include/micro_classifier_codec.h
[wire-codec-source]: ../../firmware/micro_classifier_codec.c
[state-history-api]: ../../firmware/include/micro_classifier_history.h
[state-history-source]: ../../firmware/micro_classifier_history.c
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
[review70-rover]: ../../sim/rover.py
[review70-navigation]: ../../sim/navigation.py
[review70-d3]: ../../teacher/d3_int8.py
[lbc]: https://arxiv.org/abs/1912.12294
[vl53l8cx-page]: https://www.st.com/en/imaging-and-photonics-solutions/vl53l8cx.html
[vl53l8cx-uld]: https://github.com/stm32duino/VL53L8CX/blob/main/src/vl53l8cx_api.h
[gcc-arm-options]: https://gcc.gnu.org/onlinedocs/gcc/ARM-Options.html
[cobs]: https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing
[floor-rules]: ../../sim/rules.py
[floor-rules-report]: ../../sim/reports/rules-baseline-20261020.json
[primitive-integrator]: ../../sim/rover.py
[primitive-owner]: ../../sim/diagnostics.py
[primitive-cpython-float]: https://github.com/python/cpython/blob/v3.12.3/Objects/floatobject.c
[primitive-numpy-sinc]: https://github.com/numpy/numpy/blob/v2.2.6/numpy/lib/_function_base_impl.py
[primitive-cpython-math]: https://github.com/python/cpython/blob/v3.12.3/Modules/mathmodule.c
[primitive-python-math-doc]: https://docs.python.org/3.12/library/math.html
[primitive-numpy-sinc-doc]: https://numpy.org/doc/2.2/reference/generated/numpy.sinc.html
[primitive-numpy-asarray-doc]: https://numpy.org/doc/2.2/reference/generated/numpy.asarray.html
[primitive-numpy-promotion-doc]: https://numpy.org/doc/2.2/reference/arrays.promotion.html
[primitive-numpy-scalar]: https://github.com/numpy/numpy/blob/v2.2.6/numpy/_core/src/umath/scalarmath.c.src
[primitive-numpy-arithmetic]: https://github.com/numpy/numpy/blob/v2.2.6/numpy/_core/src/umath/loops_arithm_fp.dispatch.c.src
[primitive-numpy-trig]: https://github.com/numpy/numpy/blob/v2.2.6/numpy/_core/src/umath/loops_trigonometric.dispatch.cpp
[primitive-glibc-errors]: https://sourceware.org/glibc/manual/2.39/html_node/Errors-in-Math-Functions.html
[primitive-glibc-sincos]: https://github.com/bminor/glibc/blob/glibc-2.39/sysdeps/x86_64/fpu/multiarch/s_sin.c
[primitive-glibc-selector]: https://github.com/bminor/glibc/blob/glibc-2.39/sysdeps/x86_64/fpu/multiarch/ifunc-avx-fma4.h
[primitive-ubuntu-python]: https://launchpad.net/ubuntu/+source/python3.12/3.12.3-1ubuntu0.17
[primitive-ubuntu-glibc]: https://launchpad.net/ubuntu/+source/glibc/2.39-0ubuntu8.4
[primitive-protocol-design]: ../../DESIGN.md
[cpython-correspondence-build]: https://launchpad.net/~ubuntu-security-proposed/+archive/ubuntu/ppa/+build/33562858
[cpython-correspondence-changes]: https://launchpadlibrarian.net/875581834/python3.12_3.12.3-1ubuntu0.17_amd64.changes
[cpython-correspondence-buildinfo]: https://launchpadlibrarian.net/875581836/python3.12_3.12.3-1ubuntu0.17_amd64.buildinfo
[cpython-correspondence-applied]: https://git.launchpad.net/ubuntu/+source/python3.12/commit/?id=f641d3123029c88838179c83a972bc2be28e6e60
[cpython-correspondence-series]: https://git.launchpad.net/ubuntu/+source/python3.12/plain/debian/patches/series?h=applied/3.12.3-1ubuntu0.17
[cpython-correspondence-float]: https://git.launchpad.net/ubuntu/+source/python3.12/tree/Objects/floatobject.c?id=f641d3123029c88838179c83a972bc2be28e6e60
[cpython-correspondence-math]: https://git.launchpad.net/ubuntu/+source/python3.12/tree/Modules/mathmodule.c?id=f641d3123029c88838179c83a972bc2be28e6e60
[cpython-correspondence-pymath]: https://git.launchpad.net/ubuntu/+source/python3.12/tree/Include/pymath.h?id=f641d3123029c88838179c83a972bc2be28e6e60
[cpython-correspondence-rules]: https://git.launchpad.net/ubuntu/+source/python3.12/plain/debian/rules?id=f641d3123029c88838179c83a972bc2be28e6e60
[cpython-static-cases]: https://git.launchpad.net/ubuntu/+source/python3.12/tree/Python/generated_cases.c.h?id=f641d3123029c88838179c83a972bc2be28e6e60
[controlled-arithmetic-design]: ../../DESIGN.md
[arithmetic-prototype]: ../../sim/diagnostics.py
[arithmetic-tests]: ../../tests/test_sim.py
[arithmetic-dossier-design]: ../../DESIGN.md
[arithmetic-trusted-design]: ../../DESIGN.md
[arithmetic-paper-design]: ../../DESIGN.md
[scalar-compatibility-tests]: ../../tests/test_sim.py
[controlled-owner-contract-design]: ../../DESIGN.md
[controlled-owner-prototype-design]: ../../DESIGN.md
[controlled-candidate-audit-design]: ../../DESIGN.md
[controlled-auditor-source]: ../../sim/diagnostics.py
[controlled-auditor-tests]: ../../tests/test_sim.py
[native-gap-plan-design]: ../../DESIGN.md
[sinc-contract-design]: ../../DESIGN.md
[sinc-prototype-design]: ../../DESIGN.md
[sinc-correctness-design]: ../../DESIGN.md
[sinc-bridge-design]: ../../DESIGN.md
[sinc-path-design]: ../../DESIGN.md
[sinc-route-design]: ../../DESIGN.md
[sinc-cell-design]: ../../DESIGN.md
[sinc-word-design]: ../../DESIGN.md
[sinc-word-proof-design]: ../../DESIGN.md
[sinc-certificate-plan-design]: ../../DESIGN.md
[sinc-cell-check-design]: ../../DESIGN.md
[sinc-checker-paper-design]: ../../DESIGN.md
[sinc-bind-contract-design]: ../../DESIGN.md
[sinc-bind-budget-design]: ../../DESIGN.md
[sinc-bind-implementation-design]: ../../DESIGN.md
[sinc-bind-paper-design]: ../../DESIGN.md
[sinc-composition-design]: ../../DESIGN.md
[sinc-composition-prototype-design]: ../../DESIGN.md
[sinc-composition-paper-design]: ../../DESIGN.md
[sinc-target-contract-design]: ../../DESIGN.md
[sinc-target-prototype-design]: ../../DESIGN.md
[sinc-target-paper-design]: ../../DESIGN.md
[sinc-target-join-design]: ../../DESIGN.md
[sinc-target-join-prototype-design]: ../../DESIGN.md
[sinc-target-join-paper-design]: ../../DESIGN.md
[sinc-join-worksheet-design]: ../../DESIGN.md
[sinc-binding-identity-design]: ../../DESIGN.md
[sinc-compile-comparison-design]: ../../DESIGN.md
[sinc-structural-protocol-design]: ../../DESIGN.md
[priority-reset-design]: ../../DESIGN.md
[baseline-admission-design]: ../../DESIGN.md
[c1-wire-rejection-source]: ../../sim/diagnostics.py
[concurrent-architecture-review]: 147-170.md#149-standalone-review-removal-2026-11-05
[architecture-validation-source]: 147-170.md#149-standalone-review-removal-2026-11-05
[architecture-prompt-source]: ../../teacher/label_pipeline.py
[architecture-rover-source]: ../../sim/rover.py
[architecture-arm-build]: ../../interface/build_audit.py
[architecture-head-source]: ../../firmware/micro_classifier_heads.c
[architecture-head-tests]: ../../tests/test_interface.py
[architecture-head-audit]: ../../interface/reports/reference-build-audit-20261019.json
[architecture-row-budget]: ../../teacher/reports/float32-draft-budget-d3-mini-20261016.json
[architecture-context-parity]: ../../teacher/reports/d3-mini-context-parity-capped-20261016.json
[architecture-public-readme]: ../../README.md
[architecture-validation-plan]: ../../DESIGN.md
[architecture-sensor-spec]: https://www.st.com/en/imaging-and-photonics-solutions/vl53l8cx.html
[source-command-admission-design]: ../../DESIGN.md
[admission-requirements-design]: ../../DESIGN.md
[discrete-motion-source]: ../../sim/diagnostics.py
[discrete-motion-tests]: ../../tests/test_sim.py
[autonomy-workflow]: ../../AGENTS.md
[path-cell-source]: ../../sim/diagnostics.py
[path-cell-tests]: ../../tests/test_sim.py
[path-source-implementation]: ../../sim/diagnostics.py
[path-source-controls]: ../../tests/test_sim.py
[state-motion-source]: ../../sim/diagnostics.py
[state-motion-controls]: ../../tests/test_sim.py
[history-registration-source]: ../../sim/diagnostics.py
[history-registration-controls]: ../../tests/test_sim.py
[registered-prefix-source]: ../../sim/diagnostics.py
[registered-prefix-controls]: ../../tests/test_sim.py
[path-point-error-source]: ../../sim/diagnostics.py
[path-point-error-controls]: ../../tests/test_sim.py
[command-path-source]: ../../sim/diagnostics.py
[command-path-controls]: ../../tests/test_sim.py
[continuation-workflow]: ../../AGENTS.md#continuation-and-stopping
[admission-dependencies]: ../design/07-data-and-distillation-design-01.md#admission-evidence-dependencies-2026-11-06
[python-monotonic-clock-doc]: https://docs.python.org/3.12/library/time.html#time.monotonic_ns
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
[chapter-review-12]: 236-240.md
[chapter-review-13]: 241-245.md
[chapter-review-14]: 246-250.md
[chapter-review-15]: 251-255.md
[chapter-review-16]: 256-260.md
[chapter-review-17]: 261-265.md
[chapter-review-18]: 266-270.md
[chapter-review-19]: 271-275.md
[chapter-review-20]: 276-280.md
[chapter-review-21]: 281-285.md
[chapter-review-22]: 286-290.md
[chapter-review-23]: 291-295.md
[chapter-review-24]: 296-300.md
[chapter-review-25]: 301-305.md
[chapter-review-26]: 306-310.md
[chapter-review-27]: 311-315.md
[chapter-review-28]: 316-320.md
[chapter-review-29]: 321-325.md
[chapter-review-30]: 326-330.md
[chapter-review-31]: 331-335.md
[chapter-review-32]: 336-340.md
[chapter-review-33]: 341-345.md
[chapter-review-34]: 346-350.md
[chapter-review-35]: 351-355.md
[chapter-review-36]: 356-360.md
[chapter-review-37]: 361-365.md
[chapter-review-38]: 366-370.md
[chapter-review-39]: 371-375.md
[chapter-review-40]: 376-380.md
[chapter-review-41]: 381-385.md
[chapter-review-42]: 386-390.md
[chapter-review-43]: 391-394.md
[chapter-review-44]: 395-396.md
[chapter-review-45]: 397-398.md
[chapter-review-46]: 399-400.md
[chapter-review-47]: 401-402.md
[native-tof-ray-design]: ../design/07-data-and-distillation-design-01.md#native-tof-ray-generation-prerequisites-2026-11-11
[cloud-harness-handoff]: 311-315.md#311-cloud-harness-handoff-and-restart-prompt-2026-11-12
[review-311-315-preserved-0]: 311-315.md#311-cloud-harness-handoff-and-restart-prompt-2026-11-12
[review-311-315-preserved-1]: 311-315.md#312-bounded-native-tof-postprocessing-recorder-retention-2026-11-12
[review-311-315-preserved-2]: 311-315.md#313-bounded-retained-native-tof-postprocessing-matching-2026-11-12
[review-311-315-preserved-3]: 311-315.md#314-closed-native-tof-postprocessing-delivery-publication-2026-11-12
[review-311-315-preserved-4]: 311-315.md#315-supplied-word-native-tof-noise-addition-discrepancies-2026-11-12
[review-316-320-preserved-0]: 316-320.md#316-intact-postprocessing-checkpoint-and-topic-relocation-2026-11-12
[review-316-320-preserved-1]: 316-320.md#317-matched-native-tof-noise-addition-reports-2026-11-12
[review-316-320-preserved-2]: 316-320.md#318-supplied-word-native-tof-dropout-mask-correspondence-2026-11-12
[review-316-320-preserved-3]: 316-320.md#319-matched-native-tof-dropout-reports-2026-11-12
[review-316-320-preserved-4]: 316-320.md#320-supplied-word-native-tof-clipselection-correspondence-2026-11-12
[review-321-325-preserved-0]: 321-325.md#321-matched-native-tof-clipselection-reports-2026-11-12
[review-321-325-preserved-1]: 321-325.md#322-intact-retention-and-delivery-checkpoint-archival-2026-11-12
[review-321-325-preserved-2]: 321-325.md#323-supplied-word-native-tof-selectedstorage-residuals-2026-11-12
[review-321-325-preserved-3]: 321-325.md#324-matched-native-tof-selectedstorage-reports-2026-11-12
[review-321-325-preserved-4]: 321-325.md#325-cold-native-goal-computation-source-2026-11-12
[review-326-330-preserved-0]: 326-330.md#326-native-goal-computation-acquisition-pairing-2026-11-12
[review-326-330-preserved-1]: 326-330.md#327-closed-native-goal-computation-intake-2026-11-12
[review-326-330-preserved-2]: 326-330.md#328-intact-goal-prerequisite-review-archival-2026-11-12
[review-326-330-preserved-3]: 326-330.md#329-typed-bounded-native-goal-computation-history-2026-11-12
[review-326-330-preserved-4]: 326-330.md#330-default-off-native-goal-recorder-retention-2026-11-12
[review-331-335-preserved-0]: 331-335.md#331-exact-retained-native-goal-matching-2026-11-12
[review-331-335-preserved-1]: 331-335.md#332-closed-default-off-native-goal-delivery-2026-11-12
[review-331-335-preserved-2]: 331-335.md#333-supplied-word-native-goal-delta-discrepancies-2026-11-12
[review-331-335-preserved-3]: 331-335.md#334-intact-native-goal-prerequisite-checkpoint-archival-2026-11-12
[review-331-335-preserved-4]: 331-335.md#335-matched-native-goal-delta-reports-wip-and-pause-2026-11-12
[review-336-340-preserved-0]: 336-340.md#336-current-state-review-and-native-goal-boundary-repairs-2026-11-13
[review-336-340-preserved-1]: 336-340.md#337-supplied-word-native-goal-expression-residuals-2026-11-13
[review-336-340-preserved-2]: 336-340.md#338-intact-goal-ownership-checkpoint-archival-2026-11-13
[review-336-340-preserved-3]: 336-340.md#339-matched-retained-native-goal-expression-reports-2026-11-13
[review-336-340-preserved-4]: 336-340.md#340-supplied-native-and-stored-goal-word-correspondence-2026-11-13
[review-341-345-preserved-0]: 341-345.md#341-matched-retained-goal-storage-reports-2026-11-13
[review-341-345-preserved-1]: 341-345.md#342-supplied-pre-integration-speed-update-residuals-2026-11-13
[review-341-345-preserved-2]: 341-345.md#343-supplied-target-and-yaw-clipping-correspondence-2026-11-13
[review-341-345-preserved-3]: 341-345.md#344-intact-goal-delivery-checkpoint-archival-2026-11-13
[review-341-345-preserved-4]: 341-345.md#345-closed-current-receipt-motion-update-reports-2026-11-13
[review-346-350-preserved-0]: 346-350.md#346-supplied-captured-interval-division-residuals-2026-11-13
[review-346-350-preserved-1]: 346-350.md#347-intact-motion-word-contract-relocation-2026-11-13
[review-346-350-preserved-2]: 346-350.md#348-intact-reviewed-goal-expression-checkpoint-archival-2026-11-13
[review-346-350-preserved-3]: 346-350.md#349-closed-current-receipt-interval-reports-2026-11-13
[review-346-350-preserved-4]: 346-350.md#350-supplied-unrounded-segment-count-comparison-2026-11-13
[review-351-355-preserved-0]: 351-355.md#351-closed-current-segment-selection-reports-2026-11-13
[review-351-355-preserved-1]: 351-355.md#352-native-integration-closing-observation-repairs-2026-11-13
[review-351-355-preserved-2]: 351-355.md#353-intact-motion-and-goal-checkpoint-archival-2026-11-13
[review-351-355-preserved-3]: 351-355.md#354-closed-live-receipt-owned-request-joins-2026-11-13
[review-351-355-preserved-4]: 351-355.md#355-checked-remaining-acceptance-blockers-2026-11-13
[review-356-360-preserved-0]: 356-360.md#356-actual-intake-closing-observation-repairs-2026-11-13
[review-356-360-preserved-1]: 356-360.md#357-intact-motion-checkpoint-archival-2026-11-13
[review-356-360-preserved-2]: 356-360.md#358-closed-actual-initial-tick-setup-correspondence-2026-11-13
[review-356-360-preserved-3]: 356-360.md#359-closed-initial-setup-report-consumer-metadata-2026-11-13
[review-356-360-preserved-4]: 356-360.md#360-intact-source-and-consumer-checkpoint-archival-2026-11-13
[review-361-365-preserved-0]: 361-365.md#361-bounded-initial-source-retention-2026-11-13
[review-361-365-preserved-1]: 361-365.md#362-bounded-retained-initial-source-reading-2026-11-16
[review-361-365-preserved-2]: 361-365.md#363-conditional-owned-initial-rest-startup-2026-11-16
[review-361-365-preserved-3]: 361-365.md#364-intact-initial-source-checkpoint-archival-2026-11-16
[review-361-365-preserved-4]: 361-365.md#365-supplied-normalization-division-residuals-2026-11-16
[review-366-370-preserved-0]: 366-370.md#366-closed-current-later-period-comparisons-2026-11-16
[review-366-370-preserved-1]: 366-370.md#367-actual-consumed-normalization-divisor-retention-2026-11-16
[review-366-370-preserved-2]: 366-370.md#368-intact-initial-source-checkpoint-archival-2026-11-16
[review-366-370-preserved-3]: 366-370.md#369-closed-actual-consumed-quotient-joins-2026-11-16
[review-366-370-preserved-4]: 366-370.md#370-actual-heading-shift-and-return-operand-retention-2026-11-16
[review-371-375-preserved-0]: 371-375.md#371-supplied-heading-shift-and-return-residuals-2026-11-16
[review-371-375-preserved-1]: 371-375.md#372-intact-normalization-checkpoint-archival-2026-11-16
[review-371-375-preserved-2]: 371-375.md#373-closed-current-heading-offset-reports-2026-11-16
[review-371-375-preserved-3]: 371-375.md#374-closed-default-native-reader-epoch-identities-2026-11-16
[review-371-375-preserved-4]: 371-375.md#375-closed-owning-receipt-epoch-identities-2026-11-16
[review-376-380-preserved-0]: 376-380.md#376-intact-heading-and-receipt-checkpoint-archival-2026-11-16
[review-376-380-preserved-1]: 376-380.md#377-closed-live-request-consumer-epochs-2026-11-16
[review-376-380-preserved-2]: 376-380.md#378-supplied-heading-remainder-word-residuals-2026-11-16
[review-376-380-preserved-3]: 376-380.md#379-closed-current-heading-remainder-joins-2026-11-16
[review-376-380-preserved-4]: 376-380.md#380-intact-native-word-topic-relocation-2026-11-16
[review-381-385-preserved-0]: 381-385.md#381-intact-consumer-and-remainder-checkpoint-archival-2026-11-16
[review-381-385-preserved-1]: 381-385.md#382-fresh-remaining-evidence-blockers-2026-11-16
[review-381-385-preserved-2]: 381-385.md#383-closed-current-native-tof-source-sampling-2026-11-16
[review-381-385-preserved-3]: 381-385.md#384-closed-native-tof-delivery-report-work-2026-11-17
[review-381-385-preserved-4]: 381-385.md#385-closed-fresh-native-tof-retention-sampling-2026-11-17
[review-386-390-preserved-0]: 386-390.md#386-intact-source-pipeline-checkpoint-archival-2026-11-17
[review-386-390-preserved-1]: 386-390.md#387-closed-native-goal-dynamics-sampling-2026-11-17
[review-386-390-preserved-2]: 386-390.md#388-current-source-queue-evidence-blockers-2026-11-17
[review-386-390-preserved-3]: 386-390.md#389-closed-composed-native-and-receipt-cache-identities-2026-11-17
[review-386-390-preserved-4]: 386-390.md#390-closed-live-request-receipt-cache-identity-2026-11-17
[review-391-394-preserved-0]: 391-394.md#391-closed-conditional-startup-receipt-cache-identity-2026-11-17
[review-391-394-preserved-1]: 391-394.md#392-intact-composed-source-checkpoint-archival-2026-11-17
[review-391-394-preserved-2]: 391-394.md#393-closed-owning-intake-original-and-final-sampling-2026-11-17
[review-391-394-preserved-3]: 391-394.md#394-closed-post-native-receipt-and-pending-copies-2026-11-17
[review-395-396-preserved-0]: 395-396.md#395-intact-owning-intake-checkpoint-archival-2026-11-17
[review-395-396-preserved-1]: 395-396.md#396-closed-native-tof-retention-owner-layouts-2026-11-17
[review-397-398-preserved-0]: 397-398.md#397-intact-retentionlayout-checkpoint-archival-2026-11-17
[review-397-398-preserved-1]: 397-398.md#398-closed-native-tof-snapshot-owner-layouts-2026-11-17
[review-399-400-preserved-0]: 399-400.md#399-intact-snapshot-ownership-checkpoint-archival-2026-11-17
[review-399-400-preserved-1]: 399-400.md#400-fixed-native-tof-owner-frame-extents-2026-11-17
[review-401-402-preserved-0]: 401-402.md#401-intact-frame-boundary-checkpoint-archival-2026-11-17
[review-401-402-preserved-1]: 401-402.md#402-codec-state-prevalidation-before-tof-owner-copying-2026-11-17

[Return to the review reading map][archived-sources-review-map].

[archived-sources-review-map]: ../../REVIEW.md
