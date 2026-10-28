# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for YOLO I/O functions.
"""

from pathlib import Path

import numpy as np
import pytest
import yaml

from getidata import Dataset
from getidata.categories import LabelCategories
from getidata.data_formats.base import DataFormat
from getidata.data_formats.yolo.io import load_yolo_dataset, save_yolo_dataset
from getidata.data_formats.yolo.sample import YoloSample
from getidata.fields import ImageInfo, Subset


def _create_test_image(path: Path, width: int = 640, height: int = 480) -> None:
    """Create a minimal valid image file for testing."""
    from PIL import Image

    img = Image.new("RGB", (width, height), color="red")
    img.save(path)


def _create_ultralytics_dataset(root: Path, create_images: bool = True) -> None:
    """Create a minimal Ultralytics format dataset structure."""
    images_train = root / "images" / "train"
    images_val = root / "images" / "val"
    labels_train = root / "labels" / "train"
    labels_val = root / "labels" / "val"

    images_train.mkdir(parents=True)
    images_val.mkdir(parents=True)
    labels_train.mkdir(parents=True)
    labels_val.mkdir(parents=True)

    if create_images:
        _create_test_image(images_train / "img1.jpg", 640, 480)
        _create_test_image(images_train / "img2.jpg", 640, 480)
        _create_test_image(images_val / "img3.jpg", 640, 480)

    # Create annotations
    (labels_train / "img1.txt").write_text("0 0.5 0.5 0.2 0.3\n")
    (labels_train / "img2.txt").write_text("1 0.25 0.75 0.1 0.2\n")
    (labels_val / "img3.txt").write_text("0 0.3 0.4 0.15 0.25\n")

    # Create data.yaml
    yaml_data = {
        "names": ["cat", "dog"],
        "train": "images/train",
        "val": "images/val",
    }
    (root / "data.yaml").write_text(yaml.dump(yaml_data))


def _create_roboflow_dataset(root: Path) -> None:
    """Create a Roboflow-style Ultralytics dataset laid out as <subset>/images and <subset>/labels."""
    for subset_dir_name, image_names in (("train", ("img1", "img2")), ("valid", ("img3",))):
        images_dir = root / subset_dir_name / "images"
        labels_dir = root / subset_dir_name / "labels"
        images_dir.mkdir(parents=True)
        labels_dir.mkdir(parents=True)

        for image_name in image_names:
            _create_test_image(images_dir / f"{image_name}.jpg", 640, 480)
            (labels_dir / f"{image_name}.txt").write_text("0 0.5 0.5 0.2 0.3\n")

    # Roboflow declares the paths relative to a subset directory, not to the dataset root
    yaml_data = {
        "names": ["cat", "dog"],
        "train": "../train/images",
        "val": "../valid/images",
    }
    (root / "data.yaml").write_text(yaml.dump(yaml_data))


def _create_traditional_dataset(root: Path, create_images: bool = True) -> None:
    """Create a minimal traditional YOLO format dataset structure."""
    train_dir = root / "obj_train_data"
    val_dir = root / "obj_valid_data"

    train_dir.mkdir(parents=True)
    val_dir.mkdir(parents=True)

    if create_images:
        _create_test_image(train_dir / "img1.jpg", 640, 480)
        _create_test_image(train_dir / "img2.jpg", 640, 480)
        _create_test_image(val_dir / "img3.jpg", 640, 480)

    # Create annotations alongside images
    (train_dir / "img1.txt").write_text("0 0.5 0.5 0.2 0.3\n")
    (train_dir / "img2.txt").write_text("1 0.25 0.75 0.1 0.2\n")
    (val_dir / "img3.txt").write_text("0 0.3 0.4 0.15 0.25\n")

    # Create obj.names
    (root / "obj.names").write_text("cat\ndog\n")


def _make_sample(image_path: Path, subset: Subset = Subset.TRAINING) -> YoloSample:
    """Create a test YoloSample."""
    return YoloSample(
        image=str(image_path),
        image_info=ImageInfo(height=480, width=640),
        bboxes=np.array([[320.0, 240.0, 64.0, 48.0]], dtype=np.float32),
        labels=np.array([0], dtype=np.int32),
        subset=subset,
    )


# ==========================
# load_yolo_dataset Tests
# ==========================


def test_load_yolo_dataset_ultralytics_format(tmp_path: Path):
    """Test loading an Ultralytics format dataset."""
    _create_ultralytics_dataset(tmp_path)

    ds = load_yolo_dataset(str(tmp_path))

    assert len(ds) == 3
    # Check that subsets are correctly assigned
    subsets = {s.subset for s in ds}
    assert Subset.TRAINING in subsets
    assert Subset.VALIDATION in subsets


def test_load_yolo_dataset_ultralytics_format_explicit(tmp_path: Path):
    """Test loading with explicit format specification."""
    _create_ultralytics_dataset(tmp_path)

    ds = load_yolo_dataset(str(tmp_path), format="ultralytics")

    assert len(ds) == 3


def test_load_yolo_dataset_traditional_format(tmp_path: Path):
    """Test loading a traditional YOLO format dataset."""
    _create_traditional_dataset(tmp_path)

    ds = load_yolo_dataset(str(tmp_path))

    assert len(ds) == 3
    subsets = {s.subset for s in ds}
    assert Subset.TRAINING in subsets
    assert Subset.VALIDATION in subsets


def test_load_yolo_dataset_traditional_format_explicit(tmp_path: Path):
    """Test loading with explicit traditional format specification."""
    _create_traditional_dataset(tmp_path)

    ds = load_yolo_dataset(str(tmp_path), format="traditional")

    assert len(ds) == 3


def test_load_yolo_dataset_with_categories(tmp_path: Path):
    """Test that categories are loaded correctly."""
    _create_ultralytics_dataset(tmp_path)

    ds = load_yolo_dataset(str(tmp_path))

    # Check that categories are available through the schema
    labels_attr = ds.schema.attributes.get("labels")
    assert labels_attr is not None
    assert labels_attr.categories is not None
    assert labels_attr.categories.labels == ("cat", "dog")


def test_load_yolo_dataset_with_annotations(tmp_path: Path):
    """Test that annotations are parsed correctly."""
    _create_ultralytics_dataset(tmp_path)

    ds = load_yolo_dataset(str(tmp_path))

    # Find a sample with annotations
    for sample in ds:
        if sample.bboxes is not None:
            assert sample.bboxes.shape[1] == 4  # 4 values per bbox
            assert sample.labels is not None
            break
    else:
        pytest.fail("No sample with annotations found")


def test_load_yolo_dataset_missing_directory_raises(tmp_path: Path):
    """Test that loading from missing directory raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_yolo_dataset(str(tmp_path / "nonexistent"))


def test_load_yolo_dataset_unknown_format_raises(tmp_path: Path):
    """Test that unknown format raises ValueError."""
    # Empty directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(ValueError, match="Could not detect YOLO format"):
        load_yolo_dataset(str(empty_dir))


def test_load_yolo_dataset_missing_images_dir_raises(tmp_path: Path):
    """Test that missing images directory raises FileNotFoundError."""
    # Create data.yaml but no images directory
    (tmp_path / "data.yaml").write_text("names: [cat]\n")

    with pytest.raises(FileNotFoundError, match="Could not locate any image directory"):
        load_yolo_dataset(str(tmp_path), format="ultralytics")


def test_load_yolo_dataset_roboflow_split_first_layout(tmp_path: Path):
    """Test loading a Roboflow-style dataset laid out as <subset>/images and <subset>/labels."""
    _create_roboflow_dataset(tmp_path)

    ds = load_yolo_dataset(str(tmp_path))

    assert len(ds) == 3
    assert {s.subset for s in ds} == {Subset.TRAINING, Subset.VALIDATION}
    # Annotations must be picked up from the sibling labels directory
    assert all(s.bboxes is not None and len(s.bboxes) == 1 for s in ds)

    labels_attr = ds.schema.attributes.get("labels")
    assert labels_attr is not None
    assert labels_attr.categories.labels == ("cat", "dog")


def test_load_yolo_dataset_yaml_paths_take_precedence(tmp_path: Path):
    """Test that subset directories declared in data.yaml are used even with unconventional names."""
    images_dir = tmp_path / "custom" / "pictures"
    labels_dir = tmp_path / "custom" / "labels"
    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)
    _create_test_image(images_dir / "img1.jpg", 640, 480)
    (labels_dir / "img1.txt").write_text("0 0.5 0.5 0.2 0.3\n")

    yaml_data = {"names": ["cat", "dog"], "train": "custom/pictures"}
    (tmp_path / "data.yaml").write_text(yaml.dump(yaml_data))

    ds = load_yolo_dataset(str(tmp_path))

    assert len(ds) == 1
    assert ds[0].subset == Subset.TRAINING
    assert ds[0].bboxes is not None


def test_load_yolo_dataset_ignores_yaml_paths_outside_root(tmp_path: Path):
    """Test that data.yaml paths escaping the dataset root are not followed."""
    outside_dir = tmp_path / "outside" / "images"
    outside_dir.mkdir(parents=True)
    _create_test_image(outside_dir / "secret.jpg", 640, 480)

    root = tmp_path / "dataset"
    images_train = root / "images" / "train"
    images_train.mkdir(parents=True)
    _create_test_image(images_train / "img1.jpg", 640, 480)

    yaml_data = {"names": ["cat"], "train": "images/train", "val": "/etc"}
    (root / "data.yaml").write_text(yaml.dump(yaml_data))

    ds = load_yolo_dataset(str(root))

    assert len(ds) == 1
    assert Path(ds[0].image).name == "img1.jpg"


def test_load_yolo_dataset_recovers_subset_missing_from_yaml(tmp_path: Path):
    """Test that a subset on disk is loaded even when data.yaml points at a nonexistent path."""
    _create_roboflow_dataset(tmp_path)
    # Roboflow assets sometimes disagree with the on-disk layout; the loader must not drop the split.
    yaml_data = {"names": ["cat", "dog"], "train": "../train/images", "val": "../nonexistent/images"}
    (tmp_path / "data.yaml").write_text(yaml.dump(yaml_data))

    ds = load_yolo_dataset(str(tmp_path))

    assert len(ds) == 3
    assert {s.subset for s in ds} == {Subset.TRAINING, Subset.VALIDATION}


def test_load_yolo_dataset_traditional_obj_data_directory(tmp_path: Path):
    """Test loading a traditional YOLO dataset that uses the obj_data directory (unassigned subset)."""
    obj_data_dir = tmp_path / "obj_data"
    obj_data_dir.mkdir(parents=True)

    # Create images and annotations
    _create_test_image(obj_data_dir / "img1.jpg", 640, 480)
    _create_test_image(obj_data_dir / "img2.jpg", 800, 600)
    (obj_data_dir / "img1.txt").write_text("0 0.5 0.5 0.2 0.3\n")
    (obj_data_dir / "img2.txt").write_text("0 0.3 0.4 0.15 0.25\n")

    # Create obj.names
    (tmp_path / "obj.names").write_text("cat\n")

    ds = load_yolo_dataset(str(tmp_path))

    assert len(ds) == 2
    # All samples should have Subset.UNASSIGNED
    for sample in ds:
        assert sample.subset == Subset.UNASSIGNED
        assert sample.bboxes is not None
        assert sample.labels is not None


# ==========================
# save_yolo_dataset Tests
# ==========================


def test_save_yolo_dataset_ultralytics_format(tmp_path: Path):
    """Test saving in Ultralytics format."""
    # Create source images
    src_img = tmp_path / "src" / "img.jpg"
    src_img.parent.mkdir()
    _create_test_image(src_img)

    dataset = Dataset(YoloSample, categories={"labels": LabelCategories(labels=("cat", "dog"))})
    dataset.append(_make_sample(src_img, Subset.TRAINING))

    export_dir = tmp_path / "export"
    written = save_yolo_dataset(dataset, str(export_dir), format=DataFormat.YOLO_ULTRALYTICS)

    # Check structure
    assert (export_dir / "data.yaml").exists()
    assert (export_dir / "images" / "train").is_dir()
    assert (export_dir / "labels" / "train").is_dir()
    assert "data.yaml" in written


def test_save_yolo_dataset_traditional_format(tmp_path: Path):
    """Test saving in traditional format."""
    src_img = tmp_path / "src" / "img.jpg"
    src_img.parent.mkdir()
    _create_test_image(src_img)

    dataset = Dataset(YoloSample, categories={"labels": LabelCategories(labels=("cat", "dog"))})
    dataset.append(_make_sample(src_img, Subset.TRAINING))

    export_dir = tmp_path / "export"
    written = save_yolo_dataset(dataset, str(export_dir), format=DataFormat.YOLO)

    # Check structure
    assert (export_dir / "obj.names").exists()
    assert (export_dir / "obj.data").exists()
    assert (export_dir / "obj_train_data").is_dir()
    assert "obj.names" in written
    assert "obj.data" in written


def test_save_and_reload_ultralytics(tmp_path: Path):
    """Test roundtrip: save and reload Ultralytics format."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_img = src_dir / "img.jpg"
    _create_test_image(src_img)

    original_dataset = Dataset(YoloSample, categories={"labels": LabelCategories(labels=("cat", "dog"))})
    original_dataset.append(
        YoloSample(
            image=str(src_img),
            image_info=ImageInfo(height=480, width=640),
            bboxes=np.array([[320.0, 240.0, 64.0, 48.0]], dtype=np.float32),
            labels=np.array([0], dtype=np.int32),
            subset=Subset.TRAINING,
        )
    )

    export_dir = tmp_path / "export"
    save_yolo_dataset(original_dataset, str(export_dir), format=DataFormat.YOLO_ULTRALYTICS)

    # Reload
    reloaded_dataset = load_yolo_dataset(str(export_dir))

    assert len(reloaded_dataset) == 1
    sample = reloaded_dataset[0]
    assert sample.subset == Subset.TRAINING
    assert sample.bboxes is not None
    assert sample.labels is not None


def test_save_and_reload_traditional(tmp_path: Path):
    """Test roundtrip: save and reload traditional format."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_img = src_dir / "img.jpg"
    _create_test_image(src_img)

    original_dataset = Dataset(YoloSample, categories={"labels": LabelCategories(labels=("cat", "dog"))})
    original_dataset.append(
        YoloSample(
            image=str(src_img),
            image_info=ImageInfo(height=480, width=640),
            bboxes=np.array([[320.0, 240.0, 64.0, 48.0]], dtype=np.float32),
            labels=np.array([0], dtype=np.int32),
            subset=Subset.TRAINING,
        )
    )

    export_dir = tmp_path / "export"
    save_yolo_dataset(original_dataset, str(export_dir), format=DataFormat.YOLO)

    # Reload
    reloaded_dataset = load_yolo_dataset(str(export_dir))

    assert len(reloaded_dataset) == 1
    sample = reloaded_dataset[0]
    assert sample.subset == Subset.TRAINING
    assert sample.bboxes is not None
    assert sample.labels is not None


def test_save_yolo_dataset_unsupported_format_raises(tmp_path: Path):
    """Test that unsupported format raises ValueError."""
    dataset = Dataset(YoloSample, categories={"labels": LabelCategories(labels=("cat",))})

    with pytest.raises(ValueError, match="Unsupported YOLO format"):
        save_yolo_dataset(dataset, str(tmp_path), format=DataFormat.COCO)


# ==========================
# Integration Tests
# ==========================


def test_annotation_values_preserved_roundtrip(tmp_path: Path):
    """Test that annotation values are preserved through roundtrip."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_img = src_dir / "img.jpg"
    _create_test_image(src_img, 1000, 800)

    # Create dataset with specific annotations
    original_bboxes = np.array(
        [
            [500.0, 400.0, 200.0, 160.0],  # center at 50%, 50% of image
            [250.0, 200.0, 100.0, 80.0],  # center at 25%, 25% of image
        ],
        dtype=np.float32,
    )
    original_labels = np.array([0, 1], dtype=np.int32)

    original_dataset = Dataset(YoloSample, categories={"labels": LabelCategories(labels=("cat", "dog"))})
    original_dataset.append(
        YoloSample(
            image=str(src_img),
            image_info=ImageInfo(height=800, width=1000),
            bboxes=original_bboxes,
            labels=original_labels,
            subset=Subset.TRAINING,
        )
    )

    export_dir = tmp_path / "export"
    save_yolo_dataset(original_dataset, str(export_dir), format=DataFormat.YOLO_ULTRALYTICS)

    # Reload
    reloaded_dataset = load_yolo_dataset(str(export_dir))

    assert len(reloaded_dataset) == 1
    sample = reloaded_dataset[0]

    # Verify annotations are close to original (some precision loss expected)
    np.testing.assert_array_almost_equal(sample.bboxes, original_bboxes, decimal=0)
    np.testing.assert_array_equal(sample.labels, original_labels)


def test_multiple_images_with_varying_annotations(tmp_path: Path):
    """Test dataset with multiple images having different numbers of annotations."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    dataset = Dataset(YoloSample, categories={"labels": LabelCategories(labels=("cat", "dog", "bird"))})

    # Image with 1 annotation
    img1 = src_dir / "img1.jpg"
    _create_test_image(img1)
    dataset.append(
        YoloSample(
            image=str(img1),
            image_info=ImageInfo(height=480, width=640),
            bboxes=np.array([[100.0, 100.0, 50.0, 50.0]], dtype=np.float32),
            labels=np.array([0], dtype=np.int32),
            subset=Subset.TRAINING,
        )
    )

    # Image with 3 annotations
    img2 = src_dir / "img2.jpg"
    _create_test_image(img2)
    dataset.append(
        YoloSample(
            image=str(img2),
            image_info=ImageInfo(height=480, width=640),
            bboxes=np.array(
                [
                    [100.0, 100.0, 50.0, 50.0],
                    [200.0, 200.0, 60.0, 40.0],
                    [300.0, 150.0, 30.0, 80.0],
                ],
                dtype=np.float32,
            ),
            labels=np.array([0, 1, 2], dtype=np.int32),
            subset=Subset.TRAINING,
        )
    )

    # Image with no annotations
    img3 = src_dir / "img3.jpg"
    _create_test_image(img3)
    dataset.append(
        YoloSample(
            image=str(img3),
            image_info=ImageInfo(height=480, width=640),
            bboxes=None,
            labels=None,
            subset=Subset.VALIDATION,
        )
    )

    export_dir = tmp_path / "export"
    save_yolo_dataset(dataset, str(export_dir), format=DataFormat.YOLO_ULTRALYTICS)

    # Reload
    reloaded = load_yolo_dataset(str(export_dir))

    assert len(reloaded) == 3

    # Count annotations
    total_annotations = sum(len(s.labels) if s.labels is not None else 0 for s in reloaded)
    assert total_annotations == 4  # 1 + 3 + 0


def test_empty_dataset_handling(tmp_path: Path):
    """Test saving and loading an empty dataset."""
    dataset = Dataset(YoloSample, categories={"labels": LabelCategories(labels=("cat",))})

    export_dir = tmp_path / "export"
    save_yolo_dataset(dataset, str(export_dir), format=DataFormat.YOLO_ULTRALYTICS)

    # The data.yaml should still be created
    assert (export_dir / "data.yaml").exists()
