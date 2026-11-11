import json
from pathlib import Path

import numpy as np
import pytest

from getidata import Dataset
from getidata.categories import KeypointCategories
from getidata.data_formats.base import DataFormat
from getidata.data_formats.coco.io import (
    _detect_roboflow_coco_layout,
    _is_roboflow_coco_layout,
    _subset_name_to_enum,
    import_coco_dataset,
    is_coco_format,
    load_coco_dataset,
    save_coco_dataset,
)
from getidata.data_formats.coco.sample import CocoCategories, CocoSample
from getidata.fields import ImageInfo, Subset
from getidata.format_detection import detect_dataset_format, find_dataset_root


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _make_sample(image_path: Path) -> CocoSample:
    return CocoSample(
        image=str(image_path),
        image_info=ImageInfo(height=2, width=3),
        bboxes=np.array([[0.0, 0.0, 1.0, 1.0]], dtype=np.float32),
        polygons=None,
        labels=np.array([0], dtype=np.int32),
        areas=np.array([1.0], dtype=np.float32),
        iscrowd=np.array([0], dtype=np.int32),
        subset=Subset.TRAINING,
        image_id=1,
        caption_group_ids=None,
        captions=None,
        keypoints=None,
    )


def test_load_coco_dataset_minimal(tmp_path: Path):
    root = tmp_path / "coco"
    annotations = root / "annotations"
    train_dir = root / "train2017"
    val_dir = root / "val2017"
    train_dir.mkdir(parents=True)
    val_dir.mkdir()

    (train_dir / "img.jpg").write_bytes(b"img")

    _write_json(
        annotations / "instances_train2017.json",
        {
            "images": [{"id": 1, "file_name": "img.jpg", "height": 10, "width": 8}],
            "annotations": [
                {
                    "id": 1,
                    "image_id": 1,
                    "category_id": 1,
                    "bbox": [0, 0, 2, 2],
                    "segmentation": [[0, 0, 2, 0, 2, 2, 0, 2]],
                    "area": 4,
                    "iscrowd": 0,
                }
            ],
            "categories": [{"id": 1, "name": "cat"}],
        },
    )

    ds = load_coco_dataset(
        images_dir_path={"training": str(train_dir)},
        annotations_path={"training": str(annotations / "instances_train2017.json")},
    )

    assert len(ds) == 1
    sample = ds[0]
    assert sample.subset == Subset.TRAINING
    assert sample.labels.tolist() == [0]
    assert sample.bboxes.shape == (1, 4)


def test_load_coco_dataset_errors(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_coco_dataset(
            images_dir_path=str(tmp_path / "missing"),
            annotations_path=str(tmp_path / "missing.json"),
        )

    # Test with mismatched types (str vs dict)
    with pytest.raises(ValueError):
        load_coco_dataset(
            images_dir_path=str(tmp_path),
            annotations_path={"train": str(tmp_path / "train.json")},
        )


def test_save_coco_dataset_writes_expected_structure(tmp_path: Path):
    dataset = Dataset(CocoSample, categories={"labels": CocoCategories()})
    img_path = tmp_path / "src.jpg"
    img_path.write_bytes(b"img")
    dataset.append(_make_sample(img_path))

    export_dir = tmp_path / "export"
    images_dir = export_dir / "images"
    annotations_path = export_dir / "annotations.json"

    save_coco_dataset(
        dataset,
        images_dir_path=str(images_dir),
        annotations_path=str(annotations_path),
    )

    assert annotations_path.exists()
    result = json.loads(annotations_path.read_text())
    assert result["annotations"]
    assert (images_dir / "src.jpg").exists()


def test_load_coco_dataset_simple_layout(tmp_path: Path):
    """Test loading a dataset with simple COCOAPI layout (single folder)."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img1.jpg").write_bytes(b"img1")
    (images_dir / "img2.jpg").write_bytes(b"img2")

    annotations_file = tmp_path / "annotations.json"
    _write_json(
        annotations_file,
        {
            "images": [
                {"id": 1, "file_name": "img1.jpg", "height": 10, "width": 8},
                {"id": 2, "file_name": "img2.jpg", "height": 12, "width": 10},
            ],
            "annotations": [
                {"id": 1, "image_id": 1, "category_id": 1, "bbox": [0, 0, 2, 2], "area": 4, "iscrowd": 0},
                {"id": 2, "image_id": 2, "category_id": 2, "bbox": [1, 1, 3, 3], "area": 9, "iscrowd": 0},
            ],
            "categories": [{"id": 1, "name": "cat"}, {"id": 2, "name": "dog"}],
        },
    )

    ds = load_coco_dataset(
        images_dir_path=str(images_dir),
        annotations_path=str(annotations_file),
    )

    assert len(ds) == 2
    # Simple layout should assign UNASSIGNED subset
    assert ds[0].subset == Subset.UNASSIGNED
    assert ds[1].subset == Subset.UNASSIGNED


def test_load_coco_dataset_split_layout(tmp_path: Path):
    """Test loading a dataset with split layout (multiple subsets)."""
    train_dir = tmp_path / "train"
    val_dir = tmp_path / "val"
    train_dir.mkdir()
    val_dir.mkdir()

    (train_dir / "train_img.jpg").write_bytes(b"train")
    (val_dir / "val_img.jpg").write_bytes(b"val")

    annotations_dir = tmp_path / "annotations"
    annotations_dir.mkdir()

    _write_json(
        annotations_dir / "train.json",
        {
            "images": [{"id": 1, "file_name": "train_img.jpg", "height": 10, "width": 8}],
            "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [0, 0, 2, 2], "area": 4, "iscrowd": 0}],
            "categories": [{"id": 1, "name": "cat"}],
        },
    )
    _write_json(
        annotations_dir / "val.json",
        {
            "images": [{"id": 2, "file_name": "val_img.jpg", "height": 12, "width": 10}],
            "annotations": [{"id": 2, "image_id": 2, "category_id": 1, "bbox": [1, 1, 3, 3], "area": 9, "iscrowd": 0}],
            "categories": [{"id": 1, "name": "cat"}],
        },
    )

    ds = load_coco_dataset(
        images_dir_path={
            "training": str(train_dir),
            "validation": str(val_dir),
        },
        annotations_path={
            "training": str(annotations_dir / "train.json"),
            "validation": str(annotations_dir / "val.json"),
        },
    )

    assert len(ds) == 2
    # Check subsets are correctly assigned
    subsets = {s.subset for s in ds}
    assert Subset.TRAINING in subsets
    assert Subset.VALIDATION in subsets


def test_save_coco_dataset_split_layout(tmp_path: Path):
    """Test saving a dataset with split layout (multiple subsets)."""
    dataset = Dataset(CocoSample, categories={"labels": CocoCategories()})

    # Create training sample
    train_img = tmp_path / "train_src.jpg"
    train_img.write_bytes(b"train")
    train_sample = CocoSample(
        image=str(train_img),
        image_info=ImageInfo(height=2, width=3),
        bboxes=np.array([[0.0, 0.0, 1.0, 1.0]], dtype=np.float32),
        polygons=None,
        labels=np.array([0], dtype=np.int32),
        areas=np.array([1.0], dtype=np.float32),
        iscrowd=np.array([0], dtype=np.int32),
        subset=Subset.TRAINING,
        image_id=1,
        caption_group_ids=None,
        captions=None,
        keypoints=None,
    )
    dataset.append(train_sample)

    # Create validation sample
    val_img = tmp_path / "val_src.jpg"
    val_img.write_bytes(b"val")
    val_sample = CocoSample(
        image=str(val_img),
        image_info=ImageInfo(height=4, width=5),
        bboxes=np.array([[1.0, 1.0, 2.0, 2.0]], dtype=np.float32),
        polygons=None,
        labels=np.array([1], dtype=np.int32),
        areas=np.array([4.0], dtype=np.float32),
        iscrowd=np.array([0], dtype=np.int32),
        subset=Subset.VALIDATION,
        image_id=2,
        caption_group_ids=None,
        captions=None,
        keypoints=None,
    )
    dataset.append(val_sample)

    export_dir = tmp_path / "export"
    train_export_dir = export_dir / "train"
    val_export_dir = export_dir / "val"
    annotations_dir = export_dir / "annotations"

    save_coco_dataset(
        dataset,
        images_dir_path={
            "training": str(train_export_dir),
            "validation": str(val_export_dir),
        },
        annotations_path={
            "training": str(annotations_dir / "train.json"),
            "validation": str(annotations_dir / "val.json"),
        },
    )

    # Check training subset
    assert (annotations_dir / "train.json").exists()
    train_result = json.loads((annotations_dir / "train.json").read_text())
    assert len(train_result["images"]) == 1
    assert (train_export_dir / "train_src.jpg").exists()

    # Check validation subset
    assert (annotations_dir / "val.json").exists()
    val_result = json.loads((annotations_dir / "val.json").read_text())
    assert len(val_result["images"]) == 1
    assert (val_export_dir / "val_src.jpg").exists()


def test_load_coco_dataset_mismatched_keys(tmp_path: Path):
    """Test that mismatched subset keys between images and annotations raise an error."""
    with pytest.raises(ValueError) as exc_info:
        load_coco_dataset(
            images_dir_path={"train": str(tmp_path)},
            annotations_path={"val": str(tmp_path / "val.json")},
        )
    assert "Subset keys must match" in str(exc_info.value)


def test_load_coco_dataset_attaches_keypoint_categories(tmp_path: Path):
    """When annotation file contains keypoint names, the dataset should have KeypointCategories."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img.jpg").write_bytes(b"img")

    annotations_file = tmp_path / "person_keypoints.json"
    _write_json(
        annotations_file,
        {
            "images": [{"id": 1, "file_name": "img.jpg", "height": 10, "width": 8}],
            "annotations": [
                {
                    "id": 1,
                    "image_id": 1,
                    "category_id": 1,
                    "keypoints": [100, 200, 2, 150, 250, 2, 180, 220, 1],
                    "num_keypoints": 3,
                }
            ],
            "categories": [
                {
                    "id": 1,
                    "name": "person",
                    "keypoints": ["nose", "left_eye", "right_eye"],
                    "skeleton": [[0, 1], [0, 2]],
                }
            ],
        },
    )

    ds = load_coco_dataset(
        images_dir_path=str(images_dir),
        annotations_path=str(annotations_file),
    )

    kp_categories = ds.schema.get_categories_for_field("keypoints")
    assert isinstance(kp_categories, KeypointCategories)
    assert kp_categories.labels == ("nose", "left_eye", "right_eye")


def test_load_coco_dataset_no_keypoint_categories_when_absent(tmp_path: Path):
    """When annotation file has no keypoint names, keypoint categories should not be attached."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img.jpg").write_bytes(b"img")

    annotations_file = tmp_path / "instances.json"
    _write_json(
        annotations_file,
        {
            "images": [{"id": 1, "file_name": "img.jpg", "height": 10, "width": 8}],
            "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [0, 0, 2, 2], "area": 4, "iscrowd": 0}],
            "categories": [{"id": 1, "name": "cat"}],
        },
    )

    ds = load_coco_dataset(
        images_dir_path=str(images_dir),
        annotations_path=str(annotations_file),
    )

    kp_categories = ds.schema.get_categories_for_field("keypoints")
    assert kp_categories is None


def test_load_coco_dataset_keypoint_categories_from_second_file(tmp_path: Path):
    """KeypointCategories should be detected even when only the second annotation file has them."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img.jpg").write_bytes(b"img")

    instances_file = tmp_path / "instances.json"
    _write_json(
        instances_file,
        {
            "images": [{"id": 1, "file_name": "img.jpg", "height": 10, "width": 8}],
            "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [0, 0, 2, 2], "area": 4, "iscrowd": 0}],
            "categories": [{"id": 1, "name": "person"}],
        },
    )
    keypoints_file = tmp_path / "person_keypoints.json"
    _write_json(
        keypoints_file,
        {
            "images": [{"id": 1, "file_name": "img.jpg", "height": 10, "width": 8}],
            "annotations": [],
            "categories": [
                {
                    "id": 1,
                    "name": "person",
                    "keypoints": ["left_hip", "right_hip"],
                }
            ],
        },
    )

    ds = load_coco_dataset(
        images_dir_path=str(images_dir),
        annotations_path=[str(instances_file), str(keypoints_file)],
    )

    kp_categories = ds.schema.get_categories_for_field("keypoints")
    assert isinstance(kp_categories, KeypointCategories)
    assert kp_categories.labels == ("left_hip", "right_hip")


@pytest.mark.parametrize(
    ("subset_name", "expected"),
    [
        ("train", Subset.TRAINING),
        ("Training", Subset.TRAINING),
        ("val", Subset.VALIDATION),
        ("test", Subset.TESTING),
        ("train2017", Subset.TRAINING),
        ("val2017", Subset.VALIDATION),
        ("test2017", Subset.TESTING),
        ("train2014", Subset.TRAINING),
        ("val2014", Subset.VALIDATION),
        ("test2015", Subset.TESTING),
        ("VAL_2017", Subset.VALIDATION),
        ("test-dev2017", Subset.UNASSIGNED),
        ("unlabeled2017", Subset.UNASSIGNED),
        ("default", Subset.UNASSIGNED),
        ("2017", Subset.UNASSIGNED),
    ],
)
def test_subset_name_to_enum(subset_name: str, expected: Subset):
    assert _subset_name_to_enum(subset_name) == expected


def _setup_official_coco_layout(root: Path, year: str) -> None:
    """Create a tiny dataset following the official cocodataset.org layout:
    ``images/{train,val,test}<year>/`` and ``annotations/*_<split><year>.json``.
    """
    categories = [{"id": 1, "name": "person"}, {"id": 2, "name": "dog"}]
    splits = {"train": [1, 2, 3], "val": [4, 5], "test": [6]}
    for split, image_ids in splits.items():
        images_dir = root / "images" / f"{split}{year}"
        images_dir.mkdir(parents=True)
        images = []
        for image_id in image_ids:
            file_name = f"{image_id:012d}.jpg"
            (images_dir / file_name).write_bytes(b"img")
            images.append({"id": image_id, "file_name": file_name, "height": 10, "width": 8})

        if split == "test":
            # The test split only ships image info, without annotations
            _write_json(
                root / "annotations" / f"image_info_{split}{year}.json",
                {"images": images, "categories": categories},
            )
        else:
            annotations = [
                {"id": i, "image_id": i, "category_id": 1, "bbox": [0, 0, 2, 2], "area": 4, "iscrowd": 0}
                for i in image_ids
            ]
            _write_json(
                root / "annotations" / f"instances_{split}{year}.json",
                {"images": images, "annotations": annotations, "categories": categories},
            )


@pytest.mark.parametrize("year", ["2017", "2014"])
def test_import_coco_dataset_official_year_suffixed_layout(tmp_path: Path, year: str):
    """Official COCO layout with year-suffixed subset folders must map to known subsets."""
    root = tmp_path / "coco"
    _setup_official_coco_layout(root, year)

    ds = import_coco_dataset(root)

    assert len(ds) == 6
    subsets_by_image_id = {s.image_id: s.subset for s in ds}
    assert subsets_by_image_id == {
        1: Subset.TRAINING,
        2: Subset.TRAINING,
        3: Subset.TRAINING,
        4: Subset.VALIDATION,
        5: Subset.VALIDATION,
        6: Subset.TESTING,
    }


def test_load_coco_dataset_keeps_subsets_mapping_to_same_enum(tmp_path: Path):
    """Several subset names resolving to the same Subset value must all be loaded."""
    images_config = {}
    annotations_config = {}
    for image_id, subset_name in enumerate(["foo", "bar"], start=1):
        images_dir = tmp_path / subset_name
        images_dir.mkdir()
        (images_dir / "img.jpg").write_bytes(b"img")
        annotations_file = tmp_path / f"{subset_name}.json"
        _write_json(
            annotations_file,
            {
                "images": [{"id": image_id, "file_name": "img.jpg", "height": 10, "width": 8}],
                "annotations": [],
                "categories": [{"id": 1, "name": "cat"}],
            },
        )
        images_config[subset_name] = str(images_dir)
        annotations_config[subset_name] = str(annotations_file)

    ds = load_coco_dataset(images_dir_path=images_config, annotations_path=annotations_config)

    assert len(ds) == 2
    assert all(s.subset == Subset.UNASSIGNED for s in ds)


# ---------------------------------------------------------------------------
# Roboflow COCO layout tests
# ---------------------------------------------------------------------------


def _make_roboflow_coco_annotations(categories=None, num_images=2, num_annotations=3):
    """Helper to create a minimal Roboflow-style COCO annotation dict."""
    if categories is None:
        categories = [
            {"id": 1, "name": "cat", "supercategory": "none"},
            {"id": 2, "name": "dog", "supercategory": "none"},
        ]
    images = [{"id": i, "file_name": f"img_{i}.jpg", "height": 100, "width": 200} for i in range(num_images)]
    annotations = [
        {
            "id": a,
            "image_id": a % num_images,
            "category_id": categories[0]["id"],
            "bbox": [10, 20, 30, 40],
            "area": 1200,
            "segmentation": [],
            "iscrowd": 0,
        }
        for a in range(num_annotations)
    ]
    return {
        "info": {"description": "Exported from roboflow.com"},
        "licenses": [{"id": 1, "url": "", "name": "Unknown"}],
        "categories": categories,
        "images": images,
        "annotations": annotations,
    }


def _setup_roboflow_layout(root: Path, subsets=("train",)):
    """Create a Roboflow-style directory layout under *root*."""
    for subset_name in subsets:
        subset_dir = root / subset_name
        subset_dir.mkdir(parents=True, exist_ok=True)
        ann_data = _make_roboflow_coco_annotations()
        _write_json(subset_dir / "_annotations.coco.json", ann_data)
        for img in ann_data["images"]:
            (subset_dir / img["file_name"]).write_bytes(b"fake-img")


def test_is_roboflow_coco_layout_detected(tmp_path: Path):
    """_is_roboflow_coco_layout returns True for Roboflow directories."""
    _setup_roboflow_layout(tmp_path, subsets=("train",))
    assert _is_roboflow_coco_layout(tmp_path) is True


def test_is_roboflow_coco_layout_not_detected(tmp_path: Path):
    """_is_roboflow_coco_layout returns False for empty or non-Roboflow dirs."""
    assert _is_roboflow_coco_layout(tmp_path) is False


def test_is_coco_format_roboflow(tmp_path: Path):
    """is_coco_format recognises Roboflow layout."""
    _setup_roboflow_layout(tmp_path, subsets=("train", "valid"))
    assert is_coco_format(tmp_path) is True


def test_detect_dataset_format_roboflow(tmp_path: Path):
    """detect_dataset_format returns COCO for Roboflow layout."""
    _setup_roboflow_layout(tmp_path, subsets=("train",))
    assert detect_dataset_format(tmp_path) == DataFormat.COCO


def test_detect_roboflow_coco_layout_single_subset(tmp_path: Path):
    """_detect_roboflow_coco_layout returns correct config for train only."""
    _setup_roboflow_layout(tmp_path, subsets=("train",))
    result = _detect_roboflow_coco_layout(tmp_path)
    assert result is not None
    images_config, annotations_config = result
    assert set(images_config.keys()) == {"train"}
    assert str(tmp_path / "train") == images_config["train"]
    assert len(annotations_config["train"]) == 1


def test_detect_roboflow_coco_layout_multiple_subsets(tmp_path: Path):
    """_detect_roboflow_coco_layout picks up train, valid, and test."""
    _setup_roboflow_layout(tmp_path, subsets=("train", "valid", "test"))
    result = _detect_roboflow_coco_layout(tmp_path)
    assert result is not None
    images_config, _ = result
    assert set(images_config.keys()) == {"train", "valid", "test"}


def test_import_coco_dataset_roboflow_layout(tmp_path: Path):
    """import_coco_dataset loads a Roboflow-style dataset correctly."""
    _setup_roboflow_layout(tmp_path, subsets=("train", "valid"))
    ds = import_coco_dataset(tmp_path)
    # 2 images per subset * 2 subsets = 4
    assert len(ds) == 4
    subsets = {s.subset for s in ds}
    assert Subset.TRAINING in subsets
    assert Subset.VALIDATION in subsets


def test_import_coco_dataset_roboflow_train_only(tmp_path: Path):
    """import_coco_dataset works with a single Roboflow subset."""
    _setup_roboflow_layout(tmp_path, subsets=("train",))
    ds = import_coco_dataset(tmp_path)
    assert len(ds) == 2
    assert all(s.subset == Subset.TRAINING for s in ds)


def test_import_coco_dataset_roboflow_annotations(tmp_path: Path):
    """Annotations are loaded correctly from Roboflow layout."""
    _setup_roboflow_layout(tmp_path, subsets=("train",))
    ds = import_coco_dataset(tmp_path)
    sample = ds[0]
    assert sample.bboxes is not None
    assert sample.labels is not None


def test_find_dataset_root_roboflow_with_extra_files(tmp_path: Path):
    """find_dataset_root detects Roboflow layout even with extra files like README."""
    root = tmp_path / "dataset"
    root.mkdir()
    _setup_roboflow_layout(root, subsets=("train",))
    # Add extra file like Roboflow's README
    (root / "README.roboflow.txt").write_text("metadata")
    # find_dataset_root should return root since format is detectable there
    assert find_dataset_root(root) == root.resolve()
