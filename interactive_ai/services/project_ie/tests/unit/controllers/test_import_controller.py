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

from communication.controllers import ImportController
from communication.job_creation_helpers import JobDuplicatePolicy
from communication.models import ImportOperation

from geti_types import CTX_SESSION_VAR
from grpc_interfaces.job_submission.client import GRPCJobsClient


@pytest.mark.ProjectIEMsComponent
class TestImportController:
    def test_submit_project_import_job(self, fxt_ote_id, fxt_session_ctx) -> None:
        import_operation = ImportOperation(
            file_id="dummy_file_id",
            project_name="dummy_project",
        )
        user_id = fxt_ote_id(456)
        submitted_job_id = fxt_ote_id(1000)
        payload = {
            "file_id": import_operation.file_id,
            "keep_original_dates": False,
            "project_name": import_operation.project_name,
            "user_id": str(user_id),
        }
        metadata = {
            "parameters": {
                "file_id": import_operation.file_id,
            },
            "project": {
                "name": import_operation.project_name,
            },
        }
        CTX_SESSION_VAR.get()

        with (
            patch(
                "communication.controllers.import_controller.check_max_number_of_projects"
            ) as mock_check_project_limit,
            patch.object(GRPCJobsClient, "submit", return_value=submitted_job_id) as mock_grpc_client_submit,
        ):
            job_id = ImportController.submit_project_import_job(import_operation=import_operation, author_id=user_id)

        mock_check_project_limit.assert_called()
        mock_grpc_client_submit.assert_called_once_with(
            priority=1,
            job_name="Project Import",
            job_type="import_project",
            key=json.dumps(
                {
                    "file_id": import_operation.file_id,
                    "project_name": import_operation.project_name,
                    "type": "import_project",
                }
            ),
            payload=payload,
            metadata=metadata,
            duplicate_policy=JobDuplicatePolicy.REPLACE.name.lower(),
            author=user_id,
            cancellable=False,
        )
        assert job_id == submitted_job_id
