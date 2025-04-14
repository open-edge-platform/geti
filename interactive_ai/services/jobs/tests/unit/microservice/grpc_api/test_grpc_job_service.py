# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
from datetime import datetime
from unittest.mock import Mock, patch

import grpc
import pytest

from microservice.grpc_api.grpc_job_service import DEFAULT_N_JOBS_RETURNED, GRPCJobService
from microservice.job_manager import JobManager, JobsAcl, JobSortingField, Pagination, SortDirection, TimestampFilter
from model.duplicate_policy import DuplicatePolicy
from model.job import Job, JobCancellationInfo, JobFlyteExecutions, JobMainFlyteExecution
from model.job_state import JobState, JobStateGroup
from model.telemetry import Telemetry

from geti_spicedb_tools import Permissions, SpiceDB, SpiceDBResourceTypes
from geti_types import ID, make_session
from grpc_interfaces.credit_system.client import InsufficientCreditsException
from grpc_interfaces.job_submission.pb.job_service_pb2 import (
    CancelJobRequest,
    EmptyResponse,
    FindJobsRequest,
    GetJobByIdRequest,
    GetJobsCountRequest,
    GetJobsCountResponse,
    JobIdResponse,
    JobResponse,
    ListJobsResponse,
    SubmitJobRequest,
)
from sc_sdk.utils.constants import DEFAULT_USER_NAME

DUMMY_USER = ID("dummy_user")
DUMMY_KEY = json.dumps({"key2": "value2", "key1": "value1"})
NORMALIZED_DUMMY_KEY = json.dumps({"key1": "value1", "key2": "value2"})
DUMMY_PAYLOAD = {"payload": "dummy_value"}
DUMMY_METADATA = {"metadata": "dummy_metadata"}
DUMMY_JOB = Job(
    id=ID("dummy_job_id"),
    workspace_id=ID("dummy_workspace_id"),
    type="dummy_job_type",
    priority=1,
    job_name="dummy_job",
    key=NORMALIZED_DUMMY_KEY,
    state=JobState.SCHEDULED,
    state_group=JobStateGroup.SCHEDULED,
    step_details=(),
    payload=DUMMY_PAYLOAD,
    metadata=DUMMY_METADATA,
    creation_time=datetime.strptime("2022-01-15 15:32:45", "%Y-%m-%d %H:%M:%S"),
    author=DUMMY_USER,
    cancellation_info=JobCancellationInfo(cancellable=True, is_cancelled=False),
    executions=JobFlyteExecutions(main=JobMainFlyteExecution()),
    session=make_session(),
    telemetry=Telemetry(),
)


@pytest.fixture
def fxt_grpc_job_service():
    yield GRPCJobService()


@pytest.fixture
def fxt_grpc_context():
    mock_context = Mock(spec=grpc.RpcContext, autospec=True)
    mock_context.set_code = Mock()
    mock_context.set_details = Mock()
    yield mock_context


class TestGRPCJobService:
    @pytest.mark.parametrize(
        "duplicate_policy",
        [DuplicatePolicy.REPLACE, DuplicatePolicy.OMIT],
    )
    @pytest.mark.parametrize(
        "cost, cost_requests",
        [(None, None), ([SubmitJobRequest.CostRequest(unit="images", amount=100)], {"images": 100})],
    )
    @pytest.mark.parametrize(
        "cancellable",
        [True, False],
    )
    def test_submit(
        self, fxt_grpc_job_service, fxt_grpc_context, duplicate_policy, cost, cost_requests, cancellable
    ) -> None:
        priority = 1
        dummy_workspace_id = ID("dummy_workspace_id")
        dummy_job_name = "dummy_job_name"
        dummy_type = "dummy_type"
        dummy_job_id = ID("dummy_job_id")
        telemetry = Telemetry(context="fake_context")

        with patch.object(JobManager, "submit", return_value=dummy_job_id) as mock_submit_job:
            request = SubmitJobRequest(
                priority=priority,
                workspace_id=dummy_workspace_id,
                job_name=dummy_job_name,
                type=dummy_type,
                key=DUMMY_KEY,
                payload=json.dumps(DUMMY_PAYLOAD),
                metadata=json.dumps(DUMMY_METADATA),
                duplicate_policy=duplicate_policy.name,
                author=DUMMY_USER,
                telemetry=SubmitJobRequest.Telemetry(context=telemetry.context),
                cost=cost,
                cancellable=cancellable,
            )
            result = fxt_grpc_job_service.submit(request, fxt_grpc_context)

        mock_submit_job.assert_called_once_with(
            priority=priority,
            job_type=dummy_type,
            job_name=dummy_job_name,
            key=DUMMY_KEY,
            payload=DUMMY_PAYLOAD,
            metadata=DUMMY_METADATA,
            author=DUMMY_USER,
            duplicate_policy=duplicate_policy,
            project_id=None,
            telemetry=telemetry,
            gpu_num_required=0,
            cost_requests=cost_requests,
            cancellable=cancellable,
        )
        assert isinstance(result, JobIdResponse)
        assert result.id == dummy_job_id

    def test_submit_policy_error(self, fxt_grpc_job_service, fxt_grpc_context) -> None:
        policy_str = "not_a_policy"
        expected_error_message = (
            "The supplied duplicate policy is invalid. Please provide a valid policy and try again."
        )
        telemetry = Telemetry(context="fake_context")

        request = SubmitJobRequest(
            priority=1,
            workspace_id="workspace_id",
            job_name="job_name",
            type="train",
            key=DUMMY_KEY,
            payload=json.dumps(DUMMY_PAYLOAD),
            metadata=json.dumps(DUMMY_METADATA),
            duplicate_policy=policy_str,
            author=DUMMY_USER,
            telemetry=SubmitJobRequest.Telemetry(context=telemetry.context),
        )
        fxt_grpc_job_service.submit(request, fxt_grpc_context)

        fxt_grpc_context.set_code.assert_called_once_with(grpc.StatusCode.INVALID_ARGUMENT)
        fxt_grpc_context.set_details.assert_called_once_with(expected_error_message)

    def test_submit_payload_error(self, fxt_grpc_job_service, fxt_grpc_context) -> None:
        expected_error_message = "Failed to deserialize the job payload. Please check the payload and try again."
        telemetry = Telemetry(context="fake_context")

        request = SubmitJobRequest(
            priority=1,
            workspace_id="workspace_id",
            job_name="job_name",
            type="train",
            key=DUMMY_KEY,
            payload="{'key': object}",
            metadata="{}",
            duplicate_policy="REPLACE",
            author=DUMMY_USER,
            telemetry=SubmitJobRequest.Telemetry(context=telemetry.context),
        )
        fxt_grpc_job_service.submit(request, fxt_grpc_context)

        fxt_grpc_context.set_code.assert_called_once_with(grpc.StatusCode.INVALID_ARGUMENT)
        fxt_grpc_context.set_details.assert_called_once_with(expected_error_message)

    def test_submit_insufficient_credits(self, fxt_grpc_job_service, fxt_grpc_context) -> None:
        expected_error_message = "Insufficient balance for job submission"
        telemetry = Telemetry(context="fake_context")

        with (
            patch.object(JobManager, "submit", side_effect=InsufficientCreditsException()),
        ):
            request = SubmitJobRequest(
                priority=1,
                workspace_id="workspace_id",
                job_name="job_name",
                type="train",
                key=DUMMY_KEY,
                payload=json.dumps(DUMMY_PAYLOAD),
                metadata=json.dumps(DUMMY_METADATA),
                duplicate_policy="REPLACE",
                author=DUMMY_USER,
                telemetry=SubmitJobRequest.Telemetry(context=telemetry.context),
            )
            fxt_grpc_job_service.submit(request, fxt_grpc_context)

        fxt_grpc_context.set_code.assert_called_once_with(grpc.StatusCode.FAILED_PRECONDITION)
        fxt_grpc_context.set_details.assert_called_once_with(expected_error_message)

    def test_get_by_id(self, fxt_grpc_job_service, fxt_grpc_context) -> None:
        dummy_workspace_id = ID("dummy_workspace_id")
        dummy_job_id = ID("dummy_job_id")

        with patch.object(JobManager, "get_by_id", return_value=DUMMY_JOB) as mock_get_by_id:
            request = GetJobByIdRequest(workspace_id=dummy_workspace_id, id=dummy_job_id)
            result = fxt_grpc_job_service.get_by_id(request, fxt_grpc_context)

        mock_get_by_id.assert_called_once_with(job_id=dummy_job_id)
        assert isinstance(result, JobResponse)
        assert result.id == DUMMY_JOB.id

    def test_cancel(self, fxt_grpc_job_service, fxt_grpc_context) -> None:
        dummy_workspace_id = ID("dummy_workspace_id")
        dummy_job_id = ID("dummy_job_id")

        with patch.object(JobManager, "mark_cancelled", return_value=None) as mock_mark_cancelled:
            request = CancelJobRequest(
                workspace_id=dummy_workspace_id,
                id=dummy_job_id,
                user_uid=DEFAULT_USER_NAME,
            )
            result = fxt_grpc_job_service.cancel(request, fxt_grpc_context)

        mock_mark_cancelled.assert_called_once_with(
            job_id=dummy_job_id,
            user_uid=DEFAULT_USER_NAME,
        )
        assert isinstance(result, EmptyResponse)

    def test_get_count(self, fxt_grpc_job_service, fxt_grpc_context) -> None:
        dummy_workspace_id = ID("dummy_workspace_id")
        dummy_type = "dummy_type"
        dummy_state_group = JobStateGroup.RUNNING
        dummy_project_id = ID("dummy_project_id")
        dummy_author_uid = "dummy_author_id"
        start_time_from = datetime.strptime("2022-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        start_time_to = datetime.strptime("2022-01-01 01:00:00", "%Y-%m-%d %H:%M:%S")
        time_filter = TimestampFilter(from_val=start_time_from, to_val=start_time_to)
        dummy_count = 3

        with (
            patch.object(JobManager, "get_jobs_count", return_value=dummy_count) as mock_get_jobs_count,
            patch.object(SpiceDB, "get_user_projects", return_value=[]) as mock_spice_db_get_user_projects,
            patch.object(
                SpiceDB, "check_permission", return_value=False
            ) as mock_spice_db_check_user_workspace_permission,
        ):
            request = GetJobsCountRequest(
                workspace_id=dummy_workspace_id,
                type=dummy_type,
                state=dummy_state_group.name,
                key=DUMMY_KEY,
                project_id=dummy_project_id,
                author_uid=dummy_author_uid,
                start_time_from=str(start_time_from),
                start_time_to=str(start_time_to),
                all_permitted_jobs=False,
            )
            result = fxt_grpc_job_service.get_count(request, fxt_grpc_context)

        mock_get_jobs_count.assert_called_once_with(
            job_types=[dummy_type],
            state_group=dummy_state_group,
            key=DUMMY_KEY,
            project_id=dummy_project_id,
            author_uid=dummy_author_uid,
            start_time=time_filter,
            acl=JobsAcl(),
            workspace_id=dummy_workspace_id,
        )
        mock_spice_db_get_user_projects.assert_not_called()
        mock_spice_db_check_user_workspace_permission.assert_not_called()
        assert isinstance(result, GetJobsCountResponse)
        assert result.count == dummy_count

    def test_get_count_all_organization_acl(self, fxt_grpc_job_service, fxt_grpc_context) -> None:
        dummy_type = "dummy_type"
        dummy_state_group = JobStateGroup.RUNNING
        dummy_project_id = ID("dummy_project_id")
        dummy_author_uid = "dummy_author_id"
        start_time_from = datetime.strptime("2022-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        start_time_to = datetime.strptime("2022-01-01 01:00:00", "%Y-%m-%d %H:%M:%S")
        time_filter = TimestampFilter(from_val=start_time_from, to_val=start_time_to)
        dummy_count = 3

        with (
            patch.object(JobManager, "get_jobs_count", return_value=dummy_count) as mock_get_jobs_count,
            patch.object(SpiceDB, "get_user_projects", return_value=[]) as mock_spice_db_get_user_projects,
        ):
            request = GetJobsCountRequest(
                type=dummy_type,
                state=dummy_state_group.name,
                key=DUMMY_KEY,
                project_id=dummy_project_id,
                author_uid=dummy_author_uid,
                start_time_from=str(start_time_from),
                start_time_to=str(start_time_to),
                all_permitted_jobs=True,
            )
            result = fxt_grpc_job_service.get_count(request, fxt_grpc_context)

        mock_get_jobs_count.assert_called_once_with(
            job_types=[dummy_type],
            state_group=dummy_state_group,
            key=DUMMY_KEY,
            project_id=dummy_project_id,
            author_uid=None,
            start_time=time_filter,
            acl=JobsAcl(permitted_projects=[], workspace_jobs_author=None),
            workspace_id=None,
        )
        mock_spice_db_get_user_projects.assert_called_once_with(
            user_id=dummy_author_uid, permission=Permissions.VIEW_PROJECT
        )
        assert isinstance(result, GetJobsCountResponse)
        assert result.count == dummy_count

    @pytest.mark.parametrize("view_all_workspace_jobs", [True, False])
    def test_get_count_all_acl(self, fxt_grpc_job_service, fxt_grpc_context, view_all_workspace_jobs) -> None:
        dummy_workspace_id = ID("dummy_workspace_id")
        dummy_type = "dummy_type"
        dummy_state_group = JobStateGroup.RUNNING
        dummy_project_id = ID("dummy_project_id")
        dummy_author_uid = "dummy_author_id"
        start_time_from = datetime.strptime("2022-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        start_time_to = datetime.strptime("2022-01-01 01:00:00", "%Y-%m-%d %H:%M:%S")
        time_filter = TimestampFilter(from_val=start_time_from, to_val=start_time_to)
        dummy_count = 3

        with (
            patch.object(JobManager, "get_jobs_count", return_value=dummy_count) as mock_get_jobs_count,
            patch.object(SpiceDB, "get_user_projects", return_value=[]) as mock_spice_db_get_user_projects,
            patch.object(
                SpiceDB, "check_permission", return_value=view_all_workspace_jobs
            ) as mock_spice_db_check_user_workspace_permission,
        ):
            request = GetJobsCountRequest(
                workspace_id=dummy_workspace_id,
                type=dummy_type,
                state=dummy_state_group.name,
                key=DUMMY_KEY,
                project_id=dummy_project_id,
                author_uid=dummy_author_uid,
                start_time_from=str(start_time_from),
                start_time_to=str(start_time_to),
                all_permitted_jobs=True,
            )
            result = fxt_grpc_job_service.get_count(request, fxt_grpc_context)

        mock_get_jobs_count.assert_called_once_with(
            job_types=[dummy_type],
            state_group=dummy_state_group,
            key=DUMMY_KEY,
            project_id=dummy_project_id,
            author_uid=None,
            start_time=time_filter,
            acl=JobsAcl(
                permitted_projects=[], workspace_jobs_author=None if view_all_workspace_jobs else dummy_author_uid
            ),
            workspace_id=dummy_workspace_id,
        )
        mock_spice_db_get_user_projects.assert_called_once_with(
            user_id=dummy_author_uid, permission=Permissions.VIEW_PROJECT
        )
        mock_spice_db_check_user_workspace_permission.assert_called_once_with(
            resource_type=SpiceDBResourceTypes.WORKSPACE.value,
            resource_id=dummy_workspace_id,
            subject_type=SpiceDBResourceTypes.USER.value,
            subject_id=dummy_author_uid,
            permission=Permissions.VIEW_ALL_WORKSPACE_JOBS.value,
        )
        assert isinstance(result, GetJobsCountResponse)
        assert result.count == dummy_count

    def test_find(self, fxt_grpc_job_service, fxt_grpc_context) -> None:
        dummy_workspace_id = ID("dummy_workspace_id")
        dummy_type = "dummy_type"
        dummy_state_group = JobStateGroup.RUNNING
        dummy_project_id = ID("dummy_project_id")
        dummy_author_uid = "dummy_author_id"
        start_time_from = datetime.strptime("2022-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        start_time_to = datetime.strptime("2022-01-01 01:00:00", "%Y-%m-%d %H:%M:%S")
        time_filter = TimestampFilter(from_val=start_time_from, to_val=start_time_to)
        sort_by = JobSortingField.PRIORITY
        sort_direction = SortDirection.ASC

        with (
            patch.object(JobManager, "find", return_value=[DUMMY_JOB]) as mock_find,
            patch.object(JobManager, "get_jobs_count", return_value=1) as mock_count,
            patch.object(SpiceDB, "get_user_projects", return_value=[]) as mock_spice_db_get_user_projects,
            patch.object(
                SpiceDB, "check_permission", return_value=False
            ) as mock_spice_db_check_user_workspace_permission,
        ):
            request = FindJobsRequest(
                workspace_id=dummy_workspace_id,
                type=dummy_type,
                state=dummy_state_group.name,
                key=DUMMY_KEY,
                project_id=dummy_project_id,
                author_uid=dummy_author_uid,
                start_time_from=str(start_time_from),
                start_time_to=str(start_time_to),
                sort_by=sort_by.name,
                sort_direction=sort_direction.name,
                all_permitted_jobs=False,
            )
            result = fxt_grpc_job_service.find(request, fxt_grpc_context)

        mock_find.assert_called_once_with(
            job_types=[dummy_type],
            state_group=dummy_state_group,
            key=DUMMY_KEY,
            author_uid=dummy_author_uid,
            start_time=time_filter,
            project_id=dummy_project_id,
            pagination=Pagination(skip=0, limit=DEFAULT_N_JOBS_RETURNED),
            sort_by=sort_by,
            sort_direction=sort_direction,
            acl=JobsAcl(),
        )
        mock_count.assert_called_with(
            job_types=[dummy_type],
            state_group=dummy_state_group,
            key=DUMMY_KEY,
            author_uid=dummy_author_uid,
            start_time=time_filter,
            project_id=dummy_project_id,
            acl=JobsAcl(),
        )
        mock_spice_db_get_user_projects.assert_not_called()
        mock_spice_db_check_user_workspace_permission.assert_not_called()
        assert isinstance(result, ListJobsResponse)
        assert len(result.jobs) == 1
        assert result.jobs[0].key == NORMALIZED_DUMMY_KEY

    @pytest.mark.parametrize("view_all_workspace_jobs", [True, False])
    def test_find_all_acl(self, fxt_grpc_job_service, fxt_grpc_context, view_all_workspace_jobs) -> None:
        dummy_workspace_id = ID("dummy_workspace_id")
        dummy_type = "dummy_type"
        dummy_state_group = JobStateGroup.RUNNING
        dummy_project_id = ID("dummy_project_id")
        dummy_author_uid = "dummy_author_id"
        start_time_from = datetime.strptime("2022-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        start_time_to = datetime.strptime("2022-01-01 01:00:00", "%Y-%m-%d %H:%M:%S")
        time_filter = TimestampFilter(from_val=start_time_from, to_val=start_time_to)
        sort_by = JobSortingField.PRIORITY
        sort_direction = SortDirection.ASC

        with (
            patch.object(JobManager, "find", return_value=[DUMMY_JOB]) as mock_find,
            patch.object(JobManager, "get_jobs_count", return_value=1) as mock_count,
            patch.object(SpiceDB, "get_user_projects", return_value=[]) as mock_spice_db_get_user_projects,
            patch.object(
                SpiceDB, "check_permission", return_value=view_all_workspace_jobs
            ) as mock_spice_db_check_user_workspace_permission,
        ):
            request = FindJobsRequest(
                workspace_id=dummy_workspace_id,
                type=dummy_type,
                state=dummy_state_group.name,
                key=DUMMY_KEY,
                project_id=dummy_project_id,
                author_uid=dummy_author_uid,
                start_time_from=str(start_time_from),
                start_time_to=str(start_time_to),
                sort_by=sort_by.name,
                sort_direction=sort_direction.name,
                all_permitted_jobs=True,
            )
            result = fxt_grpc_job_service.find(request, fxt_grpc_context)

        mock_find.assert_called_once_with(
            job_types=[dummy_type],
            state_group=dummy_state_group,
            key=DUMMY_KEY,
            author_uid=None,
            start_time=time_filter,
            project_id=dummy_project_id,
            pagination=Pagination(skip=0, limit=DEFAULT_N_JOBS_RETURNED),
            sort_by=sort_by,
            sort_direction=sort_direction,
            acl=JobsAcl(
                permitted_projects=[], workspace_jobs_author=None if view_all_workspace_jobs else dummy_author_uid
            ),
        )
        mock_count.assert_called_with(
            job_types=[dummy_type],
            state_group=dummy_state_group,
            key=DUMMY_KEY,
            author_uid=None,
            start_time=time_filter,
            project_id=dummy_project_id,
            acl=JobsAcl(
                permitted_projects=[], workspace_jobs_author=None if view_all_workspace_jobs else dummy_author_uid
            ),
        )
        mock_spice_db_get_user_projects.assert_called_once_with(
            user_id=dummy_author_uid, permission=Permissions.VIEW_PROJECT
        )
        mock_spice_db_check_user_workspace_permission.assert_called_once_with(
            resource_type=SpiceDBResourceTypes.WORKSPACE.value,
            resource_id=dummy_workspace_id,
            subject_type=SpiceDBResourceTypes.USER.value,
            subject_id=dummy_author_uid,
            permission=Permissions.VIEW_ALL_WORKSPACE_JOBS.value,
        )
        assert isinstance(result, ListJobsResponse)
        assert len(result.jobs) == 1
        assert result.jobs[0].key == NORMALIZED_DUMMY_KEY

    def test_find_pagination(self, fxt_grpc_job_service, fxt_grpc_context) -> None:
        with (
            patch.object(JobManager, "find", side_effect=[[DUMMY_JOB], [DUMMY_JOB]]),
            patch.object(JobManager, "get_jobs_count", return_value=2),
        ):
            request = FindJobsRequest(workspace_id=ID("dummy_workspace_id"), limit=1)
            page_1 = fxt_grpc_job_service.find(request, fxt_grpc_context)
            assert len(page_1.jobs) == 1
            assert ID(page_1.jobs[0].id) == DUMMY_JOB.id
            assert page_1.HasField("next_page")

            request = FindJobsRequest(
                workspace_id=ID("dummy_workspace_id"),
                limit=page_1.next_page.limit,
                skip=page_1.next_page.skip,
            )
            page_2 = fxt_grpc_job_service.find(request, fxt_grpc_context)
            assert len(page_2.jobs) == 1
            assert ID(page_2.jobs[0].id) == DUMMY_JOB.id
            assert not page_2.HasField("next_page")

    @pytest.mark.parametrize(
        "state_str, state",
        [
            ("RuNnInG", JobStateGroup.RUNNING),
            ("RUNNING", JobStateGroup.RUNNING),
            ("Walking", None),
            ("****", None),
        ],
    )
    def test_get_and_validate_state(self, fxt_grpc_job_service, state_str, state) -> None:
        if state:
            fxt_grpc_job_service._get_and_validate_state(state=state_str) == state
        else:
            with pytest.raises(ValueError) as error:
                fxt_grpc_job_service._get_and_validate_state(state=state_str)
            assert str(error.value) == f"Invalid job state '{state_str}'."

    @pytest.mark.parametrize(
        "sort_by_str, sort_direction_str, sort_by, sort_direction",
        [
            ("job_name", "ASC", JobSortingField.JOB_NAME, SortDirection.ASC),
            ("Start_Time", "ASCENDING", JobSortingField.START_TIME, None),
            ("Start_Time", "DESC", JobSortingField.START_TIME, SortDirection.DESC),
            ("******", "#####", None, None),
        ],
    )
    def test_get_and_validate_sorting_fields(
        self,
        fxt_grpc_job_service,
        sort_by_str,
        sort_direction_str,
        sort_by,
        sort_direction,
    ) -> None:
        if sort_by and sort_direction:
            (_sort_by, _sort_direction) = fxt_grpc_job_service._get_and_validate_sorting_fields(
                sort_by=sort_by_str, sort_direction=sort_direction_str
            )
            assert _sort_by == sort_by
            assert _sort_direction == sort_direction
        elif sort_by and not sort_direction:
            with pytest.raises(ValueError) as error:
                fxt_grpc_job_service._get_and_validate_sorting_fields(
                    sort_by=sort_by_str, sort_direction=sort_direction_str
                )
            assert str(error.value) == f"Invalid sort_direction '{sort_direction_str}'."
        else:
            with pytest.raises(ValueError) as error:
                fxt_grpc_job_service._get_and_validate_sorting_fields(
                    sort_by=sort_by_str, sort_direction=sort_direction_str
                )
            assert str(error.value) == f"Invalid sort_by '{sort_by_str}'."
