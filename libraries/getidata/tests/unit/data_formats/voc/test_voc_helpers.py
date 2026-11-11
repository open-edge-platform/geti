# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for VOC helper functions.
"""

from pathlib import Path
from xml.etree.ElementTree import Element

import numpy as np
import pytest

from getidata.categories import LabelCategories
from getidata.data_formats.voc.constants import VOC_LABELS
from getidata.data_formats.voc.helpers import (
    _create_object_element,
    _create_voc_xml_annotation,
    _detect_classification_label_files,
    _detect_voc_subsets,
    _find_image_file,
    _get_image_size,
    _load_voc_categories,
    _parse_classification_labels,
    _parse_subset_list,
    _parse_voc_annotation,
    _parse_voc_labelmap,
    _write_labelmap,
    _write_voc_xml,
)
from getidata.data_formats.voc.sample import VocSample
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
    _create_test_image(img_path)

    result = _find_image_file(tmp_path, "test")
    assert result == img_path


def test_find_image_file_finds_png_image(tmp_path: Path):
    """Test finding a .png image file."""
    img_path = tmp_path / "test.png"
    _create_test_image(img_path)

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
# _parse_voc_labelmap Tests
# ==============================


def test_parse_voc_labelmap_parses_valid_labelmap(tmp_path: Path):
    """Test parsing a valid VOC labelmap file."""
    labelmap_path = tmp_path / "labelmap.txt"
    labelmap_path.write_text("# comment\ndog:255,0,0::\ncat:0,255,0::\n")

    labels = _parse_voc_labelmap(labelmap_path)

    assert labels == ["dog", "cat"]


def test_parse_voc_labelmap_skips_comments_and_empty_lines(tmp_path: Path):
    """Test that comments and empty lines are skipped."""
    labelmap_path = tmp_path / "labelmap.txt"
    labelmap_path.write_text("# comment\n\nperson:::\n\n# another comment\ncar:::\n")

    labels = _parse_voc_labelmap(labelmap_path)

    assert labels == ["person", "car"]


def test_parse_voc_labelmap_handles_empty_file(tmp_path: Path):
    """Test handling an empty labelmap file."""
    labelmap_path = tmp_path / "labelmap.txt"
    labelmap_path.write_text("")

    labels = _parse_voc_labelmap(labelmap_path)

    assert labels == []


# ==============================
# _load_voc_categories Tests
# ==============================


def test_load_voc_categories_uses_defaults_when_no_labelmap(tmp_path: Path):
    """Test that default VOC labels are used when no labelmap exists."""
    categories = _load_voc_categories(tmp_path)

    assert categories.labels == VOC_LABELS


def test_load_voc_categories_loads_from_labelmap(tmp_path: Path):
    """Test loading categories from a labelmap file."""
    labelmap_path = tmp_path / "labelmap.txt"
    labelmap_path.write_text("custom1:::\ncustom2:::\n")

    categories = _load_voc_categories(tmp_path)

    assert categories.labels == ("custom1", "custom2")


def test_load_voc_categories_loads_from_meta_file(tmp_path: Path):
    """Test loading categories from a dataset_meta.json file."""
    import json

    meta_path = tmp_path / "dataset_meta.json"
    meta_path.write_text(json.dumps({"labels": ["label1", "label2", "label3"]}))

    categories = _load_voc_categories(tmp_path)

    assert categories.labels == ("label1", "label2", "label3")


# ==============================
# _parse_subset_list Tests
# ==============================


def test_parse_subset_list_parses_image_ids(tmp_path: Path):
    """Test parsing a simple subset file with image IDs."""
    subset_file = tmp_path / "train.txt"
    subset_file.write_text("image1\nimage2\nimage3\n")

    image_ids = _parse_subset_list(subset_file)

    assert image_ids == ["image1", "image2", "image3"]


def test_parse_subset_list_handles_classification_format(tmp_path: Path):
    """Test parsing subset file with classification labels (image_id label format)."""
    subset_file = tmp_path / "train.txt"
    subset_file.write_text("image1 1\nimage2 -1\nimage3 0\n")

    image_ids = _parse_subset_list(subset_file)

    # Should only extract image IDs, not the labels
    assert image_ids == ["image1", "image2", "image3"]


def test_parse_subset_list_skips_comments_and_empty_lines(tmp_path: Path):
    """Test that comments and empty lines are skipped."""
    subset_file = tmp_path / "train.txt"
    subset_file.write_text("# comment\n\nimage1\n\nimage2\n")

    image_ids = _parse_subset_list(subset_file)

    assert image_ids == ["image1", "image2"]


# ==============================
# _detect_voc_subsets Tests
# ==============================


def test_detect_voc_subsets_finds_subsets(tmp_path: Path):
    """Test detecting VOC subsets from ImageSets/Main directory."""
    imagesets_main = tmp_path / "ImageSets" / "Main"
    imagesets_main.mkdir(parents=True)
    (imagesets_main / "train.txt").write_text("image1\nimage2\n")
    (imagesets_main / "val.txt").write_text("image3\n")

    subsets = _detect_voc_subsets(tmp_path)

    assert "train" in subsets
    assert "val" in subsets
    assert subsets["train"] == imagesets_main / "train.txt"
    assert subsets["val"] == imagesets_main / "val.txt"


def test_detect_voc_subsets_returns_empty_when_no_imagesets(tmp_path: Path):
    """Test that empty dict is returned when ImageSets/Main doesn't exist."""
    subsets = _detect_voc_subsets(tmp_path)

    assert subsets == {}


# ==============================
# _parse_voc_annotation Tests
# ==============================


def test_parse_voc_annotation_parses_valid_xml(tmp_path: Path):
    """Test parsing a valid VOC XML annotation file."""
    anno_path = tmp_path / "test.xml"
    anno_path.write_text("""
<annotation>
    <size>
        <width>640</width>
        <height>480</height>
    </size>
    <object>
        <name>person</name>
        <bndbox>
            <xmin>100</xmin>
            <ymin>100</ymin>
            <xmax>200</xmax>
            <ymax>200</ymax>
        </bndbox>
        <difficult>0</difficult>
        <truncated>1</truncated>
        <occluded>0</occluded>
        <pose>Frontal</pose>
    </object>
</annotation>
    """)

    categories = LabelCategories(labels=VOC_LABELS)
    result = _parse_voc_annotation(anno_path, categories)

    assert result["width"] == 640
    assert result["height"] == 480
    assert len(result["bboxes"]) == 1
    assert result["bboxes"][0] == [100.0, 100.0, 200.0, 200.0]
    assert result["labels"][0] == VOC_LABELS.index("person")
    assert result["difficult"][0] is False
    assert result["truncated"][0] is True
    assert result["occluded"][0] is False
    assert result["pose"][0] == "Frontal"


def test_parse_voc_annotation_handles_missing_file(tmp_path: Path):
    """Test that missing annotation file returns empty result."""
    anno_path = tmp_path / "nonexistent.xml"
    categories = LabelCategories(labels=VOC_LABELS)

    result = _parse_voc_annotation(anno_path, categories)

    assert result["width"] == 0
    assert result["height"] == 0
    assert result["bboxes"] == []
    assert result["labels"] == []


def test_parse_voc_annotation_handles_multiple_objects(tmp_path: Path):
    """Test parsing annotation with multiple objects."""
    anno_path = tmp_path / "test.xml"
    anno_path.write_text("""
<annotation>
    <size>
        <width>640</width>
        <height>480</height>
    </size>
    <object>
        <name>person</name>
        <bndbox>
            <xmin>100</xmin>
            <ymin>100</ymin>
            <xmax>200</xmax>
            <ymax>200</ymax>
        </bndbox>
    </object>
    <object>
        <name>dog</name>
        <bndbox>
            <xmin>300</xmin>
            <ymin>300</ymin>
            <xmax>400</xmax>
            <ymax>400</ymax>
        </bndbox>
    </object>
</annotation>
    """)

    categories = LabelCategories(labels=VOC_LABELS)
    result = _parse_voc_annotation(anno_path, categories)

    assert len(result["bboxes"]) == 2
    assert len(result["labels"]) == 2


# ==============================
# _write_labelmap Tests
# ==============================


def test_write_labelmap_writes_valid_format(tmp_path: Path):
    """Test writing a VOC labelmap file."""
    output_path = tmp_path / "labelmap.txt"
    categories = LabelCategories(labels=("dog", "cat", "bird"))

    _write_labelmap(categories, output_path)

    content = output_path.read_text()
    assert "# label:color_rgb:parts:actions" in content
    assert "dog:::" in content
    assert "cat:::" in content
    assert "bird:::" in content


# ==============================
# _create_voc_xml_annotation Tests
# ==============================


def test_create_voc_xml_annotation_creates_valid_xml():
    """Test creating a VOC XML annotation element."""
    sample = VocSample(
        image="/path/to/image.jpg",
        image_info=ImageInfo(height=480, width=640),
        bboxes=np.array([[100, 100, 200, 200]], dtype=np.float32),
        labels=np.array([1], dtype=np.uint32),
        difficult=np.array([False]),
        truncated=np.array([True]),
        occluded=np.array([False]),
        pose=np.array(["Frontal"], dtype=object),
        subset=Subset.TRAINING,
    )
    categories = LabelCategories(labels=VOC_LABELS)

    root = _create_voc_xml_annotation(sample, "image.jpg", categories)

    assert root.tag == "annotation"
    assert root.find("filename").text == "image.jpg"
    assert root.find("size/width").text == "640"
    assert root.find("size/height").text == "480"

    obj = root.find("object")
    assert obj is not None
    assert obj.find("name").text == VOC_LABELS[1]  # Label index 1
    assert obj.find("bndbox/xmin").text == "100"
    assert obj.find("bndbox/ymin").text == "100"
    assert obj.find("bndbox/xmax").text == "200"
    assert obj.find("bndbox/ymax").text == "200"


def test_create_voc_xml_annotation_handles_no_objects():
    """Test creating XML annotation with no objects."""
    sample = VocSample(
        image="/path/to/image.jpg",
        image_info=ImageInfo(height=480, width=640),
        bboxes=None,
        labels=None,
        difficult=None,
        truncated=None,
        occluded=None,
        pose=None,
        subset=Subset.TRAINING,
    )
    categories = LabelCategories(labels=VOC_LABELS)

    root = _create_voc_xml_annotation(sample, "image.jpg", categories)

    assert root.tag == "annotation"
    assert root.find("object") is None


# ==============================
# _write_voc_xml Tests
# ==============================


def test_write_voc_xml_creates_file(tmp_path: Path):
    """Test writing VOC XML to a file."""
    root = Element("annotation")
    filename = Element("filename")
    filename.text = "test.jpg"
    root.append(filename)

    output_path = tmp_path / "test.xml"
    _write_voc_xml(root, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "<annotation>" in content
    assert "<filename>test.jpg</filename>" in content


# ======================================
# Classification-only (no bbox) Tests
# ======================================


def test_parse_voc_annotation_parses_objects_without_bndbox(tmp_path: Path):
    """Test that objects without bounding boxes are still parsed for labels and attributes."""
    anno_path = tmp_path / "test.xml"
    anno_path.write_text("""
<annotation>
    <size>
        <width>640</width>
        <height>480</height>
    </size>
    <object>
        <name>person</name>
        <difficult>1</difficult>
        <truncated>0</truncated>
        <occluded>1</occluded>
        <pose>Frontal</pose>
    </object>
</annotation>
    """)

    categories = LabelCategories(labels=VOC_LABELS)
    result = _parse_voc_annotation(anno_path, categories)

    assert result["width"] == 640
    assert result["height"] == 480
    # Object should be parsed even without bndbox
    assert len(result["labels"]) == 1
    assert result["labels"][0] == VOC_LABELS.index("person")
    # No bounding boxes should be present
    assert len(result["bboxes"]) == 0
    # Attributes should still be parsed
    assert result["difficult"][0] is True
    assert result["truncated"][0] is False
    assert result["occluded"][0] is True
    assert result["pose"][0] == "Frontal"


def test_parse_voc_annotation_mixed_objects_with_and_without_bndbox(tmp_path: Path):
    """Test parsing annotation with both bbox and non-bbox objects."""
    anno_path = tmp_path / "test.xml"
    anno_path.write_text("""
<annotation>
    <size>
        <width>640</width>
        <height>480</height>
    </size>
    <object>
        <name>person</name>
        <bndbox>
            <xmin>100</xmin>
            <ymin>100</ymin>
            <xmax>200</xmax>
            <ymax>200</ymax>
        </bndbox>
    </object>
    <object>
        <name>dog</name>
        <difficult>1</difficult>
    </object>
</annotation>
    """)

    categories = LabelCategories(labels=VOC_LABELS)
    result = _parse_voc_annotation(anno_path, categories)

    # Only objects with a bounding box should be included in object-level data
    assert len(result["labels"]) == 1
    assert result["labels"][0] == VOC_LABELS.index("person")
    assert len(result["bboxes"]) == 1
    assert result["bboxes"][0] == [100.0, 100.0, 200.0, 200.0]


def test_create_voc_xml_annotation_classification_only():
    """Test creating XML annotation for classification-only samples (labels but no bboxes)."""
    sample = VocSample(
        image="/path/to/image.jpg",
        image_info=ImageInfo(height=480, width=640),
        bboxes=None,
        labels=np.array([0, 2], dtype=np.uint32),
        difficult=np.array([False, True]),
        truncated=np.array([False, False]),
        occluded=np.array([False, False]),
        pose=np.array(["Unspecified", "Unspecified"], dtype=object),
        subset=Subset.TRAINING,
    )
    categories = LabelCategories(labels=VOC_LABELS)

    root = _create_voc_xml_annotation(sample, "image.jpg", categories)

    assert root.tag == "annotation"
    objects = root.findall("object")
    assert len(objects) == 2

    # Check label names
    assert objects[0].find("name").text == VOC_LABELS[0]
    assert objects[1].find("name").text == VOC_LABELS[2]

    # No bndbox elements should be present
    assert objects[0].find("bndbox") is None
    assert objects[1].find("bndbox") is None

    # Attributes should still be set
    assert objects[1].find("difficult").text == "1"


def test_create_object_element_with_bbox():
    """Test _create_object_element creates bndbox when bbox is provided."""
    sample = VocSample(
        image="/path/to/image.jpg",
        image_info=ImageInfo(height=480, width=640),
        bboxes=np.array([[10, 20, 30, 40]], dtype=np.float32),
        labels=np.array([1], dtype=np.uint32),
        difficult=np.array([True]),
        truncated=np.array([False]),
        occluded=np.array([True]),
        pose=np.array(["Left"], dtype=object),
        subset=Subset.TRAINING,
    )
    categories = LabelCategories(labels=VOC_LABELS)
    bbox = np.array([10, 20, 30, 40], dtype=np.float32)

    obj_elem = _create_object_element(sample, 0, bbox, categories)

    assert obj_elem.find("name").text == VOC_LABELS[1]
    assert obj_elem.find("difficult").text == "1"
    assert obj_elem.find("occluded").text == "1"
    assert obj_elem.find("pose").text == "Left"
    # Bounding box should be present
    bndbox = obj_elem.find("bndbox")
    assert bndbox is not None
    assert bndbox.find("xmin").text == "10"
    assert bndbox.find("ymin").text == "20"
    assert bndbox.find("xmax").text == "30"
    assert bndbox.find("ymax").text == "40"


def test_create_object_element_without_bbox():
    """Test _create_object_element omits bndbox when bbox is None."""
    sample = VocSample(
        image="/path/to/image.jpg",
        image_info=ImageInfo(height=480, width=640),
        bboxes=None,
        labels=np.array([0], dtype=np.uint32),
        difficult=np.array([False]),
        truncated=np.array([True]),
        occluded=np.array([False]),
        pose=np.array(["Frontal"], dtype=object),
        subset=Subset.TRAINING,
    )
    categories = LabelCategories(labels=VOC_LABELS)

    obj_elem = _create_object_element(sample, 0, None, categories)

    assert obj_elem.find("name").text == VOC_LABELS[0]
    assert obj_elem.find("truncated").text == "1"
    assert obj_elem.find("difficult").text == "0"
    assert obj_elem.find("pose").text == "Frontal"
    # No bounding box should be present
    assert obj_elem.find("bndbox") is None


# ==============================
# _detect_classification_label_files Tests
# ==============================


def test_detect_classification_label_files_finds_label_files(tmp_path: Path):
    """Test detecting label-specific classification files in ImageSets/Main."""
    imagesets_main = tmp_path / "ImageSets" / "Main"
    imagesets_main.mkdir(parents=True)
    (imagesets_main / "train.txt").write_text("img1\nimg2\n")
    (imagesets_main / "dog_train.txt").write_text("img1  1\nimg2 -1\n")
    (imagesets_main / "cat_train.txt").write_text("img1 -1\nimg2  1\n")

    categories = LabelCategories(labels=("background", "dog", "cat"))
    result = _detect_classification_label_files(tmp_path, {"train"}, categories)

    assert "train" in result
    assert "dog" in result["train"]
    assert "cat" in result["train"]
    assert result["train"]["dog"] == imagesets_main / "dog_train.txt"
    assert result["train"]["cat"] == imagesets_main / "cat_train.txt"


def test_detect_classification_label_files_skips_unknown_labels(tmp_path: Path):
    """Test that files with unknown label names are ignored."""
    imagesets_main = tmp_path / "ImageSets" / "Main"
    imagesets_main.mkdir(parents=True)
    (imagesets_main / "train.txt").write_text("img1\n")
    (imagesets_main / "unknown_train.txt").write_text("img1  1\n")

    categories = LabelCategories(labels=("background", "dog"))
    result = _detect_classification_label_files(tmp_path, {"train"}, categories)

    assert result == {} or "unknown" not in result.get("train", {})


def test_detect_classification_label_files_skips_background(tmp_path: Path):
    """Test that background label files are excluded."""
    imagesets_main = tmp_path / "ImageSets" / "Main"
    imagesets_main.mkdir(parents=True)
    (imagesets_main / "train.txt").write_text("img1\n")
    (imagesets_main / "background_train.txt").write_text("img1  1\n")

    categories = LabelCategories(labels=("background", "dog"))
    result = _detect_classification_label_files(tmp_path, {"train"}, categories)

    assert "background" not in result.get("train", {})


def test_detect_classification_label_files_skips_wrong_subset(tmp_path: Path):
    """Test that files for non-matching subsets are ignored."""
    imagesets_main = tmp_path / "ImageSets" / "Main"
    imagesets_main.mkdir(parents=True)
    (imagesets_main / "train.txt").write_text("img1\n")
    (imagesets_main / "dog_val.txt").write_text("img1  1\n")

    categories = LabelCategories(labels=("background", "dog"))
    result = _detect_classification_label_files(tmp_path, {"train"}, categories)

    # dog_val.txt should be ignored because subset_names only contains "train"
    assert result == {} or "val" not in result


def test_detect_classification_label_files_multiple_subsets(tmp_path: Path):
    """Test detecting label files across multiple subsets."""
    imagesets_main = tmp_path / "ImageSets" / "Main"
    imagesets_main.mkdir(parents=True)
    (imagesets_main / "train.txt").write_text("img1\n")
    (imagesets_main / "val.txt").write_text("img2\n")
    (imagesets_main / "dog_train.txt").write_text("img1  1\n")
    (imagesets_main / "dog_val.txt").write_text("img2  1\n")

    categories = LabelCategories(labels=("background", "dog"))
    result = _detect_classification_label_files(tmp_path, {"train", "val"}, categories)

    assert "train" in result
    assert "val" in result
    assert "dog" in result["train"]
    assert "dog" in result["val"]


def test_detect_classification_label_files_returns_empty_when_no_imagesets(tmp_path: Path):
    """Test that empty dict is returned when ImageSets/Main doesn't exist."""
    categories = LabelCategories(labels=("background", "dog"))
    result = _detect_classification_label_files(tmp_path, {"train"}, categories)

    assert result == {}


def test_detect_classification_label_files_handles_label_with_underscore(tmp_path: Path):
    """Test detecting label files where the label name itself contains an underscore."""
    imagesets_main = tmp_path / "ImageSets" / "Main"
    imagesets_main.mkdir(parents=True)
    (imagesets_main / "train.txt").write_text("img1\n")
    (imagesets_main / "potted_plant_train.txt").write_text("img1  1\n")

    categories = LabelCategories(labels=("background", "potted_plant"))
    result = _detect_classification_label_files(tmp_path, {"train"}, categories)

    assert "train" in result
    assert "potted_plant" in result["train"]


# ==============================
# _parse_classification_labels Tests
# ==============================


def test_parse_classification_labels_returns_positive_labels(tmp_path: Path):
    """Test parsing classification files returns correct positive label indices."""
    dog_file = tmp_path / "dog_train.txt"
    cat_file = tmp_path / "cat_train.txt"
    dog_file.write_text("img1  1\nimg2 -1\nimg3  1\n")
    cat_file.write_text("img1 -1\nimg2  1\nimg3  1\n")

    categories = LabelCategories(labels=("background", "dog", "cat"))
    label_files = {"dog": dog_file, "cat": cat_file}

    result = _parse_classification_labels(label_files, categories)

    assert result["img1"] == [1]  # dog only
    assert result["img2"] == [2]  # cat only
    assert result["img3"] == [1, 2]  # both dog and cat


def test_parse_classification_labels_excludes_negative_labels(tmp_path: Path):
    """Test that images with only -1 entries do not appear in results."""
    dog_file = tmp_path / "dog_train.txt"
    dog_file.write_text("img1 -1\nimg2 -1\n")

    categories = LabelCategories(labels=("background", "dog"))
    label_files = {"dog": dog_file}

    result = _parse_classification_labels(label_files, categories)

    assert "img1" not in result
    assert "img2" not in result


def test_parse_classification_labels_handles_empty_file(tmp_path: Path):
    """Test that an empty label file produces no entries."""
    empty_file = tmp_path / "dog_train.txt"
    empty_file.write_text("")

    categories = LabelCategories(labels=("background", "dog"))
    label_files = {"dog": empty_file}

    result = _parse_classification_labels(label_files, categories)

    assert result == {}


def test_parse_classification_labels_skips_unknown_labels(tmp_path: Path):
    """Test that labels not in categories are ignored."""
    unknown_file = tmp_path / "unknown_train.txt"
    unknown_file.write_text("img1  1\n")

    categories = LabelCategories(labels=("background", "dog"))
    label_files = {"unknown": unknown_file}

    result = _parse_classification_labels(label_files, categories)

    assert result == {}


def test_parse_classification_labels_sorts_indices(tmp_path: Path):
    """Test that label indices are sorted for determinism."""
    # Create files so that cat (index 2) is parsed before dog (index 1)
    cat_file = tmp_path / "cat_train.txt"
    dog_file = tmp_path / "dog_train.txt"
    cat_file.write_text("img1  1\n")
    dog_file.write_text("img1  1\n")

    categories = LabelCategories(labels=("background", "dog", "cat"))
    # Pass cat first to test sorting
    label_files = {"cat": cat_file, "dog": dog_file}

    result = _parse_classification_labels(label_files, categories)

    # Should be sorted: [1 (dog), 2 (cat)]
    assert result["img1"] == [1, 2]


def test_parse_classification_labels_skips_malformed_lines(tmp_path: Path):
    """Test that lines without a valid flag are skipped."""
    label_file = tmp_path / "dog_train.txt"
    label_file.write_text("img1  1\nimg2\nimg3 abc\nimg4  1\n# comment\n\n")

    categories = LabelCategories(labels=("background", "dog"))
    label_files = {"dog": label_file}

    result = _parse_classification_labels(label_files, categories)

    assert "img1" in result
    assert "img2" not in result
    assert "img3" not in result
    assert "img4" in result


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
    """VOC _get_image_size must honor EXIF orientation so the dimensions written
    into VOC XML annotations match the image as displayed and loaded.
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
