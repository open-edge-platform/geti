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

import http

from geti_fastapi_tools.exceptions import GetiBaseException


class InferenceMediaNotFound(GetiBaseException):
    """
    Exception raised when attempting to run inference, but the media (image or video frame) is not found
    """

    def __init__(self) -> None:
        super().__init__(
            message="Cannot find media for inference. Please check the image or video ID and try again.",
            error_code="media_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class MissingInputMediaException(GetiBaseException):
    """
    Exception raised when neither binary file nor media_info_payload is provided for inference.
    """

    def __init__(self) -> None:
        super().__init__(
            message="Neither file nor media_info_payload is provided. Please provide at least one.",
            error_code="missing_input_media",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )
