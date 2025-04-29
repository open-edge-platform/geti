# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests the pre-evaluate task"""

import os
from unittest.mock import MagicMock, patch

import pytest
from geti_types import ID
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.utils.exceptions import EmptyEvaluationDatasetException
from sc_sdk.entities.annotation import AnnotationSceneKind
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.entities.evaluation_result import EvaluationPurpose
from sc_sdk.entities.subset import Subset
from sc_sdk.repos import DatasetRepo, ModelRepo, ModelStorageRepo
from sc_sdk.utils.dataset_helper import DatasetHelper

from job.tasks.evaluate_and_infer.pre_evaluate import pre_evaluate
from job.utils.train_workflow_data import TrainWorkflowData
from tests.unit.tasks.utils import TEST_ENV_VARS, return_none


@pytest.mark.JobsComponent
class TestPreEvaluateTask:
    @pytest.fixture
    def mock_dataset(self):
        dataset = MagicMock(spec=Dataset)
        dataset.id_ = ID("dataset_id")
        dataset.__len__.return_value = 10
        return dataset

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch.object(DatasetRepo, "__init__", new=return_none)
    @patch.object(ModelRepo, "__init__", new=return_none)
    @patch.object(ModelStorageRepo, "__init__", new=return_none)
    def test_pre_evaluate_empty_validation_dataset(
        self,
        mocked_get_entities,
        mock_dataset,
        fxt_task_node,
        fxt_dataset_storage,
        fxt_train_data,
    ) -> None:
        # Arrange
        mock_project = MagicMock()
        mocked_get_entities.return_value = (mock_project, fxt_task_node)

        mock_project.get_training_dataset_storage.return_value = fxt_dataset_storage

        model_to_preevaluate = MagicMock()

        validation_dataset = MagicMock()
        validation_dataset.__len__.return_value = 0
        mock_dataset.get_subset.return_value = validation_dataset
        train_data = fxt_train_data()

        progress_callback = MagicMock()

        # Act
        with pytest.raises(EmptyEvaluationDatasetException):
            pre_evaluate(
                train_data=train_data,
                dataset=mock_dataset,
                model_to_preevaluate=model_to_preevaluate,
                progress_callback=progress_callback,
            )

        # Assert
        mock_project.get_training_dataset_storage.assert_called_once_with()
        mock_dataset.get_subset.assert_called_once_with(Subset.VALIDATION)

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(DatasetHelper, "create_dataset_with_filtered_annotations_up_to_task")
    @patch("job.tasks.evaluate_and_infer.pre_evaluate.infer_and_evaluate")
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch.object(DatasetRepo, "__init__", new=return_none)
    @patch.object(ModelRepo, "__init__", new=return_none)
    @patch.object(ModelStorageRepo, "__init__", new=return_none)
    def test_pre_evaluate_not_empty_validation_dataset(
        self,
        mocked_get_entities,
        mock_infer_and_evaluate_task,
        mocked_create_filtered_dataset,
        mock_dataset,
        fxt_task_node,
        fxt_dataset_storage,
        fxt_train_data,
    ) -> None:
        # Arrange
        mock_dataset = MagicMock()
        mock_project = MagicMock()
        mocked_get_entities.return_value = (mock_project, fxt_task_node)
        mock_project.get_training_dataset_storage.return_value = fxt_dataset_storage

        model_to_preevaluate = MagicMock()

        input_dataset = MagicMock()
        validation_dataset = MagicMock()
        validation_dataset.__len__.return_value = 1
        mocked_create_filtered_dataset.return_value = input_dataset
        mock_dataset.get_subset.return_value = validation_dataset

        train_data = fxt_train_data()

        progress_callback = MagicMock()

        # Act
        pre_evaluate(
            train_data=train_data,
            dataset=mock_dataset,
            model_to_preevaluate=model_to_preevaluate,
            progress_callback=progress_callback,
        )

        # Assert
        mock_project.get_training_dataset_storage.assert_called_once_with()
        mock_dataset.get_subset.assert_called_once_with(Subset.VALIDATION)
        mocked_create_filtered_dataset.assert_called_once_with(
            input_dataset=validation_dataset,
            task_node=fxt_task_node,
            project=mock_project,
            dataset_storage=fxt_dataset_storage,
            annotation_scene_kind=AnnotationSceneKind.INTERMEDIATE,
            save_to_db=False,
        )
        mock_infer_and_evaluate_task.assert_called_once_with(
            project_identifier=mock_project.identifier,
            task_node=fxt_task_node,
            model=model_to_preevaluate,
            # assumption: all the elements are in the same subset
            batch_inference_datasets=[
                BatchInferenceDataset(
                    dataset_storage=fxt_dataset_storage,
                    input_dataset=input_dataset,
                    annotated_dataset=validation_dataset,
                    output_dataset_purpose=DatasetPurpose.EVALUATION,
                    evaluation_purpose=EvaluationPurpose.PREEVALUATION,
                )
            ],
            progress_message="Pre-evaluating on validation dataset",
            progress_callback=progress_callback,
        )
