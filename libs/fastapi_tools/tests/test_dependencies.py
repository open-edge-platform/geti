import datetime

import pytest
from bson import ObjectId
from geti_types.id import ID, ProjectIdentifier

from geti_fastapi_tools.dependencies import (
    get_annotation_id,
    get_dataset_id,
    get_dataset_revision_id,
    get_deployment_id,
    get_image_id,
    get_model_group_id,
    get_model_id,
    get_optimized_model_id,
    get_optional_project_id,
    get_optional_task_id,
    get_organization_id,
    get_project_id,
    get_project_identifier,
    get_skiptoken,
    get_test_id,
    get_video_id,
    get_workspace_id,
)
from geti_fastapi_tools.exceptions import InvalidIDException

VALID_OBJECTID = "012345678901234567891234"
VALID_UUID = "ee703794-4e9a-442d-a944-ff5ca48cd8a6"
EXPECTED_OBJECTID = ID(VALID_OBJECTID)
EXPECTED_UUID = ID(VALID_UUID)
INVALID_ID = "AAAA"


class TestDependencies:
    def test_get_project_identifier(self) -> None:
        with pytest.raises(InvalidIDException):
            get_project_identifier(workspace_id=INVALID_ID, project_id=INVALID_ID)

        assert get_project_identifier(workspace_id=VALID_OBJECTID, project_id=VALID_OBJECTID) == ProjectIdentifier(
            workspace_id=EXPECTED_OBJECTID, project_id=EXPECTED_OBJECTID
        )

    def test_get_organization_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_organization_id(organization_id=INVALID_ID)

        assert get_organization_id(organization_id=VALID_UUID) == EXPECTED_UUID

    def test_get_workspace_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_workspace_id(workspace_id=INVALID_ID)

        assert get_workspace_id(workspace_id=VALID_OBJECTID) == EXPECTED_OBJECTID
        assert get_workspace_id(workspace_id=VALID_UUID) == EXPECTED_UUID

    def test_get_project_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_project_id(project_id=INVALID_ID)

        assert get_project_id(project_id=VALID_OBJECTID) == EXPECTED_OBJECTID

    def test_get_dataset_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_dataset_id(dataset_id=INVALID_ID)

        assert get_dataset_id(dataset_id=VALID_OBJECTID) == EXPECTED_OBJECTID

    def test_get_image_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_image_id(image_id=INVALID_ID)

        assert get_image_id(image_id=VALID_OBJECTID) == EXPECTED_OBJECTID

    def test_get_video_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_video_id(video_id=INVALID_ID)

        assert get_video_id(video_id=VALID_OBJECTID) == EXPECTED_OBJECTID

    def test_get_annotation_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_annotation_id(annotation_id=INVALID_ID)

        assert get_annotation_id(annotation_id=VALID_OBJECTID) == EXPECTED_OBJECTID
        assert get_annotation_id(annotation_id="latest") == ID("latest")

    def test_get_deployment_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_deployment_id(deployment_id=INVALID_ID)

        assert get_deployment_id(deployment_id=VALID_OBJECTID) == EXPECTED_OBJECTID

    def test_get_dataset_revision_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_dataset_revision_id(dataset_revision_id=INVALID_ID)

        assert get_dataset_revision_id(dataset_revision_id=VALID_OBJECTID) == EXPECTED_OBJECTID

    def test_get_test_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_test_id(test_id=INVALID_ID)

        assert get_test_id(test_id=VALID_OBJECTID) == EXPECTED_OBJECTID

    def test_get_model_group_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_model_group_id(model_group_id=INVALID_ID)

        assert get_model_group_id(model_group_id=VALID_OBJECTID) == EXPECTED_OBJECTID

    def test_get_model_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_model_id(model_id=INVALID_ID)

        assert get_model_id(model_id=VALID_OBJECTID) == EXPECTED_OBJECTID

    def test_get_optimized_model_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_optimized_model_id(optimized_model_id=INVALID_ID)

        assert get_optimized_model_id(optimized_model_id=VALID_OBJECTID) == EXPECTED_OBJECTID

    def test_get_optional_task_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_optional_task_id(task_id=INVALID_ID)

        assert get_optional_task_id(task_id=VALID_OBJECTID) == EXPECTED_OBJECTID
        assert get_optional_task_id() is None

    def test_get_optional_project_id(self) -> None:
        with pytest.raises(InvalidIDException):
            get_optional_project_id(project_id=INVALID_ID)

        assert get_optional_project_id(project_id=VALID_OBJECTID) == EXPECTED_OBJECTID
        assert get_optional_project_id() is None

    def test_get_skiptoken(self) -> None:
        with pytest.raises(InvalidIDException):
            get_skiptoken(skiptoken=INVALID_ID)

        assert get_skiptoken(skiptoken=VALID_OBJECTID) == EXPECTED_OBJECTID
        assert get_skiptoken() == ID(ObjectId.from_datetime(datetime.datetime(1970, 1, 1)))
