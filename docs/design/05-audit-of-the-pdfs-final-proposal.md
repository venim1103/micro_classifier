## 5. Audit of the PDF's Final Proposal

The final proposal's teacher-student direction is useful, but its illustrative
code and performance claims are not an implementation baseline.

| Finding | Consequence | Design response |
| --- | --- | --- |
| Labeling code substitutes `torch.randn(..., 5)` for teacher logits | No meaningful teacher supervision | Capture real, schema-aligned Vela distributions |
| Assumes a generic CLS classifier or guessed teacher forward API | Incorrect readout and labeling contract | Start with the documented public decision interface |
| Mixes teacher and student tokenization assumptions | Token IDs do not carry the same meaning | Preprocess the original input independently for each model |
| Padding is not properly masked or handled | Predictions can depend on padding rather than content | Specify and test padding, pooling, length, and missingness behaviour |
| Representation projection is omitted from the optimizer/DDP handling | Alignment parameters do not train or synchronize correctly | Omit alignment initially; include all trainable parameters if later added |
| Fixed five-class head is described as a general decision model | It cannot score arbitrary runtime options | Advertise a bounded task catalogue; option-conditioned models are a later experiment |
| Weight size is treated as proof of deployment | Ignores activations, fallback, runtime, and layout | Require compiler reports, linker checks, and board validation |
| Transformer NPU mapping is assumed | Dynamic attention products require CPU work | Prefer CNN/MLP first; profile any transformer alternative |
| SRAM operation is equated with no external boot storage | SRAM contents disappear after power loss | Separate boot storage from inference placement |
| Softmax is equated with trustworthy confidence | Normalization does not establish calibration | Calibrate deployed outputs and evaluate rejection behaviour |
| Latency, power, training duration, and accuracy are presented as guarantees | No supporting project measurement | Treat these as unknown until measured |

For the shown width-256, three-block student with vocabulary 1,024, 64 positions,
and five output classes, the parameter count depends on the feed-forward width,
which must be re-derived from the PDF's actual code. Recomputed with PyTorch
modules, it is 1.86 million with `dim_feedforward=512`, 2.65 million with 1,024,
and 4.23 million with PyTorch's default of 2,048, in which case the PDF's "four
million" is correct. An all-INT8 raw-parameter estimate is 1.8-4.0 MiB, but
normalization values, biases, quantization metadata, compiler layout, and
activations can add substantial memory. This calculation does not prove fit.

The PDF's 0.08-GOP estimate for a 128-token Vela 0.3B input is also inconsistent
with the approximately 28.2-GOP linear-projection calculation above. Neither
operation count can establish target latency without mapping and measurement.

