# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Media converters for getidata.

This module provides converters that bridge between image-specific field types
(ImagePathField, ImageInfoField) and unified media field types (MediaPathField,
MediaInfoField), as well as converters that load images/video frames from
MediaPathField.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import polars as pl

from getidata.converters.base import MediaBridgeConverter
from getidata.converters.registry import converter
from getidata.fields.images import ImageCallableField, ImageField, ImageInfoField, ImagePathField
from getidata.fields.videos import MediaInfoField, MediaPathField, VideoFramePathField, VideoInfoField
from getidata.media import LazyImage, LazyVideoFrame, extract_video_info
from getidata.schema import AttributeSpec

if TYPE_CHECKING:
    import numpy as np


@converter(lazy=True)
class MediaPathToImageConverter(MediaBridgeConverter):
    """
    Lazy converter that loads images/video frames from MediaPathField to ImageField.

    Handles both standalone images and video frames uniformly:
    - For images (frame_index is None): loads using ImageCache
    - For video frames (frame_index is set): loads using VideoFrameCache

    This is the recommended converter for datasets using MediaPathField with
    the unified DetectionSample pattern.

    Input: MediaPathField (path + nullable frame_index)
    Output: ImageField (tensor data + shape)
    """

    input_media: AttributeSpec[MediaPathField]
    output_image: AttributeSpec[ImageField]

    # Supported output formats
    SUPPORTED_FORMATS = {"RGB", "BGR", "RGBA", "GRAY"}

    def filter_output_spec(self) -> bool:
        """Configure output image specification based on input."""
        output_format = self.output_image.field.format if self.output_image.field.format else "RGB"

        if output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported output format '{output_format}' for MediaPathToImageConverter. "
                f"Supported formats are: {', '.join(sorted(self.SUPPORTED_FORMATS))}."
            )

        output_dtype = self.output_image.field.dtype if self.output_image.field.dtype else pl.UInt8()

        self.output_image = AttributeSpec(
            name=self.output_image.name,
            field=ImageField(
                semantic=self.input_media.field.semantic,
                dtype=output_dtype,
                format=output_format,
                channels_first=self.output_image.field.channels_first,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Load images or video frames and convert to image tensors.

        Checks frame_index to determine whether to load as image or video frame.

        Args:
            df: DataFrame containing path and frame_index columns

        Returns:
            DataFrame with loaded image data and shape information
        """
        input_path_col = self.input_media.name
        input_frame_idx_col = f"{self.input_media.name}_frame_index"
        output_col = self.output_image.name
        output_shape_col = f"{self.output_image.name}_shape"
        output_format = self.output_image.field.format

        image_data: list[Any] = []
        image_shapes: list[list[int]] = []

        for path, frame_idx in zip(df[input_path_col], df[input_frame_idx_col]):
            if path is None:
                image_data.append(None)
                image_shapes.append([])
                continue

            try:
                if frame_idx is not None:
                    # Video frame - use LazyVideoFrame
                    # Always load as HWC for internal storage; ImageField.from_polars
                    # handles CHW conversion when channels_first=True.
                    media = LazyVideoFrame(
                        video_path=str(path),
                        frame_index=frame_idx,
                        format=output_format,
                        channels_first=False,
                    )
                else:
                    # Standalone image - use LazyImage
                    # Always load as HWC for internal storage.
                    media = LazyImage(
                        path=str(path),
                        format=output_format,
                        channels_first=False,
                    )

                img_array = media.data
                image_data.append(img_array.flatten().tolist())
                image_shapes.append(list(img_array.shape))
            except Exception:
                image_data.append(None)
                image_shapes.append([])

        return df.with_columns(
            pl.Series(output_col, image_data, dtype=pl.List(self.output_image.field.dtype)),
            pl.Series(output_shape_col, image_shapes, dtype=pl.List(pl.Int32())),
        )


@dataclass(frozen=True)
class _MediaPathLoader:
    """Picklable callable that lazily loads an image or video frame on demand.

    Used in place of a locally-defined closure so that datasets containing this
    callable can be passed to ``torch.utils.data.DataLoader`` workers started
    with the ``spawn`` multiprocessing context, which requires every object
    reachable from the ``Dataset`` to be picklable. A closure defined inside a
    function is not picklable by the standard ``pickle`` module, whereas a
    module-level dataclass instance with simple attributes is.
    """

    path: str
    frame_index: int | None
    format: str

    def __call__(self) -> np.ndarray:
        media = (
            LazyVideoFrame(video_path=self.path, frame_index=self.frame_index, format=self.format)
            if self.frame_index is not None
            else LazyImage(path=self.path, format=self.format)
        )
        return media.data


@converter
class MediaPathToImageCallableConverter(MediaBridgeConverter):
    """
    Converter that wraps MediaPathField as ImageCallableField.

    Creates a callable for each media item (image or video frame) that loads
    data on demand.

    Input: MediaPathField (path + nullable frame_index)
    Output: ImageCallableField (callable that returns image data)
    """

    input_media: AttributeSpec[MediaPathField]
    output_callable: AttributeSpec[ImageCallableField]

    def filter_output_spec(self) -> bool:
        """Configure output callable specification based on input."""
        self.output_callable = AttributeSpec(
            name=self.output_callable.name,
            field=ImageCallableField(
                semantic=self.input_media.field.semantic,
                format=self.input_media.field.format,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert media paths to image callables.

        Args:
            df: DataFrame containing path and frame_index columns

        Returns:
            DataFrame with callable column
        """
        input_path_col = self.input_media.name
        input_frame_idx_col = f"{self.input_media.name}_frame_index"
        output_col = self.output_callable.name

        callables: list[Any] = []

        for path, frame_idx in zip(df[input_path_col], df[input_frame_idx_col]):
            if path is None:
                callables.append(None)
                continue

            callables.append(_MediaPathLoader(str(path), frame_idx, self.input_media.field.format))

        return df.with_columns(pl.Series(output_col, callables, dtype=pl.Object()))


@converter
class MediaPathToImagePathConverter(MediaBridgeConverter):
    """
    Converter that converts MediaPathField to ImagePathField.

    Handles both standalone images and video frames:
    - For images (frame_index is None): casts the Categorical path to String.
    - For video frames (frame_index is set): extracts the frame from the video,
      saves it as a PNG image file, and outputs the saved image path.

    Extracted frames are saved to a deterministic path derived from the video
    file path and frame index, placed in a directory named
    ``{video_filename}_frames`` next to the video file.  The directory name
    includes the file extension to avoid collisions between videos with the
    same base name (e.g. ``clip.mp4`` vs ``clip.avi``).  For example, for
    ``/path/to/video.mp4`` and ``frame_index=42`` the extracted frame will be
    saved as::

        /path/to/video.mp4_frames/frame000042.png

    If the extracted image already exists on disk it is not re-extracted,
    making repeated conversions cheap.

    Input: MediaPathField (path as Categorical + nullable frame_index)
    Output: ImagePathField (path as String)
    """

    input_media: AttributeSpec[MediaPathField]
    output_path: AttributeSpec[ImagePathField]

    def filter_output_spec(self) -> bool:
        """Configure output path specification based on input."""
        self.output_path = AttributeSpec(
            name=self.output_path.name,
            field=ImagePathField(
                semantic=self.input_media.field.semantic,
                format=self.output_path.field.format,
                channels_first=self.output_path.field.channels_first,
            ),
        )
        return True

    @staticmethod
    def _extract_frame(
        video_path: str,
        frame_index: int,
    ) -> str:
        """Extract a video frame and save it as a PNG image file.

        Args:
            video_path: Path to the video file.
            frame_index: Zero-based frame index to extract.

        Returns:
            Path to the saved image file.
        """
        from pathlib import Path as _Path

        from PIL import Image as _PILImage

        video_p = _Path(video_path)
        output_dir = video_p.parent / f"{video_p.name}_frames"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"frame{frame_index:06d}.png"

        if output_path.exists():
            return str(output_path)

        # Always extract in RGB for saving to PNG via PIL, regardless of the
        # downstream output_format.  The saved file is format-agnostic;
        # consumers will re-load in whatever format they need.
        frame = LazyVideoFrame(
            video_path=video_path,
            frame_index=frame_index,
            format="RGB",
        )
        img_array = frame.data
        _PILImage.fromarray(img_array).save(output_path)
        return str(output_path)

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert MediaPathField to ImagePathField.

        For image rows (null frame_index) the path is cast from Categorical to
        String.  For video frame rows the frame is extracted from the video,
        saved as a PNG file, and the resulting image path is used.

        Args:
            df: DataFrame containing MediaPathField columns (path + frame_index)

        Returns:
            DataFrame with a String path column for ImagePathField
        """
        input_col = self.input_media.name
        frame_idx_col = f"{input_col}_frame_index"
        output_col = self.output_path.name

        has_frame_idx = frame_idx_col in df.columns
        has_video_frames = has_frame_idx and bool(df.select(pl.col(frame_idx_col).is_not_null().any()).item())

        if not has_video_frames:
            # Fast path — all rows are standalone images
            return df.with_columns(
                pl.col(input_col).cast(pl.String()).alias(output_col),
            )

        # Slow path — at least one video frame needs extraction
        output_paths: list[str | None] = []
        for path, frame_idx in zip(df[input_col], df[frame_idx_col]):
            if path is None:
                output_paths.append(None)
            elif frame_idx is not None:
                output_paths.append(self._extract_frame(str(path), int(frame_idx)))
            else:
                output_paths.append(str(path))

        return df.with_columns(
            pl.Series(output_col, output_paths, dtype=pl.String()),
        )


@converter
class MediaInfoToImageInfoConverter(MediaBridgeConverter):
    """
    Converter that extracts image info from MediaInfoField to ImageInfoField.

    MediaInfoField stores comprehensive metadata (width, height,
    fps, total_frames, duration, codec, frame_index) as a Polars struct.
    ImageInfoField stores only width and height as a simpler struct.

    This converter extracts the width and height fields from the MediaInfoField
    struct and produces an ImageInfoField struct.

    Input: MediaInfoField (struct with width, height, fps, ...)
    Output: ImageInfoField (struct with width, height)
    """

    input_info: AttributeSpec[MediaInfoField]
    output_info: AttributeSpec[ImageInfoField]

    def filter_output_spec(self) -> bool:
        """Configure output info specification based on input."""
        self.output_info = AttributeSpec(
            name=self.output_info.name,
            field=ImageInfoField(
                semantic=self.input_info.field.semantic,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Extract width and height from MediaInfoField struct to ImageInfoField struct.

        Args:
            df: DataFrame containing MediaInfoField column

        Returns:
            DataFrame with ImageInfoField column containing width and height
        """
        input_col = self.input_info.name
        output_col = self.output_info.name

        return df.with_columns(
            pl.struct(
                pl.col(input_col).struct.field("width").alias("width"),
                pl.col(input_col).struct.field("height").alias("height"),
            ).alias(output_col),
        )


@converter
class ImagePathToMediaPathConverter(MediaBridgeConverter):
    """
    Converter that promotes ImagePathField to MediaPathField.

    ImagePathField stores a simple String path. MediaPathField stores a
    Categorical path plus a nullable frame_index column. This converter
    casts the String path to Categorical and adds a null frame_index column,
    making image-only datasets compatible with the unified MediaPath format.

    Input: ImagePathField (path as String)
    Output: MediaPathField (path as Categorical + null frame_index)
    """

    input_path: AttributeSpec[ImagePathField]
    output_media: AttributeSpec[MediaPathField]

    def filter_output_spec(self) -> bool:
        """Configure output media path specification based on input."""
        self.output_media = AttributeSpec(
            name=self.output_media.name,
            field=MediaPathField(
                semantic=self.input_path.field.semantic,
                format=self.output_media.field.format,
                channels_first=self.output_media.field.channels_first,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Promote image path to media path with null frame_index.

        Args:
            df: DataFrame containing ImagePathField column

        Returns:
            DataFrame with MediaPathField columns (Categorical path + null frame_index)
        """
        input_col = self.input_path.name
        output_col = self.output_media.name
        frame_idx_col = f"{output_col}_frame_index"

        return df.with_columns(
            pl.col(input_col).cast(pl.Categorical()).alias(output_col),
            pl.lit(None, dtype=pl.UInt32()).alias(frame_idx_col),
        )


@converter
class VideoFramePathToMediaPathConverter(MediaBridgeConverter):
    """
    Converter that promotes VideoFramePathField to MediaPathField.

    VideoFramePathField stores a Categorical video path and a UInt32 frame_index.
    MediaPathField stores a Categorical path and a nullable UInt32 frame_index.

    Because both field types share the same columnar layout (Categorical path +
    UInt32 frame_index) the conversion is a simple column rename/alias.

    Input: VideoFramePathField (video path as Categorical + frame_index as UInt32)
    Output: MediaPathField (path as Categorical + frame_index as UInt32)
    """

    input_frame: AttributeSpec[VideoFramePathField]
    output_media: AttributeSpec[MediaPathField]

    def filter_output_spec(self) -> bool:
        """Configure output media path specification based on input."""
        self.output_media = AttributeSpec(
            name=self.output_media.name,
            field=MediaPathField(
                semantic=self.input_frame.field.semantic,
                format=self.output_media.field.format,
                channels_first=self.output_media.field.channels_first,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Promote video frame path columns to media path columns.

        Args:
            df: DataFrame containing VideoFramePathField columns

        Returns:
            DataFrame with MediaPathField columns (Categorical path + frame_index)
        """
        input_col = self.input_frame.name
        input_frame_idx_col = f"{input_col}_frame_index"
        output_col = self.output_media.name
        output_frame_idx_col = f"{output_col}_frame_index"

        return df.with_columns(
            pl.col(input_col).alias(output_col),
            pl.col(input_frame_idx_col).alias(output_frame_idx_col),
        )


@converter
class ImageInfoToMediaInfoConverter(MediaBridgeConverter):
    """
    Converter that promotes ImageInfoField to MediaInfoField.

    ImageInfoField stores a struct with {width, height}. MediaInfoField stores
    a richer struct with {width, height, fps, total_frames,
    duration, codec, frame_index}. This converter creates the MediaInfoField
    struct by copying width and height and filling video-specific fields with null.

    Input: ImageInfoField (struct with width, height)
    Output: MediaInfoField (struct with width, height, fps=null, ...)
    """

    input_info: AttributeSpec[ImageInfoField]
    output_info: AttributeSpec[MediaInfoField]

    def filter_output_spec(self) -> bool:
        """Configure output media info specification based on input."""
        self.output_info = AttributeSpec(
            name=self.output_info.name,
            field=MediaInfoField(
                semantic=self.input_info.field.semantic,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Promote image info to media info with null video-specific fields.

        Args:
            df: DataFrame containing ImageInfoField column

        Returns:
            DataFrame with MediaInfoField column
        """
        input_col = self.input_info.name
        output_col = self.output_info.name

        return df.with_columns(
            pl.struct(
                pl.col(input_col).struct.field("width").alias("width"),
                pl.col(input_col).struct.field("height").alias("height"),
                pl.lit(None, dtype=pl.Float32()).alias("fps"),
                pl.lit(None, dtype=pl.UInt32()).alias("total_frames"),
                pl.lit(None, dtype=pl.Float32()).alias("duration"),
                pl.lit(None, dtype=pl.String()).alias("codec"),
                pl.lit(None, dtype=pl.UInt32()).alias("frame_index"),
            ).alias(output_col),
        )


@converter
class VideoInfoToMediaInfoConverter(MediaBridgeConverter):
    """
    Converter that promotes VideoInfoField to MediaInfoField.

    VideoInfoField stores a struct with {path, total_frames, fps (Float64),
    width, height, duration (Float64), codec}.  MediaInfoField stores a struct
    with {width, height, fps (Float32), total_frames, duration (Float32),
    codec, frame_index}.

    This converter maps the common fields, casts fps/duration from Float64 to
    Float32, drops the ``path`` field (not part of MediaInfoField), and fills
    ``frame_index`` with null (VideoInfoField describes the whole video, not a
    specific frame).

    Input: VideoInfoField
    Output: MediaInfoField
    """

    input_info: AttributeSpec[VideoInfoField]
    output_info: AttributeSpec[MediaInfoField]

    def filter_output_spec(self) -> bool:
        """Configure output media info specification based on input."""
        self.output_info = AttributeSpec(
            name=self.output_info.name,
            field=MediaInfoField(
                semantic=self.input_info.field.semantic,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert VideoInfoField struct to MediaInfoField struct.

        Casts fps/duration from Float64 → Float32 and adds a null frame_index.

        Args:
            df: DataFrame containing VideoInfoField column

        Returns:
            DataFrame with MediaInfoField column
        """
        input_col = self.input_info.name
        output_col = self.output_info.name

        return df.with_columns(
            pl.struct(
                pl.col(input_col).struct.field("width").alias("width"),
                pl.col(input_col).struct.field("height").alias("height"),
                pl.col(input_col).struct.field("fps").cast(pl.Float32()).alias("fps"),
                pl.col(input_col).struct.field("total_frames").alias("total_frames"),
                pl.col(input_col).struct.field("duration").cast(pl.Float32()).alias("duration"),
                pl.col(input_col).struct.field("codec").alias("codec"),
                pl.lit(None, dtype=pl.UInt32()).alias("frame_index"),
            ).alias(output_col),
        )


@converter
class MediaInfoToVideoInfoConverter(MediaBridgeConverter):
    """
    Converter that demotes MediaInfoField to VideoInfoField.

    MediaInfoField stores {width, height, fps (Float32), total_frames,
    duration (Float32), codec, frame_index}.  VideoInfoField stores
    {path, total_frames, fps (Float64), width, height, duration (Float64),
    codec}.

    This converter maps the common fields, casts fps/duration from Float32 to
    Float64, and fills ``path`` with null (the video path is not tracked in
    MediaInfoField).  The ``frame_index`` field is dropped since VideoInfoField
    describes the whole video.

    Input: MediaInfoField
    Output: VideoInfoField
    """

    input_info: AttributeSpec[MediaInfoField]
    output_info: AttributeSpec[VideoInfoField]

    def filter_output_spec(self) -> bool:
        """Configure output video info specification based on input."""
        self.output_info = AttributeSpec(
            name=self.output_info.name,
            field=VideoInfoField(
                semantic=self.input_info.field.semantic,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert MediaInfoField struct to VideoInfoField struct.

        Casts fps/duration from Float32 → Float64 and adds a null path.

        Args:
            df: DataFrame containing MediaInfoField column

        Returns:
            DataFrame with VideoInfoField column
        """
        input_col = self.input_info.name
        output_col = self.output_info.name

        return df.with_columns(
            pl.struct(
                pl.lit(None, dtype=pl.String()).alias("path"),
                pl.col(input_col).struct.field("total_frames").alias("total_frames"),
                pl.col(input_col).struct.field("fps").cast(pl.Float64()).alias("fps"),
                pl.col(input_col).struct.field("width").alias("width"),
                pl.col(input_col).struct.field("height").alias("height"),
                pl.col(input_col).struct.field("duration").cast(pl.Float64()).alias("duration"),
                pl.col(input_col).struct.field("codec").alias("codec"),
            ).alias(output_col),
        )


@converter
class MediaPathToMediaInfoConverter(MediaBridgeConverter):
    """
    Converter that extracts media metadata from MediaPathField to MediaInfoField.

    Handles both standalone images and video frames uniformly:
    - For images (frame_index is None): reads image dimensions using PIL header-only
    - For video frames (frame_index is set): extracts video metadata (fps, total_frames,
      dimensions, duration, codec) using OpenCV

    This is analogous to ImagePathToImageInfoConverter but works with the unified
    MediaPathField and produces the richer MediaInfoField.

    Input: MediaPathField (path as Categorical + nullable frame_index)
    Output: MediaInfoField (struct with width, height, fps, total_frames, duration, codec, frame_index)
    """

    input_media: AttributeSpec[MediaPathField]
    output_info: AttributeSpec[MediaInfoField]

    def filter_output_spec(self) -> bool:
        """Configure output info specification based on input."""
        self.output_info = AttributeSpec(
            name=self.output_info.name,
            field=MediaInfoField(
                semantic=self.input_media.field.semantic,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Extract media metadata from file paths and optional frame indices.

        For images: reads width and height from the image header.
        For video frames: extracts video metadata (dimensions, fps, etc.)
        and includes the frame_index.

        Args:
            df: DataFrame containing MediaPathField columns

        Returns:
            DataFrame with MediaInfoField column
        """
        from pathlib import Path as _Path

        from PIL import Image as _PILImage

        input_col = self.input_media.name
        frame_idx_col = f"{input_col}_frame_index"
        output_col = self.output_info.name

        rows: list[dict[str, Any] | None] = []
        # Cache video metadata by path to avoid redundant I/O for frames
        # from the same video file.
        _video_info_cache: dict[str, Any] = {}

        for i in range(len(df)):
            path = df[input_col][i]
            frame_idx = df[frame_idx_col][i] if frame_idx_col in df.columns else None

            if path is None:
                rows.append(None)
                continue

            path_str = str(path)

            if frame_idx is not None:
                # Video frame — extract video metadata (cached per path)
                if path_str not in _video_info_cache:
                    try:
                        _video_info_cache[path_str] = extract_video_info(path_str)
                    except (FileNotFoundError, ValueError):
                        _video_info_cache[path_str] = None
                video_info = _video_info_cache[path_str]
                if video_info is None:
                    rows.append(None)
                    continue
                rows.append(
                    {
                        "width": video_info.width,
                        "height": video_info.height,
                        "fps": float(video_info.fps) if video_info.fps is not None else None,
                        "total_frames": video_info.total_frames,
                        "duration": float(video_info.duration) if video_info.duration is not None else None,
                        "codec": video_info.codec,
                        "frame_index": int(frame_idx),
                    }
                )
            else:
                # Standalone image — read dimensions only
                p = _Path(path_str)
                if not p.exists():
                    rows.append(None)
                    continue

                with _PILImage.open(path_str) as img:
                    from getidata.exif_utils import get_exif_orientation, get_oriented_size

                    w, h = img.size
                    # Respect EXIF orientation so reported dimensions match
                    # the image as displayed (and as loaded via LazyImage).
                    w, h = get_oriented_size(w, h, get_exif_orientation(img))

                rows.append(
                    {
                        "width": w,
                        "height": h,
                        "fps": None,
                        "total_frames": None,
                        "duration": None,
                        "codec": None,
                        "frame_index": None,
                    }
                )

        schema = pl.Struct(
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

        return df.with_columns(
            pl.Series(output_col, rows, dtype=schema),
        )
