# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
from http import HTTPStatus
from unittest.mock import patch

from testfixtures import compare

from communication.controllers.model_test_controller import ModelTestController

from geti_types import ID
from iai_core_py.repos import ModelTestResultRepo, ProjectRepo
from iai_core_py.utils.deletion_helpers import DeletionHelpers

DUMMY_ORGANIZATION_ID = "567890123456789012340001"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_MODEL_TEST_ID = "567890123456789012340002"
DUMMY_PREDICTION_ID = "457678923456789012340000"

API_BASE_PATTERN = (
    f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}/workspaces/{DUMMY_WORKSPACE_ID}/projects/{DUMMY_PROJECT_ID}"
)


class TestModelTestsRESTEndpoint:
    def test_model_tests_endpoint_get(self, fxt_director_app, fxt_model_test_results_rest) -> None:
        # Arrange
        endpoint = f"{API_BASE_PATTERN}/tests"

        # Act
        with patch.object(
            ModelTestController,
            "get_all_model_test_results",
            return_value=fxt_model_test_results_rest,
        ) as mock_model_test_results:
            result = fxt_director_app.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_model_test_results.assert_called_once()
        compare(json.loads(result.content), fxt_model_test_results_rest, ignore_eq=True)

    def test_model_tests_endpoint_post(self, fxt_director_app, fxt_model_test_job_rest) -> None:
        # Arrange
        endpoint = f"{API_BASE_PATTERN}/tests"

        # Act
        with patch.object(
            ModelTestController,
            "create_and_submit_job",
            return_value=fxt_model_test_job_rest,
        ) as mock_create_model_test:
            result = fxt_director_app.post(endpoint, json={})

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_create_model_test.assert_called_once()
        compare(json.loads(result.content), fxt_model_test_job_rest, ignore_eq=True)

    def test_model_test_endpoint_get(
        self,
        fxt_director_app,
        fxt_model_test_result_rest,
    ) -> None:
        # Arrange
        endpoint = f"{API_BASE_PATTERN}/tests/{DUMMY_MODEL_TEST_ID}"

        # Act
        with patch.object(
            ModelTestController,
            "get_model_test_result",
            return_value=fxt_model_test_result_rest,
        ) as mock_model_test_result:
            result = fxt_director_app.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_model_test_result.assert_called_once()
        compare(json.loads(result.content), fxt_model_test_result_rest, ignore_eq=True)

    def test_model_test_endpoint_delete(self, fxt_director_app, fxt_project, fxt_model_test_result) -> None:
        # Arrange
        endpoint = f"{API_BASE_PATTERN}/tests/{DUMMY_MODEL_TEST_ID}"

        # Act
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project),
            patch.object(ModelTestResultRepo, "get_by_id", return_value=fxt_model_test_result),
            patch.object(
                DeletionHelpers,
                "delete_model_test_result",
            ) as mock_delete_test_result,
        ):
            result = fxt_director_app.delete(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_delete_test_result.assert_called_once_with(
            project_identifier=fxt_project.identifier, model_test_result=fxt_model_test_result
        )

    def test_get_model_tests_prediction_endpoint(self, fxt_director_app, fxt_model_test_results_rest) -> None:
        # Arrange
        endpoint = f"{API_BASE_PATTERN}/tests/{DUMMY_MODEL_TEST_ID}/predictions/{DUMMY_PREDICTION_ID}"

        # Act
        with patch.object(
            ModelTestController,
            "get_model_test_prediction",
            return_value=fxt_model_test_results_rest,
        ) as mock_get_prediction:
            result = fxt_director_app.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_get_prediction.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
            model_test_result_id=ID(DUMMY_MODEL_TEST_ID),
            prediction_id=ID(DUMMY_PREDICTION_ID),
        )
        compare(json.loads(result.content), fxt_model_test_results_rest, ignore_eq=True)
