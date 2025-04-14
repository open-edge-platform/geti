# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module holds the TaskTrainReadiness dataclass, that is used to check whether
a task is ready to receive a manual training trigger
"""

from dataclasses import dataclass

from geti_types import ID


@dataclass
class TaskTrainReadiness:
    """
    Holds data regarding the readiness of a task to accept a manual training trigger.

    task_id: ID of the task to which this TaskTrainReadiness status pertains
    total_missing_annotations: Integer representing the number of annotations
        required before training could be triggered
    missing_annotations_per_label: For each label, integer representing the number of annotations required
        before training could be triggered.
    """

    task_id: ID
    total_missing_annotations: int
    missing_annotations_per_label: dict[ID, int]

    @property
    def is_ready(self) -> bool:
        """
        Returns True if the task meets the criteria to accept a manual training
        trigger, False otherwise

        :return: True if task is ready for training, False otherwise
        """
        return self.total_missing_annotations == 0
