# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import pytest

from app.execution.common.geti_config_converter import GetiConfigConverter
from app.models.task import TaskType
from app.models.training_configuration.evaluation import ValidationMetric, metrics_for_task


@pytest.mark.parametrize(
    ("task", "exclusive", "expected"),
    [
        (TaskType.CLASSIFICATION, True, ["default", "f1", "accuracy"]),
        (TaskType.CLASSIFICATION, False, ["default", "map", "accuracy"]),
        (TaskType.DETECTION, False, ["default", "map", "map_50"]),
        (TaskType.INSTANCE_SEGMENTATION, False, ["default", "map", "map_50"]),
    ],
)
def test_metrics_for_task(task, exclusive, expected):
    assert metrics_for_task(task, exclusive_labels=exclusive) == expected


@pytest.mark.parametrize("backend", ["lightning", "huggingface", "ultralytics"])
def test_selected_metric_updates_training_monitors(backend):
    converted: dict[str, Any] = {
        "callback_monitor": "val/map",
        "callbacks": [{"init_args": {"monitor": "val/map"}}],
        "model": {"scheduler": {"monitor": "val/map"}},
    }
    config = {
        "sub_task_type": "DETECTION",
        "task_level_parameters": {"evaluation": {"validation_metric": "map_50"}},
    }
    GetiConfigConverter._apply_validation_metric(converted, config, backend)
    if backend == "lightning":
        assert converted["callback_monitor"] == "val/map_50"
        assert converted["callbacks"][0]["init_args"]["monitor"] == "val/map_50"
        assert converted["model"]["scheduler"]["monitor"] == "val/map_50"
    else:
        assert converted["training"]["monitor"] == "val/map_50"


def test_default_preserves_recipe_and_incompatible_metric_is_rejected():
    converted = {"callback_monitor": "val/map_50"}
    config = {"sub_task_type": "DETECTION", "task_level_parameters": {"evaluation": {"validation_metric": "default"}}}
    GetiConfigConverter._apply_validation_metric(converted, config, "lightning")
    assert converted == {"callback_monitor": "val/map_50"}
    config["task_level_parameters"]["evaluation"]["validation_metric"] = ValidationMetric.F1
    with pytest.raises(ValueError, match="not supported"):
        GetiConfigConverter._apply_validation_metric(converted, config, "lightning")
