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
from unittest.mock import patch

import pytest
from grpc import RpcError

from geti_types import ID
from grpc_interfaces.job_submission.client import GRPCJobsClient


def do_nothing(self, *args, **kwargs) -> None:
    return None


S3_ENV_VARS = {
    "S3_CREDENTIALS_PROVIDER": "local",
    "S3_ACCESS_KEY": "access_key",
    "S3_SECRET_KEY": "secret_key",
}


@pytest.mark.ProjectIEMsComponent
class TestProjectImport:
    def test_start_import(self, fxt_session_ctx, fxt_test_app, fxt_ote_id) -> None:
        # Arrange
        upload_file_id = fxt_ote_id(101)
        import_job_id = fxt_ote_id(102)
        endpoint = (
            f"/api/v1/organizations/{str(fxt_session_ctx.organization_id)}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects:import"
        )
        request_body: dict = {"file_id": str(upload_file_id), "project_name": "my-project"}
        with (
            patch.object(GRPCJobsClient, "__init__", new=do_nothing),
            patch.object(GRPCJobsClient, "close") as mock_close_grpc_client,
            patch.object(GRPCJobsClient, "submit", return_value=import_job_id) as mock_submit_job,
        ):
            # Act
            result = fxt_test_app.post(endpoint, json=request_body)

        # Assert
        expected_job_key = (
            f'{{"file_id": "{str(upload_file_id)}", "project_name": "my-project", "type": "import_project"}}'
        )

        expected_job_payload = {
            "file_id": str(upload_file_id),
            "keep_original_dates": False,
            "project_name": "my-project",
            "user_id": "dummy_user",
        }
        expected_job_metadata = {
            "parameters": {"file_id": str(upload_file_id)},
            "project": {"name": "my-project"},
        }
        mock_submit_job.assert_called_once_with(
            priority=1,
            job_name="Project Import",
            job_type="import_project",
            key=expected_job_key,
            payload=expected_job_payload,
            metadata=expected_job_metadata,
            duplicate_policy="replace",
            author=ID("dummy_user"),
            cancellable=False,
        )
        mock_close_grpc_client.assert_called_once_with()
        assert result.status_code == 200
        result_rest = json.loads(result.content)
        assert result_rest == {"job_id": str(import_job_id)}

    def test_start_import_unavailable_job_server(self, fxt_session_ctx, fxt_test_app, fxt_ote_id) -> None:
        # Arrange
        upload_file_id = fxt_ote_id(101)
        fxt_ote_id(102)
        endpoint = (
            f"/api/v1/organizations/{str(fxt_session_ctx.organization_id)}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects:import"
        )
        request_body: dict = {"file_id": str(upload_file_id), "project_name": "my-project"}
        with (
            patch.object(GRPCJobsClient, "__init__", new=do_nothing),
            patch.object(GRPCJobsClient, "close"),
            patch.object(GRPCJobsClient, "submit", side_effect=RpcError),  # raise an exception from 'submit'
        ):
            # Act
            result = fxt_test_app.post(endpoint, json=request_body)

        # Assert
        assert result.status_code == 503
