# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


"""
Unit tests for Ultralytics YOLO segmentation I/O functions.
"""

from pathlib import Path

import numpy as np
import pytest

from getidata import Dataset
from getidata.categories import LabelCategories
from getidata.data_formats.base import DataFormat
from getidata.data_formats.yolo.io import (
    is_yolo_seg_format,
    load_yolo_dataset,
    load_yolo_seg_dataset,
    save_yolo_seg_dataset,
)
from getidata.data_formats.yolo.sample import YoloSegSample
from getidata.export_import import export_dataset, import_dataset
from getidata.fields import ImageInfo, Subset
from getidata.format_detection import detect_dataset_format


def _create_test_image(path: Path, width: int = 640, height: int = 480) -> None:
    """Create a minimal valid image file for testing."""
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), color="red")
    img.save(path)


def _create_seg_dataset(root: Path) -> None:
    """Create a minimal Ultralytics YOLO segmentation dataset structure."""
    _create_test_image(root / "images" / "train" / "img1.jpg")
    _create_test_image(root / "images" / "train" / "img2.jpg")
    _create_test_image(root / "images" / "val" / "img3.jpg")
    (root / "labels" / "train").mkdir(parents=True)
    (root / "labels" / "val").mkdir(parents=True)
    (root / "labels" / "train" / "img1.txt").write_text(
        "0 0.1 0.2 0.3 0.2 0.3 0.4\n1 0.5 0.1 0.7 0.1 0.7 0.9 0.5 0.9\n"
    )
    (root / "labels" / "train" / "img2.txt").write_text("0 0.0 0.0 0.5 0.0 0.5 0.5 0.0 0.5 0.25 0.25\n")
    (root / "labels" / "val" / "img3.txt").write_text("1 0.5 0.5 0.6 0.5 0.6 0.6 0.5 0.6\n")
    (root / "data.yaml").write_text("names: [cat, dog]\ntrain: images/train\nval: images/val\n")


def _create_detection_dataset(root: Path) -> None:
    """Create a minimal Ultralytics YOLO detection dataset structure."""
    _create_test_image(root / "images" / "train" / "img1.jpg")
    (root / "labels" / "train").mkdir(parents=True)
    (root / "labels" / "train" / "img1.txt").write_text("0 0.5 0.5 0.2 0.3\n")
    (root / "data.yaml").write_text("names: [cat]\ntrain: images/train\n")


def _make_seg_sample(image_path: Path, polygons: list, labels: list, subset: Subset = Subset.TRAINING):
    """Create a test YoloSegSample with absolute-coordinate polygons."""
    polygons_arr = np.empty(len(polygons), dtype=object)
    for i, polygon in enumerate(polygons):
        polygons_arr[i] = np.asarray(polygon, dtype=np.float32)
    labels_arr = np.array(labels, dtype=np.int32) if labels else None
    return YoloSegSample(
        image=str(image_path),
        image_info=ImageInfo(height=480, width=640),
        polygons=polygons_arr if labels else None,
        labels=labels_arr,
        subset=subset,
    )


# ==========================
# Detection Tests
# ==========================


def test_is_yolo_seg_format_positive(tmp_path: Path):
    """Test that the segmentation layout is detected."""
    _create_seg_dataset(tmp_path)

    assert is_yolo_seg_format(tmp_path)


def test_detect_dataset_format_yolo_seg(tmp_path: Path):
    """Test that auto-detection returns the segmentation format."""
    _create_seg_dataset(tmp_path)

    assert detect_dataset_format(tmp_path) == DataFormat.YOLO_ULTRALYTICS_SEG


def test_is_yolo_seg_format_positive_without_yaml(tmp_path: Path):
    """Test that the segmentation format is detected without a data.yaml file."""
    _create_test_image(tmp_path / "images" / "train" / "img1.jpg")
    (tmp_path / "labels" / "train").mkdir(parents=True)
    (tmp_path / "labels" / "train" / "img1.txt").write_text("0 0.1 0.2 0.3 0.2 0.3 0.4\n")

    assert is_yolo_seg_format(tmp_path)
    assert detect_dataset_format(tmp_path) == DataFormat.YOLO_ULTRALYTICS_SEG


def test_is_yolo_seg_format_negative_detection_rows(tmp_path: Path):
    """Test that detection datasets with 5-field rows are not misdetected as segmentation."""
    _create_detection_dataset(tmp_path)

    assert not is_yolo_seg_format(tmp_path)
    assert detect_dataset_format(tmp_path) == DataFormat.YOLO


def test_is_yolo_seg_format_negative_empty_labels(tmp_path: Path):
    """Test that a detection layout without label rows is not detected as segmentation."""
    _create_test_image(tmp_path / "images" / "train" / "img1.jpg")
    (tmp_path / "labels" / "train").mkdir(parents=True)
    (tmp_path / "data.yaml").write_text("names: [cat]\ntrain: images/train\n")

    assert not is_yolo_seg_format(tmp_path)
    assert detect_dataset_format(tmp_path) == DataFormat.YOLO


def test_is_yolo_seg_format_negative_malformed_rows_only(tmp_path: Path):
    """Test that malformed rows (even field count) do not mark a dataset as segmentation."""
    _create_test_image(tmp_path / "images" / "train" / "img1.jpg")
    (tmp_path / "labels" / "train").mkdir(parents=True)
    (tmp_path / "labels" / "train" / "img1.txt").write_text("0 0.1 0.2 0.3 0.2 0.3 0.4 0.5\n")
    (tmp_path / "data.yaml").write_text("names: [cat]\ntrain: images/train\n")

    assert not is_yolo_seg_format(tmp_path)


def test_is_yolo_seg_format_negative_classification(tmp_path: Path):
    """Test that the classification layout is not misdetected as segmentation."""
    _create_test_image(tmp_path / "train" / "cat" / "img1.jpg")
    _create_test_image(tmp_path / "val" / "cat" / "img2.jpg")

    assert not is_yolo_seg_format(tmp_path)
    assert detect_dataset_format(tmp_path) == DataFormat.YOLO_ULTRALYTICS_CLS


def test_is_yolo_seg_format_negative_traditional(tmp_path: Path):
    """Test that the traditional YOLO layout is never treated as segmentation."""
    _create_test_image(tmp_path / "obj_train_data" / "img1.jpg")
    (tmp_path / "obj_train_data" / "img1.txt").write_text("0 0.1 0.2 0.3 0.2 0.3 0.4\n")
    (tmp_path / "obj.names").write_text("cat\n")

    assert not is_yolo_seg_format(tmp_path)


# ==========================
# load_yolo_seg_dataset Tests
# ==========================


def test_load_yolo_seg_dataset(tmp_path: Path):
    """Test loading a segmentation dataset with polygon rows of varying length."""
    _create_seg_dataset(tmp_path)

    ds = load_yolo_seg_dataset(str(tmp_path))

    assert len(ds) == 3
    assert ds.dtype is YoloSegSample

    label_categories = ds.schema.attributes["labels"].categories
    assert label_categories.labels == ("cat", "dog")

    by_image = {Path(sample.image).name: sample for sample in ds}
    assert by_image["img1.jpg"].subset == Subset.TRAINING
    assert by_image["img3.jpg"].subset == Subset.VALIDATION

    # Normalized coordinates are converted to absolute pixel coordinates (x * width, y * height)
    img1_polygons = [np.asarray(p).tolist() for p in by_image["img1.jpg"].polygons]
    assert img1_polygons == [
        [[64.0, 96.0], [192.0, 96.0], [192.0, 192.0]],
        [[320.0, 48.0], [448.0, 48.0], [448.0, 432.0], [320.0, 432.0]],
    ]
    assert by_image["img1.jpg"].labels.tolist() == [0, 1]

    # Rows may have different lengths: img2 holds a single 5-point polygon
    img2_polygons = [np.asarray(p).tolist() for p in by_image["img2.jpg"].polygons]
    assert len(img2_polygons) == 1
    assert len(img2_polygons[0]) == 5
    assert by_image["img2.jpg"].labels.tolist() == [0]


def test_load_yolo_seg_dataset_missing_root(tmp_path: Path):
    """Test that a missing root directory raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_yolo_seg_dataset(str(tmp_path / "missing"))


def test_load_yolo_seg_dataset_no_subsets(tmp_path: Path):
    """Test that a directory without image directories raises FileNotFoundError."""
    (tmp_path / "data.yaml").write_text("names: [cat]\n")

    with pytest.raises(FileNotFoundError, match="Could not locate any image directory"):
        load_yolo_seg_dataset(str(tmp_path))


def test_load_yolo_seg_dataset_skips_malformed_rows(tmp_path: Path):
    """Test that malformed rows are skipped while valid rows are still loaded."""
    _create_test_image(tmp_path / "images" / "train" / "img1.jpg")
    (tmp_path / "labels" / "train").mkdir(parents=True)
    # valid row, a detection-format row (5 fields), an unpaired-coordinates row (8 fields),
    # a too-short row (6 fields) and a row with a non-numeric coordinate
    (tmp_path / "labels" / "train" / "img1.txt").write_text(
        "0 0.1 0.2 0.3 0.2 0.3 0.4\n"
        "0 0.5 0.5 0.2 0.3\n"
        "0 0.1 0.2 0.3 0.2 0.3 0.4 0.5\n"
        "0 0.1 0.2 0.3 0.2 0.3\n"
        "0 0.1 0.2 0.3 abc 0.3 0.4\n"
    )
    (tmp_path / "data.yaml").write_text("names: [cat]\ntrain: images/train\n")

    ds = load_yolo_seg_dataset(str(tmp_path))

    assert len(ds) == 1
    sample = ds[0]
    assert sample.labels.tolist() == [0]
    assert [np.asarray(p).tolist() for p in sample.polygons] == [[[64.0, 96.0], [192.0, 96.0], [192.0, 192.0]]]


def test_load_yolo_seg_dataset_image_without_labels(tmp_path: Path):
    """Test that an image without a label file yields a sample without polygons."""
    _create_test_image(tmp_path / "images" / "train" / "img1.jpg")
    _create_test_image(tmp_path / "images" / "train" / "img2.jpg")
    (tmp_path / "labels" / "train").mkdir(parents=True)
    (tmp_path / "labels" / "train" / "img1.txt").write_text("0 0.1 0.2 0.3 0.2 0.3 0.4\n")
    (tmp_path / "data.yaml").write_text("names: [cat]\ntrain: images/train\n")

    ds = load_yolo_seg_dataset(str(tmp_path))

    by_image = {Path(sample.image).name: sample for sample in ds}
    assert by_image["img1.jpg"].polygons is not None
    assert by_image["img2.jpg"].polygons is None
    assert by_image["img2.jpg"].labels is None


def test_load_yolo_dataset_rejects_segmentation_labels(tmp_path: Path):
    """Test that the detection loader refuses to load a segmentation dataset as detection."""
    _create_seg_dataset(tmp_path)

    with pytest.raises(ValueError, match="segmentation labels"):
        load_yolo_dataset(str(tmp_path))


def test_import_dataset_auto_detects_yolo_seg(tmp_path: Path):
    """Test that import_dataset auto-detects and loads the segmentation format."""
    _create_seg_dataset(tmp_path)

    ds = import_dataset(str(tmp_path))

    assert ds.dtype is YoloSegSample
    assert len(ds) == 3


def test_import_dataset_explicit_yolo_seg_format(tmp_path: Path):
    """Test loading with an explicit data_format."""
    _create_seg_dataset(tmp_path)

    ds = import_dataset(str(tmp_path), data_format=DataFormat.YOLO_ULTRALYTICS_SEG)

    assert ds.dtype is YoloSegSample
    assert len(ds) == 3


# ==========================
# save_yolo_seg_dataset Tests
# ==========================


def test_save_yolo_seg_dataset(tmp_path: Path):
    """Test saving a segmentation dataset."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    _create_test_image(src_dir / "img1.jpg")

    dataset = Dataset(YoloSegSample, categories={"labels": LabelCategories(labels=("cat", "dog"))})
    dataset.append(_make_seg_sample(src_dir / "img1.jpg", polygons=[[[64, 96], [192, 96], [192, 192]]], labels=[0]))

    export_dir = tmp_path / "export"
    written = save_yolo_seg_dataset(dataset, str(export_dir))

    assert (export_dir / "images" / "train" / "img1.jpg").exists()
    # Coordinates are normalized relative to the image dimensions (x/640, y/480)
    assert (
        export_dir / "labels" / "train" / "img1.txt"
    ).read_text() == "0 0.100000 0.200000 0.300000 0.200000 0.300000 0.400000\n"
    assert (export_dir / "data.yaml").exists()
    assert written["data.yaml"] == export_dir / "data.yaml"


def test_save_yolo_seg_dataset_skips_short_polygons(tmp_path: Path):
    """Test that polygons with fewer than three points are skipped."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    _create_test_image(src_dir / "img1.jpg")

    dataset = Dataset(YoloSegSample, categories={"labels": LabelCategories(labels=("cat",))})
    dataset.append(
        _make_seg_sample(
            src_dir / "img1.jpg",
            polygons=[[[64, 96], [192, 96]], [[64, 96], [192, 96], [192, 192]]],
            labels=[0, 0],
        )
    )

    export_dir = tmp_path / "export"
    save_yolo_seg_dataset(dataset, str(export_dir))

    lines = (export_dir / "labels" / "train" / "img1.txt").read_text().splitlines()
    assert len(lines) == 1
    assert lines[0].split()[0] == "0"
    assert len(lines[0].split()) == 7


def test_save_yolo_seg_dataset_unlabeled_sample_gets_empty_label_file(tmp_path: Path):
    """Test that samples without polygons get an empty label file, as in the detection format."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    _create_test_image(src_dir / "img1.jpg")
    _create_test_image(src_dir / "img2.jpg")

    dataset = Dataset(YoloSegSample, categories={"labels": LabelCategories(labels=("cat",))})
    dataset.append(_make_seg_sample(src_dir / "img1.jpg", polygons=[[[64, 96], [192, 96], [192, 192]]], labels=[0]))
    dataset.append(_make_seg_sample(src_dir / "img2.jpg", polygons=[], labels=[]))

    export_dir = tmp_path / "export"
    save_yolo_seg_dataset(dataset, str(export_dir))

    assert (export_dir / "images" / "train" / "img1.jpg").exists()
    assert (export_dir / "images" / "train" / "img2.jpg").exists()
    assert (export_dir / "labels" / "train" / "img1.txt").read_text() != ""
    assert (export_dir / "labels" / "train" / "img2.txt").read_text() == ""


def test_save_yolo_seg_dataset_name_collision(tmp_path: Path):
    """Test that colliding file names get a numeric suffix."""
    src_dir_a = tmp_path / "a"
    src_dir_b = tmp_path / "b"
    _create_test_image(src_dir_a / "img.jpg")
    _create_test_image(src_dir_b / "img.jpg")

    dataset = Dataset(YoloSegSample, categories={"labels": LabelCategories(labels=("cat",))})
    dataset.append(_make_seg_sample(src_dir_a / "img.jpg", polygons=[[[64, 96], [192, 96], [192, 192]]], labels=[0]))
    dataset.append(_make_seg_sample(src_dir_b / "img.jpg", polygons=[[[64, 96], [192, 96], [192, 192]]], labels=[0]))

    export_dir = tmp_path / "export"
    save_yolo_seg_dataset(dataset, str(export_dir))

    assert (export_dir / "images" / "train" / "img.jpg").exists()
    assert (export_dir / "images" / "train" / "img_1.jpg").exists()
    assert (export_dir / "labels" / "train" / "img.txt").exists()
    assert (export_dir / "labels" / "train" / "img_1.txt").exists()


# ==========================
# Round-trip Tests
# ==========================


def test_save_and_reload_yolo_seg(tmp_path: Path):
    """Test round-trip: save and reload a segmentation dataset with polygons intact."""
    _create_seg_dataset(tmp_path)

    original = load_yolo_seg_dataset(str(tmp_path))

    export_dir = tmp_path / "export"
    save_yolo_seg_dataset(original, str(export_dir))

    reloaded = load_yolo_seg_dataset(str(export_dir))

    assert len(reloaded) == len(original)
    original_by_name = {Path(sample.image).name: sample for sample in original}
    for sample in reloaded:
        original_sample = original_by_name[Path(sample.image).name]
        assert sample.subset == original_sample.subset
        assert sample.labels.tolist() == original_sample.labels.tolist()
        assert len(sample.polygons) == len(original_sample.polygons)
        for polygon, original_polygon in zip(sample.polygons, original_sample.polygons):
            assert np.asarray(polygon) == pytest.approx(np.asarray(original_polygon), abs=1e-3)


def test_export_dataset_yolo_seg_format(tmp_path: Path):
    """Test the export_dataset entry point with the segmentation format."""
    _create_seg_dataset(tmp_path)

    original = load_yolo_seg_dataset(str(tmp_path))

    export_dir = tmp_path / "export"
    export_dataset(original, output_path=str(export_dir), data_format=DataFormat.YOLO_ULTRALYTICS_SEG)

    assert (export_dir / "images" / "train").is_dir()
    assert (export_dir / "labels" / "train").is_dir()
    assert (export_dir / "data.yaml").exists()

    reloaded = import_dataset(str(export_dir))
    assert reloaded.dtype is YoloSegSample
    assert len(reloaded) == len(original)


def test_export_dataset_yolo_seg_format_as_zip(tmp_path: Path):
    """Test exporting the segmentation format as a zip archive."""
    _create_seg_dataset(tmp_path)

    original = load_yolo_seg_dataset(str(tmp_path))

    zip_path = tmp_path / "export.zip"
    export_dataset(original, output_path=str(zip_path), data_format=DataFormat.YOLO_ULTRALYTICS_SEG, as_zip=True)

    assert zip_path.exists()

    reloaded = import_dataset(str(zip_path), extract_dir=tmp_path / "extracted")
    assert reloaded.dtype is YoloSegSample
    assert len(reloaded) == len(original)


def test_seg_dataset_not_misdetected_after_detection_export(tmp_path: Path):
    """Test that a seg dataset saved through the generic YOLO exporter stays detectable as seg."""
    _create_seg_dataset(tmp_path)

    original = load_yolo_seg_dataset(str(tmp_path))

    export_dir = tmp_path / "export"
    export_dataset(original, output_path=str(export_dir), data_format=DataFormat.YOLO_ULTRALYTICS_SEG)

    assert detect_dataset_format(export_dir) == DataFormat.YOLO_ULTRALYTICS_SEG
