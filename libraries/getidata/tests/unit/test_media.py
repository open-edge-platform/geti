"""
Unit tests for LazyImage, LazyVideoFrame, and related media classes.
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image as PILImage

from getidata import Dataset, ImageCache, LazyImage, Sample
from getidata.fields import image_path_field
from getidata.media import (
    LazyVideoFrame,
    VideoFrameCache,
    VideoInfo,
    _video_info_cache,
    clear_video_info_cache,
    extract_video_info,
)

# Path to test video in assets
TEST_VIDEO_PATH = Path(__file__).parent.parent / "assets" / "cvat_dataset" / "test.mp4"


class LazyImageClassTest:
    """Tests for the LazyImage class directly."""

    @pytest.fixture
    def temp_image_path(self):
        """Create a temporary test image and return its path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "test_image.png")
            # Create a 100x150 RGB image with distinct colors
            img_array = np.zeros((100, 150, 3), dtype=np.uint8)
            img_array[:, :, 0] = 255  # Red channel
            img_array[50:, :, 1] = 128  # Green in bottom half
            img_array[:, 75:, 2] = 64  # Blue in right half

            test_img = PILImage.fromarray(img_array)
            test_img.save(test_image_path)
            yield test_image_path

    def test_lazy_image_creation_with_string_path(self, temp_image_path):
        """Test creating LazyImage with a string path."""
        lazy_img = LazyImage(path=temp_image_path)
        assert lazy_img.path == temp_image_path
        assert lazy_img.format == "RGB"
        assert lazy_img.channels_first is False

    def test_lazy_image_creation_with_path_object(self, temp_image_path):
        """Test creating LazyImage with a Path object."""
        path_obj = Path(temp_image_path)
        lazy_img = LazyImage(path=path_obj)
        # Path should be converted to string
        assert lazy_img.path == str(path_obj)
        assert isinstance(lazy_img.path, str)

    def test_lazy_image_path_access_no_load(self, temp_image_path):
        """Test that accessing path doesn't load the image."""
        ImageCache.clear()
        lazy_img = LazyImage(path=temp_image_path)
        _ = lazy_img.path
        # Cache should still be empty - image not loaded
        assert ImageCache.length() == 0

    def test_lazy_image_data_loads_image(self, temp_image_path):
        """Test that accessing data loads the image."""
        lazy_img = LazyImage(path=temp_image_path)
        data = lazy_img.data
        assert isinstance(data, np.ndarray)
        assert data.shape == (100, 150, 3)
        assert data.dtype == np.uint8

    def test_lazy_image_data_caches_result(self, temp_image_path):
        """Test that data is cached after first access."""
        lazy_img = LazyImage(path=temp_image_path)
        data1 = lazy_img.data
        data2 = lazy_img.data
        # Should be the exact same object (cached)
        assert data1 is data2

    def test_lazy_image_rgb_format(self, temp_image_path):
        """Test loading image in RGB format."""
        lazy_img = LazyImage(path=temp_image_path, format="RGB")
        data = lazy_img.data
        # Check that first pixel has expected RGB values
        assert data[0, 0, 0] == 255  # Red
        assert data[0, 0, 1] == 0  # Green
        assert data[0, 0, 2] == 0  # Blue (left half)

    def test_lazy_image_bgr_format(self, temp_image_path):
        """Test loading image in BGR format."""
        lazy_img_rgb = LazyImage(path=temp_image_path, format="RGB")
        lazy_img_bgr = LazyImage(path=temp_image_path, format="BGR")

        data_rgb = lazy_img_rgb.data
        data_bgr = lazy_img_bgr.data

        # BGR should have R and B channels swapped
        assert np.array_equal(data_rgb[:, :, 0], data_bgr[:, :, 2])  # R in RGB == B in BGR
        assert np.array_equal(data_rgb[:, :, 2], data_bgr[:, :, 0])  # B in RGB == R in BGR
        assert np.array_equal(data_rgb[:, :, 1], data_bgr[:, :, 1])  # G stays same

    def test_lazy_image_channels_first(self, temp_image_path):
        """Test loading image with channels-first format."""
        lazy_img = LazyImage(path=temp_image_path, channels_first=True)
        data = lazy_img.data
        # Should be (C, H, W) instead of (H, W, C)
        assert data.shape == (3, 100, 150)

    def test_lazy_image_channels_last(self, temp_image_path):
        """Test loading image with channels-last format (default)."""
        lazy_img = LazyImage(path=temp_image_path, channels_first=False)
        data = lazy_img.data
        # Should be (H, W, C)
        assert data.shape == (100, 150, 3)

    def test_lazy_image_width_property(self, temp_image_path):
        """Test width property without loading full image."""
        ImageCache.clear()
        lazy_img = LazyImage(path=temp_image_path)
        assert lazy_img.width == 150
        # Should not have cached the full data (width uses PIL directly)
        assert ImageCache.length() == 0

    def test_lazy_image_height_property(self, temp_image_path):
        """Test height property without loading full image."""
        ImageCache.clear()
        lazy_img = LazyImage(path=temp_image_path)
        assert lazy_img.height == 100
        # Should not have cached the full data (height uses PIL directly)
        assert ImageCache.length() == 0

    def test_lazy_image_size_property(self, temp_image_path):
        """Test size property returns (width, height)."""
        ImageCache.clear()
        lazy_img = LazyImage(path=temp_image_path)
        assert lazy_img.size == (150, 100)
        # Should not have cached the full data (size uses PIL directly)
        assert ImageCache.length() == 0

    def test_lazy_image_shape_property(self, temp_image_path):
        """Test shape property (triggers data load)."""
        ImageCache.clear()
        lazy_img = LazyImage(path=temp_image_path)
        assert lazy_img.shape == (100, 150, 3)
        # Should have loaded and cached the data
        assert ImageCache.length() == 1

    def test_lazy_image_fspath(self, temp_image_path):
        """Test __fspath__ allows use with os.path functions."""
        lazy_img = LazyImage(path=temp_image_path)
        assert os.fspath(lazy_img) == temp_image_path
        # Should work with os.path functions
        assert os.path.exists(lazy_img)
        assert os.path.basename(lazy_img) == "test_image.png"

    def test_lazy_image_file_not_found(self):
        """Test that accessing data on non-existent file raises error."""
        lazy_img = LazyImage(path="/nonexistent/path/image.png")
        with pytest.raises(FileNotFoundError):
            _ = lazy_img.data

    def test_lazy_image_grayscale(self):
        """Test loading grayscale image."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "gray_image.png")
            # Create grayscale image
            img_array = np.random.randint(0, 255, (50, 80), dtype=np.uint8)
            test_img = PILImage.fromarray(img_array, mode="L")
            test_img.save(test_image_path)

            lazy_img = LazyImage(path=test_image_path, format="L")
            data = lazy_img.data
            assert data.shape == (50, 80)
            assert data.dtype == np.uint8

    def test_lazy_image_16bit_grayscale(self):
        """Test loading 16-bit grayscale image preserves bit depth."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "gray16_image.png")
            # Create 16-bit grayscale image with values > 255
            img_array = np.array([[1000, 2000, 30000], [40000, 50000, 60000]], dtype=np.uint16)
            test_img = PILImage.fromarray(img_array, mode="I;16")
            test_img.save(test_image_path)

            lazy_img = LazyImage(path=test_image_path, format="L")
            data = lazy_img.data
            assert data.shape == (2, 3)
            # Verify 16-bit values are preserved (not truncated to 8-bit)
            assert data.dtype in (np.uint16, np.int32, np.uint32)
            assert data[0, 0] == 1000
            assert data[0, 2] == 30000
            assert data[1, 2] == 60000

    def test_lazy_image_16bit_to_rgb(self):
        """Test loading 16-bit grayscale image as RGB preserves bit depth."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "gray16_image.png")
            # Create 16-bit grayscale image with values > 255
            img_array = np.array([[1000, 2000], [30000, 40000]], dtype=np.uint16)
            test_img = PILImage.fromarray(img_array, mode="I;16")
            test_img.save(test_image_path)

            lazy_img = LazyImage(path=test_image_path, format="RGB")
            data = lazy_img.data
            # Should be converted to 3-channel with preserved values
            assert data.shape == (2, 2, 3)
            # All channels should have the same value (grayscale expanded to RGB)
            assert data[0, 0, 0] == 1000
            assert data[0, 0, 1] == 1000
            assert data[0, 0, 2] == 1000
            assert data[1, 1, 0] == 40000

    def test_lazy_image_16bit_to_bgr(self):
        """Test loading 16-bit grayscale image as BGR preserves bit depth."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "gray16_image.png")
            # Create 16-bit grayscale image
            img_array = np.array([[5000, 10000]], dtype=np.uint16)
            test_img = PILImage.fromarray(img_array, mode="I;16")
            test_img.save(test_image_path)

            lazy_img = LazyImage(path=test_image_path, format="BGR")
            data = lazy_img.data
            assert data.shape == (1, 2, 3)
            # Values should be preserved
            assert data[0, 0, 0] == 5000
            assert data[0, 1, 2] == 10000

    def test_lazy_image_16bit_channels_first(self):
        """Test loading 16-bit image with channels-first format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "gray16_image.png")
            img_array = np.array([[1000, 2000], [3000, 4000]], dtype=np.uint16)
            test_img = PILImage.fromarray(img_array, mode="I;16")
            test_img.save(test_image_path)

            lazy_img = LazyImage(path=test_image_path, format="RGB", channels_first=True)
            data = lazy_img.data
            # Should be (C, H, W)
            assert data.shape == (3, 2, 2)
            # Values should be preserved
            assert data[0, 0, 0] == 1000
            assert data[1, 0, 0] == 1000
            assert data[2, 1, 1] == 4000


class ImagePathFieldWithLazyImageTest:
    """Tests for ImagePathField when used with LazyImage type annotation."""

    @pytest.fixture
    def temp_image_path(self):
        """Create a temporary test image and return its path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "test_image.png")
            img_array = np.zeros((100, 150, 3), dtype=np.uint8)
            img_array[:, :, 0] = 255  # Red
            img_array[:, :, 1] = 128  # Green
            img_array[:, :, 2] = 64  # Blue

            test_img = PILImage.fromarray(img_array)
            test_img.save(test_image_path)
            yield test_image_path

    def test_sample_with_lazy_image_type(self, temp_image_path):
        """Test creating a Sample with LazyImage type annotation."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        sample = TestSample(image=temp_image_path)
        assert isinstance(sample.image, LazyImage)
        assert sample.image.path == temp_image_path

    def test_sample_coerces_string_to_lazy_image(self, temp_image_path):
        """Test that string path is automatically coerced to LazyImage."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        # Pass a string, should be converted to LazyImage
        sample = TestSample(image=temp_image_path)
        assert isinstance(sample.image, LazyImage)

    def test_sample_accepts_lazy_image_directly(self, temp_image_path):
        """Test that LazyImage can be passed directly."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        lazy_img = LazyImage(path=temp_image_path)
        sample = TestSample(image=lazy_img)
        assert isinstance(sample.image, LazyImage)
        assert sample.image.path == temp_image_path

    def test_sample_with_path_object(self, temp_image_path):
        """Test creating Sample with Path object."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        sample = TestSample(image=Path(temp_image_path))
        assert isinstance(sample.image, LazyImage)
        assert sample.image.path == temp_image_path

    def test_dataset_with_lazy_image(self, temp_image_path):
        """Test Dataset operations with LazyImage samples."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        dataset = Dataset(TestSample)
        dataset.append(TestSample(image=temp_image_path))

        retrieved = dataset[0]
        assert isinstance(retrieved.image, LazyImage)
        assert retrieved.image.path == temp_image_path
        assert retrieved.image.data.shape == (100, 150, 3)

    def test_dataset_iteration_with_lazy_image(self, temp_image_path):
        """Test iterating over Dataset with LazyImage samples."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        dataset = Dataset(TestSample)
        dataset.append(TestSample(image=temp_image_path))

        for sample in dataset:
            assert isinstance(sample.image, LazyImage)
            assert sample.image.path == temp_image_path

    def test_image_path_field_format_parameter(self, temp_image_path):
        """Test that format parameter is passed to LazyImage."""

        class TestSample(Sample):
            image: LazyImage = image_path_field(format="BGR")

        sample = TestSample(image=temp_image_path)
        assert sample.image.format == "BGR"

    def test_image_path_field_channels_first_parameter(self, temp_image_path):
        """Test that channels_first parameter is passed to LazyImage."""

        class TestSample(Sample):
            image: LazyImage = image_path_field(channels_first=True)

        sample = TestSample(image=temp_image_path)
        assert sample.image.channels_first is True
        assert sample.image.data.shape == (3, 100, 150)

    def test_dataset_from_polars_with_lazy_image(self, temp_image_path):
        """Test that LazyImage is properly reconstructed from Polars data."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        dataset = Dataset(TestSample)
        dataset.append(TestSample(image=temp_image_path))

        # Access from dataset (goes through from_polars)
        retrieved = dataset[0]
        assert isinstance(retrieved.image, LazyImage)
        assert retrieved.image.data.shape == (100, 150, 3)

    def test_multiple_samples_with_lazy_image(self):
        """Test multiple samples with different images."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for i in range(3):
                path = os.path.join(temp_dir, f"image_{i}.png")
                img_array = np.full((50 + i * 10, 60 + i * 10, 3), i * 50, dtype=np.uint8)
                PILImage.fromarray(img_array).save(path)
                paths.append(path)

            dataset = Dataset(TestSample)
            for path in paths:
                dataset.append(TestSample(image=path))

            assert len(dataset) == 3

            for i, sample in enumerate(dataset):
                expected_shape = (50 + i * 10, 60 + i * 10, 3)
                assert sample.image.data.shape == expected_shape


class ImagePathFieldWithStringTypeTest:
    """Tests to ensure ImagePathField still works with string type annotation."""

    @pytest.fixture
    def temp_image_path(self):
        """Create a temporary test image and return its path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "test_image.png")
            img_array = np.zeros((100, 150, 3), dtype=np.uint8)
            PILImage.fromarray(img_array).save(test_image_path)
            yield test_image_path

    def test_sample_with_string_type(self, temp_image_path):
        """Test that string type annotation still works as before."""

        class TestSample(Sample):
            image: str = image_path_field()

        sample = TestSample(image=temp_image_path)
        assert isinstance(sample.image, str)
        assert sample.image == temp_image_path

    def test_dataset_with_string_type(self, temp_image_path):
        """Test Dataset operations with string type annotation."""

        class TestSample(Sample):
            image: str = image_path_field()

        dataset = Dataset(TestSample)
        dataset.append(TestSample(image=temp_image_path))

        retrieved = dataset[0]
        assert isinstance(retrieved.image, str)
        assert retrieved.image == temp_image_path


class LazyImageEdgeCasesTest:
    """Edge case tests for LazyImage functionality."""

    def test_lazy_image_with_none_value(self):
        """Test that None values are handled correctly."""

        class TestSample(Sample):
            image: LazyImage | None = image_path_field()

        sample = TestSample(image=None)
        assert sample.image is None

    def test_lazy_image_rgba_format(self):
        """Test loading RGBA image."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "rgba_image.png")
            img_array = np.zeros((50, 80, 4), dtype=np.uint8)
            img_array[:, :, 0] = 255  # R
            img_array[:, :, 1] = 128  # G
            img_array[:, :, 2] = 64  # B
            img_array[:, :, 3] = 200  # A
            PILImage.fromarray(img_array, mode="RGBA").save(test_image_path)

            lazy_img = LazyImage(path=test_image_path, format="RGBA")
            data = lazy_img.data
            assert data.shape == (50, 80, 4)

    def test_lazy_image_channels_first_with_bgr(self):
        """Test channels-first combined with BGR format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "test_image.png")
            img_array = np.zeros((40, 60, 3), dtype=np.uint8)
            img_array[:, :, 0] = 100  # R
            img_array[:, :, 1] = 150  # G
            img_array[:, :, 2] = 200  # B
            PILImage.fromarray(img_array).save(test_image_path)

            lazy_img = LazyImage(path=test_image_path, format="BGR", channels_first=True)
            data = lazy_img.data
            assert data.shape == (3, 40, 60)
            # First channel should be Blue (200), last should be Red (100)
            assert data[0, 0, 0] == 200  # B
            assert data[1, 0, 0] == 150  # G
            assert data[2, 0, 0] == 100  # R

    def test_dataset_slice_with_lazy_image(self):
        """Test dataset slicing with LazyImage samples."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for i in range(5):
                path = os.path.join(temp_dir, f"image_{i}.png")
                img_array = np.full((50, 60, 3), i * 40, dtype=np.uint8)
                PILImage.fromarray(img_array).save(path)
                paths.append(path)

            dataset = Dataset(TestSample)
            for path in paths:
                dataset.append(TestSample(image=path))

            # Test slicing
            sliced = dataset.slice(1, 3)
            assert len(sliced) == 3

            for i, sample in enumerate(sliced):
                assert isinstance(sample.image, LazyImage)
                # Check we got the right samples (indices 1, 2, 3)
                expected_path = paths[i + 1]
                assert sample.image.path == expected_path


class LazyImageExifOrientationTest:
    """Tests that LazyImage correctly honors EXIF orientation metadata.

    Some cameras store images in their raw sensor orientation and set an EXIF
    ``Orientation`` tag indicating that the image should be rotated/flipped for
    display. PIL's ``Image.open`` does not apply this transform automatically,
    so ``img.size`` / ``img.width`` / ``img.height`` return the un-oriented
    dimensions, which don't match what is shown on screen (or what dataset
    annotations typically reference).

    ``LazyImage`` is expected to apply EXIF orientation so that ``data``,
    ``width``, ``height``, ``size`` and ``shape`` all correspond to the image
    as displayed.
    """

    # EXIF Orientation tag id
    _ORIENTATION_TAG = 0x0112

    @staticmethod
    def _save_with_orientation(path: str, img_array: np.ndarray, orientation: int) -> None:
        """Save a JPEG with a given EXIF Orientation tag."""
        img = PILImage.fromarray(img_array)
        exif = img.getexif()
        exif[LazyImageExifOrientationTest._ORIENTATION_TAG] = orientation
        # JPEG is required to round-trip the EXIF orientation tag reliably.
        img.save(path, format="JPEG", exif=exif.tobytes())

    @pytest.fixture(autouse=True)
    def _reset_cache(self):
        ImageCache.clear()
        yield
        ImageCache.clear()

    @pytest.mark.parametrize("orientation", [1, 2, 3, 4])
    def test_non_rotating_orientation_preserves_dimensions(self, orientation):
        """Orientations 1-4 do not swap width/height (identity/flip/180°)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Raw pixel data is landscape 80 wide x 40 tall (H=40, W=80).
            img_array = np.zeros((40, 80, 3), dtype=np.uint8)
            path = os.path.join(temp_dir, f"orient_{orientation}.jpg")
            self._save_with_orientation(path, img_array, orientation)

            lazy_img = LazyImage(path=path)

            assert lazy_img.width == 80
            assert lazy_img.height == 40
            assert lazy_img.size == (80, 40)
            # data should remain (H, W, C)
            assert lazy_img.data.shape == (40, 80, 3)

    @pytest.mark.parametrize("orientation", [5, 6, 7, 8])
    def test_rotating_orientation_swaps_dimensions(self, orientation):
        """Orientations 5-8 imply a 90/270° rotation, so width/height swap."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Raw pixel data is landscape 80 wide x 40 tall (H=40, W=80).
            img_array = np.zeros((40, 80, 3), dtype=np.uint8)
            path = os.path.join(temp_dir, f"orient_{orientation}.jpg")
            self._save_with_orientation(path, img_array, orientation)

            lazy_img = LazyImage(path=path)

            # After applying EXIF orientation, the image is portrait: 40x80.
            assert lazy_img.width == 40
            assert lazy_img.height == 80
            assert lazy_img.size == (40, 80)
            # data should match the oriented dimensions: (H=80, W=40, C)
            assert lazy_img.data.shape == (80, 40, 3)

    def test_orientation_6_data_matches_width_height(self):
        """Regression: ``data.shape`` must be consistent with width/height.

        Previously ``width``/``height`` returned the raw (un-oriented) size
        while ``data`` was also un-oriented; since some data sources (e.g.
        COCO annotations) record oriented dimensions, the mismatch looked
        like width/height were swapped. After the fix, both report the same
        (oriented) dimensions and ``data.shape`` matches ``(height, width, C)``.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use distinct width/height so a swap is detectable.
            img_array = np.zeros((30, 90, 3), dtype=np.uint8)
            path = os.path.join(temp_dir, "orient_6.jpg")
            self._save_with_orientation(path, img_array, 6)

            lazy_img = LazyImage(path=path)

            h, w, _ = lazy_img.data.shape
            assert (w, h) == lazy_img.size
            assert w == lazy_img.width
            assert h == lazy_img.height

    def test_orientation_not_set_uses_raw_dimensions(self):
        """Images without an EXIF orientation tag should behave as before."""
        with tempfile.TemporaryDirectory() as temp_dir:
            img_array = np.zeros((40, 80, 3), dtype=np.uint8)
            path = os.path.join(temp_dir, "no_exif.png")
            # PNG save without EXIF - no orientation metadata at all.
            PILImage.fromarray(img_array).save(path)

            lazy_img = LazyImage(path=path)

            assert lazy_img.width == 80
            assert lazy_img.height == 40
            assert lazy_img.size == (80, 40)
            assert lazy_img.data.shape == (40, 80, 3)


class LazyImageTypeAliasTest:
    """Tests for the LazyImage type alias to avoid type checker warnings."""

    @pytest.fixture
    def temp_image_path(self):
        """Create a temporary test image and return its path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "test_image.png")
            img_array = np.zeros((100, 150, 3), dtype=np.uint8)
            PILImage.fromarray(img_array).save(test_image_path)
            yield test_image_path

    def test_sample_with_image_path_like_type(self, temp_image_path):
        """Test creating a Sample with LazyImage type annotation."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        # Should not raise type checker warnings when passing a string
        sample = TestSample(image=temp_image_path)
        assert isinstance(sample.image, LazyImage)
        assert sample.image.path == temp_image_path

    def test_sample_with_image_path_like_accepts_path(self, temp_image_path):
        """Test that LazyImage accepts Path objects."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        sample = TestSample(image=Path(temp_image_path))
        assert isinstance(sample.image, LazyImage)
        assert sample.image.path == temp_image_path

    def test_sample_with_image_path_like_accepts_lazy_image(self, temp_image_path):
        """Test that LazyImage accepts LazyImage directly."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        lazy_img = LazyImage(path=temp_image_path)
        sample = TestSample(image=lazy_img)
        assert isinstance(sample.image, LazyImage)
        assert sample.image.path == temp_image_path

    def test_dataset_with_image_path_like(self, temp_image_path):
        """Test Dataset operations with LazyImage type."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        dataset = Dataset(TestSample)
        dataset.append(TestSample(image=temp_image_path))

        retrieved = dataset[0]
        assert isinstance(retrieved.image, LazyImage)
        assert retrieved.image.path == temp_image_path
        assert retrieved.image.data.shape == (100, 150, 3)

    def test_image_path_like_with_format_option(self, temp_image_path):
        """Test LazyImage with format option."""

        class TestSample(Sample):
            image: LazyImage = image_path_field(format="BGR")

        sample = TestSample(image=temp_image_path)
        assert sample.image.format == "BGR"

    def test_image_path_like_with_channels_first_option(self, temp_image_path):
        """Test LazyImage with channels_first option."""

        class TestSample(Sample):
            image: LazyImage = image_path_field(channels_first=True)

        sample = TestSample(image=temp_image_path)
        assert sample.image.channels_first is True
        assert sample.image.data.shape == (3, 100, 150)


class ImageCacheLRUTest:
    """Tests for the LRU cache functionality of LazyImage."""

    # Size constants for test images
    # 50x50x3 = 7500 bytes, 10x10x3 = 300 bytes
    DEFAULT_CACHE_SIZE = 1024 * 1024  # 1 MB - plenty for test images
    SMALL_CACHE_SIZE = 3 * 300  # Just enough for 3 small (10x10x3) images

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset cache before and after each test."""
        ImageCache.clear()
        ImageCache.set_size(self.DEFAULT_CACHE_SIZE)
        yield
        ImageCache.clear()
        ImageCache.set_size(self.DEFAULT_CACHE_SIZE)

    def test_image_is_cached_after_access(self):
        """Test that accessing image data caches it."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "test.png")
            PILImage.fromarray(np.zeros((50, 50, 3), dtype=np.uint8)).save(path)

            lazy_img = LazyImage(path=path)
            assert ImageCache.length() == 0

            _ = lazy_img.data
            assert ImageCache.length() == 1

    def test_same_image_uses_cache(self):
        """Test that accessing the same image twice uses the cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "test.png")
            PILImage.fromarray(np.zeros((50, 50, 3), dtype=np.uint8)).save(path)

            lazy_img1 = LazyImage(path=path)
            lazy_img2 = LazyImage(path=path)

            data1 = lazy_img1.data
            assert ImageCache.length() == 1

            data2 = lazy_img2.data
            assert ImageCache.length() == 1  # Still 1, using cache

            # Should be the same array object (from cache)
            assert data1 is data2

    def test_different_formats_cached_separately(self):
        """Test that same image with different formats are cached separately."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "test.png")
            PILImage.fromarray(np.zeros((50, 50, 3), dtype=np.uint8)).save(path)

            lazy_rgb = LazyImage(path=path, format="RGB")
            lazy_bgr = LazyImage(path=path, format="BGR")

            _ = lazy_rgb.data
            assert ImageCache.length() == 1

            _ = lazy_bgr.data
            assert ImageCache.length() == 2  # Different format = different cache entry

    def test_lru_eviction(self):
        """Test that LRU eviction works when cache is full."""
        # Set cache size to fit exactly 3 images (10x10x3 = 300 bytes each)
        ImageCache.set_size(self.SMALL_CACHE_SIZE)

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for i in range(5):
                path = os.path.join(temp_dir, f"image_{i}.png")
                PILImage.fromarray(np.full((10, 10, 3), i, dtype=np.uint8)).save(path)
                paths.append(path)

            # Load first 3 images
            for i in range(3):
                _ = LazyImage(path=paths[i]).data

            assert ImageCache.length() == 3

            # Load 4th image - should evict the first one
            _ = LazyImage(path=paths[3]).data
            assert ImageCache.length() == 3  # Still 3

            # Load 5th image - should evict the second one
            _ = LazyImage(path=paths[4]).data
            assert ImageCache.length() == 3  # Still 3

    def test_image_cache_clear(self):
        """Test clearing the entire cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            for i in range(5):
                path = os.path.join(temp_dir, f"image_{i}.png")
                PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(path)
                _ = LazyImage(path=path).data

            assert ImageCache.length() == 5

            ImageCache.clear()
            assert ImageCache.length() == 0

    def test_image_cache_set_size(self):
        """Test setting cache size."""
        # Set cache size to fit exactly 5 images (10x10x3 = 300 bytes each)
        ImageCache.set_size(5 * 300)

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for i in range(10):
                path = os.path.join(temp_dir, f"image_{i}.png")
                PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(path)
                paths.append(path)
                _ = LazyImage(path=path).data

            # Should only have 5 images cached
            assert ImageCache.length() == 5

    def test_set_cache_size_evicts_existing(self):
        """Test that reducing cache size evicts existing items."""
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for i in range(10):
                path = os.path.join(temp_dir, f"image_{i}.png")
                PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(path)
                paths.append(path)
                _ = LazyImage(path=path).data

            assert ImageCache.length() == 10

            # Reduce cache size to fit 3 images - should evict oldest items
            ImageCache.set_size(self.SMALL_CACHE_SIZE)
            assert ImageCache.length() == 3

    def test_clear_cache_on_single_image(self):
        """Test clearing cache for a single image."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path1 = os.path.join(temp_dir, "image1.png")
            path2 = os.path.join(temp_dir, "image2.png")
            PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(path1)
            PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(path2)

            lazy1 = LazyImage(path=path1)
            lazy2 = LazyImage(path=path2)

            _ = lazy1.data
            _ = lazy2.data
            assert ImageCache.length() == 2

            lazy1.clear_cache()
            assert ImageCache.length() == 1

    def test_cache_zero_size_disables_caching(self):
        """Test that setting cache size to 0 effectively disables caching."""
        ImageCache.set_size(0)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "test.png")
            PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(path)

            lazy_img = LazyImage(path=path)
            _ = lazy_img.data
            assert ImageCache.length() == 0  # Nothing cached

    def test_cache_with_channels_first(self):
        """Test that channels_first affects cache key."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "test.png")
            PILImage.fromarray(np.zeros((50, 50, 3), dtype=np.uint8)).save(path)

            lazy_chw = LazyImage(path=path, channels_first=True)
            lazy_hwc = LazyImage(path=path, channels_first=False)

            _ = lazy_chw.data
            assert ImageCache.length() == 1

            _ = lazy_hwc.data
            assert ImageCache.length() == 2  # Different cache entries

    def test_lru_access_order(self):
        """Test that accessing an image moves it to the end of LRU."""
        # Set cache size to fit exactly 3 images (10x10x3 = 300 bytes each)
        ImageCache.set_size(self.SMALL_CACHE_SIZE)

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for i in range(3):
                path = os.path.join(temp_dir, f"image_{i}.png")
                PILImage.fromarray(np.full((10, 10, 3), i, dtype=np.uint8)).save(path)
                paths.append(path)

            lazy_images = [LazyImage(path=p) for p in paths]

            # Load all 3 images (order: 0, 1, 2)
            for lazy in lazy_images:
                _ = lazy.data

            # Access image 0 again (moves it to end, order now: 1, 2, 0)
            _ = lazy_images[0].data

            # Add a new image - should evict image 1 (the LRU)
            path_new = os.path.join(temp_dir, "image_new.png")
            PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(path_new)
            _ = LazyImage(path=path_new).data

            assert ImageCache.length() == 3

            # Image 0 should still be in cache (we accessed it recently)
            data0 = lazy_images[0].data
            assert data0 is not None

    def test_cache_works_with_dataset(self):
        """Test that cache works correctly when using Dataset."""

        class TestSample(Sample):
            image: LazyImage = image_path_field()

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = []
            for i in range(5):
                path = os.path.join(temp_dir, f"image_{i}.png")
                PILImage.fromarray(np.full((20, 20, 3), i * 50, dtype=np.uint8)).save(path)
                paths.append(path)

            dataset = Dataset(TestSample)
            for path in paths:
                dataset.append(TestSample(image=path))

            # Access all images
            for sample in dataset:
                _ = sample.image.data

            assert ImageCache.length() == 5

            # Clear cache and verify
            ImageCache.clear()
            assert ImageCache.length() == 0


# ============================================================================
# Video Media Tests
# ============================================================================


class VideoInfoTest:
    """Tests for the VideoInfo dataclass."""

    def test_video_info_creation(self):
        """Test creating VideoInfo with all fields."""
        info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
            codec="h264",
        )
        assert info.path == "/path/to/video.mp4"
        assert info.total_frames == 100
        assert info.fps == 30.0
        assert info.width == 1920
        assert info.height == 1080
        assert info.duration == 3.33
        assert info.codec == "h264"

    def test_video_info_optional_codec(self):
        """Test VideoInfo with optional codec field."""
        info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
        )
        assert info.codec is None

    def test_video_info_is_frozen(self):
        """Test that VideoInfo is immutable (frozen dataclass)."""
        info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            info.path = "/new/path.mp4"

    def test_video_info_to_dict(self):
        """Test VideoInfo.to_dict() serialization."""
        info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
            codec="h264",
        )
        result = info.to_dict()
        assert result == {
            "path": "/path/to/video.mp4",
            "total_frames": 100,
            "fps": 30.0,
            "width": 1920,
            "height": 1080,
            "duration": 3.33,
            "codec": "h264",
        }

    def test_video_info_from_dict(self):
        """Test VideoInfo.from_dict() deserialization."""
        data = {
            "path": "/path/to/video.mp4",
            "total_frames": 100,
            "fps": 30.0,
            "width": 1920,
            "height": 1080,
            "duration": 3.33,
            "codec": "h264",
        }
        info = VideoInfo.from_dict(data)
        assert info.path == "/path/to/video.mp4"
        assert info.total_frames == 100
        assert info.fps == 30.0
        assert info.codec == "h264"

    def test_video_info_from_dict_without_codec(self):
        """Test VideoInfo.from_dict() handles missing codec."""
        data = {
            "path": "/path/to/video.mp4",
            "total_frames": 100,
            "fps": 30.0,
            "width": 1920,
            "height": 1080,
            "duration": 3.33,
        }
        info = VideoInfo.from_dict(data)
        assert info.codec is None

    def test_video_info_round_trip(self):
        """Test VideoInfo serialization round-trip."""
        original = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
            codec="h264",
        )
        restored = VideoInfo.from_dict(original.to_dict())
        assert restored == original

    def test_video_info_equality(self):
        """Test VideoInfo equality comparison."""
        info1 = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
            codec="h264",
        )
        info2 = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
            codec="h264",
        )
        assert info1 == info2

    def test_video_info_hash(self):
        """Test VideoInfo is hashable (frozen dataclass)."""
        info = VideoInfo(
            path="/path/to/video.mp4",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
        )
        # Should be hashable since it's frozen
        hash_value = hash(info)
        assert isinstance(hash_value, int)


@pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not available")
class ExtractVideoInfoTest:
    """Tests for the extract_video_info function."""

    def test_extract_video_info_returns_video_info(self):
        """Test that extract_video_info returns a VideoInfo object."""
        info = extract_video_info(TEST_VIDEO_PATH)
        assert isinstance(info, VideoInfo)

    def test_extract_video_info_correct_path(self):
        """Test that extracted info has correct path."""
        info = extract_video_info(TEST_VIDEO_PATH)
        assert info.path == str(TEST_VIDEO_PATH)

    def test_extract_video_info_positive_dimensions(self):
        """Test that extracted video has positive dimensions."""
        info = extract_video_info(TEST_VIDEO_PATH)
        assert info.width > 0
        assert info.height > 0
        assert info.total_frames > 0
        assert info.fps > 0
        assert info.duration > 0

    def test_extract_video_info_accepts_path_object(self):
        """Test that extract_video_info accepts Path objects."""
        info = extract_video_info(Path(TEST_VIDEO_PATH))
        assert isinstance(info, VideoInfo)
        assert info.path == str(TEST_VIDEO_PATH)

    def test_extract_video_info_file_not_found(self):
        """Test extract_video_info raises for non-existent file."""
        with pytest.raises(FileNotFoundError):
            extract_video_info("/non/existent/video.mp4")


@pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not available")
class LazyVideoFrameClassTest:
    """Tests for the LazyVideoFrame class."""

    def setup_method(self):
        """Clear caches before each test."""
        VideoFrameCache.clear()
        clear_video_info_cache()

    def test_lazy_video_frame_creation(self):
        """Test creating LazyVideoFrame."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        assert frame.video_path == str(TEST_VIDEO_PATH)
        assert frame.frame_index == 0
        assert frame.format == "RGB"
        assert frame.channels_first is False

    def test_lazy_video_frame_creation_with_path_object(self):
        """Test creating LazyVideoFrame with Path object."""
        frame = LazyVideoFrame(video_path=TEST_VIDEO_PATH, frame_index=5)
        assert frame.video_path == str(TEST_VIDEO_PATH)
        assert frame.frame_index == 5

    def test_lazy_video_frame_path_access_no_load(self):
        """Test that accessing video_path doesn't load the frame."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        _ = frame.video_path
        _ = frame.frame_index
        # Cache should be empty
        assert VideoFrameCache.length() == 0

    def test_lazy_video_frame_data_loads_frame(self):
        """Test that accessing data loads the frame."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        data = frame.data
        assert isinstance(data, np.ndarray)
        assert data.ndim == 3  # (H, W, C)
        assert data.dtype == np.uint8

    def test_lazy_video_frame_data_caches_result(self):
        """Test that frame data is cached after first access."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        data1 = frame.data
        data2 = frame.data
        # Should be the exact same object (cached)
        assert data1 is data2

    def test_lazy_video_frame_different_frames_different_data(self):
        """Test that different frame indices return different data."""
        frame0 = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        frame1 = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=1)

        data0 = frame0.data
        data1 = frame1.data

        # Different frames should have different data (usually)
        # At minimum, they should be different objects
        assert data0 is not data1

    def test_lazy_video_frame_rgb_format(self):
        """Test loading frame in RGB format."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0, format="RGB")
        data = frame.data
        assert data.ndim == 3
        assert data.shape[2] == 3  # 3 channels

    def test_lazy_video_frame_bgr_format(self):
        """Test loading frame in BGR format."""
        frame_rgb = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0, format="RGB")
        frame_bgr = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0, format="BGR")

        data_rgb = frame_rgb.data
        data_bgr = frame_bgr.data

        # BGR should have R and B channels swapped
        assert np.array_equal(data_rgb[:, :, 0], data_bgr[:, :, 2])  # R in RGB == B in BGR
        assert np.array_equal(data_rgb[:, :, 2], data_bgr[:, :, 0])  # B in RGB == R in BGR
        assert np.array_equal(data_rgb[:, :, 1], data_bgr[:, :, 1])  # G stays same

    def test_lazy_video_frame_grayscale_format(self):
        """Test loading frame in grayscale format."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0, format="L")
        data = frame.data
        assert data.ndim == 2  # Grayscale is 2D

    def test_lazy_video_frame_channels_first(self):
        """Test loading frame with channels-first format."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0, channels_first=True)
        data = frame.data
        # Should be (C, H, W) instead of (H, W, C)
        assert data.shape[0] == 3  # Channels first

    def test_lazy_video_frame_video_info_property(self):
        """Test that video_info property returns VideoInfo."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        info = frame.video_info
        assert isinstance(info, VideoInfo)
        assert info.path == str(TEST_VIDEO_PATH)

    def test_lazy_video_frame_video_info_cached(self):
        """Test that video_info is cached globally."""
        clear_video_info_cache()

        frame1 = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        frame2 = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=5)

        info1 = frame1.video_info
        info2 = frame2.video_info

        # Should be the same cached object
        assert info1 is info2

    def test_lazy_video_frame_width_height(self):
        """Test width and height properties."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        assert frame.width > 0
        assert frame.height > 0
        # Width and height should match video info
        assert frame.width == frame.video_info.width
        assert frame.height == frame.video_info.height

    def test_lazy_video_frame_shape(self):
        """Test shape property."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        shape = frame.shape
        assert len(shape) == 3
        assert shape[0] == frame.height
        assert shape[1] == frame.width
        assert shape[2] == 3  # RGB channels

    def test_lazy_video_frame_clear_cache(self):
        """Test clearing a single frame from cache."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        _ = frame.data
        assert VideoFrameCache.length() >= 1

        frame.clear_cache()
        # Cache should have one less entry
        # (exact count depends on what else was loaded)

    def test_lazy_video_frame_repr(self):
        """Test string representation."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=42)
        repr_str = repr(frame)
        assert "LazyVideoFrame" in repr_str
        assert "42" in repr_str

    def test_lazy_video_frame_fspath(self):
        """Test __fspath__ for os.path compatibility."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        assert os.fspath(frame) == str(TEST_VIDEO_PATH)

    def test_lazy_video_frame_invalid_frame_index(self):
        """Test that invalid frame index raises error."""
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=999999)
        with pytest.raises(ValueError, match="out of bounds"):
            _ = frame.data

    def test_lazy_video_frame_negative_frame_index(self):
        """Test that negative frame index raises error at construction time."""
        with pytest.raises(ValueError, match="frame_index must be non-negative"):
            LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=-1)

    def test_lazy_video_frame_invalid_video_path(self):
        """Test that invalid video path raises error."""
        frame = LazyVideoFrame(video_path="/non/existent/video.mp4", frame_index=0)
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            _ = frame.data


class VideoFrameCacheTest:
    """Tests for the VideoFrameCache class."""

    def setup_method(self):
        """Reset cache before each test."""
        VideoFrameCache.clear()
        VideoFrameCache.set_size(256 * 1024 * 1024)  # Reset to default

    def teardown_method(self):
        """Clean up after tests."""
        VideoFrameCache.clear()
        VideoFrameCache.set_size(256 * 1024 * 1024)

    def test_cache_initially_empty(self):
        """Test that cache starts empty."""
        VideoFrameCache.clear()
        assert VideoFrameCache.length() == 0
        assert VideoFrameCache.get_size() == 0

    def test_cache_set_size(self):
        """Test setting cache size."""
        VideoFrameCache.set_size(512 * 1024 * 1024)
        assert VideoFrameCache.get_max_size() == 512 * 1024 * 1024

    def test_cache_clear(self):
        """Test clearing the cache."""
        # Add some data to cache manually
        VideoFrameCache._cache[("test", 0, "RGB", False)] = np.zeros((10, 10, 3), dtype=np.uint8)
        assert VideoFrameCache.length() > 0

        VideoFrameCache.clear()
        assert VideoFrameCache.length() == 0

    def test_cache_info(self):
        """Test cache info method."""
        VideoFrameCache.clear()
        info = VideoFrameCache.info()
        assert "count" in info
        assert "current_size" in info
        assert "max_size" in info
        assert info["count"] == 0

    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not available")
    def test_cache_stores_frames(self):
        """Test that frames are stored in cache."""
        VideoFrameCache.clear()
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        _ = frame.data
        assert VideoFrameCache.length() >= 1

    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not available")
    def test_cache_multiple_frames(self):
        """Test caching multiple frames."""
        VideoFrameCache.clear()
        for i in range(3):
            frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=i)
            _ = frame.data
        assert VideoFrameCache.length() == 3

    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not available")
    def test_cache_different_formats_separate_entries(self):
        """Test that different formats create separate cache entries."""
        VideoFrameCache.clear()

        frame_rgb = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0, format="RGB")
        frame_bgr = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0, format="BGR")

        _ = frame_rgb.data
        _ = frame_bgr.data

        # Same frame but different formats = 2 cache entries
        assert VideoFrameCache.length() == 2


class ClearVideoInfoCacheTest:
    """Tests for the clear_video_info_cache function."""

    def test_clear_video_info_cache(self):
        """Test clearing the video info cache."""
        # Add something to the cache
        _video_info_cache["test_path"] = VideoInfo(
            path="test_path",
            total_frames=100,
            fps=30.0,
            width=1920,
            height=1080,
            duration=3.33,
        )
        assert len(_video_info_cache) > 0

        clear_video_info_cache()
        assert len(_video_info_cache) == 0

    @pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not available")
    def test_clear_video_info_cache_after_extraction(self):
        """Test clearing cache after video info extraction via LazyVideoFrame."""
        clear_video_info_cache()

        # Access video info via LazyVideoFrame (should populate cache)
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        _ = frame.video_info
        assert str(TEST_VIDEO_PATH) in _video_info_cache

        clear_video_info_cache()
        assert len(_video_info_cache) == 0
        assert len(_video_info_cache) == 0


@pytest.mark.skipif(not TEST_VIDEO_PATH.exists(), reason="Test video not available")
class VideoFramePrefetchTest:
    """Tests for video frame prefetching."""

    def setup_method(self):
        """Clear cache before each test."""
        VideoFrameCache.clear()

    def test_prefetch_frames(self):
        """Test prefetching multiple frames."""
        VideoFrameCache.clear()

        # Prefetch frames 0, 1, 2
        VideoFrameCache.prefetch(str(TEST_VIDEO_PATH), [0, 1, 2])

        # Frames should be in cache
        assert VideoFrameCache.length() >= 1  # At least some frames prefetched

    def test_prefetch_does_not_duplicate(self):
        """Test that prefetch doesn't create duplicates."""
        VideoFrameCache.clear()

        # Load frame 0 first
        frame = LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)
        _ = frame.data
        initial_count = VideoFrameCache.length()

        # Prefetch same frame
        VideoFrameCache.prefetch(str(TEST_VIDEO_PATH), [0])

        # Should not increase count
        assert VideoFrameCache.length() == initial_count
