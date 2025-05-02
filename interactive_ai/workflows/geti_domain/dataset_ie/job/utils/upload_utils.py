# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements upload utilities
"""

import abc
import datetime
import logging
import os.path as osp
from collections.abc import Callable
from typing import Any, cast

import cv2
import numpy as np
from datumaro import DatasetItem as dm_DatasetItem
from datumaro import Label as dm_Label
from geti_kafka_tools import publish_event
from geti_telemetry_tools import ENABLE_METRICS
from geti_telemetry_tools.metrics import (
    EmptyInstrumentAttributes,
    convert_pixels,
    images_resolution_histogram,
    videos_frames_histogram,
    videos_resolution_histogram,
)
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, MediaIdentifierEntity
from iai_core.adapters.binary_interpreters import NumpyBinaryInterpreter
from iai_core.entities.annotation import AnnotationScene
from iai_core.entities.image import Image
from iai_core.entities.label import Label, NullLabel
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core.entities.project import Project
from iai_core.entities.video import NullVideo, Video
from iai_core.entities.video_annotation_range import RangeLabels
from iai_core.repos import AnnotationSceneRepo, AnnotationSceneStateRepo, ImageRepo, VideoRepo
from iai_core.repos.storage.binary_repos import ImageBinaryRepo, VideoBinaryRepo
from iai_core.services.dataset_storage_filter_service import DatasetStorageFilterService
from iai_core.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core.utils.media_factory import Media2DFactory
from jobs_common_extras.datumaro_conversion.convert_utils import ConvertUtils, MediaInfo
from media_utils import VideoFrameOutOfRangeInternalException, VideoFrameReader

from job.utils.constants import (
    MAX_IMAGE_SIZE,
    MAX_NUMBER_OF_PIXELS,
    MAX_VIDEO_HEIGHT,
    MAX_VIDEO_LENGTH,
    MAX_VIDEO_WIDTH,
    MIN_IMAGE_SIZE,
    MIN_VIDEO_SIZE,
)
from job.utils.exceptions import FileNotFoundException, InvalidMediaException

logger = logging.getLogger(__name__)


class UploadManager(metaclass=abc.ABCMeta):
    """This interface represents the media/annotations uploader."""

    def __init__(self, dataset_storage_identifier: DatasetStorageIdentifier, uploader_id: str):
        self._dataset_storage_identifier = dataset_storage_identifier
        self._uploader_id = uploader_id

    def _publish_media_upload_message(
        self,
        media_identifier: MediaIdentifierEntity,
    ) -> None:
        """
        Publish media uploaded message

        :param media_identifier: The media identifier belonging to the uploaded media
        """
        body = {
            "workspace_id": str(self._dataset_storage_identifier.workspace_id),
            "project_id": str(self._dataset_storage_identifier.project_id),
            "dataset_storage_id": str(self._dataset_storage_identifier.dataset_storage_id),
            "media_id": str(media_identifier.media_id),
            "media_type": media_identifier.media_type.value,
        }
        publish_event(
            topic="media_uploads",
            body=body,
            key=str(media_identifier.media_id).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

    @abc.abstractmethod
    def upload(self, *args, **kwargs) -> Any:
        pass

    @abc.abstractmethod
    def __len__(self):
        pass

    def _process_on_new_media_upload(self, media_identifier: MediaIdentifierEntity) -> None:
        DatasetStorageFilterService.on_new_media_upload(
            workspace_id=self._dataset_storage_identifier.workspace_id,
            project_id=self._dataset_storage_identifier.project_id,
            dataset_storage_id=self._dataset_storage_identifier.dataset_storage_id,
            media_id=media_identifier.media_id,
            media_type=media_identifier.media_type,
        )
        self._publish_media_upload_message(media_identifier=media_identifier)


class ImageUploadManager(UploadManager):
    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        uploader_id: str,
        get_image_name: Callable,
    ):
        """
        ImageUploadManager converts dm_DatasetItem to Image and saves it to ImageRepo.

        :param dataset_storage_identifier: The identifier of the target dataset storage.
        :param uploader_id: ID of the user who uploaded.
        :param get_image_name: Function to get image name of converted image.
        """
        super().__init__(
            dataset_storage_identifier=dataset_storage_identifier,
            uploader_id=uploader_id,
        )
        self._dataset_storage_identifier = dataset_storage_identifier
        self._image_repo = ImageRepo(dataset_storage_identifier=dataset_storage_identifier)
        self._image_binary_repo = ImageBinaryRepo(identifier=dataset_storage_identifier)
        self._get_image_name = get_image_name
        self._image_paths: set[str] = set()

    def upload(self, dm_item: dm_DatasetItem) -> MediaInfo | None:
        """
        Convert and validate dm_item into SC Image and upload it to ImageRepo.

        :param dm_item: Datumaro dataset item containing an image.
        :return: Media information of uploaded image.
        """
        image_path = getattr(dm_item.media, "path", None)
        # TODO: Check if this is intended or not.
        # Even if the image_path is the same, annotations can be merged, but here just skipping.
        if image_path is not None and image_path in self._image_paths:
            return None

        try:
            numpy, image_extension = ConvertUtils.get_image_from_dm_item(dm_item=dm_item)
        except Exception as e:
            logger.exception(msg=f"Cannot read numpy data of an image with an error, {str(e)}")

            raise InvalidMediaException(
                f"Cannot upload image `{osp.basename(image_path) if image_path else ''}`."
                " The server was not able to interpret it."
            )

        error_messages = self._validate_image_dimensions(width=numpy.shape[1], height=numpy.shape[0])
        if error_messages:
            raise InvalidMediaException(" ".join(error_messages))

        image_binary_repo = ImageBinaryRepo(self._dataset_storage_identifier)
        image_id = ImageRepo.generate_id()
        binary_filename = None
        try:
            # Store binary file
            filename = f"{str(image_id)}{image_extension.value}"
            binary_filename = image_binary_repo.save(
                dst_file_name=filename,
                data_source=NumpyBinaryInterpreter.get_bytes_from_numpy(numpy, image_extension.value),
            )
            size = image_binary_repo.get_object_size(binary_filename)

            image = Image(
                name=self._get_image_name(dm_item),
                uploader_id=self._uploader_id,
                extension=image_extension,
                id=image_id,
                width=numpy.shape[1],
                height=numpy.shape[0],
                size=size,
                preprocessing=MediaPreprocessing(
                    status=MediaPreprocessingStatus.IN_PROGRESS,
                    start_timestamp=datetime.datetime.now(),
                ),
            )
            self._image_repo.save(image)
        except Exception:
            # In case of error, delete any binary file that was already stored
            logger.exception(
                "Error saving image `%s` to `%s`; associated binaries will be removed",
                image_id,
                self._dataset_storage_identifier,
            )
            if binary_filename is not None:
                image_binary_repo.delete_by_filename(binary_filename)
            raise

        Media2DFactory.create_and_save_media_thumbnail(
            dataset_storage_identifier=self._dataset_storage_identifier,
            media_numpy=cv2.cvtColor(numpy, cv2.COLOR_BGR2RGB),
            thumbnail_binary_filename=image.thumbnail_filename,
        )

        image.preprocessing.finished()
        self._image_repo.save(image)

        self._update_image_metrics(image=image)
        self._process_on_new_media_upload(media_identifier=image.media_identifier)

        if image_path:
            self._image_paths.add(image_path)

        return MediaInfo(image.media_identifier, image.height, image.width)

    @staticmethod
    def _validate_image_dimensions(width: int, height: int) -> list[str]:
        """
        Validates that the image does not exceed the minimum/maximum allowed dimensions, or the maximum number of pixels
        """
        error_messages = []
        is_too_small = height < MIN_IMAGE_SIZE or width < MIN_IMAGE_SIZE
        is_too_large = height > MAX_IMAGE_SIZE or width > MAX_IMAGE_SIZE

        if is_too_small or is_too_large:
            error_messages.append(
                f"Invalid image dimensions. Image width and height have to be within the range of "
                f"{MIN_IMAGE_SIZE} to {MAX_IMAGE_SIZE} pixels."
            )

        if MAX_NUMBER_OF_PIXELS and height * width > MAX_NUMBER_OF_PIXELS:
            error_messages.append(f"The maximum number of pixels is {MAX_NUMBER_OF_PIXELS}.")

        return error_messages

    @staticmethod
    def _update_image_metrics(image: Image) -> None:
        """
        Update metrics relative to images:
          - resolution histogram

        :param image: Uploaded image
        """
        if not ENABLE_METRICS:
            return

        # Compute the size of the image in the unit required by the instrument
        image_resolution = convert_pixels(
            num_pixels=(image.width * image.height),
            unit=images_resolution_histogram.unit,  # type: ignore
        )
        # Record data point
        images_resolution_histogram.record(image_resolution, EmptyInstrumentAttributes().to_dict())

    def __len__(self):
        return len(self._image_paths)


class VideoUploadManager(UploadManager):
    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        uploader_id: str,
        get_video_name: Callable,
    ):
        """
        VideoUploadManager converts dm_DatasetItem to Video and saves it to VideoRepo.

        :param dataset_storage_identifier: The identifier of the target dataset storage.
        :param uploader_id: ID of the user who uploaded.
        :param get_video_name: Function to get video name of converted video
        """
        super().__init__(
            dataset_storage_identifier=dataset_storage_identifier,
            uploader_id=uploader_id,
        )
        self._video_repo = VideoRepo(dataset_storage_identifier=dataset_storage_identifier)
        self._get_video_name = get_video_name
        self._video_paths: dict[str, ID] = {}

    def get_video_id(self, video_path: str) -> ID | None:
        return self._video_paths.get(video_path, None)

    def upload(self, dm_item: dm_DatasetItem) -> Video:
        """
        Convert and validate dm_item into SC Video and upload it to VideoRepo if it hasn't uploaded.

        :param dm_item: Datumaro dataset item containing a VideoFrame.
        :return: Uploaded video.
        """
        video_path = getattr(dm_item.media, "path", None)
        if not video_path:
            logger.warning(f"Skip dm item with media type '{dm_item.media.type.name}' because media.path is None.")
            return NullVideo()

        video_id = self.get_video_id(video_path)
        if video_id is not None:
            video = self._video_repo.get_by_id(video_id)
        else:
            video = self._validate_and_upload_video(dm_item=dm_item)
            self._video_paths[video_path] = video.id_

        return video

    def _validate_and_upload_video(self, dm_item: dm_DatasetItem) -> Video:
        video_binary_repo = self._video_repo.binary_repo

        try:
            video = ConvertUtils.get_video_from_dm_item(
                dm_item=dm_item,
                get_video_name=self._get_video_name,
                uploader_id=self._uploader_id,
                video_binary_repo=video_binary_repo,
            )
        except Exception as e:
            error_message = f"Video file from `{osp.basename(dm_item.media.path)}` could not be read"
            logger.exception(msg=f"{error_message} with an error, {str(e)}")
            raise InvalidMediaException(f"{error_message}.")

        # Should we check VideoFileRepair.check_and_repair_video?
        # No. Most of the Datumaro datasets come from Geti, with videos that were
        # already validated on upload. The risk of broken videos on dataset import is low.

        error_messages = self._validate_video_data(video.id_, video)
        if error_messages:
            video_binary_repo.delete_by_filename(filename=video.data_binary_filename)
            raise InvalidMediaException(" ".join(error_messages))

        video.preprocessing = MediaPreprocessing(
            status=MediaPreprocessingStatus.IN_PROGRESS,
            start_timestamp=datetime.datetime.now(),
        )
        self._video_repo.save(video)
        logger.info(
            "Uploaded video '%s' with video_path '%s' to dataset storage '%s'",
            dm_item.media.path,
            video.data_binary_filename,
            self._dataset_storage_identifier,
        )

        video_numpy = self._get_video_frame_thumbnail_numpy(video=video)
        Media2DFactory.create_and_save_media_thumbnail(
            dataset_storage_identifier=self._dataset_storage_identifier,
            media_numpy=video_numpy,
            thumbnail_binary_filename=video.thumbnail_filename,
        )
        logger.info(
            "Created thumbnail for video `%s` (ID `%s`) in dataset storage `%s`",
            video.name,
            video.id_,
            self._dataset_storage_identifier,
        )

        video.preprocessing.finished()
        self._video_repo.save(video)

        self._update_video_metrics(video=video)
        self._process_on_new_media_upload(media_identifier=video.media_identifier)

        logger.debug(
            "Uploaded video '%s' to filename %s in dataset storage '%s'",
            dm_item.media.path,
            video.data_binary_filename,
            self._dataset_storage_identifier,
        )

        return video

    @staticmethod
    def _validate_video_data(video_id: ID, video: Video) -> list[str]:
        error_messages = []
        if video.total_frames == 0:
            error_messages.append(
                f"Encountered an error while decoding video with ID '{video_id}'. Unable to extract frames from video."
            )
        if (
            video.width > MAX_VIDEO_WIDTH
            or video.height > MAX_VIDEO_HEIGHT
            or video.width < MIN_VIDEO_SIZE
            or video.height < MIN_VIDEO_SIZE
        ):
            error_messages.append(
                "Video too small or too large: The supported video dimensions range "
                f"from {MIN_VIDEO_SIZE}x{MIN_VIDEO_SIZE} to "
                f"{MAX_VIDEO_WIDTH}x{MAX_VIDEO_HEIGHT} pixels. "
                "However, the dimensions extracted for this video are: "
                f"{video.width}x{video.height}"
            )
        if video.duration > MAX_VIDEO_LENGTH:
            error_messages.append(f"Video too long: the maximum duration is {MAX_VIDEO_LENGTH // 3600} hours")
        return error_messages

    def _get_video_frame_thumbnail_numpy(
        self,
        video: Video,
        frame_index: int | None = None,
    ) -> np.ndarray:
        """
        Fetch a video frame from the repo and crop it to a thumbnail

        :param dataset_storage_identifier: The identifier of the target dataset storage.
        :param video: The SC video instance.
        :param frame_index: Index of the video frame in the video.
        :return: numpy array that is a RGB representation of the video frame thumbnail
        """
        if frame_index is None:
            frame_index = video.total_frames // 2
        try:
            video_binary_repo = VideoBinaryRepo(self._dataset_storage_identifier)
            frame_numpy = VideoFrameReader.get_frame_numpy(
                file_location_getter=lambda: str(
                    video_binary_repo.get_path_or_presigned_url(video.data_binary_filename)
                ),
                frame_index=frame_index,
            )
        except FileNotFoundError:
            raise FileNotFoundException(
                f"Attempted to fetch video frame data for frame {str(frame_index)} of the video "
                f"with ID `{str(video.id_)}`, but the data was not present in the repository."
            )
        except VideoFrameOutOfRangeInternalException:
            raise InvalidMediaException(
                f"Requested video frame with frame_index {str(frame_index)} is out of range for "
                f"video with {video.total_frames} frames. Video ID: {str(video.id_)}."
            )
        return frame_numpy

    @staticmethod
    def _update_video_metrics(video: Video) -> None:
        """
        Update metrics relative to videos:
          - resolution histogram
          - frame histogram

        :param video: Uploaded video
        """
        if not ENABLE_METRICS:
            return
        # Compute the size of the video in the unit required by the instrument
        video_resolution = convert_pixels(
            num_pixels=(video.width * video.height),
            unit=videos_resolution_histogram.unit,  # type: ignore
        )
        # Record data point
        videos_resolution_histogram.record(video_resolution, EmptyInstrumentAttributes().to_dict())
        videos_frames_histogram.record(video.total_frames, EmptyInstrumentAttributes().to_dict())

    def __len__(self):
        return len(self._video_paths)


class AnnotationUploadManager(UploadManager):
    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        uploader_id: str,
        project: Project,
        label_schema: LabelSchema,
        get_sc_label: Callable,
        sc_label_to_all_parents: dict[Label, list[Label]] | None = None,
    ):
        """
        AnnotationUploadManager converts dm_DatasetItem to AnnotationScene and saves it to AnnotationSceneRepo.

        :param dataset_storage_identifier: The identifier of the target dataset storage.
        :param uploader_id: ID of the user who uploaded.
        :param project: Project to populate annotation scenes.
        :param label_schema: Label schema of the project.
        :param get_sc_label: Method used to get SC label from datumaro label name.
        :param sc_label_to_all_parents: Optional. Dictionary of mapping sc_label to all ancestor labels.
        """
        super().__init__(
            dataset_storage_identifier=dataset_storage_identifier,
            uploader_id=uploader_id,
        )
        self._ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier=dataset_storage_identifier)
        self._ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier=dataset_storage_identifier)
        self._project = project
        self._get_sc_label = get_sc_label
        self._empty_labels = cast("list[Label]", label_schema.get_empty_labels())
        self._sc_label_to_all_parents = sc_label_to_all_parents
        self._sc_label_to_group_id = ConvertUtils.get_sc_label_to_group_id(label_schema=label_schema)
        self._num_annotation_scenes: int = 0

    def upload(self, dm_item: dm_DatasetItem, media_info: MediaInfo) -> AnnotationScene:
        """
        Convert and validate dm_item into SC Video and upload it to VideoRepo.

        :param dm_item: Datumaro dataset item.
        :param media_info: SC media information containing the annotations
        :return Converted AnnotationScene item.
        """
        # TODO: check_free_space_for_operation
        # CVS-151440: There's no need to verify the number of annotation versions.
        # Even if the MAX_NUMBER_OF_ANNOTATION_VERSIONS_PER_MEDIA is specified,
        # the new annotations_scene will always be the initial version.
        annotation_scene = ConvertUtils.get_annotation_scene_from_dm_item(
            dm_item=dm_item,
            media_info=media_info,
            get_sc_label=self._get_sc_label,
            uploader_id=self._uploader_id,
            empty_labels=self._empty_labels,
            sc_label_to_all_parents=self._sc_label_to_all_parents,
            sc_label_to_group_id=self._sc_label_to_group_id,
        )
        # since CVS-98893, Geti does no longer require empty annotations to represent unannotated media in the database
        if annotation_scene.annotations:
            self._ann_scene_repo.save(annotation_scene)
            ann_scene_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                annotation_scene=annotation_scene, project=self._project
            )
            self._ann_scene_state_repo.save(ann_scene_state)

            self._publish_annotation_scene_message(
                annotation_scene_id=annotation_scene.id_,
            )

            self._num_annotation_scenes += 1

        return annotation_scene

    def _publish_annotation_scene_message(
        self,
        annotation_scene_id: ID,
    ) -> None:
        """
        Publish annotation scene created message

        :param annotation_scene_id: ID of newly added annotation scene
        """
        body = {
            "workspace_id": str(self._dataset_storage_identifier.workspace_id),
            "project_id": str(self._dataset_storage_identifier.project_id),
            "dataset_storage_id": str(self._dataset_storage_identifier.dataset_storage_id),
            "annotation_scene_id": str(annotation_scene_id),
        }
        publish_event(
            topic="new_annotation_scene",
            body=body,
            key=str(annotation_scene_id).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

    def __len__(self):
        return self._num_annotation_scenes

    def get_range_labels(self, dm_item: dm_DatasetItem) -> RangeLabels | None:
        """
        Convert dm.Video media to RangeLabels.

        :return: Video path and its range labels
        """
        # We assume that a dm_Video represents one of RangeLabels in a VideoAnnotationRange.
        try:
            start_frame = dm_item.media._start_frame
            end_frame = dm_item.media._end_frame or 0  # end_frame=None if end_frame==0
        except AttributeError:
            return None

        has_empty_label = dm_item.attributes.get("has_empty_label", False)
        if has_empty_label and len(self._empty_labels) > 0:
            label_ids = [self._empty_labels[0].id_]
        else:
            label_ids = []
            for ann in dm_item.annotations:
                label: Label | None = self._get_sc_label(ann.label)
                if label and label != NullLabel and isinstance(ann, dm_Label):
                    label_ids.append(label.id_)
            if len(label_ids) == 0:
                return None
        return RangeLabels(start_frame=start_frame, end_frame=end_frame, label_ids=label_ids)
