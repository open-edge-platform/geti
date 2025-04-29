# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from http import HTTPStatus
from unittest.mock import patch

import pytest
from starlette.responses import RedirectResponse

from communication.controllers import ExportController

from geti_types import ID


@pytest.mark.ProjectIEMsComponent
class TestProjectExportEndpoints:
    def test_start_project_export(self, fxt_test_app, fxt_session_ctx, fxt_project_identifier, fxt_ote_id) -> None:
        # Arrange
        endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}/workspaces/{fxt_session_ctx.workspace_id}"
            f"/projects/{fxt_project_identifier.project_id}:export"
        )
        submitted_job_id = fxt_ote_id(100)

        # Act
        with patch.object(
            ExportController, "submit_project_export_job", return_value=submitted_job_id
        ) as mock_submit_export_job:
            result = fxt_test_app.post(endpoint)

        # Assert
        assert result.status_code == HTTPStatus.OK
        mock_submit_export_job.assert_called_once_with(
            project_identifier=fxt_project_identifier, author_id=ID("dummy_user")
        )
        assert result.json() == {"job_id": str(submitted_job_id)}

    def test_download_exported_project(self, fxt_test_app, fxt_session_ctx, fxt_project_identifier, fxt_ote_id) -> None:
        # Arrange
        export_operation_id = fxt_ote_id(123)
        endpoint_base = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}/workspaces/{fxt_session_ctx.workspace_id}"
            f"/projects/{fxt_project_identifier.project_id}/exports/{export_operation_id}"
        )
        endpoint = endpoint_base + "/download"
        expected_redirect = endpoint_base + "/some_url"
        redirect_response = RedirectResponse(url="some_url")

        # Act
        with patch.object(
            ExportController, "get_exported_archive_presigned_url", return_value=redirect_response
        ) as mock_get_presigned_url:
            result = fxt_test_app.get(endpoint)

        # Assert
        mock_get_presigned_url.assert_called_once_with(
            project_identifier=fxt_project_identifier, export_operation_id=export_operation_id, domain_name="testserver"
        )
        assert result.url == "http://testserver" + expected_redirect
