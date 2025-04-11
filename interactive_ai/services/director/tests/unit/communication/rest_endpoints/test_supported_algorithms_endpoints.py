# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import json
from http import HTTPStatus
from unittest.mock import patch

from communication.controllers.supported_algorithm_controller import SupportedAlgorithmRESTController

from sc_sdk.repos import TaskNodeRepo

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
