# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests train workflow data class"""

from unittest.mock import MagicMock, patch

import pytest
from geti_types import ID
from iai_core.entities.label_schema import LabelSchemaView
from iai_core.entities.model_storage import ModelStorage, ModelStorageIdentifier
from iai_core.entities.project import Project
from iai_core.entities.task_node import TaskNode
from iai_core.repos import LabelSchemaRepo, ModelRepo, ModelStorageRepo, ProjectRepo, TaskNodeRepo

from tests.unit.tasks.utils import return_none


@pytest.mark.JobsComponent
class TestTrainWorkflowDataTask:
    @patch.object(ProjectRepo, "get_by_id")
    @patch.object(TaskNodeRepo, "get_by_id")
    @patch.object(ProjectRepo, "__init__", new=return_none)
    @patch.object(TaskNodeRepo, "__init__", new=return_none)
    def test_get_common_entities(self, mocked_get_task, mocked_get_project, fxt_train_data):
        # Arrange
        train_data = fxt_train_data()
        mock_project = MagicMock(spec=Project)
        mock_task_node = MagicMock(spec=TaskNode)

        mocked_get_project.return_value = mock_project
        mocked_get_task.return_value = mock_task_node

        # Act
        project, task_node = train_data.get_common_entities()

        # Assert
        mocked_get_project.assert_called_once_with(ID(train_data.project_id))
        mocked_get_task.assert_called_once_with(ID(train_data.task_id))
        assert (project, task_node) == (mock_project, mock_task_node)

    @patch.object(LabelSchemaRepo, "get_by_id")
    @patch.object(LabelSchemaRepo, "__init__", new=return_none)
    def test_get_label_schema(self, mocked_get_label_schema, fxt_train_data):
        # Arrange
        train_data = fxt_train_data()
        mock_label_schema = MagicMock(spec=LabelSchemaView)

        mocked_get_label_schema.return_value = mock_label_schema

        # Act
        label_schema = train_data.get_label_schema()

        # Assert
        mocked_get_label_schema.assert_called_once_with(ID(train_data.label_schema_id))
        assert label_schema == mock_label_schema

    @patch.object(ModelStorageRepo, "get_by_id")
    @patch.object(ModelStorageRepo, "__init__", new=return_none)
    def test_get_model_storage(self, mocked_get_model_storage, fxt_train_data):
        # Arrange
        train_data = fxt_train_data()
        mock_model_storage = MagicMock(spec=ModelStorage)

        mocked_get_model_storage.return_value = mock_model_storage

        # Act
        model_storage = train_data.get_model_storage()

        # Assert
        mocked_get_model_storage.assert_called_once_with(ID(train_data.model_storage_id))
        assert model_storage == mock_model_storage

    @pytest.mark.parametrize("input_model_id", [None, "input_model_id"])
    @patch.object(ModelRepo, "get_by_id")
    @patch.object(ModelStorageRepo, "get_by_id")
    @patch.object(ModelRepo, "__init__", new=return_none)
    @patch.object(ModelStorageRepo, "__init__", new=return_none)
    def test_get_input_model(self, mocked_get_model_storage, mocked_get_model, fxt_train_data, input_model_id):
        # Arrange
        train_data = fxt_train_data(input_model_id=input_model_id)
        mock_model_storage = MagicMock(spec=ModelStorage)
        mock_model_storage_identifier = MagicMock(spec=ModelStorageIdentifier)
        mock_model_storage.identifier = mock_model_storage_identifier
        mock_input_model = MagicMock()

        mocked_get_model_storage.return_value = mock_model_storage
        mocked_get_model.return_value = mock_input_model

        # Act
        input_model = train_data.get_input_model()

        # Assert
        mocked_get_model_storage.assert_called_once_with(ID(train_data.model_storage_id))
        if input_model_id is not None:
            assert mock_input_model == input_model
        else:
            assert input_model is None
