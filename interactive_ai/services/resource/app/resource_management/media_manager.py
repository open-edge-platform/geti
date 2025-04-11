# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

"""This module contains the media manager"""

import datetime
import functools
import logging
import subprocess
from pathlib import Path
from typing import BinaryIO

import cv2
import numpy as np

from communication.constants import (
    MAX_IMAGE_SIZE,
    MAX_NUMBER_OF_PIXELS,
    MAX_VIDEO_HEIGHT,
    MAX_VIDEO_LENGTH,
    MAX_VIDEO_WIDTH,
    MIN_IMAGE_SIZE,
    MIN_VIDEO_SIZE,
)
from communication.exceptions import (
    FileNotFoundException,
    ImageNotFoundException,
    ProjectLockedException,
    VideoFrameNotFoundException,
    VideoFrameOutOfRangeException,
    VideoNotFoundException,
)

from geti_fastapi_tools.exceptions import InvalidMediaException
from geti_kafka_tools import publish_event
from geti_telemetry_tools import unified_tracing
from geti_telemetry_tools.metrics import (
    EmptyInstrumentAttributes,
    convert_pixels,
    images_resolution_histogram,
    videos_frames_histogram,
    videos_resolution_histogram,
)
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, MediaType
from media_utils import (
    USE_DECORD,
    VideoDecoder,
    VideoFileRepair,
    VideoFrameOutOfRangeInternalException,
    VideoFrameReader,
    VideoFrameReadingError,
    get_image_numpy,
    get_media_roi_numpy,
)
from sc_sdk.adapters.binary_interpreters import NumpyBinaryInterpreter, StreamBinaryInterpreter
from sc_sdk.entities.annotation import Annotation
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.image import Image, NullImage
from sc_sdk.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from sc_sdk.entities.project import Project
from sc_sdk.entities.video import NullVideo, Video, VideoFrame
from sc_sdk.repos import ImageRepo, ProjectRepo, VideoRepo
from sc_sdk.repos.storage.binary_repos import ImageBinaryRepo, ThumbnailBinaryRepo, VideoBinaryRepo
from sc_sdk.repos.storage.storage_client import BytesStream
from sc_sdk.utils.constants import DEFAULT_THUMBNAIL_SIZE
from sc_sdk.utils.deletion_helpers import DeletionHelpers
from sc_sdk.utils.media_factory import Media2DFactory

IMAGES = "images"
VIDEOS = "videos"
IMAGE = "image"
VIDEO = "video"

logger = logging.getLogger(__name__)

IMAGE_EXT_SAVE_MAPPING: dict[ImageExtensions, ImageExtensions] = {
    # extensions stored natively
    ImageExtensions.PNG: ImageExtensions.PNG,
    ImageExtensions.JPG: ImageExtensions.JPG,
    ImageExtensions.JPEG: ImageExtensions.JPEG,
    ImageExtensions.BMP: ImageExtensions.BMP,
    ImageExtensions.WEBP: ImageExtensions.WEBP,
    # extensions to be converted before saving
    ImageExtensions.JFIF: ImageExtensions.JPEG,
    ImageExtensions.TIF: ImageExtensions.JPEG,
    ImageExtensions.TIFF: ImageExtensions.JPEG,
}


class MediaManager:
    @staticmethod
    @functools.lru_cache
    def get_image_by_id(dataset_storage_identifier: DatasetStorageIdentifier, image_id: ID) -> Image:
        image = ImageRepo(dataset_storage_identifier).get_by_id(image_id)
        if image is None or isinstance(image, NullImage):
            raise ImageNotFoundException(
                image_id=image_id,
                dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
            )
        return image

    @staticmethod
    def get_video_thumbnail(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
    ) -> BinaryIO:
        """
        Fetch a video frame from the repo and crop it to a thumbnail. Will try to use an
        existing thumbnail, otherwise one is created and saved.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video to fetch from the repo
        :return BinaryIO: image bytes stream that is a RGB representation of the image thumbnail
        """
        thumbnail_filename = Video.thumbnail_filename_by_video_id(str(video_id))
        try:
            return ThumbnailBinaryRepo(dataset_storage_identifier).get_by_filename(
                filename=thumbnail_filename,
                binary_interpreter=StreamBinaryInterpreter(),
            )
        except FileNotFoundError:
            try:
                video_numpy = MediaManager.get_video_frame_by_id(
                    dataset_storage_identifier=dataset_storage_identifier,
                    video_id=video_id,
                )
                return Media2DFactory.create_and_save_media_thumbnail(
                    dataset_storage_identifier=dataset_storage_identifier,
                    media_numpy=video_numpy,
                    thumbnail_binary_filename=thumbnail_filename,
                )
            except FileNotFoundError:
                raise FileNotFoundException(
                    f"Attempted to fetch a video frame from the video, but the data was not "
                    f"present in the repository."
                    f"Video ID: `{video_id}`."
                )

    @staticmethod
    def get_image_thumbnail(
        dataset_storage_identifier: DatasetStorageIdentifier,
        image_id: ID,
    ) -> BinaryIO:
        """
        Return the image thumbnail in BinaryIO format. If the thumbnail file is missing it is generated.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the image
        :param image_id: ID of the image
        :return: Image thumbnail in BinaryIO format
        """

        thumbnail_filename = Image.thumbnail_filename_by_image_id(str(image_id))
        try:
            return ThumbnailBinaryRepo(dataset_storage_identifier).get_by_filename(
                filename=thumbnail_filename,
                binary_interpreter=StreamBinaryInterpreter(),
            )
        except FileNotFoundError:
            image = MediaManager.get_image_by_id(
                dataset_storage_identifier=dataset_storage_identifier, image_id=image_id
            )
            image_numpy_data = get_image_numpy(dataset_storage_identifier=dataset_storage_identifier, image=image)
            return Media2DFactory.create_and_save_media_thumbnail(
                dataset_storage_identifier=dataset_storage_identifier,
                media_numpy=image_numpy_data,
                thumbnail_binary_filename=thumbnail_filename,
            )

    @staticmethod
    def get_video_by_id(dataset_storage_identifier: DatasetStorageIdentifier, video_id: ID) -> Video:
        """
        Get a video object by ID.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video to retrieve
        :return: Video
        :raises VideoNotFoundException if video could not be retrieved from the
            database.
        """
        video = VideoRepo(dataset_storage_identifier).get_by_id(video_id)
        if video is None or isinstance(video, NullVideo):
            raise VideoNotFoundException(
                video_id=video_id,
                dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
            )
        return video

    @staticmethod
    def validate_video_frame_exists(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        frame_index: int,
    ) -> Video:
        """
        Validate a video frame by video ID and frame index and return Video.

        Note that obtaining a video frame is an expensive operation, which is kept in a
        separate method.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video the frame belongs to.
        :param frame_index: int of the requested frame. Return frame in the middle if
            frame_index is not given.
        :return: Video to which the frame belongs.
        :raises VideoFrameNotFoundException if frame index is negative or larger than
            total video frames.
        """
        video = MediaManager.get_video_by_id(dataset_storage_identifier=dataset_storage_identifier, video_id=video_id)

        if not 0 <= frame_index < video.total_frames:
            raise VideoFrameNotFoundException(video_id=video_id, frame_index=frame_index)

        return video

    @staticmethod
    @unified_tracing
    def get_video_frame_by_id(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        frame_index: int | None = None,
        roi: Annotation | None = None,
    ) -> np.ndarray:
        """
        Get a video frame by video ID and frame index.

        Returns frame in the middle of the video if frame index is not given as the
        first frames of the video might not give a representative thumbnail.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video the frame belongs to.
        :param frame_index: int of the requested frame. Return frame in the middle if
            frame_index is not given.
        :param roi: Region of interest to crop the frame to. If not given, the whole frame is returned.
        :return: ndarray representation of video frame.
        """
        video = MediaManager.get_video_by_id(dataset_storage_identifier=dataset_storage_identifier, video_id=video_id)
        if frame_index is None:
            frame_index = video.total_frames // 2
        try:
            frame_numpy = get_media_roi_numpy(
                dataset_storage_identifier=dataset_storage_identifier,
                media=VideoFrame(video=video, frame_index=frame_index),
                roi_shape=roi.shape if roi is not None else None,
            )
        except FileNotFoundError:
            raise FileNotFoundException(
                f"Attempted to fetch video frame data for frame {str(frame_index)} of "
                f"the video, but the data was not present in the repository. "
                f"Video ID: `{video_id}`."
            )
        except VideoFrameOutOfRangeInternalException:
            raise VideoFrameOutOfRangeException(
                video_id=video.id_,
                frame_index=frame_index,
                total_frames=video.total_frames,
            )
        return frame_numpy

    @staticmethod
    def get_single_thumbnail_frame_numpy(
        dataset_storage_identifier: DatasetStorageIdentifier, video: Video, frame_index: int
    ) -> np.ndarray:
        """
        Get the thumbnail of a specific frame as a numpy array. Since the thumbnail video
        is generated at 1 fps, this function divides the frame index by the video fps

        :param dataset_storage_identifier: DatasetStorage containing the video
        :param video: video
        :param frame_index: Frame index (0 for first frame)

        :return: RGB numpy array
        """

        thumbnail_binary_repo = ThumbnailBinaryRepo(dataset_storage_identifier)
        if not thumbnail_binary_repo.exists(video.thumbnail_video_filename):
            logger.warning(f"Thumbnail video not found for {video}.")
            raise FileNotFoundError("No thumbnail video found.")

        index = int(frame_index / video.fps)

        # The preview video is rounded down on fps. In case a thumbnail for one of the last frames is requested,
        # subtract the FPS from the frame index to ensure it is in range of the thumbnail video.
        if video.total_frames - frame_index < video.fps and index > 0:
            index -= 1

        return VideoFrameReader.get_frame_numpy(
            file_location_getter=lambda: str(
                thumbnail_binary_repo.get_path_or_presigned_url(filename=video.thumbnail_video_filename)
            ),
            frame_index=index,
        )

    @staticmethod
    @unified_tracing
    def get_video_thumbnail_frame_by_id(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        frame_index: int | None = None,
    ) -> np.ndarray:
        """
        Get a video thumbnail frame by video ID and frame index.

        Returns frame in the middle of the video if frame index is not given as the
        first frames of the video might not give a representative thumbnail.

        :param dataset_storage_identifier: DatasetStorage containing the video
        :param video_id: ID of the video the frame belongs to.
        :param frame_index: int of the requested frame. Return frame in the middle if
            frame_index is not given.
        :return: ndarray representation of video frame.
        """
        video = VideoRepo(dataset_storage_identifier).get_by_id(video_id)
        video_binary_repo = VideoBinaryRepo(dataset_storage_identifier)
        if frame_index is None:
            frame_index = video.total_frames // 2
        try:
            frame_numpy = MediaManager.get_single_thumbnail_frame_numpy(
                video=video, dataset_storage_identifier=dataset_storage_identifier, frame_index=frame_index
            )
        except FileNotFoundError:
            publish_event(
                topic="thumbnail_video_missing",
                body={
                    "video_id": video.id_,
                    "workspace_id": dataset_storage_identifier.workspace_id,
                    "project_id": dataset_storage_identifier.project_id,
                    "dataset_storage_id": dataset_storage_identifier.dataset_storage_id,
                },
                key=str(video.id_).encode(),
                headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
            )
            full_frame_numpy = VideoFrameReader.get_frame_numpy(
                file_location_getter=lambda: str(
                    video_binary_repo.get_path_or_presigned_url(video.data_binary_filename)
                ),
                frame_index=frame_index,
            )
            frame_numpy = Media2DFactory.crop_to_thumbnail(
                media_numpy=full_frame_numpy,
                target_height=DEFAULT_THUMBNAIL_SIZE,
                target_width=DEFAULT_THUMBNAIL_SIZE,
            )
        except VideoFrameReadingError:  # Raised when video thumbnail video is not ready yet
            logger.warning(
                f"Video thumbnail for video {video.id_} is not available yet, creating and returning a "
                f"thumbnail frame on-the-fly"
            )
            full_frame_numpy = VideoFrameReader.get_frame_numpy(
                file_location_getter=lambda: str(
                    video_binary_repo.get_path_or_presigned_url(video.data_binary_filename)
                ),
                frame_index=frame_index,
            )
            frame_numpy = Media2DFactory.crop_to_thumbnail(
                media_numpy=full_frame_numpy,
                target_height=DEFAULT_THUMBNAIL_SIZE,
                target_width=DEFAULT_THUMBNAIL_SIZE,
            )
        except VideoFrameOutOfRangeInternalException:
            raise VideoFrameOutOfRangeException(
                video_id=video.id_,
                frame_index=frame_index,
                total_frames=video.total_frames,
            )
        return frame_numpy

    @staticmethod
    def get_video_frame_thumbnail_numpy(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        target_height: int,
        target_width: int,
        frame_index: int | None = None,
    ) -> np.ndarray:
        """
        Fetch a video frame from the repo and crop it to a thumbnail

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video to fetch from the repo
        :param frame_index: Index of the video frame in the video
        :param target_height: target height of the thumbnail
        :param target_width: target width of the thumbnail
        :return: numpy array that is a RGB representation of the video frame thumbnail
        """
        video_frame = MediaManager.get_video_frame_by_id(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
            frame_index=frame_index,
        )
        return Media2DFactory.crop_to_thumbnail(
            media_numpy=video_frame,
            target_height=target_height,
            target_width=target_width,
        )

    @staticmethod
    def get_path_or_presigned_url_for_video(
        dataset_storage_identifier: DatasetStorageIdentifier, video_id: ID
    ) -> Path | str:
        """
        Get the local storage path or presigned S3 URL pointing to the video with the given ID.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video
        :return: Path or presigned URL pointing to the binary file
        """
        video = MediaManager.get_video_by_id(dataset_storage_identifier=dataset_storage_identifier, video_id=video_id)
        video_name = f"{video.name}{video.extension.value}"
        # This will override the default Content-Disposition header based on ID set by the object storage.
        # Example of the default header: "ContentDisposition": "inline; filename=\"677fb6531255b4d731725d11.mp4\"".
        headers = {
            "response-content-disposition": f'attachment; filename="{video_name}"',
        }
        return VideoBinaryRepo(dataset_storage_identifier).get_path_or_presigned_url(
            filename=video.data_binary_filename, preset_headers=headers
        )

    @staticmethod
    @unified_tracing
    def upload_image(
        dataset_storage_identifier: DatasetStorageIdentifier,
        basename: str,
        extension: ImageExtensions,
        data_stream: BytesStream,
        user_id: ID,
        update_metrics: bool = False,
    ) -> Image:
        """
        Store a image uploaded by the user.

        Specifically, this function:
         - Sanity checks the image data and filename
         - Updates the extension to use for saving the image
         - Saves the image to the database and object storage
         - Creates and saves a thumbnail

        :param dataset_storage_identifier: Identifier of the dataset storage where the image is uploaded
        :param basename: Basename of the image file uploaded by the user
        :param extension: Extension of the image file uploaded by the user
        :param data_stream: Binary data stream of image
        :param user_id: ID of the user who created or updated the annotation
        :param update_metrics: Whether to update telemetry metrics
        :return: Image entity created or Exception if it fails to upload
        :raises InvalidMediaException when the uploaded media deviates from minimum/maximum media size
        :raises ValueError when the project does not exist
        """
        # Determine the extension to use for saving the image;
        # this may differ from the original extension of the user-uploaded file.
        save_extension = IMAGE_EXT_SAVE_MAPPING.get(extension)
        if not save_extension:  # to avoid issue, we require each supported format to have an explicit mapping
            raise InvalidMediaException(f"Unsupported image extension: {extension}")

        # Decode the image data
        data = data_stream.data().read(data_stream.length())
        try:
            bgr_image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        except cv2.error:
            bgr_image = None
        if bgr_image is None:
            raise InvalidMediaException(
                f"Cannot upload image `{basename}{extension}`. The server was not able to interpret it."
            )

        # Check that the image size is within the allowed range
        MediaManager.validate_image_dimensions(bgr_image)

        if extension != save_extension:
            data = NumpyBinaryInterpreter.get_bytes_from_numpy(bgr_image, save_extension.value)

        # Store the image with provided data and extension.
        # If the original extension does not match the save extension,
        # the image will be converted and saved with the save extension.
        image_repo = ImageRepo(dataset_storage_identifier)
        image_binary_repo = ImageBinaryRepo(dataset_storage_identifier)
        image_id = ImageRepo.generate_id()
        binary_filename = None
        try:
            # Store binary file
            filename = f"{str(image_id)}{save_extension.value}"
            binary_filename = image_binary_repo.save(dst_file_name=filename, data_source=data)
            size = image_binary_repo.get_object_size(binary_filename)

            image = Image(
                name=basename,
                uploader_id=user_id,
                id=image_id,
                extension=save_extension,
                width=bgr_image.shape[1],
                height=bgr_image.shape[0],
                size=size,
                preprocessing=MediaPreprocessing(
                    status=MediaPreprocessingStatus.IN_PROGRESS, start_timestamp=datetime.datetime.now()
                ),
            )
            image_repo.save(image)
        except Exception:
            # In case of error, delete any binary file that was already stored
            logger.exception(
                "Error saving image `%s` to `%s`; associated binaries will be removed",
                image_id,
                dataset_storage_identifier,
            )
            if binary_filename is not None:
                image_binary_repo.delete_by_filename(binary_filename)
            raise

        try:
            # Create a thumbnail for the image
            Media2DFactory.create_and_save_media_thumbnail(
                dataset_storage_identifier=dataset_storage_identifier,
                media_numpy=cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB),
                thumbnail_binary_filename=image.thumbnail_filename,
            )
            image.preprocessing.finished()
        except Exception:
            image.preprocessing.failed("Failed to preprocess image file")
            raise
        finally:
            image_repo.save(image)

        if update_metrics:
            MediaManager._update_image_metrics(image=image)

        logger.debug(
            f"Image '{basename}{extension}' uploaded by user {user_id} to {dataset_storage_identifier} "
            f"was successfully stored as '{image.data_binary_filename}'"
        )
        return image

    @staticmethod
    def _update_image_metrics(image: Image) -> None:
        """
        Update metrics relative to images:
          - resolution histogram

        :param image: Uploaded image
        """
        # Compute the size of the image in the unit required by the instrument
        image_resolution = convert_pixels(
            num_pixels=(image.width * image.height),
            unit=images_resolution_histogram.unit,  # type: ignore
        )
        # Record data point
        images_resolution_histogram.record(image_resolution, EmptyInstrumentAttributes().to_dict())

    @staticmethod
    def _update_video_metrics(video: Video) -> None:
        """
        Update metrics relative to videos:
          - resolution histogram
          - histogram

        :param video: Uploaded video
        """
        # Compute the size of the video in the unit required by the instrument
        video_resolution = convert_pixels(
            num_pixels=(video.width * video.height),
            unit=videos_resolution_histogram.unit,  # type: ignore
        )
        # Record data point
        videos_resolution_histogram.record(video_resolution, EmptyInstrumentAttributes().to_dict())
        videos_frames_histogram.record(video.total_frames, EmptyInstrumentAttributes().to_dict())

    @staticmethod
    def validate_image_dimensions(image: np.ndarray) -> None:
        """
        Validates that the image does not exceed the minimum/maximum allowed dimensions, or the maximum number of pixels
        """
        is_too_small = image.shape[0] < MIN_IMAGE_SIZE or image.shape[1] < MIN_IMAGE_SIZE
        is_too_large = image.shape[0] > MAX_IMAGE_SIZE or image.shape[1] > MAX_IMAGE_SIZE

        if MAX_NUMBER_OF_PIXELS:
            is_too_many_pixels = image.shape[0] * image.shape[1] > MAX_NUMBER_OF_PIXELS
            if is_too_many_pixels or is_too_small or is_too_large:
                raise InvalidMediaException(
                    f"Invalid image dimensions. Image width and height have to be within the range of "
                    f"{MIN_IMAGE_SIZE} to {MAX_IMAGE_SIZE} pixels."
                    f"The maximum number of pixels is {MAX_NUMBER_OF_PIXELS}."
                )

        if is_too_small or is_too_large:
            raise InvalidMediaException(
                f"Invalid image dimensions. Image width and height have to be within the range of "
                f"{MIN_IMAGE_SIZE} to {MAX_IMAGE_SIZE} pixels."
            )

    @staticmethod
    def create_and_save_thumbnail_video(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video: Video,
    ) -> None:
        """
        Creates and saves a video thumbnail. Tries to maintain aspect ratio up until
        16:9 when generating the thumbnail video. Anything above that will be squared.
        Thumbnail video is first written to a temporary file and then renamed to the
        original thumbnail video file path. This is done so any checks if the thumbnail
        video path already exists do not pass while the file is still being written to.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video: Base Video to use for thumbnail generation
        """
        VideoRepo(dataset_storage_identifier)
        thumbnail_binary_repo = ThumbnailBinaryRepo(dataset_storage_identifier)
        video_binary_repo = VideoBinaryRepo(dataset_storage_identifier)
        # This checks if the video thumbnail has already been generated. If so,the
        # thumbnail video is not generated
        thumbnail_exists = thumbnail_binary_repo.exists(filename=video.thumbnail_video_filename)
        if not thumbnail_exists:
            aspect_ratio = video.width / video.height
            target_resolution = f"{DEFAULT_THUMBNAIL_SIZE}:{DEFAULT_THUMBNAIL_SIZE}"
            if 1 < aspect_ratio < 1.8:
                target_resolution = f"{DEFAULT_THUMBNAIL_SIZE}:-2"

            tmp_thumbnail_path = thumbnail_binary_repo.create_path_for_temporary_file(
                filename=video.thumbnail_video_filename, make_unique=False
            )
            video_path_or_url = str(video_binary_repo.get_path_or_presigned_url(filename=video.data_binary_filename))
            process = subprocess.Popen(  # noqa: S603
                [  # noqa: S607
                    "ffmpeg",
                    "-threads",
                    "1",
                    "-y",
                    "-i",
                    video_path_or_url,
                    "-vf",
                    f"scale={target_resolution}",
                    "-r",
                    "1",
                    "-an",
                    "-threads",
                    "1",
                    tmp_thumbnail_path,
                ],
            )
            # Since this method is usually called from a Kafka event, this needs to complete within 15 minutes so the
            # Kafka consumer is not kicked out for exceeding the polling interval.
            exit_code = process.wait(timeout=885)
            if exit_code != 0:
                logger.warning(f"Failed writing thumbnail video for video {video.id_} with exit code: {exit_code}")
            thumbnail_binary_repo.save(
                data_source=tmp_thumbnail_path,
                remove_source=True,
                dst_file_name=video.thumbnail_video_filename,
            )

    @staticmethod
    @unified_tracing
    def upload_video(
        dataset_storage_identifier: DatasetStorageIdentifier,
        basename: str,
        extension: VideoExtensions,
        data_stream: BytesStream,
        user_id: ID,
        update_metrics: bool = False,
    ) -> Video:
        """
        Store a video uploaded by the user.

        :param dataset_storage_identifier: Identifier of the dataset storage where the video is uploaded
        :param basename: Basename of the video file uploaded by the user
        :param extension: Extension of the video file uploaded by the user
        :param data_stream: Binary data stream of video
        :param user_id: ID of the user who uploaded the video
        :param update_metrics: Whether to update telemetry metrics
        :return: Video entity created or Exception if it fails to upload
        :raises InvalidMediaException if the video is invalid (corrupted or empty data,
            unsupported format, bad size, ...)
        """
        video_repo = VideoRepo(dataset_storage_identifier)
        video_binary_repo = video_repo.binary_repo
        video_id = VideoRepo.generate_id()
        orig_filename = f"{basename}{extension.value}"

        binary_filename = video_binary_repo.save(
            dst_file_name=f"{str(video_id)}{extension.value}", data_source=data_stream
        )
        logger.debug(
            f"Saved bytes of video `{basename}{extension.value}` (ID `{video_id}`) in {dataset_storage_identifier}",
        )

        if USE_DECORD:
            try:
                info = VideoDecoder.get_video_information(
                    str(video_binary_repo.get_path_or_presigned_url(binary_filename))
                )
            except (RuntimeError, KeyError):
                video_binary_repo.delete_by_filename(filename=binary_filename)
                raise InvalidMediaException("Video file can not be read.")
        else:
            logger.debug(f"Getting video information for video with ID {video_id} with name {binary_filename}.")
            try:
                info = VideoDecoder.get_video_information(
                    str(video_binary_repo.get_path_or_presigned_url(binary_filename))
                )
            except KeyError:
                video_binary_repo.delete_by_filename(filename=binary_filename)
                raise InvalidMediaException("Video file can not be read.")

            logger.debug(f"Successfully fetched video information for video with ID {video_id}.")
            if not VideoFileRepair.check_and_repair_video(
                video_binary_repo=video_binary_repo, filename=binary_filename
            ):
                video_binary_repo.delete_by_filename(filename=binary_filename)  # Delete binary
                raise InvalidMediaException(
                    "The video file is corrupt. "
                    "The server was not able to read the last frame of the video, "
                    "and it was not able to repair the video"
                )

        video = Video(
            id=video_id,
            name=basename,
            extension=extension,
            uploader_id=user_id,
            fps=info.fps,
            width=info.width,
            height=info.height,
            total_frames=info.total_frames,
            size=video_binary_repo.get_object_size(binary_filename),
            preprocessing=MediaPreprocessing(
                status=MediaPreprocessingStatus.IN_PROGRESS, start_timestamp=datetime.datetime.now()
            ),
        )

        error_messages = MediaManager._validate_video_data(orig_filename, video)
        if error_messages:
            video_binary_repo.delete_by_filename(filename=binary_filename)
            raise InvalidMediaException(" ".join(error_messages))

        video_repo.save(video)

        try:
            video_numpy = MediaManager.get_video_frame_thumbnail_numpy(
                dataset_storage_identifier=dataset_storage_identifier,
                video_id=video_id,
                target_height=DEFAULT_THUMBNAIL_SIZE,
                target_width=DEFAULT_THUMBNAIL_SIZE,
            )
            Media2DFactory.create_and_save_media_thumbnail(
                dataset_storage_identifier=dataset_storage_identifier,
                media_numpy=video_numpy,
                thumbnail_binary_filename=video.thumbnail_filename,
            )
            logger.debug(
                f"Created thumbnail for video `{orig_filename}` (ID `{video_id}`) "
                f"in dataset storage `{dataset_storage_identifier}`",
            )
            video.preprocessing.finished()
        except Exception:
            video.preprocessing.failed("Failed to preprocess video file")
            raise
        finally:
            video_repo.save(video)

        publish_event(
            topic="thumbnail_video_missing",
            body={
                "video_id": video.id_,
                "workspace_id": dataset_storage_identifier.workspace_id,
                "project_id": dataset_storage_identifier.project_id,
                "dataset_storage_id": dataset_storage_identifier.dataset_storage_id,
            },
            key=str(video.id_).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

        if update_metrics:
            MediaManager._update_video_metrics(video=video)

        logger.debug(
            f"Video '{orig_filename}' uploaded by user {user_id} to {dataset_storage_identifier} "
            f"was successfully stored as '{video.data_binary_filename}'"
        )
        return video

    @staticmethod
    def _validate_video_data(filename: str, video: Video) -> list[str]:
        error_messages = []
        if video.total_frames == 0:
            error_messages.append(
                f"Encountered an error while decoding video: '{filename}'. Unable to extract frames from video."
            )
        if video.width > MAX_VIDEO_WIDTH or video.height > MAX_VIDEO_HEIGHT:
            error_messages.append(
                f"Video too large: the maximum width is {MAX_VIDEO_WIDTH} and the maximum height is {MAX_VIDEO_HEIGHT}."
            )
        if video.duration > MAX_VIDEO_LENGTH:
            error_messages.append(f"Video too long: the maximum duration is {MAX_VIDEO_LENGTH // 3600} hours")
        if video.width < MIN_VIDEO_SIZE or video.height < MIN_VIDEO_SIZE:
            error_messages.append(
                f"Video too small, the minimum size is {MIN_VIDEO_SIZE}x{MIN_VIDEO_SIZE} pixels. The dimensions "
                f"extracted for this video are: "
                f"{video.width}x{video.height} pixels"
            )
        return error_messages

    @staticmethod
    @unified_tracing
    def delete_image_by_id(project: Project, dataset_storage: DatasetStorage, image_id: ID) -> None:
        if ProjectRepo().read_lock(project_id=project.id_):
            raise ProjectLockedException(name=project.name)

        image = MediaManager.get_image_by_id(
            dataset_storage_identifier=dataset_storage.identifier,
            image_id=image_id,
        )
        try:
            DeletionHelpers.delete_image_entity(dataset_storage=dataset_storage, image=image)
        except FileNotFoundError:
            logger.error(
                f"Attempted to fetch image data for image {image.id_} but the data was not present in the repository."
            )
        body = {
            "workspace_id": project.workspace_id,
            "project_id": project.id_,
            "dataset_storage_id": dataset_storage.id_,
            "media_id": image_id,
            "media_type": MediaType.IMAGE.value,
        }
        publish_event(
            topic="media_deletions",
            body=body,
            key=str(image_id).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

    @staticmethod
    @unified_tracing
    def delete_video_by_id(project: Project, dataset_storage: DatasetStorage, video_id: ID) -> None:
        if ProjectRepo().read_lock(project_id=project.id_):
            raise ProjectLockedException(name=project.name)

        video = MediaManager.get_video_by_id(dataset_storage_identifier=dataset_storage.identifier, video_id=video_id)
        try:
            DeletionHelpers.delete_video_entity(dataset_storage=dataset_storage, video=video)
        except FileNotFoundError:
            logger.error(
                f"Attempted to fetch video data for video {video.id_} but the data was not present in the repository."
            )
        body = {
            "workspace_id": project.workspace_id,
            "project_id": project.id_,
            "dataset_storage_id": dataset_storage.id_,
            "media_id": video_id,
            "media_type": MediaType.VIDEO.value,
        }
        publish_event(
            topic="media_deletions",
            body=body,
            key=str(video_id).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

    @staticmethod
    def get_first_media(
        dataset_storage_identifier: DatasetStorageIdentifier,
    ) -> Video | Image | None:
        """
        Gets the first image in the project, or the first video if there is no image. Return None if neither exists.

        :param dataset_storage_identifier: Identifier of the dataset
        :return: first Image or Video, if media exists in project, else None
        """
        first_image = ImageRepo(dataset_storage_identifier).get_one(earliest=True)
        if not isinstance(first_image, NullImage):
            return first_image
        first_video = VideoRepo(dataset_storage_identifier).get_one(earliest=True)
        if not isinstance(first_video, NullVideo):
            return first_video
        return None
