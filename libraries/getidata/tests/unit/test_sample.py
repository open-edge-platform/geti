"""
Unit tests for Sample class.
"""

from typing import Any

import numpy as np
import numpy.typing as npt
import polars as pl
import pytest

from getidata.dataset import Sample
from getidata.fields import (
    BBoxField,
    ImageField,
    ImageInfo,
    ImageInfoField,
    bbox_field,
    image_field,
    image_info_field,
    numeric_field,
)
from getidata.fields.images import image_path_field
from getidata.schema import Schema


def test_sample_class_definition():
    """Test basic Sample class definition."""

    class TestSample(Sample):
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)
        image_info: ImageInfo = image_info_field()

    # Test class attributes exist
    assert hasattr(TestSample, "image")
    assert hasattr(TestSample, "bbox")
    assert hasattr(TestSample, "image_info")


def test_sample_instantiation():
    """Test Sample instance creation."""

    class TestSample(Sample):
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)
        image_info: ImageInfo = image_info_field()

    sample = TestSample(
        image=np.array([[[255, 0, 0]], [[0, 255, 0]]], dtype=np.uint8),
        bbox=np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32),
        image_info=ImageInfo(width=1, height=2),
    )

    assert isinstance(sample, TestSample)
    assert isinstance(sample.image, np.ndarray)
    assert isinstance(sample.bbox, np.ndarray)
    assert isinstance(sample.image_info, ImageInfo)
    assert sample.image_info.width == 1
    assert sample.image_info.height == 2


def test_sample_schema_inference():
    """Test schema inference from Sample class."""

    class TestSample(Sample):
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)
        image_info: ImageInfo = image_info_field()

    schema = TestSample.infer_schema()

    assert isinstance(schema, Schema)
    assert len(schema.attributes) == 3
    assert "image" in schema.attributes
    assert "bbox" in schema.attributes
    assert "image_info" in schema.attributes

    # Check attribute types
    assert schema.attributes["image"].type == np.ndarray
    assert schema.attributes["bbox"].type == np.ndarray
    assert schema.attributes["image_info"].type == ImageInfo

    assert isinstance(schema.attributes["image"].field, ImageField)
    assert isinstance(schema.attributes["bbox"].field, BBoxField)
    assert isinstance(schema.attributes["image_info"].field, ImageInfoField)


def test_sample_with_semantic_fields():
    """Test Sample with semantic field tags."""

    class StereoSample(Sample):
        left_image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB", semantic="left")
        right_image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="BGR", semantic="right")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=True)

    StereoSample(
        left_image=np.array([[[255, 0, 0]], [[0, 255, 0]]], dtype=np.uint8),
        right_image=np.array([[[0, 0, 255]], [[255, 255, 0]]], dtype=np.uint8),
        bbox=np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32),
    )

    schema = StereoSample.infer_schema()

    # Check semantic tags are preserved
    left_field = schema.attributes["left_image"].field
    right_field = schema.attributes["right_image"].field
    bbox = schema.attributes["bbox"].field

    assert left_field.semantic == "left"
    assert right_field.semantic == "right"
    assert bbox.semantic == "default"

    assert isinstance(left_field, ImageField)
    assert isinstance(right_field, ImageField)
    assert isinstance(bbox, BBoxField)


def test_generic_sample_creation():
    """Test creating generic Sample instances without custom class."""
    sample = Sample(
        image=np.array([[[255, 0, 0]], [[0, 255, 0]]], dtype=np.uint8),
        bbox=np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32),
        image_info=ImageInfo(width=1, height=2),
    )

    assert isinstance(sample, Sample)
    assert hasattr(sample, "image")
    assert hasattr(sample, "bbox")
    assert hasattr(sample, "image_info")
    assert np.allclose(getattr(sample, "bbox"), np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32))


def test_sample_with_complex_fields():
    """Test Sample with various complex field types."""

    class ComplexSample(Sample):
        image_path: str = image_path_field()
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        multiple_bboxes: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)
        image_info: ImageInfo = image_info_field()

    sample = ComplexSample(
        image_path="test_string",
        image=np.array([[[255, 0, 0]], [[0, 255, 0]]], dtype=np.uint8),
        multiple_bboxes=np.array(
            [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8], [0.9, 0.8, 0.7, 0.6]],
            dtype=np.float32,
        ),
        image_info=ImageInfo(width=1, height=2),
    )

    assert sample.multiple_bboxes.shape[0] == 3  # Three bounding boxes
    assert sample.multiple_bboxes.shape[1] == 4  # Four coordinates each


def test_sample_schema_caching():
    """Test that schema inference is cached."""

    class TestSample(Sample):
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)

    # Call infer_schema multiple times
    schema1 = TestSample.infer_schema()
    schema2 = TestSample.infer_schema()

    # Should return the same object due to caching
    assert schema1 is schema2


@pytest.mark.xfail(reason="Sample inheritance schema inference not implemented")
def test_sample_inheritance():
    """Test Sample class inheritance."""

    class BaseSample(Sample):
        image: np.ndarray[Any, Any] = image_field(dtype=pl.UInt8(), format="RGB")
        bbox: np.ndarray[Any, Any] = bbox_field(dtype=pl.Float32(), normalize=False)

    class ExtendedSample(BaseSample):
        image_info: ImageInfo = image_info_field()

    base_schema = BaseSample.infer_schema()
    extended_schema = ExtendedSample.infer_schema()

    assert len(base_schema.attributes) == 2
    assert len(extended_schema.attributes) == 3
    assert "image_info" in extended_schema.attributes
    assert "image_info" not in base_schema.attributes


def test_sample_with_is_list():
    class MySample(Sample):
        confidence: npt.NDArray[np.float32] | None = numeric_field(
            dtype=pl.Float32(), is_list=True, semantic="confidence"
        )

    # Assert that sample can be created without validation errors
    MySample(confidence=np.array([0.8]))
