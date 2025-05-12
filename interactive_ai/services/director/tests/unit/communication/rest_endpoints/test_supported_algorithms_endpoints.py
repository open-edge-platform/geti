# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from http import HTTPStatus
from unittest.mock import patch

from communication.controllers.supported_algorithm_controller import SupportedAlgorithmRESTController

from iai_core.repos import TaskNodeRepo

DUMMY_ORGANIZATION_ID = "567890123456789012340001"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_PROJECT_ID = "234567890123456789010000"

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_PROJECT_PATTERN = f"{API_WORKSPACE_PATTERN}/projects/{DUMMY_PROJECT_ID}"


class TestSupportedAlgorithmsEndpoints:
    def test_supported_algorithms_endpoint(self, fxt_director_app, fxt_task) -> None:
        # Arrange
        endpoint = f"{API_PROJECT_PATTERN}/supported_algorithms"
        dummy_rest_response = {"key": "value"}

        # Act
        with (
            patch.object(
                SupportedAlgorithmRESTController,
                "get_supported_algorithms",
                return_value=dummy_rest_response,
            ) as mock_get_supported_algorithms,
            patch.object(TaskNodeRepo, "get_trainable_task_nodes", return_value=[fxt_task]),
        ):
            result = fxt_director_app.get(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_get_supported_algorithms.assert_called_once_with(
            task_types={fxt_task.task_properties.task_type}, include_obsolete=True
        )
        assert json.loads(result.content) == dummy_rest_response
