# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for VOC sample classes.
"""

import numpy as np

from getidata.data_formats.voc.constants import VOC_LABELS
from getidata.data_formats.voc.sample import VocCategories, VocSample
from getidata.fields import ImageInfo, Subset


def test_voc_sample_create_with_all_fields():
    """Test creating a sample with all fields populated."""
    bboxes = np.array([[100.0, 100.0, 200.0, 200.0]], dtype=np.float32)
    labels = np.array([1], dtype=np.uint32)
    difficult = np.array([False])
    truncated = np.array([True])
    occluded = np.array([False])
    pose = np.array(["Frontal"], dtype=object)

    sample = VocSample(
        image="/path/to/image.jpg",
        image_info=ImageInfo(height=480, width=640),
        bboxes=bboxes,
        labels=labels,
        difficult=difficult,
        truncated=truncated,
        occluded=occluded,
        pose=pose,
        subset=Subset.TRAINING,
    )

    assert sample.image.path == "/path/to/image.jpg"
    assert sample.image_info.height == 480
    assert sample.image_info.width == 640
    assert sample.subset == Subset.TRAINING
    np.testing.assert_array_equal(sample.bboxes, bboxes)
    np.testing.assert_array_equal(sample.labels, labels)
    np.testing.assert_array_equal(sample.difficult, difficult)
    np.testing.assert_array_equal(sample.truncated, truncated)
    np.testing.assert_array_equal(sample.occluded, occluded)
    np.testing.assert_array_equal(sample.pose, pose)


def test_voc_sample_create_with_minimal_fields():
    """Test creating a sample with only required fields."""
    sample = VocSample(
        image="/path/to/image.jpg",
        image_info=ImageInfo(height=480, width=640),
        bboxes=None,
        labels=None,
        difficult=None,
        truncated=None,
        occluded=None,
        pose=None,
        subset=Subset.UNASSIGNED,
    )

    assert sample.image.path == "/path/to/image.jpg"
    assert sample.bboxes is None
    assert sample.labels is None


def test_voc_sample_schema_has_required_attributes():
    """Test that VocSample schema has all required attributes."""
    schema = VocSample.infer_schema()
    expected_attrs = [
        "image",
        "image_info",
        "bboxes",
        "labels",
        "difficult",
        "truncated",
        "occluded",
        "pose",
        "subset",
    ]
    for attr in expected_attrs:
        assert attr in schema.attributes, f"Missing attribute: {attr}"


def test_voc_sample_bbox_format_is_xyxy():
    """Test that VocSample bboxes are in xyxy format."""
    schema = VocSample.infer_schema()
    bbox_attr = schema.attributes.get("bboxes")
    assert bbox_attr is not None
    assert bbox_attr.field.format == "xyxy"


def test_voc_categories_default_labels():
    """Test VocCategories uses default VOC labels."""
    categories = VocCategories()
    assert categories.labels == VOC_LABELS
    assert len(categories.labels) == 21


def test_voc_categories_custom_labels():
    """Test VocCategories with custom labels."""
    custom_labels = ("custom1", "custom2", "custom3")
    categories = VocCategories(labels=custom_labels)
    assert categories.labels == custom_labels
