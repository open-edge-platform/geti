# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
from datetime import datetime
from unittest.mock import MagicMock

import grpc
import pytest
from bson import ObjectId

from geti_types import ID, make_session, session_context
from grpc_interfaces.job_submission.client import CommunicationError, GRPCJobsClient
from grpc_interfaces.job_submission.pb.job_service_pb2 import (
    CancelJobRequest,
    FindJobsRequest,
    GetJobByIdRequest,
    GetJobsCountRequest,
    GetJobsCountResponse,
    JobIdResponse,
    SubmitJobRequest,
)
from sc_sdk.utils.constants import DEFAULT_USER_NAME

job_id = ID(ObjectId())
job_key = json.dumps({"key": "value"})
payload = {"paylod_key": "value"}
metadata = {"metadata_key": "value"}
organization_id = ID(ObjectId())
workspace_id = ID("test_workspace_id")
project_id = ID("test_project_id")


def do_nothing(self, *args, **kwargs) -> None:
    return None


@pytest.fixture
def fxt_grpc_client():
    session = make_session(
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    client = GRPCJobsClient(grpc_address="localhost:50051", metadata_getter=lambda: session.as_tuple())
    client.job_service_stub = MagicMock()
    yield client


class TestGRPCJobsClient:
    def test_submit(self, fxt_grpc_client) -> None:
        # Arrange
        session = make_session(
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        mocked_submit = fxt_grpc_client.job_service_stub.submit
        mocked_submit.return_value = JobIdResponse(id=job_id)
        expected_grpc_message = SubmitJobRequest(
            priority=1,
            workspace_id=workspace_id,
            job_name="test_job",
            type="train",
            key=job_key,
            payload=json.dumps(payload),
            metadata=json.dumps(metadata),
            duplicate_policy="replace",
            author=ID("dummy_user"),
            project_id=project_id,
            telemetry=SubmitJobRequest.Telemetry(context=""),
            cancellable=True,
        )

        # Act
        with session_context(session=session):
            result = fxt_grpc_client.submit(
                priority=1,
                job_name="test_job",
                job_type="train",
                key=job_key,
                payload=payload,
                metadata=metadata,
                duplicate_policy="replace",
                author=ID("dummy_user"),
                project_id=project_id,
                cancellable=True,
            )

        # Assert
        mocked_submit.assert_called_once_with(
            expected_grpc_message,
            metadata=session.as_tuple(),
            wait_for_ready=True,
        )
        assert result == job_id

    def test_find(self, fxt_grpc_client) -> None:
        # Arrange
        session = make_session(
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        dummy_jobs = ["dummy_job"]
        dummy_start_time_from = datetime.now()
        dummy_start_time_to = datetime.now()
        mocked_find = fxt_grpc_client.job_service_stub.find
        mocked_find.return_value = dummy_jobs
        expected_grpc_message = FindJobsRequest(
            workspace_id=workspace_id,
            type="train",
            state="SUBMITTED",
            project_id=project_id,
            author_uid=ID("dummy_user"),
            start_time_from=dummy_start_time_from.isoformat(),
            start_time_to=dummy_start_time_to.isoformat(),
            limit=3,
            skip=1,
        )

        # Act
        with session_context(session=session):
            result = fxt_grpc_client.find(
                workspace_id=workspace_id,
                job_type="train",
                state="SUBMITTED",
                project_id=project_id,
                author_uid=ID("dummy_user"),
                start_time_from=dummy_start_time_from,
                start_time_to=dummy_start_time_to,
                limit=3,
                skip=1,
            )

        # Assert
        mocked_find.assert_called_once_with(expected_grpc_message, metadata=session.as_tuple(), wait_for_ready=True)
        assert result == dummy_jobs

    def test_get_by_id(self, fxt_grpc_client) -> None:
        # Arrange
        session = make_session(
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        mocked_get_by_id = fxt_grpc_client.job_service_stub.get_by_id
        mocked_get_by_id.return_value = "dummy_job"
        expected_grpc_message = GetJobByIdRequest(workspace_id=workspace_id, id=job_id)

        # Act
        with session_context(session=session):
            result = fxt_grpc_client.get_by_id(job_id=job_id)

        # Assert
        mocked_get_by_id.assert_called_once_with(
            expected_grpc_message, metadata=session.as_tuple(), wait_for_ready=True
        )
        assert result == "dummy_job"

    def test_cancel(self, fxt_grpc_client) -> None:
        # Arrange
        session = make_session(
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        mocked_cancel = fxt_grpc_client.job_service_stub.cancel
        expected_grpc_message = CancelJobRequest(workspace_id=workspace_id, id=job_id, user_uid=DEFAULT_USER_NAME)

        # Act
        with session_context(session=session):
            fxt_grpc_client.cancel(job_id=job_id, user_uid=DEFAULT_USER_NAME)

        # Assert
        mocked_cancel.assert_called_once_with(expected_grpc_message, metadata=session.as_tuple(), wait_for_ready=True)

    def test_get_count(self, fxt_grpc_client) -> None:
        # Arrange
        session = make_session(
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        dummy_count = 3
        dummy_start_time_from = datetime.now()
        dummy_start_time_to = datetime.now()
        mocked_get_count = fxt_grpc_client.job_service_stub.get_count
        mocked_get_count.return_value = GetJobsCountResponse(count=dummy_count)
        expected_grpc_message = GetJobsCountRequest(
            workspace_id=workspace_id,
            type="train",
            state="SUBMITTED",
            project_id=project_id,
            author_uid=ID("dummy_user"),
            start_time_from=dummy_start_time_from.isoformat(),
            start_time_to=dummy_start_time_to.isoformat(),
        )

        # Act
        with session_context(session=session):
            result = fxt_grpc_client.get_count(
                workspace_id=workspace_id,
                job_type="train",
                state="SUBMITTED",
                project_id=project_id,
                author_uid=ID("dummy_user"),
                start_time_from=dummy_start_time_from,
                start_time_to=dummy_start_time_to,
            )

        # Assert
        mocked_get_count.assert_called_once_with(
            expected_grpc_message, metadata=session.as_tuple(), wait_for_ready=True
        )
        assert result == dummy_count

    @pytest.mark.parametrize(
        "error_msg, expected_exc, expected_error_msg",
        [
            (
                "The supplied duplicate policy is invalid. Please provide a valid policy and try again",
                CommunicationError,
                "Request failed due to the following error: "
                "`The supplied duplicate policy is invalid. Please provide a valid policy and try again`. "
                "Please try again later.",
            ),
            (
                "Insufficient balance for job submission",
                CommunicationError,
                "Request failed due to the following error: "
                "`Insufficient balance for job submission`. "
                "Please try again later.",
            ),
            (
                "",
                CommunicationError,
                "Request failed due to unknown issues. Please try again later.",
            ),
        ],
    )
    def test_handle_grpc_error(self, fxt_grpc_client, error_msg, expected_exc, expected_error_msg) -> None:
        # Arrange

        error = grpc.RpcError()
        error.details = lambda: error_msg  # type: ignore[method-assign]
        error.code = lambda: grpc.StatusCode.INVALID_ARGUMENT  # type: ignore[method-assign]
        mocked_submit = fxt_grpc_client.job_service_stub.submit
        mocked_submit.side_effect = error

        # Act
        with pytest.raises(expected_exc) as client_error:
            fxt_grpc_client.submit(
                priority=1,
                job_name="test_job",
                job_type="train",
                key=job_key,
                payload=payload,
                metadata=metadata,
                duplicate_policy="replace",
                author=ID("dummy_user"),
                project_id=project_id,
                cancellable=True,
            )

        # Assert
        assert str(client_error.value) == (expected_error_msg or error_msg)
