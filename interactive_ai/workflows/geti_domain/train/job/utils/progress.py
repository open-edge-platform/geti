# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
"""Progress reporting utilities"""

import typing

from jobs_common.tasks.utils.progress import report_task_step_progress


class ModelsIds(typing.NamedTuple):
    """NamedTuple to store model ids"""

    base_model_id: str
    mo_model_id: str


IDX_STEP_TRAIN = 0
STEPS_COUNT = 1


def report_train_progress(progress: float, message: str) -> None:
    """
    Function to report training progress
    """
    report_task_step_progress(
        step_index=IDX_STEP_TRAIN, steps_count=STEPS_COUNT, step_progress=progress, step_message=message
    )
