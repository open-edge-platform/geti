# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Verify default worker counts across every shipped model recipe."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from getitune.backend.huggingface.tools.utils import load_recipe
from getitune.data.module import DataModule
from getitune.types.task import TaskType

RECIPE_ROOT = Path(__file__).resolve().parents[3] / "src" / "getitune" / "recipe"


def _recipes_with_data() -> list[Path]:
    recipes = []
    for path in sorted(RECIPE_ROOT.rglob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        if isinstance(data, dict) and isinstance(data.get("data"), str):
            recipes.append(path)
    return recipes


@pytest.mark.parametrize("recipe_path", _recipes_with_data(), ids=lambda path: str(path.relative_to(RECIPE_ROOT)))
def test_recipe_worker_defaults(recipe_path: Path) -> None:
    config = load_recipe(recipe_path)["data"]
    assert [config[f"{subset}_subset"]["num_workers"] for subset in ("train", "val", "test")] == [2, 2, 1]


@pytest.mark.parametrize("task", list(TaskType))
def test_datamodule_default_subset_workers(task: TaskType) -> None:
    if task not in {
        TaskType.MULTI_CLASS_CLS,
        TaskType.MULTI_LABEL_CLS,
        TaskType.DETECTION,
        TaskType.INSTANCE_SEGMENTATION,
        TaskType.SEMANTIC_SEGMENTATION,
        TaskType.KEYPOINT_DETECTION,
    }:
        pytest.skip("Task has no built-in DataModule recipe")
    datamodule = DataModule.__new__(DataModule)
    datamodule.task = task
    subsets = datamodule.get_default_subset_configs((224, 224))
    assert [subsets[f"{subset}_subset"].num_workers for subset in ("train", "val", "test")] == [2, 2, 1]
