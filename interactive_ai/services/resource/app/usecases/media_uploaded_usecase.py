# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from typing import Any

from geti_kafka_tools import publish_event
from geti_types import CTX_SESSION_VAR, ID
from iai_core.adapters.binary_interpreters import NumpyBinaryInterpreter
from iai_core.entities.dataset_storage import DatasetStorageIdentifier
from iai_core.entities.image import Image
from iai_core.entities.video import Video
from iai_core.repos.storage.binary_repos import ImageBinaryRepo, ThumbnailBinaryRepo, VideoBinaryRepo
from iai_core.utils.constants import DEFAULT_THUMBNAIL_SIZE
from iai_core.utils.media_factory import Media2DFactory
from media_utils import VideoDecoder, VideoFrameReader, generate_thumbnail_video

logger = logging.getLogger(__name__)


class MediaUploadedUseCase:
    @staticmethod
    def on_media_uploaded(
        dataset_storage_identifier: DatasetStorageIdentifier, media_type: str, media_id: ID, data_binary_filename: str
    ) -> None:
        MediaUploadedUseCase.publish_media_preprocessing_event(
            dataset_storage_identifier=dataset_storage_identifier,
            media_id=media_id,
            media_type=media_type,
            event="MEDIA_PREPROCESSING_STARTED",
        )

        try:
            if media_type == "IMAGE":
                MediaUploadedUseCase.on_image_uploaded(
                    dataset_storage_identifier=dataset_storage_identifier,
                    image_id=media_id,
                    data_binary_filename=data_binary_filename,
                )
            elif media_type == "VIDEO":
                MediaUploadedUseCase.on_video_uploaded(
                    dataset_storage_identifier=dataset_storage_identifier,
                    video_id=media_id,
                    data_binary_filename=data_binary_filename,
                )
            preprocessing: dict[str, Any] = {"success": True}
        except Exception as ex:
            preprocessing = {"success": False, "message": str(ex)}

        MediaUploadedUseCase.publish_media_preprocessing_event(
            dataset_storage_identifier=dataset_storage_identifier,
            media_id=media_id,
            media_type=media_type,
            event="MEDIA_PREPROCESSING_FINISHED",
            preprocessing=preprocessing,
        )

    @staticmethod
    def on_image_uploaded(
        dataset_storage_identifier: DatasetStorageIdentifier, image_id: ID, data_binary_filename: str
    ) -> None:
        """
        Handles image being uploaded. Creates and store image thumbnail

        :param dataset_storage_identifier: Identifier of the dataset storage containing the dataset
        :param image_id: image ID
        :param data_binary_filename: uploaded binary filename
        """
        image_numpy = ImageBinaryRepo(dataset_storage_identifier).get_by_filename(
            filename=data_binary_filename, binary_interpreter=NumpyBinaryInterpreter()
        )
        try:
            # Create a thumbnail for the image
            Media2DFactory.create_and_save_media_thumbnail(
                dataset_storage_identifier=dataset_storage_identifier,
                media_numpy=image_numpy,
                thumbnail_binary_filename=Image.thumbnail_filename_by_image_id(image_id),
            )
            logger.debug(f"Image {image_id} has been successfully preprocessed")
        except Exception as ex:
            logger.error(f"Error occurred while preprocessing image {image_id}", exc_info=ex)
            raise RuntimeError("Failed to preprocess image file") from ex

    @staticmethod
    def on_video_uploaded(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        data_binary_filename: str,
    ) -> None:
        """
        Handles video being uploaded. Creates and store video thumbnail, generates thumbnail video

        :param dataset_storage_identifier: Identifier of the dataset storage containing the dataset
        :param video_id: video ID
        :param data_binary_filename: uploaded binary filename
        """
        try:
            video_binary_repo = VideoBinaryRepo(dataset_storage_identifier)
            thumbnail_binary_repo = ThumbnailBinaryRepo(dataset_storage_identifier)
            url = video_binary_repo.get_path_or_presigned_url(filename=data_binary_filename)
            video_information = VideoDecoder.get_video_information(url)
            frame_index = video_information.total_frames // 2
            frame_numpy = VideoFrameReader.get_frame_numpy(
                file_location_getter=lambda: url,
                frame_index=frame_index,
            )
            cropped_numpy = Media2DFactory.crop_to_thumbnail(
                media_numpy=frame_numpy,
                target_height=DEFAULT_THUMBNAIL_SIZE,
                target_width=DEFAULT_THUMBNAIL_SIZE,
            )
            Media2DFactory.create_and_save_media_thumbnail(
                dataset_storage_identifier=dataset_storage_identifier,
                media_numpy=cropped_numpy,
                thumbnail_binary_filename=Video.thumbnail_filename_by_video_id(video_id),
            )

            tmp_thumbnail_video = thumbnail_binary_repo.create_path_for_temporary_file(
                filename=data_binary_filename, make_unique=False
            )
            generate_thumbnail_video(
                data_binary_url=url,
                thumbnail_video_path=tmp_thumbnail_video,
                video_width=video_information.width,
                video_height=video_information.height,
                default_thumbnail_size=DEFAULT_THUMBNAIL_SIZE,
            )
            thumbnail_binary_repo.save(
                data_source=tmp_thumbnail_video,
                remove_source=True,
                dst_file_name=Video.thumbnail_video_filename_by_video_id(video_id),
            )
            logger.debug(f"Video {video_id} has been successfully preprocessed")
        except Exception as ex:
            logger.error(f"Error occurred while preprocessing video {video_id}", exc_info=ex)
            raise RuntimeError("Failed to preprocess video file") from ex

    @staticmethod
    def publish_media_preprocessing_event(
        dataset_storage_identifier: DatasetStorageIdentifier,
        media_id: ID,
        media_type: str,
        event: str,
        preprocessing: dict | None = None,
    ) -> None:
        body: dict[str, Any] = {
            "project_id": str(dataset_storage_identifier.project_id),
            "dataset_storage_id": str(dataset_storage_identifier.dataset_storage_id),
            "media_id": str(media_id),
            "media_type": media_type,
            "event": event,
        }
        if preprocessing is not None:
            body["preprocessing"] = preprocessing
        publish_event(
            topic="media_preprocessing",
            body=body,
            key=str(media_id).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )
