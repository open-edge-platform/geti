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
This module implements upload endpoint tests
"""

import os
import tempfile
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from communication.endpoints.main import app
from communication.helpers.http_exceptions import NotEnoughSpaceGetiBaseException
from communication.repos.file_metadata_repo import FileMetadataRepo
from domain.entities.dataset_ie_file_metadata import NullFileMetadata

from geti_types import ID

client = TestClient(app)


@pytest.fixture
def fxt_create_a_temp_file():
    with tempfile.TemporaryFile() as file:
        yield file


@pytest.mark.DatasetIEMsComponent
class TestUploadEndpoints:
    """
    Tests upload endpoints, both simple (one go) adn TUS (resumable)
    """

    @patch("application.file_object_management.ObjectDataRepo")
    def test_upload_file(self, patched_object_data_repo, request, fxt_url_prefix, fxt_create_a_temp_file):
        """
        Test simple file upload
        """
        # arrange
        upload_data = b"Hello world!"
        upload_file = fxt_create_a_temp_file
        upload_file.write(upload_data)
        upload_file.seek(0)

        # act
        response = client.post(
            f"{fxt_url_prefix}/datasets/uploads",
            files={"file": ("my_file", upload_file, "application/octet-stream")},
        )
        data = response.json()

        # assert
        assert response.status_code == 200
        assert "file_id" in data
        self._assert_upload_completed(
            data["file_id"],
            upload_data,
        )

    @patch("application.file_object_management.ObjectDataRepo")
    def test_upload_file_zero_size(self, patched_object_data_repo, request, fxt_url_prefix, fxt_create_a_temp_file):
        """
        Test simple file upload
        """
        # arrange
        upload_data = b""
        upload_file = fxt_create_a_temp_file
        upload_file.write(upload_data)
        upload_file.seek(0)

        # act
        response = client.post(
            f"{fxt_url_prefix}/datasets/uploads",
            files={"file": ("my_file", upload_file, "application/octet-stream")},
        )
        response.json()

        # assert
        assert response.status_code == 400
        assert response.json()["message"].startswith("Could not upload a file")

    @patch(
        "communication.endpoints.upload_endpoints.check_free_space_for_upload",
        side_effect=NotEnoughSpaceGetiBaseException("no space left"),
    )
    def test_upload_file_no_space(self, patched_check_space, fxt_create_a_temp_file, fxt_url_prefix) -> None:
        """Test simple file upload under the error condition of insufficient space"""
        upload_data = b"Hello world!"
        upload_file = fxt_create_a_temp_file
        upload_file.write(upload_data)
        upload_file.seek(0)

        response = client.post(
            f"{fxt_url_prefix}/datasets/uploads",
            files={"file": ("my_file", upload_file, "application/octet-stream")},
        )

        assert response.status_code == 507

    def test_tus_options(self, fxt_url_prefix):
        """
        Test tus options endpoints and check that it returns correct headers
        """
        response = client.options(
            f"{fxt_url_prefix}/datasets/uploads/resumable",
        )
        assert response.status_code == 204
        assert dict(response.headers) == {
            "tus-resumable": "1.0.0",
            "tus-version": "1.0.0",
            "tus-extension": "creation",
        }

    @patch("application.file_object_management.ObjectDataRepo")
    def test_tus_upload(self, patched_object_data_repo, request, fxt_url_prefix, fxt_create_a_temp_file):
        """
        Upload using TUS, includes:
            - Create temporary file to upload and temp folder to use for storage on server
                side
            - POST: create file in server
            - HEAD: check that file exists in server with offset == 0
            - PATCH: append data to file in chunks using patch requests until file is
                fully uploaded
            - Check that file is correctly and fully uploaded to the server
        """
        object_data_repo = patched_object_data_repo.return_value
        object_data_repo.create_multi_upload_file.return_value = "dummy_upload_id"
        object_data_repo.upload_part_to_file.return_value = "dummy_etag"

        # arrange
        data_size = 2**14
        data = os.urandom(data_size)
        upload_file = fxt_create_a_temp_file
        upload_file.write(data)
        upload_file.seek(0)

        # tus creation
        headers = {"tus-resumable": "1.0.0", "upload-length": str(len(data))}
        response = client.post(
            f"{fxt_url_prefix}/datasets/uploads/resumable",
            headers=headers,
        )

        assert response.status_code == 201
        assert "location" in response.headers

        # initial tus head
        location = response.headers["location"]
        path = urlparse(location).path

        headers = {"tus-resumable": "1.0.0"}
        response = client.head(path, headers=headers)

        headers = dict(response.headers)
        assert response.status_code == 200
        assert headers["cache-content"] == "no-store"
        assert int(headers["upload-length"]) == len(data)
        assert int(headers["upload-offset"]) == 0

        # loop and patch chunks
        offset = 0
        chunk_size = int(data_size / 8)
        for _i in range(10):
            upload_file.seek(offset)
            data_to_upload = upload_file.read(chunk_size)
            if len(data_to_upload) == 0:
                break
            headers = {
                "tus-resumable": "1.0.0",
                "upload-offset": str(offset),
                "content-type": "application/offset+octet-stream",
            }
            response = client.patch(path, headers=headers, data=data_to_upload)
            offset = int(response.headers["upload-offset"])

        # assert upload successful
        file_id = path.split("/")[-1]
        self._assert_upload_completed(file_id, data)

    @patch("application.file_object_management.ObjectDataRepo")
    def test_tus_upload_cancel(self, patched_object_data_repo, request, fxt_url_prefix, fxt_create_a_temp_file):
        """
        Upload using TUS then cancel during, includes:
            - Create temporary file to upload and temp folder to use for storage on server
                side
            - POST: create file in server
            - HEAD: check that file exists in server with offset == 0
            - PATCH: append data to file in chunks using patch requests until file is
                fully uploaded
            - Check that file is correctly and fully uploaded to the server
        """
        object_data_repo = patched_object_data_repo.return_value
        object_data_repo.create_multi_upload_file.return_value = "dummy_upload_id"
        object_data_repo.upload_part_to_file.return_value = "dummy_etag"

        # arrange
        data_size = 2**14
        data = os.urandom(data_size)
        upload_file = fxt_create_a_temp_file
        upload_file.write(data)
        upload_file.seek(0)

        # tus creation
        headers = {"tus-resumable": "1.0.0", "upload-length": str(len(data))}
        response = client.post(
            f"{fxt_url_prefix}/datasets/uploads/resumable",
            headers=headers,
        )

        assert response.status_code == 201
        assert "location" in response.headers

        # initial tus head
        location = response.headers["location"]
        path = urlparse(location).path

        headers = {"tus-resumable": "1.0.0"}
        response = client.head(path, headers=headers)

        headers = dict(response.headers)
        assert response.status_code == 200
        assert headers["cache-content"] == "no-store"
        assert int(headers["upload-length"]) == len(data)
        assert int(headers["upload-offset"]) == 0

        # loop and patch chunks
        offset = 0
        chunk_size = int(data_size / 8)
        for _i in range(5):
            upload_file.seek(offset)
            data_to_upload = upload_file.read(chunk_size)
            if len(data_to_upload) == 0:
                break
            headers = {
                "tus-resumable": "1.0.0",
                "upload-offset": str(offset),
                "content-type": "application/offset+octet-stream",
            }
            response = client.patch(path, headers=headers, data=data_to_upload)
            offset = int(response.headers["upload-offset"])

        response = client.delete(
            path,
            headers=headers,
        )

        # assert upload cancellation successful
        file_id = path.split("/")[-1]
        assert response.status_code == 204

        metadata_repo = FileMetadataRepo()
        file_metadata = metadata_repo.get_by_id(file_id)
        assert file_metadata == NullFileMetadata()

    @patch(
        "communication.endpoints.upload_endpoints.check_free_space_for_upload",
        side_effect=NotEnoughSpaceGetiBaseException("no space left"),
    )
    def test_tus_upload_no_space(self, patched_check_space, fxt_url_prefix) -> None:
        """Test the TUS upload endpoint when the space is insufficient"""
        headers = {"tus-resumable": "1.0.0", "upload-length": "10"}

        response = client.post(
            f"{fxt_url_prefix}/datasets/uploads/resumable",
            headers=headers,
        )

        assert response.status_code == 507

    @patch("application.file_object_management.ObjectDataRepo")
    def test_tus_upload_zero_size(self, patched_object_data_repo, fxt_url_prefix):
        """
        Uploading using TUS with an incorrect file id returns 400
        """
        object_data_repo = patched_object_data_repo.return_value
        object_data_repo.create_multi_upload_file.return_value = "dummy_upload_id"

        # tus creation
        headers = {"tus-resumable": "1.0.0", "upload-length": "0"}
        response = client.post(
            f"{fxt_url_prefix}/datasets/uploads/resumable",
            headers=headers,
        )

        assert response.status_code == 400
        assert response.json()["message"].startswith("Could not upload a file")

        # tus creation
        headers = {"tus-resumable": "1.0.0", "upload-length": "10"}
        response = client.post(
            f"{fxt_url_prefix}/datasets/uploads/resumable",
            headers=headers,
        )

        assert response.status_code == 201
        assert "location" in response.headers

        location = response.headers["location"]
        path = urlparse(location).path
        # Make zero size patch
        headers = {
            "tus-resumable": "1.0.0",
            "upload-offset": "0",
            "content-type": "application/offset+octet-stream",
        }
        response = client.patch(path, headers=headers, data=b"")
        assert response.status_code == 400
        assert response.json()["message"].startswith("Could not upload a file")

    @patch("application.file_object_management.ObjectDataRepo")
    def test_tus_upload_wrong_id(self, patched_object_data_repo, fxt_url_prefix):
        """
        Uploading using TUS with an incorrect file id returns 400
        """
        object_data_repo = patched_object_data_repo.return_value
        object_data_repo.create_multi_upload_file.return_value = "dummy_upload_id"

        # tus creation
        headers = {"tus-resumable": "1.0.0", "upload-length": "10"}
        response = client.post(
            f"{fxt_url_prefix}/datasets/uploads/resumable",
            headers=headers,
        )

        assert response.status_code == 201
        assert "location" in response.headers

        # Make wrong path
        location = response.headers["location"]
        wrong_path = urlparse(location).path + "wrong_id"

        headers = {
            "tus-resumable": "1.0.0",
            "upload-offset": "10",
            "content-type": "application/offset+octet-stream",
        }
        response = client.patch(wrong_path, headers=headers, data=b"")
        assert response.status_code == 400
        assert response.json()["message"].startswith("Invalid request parameters: 'file_id'")

        headers = {"tus-resumable": "1.0.0"}
        response = client.head(wrong_path, headers=headers)
        assert response.status_code == 400
        # There's no document for describing client error for HEAD operation.

    @staticmethod
    def _assert_upload_completed(file_id: str, data: bytes):
        """
        assert file with file_id exists in the metadata_repo

        :param storage_path: path to directory where file is stored
        :param file_id: id of stored file
        :param data: the data to check the content of file against
        """

        metadata_repo = FileMetadataRepo()
        file_metadata = metadata_repo.get_by_id(ID(file_id))
        assert file_metadata.size == len(data)
