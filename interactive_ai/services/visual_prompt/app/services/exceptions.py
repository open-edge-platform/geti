# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
