# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Helper functions for YOLO dataset I/O.
"""

import logging
import shutil
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Literal

import numpy as np
import yaml

from getidata import Dataset
from getidata.categories import LabelCategories
from getidata.data_formats.base import IMAGE_EXTENSIONS, find_images, unique_destination_filename
from getidata.data_formats.yolo.constants import (
    DIR_NAME_TO_SUBSET,
    SUBSET_TO_DIR_NAME,
    TRADITIONAL_DIR_NAME_TO_SUBSET,
    TRADITIONAL_SUBSET_CONFIG_KEYS,
    TRADITIONAL_SUBSET_DIR_NAMES,
)
from getidata.data_formats.yolo.sample import YoloSample
from getidata.fields import ImageInfo, Subset

logger = logging.getLogger(__name__)


def _find_image_file(images_dir: Path, stem: str) -> Path | None:
    """Find an image file with any supported extension."""
    # Use glob to find all files starting with the stem, then filter by extension
    for candidate in images_dir.glob(f"{stem}.*"):
        if candidate.suffix.lower() in IMAGE_EXTENSIONS:
            return candidate
    return None


def _find_image_files(directory: Path) -> list[Path]:
    """Find all image files in a directory."""
    return sorted(Path(p) for p in find_images(str(directory)))


def _get_image_size(image_path: Path) -> tuple[int, int]:
    """Get image dimensions (height, width) using PIL, honoring EXIF orientation."""
    try:
        from PIL import Image

        from getidata.exif_utils import get_exif_orientation, get_oriented_size

        with Image.open(image_path) as img:
            w, h = img.size
            w, h = get_oriented_size(w, h, get_exif_orientation(img))
            return h, w  # height, width
    except Exception as e:
        logger.warning("Failed to read image size from %s: %s", image_path, e)
        return 0, 0


def _parse_yolo_annotation(anno_path: Path, image_width: int, image_height: int) -> tuple[list, list]:
    """
    Parse a YOLO annotation file.

    YOLO format: <class_id> <center_x> <center_y> <width> <height>
    All values are normalized to [0, 1] relative to image dimensions.

    Returns:
        Tuple of (bboxes in xywh absolute format, labels)
    """
    bboxes = []
    labels = []

    if not anno_path.exists():
        return bboxes, labels

    with open(anno_path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 5:
                logger.warning("Skipping invalid annotation line in %s: %s", anno_path, line)
                continue

            try:
                label_id = int(parts[0])
                center_x = float(parts[1])
                center_y = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])

                # Convert normalized coordinates to absolute xywh format
                abs_center_x = center_x * image_width
                abs_center_y = center_y * image_height
                abs_width = width * image_width
                abs_height = height * image_height

                bboxes.append([abs_center_x, abs_center_y, abs_width, abs_height])
                labels.append(label_id)
            except ValueError as e:
                logger.warning("Skipping malformed annotation line in %s: %s (%s)", anno_path, line, e)
                continue

    return bboxes, labels


def _detect_yolo_format(root_path: Path) -> Literal["ultralytics", "traditional", "unknown"]:
    """Detect the YOLO format based on directory structure."""
    # Check for Ultralytics format (data.yaml)
    if (root_path / "data.yaml").exists():
        return "ultralytics"

    # Check for traditional YOLO format (obj.names or obj.data)
    if (root_path / "obj.names").exists() or (root_path / "obj.data").exists():
        return "traditional"

    # Check for Ultralytics-style directory structure
    if (root_path / "images").is_dir() and (root_path / "labels").is_dir():
        return "ultralytics"

    return "unknown"


def _load_categories_from_yaml(yaml_path: Path) -> LabelCategories:
    """Load categories from a data.yaml file (Ultralytics format)."""

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    names = data.get("names", [])
    if isinstance(names, list):
        label_names = tuple(names)
    elif isinstance(names, dict):
        # Ultralytics format can also have {0: "class0", 1: "class1", ...}
        label_names = tuple(names[k] for k in sorted(names.keys()))
    else:
        raise ValueError(f"Invalid 'names' format in {yaml_path}: expected list or dict")

    return LabelCategories(labels=label_names)


def _load_categories_from_names(names_path: Path) -> LabelCategories:
    """Load categories from an obj.names file (traditional YOLO format)."""
    labels = []
    with open(names_path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if line:
                labels.append(line)
    return LabelCategories(labels=tuple(labels))


def _load_ultralytics_categories(root_path: Path) -> LabelCategories:
    """Load categories for Ultralytics format, trying yaml first then names files."""
    yaml_path = root_path / "data.yaml"
    if yaml_path.exists():
        return _load_categories_from_yaml(yaml_path)

    # Try to find any names file
    names_candidates = list(root_path.glob("*.names")) + list(root_path.glob("**/*.names"))
    if names_candidates:
        return _load_categories_from_names(names_candidates[0])

    logger.warning("[YOLO] No category file found, using empty categories")
    return LabelCategories(labels=())


def _resolve_within_root(root_path: Path, base_dirs: list[Path], raw_value: Any) -> Path | None:
    """
    Resolve a directory path taken from ``data.yaml`` against the dataset root.

    The value is treated as untrusted input: absolute paths are rejected and leading ``..`` /
    ``.`` components are dropped, so the result can never escape ``root_path``. The latter also
    makes Roboflow exports work, as they declare paths such as ``../train/images`` while
    ``data.yaml`` itself sits at the dataset root.

    Args:
        root_path: Dataset root directory; the result is guaranteed to be inside it.
        base_dirs: Directories to try the value against, in order of preference.
        raw_value: Value read from ``data.yaml``; a string or a list of strings.

    Returns:
        The resolved existing directory, or None if the value cannot be resolved.
    """
    candidates = raw_value if isinstance(raw_value, list | tuple) else [raw_value]
    resolved_root = root_path.resolve()

    for candidate in candidates:
        if not isinstance(candidate, str) or not candidate.strip():
            continue

        candidate_str = candidate.strip()
        pure_path = PurePosixPath(candidate_str.replace("\\", "/"))
        has_drive_letter = len(candidate_str) > 1 and candidate_str[1] == ":" and candidate_str[0].isalpha()
        if pure_path.is_absolute() or has_drive_letter:
            logger.warning("[YOLO] Ignoring absolute path in data.yaml: %s", candidate)
            continue

        # Only leading ".."/"." are stripped, so Roboflow-style "../train/images" resolves against
        # the dataset root. Inner navigation is left to resolve(), and the is_relative_to() check
        # below rejects anything that ends up outside the root.
        parts = list(pure_path.parts)
        while parts and parts[0] in (".", ".."):
            parts.pop(0)
        if not parts:
            continue
        relative_path = Path(*parts)

        for base_dir in base_dirs:
            resolved = (base_dir / relative_path).resolve()
            if not resolved.is_relative_to(resolved_root):
                logger.warning("[YOLO] Ignoring path in data.yaml pointing outside the dataset: %s", candidate)
                continue
            if resolved.is_dir():
                return resolved

    return None


def _derive_labels_dir(images_dir: Path, root_path: Path) -> Path | None:
    """
    Find the labels directory matching an images directory.

    Mirrors the Ultralytics convention of swapping the ``images`` path component for ``labels``,
    which covers both the data-first (``images/train`` -> ``labels/train``) and the split-first
    (``train/images`` -> ``train/labels``) layouts.
    """
    try:
        relative_parts = list(images_dir.relative_to(root_path.resolve()).parts)
    except ValueError:
        relative_parts = []

    for index in range(len(relative_parts) - 1, -1, -1):
        if relative_parts[index].lower() == "images":
            relative_parts[index] = "labels"
            candidate = root_path.resolve().joinpath(*relative_parts)
            if candidate.is_dir():
                return candidate
            break

    candidate = images_dir.parent / "labels"
    return candidate if candidate.is_dir() else None


def _subsets_from_yaml(root_path: Path) -> list[tuple[str, Path, Path | None]]:
    """Resolve subset directories declared in ``data.yaml``, if any."""
    yaml_path = root_path / "data.yaml"
    if not yaml_path.exists():
        return []

    try:
        with open(yaml_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError) as e:
        logger.warning("[YOLO] Failed to read %s: %s", yaml_path, e)
        return []

    if not isinstance(config, dict):
        return []

    base_dirs = [root_path.resolve()]
    declared_base = _resolve_within_root(root_path, base_dirs, config.get("path"))
    if declared_base is not None:
        base_dirs.insert(0, declared_base)

    subsets: list[tuple[str, Path, Path | None]] = []
    for subset_name in DIR_NAME_TO_SUBSET:
        if subset_name not in config:
            continue
        images_dir = _resolve_within_root(root_path, base_dirs, config[subset_name])
        if images_dir is None:
            logger.warning(
                "[YOLO] Could not resolve the '%s' path declared in %s: %s",
                subset_name,
                yaml_path,
                config[subset_name],
            )
            continue
        subsets.append((subset_name, images_dir, _derive_labels_dir(images_dir, root_path)))

    return subsets


def _subsets_from_dir_layout(root_path: Path) -> list[tuple[str, Path, Path | None]]:
    """
    Discover subset directories from the on-disk layout.

    Covers the data-first layout (``images/<subset>``) as well as the split-first layout
    (``<subset>/images``) used by Roboflow exports.
    """
    subsets: list[tuple[str, Path, Path | None]] = []

    images_dir = root_path / "images"
    if images_dir.is_dir():
        for subset_dir in sorted(images_dir.iterdir()):
            if subset_dir.is_dir():
                subsets.append((subset_dir.name, subset_dir, _derive_labels_dir(subset_dir.resolve(), root_path)))

    for subset_name in DIR_NAME_TO_SUBSET:
        subset_images_dir = root_path / subset_name / "images"
        if subset_images_dir.is_dir():
            subsets.append((subset_name, subset_images_dir, _derive_labels_dir(subset_images_dir.resolve(), root_path)))

    return subsets


def _resolve_ultralytics_subsets(root_path: Path) -> list[tuple[str, Path, Path | None]]:
    """
    Resolve the ``(subset_name, images_dir, labels_dir)`` triples of an Ultralytics dataset.

    Paths declared in ``data.yaml`` take precedence; the on-disk layout is then scanned to pick
    up any subset the config did not declare, or declared with a path that does not exist.
    """
    subsets: list[tuple[str, Path, Path | None]] = []
    seen_dirs: set[Path] = set()

    for subset_name, images_dir, labels_dir in _subsets_from_yaml(root_path) + _subsets_from_dir_layout(root_path):
        resolved_images_dir = images_dir.resolve()
        if resolved_images_dir in seen_dirs:
            continue
        seen_dirs.add(resolved_images_dir)
        subsets.append((subset_name, resolved_images_dir, labels_dir))

    return subsets


def _create_sample_from_image(
    image_path: Path,
    labels_subset_dir: Path | None,
    subset_enum: Subset,
) -> YoloSample | None:
    """Create a YoloSample from an image file (Ultralytics format)."""
    height, width = _get_image_size(image_path)

    # Find corresponding annotation file
    anno_path = None
    if labels_subset_dir:
        anno_path = labels_subset_dir / f"{image_path.stem}.txt"

    # Parse annotations
    bboxes_list = []
    labels_list = []
    if anno_path and anno_path.exists() and width > 0 and height > 0:
        bboxes_list, labels_list = _parse_yolo_annotation(anno_path, width, height)

    # Create sample
    bboxes = np.array(bboxes_list, dtype=np.float32) if bboxes_list else None
    labels = np.array(labels_list, dtype=np.int32) if labels_list else None

    return YoloSample(
        image=str(image_path),
        image_info=ImageInfo(height=height, width=width),
        bboxes=bboxes,
        labels=labels,
        subset=subset_enum,
    )


def _create_sample_from_traditional_image(
    image_path: Path,
    subset_enum: Subset,
) -> YoloSample | None:
    """Create a YoloSample from a traditional YOLO image file (annotation alongside image)."""
    height, width = _get_image_size(image_path)

    # Annotation file is alongside the image
    anno_path = image_path.with_suffix(".txt")

    bboxes_list = []
    labels_list = []
    if anno_path.exists() and width > 0 and height > 0:
        bboxes_list, labels_list = _parse_yolo_annotation(anno_path, width, height)

    bboxes = np.array(bboxes_list, dtype=np.float32) if bboxes_list else None
    labels = np.array(labels_list, dtype=np.int32) if labels_list else None

    return YoloSample(
        image=str(image_path),
        image_info=ImageInfo(height=height, width=width),
        bboxes=bboxes,
        labels=labels,
        subset=subset_enum,
    )


# =============================================================================
# Dataset Helpers (Saving)
# =============================================================================


def _group_samples_by_subset(dataset: Dataset[YoloSample]) -> dict[Subset, list[YoloSample]]:
    """Group dataset samples by their subset."""
    subset_to_samples: dict[Subset, list[YoloSample]] = defaultdict(list)
    for sample in dataset:
        subset_to_samples[sample.subset].append(sample)
    return subset_to_samples


def _get_label_names_from_dataset(dataset: Dataset[YoloSample]) -> list[str]:
    """Extract label names from dataset schema."""
    label_categories = dataset.schema.attributes.get("labels")
    categories = label_categories.categories if label_categories else None
    return list(categories.labels) if categories and hasattr(categories, "labels") else []


def _make_yolo_bbox(img_size: tuple[int, int], bbox: list[float]) -> tuple[float, float, float, float]:
    """
    Convert absolute xywh bbox to normalized YOLO format.

    Args:
        img_size: (width, height) of the image
        bbox: [center_x, center_y, width, height] in absolute coordinates

    Returns:
        (center_x, center_y, width, height) normalized to [0, 1]
    """
    width, height = img_size
    if width == 0 or height == 0:
        return 0.0, 0.0, 0.0, 0.0

    cx = bbox[0] / width
    cy = bbox[1] / height
    w = bbox[2] / width
    h = bbox[3] / height
    return cx, cy, w, h


def _write_sample_annotation(
    anno_path: Path,
    sample: YoloSample,
) -> None:
    """Write annotation file for a single sample."""
    info = sample.image_info
    width = int(info.width) if info and info.width else 0
    height = int(info.height) if info and info.height else 0

    with open(anno_path, "w", encoding="utf-8") as f:
        if sample.bboxes is not None and sample.labels is not None and width > 0 and height > 0:
            for i in range(len(sample.labels)):
                if i < len(sample.bboxes):
                    bbox = sample.bboxes[i]
                    label = int(sample.labels[i])
                    cx, cy, w, h = _make_yolo_bbox((width, height), bbox.tolist())
                    f.write(f"{label} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")


def _save_sample_to_dir(
    sample: YoloSample,
    images_dir: Path,
    labels_dir: Path,
    save_images: bool,
    used_names: dict[str, str],
) -> None:
    """Save a single sample's image and annotation to directories (Ultralytics format)."""
    image_path = Path(sample.image) if sample.image else None
    if not image_path:
        return

    file_name = unique_destination_filename(image_path, used_names)
    dst_image_path = images_dir / file_name

    # Copy image if requested
    if save_images and image_path.exists() and not dst_image_path.exists():
        shutil.copy2(image_path, dst_image_path)

    # Write annotation file
    anno_path = labels_dir / f"{Path(file_name).stem}.txt"
    _write_sample_annotation(anno_path, sample)


def _save_traditional_sample(
    sample: YoloSample,
    subset_dir: Path,
    subset_dir_name: str,
    save_images: bool,
    used_names: dict[str, str],
) -> str | None:
    """Save a single sample in traditional YOLO format. Returns the image path string or None."""
    image_path = Path(sample.image) if sample.image else None
    if not image_path:
        return None

    file_name = unique_destination_filename(image_path, used_names)
    dst_image_path = subset_dir / file_name

    # Copy image if requested
    if save_images and image_path.exists() and not dst_image_path.exists():
        shutil.copy2(image_path, dst_image_path)

    # Write annotation file
    anno_path = subset_dir / f"{Path(file_name).stem}.txt"
    _write_sample_annotation(anno_path, sample)

    return f"data/{subset_dir_name}/{file_name}"


def _save_traditional_subset(
    samples: list[YoloSample],
    subset_dir: Path,
    subset_dir_name: str,
    save_images: bool,
) -> list[str]:
    """Save all samples for a subset. Returns list of image paths."""
    image_paths = []
    used_names: dict[str, str] = {}
    for sample in samples:
        try:
            img_path = _save_traditional_sample(sample, subset_dir, subset_dir_name, save_images, used_names)
            if img_path:
                image_paths.append(img_path)
        except Exception as e:
            logger.warning("[YOLO] Failed to save sample: %s", e)
    return image_paths


# =============================================================================
# File Writing Helpers (Traditional Format)
# =============================================================================


def _write_obj_names(names_path: Path, label_names: list[str]) -> None:
    """Write obj.names file."""
    with open(names_path, "w", encoding="utf-8") as f:
        for name in label_names:
            f.write(f"{name}\n")


def _write_obj_data(
    root_path: Path,
    label_names: list[str],
    subset_lists: dict[str, list[str]],
    written: dict[str, Path],
) -> Path:
    """Write obj.data file and subset list files. Returns path to obj.data."""
    data_path = root_path / "obj.data"
    with open(data_path, "w", encoding="utf-8") as f:
        f.write(f"classes = {len(label_names)}\n")
        for config_key, image_paths in subset_lists.items():
            list_file = f"{config_key}.txt"
            f.write(f"{config_key} = data/{list_file}\n")

            # Write subset list file
            list_path = root_path / list_file
            with open(list_path, "w", encoding="utf-8") as lf:
                for img_path in image_paths:
                    lf.write(f"{img_path}\n")
            written[list_file] = list_path

        f.write("names = data/obj.names\n")
        f.write("backup = backup/\n")
    return data_path


# =============================================================================
# Format-Specific Loaders
# =============================================================================


def _load_yolo_ultralytics(root_path: Path) -> Dataset:
    """Load a YOLO Ultralytics format dataset."""

    categories = _load_ultralytics_categories(root_path)
    dataset = Dataset(YoloSample, categories={"labels": categories})

    # Prefer the subset paths declared in data.yaml, and fall back to the on-disk layout.
    subsets = _resolve_ultralytics_subsets(root_path)
    if not subsets:
        raise FileNotFoundError(
            f"Could not locate any image directory under YOLO root: {root_path}. Expected either an "
            "'images' directory holding one folder per subset, a '<subset>/images' directory per "
            "subset, or a 'data.yaml' declaring the train/val/test image directories."
        )

    for subset_name, images_subset_dir, labels_subset_dir in subsets:
        subset_enum = DIR_NAME_TO_SUBSET.get(subset_name, Subset.UNASSIGNED)

        logger.info("[YOLO] Loading subset '%s' from '%s'", subset_name, images_subset_dir)

        image_files = _find_image_files(images_subset_dir)
        samples = []
        for image_path in image_files:
            try:
                sample = _create_sample_from_image(image_path, labels_subset_dir, subset_enum)
                if sample:
                    samples.append(sample)
            except Exception as e:
                logger.warning("[YOLO] Failed to load image %s: %s", image_path, e)

        if samples:
            dataset.append_batch(samples)

        logger.info("[YOLO] Loaded %d samples from subset '%s'", len(samples), subset_name)

    logger.info("[YOLO] Finished loading dataset with %d samples", len(dataset))
    return dataset


def _load_yolo_traditional(root_path: Path) -> Dataset:
    """Load a traditional YOLO format dataset."""
    # Load categories
    names_path = root_path / "obj.names"
    if names_path.exists():
        categories = _load_categories_from_names(names_path)
    else:
        categories = LabelCategories(labels=())
        logger.warning("[YOLO] No obj.names file found, using empty categories")

    dataset = Dataset(YoloSample, categories={"labels": categories})

    for dir_name, subset_enum in TRADITIONAL_DIR_NAME_TO_SUBSET.items():
        subset_dir = root_path / dir_name
        if not subset_dir.exists() or not subset_dir.is_dir():
            continue

        logger.info("[YOLO] Loading subset from '%s'", subset_dir)

        image_files = _find_image_files(subset_dir)
        samples = []
        for image_path in image_files:
            try:
                sample = _create_sample_from_traditional_image(image_path, subset_enum)
                if sample:
                    samples.append(sample)
            except Exception as e:
                logger.warning("[YOLO] Failed to load image %s: %s", image_path, e)

        # Use batch append for efficiency
        if samples:
            dataset.append_batch(samples)

        logger.info("[YOLO] Loaded %d samples from '%s'", len(samples), dir_name)

    logger.info("[YOLO] Finished loading dataset with %d samples", len(dataset))
    return dataset


# =============================================================================
# Format-Specific Savers
# =============================================================================


def _save_yolo_ultralytics(
    dataset: Dataset[YoloSample],
    root_path: Path,
    save_images: bool,
) -> dict[str, Path]:
    """Save dataset in YOLO Ultralytics format."""

    images_dir = root_path / "images"
    labels_dir = root_path / "labels"

    subset_to_samples = _group_samples_by_subset(dataset)
    label_names = _get_label_names_from_dataset(dataset)
    written: dict[str, Path] = {}

    for subset, samples in subset_to_samples.items():
        if not samples:
            continue

        subset_name = SUBSET_TO_DIR_NAME.get(subset, "unassigned")
        images_subset_dir = images_dir / subset_name
        labels_subset_dir = labels_dir / subset_name
        images_subset_dir.mkdir(parents=True, exist_ok=True)
        labels_subset_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[YOLO] Saving subset '%s' with %d samples", subset_name, len(samples))

        used_names: dict[str, str] = {}
        for sample in samples:
            try:
                _save_sample_to_dir(sample, images_subset_dir, labels_subset_dir, save_images, used_names)
            except Exception as e:
                logger.warning("[YOLO] Failed to save sample: %s", e)

        written[f"images_{subset_name}"] = images_subset_dir
        written[f"labels_{subset_name}"] = labels_subset_dir

    # Write data.yaml
    yaml_path = root_path / "data.yaml"
    yaml_data: dict[str, Any] = {
        "names": dict(enumerate(label_names)),
    }

    # Add subset paths
    for subset in subset_to_samples:
        subset_name = SUBSET_TO_DIR_NAME.get(subset, "unassigned")
        yaml_data[subset_name] = f"images/{subset_name}"

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(yaml_data, f, sort_keys=False, allow_unicode=True)

    written["data.yaml"] = yaml_path

    logger.info("[YOLO] Finished saving dataset to '%s'", root_path)
    return written


def _save_yolo_traditional(
    dataset: Dataset[YoloSample],
    root_path: Path,
    save_images: bool,
) -> dict[str, Path]:
    """Save dataset in traditional YOLO format."""
    subset_to_samples = _group_samples_by_subset(dataset)
    label_names = _get_label_names_from_dataset(dataset)

    written: dict[str, Path] = {}
    subset_lists: dict[str, list[str]] = {}

    for subset, samples in subset_to_samples.items():
        if not samples:
            continue

        subset_dir_name = TRADITIONAL_SUBSET_DIR_NAMES.get(subset, "obj_data")
        subset_dir = root_path / subset_dir_name
        subset_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[YOLO] Saving subset '%s' with %d samples", subset_dir_name, len(samples))

        image_paths = _save_traditional_subset(samples, subset_dir, subset_dir_name, save_images)

        config_key = TRADITIONAL_SUBSET_CONFIG_KEYS.get(subset, "data")
        subset_lists[config_key] = image_paths
        written[subset_dir_name] = subset_dir

    # Write obj.names
    names_path = root_path / "obj.names"
    _write_obj_names(names_path, label_names)
    written["obj.names"] = names_path

    # Write obj.data and subset list files
    data_path = _write_obj_data(root_path, label_names, subset_lists, written)
    written["obj.data"] = data_path

    logger.info("[YOLO] Finished saving dataset to '%s'", root_path)
    return written
