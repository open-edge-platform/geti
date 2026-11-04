import json
from pathlib import Path

import numpy as np
import pytest

from getidata import Dataset
from getidata.categories import KeypointCategories, LabelCategories
from getidata.data_formats.coco.helpers import (
    InstanceArrays,
    _assemble_sample_from_image_record,
    _build_and_copy_images_section,
    _build_subset_config,
    _cat_id_to_idx_from_primary,
    _collect_captions_for_image,
    _collect_instances_for_image,
    _collect_keypoints_for_image,
    _detect_coco_keypoint_categories_from_paths,
    _index_annotations_by_image,
    _load_json_or_none,
    _prepare_categories,
    _save_subset,
    _segmentation_to_poly,
    _segmentation_to_poly_parts,
    _serialize_annotations_for_subset,
    _serialize_captions_for_sample,
    _serialize_instances_for_sample,
    _serialize_keypoints_for_sample,
    _serialize_single_instance,
    _trim_poly_row,
    _validate_and_normalize_instance_arrays,
    _write_json,
)
from getidata.data_formats.coco.sample import CocoSample
from getidata.fields import ImageInfo, Subset


def test_segmentation_to_poly_from_nested_list():
    segm = [[0, 0, 2, 0, 2, 2, 0, 2]]
    poly = _segmentation_to_poly(segm)
    assert poly.shape == (4, 2)
    assert np.allclose(poly, np.array([[0, 0], [2, 0], [2, 2], [0, 2]], dtype=np.float32))


class SegmentationToPolyPartsTest:
    """Unit tests for _segmentation_to_poly_parts multi-part polygon splitting."""

    def test_none_returns_empty_array(self):
        result = _segmentation_to_poly_parts(None)
        assert len(result) == 1
        assert result[0].shape == (0, 2)

    def test_single_flat_polygon(self):
        segm = [10.0, 20.0, 30.0, 20.0, 30.0, 40.0]
        result = _segmentation_to_poly_parts(segm)
        assert len(result) == 1
        expected = np.array([[10, 20], [30, 20], [30, 40]], dtype=np.float32)
        assert np.allclose(result[0], expected)

    def test_single_nested_polygon(self):
        segm = [[10.0, 20.0, 30.0, 20.0, 30.0, 40.0]]
        result = _segmentation_to_poly_parts(segm)
        assert len(result) == 1
        expected = np.array([[10, 20], [30, 20], [30, 40]], dtype=np.float32)
        assert np.allclose(result[0], expected)

    def test_multi_part_polygon_splits_into_separate_arrays(self):
        part1 = [0.0, 0.0, 10.0, 0.0, 10.0, 10.0, 0.0, 10.0]
        part2 = [20.0, 20.0, 30.0, 20.0, 30.0, 30.0, 20.0, 30.0]
        segm = [part1, part2]
        result = _segmentation_to_poly_parts(segm)
        assert len(result) == 2
        assert result[0].shape == (4, 2)
        assert result[1].shape == (4, 2)
        assert np.allclose(result[0], np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float32))
        assert np.allclose(result[1], np.array([[20, 20], [30, 20], [30, 30], [20, 30]], dtype=np.float32))

    def test_multi_part_skips_too_short_parts(self):
        valid = [0.0, 0.0, 10.0, 0.0, 10.0, 10.0]
        too_short = [1.0, 2.0]  # Only 1 point, needs at least 3
        segm = [valid, too_short]
        result = _segmentation_to_poly_parts(segm)
        assert len(result) == 1
        assert result[0].shape == (3, 2)


def test_trim_poly_row_discard_trailing_zero_rows():
    pts = np.array([[3, 3], [4, 4], [0, 0], [0, 0]], dtype=np.float32)
    trimmed = _trim_poly_row(pts)
    assert trimmed == pytest.approx([3.0, 3.0, 4.0, 4.0])


def test_validate_and_normalize_instance_arrays_reshapes_and_checks_lengths():
    bbox = np.array([1, 2, 3, 4], dtype=np.float32)
    poly = np.array([[0, 0], [1, 1]], dtype=np.float32)
    polygons = np.empty((1,), dtype=object)
    polygons[0] = poly

    labels = np.array([0], dtype=np.int32)
    areas = np.array([[16.0]], dtype=np.float32)
    iscrowd = np.array([[0]], dtype=np.int32)

    n_inst, arrays = _validate_and_normalize_instance_arrays(bbox, polygons, labels, areas, iscrowd)
    assert n_inst == 1
    assert isinstance(arrays, InstanceArrays)
    assert arrays.bboxes.shape == (1, 4)
    assert arrays.polygons.shape == (1,)
    assert arrays.areas.shape == (1,)
    assert arrays.iscrowd.shape == (1,)

    bad_bboxes = np.zeros((2, 4), dtype=np.float32)
    with pytest.raises(ValueError, match="bboxes\\.shape"):
        _validate_and_normalize_instance_arrays(bad_bboxes, polygons, labels, areas, iscrowd)


def test_serialize_single_instance_uses_polygon_to_fill_bbox_and_area():
    bbox = np.array([0, 0, 0, 0], dtype=np.float32)
    poly = np.array([[1, 1], [4, 1], [4, 3], [1, 3]], dtype=np.float32)
    polygons = np.empty((1,), dtype=object)
    polygons[0] = poly
    labels = np.array([2], dtype=np.int32)
    areas = np.empty((0,), dtype=np.float32)
    iscrowd = np.array([[1]], dtype=np.int32)

    _, arrays = _validate_and_normalize_instance_arrays(bbox, polygons, labels, areas, iscrowd)

    def to_category_id(idx):
        return 10 if idx is None else idx + 1

    inst, next_ann = _serialize_single_instance(
        0,
        arrays,
        to_category_id,
        image_id=7,
        next_ann_id=99,
    )

    assert next_ann == 100
    assert inst["id"] == 99
    assert inst["image_id"] == 7
    assert inst["category_id"] == 3
    assert inst["bbox"] == pytest.approx([1.0, 1.0, 3.0, 2.0])
    assert inst["area"] == pytest.approx(6.0)
    assert inst["iscrowd"] == 1
    assert inst["segmentation"]
    assert inst["segmentation"][0] == pytest.approx([1.0, 1.0, 4.0, 1.0, 4.0, 3.0, 1.0, 3.0])


def test_round_and_json_helpers(tmp_path: Path):
    data = {"value": 3.14159, "nested": [1.237, {"more": 2.71828}]}
    path = tmp_path / "obj.json"
    _write_json(path, data)
    loaded_raw = json.loads(path.read_text())
    assert loaded_raw["value"] == pytest.approx(3.14)
    assert loaded_raw["nested"][0] == pytest.approx(1.24)
    assert _load_json_or_none(path)["nested"][1]["more"] == pytest.approx(2.72)
    assert _load_json_or_none(path.with_name("missing.json")) is None


def test_build_subset_config_detects_optional_test_dir(tmp_path: Path):
    (tmp_path / "annotations").mkdir()
    (tmp_path / "train2017").mkdir()
    (tmp_path / "val2017").mkdir()
    cfg = _build_subset_config(tmp_path, "2017")
    assert set(cfg) == {Subset.TRAINING, Subset.VALIDATION}
    (tmp_path / "test2017").mkdir()
    cfg_with_test = _build_subset_config(tmp_path, "2017")
    assert Subset.TESTING in cfg_with_test
    assert cfg_with_test[Subset.TESTING]["instances"].name == "instances_test2017.json"


def test_category_indexing_and_annotation_grouping():
    primary = {"categories": [{"id": 5}, {"id": 1}]}
    mapping = _cat_id_to_idx_from_primary(primary)
    assert mapping == {1: 0, 5: 1}
    instances = {"annotations": [{"image_id": 1, "id": 7}]}
    grouped = _index_annotations_by_image(instances, None, None)
    assert grouped[0][1][0]["id"] == 7


def _make_sample(**overrides: object) -> CocoSample:
    defaults = dict(
        image="",
        image_info=ImageInfo(height=4, width=5),
        bboxes=np.array([[1, 2, 3, 4]], dtype=np.float32),
        polygons=None,
        labels=np.array([0], dtype=np.int32),
        areas=np.array([12.0], dtype=np.float32),
        iscrowd=np.array([0], dtype=np.int32),
        keypoints=None,
        captions=None,
        caption_group_ids=None,
        subset=Subset.TRAINING,
        image_id=1,
    )
    defaults.update(overrides)
    return CocoSample(**defaults)


def test_assemble_sample_from_image_record(tmp_path: Path):
    img_dir = tmp_path / "train2017"
    img_dir.mkdir()
    img = {"id": 1, "file_name": "im.jpg", "height": 10, "width": 8}
    instances = {
        1: [
            {
                "image_id": 1,
                "category_id": 4,
                "bbox": [0, 0, 2, 2],
                "segmentation": [[0, 0, 2, 0, 2, 2, 0, 2]],
                "iscrowd": 0,
            }
        ]
    }
    keypoints = {1: [{"image_id": 1, "keypoints": [0, 0, 2, 1, 1, 0]}]}
    captions = {1: [{"image_id": 1, "caption": "hello", "id": 99}]}
    sample = _assemble_sample_from_image_record(
        img_dir,
        img,
        {4: 0},
        instances,
        keypoints,
        captions,
        Subset.TRAINING,
    )
    assert sample.image.path.endswith("im.jpg")
    assert sample.labels.tolist() == [0]
    assert sample.keypoints.shape == (1, 2, 3)
    assert sample.captions.tolist() == ["hello"]


def test_build_and_copy_images_section(tmp_path: Path):
    src_img = tmp_path / "src.jpg"
    src_img.write_bytes(b"fake")
    subset_dir = tmp_path / "subset"
    subset_dir.mkdir()
    sample = _make_sample(image=str(src_img), image_id=3)
    images = _build_and_copy_images_section([sample], lambda s: s.image_id, subset_dir)
    assert images == [{"id": 3, "file_name": "src.jpg", "height": 4, "width": 5}]
    assert (subset_dir / "src.jpg").exists()


def test_build_and_copy_images_section_disambiguates_same_basename(tmp_path: Path):
    """Regression test for https://github.com/open-edge-platform/geti/issues/7496.

    Different source files sharing the same basename (e.g. video frames extracted
    from different videos into per-video directories, both named "frame000066.png")
    must not collide/overwrite each other when flattened into a single subset dir.
    """
    video_a_dir = tmp_path / "video_a_frames"
    video_b_dir = tmp_path / "video_b_frames"
    video_a_dir.mkdir()
    video_b_dir.mkdir()
    frame_a = video_a_dir / "frame000066.png"
    frame_b = video_b_dir / "frame000066.png"
    frame_a.write_bytes(b"frame-a")
    frame_b.write_bytes(b"frame-b")

    subset_dir = tmp_path / "subset"
    subset_dir.mkdir()

    sample_a = _make_sample(image=str(frame_a), image_id=1)
    sample_b = _make_sample(image=str(frame_b), image_id=2)

    images = _build_and_copy_images_section([sample_a, sample_b], lambda s: s.image_id, subset_dir)

    file_names = [img["file_name"] for img in images]
    assert len(set(file_names)) == 2, f"expected unique file names, got {file_names}"
    assert (subset_dir / file_names[0]).read_bytes() == b"frame-a"
    assert (subset_dir / file_names[1]).read_bytes() == b"frame-b"


def test_collect_helpers_extract_expected_fields():
    instances_by_image = {
        1: [
            {"image_id": 1, "category_id": 2, "bbox": [1, 1, 2, 2], "segmentation": [[0, 0, 2, 0, 2, 2, 0, 2]]},
        ]
    }
    bboxes, polys, labels, areas, iscrowd = _collect_instances_for_image(1, instances_by_image, {2: 0})
    assert bboxes[0] == [1.0, 1.0, 2.0, 2.0]  # Uses annotation bbox as primary source
    assert polys[0].shape == (4, 2)
    assert labels == [0]
    assert areas[0] == pytest.approx(4.0)
    assert iscrowd == [False]
    keypoints = _collect_keypoints_for_image(1, {1: [{"image_id": 1, "keypoints": [0, 0, 2]}]})
    assert keypoints[0].shape == (1, 3)
    caps = _collect_captions_for_image(
        1, {1: [{"image_id": 1, "caption": "hi", "id": 5}, {"image_id": 1, "caption": "", "id": 1}]}
    )
    assert caps == (["hi"], [5])


def test_collect_instances_uses_bbox_when_no_polygon():
    """Test that bbox values are preserved when there's no polygon segmentation."""
    instances_by_image = {
        1: [
            # Annotation with bbox but no polygon (empty segmentation)
            {
                "image_id": 1,
                "category_id": 1,
                "bbox": [100.0, 150.0, 200.0, 250.0],
                "area": 50000.0,
                "segmentation": [],
            },
        ]
    }
    bboxes, polys, labels, areas, iscrowd = _collect_instances_for_image(1, instances_by_image, {1: 0})

    # Should use the original bbox from annotation, not [0, 0, 0, 0]
    assert bboxes[0] == [100.0, 150.0, 200.0, 250.0]
    # Polygon should be empty
    assert polys[0].shape == (0, 2)
    assert labels == [0]
    # Should use the original area from annotation
    assert areas[0] == pytest.approx(50000.0)
    assert iscrowd == [False]


def test_collect_instances_multi_polygon_union_bbox():
    """Multi-part polygon annotation yields one bbox covering the union of all parts."""
    part1 = [0.0, 0.0, 10.0, 0.0, 10.0, 10.0, 0.0, 10.0]
    part2 = [20.0, 20.0, 30.0, 20.0, 30.0, 30.0, 20.0, 30.0]
    instances_by_image = {
        1: [
            {
                "image_id": 1,
                "category_id": 1,
                "bbox": [0, 0, 30, 30],
                "segmentation": [part1, part2],
            },
        ]
    }
    bboxes, polys, labels, areas, iscrowd = _collect_instances_for_image(1, instances_by_image, {1: 0})

    assert len(bboxes) == 1
    assert bboxes[0] == [0.0, 0.0, 30.0, 30.0]
    assert len(polys) == 1
    assert polys[0].shape == (8, 2)
    assert labels == [0]
    assert areas[0] == pytest.approx(900.0)
    assert iscrowd == [False]


def test_collect_instances_dedup_identical_annotations():
    """Exact duplicate (label + bbox) annotations are collapsed to one."""
    instances_by_image = {
        1: [
            {
                "image_id": 1,
                "category_id": 1,
                "bbox": [10, 10, 20, 20],
                "segmentation": [[10, 10, 30, 10, 30, 30, 10, 30]],
            },
            {
                "image_id": 1,
                "category_id": 1,
                "bbox": [10, 10, 20, 20],
                "segmentation": [[10, 10, 30, 10, 30, 30, 10, 30]],
            },
        ]
    }
    bboxes, _polys, labels, _areas, _iscrowd = _collect_instances_for_image(1, instances_by_image, {1: 0})

    assert len(bboxes) == 1
    assert bboxes[0] == [10.0, 10.0, 20.0, 20.0]
    assert labels == [0]


def test_serialize_instances_requires_labels():
    sample = _make_sample(labels=None)
    with pytest.raises(ValueError):
        _serialize_instances_for_sample(sample, 1, lambda _: 1, 1)


def test_serialize_instances_and_keypoints(tmp_path: Path):
    poly = np.array([[0, 0], [1, 0], [1, 1]], dtype=np.float32)
    polygons = np.empty((1,), dtype=object)
    polygons[0] = poly
    sample = _make_sample(polygons=polygons)
    inst, next_id = _serialize_instances_for_sample(sample, 5, lambda idx: (idx or 0) + 1, 10)
    assert inst[0]["bbox"] == pytest.approx([1, 2, 3, 4])
    assert next_id == 11
    kpts = np.array([[[0, 0, 2], [1, 1, 0]]], dtype=np.float32)
    sample.keypoints = kpts
    sample.labels = np.array([4], dtype=np.int32)
    keypoint_anns, next_kp = _serialize_keypoints_for_sample(sample, 5, lambda idx: idx or 0, 20)
    assert keypoint_anns[0]["num_keypoints"] == 1
    assert next_kp == 21


def test_serialize_captions_and_annotations():
    sample = _make_sample()
    sample.captions = np.array(["a", "b"], dtype=object)
    sample.caption_group_ids = np.array([7, 0], dtype=np.int32)
    captions, _ = _serialize_captions_for_sample(sample, 2, 1)
    assert [cap["id"] for cap in captions] == [7, 0]
    inst, _, cap = _serialize_annotations_for_subset([sample], lambda s: 1, lambda idx: (idx or 0) + 1)
    assert len(inst) == 1
    assert cap[0]["caption"] == "a"


def test_prepare_categories_and_save_subset(tmp_path: Path):
    dataset = Dataset(CocoSample, categories={"labels": LabelCategories(labels=("apple", "orange"))})
    cats, to_cat_id = _prepare_categories(dataset)
    assert cats[0]["name"] == "apple"
    assert to_cat_id(None) == 1
    assert to_cat_id(5) == 2
    sample = _make_sample(image=str(tmp_path / "x.jpg"))
    (tmp_path / "x.jpg").write_bytes(b"img")
    annotations_dir = tmp_path / "ann"
    annotations_dir.mkdir(parents=True, exist_ok=True)
    written = _save_subset(
        root_path=tmp_path,
        annotations_path=annotations_dir,
        version="2017",
        subset=Subset.TRAINING,
        samples=[sample],
        categories_coco=cats,
        to_category_id=to_cat_id,
    )
    assert "instances_train" in written
    content = json.loads(written["instances_train"].read_text())
    assert content["annotations"][0]["bbox"] == pytest.approx([1.0, 2.0, 3.0, 4.0])


def test_save_subset_image_id_none_consistency(tmp_path: Path):
    """Annotation image_ids must match image ids when samples have image_id=None.

    Regression test: previously the auto-assigned counter was not cached so
    _build_and_copy_images_section assigned ids 1..N while
    _serialize_annotations_for_subset assigned ids N+1..2N.
    """
    samples = [_make_sample(image=str(tmp_path / f"img{i}.jpg"), image_id=None) for i in range(3)]
    for i in range(3):
        (tmp_path / f"img{i}.jpg").write_bytes(b"img")

    cats = [{"id": 1, "name": "a", "supercategory": ""}]
    to_cat_id = lambda idx: 1  # noqa: E731

    annotations_dir = tmp_path / "ann"
    annotations_dir.mkdir(parents=True, exist_ok=True)
    written = _save_subset(
        root_path=tmp_path,
        annotations_path=annotations_dir,
        version="2017",
        subset=Subset.TRAINING,
        samples=samples,
        categories_coco=cats,
        to_category_id=to_cat_id,
    )
    content = json.loads(written["instances_train"].read_text())
    image_ids = {img["id"] for img in content["images"]}
    ann_image_ids = {ann["image_id"] for ann in content["annotations"]}
    assert ann_image_ids.issubset(image_ids), (
        f"Annotation image_ids {ann_image_ids} not a subset of image ids {image_ids}"
    )


class DetectCocoKeypointCategoriesTest:
    """Unit tests for _detect_coco_keypoint_categories_from_paths."""

    def test_returns_none_when_no_keypoints_in_categories(self, tmp_path: Path):
        ann_file = tmp_path / "instances.json"
        _write_json(
            ann_file,
            {
                "images": [],
                "annotations": [],
                "categories": [{"id": 1, "name": "person"}],
            },
        )
        config = {Subset.TRAINING: {"annotations": [ann_file]}}
        result = _detect_coco_keypoint_categories_from_paths(config)
        assert result is None

    def test_returns_none_when_no_categories_section(self, tmp_path: Path):
        ann_file = tmp_path / "instances.json"
        _write_json(ann_file, {"images": [], "annotations": []})
        config = {Subset.TRAINING: {"annotations": [ann_file]}}
        result = _detect_coco_keypoint_categories_from_paths(config)
        assert result is None

    def test_returns_none_when_annotations_key_missing(self):
        config = {Subset.TRAINING: {"images_dir": Path("/tmp")}}
        result = _detect_coco_keypoint_categories_from_paths(config)
        assert result is None

    def test_returns_none_when_file_does_not_exist(self, tmp_path: Path):
        config = {Subset.TRAINING: {"annotations": [tmp_path / "missing.json"]}}
        result = _detect_coco_keypoint_categories_from_paths(config)
        assert result is None

    def test_returns_none_for_empty_keypoints_list(self, tmp_path: Path):
        ann_file = tmp_path / "keypoints.json"
        _write_json(
            ann_file,
            {
                "images": [],
                "annotations": [],
                "categories": [{"id": 1, "name": "person", "keypoints": []}],
            },
        )
        config = {Subset.TRAINING: {"annotations": [ann_file]}}
        result = _detect_coco_keypoint_categories_from_paths(config)
        assert result is None

    def test_detects_keypoints_from_single_file(self, tmp_path: Path):
        ann_file = tmp_path / "person_keypoints.json"
        _write_json(
            ann_file,
            {
                "images": [],
                "annotations": [],
                "categories": [
                    {
                        "id": 1,
                        "name": "person",
                        "keypoints": ["nose", "left_eye", "right_eye"],
                    }
                ],
            },
        )
        config = {Subset.TRAINING: {"annotations": [ann_file]}}
        result = _detect_coco_keypoint_categories_from_paths(config)
        assert isinstance(result, KeypointCategories)
        assert result.labels == ("nose", "left_eye", "right_eye")

    def test_detects_keypoints_from_multiple_files(self, tmp_path: Path):
        instances_file = tmp_path / "instances.json"
        _write_json(
            instances_file,
            {
                "images": [],
                "annotations": [],
                "categories": [{"id": 1, "name": "person"}],
            },
        )
        kp_file = tmp_path / "person_keypoints.json"
        _write_json(
            kp_file,
            {
                "images": [],
                "annotations": [],
                "categories": [
                    {
                        "id": 1,
                        "name": "person",
                        "keypoints": ["nose", "left_eye"],
                    }
                ],
            },
        )
        config = {Subset.TRAINING: {"annotations": [instances_file, kp_file]}}
        result = _detect_coco_keypoint_categories_from_paths(config)
        assert isinstance(result, KeypointCategories)
        assert result.labels == ("nose", "left_eye")

    def test_detects_keypoints_across_subsets(self, tmp_path: Path):
        train_file = tmp_path / "train.json"
        _write_json(
            train_file,
            {
                "images": [],
                "annotations": [],
                "categories": [{"id": 1, "name": "person"}],
            },
        )
        val_file = tmp_path / "val_keypoints.json"
        _write_json(
            val_file,
            {
                "images": [],
                "annotations": [],
                "categories": [
                    {
                        "id": 1,
                        "name": "person",
                        "keypoints": ["ankle", "knee"],
                    }
                ],
            },
        )
        config = {
            Subset.TRAINING: {"annotations": [train_file]},
            Subset.VALIDATION: {"annotations": [val_file]},
        }
        result = _detect_coco_keypoint_categories_from_paths(config)
        assert isinstance(result, KeypointCategories)
        assert result.labels == ("ankle", "knee")

    def test_single_path_not_list(self, tmp_path: Path):
        ann_file = tmp_path / "keypoints.json"
        _write_json(
            ann_file,
            {
                "images": [],
                "annotations": [],
                "categories": [
                    {
                        "id": 1,
                        "name": "person",
                        "keypoints": ["nose"],
                    }
                ],
            },
        )
        config = {Subset.TRAINING: {"annotations": ann_file}}
        result = _detect_coco_keypoint_categories_from_paths(config)
        assert isinstance(result, KeypointCategories)
        assert result.labels == ("nose",)
