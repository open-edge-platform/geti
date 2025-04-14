# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from datetime import datetime
from unittest.mock import patch

import pytest

from controller import AutoTrainController
from entities import AutoTrainActivationRequest, NullAutoTrainActivationRequest
from exceptions import JobSubmissionError
from main import run_controller_loop

from geti_types import Session
from grpc_interfaces.job_submission.client import InsufficientBalanceException


@pytest.fixture
def fxt_auto_train_activation_request(fxt_ote_id):
    yield AutoTrainActivationRequest(
        project_id=fxt_ote_id(1),
        task_node_id=fxt_ote_id(2),
        model_storage_id=fxt_ote_id(3),
        timestamp=datetime(2024, 1, 1, 0, 0, 0),
        ready=True,
        bypass_debouncer=False,
        session=Session(
            organization_id=fxt_ote_id(10),
            workspace_id=fxt_ote_id(11),
        ),
    )


@pytest.mark.AutoTrainControllerComponent
class TestAutoTrainController:
    @pytest.mark.parametrize("submit_error", [False, True], ids=["Job successfully submitted", "Job submission error"])
    def test_run_controller_loop(self, submit_error, fxt_auto_train_activation_request) -> None:
        with (
            patch.object(
                AutoTrainController,
                "find_ready_request",
                side_effect=[fxt_auto_train_activation_request, NullAutoTrainActivationRequest()],
            ) as mock_find_request,
            patch.object(
                AutoTrainController, "submit_train_job", side_effect=JobSubmissionError() if submit_error else None
            ) as mock_submit_job,
            patch.object(AutoTrainController, "remove_request_by_task") as mock_remove_request,
        ):
            run_controller_loop()

        assert mock_find_request.call_count == 2
        mock_submit_job.assert_called_once_with(auto_train_request=fxt_auto_train_activation_request)
        mock_remove_request.assert_called_once_with(task_node_id=fxt_auto_train_activation_request.task_node_id)

    def test_run_controller_loop_insufficient_balance(self, fxt_auto_train_activation_request) -> None:
        with (
            patch.object(
                AutoTrainController,
                "find_ready_request",
                side_effect=[fxt_auto_train_activation_request, NullAutoTrainActivationRequest()],
            ) as mock_find_request,
            patch.object(
                AutoTrainController, "submit_train_job", side_effect=InsufficientBalanceException()
            ) as mock_submit_job,
            patch.object(AutoTrainController, "remove_request_by_task") as mock_remove_request,
        ):
            run_controller_loop()

        assert mock_find_request.call_count == 2
        mock_submit_job.assert_called_once_with(auto_train_request=fxt_auto_train_activation_request)
        mock_remove_request.assert_called_once_with(task_node_id=fxt_auto_train_activation_request.task_node_id)
