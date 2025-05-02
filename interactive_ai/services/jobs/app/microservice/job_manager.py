# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Job manager module
"""

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from pymongo.client_session import ClientSession

from microservice.exceptions import DuplicateJobFoundException, JobNotCancellableException
from microservice.job_repo import SessionBasedMicroserviceJobRepo, WorkspaceBasedMicroserviceJobRepo
from model.duplicate_policy import DuplicatePolicy
from model.job import Job
from model.job_state import JobGpuRequestState, JobState, JobStateGroup
from model.mapper.job_mapper import JobMapper
from model.telemetry import Telemetry

from geti_spicedb_tools import SpiceDB, SpiceDBResourceTypes
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, Singleton
from grpc_interfaces.credit_system.client import CreditSystemClient, ResourceRequest
from iai_core_py.utils.time_utils import now

if TYPE_CHECKING:
    from iai_core_py.repos.base import SessionBasedRepo

logger = logging.getLogger(__name__)


@dataclass
class TimestampFilter:
    """
    Timestamp filter, defines an interval (either closed or open) to look for a timestamp
    """

    from_val: datetime | None
    to_val: datetime | None


@dataclass
class Pagination:
    """
    Result data pagination
    """

    skip: int
    limit: int


class JobSortingField(Enum):
    """
    Enum representing possible job fields available for sorting
    """

    JOB_NAME = auto()
    START_TIME = auto()
    END_TIME = auto()
    CREATION_TIME = auto()
    PRIORITY = auto()


class SortDirection(Enum):
    """
    Enum representing possible sorting directions
    """

    ASC = 1
    DESC = -1


@dataclass()
class JobsCount:
    n_scheduled_jobs: int = 0
    n_running_jobs: int = 0
    n_finished_jobs: int = 0
    n_failed_jobs: int = 0
    n_cancelled_jobs: int = 0


@dataclass()
class JobsAcl:
    """
    Jobs listing ACL (access control list)

    permitted_projects          A list of user permitted projects ID's
                                If None, then no project level authorization is performed
                                If empty, user doesn't have permitted projects
                                If it has data, only jobs belonging to specified projects will be returned
    workspace_jobs_author       author of workspace jobs
                                If None, then no workspace level authorization is performed
                                If it's defined then only user's submitted workspace jobs will be returned
    """

    permitted_projects: Sequence[ID] | None = None
    workspace_jobs_author: str | None = None


class JobManager(metaclass=Singleton):
    """
    Job Manager

    Main entry point for jobs management related operations available in Jobs microservice.
    Operations provided by this module are available to clients through REST or gRPC API and are:
        * submit a job
        * get job by ID
        * mark job cancelled (with or without deletion flag)
        * get jobs count
        * find jobs satisfying filter

    This module contains all the business logic, however since we have manipulations with MongoDB documents as a part
    of business logic, it also has MongoDB dependencies.

    Manages database transactions.
    """

    @staticmethod
    def _normalize_key(key: str) -> str:
        """
        Normalize a key by deserializing it to a dict, sorting its keys in ascending
        order and then serialize it again to string.

        :param key: the key in json string format
        :return: the key in json string format, with its keys sorted in ascending order
        """
        key_dict = json.loads(key)
        sorted_key_dict = dict(sorted(key_dict.items()))
        return json.dumps(sorted_key_dict)

    #################################################################################
    # CRUD Operations                                                               #
    #################################################################################

    def submit(  # noqa: PLR0913
        self,
        job_type: str,
        priority: int,
        job_name: str,
        key: str,
        payload: dict,
        metadata: dict,
        author: ID,
        duplicate_policy: DuplicatePolicy,
        cancellable: bool,
        telemetry: Telemetry | None = None,
        project_id: ID | None = None,
        gpu_num_required: int | None = None,
        cost_requests: dict[str, int] | None = None,
    ) -> ID:
        """
        Submits a new job to storage.

        Job key identifies duplicated jobs.
        There shouldn't be more than one SUBMITTED job having the same key.
        There shouldn't be more than one SCHEDULED or RUNNING job having the same key.

        Duplication checking is performed based on
        the provided duplicate policy and key. The supported duplicate policies are:
            - 'REPLACE': it cancels the previous job and submits a new one
            - 'OMIT': it returns the id of the already running job with the same key

        :param job_type: job type, i.e. "train", "test", etc.
        :param priority: job priority
        :param job_name: job human-readable name
        :param key: job key, which must be a json-serializable string
        :param payload: job payload (all required data for job execution)
        :param metadata: job metadata
        :param author: job author
        :param duplicate_policy: policy to adopt in case of duplicate job
        :param telemetry: telemetry data
        :param project_id: project ID
        :param gpu_num_required: number of GPUs required for job execution
        :param cost_requests: job cost requests in case if credits should be charged for job execution
        :param cancellable: flag, defining if job can be cancelled after startup
        :return submitted job ID
        """
        normalized_key = self._normalize_key(key)
        _telemetry = telemetry if telemetry is not None else Telemetry()
        session = CTX_SESSION_VAR.get()
        document = {
            "workspace_id": session.workspace_id,
            "type": job_type,
            "priority": priority,
            "job_name": job_name,
            "state": JobState.SUBMITTED.value,
            "state_group": JobStateGroup.SCHEDULED.value,
            "cancellation_info": {"is_cancelled": False, "cancellable": cancellable},
            "step_details": [],
            "key": normalized_key,
            "payload": payload,
            "metadata": metadata,
            "creation_time": now(),
            "author": author,
            "executions": {"main": {}},
            "session": session.as_json(),
            "telemetry": {"context": _telemetry.context},
        }
        if project_id is not None:
            document["project_id"] = str(project_id)
        if gpu_num_required is not None:
            document["gpu"] = {"num_required": gpu_num_required, "state": JobGpuRequestState.WAITING.value}

        if cost_requests is not None:
            with CreditSystemClient(metadata_getter=lambda: ()) as client:
                lease_id = client.acquire_lease(
                    organization_id=str(session.organization_id),
                    workspace_id=str(session.workspace_id),
                    project_id=str(project_id) if project_id is not None else None,
                    service_name=job_type,
                    requests=[ResourceRequest(amount=cost_requests[unit], unit=unit) for unit in cost_requests],
                )
                document["cost"] = {
                    "requests": [{"amount": cost_requests[unit], "unit": unit} for unit in cost_requests],
                    "lease_id": lease_id,
                    "consumed": [],
                    "reported": False,
                }

        job_repo = WorkspaceBasedMicroserviceJobRepo()
        with job_repo._mongo_client.start_session() as mongodb_session:
            return self._submit_with_duplicate_checks(
                project_id=project_id,
                job_key=normalized_key,
                document=document,
                duplicate_policy=duplicate_policy,
                mongodb_session=mongodb_session,
            )

    @staticmethod
    def _submit_with_duplicate_checks(
        project_id: ID | None,
        job_key: str,
        document: dict,
        duplicate_policy: DuplicatePolicy,
        mongodb_session: ClientSession,
    ) -> ID:
        """
        Helper function for submitting job document based on duplicated policy.

        :param job_key: normalized job key
        :param duplicate_policy: policy to adopt in case of duplicate job
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :return: the submitted job ID
        """
        job_repo = WorkspaceBasedMicroserviceJobRepo()
        if duplicate_policy == DuplicatePolicy.REPLACE:
            job_repo.update_many(
                job_filter={"key": job_key, "state": JobState.SUBMITTED.value},
                update={
                    "$set": {
                        "cancellation_info.is_cancelled": True,
                        "cancellation_info.delete_job": True,
                    }
                },
                mongodb_session=mongodb_session,
            )
        elif duplicate_policy in (DuplicatePolicy.OMIT, DuplicatePolicy.REJECT):
            duplicate = job_repo.find_one(
                job_filter={
                    "key": job_key,
                    "state": {"$lt": JobState.RUNNING.value},
                },
                mongodb_session=mongodb_session,
            )
            if duplicate is not None and duplicate_policy == DuplicatePolicy.OMIT:
                duplicate_id = ID(duplicate.get("_id"))
                logger.info(f"Duplicate job with ID {duplicate_id} has been found, omitting submitted job")
                return duplicate_id
            if duplicate is not None and duplicate_policy == DuplicatePolicy.REJECT:
                logger.info(f"Duplicate job with ID {duplicate.get('_id')} has been found, rejecting submitted job")
                raise DuplicateJobFoundException
        job_id = job_repo.insert_document(document, mongodb_session=mongodb_session)
        if project_id is not None:
            SpiceDB().create_job(
                job_id=str(job_id),
                parent_entity_type=SpiceDBResourceTypes.PROJECT.value,
                parent_entity_id=str(project_id),
            )
        else:
            workspace_id = CTX_SESSION_VAR.get().workspace_id
            SpiceDB().create_job(
                parent_entity_id=workspace_id,
                parent_entity_type=SpiceDBResourceTypes.WORKSPACE.value,
                job_id=str(job_id),
            )
        return ID(job_id)

    def get_by_id(self, job_id: ID) -> Job | None:
        """
        Returns a job by its ID
        :param job_id: identifier of a job to be returned
        :return found job or None
        """
        job_repo = WorkspaceBasedMicroserviceJobRepo()
        with job_repo._mongo_client.start_session():
            document = job_repo.get_document_by_id(job_id)
            return JobMapper.backward(document) if document is not None else None

    #################################################################################
    # Cancellation                                                                  #
    #################################################################################

    def mark_cancelled(self, job_id: ID, user_uid: str, delete_job: bool = False) -> bool:
        """
        Marks job as cancelled
        :param job_id: identifier of a job to mark
        :param user_uid: uid of the user that cancelled the job
        :param delete_job: If the job should be deleted after cancellation
        :return: True if the job is marked as cancelled, False otherwise
        """
        job_repo = WorkspaceBasedMicroserviceJobRepo()
        with job_repo._mongo_client.start_session():
            job = self.get_by_id(job_id)
            if job is None:
                return False
            if (
                not job.cancellation_info.cancellable
                and JobState.READY_FOR_SCHEDULING.value < job.state.value < JobState.FINISHED.value
            ):
                raise JobNotCancellableException(job_id)
            return job_repo.update(
                job_id=job_id,
                update={
                    "$set": {
                        "cancellation_info.is_cancelled": True,
                        "cancellation_info.user_uid": user_uid,
                        "cancellation_info.request_time": now(),
                        "cancellation_info.delete_job": delete_job,
                    }
                },
            )

    #################################################################################
    # Count & search                                                                #
    #################################################################################

    def get_jobs_count(  # noqa: PLR0913
        self,
        workspace_id: ID | None = None,
        job_types: Sequence[str] | None = None,
        state_group: JobStateGroup | None = None,
        project_id: ID | None = None,
        key: str | None = None,
        author_uid: str | None = None,
        start_time: TimestampFilter | None = None,
        acl: JobsAcl | None = None,
    ) -> int:
        """
        Returns a number of job according to the filter

        :param workspace_id: workspace ID
        :param job_types: list of job types to filter on
        :param state_group: job's state group
        :param project_id: job's project ID
        :param key: job's key
        :param author_uid: job's author UID
        :param start_time: job's start time from/to range
        :param acl: jobs ACL (access control list)
        :return number of jobs found
        """
        normalized_key = self._normalize_key(key) if key else None
        job_filter = self._get_job_filter(
            job_types=job_types,
            state_group=state_group,
            normalized_key=normalized_key,
            acl_filter=self._get_acl_filter(acl=acl),
            author_uid=author_uid,
            start_time=start_time,
            project_id=project_id,
        )
        job_repo: SessionBasedRepo[Job] = (
            SessionBasedMicroserviceJobRepo() if workspace_id is None else WorkspaceBasedMicroserviceJobRepo()
        )
        with job_repo._mongo_client.start_session():
            return job_repo.count(job_filter)

    def get_jobs_count_per_state(
        self,
        job_types: Sequence[str] | None = None,
        project_id: ID | None = None,
        author_uid: str | None = None,
        start_time: TimestampFilter | None = None,
        acl: JobsAcl | None = None,
    ) -> JobsCount:
        """
        Returns a number of jobs for each state.

        :param job_types: list of job types to filter on
        :param project_id: job's project ID
        :param author_uid: job's author UID
        :param start_time: job's start time from/to range
        :param acl: jobs ACL (access control list)
        :return: JobCount object
        """
        job_filter = self._get_job_filter(
            job_types=job_types,
            acl_filter=self._get_acl_filter(acl=acl),
            author_uid=author_uid,
            start_time=start_time,
            project_id=project_id,
        )
        aggr_pipeline = [{"$match": job_filter}] if job_filter else []
        aggr_pipeline.extend(self._build_counts_query())

        job_repo = WorkspaceBasedMicroserviceJobRepo()
        with job_repo._mongo_client.start_session():
            result = next(job_repo.aggregate_read(aggr_pipeline))
            return JobsCount(
                n_scheduled_jobs=result.get("n_scheduled_jobs", 0),
                n_running_jobs=result.get("n_running_jobs", 0),
                n_finished_jobs=result.get("n_finished_jobs", 0),
                n_failed_jobs=result.get("n_failed_jobs", 0),
                n_cancelled_jobs=result.get("n_cancelled_jobs", 0),
            )

    @unified_tracing
    def find(  # noqa: PLR0913
        self,
        job_types: Sequence[str] | None = None,
        states: list[JobState] | None = None,
        state_group: JobStateGroup | None = None,
        project_id: ID | None = None,
        key: str | None = None,
        author_uid: str | None = None,
        start_time: TimestampFilter | None = None,
        acl: JobsAcl | None = None,
        pagination: Pagination | None = None,
        sort_by: JobSortingField | None = None,
        sort_direction: SortDirection | None = None,
    ) -> tuple[Job, ...]:
        """
        Finds jobs according to the filter
        :param job_types: list of job types to filter on
        :param states: job's states to filter
        :param state_group: job's state group, only used if states not specified
        :param project_id: job's project ID
        :param key: job's key
        :param author_uid: job's author UID
        :param start_time: job's start time from/to range
        :param acl: jobs ACL (access control list)
        :param pagination: query pagination
        :param sort_by: Sorting field to sort by
        :param sort_direction: Sorting direction
        :return jobs found
        """
        normalized_key = self._normalize_key(key) if key else None
        job_filter = JobManager._get_job_filter(
            job_types=job_types,
            states=states,
            state_group=state_group,
            acl_filter=self._get_acl_filter(acl=acl),
            normalized_key=normalized_key,
            author_uid=author_uid,
            start_time=start_time,
            project_id=project_id,
        )
        aggr_pipeline: list[dict] = [{"$match": job_filter}]
        _sort_direction = 1 if sort_direction is None else sort_direction.value
        # The order of the sorting fields is important. The primary sorting field should be specified as the first key.
        sorting_fields = {}
        if sort_by is not None:
            sorting_fields[sort_by.name.lower()] = _sort_direction
        sorting_fields["_id"] = _sort_direction
        aggr_pipeline.append({"$sort": sorting_fields})

        if pagination is not None:
            aggr_pipeline.append(
                {"$skip": pagination.skip},
            )
            aggr_pipeline.append(
                {"$limit": pagination.limit},
            )

        job_repo = WorkspaceBasedMicroserviceJobRepo()
        with job_repo._mongo_client.start_session():
            documents = job_repo.aggregate_read(aggr_pipeline)
            return tuple(JobMapper().backward(document) for document in documents)

    @staticmethod
    def _get_job_filter(  # noqa: PLR0913
        job_types: Sequence[str] | None = None,
        states: list[JobState] | None = None,
        state_group: JobStateGroup | None = None,
        acl_filter: dict | None = None,
        normalized_key: str | None = None,
        author_uid: str | None = None,
        start_time: TimestampFilter | None = None,
        project_id: ID | None = None,
    ) -> dict:
        job_filter: dict[Any, Any] = {}
        if job_types is not None and len(job_types) > 0:
            job_filter["type"] = {"$in": list(job_types)}
        if states is not None:
            job_filter["state"] = {"$in": [state.value for state in states]}
        if state_group is not None and states is None:
            job_filter["state_group"] = state_group.value
        if acl_filter is not None:
            job_filter.update(acl_filter)
        if normalized_key is not None:
            job_filter["key"] = normalized_key
        if author_uid is not None:
            job_filter["author"] = author_uid
        if project_id is not None:
            job_filter["project_id"] = str(project_id)
        start_time_filter = JobManager._get_timestamp_filter(start_time)
        if start_time_filter is not None:
            job_filter["start_time"] = start_time_filter
        return job_filter

    @staticmethod
    def _get_timestamp_filter(
        timestamp_filter: TimestampFilter | None = None,
    ) -> dict | None:
        if timestamp_filter is None or (timestamp_filter.from_val is None and timestamp_filter.to_val is None):
            return None
        result = {}
        if timestamp_filter.from_val is not None:
            result["$gte"] = timestamp_filter.from_val
        if timestamp_filter.to_val is not None:
            result["$lte"] = timestamp_filter.to_val
        return result

    @staticmethod
    def _get_acl_filter(acl: JobsAcl | None) -> dict[str, Any] | None:
        """
        Returns a filter query that restricts the jobs that can be accessed based
        on the list of permitted projects to which the job belongs and workspace jobs author.

        :param acl: ACL
        :returns: MongoDB ACL filtering query
        """
        if not acl:
            return None

        project_jobs_filter: dict[str, Any] = {"project_id": {"$exists": True}}
        if acl.permitted_projects is not None:
            project_jobs_filter["project_id"] = {"$in": [str(_id) for _id in acl.permitted_projects]}

        workspace_jobs_filter: dict[str, Any] = {"project_id": {"$exists": False}}
        if acl.workspace_jobs_author is not None:
            workspace_jobs_filter["author"] = acl.workspace_jobs_author

        return {"$or": [project_jobs_filter, workspace_jobs_filter]}

    @staticmethod
    def _build_counts_query() -> list:
        """
        Builds a query for counting jobs for each state.

        :return: aggregate jobs counting query
        """
        facet_stage = {}
        project_stage = {}
        for state in JobStateGroup:
            count_name = f"n_{state.value.lower()}_jobs"
            facet_stage[count_name] = [
                {"$match": {"state_group": state.value}},
                {"$count": "num"},
            ]
            project_stage[count_name] = {"$arrayElemAt": [f"${count_name}.num", 0]}
        return [{"$facet": facet_stage}, {"$project": project_stage}]
