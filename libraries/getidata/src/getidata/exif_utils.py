# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Shared EXIF orientation helpers.

Centralizes handling of the EXIF ``Orientation`` tag so that dimension/shape
logic behaves identically across loaders (``LazyImage``, YOLO/VOC helpers,
and media/image converters).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image as PILImageType

# EXIF Orientation tag id.
EXIF_ORIENTATION_TAG = 0x0112

# Orientations that imply a 90°/270° rotation and therefore swap width/height.
_DIMENSION_SWAPPING_ORIENTATIONS = frozenset({5, 6, 7, 8})


def get_exif_orientation(img: PILImageType) -> int:
    """Return the EXIF Orientation value for a PIL image, defaulting to 1.

    Safely handles missing/None EXIF tags.
    """
    try:
        value = img.getexif().get(EXIF_ORIENTATION_TAG, 1)
    except Exception:
        return 1
    try:
        return int(value) if value else 1
    except (TypeError, ValueError):
        return 1


def needs_dimension_swap(orientation: int) -> bool:
    """Whether the given EXIF orientation swaps width and height."""
    return orientation in _DIMENSION_SWAPPING_ORIENTATIONS


def get_oriented_size(width: int, height: int, orientation: int) -> tuple[int, int]:
    """Return ``(width, height)`` after applying EXIF orientation.

    For rotating orientations (5-8), width and height are swapped.
    """
    if needs_dimension_swap(orientation):
        return height, width
    return width, height


def has_nontrivial_exif_orientation(path: str) -> bool:
    """Return True if the image at ``path`` has a non-identity EXIF orientation.

    Uses a lightweight PIL header read (does not decode pixel data). Returns
    False if the file can't be opened or has no EXIF data.
    """
    try:
        from PIL import Image

        with Image.open(path) as img:
            return get_exif_orientation(img) != 1
    except Exception:
        return False
