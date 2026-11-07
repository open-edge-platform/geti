# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for YOLO helper functions.
"""

from pathlib import Path

import numpy as np
import pytest
import yaml

from getidata import Dataset
from getidata.categories import LabelCategories
from getidata.data_formats.yolo.helpers import (
    _create_sample_from_image,
    _create_sample_from_traditional_image,
    _detect_yolo_format,
    _find_image_file,
    _get_image_size,
    _get_label_names_from_dataset,
    _group_samples_by_subset,
    _load_categories_from_names,
    _load_categories_from_yaml,
    _load_ultralytics_categories,
    _make_yolo_bbox,
    _parse_yolo_annotation,
    _save_sample_to_dir,
    _save_traditional_sample,
    _write_obj_data,
    _write_obj_names,
    _write_sample_annotation,
)
from getidata.data_formats.yolo.sample import YoloSample
from getidata.fields import ImageInfo, Subset


def _create_test_image(path: Path, width: int = 640, height: int = 480) -> None:
    """Create a minimal valid image file for testing."""
    from PIL import Image

    img = Image.new("RGB", (width, height), color="red")
    img.save(path)


# ==========================
# _find_image_file Tests
# ==========================


def test_find_image_file_finds_jpg_image(tmp_path: Path):
    """Test finding a .jpg image file."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake jpg")

    result = _find_image_file(tmp_path, "test")
    assert result == img_path


def test_find_image_file_finds_png_image(tmp_path: Path):
    """Test finding a .png image file."""
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"fake png")

    result = _find_image_file(tmp_path, "test")
    assert result == img_path


def test_find_image_file_returns_none_for_missing_image(tmp_path: Path):
    """Test returning None when no image is found."""
    result = _find_image_file(tmp_path, "nonexistent")
    assert result is None


def test_find_image_file_ignores_non_image_files(tmp_path: Path):
    """Test that non-image files are ignored."""
    (tmp_path / "test.txt").write_text("not an image")

    result = _find_image_file(tmp_path, "test")
    assert result is None


# ==============================
# _parse_yolo_annotation Tests
# ==============================


def test_parse_yolo_annotation_parses_valid_annotations(tmp_path: Path):
    """Test parsing a valid YOLO annotation file."""
    anno_path = tmp_path / "test.txt"
    anno_path.write_text("0 0.5 0.5 0.2 0.3\n1 0.25 0.75 0.1 0.2\n")

    bboxes, labels = _parse_yolo_annotation(anno_path, 640, 480)

    assert len(bboxes) == 2
    assert len(labels) == 2
    assert labels == [0, 1]
    # Check first bbox: center_x=0.5*640=320, center_y=0.5*480=240, w=0.2*640=128, h=0.3*480=144
    assert bboxes[0] == pytest.approx([320.0, 240.0, 128.0, 144.0])
    # Check second bbox: center_x=0.25*640=160, center_y=0.75*480=360, w=0.1*640=64, h=0.2*480=96
    assert bboxes[1] == pytest.approx([160.0, 360.0, 64.0, 96.0])


def test_parse_yolo_annotation_handles_empty_file(tmp_path: Path):
    """Test parsing an empty annotation file."""
    anno_path = tmp_path / "empty.txt"
    anno_path.write_text("")

    bboxes, labels = _parse_yolo_annotation(anno_path, 640, 480)

    assert bboxes == []
    assert labels == []


def test_parse_yolo_annotation_handles_missing_file(tmp_path: Path):
    """Test parsing when annotation file doesn't exist."""
    anno_path = tmp_path / "missing.txt"

    bboxes, labels = _parse_yolo_annotation(anno_path, 640, 480)

    assert bboxes == []
    assert labels == []


def test_parse_yolo_annotation_skips_invalid_lines(tmp_path: Path):
    """Test skipping lines with too few parts."""
    anno_path = tmp_path / "test.txt"
    anno_path.write_text("0 0.5 0.5\n1 0.25 0.75 0.1 0.2\n")

    bboxes, labels = _parse_yolo_annotation(anno_path, 640, 480)

    assert len(bboxes) == 1
    assert labels == [1]


def test_parse_yolo_annotation_skips_malformed_values(tmp_path: Path):
    """Test skipping lines with non-numeric values."""
    anno_path = tmp_path / "test.txt"
    anno_path.write_text("0 abc 0.5 0.2 0.3\n1 0.25 0.75 0.1 0.2\n")

    bboxes, labels = _parse_yolo_annotation(anno_path, 640, 480)

    assert len(bboxes) == 1
    assert labels == [1]


def test_parse_yolo_annotation_handles_blank_lines(tmp_path: Path):
    """Test that blank lines are ignored."""
    anno_path = tmp_path / "test.txt"
    anno_path.write_text("\n0 0.5 0.5 0.2 0.3\n\n1 0.25 0.75 0.1 0.2\n\n")

    bboxes, labels = _parse_yolo_annotation(anno_path, 640, 480)

    assert len(bboxes) == 2
    assert labels == [0, 1]


# ============================
# _detect_yolo_format Tests
# ============================


def test_detect_yolo_format_ultralytics_with_yaml(tmp_path: Path):
    """Test detecting Ultralytics format via data.yaml."""
    (tmp_path / "data.yaml").write_text("names: [cat, dog]\n")

    result = _detect_yolo_format(tmp_path)
    assert result == "ultralytics"


def test_detect_yolo_format_traditional_with_obj_names(tmp_path: Path):
    """Test detecting traditional format via obj.names."""
    (tmp_path / "obj.names").write_text("cat\ndog\n")

    result = _detect_yolo_format(tmp_path)
    assert result == "traditional"


def test_detect_yolo_format_traditional_with_obj_data(tmp_path: Path):
    """Test detecting traditional format via obj.data."""
    (tmp_path / "obj.data").write_text("classes = 2\n")

    result = _detect_yolo_format(tmp_path)
    assert result == "traditional"


def test_detect_yolo_format_ultralytics_with_directory_structure(tmp_path: Path):
    """Test detecting Ultralytics format via directory structure."""
    (tmp_path / "images").mkdir()
    (tmp_path / "labels").mkdir()

    result = _detect_yolo_format(tmp_path)
    assert result == "ultralytics"


def test_detect_yolo_format_returns_unknown_for_empty_directory(tmp_path: Path):
    """Test returning unknown for unrecognized structure."""
    result = _detect_yolo_format(tmp_path)
    assert result == "unknown"


# ==========================
# Category loading Tests
# ==========================


def test_load_categories_from_yaml_with_list(tmp_path: Path):
    """Test loading categories from YAML with list format."""
    yaml_path = tmp_path / "data.yaml"
    yaml_path.write_text("names: [cat, dog, bird]\n")

    categories = _load_categories_from_yaml(yaml_path)

    assert categories.labels == ("cat", "dog", "bird")


def test_load_categories_from_yaml_with_dict(tmp_path: Path):
    """Test loading categories from YAML with dict format."""
    yaml_path = tmp_path / "data.yaml"
    yaml_data = {"names": {0: "cat", 1: "dog", 2: "bird"}}
    yaml_path.write_text(yaml.dump(yaml_data))

    categories = _load_categories_from_yaml(yaml_path)

    assert categories.labels == ("cat", "dog", "bird")


def test_load_categories_from_yaml_invalid_format(tmp_path: Path):
    """Test error when names has invalid format."""
    yaml_path = tmp_path / "data.yaml"
    yaml_path.write_text("names: 'invalid'\n")

    with pytest.raises(ValueError, match="Invalid 'names' format"):
        _load_categories_from_yaml(yaml_path)


def test_load_categories_from_names(tmp_path: Path):
    """Test loading categories from obj.names file."""
    names_path = tmp_path / "obj.names"
    names_path.write_text("cat\ndog\nbird\n")

    categories = _load_categories_from_names(names_path)

    assert categories.labels == ("cat", "dog", "bird")


def test_load_categories_from_names_ignores_blank_lines(tmp_path: Path):
    """Test that blank lines are ignored in obj.names."""
    names_path = tmp_path / "obj.names"
    names_path.write_text("cat\n\ndog\n\nbird\n")

    categories = _load_categories_from_names(names_path)

    assert categories.labels == ("cat", "dog", "bird")


def test_load_ultralytics_categories_with_yaml(tmp_path: Path):
    """Test _load_ultralytics_categories with data.yaml present."""
    yaml_path = tmp_path / "data.yaml"
    yaml_path.write_text("names: [cat, dog]\n")

    categories = _load_ultralytics_categories(tmp_path)

    assert categories.labels == ("cat", "dog")


def test_load_ultralytics_categories_falls_back_to_names(tmp_path: Path):
    """Test fallback to .names file when data.yaml is missing."""
    names_path = tmp_path / "classes.names"
    names_path.write_text("cat\ndog\n")

    categories = _load_ultralytics_categories(tmp_path)

    assert categories.labels == ("cat", "dog")


def test_load_ultralytics_categories_returns_empty_when_nothing_found(tmp_path: Path):
    """Test returning empty categories when no config file is found."""
    categories = _load_ultralytics_categories(tmp_path)

    assert categories.labels == ()


# =======================
# _make_yolo_bbox Tests
# =======================


def test_make_yolo_bbox_converts_absolute_to_normalized():
    """Test converting absolute coordinates to normalized YOLO format."""
    img_size = (640, 480)
    bbox = [320.0, 240.0, 64.0, 48.0]  # center_x, center_y, width, height

    result = _make_yolo_bbox(img_size, bbox)

    assert result == pytest.approx((0.5, 0.5, 0.1, 0.1))


def test_make_yolo_bbox_handles_zero_dimensions():
    """Test handling images with zero dimensions."""
    img_size = (0, 0)
    bbox = [100.0, 100.0, 50.0, 50.0]

    result = _make_yolo_bbox(img_size, bbox)

    assert result == (0.0, 0.0, 0.0, 0.0)


def test_make_yolo_bbox_handles_zero_width():
    """Test handling images with zero width."""
    img_size = (0, 480)
    bbox = [100.0, 100.0, 50.0, 50.0]

    result = _make_yolo_bbox(img_size, bbox)

    assert result == (0.0, 0.0, 0.0, 0.0)


# ================================
# _create_sample_from_image Tests
# ================================


def test_create_sample_from_image_with_annotations(tmp_path: Path):
    """Test creating a sample with annotations."""
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    # Create test image
    img_path = images_dir / "test.jpg"
    _create_test_image(img_path, 640, 480)

    # Create annotation
    anno_path = labels_dir / "test.txt"
    anno_path.write_text("0 0.5 0.5 0.2 0.3\n")

    sample = _create_sample_from_image(img_path, labels_dir, Subset.TRAINING)

    assert sample is not None
    assert sample.image.path == str(img_path)
    assert sample.image_info.width == 640
    assert sample.image_info.height == 480
    assert sample.subset == Subset.TRAINING
    assert sample.bboxes is not None
    assert sample.labels is not None
    assert sample.labels[0] == 0


def test_create_sample_from_image_without_annotations(tmp_path: Path):
    """Test creating a sample without annotations."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    img_path = images_dir / "test.jpg"
    _create_test_image(img_path, 640, 480)

    sample = _create_sample_from_image(img_path, None, Subset.VALIDATION)

    assert sample is not None
    assert sample.bboxes is None
    assert sample.labels is None


# ===========================================
# _create_sample_from_traditional_image Tests
# ===========================================


def test_create_sample_from_traditional_image_with_annotation_alongside(tmp_path: Path):
    """Test creating a sample with annotation file next to image."""
    img_path = tmp_path / "test.jpg"
    _create_test_image(img_path, 640, 480)

    anno_path = tmp_path / "test.txt"
    anno_path.write_text("0 0.5 0.5 0.2 0.3\n")

    sample = _create_sample_from_traditional_image(img_path, Subset.TRAINING)

    assert sample is not None
    assert sample.bboxes is not None
    assert sample.labels is not None


# =======================
# Writing Functions Tests
# =======================


def test_write_obj_names(tmp_path: Path):
    """Test writing obj.names file."""
    names_path = tmp_path / "obj.names"
    label_names = ["cat", "dog", "bird"]

    _write_obj_names(names_path, label_names)

    content = names_path.read_text()
    assert content == "cat\ndog\nbird\n"


def test_write_obj_data(tmp_path: Path):
    """Test writing obj.data file and subset list files."""
    label_names = ["cat", "dog"]
    subset_lists = {
        "train": ["data/obj_train_data/img1.jpg", "data/obj_train_data/img2.jpg"],
        "valid": ["data/obj_valid_data/img3.jpg"],
    }
    written = {}

    data_path = _write_obj_data(tmp_path, label_names, subset_lists, written)

    assert data_path.exists()
    content = data_path.read_text()
    assert "classes = 2" in content
    assert "names = data/obj.names" in content
    assert "train.txt" in written
    assert "valid.txt" in written


def test_write_sample_annotation(tmp_path: Path):
    """Test writing annotation for a sample."""
    anno_path = tmp_path / "test.txt"

    sample = YoloSample(
        image="/path/to/image.jpg",
        image_info=ImageInfo(height=480, width=640),
        bboxes=np.array([[320.0, 240.0, 64.0, 48.0]], dtype=np.float32),
        labels=np.array([0], dtype=np.int32),
        subset=Subset.TRAINING,
    )

    _write_sample_annotation(anno_path, sample)

    content = anno_path.read_text()
    lines = content.strip().split("\n")
    assert len(lines) == 1
    parts = lines[0].split()
    assert parts[0] == "0"  # label
    assert float(parts[1]) == pytest.approx(0.5, abs=0.001)  # center_x normalized
    assert float(parts[2]) == pytest.approx(0.5, abs=0.001)  # center_y normalized
    assert float(parts[3]) == pytest.approx(0.1, abs=0.001)  # width normalized
    assert float(parts[4]) == pytest.approx(0.1, abs=0.001)  # height normalized


# ================================
# _save_sample_to_dir / _save_traditional_sample Tests
# ================================


def test_save_sample_to_dir_disambiguates_same_basename(tmp_path: Path):
    """Regression test for https://github.com/open-edge-platform/geti/issues/7496.

    Frames extracted from different videos into per-video directories can share the
    same basename (e.g. "frame000066.png"). Saving them to a flattened YOLO images
    directory must not let one overwrite/shadow the other.
    """
    video_a_dir = tmp_path / "video_a_frames"
    video_b_dir = tmp_path / "video_b_frames"
    video_a_dir.mkdir()
    video_b_dir.mkdir()
    frame_a = video_a_dir / "frame000066.png"
    frame_b = video_b_dir / "frame000066.png"
    _create_test_image(frame_a, 640, 480)
    _create_test_image(frame_b, 320, 240)

    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    sample_a = YoloSample(
        image=str(frame_a),
        image_info=ImageInfo(height=480, width=640),
        bboxes=np.array([[320.0, 240.0, 64.0, 48.0]], dtype=np.float32),
        labels=np.array([0], dtype=np.int32),
        subset=Subset.TRAINING,
    )
    sample_b = YoloSample(
        image=str(frame_b),
        image_info=ImageInfo(height=240, width=320),
        bboxes=np.array([[160.0, 120.0, 32.0, 24.0]], dtype=np.float32),
        labels=np.array([1], dtype=np.int32),
        subset=Subset.TRAINING,
    )

    used_names: dict[str, str] = {}
    _save_sample_to_dir(sample_a, images_dir, labels_dir, save_images=True, used_names=used_names)
    _save_sample_to_dir(sample_b, images_dir, labels_dir, save_images=True, used_names=used_names)

    saved_images = sorted(p.name for p in images_dir.iterdir())
    saved_labels = sorted(p.name for p in labels_dir.iterdir())
    assert len(saved_images) == 2, f"expected 2 distinct images, got {saved_images}"
    assert len(saved_labels) == 2, f"expected 2 distinct label files, got {saved_labels}"

    # Each label file must reference its own sample's class, not be overwritten by the other.
    label_contents = {p.name: p.read_text() for p in labels_dir.iterdir()}
    classes = {content.split()[0] for content in label_contents.values()}
    assert classes == {"0", "1"}


def test_save_traditional_sample_disambiguates_same_basename(tmp_path: Path):
    """Regression test for https://github.com/open-edge-platform/geti/issues/7496 (traditional format)."""
    video_a_dir = tmp_path / "video_a_frames"
    video_b_dir = tmp_path / "video_b_frames"
    video_a_dir.mkdir()
    video_b_dir.mkdir()
    frame_a = video_a_dir / "frame000066.png"
    frame_b = video_b_dir / "frame000066.png"
    _create_test_image(frame_a, 640, 480)
    _create_test_image(frame_b, 320, 240)

    subset_dir = tmp_path / "obj_train_data"
    subset_dir.mkdir()

    sample_a = YoloSample(
        image=str(frame_a),
        image_info=ImageInfo(height=480, width=640),
        bboxes=np.array([[320.0, 240.0, 64.0, 48.0]], dtype=np.float32),
        labels=np.array([0], dtype=np.int32),
        subset=Subset.TRAINING,
    )
    sample_b = YoloSample(
        image=str(frame_b),
        image_info=ImageInfo(height=240, width=320),
        bboxes=np.array([[160.0, 120.0, 32.0, 24.0]], dtype=np.float32),
        labels=np.array([1], dtype=np.int32),
        subset=Subset.TRAINING,
    )

    used_names: dict[str, str] = {}
    path_a = _save_traditional_sample(sample_a, subset_dir, "obj_train_data", save_images=True, used_names=used_names)
    path_b = _save_traditional_sample(sample_b, subset_dir, "obj_train_data", save_images=True, used_names=used_names)

    assert path_a != path_b
    saved_images = sorted(p.name for p in subset_dir.iterdir() if p.suffix == ".png")
    assert len(saved_images) == 2, f"expected 2 distinct images, got {saved_images}"


# ================================
# _group_samples_by_subset Tests
# ================================


def test_group_samples_by_subset_groups_correctly():
    """Test grouping samples by subset."""
    dataset = Dataset(YoloSample, categories={"labels": LabelCategories(labels=("cat", "dog"))})

    dataset.append(
        YoloSample(
            image="/path/train1.jpg",
            image_info=ImageInfo(height=480, width=640),
            bboxes=None,
            labels=None,
            subset=Subset.TRAINING,
        )
    )
    dataset.append(
        YoloSample(
            image="/path/val1.jpg",
            image_info=ImageInfo(height=480, width=640),
            bboxes=None,
            labels=None,
            subset=Subset.VALIDATION,
        )
    )
    dataset.append(
        YoloSample(
            image="/path/train2.jpg",
            image_info=ImageInfo(height=480, width=640),
            bboxes=None,
            labels=None,
            subset=Subset.TRAINING,
        )
    )

    result = _group_samples_by_subset(dataset)

    assert len(result[Subset.TRAINING]) == 2
    assert len(result[Subset.VALIDATION]) == 1


# ======================================
# _get_label_names_from_dataset Tests
# ======================================


def test_get_label_names_from_dataset_extracts_label_names():
    """Test extracting label names from dataset schema."""
    dataset = Dataset(YoloSample, categories={"labels": LabelCategories(labels=("cat", "dog", "bird"))})

    result = _get_label_names_from_dataset(dataset)

    assert result == ["cat", "dog", "bird"]


def test_get_label_names_from_dataset_returns_empty_when_no_categories():
    """Test returning empty list when no categories are set."""
    dataset = Dataset(YoloSample)

    result = _get_label_names_from_dataset(dataset)

    assert result == []


@pytest.mark.parametrize(
    ("orientation", "expected_height", "expected_width"),
    [
        (1, 40, 80),
        (2, 40, 80),
        (3, 40, 80),
        (4, 40, 80),
        (5, 80, 40),
        (6, 80, 40),
        (7, 80, 40),
        (8, 80, 40),
    ],
)
def test_get_image_size_respects_exif_orientation(tmp_path, orientation, expected_height, expected_width):
    """YOLO _get_image_size must honor EXIF orientation so image dimensions
    match the displayed image and the annotations derived from it.
    """
    from PIL import Image as PILImage

    # Raw pixels: landscape H=40, W=80.
    img = PILImage.fromarray(np.zeros((40, 80, 3), dtype=np.uint8))
    exif = img.getexif()
    exif[0x0112] = orientation
    path = tmp_path / f"orient_{orientation}.jpg"
    img.save(path, format="JPEG", exif=exif.tobytes())

    height, width = _get_image_size(path)
    assert (height, width) == (expected_height, expected_width)
