# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Job endpoints
"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from microservice.rest.job_controller import JobController

from geti_fastapi_tools.dependencies import get_user_id_fastapi, setup_session_fastapi
from geti_types import ID

router = APIRouter(prefix="/api/v1", tags=["Jobs"], dependencies=[Depends(setup_session_fastapi)])
logger = logging.getLogger(__name__)


@router.get("/organizations/{organization_id}/workspaces/{workspace_id}/jobs")
def get_jobs_endpoint(  # noqa: PLR0913
    user_id: Annotated[ID, Depends(get_user_id_fastapi)],
    organization_id: str,  # noqa: ARG001
    workspace_id: str,  # noqa: ARG001
    project_id: str | None = None,
    state: str | None = None,
    job_type: Annotated[list[str] | None, Query()] = None,
    key: str | None = None,
    author_id: str | None = None,
    start_time_from: str | None = None,
    start_time_to: str | None = None,
    creation_time_from: str | None = None,
    creation_time_to: str | None = None,
    skip: int | None = None,
    limit: int | None = None,
    sort_by: str | None = None,
    sort_direction: str | None = None,
) -> dict:
    """
    Endpoint for getting a list of jobs.

    :param user_id: ID of user making a request
    :param organization_id: The id of the organization
    :param workspace_id: The id of the workspace to retrieve jobs from
    :param project_id: The id of the project to filter jobs by
    :param state: The state of the job to filter by
    :param job_type: The type of the job to filter by, multiple job types can be specified
    :param key: The key of the job to filter by
    :param author_id: The author_id of the job to filter by
    :param start_time_from: The start time from which to filter jobs by
    :param start_time_to: The start time to which to filter jobs by
    :param creation_time_from: The creation time from which to filter jobs by
    :param creation_time_to: The creation time to which to filter jobs by
    :param skip: The number of jobs to skip
    :param limit: The maximum number of jobs to return
    :param sort_by: Sorting field to sort by
    :param sort_direction: Sorting direction
    :return: A list of jobs.
    """
    return JobController().get_jobs(
        user_id=user_id,
        project_id=ID(project_id) if project_id else None,
        state=state,
        job_types=job_type,
        key=key,
        author_uid=author_id,
        start_time_from=datetime.fromisoformat(start_time_from) if start_time_from else None,
        start_time_to=datetime.fromisoformat(start_time_to) if start_time_to else None,
        creation_time_from=datetime.fromisoformat(creation_time_from) if creation_time_from else None,
        creation_time_to=datetime.fromisoformat(creation_time_to) if creation_time_to else None,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )


@router.get("/organizations/{organization_id}/workspaces/{workspace_id}/jobs/{job_id}")
def get_job_endpoint(
    user_id: Annotated[ID, Depends(get_user_id_fastapi)],
    organization_id: str,  # noqa: ARG001
    workspace_id: str,  # noqa: ARG001
    job_id: str,
) -> dict:
    """
    Endpoint for getting a job by id.

    :param user_id: ID of user making a request
    :param organization_id: The id of the organization
    :param workspace_id: The id of the workspace the job belongs to
    :param job_id: The id of the job to retrieve
    :return: The job with the given id
    """
    job_id_ = ID(job_id)
    return JobController().get_job(user_uid=user_id, job_id=job_id_)


@router.post(
    "/organizations/{organization_id}/workspaces/{workspace_id}/jobs/{job_id}:cancel",
    status_code=status.HTTP_202_ACCEPTED,
)
def cancel_job_endpoint(
    user_id: Annotated[ID, Depends(get_user_id_fastapi)],
    organization_id: str,  # noqa: ARG001
    workspace_id: str,  # noqa: ARG001
    job_id: str,
) -> str:
    """
    Endpoint for canceling a job.

    :param user_id: ID of user making a request
    :param organization_id: The id of the organization
    :param workspace_id: The id of the workspace the job belongs to
    :param job_id: The id of the job to cancel
    :return: Response acknowledging the cancel request
    """
    return JobController().cancel_job(job_id=ID(job_id), user_uid=user_id)


@router.delete(
    "/organizations/{organization_id}/workspaces/{workspace_id}/jobs/{job_id}", status_code=status.HTTP_202_ACCEPTED
)
def delete_job_endpoint(
    user_id: Annotated[ID, Depends(get_user_id_fastapi)],
    organization_id: str,  # noqa: ARG001
    workspace_id: str,  # noqa: ARG001
    job_id: str,
) -> str:
    """
    Endpoint for deleting a job.

    :param user_id: ID of user making a request
    :param organization_id: The id of the organization
    :param workspace_id: The id of the workspace the job belongs to
    :param job_id: The id of the job to delete
    :return: Response acknowledging the delete request
    """
    return JobController().cancel_job(job_id=ID(job_id), user_uid=user_id, delete_job=True)
