# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
import os
from unittest.mock import patch

import pytest

from communication.controllers import ExportController
from communication.job_creation_helpers import JobDuplicatePolicy
from repos import ZipStorageRepo

from grpc_interfaces.job_submission.client import GRPCJobsClient
from iai_core_py.entities.project import NullProject
from iai_core_py.repos import ProjectRepo


def do_nothing(*args, **kwargs):
    pass


@pytest.mark.ProjectIEMsComponent
class TestExportController:
    def test_submit_project_export_job(self, fxt_ote_id, fxt_project) -> None:
        submitted_job_id = fxt_ote_id(100)
        author_id = fxt_ote_id(101)
        payload = {"project_id": str(fxt_project.id_)}
        metadata = {
            "project": {
                "id": str(fxt_project.id_),
                "name": str(fxt_project.name),
            }
        }
        with (
            patch.object(GRPCJobsClient, "submit", return_value=submitted_job_id) as mock_grpc_client_submit,
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project),
        ):
            job_id = ExportController.submit_project_export_job(
                project_identifier=fxt_project.identifier, author_id=author_id
            )

        mock_grpc_client_submit.assert_called_once_with(
            priority=1,
            job_name="Project Export",
            job_type="export_project",
            key=json.dumps(dict(payload, type="export_project")),
            payload=payload,
            metadata=metadata,
            duplicate_policy=JobDuplicatePolicy.REPLACE.name.lower(),
            author=author_id,
            project_id=fxt_project.id_,
            cancellable=True,
        )
        assert job_id == submitted_job_id

    def test_get_exported_archive_presigned_url(self, fxt_project_identifier, fxt_ote_id) -> None:
        s3_host = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
        internal_url = f"http://{s3_host}/exported_projects/123/project.zip"
        domain_name = "app.geti.intel.com"
        operation_id = fxt_ote_id(123)
        with patch.object(ExportController, "_get_zip_presigned_url", return_value=internal_url) as mock_get_url:
            response = ExportController.get_exported_archive_presigned_url(
                project_identifier=fxt_project_identifier, export_operation_id=operation_id, domain_name=domain_name
            )

        mock_get_url.assert_called_once_with(
            project_id=fxt_project_identifier.project_id, export_operation_id=operation_id
        )
        assert (
            response.headers["location"]
            == "https://app.geti.intel.com/api/v1/fileservice/exported_projects/123/project.zip"
        )

    def test_get_zip_presigned_url(self, fxt_project_identifier, fxt_ote_id) -> None:
        operation_id = fxt_ote_id(123)
        dummy_presigned_url = "https://myhost/project.zip"
        with (
            patch.object(ZipStorageRepo, "__init__", new=do_nothing),
            patch.object(
                ZipStorageRepo, "get_downloadable_archive_presigned_url", return_value=dummy_presigned_url
            ) as mock_get_url,
            patch.object(ProjectRepo, "get_by_id", return_value=NullProject()) as mock_get_project,
        ):
            url = ExportController._get_zip_presigned_url(
                project_id=fxt_project_identifier.project_id, export_operation_id=operation_id
            )

        mock_get_project.assert_called_once_with(fxt_project_identifier.project_id)
        mock_get_url.assert_called_once_with(operation_id=operation_id, download_file_name="project.zip")
        assert url == dummy_presigned_url
