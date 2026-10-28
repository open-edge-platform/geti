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
    _load_yolo_traditional,
    _load_yolo_ultralytics,
    _save_yolo_traditional,
    _save_yolo_ultralytics,
)
from getidata.data_formats.yolo.sample import YoloSample

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
    if format == "auto":
        format = _detect_yolo_format(root_path)
        if format == "unknown":
            raise ValueError(
                f"Could not detect YOLO format in {root_dir}. "
                "Expected data.yaml (Ultralytics) or obj.names (traditional YOLO)."
            )

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
