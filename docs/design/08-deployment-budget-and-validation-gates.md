## 8. Deployment Budget and Validation Gates

### Proposed Initial Budgets

| Resource | Planning target |
| --- | --- |
| Compiled model constants, including metadata and biases | At most 1 MiB |
| Peak activation/scratch allocation | At most 512 KiB |
| Complete peak internal SRAM use | At most 3 MiB |
| External RAM / external model reads during inference | None for the proposed internal-memory milestone |
| Decision rate and end-to-end latency | Derived per frame: the distance travelled during one decision period plus latency must fit inside the stopping or avoidance margin (a rover at 0.5 m/s and 20 Hz moves 2.5 cm per tick); measured at nominal clocks |
| Energy | To be agreed from the frame's power budget |

The total SRAM gate includes firmware-resident data/code, stacks, preprocessing,
I/O, runtime state, control blobs, initialized model data, and temporary copies.
The difference between total advertised memory and these targets is headroom,
not automatically usable contiguous space in every bank.

These targets can change only through an explicit design decision supported by
task quality and compiler evidence. They are not claims that an untrained
architecture already meets them.

### Acceptance Gates

| Gate | Required evidence |
| --- | --- |
| Export and mapping | Static supported graph; generated reports identify all CPU fallback |
| Internal-memory placement | No external inference pools; compiler allocation agrees with linker reservations |
| Complete memory fit | Peak application memory, stack use, and temporary buffers meet the agreed budget |
| Numerical parity | Golden preprocessing and outputs compared across float host, INT8 host, and target |
| Task quality | Agreed human-ground-truth metrics and per-class/error-cost requirements on a locked test set |
| Distillation benefit | Controlled comparison against supervised-only and simpler non-neural baselines |
| Confidence and rejection | Agreed error/coverage behaviour, including ambiguous and out-of-domain inputs |
| Timing and energy | Board measurements include preprocessing, fallback, probability calculation, and I/O |
| Persistence | Cold boot loads the correct firmware and matching model initializers without a debugger |
| Robustness | Invalid inputs, stale data, unsupported schemas, timeouts, and inference failure follow application policy |
| Interface contract | Malformed, stale, out-of-order, and missing packets are handled as specified; a silent module triggers the host's fail-safe |
| Closed-loop behaviour | Scenario suites in simulation and then in an arena: collisions, rejections, oscillation, and task completion within agreed limits |

Define numerical tolerances and class-change expectations explicitly rather
than assume bit-exactness across backends. ST's
[quantization guide][st-quant] warns that ONNX Runtime on x86-64 with AVX2 or
AVX-512 can saturate in U8S8 kernels, so treat the host INT8 reference as an
approximation and check for saturation before attributing a mismatch to the
NPU. Measure latency distributions and, where the application needs one, a
defensible worst-case deadline. NPU kernel time alone is not end-to-end
decision latency.

ST's NPU and CM55 validation projects target the STM32N6570-DK, so M1b starts
there; its NPU validation example supports
`USE_EXTERNAL_MEMORY_DEVICES=0` for an internal-only development check.
Separately validate the intended production boot flow, including any permitted
external flash, instead of confusing development loading with cold boot.

[st-quant]: https://dev.st.com/edge-ai-docs/st-edge-ai-core/4.0.1/en/docs/user-manual/core-quantization.html
