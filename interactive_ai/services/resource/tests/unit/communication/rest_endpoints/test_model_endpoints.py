# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import io
from http import HTTPStatus
from unittest.mock import patch

from testfixtures import compare

from communication.rest_controllers import ModelRESTController
from managers.project_manager import ProjectManager

from geti_fastapi_tools.exceptions import InvalidIDException
from geti_types import ID

DUMMY_BYTES = b"DUMMY_BYTES"
DUMMY_ORGANIZATION_ID = "000000000000000000000001"
DUMMY_PROJECT_ID = ID("234567890123456789010000")
DUMMY_WORKSPACE_ID = ID("567890123456789012340000")
DUMMY_MODEL_GROUP_ID = ID("824574837374327843272841")
DUMMY_MODEL_ID = ID("452783490786444629506348")
API_PROJECT_PATTERN = (
    f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}/workspaces/{DUMMY_WORKSPACE_ID}/projects/{DUMMY_PROJECT_ID}"
)
API_MODEL_GROUP_PATTERN = f"{API_PROJECT_PATTERN}/model_groups/{DUMMY_MODEL_GROUP_ID}"
API_MODEL_PATTERN = f"{API_MODEL_GROUP_PATTERN}/models/{DUMMY_MODEL_ID}"

MOCK_RUNNING_TEST_JOB_ID = "123456789012345678901238"

MOCK_MODEL_ID = "123456789012345678901234"

MOCK_MODEL_GROUP_ID = "123456789012345678901235"

MOCK_LABEL_ID = "123456789012345678901236"

MOCK_LABEL_NAME = "mock_label_name"

MOCK_MODEL_TEST_RESULT: dict = {
    "id": 1234,
    "name": "Mock model testing",
    "creation_time": "2022-07-13T13:43:14.124000+00:00",
    "job_info": {"id": "mock_model_test_done", "status": "DONE"},
    "model_info": {
        "group_id": MOCK_MODEL_GROUP_ID,
        "id": MOCK_MODEL_ID,
        "template_id": "MOCK_MODEL_TEST_ARCHITECTURE",
        "task_type": "Mock task",
        "n_labels": 2,
        "version": 1,
    },
    "datasets_info": [
        {
            "id": 1234,
            "name": "Mock dataset",
            "n_images": 15,
            "n_frames": 10,
            "n_samples": 25,
        }
    ],
    "scores": [
        {"label_id": None, "name": "Mock accuracy", "value": 0.5},
        {"label_id": "1234", "name": "Mock accuracy", "value": 0.3},
        {"label_id": "12345", "name": "Mock accuracy", "value": 0.7},
    ],
}

MOCK_MODEL_TEST_RESULTS: dict = {
    "test_results": [
        {
            "id": 1234,
            "name": "Mock model testing 1",
            "creation_time": "2022-07-13T13:39:14.124000+00:00",
            "job_info": {"id": "mock_model_test_job_pending", "status": "PENDING"},
            "model_info": {
                "group_id": MOCK_MODEL_GROUP_ID,
                "id": MOCK_MODEL_ID,
                "template_id": "MOCK_MODEL_TEST_ARCHITECTURE",
                "task_type": "Mock task",
                "n_labels": 2,
                "version": 1,
            },
            "datasets_info": [
                {
                    "id": 1234,
                    "name": "Mock dataset",
                    "n_images": 15,
                    "n_frames": 10,
                    "n_samples": 25,
                }
            ],
            "scores": [
                {"label_id": None, "name": "Mock accuracy", "value": 0.5},
                {"label_id": "1234", "name": "Mock accuracy", "value": 0.3},
                {"label_id": "12345", "name": "Mock accuracy", "value": 0.7},
            ],
        },
        {
            "id": 1234,
            "name": "Mock model testing 2",
            "creation_time": "2022-07-13T13:40:14.124000+00:00",
            "job_info": {"id": MOCK_RUNNING_TEST_JOB_ID, "status": "INFERRING"},
            "model_info": {
                "group_id": MOCK_MODEL_GROUP_ID,
                "id": MOCK_MODEL_ID,
                "template_id": "MOCK_MODEL_TEST_ARCHITECTURE",
                "task_type": "Mock task",
                "n_labels": 2,
                "version": 1,
            },
            "datasets_info": [
                {
                    "id": 1234,
                    "name": "Mock dataset",
                    "n_images": 10,
                    "n_frames": 20,
                    "n_samples": 30,
                }
            ],
            "scores": [
                {"label_id": None, "name": "Mock accuracy", "value": 0.5},
                {"label_id": "1234", "name": "Mock accuracy", "value": 0.3},
                {"label_id": "12345", "name": "Mock accuracy", "value": 0.7},
            ],
        },
        {
            "id": 1234,
            "name": "Mock model testing 3",
            "creation_time": "2022-07-13T13:41:14.124000+00:00",
            "job_info": {"id": MOCK_RUNNING_TEST_JOB_ID, "status": "EVALUATING"},
            "model_info": {
                "group_id": MOCK_MODEL_GROUP_ID,
                "id": MOCK_MODEL_ID,
                "template_id": "MOCK_MODEL_TEST_ARCHITECTURE",
                "task_type": "Mock task",
                "n_labels": 2,
                "version": 1,
            },
            "datasets_info": [
                {
                    "id": 1234,
                    "name": "Mock dataset",
                    "n_images": 10,
                    "n_frames": 30,
                    "n_samples": 40,
                }
            ],
            "scores": [
                {"label_id": None, "name": "Mock accuracy", "value": 0.5},
                {"label_id": "1234", "name": "Mock accuracy", "value": 0.3},
                {"label_id": "12345", "name": "Mock accuracy", "value": 0.7},
            ],
        },
        {
            "id": 1234,
            "name": "Mock model testing 4",
            "creation_time": "2022-07-13T13:42:14.124000+00:00",
            "job_info": {"id": "mock_model_test_job_done", "status": "DONE"},
            "model_info": {
                "group_id": MOCK_MODEL_GROUP_ID,
                "id": MOCK_MODEL_ID,
                "template_id": "MOCK_MODEL_TEST_ARCHITECTURE",
                "task_type": "Mock task",
                "n_labels": 2,
                "version": 1,
            },
            "datasets_info": [
                {
                    "id": 1234,
                    "name": "Mock dataset",
                    "n_images": 10,
                    "n_frames": 40,
                    "n_samples": 50,
                }
            ],
            "scores": [
                {"label_id": None, "name": "Mock accuracy", "value": 0.5},
                {"label_id": "1234", "name": "Mock accuracy", "value": 0.3},
                {"label_id": "12345", "name": "Mock accuracy", "value": 0.7},
            ],
        },
    ],
}

MOCK_JOB: dict = {
    "id": MOCK_RUNNING_TEST_JOB_ID,
    "name": "Mock job",
    "creation_time": "2022-07-13T13:45:14.124000+00:00",
    "type": "test",
    "metadata": {
        "test": {
            "model_template_id": "MOCK_MODEL_TEST_ARCHITECTURE",
            "model_architecture": "MOCK MODEL TEST ARCHITECTURE",
            "datasets": [{"id": "MOCK DS", "name": "MOCK DS"}],
        },
        "project": {
            "id": 1234,
            "name": "Mock project",
        },
    },
}

MOCK_MODEL_DETAIL: dict = {
    "id": MOCK_MODEL_ID,
    "name": "Mock model detail",
    "architecture": "Mock Dataset Template",
    "creation_date": "2022-07-19T13:51:01.394000+00:00",
    "size": 10,
    "score_up_to_date": True,
    "fps_throughput": 0,
    "latency": 0,
    "performance": {"score": 0.0},
    "precision": ["FP32"],
    "target_device": "CPU",
    "target_device_type": None,
    "optimized_models": [],
    "labels": [
        {
            "id": MOCK_LABEL_ID,
            "name": MOCK_LABEL_NAME,
            "is_anomalous": False,
            "color": "#ff0000ff",
            "hotkey": "ctrl+V",
            "is_empty": False,
            "group": "from_label_list",
            "parent_id": None,
        }
    ],
    "training_dataset_info": {
        "dataset_storage_id": 12345,
        "dataset_revision_id": 123456,
    },
    "previous_revision_id": "",
    "previous_trained_revision_id": "",
}


class TestModelRESTEndpoint:
    def test_export_model_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_MODEL_PATTERN}/export"

        # Act
        with patch.object(
            ModelRESTController,
            "export_model",
            return_value=(io.BytesIO(DUMMY_BYTES), "base_model.zip"),
        ) as mock_export_model:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_export_model.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            model_id=ID(DUMMY_MODEL_ID),
            model_storage_id=ID(DUMMY_MODEL_GROUP_ID),
            model_only=True,
        )

        assert result.status_code == HTTPStatus.OK
        compare(result.content, DUMMY_BYTES, ignore_eq=True)

    def test_export_optimized_model_endpoint(self, fxt_resource_rest, fxt_mongo_id) -> None:
        # Arrange
        dummy_opt_model_id = fxt_mongo_id(4)
        endpoint = f"{API_MODEL_PATTERN}/optimized_models/{str(dummy_opt_model_id)}/export"

        # Act
        with patch.object(
            ModelRESTController,
            "export_model",
            return_value=(io.BytesIO(DUMMY_BYTES), "base_model.zip"),
        ) as mock_export_model:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_export_model.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            model_storage_id=ID(DUMMY_MODEL_GROUP_ID),
            model_id=ID(dummy_opt_model_id),
            model_only=False,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.content, DUMMY_BYTES, ignore_eq=True)

    def test_model_statistics_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_MODEL_PATTERN}/statistics"
        dummy_stats = {"dummy_stats": "value"}

        # Act
        with patch.object(
            ModelRESTController,
            "get_model_statistics",
            return_value=dummy_stats,
        ) as mock_statistics:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_statistics.assert_called_once_with(
            project_id=DUMMY_PROJECT_ID,
            model_storage_id=DUMMY_MODEL_GROUP_ID,
            model_id=DUMMY_MODEL_ID,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), dummy_stats, ignore_eq=True)

    def test_model_group_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_MODEL_GROUP_PATTERN}?include_lifecycle_stage=true"
        dummy_model_storage_rest = {"dummy_id": "dummy_model_storage"}

        # Act
        with patch.object(
            ModelRESTController,
            "get_model_group",
            return_value=dummy_model_storage_rest,
        ) as mock_get_model_group:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_model_group.assert_called_once_with(
            project_id=DUMMY_PROJECT_ID,
            model_storage_id=ID(DUMMY_MODEL_GROUP_ID),
            include_lifecycle_stage=True,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), dummy_model_storage_rest, ignore_eq=True)

    def test_model_groups_endpoint(self, fxt_resource_rest, fxt_mongo_id) -> None:
        # Arrange
        dummy_task_id = fxt_mongo_id(0)
        endpoint = f"{API_PROJECT_PATTERN}/model_groups?task_id={dummy_task_id}&include_lifecycle_stage=true"
        dummy_model_groups_rest = {"dummy_task": "dummy_model_storage"}

        # Act
        with patch.object(
            ModelRESTController,
            "get_all_model_groups",
            return_value=dummy_model_groups_rest,
        ) as mock_get_all_model_groups:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_all_model_groups.assert_called_once_with(
            project_id=DUMMY_PROJECT_ID,
            task_id=dummy_task_id,
            include_lifecycle_stage=True,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), dummy_model_groups_rest, ignore_eq=True)

    def test_model_groups_endpoint_invalid_task(self, fxt_resource_rest, fxt_project) -> None:
        # Arrange
        dummy_task_id = "invalid_task_id"
        endpoint = f"{API_PROJECT_PATTERN}/model_groups?task_id={dummy_task_id}"

        # Act
        with patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project):
            response = fxt_resource_rest.get(endpoint)

        # Assert
        assert response.status_code == InvalidIDException.http_status

    def test_model_detail_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = API_MODEL_PATTERN
        dummy_model_detail_rest = {"dummy_model": "value"}

        # Act
        with patch.object(
            ModelRESTController,
            "get_model_detail",
            return_value=dummy_model_detail_rest,
        ) as mock_get_model_detail:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_model_detail.assert_called_once_with(
            project_id=DUMMY_PROJECT_ID,
            model_storage_id=ID(DUMMY_MODEL_GROUP_ID),
            model_id=ID(DUMMY_MODEL_ID),
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), dummy_model_detail_rest, ignore_eq=True)

    def test_model_detail_endpoint_mock(self, fxt_resource_rest, fxt_project) -> None:
        # Arrange
        endpoint = f"{API_PROJECT_PATTERN}/model_groups/{MOCK_MODEL_GROUP_ID}/models/{MOCK_MODEL_ID}"

        # Act
        with patch.object(
            ModelRESTController, "get_model_detail", return_value=MOCK_MODEL_DETAIL
        ) as mock_model_controller:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_model_controller.assert_called_once_with(
            project_id=DUMMY_PROJECT_ID,
            model_storage_id=MOCK_MODEL_GROUP_ID,
            model_id=MOCK_MODEL_ID,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), MOCK_MODEL_DETAIL, ignore_eq=True)

    def test_model_storage_activation_endpoint(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_MODEL_GROUP_PATTERN}:activate?include_lifecycle_stage=true"
        dummy_activation_rest = {"active_model_storage": "dummy_storage"}

        # Act
        with patch.object(
            ModelRESTController,
            "activate_model_storage",
            return_value=dummy_activation_rest,
        ) as mock_activate_model_storage:
            result = fxt_resource_rest.post(endpoint, json={})

        # Assert
        mock_activate_model_storage.assert_called_once_with(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
            model_storage_id=ID(DUMMY_MODEL_GROUP_ID),
            include_lifecycle_stage=True,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), dummy_activation_rest, ignore_eq=True)
