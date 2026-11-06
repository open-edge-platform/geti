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
If the import or version check fails, reinstall `getitune==0.4.0` in the active
environment.

## List models from Python

```python
from getitune.utils import list_models

list_models()                                # all model names
list_models(return_recipes=True)             # full recipe paths in the package
list_models(task="DETECTION")                # filter by task
list_models(pattern="*efficient*")           # filter by name pattern
list_models(task="DETECTION", return_recipes=True)  # recipe paths for one task
```

Pass any returned name (or recipe path) to
`create_engine(model="...", data="...")` — see `getitune-training-a-model`.

## List models from the CLI

```bash
getitune find                # lists available model recipes
```

## Tasks

Task types live in `getitune.types` (`TaskType`) and organize both the model
implementations and the recipe folders:

- Classification: `MULTI_CLASS_CLS`, `MULTI_LABEL_CLS`, `H_LABEL_CLS`
- Detection: `DETECTION`, `ROTATED_DETECTION`, `KEYPOINT_DETECTION`
- Segmentation: `INSTANCE_SEGMENTATION`, `SEMANTIC_SEGMENTATION`

Recipes whose name ends in `_tile` enable the tiling pipeline for large images.
Each task directory also ships an `openvino_model.yaml` recipe for running
pre-exported OpenVINO IR models.

## Resolving model-name ambiguity

- Passing a **model name** that matches recipes under **multiple tasks** raises a
  `ValueError` listing the matches — pass `task=` to disambiguate
  (e.g. `create_engine(model="dino_v2", task="DETECTION", ...)`).
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
