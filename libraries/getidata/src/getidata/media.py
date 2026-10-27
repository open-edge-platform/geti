# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Media types for lazy loading and caching of image and video data.

This module provides the LazyImage and LazyVideoFrame classes for lazy loading
media from disk, along with global LRU caches to manage memory usage when
working with many images and video frames.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from threading import RLock
from typing import Any

import numpy as np
from cachetools import LRUCache, cachedmethod
from PIL import Image, ImageOps

# Default cache size: 256 MB
_DEFAULT_CACHE_SIZE_BYTES = 256 * 1024 * 1024


def _get_image_size(img: np.ndarray) -> int:
    """Get the size of an image in bytes."""
    return img.nbytes


class ImageCache:
    """
    Global LRU cache for lazy-loaded images.

    The size of the cache can be updated dynamically, allowing fine-grained
    control over the memory usage. Images are automatically evicted when
    the cache exceeds its maximum size, with the least recently used images
    being removed first.

    The cache is keyed by (path, format, channels_first) tuples, so the same
    image loaded with different settings will be cached separately.

    Examples:
        >>> from getidata import ImageCache
        >>> ImageCache.set_size(512 * 1024 * 1024)  # Set cache to 512 MB
        >>> ImageCache.get_size()  # Get current cache size in bytes
        >>> ImageCache.length()  # Get number of cached images
        >>> ImageCache.clear()  # Clear all cached images
    """

    _cache: LRUCache[tuple[str, str, bool], np.ndarray] = LRUCache(
        maxsize=_DEFAULT_CACHE_SIZE_BYTES, getsizeof=_get_image_size
    )
    _lock = RLock()

    @classmethod
    def set_size(cls, maxsize_bytes: int) -> None:
        """
        Set the maximum size in bytes for the image cache.

        When the cache exceeds this size, the least recently used images are evicted.

        Args:
            maxsize_bytes: Maximum cache size in bytes. Set to 0 to disable caching.

        Example:
            >>> ImageCache.set_size(512 * 1024 * 1024)  # Set cache to 512 MB
        """
        with cls._lock:
            # Create a new cache with the new size, preserving existing items if they fit
            new_cache: LRUCache[tuple[str, str, bool], np.ndarray] = LRUCache(
                maxsize=maxsize_bytes, getsizeof=_get_image_size
            )
            if maxsize_bytes > 0:
                for key, value in cls._cache.items():
                    item_size = _get_image_size(value)
                    if new_cache.currsize + item_size <= maxsize_bytes:
                        new_cache[key] = value
            cls._cache = new_cache

    @classmethod
    def get_size(cls) -> int:
        """
        Get the current cache size in bytes.

        Returns:
            Current cache size in bytes.
        """
        with cls._lock:
            return int(cls._cache.currsize)

    @classmethod
    def get_max_size(cls) -> int:
        """
        Get the maximum cache size in bytes.

        Returns:
            Maximum cache size in bytes.
        """
        with cls._lock:
            return int(cls._cache.maxsize)

    @classmethod
    def clear(cls) -> None:
        """
        Clear all cached images from memory.

        Example:
            >>> ImageCache.clear()  # Free all cached image memory
        """
        with cls._lock:
            cls._cache.clear()

    @classmethod
    def length(cls) -> int:
        """
        Get the number of images currently cached.

        Returns:
            Number of cached images.
        """
        with cls._lock:
            return len(cls._cache)

    @classmethod
    def info(cls) -> dict[str, int]:
        """
        Get information about the current cache state.

        Returns:
            A dictionary with:
            - 'count': Number of images currently cached
            - 'current_size': Current cache size in bytes
            - 'max_size': Maximum cache size in bytes
        """
        with cls._lock:
            return {
                "count": len(cls._cache),
                "current_size": cls._cache.currsize,
                "max_size": cls._cache.maxsize,
            }


@dataclass
class LazyImage:
    """
    A wrapper class that holds an image path and provides lazy loading of image data.

    This class enables lazy loading patterns where the image is only loaded from
    disk when the `data` property is accessed. Loaded images are stored in a
    global LRU cache that limits total memory usage.

    The cache keeps the most recently accessed images in memory and automatically
    evicts the least recently used images when the cache is full. By default,
    the cache is limited to 256 MB. Use `ImageCache.set_size()` to adjust this limit.

    Attributes:
        path: The file path to the image (can be a string, Path object, or another LazyImage)
        format: The color format to use when loading ("RGB", "BGR", etc.)
        channels_first: Whether to return data in channels-first format (C, H, W)

    Examples:
        >>> lazy_img = LazyImage("/path/to/image.jpg")
        >>> print(lazy_img.path)  # Access path without loading
        /path/to/image.jpg
        >>> img_array = lazy_img.data  # Image loaded here on first access
        >>> print(img_array.shape)
        (480, 640, 3)

    Cache management:
        >>> from getidata import ImageCache
        >>> ImageCache.set_size(512 * 1024 * 1024)  # Limit to 512 MB
        >>> ImageCache.clear()  # Clear all cached images

    Using with Sample:
        >>> from getidata import Sample
        >>> from getidata.fields import image_path_field
        >>> class MySample(Sample):
        ...     image: LazyImage = image_path_field()
        ...
        >>> sample = MySample(image="/path/to/image.jpg")
        >>> sample.image.path  # Returns the path string
        >>> sample.image.data  # Returns the numpy array
    """

    path: str | Path | LazyImage
    format: str = "RGB"
    channels_first: bool = False

    def __post_init__(self) -> None:
        # Ensure path is stored as a string for consistency
        # Handle LazyImage input by extracting its path
        if isinstance(self.path, LazyImage):
            object.__setattr__(self, "path", self.path.path)
        elif isinstance(self.path, Path):
            object.__setattr__(self, "path", str(self.path))

    def _cache_key(self) -> tuple[str, str, bool]:
        """Generate a cache key for this image configuration."""
        return str(self.path), self.format.upper(), self.channels_first

    def _convert_to_format(self, img: Image.Image, target_format: str) -> np.ndarray:
        """Convert PIL image to numpy array in the target format.

        Supports 8-bit, 16-bit, and 32-bit images. The bit depth is preserved
        from the original image file - 16-bit images return uint16 arrays and
        32-bit images return int32 arrays.

        PIL mode reference:
            - "I": 32-bit signed integer pixels (int32)
            - "I;16", "I;16B", "I;16L", "I;16N": 16-bit unsigned integer pixels (uint16)

        Supported formats:
            - RGB: Standard RGB format (Red, Green, Blue)
            - BGR: OpenCV-compatible format (Blue, Green, Red)
            - RGBA: RGB with alpha channel
            - BGRA: BGR with alpha channel (OpenCV-compatible)
            - L / GRAY: Grayscale
        """
        is_high_depth = img.mode in ("I", "I;16", "I;16B", "I;16L", "I;16N")

        if target_format == "RGB":
            return self._convert_to_rgb(img, is_high_depth)
        if target_format == "BGR":
            return self._convert_to_bgr(img, is_high_depth)
        if target_format == "RGBA":
            return self._convert_to_rgba(img, is_high_depth)
        if target_format == "BGRA":
            return self._convert_to_bgra(img, is_high_depth)
        if target_format in ("L", "GRAY"):
            return self._convert_to_grayscale(img, is_high_depth)
        raise ValueError(
            f"Unsupported image format: {target_format!r}. Supported formats are: RGB, BGR, RGBA, BGRA, L, GRAY."
        )

    @staticmethod
    def _swap_rb_channels(img_array: np.ndarray) -> np.ndarray:
        """Swap red and blue channels for RGB <-> BGR conversion.

        Works with both 3-channel (RGB/BGR) and 4-channel (RGBA/BGRA) images.
        Returns a contiguous copy to avoid negative strides issues.
        """
        if img_array.ndim == 3:
            if img_array.shape[-1] == 3:
                # RGB <-> BGR: swap channels 0 and 2
                swapped = np.empty_like(img_array)
                swapped[..., 0] = img_array[..., 2]
                swapped[..., 1] = img_array[..., 1]
                swapped[..., 2] = img_array[..., 0]
                return swapped
            if img_array.shape[-1] == 4:
                # RGBA <-> BGRA: swap channels 0 and 2, keep alpha
                swapped = np.empty_like(img_array)
                swapped[..., 0] = img_array[..., 2]
                swapped[..., 1] = img_array[..., 1]
                swapped[..., 2] = img_array[..., 0]
                swapped[..., 3] = img_array[..., 3]
                return swapped
        return img_array.copy()

    def _convert_to_rgb(self, img: Image.Image, is_high_depth: bool) -> np.ndarray:
        """Convert image to RGB format (Red, Green, Blue)."""
        if is_high_depth:
            img_array = np.array(img)
            if img_array.ndim == 2:
                return np.stack([img_array] * 3, axis=-1)
            return img_array
        return np.array(img.convert("RGB"))

    def _convert_to_bgr(self, img: Image.Image, is_high_depth: bool) -> np.ndarray:
        """Convert image to BGR format (Blue, Green, Red).

        BGR is the default format used by OpenCV and some other libraries.
        """
        rgb_array = self._convert_to_rgb(img, is_high_depth)
        return self._swap_rb_channels(rgb_array)

    def _convert_to_rgba(self, img: Image.Image, is_high_depth: bool) -> np.ndarray:
        """Convert image to RGBA format (Red, Green, Blue, Alpha)."""
        if is_high_depth:
            img_array = np.array(img)
            if img_array.ndim == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            alpha = np.full(img_array.shape[:2], np.iinfo(img_array.dtype).max, dtype=img_array.dtype)
            return np.concatenate([img_array, alpha[..., np.newaxis]], axis=-1)
        return np.array(img.convert("RGBA"))

    def _convert_to_bgra(self, img: Image.Image, is_high_depth: bool) -> np.ndarray:
        """Convert image to BGRA format (Blue, Green, Red, Alpha).

        BGRA is used by OpenCV and some other libraries when alpha is needed.
        """
        rgba_array = self._convert_to_rgba(img, is_high_depth)
        return self._swap_rb_channels(rgba_array)

    def _convert_to_grayscale(self, img: Image.Image, is_high_depth: bool) -> np.ndarray:
        """Convert image to grayscale format (single channel)."""
        if is_high_depth:
            return np.array(img)
        return np.array(img.convert("L"))

    @cachedmethod(
        cache=lambda _: ImageCache._cache,
        key=lambda self: self._cache_key(),
        lock=lambda _: ImageCache._lock,
    )
    def _load_data(self) -> np.ndarray:
        """Load the image from disk (cached via @cachedmethod)."""
        with Image.open(self.path) as img:
            # Apply EXIF orientation so the returned array matches the
            # image's displayed orientation (and matches ``width``/``height``).
            oriented_img = ImageOps.exif_transpose(img)
            target_format = self.format.upper()
            img_array = self._convert_to_format(oriented_img, target_format)

            # Handle channels-first format
            if self.channels_first and img_array.ndim == 3:
                img_array = img_array.transpose(2, 0, 1)

        return img_array

    @property
    def data(self) -> np.ndarray:
        """
        Load and return the image data as a numpy array.

        The image is loaded from disk on first access and cached in a global
        LRU cache. Subsequent accesses return the cached data if available.
        When the cache is full, least recently used images are automatically
        evicted based on total memory usage.

        Returns:
            numpy.ndarray: The image data as a numpy array with shape:
                - (H, W, C) if channels_first is False
                - (C, H, W) if channels_first is True

        Raises:
            FileNotFoundError: If the image file does not exist
            PIL.UnidentifiedImageError: If the file cannot be read as an image
        """
        return self._load_data()

    def clear_cache(self) -> None:
        """Remove this image from the cache to free memory."""
        with ImageCache._lock:
            ImageCache._cache.pop(self._cache_key(), None)

    @cached_property
    def width(self) -> int:
        """Get the image width without fully loading the image data."""
        return self.size[0]

    @cached_property
    def height(self) -> int:
        """Get the image height without fully loading the image data."""
        return self.size[1]

    @cached_property
    def size(self) -> tuple[int, int]:
        """Get the image size (width, height) without fully loading the image data.

        Accounts for the EXIF orientation so that the reported dimensions match
        the image's displayed orientation.
        """
        with Image.open(self.path) as img:
            from getidata.exif_utils import get_exif_orientation, get_oriented_size

            w, h = img.size
            return get_oriented_size(w, h, get_exif_orientation(img))

    @property
    def shape(self) -> tuple[int, ...]:
        """
        Get the shape of the image data.

        Returns:
            tuple: Shape of the image array. If channels_first is False: (H, W, C).
                   If channels_first is True: (C, H, W). For grayscale: (H, W).
        """
        return self.data.shape

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path={self.path})"

    def __fspath__(self) -> str:
        """Allow LazyImage to be used in os.path operations."""
        return str(self.path)


@dataclass(frozen=True)
class VideoInfo:
    """
    Immutable container for video metadata.

    Attributes:
        path: Path to the video file
        total_frames: Total number of frames in the video
        fps: Frames per second
        width: Frame width in pixels
        height: Frame height in pixels
        duration: Video duration in seconds
        codec: Video codec (e.g., 'h264', 'vp9')
    """

    path: str
    total_frames: int
    fps: float
    width: int
    height: int
    duration: float
    codec: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize VideoInfo to a dictionary."""
        return {
            "path": self.path,
            "total_frames": self.total_frames,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "codec": self.codec,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VideoInfo:
        """Deserialize VideoInfo from a dictionary."""
        return cls(
            path=data["path"],
            total_frames=data["total_frames"],
            fps=data["fps"],
            width=data["width"],
            height=data["height"],
            duration=data["duration"],
            codec=data.get("codec"),
        )


@dataclass(frozen=True)
class MediaInfo:
    """
    Unified media metadata container for both images and video frames.

    This class provides a consistent interface for accessing media dimensions
    and metadata regardless of whether the source is an image file or a video frame.

    For images:
        - width, height: Image dimensions
        - fps, total_frames, duration, codec, frame_index: All None

    For video frames:
        - width, height: Frame dimensions
        - fps: Video frame rate
        - total_frames: Total frames in the video
        - duration: Video duration in seconds
        - codec: Video codec (e.g., 'h264')
        - frame_index: The specific frame index this info refers to

    Attributes:
        width: Media width in pixels
        height: Media height in pixels
        fps: Frames per second (None for images)
        total_frames: Total number of frames in the video (None for images)
        duration: Video duration in seconds (None for images)
        codec: Video codec string (None for images)
        frame_index: Frame index within video (None for images)

    Examples:
        >>> # From an image
        >>> info = MediaInfo.from_lazy_image(lazy_img)
        >>> info.width, info.height
        (1920, 1080)
        >>> info.is_video_frame
        False

        >>> # From a video frame
        >>> info = MediaInfo.from_lazy_video_frame(lazy_frame)
        >>> info.fps
        30.0
        >>> info.is_video_frame
        True
    """

    width: int
    height: int
    fps: float | None = None
    total_frames: int | None = None
    duration: float | None = None
    codec: str | None = None
    frame_index: int | None = None

    @property
    def is_video_frame(self) -> bool:
        """Check if this MediaInfo represents a video frame (vs an image)."""
        return self.fps is not None

    @property
    def is_image(self) -> bool:
        """Check if this MediaInfo represents a static image (vs a video frame)."""
        return self.fps is None

    @property
    def size(self) -> tuple[int, int]:
        """Get (width, height) tuple."""
        return (self.width, self.height)

    def to_dict(self) -> dict[str, Any]:
        """Serialize MediaInfo to a dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "total_frames": self.total_frames,
            "duration": self.duration,
            "codec": self.codec,
            "frame_index": self.frame_index,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MediaInfo:
        """Deserialize MediaInfo from a dictionary."""
        return cls(
            width=data["width"],
            height=data["height"],
            fps=data.get("fps"),
            total_frames=data.get("total_frames"),
            duration=data.get("duration"),
            codec=data.get("codec"),
            frame_index=data.get("frame_index"),
        )

    @classmethod
    def from_lazy_image(cls, lazy_image: LazyImage) -> MediaInfo:
        """
        Create MediaInfo from a LazyImage instance.

        Extracts width and height without loading the full image data.

        Args:
            lazy_image: The LazyImage to extract info from

        Returns:
            MediaInfo with image dimensions populated
        """
        return cls(
            width=lazy_image.width,
            height=lazy_image.height,
        )

    @classmethod
    def from_lazy_video_frame(cls, lazy_frame: LazyVideoFrame) -> MediaInfo:
        """
        Create MediaInfo from a LazyVideoFrame instance.

        Extracts both frame dimensions and video metadata.

        Args:
            lazy_frame: The LazyVideoFrame to extract info from

        Returns:
            MediaInfo with frame dimensions and video metadata populated
        """
        video_info = lazy_frame.video_info
        return cls(
            width=video_info.width,
            height=video_info.height,
            fps=video_info.fps,
            total_frames=video_info.total_frames,
            duration=video_info.duration,
            codec=video_info.codec,
            frame_index=lazy_frame.frame_index,
        )

    @classmethod
    def from_video_info(cls, video_info: VideoInfo, frame_index: int | None = None) -> MediaInfo:
        """
        Create MediaInfo from a VideoInfo instance.

        Args:
            video_info: The VideoInfo to convert
            frame_index: Optional frame index if this represents a specific frame

        Returns:
            MediaInfo with video metadata populated
        """
        return cls(
            width=video_info.width,
            height=video_info.height,
            fps=video_info.fps,
            total_frames=video_info.total_frames,
            duration=video_info.duration,
            codec=video_info.codec,
            frame_index=frame_index,
        )

    @classmethod
    def from_media(cls, media: LazyImage | LazyVideoFrame) -> MediaInfo:
        """
        Create MediaInfo from either a LazyImage or LazyVideoFrame.

        This is a convenience method that automatically detects the media type
        and extracts the appropriate information.

        Args:
            media: Either a LazyImage or LazyVideoFrame instance

        Returns:
            MediaInfo with appropriate fields populated

        Raises:
            TypeError: If media is not a LazyImage or LazyVideoFrame
        """
        if isinstance(media, LazyVideoFrame):
            return cls.from_lazy_video_frame(media)
        if isinstance(media, LazyImage):
            return cls.from_lazy_image(media)
        raise TypeError(f"Expected LazyImage or LazyVideoFrame, got {type(media)}")


# Global cache for video metadata (extracted once per video file)
_video_info_cache: dict[str, VideoInfo] = {}


def _get_frame_size(frame: np.ndarray) -> int:
    """Get the size of a video frame in bytes."""
    return frame.nbytes


class VideoFrameCache:
    """
    Global LRU cache for lazy-loaded video frames.

    Similar to ImageCache but optimized for video access patterns.
    The cache is keyed by (video_path, frame_index, format, channels_first) tuples.

    Features:
        - Configurable maximum size in bytes
        - Thread-safe access with RLock
        - Prefetch support for sequential access patterns

    Examples:
        >>> VideoFrameCache.set_size(512 * 1024 * 1024)  # 512 MB
        >>> VideoFrameCache.clear()
        >>> VideoFrameCache.info()
    """

    _cache: LRUCache[tuple[str, int, str, bool], np.ndarray] = LRUCache(
        maxsize=_DEFAULT_CACHE_SIZE_BYTES, getsizeof=_get_frame_size
    )
    _lock = RLock()
    _video_readers: dict[str, Any] = {}  # Cached video reader handles

    @classmethod
    def set_size(cls, maxsize_bytes: int) -> None:
        """
        Set the maximum size in bytes for the video frame cache.

        When the cache exceeds this size, the least recently used frames are evicted.

        Args:
            maxsize_bytes: Maximum cache size in bytes. Set to 0 to disable caching.

        Example:
            >>> VideoFrameCache.set_size(512 * 1024 * 1024)  # Set cache to 512 MB
        """
        with cls._lock:
            new_cache: LRUCache[tuple[str, int, str, bool], np.ndarray] = LRUCache(
                maxsize=maxsize_bytes, getsizeof=_get_frame_size
            )
            if maxsize_bytes > 0:
                for key, value in cls._cache.items():
                    item_size = _get_frame_size(value)
                    if new_cache.currsize + item_size <= maxsize_bytes:
                        new_cache[key] = value
            cls._cache = new_cache

    @classmethod
    def get_size(cls) -> int:
        """
        Get the current cache size in bytes.

        Returns:
            Current cache size in bytes.
        """
        with cls._lock:
            return int(cls._cache.currsize)

    @classmethod
    def get_max_size(cls) -> int:
        """
        Get the maximum cache size in bytes.

        Returns:
            Maximum cache size in bytes.
        """
        with cls._lock:
            return int(cls._cache.maxsize)

    @classmethod
    def clear(cls) -> None:
        """
        Clear all cached video frames from memory.

        Example:
            >>> VideoFrameCache.clear()  # Free all cached video frame memory
        """
        with cls._lock:
            cls._cache.clear()
            cls._video_readers.clear()

    @classmethod
    def length(cls) -> int:
        """
        Get the number of frames currently cached.

        Returns:
            Number of cached frames.
        """
        with cls._lock:
            return len(cls._cache)

    @classmethod
    def info(cls) -> dict[str, int]:
        """
        Get information about the current cache state.

        Returns:
            A dictionary with:
            - 'count': Number of frames currently cached
            - 'current_size': Current cache size in bytes
            - 'max_size': Maximum cache size in bytes
        """
        with cls._lock:
            return {
                "count": len(cls._cache),
                "current_size": cls._cache.currsize,
                "max_size": cls._cache.maxsize,
            }

    @classmethod
    def prefetch(cls, video_path: str, frame_indices: list[int]) -> None:
        """
        Prefetch frames in background for sequential access optimization.

        Args:
            video_path: Path to the video file
            frame_indices: List of frame indices to prefetch
        """
        # Import cv2 lazily to avoid import errors if not installed
        try:
            import cv2
        except ImportError:
            return

        with cls._lock:
            cap = cv2.VideoCapture(video_path)
            try:
                for frame_idx in frame_indices:
                    cache_key = (video_path, frame_idx, "RGB", False)
                    if cache_key not in cls._cache:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                        ret, frame = cap.read()
                        if ret:
                            # Convert BGR to RGB
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            cls._cache[cache_key] = frame_rgb
            finally:
                cap.release()


def extract_video_info(video_path: str | Path) -> VideoInfo:
    """
    Extract metadata from a video file without loading frames.

    Uses OpenCV for efficient metadata extraction.

    Args:
        video_path: Path to the video file

    Returns:
        VideoInfo with all metadata populated

    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If file is not a valid video
    """
    import cv2

    video_path_str = str(video_path)

    if not Path(video_path_str).exists():
        raise FileNotFoundError(f"Video file not found: {video_path_str}")

    cap = cv2.VideoCapture(video_path_str)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path_str}")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0.0

        # Try to get codec information
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)]) if fourcc else None

        return VideoInfo(
            path=video_path_str,
            total_frames=total_frames,
            fps=fps,
            width=width,
            height=height,
            duration=duration,
            codec=codec,
        )
    finally:
        cap.release()


@dataclass
class LazyVideoFrame:
    """
    A wrapper class that holds a video path and frame index for lazy loading.

    Similar to LazyImage, but extracts a specific frame from a video file.
    The frame is only loaded when the `data` property is accessed.

    Attributes:
        video_path: Path to the video file
        frame_index: Zero-based index of the frame to load
        format: Color format for loading ("RGB", "BGR", etc.)
        channels_first: Whether to return data in (C, H, W) format

    Examples:
        >>> frame = LazyVideoFrame("/path/to/video.mp4", frame_index=42)
        >>> frame.video_path  # Returns path without loading
        >>> frame.frame_index
        >>> frame.data

    Properties:
        video_info: VideoInfo for the parent video (cached)
        width: Frame width
        height: Frame height
        data: numpy array of frame pixels (lazy loaded)
    """

    video_path: str | Path
    frame_index: int
    format: str = "RGB"
    channels_first: bool = False

    def __post_init__(self) -> None:
        # Ensure video_path is stored as a string for consistency
        if isinstance(self.video_path, Path):
            object.__setattr__(self, "video_path", str(self.video_path))

        if self.frame_index < 0:
            raise ValueError(
                f"frame_index must be non-negative, got {self.frame_index}. "
                "Frame indices are zero-based (0 is the first frame)."
            )

    def _cache_key(self) -> tuple[str, int, str, bool]:
        """Generate a cache key for this video frame configuration."""
        return str(self.video_path), self.frame_index, self.format.upper(), self.channels_first

    @cached_property
    def video_info(self) -> VideoInfo:
        """
        Get video metadata, extracted lazily and cached globally.

        The first access for a video path triggers extraction.
        Subsequent accesses (for any frame of the same video) use the cache.
        """
        video_path_str = str(self.video_path)
        if video_path_str not in _video_info_cache:
            _video_info_cache[video_path_str] = extract_video_info(video_path_str)
        return _video_info_cache[video_path_str]

    @property
    def width(self) -> int:
        """Frame width from video metadata."""
        return self.video_info.width

    @property
    def height(self) -> int:
        """Frame height from video metadata."""
        return self.video_info.height

    def _convert_frame_format(self, frame: np.ndarray, target_format: str) -> np.ndarray:
        """Convert BGR frame (from OpenCV) to the target format."""
        import cv2

        target_format = target_format.upper()

        if target_format == "BGR":
            return frame
        if target_format == "RGB":
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if target_format == "RGBA":
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        if target_format == "BGRA":
            return cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        if target_format in ("L", "GRAY"):
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        raise ValueError(f"Unsupported video frame format: {target_format!r}")

    @cachedmethod(
        cache=lambda _: VideoFrameCache._cache,
        key=lambda self: self._cache_key(),
        lock=lambda _: VideoFrameCache._lock,
    )
    def _load_data(self) -> np.ndarray:
        """Load the video frame from disk (cached via @cachedmethod)."""
        import cv2

        video_path_str = str(self.video_path)

        if not Path(video_path_str).exists():
            raise FileNotFoundError(f"Video file not found: {video_path_str}")

        cap = cv2.VideoCapture(video_path_str)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path_str}")

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Validate frame_index is within bounds
            if self.frame_index >= total_frames:
                raise ValueError(
                    f"Frame index {self.frame_index} is out of bounds for video '{video_path_str}' "
                    f"which has {total_frames} frames (valid indices: 0 to {total_frames - 1})."
                )

            cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
            ret, frame = cap.read()

            if not ret:
                raise ValueError(f"Could not read frame {self.frame_index} from video: {video_path_str}")

            # Convert to target format
            frame_converted = self._convert_frame_format(frame, self.format)

            # Handle channels-first format
            if self.channels_first and frame_converted.ndim == 3:
                frame_converted = frame_converted.transpose(2, 0, 1)

            return frame_converted
        finally:
            cap.release()

    @property
    def data(self) -> np.ndarray:
        """
        Load and return the frame data as a numpy array.

        The frame is loaded from the video file on first access and cached
        in a global LRU cache. Subsequent accesses return the cached data
        if available.

        Returns:
            numpy.ndarray: The frame data as a numpy array with shape:
                - (H, W, C) if channels_first is False
                - (C, H, W) if channels_first is True

        Raises:
            FileNotFoundError: If the video file does not exist
            ValueError: If the frame cannot be read
        """
        return self._load_data()

    def clear_cache(self) -> None:
        """Remove this frame from the cache to free memory."""
        with VideoFrameCache._lock:
            VideoFrameCache._cache.pop(self._cache_key(), None)

    @property
    def shape(self) -> tuple[int, ...]:
        """
        Get the shape of the frame data.

        Returns:
            tuple: Shape of the frame array. If channels_first is False: (H, W, C).
                   If channels_first is True: (C, H, W). For grayscale: (H, W).
        """
        return self.data.shape

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(video_path={self.video_path}, frame_index={self.frame_index})"

    def __fspath__(self) -> str:
        """Allow LazyVideoFrame to be used in os.path operations (returns video path)."""
        return str(self.video_path)


def clear_video_info_cache() -> None:
    """Clear the global video info cache."""
    _video_info_cache.clear()
