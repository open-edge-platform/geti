"""
Integration tests for end-to-end workflows.

These tests verify complete workflows similar to those shown in examples.py
"""

import os
import tempfile
from typing import Any, cast

import numpy as np
import polars as pl
import pytest
from PIL import Image as PILImage

from getidata.dataset import AttributeInfo, Dataset, Sample, Schema
from getidata.fields import ImageField, ImageInfo, bbox_field, image_field, image_info_field, image_path_field


def test_basic_sample_workflow():
    """Test the basic sample workflow from Example 1."""

    class BasicSample(Sample):
        bboxes: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32())
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        image_info: ImageInfo = image_info_field()

    dataset = Dataset(BasicSample)

    sample = BasicSample(
        bboxes=np.array([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]),
        image=np.array([[255, 255], [0, 0]]),
        image_info=ImageInfo(width=2, height=2),
    )

    dataset.append(sample)

    # Verify dataset properties
    assert len(dataset.df) == 1
    assert len(dataset.schema.attributes) == 3

    # Verify sample retrieval
    retrieved_sample = dataset[0]
    assert isinstance(retrieved_sample, BasicSample)
    assert np.allclose(retrieved_sample.bboxes, sample.bboxes)
    assert retrieved_sample.image_info.width == 2
    assert retrieved_sample.image_info.height == 2


def test_stereo_camera_workflow():
    """Test the stereo camera workflow from Example 2."""

    class StereoSample(Sample):
        bboxes: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32())
        left_image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB", semantic="left")
        right_image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="BGR", semantic="right")
        left_image_info: ImageInfo = image_info_field("left")
        right_image_info: ImageInfo = image_info_field("right")

    dataset = Dataset(StereoSample)

    sample = StereoSample(
        bboxes=np.array([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]),
        left_image=np.array([[255, 255], [0, 0]]),
        right_image=np.array([[128, 128], [64, 64]]),
        left_image_info=ImageInfo(width=2, height=2),
        right_image_info=ImageInfo(width=2, height=2),
    )

    dataset.append(sample)

    # Verify dataset and semantic fields
    assert len(dataset.df) == 1

    # Check semantic fields were preserved
    schema = StereoSample.infer_schema()
    left_field = schema.attributes["left_image"].field
    right_field = schema.attributes["right_image"].field

    assert isinstance(left_field, ImageField)
    assert isinstance(right_field, ImageField)
    assert left_field.semantic == "left"
    assert right_field.semantic == "right"
    assert left_field.format == "RGB"
    assert right_field.format == "BGR"


def test_dynamic_schema_workflow():
    """Test dynamic schema definition from Example 3."""

    schema = Schema(
        attributes={
            "bboxes": AttributeInfo(
                type=np.ndarray,
                field=bbox_field(dtype=pl.Float32()),
            ),
            "image": AttributeInfo(
                type=np.ndarray,
                field=image_field(dtype=pl.UInt8(), format="RGB"),
            ),
            "image_info": AttributeInfo(type=ImageInfo, field=image_info_field()),
        }
    )

    dataset = Dataset(schema)

    sample = Sample(
        bboxes=np.array([[0.1, 0.2, 0.3, 0.4]]),
        image=np.array([[255, 255], [0, 0]]),
        image_info=ImageInfo(width=2, height=2),
    )

    dataset.append(sample)

    # Verify dynamic schema works
    assert len(dataset.df) == 1
    assert dataset.schema == schema

    retrieved_sample = dataset[0]
    assert isinstance(retrieved_sample, Sample)
    assert np.allclose(getattr(retrieved_sample, "bboxes"), getattr(sample, "bboxes"))


def test_dataset_modification_workflow():
    """Test dataset modification from Example 5."""

    class ModifiableSample(Sample):
        bboxes: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32())
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        image_info: ImageInfo = image_info_field()

    dataset = Dataset(ModifiableSample)

    # Add initial samples
    sample1 = ModifiableSample(
        bboxes=np.array([[0.1, 0.2, 0.3, 0.4]]),
        image=np.array([[255, 255], [0, 0]]),
        image_info=ImageInfo(width=2, height=2),
    )

    sample2 = ModifiableSample(
        bboxes=np.array([[0.5, 0.6, 0.7, 0.8]]),
        image=np.array([[128, 128], [64, 64]]),
        image_info=ImageInfo(width=2, height=2),
    )

    dataset.append(sample1)
    dataset.append(sample2)

    assert len(dataset.df) == 2

    # Modify first sample
    modified_sample = ModifiableSample(
        bboxes=np.array([[0.9, 0.8, 0.7, 0.6]]),
        image=np.array([[200, 200], [100, 100]]),
        image_info=ImageInfo(width=2, height=2),
    )

    dataset[0] = modified_sample

    # Verify modification
    retrieved_sample = dataset[0]
    assert np.allclose(retrieved_sample.bboxes, modified_sample.bboxes)

    # Verify second sample unchanged
    retrieved_sample2 = dataset[1]
    assert np.allclose(retrieved_sample2.bboxes, sample2.bboxes)


def test_schema_conversion_workflow():
    """Test schema conversion workflow from Example 6."""

    class SourceSample(Sample):
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)

    class TargetSample(Sample):
        image: np.ndarray[Any, Any] = image_field(dtype=pl.Float32(), format="BGR")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=True)

    # Create source dataset
    source_dataset = Dataset(SourceSample)
    source_sample = SourceSample(
        image=np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8),
        bbox=np.array([[100.0, 150.0, 200.0, 170.0], [50.0, 25.0, 150.0, 40.0]]),
    )
    source_dataset.append(source_sample)

    # Attempt conversion
    converted_dataset = source_dataset.convert_to_schema(TargetSample)

    # Verify conversion results
    assert len(converted_dataset.df) == 1
    converted_sample = converted_dataset[0]

    # Check that image dtype was converted
    assert converted_sample.image.dtype == np.float32
    assert converted_sample.bbox.dtype == np.float32

    # Check that bbox normalization occurred (requires image dimensions)
    # For a 200x300x3 image (HxWxC), normalized bbox should be in [0,1] range
    assert (converted_sample.bbox >= 0.0).all()
    assert (converted_sample.bbox <= 1.0).all()


def test_lazy_loading_integration():
    """Test lazy loading integration from Example 7."""

    class PathSample(Sample):
        image_path: str = image_path_field()
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)

    class ImageSample(Sample):
        image_path: str = image_path_field()
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test image
        test_image_path = os.path.join(temp_dir, "test_image.png")

        img_array = np.zeros((100, 150, 3), dtype=np.uint8)
        img_array[:, :, 0] = 255  # Red channel
        img_array[50:, :, 1] = 255  # Green channel in bottom half
        img_array[:, 75:, 2] = 255  # Blue channel in right half

        test_img = PILImage.fromarray(img_array)
        test_img.save(test_image_path)

        # Create path dataset
        path_dataset = Dataset(PathSample)
        path_sample = PathSample(
            image_path=test_image_path,
            bbox=np.array([[20.0, 30.0, 80.0, 70.0], [10.0, 40.0, 60.0, 90.0]]),
        )
        path_dataset.append(path_sample)

        # Convert to image dataset
        image_dataset = path_dataset.convert_to_schema(ImageSample)

        # Access sample to trigger lazy loading
        loaded_sample = image_dataset[0]

        # Verify image was loaded
        assert hasattr(loaded_sample, "image")
        assert loaded_sample.image.shape == (100, 150, 3)

        # Verify bbox normalization
        # Original: [[20.0, 30.0, 80.0, 70.0], [10.0, 40.0, 60.0, 90.0]]
        # For 150x100 image (WxH): normalize x by 150, y by 100
        expected_bbox = np.array(
            [
                [20.0 / 150, 30.0 / 100, 80.0 / 150, 70.0 / 100],
                [10.0 / 150, 40.0 / 100, 60.0 / 150, 90.0 / 100],
            ]
        )

        assert np.allclose(loaded_sample.bbox, expected_bbox, atol=1e-3)


def test_performance_with_large_dataset():
    """Test performance with a larger dataset."""

    class PerfSample(Sample):
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)
        image_info: ImageInfo = image_info_field()

    dataset = Dataset(PerfSample)

    # Add multiple samples
    num_samples = 100
    for i in range(num_samples):
        sample = PerfSample(
            image=np.random.randint(0, 255, (10, 15, 3), dtype=np.uint8),
            bbox=np.random.rand(1, 4) * 100,  # Random absolute coordinates
            image_info=ImageInfo(width=15, height=10),
        )
        dataset.append(sample)

    assert len(dataset.df) == num_samples

    # Test random access
    for i in range(0, num_samples, 10):  # Sample every 10th element
        sample = dataset[i]
        assert isinstance(sample, PerfSample)
        assert sample.image.shape == (10, 15, 3)
        assert sample.bbox.shape == (1, 4)


def test_error_handling_workflow():
    """Test error handling in various workflows."""

    class TestSample(Sample):
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)

    dataset = Dataset(TestSample)

    # Test invalid index access
    with pytest.raises(IndexError):
        _ = dataset[0]  # Should fail on empty dataset

    # Test schema mismatch
    class OtherSample(Sample):
        data: np.ndarray[Any, Any] = image_field(dtype=pl.Float32(), format="RGB")

    other_dataset = Dataset(OtherSample)

    # Adding wrong sample type should be caught
    sample = TestSample(
        image=np.random.randint(0, 255, (10, 15, 3), dtype=np.uint8),
        bbox=np.array([[0.1, 0.2, 0.3, 0.4]]),
    )

    with pytest.raises(AttributeError):
        other_dataset.append(cast("OtherSample", sample))  # Wrong type
