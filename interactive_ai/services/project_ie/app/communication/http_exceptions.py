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
This module defines exceptions that are linked to a HTTP response code and can be
returned to the user by the REST API.
"""

import http

from geti_fastapi_tools.exceptions import GetiBaseException


class InvalidOperationIdException(GetiBaseException):
    """Exception raised when the id of the import/export operation is malformed or invalid"""

    def __init__(self, operation_id: str) -> None:
        super().__init__(
            message=f"Invalid import/export operation id: {operation_id}",
            error_code="invalid_ie_operation_id",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class UnsupportedMediaTypeException(GetiBaseException):
    """Exception raised when the user uploads media of an incorrect type"""

    def __init__(self, received_type: str, expected_type: str) -> None:
        message = f"Unsupported media type received '{received_type}, expected '{expected_type}'"
        super().__init__(
            message=message,
            error_code="unsupported_media_type",
            http_status=http.HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        )


class UnsupportedTUSVersionException(GetiBaseException):
    """
    Raised when the user uses a TUS version that is not supported
    """

    def __init__(self, received_version: str, expected_versions: str) -> None:
        message = (
            f"Version of tus used by client: '{received_version}' is not in the list of versions"
            f"supported by server: '{expected_versions}'"
        )
        super().__init__(
            message=message,
            error_code="unsupported_tus_version",
            http_status=http.HTTPStatus.PRECONDITION_FAILED,
        )


class FailedArchiveDownloadException(GetiBaseException):
    """Raised when the project archive cannot be downloaded due to an internal error"""

    def __init__(self) -> None:
        super().__init__(
            message="The exported project archive cannot be downloaded due to an internal error",
            error_code="download_failed",
            http_status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class FailedJobSubmissionException(GetiBaseException):
    """Exception raised when a problem occurs while submitting a job to the jobs client"""

    def __init__(self) -> None:
        super().__init__(
            message="Could not submit job due to temporary unavailable server: try again later",
            error_code="job_submission_failed",
            http_status=http.HTTPStatus.SERVICE_UNAVAILABLE,
        )


class PayloadTooLargeException(GetiBaseException):
    """
    Exception raised when the request payload is too large.

    :param max_size: Max size in bytes
    """

    def __init__(self, max_size: float) -> None:
        super().__init__(
            message=f"Request too large: exceeding {max_size / (2**20)} MB is not allowed.",
            error_code="payload_too_large",
            http_status=http.HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )


class MaxProjectsReachedException(GetiBaseException):
    """
    Exception to indicate the maximum number of projects have been reached
    """

    def __init__(self, maximum: int) -> None:
        super().__init__(
            message=f"You have hit the limit of number of projects in your organization "
            f"({maximum}). Please delete some projects before making new ones.",
            error_code="limit_reached",
            http_status=http.HTTPStatus.CONFLICT,
        )
