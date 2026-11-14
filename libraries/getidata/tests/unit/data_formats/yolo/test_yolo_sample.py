# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for YOLO sample classes.
"""

import numpy as np
import pytest

from getidata.data_formats.yolo.sample import YoloClsSample, YoloSample, YoloSegSample, _YoloBaseSample
from getidata.fields import ImageInfo, Subset


def test_yolo_sample_create_with_all_fields():
    """Test creating a sample with all fields populated."""
    bboxes = np.array([[100.0, 100.0, 50.0, 50.0]], dtype=np.float32)
    labels = np.array([0], dtype=np.int32)

    sample = YoloSample(
        image="/path/to/image.jpg",
        image_info=ImageInfo(height=480, width=640),
        bboxes=bboxes,
        labels=labels,
        subset=Subset.TRAINING,
    )

    assert sample.image.path == "/path/to/image.jpg"
    assert sample.image_info.height == 480
    assert sample.image_info.width == 640
    assert sample.subset == Subset.TRAINING
    np.testing.assert_array_equal(sample.bboxes, bboxes)
    np.testing.assert_array_equal(sample.labels, labels)


@pytest.mark.parametrize("sample_type", [YoloClsSample, YoloSegSample, YoloSample])
def test_yolo_samples_share_base_fields(sample_type):
    """Test that every YOLO sample type inherits the common fields from the shared base class."""
    assert issubclass(sample_type, _YoloBaseSample)

    schema = sample_type.infer_schema()
    assert set(schema.attributes) >= {"image", "image_info", "subset"}
