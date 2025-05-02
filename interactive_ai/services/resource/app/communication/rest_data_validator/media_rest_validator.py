# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the MediaRestValidator class"""

import json
import os
from typing import Annotated

from bson import ObjectId
from fastapi import Form, Request, UploadFile

from geti_fastapi_tools.exceptions import (
    BadRequestException,
    InvalidIDException,
    InvalidMediaException,
    PayloadTooLargeException,
)
from geti_fastapi_tools.validation import RestApiValidator
from iai_core.entities.media import ImageExtensions, VideoExtensions


class MediaRestValidator(RestApiValidator):
    SUPPORTED_IMAGE_TYPES = [extension.value for extension in ImageExtensions]
    SUPPORTED_VIDEO_TYPES = [extension.value for extension in VideoExtensions]
    MAX_BYTES_SIZE = 4.7 * 1024**3

    @staticmethod
    def validate_image_file(request: Request, file: UploadFile) -> UploadFile:
        """
        Validates a request to upload an image.

        :param request: FastAPI request that was made to upload the file
        :param file: uploaded image file
        :raises InvalidMediaException if the file name is empty or the file extension is
        not in the supported file extensions
        :raises PayloadTooLargeException when the total size of the request exceeds 8GB
        """
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
    def validate_video_file(request: Request, file: UploadFile) -> UploadFile:
        """
        Validates a request to upload a video.

        :param request: FastAPI request that was made to upload the file
        :param file: uploaded video file
        :raises BadRequestException if the file is not present
        :raises InvalidMediaException if the file name is empty or the file extension is
        not in the supported file extensions
        :raises PayloadTooLargeException when the total size of the request exceeds 8GB
        """
        file_size = file.size if file.size else int(request.headers["content-length"])
        if file_size > MediaRestValidator.MAX_BYTES_SIZE:
            raise PayloadTooLargeException(MediaRestValidator.MAX_BYTES_SIZE / (1024**2))

        if file.filename is None:
            raise InvalidMediaException("Filename can't be empty.")

        extension = list(os.path.splitext(file.filename)).pop().lower()
        if extension not in MediaRestValidator.SUPPORTED_VIDEO_TYPES:
            raise InvalidMediaException(
                f"Not a valid video format. Received {extension}, but only the following are allowed: "
                f"{str(MediaRestValidator.SUPPORTED_VIDEO_TYPES)}"
            )
        return file

    @staticmethod
    def validate_upload_info(upload_info: Annotated[str, Form()] = "{}") -> dict:
        """
        Validates the upload_info for an upload media request. upload_info must be a
        json-decodeable string of the format {"label_ids":[MONGO_ID,MONGO_ID]}

        :param upload_info: upload_info to be validated
        :raises NotImplementedError if the project is not a classification project, since
        uploading labels for non-classification projects is not currently allowed
        :raises BadRequestException if upload_info is not decodable, or if the string does
        not have the correct format
        """
        if upload_info == "{}":
            return {}

        try:
            upload_info_dict = json.loads(upload_info)
        except json.decoder.JSONDecodeError:
            raise BadRequestException("upload_info must be in json format.")
        if not isinstance(upload_info_dict, dict):
            raise BadRequestException(
                f"upload_info must be a dictionary in json format. "
                f"Received '{upload_info_dict}' of type {type(upload_info_dict)} instead."
            )

        label_ids = upload_info_dict.get("label_ids", [])
        if not isinstance(label_ids, list):
            raise BadRequestException("label_ids must be a list of well-formed MongoDB ObjectIDs.")
        for label_id in label_ids:
            if not ObjectId.is_valid(label_id):
                raise InvalidIDException(id_name="label_id", invalid_id=label_id)

        return upload_info_dict
