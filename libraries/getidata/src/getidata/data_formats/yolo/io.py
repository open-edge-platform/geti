# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
YOLO dataset I/O support for Ultralytics and traditional formats.
"""

import logging
from pathlib import Path

from getidata import Dataset
from getidata.data_formats.base import DataFormat
from getidata.data_formats.yolo.helpers import (
    _detect_yolo_format,
    _has_segmentation_rows,
    _is_yolo_cls_layout,
    _load_yolo_cls,
    _load_yolo_seg,
    _load_yolo_traditional,
    _load_yolo_ultralytics,
    _save_yolo_cls,
    _save_yolo_seg,
    _save_yolo_traditional,
    _save_yolo_ultralytics,
)
from getidata.data_formats.yolo.sample import YoloClsSample, YoloSample, YoloSegSample

logger = logging.getLogger(__name__)


def is_yolo_format(input_dir: Path) -> bool:
    """
    Detect if a directory contains a YOLO-format dataset.

    YOLO format is identified by:
    - data.yaml file (Ultralytics format)
    - OR obj.names/obj.data files (traditional format)
    - OR images/ and labels/ directories (Ultralytics structure)

    Args:
        input_dir: Path to the directory to check

    Returns:
        True if the directory contains a YOLO-format dataset
    """
    if (input_dir / "data.yaml").exists():
        return True

    if (input_dir / "obj.names").exists() or (input_dir / "obj.data").exists():
        return True

    return (input_dir / "images").is_dir() and (input_dir / "labels").is_dir()


def is_yolo_cls_format(input_dir: Path) -> bool:
    """
    Detect if a directory contains an Ultralytics YOLO classification dataset.

    The classification layout is identified by subset directories (train/val/test and common
    spelling variants) holding one image directory per class::

        train/
            <class_a>/
                img1.jpg
            <class_b>/
                img2.jpg
        val/
            ...

    Args:
        input_dir: Path to the directory to check

    Returns:
        True if the directory contains a YOLO classification-format dataset
    """
    return _is_yolo_cls_layout(input_dir)


def import_yolo_cls_dataset(input_dir: Path) -> Dataset:
    """
    Import an Ultralytics YOLO classification dataset from a directory.

    Args:
        input_dir: Path to the YOLO classification dataset directory

    Returns:
        Dataset containing YoloClsSample instances
    """
    return load_yolo_cls_dataset(root_dir=str(input_dir))


def load_yolo_cls_dataset(root_dir: str) -> Dataset:
    """
    Load an Ultralytics YOLO classification dataset from its top-level directory.

    Ultralytics classification format (ImageNet-style layout)::

        train/
            <class_a>/
            <class_b>/
        val/
            <class_a>/
            <class_b>/
        test/  (optional)

    There are no annotation files: each image is labeled by the class directory that
    contains it, so every image carries exactly one label. Images inside the reserved
    ``unannotated`` directory of a subset carry no label.

    Args:
        root_dir: Path to the top-level YOLO classification dataset directory.

    Returns:
        Dataset containing YoloClsSample instances.
    """
    root_path = Path(root_dir)
    if not root_path.exists():
        raise FileNotFoundError(f"YOLO classification root directory does not exist: {root_dir}")

    logger.info("[YOLO-CLS] Loading classification dataset from '%s'", root_dir)
    return _load_yolo_cls(root_path)


def save_yolo_cls_dataset(
    dataset: Dataset[YoloClsSample],
    root_dir: str,
    save_images: bool = True,
) -> dict[str, Path]:
    """
    Save a Dataset of YoloClsSample to disk in Ultralytics YOLO classification format.

    Creates the ImageNet-style layout with one directory per subset, each holding one
    subdirectory per class with the images copied into it. Samples without a label are
    written into the reserved ``unannotated`` directory of their subset, where the loader
    picks them up again as samples without a label.

    Args:
        dataset: Dataset containing YoloClsSample samples.
        root_dir: Path to the output directory.
        save_images: Whether to copy images to the output directory.

    Returns:
        Mapping from subset names to written subset directories.
    """
    root_path = Path(root_dir)
    root_path.mkdir(parents=True, exist_ok=True)

    logger.info("[YOLO-CLS] Saving classification dataset to '%s'", root_dir)
    return _save_yolo_cls(dataset, root_path, save_images)


def is_yolo_seg_format(input_dir: Path) -> bool:
    """
    Detect if a directory contains an Ultralytics YOLO instance segmentation dataset.

    The segmentation layout is identical to the Ultralytics detection layout (images/
    and labels/ directories per split, data.yaml with class names), so the two are
    distinguished by the content of the label files: a label file holds segmentation
    data when any of its rows consists of a class index followed by at least three
    normalized (x, y) coordinate pairs, i.e. seven or more fields with an odd count.
    Detection rows always have exactly five fields.

    Args:
        input_dir: Path to the directory to check

    Returns:
        True if the directory contains a YOLO segmentation-format dataset
    """
    if (input_dir / "obj.names").exists() or (input_dir / "obj.data").exists():
        # The traditional YOLO layout never carries polygon rows
        return False

    if not is_yolo_format(input_dir):
        return False

    return _has_segmentation_rows(input_dir)


def import_yolo_seg_dataset(input_dir: Path) -> Dataset:
    """
    Import an Ultralytics YOLO instance segmentation dataset from a directory.

    Args:
        input_dir: Path to the YOLO segmentation dataset directory

    Returns:
        Dataset containing YoloSegSample instances
    """
    return load_yolo_seg_dataset(root_dir=str(input_dir))


def load_yolo_seg_dataset(root_dir: str) -> Dataset:
    """
    Load an Ultralytics YOLO instance segmentation dataset from its top-level directory.

    The layout matches the Ultralytics detection format (images/ and labels/
    directories per split, data.yaml with class names); the label files hold one
    polygon per row as ``<class-index> <x1> <y1> <x2> <y2> ... <xn> <yn>`` with
    normalized coordinates. Rows with fewer than seven fields -- including
    detection-format rows -- are skipped with a warning.

    Args:
        root_dir: Path to the top-level YOLO segmentation dataset directory.

    Returns:
        Dataset containing YoloSegSample instances.
    """
    root_path = Path(root_dir)
    if not root_path.exists():
        raise FileNotFoundError(f"YOLO segmentation root directory does not exist: {root_dir}")

    logger.info("[YOLO-SEG] Loading segmentation dataset from '%s'", root_dir)
    return _load_yolo_seg(root_path)


def save_yolo_seg_dataset(
    dataset: Dataset[YoloSegSample],
    root_dir: str,
    save_images: bool = True,
) -> dict[str, Path]:
    """
    Save a Dataset of YoloSegSample to disk in Ultralytics YOLO segmentation format.

    Creates the same images/ + labels/ layout as the Ultralytics detection format,
    with one label file per image holding a normalized polygon row per instance.
    Polygons with fewer than three points cannot be represented and are skipped;
    samples without polygons get an empty label file.

    Args:
        dataset: Dataset containing YoloSegSample samples.
        root_dir: Path to the output directory.
        save_images: Whether to copy images to the output directory.

    Returns:
        Mapping from logical names to written paths.
    """
    root_path = Path(root_dir)
    root_path.mkdir(parents=True, exist_ok=True)

    logger.info("[YOLO-SEG] Saving segmentation dataset to '%s'", root_dir)
    return _save_yolo_seg(dataset, root_path, save_images)


def import_yolo_dataset(input_dir: Path) -> Dataset:
    """
    Import a YOLO-format dataset from a directory.

    Supports both Ultralytics and traditional YOLO formats.

    Args:
        input_dir: Path to the YOLO dataset directory

    Returns:
        Dataset containing YoloSample instances
    """
    return load_yolo_dataset(root_dir=str(input_dir))


def load_yolo_dataset(root_dir: str, format: str = "auto") -> Dataset:
    """
    Load a YOLO dataset from its top-level directory.

    Supports both Ultralytics format and traditional YOLO format:

    Ultralytics format::

        data.yaml
        images/
            train/
            val/
            test/  (optional)
        labels/
            train/
            val/
            test/  (optional)

    Ultralytics format, split-first layout (as exported by Roboflow)::

        data.yaml    (declares e.g. "train: ../train/images")
        train/
            images/
            labels/
        valid/
            images/
            labels/
        test/  (optional)

    Traditional YOLO format::

        obj.names
        obj.data  (optional)
        obj_train_data/
        obj_valid_data/  (optional)

    Args:
        root_dir: Path to the top-level YOLO dataset directory.
        format: Format to use - "auto", "ultralytics", or "traditional".

    Returns:
        Dataset containing YoloSample instances.
    """
    root_path = Path(root_dir)
    if not root_path.exists():
        raise FileNotFoundError(f"YOLO root directory does not exist: {root_dir}")

    # Detect format if auto
    segmentation_error = (
        f"The YOLO dataset in {root_dir} contains segmentation labels. "
        "Use load_yolo_seg_dataset to load instance segmentation datasets."
    )
    if format == "auto":
        format = _detect_yolo_format(root_path)
        if format == "segmentation":
            raise ValueError(segmentation_error)
        if format == "unknown":
            raise ValueError(
                f"Could not detect YOLO format in {root_dir}. "
                "Expected data.yaml (Ultralytics) or obj.names (traditional YOLO)."
            )
    elif format == "ultralytics":
        # The explicit format bypasses detection, so the segmentation check has to run here as
        # well: the detection loader would otherwise misparse polygon rows as cxcywh boxes.
        if _has_segmentation_rows(root_path):
            raise ValueError(segmentation_error)

    logger.info("[YOLO] Loading %s format dataset from '%s'", format, root_dir)

    if format == "ultralytics":
        return _load_yolo_ultralytics(root_path)
    return _load_yolo_traditional(root_path)


def save_yolo_dataset(
    dataset: Dataset[YoloSample],
    root_dir: str,
    format: DataFormat = DataFormat.YOLO_ULTRALYTICS,
    save_images: bool = True,
) -> dict[str, Path]:
    """
    Save a Dataset of YoloSample to disk in YOLO format.

    Args:
        dataset: Dataset containing YoloSample samples.
        root_dir: Path to the output directory.
        format: Output format (YOLO_ULTRALYTICS or YOLO).
        save_images: Whether to copy images to the output directory.

    Returns:
        Mapping from logical names to written paths.
    """
    root_path = Path(root_dir)
    root_path.mkdir(parents=True, exist_ok=True)

    logger.info("[YOLO] Saving dataset to '%s' in %s format", root_dir, format)

    if format == DataFormat.YOLO_ULTRALYTICS:
        return _save_yolo_ultralytics(dataset, root_path, save_images)
    if format == DataFormat.YOLO:
        return _save_yolo_traditional(dataset, root_path, save_images)
    raise ValueError(f"Unsupported YOLO format: {format}")
