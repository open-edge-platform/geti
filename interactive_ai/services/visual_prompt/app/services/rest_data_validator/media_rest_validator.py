# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os

from fastapi import Depends, File, Request, UploadFile

from services.models.media_info_payload import MediaInfoPayload

from geti_fastapi_tools.dependencies import get_optional_request_json
from geti_fastapi_tools.exceptions import InvalidMediaException, PayloadTooLargeException
from geti_fastapi_tools.validation import RestApiValidator
from iai_core_py.entities.media import ImageExtensions


class MediaRestValidator(RestApiValidator):
    SUPPORTED_IMAGE_TYPES = [extension.value for extension in ImageExtensions]
    MAX_BYTES_SIZE = 4.7 * 1024**3

    @staticmethod
    def validate_image_file(request: Request, file: UploadFile = File(None)) -> UploadFile | None:
        """
        Validates a request to upload an image, if the file is not present, returns None.

        :param request: FastAPI request that was made to upload the file
        :param file: uploaded image file
        :raises InvalidMediaException if the file name is empty or the file extension is
        not in the supported file extensions
        :raises PayloadTooLargeException when the total size of the request exceeds 8GB
        """
        if file is None:
            return None

        file_size = file.size if file.size else int(request.headers["content-length"])
        if file_size > MediaRestValidator.MAX_BYTES_SIZE:
            raise PayloadTooLargeException(MediaRestValidator.MAX_BYTES_SIZE / (1024**2))

        if file.filename is None:
            raise InvalidMediaException("Filename can't be empty.")

        extension = list(os.path.splitext(file.filename)).pop().lower()
        if extension not in MediaRestValidator.SUPPORTED_IMAGE_TYPES:
            raise InvalidMediaException(
                f"Not a valid image format. Received {extension}, but only the following are allowed: "
                f"{str(MediaRestValidator.SUPPORTED_IMAGE_TYPES)}"
            )
        return file

    @staticmethod
    def validate_media_info_payload(
        json_body: dict | None = Depends(get_optional_request_json),
    ) -> MediaInfoPayload | None:
        """
        Validates the media info payload.

        :param json_body: The JSON body of the request.
        :return: MediaInfoPayload object if the JSON body is valid, None otherwise
        """
        if json_body is None:
            return None

        dataset_storage_id = json_body.get("dataset_id")
        if dataset_storage_id is None:
            raise ValueError("Dataset ID must be provided")

        media_info_payload = MediaInfoPayload(
            dataset_storage_id=dataset_storage_id,
            image_id=json_body.get("image_id"),
            video_id=json_body.get("video_id"),
            frame_index=json_body.get("frame_index"),
        )

        if media_info_payload.image_id is not None and (
            media_info_payload.video_id is not None or media_info_payload.frame_index is not None
        ):
            raise ValueError("Only image or video frame can be provided, not both")

        if media_info_payload.image_id is None:
            if media_info_payload.video_id is None or media_info_payload.frame_index is None:
                raise ValueError("Either image or video frame must be provided")
            if media_info_payload.frame_index < 0:
                raise ValueError("Frame index must be non-negative")

        return media_info_payload
