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

"""Controller for project upload related requests"""

from starlette import status
from starlette.datastructures import URL
from starlette.responses import Response

from usecases import ProjectUploadUseCase

from geti_types import ID


class UploadController:
    """
    The upload controller interprets the information in users' requests, calls the relevant use-cases
    and eventually creates the HTTP response to return to the endpoint.
    """

    @staticmethod
    def get_options_response() -> Response:
        """
        Get information about the TUS protocol used by the server

        :return: Response with TUS info in the headers
        """
        response = Response(status_code=status.HTTP_204_NO_CONTENT)
        response.headers.update({"Tus-Resumable": "1.0.0", "Tus-Version": "1.0.0", "Tus-Extension": "creation"})
        return response

    @staticmethod
    def create_resumable_upload(upload_length: int, request_url: URL) -> Response:
        """
        Setup a resumable upload.

        Specifically, the method initializes the internal structures necessary to
        support the upload of a file with TUS.

        :param upload_length: Total bytes to be uploaded
        :param request_url: URL used by the user for the request
        :return: Response with information about the created multipart upload in the headers
        """
        operation_id = ProjectUploadUseCase.create_multipart_upload(upload_length=upload_length)
        location = f"{request_url.replace(scheme='https')}/{operation_id}"
        return Response(
            headers={"Location": location},
            status_code=status.HTTP_201_CREATED,
        )

    @staticmethod
    def get_resumable_upload_info(operation_id: ID) -> Response:
        """
        Get information about an existing multipart upload operation

        :param operation_id: Operation ID for the multipart upload operation
        :return: Response with information about the multipart upload in the headers
        """
        size, offset = ProjectUploadUseCase.get_multipart_upload_info(operation_id=operation_id)
        return Response(
            headers={
                "Upload-Length": str(size),
                "Upload-Offset": str(offset),
                "Cache-Content": "no-store",
            },
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @staticmethod
    def append_to_multipart_upload(operation_id: ID, offset: int, data: bytes) -> Response:
        """
        Append bytes to an existing multipart upload

        :param operation_id: ID of the multipart upload operation
        :param offset: Number of bytes present in the file before adding the new part
        :param data: Bytes to be appended to the upload
        :return: Response with information about the multipart upload in the headers
        """
        new_offset = ProjectUploadUseCase.append_to_multipart_upload(
            operation_id=operation_id, offset=offset, data=data
        )
        return Response(
            headers={"Upload-Offset": str(new_offset)},
            status_code=status.HTTP_204_NO_CONTENT,
        )
