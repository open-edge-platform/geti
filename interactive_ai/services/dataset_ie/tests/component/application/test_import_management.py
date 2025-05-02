# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from _pytest.fixtures import FixtureRequest

from communication.helpers.http_exceptions import (
    BadRequestGetiBaseException,
    FileNotFoundGetiBaseException,
    FileNotFullyUploadedGetiBaseException,
)
from communication.helpers.job_helper import JobType
from communication.repos.file_metadata_repo import FileMetadataRepo
from domain.entities.dataset_ie_file_metadata import ExportMetadata, ImportMetadata
from domain.entities.geti_project_type import GetiProjectType

from geti_types import ID
from grpc_interfaces.job_submission.client import GRPCJobsClient
from iai_core_py.entities.label import Domain, Label, NullLabel


@pytest.mark.DatasetIEMsComponent
class TestImportManager:
    def test_submit_prepare_import_to_new_project_job(
        self,
        fxt_import_manager,
        fxt_dataset_id,
        fxt_user_id,
    ):
        metadata = {"file_id": fxt_dataset_id}

        with patch.object(GRPCJobsClient, "submit", return_value=None) as mock_submit:
            fxt_import_manager.submit_prepare_import_to_new_project_job(
                import_id=fxt_dataset_id, author=fxt_user_id, metadata=metadata
            )

        mock_submit.assert_called_once_with(
            priority=1,
            job_name="Prepare Import to New Project",
            job_type=JobType.PREPARE_IMPORT_TO_NEW_PROJECT.value,
            key=f'{{"import_id": "{fxt_dataset_id}", "type": "prepare_import_to_new_project"}}',
            payload={"import_id": fxt_dataset_id},
            metadata=metadata,
            duplicate_policy="replace",
            author=fxt_user_id,
            cancellable=True,
        )

    def test_submit_prepare_import_to_existing_project_job(
        self,
        fxt_import_manager,
        fxt_workspace_id,
        fxt_dataset_id,
        fxt_user_id,
        fxt_project,
    ):
        project_type = "detection"
        metadata = {
            "file_id": str(fxt_dataset_id),
            "project": {"id": str(fxt_project.id_), "name": fxt_project.name, "type": project_type},
        }

        with patch.object(GRPCJobsClient, "submit", return_value=None) as mock_submit:
            fxt_import_manager.submit_prepare_import_to_existing_project_job(
                import_id=fxt_dataset_id,
                author=fxt_user_id,
                project_id=fxt_project.id_,
                metadata=metadata,
            )

        mock_submit.assert_called_once_with(
            priority=1,
            project_id=fxt_project.id_,
            job_name="Prepare Import to Existing Project",
            job_type=JobType.PREPARE_IMPORT_TO_EXISTING_PROJECT.value,
            key=(
                f'{{"import_id": "{fxt_dataset_id}", "project_id": "{fxt_project.id_}", '
                f'"type": "prepare_import_to_existing_project"}}'
            ),
            payload={"import_id": fxt_dataset_id, "project_id": fxt_project.id_},
            metadata=metadata,
            duplicate_policy="replace",
            author=fxt_user_id,
            cancellable=True,
        )

    def test_submit_perform_import_to_new_project_job(
        self, fxt_import_manager, fxt_workspace_id, fxt_dataset_id, fxt_user_id
    ):
        project_type = GetiProjectType.DETECTION
        project_name = "test_detection_project"
        label_names = (["car", "truck", "bus"],)
        color_by_label = {"car": "#00ff00ff", "truck": "#ff0000ff", "bus": "#0000ffff"}
        keypoint_structure = {"edges": [], "positions": []}
        metadata = {"file_id": fxt_dataset_id, "project": {"name": project_name, "type": "detection"}}

        with patch.object(GRPCJobsClient, "submit", return_value=None) as mock_submit:
            fxt_import_manager.submit_perform_import_to_new_project_job(
                import_id=fxt_dataset_id,
                project_type=project_type,
                project_name=project_name,
                label_names=label_names,
                color_by_label=color_by_label,
                keypoint_structure=keypoint_structure,
                author=fxt_user_id,
                metadata=metadata,
            )

        job_type = JobType.PERFORM_IMPORT_TO_NEW_PROJECT.value
        job_payload = {
            "import_id": str(fxt_dataset_id),
            "project_type": project_type.name,
            "project_name": project_name,
            "label_names": label_names,
            "color_by_label": color_by_label,
            "keypoint_structure": keypoint_structure,
            "user_id": fxt_user_id,
        }
        serialized_key = f'{{"import_id": "{fxt_dataset_id}", "type": "{job_type}"}}'

        mock_submit.assert_called_once_with(
            priority=1,
            job_name="Create Project from Dataset",
            job_type=job_type,
            key=serialized_key,
            payload=job_payload,
            metadata=metadata,
            duplicate_policy="replace",
            author=fxt_user_id,
            cancellable=False,
        )

    def test_submit_perform_import_to_existing_project_job(
        self, fxt_import_manager, fxt_workspace_id, fxt_project, fxt_dataset_id, fxt_user_id
    ):
        labels_map = {"a": "car", "b": "person"}
        metadata = {
            "file_id": str(fxt_dataset_id),
            "project": {"id": str(fxt_project.id_), "name": fxt_project.name, "type": "detection"},
            "dataset": {
                "id": None,
                "name": "",
            },
        }

        with patch.object(GRPCJobsClient, "submit", return_value=None) as mock_submit:
            fxt_import_manager.submit_perform_import_to_existing_project_job(
                project_id=fxt_project.id_,
                import_id=fxt_dataset_id,
                labels_map=labels_map,
                dataset_storage_id=None,
                dataset_name=None,
                author=fxt_user_id,
                metadata=metadata,
            )

        job_type = JobType.PERFORM_IMPORT_TO_EXISTING_PROJECT.value
        job_payload = {
            "import_id": str(fxt_dataset_id),
            "project_id": str(fxt_project.id_),
            "labels_map": labels_map,
            "dataset_storage_id": "",
            "dataset_name": "",
            "user_id": str(fxt_user_id),
        }
        serialized_key = f'{{"import_id": "{fxt_dataset_id}", "project_id": "{fxt_project.id_}", "type": "{job_type}"}}'

        mock_submit.assert_called_once_with(
            priority=1,
            project_id=fxt_project.id_,
            job_name="Import Dataset to Existing Project",
            job_type=job_type,
            key=serialized_key,
            payload=job_payload,
            metadata=metadata,
            duplicate_policy="replace",
            author=fxt_user_id,
            cancellable=False,
        )

    def test_get_validated_file_metadata(
        self,
        request: FixtureRequest,
        fxt_import_manager,
        fxt_dataset_id,
    ):
        repo = FileMetadataRepo()
        repo.save(ImportMetadata(fxt_dataset_id, size=10, offset=10))
        request.addfinalizer(lambda: repo.delete_by_id(fxt_dataset_id))

        metadata = fxt_import_manager.get_validated_file_metadata(fxt_dataset_id)
        assert metadata.id_ == fxt_dataset_id
        assert metadata.size == 10
        assert metadata.offset == 10

    def test_get_validated_file_metadata_invalid_id(
        self,
        fxt_import_manager,
        fxt_dataset_id,
    ):
        with pytest.raises(FileNotFoundGetiBaseException):
            fxt_import_manager.get_validated_file_metadata(fxt_dataset_id)

        with pytest.raises(FileNotFoundGetiBaseException):
            fxt_import_manager.get_validated_file_metadata("invalid_id")

    @pytest.mark.parametrize("size,offset", [(0, 0), (10, 0)])
    def test_get_validated_file_metadata_invalid_size(
        self,
        size,
        offset,
        request: FixtureRequest,
        fxt_import_manager,
        fxt_dataset_id,
    ):
        repo = FileMetadataRepo()
        repo.save(ImportMetadata(fxt_dataset_id, size=size, offset=offset))
        request.addfinalizer(lambda: repo.delete_by_id(fxt_dataset_id))

        with pytest.raises(FileNotFullyUploadedGetiBaseException):
            fxt_import_manager.get_validated_file_metadata(fxt_dataset_id)

    def test_get_validated_file_metadata_invalid_metadata_type(
        self,
        request: FixtureRequest,
        fxt_import_manager,
        fxt_dataset_id,
    ):
        repo = FileMetadataRepo()
        repo.save(ExportMetadata(fxt_dataset_id, size=10, offset=10, project_id=ID("dummy_id")))
        request.addfinalizer(lambda: repo.delete_by_id(fxt_dataset_id))

        with pytest.raises(BadRequestGetiBaseException):
            fxt_import_manager.get_validated_file_metadata(fxt_dataset_id)

    @patch("application.import_management.LabelRepo")
    def test_validate_project_label_ids(
        self,
        patched_label_repo,
        fxt_import_manager,
        fxt_project,
        fxt_mongo_id,
    ):
        label_repo = patched_label_repo.return_value
        label_repo.get_by_id.return_value = Label(fxt_mongo_id, "dummy_name", Domain.DETECTION)

        label_ids_map = {"dm_label_1": "sc_label_id_1", "dm_label_2": "sc_label_id_2"}
        try:
            fxt_import_manager.validate_project_label_ids(fxt_project.id_, label_ids_map)
        except Exception as e:
            assert False, f"No exception is expected but got {e}"

    def test_validate_project_label_ids_invalid_project(
        self,
        fxt_import_manager,
    ):
        label_ids_map = {"dm_label_1": "sc_label_id_1", "dm_label_2": "sc_label_id_2"}

        with pytest.raises(BadRequestGetiBaseException) as e:
            fxt_import_manager.validate_project_label_ids("invalid_project_id", label_ids_map)
            assert "No project" in e.details

    @patch("application.import_management.LabelRepo")
    def test_validate_project_label_ids_invalid_label_id(
        self,
        patched_label_repo,
        fxt_import_manager,
        fxt_project,
    ):
        project_id = str(fxt_project.id_)
        label_repo = patched_label_repo.return_value
        label_repo.get_by_id.return_value = NullLabel()

        label_ids_map = {"dm_label_1": "sc_label_id_1", "dm_label_2": "sc_label_id_2"}

        with pytest.raises(BadRequestGetiBaseException) as e:
            fxt_import_manager.validate_project_label_ids(project_id, label_ids_map)
            assert "cannot map a label name to an invalid ID" in e.details

    def test_save_project_id(
        self, request: FixtureRequest, fxt_import_manager, fxt_workspace_id, fxt_dataset_id, fxt_project_id
    ):
        repo = FileMetadataRepo()
        repo.save(ImportMetadata(fxt_dataset_id, size=10, offset=10))
        request.addfinalizer(lambda: repo.delete_by_id(fxt_dataset_id))

        metadata = repo.get_by_id(fxt_dataset_id)
        assert metadata.project_id == ID()

        fxt_import_manager.save_project_id(fxt_dataset_id, fxt_project_id)

        metadata = repo.get_by_id(fxt_dataset_id)
        assert metadata.project_id == fxt_project_id

    def test_save_project_id_no_metadata(self, fxt_import_manager, fxt_workspace_id, fxt_dataset_id, fxt_project_id):
        with pytest.raises(FileNotFoundGetiBaseException):
            fxt_import_manager.save_project_id(fxt_dataset_id, fxt_project_id)
