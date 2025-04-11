# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
"""
This module tests the object storage repo
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from communication.repos.object_storage_repo import ObjectDataRepo

ENV_VARS = {
    "S3_CREDENTIALS_PROVIDER": "local",
    "S3_HOST": "host_name",
    "S3_ACCESS_KEY": "access_key",
    "S3_SECRET_KEY": "secret_key",
}


@pytest.mark.DatasetIEMsComponent
class TestObjectStorageRepo:
    """
    unitest the object storage repo
    """

    @patch("communication.repos.object_storage_repo.boto3.client")
    @patch.dict(os.environ, ENV_VARS)
    def test_init(self, mocked_client_init):
        # Arrange
        mock_client = MagicMock()
        mocked_client_init.return_value = mock_client
        object_repo = ObjectDataRepo()

        # Act
        mocked_client_init.assert_called_once_with(
            service_name="s3",
            aws_access_key_id=ENV_VARS["S3_ACCESS_KEY"],
            aws_secret_access_key=ENV_VARS["S3_SECRET_KEY"],
            endpoint_url=f"http://{ENV_VARS['S3_HOST']}",
        )

        # Assert
        assert object_repo.client == mock_client

    @patch("communication.repos.object_storage_repo.boto3.client")
    @patch.dict(os.environ, ENV_VARS)
    def test_save_file(self, mocked_client_init):
        # Arrange
        mock_client = MagicMock()
        mocked_client_init.return_value = mock_client
        object_repo = ObjectDataRepo()
        id_ = object_repo.workspace_id
        data = b""

        # Act
        object_repo.save_file(id_=id_, data=data)

        # Assert
        mock_client.put_object.assert_called_once_with(
            Body=data,
            Bucket=object_repo.bucket,
            Key=f"{object_repo.get_import_directory_path(id_)}/{object_repo.zipped_file_name}",
            ContentType="application/octet-stream",
        )

    @patch("communication.repos.object_storage_repo.boto3.client")
    @patch.dict(os.environ, ENV_VARS)
    def test_create_multi_upload(self, mocked_client_init):
        # Arrange
        mock_client = MagicMock()
        upload_id = "upload_id"
        mocked_client_init.return_value = mock_client
        mock_client.create_multipart_upload.return_value = {"UploadId": upload_id}
        object_repo = ObjectDataRepo()
        id_ = object_repo.workspace_id

        # Act
        response = object_repo.create_multi_upload_file(id_=id_)

        # Assert
        mock_client.create_multipart_upload.assert_called_once_with(
            Bucket=object_repo.bucket,
            Key=f"{object_repo.get_import_directory_path(id_)}/{object_repo.zipped_file_name}",
        )
        assert response == upload_id

    @patch("communication.repos.object_storage_repo.boto3.client")
    @patch.dict(os.environ, ENV_VARS)
    def test_upload_part_to_file(self, mocked_client_init):
        # Arrange
        mock_client = MagicMock()
        upload_id = "upload_id"
        part_number = 1
        data = b"part_data"
        mocked_client_init.return_value = mock_client
        mock_client.upload_part.return_value = {"ETag": "etag"}
        object_repo = ObjectDataRepo()
        id_ = object_repo.workspace_id

        # Act
        response = object_repo.upload_part_to_file(id_=id_, upload_id=upload_id, part_number=part_number, data=data)

        # Assert
        mock_client.upload_part.assert_called_once_with(
            Body=data,
            Bucket=object_repo.bucket,
            Key=f"{object_repo.get_import_directory_path(id_)}/{object_repo.zipped_file_name}",
            PartNumber=part_number,
            UploadId=upload_id,
        )
        assert response == "etag"

    @patch("communication.repos.object_storage_repo.boto3.client")
    @patch.dict(os.environ, ENV_VARS)
    def test_complete_file_upload(self, mocked_client_init):
        # Arrange
        mock_client = MagicMock()
        upload_id = "upload_id"
        parts = [{"ETag": "etag1", "PartNumber": 1}, {"ETag": "etag2", "PartNumber": 2}]
        mocked_client_init.return_value = mock_client
        object_repo = ObjectDataRepo()
        id_ = object_repo.workspace_id

        # Act
        object_repo.complete_file_upload(id_=id_, upload_id=upload_id, parts=parts)

        # Assert
        mock_client.complete_multipart_upload.assert_called_once_with(
            Bucket=object_repo.bucket,
            Key=f"{object_repo.get_import_directory_path(id_)}/{object_repo.zipped_file_name}",
            UploadId=upload_id,
            MultipartUpload={
                "Parts": [
                    {"ETag": "etag1", "PartNumber": 1},
                    {"ETag": "etag2", "PartNumber": 2},
                ],
            },
        )

    @patch("communication.repos.object_storage_repo.boto3.client")
    @patch.dict(os.environ, ENV_VARS)
    def test_get_zipped_dataset_presigned_url(self, mocked_client_init, fxt_temp_directory):
        # Arrange
        mock_client = MagicMock()
        dummy_filename = "dataset.zip"
        mocked_client_init.return_value = mock_client
        object_repo = ObjectDataRepo()
        id_ = object_repo.workspace_id

        # Act
        object_repo.get_zipped_dataset_presigned_url(id_=id_, filename=dummy_filename)

        # Assert
        mock_client.generate_presigned_url.assert_called_once_with(
            ClientMethod="get_object",
            Params={
                "Bucket": "temporaryfiles",
                "Key": f"{object_repo.get_export_directory_path(id_)}/{object_repo.zipped_file_name}",
                "ResponseContentDisposition": f'attachment; filename="{dummy_filename}"',
            },
            ExpiresIn=24 * 60 * 60,
        )
