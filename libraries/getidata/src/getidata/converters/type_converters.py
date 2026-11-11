# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Converters for generic field types: NumericField, BoolField, and StringField.

These converters handle shape (is_list) and dtype conversions for the
simple value field types defined in :mod:`getidata.fields.types`.
"""

import logging

import polars as pl

from getidata.converters.base import Converter
from getidata.converters.registry import converter
from getidata.fields.types import BoolField, NumericField, StringField
from getidata.schema import AttributeSpec

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NumericField converters
# ---------------------------------------------------------------------------


@converter
class NumericFieldShapeConverter(Converter):
    """Convert NumericField between scalar and list configurations.

    This converter handles changes to the ``is_list`` flag of a
    :class:`NumericField`.

    Supported conversions:
      - ``dtype → List(dtype)``: wrap scalar in a one-element list
      - ``List(dtype) → dtype``: keep the first element only (lossy, logs a warning)
    """

    input_numeric: AttributeSpec[NumericField]
    output_numeric: AttributeSpec[NumericField]

    def filter_output_spec(self) -> bool:
        """Configure output specification with target is_list setting."""
        input_is_list = self.input_numeric.field.is_list
        target_is_list = self.output_numeric.field.is_list

        if input_is_list == target_is_list:
            return False

        self.output_numeric = AttributeSpec(
            name=self.output_numeric.name,
            field=NumericField(
                semantic=self.input_numeric.field.semantic,
                dtype=self.input_numeric.field.dtype,
                is_list=target_is_list,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert numeric data between scalar and list configurations."""
        input_col = self.input_numeric.name
        output_col = self.output_numeric.name

        input_is_list = self.input_numeric.field.is_list
        output_is_list = self.output_numeric.field.is_list

        if input_is_list and not output_is_list:
            log.warning(
                "Converting list to scalar for numeric field '%s': keeping the first element only. Data may be lost.",
                input_col,
            )
            df = df.with_columns(pl.col(input_col).list.first().alias(output_col))
        if not input_is_list and output_is_list:
            # dtype → List(dtype): wrap the scalar value in a list, preserving nulls
            df = df.with_columns(
                pl.when(pl.col(input_col).is_not_null())
                .then(pl.concat_list(pl.col(input_col)))
                .otherwise(pl.lit(None, dtype=pl.List(self.input_numeric.field.dtype)))
                .alias(output_col)
            )

        return df


@converter
class NumericFieldDtypeConverter(Converter):
    """Convert NumericField between different data types."""

    input_numeric: AttributeSpec[NumericField]
    output_numeric: AttributeSpec[NumericField]

    def filter_output_spec(self) -> bool:
        """Configure output specification with target dtype."""
        input_dtype = self.input_numeric.field.dtype
        target_dtype = self.output_numeric.field.dtype

        if input_dtype == target_dtype:
            return False

        self.output_numeric = AttributeSpec(
            name=self.output_numeric.name,
            field=NumericField(
                semantic=self.input_numeric.field.semantic,
                dtype=target_dtype,
                is_list=self.input_numeric.field.is_list,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert numeric data to target dtype."""
        input_col = self.input_numeric.name
        output_col = self.output_numeric.name
        target_dtype = self.output_numeric.field.dtype

        if self.input_numeric.field.is_list:
            return df.with_columns(pl.col(input_col).list.eval(pl.element().cast(target_dtype)).alias(output_col))
        return df.with_columns(pl.col(input_col).cast(target_dtype).alias(output_col))


# ---------------------------------------------------------------------------
# BoolField converters
# ---------------------------------------------------------------------------


@converter
class BoolFieldShapeConverter(Converter):
    """Convert BoolField between scalar and list configurations.

    This converter handles changes to the ``is_list`` flag of a
    :class:`BoolField`.

    Supported conversions:
      - ``Boolean → List(Boolean)``: wrap scalar in a one-element list
      - ``List(Boolean) → Boolean``: keep the first element only (lossy, logs a warning)
    """

    input_bool: AttributeSpec[BoolField]
    output_bool: AttributeSpec[BoolField]

    def filter_output_spec(self) -> bool:
        """Configure output specification with target is_list setting."""
        input_is_list = self.input_bool.field.is_list
        target_is_list = self.output_bool.field.is_list

        if input_is_list == target_is_list:
            return False

        self.output_bool = AttributeSpec(
            name=self.output_bool.name,
            field=BoolField(
                semantic=self.input_bool.field.semantic,
                is_list=target_is_list,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert boolean data between scalar and list configurations."""
        input_col = self.input_bool.name
        output_col = self.output_bool.name

        input_is_list = self.input_bool.field.is_list
        output_is_list = self.output_bool.field.is_list

        if input_is_list and not output_is_list:
            log.warning(
                "Converting list to scalar for boolean field '%s': keeping the first element only. Data may be lost.",
                input_col,
            )
            df = df.with_columns(pl.col(input_col).list.first().alias(output_col))
        if not input_is_list and output_is_list:
            # Boolean → List(Boolean): wrap the scalar value in a list, preserving nulls
            df = df.with_columns(
                pl.when(pl.col(input_col).is_not_null())
                .then(pl.concat_list(pl.col(input_col)))
                .otherwise(pl.lit(None, dtype=pl.List(pl.Boolean())))
                .alias(output_col)
            )

        return df


# ---------------------------------------------------------------------------
# StringField converters
# ---------------------------------------------------------------------------


@converter
class StringFieldShapeConverter(Converter):
    """Convert StringField between scalar and list configurations.

    This converter handles changes to the ``is_list`` flag of a
    :class:`StringField`.

    Supported conversions:
      - ``String → List(String)``: wrap scalar in a one-element list
      - ``List(String) → String``: keep the first element only (lossy, logs a warning)
    """

    input_string: AttributeSpec[StringField]
    output_string: AttributeSpec[StringField]

    def filter_output_spec(self) -> bool:
        """Configure output specification with target is_list setting."""
        input_is_list = self.input_string.field.is_list
        target_is_list = self.output_string.field.is_list

        if input_is_list == target_is_list:
            return False

        self.output_string = AttributeSpec(
            name=self.output_string.name,
            field=StringField(
                semantic=self.input_string.field.semantic,
                is_list=target_is_list,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert string data between scalar and list configurations."""
        input_col = self.input_string.name
        output_col = self.output_string.name

        input_is_list = self.input_string.field.is_list
        output_is_list = self.output_string.field.is_list

        if input_is_list and not output_is_list:
            log.warning(
                "Converting list to scalar for string field '%s': keeping the first element only. Data may be lost.",
                input_col,
            )
            df = df.with_columns(pl.col(input_col).list.first().alias(output_col))
        if not input_is_list and output_is_list:
            # String → List(String): wrap the scalar value in a list, preserving nulls
            df = df.with_columns(
                pl.when(pl.col(input_col).is_not_null())
                .then(pl.concat_list(pl.col(input_col)))
                .otherwise(pl.lit(None, dtype=pl.List(pl.String())))
                .alias(output_col)
            )

        return df
