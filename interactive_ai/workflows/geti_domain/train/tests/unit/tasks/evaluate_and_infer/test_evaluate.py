# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
"""This module tests evaluate task"""

import os
from unittest.mock import MagicMock, call, patch

import pytest
from geti_types import ID, DatasetStorageIdentifier
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.utils.exceptions import EmptyEvaluationDatasetException
from sc_sdk.entities.annotation import AnnotationSceneKind
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.entities.evaluation_result import EvaluationPurpose
from sc_sdk.entities.model_storage import ModelStorage, ModelStorageIdentifier
from sc_sdk.entities.subset import Subset
from sc_sdk.repos import DatasetRepo, ModelRepo
from sc_sdk.utils.dataset_helper import DatasetHelper

from job.tasks.evaluate_and_infer.evaluate import evaluate
from job.utils.train_workflow_data import TrainWorkflowData
from tests.unit.tasks.utils import TEST_ENV_VARS, return_none


@pytest.mark.JobsComponent
class TestEvaluateTask:
    dataset_id = "dataset_id"
    base_model_id = "base_model_id"
    mo_model_id = "mo_model_id"
    train_dataset_id = "train_dataset_id"

    @patch.dict(os.environ, TEST_ENV_VARS)
    @pytest.mark.parametrize("subset", [Subset.TESTING, Subset.VALIDATION, Subset.TRAINING])
    @patch.object(DatasetRepo, "get_by_id")
    @patch.object(TrainWorkflowData, "get_model_storage")
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch.object(DatasetRepo, "__init__", new=return_none)
    def test_evaluate_empty_dataset(
        self,
        mocked_get_entities,
        mocked_get_model_storage,
        mocked_dr_get_by_id,
        fxt_task_node,
        fxt_train_data,
        subset,
    ) -> None:
        # Arrange
        mock_project = MagicMock()
        mock_dataset = MagicMock()
        mock_dataset_storage = MagicMock(spec=DatasetStorage)
        mock_dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        mock_dataset_storage.identifier = mock_dataset_storage_identifier

        mocked_get_entities.return_value = (mock_project, fxt_task_node)
        mocked_get_model_storage.return_value = MagicMock()
        mocked_dr_get_by_id.return_value = mock_dataset

        mock_project.get_training_dataset_storage.return_value = mock_dataset_storage
        mock_validation_dataset = MagicMock()
        mock_testing_dataset = MagicMock()
        mock_train_dataset = MagicMock()
        mock_train_dataset.__len__.return_value = 1
        mock_testing_dataset.__len__.return_value = 1
        mock_validation_dataset.__len__.return_value = 1
        subsets = {
            Subset.VALIDATION: mock_validation_dataset,
            Subset.TRAINING: mock_train_dataset,
            Subset.TESTING: mock_testing_dataset,
        }
        mock_dataset.get_subset.side_effect = lambda sub: subsets[sub]

        subsets[subset].__len__.return_value = 0
        expected_exc = RuntimeError if subset == Subset.TRAINING else EmptyEvaluationDatasetException

        train_data = fxt_train_data()

        progress_callback = MagicMock()

        # Act
        with pytest.raises(expected_exc):
            evaluate(
                train_data=train_data,
                dataset_id=self.dataset_id,
                base_model_id=self.base_model_id,
                mo_model_id=self.mo_model_id,
                progress_callback=progress_callback,
            )

        # Assert
        mocked_get_entities.assert_called_once_with()
        mocked_get_model_storage.assert_called_once_with()
        mock_project.get_training_dataset_storage.assert_called_once_with()
        mocked_dr_get_by_id.assert_called_once_with(ID(self.dataset_id))
        mock_dataset.get_subset.assert_called_with(subset)

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(ModelRepo, "get_by_id")
    @patch.object(DatasetRepo, "get_by_id")
    @patch.object(TrainWorkflowData, "get_model_storage")
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch.object(ModelRepo, "__init__", new=return_none)
    @patch.object(DatasetRepo, "__init__", new=return_none)
    def test_evaluate_no_weights(
        self,
        mocked_get_entities,
        mocked_get_model_storage,
        mocked_dr_get_by_id,
        mocked_mr_get_by_id,
        fxt_task_node,
        fxt_train_data,
    ) -> None:
        # Arrange
        mock_project = MagicMock()
        mock_dataset = MagicMock()
        mock_base_model = MagicMock()
        mock_mo_model = MagicMock()
        mock_dataset_storage = MagicMock(spec=DatasetStorage)
        mock_dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        mock_dataset_storage.identifier = mock_dataset_storage_identifier
        mock_model_storage = MagicMock(spec=ModelStorage)
        mock_model_storage_identifier = MagicMock(spec=ModelStorageIdentifier)
        mock_model_storage.identifier = mock_model_storage_identifier

        mocked_get_entities.return_value = (mock_project, fxt_task_node)
        mocked_get_model_storage.return_value = mock_model_storage
        mocked_dr_get_by_id.return_value = mock_dataset

        mock_project.get_training_dataset_storage.return_value = mock_dataset_storage
        mock_validation_dataset = MagicMock()
        mock_testing_dataset = MagicMock()
        mock_train_dataset = MagicMock()
        mock_train_dataset.__len__.return_value = 1
        mock_testing_dataset.__len__.return_value = 1
        mock_validation_dataset.__len__.return_value = 1
        subsets = {
            Subset.VALIDATION: mock_validation_dataset,
            Subset.TRAINING: mock_train_dataset,
            Subset.TESTING: mock_testing_dataset,
        }
        mock_dataset.get_subset.side_effect = lambda sub: subsets[sub]

        models = {
            self.base_model_id: mock_base_model,
            self.mo_model_id: mock_mo_model,
        }
        mocked_mr_get_by_id.side_effect = lambda id_: models[id_]
        mock_base_model.has_trained_weights.return_value = False

        train_data = fxt_train_data()

        progress_callback = MagicMock()

        # Act
        is_model_improved, train_dataset_id = evaluate(
            train_data=train_data,
            dataset_id=self.dataset_id,
            base_model_id=self.base_model_id,
            mo_model_id=self.mo_model_id,
            progress_callback=progress_callback,
        )

        # Assert
        assert is_model_improved is False
        assert train_dataset_id == ""
        mocked_get_entities.assert_called_once_with()
        mocked_get_model_storage.assert_called_once_with()
        mock_project.get_training_dataset_storage.assert_called_once_with()
        mocked_dr_get_by_id.assert_called_once_with(ID(self.dataset_id))
        progress_callback.assert_called_once_with(100, "Model doesn't have weights, skipping.")
        mocked_mr_get_by_id.assert_has_calls([call(ID(self.base_model_id)), call(ID(self.mo_model_id))])

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(DatasetHelper, "create_dataset_with_filtered_annotations_up_to_task")
    @patch.object(ModelRepo, "get_by_id")
    @patch.object(DatasetRepo, "get_by_id")
    @patch.object(TrainWorkflowData, "get_model_storage")
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch("job.tasks.evaluate_and_infer.evaluate.infer_and_evaluate")
    @patch("job.tasks.evaluate_and_infer.evaluate.check_model_improvement")
    @patch.object(ModelRepo, "__init__", new=return_none)
    @patch.object(DatasetRepo, "__init__", new=return_none)
    def test_evaluate(
        self,
        mocked_check_improvement,
        mocked_evaluate_task,
        mocked_get_entities,
        mocked_get_model_storage,
        mocked_dr_get_by_id,
        mocked_mr_get_by_id,
        mocked_create_dataset,
        fxt_train_data,
    ) -> None:
        # Arrange
        mock_project = MagicMock()
        mock_task_node = MagicMock()
        mock_dataset = MagicMock()
        mock_base_model = MagicMock()
        mock_mo_model = MagicMock()
        mock_active_model = MagicMock()
        train_output_dataset = MagicMock(spec=Dataset, id_=self.train_dataset_id)
        mock_dataset_storage = MagicMock(spec=DatasetStorage)
        mock_dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        mock_dataset_storage.identifier = mock_dataset_storage_identifier
        mock_model_storage = MagicMock(spec=ModelStorage)
        mock_model_storage_identifier = MagicMock(spec=ModelStorageIdentifier)
        mock_model_storage.identifier = mock_model_storage_identifier

        mocked_get_entities.return_value = (mock_project, mock_task_node)
        mocked_get_model_storage.return_value = mock_model_storage
        mocked_dr_get_by_id.return_value = mock_dataset
        mocked_check_improvement.return_value = True

        mock_project.get_training_dataset_storage.return_value = mock_dataset_storage
        mock_validation_dataset = MagicMock()
        mock_testing_dataset = MagicMock()
        mock_train_dataset = MagicMock()
        mock_train_dataset.__len__.return_value = 1
        mock_testing_dataset.__len__.return_value = 1
        mock_validation_dataset.__len__.return_value = 1
        subsets = {
            Subset.VALIDATION: mock_validation_dataset,
            Subset.TRAINING: mock_train_dataset,
            Subset.TESTING: mock_testing_dataset,
        }
        mock_dataset.get_subset.side_effect = lambda sub: subsets[sub]
        train_data = fxt_train_data()
        models = {
            self.base_model_id: mock_base_model,
            self.mo_model_id: mock_mo_model,
            train_data.active_model_id: mock_active_model,
        }
        mocked_mr_get_by_id.side_effect = lambda id_: models[id_]
        mock_base_model.has_trained_weights.return_value = True

        progress_callback = MagicMock()

        batch_inference_datasets = [
            # Inference on training subset to generate active learning metadata
            BatchInferenceDataset(
                dataset_storage=mock_dataset_storage,
                input_dataset=DatasetHelper.create_dataset_with_filtered_annotations_up_to_task(
                    input_dataset=mock_train_dataset,
                    task_node=mock_task_node,
                    project=mock_project,
                    dataset_storage=mock_dataset_storage,
                    annotation_scene_kind=AnnotationSceneKind.INTERMEDIATE,
                    save_to_db=True,
                ),
                output_dataset_purpose=DatasetPurpose.TASK_INFERENCE,
            ),
            # Evaluation on validation subset
            BatchInferenceDataset(
                dataset_storage=mock_dataset_storage,
                input_dataset=DatasetHelper.create_dataset_with_filtered_annotations_up_to_task(
                    input_dataset=mock_validation_dataset,
                    task_node=mock_task_node,
                    project=mock_project,
                    dataset_storage=mock_dataset_storage,
                    annotation_scene_kind=AnnotationSceneKind.INTERMEDIATE,
                    save_to_db=True,
                ),
                annotated_dataset=mock_validation_dataset,
                output_dataset_purpose=DatasetPurpose.EVALUATION,
                evaluation_purpose=EvaluationPurpose.VALIDATION,
            ),
            # Evaluation on test subset
            BatchInferenceDataset(
                dataset_storage=mock_dataset_storage,
                input_dataset=DatasetHelper.create_dataset_with_filtered_annotations_up_to_task(
                    input_dataset=mock_testing_dataset,
                    task_node=mock_task_node,
                    project=mock_project,
                    dataset_storage=mock_dataset_storage,
                    annotation_scene_kind=AnnotationSceneKind.INTERMEDIATE,
                    save_to_db=True,
                ),
                annotated_dataset=mock_testing_dataset,
                output_dataset_purpose=DatasetPurpose.EVALUATION,
                evaluation_purpose=EvaluationPurpose.TEST,
            ),
        ]

        # Act
        with patch(
            "job.tasks.evaluate_and_infer.evaluate.next",
            return_value=train_output_dataset.id_,
        ):
            is_model_improved, train_dataset_id = evaluate(
                train_data=train_data,
                dataset_id=self.dataset_id,
                base_model_id=self.base_model_id,
                mo_model_id=self.mo_model_id,
                progress_callback=progress_callback,
            )

        # Assert
        assert is_model_improved is True
        assert train_dataset_id == self.train_dataset_id
        mocked_get_entities.assert_called_once_with()
        mocked_get_model_storage.assert_called_once_with()
        mock_project.get_training_dataset_storage.assert_called_once_with()
        mocked_dr_get_by_id.assert_called_once_with(ID(self.dataset_id))
        mocked_mr_get_by_id.assert_has_calls(
            [call(ID(self.base_model_id)), call(ID(self.mo_model_id)), call(ID(train_data.active_model_id))]
        )
        progress_callback.assert_has_calls(
            [
                call(100, "Model is evaluated, checking improvement"),  # type: ignore
                call(100, "Model is evaluated"),  # type: ignore
            ]
        )
        mocked_evaluate_task.assert_called_once_with(
            project_identifier=mock_project.identifier,
            task_node=mock_task_node,
            model=mock_mo_model,
            batch_inference_datasets=batch_inference_datasets,
            progress_callback=progress_callback,
            progress_message="Evaluating the model",
        )
