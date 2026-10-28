# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Video frame converters for getidata.

This module provides converters for transforming video frame references
(VideoFramePathField, VideoFrameCallableField) into image tensors or callables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import polars as pl

from getidata.converters.base import MediaBridgeConverter
from getidata.converters.registry import converter
from getidata.fields.images import ImageCallableField, ImageField
from getidata.fields.videos import VideoFrameCallableField, VideoFramePathField
from getidata.media import LazyVideoFrame
from getidata.schema import AttributeSpec

if TYPE_CHECKING:
    import numpy as np


@converter(lazy=True)
class VideoFramePathToImageConverter(MediaBridgeConverter):
    """
    Lazy converter that loads video frames from VideoFramePathField to ImageField.

    Converts (video_path, frame_index) references to loaded image tensors.
    Uses VideoFrameCache for efficient caching.

    Input: VideoFramePathField (path + frame_index)
    Output: ImageField (tensor data + shape)

    Supported output formats:
        - RGB: 3-channel color image in Red-Green-Blue order
        - BGR: 3-channel color image in Blue-Green-Red order (OpenCV default)
        - RGBA: 4-channel color image with alpha channel
        - GRAY: Single-channel grayscale image
    """

    input_frame: AttributeSpec[VideoFramePathField]
    output_image: AttributeSpec[ImageField]

    # Supported output formats
    SUPPORTED_FORMATS = {"RGB", "BGR", "RGBA", "GRAY"}

    def filter_output_spec(self) -> bool:
        """Configure output image specification based on input."""
        output_format = self.output_image.field.format if self.output_image.field.format else "RGB"

        if output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported output format '{output_format}' for VideoFramePathToImageConverter. "
                f"Supported formats are: {', '.join(sorted(self.SUPPORTED_FORMATS))}."
            )

        output_dtype = self.output_image.field.dtype if self.output_image.field.dtype else pl.UInt8()

        self.output_image = AttributeSpec(
            name=self.output_image.name,
            field=ImageField(
                semantic=self.input_frame.field.semantic,
                dtype=output_dtype,
                format=output_format,
                channels_first=self.output_image.field.channels_first,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert video frame paths to loaded image tensors.

        Args:
            df: DataFrame containing video path and frame_index columns

        Returns:
            DataFrame with loaded image data and shape information
        """
        input_path_col = self.input_frame.name
        input_frame_idx_col = f"{self.input_frame.name}_frame_index"
        output_col = self.output_image.name
        output_shape_col = f"{self.output_image.name}_shape"
        output_format = self.output_image.field.format

        image_data: list[Any] = []
        image_shapes: list[list[int]] = []

        for path, frame_idx in zip(df[input_path_col], df[input_frame_idx_col]):
            if path is None or frame_idx is None:
                image_data.append(None)
                image_shapes.append([])
                continue

            # Use LazyVideoFrame for loading (which uses VideoFrameCache)
            lazy_frame = LazyVideoFrame(
                video_path=str(path),
                frame_index=frame_idx,
                format=output_format,
            )

            try:
                img_array = lazy_frame.data
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
class _VideoFramePathLoader:
    """Picklable callable that lazily loads a single video frame on demand.

    Used in place of a locally-defined closure so that datasets containing this
    callable can be passed to ``torch.utils.data.DataLoader`` workers started
    with the ``spawn`` multiprocessing context, which requires every object
    reachable from the ``Dataset`` to be picklable. A closure defined inside a
    function is not picklable by the standard ``pickle`` module, whereas a
    module-level dataclass instance with simple attributes is.
    """

    video_path: str
    frame_index: int
    format: str

    def __call__(self) -> np.ndarray:
        return LazyVideoFrame(
            video_path=self.video_path,
            frame_index=self.frame_index,
            format=self.format,
        ).data


@converter
class VideoFrameToImageCallableConverter(MediaBridgeConverter):
    """
    Converter that wraps VideoFramePathField as ImageCallableField.

    Creates a callable for each frame that loads data on demand.
    Useful for compatibility with existing image processing pipelines.

    Input: VideoFramePathField (path + frame_index)
    Output: ImageCallableField (callable that returns image data)
    """

    input_frame: AttributeSpec[VideoFramePathField]
    output_callable: AttributeSpec[ImageCallableField]

    def filter_output_spec(self) -> bool:
        """Configure output callable specification based on input."""
        self.output_callable = AttributeSpec(
            name=self.output_callable.name,
            field=ImageCallableField(
                semantic=self.input_frame.field.semantic,
                format=self.input_frame.field.format,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert video frame paths to image callables.

        Args:
            df: DataFrame containing video path and frame_index columns

        Returns:
            DataFrame with callable column
        """
        input_path_col = self.input_frame.name
        input_frame_idx_col = f"{self.input_frame.name}_frame_index"
        output_col = self.output_callable.name

        callables: list[Any] = []

        for path, frame_idx in zip(df[input_path_col], df[input_frame_idx_col]):
            if path is None or frame_idx is None:
                callables.append(None)
                continue

            callables.append(_VideoFramePathLoader(str(path), frame_idx, self.input_frame.field.format))

        return df.with_columns(pl.Series(output_col, callables, dtype=pl.Object()))


@converter
class VideoFrameCallableToImageCallableConverter(MediaBridgeConverter):
    """
    Converter that adapts VideoFrameCallableField to ImageCallableField.

    VideoFrameCallableField stores a callable that returns a video frame as a
    numpy array. This converter wraps it as an ImageCallableField, making video
    frame callables compatible with image processing pipelines.

    Input: VideoFrameCallableField (callable returning frame as numpy array)
    Output: ImageCallableField (callable returning image as numpy array)
    """

    input_callable: AttributeSpec[VideoFrameCallableField]
    output_callable: AttributeSpec[ImageCallableField]

    def filter_output_spec(self) -> bool:
        """Configure output callable specification based on input."""
        self.output_callable = AttributeSpec(
            name=self.output_callable.name,
            field=ImageCallableField(
                semantic=self.input_callable.field.semantic,
                format=self.input_callable.field.format,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Pass through video frame callables as image callables.

        Both field types store callables returning numpy arrays, so the
        data can be passed through directly.

        Args:
            df: DataFrame containing VideoFrameCallableField column

        Returns:
            DataFrame with ImageCallableField column
        """
        input_col = self.input_callable.name
        output_col = self.output_callable.name

        return df.with_columns(
            pl.col(input_col).alias(output_col),
        )
