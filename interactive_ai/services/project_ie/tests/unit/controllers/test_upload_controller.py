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
from unittest.mock import patch

import pytest
from starlette import status
from starlette.datastructures import URL
from starlette.responses import Response

from communication.controllers.upload_controller import UploadController
from usecases import ProjectUploadUseCase


@pytest.mark.ProjectIEMsComponent
class TestUploadController:
    def test_get_options_response(self):
        expected_response = Response(status_code=status.HTTP_204_NO_CONTENT)
        expected_response.headers.update(
            {"Tus-Resumable": "1.0.0", "Tus-Version": "1.0.0", "Tus-Extension": "creation"}
        )

        response = UploadController.get_options_response()

        assert response.headers == expected_response.headers
        assert response.body == expected_response.body
        assert response.status_code == expected_response.status_code

    def test_create_resumable_upload(self, fxt_mongo_id):
        operation_id = fxt_mongo_id(1)
        request_url = URL("dummy_url")
        upload_length = 100
        expected_response = Response(
            headers={"Location": f"{request_url.replace(scheme='https')}/{operation_id}"},
            status_code=status.HTTP_201_CREATED,
        )
        with patch.object(
            ProjectUploadUseCase, "create_multipart_upload", return_value=operation_id
        ) as mock_create_upload:
            response = UploadController.create_resumable_upload(upload_length=upload_length, request_url=request_url)

        mock_create_upload.assert_called_once_with(upload_length=upload_length)
        assert response.headers == expected_response.headers
        assert response.body == expected_response.body
        assert response.status_code == expected_response.status_code

    def test_get_resumable_upload_info(self, fxt_mongo_id):
        operation_id = fxt_mongo_id(1)
        mock_size = 100
        mock_offset = 50
        expected_response = Response(
            headers={
                "Upload-Length": str(mock_size),
                "Upload-Offset": str(mock_offset),
                "Cache-Content": "no-store",
            },
            status_code=status.HTTP_204_NO_CONTENT,
        )
        with patch.object(
            ProjectUploadUseCase, "get_multipart_upload_info", return_value=(mock_size, mock_offset)
        ) as mock_get_info:
            response = UploadController.get_resumable_upload_info(operation_id=operation_id)

        mock_get_info.assert_called_once_with(operation_id=operation_id)
        assert response.headers == expected_response.headers
        assert response.body == expected_response.body
        assert response.status_code == expected_response.status_code

    def test_append_to_multipart_upload(self, fxt_mongo_id):
        operation_id = fxt_mongo_id(1)
        mock_offset = 50
        mock_data = b""
        expected_response = Response(
            headers={"Upload-Offset": str(mock_offset)},
            status_code=status.HTTP_204_NO_CONTENT,
        )
        with patch.object(
            ProjectUploadUseCase, "append_to_multipart_upload", return_value=mock_offset + len(mock_data)
        ) as mock_append:
            response = UploadController.append_to_multipart_upload(
                operation_id=operation_id, offset=mock_offset, data=mock_data
            )

        mock_append.assert_called_once_with(operation_id=operation_id, offset=mock_offset, data=mock_data)
        assert response.headers == expected_response.headers
        assert response.body == expected_response.body
        assert response.status_code == expected_response.status_code
