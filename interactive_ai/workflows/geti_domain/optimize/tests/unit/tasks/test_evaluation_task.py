# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import MagicMock, patch

import jobs_common.tasks.utils.secrets
import pytest
from iai_core_py.entities.datasets import Dataset, DatasetPurpose
from iai_core_py.entities.evaluation_result import EvaluationPurpose
from iai_core_py.repos import (
    DatasetRepo,
    DatasetStorageRepo,
    EvaluationResultRepo,
    ModelRepo,
    ModelStorageRepo,
    ProjectRepo,
)
from iai_core_py.utils.dataset_helper import DatasetHelper
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset

from tests.unit.tasks.mock_utils import mock_decorator

patch("jobs_common.tasks.utils.progress.task_progress", mock_decorator).start()
from job.tasks.evaluation_task import _evaluate_optimized_model, evaluate_optimized_model_pot  # noqa: E402

PROJECT_ID = "project_id"
MODEL_STORAGE_ID = "model_storage_id"
DATASET_STORAGE_ID = "dataset_storage_id"
MODEL_ID = "model_id"


@pytest.fixture
def fxt_secrets(mocker):
    return mocker.patch(
        "job.tasks.optimize_model.SECRETS",
        new=None,
        autospec=False,
    )


@pytest.mark.JobsComponent
@patch.object(jobs_common.tasks.utils.secrets, "set_env_vars", return_value=None)
@patch.object(jobs_common.tasks.utils.secrets, "setup_session_from_env", return_value=None)
class TestEvaluationTask:
    @patch("job.tasks.evaluation_task._evaluate_optimized_model")
    @patch("job.tasks.evaluation_task.finalize_optimize")
    def test_evaluate_optimized_model_pot(
        self,
        mock_finalize_optimize,
        mock_evaluate_optimized_model,
        mock_setup_session_from_env,
        mock_set_env_vars,
        fxt_optimization_trainer_ctx,
    ) -> None:
        evaluate_optimized_model_pot(
            trainer_ctx=fxt_optimization_trainer_ctx,
            dataset_storage_id=DATASET_STORAGE_ID,
            model_id=MODEL_ID,
        )

        mock_finalize_optimize.assert_called_once_with(
            trainer_ctx=fxt_optimization_trainer_ctx,
            keep_mlflow_artifacts=False,
        )

        mock_evaluate_optimized_model.assert_called_once_with(
            project_id=fxt_optimization_trainer_ctx.project_id,
            dataset_storage_id=DATASET_STORAGE_ID,
            model_storage_id=fxt_optimization_trainer_ctx.model_storage_id,
            model_id=MODEL_ID,
            optimized_model_id=fxt_optimization_trainer_ctx.model_to_optimize_id,
            min_annotation_size=None,
            max_number_of_annotations=None,
        )

    def test_evaluate_model(
        self,
        fxt_secrets,
        fxt_project,
        fxt_model_storage_detection,
        fxt_model,
        fxt_dataset_storage,
    ) -> None:
        mock_task_node = MagicMock()
        mock_dataset = MagicMock()
        mock_testing_dataset = MagicMock()
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project),
            patch.object(DatasetStorageRepo, "get_by_id", return_value=fxt_dataset_storage),
            patch("job.tasks.evaluation_task._find_task_node_for_model", return_value=mock_task_node),
            patch("job.tasks.evaluation_task.infer_and_evaluate", return_value=None) as mock_infer_and_evaluate_task,
            patch.object(
                DatasetHelper, "create_dataset_with_filtered_annotations_up_to_task", return_value=mock_dataset
            ),
            patch.object(Dataset, "get_subset", return_value=mock_testing_dataset),
            patch.object(DatasetRepo, "save_deep", return_value=None),
            patch.object(ModelStorageRepo, "get_by_id", return_value=fxt_model_storage_detection),
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model),
            patch.object(EvaluationResultRepo, "save", return_value=None),
            patch.object(DatasetRepo, "save_deep", return_value=None),
        ):
            _evaluate_optimized_model(
                project_id=PROJECT_ID,
                dataset_storage_id=DATASET_STORAGE_ID,
                model_storage_id=MODEL_STORAGE_ID,
                model_id=MODEL_ID,
                optimized_model_id=MODEL_ID,
            )

        mock_infer_and_evaluate_task.assert_called_once_with(
            project_identifier=fxt_project.identifier,
            task_node=mock_task_node,
            model=fxt_model,
            batch_inference_datasets=[
                BatchInferenceDataset(
                    dataset_storage=fxt_dataset_storage,
                    input_dataset=mock_dataset,
                    annotated_dataset=mock_testing_dataset,
                    output_dataset_purpose=DatasetPurpose.EVALUATION,
                    evaluation_purpose=EvaluationPurpose.TEST,
                )
            ],
        )
