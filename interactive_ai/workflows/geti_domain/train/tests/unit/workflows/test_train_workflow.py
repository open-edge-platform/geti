# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests the train workflow"""

import pytest
from flytekit.core.testing import task_mock
from jobs_common_extras.mlflow.utils.train_output_models import TrainOutputModelIds

from job.tasks.evaluate_and_infer.evaluate_and_infer import evaluate_and_infer
from job.tasks.prepare_and_train.prepare_data_and_train import prepare_training_data_model_and_start_training
from job.utils.train_workflow_data import TrainWorkflowDataForFlyteTaskTrainer
from job.workflows.train_workflow import train_workflow

WORKSPACE_ID = "workspace_id"
PROJECT_ID = "project_id"
TASK_ID = "task_id"
DATASET_ID = "dataset_id"
BASE_MODEL_ID = "base_model_id"
MO_MODEL_ID = "mo_model_id"
MODEL_STORAGE_ID = "model_storage_id"
ACTIVE_MODEL_ID = "active_model_id"
HYPER_PARAMETERS_ID = "hyper_parameters_id"
INPUT_MODEL_ID = "input_model_id"
LABEL_SCHEMA_ID = "label_schema_id"
TRAIN_SUBSET_ID = "train_subset_id"
COMPILED_DATASET_SHARD_ID = "compiled_dataset_shards_id"


@pytest.mark.JobsComponent
class TestTrainWorkflow:
    @pytest.mark.parametrize("enable_training_from_dataset_shard", [False, True])
    @pytest.mark.parametrize("from_scratch", [True, False])
    @pytest.mark.parametrize("should_activate_model", [True, False])
    @pytest.mark.parametrize("num_image_pulling_threads", [2])
    @pytest.mark.parametrize("num_upload_threads", [5])
    def test_train_workflow(
        self,
        from_scratch,
        should_activate_model,
        enable_training_from_dataset_shard,
        num_image_pulling_threads,
        num_upload_threads,
        fxt_train_data,
    ):
        with (
            task_mock(prepare_training_data_model_and_start_training) as mocked_prepare_and_train,
            task_mock(evaluate_and_infer) as mocked_evaluate_and_infer,
        ):
            # Arrange
            infer_on_pipeline = True
            reshuffle_subsets = False
            train_workflow_data = fxt_train_data(
                workspace_id=WORKSPACE_ID,
                project_id=PROJECT_ID,
                task_id=TASK_ID,
                from_scratch=from_scratch,
                infer_on_pipeline=infer_on_pipeline,
                should_activate_model=should_activate_model,
                active_model_id=ACTIVE_MODEL_ID,
                model_storage_id=MODEL_STORAGE_ID,
                hyperparameters_id=HYPER_PARAMETERS_ID,
                input_model_id=INPUT_MODEL_ID,
                label_schema_id=LABEL_SCHEMA_ID,
                compiled_dataset_shards_id=None,
                reshuffle_subsets=reshuffle_subsets,
            )
            data_task_trainer = TrainWorkflowDataForFlyteTaskTrainer(
                train_data=train_workflow_data,
                dataset_id=DATASET_ID,
                organization_id="organization_id",
                job_id="job_id",
                train_output_model_ids=TrainOutputModelIds(
                    base=BASE_MODEL_ID,
                    mo_with_xai=MO_MODEL_ID,
                    mo_fp32_without_xai=None,
                    mo_fp16_without_xai=None,
                    onnx=None,
                ),
            )
            mocked_prepare_and_train.return_value = data_task_trainer

            # Act
            train_workflow(
                project_id=PROJECT_ID,
                task_id=TASK_ID,
                from_scratch=from_scratch,
                should_activate_model=should_activate_model,
                infer_on_pipeline=infer_on_pipeline,
                model_storage_id=MODEL_STORAGE_ID,
                hyper_parameters_id=HYPER_PARAMETERS_ID,
                enable_training_from_dataset_shard=enable_training_from_dataset_shard,
                num_image_pulling_threads=num_image_pulling_threads,
                num_upload_threads=num_upload_threads,
                max_training_dataset_size=100,
                reshuffle_subsets=reshuffle_subsets,
            )

            # Assert
            mocked_prepare_and_train.assert_called_once_with(
                project_id=PROJECT_ID,
                task_id=TASK_ID,
                from_scratch=from_scratch,
                should_activate_model=should_activate_model,
                infer_on_pipeline=infer_on_pipeline,
                command=["bash", "-c", "run"],
                model_storage_id=MODEL_STORAGE_ID,
                hyper_parameters_id=HYPER_PARAMETERS_ID,
                enable_training_from_dataset_shard=enable_training_from_dataset_shard,
                max_shard_size=1000,
                num_image_pulling_threads=num_image_pulling_threads,
                num_upload_threads=num_upload_threads,
                max_training_dataset_size=100,
                min_annotation_size=None,
                max_number_of_annotations=None,
                reshuffle_subsets=reshuffle_subsets,
                hyperparameters=None,
            )
            mocked_evaluate_and_infer.assert_called_once_with(
                train_data=data_task_trainer,
                should_activate_model=should_activate_model,
                infer_on_pipeline=infer_on_pipeline,
                from_scratch=from_scratch,
                keep_mlflow_artifacts=False,
            )
