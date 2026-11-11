# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field
from typing import Any

import polars as pl

from getidata.arrow_utils import numpy_to_nested_lists
from getidata.categories import BaseLabelCategories, Categories
from getidata.fields.base import Field, T, convert_numpy_object_array_to_series
from getidata.type_registry import (
    create_tv_tensors_bounding_boxes,
    from_polars_data,
    get_tv_tensors_canvas_size,
    to_numpy,
)


@dataclass(frozen=True)
class BBoxField(Field):
    """
    Represents a bounding box field with format and normalization options.

    Handles bounding box data with support for different coordinate formats
    and optional normalization to [0,1] range. Also supports torchvision
    tv_tensors.BoundingBoxes with automatic canvas_size preservation.

    Attributes:
        semantic: String tag describing the bounding box purpose
        dtype: Polars data type for coordinate values
        format: Coordinate format (e.g., "x1y1x2y2", "xywh")
        normalize: Whether coordinates are normalized to [0,1] range
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.Float32)
    format: str = "x1y1x2y2"
    normalize: bool = False

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema for bounding box as list of 4-element arrays.

        The associated ``*_canvas_size`` column used for tv_tensors.BoundingBoxes
        support is treated as an optional/auxiliary column and is therefore
        not part of the required schema. This keeps older DataFrames that only
        contain the bounding box column compatible.
        """
        return {
            name: pl.List(pl.Array(self.dtype, 4)),
        }

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert bounding box tensor to Polars list format.

        If value is a tv_tensors.BoundingBoxes, also stores canvas_size.
        """
        # Extract canvas_size if this is a tv_tensors.BoundingBoxes
        canvas_size = get_tv_tensors_canvas_size(value)

        numpy_value = to_numpy(value, self.dtype)

        if numpy_value is not None:
            data: Any = numpy_value.reshape(1, -1, 4)
        else:
            data = [None]

        # Store canvas_size as a list [height, width] or None
        canvas_size_data: Any = [list(canvas_size)] if canvas_size is not None else [None]

        return {
            name: pl.Series(
                name,
                data,
                dtype=pl.List(pl.Array(self.dtype, 4)),
            ),
            f"{name}_canvas_size": pl.Series(
                f"{name}_canvas_size",
                canvas_size_data,
                dtype=pl.List(pl.Int32()),
            ),
        }

    def to_python_scalars(self, name: str, value: Any) -> dict[str, Any]:
        """Fast path: return nested Python lists + canvas_size for batch construction.

        Avoids constructing per-item ``pl.Series`` with nested dtypes, which is
        expensive. Values collected this way can be bulk-converted via PyArrow
        downstream.
        """
        canvas_size = get_tv_tensors_canvas_size(value)
        numpy_value = to_numpy(value, self.dtype)
        bbox_value: Any = numpy_value.reshape(-1, 4).tolist() if numpy_value is not None else None
        canvas_value: Any = list(canvas_size) if canvas_size is not None else None
        return {name: bbox_value, f"{name}_canvas_size": canvas_value}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T | None:
        """Reconstruct bounding box tensor from Polars data.

        If target_type is tv_tensors.BoundingBoxes and canvas_size is available,
        returns a proper tv_tensors.BoundingBoxes instance.
        """
        polars_data = df[name][row_index]

        # Check if target type is tv_tensors.BoundingBoxes
        try:
            from torchvision import tv_tensors  # pyright: ignore[reportMissingImports]

            if target_type is tv_tensors.BoundingBoxes:
                # Try to get canvas_size from the stored column
                canvas_size_col = f"{name}_canvas_size"
                if canvas_size_col in df.columns:
                    canvas_size_data = df[canvas_size_col][row_index]
                    if canvas_size_data is not None:
                        # Handle list, tuple, pl.Series, and np.ndarray robustly
                        if hasattr(canvas_size_data, "to_list"):
                            canvas_size = tuple(canvas_size_data.to_list())
                        else:
                            canvas_size = tuple(canvas_size_data)
                        return create_tv_tensors_bounding_boxes(polars_data, canvas_size, self.format)  # type: ignore
                # If no canvas_size stored, raise an error
                raise ValueError(
                    "Cannot reconstruct tv_tensors.BoundingBoxes without canvas_size. "
                    "Use np.ndarray as target type or ensure canvas_size was stored."
                )
        except ImportError:
            pass

        return from_polars_data(polars_data, target_type)


def bbox_field(
    dtype: Any,
    format: str = "x1y1x2y2",
    normalize: bool = False,
    semantic: str = "default",
) -> Any:
    """
    Create a BBoxField instance with the specified parameters.

    Args:
        dtype: Polars data type for coordinate values
        format: Coordinate format (defaults to "x1y1x2y2")
        normalize: Whether coordinates are normalized (defaults to False)
        semantic: String tag describing the bounding box purpose (optional)

    Returns:
        BBoxField instance configured with the given parameters
    """
    return BBoxField(semantic=semantic, dtype=dtype, format=format, normalize=normalize)


@dataclass(frozen=True)
class RotatedBBoxField(Field):
    """
    Represents a rotated bounding box field with format and normalization options.

    Handles rotated bounding box data with support for different coordinate formats
    and optional normalization to [0,1] range. Stores all attributes (cx, cy, w, h, r)
    in one tensor similar to BBoxField.

    Attributes:
        semantic: String tag describing the rotated bounding box purpose
        dtype: Polars data type for coordinate values
        format: Coordinate format (e.g., "cxcywhr", "cxcywha" for angle in degrees)
        normalize: Whether coordinates are normalized to [0,1] range
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.Float32)
    format: str = "cxcywhr"
    normalize: bool = False

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema for rotated bounding box as list of 5-element arrays."""
        return {name: pl.List(pl.Array(self.dtype, 5))}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert rotated bounding box tensor to Polars list format."""
        numpy_value = to_numpy(value, self.dtype)

        if numpy_value is not None:
            data: Any = numpy_value.reshape(1, -1, 5)
        else:
            data = [None]

        return {
            name: pl.Series(
                name,
                data,
                dtype=pl.List(pl.Array(self.dtype, 5)),
            )
        }

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T | None:
        """Reconstruct rotated bounding box tensor from Polars data."""
        polars_data = df[name][row_index]
        return from_polars_data(polars_data, target_type)


def rotated_bbox_field(
    dtype: Any,
    format: str = "cxcywhr",
    normalize: bool = False,
    semantic: str = "default",
) -> Any:
    """
    Create a RotatedBBoxField instance with the specified parameters.

    Args:
        dtype: Polars data type for coordinate values
        format: Coordinate format (defaults to "cxcywhr" for cx,cy,w,h,rotation_radians)
        normalize: Whether coordinates are normalized (defaults to False)
        semantic: String tag describing the rotated bounding box purpose (optional)

    Returns:
        RotatedBBoxField instance configured with the given parameters
    """
    return RotatedBBoxField(semantic=semantic, dtype=dtype, format=format, normalize=normalize)


@dataclass(frozen=True)
class LabelField(Field):
    """
    Represents a unified label annotation field that supports both single and multi-label scenarios.

    This field automatically detects whether the input is a single label or multiple labels
    and handles the conversion accordingly:
    - Single labels: stored as Int32
    - Multi-labels: stored as List(Int32)
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.UInt8)
    multi_label: bool = False  # Flag to indicate if this field should handle multi-labels
    is_list: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.dtype.is_unsigned_integer():
            raise ValueError(
                "A label field's dtype must be a polars unsigned integer type (e.g. UInt8). This integer normally "
                "represents the index of a category, with reference to the label categories of the dataset to which "
                "the sample is (or will be) appended."
            )

    @property
    def _pl_type(self) -> pl.DataType:
        pl_type = self.dtype
        if self.multi_label:
            pl_type = pl.List(pl_type)
        if self.is_list:
            pl_type = pl.List(pl_type)
        return pl_type

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema based on whether this is single or multi-label."""
        return {name: self._pl_type}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert label(s) to Polars format for single or multi-label cases."""
        return {name: pl.Series(name, [value], dtype=self._pl_type)}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T | None:
        """Reconstruct label(s) from Polars data."""
        data = df[name][row_index]
        return from_polars_data(data, target_type)

    def get_expected_categories_type(self) -> type[Categories] | None:
        return BaseLabelCategories


def label_field(
    dtype: Any = pl.UInt8(),
    semantic: str = "default",
    multi_label: bool = False,
    is_list: bool = False,
) -> Any:
    """
    Create a LabelField instance with the specified parameters.

    Args:
        dtype: Polars data type for label values (defaults to pl.Int32())
        semantic: String tag describing the label purpose (optional)
        multi_label: Whether this field should handle multiple labels (defaults to False)
        is_list: Whether this field should be treated as a list type (defaults to False)

    Returns:
        LabelField instance configured with the given parameters
    """
    return LabelField(semantic=semantic, dtype=dtype, multi_label=multi_label, is_list=is_list)


@dataclass(frozen=True)
class PolygonField(Field):
    """
    Represents a polygon field with format and normalization options.

    Handles polygon data with support for different coordinate formats
    and optional normalization to [0,1] range. Polygons are stored as
    variable-length lists of coordinate pairs.

    Attributes:
        semantic: String tag describing the polygon purpose
        dtype: Polars data type for coordinate values
        format: Coordinate format (e.g., "xy", "yx")
        normalize: Whether coordinates are normalized to [0,1] range
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.Float32)
    format: str = "xy"
    normalize: bool = False

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema for polygon as list of coordinate values."""
        return {name: pl.List(pl.List(pl.Array(self.dtype, 2)))}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert polygon tensor to Polars list format."""
        numpy_value = to_numpy(value, self.dtype)

        series = convert_numpy_object_array_to_series(numpy_value)

        return {name: pl.Series(name, [series], dtype=pl.List(pl.List(pl.Array(self.dtype, 2))))}

    def to_python_scalars(self, name: str, value: Any) -> dict[str, Any]:
        """Convert polygon value to nested Python lists (fast path for batch construction)."""
        numpy_value = to_numpy(value, self.dtype)
        if numpy_value is None:
            return {name: None}
        return {name: numpy_to_nested_lists(numpy_value)}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T | None:
        """Reconstruct polygon tensor from Polars data."""
        polars_data = df[name][row_index]
        return from_polars_data(polars_data, target_type)


def polygon_field(
    dtype: Any,
    format: str = "xy",
    normalize: bool = False,
    semantic: str = "default",
) -> Any:
    """
    Create a PolygonField instance with the specified parameters.

    Args:
        dtype: Polars data type for coordinate values
        format: Coordinate format (defaults to "xy")
        normalize: Whether coordinates are normalized (defaults to False)
        semantic: String tag describing the polygon purpose (optional)

    Returns:
        PolygonField instance configured with the given parameters
    """
    return PolygonField(semantic=semantic, dtype=dtype, format=format, normalize=normalize)


@dataclass(frozen=True)
class KeypointsField(Field):
    """
    Represents a keypoints field with coordinate and visibility information.

    Handles keypoint data where each keypoint has (x, y) coordinates and a (v) visibility state.
    The keypoints are stored as triplets [[x1, y1, v1], [x2, y2, v2], ...] where each triplet
    contains x coordinate, y coordinate, and visibility (0=absent, 1=hidden, 2=visible).

    Attributes:
        semantic: String tag describing the keypoints purpose
        dtype: Polars data type for coordinate values
        normalize: Whether coordinates are normalized to [0,1] range
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.Float32)
    normalize: bool = False

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema for keypoints as list of 3-element arrays (x, y, visibility)."""
        return {name: pl.List(pl.Array(self.dtype, 3))}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert keypoints tensor to Polars list format."""
        numpy_value = to_numpy(value, self.dtype)

        if numpy_value is not None:
            data: Any = numpy_value.reshape(1, -1, 3)
        else:
            data = [None]

        return {
            name: pl.Series(
                name,
                data,
                dtype=pl.List(pl.Array(self.dtype, 3)),
            )
        }

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T | None:
        """Reconstruct keypoints tensor from Polars data."""
        polars_data = df[name][row_index]
        return from_polars_data(polars_data, target_type)

    def get_expected_categories_type(self) -> type[Categories] | None:
        """KeypointCategories are optional for KeypointsField so we return None here"""
        return None


def keypoints_field(
    dtype: Any = pl.Float32(),
    normalize: bool = False,
    semantic: str = "default",
) -> Any:
    """
    Create a KeypointsField instance with the specified parameters.

    Args:
        dtype: Polars data type for coordinate values (defaults to pl.Float32())
        normalize: Whether coordinates are normalized (defaults to False)
        semantic: String tag describing the keypoints purpose (optional)

    Returns:
        KeypointsField instance configured with the given parameters
    """
    return KeypointsField(semantic=semantic, dtype=dtype, normalize=normalize)


@dataclass(frozen=True)
class EllipseField(Field):
    """
    Represents an ellipse field with format and normalization options.

    Handles ellipse data with support for different coordinate formats
    and optional normalization to [0,1] range.

    Attributes:
        semantic: String tag describing the ellipses purpose
        dtype: Polars data type for coordinate values
        format: Coordinate format (e.g., "x1y1x2y2", "xywh")
        normalize: Whether coordinates are normalized to [0,1] range
    """

    semantic: str = "default"
    dtype: pl.DataType = field(default_factory=pl.Float32)
    format: str = "x1y1x2y2"
    normalize: bool = False

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema for ellipses as list of 4-element arrays."""
        return {name: pl.List(pl.Array(self.dtype, 4))}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert ellipse tensor to Polars list format."""
        numpy_value = to_numpy(value, self.dtype)

        if numpy_value is not None:
            data: Any = numpy_value.reshape(1, -1, 4)
        else:
            data = [None]

        return {
            name: pl.Series(
                name,
                data,
                dtype=pl.List(pl.Array(self.dtype, 4)),
            )
        }

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T | None:
        """Reconstruct an ellipse tensor from Polars data."""
        polars_data = df[name][row_index]
        return from_polars_data(polars_data, target_type)


def ellipse_field(
    dtype: Any = pl.Float32(),
    format: str = "x1y1x2y2",
    normalize: bool = False,
    semantic: str = "default",
) -> Any:
    """
    Create an EllipseField instance with the specified parameters.

    Args:
        dtype: Polars data type for coordinate values (defaults to pl.Float32())
        format: Coordinate format (defaults to "x1y1x2y2")
        normalize: Whether coordinates are normalized (defaults to False)
        semantic: String tag describing the ellipse purpose (optional)

    Returns:
        EllipseField instance configured with the given parameters
    """
    return EllipseField(semantic=semantic, dtype=dtype, format=format, normalize=normalize)


@dataclass(frozen=True)
class CaptionField(Field):
    """
    Represents a text caption field.

    Stores either a single caption string or a list of caption strings when
    is_list=True. Useful for tasks like image captioning, multi-caption datasets,
    or storing alternative textual descriptions.

    Attributes:
        semantic: String tag describing the caption's purpose
        is_list: Whether this field stores multiple captions (list[str])
    """

    semantic: str = "default"
    is_list: bool = False
    dtype: pl.DataType = field(default_factory=pl.Utf8, init=False)

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema for caption column (string or list of strings)."""
        dtype = pl.List(pl.Utf8()) if self.is_list else pl.Utf8()
        return {name: dtype}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert caption value(s) to Polars series."""
        dtype = pl.List(pl.Utf8()) if self.is_list else pl.Utf8()
        return {name: pl.Series(name, [value], dtype=dtype)}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T | None:
        """Reconstruct caption value(s) from Polars data."""
        data = df[name][row_index]
        if self.is_list and target_type is list:
            return list(data) if data is not None else None
        # Single caption
        return from_polars_data(data, target_type)


def caption_field(semantic: str = "default", is_list: bool = False) -> Any:
    """
    Create a CaptionField instance.

    Args:
        semantic: String tag describing the caption purpose (optional)
        is_list: Whether this field stores multiple captions (defaults to False)

    Returns:
        CaptionField instance configured with the given parameters
    """
    return CaptionField(semantic=semantic, is_list=is_list)
