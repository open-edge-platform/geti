# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Utility functions for Polars DataFrame pickling with Object columns."""

from __future__ import annotations

from typing import Any

import polars as pl


def prepare_dataframe_for_pickle(df: pl.DataFrame, df_attr_name: str, state: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare a Polars DataFrame for pickling by extracting Object columns.

    Polars DataFrames with Object columns cannot be serialized using Polars' default
    serialization. This function extracts Object columns as Python lists before pickling.

    Args:
        df: The DataFrame to prepare for pickling
        df_attr_name: The attribute name of the DataFrame in the object's state
        state: The object's __dict__.copy() to be modified

    Returns:
        The modified state dictionary ready for pickling
    """
    # Check if DataFrame has Object columns
    object_columns = [col for col, dtype in df.schema.items() if dtype == pl.Object]

    if object_columns:
        # Extract Object column data as Python lists
        state["_object_column_data"] = {col: df[col].to_list() for col in object_columns}
        # Create a DataFrame without Object columns for serialization
        non_object_df = df.drop(object_columns)
        state[df_attr_name] = non_object_df
        state["_object_columns_schema"] = dict.fromkeys(object_columns, pl.Object)

    return state


def restore_dataframe_from_pickle(state: dict[str, Any], df_attr_name: str) -> pl.DataFrame:
    """
    Restore Object columns to a Polars DataFrame after unpickling.

    Reconstructs Object columns from the Python lists stored during pickling.

    Args:
        state: The state dictionary from __setstate__
        df_attr_name: The attribute name of the DataFrame in the object's state

    Returns:
        The restored DataFrame with Object columns
    """
    object_column_data = state.pop("_object_column_data", None)
    object_columns_schema = state.pop("_object_columns_schema", None)

    df = state[df_attr_name]

    # Restore Object columns if they were extracted
    if object_column_data is not None and object_columns_schema is not None:
        for col, values in object_column_data.items():
            df = df.with_columns(pl.Series(col, values, dtype=pl.Object()))

    return df
