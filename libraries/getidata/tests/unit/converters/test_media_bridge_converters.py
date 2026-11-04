# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for converters that bridge between image and media/video field types.

Covers bidirectional conversions:
- ImagePath ↔ MediaPath
- ImageInfo ↔ MediaInfo
- ImagePath → ImageInfo (header-only)
- ImagePath → ImageCallable (lazy loader)
- VideoFrameCallable → ImageCallable
"""

from pathlib import Path

import numpy as np
import polars as pl
import pytest
from PIL import Image as PILImage

from getidata.converters.image_converters import ImagePathToImageCallableConverter, ImagePathToImageInfoConverter
from getidata.converters.media_converters import (
    ImageInfoToMediaInfoConverter,
    ImagePathToMediaPathConverter,
    MediaInfoToImageInfoConverter,
    MediaInfoToVideoInfoConverter,
    MediaPathToImagePathConverter,
    MediaPathToMediaInfoConverter,
    VideoFramePathToMediaPathConverter,
    VideoInfoToMediaInfoConverter,
)
from getidata.converters.video_converters import VideoFrameCallableToImageCallableConverter
from getidata.fields.images import ImageCallableField, ImageInfoField, ImagePathField
from getidata.fields.videos import (
    MediaInfoField,
    MediaPathField,
    VideoFrameCallableField,
    VideoFramePathField,
    VideoInfoField,
)
from getidata.schema import AttributeSpec

# ===== Fixtures =====


@pytest.fixture
def test_image_path(tmp_path):
    """Create a test image file and return its path."""
    img_path = tmp_path / "test_image.png"
    img_array = np.random.randint(0, 255, (48, 64, 3), dtype=np.uint8)
    test_img = PILImage.fromarray(img_array)
    test_img.save(img_path)
    return img_path


@pytest.fixture
def test_image_path_gray(tmp_path):
    """Create a grayscale test image file and return its path."""
    img_path = tmp_path / "test_gray.png"
    img_array = np.random.randint(0, 255, (30, 40), dtype=np.uint8)
    test_img = PILImage.fromarray(img_array, mode="L")
    test_img.save(img_path)
    return img_path


# ===== ImagePathToImageInfoConverter =====


class ImagePathToImageInfoConverterTest:
    """Tests for ImagePathToImageInfoConverter."""

    def test_filter_output_spec_sets_semantic(self):
        """Test that filter_output_spec copies semantic from input."""
        conv = ImagePathToImageInfoConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(semantic="left"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="info",
                field=ImageInfoField(),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_info.field.semantic == "left"

    def test_convert_reads_dimensions(self, test_image_path):
        """Test that convert reads image width/height from file headers."""
        conv = ImagePathToImageInfoConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="info",
                field=ImageInfoField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": [str(test_image_path)]})
        result = conv.convert(df)

        info = result["info"][0]
        assert info["width"] == 64
        assert info["height"] == 48

    def test_convert_grayscale_image(self, test_image_path_gray):
        """Test with a grayscale image."""
        conv = ImagePathToImageInfoConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="info",
                field=ImageInfoField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": [str(test_image_path_gray)]})
        result = conv.convert(df)

        info = result["info"][0]
        assert info["width"] == 40
        assert info["height"] == 30

    def test_convert_none_path(self):
        """Test that None paths raise a ValueError."""
        conv = ImagePathToImageInfoConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="info",
                field=ImageInfoField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": [None]}, schema={"img": pl.String()})
        with pytest.raises(ValueError, match="None path"):
            conv.convert(df)

    def test_convert_invalid_path(self):
        """Test that invalid paths raise a FileNotFoundError."""
        conv = ImagePathToImageInfoConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="info",
                field=ImageInfoField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": ["/nonexistent/path/image.png"]})
        with pytest.raises(FileNotFoundError):
            conv.convert(df)

    def test_convert_multiple_images(self, tmp_path):
        """Test with multiple images of different sizes."""
        # Create two images of different sizes
        img1_path = tmp_path / "img1.png"
        PILImage.fromarray(np.zeros((100, 200, 3), dtype=np.uint8)).save(img1_path)

        img2_path = tmp_path / "img2.png"
        PILImage.fromarray(np.zeros((50, 75, 3), dtype=np.uint8)).save(img2_path)

        conv = ImagePathToImageInfoConverter()
        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="info",
                field=ImageInfoField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": [str(img1_path), str(img2_path)]})
        result = conv.convert(df)

        assert result["info"][0]["width"] == 200
        assert result["info"][0]["height"] == 100
        assert result["info"][1]["width"] == 75
        assert result["info"][1]["height"] == 50


# ===== ImagePathToImageCallableConverter =====


class ImagePathToImageCallableConverterTest:
    """Tests for ImagePathToImageCallableConverter."""

    def test_filter_output_spec_sets_semantic_and_format(self):
        """Test that filter_output_spec copies semantic and format."""
        conv = ImagePathToImageCallableConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(semantic="right", format="BGR"),
            ),
        )
        setattr(
            conv,
            "output_callable",
            AttributeSpec(
                name="loader",
                field=ImageCallableField(),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_callable.field.semantic == "right"
        assert conv.output_callable.field.format == "BGR"

    def test_convert_creates_callable(self, test_image_path):
        """Test that convert creates a callable that loads the image."""
        conv = ImagePathToImageCallableConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(format="RGB"),
            ),
        )
        setattr(
            conv,
            "output_callable",
            AttributeSpec(
                name="loader",
                field=ImageCallableField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": [str(test_image_path)]})
        result = conv.convert(df)

        loader = result["loader"][0]
        assert callable(loader)

        img_data = loader()
        assert isinstance(img_data, np.ndarray)
        assert img_data.shape == (48, 64, 3)
        assert img_data.dtype == np.uint8

    def test_convert_none_path(self):
        """Test that None paths produce None callable."""
        conv = ImagePathToImageCallableConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(),
            ),
        )
        setattr(
            conv,
            "output_callable",
            AttributeSpec(
                name="loader",
                field=ImageCallableField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": [None]}, schema={"img": pl.String()})
        result = conv.convert(df)

        assert result["loader"][0] is None

    def test_convert_multiple_paths(self, tmp_path):
        """Test with multiple image paths."""
        paths = []
        for i, size in enumerate([(20, 30, 3), (40, 50, 3)]):
            p = tmp_path / f"img{i}.png"
            PILImage.fromarray(np.zeros(size, dtype=np.uint8)).save(p)
            paths.append(str(p))

        conv = ImagePathToImageCallableConverter()
        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(format="RGB"),
            ),
        )
        setattr(
            conv,
            "output_callable",
            AttributeSpec(
                name="loader",
                field=ImageCallableField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": paths})
        result = conv.convert(df)

        img0 = result["loader"][0]()
        img1 = result["loader"][1]()
        assert img0.shape == (20, 30, 3)
        assert img1.shape == (40, 50, 3)


# ===== VideoFrameCallableToImageCallableConverter =====


class VideoFrameCallableToImageCallableConverterTest:
    """Tests for VideoFrameCallableToImageCallableConverter."""

    def test_filter_output_spec_sets_semantic_and_format(self):
        """Test that filter_output_spec copies semantic and format."""
        conv = VideoFrameCallableToImageCallableConverter()

        setattr(
            conv,
            "input_callable",
            AttributeSpec(
                name="frame_loader",
                field=VideoFrameCallableField(semantic="cam1", format="BGR"),
            ),
        )
        setattr(
            conv,
            "output_callable",
            AttributeSpec(
                name="img_loader",
                field=ImageCallableField(),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_callable.field.semantic == "cam1"
        assert conv.output_callable.field.format == "BGR"

    def test_convert_passes_callable_through(self):
        """Test that convert passes the callable through directly."""
        test_array = np.random.randint(0, 255, (32, 48, 3), dtype=np.uint8)

        def frame_loader():
            return test_array

        conv = VideoFrameCallableToImageCallableConverter()

        setattr(
            conv,
            "input_callable",
            AttributeSpec(
                name="frame_loader",
                field=VideoFrameCallableField(format="RGB"),
            ),
        )
        setattr(
            conv,
            "output_callable",
            AttributeSpec(
                name="img_loader",
                field=ImageCallableField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"frame_loader": [frame_loader]})
        result = conv.convert(df)

        img_callable = result["img_loader"][0]
        assert callable(img_callable)
        np.testing.assert_array_equal(img_callable(), test_array)

    def test_convert_handles_none(self):
        """Test that None callables are passed through as None."""
        conv = VideoFrameCallableToImageCallableConverter()

        setattr(
            conv,
            "input_callable",
            AttributeSpec(
                name="frame_loader",
                field=VideoFrameCallableField(format="RGB"),
            ),
        )
        setattr(
            conv,
            "output_callable",
            AttributeSpec(
                name="img_loader",
                field=ImageCallableField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"frame_loader": [None]})
        result = conv.convert(df)

        assert result["img_loader"][0] is None

    def test_convert_multiple_callables(self):
        """Test with multiple callables."""
        arrays = [
            np.random.randint(0, 255, (10, 20, 3), dtype=np.uint8),
            np.random.randint(0, 255, (30, 40, 3), dtype=np.uint8),
        ]

        conv = VideoFrameCallableToImageCallableConverter()
        setattr(
            conv,
            "input_callable",
            AttributeSpec(
                name="frame_loader",
                field=VideoFrameCallableField(format="RGB"),
            ),
        )
        setattr(
            conv,
            "output_callable",
            AttributeSpec(
                name="img_loader",
                field=ImageCallableField(),
            ),
        )
        conv.filter_output_spec()

        callables = [lambda a=a: a for a in arrays]
        df = pl.DataFrame({"frame_loader": callables})
        result = conv.convert(df)

        for i, expected in enumerate(arrays):
            np.testing.assert_array_equal(result["img_loader"][i](), expected)


# ===== ImagePathToMediaPathConverter =====


class ImagePathToMediaPathConverterTest:
    """Tests for ImagePathToMediaPathConverter."""

    def test_filter_output_spec_sets_semantic_and_format(self):
        """Test that filter_output_spec copies semantic from input but preserves output format."""
        conv = ImagePathToMediaPathConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(semantic="left", format="BGR"),
            ),
        )
        setattr(
            conv,
            "output_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(format="RGB"),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_media.field.semantic == "left"
        assert conv.output_media.field.format == "RGB"

    def test_convert_creates_categorical_path_and_null_frame_index(self, test_image_path):
        """Test that convert creates a Categorical path and null frame_index."""
        conv = ImagePathToMediaPathConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(),
            ),
        )
        setattr(
            conv,
            "output_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": [str(test_image_path)]})
        result = conv.convert(df)

        # Media path should be Categorical
        assert result["media"].dtype == pl.Categorical
        assert str(result["media"][0]) == str(test_image_path)

        # Frame index should be null
        assert result["media_frame_index"].dtype == pl.UInt32
        assert result["media_frame_index"][0] is None

    def test_convert_multiple_paths(self, tmp_path):
        """Test with multiple image paths."""
        paths = []
        for i in range(3):
            p = tmp_path / f"img{i}.png"
            PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(p)
            paths.append(str(p))

        conv = ImagePathToMediaPathConverter()
        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(),
            ),
        )
        setattr(
            conv,
            "output_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": paths})
        result = conv.convert(df)

        assert len(result) == 3
        for i, expected_path in enumerate(paths):
            assert str(result["media"][i]) == expected_path
            assert result["media_frame_index"][i] is None

    def test_convert_none_path(self):
        """Test that None path is handled."""
        conv = ImagePathToMediaPathConverter()

        setattr(
            conv,
            "input_path",
            AttributeSpec(
                name="img",
                field=ImagePathField(),
            ),
        )
        setattr(
            conv,
            "output_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame({"img": [None]}, schema={"img": pl.String()})
        result = conv.convert(df)

        assert result["media"][0] is None
        assert result["media_frame_index"][0] is None


# ===== ImageInfoToMediaInfoConverter =====


class ImageInfoToMediaInfoConverterTest:
    """Tests for ImageInfoToMediaInfoConverter."""

    def test_filter_output_spec_sets_semantic(self):
        """Test that filter_output_spec copies semantic."""
        conv = ImageInfoToMediaInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="img_info",
                field=ImageInfoField(semantic="left"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_info.field.semantic == "left"

    def test_convert_promotes_image_info(self):
        """Test that convert creates MediaInfo struct with null video fields."""
        conv = ImageInfoToMediaInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="img_info",
                field=ImageInfoField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        conv.filter_output_spec()

        # Create input DataFrame with ImageInfoField struct
        df = pl.DataFrame(
            {
                "img_info": [{"width": 640, "height": 480}],
            }
        ).cast({"img_info": pl.Struct({"width": pl.Int32, "height": pl.Int32})})

        result = conv.convert(df)

        info = result["media_info"][0]
        assert info["width"] == 640
        assert info["height"] == 480
        assert info["fps"] is None
        assert info["total_frames"] is None
        assert info["duration"] is None
        assert info["codec"] is None
        assert info["frame_index"] is None


# ===== MediaPathToImagePathConverter =====


# Path to test video in assets
TEST_VIDEO_PATH = Path(__file__).parent.parent.parent / "assets" / "cvat_dataset" / "test.mp4"


class MediaPathToImagePathConverterTest:
    """Tests for MediaPathToImagePathConverter."""

    def test_filter_output_spec_sets_semantic_and_format(self):
        """Test that filter_output_spec copies semantic from input but preserves output format."""
        conv = MediaPathToImagePathConverter()

        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(semantic="left", format="BGR"),
            ),
        )
        setattr(
            conv,
            "output_path",
            AttributeSpec(
                name="image",
                field=ImagePathField(format="RGB"),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_path.field.semantic == "left"
        assert conv.output_path.field.format == "RGB"

    def test_convert_image_only_data(self, test_image_path):
        """Test that image-only data (null frame_index) converts successfully."""
        conv = MediaPathToImagePathConverter()

        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(),
            ),
        )
        setattr(
            conv,
            "output_path",
            AttributeSpec(
                name="image",
                field=ImagePathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": pl.Series([str(test_image_path)], dtype=pl.Categorical()),
                "media_frame_index": pl.Series([None], dtype=pl.UInt32()),
            }
        )
        result = conv.convert(df)

        assert result["image"].dtype == pl.String
        assert result["image"][0] == str(test_image_path)

    def test_convert_multiple_image_paths(self, tmp_path):
        """Test with multiple image paths, all with null frame_index."""
        paths = []
        for i in range(3):
            p = tmp_path / f"img{i}.png"
            PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(p)
            paths.append(str(p))

        conv = MediaPathToImagePathConverter()
        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(),
            ),
        )
        setattr(
            conv,
            "output_path",
            AttributeSpec(
                name="image",
                field=ImagePathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": pl.Series(paths, dtype=pl.Categorical()),
                "media_frame_index": pl.Series([None] * 3, dtype=pl.UInt32()),
            }
        )
        result = conv.convert(df)

        assert len(result) == 3
        for i, expected_path in enumerate(paths):
            assert result["image"][i] == expected_path

    @pytest.fixture
    def test_video_exists(self):
        """Skip test if test video is not available."""
        if not TEST_VIDEO_PATH.exists():
            pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
        return TEST_VIDEO_PATH

    def test_convert_extracts_video_frame(self, test_video_exists, tmp_path):
        """Test that video frame rows are extracted and saved as images."""
        import shutil

        # Copy video to tmp_path so extracted frames don't pollute the repo
        video_copy = tmp_path / "test.mp4"
        shutil.copy2(test_video_exists, video_copy)

        conv = MediaPathToImagePathConverter()
        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(format="RGB"),
            ),
        )
        setattr(
            conv,
            "output_path",
            AttributeSpec(
                name="image",
                field=ImagePathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": pl.Series([str(video_copy)], dtype=pl.Categorical()),
                "media_frame_index": pl.Series([0], dtype=pl.UInt32()),
            }
        )
        result = conv.convert(df)

        output_path = result["image"][0]
        assert output_path is not None
        assert Path(output_path).exists()
        assert output_path.endswith(".png")

        # Verify the extracted image is valid and loadable
        img = PILImage.open(output_path)
        assert img.size[0] > 0 and img.size[1] > 0

    def test_convert_mixed_images_and_video_frames(self, test_video_exists, tmp_path):
        """Test that mixed image + video frame data is handled correctly."""
        import shutil

        video_copy = tmp_path / "test.mp4"
        shutil.copy2(test_video_exists, video_copy)

        img_path = tmp_path / "standalone.png"
        PILImage.fromarray(np.zeros((20, 30, 3), dtype=np.uint8)).save(img_path)

        conv = MediaPathToImagePathConverter()
        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(format="RGB"),
            ),
        )
        setattr(
            conv,
            "output_path",
            AttributeSpec(
                name="image",
                field=ImagePathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": pl.Series([str(img_path), str(video_copy), str(video_copy)], dtype=pl.Categorical()),
                "media_frame_index": pl.Series([None, 0, 1], dtype=pl.UInt32()),
            }
        )
        result = conv.convert(df)

        # Image row: path passes through unchanged
        assert result["image"][0] == str(img_path)

        # Video frame rows: extracted to new image files
        for i in [1, 2]:
            p = result["image"][i]
            assert p is not None
            assert Path(p).exists()
            assert p.endswith(".png")
            assert p != str(video_copy)

        # Two different frames should produce two different files
        assert result["image"][1] != result["image"][2]

    def test_convert_extraction_is_idempotent(self, test_video_exists, tmp_path):
        """Test that re-extracting the same frame reuses the existing file."""
        import shutil

        video_copy = tmp_path / "test.mp4"
        shutil.copy2(test_video_exists, video_copy)

        conv = MediaPathToImagePathConverter()
        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(format="RGB"),
            ),
        )
        setattr(
            conv,
            "output_path",
            AttributeSpec(
                name="image",
                field=ImagePathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": pl.Series([str(video_copy)], dtype=pl.Categorical()),
                "media_frame_index": pl.Series([0], dtype=pl.UInt32()),
            }
        )
        result1 = conv.convert(df)
        result2 = conv.convert(df)

        # Same path both times
        assert result1["image"][0] == result2["image"][0]

    def test_convert_none_path(self):
        """Test that None paths produce None output."""
        conv = MediaPathToImagePathConverter()
        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(),
            ),
        )
        setattr(
            conv,
            "output_path",
            AttributeSpec(
                name="image",
                field=ImagePathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": pl.Series([None], dtype=pl.Categorical()),
                "media_frame_index": pl.Series([None], dtype=pl.UInt32()),
            }
        )
        result = conv.convert(df)
        assert result["image"][0] is None

    def test_convert_without_frame_index_column(self, test_image_path):
        """Test graceful handling when frame_index column is missing."""
        conv = MediaPathToImagePathConverter()

        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(),
            ),
        )
        setattr(
            conv,
            "output_path",
            AttributeSpec(
                name="image",
                field=ImagePathField(),
            ),
        )
        conv.filter_output_spec()

        # DataFrame without the frame_index column — should still work
        df = pl.DataFrame(
            {
                "media": pl.Series([str(test_image_path)], dtype=pl.Categorical()),
            }
        )
        result = conv.convert(df)
        assert result["image"][0] == str(test_image_path)


# ===== MediaInfoToImageInfoConverter =====


class MediaInfoToImageInfoConverterTest:
    """Tests for MediaInfoToImageInfoConverter."""

    def test_filter_output_spec_sets_semantic(self):
        """Test that filter_output_spec copies semantic from input."""
        conv = MediaInfoToImageInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(semantic="left"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="image_info",
                field=ImageInfoField(),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_info.field.semantic == "left"

    def test_convert_extracts_width_height_from_image_data(self):
        """Test extraction of width/height from MediaInfo that represents an image."""
        conv = MediaInfoToImageInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="image_info",
                field=ImageInfoField(),
            ),
        )
        conv.filter_output_spec()

        media_info_struct = pl.Struct(
            {
                "width": pl.Int32,
                "height": pl.Int32,
                "fps": pl.Float32,
                "total_frames": pl.UInt32,
                "duration": pl.Float32,
                "codec": pl.String,
                "frame_index": pl.UInt32,
            }
        )
        df = pl.DataFrame(
            {
                "media_info": [
                    {
                        "width": 640,
                        "height": 480,
                        "fps": None,
                        "total_frames": None,
                        "duration": None,
                        "codec": None,
                        "frame_index": None,
                    }
                ],
            }
        ).cast({"media_info": media_info_struct})

        result = conv.convert(df)

        info = result["image_info"][0]
        assert info["width"] == 640
        assert info["height"] == 480

    def test_convert_extracts_width_height_from_video_frame_data(self):
        """Test extraction of width/height from MediaInfo that represents a video frame.

        MediaInfoToImageInfoConverter should work for video frames too — width
        and height are valid for both images and video frames.
        """
        conv = MediaInfoToImageInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="image_info",
                field=ImageInfoField(),
            ),
        )
        conv.filter_output_spec()

        media_info_struct = pl.Struct(
            {
                "width": pl.Int32,
                "height": pl.Int32,
                "fps": pl.Float32,
                "total_frames": pl.UInt32,
                "duration": pl.Float32,
                "codec": pl.String,
                "frame_index": pl.UInt32,
            }
        )
        df = pl.DataFrame(
            {
                "media_info": [
                    {
                        "width": 1920,
                        "height": 1080,
                        "fps": 30.0,
                        "total_frames": 1000,
                        "duration": 33.33,
                        "codec": "h264",
                        "frame_index": 42,
                    }
                ],
            }
        ).cast({"media_info": media_info_struct})

        result = conv.convert(df)

        info = result["image_info"][0]
        assert info["width"] == 1920
        assert info["height"] == 1080


# ===== VideoInfoToMediaInfoConverter =====


class VideoInfoToMediaInfoConverterTest:
    """Tests for VideoInfoToMediaInfoConverter."""

    def test_filter_output_spec_sets_semantic(self):
        """Test that filter_output_spec copies semantic from input."""
        conv = VideoInfoToMediaInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="video_info",
                field=VideoInfoField(semantic="cam1"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_info.field.semantic == "cam1"

    def test_convert_promotes_video_info(self):
        """Test that convert creates MediaInfo struct from VideoInfo with correct casts."""
        conv = VideoInfoToMediaInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="video_info",
                field=VideoInfoField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        conv.filter_output_spec()

        video_info_struct = pl.Struct(
            {
                "path": pl.String,
                "total_frames": pl.UInt32,
                "fps": pl.Float64,
                "width": pl.Int32,
                "height": pl.Int32,
                "duration": pl.Float64,
                "codec": pl.String,
            }
        )
        df = pl.DataFrame(
            {
                "video_info": [
                    {
                        "path": "/path/to/video.mp4",
                        "total_frames": 1000,
                        "fps": 29.97,
                        "width": 1920,
                        "height": 1080,
                        "duration": 33.37,
                        "codec": "h264",
                    }
                ],
            }
        ).cast({"video_info": video_info_struct})

        result = conv.convert(df)

        info = result["media_info"][0]
        assert info["width"] == 1920
        assert info["height"] == 1080
        assert info["total_frames"] == 1000
        assert info["codec"] == "h264"
        assert info["frame_index"] is None
        # fps/duration cast from Float64 → Float32, check approximate
        assert abs(info["fps"] - 29.97) < 0.01
        assert abs(info["duration"] - 33.37) < 0.01

    def test_convert_null_codec(self):
        """Test that null codec in VideoInfo is preserved."""
        conv = VideoInfoToMediaInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="video_info",
                field=VideoInfoField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        conv.filter_output_spec()

        video_info_struct = pl.Struct(
            {
                "path": pl.String,
                "total_frames": pl.UInt32,
                "fps": pl.Float64,
                "width": pl.Int32,
                "height": pl.Int32,
                "duration": pl.Float64,
                "codec": pl.String,
            }
        )
        df = pl.DataFrame(
            {
                "video_info": [
                    {
                        "path": "/video.mp4",
                        "total_frames": 100,
                        "fps": 30.0,
                        "width": 640,
                        "height": 480,
                        "duration": 3.33,
                        "codec": None,
                    }
                ],
            }
        ).cast({"video_info": video_info_struct})

        result = conv.convert(df)
        assert result["media_info"][0]["codec"] is None


# ===== MediaInfoToVideoInfoConverter =====


class MediaInfoToVideoInfoConverterTest:
    """Tests for MediaInfoToVideoInfoConverter."""

    def test_filter_output_spec_sets_semantic(self):
        """Test that filter_output_spec copies semantic from input."""
        conv = MediaInfoToVideoInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(semantic="cam2"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="video_info",
                field=VideoInfoField(),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_info.field.semantic == "cam2"

    def test_convert_demotes_media_info(self):
        """Test that convert creates VideoInfo struct from MediaInfo with correct casts."""
        conv = MediaInfoToVideoInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="video_info",
                field=VideoInfoField(),
            ),
        )
        conv.filter_output_spec()

        media_info_struct = pl.Struct(
            {
                "width": pl.Int32,
                "height": pl.Int32,
                "fps": pl.Float32,
                "total_frames": pl.UInt32,
                "duration": pl.Float32,
                "codec": pl.String,
                "frame_index": pl.UInt32,
            }
        )
        df = pl.DataFrame(
            {
                "media_info": [
                    {
                        "width": 1280,
                        "height": 720,
                        "fps": 24.0,
                        "total_frames": 500,
                        "duration": 20.83,
                        "codec": "vp9",
                        "frame_index": 10,
                    }
                ],
            }
        ).cast({"media_info": media_info_struct})

        result = conv.convert(df)

        info = result["video_info"][0]
        assert info["width"] == 1280
        assert info["height"] == 720
        assert info["total_frames"] == 500
        assert info["codec"] == "vp9"
        assert info["path"] is None
        # fps/duration cast from Float32 → Float64
        assert abs(info["fps"] - 24.0) < 0.01
        assert abs(info["duration"] - 20.83) < 0.01

    def test_convert_drops_frame_index(self):
        """Test that frame_index from MediaInfo is dropped (not in VideoInfo)."""
        conv = MediaInfoToVideoInfoConverter()

        setattr(
            conv,
            "input_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="video_info",
                field=VideoInfoField(),
            ),
        )
        conv.filter_output_spec()

        media_info_struct = pl.Struct(
            {
                "width": pl.Int32,
                "height": pl.Int32,
                "fps": pl.Float32,
                "total_frames": pl.UInt32,
                "duration": pl.Float32,
                "codec": pl.String,
                "frame_index": pl.UInt32,
            }
        )
        df = pl.DataFrame(
            {
                "media_info": [
                    {
                        "width": 640,
                        "height": 480,
                        "fps": 30.0,
                        "total_frames": 100,
                        "duration": 3.33,
                        "codec": None,
                        "frame_index": 42,
                    }
                ],
            }
        ).cast({"media_info": media_info_struct})

        result = conv.convert(df)
        info = result["video_info"][0]

        # VideoInfoField struct should not have frame_index
        assert "frame_index" not in info
        # But should have path (filled with null)
        assert info["path"] is None


# ===== VideoFramePathToMediaPathConverter =====


class VideoFramePathToMediaPathConverterTest:
    """Tests for VideoFramePathToMediaPathConverter."""

    def test_filter_output_spec_sets_semantic(self):
        """Test that filter_output_spec copies semantic from input."""
        conv = VideoFramePathToMediaPathConverter()

        setattr(
            conv,
            "input_frame",
            AttributeSpec(
                name="video_frame",
                field=VideoFramePathField(semantic="surveillance"),
            ),
        )
        setattr(
            conv,
            "output_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_media.field.semantic == "surveillance"

    def test_filter_output_spec_preserves_format(self):
        """Test that filter_output_spec preserves the output format."""
        conv = VideoFramePathToMediaPathConverter()

        setattr(
            conv,
            "input_frame",
            AttributeSpec(
                name="video_frame",
                field=VideoFramePathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(format="BGR"),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_media.field.format == "BGR"

    def test_convert_renames_columns(self):
        """Test that convert properly aliases video frame path columns to media path columns."""
        conv = VideoFramePathToMediaPathConverter()

        setattr(
            conv,
            "input_frame",
            AttributeSpec(
                name="video_frame",
                field=VideoFramePathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "video_frame": pl.Series(
                    ["/path/to/video1.mp4", "/path/to/video2.mp4"],
                    dtype=pl.Categorical(),
                ),
                "video_frame_frame_index": pl.Series([0, 10], dtype=pl.UInt32()),
            }
        )

        result = conv.convert(df)

        assert "media" in result.columns
        assert "media_frame_index" in result.columns
        assert result["media"][0] == "/path/to/video1.mp4"
        assert result["media"][1] == "/path/to/video2.mp4"
        assert result["media_frame_index"][0] == 0
        assert result["media_frame_index"][1] == 10

    def test_convert_single_frame(self):
        """Test conversion with a single video frame."""
        conv = VideoFramePathToMediaPathConverter()

        setattr(
            conv,
            "input_frame",
            AttributeSpec(
                name="frame",
                field=VideoFramePathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_media",
            AttributeSpec(
                name="media_path",
                field=MediaPathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "frame": pl.Series(["/video.mp4"], dtype=pl.Categorical()),
                "frame_frame_index": pl.Series([42], dtype=pl.UInt32()),
            }
        )

        result = conv.convert(df)

        assert result["media_path"][0] == "/video.mp4"
        assert result["media_path_frame_index"][0] == 42

    def test_convert_preserves_original_columns(self):
        """Test that convert preserves the original input columns."""
        conv = VideoFramePathToMediaPathConverter()

        setattr(
            conv,
            "input_frame",
            AttributeSpec(
                name="vf",
                field=VideoFramePathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_media",
            AttributeSpec(
                name="mp",
                field=MediaPathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "vf": pl.Series(["/vid.mp4"], dtype=pl.Categorical()),
                "vf_frame_index": pl.Series([5], dtype=pl.UInt32()),
            }
        )

        result = conv.convert(df)

        # Original columns should still be present (with_columns doesn't drop)
        assert "vf" in result.columns
        assert "vf_frame_index" in result.columns
        # New columns should also be present
        assert "mp" in result.columns
        assert "mp_frame_index" in result.columns

    def test_convert_multiple_frames_same_video(self):
        """Test conversion with multiple frames from the same video."""
        conv = VideoFramePathToMediaPathConverter()

        setattr(
            conv,
            "input_frame",
            AttributeSpec(
                name="video_frame",
                field=VideoFramePathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "video_frame": pl.Series(
                    ["/path/to/video.mp4"] * 5,
                    dtype=pl.Categorical(),
                ),
                "video_frame_frame_index": pl.Series([0, 10, 20, 30, 40], dtype=pl.UInt32()),
            }
        )

        result = conv.convert(df)

        assert len(result) == 5
        # All paths should be the same
        for i in range(5):
            assert result["media"][i] == "/path/to/video.mp4"
        # Frame indices should be preserved
        assert result["media_frame_index"].to_list() == [0, 10, 20, 30, 40]


# ===== MediaPathToMediaInfoConverter =====


class MediaPathToMediaInfoConverterTest:
    """Tests for MediaPathToMediaInfoConverter."""

    def test_filter_output_spec_sets_semantic(self):
        """Test that filter_output_spec copies semantic from input."""
        conv = MediaPathToMediaInfoConverter()

        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(semantic="traffic"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="info",
                field=MediaInfoField(),
            ),
        )

        assert conv.filter_output_spec() is True
        assert conv.output_info.field.semantic == "traffic"

    def test_convert_image_path(self, test_image_path):
        """Test that convert extracts image dimensions for image paths (null frame_index)."""
        conv = MediaPathToMediaInfoConverter()

        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": pl.Series([str(test_image_path)], dtype=pl.Categorical()),
                "media_frame_index": pl.Series([None], dtype=pl.UInt32()),
            }
        )

        result = conv.convert(df)

        assert "media_info" in result.columns
        info = result["media_info"][0]
        # test_image_path is 64x48 (from fixture)
        assert info["width"] == 64
        assert info["height"] == 48
        # Image-specific: video fields should be null
        assert info["fps"] is None
        assert info["total_frames"] is None
        assert info["duration"] is None
        assert info["codec"] is None
        assert info["frame_index"] is None

    def test_convert_null_path_returns_null(self):
        """Test that null paths produce null info."""
        conv = MediaPathToMediaInfoConverter()

        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": pl.Series([None], dtype=pl.Categorical()),
                "media_frame_index": pl.Series([None], dtype=pl.UInt32()),
            }
        )

        result = conv.convert(df)

        assert "media_info" in result.columns
        info = result["media_info"][0]
        assert info is None

    def test_convert_nonexistent_image_path_returns_null(self, tmp_path):
        """Test that non-existent image paths produce null info."""
        conv = MediaPathToMediaInfoConverter()

        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        conv.filter_output_spec()

        nonexistent_path = str(tmp_path / "nonexistent.jpg")
        df = pl.DataFrame(
            {
                "media": pl.Series([nonexistent_path], dtype=pl.Categorical()),
                "media_frame_index": pl.Series([None], dtype=pl.UInt32()),
            }
        )

        result = conv.convert(df)

        assert "media_info" in result.columns
        info = result["media_info"][0]
        assert info is None

    def test_convert_multiple_images(self, tmp_path):
        """Test conversion with multiple image paths."""
        conv = MediaPathToMediaInfoConverter()

        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        conv.filter_output_spec()

        # Create two test images with different dimensions
        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"

        img1 = PILImage.fromarray(np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8))
        img2 = PILImage.fromarray(np.random.randint(0, 255, (50, 75, 3), dtype=np.uint8))
        img1.save(img1_path)
        img2.save(img2_path)

        df = pl.DataFrame(
            {
                "media": pl.Series([str(img1_path), str(img2_path)], dtype=pl.Categorical()),
                "media_frame_index": pl.Series([None, None], dtype=pl.UInt32()),
            }
        )

        result = conv.convert(df)

        assert len(result) == 2
        info1 = result["media_info"][0]
        info2 = result["media_info"][1]

        assert info1["width"] == 200
        assert info1["height"] == 100
        assert info2["width"] == 75
        assert info2["height"] == 50

    def test_convert_output_schema_structure(self, test_image_path):
        """Test that the output has the correct MediaInfoField struct schema."""
        conv = MediaPathToMediaInfoConverter()

        setattr(
            conv,
            "input_media",
            AttributeSpec(
                name="media",
                field=MediaPathField(semantic="default"),
            ),
        )
        setattr(
            conv,
            "output_info",
            AttributeSpec(
                name="media_info",
                field=MediaInfoField(),
            ),
        )
        conv.filter_output_spec()

        df = pl.DataFrame(
            {
                "media": pl.Series([str(test_image_path)], dtype=pl.Categorical()),
                "media_frame_index": pl.Series([None], dtype=pl.UInt32()),
            }
        )

        result = conv.convert(df)

        # Verify the struct has all expected fields
        media_info_dtype = result["media_info"].dtype
        assert isinstance(media_info_dtype, pl.Struct)
        field_names = [f.name for f in media_info_dtype.fields]
        assert "width" in field_names
        assert "height" in field_names
        assert "fps" in field_names
        assert "total_frames" in field_names
        assert "duration" in field_names
        assert "codec" in field_names
        assert "frame_index" in field_names


class DirectOnlyAllowsMediaBridgeConversionsTest:
    """Tests that direct_only=True allows media bridge converters.

    Media bridge converters (MediaPath→ImagePath, MediaInfo→ImageInfo, etc.)
    should always be allowed, even with direct_only=True, because they
    represent format-level narrowing/widening of media representations
    rather than semantic cross-field-type transformations.
    """

    def test_direct_only_allows_media_path_to_image_path(self):
        """Test that MediaPathField→ImagePathField works with direct_only=True."""
        from getidata.converters.registry import find_conversion_path
        from getidata.schema import AttributeInfo, Schema

        source_schema = Schema(
            attributes={
                "media": AttributeInfo(
                    type=str,
                    field=MediaPathField(),
                ),
            }
        )
        target_schema = Schema(
            attributes={
                "image": AttributeInfo(
                    type=str,
                    field=ImagePathField(),
                ),
            }
        )

        # Should succeed with direct_only=True since media→image is a media bridge
        path, _ = find_conversion_path(source_schema, target_schema, direct_only=True)
        assert "image" in path.converters

    def test_direct_only_allows_media_info_to_image_info(self):
        """Test that MediaInfoField→ImageInfoField works with direct_only=True."""
        from getidata.converters.registry import find_conversion_path
        from getidata.fields.images import ImageInfo
        from getidata.media import MediaInfo
        from getidata.schema import AttributeInfo, Schema

        source_schema = Schema(
            attributes={
                "info": AttributeInfo(
                    type=MediaInfo,
                    field=MediaInfoField(),
                ),
            }
        )
        target_schema = Schema(
            attributes={
                "info": AttributeInfo(
                    type=ImageInfo,
                    field=ImageInfoField(),
                ),
            }
        )

        path, _ = find_conversion_path(source_schema, target_schema, direct_only=True)
        assert "info" in path.converters

    def test_direct_only_allows_image_path_to_media_path(self):
        """Test that ImagePathField→MediaPathField works with direct_only=True."""
        from getidata.converters.registry import find_conversion_path
        from getidata.schema import AttributeInfo, Schema

        source_schema = Schema(
            attributes={
                "image": AttributeInfo(
                    type=str,
                    field=ImagePathField(),
                ),
            }
        )
        target_schema = Schema(
            attributes={
                "media": AttributeInfo(
                    type=str,
                    field=MediaPathField(),
                ),
            }
        )

        path, _ = find_conversion_path(source_schema, target_schema, direct_only=True)
        assert "media" in path.converters

    def test_direct_only_allows_video_frame_path_to_media_path(self):
        """Test that VideoFramePathField→MediaPathField works with direct_only=True."""
        from getidata.converters.registry import find_conversion_path
        from getidata.schema import AttributeInfo, Schema

        source_schema = Schema(
            attributes={
                "frame": AttributeInfo(
                    type=str,
                    field=VideoFramePathField(),
                ),
            }
        )
        target_schema = Schema(
            attributes={
                "media": AttributeInfo(
                    type=str,
                    field=MediaPathField(),
                ),
            }
        )

        path, _ = find_conversion_path(source_schema, target_schema, direct_only=True)
        assert "media" in path.converters

    def test_direct_only_allows_combined_media_to_image_conversion(self):
        """Test that a schema with both MediaPath and MediaInfo converts to
        ImagePath and ImageInfo with direct_only=True."""
        from getidata.converters.registry import find_conversion_path
        from getidata.fields.images import ImageInfo
        from getidata.media import MediaInfo
        from getidata.schema import AttributeInfo, Schema

        source_schema = Schema(
            attributes={
                "media": AttributeInfo(
                    type=str,
                    field=MediaPathField(),
                ),
                "info": AttributeInfo(
                    type=MediaInfo,
                    field=MediaInfoField(),
                ),
            }
        )
        target_schema = Schema(
            attributes={
                "image": AttributeInfo(
                    type=str,
                    field=ImagePathField(),
                ),
                "image_info": AttributeInfo(
                    type=ImageInfo,
                    field=ImageInfoField(),
                ),
            }
        )

        path, _ = find_conversion_path(source_schema, target_schema, direct_only=True)
        assert "image" in path.converters
        assert "image_info" in path.converters
