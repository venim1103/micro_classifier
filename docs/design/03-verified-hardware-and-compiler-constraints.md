## 3. Verified Hardware and Compiler Constraints

### STM32N6

The [STM32N6 family][st-family] includes Cortex-M55 devices with Helium/MVE.
N6x7 variants include Neural-ART; N6x5 variants do not. The
[STM32N657][st-n657] offers a CPU up to 800 MHz, an NPU up to 1 GHz, and
advertised NPU performance around 600 GOPS. Peak throughput is not an
application latency guarantee. Those clocks need overdrive (VDDCORE 0.9 V);
nominal clocks are 600 MHz for the CPU and 800 MHz for the NPU
([ST project guide][st-projects]). Budget latency and energy at nominal clocks
and measure overdrive separately. In ST's recommended asynchronous runtime mode
the core waits in `WFE`, so the NPU, NPU RAMs, and every memory the model uses
must stay clocked in low-power modes.

ST advertises approximately 4.2 MB of contiguous embedded SRAM, organized in
banks. Firmware, stacks, input/output buffers, model constants, activations,
runtime objects, and compiler-generated control data compete for memory. Bank
accessibility, alignment, bandwidth, and security configuration also matter.

STM32N6 has no internal user flash. As described in ST's
[boot example][st-boot], SRAM-loaded development operation is temporary.
Standalone cold boot needs persistent storage or an external loader. Therefore:

- Internal-SRAM inference can avoid external RAM and external weight reads
  during inference.
- External flash may still store firmware and model initializers for boot.
- A debugger-loaded SRAM demo is not proof of a standalone product.
- If all external persistent storage is forbidden, the boot/loading requirement
  must be resolved separately; volatile SRAM cannot retain the application.

### Neural-ART Mapping

The [ST Edge AI Core 4.0.1 operator documentation][st-operators] describes
static input/output shapes and efficient INT8 weights plus INT8 activations.
Supported formats include tensor-oriented ONNX QDQ and fully integer TFLite.
The documented quantization scheme uses symmetric signed weights, asymmetric
signed activations, per-channel weight scales, and per-tensor activation scales.

| Operation or feature | Deployment implication |
| --- | --- |
| Quantized convolution and dense layers with constant weights | Strong initial building blocks |
| Quantized ReLU and supported pooling | Suitable subject to shape/window constraints |
| `MatMul` / `BATCH_MATMUL` | Hardware mapping requires a constant second input |
| Attention score and value products | Variable operands require software fallback, if available |
| Embedding lookup / `Gather` | Software integer mapping |
| Floating-point operations | CPU execution rather than direct NPU execution |
| Dynamic shapes or weight-only quantization | Not the intended efficient deployment path |
| ONNX importer accepts an operator | Does not establish NPU acceleration |

An unsupported hardware operator may use a CPU implementation or cause
compilation failure. Inspect the generated mapping and actual target profiling;
do not assume all fallback paths are available or inexpensive.

The compiler's pooling, broadcasting, kernel, and feature-width constraints
must inform model layout. Even supported operations can be decomposed into
multiple epochs and perform differently from their nominal operation count.

For 1-D text, the documented efficiency rules are concrete: kernels up to 6
wide (stride 1) and 3 high; kernels with a dimension of 1 run efficiently; for
INT8, feature width times input channels should stay at or below 2,048 or the
compiler splits the work, and pooling line buffers share that limit; MaxPool
windows above 3 are decomposed; prime channel counts should be avoided. A
`[1, C, 1, T]` layout with 1x3 kernels exceeds the limit at T = 128 and
C = 128, whereas `[1, C, T, 1]` with 3x1 kernels keeps the width at 1. Compile
both and compare epochs and estimated cycles (§12, M1a).

### Memory Placement and Initialization

The [Neural-ART compiler][st-compiler] provides an
`internal-memories-only--default` profile. Default profiles can permit external
flash and RAM, so default compilation does not prove the proposed constraint.

ST's default memory-pool example splits internal SRAM as follows:

| Region | Size | Use in ST's example |
| --- | --- | --- |
| FLEXMEM and AXISRAM1 | 400 KiB + 624 KiB | Firmware |
| AXISRAM2 | 1,024 KiB | NPU pool |
| AXISRAM3-6 | 4 x 448 KiB | NPU pools, fastest for the NPU |

That leaves about 2.75 MiB for inference and 1 MiB for firmware, enough for the
budgets in §8. For a sub-million-parameter student, memory is not the binding
constraint; task quality is.

The following is documented prospective syntax, not a command already run:

```sh
stedgeai generate -m student_int8.onnx --target stm32n6 \
  --st-neural-art profile-internal-memories-only--default
```

The final application needs a memory-pool configuration and linker layout with
disjoint firmware and inference regions. Check all generated initializers and
control blobs, not only the activation allocation. The `--st-neural-art` option
is essential to select the NPU compilation path rather than M55-only code.

ST's [initializer documentation][st-initializers] makes the application
responsible for copying/loading SRAM-resident weights before inference.
Memory must be enabled and clocked before initialization. Startup loading,
cache maintenance, NPU permissions, RIF/RISAF configuration, and reserved memory
ranges are part of the design, not incidental firmware details.

Use the generated bindings and matching LL_ATON/STAI runtime from one pinned
tool delivery. Do not transplant the PDF's legacy `ai_network_run` example or
handwritten activation allocation into an NPU deployment without validating
the generated contract.

There is no documented host NPU emulator that replaces numerical validation of
the generated implementation on a physical board. The
[NPU validation project][st-projects] and AiRunner provide an appropriate
starting point. The supplied CM55 validation example assumes external-flash
weights and is not a ready-made internal-SRAM CPU comparison.

[st-family]: https://www.st.com/en/microcontrollers-microprocessors/stm32n6-series.html
[st-n657]: https://www.st.com/en/microcontrollers-microprocessors/stm32n657a0.html
[st-boot]: https://github.com/STMicroelectronics/STM32N6-GettingStarted-ImageClassification#boot-modes
[st-operators]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-operators.html
[st-compiler]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-compiler.html
[st-initializers]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-memory-initializers.html
[st-projects]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-neural-art-stm32n6-projects.html
