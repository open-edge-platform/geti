# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Converter implementations for data transformation between different schemas.

This module contains concrete converter implementations that handle various
data transformations such as format conversions, dtype conversions, and
multi-field transformations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cache
from typing import TYPE_CHECKING, Any, TypeVar, cast, get_type_hints

import polars as pl
from typing_extensions import dataclass_transform

from getidata.fields.base import Field
from getidata.schema import AttributeSpec

if TYPE_CHECKING:
    from collections.abc import Callable


def list_eval_ref(
    list_col: str,
    ref_col: str,
    op: Callable[[pl.Expr, pl.Expr], pl.Expr],
) -> pl.Expr:
    """
    Apply an operation element-wise between a list column and a reference column.

    This helper function enables operations between elements of a list column
    and values from a reference column, returning a new list column with
    the results.

    Args:
        list_col: Name of the list column
        ref_col: Name of the reference column
        op: Operation function to apply between list elements and reference values

    Returns:
        Polars expression for the computed list column

    Note:
        See https://github.com/pola-rs/polars/issues/7210 for implementation details
    """
    return pl.concat_list(pl.struct(list_col, ref_col)).list.eval(
        op(
            pl.element().struct.field(list_col).explode(),
            pl.element().struct.field(ref_col),
        )
    )


TField = TypeVar("TField", bound=Field)


@dataclass_transform()
class Converter(ABC):
    """
    Base class for data converters with input/output specifications.

    Converters transform data between different field representations by
    implementing the convert() method and optionally filtering their
    applicability through filter_output_spec().
    """

    def __init__(self, **kwargs: Any):
        """
        Initialize converter with input and output AttributeSpec instances.

        Args:
            **kwargs: AttributeSpec instances for converter inputs/outputs
                     based on input_*/output_* class attributes
        """
        # Set all provided kwargs as instance attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    lazy: bool = False
    """
    Whether this converter performs lazy operations.

    Lazy converters defer expensive operations (like loading images from disk)
    until data is actually accessed. When a lazy converter is in the conversion
    path, all dependent converters must also be executed lazily.
    """

    @classmethod
    @cache
    def get_from_types(cls) -> dict[str, type[Field]]:
        """
        Extract input field types from input_* class attributes.

        Returns:
            Dictionary mapping input attribute names to their Field types
        """
        from_types: dict[str, type[Field]] = {}

        # Get type hints for the class
        hints = get_type_hints(cls)

        for attr_name, attr_type in hints.items():
            if attr_name.startswith("input_"):
                # Extract the Field type from AttributeSpec[FieldType] annotation
                if hasattr(attr_type, "__args__") and len(attr_type.__args__) > 0:
                    # Handle generic types like AttributeSpec[SomeField]
                    field_type = attr_type.__args__[0]
                else:
                    raise RuntimeError("Attributes must be annotated with AttributeSpec[FieldType]")

                from_types[attr_name] = field_type

        return from_types

    @classmethod
    @cache
    def get_to_types(cls) -> dict[str, type[Field]]:
        """
        Extract output field types from output_* class attributes.

        Returns:
            Dictionary mapping output attribute names to their Field types
        """
        to_types: dict[str, type[Field]] = {}

        # Get type hints for the class
        hints = get_type_hints(cls)

        for attr_name, attr_type in hints.items():
            if attr_name.startswith("output_"):
                # Extract the Field type from AttributeSpec[FieldType] annotation
                if hasattr(attr_type, "__args__") and len(attr_type.__args__) > 0:
                    # Handle generic types like AttributeSpec[SomeField]
                    field_type = attr_type.__args__[0]
                else:
                    raise RuntimeError("Attributes must be annotated with AttributeSpec[FieldType]")

                to_types[attr_name] = field_type

        return to_types

    @abstractmethod
    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert a DataFrame using the stored AttributeSpec instances.

        Args:
            df: Input DataFrame

        Returns:
            Converted DataFrame
        """

    def filter_output_spec(self) -> bool:
        """
        Filter and modify the converter's output specification in-place.

        This method allows converters to inspect and modify their output
        specifications based on input characteristics. It should return
        True if the converter can handle the given input/output combination.

        Returns:
            True if the converter is applicable, False otherwise
        """
        # Default implementation accepts all conversions
        # Subclasses should override for sophisticated filtering
        return True

    def get_input_attr_specs(self) -> list[AttributeSpec[Field]]:
        """
        Get the current input AttributeSpec instances from input_* attributes.

        Returns:
            List of input AttributeSpec instances currently configured on the converter
        """
        input_attr_specs: list[AttributeSpec[Field]] = []

        # Get the input attribute names from class type hints
        from_types = self.get_from_types()

        for attr_name in from_types:
            attr_spec = cast("AttributeSpec[Field]", getattr(self, attr_name))
            input_attr_specs.append(attr_spec)

        return input_attr_specs

    def get_output_attr_specs(self) -> list[AttributeSpec[Field]]:
        """
        Get the current output AttributeSpec instances from output_* attributes.

        Returns:
            List of output AttributeSpec instances currently configured on the converter
        """
        output_attr_specs: list[AttributeSpec[Field]] = []

        # Get the output attribute names from class type hints
        to_types = self.get_to_types()

        for attr_name in to_types:
            attr_spec = cast("AttributeSpec[Field]", getattr(self, attr_name))
            output_attr_specs.append(attr_spec)

        return output_attr_specs


class ConversionError(Exception):
    """Exception raised when conversion fails."""


class MediaBridgeConverter(Converter, ABC):
    """Base class for media bridge converters.

    Media bridge converters handle conversions between related media field
    types (e.g., MediaPathField ↔ ImagePathField, MediaInfoField ↔
    ImageInfoField, ImageCallableField → ImageField, etc.).

    These converters are always allowed even when ``direct_only=True``
    because they represent format-level narrowing or widening of media
    representations rather than semantic cross-field-type transformations.

    Subclass this instead of :class:`Converter` when the converter bridges
    between different representations of the same media content.
    """


class AttributeRemapperConverter(Converter):
    """
    Special converter for renaming/selecting attributes and dropping others.

    This converter is not registered with the converter registry but is used
    internally by find_conversion_path when attributes need to be renamed or deleted.
    It uses .select() to only keep the specified attributes with their new names,
    effectively handling both renaming and deletion in a single operation.
    """

    def __init__(self, attr_mappings: list[tuple[AttributeSpec, AttributeSpec]]):
        """
        Initialize the converter with a list of attribute mappings.

        Args:
            attr_mappings: List of tuples (from_attr_spec, to_attr_spec) defining
                          the attribute transformations. Only attributes in this
                          list will be kept in the output.
        """
        self.attr_mappings = attr_mappings

        # Calculate column mapping from attribute mappings
        self.column_map = {}
        for from_attr, to_attr in attr_mappings:
            # Get all column names for this field using to_polars_schema
            from_columns = list(from_attr.field.to_polars_schema(from_attr.name).keys())
            to_columns = list(to_attr.field.to_polars_schema(to_attr.name).keys())

            # Map each column from source to target
            for from_col, to_col in zip(from_columns, to_columns):
                self.column_map[from_col] = to_col

        # Dynamically set input_* and output_* attributes for get_from_types/get_to_types
        for i, (from_attr, to_attr) in enumerate(attr_mappings):
            setattr(self, f"input_{i}", from_attr)
            setattr(self, f"output_{i}", to_attr)

        super().__init__()

    @cache
    def get_from_types(self) -> dict[str, type[Field]]:
        """
        Extract input field types from input_* class attributes.

        Returns:
            Dictionary mapping input attribute names to their Field types
        """
        from_types: dict[str, type[Field]] = {}
        for i, (input_spec, _) in enumerate(self.attr_mappings):
            from_types[f"input_{i}"] = type(input_spec.field)

        return from_types

    @cache
    def get_to_types(self) -> dict[str, type[Field]]:
        """
        Extract output field types from output_* class attributes.

        Returns:
            Dictionary mapping output attribute names to their Field types
        """
        to_types: dict[str, type[Field]] = {}
        for i, (_, output_spec) in enumerate(self.attr_mappings):
            to_types[f"output_{i}"] = type(output_spec.field)

        return to_types

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Rename columns according to column_map and keep all other columns.

        Also renames auxiliary columns (e.g., ``*_canvas_size``) that are present
        in the DataFrame but not part of the field's required schema.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with renamed columns
        """
        # Build extended column map that includes auxiliary columns in the DataFrame
        extended_map = dict(self.column_map)
        for from_attr, to_attr in self.attr_mappings:
            prefix = f"{from_attr.name}_"
            new_prefix = f"{to_attr.name}_"
            for col_name in df.columns:
                if col_name.startswith(prefix) and col_name not in extended_map:
                    suffix = col_name[len(prefix) :]
                    extended_map[col_name] = f"{new_prefix}{suffix}"

        # Apply all renames
        return df.rename(extended_map)

    def filter_output_spec(self) -> bool:
        """Always return True as renaming is always applicable."""
        return True


def copy_columns_with_shape(
    df: pl.DataFrame,
    input_name: str,
    output_name: str,
    has_shape: bool = True,
) -> pl.DataFrame:
    """
    Copy/rename columns from input to output, optionally including shape column.

    This is a helper for metadata-only converters that don't need to modify
    the actual data, just update field metadata. The data transposition or
    other transformations are handled by the field's from_polars() method.

    Args:
        df: Input DataFrame
        input_name: Name of the input column
        output_name: Name of the output column
        has_shape: Whether to also copy the associated _shape column

    Returns:
        DataFrame with copied/renamed columns
    """
    columns = [pl.col(input_name).alias(output_name)]
    if has_shape:
        columns.append(pl.col(f"{input_name}_shape").alias(f"{output_name}_shape"))
    return df.with_columns(columns)
