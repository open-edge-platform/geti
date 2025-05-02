# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests post model acceptance task"""

import os
from unittest.mock import ANY, MagicMock, call, patch

import pytest
from iai_core_py.entities.model_storage import ModelStorage, ModelStorageIdentifier
from iai_core_py.services import ModelService

from job.tasks.evaluate_and_infer.post_model_acceptance import activate_model_storage, post_model_acceptance
from job.utils.train_workflow_data import TrainWorkflowData
from tests.unit.tasks.utils import TEST_ENV_VARS


@pytest.mark.JobsComponent
class TestPostModelAcceptanceTask:
    model_id = "model_id"

    @pytest.mark.parametrize("old_id,new_id", [("id_1", "id_2"), ("id_3", "id_3")], ids=["Different ids", "Same id"])
    @patch.object(ModelService, "activate_model_storage")
    @patch.object(ModelService, "get_active_model_storage")
    def test_activate_model_storage(self, mocked_get_active_ms, mocked_activate_ms, old_id, new_id) -> None:
        # Arrange
        task_node_id = "task_node_id"
        mock_model_storage = MagicMock(spec=ModelStorage, task_node_id=task_node_id, id_=old_id)
        mock_old_model_storage = MagicMock(spec=ModelStorage, task_node_id=task_node_id, id_=new_id)

        mocked_get_active_ms.return_value = mock_old_model_storage
        # Act
        activate_model_storage(model_storage=mock_model_storage)

        # Assert
        if old_id != new_id:
            mocked_activate_ms.assert_called_once_with(model_storage=mock_model_storage)
        else:
            mocked_activate_ms.assert_not_called()

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch("job.tasks.evaluate_and_infer.post_model_acceptance.publish_metadata_update")
    @patch("job.tasks.evaluate_and_infer.post_model_acceptance.publish_event")
    @patch("job.tasks.evaluate_and_infer.post_model_acceptance.activate_model_storage")
    @patch.object(TrainWorkflowData, "get_model_storage")
    @patch.object(TrainWorkflowData, "get_common_entities")
    def test_post_model_acceptance(
        self,
        mocked_get_entities,
        mocked_get_model_storage,
        mocked_activate_model_storage,
        mocked_publish_event,
        mocked_publish_metadata_update,
        fxt_train_data,
    ) -> None:
        # Arrange
        mock_project = MagicMock()
        mock_task_node = MagicMock()
        mock_model_storage = MagicMock(spec=ModelStorage)
        mock_model_storage_identifier = MagicMock(spec=ModelStorageIdentifier)
        mock_model_storage.identifier = mock_model_storage_identifier

        mocked_get_entities.return_value = (mock_project, mock_task_node)
        mocked_get_model_storage.return_value = mock_model_storage
        train_data = fxt_train_data()

        # Act
        post_model_acceptance(train_data=train_data, base_model_id=self.model_id, inference_model_id=self.model_id)

        # Assert
        mocked_get_entities.assert_called_once_with()
        mocked_get_model_storage.assert_called_once_with()
        mocked_activate_model_storage.assert_called_once_with(model_storage=mock_model_storage)

        mocked_publish_event.assert_has_calls(
            [
                call(
                    topic="model_activated",
                    body={
                        "workspace_id": str(mock_project.workspace_id),
                        "project_id": str(mock_project.id_),
                        "task_node_id": str(mock_task_node.id_),
                        "model_storage_id": str(mock_model_storage.id_),
                        "base_model_id": str(self.model_id),
                        "inference_model_id": str(self.model_id),
                    },
                    headers_getter=ANY,
                ),
                call(
                    topic="training_successful",
                    body={
                        "workspace_id": str(mock_project.workspace_id),
                        "project_id": str(mock_project.id_),
                    },
                    key=str(mock_project.id_).encode(),
                    headers_getter=ANY,
                ),
            ]
        )
        mocked_publish_metadata_update.assert_called_once_with(
            metadata={
                "trained_model": {
                    "model_storage_id": str(mock_model_storage.id_),
                    "model_id": self.model_id,
                    "model_activated": True,
                }
            }
        )
