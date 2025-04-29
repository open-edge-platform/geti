# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
import re
from unittest.mock import patch

import pytest

from application.export_management import DatasetExportOperationConfig
from communication.helpers.job_helper import JobType
from domain.entities.dataset_ie_file_metadata import ExportFormat

from grpc_interfaces.job_submission.client import GRPCJobsClient

ENV_VARS = {
    "S3_CREDENTIALS_PROVIDER": "local",
    "S3_ACCESS_KEY": "access_key",
    "S3_SECRET_KEY": "secret_key",
}


@pytest.mark.DatasetIEMsComponent
class TestExportManager:
    def test_submit_export_job(
        self,
        fxt_export_manager,
        fxt_project,
        fxt_dataset_storage,
        fxt_user_id,
        fxt_organization_id,
    ):
        export_format_str = "datumaro"
        job_metadata = {
            "project": {"id": str(fxt_project.id_), "name": fxt_project.name, "type": "detection"},
            "dataset": {
                "id": str(fxt_dataset_storage.id_),
                "name": fxt_dataset_storage.name,
            },
            "export_format": export_format_str,
        }

        with patch.object(GRPCJobsClient, "submit", return_value=None) as mock_submit:
            fxt_export_manager.submit_export_job(
                project_id=fxt_project.id_,
                dataset_storage_id=fxt_dataset_storage.id_,
                export_config=DatasetExportOperationConfig(
                    export_format=ExportFormat.DATUMARO, include_unannotated=True, save_video_as_images=True
                ),
                author=fxt_user_id,
                metadata=job_metadata,
            )

        export_job_type = JobType.EXPORT_DATASET.value
        job_payload = {
            "organization_id": str(fxt_organization_id),
            "project_id": str(fxt_project.id_),
            "dataset_storage_id": str(fxt_dataset_storage.id_),
            "include_unannotated": True,
            "export_format": export_format_str,
            "save_video_as_images": True,
        }
        serialized_key = (
            f'{{"dataset_storage_id": "{fxt_dataset_storage.id_}", "export_format": "{export_format_str}", '
            f'"include_unannotated": true, "save_video_as_images": true, "type": "{export_job_type}"}}'
        )
        mock_submit.assert_called_once_with(
            priority=1,
            job_name="Dataset Export",
            job_type=export_job_type,
            key=serialized_key,
            payload=job_payload,
            metadata=job_metadata,
            duplicate_policy="replace",
            author=fxt_user_id,
            project_id=fxt_project.id_,
            cancellable=True,
        )

    @patch.dict(os.environ, ENV_VARS)
    def test_get_exported_dataset_presigned_url(
        self,
        fxt_export_manager,
        fxt_dataset_id,
        fxt_organization_id,
        fxt_workspace_id,
    ):
        filename = "dataset-DATUMARO.zip"
        url = fxt_export_manager.get_exported_dataset_presigned_url(fxt_dataset_id, filename)

        s3_internal_address = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
        pattern = (
            "https?://(.+:\d+)/.*organizations/(.{24})/workspaces/(.{24})/exports/(.{24})/dataset.zip\?"
            "response-content-disposition=attachment%3B%20filename%3D%22(.*)%22"
        )

        m = re.search(pattern, url)
        assert m.group(1) == s3_internal_address
        assert m.group(2) == str(fxt_organization_id)
        assert m.group(3) == str(fxt_workspace_id)
        assert m.group(4) == str(fxt_dataset_id)
        assert m.group(5) == filename
