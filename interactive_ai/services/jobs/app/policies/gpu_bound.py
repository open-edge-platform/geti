# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
Methods to prioritize GPU-bound jobs
"""

import logging
from typing import Any

from bson import ObjectId

from model.job import Job
from model.job_state import JobGpuRequestState, JobState
from model.mapper.job_mapper import JobMapper
from policies.duplicate import get_duplicate_check_sub_pipeline
from policies.job_repo import SessionBasedPolicyJobRepo

logger = logging.getLogger(__name__)


def get_number_of_reserved_gpus(gpu_jobs_types: list[str]) -> int:
    """
    Returns a number of GPUs already reserved by GPU-bound jobs
    :param gpu_jobs_types: GPU-bound job types
    :return int: number of reserved gpus
    """
    job_repo = SessionBasedPolicyJobRepo()
    with job_repo._mongo_client.start_session():
        aggr_pipeline: list[dict[Any, Any]] = [
            {"$match": {"type": {"$in": gpu_jobs_types}, "gpu.state": JobGpuRequestState.RESERVED.value}},
            {"$project": {"gpu_required": "$gpu.num_required"}},
        ]
        result = job_repo.aggregate_read(aggr_pipeline)
        return sum([item["gpu_required"] for item in result])


def get_submitted_gpu_bound_jobs_without_duplicates(gpu_jobs_types: list[str]) -> tuple[Job, ...]:
    """
    Returns all GPU-bound non-cancelled jobs in SUBMITTED state which do not have running duplicates.
    The resulting jobs list is sorted by priority and creation time.
    :param gpu_jobs_types: GPU-bound job types
    :return tuple[Job, ...]: resulting jobs
    """
    job_repo = SessionBasedPolicyJobRepo()
    with job_repo._mongo_client.start_session():
        aggr_pipeline: list[dict[Any, Any]] = [
            # Find SUBMITTED and not cancelled GPU-bound jobs
            {
                "$match": {
                    "state": JobState.SUBMITTED.value,
                    "type": {"$in": gpu_jobs_types},
                    "cancellation_info.is_cancelled": False,
                }
            },
        ]
        aggr_pipeline.extend(
            # Exclude jobs with running duplicates
            get_duplicate_check_sub_pipeline()
        )
        aggr_pipeline.extend(
            [
                # Sort by priority and creation time
                {"$sort": {"priority": -1, "creation_time": 1}},
            ]
        )
        result = job_repo.aggregate_read(aggr_pipeline)
        return tuple(JobMapper().backward(document) for document in result)


def mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue(
    gpu_jobs_types: list[str], gpu_capacity: list[int]
) -> None:
    """
    Choose next GPU-bound jobs which can be scheduled for the organization,
    set state to READY_FOR_SCHEDULING for them and mark GPU request state as RESERVED

    :param gpu_jobs_types: GPU-bound job types
    :param gpu_capacity: list of executions nodes GPU capacities
    """
    logger.debug("Processing GPU-bound jobs")

    number_of_reserved_gpus = get_number_of_reserved_gpus(gpu_jobs_types=gpu_jobs_types)
    logger.debug(f"There are already {number_of_reserved_gpus} GPUs reserved out of {sum(gpu_capacity)}")

    if sum(gpu_capacity) <= number_of_reserved_gpus:
        return

    # Currently there is no way to calculate GPU reservations per node, therefore we cannot define number of
    # available GPUs per node. That's why here we calculate sum of GPUs instead of considering them
    # separately.
    num_gpus = sum(gpu_capacity) - number_of_reserved_gpus
    logger.info(f"Looking for GPU-bound jobs to mark as ready for scheduling, available GPUs number - {num_gpus}")
    jobs = get_submitted_gpu_bound_jobs_without_duplicates(gpu_jobs_types=gpu_jobs_types)

    jobs_ids: list[ObjectId] = []
    for job in jobs:
        if job.gpu is None or job.gpu.num_required > num_gpus:
            continue
        jobs_ids.append(ObjectId(job.id))
        num_gpus = num_gpus - job.gpu.num_required

    if len(jobs_ids) == 0:
        return

    logger.info(f"Marking GPU-bound jobs {jobs_ids} as ready for scheduling")
    # We still need to use filtering by state and cancelled flag here to
    # provide atomicity and consistency
    SessionBasedPolicyJobRepo().update_many(
        filter={
            "_id": {"$in": jobs_ids},
            "state": JobState.SUBMITTED.value,
            "cancellation_info.is_cancelled": False,
        },
        update={"$set": {"state": JobState.READY_FOR_SCHEDULING.value, "gpu.state": JobGpuRequestState.RESERVED.value}},
    )
