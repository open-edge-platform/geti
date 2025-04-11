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
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from job.repos.object_storage_repo import ObjectStorageRepo
from job.utils.exceptions import FileNotFoundException, MissingEnvVariables, WrongS3CredentialsProvider

# Define environment variables for testing
ENV_VARS = {
    "S3_CREDENTIALS_PROVIDER": "local",
    "S3_HOST": "test_host",
    "S3_ACCESS_KEY": "test_access_key",
    "S3_SECRET_KEY": "test_secret_key",
}


@pytest.fixture
@patch("job.repos.object_storage_repo.boto3.client")
def fxt_object_storage_repo(mocked_boto3_client):
    # Set environment variables
    os.environ.update(ENV_VARS)
    return ObjectStorageRepo()


@pytest.mark.JobsComponent
class TestObjectStorageRepo:
    """
    Unit tests for the ObjectStorageRepo class
    """

    @patch("job.repos.object_storage_repo.boto3.client")
    @patch.dict(os.environ, ENV_VARS)
    def test_init(self, mocked_client_init):
        # Arrange
        mock_client = MagicMock()
        mocked_client_init.return_value = mock_client

        # Act
        object_repo = ObjectStorageRepo()

        # Assert
        mocked_client_init.assert_called_once_with(
            service_name="s3",
            aws_access_key_id=ENV_VARS["S3_ACCESS_KEY"],
            aws_secret_access_key=ENV_VARS["S3_SECRET_KEY"],
            endpoint_url=f"http://{ENV_VARS['S3_HOST']}",
        )
        assert object_repo.client == mock_client

    @patch("job.repos.object_storage_repo.boto3.client")
    @patch.dict(os.environ, {"S3_CREDENTIALS_PROVIDER": "unknown"})
    def test_init_with_error(self, mocked_client_init):
        # Arrange
        mock_client = MagicMock()
        mocked_client_init.return_value = mock_client

        # Act & Assert
        with pytest.raises(WrongS3CredentialsProvider):
            _ = ObjectStorageRepo()

    def test_validate_environment_variables(self, fxt_object_storage_repo):
        # Arrange
        required_variables = ["S3_ACCESS_KEY", "S3_SECRET_KEY"]

        # Act
        with patch.dict(os.environ, ENV_VARS):
            fxt_object_storage_repo._ObjectStorageRepo__validate_environment_variables(required_variables)

        # Assert: No exceptions are raised

    def test_validate_environment_variables_missing_variables(self, fxt_object_storage_repo):
        # Arrange
        required_variables = ["S3_ACCESS_KEY", "MISSING_ENV_VAR"]

        # Act & Assert
        with patch.dict(os.environ, ENV_VARS):
            with pytest.raises(MissingEnvVariables, match=r".*MISSING_ENV_VAR.*"):
                fxt_object_storage_repo._ObjectStorageRepo__validate_environment_variables(required_variables)

    def test_upload_file(self, fxt_object_storage_repo):
        # Arrange
        mocked_client = MagicMock()
        file_path = "test_data/file1.txt"
        key = "uploads/test_data/file1.txt"
        data = b"Test file content"
        mocked_client.upload_fileobj.return_value = None
        fxt_object_storage_repo.client = mocked_client

        # Mock the file open function
        mock_file = mock_open(read_data=data)
        with patch("builtins.open", mock_file):
            # Act
            fxt_object_storage_repo.upload_file(source_path=file_path, key=key)

        # Assert
        mocked_client.upload_fileobj.assert_called_once_with(
            Bucket=fxt_object_storage_repo.bucket,
            Key=key,
            Fileobj=mock_file.return_value,
        )

    def test_download_directory(self, fxt_object_storage_repo):
        # Arrange
        mocked_client = MagicMock()
        dir_path = os.path.join(os.path.dirname(__file__), "test_data")
        key = "downloads/test_data/"
        file_paths = ["file1.txt", "file2.txt"]
        mocked_client.list_objects.return_value = {"Contents": [{"Key": key + path} for path in file_paths]}
        mocked_client.download_file.return_value = None
        fxt_object_storage_repo.client = mocked_client

        # Act
        fxt_object_storage_repo.download_directory(target_path=dir_path, key=key)

        # Assert
        expected_calls = [
            call(Bucket=fxt_object_storage_repo.bucket, Filename=dir_path + file_path, Key=key + file_path)
            for file_path in file_paths
        ]
        mocked_client.download_file.assert_has_calls(expected_calls, any_order=True)

    def test_download_directory_with_error(self, fxt_object_storage_repo):
        # Arrange
        mocked_client = MagicMock()
        dir_path = os.path.join(os.path.dirname(__file__), "test_data")
        key = "downloads/test_data/"
        mocked_client.list_objects.return_value = {}
        mocked_client.download_file.return_value = None
        fxt_object_storage_repo.client = mocked_client

        # Act & Assert
        with pytest.raises(FileNotFoundException):
            fxt_object_storage_repo.download_directory(target_path=dir_path, key=key)

    def test_download_file(self, fxt_object_storage_repo):
        # Arrange
        mocked_client = MagicMock()
        file_path = "test_data/file1.txt"
        key = "downloads/test_data/file1.txt"
        mocked_client.download_file.return_value = None
        fxt_object_storage_repo.client = mocked_client

        # Act
        fxt_object_storage_repo.download_file(target_path=file_path, key=key)

        # Assert
        mocked_client.download_file.assert_called_once_with(
            Bucket=fxt_object_storage_repo.bucket, Key=key, Filename=file_path
        )
