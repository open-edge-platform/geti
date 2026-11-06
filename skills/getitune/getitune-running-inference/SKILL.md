---
name: getitune-running-inference
description: Run inference and evaluation with a getitune model. Use when a user wants to call `engine.predict()` / `engine.test()` or `getitune predict` / `getitune test`, run inference with a PyTorch checkpoint versus an exported OpenVINO IR (`.xml`) or ONNX (`.onnx`) model, or compare backend results. This skill is not for training, exporting, or changing getitune source code.
---

# Running inference with getitune

`getitune` runs inference through `engine.predict()` (per-item predictions) and
`engine.test()` (metrics on the test subset). The same calls work whether the
engine holds a **PyTorch** model or an **exported** OpenVINO/ONNX model — the
backend is selected from what you pass to `model=`.

Install the package before starting:

```bash
python -m pip install "getitune[cpu]==0.4.0" --extra-index-url https://download.pytorch.org/whl/cpu
```

For Intel GPUs, use `[xpu]` with the index suffix `/xpu`; for NVIDIA GPUs, use
`[cuda]` with `/cu130`. Select one hardware extra and check driver compatibility.
Confirm the installed version and device before inference. If the exported
model cannot load, check the matching `.bin` file for OpenVINO XML or use the
original checkpoint to distinguish an artifact problem from a dataset problem.

## PyTorch inference (trained model)

```python
from getitune.engine import create_engine

engine = create_engine(
    model="efficientnet_b0",
    data="/path/to/dataset",
)
test_metrics = engine.test()      # metrics on the test subset
predictions = engine.predict()    # predictions on the test subset
```

## OpenVINO / ONNX inference (exported model)

```python
from getitune.engine import create_engine

# OpenVINO IR — pass the .xml
ov_engine = create_engine(model="/path/to/exported_model.xml", data="/path/to/dataset")
ov_engine.test()
ov_engine.predict()

# ONNX — pass the .onnx
onnx_engine = create_engine(model="/path/to/exported_model.onnx", data="/path/to/dataset")
onnx_engine.test()
onnx_engine.predict()
```

Passing an `.xml` or `.onnx` path builds an `OVEngine`, which loads the model via
[ModelAPI](https://github.com/open-edge-platform/model_api).

## Workflow

1. **Pick the model surface.** Use a model name/checkpoint for PyTorch inference,
   or an exported `.xml`/`.onnx` for deployed inference.
   - Done when: `create_engine(...)` returns the expected engine type.
2. **Point `data=` at a dataset with a test subset** (see
   `getitune-preparing-datasets`).
   - Done when: `engine.test()` runs without a data/format error.
3. **Run `test()` for metrics or `predict()` for per-item outputs.**
   - Done when: metrics are produced, or predictions are returned for each item.
4. **Compare backends when validating an export.** PyTorch vs OpenVINO/ONNX
   metrics should closely match (small numeric drift is expected).
   - Done when: exported-model metrics are within tolerance of the PyTorch model.

## CLI

```bash
getitune predict --data_root /path/to/dataset --model efficientnet_b0
getitune test    --data_root /path/to/dataset --model /path/to/exported_model.xml
```

## Related skills

- `getitune-exporting-a-model` — produce the `.xml`/`.onnx` used here.
- `getitune-optimizing-a-model` — run inference with an INT8 quantized model.
- `getitune-preparing-datasets` — the `data=` half of inference.
