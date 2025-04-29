# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

from repos.reference_feature_repo import ReferenceFeatureRepo
from services.kafka_handler import VPSKafkaHandler

from geti_kafka_tools import KafkaRawMessage
from sc_sdk.entities.label_schema import NullLabelSchema
from sc_sdk.entities.model import NullModel
from sc_sdk.entities.model_template import TaskType
from sc_sdk.repos import DatasetRepo, LabelSchemaRepo, ModelRepo, ModelStorageRepo, ProjectRepo, TaskNodeRepo


class TestVPSKafkaHandler:
    @pytest.mark.parametrize("label_schema_in_sync", [True, False])
    def test_on_project_updated(self, label_schema_in_sync, fxt_project, fxt_ote_id, fxt_label_schema):
        # Arrange
        raw_message = KafkaRawMessage(
            topic="project_updates",
            partition=0,
            offset=0,
            timestamp=int(datetime.now().timestamp()),
            timestamp_type=0,
            key="",
            value={
                "workspace_id": fxt_project.identifier.workspace_id,
                "project_id": fxt_project.id_,
            },
            headers=[
                ("organization_id", b"000000000000000000000001"),
                ("workspace_id", b"63b183d00000000000000001"),
                ("source", b"browser"),
            ],
        )
        mock_model_storage = MagicMock()
        mock_model_storage.model_template.task_type = TaskType.VISUAL_PROMPTING
        mock_model_storage.task_node_id = fxt_ote_id(1)
        mock_model_storage.id_ = fxt_ote_id(10)
        mock_model = MagicMock()
        mock_model.id_ = fxt_ote_id(11)
        mock_model.label_schema_id = fxt_ote_id(100)
        mock_model.train_dataset_id = fxt_ote_id(101)

        # Act
        with (
            patch.object(
                LabelSchemaRepo,
                "get_latest_view_by_task",
                return_value=fxt_label_schema,
            ),
            patch.object(
                VPSKafkaHandler,
                "_compare_labels_sync_status",
                return_value=label_schema_in_sync,
            ) as mock_compare_labels_sync_status,
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project),
            patch.object(TaskNodeRepo, "get_trainable_task_ids", return_value=[fxt_ote_id(1)]),
            patch.object(ModelStorageRepo, "get_all", return_value=[mock_model_storage]),
            patch.object(
                ModelStorageRepo, "delete_by_id", return_value=[mock_model_storage]
            ) as mock_delete_model_storage,
            patch.object(ModelRepo, "get_one", return_value=mock_model) as mock_get_model,
            patch.object(ModelRepo, "delete_all") as mock_delete_model,
            patch.object(ReferenceFeatureRepo, "delete_all_by_task_id") as mock_delete_ref_features_by_task_id,
            patch.object(DatasetRepo, "delete_by_id") as mock_delete_dataset,
            patch("services.kafka_handler.isinstance", return_value=False) as mock_isinstance,
        ):
            VPSKafkaHandler.on_project_updated(raw_message)

        # Assert
        mock_get_model.assert_called_once()
        mock_isinstance.assert_has_calls(
            [
                call(fxt_label_schema, NullLabelSchema),
                call(mock_model, NullModel),
            ]
        )
        mock_compare_labels_sync_status.assert_called_once_with(
            project_identifier=fxt_project.identifier,
            label_schema_1=fxt_label_schema,
            label_schema_id_2=mock_model.label_schema_id,
        )
        if label_schema_in_sync:  # Deletion is not needed when label schema is in sync
            mock_delete_ref_features_by_task_id.assert_not_called()
            mock_delete_dataset.assert_not_called()
            mock_delete_model.assert_not_called()
            mock_delete_model_storage.assert_not_called()
        else:
            mock_delete_ref_features_by_task_id.assert_called_once_with(task_id=mock_model_storage.task_node_id)
            mock_delete_dataset.assert_called_once_with(mock_model.train_dataset_id)
            mock_delete_model.assert_called_once()
            mock_delete_model_storage.assert_called_once_with(mock_model_storage.id_)

    def test_on_project_deleted(self, fxt_project_identifier) -> None:
        raw_message = KafkaRawMessage(
            topic="project_deletions",
            partition=0,
            offset=0,
            timestamp=int(datetime.now().timestamp()),
            timestamp_type=0,
            key="",
            value={
                "workspace_id": fxt_project_identifier.workspace_id,
                "project_id": fxt_project_identifier.project_id,
            },
            headers=[
                ("organization_id", b"000000000000000000000001"),
                ("workspace_id", b"63b183d00000000000000001"),
                ("source", b"browser"),
            ],
        )

        with patch.object(ReferenceFeatureRepo, "delete_all") as mock_delete_all_ref_features:
            VPSKafkaHandler.on_project_deleted(raw_message)

        mock_delete_all_ref_features.assert_called_once_with()
