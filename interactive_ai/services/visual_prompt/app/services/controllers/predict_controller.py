# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os
from typing import Any

import numpy as np
from fastapi import Request, UploadFile

from entities.exceptions import InferenceMediaNotFound, MissingInputMediaException
from services.models.media_info_payload import MediaInfoPayload
from services.rest_views.prediction_rest_views import PredictionRESTViews

from geti_fastapi_tools.exceptions import InvalidMediaException
from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity, ProjectIdentifier
from iai_core_py.adapters.binary_interpreters import NumpyBinaryInterpreter
from iai_core_py.entities.image import Image, NullImage
from iai_core_py.entities.video import NullVideo, VideoFrame
from iai_core_py.repos import ImageRepo, VideoRepo
from media_utils import get_media_numpy

logger = logging.getLogger(__name__)


class PredictController:
    """
    The predict controller class is responsible for handling the visual prompt predict requests.
    """

    @classmethod
    def predict(
        cls,
        request: Request,
        project_identifier: ProjectIdentifier,
        task_id: ID,
        media_info_payload: MediaInfoPayload | None = None,
        file: UploadFile | None = None,
    ) -> dict[str, Any]:
        """
        Predicts on a media via the visual prompt service and returns the REST representation of the inference results.

        :param request: FastAPI request object.
        :param project_identifier: The project identifier.
        :param task_id: The task to predict.
        :param media_info_payload: The media information payload.
        :param file: The uploaded image file to predict on.
        :return: REST representation of the VPS predictions.
        """
        numpy_data, media_identifier = cls._get_numpy_data(
            project_identifier=project_identifier, media_info_payload=media_info_payload, file=file
        )

        prediction_results = request.app.visual_prompt_service.infer(
            project_identifier=project_identifier, task_id=task_id, media=numpy_data
        )
        return PredictionRESTViews.predictions_results_to_rest(
            prediction_results=prediction_results,
            media_identifier=media_identifier,
            media_width=numpy_data.shape[1],
            media_height=numpy_data.shape[0],
        )

    @classmethod
    def _get_numpy_data(
        cls,
        project_identifier: ProjectIdentifier,
        media_info_payload: MediaInfoPayload | None,
        file: UploadFile | None = None,
    ) -> tuple[np.ndarray, MediaIdentifierEntity | None]:
        """
        Gets the media from the media user's provided media info payload.

        :param project_identifier: The project identifier.
        :param media_info_payload: The media information payload.
        :return: Image or VideoFrame entity.
        """
        if file is not None and file.filename:
            logger.info(f"Received request for image `{file.filename}`")
            image_binary = cls._read_bytes_from_upload_file(file_from_request=file)
            ext = str(os.path.splitext(file.filename)[1]).lower()
            return NumpyBinaryInterpreter.read_image_from_bytes(extension=ext, data=image_binary), None
        if media_info_payload is not None:
            logger.info(f"Received request for media `{media_info_payload}`")
            dataset_storage_identifier = DatasetStorageIdentifier(
                workspace_id=project_identifier.workspace_id,
                project_id=project_identifier.project_id,
                dataset_storage_id=ID(media_info_payload.dataset_storage_id),
            )
            return cls._get_media(
                dataset_storage_identifier=dataset_storage_identifier, media_info_payload=media_info_payload
            )
        raise MissingInputMediaException

    @staticmethod
    def _get_media(
        dataset_storage_identifier: DatasetStorageIdentifier, media_info_payload: MediaInfoPayload
    ) -> tuple[np.ndarray, MediaIdentifierEntity | None]:
        """
        Gets the media from the media user's provided media info payload.

        :param dataset_storage_identifier: The dataset storage identifier containing the media.
        :param media_info_payload: The media information payload.
        :return: Image or VideoFrame numpy array and media identifier.
        """
        media: Image | VideoFrame | None = None
        if media_info_payload.image_id is not None:
            image = ImageRepo(dataset_storage_identifier).get_by_id(ID(media_info_payload.image_id))
            if image is not None and not isinstance(image, NullImage):
                media = image
        if media_info_payload.video_id is not None and media_info_payload.frame_index is not None:
            video = VideoRepo(dataset_storage_identifier).get_by_id(ID(media_info_payload.video_id))
            if video is not None and not isinstance(video, NullVideo):
                media = VideoFrame(video=video, frame_index=media_info_payload.frame_index)
        if media is None:
            logger.warning(f"Media not found for media_info_payload: {media_info_payload}")
            raise InferenceMediaNotFound
        return get_media_numpy(
            dataset_storage_identifier=dataset_storage_identifier, media=media
        ), media.media_identifier

    @staticmethod
    def _read_bytes_from_upload_file(file_from_request: UploadFile) -> bytes:
        """
        Read bytes from an upload file

        :param file_from_request: UploadFile object
        :return: bytes
        """
        filename = file_from_request.filename
        try:
            file_from_request.file.seek(0)  # rewind cursor to the start of the file
            data = file_from_request.file.read()
            if not data:
                logger.warning(
                    f"Cannot read any data from the file: '{file_from_request.file}'. Data content: {data!r}"
                )
                raise InvalidMediaException(
                    f"Failed to upload the image '{filename}'. "
                    f"Cannot read any data from the file, it appears to be empty."
                )
        except InvalidMediaException as err:
            raise err
        except Exception as err:
            logger.exception(f"Failed to read file '{file_from_request.file}' due to unexpected error.")
            raise InvalidMediaException(f"Failed to upload the image '{filename}'. ") from err
        finally:
            file_from_request.file.close()
        return data
