# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines methods and wrappers to work with task progress"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any

from flytekit import current_context
from geti_kafka_tools import publish_event
from geti_types import CTX_SESSION_VAR
from grpc_interfaces.job_update.client import JobUpdateClient
from grpc_interfaces.job_update.pb.job_update_service_pb2 import JobUpdateRequest

from jobs_common.exceptions import TaskErrorMessage
from jobs_common.tasks.utils.secrets import JobMetadata

logger = logging.getLogger(__name__)


@dataclass
class ProgressRange:
    """Class to store a range used for progress reporting"""

    start: int = 0
    end: int = 100


def report_task_step_progress(
    step_index: int,
    steps_count: int,
    step_progress: float | None = None,
    step_message: str | None = None,
) -> None:
    """
    Reports task's step completion percentage and progress message
    Task might consist of multiple steps, i.e. prepare_training_data consists of 4 steps:

    1. Retrieve train data
    2. Create train dataset
    3. Shard dataset (if needed)
    4. Pre-evaluate model (if needed)

    :param step_index: step index (within task's steps), starting from 0
    :param steps_count: total steps count within a task
    :param step_progress: step completion percentage
    :param step_message: step progress message
    """
    progress = round((step_index * 100 + step_progress) / steps_count, 1) if step_progress is not None else None
    report_progress(progress=progress, message=step_message)


def report_progress(
    progress: float | None = None,
    message: str | None = None,
    warning: str | None = None,
) -> None:
    """
    Reports current task completion percentage and progress message
    :param progress: task completion percentage
    :param message: task progress message
    :param warning: task warning
    """
    if progress is None and message is None and warning is None:
        return

    context = current_context()
    execution_id = context.execution_id.name
    task_id = context.task_id.name
    key = f"{execution_id}-{task_id}"
    body: dict = {"execution_id": execution_id, "task_id": task_id}
    if progress is not None:
        body["progress"] = progress
    if message is not None:
        body["message"] = message
    if warning is not None:
        body["warning"] = warning

    logger.debug(f"Reporting {context.execution_id.name} execution's {context.task_id.name} task's progress: {body}")
    publish_event(
        topic="job_step_details",
        body=body,
        key=str(key).encode(),
        headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
    )


def publish_metadata_update(metadata: dict) -> None:
    """
    Send message to add metadata to job.metadata.
    If metadata keys are new they are added to dict, if the keys already exist, the new
    values override the existing values in job metadata

    Careful when calling this function to not overwrite existing metadata unintentionally

    :param metadata: dict of metadata keys and values
    """
    context = current_context()
    execution_id = context.execution_id.name

    logger.debug(f"Task {context.task_id.name} is updating {execution_id} execution's metadata: {metadata}")
    JobUpdateClient(metadata_getter=lambda: CTX_SESSION_VAR.get().as_tuple()).job_update(
        execution_id=execution_id, metadata=metadata
    )


def publish_consumed_resources(amount: int, unit: str, service: str) -> None:
    """
    Send message to report consumed paid resources.

    :param amount: paid resource amount
    :param unit: paid resource unit
    :param service: service, which consumed the resources
    """
    context = current_context()
    execution_id = context.execution_id.name

    logger.debug(
        f"Task {context.task_id.name} of execution {execution_id} publishes consumed resources: {amount} {unit}"
    )
    JobUpdateClient(metadata_getter=lambda: CTX_SESSION_VAR.get().as_tuple()).job_update(
        execution_id=execution_id,
        cost=JobUpdateRequest.Cost(
            consumed=[
                JobUpdateRequest.Cost.Consumed(
                    amount=amount, unit=unit, consuming_date=int(datetime.now().timestamp()), service=service
                )
            ]
        ),
    )


def release_gpu() -> None:
    """
    Send message to release reserved GPU.
    """
    context = current_context()
    execution_id = context.execution_id.name

    logger.debug(f"Task {context.task_id.name} is releasing {execution_id} execution's GPU")
    JobUpdateClient(metadata_getter=lambda: CTX_SESSION_VAR.get().as_tuple()).job_update(
        execution_id=execution_id,
        gpu=JobUpdateRequest.Gpu(action=JobUpdateRequest.Gpu.RELEASE),
    )


def task_progress(
    start_message: str,
    finish_message: str | None,
    failure_message: str,
    start_progress: float = -1,
    finish_progress: float = 100,
) -> Any:
    """
    Decorator to report task start & finish

    :param start_message: message to be shown when task is being started
    :param finish_message: message to be shown when task is being finished
    :param failure_message: message to be shown when task is being failed
    :param start_progress: initial progress value, default is -1 for compatibility with CRD commands
    :param finish_progress: final progress value, default is 100
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> Callable:
            report_progress(progress=start_progress, message=start_message)
            failed = False
            try:
                return fn(*args, **kwargs)
            except Exception as ex:
                failed = True
                message = (
                    ex.message
                    if isinstance(ex, TaskErrorMessage)
                    else (
                        f"{failure_message} (Code: {ex.__class__.__name__}). "
                        "Please retry or contact customer support if problem persists."
                    )
                )
                message += f" (ID: {JobMetadata.from_env_vars().id})"
                report_progress(message=message)
                raise ex
            finally:
                if not failed and finish_message is not None:
                    report_progress(progress=finish_progress, message=finish_message)

        return wrapper

    return decorator
