"""
Unit tests for converter registry and converter implementations.
"""

import numpy as np
import polars as pl
import pytest

from getidata.converters import (
    InstanceMaskCallableToInstanceMaskConverter,
    MaskCallableToMaskConverter,
    PolygonToInstanceMaskConverter,
    PolygonToMaskConverter,
)
from getidata.converters.mask_converters import polygons_to_instance_masks, polygons_to_mask
from getidata.fields import (
    ImageInfoField,
    InstanceMaskCallableField,
    InstanceMaskField,
    LabelField,
    MaskCallableField,
    MaskField,
    PolygonField,
)
from getidata.schema import AttributeSpec


def test_polygon_to_mask_converter():
    """Test conversion from polygon coordinates to mask format."""
    converter_instance = PolygonToMaskConverter()  # type: ignore[call-arg]

    # Create test data with polygon coordinates and labels
    # Triangle polygon: (10,10) -> (30,10) -> (20,30) -> (10,10)
    polygon_coords1 = [[10.0, 10.0], [30.0, 10.0], [20.0, 30.0]]

    # Rectangle polygon: (40,40) -> (60,40) -> (60,60) -> (40,60) -> (40,40)
    polygon_coords2 = [[40.0, 40.0], [60.0, 40.0], [60.0, 60.0], [40.0, 60.0], [40.0, 40.0]]

    # Pentagon polygon: (70,10) -> (85,5) -> (90,20) -> (80,35) -> (65,25)
    polygon_coords3 = [[70.0, 10.0], [85.0, 5.0], [90.0, 20.0], [80.0, 35.0], [65.0, 25.0]]

    polygon_series = pl.Series(
        [polygon_coords1, polygon_coords2, polygon_coords3], dtype=pl.List(pl.Array(pl.Float32, 2))
    )

    df = pl.DataFrame(
        {
            "polygons": [polygon_series],  # List of three polygons
            "labels": [[0, 1, 2]],  # Corresponding labels for each polygon
            "image_info": [{"width": 100, "height": 100}],  # Image dimensions
        }
    )

    # Set up converter attributes
    input_polygon_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=False)
    input_labels_field = LabelField(dtype=pl.UInt32(), multi_label=True)
    image_info_field = ImageInfoField()
    output_mask_field = MaskField(dtype=pl.UInt8())

    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=input_polygon_field),
    )
    setattr(
        converter_instance,
        "input_labels",
        AttributeSpec(name="labels", field=input_labels_field),
    )
    setattr(
        converter_instance,
        "input_image_info",
        AttributeSpec(name="image_info", field=image_info_field),
    )
    setattr(
        converter_instance,
        "output_mask",
        AttributeSpec(name="mask", field=output_mask_field),
    )

    # Test filter - should return True when we have valid input
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    # Check that mask column was created
    assert "mask" in result_df.columns
    assert "mask_shape" in result_df.columns

    # Get the mask data and reshape it
    mask_data = np.array(result_df["mask"][0])
    mask_shape = result_df["mask_shape"][0]
    mask = mask_data.reshape(mask_shape)

    # Check mask properties
    assert mask.shape == (100, 100)  # Should match image dimensions
    assert mask.dtype == np.uint8

    # Check that polygons were filled with correct labels
    # Triangle should have label 1, rectangle should have label 2, pentagon should have label 3
    # Background should be 0

    # Check that triangle area has label 0 (stored as mask value 1)
    assert mask[15, 20] == 1  # Point inside triangle

    # Check that rectangle area has label 1 (stored as mask value 2)
    assert mask[50, 50] == 2  # Point inside rectangle

    # Check that pentagon area has label 2 (stored as mask value 3)
    assert mask[20, 75] == 3  # Point inside pentagon

    # Check background area has label 0
    assert mask[5, 5] == 0  # Point outside all polygons
    assert mask[95, 95] == 0  # Another background point

    # Check that mask contains the expected label values
    unique_labels = np.unique(mask)
    assert 0 in unique_labels  # Background
    assert 1 in unique_labels  # First polygon label (triangle)
    assert 2 in unique_labels  # Second polygon label (rectangle)
    assert 3 in unique_labels  # Third polygon label (pentagon)


def test_polygon_to_mask_converter_normalized():
    """Test conversion with normalized polygon coordinates."""
    converter_instance = PolygonToMaskConverter()  # type: ignore[call-arg]

    # Create test data with normalized coordinates (0.0 to 1.0 range)
    # Small triangle in normalized coordinates
    polygon_coords = [[0.1, 0.1], [0.3, 0.1], [0.2, 0.3]]  # Normalized coordinates
    polygon_series = pl.Series([polygon_coords], dtype=pl.List(pl.Array(pl.Float32, 2)))

    df = pl.DataFrame(
        {
            "polygons": [polygon_series],
            "labels": [[5]],  # Label 5 for this polygon
            "image_info": [{"width": 100, "height": 100}],
        }
    )

    # Set up converter attributes with normalization enabled
    input_polygon_field = PolygonField(
        dtype=pl.Float32(),
        format="xy",
        normalize=True,  # Enable normalization
    )
    input_labels_field = LabelField(dtype=pl.UInt32(), multi_label=True)
    image_info_field = ImageInfoField()
    output_mask_field = MaskField(dtype=pl.UInt8())

    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=input_polygon_field),
    )
    setattr(converter_instance, "input_labels", AttributeSpec(name="labels", field=input_labels_field))
    setattr(
        converter_instance,
        "input_image_info",
        AttributeSpec(name="image_info", field=image_info_field),
    )
    setattr(converter_instance, "output_mask", AttributeSpec(name="mask", field=output_mask_field))

    # Test conversion
    result_df = converter_instance.convert(df)

    # Get the mask and check it
    mask_data = np.array(result_df["mask"][0])
    mask_shape = result_df["mask_shape"][0]
    mask = mask_data.reshape(mask_shape)

    # Check that polygon was filled with label 5 (stored as mask value 6)
    # Normalized coordinates should be scaled: 0.2 * 100 = 20, 0.1 * 100 = 10, etc.
    assert mask[15, 20] == 6  # Point inside the scaled triangle (5+1=6)
    assert mask[5, 5] == 0  # Background point


def test_polygon_to_mask_converter_honors_configured_dtype():
    """Test conversion preserves the configured mask dtype."""
    converter_instance = PolygonToMaskConverter()  # type: ignore[call-arg]

    polygon_coords = [[10.0, 10.0], [30.0, 10.0], [20.0, 30.0]]
    polygon_series = pl.Series([polygon_coords], dtype=pl.List(pl.Array(pl.Float32, 2)))

    df = pl.DataFrame(
        {
            "polygons": [polygon_series],
            "labels": [[0]],
            "image_info": [{"width": 100, "height": 100}],
        }
    )

    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=PolygonField(dtype=pl.Float32(), format="xy", normalize=False)),
    )
    setattr(
        converter_instance,
        "input_labels",
        AttributeSpec(name="labels", field=LabelField(dtype=pl.UInt32(), multi_label=True)),
    )
    setattr(
        converter_instance,
        "input_image_info",
        AttributeSpec(name="image_info", field=ImageInfoField()),
    )
    setattr(
        converter_instance,
        "output_mask",
        AttributeSpec(name="mask", field=MaskField(dtype=pl.UInt16())),
    )

    result_df = converter_instance.convert(df)

    mask_data = np.array(result_df["mask"][0])
    mask_shape = result_df["mask_shape"][0]
    mask = mask_data.reshape(mask_shape)

    assert result_df.schema["mask"] == pl.List(pl.UInt16())
    assert mask.dtype == np.uint16
    assert mask[15, 20] == 1
    assert mask[5, 5] == 0


def test_polygon_to_instance_mask_converter():
    """Test conversion from polygon coordinates to instance mask format."""
    # Create test data with triangle, rectangle, and pentagon polygons
    polygon_coords1 = [[10.0, 10.0], [20.0, 10.0], [15.0, 20.0]]
    polygon_coords2 = [[30.0, 30.0], [40.0, 30.0], [40.0, 40.0], [30.0, 40.0]]
    polygon_coords3 = [[50.0, 50.0], [60.0, 50.0], [65.0, 60.0], [55.0, 70.0], [45.0, 60.0]]

    polygon_series = pl.Series(
        [polygon_coords1, polygon_coords2, polygon_coords3], dtype=pl.List(pl.Array(pl.Float32, 2))
    )

    df = pl.DataFrame(
        {
            "polygons": [polygon_series],
            "image_info": [{"width": 100, "height": 100}],
        }
    )

    # Create converter instance
    converter_instance = PolygonToInstanceMaskConverter()

    # Set up field specs
    input_polygon_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=False)
    image_info_field = ImageInfoField()
    output_instance_mask_field = InstanceMaskField(dtype=pl.Boolean())

    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=input_polygon_field),
    )
    setattr(
        converter_instance,
        "input_image_info",
        AttributeSpec(name="image_info", field=image_info_field),
    )
    setattr(
        converter_instance,
        "output_instance_mask",
        AttributeSpec(name="instance_mask", field=output_instance_mask_field),
    )

    # Test filter - should return True when we have valid input
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    # Check that instance mask column was created
    assert "instance_mask" in result_df.columns
    assert "instance_mask_shape" in result_df.columns

    # Get the mask data and reshape it
    mask_data = np.array(result_df["instance_mask"][0])
    mask_shape = result_df["instance_mask_shape"][0]
    masks = mask_data.reshape(mask_shape)

    # Check mask properties
    assert masks.shape == (3, 100, 100)  # 3 instances, 100x100 image
    assert masks.dtype == bool

    # Check that each instance is properly filled
    # Triangle should be in first mask
    assert masks[0, 15, 15]  # Point inside triangle
    assert not masks[0, 5, 5]  # Point outside triangle

    # Rectangle should be in second mask
    assert masks[1, 35, 35]  # Point inside rectangle
    assert not masks[1, 5, 5]  # Point outside rectangle

    # Pentagon should be in third mask
    assert masks[2, 55, 55]  # Point inside pentagon
    assert not masks[2, 5, 5]  # Point outside pentagon

    # No overlap between instances
    assert not np.any(masks[0] & masks[1])  # Triangle and rectangle don't overlap
    assert not np.any(masks[0] & masks[2])  # Triangle and pentagon don't overlap
    assert not np.any(masks[1] & masks[2])  # Rectangle and pentagon don't overlap


def test_polygon_to_instance_mask_converter_normalized():
    """Test conversion with normalized polygon coordinates."""
    # Create test data with normalized coordinates (0-1 range)
    polygon_coords1 = [[0.1, 0.1], [0.2, 0.1], [0.15, 0.2]]
    polygon_coords2 = [[0.3, 0.3], [0.4, 0.3], [0.4, 0.4], [0.3, 0.4]]

    polygon_series = pl.Series([polygon_coords1, polygon_coords2], dtype=pl.List(pl.Array(pl.Float32, 2)))

    df = pl.DataFrame(
        {
            "polygons": [polygon_series],
            "image_info": [{"width": 100, "height": 100}],
        }
    )

    # Create converter instance with normalized coordinates
    converter_instance = PolygonToInstanceMaskConverter()

    # Set up field specs
    input_polygon_field = PolygonField(dtype=pl.Float32(), format="xy", normalize=True)
    image_info_field = ImageInfoField()
    output_instance_mask_field = InstanceMaskField(dtype=pl.Boolean())

    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=input_polygon_field),
    )
    setattr(
        converter_instance,
        "input_image_info",
        AttributeSpec(name="image_info", field=image_info_field),
    )
    setattr(
        converter_instance,
        "output_instance_mask",
        AttributeSpec(name="instance_mask", field=output_instance_mask_field),
    )

    # Test conversion
    result_df = converter_instance.convert(df)

    # Get the mask and check it
    mask_data = np.array(result_df["instance_mask"][0])
    mask_shape = result_df["instance_mask_shape"][0]
    masks = mask_data.reshape(mask_shape)

    # Check mask properties
    assert masks.shape == (2, 100, 100)

    # Check that polygons were filled correctly after denormalization
    # Triangle: 0.1 * 100 = 10, 0.2 * 100 = 20, etc.
    assert masks[0, 15, 15]  # Point inside the scaled triangle
    assert not masks[0, 5, 5]  # Background point

    # Rectangle: 0.3 * 100 = 30, 0.4 * 100 = 40, etc.
    assert masks[1, 35, 35]  # Point inside the scaled rectangle
    assert not masks[1, 5, 5]  # Background point


def test_instance_mask_callable_to_instance_mask_converter():
    """Test InstanceMaskCallableToInstanceMaskConverter conversion."""
    converter_instance = InstanceMaskCallableToInstanceMaskConverter()  # type: ignore[call-arg]

    # Create a test callable that returns instance masks
    def get_instance_masks():
        return np.array([[[True, False], [False, True]], [[False, True], [True, False]]], dtype=bool)  # (2,2,2)

    df = pl.DataFrame(
        {
            "instance_mask_callable": [get_instance_masks],
        },
        schema=pl.Schema({"instance_mask_callable": pl.Object}),
    )

    # Set up converter attributes
    input_field = InstanceMaskCallableField(dtype=pl.Boolean())
    output_field = InstanceMaskField(dtype=pl.Boolean())

    setattr(
        converter_instance,
        "input_callable",
        AttributeSpec(
            name="instance_mask_callable",
            field=input_field,
        ),
    )
    setattr(
        converter_instance,
        "output_mask",
        AttributeSpec(
            name="instance_mask",
            field=output_field,
        ),
    )

    # Convert
    result_df = converter_instance.convert(df)

    # Check result
    assert "instance_mask" in result_df.columns
    assert "instance_mask_shape" in result_df.columns

    # Verify shape
    expected_shape = [2, 2, 2]  # N, H, W
    assert result_df["instance_mask_shape"][0].to_list() == expected_shape

    # Check instance masks
    expected_masks = get_instance_masks()
    result_masks = np.array(result_df["instance_mask"][0]).reshape(expected_shape)
    assert np.array_equal(result_masks, expected_masks)


def test_instance_mask_callable_to_instance_mask_converter_validation():
    """Test validation in InstanceMaskCallableToInstanceMaskConverter."""
    converter_instance = InstanceMaskCallableToInstanceMaskConverter()  # type: ignore[call-arg]

    # Create an invalid test callable that returns wrong shape
    def get_invalid_masks():
        return np.array([[True, False], [False, True]], dtype=bool)  # 2D instead of 3D

    df = pl.DataFrame(
        {
            "instance_mask_callable": [get_invalid_masks],
        },
        schema=pl.Schema({"instance_mask_callable": pl.Object}),
    )

    # Set up converter attributes
    input_field = InstanceMaskCallableField(dtype=pl.Boolean())
    output_field = InstanceMaskField(dtype=pl.Boolean())

    setattr(
        converter_instance,
        "input_callable",
        AttributeSpec(
            name="instance_mask_callable",
            field=input_field,
        ),
    )
    setattr(
        converter_instance,
        "output_mask",
        AttributeSpec(
            name="instance_mask",
            field=output_field,
        ),
    )

    # Conversion should raise error due to wrong shape
    with pytest.raises(ValueError):
        converter_instance.convert(df)


def test_mask_callable_to_mask_converter():
    """Test MaskCallableToMaskConverter conversion."""
    converter_instance = MaskCallableToMaskConverter()  # type: ignore[call-arg]

    # Create a test callable that returns a mask with category IDs
    def get_mask():
        return np.array([[1, 2], [2, 1]], dtype=np.uint8)  # (2,2)

    df = pl.DataFrame(
        {
            "mask_callable": [get_mask],
        },
        schema=pl.Schema({"mask_callable": pl.Object}),
    )

    # Set up converter attributes
    input_field = MaskCallableField(dtype=pl.UInt8())
    output_field = MaskField(dtype=pl.UInt8())

    setattr(
        converter_instance,
        "input_callable",
        AttributeSpec(
            name="mask_callable",
            field=input_field,
        ),
    )
    setattr(
        converter_instance,
        "output_mask",
        AttributeSpec(
            name="mask",
            field=output_field,
        ),
    )

    # Convert
    result_df = converter_instance.convert(df)

    # Check result
    assert "mask" in result_df.columns
    assert "mask_shape" in result_df.columns

    # Verify shape
    expected_shape = [2, 2]  # H, W
    assert result_df["mask_shape"][0].to_list() == expected_shape

    # Check mask
    expected_mask = get_mask()
    result_mask = np.array(result_df["mask"][0]).reshape(expected_shape)
    assert np.array_equal(result_mask, expected_mask)


def test_mask_callable_to_mask_converter_validation():
    """Test validation in MaskCallableToMaskConverter."""
    converter_instance = MaskCallableToMaskConverter()  # type: ignore[call-arg]

    # Create an invalid test callable that returns wrong shape
    def get_invalid_mask():
        return np.array([[[True, False], [False, True]]], dtype=np.uint8)

    df = pl.DataFrame(
        {
            "mask_callable": [get_invalid_mask],
        },
        schema=pl.Schema({"mask_callable": pl.Object}),
    )

    # Set up converter attributes
    input_field = MaskCallableField(dtype=pl.Boolean())
    output_field = InstanceMaskField(dtype=pl.Boolean())

    setattr(
        converter_instance,
        "input_callable",
        AttributeSpec(
            name="mask_callable",
            field=input_field,
        ),
    )
    setattr(
        converter_instance,
        "output_mask",
        AttributeSpec(
            name="mask",
            field=output_field,
        ),
    )

    # Check that it raises error for invalid shape
    with pytest.raises(ValueError, match="Mask array must be 2D \(H,W\), got shape \(1, 2, 2\)"):
        converter_instance.convert(df)


def test_polygon_to_instance_mask_converter_uint8_dtype():
    """Test instance mask converter with UInt8 output dtype (no boolean cast path)."""
    polygon_coords1 = [[10.0, 10.0], [20.0, 10.0], [15.0, 20.0]]
    polygon_coords2 = [[30.0, 30.0], [40.0, 30.0], [40.0, 40.0], [30.0, 40.0]]

    polygon_series = pl.Series([polygon_coords1, polygon_coords2], dtype=pl.List(pl.Array(pl.Float32, 2)))

    df = pl.DataFrame(
        {
            "polygons": [polygon_series],
            "image_info": [{"width": 80, "height": 80}],
        }
    )

    converter_instance = PolygonToInstanceMaskConverter()
    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=PolygonField(dtype=pl.Float32(), format="xy", normalize=False)),
    )
    setattr(converter_instance, "input_image_info", AttributeSpec(name="image_info", field=ImageInfoField()))
    setattr(
        converter_instance,
        "output_instance_mask",
        AttributeSpec(name="instance_mask", field=InstanceMaskField(dtype=pl.UInt8())),
    )
    converter_instance.filter_output_spec()

    result_df = converter_instance.convert(df)

    mask_data = np.array(result_df["instance_mask"][0])
    mask_shape = result_df["instance_mask_shape"][0]
    masks = mask_data.reshape(mask_shape)

    assert masks.shape == (2, 80, 80)
    assert masks.dtype == np.uint8
    assert masks[0, 15, 15] == 1  # Inside triangle
    assert masks[0, 5, 5] == 0  # Outside triangle
    assert masks[1, 35, 35] == 1  # Inside rectangle
    assert not np.any(masks[0] & masks[1])


def test_polygon_to_instance_mask_converter_uint16_dtype():
    """Test instance mask converter with UInt16 output dtype to verify proper casting."""
    polygon_coords1 = [[10.0, 10.0], [20.0, 10.0], [15.0, 20.0]]

    polygon_series = pl.Series([polygon_coords1], dtype=pl.List(pl.Array(pl.Float32, 2)))

    df = pl.DataFrame(
        {
            "polygons": [polygon_series],
            "image_info": [{"width": 50, "height": 50}],
        }
    )

    converter_instance = PolygonToInstanceMaskConverter()
    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=PolygonField(dtype=pl.Float32(), format="xy", normalize=False)),
    )
    setattr(converter_instance, "input_image_info", AttributeSpec(name="image_info", field=ImageInfoField()))
    setattr(
        converter_instance,
        "output_instance_mask",
        AttributeSpec(name="instance_mask", field=InstanceMaskField(dtype=pl.UInt16())),
    )
    converter_instance.filter_output_spec()

    result_df = converter_instance.convert(df)

    mask_data = np.array(result_df["instance_mask"][0])
    mask_shape = result_df["instance_mask_shape"][0]
    masks = mask_data.reshape(mask_shape)

    assert masks.shape == (1, 50, 50)
    assert masks.dtype == np.uint16
    assert masks[0, 15, 15] == 1  # Inside triangle
    assert masks[0, 5, 5] == 0  # Outside


def test_polygon_to_instance_mask_converter_multi_sample_batch():
    """Test instance mask converter with multiple samples in a single DataFrame."""
    poly1 = pl.Series(
        [[[10.0, 10.0], [20.0, 10.0], [15.0, 20.0]]],
        dtype=pl.List(pl.Array(pl.Float32, 2)),
    )
    poly2 = pl.Series(
        [[[30.0, 30.0], [50.0, 30.0], [50.0, 50.0], [30.0, 50.0]]],
        dtype=pl.List(pl.Array(pl.Float32, 2)),
    )

    df = pl.DataFrame(
        {
            "polygons": [poly1, poly2],
            "image_info": [{"width": 60, "height": 60}, {"width": 60, "height": 60}],
        }
    )

    converter_instance = PolygonToInstanceMaskConverter()
    setattr(
        converter_instance,
        "input_polygon",
        AttributeSpec(name="polygons", field=PolygonField(dtype=pl.Float32(), format="xy", normalize=False)),
    )
    setattr(converter_instance, "input_image_info", AttributeSpec(name="image_info", field=ImageInfoField()))
    setattr(
        converter_instance,
        "output_instance_mask",
        AttributeSpec(name="instance_mask", field=InstanceMaskField(dtype=pl.Boolean())),
    )
    converter_instance.filter_output_spec()

    result_df = converter_instance.convert(df)

    # Check first sample (triangle)
    mask1 = np.array(result_df["instance_mask"][0]).reshape(result_df["instance_mask_shape"][0])
    assert mask1.shape == (1, 60, 60)
    assert mask1[0, 15, 15]  # Inside triangle

    # Check second sample (rectangle)
    mask2 = np.array(result_df["instance_mask"][1]).reshape(result_df["instance_mask_shape"][1])
    assert mask2.shape == (1, 60, 60)
    assert mask2[0, 40, 40]  # Inside rectangle
    assert not mask2[0, 5, 5]  # Outside rectangle


# ---------------------------------------------------------------------------
# Tests for generating masks at a different size than the image
# ---------------------------------------------------------------------------


def test_polygons_to_mask_default_size_matches_image():
    """Without mask_size the mask matches the image dimensions."""
    # Square polygon covering the left/top quadrant of a 20x20 image.
    polygons = [np.array([[0, 0], [10, 0], [10, 10], [0, 10]])]

    mask_data, shape = polygons_to_mask(polygons, [0], (20, 20))
    mask = mask_data.reshape(shape)

    assert shape == [20, 20]
    assert mask[5, 5] == 1  # Inside the square (label 0 -> stored as 1)
    assert mask[15, 15] == 0  # Background


def test_polygons_to_mask_smaller_than_image():
    """A smaller mask scales the polygon coordinates down accordingly."""
    polygons = [np.array([[0, 0], [10, 0], [10, 10], [0, 10]])]

    mask_data, shape = polygons_to_mask(polygons, [0], (20, 20), mask_size=(10, 10))
    mask = mask_data.reshape(shape)

    assert shape == [10, 10]
    # The 10x10 square in a 20x20 image scales to a 5x5 square in a 10x10 mask.
    assert mask[2, 2] == 1  # Inside the scaled square
    assert mask[8, 8] == 0  # Background (outside scaled square)


def test_polygons_to_mask_larger_than_image():
    """A larger mask scales the polygon coordinates up accordingly."""
    polygons = [np.array([[0, 0], [10, 0], [10, 10], [0, 10]])]

    mask_data, shape = polygons_to_mask(polygons, [0], (20, 20), mask_size=(40, 40))
    mask = mask_data.reshape(shape)

    assert shape == [40, 40]
    # The 10x10 square scales to a 20x20 square in a 40x40 mask.
    assert mask[10, 10] == 1  # Inside the scaled-up square
    assert mask[30, 30] == 0  # Background


def test_polygons_to_mask_non_uniform_size():
    """Width and height can be scaled independently."""
    polygons = [np.array([[0, 0], [10, 0], [10, 10], [0, 10]])]

    mask_data, shape = polygons_to_mask(polygons, [0], (20, 20), mask_size=(40, 10))
    mask = mask_data.reshape(shape)

    assert shape == [10, 40]  # [height, width]
    # x scales by 2 (20->40), y scales by 0.5 (20->10): square becomes 20 wide, 5 tall.
    assert mask[2, 10] == 1  # Inside the stretched square
    assert mask[8, 30] == 0  # Background


def test_polygons_to_instance_masks_custom_size():
    """Instance masks can also be rasterized at a different size than the image."""
    polygons = [np.array([[0, 0], [10, 0], [10, 10], [0, 10]])]

    mask_data, shape = polygons_to_instance_masks(polygons, (20, 20), mask_size=(40, 40))
    masks = mask_data.reshape(shape)

    assert shape == [1, 40, 40]
    assert masks[0, 10, 10] == 1  # Inside the scaled-up instance
    assert masks[0, 35, 35] == 0  # Background


def test_polygons_to_instance_masks_empty_custom_size():
    """An empty polygon list still respects the requested mask size."""
    mask_data, shape = polygons_to_instance_masks([], (20, 20), mask_size=(30, 15))

    assert shape == [0, 15, 30]
    assert mask_data.size == 0
