# Geti Library Agent Guide

Component guide for `library/` — the `getitune` Python package (the Geti training
library). Read this together with the repo-wide `../AGENTS.md` and the matching
skill `.agents/skills/geti-library-dev/`.

## What This Component Is

- `getitune` is a low-code transfer-learning computer-vision library.
- It is published to PyPI and consumed by `application/backend/` as an editable
  `uv` source with the `getitune[cpu|xpu|cuda]` extras.
- Python 3.11+, PyTorch, PyTorch Lightning, OpenVINO, Datumaro.

## Package Layout (`src/getitune/`)

| Directory   | Responsibility |
| ----------- | -------------- |
| `backend/`  | Multi-backend implementations: `lightning/` (training), `openvino/` (inference), optional `ultralytics/`. |
| `models/`   | Central re-export hub that exposes model classes from every backend under one namespace. |
| `recipe/`   | YAML recipe configs organized by task (`classification/`, `detection/`, `instance_segmentation/`, `keypoint_detection/`, `rotated_detection/`, `semantic_segmentation/`, shared `_base_/`). |
| `engine/`   | Abstract `Engine` base class defining the `train` / `test` / `predict` / `export` interface. |
| `cli/`      | Command-line entry points (jsonargparse) for `train`, `test`, `predict`, `export`, `benchmark`, `find`. |
| `data/`     | Lightning `DataModule`, dataset factories, augmentation pipelines, samplers. |
| `config/`   | Typed dataclasses for configuration (`device.py`, data, explain, …) plus YAML helpers. |
| `types/`    | Enums and type aliases (`TaskType`, `DeviceType`, `ExportFormat`, `Precision`, …). |
| `tools/`    | `AutoConfigurator` (model → recipe mapping), exporters, explainability tooling. |
| `metrics/`  | Metric callables and evaluation logic. |
| `utils/`    | Shared utilities: recipe discovery (`recipes.py`), device helpers (`device.py`), caching. |
| `benchmark/`| Benchmark manifest parsing and regression runner. |

## Multi-Backend Design

- Compute/framework backends live under `src/getitune/backend/`:
  - `lightning/` — the primary **training** backend (PyTorch Lightning). Holds
    production models (YOLOX, RT-DETR, MaskRCNN, SegNext, EfficientNet,
    MobileNetV3, ViT, …) plus optimizers, schedulers, callbacks, exporters, and
    XPU accelerator/strategy support under `lightning/accelerators/`.
  - `openvino/` — an **inference-only** backend (`OVEngine`, `OVModel`,
    `OVDetectionModel`, …) for deploying exported IR/ONNX models.
  - `ultralytics/` — an **optional** backend (imported behind `try/except`)
    wrapping Ultralytics YOLO models.
- `src/getitune/models/__init__.py` re-exports classes from each backend so
  callers use one import path (`from getitune.models import YOLOX, OVDetectionModel`).
- There is **no explicit model registry**. Models are resolved by fully-qualified
  `class_path` inside recipe YAML and instantiated by jsonargparse.

### Device / accelerator abstraction

- `TaskType` and `DeviceType` enums live in `src/getitune/types/`. Supported
  device types include `auto`, `cpu`, `gpu`, `xpu`, `mps`, and others.
- `DeviceConfig` (`src/getitune/config/device.py`) carries the accelerator and
  device count into the Lightning trainer.
- Device capability checks (e.g. `is_xpu_available()`) live in
  `src/getitune/utils/device.py`.
- **Guard device-specific code with capability checks, never import-time
  failures.** XPU is first-class; do not add hard CUDA-only imports.

## Task Types

Defined in `src/getitune/types/task.py`:

- Classification: `MULTI_CLASS_CLS`, `MULTI_LABEL_CLS`, `H_LABEL_CLS`
- Detection: `DETECTION`, `ROTATED_DETECTION`, `KEYPOINT_DETECTION`
- Segmentation: `INSTANCE_SEGMENTATION`, `SEMANTIC_SEGMENTATION`

Both model implementations (`backend/lightning/models/<task>/`) and recipes
(`recipe/<task>/`) are organized by these task types.

## Recipes

- A recipe is a Lightning-CLI YAML file at
  `src/getitune/recipe/<task>/<model_name>.yaml`.
- Typical sections:
  - `task` — a `TaskType` value.
  - `model` — `class_path` + `init_args` (model name, `label_info`, optimizer,
    scheduler, …).
  - `engine` — device/accelerator.
  - `data` — path to a shared base data config under `recipe/_base_/data/`.
  - `callbacks` and `callback_monitor` — training callbacks and the monitored metric.
  - `overrides` — training hyperparameters (`max_epochs`, `batch_size`, input size).
- Recipes are **self-discovering**: `src/getitune/utils/recipes.py` (`list_models`)
  globs `recipe/**/*.yaml`. Placing a file in the correct task folder is enough —
  there is no registry to update.
- `LightningEngine.from_config()` parses a recipe and instantiates the model,
  datamodule, and callbacks.

## Adding a New Model

1. **Implement the model class** under
   `src/getitune/backend/lightning/models/<task>/`, inheriting the task base
   class (e.g. `LightningDetectionModel`, `LightningMulticlassClsModel`), which
   all derive from `LightningModel` (`backend/lightning/models/base.py`).
   Implement `_create_model(...)` and `forward_for_tracing(...)` (used for export).
2. **Export the class** from the task package `__init__.py` (and optionally the
   root `models/__init__.py`).
3. **Add a recipe** at `recipe/<task>/<model_name>.yaml` pointing `model.class_path`
   at the new class.
4. **No registration is required** — the model appears in
   `list_models(task=...)` and is trainable immediately.
5. Add or update unit tests (`tests/unit/`, mirroring the source tree) and, when
   relevant, model tests (`just test-unit-models`).

## Model Manifests

- The user-facing "model config" is the **recipe** — there is no separate
  per-model manifest file.
- A **benchmark manifest** (`library/benchmark_manifest.yaml`,
  `library/benchmark_catalog.yaml`) drives regression/benchmark runs. It is
  parsed by `src/getitune/benchmark/manifest.py` into dataclasses
  (`BenchmarkManifest`, `TaskSection`, `ModelEntry`, `Scenario`, `CriteriaConfig`)
  and maps model names to recipe paths, datasets, scenarios, and accuracy criteria.
  This manifest is for CI/testing only.

## Engine & CLI

- `Engine` (`src/getitune/engine/engine.py`) is the abstract base with
  `train`, `test`, `predict`, `export`, `is_supported`, and the `from_config`
  factory.
- `LightningEngine` (`backend/lightning/engine.py`) is the main training engine;
  `OVEngine` (`backend/openvino/engine.py`) is inference-only.
- CLI (`src/getitune/cli/cli.py`) exposes `train`, `test`, `predict`, `export`,
  `benchmark`, and `find`, e.g.
  `getitune train --config recipe/detection/yolox_s.yaml --data_root <path>`.

## Commands

Work from `library/`. See `.github/instructions/library.instructions.md` for the
full table.

| Task              | Recipe                              |
| ----------------- | ----------------------------------- |
| Create venv       | `just venv --device cpu\|xpu\|cuda` |
| Refresh lockfile  | `just venv-lock`                    |
| Lint + type-check | `just lint`                         |
| Auto-fix lint     | `just ruff-fix`                     |
| Unit tests        | `just test-unit -- <pytest args>`   |
| Model unit tests  | `just test-unit-models -- <args>`   |
| Integration tests | `just test-integration -- <args>`   |

## Conventions & Guardrails

- Use stdlib `logging` (`logging.getLogger(__name__)`), not `loguru`.
- Prefer `lightning.pytorch` over `pytorch_lightning` imports.
- Modern typing (`list[int]`, `X | None`), `pathlib.Path`, Google-style docstrings.
- Respect the `pyrefly` baseline (`library/pyrefly-baseline.json`) — do not regress.
- Keep the public API stable; `application/backend/` depends on it.
- Do not import from `application/`.
- Tests live in `library/tests/` (`unit/`, `integration/`, `regression/`); reuse
  fixtures under `library/tests/assets/` and do not commit datasets.
