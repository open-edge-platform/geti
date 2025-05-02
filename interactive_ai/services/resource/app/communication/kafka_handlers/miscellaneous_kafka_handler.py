# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging

from repos.mlflow_binary_repo import MLFlowBinaryRepo
from resource_management.ui_settings_manager import UISettingsManager
from usecases.update_project_performance_usecase import UpdateProjectPerformanceUseCase

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, ProjectIdentifier, Singleton
from grpc_interfaces.model_registration.client import ModelRegistrationClient
from iai_core.repos import VideoAnnotationRangeRepo
from iai_core.session.session_propagation import setup_session_kafka

logger = logging.getLogger(__name__)


class MiscellaneousKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """
    This class handles miscellaneous incoming Kafka events for the resource MS.
    """

    def __init__(self) -> None:
        super().__init__(group_id="miscellaneous_consumer")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="project_deletions", callback=self.on_project_deleted),
            TopicSubscription(topic="model_activated", callback=self.on_model_activated),
        ]

    @staticmethod
    @setup_session_kafka
    def on_model_activated(raw_message: KafkaRawMessage) -> None:
        data: dict = raw_message.value

        UpdateProjectPerformanceUseCase.update_project_performance(
            project_id=ID(data["project_id"]),
            task_node_id=ID(data["task_node_id"]),
            inference_model_id=ID(data["inference_model_id"]),
        )

    @staticmethod
    @setup_session_kafka
    def on_project_deleted(raw_message: KafkaRawMessage) -> None:
        """
        Event handler for when a project is deleted.
        The project manager is responsible for deleting resource entities.
        """
        value: dict = raw_message.value
        workspace_id = ID(value["workspace_id"])
        project_id = ID(value["project_id"])
        dataset_storage_id = ID(value["training_dataset_storage_id"])
        UISettingsManager.delete_ui_settings_by_project(project_id)
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )
        VideoAnnotationRangeRepo(dataset_storage_identifier).delete_all()
        with ModelRegistrationClient(metadata_getter=lambda: CTX_SESSION_VAR.get().as_tuple()) as client:
            client.delete_project_pipelines(project_id=project_id)

        project_identifier = ProjectIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
        )
        MLFlowBinaryRepo(identifier=project_identifier).delete_all_under_project_dir()
