# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from http import HTTPStatus
from unittest.mock import patch

import pytest

from communication.controllers import ImportController
from communication.models import ImportOperation

from geti_types import ID


@pytest.mark.ProjectIEMsComponent
class TestProjectImportEndpoints:
    def test_start_project_import(self, fxt_test_app, fxt_session_ctx, fxt_ote_id) -> None:
        # Arrange
        file_id = "dummy_file_id"
        endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}/workspaces/{fxt_session_ctx.workspace_id}"
            f"/projects:import"
        )
        submitted_job_id = fxt_ote_id(1000)
        import_operation = ImportOperation(
            file_id=file_id,
            project_name="dummy_project",
        )
        payload = {
            "file_id": import_operation.file_id,
            "keep_original_dates": False,
            "project_name": import_operation.project_name,
        }

        # Act
        with patch.object(
            ImportController, "submit_project_import_job", return_value=submitted_job_id
        ) as mock_submit_import:
            result = fxt_test_app.post(endpoint, json=payload)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_submit_import.assert_called_once_with(import_operation=import_operation, author_id=ID("dummy_user"))
        assert result.json() == {"job_id": str(submitted_job_id)}

    def test_start_project_import_missing_field(self, fxt_test_app, fxt_session_ctx) -> None:
        # Arrange
        endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}/workspaces/{fxt_session_ctx.workspace_id}"
            f"/projects:import"
        )
        # missing required field "file_id"
        payload = {
            "project_name": "project_name",
        }

        # Act
        result = fxt_test_app.post(endpoint, json=payload)

        # Assert
        assert result.status_code == HTTPStatus.BAD_REQUEST
