# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Converters between objects and their corresponding REST views
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from microservice.job_manager import JobsCount, JobSortingField, Pagination, SortDirection
from model.job import Job, JobStepDetails
from model.job_state import JobStateGroup

from geti_types import ID


@dataclass(frozen=True)
class FindJobsQuery:
    organization_id: ID
    workspace_id: ID
    pagination: Pagination
    project_id: ID | None = None
    state_group: JobStateGroup | None = None
    job_types: Sequence[str] | None = None
    key: str | None = None
    author_uid: str | None = None
    start_time_from: datetime | None = None
    start_time_to: datetime | None = None
    creation_time_from: datetime | None = None
    creation_time_to: datetime | None = None
    sort_by: JobSortingField | None = None
    sort_direction: SortDirection | None = None


class JobRestViews:
    @staticmethod
    def job_to_rest(job: Job) -> dict:
        """
        Get the REST view of job.

        :param job: Job to convert to REST
        :return: REST view of the job
        """

        rest_job = {
            "id": str(job.id),
            "type": job.type,
            "creation_time": job.creation_time.isoformat(),
            "start_time": job.start_time.isoformat() if job.start_time else None,
            "end_time": job.end_time.isoformat() if job.end_time else None,
            "name": job.job_name,
            "author": job.author,
            "state": job.state_group.name.lower(),
            "steps": JobRestViews.job_progress_to_rest(job.step_details),
            "cancellation_info": {
                "cancellable": job.cancellation_info.cancellable,
                "is_cancelled": job.cancellation_info.is_cancelled,
                "user_uid": job.cancellation_info.user_uid,
                "cancel_time": (
                    job.cancellation_info.cancel_time.isoformat() if job.cancellation_info.cancel_time else None
                ),
            },
            "metadata": {str(key): value for key, value in job.metadata.items()},
        }
        if job.cost is not None:
            rest_job["cost"] = {
                "requests": [{"amount": request.amount, "unit": request.unit} for request in job.cost.requests],
                "consumed": [{"amount": request.amount, "unit": request.unit} for request in job.cost.consumed],
            }
        return rest_job

    @staticmethod
    def jobs_to_rest(
        jobs: Sequence[Job],
        total_count: int,
        find_query: FindJobsQuery,
        jobs_count: JobsCount,
    ) -> dict:
        """
        Get the REST view of a list of jobs.

        :param jobs: Sequence of jobs to convert to REST
        :param total_count: total number of jobs
        :param find_query: query information
        :param jobs_count: object containing count information for each job state
        :return: REST view of the jobs
        """
        jobs_rest_list = [JobRestViews.job_to_rest(job) for job in jobs]
        rest_views = {
            "jobs": jobs_rest_list,
            "jobs_count": {
                "n_scheduled_jobs": jobs_count.n_scheduled_jobs,
                "n_running_jobs": jobs_count.n_running_jobs,
                "n_finished_jobs": jobs_count.n_finished_jobs,
                "n_failed_jobs": jobs_count.n_failed_jobs,
                "n_cancelled_jobs": jobs_count.n_cancelled_jobs,
            },
        }
        offset = len(jobs_rest_list) + find_query.pagination.skip
        if total_count > offset:
            rest_views["next_page"] = JobRestViews._get_next_page_url(offset=offset, find_query=find_query)
        return rest_views

    @staticmethod
    def job_progress_to_rest(job_step_progress: tuple[JobStepDetails, ...]) -> list[dict]:
        """
        Get the REST of a job's progress.

        :param job_step_progress: list of progress objects associated with the job
        :return: REST of representation of the job progress
        """
        rest = []
        for progress in job_step_progress:
            step_rest = {
                "message": progress.message,
                "index": progress.index,
                "progress": progress.progress,
                "state": progress.state.name.lower(),
                "step_name": progress.step_name,
            }
            if progress.start_time is not None and progress.end_time is not None:
                step_rest["duration"] = (progress.end_time - progress.start_time).total_seconds()
            if progress.warning is not None:
                step_rest["warning"] = progress.warning
            rest.append(step_rest)
        return rest

    @staticmethod
    def _get_next_page_url(offset: int, find_query: FindJobsQuery) -> str:
        """
        Builds the next page URL for the get jobs endpoint.

        :param offset: number of items to skip for the next page
        :param find_query: query information
        :return: URL for the next page
        """
        base_url = (
            f"/api/v1/organizations/{str(find_query.organization_id)}/workspaces/{str(find_query.workspace_id)}/jobs"
        )

        # Map query attributes to URL parameters with transformers
        params = [
            ("limit", find_query.pagination.limit, str),
            ("skip", offset, str),
            ("project_id", find_query.project_id, str),
            ("state", find_query.state_group, lambda x: x.name),
            ("key", find_query.key, None),
            ("author_uid", find_query.author_uid, None),
            ("start_time_from", find_query.start_time_from, lambda x: x.isoformat()),
            ("start_time_to", find_query.start_time_to, lambda x: x.isoformat()),
            ("creation_time_from", find_query.creation_time_from, lambda x: x.isoformat()),
            ("creation_time_to", find_query.creation_time_to, lambda x: x.isoformat()),
            ("sort_by", find_query.sort_by, lambda x: x.name),
            ("sort_direction", find_query.sort_direction, lambda x: x.name),
        ]

        # Build query parameters
        query_params = []
        for param_name, value, transformer in params:
            if value is not None:
                transformed_value = transformer(value) if transformer else value
                query_params.append(f"{param_name}={transformed_value}")

        # Handle job_types separately as it's a sequence
        for job_type in find_query.job_types or []:
            query_params.append(f"job_type={job_type}")

        # Combine URL with query parameters
        return f"{base_url}?{'&'.join(query_params)}"
