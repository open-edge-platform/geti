# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
from datetime import datetime, timedelta
from unittest.mock import call, patch

import pytest
from bson import ObjectId

from entities import AutoTrainActivationRequest, NullAutoTrainActivationRequest
from main import run_controller_loop
from repo import SessionBasedAutoTrainActivationRepo

from geti_types import ID, ProjectIdentifier
from grpc_interfaces.job_submission.client import GRPCJobsClient
from grpc_interfaces.job_submission.pb.job_service_pb2 import SubmitJobRequest
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.project import Project
from iai_core.entities.task_graph import TaskEdge, TaskGraph
from iai_core.repos import (
    ConfigurableParametersRepo,
    DatasetRepo,
    DatasetStorageRepo,
    ModelStorageRepo,
    ProjectRepo,
    TaskNodeRepo,
)
from iai_core.repos.dataset_entity_repo import PipelineDatasetRepo
from iai_core.repos.mappers import DatetimeToMongo
from iai_core.utils.time_utils import now


def return_none(*args, **kwargs) -> None:
    return None


@pytest.fixture
def fxt_project_with_detection_task(request, fxt_ote_id, fxt_dataset_task, fxt_detection_task, fxt_session):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_dataset_task)
    task_graph.add_node(fxt_detection_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_dataset_task, to_task=fxt_detection_task))
    project_repo = ProjectRepo()
    project_id = fxt_ote_id(1000)
    request.addfinalizer(lambda: project_repo.delete_by_id(project_id))
    fxt_dataset_task.use_for_training = True
    project_identifier = ProjectIdentifier(workspace_id=fxt_session.workspace_id, project_id=project_id)
    dataset_storage_repo = DatasetStorageRepo(project_identifier)
    ds = DatasetStorage(
        name="test_dataset_storage",
        _id=DatasetStorageRepo.generate_id(),
        project_id=project_identifier.project_id,
        use_for_training=True,
    )
    request.addfinalizer(lambda: dataset_storage_repo.delete_all())
    dataset_storage_repo.save(ds)
    project = Project(
        name="dummy_detection_project",
        description="Sample project with a detection task",
        creator_id="",
        user_names=["alice", "bob"],
        dataset_storages=[ds],
        task_graph=task_graph,
        id=project_id,
    )
    project_repo.save(project)
    task_node_repo = TaskNodeRepo(project_identifier=project.identifier)
    request.addfinalizer(lambda: task_node_repo.delete_all())
    task_node_repo.save_many([fxt_dataset_task, fxt_detection_task])
    yield project


@pytest.fixture
def fxt_project_with_classification_task(request, fxt_ote_id, fxt_dataset_task, fxt_classification_task, fxt_session):
    task_graph = TaskGraph()
    task_graph.add_node(fxt_dataset_task)
    task_graph.add_node(fxt_classification_task)
    task_graph.add_task_edge(TaskEdge(from_task=fxt_dataset_task, to_task=fxt_classification_task))
    project_repo = ProjectRepo()
    project_id = fxt_ote_id(1001)
    request.addfinalizer(lambda: project_repo.delete_by_id(project_id))
    fxt_dataset_task.use_for_training = True
    project_identifier = ProjectIdentifier(workspace_id=fxt_session.workspace_id, project_id=project_id)
    dataset_storage_repo = DatasetStorageRepo(project_identifier)
    ds = DatasetStorage(
        name="test_dataset_storage",
        _id=DatasetStorageRepo.generate_id(),
        project_id=project_identifier.project_id,
        use_for_training=True,
    )
    request.addfinalizer(lambda: dataset_storage_repo.delete_all())
    dataset_storage_repo.save(ds)
    project = Project(
        name="dummy_classification_project",
        description="Sample project with a classification task",
        creator_id="",
        user_names=["alice", "bob"],
        dataset_storages=[ds],
        task_graph=task_graph,
        id=project_id,
    )
    project_repo.save(project)
    task_node_repo = TaskNodeRepo(project_identifier=project.identifier)
    request.addfinalizer(lambda: task_node_repo.delete_all())
    task_node_repo.save_many([fxt_dataset_task, fxt_classification_task])
    yield project


@pytest.fixture
def fxt_auto_train_activation_request_factory(request, fxt_session):
    session_doc = {
        "organization_id": ObjectId(fxt_session.organization_id),
        "workspace_id": ObjectId(fxt_session.workspace_id),
    }

    def _factory(
        task_id: ID,
        project_id: ID,
        model_storage_id: ID,
        timestamp: datetime,
        ready: bool,
    ):
        repo = SessionBasedAutoTrainActivationRepo()
        request.addfinalizer(lambda: repo.delete_all())
        repo._collection.insert_one(
            {
                "_id": ObjectId(task_id),
                "organization_id": session_doc["organization_id"],
                "workspace_id": session_doc["workspace_id"],
                "project_id": ObjectId(project_id),
                "model_storage_id": ObjectId(model_storage_id),
                "ready": ready,
                "request_time": DatetimeToMongo.forward(timestamp),
                "session": session_doc,
            }
        )

    yield _factory


class TestAutoTrainControllerLoopIntegration:
    @patch.object(GRPCJobsClient, "__init__", new=return_none)
    @patch.object(GRPCJobsClient, "submit", return_value=ID("submitted_job_id"))
    @patch.object(GRPCJobsClient, "close")
    def test_run_controller_loop_no_requests(
        self,
        mock_grpc_client_close,
        mock_grpc_client_submit,
        fxt_session,
    ) -> None:
        auto_train_repo = SessionBasedAutoTrainActivationRepo()
        ready_request = auto_train_repo.get_one_ready(latest_timestamp=now())
        assert isinstance(ready_request, NullAutoTrainActivationRequest)

        run_controller_loop()

        mock_grpc_client_submit.assert_not_called()
        mock_grpc_client_close.assert_not_called()

    @pytest.mark.freeze_time("2000-01-01")
    @patch.object(GRPCJobsClient, "__init__", new=return_none)
    @patch.object(GRPCJobsClient, "submit", return_value=ID("submitted_job_id"))
    @patch.object(GRPCJobsClient, "close")
    @patch.object(DatasetRepo, "count_items", return_value=12)
    @patch("main.AUTO_TRAIN_DEBOUNCING_PERIOD", 10)
    def test_run_controller_loop_process_requests(
        self,
        mock_dataset_repo_count_items,
        mock_grpc_client_close,
        mock_grpc_client_submit,
        request,
        fxt_auto_train_activation_request_factory,
        fxt_ote_id,
        fxt_project_with_detection_task,
        fxt_project_with_classification_task,
        fxt_model_storage_detection,
        fxt_model_storage_classification,
    ) -> None:
        # Arrange
        # - 2 ready request to be submitted
        # - 1 ready request but too early to be submitted
        # - 1 not ready request

        model_storage_repo_det = ModelStorageRepo(project_identifier=fxt_project_with_detection_task.identifier)
        model_storage_repo_clas = ModelStorageRepo(project_identifier=fxt_project_with_classification_task.identifier)
        request.addfinalizer(lambda: model_storage_repo_det.delete_all())
        request.addfinalizer(lambda: model_storage_repo_clas.delete_all())
        request.addfinalizer(
            lambda: ConfigurableParametersRepo(fxt_project_with_classification_task.identifier).delete_all()
        )
        request.addfinalizer(
            lambda: ConfigurableParametersRepo(fxt_project_with_detection_task.identifier).delete_all()
        )

        fxt_model_storage_detection.id_ = fxt_ote_id(1)
        fxt_model_storage_detection.workspace_id = fxt_project_with_detection_task.workspace_id
        fxt_model_storage_detection.project_id = fxt_project_with_detection_task.id_
        fxt_model_storage_classification.id_ = fxt_ote_id(2)
        fxt_model_storage_classification.workspace_id = fxt_project_with_classification_task.workspace_id
        fxt_model_storage_classification.project_id = fxt_project_with_classification_task.id_
        model_storage_repo_det.save(fxt_model_storage_detection)
        model_storage_repo_clas.save(fxt_model_storage_classification)
        detection_task = fxt_project_with_detection_task.get_trainable_task_nodes()[0]
        classification_task = fxt_project_with_classification_task.get_trainable_task_nodes()[0]
        PipelineDatasetRepo.get_or_create(fxt_project_with_detection_task.get_training_dataset_storage().identifier)
        PipelineDatasetRepo.get_or_create(
            fxt_project_with_classification_task.get_training_dataset_storage().identifier
        )

        fxt_auto_train_activation_request_factory(
            task_id=detection_task.id_,
            project_id=fxt_project_with_detection_task.id_,
            model_storage_id=fxt_model_storage_detection.id_,
            timestamp=now() - timedelta(seconds=11),
            ready=True,
        )
        fxt_auto_train_activation_request_factory(
            task_id=classification_task.id_,
            project_id=fxt_project_with_classification_task.id_,
            model_storage_id=fxt_model_storage_classification.id_,
            timestamp=now() - timedelta(seconds=15),
            ready=True,
        )
        fxt_auto_train_activation_request_factory(
            task_id=fxt_ote_id(21),
            project_id=fxt_ote_id(22),
            model_storage_id=fxt_ote_id(23),
            timestamp=now() - timedelta(seconds=5),
            ready=True,
        )
        fxt_auto_train_activation_request_factory(
            task_id=fxt_ote_id(31),
            project_id=fxt_ote_id(32),
            model_storage_id=fxt_ote_id(33),
            timestamp=now() - timedelta(seconds=20),
            ready=False,
        )
        auto_train_repo = SessionBasedAutoTrainActivationRepo()
        auto_train_request_1 = auto_train_repo.backward_map(
            auto_train_repo._collection.find_one({"_id": ObjectId(detection_task.id_)})
        )
        auto_train_request_2 = auto_train_repo.backward_map(
            auto_train_repo._collection.find_one({"_id": ObjectId(classification_task.id_)})
        )
        ready_request = auto_train_repo.get_one_ready(latest_timestamp=now() - timedelta(seconds=10))
        assert isinstance(ready_request, AutoTrainActivationRequest)

        # Act
        run_controller_loop()

        # Assert
        mock_grpc_client_submit.assert_has_calls(
            [
                call(
                    priority=1,
                    job_name="Training",
                    job_type="train",
                    key=json.dumps(
                        {
                            "model_storage_id": auto_train_request.model_storage_id,
                            "project_id": auto_train_request.project_id,
                            "task_id": auto_train_request.task_node_id,
                            "type": "train",
                            "workspace_id": auto_train_request.workspace_id,
                        }
                    ),
                    payload={
                        "project_id": str(auto_train_request.project_id),
                        "task_id": str(auto_train_request.task_node_id),
                        "from_scratch": False,
                        "reshuffle_subsets": False,
                        "should_activate_model": True,
                        "infer_on_pipeline": True,
                        "model_storage_id": str(auto_train_request.model_storage_id),
                        "hyper_parameters_id": "",
                        "enable_training_from_dataset_shard": True,
                        "max_training_dataset_size": 12,
                        "max_number_of_annotations": None,
                        "min_annotation_size": None,
                        "keep_mlflow_artifacts": False,
                    },
                    metadata={
                        "project": {
                            "id": auto_train_request.project_id,
                            "name": project.name,
                        },
                        "task": {
                            "dataset_storage_id": project.get_training_dataset_storage().id_,
                            "model_template_id": model_storage.model_template.model_template_id,
                            "model_architecture": model_storage.model_template.name,
                            "name": project.get_trainable_task_node_by_id(auto_train_request.task_node_id).title,
                            "task_id": auto_train_request.task_node_id,
                        },
                    },
                    duplicate_policy="replace",
                    author=ID("geti"),
                    cost=[SubmitJobRequest.CostRequest(unit="images", amount=12)],
                    project_id=auto_train_request.project_id,
                    gpu_num_required=1,
                    cancellable=True,
                )
                for auto_train_request, project, model_storage in [
                    (
                        auto_train_request_1,
                        fxt_project_with_detection_task,
                        fxt_model_storage_detection,
                    ),
                    (
                        auto_train_request_2,
                        fxt_project_with_classification_task,
                        fxt_model_storage_classification,
                    ),
                ]
            ]
        )
        mock_grpc_client_close.assert_called_once()
        ready_request = auto_train_repo.get_one_ready(latest_timestamp=now() - timedelta(seconds=10))
        assert isinstance(ready_request, NullAutoTrainActivationRequest)

    @pytest.mark.freeze_time("2000-01-01")
    @patch.object(GRPCJobsClient, "__init__", new=return_none)
    @patch.object(GRPCJobsClient, "submit", return_value=ID("submitted_job_id"))
    @patch.object(GRPCJobsClient, "close")
    @patch.object(DatasetRepo, "count_items", return_value=12)
    @patch("main.AUTO_TRAIN_DEBOUNCING_PERIOD", 10)
    @patch("main.AUTO_TRAIN_JOB_SUBMISSION_COOLDOWN", 60)
    def test_controller_loop_cooldown(
        self,
        mock_dataset_repo_count_items,
        mock_grpc_client_submit,
        request,
        fxt_auto_train_activation_request_factory,
        fxt_ote_id,
        fxt_project_with_detection_task,
        fxt_model_storage_detection,
    ) -> None:
        # Arrange
        import controller

        controller.last_job_submission_time = {}

        model_storage_repo_det = ModelStorageRepo(project_identifier=fxt_project_with_detection_task.identifier)
        request.addfinalizer(lambda: model_storage_repo_det.delete_all())
        request.addfinalizer(
            lambda: ConfigurableParametersRepo(fxt_project_with_detection_task.identifier).delete_all()
        )

        fxt_model_storage_detection.id_ = fxt_ote_id(1)
        fxt_model_storage_detection.workspace_id = fxt_project_with_detection_task.workspace_id
        fxt_model_storage_detection.project_id = fxt_project_with_detection_task.id_
        model_storage_repo_det.save(fxt_model_storage_detection)
        detection_task = fxt_project_with_detection_task.get_trainable_task_nodes()[0]
        PipelineDatasetRepo.get_or_create(fxt_project_with_detection_task.get_training_dataset_storage().identifier)

        # request #1
        fxt_auto_train_activation_request_factory(
            task_id=detection_task.id_,
            project_id=fxt_project_with_detection_task.id_,
            model_storage_id=fxt_model_storage_detection.id_,
            timestamp=now() - timedelta(seconds=31),
            ready=True,
        )

        # Act & assert
        run_controller_loop()

        # request #2, copy of #1, should be ignored during cooldown period
        fxt_auto_train_activation_request_factory(
            task_id=detection_task.id_,
            project_id=fxt_project_with_detection_task.id_,
            model_storage_id=fxt_model_storage_detection.id_,
            timestamp=now() - timedelta(seconds=30),
            ready=True,
        )

        run_controller_loop()

        # request #2 should have been discarded
        mock_grpc_client_submit.assert_called_once()
        activation_repo = SessionBasedAutoTrainActivationRepo()
        ready_request = activation_repo.get_one_ready(now() - timedelta(seconds=10))
        assert isinstance(ready_request, NullAutoTrainActivationRequest)
        assert controller.last_job_submission_time[detection_task.id_] == now()

        # after cooldown period, new auto-train requests are allowed to be submitted
        with patch.object(datetime, "now", return_value=now() + timedelta(seconds=80)):
            # request #3
            fxt_auto_train_activation_request_factory(
                task_id=detection_task.id_,
                project_id=fxt_project_with_detection_task.id_,
                model_storage_id=fxt_model_storage_detection.id_,
                timestamp=now() - timedelta(seconds=15),  # 80 - 15 - 60 = 5 seconds after end of cooldown
                ready=True,
            )
            run_controller_loop()

            # request #3 should have been submitted
            ready_request = activation_repo.get_one_ready(latest_timestamp=now() - timedelta(seconds=10))
            assert isinstance(ready_request, NullAutoTrainActivationRequest)
            assert controller.last_job_submission_time[detection_task.id_] == now()
