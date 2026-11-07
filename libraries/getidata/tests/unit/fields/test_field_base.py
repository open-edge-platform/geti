# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import polars as pl
import pytest

from getidata.fields.annotations import BBoxField


def test_field_dtype_validation():
    # pl.Float32() (instance) should be accepted
    field_instance = BBoxField(dtype=pl.Float32())
    assert isinstance(field_instance.dtype, pl.DataType)
    assert str(field_instance.dtype) == str(pl.Float32())

    # pl.Float32 (type) should raise with special message
    with pytest.raises(
        TypeError, match=r"dtype must be a Polars 'DataType' \(instance\), not a Polars 'DataTypeClass' \(type\)\."
    ):
        BBoxField(dtype=pl.Float32)

    # Invalid dtype should raise TypeError
    with pytest.raises(TypeError, match=r"dtype must be a Polars 'DataType', got 'float' instead."):
        BBoxField(dtype=float)
