# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests pipeline infer task"""

import os
from unittest.mock import MagicMock, call, patch

import pytest
from geti_types import ID, DatasetStorageIdentifier
from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.datasets import Dataset, DatasetPurpose, NullDataset
from iai_core_py.entities.label_schema import LabelSchemaView
from iai_core_py.entities.model_storage import ModelStorage, ModelStorageIdentifier
from iai_core_py.entities.model_template import TaskFamily
from iai_core_py.entities.task_node import TaskNode
from iai_core_py.repos import DatasetRepo, LabelSchemaRepo, ModelRepo
from iai_core_py.services import ModelService
from iai_core_py.utils.dataset_helper import DatasetHelper
from iai_core_py.utils.flow_control import FlowControl
from jobs_common.utils.dataset_helpers import DatasetHelpers
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.tasks.infer_and_evaluate import BATCH_INFERENCE_NUM_ASYNC_REQUESTS

from job.tasks.evaluate_and_infer.pipeline_infer_on_unannotated import (
    MAX_UNANNOTATED_MEDIA,
    load_tasks_schemas,
    perform_task_inference,
    pipeline_infer_on_unannotated,
)
from job.utils.train_workflow_data import TrainWorkflowData
from tests.unit.tasks.utils import TEST_ENV_VARS, return_none


@pytest.mark.JobsComponent
class TestPipelineInferenceTask:
    model_id = "model_id"

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(DatasetRepo, "save_deep")
    @patch.object(FlowControl, "flow_control")
    @patch("job.tasks.evaluate_and_infer.pipeline_infer_on_unannotated.perform_task_inference")
    @patch.object(DatasetHelpers, "get_unannotated_dataset")
    @patch("job.tasks.evaluate_and_infer.pipeline_infer_on_unannotated.load_tasks_schemas")
    @patch.object(ModelService, "get_inference_active_model")
    @patch.object(TrainWorkflowData, "get_model_storage")
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch.object(DatasetRepo, "__init__", new=return_none)
    def test_pipeline_inference(
        self,
        mocked_get_entities,
        mocked_get_ms,
        mocked_get_active_model,
        mocked_load_tasks_schemas,
        mocked_get_dataset,
        mocked_perform_inference,
        mocked_flow_control,
        mocked_dr_save,
        fxt_train_data,
    ) -> None:
        # Arrange
        mock_model_storage = MagicMock(spec=ModelStorage)
        mock_model_storage_identifier = MagicMock(spec=ModelStorageIdentifier)
        mock_model_storage.identifier = mock_model_storage_identifier
        mock_model = MagicMock()
        mock_dataset_storage = MagicMock(spec=DatasetStorage)
        mock_dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        mock_dataset_storage.identifier = mock_dataset_storage_identifier
        mock_dataset = MagicMock(spec=Dataset)
        mock_task_1, mock_crop_task, mock_task_2 = (
            MagicMock(spec=TaskNode),
            MagicMock(spec=TaskNode),
            MagicMock(spec=TaskNode),
        )
        mock_tasks_schemas = MagicMock()
        inferred_dataset_1, cropped_dataset, inferred_dataset_2 = (MagicMock(), MagicMock(), MagicMock())
        mock_project = MagicMock(tasks=[mock_task_1, mock_crop_task, mock_task_2])
        train_data = fxt_train_data()

        def _mocked_infer(*args, **kwargs):
            task = kwargs.pop("task_node")
            if task == mock_task_1:
                return inferred_dataset_1
            return inferred_dataset_2

        mock_project.get_trainable_task_nodes.return_value = [mock_task_1, mock_task_2]
        mock_project.get_training_dataset_storage.return_value = mock_dataset_storage
        mocked_get_entities.return_value = [mock_project, None]
        mocked_get_ms.return_value = mock_model_storage
        mocked_get_active_model.return_value = mock_model
        mocked_load_tasks_schemas.return_value = mock_tasks_schemas
        mock_dataset.__len__.return_value = 1
        mocked_get_dataset.return_value = mock_dataset
        mock_task_1.task_properties.is_trainable = True
        mock_crop_task.task_properties.is_trainable = False
        mock_task_2.task_properties.is_trainable = True
        mock_crop_task.task_properties.task_family = TaskFamily.FLOW_CONTROL
        mocked_perform_inference.side_effect = _mocked_infer
        mocked_flow_control.return_value = cropped_dataset

        progress_callback = MagicMock()

        # Act
        pipeline_infer_on_unannotated(train_data=train_data, progress_callback=progress_callback)

        # Assert
        mocked_get_entities.assert_called_once_with()
        mocked_get_active_model.assert_has_calls(
            [
                call(project_identifier=mock_project.identifier, task_node_id=mock_task_1.id_),
                call(project_identifier=mock_project.identifier, task_node_id=mock_task_2.id_),
            ]
        )
        mocked_get_dataset.assert_called_once_with(
            project=mock_project,
            dataset_storage=mock_dataset_storage,
            max_dataset_size=MAX_UNANNOTATED_MEDIA,
        )
        mocked_flow_control.assert_called_once_with(
            project=mock_project,
            task_node=mock_crop_task,
            prev_task_node=mock_task_1,
            dataset=inferred_dataset_1,
            label_schema=mock_tasks_schemas[mock_task_1.id_],
        )
        progress_callback.assert_called_once_with(
            100, "Finished generating task-chain predictions on unannotated media"
        )

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(DatasetHelpers, "get_unannotated_dataset")
    @patch("job.tasks.evaluate_and_infer.pipeline_infer_on_unannotated.load_tasks_schemas")
    @patch.object(TrainWorkflowData, "get_model_storage")
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch.object(ModelRepo, "__init__", new=return_none)
    def test_pipeline_inference_empty_dataset_for_first_task(
        self,
        mocked_get_entities,
        mocked_get_ms,
        mocked_load_tasks_schemas,
        mocked_get_dataset,
        fxt_train_data,
    ) -> None:
        # Arrange
        mock_project = MagicMock()
        mock_model_storage = MagicMock(spec=ModelStorage)
        mock_model_storage_identifier = MagicMock(spec=ModelStorageIdentifier)
        mock_model_storage.identifier = mock_model_storage_identifier
        mock_dataset_storage = MagicMock(spec=DatasetStorage)
        mock_dataset = MagicMock(spec=Dataset)
        mock_task_1, mock_task_2 = MagicMock(spec=TaskNode), MagicMock(spec=TaskNode)
        train_data = fxt_train_data()

        mock_project.get_trainable_task_nodes.return_value = [mock_task_1, mock_task_2]
        mock_project.get_training_dataset_storage.return_value = mock_dataset_storage
        mocked_get_entities.return_value = [mock_project, None]
        mocked_get_ms.return_value = mock_model_storage
        mocked_load_tasks_schemas.return_value = {}
        mock_dataset.__len__.return_value = 0
        mocked_get_dataset.return_value = mock_dataset

        progress_callback = MagicMock()

        # Act
        pipeline_infer_on_unannotated(train_data=train_data, progress_callback=progress_callback)

        # Assert
        mocked_get_entities.assert_called_once_with()
        mocked_get_dataset.assert_called_once_with(
            project=mock_project,
            dataset_storage=mock_dataset_storage,
            max_dataset_size=MAX_UNANNOTATED_MEDIA,
        )
        progress_callback.assert_called_once_with(
            100, "All media are already annotated, no predictions need to be generated"
        )

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(DatasetRepo, "save_deep")
    @patch.object(FlowControl, "flow_control")
    @patch("job.tasks.evaluate_and_infer.pipeline_infer_on_unannotated.perform_task_inference")
    @patch.object(DatasetHelpers, "get_unannotated_dataset")
    @patch("job.tasks.evaluate_and_infer.pipeline_infer_on_unannotated.load_tasks_schemas")
    @patch.object(ModelService, "get_inference_active_model")
    @patch.object(TrainWorkflowData, "get_model_storage")
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch.object(DatasetRepo, "__init__", new=return_none)
    def test_pipeline_inference_empty_dataset_for_second_task(
        self,
        mocked_get_entities,
        mocked_get_ms,
        mocked_get_active_model,
        mocked_load_tasks_schemas,
        mocked_get_dataset,
        mocked_perform_inference,
        mocked_flow_control,
        mocked_dr_save,
        fxt_train_data,
    ) -> None:
        # Arrange
        mock_model_storage = MagicMock(spec=ModelStorage)
        mock_model_storage_identifier = MagicMock(spec=ModelStorageIdentifier)
        mock_model_storage.identifier = mock_model_storage_identifier
        mock_model = MagicMock()
        mock_dataset_storage = MagicMock(spec=DatasetStorage)
        mock_dataset_storage_identifier = MagicMock(spec=DatasetStorageIdentifier)
        mock_dataset_storage.identifier = mock_dataset_storage_identifier
        mock_dataset = MagicMock(spec=Dataset)
        mock_empty_dataset = MagicMock(spec=NullDataset)
        mock_task_1, mock_crop_task, mock_task_2 = (
            MagicMock(spec=TaskNode),
            MagicMock(spec=TaskNode),
            MagicMock(spec=TaskNode),
        )
        mock_tasks_schemas = MagicMock()
        inferred_dataset = MagicMock()
        mock_project = MagicMock(tasks=[mock_task_1, mock_crop_task, mock_task_2])
        train_data = fxt_train_data()

        mock_project.get_trainable_task_nodes.return_value = [mock_task_1, mock_task_2]
        mock_project.get_training_dataset_storage.return_value = mock_dataset_storage
        mocked_get_entities.return_value = [mock_project, None]
        mocked_get_ms.return_value = mock_model_storage
        mocked_get_active_model.return_value = mock_model
        mocked_load_tasks_schemas.return_value = mock_tasks_schemas
        mock_dataset.__len__.return_value = 1
        mocked_get_dataset.return_value = mock_dataset
        mock_task_1.task_properties.is_trainable = True
        mock_crop_task.task_properties.is_trainable = False
        mock_task_2.task_properties.is_trainable = True
        mock_crop_task.task_properties.task_family = TaskFamily.FLOW_CONTROL
        mocked_perform_inference.return_value = inferred_dataset
        mocked_flow_control.return_value = mock_empty_dataset

        progress_callback = MagicMock()

        # Act
        pipeline_infer_on_unannotated(train_data=train_data, progress_callback=progress_callback)

        # Assert
        mocked_get_entities.assert_called_once_with()
        mocked_get_active_model.assert_has_calls(
            [
                call(project_identifier=mock_project.identifier, task_node_id=mock_task_1.id_),
                call(project_identifier=mock_project.identifier, task_node_id=mock_task_2.id_),
            ]
        )
        mocked_get_dataset.assert_called_once_with(
            project=mock_project,
            dataset_storage=mock_dataset_storage,
            max_dataset_size=MAX_UNANNOTATED_MEDIA,
        )
        mocked_flow_control.assert_called_once_with(
            project=mock_project,
            task_node=mock_crop_task,
            prev_task_node=mock_task_1,
            dataset=inferred_dataset,
            label_schema=mock_tasks_schemas[mock_task_1.id_],
        )
        progress_callback.assert_called_once_with(
            100, "Finished generating task-chain predictions on unannotated media"
        )

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(TrainWorkflowData, "get_common_entities")
    def test_pipeline_inference_one_task(self, mocked_get_entities, fxt_train_data) -> None:
        # Arrange
        mock_project = MagicMock()
        train_data = fxt_train_data()

        mock_project.get_trainable_task_nodes.return_value = [MagicMock(spec=TaskNode)]
        mocked_get_entities.return_value = [mock_project, None]

        progress_callback = MagicMock()

        # Act
        pipeline_infer_on_unannotated(train_data=train_data, progress_callback=progress_callback)

        # Assert
        mocked_get_entities.assert_called_once_with()
        progress_callback.assert_called_once_with(
            100, "Skipping generation of task-chain predictions because the project has only one task."
        )

    @pytest.mark.parametrize("first_task", [True, False])
    @patch.object(DatasetHelper, "clone_dataset")
    @patch("job.tasks.evaluate_and_infer.pipeline_infer_on_unannotated.BatchInference")
    def test_perform_task_inference(self, mocked_command_init, mocked_clone, first_task) -> None:
        # Arrange
        mock_dataset_storage = MagicMock(spec=DatasetStorage)
        mock_project = MagicMock()
        mock_task_node_1 = MagicMock()
        mock_task_node_1.title = "detection"
        mock_task_node_2 = MagicMock()
        tasks_list = [mock_task_node_1, mock_task_node_2]
        if not first_task:
            tasks_list.reverse()
        mock_model = MagicMock()
        mock_dataset = MagicMock()
        mock_task_output_dataset = MagicMock()
        mock_cloned_dataset = MagicMock()
        mock_batch_inference = MagicMock(output_datasets=[mock_task_output_dataset])
        mock_progress_callback = MagicMock()

        mock_project.get_trainable_task_nodes.return_value = tasks_list

        mocked_command_init.return_value = mock_batch_inference
        mocked_clone.return_value = mock_cloned_dataset

        # Act
        output_dataset = perform_task_inference(
            project=mock_project,
            task_node=mock_task_node_1,
            model=mock_model,
            dataset_storage=mock_dataset_storage,
            inference_dataset=mock_dataset,
            progress_callback=mock_progress_callback,
        )

        # Assert
        mocked_command_init.assert_called_once_with(
            project_identifier=mock_project.identifier,
            task_node=mock_task_node_1,
            model=mock_model,
            batch_inference_datasets=[
                BatchInferenceDataset(
                    dataset_storage=mock_dataset_storage,
                    input_dataset=mock_dataset,
                    output_dataset_purpose=DatasetPurpose.INFERENCE,
                )
            ],
            progress_callback=mock_progress_callback,
            progress_message=f"Generating predictions for task '{mock_task_node_1.title}' on unannotated media",
            max_async_requests=BATCH_INFERENCE_NUM_ASYNC_REQUESTS,
        )
        mock_batch_inference.run.assert_called_once_with(use_async=True)
        if first_task:
            mocked_clone.assert_called_once_with(
                dataset=mock_task_output_dataset, dataset_storage=mock_dataset_storage, save_db=True
            )
            assert output_dataset == mock_cloned_dataset
        else:
            mocked_clone.assert_not_called()
            assert output_dataset == mock_task_output_dataset

    @patch.object(LabelSchemaRepo, "get_latest_view_by_task")
    @patch.object(LabelSchemaRepo, "__init__", new=return_none)
    def test_load_tasks_schemas(self, mocked_get_label_schema) -> None:
        # Arrange
        task_node_id = "task_node_id"
        mock_project = MagicMock()
        mock_task = MagicMock(id_=ID(task_node_id))
        mock_label_schema = MagicMock(spec=LabelSchemaView)

        mock_project.get_trainable_task_nodes.return_value = [mock_task]

        mocked_get_label_schema.return_value = mock_label_schema

        # Act
        task_schemas = load_tasks_schemas(project=mock_project)

        # Assert
        assert task_schemas[ID(task_node_id)] == mock_label_schema
