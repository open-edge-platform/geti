# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

import numpy as np
from geti_types import DatasetStorageIdentifier
from iai_core.adapters.binary_interpreters import NumpyBinaryInterpreter, RAWBinaryInterpreter
from iai_core.entities.image import Image
from iai_core.entities.media_2d import Media2D
from iai_core.entities.shapes import Rectangle, Shape
from iai_core.entities.video import Video, VideoFrame
from iai_core.repos.storage.binary_repos import ImageBinaryRepo, VideoBinaryRepo

from .video_frame_reader import VideoFrameReader

logger = logging.getLogger(__name__)


def get_media_roi_numpy(
    dataset_storage_identifier: DatasetStorageIdentifier,
    media: Image | VideoFrame | Media2D,
    roi_shape: Shape | None = None,
) -> np.ndarray:
    """
    Returns media (image or video frame) ROI-cropped numpy array. Only Rectangle ROI shape is supported.
    :param dataset_storage_identifier: Dataset storage identifier
    :param media: media to get numpy array for
    :param roi_shape: ROI shape
    :return np.ndarray: media ROI-cropped numpy array
    :raises ValueError: when ROI shape is not Rectangle or it's one dimensional
    """
    if roi_shape is not None and not isinstance(roi_shape, Rectangle):
        raise ValueError(f"ROI shape passed to {str(media)} is not a Rectangle")

    media_numpy = get_media_numpy(dataset_storage_identifier=dataset_storage_identifier, media=media)
    if roi_shape is None:
        return media_numpy

    if len(media_numpy.shape) < 2:
        raise ValueError(f"{str(media)} is one dimensional, and thus cannot be cropped")

    return roi_shape.crop_numpy_array(media_numpy)


def get_media_numpy(
    dataset_storage_identifier: DatasetStorageIdentifier,
    media: Image | VideoFrame | Media2D,
) -> np.ndarray:
    """
    Returns media (image or video frame) numpy array
    :param dataset_storage_identifier: Dataset storage identifier
    :param media: media to get numpy array for
    :return np.ndarray: media numpy array
    """
    if isinstance(media, VideoFrame):
        return get_video_frame_numpy(dataset_storage_identifier=dataset_storage_identifier, video_frame=media)
    return get_image_numpy(dataset_storage_identifier=dataset_storage_identifier, image=media)


def get_video_frame_numpy(dataset_storage_identifier: DatasetStorageIdentifier, video_frame: VideoFrame) -> np.ndarray:
    """
    Returns video frame numpy array
    :param dataset_storage_identifier: Dataset storage identifier
    :param video_frame: video frame to get numpy array for
    :return np.ndarray: video frame numpy array
    """
    video_binary_repo = VideoBinaryRepo(dataset_storage_identifier)
    return VideoFrameReader.get_frame_numpy(
        file_location_getter=lambda: str(
            video_binary_repo.get_path_or_presigned_url(filename=video_frame.video.data_binary_filename)
        ),
        frame_index=video_frame.frame_index,
    )


def get_image_numpy(dataset_storage_identifier: DatasetStorageIdentifier, image: Image) -> np.ndarray:
    """
    Returns image numpy array
    :param dataset_storage_identifier: Dataset storage identifier
    :param image: image to get numpy array for
    :return np.ndarray: image numpy array
    """
    image_binary_repo = ImageBinaryRepo(dataset_storage_identifier)
    return image_binary_repo.get_by_filename(
        filename=image.data_binary_filename, binary_interpreter=NumpyBinaryInterpreter()
    )


def get_image_bytes(dataset_storage_identifier: DatasetStorageIdentifier, image: Image) -> bytes:
    """
    Returns image binary content
    :param dataset_storage_identifier: Dataset storage identifier
    :param image: image to get content for
    :return bytes: image binary content
    """
    image_binary_repo = ImageBinaryRepo(dataset_storage_identifier)
    return image_binary_repo.get_by_filename(
        filename=image.data_binary_filename, binary_interpreter=RAWBinaryInterpreter()
    )


def get_video_bytes(dataset_storage_identifier: DatasetStorageIdentifier, video: Video) -> bytes:
    """
    Returns video binary content
    :param dataset_storage_identifier: Dataset storage identifier
    :param video: video to get content for
    :return bytes: video binary content
    """
    video_binary_repo = VideoBinaryRepo(dataset_storage_identifier)
    return video_binary_repo.get_by_filename(
        filename=video.data_binary_filename, binary_interpreter=RAWBinaryInterpreter()
    )
