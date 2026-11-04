# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Shared helpers for building Polars Series from raw Python values.

These helpers are used by the batch build path (``Dataset.append_batch``) to
efficiently construct columns of deeply nested
dtypes (``List``/``Array``/``Struct``) via PyArrow, which is orders of
magnitude faster than constructing per-item Polars Series and concatenating
them.
"""

from __future__ import annotations

from typing import Any

import polars as pl
import pyarrow as pa


def polars_dtype_to_pyarrow(dtype: pl.DataType) -> Any:
    """Convert a Polars DataType to the corresponding PyArrow type."""
    if isinstance(dtype, pl.Array):
        return pa.list_(polars_dtype_to_pyarrow(dtype.inner), dtype.size)  # type: ignore[arg-type]
    if isinstance(dtype, pl.List):
        return pa.list_(polars_dtype_to_pyarrow(dtype.inner))  # type: ignore[arg-type]
    if isinstance(dtype, pl.Struct):
        return pa.struct([pa.field(f.name, polars_dtype_to_pyarrow(f.dtype)) for f in dtype.fields])
    _MAP: dict[pl.DataType, Any] = {
        pl.Float32(): pa.float32(),
        pl.Float64(): pa.float64(),
        pl.Int8(): pa.int8(),
        pl.Int16(): pa.int16(),
        pl.Int32(): pa.int32(),
        pl.Int64(): pa.int64(),
        pl.UInt8(): pa.uint8(),
        pl.UInt16(): pa.uint16(),
        pl.UInt32(): pa.uint32(),
        pl.UInt64(): pa.uint64(),
        pl.Boolean(): pa.bool_(),
        pl.String(): pa.string(),
        pl.Utf8(): pa.string(),
    }
    if dtype in _MAP:
        return _MAP[dtype]
    raise NotImplementedError(f"Unsupported Polars dtype for PyArrow conversion: {dtype!r}")


def numpy_to_nested_lists(value: Any) -> Any:
    """Convert a numpy array (possibly ragged/object dtype) to nested Python lists.

    - ``None`` is passed through.
    - Object arrays are recursively converted element-wise (handles ragged shapes).
    - Regular ndarrays are converted via ``tolist()``.
    - Any other value is returned as-is.
    """
    if value is None:
        return None
    if hasattr(value, "dtype") and value.dtype == object:
        return [numpy_to_nested_lists(elem) for elem in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def build_series_bulk(col_name: str, values: list[Any], dtype: pl.DataType) -> pl.Series:
    """Build a ``pl.Series`` from a list of Python values.

    For nested dtypes (``List``/``Array``/``Struct``) this uses PyArrow as
    the backend, which is dramatically faster than Polars' native
    construction for these shapes. Falls back to a Polars-native path (and
    ultimately ``vertical_relaxed`` concat) for dtypes/values PyArrow
    cannot represent directly.
    """
    if isinstance(dtype, (pl.List, pl.Array, pl.Struct)):
        try:
            pa_type = polars_dtype_to_pyarrow(dtype)
            return pl.Series(col_name, pa.array(values, type=pa_type))
        except Exception:  # noqa: S110 - fall through to Polars-native path on any PyArrow failure
            pass
    try:
        return pl.Series(col_name, values, dtype=dtype)
    except Exception:
        # Fallback: build single-element Series and use vertical_relaxed concat
        # (handles type relaxation like Array[u32, N] -> List[u32] for variable sizes).
        col_dfs = [pl.Series(col_name, [v]).to_frame() for v in values]
        return pl.concat(col_dfs, how="vertical_relaxed").to_series()
