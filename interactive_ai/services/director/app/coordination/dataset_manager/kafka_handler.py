# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

from service.project_service import ProjectService

from .dataset_counter import DatasetCounterUseCase
from .dataset_suspender import DatasetSuspender
from .dataset_update import DatasetUpdateUseCase
from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_telemetry_tools import unified_tracing
from geti_types import ID, Singleton
from sc_sdk.session.session_propagation import setup_session_kafka


class DatasetManagementMediaAndAnnotationKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """KafkaHandler for dataset management media and annotation scene use cases. Bursty operation."""

    def __init__(self) -> None:
        super().__init__(group_id="dataset_management_media_annotation_events")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="media_deletions", callback=self.on_media_deleted),
            TopicSubscription(topic="annotation_scenes_to_revisit", callback=self.on_annotations_suspended),
            TopicSubscription(topic="new_annotation_scene", callback=self.on_new_annotation_scene),
        ]

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_annotations_suspended(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        workspace_id = ID(value["workspace_id"])
        project_id = ID(value["project_id"])
        dataset_storage_id = ID(value["dataset_storage_id"])
        suspended_scenes_descriptor_id = ID(value["suspended_scenes_descriptor_id"])

        is_training_dataset_storage = ProjectService.is_training_dataset_storage_id(
            project_id=project_id, dataset_storage_id=dataset_storage_id
        )

        # We only consider messages relative to the 'training' dataset storage because
        # it is the only one whose dataset is built incrementally.
        # The datasets of other storages are instead constructed from scratch when
        # requested, so they do not need to be updated here.
        if is_training_dataset_storage:
            DatasetSuspender.suspend_dataset_items(
                workspace_id=workspace_id,
                project_id=project_id,
                suspended_scenes_descriptor_id=suspended_scenes_descriptor_id,
            )

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_new_annotation_scene(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        project_id = ID(value["project_id"])
        dataset_storage_id = ID(value["dataset_storage_id"])
        annotation_scene_id = ID(value["annotation_scene_id"])
        is_training_dataset_storage = ProjectService.is_training_dataset_storage_id(
            project_id=project_id, dataset_storage_id=dataset_storage_id
        )

        if is_training_dataset_storage:
            DatasetUpdateUseCase.update_dataset_with_new_annotation_scene(
                project_id=project_id,
                annotation_scene_id=annotation_scene_id,
            )

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_media_deleted(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        project_id = ID(value["project_id"])
        dataset_storage_id = ID(value["dataset_storage_id"])
        media_id = ID(value["media_id"])

        is_training_dataset_storage = ProjectService.is_training_dataset_storage_id(
            project_id=project_id, dataset_storage_id=dataset_storage_id
        )

        if is_training_dataset_storage:
            DatasetUpdateUseCase.delete_media_from_datasets(
                project_id=project_id,
                media_id=media_id,
            )


class DatasetManagementDatasetUpdatedKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """KafkaHandler for dataset management dataset updated use case. Bursty operation."""

    def __init__(self) -> None:
        super().__init__(group_id="dataset_management_dataset_updated")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="dataset_updated", callback=self.on_dataset_updated),
        ]

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_dataset_updated(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        DatasetCounterUseCase.on_dataset_update(
            workspace_id=ID(value["workspace_id"]),
            project_id=ID(value["project_id"]),
            task_node_id=ID(value["task_node_id"]),
            dataset_id=ID(value["dataset_id"]),
            new_dataset_items=[ID(dataset_item) for dataset_item in value["new_dataset_items"]],
            deleted_dataset_items=[ID(dataset_item) for dataset_item in value["deleted_dataset_items"]],
            assigned_dataset_items=[ID(dataset_item) for dataset_item in value["assigned_dataset_items"]],
        )


class DatasetManagementProjectEventsKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """KafkaHandler for dataset management for project events use cases."""

    def __init__(self) -> None:
        super().__init__(group_id="dataset_management_project_events")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="project_creations", callback=self.on_project_created),
            TopicSubscription(topic="project_updates", callback=self.on_project_updated),
        ]

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_project_created(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        DatasetCounterUseCase.on_project_create(
            workspace_id=ID(value["workspace_id"]), project_id=ID(value["project_id"])
        )

    @staticmethod
    @setup_session_kafka
    @unified_tracing
    def on_project_updated(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        DatasetCounterUseCase.on_project_update(
            workspace_id=ID(value["workspace_id"]), project_id=ID(value["project_id"])
        )
