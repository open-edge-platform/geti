# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import polars as pl

from getidata.categories import Categories, MaskCategories
from getidata.fields.base import Field, T
from getidata.type_registry import from_polars_data, to_numpy


@dataclass(frozen=True)
class MaskField(Field):
    """
    Represents a mask tensor field for binary or indexed segmentation masks.

    Similar to TensorField but specialized for masks: handles single-channel
    2D arrays with no color format specification. Uses uint8 as the default
    data type suitable for binary masks, class masks, or instance masks.

    Attributes:
        semantic: String tag describing the mask purpose
        dtype: Polars data type for mask values (defaults to uint8)
        channels_first: Whether the mask uses channels-first format (C, H, W) vs channels-last (H, W, C)
        has_channels_dim: Whether the mask includes a channels dimension (e.g., (H, W, C) vs (H, W))
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.UInt8)
    channels_first: bool = False
    has_channels_dim: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not (self.dtype.is_(pl.Boolean) or self.dtype.is_unsigned_integer()):
            raise ValueError(
                "A mask field's dtype must be a polars Boolean or unsigned integer type (e.g. UInt8). This integer "
                "normally represents the index of a category, with reference to the mask categories of the dataset to "
                "which the sample is (or will be) appended."
            )

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate Polars schema with separate columns for data and shape."""
        return {name: pl.List(self.dtype), name + "_shape": pl.List(pl.Int32())}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert mask tensor to flattened data and shape information."""
        numpy_value = to_numpy(value, self.dtype)
        schema = self.to_polars_schema("mask")

        numpy_value_shape: Any | None = None
        if numpy_value is not None:
            if self.has_channels_dim:
                if self.channels_first:
                    numpy_value = numpy_value.squeeze(axis=0)
                else:
                    numpy_value = numpy_value.squeeze(axis=-1)
            numpy_value_shape = numpy_value.shape
            numpy_value = numpy_value.reshape(-1)

        return {
            name: pl.Series(name, [numpy_value], dtype=schema["mask"]),
            name + "_shape": pl.Series(name + "_shape", [numpy_value_shape], dtype=schema["mask_shape"]),
        }

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T:
        """Reconstruct mask tensor from flattened data using stored shape."""
        flat_data = df[name][row_index]
        shape = df[name + "_shape"][row_index]
        numpy_data = np.array(flat_data).reshape(shape) if flat_data is not None and shape is not None else None

        if numpy_data is not None and self.has_channels_dim:
            if self.channels_first:
                numpy_data = numpy_data[np.newaxis, ...]
            else:
                numpy_data = numpy_data[..., np.newaxis]

        return from_polars_data(numpy_data, target_type)  # type: ignore

    def get_expected_categories_type(self) -> type[Categories] | None:
        return MaskCategories


def mask_field(
    dtype: Any = pl.UInt8(),
    channels_first: bool = False,
    has_channels_dim: bool = False,
    semantic: str = "default",
) -> Any:
    """
    Create a MaskField instance with the specified parameters.

    Args:
        dtype: Polars data type for mask values (defaults to pl.UInt8())
        semantic: String tag describing the mask purpose (optional)

    Returns:
        MaskField instance configured with the given parameters
    """
    return MaskField(
        semantic=semantic,
        dtype=dtype,
        channels_first=channels_first,
        has_channels_dim=has_channels_dim,
    )


@dataclass(frozen=True)
class InstanceMaskField(Field):
    """
    Represents an instance mask tensor field for instance segmentation masks.

    Handles 3D tensor data of shape (N, H, W) where N is the number of instances,
    H and W are the mask height and width. Each mask is a binary mask representing
    a single instance. Unlike MaskField, this does not contain category information.

    Attributes:
        semantic: String tag describing the instance mask purpose
        dtype: Polars data type for mask values (defaults to bool for binary masks)
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.Boolean)

    def __post_init__(self) -> None:
        super().__post_init__()
        if not (self.dtype.is_(pl.Boolean) or self.dtype.is_unsigned_integer()):
            raise ValueError(
                "An instance mask field's dtype must be a polars Boolean or unsigned integer type (e.g. UInt8). This "
                "integer normally represents the index of a category, with reference to the mask categories of the "
                "dataset to which the sample is (or will be) appended."
            )

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate Polars schema with separate columns for data and shape."""
        return {name: pl.List(self.dtype), name + "_shape": pl.List(pl.Int32())}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert instance mask tensor to flattened data and shape information."""
        numpy_value = to_numpy(value, self.dtype)
        schema = self.to_polars_schema("mask")

        numpy_value_shape: Any | None = None
        if numpy_value is not None:
            numpy_value_shape = numpy_value.shape
            numpy_value = numpy_value.reshape(-1)

        return {
            name: pl.Series(name, [numpy_value], dtype=schema["mask"]),
            name + "_shape": pl.Series(name + "_shape", [numpy_value_shape], dtype=schema["mask_shape"]),
        }

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T:
        """Reconstruct instance mask tensor from flattened data using stored shape."""
        flat_data = df[name][row_index]
        shape = df[name + "_shape"][row_index]
        numpy_data = np.array(flat_data).reshape(shape) if flat_data is not None and shape is not None else None
        return from_polars_data(numpy_data, target_type)  # type: ignore

    def get_expected_categories_type(self) -> type[Categories] | None:
        return MaskCategories


def instance_mask_field(dtype: Any = pl.Boolean(), semantic: str = "default") -> Any:
    """
    Create an InstanceMaskField instance with the specified parameters.

    Args:
        dtype: Polars data type for mask values (defaults to pl.Boolean())
        semantic: String tag describing the instance mask purpose (optional)

    Returns:
        InstanceMaskField instance configured with the given parameters
    """
    return InstanceMaskField(semantic=semantic, dtype=dtype)


@dataclass(frozen=True)
class InstanceMaskCallableField(Field):
    """
    Represents a field that stores a callable which returns an instance mask as a numpy array.

    This field is useful for lazy loading scenarios where instance masks are generated
    or loaded on-demand. The callable should return a numpy array representing
    the instance mask data when invoked.

    Attributes:
        semantic: String tag describing the callable's purpose
        dtype: Polars data type for the mask values (e.g., pl.UInt8(), pl.Boolean())
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.Boolean)

    def __post_init__(self) -> None:
        super().__post_init__()
        if not (self.dtype.is_(pl.Boolean) or self.dtype.is_unsigned_integer()):
            raise ValueError(
                "An instance mask callable field's dtype must be a polars Boolean or unsigned integer type "
                "(e.g. UInt8). This integer normally represents the index of a category, with reference to the mask "
                "categories of the dataset to which the sample is (or will be) appended."
            )

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Return schema with Object type to store callable."""
        return {name: pl.Object()}

    def to_polars(self, name: str, value: Callable) -> dict[str, pl.Series]:
        """
        Store instance mask callable as Object in Polars series.

        The callable must return a 3D numpy array of shape (N, H, W) where:
        - N is the number of instances
        - H is the mask height
        - W is the mask width
        Each mask should be a binary mask for a single instance.
        """
        if not callable(value) and value is not None:
            raise TypeError(f"Expected callable, got {type(value)}")
        return {name: pl.Series(name, [value], dtype=pl.Object())}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type) -> Callable:  # noqa: ARG002
        """
        Extract instance mask callable from Polars dataframe.

        Returns a callable that produces a 3D numpy array of binary masks,
        one for each instance in the image.
        """
        value = df[name][row_index]
        if not callable(value) and value is not None:
            raise TypeError(f"Expected callable in column {name}, got {type(value)}")
        return value

    def get_expected_categories_type(self) -> type[Categories] | None:
        return MaskCategories


def instance_mask_callable_field(dtype: Any = pl.Boolean(), semantic: str = "default") -> Any:
    """
    Create an InstanceMaskCallableField for storing instance mask-generating callables.

    Args:
        dtype: Polars data type for mask values (defaults to pl.Boolean())
        semantic: String tag describing the instance mask purpose (optional)

    Returns:
        InstanceMaskCallableField instance configured with the given parameters

    Example:
        >>> def generate_masks():
        ...     # Example with 2 instances, 3x3 masks
        ...     return np.array([
        ...         [[1, 1, 0], [1, 1, 0], [0, 0, 0]],  # First instance
        ...         [[0, 0, 1], [0, 0, 1], [1, 1, 1]],  # Second instance
        ...     ], dtype=bool)
        >>> field = instance_mask_callable_field()
        >>> sample = Sample(instance_masks=generate_masks)
    """
    return InstanceMaskCallableField(semantic=semantic, dtype=dtype)


@dataclass(frozen=True)
class MaskCallableField(Field):
    """
    Represents a field that stores a callable which returns a mask as a numpy array.

    This field is useful for lazy loading scenarios where masks are generated
    or loaded on-demand. The callable should return a numpy array representing
    a single mask when invoked.

    Attributes:
        semantic: String tag describing the callable's purpose
        dtype: Polars data type for mask values (e.g., pl.UInt8(), pl.Boolean())
        categories_from: Optional name of another field from which to share categories.
            When set, this field will use the same categories as the referenced field.
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.UInt8)
    categories_from: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not (self.dtype.is_(pl.Boolean) or self.dtype.is_unsigned_integer()):
            raise ValueError(
                "A mask callable field's dtype must be a polars Boolean or unsigned integer type (e.g. UInt8). This "
                "integer normally represents the index of a category, with reference to the mask categories of the "
                "dataset to which the sample is (or will be) appended."
            )

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Return schema with Object type to store callable."""
        return {name: pl.Object()}

    def to_polars(self, name: str, value: Callable) -> dict[str, pl.Series]:
        """
        Store mask callable as Object in Polars series.

        The callable must return a 2D numpy array of shape (H, W) where:
        - H is the mask height
        - W is the mask width
        The array should be a binary or category mask.
        """
        if not callable(value) and value is not None:
            raise TypeError(f"Expected callable, got {type(value)}")
        return {name: pl.Series(name, [value], dtype=pl.Object())}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type) -> Callable:  # noqa: ARG002
        """
        Extract mask callable from Polars dataframe.

        Returns a callable that produces a 2D numpy array representing
        a binary or category mask.
        """
        value = df[name][row_index]
        if not callable(value) and value is not None:
            raise TypeError(f"Expected callable in column {name}, got {type(value)}")
        return value

    def get_expected_categories_type(self) -> type[Categories] | None:
        return MaskCategories


def mask_callable_field(
    dtype: Any = pl.Boolean(), semantic: str = "default", categories_from: str | None = None
) -> Any:
    """
    Create a MaskCallableField for storing mask-generating callables.

    Args:
        dtype: Polars data type for mask values (defaults to pl.Boolean())
        semantic: String tag describing the mask purpose (optional)
        categories_from: Optional name of another field from which to share categories.
            When set, this field will use the same categories as the referenced field,
            avoiding the need to specify duplicate categories.

    Returns:
        MaskCallableField instance configured with the given parameters

    Example:
        >>> def generate_mask():
        ...     # Example 3x3 mask
        ...     return np.array([[1, 1, 0], [1, 1, 0], [0, 0, 0]], dtype=bool)
        >>> field = mask_callable_field()
        >>> sample = Sample(mask=generate_mask)

        # Sharing categories with another field:
        >>> class_mask = mask_callable_field(semantic="class_mask")
        >>> instance_mask = mask_callable_field(semantic="instance_mask", categories_from="class_mask")
    """
    return MaskCallableField(semantic=semantic, dtype=dtype, categories_from=categories_from)
