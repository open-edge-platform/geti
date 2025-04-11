# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

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
