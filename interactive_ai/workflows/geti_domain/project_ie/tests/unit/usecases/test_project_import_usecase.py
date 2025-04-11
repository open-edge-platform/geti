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
import contextlib
import os.path
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import ANY, MagicMock, _Call, call, patch
from uuid import uuid4
from zipfile import ZipFile

import pytest
from geti_spicedb_tools import SpiceDB
from geti_types import ID, ProjectIdentifier
from grpc_interfaces.model_registration.client import ModelRegistrationClient
from grpc_interfaces.model_registration.pb.service_pb2 import Model as ProtoModel
from grpc_interfaces.model_registration.pb.service_pb2 import Project as ProtoProject
from sc_sdk.entities.model import Model, NullModel
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import ProjectRepo
from sc_sdk.repos.storage.storage_client import BinaryObjectType
from sc_sdk.services import ModelService
from sc_sdk.versioning import DataVersion

from job.entities import Manifest, ProjectZipArchive, ProjectZipArchiveWrapper, ZipArchive
from job.entities.exceptions import (
    ImportProjectFailedException,
    ImportProjectUnsupportedVersionException,
    SignatureVerificationFailed,
    ZipBombDetectedError,
)
from job.repos import BinaryStorageRepo, DocumentRepo
from job.repos.zip_storage_repo import ZipStorageRepo
from job.usecases import ImportDataRedactionUseCase, ProjectImportUseCase, SignatureUseCaseHelper
from job.usecases.data_migration_usecase import DataMigrationUseCase
from job.usecases.signature_usecase import PublicKeyBytes, SignatureBytes
from job.utils.model_registration_utils import ModelMapper, ProjectMapper

DUMMY_SIGNATURE_BYTES = SignatureBytes(b"dummy_signature_bytes")
DUMMY_PUBLIC_KEY_BYTES = PublicKeyBytes(b"dummy_public_key_data")


def do_nothing(*args, **kwargs):
    pass


def identity_map(self, x):
    return x


def mocked_download_import_zip(file_id: ID, local_zip_path: str):
    if not os.path.exists(os.path.dirname(local_zip_path)):
        os.makedirs(os.path.dirname(local_zip_path))

    with TemporaryDirectory() as temp_dir:
        project_archive = Path(temp_dir) / "project.zip"
        with ZipFile(project_archive, "w") as zipfile:
            zipfile.writestr("data", b"data")
        with ProjectZipArchiveWrapper(local_zip_path) as zipfile:
            zipfile.add_project_archive(project_archive)
            zipfile.add_signature(DUMMY_SIGNATURE_BYTES)
            zipfile.add_public_key(DUMMY_PUBLIC_KEY_BYTES)


@pytest.fixture
def fxt_mock_progress_callback():
    yield MagicMock()


@pytest.mark.ProjectIEMsComponent
class TestProjectImportUseCase:
    @pytest.mark.parametrize("import_version, current_version", (("1.0", "1.0"), ("0.5", "1.0"), ("1.5", "1.0")))
    def test_import_zip(
        self, fxt_ote_id, fxt_session_ctx, fxt_mock_progress_callback, import_version, current_version
    ) -> None:
        file_id = fxt_ote_id(0)
        project_id = fxt_ote_id(1)
        project_identifier = ProjectIdentifier(fxt_session_ctx.workspace_id, project_id)
        creator_id = ID(str(uuid4()))
        manifest = Manifest(version=import_version, export_date=datetime.now(), min_id="00000000000000000000000f")
        import_data_version = DataVersion(import_version)
        current_data_version = DataVersion(current_version)

        # Python has a limit of 20 statically nested blocks ('with' statements); to override this limitation,
        # some of the mocks are applied dynamically with "enter_context()"
        mocks = [
            patch.object(ImportDataRedactionUseCase, "update_user_info_in_mongodb_doc", new=identity_map),
            patch.object(
                ImportDataRedactionUseCase, "recreate_objectid_based_binary_filename_in_mongodb_doc", new=identity_map
            ),
            patch.object(ImportDataRedactionUseCase, "recreate_objectid_in_mongodb_doc", new=identity_map),
            patch.object(ImportDataRedactionUseCase, "recreate_objectid_in_file", new=identity_map),
            patch.object(ImportDataRedactionUseCase, "recreate_objectid_in_url", new=identity_map),
            patch.object(ImportDataRedactionUseCase, "update_creation_time_in_mongodb_doc", new=identity_map),
            patch.object(ZipArchive, "validate_against_zip_bomb", return_value=1.0),
            patch.object(ZipArchive, "validate_files_structure"),
            patch.object(ProjectZipArchive, "__init__", new=do_nothing),
            patch.object(ProjectZipArchive, "get_manifest", return_value=manifest),
            patch.object(
                ProjectZipArchive,
                "get_documents_by_collection",
                return_value=[f'{{"_id": {{"$oid": "{str(project_id)}"}}, "name": "bar"}}'],
            ),
            patch.object(ProjectZipArchive, "get_objects_by_type", return_value=[("local_path_1", "remote_path_1")]),
            patch.object(ProjectZipArchive, "close", return_value=None),
            patch.object(ProjectZipArchive, "get_collection_names", return_value=["coll_1", "project", "job"]),
            patch.object(BinaryStorageRepo, "__init__", new=do_nothing),
            patch.object(SpiceDB, "__init__", new=do_nothing),
        ]
        with (
            contextlib.ExitStack() as stack,
            patch.object(BinaryStorageRepo, "store_objects_by_type", return_value=None) as mock_store_objects,
            patch.object(SpiceDB, "create_project", return_value=None) as mock_spicedb_create_project,
            patch.object(DocumentRepo, "insert_documents_to_db_collection", return_value=None) as mock_insert_documents,
            patch.object(ZipStorageRepo, "__init__", new=do_nothing),
            patch.object(ProjectImportUseCase, "_download_import_zip", new=mocked_download_import_zip),
            patch.object(ProjectImportUseCase, "_delete_import_zip") as mock_delete_import_zip,
            patch.object(ProjectImportUseCase, "_register_active_models") as mock_register_active_models,
            patch.object(ProjectImportUseCase, "_verify_signature") as mock_signature_verification,
            patch("job.usecases.project_import_usecase.publish_metadata_update") as mock_metadata_update,
            patch.object(DataMigrationUseCase, "upgrade_project_to_current_version") as mock_date_upgrade,
            patch.object(DataVersion, "get_current", return_value=current_data_version),
        ):
            for m in mocks:
                stack.enter_context(m)
            ProjectImportUseCase().import_zip(
                file_id=file_id, creator_id=creator_id, progress_callback=fxt_mock_progress_callback
            )

        mock_insert_documents.assert_called_with(collection_name=DocumentRepo.PROJECTS_COLLECTION, documents=ANY)
        mock_store_objects.assert_called()
        mock_register_active_models.assert_called_once_with(project_identifier=project_identifier)
        fxt_mock_progress_callback.assert_called()
        mock_metadata_update.assert_called_once_with(
            {
                "project": {
                    "id": project_id,
                    "name": "bar",
                },
            }
        )
        mock_signature_verification.assert_called()
        # check no data upgrade is performed if importing project with older version
        if import_version < current_version:
            mock_date_upgrade.assert_called_once_with(project_id=project_id, version=import_data_version)
        else:
            mock_date_upgrade.assert_not_called()
        mock_spicedb_create_project.assert_called_once()
        mock_delete_import_zip.assert_called()

    def test_import_zip_signature_verification_failed(self, fxt_ote_id, fxt_mock_progress_callback) -> None:
        # Arrange
        file_id = fxt_ote_id(0)
        creator_id = ID(str(uuid4()))

        # Act & Assert
        with (
            pytest.raises(SignatureVerificationFailed),
            patch.object(
                ProjectImportUseCase, "_ProjectImportUseCase__import_zip", side_effect=SignatureVerificationFailed
            ),
            patch.object(ProjectImportUseCase, "rollback_import") as mock_rollback,
            patch.object(ProjectImportUseCase, "_delete_import_zip") as mock_delete_import_zip,
        ):
            ProjectImportUseCase().import_zip(
                file_id=file_id, creator_id=creator_id, progress_callback=fxt_mock_progress_callback
            )
            mock_rollback.assert_called_once_with(file_id=file_id)
            mock_delete_import_zip.assert_called()

    def test_rollback_import(self, fxt_project_identifier, fxt_ote_id) -> None:
        file_id = fxt_ote_id(123)
        import_use_case = ProjectImportUseCase()
        import_use_case.project_id = fxt_ote_id(456)
        with (
            patch.object(DocumentRepo, "__init__", new=do_nothing),
            patch.object(DocumentRepo, "delete_all_documents") as mock_delete_all_docs,
            patch.object(BinaryStorageRepo, "__init__", new=do_nothing),
            patch.object(BinaryStorageRepo, "get_object_types", return_value=[BinaryObjectType.IMAGES]),
            patch.object(BinaryStorageRepo, "delete_all_objects_by_type") as mock_delete_objects_by_type,
        ):
            import_use_case.rollback_import(file_id=file_id)

        mock_delete_all_docs.assert_called_once_with()
        mock_delete_objects_by_type.assert_called_once_with(object_type=BinaryObjectType.IMAGES)

    @pytest.mark.parametrize(
        "is_task_chain,first_task_trained,second_task_trained",
        [
            (False, False, False),
            (False, True, False),
            (True, False, False),
            (True, True, False),
            (True, False, True),
            (True, True, True),
        ],
        ids=[
            "Single-task, no model trained",
            "Single-task, model trained",
            "Task-chain, no model trained",
            "Task-chain, first task with trained model",
            "Task-chain, second task with trained model",
            "Task-chain, both tasks with trained model",
        ],
    )
    def test_register_active_models(
        self, is_task_chain, first_task_trained, second_task_trained, fxt_project_identifier, fxt_ote_id
    ) -> None:
        dummy_project = MagicMock(spec=Project)
        dummy_project.id_ = fxt_project_identifier.project_id
        proto_project = MagicMock(spec=ProtoProject)
        proto_project.id_ = str(fxt_project_identifier.project_id)
        num_tasks = 2 if is_task_chain else 1
        tasks = [MagicMock(spec=TaskNode) for _ in range(num_tasks)]
        tasks[0].id_ = fxt_ote_id(100)
        if is_task_chain:
            tasks[1].id_ = fxt_ote_id(101)
        active_base_models = [
            MagicMock(spec=Model) if first_task_trained else NullModel(),
            MagicMock(spec=Model) if second_task_trained else NullModel(),
        ]
        active_optimized_models = [
            MagicMock(spec=Model) if first_task_trained else NullModel(),
            MagicMock(spec=Model) if second_task_trained else NullModel(),
        ]
        proto_models = [MagicMock(spec=ProtoModel) for _ in range(num_tasks)]

        with (
            patch.object(ProjectRepo, "get_by_id", return_value=dummy_project),
            patch.object(dummy_project, "get_trainable_task_nodes", return_value=tasks),
            patch.object(ModelService, "get_base_active_model", side_effect=active_base_models),
            patch.object(ModelService, "get_inference_active_model", side_effect=active_optimized_models),
            patch.object(ProjectMapper, "forward", return_value=proto_project),
            patch.object(ModelMapper, "forward", side_effect=proto_models),
            patch.object(ModelRegistrationClient, "__init__", new=do_nothing),
            patch.object(ModelRegistrationClient, "close"),
            patch.object(ModelRegistrationClient, "register") as mock_register,
        ):
            ProjectImportUseCase._register_active_models(project_identifier=fxt_project_identifier)

        if is_task_chain:
            expected_register_calls: list[_Call] = []
            if first_task_trained:
                expected_register_calls.append(
                    call(
                        name=f"{str(fxt_project_identifier.project_id)}-{str(tasks[0].id_)}",
                        project=proto_project,
                        models=ANY,
                        override=True,
                    )
                )
                expected_register_calls.append(
                    call(
                        name=f"{str(fxt_project_identifier.project_id)}-active",
                        project=proto_project,
                        models=ANY,
                        override=True,
                    )
                )
            if second_task_trained:
                expected_register_calls.append(
                    call(
                        name=f"{str(fxt_project_identifier.project_id)}-{str(tasks[1].id_)}",
                        project=proto_project,
                        models=ANY,
                        override=True,
                    )
                )
            mock_register.assert_has_calls(expected_register_calls, any_order=True)
        else:
            if first_task_trained:
                mock_register.assert_called_once_with(
                    name=f"{str(fxt_project_identifier.project_id)}-active",
                    project=proto_project,
                    models=ANY,
                    override=True,
                )
                assert mock_register.call_args.kwargs["models"] == [proto_models[0]]
            else:
                mock_register.assert_not_called()

    def test_signature_verification(self, request) -> None:
        # Arrange
        local_zip_path = "test_project.zip"
        mocked_signature_use_case = MagicMock()
        with ZipFile(local_zip_path, "w") as inner_zip:
            inner_zip.writestr("data", b"data")

        request.addfinalizer(lambda: os.remove(local_zip_path))

        # Act
        with (
            patch.object(SignatureUseCaseHelper, "get_signature_use_case", return_value=mocked_signature_use_case),
            patch("job.usecases.project_import_usecase.read_file_in_chunks") as mock_read_file,
        ):
            ProjectImportUseCase._verify_signature(
                project_archive_path=local_zip_path,
                signature=DUMMY_SIGNATURE_BYTES,
                public_key=DUMMY_PUBLIC_KEY_BYTES,
            )

        # Assert
        mock_read_file.assert_called_once_with(filename=local_zip_path)
        mocked_signature_use_case.verify.assert_called_once_with(
            data=ANY,
            signature=DUMMY_SIGNATURE_BYTES,
            public_key=DUMMY_PUBLIC_KEY_BYTES,
        )

    def test_signature_verification_failed(self, request) -> None:
        # Arrange
        local_zip_path = "test_project.zip"
        mocked_signature_use_case = MagicMock()
        mocked_signature_use_case.verify.side_effect = SignatureVerificationFailed

        with ZipFile(local_zip_path, "w") as zipfile:
            zipfile.writestr("data", b"data")
        request.addfinalizer(lambda: os.remove(local_zip_path))

        # Act & Assert
        with (
            patch.object(SignatureUseCaseHelper, "get_signature_use_case", return_value=mocked_signature_use_case),
            pytest.raises(SignatureVerificationFailed),
        ):
            ProjectImportUseCase._verify_signature(
                project_archive_path=local_zip_path,
                signature=DUMMY_SIGNATURE_BYTES,
                public_key=DUMMY_PUBLIC_KEY_BYTES,
            )

    def test_import_zip_bomb(self, request, fxt_ote_id, fxt_mock_progress_callback) -> None:
        # Arrange
        operation_id = fxt_ote_id(0)
        creator_id = ID(str(uuid4()))
        local_zip_path = "test_project.zip"
        with ZipFile(local_zip_path, "w") as inner_zip:
            inner_zip.writestr("data", b"data")

        request.addfinalizer(lambda: os.remove(local_zip_path))

        # Act
        with (
            patch.object(ProjectImportUseCase, "_download_import_zip", new=mocked_download_import_zip),
            patch.object(ProjectImportUseCase, "_delete_import_zip") as mock_delete_import_zip,
            patch.object(ZipArchive, "validate_against_zip_bomb", side_effect=ZipBombDetectedError),
            pytest.raises(ImportProjectFailedException),
        ):
            ProjectImportUseCase().import_zip(
                file_id=operation_id, creator_id=creator_id, progress_callback=fxt_mock_progress_callback
            )

        mock_delete_import_zip.assert_called()

    def test_import_zip_data_upgrade_version_not_supported(
        self,
        fxt_ote_id,
        fxt_session_ctx,
        fxt_mock_progress_callback,
    ) -> None:
        # Arrange
        file_id = fxt_ote_id(0)
        project_id = fxt_ote_id(1)
        creator_id = ID(str(uuid4()))
        import_data_version = DataVersion("2.0")
        current_data_version = DataVersion("1.0")
        manifest = Manifest(
            version=import_data_version.version_string, export_date=datetime.now(), min_id="00000000000000000000000f"
        )

        # Python has a limit of 20 statically nested blocks ('with' statements); to override this limitation,
        # some of the mocks are applied dynamically with "enter_context()"
        mocks = [
            patch.object(ImportDataRedactionUseCase, "update_user_info_in_mongodb_doc", new=identity_map),
            patch.object(
                ImportDataRedactionUseCase, "recreate_objectid_based_binary_filename_in_mongodb_doc", new=identity_map
            ),
            patch.object(ImportDataRedactionUseCase, "recreate_objectid_in_mongodb_doc", new=identity_map),
            patch.object(ImportDataRedactionUseCase, "recreate_objectid_in_file", new=identity_map),
            patch.object(ImportDataRedactionUseCase, "recreate_objectid_in_url", new=identity_map),
            patch.object(ImportDataRedactionUseCase, "update_creation_time_in_mongodb_doc", new=identity_map),
            patch.object(ProjectZipArchive, "__init__", new=do_nothing),
            patch.object(ProjectZipArchive, "get_manifest", return_value=manifest),
            patch.object(
                ProjectZipArchive,
                "get_documents_by_collection",
                return_value=[f'{{"_id": {{"$oid": "{str(project_id)}"}}, "name": "bar"}}'],
            ),
            patch.object(ProjectZipArchive, "get_objects_by_type", return_value=[("local_path_1", "remote_path_1")]),
            patch.object(ProjectZipArchive, "close", return_value=None),
            patch.object(ProjectZipArchive, "get_collection_names", return_value=["collection_1", "project"]),
            patch.object(BinaryStorageRepo, "__init__", new=do_nothing),
        ]

        # Act & Assert
        with (
            contextlib.ExitStack() as stack,
            pytest.raises(ImportProjectUnsupportedVersionException),
            patch.object(BinaryStorageRepo, "store_objects_by_type", return_value=None),
            patch.object(DocumentRepo, "insert_documents_to_db_collection", return_value=None),
            patch.object(ZipStorageRepo, "__init__", new=do_nothing),
            patch.object(ProjectImportUseCase, "_download_import_zip", new=mocked_download_import_zip),
            patch.object(ProjectImportUseCase, "_delete_import_zip", new=do_nothing),
            patch.object(ProjectImportUseCase, "_register_active_models"),
            patch.object(ProjectImportUseCase, "_verify_signature"),
            patch("job.usecases.project_import_usecase.publish_metadata_update"),
            patch.object(DataMigrationUseCase, "upgrade_project_to_current_version"),
            patch.object(DataVersion, "get_current", return_value=current_data_version),
            patch.object(ZipArchive, "validate_against_zip_bomb", return_value=1.0),
            patch.object(ZipArchive, "validate_files_structure"),
        ):
            for m in mocks:
                stack.enter_context(m)
            ProjectImportUseCase().import_zip(
                file_id=file_id, creator_id=creator_id, progress_callback=fxt_mock_progress_callback
            )
