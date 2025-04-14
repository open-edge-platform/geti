# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from coordination.dataset_manager.dynamic_required_num_annotations import DynamicRequiredAnnotations

from .auto_train_use_case import AutoTrainUseCase
from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_telemetry_tools import unified_tracing
from geti_types import ID, ProjectIdentifier, Singleton
from sc_sdk.session.session_propagation import setup_session_kafka


class AutoTrainingKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """KafkaHandler for auto training use cases"""

    def __init__(self) -> None:
        super().__init__(group_id="auto_training_consumer")

        self.auto_train_use_case = AutoTrainUseCase()

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="configuration_changes", callback=self.on_configuration_changed),
            TopicSubscription(topic="dataset_counters_updated", callback=self.on_dataset_counters_updated),
            TopicSubscription(topic="training_successful", callback=self.on_training_successful),
            TopicSubscription(topic="model_activated", callback=self.on_model_activated),
        ]

    def stop(self) -> None:
        super().stop()
        self.auto_train_use_case.stop()

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
