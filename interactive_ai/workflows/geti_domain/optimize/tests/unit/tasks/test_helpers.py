# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from datetime import datetime
from unittest.mock import patch

import pytest

from job.tasks.helpers import finalize_optimize, prepare_optimize


@pytest.mark.JobsComponent
@patch.dict(
    os.environ,
    {
        "JOB_METADATA_ID": "job_id",
        "JOB_METADATA_TYPE": "job_type",
        "JOB_METADATA_NAME": "job_name",
        "JOB_METADATA_AUTHOR": "job_author",
        "JOB_METADATA_START_TIME": datetime.now().isoformat(),
    },
)
class TestOptimizeHelpers:
    @patch("job.tasks.helpers.ProjectRepo")
    @patch("job.tasks.helpers.ModelRepo")
    @patch("job.tasks.helpers.CompiledDatasetShardsRepo")
    @patch("job.tasks.helpers.AnnotationFilter")
    @patch("job.tasks.helpers.lock_project")
    @patch("job.tasks.helpers.publish_metadata_update")
    @patch("job.tasks.helpers.OptimizationTrainerContext")
    @patch("job.tasks.helpers.GetiOTXInterfaceAdapter")
    def test_prepare_optimize(
        self,
        mock_geti_otx_interface_adapter,
        mock_optimization_trainer_ctx,
        mock_publish_metadata_update,
        mock_lock_project,
        mock_annotation_filter,
        mock_compiled_dataset_shards_repo,
        mock_model_repo,
        mock_project_repo,
        fxt_model_optimized,
        fxt_project,
        fxt_optimization_trainer_ctx,
    ):
        mock_optimization_trainer_ctx.create_from_config.return_value = fxt_optimization_trainer_ctx
        mock_project_repo().get_by_id.return_value = fxt_project
        mock_model_repo().get_optimized_models_by_base_model_id.return_value = [fxt_model_optimized]
        mock_annotation_filter.apply_annotation_filters.return_value = "filtered_train_dataset"
        mock_compiled_dataset_shards_repo().get_by_id.return_value = "compiled_dataset_shards"
        mock_adapter = mock_geti_otx_interface_adapter()

        trainer_ctx = prepare_optimize(
            project_id="project_id",
            model_storage_id="model_storage_id",
            model_id="model_id",
            compiled_dataset_shards_id="compiled_dataset_shards_id",
            min_annotation_size=10,
            max_number_of_annotations=100,
        )

        assert trainer_ctx is fxt_optimization_trainer_ctx
        mock_lock_project.assert_called_once()
        mock_model_repo().save.assert_called_once()
        mock_publish_metadata_update.assert_called_once()
        mock_adapter.push_placeholders.assert_called_once()
        mock_adapter.push_metadata.assert_called_once()
        mock_adapter.push_input_configuration.assert_called_once()
        mock_adapter.push_input_model.assert_called_once()

    @pytest.mark.parametrize("keep_mlflow_artifacts", [True, False])
    @patch("job.tasks.helpers.GetiOTXInterfaceAdapter")
    @patch("job.tasks.helpers.ModelRepo")
    def test_finalize_optimize(
        self,
        mock_model_repo,
        mock_geti_otx_interface_adapter,
        fxt_optimization_trainer_ctx,
        keep_mlflow_artifacts,
    ):
        finalize_optimize(trainer_ctx=fxt_optimization_trainer_ctx, keep_mlflow_artifacts=keep_mlflow_artifacts)

        mock_adapter = mock_geti_otx_interface_adapter.return_value

        mock_adapter.update_output_model_for_optimize.assert_called_once_with(
            fxt_optimization_trainer_ctx.model_to_optimize
        )
        mock_model_repo().save.assert_called_once_with(fxt_optimization_trainer_ctx.model_to_optimize)
        if keep_mlflow_artifacts:
            mock_adapter.clean.assert_not_called()
        else:
            mock_adapter.clean.assert_called_once()
