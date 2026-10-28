"""
Unit tests for lazy loading functionality.
"""

import os
import tempfile
from typing import Any

import numpy as np
import polars as pl
import pytest
from PIL import Image as PILImage

from getidata.dataset import Dataset, Sample
from getidata.fields import ImageInfo, bbox_field, image_field, image_info_field, image_path_field


def test_lazy_image_loading_basic():
    """Test basic lazy loading of images from file paths."""

    class PathSample(Sample):
        image_path: str = image_path_field()
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)

    class ImageSample(Sample):
        image_path: str = image_path_field()
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test image
        test_image_path = os.path.join(temp_dir, "test_image.png")
        img_array = np.zeros((100, 150, 3), dtype=np.uint8)
        img_array[:, :, 0] = 255  # Red channel
        img_array[50:, :, 1] = 255  # Green channel in bottom half
        img_array[:, 75:, 2] = 255  # Blue channel in right half

        test_img = PILImage.fromarray(img_array)
        test_img.save(test_image_path)

        # Create dataset with paths
        path_dataset = Dataset(PathSample)
        path_dataset.append(
            PathSample(
                image_path=test_image_path,
                bbox=np.array([[20.0, 30.0, 80.0, 70.0]], dtype=np.float32),
            )
        )

        # Convert to image dataset (should trigger lazy loading)
        image_dataset = path_dataset.convert_to_schema(ImageSample)

        # Access sample to trigger loading
        loaded_sample = image_dataset[0]

        assert hasattr(loaded_sample, "image")
        assert hasattr(loaded_sample, "bbox")
        assert isinstance(loaded_sample.image, np.ndarray)
        assert loaded_sample.image.shape == (100, 150, 3)  # height, width, channels

        # Check bbox normalization happened
        # Original: [20.0, 30.0, 80.0, 70.0] for 150x100 image (WxH)
        # Normalized: [20/150, 30/100, 80/150, 70/100] = [0.133, 0.3, 0.533, 0.7]
        expected_normalized = np.array([[20.0 / 150, 30.0 / 100, 80.0 / 150, 70.0 / 100]], dtype=np.float32)
        assert np.allclose(loaded_sample.bbox, expected_normalized, atol=1e-3)


def test_lazy_loading_with_multiple_images():
    """Test lazy loading with multiple image files."""

    class PathSample(Sample):
        image_path: str = image_path_field()
        image_info: ImageInfo = image_info_field()

    class ImageSample(Sample):
        image_path: str = image_path_field()
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        image_info: ImageInfo = image_info_field()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple test images
        image_paths: list[str] = []
        image_infos: list[ImageInfo] = []
        expected_shapes: list[tuple[int, int, int]] = []

        for i in range(3):
            test_image_path = os.path.join(temp_dir, f"test_image_{i}.png")
            width, height = 50 + i * 10, 40 + i * 5  # Varying sizes

            img_array = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            test_img = PILImage.fromarray(img_array)
            test_img.save(test_image_path)

            image_paths.append(test_image_path)
            image_infos.append(ImageInfo(width=width, height=height))
            expected_shapes.append((height, width, 3))

        # Create dataset with paths
        path_dataset = Dataset(PathSample)
        for path, info in zip(image_paths, image_infos):
            path_dataset.append(PathSample(image_path=path, image_info=info))

        assert len(path_dataset.df) == 3

        # Convert to image dataset - this should trigger lazy loading
        image_dataset = path_dataset.convert_to_schema(ImageSample)

        # Verify each image was loaded correctly
        for i in range(3):
            loaded_sample = image_dataset[i]

            # Check that image was actually loaded
            assert hasattr(loaded_sample, "image")
            assert isinstance(loaded_sample.image, np.ndarray)

            # Verify image shape matches expected
            assert loaded_sample.image.shape == expected_shapes[i]

            # Verify metadata is preserved
            assert loaded_sample.image_path == image_paths[i]
            assert loaded_sample.image_info.width == image_infos[i].width
            assert loaded_sample.image_info.height == image_infos[i].height


def test_lazy_loading_nonexistent_file():
    """Test lazy loading behavior with nonexistent files."""

    class PathSample(Sample):
        image_path: str = image_path_field()

    class ImageSample(Sample):
        image_path: str = image_path_field()
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")

    # Create dataset with nonexistent path
    path_dataset = Dataset(PathSample)
    path_dataset.append(PathSample(image_path="/nonexistent/path/to/image.jpg"))

    image_dataset = path_dataset.convert_to_schema(ImageSample)
    # With lazy loading, conversion should succeed
    sample = image_dataset[0]

    # But accessing the lazy image attribute should raise an error
    with pytest.raises(FileNotFoundError):
        _ = sample.image


def test_lazy_loading_with_semantic_fields():
    """Test lazy loading with semantic field variations."""

    class StereoPathSample(Sample):
        left_image_path: str = image_path_field(semantic="left")
        right_image_path: str = image_path_field(semantic="right")

    class StereoImageSample(Sample):
        left_image_path: str = image_path_field(semantic="left")
        right_image_path: str = image_path_field(semantic="right")
        left_image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB", semantic="left")
        right_image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB", semantic="right")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create left and right images with distinct patterns
        left_path = os.path.join(temp_dir, "left.png")
        right_path = os.path.join(temp_dir, "right.png")

        # Left image: predominantly red
        left_array = np.zeros((50, 75, 3), dtype=np.uint8)
        left_array[:, :, 0] = 255  # Red channel
        left_array[:25, :, 1] = 128  # Some green in top half
        left_img = PILImage.fromarray(left_array)
        left_img.save(left_path)

        # Right image: predominantly blue
        right_array = np.zeros((50, 75, 3), dtype=np.uint8)
        right_array[:, :, 2] = 255  # Blue channel
        right_array[25:, :, 0] = 128  # Some red in bottom half
        right_img = PILImage.fromarray(right_array)
        right_img.save(right_path)

        # Create dataset with paths
        path_dataset = Dataset(StereoPathSample)
        path_dataset.append(StereoPathSample(left_image_path=left_path, right_image_path=right_path))

        # Verify semantic fields are handled correctly in schema
        schema = StereoPathSample.infer_schema()
        left_field = schema.attributes["left_image_path"].field
        right_field = schema.attributes["right_image_path"].field

        assert left_field.semantic == "left"
        assert right_field.semantic == "right"

        # Convert to image dataset - this should trigger lazy loading
        image_dataset = path_dataset.convert_to_schema(StereoImageSample)

        # Access sample to trigger lazy loading
        loaded_sample = image_dataset[0]

        # Verify both images were loaded
        assert hasattr(loaded_sample, "left_image")
        assert hasattr(loaded_sample, "right_image")
        assert isinstance(loaded_sample.left_image, np.ndarray)
        assert isinstance(loaded_sample.right_image, np.ndarray)

        # Verify image shapes
        assert loaded_sample.left_image.shape == (50, 75, 3)
        assert loaded_sample.right_image.shape == (50, 75, 3)

        # Verify semantic distinction - left image should be more red, right more blue
        left_red_mean = np.mean(loaded_sample.left_image[:, :, 0])
        left_blue_mean = np.mean(loaded_sample.left_image[:, :, 2])
        right_red_mean = np.mean(loaded_sample.right_image[:, :, 0])
        right_blue_mean = np.mean(loaded_sample.right_image[:, :, 2])

        assert left_red_mean > left_blue_mean  # Left image more red than blue
        assert right_blue_mean > right_red_mean  # Right image more blue than red

        # Verify paths are preserved
        assert loaded_sample.left_image_path == left_path
        assert loaded_sample.right_image_path == right_path


def test_lazy_loading_data_consistency():
    """Test that lazily loaded data maintains consistency."""

    class PathSample(Sample):
        image_path: str = image_path_field()

    class ImageSample(Sample):
        image_path: str = image_path_field()
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test image with known content
        test_image_path = os.path.join(temp_dir, "known_content.png")

        # Create image with specific pattern
        img_array = np.zeros((10, 15, 3), dtype=np.uint8)
        img_array[:5, :, 0] = 100  # Top half red = 100
        img_array[5:, :, 1] = 200  # Bottom half green = 200

        test_img = PILImage.fromarray(img_array)
        test_img.save(test_image_path)

        # Calculate expected sum
        expected_sum = np.sum(img_array)

        # Create dataset
        path_dataset = Dataset(PathSample)
        path_dataset.append(PathSample(image_path=test_image_path))

        image_dataset = path_dataset.convert_to_schema(ImageSample)
        loaded_sample = image_dataset[0]

        # Verify loaded image matches expected content
        if hasattr(loaded_sample, "image"):
            loaded_sum = np.sum(loaded_sample.image)
            assert loaded_sum == expected_sum

            # Verify image shape
            assert loaded_sample.image.shape == (10, 15, 3)
