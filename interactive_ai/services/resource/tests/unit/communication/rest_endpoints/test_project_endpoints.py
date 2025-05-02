# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import io
import json
from http import HTTPStatus
from unittest.mock import ANY, patch

import cv2
import numpy as np
import pytest
from testfixtures import compare

from communication.exceptions import NoMediaInProjectException
from communication.rest_controllers import MediaRESTController, ProjectRESTController
from communication.rest_utils import project_query_data
from features.feature_flags import FeatureFlag
from managers.project_manager import ProjectManager

from geti_types import ID, DatasetStorageIdentifier
from iai_core_py.entities.project import Project
from iai_core_py.repos.annotation_template_repo import AnnotationTemplateRepo
from iai_core_py.repos.project_repo_helpers import ProjectSortBy, SortDirection

DUMMY_DATA = {"dummy_key": "dummy_value"}
DUMMY_ORGANIZATION_ID = "6682a33b-3d18-4dab-abee-f797090480e0"
DUMMY_DATASET_ID = "012345678901234567890000"
DUMMY_IMAGE_ID = "123456789012345678900000"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_TASK_ID = "345678901234567890120000"
DUMMY_VIDEO_ID = "456789012345678901230000"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_REST_MEDIA = {"media": "dummy_rest_media"}
DUMMY_PROJECT_QUERY_DATA = "project_query_data"

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_PROJECT_PATTERN = f"{API_WORKSPACE_PATTERN}/projects/{DUMMY_PROJECT_ID}"
API_DATASET_PATTERN = f"{API_PROJECT_PATTERN}/datasets/{DUMMY_DATASET_ID}"

ERROR_CODE = "user_error"
ERROR_MESSAGE = "User is not authorized"

HEADERS = {"Content-Type": "application/json"}


class TestProjectRESTEndpoint:
    def test_projects_names_endpoint_get(self, request, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_WORKSPACE_PATTERN}/projects_names"

        # Act
        with patch.object(
            ProjectRESTController,
            "get_projects_names",
            return_value=DUMMY_DATA,
        ) as mock_get_projects_names:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_projects_names.assert_called_once_with(user_id=ANY)
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_projects_endpoint_get(self, request, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_WORKSPACE_PATTERN}/projects"

        # Act
        with patch.object(
            ProjectRESTController,
            "get_projects",
            return_value=DUMMY_DATA,
        ) as mock_get_projects:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_projects.assert_called_once_with(
            organization_id=DUMMY_ORGANIZATION_ID,
            user_id=ANY,
            query_data=project_query_data(),
            url=ANY,
            include_hidden=False,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_projects_endpoint_get_with_query_data(self, request, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_WORKSPACE_PATTERN}/projects?skip=3&limit=5&sort_by=name&sort_direction=asc"

        # Act
        with patch.object(
            ProjectRESTController,
            "get_projects",
            return_value=DUMMY_DATA,
        ) as mock_get_projects:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_projects.assert_called_once_with(
            organization_id=DUMMY_ORGANIZATION_ID,
            user_id=ANY,
            query_data=project_query_data(
                skip=3,
                limit=5,
                sort_by=ProjectSortBy.NAME,
                sort_direction=SortDirection.ASC,
            ),
            url=ANY,
            include_hidden=False,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    @pytest.mark.parametrize(
        "query",
        [
            "?skip=not_an_integer",
            "?limit=not_an_integer",
            "?sort_by=random",
            "?sort_direction=wrong_direction",
        ],
    )
    def test_projects_endpoint_get_error_handling(self, fxt_resource_rest, query) -> None:
        # Arrange
        endpoint = f"{API_WORKSPACE_PATTERN}/projects{query}"

        # Act
        response = fxt_resource_rest.get(endpoint)

        # Assert
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_projects_endpoint_post(self, fxt_resource_rest, fxt_organization_id) -> None:
        # Arrange
        endpoint = f"{API_WORKSPACE_PATTERN}/projects"

        # Act
        with patch.object(
            ProjectRESTController,
            "create_project",
            return_value=DUMMY_DATA,
        ) as mock_create_project:
            result = fxt_resource_rest.post(endpoint, data=json.dumps(DUMMY_DATA), headers=HEADERS)

        # Assert
        mock_create_project.assert_called_once_with(
            organization_id=DUMMY_ORGANIZATION_ID,
            data=DUMMY_DATA,
            creator_id=ANY,
            workspace_id=ID(DUMMY_WORKSPACE_ID),
        )
        assert result.status_code == HTTPStatus.CREATED
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_projects_endpoint_post_error_handling(self, fxt_resource_rest) -> None:
        # Arrange
        endpoint = f"{API_WORKSPACE_PATTERN}/projects"
        data: dict = {}  # invalid data

        # Act
        result = fxt_resource_rest.post(endpoint, json=data, headers=HEADERS)

        # Assert
        assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_project_endpoint_get(self, fxt_resource_rest, fxt_organization_id) -> None:
        # Arrange
        endpoint = f"{API_PROJECT_PATTERN}"

        # Act
        with patch.object(
            ProjectRESTController,
            "get_project",
            return_value=DUMMY_DATA,
        ) as mock_get_project:
            result = fxt_resource_rest.get(endpoint)

        # Assert
        mock_get_project.assert_called_once_with(
            organization_id=DUMMY_ORGANIZATION_ID,
            project_id=ID(DUMMY_PROJECT_ID),
            include_deleted_labels=False,
            with_size=False,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_project_endpoint_delete(self, fxt_resource_rest, fxt_organization_id) -> None:
        # Arrange
        endpoint = f"{API_PROJECT_PATTERN}"

        # Act
        with patch.object(
            ProjectRESTController,
            "delete_project",
            return_value=DUMMY_DATA,
        ) as mock_delete_project:
            result = fxt_resource_rest.delete(endpoint)

        # Assert
        mock_delete_project.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_project_endpoint_put(self, fxt_resource_rest, fxt_organization_id) -> None:
        # Arrange
        endpoint = f"{API_PROJECT_PATTERN}"

        # Act
        with patch.object(
            ProjectRESTController,
            "update_project",
            return_value=DUMMY_DATA,
        ) as mock_update_project:
            result = fxt_resource_rest.put(endpoint, data=json.dumps(DUMMY_DATA), headers=HEADERS)

        # Assert
        mock_update_project.assert_called_once_with(
            organization_id=DUMMY_ORGANIZATION_ID,
            project_id=ID(DUMMY_PROJECT_ID),
            data=DUMMY_DATA,
        )
        assert result.status_code == HTTPStatus.OK
        compare(result.json(), DUMMY_DATA, ignore_eq=True)

    def test_project_thumbnail_endpoint_image(
        self,
        fxt_resource_rest,
        request,
        fxt_project,
        fxt_dataset_storage,
        fxt_image_entity,
    ) -> None:
        # Arrange
        endpoint = f"{API_PROJECT_PATTERN}/thumbnail"
        img = np.zeros([10, 10, 3], dtype=np.uint8)
        _, np_img_bytes = cv2.imencode(".jpg", img)
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=ID(DUMMY_WORKSPACE_ID),
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=fxt_dataset_storage.id_,
        )

        # Act
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project),
            patch.object(Project, "get_training_dataset_storage", return_value=fxt_dataset_storage),
            patch.object(
                MediaRESTController,
                "get_project_thumbnail",
                return_value=io.BytesIO(bytes(np_img_bytes)),
            ) as mock_get_thumbnail,
        ):
            result = fxt_resource_rest.get(endpoint)

        mock_get_thumbnail.assert_called_once_with(
            dataset_storage_identifier=dataset_storage_identifier,
        )
        assert result.status_code == HTTPStatus.OK

    def test_project_thumbnail_endpoint_null(self, fxt_resource_rest, fxt_dataset_storage, fxt_project) -> None:
        # Arrange
        endpoint = f"{API_PROJECT_PATTERN}/thumbnail"

        # Act
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project),
            patch.object(Project, "get_training_dataset_storage", return_value=fxt_dataset_storage),
        ):
            response = fxt_resource_rest.get(endpoint)
        assert response.status_code == NoMediaInProjectException.http_status

    def test_post_annotation_template(self, fxt_resource_rest, fxt_enable_feature_flag_name) -> None:
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION.name)
        endpoint = f"{API_PROJECT_PATTERN}/settings/annotation_templates"

        data = {
            "name": "test_name",
            "value": "test_value",
        }

        with (
            patch.object(AnnotationTemplateRepo, "save") as mock_save_annotation_template,
            patch.object(AnnotationTemplateRepo, "generate_id", return_value=ID("test_id")),
        ):
            result = fxt_resource_rest.post(endpoint, json=data, headers=HEADERS)

        mock_save_annotation_template.assert_called_once()
        assert result.status_code == HTTPStatus.OK
        assert result.json() == {
            "id": "test_id",
            "name": "test_name",
            "value": "test_value",
        }

    def test_get_annotation_templates(
        self,
        fxt_resource_rest,
        fxt_annotation_template_1,
        fxt_annotation_template_2,
        fxt_annotation_template_1_mapped,
        fxt_annotation_template_2_mapped,
        fxt_enable_feature_flag_name,
    ) -> None:
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION.name)
        endpoint = f"{API_PROJECT_PATTERN}/settings/annotation_templates"

        with (
            patch.object(
                AnnotationTemplateRepo,
                "get_all",
                return_value=[fxt_annotation_template_1, fxt_annotation_template_2],
            ) as mock_get_annotation_template,
        ):
            result = fxt_resource_rest.get(endpoint, headers=HEADERS)

        mock_get_annotation_template.assert_called_once()
        assert result.status_code == HTTPStatus.OK
        assert result.json() == {
            "annotation_templates": [fxt_annotation_template_1_mapped, fxt_annotation_template_2_mapped]
        }
