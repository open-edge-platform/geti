# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from getidata import Dataset
from getidata.categories import KeypointCategories, LabelCategories
from getidata.data_formats.base import unique_destination_filename
from getidata.data_formats.coco.sample import CocoCategories, CocoSample
from getidata.fields import ImageInfo, Subset

logger = logging.getLogger(__name__)


def _round_floats(x: Any, ndigits: int = 2):
    if isinstance(x, float):
        return round(x, ndigits)
    if isinstance(x, list):
        return [_round_floats(v, ndigits) for v in x]
    if isinstance(x, tuple):
        return tuple(_round_floats(v, ndigits) for v in x)
    if isinstance(x, dict):
        return {k: _round_floats(v, ndigits) for k, v in x.items()}
    return x


def _subset_name(s: Subset) -> str:
    return {
        Subset.TRAINING: "train",
        Subset.VALIDATION: "val",
        Subset.TESTING: "test",
        Subset.UNASSIGNED: "unassigned",
    }[s]


def _write_json(path: Path, obj: dict) -> None:
    obj = _round_floats(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def _load_json_or_none(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _build_subset_config(root_path: Path, version: str) -> dict[Subset, dict[str, Path]]:
    annotations_path = root_path / "annotations"
    train_images_dir = root_path / f"train{version}"
    val_images_dir = root_path / f"val{version}"
    test_images_dir = root_path / f"test{version}"

    subset_config: dict[Subset, dict[str, Path]] = {
        Subset.TRAINING: {
            "images_dir": train_images_dir,
            "instances": annotations_path / f"instances_train{version}.json",
            "keypoints": annotations_path / f"person_keypoints_train{version}.json",
            "captions": annotations_path / f"captions_train{version}.json",
        },
        Subset.VALIDATION: {
            "images_dir": val_images_dir,
            "instances": annotations_path / f"instances_val{version}.json",
            "keypoints": annotations_path / f"person_keypoints_val{version}.json",
            "captions": annotations_path / f"captions_val{version}.json",
        },
    }

    if test_images_dir.exists():
        subset_config[Subset.TESTING] = {
            "images_dir": test_images_dir,
            "instances": annotations_path / f"instances_test{version}.json",
            "keypoints": annotations_path / f"person_keypoints_test{version}.json",
            "captions": annotations_path / f"captions_test{version}.json",
        }
    return subset_config


def _detect_coco_label_categories_from_paths(
    subset_config: dict[Subset, dict[str, Path | list[Path]]],
) -> CocoCategories:
    """
    Detect COCO label categories by probing available annotation JSON files.

    Args:
        subset_config: Mapping with 'annotations' path(s) for each subset.
            The 'annotations' value can be a single Path or a list of Paths.

    Returns:
        CocoCategories instance with either discovered labels or defaults.
    """
    best_label_names: tuple[str, ...] | None = None
    best_count = 0

    for _subset, cfg in subset_config.items():
        annotations_paths = cfg.get("annotations")
        if annotations_paths is None:
            continue

        # Normalize to list for uniform handling
        if isinstance(annotations_paths, Path):
            paths_to_check = [annotations_paths]
        else:
            paths_to_check = annotations_paths

        for annotations_path in paths_to_check:
            annotations_data = _load_json_or_none(annotations_path)
            if annotations_data and isinstance(annotations_data, dict):
                cats = annotations_data.get("categories") or []
                if isinstance(cats, list) and len(cats) > best_count:
                    try:
                        cats_sorted = sorted(cats, key=lambda c: c["id"])  # type: ignore[index]
                        label_names = tuple(str(c["name"]) for c in cats_sorted)  # type: ignore[index]
                        best_label_names = label_names
                        best_count = len(cats)
                    except Exception:  # noqa: S110
                        pass

    if best_label_names is not None:
        return CocoCategories(labels=best_label_names)

    logger.warning("Unable to extract labels from COCO annotations, falling back to defaults")
    return CocoCategories()


def _detect_coco_keypoint_categories_from_paths(
    subset_config: dict[Subset, dict[str, Path | list[Path]]],
) -> KeypointCategories | None:
    """
    Detect COCO keypoint categories by probing available annotation JSON files.

    Looks for ``"keypoints"`` lists inside the ``"categories"`` section of each
    annotation file (the standard COCO format for person_keypoints files).

    Args:
        subset_config: Mapping with 'annotations' path(s) for each subset.

    Returns:
        KeypointCategories with discovered keypoint names, or None if not found.
    """
    for _subset, cfg in subset_config.items():
        annotations_paths = cfg.get("annotations")
        if annotations_paths is None:
            continue

        if isinstance(annotations_paths, Path):
            paths_to_check = [annotations_paths]
        else:
            paths_to_check = annotations_paths

        for annotations_path in paths_to_check:
            annotations_data = _load_json_or_none(annotations_path)
            if annotations_data and isinstance(annotations_data, dict):
                for cat in annotations_data.get("categories") or []:
                    if isinstance(cat, dict):
                        kp_names = cat.get("keypoints")
                        if isinstance(kp_names, list) and len(kp_names) > 0:
                            return KeypointCategories(labels=tuple(str(n) for n in kp_names))

    return None


def _cat_id_to_idx_from_primary(primary_data: dict) -> dict[int, int]:
    categories_list = sorted(primary_data.get("categories", []), key=lambda c: c["id"])  # type: ignore[index]
    return {c["id"]: i for i, c in enumerate(categories_list)}  # type: ignore[index]


def _index_annotations_by_image(instances: dict | None, keypoints: dict | None, captions: dict | None):
    instances_by_image: dict[int, list[dict]] = defaultdict(list)
    keypoints_by_image: dict[int, list[dict]] = defaultdict(list)
    captions_by_image: dict[int, list[dict]] = defaultdict(list)

    if instances:
        for ann in instances.get("annotations", []):
            instances_by_image[ann["image_id"]].append(ann)
    if keypoints:
        for ann in keypoints.get("annotations", []):
            keypoints_by_image[ann["image_id"]].append(ann)
    if captions:
        for ann in captions.get("annotations", []):
            captions_by_image[ann["image_id"]].append(ann)

    return instances_by_image, keypoints_by_image, captions_by_image


def _segmentation_to_poly(segm: Any) -> np.ndarray:
    # COCO segmentation can be list[list[float]] | list[float] | dict (RLE)
    if isinstance(segm, dict) or segm is None or (isinstance(segm, list) and len(segm) == 0):
        return np.zeros((0, 2), dtype=np.float32)
    if isinstance(segm, list):
        first = segm[0] if len(segm) > 0 else []
        flat = first if isinstance(first, list | tuple | np.ndarray) else segm
        try:
            arr = np.array(flat, dtype=np.float32)
            if arr.size % 2 == 0:
                return arr.reshape(-1, 2)
        except Exception:  # pragma: no cover - robust parsing
            return np.zeros((0, 2), dtype=np.float32)
    return np.zeros((0, 2), dtype=np.float32)


def _assemble_sample_from_image_record(
    images_dir: Path,
    img: dict,
    cat_id_to_idx: dict[int, int],
    instances_by_image: dict[int, list[dict]],
    keypoints_by_image: dict[int, list[dict]],
    captions_by_image: dict[int, list[dict]],
    subset: Subset,
) -> CocoSample:
    image_id = img["id"]
    image_path = str(images_dir / img["file_name"])  # type: ignore[index]

    # instances
    (
        bboxes_list,
        polygons_list,
        labels_list,
        areas_list,
        iscrowd_list,
    ) = _collect_instances_for_image(image_id, instances_by_image, cat_id_to_idx)

    # keypoints
    keypoints_list = _collect_keypoints_for_image(image_id, keypoints_by_image)

    # captions
    captions_list, caption_group_ids_list = _collect_captions_for_image(image_id, captions_by_image)

    bboxes = np.array(bboxes_list, dtype=np.float32) if bboxes_list else None
    if polygons_list:
        polygons = np.empty(len(polygons_list), dtype=object)
        for i, poly in enumerate(polygons_list):
            polygons[i] = poly
    else:
        polygons = None
    labels = np.array(labels_list, dtype=np.int32) if labels_list else None
    areas = np.array(areas_list, dtype=np.float64) if areas_list else None
    iscrowd = np.array(iscrowd_list, dtype=np.bool_) if iscrowd_list else None
    keypoints = np.array(keypoints_list, dtype=np.float32) if keypoints_list else None
    captions = np.array(captions_list, dtype=np.str_) if captions_list else None
    caption_group_ids = np.array(caption_group_ids_list, dtype=np.int32) if caption_group_ids_list else None

    return CocoSample(
        image=image_path,
        image_info=ImageInfo(height=img["height"], width=img["width"]),
        bboxes=bboxes,
        polygons=polygons,
        labels=labels,
        areas=areas,
        iscrowd=iscrowd,
        keypoints=keypoints,
        captions=captions,
        caption_group_ids=caption_group_ids,
        subset=subset,
        image_id=image_id,
    )


def _build_and_copy_images_section(
    samples: list[CocoSample],
    get_or_assign_image_id: Any,
    subset_dir: Path,
) -> list[dict]:
    images_section: list[dict] = []
    seen_images: set[int] = set()
    used_names: dict[str, str] = {}
    for s in samples:
        iid = get_or_assign_image_id(s)
        if iid in seen_images:
            continue
        seen_images.add(iid)

        image_path = Path(s.image) if s.image else None
        file_name = unique_destination_filename(image_path, used_names) if image_path is not None else ""
        info = s.image_info
        height = int(info.height) if (info is not None and getattr(info, "height", None) is not None) else 0
        width = int(info.width) if (info is not None and getattr(info, "width", None) is not None) else 0

        images_section.append(
            {
                "id": iid,
                "file_name": file_name,
                "height": height,
                "width": width,
            }
        )

        if image_path is not None and image_path.exists():
            dst_path = subset_dir / file_name
            if not dst_path.exists():
                try:
                    shutil.copy2(image_path, dst_path)
                except Exception as e:
                    logger.warning("Failed to copy image '%s' -> '%s': %s", image_path, dst_path, e)
    return images_section


def _trim_poly_row(pts_row: np.ndarray | None) -> list[float]:
    if not isinstance(pts_row, np.ndarray) or pts_row.ndim != 2 or pts_row.shape[1] != 2:
        return []
    trimmed = pts_row
    nz = np.where(np.any(trimmed != 0.0, axis=1))[0]
    if nz.size > 0:
        trimmed = trimmed[: nz[-1] + 1]
    else:
        trimmed = np.empty((0, 2), dtype=trimmed.dtype)
    return trimmed.astype(float).reshape(-1).tolist()


def _serialize_instances_for_sample(
    s: CocoSample, image_id: int, to_category_id: Any, next_ann_id: int
) -> tuple[list[dict], int]:
    out: list[dict] = []

    bboxes = s.bboxes
    polygons = s.polygons
    labels = s.labels
    areas_arr = s.areas
    iscrowd_arr = s.iscrowd

    if labels is None:
        b_count = int(bboxes.shape[0]) if isinstance(bboxes, np.ndarray) else 0
        p_count = int(polygons.shape[0]) if isinstance(polygons, np.ndarray) else 0
        if b_count > 0 or p_count > 0:
            raise ValueError(
                "CocoSample.labels is required when instance bboxes/polygons are present in unified COCO export"
            )
        return out, next_ann_id

    n_inst, arrays = _validate_and_normalize_instance_arrays(bboxes, polygons, labels, areas_arr, iscrowd_arr)

    for i in range(n_inst):
        inst, next_ann_id = _serialize_single_instance(i, arrays, to_category_id, image_id, next_ann_id)
        out.append(inst)

    return out, next_ann_id


def _serialize_keypoints_for_sample(
    s: CocoSample, image_id: int, to_category_id: Any, next_ann_id: int
) -> tuple[list[dict], int]:
    out: list[dict] = []
    keypoints = s.keypoints
    num_key_groups = int(keypoints.shape[0]) if isinstance(keypoints, np.ndarray) and keypoints.ndim >= 2 else 0
    for i in range(num_key_groups):
        kpts_flat: list[float] = []
        num_k = 0
        if isinstance(keypoints, np.ndarray) and i < num_key_groups:
            pts = keypoints[i]
            if isinstance(pts, np.ndarray) and pts.ndim == 2 and pts.shape[1] == 3:
                kpts_flat = pts.astype(float).reshape(-1).tolist()
                num_k = int(np.sum(pts[:, 2] > 0))
        label_idx = None
        if isinstance(s.labels, np.ndarray) and s.labels.size > 0:
            try:
                label_idx = int(s.labels[0])
            except Exception:
                label_idx = None
        category_id = to_category_id(label_idx)

        out.append(
            {
                "id": next_ann_id,
                "image_id": image_id,
                "category_id": category_id,
                "keypoints": kpts_flat,
                "num_keypoints": num_k,
            }
        )
        next_ann_id += 1
    return out, next_ann_id


def _serialize_captions_for_sample(s: CocoSample, image_id: int, next_ann_id: int) -> tuple[list[dict], int]:
    out: list[dict] = []
    captions = s.captions
    group_ids = s.caption_group_ids
    if isinstance(captions, list) and len(captions) == 0:
        captions = None
    if captions is not None:
        captions_list = captions.tolist() if hasattr(captions, "tolist") else list(captions)
        gid_list = group_ids.tolist() if isinstance(group_ids, np.ndarray) else None
        for i, cap in enumerate(captions_list):
            if not cap:
                continue
            if gid_list is not None and i < len(gid_list):
                ann_id = int(gid_list[i])
            else:
                ann_id = next_ann_id
                next_ann_id += 1
            out.append({"id": ann_id, "image_id": image_id, "caption": str(cap)})
    return out, next_ann_id


def _serialize_annotations_for_subset(
    samples: list[CocoSample], get_or_assign_image_id: Any, to_category_id: Any
) -> tuple[list[dict], list[dict], list[dict]]:
    next_ann_id_instances = 1
    next_ann_id_keypoints = 1
    next_ann_id_captions = 1

    instances_annotations: list[dict] = []
    keypoints_annotations: list[dict] = []
    captions_annotations: list[dict] = []

    for s in samples:
        image_id = s.image_id if isinstance(s.image_id, int) else get_or_assign_image_id(s)

        inst_out, next_ann_id_instances = _serialize_instances_for_sample(
            s, image_id, to_category_id, next_ann_id_instances
        )
        instances_annotations.extend(inst_out)

        kp_out, next_ann_id_keypoints = _serialize_keypoints_for_sample(
            s, image_id, to_category_id, next_ann_id_keypoints
        )
        keypoints_annotations.extend(kp_out)

        cap_out, next_ann_id_captions = _serialize_captions_for_sample(s, image_id, next_ann_id_captions)
        captions_annotations.extend(cap_out)

    return instances_annotations, keypoints_annotations, captions_annotations


def _collect_instances_for_image(
    image_id: int,
    instances_by_image: dict[int, list[dict]],
    cat_id_to_idx: dict[int, int],
) -> tuple[list[list[float] | None], list[np.ndarray], list[int | None], list[float], list[bool]]:
    bboxes_list: list[list[float] | None] = []
    polygons_list: list[np.ndarray] = []
    labels_list: list[int | None] = []
    areas_list: list[float] = []
    iscrowd_list: list[bool] = []

    for ann in instances_by_image.get(image_id, []):
        category_idx = cat_id_to_idx.get(ann.get("category_id"))
        segmentation = ann.get("segmentation")
        original_bbox = ann.get("bbox")
        original_area = ann.get("area")

        polygon_parts = _segmentation_to_poly_parts(segmentation)

        ic = ann.get("iscrowd", 0)
        try:
            iscrowd_val = bool(int(ic))
        except Exception:  # pragma: no cover - tolerant casting
            iscrowd_val = False

        valid_parts = [part for part in polygon_parts if part.size > 0]
        combined_poly = np.concatenate(valid_parts, axis=0) if valid_parts else np.zeros((0, 2), dtype=np.float32)

        if original_bbox is not None and len(original_bbox) == 4:
            computed_bbox = [float(v) for v in original_bbox]
            area = float(original_area) if original_area is not None else computed_bbox[2] * computed_bbox[3]
        elif valid_parts:
            x1 = float(combined_poly[:, 0].min())
            y1 = float(combined_poly[:, 1].min())
            x2 = float(combined_poly[:, 0].max())
            y2 = float(combined_poly[:, 1].max())
            computed_bbox: list[float] = [x1, y1, x2 - x1, y2 - y1]
            area = (x2 - x1) * (y2 - y1)
        else:
            computed_bbox = [0.0, 0.0, 0.0, 0.0]
            area = 0.0

        bboxes_list.append(computed_bbox)
        polygons_list.append(combined_poly)
        labels_list.append(category_idx)
        areas_list.append(area)
        iscrowd_list.append(iscrowd_val)

    if bboxes_list:
        seen: set[tuple[int | None, tuple[float, ...]]] = set()
        dedup_indices: list[int] = []
        for index, (bbox, label) in enumerate(zip(bboxes_list, labels_list)):
            key = (label, tuple(round(value, 2) for value in bbox) if bbox else ())
            if key not in seen:
                seen.add(key)
                dedup_indices.append(index)

        if len(dedup_indices) < len(bboxes_list):
            bboxes_list = [bboxes_list[index] for index in dedup_indices]
            polygons_list = [polygons_list[index] for index in dedup_indices]
            labels_list = [labels_list[index] for index in dedup_indices]
            areas_list = [areas_list[index] for index in dedup_indices]
            iscrowd_list = [iscrowd_list[index] for index in dedup_indices]

    return bboxes_list, polygons_list, labels_list, areas_list, iscrowd_list


def _segmentation_to_poly_parts(segm: Any) -> list[np.ndarray]:
    """Convert COCO segmentation to a list of polygon arrays, one per part.

    This handles multi-part polygons by returning each part as a separate array,
    ensuring each polygon part gets its own annotation.
    """
    if isinstance(segm, dict) or segm is None or (isinstance(segm, list) and len(segm) == 0):
        return [np.zeros((0, 2), dtype=np.float32)]

    if isinstance(segm, list):
        # Check if it's a list of polygon parts (list[list[float]]) or a single polygon (list[float])
        if len(segm) > 0 and isinstance(segm[0], (list, tuple, np.ndarray)):
            # Multi-part polygon: each element is a separate polygon part
            result = []
            for part in segm:
                try:
                    arr = np.array(part, dtype=np.float32)
                    if arr.size >= 6 and arr.size % 2 == 0:  # At least 3 points
                        result.append(arr.reshape(-1, 2))
                except Exception:  # noqa: S110
                    pass
            return result if result else [np.zeros((0, 2), dtype=np.float32)]
        # Single polygon (flat list of coordinates)
        try:
            arr = np.array(segm, dtype=np.float32)
            if arr.size >= 6 and arr.size % 2 == 0:
                return [arr.reshape(-1, 2)]
        except Exception:  # noqa: S110
            pass

    return [np.zeros((0, 2), dtype=np.float32)]


def _collect_keypoints_for_image(image_id: int, keypoints_by_image: dict[int, list[dict]]) -> list[np.ndarray]:
    keypoints_list: list[np.ndarray] = []
    for ann in keypoints_by_image.get(image_id, []):
        if ann.get("keypoints"):
            kpts = ann["keypoints"]
            keypoints_array = np.array(kpts, dtype=np.float32).reshape(-1, 3)
            keypoints_list.append(keypoints_array)
    return keypoints_list


def _collect_captions_for_image(image_id: int, captions_by_image: dict[int, list[dict]]) -> tuple[list[str], list[int]]:
    captions_list: list[str] = []
    caption_group_ids_list: list[int] = []
    for ann in captions_by_image.get(image_id, []):
        caption_text = ann.get("caption", "")
        annotation_id = ann.get("id", 0)
        if caption_text:
            captions_list.append(caption_text)
            caption_group_ids_list.append(annotation_id)
    return captions_list, caption_group_ids_list


def _prepare_categories(dataset: Dataset[CocoSample]):
    label_categories: CocoCategories | None = None
    try:
        schema = dataset.schema
        if "labels" in schema.attributes and getattr(schema.attributes["labels"], "categories", None):
            cats = schema.attributes["labels"].categories
            if isinstance(cats, (LabelCategories, CocoCategories)) and len(cats) > 0:
                label_categories = cats
    except Exception:
        logger.warning("CocoCategories not available for dataset. Exporting with default COCO labels.")
        label_categories = CocoCategories()

    categories_coco = [{"id": idx + 1, "name": name, "supercategory": ""} for idx, name in enumerate(label_categories)]

    def to_category_id(label_idx: int | None) -> int:
        return 1 if label_idx is None else min(max(label_idx, 0), len(label_categories) - 1) + 1

    return categories_coco, to_category_id


class _ImageIdAssigner:
    """Assigns stable image IDs to samples, reusing explicit IDs and auto-assigning others."""

    def __init__(self, samples: list[CocoSample]) -> None:
        explicit = {s.image_id for s in samples if isinstance(s.image_id, int)}
        self._used: set[int] = set(explicit)
        self._next: int = (max(explicit) + 1) if explicit else 1
        self._cache: dict[int, int] = {}

    def __call__(self, s: CocoSample) -> int:
        img_id = s.image_id
        if isinstance(img_id, int):
            # Track explicit IDs to prevent future auto-assigned collisions.
            self._used.add(img_id)
            return img_id
        sample_key = id(s)
        if sample_key in self._cache:
            return self._cache[sample_key]
        # Find the next unused image ID.
        while self._next in self._used:
            self._next += 1
        assigned = self._next
        self._used.add(assigned)
        self._next += 1
        self._cache[sample_key] = assigned
        return assigned


def _save_subset(
    *,
    root_path: Path,
    annotations_path: Path,
    version: str,
    subset: Subset,
    samples: list[CocoSample],
    categories_coco: list[dict],
    to_category_id: Any,
) -> dict[str, Path]:
    written: dict[str, Path] = {}
    get_or_assign_image_id = _ImageIdAssigner(samples)

    subset_dir = root_path / f"{_subset_name(subset)}{version}"
    subset_dir.mkdir(parents=True, exist_ok=True)

    images_section: list[dict] = _build_and_copy_images_section(samples, get_or_assign_image_id, subset_dir)

    instances_annotations, keypoints_annotations, captions_annotations = _serialize_annotations_for_subset(
        samples, get_or_assign_image_id, to_category_id
    )

    subset_key = _subset_name(subset)

    if len(instances_annotations) > 0 or len(images_section) > 0:
        inst_path = annotations_path / f"instances_{subset_key}{version}.json"
        _write_json(
            inst_path,
            {"images": images_section, "annotations": instances_annotations, "categories": categories_coco},
        )
        written[f"instances_{subset_key}"] = inst_path

    if len(keypoints_annotations) > 0 or len(images_section) > 0:
        kp_path = annotations_path / f"person_keypoints_{subset_key}{version}.json"
        _write_json(
            kp_path,
            {"images": images_section, "annotations": keypoints_annotations, "categories": categories_coco},
        )
        written[f"keypoints_{subset_key}"] = kp_path

    if len(captions_annotations) > 0 or len(images_section) > 0:
        cap_path = annotations_path / f"captions_{subset_key}{version}.json"
        _write_json(
            cap_path,
            {"images": images_section, "annotations": captions_annotations, "categories": []},
        )
        written[f"captions_{subset_key}"] = cap_path

    return written


def _save_subset_flexible(
    *,
    images_dir: Path,
    annotations_file: Path,
    samples: list[CocoSample],
    categories_coco: list[dict],
    to_category_id: Any,
) -> None:
    """
    Save samples to a single images directory and annotation file.

    Args:
        images_dir: Directory where images will be copied.
        annotations_file: Path to the annotation JSON file to write.
        samples: List of CocoSample objects to save.
        categories_coco: List of category dicts for the COCO format.
        to_category_id: Function to map label index to category ID.
    """
    images_dir.mkdir(parents=True, exist_ok=True)
    annotations_file.parent.mkdir(parents=True, exist_ok=True)

    get_or_assign_image_id = _ImageIdAssigner(samples)

    # Build images section and copy images
    images_section: list[dict] = _build_and_copy_images_section(samples, get_or_assign_image_id, images_dir)

    # Serialize annotations
    instances_annotations, keypoints_annotations, captions_annotations = _serialize_annotations_for_subset(
        samples, get_or_assign_image_id, to_category_id
    )

    # Merge all annotations into a single list
    all_annotations = instances_annotations + keypoints_annotations + captions_annotations

    # Write to a single JSON file
    _write_json(
        annotations_file,
        {
            "images": images_section,
            "annotations": all_annotations,
            "categories": categories_coco,
        },
    )


@dataclass
class InstanceArrays:
    bboxes: Any
    polygons: Any
    labels: Any
    areas: Any
    iscrowd: Any


def _validate_and_normalize_instance_arrays(
    bboxes: Any,
    polygons: Any,
    labels: Any,
    areas_arr: Any,
    iscrowd_arr: Any,
) -> tuple[int, InstanceArrays]:
    if isinstance(bboxes, np.ndarray) and bboxes.ndim == 1 and bboxes.size == 4:
        bboxes = bboxes.reshape(1, 4)

    n_inst = int(labels.shape[0])

    if isinstance(bboxes, np.ndarray) and bboxes.shape[0] not in (0, n_inst):
        raise ValueError(f"bboxes.shape[0] ({bboxes.shape[0]}) must match labels.shape[0] ({n_inst})")
    if isinstance(polygons, np.ndarray) and polygons.shape[0] not in (0, n_inst):
        raise ValueError(f"polygons.shape[0] ({polygons.shape[0]}) must match labels.shape[0] ({n_inst})")

    if isinstance(areas_arr, np.ndarray) and areas_arr.ndim > 1:
        areas_arr = areas_arr.reshape(-1)
    if isinstance(iscrowd_arr, np.ndarray) and iscrowd_arr.ndim > 1:
        iscrowd_arr = iscrowd_arr.reshape(-1)

    if isinstance(areas_arr, np.ndarray) and areas_arr.shape[0] not in (0, n_inst):
        raise ValueError(f"areas.shape[0] ({areas_arr.shape[0]}) must match labels.shape[0] ({n_inst})")
    if isinstance(iscrowd_arr, np.ndarray) and iscrowd_arr.shape[0] not in (0, n_inst):
        raise ValueError(f"iscrowd.shape[0] ({iscrowd_arr.shape[0]}) must match labels.shape[0] ({n_inst})")

    return n_inst, InstanceArrays(bboxes=bboxes, polygons=polygons, labels=labels, areas=areas_arr, iscrowd=iscrowd_arr)


def _serialize_single_instance(
    i: int,
    arrays: InstanceArrays,
    to_category_id: Any,
    image_id: int,
    next_ann_id: int,
) -> tuple[dict, int]:
    label_idx = None
    labels = arrays.labels
    if isinstance(labels, np.ndarray) and i < labels.shape[0]:
        label_idx = int(labels[i])
    category_id = to_category_id(label_idx)

    bbox = [0.0, 0.0, 0.0, 0.0]
    bboxes = arrays.bboxes
    if isinstance(bboxes, np.ndarray) and i < bboxes.shape[0]:
        bb = bboxes[i].tolist()
        if len(bb) == 4:
            bbox = [float(bb[0]), float(bb[1]), float(bb[2]), float(bb[3])]

    flat: list[float] = []
    polygons = arrays.polygons
    if isinstance(polygons, np.ndarray) and i < polygons.shape[0]:
        flat = _trim_poly_row(polygons[i])

    if (bbox[2] == 0.0 or bbox[3] == 0.0) and len(flat) >= 6:
        xs = flat[0::2]
        ys = flat[1::2]
        if xs and ys:
            x0, y0 = min(xs), min(ys)
            x1, y1 = max(xs), max(ys)
            bbox = [float(x0), float(y0), float(max(0.0, x1 - x0)), float(max(0.0, y1 - y0))]

    if isinstance(arrays.areas, np.ndarray) and i < arrays.areas.shape[0]:
        area_val = float(arrays.areas[i])
    else:
        area_val = float(bbox[2] * bbox[3]) if len(bbox) == 4 else 0.0

    if isinstance(arrays.iscrowd, np.ndarray) and i < arrays.iscrowd.shape[0]:
        try:
            iscrowd_val = int(bool(arrays.iscrowd[i]))
        except Exception:
            iscrowd_val = 0
    else:
        iscrowd_val = 0

    inst = {
        "id": next_ann_id,
        "image_id": image_id,
        "category_id": category_id,
        "bbox": bbox,
        "area": area_val,
        "iscrowd": iscrowd_val,
        "segmentation": [flat] if len(flat) >= 6 else [],
    }
    return inst, next_ann_id + 1
