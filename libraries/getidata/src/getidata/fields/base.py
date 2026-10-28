# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Base Field class implementations for various data types.

This module provides concrete field implementations that handle serialization
to/from Polars DataFrames for different data types commonly used in machine
learning and computer vision applications.
"""

from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass
from typing import Any, TypeVar

import numpy as np
import polars as pl

from getidata.categories import Categories

T = TypeVar("T")


class Field:
    """
    Base class for fields with semantic tags and Polars type mapping.

    This abstract base class defines the interface for all field types,
    providing methods for converting between Python objects and Polars
    DataFrame representations.

    Attributes:
        semantic: A string tag used for disambiguation when multiple fields
            of the same type exist (e.g., "default", "left", "right").
        categories_from: Optional name of another field from which to share categories.
            When set, this field will use the same categories as the referenced field,
            avoiding the need to specify duplicate categories. For example, in VOC format,
            both class_mask and instance_mask can share the same MaskCategories.
    """

    semantic: str
    dtype: pl.DataType
    categories_from: str | None = None

    def __post_init__(self):
        dtype = getattr(self, "dtype")
        if isinstance(dtype, type) and issubclass(dtype, pl.DataType):
            raise TypeError(
                f"dtype must be a Polars 'DataType' (instance), not a Polars 'DataTypeClass' (type). "
                f"Make sure your dtype declaration uses parentheses ({dtype.__name__}() instead of {dtype.__name__})"
            )
        if not isinstance(dtype, pl.DataType):
            raise TypeError(f"dtype must be a Polars 'DataType', got '{dtype.__name__}' instead.")

    def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
        """
        Generate Polars schema definition for this field.

        Args:
            name: The column name for this field

        Returns:
            Dictionary mapping column names to Polars data types

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement the to_polars_type method.")

    def to_polars(self, name: str, value: Any) -> dict[str, pl.Series]:
        """
        Convert the field value to Polars-compatible format.

        Args:
            name: The column name for this field
            value: The value to convert

        Returns:
            Dictionary mapping column names to Polars Series
        """
        return {name: pl.Series(name, [value])}

    def to_python_scalars(self, name: str, value: Any) -> dict[str, Any]:
        """
        Convert the field value to Python scalars suitable for batch Series construction.

        This method returns raw Python values (not wrapped in pl.Series) that can be
        collected into lists and then efficiently converted to pl.Series in bulk.
        The default implementation calls to_polars and extracts s[0] from each Series.
        Subclasses with expensive to_polars implementations should override this.

        Args:
            name: The column name for this field
            value: The value to convert

        Returns:
            Dictionary mapping column names to Python scalar values
        """
        series_map = self.to_polars(name, value)
        return {col_name: series[0] for col_name, series in series_map.items()}

    def from_polars(self, name: str, row_index: int, df: pl.DataFrame, target_type: type) -> Any:
        """
        Convert from Polars-compatible format back to the field's value.

        Args:
            name: The column name for this field
            row_index: The row index to extract
            df: The source DataFrame
            target_type: The target type to convert to

        Returns:
            The converted value in the target type
        """
        return target_type(df[name][row_index])

    def get_expected_categories_type(self) -> type[Categories] | None:
        """
        Return the expected type of the categories, e.g. LabelCategories for LabelField

        If None, no categories are expected.
        """

    def get_categories_from(self) -> str | None:
        """
        Return the name of the field from which to share categories.

        Returns None if this field doesn't share categories with another field.
        """
        return getattr(self, "categories_from", None)

    def __set_name__(self, _: Any, name: str):
        object.__setattr__(self, "_name", name)

    def __get__(self, instance: Any, _: Any):
        if instance is None:
            return self

        name = getattr(self, "_name")
        value = instance.evaluate_lazy_field(name)

        # Cache the value and set it as a real attribute
        setattr(instance, name, value)

        return value

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize this Field to a JSON-compatible dictionary.

        Automatically serializes all dataclass fields by introspection.

        Returns:
            Dictionary containing field type and parameters
        """

        field_dict = {
            "type": self.__class__.__name__,
        }

        # Use dataclass introspection to get all fields
        if is_dataclass(self):
            for dc_field in dataclass_fields(self):
                field_name = dc_field.name
                field_value = getattr(self, field_name)

                # Handle Polars data types
                if field_name == "dtype" and isinstance(field_value, pl.DataType):
                    field_dict[field_name] = str(field_value)
                # Handle regular serializable values
                else:
                    field_dict[field_name] = field_value

        return field_dict

    @classmethod
    def from_dict(cls, field_dict: dict[str, Any]) -> "Field":
        """
        Deserialize a Field from a JSON dictionary.

        Automatically reconstructs all dataclass fields by introspection.

        Args:
            field_dict: Dictionary containing field type and parameters

        Returns:
            Reconstructed Field instance
        """
        import getidata.fields as fields_module

        field_type = field_dict["type"]

        # Get the field class
        field_class = getattr(fields_module, field_type)

        # Prepare kwargs for field construction
        kwargs: dict[str, Any] = {}

        # Use dataclass introspection to get all expected fields
        if is_dataclass(field_class):
            for dc_field in dataclass_fields(field_class):
                if not dc_field.init:
                    continue  # Skip fields that are not in __init__

                field_name = dc_field.name

                # Skip if not in the serialized data
                if field_name not in field_dict:
                    continue

                field_value = field_dict[field_name]

                # Handle dtype reconstruction (Polars types)
                if field_name == "dtype" and isinstance(field_value, str):
                    # Try to resolve Polars data types
                    dtype_str = field_value.replace("()", "")
                    if hasattr(pl, dtype_str):
                        dtype_obj = getattr(pl, dtype_str)
                        if callable(dtype_obj):
                            kwargs[field_name] = dtype_obj()
                        else:
                            kwargs[field_name] = dtype_obj
                    else:
                        # Keep as string if we can't resolve it
                        kwargs[field_name] = field_value
                # Handle regular values
                else:
                    kwargs[field_name] = field_value

        return field_class(**kwargs)


def convert_numpy_object_array_to_series(data: np.ndarray) -> pl.Series:
    """
    Convert ragged numpy object arrays to Polars Series recursively.

    Handles nested object arrays containing variable-length lists.

    Example:
        >>> import numpy as np
        >>> ragged = np.array([
        ...     np.array([1, 2, 3]),
        ...     np.array([4, 5]),
        ...     np.array([6, 7, 8, 9])
        ... ], dtype=object)
        >>> series = convert_numpy_object_array_to_series(ragged)
        >>> print(series)
        shape: (3,)
        Series: '' [list[i64]]
        [
                [1, 2, 3]
                [4, 5]
                [6, 7, … 9]
        ]

        # Compare with direct conversion which results
        # into an object Series instead of a list Series:
        >>> direct = pl.Series(ragged)
        >>> print(direct)
        shape: (3,)
        Series: '' [o][object]
        [
                [1 2 3]
                [4 5]
                [6 7 8 9]
        ]
    """
    if data is not None and data.dtype == object:
        return pl.Series([convert_numpy_object_array_to_series(elem) for elem in data])
    return pl.Series(data)
