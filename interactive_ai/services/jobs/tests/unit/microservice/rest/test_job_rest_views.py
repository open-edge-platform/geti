# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json

import pytest
from testfixtures import compare

from microservice.job_manager import JobsCount, Pagination
from microservice.rest.job_rest_views import FindJobsQuery, JobRestViews
from model.job_state import JobStateGroup

from geti_types import ID
from iai_core.utils.time_utils import now

DUMMY_JOB_KEY = json.dumps({"job_key": "job_value"})
DUMMY_AUTHOR = ID("author_uid")
DUMMY_TIME = now()


class TestJobRESTViews:
    def test_job_to_rest(self, fxt_job, fxt_job_rest) -> None:
        result = JobRestViews.job_to_rest(job=fxt_job)

        compare(result, fxt_job_rest, ignore_eq=True)

    @pytest.mark.parametrize(
        "count, skip, limit, next_page_available",
        [
            (5, 0, 3, True),
            (5, 4, 3, False),
        ],
    )
    def test_jobs_to_rest(self, fxt_job, fxt_job_rest, count, skip, limit, next_page_available) -> None:
        # Arrange
        organization_id = ID("dummy_organization_id")
        workspace_id = ID("dummy_workspace_id")
        pagination = Pagination(skip=skip, limit=limit)
        jobs = [fxt_job_rest, fxt_job_rest]
        jobs_count = JobsCount(
            n_scheduled_jobs=1,
            n_running_jobs=0,
            n_finished_jobs=2,
            n_failed_jobs=3,
            n_cancelled_jobs=1,
        )
        jobs_count_rest = {
            "n_scheduled_jobs": jobs_count.n_scheduled_jobs,
            "n_running_jobs": jobs_count.n_running_jobs,
            "n_finished_jobs": jobs_count.n_finished_jobs,
            "n_failed_jobs": jobs_count.n_failed_jobs,
            "n_cancelled_jobs": jobs_count.n_cancelled_jobs,
        }
        jobs_rest = {"jobs": jobs, "jobs_count": jobs_count_rest}
        if next_page_available:
            jobs_rest["next_page"] = (
                f"/api/v1/organizations/{str(organization_id)}/workspaces/{str(workspace_id)}/jobs"
                f"?limit={str(limit)}&skip={str(skip + len(jobs))}"
            )
        find_query = FindJobsQuery(
            organization_id=organization_id,
            workspace_id=workspace_id,
            pagination=pagination,
        )

        # Act
        result = JobRestViews.jobs_to_rest(
            jobs=[fxt_job, fxt_job],
            total_count=count,
            find_query=find_query,
            jobs_count=jobs_count,
        )

        # Assert
        compare(result, jobs_rest, ignore_eq=True)

    def test_jobs_to_rest_next_page(self, fxt_job, fxt_job_rest) -> None:
        # Arrange
        organization_id = ID("dummy_organization_id")
        workspace_id = ID("dummy_workspace_id")
        project_id = ID("dummy_project_id")
        page_num_jobs = 10
        pagination = Pagination(skip=1, limit=10)
        find_query = FindJobsQuery(
            organization_id=organization_id,
            workspace_id=workspace_id,
            pagination=pagination,
            project_id=project_id,
            state_group=JobStateGroup.SCHEDULED,
            job_types=["train"],
            key=DUMMY_JOB_KEY,
            author_uid=DUMMY_AUTHOR,
            start_time_from=DUMMY_TIME,
            start_time_to=DUMMY_TIME,
            creation_time_from=DUMMY_TIME,
            creation_time_to=DUMMY_TIME,
        )
        offset = pagination.skip + page_num_jobs
        expected_next_page = (
            f"/api/v1/organizations/{str(organization_id)}"
            f"/workspaces/{str(workspace_id)}/jobs"
            f"?limit={str(pagination.limit)}&skip={str(offset)}"
            f"&project_id={project_id}"
            f"&state={JobStateGroup.SCHEDULED.name}"
            f"&key={DUMMY_JOB_KEY}"
            f"&author_uid={DUMMY_AUTHOR}"
            f"&start_time_from={DUMMY_TIME.isoformat()}"
            f"&start_time_to={DUMMY_TIME.isoformat()}"
            f"&creation_time_from={DUMMY_TIME.isoformat()}"
            f"&creation_time_to={DUMMY_TIME.isoformat()}"
            f"&job_type=train"
        )

        # Act
        result = JobRestViews._get_next_page_url(
            offset=offset,
            find_query=find_query,
        )

        # Assert
        assert result == expected_next_page
