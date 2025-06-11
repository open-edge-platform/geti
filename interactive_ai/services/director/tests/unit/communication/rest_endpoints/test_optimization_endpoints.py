# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from http import HTTPStatus
from unittest.mock import patch

from testfixtures import compare

from communication.controllers.optimization_controller import OptimizationController

from geti_types import ID

DUMMY_ORGANIZATION_ID = "567890123456789012340001"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_MODEL_GROUP_ID = "455765556788919199980000"
DUMMY_MODEL_ID = "923857474846573626510000"

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_PROJECT_PATTERN = f"{API_WORKSPACE_PATTERN}/projects/{DUMMY_PROJECT_ID}"
API_MODEL_GROUP_PATTERN = f"{API_PROJECT_PATTERN}/model_groups/{DUMMY_MODEL_GROUP_ID}"
API_MODEL_PATTERN = f"{API_MODEL_GROUP_PATTERN}/models/{DUMMY_MODEL_ID}"
API_OPTIMIZE_PATTERN_LEGACY = f"{API_MODEL_PATTERN}/optimize"
API_OPTIMIZE_PATTERN = f"{API_MODEL_PATTERN}:optimize"


def do_nothing(self, *args, **kwargs) -> None:
    return None


class TestOptimizationRESTEndpoint:
    def test_model_optimization_endpoint(self, fxt_director_app) -> None:
        dummy_jobs_rest = {"dummy_job_rest_key": "dummy_job_rest_value"}

        with (
            patch.object(OptimizationController, "__init__", new=do_nothing),
            patch.object(
                OptimizationController,
                "start_optimization",
                return_value=dummy_jobs_rest,
            ) as mock_optimization_result,
        ):
            result = fxt_director_app.post(API_OPTIMIZE_PATTERN)

        mock_optimization_result.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            model_storage_id=ID(DUMMY_MODEL_GROUP_ID),
            model_id=ID(DUMMY_MODEL_ID),
            author=ID("dummy_user"),
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), dummy_jobs_rest, ignore_eq=True)
