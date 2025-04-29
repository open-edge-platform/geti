# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements export endpoint tests
"""

import os
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from communication.endpoints.export_endpoints import get_download_file_name
from communication.helpers.http_exceptions import NotEnoughSpaceGetiBaseException
from domain.entities.dataset_ie_file_metadata import ExportFormat

from geti_types import ID
from sc_sdk.entities.project import Project
from sc_sdk.utils.naming_helpers import slugify

ENV_VARS = {
    "S3_CREDENTIALS_PROVIDER": "local",
    "S3_ACCESS_KEY": "access_key",
    "S3_SECRET_KEY": "secret_key",
}


@pytest.mark.DatasetIEMsComponent
class TestExportEndpoints:
    @patch("communication.endpoints.export_endpoints.ExportManager")
    def test_prepare_dataset_endpoint(
        self,
        patched_export_manager,
        fxt_project: Project,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_job_id,
    ):
        export_manager = patched_export_manager.return_value
        export_manager.submit_export_job.return_value = fxt_job_id

        project_id = fxt_project.id_
        dataset_storage_id = fxt_project.dataset_storage_ids[0]

        response = self._call_prepare_dataset(client, fxt_headers, fxt_url_prefix, project_id, dataset_storage_id)

        assert response.status_code == 200
        assert response.json()["job_id"] == str(fxt_job_id)

    @pytest.mark.parametrize("export_format", ["datumaro", "coco"])
    @pytest.mark.parametrize("save_video_as_images", [True, False])
    @patch("communication.endpoints.export_endpoints.ExportManager")
    def test_prepare_dataset_endpoint_with_save_video_with_images(
        self,
        patched_export_manager,
        save_video_as_images,
        export_format,
        fxt_project: Project,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_job_id,
    ):
        export_manager = patched_export_manager.return_value
        export_manager.submit_export_job.return_value = fxt_job_id

        project_id = fxt_project.id_
        dataset_storage_id = fxt_project.dataset_storage_ids[0]

        response = self._call_prepare_dataset(
            client,
            fxt_headers,
            fxt_url_prefix,
            project_id,
            dataset_storage_id,
            export_format=export_format,
            save_video_as_images=save_video_as_images,
        )

        assert response.status_code == 200
        assert response.json()["job_id"] == str(fxt_job_id)

    def test_prepare_dataset_endpoint_wrong_format(
        self,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_storage_id,
    ):
        response = self._call_prepare_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_project_id, fxt_dataset_storage_id, export_format="unknown"
        )

        assert response.status_code == 400
        assert response.json()["message"].startswith("Export format not supported.")

    @patch(
        "communication.endpoints.export_endpoints.check_free_space_for_operation",
        side_effect=NotEnoughSpaceGetiBaseException("not enough space"),
    )
    def test_prepare_dataset_endpoint_not_enough_space(
        self,
        patched_check_free_space,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_storage_id,
    ):
        response = self._call_prepare_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_project_id, fxt_dataset_storage_id
        )

        assert response.status_code == 507

    def test_prepare_dataset_endpoint_wrong_project(
        self,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_mongo_id,
        fxt_dataset_storage_id,
    ):
        # invalid project_id
        response = self._call_prepare_dataset(
            client, fxt_headers, fxt_url_prefix, ID("invalid_project_id"), fxt_dataset_storage_id
        )

        assert response.status_code == 400
        assert response.json()["message"].startswith("Invalid request parameters: 'project_id'")

        # project_id is in valid format but cannot find the project
        response = self._call_prepare_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_mongo_id(2000), fxt_dataset_storage_id
        )

        assert response.status_code == 404
        assert response.json()["message"].startswith("The requested project could not be found.")

    def test_prepare_dataset_endpoint_wrong_dataset_storage(
        self, client: TestClient, fxt_headers, fxt_url_prefix, fxt_project: Project, fxt_mongo_id
    ):
        # invalid dataset_storage_id
        response = self._call_prepare_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_project.id_, ID("invalid_dataset_storage_id")
        )
        assert response.status_code == 400
        assert response.json()["message"].startswith("Invalid request parameters: 'dataset_storage_id'")

        # dataset_storage_id is int valid format but doesn't exist
        response = self._call_prepare_dataset(client, fxt_headers, fxt_url_prefix, fxt_project.id_, fxt_mongo_id(2000))
        assert response.status_code == 404
        assert response.json()["message"].startswith("The requested dataset could not be found.")

    def test_prepare_dataset_endpoint_wrong_user_id(
        self,
        client: TestClient,
        fxt_url_prefix,
        fxt_project: Project,
        fxt_dataset_storage_id,
    ):
        # remove the overrides including 'get_user_id_fastapi
        client.app.dependency_overrides = {}  # type: ignore[attr-defined]
        response = self._call_prepare_dataset(client, {}, fxt_url_prefix, fxt_project.id_, fxt_dataset_storage_id)

        assert response.status_code == 401

    @patch("communication.endpoints.export_endpoints.ExportManager")
    def test_prepare_dataset_endpoint_grpc_error(
        self,
        patched_export_manager,
        fxt_project: Project,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
    ):
        export_manager = patched_export_manager.return_value
        export_manager.submit_export_job.side_effect = ValueError("grpc error")
        project_id = fxt_project.id_
        dataset_storage_id = fxt_project.dataset_storage_ids[0]

        response = self._call_prepare_dataset(client, fxt_headers, fxt_url_prefix, project_id, dataset_storage_id)

        assert response.status_code == 500

    @patch.dict(os.environ, ENV_VARS)
    def test_download_dataset_endpoint(
        self,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_project,
        fxt_dataset_storage_id,
        fxt_dataset_id,
        fxt_download_path,
    ):
        response = self._call_download_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_project.id_, fxt_dataset_storage_id, fxt_dataset_id
        )

        assert response.status_code == 307  # redirect
        assert response.next_request.url.path == fxt_download_path

    def test_download_dataset_endpoint_wrong_project(
        self,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_dataset_storage_id,
        fxt_dataset_id,
        fxt_mongo_id,
    ):
        response = self._call_download_dataset(
            client, fxt_headers, fxt_url_prefix, ID("invalid_project_id"), fxt_dataset_storage_id, fxt_dataset_id
        )
        assert response.status_code == 400
        assert response.json()["message"].startswith("Invalid request parameters: 'project_id'")

        response = self._call_download_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_mongo_id(2000), fxt_dataset_storage_id, fxt_dataset_id
        )
        assert response.status_code == 404
        assert response.json()["message"].startswith("The requested project could not be found.")

    def test_download_dataset_endpoint_wrong_dataset_storage(
        self,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_project: Project,
        fxt_dataset_id,
        fxt_mongo_id,
    ):
        response = self._call_download_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_project.id_, ID("invalid_dataset_storage_id"), fxt_dataset_id
        )
        assert response.status_code == 400
        assert response.json()["message"].startswith("Invalid request parameters: 'dataset_storage_id'")

        response = self._call_download_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_project.id_, fxt_mongo_id(2000), fxt_dataset_id
        )
        assert response.status_code == 404
        assert response.json()["message"].startswith("The requested dataset could not be found.")

    @patch("communication.endpoints.export_endpoints.ExportManager")
    def test_download_dataset_endpoint_wrong_export_dataset_id(
        self,
        patched_export_manager,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_project: Project,
        fxt_dataset_storage_id,
        fxt_mongo_id,
    ):
        export_manager = patched_export_manager.return_value
        export_manager.get_exported_dataset_presigned_url.side_effect = FileNotFoundError

        response = self._call_download_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_project.id_, fxt_dataset_storage_id, ID("invalid_dataset_id")
        )
        assert response.status_code == 400
        assert response.json()["message"].startswith("Invalid request parameters: 'export_dataset_id'")

        with patch(
            "communication.endpoints.export_endpoints.get_validated_project", return_value=fxt_project
        ) as mock_get_validated_project:
            response = self._call_download_dataset(
                client, fxt_headers, fxt_url_prefix, fxt_project.id_, fxt_dataset_storage_id, fxt_mongo_id(2000)
            )
            mock_get_validated_project.assert_called()

        assert response.status_code == 404
        assert response.json()["message"].startswith("The requested export dataset could not be found.")

    @patch("communication.endpoints.export_endpoints.ExportManager")
    def test_download_dataset_endpoint_other_exception(
        self,
        patched_export_manager,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_project,
        fxt_dataset_storage_id,
        fxt_dataset_id,
    ):
        export_manager = patched_export_manager.return_value
        export_manager.get_exported_dataset_presigned_url.return_value = None

        response = self._call_download_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_project.id_, fxt_dataset_storage_id, fxt_dataset_id
        )

        assert response.status_code == 500

        export_manager.get_exported_dataset_presigned_url.side_effect = ValueError
        response = self._call_download_dataset(
            client, fxt_headers, fxt_url_prefix, fxt_project.id_, fxt_dataset_storage_id, fxt_dataset_id
        )
        assert response.status_code == 500

    @patch("communication.endpoints.export_endpoints.ExportManager")
    def test_download_dataset_endpoint_none_url(
        self,
        patched_export_manager,
        client: TestClient,
        fxt_headers,
        fxt_url_prefix,
        fxt_project_id,
        fxt_project,
        fxt_dataset_storage_id,
        fxt_dataset_id,
    ):
        export_manager = patched_export_manager.return_value
        export_manager.get_exported_dataset_presigned_url.return_value = None

        with patch(
            "communication.endpoints.export_endpoints.get_validated_project", return_value=fxt_project
        ) as mock_get_validated_project:
            response = self._call_download_dataset(
                client, fxt_headers, fxt_url_prefix, fxt_project_id, fxt_dataset_storage_id, fxt_dataset_id
            )
            mock_get_validated_project.assert_called()
        assert response.status_code == 500

    @pytest.mark.parametrize(
        "export_format,expected_filename",
        [
            (ExportFormat.DATUMARO, "dataset-DATUMARO.zip"),
            (None, "dataset.zip"),
        ],
    )
    def test_get_download_file_name(
        self,
        fxt_workspace_id,
        fxt_dataset_storage_id,
        fxt_project: Project,
        export_format,
        expected_filename,
    ):
        project_name = f'"{fxt_project.name}"'

        filename = get_download_file_name(fxt_dataset_storage_id, export_format)
        assert filename == f"{slugify(project_name)}-{expected_filename}"

    @staticmethod
    def _call_prepare_dataset(
        client: TestClient,
        headers: dict,
        url_prefix: str,
        project_id: ID,
        dataset_storage_id: ID,
        export_format: str = "datumaro",
        save_video_as_images: bool = True,
    ):
        return client.post(
            f"{url_prefix}/projects/{str(project_id)}/datasets/{str(dataset_storage_id)}:prepare-for-export"
            f"?export_format={export_format}&save_video_as_images={save_video_as_images}",
            headers=headers,
        )

    @staticmethod
    def _call_download_dataset(
        client: TestClient, headers: dict, url_prefix: str, project_id: ID, dataset_storage_id: ID, file_id: ID
    ):
        return client.get(
            f"{url_prefix}/projects/{str(project_id)}/datasets/{str(dataset_storage_id)}/exports/{str(file_id)}/download",
            headers=headers,
            follow_redirects=False,
        )
