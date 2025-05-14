# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the Video entity"""

import datetime
import logging

from iai_core.entities.media import Media, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from iai_core.utils.time_utils import now

from geti_types import ID, VideoFrameIdentifier, VideoIdentifier, PersistentEntity

logger = logging.getLogger(__name__)

VIDEO_FRAME_THUMBNAIL_SUFFIX = "_thumbnail.jpg"
VIDEO_THUMBNAIL_SUFFIX = "_thumbnail.mp4"


class Video(Media, PersistentEntity):
    """
    This entity represents video as a persistent media in SC.

    :param id: the id of the video. Set to ID() so that a new unique ID will be assigned upon saving.
        If the argument is None, it will be set to ID()
    :param name: the name of the video
    :param stride: the stride of the video. This stride is the frame stride which will be shown on the UI.
                  The stride also determines which frames of the video will be analysed upon analysis request.
    :param creation_date: the date time on which the video is created.
        Set to None to automatically assign it to the time of object creation.
    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        id: ID,
        uploader_id: str,
        fps: float,
        width: int,
        height: int,
        total_frames: int,
        size: int,
        preprocessing: MediaPreprocessing,
        stride: int | None = None,
        creation_date: datetime.datetime | None = None,
        ephemeral: bool = True,
        extension: VideoExtensions = VideoExtensions.MP4,
    ) -> None:
        creation_date = now() if creation_date is None else creation_date
        stride = int(fps) if stride is None else stride  # default to 1 Hz

        PersistentEntity.__init__(self, id_=id, ephemeral=ephemeral)
        Media.__init__(
            self,
            name=name,
            height=height,
            width=width,
            creation_date=creation_date,
            uploader_id=uploader_id,
            size=size,
            extension=extension,
            preprocessing=preprocessing,
        )

        self.stride = stride
        self._fps = fps
        self._total_frames = total_frames

    @property
    def media_identifier(self) -> VideoIdentifier:
        return VideoIdentifier(self.id_)

    @property
    def total_frames(self) -> int:
        """Returns the total amount of frames in the video."""
        return self._total_frames

    @property
    def duration(self) -> int:
        """Return duration in seconds"""
        return int(self.total_frames // self.fps)

    @property
    def fps(self) -> float:
        """Returns the frames per second that are in the video as a float."""
        return self._fps

    @property
    def data_binary_filename(self) -> str:
        """
        Return the file name of the video.
        """
        return str(self.id_) + self.extension.value

    @property
    def thumbnail_filename(self) -> str:
        """
        :return: Filename for the frame thumbnail of the video.
        """
        return Video.thumbnail_filename_by_video_id(str(self.id_))

    @staticmethod
    def thumbnail_filename_by_video_id(video_id: str) -> str:
        """
        :param video_id: Video identifier
        :return: Filename for the frame thumbnail of the video.
        """
        return video_id + VIDEO_FRAME_THUMBNAIL_SUFFIX

    @property
    def thumbnail_video_filename(self) -> str:
        """
        :return: Filename of the thumbnail video for the video
        """
        return Video.thumbnail_video_filename_by_video_id(str(self.id_))

    @staticmethod
    def thumbnail_video_filename_by_video_id(video_id: str) -> str:
        """
        :param video_id: Video identifier
        :return: Filename of the thumbnail video for the video
        """
        return video_id + VIDEO_THUMBNAIL_SUFFIX

    def __eq__(self, other: object):
        if not isinstance(other, Video):
            return False

        return (
            self.id_ == other.id_
            and self.name == other.name
            and self.width == other.width
            and self.height == other.height
            and self.total_frames == other.total_frames
            and self.fps == other.fps
            and self.size == other.size
        )

    def __repr__(self) -> str:
        return f"Video({self.id_}, '{self.name}')"


class NullVideo(Video):
    """Representation of 'video not found'"""

    def __init__(self) -> None:
        super().__init__(
            name="",
            creation_date=datetime.datetime.min,
            id=ID(),
            uploader_id="",
            fps=0,
            width=0,
            height=0,
            total_frames=0,
            size=0,
            ephemeral=False,
            extension=VideoExtensions.MP4,  # have to provide a dummy extension when using NullVideo
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )

    def __repr__(self) -> str:
        return "NullVideo()"


class VideoFrame(Media):
    """
    Single video frame.

    Not persisted in database but extracted from `Video`.
    :param video: `Video` the frame belongs to
    :param frame_index: frame number of the frame
    """

    def __init__(self, video: Video, frame_index: int) -> None:
        Media.__init__(
            self,
            name=video.name,
            height=video.height,
            width=video.width,
            creation_date=video.creation_date,
            uploader_id=video.uploader_id,
            size=video.size,
            extension=video.extension,
            preprocessing=video.preprocessing,
        )
        self.video = video
        self.frame_index = frame_index

    def __eq__(self, other: object):
        if not isinstance(other, VideoFrame):
            return False
        return self.video.id_ == other.video.id_ and self.frame_index == other.frame_index

    def __repr__(self) -> str:
        return f"VideoFrame({self.video.id_}, frame_index='{self.frame_index}')"

    @property
    def media_identifier(self) -> VideoFrameIdentifier:
        return VideoFrameIdentifier(self.video.id_, self.frame_index)
