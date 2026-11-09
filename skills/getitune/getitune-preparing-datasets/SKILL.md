---
name: getitune-preparing-datasets
description: Prepare and point datasets at the getitune package for training, testing, and prediction. Use when a user asks which dataset formats are supported, how the `data=` argument of `create_engine(...)` / `--data_root` works, why format auto-detection fails, how to lay out COCO/YOLO/Pascal VOC/Datumaro-native data, how to use a zip archive, or how to pass an Ultralytics YOLO `data.yaml`. This skill is not for changing getitune source code or dataset converters.
---

# Preparing datasets for getitune

When you pass a filesystem path to `data=` (Python API) or `--data_root` (CLI),
`getitune` uses [Datumaro](https://github.com/open-edge-platform/datumaro) to
**auto-detect the dataset format** — you point at the dataset root and the same
call works regardless of the underlying format.

Use Python 3.11-3.14 in a dedicated environment. Check `python --version` and
`python -m pip show getitune` first; use a separate environment if the installed
version differs from 0.4.0. Installation and weight downloads require network
access. Install the package before starting:

```bash
python -m pip install "getitune[cpu]==0.4.0" --extra-index-url https://download.pytorch.org/whl/cpu
```

For Intel GPUs, use `[xpu]` with the index suffix `/xpu`; for NVIDIA GPUs, use
`[cuda]` with `/cu130`. Select one hardware extra and check driver compatibility.
Inspect dataset paths and annotation types before launching training. If a
smoke run uses an accelerator, check `torch.cuda.is_available()` or
`torch.xpu.is_available()` first. For a backend import failure, check the active
environment and matching extra; agree on a CPU fallback to separate device
issues from format errors. Ask for missing data rather than inventing fixtures.

## Supported formats and how they are detected

| Format                | Detected by                                             |
| --------------------- | ------------------------------------------------------- |
| **COCO**              | an `annotations/` directory with COCO JSON files        |
| **YOLO**              | a `data.yaml` file (Ultralytics layout)                 |
| **Pascal VOC**        | `JPEGImages/`, `Annotations/`, `ImageSets/` directories |
| **Datumaro (native)** | `metadata.json` + `data.parquet` at the root            |

- **Zip archives** are accepted too; Datumaro extracts them on import.
- Point `data=` at the **dataset root** — the directory that directly contains
  the marker files/folders above, not a parent of it.

## Workflow

```python
from getitune.engine import create_engine

# Same call for any supported format — just point at the root
engine = create_engine(
    model="yolox_s",
    data="/path/to/dataset_root",
)
engine.train()
```

1. **Lay the dataset out as one supported format** and confirm the marker
   files/folders sit at the root you will pass.
   - Done when: the root matches exactly one row in the table above.
2. **Match the dataset to the task.** A detection dataset needs bounding-box
   annotations; segmentation needs masks; classification needs per-image labels.
   Task and labels must agree with the model you choose in the
   `getitune-training-a-model` skill.
   - Done when: `create_engine(...)` builds a datamodule without a
     feature/label mismatch error.
3. **Smoke-test loading** with a tiny run (`engine.train(max_epochs=1)`) before a
   full run.
   - Done when: one train + one validation batch load without shape errors.

## Ultralytics YOLO datasets

If you train an Ultralytics YOLO model, pass the Ultralytics
[`data.yaml`](https://docs.ultralytics.com/datasets/) file directly as `data=`
(or `--data_root`). Install the optional backend from PyPI with
`python -m pip install "getitune[cpu,ultralytics]==0.4.0" --extra-index-url https://download.pytorch.org/whl/cpu`.
For a GPU, replace the CPU extra and index with the matching pair above while
keeping `ultralytics`.

## Debugging auto-detection

- **Wrong/failed format detection:** the root probably has extra nesting or a
  missing marker. Verify the exact marker files (`annotations/` for COCO,
  `data.yaml` for YOLO, the three VOC dirs, `metadata.json` + `data.parquet` for
  native) are directly under the path you pass.
- **Feature/label mismatch during training:** the dataset's annotation type does
  not match the task — cross-check with `getitune-training-a-model` and pass an
  explicit `task=`.

## Related skills

- `getitune-training-a-model` — consumes the prepared dataset via `data=`.
- `getitune-discovering-models` — pick a model that matches the dataset's task.
