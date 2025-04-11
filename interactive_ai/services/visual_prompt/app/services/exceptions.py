# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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
from geti_types import ID


class ImageNotFoundException(GetiBaseException):
    """
    Exception raised when image could not be found in database.

    :param image_id: ID of the image
    :param dataset_storage_id: ID of the DatasetStorage
    """

    def __init__(self, image_id: ID, dataset_storage_id: ID) -> None:
        super().__init__(
            message=(
                f"The requested image could not be found in this dataset. "
                f"Dataset Storage ID: `{dataset_storage_id}`, "
                f"Image ID: `{image_id}`. "
            ),
            error_code="image_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class VideoNotFoundException(GetiBaseException):
    """
    Exception raised when video could not be found in database.

    :param video_id: ID of the video
    :param dataset_storage_id: ID of the dataset_storage
    """

    def __init__(self, video_id: ID, dataset_storage_id: ID) -> None:
        super().__init__(
            message=(
                f"The requested video could not be found in this dataset. "
                f"Dataset Storage ID: `{dataset_storage_id}`, "
                f"Video ID: `{video_id}'. "
            ),
            error_code="video_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )
