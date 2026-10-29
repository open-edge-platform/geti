# Copyright (C) 2022-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import Any

import polars as pl

from getidata.fields.base import Field, T
from getidata.type_registry import from_polars_data


@dataclass(frozen=True)
class NumericField(Field):
    """
    Represents a numeric value with arbitrary semantics.

    This field can be used, for instance, to represent attributes like area, depth, distance, score, etc.

    Attributes:
        semantic: A string tag describing the purpose of the value (e.g., "area")
        dtype: Polars data type for the numeric value (e.g., pl.Float32, pl.Int64)
        is_list: If True, the field can hold a list of numeric values instead of a single value.
    """

    semantic: str
    dtype: pl.DataType = field(default_factory=pl.Float32)
    is_list: bool = False

    @property
    def _pl_type(self) -> pl.DataType:
        return pl.List(self.dtype) if self.is_list else self.dtype

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        return {name: self._pl_type}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        # Wrap the provided value in a Series with proper dtype/list-typing
        return {name: pl.Series(name, [value], dtype=self._pl_type)}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T:
        data = df[name][row_index]
        if target_type is list:
            return list(data) if data is not None else None  # type: ignore[return-value]
        return from_polars_data(data, target_type)


def numeric_field(
    semantic: str,
    dtype: Any = pl.Float32(),
    is_list: bool = False,
) -> Any:
    """
    Create a NumericField instance.

    Args:
        semantic: String tag describing the field purpose
        dtype: Polars data type for the numeric value (e.g., pl.Float32, pl.Int64)
        is_list: Whether this field should be treated as a list type

    Returns:
        NumericField configured with the given parameters
    """
    return NumericField(dtype=dtype, is_list=is_list, semantic=semantic)


@dataclass(frozen=True)
class BoolField(Field):
    """
    Represents a boolean value with arbitrary semantics.

    This field can be used, for instance, to represent attributes like "is_occluded", "has_mask", "is_crowd", etc.

    Attributes:
        semantic: A string tag describing the purpose of the value (e.g., "is_occluded")
        is_list: If True, the field can hold a list of boolean values instead of a single value.
    """

    semantic: str
    is_list: bool = False
    dtype: pl.DataType = field(default_factory=pl.Boolean, init=False)

    @property
    def _pl_type(self) -> pl.DataType:
        return pl.List(self.dtype) if self.is_list else self.dtype

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        return {name: self._pl_type}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        return {name: pl.Series(name, [value], dtype=self._pl_type)}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T:
        data = df[name][row_index]
        if target_type is list:
            return list(data) if data is not None else None  # type: ignore[return-value]
        return from_polars_data(data, target_type)


def bool_field(
    semantic: str,
    is_list: bool = False,
) -> Any:
    """
    Create a BoolField instance.

    Args:
        semantic: String tag describing the field purpose
        is_list: Whether this field should be treated as a list type

    Returns:
        BoolField configured with the given parameters
    """
    return BoolField(semantic=semantic, is_list=is_list)


@dataclass(frozen=True)
class StringField(Field):
    """
    Represents a string value with arbitrary semantics.

    This field can be used, for instance, to represent attributes like "id", "source", "tags", etc...

    Attributes:
        semantic: A string tag describing the purpose of the value (e.g., "id")
        is_list: If True, the field can hold a list of string values instead of a single value.
    """

    semantic: str
    is_list: bool = False
    dtype: pl.DataType = field(default_factory=pl.String, init=False)

    @property
    def _pl_type(self) -> pl.DataType:
        return pl.List(self.dtype) if self.is_list else self.dtype

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        return {name: self._pl_type}

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        return {name: pl.Series(name, [value], dtype=self._pl_type)}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type[T]) -> T:
        data = df[name][row_index]
        if target_type is list:
            return list(data) if data is not None else None  # type: ignore[return-value]
        return from_polars_data(data, target_type)


def string_field(
    semantic: str,
    is_list: bool = False,
) -> Any:
    """
    Create a StringField instance.

    Args:
        semantic: String tag describing the field purpose
        is_list: Whether this field should be treated as a list type

    Returns:
        StringField configured with the given parameters
    """
    return StringField(semantic=semantic, is_list=is_list)
