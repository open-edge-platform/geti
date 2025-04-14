# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from grpc import RpcError

from controller import AUTO_TRAIN_AUTHOR, AutoTrainController, last_job_submission_time
from entities import AutoTrainActivationRequest, NullAutoTrainActivationRequest
from exceptions import InvalidAutoTrainRequestError, JobSubmissionError
from job_creation_helpers import TRAIN_JOB_PRIORITY, TrainTaskJobData
from repo import SessionBasedAutoTrainActivationRepo

from geti_types import Session
from grpc_interfaces.job_submission.client import GRPCJobsClient
from grpc_interfaces.job_submission.pb.job_service_pb2 import SubmitJobRequest
from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.configuration.elements.dataset_manager_parameters import DatasetManagementConfig
from sc_sdk.entities.model_storage import NullModelStorage
from sc_sdk.entities.model_template import ModelTemplateDeprecationStatus, TaskFamily, TaskType
from sc_sdk.entities.project import NullProject, Project
from sc_sdk.entities.task_node import TaskNode, TaskProperties
from sc_sdk.repos import ConfigurableParametersRepo, ModelStorageRepo, ProjectRepo, TaskNodeRepo
from sc_sdk.utils.time_utils import now

MOCK_JOBS_CLIENT = MagicMock()


def return_none(*args, **kwargs) -> None:
    return None


@pytest.fixture
def fxt_auto_train_controller():
    with patch.object(GRPCJobsClient, "__init__", new=return_none):
        controller = AutoTrainController(
            debouncing_period=10, jobs_grpc_client_address="clientaddress", job_submission_cooldown=60
        )
        controller._jobs_client = MOCK_JOBS_CLIENT
        yield controller


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


@pytest.fixture
def fxt_task_node(fxt_empty_project):
    detection_properties = TaskProperties(
        task_family=TaskFamily.VISION,
        task_type=TaskType.DETECTION,
        is_trainable=True,
        is_global=False,
        is_anomaly=False,
    )
    yield TaskNode(
        title="Test task",
        task_properties=detection_properties,
        project_id=fxt_empty_project.id_,
        id_=TaskNodeRepo.generate_id(),
        ephemeral=False,
    )


@pytest.mark.AutoTrainControllerComponent
class TestAutoTrainController:
    @pytest.mark.freeze_time("2024-1-1 0:0:11")
    def test_find_ready_request(self, fxt_auto_train_controller, fxt_auto_train_activation_request) -> None:
        with patch.object(
            SessionBasedAutoTrainActivationRepo,
            "get_one_ready",
            return_value=fxt_auto_train_activation_request,
        ) as mock_get_one_ready:
            result = fxt_auto_train_controller.find_ready_request()

        mock_get_one_ready.assert_called_once_with(
            latest_timestamp=now() - timedelta(seconds=fxt_auto_train_controller.debounce_period)
        )
        assert result == fxt_auto_train_activation_request

    @pytest.mark.freeze_time("2024-1-1 0:0:11")
    def test_find_ready_request_during_cooldown(
        self, fxt_auto_train_controller, fxt_auto_train_activation_request
    ) -> None:
        task_id = fxt_auto_train_activation_request.task_node_id
        last_job_submission_time[task_id] = now() - timedelta(seconds=10)  # simulate a job submission 10 seconds ago
        with (
            patch.object(
                SessionBasedAutoTrainActivationRepo,
                "get_one_ready",
                return_value=fxt_auto_train_activation_request,
            ) as mock_get_one_ready,
            patch.object(fxt_auto_train_controller, "remove_request_by_task") as mock_remove_request_by_task,
        ):
            result = fxt_auto_train_controller.find_ready_request()

        mock_get_one_ready.assert_called_once_with(
            latest_timestamp=now() - timedelta(seconds=fxt_auto_train_controller.debounce_period)
        )
        mock_remove_request_by_task.assert_called_once_with(task_node_id=task_id)
        assert isinstance(result, NullAutoTrainActivationRequest)

    def test_submit_train_job(
        self,
        fxt_auto_train_controller,
        fxt_auto_train_activation_request,
        fxt_empty_project,
        fxt_model_storage,
        fxt_task_node,
    ) -> None:
        # Arrange
        dummy_dataset_config = MagicMock()
        dummy_train_job_key = "dummy_job_key"
        dummy_train_job_payload = "dummy_job_payload"
        dummy_train_job_metadata = "dummy_job_metadata"

        # Act
        with (
            patch.object(
                ConfigurableParametersRepo, "get_or_create_component_parameters", return_value=dummy_dataset_config
            ) as mock_get_dataset_config,
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project) as mock_get_project,
            patch.object(
                Project, "get_trainable_task_node_by_id", return_value=fxt_task_node
            ) as mock_get_trainable_task_node,
            patch.object(ModelStorageRepo, "get_by_id", return_value=fxt_model_storage),
            patch.object(TrainTaskJobData, "create_key", return_value=dummy_train_job_key),
            patch.object(TrainTaskJobData, "create_payload", return_value=dummy_train_job_payload),
            patch.object(TrainTaskJobData, "create_metadata", return_value=dummy_train_job_metadata),
            patch.object(AutoTrainController, "get_num_dataset_items", return_value=0),
        ):
            fxt_auto_train_controller.submit_train_job(fxt_auto_train_activation_request)

        # Assert
        mock_get_dataset_config.assert_called_once_with(
            data_instance_of=DatasetManagementConfig,
            component=ComponentType.PIPELINE_DATASET_MANAGER,
        )
        mock_get_project.assert_called_once_with(fxt_auto_train_activation_request.project_id)
        mock_get_trainable_task_node.assert_called_once_with(task_id=fxt_auto_train_activation_request.task_node_id)
        MOCK_JOBS_CLIENT.submit.assert_called_with(
            priority=TRAIN_JOB_PRIORITY,
            cost=[SubmitJobRequest.CostRequest(unit="images")],
            job_name="Training",
            job_type="train",
            key=dummy_train_job_key,
            payload=dummy_train_job_payload,
            metadata=dummy_train_job_metadata,
            duplicate_policy="replace",
            author=AUTO_TRAIN_AUTHOR,
            project_id=fxt_auto_train_activation_request.project_id,
            gpu_num_required=1,
            cancellable=True,
        )

    def test_submit_train_job_project_not_found(
        self,
        fxt_auto_train_controller,
        fxt_auto_train_activation_request,
    ) -> None:
        dummy_dataset_config = MagicMock()
        with (
            patch.object(
                ConfigurableParametersRepo, "get_or_create_component_parameters", return_value=dummy_dataset_config
            ),
            patch.object(ProjectRepo, "get_by_id", return_value=NullProject()),
            pytest.raises(InvalidAutoTrainRequestError),
        ):
            fxt_auto_train_controller.submit_train_job(fxt_auto_train_activation_request)

    def test_submit_train_job_model_storage_not_found(
        self,
        fxt_auto_train_controller,
        fxt_auto_train_activation_request,
        fxt_empty_project,
    ) -> None:
        dummy_dataset_config = MagicMock()
        with (
            patch.object(
                ConfigurableParametersRepo, "get_or_create_component_parameters", return_value=dummy_dataset_config
            ),
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
            patch.object(Project, "get_trainable_task_node_by_id", return_value=fxt_task_node),
            patch.object(ModelStorageRepo, "get_by_id", return_value=NullModelStorage()),
            pytest.raises(InvalidAutoTrainRequestError),
        ):
            fxt_auto_train_controller.submit_train_job(fxt_auto_train_activation_request)

    def test_submit_train_job_no_model_storage_in_request(
        self,
        fxt_auto_train_controller,
        fxt_auto_train_activation_request,
        fxt_empty_project,
    ) -> None:
        dummy_dataset_config = MagicMock()
        fxt_auto_train_activation_request.model_storage_id = None
        with (
            patch.object(
                ConfigurableParametersRepo, "get_or_create_component_parameters", return_value=dummy_dataset_config
            ),
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
            patch.object(Project, "get_trainable_task_node_by_id", return_value=fxt_task_node),
            pytest.raises(InvalidAutoTrainRequestError),
        ):
            fxt_auto_train_controller.submit_train_job(fxt_auto_train_activation_request)

    def test_submit_train_job_obsolete_model_template(
        self,
        fxt_auto_train_controller,
        fxt_auto_train_activation_request,
        fxt_empty_project,
        fxt_task_node,
        fxt_model_storage,
    ) -> None:
        dummy_dataset_config = MagicMock()
        fxt_model_storage.model_template.model_status = ModelTemplateDeprecationStatus.OBSOLETE
        # Act
        with (
            patch.object(
                ConfigurableParametersRepo, "get_or_create_component_parameters", return_value=dummy_dataset_config
            ),
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
            patch.object(Project, "get_trainable_task_node_by_id", return_value=fxt_task_node),
            patch.object(ModelStorageRepo, "get_by_id", return_value=fxt_model_storage),
            pytest.raises(InvalidAutoTrainRequestError),
        ):
            fxt_auto_train_controller.submit_train_job(fxt_auto_train_activation_request)

    def test_submit_train_job_grpc_error(
        self,
        fxt_auto_train_controller,
        fxt_auto_train_activation_request,
        fxt_empty_project,
        fxt_model_storage,
    ) -> None:
        dummy_dataset_config = MagicMock()
        dummy_train_job_key = "dummy_job_key"
        dummy_train_job_payload = "dummy_job_payload"
        dummy_train_job_metadata = "dummy_job_metadata"
        with (
            patch.object(
                ConfigurableParametersRepo, "get_or_create_component_parameters", return_value=dummy_dataset_config
            ),
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
            patch.object(Project, "get_trainable_task_node_by_id", return_value=fxt_task_node),
            patch.object(ModelStorageRepo, "get_by_id", return_value=fxt_model_storage),
            patch.object(TrainTaskJobData, "create_key", return_value=dummy_train_job_key),
            patch.object(TrainTaskJobData, "create_payload", return_value=dummy_train_job_payload),
            patch.object(TrainTaskJobData, "create_metadata", return_value=dummy_train_job_metadata),
            patch.object(AutoTrainController, "get_num_dataset_items", return_value=0),
            patch.object(fxt_auto_train_controller._jobs_client, "submit", side_effect=RpcError),
            pytest.raises(JobSubmissionError),
        ):
            fxt_auto_train_controller.submit_train_job(fxt_auto_train_activation_request)

    def test_remove_request_by_task(self, fxt_ote_id, fxt_auto_train_controller) -> None:
        task_node_id = fxt_ote_id(100)
        with patch.object(
            SessionBasedAutoTrainActivationRepo,
            "delete_by_task_node_id",
            return_value=None,
        ) as mock_delete_by_task_node_id:
            fxt_auto_train_controller.remove_request_by_task(task_node_id=task_node_id)

        mock_delete_by_task_node_id.assert_called_once_with(task_node_id=task_node_id)
