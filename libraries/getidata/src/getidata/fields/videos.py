# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Video-related field definitions for getidata.

This module provides field types for storing video frame references and
metadata in Polars DataFrames, enabling lazy loading of video frames
similar to how ImagePathField works for images.
"""

from __future__ import annotations

import types
import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union, get_args, get_origin

import polars as pl

from getidata.fields.base import Field
from getidata.media import LazyImage, LazyVideoFrame, MediaInfo, VideoInfo


@dataclass(frozen=True)
class VideoFramePathField(Field):
    """
    Represents a field containing a reference to a specific frame in a video file.

    Stores both the video path and frame index. When the target type is
    `LazyVideoFrame`, it returns a lazy loader for memory-efficient access.

    Schema columns:
        - {name}: Video file path (String)
        - {name}_frame_index: Frame index within the video (UInt32)

    Attributes:
        semantic: String tag describing the frame's purpose
        format: Color format for LazyVideoFrame loading ("RGB", "BGR", etc.)
        channels_first: Whether LazyVideoFrame returns (C, H, W) format

    Examples:
        >>> class VideoSample(Sample):
        ...     frame: LazyVideoFrame = video_frame_path_field()
        ...
        >>> sample = VideoSample(
        ...     frame=LazyVideoFrame("/path/to/video.mp4", frame_index=100)
        ... )
        >>> sample.frame.data  # Loads frame 100
    """

    semantic: str = "default"
    format: str = "RGB"
    channels_first: bool = False
    dtype: pl.DataType = field(default_factory=pl.String, init=False)

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema with path and frame_index columns.

        Uses Categorical for the path column since video datasets typically
        have many frames from the same video, making deduplication beneficial.
        """
        return {
            name: pl.Categorical(),
            f"{name}_frame_index": pl.UInt32(),
        }

    def to_polars(self, name: str, value: LazyVideoFrame | tuple[Any, int] | None) -> dict[str, pl.Series]:
        if value is None:
            return {
                name: pl.Series(name, [None], dtype=pl.Categorical()),
                f"{name}_frame_index": pl.Series(f"{name}_frame_index", [None], dtype=pl.UInt32()),
            }

        if isinstance(value, LazyVideoFrame):
            return {
                name: pl.Series(name, [str(value.video_path)], dtype=pl.Categorical()),
                f"{name}_frame_index": pl.Series(f"{name}_frame_index", [value.frame_index], dtype=pl.UInt32()),
            }

        # Handle tuple (path, frame_index) input
        if isinstance(value, tuple) and len(value) == 2:
            path, frame_idx = value
            return {
                name: pl.Series(name, [str(path)], dtype=pl.Categorical()),
                f"{name}_frame_index": pl.Series(f"{name}_frame_index", [frame_idx], dtype=pl.UInt32()),
            }

        raise TypeError(f"Expected LazyVideoFrame or (path, frame_index) tuple, got {type(value)}")

    def from_polars(
        self, name: str, row_index: int, df: pl.DataFrame, target_type: type
    ) -> LazyVideoFrame | tuple[str, int] | None:
        """Reconstruct LazyVideoFrame from stored path and frame_index."""
        path = df[name][row_index]
        frame_index = df[f"{name}_frame_index"][row_index]

        if path is None:
            return None

        # Check if target type involves LazyVideoFrame
        should_return_lazy = self._should_return_lazy_video_frame(target_type)

        if should_return_lazy:
            return LazyVideoFrame(
                video_path=path,
                frame_index=frame_index,
                format=self.format,
                channels_first=self.channels_first,
            )

        # Return tuple if not expecting LazyVideoFrame
        return path, frame_index  # type: ignore

    def _should_return_lazy_video_frame(self, target_type: type) -> bool:
        """Check if target type expects a LazyVideoFrame."""
        if target_type is LazyVideoFrame or (isinstance(target_type, type) and issubclass(target_type, LazyVideoFrame)):
            return True

        # Check for Union types
        origin = get_origin(target_type)
        if origin in (Union, types.UnionType):
            type_args = get_args(target_type)
            if LazyVideoFrame in type_args:
                return True

        return False

    def coerce(self, value: Any, target_type: type) -> Any:  # noqa: ARG002
        """Coerce tuple (path, frame_idx) to LazyVideoFrame if needed."""
        if value is None:
            return None

        if isinstance(value, LazyVideoFrame):
            return value

        if isinstance(value, tuple) and len(value) == 2:
            path, frame_idx = value
            return LazyVideoFrame(
                video_path=str(path),
                frame_index=frame_idx,
                format=self.format,
                channels_first=self.channels_first,
            )

        return value


def video_frame_path_field(
    semantic: str = "default",
    format: str = "RGB",
    channels_first: bool = False,
) -> Any:
    """
    Create a VideoFramePathField for storing video frame references.

    This field stores a reference to a specific frame within a video file.
    When used with LazyVideoFrame type annotation, the field returns a
    LazyVideoFrame instance that provides lazy loading of frame data.

    Args:
        semantic: String tag describing the frame's purpose
        format: Color format for LazyVideoFrame loading ("RGB", "BGR", etc.)
        channels_first: Whether LazyVideoFrame should return (C, H, W) format

    Returns:
        VideoFramePathField instance

    Examples:
        >>> class VideoDetectionSample(Sample):
        ...     frame: LazyVideoFrame = video_frame_path_field()
        ...
        >>> sample = VideoDetectionSample(
        ...     frame=LazyVideoFrame("/video.mp4", frame_index=42)
        ... )
        >>> sample.frame.data  # Loads frame 42 lazily
    """
    return VideoFramePathField(semantic=semantic, format=format, channels_first=channels_first)


@dataclass(frozen=True)
class VideoInfoField(Field):
    """
    Represents video metadata as a Polars struct.

    Stores comprehensive video information including dimensions, fps,
    duration, and codec information.

    Schema:
        Struct with fields: path, total_frames, fps, width, height, duration, codec
    """

    semantic: str = "default"
    dtype: pl.DataType = field(
        default_factory=lambda: pl.Struct(
            [
                pl.Field("path", pl.String()),
                pl.Field("total_frames", pl.UInt32()),
                pl.Field("fps", pl.Float64()),
                pl.Field("width", pl.Int32()),
                pl.Field("height", pl.Int32()),
                pl.Field("duration", pl.Float64()),
                pl.Field("codec", pl.String()),
            ]
        ),
        init=False,
    )

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema for VideoInfo struct."""
        return {
            name: pl.Struct(
                [
                    pl.Field("path", pl.String()),
                    pl.Field("total_frames", pl.UInt32()),
                    pl.Field("fps", pl.Float64()),
                    pl.Field("width", pl.Int32()),
                    pl.Field("height", pl.Int32()),
                    pl.Field("duration", pl.Float64()),
                    pl.Field("codec", pl.String()),
                ]
            )
        }

    def to_polars(self, name: str, value: VideoInfo | None) -> dict[str, pl.Series]:
        """Convert VideoInfo to Polars struct."""
        schema = self.to_polars_schema(name)
        if value is not None:
            data = [
                {
                    "path": value.path,
                    "total_frames": value.total_frames,
                    "fps": value.fps,
                    "width": value.width,
                    "height": value.height,
                    "duration": value.duration,
                    "codec": value.codec,
                }
            ]
        else:
            data = [None]
        return {name: pl.Series(name, data, dtype=schema[name])}

    def from_polars(
        self,
        name: str,
        row_index: int,
        df: pl.DataFrame,
        target_type: type,  # noqa: ARG002
    ) -> VideoInfo | None:
        """Reconstruct VideoInfo from Polars struct."""
        struct_val = df[name][row_index]
        if struct_val is None:
            return None

        return VideoInfo(
            path=struct_val["path"],
            total_frames=struct_val["total_frames"],
            fps=struct_val["fps"],
            width=struct_val["width"],
            height=struct_val["height"],
            duration=struct_val["duration"],
            codec=struct_val.get("codec"),
        )


def video_info_field(semantic: str = "default") -> Any:
    """
    Create a VideoInfoField for storing video metadata.

    Args:
        semantic: String tag describing the video info's purpose

    Returns:
        VideoInfoField instance

    Examples:
        >>> class VideoSample(Sample):
        ...     video_info: VideoInfo | None = video_info_field()
    """
    return VideoInfoField(semantic=semantic)


@dataclass(frozen=True)
class MediaInfoField(Field):
    """
    Unified field for storing media metadata (both images and video frames).

    This field stores comprehensive metadata that works for both image files
    and video frames:
    - For images: width, height
    - For video frames: width, height, fps, total_frames, duration, codec, frame_index

    The field automatically detects whether the source is an image or video frame
    based on the presence of video-specific fields (fps, etc.).

    Schema columns (as a single Struct):
        - width: Frame/image width (Int32)
        - height: Frame/image height (Int32)
        - fps: Frames per second (Float32, nullable - None for images)
        - total_frames: Total frames in video (UInt32, nullable - None for images)
        - duration: Video duration in seconds (Float32, nullable - None for images)
        - codec: Video codec (String, nullable - None for images)
        - frame_index: Frame index in video (UInt32, nullable - None for images)

    Attributes:
        semantic: String tag describing the media info's purpose

    Examples:
        >>> class DetectionSample(Sample):
        ...     media: LazyImage | LazyVideoFrame = media_path_field()
        ...     media_info: MediaInfo = media_info_field()
        ...
        >>> # For images
        >>> sample.media_info.width, sample.media_info.height
        (1920, 1080)
        >>> sample.media_info.is_video_frame
        False
        >>>
        >>> # For video frames
        >>> sample.media_info.fps
        30.0
        >>> sample.media_info.frame_index
        42
    """

    semantic: str = "default"
    dtype: pl.DataType = field(
        default_factory=lambda: pl.Struct(
            [
                pl.Field("width", pl.Int32()),
                pl.Field("height", pl.Int32()),
                pl.Field("fps", pl.Float32()),
                pl.Field("total_frames", pl.UInt32()),
                pl.Field("duration", pl.Float32()),
                pl.Field("codec", pl.String()),
                pl.Field("frame_index", pl.UInt32()),
            ]
        ),
        init=False,
    )

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema for MediaInfo struct."""
        return {
            name: pl.Struct(
                [
                    pl.Field("width", pl.Int32()),
                    pl.Field("height", pl.Int32()),
                    pl.Field("fps", pl.Float32()),
                    pl.Field("total_frames", pl.UInt32()),
                    pl.Field("duration", pl.Float32()),
                    pl.Field("codec", pl.String()),
                    pl.Field("frame_index", pl.UInt32()),
                ]
            )
        }

    def to_polars(self, name: str, value: MediaInfo | None) -> dict[str, pl.Series]:
        """Convert MediaInfo to Polars struct."""
        schema = self.to_polars_schema(name)
        if value is not None:
            data = [
                {
                    "width": value.width,
                    "height": value.height,
                    "fps": value.fps,
                    "total_frames": value.total_frames,
                    "duration": value.duration,
                    "codec": value.codec,
                    "frame_index": value.frame_index,
                }
            ]
        else:
            data = [None]
        return {name: pl.Series(name, data, dtype=schema[name])}

    def from_polars(
        self,
        name: str,
        row_index: int,
        df: pl.DataFrame,
        target_type: type,  # noqa: ARG002
    ) -> MediaInfo | None:
        """Reconstruct MediaInfo from Polars struct."""
        struct_val = df[name][row_index]
        if struct_val is None:
            return None

        return MediaInfo(
            width=struct_val["width"],
            height=struct_val["height"],
            fps=struct_val.get("fps"),
            total_frames=struct_val.get("total_frames"),
            duration=struct_val.get("duration"),
            codec=struct_val.get("codec"),
            frame_index=struct_val.get("frame_index"),
        )

    def coerce(self, value: Any, target_type: type) -> Any:  # noqa: ARG002
        """
        Coerce various input types to MediaInfo.

        Supports:
        - MediaInfo instances (pass through)
        - LazyImage instances (extract image info)
        - LazyVideoFrame instances (extract video frame info)
        - Dict with width/height keys (convert to MediaInfo)
        """
        if value is None:
            return None

        if isinstance(value, MediaInfo):
            return value

        if isinstance(value, LazyVideoFrame):
            return MediaInfo.from_lazy_video_frame(value)

        if isinstance(value, LazyImage):
            return MediaInfo.from_lazy_image(value)

        if isinstance(value, dict) and "width" in value and "height" in value:
            return MediaInfo.from_dict(value)

        return value


def media_info_field(semantic: str = "default") -> Any:
    """
    Create a MediaInfoField for storing unified media metadata.

    This field stores metadata that works for both images and video frames,
    providing a consistent interface regardless of media type.

    Args:
        semantic: String tag describing the media info's purpose

    Returns:
        MediaInfoField instance

    Examples:
        >>> class DetectionSample(Sample):
        ...     media: LazyImage | LazyVideoFrame = media_path_field()
        ...     media_info: MediaInfo = media_info_field()
        ...
        >>> # For images - only width/height are populated
        >>> img_sample = DetectionSample(
        ...     media=LazyImage("image.jpg"),
        ...     media_info=MediaInfo(width=1920, height=1080),
        ... )
        >>> img_sample.media_info.is_image
        True
        >>>
        >>> # For video frames - full metadata available
        >>> vid_sample = DetectionSample(
        ...     media=LazyVideoFrame("video.mp4", frame_index=42),
        ...     media_info=MediaInfo(
        ...         width=1920, height=1080,
        ...         fps=30.0, total_frames=1000,
        ...         duration=33.33, frame_index=42
        ...     ),
        ... )
        >>> vid_sample.media_info.is_video_frame
        True
        >>> vid_sample.media_info.fps
        30.0
    """
    return MediaInfoField(semantic=semantic)


@dataclass(frozen=True)
class VideoFrameCallableField(Field):
    """
    Represents a field storing a callable that returns a video frame.

    Similar to ImageCallableField, useful for custom frame loading logic
    or generated frame data.

    Attributes:
        semantic: String tag describing the callable's purpose
        format: Expected frame color format
    """

    semantic: str = "default"
    format: str = "RGB"
    dtype: pl.DataType = field(default_factory=pl.Object, init=False)

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Return schema with Object type to store callable."""
        return {name: pl.Object()}

    def to_polars(self, name: str, value: typing.Callable) -> dict[str, pl.Series]:
        """Store callable as Object in Polars series."""
        if not callable(value) and value is not None:
            raise TypeError(f"Expected callable, got {type(value)}")
        return {name: pl.Series(name, [value], dtype=pl.Object())}

    def from_polars(
        self,
        name: str,
        row_index: int,
        df: pl.DataFrame,
        target_type: type,  # noqa: ARG002
    ) -> typing.Callable:
        """Extract callable from Polars dataframe."""
        value = df[name][row_index]
        if not callable(value) and value is not None:
            raise TypeError(f"Expected callable in column {name}, got {type(value)}")
        return value


def video_frame_callable_field(
    format: str = "RGB",
    semantic: str = "default",
) -> Any:
    """
    Create a VideoFrameCallableField for callable frame loaders.

    Args:
        format: Expected frame color format (defaults to "RGB")
        semantic: String tag describing the callable's purpose

    Returns:
        VideoFrameCallableField instance
    """
    return VideoFrameCallableField(semantic=semantic, format=format)


@dataclass(frozen=True)
class MediaPathField(Field):
    """
    Unified field for storing references to either images or video frames.

    This field is the recommended approach when you need a single sample class
    that can hold either standalone images or video frames. It stores:
    - Media path (image file or video file)
    - Frame index (None for images, integer for video frames)

    The field automatically returns the appropriate lazy loader type based on
    whether frame_index is set.

    Schema columns:
        - {name}: Path to image or video file (String)
        - {name}_frame_index: Frame index (UInt32, nullable - None for images)

    Attributes:
        semantic: String tag describing the media's purpose
        format: Color format for lazy loading ("RGB", "BGR", etc.)
        channels_first: Whether to return data in (C, H, W) format

    Examples:
        >>> class DetectionSample(Sample):
        ...     media: LazyImage | LazyVideoFrame = media_path_field()
        ...     bboxes: np.ndarray | None = bbox_field(dtype=pl.Float32())
        ...
        >>> # Image sample
        >>> img_sample = DetectionSample(
        ...     media=LazyImage("/path/to/image.jpg"),
        ...     bboxes=np.array([[10, 20, 100, 200]]),
        ... )
        >>>
        >>> # Video frame sample
        >>> vid_sample = DetectionSample(
        ...     media=LazyVideoFrame("/path/to/video.mp4", frame_index=42),
        ...     bboxes=np.array([[50, 60, 150, 160]]),
        ... )
    """

    semantic: str = "default"
    format: str = "RGB"
    channels_first: bool = False
    dtype: pl.DataType = field(default_factory=pl.String, init=False)

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema with path and nullable frame_index columns.

        Uses Categorical for the path column since video datasets typically
        have many frames from the same video, making deduplication beneficial.
        """
        return {
            name: pl.Categorical(),
            f"{name}_frame_index": pl.UInt32(),  # Nullable: None = image, int = video frame
        }

    def to_polars(self, name: str, value: LazyImage | LazyVideoFrame | None) -> dict[str, pl.Series]:
        """Convert LazyImage or LazyVideoFrame to path and frame_index columns."""
        if value is None:
            return {
                name: pl.Series(name, [None], dtype=pl.Categorical()),
                f"{name}_frame_index": pl.Series(f"{name}_frame_index", [None], dtype=pl.UInt32()),
            }

        if isinstance(value, LazyVideoFrame):
            return {
                name: pl.Series(name, [str(value.video_path)], dtype=pl.Categorical()),
                f"{name}_frame_index": pl.Series(f"{name}_frame_index", [value.frame_index], dtype=pl.UInt32()),
            }

        # LazyImage or path string
        if isinstance(value, LazyImage):
            path = str(value.path)
        elif isinstance(value, (str, Path)):
            path = str(value)
        else:
            raise TypeError(f"Expected LazyImage, LazyVideoFrame, or path string, got {type(value)}")

        return {
            name: pl.Series(name, [path], dtype=pl.Categorical()),
            f"{name}_frame_index": pl.Series(f"{name}_frame_index", [None], dtype=pl.UInt32()),
        }

    def from_polars(
        self,
        name: str,
        row_index: int,
        df: pl.DataFrame,
        target_type: type,  # noqa: ARG002
    ) -> LazyImage | LazyVideoFrame | None:
        """Reconstruct LazyImage or LazyVideoFrame based on frame_index presence."""
        path = df[name][row_index]
        frame_index = df[f"{name}_frame_index"][row_index]

        if path is None:
            return None

        # If frame_index is set, it's a video frame; otherwise it's an image
        if frame_index is not None:
            return LazyVideoFrame(
                video_path=path,
                frame_index=frame_index,
                format=self.format,
                channels_first=self.channels_first,
            )

        return LazyImage(
            path=path,
            format=self.format,
            channels_first=self.channels_first,
        )

    def coerce(self, value: Any, target_type: type) -> Any:  # noqa: ARG002
        """Coerce various input types to LazyImage or LazyVideoFrame."""
        if value is None:
            return None

        if isinstance(value, (LazyImage, LazyVideoFrame)):
            return value

        if isinstance(value, (str, Path)):
            return LazyImage(path=str(value), format=self.format, channels_first=self.channels_first)

        if isinstance(value, tuple) and len(value) == 2:
            # (path, frame_index) tuple -> LazyVideoFrame
            path, frame_idx = value
            return LazyVideoFrame(
                video_path=str(path),
                frame_index=frame_idx,
                format=self.format,
                channels_first=self.channels_first,
            )

        return value


def media_path_field(
    semantic: str = "default",
    format: str = "RGB",
    channels_first: bool = False,
) -> Any:
    """
    Create a MediaPathField for storing either image or video frame references.

    This is the recommended field for any task where you want a single sample
    class that can hold both images and video frames.

    Args:
        semantic: String tag describing the media's purpose
        format: Color format for lazy loading ("RGB", "BGR", etc.)
        channels_first: Whether to return data in (C, H, W) format

    Returns:
        MediaPathField instance

    Examples:
        >>> class DetectionSample(Sample):
        ...     media: LazyImage | LazyVideoFrame = media_path_field(format="RGB")
        ...     bboxes: np.ndarray | None = bbox_field(dtype=pl.Float32())
        ...     labels: list[int] | None = label_field(dtype=pl.UInt8(), is_list=True)
        ...
        >>> # Works with both images and video frames
        >>> img_sample = DetectionSample(media=LazyImage("image.jpg"), ...)
        >>> vid_sample = DetectionSample(media=LazyVideoFrame("video.mp4", 42), ...)
    """
    return MediaPathField(semantic=semantic, format=format, channels_first=channels_first)
