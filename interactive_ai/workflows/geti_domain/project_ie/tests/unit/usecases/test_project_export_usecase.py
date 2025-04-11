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
import shutil
from unittest.mock import ANY, MagicMock, patch

import pytest
from geti_types import CTX_SESSION_VAR, ID, Session
from sc_sdk.repos.base import SessionBasedRepo
from sc_sdk.versioning import DataVersion

from job.entities.zip_archive import ProjectZipArchive, ProjectZipArchiveWrapper
from job.repos import BinaryStorageRepo, DocumentRepo, ZipStorageRepo
from job.usecases import ExportDataRedactionUseCase, ProjectExportUseCase, SignatureUseCaseHelper


def do_nothing(*args, **kwargs):
    pass


def identity_map(self, x):
    return x


@pytest.mark.JobsComponent
class TestProjectExportUseCase:
    def test_export_as_zip(self, request, fxt_ote_id) -> None:
        def mocked_upload_downloadable_archive(self, operation_id: ID, zip_local_path: str):
            shutil.move(zip_local_path, exported_zip_path)

        def mocked_progress_callback(progress: float, message: str) -> None:
            mocked_progress(progress, message)

        dummy_signature_bytes = b"dummy_signature_bytes"
        mocked_signing_use_case = MagicMock()
        mocked_signing_use_case.public_key_bytes = b"dummy_public_key_data"
        mocked_signing_use_case.generate_signature.return_value = dummy_signature_bytes
        mocked_progress = MagicMock()
        project_id = fxt_ote_id(1)
        export_id = fxt_ote_id(1000)
        exported_zip_path = "test_project_archive.zip"
        session: Session = CTX_SESSION_VAR.get()
        download_url = (
            f"api/v1/organizations/{session.organization_id}/workspaces/{session.workspace_id}/"
            f"projects/{project_id}/exports/{export_id}/download"
        )
        # Python has a limit of 20 statically nested blocks ('with' statements); to override this limitation,
        # some of the mocks are applied dynamically with "enter_context()"
        mocks = [
            patch.object(SessionBasedRepo, "generate_id", return_value=export_id),
            patch.object(BinaryStorageRepo, "__init__", new=do_nothing),
            patch.object(
                BinaryStorageRepo, "get_all_objects_by_type", return_value=[("local_path_1", "remote_path_1")]
            ),
            patch.object(ZipStorageRepo, "__init__", new=do_nothing),
            patch.object(ZipStorageRepo, "upload_downloadable_archive", new=mocked_upload_downloadable_archive),
            patch.object(DocumentRepo, "get_all_documents_from_db_for_collection", return_value=[{"key1": "value1"}]),
            patch.object(DocumentRepo, "get_collection_names", return_value=("collection_1",)),
            patch.object(ExportDataRedactionUseCase, "remove_container_info_in_mongodb_doc", new=identity_map),
            patch.object(ExportDataRedactionUseCase, "remove_job_id_in_mongodb_doc", new=identity_map),
            patch.object(ExportDataRedactionUseCase, "remove_lock_in_mongodb_doc", new=identity_map),
            patch.object(ExportDataRedactionUseCase, "replace_objectid_in_mongodb_doc", new=identity_map),
            patch.object(
                ExportDataRedactionUseCase, "replace_objectid_based_binary_filename_in_mongodb_doc", new=identity_map
            ),
            patch.object(ExportDataRedactionUseCase, "replace_objectid_in_url", new=identity_map),
            patch.object(ExportDataRedactionUseCase, "replace_objectid_in_file", new=identity_map),
            patch.object(ExportDataRedactionUseCase, "mask_user_info_in_mongodb_doc", new=identity_map),
            patch.object(
                ExportDataRedactionUseCase, "objectid_replacement_min_id", return_value="00000000000000000000000f"
            ),
            patch.object(SignatureUseCaseHelper, "get_signature_use_case", return_value=mocked_signing_use_case),
        ]
        with (
            contextlib.ExitStack() as stack,
            patch.object(ProjectZipArchive, "add_collection_with_documents") as mock_add_collection,
            patch.object(ProjectZipArchive, "add_objects_by_type") as mock_add_objects,
            patch.object(ProjectZipArchive, "add_manifest") as mock_add_manifest,
            patch.object(ProjectZipArchiveWrapper, "add_signature") as mock_add_signature,
            patch.object(ProjectZipArchiveWrapper, "add_public_key") as mock_add_public_key,
            patch.object(DataVersion, "get_current", return_value=DataVersion("1.0")) as mock_get_version,
            patch("job.usecases.project_export_usecase.publish_metadata_update") as mock_metadata_update,
        ):
            for m in mocks:
                stack.enter_context(m)
            ProjectExportUseCase.export_as_zip(
                project_id=project_id,
                progress_callback=mocked_progress_callback,
            )

        request.addfinalizer(lambda: os.remove(exported_zip_path))
        mock_add_collection.assert_called_once_with(collection_name="collection_1", documents=ANY)
        mock_add_objects.assert_called()
        mock_get_version.assert_called_once_with()
        mock_add_manifest.assert_called_once_with(version="1.0", min_id=ANY)
        mocked_progress.assert_called()
        assert os.path.exists(exported_zip_path)
        mock_metadata_update.assert_called_once_with(metadata={"download_url": download_url, "size": 0})
        mock_add_signature.assert_called_once_with(signature=dummy_signature_bytes)
        mock_add_public_key.assert_called_once_with(public_key=mocked_signing_use_case.public_key_bytes)
