# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from typing import Any

from geti_types import ID
from iai_core.entities.dataset_storage import DatasetStorageIdentifier
from iai_core.entities.image import Image
from iai_core.entities.video import Video
from iai_core.repos import ImageRepo, VideoRepo
from iai_core.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo

logger = logging.getLogger(__name__)


class MediaPreprocessingStatusUseCase:
    @staticmethod
    def _update_preprocessing_status(media: Image | Video, event: str, preprocessing: dict[str, Any] | None) -> None:
        if event == "MEDIA_PREPROCESSING_STARTED":
            media.preprocessing.started()
        elif preprocessing is not None and preprocessing["success"]:
            media.preprocessing.finished()
        elif preprocessing is not None:
            media.preprocessing.failed(preprocessing.get("message", ""))

    @staticmethod
    def update_image_preprocessing_status(
        dataset_storage_identifier: DatasetStorageIdentifier,
        image_id: ID,
        event: str,
        preprocessing: dict | None,
    ) -> None:
        """
        Update image preprocessing status.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the dataset
        :param image_id: image ID
        :param event: preprocessing event, either MEDIA_PREPROCESSING_STARTED or MEDIA_PREPROCESSING_FINISHED
        :param preprocessing: preprocessing payload, flag if preprocessing was successful and failure message
        """
        image_repo = ImageRepo(dataset_storage_identifier=dataset_storage_identifier)
        image = image_repo.get_by_id(image_id)
        MediaPreprocessingStatusUseCase._update_preprocessing_status(
            media=image, event=event, preprocessing=preprocessing
        )
        image_repo.save(image)

        DatasetStorageFilterRepo(dataset_storage_identifier=dataset_storage_identifier).update_preprocessing_status(
            media_id=image.id_,
            status=image.preprocessing.status,
        )

    @staticmethod
    def update_video_preprocessing_status(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        event: str,
        preprocessing: dict | None,
    ) -> None:
        """
        Update video preprocessing status.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the dataset
        :param video_id: video ID
        :param event: preprocessing event, either MEDIA_PREPROCESSING_STARTED or MEDIA_PREPROCESSING_FINISHED
        :param preprocessing: preprocessing payload, flag if preprocessing was successful and failure message
        """
        video_repo = VideoRepo(dataset_storage_identifier=dataset_storage_identifier)
        video = video_repo.get_by_id(video_id)
        MediaPreprocessingStatusUseCase._update_preprocessing_status(
            media=video, event=event, preprocessing=preprocessing
        )
        video_repo.save(video)

        DatasetStorageFilterRepo(dataset_storage_identifier=dataset_storage_identifier).update_preprocessing_status(
            media_id=video.id_,
            status=video.preprocessing.status,
        )
