---
name: getitune-discovering-models
description: Discover which models, recipes, and tasks the getitune package supports before training. Use when a user asks what models are available, how to list recipes, how to filter by task or name pattern, how `list_models(...)` and `getitune find` behave, or how to resolve the "model name matches multiple tasks" error. This skill is not for changing getitune source code or adding recipes.
---

# Discovering models and recipes in getitune

Every trainable model in `getitune` is backed by a **recipe** included in the
installed package. Recipes are self-discovering, so listing them is how you
learn what you can train and what to pass to `create_engine`.

Before running a workflow, confirm the installed version with
`python -c "from importlib.metadata import version; print(version('getitune'))"`.
These examples target Python 3.11-3.14 and `getitune==0.4.0`. Check
`python --version` too. If the package is missing, install into a dedicated
environment; installation requires network access:

```bash
python -m pip install "getitune[cpu]==0.4.0" --extra-index-url https://download.pytorch.org/whl/cpu
```

If a different version is already installed, report the mismatch and use an
isolated environment for the pinned examples rather than downgrading the user's
working environment. Model discovery does not require selecting an accelerator.

## List models from Python

```python
from getitune.utils import list_models

list_models()                                # all model names
list_models(return_recipes=True)             # full recipe paths in the package
list_models(task="DETECTION")                # filter by task
list_models(pattern="*efficient*")           # filter by name pattern
list_models(task="DETECTION", return_recipes=True)  # recipe paths for one task
```

To display names alongside paths, derive each name from its recipe; the
name list is deduplicated and is not ordered to match the recipe list:

```python
from pathlib import Path

for recipe in list_models(task="DETECTION", return_recipes=True):
    print(Path(recipe).stem, recipe)
```

Pass a returned name with its task (or an unambiguous recipe path) to an engine.
The factory is exported from `getitune.engine`, not the package root:

```python
from getitune.engine import create_engine

engine = create_engine(model="dino_v2", task="MULTI_CLASS_CLS", data="./dataset")
```

## List models from the CLI

```bash
getitune find                # lists available model recipes
```

## Tasks

Task types live in `getitune.types` (`TaskType`) and organize both the model
implementations and the recipe folders:

- Classification: `MULTI_CLASS_CLS`, `MULTI_LABEL_CLS`
- Detection: `DETECTION`, `KEYPOINT_DETECTION`
- Segmentation: `INSTANCE_SEGMENTATION`, `SEMANTIC_SEGMENTATION`

Recipes whose name ends in `_tile` enable the tiling pipeline for large images.
Each task directory also ships an `openvino_model.yaml` recipe for running
pre-exported OpenVINO IR models.

## Resolving model-name ambiguity

- Passing a **model name** that matches recipes under **multiple tasks** raises a
  `ValueError` listing the matches — pass `task=` to disambiguate
  (e.g. `create_engine(model="dino_v2", task="MULTI_CLASS_CLS", ...)`).
- Passing a **recipe path** (`.yaml`/`.yml`) that does not exist raises
  `FileNotFoundError`.
- Use `list_models(task="...", return_recipes=True)` to get unambiguous full
  recipe paths.

## Workflow

1. **List candidates**, filtering by `task=` and/or `pattern=` to narrow down.
   - Done when: you have a concrete model name or recipe path.
2. **Confirm the task matches your dataset** (see `getitune-preparing-datasets`).
   - Done when: model task and dataset annotations agree.
3. **Hand the chosen model to `create_engine`** in `getitune-training-a-model`.

## Related skills

- `getitune-training-a-model` — train the model you selected.
- `getitune-preparing-datasets` — match the model's task to your data.
