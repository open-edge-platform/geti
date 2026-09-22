# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
from enum import StrEnum

from pydantic import Field

from .base import BaseEntity
from .label import Label


class TaskType(StrEnum):
    """
    Enumeration of supported machine learning task types.

    Defines the available types of annotation and modeling tasks that can be configured within a project.

    Attributes:
        CLASSIFICATION: Image or object classification task where items are assigned to predefined categories.
        DETECTION: Object detection task that identifies and locates objects within images using bounding boxes.
        INSTANCE_SEGMENTATION: Instance segmentation task that identifies and delineates individual object instances at
            the pixel level.
    """

    CLASSIFICATION = "classification"
    DETECTION = "detection"
    INSTANCE_SEGMENTATION = "instance_segmentation"


class Task(BaseEntity):
    """
    Represents a labeling task configuration within a project.

    A task defines the type of annotation work to be performed, the available labels, and whether labels are
    mutually exclusive (relevant only for classification problem).

    Attributes:
        exclusive_labels: Whether only one label can be assigned per item. Defaults to False, allowing multiple labels.
        task_type: The type of task (e.g., classification, detection, instance_segmentation).
        labels: List of available labels for annotation. Defaults to empty list.
    """

    exclusive_labels: bool = False
    task_type: TaskType
    labels: list[Label] = Field(default_factory=list)

    @property
    def is_multiclass(self) -> bool:
        return self.task_type is TaskType.CLASSIFICATION and self.exclusive_labels

    def validate_trainable(self, labels: Sequence[Label] | None = None) -> None:
        """
        Check that the task has enough labels to be trained on.

        A project may be created and annotated without labels, so this invariant is enforced only where training
        actually starts.

        Args:
            labels: Labels to validate instead of the ones held by this task. Callers that resumed after a delay
                (e.g. a queued training job) should pass the labels currently stored for the project, since this
                task may be a stale snapshot.

        Raises:
            ValueError: If the task has no labels, or fewer than two for multi-class classification.
        """
        effective_labels = self.labels if labels is None else labels
        if not effective_labels:
            raise ValueError("Create at least one label before training.")
        if self.is_multiclass and len(effective_labels) < 2:
            raise ValueError("Multi-class classification requires at least two labels before training.")
