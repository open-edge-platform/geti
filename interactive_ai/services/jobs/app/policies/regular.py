# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Methods to prioritize regular (non GPU-bound) jobs
"""

import logging
from typing import Any

from bson import ObjectId

from model.job_state import JobState
from policies.duplicate import get_duplicate_check_sub_pipeline
from policies.job_repo import SessionBasedPolicyJobRepo

logger = logging.getLogger(__name__)


def get_number_of_running_jobs_by_types(types: list[str]) -> int:
    """
    Returns a number of running jobs of specified types
    :param types: job types
    :return int: number of running jobs
    """
    job_repo = SessionBasedPolicyJobRepo()
    with job_repo._mongo_client.start_session():
        aggr_pipeline: list[dict[Any, Any]] = [
            {
                "$match": {
                    "$and": [
                        {"state": {"$gte": JobState.READY_FOR_SCHEDULING.value}},
                        {"state": {"$lt": JobState.FINISHED.value}},
                    ],
                    "type": {"$in": types},
                    "cancellation_info.is_cancelled": False,
                }
            },
            {"$count": "count"},
        ]
        result = job_repo.aggregate_read(aggr_pipeline)
        return sum([item["count"] for item in result])


def get_next_regular_jobs_ids_to_schedule(types: list[str], num_jobs: int) -> list[ObjectId]:
    """
    Returns a list of regular jobs IDs of specified types which can be scheduled
    :param types: jobs types
    :param num_jobs: max number of jobs which can be scheduled
    :return list[ObjectId]: job  IDs
    """
    job_repo = SessionBasedPolicyJobRepo()
    with job_repo._mongo_client.start_session():
        aggr_pipeline: list[dict[Any, Any]] = [
            # Find SUBMITTED and not cancelled jobs
            {
                "$match": {
                    "state": JobState.SUBMITTED.value,
                    "type": {"$in": types},
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
                # Pick only required number of jobs
                {"$limit": num_jobs},
            ]
        )
        result = job_repo.aggregate_read(aggr_pipeline)
        return [ObjectId(item["_id"]) for item in result]


def mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue(
    types: list[str], max_number_of_running_jobs: int
) -> None:
    """
    Choose next regular (non GPU-bound) jobs which can be scheduled for the organization and
    set state to READY_FOR_SCHEDULING for them

    Checks current number of running jobs and max number.
    If policies allow, puts number of jobs in READY_FOR_SCHEDULING state up to max number.

    """
    logger.debug(f"Processing {types} job types")

    number_of_running_jobs = get_number_of_running_jobs_by_types(types=types)
    logger.debug(f"There are already {number_of_running_jobs} jobs running out of {max_number_of_running_jobs}")

    if max_number_of_running_jobs <= number_of_running_jobs:
        return

    num_jobs = max_number_of_running_jobs - number_of_running_jobs
    logger.info(f"Looking for {num_jobs} regular jobs of {types} types to mark as ready for scheduling")
    jobs_ids = get_next_regular_jobs_ids_to_schedule(
        types=types,
        num_jobs=num_jobs,
    )
    logger.info(f"Marking jobs {jobs_ids} as ready for scheduling")
    # We still need to use filtering by state and cancelled flag here to
    # provide atomicity and consistency
    SessionBasedPolicyJobRepo().update_many(
        filter={
            "_id": {"$in": jobs_ids},
            "state": JobState.SUBMITTED.value,
            "cancellation_info.is_cancelled": False,
        },
        update={
            "$set": {
                "state": JobState.READY_FOR_SCHEDULING.value,
            }
        },
    )
