"""
Unit tests for type converter implementations (NumericField, BoolField, StringField).
"""

import polars as pl
import pytest

from getidata.converters.type_converters import (
    BoolFieldShapeConverter,
    NumericFieldDtypeConverter,
    NumericFieldShapeConverter,
    StringFieldShapeConverter,
)
from getidata.fields.types import BoolField, NumericField, StringField
from getidata.schema import AttributeSpec

# ---------------------------------------------------------------------------
# NumericFieldShapeConverter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "input_is_list, output_is_list, data, schema_type, expected_dtype, expected_value",
    [
        pytest.param(False, True, {"score": [0.5]}, pl.Float32(), pl.List(pl.Float32), [0.5], id="scalar_to_list"),
        pytest.param(False, True, {"score": [42]}, pl.Int64(), pl.List(pl.Int64), [42], id="int_scalar_to_list"),
    ],
)
def test_numeric_shape_converter_conversions(
    input_is_list,
    output_is_list,
    data,
    schema_type,
    expected_dtype,
    expected_value,
):
    """Test NumericFieldShapeConverter across scalar/list transitions."""
    converter_instance = NumericFieldShapeConverter()

    col_name = next(iter(data.keys()))
    df = pl.DataFrame(data, schema=pl.Schema({col_name: schema_type}))

    input_field = NumericField(
        semantic="s",
        dtype=schema_type if not isinstance(schema_type, pl.List) else schema_type.inner,
        is_list=input_is_list,
    )
    output_field = NumericField(semantic="s", dtype=input_field.dtype, is_list=output_is_list)

    setattr(converter_instance, "input_numeric", AttributeSpec(name=col_name, field=input_field))
    setattr(converter_instance, "output_numeric", AttributeSpec(name=col_name, field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)

    assert result_df[col_name].dtype == expected_dtype
    result_val = result_df[col_name][0]
    if hasattr(result_val, "to_list"):
        assert result_val.to_list() == expected_value
    else:
        assert result_val == expected_value


def test_numeric_shape_converter_list_to_scalar(caplog):
    """convert() keeps the first element and logs a warning for lossy list → scalar conversion."""
    converter_instance = NumericFieldShapeConverter()

    input_field = NumericField(semantic="s", dtype=pl.Float32(), is_list=True)
    output_field = NumericField(semantic="s", dtype=pl.Float32(), is_list=False)

    setattr(converter_instance, "input_numeric", AttributeSpec(name="score", field=input_field))
    setattr(converter_instance, "output_numeric", AttributeSpec(name="score", field=output_field))

    assert converter_instance.filter_output_spec() is True

    df = pl.DataFrame({"score": [[0.5, 0.9]]}, schema=pl.Schema({"score": pl.List(pl.Float32())}))
    with caplog.at_level("WARNING"):
        result_df = converter_instance.convert(df)

    assert result_df["score"].dtype == pl.Float32()
    assert result_df["score"][0] == pytest.approx(0.5)
    assert any("keeping the first element only" in msg for msg in caplog.messages)


def test_numeric_shape_converter_filter_returns_false():
    """filter_output_spec returns False when is_list is already the same."""
    converter_instance = NumericFieldShapeConverter()

    field = NumericField(semantic="s", dtype=pl.Float32(), is_list=True)
    setattr(converter_instance, "input_numeric", AttributeSpec(name="score", field=field))
    setattr(converter_instance, "output_numeric", AttributeSpec(name="score", field=field))

    assert converter_instance.filter_output_spec() is False


def test_numeric_shape_converter_preserves_dtype():
    """filter_output_spec keeps the dtype from the input, not the output."""
    converter_instance = NumericFieldShapeConverter()

    input_field = NumericField(semantic="s", dtype=pl.Float64(), is_list=False)
    output_field = NumericField(semantic="s", dtype=pl.Float32(), is_list=True)

    setattr(converter_instance, "input_numeric", AttributeSpec(name="score", field=input_field))
    setattr(converter_instance, "output_numeric", AttributeSpec(name="score", field=output_field))

    assert converter_instance.filter_output_spec() is True
    assert converter_instance.output_numeric.field.dtype == pl.Float64()  # Preserved from input
    assert converter_instance.output_numeric.field.is_list is True  # From target


def test_numeric_shape_converter_with_nulls():
    """Null values are preserved as null in both conversion directions."""
    converter_instance = NumericFieldShapeConverter()

    # scalar → list
    df = pl.DataFrame({"score": [0.5, None, 0.9]}, schema=pl.Schema({"score": pl.Float32()}))
    input_field = NumericField(semantic="s", dtype=pl.Float32(), is_list=False)
    output_field = NumericField(semantic="s", dtype=pl.Float32(), is_list=True)

    setattr(converter_instance, "input_numeric", AttributeSpec(name="score", field=input_field))
    setattr(converter_instance, "output_numeric", AttributeSpec(name="score", field=output_field))

    assert converter_instance.filter_output_spec() is True
    result_df = converter_instance.convert(df)

    assert result_df["score"][0].to_list() == pytest.approx([0.5])
    assert result_df["score"][1] is None
    assert result_df["score"][2].to_list() == pytest.approx([0.9])


def test_numeric_shape_converter_different_column_names():
    """Input and output may use different column names."""
    converter_instance = NumericFieldShapeConverter()

    df = pl.DataFrame({"src_score": [1.0, 2.0]}, schema=pl.Schema({"src_score": pl.Float32()}))
    input_field = NumericField(semantic="s", dtype=pl.Float32(), is_list=False)
    output_field = NumericField(semantic="s", dtype=pl.Float32(), is_list=True)

    setattr(converter_instance, "input_numeric", AttributeSpec(name="src_score", field=input_field))
    setattr(converter_instance, "output_numeric", AttributeSpec(name="dst_score", field=output_field))

    assert converter_instance.filter_output_spec() is True
    result_df = converter_instance.convert(df)

    assert "dst_score" in result_df.columns
    assert result_df["dst_score"][0].to_list() == [1.0]


# ---------------------------------------------------------------------------
# NumericFieldDtypeConverter
# ---------------------------------------------------------------------------


def test_numeric_dtype_converter_float32_to_float64():
    """Convert Float32 → Float64 for a scalar NumericField."""
    converter_instance = NumericFieldDtypeConverter()

    df = pl.DataFrame({"val": pl.Series([1.5, 2.5], dtype=pl.Float32())})
    input_field = NumericField(semantic="s", dtype=pl.Float32(), is_list=False)
    output_field = NumericField(semantic="s", dtype=pl.Float64(), is_list=False)

    setattr(converter_instance, "input_numeric", AttributeSpec(name="val", field=input_field))
    setattr(converter_instance, "output_numeric", AttributeSpec(name="val", field=output_field))

    assert converter_instance.filter_output_spec() is True
    result_df = converter_instance.convert(df)

    assert result_df["val"].dtype == pl.Float64
    assert result_df["val"].to_list() == pytest.approx([1.5, 2.5])


def test_numeric_dtype_converter_list_mode():
    """Convert List(Int32) → List(Float32)."""
    converter_instance = NumericFieldDtypeConverter()

    df = pl.DataFrame({"val": [[1, 2], [3, 4]]}, schema=pl.Schema({"val": pl.List(pl.Int32())}))
    input_field = NumericField(semantic="s", dtype=pl.Int32(), is_list=True)
    output_field = NumericField(semantic="s", dtype=pl.Float32(), is_list=True)

    setattr(converter_instance, "input_numeric", AttributeSpec(name="val", field=input_field))
    setattr(converter_instance, "output_numeric", AttributeSpec(name="val", field=output_field))

    assert converter_instance.filter_output_spec() is True
    result_df = converter_instance.convert(df)

    assert result_df["val"].dtype == pl.List(pl.Float32)
    assert result_df["val"][0].to_list() == pytest.approx([1.0, 2.0])


def test_numeric_dtype_converter_filter_returns_false():
    """filter_output_spec returns False when dtype already matches."""
    converter_instance = NumericFieldDtypeConverter()

    field = NumericField(semantic="s", dtype=pl.Float32(), is_list=False)
    setattr(converter_instance, "input_numeric", AttributeSpec(name="val", field=field))
    setattr(converter_instance, "output_numeric", AttributeSpec(name="val", field=field))

    assert converter_instance.filter_output_spec() is False


def test_numeric_dtype_converter_preserves_is_list():
    """filter_output_spec keeps is_list from the input, not the output."""
    converter_instance = NumericFieldDtypeConverter()

    input_field = NumericField(semantic="s", dtype=pl.Int32(), is_list=True)
    output_field = NumericField(semantic="s", dtype=pl.Float64(), is_list=False)

    setattr(converter_instance, "input_numeric", AttributeSpec(name="val", field=input_field))
    setattr(converter_instance, "output_numeric", AttributeSpec(name="val", field=output_field))

    assert converter_instance.filter_output_spec() is True
    assert converter_instance.output_numeric.field.is_list is True  # Preserved from input
    assert converter_instance.output_numeric.field.dtype == pl.Float64()  # From target


# ---------------------------------------------------------------------------
# BoolFieldShapeConverter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "input_is_list, output_is_list, data, schema_type, expected_dtype, expected_value",
    [
        pytest.param(False, True, {"flag": [True]}, pl.Boolean(), pl.List(pl.Boolean), [True], id="scalar_to_list"),
        pytest.param(
            False, True, {"flag": [False]}, pl.Boolean(), pl.List(pl.Boolean), [False], id="scalar_false_to_list"
        ),
    ],
)
def test_bool_shape_converter_conversions(
    input_is_list,
    output_is_list,
    data,
    schema_type,
    expected_dtype,
    expected_value,
):
    """Test BoolFieldShapeConverter across scalar/list transitions."""
    converter_instance = BoolFieldShapeConverter()

    col_name = next(iter(data.keys()))
    df = pl.DataFrame(data, schema=pl.Schema({col_name: schema_type}))

    input_field = BoolField(semantic="s", is_list=input_is_list)
    output_field = BoolField(semantic="s", is_list=output_is_list)

    setattr(converter_instance, "input_bool", AttributeSpec(name=col_name, field=input_field))
    setattr(converter_instance, "output_bool", AttributeSpec(name=col_name, field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)

    assert result_df[col_name].dtype == expected_dtype
    result_val = result_df[col_name][0]
    if hasattr(result_val, "to_list"):
        assert result_val.to_list() == expected_value
    else:
        assert result_val == expected_value


def test_bool_shape_converter_list_to_scalar(caplog):
    """convert() keeps the first element and logs a warning for lossy list → scalar conversion."""
    converter_instance = BoolFieldShapeConverter()

    input_field = BoolField(semantic="s", is_list=True)
    output_field = BoolField(semantic="s", is_list=False)

    setattr(converter_instance, "input_bool", AttributeSpec(name="flag", field=input_field))
    setattr(converter_instance, "output_bool", AttributeSpec(name="flag", field=output_field))

    assert converter_instance.filter_output_spec() is True

    df = pl.DataFrame({"flag": [[True, False]]}, schema=pl.Schema({"flag": pl.List(pl.Boolean())}))
    with caplog.at_level("WARNING"):
        result_df = converter_instance.convert(df)

    assert result_df["flag"].dtype == pl.Boolean()
    assert result_df["flag"][0] is True
    assert any("keeping the first element only" in msg for msg in caplog.messages)


def test_bool_shape_converter_filter_returns_false():
    """filter_output_spec returns False when is_list is already the same."""
    converter_instance = BoolFieldShapeConverter()

    field = BoolField(semantic="s", is_list=False)
    setattr(converter_instance, "input_bool", AttributeSpec(name="flag", field=field))
    setattr(converter_instance, "output_bool", AttributeSpec(name="flag", field=field))

    assert converter_instance.filter_output_spec() is False


def test_bool_shape_converter_with_nulls():
    """Null values are preserved as null during boolean shape conversion."""
    converter_instance = BoolFieldShapeConverter()

    df = pl.DataFrame({"flag": [True, None, False]}, schema=pl.Schema({"flag": pl.Boolean()}))
    input_field = BoolField(semantic="s", is_list=False)
    output_field = BoolField(semantic="s", is_list=True)

    setattr(converter_instance, "input_bool", AttributeSpec(name="flag", field=input_field))
    setattr(converter_instance, "output_bool", AttributeSpec(name="flag", field=output_field))

    assert converter_instance.filter_output_spec() is True
    result_df = converter_instance.convert(df)

    assert result_df["flag"][0].to_list() == [True]
    assert result_df["flag"][1] is None
    assert result_df["flag"][2].to_list() == [False]


# ---------------------------------------------------------------------------
# StringFieldShapeConverter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "input_is_list, output_is_list, data, schema_type, expected_dtype, expected_value",
    [
        pytest.param(False, True, {"tag": ["cat"]}, pl.String(), pl.List(pl.String), ["cat"], id="scalar_to_list"),
        pytest.param(
            False, True, {"tag": [""]}, pl.String(), pl.List(pl.String), [""], id="empty_string_scalar_to_list"
        ),
    ],
)
def test_string_shape_converter_conversions(
    input_is_list,
    output_is_list,
    data,
    schema_type,
    expected_dtype,
    expected_value,
):
    """Test StringFieldShapeConverter across scalar/list transitions."""
    converter_instance = StringFieldShapeConverter()

    col_name = next(iter(data.keys()))
    df = pl.DataFrame(data, schema=pl.Schema({col_name: schema_type}))

    input_field = StringField(semantic="s", is_list=input_is_list)
    output_field = StringField(semantic="s", is_list=output_is_list)

    setattr(converter_instance, "input_string", AttributeSpec(name=col_name, field=input_field))
    setattr(converter_instance, "output_string", AttributeSpec(name=col_name, field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)

    assert result_df[col_name].dtype == expected_dtype
    result_val = result_df[col_name][0]
    if hasattr(result_val, "to_list"):
        assert result_val.to_list() == expected_value
    else:
        assert result_val == expected_value


def test_string_shape_converter_list_to_scalar(caplog):
    """convert() keeps the first element and logs a warning for lossy list → scalar conversion."""
    converter_instance = StringFieldShapeConverter()

    input_field = StringField(semantic="s", is_list=True)
    output_field = StringField(semantic="s", is_list=False)

    setattr(converter_instance, "input_string", AttributeSpec(name="tag", field=input_field))
    setattr(converter_instance, "output_string", AttributeSpec(name="tag", field=output_field))

    assert converter_instance.filter_output_spec() is True

    df = pl.DataFrame({"tag": [["cat", "dog"]]}, schema=pl.Schema({"tag": pl.List(pl.String())}))
    with caplog.at_level("WARNING"):
        result_df = converter_instance.convert(df)

    assert result_df["tag"].dtype == pl.String()
    assert result_df["tag"][0] == "cat"
    assert any("keeping the first element only" in msg for msg in caplog.messages)


def test_string_shape_converter_filter_returns_false():
    """filter_output_spec returns False when is_list is already the same."""
    converter_instance = StringFieldShapeConverter()

    field = StringField(semantic="s", is_list=True)
    setattr(converter_instance, "input_string", AttributeSpec(name="tag", field=field))
    setattr(converter_instance, "output_string", AttributeSpec(name="tag", field=field))

    assert converter_instance.filter_output_spec() is False


def test_string_shape_converter_with_nulls():
    """Null values are preserved as null during string shape conversion."""
    converter_instance = StringFieldShapeConverter()

    df = pl.DataFrame({"tag": ["hello", None, "world"]}, schema=pl.Schema({"tag": pl.String()}))
    input_field = StringField(semantic="s", is_list=False)
    output_field = StringField(semantic="s", is_list=True)

    setattr(converter_instance, "input_string", AttributeSpec(name="tag", field=input_field))
    setattr(converter_instance, "output_string", AttributeSpec(name="tag", field=output_field))

    assert converter_instance.filter_output_spec() is True
    result_df = converter_instance.convert(df)

    assert result_df["tag"][0].to_list() == ["hello"]
    assert result_df["tag"][1] is None
    assert result_df["tag"][2].to_list() == ["world"]


# ---------------------------------------------------------------------------
# End-to-end conversion path tests
# ---------------------------------------------------------------------------


def test_numeric_shape_conversion_path_found():
    """find_conversion_path discovers NumericFieldShapeConverter for is_list change."""
    from getidata.converters.registry import find_conversion_path
    from getidata.dataset import Sample
    from getidata.fields.types import numeric_field

    class SourceSample(Sample):
        score: float = numeric_field(semantic="default", dtype=pl.Float32(), is_list=False)

    class TargetSample(Sample):
        score: list[float] = numeric_field(semantic="default", dtype=pl.Float32(), is_list=True)

    source_schema = SourceSample.infer_schema()
    target_schema = TargetSample.infer_schema()

    conversion_paths, _categories = find_conversion_path(source_schema, target_schema)
    assert len(conversion_paths.converters) > 0


def test_numeric_dtype_conversion_path_found():
    """find_conversion_path discovers NumericFieldDtypeConverter for dtype change."""
    from getidata.converters.registry import find_conversion_path
    from getidata.dataset import Sample
    from getidata.fields.types import numeric_field

    class SourceSample(Sample):
        score: float = numeric_field(semantic="default", dtype=pl.Float32(), is_list=False)

    class TargetSample(Sample):
        score: float = numeric_field(semantic="default", dtype=pl.Float64(), is_list=False)

    source_schema = SourceSample.infer_schema()
    target_schema = TargetSample.infer_schema()

    conversion_paths, _categories = find_conversion_path(source_schema, target_schema)
    assert len(conversion_paths.converters) > 0


def test_numeric_dtype_conversion_path_found_list_mode():
    """find_conversion_path discovers NumericFieldDtypeConverter for dtype change in list mode."""
    from getidata.converters.registry import find_conversion_path
    from getidata.dataset import Sample
    from getidata.fields.types import numeric_field

    class SourceSample(Sample):
        scores: list[float] = numeric_field(semantic="default", dtype=pl.Int32(), is_list=True)

    class TargetSample(Sample):
        scores: list[float] = numeric_field(semantic="default", dtype=pl.Float32(), is_list=True)

    source_schema = SourceSample.infer_schema()
    target_schema = TargetSample.infer_schema()

    conversion_paths, _categories = find_conversion_path(source_schema, target_schema)
    assert len(conversion_paths.converters) > 0


def test_bool_shape_conversion_path_found():
    """find_conversion_path discovers BoolFieldShapeConverter for is_list change."""
    from getidata.converters.registry import find_conversion_path
    from getidata.dataset import Sample
    from getidata.fields.types import bool_field

    class SourceSample(Sample):
        flag: bool = bool_field(semantic="default", is_list=False)

    class TargetSample(Sample):
        flag: list[bool] = bool_field(semantic="default", is_list=True)

    source_schema = SourceSample.infer_schema()
    target_schema = TargetSample.infer_schema()

    conversion_paths, _categories = find_conversion_path(source_schema, target_schema)
    assert len(conversion_paths.converters) > 0


def test_string_shape_conversion_path_found():
    """find_conversion_path discovers StringFieldShapeConverter for is_list change."""
    from getidata.converters.registry import find_conversion_path
    from getidata.dataset import Sample
    from getidata.fields.types import string_field

    class SourceSample(Sample):
        tag: str = string_field(semantic="default", is_list=False)

    class TargetSample(Sample):
        tag: list[str] = string_field(semantic="default", is_list=True)

    source_schema = SourceSample.infer_schema()
    target_schema = TargetSample.infer_schema()

    conversion_paths, _categories = find_conversion_path(source_schema, target_schema)
    assert len(conversion_paths.converters) > 0
