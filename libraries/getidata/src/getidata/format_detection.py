# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Dataset format detection and auto-import functionality.

This module detects dataset formats and dispatches to the appropriate loader.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from getidata.data_formats.base import DataFormat

# File names for native getidata format
METADATA_FILE = "metadata.json"
DATAFRAME_FILE = "data.parquet"


def is_getidata_format(input_dir: Path) -> bool:
    """
    Detect if a directory contains a getidata-exported dataset.

    getidata format is identified by:
    - metadata.json file
    - data.parquet file

    Args:
        input_dir: Path to the directory to check

    Returns:
        True if the directory contains a getidata-format dataset
    """
    return (input_dir / METADATA_FILE).exists() and (input_dir / DATAFRAME_FILE).exists()


def detect_dataset_format(input_dir: Path) -> DataFormat:
    """
    Detect the format of a dataset directory.

    Checks formats in order of specificity:
    1. getidata (most specific - requires both metadata.json and data.parquet)
    2. COCO (JSON files with images/annotations structure)
    3. YOLO (data.yaml, obj.names, or directory structure)
    4. VOC (JPEGImages/, Annotations/, ImageSets/ directories)

    Args:
        input_dir: Path to the directory to check

    Returns:
        DataFormat enum value: GETIDATA, COCO, YOLO, VOC, or UNKNOWN
    """
    if is_getidata_format(input_dir):
        return DataFormat.GETIDATA

    # Inline imports to avoid circular dependency:
    from getidata.data_formats.coco.io import is_coco_format
    from getidata.data_formats.voc.io import is_voc_format
    from getidata.data_formats.yolo.io import is_yolo_format

    if is_coco_format(input_dir):
        return DataFormat.COCO
    if is_yolo_format(input_dir):
        return DataFormat.YOLO
    if is_voc_format(input_dir):
        return DataFormat.VOC
    return DataFormat.UNKNOWN


def find_dataset_root(input_dir: Path) -> Path:
    """
    Find the actual dataset root, descending at most one level into a single child directory.

    Many third-party dataset zips extract with a single top-level folder
    (e.g., dataset.zip -> dataset/annotations/...). This function checks if
    the format is detectable at the input level, and if not, descends into
    a single child directory (if one exists) to check there.

    Args:
        input_dir: The directory to start searching from

    Returns:
        The detected dataset root directory (may be the input directory itself
        if format is detectable there, or a single nested child directory)
    """
    if detect_dataset_format(input_dir) != DataFormat.UNKNOWN:
        return input_dir

    children = list(input_dir.iterdir())
    child_dirs = [c for c in children if c.is_dir()]
    child_files = [c for c in children if c.is_file()]

    if len(child_dirs) == 1 and not child_files:
        return child_dirs[0]

    return input_dir
