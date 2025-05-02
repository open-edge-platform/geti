# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
from unittest.mock import patch

import pytest
from starlette import status
from testfixtures import compare

from microservice.exceptions import JobNotCancellableException
from microservice.job_manager import (
    JobManager,
    JobsAcl,
    JobsCount,
    JobSortingField,
    Pagination,
    SortDirection,
    TimestampFilter,
)
from microservice.rest.http_exceptions import (
    BadRequestHTTPException,
    JobNotCancellableHTTPException,
    JobNotFoundHTTPException,
    JobNotPermittedHTTPException,
)
from microservice.rest.job_controller import DEFAULT_N_JOBS_RETURNED, MAX_N_JOBS_RETURNED, JobController
from microservice.rest.job_rest_views import FindJobsQuery, JobRestViews
from model.job_state import JobStateGroup

from geti_spicedb_tools import Permissions, SpiceDB, SpiceDBResourceTypes
from geti_types import ID
from iai_core.utils.constants import DEFAULT_USER_NAME
from iai_core.utils.time_utils import now

DUMMY_ORGANIZATION_ID = "000000000000000000000001"
DUMMY_JOB_KEY = json.dumps({"job_key": "job_value"})
DUMMY_AUTHOR = ID("author_uid")
DUMMY_TIME = now()


class TestJobController:
    def test_get_project_job(self, fxt_job, fxt_job_rest) -> None:
        # Arrange
        user_id = "user"
        job_id = fxt_job.id

        # Act
        with (
            patch.object(JobManager, "get_by_id", return_value=fxt_job) as mock_get_job_by_id,
            patch.object(JobRestViews, "job_to_rest", return_value=fxt_job_rest) as mock_job_to_rest,
            patch.object(
                SpiceDB, "check_permission", return_value=True
            ) as mock_spice_db_check_user_workspace_permission,
        ):
            result = JobController().get_job(user_uid=user_id, job_id=job_id)

        # Assert
        mock_get_job_by_id.assert_called_once_with(job_id=job_id)
        mock_spice_db_check_user_workspace_permission.assert_not_called()
        mock_job_to_rest.assert_called_once_with(job=fxt_job)
        compare(result, fxt_job_rest, ignore_eq=True)

    def test_get_workspace_job_view_all_permitted(self, fxt_workspace_job, fxt_job_rest) -> None:
        # Arrange
        user_id = "user"
        job_id = fxt_workspace_job.id

        # Act
        with (
            patch.object(JobManager, "get_by_id", return_value=fxt_workspace_job) as mock_get_job_by_id,
            patch.object(JobRestViews, "job_to_rest", return_value=fxt_job_rest) as mock_job_to_rest,
            patch.object(
                SpiceDB, "check_permission", return_value=True
            ) as mock_spice_db_check_user_workspace_permission,
        ):
            result = JobController().get_job(user_uid=user_id, job_id=job_id)

        # Assert
        mock_get_job_by_id.assert_called_once_with(job_id=job_id)
        mock_spice_db_check_user_workspace_permission.assert_called_once_with(
            resource_type=SpiceDBResourceTypes.WORKSPACE.value,
            resource_id=fxt_workspace_job.workspace_id,
            subject_type=SpiceDBResourceTypes.USER.value,
            subject_id=user_id,
            permission=Permissions.VIEW_ALL_WORKSPACE_JOBS.value,
        )
        mock_job_to_rest.assert_called_once_with(job=fxt_workspace_job)
        compare(result, fxt_job_rest, ignore_eq=True)

    def test_get_workspace_job_is_author(self, fxt_workspace_job, fxt_job_rest) -> None:
        # Arrange
        user_id = "author_uid"
        job_id = fxt_workspace_job.id

        # Act
        with (
            patch.object(JobManager, "get_by_id", return_value=fxt_workspace_job) as mock_get_job_by_id,
            patch.object(JobRestViews, "job_to_rest", return_value=fxt_job_rest) as mock_job_to_rest,
            patch.object(
                SpiceDB, "check_permission", return_value=False
            ) as mock_spice_db_check_user_workspace_permission,
        ):
            result = JobController().get_job(user_uid=user_id, job_id=job_id)

        # Assert
        mock_get_job_by_id.assert_called_once_with(job_id=job_id)
        mock_spice_db_check_user_workspace_permission.assert_not_called()
        mock_job_to_rest.assert_called_once_with(job=fxt_workspace_job)
        compare(result, fxt_job_rest, ignore_eq=True)

    def test_get_workspace_job_not_permitted(self, fxt_workspace_job, fxt_job_rest) -> None:
        # Arrange
        user_id = "another_author_uid"
        job_id = fxt_workspace_job.id

        # Act
        with (
            patch.object(JobManager, "get_by_id", return_value=fxt_workspace_job) as mock_get_job_by_id,
            patch.object(JobRestViews, "job_to_rest", return_value=fxt_job_rest) as mock_job_to_rest,
            patch.object(
                SpiceDB, "check_permission", return_value=False
            ) as mock_spice_db_check_user_workspace_permission,
            pytest.raises(JobNotPermittedHTTPException) as error,
        ):
            JobController().get_job(user_uid=user_id, job_id=job_id)

        # Assert
        mock_get_job_by_id.assert_called_once_with(job_id=job_id)
        mock_spice_db_check_user_workspace_permission.assert_called_once_with(
            resource_type=SpiceDBResourceTypes.WORKSPACE.value,
            resource_id=fxt_workspace_job.workspace_id,
            subject_type=SpiceDBResourceTypes.USER.value,
            subject_id=user_id,
            permission=Permissions.VIEW_ALL_WORKSPACE_JOBS.value,
        )
        mock_job_to_rest.assert_not_called()
        assert error.value.status_code == status.HTTP_403_FORBIDDEN

    def test_get_job_not_found(self) -> None:
        # Arrange
        user_id = "user"
        job_id = ID("job_id")

        # Act
        with (
            pytest.raises(JobNotFoundHTTPException) as error,
            patch.object(JobManager, "get_by_id", return_value=None) as mock_get_job_by_id,
        ):
            JobController().get_job(user_uid=user_id, job_id=job_id)

        # Assert
        mock_get_job_by_id.assert_called_once_with(job_id=job_id)
        assert error.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "skip, limit, expected_skip, expected_limit",
        (
            (1, 2, 1, 2),
            (-3, -8, 0, 1),
            (None, None, 0, DEFAULT_N_JOBS_RETURNED),
            (None, 4, 0, 4),
            (1, MAX_N_JOBS_RETURNED + 1, 1, MAX_N_JOBS_RETURNED),
        ),
    )
    @pytest.mark.parametrize("view_all_workspace_jobs", (True, False))
    def test_get_jobs(
        self,
        fxt_job,
        fxt_job_rest,
        skip,
        limit,
        expected_skip,
        expected_limit,
        view_all_workspace_jobs,
    ) -> None:
        # Arrange
        workspace_id = fxt_job.workspace_id
        organization_id = ID(DUMMY_ORGANIZATION_ID)
        project_id = ID("project_id")
        state = "SCHEDULED"
        job_type = "train"
        key = DUMMY_JOB_KEY
        author_uid = DUMMY_AUTHOR
        start_time = TimestampFilter(from_val=now(), to_val=now())
        expected_pagination = Pagination(skip=expected_skip, limit=expected_limit)
        sort_by = "start_time"
        sort_direction = "desc"
        find_query = FindJobsQuery(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            state_group=JobStateGroup.SCHEDULED,
            job_types=[job_type],
            key=key,
            author_uid=author_uid,
            start_time_from=start_time.from_val,
            start_time_to=start_time.to_val,
            pagination=expected_pagination,
            sort_by=JobSortingField[sort_by.upper()],
            sort_direction=SortDirection[sort_direction.upper()],
        )
        jobs_count = JobsCount(
            n_scheduled_jobs=1,
            n_running_jobs=0,
            n_finished_jobs=2,
            n_failed_jobs=3,
            n_cancelled_jobs=1,
        )
        rest_view = {
            "jobs": [fxt_job_rest, fxt_job_rest],
            "jobs_count": {
                "n_scheduled_jobs": jobs_count.n_scheduled_jobs,
                "n_running_jobs": jobs_count.n_running_jobs,
                "n_finished_jobs": jobs_count.n_finished_jobs,
                "n_failed_jobs": jobs_count.n_failed_jobs,
                "n_cancelled_jobs": jobs_count.n_cancelled_jobs,
            },
        }

        # Act
        with (
            patch.object(JobManager, "find", return_value=[fxt_job, fxt_job]) as mock_find,
            patch.object(JobManager, "get_jobs_count", return_value=2) as mock_get_count,
            patch.object(JobManager, "get_jobs_count_per_state", return_value=jobs_count) as mock_get_count_per_state,
            patch.object(JobRestViews, "jobs_to_rest", return_value=rest_view) as mock_jobs_to_rest,
            patch.object(SpiceDB, "get_user_projects", return_value=[]) as mock_spice_db_get_user_projects,
            patch.object(
                SpiceDB, "check_permission", return_value=view_all_workspace_jobs
            ) as mock_spice_db_check_user_workspace_permission,
        ):
            result = JobController().get_jobs(
                user_id=DUMMY_AUTHOR,
                project_id=project_id,
                state=state,
                job_types=[job_type],
                key=key,
                author_uid=author_uid,
                start_time_from=start_time.from_val,
                start_time_to=start_time.to_val,
                skip=skip,
                limit=limit,
                sort_by=sort_by,
                sort_direction=sort_direction,
            )

        # Assert
        mock_find.assert_called_once_with(
            project_id=project_id,
            state_group=JobStateGroup.SCHEDULED,
            job_types=[job_type],
            key=key,
            author_uid=author_uid,
            start_time=start_time,
            pagination=expected_pagination,
            acl=JobsAcl(
                permitted_projects=[],
                workspace_jobs_author=None if view_all_workspace_jobs else DUMMY_AUTHOR,
            ),
            sort_by=JobSortingField[sort_by.upper()],
            sort_direction=SortDirection[sort_direction.upper()],
        )
        mock_get_count.assert_called_once_with(
            project_id=project_id,
            state_group=JobStateGroup.SCHEDULED,
            job_types=[job_type],
            key=key,
            author_uid=author_uid,
            start_time=start_time,
            acl=JobsAcl(
                permitted_projects=[],
                workspace_jobs_author=None if view_all_workspace_jobs else DUMMY_AUTHOR,
            ),
        )
        mock_get_count_per_state.assert_called_once_with(
            project_id=project_id,
            job_types=[job_type],
            author_uid=author_uid,
            start_time=start_time,
            acl=JobsAcl(
                permitted_projects=[],
                workspace_jobs_author=None if view_all_workspace_jobs else DUMMY_AUTHOR,
            ),
        )
        mock_spice_db_get_user_projects.assert_called_once_with(
            user_id=DUMMY_AUTHOR, permission=Permissions.VIEW_PROJECT
        )
        mock_spice_db_check_user_workspace_permission.assert_called_once_with(
            resource_type=SpiceDBResourceTypes.WORKSPACE.value,
            resource_id=workspace_id,
            subject_type=SpiceDBResourceTypes.USER.value,
            subject_id=DUMMY_AUTHOR,
            permission=Permissions.VIEW_ALL_WORKSPACE_JOBS.value,
        )
        mock_jobs_to_rest.assert_called_once_with(
            jobs=[fxt_job, fxt_job],
            total_count=2,
            find_query=find_query,
            jobs_count=jobs_count,
        )
        compare(result, rest_view)

    def test_get_jobs_wrong_state(self) -> None:
        # Arrange
        state = "DUMMY_STATE"
        expected_error_message = f"The state {state} is not valid"

        # Act
        with pytest.raises(BadRequestHTTPException) as error:
            JobController().get_jobs(user_id=DUMMY_AUTHOR, state=state)

        # Assert
        assert error.value.detail == expected_error_message
        assert error.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_cancel_job(self, fxt_job) -> None:
        # Arrange
        job_id = fxt_job.id

        # Act
        with patch.object(JobManager, "mark_cancelled", return_value=True) as mock_mark_cancelled:
            JobController().cancel_job(job_id=job_id, user_uid=DEFAULT_USER_NAME)

        # Assert
        mock_mark_cancelled.assert_called_once_with(
            job_id=job_id,
            user_uid=DEFAULT_USER_NAME,
            delete_job=False,
        )

    def test_cancel_job_not_found(self, fxt_job) -> None:
        # Arrange
        job_id = fxt_job.id

        # Act
        with (
            pytest.raises(JobNotFoundHTTPException) as error,
            patch.object(JobManager, "mark_cancelled", return_value=False) as mock_mark_cancelled,
        ):
            JobController().cancel_job(job_id=job_id, user_uid=DEFAULT_USER_NAME)

        # Assert
        mock_mark_cancelled.assert_called_once_with(
            job_id=job_id,
            user_uid=DEFAULT_USER_NAME,
            delete_job=False,
        )
        assert error.value.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_job_not_cancellable(self, fxt_job) -> None:
        # Arrange
        job_id = fxt_job.id

        # Act
        with (
            pytest.raises(JobNotCancellableHTTPException) as error,
            patch.object(
                JobManager,
                "mark_cancelled",
                side_effect=JobNotCancellableException(job_id=job_id),
            ) as mock_mark_cancelled,
        ):
            JobController().cancel_job(job_id=job_id, user_uid=DEFAULT_USER_NAME)

        # Assert
        mock_mark_cancelled.assert_called_once_with(
            job_id=job_id,
            user_uid=DEFAULT_USER_NAME,
            delete_job=False,
        )
        assert error.value.status_code == status.HTTP_412_PRECONDITION_FAILED
