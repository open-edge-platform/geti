# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
import polars as pl
from PIL import Image, ImageOps

from getidata.converters.base import Converter, MediaBridgeConverter, copy_columns_with_shape
from getidata.converters.registry import converter
from getidata.exif_utils import get_exif_orientation, get_oriented_size, has_nontrivial_exif_orientation
from getidata.fields import ImageBytesField
from getidata.fields.images import ImageCallableField, ImageField, ImageInfoField, ImagePathField
from getidata.schema import AttributeSpec
from getidata.type_registry import polars_to_numpy_dtype

# Mapping from numpy dtype to Polars dtype for image data.
# Used by converters that load/decode images to detect and preserve bit depth.
_NUMPY_TO_POLARS_DTYPE: dict[np.dtype, pl.DataType] = {
    np.dtype(np.uint8): pl.UInt8(),
    np.dtype(np.uint16): pl.UInt16(),
    np.dtype(np.uint32): pl.UInt32(),
    np.dtype(np.int8): pl.Int8(),
    np.dtype(np.int16): pl.Int16(),
    np.dtype(np.int32): pl.Int32(),
    np.dtype(np.float32): pl.Float32(),
    np.dtype(np.float64): pl.Float64(),
}


# EXIF Orientation tag id is re-exported from ``getidata.exif_utils``
# (see ``EXIF_ORIENTATION_TAG``). No local constant is needed.


@converter
class RedBlueColorConverter(Converter):
    """
    Converter that transforms RGB image format to BGR format and vice-versa.
    """

    input_image: AttributeSpec[ImageField]
    output_image: AttributeSpec[ImageField]

    def filter_output_spec(self) -> bool:
        """
        Check if input is RGB/BGR and configure output for BGR/RGB conversion.

        Returns:
            True if the converter should be applied (RGB to BGR/BGR to RGB), False otherwise
        """
        input_format = self.input_image.field.format
        output_format = self.output_image.field.format

        self.output_image = AttributeSpec(
            name=self.output_image.name,
            field=ImageField(
                semantic=self.input_image.field.semantic,
                dtype=self.input_image.field.dtype,
                channels_first=self.output_image.field.channels_first,
                format=self.output_image.field.format,
            ),
        )

        return (input_format == "RGB" and output_format == "BGR") or (input_format == "BGR" and output_format == "RGB")

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        input_column_name = self.input_image.name
        output_column_name = self.output_image.name

        input_shape_column_name = self.input_image.name + "_shape"
        output_shape_column_name = self.output_image.name + "_shape"

        expected_dtype = polars_to_numpy_dtype(self.input_image.field.dtype)

        def red_blue_swap(flat_data: np.ndarray, shape: tuple) -> np.ndarray:
            """Fast channel swap using numpy views and advanced indexing."""
            if len(shape) == 3:
                h, w, c = shape
                if c == 3:
                    # RGB/BGR swap: swap channels 0 and 2
                    reshaped = flat_data.reshape(h, w, c)
                    swapped = np.empty_like(reshaped)
                    swapped[..., 0] = reshaped[..., 2]
                    swapped[..., 1] = reshaped[..., 1]
                    swapped[..., 2] = reshaped[..., 0]
                    return swapped.reshape(-1)
            # Fallback for non-standard shapes - reverse all channels
            reshaped = flat_data.reshape(shape)
            swapped = reshaped[..., ::-1].copy()
            return swapped.reshape(-1)

        result_data = []
        for flat_list, shape_list in zip(df[input_column_name].to_list(), df[input_shape_column_name].to_list()):
            flat_data = np.array(flat_list, dtype=expected_dtype)
            shape = tuple(shape_list)
            swapped = red_blue_swap(flat_data, shape)
            result_data.append(swapped.tolist())

        return df.with_columns(
            pl.Series(output_column_name, result_data, dtype=pl.List(self.input_image.field.dtype)),
            pl.col(input_shape_column_name).alias(output_shape_column_name),
        )


@converter
class ImageDtypeConverter(Converter):
    """
    Convert image data between different data types with appropriate normalization.

    Supports the following conversions:

    - **Integer → Float**: Normalizes pixel values to [0.0, 1.0] by dividing
      by the maximum value of the source integer type (e.g., UInt8: /255, UInt16: /65535).
    - **Float → Integer**: Denormalizes by multiplying by the target integer type's
      maximum value, clamping, and rounding.
    - **Integer → Integer**: Rescales between integer ranges (e.g., UInt8 [0,255] →
      UInt16 [0,65535]) by normalizing to [0,1] then denormalizing to the target range.
    - **Float → Float**: Simple dtype cast (e.g., Float64 → Float32).
    """

    input_image: AttributeSpec[ImageField]
    output_image: AttributeSpec[ImageField]

    def filter_output_spec(self) -> bool:
        """
        Check if input and output dtypes differ, and configure the output specification.

        Returns:
            True if the converter should be applied (dtypes differ), False otherwise
        """
        self.output_image = AttributeSpec(
            name=self.output_image.name,
            field=ImageField(
                semantic=self.input_image.field.semantic,
                dtype=self.output_image.field.dtype,
                format=self.input_image.field.format,
                channels_first=self.output_image.field.channels_first,
            ),
        )
        return self.input_image.field.dtype != self.output_image.field.dtype

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert image data between dtypes with proper normalization.

        Args:
            df: Input DataFrame containing image data

        Returns:
            DataFrame with converted image data
        """
        input_column_name = self.input_image.name
        output_column_name = self.output_image.name

        input_shape_column_name = self.input_image.name + "_shape"
        output_shape_column_name = self.output_image.name + "_shape"

        src_dtype = self.input_image.field.dtype
        dst_dtype = self.output_image.field.dtype

        expr = self._build_conversion_expr(src_dtype, dst_dtype)

        return df.with_columns(
            pl.col(input_column_name).list.eval(expr).alias(output_column_name),
            pl.col(input_shape_column_name).alias(output_shape_column_name),
        )

    @staticmethod
    def _build_conversion_expr(src_dtype: pl.DataType, dst_dtype: pl.DataType) -> pl.Expr:
        """Build the Polars expression for the dtype conversion."""
        src_is_int = src_dtype.is_integer()
        dst_is_int = dst_dtype.is_integer()
        src_is_float = src_dtype.is_float()
        dst_is_float = dst_dtype.is_float()

        if src_is_int and dst_is_float:
            # Integer → Float: normalize to [0.0, 1.0]
            return (pl.element() / src_dtype.max()).cast(dst_dtype)

        if src_is_float and dst_is_int:
            # Float → Integer: denormalize from [0.0, 1.0], clamp, round
            return (pl.element() * dst_dtype.max()).round(0).clip(0, dst_dtype.max()).cast(dst_dtype)

        if src_is_int and dst_is_int:
            # Integer → Integer: rescale between ranges
            return (
                (pl.element() * (dst_dtype.max() / src_dtype.max())).round(0).clip(0, dst_dtype.max()).cast(dst_dtype)
            )

        # Float → Float: simple cast
        if src_is_float and dst_is_float:
            return pl.element().cast(dst_dtype)

        # Fallback: attempt a direct cast
        return pl.element().cast(dst_dtype)


@converter(lazy=True)
class ImagePathToImageConverter(MediaBridgeConverter):
    """
    Lazy converter that loads images from file paths.

    This converter reads image files from disk and converts them to tensor format.
    It's marked as lazy to defer the expensive I/O operation until the data
    is actually accessed.

    Uses OpenCV for faster image loading, with PIL as fallback.

    Supported output formats:
        - RGB: 3-channel color image in Red-Green-Blue order
        - BGR: 3-channel color image in Blue-Green-Red order (OpenCV default)
        - RGBA: 4-channel color image with alpha channel
        - GRAY: Single-channel grayscale image
    """

    input_path: AttributeSpec[ImagePathField]
    output_image: AttributeSpec[ImageField]

    # Supported output formats for this converter
    SUPPORTED_FORMATS = {"RGB", "BGR", "RGBA", "GRAY"}

    # OpenCV read flags for each format (combined with IMREAD_ANYDEPTH to preserve bit depth)
    _CV2_READ_FLAGS = {
        "RGB": cv2.IMREAD_COLOR | cv2.IMREAD_ANYDEPTH,
        "BGR": cv2.IMREAD_COLOR | cv2.IMREAD_ANYDEPTH,
        "RGBA": cv2.IMREAD_UNCHANGED,
        "GRAY": cv2.IMREAD_GRAYSCALE | cv2.IMREAD_ANYDEPTH,
    }

    # PIL target modes for each format
    _PIL_MODES = {
        "RGB": "RGB",
        "BGR": "RGB",  # Load as RGB, then swap channels
        "RGBA": "RGBA",
        "GRAY": "L",
    }

    def filter_output_spec(self) -> bool:
        """Configure output image specification based on input."""
        # Configure output specification - preserve the requested format
        output_format = self.output_image.field.format if self.output_image.field.format else "RGB"

        # Validate that the requested format is supported
        if output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported output format '{output_format}' for ImagePathToImageConverter. "
                f"Supported formats are: {', '.join(sorted(self.SUPPORTED_FORMATS))}."
            )

        # Use the requested output dtype if specified, otherwise default to UInt8.
        # The actual dtype will be updated at convert time based on the loaded image
        # to handle cases like 16-bit images (UInt16) automatically.
        output_dtype = self.output_image.field.dtype if self.output_image.field.dtype else pl.UInt8()

        self.output_image = AttributeSpec(
            name=self.output_image.name,
            field=ImageField(
                semantic=self.input_path.field.semantic,
                dtype=output_dtype,
                format=output_format,
                channels_first=self.output_image.field.channels_first,
            ),
        )
        return True

    def _load_image_opencv(self, path: str, output_format: str) -> np.ndarray | None:
        """
        Load an image using OpenCV and convert to the requested format.

        Args:
            path: Path to the image file
            output_format: Desired output format (RGB, BGR, RGBA, GRAY)

        Returns:
            Image as numpy array in the requested format, or None if loading failed
        """
        read_flag = self._CV2_READ_FLAGS[output_format]
        img_array = cv2.imread(path, read_flag)

        if img_array is None:
            return None

        # Handle format conversions
        if output_format == "RGB":
            # OpenCV loads as BGR, convert to RGB
            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        elif output_format == "BGR":
            # Already in BGR format, no conversion needed
            pass
        elif output_format == "RGBA":
            # Handle various source formats for RGBA output
            if len(img_array.shape) == 2:
                # Grayscale to RGBA
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGBA)
            elif img_array.shape[2] == 3:
                # BGR to RGBA (OpenCV loads as BGR)
                img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGBA)
            elif img_array.shape[2] == 4:
                # BGRA to RGBA
                img_array = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGBA)
        elif output_format == "GRAY" and len(img_array.shape) == 2:
            img_array = img_array[:, :, np.newaxis]

        # Note: EXIF orientation is handled deterministically by the caller
        # (``convert``), which routes EXIF-rotated images through the PIL path
        # (``ImageOps.exif_transpose``) regardless of OpenCV's build-time
        # auto-orientation behavior.
        return img_array

    def _load_image_pil(self, path: str, output_format: str) -> np.ndarray:
        """
        Load an image using PIL and convert to the requested format.

        Args:
            path: Path to the image file
            output_format: Desired output format (RGB, BGR, RGBA, GRAY)

        Returns:
            Image as numpy array in the requested format
        """
        target_mode = self._PIL_MODES[output_format]

        with Image.open(path) as raw_img:
            # Apply EXIF orientation so the returned array matches the
            # image's displayed orientation (consistent with LazyImage).
            img = ImageOps.exif_transpose(raw_img)
            # For 16-bit grayscale images, PIL uses mode 'I;16' or 'I'
            # Convert to target mode if needed, preserving bit depth
            if output_format == "GRAY" and img.mode in ("I;16", "I;16L", "I;16B"):
                # Preserve 16-bit depth for grayscale
                img_array = np.array(img, dtype=np.uint16)
            elif output_format == "GRAY" and img.mode == "I":
                # 32-bit integer images
                img_array = np.array(img, dtype=np.int32)
            else:
                source_img = img if img.mode == target_mode else img.convert(target_mode)
                img_array = np.array(source_img)

            # Handle BGR format (swap R and B channels)
            if output_format == "BGR":
                img_array = img_array[..., ::-1].copy()

            # Handle grayscale - ensure 3D shape (H, W, 1)
            if output_format == "GRAY" and len(img_array.shape) == 2:
                img_array = img_array[:, :, np.newaxis]

        return img_array

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert image paths to loaded image tensors and image info.

        Args:
            df: DataFrame containing image path column

        Returns:
            DataFrame with loaded image data, shape information, and image info
        """
        input_col = self.input_path.name
        output_col = self.output_image.name
        output_format = self.output_image.field.format

        # Load images from paths
        image_data: list[Any] = []
        image_shapes: list[list[int]] = []

        for path in df[input_col]:
            path_str = str(path)

            # For deterministic behavior across OpenCV builds (some builds
            # auto-apply EXIF orientation on JPEG, others don't), skip the
            # OpenCV fast path when the image has a non-identity EXIF
            # orientation and defer to the PIL path, which always applies
            # ``ImageOps.exif_transpose``.
            if has_nontrivial_exif_orientation(path_str):
                img_array = self._load_image_pil(path_str, output_format)
            else:
                # Try OpenCV first (faster)
                img_array = self._load_image_opencv(path_str, output_format)

                if img_array is None:
                    # Fallback to PIL for unsupported formats
                    img_array = self._load_image_pil(path_str, output_format)

            image_data.append(img_array.flatten())
            image_shapes.append(list(img_array.shape))

        # Detect actual dtype from loaded images and update the output field
        # to match. This handles 16-bit (uint16), 32-bit (float32), etc.
        if image_data:
            actual_numpy_dtype = image_data[0].dtype
            actual_polars_dtype = _NUMPY_TO_POLARS_DTYPE.get(actual_numpy_dtype)
            if actual_polars_dtype is not None and actual_polars_dtype != self.output_image.field.dtype:
                self.output_image = AttributeSpec(
                    name=self.output_image.name,
                    field=ImageField(
                        semantic=self.output_image.field.semantic,
                        dtype=actual_polars_dtype,
                        format=self.output_image.field.format,
                        channels_first=self.output_image.field.channels_first,
                    ),
                )

        # Create output DataFrame
        image_schema = self.output_image.field.to_polars_schema("image")

        result_df = df.clone()

        return result_df.with_columns(
            [
                pl.Series(output_col, image_data, dtype=image_schema["image"]),
                pl.Series(output_col + "_shape", image_shapes, dtype=image_schema["image_shape"]),
            ]
        )


@converter
class ImageToImageInfo(MediaBridgeConverter):
    """
    Lazy converter that loads images from file paths using Pillow.

    This converter reads image files from disk and converts them to tensor format.
    It's marked as lazy to defer the expensive I/O operation until the data
    is actually accessed.
    """

    input_image: AttributeSpec[ImageField]
    output_info: AttributeSpec[ImageInfoField]

    def filter_output_spec(self) -> bool:
        """Configure output image specification based on input."""
        # Configure output info specification
        self.output_info = AttributeSpec(
            name=self.output_info.name,
            field=ImageInfoField(
                semantic=self.input_image.field.semantic,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert image paths to loaded image tensors and image info.

        Args:
            df: DataFrame containing image path column

        Returns:
            DataFrame with loaded image data, shape information, and image info
        """
        input_col = self.input_image.name + "_shape"
        output_col = self.output_info.name

        # Set image info
        return df.with_columns(
            pl.struct(
                pl.col(input_col).list.get(0).alias("height"),
                pl.col(input_col).list.get(1).alias("width"),
            ).alias(output_col)
        )


@converter(lazy=True)
class ImageBytesToImageConverter(MediaBridgeConverter):
    """
    Lazy converter that decodes images from byte data.

    This converter takes encoded image bytes (PNG, JPEG, BMP, etc.) and decodes
    them to tensor format. It's marked as lazy to defer the expensive decoding
    operation until the data is actually accessed.
    """

    input_bytes: AttributeSpec[ImageBytesField]
    output_image: AttributeSpec[ImageField]

    def filter_output_spec(self) -> bool:
        """Configure output image specification based on input."""
        # Use the requested output dtype if specified, otherwise default to UInt8.
        # The actual dtype will be updated at convert time based on the decoded image.
        output_dtype = self.output_image.field.dtype if self.output_image.field.dtype else pl.UInt8()
        output_format = self.output_image.field.format if self.output_image.field.format else "RGB"

        # Configure output specification
        self.output_image = AttributeSpec(
            name=self.output_image.name,
            field=ImageField(
                semantic=self.input_bytes.field.semantic,
                dtype=output_dtype,
                format=output_format,
                channels_first=self.output_image.field.channels_first,
            ),
        )
        return True

    @staticmethod
    def _decode_image_bytes(image_bytes: bytes, output_format: str) -> np.ndarray:
        """
        Decode image bytes into a numpy array in the requested format.

        Handles 8-bit, 16-bit, and 32-bit images, preserving bit depth.

        Args:
            image_bytes: Raw image bytes (PNG, JPEG, etc.)
            output_format: Desired output format (RGB, BGR, RGBA, GRAY)

        Returns:
            Image as numpy array in the requested format
        """
        from io import BytesIO

        with Image.open(BytesIO(image_bytes)) as raw_img:
            # Apply EXIF orientation so decoded bytes match the image's
            # displayed orientation (consistent with file-based loading).
            img = ImageOps.exif_transpose(raw_img)
            is_high_depth = img.mode in ("I", "I;16", "I;16B", "I;16L", "I;16N")

            if is_high_depth and output_format in ("RGB", "BGR"):
                # For high bit-depth grayscale, stack into 3-channel preserving native dtype.
                # "I" mode -> int32, "I;16*" modes -> uint16.
                # All channels are identical, so no channel reordering is needed
                # even when the requested format is BGR.
                gray = np.array(img)
                img_array = np.stack([gray, gray, gray], axis=-1)
            elif is_high_depth and output_format == "GRAY":
                img_array = np.array(img)
                if img_array.ndim == 2:
                    img_array = img_array[:, :, np.newaxis]
            else:
                target_mode = output_format if output_format != "BGR" else "RGB"
                if target_mode == "GRAY":
                    target_mode = "L"
                converted_img = img if img.mode == target_mode else img.convert(target_mode)
                img_array = np.array(converted_img)

                if output_format == "BGR":
                    img_array = img_array[..., ::-1].copy()

                if output_format == "GRAY" and img_array.ndim == 2:
                    img_array = img_array[:, :, np.newaxis]

        return img_array

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert image bytes to decoded image tensors and image info.

        Args:
            df: DataFrame containing image bytes column

        Returns:
            DataFrame with decoded image data, shape information, and image info
        """
        input_col = self.input_bytes.name
        output_col = self.output_image.name
        output_format = self.output_image.field.format

        # Decode images from bytes
        image_data: list[np.ndarray] = []
        image_shapes: list[list[int]] = []

        for image_bytes in df[input_col]:
            img_array = self._decode_image_bytes(image_bytes, output_format)
            image_data.append(img_array.reshape(-1))
            image_shapes.append(list(img_array.shape))

        # Detect actual dtype from decoded images and update the output field
        if image_data:
            actual_numpy_dtype = image_data[0].dtype
            actual_polars_dtype = _NUMPY_TO_POLARS_DTYPE.get(actual_numpy_dtype)
            if actual_polars_dtype is not None and actual_polars_dtype != self.output_image.field.dtype:
                self.output_image = AttributeSpec(
                    name=self.output_image.name,
                    field=ImageField(
                        semantic=self.output_image.field.semantic,
                        dtype=actual_polars_dtype,
                        format=self.output_image.field.format,
                        channels_first=self.output_image.field.channels_first,
                    ),
                )

        # Create output DataFrame using the correct schema
        image_schema = self.output_image.field.to_polars_schema("image")

        result_df = df.clone()
        return result_df.with_columns(
            [
                pl.Series(output_col, image_data, dtype=image_schema["image"]),
                pl.Series(output_col + "_shape", image_shapes, dtype=image_schema["image_shape"]),
            ]
        )


@converter(lazy=True)
class ImageCallableToImageConverter(MediaBridgeConverter):
    """
    Lazy converter that executes callables to generate image data.

    This converter takes a callable stored in an ImageCallableField,
    executes it to get image data as a numpy array, and produces both
    ImageField and ImageInfoField outputs.
    """

    input_callable: AttributeSpec[ImageCallableField]
    output_image: AttributeSpec[ImageField]

    def filter_output_spec(self) -> bool:
        """Configure output image and info specifications based on input."""
        # Use the requested output dtype if specified, otherwise default to UInt8.
        # The actual dtype will be updated at convert time based on the callable's output.
        output_dtype = self.output_image.field.dtype if self.output_image.field.dtype else pl.UInt8()

        # Configure output image specification
        self.output_image = AttributeSpec(
            name=self.output_image.name,
            field=ImageField(
                semantic=self.input_callable.field.semantic,
                dtype=output_dtype,
                format=self.input_callable.field.format,  # Use format from callable field
                channels_first=self.output_image.field.channels_first,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Execute callables to generate image data and metadata.

        Args:
            df: DataFrame containing callable column

        Returns:
            DataFrame with image tensor data, shape information, and image info
        """
        input_col = self.input_callable.name
        output_col = self.output_image.name

        # Execute callables to generate image data
        image_data: list[Any] = []
        image_shapes: list[list[int]] = []

        for callable_obj in df[input_col]:
            try:
                # Execute the callable to get image array
                img_array = callable_obj()

                if img_array is None:
                    image_data.append(None)
                    image_shapes.append(None)
                    continue

                # Validate that we got a numpy array
                if not isinstance(img_array, np.ndarray):
                    raise TypeError(f"Callable must return numpy.ndarray, got {type(img_array)}")

                # Ensure the array has 3 dimensions for an image (height, width, channels)
                if len(img_array.shape) != 3:
                    raise ValueError(f"Image array must be 3D (height, width, channels), got shape {img_array.shape}")

                # Store flattened image data and shape
                image_data.append(img_array.flatten())
                image_shapes.append(list(img_array.shape))

            except Exception as e:
                raise RuntimeError(f"Error executing callable for image generation: {e}") from e

        # Detect actual dtype from callable outputs and update the output field
        # to match. This handles 16-bit (uint16), float32, etc.
        if image_data:
            # Find the first non-None entry to detect dtype
            first_data = next((d for d in image_data if d is not None), None)
            if first_data is not None:
                actual_numpy_dtype = first_data.dtype
                actual_polars_dtype = _NUMPY_TO_POLARS_DTYPE.get(actual_numpy_dtype)
                if actual_polars_dtype is not None and actual_polars_dtype != self.output_image.field.dtype:
                    self.output_image = AttributeSpec(
                        name=self.output_image.name,
                        field=ImageField(
                            semantic=self.output_image.field.semantic,
                            dtype=actual_polars_dtype,
                            format=self.output_image.field.format,
                            channels_first=self.output_image.field.channels_first,
                        ),
                    )

        # Create output DataFrame using the correct schema
        image_schema = self.output_image.field.to_polars_schema("image")

        result_df = df.clone()
        return result_df.with_columns(
            [
                pl.Series(output_col, image_data, dtype=image_schema["image"]),
                pl.Series(output_col + "_shape", image_shapes, dtype=image_schema["image_shape"]),
            ]
        )


@converter
class ChannelsFirstConverter(Converter):
    """
    Converter that updates the channels_first metadata for image fields.

    This converter handles the transition between channels-first (C, H, W) and
    channels-last (H, W, C) format specifications. The actual data transposition
    is handled by the ImageField.from_polars() method when data is accessed,
    so this converter only needs to update the field metadata.

    Channels-first format: (C, H, W) - commonly used in PyTorch
    Channels-last format: (H, W, C) - commonly used in TensorFlow and image libraries
    """

    input_image: AttributeSpec[ImageField]
    output_image: AttributeSpec[ImageField]

    def filter_output_spec(self) -> bool:
        """
        Check if channels_first conversion is needed and configure output.

        Returns:
            True if the converter should be applied (channels_first differs), False otherwise
        """
        input_channels_first = self.input_image.field.channels_first
        output_channels_first = self.output_image.field.channels_first

        self.output_image = AttributeSpec(
            name=self.output_image.name,
            field=ImageField(
                semantic=self.input_image.field.semantic,
                dtype=self.input_image.field.dtype,
                channels_first=output_channels_first,
                format=self.input_image.field.format,
            ),
        )

        # Apply converter only if channels_first status differs
        return input_channels_first != output_channels_first

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Update image field metadata for channels_first change.

        The actual transposition is handled by ImageField.from_polars(),
        so this just ensures the column names are properly mapped.
        """

        return copy_columns_with_shape(df, self.input_image.name, self.output_image.name)


@converter
class ImagePathToImageInfoConverter(MediaBridgeConverter):
    """
    Converter that reads image dimensions from file paths without loading pixel data.

    This is much more efficient than the alternative path of
    ImagePathField → ImageField → ImageInfoField, which requires loading
    the entire image into memory. This converter only reads image headers
    to extract width and height using PIL.

    Input: ImagePathField (path as String)
    Output: ImageInfoField (struct with width, height)
    """

    input_path: AttributeSpec[ImagePathField]
    output_info: AttributeSpec[ImageInfoField]

    def filter_output_spec(self) -> bool:
        """Configure output info specification based on input."""
        self.output_info = AttributeSpec(
            name=self.output_info.name,
            field=ImageInfoField(
                semantic=self.input_path.field.semantic,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Read image dimensions from file paths using PIL header-only reads.

        Args:
            df: DataFrame containing image path column

        Returns:
            DataFrame with ImageInfoField column containing width and height
        """
        input_col = self.input_path.name
        output_col = self.output_info.name

        widths: list[int] = []
        heights: list[int] = []

        for path in df[input_col]:
            if path is None:
                raise ValueError(
                    f"Encountered None path in column '{input_col}'. All image paths must be valid to read dimensions."
                )

            with Image.open(str(path)) as img:
                # Respect EXIF orientation so reported dimensions match the
                # image as displayed (and as loaded via LazyImage).
                w, h = img.size
                w, h = get_oriented_size(w, h, get_exif_orientation(img))
                widths.append(w)
                heights.append(h)

        return df.with_columns(
            pl.struct(
                pl.Series("width", widths, dtype=pl.Int32()),
                pl.Series("height", heights, dtype=pl.Int32()),
            ).alias(output_col),
        )


@dataclass(frozen=True)
class _ImagePathLoader:
    """Picklable callable that lazily loads an image from *path* on demand.

    Used in place of a locally-defined closure so that datasets containing this
    callable can be passed to ``torch.utils.data.DataLoader`` workers started
    with the ``spawn`` multiprocessing context, which requires every object
    reachable from the ``Dataset`` to be picklable. A closure defined inside a
    function is not picklable by the standard ``pickle`` module, whereas a
    module-level dataclass instance with simple attributes is.
    """

    path: str
    format: str

    def __call__(self) -> np.ndarray:
        from getidata.media import LazyImage

        return LazyImage(path=self.path, format=self.format).data


@converter
class ImagePathToImageCallableConverter(MediaBridgeConverter):
    """
    Converter that wraps ImagePathField as ImageCallableField.

    Creates a callable for each image path that loads the image on demand.
    This is useful for pipeline compatibility where a callable interface
    is expected rather than a file path.

    Input: ImagePathField (path as String)
    Output: ImageCallableField (callable that returns image data as numpy array)
    """

    input_path: AttributeSpec[ImagePathField]
    output_callable: AttributeSpec[ImageCallableField]

    def filter_output_spec(self) -> bool:
        """Configure output callable specification based on input."""
        self.output_callable = AttributeSpec(
            name=self.output_callable.name,
            field=ImageCallableField(
                semantic=self.input_path.field.semantic,
                format=self.input_path.field.format,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Wrap image paths as lazy-loading callables.

        Args:
            df: DataFrame containing image path column

        Returns:
            DataFrame with callable column that loads images on demand
        """
        input_col = self.input_path.name
        output_col = self.output_callable.name

        callables: list[Any] = []

        for path in df[input_col]:
            if path is None:
                callables.append(None)
                continue

            callables.append(_ImagePathLoader(str(path), self.input_path.field.format))

        return df.with_columns(pl.Series(output_col, callables, dtype=pl.Object()))
