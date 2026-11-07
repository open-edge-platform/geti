# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for Ultralytics YOLO classification I/O functions.
"""

from pathlib import Path

import pytest

from getidata import Dataset
from getidata.categories import LabelCategories
from getidata.data_formats.base import DataFormat
from getidata.data_formats.yolo.io import is_yolo_cls_format, load_yolo_cls_dataset, save_yolo_cls_dataset
from getidata.data_formats.yolo.sample import YoloClsSample
from getidata.export_import import export_dataset, import_dataset
from getidata.fields import ImageInfo, Subset
from getidata.format_detection import detect_dataset_format


def _create_test_image(path: Path, width: int = 640, height: int = 480) -> None:
    """Create a minimal valid image file for testing."""
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), color="red")
    img.save(path)


def _create_cls_dataset(root: Path) -> None:
    """Create a minimal Ultralytics YOLO classification dataset structure."""
    _create_test_image(root / "train" / "cat" / "img1.jpg")
    _create_test_image(root / "train" / "dog" / "img2.jpg")
    _create_test_image(root / "val" / "cat" / "img3.jpg")


def _make_cls_sample(image_path: Path, label: int, subset: Subset = Subset.TRAINING) -> YoloClsSample:
    """Create a test YoloClsSample."""
    return YoloClsSample(
        image=str(image_path),
        image_info=ImageInfo(height=480, width=640),
        label=label,
        subset=subset,
    )


# ==========================
# Detection Tests
# ==========================


def test_is_yolo_cls_format_positive(tmp_path: Path):
    """Test that the classification layout is detected."""
    _create_cls_dataset(tmp_path)

    assert is_yolo_cls_format(tmp_path)


def test_detect_dataset_format_yolo_cls(tmp_path: Path):
    """Test that auto-detection returns the classification format."""
    _create_cls_dataset(tmp_path)

    assert detect_dataset_format(tmp_path) == DataFormat.YOLO_ULTRALYTICS_CLS


def test_is_yolo_cls_format_valid_alias(tmp_path: Path):
    """Test that the 'valid' spelling of the validation split is accepted."""
    _create_test_image(tmp_path / "train" / "cat" / "img1.jpg")
    _create_test_image(tmp_path / "valid" / "cat" / "img2.jpg")

    assert is_yolo_cls_format(tmp_path)

    ds = load_yolo_cls_dataset(str(tmp_path))
    subsets = {sample.subset for sample in ds}
    assert subsets == {Subset.TRAINING, Subset.VALIDATION}


def test_is_yolo_cls_format_negative_empty_dirs(tmp_path: Path):
    """Test that split directories without images are not detected."""
    (tmp_path / "train" / "cat").mkdir(parents=True)
    (tmp_path / "val" / "dog").mkdir(parents=True)

    assert not is_yolo_cls_format(tmp_path)
    assert detect_dataset_format(tmp_path) == DataFormat.UNKNOWN


def test_is_yolo_cls_format_negative_images_directly_in_split(tmp_path: Path):
    """Test that split directories with loose images (no class dirs) are not detected."""
    _create_test_image(tmp_path / "train" / "img1.jpg")

    assert not is_yolo_cls_format(tmp_path)


def test_is_yolo_cls_format_negative_ultralytics_detection(tmp_path: Path):
    """Test that the Ultralytics detection layout is not misdetected as classification."""
    _create_test_image(tmp_path / "images" / "train" / "img1.jpg")
    (tmp_path / "labels" / "train").mkdir(parents=True)
    (tmp_path / "labels" / "train" / "img1.txt").write_text("0 0.5 0.5 0.2 0.3\n")
    (tmp_path / "data.yaml").write_text("names: [cat]\ntrain: images/train\n")

    assert not is_yolo_cls_format(tmp_path)
    assert detect_dataset_format(tmp_path) == DataFormat.YOLO


def test_is_yolo_cls_format_negative_split_first_detection(tmp_path: Path):
    """Test that the split-first detection layout (train/images + train/labels) is not misdetected."""
    _create_test_image(tmp_path / "train" / "images" / "img1.jpg")
    (tmp_path / "train" / "labels").mkdir(parents=True)
    (tmp_path / "train" / "labels" / "img1.txt").write_text("0 0.5 0.5 0.2 0.3\n")

    assert not is_yolo_cls_format(tmp_path)
    assert detect_dataset_format(tmp_path) == DataFormat.UNKNOWN


def test_is_yolo_cls_format_negative_coco_layout(tmp_path: Path):
    """Test that a flat images directory (COCO-style) is not misdetected as classification."""
    _create_test_image(tmp_path / "images" / "img1.jpg")

    assert not is_yolo_cls_format(tmp_path)


def test_is_yolo_cls_format_class_named_images(tmp_path: Path):
    """Test that a class literally named 'images' is detected when no paired 'labels' dir exists."""
    _create_test_image(tmp_path / "train" / "cat" / "img1.jpg")
    _create_test_image(tmp_path / "train" / "images" / "img2.jpg")

    assert is_yolo_cls_format(tmp_path)
    assert detect_dataset_format(tmp_path) == DataFormat.YOLO_ULTRALYTICS_CLS

    ds = load_yolo_cls_dataset(str(tmp_path))
    assert ds.schema.attributes["label"].categories.labels == ("cat", "images")
    assert len(ds) == 2


def test_is_yolo_cls_format_class_named_labels_only(tmp_path: Path):
    """Test that a dataset whose only class is named 'labels' is detected and loads."""
    _create_test_image(tmp_path / "train" / "labels" / "img1.jpg")

    assert is_yolo_cls_format(tmp_path)
    assert detect_dataset_format(tmp_path) == DataFormat.YOLO_ULTRALYTICS_CLS

    ds = load_yolo_cls_dataset(str(tmp_path))
    assert ds.schema.attributes["label"].categories.labels == ("labels",)
    assert len(ds) == 1


def test_is_yolo_cls_format_reserved_names_with_paired_layout(tmp_path: Path):
    """Test that 'images' next to a 'labels' sibling holding label files stays reserved."""
    _create_test_image(tmp_path / "train" / "images" / "img1.jpg")
    _create_test_image(tmp_path / "train" / "cat" / "img2.jpg")
    (tmp_path / "train" / "labels").mkdir()
    (tmp_path / "train" / "labels" / "img1.txt").write_text("0 0.5 0.5 0.2 0.3\n")

    ds = load_yolo_cls_dataset(str(tmp_path))
    assert ds.schema.attributes["label"].categories.labels == ("cat",)
    assert len(ds) == 1


def test_is_yolo_cls_format_classes_named_images_and_labels(tmp_path: Path):
    """Test that classes named 'images' and 'labels' are both detected when they hold images."""
    _create_test_image(tmp_path / "train" / "images" / "img1.jpg")
    _create_test_image(tmp_path / "train" / "labels" / "img2.jpg")

    assert is_yolo_cls_format(tmp_path)

    ds = load_yolo_cls_dataset(str(tmp_path))
    assert ds.schema.attributes["label"].categories.labels == ("images", "labels")
    assert len(ds) == 2


# ==========================
# load_yolo_cls_dataset Tests
# ==========================


def test_load_yolo_cls_dataset(tmp_path: Path):
    """Test loading a classification dataset."""
    _create_cls_dataset(tmp_path)

    ds = load_yolo_cls_dataset(str(tmp_path))

    assert len(ds) == 3
    assert ds.dtype is YoloClsSample

    label_categories = ds.schema.attributes["label"].categories
    # Class names are collected across subsets and sorted alphabetically
    assert label_categories.labels == ("cat", "dog")

    by_image = {Path(sample.image).name: sample for sample in ds}
    assert by_image["img1.jpg"].label == label_categories.find("cat")[0]
    assert by_image["img2.jpg"].label == label_categories.find("dog")[0]
    assert by_image["img1.jpg"].subset == Subset.TRAINING
    assert by_image["img2.jpg"].subset == Subset.TRAINING
    assert by_image["img3.jpg"].subset == Subset.VALIDATION

    sample = by_image["img1.jpg"]
    assert sample.image_info.height == 480
    assert sample.image_info.width == 640


def test_load_yolo_cls_dataset_missing_root(tmp_path: Path):
    """Test that a missing root directory raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_yolo_cls_dataset(str(tmp_path / "missing"))


def test_load_yolo_cls_dataset_no_splits(tmp_path: Path):
    """Test that a directory without classification splits raises FileNotFoundError."""
    (tmp_path / "train" / "cat").mkdir(parents=True)  # no images anywhere

    with pytest.raises(FileNotFoundError, match="classification split"):
        load_yolo_cls_dataset(str(tmp_path))


def test_import_dataset_auto_detects_yolo_cls(tmp_path: Path):
    """Test that import_dataset auto-detects and loads the classification format."""
    _create_cls_dataset(tmp_path)

    ds = import_dataset(str(tmp_path))

    assert ds.dtype is YoloClsSample
    assert len(ds) == 3


def test_import_dataset_explicit_yolo_cls_format(tmp_path: Path):
    """Test loading with an explicit data_format."""
    _create_cls_dataset(tmp_path)

    ds = import_dataset(str(tmp_path), data_format=DataFormat.YOLO_ULTRALYTICS_CLS)

    assert ds.dtype is YoloClsSample
    assert len(ds) == 3


# ==========================
# save_yolo_cls_dataset Tests
# ==========================


def test_save_yolo_cls_dataset(tmp_path: Path):
    """Test saving a classification dataset."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    _create_test_image(src_dir / "img1.jpg")

    dataset = Dataset(YoloClsSample, categories={"label": LabelCategories(labels=("cat", "dog"))})
    dataset.append(_make_cls_sample(src_dir / "img1.jpg", label=1, subset=Subset.TRAINING))

    export_dir = tmp_path / "export"
    written = save_yolo_cls_dataset(dataset, str(export_dir))

    assert (export_dir / "train" / "dog" / "img1.jpg").exists()
    assert not (export_dir / "train" / "cat").exists()
    assert written == {"train": export_dir / "train"}


def test_save_yolo_cls_dataset_skips_unlabeled_samples(tmp_path: Path):
    """Test that samples without a label are skipped, as the format cannot represent them."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    _create_test_image(src_dir / "img1.jpg")
    _create_test_image(src_dir / "img2.jpg")

    dataset = Dataset(YoloClsSample, categories={"label": LabelCategories(labels=("cat", "dog"))})
    dataset.append(_make_cls_sample(src_dir / "img1.jpg", label=0, subset=Subset.TRAINING))
    dataset.append(
        YoloClsSample(
            image=str(src_dir / "img2.jpg"),
            image_info=ImageInfo(height=480, width=640),
            label=None,
            subset=Subset.TRAINING,
        )
    )

    export_dir = tmp_path / "export"
    save_yolo_cls_dataset(dataset, str(export_dir))

    assert (export_dir / "train" / "cat" / "img1.jpg").exists()
    assert not (export_dir / "train" / "cat" / "img2.jpg").exists()


def test_save_yolo_cls_dataset_name_collision(tmp_path: Path):
    """Test that colliding file names within a class directory get a numeric suffix."""
    src_dir_a = tmp_path / "a"
    src_dir_b = tmp_path / "b"
    _create_test_image(src_dir_a / "img.jpg")
    _create_test_image(src_dir_b / "img.jpg")

    dataset = Dataset(YoloClsSample, categories={"label": LabelCategories(labels=("cat",))})
    dataset.append(_make_cls_sample(src_dir_a / "img.jpg", label=0, subset=Subset.TRAINING))
    dataset.append(_make_cls_sample(src_dir_b / "img.jpg", label=0, subset=Subset.TRAINING))

    export_dir = tmp_path / "export"
    save_yolo_cls_dataset(dataset, str(export_dir))

    assert (export_dir / "train" / "cat" / "img.jpg").exists()
    assert (export_dir / "train" / "cat" / "img_1.jpg").exists()


def test_save_yolo_cls_dataset_same_name_different_classes(tmp_path: Path):
    """Test that the same file name can be used in different class directories."""
    src_dir = tmp_path / "src"
    _create_test_image(src_dir / "img.jpg")

    dataset = Dataset(YoloClsSample, categories={"label": LabelCategories(labels=("cat", "dog"))})
    dataset.append(_make_cls_sample(src_dir / "img.jpg", label=0, subset=Subset.TRAINING))
    dataset.append(_make_cls_sample(src_dir / "img.jpg", label=1, subset=Subset.TRAINING))

    export_dir = tmp_path / "export"
    save_yolo_cls_dataset(dataset, str(export_dir))

    assert (export_dir / "train" / "cat" / "img.jpg").exists()
    assert (export_dir / "train" / "dog" / "img.jpg").exists()


@pytest.mark.parametrize(
    "class_name",
    [
        "../escaped",
        "sub/escaped",
        "sub\\escaped",
        "/escaped",
        "C:\\escaped",
        "C:escaped",
        "\\\\server\\share",
        "..",
        ".",
    ],
)
def test_save_yolo_cls_dataset_skips_unsafe_class_names(tmp_path: Path, class_name: str):
    """Test that class names that cannot be a single safe directory are skipped, not written."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    _create_test_image(src_dir / "img_ok.jpg")
    _create_test_image(src_dir / "img_evil.jpg")

    dataset = Dataset(YoloClsSample, categories={"label": LabelCategories(labels=("ok", class_name))})
    dataset.append(_make_cls_sample(src_dir / "img_ok.jpg", label=0, subset=Subset.TRAINING))
    dataset.append(_make_cls_sample(src_dir / "img_evil.jpg", label=1, subset=Subset.TRAINING))

    export_dir = tmp_path / "export"
    save_yolo_cls_dataset(dataset, str(export_dir))

    assert (export_dir / "train" / "ok" / "img_ok.jpg").exists()
    # The unsafe class must not write its images anywhere, inside or outside the export root
    assert list(export_dir.rglob("img_evil*")) == []
    assert [p.relative_to(tmp_path).as_posix() for p in sorted(tmp_path.rglob("img_evil*"))] == ["src/img_evil.jpg"]


# ==========================
# Round-trip Tests
# ==========================


def test_save_yolo_cls_dataset_skips_absolute_class_name(tmp_path: Path):
    """Test that an absolute class name cannot make the export write outside the export root."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    _create_test_image(src_dir / "img.jpg")

    dataset = Dataset(YoloClsSample, categories={"label": LabelCategories(labels=(str(tmp_path / "escaped"),))})
    dataset.append(_make_cls_sample(src_dir / "img.jpg", label=0, subset=Subset.TRAINING))

    export_dir = tmp_path / "export"
    save_yolo_cls_dataset(dataset, str(export_dir))

    assert not (tmp_path / "escaped" / "img.jpg").exists()
    assert list(export_dir.rglob("img.jpg")) == []


def test_save_and_reload_yolo_cls_reserved_class_names(tmp_path: Path):
    """Test that a class literally named 'images' round-trips through save and reload."""
    _create_test_image(tmp_path / "train" / "images" / "img1.jpg")
    original = load_yolo_cls_dataset(str(tmp_path))

    export_dir = tmp_path / "export"
    save_yolo_cls_dataset(original, str(export_dir))

    reloaded = load_yolo_cls_dataset(str(export_dir))

    assert reloaded.schema.attributes["label"].categories.labels == ("images",)
    assert len(reloaded) == len(original)
    assert reloaded[0].label == original[0].label


def test_save_and_reload_yolo_cls(tmp_path: Path):
    """Test round-trip: save and reload a classification dataset."""
    _create_cls_dataset(tmp_path)

    original = load_yolo_cls_dataset(str(tmp_path))

    export_dir = tmp_path / "export"
    save_yolo_cls_dataset(original, str(export_dir))

    reloaded = load_yolo_cls_dataset(str(export_dir))

    assert len(reloaded) == len(original)
    original_by_name = {Path(sample.image).name: sample for sample in original}
    for sample in reloaded:
        original_sample = original_by_name[Path(sample.image).name]
        assert sample.label == original_sample.label
        assert sample.subset == original_sample.subset


def test_export_dataset_yolo_cls_format(tmp_path: Path):
    """Test the export_dataset entry point with the classification format."""
    _create_cls_dataset(tmp_path)

    original = load_yolo_cls_dataset(str(tmp_path))

    export_dir = tmp_path / "export"
    export_dataset(original, output_path=str(export_dir), data_format=DataFormat.YOLO_ULTRALYTICS_CLS)

    assert (export_dir / "train" / "cat").is_dir()
    assert (export_dir / "train" / "dog").is_dir()
    assert (export_dir / "val" / "cat").is_dir()

    reloaded = import_dataset(str(export_dir))
    assert reloaded.dtype is YoloClsSample
    assert len(reloaded) == len(original)


def test_export_dataset_yolo_cls_format_as_zip(tmp_path: Path):
    """Test exporting the classification format as a zip archive."""
    _create_cls_dataset(tmp_path)

    original = load_yolo_cls_dataset(str(tmp_path))

    zip_path = tmp_path / "export.zip"
    export_dataset(original, output_path=str(zip_path), data_format=DataFormat.YOLO_ULTRALYTICS_CLS, as_zip=True)

    assert zip_path.exists()

    reloaded = import_dataset(str(zip_path), extract_dir=tmp_path / "extracted")
    assert reloaded.dtype is YoloClsSample
    assert len(reloaded) == len(original)
