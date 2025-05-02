# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests task inference task"""

import os
from unittest.mock import ANY, MagicMock, patch

import pytest
from geti_types import ID
from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.datasets import Dataset, DatasetPurpose
from iai_core_py.entities.model_storage import ModelStorage, ModelStorageIdentifier
from iai_core_py.repos import ModelRepo
from jobs_common.utils.dataset_helpers import DatasetHelpers
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.tasks.infer_and_evaluate import BATCH_INFERENCE_NUM_ASYNC_REQUESTS

from job.tasks.evaluate_and_infer.pipeline_infer_on_unannotated import MAX_UNANNOTATED_MEDIA
from job.tasks.evaluate_and_infer.task_infer_on_unannotated import task_infer_on_unannotated
from job.utils.train_workflow_data import TrainWorkflowData
from tests.unit.tasks.utils import TEST_ENV_VARS, return_none


@pytest.mark.JobsComponent
class TestTaskInferenceTask:
    training_dataset_id = "dataset_id"
    train_subset_id = "train_subset_id"
    model_id = "model_id"

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(DatasetHelpers, "get_unannotated_dataset_for_task")
    @patch.object(ModelRepo, "get_by_id")
    @patch.object(TrainWorkflowData, "get_model_storage")
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch.object(ModelRepo, "__init__", new=return_none)
    def test_task_inference_empty_dataset(
        self,
        mocked_get_entities,
        mocked_get_model_storage,
        mocked_mr_get_by_id,
        mocked_get_unannotated_dataset,
        fxt_train_data,
    ) -> None:
        # Arrange
        mock_project = MagicMock()
        mock_task_node_1 = MagicMock()
        mock_task_node_2 = MagicMock()
        tasks_list = [mock_task_node_1, mock_task_node_2]
        mock_model_storage = MagicMock(spec=ModelStorage)
        mock_model_storage_identifier = MagicMock(spec=ModelStorageIdentifier)
        mock_model_storage.identifier = mock_model_storage_identifier
        mock_dataset_storage = MagicMock(spec=DatasetStorage)
        mock_model = MagicMock()
        mock_dataset = MagicMock(spec=Dataset)
        mock_dataset.__len__.return_value = 0

        mock_project.get_training_dataset_storage.return_value = mock_dataset_storage
        mock_project.get_trainable_task_nodes.return_value = tasks_list

        mocked_get_entities.return_value = (mock_project, mock_task_node_1)
        mocked_get_model_storage.return_value = mock_model_storage
        mocked_mr_get_by_id.return_value = mock_model
        mocked_get_unannotated_dataset.return_value = mock_dataset
        train_data = fxt_train_data()

        progress_callback = MagicMock()

        # Act
        task_infer_on_unannotated(
            train_data=train_data,
            training_dataset_id=self.training_dataset_id,
            train_inference_subset_id=self.train_subset_id,
            model_id=self.model_id,
            progress_callback=progress_callback,
        )

        # Assert
        mocked_get_entities.assert_called_once_with()
        mocked_get_model_storage.assert_called_once_with()
        mocked_mr_get_by_id.assert_called_once_with(ID(self.model_id))
        mocked_get_unannotated_dataset(
            project=mock_project,
            dataset_storage=mock_dataset_storage,
            task_node=mock_task_node_1,
            max_dataset_size=MAX_UNANNOTATED_MEDIA,
        )
        progress_callback.assert_called_once_with(
            100, "All media are already annotated, no predictions need to be generated"
        )

    @patch.dict(os.environ, TEST_ENV_VARS)
    @pytest.mark.parametrize("first_task", [True, False])
    @patch("job.tasks.evaluate_and_infer.task_infer_on_unannotated.publish_event")
    @patch("job.tasks.evaluate_and_infer.task_infer_on_unannotated.BatchInference")
    @patch.object(DatasetHelpers, "get_unannotated_dataset_for_task")
    @patch.object(ModelRepo, "get_by_id")
    @patch.object(TrainWorkflowData, "get_model_storage")
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch.object(ModelRepo, "__init__", new=return_none)
    def test_task_inference(
        self,
        mocked_get_entities,
        mocked_get_model_storage,
        mocked_mr_get_by_id,
        mocked_get_unannotated_dataset,
        mocked_batch_inference_init,
        mocked_publish_event,
        fxt_train_data,
        first_task,
    ) -> None:
        # Arrange
        mock_batch_inference = MagicMock()
        mock_project = MagicMock()
        mock_task_node_1 = MagicMock()
        mock_task_node_2 = MagicMock()
        tasks_list = [mock_task_node_1, mock_task_node_2]
        if not first_task:
            tasks_list.reverse()
        mock_model_storage = MagicMock(spec=ModelStorage)
        mock_model_storage_identifier = MagicMock(spec=ModelStorageIdentifier)
        mock_model_storage.identifier = mock_model_storage_identifier
        mock_dataset_storage = MagicMock(spec=DatasetStorage)
        mock_model = MagicMock()
        mock_dataset = MagicMock(spec=Dataset)
        mock_dataset.__len__.return_value = 10

        mock_project.get_training_dataset_storage.return_value = mock_dataset_storage
        mock_project.get_trainable_task_nodes.return_value = tasks_list

        mocked_get_entities.return_value = (mock_project, mock_task_node_1)
        mocked_get_model_storage.return_value = mock_model_storage
        mocked_mr_get_by_id.return_value = mock_model
        mocked_get_unannotated_dataset.return_value = mock_dataset
        mocked_batch_inference_init.return_value = mock_batch_inference
        train_data = fxt_train_data()

        progress_callback = MagicMock()

        # Act
        task_infer_on_unannotated(
            train_data=train_data,
            training_dataset_id=self.training_dataset_id,
            train_inference_subset_id=self.train_subset_id,
            model_id=self.model_id,
            progress_callback=progress_callback,
        )

        # Assert
        mocked_get_entities.assert_called_once_with()
        mocked_get_model_storage.assert_called_once_with()
        mocked_mr_get_by_id.assert_called_once_with(ID(self.model_id))
        mocked_get_unannotated_dataset(
            project=mock_project,
            dataset_storage=mock_dataset_storage,
            task_node=mock_task_node_1,
            max_dataset_size=MAX_UNANNOTATED_MEDIA,
        )
        mocked_batch_inference_init.assert_called_once_with(
            project_identifier=mock_project.identifier,
            task_node=mock_task_node_1,
            model=mock_model,
            batch_inference_datasets=[
                BatchInferenceDataset(
                    dataset_storage=mock_dataset_storage,
                    input_dataset=mock_dataset,
                    output_dataset_purpose=DatasetPurpose.INFERENCE if first_task else DatasetPurpose.TASK_INFERENCE,
                )
            ],
            progress_callback=progress_callback,
            progress_message="Generating task-level predictions on unannotated media",
            max_async_requests=BATCH_INFERENCE_NUM_ASYNC_REQUESTS,
        )
        mocked_publish_event.assert_called_once_with(
            topic="predictions_and_metadata_created",
            body={
                "workspace_id": train_data.workspace_id,
                "project_id": train_data.project_id,
                "dataset_storage_id": str(mock_project.training_dataset_storage_id),
                "task_node_id": train_data.task_id,
                "model_storage_id": train_data.model_storage_id,
                "model_id": self.model_id,
                "annotated_dataset_id": self.training_dataset_id,
                "train_dataset_with_predictions_id": self.train_subset_id,
                "unannotated_dataset_with_predictions_id": str(mock_batch_inference.output_datasets[0].id_),
            },
            key=str(mock_project.id_).encode(),
            headers_getter=ANY,
        )
        progress_callback.assert_called_once_with(
            100, "Finished generating task-level predictions on unannotated media"
        )
