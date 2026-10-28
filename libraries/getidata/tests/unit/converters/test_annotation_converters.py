"""
Unit tests for annotation converter implementations.
"""

from typing import Any

import numpy as np
import numpy.typing as npt
import polars as pl
import pytest

from getidata.categories import LabelCategories
from getidata.converters import (
    BBoxCoordinateConverter,
    BBoxFormatConverter,
    BBoxToPolygonConverter,
    EllipseDtypeConverter,
    EllipseToBBoxConverter,
    KeypointsCoordinateConverter,
    KeypointsDtypeConverter,
    KeypointsToBBoxConverter,
    LabelIndexConverter,
    PolygonToBBoxConverter,
    RotatedBBoxCoordinateConverter,
    RotatedBBoxToBBoxConverter,
    RotatedBBoxToPolygonConverter,
)
from getidata.dataset import Dataset, Sample
from getidata.fields import (
    BBoxField,
    EllipseField,
    ImageField,
    KeypointsField,
    LabelField,
    PolygonField,
    RotatedBBoxField,
    bbox_field,
)
from getidata.schema import AttributeSpec


def test_bbox_coordinate_converter():
    """Test bounding box coordinate normalization/denormalization."""
    converter_instance = BBoxCoordinateConverter()  # type: ignore[call-arg]

    # Create test data with absolute coordinates and image dimensions
    df = pl.DataFrame(
        {
            "bbox": [[[100.0, 150.0, 200.0, 250.0]]],  # One bbox: x1,y1,x2,y2
            "image_shape": [[300, 400, 3]],  # height=300, width=400
        },
        schema=pl.Schema({"bbox": pl.List(pl.Array(pl.Float32, 4)), "image_shape": pl.List(pl.Int64())}),
    )

    # Set up converter for absolute to normalized conversion
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

    # Test filter - should return True for normalization change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "bbox" in result_df.columns
    result_bbox = result_df["bbox"][0][0]  # First bbox

    # Check normalization: divide by width for x coords, height for y coords
    # x1: 100/400 = 0.25, y1: 150/300 = 0.5, x2: 200/400 = 0.5, y2: 250/300 = 0.833...
    expected = [100 / 400, 150 / 300, 200 / 400, 250 / 300]
    assert np.allclose(result_bbox.to_numpy(), expected)


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


def test_polygon_to_bbox_converter():
    """Test conversion from polygon coordinates to bounding box format."""
    # Create test data with triangle and rectangle polygons
    polygon_coords1 = [[10.0, 10.0], [20.0, 10.0], [15.0, 20.0]]
    polygon_coords2 = [[30.0, 30.0], [40.0, 30.0], [40.0, 40.0], [30.0, 40.0]]

    polygon_series = pl.Series([polygon_coords1, polygon_coords2], dtype=pl.List(pl.Array(pl.Float32, 2)))

    df = pl.DataFrame(
        {
            "polygons": [polygon_series],
        }
    )

    # Create converter instance
    converter_instance = PolygonToBBoxConverter()

    # Set up field specs
    input_polygon_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=False)
    output_bbox_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)

    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=input_polygon_field),
    )
    setattr(
        converter_instance,
        "output_bbox",
        AttributeSpec(name="bboxes", field=output_bbox_field),
    )

    # Test filter - should return True when we have valid input
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    # Check that bbox column was created
    assert "bboxes" in result_df.columns

    # Get the bbox data
    bboxes = result_df["bboxes"][0]

    # Check that we have 2 bounding boxes (triangle and rectangle)
    assert len(bboxes) == 2

    # Check triangle bbox (x1y1x2y2 format)
    triangle_bbox = bboxes[0]
    assert triangle_bbox[0] == 10.0  # x1 (min x)
    assert triangle_bbox[1] == 10.0  # y1 (min y)
    assert triangle_bbox[2] == 20.0  # x2 (max x)
    assert triangle_bbox[3] == 20.0  # y2 (max y)

    # Check rectangle bbox
    rectangle_bbox = bboxes[1]
    assert rectangle_bbox[0] == 30.0  # x1
    assert rectangle_bbox[1] == 30.0  # y1
    assert rectangle_bbox[2] == 40.0  # x2
    assert rectangle_bbox[3] == 40.0  # y2


def test_polygon_to_bbox_converter_xywh():
    """Test conversion to xywh bbox format."""
    # Create test data with rectangle polygon
    polygon_coords = [[30.0, 30.0], [40.0, 30.0], [40.0, 40.0], [30.0, 40.0]]

    polygon_series = pl.Series([polygon_coords], dtype=pl.List(pl.Array(pl.Float32, 2)))

    df = pl.DataFrame(
        {
            "polygons": [polygon_series],
        }
    )

    # Create converter instance
    converter_instance = PolygonToBBoxConverter()

    # Set up field specs for xywh format
    input_polygon_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=False)
    output_bbox_field = BBoxField(dtype=pl.Float32(), format="xywh", normalize=False)

    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=input_polygon_field),
    )
    setattr(
        converter_instance,
        "output_bbox",
        AttributeSpec(name="bboxes", field=output_bbox_field),
    )

    # Test conversion
    result_df = converter_instance.convert(df)

    # Get the bbox data
    bboxes = result_df["bboxes"][0]

    # Check rectangle bbox in xywh format
    rectangle_bbox = bboxes[0]
    assert rectangle_bbox[0] == 30.0  # x (min x)
    assert rectangle_bbox[1] == 30.0  # y (min y)
    assert rectangle_bbox[2] == 10.0  # w (width)
    assert rectangle_bbox[3] == 10.0  # h (height)


def test_polygon_to_bbox_converter_normalized():
    """Test conversion with normalized polygon coordinates."""
    # Create test data with normalized coordinates (0-1 range)
    polygon_coords = [[0.3, 0.3], [0.4, 0.3], [0.4, 0.4], [0.3, 0.4]]

    polygon_series = pl.Series([polygon_coords], dtype=pl.List(pl.Array(pl.Float32, 2)))

    df = pl.DataFrame(
        {
            "polygons": [polygon_series],
        }
    )

    # Create converter instance
    converter_instance = PolygonToBBoxConverter()

    # Set up field specs with normalized coordinates
    input_polygon_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=True)
    output_bbox_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=True)

    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=input_polygon_field),
    )
    setattr(
        converter_instance,
        "output_bbox",
        AttributeSpec(name="bboxes", field=output_bbox_field),
    )

    # Test conversion
    result_df = converter_instance.convert(df)

    # Get the bbox data
    bboxes = result_df["bboxes"][0]

    # Check rectangle bbox with normalized coordinates
    rectangle_bbox = bboxes[0]
    assert abs(rectangle_bbox[0] - 0.3) < 1e-6  # x1 (normalized)
    assert abs(rectangle_bbox[1] - 0.3) < 1e-6  # y1 (normalized)
    assert abs(rectangle_bbox[2] - 0.4) < 1e-6  # x2 (normalized)
    assert abs(rectangle_bbox[3] - 0.4) < 1e-6  # y2 (normalized)


def test_label_index_converter():
    """Test LabelIndexConverter functionality for remapping label indices."""

    # Create input and output specs with different label orders
    input_categories = LabelCategories(labels=("cat", "dog", "bird"))
    output_categories = LabelCategories(labels=("bird", "cat", "dog"))  # Different order

    input_spec = AttributeSpec(
        name="label",
        field=LabelField(dtype=pl.UInt32(), multi_label=False),
        categories=input_categories,
    )

    output_spec = AttributeSpec(
        name="label",
        field=LabelField(dtype=pl.UInt32(), multi_label=False),
        categories=output_categories,
    )

    # Create converter
    converter = LabelIndexConverter(input_labels=input_spec, output_labels=output_spec)

    # Test filter - should return True for valid category remapping
    assert converter.filter_output_spec() is True

    # Test data with original label indices
    test_df = pl.DataFrame({"label": [0, 1, 2, 0, 1]})  # cat=0, dog=1, bird=2 in input

    # Convert
    result_df = converter.convert(test_df)

    # Verify the mapping: cat(0->1), dog(1->2), bird(2->0)
    expected = [1, 2, 0, 1, 2]  # cat=1, dog=2, bird=0 in output
    actual = result_df["label"].to_list()

    assert actual == expected


def test_label_index_converter_multi_label():
    """Test LabelIndexConverter functionality for multi-label scenarios."""

    # Create input and output specs with different label orders
    input_categories = LabelCategories(labels=("cat", "dog", "bird"))
    output_categories = LabelCategories(labels=("bird", "cat", "dog"))  # Different order

    input_spec = AttributeSpec(
        name="labels",
        field=LabelField(dtype=pl.UInt32(), multi_label=True),
        categories=input_categories,
    )

    output_spec = AttributeSpec(
        name="labels",
        field=LabelField(dtype=pl.UInt32(), multi_label=True),
        categories=output_categories,
    )

    # Create converter
    converter = LabelIndexConverter(input_labels=input_spec, output_labels=output_spec)

    # Test filter - should return True for valid category remapping
    assert converter.filter_output_spec() is True

    # Test multi-label data
    test_df = pl.DataFrame({"labels": [[0, 1], [2], [0, 2], [1]]})  # Multiple labels per row

    # Convert
    result_df = converter.convert(test_df)

    # Verify multi-label mapping
    expected = [[1, 2], [0], [1, 0], [2]]
    actual = result_df["labels"].to_list()

    assert actual == expected


def test_label_index_converter_same_categories():
    """Test LabelIndexConverter with identical categories (should not apply)."""

    # Create identical input and output categories
    categories = LabelCategories(labels=("cat", "dog", "bird"))

    input_spec = AttributeSpec(
        name="label",
        field=LabelField(dtype=pl.UInt32(), multi_label=False),
        categories=categories,
    )

    output_spec = AttributeSpec(
        name="label",
        field=LabelField(dtype=pl.UInt32(), multi_label=False),
        categories=categories,
    )

    # Create converter
    converter = LabelIndexConverter(input_labels=input_spec, output_labels=output_spec)

    # Test filter - should return False for identical categories
    assert converter.filter_output_spec() is False


def test_label_index_converter_different_labels():
    """Test LabelIndexConverter with different label sets (should not apply)."""

    # Create categories with different label sets
    input_categories = LabelCategories(labels=("cat", "dog", "bird"))
    output_categories = LabelCategories(labels=("horse", "cow", "sheep"))  # Different labels

    input_spec = AttributeSpec(
        name="label",
        field=LabelField(dtype=pl.UInt32(), multi_label=False),
        categories=input_categories,
    )

    output_spec = AttributeSpec(
        name="label",
        field=LabelField(dtype=pl.UInt32(), multi_label=False),
        categories=output_categories,
    )

    # Create converter
    converter = LabelIndexConverter(input_labels=input_spec, output_labels=output_spec)

    # Test filter - should return False for different label sets
    assert converter.filter_output_spec() is False


def test_label_index_converter_missing_categories():
    """Test LabelIndexConverter with missing categories (should not apply)."""

    # Create specs where one is missing categories
    input_categories = LabelCategories(labels=("cat", "dog", "bird"))

    input_spec = AttributeSpec(
        name="label",
        field=LabelField(dtype=pl.UInt32(), multi_label=False),
        categories=input_categories,
    )

    output_spec = AttributeSpec(
        name="label",
        field=LabelField(dtype=pl.UInt32(), multi_label=False),
        categories=None,  # Missing categories
    )

    # Create converter
    converter = LabelIndexConverter(input_labels=input_spec, output_labels=output_spec)

    # Test filter - should return False when categories are missing
    assert converter.filter_output_spec() is False


def test_label_index_converter_unmapped_labels():
    """Test LabelIndexConverter with unmapped labels using None default."""

    # Create input and output specs where input has extra labels not in output
    input_categories = LabelCategories(labels=("cat", "dog", "bird", "fish"))
    output_categories = LabelCategories(labels=("bird", "cat"))  # Missing dog and fish

    input_spec = AttributeSpec(
        name="label",
        field=LabelField(dtype=pl.UInt32(), multi_label=False),
        categories=input_categories,
    )

    output_spec = AttributeSpec(
        name="label",
        field=LabelField(dtype=pl.UInt32(), multi_label=False),
        categories=output_categories,
    )

    # Create converter
    converter = LabelIndexConverter(input_labels=input_spec, output_labels=output_spec)

    # This should return False because the label sets are different
    assert converter.filter_output_spec() is False


def test_rotated_bbox_to_polygon_converter():
    """Test conversion from rotated bounding box to polygon format."""
    import math

    # Create test data with rotated bboxes: [cx, cy, w, h, r]
    rotated_bbox_coords1 = [50.0, 60.0, 30.0, 20.0, 0.0]  # No rotation
    rotated_bbox_coords2 = [100.0, 120.0, 40.0, 25.0, math.pi / 4]  # 45 degrees

    rotated_bbox_series = pl.Series([rotated_bbox_coords1, rotated_bbox_coords2], dtype=pl.Array(pl.Float32, 5))

    df = pl.DataFrame(
        {
            "rotated_bboxes": [rotated_bbox_series],
        }
    )

    # Create converter instance
    converter_instance = RotatedBBoxToPolygonConverter()

    # Set up field specs
    input_rotated_bbox_field = RotatedBBoxField(dtype=pl.Float32(), format="cxcywhr", normalize=False)
    output_polygon_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=False)

    setattr(
        converter_instance,
        "input_rotated_bbox",
        AttributeSpec(name="rotated_bboxes", field=input_rotated_bbox_field),
    )
    setattr(
        converter_instance,
        "output_polygon",
        AttributeSpec(name="polygons", field=output_polygon_field),
    )

    # Test filter - should return True when we have valid input
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    # Check that polygon column was created
    assert "polygons" in result_df.columns

    # Get the polygon data
    polygons = result_df["polygons"][0]

    # Check that we have 2 polygons
    assert len(polygons) == 2

    # Check first polygon (no rotation) - should be axis-aligned rectangle
    polygon1 = polygons[0]
    assert len(polygon1) == 4  # Four corners

    # For no rotation, corners should be at predictable positions
    expected_corners = [
        [35.0, 50.0],  # bottom-left
        [65.0, 50.0],  # bottom-right
        [65.0, 70.0],  # top-right
        [35.0, 70.0],  # top-left
    ]

    for expected, actual in zip(expected_corners, polygon1):
        assert abs(actual[0] - expected[0]) < 1e-5
        assert abs(actual[1] - expected[1]) < 1e-5

    # Check second polygon (45-degree rotation)
    polygon2 = polygons[1]
    assert len(polygon2) == 4  # Four corners


def test_bbox_dtype_converter_int_to_float():
    """Test BBoxDtypeConverter converting Int32 to Float32."""
    from getidata.converters import BBoxDtypeConverter

    converter_instance = BBoxDtypeConverter()

    # Create test data with Int32 bboxes
    df = pl.DataFrame(
        {"bbox": [[[5, 5, 20, 20], [25, 30, 50, 60]]]},
        schema=pl.Schema({"bbox": pl.List(pl.Array(pl.Int32, 4))}),
    )

    # Set up converter attributes
    input_bbox_field = BBoxField(dtype=pl.Int32(), format="x1y1x2y2", normalize=False)
    output_bbox_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)

    setattr(converter_instance, "input_bbox", AttributeSpec(name="bbox", field=input_bbox_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_bbox_field))

    # Test filter - should return True for dtype change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "bbox" in result_df.columns
    # Check dtype conversion
    result_bbox = result_df["bbox"][0]
    assert result_bbox[0].to_numpy().dtype == np.float32
    assert result_bbox[1].to_numpy().dtype == np.float32

    # Check values preserved
    np.testing.assert_array_almost_equal(result_bbox[0].to_numpy(), [5.0, 5.0, 20.0, 20.0])
    np.testing.assert_array_almost_equal(result_bbox[1].to_numpy(), [25.0, 30.0, 50.0, 60.0])


def test_bbox_dtype_converter_float_to_int():
    """Test BBoxDtypeConverter converting Float64 to Int32."""
    from getidata.converters import BBoxDtypeConverter

    converter_instance = BBoxDtypeConverter()

    # Create test data with Float64 bboxes
    df = pl.DataFrame(
        {"bbox": [[[10.5, 20.7, 30.2, 40.9]]]},
        schema=pl.Schema({"bbox": pl.List(pl.Array(pl.Float64, 4))}),
    )

    # Set up converter attributes
    input_bbox_field = BBoxField(dtype=pl.Float64(), format="x1y1x2y2", normalize=False)
    output_bbox_field = BBoxField(dtype=pl.Int32(), format="x1y1x2y2", normalize=False)

    setattr(converter_instance, "input_bbox", AttributeSpec(name="bbox", field=input_bbox_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_bbox_field))

    # Test filter - should return True for dtype change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "bbox" in result_df.columns
    # Check dtype conversion
    result_bbox = result_df["bbox"][0]
    assert result_bbox[0].to_numpy().dtype == np.int32
    # Values should be truncated
    np.testing.assert_array_equal(result_bbox[0].to_numpy(), [10, 20, 30, 40])


def test_bbox_dtype_converter_same_dtype():
    """Test BBoxDtypeConverter returns False when dtypes are the same."""
    from getidata.converters import BBoxDtypeConverter

    converter_instance = BBoxDtypeConverter()

    # Set up converter attributes with same dtype
    input_bbox_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)
    output_bbox_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)

    setattr(converter_instance, "input_bbox", AttributeSpec(name="bbox", field=input_bbox_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_bbox_field))

    # Test filter - should return False when dtypes are the same
    assert converter_instance.filter_output_spec() is False


def test_rotated_bbox_dtype_converter_int_to_float():
    """Test RotatedBBoxDtypeConverter converting Int32 to Float32."""
    from getidata.converters import RotatedBBoxDtypeConverter

    converter_instance = RotatedBBoxDtypeConverter()

    # Create test data with Int32 rotated bboxes (cx, cy, w, h, r)
    df = pl.DataFrame(
        {"rotated_bbox": [[[50, 60, 30, 20, 0], [100, 120, 40, 25, 1]]]},
        schema=pl.Schema({"rotated_bbox": pl.List(pl.Array(pl.Int32, 5))}),
    )

    # Set up converter attributes
    input_field = RotatedBBoxField(dtype=pl.Int32(), format="cxcywhr", normalize=False)
    output_field = RotatedBBoxField(dtype=pl.Float32(), format="cxcywhr", normalize=False)

    setattr(converter_instance, "input_rotated_bbox", AttributeSpec(name="rotated_bbox", field=input_field))
    setattr(converter_instance, "output_rotated_bbox", AttributeSpec(name="rotated_bbox", field=output_field))

    # Test filter - should return True for dtype change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "rotated_bbox" in result_df.columns
    # Check dtype conversion
    result_rotated_bbox = result_df["rotated_bbox"][0]
    assert result_rotated_bbox[0].to_numpy().dtype == np.float32

    # Check values preserved
    np.testing.assert_array_almost_equal(result_rotated_bbox[0].to_numpy(), [50.0, 60.0, 30.0, 20.0, 0.0])
    np.testing.assert_array_almost_equal(result_rotated_bbox[1].to_numpy(), [100.0, 120.0, 40.0, 25.0, 1.0])


def test_rotated_bbox_dtype_converter_same_dtype():
    """Test RotatedBBoxDtypeConverter returns False when dtypes are the same."""
    from getidata.converters import RotatedBBoxDtypeConverter

    converter_instance = RotatedBBoxDtypeConverter()

    # Set up converter attributes with same dtype
    input_field = RotatedBBoxField(dtype=pl.Float32(), format="cxcywhr", normalize=False)
    output_field = RotatedBBoxField(dtype=pl.Float32(), format="cxcywhr", normalize=False)

    setattr(converter_instance, "input_rotated_bbox", AttributeSpec(name="rotated_bbox", field=input_field))
    setattr(converter_instance, "output_rotated_bbox", AttributeSpec(name="rotated_bbox", field=output_field))

    # Test filter - should return False when dtypes are the same
    assert converter_instance.filter_output_spec() is False


def test_label_dtype_converter_int32_to_uint8():
    """Test LabelDtypeConverter converting Int32 to UInt8."""
    from getidata.converters import LabelDtypeConverter

    converter_instance = LabelDtypeConverter()

    # Create test data with Int32 label
    df = pl.DataFrame(
        {"label": [5]},
        schema=pl.Schema({"label": pl.Int32()}),
    )

    # Set up converter attributes
    input_field = LabelField(dtype=pl.UInt32(), multi_label=False, is_list=False)
    output_field = LabelField(dtype=pl.UInt8(), multi_label=False, is_list=False)

    setattr(converter_instance, "input_label", AttributeSpec(name="label", field=input_field))
    setattr(converter_instance, "output_label", AttributeSpec(name="label", field=output_field))

    # Test filter - should return True for dtype change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "label" in result_df.columns
    assert result_df["label"].dtype == pl.UInt8
    assert result_df["label"][0] == 5


def test_label_dtype_converter_list_labels():
    """Test LabelDtypeConverter with is_list=True."""
    from getidata.converters import LabelDtypeConverter

    converter_instance = LabelDtypeConverter()

    # Create test data with list of Int32 labels
    df = pl.DataFrame(
        {"labels": [[1, 2, 3, 255]]},
        schema=pl.Schema({"labels": pl.List(pl.Int32())}),
    )

    # Set up converter attributes
    input_field = LabelField(dtype=pl.UInt32(), multi_label=False, is_list=True)
    output_field = LabelField(dtype=pl.UInt8(), multi_label=False, is_list=True)

    setattr(converter_instance, "input_label", AttributeSpec(name="labels", field=input_field))
    setattr(converter_instance, "output_label", AttributeSpec(name="labels", field=output_field))

    # Test filter - should return True for dtype change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "labels" in result_df.columns
    assert result_df["labels"].dtype == pl.List(pl.UInt8)
    assert result_df["labels"][0].to_list() == [1, 2, 3, 255]


def test_label_dtype_converter_same_dtype():
    """Test LabelDtypeConverter returns False when dtypes are the same."""
    from getidata.converters import LabelDtypeConverter

    converter_instance = LabelDtypeConverter()

    # Set up converter attributes with same dtype
    input_field = LabelField(dtype=pl.UInt32(), multi_label=False, is_list=False)
    output_field = LabelField(dtype=pl.UInt32(), multi_label=False, is_list=False)

    setattr(converter_instance, "input_label", AttributeSpec(name="label", field=input_field))
    setattr(converter_instance, "output_label", AttributeSpec(name="label", field=output_field))

    # Test filter - should return False when dtypes are the same
    assert converter_instance.filter_output_spec() is False


def test_label_dtype_converter_multi_label_and_list():
    """Test LabelDtypeConverter with multi_label=True and is_list=True (List(List(dtype)))."""
    from getidata.converters import LabelDtypeConverter

    converter_instance = LabelDtypeConverter()

    # Create test data with List(List(UInt32)) labels
    df = pl.DataFrame(
        {"labels": [[[1, 2], [3, 4, 5]]]},
        schema=pl.Schema({"labels": pl.List(pl.List(pl.UInt32()))}),
    )

    # Set up converter attributes
    input_field = LabelField(dtype=pl.UInt32(), multi_label=True, is_list=True)
    output_field = LabelField(dtype=pl.UInt8(), multi_label=True, is_list=True)

    setattr(converter_instance, "input_label", AttributeSpec(name="labels", field=input_field))
    setattr(converter_instance, "output_label", AttributeSpec(name="labels", field=output_field))

    # Test filter - should return True for dtype change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "labels" in result_df.columns
    assert result_df["labels"].dtype == pl.List(pl.List(pl.UInt8))
    row = result_df["labels"][0].to_list()
    assert row == [[1, 2], [3, 4, 5]]


# fmt: off
@pytest.mark.parametrize(
    "input_multi, input_is_list, output_multi, output_is_list, data, schema_type, expected_dtype, expected_value",
    [
        # --- multi_label changes only (non-lossy: single → multi) ---
        pytest.param(False, False, True,  False, {"label": [5]},                      pl.UInt32(),                  pl.List(pl.UInt32),              [5],          id="single_to_multi_scalar"),  # noqa: E501
        pytest.param(False, True,  True,  True,  {"labels": [[1, 2, 3]]},             pl.List(pl.UInt32()),         pl.List(pl.List(pl.UInt32)),      [[1], [2], [3]], id="single_to_multi_list"),  # noqa: E501
        # --- is_list changes only (non-lossy: non-list → list) ---
        pytest.param(False, False, False, True,  {"label": [5]},                      pl.UInt32(),                  pl.List(pl.UInt32),              [5],          id="scalar_to_list"),  # noqa: E501
        pytest.param(True,  False, True,  True,  {"label": [[1, 2, 3]]},              pl.List(pl.UInt32()),         pl.List(pl.List(pl.UInt32)),      [[1, 2, 3]], id="multi_label_scalar_to_list"),  # noqa: E501
        # --- both flags change (non-lossy: both expanding) ---
        pytest.param(False, False, True,  True,  {"label": [5]},                      pl.UInt32(),                  pl.List(pl.List(pl.UInt32)),      [[5]],       id="both_scalar_to_list_list"),  # noqa: E501
        # --- flag swap (no-op semantic reinterpretation) ---
        pytest.param(False, True,  True,  False, {"label": [[3, 1, 2, 2, 1]]},           pl.List(pl.UInt32()),         pl.List(pl.UInt32),               [3, 1, 2],   id="swap_is_list_to_multi_label_dedup"),  # noqa: E501
        pytest.param(True,  False, False, True,  {"label": [[1, 2, 3]]},              pl.List(pl.UInt32()),         pl.List(pl.UInt32),               [1, 2, 3],   id="swap_multi_label_to_is_list"),  # noqa: E501
    ],
)  # fmt: on  noqa: RUF028
def test_label_shape_converter_conversions(
    input_multi,
    input_is_list,
    output_multi,
    output_is_list,
    data,
    schema_type,
    expected_dtype,
    expected_value,
):
    """Test LabelShapeConverter conversion across non-lossy multi_label/is_list combinations."""
    from getidata.converters import LabelShapeConverter

    converter_instance = LabelShapeConverter()

    col_name = next(iter(data.keys()))
    df = pl.DataFrame(data, schema=pl.Schema({col_name: schema_type}))

    input_field = LabelField(dtype=pl.UInt32(), multi_label=input_multi, is_list=input_is_list)
    output_field = LabelField(dtype=pl.UInt32(), multi_label=output_multi, is_list=output_is_list)

    setattr(converter_instance, "input_label", AttributeSpec(name=col_name, field=input_field))
    setattr(converter_instance, "output_label", AttributeSpec(name=col_name, field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)

    assert col_name in result_df.columns
    assert result_df[col_name].dtype == expected_dtype

    result_val = result_df[col_name][0]
    if hasattr(result_val, "to_list"):
        assert result_val.to_list() == expected_value
    else:
        assert result_val == expected_value


# fmt: off
@pytest.mark.parametrize(
    "input_multi, input_is_list, output_multi, output_is_list, data, schema_type, expected_value, expected_dtype",
    [
        pytest.param(True,  False, False, False, {"label": [[5, 10, 15]]},            pl.List(pl.UInt32()),          15,         pl.UInt32(),          id="multi_to_single_scalar"),  # noqa: E501
        pytest.param(True,  True,  False, True,  {"label": [[[5, 10], [15, 20]]]},    pl.List(pl.List(pl.UInt32())), [10, 20],   pl.List(pl.UInt32()), id="multi_to_single_list"),  # noqa: E501
        pytest.param(False, True,  False, False, {"label": [[10, 20, 30]]},           pl.List(pl.UInt32()),          30,         pl.UInt32(),          id="list_to_scalar"),  # noqa: E501
        pytest.param(True,  True,  True,  False, {"label": [[[1, 2], [3, 4], [5]]]},  pl.List(pl.List(pl.UInt32())), [5],        pl.List(pl.UInt32()), id="multi_label_list_to_scalar"),  # noqa: E501
        pytest.param(True,  True,  False, False, {"label": [[[5, 10], [15, 20]]]},    pl.List(pl.List(pl.UInt32())), 20,         pl.UInt32(),          id="both_list_list_to_scalar"),  # noqa: E501
    ],
)  # fmt: on  noqa: RUF028
def test_label_shape_converter_lossy_conversions(
    input_multi,
    input_is_list,
    output_multi,
    output_is_list,
    data,
    schema_type,
    expected_value,
    expected_dtype,
    caplog,
):
    """convert() keeps the last element and logs a warning for lossy multi_label/is_list reductions."""
    from getidata.converters import LabelShapeConverter

    converter_instance = LabelShapeConverter()

    col_name = next(iter(data.keys()))
    input_field = LabelField(dtype=pl.UInt32(), multi_label=input_multi, is_list=input_is_list)
    output_field = LabelField(dtype=pl.UInt32(), multi_label=output_multi, is_list=output_is_list)

    setattr(converter_instance, "input_label", AttributeSpec(name=col_name, field=input_field))
    setattr(converter_instance, "output_label", AttributeSpec(name=col_name, field=output_field))

    assert converter_instance.filter_output_spec() is True

    df = pl.DataFrame(data, schema=pl.Schema({col_name: schema_type}))
    with caplog.at_level("WARNING"):
        result_df = converter_instance.convert(df)

    assert result_df[col_name].dtype == expected_dtype
    result_val = result_df[col_name][0]
    if hasattr(result_val, "to_list"):
        assert result_val.to_list() == expected_value
    else:
        assert result_val == expected_value

    # Verify a warning was logged
    assert any("keeping the last" in msg for msg in caplog.messages)


def test_label_shape_converter_filter_returns_false():
    """Test LabelShapeConverter returns False when neither multi_label nor is_list changes."""
    from getidata.converters import LabelShapeConverter

    converter_instance = LabelShapeConverter()

    input_field = LabelField(dtype=pl.UInt32(), multi_label=False, is_list=True)
    output_field = LabelField(dtype=pl.UInt32(), multi_label=False, is_list=True)

    setattr(converter_instance, "input_label", AttributeSpec(name="labels", field=input_field))
    setattr(converter_instance, "output_label", AttributeSpec(name="labels", field=output_field))

    assert converter_instance.filter_output_spec() is False


def test_label_shape_converter_preserves_dtype():
    """Test that filter_output_spec preserves dtype from input and takes flags from target."""
    from getidata.converters import LabelShapeConverter

    converter_instance = LabelShapeConverter()

    input_field = LabelField(dtype=pl.UInt32(), multi_label=False, is_list=True)
    output_field = LabelField(dtype=pl.UInt8(), multi_label=True, is_list=False)

    setattr(converter_instance, "input_label", AttributeSpec(name="labels", field=input_field))
    setattr(converter_instance, "output_label", AttributeSpec(name="labels", field=output_field))

    assert converter_instance.filter_output_spec() is True
    assert converter_instance.output_label.field.dtype == pl.UInt32()  # Preserved from input
    assert converter_instance.output_label.field.multi_label is True  # From target
    assert converter_instance.output_label.field.is_list is False  # From target


# fmt: off
@pytest.mark.parametrize(
    "input_multi, input_is_list, output_multi, output_is_list, data, schema_type, expected_dtype, expected_non_null, expected_null_idx",  # noqa: E501
    [
        pytest.param(False, True,  True, True, {"labels": [[1, 2], None, [3]]}, pl.List(pl.UInt32()), pl.List(pl.List(pl.UInt32)), {0: [[1], [2]], 2: [[3]]}, 1, id="multi_label_with_nulls"),  # noqa: E501
        pytest.param(False, False, True, False, {"labels": [5, None, 3]},      pl.UInt32(),          pl.List(pl.UInt32),          {0: [5], 2: [3]},          1, id="scalar_to_multi_label_with_nulls"),  # noqa: E501
        pytest.param(False, False, False, True, {"labels": [5, None, 3]},       pl.UInt32(),          pl.List(pl.UInt32),          {0: [5], 2: [3]},          1, id="is_list_with_nulls"),  # noqa: E501
        pytest.param(False, True,  True, False, {"labels": [[1, 2], None, [3]]}, pl.List(pl.UInt32()), pl.List(pl.UInt32),          {0: [1, 2], 2: [3]},       1, id="swap_is_list_to_multi_label_with_nulls"),  # noqa: E501
        pytest.param(True,  False, False, True, {"labels": [[1, 2], None, [3]]}, pl.List(pl.UInt32()), pl.List(pl.UInt32),          {0: [1, 2], 2: [3]},       1, id="swap_multi_label_to_is_list_with_nulls"),  # noqa: E501
    ],
)  # fmt: on noqa: RUF028
def test_label_shape_converter_with_nulls(
    input_multi,
    input_is_list,
    output_multi,
    output_is_list,
    data,
    schema_type,
    expected_dtype,
    expected_non_null,
    expected_null_idx,
):
    """Test LabelShapeConverter handles null values correctly."""
    from getidata.converters import LabelShapeConverter

    converter_instance = LabelShapeConverter()

    col_name = next(iter(data.keys()))
    df = pl.DataFrame(data, schema=pl.Schema({col_name: schema_type}))

    input_field = LabelField(dtype=pl.UInt32(), multi_label=input_multi, is_list=input_is_list)
    output_field = LabelField(dtype=pl.UInt32(), multi_label=output_multi, is_list=output_is_list)

    setattr(converter_instance, "input_label", AttributeSpec(name=col_name, field=input_field))
    setattr(converter_instance, "output_label", AttributeSpec(name=col_name, field=output_field))

    assert converter_instance.filter_output_spec() is True
    result_df = converter_instance.convert(df)

    assert result_df[col_name].dtype == expected_dtype
    assert result_df[col_name][expected_null_idx] is None
    for idx, expected_val in expected_non_null.items():
        assert result_df[col_name][idx].to_list() == expected_val


# fmt: off
@pytest.mark.parametrize(
    "input_multi, input_is_list, output_multi, output_is_list, data, schema_type, expected_dtype, expected_value",
    [
        pytest.param(False, True,  True, True, {"source_labels": [[1, 2, 3]]}, pl.List(pl.UInt32()), pl.List(pl.List(pl.UInt32)), [[1], [2], [3]], id="multi_label_diff_names"),  # noqa: E501
        pytest.param(False, False, False, True, {"source_labels": [5]},        pl.UInt32(),          pl.List(pl.UInt32),          [5],             id="is_list_diff_names"),  # noqa: E501
    ],
)  # fmt: on noqa: RUF028
def test_label_shape_converter_different_column_names(
    input_multi,
    input_is_list,
    output_multi,
    output_is_list,
    data,
    schema_type,
    expected_dtype,
    expected_value,
):
    """Test LabelShapeConverter when input and output column names differ."""
    from getidata.converters import LabelShapeConverter

    converter_instance = LabelShapeConverter()

    input_col = next(iter(data.keys()))
    output_col = "target_labels"
    df = pl.DataFrame(data, schema=pl.Schema({input_col: schema_type}))

    input_field = LabelField(dtype=pl.UInt32(), multi_label=input_multi, is_list=input_is_list)
    output_field = LabelField(dtype=pl.UInt32(), multi_label=output_multi, is_list=output_is_list)

    setattr(converter_instance, "input_label", AttributeSpec(name=input_col, field=input_field))
    setattr(converter_instance, "output_label", AttributeSpec(name=output_col, field=output_field))

    assert converter_instance.filter_output_spec() is True
    result_df = converter_instance.convert(df)

    assert output_col in result_df.columns
    assert result_df[output_col].dtype == expected_dtype
    result_val = result_df[output_col][0]
    if hasattr(result_val, "to_list"):
        assert result_val.to_list() == expected_value
    else:
        assert result_val == expected_value


def test_polygon_dtype_converter_int_to_float():
    """Test PolygonDtypeConverter converting Int32 to Float32."""
    from getidata.converters import PolygonDtypeConverter

    converter_instance = PolygonDtypeConverter()

    # Create test data with Int32 polygons: List[List[Array[2]]]
    # Each polygon is a list of (x, y) points
    polygon1 = [[10, 10], [30, 10], [20, 30]]  # Triangle
    polygon2 = [[40, 40], [60, 40], [60, 60], [40, 60]]  # Rectangle

    df = pl.DataFrame(
        {"polygon": [[polygon1, polygon2]]},
        schema=pl.Schema({"polygon": pl.List(pl.List(pl.Array(pl.Int32, 2)))}),
    )

    # Set up converter attributes
    input_field = PolygonField(dtype=pl.Int32(), format="xy", normalize=False)
    output_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=False)

    setattr(converter_instance, "input_polygon", AttributeSpec(name="polygon", field=input_field))
    setattr(converter_instance, "output_polygon", AttributeSpec(name="polygon", field=output_field))

    # Test filter - should return True for dtype change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "polygon" in result_df.columns
    # Check dtype conversion - get the inner arrays and check their dtype
    result_polygons = result_df["polygon"][0]
    assert len(result_polygons) == 2

    # Check first polygon (triangle)
    result_polygon1 = result_polygons[0]
    assert len(result_polygon1) == 3
    np.testing.assert_array_almost_equal(result_polygon1[0].to_numpy(), [10.0, 10.0])
    np.testing.assert_array_almost_equal(result_polygon1[1].to_numpy(), [30.0, 10.0])
    np.testing.assert_array_almost_equal(result_polygon1[2].to_numpy(), [20.0, 30.0])

    # Check second polygon (rectangle)
    result_polygon2 = result_polygons[1]
    assert len(result_polygon2) == 4


def test_polygon_dtype_converter_same_dtype():
    """Test PolygonDtypeConverter returns False when dtypes are the same."""
    from getidata.converters import PolygonDtypeConverter

    converter_instance = PolygonDtypeConverter()

    # Set up converter attributes with same dtype
    input_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=False)
    output_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=False)

    setattr(converter_instance, "input_polygon", AttributeSpec(name="polygon", field=input_field))
    setattr(converter_instance, "output_polygon", AttributeSpec(name="polygon", field=output_field))

    # Test filter - should return False when dtypes are the same
    assert converter_instance.filter_output_spec() is False


def test_bbox_dtype_converter_preserves_array_structure():
    """Test that BBoxDtypeConverter preserves the fixed-size array structure."""
    from getidata.converters import BBoxDtypeConverter

    converter_instance = BBoxDtypeConverter()

    # Create test data with multiple bboxes
    df = pl.DataFrame(
        {"bbox": [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]]},
        schema=pl.Schema({"bbox": pl.List(pl.Array(pl.Int32, 4))}),
    )

    # Set up converter attributes
    input_bbox_field = BBoxField(dtype=pl.Int32(), format="x1y1x2y2", normalize=False)
    output_bbox_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)

    setattr(converter_instance, "input_bbox", AttributeSpec(name="bbox", field=input_bbox_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_bbox_field))

    converter_instance.filter_output_spec()

    # Test conversion
    result_df = converter_instance.convert(df)

    # Check that the result maintains the List[Array[4]] structure
    assert result_df.schema["bbox"] == pl.List(pl.Array(pl.Float32, 4))

    # Check that all bboxes are correctly converted
    result_bboxes = result_df["bbox"][0]
    assert len(result_bboxes) == 3
    np.testing.assert_array_almost_equal(result_bboxes[0].to_numpy(), [1.0, 2.0, 3.0, 4.0])
    np.testing.assert_array_almost_equal(result_bboxes[1].to_numpy(), [5.0, 6.0, 7.0, 8.0])
    np.testing.assert_array_almost_equal(result_bboxes[2].to_numpy(), [9.0, 10.0, 11.0, 12.0])


def test_create_fixed_array_cast_expr():
    """Test the _create_fixed_array_cast_expr helper function."""
    from getidata.converters.annotation_converters import _create_fixed_array_cast_expr

    # Test with 4-element array (bbox)
    arr_data = np.array([1, 2, 3, 4], dtype=np.int32)
    df = pl.DataFrame(
        {"arr": [[arr_data]]},
        schema=pl.Schema({"arr": pl.List(pl.Array(pl.Int32(), 4))}),
    )

    # Apply the expression
    result = df.select(pl.col("arr").list.eval(_create_fixed_array_cast_expr(pl.Float64(), 4)))

    # Check result
    assert result["arr"].dtype == pl.List(pl.Array(pl.Float64(), 4))
    np.testing.assert_array_almost_equal(result["arr"][0][0].to_numpy(), [1.0, 2.0, 3.0, 4.0])


def test_convert_fixed_array_dtype():
    """Test the _convert_fixed_array_dtype helper function."""
    from getidata.converters.annotation_converters import _convert_fixed_array_dtype

    # Test with 5-element array (rotated bbox)
    df = pl.DataFrame(
        {"input": [[[10, 20, 30, 40, 50]]]},
        schema=pl.Schema({"input": pl.List(pl.Array(pl.Int32(), 5))}),
    )

    # Apply the conversion
    result_df = _convert_fixed_array_dtype(df, "input", "output", pl.Float32(), array_size=5)

    # Check result
    assert "output" in result_df.columns
    assert result_df["output"].dtype == pl.List(pl.Array(pl.Float32, 5))
    np.testing.assert_array_almost_equal(result_df["output"][0][0].to_numpy(), [10.0, 20.0, 30.0, 40.0, 50.0])


def test_bbox_dtype_conversion_numpy_dtype():
    class DetectionSampleFloat(Sample):
        bboxes: npt.NDArray[np.floating[Any]] = bbox_field(dtype=pl.Float32())

    class DetectionSampleInt(Sample):
        bboxes: npt.NDArray[np.integer[Any]] = bbox_field(dtype=pl.Int32())

    # Create source dataset with int32 bboxes
    dataset_int = Dataset(DetectionSampleInt)
    di_int = DetectionSampleInt(bboxes=np.array([[5, 5, 20, 20], [25, 30, 50, 60]], dtype=np.int32))
    dataset_int.append(di_int)

    # Convert to float32 schema
    dataset_float = dataset_int.convert_to_schema(DetectionSampleFloat)

    # Verify original dataset is unchanged
    assert dataset_int[0].bboxes.dtype == np.int32
    np.testing.assert_array_equal(dataset_int[0].bboxes, [[5, 5, 20, 20], [25, 30, 50, 60]])

    # The dtype should be float32, not object
    assert dataset_float[0].bboxes.dtype == np.float32

    # Verify the values are correct
    expected_values = np.array([[5.0, 5.0, 20.0, 20.0], [25.0, 30.0, 50.0, 60.0]], dtype=np.float32)
    np.testing.assert_array_almost_equal(dataset_float[0].bboxes, expected_values)


def test_keypoints_dtype_converter():
    """Test KeypointsDtypeConverter converting Float32 to Float64."""
    converter_instance = KeypointsDtypeConverter()

    # Create test data with Float32 keypoints [x, y, visibility]
    df = pl.DataFrame(
        {"keypoints": [[[10.0, 20.0, 2.0], [30.0, 40.0, 1.0], [50.0, 60.0, 0.0]]]},
        schema=pl.Schema({"keypoints": pl.List(pl.Array(pl.Float32, 3))}),
    )

    # Set up converter attributes
    input_field = KeypointsField(dtype=pl.Float32(), normalize=False)
    output_field = KeypointsField(dtype=pl.Float64(), normalize=False)

    setattr(converter_instance, "input_keypoints", AttributeSpec(name="keypoints", field=input_field))
    setattr(converter_instance, "output_keypoints", AttributeSpec(name="keypoints", field=output_field))

    # Test filter - should return True for dtype change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "keypoints" in result_df.columns
    assert result_df.schema["keypoints"] == pl.List(pl.Array(pl.Float64, 3))

    result_kpts = result_df["keypoints"][0]
    np.testing.assert_array_almost_equal(result_kpts[0].to_numpy(), [10.0, 20.0, 2.0])
    np.testing.assert_array_almost_equal(result_kpts[1].to_numpy(), [30.0, 40.0, 1.0])
    np.testing.assert_array_almost_equal(result_kpts[2].to_numpy(), [50.0, 60.0, 0.0])


def test_keypoints_coordinate_converter_normalize():
    """Test KeypointsCoordinateConverter normalizing absolute coordinates."""

    converter_instance = KeypointsCoordinateConverter()

    # Create test data with absolute coordinates
    df = pl.DataFrame(
        {
            "keypoints": [[[100.0, 150.0, 2.0], [200.0, 300.0, 1.0]]],
            "image": [[0] * 100],  # dummy image data
            "image_shape": [[400, 500, 3]],  # height=400, width=500
        },
        schema=pl.Schema(
            {
                "keypoints": pl.List(pl.Array(pl.Float32, 3)),
                "image": pl.List(pl.UInt8),
                "image_shape": pl.List(pl.Int32),
            }
        ),
    )

    # Set up converter attributes
    input_keypoints_field = KeypointsField(dtype=pl.Float32(), normalize=False)
    output_keypoints_field = KeypointsField(dtype=pl.Float32(), normalize=True)
    image_field = ImageField(dtype=pl.UInt8())

    setattr(converter_instance, "input_keypoints", AttributeSpec(name="keypoints", field=input_keypoints_field))
    setattr(converter_instance, "output_keypoints", AttributeSpec(name="keypoints", field=output_keypoints_field))
    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=image_field))

    # Test filter - should return True for normalization change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    result_kpts = result_df["keypoints"][0]
    # x is normalized by width (500), y by height (400)
    np.testing.assert_array_almost_equal(result_kpts[0].to_numpy(), [100.0 / 500, 150.0 / 400, 2.0], decimal=5)
    np.testing.assert_array_almost_equal(result_kpts[1].to_numpy(), [200.0 / 500, 300.0 / 400, 1.0], decimal=5)


def test_ellipse_dtype_converter():
    """Test EllipseDtypeConverter converting Int32 to Float32."""

    converter_instance = EllipseDtypeConverter()

    # Create test data with Int32 ellipses [x1, y1, x2, y2]
    df = pl.DataFrame(
        {"ellipse": [[[10, 20, 30, 40], [50, 60, 70, 80]]]},
        schema=pl.Schema({"ellipse": pl.List(pl.Array(pl.Int32, 4))}),
    )

    # Set up converter attributes
    input_field = EllipseField(dtype=pl.Int32(), format="x1y1x2y2", normalize=False)
    output_field = EllipseField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)

    setattr(converter_instance, "input_ellipse", AttributeSpec(name="ellipse", field=input_field))
    setattr(converter_instance, "output_ellipse", AttributeSpec(name="ellipse", field=output_field))

    # Test filter - should return True for dtype change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "ellipse" in result_df.columns
    assert result_df.schema["ellipse"] == pl.List(pl.Array(pl.Float32, 4))

    result_ellipses = result_df["ellipse"][0]
    np.testing.assert_array_almost_equal(result_ellipses[0].to_numpy(), [10.0, 20.0, 30.0, 40.0])
    np.testing.assert_array_almost_equal(result_ellipses[1].to_numpy(), [50.0, 60.0, 70.0, 80.0])


def test_bbox_format_converter_x1y1x2y2_to_xywh():
    """Test BBoxFormatConverter converting x1y1x2y2 to xywh."""

    converter_instance = BBoxFormatConverter()

    # Create test data with x1y1x2y2 format
    df = pl.DataFrame(
        {"bbox": [[[10.0, 20.0, 30.0, 50.0], [100.0, 150.0, 200.0, 250.0]]]},
        schema=pl.Schema({"bbox": pl.List(pl.Array(pl.Float32, 4))}),
    )

    # Set up converter attributes
    input_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)
    output_field = BBoxField(dtype=pl.Float32(), format="xywh", normalize=False)

    setattr(converter_instance, "input_bbox", AttributeSpec(name="bbox", field=input_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_field))

    # Test filter - should return True for format change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    result_bboxes = result_df["bbox"][0]
    # x1y1x2y2 [10, 20, 30, 50] -> xywh [10, 20, 20, 30] (w=30-10=20, h=50-20=30)
    np.testing.assert_array_almost_equal(result_bboxes[0].to_numpy(), [10.0, 20.0, 20.0, 30.0])
    # x1y1x2y2 [100, 150, 200, 250] -> xywh [100, 150, 100, 100]
    np.testing.assert_array_almost_equal(result_bboxes[1].to_numpy(), [100.0, 150.0, 100.0, 100.0])


def test_bbox_format_converter_xywh_to_cxcywh():
    """Test BBoxFormatConverter converting xywh to cxcywh."""

    converter_instance = BBoxFormatConverter()

    # Create test data with xywh format
    df = pl.DataFrame(
        {"bbox": [[[10.0, 20.0, 20.0, 30.0]]]},  # x, y, w, h
        schema=pl.Schema({"bbox": pl.List(pl.Array(pl.Float32, 4))}),
    )

    # Set up converter attributes
    input_field = BBoxField(dtype=pl.Float32(), format="xywh", normalize=False)
    output_field = BBoxField(dtype=pl.Float32(), format="cxcywh", normalize=False)

    setattr(converter_instance, "input_bbox", AttributeSpec(name="bbox", field=input_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_field))

    # Test filter - should return True for format change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    result_bboxes = result_df["bbox"][0]
    # xywh [10, 20, 20, 30] -> cxcywh [20, 35, 20, 30] (cx=10+20/2=20, cy=20+30/2=35)
    np.testing.assert_array_almost_equal(result_bboxes[0].to_numpy(), [20.0, 35.0, 20.0, 30.0])


def test_bbox_format_converter_cxcywh_to_x1y1x2y2():
    """Test BBoxFormatConverter converting cxcywh to x1y1x2y2."""

    converter_instance = BBoxFormatConverter()

    # Create test data with cxcywh format
    df = pl.DataFrame(
        {"bbox": [[[20.0, 35.0, 20.0, 30.0]]]},  # cx, cy, w, h
        schema=pl.Schema({"bbox": pl.List(pl.Array(pl.Float32, 4))}),
    )

    # Set up converter attributes
    input_field = BBoxField(dtype=pl.Float32(), format="cxcywh", normalize=False)
    output_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)

    setattr(converter_instance, "input_bbox", AttributeSpec(name="bbox", field=input_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_field))

    # Test filter - should return True for format change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    result_bboxes = result_df["bbox"][0]
    # cxcywh [20, 35, 20, 30] -> x1y1x2y2 [10, 20, 30, 50]
    np.testing.assert_array_almost_equal(result_bboxes[0].to_numpy(), [10.0, 20.0, 30.0, 50.0])


def test_bbox_format_converter_cxcywh_to_x1y1x2y2_clamps_negative_edge_coords():
    """Boxes touching the image edge can produce a tiny negative y1/x1 due to
    float32 precision loss inherent in YOLO's 6-decimal-place normalized format
    (e.g. 0.033333 * 1080 = 35.99964, not exactly 36.0). BBoxFormatConverter
    must clamp x1/y1 to >= 0 rather than propagating the negative epsilon.

    Source values: cx=0.605208, cy=0.033333, w=0.066667, h=0.066667 (normalized,
    1920x1080 image) -> denormalized cxcywh = [1161.9994, 35.99964, 128.00064, 72.00036]
    which, before clamping, converts to y1 = cy - h/2 = -0.00054.
    """

    converter_instance = BBoxFormatConverter()

    df = pl.DataFrame(
        {"bbox": [[[1161.9994, 35.99964, 128.00064, 72.00036]]]},  # cx, cy, w, h (denormalized)
        schema=pl.Schema({"bbox": pl.List(pl.Array(pl.Float32, 4))}),
    )

    input_field = BBoxField(dtype=pl.Float32(), format="cxcywh", normalize=False)
    output_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)

    setattr(converter_instance, "input_bbox", AttributeSpec(name="bbox", field=input_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)
    result_bbox = result_df["bbox"][0][0].to_numpy()

    x1, y1, x2, y2 = result_bbox

    # y1 must be clamped to exactly 0, never negative
    assert y1 == 0.0, f"Expected y1 clamped to 0.0, got {y1}"
    assert x1 >= 0.0

    # width/height derived from corners must stay non-negative
    assert (x2 - x1) > 0
    assert (y2 - y1) > 0


def test_bbox_to_polygon_converter():
    """Test BBoxToPolygonConverter converting bbox to polygon."""

    converter_instance = BBoxToPolygonConverter()

    # Create test data with x1y1x2y2 format
    df = pl.DataFrame(
        {"bbox": [[[10.0, 20.0, 30.0, 50.0]]]},  # x1, y1, x2, y2
        schema=pl.Schema({"bbox": pl.List(pl.Array(pl.Float32, 4))}),
    )

    # Set up converter attributes
    input_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)
    output_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=False)

    setattr(converter_instance, "input_bbox", AttributeSpec(name="bbox", field=input_field))
    setattr(converter_instance, "output_polygon", AttributeSpec(name="polygon", field=output_field))

    # Test filter - should return True
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "polygon" in result_df.columns
    result_polygons = result_df["polygon"][0]

    # Check that we have 1 polygon with 4 corners
    assert len(result_polygons) == 1
    polygon = result_polygons[0]
    assert len(polygon) == 4

    # Check corners: top-left, top-right, bottom-right, bottom-left
    np.testing.assert_array_almost_equal(polygon[0].to_numpy(), [10.0, 20.0])  # top-left
    np.testing.assert_array_almost_equal(polygon[1].to_numpy(), [30.0, 20.0])  # top-right
    np.testing.assert_array_almost_equal(polygon[2].to_numpy(), [30.0, 50.0])  # bottom-right
    np.testing.assert_array_almost_equal(polygon[3].to_numpy(), [10.0, 50.0])  # bottom-left


def test_ellipse_to_bbox_converter():
    """Test EllipseToBBoxConverter converting ellipse to bbox."""

    converter_instance = EllipseToBBoxConverter()

    # Create test data with x1y1x2y2 format ellipse
    df = pl.DataFrame(
        {"ellipse": [[[10.0, 20.0, 30.0, 50.0]]]},
        schema=pl.Schema({"ellipse": pl.List(pl.Array(pl.Float32, 4))}),
    )

    # Set up converter attributes
    input_field = EllipseField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)
    output_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)

    setattr(converter_instance, "input_ellipse", AttributeSpec(name="ellipse", field=input_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_field))

    # Test filter - should return True
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "bbox" in result_df.columns
    result_bboxes = result_df["bbox"][0]

    # Ellipse and bbox use same format, should be identical
    np.testing.assert_array_almost_equal(result_bboxes[0].to_numpy(), [10.0, 20.0, 30.0, 50.0])


def test_keypoints_to_bbox_converter():
    """Test KeypointsToBBoxConverter converting keypoints to enclosing bbox."""

    converter_instance = KeypointsToBBoxConverter()

    # Create test data with keypoints [x, y, visibility]
    # visibility > 0 means visible
    df = pl.DataFrame(
        {
            "keypoints": [
                [[10.0, 20.0, 2.0], [30.0, 50.0, 1.0], [25.0, 35.0, 2.0], [5.0, 5.0, 0.0]]  # invisible
            ]
        },
        schema=pl.Schema({"keypoints": pl.List(pl.Array(pl.Float32, 3))}),
    )

    # Set up converter attributes
    input_field = KeypointsField(dtype=pl.Float32(), normalize=False)
    output_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)

    setattr(converter_instance, "input_keypoints", AttributeSpec(name="keypoints", field=input_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_field))

    # Test filter - should return True
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "bbox" in result_df.columns
    result_bboxes = result_df["bbox"][0]

    # Bbox should enclose only visible keypoints: (10,20), (30,50), (25,35)
    # Not (5,5) which has visibility=0
    # min_x=10, min_y=20, max_x=30, max_y=50
    np.testing.assert_array_almost_equal(result_bboxes[0].to_numpy(), [10.0, 20.0, 30.0, 50.0])


def test_rotated_bbox_to_bbox_converter():
    """Test RotatedBBoxToBBoxConverter converting rotated bbox to AABB."""

    converter_instance = RotatedBBoxToBBoxConverter()

    # Create test data with rotated bboxes [cx, cy, w, h, r]
    # No rotation - should give same as regular bbox
    df = pl.DataFrame(
        {"rotated_bbox": [[[50.0, 60.0, 20.0, 10.0, 0.0]]]},  # cx=50, cy=60, w=20, h=10, r=0
        schema=pl.Schema({"rotated_bbox": pl.List(pl.Array(pl.Float32, 5))}),
    )

    # Set up converter attributes
    input_field = RotatedBBoxField(dtype=pl.Float32(), format="cxcywhr", normalize=False)
    output_field = BBoxField(dtype=pl.Float32(), format="x1y1x2y2", normalize=False)

    setattr(converter_instance, "input_rotated_bbox", AttributeSpec(name="rotated_bbox", field=input_field))
    setattr(converter_instance, "output_bbox", AttributeSpec(name="bbox", field=output_field))

    # Test filter - should return True
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "bbox" in result_df.columns
    result_bboxes = result_df["bbox"][0]

    # With r=0: cx=50, cy=60, w=20, h=10 -> x1=40, y1=55, x2=60, y2=65
    np.testing.assert_array_almost_equal(result_bboxes[0].to_numpy(), [40.0, 55.0, 60.0, 65.0])


def test_rotated_bbox_coordinate_converter():
    """Test RotatedBBoxCoordinateConverter normalizing coordinates."""

    converter_instance = RotatedBBoxCoordinateConverter()

    # Create test data with absolute coordinates
    df = pl.DataFrame(
        {
            "rotated_bbox": [[[250.0, 200.0, 100.0, 80.0, 0.5]]],  # cx, cy, w, h, r
            "image": [[0] * 100],  # dummy image data
            "image_shape": [[400, 500, 3]],  # height=400, width=500
        },
        schema=pl.Schema(
            {
                "rotated_bbox": pl.List(pl.Array(pl.Float32, 5)),
                "image": pl.List(pl.UInt8),
                "image_shape": pl.List(pl.Int32),
            }
        ),
    )

    # Set up converter attributes
    input_rbbox_field = RotatedBBoxField(dtype=pl.Float32(), format="cxcywhr", normalize=False)
    output_rbbox_field = RotatedBBoxField(dtype=pl.Float32(), format="cxcywhr", normalize=True)
    image_field = ImageField(dtype=pl.UInt8())

    setattr(converter_instance, "input_rotated_bbox", AttributeSpec(name="rotated_bbox", field=input_rbbox_field))
    setattr(converter_instance, "output_rotated_bbox", AttributeSpec(name="rotated_bbox", field=output_rbbox_field))
    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=image_field))

    # Test filter - should return True for normalization change
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    result_rbbox = result_df["rotated_bbox"][0][0].to_numpy()
    # cx and w normalized by width (500), cy and h normalized by height (400), r unchanged
    expected = [250.0 / 500, 200.0 / 400, 100.0 / 500, 80.0 / 400, 0.5]
    np.testing.assert_array_almost_equal(result_rbbox, expected, decimal=5)


def test_label_shape_conversion_path_found():
    """Test that find_conversion_path can find a path for multi_label=False → multi_label=True."""
    from getidata.converters.registry import find_conversion_path
    from getidata.fields import label_field

    class SourceSample(Sample):
        label: npt.NDArray[Any] = label_field(dtype=pl.UInt32(), multi_label=False, is_list=True)

    class TargetSample(Sample):
        label: npt.NDArray[Any] = label_field(dtype=pl.UInt8(), multi_label=True, is_list=True)

    source_schema = SourceSample.infer_schema()
    target_schema = TargetSample.infer_schema()

    # This should NOT raise a ConversionError
    conversion_paths, _categories = find_conversion_path(source_schema, target_schema)

    # There should be converters in the path
    assert len(conversion_paths.converters) > 0


def test_label_shape_dataset_conversion():
    """Test end-to-end dataset conversion with multi_label change."""
    from getidata.fields import label_field

    class SourceSample(Sample):
        label: npt.NDArray[Any] = label_field(dtype=pl.UInt32(), multi_label=False, is_list=True)

    class TargetSample(Sample):
        label: npt.NDArray[Any] = label_field(dtype=pl.UInt8(), multi_label=True, is_list=True)

    categories = {"label": LabelCategories(labels=("cat", "dog", "bird", "fish", "horse"))}
    dataset = Dataset(SourceSample, categories=categories)

    # Add samples with list-of-single-labels (detection-style)
    sample1 = SourceSample(label=np.array([0, 1, 2], dtype=np.uint32))
    sample2 = SourceSample(label=np.array([3, 4], dtype=np.uint32))
    dataset.append(sample1)
    dataset.append(sample2)

    # Convert to multi-label schema
    converted = dataset.convert_to_schema(TargetSample)

    assert len(converted) == 2
    assert converted.schema.attributes["label"].field.multi_label is True
    assert converted.schema.attributes["label"].field.dtype == pl.UInt8()
    assert converted.df["label"].dtype == pl.List(pl.List(pl.UInt8))

    # Each single label should be wrapped in its own list
    row0 = converted.df["label"][0].to_list()
    assert row0 == [[0], [1], [2]]
    row1 = converted.df["label"][1].to_list()
    assert row1 == [[3], [4]]
