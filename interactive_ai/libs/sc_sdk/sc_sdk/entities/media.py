"""This module implements the Media entity"""

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

import abc
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from geti_types import MediaIdentifierEntity


class VideoExtensions(str, Enum):
    """
    Enum defining possible video extensions that are supported in the SDK.
    Please update the docs as well:
    - internal_docs/in_depth/01-system_components/01-interactive_learning/03-dataset_management/03-dataset_management.md
    """

    MP4 = ".mp4"
    AVI = ".avi"
    MKV = ".mkv"
    MOV = ".mov"
    WEBM = ".webm"
    M4V = ".m4v"


class ImageExtensions(str, Enum):
    """
    Enum defining possible image extensions that are supported in the SDK.
    Please update the docs as well:
    - internal_docs/in_depth/01-system_components/01-interactive_learning/03-dataset_management/03-dataset_management.md
    """

    JPG = ".jpg"
    JPEG = ".jpeg"
    PNG = ".png"
    BMP = ".bmp"
    TIF = ".tif"
    TIFF = ".tiff"
    JFIF = ".jfif"
    WEBP = ".webp"


class MediaPreprocessingStatus(Enum):
    """
    Media preprocessing status.
    """

    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


@dataclass
class MediaPreprocessing:
    """
    Media preprocessing.
    """

    status: MediaPreprocessingStatus
    message: str | None = None
    start_timestamp: datetime | None = None
    end_timestamp: datetime | None = None

    def started(self) -> None:
        self.status = MediaPreprocessingStatus.IN_PROGRESS
        self.start_timestamp = datetime.now()

    def finished(self) -> None:
        self.status = MediaPreprocessingStatus.FINISHED
        self.end_timestamp = datetime.now()

    def failed(self, message: str) -> None:
        self.status = MediaPreprocessingStatus.FAILED
        self.end_timestamp = datetime.now()
        self.message = message


class Media(metaclass=abc.ABCMeta):
    """
    Media entities represent images, videos and video_frames.
    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        height: int,
        width: int,
        uploader_id: str,
        creation_date: datetime,
        size: int,
        extension: ImageExtensions | VideoExtensions,
        preprocessing: MediaPreprocessing,
    ) -> None:
        self.name = name
        self.preprocessing = preprocessing
        self._height = height
        self._width = width
        self._creation_date = creation_date
        self._uploader_id = uploader_id
        self._size = size
        self._extension = extension

    @property
    def height(self) -> int:
        """Returns the height of the media object."""
        return self._height

    @property
    def width(self) -> int:
        """Returns the width of the media object."""
        return self._width

    @property
    def creation_date(self) -> datetime:
        """Creation date of the media object"""
        return self._creation_date

    @property
    def uploader_id(self) -> str:
        """Unique identifier for the user who uploaded the media object"""
        return self._uploader_id

    @property
    def size(self) -> int:
        """Size of the media object in bytes"""
        return self._size

    @property
    def extension(self) -> ImageExtensions | VideoExtensions:
        """
        Returns the extension of the media object.
        """
        return self._extension

    @property
    @abc.abstractmethod
    def media_identifier(self) -> MediaIdentifierEntity:
        """
        Returns the media identifier which can be used to identify this media.
        See :class:`MediaIdentifierEntity`
        """
        raise NotImplementedError
