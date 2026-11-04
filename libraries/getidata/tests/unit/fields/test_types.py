# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

import polars as pl
import pytest

from getidata.dataset import Dataset, Sample
from getidata.fields import bool_field, numeric_field
from getidata.fields.types import BoolField, NumericField, StringField

# NumericField Tests


@pytest.mark.parametrize("value", [0.0, 3.14, -3.14, 1e10, float("inf")])
def test_numeric_field_roundtrip(value):
    """Test NumericField roundtrip through Dataset."""

    class NumericSample(Sample):
        value: Annotated[float, numeric_field(dtype=pl.Float64(), semantic="value")]

    ds = Dataset(NumericSample)
    s = NumericSample(value=value)
    ds.append(s)

    out = ds[0]
    if value != float("inf"):
        assert out.value == pytest.approx(value, rel=1e-5)
    else:
        assert out.value == value


def test_numeric_field_list_roundtrip():
    """Test NumericField with is_list=True roundtrip."""

    class VectorSample(Sample):
        values: Annotated[list[float], numeric_field(dtype=pl.Float32(), is_list=True, semantic="values")]

    ds = Dataset(VectorSample)
    values = [1.0, 2.0, 3.0]
    s = VectorSample(values=values)
    ds.append(s)

    out = ds[0]
    assert out.values == pytest.approx(values, rel=1e-5)


def test_numeric_field_polars_conversion():
    """Test NumericField to/from polars conversion."""
    field = NumericField(dtype=pl.Float32(), semantic="value")
    result = field.to_polars("value", 3.14)
    assert result["value"].dtype == pl.Float32()

    df = pl.DataFrame({"value": [3.14]}).cast({"value": pl.Float32()})
    assert field.from_polars("value", 0, df, float) == pytest.approx(3.14, rel=1e-5)


# BoolField Tests


@pytest.mark.parametrize("value", [True, False])
def test_bool_field_roundtrip(value):
    """Test BoolField roundtrip through Dataset."""

    class BoolSample(Sample):
        flag: Annotated[bool, bool_field(semantic="flag")]

    ds = Dataset(BoolSample)
    s = BoolSample(flag=value)
    ds.append(s)

    assert ds[0].flag is value


def test_bool_field_list_roundtrip():
    """Test BoolField with is_list=True roundtrip."""

    class MultiBoolSample(Sample):
        flags: Annotated[list[bool], bool_field(is_list=True, semantic="flags")]

    ds = Dataset(MultiBoolSample)
    flags = [True, False, True]
    s = MultiBoolSample(flags=flags)
    ds.append(s)

    assert ds[0].flags == flags


def test_bool_field_polars_conversion():
    """Test BoolField to/from polars conversion."""
    field = BoolField(semantic="flag")
    result = field.to_polars("flag", True)
    assert result["flag"].dtype == pl.Boolean()
    assert result["flag"][0] is True

    df = pl.DataFrame({"flag": [False]})
    assert field.from_polars("flag", 0, df, bool) is False


# StringField Tests


def test_string_field_polars_conversion():
    """Test StringField to/from polars conversion."""
    field = StringField(semantic="text")
    result = field.to_polars("text", "hello")
    assert result["text"].dtype == pl.String()
    assert result["text"][0] == "hello"

    df = pl.DataFrame({"text": ["world"]})
    assert field.from_polars("text", 0, df, str) == "world"
