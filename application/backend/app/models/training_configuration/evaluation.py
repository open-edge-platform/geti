# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from enum import StrEnum

from pydantic import BaseModel, Field, PrivateAttr

from app.models.task import TaskType


class ValidationMetric(StrEnum):
    """Available metrics for model evaluation during validation."""

    DEFAULT = "default"  # Auto-select the most appropriate metric based on the task type
    F1 = "f1"
    ACCURACY = "accuracy"
    MAP = "map"
    MAP_50 = "map_50"
    MIOU = "miou"
    DICE = "dice"


def metrics_for_task(task_type: TaskType, *, exclusive_labels: bool = False) -> list[ValidationMetric]:
    """Return metrics computed during validation for an application task."""
    if task_type == TaskType.CLASSIFICATION:
        metrics = (
            [ValidationMetric.F1, ValidationMetric.ACCURACY]
            if exclusive_labels
            else [ValidationMetric.MAP, ValidationMetric.ACCURACY]
        )
    elif task_type in (TaskType.DETECTION, TaskType.INSTANCE_SEGMENTATION):
        metrics = [ValidationMetric.MAP, ValidationMetric.MAP_50]
    else:
        raise ValueError(f"Unsupported task type: {task_type}")
    return [ValidationMetric.DEFAULT, *metrics]


class TaskLevelEvaluationParameters(BaseModel):
    """Evaluation parameters that apply at the task level and are relevant for all models architectures."""

    _allowed_metrics: list[ValidationMetric] = PrivateAttr(default_factory=lambda: [ValidationMetric.DEFAULT])

    @property
    def allowed_metrics(self) -> list[ValidationMetric]:
        return self._allowed_metrics

    validation_metric: ValidationMetric = Field(
        default=ValidationMetric.DEFAULT,
        title="Validation metric",
        description="Metric used to evaluate model performance during validation.",
        json_schema_extra={"allowed_values_from": "allowed_metrics"},
    )
