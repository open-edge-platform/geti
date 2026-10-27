# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for MediaInfo class.

Tests cover:
- MediaInfo instantiation and properties
- is_image and is_video_frame properties
- Factory methods: from_lazy_image, from_lazy_video_frame, from_video_info, from_media
- Serialization: to_dict and from_dict
- Edge cases: minimal fields, None values
"""

import tempfile
from pathlib import Path

import pytest

from getidata.media import LazyImage, LazyVideoFrame, MediaInfo, VideoInfo

# Path to test video in assets
TEST_VIDEO_PATH = Path(__file__).parent.parent / "assets" / "cvat_dataset" / "test.mp4"


class MediaInfoInstantiationTest:
    """Tests for MediaInfo basic instantiation."""

    def test_create_image_media_info(self):
        """Test creating MediaInfo for an image with minimal fields."""
        info = MediaInfo(width=1920, height=1080)

        assert info.width == 1920
        assert info.height == 1080
        assert info.is_image is True
        assert info.is_video_frame is False
        assert info.fps is None
        assert info.total_frames is None
        assert info.duration is None
        assert info.codec is None
        assert info.frame_index is None

    def test_create_video_frame_media_info(self):
        """Test creating MediaInfo for a video frame with all fields."""
        info = MediaInfo(
            width=1280,
            height=720,
            fps=30.0,
            total_frames=1000,
            duration=33.33,
            codec="h264",
            frame_index=42,
        )

        assert info.width == 1280
        assert info.height == 720
        assert info.fps == 30.0
        assert info.total_frames == 1000
        assert info.duration == 33.33
        assert info.codec == "h264"
        assert info.frame_index == 42
        assert info.is_image is False
        assert info.is_video_frame is True

    def test_media_info_is_frozen(self):
        """Test that MediaInfo is immutable (frozen dataclass)."""
        info = MediaInfo(width=100, height=100)

        with pytest.raises(AttributeError):
            info.width = 200  # type: ignore


class MediaInfoPropertiesTest:
    """Tests for MediaInfo properties."""

    def test_is_image_true_when_fps_is_none(self):
        """Test is_image returns True when fps is None."""
        info = MediaInfo(width=100, height=100, fps=None)
        assert info.is_image is True
        assert info.is_video_frame is False

    def test_is_video_frame_true_when_fps_is_set(self):
        """Test is_video_frame returns True when fps is set."""
        info = MediaInfo(width=100, height=100, fps=30.0)
        assert info.is_video_frame is True
        assert info.is_image is False

    def test_size_property(self):
        """Test size property returns (width, height) tuple."""
        info = MediaInfo(width=1920, height=1080)
        assert info.size == (1920, 1080)

    def test_size_property_for_video_frame(self):
        """Test size property works for video frames."""
        info = MediaInfo(width=1280, height=720, fps=24.0)
        assert info.size == (1280, 720)


class MediaInfoSerializationTest:
    """Tests for MediaInfo serialization (to_dict/from_dict)."""

    def test_to_dict_image(self):
        """Test to_dict() for image MediaInfo."""
        info = MediaInfo(width=1920, height=1080)
        result = info.to_dict()

        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["fps"] is None
        assert result["total_frames"] is None
        assert result["duration"] is None
        assert result["codec"] is None
        assert result["frame_index"] is None

    def test_to_dict_video_frame(self):
        """Test to_dict() for video frame MediaInfo."""
        info = MediaInfo(
            width=1280,
            height=720,
            fps=30.0,
            total_frames=1000,
            duration=33.33,
            codec="h264",
            frame_index=42,
        )
        result = info.to_dict()

        assert result["width"] == 1280
        assert result["height"] == 720
        assert result["fps"] == 30.0
        assert result["total_frames"] == 1000
        assert result["duration"] == 33.33
        assert result["codec"] == "h264"
        assert result["frame_index"] == 42

    def test_from_dict_image(self):
        """Test from_dict() for image MediaInfo."""
        data = {"width": 640, "height": 480}
        info = MediaInfo.from_dict(data)

        assert info.width == 640
        assert info.height == 480
        assert info.is_image is True

    def test_from_dict_video_frame(self):
        """Test from_dict() for video frame MediaInfo."""
        data = {
            "width": 1280,
            "height": 720,
            "fps": 24.0,
            "total_frames": 500,
            "duration": 20.83,
            "codec": "vp9",
            "frame_index": 100,
        }
        info = MediaInfo.from_dict(data)

        assert info.width == 1280
        assert info.height == 720
        assert info.fps == 24.0
        assert info.frame_index == 100
        assert info.is_video_frame is True

    def test_round_trip_serialization(self):
        """Test to_dict/from_dict round-trip preserves all data."""
        original = MediaInfo(
            width=1920,
            height=1080,
            fps=60.0,
            total_frames=3600,
            duration=60.0,
            codec="h265",
            frame_index=1800,
        )

        restored = MediaInfo.from_dict(original.to_dict())

        assert restored.width == original.width
        assert restored.height == original.height
        assert restored.fps == original.fps
        assert restored.total_frames == original.total_frames
        assert restored.duration == original.duration
        assert restored.codec == original.codec
        assert restored.frame_index == original.frame_index


class MediaInfoFactoryMethodsTest:
    """Tests for MediaInfo factory methods."""

    def test_from_lazy_image_with_real_file(self):
        """Test from_lazy_image() with a real image file."""
        from PIL import Image as PILImage

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test image
            image_path = Path(tmpdir) / "test_image.png"
            test_img = PILImage.new("RGB", (320, 240), color=(100, 150, 200))
            test_img.save(image_path)

            lazy_img = LazyImage(str(image_path))
            info = MediaInfo.from_lazy_image(lazy_img)

            assert info.width == 320
            assert info.height == 240
            assert info.is_image is True
            assert info.fps is None

    def test_from_lazy_video_frame_with_real_file(self):
        """Test from_lazy_video_frame() with a real video file."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")

        lazy_frame = LazyVideoFrame(str(TEST_VIDEO_PATH), frame_index=0)
        info = MediaInfo.from_lazy_video_frame(lazy_frame)

        assert info.width > 0
        assert info.height > 0
        assert info.fps is not None
        assert info.fps > 0
        assert info.total_frames is not None
        assert info.frame_index == 0
        assert info.is_video_frame is True

    def test_from_video_info(self):
        """Test from_video_info() factory method."""
        video_info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=1000,
            fps=30.0,
            width=1920,
            height=1080,
            duration=33.33,
            codec="h264",
        )

        info = MediaInfo.from_video_info(video_info)

        assert info.width == 1920
        assert info.height == 1080
        assert info.fps == 30.0
        assert info.total_frames == 1000
        assert info.duration == 33.33
        assert info.codec == "h264"
        assert info.frame_index is None
        assert info.is_video_frame is True

    def test_from_video_info_with_frame_index(self):
        """Test from_video_info() with explicit frame_index."""
        video_info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=1000,
            fps=30.0,
            width=1920,
            height=1080,
            duration=33.33,
            codec="h264",
        )

        info = MediaInfo.from_video_info(video_info, frame_index=500)

        assert info.frame_index == 500

    def test_from_media_with_lazy_image(self):
        """Test from_media() with LazyImage."""
        from PIL import Image as PILImage

        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "test.jpg"
            test_img = PILImage.new("RGB", (640, 480))
            test_img.save(image_path)

            lazy_img = LazyImage(str(image_path))
            info = MediaInfo.from_media(lazy_img)

            assert info.width == 640
            assert info.height == 480
            assert info.is_image is True

    def test_from_media_with_lazy_video_frame(self):
        """Test from_media() with LazyVideoFrame."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")

        lazy_frame = LazyVideoFrame(str(TEST_VIDEO_PATH), frame_index=5)
        info = MediaInfo.from_media(lazy_frame)

        assert info.is_video_frame is True
        assert info.frame_index == 5

    def test_from_media_raises_for_invalid_type(self):
        """Test from_media() raises TypeError for invalid input."""
        with pytest.raises(TypeError, match="Expected LazyImage or LazyVideoFrame"):
            MediaInfo.from_media("invalid_string")  # type: ignore

        with pytest.raises(TypeError, match="Expected LazyImage or LazyVideoFrame"):
            MediaInfo.from_media(123)  # type: ignore


class MediaInfoEdgeCasesTest:
    """Tests for MediaInfo edge cases."""

    def test_minimal_media_info(self):
        """Test MediaInfo with only required fields."""
        info = MediaInfo(width=1, height=1)
        assert info.width == 1
        assert info.height == 1
        assert info.is_image is True

    def test_large_dimensions(self):
        """Test MediaInfo with very large dimensions."""
        info = MediaInfo(width=7680, height=4320)  # 8K resolution
        assert info.width == 7680
        assert info.height == 4320
        assert info.size == (7680, 4320)

    def test_high_fps_video(self):
        """Test MediaInfo with high frame rate video."""
        info = MediaInfo(width=1920, height=1080, fps=240.0, total_frames=24000, duration=100.0)
        assert info.fps == 240.0
        assert info.is_video_frame is True

    def test_zero_frame_index(self):
        """Test MediaInfo with frame_index=0 (first frame)."""
        info = MediaInfo(width=1920, height=1080, fps=30.0, frame_index=0)
        assert info.frame_index == 0
        assert info.is_video_frame is True

    def test_explicit_none_fps(self):
        """Test MediaInfo with explicitly set fps=None."""
        info = MediaInfo(width=100, height=100, fps=None)
        assert info.fps is None
        assert info.is_image is True

    def test_codec_none_for_unknown(self):
        """Test MediaInfo with unknown codec (None)."""
        info = MediaInfo(width=1920, height=1080, fps=30.0, codec=None)
        assert info.codec is None
        assert info.is_video_frame is True
