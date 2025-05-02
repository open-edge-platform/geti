#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#
from unittest.mock import patch

import pytest

from sc_sdk.entities.active_model_state import ActiveModelState
from sc_sdk.repos import ActiveModelStateRepo


class TestActiveModelStateRepo:
    def test_indexes(self, fxt_project_identifier) -> None:
        active_model_state_repo = ActiveModelStateRepo(fxt_project_identifier)

        indexes_names = set(active_model_state_repo._collection.index_information().keys())

        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1__id_1",
        }

    def test_get_by_task_node_id(self, fxt_active_model_state_repo, fxt_active_model_state) -> None:
        # Arrange
        repo = fxt_active_model_state_repo
        task_node_id = fxt_active_model_state.task_node_id

        # Act
        with patch.object(repo, "get_by_id", return_value=fxt_active_model_state) as mock_get_by_id:
            active_model_state = repo.get_by_task_node_id(task_node_id=task_node_id)

        # Assert
        mock_get_by_id.assert_called_once_with(task_node_id)
        assert active_model_state == fxt_active_model_state

    def test_delete_by_task_node_id(self, fxt_active_model_state_repo, fxt_active_model_state) -> None:
        # Arrange
        repo = fxt_active_model_state_repo
        task_node_id = fxt_active_model_state.task_node_id

        # Act
        with patch.object(repo, "delete_by_id") as mock_delete_by_id:
            repo.delete_by_task_node_id(task_node_id=task_node_id)

        # Assert
        mock_delete_by_id.assert_called_once_with(task_node_id)

    @pytest.fixture
    def fxt_active_model_state(self, fxt_ote_id, fxt_model_storage_classification):
        yield ActiveModelState(
            task_node_id=fxt_ote_id(11),
            active_model_storage=fxt_model_storage_classification,
        )

    @pytest.fixture
    def fxt_active_model_state_repo(self, fxt_empty_project_persisted):
        repo = ActiveModelStateRepo(fxt_empty_project_persisted.identifier)
        yield repo
