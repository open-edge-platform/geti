# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import datetime
from unittest.mock import patch

import pytest

from coordination.dataset_manager.dataset_counter import DatasetCounterUseCase
from coordination.dataset_manager.dataset_suspender import DatasetSuspender
from coordination.dataset_manager.dataset_update import DatasetUpdateUseCase
from coordination.dataset_manager.kafka_handler import (
    DatasetManagementDatasetUpdatedKafkaHandler,
    DatasetManagementMediaAndAnnotationKafkaHandler,
    DatasetManagementProjectEventsKafkaHandler,
)
from service.project_service import ProjectService

from geti_kafka_tools import KafkaRawMessage


@pytest.fixture
def fxt_consumer_record():
    def _build_consumer_record(value: dict):
        return KafkaRawMessage(
            topic="test_topic",
            partition=0,
            offset=0,
            timestamp=int(datetime.datetime.now().timestamp()),
            timestamp_type=0,
            key="",
            value=value,
            headers=[],
        )

    return _build_consumer_record


class TestDatasetManagementKafkaHandler:
    def test_on_annotations_suspended(self, fxt_consumer_record, fxt_mongo_id) -> None:
        raw_message = fxt_consumer_record(
            value={
                "suspended_scenes_descriptor_id": str(fxt_mongo_id(0)),
                "workspace_id": str(fxt_mongo_id(1)),
                "project_id": str(fxt_mongo_id(2)),
                "dataset_storage_id": str(fxt_mongo_id(3)),
            }
        )
        with (
            patch.object(ProjectService, "is_training_dataset_storage_id", return_value=True),
            patch.object(DatasetSuspender, "suspend_dataset_items", return_value=None) as mock_suspend_dataset_items,
        ):
            DatasetManagementMediaAndAnnotationKafkaHandler.on_annotations_suspended(raw_message=raw_message)

            mock_suspend_dataset_items.assert_called_once_with(
                suspended_scenes_descriptor_id=fxt_mongo_id(0),
                workspace_id=fxt_mongo_id(1),
                project_id=fxt_mongo_id(2),
            )

    def test_on_dataset_updated(self, fxt_consumer_record, fxt_mongo_id) -> None:
        raw_message = fxt_consumer_record(
            value={
                "workspace_id": str(fxt_mongo_id(0)),
                "project_id": str(fxt_mongo_id(1)),
                "task_node_id": str(fxt_mongo_id(2)),
                "dataset_id": str(fxt_mongo_id(3)),
                "new_dataset_items": [str(fxt_mongo_id(4))],
                "deleted_dataset_items": [str(fxt_mongo_id(5))],
                "assigned_dataset_items": [str(fxt_mongo_id(6))],
            }
        )
        with patch.object(DatasetCounterUseCase, "on_dataset_update", return_value=None) as mock_suspend_dataset_items:
            DatasetManagementDatasetUpdatedKafkaHandler.on_dataset_updated(raw_message=raw_message)

            mock_suspend_dataset_items.assert_called_once_with(
                workspace_id=fxt_mongo_id(0),
                project_id=fxt_mongo_id(1),
                task_node_id=fxt_mongo_id(2),
                dataset_id=fxt_mongo_id(3),
                new_dataset_items=[fxt_mongo_id(4)],
                deleted_dataset_items=[fxt_mongo_id(5)],
                assigned_dataset_items=[fxt_mongo_id(6)],
            )

    def test_on_media_deleted_training_ds(self, fxt_consumer_record, fxt_mongo_id) -> None:
        raw_message = fxt_consumer_record(
            value={
                "workspace_id": str(fxt_mongo_id(0)),
                "project_id": str(fxt_mongo_id(1)),
                "dataset_storage_id": str(fxt_mongo_id(2)),
                "media_id": str(fxt_mongo_id(3)),
            }
        )
        with (
            patch.object(ProjectService, "is_training_dataset_storage_id", return_value=True) as mock_is_training_ds,
            patch.object(DatasetUpdateUseCase, "delete_media_from_datasets", return_value=None) as mock_delete_media,
        ):
            DatasetManagementMediaAndAnnotationKafkaHandler.on_media_deleted(raw_message=raw_message)

            mock_is_training_ds.assert_called_once_with(
                project_id=fxt_mongo_id(1),
                dataset_storage_id=fxt_mongo_id(2),
            )
            mock_delete_media.assert_called_once_with(
                project_id=fxt_mongo_id(1),
                media_id=fxt_mongo_id(3),
            )

    def test_on_media_deleted_non_training_ds(self, fxt_consumer_record, fxt_mongo_id) -> None:
        raw_message = fxt_consumer_record(
            value={
                "workspace_id": str(fxt_mongo_id(0)),
                "project_id": str(fxt_mongo_id(1)),
                "dataset_storage_id": str(fxt_mongo_id(2)),
                "media_id": str(fxt_mongo_id(3)),
            }
        )
        with (
            patch.object(ProjectService, "is_training_dataset_storage_id", return_value=False) as mock_is_training_ds,
            patch.object(DatasetUpdateUseCase, "delete_media_from_datasets", return_value=None) as mock_delete_media,
        ):
            DatasetManagementMediaAndAnnotationKafkaHandler.on_media_deleted(raw_message=raw_message)

            mock_is_training_ds.assert_called_once_with(
                project_id=fxt_mongo_id(1),
                dataset_storage_id=fxt_mongo_id(2),
            )
            mock_delete_media.assert_not_called()

    def test_on_new_annotation_scene_training_ds(self, fxt_consumer_record, fxt_mongo_id) -> None:
        raw_message = fxt_consumer_record(
            value={
                "workspace_id": str(fxt_mongo_id(0)),
                "project_id": str(fxt_mongo_id(1)),
                "dataset_storage_id": str(fxt_mongo_id(2)),
                "annotation_scene_id": str(fxt_mongo_id(3)),
                "empty_annotation_for_new_media": False,
            }
        )
        with (
            patch.object(ProjectService, "is_training_dataset_storage_id", return_value=True) as mock_is_training_ds,
            patch.object(
                DatasetUpdateUseCase,
                "update_dataset_with_new_annotation_scene",
                return_value=None,
            ) as mock_update_dataset,
        ):
            DatasetManagementMediaAndAnnotationKafkaHandler.on_new_annotation_scene(raw_message=raw_message)

            mock_is_training_ds.assert_called_once_with(
                project_id=fxt_mongo_id(1),
                dataset_storage_id=fxt_mongo_id(2),
            )
            mock_update_dataset.assert_called_once_with(
                project_id=fxt_mongo_id(1),
                annotation_scene_id=fxt_mongo_id(3),
            )

    def test_on_new_annotation_scene_non_training_ds(self, fxt_consumer_record, fxt_mongo_id) -> None:
        raw_message = fxt_consumer_record(
            value={
                "workspace_id": str(fxt_mongo_id(0)),
                "project_id": str(fxt_mongo_id(1)),
                "dataset_storage_id": str(fxt_mongo_id(2)),
                "annotation_scene_id": str(fxt_mongo_id(3)),
                "empty_annotation_for_new_media": True,
            }
        )
        with (
            patch.object(ProjectService, "is_training_dataset_storage_id", return_value=False) as mock_is_training_ds,
            patch.object(
                DatasetUpdateUseCase,
                "update_dataset_with_new_annotation_scene",
                return_value=None,
            ) as mock_update_dataset,
        ):
            DatasetManagementMediaAndAnnotationKafkaHandler.on_new_annotation_scene(raw_message=raw_message)

            mock_is_training_ds.assert_called_once_with(
                project_id=fxt_mongo_id(1),
                dataset_storage_id=fxt_mongo_id(2),
            )
            mock_update_dataset.assert_not_called()

    def test_on_project_created(self, fxt_consumer_record, fxt_mongo_id) -> None:
        raw_message = fxt_consumer_record(
            value={
                "workspace_id": str(fxt_mongo_id(0)),
                "project_id": str(fxt_mongo_id(1)),
            }
        )
        with patch.object(DatasetCounterUseCase, "on_project_create", return_value=None) as mock_on_project_create:
            DatasetManagementProjectEventsKafkaHandler.on_project_created(raw_message=raw_message)

            mock_on_project_create.assert_called_once_with(workspace_id=fxt_mongo_id(0), project_id=fxt_mongo_id(1))

    def test_on_project_updated(self, fxt_consumer_record, fxt_mongo_id) -> None:
        raw_message = fxt_consumer_record(
            value={
                "workspace_id": str(fxt_mongo_id(0)),
                "project_id": str(fxt_mongo_id(1)),
            }
        )
        with patch.object(DatasetCounterUseCase, "on_project_update", return_value=None) as mock_on_project_update:
            DatasetManagementProjectEventsKafkaHandler.on_project_updated(raw_message=raw_message)

            mock_on_project_update.assert_called_once_with(workspace_id=fxt_mongo_id(0), project_id=fxt_mongo_id(1))
