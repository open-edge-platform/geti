# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import types
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Union, get_args, get_origin

import polars as pl

from getidata.fields.base import Field, T


class Subset(Enum):
    """Standard dataset subset values."""

    TRAINING = auto()
    VALIDATION = auto()
    TESTING = auto()
    UNASSIGNED = auto()


@dataclass()
class TileInfo:
    """Information about a single tile within a larger image or data."""

    source_sample_idx: int  # ID of the source image this tile comes from
    x: int  # Top-left x coordinate of the tile
    y: int  # Top-left y coordinate of the tile
    width: int  # Width of the tile
    height: int  # Height of the tile


@dataclass(frozen=True)
class TileField(Field):
    """
    Represents a tile field storing information about how data was tiled.

    This field contains information about the source data index and
    the tile's position and dimensions within the source data.

    Attributes:
        semantic: String tag describing the tile's purpose
    """

    semantic: str = "default"
    dtype: pl.DataType = field(
        default_factory=lambda: pl.Struct(
            [
                pl.Field("source_sample_idx", pl.Int32()),
                pl.Field("x", pl.Int32()),
                pl.Field("y", pl.Int32()),
                pl.Field("width", pl.Int32()),
                pl.Field("height", pl.Int32()),
            ]
        ),
        init=False,
    )

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate Polars schema for tile information."""
        return {
            name: pl.Struct(
                [
                    pl.Field("source_sample_idx", pl.Int32()),
                    pl.Field("x", pl.Int32()),
                    pl.Field("y", pl.Int32()),
                    pl.Field("width", pl.Int32()),
                    pl.Field("height", pl.Int32()),
                ]
            )
        }

    def to_polars(self, name: str, value: TileInfo | None) -> dict[str, pl.Series]:
        """Convert tile info to Polars series."""
        schema = self.to_polars_schema("tile")
        if value is not None:
            data = [
                {
                    "source_sample_idx": value.source_sample_idx,
                    "x": value.x,
                    "y": value.y,
                    "width": value.width,
                    "height": value.height,
                }
            ]
        else:
            data = [None]
        return {name: pl.Series(name, data, dtype=schema["tile"])}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type) -> TileInfo | None:
        """Convert Polars data back to TileInfo."""
        if not issubclass(target_type, TileInfo):
            raise TypeError(f"Expected target_type to be TileInfo, got {target_type}")
        struct_val = df[name][row_index]
        if struct_val is None:
            return None
        return TileInfo(
            source_sample_idx=struct_val["source_sample_idx"],
            x=struct_val["x"],
            y=struct_val["y"],
            width=struct_val["width"],
            height=struct_val["height"],
        )


def tile_field(semantic: str = "default") -> Any:
    """
    Create a TileField instance for storing tile information.

    Args:
        semantic: Optional string tag for disambiguation (defaults to "default")

    Returns:
        TileField instance configured with the given semantic tags
    """
    return TileField(semantic=semantic)


@dataclass(frozen=True)
class SubsetField(Field):
    """
    A field for storing subset information in a dataset.

    This field supports both Enum and string values for subsets, storing them
    as Polars categorical type for efficient memory usage and type safety.
    When using an Enum type, the field maintains type safety by ensuring values
    match the Enum. When using strings, any string value is accepted.

    Attributes:
        semantic: String tag for the field
        subset_type: Optional type hint for the subset values (Enum or str)
        categories: Optional list of valid category values, required for categorical type
    """

    semantic: str = "default"
    categories: list[str] | None = None
    dtype: pl.DataType = field(default_factory=pl.Categorical, init=False)

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """Generate schema with categorical type for subset values."""
        return {name: pl.Categorical()}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """Convert subset value to Polars categorical type.

        If value is an Enum, uses the enum name. Otherwise, uses string representation.
        """
        if value is None:
            polars_value = None
        elif isinstance(value, Enum):
            polars_value = value.name
        else:
            polars_value = str(value)

        # Create categorical series with predefined categories if available
        return {name: pl.Series(name, [polars_value], dtype=pl.Categorical())}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T:
        """Reconstruct subset value from Polars data.

        Converts categorical string back to Subset enum value, or None if missing.
        Handles Union types (e.g., Subset | None).
        """
        value = df[name][row_index]

        if value is None:
            return None  # type: ignore

        # Handle Union types (e.g., Subset | None)
        origin = get_origin(target_type)
        if isinstance(target_type, types.UnionType) or origin is Union:
            # Extract the Subset type from the union
            args = get_args(target_type)
            for arg in args:
                if arg is not type(None) and isinstance(arg, type) and issubclass(arg, Enum):
                    try:
                        return arg[value]  # type: ignore
                    except KeyError:
                        if issubclass(arg, Subset):
                            return arg.UNASSIGNED  # type: ignore
                        raise

        # Handle direct Enum types
        if isinstance(target_type, type) and issubclass(target_type, Enum):
            try:
                return target_type[value]  # type: ignore
            except KeyError:
                if issubclass(target_type, Subset):
                    return target_type.UNASSIGNED  # type: ignore
                raise

        return value  # type: ignore


def subset_field(semantic: str = "default") -> Any:
    """
    Create a SubsetField instance for storing dataset subset information.

    Args:
        semantic: String tag for the field (defaults to "default")

    Returns:
        SubsetField instance configured with the given parameters
    """
    return SubsetField(semantic=semantic)
