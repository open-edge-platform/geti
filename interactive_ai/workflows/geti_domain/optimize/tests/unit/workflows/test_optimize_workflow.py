# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from flytekit.core.testing import task_mock
from iai_core.entities.model import ModelOptimizationType

from job.tasks.evaluation_task import evaluate_optimized_model_pot
from job.tasks.optimization_task import shard_dataset_prepare_models_and_start_optimization
from job.workflows.optimize_workflow import optimize_workflow_pot


@pytest.mark.JobsComponent
class TestOptimize:
    def test_optimize_workflow_pot(self, fxt_optimization_trainer_ctx) -> None:
        with (
            task_mock(shard_dataset_prepare_models_and_start_optimization) as mock_shard_dataset_and_start_optimization,
            task_mock(evaluate_optimized_model_pot) as mock_evaluate,
        ):
            mock_shard_dataset_and_start_optimization.return_value = fxt_optimization_trainer_ctx
            optimize_workflow_pot(
                project_id="project_id",
                dataset_storage_id="dataset_storage_id",
                model_storage_id="model_storage_id",
                model_id="model_id",
                enable_optimize_from_dataset_shard=True,
            )
            mock_shard_dataset_and_start_optimization.assert_called_once_with(
                project_id="project_id",
                model_storage_id="model_storage_id",
                model_id="model_id",
                max_shard_size=1000,
                num_image_pulling_threads=10,
                num_upload_threads=2,
                enable_optimize_from_dataset_shard=True,
                optimization_type=ModelOptimizationType.POT.name,
                command=["bash", "-c", "run"],
                min_annotation_size=None,
                max_number_of_annotations=None,
            )
            mock_evaluate.assert_called_once_with(
                trainer_ctx=fxt_optimization_trainer_ctx,
                model_id="model_id",
                dataset_storage_id="dataset_storage_id",
                keep_mlflow_artifacts=False,
                min_annotation_size=None,
                max_number_of_annotations=None,
            )
