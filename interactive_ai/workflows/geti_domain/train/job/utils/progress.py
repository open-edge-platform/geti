# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
