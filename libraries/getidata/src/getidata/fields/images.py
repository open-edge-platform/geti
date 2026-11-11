# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import types
import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union, get_args, get_origin

import numpy as np
import polars as pl

from getidata.fields.base import Field, T
from getidata.media import LazyImage
from getidata.type_registry import from_polars_data, to_numpy


@dataclass(frozen=True)
class TensorField(Field):
    """
    Represents a tensor field with semantic tags and data type information.

    This field handles n-dimensional tensor data by flattening it for storage
    and preserving shape information separately for reconstruction.

    Attributes:
        semantic: String tag describing the tensor's purpose
        dtype: Polars data type for tensor elements
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.UInt8)

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate Polars schema with separate columns for data and shape."""
        return {name: pl.List(self.dtype), name + "_shape": pl.List(pl.Int32())}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert tensor to flattened data and shape information."""
        numpy_value = to_numpy(value, self.dtype)

        schema = self.to_polars_schema("tensor")

        numpy_value_shape: Any | None = None
        if numpy_value is not None:
            numpy_value_shape = numpy_value.shape
            numpy_value = numpy_value.reshape(-1)

        return {
            name: pl.Series(name, [numpy_value], dtype=schema["tensor"]),
            name + "_shape": pl.Series(name + "_shape", [numpy_value_shape], dtype=schema["tensor_shape"]),
        }

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T:
        """Reconstruct tensor from flattened data using stored shape."""
        flat_data = df[name][row_index]
        shape = df[name + "_shape"][row_index]
        numpy_data = np.array(flat_data).reshape(shape) if flat_data is not None else None

        return from_polars_data(numpy_data, target_type)  # type: ignore


def tensor_field(dtype: Any, semantic: str = "default") -> Any:
    """
    Create a TensorField instance with the specified semantic tags and data type.

    Args:
        dtype: Polars data type for tensor elements
        semantic: String tag describing the tensor's purpose (optional)

    Returns:
        TensorField instance configured with the given parameters
    """
    return TensorField(semantic=semantic, dtype=dtype)


@dataclass(frozen=True)
class ImageField(Field):
    """
    Represents an image tensor field with format information.

    3D image data is stored internally in HWC (height, width, channels)
    format. Images without an explicit channel dimension (for example,
    grayscale images shaped as HW) are stored as-is in HW format.
    When channels_first is True, the user provides/receives CHW data for
    3D images, and this field handles the conversion to/from HWC for
    internal storage. 2D images are not transposed.

    Attributes:
        semantic: String tag describing the image's purpose
        dtype: Polars data type for pixel values
        format: Image color format (e.g., "RGB", "BGR", "RGBA")
        channels_first: Whether the user provides/receives CHW format
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.UInt8)
    format: str = "RGB"
    channels_first: bool = False

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate Polars schema with separate columns for data and shape."""
        return {name: pl.List(self.dtype), name + "_shape": pl.List(pl.Int32())}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert image tensor to flattened data."""
        numpy_value = to_numpy(value, self.dtype)

        if self.channels_first and numpy_value is not None and numpy_value.ndim == 3:
            # User provides CHW; store as HWC internally
            numpy_value = np.transpose(numpy_value, (1, 2, 0))

        schema = self.to_polars_schema("tensor")

        numpy_value_shape: Any | None = None
        if numpy_value is not None:
            numpy_value_shape = numpy_value.shape
            numpy_value = numpy_value.reshape(-1)

        return {
            name: pl.Series(name, [numpy_value], dtype=schema["tensor"]),
            name + "_shape": pl.Series(name + "_shape", [numpy_value_shape], dtype=schema["tensor_shape"]),
        }

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T:
        """Reconstruct image tensor, converting from internal HWC to CHW if needed."""
        flat_data = df[name][row_index]
        shape = df[name + "_shape"][row_index]
        numpy_data = np.array(flat_data).reshape(shape) if flat_data is not None else None

        if self.channels_first and numpy_data is not None and numpy_data.ndim == 3:
            # Stored as HWC; user expects CHW
            numpy_data = np.transpose(numpy_data, (2, 0, 1))

        return from_polars_data(numpy_data, target_type)  # type: ignore


def image_field(
    dtype: Any,
    format: str = "RGB",
    channels_first: bool = False,
    semantic: str = "default",
) -> Any:
    """
    Create an ImageField instance with the specified parameters.

    Args:
        dtype: Polars data type for pixel values
        format: Image color format (defaults to "RGB")
        semantic: String tag describing the image's purpose (optional)

    Returns:
        ImageField instance configured with the given parameters
    """
    return ImageField(semantic=semantic, dtype=dtype, format=format, channels_first=channels_first)


@dataclass(frozen=True)
class ImageBytesField(Field):
    """
    Represents an image field stored as bytes data.

    This field stores image data as encoded bytes (PNG, JPEG, BMP, etc.) and
    provides conversion capabilities to decode them into numpy arrays or encode
    numpy arrays into bytes format.

    Attributes:
        semantic: String tag describing the image's purpose
        format: Image encoding format (e.g., "PNG", "JPEG", "BMP"). If None,
                auto-detects format when decoding or defaults to PNG when encoding.
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.Binary, init=False)

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema for image bytes as binary data."""
        return {name: pl.Binary()}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert image data to bytes and store in Polars series."""
        numpy_value = to_numpy(value, pl.Binary)
        bytes_value = bytes(numpy_value) if numpy_value is not None else None
        return {name: pl.Series(name, [bytes_value], dtype=pl.Binary())}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T:
        """Reconstruct image from bytes data."""
        bytes_data = df[name][row_index]
        return from_polars_data(bytes_data, target_type)  # type: ignore


def image_bytes_field(semantic: str = "default") -> Any:
    """
    Create an ImageBytesField instance with the specified parameters.

    Args:
        semantic: String tag describing the image's purpose (optional)

    Returns:
        ImageBytesField instance configured with the given parameters
    """
    return ImageBytesField(semantic=semantic)


@dataclass
class ImageInfo:
    """Container for image metadata (width and height)."""

    width: int
    height: int


@dataclass(frozen=True)
class ImageInfoField(Field):
    """
    Represents image metadata (width, height) as a Polars struct.
    """

    semantic: str = "default"
    dtype: pl.DataType = field(
        default_factory=lambda: pl.Struct([pl.Field("width", pl.Int32()), pl.Field("height", pl.Int32())]), init=False
    )

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        return {
            name: pl.Struct(
                [
                    pl.Field("width", pl.Int32()),
                    pl.Field("height", pl.Int32()),
                ]
            )
        }

    def to_polars(self, name: str, value: ImageInfo | None) -> dict[str, pl.Series]:
        schema = self.to_polars_schema("info")
        if value is not None:
            data = [{"width": value.width, "height": value.height}]
        else:
            data = [None]
        return {name: pl.Series(name, data, dtype=schema["info"])}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type) -> ImageInfo | None:
        if not issubclass(target_type, ImageInfo):
            raise TypeError(f"Expected target_type to be ImageInfo, got {target_type}")
        struct_val = df[name][row_index]
        if struct_val is None:
            return None
        return ImageInfo(width=struct_val["width"], height=struct_val["height"])


def image_info_field(semantic: str = "default") -> Any:
    """
    Create an ImageInfoField instance for storing image width and height.

    Args:
        semantic: Optional string tag for disambiguation

    Returns:
        ImageInfoField instance configured with the given semantic tags
    """
    return ImageInfoField(semantic=semantic)


@dataclass(frozen=True)
class ImagePathField(Field):
    """
    Represents a field containing the file path to an image on disk.

    This field stores image file paths as strings and is typically used
    as input for lazy loading operations where images are loaded on-demand.

    When the target type is `LazyImage`, the field returns a LazyImage instance
    that provides lazy loading of the actual image data through its `data` property.

    Attributes:
        semantic: String tag describing the image path's purpose
        format: Image color format for LazyImage loading (e.g., "RGB", "BGR")
        channels_first: Whether LazyImage should return data in channels-first format

    Examples:
        Using with a string type:
            >>> class MySample(Sample):
            ...     image: str = image_path_field()
            ...
            >>> sample = MySample(image="/path/to/image.jpg")
            >>> sample.image  # Returns "/path/to/image.jpg"

        Using with LazyImage type for lazy loading:
            >>> class MySample(Sample):
            ...     image: LazyImage = image_path_field()
            ...
            >>> sample = MySample(image="/path/to/image.jpg")
            >>> sample.image.path  # Returns "/path/to/image.jpg"
            >>> sample.image.data  # Loads and returns numpy array
    """

    semantic: str = "default"
    format: str = "RGB"
    channels_first: bool = False
    dtype: pl.DataType = field(default_factory=pl.String, init=False)

    def coerce(self, value: Any, target_type: type) -> Any:
        """
        Coerce a value to the target type if possible.

        This method is called during Sample initialization to convert
        input values to the expected type. For ImagePathField, this allows
        passing a string path when the target type is LazyImage.

        Args:
            value: The input value to coerce
            target_type: The expected target type

        Returns:
            The coerced value, or the original value if no coercion is needed
        """

        if value is None:
            return None

        # Check if target type involves LazyImage (direct or in a union)
        should_convert_to_lazy = False

        if target_type is LazyImage or (isinstance(target_type, type) and issubclass(target_type, LazyImage)):
            should_convert_to_lazy = True
        else:
            # Check for Union types (e.g., str | Path | LazyImage)
            origin = get_origin(target_type)
            if origin in (Union, types.UnionType):
                type_args = get_args(target_type)
                # If LazyImage is in the union, convert string/Path to LazyImage
                if LazyImage in type_args:
                    should_convert_to_lazy = True

        if should_convert_to_lazy:
            if isinstance(value, str | Path):
                return LazyImage(path=str(value), format=self.format, channels_first=self.channels_first)
            if isinstance(value, LazyImage):
                return value

        return value

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema for string path column."""
        return {name: pl.String()}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert path string or LazyImage to Polars series."""
        if value is None:
            str_value = None
        elif isinstance(value, LazyImage):
            str_value = str(value.path)
        else:
            str_value = str(value)
        return {name: pl.Series(name, [str_value])}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type) -> Any:
        """Extract path string or LazyImage from Polars data."""

        data = df[name][row_index]
        if data is None:
            return None

        # Check if target type involves LazyImage (direct or in a union)
        should_return_lazy = False

        if target_type is LazyImage or (isinstance(target_type, type) and issubclass(target_type, LazyImage)):
            should_return_lazy = True
        else:
            # Check for Union types (e.g., str | Path | LazyImage)
            origin = get_origin(target_type)
            if origin in (Union, types.UnionType):
                type_args = get_args(target_type)
                # If LazyImage is in the union, return LazyImage
                if LazyImage in type_args:
                    should_return_lazy = True

        if should_return_lazy:
            return LazyImage(path=data, format=self.format, channels_first=self.channels_first)

        return target_type(data)


def image_path_field(
    semantic: str = "default",
    format: str = "RGB",
    channels_first: bool = False,
) -> Any:
    """
    Create an ImagePathField instance with the specified parameters.

    When used with a `LazyImage` type annotation, this field will return a LazyImage
    instance that provides lazy loading of the actual image data.

    Since LazyImage accepts str, Path, or LazyImage as input, you can wrap your
    string path in LazyImage() when constructing the sample for full type safety:

        >>> sample = MySample(image=LazyImage("/path/to/image.jpg"))

    Args:
        semantic: String tag describing the image path's purpose (optional)
        format: Image color format for LazyImage loading (e.g., "RGB", "BGR")
        channels_first: Whether LazyImage should return data in channels-first format

    Returns:
        ImagePathField instance configured with the given parameters

    Examples:
        Using with LazyImage type (recommended, type-safe):
            >>> class MySample(Sample):
            ...     image: LazyImage = image_path_field()
            ...
            >>> sample = MySample(image=LazyImage("/path/to/image.jpg"))
            >>> sample.image.path  # Returns the path string
            >>> sample.image.data  # Loads and returns numpy array

        Using with a string type (just stores the path as string):
            >>> class MySample(Sample):
            ...     image: str = image_path_field()

        With BGR format and channels-first:
            >>> class MySample(Sample):
            ...     image: LazyImage = image_path_field(format="BGR", channels_first=True)
    """
    return ImagePathField(semantic=semantic, format=format, channels_first=channels_first)


@dataclass(frozen=True)
class ImageCallableField(Field):
    """
    Represents a field that stores a callable which returns an image as a numpy array.

    This field is useful for lazy loading scenarios where images are generated
    or loaded on-demand. The callable should return a numpy array representing
    the image data when invoked.

    Attributes:
        semantic: String tag describing the callable's purpose
        format: Expected image color format (e.g., "RGB", "BGR", "RGBA")
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

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type) -> typing.Callable:  # noqa: ARG002
        """Extract callable from Polars dataframe."""
        value = df[name][row_index]
        if not callable(value) and value is not None:
            raise TypeError(f"Expected callable in column {name}, got {type(value)}")
        return value


def image_callable_field(format: str = "RGB", semantic: str = "default") -> Any:
    """
    Create an ImageCallableField instance for storing image-generating callables.

    Args:
        format: Expected image color format (defaults to "RGB")
        semantic: String tag describing the callable's purpose (optional)

    Returns:
        ImageCallableField instance configured with the given parameters
    """
    return ImageCallableField(semantic=semantic, format=format)
