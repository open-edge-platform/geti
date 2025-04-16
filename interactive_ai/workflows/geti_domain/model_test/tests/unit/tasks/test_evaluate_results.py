# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from sc_sdk.repos import MediaScoreRepo, ModelTestResultRepo, ProjectRepo

from job.tasks.model_testing import evaluate_results

WORKSPACE_ID = "workspace_id"
PROJECT_ID = "project_id"
MODEL_TEST_RESULT_ID = "model_test_result_id"


@pytest.mark.JobsComponent
class TestEvaluateResults:
    @patch("job.tasks.model_testing.evaluate_and_save_results")
    def test_evaluate_results(
        self,
        mocked_evaluate,
        fxt_project,
        fxt_model_test_result,
        fxt_dataset,
        fxt_task_node,
    ) -> None:
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project),
            patch.object(ModelTestResultRepo, "get_by_id", return_value=fxt_model_test_result),
            patch.object(ProjectRepo, "__init__", return_value=None),
            patch.object(MediaScoreRepo, "__init__", return_value=None),
            patch.object(
                ModelTestResultRepo,
                "__init__",
                return_value=None,
            ),
            patch.object(
                ModelTestResultRepo,
                "save",
                return_value=None,
            ) as mocked_model_test_result_save,
            patch(
                "job.tasks.model_testing._get_task_node",
                return_value=fxt_task_node,
            ),
            patch("job.tasks.model_testing.report_progress") as mock_report_progress,
        ):
            evaluate_results(
                project_id=PROJECT_ID,
                model_test_result_id=MODEL_TEST_RESULT_ID,
                gt_dataset=fxt_dataset,
                output_dataset=fxt_dataset,
            )

        mocked_evaluate.assert_called_once_with(
            project_identifier=fxt_project.identifier,
            evaluation_results=[fxt_model_test_result],
            task_type=fxt_task_node.task_properties.task_type,
            progress_callback=mock_report_progress,
            progress_message="Evaluating on testing dataset",
        )
        mocked_model_test_result_save.assert_called()
