"""
Unit tests for converter registry and converter implementations.
"""

import os
import tempfile

import numpy as np
import polars as pl
import pytest

from getidata.converters import (
    ChannelsFirstConverter,
    ImageBytesToImageConverter,
    ImageCallableToImageConverter,
    ImageDtypeConverter,
    ImagePathToImageConverter,
    RedBlueColorConverter,
    find_conversion_path,
)
from getidata.converters.image_converters import ImagePathToImageInfoConverter
from getidata.fields import ImageBytesField, ImageCallableField, ImageField, ImageInfoField, ImagePathField
from getidata.schema import AttributeInfo, AttributeSpec, Schema


def test_rgb_to_bgr_converter():
    """Test RGB to BGR format conversion."""
    converter_instance = RedBlueColorConverter()  # type: ignore[call-arg]

    # Create test data
    rgb_data = np.array([255, 0, 0, 0, 255, 0, 0, 0, 255, 128, 128, 128])
    df = pl.DataFrame(
        {"image": [rgb_data], "image_shape": [[2, 2, 3]]},
        schema=pl.Schema({"image": pl.List(pl.UInt8()), "image_shape": pl.List(pl.Int64)}),
    )

    # Set up converter attributes
    input_field = ImageField(dtype=pl.UInt8(), format="RGB")
    output_field = ImageField(dtype=pl.UInt8(), format="BGR")

    setattr(
        converter_instance,
        "input_image",
        AttributeSpec(name="image", field=input_field),
    )
    setattr(
        converter_instance,
        "output_image",
        AttributeSpec(name="image", field=output_field),
    )

    # Test filter - should return True for RGB->BGR conversion
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "image" in result_df.columns
    # Result should have BGR format (channels swapped)
    result_data = result_df["image"][0]
    # First pixel: RGB [255, 0, 0] -> BGR [0, 0, 255]
    assert (result_data.reshape((2, 2, 3))[0][0] == [0, 0, 255]).all()


def test_uint8_to_float32_converter():
    """Test UInt8 to Float32 data type conversion."""
    converter_instance = ImageDtypeConverter()  # type: ignore[call-arg]

    # Create test data with UInt8 values
    uint8_data = [255, 128, 0, 64, 192, 32]
    df = pl.DataFrame(
        {"image": [uint8_data], "image_shape": [[2, 3]]},
        schema=pl.Schema({"image": pl.List(pl.UInt8()), "image_shape": pl.List(pl.Int64)}),
    )

    # Set up converter attributes
    input_field = ImageField(dtype=pl.UInt8(), format="RGB")
    output_field = ImageField(dtype=pl.Float32(), format="RGB")

    setattr(
        converter_instance,
        "input_image",
        AttributeSpec(name="image", field=input_field),
    )
    setattr(
        converter_instance,
        "output_image",
        AttributeSpec(name="image", field=output_field),
    )

    # Test filter - should return True for UInt8->Float32 conversion
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "image" in result_df.columns
    result_data = result_df["image"][0]

    # Check that values are normalized to [0, 1] range
    assert (result_data >= 0).all()
    assert (result_data <= 1).all()


def test_image_path_to_image_converter():
    """Test lazy loading of images from file paths."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test image file
        import numpy as np
        from PIL import Image as PILImage

        test_image_path = os.path.join(temp_dir, "test.png")
        img_array = np.random.randint(0, 255, (50, 75, 3), dtype=np.uint8)
        test_img = PILImage.fromarray(img_array)
        test_img.save(test_image_path)

        converter_instance = ImagePathToImageConverter()  # type: ignore[call-arg]

        # Create test data
        df = pl.DataFrame({"image_path": [test_image_path]})

        # Set up converter attributes
        input_field = ImagePathField()
        output_field = ImageField(dtype=pl.UInt8(), format="RGB")
        output_info_field = ImageInfoField()

        setattr(
            converter_instance,
            "input_path",
            AttributeSpec(name="image_path", field=input_field),
        )
        setattr(
            converter_instance,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )
        setattr(
            converter_instance,
            "output_info",
            AttributeSpec(name="image_info", field=output_info_field),
        )

        # Test filter - should return True for path->image conversion
        assert converter_instance.filter_output_spec() is True

        # Test conversion
        result_df = converter_instance.convert(df)

        assert "image" in result_df.columns
        assert "image_shape" in result_df.columns

        # Check that image was loaded correctly
        result_shape = list(result_df["image_shape"][0])
        assert result_shape == [50, 75, 3]  # height, width, channels


def test_image_bytes_to_image_converter():
    """Test ImageBytesToImageConverter functionality."""
    import cv2
    import numpy as np

    converter_instance = ImageBytesToImageConverter()  # type: ignore[call-arg]

    # Create test image data
    test_image = np.random.randint(0, 256, (32, 48, 3), dtype=np.uint8)
    image_bytes = cv2.imencode(".png", test_image)[1].tobytes()

    # Create test data
    df = pl.DataFrame({"image_bytes": [image_bytes]})

    # Set up converter attributes

    input_field = ImageBytesField()
    output_field = ImageField(dtype=pl.UInt8(), format="RGB")
    output_info_field = ImageInfoField()

    setattr(
        converter_instance,
        "input_bytes",
        AttributeSpec(name="image_bytes", field=input_field),
    )
    setattr(
        converter_instance,
        "output_image",
        AttributeSpec(name="image", field=output_field),
    )
    setattr(
        converter_instance,
        "output_info",
        AttributeSpec(name="image_info", field=output_info_field),
    )

    # Test filter - should return True for bytes->image conversion
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    assert "image" in result_df.columns
    assert "image_shape" in result_df.columns

    # Check that image was loaded correctly
    result_shape = tuple(result_df["image_shape"][0])
    assert result_shape == (32, 48, 3)  # height, width, channels

    # Check that the actual image data is correct (approximately, since PNG compression may cause slight differences)
    result_image = result_df["image"][0].to_numpy().reshape(result_shape)
    assert result_image.shape == test_image.shape
    assert result_image.dtype == np.uint8


def test_image_callable_to_image_converter():
    """Test ImageCallableToImageConverter functionality."""
    import numpy as np

    # Create a callable that returns a test image
    def create_test_image():
        return np.array(
            [
                [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
                [[255, 255, 0], [255, 0, 255], [0, 255, 255]],
                [[128, 128, 128], [64, 64, 64], [192, 192, 192]],
            ],
            dtype=np.uint8,
        )

    # Create input DataFrame with callable
    df = pl.DataFrame({"my_callable": [create_test_image]}, schema={"my_callable": pl.Object})

    # Create converter instance
    converter_instance = ImageCallableToImageConverter()  # type: ignore[call-arg]

    # Set up converter attributes
    input_field = ImageCallableField(format="RGB")
    output_field = ImageField(dtype=pl.UInt8(), format="RGB")
    output_info_field = ImageInfoField()

    setattr(
        converter_instance,
        "input_callable",
        AttributeSpec(name="my_callable", field=input_field),
    )
    setattr(
        converter_instance,
        "output_image",
        AttributeSpec(name="output_image", field=output_field),
    )
    setattr(
        converter_instance,
        "output_info",
        AttributeSpec(name="output_info", field=output_info_field),
    )

    # Test filter - should return True
    assert converter_instance.filter_output_spec() is True

    # Test conversion
    result_df = converter_instance.convert(df)

    # Check expected columns exist
    assert "output_image" in result_df.columns
    assert "output_image_shape" in result_df.columns

    # Check image shape
    image_shape = result_df["output_image_shape"][0]
    assert list(image_shape) == [3, 3, 3]  # height, width, channels

    # Check image data can be reconstructed
    image_data = result_df["output_image"][0]
    reconstructed = np.array(image_data, dtype=np.uint8).reshape(list(image_shape))
    assert reconstructed.shape == (3, 3, 3)
    assert reconstructed.dtype == np.uint8


def test_image_callable_converter_error_handling():
    """Test error handling in ImageCallableToImageConverter."""
    import numpy as np

    # Test with callable that returns non-numpy array
    def bad_callable_1():
        return "not an array"

    # Test with callable that returns wrong shape
    def bad_callable_2():
        return np.array([1, 2, 3, 4])  # 1D array

    # Test with callable that raises exception
    def bad_callable_3():
        raise ValueError("Something went wrong")

    # Create converter instance
    converter_instance = ImageCallableToImageConverter()  # type: ignore[call-arg]

    # Set up converter attributes
    input_field = ImageCallableField(format="RGB")
    output_field = ImageField(dtype=pl.UInt8(), format="RGB")
    output_info_field = ImageInfoField()

    setattr(
        converter_instance,
        "input_callable",
        AttributeSpec(name="my_callable", field=input_field),
    )
    setattr(
        converter_instance,
        "output_image",
        AttributeSpec(name="output_image", field=output_field),
    )
    setattr(
        converter_instance,
        "output_info",
        AttributeSpec(name="output_info", field=output_info_field),
    )

    # Test TypeError for non-numpy return
    df1 = pl.DataFrame({"my_callable": [bad_callable_1]}, schema={"my_callable": pl.Object})
    with pytest.raises(RuntimeError, match="must return numpy\.ndarray"):
        converter_instance.convert(df1)

    # Test ValueError for wrong shape
    df2 = pl.DataFrame({"my_callable": [bad_callable_2]}, schema={"my_callable": pl.Object})
    with pytest.raises(RuntimeError, match="must be 3D"):
        converter_instance.convert(df2)

    # Test exception propagation
    df3 = pl.DataFrame({"my_callable": [bad_callable_3]}, schema={"my_callable": pl.Object})
    with pytest.raises(RuntimeError, match="Error executing callable"):
        converter_instance.convert(df3)


def test_image_callable_converter_dtype_handling():
    """Test dtype handling in ImageCallableToImageConverter."""
    import numpy as np

    # Test with uint8 image (should work)
    def uint8_callable():
        return np.array([[[255, 0, 128]]], dtype=np.uint8)

    # Test with float32 image
    def float32_callable():
        return np.array([[[1.0, 0.5, 0.25]]], dtype=np.float32)

    # Create converter instance
    converter_instance = ImageCallableToImageConverter()  # type: ignore[call-arg]

    # Set up converter attributes for uint8
    input_field = ImageCallableField(format="RGB")
    output_field = ImageField(dtype=pl.UInt8(), format="RGB")
    output_info_field = ImageInfoField()

    setattr(converter_instance, "input_callable", AttributeSpec(name="my_callable", field=input_field))
    setattr(converter_instance, "output_image", AttributeSpec(name="output_image", field=output_field))
    setattr(
        converter_instance,
        "output_info",
        AttributeSpec(name="output_info", field=output_info_field),
    )

    # Test uint8 image
    df1 = pl.DataFrame({"my_callable": [uint8_callable]}, schema={"my_callable": pl.Object})
    result1 = converter_instance.convert(df1)
    image_data1 = np.array(result1["output_image"][0], dtype=np.uint8).reshape([1, 1, 3])
    assert image_data1.dtype == np.uint8
    assert image_data1[0, 0, 0] == 255
    assert image_data1[0, 0, 1] == 0
    assert image_data1[0, 0, 2] == 128

    # Test float32 image with different output field
    output_field_f32 = ImageField(dtype=pl.Float32(), format="RGB")
    setattr(
        converter_instance,
        "output_image",
        AttributeSpec(name="output_image", field=output_field_f32),
    )

    df2 = pl.DataFrame({"my_callable": [float32_callable]}, schema={"my_callable": pl.Object})
    result2 = converter_instance.convert(df2)
    image_data2 = np.array(result2["output_image"][0], dtype=np.float32).reshape([1, 1, 3])
    assert image_data2.dtype == np.float32
    assert image_data2[0, 0, 0] == 1.0
    assert image_data2[0, 0, 1] == 0.5
    assert image_data2[0, 0, 2] == 0.25


def test_channels_first_converter():
    """Test ChannelsFirstConverter updates metadata without data transposition."""

    converter_instance = ChannelsFirstConverter()

    # Create test data with channels-first image (the data is stored flattened)
    # Shape would be (3, 2, 2) for channels-first
    image_data = list(range(12))  # 3 channels * 2 height * 2 width
    df = pl.DataFrame(
        {
            "image": [image_data],
            "image_shape": [[3, 2, 2]],  # channels-first shape (C, H, W)
        },
        schema=pl.Schema({"image": pl.List(pl.UInt8), "image_shape": pl.List(pl.Int32)}),
    )

    # Set up converter attributes
    input_field = ImageField(dtype=pl.UInt8(), format="RGB", channels_first=True)
    output_field = ImageField(dtype=pl.UInt8(), format="RGB", channels_first=False)

    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=input_field))
    setattr(converter_instance, "output_image", AttributeSpec(name="image", field=output_field))

    # Test filter - should return True for channels_first change
    assert converter_instance.filter_output_spec() is True

    # Test conversion - should just copy the data (transposition handled by from_polars)
    result_df = converter_instance.convert(df)

    assert "image" in result_df.columns
    assert "image_shape" in result_df.columns

    # Data should be unchanged
    assert result_df["image"][0].to_list() == image_data
    # Shape should be unchanged (the field handles transposition on read)
    assert result_df["image_shape"][0].to_list() == [3, 2, 2]


def test_channels_first_converter_same_channels_first():
    """Test ChannelsFirstConverter returns False when channels_first is the same."""

    converter_instance = ChannelsFirstConverter()

    # Set up converter attributes with same channels_first
    input_field = ImageField(dtype=pl.UInt8(), format="RGB", channels_first=True)
    output_field = ImageField(dtype=pl.UInt8(), format="RGB", channels_first=True)

    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=input_field))
    setattr(converter_instance, "output_image", AttributeSpec(name="image", field=output_field))

    # Test filter - should return False when channels_first is the same
    assert converter_instance.filter_output_spec() is False


def test_channels_first_converter_schema_conversion():
    """Test schema conversion for channels_first change using find_conversion_path."""

    # Create source schema with channels_first=True
    source_schema = Schema(
        attributes={
            "image": AttributeInfo(
                type=np.ndarray,
                field=ImageField(dtype=pl.UInt8(), format="RGB", channels_first=True),
            )
        }
    )

    # Create target schema with channels_first=False
    target_schema = Schema(
        attributes={
            "image": AttributeInfo(
                type=np.ndarray,
                field=ImageField(dtype=pl.UInt8(), format="RGB", channels_first=False),
            )
        }
    )

    # Find conversion path
    conversion_paths, _ = find_conversion_path(source_schema, target_schema)

    # Should have exactly one converter
    assert len(conversion_paths.converters["image"]) == 1
    assert type(conversion_paths.converters["image"][0]) is ChannelsFirstConverter


def test_image_path_to_image_converter_16bit():
    """Test that 16-bit images are loaded without truncation to 8-bit."""
    with tempfile.TemporaryDirectory() as temp_dir:
        from PIL import Image as PILImage

        # Create a 16-bit grayscale test image
        test_image_path = os.path.join(temp_dir, "test_16bit.png")
        # Values above 255 to verify they survive round-trip (would be lost with uint8)
        img_array_16 = np.array([[1000, 2000], [30000, 65535]], dtype=np.uint16)
        test_img = PILImage.fromarray(img_array_16, mode="I;16")
        test_img.save(test_image_path)

        converter_instance = ImagePathToImageConverter()  # type: ignore[call-arg]

        # Create test data
        df = pl.DataFrame({"image_path": [test_image_path]})

        # Set up converter attributes
        input_field = ImagePathField()
        output_field = ImageField(dtype=pl.UInt8(), format="GRAY")  # default dtype, should be overridden

        setattr(
            converter_instance,
            "input_path",
            AttributeSpec(name="image_path", field=input_field),
        )
        setattr(
            converter_instance,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        # Test filter
        assert converter_instance.filter_output_spec() is True

        # Test conversion
        result_df = converter_instance.convert(df)

        assert "image" in result_df.columns
        assert "image_shape" in result_df.columns

        # After conversion, the dtype should have been updated to UInt16
        assert converter_instance.output_image.field.dtype == pl.UInt16()

        # Check that image shape is correct (H, W, 1) for grayscale
        result_shape = list(result_df["image_shape"][0])
        assert result_shape == [2, 2, 1]

        # Check that 16-bit values are preserved (not truncated to 8-bit)
        result_data = result_df["image"][0].to_numpy().reshape(result_shape)
        assert result_data.dtype == np.uint16
        assert result_data[0, 0, 0] == 1000
        assert result_data[0, 1, 0] == 2000
        assert result_data[1, 0, 0] == 30000
        assert result_data[1, 1, 0] == 65535


def test_image_dtype_converter_uint16_to_float32():
    """Test UInt16 to Float32 conversion with normalization."""
    converter_instance = ImageDtypeConverter()  # type: ignore[call-arg]

    # Create test data with UInt16 values
    uint16_data = [0, 32768, 65535, 1000, 60000, 100]
    df = pl.DataFrame(
        {"image": [uint16_data], "image_shape": [[2, 3]]},
        schema=pl.Schema({"image": pl.List(pl.UInt16()), "image_shape": pl.List(pl.Int64)}),
    )

    input_field = ImageField(dtype=pl.UInt16(), format="RGB")
    output_field = ImageField(dtype=pl.Float32(), format="RGB")

    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=input_field))
    setattr(converter_instance, "output_image", AttributeSpec(name="image", field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)
    result_data = result_df["image"][0]

    # Check normalization: values should be in [0, 1]
    assert (result_data >= 0).all()
    assert (result_data <= 1).all()
    # 0 / 65535 == 0.0
    assert result_data[0] == pytest.approx(0.0)
    # 65535 / 65535 == 1.0
    assert result_data[2] == pytest.approx(1.0)
    # 32768 / 65535 ≈ 0.5
    assert result_data[1] == pytest.approx(32768 / 65535, abs=1e-5)


def test_image_dtype_converter_float32_to_uint8():
    """Test Float32 to UInt8 conversion with denormalization."""
    converter_instance = ImageDtypeConverter()  # type: ignore[call-arg]

    float_data = [0.0, 0.5, 1.0, 0.25, 0.75, 0.1]
    df = pl.DataFrame(
        {"image": [float_data], "image_shape": [[2, 3]]},
        schema=pl.Schema({"image": pl.List(pl.Float32()), "image_shape": pl.List(pl.Int64)}),
    )

    input_field = ImageField(dtype=pl.Float32(), format="RGB")
    output_field = ImageField(dtype=pl.UInt8(), format="RGB")

    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=input_field))
    setattr(converter_instance, "output_image", AttributeSpec(name="image", field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)
    result_data = result_df["image"][0].to_list()

    # 0.0 * 255 = 0, 0.5 * 255 = 128 (rounded), 1.0 * 255 = 255
    assert result_data[0] == 0
    assert result_data[1] == 128
    assert result_data[2] == 255
    assert result_data[3] == 64  # 0.25 * 255 = 63.75, rounded = 64
    assert result_data[4] == 191  # 0.75 * 255 = 191.25, rounded = 191


def test_image_dtype_converter_float32_to_uint16():
    """Test Float32 to UInt16 conversion with denormalization."""
    converter_instance = ImageDtypeConverter()  # type: ignore[call-arg]

    float_data = [0.0, 0.5, 1.0]
    df = pl.DataFrame(
        {"image": [float_data], "image_shape": [[1, 3]]},
        schema=pl.Schema({"image": pl.List(pl.Float32()), "image_shape": pl.List(pl.Int64)}),
    )

    input_field = ImageField(dtype=pl.Float32(), format="GRAY")
    output_field = ImageField(dtype=pl.UInt16(), format="GRAY")

    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=input_field))
    setattr(converter_instance, "output_image", AttributeSpec(name="image", field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)
    result_data = result_df["image"][0].to_list()

    assert result_data[0] == 0
    assert result_data[1] == 32768  # 0.5 * 65535 = 32767.5, rounded = 32768
    assert result_data[2] == 65535


def test_image_dtype_converter_uint8_to_uint16():
    """Test UInt8 to UInt16 rescaling."""
    converter_instance = ImageDtypeConverter()  # type: ignore[call-arg]

    uint8_data = [0, 128, 255]
    df = pl.DataFrame(
        {"image": [uint8_data], "image_shape": [[1, 3]]},
        schema=pl.Schema({"image": pl.List(pl.UInt8()), "image_shape": pl.List(pl.Int64)}),
    )

    input_field = ImageField(dtype=pl.UInt8(), format="GRAY")
    output_field = ImageField(dtype=pl.UInt16(), format="GRAY")

    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=input_field))
    setattr(converter_instance, "output_image", AttributeSpec(name="image", field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)
    result_data = result_df["image"][0].to_list()

    # 0 -> 0, 255 -> 65535
    assert result_data[0] == 0
    assert result_data[2] == 65535
    # 128 * (65535/255) = 128 * 257.0 = 32896
    assert result_data[1] == 32896


def test_image_dtype_converter_uint16_to_uint8():
    """Test UInt16 to UInt8 rescaling."""
    converter_instance = ImageDtypeConverter()  # type: ignore[call-arg]

    uint16_data = [0, 32768, 65535]
    df = pl.DataFrame(
        {"image": [uint16_data], "image_shape": [[1, 3]]},
        schema=pl.Schema({"image": pl.List(pl.UInt16()), "image_shape": pl.List(pl.Int64)}),
    )

    input_field = ImageField(dtype=pl.UInt16(), format="GRAY")
    output_field = ImageField(dtype=pl.UInt8(), format="GRAY")

    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=input_field))
    setattr(converter_instance, "output_image", AttributeSpec(name="image", field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)
    result_data = result_df["image"][0].to_list()

    # 0 -> 0, 65535 -> 255
    assert result_data[0] == 0
    assert result_data[2] == 255
    # 32768 * (255/65535) ≈ 127.5 -> 128
    assert result_data[1] == 128


def test_image_dtype_converter_float64_to_float32():
    """Test Float64 to Float32 simple cast."""
    converter_instance = ImageDtypeConverter()  # type: ignore[call-arg]

    float64_data = [0.0, 0.123456789, 1.0]
    df = pl.DataFrame(
        {"image": [float64_data], "image_shape": [[1, 3]]},
        schema=pl.Schema({"image": pl.List(pl.Float64()), "image_shape": pl.List(pl.Int64)}),
    )

    input_field = ImageField(dtype=pl.Float64(), format="GRAY")
    output_field = ImageField(dtype=pl.Float32(), format="GRAY")

    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=input_field))
    setattr(converter_instance, "output_image", AttributeSpec(name="image", field=output_field))

    assert converter_instance.filter_output_spec() is True

    result_df = converter_instance.convert(df)
    result_data = result_df["image"][0]

    assert result_data[0] == pytest.approx(0.0)
    assert result_data[1] == pytest.approx(0.123456789, abs=1e-6)
    assert result_data[2] == pytest.approx(1.0)


def test_image_dtype_converter_same_dtype_no_op():
    """Test that filter returns False when input and output dtypes match."""
    converter_instance = ImageDtypeConverter()  # type: ignore[call-arg]

    input_field = ImageField(dtype=pl.UInt8(), format="RGB")
    output_field = ImageField(dtype=pl.UInt8(), format="RGB")

    setattr(converter_instance, "input_image", AttributeSpec(name="image", field=input_field))
    setattr(converter_instance, "output_image", AttributeSpec(name="image", field=output_field))

    # Should return False — no conversion needed
    assert converter_instance.filter_output_spec() is False


def test_image_dtype_converter_schema_conversion_uint16_to_float32():
    """Test that A* search finds ImageDtypeConverter for UInt16 → Float32."""
    source_schema = Schema(
        attributes={"image": AttributeInfo(type=np.ndarray, field=ImageField(dtype=pl.UInt16(), format="RGB"))}
    )
    target_schema = Schema(
        attributes={"image": AttributeInfo(type=np.ndarray, field=ImageField(dtype=pl.Float32(), format="RGB"))}
    )

    path, _ = find_conversion_path(source_schema, target_schema)
    assert len(path.converters["image"]) == 1
    assert type(path.converters["image"][0]) is ImageDtypeConverter


# ============================================================================
# EXIF orientation handling
# ============================================================================


_EXIF_ORIENTATION_TAG = 0x0112


def _save_jpeg_with_orientation(path: str, img_array: np.ndarray, orientation: int) -> None:
    """Save a JPEG with a given EXIF Orientation tag.

    JPEG is required to round-trip the EXIF orientation tag reliably.
    """
    from PIL import Image as PILImage

    img = PILImage.fromarray(img_array)
    exif = img.getexif()
    exif[_EXIF_ORIENTATION_TAG] = orientation
    img.save(path, format="JPEG", exif=exif.tobytes())


def _run_image_path_to_image(path: str) -> pl.DataFrame:
    """Run ImagePathToImageConverter on a single-path DataFrame."""
    converter_instance = ImagePathToImageConverter()  # type: ignore[call-arg]
    df = pl.DataFrame({"image_path": [path]})

    setattr(
        converter_instance,
        "input_path",
        AttributeSpec(name="image_path", field=ImagePathField()),
    )
    setattr(
        converter_instance,
        "output_image",
        AttributeSpec(name="image", field=ImageField(dtype=pl.UInt8(), format="RGB")),
    )
    setattr(
        converter_instance,
        "output_info",
        AttributeSpec(name="image_info", field=ImageInfoField()),
    )
    assert converter_instance.filter_output_spec() is True
    return converter_instance.convert(df)


@pytest.mark.parametrize("orientation", [5, 6, 7, 8])
def test_image_path_to_image_converter_respects_exif_orientation(orientation):
    """ImagePathToImageConverter must honor EXIF orientation for rotating tags.

    Orientations 5-8 imply a 90°/270° rotation; the loaded pixel data must
    reflect the oriented dimensions so it stays consistent with LazyImage
    and with ``image_info`` (which is computed separately by a dedicated
    converter that also honors EXIF).
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Raw pixels: landscape H=40, W=80.
        img_array = np.zeros((40, 80, 3), dtype=np.uint8)
        path = os.path.join(temp_dir, f"orient_{orientation}.jpg")
        _save_jpeg_with_orientation(path, img_array, orientation)

        result_df = _run_image_path_to_image(path)

        # After orientation, the image is portrait: H=80, W=40.
        assert list(result_df["image_shape"][0]) == [80, 40, 3]


@pytest.mark.parametrize("orientation", [1, 2, 3, 4])
def test_image_path_to_image_converter_keeps_dimensions_for_non_rotating_orientation(orientation):
    """Orientations 1-4 do not swap width/height."""
    with tempfile.TemporaryDirectory() as temp_dir:
        img_array = np.zeros((40, 80, 3), dtype=np.uint8)
        path = os.path.join(temp_dir, f"orient_{orientation}.jpg")
        _save_jpeg_with_orientation(path, img_array, orientation)

        result_df = _run_image_path_to_image(path)

        assert list(result_df["image_shape"][0]) == [40, 80, 3]


def test_image_bytes_to_image_converter_respects_exif_orientation():
    """ImageBytesToImageConverter must honor EXIF orientation embedded in bytes."""
    import io

    from PIL import Image as PILImage

    # Raw pixels: landscape H=40, W=80. Save with orientation=6 (90° CW).
    img_array = np.zeros((40, 80, 3), dtype=np.uint8)
    pil_img = PILImage.fromarray(img_array)
    exif = pil_img.getexif()
    exif[_EXIF_ORIENTATION_TAG] = 6
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", exif=exif.tobytes())
    image_bytes = buf.getvalue()

    converter_instance = ImageBytesToImageConverter()  # type: ignore[call-arg]
    df = pl.DataFrame({"image_bytes": [image_bytes]})

    setattr(
        converter_instance,
        "input_bytes",
        AttributeSpec(name="image_bytes", field=ImageBytesField()),
    )
    setattr(
        converter_instance,
        "output_image",
        AttributeSpec(name="image", field=ImageField(dtype=pl.UInt8(), format="RGB")),
    )
    setattr(
        converter_instance,
        "output_info",
        AttributeSpec(name="image_info", field=ImageInfoField()),
    )
    assert converter_instance.filter_output_spec() is True
    result_df = converter_instance.convert(df)

    # After orientation, image is portrait: H=80, W=40.
    assert list(result_df["image_shape"][0]) == [80, 40, 3]


@pytest.mark.parametrize(
    ("orientation", "expected_width", "expected_height"),
    [
        (1, 80, 40),
        (2, 80, 40),
        (3, 80, 40),
        (4, 80, 40),
        (5, 40, 80),
        (6, 40, 80),
        (7, 40, 80),
        (8, 40, 80),
    ],
)
def test_image_path_to_image_info_converter_respects_exif_orientation(orientation, expected_width, expected_height):
    """ImagePathToImageInfoConverter must honor EXIF orientation.

    This converter is used when only dimensions are needed (no pixel load),
    so it's crucial that it reports the oriented dimensions consistently
    with the full image loader.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Raw pixels: landscape H=40, W=80.
        img_array = np.zeros((40, 80, 3), dtype=np.uint8)
        path = os.path.join(temp_dir, f"orient_{orientation}.jpg")
        _save_jpeg_with_orientation(path, img_array, orientation)

        converter_instance = ImagePathToImageInfoConverter()  # type: ignore[call-arg]
        df = pl.DataFrame({"image_path": [path]})

        setattr(
            converter_instance,
            "input_path",
            AttributeSpec(name="image_path", field=ImagePathField()),
        )
        setattr(
            converter_instance,
            "output_info",
            AttributeSpec(name="image_info", field=ImageInfoField()),
        )
        assert converter_instance.filter_output_spec() is True
        result_df = converter_instance.convert(df)

        info = result_df["image_info"][0]
        assert info["width"] == expected_width
        assert info["height"] == expected_height
