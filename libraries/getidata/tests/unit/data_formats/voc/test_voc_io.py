# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Unit tests for VOC I/O functions.
"""

from pathlib import Path

import numpy as np
import pytest

from getidata import Dataset
from getidata.data_formats.voc.helpers import _build_image_index, _find_image_file
from getidata.data_formats.voc.io import load_voc_dataset, save_voc_dataset
from getidata.data_formats.voc.sample import VocSample
from getidata.fields import ImageInfo, Subset


def _create_test_image(path: Path, width: int = 640, height: int = 480) -> None:
    """Create a minimal valid image file for testing."""
    from PIL import Image

    img = Image.new("RGB", (width, height), color="red")
    img.save(path)


def _create_voc_structure(root: Path) -> None:
    """Create a minimal VOC directory structure with test data."""
    # Create directories
    (root / "JPEGImages").mkdir(parents=True)
    (root / "Annotations").mkdir(parents=True)
    (root / "ImageSets" / "Main").mkdir(parents=True)

    # Create test images
    _create_test_image(root / "JPEGImages" / "test001.jpg")
    _create_test_image(root / "JPEGImages" / "test002.jpg")

    # Create annotations
    (root / "Annotations" / "test001.xml").write_text("""
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
    </object>
</annotation>
    """)

    (root / "Annotations" / "test002.xml").write_text("""
<annotation>
    <size>
        <width>640</width>
        <height>480</height>
    </size>
    <object>
        <name>dog</name>
        <bndbox>
            <xmin>50</xmin>
            <ymin>50</ymin>
            <xmax>150</xmax>
            <ymax>150</ymax>
        </bndbox>
    </object>
    <object>
        <name>cat</name>
        <bndbox>
            <xmin>300</xmin>
            <ymin>200</ymin>
            <xmax>400</xmax>
            <ymax>350</ymax>
        </bndbox>
    </object>
</annotation>
    """)

    # Create ImageSets
    (root / "ImageSets" / "Main" / "train.txt").write_text("test001\n")
    (root / "ImageSets" / "Main" / "val.txt").write_text("test002\n")


# ==============================
# load_voc_dataset Tests
# ==============================


def test_load_voc_dataset_from_standard_layout(tmp_path: Path):
    """Test loading a VOC dataset from standard directory layout."""
    _create_voc_structure(tmp_path)

    dataset = load_voc_dataset(root_dir=str(tmp_path))

    assert len(dataset) == 2


def test_load_voc_dataset_samples_have_correct_structure(tmp_path: Path):
    """Test that loaded samples have the expected structure."""
    _create_voc_structure(tmp_path)

    dataset = load_voc_dataset(root_dir=str(tmp_path))

    for sample in dataset:
        assert hasattr(sample, "image")
        assert hasattr(sample, "image_info")
        assert hasattr(sample, "bboxes")
        assert hasattr(sample, "labels")
        assert hasattr(sample, "subset")


def test_load_voc_dataset_parses_annotations_correctly(tmp_path: Path):
    """Test that annotations are parsed correctly."""
    _create_voc_structure(tmp_path)

    dataset = load_voc_dataset(root_dir=str(tmp_path))

    # Find the sample with 2 objects (test002)
    multi_obj_sample = None
    for sample in dataset:
        if sample.bboxes is not None and len(sample.bboxes) == 2:
            multi_obj_sample = sample
            break

    assert multi_obj_sample is not None
    assert multi_obj_sample.bboxes.shape == (2, 4)
    assert len(multi_obj_sample.labels) == 2


def test_load_voc_dataset_assigns_subsets_correctly(tmp_path: Path):
    """Test that subsets are assigned based on ImageSets."""
    _create_voc_structure(tmp_path)

    dataset = load_voc_dataset(root_dir=str(tmp_path))

    subsets = set()
    for sample in dataset:
        subsets.add(sample.subset)

    # Should have both training and validation samples
    assert Subset.TRAINING in subsets and Subset.VALIDATION in subsets


def test_load_voc_dataset_raises_on_missing_root():
    """Test that loading from non-existent path raises error."""
    with pytest.raises(FileNotFoundError):
        load_voc_dataset(root_dir="/nonexistent/path")


def _create_voc_structure_with_n_images(root: Path, num_images: int) -> None:
    """Create a minimal standard-layout VOC dataset with N images.

    Unlike :func:`_create_voc_structure` (which hand-crafts two richly
    annotated samples for content-correctness tests), this generates a
    variable number of minimal placeholder samples, for tests that need to
    vary the dataset size (e.g. performance regression tests).
    """
    (root / "JPEGImages").mkdir(parents=True)
    (root / "Annotations").mkdir(parents=True)
    (root / "ImageSets" / "Main").mkdir(parents=True)

    image_ids = [f"img{i:04d}" for i in range(num_images)]
    for image_id in image_ids:
        _create_test_image(root / "JPEGImages" / f"{image_id}.jpg")
        (root / "Annotations" / f"{image_id}.xml").write_text("""
<annotation>
    <size>
        <width>64</width>
        <height>48</height>
    </size>
    <object>
        <name>person</name>
        <bndbox>
            <xmin>1</xmin>
            <ymin>1</ymin>
            <xmax>10</xmax>
            <ymax>10</ymax>
        </bndbox>
    </object>
</annotation>
        """)

    (root / "ImageSets" / "Main" / "train.txt").write_text("\n".join(image_ids) + "\n")


def test_load_voc_dataset_does_not_rescan_directory_per_image(tmp_path: Path, monkeypatch):
    """Regression test for a perf bug where resolving each VOC sample's image
    file called ``Path.glob()`` once per image, rescanning the entire images
    directory on every call (O(images * files) overall - on large datasets
    this made loading take hours instead of seconds). ``Path.glob()`` call
    count must not scale with the number of images in the dataset.
    """
    counters = {"count": 0}
    original_glob = Path.glob

    def counting_glob(self, *args, **kwargs):
        counters["count"] += 1
        return original_glob(self, *args, **kwargs)

    monkeypatch.setattr(Path, "glob", counting_glob)

    def build_and_load(num_images: int) -> int:
        root = tmp_path / f"voc_{num_images}"
        _create_voc_structure_with_n_images(root, num_images)
        counters["count"] = 0
        dataset = load_voc_dataset(root_dir=str(root))
        assert len(dataset) == num_images
        return counters["count"]

    small_calls = build_and_load(5)
    large_calls = build_and_load(50)

    assert large_calls == small_calls, (
        f"Path.glob() call count scaled with the number of images ({small_calls} -> {large_calls} "
        "for 5 -> 50 images); expected a constant, image-count-independent number of calls. This "
        "indicates the O(images * files) per-image directory rescan regression has returned."
    )


def test_load_voc_dataset_from_simple_layout(tmp_path: Path):
    """Test loading VOC dataset from simple images + annotations directories."""
    images_dir = tmp_path / "images"
    annotations_dir = tmp_path / "annotations"
    images_dir.mkdir()
    annotations_dir.mkdir()

    # Create test image and annotation
    _create_test_image(images_dir / "test.jpg")
    (annotations_dir / "test.xml").write_text("""
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
</annotation>
    """)

    dataset = load_voc_dataset(
        images_dir_path=str(images_dir),
        annotations_dir_path=str(annotations_dir),
    )

    assert len(dataset) == 1


def test_load_voc_dataset_simple_layout_does_not_rescan_directory_per_image(tmp_path: Path, monkeypatch):
    """Same regression test as
    ``test_load_voc_dataset_does_not_rescan_directory_per_image`` but for the
    "simple" images+annotations layout (``_load_voc_simple``), which builds
    its own separate ``VocLoadContext``.
    """
    counters = {"count": 0}
    original_glob = Path.glob

    def counting_glob(self, *args, **kwargs):
        counters["count"] += 1
        return original_glob(self, *args, **kwargs)

    monkeypatch.setattr(Path, "glob", counting_glob)

    def build_and_load(num_images: int) -> int:
        images_dir = tmp_path / f"simple_images_{num_images}"
        annotations_dir = tmp_path / f"simple_annotations_{num_images}"
        images_dir.mkdir()
        annotations_dir.mkdir()

        for i in range(num_images):
            image_id = f"img{i:04d}"
            _create_test_image(images_dir / f"{image_id}.jpg")
            (annotations_dir / f"{image_id}.xml").write_text("""
<annotation>
    <size>
        <width>64</width>
        <height>48</height>
    </size>
    <object>
        <name>person</name>
        <bndbox>
            <xmin>1</xmin>
            <ymin>1</ymin>
            <xmax>10</xmax>
            <ymax>10</ymax>
        </bndbox>
    </object>
</annotation>
            """)

        counters["count"] = 0
        dataset = load_voc_dataset(
            images_dir_path=str(images_dir),
            annotations_dir_path=str(annotations_dir),
        )
        assert len(dataset) == num_images
        return counters["count"]

    small_calls = build_and_load(5)
    large_calls = build_and_load(50)

    assert large_calls == small_calls, (
        f"Path.glob() call count scaled with the number of images ({small_calls} -> {large_calls} "
        "for 5 -> 50 images) in the simple-layout VOC loader."
    )


def test_load_voc_dataset_simple_layout_tie_break_matches_build_image_index(tmp_path: Path):
    """Regression test: `_load_voc_simple` must resolve ambiguous (duplicate
    stem, different extension) filenames the same way `_build_image_index`
    does, rather than applying its own, different tie-breaking rule.

    Previously `_load_voc_simple` built its image lookup with a plain
    ``{stem: path for path in image_files}`` dict comprehension, which keeps
    the *last* match for a repeated key - silently different from
    `_build_image_index`'s (and the original `_find_image_file`'s) "first
    match wins" behavior used everywhere else in the VOC loader.
    """
    images_dir = tmp_path / "images"
    annotations_dir = tmp_path / "annotations"
    images_dir.mkdir()
    annotations_dir.mkdir()

    # Two images sharing the same stem, different extensions.
    _create_test_image(images_dir / "img0001.jpg")
    _create_test_image(images_dir / "img0001.png")
    (annotations_dir / "img0001.xml").write_text("""
<annotation>
    <size>
        <width>640</width>
        <height>480</height>
    </size>
    <object>
        <name>person</name>
        <bndbox>
            <xmin>1</xmin>
            <ymin>1</ymin>
            <xmax>10</xmax>
            <ymax>10</ymax>
        </bndbox>
    </object>
</annotation>
    """)

    expected_path = _build_image_index(images_dir)["img0001"]

    dataset = load_voc_dataset(
        images_dir_path=str(images_dir),
        annotations_dir_path=str(annotations_dir),
    )

    # Note: `_load_voc_simple` iterates every image file found (one loop
    # entry per extension for a shared stem), so both "img0001.jpg" and
    # "img0001.png" each produce a sample here - that duplication is a
    # separate, pre-existing behavior and not what this test is about.
    # What matters is that *every* sample for this stem resolves to the
    # exact same file that `_build_image_index` picked for it.
    assert len(dataset) == 2
    for sample in dataset:
        assert sample.image.path == str(expected_path)


def test_build_image_index_registers_all_dot_prefixes(tmp_path: Path):
    """Regression test: `_find_image_file(images_dir, stem)` resolves via
    ``glob(f"{stem}.*")``, which matches on *any* "." in the filename - so a
    file like "img0001.v1.png" is matched by both stem="img0001" and
    stem="img0001.v1". `_build_image_index` must register the file under
    every such prefix, not just `Path.stem` ("img0001.v1"), otherwise a
    lookup for the shorter, more common annotation ID ("img0001") would miss
    the index and silently fall back to the slow per-sample glob.
    """
    (tmp_path / "img0001.v1.png").touch()

    index = _build_image_index(tmp_path)

    assert index["img0001"] == tmp_path / "img0001.v1.png"
    assert index["img0001.v1"] == tmp_path / "img0001.v1.png"


def test_load_voc_dataset_resolves_annotation_id_with_extra_dots_in_filename(tmp_path: Path, monkeypatch):
    """End-to-end version of the above: an annotation/ImageSets ID of
    "img0001" must resolve correctly - via the fast `images_index` lookup,
    *without* falling back to `_find_image_file` (a per-sample glob) - even
    when the actual image file on disk has an extra dot before its
    extension ("img0001.v1.jpg"). Before the fix, `images_index` wouldn't
    contain the "img0001" key at all, so this would only resolve correctly
    by luck, via the slow fallback path.
    """
    root = tmp_path
    (root / "JPEGImages").mkdir()
    (root / "Annotations").mkdir()
    (root / "ImageSets" / "Main").mkdir(parents=True)

    _create_test_image(root / "JPEGImages" / "img0001.v1.jpg")
    (root / "Annotations" / "img0001.xml").write_text("""
<annotation>
    <size>
        <width>640</width>
        <height>480</height>
    </size>
    <object>
        <name>person</name>
        <bndbox>
            <xmin>1</xmin>
            <ymin>1</ymin>
            <xmax>10</xmax>
            <ymax>10</ymax>
        </bndbox>
    </object>
</annotation>
    """)
    (root / "ImageSets" / "Main" / "train.txt").write_text("img0001\n")

    fallback_calls = {"count": 0}
    original_find_image_file = _find_image_file

    def counting_find_image_file(*args, **kwargs):
        fallback_calls["count"] += 1
        return original_find_image_file(*args, **kwargs)

    monkeypatch.setattr(
        "getidata.data_formats.voc.helpers._find_image_file",
        counting_find_image_file,
    )

    dataset = load_voc_dataset(root_dir=str(root))

    assert len(dataset) == 1
    assert dataset[0].image.path == str(root / "JPEGImages" / "img0001.v1.jpg")
    assert fallback_calls["count"] == 0, (
        "Resolution fell back to the slow per-sample _find_image_file() glob instead of "
        "hitting the fast images_index lookup built by _build_image_index()."
    )


# ==============================
# save_voc_dataset Tests
# ==============================


def test_save_voc_dataset_creates_correct_structure(tmp_path: Path):
    """Test that saving creates the correct VOC directory structure."""
    # Create a simple dataset
    from getidata.categories import LabelCategories, MaskCategories
    from getidata.data_formats.voc.constants import VOC_LABELS

    label_categories = LabelCategories(labels=VOC_LABELS)
    mask_categories = MaskCategories.generate(size=len(VOC_LABELS), include_background=True)
    mask_categories = MaskCategories(labels=list(VOC_LABELS), colormap=mask_categories.colormap)
    # Note: instance_mask shares categories with class_mask via categories_from field attribute
    dataset = Dataset(
        VocSample,
        categories={
            "labels": label_categories,
            "class_mask": mask_categories,
        },
    )

    # Create a temp image
    img_path = tmp_path / "source" / "image.jpg"
    img_path.parent.mkdir()
    _create_test_image(img_path)

    sample = VocSample(
        image=str(img_path),
        image_info=ImageInfo(height=480, width=640),
        bboxes=np.array([[100, 100, 200, 200]], dtype=np.float32),
        labels=np.array([1], dtype=np.uint32),
        difficult=np.array([False]),
        truncated=np.array([False]),
        occluded=np.array([False]),
        pose=np.array(["Frontal"], dtype=object),
        class_mask=None,
        instance_mask=None,
        subset=Subset.TRAINING,
    )
    dataset.append(sample)

    output_dir = tmp_path / "output"
    save_voc_dataset(dataset, root_dir=str(output_dir), save_images=True)

    # Check directory structure
    assert (output_dir / "JPEGImages").is_dir()
    assert (output_dir / "Annotations").is_dir()
    assert (output_dir / "ImageSets" / "Main").is_dir()
    assert (output_dir / "labelmap.txt").exists()


def test_save_voc_dataset_creates_xml_annotations(tmp_path: Path):
    """Test that XML annotation files are created."""
    from getidata.categories import LabelCategories, MaskCategories
    from getidata.data_formats.voc.constants import VOC_LABELS

    label_categories = LabelCategories(labels=VOC_LABELS)
    mask_categories = MaskCategories.generate(size=len(VOC_LABELS), include_background=True)
    mask_categories = MaskCategories(labels=list(VOC_LABELS), colormap=mask_categories.colormap)
    # Note: instance_mask shares categories with class_mask via categories_from field attribute
    dataset = Dataset(
        VocSample,
        categories={
            "labels": label_categories,
            "class_mask": mask_categories,
        },
    )

    img_path = tmp_path / "source" / "test001.jpg"
    img_path.parent.mkdir()
    _create_test_image(img_path)

    sample = VocSample(
        image=str(img_path),
        image_info=ImageInfo(height=480, width=640),
        bboxes=np.array([[100, 100, 200, 200]], dtype=np.float32),
        labels=np.array([1], dtype=np.uint32),
        difficult=None,
        truncated=None,
        occluded=None,
        pose=None,
        class_mask=None,
        instance_mask=None,
        subset=Subset.TRAINING,
    )
    dataset.append(sample)

    output_dir = tmp_path / "output"
    save_voc_dataset(dataset, root_dir=str(output_dir), save_images=True)

    # Check XML annotation
    xml_path = output_dir / "Annotations" / "test001_000000.xml"
    assert xml_path.exists()
    content = xml_path.read_text()
    assert "<annotation>" in content
    assert "<object>" in content


def test_save_voc_dataset_creates_imagesets(tmp_path: Path):
    """Test that ImageSets files are created based on subsets."""
    from getidata.categories import LabelCategories, MaskCategories
    from getidata.data_formats.voc.constants import VOC_LABELS

    label_categories = LabelCategories(labels=VOC_LABELS)
    mask_categories = MaskCategories.generate(size=len(VOC_LABELS), include_background=True)
    mask_categories = MaskCategories(labels=list(VOC_LABELS), colormap=mask_categories.colormap)
    # Note: instance_mask shares categories with class_mask via categories_from field attribute
    dataset = Dataset(
        VocSample,
        categories={
            "labels": label_categories,
            "class_mask": mask_categories,
        },
    )

    for i, subset in enumerate([Subset.TRAINING, Subset.VALIDATION]):
        img_path = tmp_path / "source" / f"image{i}.jpg"
        img_path.parent.mkdir(exist_ok=True)
        _create_test_image(img_path)

        sample = VocSample(
            image=str(img_path),
            image_info=ImageInfo(height=480, width=640),
            bboxes=None,
            labels=None,
            difficult=None,
            truncated=None,
            occluded=None,
            pose=None,
            class_mask=None,
            instance_mask=None,
            subset=subset,
        )
        dataset.append(sample)

    output_dir = tmp_path / "output"
    save_voc_dataset(dataset, root_dir=str(output_dir), save_images=True)

    # Check ImageSets files
    assert (output_dir / "ImageSets" / "Main" / "train.txt").exists()
    assert (output_dir / "ImageSets" / "Main" / "val.txt").exists()


# ==============================
# Round-trip Tests
# ==============================


def test_roundtrip_preserves_sample_count(tmp_path: Path):
    """Test that load -> save -> load preserves sample count."""
    _create_voc_structure(tmp_path)

    # Load original
    dataset = load_voc_dataset(root_dir=str(tmp_path))
    original_len = len(dataset)

    # Save
    output_dir = tmp_path / "output"
    save_voc_dataset(dataset, root_dir=str(output_dir), save_images=True)

    # Reload
    reloaded = load_voc_dataset(root_dir=str(output_dir))

    assert len(reloaded) == original_len


def test_roundtrip_preserves_bbox_data(tmp_path: Path):
    """Test that round-trip preserves bounding box data."""
    _create_voc_structure(tmp_path)

    # Load original
    dataset = load_voc_dataset(root_dir=str(tmp_path))

    # Save
    output_dir = tmp_path / "output"
    save_voc_dataset(dataset, root_dir=str(output_dir), save_images=True)

    # Reload and compare
    reloaded = load_voc_dataset(root_dir=str(output_dir))

    original_samples = list(dataset)
    reloaded_samples = list(reloaded)

    for orig, reload in zip(
        sorted(original_samples, key=lambda s: s.image.path), sorted(reloaded_samples, key=lambda s: s.image.path)
    ):
        if orig.bboxes is not None:
            assert reload.bboxes is not None
            np.testing.assert_array_almost_equal(orig.bboxes, reload.bboxes, decimal=0)


# ==============================
# Classification Label Loading Tests
# ==============================


def _create_classification_voc_structure(root: Path) -> None:
    """Create a VOC directory structure for a classification-only dataset (no XML annotations)."""
    (root / "JPEGImages").mkdir(parents=True)
    (root / "Annotations").mkdir(parents=True)
    (root / "ImageSets" / "Main").mkdir(parents=True)

    # Create test images
    _create_test_image(root / "JPEGImages" / "dog01.jpg")
    _create_test_image(root / "JPEGImages" / "dog02.jpg")
    _create_test_image(root / "JPEGImages" / "cat01.jpg")
    _create_test_image(root / "JPEGImages" / "cat02.jpg")
    _create_test_image(root / "JPEGImages" / "unlabeled01.jpg")

    # Main subset listing
    (root / "ImageSets" / "Main" / "train.txt").write_text("dog01\ndog02\ncat01\ncat02\nunlabeled01\n")

    # Label-specific classification files
    (root / "ImageSets" / "Main" / "dog_train.txt").write_text("dog01  1\ndog02  1\ncat01 -1\ncat02 -1\n")
    (root / "ImageSets" / "Main" / "cat_train.txt").write_text("dog01 -1\ndog02 -1\ncat01  1\ncat02  1\n")

    # Labelmap
    (root / "labelmap.txt").write_text(
        "# label:color_rgb:parts:actions\nbackground:0,0,0::\ndog:128,0,0::\ncat:0,128,0::\n"
    )


def test_load_classification_dataset_assigns_labels(tmp_path: Path):
    """Test that classification labels from ImageSets/Main are loaded when no XML annotations exist."""
    _create_classification_voc_structure(tmp_path)

    dataset = load_voc_dataset(root_dir=str(tmp_path))

    assert len(dataset) == 5

    labels_by_image = {}
    for sample in dataset:
        stem = Path(sample.image.path).stem
        labels_by_image[stem] = sample.labels

    # dog images should have label index 1 (dog)
    assert labels_by_image["dog01"] is not None
    np.testing.assert_array_equal(labels_by_image["dog01"], [1])
    assert labels_by_image["dog02"] is not None
    np.testing.assert_array_equal(labels_by_image["dog02"], [1])

    # cat images should have label index 2 (cat)
    assert labels_by_image["cat01"] is not None
    np.testing.assert_array_equal(labels_by_image["cat01"], [2])
    assert labels_by_image["cat02"] is not None
    np.testing.assert_array_equal(labels_by_image["cat02"], [2])

    # unlabeled image should have no labels
    assert labels_by_image["unlabeled01"] is None


def test_load_classification_dataset_no_bboxes(tmp_path: Path):
    """Test that classification-only samples have no bounding boxes."""
    _create_classification_voc_structure(tmp_path)

    dataset = load_voc_dataset(root_dir=str(tmp_path))

    for sample in dataset:
        assert sample.bboxes is None


def test_load_classification_dataset_label_dtype(tmp_path: Path):
    """Test that classification labels are uint32 arrays."""
    _create_classification_voc_structure(tmp_path)

    dataset = load_voc_dataset(root_dir=str(tmp_path))

    for sample in dataset:
        if sample.labels is not None:
            assert sample.labels.dtype == np.uint32


def test_load_classification_dataset_multi_label(tmp_path: Path):
    """Test that an image can receive multiple classification labels."""
    root = tmp_path / "multi"
    (root / "JPEGImages").mkdir(parents=True)
    (root / "Annotations").mkdir(parents=True)
    (root / "ImageSets" / "Main").mkdir(parents=True)

    _create_test_image(root / "JPEGImages" / "both.jpg")

    (root / "ImageSets" / "Main" / "train.txt").write_text("both\n")
    (root / "ImageSets" / "Main" / "dog_train.txt").write_text("both  1\n")
    (root / "ImageSets" / "Main" / "cat_train.txt").write_text("both  1\n")
    (root / "labelmap.txt").write_text(
        "# label:color_rgb:parts:actions\nbackground:0,0,0::\ndog:128,0,0::\ncat:0,128,0::\n"
    )

    dataset = load_voc_dataset(root_dir=str(root))

    assert len(dataset) == 1
    sample = dataset[0]
    assert sample.labels is not None
    # Both labels present and sorted
    np.testing.assert_array_equal(sample.labels, [1, 2])


def test_xml_annotations_take_precedence_over_classification_labels(tmp_path: Path):
    """Test that XML annotation labels are used when present, even if classification files exist."""
    root = tmp_path / "mixed"
    (root / "JPEGImages").mkdir(parents=True)
    (root / "Annotations").mkdir(parents=True)
    (root / "ImageSets" / "Main").mkdir(parents=True)

    _create_test_image(root / "JPEGImages" / "img.jpg", width=640, height=480)

    # XML annotation with a person bbox
    (root / "Annotations" / "img.xml").write_text("""
<annotation>
    <size><width>640</width><height>480</height></size>
    <object>
        <name>person</name>
        <bndbox><xmin>10</xmin><ymin>20</ymin><xmax>100</xmax><ymax>200</ymax></bndbox>
    </object>
</annotation>
    """)

    (root / "ImageSets" / "Main" / "train.txt").write_text("img\n")
    (root / "ImageSets" / "Main" / "person_train.txt").write_text("img  1\n")
    (root / "ImageSets" / "Main" / "car_train.txt").write_text("img  1\n")
    (root / "labelmap.txt").write_text(
        "# label:color_rgb:parts:actions\nbackground:0,0,0::\nperson:128,0,0::\ncar:0,128,0::\n"
    )

    dataset = load_voc_dataset(root_dir=str(root))

    sample = dataset[0]
    # Should have the XML-based label (person=1), not the classification labels
    assert sample.bboxes is not None
    assert sample.bboxes.shape == (1, 4)
    np.testing.assert_array_equal(sample.labels, [1])  # person only from XML


def test_load_classification_with_multiple_subsets(tmp_path: Path):
    """Test classification labels across train and val subsets."""
    root = tmp_path / "subsets"
    (root / "JPEGImages").mkdir(parents=True)
    (root / "Annotations").mkdir(parents=True)
    (root / "ImageSets" / "Main").mkdir(parents=True)

    _create_test_image(root / "JPEGImages" / "train_img.jpg")
    _create_test_image(root / "JPEGImages" / "val_img.jpg")

    (root / "ImageSets" / "Main" / "train.txt").write_text("train_img\n")
    (root / "ImageSets" / "Main" / "val.txt").write_text("val_img\n")
    (root / "ImageSets" / "Main" / "dog_train.txt").write_text("train_img  1\n")
    (root / "ImageSets" / "Main" / "cat_val.txt").write_text("val_img  1\n")
    (root / "labelmap.txt").write_text(
        "# label:color_rgb:parts:actions\nbackground:0,0,0::\ndog:128,0,0::\ncat:0,128,0::\n"
    )

    dataset = load_voc_dataset(root_dir=str(root))

    assert len(dataset) == 2

    labels_by_image = {}
    subset_by_image = {}
    for sample in dataset:
        stem = Path(sample.image.path).stem
        labels_by_image[stem] = sample.labels
        subset_by_image[stem] = sample.subset

    np.testing.assert_array_equal(labels_by_image["train_img"], [1])  # dog
    np.testing.assert_array_equal(labels_by_image["val_img"], [2])  # cat
    assert subset_by_image["train_img"] == Subset.TRAINING
    assert subset_by_image["val_img"] == Subset.VALIDATION
