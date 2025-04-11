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
import logging
from collections.abc import Sequence
from datetime import datetime

from microservice.exceptions import JobNotCancellableException
from microservice.job_manager import JobManager, JobsAcl, JobSortingField, Pagination, SortDirection, TimestampFilter
from microservice.rest.http_exceptions import (
    BadRequestHTTPException,
    JobNotCancellableHTTPException,
    JobNotFoundHTTPException,
    JobNotPermittedHTTPException,
)
from microservice.rest.job_rest_views import FindJobsQuery, JobRestViews
from model.job_state import JobStateGroup

from geti_spicedb_tools import Permissions, SpiceDB, SpiceDBResourceTypes
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, Singleton

BE_CONTROLLER = logging.DEBUG
IO_CONTROLLER = logging.DEBUG

DEFAULT_N_JOBS_RETURNED = 10
MAX_N_JOBS_RETURNED = 50

logger = logging.getLogger(__name__)


class JobController(metaclass=Singleton):
    """
    Controller for jobs
    """

    def __init__(self) -> None:
        self.job_manager = JobManager()

    @unified_tracing
    def get_jobs(  # noqa: PLR0913
        self,
        user_id: str,
        project_id: ID | None = None,
        state: str | None = None,
        job_types: Sequence[str] | None = None,
        key: str | None = None,
        author_uid: str | None = None,
        start_time_from: datetime | None = None,
        start_time_to: datetime | None = None,
        skip: int | None = None,
        limit: int | None = None,
        sort_by: str | None = None,
        sort_direction: str | None = None,
    ) -> dict:
        """
        Get a REST view of all jobs that matches the given filter parameters.

        :param user_id: the user requesting the jobs
        :param project_id: ID of the project
        :param state: filter on state
        :param job_types: list of job types to filter on
        :param key: filter on job key
        :param author_uid: filter on author
        :param start_time_from: filter jobs that started after the specified time
        :param start_time_to: filter jobs that started before the specified time
        :param skip: number of jobs to skip for pagination
        :param limit: number of jobs to retrieve for pagination
        :param sort_by: Sorting field to sort by
        :param sort_direction: Sorting direction
        :return: REST representation of the retrieved jobs
        :raises: BadRequestException if the specified state is invalid
        """
        start_time_filter = TimestampFilter(from_val=start_time_from, to_val=start_time_to)
        # Make sure pagination attributes are valid
        skip_ = max(skip, 0) if skip is not None else 0
        limit_ = min(max(limit, 1), MAX_N_JOBS_RETURNED) if limit is not None else DEFAULT_N_JOBS_RETURNED
        pagination = Pagination(skip=skip_, limit=limit_)

        if state is not None:
            try:
                state_ = JobStateGroup[state.upper()]
            except KeyError:
                raise BadRequestHTTPException(message=f"The state {state} is not valid")
        else:
            state_ = None

        if sort_by is not None:
            try:
                _sort_by = JobSortingField[sort_by.upper()]
            except KeyError:
                raise BadRequestHTTPException(message=f"Cannot sort on field {sort_by}.")
        else:
            _sort_by = None

        if sort_direction is not None:
            try:
                _sort_direction = SortDirection[sort_direction.upper()]
            except KeyError:
                raise BadRequestHTTPException(message=f"Sort direction {sort_direction} is not valid.")
        else:
            _sort_direction = None

        session = CTX_SESSION_VAR.get()
        view_all_workspace_jobs = SpiceDB().check_permission(
            subject_type=SpiceDBResourceTypes.USER.value,
            subject_id=user_id,
            resource_type=SpiceDBResourceTypes.WORKSPACE.value,
            resource_id=session.workspace_id,
            permission=Permissions.VIEW_ALL_WORKSPACE_JOBS.value,
        )
        permitted_projects = [
            ID(project_id)
            for project_id in SpiceDB().get_user_projects(user_id=user_id, permission=Permissions.VIEW_PROJECT)
        ]
        acl = JobsAcl(
            permitted_projects=permitted_projects, workspace_jobs_author=None if view_all_workspace_jobs else user_id
        )

        count = self.job_manager.get_jobs_count(
            job_types=job_types,
            state_group=state_,
            project_id=project_id,
            key=key,
            author_uid=author_uid,
            start_time=start_time_filter,
            acl=acl,
        )
        jobs = self.job_manager.find(
            job_types=job_types,
            state_group=state_,
            project_id=project_id,
            key=key,
            author_uid=author_uid,
            start_time=start_time_filter,
            pagination=pagination,
            acl=acl,
            sort_by=_sort_by,
            sort_direction=_sort_direction,
        )
        jobs_count = self.job_manager.get_jobs_count_per_state(
            job_types=job_types,
            project_id=project_id,
            author_uid=author_uid,
            start_time=start_time_filter,
            acl=acl,
        )

        find_query = FindJobsQuery(
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            project_id=project_id,
            state_group=state_,
            job_types=job_types,
            key=key,
            author_uid=author_uid,
            start_time_from=start_time_from,
            start_time_to=start_time_to,
            pagination=pagination,
            sort_by=_sort_by,
            sort_direction=_sort_direction,
        )
        return JobRestViews.jobs_to_rest(jobs=jobs, total_count=count, find_query=find_query, jobs_count=jobs_count)

    @unified_tracing
    def get_job(self, user_uid: str, job_id: ID) -> dict:
        """
        Get a specific job by ID as REST representation.

        :param user_uid: the user requesting the jobs
        :param job_id: ID of the job to get
        :return: REST representation of the job
        :raises: JobNotFoundException if the job is not found
        """
        job = self.job_manager.get_by_id(job_id=job_id)
        if job is None:
            raise JobNotFoundHTTPException(job_id=job_id)

        if job.project_id is None:
            if job.author == ID(user_uid):
                return JobRestViews.job_to_rest(job=job)
            view_all_workspace_jobs = SpiceDB().check_permission(
                subject_type=SpiceDBResourceTypes.USER.value,
                subject_id=user_uid,
                resource_type=SpiceDBResourceTypes.WORKSPACE.value,
                resource_id=CTX_SESSION_VAR.get().workspace_id,
                permission=Permissions.VIEW_ALL_WORKSPACE_JOBS.value,
            )
            if view_all_workspace_jobs:
                return JobRestViews.job_to_rest(job=job)
            raise JobNotPermittedHTTPException
        return JobRestViews.job_to_rest(job=job)

    @unified_tracing
    def cancel_job(self, job_id: ID, user_uid: str, delete_job: bool = False) -> str:
        """
        Cancels a specific job by ID.

        :param job_id: ID of the job to cancel
        :param user_uid: UID of the user that cancelled the job
        :param delete_job: If the job should be deleted after cancellation
        :return: REST message acknowledging the cancellation request
        :raises: JobNotFoundException if the job does not exist
        """
        try:
            cancelled = self.job_manager.mark_cancelled(job_id=job_id, user_uid=user_uid, delete_job=delete_job)
        except JobNotCancellableException as ex:
            raise JobNotCancellableHTTPException from ex
        if not cancelled:
            raise JobNotFoundHTTPException(job_id=job_id)
        logger.info(
            f"Job with ID '{job_id}' marked as cancelled {'with deletion flag ' if delete_job else ''}"
            f"by user_id: '{user_uid}'."
        )
        return f"Job with ID '{job_id}' marked as cancelled{' with deletion flag' if delete_job else ''}."
