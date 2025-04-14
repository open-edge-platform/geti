# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest

from entities import UploadOperation
from repos import UploadOperationRepo
from repos.zip_storage_repo import ZipStorageRepo
from usecases import ProjectUploadUseCase

from geti_types import CTX_SESSION_VAR


@pytest.mark.ProjectIEMsComponent
class TestProjectUploadUseCase:
    def test_create_multipart_upload(self, fxt_mongo_id, fxt_session_ctx):
        operation_id = fxt_mongo_id(1)
        mock_size = 100
        upload_id = "dummy upload id"
        CTX_SESSION_VAR.set(fxt_session_ctx)
        expected_operation = UploadOperation(
            id_=operation_id,
            upload_id=upload_id,
            upload_parts=[],
            size=mock_size,
            offset=0,
        )
        with (
            patch.object(UploadOperationRepo, "generate_id", return_value=operation_id) as mock_generate_id,
            patch.object(ZipStorageRepo, "__init__", return_value=None) as mock_init,
            patch.object(ZipStorageRepo, "create_multipart_upload", return_value=upload_id) as mock_create_upload,
            patch.object(UploadOperationRepo, "save", return_value=None) as mock_save,
        ):
            result = ProjectUploadUseCase.create_multipart_upload(upload_length=mock_size)

            assert result == operation_id
            mock_init.assert_called_once_with(
                workspace_id=fxt_session_ctx.workspace_id, organization_id=fxt_session_ctx.organization_id
            )
            mock_generate_id.assert_called_once_with()
            mock_create_upload.assert_called_once_with(operation_id=operation_id)
            mock_save.assert_called_once_with(instance=expected_operation)

    def test_get_multipart_upload_info(self, fxt_mongo_id):
        operation_id = fxt_mongo_id
        mock_size = 100
        mock_offset = 50
        mock_ie_operation = UploadOperation(
            id_=operation_id,
            size=mock_size,
            offset=mock_offset,
        )
        with patch.object(UploadOperationRepo, "get_by_id", return_value=mock_ie_operation) as mock_get:
            result = ProjectUploadUseCase.get_multipart_upload_info(operation_id=operation_id)

            assert result == (mock_size, mock_offset)
            mock_get.assert_called_once_with(id_=operation_id)

    def test_append_to_multipart_upload(self, fxt_mongo_id, fxt_session_ctx):
        # Arrange
        operation_id = fxt_mongo_id(1)
        mock_offset = 50
        mock_data = b"test data"
        mock_etag = "dummy etag"
        mock_ie_operation = UploadOperation(
            id_=operation_id,
            upload_id="upload_id",
            upload_parts=[],
            size=1000,
            offset=mock_offset,
        )
        with (
            patch.object(UploadOperationRepo, "get_by_id", return_value=mock_ie_operation) as mock_get,
            patch.object(ZipStorageRepo, "__init__", return_value=None) as mock_init,
            patch.object(ZipStorageRepo, "upload_part_to_file", return_value=mock_etag) as mock_upload_part,
            patch.object(UploadOperationRepo, "save", return_value=None) as mock_save,
        ):
            # Act
            result = ProjectUploadUseCase.append_to_multipart_upload(
                operation_id=operation_id, offset=mock_offset, data=mock_data
            )

            # Assert
            assert result == mock_offset + len(mock_data)
            mock_init.assert_called_once_with(
                workspace_id=fxt_session_ctx.workspace_id, organization_id=fxt_session_ctx.organization_id
            )
            mock_get.assert_called_once_with(id_=operation_id)
            mock_upload_part.assert_called()
            mock_save.assert_called_once_with(instance=mock_ie_operation)

            # Check that the part was correctly appended to the UploadOperation's upload_parts
            assert len(mock_ie_operation.upload_parts) == 1
            assert mock_ie_operation.upload_parts[0] == {"ETag": mock_etag, "PartNumber": 1}
