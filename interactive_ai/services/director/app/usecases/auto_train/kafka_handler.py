# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import logging

from coordination.dataset_manager.dynamic_required_num_annotations import DynamicRequiredAnnotations
from environment import get_gpu_provider

from .auto_train_use_case import AutoTrainUseCase
from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_telemetry_tools import unified_tracing
from geti_types import ID, ProjectIdentifier, Singleton
from iai_core.algorithms import ModelTemplateList
from iai_core.repos import ProjectRepo
from iai_core.services import ModelService
from iai_core.session.session_propagation import setup_session_kafka

logger = logging.getLogger(__name__)


class AutoTrainingKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """KafkaHandler for auto training use cases"""

    def __init__(self) -> None:
        super().__init__(group_id="auto_training_consumer")

        self.auto_train_use_case = AutoTrainUseCase()

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        subs = [
            TopicSubscription(topic="configuration_changes", callback=self.on_configuration_changed),
            TopicSubscription(
                topic="dataset_counters_updated",
                callback=self.on_dataset_counters_updated,
            ),
            TopicSubscription(topic="training_successful", callback=self.on_training_successful),
            TopicSubscription(topic="model_activated", callback=self.on_model_activated),
        ]
        # Workaround (ITEP-67586): change some model defaults for Intel GPU
        # This is done by reconfiguring the active model immediately after project creation
        if get_gpu_provider() != "intel":
            subs.append(TopicSubscription(topic="project_creations", callback=self.on_project_created))
        return subs

    def stop(self) -> None:
        super().stop()
        self.auto_train_use_case.stop()

    @setup_session_kafka
    @unified_tracing
    def on_project_created(self, raw_message: KafkaRawMessage) -> None:
        # Workaround (ITEP-67586): change some model defaults for Intel GPU
        # This is done by reconfiguring the active model immediately after project creation
        value: dict = raw_message.value
        project_identifier = ProjectIdentifier(
            workspace_id=ID(value["workspace_id"]), project_id=ID(value["project_id"])
        )
        project = ProjectRepo().get_by_id(project_identifier.project_id)
        for task_node in project.get_trainable_task_nodes():
            task_type = task_node.task_properties.task_type
            try:
                default_model_template_id = next(
                    model_template.model_template_id
                    for model_template in ModelTemplateList().get_all()
                    if model_template.task_type == task_type and model_template.is_default_for_task
                )
            except StopIteration:
                logger.error("Could not resolve default model template for task type %s", task_type)
                return
            logger.info(
                "[WORKAROUND] Switching active model storage to '%s' for task '%s'",
                default_model_template_id,
                task_node,
            )
            model_storage = ModelService.get_or_create_model_storage(
                project_identifier=project_identifier,
                task_node=task_node,
                model_template_id=default_model_template_id,
            )
            ModelService.activate_model_storage(model_storage)

    @setup_session_kafka
    @unified_tracing
    def on_configuration_changed(self, raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        project_identifier = ProjectIdentifier(
            workspace_id=ID(value["workspace_id"]), project_id=ID(value["project_id"])
        )
        self.auto_train_use_case.on_configuration_changed(project_identifier=project_identifier)

    @setup_session_kafka
    @unified_tracing
    def on_dataset_counters_updated(self, raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        project_identifier = ProjectIdentifier(
            workspace_id=ID(value["workspace_id"]), project_id=ID(value["project_id"])
        )
        self.auto_train_use_case.on_dataset_counters_updated(project_identifier=project_identifier)

    @setup_session_kafka
    @unified_tracing
    def on_training_successful(self, raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        project_identifier = ProjectIdentifier(
            workspace_id=ID(value["workspace_id"]), project_id=ID(value["project_id"])
        )
        AutoTrainUseCase.on_training_successful(project_identifier=project_identifier)

    @setup_session_kafka
    @unified_tracing
    def on_model_activated(self, raw_message: KafkaRawMessage) -> None:
        message_data: dict = raw_message.value

        project_identifier = ProjectIdentifier(
            workspace_id=ID(message_data["workspace_id"]),
            project_id=ID(message_data["project_id"]),
        )
        task_node_id = ID(message_data["task_node_id"])

        DynamicRequiredAnnotations.on_model_activated(
            project_identifier=project_identifier,
            task_node_id=task_node_id,
        )
