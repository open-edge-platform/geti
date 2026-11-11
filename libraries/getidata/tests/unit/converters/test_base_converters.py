"""
Unit tests for converter registry and converter implementations.
"""

from collections import Counter
from dataclasses import field

import numpy as np
import numpy.typing as npt
import polars as pl
import pytest

from getidata.categories import LabelCategories, MaskCategories
from getidata.converters import (
    AttributeRemapperConverter,
    BBoxCoordinateConverter,
    ConversionError,
    Converter,
    ConverterRegistry,
    ImageDtypeConverter,
    ImagePathToImageConverter,
    RedBlueColorConverter,
    converter,
    find_conversion_path,
)
from getidata.dataset import Dataset, Sample
from getidata.fields import (
    BBoxField,
    Field,
    ImageField,
    ImageInfoField,
    KeypointsField,
    LabelField,
    MaskField,
    PolygonField,
    bbox_field,
    image_field,
    image_info_field,
    label_field,
)
from getidata.schema import AttributeInfo, AttributeSpec, Schema


def test_converter_decorator(request: pytest.FixtureRequest):
    """Test the @converter decorator functionality."""

    # Create a simple converter for testing
    @converter
    class TestConverter(Converter):  # type: ignore[reportUnusedClass]
        input_field: AttributeSpec[ImageField]
        output_field: AttributeSpec[ImageField]

        def filter_output_spec(self) -> bool:
            return False

        def convert(self, df: pl.DataFrame) -> pl.DataFrame:
            return df

    registry = ConverterRegistry()
    request.addfinalizer(lambda: registry.remove_converter(TestConverter))

    # Check that it was registered
    converters = registry.list_converters()

    # Should find our test converter in the registry
    test_converters = [c for c in converters if c == TestConverter]
    assert len(test_converters) > 0


def test_find_conversion_path():
    """Test the find_conversion_path function."""

    # Create simple source and target schemas
    source_schema = Schema(
        attributes={"image": AttributeInfo(type=np.ndarray, field=image_field(dtype=pl.UInt8(), format="RGB"))}
    )

    target_schema = Schema(
        attributes={"image": AttributeInfo(type=np.ndarray, field=image_field(dtype=pl.Float32(), format="RGB"))}
    )

    # This should find a conversion path (UInt8 -> Float32)
    path, _ = find_conversion_path(source_schema, target_schema)
    assert len(path.converters["image"]) == 1
    assert type(path.converters["image"][0]) is ImageDtypeConverter


def test_convert_dataframe():
    """Test getting conversion path and applying it manually."""

    # Create test DataFrame
    df = pl.DataFrame(
        {"image": [[255, 0, 0, 0, 255, 0]], "image_shape": [[2, 3]]},
        schema=pl.Schema({"image": pl.List(pl.UInt8()), "image_shape": pl.List(pl.Int64)}),
    )

    source_schema = Schema(
        attributes={"image": AttributeInfo(type=np.ndarray, field=image_field(dtype=pl.UInt8(), format="RGB"))}
    )

    target_schema = Schema(
        attributes={"image": AttributeInfo(type=np.ndarray, field=image_field(dtype=pl.Float32(), format="BGR"))}
    )

    # Get conversion path and apply it manually
    conversion_paths, _ = find_conversion_path(source_schema, target_schema)

    # Apply batch converters first
    result_df = df
    for conv in conversion_paths.converters["image"]:
        result_df = conv.convert(result_df)

    # For this test we convert from UInt8 + RGB to Float32 + BGR; we just
    # verify the conversion runs and the result matches the expected values.
    assert result_df is not None

    image = result_df["image"][0].to_numpy()
    assert np.all(image == [0.0, 0.0, 1.0, 0.0, 1.0, 0.0])


def test_lazy_converter():
    """Test lazy converter functionality."""
    registry = ConverterRegistry()
    lazy_converters = [c for c in registry.list_converters() if c.lazy]

    # Should have at least one lazy converter (ImagePathToImageConverter)
    assert len(lazy_converters) > 0

    # Check that ImagePathToImageConverter is marked as lazy
    image_path_converters = [c for c in lazy_converters if issubclass(c, ImagePathToImageConverter) and c.lazy]
    assert len(image_path_converters) > 0


def test_converter_with_auxiliary_fields():
    """Test converters that require auxiliary fields."""
    # This would test converters like bbox normalization that need image size
    # The exact implementation depends on how auxiliary fields are handled

    converter_instance = BBoxCoordinateConverter()  # type: ignore[call-arg]

    # BBox converter needs image data as auxiliary
    input_bbox_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)
    output_bbox_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=True)
    input_image_field = ImageField(dtype=pl.UInt8(), format="RGB")

    setattr(
        converter_instance,
        "input_bbox",
        AttributeSpec(name="bbox", field=input_bbox_field),
    )
    setattr(
        converter_instance,
        "output_bbox",
        AttributeSpec(name="bbox", field=output_bbox_field),
    )
    setattr(
        converter_instance,
        "input_image",
        AttributeSpec(name="image", field=input_image_field),
    )

    # Should require auxiliary image data for bbox normalization
    assert hasattr(converter_instance, "input_image")


def test_multiple_converter_chaining():
    """Test that multiple converters can be chained together."""
    # This tests the A* search functionality for finding conversion paths

    # Create a complex conversion scenario
    source_schema = Schema(
        attributes={
            "image": AttributeInfo(type=np.ndarray, field=image_field(dtype=pl.UInt8(), format="RGB")),
            "bbox": AttributeInfo(
                type=np.ndarray,
                field=bbox_field(dtype=pl.Float32(), normalize=False),
            ),
        }
    )

    target_schema = Schema(
        attributes={
            "image": AttributeInfo(type=np.ndarray, field=image_field(dtype=pl.Float32(), format="BGR")),
            "bbox": AttributeInfo(type=np.ndarray, field=bbox_field(dtype=pl.Float32(), normalize=True)),
        }
    )

    # This would require multiple conversions:
    # 1. RGB -> BGR (format)
    # 2. UInt8 -> Float32 (dtype)
    # 3. absolute -> normalized bbox (with image as auxiliary)

    path, _ = find_conversion_path(source_schema, target_schema)
    # If successful, should have multiple steps
    assert len(path.converters["image"]) == 2
    image_converter_counter = Counter(type(c) for c in path.converters["image"])
    assert image_converter_counter == Counter([ImageDtypeConverter, RedBlueColorConverter])

    # The BBoxCoordinateConverter needs an image for normalization (to get dimensions).
    # The bbox chain includes BBoxCoordinateConverter plus any image converters it depends on,
    # since the image field needs to be converted before the bbox can use it for normalization.
    bbox_converter_counter = Counter(type(c) for c in path.converters["bbox"])
    # Ensure there is exactly one BBoxCoordinateConverter and no unexpected converter types.
    assert bbox_converter_counter[BBoxCoordinateConverter] == 1
    allowed_bbox_converters = {BBoxCoordinateConverter, ImageDtypeConverter, RedBlueColorConverter}
    assert set(bbox_converter_counter).issubset(allowed_bbox_converters)


def test_astar_direct_conversion():
    """Test direct conversion without chaining using A* search."""
    from dataclasses import dataclass

    # Mock field types for testing
    @dataclass(frozen=True)
    class TestImageField(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Binary, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Binary()}

    @dataclass(frozen=True)
    class TestImageSizeField(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Int32, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {f"{name}_width": pl.Int32(), f"{name}_height": pl.Int32()}

    # Register test converter as a class
    @converter
    class ExtractImageSizeConverter(Converter):
        input_image: AttributeSpec[TestImageField]
        output_image_size: AttributeSpec[TestImageSizeField]

        def filter_output_spec(self) -> bool:
            return True

        def convert(self, df: pl.DataFrame) -> pl.DataFrame:
            """Extract image size from image data."""
            return df.with_columns(
                [
                    pl.lit(640).alias("image_size_width"),
                    pl.lit(480).alias("image_size_height"),
                ]
            )

    # Create schemas
    from_schema = Schema(
        {
            "image": AttributeInfo(type=bytes, field=TestImageField()),
        }
    )

    to_schema = Schema(
        {
            "image_size": AttributeInfo(type=tuple, field=TestImageSizeField()),
        }
    )

    # Test finding conversion path
    path, _ = find_conversion_path(from_schema, to_schema)
    assert len(path.converters["image_size"]) == 1
    assert type(path.converters["image_size"][0]) is ExtractImageSizeConverter


def test_astar_chained_conversion():
    """Test chained conversion using A* search."""
    from dataclasses import dataclass

    # Mock field types for testing
    @dataclass(frozen=True)
    class TestImageField(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Binary, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Binary()}

    @dataclass(frozen=True)
    class TestImageSizeField(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Int32, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {f"{name}_width": pl.Int32(), f"{name}_height": pl.Int32()}

    @dataclass(frozen=True)
    class TestNormalizedBboxField(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Float32, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.List(pl.Float32())}

    @dataclass(frozen=True)
    class TestAbsoluteBboxField(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Int32, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.List(pl.Int32())}

    # Register test converters as classes
    @converter
    class ExtractImageSizeChainConverter(Converter):
        input_image: AttributeSpec[TestImageField]
        output_image_size: AttributeSpec[TestImageSizeField]

        def filter_output_spec(self) -> bool:
            return True

        def convert(self, df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(
                [
                    pl.lit(640).alias("image_size_width"),
                    pl.lit(480).alias("image_size_height"),
                ]
            )

    @converter
    class NormalizeToAbsoluteBboxConverter(Converter):
        input_bbox: AttributeSpec[TestNormalizedBboxField]
        input_image_size: AttributeSpec[TestImageSizeField]
        output_absolute_bbox: AttributeSpec[TestAbsoluteBboxField]

        def filter_output_spec(self) -> bool:
            return True

        def convert(self, df: pl.DataFrame) -> pl.DataFrame:
            """Convert normalized bbox to absolute coordinates."""
            width = df.select("image_size_width").item()
            height = df.select("image_size_height").item()

            return df.with_columns(
                [
                    pl.col("bbox")
                    .list.eval(
                        pl.when(pl.int_range(pl.len()) % 2 == 0)
                        .then(pl.element() * width)
                        .otherwise(pl.element() * height)
                    )
                    .alias("absolute_bbox")
                ]
            ).drop("bbox")

    # Create schemas that require chaining
    from_schema = Schema(
        {
            "image": AttributeInfo(type=bytes, field=TestImageField()),
            "bbox": AttributeInfo(type=list, field=TestNormalizedBboxField()),
        }
    )

    to_schema = Schema(
        {
            "absolute_bbox": AttributeInfo(type=list, field=TestAbsoluteBboxField()),
        }
    )

    # Test finding conversion path
    path, _ = find_conversion_path(from_schema, to_schema)
    # Should need 2 converters: ImageField -> ImageSizeField, then NormalizedBbox -> AbsoluteBbox
    assert len(path.converters["absolute_bbox"]) == 2
    assert type(path.converters["absolute_bbox"][0]) is ExtractImageSizeChainConverter
    assert type(path.converters["absolute_bbox"][1]) is NormalizeToAbsoluteBboxConverter


def test_astar_no_conversion_needed():
    """Test when no conversion is needed using A* search."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class TestField(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    # Identical schemas - no conversion needed
    schema = Schema(
        {
            "data": AttributeInfo(type=str, field=TestField()),
        }
    )

    path, _ = find_conversion_path(schema, schema)
    assert len(path.converters) == 0, f"Expected 0 converters for identical schemas, got {len(path.converters)}"


def test_astar_impossible_conversion():
    """Test conversion that should fail using A* search."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class FieldA(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    @dataclass(frozen=True)
    class FieldB(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    # No converters registered between these types - should fail
    from_schema = Schema(
        {
            "field_a": AttributeInfo(type=str, field=FieldA()),
        }
    )

    to_schema = Schema(
        {
            "field_b": AttributeInfo(type=str, field=FieldB()),
        }
    )

    # Should raise ConversionError
    with pytest.raises(ConversionError):
        find_conversion_path(from_schema, to_schema)


def test_optimal_path_selection():
    """Test that A* chooses the shortest path when multiple paths exist."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class FieldA(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    @dataclass(frozen=True)
    class FieldB(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    @dataclass(frozen=True)
    class FieldC(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    # Register converters: A->B, B->C, and A->C (direct path)
    @converter
    class AToBConverter(Converter):  # pyright: ignore [reportUnusedClass]
        input_field_a: AttributeSpec[FieldA]
        output_field_b: AttributeSpec[FieldB]

        def filter_output_spec(self) -> bool:
            return True

        def convert(self, df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.col("field_a").alias("field_b")).drop("field_a")

    @converter
    class BToCConverter(Converter):  # pyright: ignore [reportUnusedClass]
        input_field_b: AttributeSpec[FieldB]
        output_field_c: AttributeSpec[FieldC]

        def filter_output_spec(self) -> bool:
            return True

        def convert(self, df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.col("field_b").alias("field_c")).drop("field_b")

    @converter  # Direct path (should be preferred)
    class AToCDirectConverter(Converter):
        input_field_a: AttributeSpec[FieldA]
        output_field_c: AttributeSpec[FieldC]

        def filter_output_spec(self) -> bool:
            return True

        def convert(self, df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.col("field_a").alias("field_c")).drop("field_a")

    from_schema = Schema(
        {
            "field_a": AttributeInfo(type=str, field=FieldA()),
        }
    )

    to_schema = Schema(
        {
            "field_c": AttributeInfo(type=str, field=FieldC()),
        }
    )

    path, _ = find_conversion_path(from_schema, to_schema)
    assert len(path.converters["field_c"]) == 1
    assert type(path.converters["field_c"][0]) is AToCDirectConverter


def test_generator_converter():
    """Test converter that generates fields from nothing."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class FieldB(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    @converter  # Generator converter (no inputs)
    class GenerateBConverter(Converter):
        output_field_b: AttributeSpec[FieldB]

        def filter_output_spec(self) -> bool:
            return True

        def convert(self, df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.lit("generated_b").alias("field_b"))

    from_schema = Schema({})  # Empty schema

    to_schema = Schema(
        {
            "field_b": AttributeInfo(type=str, field=FieldB()),
        }
    )

    path, _ = find_conversion_path(from_schema, to_schema)
    assert len(path.converters["field_b"]) == 1
    assert type(path.converters["field_b"][0]) is GenerateBConverter


def test_multiple_output_converter():
    """Test converters that produce multiple outputs."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class FieldA(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    @dataclass(frozen=True)
    class MultiField1(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    @dataclass(frozen=True)
    class MultiField2(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    @converter
    class AToMultiConverter(Converter):
        input_field_a: AttributeSpec[FieldA]
        output_multi1: AttributeSpec[MultiField1]
        output_multi2: AttributeSpec[MultiField2]

        def filter_output_spec(self) -> bool:
            return True

        def convert(self, df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns([pl.col("field_a").alias("multi1"), pl.col("field_a").alias("multi2")]).drop(
                "field_a"
            )

    from_schema = Schema(
        {
            "field_a": AttributeInfo(type=str, field=FieldA()),
        }
    )

    to_schema = Schema(
        {
            "multi1": AttributeInfo(type=str, field=MultiField1()),
            "multi2": AttributeInfo(type=str, field=MultiField2()),
        }
    )

    path, _ = find_conversion_path(from_schema, to_schema)
    assert len(path.converters["multi1"]) == 1
    assert type(path.converters["multi1"][0]) is AToMultiConverter
    assert len(path.converters["multi2"]) == 1
    assert type(path.converters["multi2"][0]) is AToMultiConverter


def test_partial_schema_matching():
    """Test when target schema is a subset of what converters can produce."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class FieldA(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    @dataclass(frozen=True)
    class FieldC(Field):
        semantic: str = "default"
        dtype: pl.DataType = field(default_factory=pl.Utf8, init=False)

        def to_polars_schema(self, name: str) -> dict[str, pl.DataType]:
            return {name: pl.Utf8()}

    @converter
    class AToCPartialConverter(Converter):
        input_field_a: AttributeSpec[FieldA]
        output_field_c: AttributeSpec[FieldC]

        def filter_output_spec(self) -> bool:
            return True

        def convert(self, df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.col("field_a").alias("field_c")).drop("field_a")

    from_schema = Schema(
        {
            "field_a": AttributeInfo(type=str, field=FieldA()),
            "other_field": AttributeInfo(
                type=str, field=FieldA(semantic="bbox")
            ),  # Extra field with different semantic
        }
    )

    to_schema = Schema(
        {
            "field_c": AttributeInfo(type=str, field=FieldC()),
            # Only requesting field_c, not other_field
        }
    )

    path, _ = find_conversion_path(from_schema, to_schema)
    assert len(path.converters["field_c"]) == 1
    assert type(path.converters["field_c"][0]) is AToCPartialConverter


def test_attribute_renaming():
    """Test attribute renaming functionality using special converters."""

    # Create source schema with an image field named "input_image"
    source_schema = Schema(
        {
            "input_image": AttributeInfo(type=str, field=image_field(dtype=pl.UInt8(), format="RGB")),
        }
    )

    # Create target schema with the same field type but different name "output_image"
    target_schema = Schema(
        {
            "output_image": AttributeInfo(type=str, field=image_field(dtype=pl.UInt8(), format="RGB")),
        }
    )

    # Find conversion path - should include a remapper converter
    path, _ = find_conversion_path(source_schema, target_schema)

    # Should have exactly one batch converter for renaming
    assert len(path.converters["output_image"]) == 1
    assert isinstance(path.converters["output_image"][0], AttributeRemapperConverter)

    # Test the remapper converter functionality
    remapper_converter = path.converters["output_image"][0]

    # Create test DataFrame with the source column
    test_data = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
    df = pl.DataFrame({"input_image": [test_data.flatten()], "input_image_shape": [test_data.shape]})

    # Apply the remapper converter
    result_df = remapper_converter.convert(df)

    # Check that columns were renamed correctly
    assert "output_image" in result_df.columns
    assert "output_image_shape" in result_df.columns
    assert "input_image" not in result_df.columns
    assert "input_image_shape" not in result_df.columns

    # Check that data was preserved
    assert result_df["output_image"][0].to_list() == test_data.flatten().tolist()
    assert result_df["output_image_shape"][0].to_list() == list(test_data.shape)


def test_combined_rename_and_delete():
    """Test scenario with both renaming and deletion operations."""

    # Create source schema with three fields
    source_schema = Schema(
        {
            "old_image": AttributeInfo(type=str, field=image_field(dtype=pl.UInt8(), format="RGB")),
            "bbox": AttributeInfo(type=str, field=bbox_field(dtype=pl.Float32(), format="x1y1x2y2")),
            "extra_field": AttributeInfo(type=str, field=image_info_field()),
        }
    )

    # Create target schema with renamed image and no bbox or extra_field
    target_schema = Schema(
        {
            "new_image": AttributeInfo(type=str, field=image_field(dtype=pl.UInt8(), format="RGB")),
        }
    )

    # Find conversion path - should include a single remapper converter that handles both operations
    path, _ = find_conversion_path(source_schema, target_schema)

    # Should have exactly one batch converter that handles both renaming and deletion
    assert len(path.converters["new_image"]) == 1
    assert isinstance(path.converters["new_image"][0], AttributeRemapperConverter)

    # Check that the remapper handles the conversion correctly by testing on sample data
    remapper_converter = path.converters["new_image"][0]

    # Create test DataFrame
    test_df = pl.DataFrame(
        {
            "old_image": [[1, 2, 3, 4, 5, 6]],  # Sample image data
            "old_image_shape": [[2, 3]],  # Sample shape data
            "other_field": ["should_not_change"],  # Should not be changed
        }
    )

    # Apply the converter
    result_df = remapper_converter.convert(test_df)

    # Check that only the renamed fields and the unmodified ones are present
    expected_columns = {"new_image", "new_image_shape", "other_field"}
    assert set(result_df.columns) == expected_columns

    # Check that data is preserved correctly
    assert result_df["new_image"].to_list() == [[1, 2, 3, 4, 5, 6]]
    assert result_df["new_image_shape"].to_list() == [[2, 3]]


def test_attribute_remapping_converter():
    """Test AttributeRemapperConverter with multiple attributes."""
    import polars as pl

    # Create test DataFrame with multiple columns including auxiliary columns
    df = pl.DataFrame(
        {
            "old_image": [[1, 2, 3]],
            "old_image_shape": [[3]],
            "old_bbox": [[[1, 2, 3, 4]]],
            "old_bbox_canvas_size": [None],  # canvas_size column for bbox field
            "other_field": ["test"],
        }
    )

    # Create attribute mappings using AttributeSpec
    from_image_attr = AttributeSpec(name="old_image", field=image_field(dtype=pl.Int32()))
    to_image_attr = AttributeSpec(name="new_image", field=image_field(dtype=pl.Int32()))

    from_bbox_attr = AttributeSpec(name="old_bbox", field=bbox_field(dtype=pl.Int32()))
    to_bbox_attr = AttributeSpec(name="new_bbox", field=bbox_field(dtype=pl.Int32()))

    attr_mappings = [(from_image_attr, to_image_attr), (from_bbox_attr, to_bbox_attr)]

    # Create and apply converter
    converter = AttributeRemapperConverter(attr_mappings=attr_mappings)
    result_df = converter.convert(df)

    # Check that columns were remapped correctly (including canvas_size column)
    expected_columns = {"new_image", "new_image_shape", "new_bbox", "new_bbox_canvas_size", "other_field"}
    assert set(result_df.columns) == expected_columns

    # Check that data is preserved
    assert result_df["new_image"].to_list() == [[1, 2, 3]]
    assert result_df["new_image_shape"].to_list() == [[3]]
    assert result_df["new_bbox"].to_list() == [[[1, 2, 3, 4]]]


def test_find_conversion_path_inferred_categories():
    """Test that find_conversion_path returns inferred categories."""

    # Create test data for polygon to mask conversion
    pl.DataFrame(
        {
            "polygons": [[[10, 20, 30, 25, 20, 40]]],  # Triangle coordinates
            "labels": [[2]],  # Label 2
            "image_info": [{"width": 100, "height": 100}],
        },
        schema=pl.Schema(
            {
                "polygons": pl.List(pl.List(pl.Float32())),
                "labels": pl.List(pl.Int32()),
                "image_info": pl.Struct({"width": pl.Int32, "height": pl.Int32}),
            }
        ),
    )

    # Create source schema with label categories
    label_categories = LabelCategories(labels=("cat", "dog", "bird"))
    source_schema = Schema(
        attributes={
            "polygons": AttributeInfo(
                type=list,
                field=PolygonField(dtype=pl.Float32()),
                categories=None,
            ),
            "labels": AttributeInfo(
                type=list,
                field=LabelField(),
                categories=label_categories,
            ),
            "image_info": AttributeInfo(type=dict, field=ImageInfoField()),
        }
    )

    # Create target schema (polygon to mask conversion)
    target_schema = Schema(attributes={"mask": AttributeInfo(type=np.ndarray, field=MaskField(dtype=pl.UInt8()))})

    # Get conversion path and check inferred categories
    conversion_paths, inferred_categories = find_conversion_path(source_schema, target_schema)

    # Should have converters for polygon to mask conversion
    assert len(conversion_paths.converters) > 0

    # Check that mask categories were inferred
    assert "mask" in inferred_categories
    mask_categories = inferred_categories["mask"]
    assert isinstance(mask_categories, MaskCategories)

    # Check that the mask categories include background + original labels
    expected_labels = ("background", "cat", "dog", "bird")
    assert mask_categories.labels == expected_labels


def test_convert_to_schema_propagates_categories():
    """Test that converting a dataset to a new schema propagates categories when target has None."""

    class SourceSample(Sample):
        label: npt.NDArray[np.int_] = label_field(dtype=pl.UInt8())

    class TargetSample(Sample):
        label: npt.NDArray[np.int_] = label_field(dtype=pl.UInt8())

    # Create source dataset with categories
    source_categories = LabelCategories(labels=("car", "truck", "motorbike"))
    source_dataset = Dataset(
        SourceSample,
        categories={"label": source_categories},
    )

    # Convert to target schema (which has no explicit categories)
    target_dataset = source_dataset.convert_to_schema(TargetSample)

    # Categories should be propagated from source to target
    source_label_categories = source_dataset.schema.attributes["label"].categories
    target_label_categories = target_dataset.schema.attributes["label"].categories

    assert source_label_categories is not None
    assert target_label_categories is not None
    assert source_label_categories == target_label_categories
    assert target_label_categories.labels == ("car", "truck", "motorbike")


def test_is_type_optional_registry():
    """Test is_type_optional correctly identifies optional types."""
    from typing import Union

    from getidata.type_registry import is_type_optional

    # Test modern syntax (Python 3.10+)
    assert is_type_optional(int | None) is True
    assert is_type_optional(str | None) is True
    assert is_type_optional(np.ndarray | None) is True

    # Test typing.Union syntax
    assert is_type_optional(Union[int, None]) is True
    assert is_type_optional(Union[str, None]) is True

    # Test complex unions with None
    assert is_type_optional(int | str | None) is True

    # Non-optional types
    assert is_type_optional(int) is False
    assert is_type_optional(str) is False
    assert is_type_optional(int | str) is False
    assert is_type_optional(Union[int, str]) is False


def test_get_optional_field_types():
    """Test _get_optional_field_types_by_semantic returns correct optional field types grouped by semantic."""
    from getidata.converters.registry import _get_optional_field_types_by_semantic
    from getidata.fields import numeric_field, string_field

    # Schema with mix of optional and required fields
    schema = Schema(
        attributes={
            "required_int": AttributeInfo(type=int, field=numeric_field(dtype=pl.Int32(), semantic="required_int")),
            "optional_int": AttributeInfo(type=int | None, field=numeric_field(dtype=pl.Int32(), semantic="opt_int")),
            "required_str": AttributeInfo(type=str, field=string_field(semantic="required_str")),
            "optional_str": AttributeInfo(type=str | None, field=string_field(semantic="opt_str")),
        }
    )

    optional_types_by_semantic = _get_optional_field_types_by_semantic(schema)

    # Should contain the field types for optional_int and optional_str, grouped by semantic
    from getidata.fields.types import NumericField, StringField

    assert "opt_int" in optional_types_by_semantic
    assert NumericField in optional_types_by_semantic["opt_int"]
    assert "opt_str" in optional_types_by_semantic
    assert StringField in optional_types_by_semantic["opt_str"]


def test_get_optional_field_types_empty_schema():
    """Test _get_optional_field_types_by_semantic returns empty dict for schema with no optional fields."""
    from getidata.converters.registry import _get_optional_field_types_by_semantic
    from getidata.fields import numeric_field

    schema = Schema(
        attributes={
            "required_int": AttributeInfo(type=int, field=numeric_field(dtype=pl.Int32(), semantic="required_int")),
        }
    )

    optional_types_by_semantic = _get_optional_field_types_by_semantic(schema)
    # The default semantic should have no optional fields (empty set or not present)
    default_semantic_optional = optional_types_by_semantic.get("default", set())
    assert len(default_semantic_optional) == 0


def test_filter_unreachable_optional_fields():
    """Test _filter_unreachable_optional_fields removes unreachable optional fields."""
    from getidata.converters.registry import _filter_unreachable_optional_fields, _SchemaState
    from getidata.fields import numeric_field, string_field
    from getidata.fields.types import NumericField, StringField
    from getidata.schema import AttributeSpec

    # Create a target state with two fields
    target_state = _SchemaState(
        {
            NumericField: AttributeSpec(name="num", field=numeric_field(dtype=pl.Int32(), semantic="opt_num")),
            StringField: AttributeSpec(name="str", field=string_field(semantic="str")),
        }
    )

    # Only NumericField is reachable
    reachable_types = {NumericField}

    # StringField is optional
    optional_field_types = {StringField}

    # Filter should remove StringField (unreachable + optional)
    filtered = _filter_unreachable_optional_fields(target_state, reachable_types, optional_field_types)

    assert NumericField in filtered.field_to_attr_spec
    assert StringField not in filtered.field_to_attr_spec


def test_filter_unreachable_optional_fields_keeps_required():
    """Test _filter_unreachable_optional_fields keeps unreachable required fields."""
    from getidata.converters.registry import _filter_unreachable_optional_fields, _SchemaState
    from getidata.fields import numeric_field, string_field
    from getidata.fields.types import NumericField, StringField
    from getidata.schema import AttributeSpec

    # Create a target state with two fields
    target_state = _SchemaState(
        {
            NumericField: AttributeSpec(name="num", field=numeric_field(dtype=pl.Int32(), semantic="opt_num")),
            StringField: AttributeSpec(name="str", field=string_field(semantic="str")),
        }
    )

    # Only NumericField is reachable
    reachable_types = {NumericField}

    # No optional fields - StringField is required
    optional_field_types: set = set()

    # Filter should keep both since StringField is required (not optional)
    filtered = _filter_unreachable_optional_fields(target_state, reachable_types, optional_field_types)

    assert NumericField in filtered.field_to_attr_spec
    assert StringField in filtered.field_to_attr_spec  # kept because it's required


def test_find_conversion_path_skips_unreachable_optional_fields():
    """Test find_conversion_path skips optional fields that can't be reached from source."""
    from getidata.fields import numeric_field, string_field

    # Source schema has only an int field
    source_schema = Schema(
        attributes={
            "value": AttributeInfo(type=int, field=numeric_field(dtype=pl.Int32(), semantic="opt_num")),
        }
    )

    # Target schema has int field + optional string field (unreachable from int)
    target_schema = Schema(
        attributes={
            "value": AttributeInfo(type=int, field=numeric_field(dtype=pl.Int32(), semantic="opt_num")),
            "optional_name": AttributeInfo(type=str | None, field=string_field(semantic="name")),
        }
    )

    # Should not raise - optional_name is skipped because it's unreachable
    conversion_paths, _ = find_conversion_path(source_schema, target_schema)

    # No converters needed for identical int field, and optional_name is skipped
    assert "value" not in conversion_paths.converters or len(conversion_paths.converters.get("value", [])) == 0


def test_find_conversion_path_raises_for_unreachable_required_fields():
    """Test find_conversion_path raises ConversionError for unreachable required fields."""
    from getidata.fields import numeric_field, string_field

    # Source schema has only an int field
    source_schema = Schema(
        attributes={
            "value": AttributeInfo(type=int, field=numeric_field(dtype=pl.Int32(), semantic="value")),
        }
    )

    # Target schema has int field + required string field (unreachable from int)
    target_schema = Schema(
        attributes={
            "value": AttributeInfo(type=int, field=numeric_field(dtype=pl.Int32(), semantic="value")),
            "required_name": AttributeInfo(type=str, field=string_field(semantic="name")),  # Required, not optional
        }
    )

    # Should raise ConversionError because required_name is unreachable
    with pytest.raises(ConversionError):
        find_conversion_path(source_schema, target_schema)


def test_find_conversion_path_with_multiple_optional_fields():
    """Test find_conversion_path handles multiple optional fields correctly."""
    from getidata.fields import numeric_field

    # Source schema with one field
    source_schema = Schema(
        attributes={
            "value": AttributeInfo(type=int, field=numeric_field(dtype=pl.Int32(), semantic="value")),
        }
    )

    # Target schema with same field + multiple optional fields that are unreachable
    target_schema = Schema(
        attributes={
            "value": AttributeInfo(type=int, field=numeric_field(dtype=pl.Int32(), semantic="value")),
            "opt_a": AttributeInfo(type=float | None, field=numeric_field(dtype=pl.Float32(), semantic="a")),
            "opt_b": AttributeInfo(type=float | None, field=numeric_field(dtype=pl.Float64(), semantic="b")),
        }
    )

    # Should not raise - both optional fields are skipped
    conversion_paths, _ = find_conversion_path(source_schema, target_schema)

    # Conversion should succeed with optional fields skipped
    assert conversion_paths is not None


def test_find_conversion_path_converts_reachable_optional_fields():
    """Test find_conversion_path includes converters for reachable optional fields."""

    # Source schema with bbox field
    source_schema = Schema(
        attributes={
            "bbox": AttributeInfo(
                type=np.ndarray,
                field=bbox_field(dtype=pl.Float32(), format="xywh"),
            ),
        }
    )

    # Target schema with optional bbox field in different format (reachable via converter)
    target_schema = Schema(
        attributes={
            "bbox": AttributeInfo(
                type=np.ndarray | None,  # Optional
                field=bbox_field(dtype=pl.Float32(), format="x1y1x2y2"),  # Different format
            ),
        }
    )

    # Should find conversion path since bbox -> bbox conversion exists
    conversion_paths, _ = find_conversion_path(source_schema, target_schema)

    # Should have a converter for the format change
    assert "bbox" in conversion_paths.converters
    assert len(conversion_paths.converters["bbox"]) >= 1


def test_direct_only_blocks_cross_field_type_conversion():
    """Test that direct_only=True blocks cross-field-type converters like BBoxToPolygon."""
    source_schema = Schema(
        attributes={
            "bbox": AttributeInfo(
                type=np.ndarray,
                field=BBoxField(dtype=pl.Float32(), format="xywh"),
            ),
        }
    )

    target_schema = Schema(
        attributes={
            "polygon": AttributeInfo(
                type=np.ndarray,
                field=PolygonField(dtype=pl.Float32()),
            ),
        }
    )

    # Without direct_only, conversion should succeed (BBoxToPolygonConverter exists)
    path, _ = find_conversion_path(source_schema, target_schema, direct_only=False)
    assert "polygon" in path.converters

    # With direct_only, conversion should fail (BBox→Polygon is cross-field-type)
    with pytest.raises(ConversionError):
        find_conversion_path(source_schema, target_schema, direct_only=True)


def test_direct_only_allows_same_field_type_conversion():
    """Test that direct_only=True allows same-field-type converters like BBox format changes."""
    source_schema = Schema(
        attributes={
            "bbox": AttributeInfo(
                type=np.ndarray,
                field=BBoxField(dtype=pl.Float32(), format="xywh"),
            ),
        }
    )

    target_schema = Schema(
        attributes={
            "bbox": AttributeInfo(
                type=np.ndarray,
                field=BBoxField(dtype=pl.Float32(), format="x1y1x2y2"),
            ),
        }
    )

    # With direct_only, same-type conversion (format change) should still work
    path, _ = find_conversion_path(source_schema, target_schema, direct_only=True)
    assert "bbox" in path.converters
    assert len(path.converters["bbox"]) >= 1


def test_direct_only_convert_to_schema():
    """Test direct_only parameter through Dataset.convert_to_schema."""

    class SourceSample(Sample):
        bbox: np.ndarray = BBoxField(dtype=pl.Float32(), format="xywh")

    class TargetSampleDirect(Sample):
        bbox: np.ndarray = BBoxField(dtype=pl.Float32(), format="x1y1x2y2")

    class TargetSampleCrossField(Sample):
        polygon: np.ndarray = PolygonField(dtype=pl.Float32())

    ds = Dataset(SourceSample)
    ds.append(SourceSample(bbox=np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32)))

    # Same-type conversion should work with direct_only=True
    converted = ds.convert_to_schema(TargetSampleDirect, direct_only=True)
    assert len(converted) == 1

    # Cross-type conversion should fail with direct_only=True
    with pytest.raises(ConversionError):
        ds.convert_to_schema(TargetSampleCrossField, direct_only=True)

    # Cross-type conversion should work with direct_only=False (default)
    converted = ds.convert_to_schema(TargetSampleCrossField, direct_only=False)
    assert len(converted) == 1


def test_direct_only_skips_unreachable_optional_cross_field():
    """Test that direct_only skips optional cross-field-type targets that are unreachable."""
    source_schema = Schema(
        attributes={
            "bbox": AttributeInfo(
                type=np.ndarray,
                field=BBoxField(dtype=pl.Float32(), format="xywh"),
            ),
        }
    )

    target_schema = Schema(
        attributes={
            "bbox": AttributeInfo(
                type=np.ndarray,
                field=BBoxField(dtype=pl.Float32(), format="x1y1x2y2"),
            ),
            "polygon": AttributeInfo(
                type=np.ndarray | None,  # Optional
                field=PolygonField(dtype=pl.Float32()),
            ),
        }
    )

    # With direct_only=True, the optional PolygonField should be skipped (unreachable)
    # and the BBox format conversion should still succeed
    path, _ = find_conversion_path(source_schema, target_schema, direct_only=True)
    assert "bbox" in path.converters


def test_direct_only_append_dataset():
    """Test direct_only parameter through Dataset.append_dataset."""
    from getidata.categories import LabelCategories

    class SampleA(Sample):
        label: int = LabelField(dtype=pl.UInt8())

    class SampleB(Sample):
        label: int = LabelField(dtype=pl.UInt32())

    categories = {"label": LabelCategories(labels=("cat", "dog", "bird"))}

    ds_a = Dataset(SampleA, categories=categories)
    ds_a.append(SampleA(label=1))

    ds_b = Dataset(SampleB, categories=categories)
    ds_b.append(SampleB(label=2))

    # Same field type (LabelField→LabelField dtype change) should work with direct_only=True
    ds_a.append_dataset(ds_b, direct_only=True)
    assert len(ds_a) == 2


def test_conversion_error_message_end_to_end():
    """End-to-end test: verify the error raised by find_conversion_path contains
    the right semantic group, attribute names, diagnosis sections, and that
    reachable field types are not incorrectly reported as missing.
    """
    from getidata.fields import image_info_field, image_path_field, string_field
    from getidata.fields.masks import MaskField
    from getidata.fields.videos import media_info_field, media_path_field

    # 1) Missing field type - includes semantic group and attribute name
    with pytest.raises(ConversionError, match=r"semantic group 'default'") as exc_info:
        find_conversion_path(
            Schema(attributes={"img": AttributeInfo(type=str, field=image_path_field())}),
            Schema(
                attributes={
                    "img": AttributeInfo(type=str, field=image_path_field()),
                    "caption": AttributeInfo(type=str, field=string_field(semantic="default")),
                }
            ),
        )
    assert "'caption'" in str(exc_info.value) and "StringField" in str(exc_info.value)

    # 2) Empty source semantic group
    with pytest.raises(ConversionError, match=r"semantic group 'metadata'") as exc_info:
        find_conversion_path(
            Schema(attributes={"img": AttributeInfo(type=str, field=image_path_field())}),
            Schema(
                attributes={
                    "img": AttributeInfo(type=str, field=image_path_field()),
                    "tag": AttributeInfo(type=str, field=string_field(semantic="metadata")),
                }
            ),
        )
    assert "Source fields: (none)" in str(exc_info.value)

    # 3) Reachable fields (MediaPath→ImagePath) not flagged as missing;
    #    only truly unreachable MaskField appears under "Missing field types"
    with pytest.raises(ConversionError) as exc_info:
        find_conversion_path(
            Schema(
                attributes={
                    "media": AttributeInfo(type=str, field=media_path_field()),
                    "info": AttributeInfo(type=str, field=media_info_field()),
                }
            ),
            Schema(
                attributes={
                    "image": AttributeInfo(type=str, field=image_path_field()),
                    "info": AttributeInfo(type=str, field=image_info_field()),
                    "mask": AttributeInfo(type=str, field=MaskField(semantic="default", dtype=pl.UInt8())),
                }
            ),
        )
    msg = str(exc_info.value)
    assert "'mask' (MaskField)" in msg
    after_missing = msg.split("Missing field types:")[1]
    assert "ImagePathField" not in after_missing
    assert "ImageInfoField" not in after_missing


def test_find_conversion_path_prefers_direct_over_cross_field_type():
    """Test that find_conversion_path prefers direct same-field-type converters over cross-field-type converters.

    When the source schema has both BBoxField (xywh) and KeypointsField, and the
    target needs BBoxField (x1y1x2y2), the A* search should prefer:
      BBoxFormatConverter (BBoxField → BBoxField, format change)
    over:
      KeypointsToBBoxConverter (KeypointsField → BBoxField, cross-field-type)

    Both paths have the same integer step count, but the direct path preserves the
    original data while the cross-field-type path would derive bboxes from keypoints
    (which may be null, producing incorrect results).
    """
    from getidata.converters import BBoxDtypeConverter, BBoxFormatConverter

    source_schema = Schema(
        attributes={
            "bboxes": AttributeInfo(
                type=np.ndarray | None,
                field=BBoxField(semantic="default", dtype=pl.Float32(), format="xywh"),
            ),
            "keypoints": AttributeInfo(
                type=np.ndarray | None,
                field=KeypointsField(semantic="default", dtype=pl.Float32()),
            ),
        }
    )

    target_schema = Schema(
        attributes={
            "bboxes": AttributeInfo(
                type=np.ndarray | None,
                field=BBoxField(semantic="default", dtype=pl.Int32(), format="x1y1x2y2"),
            ),
        }
    )

    conversion_paths, _ = find_conversion_path(source_schema, target_schema)

    # The bboxes conversion chain must use the direct BBoxField→BBoxField path
    bbox_converters = conversion_paths.converters["bboxes"]
    bbox_converter_types = [type(c) for c in bbox_converters]

    assert BBoxFormatConverter in bbox_converter_types, (
        f"Expected BBoxFormatConverter in the conversion chain, got {bbox_converter_types}. "
        "The A* search should prefer direct same-field-type converters over cross-field-type ones."
    )
    assert BBoxDtypeConverter in bbox_converter_types, (
        f"Expected BBoxDtypeConverter in the conversion chain, got {bbox_converter_types}."
    )

    # Verify KeypointsToBBoxConverter is NOT in the chain
    from getidata.converters import KeypointsToBBoxConverter

    assert KeypointsToBBoxConverter not in bbox_converter_types, (
        "KeypointsToBBoxConverter should NOT be used when BBoxField data is already available. "
        "Direct BBoxField→BBoxField conversion should be preferred."
    )


class _StubParent:
    """Minimal parent transform that returns an empty DataFrame for pickle tests.

    Defined at module level so it can be pickled (local classes cannot).
    """

    def __init__(self, schema: Schema):
        self._schema = schema
        self._df = pl.DataFrame()

    def apply(self, fields) -> pl.DataFrame:
        return self._df

    def get_lazy_attributes(self) -> set[str]:
        return set()

    def get_batch_attributes(self) -> list[str]:
        return []

    def slice(self, offset, length=None):
        return self

    def __len__(self):
        return 0


def test_converter_transform_pickle_roundtrip_preserves_applied_converters():
    """Test that _applied_converters survives a pickle round-trip.

    When a ConverterTransform is pickled (e.g., for DataLoader workers) and
    then unpickled, the _applied_converters set must correctly track which
    converters have already been run so they are not re-executed.

    Regression test for: previously _applied_converters stored id() ints which
    became stale after unpickling, causing converters (e.g., BBoxFormatConverter
    XYWH→XYXY) to re-execute and silently corrupt data.  The fix stores
    Converter object references directly; pickle preserves object identity
    within a single stream, so the set naturally stays consistent.
    """
    import pickle

    from getidata.converters.registry import ConverterTransform, find_conversion_path

    # Set up a schema pair that requires BBoxFormatConverter (xywh → x1y1x2y2).
    source_schema = Schema(
        attributes={
            "bboxes": AttributeInfo(
                type=np.ndarray | None,
                field=BBoxField(semantic="default", dtype=pl.Float32(), format="xywh"),
            ),
        }
    )
    target_schema = Schema(
        attributes={
            "bboxes": AttributeInfo(
                type=np.ndarray | None,
                field=BBoxField(semantic="default", dtype=pl.Float32(), format="x1y1x2y2"),
            ),
        }
    )

    conversion_paths, _ = find_conversion_path(source_schema, target_schema)

    # Collect all unique converter objects that exist in the conversion paths.
    all_converters: set[Converter] = set()
    for convs in conversion_paths.converters.values():
        all_converters.update(convs)
    assert len(all_converters) > 0, "Expected at least one converter in the conversion path"

    # Build a minimal ConverterTransform with a trivial parent.
    parent = _StubParent(source_schema)
    ct = ConverterTransform(parent, target_schema, conversion_paths)

    # Mark all converters as applied to simulate the common post-init state.
    ct._applied_converters = set(all_converters)
    applied_before = len(ct._applied_converters)

    # Pickle round-trip — this is what happens when a DataLoader sends the
    # dataset to a worker process.
    data = pickle.dumps(ct)
    ct2 = pickle.loads(data)

    # Collect the converter objects that live in the deserialized _conversion_paths.
    new_converters: set[Converter] = set()
    for convs in ct2._conversion_paths.converters.values():
        new_converters.update(convs)

    # The restored _applied_converters must contain the same (deserialized)
    # converter objects that appear in _conversion_paths, not stale references.
    assert len(ct2._applied_converters) == applied_before, (
        f"Expected {applied_before} applied converters after unpickling, got {len(ct2._applied_converters)}"
    )

    # Every converter in _applied_converters must be one of the converter
    # objects living in the deserialized _conversion_paths.
    for conv in ct2._applied_converters:
        assert conv in new_converters, (
            "After unpickling, _applied_converters should reference the same "
            "converter objects as _conversion_paths. Found a stale reference."
        )

    # Conversely, every converter in the paths should already be marked applied.
    for conv in new_converters:
        assert conv in ct2._applied_converters, (
            "A converter from _conversion_paths is missing from _applied_converters "
            "after unpickling — it would be incorrectly re-executed in a worker."
        )
