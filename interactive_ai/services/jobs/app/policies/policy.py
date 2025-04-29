# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Job prioritizer module
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

from model.job_state import JobState
from policies.gpu_bound import mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue
from policies.job_repo import SessionBasedPolicyJobRepo
from policies.quota import get_organization_job_quota
from policies.regular import mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue
from policies.resource_manager import ResourceManager

from geti_types import CTX_SESSION_VAR, ID, Singleton
from sc_sdk.repos.base.constants import ORGANIZATION_ID_FIELD_NAME, WORKSPACE_ID_FIELD_NAME
from sc_sdk.repos.mappers import IDToMongo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MaxRunningJobsPolicy:
    """
    Policy which specifies that certain job type can have max number of simultaneously running jobs
    """

    limit: int


@dataclass(frozen=True)
class GpuPolicy:
    """
    Policy which specifies that jobs of certain type should be checked against number of available GPU's in the system
    """


@dataclass(frozen=True)
class QuotaPolicy:
    """
    Policy which specifies that jobs of certain type should be checked against organization quota
    """


class Prioritizer(metaclass=Singleton):
    """
    Job prioritizer
    This class provides methods for prioritizing next jobs(s) for further scheduling and execution.
    """

    def __init__(self) -> None:
        """
        Initializes policy manager
        """
        try:
            self.max_jobs_running_per_organization = int(os.environ.get("MAX_JOBS_RUNNING_PER_ORGANIZATION", ""))
        except (TypeError, ValueError):
            raise Exception("Environment variable MAX_JOBS_RUNNING_PER_ORGANIZATION must be properly defined")
        logger.info(f"Default MAX_JOBS_RUNNING_PER_ORGANIZATION is {self.max_jobs_running_per_organization}")

    def get_session_ids_with_submitted_jobs(self) -> dict[ID, ID]:
        """
        Returns ID's of organizations and workspaces which have non-cancelled jobs in SUBMITTED state
        """
        ids = {}
        job_repo = SessionBasedPolicyJobRepo()
        with job_repo._mongo_client.start_session():
            aggr_pipeline: list[dict] = [
                {
                    "$match": {
                        "state": JobState.SUBMITTED.value,
                        "cancellation_info.is_cancelled": False,
                    }
                },
            ]
            documents = job_repo._collection.aggregate(aggr_pipeline, allowDiskUse=True)
            for doc in documents:
                organization_id = IDToMongo.backward(doc[ORGANIZATION_ID_FIELD_NAME])
                workspace_id = IDToMongo.backward(doc[WORKSPACE_ID_FIELD_NAME])
                ids[organization_id] = workspace_id
            return ids

    def mark_next_jobs_as_ready_for_scheduling_from_submitted_queue(self) -> None:
        """
        Marks next batches of both regular and GPU-bound jobs as READY_FOR_SCHEDULING if there is
        a space for execution.
        """
        logger.debug("Marking next jobs as ready for scheduling...")
        job_repo = SessionBasedPolicyJobRepo()
        with job_repo._mongo_client.start_session():
            types = self.get_submitted_job_types()

            gpu_jobs_types: list[str] = []
            quota_jobs_types: list[str] = []
            for type in types:
                policy = self.get_job_type_policy(type=type)
                if isinstance(policy, GpuPolicy):
                    gpu_jobs_types.append(type)
                    continue
                if isinstance(policy, QuotaPolicy):
                    quota_jobs_types.append(type)
                    continue

                mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue(
                    types=[type], max_number_of_running_jobs=policy.limit
                )

            if len(gpu_jobs_types) > 0:
                gpu_capacity = ResourceManager().gpu_capacity
                if gpu_capacity is None:
                    return
                mark_next_gpu_bound_jobs_ids_as_ready_for_scheduling_from_submitted_queue(
                    gpu_jobs_types=gpu_jobs_types, gpu_capacity=gpu_capacity
                )

            if len(quota_jobs_types) > 0:
                organization_id = CTX_SESSION_VAR.get().organization_id
                quota = get_organization_job_quota(organization_id=organization_id)
                mark_next_regular_jobs_as_ready_for_scheduling_from_submitted_queue(
                    types=quota_jobs_types, max_number_of_running_jobs=quota
                )

    def get_submitted_job_types(self) -> set[str]:
        """
        Returns a set of types of all jobs in SUBMITTED state
        :return set[str]: job types set
        """
        job_repo = SessionBasedPolicyJobRepo()
        with job_repo._mongo_client.start_session():
            aggr_pipeline: list[dict[Any, Any]] = [
                # Find SUBMITTED and not cancelled jobs
                {
                    "$match": {
                        "state": JobState.SUBMITTED.value,
                        "cancellation_info.is_cancelled": False,
                    }
                },
                {"$group": {"_id": "$type"}},
            ]
            result = job_repo.aggregate_read(aggr_pipeline)
            return {item["_id"] for item in result}

    def get_job_type_policy(self, type: str) -> MaxRunningJobsPolicy | GpuPolicy | QuotaPolicy:
        """
        Returns a policy for job type, there are three options:
            * MaxRunningJobsPolicy for regular jobs with limit specified
            * GpuPolicy for GPU-bound jobs
            * QuotaPolicy for organization quota based jobs

        Limits are defined via environment variables:

            * MAX_{type.upper()}_JOBS_RUNNING_PER_ORGANIZATION
            * MAX_JOBS_RUNNING_PER_ORGANIZATION

        :param type: job type
        :return MaxRunningJobsPolicy | GpuPolicy | QuotaPolicy: jobs type policy
        """
        max_jobs = os.environ.get(f"MAX_{type.upper()}_JOBS_RUNNING_PER_ORGANIZATION", None)
        match max_jobs:
            case "gpu":
                return GpuPolicy()
            case "quota":
                return QuotaPolicy()
            case _:
                limit = int(max_jobs) if max_jobs is not None else self.max_jobs_running_per_organization
                return MaxRunningJobsPolicy(limit=limit)
