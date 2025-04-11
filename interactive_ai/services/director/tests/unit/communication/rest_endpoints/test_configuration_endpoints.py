# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

from testfixtures import compare

from communication.controllers.configuration_controller import ConfigurationRESTController

from geti_types import ID

DUMMY_USER = ID("dummy_user")
DUMMY_ORGANIZATION_ID = "6682a33b-3d18-4dab-abee-f797090480e0"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_TASK_ID = "42d31793d5f1fb7e6efa6642"
DUMMY_DATA = {"dummy_key": "dummy_value"}
API_PROJECT_PATTERN = (
    f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}/workspaces/{DUMMY_WORKSPACE_ID}/projects/{DUMMY_PROJECT_ID}"
)
API_CONFIGURATION_PATTERN = f"{API_PROJECT_PATTERN}/configuration"


class TestConfigurationRESTEndpoint:
    def test_set_task_chain_configuration_endpoint_error_handling(self, fxt_director_app) -> None:
        # Arrange
        endpoint = f"{API_CONFIGURATION_PATTERN}/task_chain"
        request_body: dict = {}

        # Act and Assert
        result = fxt_director_app.post(endpoint, json=request_body)

        assert result.status_code == 400

    def test_task_chain_configuration_endpoint_get(self, fxt_director_app) -> None:
        # Arrange
        endpoint = f"{API_CONFIGURATION_PATTERN}/task_chain"

        # Act
        with patch.object(
            ConfigurationRESTController,
            "get_task_chain_configuration",
            return_value=DUMMY_DATA,
        ) as mock_get_task_chain_config:
            result = fxt_director_app.get(endpoint)

        # Assert
        mock_get_task_chain_config.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_task_chain_configuration_endpoint_post(self, fxt_director_app) -> None:
        # Arrange
        endpoint = f"{API_CONFIGURATION_PATTERN}/task_chain"
        request_data: dict = {}

        # Act
        with patch.object(
            ConfigurationRESTController,
            "validate_and_set_task_chain_configuration",
            return_value=DUMMY_DATA,
        ) as mock_validate_and_set_task_chain_config:
            result = fxt_director_app.post(endpoint, json=request_data)

        # Assert
        mock_validate_and_set_task_chain_config.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
            set_request=request_data,
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_set_global_configuration_endpoint_error_handling(self, fxt_director_app) -> None:
        # Arrange
        endpoint = f"{API_CONFIGURATION_PATTERN}/global"
        request_body: dict = {}

        # Act
        result = fxt_director_app.post(endpoint, json=request_body)

        # Assert
        assert result.status_code == 400

    def test_global_configuration_endpoint_get(self, fxt_director_app) -> None:
        # Arrange
        endpoint = f"{API_CONFIGURATION_PATTERN}/global"

        # Act
        with patch.object(
            ConfigurationRESTController,
            "get_global_configuration",
            return_value=DUMMY_DATA,
        ) as mock_get_global_config:
            result = fxt_director_app.get(endpoint)

        # Assert
        mock_get_global_config.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_global_configuration_endpoint_post(self, fxt_director_app) -> None:
        # Arrange
        endpoint = f"{API_CONFIGURATION_PATTERN}/global"
        request_data: dict = {}

        # Act
        with patch.object(
            ConfigurationRESTController,
            "validate_and_set_global_configuration",
            return_value=DUMMY_DATA,
        ) as mock_validate_and_set_global_config:
            result = fxt_director_app.post(endpoint, json=request_data)

        # Assert
        mock_validate_and_set_global_config.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
            set_request=request_data,
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_full_configuration_endpoint_get(self, fxt_director_app) -> None:
        # Arrange
        endpoint = API_CONFIGURATION_PATTERN

        # Act
        with patch.object(
            ConfigurationRESTController,
            "get_full_configuration",
            return_value=DUMMY_DATA,
        ) as mock_get_full_config:
            result = fxt_director_app.get(endpoint)

        # Assert
        mock_get_full_config.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_full_configuration_endpoint_post(self, fxt_director_app) -> None:
        # Arrange
        endpoint = API_CONFIGURATION_PATTERN
        request_data: dict = {}

        # Act
        with patch.object(
            ConfigurationRESTController,
            "set_full_configuration",
            return_value=DUMMY_DATA,
        ) as mock_set_full_config:
            result = fxt_director_app.post(endpoint, json=request_data)

        # Assert
        mock_set_full_config.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
            set_request=request_data,
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_task_configuration_endpoint_get(self, fxt_director_app) -> None:
        # Arrange
        dummy_model_id = "dummy_model_id"
        dummy_algorithm = "dummy_algo"
        endpoint = (
            f"{API_CONFIGURATION_PATTERN}/task_chain/{DUMMY_TASK_ID}"
            f"?model_id={dummy_model_id}&algorithm_name={dummy_algorithm}"
        )

        # Act
        with patch.object(
            ConfigurationRESTController,
            "get_task_or_model_configuration",
            return_value=DUMMY_DATA,
        ) as mock_get_task_or_model_config:
            result = fxt_director_app.get(endpoint)

        # Assert
        mock_get_task_or_model_config.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
            task_id=ID(DUMMY_TASK_ID),
            model_id=dummy_model_id,
            algorithm_name=dummy_algorithm,
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_task_configuration_endpoint_post(self, fxt_director_app) -> None:
        # Arrange
        endpoint = f"{API_CONFIGURATION_PATTERN}/task_chain/{DUMMY_TASK_ID}"
        request_data: dict = {}

        # Act
        with patch.object(
            ConfigurationRESTController,
            "set_task_configuration",
            return_value=DUMMY_DATA,
        ) as mock_set_task_or_model_config:
            result = fxt_director_app.post(endpoint, json=request_data)

        # Assert
        mock_set_task_or_model_config.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
            task_id=ID(DUMMY_TASK_ID),
            set_request=request_data,
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)
