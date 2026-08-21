# Hugging Face Backend

Optional training backend built on [`transformers`](https://github.com/huggingface/transformers)
and [`accelerate`](https://github.com/huggingface/accelerate). Selected through
the recipe `backend: huggingface` field.

Design document: [`docs/design/huggingface-backend-integration.md`](../../../../docs/design/huggingface-backend-integration.md)

## Installation

```bash
just venv --device xpu       # includes the huggingface extra
# or
uv sync --extra xpu --extra huggingface
```

The backend imports lazily. Environments without the extra continue to use the
`lightning`, `openvino`, and `ultralytics` backends normally.

## Supported tasks

| Task | HF `Auto*` class | ModelAPI `model_type` |
| --- | --- | --- |
| `DETECTION` | `AutoModelForObjectDetection` | `ssd` |
| `INSTANCE_SEGMENTATION` | `AutoModelForUniversalSegmentation` | `DETRInstSeg` |
| `SEMANTIC_SEGMENTATION` | `AutoModelForSemanticSegmentation` | `Segmentation` |
| `MULTI_CLASS_CLS` | `AutoModelForImageClassification` | `Classification` |
| `MULTI_LABEL_CLS` | `AutoModelForImageClassification` | `Classification` |

Keypoint detection is **not** supported: `transformers` ships only SuperPoint,
which is a descriptor extractor rather than a pose estimator. Use the Lightning
backend for that task.

## Design principles

- **One wrapper per task, not per model.** The `transformers` training contract
  is stable within a task, so adding a checkpoint is normally a recipe change
  with no Python.
- **Geti owns all data and augmentation.** The existing Datumaro-backed
  `DataModule`, `VisionDataset`, and CPU/GPU augmentation pipelines are used
  unchanged. The HF image processor is constructed with resizing, rescaling,
  and normalisation **disabled** and is used only for post-processing.
- **Geti owns evaluation.** The existing metric callables are the source of
  truth; no HF metrics are introduced.
- **Export targets the existing ModelAPI contracts.** No new `model_type`
  strings are introduced.

## Implementation status

| Phase | Scope | Status |
| --- | --- | --- |
| 0 | Spike and decision gate | Complete |
| 1 | Backend skeleton and registration | Complete |
| 2 | `HFModel` base and five task classes | Complete |
| 3 | Datumaro adapter and target builders | Complete |
| 4 | `transformers.Trainer` bridge | Complete |
| 5 | Postprocessing and metrics | Complete |
| 6 | Export | Complete |
| 7 | Recipes and configurator | Partial — configurator + recipes done, CLI out of scope |
| 8 | Application integration | Pending |
| 9 | Integration and end-to-end validation | Pending |
| 10 | NNCF INT8 optimization | Pending |

All lifecycle methods (`train()`, `test()`, `predict()`, `export()`,
`from_config()`) are fully implemented. `create_engine()` works with a recipe
path, a bare model name plus `task=`, or an already-built `HFModel` — for
example `create_engine(model="hf_mask2former_swin_t", data="data/wgisd",
task="INSTANCE_SEGMENTATION")`. The CLI (`getitune train/test/... --config`)
is intentionally not wired up for this backend; it is considered outdated and
out of scope.

Real, network-downloading recipes live under `recipe/<task>/hf_*.yaml`
(`hf_rtdetrv2_r18`, `hf_mask2former_swin_t`, `hf_segformer_b0`, `hf_vit_b16`
for both classification tasks). The recipe's `training:` block is parsed
(`Configurator.training`) but not yet auto-applied to `HFEngine.train()` —
training hyperparameters still need to be passed explicitly to `.train()`.
