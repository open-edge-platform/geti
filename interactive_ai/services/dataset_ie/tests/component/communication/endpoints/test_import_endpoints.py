# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements import endpoint tests
"""

import logging
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from communication.helpers.http_exceptions import (
    BadRequestGetiBaseException,
    FileNotFoundGetiBaseException,
    FileNotFullyUploadedGetiBaseException,
    MaxProjectsReachedGetiBaseException,
)
from domain.entities.dataset_ie_file_metadata import ImportMetadata

from geti_types import ID
from iai_core.entities.model_template import TaskType

logger = logging.getLogger(__name__)

_params_metadata_error = [
    (FileNotFoundGetiBaseException(), 404),
    (FileNotFullyUploadedGetiBaseException(), 412),
    (BadRequestGetiBaseException("invalid metadata"), 400),
]


@pytest.mark.DatasetIEMsComponent
class TestImportEndpoints:
    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_prepare_dataset_for_import_endpoint(
        self,
        patched_import_manager,
        fxt_job_id,
        client: TestClient,
        fxt_url_prefix,
        fxt_dataset_id,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.submit_prepare_import_to_new_project_job.return_value = fxt_job_id

        response = self._call_prepare_dataset_for_import(client, fxt_url_prefix, fxt_dataset_id)

        assert response.status_code == 200
        assert response.json()["job_id"] == str(fxt_job_id)

    @pytest.mark.parametrize("side_effect,error_code", _params_metadata_error)
    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_prepare_dataset_for_import_endpoint_file_metadata_error(
        self,
        patched_import_manager,
        side_effect,
        error_code,
        client: TestClient,
        fxt_url_prefix,
        fxt_dataset_id,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.get_validated_file_metadata.side_effect = side_effect

        response = self._call_prepare_dataset_for_import(client, fxt_url_prefix, fxt_dataset_id)

        assert response.status_code == error_code

    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_prepare_dataset_for_import_endpoint_grpc_error(
        self,
        patched_import_manager,
        client: TestClient,
        fxt_url_prefix,
        fxt_dataset_id,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.submit_prepare_import_to_new_project_job.side_effect = ValueError("grpc error")

        response = self._call_prepare_dataset_for_import(client, fxt_url_prefix, fxt_dataset_id)

        assert response.status_code == 500

    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_import_project_from_dataset_endpoint(
        self,
        patched_import_manager,
        fxt_job_id,
        client: TestClient,
        fxt_url_prefix,
        fxt_dataset_id,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.submit_perform_import_to_new_project_job.return_value = fxt_job_id

        response = self._call_import_from_dataset(client, fxt_url_prefix, fxt_dataset_id)

        assert response.status_code == 200
        assert response.json()["job_id"] == str(fxt_job_id)

    @pytest.mark.parametrize("side_effect,error_code", _params_metadata_error)
    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_import_project_from_dataset_endpoint_file_metadata_error(
        self,
        patched_import_manager,
        side_effect,
        error_code,
        client: TestClient,
        fxt_url_prefix,
        fxt_dataset_id,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.get_validated_file_metadata.side_effect = side_effect

        response = self._call_import_from_dataset(client, fxt_url_prefix, fxt_dataset_id)

        assert response.status_code == error_code

    @patch(
        "communication.endpoints.import_endpoints.get_validated_project_type_from_task_type",
        side_effect=BadRequestGetiBaseException("Given task_type is not a supported task type"),
    )
    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_import_project_from_dataset_endpoint_invalid_task_type(
        self,
        patched_import_manager,
        patched_validated_project_type,
        client: TestClient,
        fxt_url_prefix,
        fxt_dataset_id,
    ):
        response = self._call_import_from_dataset(client, fxt_url_prefix, fxt_dataset_id)

        assert response.status_code == 400

    @patch(
        "communication.endpoints.import_endpoints.check_max_number_of_projects",
        side_effect=MaxProjectsReachedGetiBaseException(1000),
    )
    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_import_project_from_dataset_endpoint_max_num_projects(
        self,
        patched_import_manager,
        patched_validated_project_type,
        client: TestClient,
        fxt_url_prefix,
        fxt_dataset_id,
    ):
        response = self._call_import_from_dataset(client, fxt_url_prefix, fxt_dataset_id)

        assert response.status_code == 409

    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_import_project_from_dataset_endpoint_grpc_error(
        self,
        patched_import_manager,
        client: TestClient,
        fxt_url_prefix,
        fxt_dataset_id,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.submit_perform_import_to_new_project_job.side_effect = ValueError("grpc error")

        response = self._call_import_from_dataset(client, fxt_url_prefix, fxt_dataset_id)

        assert response.status_code == 500

    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_prepare_dataset_for_import_to_existing_project_endpoint(
        self,
        patched_import_manager,
        fxt_job_id,
        client: TestClient,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_id,
        fxt_project,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.submit_prepare_import_to_existing_project_job.return_value = fxt_job_id

        with (
            patch(
                "communication.endpoints.import_endpoints.get_validated_project",
                return_value=fxt_project,
            ) as mock_get_validated_project,
            patch(
                "communication.helpers.import_utils.ImportUtils.get_validated_task_type",
                return_value=TaskType.DETECTION,
            ) as mock_get_validated_task_type,
        ):
            response = self._call_prepare_dataset_for_existing_project(
                client, fxt_url_prefix, fxt_project_id, fxt_dataset_id
            )
            mock_get_validated_project.assert_called()
            mock_get_validated_task_type.assert_called()

        assert response.status_code == 200
        assert response.json()["job_id"] == str(fxt_job_id)

    @pytest.mark.parametrize("side_effect,error_code", _params_metadata_error)
    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_prepare_dataset_for_import_to_existing_project_endpoint_file_metadata_error(
        self,
        patched_import_manager,
        side_effect,
        error_code,
        client: TestClient,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_id,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.get_validated_file_metadata.side_effect = side_effect

        response = self._call_prepare_dataset_for_existing_project(
            client, fxt_url_prefix, fxt_project_id, fxt_dataset_id
        )

        assert response.status_code == error_code

    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_prepare_dataset_for_import_to_existing_project_endpoint_no_dataset(
        self,
        patched_import_manager,
        client: TestClient,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_id,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.save_project_id.side_effect = FileNotFoundGetiBaseException()

        response = self._call_prepare_dataset_for_existing_project(
            client, fxt_url_prefix, fxt_project_id, fxt_dataset_id
        )

        assert response.status_code == 404

    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_prepare_dataset_for_import_to_existing_project_endpoint_grpc_error(
        self,
        patched_import_manager,
        client: TestClient,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_id,
        fxt_project,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.submit_prepare_import_to_existing_project_job.side_effect = ValueError("grpc error")

        with (
            patch(
                "communication.endpoints.import_endpoints.get_validated_project",
                return_value=fxt_project,
            ) as mock_get_validated_project,
            patch(
                "communication.helpers.import_utils.ImportUtils.get_validated_task_type",
                return_value=TaskType.DETECTION,
            ) as mock_get_validated_task_type,
        ):
            response = self._call_prepare_dataset_for_existing_project(
                client, fxt_url_prefix, fxt_project_id, fxt_dataset_id
            )
            mock_get_validated_project.assert_called()
            mock_get_validated_task_type.assert_called()

        assert response.status_code == 500

    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_import_dataset_to_project_endpoint(
        self,
        patched_import_manager,
        fxt_job_id,
        client: TestClient,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_id,
        fxt_dataset_storage_id,
        fxt_project,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.get_validated_file_metadata.return_value = ImportMetadata(
            id_=fxt_dataset_id, project_id=fxt_project_id
        )
        import_manager.submit_perform_import_to_existing_project_job.return_value = fxt_job_id

        with (
            patch(
                "communication.endpoints.import_endpoints.get_validated_project",
                return_value=fxt_project,
            ) as mock_get_validated_project,
            patch(
                "communication.helpers.import_utils.ImportUtils.get_validated_task_type",
                return_value=TaskType.DETECTION,
            ) as mock_get_validated_task_type,
        ):
            response = self._call_import_dataset_to_existing_project(
                client,
                fxt_url_prefix,
                fxt_project_id,
                fxt_dataset_id,
                fxt_dataset_storage_id,
            )
            mock_get_validated_project.assert_called()
            mock_get_validated_task_type.assert_called()

        assert response.status_code == 200
        assert response.json()["job_id"] == str(fxt_job_id)

    @pytest.mark.parametrize("side_effect,error_code", _params_metadata_error)
    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_import_dataset_to_project_endpoint_file_metadata_error(
        self,
        patched_import_manager,
        side_effect,
        error_code,
        client: TestClient,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_id,
        fxt_dataset_storage_id,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.get_validated_file_metadata.side_effect = side_effect

        response = self._call_import_dataset_to_existing_project(
            client,
            fxt_url_prefix,
            fxt_project_id,
            fxt_dataset_id,
            fxt_dataset_storage_id,
        )

        assert response.status_code == error_code

    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_import_dataset_to_project_endpoint_invalid_project_id(
        self,
        patched_import_manager,
        client: TestClient,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_id,
        fxt_dataset_storage_id,
        fxt_project,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.get_validated_file_metadata.return_value = ImportMetadata(
            id_=fxt_dataset_id, project_id=ID("invalid_id")
        )

        with (
            patch(
                "communication.endpoints.import_endpoints.get_validated_project",
                return_value=fxt_project,
            ) as mock_get_validated_project,
            patch(
                "communication.helpers.import_utils.ImportUtils.get_validated_task_type",
                return_value=TaskType.DETECTION,
            ) as mock_get_validated_task_type,
        ):
            response = self._call_import_dataset_to_existing_project(
                client,
                fxt_url_prefix,
                fxt_project_id,
                fxt_dataset_id,
                fxt_dataset_storage_id,
            )
            mock_get_validated_project.assert_called()
            mock_get_validated_task_type.assert_called()

        assert response.status_code == 400

    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_import_dataset_to_project_endpoint_invalid_label_id(
        self,
        patched_import_manager,
        client: TestClient,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_id,
        fxt_dataset_storage_id,
        fxt_project,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.validate_project_label_ids.side_effect = BadRequestGetiBaseException("invalid label_id")

        with (
            patch(
                "communication.endpoints.import_endpoints.get_validated_project",
                return_value=fxt_project,
            ) as mock_get_validated_project,
            patch(
                "communication.helpers.import_utils.ImportUtils.get_validated_task_type",
                return_value=TaskType.DETECTION,
            ) as mock_get_validated_task_type,
        ):
            response = self._call_import_dataset_to_existing_project(
                client,
                fxt_url_prefix,
                fxt_project_id,
                fxt_dataset_id,
                fxt_dataset_storage_id,
            )
            mock_get_validated_project.assert_called()
            mock_get_validated_task_type.assert_called()

        assert response.status_code == 400

    @patch("communication.endpoints.import_endpoints.ImportManager")
    def test_import_dataset_to_project_endpoint_grpc_error(
        self,
        patched_import_manager,
        client: TestClient,
        fxt_url_prefix,
        fxt_project_id,
        fxt_dataset_id,
        fxt_dataset_storage_id,
        fxt_project,
    ):
        import_manager = patched_import_manager.return_value
        import_manager.get_validated_file_metadata.return_value = ImportMetadata(
            id_=fxt_dataset_id, project_id=fxt_project_id
        )
        import_manager.submit_perform_import_to_existing_project_job.side_effect = ValueError("grpc error")

        with (
            patch(
                "communication.endpoints.import_endpoints.get_validated_project",
                return_value=fxt_project,
            ) as mock_get_validated_project,
            patch(
                "communication.helpers.import_utils.ImportUtils.get_validated_task_type",
                return_value=TaskType.DETECTION,
            ) as mock_get_validated_task_type,
        ):
            response = self._call_import_dataset_to_existing_project(
                client,
                fxt_url_prefix,
                fxt_project_id,
                fxt_dataset_id,
                fxt_dataset_storage_id,
            )
            mock_get_validated_project.assert_called()
            mock_get_validated_task_type.assert_called()

        assert response.status_code == 500

    @staticmethod
    def _call_prepare_dataset_for_import(client: TestClient, url_prefix: str, file_id: ID):
        return client.post(f"{url_prefix}/datasets:prepare-for-import?file_id={str(file_id)}")

    @staticmethod
    def _call_import_from_dataset(client: TestClient, url_prefix: str, file_id: ID):
        labels = [
            {"name": "car", "color": "#00ff00ff"},
            {"name": "person", "color": "#0000ffff"},
        ]
        return client.post(
            f"{url_prefix}/projects:import-from-dataset",
            json={
                "file_id": str(file_id),
                "project_name": "test_create_project_from_dataset",
                "task_type": "detection",
                "labels": labels,
            },
        )

    @staticmethod
    def _call_prepare_dataset_for_existing_project(client: TestClient, url_prefix: str, project_id: ID, file_id: ID):
        return client.post(
            f"{url_prefix}/projects/{str(project_id)}/datasets:prepare-for-import?file_id={str(file_id)}",
        )

    @staticmethod
    def _call_import_dataset_to_existing_project(
        client: TestClient, url_prefix: str, project_id: ID, file_id: ID, dataset_id: ID
    ):
        return client.post(
            f"{url_prefix}/projects/{str(project_id)}:import-from-dataset",
            json={
                "file_id": str(file_id),
                "labels_map": {"a": "car", "b": "person"},
                "dataset_id": str(dataset_id),
                "dataset_name": "training_dataset",
            },
        )
