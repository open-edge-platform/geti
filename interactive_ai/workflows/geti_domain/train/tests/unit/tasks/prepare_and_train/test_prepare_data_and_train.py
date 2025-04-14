# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests train task"""

import os
from unittest.mock import ANY, MagicMock, call, patch

import pytest
from geti_types import CTX_SESSION_VAR, ID
from jobs_common.tasks.utils.secrets import JobMetadata
from sc_sdk.entities.datasets import Dataset
from sc_sdk.repos import ProjectRepo

from job.tasks.prepare_and_train.prepare_data_and_train import prepare_training_data_model_and_start_training
from tests.unit.tasks.utils import TEST_ENV_VARS, return_none

WORKSPACE_ID = "workspace_id"
PROJECT_ID = "project_id"
TASK_ID = "task_id"
DATASET_ID = "dataset_id"
LABEL_SCHEMA_ID = "label_schema_id"
MODEL_STORAGE_ID = "model_storage_id"
BASE_MODEL_ID = "base_model_id"
MO_MODEL_ID = "mo_model_id"
HYPER_PARAMETERS_ID = "hyper_parameters_id"


@pytest.mark.JobsComponent
class TestPrepareTrainingDataTask:
    @pytest.mark.parametrize("from_scratch", [True, False])
    @pytest.mark.parametrize("reshuffle_subsets", [True, False])
    @pytest.mark.parametrize("should_activate_model", [True, False])
    @pytest.mark.parametrize("infer_on_pipeline", [True, False])
    @pytest.mark.parametrize("enable_training_from_dataset_shard", [True, False])
    @pytest.mark.parametrize("num_image_pulling_threads", [2])
    @pytest.mark.parametrize("num_upload_threads", [5])
    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch("jobs_common.tasks.utils.progress.report_progress")
    @patch("job.tasks.prepare_and_train.prepare_data_and_train.shard_dataset_for_train")
    @patch("job.tasks.prepare_and_train.prepare_data_and_train.create_task_train_dataset")
    @patch("job.tasks.prepare_and_train.prepare_data_and_train.get_train_data")
    @patch.object(ProjectRepo, "mark_locked")
    @patch("job.tasks.prepare_and_train.prepare_data_and_train.prepare_train")
    @patch("job.tasks.prepare_and_train.prepare_data_and_train.create_flyte_container_task")
    @patch("job.tasks.prepare_and_train.prepare_data_and_train.ComputeResources.from_node_resources")
    @patch(
        "job.tasks.prepare_and_train.prepare_data_and_train.EphemeralStorageResources.create_from_compiled_dataset_shards"
    )
    @patch("job.tasks.prepare_and_train.prepare_data_and_train.TrainerImageInfo.create")
    @patch("job.tasks.prepare_and_train.prepare_data_and_train.publish_consumed_resources")
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    def test_prepare_training_data(
        self,
        mocked_publish_consumed_resources,
        mocked_trainer_image_info_create,
        mocked_create_from_compiled_dataset_shards,
        mocked_compute_resources_from_node_resources,
        mocked_create_flyte_container_task,
        mocked_prepare_train,
        mocked_lock_project,
        mocked_get_train_data,
        mocked_create_task_train_dataset,
        mocked_shard_dataset_for_train,
        mocked_report_progress,
        from_scratch,
        reshuffle_subsets,
        should_activate_model,
        infer_on_pipeline,
        enable_training_from_dataset_shard,
        num_image_pulling_threads,
        num_upload_threads,
        fxt_train_data,
        fxt_train_output_models,
    ) -> None:
        # Arrange
        train_data = fxt_train_data(workspace_id=WORKSPACE_ID, project_id=PROJECT_ID, task_id=TASK_ID)
        train_data.get_compiled_dataset_shards = MagicMock()

        mocked_get_train_data.return_value = train_data
        dataset = Dataset(ID(DATASET_ID))
        mocked_create_task_train_dataset.return_value = dataset
        mocked_shard_dataset_for_train.return_value = "sharded_dataset_id"
        mocked_prepare_train.return_value = fxt_train_output_models
        mocked_train_task = MagicMock()
        mocked_create_flyte_container_task.return_value = mocked_train_task

        # Act
        prepare_training_data_model_and_start_training(
            project_id=PROJECT_ID,
            task_id=TASK_ID,
            from_scratch=from_scratch,
            should_activate_model=should_activate_model,
            infer_on_pipeline=infer_on_pipeline,
            model_storage_id=MODEL_STORAGE_ID,
            enable_training_from_dataset_shard=enable_training_from_dataset_shard,
            max_shard_size=1000,
            hyper_parameters_id=HYPER_PARAMETERS_ID,
            num_image_pulling_threads=num_image_pulling_threads,
            num_upload_threads=num_upload_threads,
            max_training_dataset_size=100,
            command=["bash", "-c", "/opt/run"],
            reshuffle_subsets=reshuffle_subsets,
        )

        # Assert
        mocked_lock_project.assert_called_once_with(owner="train", project_id=ID(PROJECT_ID), duration_seconds=ANY)
        mocked_get_train_data.assert_called_once_with(
            project_id=PROJECT_ID,
            task_id=TASK_ID,
            from_scratch=from_scratch,
            should_activate_model=should_activate_model,
            infer_on_pipeline=infer_on_pipeline,
            model_storage_id=MODEL_STORAGE_ID,
            hyper_parameters_id=HYPER_PARAMETERS_ID,
            max_number_of_annotations=None,
            min_annotation_size=None,
            reshuffle_subsets=reshuffle_subsets,
        )
        mocked_create_task_train_dataset.assert_called_once_with(train_data=train_data, max_training_dataset_size=100)

        report_progress_calls = [
            call(progress=-1, message="Starting training data preparation"),
            call(progress=0.0, message="Starting train data retrieval"),
            call(progress=33.3, message="Train data retrieved"),
            call(progress=33.3, message="Starting train dataset creation"),
            call(progress=66.7, message="Train dataset is created"),
        ]

        if enable_training_from_dataset_shard:
            mocked_shard_dataset_for_train.assert_called_once_with(
                train_data=train_data,
                dataset=dataset,
                max_shard_size=1000,
                progress_callback=ANY,
                num_image_pulling_threads=num_image_pulling_threads,
                num_upload_threads=num_upload_threads,
            )
            report_progress_calls.extend(
                [
                    call(progress=66.7, message="Starting dataset sharding"),
                    call(progress=100.0, message="Dataset sharding is done"),
                ]
            )
        else:
            mocked_shard_dataset_for_train.assert_not_called()
            report_progress_calls.append(call(progress=100.0, message="Training from sharded dataset is disabled"))

        mocked_prepare_train.assert_called_once_with(train_data=train_data, dataset=dataset)
        mocked_compute_resources_from_node_resources.assert_called_once()
        mocked_trainer_image_info_create.assert_called_once()
        mocked_create_from_compiled_dataset_shards.assert_called_once()
        mocked_create_flyte_container_task.assert_called_once_with(
            session=CTX_SESSION_VAR.get(),
            project_id=train_data.project_id,
            job_id=str(JobMetadata.from_env_vars().id),
            compute_resources=ANY,
            ephemeral_storage_resources=ANY,
            trainer_image_info=ANY,
            command=["bash", "-c", "/opt/run"],
            container_name="train",
        )
        mocked_publish_consumed_resources.assert_called_once_with(
            amount=len(dataset), unit="images", service="training"
        )
        mocked_train_task.assert_called_once()

        report_progress_calls.append(call(progress=100, message="Training data prepared"))

        mocked_report_progress.assert_has_calls(report_progress_calls)
