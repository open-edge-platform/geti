# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Implementation of VideoDecoder"""

import json
import logging
import os
import subprocess
from abc import abstractmethod
from collections.abc import Callable
from threading import Lock
from typing import Generic, NamedTuple, TypeVar

import cv2
import numpy as np
from cachetools import TTLCache
from geti_feature_tools import FeatureFlagProvider
from geti_types import Singleton

from media_utils.features import FeatureFlag

logger = logging.getLogger(__name__)

USE_DECORD = FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_DECORD_VIDEO_DECODER)
NUM_VIDEO_FRAME_DECODE_RETRIES = int(os.getenv("NUM_VIDEO_FRAME_DECODE_RETRIES", "5"))
VIDEO_FRAME_CACHE_MAX_SIZE_BYTES = int(os.getenv("VIDEO_FRAME_CACHE_MAX_SIZE_BYTES", "100000000"))  # def 100MB
# Note that the VIDEO_CACHE_TTL should be less than the expiry time for a video presigned URL.
VIDEO_CACHE_TTL = int(os.getenv("VIDEO_FRAME_CACHE_TTL", "300"))  # def 5 minutes
logger.info(
    "VideoDecoder configuration: "
    "Backend: 'OpenCV'; "
    f"Frame cache size: {VIDEO_FRAME_CACHE_MAX_SIZE_BYTES} bytes; "
    f"Video cache TTL: {VIDEO_CACHE_TTL}s "
)

ReaderT = TypeVar("ReaderT", bound=cv2.VideoCapture)
ReaderLockT = TypeVar("ReaderLockT")


class VideoFrameOutOfRangeInternalException(Exception):
    """Raised when a video frame is requested that is outside the video frame range for the video"""


def _clean_file_location(file_location: str) -> str:
    """
    Remove the variable path from the file location in case of a presigned url to ensure caching works.
    """
    return file_location.split("?")[0]


class _VideoFrameCache(metaclass=Singleton):
    """LRU cache for video frames with TTL and bounded size in bytes"""

    def __init__(self) -> None:
        self._lock = Lock()
        self._cache: TTLCache = TTLCache(
            maxsize=VIDEO_FRAME_CACHE_MAX_SIZE_BYTES,
            ttl=VIDEO_CACHE_TTL,
            getsizeof=lambda frame_np: frame_np.nbytes,
        )

    def get_if_exists(self, file_location: str, frame_index: int) -> np.ndarray | None:
        """
        Get a specific frame from the cache, if present.

        :param file_location: Path to the video file, used to uniquely identify the video within the cache
        :param frame_index: Index of the video frame to get
        :return: Frame as numpy array, or None if not cached
        """
        file_location = _clean_file_location(file_location)
        frame = self._cache.get((file_location, frame_index))
        if frame is not None:
            logger.debug(f"Frame {frame_index} at {file_location} found in cache.")
        return frame

    def store(self, file_location: str, frame_index: int, frame: np.ndarray) -> None:
        """
        Store a frame in the cache.

        :param file_location: Path to the video file, used to uniquely identify the video within the cache
        :param frame_index: Index of the video frame to be stored
        :param frame: Frame to be stored
        """
        file_location = _clean_file_location(file_location)
        with self._lock:
            try:
                self._cache[(file_location, frame_index)] = frame
            except ValueError as exc:
                # A ValueError may be raised if the frame size is larger than the cache.
                # Log at debug level to avoid spam
                logger.debug(f"Frame at {file_location} could not be cached due to exception: {exc}")


class VideoTTLCache(TTLCache):
    """
    Custom TTL cache that can release the video capture when an entry is removed from the cache
    """

    @staticmethod
    def release_video_capture(value: ReaderT) -> None:
        """Release the videocapture"""
        if isinstance(value, cv2.VideoCapture):
            logger.debug("Cached video capture has been released")
            value.release()

    def __delitem__(self, key: str) -> None:
        self.release_video_capture(self[key][0])
        super().__delitem__(key)


class _VideoReaderCache(Generic[ReaderT, ReaderLockT], metaclass=Singleton):
    """LRU cache for video readers"""

    def __init__(self) -> None:
        self._lock = Lock()
        self._cache: VideoTTLCache = VideoTTLCache(maxsize=2, ttl=VIDEO_CACHE_TTL)

    def get_or_create(
        self, file_location: str, create_fn: Callable[[], tuple[ReaderT, ReaderLockT]]
    ) -> tuple[ReaderT, ReaderLockT]:
        """
        Get a video reader object from the cache, or create a new one if not already present.

        :param file_location: Path to the video file, used to uniquely identify the video within the cache
        :param create_fn: Function to create a new reader object
        :return: Tuple containing the video reader object and its associate lock
        """
        file_location = _clean_file_location(file_location)
        cached_value = self._cache.get(file_location)
        if cached_value is not None:
            return cached_value
        with self._lock:  # double-checked locking
            cached_value = self._cache.get(file_location)
            if cached_value is not None:
                return cached_value
            new_reader_with_lock = create_fn()
            self._cache[file_location] = new_reader_with_lock
            logger.debug(f"Video adapter cached for {file_location}")
            return new_reader_with_lock

    def evict(self, file_location: str) -> None:
        """
        Remove a specific entry from the cache

        :param file_location: Path to the video file, used to uniquely identify the video within the cache
        """
        file_location = _clean_file_location(file_location)
        with self._lock:
            self._cache.pop(file_location, None)


class VideoInformation(NamedTuple):
    fps: float
    width: int
    height: int
    total_frames: int


class VideoFrameReadingError(ValueError):
    """Error that can be raised when failing to read a video frame"""


class _VideoDecoderInterface:
    @abstractmethod
    def decode(self, file_location: str, frame_index: int) -> np.ndarray:
        pass

    @abstractmethod
    def get_video_information(self, file_location: str) -> VideoInformation:
        pass

    @abstractmethod
    def reset_reader(self, file_location: str) -> None:
        pass

    def get_fps(self, file_location: str) -> float:
        # Run ffprobe to get video stream information
        result = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=r_frame_rate",
                "-of",
                "json",
                file_location,
            ],
            capture_output=True,
            check=False,
        )
        ffprobe_output = json.loads(result.stdout)
        # Extract the raw frame rate (the frame rate at which the video stream is encoded).
        # This is a static value that may differ from the playback frame rate, which instead
        # changes dynamically during playback for VFR (Variable Frame Rate) videos.
        # The raw frame rate is expressed as a fraction (e.g. 30000/1001 -> 29.97 fps).
        r_frame_rate = ffprobe_output["streams"][0]["r_frame_rate"]
        # Calculate FPS from the r_frame_rate fraction
        num, denominator = map(int, r_frame_rate.split("/"))
        return num / denominator


class _VideoDecoderOpenCV(_VideoDecoderInterface, metaclass=Singleton):
    """OpenCV-based video decoder"""

    __video_reader_cache: _VideoReaderCache[cv2.VideoCapture, Lock] = _VideoReaderCache()

    def get_video_information(self, file_location: str) -> VideoInformation:
        """
        Create a _VideoInformation object with descriptive information about the video

        :param file_location: Local path or presigned S3 URL pointing to the video
        :return: _VideoInformation object containing information about the video
        """
        video_reader, video_reader_lock = _VideoDecoderOpenCV.__video_reader_cache.get_or_create(
            file_location=file_location,
            create_fn=lambda _fl=file_location: (cv2.VideoCapture(_fl, cv2.CAP_FFMPEG), Lock()),  # type: ignore[misc]
        )
        with video_reader_lock:
            return VideoInformation(
                fps=self.get_fps(file_location),
                width=int(video_reader.get(cv2.CAP_PROP_FRAME_WIDTH)),
                height=int(video_reader.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                total_frames=int(video_reader.get(cv2.CAP_PROP_FRAME_COUNT)),
            )

    def decode(self, file_location: str, frame_index: int) -> np.ndarray:
        """
        Decode the video and return the requested frame in array format

        :param file_location: Local storage path or presigned S3 URL pointing to the video
        :param frame_index: Frame index for the requested frame
        :return: Numpy array for the requested frame
        """
        # Get the frame from the cache, if present
        cached_frame = _VideoFrameCache().get_if_exists(file_location=file_location, frame_index=frame_index)
        if cached_frame is not None:
            return cached_frame

        # Acquire the VideoCapture
        video_reader, video_reader_lock = _VideoDecoderOpenCV.__video_reader_cache.get_or_create(
            file_location=file_location,
            create_fn=lambda _fl=file_location: (cv2.VideoCapture(_fl, cv2.CAP_FFMPEG), Lock()),  # type: ignore[misc]
        )
        with video_reader_lock:
            frame_count = int(video_reader.get(cv2.CAP_PROP_FRAME_COUNT))
            if not (0 <= frame_index < frame_count):
                raise VideoFrameOutOfRangeInternalException(
                    f"The requested frame index `{frame_index}` is out of bounds."
                )
            # For non-sequential reads, seek to the right frame position
            video_reader_frame_pos = int(video_reader.get(cv2.CAP_PROP_POS_FRAMES))
            if video_reader_frame_pos != frame_index:
                video_reader.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            # Read the frame at the requested position
            read_success, video_frame_raw = video_reader.read()
            if not read_success:
                raise VideoFrameReadingError(
                    f"Failed to read video frame at index {video_reader_frame_pos} for video at {file_location}"
                )
        # Post-process the frame (because OpenCV output is BGR)
        video_frame = cv2.cvtColor(video_frame_raw, cv2.COLOR_BGR2RGB)
        # Cache the frame
        _VideoFrameCache().store(file_location=file_location, frame_index=frame_index, frame=video_frame)
        return video_frame

    def reset_reader(self, file_location: str) -> None:
        _VideoDecoderOpenCV.__video_reader_cache.evict(file_location=file_location)


VideoDecoder: _VideoDecoderInterface = _VideoDecoderOpenCV()
