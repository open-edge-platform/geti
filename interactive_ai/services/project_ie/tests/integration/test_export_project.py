# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
import os
from unittest.mock import patch

import pytest
from grpc import RpcError

from grpc_interfaces.job_submission.client import GRPCJobsClient
from sc_sdk.repos import ProjectRepo


def do_nothing(self, *args, **kwargs) -> None:
    return None


S3_ENV_VARS = {
    "S3_CREDENTIALS_PROVIDER": "local",
    "S3_ACCESS_KEY": "access_key",
    "S3_SECRET_KEY": "secret_key",
}


@pytest.mark.ProjectIEMsComponent
class TestProjectExport:
    def test_start_export(self, fxt_session_ctx, fxt_test_app, fxt_project, fxt_ote_id) -> None:
        # Arrange
        export_job_id = fxt_ote_id(123)
        endpoint = (
            f"/api/v1/organizations/{str(fxt_session_ctx.organization_id)}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects/{str(fxt_project.id_)}:export"
        )
        with (
            patch.object(GRPCJobsClient, "__init__", new=do_nothing),
            patch.object(GRPCJobsClient, "close") as mock_close_grpc_client,
            patch.object(GRPCJobsClient, "submit", return_value=export_job_id) as mock_submit_job,
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_load_project,
        ):
            # Act
            result = fxt_test_app.post(endpoint)

        # Assert
        expected_job_key = f'{{"project_id": "{str(fxt_project.id_)}", "type": "export_project"}}'
        expected_job_payload = {"project_id": str(fxt_project.id_)}
        expected_job_metadata = {
            "project": {
                "id": str(fxt_project.id_),
                "name": fxt_project.name,
            },
        }
        mock_load_project.assert_called_once_with(fxt_project.id_)
        mock_submit_job.assert_called_once_with(
            priority=1,
            job_name="Project Export",
            job_type="export_project",
            key=expected_job_key,
            payload=expected_job_payload,
            metadata=expected_job_metadata,
            duplicate_policy="replace",
            author="dummy_user",
            project_id=fxt_project.id_,
            cancellable=True,
        )
        mock_close_grpc_client.assert_called_once_with()
        assert result.status_code == 200
        result_rest = json.loads(result.content)
        assert result_rest == {"job_id": str(export_job_id)}

    def test_start_export_nonexisting_project(self, fxt_session_ctx, fxt_test_app, fxt_ote_id) -> None:
        # Arrange
        project_id = fxt_ote_id(456)
        endpoint = (
            f"/api/v1/organizations/{str(fxt_session_ctx.organization_id)}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects/{str(project_id)}:export"
        )

        # Act
        result = fxt_test_app.post(endpoint)

        # Assert
        assert result.status_code == 404

    def test_start_export_unavailable_job_server(self, fxt_session_ctx, fxt_test_app, fxt_project) -> None:
        # Arrange
        endpoint = (
            f"/api/v1/organizations/{str(fxt_session_ctx.organization_id)}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects/{str(fxt_project.id_)}:export"
        )
        with (
            patch.object(GRPCJobsClient, "__init__", new=do_nothing),
            patch.object(GRPCJobsClient, "close"),
            patch.object(GRPCJobsClient, "submit", side_effect=RpcError),  # raise an exception from 'submit'
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_load_project,
        ):
            # Act
            result = fxt_test_app.post(endpoint)

        # Assert
        mock_load_project.assert_called_once_with(fxt_project.id_)
        assert result.status_code == 503

    @patch.dict(os.environ, S3_ENV_VARS)
    def test_download_archive(self, fxt_session_ctx, fxt_test_app, fxt_project, fxt_ote_id) -> None:
        # Arrange
        operation_id = fxt_ote_id(111)
        endpoint = (
            f"/api/v1/organizations/{str(fxt_session_ctx.organization_id)}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects/{str(fxt_project.id_)}"
            f"/exports/{str(operation_id)}/download"
        )

        # Act
        result = fxt_test_app.get(endpoint, follow_redirects=False)

        # Assert
        assert result.status_code == 307
