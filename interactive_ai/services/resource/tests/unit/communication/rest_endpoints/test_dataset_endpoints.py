# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from http import HTTPStatus
from unittest.mock import patch

from testfixtures import compare

from communication.rest_controllers import DatasetRESTController

from geti_types import ID

DUMMY_ORGANIZATION_ID = "567890123456789012340001"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_DATASET_ID = "012345678901234567890000"
DUMMY_DATASET_REVISION_ID = "42d31793d5f1fb7e6efa6642"
DUMMY_DATA = {"dummy_key": "value"}

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_PROJECT_PATTERN = f"{API_WORKSPACE_PATTERN}/projects/{DUMMY_PROJECT_ID}"
API_DATASET_PATTERN = f"{API_PROJECT_PATTERN}/datasets/{DUMMY_DATASET_ID}"

HEADERS = {"Content-Type": "application/json"}


class TestDatasetRESTEndpoint:
    def test_datasets_endpoint_post_error_handling(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_PROJECT_PATTERN}/datasets"
        data: dict = {}  # invalid data

        # Act
        result = fxt_resource_rest.post(endpoint, json=data, headers=HEADERS)

        # Assert
        assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_datasets_endpoint_get(self, fxt_resource_rest, fxt_project, fxt_dataset_storage) -> None:
        # Arrange
        endpoint = f"{API_PROJECT_PATTERN}/datasets"

        # Act
        with patch.object(
            DatasetRESTController,
            "get_dataset_storages",
            return_value=DUMMY_DATA,
        ) as mock_get_dataset_storages:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_dataset_storages.assert_called_once_with(project_id=ID(DUMMY_PROJECT_ID))
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_datasets_endpoint_post(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_PROJECT_PATTERN}/datasets"
        request_data: dict = {}

        # Act
        with patch.object(
            DatasetRESTController,
            "create_dataset_storage",
            return_value=DUMMY_DATA,
        ) as mock_get_dataset_storages:
            result = fxt_resource_rest.post(endpoint, json=request_data, headers=HEADERS)

        # Assert
        mock_get_dataset_storages.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            data=request_data,
        )
        assert result.status_code == HTTPStatus.CREATED
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_dataset_endpoint_get(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = API_DATASET_PATTERN

        # Act
        with patch.object(
            DatasetRESTController,
            "get_dataset_storage",
            return_value=DUMMY_DATA,
        ) as mock_get_dataset_storage:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_dataset_storage.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=ID(DUMMY_DATASET_ID),
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_dataset_endpoint_put(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = API_DATASET_PATTERN
        request_data: dict = {"dummy": "new_value"}

        # Act
        with patch.object(
            DatasetRESTController,
            "update_dataset_storage",
            return_value=DUMMY_DATA,
        ) as mock_update_dataset_storage:
            result = fxt_resource_rest.put(endpoint, json=request_data)

        # Assert
        mock_update_dataset_storage.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=ID(DUMMY_DATASET_ID),
            data=request_data,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_dataset_endpoint_delete(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = API_DATASET_PATTERN

        # Act
        with patch.object(
            DatasetRESTController,
            "delete_dataset_storage",
            return_value=DUMMY_DATA,
        ) as mock_delete_dataset_storage:
            result = fxt_resource_rest.delete(endpoint)

        # Assert
        mock_delete_dataset_storage.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=ID(DUMMY_DATASET_ID),
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_dataset_storage_statistics_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_DATASET_PATTERN}/statistics"

        # Act
        with patch.object(
            DatasetRESTController,
            "get_dataset_storage_statistics",
            return_value=DUMMY_DATA,
        ) as mock_get_statistics:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_statistics.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=ID(DUMMY_DATASET_ID),
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_dataset_storage_statistics_endpoint_task(self, fxt_resource_rest) -> None:
        # Arrange
        dummy_task_id = "012345678901234567891234"
        endpoint = f"{API_DATASET_PATTERN}/statistics?task_id={dummy_task_id}"

        # Act
        with patch.object(
            DatasetRESTController,
            "get_dataset_storage_statistics_for_task",
            return_value=DUMMY_DATA,
        ) as mock_get_statistics_for_task:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_statistics_for_task.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=ID(DUMMY_DATASET_ID),
            task_id=ID(dummy_task_id),
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_dataset_statistics_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_DATASET_PATTERN}/training_revisions/{DUMMY_DATASET_REVISION_ID}"

        # Act
        with patch.object(
            DatasetRESTController,
            "get_dataset_statistics",
            return_value=DUMMY_DATA,
        ) as mock_get_dataset_statistics:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_dataset_statistics.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=ID(DUMMY_DATASET_ID),
            dataset_id=ID(DUMMY_DATASET_REVISION_ID),
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)
