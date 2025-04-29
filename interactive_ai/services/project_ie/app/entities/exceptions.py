# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
