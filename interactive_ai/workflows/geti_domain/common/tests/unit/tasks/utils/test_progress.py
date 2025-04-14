# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import datetime
from unittest.mock import ANY, MagicMock, call, patch

import pytest
from freezegun import freeze_time
from geti_types import ID
from grpc_interfaces.job_update.pb.job_update_service_pb2 import JobUpdateRequest

from jobs_common.exceptions import CommandInitializationFailedException, TaskErrorMessage
from jobs_common.tasks.utils.progress import (
    publish_consumed_resources,
    publish_metadata_update,
    release_gpu,
    report_progress,
    task_progress,
)
from jobs_common.tasks.utils.secrets import JobMetadata


@pytest.mark.JobsComponent
class TestProgress:
    @patch("jobs_common.tasks.utils.progress.publish_event")
    def test_report_progress_no_updates(self, mock_publish_event) -> None:
        # Arrange

        # Act
        report_progress()

        # Assert
        mock_publish_event.assert_not_called()

    @patch("jobs_common.tasks.utils.progress.publish_event")
    @patch("jobs_common.tasks.utils.progress.current_context")
    def test_report_progress_progress(self, mock_current_context, mock_publish_event) -> None:
        # Arrange
        context = MagicMock()
        context.execution_id.name = "execution_name"
        context.task_id.name = "task_name"
        mock_current_context.return_value = context

        # Act
        report_progress(progress=50)

        # Assert
        mock_publish_event.assert_called_once_with(
            topic="job_step_details",
            body={"execution_id": "execution_name", "task_id": "task_name", "progress": 50},
            key=b"execution_name-task_name",
            headers_getter=ANY,
        )

    @patch("jobs_common.tasks.utils.progress.publish_event")
    @patch("jobs_common.tasks.utils.progress.current_context")
    def test_report_progress_message(self, mock_current_context, mock_publish_event) -> None:
        # Arrange
        context = MagicMock()
        context.execution_id.name = "execution_name"
        context.task_id.name = "task_name"
        mock_current_context.return_value = context

        # Act
        report_progress(message="Test message")

        # Assert
        mock_publish_event.assert_called_once_with(
            topic="job_step_details",
            body={"execution_id": "execution_name", "task_id": "task_name", "message": "Test message"},
            key=b"execution_name-task_name",
            headers_getter=ANY,
        )

    @patch("jobs_common.tasks.utils.progress.publish_event")
    @patch("jobs_common.tasks.utils.progress.current_context")
    def test_report_progress_progress_and_message(self, mock_current_context, mock_publish_event) -> None:
        # Arrange
        context = MagicMock()
        context.execution_id.name = "execution_name"
        context.task_id.name = "task_name"
        mock_current_context.return_value = context

        # Act
        report_progress(progress=50, message="Test message")

        # Assert
        mock_publish_event.assert_called_once_with(
            topic="job_step_details",
            body={"execution_id": "execution_name", "task_id": "task_name", "progress": 50, "message": "Test message"},
            key=b"execution_name-task_name",
            headers_getter=ANY,
        )

    @patch("jobs_common.tasks.utils.progress.JobUpdateClient", autospec=True)
    @patch("jobs_common.tasks.utils.progress.current_context")
    def test_publish_metadata_update(self, mock_current_context, mock_job_update_client) -> None:
        # Arrange
        context = MagicMock()
        context.execution_id.name = "execution_name"
        context.task_id.name = "task_name"
        mock_current_context.return_value = context

        client = MagicMock()
        mock_job_update_client.return_value = client

        # Act
        publish_metadata_update(metadata={"foo": "bar"})

        # Assert
        mock_job_update_client.assert_called_once()
        client.job_update.assert_called_once_with(execution_id="execution_name", metadata={"foo": "bar"})

    @patch("jobs_common.tasks.utils.progress.JobUpdateClient", autospec=True)
    @patch("jobs_common.tasks.utils.progress.current_context")
    @freeze_time("2024-01-01 00:00:01")
    def test_publish_consumed_resources(self, mock_current_context, mock_job_update_client) -> None:
        # Arrange
        context = MagicMock()
        context.execution_id.name = "execution_name"
        context.task_id.name = "task_name"
        mock_current_context.return_value = context

        client = MagicMock()
        mock_job_update_client.return_value = client

        # Act
        publish_consumed_resources(amount=100, unit="images", service="training")

        # Assert
        mock_job_update_client.assert_called_once()
        client.job_update.assert_called_once_with(
            execution_id="execution_name",
            cost=JobUpdateRequest.Cost(
                consumed=[
                    JobUpdateRequest.Cost.Consumed(
                        amount=100, unit="images", consuming_date=1704067201, service="training"
                    )
                ]
            ),
        )

    @patch("jobs_common.tasks.utils.progress.JobUpdateClient", autospec=True)
    @patch("jobs_common.tasks.utils.progress.current_context")
    def test_release_gpu(self, mock_current_context, mock_job_update_client) -> None:
        # Arrange
        context = MagicMock()
        context.execution_id.name = "execution_name"
        context.task_id.name = "task_name"
        mock_current_context.return_value = context

        client = MagicMock()
        mock_job_update_client.return_value = client

        # Act
        release_gpu()

        # Assert
        mock_job_update_client.assert_called_once()
        client.job_update.assert_called_once_with(
            execution_id="execution_name",
            gpu=JobUpdateRequest.Gpu(action=JobUpdateRequest.Gpu.RELEASE),
        )

    @patch("jobs_common.tasks.utils.progress.report_progress")
    def test_task_progress_no_finish_message(self, mock_report_progress) -> None:
        # Arrange
        @task_progress(
            start_message="Starting test function", finish_message=None, failure_message="Test function failed"
        )
        def test_function():
            pass

        # Act
        test_function()

        # Assert
        mock_report_progress.assert_called_once_with(progress=-1, message="Starting test function")

    @patch("jobs_common.tasks.utils.progress.report_progress")
    def test_task_progress_finish_message(self, mock_report_progress) -> None:
        # Arrange
        @task_progress(
            start_message="Starting test function",
            finish_message="Test function finished",
            failure_message="Test function failed",
        )
        def test_function():
            pass

        # Act
        test_function()

        # Assert
        mock_report_progress.assert_has_calls(
            [
                call(progress=-1, message="Starting test function"),
                call(progress=100, message="Test function finished"),
            ]
        )

    @pytest.mark.parametrize(
        "exception, message",
        [
            (
                Exception("Failure"),
                "Test function failed (Code: Exception). Please retry or contact customer support if "
                "problem persists. (ID: job_id)",
            ),
            (
                CommandInitializationFailedException("Failure"),
                "Test function failed (Code: CommandInitializationFailedException). Please retry or contact customer "
                "support if problem persists. (ID: job_id)",
            ),
        ],
    )
    @patch.object(
        JobMetadata,
        "from_env_vars",
        return_value=JobMetadata(ID("job_id"), "test_job", "Test jobs", ID("author"), datetime.datetime.now()),
    )
    @patch("jobs_common.tasks.utils.progress.report_progress")
    def test_task_progress_failure_message(self, mock_report_progress, mock_from_env_vars, exception, message) -> None:
        # Arrange
        @task_progress(
            start_message="Starting test function", finish_message=None, failure_message="Test function failed"
        )
        def test_function():
            raise exception

        # Act
        with pytest.raises(Exception):
            test_function()

        # Assert
        mock_report_progress.assert_has_calls(
            [
                call(progress=-1, message="Starting test function"),
                call(message=message),
            ]
        )
        mock_from_env_vars.assert_called_once_with()

    @patch.object(
        JobMetadata,
        "from_env_vars",
        return_value=JobMetadata(ID("job_id"), "test_job", "Test jobs", ID("author"), datetime.datetime.now()),
    )
    @patch("jobs_common.tasks.utils.progress.report_progress")
    def test_task_progress_task_error_message(self, mock_report_progress, mock_from_env_vars) -> None:
        # Arrange

        class CustomException(Exception, TaskErrorMessage):
            def __init__(self) -> None:
                super().__init__("Exception message")

        @task_progress(
            start_message="Starting test function",
            finish_message=None,
            failure_message="Test function failed",
        )
        def test_function():
            raise CustomException

        # Act
        with pytest.raises(CustomException):
            test_function()

        # Assert
        mock_report_progress.assert_has_calls(
            [
                call(progress=-1, message="Starting test function"),
                call(message="Exception message (ID: job_id)"),
            ]
        )
        mock_from_env_vars.assert_called_once_with()
