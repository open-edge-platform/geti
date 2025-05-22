# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests train task"""

import datetime
import os
from unittest.mock import ANY, call, patch

import pytest
from geti_types import ID
from jobs_common.tasks.utils.secrets import JobMetadata

from job.tasks.evaluate_and_infer.evaluate_and_infer import (
    EvaluationFailedException,
    ModelNotImprovedException,
    evaluate_and_infer,
)
from tests.unit.tasks.utils import TEST_ENV_VARS, return_none

WORKSPACE_ID = "workspace_id"
PROJECT_ID = "project_id"
TASK_ID = "task_id"
DATASET_ID = "dataset_id"
LABEL_SCHEMA_ID = "label_schema_id"
MODEL_STORAGE_ID = "model_storage_id"
BASE_MODEL_ID = "base_model_id"
MO_MODEL_ID = "mo_model_id"
TRAIN_INFERENCE_SUBSET_ID = "train_inference_subset_id"


@pytest.mark.JobsComponent
class TestEvaluateAndInferTask:
    @pytest.mark.parametrize("should_activate_model", [True, False])
    @pytest.mark.parametrize("infer_on_pipeline", [True, False])
    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(
        JobMetadata,
        "from_env_vars",
        return_value=JobMetadata(ID("job_id"), "test_job", "Test jobs", ID("author"), datetime.datetime.now()),
    )
    @patch("jobs_common.tasks.utils.progress.report_progress")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pipeline_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.register_models")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.task_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.post_model_acceptance")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.evaluate")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pre_evaluate_model")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.finalize_train")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.update_model_trained_metadata")
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    def test_evaluate_and_infer_model_not_accepted(
        self,
        mocked_update_model_trained_metadata,
        mocked_finalize_train,
        mocked_pre_evaluate_model,
        mocked_evaluate,
        mocked_post_model_acceptance,
        mocked_task_infer_on_unannotated,
        mocked_register_models,
        mocked_pipeline_infer_on_unannotated,
        mocked_report_progress,
        mocked_from_env_vars,
        should_activate_model,
        infer_on_pipeline,
        fxt_train_data_for_flyte_task_trainer,
    ) -> None:
        # Arrange
        train_data = fxt_train_data_for_flyte_task_trainer
        mocked_evaluate.return_value = (False, TRAIN_INFERENCE_SUBSET_ID)

        # Act
        with pytest.raises(ModelNotImprovedException):
            evaluate_and_infer(
                train_data=train_data,
                should_activate_model=should_activate_model,
                infer_on_pipeline=infer_on_pipeline,
                from_scratch=True,
            )

        # Assert
        mocked_update_model_trained_metadata.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=train_data.train_output_model_ids.base,
        )
        mocked_finalize_train.assert_called_once_with(
            train_data=train_data.train_data,
            train_output_model_ids=train_data.train_output_model_ids,
            keep_mlflow_artifacts=False,
        )
        mocked_pre_evaluate_model.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=ID(train_data.train_output_model_ids.base),
            dataset_id=ID(train_data.dataset_id),
            from_scratch=True,
        )
        mocked_evaluate.assert_called_once_with(
            train_data=train_data.train_data,
            dataset_id=train_data.dataset_id,
            base_model_id=train_data.train_output_model_ids.base,
            mo_model_id=train_data.train_output_model_ids.mo_with_xai,
            progress_callback=ANY,
        )

        mocked_register_models.assert_not_called()
        mocked_pipeline_infer_on_unannotated.assert_not_called()
        mocked_task_infer_on_unannotated.assert_not_called()
        mocked_post_model_acceptance.assert_not_called()

        mocked_report_progress.assert_has_calls(
            [
                call(progress=-1, message="Starting model evaluation and inference"),
                call(progress=20.0, message="Starting model evaluation"),
                call(
                    message=(
                        "The training is finished successfully but the new model accuracy is lower than the previous "
                        "model accuracy. Possible solutions: (1) add more annotated data to the dataset, (2) train "
                        "from scratch, (3) use a different model architecture or (4) run optimize accuracy operation "
                        "from the last trained model. (ID: job_id)"
                    )
                ),
            ]
        )
        mocked_from_env_vars.assert_called_once_with()

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(
        JobMetadata,
        "from_env_vars",
        return_value=JobMetadata(ID("job_id"), "test_job", "Test jobs", ID("author"), datetime.datetime.now()),
    )
    @patch("jobs_common.tasks.utils.progress.report_progress")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pipeline_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.register_models")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.task_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.post_model_acceptance")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.evaluate")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pre_evaluate_model")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.finalize_train")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.update_model_trained_metadata")
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    def test_evaluate_and_infer_evaluate_failed(
        self,
        mocked_update_model_trained_metadata,
        mocked_finalize_train,
        mocked_pre_evaluate_model,
        mocked_evaluate,
        mocked_post_model_acceptance,
        mocked_task_infer_on_unannotated,
        mocked_register_models,
        mocked_pipeline_infer_on_unannotated,
        mocked_report_progress,
        mocked_from_env_vars,
        fxt_train_data_for_flyte_task_trainer,
    ) -> None:
        # Arrange
        train_data = fxt_train_data_for_flyte_task_trainer
        mocked_evaluate.side_effect = Exception

        # Act
        with pytest.raises(EvaluationFailedException):
            evaluate_and_infer(
                train_data=train_data,
                should_activate_model=True,
                infer_on_pipeline=False,
                from_scratch=True,
            )

        # Assert
        mocked_update_model_trained_metadata.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=train_data.train_output_model_ids.base,
        )
        mocked_finalize_train.assert_called_once_with(
            train_data=train_data.train_data,
            train_output_model_ids=train_data.train_output_model_ids,
            keep_mlflow_artifacts=False,
        )
        mocked_pre_evaluate_model.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=ID(train_data.train_output_model_ids.base),
            dataset_id=ID(train_data.dataset_id),
            from_scratch=True,
        )
        mocked_evaluate.assert_called_once_with(
            train_data=train_data.train_data,
            dataset_id=train_data.dataset_id,
            base_model_id=train_data.train_output_model_ids.base,
            mo_model_id=train_data.train_output_model_ids.mo_with_xai,
            progress_callback=ANY,
        )

        mocked_register_models.assert_not_called()
        mocked_pipeline_infer_on_unannotated.assert_not_called()
        mocked_task_infer_on_unannotated.assert_not_called()
        mocked_post_model_acceptance.assert_not_called()

        mocked_report_progress.assert_has_calls(
            [
                call(progress=-1, message="Starting model evaluation and inference"),
                call(progress=20.0, message="Starting model evaluation"),
                call(
                    message=(
                        "Training failed at evaluation stage. No model is saved from this training round. "
                        "Please try again and if problem persists, contact our customer support team. (ID: job_id)"
                    )
                ),
            ]
        )
        mocked_from_env_vars.assert_called_once_with()

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(
        JobMetadata,
        "from_env_vars",
        return_value=JobMetadata(ID("job_id"), "test_job", "Test jobs", ID("author"), datetime.datetime.now()),
    )
    @patch("jobs_common.tasks.utils.progress.report_progress")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pipeline_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.register_models")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.task_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.post_model_acceptance")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.evaluate")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pre_evaluate_model")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.finalize_train")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.update_model_trained_metadata")
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    def test_evaluate_and_infer_post_model_acceptance_failed(
        self,
        mocked_update_model_trained_metadata,
        mocked_finalize_train,
        mocked_pre_evaluate_model,
        mocked_evaluate,
        mocked_post_model_acceptance,
        mocked_task_infer_on_unannotated,
        mocked_register_models,
        mocked_pipeline_infer_on_unannotated,
        mocked_report_progress,
        mocked_from_env_vars,
        fxt_train_data_for_flyte_task_trainer,
    ) -> None:
        # Arrange
        train_data = fxt_train_data_for_flyte_task_trainer
        mocked_evaluate.return_value = (True, TRAIN_INFERENCE_SUBSET_ID)
        mocked_post_model_acceptance.side_effect = Exception

        # Act
        with pytest.raises(EvaluationFailedException):
            evaluate_and_infer(
                train_data=train_data,
                should_activate_model=True,
                infer_on_pipeline=False,
                from_scratch=True,
            )

        # Assert
        mocked_update_model_trained_metadata.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=train_data.train_output_model_ids.base,
        )
        mocked_finalize_train.assert_called_once_with(
            train_data=train_data.train_data,
            train_output_model_ids=train_data.train_output_model_ids,
            keep_mlflow_artifacts=False,
        )
        mocked_pre_evaluate_model.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=ID(train_data.train_output_model_ids.base),
            dataset_id=ID(train_data.dataset_id),
            from_scratch=True,
        )
        mocked_evaluate.assert_called_once_with(
            train_data=train_data.train_data,
            dataset_id=train_data.dataset_id,
            base_model_id=train_data.train_output_model_ids.base,
            mo_model_id=train_data.train_output_model_ids.mo_with_xai,
            progress_callback=ANY,
        )

        mocked_register_models.assert_called_once()
        mocked_pipeline_infer_on_unannotated.assert_not_called()
        mocked_task_infer_on_unannotated.assert_not_called()
        mocked_post_model_acceptance.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=train_data.train_output_model_ids.base,
            inference_model_id=train_data.train_output_model_ids.mo_with_xai,
        )

        mocked_report_progress.assert_has_calls(
            [
                call(progress=-1, message="Starting model evaluation and inference"),
                call(progress=20.0, message="Starting model evaluation"),
                call(progress=40.0, message="Activating trained model"),
                call(
                    message=(
                        "Training failed at evaluation stage. No model is saved from this training round. "
                        "Please try again and if problem persists, contact our customer support team. (ID: job_id)"
                    )
                ),
            ]
        )
        mocked_from_env_vars.assert_called_once_with()

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch("jobs_common.tasks.utils.progress.report_progress")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pipeline_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.register_models")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.task_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.post_model_acceptance")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.evaluate")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pre_evaluate_model")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.finalize_train")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.update_model_trained_metadata")
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    def test_evaluate_and_infer_task_inference_failed(
        self,
        mocked_update_model_trained_metadata,
        mocked_finalize_train,
        mocked_pre_evaluate_model,
        mocked_evaluate,
        mocked_post_model_acceptance,
        mocked_task_infer_on_unannotated,
        mocked_register_models,
        mocked_pipeline_infer_on_unannotated,
        mocked_report_progress,
        fxt_train_data_for_flyte_task_trainer,
    ) -> None:
        # Arrange
        train_data = fxt_train_data_for_flyte_task_trainer
        mocked_evaluate.return_value = (True, TRAIN_INFERENCE_SUBSET_ID)
        mocked_task_infer_on_unannotated.side_effect = Exception

        # Act
        evaluate_and_infer(
            train_data=train_data,
            should_activate_model=True,
            infer_on_pipeline=False,
            from_scratch=True,
        )

        # Assert
        mocked_update_model_trained_metadata.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=train_data.train_output_model_ids.base,
        )
        mocked_finalize_train.assert_called_once_with(
            train_data=train_data.train_data,
            train_output_model_ids=train_data.train_output_model_ids,
            keep_mlflow_artifacts=False,
        )
        mocked_pre_evaluate_model.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=ID(train_data.train_output_model_ids.base),
            dataset_id=ID(train_data.dataset_id),
            from_scratch=True,
        )
        mocked_evaluate.assert_called_once_with(
            train_data=train_data.train_data,
            dataset_id=train_data.dataset_id,
            base_model_id=train_data.train_output_model_ids.base,
            mo_model_id=train_data.train_output_model_ids.mo_with_xai,
            progress_callback=ANY,
        )

        mocked_post_model_acceptance.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=train_data.train_output_model_ids.base,
            inference_model_id=train_data.train_output_model_ids.mo_with_xai,
        )

        mocked_register_models.assert_called_once_with(
            project_id=ID(train_data.train_data.project_id),
            model_id=ID(train_data.train_output_model_ids.base),
            optimized_model_id=ID(train_data.train_output_model_ids.mo_with_xai),
            model_storage_id=ID(train_data.train_data.model_storage_id),
            task_id=ID(train_data.train_data.task_id),
        )
        mocked_task_infer_on_unannotated.assert_called_once_with(
            train_data=train_data.train_data,
            training_dataset_id=train_data.dataset_id,
            train_inference_subset_id=TRAIN_INFERENCE_SUBSET_ID,
            model_id=train_data.train_output_model_ids.mo_with_xai,
            progress_callback=ANY,
        )
        mocked_pipeline_infer_on_unannotated.assert_not_called()

        mocked_report_progress.assert_has_calls(
            [
                call(progress=-1, message="Starting model evaluation and inference"),
                call(progress=20, message="Starting model evaluation"),
                call(progress=40, message="Activating trained model"),
                call(progress=60, message="Trained model is activated"),
                call(progress=60, message="Generating task-level predictions on unannotated media"),
                call(progress=80, message="Failed to generate task-level predictions on unannotated media"),
                call(progress=100, message="Skipped generating task-chain predictions on unannotated media"),
                call(progress=100, message="Model is evaluated and inference is finished"),
            ]
        )

    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch("jobs_common.tasks.utils.progress.report_progress")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pipeline_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.register_models")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.task_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.post_model_acceptance")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.evaluate")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pre_evaluate_model")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.finalize_train")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.update_model_trained_metadata")
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    def test_evaluate_and_infer_pipeline_inference_failed(
        self,
        mocked_update_model_trained_metadata,
        mocked_finalize_train,
        mocked_pre_evaluate_model,
        mocked_evaluate,
        mocked_post_model_acceptance,
        mocked_task_infer_on_unannotated,
        mocked_register_models,
        mocked_pipeline_infer_on_unannotated,
        mocked_report_progress,
        fxt_train_data_for_flyte_task_trainer,
    ) -> None:
        # Arrange
        train_data = fxt_train_data_for_flyte_task_trainer
        mocked_evaluate.return_value = (True, TRAIN_INFERENCE_SUBSET_ID)
        mocked_pipeline_infer_on_unannotated.side_effect = Exception

        # Act
        evaluate_and_infer(
            train_data=train_data,
            should_activate_model=True,
            infer_on_pipeline=True,
            from_scratch=True,
        )

        # Assert
        mocked_update_model_trained_metadata.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=train_data.train_output_model_ids.base,
        )
        mocked_finalize_train.assert_called_once_with(
            train_data=train_data.train_data,
            train_output_model_ids=train_data.train_output_model_ids,
            keep_mlflow_artifacts=False,
        )
        mocked_pre_evaluate_model.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=ID(train_data.train_output_model_ids.base),
            dataset_id=ID(train_data.dataset_id),
            from_scratch=True,
        )
        mocked_evaluate.assert_called_once_with(
            train_data=train_data.train_data,
            dataset_id=train_data.dataset_id,
            base_model_id=train_data.train_output_model_ids.base,
            mo_model_id=train_data.train_output_model_ids.mo_with_xai,
            progress_callback=ANY,
        )

        mocked_post_model_acceptance.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=train_data.train_output_model_ids.base,
            inference_model_id=train_data.train_output_model_ids.mo_with_xai,
        )
        mocked_register_models.assert_called_once_with(
            project_id=ID(train_data.train_data.project_id),
            model_id=ID(train_data.train_output_model_ids.base),
            optimized_model_id=ID(train_data.train_output_model_ids.mo_with_xai),
            model_storage_id=ID(train_data.train_data.model_storage_id),
            task_id=ID(train_data.train_data.task_id),
        )
        mocked_task_infer_on_unannotated.assert_called_once_with(
            train_data=train_data.train_data,
            training_dataset_id=train_data.dataset_id,
            train_inference_subset_id=TRAIN_INFERENCE_SUBSET_ID,
            model_id=train_data.train_output_model_ids.mo_with_xai,
            progress_callback=ANY,
        )
        mocked_pipeline_infer_on_unannotated.assert_called_once_with(
            train_data=train_data.train_data, progress_callback=ANY
        )

        mocked_report_progress.assert_has_calls(
            [
                call(progress=-1, message="Starting model evaluation and inference"),
                call(progress=20, message="Starting model evaluation"),
                call(progress=40, message="Activating trained model"),
                call(progress=60, message="Trained model is activated"),
                call(progress=60, message="Generating task-level predictions on unannotated media"),
                call(progress=80, message="Generating task-chain predictions on unannotated media"),
                call(progress=100, message="Failed to generate task-chain predictions on unannotated media"),
                call(progress=100, message="Model is evaluated and inference is finished"),
            ]
        )

    @pytest.mark.parametrize("should_activate_model", [True, False])
    @pytest.mark.parametrize("infer_on_pipeline", [True, False])
    @pytest.mark.parametrize("from_scratch", [True, False])
    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch("jobs_common.tasks.utils.progress.report_progress")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pipeline_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.register_models")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.task_infer_on_unannotated")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.post_model_acceptance")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.evaluate")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.pre_evaluate_model")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.finalize_train")
    @patch("job.tasks.evaluate_and_infer.evaluate_and_infer.update_model_trained_metadata")
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    def test_evaluate_and_infer_model_accepted(
        self,
        mocked_update_model_trained_metadata,
        mocked_finalize_train,
        mocked_pre_evaluate_model,
        mocked_evaluate,
        mocked_post_model_acceptance,
        mocked_task_infer_on_unannotated,
        mocked_register_models,
        mocked_pipeline_infer_on_unannotated,
        mocked_report_progress,
        should_activate_model,
        infer_on_pipeline,
        from_scratch,
        fxt_train_data_for_flyte_task_trainer,
    ) -> None:
        # Arrange
        train_data = fxt_train_data_for_flyte_task_trainer
        mocked_evaluate.return_value = (True, TRAIN_INFERENCE_SUBSET_ID)

        # Act
        evaluate_and_infer(
            train_data=train_data,
            should_activate_model=should_activate_model,
            infer_on_pipeline=infer_on_pipeline,
            from_scratch=from_scratch,
        )

        # Assert
        mocked_update_model_trained_metadata.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=train_data.train_output_model_ids.base,
        )
        mocked_finalize_train.assert_called_once_with(
            train_data=train_data.train_data,
            train_output_model_ids=train_data.train_output_model_ids,
            keep_mlflow_artifacts=False,
        )
        mocked_pre_evaluate_model.assert_called_once_with(
            train_data=train_data.train_data,
            base_model_id=ID(train_data.train_output_model_ids.base),
            dataset_id=ID(train_data.dataset_id),
            from_scratch=from_scratch,
        )
        mocked_evaluate.assert_called_once_with(
            train_data=train_data.train_data,
            dataset_id=train_data.dataset_id,
            base_model_id=train_data.train_output_model_ids.base,
            mo_model_id=train_data.train_output_model_ids.mo_with_xai,
            progress_callback=ANY,
        )

        report_progress_calls = [
            call(progress=-1, message="Starting model evaluation and inference"),
            call(progress=20.0, message="Starting model evaluation"),
        ]

        if should_activate_model:
            mocked_post_model_acceptance.assert_called_once_with(
                train_data=train_data.train_data,
                base_model_id=train_data.train_output_model_ids.base,
                inference_model_id=train_data.train_output_model_ids.mo_with_xai,
            )
            mocked_register_models.assert_called_once_with(
                project_id=ID(train_data.train_data.project_id),
                model_id=ID(train_data.train_output_model_ids.base),
                optimized_model_id=ID(train_data.train_output_model_ids.mo_with_xai),
                model_storage_id=ID(train_data.train_data.model_storage_id),
                task_id=ID(train_data.train_data.task_id),
            )
            mocked_task_infer_on_unannotated.assert_called_once_with(
                train_data=train_data.train_data,
                training_dataset_id=train_data.dataset_id,
                train_inference_subset_id=TRAIN_INFERENCE_SUBSET_ID,
                model_id=train_data.train_output_model_ids.mo_with_xai,
                progress_callback=ANY,
            )
            report_progress_calls.extend(
                [
                    call(progress=40, message="Activating trained model"),
                    call(progress=60, message="Trained model is activated"),
                    call(progress=60, message="Generating task-level predictions on unannotated media"),
                ]
            )
            if infer_on_pipeline:
                mocked_pipeline_infer_on_unannotated.assert_called_once_with(
                    train_data=train_data.train_data, progress_callback=ANY
                )
                report_progress_calls.append(
                    call(progress=80, message="Generating task-chain predictions on unannotated media")
                )
            else:
                report_progress_calls.append(
                    call(progress=100, message="Skipped generating task-chain predictions on unannotated media")
                )
        else:
            mocked_register_models.assert_not_called()
            mocked_pipeline_infer_on_unannotated.assert_not_called()
            mocked_task_infer_on_unannotated.assert_not_called()
            mocked_post_model_acceptance.assert_not_called()

        report_progress_calls.append(call(progress=100, message="Model is evaluated and inference is finished"))

        mocked_report_progress.assert_has_calls(report_progress_calls)
