---
name: getitune-training-a-model
description: Train a computer-vision model with the getitune package using its Python API or CLI. Use when a user wants to train, fine-tune, or evaluate a model with `create_engine(...)` and `engine.train()/engine.test()`, run `getitune train`/`getitune test`, choose a model or task, select a device (cpu/gpu/xpu/cuda), warm-start from a checkpoint, or debug a training run. This skill is not for changing getitune source code or recipes.
---

# Training a model with getitune

`getitune` is a low-code transfer-learning library. Training is driven by an
`Engine` created with `create_engine(...)`, which pairs a **model/recipe** with a
**dataset** and returns a runnable engine. The installed package includes recipes
that bundle the model, data pipeline, and training config, so a model name alone
gives a strong baseline.

Use the Python API as the default entry point:

- **Python API** — `from getitune.engine import create_engine`, then
  `engine.train()` / `engine.test()` for notebooks, scripts, and smoke tests.
  Use the CLI when the workflow must be driven entirely from shell commands.

Use Python 3.11-3.14 in a dedicated environment. Before installing, check
`python --version` and `python -m pip show getitune`; if a different version is
present, use a separate environment instead of downgrading it in place.
Installation and pretrained-weight downloads require network access.
Install the pinned package with the extra that matches your hardware:

```bash
python -m pip install "getitune[cpu]==0.4.0" --extra-index-url https://download.pytorch.org/whl/cpu
```

For Intel GPUs, replace `[cpu]` with `[xpu]` and the index suffix `/cpu` with
`/xpu`. For NVIDIA GPUs, use `[cuda]` and `/cu130`. Install only the extra for
the selected hardware; the accelerator wheels also require compatible drivers.
After installation, check the selected accelerator before training:

```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available(), 'XPU:', torch.xpu.is_available())"
```

If the selected accelerator is unavailable, check drivers and the installed
wheel. Offer CPU as an explicit fallback rather than silently changing the
user's device. Missing checkpoints or datasets require user input before a run.

## Python API workflow

```python
from getitune.engine import create_engine

engine = create_engine(
    model="efficientnet_b0",          # model name, recipe .yaml path, or model class
    task="MULTI_CLASS_CLS",           # single-label classification; this model also has a multilabel recipe
    data="/path/to/dataset_root",     # dataset root (COCO/YOLO/VOC/native), auto-detected
    work_dir="./my_workspace",        # checkpoints + logs; defaults to ./getitune-workspace
    device="auto",                    # "auto", "cpu", "gpu", "xpu", "cuda", "0", ...
)
engine.train(max_epochs=50)
engine.test()
```

1. **Pick the model/recipe.** Pass a model name (`"efficientnet_b0"`), a recipe
   path provided by your own package or script, or a model class. If a
   name matches recipes under several tasks, pass the dataset's exact task:
   `MULTI_CLASS_CLS` for single-label or `MULTI_LABEL_CLS` for multilabel
   classification. `CLASSIFICATION` is not a valid task in 0.4.0.
   Use the `getitune-discovering-models`
   skill to list options.
   - Done when: `create_engine(...)` returns without a `ValueError`/`FileNotFoundError`.
2. **Point `data=` at the dataset root.** Format is auto-detected by Datumaro; see
   the `getitune-preparing-datasets` skill.
   - Done when: the engine builds a datamodule without a format/feature error.
3. **Smoke-test the wiring first** with a tiny run (`engine.train(max_epochs=1)`
   or a small subset) before a long run.
   - Done when: one train + one validation pass complete without shape errors.
4. **Train**, overriding hyperparameters as needed
   (`engine.train(max_epochs=50)`).
   - Done when: checkpoints appear under `work_dir`.
5. **Evaluate** with `engine.test()` and confirm the task metric moves, not just
   loss. Record the model + `work_dir` that produced it.

Warm-start from existing weights with
`create_engine(..., checkpoint="/path/to/weights.pt")`.

## CLI workflow

```bash
# 1. Simplest: data only — getitune picks a default model for the task
getitune train --data_root /path/to/dataset

# 2. Choose a model or recipe
getitune train --data_root /path/to/dataset --model yolox_s

# 3. Override hyperparameters
getitune train --data_root /path/to/dataset --model yolox_s \
  --max_epochs 200 --checkpoint /path/to/weights.pt

# 4. Inspect all available training CLI options
getitune train --help -v
```

`getitune test` and `getitune predict` share the same `--model` / `--data_root`
shape. Use `getitune <cmd> --help -v` (and `-vv`) for the full overridable
argument list.

## Choosing a device

- `device="auto"` selects an available accelerator; force with `"cpu"`, `"gpu"`,
  `"xpu"`, `"cuda"`, or an index like `"0"`.
- The device must match the installed extra: `[xpu]` for Intel GPUs or `[cuda]`
  for NVIDIA, using the matching PyTorch index above. Check availability before
  starting a long run; a selected extra alone does not install GPU drivers.

## Debugging a run

- Run one epoch on a small dataset first to isolate construction vs. dataloading
  vs. training failures.
- Shape/feature mismatches usually mean the dataset's labels or task disagree
  with the model — recheck `task=` and the dataset format
  (`getitune-preparing-datasets`).
- Dataset auto-detection failures: confirm the folder matches one supported
  layout (COCO/YOLO/VOC/native).

## Verify

Run a short Python smoke test with `create_engine(...)` +
`engine.train(max_epochs=1)` on a tiny fixture before a long real run. Verify that
the checkpoint is written under `work_dir` and that `engine.test()` produces a
task metric, not only a loss value.

## Related skills

- `getitune-discovering-models` — list models/recipes and disambiguate by task.
- `getitune-preparing-datasets` — the `data=` half of the engine.
- `getitune-exporting-a-model` — export a trained checkpoint to OpenVINO/ONNX.
- `getitune-running-inference` — run predictions with a trained or exported model.
