# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for video-related field definitions.

Tests cover:
- VideoFramePathField: path + frame_index storage and LazyVideoFrame reconstruction
- VideoInfoField: video metadata struct serialization/deserialization
- VideoFrameCallableField: callable storage for video frame loaders
- MediaPathField: unified field for images and video frames
- Helper functions: video_frame_path_field(), video_info_field(), etc.
"""

from pathlib import Path
from typing import Callable, Union

import numpy as np
import polars as pl
import pytest

from getidata.dataset import Dataset, Sample
from getidata.fields.videos import (
    MediaPathField,
    VideoFrameCallableField,
    VideoFramePathField,
    VideoInfoField,
    media_path_field,
    video_frame_callable_field,
    video_frame_path_field,
    video_info_field,
)
from getidata.media import LazyImage, LazyVideoFrame, VideoInfo

# Path to test video in assets
TEST_VIDEO_PATH = Path(__file__).parent.parent.parent / "assets" / "cvat_dataset" / "test.mp4"


class VideoFramePathFieldTest:
    """Tests for VideoFramePathField."""

    def test_to_polars_schema_returns_correct_columns(self):
        """Test to_polars_schema() returns path and frame_index columns."""
        field = VideoFramePathField(semantic="test", format="RGB")
        schema = field.to_polars_schema("frame")

        assert "frame" in schema
        assert "frame_frame_index" in schema
        assert schema["frame"] == pl.Categorical()
        assert schema["frame_frame_index"] == pl.UInt32()

    def test_to_polars_with_lazy_video_frame(self):
        """Test to_polars() correctly serializes LazyVideoFrame."""
        field = VideoFramePathField(semantic="test", format="RGB")
        lazy_frame = LazyVideoFrame("/path/to/video.mp4", frame_index=42)

        result = field.to_polars("frame", lazy_frame)

        assert "frame" in result
        assert "frame_frame_index" in result
        assert result["frame"][0] == "/path/to/video.mp4"
        assert result["frame_frame_index"][0] == 42

    def test_to_polars_with_tuple_input(self):
        """Test to_polars() correctly serializes (path, frame_index) tuple."""
        field = VideoFramePathField(semantic="test", format="RGB")
        value = ("/path/to/video.mp4", 100)

        result = field.to_polars("frame", value)

        assert result["frame"][0] == "/path/to/video.mp4"
        assert result["frame_frame_index"][0] == 100

    def test_to_polars_with_none_value(self):
        """Test to_polars() handles None value correctly."""
        field = VideoFramePathField(semantic="test", format="RGB")

        result = field.to_polars("frame", None)

        assert result["frame"][0] is None
        assert result["frame_frame_index"][0] is None

    def test_to_polars_raises_error_for_invalid_type(self):
        """Test to_polars() raises TypeError for invalid input."""
        field = VideoFramePathField(semantic="test", format="RGB")

        with pytest.raises(TypeError, match="Expected LazyVideoFrame or"):
            field.to_polars("frame", "invalid_string")

    def test_from_polars_returns_lazy_video_frame(self):
        """Test from_polars() reconstructs LazyVideoFrame correctly."""
        field = VideoFramePathField(semantic="test", format="RGB", channels_first=False)

        df = pl.DataFrame(
            {
                "frame": ["/path/to/video.mp4"],
                "frame_frame_index": [42],
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        result = field.from_polars("frame", 0, df, LazyVideoFrame)

        assert isinstance(result, LazyVideoFrame)
        assert result.video_path == "/path/to/video.mp4"
        assert result.frame_index == 42
        assert result.format == "RGB"
        assert result.channels_first is False

    def test_from_polars_returns_none_for_none_path(self):
        """Test from_polars() returns None when path is None."""
        field = VideoFramePathField(semantic="test", format="RGB")

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

        result = field.from_polars("frame", 0, df, LazyVideoFrame)

        assert result is None

    def test_from_polars_with_union_type_returns_lazy_video_frame(self):
        """Test from_polars() returns LazyVideoFrame for Union types containing it."""
        field = VideoFramePathField(semantic="test", format="BGR")

        df = pl.DataFrame(
            {
                "frame": ["/path/to/video.mp4"],
                "frame_frame_index": [10],
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        # Test with Union type annotation
        result = field.from_polars("frame", 0, df, Union[LazyVideoFrame, None])

        assert isinstance(result, LazyVideoFrame)
        assert result.format == "BGR"

    def test_from_polars_respects_channels_first(self):
        """Test from_polars() passes channels_first to LazyVideoFrame."""
        field = VideoFramePathField(semantic="test", format="RGB", channels_first=True)

        df = pl.DataFrame(
            {
                "frame": ["/path/to/video.mp4"],
                "frame_frame_index": [5],
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        result = field.from_polars("frame", 0, df, LazyVideoFrame)

        assert result.channels_first is True

    def test_coerce_none_returns_none(self):
        """Test coerce() returns None for None input."""
        field = VideoFramePathField(semantic="test", format="RGB")

        result = field.coerce(None, LazyVideoFrame)

        assert result is None

    def test_coerce_lazy_video_frame_returns_same(self):
        """Test coerce() returns LazyVideoFrame unchanged."""
        field = VideoFramePathField(semantic="test", format="RGB")
        lazy_frame = LazyVideoFrame("/path/to/video.mp4", frame_index=42)

        result = field.coerce(lazy_frame, LazyVideoFrame)

        assert result is lazy_frame

    def test_coerce_tuple_to_lazy_video_frame(self):
        """Test coerce() converts (path, frame_index) tuple to LazyVideoFrame."""
        field = VideoFramePathField(semantic="test", format="BGR", channels_first=True)
        value = ("/path/to/video.mp4", 100)

        result = field.coerce(value, LazyVideoFrame)

        assert isinstance(result, LazyVideoFrame)
        assert result.video_path == "/path/to/video.mp4"
        assert result.frame_index == 100
        assert result.format == "BGR"
        assert result.channels_first is True

    def test_coerce_other_value_returns_unchanged(self):
        """Test coerce() returns non-matching values unchanged."""
        field = VideoFramePathField(semantic="test", format="RGB")

        result = field.coerce("some_string", LazyVideoFrame)

        assert result == "some_string"

    def test_should_return_lazy_video_frame_with_direct_type(self):
        """Test _should_return_lazy_video_frame() with direct LazyVideoFrame type."""
        field = VideoFramePathField(semantic="test", format="RGB")

        assert field._should_return_lazy_video_frame(LazyVideoFrame) is True

    def test_should_return_lazy_video_frame_with_union_type(self):
        """Test _should_return_lazy_video_frame() with Union containing LazyVideoFrame."""
        field = VideoFramePathField(semantic="test", format="RGB")

        assert field._should_return_lazy_video_frame(Union[LazyVideoFrame, None]) is True
        assert field._should_return_lazy_video_frame(LazyVideoFrame | None) is True

    def test_should_return_lazy_video_frame_with_non_matching_type(self):
        """Test _should_return_lazy_video_frame() returns False for non-matching types."""
        field = VideoFramePathField(semantic="test", format="RGB")

        assert field._should_return_lazy_video_frame(str) is False
        assert field._should_return_lazy_video_frame(tuple) is False

    def test_from_polars_returns_tuple_when_not_expecting_lazy(self):
        """Test from_polars() returns tuple when target type doesn't include LazyVideoFrame."""
        field = VideoFramePathField(semantic="test", format="RGB")

        df = pl.DataFrame(
            {
                "frame": ["/path/to/video.mp4"],
                "frame_frame_index": [42],
            },
            schema={
                "frame": pl.String(),
                "frame_frame_index": pl.UInt32(),
            },
        )

        # When target type is tuple, should return tuple
        result = field.from_polars("frame", 0, df, tuple)

        assert isinstance(result, tuple)
        assert result == ("/path/to/video.mp4", 42)


class VideoFramePathFieldHelperTest:
    """Tests for video_frame_path_field() helper function."""

    def test_creates_field_with_defaults(self):
        """Test video_frame_path_field() creates field with default values."""
        field = video_frame_path_field()

        assert isinstance(field, VideoFramePathField)
        assert field.semantic == "default"
        assert field.format == "RGB"
        assert field.channels_first is False

    def test_creates_field_with_custom_values(self):
        """Test video_frame_path_field() respects custom parameters."""
        field = video_frame_path_field(
            semantic="primary",
            format="BGR",
            channels_first=True,
        )

        assert field.semantic == "primary"
        assert field.format == "BGR"
        assert field.channels_first is True


class VideoInfoFieldTest:
    """Tests for VideoInfoField."""

    def test_to_polars_schema_returns_struct(self):
        """Test to_polars_schema() returns correct struct schema."""
        field = VideoInfoField(semantic="test")
        schema = field.to_polars_schema("video_info")

        assert "video_info" in schema
        assert isinstance(schema["video_info"], pl.Struct)

    def test_to_polars_with_video_info(self):
        """Test to_polars() correctly serializes VideoInfo."""
        field = VideoInfoField(semantic="test")
        video_info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=1000,
            fps=30.0,
            width=1920,
            height=1080,
            duration=33.33,
            codec="h264",
        )

        result = field.to_polars("video_info", video_info)

        assert "video_info" in result
        struct_data = result["video_info"][0]
        assert struct_data["path"] == "/path/to/video.mp4"
        assert struct_data["total_frames"] == 1000
        assert struct_data["fps"] == pytest.approx(30.0)
        assert struct_data["width"] == 1920
        assert struct_data["height"] == 1080
        assert struct_data["duration"] == pytest.approx(33.33)
        assert struct_data["codec"] == "h264"

    def test_to_polars_with_none_value(self):
        """Test to_polars() handles None value correctly."""
        field = VideoInfoField(semantic="test")

        result = field.to_polars("video_info", None)

        assert result["video_info"][0] is None

    def test_from_polars_reconstructs_video_info(self):
        """Test from_polars() reconstructs VideoInfo correctly."""
        field = VideoInfoField(semantic="test")
        video_info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=500,
            fps=25.0,
            width=1280,
            height=720,
            duration=20.0,
            codec="vp9",
        )

        # Serialize and deserialize
        serialized = field.to_polars("video_info", video_info)
        df = pl.DataFrame(serialized)

        result = field.from_polars("video_info", 0, df, VideoInfo)

        assert isinstance(result, VideoInfo)
        assert result.path == "/path/to/video.mp4"
        assert result.total_frames == 500
        assert result.fps == pytest.approx(25.0)
        assert result.width == 1280
        assert result.height == 720
        assert result.duration == pytest.approx(20.0)
        assert result.codec == "vp9"

    def test_from_polars_returns_none_for_none_struct(self):
        """Test from_polars() returns None when struct is None."""
        field = VideoInfoField(semantic="test")

        serialized = field.to_polars("video_info", None)
        df = pl.DataFrame(serialized)

        result = field.from_polars("video_info", 0, df, VideoInfo)

        assert result is None


class VideoInfoFieldHelperTest:
    """Tests for video_info_field() helper function."""

    def test_creates_field_with_defaults(self):
        """Test video_info_field() creates field with default values."""
        field = video_info_field()

        assert isinstance(field, VideoInfoField)
        assert field.semantic == "default"

    def test_creates_field_with_custom_semantic(self):
        """Test video_info_field() respects custom semantic."""
        field = video_info_field(semantic="metadata")

        assert field.semantic == "metadata"


class VideoFrameCallableFieldTest:
    """Tests for VideoFrameCallableField."""

    def test_to_polars_schema_returns_object_type(self):
        """Test to_polars_schema() returns Object type for callable storage."""
        field = VideoFrameCallableField(semantic="test", format="RGB")
        schema = field.to_polars_schema("frame_loader")

        assert "frame_loader" in schema
        assert schema["frame_loader"] == pl.Object()

    def test_to_polars_stores_callable(self):
        """Test to_polars() stores callable correctly."""
        field = VideoFrameCallableField(semantic="test", format="RGB")

        def loader():
            return np.zeros((100, 100, 3), dtype=np.uint8)

        result = field.to_polars("frame_loader", loader)

        assert "frame_loader" in result
        stored_callable = result["frame_loader"][0]
        assert callable(stored_callable)
        assert stored_callable is loader

    def test_to_polars_stores_none(self):
        """Test to_polars() handles None value."""
        field = VideoFrameCallableField(semantic="test", format="RGB")

        result = field.to_polars("frame_loader", None)

        assert result["frame_loader"][0] is None

    def test_to_polars_raises_error_for_non_callable(self):
        """Test to_polars() raises TypeError for non-callable values."""
        field = VideoFrameCallableField(semantic="test", format="RGB")

        with pytest.raises(TypeError, match="Expected callable"):
            field.to_polars("frame_loader", "not_a_callable")

    def test_from_polars_returns_callable(self):
        """Test from_polars() retrieves callable correctly."""
        field = VideoFrameCallableField(semantic="test", format="RGB")

        def loader():
            return np.ones((50, 50, 3), dtype=np.uint8)

        serialized = field.to_polars("frame_loader", loader)
        df = pl.DataFrame(serialized)

        result = field.from_polars("frame_loader", 0, df, Callable)

        assert callable(result)
        output = result()
        assert output.shape == (50, 50, 3)

    def test_from_polars_returns_none(self):
        """Test from_polars() returns None when stored value is None."""
        field = VideoFrameCallableField(semantic="test", format="RGB")

        serialized = field.to_polars("frame_loader", None)
        df = pl.DataFrame(serialized)

        result = field.from_polars("frame_loader", 0, df, Callable)

        assert result is None


class VideoFrameCallableFieldHelperTest:
    """Tests for video_frame_callable_field() helper function."""

    def test_creates_field_with_defaults(self):
        """Test video_frame_callable_field() creates field with default values."""
        field = video_frame_callable_field()

        assert isinstance(field, VideoFrameCallableField)
        assert field.semantic == "default"
        assert field.format == "RGB"

    def test_creates_field_with_custom_values(self):
        """Test video_frame_callable_field() respects custom parameters."""
        field = video_frame_callable_field(format="BGR", semantic="custom")

        assert field.format == "BGR"
        assert field.semantic == "custom"


class MediaPathFieldTest:
    """Tests for MediaPathField (unified image/video field)."""

    def test_to_polars_schema_returns_correct_columns(self):
        """Test to_polars_schema() returns path and nullable frame_index columns."""
        field = MediaPathField(semantic="test", format="RGB")
        schema = field.to_polars_schema("media")

        assert "media" in schema
        assert "media_frame_index" in schema
        assert schema["media"] == pl.Categorical()
        assert schema["media_frame_index"] == pl.UInt32()

    def test_to_polars_with_lazy_image(self):
        """Test to_polars() correctly serializes LazyImage (frame_index=None)."""
        field = MediaPathField(semantic="test", format="RGB")
        lazy_image = LazyImage("/path/to/image.jpg")

        result = field.to_polars("media", lazy_image)

        assert result["media"][0] == "/path/to/image.jpg"
        assert result["media_frame_index"][0] is None

    def test_to_polars_with_lazy_video_frame(self):
        """Test to_polars() correctly serializes LazyVideoFrame."""
        field = MediaPathField(semantic="test", format="RGB")
        lazy_frame = LazyVideoFrame("/path/to/video.mp4", frame_index=42)

        result = field.to_polars("media", lazy_frame)

        assert result["media"][0] == "/path/to/video.mp4"
        assert result["media_frame_index"][0] == 42

    def test_to_polars_with_path_string(self):
        """Test to_polars() correctly serializes path string as image."""
        field = MediaPathField(semantic="test", format="RGB")

        result = field.to_polars("media", "/path/to/image.png")

        assert result["media"][0] == "/path/to/image.png"
        assert result["media_frame_index"][0] is None

    def test_to_polars_with_path_object(self):
        """Test to_polars() correctly serializes Path object as image."""
        field = MediaPathField(semantic="test", format="RGB")
        path = Path("/path/to/image.png")

        result = field.to_polars("media", path)

        assert result["media"][0] == str(path)
        assert result["media_frame_index"][0] is None

    def test_to_polars_with_none_value(self):
        """Test to_polars() handles None value correctly."""
        field = MediaPathField(semantic="test", format="RGB")

        result = field.to_polars("media", None)

        assert result["media"][0] is None
        assert result["media_frame_index"][0] is None

    def test_to_polars_raises_error_for_invalid_type(self):
        """Test to_polars() raises TypeError for invalid input."""
        field = MediaPathField(semantic="test", format="RGB")

        with pytest.raises(TypeError, match="Expected LazyImage, LazyVideoFrame"):
            field.to_polars("media", 12345)

    def test_from_polars_returns_lazy_image_when_frame_index_is_none(self):
        """Test from_polars() returns LazyImage when frame_index is None."""
        field = MediaPathField(semantic="test", format="RGB", channels_first=False)

        df = pl.DataFrame(
            {
                "media": ["/path/to/image.jpg"],
                "media_frame_index": [None],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result = field.from_polars("media", 0, df, Union[LazyImage, LazyVideoFrame])

        assert isinstance(result, LazyImage)
        assert result.path == "/path/to/image.jpg"
        assert result.format == "RGB"

    def test_from_polars_returns_lazy_video_frame_when_frame_index_is_set(self):
        """Test from_polars() returns LazyVideoFrame when frame_index is set."""
        field = MediaPathField(semantic="test", format="BGR", channels_first=True)

        df = pl.DataFrame(
            {
                "media": ["/path/to/video.mp4"],
                "media_frame_index": [100],
            },
            schema={
                "media": pl.String(),
                "media_frame_index": pl.UInt32(),
            },
        )

        result = field.from_polars("media", 0, df, Union[LazyImage, LazyVideoFrame])

        assert isinstance(result, LazyVideoFrame)
        assert result.video_path == "/path/to/video.mp4"
        assert result.frame_index == 100
        assert result.format == "BGR"
        assert result.channels_first is True

    def test_from_polars_returns_none_when_path_is_none(self):
        """Test from_polars() returns None when path is None."""
        field = MediaPathField(semantic="test", format="RGB")

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

        result = field.from_polars("media", 0, df, Union[LazyImage, LazyVideoFrame])

        assert result is None

    def test_coerce_none_returns_none(self):
        """Test coerce() returns None for None input."""
        field = MediaPathField(semantic="test", format="RGB")

        result = field.coerce(None, Union[LazyImage, LazyVideoFrame])

        assert result is None

    def test_coerce_lazy_image_returns_same(self):
        """Test coerce() returns LazyImage unchanged."""
        field = MediaPathField(semantic="test", format="RGB")
        lazy_image = LazyImage("/path/to/image.jpg")

        result = field.coerce(lazy_image, Union[LazyImage, LazyVideoFrame])

        assert result is lazy_image

    def test_coerce_lazy_video_frame_returns_same(self):
        """Test coerce() returns LazyVideoFrame unchanged."""
        field = MediaPathField(semantic="test", format="RGB")
        lazy_frame = LazyVideoFrame("/path/to/video.mp4", frame_index=42)

        result = field.coerce(lazy_frame, Union[LazyImage, LazyVideoFrame])

        assert result is lazy_frame

    def test_coerce_string_to_lazy_image(self):
        """Test coerce() converts string path to LazyImage."""
        field = MediaPathField(semantic="test", format="BGR", channels_first=True)

        result = field.coerce("/path/to/image.jpg", Union[LazyImage, LazyVideoFrame])

        assert isinstance(result, LazyImage)
        assert result.path == "/path/to/image.jpg"
        assert result.format == "BGR"
        assert result.channels_first is True

    def test_coerce_path_to_lazy_image(self):
        """Test coerce() converts Path object to LazyImage."""
        field = MediaPathField(semantic="test", format="RGB")
        path = Path("/path/to/image.png")

        result = field.coerce(path, Union[LazyImage, LazyVideoFrame])

        assert isinstance(result, LazyImage)
        assert result.path == str(path)

    def test_coerce_tuple_to_lazy_video_frame(self):
        """Test coerce() converts (path, frame_index) tuple to LazyVideoFrame."""
        field = MediaPathField(semantic="test", format="RGB", channels_first=False)
        value = ("/path/to/video.mp4", 50)

        result = field.coerce(value, Union[LazyImage, LazyVideoFrame])

        assert isinstance(result, LazyVideoFrame)
        assert result.video_path == "/path/to/video.mp4"
        assert result.frame_index == 50

    def test_coerce_other_value_returns_unchanged(self):
        """Test coerce() returns non-matching values unchanged."""
        field = MediaPathField(semantic="test", format="RGB")

        result = field.coerce(12345, Union[LazyImage, LazyVideoFrame])

        assert result == 12345


class MediaPathFieldHelperTest:
    """Tests for media_path_field() helper function."""

    def test_creates_field_with_defaults(self):
        """Test media_path_field() creates field with default values."""
        field = media_path_field()

        assert isinstance(field, MediaPathField)
        assert field.semantic == "default"
        assert field.format == "RGB"
        assert field.channels_first is False

    def test_creates_field_with_custom_values(self):
        """Test media_path_field() respects custom parameters."""
        field = media_path_field(
            semantic="primary",
            format="BGR",
            channels_first=True,
        )

        assert field.semantic == "primary"
        assert field.format == "BGR"
        assert field.channels_first is True


class VideoFieldIntegrationTest:
    """Integration tests for video fields with Dataset."""

    @pytest.fixture
    def test_video_exists(self):
        """Skip if test video is not available."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
        return TEST_VIDEO_PATH

    def test_video_frame_path_field_in_sample(self, test_video_exists):
        """Test VideoFramePathField works correctly in a Sample class."""

        class VideoSample(Sample):
            frame: LazyVideoFrame = video_frame_path_field()

        dataset = Dataset(VideoSample)
        dataset.append(VideoSample(frame=LazyVideoFrame(str(test_video_exists), frame_index=0)))

        sample = dataset[0]
        assert isinstance(sample.frame, LazyVideoFrame)
        assert sample.frame.frame_index == 0

        # Actually load the frame data
        frame_data = sample.frame.data
        assert isinstance(frame_data, np.ndarray)
        assert frame_data.ndim == 3

    def test_media_path_field_in_sample_with_video(self, test_video_exists):
        """Test MediaPathField works with video frames in a Sample class."""

        class MediaSample(Sample):
            media: LazyImage | LazyVideoFrame = media_path_field()

        dataset = Dataset(MediaSample)
        dataset.append(MediaSample(media=LazyVideoFrame(str(test_video_exists), frame_index=5)))

        sample = dataset[0]
        assert isinstance(sample.media, LazyVideoFrame)
        assert sample.media.frame_index == 5

    def test_media_path_field_in_sample_with_image(self, tmp_path):
        """Test MediaPathField works with images in a Sample class."""
        from PIL import Image as PILImage

        # Create test image
        img_path = tmp_path / "test.png"
        img_array = np.random.randint(0, 255, (50, 75, 3), dtype=np.uint8)
        PILImage.fromarray(img_array).save(img_path)

        class MediaSample(Sample):
            media: LazyImage | LazyVideoFrame = media_path_field()

        dataset = Dataset(MediaSample)
        dataset.append(MediaSample(media=LazyImage(str(img_path))))

        sample = dataset[0]
        assert isinstance(sample.media, LazyImage)

        # Actually load the image data
        image_data = sample.media.data
        assert isinstance(image_data, np.ndarray)
        assert image_data.shape == (50, 75, 3)

    def test_video_info_field_in_sample(self):
        """Test VideoInfoField works correctly in a Sample class."""

        class VideoMetaSample(Sample):
            info: VideoInfo | None = video_info_field()

        video_info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=1000,
            fps=30.0,
            width=1920,
            height=1080,
            duration=33.33,
            codec="h264",
        )

        dataset = Dataset(VideoMetaSample)
        dataset.append(VideoMetaSample(info=video_info))

        sample = dataset[0]
        assert isinstance(sample.info, VideoInfo)
        assert sample.info.total_frames == 1000
        assert sample.info.fps == pytest.approx(30.0)
        assert sample.info.codec == "h264"

    def test_video_frame_callable_field_in_sample(self):
        """Test VideoFrameCallableField works correctly in a Sample class."""

        class CallableSample(Sample):
            frame_loader: Callable | None = video_frame_callable_field()

        def loader():
            return np.zeros((100, 100, 3), dtype=np.uint8)

        dataset = Dataset(CallableSample)
        dataset.append(CallableSample(frame_loader=loader))

        sample = dataset[0]
        assert callable(sample.frame_loader)
        result = sample.frame_loader()
        assert result.shape == (100, 100, 3)

    def test_mixed_media_dataset(self, test_video_exists, tmp_path):
        """Test dataset with both images and video frames using MediaPathField."""
        from PIL import Image as PILImage

        # Create test image
        img_path = tmp_path / "test.png"
        img_array = np.random.randint(0, 255, (50, 75, 3), dtype=np.uint8)
        PILImage.fromarray(img_array).save(img_path)

        class MediaSample(Sample):
            media: LazyImage | LazyVideoFrame = media_path_field()

        dataset = Dataset(MediaSample)

        # Add image sample
        dataset.append(MediaSample(media=LazyImage(str(img_path))))

        # Add video frame sample
        dataset.append(MediaSample(media=LazyVideoFrame(str(test_video_exists), frame_index=0)))

        # Verify image sample
        img_sample = dataset[0]
        assert isinstance(img_sample.media, LazyImage)

        # Verify video sample
        vid_sample = dataset[1]
        assert isinstance(vid_sample.media, LazyVideoFrame)
        assert vid_sample.media.frame_index == 0

    def test_dataset_serialization_with_video_fields(self, test_video_exists, tmp_path):
        """Test dataset with video fields can be serialized and deserialized."""

        class VideoSample(Sample):
            frame: LazyVideoFrame = video_frame_path_field()

        dataset = Dataset(VideoSample)
        dataset.append(VideoSample(frame=LazyVideoFrame(str(test_video_exists), frame_index=0)))
        dataset.append(VideoSample(frame=LazyVideoFrame(str(test_video_exists), frame_index=10)))

        # Export to parquet
        output_path = tmp_path / "video_dataset.parquet"
        dataset.df.write_parquet(output_path)

        # Read back
        loaded_df = pl.read_parquet(output_path)

        assert len(loaded_df) == 2
        assert loaded_df["frame"][0] == str(test_video_exists)
        assert loaded_df["frame_frame_index"][0] == 0
        assert loaded_df["frame_frame_index"][1] == 10


class MediaInfoFieldTest:
    """Tests for MediaInfoField - unified media metadata field."""

    @pytest.fixture
    def test_video_exists(self):
        """Skip if test video is not available."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
        return TEST_VIDEO_PATH

    def test_media_info_field_to_polars_schema(self):
        """Test to_polars_schema() returns correct struct schema."""
        from getidata.fields.videos import MediaInfoField

        field = MediaInfoField(semantic="test")
        schema = field.to_polars_schema("media_info")

        assert "media_info" in schema
        assert isinstance(schema["media_info"], pl.Struct)

    def test_media_info_field_to_polars_with_image_info(self):
        """Test to_polars() serializes image MediaInfo correctly."""
        from getidata.fields.videos import MediaInfoField
        from getidata.media import MediaInfo

        field = MediaInfoField(semantic="test")
        info = MediaInfo(width=1920, height=1080)

        result = field.to_polars("media_info", info)

        assert "media_info" in result
        struct_val = result["media_info"][0]
        assert struct_val["width"] == 1920
        assert struct_val["height"] == 1080
        assert struct_val["fps"] is None

    def test_media_info_field_to_polars_with_video_info(self):
        """Test to_polars() serializes video frame MediaInfo correctly."""
        from getidata.fields.videos import MediaInfoField
        from getidata.media import MediaInfo

        field = MediaInfoField(semantic="test")
        info = MediaInfo(
            width=1280,
            height=720,
            fps=30.0,
            total_frames=1000,
            duration=33.33,
            codec="h264",
            frame_index=42,
        )

        result = field.to_polars("media_info", info)

        struct_val = result["media_info"][0]
        assert struct_val["width"] == 1280
        assert struct_val["height"] == 720
        assert struct_val["fps"] == pytest.approx(30.0)
        assert struct_val["frame_index"] == 42

    def test_media_info_field_to_polars_with_none(self):
        """Test to_polars() handles None value correctly."""
        from getidata.fields.videos import MediaInfoField

        field = MediaInfoField(semantic="test")
        result = field.to_polars("media_info", None)

        assert result["media_info"][0] is None

    def test_media_info_field_from_polars_image(self):
        """Test from_polars() reconstructs image MediaInfo correctly."""
        from getidata.fields.videos import MediaInfoField
        from getidata.media import MediaInfo

        field = MediaInfoField(semantic="test")
        df = pl.DataFrame(
            {
                "media_info": [
                    {
                        "width": 1920,
                        "height": 1080,
                        "fps": None,
                        "total_frames": None,
                        "duration": None,
                        "codec": None,
                        "frame_index": None,
                    }
                ]
            }
        )

        result = field.from_polars("media_info", 0, df, MediaInfo)

        assert result is not None
        assert result.width == 1920
        assert result.height == 1080
        assert result.is_image is True

    def test_media_info_field_from_polars_video(self):
        """Test from_polars() reconstructs video frame MediaInfo correctly."""
        from getidata.fields.videos import MediaInfoField
        from getidata.media import MediaInfo

        field = MediaInfoField(semantic="test")
        df = pl.DataFrame(
            {
                "media_info": [
                    {
                        "width": 1280,
                        "height": 720,
                        "fps": 30.0,
                        "total_frames": 1000,
                        "duration": 33.33,
                        "codec": "h264",
                        "frame_index": 42,
                    }
                ]
            }
        )

        result = field.from_polars("media_info", 0, df, MediaInfo)

        assert result is not None
        assert result.width == 1280
        assert result.height == 720
        assert result.fps == pytest.approx(30.0)
        assert result.frame_index == 42
        assert result.is_video_frame is True

    def test_media_info_field_from_polars_none(self):
        """Test from_polars() handles None value correctly."""
        from getidata.fields.videos import MediaInfoField
        from getidata.media import MediaInfo

        field = MediaInfoField(semantic="test")
        df = pl.DataFrame({"media_info": [None]}, schema={"media_info": field.dtype})

        result = field.from_polars("media_info", 0, df, MediaInfo)

        assert result is None

    def test_media_info_field_coerce_from_lazy_image(self, tmp_path):
        """Test coerce() converts LazyImage to MediaInfo."""
        from PIL import Image as PILImage

        from getidata.fields.videos import MediaInfoField
        from getidata.media import MediaInfo

        # Create test image
        img_path = tmp_path / "test.png"
        PILImage.new("RGB", (640, 480)).save(img_path)

        field = MediaInfoField(semantic="test")
        lazy_img = LazyImage(str(img_path))

        result = field.coerce(lazy_img, MediaInfo)

        assert isinstance(result, MediaInfo)
        assert result.width == 640
        assert result.height == 480
        assert result.is_image is True

    def test_media_info_field_coerce_from_lazy_video_frame(self, test_video_exists):
        """Test coerce() converts LazyVideoFrame to MediaInfo."""
        from getidata.fields.videos import MediaInfoField
        from getidata.media import MediaInfo

        field = MediaInfoField(semantic="test")
        lazy_frame = LazyVideoFrame(str(test_video_exists), frame_index=5)

        result = field.coerce(lazy_frame, MediaInfo)

        assert isinstance(result, MediaInfo)
        assert result.is_video_frame is True
        assert result.frame_index == 5
        assert result.fps is not None

    def test_media_info_field_coerce_from_dict(self):
        """Test coerce() converts dict to MediaInfo."""
        from getidata.fields.videos import MediaInfoField
        from getidata.media import MediaInfo

        field = MediaInfoField(semantic="test")
        data = {"width": 800, "height": 600}

        result = field.coerce(data, MediaInfo)

        assert isinstance(result, MediaInfo)
        assert result.width == 800
        assert result.height == 600

    def test_media_info_field_coerce_passthrough(self):
        """Test coerce() passes through MediaInfo unchanged."""
        from getidata.fields.videos import MediaInfoField
        from getidata.media import MediaInfo

        field = MediaInfoField(semantic="test")
        original = MediaInfo(width=1920, height=1080)

        result = field.coerce(original, MediaInfo)

        assert result is original

    def test_media_info_field_coerce_none(self):
        """Test coerce() handles None correctly."""
        from getidata.fields.videos import MediaInfoField
        from getidata.media import MediaInfo

        field = MediaInfoField(semantic="test")
        result = field.coerce(None, MediaInfo)

        assert result is None


class MediaInfoFieldInDatasetTest:
    """Integration tests for MediaInfoField in Dataset."""

    @pytest.fixture
    def test_video_exists(self):
        """Skip if test video is not available."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
        return TEST_VIDEO_PATH

    def test_dataset_with_media_info_field(self):
        """Test creating a dataset with MediaInfoField."""
        from getidata.fields.videos import media_info_field
        from getidata.media import MediaInfo

        class SampleWithMediaInfo(Sample):
            media: LazyImage | LazyVideoFrame = media_path_field()
            media_info: MediaInfo = media_info_field()

        dataset = Dataset(SampleWithMediaInfo)

        dataset.append(
            SampleWithMediaInfo(
                media=LazyImage("/path/to/image.jpg"),
                media_info=MediaInfo(width=1920, height=1080),
            )
        )

        sample = dataset[0]
        assert sample.media_info.width == 1920
        assert sample.media_info.height == 1080
        assert sample.media_info.is_image is True

    def test_dataset_with_mixed_media_info(self, test_video_exists, tmp_path):
        """Test dataset with both image and video frame MediaInfo."""
        from PIL import Image as PILImage

        from getidata.fields.videos import media_info_field
        from getidata.media import MediaInfo

        # Create test image
        img_path = tmp_path / "test.png"
        PILImage.new("RGB", (640, 480)).save(img_path)

        class SampleWithMediaInfo(Sample):
            media: LazyImage | LazyVideoFrame = media_path_field()
            media_info: MediaInfo = media_info_field()

        dataset = Dataset(SampleWithMediaInfo)

        # Add image sample
        dataset.append(
            SampleWithMediaInfo(
                media=LazyImage(str(img_path)),
                media_info=MediaInfo(width=640, height=480),
            )
        )

        # Add video frame sample
        dataset.append(
            SampleWithMediaInfo(
                media=LazyVideoFrame(str(test_video_exists), frame_index=0),
                media_info=MediaInfo(
                    width=1280,
                    height=720,
                    fps=30.0,
                    total_frames=100,
                    duration=3.33,
                    frame_index=0,
                ),
            )
        )

        # Verify image sample
        img_sample = dataset[0]
        assert img_sample.media_info.is_image is True
        assert img_sample.media_info.width == 640

        # Verify video sample
        vid_sample = dataset[1]
        assert vid_sample.media_info.is_video_frame is True
        assert vid_sample.media_info.fps == 30.0
        assert vid_sample.media_info.frame_index == 0

    def test_dataset_export_import_with_media_info(self, tmp_path):
        """Test that MediaInfo is preserved through export/import."""
        from getidata.export_import import ExportMode, export_dataset, import_dataset
        from getidata.fields.videos import media_info_field
        from getidata.media import MediaInfo

        class SampleWithMediaInfo(Sample):
            media: LazyImage | LazyVideoFrame = media_path_field()
            media_info: MediaInfo = media_info_field()

        dataset = Dataset(SampleWithMediaInfo)

        # Add samples
        dataset.append(
            SampleWithMediaInfo(
                media=LazyImage("/path/to/image.jpg"),
                media_info=MediaInfo(width=1920, height=1080),
            )
        )

        dataset.append(
            SampleWithMediaInfo(
                media=LazyImage("/path/to/video_frame.jpg"),
                media_info=MediaInfo(
                    width=1280,
                    height=720,
                    fps=30.0,
                    frame_index=42,
                ),
            )
        )

        # Export
        export_path = tmp_path / "exported"
        export_dataset(dataset, export_path, export_media=ExportMode.REFERENCE)

        # Import
        imported = import_dataset(export_path, dtype=SampleWithMediaInfo)

        # Verify
        assert len(imported) == 2
        assert imported[0].media_info.width == 1920
        assert imported[0].media_info.is_image is True

        assert imported[1].media_info.fps == 30.0
        assert imported[1].media_info.frame_index == 42
        assert imported[1].media_info.is_video_frame is True
