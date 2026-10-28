# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import tempfile

import numpy as np
import pytest

from getidata.data_formats.voc.constants import VOC_LABELS
from getidata.data_formats.voc.io import load_voc_dataset, save_voc_dataset
from getidata.data_formats.voc.sample import VocCategories, VocSample


class VocConstantsTest:
    def test_voc_labels_count(self):
        """VOC has 21 labels including background."""
        assert len(VOC_LABELS) == 21

    def test_voc_labels_includes_background(self):
        """Background should be the first label."""
        assert VOC_LABELS[0] == "background"

    def test_voc_labels_includes_common_objects(self):
        """Check that common VOC objects are included."""
        common_objects = ["person", "car", "dog", "cat", "bicycle"]
        for obj in common_objects:
            assert obj in VOC_LABELS


class VocCategoriesTest:
    def test_default_categories(self):
        """VocCategories should use default VOC labels by default."""
        categories = VocCategories()
        assert categories.labels == VOC_LABELS
        assert len(categories.labels) == 21

    def test_custom_categories(self):
        """VocCategories should accept custom labels."""
        custom_labels = ("custom1", "custom2", "custom3")
        categories = VocCategories(labels=custom_labels)
        assert categories.labels == custom_labels


class VocSampleTest:
    def test_sample_schema_has_required_attributes(self):
        """VocSample schema should have all required attributes."""
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

    def test_sample_creation(self):
        """Test creating a VocSample with valid data."""
        from getidata.fields import ImageInfo, Subset

        sample = VocSample(
            image="/path/to/image.jpg",
            image_info=ImageInfo(height=480, width=640),
            bboxes=np.array([[100, 100, 200, 200]], dtype=np.float32),
            labels=np.array([1], dtype=np.uint32),
            difficult=np.array([False]),
            truncated=np.array([False]),
            occluded=np.array([False]),
            pose=np.array(["Frontal"], dtype=object),
            subset=Subset.TRAINING,
        )

        assert sample.bboxes.shape == (1, 4)
        assert sample.labels[0] == 1


class VocIOTest:
    def test_load_voc_dataset(self, voc_dataset_path):
        """Test loading a VOC dataset from standard layout."""
        dataset = load_voc_dataset(root_dir=voc_dataset_path)
        assert len(dataset) > 0

    def test_load_voc_dataset_samples_have_correct_attributes(self, voc_dataset_path):
        """Test that loaded samples have the expected attributes."""
        dataset = load_voc_dataset(root_dir=voc_dataset_path)

        for sample in dataset:
            assert hasattr(sample, "image")
            assert hasattr(sample, "image_info")
            assert hasattr(sample, "bboxes")
            assert hasattr(sample, "labels")
            assert hasattr(sample, "subset")

    def test_save_and_load_voc_dataset(self, voc_dataset_path):
        """Test round-trip: load -> save -> load."""
        # Load original dataset
        dataset = load_voc_dataset(root_dir=voc_dataset_path)
        original_len = len(dataset)

        # Save to temp directory (with images so we can reload)
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_voc_dataset(dataset, root_dir=tmp_dir, save_images=True)

            # Load saved dataset
            reloaded = load_voc_dataset(root_dir=tmp_dir)
            assert len(reloaded) == original_len


class VocFormatDetectionTest:
    def test_detect_voc_format(self, voc_dataset_path):
        """Test that VOC format is correctly detected."""
        from pathlib import Path

        from getidata.data_formats.base import DataFormat
        from getidata.data_formats.voc.io import is_voc_format
        from getidata.format_detection import detect_dataset_format

        path = Path(voc_dataset_path)
        assert is_voc_format(path) is True
        assert detect_dataset_format(path) == DataFormat.VOC

    def test_import_voc_via_import_dataset(self, voc_dataset_path):
        """Test importing VOC dataset via the generic import_dataset function."""
        from getidata import import_dataset

        dataset = import_dataset(voc_dataset_path)
        assert len(dataset) > 0

        # Verify the samples have expected VOC attributes
        for sample in dataset:
            assert hasattr(sample, "image")
            assert hasattr(sample, "bboxes")
            assert hasattr(sample, "labels")


@pytest.fixture
def voc_dataset_path():
    """Return path to test VOC dataset."""
    import os

    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "..",
        "assets",
        "voc_dataset",
        "voc_dataset1",
    )
    if os.path.exists(path):
        return path
    pytest.skip("VOC test dataset not found")
