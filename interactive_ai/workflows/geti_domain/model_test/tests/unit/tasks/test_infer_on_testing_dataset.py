# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from copy import copy
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from iai_core.entities.model import ModelFormat
from iai_core.repos import DatasetRepo, ModelTestResultRepo, ProjectRepo
from iai_core.utils.dataset_helper import DatasetHelper
from jobs_common.exceptions import UnsupportedModelFormatForModelTestingException
from jobs_common_extras.evaluation.services.batch_inference import BatchInference

import job.tasks.model_testing
from job.tasks.model_testing import infer_on_testing_dataset

WORKSPACE_ID = "workspace_id"
PROJECT_ID = "project_id"
MODEL_TEST_RESULT_ID = "model_test_result_id"


@pytest.fixture
def fxt_model_base_framework(fxt_model):
    model = copy(fxt_model)
    model.model_format = ModelFormat.BASE_FRAMEWORK
    yield model


@pytest.mark.JobsComponent
class TestInferOnTestingDataset:
    def test_infer_on_testing_dataset(
        self,
        fxt_empty_project,
        fxt_model_test_result,
        fxt_dataset_non_empty_2,
        fxt_task_node,
        fxt_dataset,
    ) -> None:
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
            patch.object(ModelTestResultRepo, "get_by_id", return_value=fxt_model_test_result),
            patch.object(ModelTestResultRepo, "save", return_value=None),
            patch.object(
                job.tasks.model_testing,
                "_get_task_node",
                return_value=fxt_task_node,
            ),
            patch.object(BatchInference, "__init__", return_value=None),
            patch.object(BatchInference, "output_datasets", new_callable=PropertyMock) as mock_output_dataset,
            patch.object(BatchInference, "run", return_value=None) as mock_batch_inference_run,
            patch.object(DatasetRepo, "get_by_id", return_value=fxt_dataset_non_empty_2),
            patch.object(DatasetRepo, "__init__", return_value=None),
            patch.object(ProjectRepo, "__init__", return_value=None),
            patch.object(
                DatasetHelper,
                "create_dataset_up_to_task_from_media_identifiers",
                return_value=fxt_dataset_non_empty_2,
            ),
            patch.object(DatasetRepo, "save_deep", return_value=None),
            patch.object(
                ModelTestResultRepo,
                "__init__",
                return_value=None,
            ),
        ):
            mock_output_dataset.return_value = [fxt_dataset_non_empty_2]
            output_dataset = infer_on_testing_dataset(
                project_id=PROJECT_ID,
                model_test_result_id=MODEL_TEST_RESULT_ID,
                gt_dataset=fxt_dataset,
            )

        mock_batch_inference_run.assert_called_once()
        assert output_dataset == fxt_dataset_non_empty_2

    def test_unsupported_model_format(
        self,
        fxt_empty_project,
        fxt_dataset_non_empty_2,
        fxt_task_node,
        fxt_model_base_framework,
        fxt_dataset,
    ) -> None:
        mock_model_test = MagicMock()
        mock_model_test.get_model.return_value = fxt_model_base_framework
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
            patch.object(ModelTestResultRepo, "get_by_id", return_value=mock_model_test),
            patch.object(ModelTestResultRepo, "save", return_value=None),
            patch.object(job.tasks.model_testing, "_get_task_node", return_value=fxt_task_node),
            patch.object(DatasetRepo, "get_by_id", return_value=fxt_dataset_non_empty_2),
            patch.object(
                ModelTestResultRepo,
                "__init__",
                return_value=None,
            ),
            pytest.raises(UnsupportedModelFormatForModelTestingException),
        ):
            infer_on_testing_dataset(
                project_id=PROJECT_ID,
                model_test_result_id=MODEL_TEST_RESULT_ID,
                gt_dataset=fxt_dataset,
            )
