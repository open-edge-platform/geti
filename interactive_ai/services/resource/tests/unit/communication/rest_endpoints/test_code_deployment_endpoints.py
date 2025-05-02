# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from http import HTTPStatus
from pathlib import Path
from tempfile import TemporaryDirectory, mkstemp
from unittest.mock import ANY, MagicMock, patch

import pytest
from testfixtures import compare

from communication.rest_controllers import CodeDeploymentRESTController, DeploymentPackageRESTController

from geti_types import ID, ProjectIdentifier
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

MODEL_IDENTIFIER_LIST = [
    {
        "model_id": "6138af293b7b11505c43f2bc",
        "model_group_id": "6138af293b7b11505c43f1dq",
    },
    {
        "model_id": "6138af293b7b11505c43f7ef",
        "model_group_id": "6138af293b7b11505c43f1dq",
    },
]
MODEL_IDENTIFIER_LIST_INVALID_EMPTY: list[dict] = []
MODEL_IDENTIFIER_LIST_INVALID_MISSING_MODEL_ID: list[dict] = [
    {"model_group_id": "6138af293b7b11505c43f1dq"},
]
MODEL_IDENTIFIER_LIST_INVALID_MISSING_MODEL_GROUP_ID: list[dict] = [
    {"model_id": "6138af293b7b11505c43f7ef"},
]

DUMMY_CODE_DEPLOYMENT_REST = {
    "id": "6138afea3b7b11505c43f2f1",
    "progress": 0.0,
    "state": "PREPARING",
    "models": MODEL_IDENTIFIER_LIST,
    "creator_id": "dummy_user",
    "creation_time": "2021-06-30T09:25:20.472000+00:00",
}

DUMMY_CODE_DEPLOYMENT_ID = "6138afea3b7b11505c43f2f1"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_ORGANIZATION_ID = "6682a33b-3d18-4dab-abee-f797090480e0"
API_BASE_PATTERN = (
    f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}/workspaces/{DUMMY_WORKSPACE_ID}/projects/{DUMMY_PROJECT_ID}"
)
API_CODE_DEPLOYMENTS_PATTERN = f"{API_BASE_PATTERN}/code_deployments"
API_CODE_DEPLOYMENT_PATTERN = f"{API_CODE_DEPLOYMENTS_PATTERN}/<deployment_id>"

API_DEPLOYMENT_PACKAGE_PATTERN = f"{API_BASE_PATTERN}/deployment_package"

DEPLOYMENT_PACKAGE_OVMS_REQUEST = {
    "package_type": "ovms",
    "models": [{"model_id": "6138af293b7b11505c43f7ef"}],
}
DEPLOYMENT_PACKAGE_CODE_REQUEST = {
    "package_type": "geti_sdk",
    "models": [{"model_id": "6138af293b7b11505c43f7ef"}],
}
DEPLOYMENT_PACKAGE_INVALID_TYPE_REQUEST = {
    "package_type": "invalid",
    "models": [{"model_id": "6138af293b7b11505c43f7ef"}],
}
DEPLOYMENT_PACKAGE_INVALID_BODY_REQUEST = {"a": 1}


class TestCodeDeploymentRESTEndpoint:
    def test_prepare_code_deployment_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_CODE_DEPLOYMENTS_PATTERN}:prepare"

        # Act
        with patch.object(
            CodeDeploymentRESTController,
            "prepare_for_code_deployment",
            return_value=DUMMY_CODE_DEPLOYMENT_REST,
        ) as mock_prepare_for_code_deployment:
            result = fxt_resource_rest.post(endpoint, json=MODEL_IDENTIFIER_LIST)

        # Assert
        mock_prepare_for_code_deployment.assert_called_once_with(
            organization_id=ID(DUMMY_ORGANIZATION_ID),
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
            model_list_rest=MODEL_IDENTIFIER_LIST,
            user_id=ANY,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_CODE_DEPLOYMENT_REST, ignore_eq=True)

    @pytest.mark.parametrize(
        "request_body",
        [
            MODEL_IDENTIFIER_LIST_INVALID_EMPTY,
            MODEL_IDENTIFIER_LIST_INVALID_MISSING_MODEL_ID,
            MODEL_IDENTIFIER_LIST_INVALID_MISSING_MODEL_GROUP_ID,
        ],
        ids=[
            "empty list of models",
            "missing model ID",
            "missing model group ID",
        ],
    )
    def test_prepare_code_deployment_endpoint_invalid_body(self, request_body, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_CODE_DEPLOYMENTS_PATTERN}:prepare"

        # Act
        response = fxt_resource_rest.post(endpoint, json=request_body)

        # Assert
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_code_deployment_detail_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_CODE_DEPLOYMENTS_PATTERN}/{DUMMY_CODE_DEPLOYMENT_ID}"

        # Act
        with patch.object(
            CodeDeploymentRESTController,
            "get_code_deployment_detail",
            return_value=DUMMY_CODE_DEPLOYMENT_REST,
        ) as mock_get_code_deployment_detail:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_code_deployment_detail.assert_called_once_with(
            project_identifier=ProjectIdentifier(
                workspace_id=ID(DUMMY_WORKSPACE_ID),
                project_id=ID(DUMMY_PROJECT_ID),
            ),
            code_deployment_id=DUMMY_CODE_DEPLOYMENT_ID,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_CODE_DEPLOYMENT_REST, ignore_eq=True)

    def test_download_code_deployment_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_CODE_DEPLOYMENTS_PATTERN}/{DUMMY_CODE_DEPLOYMENT_ID}/download"
        project_identifier = ProjectIdentifier(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
        )

        with TemporaryDirectory() as temp_dir:
            temp_file_path = f"{temp_dir}/dummy_code_deployment.zip"
            with open(temp_file_path, "w") as temp_file:
                temp_file.write("This is some data.")
            code_deployment_response = (
                Path(temp_file_path),
                "dummy_code_deployment.zip",
            )
            with patch.object(
                CodeDeploymentRESTController,
                "get_filepath_by_deployment_id",
                return_value=code_deployment_response,
            ) as mock_get_filepath_by_deployment_id:
                # Act
                result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_filepath_by_deployment_id.assert_called_once_with(
            project_identifier=project_identifier,
            code_deployment_id=IDToMongo.backward(DUMMY_CODE_DEPLOYMENT_ID),
        )
        assert result.status_code == HTTPStatus.OK

    @pytest.mark.parametrize(
        "request_json,expected_code",
        [
            (
                DEPLOYMENT_PACKAGE_OVMS_REQUEST,
                HTTPStatus.OK,
            ),
            (
                DEPLOYMENT_PACKAGE_CODE_REQUEST,
                HTTPStatus.OK,
            ),
            (DEPLOYMENT_PACKAGE_INVALID_TYPE_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY),
            (DEPLOYMENT_PACKAGE_INVALID_BODY_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY),
        ],
    )
    def test_download_deployment_package(self, fxt_resource_rest, request_json, expected_code) -> None:
        # Arrange
        endpoint = f"{API_DEPLOYMENT_PACKAGE_PATTERN}:download"
        project_identifier = ProjectIdentifier(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
        )

        download_package_mock = MagicMock()
        _, filename = mkstemp()
        download_package_mock.return_value = Path(filename)

        # Act
        with patch.multiple(
            DeploymentPackageRESTController,
            download_ovms_package=download_package_mock,
            download_geti_sdk_package=download_package_mock,
        ):
            result = fxt_resource_rest.post(endpoint, json=request_json)

        # Assert
        if expected_code == HTTPStatus.OK:
            download_package_mock.assert_called_once_with(
                project_identifier=project_identifier,
                deployment_package_json=request_json,
            )

        assert result.status_code == expected_code
