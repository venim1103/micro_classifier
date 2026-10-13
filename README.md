# micro_classifier

Design and feasibility findings: [DESIGN.md](DESIGN.md).

Independent research review of the design: [REVIEW.md](REVIEW.md).

## Teacher tooling

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
