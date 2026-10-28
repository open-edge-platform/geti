"""
Implementations of filters for specific field types.

This module contains filters that operate on different types of fields
in the dataset schema.
"""

import polars as pl

from getidata.fields import BBoxField, PolygonField
from getidata.filtering.filter_registry import Filter, FilterRegistry
from getidata.schema import AttributeSpec


@FilterRegistry.register(BBoxField)
class EmptyBBoxFilter(Filter):
    """Filter that removes rows with empty bounding box lists."""

    field_spec: AttributeSpec[BBoxField]

    def filter(self, df: pl.DataFrame) -> pl.Expr:  # noqa: ARG002
        """Filter out rows where bounding box list is empty.

        Args:
            df: Input dataframe with bounding box column

        Returns:
            Boolean series indicating which rows to keep (True) or remove (False)
        """
        column_name = self.field_spec.name

        return pl.col(column_name).list.len() > 0


@FilterRegistry.register(PolygonField)
class EmptyPolygonFilter(Filter):
    """Filter that removes rows with empty polygon lists."""

    field_spec: AttributeSpec[PolygonField]

    def filter(self, df: pl.DataFrame) -> pl.Expr:  # noqa: ARG002
        """Filter out rows where polygon list is empty.

        Args:
            df: Input dataframe with polygon column

        Returns:
            Boolean series indicating which rows to keep (True) or remove (False)
        """
        column_name = self.field_spec.name
        return pl.col(column_name).list.len() > 0
