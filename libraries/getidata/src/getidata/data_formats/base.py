# Copyright (C) 2022-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

IMAGE_EXTENSIONS = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".jpe",
        ".jp2",
        ".png",
        ".bmp",
        ".dib",
        ".tif",
        ".tiff",
        ".tga",
        ".webp",
        ".pfm",
        ".sr",
        ".ras",
        ".exr",
        ".hdr",
        ".pic",
        ".pbm",
        ".pgm",
        ".ppm",
        ".pxm",
        ".pnm",
    }
)


def find_images(dirpath: str | Path) -> Iterator[str]:
    """Yield the paths of the image files located directly in ``dirpath`` (non-recursive)."""
    for path in Path(dirpath).iterdir():
        if path.suffix.lower() in IMAGE_EXTENSIONS and path.is_file():
            yield str(path)


class DataFormat(Enum):
    """Supported data formats for load/save."""

    GETIDATA = "GETIDATA"
    COCO = "COCO"
    VOC = "VOC"
    YOLO = "YOLO"
    YOLO_ULTRALYTICS = "YOLO_ULTRALYTICS"
    UNKNOWN = "UNKNOWN"


def unique_destination_filename(source_path: Path, used_names: dict[str, str]) -> str:
    """
    Pick a destination filename for ``source_path`` that cannot collide with another source file.

    Exporters that flatten samples into a single output directory (COCO, YOLO, ...) traditionally
    used the bare basename of the source path as the destination filename. When two source files
    from different directories share the same basename -- e.g. video frames extracted from
    different videos, both named ``frame000066.png`` -- this silently drops all but the first one.

    This helper keeps a registry (``used_names``) of destination names already claimed during the
    current export, mapping each name to the resolved source path that claimed it. If the requested
    name is free, or already claimed by this same source path, it is returned as-is. Otherwise a
    numeric suffix is appended (``name_1.ext``, ``name_2.ext``, ...) until a free name is found.

    Args:
        source_path: Path of the file being exported.
        used_names: Registry of destination names already claimed in this export, mapping name ->
            resolved source path. Mutated in place with the returned name.

    Returns:
        A destination filename, unique with respect to every other source path seen so far.
    """
    base_name = source_path.name
    if not base_name:
        return base_name

    resolved_source = str(source_path.resolve())
    stem, suffix = source_path.stem, source_path.suffix

    candidate = base_name
    counter = 1
    while used_names.get(candidate, resolved_source) != resolved_source:
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1

    used_names[candidate] = resolved_source
    return candidate
