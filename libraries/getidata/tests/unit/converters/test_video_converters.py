# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for video converters.

Tests cover:
- VideoFramePathToImageConverter
- VideoFrameToImageCallableConverter
- MediaPathToImageConverter
- MediaPathToImageCallableConverter
"""

from pathlib import Path

import numpy as np
import polars as pl
import pytest

from getidata.converters.media_converters import MediaPathToImageCallableConverter, MediaPathToImageConverter
from getidata.converters.video_converters import VideoFramePathToImageConverter, VideoFrameToImageCallableConverter
from getidata.fields import ImageCallableField, ImageField
from getidata.fields.videos import MediaPathField, VideoFramePathField
from getidata.media import VideoFrameCache
from getidata.schema import AttributeSpec

# Path to test video in assets
TEST_VIDEO_PATH = Path(__file__).parent.parent.parent / "assets" / "cvat_dataset" / "test.mp4"


class VideoFramePathToImageConverterTest:
    """Tests for VideoFramePathToImageConverter."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear caches before each test."""
        VideoFrameCache.clear()
        yield
        VideoFrameCache.clear()

    @pytest.fixture
    def test_video(self):
        return TEST_VIDEO_PATH

    def test_filter_output_spec_sets_correct_format(self, test_video):
        """Test filter_output_spec() sets the correct output format."""
        converter = VideoFramePathToImageConverter()

        input_field = VideoFramePathField(semantic="test", format="RGB")
        output_field = ImageField(format="RGB")

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        result = converter.filter_output_spec()
        assert result is True
        assert converter.output_image.field.format == "RGB"
        assert converter.output_image.field.dtype == pl.UInt8()

    def test_filter_output_spec_default_format(self):
        """Test filter_output_spec() uses RGB as default format."""
        converter = VideoFramePathToImageConverter()

        input_field = VideoFramePathField(semantic="test")
        output_field = ImageField()  # No format specified

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        result = converter.filter_output_spec()
        assert result is True
        assert converter.output_image.field.format == "RGB"

    def test_filter_output_spec_bgr_format(self):
        """Test filter_output_spec() supports BGR format."""
        converter = VideoFramePathToImageConverter()

        input_field = VideoFramePathField(semantic="test", format="BGR")
        output_field = ImageField(format="BGR")

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        result = converter.filter_output_spec()
        assert result is True
        assert converter.output_image.field.format == "BGR"

    def test_filter_output_spec_unsupported_format_raises_error(self):
        """Test filter_output_spec() raises error for unsupported format."""
        converter = VideoFramePathToImageConverter()

        input_field = VideoFramePathField(semantic="test")
        output_field = ImageField(format="YUV")  # Unsupported format

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        with pytest.raises(ValueError, match="Unsupported output format 'YUV'"):
            converter.filter_output_spec()

    def test_convert_loads_video_frame(self, test_video):
        """Test convert() correctly loads video frame data."""
        converter = VideoFramePathToImageConverter()

        input_field = VideoFramePathField(semantic="test", format="RGB")
        output_field = ImageField(format="RGB")

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        converter.filter_output_spec()

        # Create test DataFrame with video frame reference
        df = pl.DataFrame(
            {
                "frame": [str(test_video)],
                "frame_frame_index": [0],  # First frame
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)

        # Check output columns exist
        assert "image" in result_df.columns
        assert "image_shape" in result_df.columns

        # Check image data is loaded
        image_data = result_df["image"][0]
        image_shape = list(result_df["image_shape"][0])

        assert image_data is not None
        assert len(image_shape) == 3  # H, W, C
        assert image_shape[2] == 3  # RGB has 3 channels

    def test_convert_handles_none_path(self, test_video):
        """Test convert() handles None path correctly."""
        converter = VideoFramePathToImageConverter()

        input_field = VideoFramePathField(semantic="test", format="RGB")
        output_field = ImageField(format="RGB")

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        converter.filter_output_spec()

        df = pl.DataFrame(
            {
                "frame": [None],
                "frame_frame_index": [None],
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)

        assert result_df["image"][0] is None
        assert len(result_df["image_shape"][0]) == 0

    def test_convert_multiple_frames(self, test_video):
        """Test convert() handles multiple frames correctly."""
        converter = VideoFramePathToImageConverter()

        input_field = VideoFramePathField(semantic="test", format="RGB")
        output_field = ImageField(format="RGB")

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        converter.filter_output_spec()

        df = pl.DataFrame(
            {
                "frame": [str(test_video), str(test_video)],
                "frame_frame_index": [0, 1],
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)

        assert len(result_df) == 2
        assert result_df["image"][0] is not None
        assert result_df["image"][1] is not None


class VideoFrameToImageCallableConverterTest:
    """Tests for VideoFrameToImageCallableConverter."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear caches before each test."""
        VideoFrameCache.clear()
        yield
        VideoFrameCache.clear()

    @pytest.fixture
    def test_video_exists(self):
        """Skip if test video is not available."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
        return TEST_VIDEO_PATH

    def test_filter_output_spec_sets_semantic(self, test_video_exists):
        """Test filter_output_spec() sets semantic from input."""
        converter = VideoFrameToImageCallableConverter()

        input_field = VideoFramePathField(semantic="test_semantic", format="RGB")
        output_field = ImageCallableField()

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_callable",
            AttributeSpec(name="callable", field=output_field),
        )

        result = converter.filter_output_spec()
        assert result is True
        assert converter.output_callable.field.semantic == "test_semantic"

    def test_convert_creates_callable(self, test_video_exists):
        """Test convert() creates callable that loads frame data."""
        converter = VideoFrameToImageCallableConverter()

        input_field = VideoFramePathField(semantic="test", format="RGB")
        output_field = ImageCallableField()

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_callable",
            AttributeSpec(name="callable", field=output_field),
        )

        converter.filter_output_spec()

        df = pl.DataFrame(
            {
                "frame": [str(test_video_exists)],
                "frame_frame_index": [0],
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)

        assert "callable" in result_df.columns

        # Test that the callable works
        loader = result_df["callable"][0]
        assert callable(loader)

        frame_data = loader()
        assert isinstance(frame_data, np.ndarray)
        assert frame_data.ndim == 3
        assert frame_data.shape[2] == 3  # RGB

    def test_convert_handles_none_path(self, test_video_exists):
        """Test convert() handles None path correctly."""
        converter = VideoFrameToImageCallableConverter()

        input_field = VideoFramePathField(semantic="test", format="RGB")
        output_field = ImageCallableField()

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_callable",
            AttributeSpec(name="callable", field=output_field),
        )

        converter.filter_output_spec()

        df = pl.DataFrame(
            {
                "frame": [None],
                "frame_frame_index": [None],
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)
        assert result_df["callable"][0] is None


class MediaPathToImageConverterTest:
    """Tests for MediaPathToImageConverter (unified image/video field)."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear caches before each test."""
        VideoFrameCache.clear()
        yield
        VideoFrameCache.clear()

    @pytest.fixture
    def test_video_exists(self):
        """Skip if test video is not available."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
        return TEST_VIDEO_PATH

    @pytest.fixture
    def test_image_path(self, tmp_path):
        """Create a test image file."""
        from PIL import Image as PILImage

        img_path = tmp_path / "test.png"
        img_array = np.random.randint(0, 255, (50, 75, 3), dtype=np.uint8)
        test_img = PILImage.fromarray(img_array)
        test_img.save(img_path)
        return img_path

    def test_filter_output_spec_default_format(self):
        """Test filter_output_spec() uses RGB as default."""
        converter = MediaPathToImageConverter()

        input_field = MediaPathField(semantic="test")
        output_field = ImageField()

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        result = converter.filter_output_spec()
        assert result is True
        assert converter.output_image.field.format == "RGB"
        assert converter.output_image.field.dtype == pl.UInt8()

    def test_filter_output_spec_unsupported_format_raises_error(self):
        """Test filter_output_spec() raises error for unsupported format."""
        converter = MediaPathToImageConverter()

        input_field = MediaPathField(semantic="test")
        output_field = ImageField(format="CMYK")

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        with pytest.raises(ValueError, match="Unsupported output format 'CMYK'"):
            converter.filter_output_spec()

    def test_convert_loads_video_frame(self, test_video_exists):
        """Test convert() correctly loads video frame when frame_index is set."""
        converter = MediaPathToImageConverter()

        input_field = MediaPathField(semantic="test", format="RGB")
        output_field = ImageField(format="RGB")

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        converter.filter_output_spec()

        # Video frame: frame_index is set
        df = pl.DataFrame(
            {
                "media": [str(test_video_exists)],
                "media_frame_index": [0],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)

        assert "image" in result_df.columns
        assert "image_shape" in result_df.columns

        image_data = result_df["image"][0]
        image_shape = list(result_df["image_shape"][0])

        assert image_data is not None
        assert len(image_shape) == 3
        assert image_shape[2] == 3

    def test_convert_loads_image(self, test_image_path):
        """Test convert() correctly loads image when frame_index is None."""
        converter = MediaPathToImageConverter()

        input_field = MediaPathField(semantic="test", format="RGB")
        output_field = ImageField(format="RGB")

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        converter.filter_output_spec()

        # Image: frame_index is None
        df = pl.DataFrame(
            {
                "media": [str(test_image_path)],
                "media_frame_index": [None],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)

        assert "image" in result_df.columns
        image_data = result_df["image"][0]
        image_shape = list(result_df["image_shape"][0])

        assert image_data is not None
        assert image_shape == [50, 75, 3]  # H, W, C

    def test_convert_mixed_image_and_video(self, test_video_exists, test_image_path):
        """Test convert() handles mixed images and video frames."""
        converter = MediaPathToImageConverter()

        input_field = MediaPathField(semantic="test", format="RGB")
        output_field = ImageField(format="RGB")

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        converter.filter_output_spec()

        # Mixed: first is image, second is video frame
        df = pl.DataFrame(
            {
                "media": [str(test_image_path), str(test_video_exists)],
                "media_frame_index": [None, 0],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)

        assert len(result_df) == 2
        assert result_df["image"][0] is not None
        assert result_df["image"][1] is not None

    def test_convert_handles_none_path(self):
        """Test convert() handles None path correctly."""
        converter = MediaPathToImageConverter()

        input_field = MediaPathField(semantic="test", format="RGB")
        output_field = ImageField(format="RGB")

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        converter.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": [None],
                "media_frame_index": [None],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)

        assert result_df["image"][0] is None
        assert len(result_df["image_shape"][0]) == 0


class MediaPathToImageCallableConverterTest:
    """Tests for MediaPathToImageCallableConverter."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear caches before each test."""
        VideoFrameCache.clear()
        yield
        VideoFrameCache.clear()

    @pytest.fixture
    def test_video_exists(self):
        """Skip if test video is not available."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
        return TEST_VIDEO_PATH

    @pytest.fixture
    def test_image_path(self, tmp_path):
        """Create a test image file."""
        from PIL import Image as PILImage

        img_path = tmp_path / "test.png"
        img_array = np.random.randint(0, 255, (50, 75, 3), dtype=np.uint8)
        test_img = PILImage.fromarray(img_array)
        test_img.save(img_path)
        return img_path

    def test_filter_output_spec_sets_semantic(self):
        """Test filter_output_spec() sets semantic from input."""
        converter = MediaPathToImageCallableConverter()

        input_field = MediaPathField(semantic="test_semantic", format="RGB")
        output_field = ImageCallableField()

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_callable",
            AttributeSpec(name="callable", field=output_field),
        )

        result = converter.filter_output_spec()
        assert result is True
        assert converter.output_callable.field.semantic == "test_semantic"

    def test_convert_creates_callable_for_video_frame(self, test_video_exists):
        """Test convert() creates callable for video frame."""
        converter = MediaPathToImageCallableConverter()

        input_field = MediaPathField(semantic="test", format="RGB")
        output_field = ImageCallableField()

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_callable",
            AttributeSpec(name="callable", field=output_field),
        )

        converter.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": [str(test_video_exists)],
                "media_frame_index": [0],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)

        loader = result_df["callable"][0]
        assert callable(loader)

        frame_data = loader()
        assert isinstance(frame_data, np.ndarray)
        assert frame_data.ndim == 3

    def test_convert_creates_callable_for_image(self, test_image_path):
        """Test convert() creates callable for image."""
        converter = MediaPathToImageCallableConverter()

        input_field = MediaPathField(semantic="test", format="RGB")
        output_field = ImageCallableField()

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_callable",
            AttributeSpec(name="callable", field=output_field),
        )

        converter.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": [str(test_image_path)],
                "media_frame_index": [None],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)

        loader = result_df["callable"][0]
        assert callable(loader)

        image_data = loader()
        assert isinstance(image_data, np.ndarray)
        assert image_data.shape == (50, 75, 3)

    def test_convert_handles_none_path(self):
        """Test convert() handles None path correctly."""
        converter = MediaPathToImageCallableConverter()

        input_field = MediaPathField(semantic="test", format="RGB")
        output_field = ImageCallableField()

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_callable",
            AttributeSpec(name="callable", field=output_field),
        )

        converter.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": [None],
                "media_frame_index": [None],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)
        assert result_df["callable"][0] is None


class ConverterFormatsTest:
    """Test various format conversions for video converters."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear caches before each test."""
        VideoFrameCache.clear()
        yield
        VideoFrameCache.clear()

    @pytest.fixture
    def test_video_exists(self):
        """Skip if test video is not available."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
        return TEST_VIDEO_PATH

    @pytest.mark.parametrize("format_name", ["RGB", "BGR", "RGBA", "GRAY"])
    def test_video_frame_path_converter_formats(self, test_video_exists, format_name):
        """Test VideoFramePathToImageConverter with different formats."""
        converter = VideoFramePathToImageConverter()

        input_field = VideoFramePathField(semantic="test", format=format_name)
        output_field = ImageField(format=format_name)

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        result = converter.filter_output_spec()
        assert result is True
        assert converter.output_image.field.format == format_name

        df = pl.DataFrame(
            {
                "frame": [str(test_video_exists)],
                "frame_frame_index": [0],
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)
        image_shape = list(result_df["image_shape"][0])

        if format_name == "GRAY":
            # Grayscale should have 2D or 3D with 1 channel
            assert len(image_shape) >= 2
        elif format_name == "RGBA":
            assert image_shape[-1] == 4
        else:
            assert image_shape[-1] == 3

    @pytest.mark.parametrize("format_name", ["RGB", "BGR", "RGBA", "GRAY"])
    def test_media_path_converter_formats(self, test_video_exists, format_name):
        """Test MediaPathToImageConverter with different formats."""
        converter = MediaPathToImageConverter()

        input_field = MediaPathField(semantic="test", format=format_name)
        output_field = ImageField(format=format_name)

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        result = converter.filter_output_spec()
        assert result is True
        assert converter.output_image.field.format == format_name

        df = pl.DataFrame(
            {
                "media": [str(test_video_exists)],
                "media_frame_index": [0],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)
        image_shape = list(result_df["image_shape"][0])

        assert len(image_shape) >= 2


class ConverterChannelsFirstTest:
    """Test channels_first option for video converters."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear caches before each test."""
        VideoFrameCache.clear()
        yield
        VideoFrameCache.clear()

    @pytest.fixture
    def test_video_exists(self):
        """Skip if test video is not available."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
        return TEST_VIDEO_PATH

    def test_video_frame_converter_channels_first(self, test_video_exists):
        """Test VideoFramePathToImageConverter with channels_first=True."""
        converter = VideoFramePathToImageConverter()

        input_field = VideoFramePathField(semantic="test", format="RGB", channels_first=True)
        output_field = ImageField(format="RGB", channels_first=True)

        setattr(
            converter,
            "input_frame",
            AttributeSpec(name="frame", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        converter.filter_output_spec()

        df = pl.DataFrame(
            {
                "frame": [str(test_video_exists)],
                "frame_frame_index": [0],
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)
        image_shape = list(result_df["image_shape"][0])

        # Internally stored as HWC; ImageField.from_polars handles CHW conversion
        assert image_shape[-1] == 3  # RGB channels last in storage

    def test_media_path_converter_channels_first(self, test_video_exists):
        """Test MediaPathToImageConverter with channels_first=True."""
        converter = MediaPathToImageConverter()

        input_field = MediaPathField(semantic="test", format="RGB", channels_first=True)
        output_field = ImageField(format="RGB", channels_first=True)

        setattr(
            converter,
            "input_media",
            AttributeSpec(name="media", field=input_field),
        )
        setattr(
            converter,
            "output_image",
            AttributeSpec(name="image", field=output_field),
        )

        converter.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": [str(test_video_exists)],
                "media_frame_index": [0],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result_df = converter.convert(df)
        image_shape = list(result_df["image_shape"][0])

        # Internally stored as HWC; ImageField.from_polars handles CHW conversion
        assert image_shape[-1] == 3  # RGB channels last in storage
