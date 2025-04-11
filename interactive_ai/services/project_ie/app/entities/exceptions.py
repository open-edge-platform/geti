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

"""Exceptions raised by Project I/E entities and services"""

import http

from geti_fastapi_tools.exceptions import GetiBaseException


class InvalidUploadFileType(GetiBaseException):
    """
    Exception raised when attempting to create an upload operation with an invalid file type

    :param file_type: the invalid file type
    """

    def __init__(self, file_type: str) -> None:
        super().__init__(
            message=f"Cannot create upload operation with file type: '{file_type}'",
            error_code="invalid_upload_file_type",
            http_status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )
