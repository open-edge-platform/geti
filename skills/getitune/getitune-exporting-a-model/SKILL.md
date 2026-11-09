---
name: getitune-exporting-a-model
description: Export a trained getitune model to a deployable format. Use when a user wants to run `engine.export(...)` or `getitune export`, choose between OpenVINO IR and ONNX, set FP32 vs FP16 precision with `ExportFormat` / `Precision`, or validate that exported artifacts load back for inference. This skill is not for training from scratch or post-training quantization.
---

# Exporting a model with getitune

After training, export a model to a deployable format with `engine.export(...)`
(Python API) or `getitune export` (CLI). getitune exports to **OpenVINO IR**
(default) or **ONNX**, each at **FP32** (default) or **FP16** precision. Exported
artifacts load back for inference via the OpenVINO/ONNX path (see the
`getitune-running-inference` skill).

Use Python 3.11-3.14 in a dedicated environment. Check `python --version` and
`python -m pip show getitune` first; use a separate environment if the installed
version differs from 0.4.0. Installation and weight downloads require network
access. Install the package before starting:

```bash
python -m pip install "getitune[cpu]==0.4.0" --extra-index-url https://download.pytorch.org/whl/cpu
```

For Intel GPUs, use `[xpu]` with the index suffix `/xpu`; for NVIDIA GPUs, use
`[cuda]` with `/cu130`. Select one hardware extra and check driver compatibility.
Check device availability with `torch.cuda.is_available()` or
`torch.xpu.is_available()` when exporting from an accelerator-backed engine;
check its drivers and wheel if unavailable, or agree on a CPU fallback.
If export fails at model loading, first rerun `engine.test()` on the trained
model; if that fails, fix the model or checkpoint before diagnosing the export
format.

## Python API workflow

```python
from pathlib import Path

from getitune.engine import create_engine
from getitune.types.export import ExportFormat
from getitune.types.precision import Precision

engine = create_engine(
    model="efficientnet_b0",
    task="MULTI_CLASS_CLS",
    data="/path/to/dataset",
    checkpoint="/path/to/trained_checkpoint.ckpt",
    work_dir="./my_workspace",
)
baseline_metrics = engine.test()

# FP32 OpenVINO IR (default) -> returns the .xml path
ov_ir_path = engine.export()

# FP16 OpenVINO IR
ov_fp16 = engine.export(export_format=ExportFormat.OPENVINO, export_precision=Precision.FP16)
assert Path(ov_fp16).is_file()
assert Path(ov_fp16).with_suffix(".bin").is_file()

# FP32 ONNX
onnx_path = engine.export(export_format=ExportFormat.ONNX)

# FP16 ONNX
onnx_fp16 = engine.export(export_format=ExportFormat.ONNX, export_precision=Precision.FP16)

exported_engine = create_engine(model=ov_fp16, data="/path/to/dataset")
exported_metrics = exported_engine.test()
```

1. **Load the trained checkpoint** with its matching model or recipe (export
   operates on the engine's current model). Ask for the checkpoint and evaluation
   dataset if missing; do not train a new model just to satisfy an export request.
   - Done when: `engine.test()` produces sensible metrics before you export.
2. **Choose format and precision.** Default is FP32 OpenVINO IR. Use
   `export_format=ExportFormat.ONNX` for ONNX; `export_precision=Precision.FP16`
   for FP16 output. Import the enums from `getitune.types.export` and
   `getitune.types.precision`, respectively.
   - Done when: `engine.export(...)` returns a path to the written artifact.
3. **Confirm the artifact exists** under `work_dir` (`.xml` + `.bin` for
   OpenVINO IR, `.onnx` for ONNX).
   - Done when: the returned path exists on disk.
4. **Validate parity** by loading the exported model back and running
   `engine.test()` — accuracy should closely match the trained model (small
   FP16 drift is expected). See `getitune-running-inference`.
   - Done when: exported-model metrics are within tolerance of the trained model.

## CLI workflow

```bash
getitune export --data_root /path/to/dataset --model efficientnet_b0 --task MULTI_CLASS_CLS --checkpoint /path/to/trained_checkpoint.ckpt
# use --help -v for export-format / precision flags
```

## Export/load contract

- Each model provides a tracing path that defines the exported graph. If you
  provide a custom model, keep its input/output contract consistent so export
  parity does not break.
- Exported OpenVINO IR / ONNX models are loaded for inference through the
  OpenVINO backend (`OVEngine`) using
  [ModelAPI](https://github.com/open-edge-platform/model_api).
- Each task also ships an `openvino_model.yaml` recipe for loading a
  pre-exported IR model directly.

## Verify

After export, load the returned artifact with `getitune test` or
`create_engine(...)` and compare its metrics with the trained model.

## Related skills

- `getitune-training-a-model` — produce the checkpoint to export.
- `getitune-running-inference` — load and validate the exported model.
- `getitune-optimizing-a-model` — quantize an exported OpenVINO model to INT8.
