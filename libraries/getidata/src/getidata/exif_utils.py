# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Shared EXIF orientation helpers.

Centralizes handling of the EXIF ``Orientation`` tag so that dimension/shape
logic behaves identically across loaders (``LazyImage``, YOLO/VOC helpers,
and media/image converters).
"""

from __future__ import annotations

import os
from functools import lru_cache
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

    Returns False if the file can't be opened or has no EXIF data. The result is cached per file version, because
    for PNG ``getexif`` decodes the whole image and tiled datasets ask once per tile.
    """
    try:
        stat = os.stat(path)
    except OSError:
        return False
    return _has_nontrivial_exif_orientation(path, stat.st_mtime_ns, stat.st_size)


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_TEXT_CHUNKS = (b"tEXt", b"zTXt", b"iTXt")


def _png_has_no_exif(path: str) -> bool:  # noqa: PLR0911
    """True when a PNG provably carries no EXIF, found by walking its chunk headers (no pixel decoding).

    PIL's ``getexif`` decodes the whole image for PNG, which costs as much as the real decode on large images.
    Any ``eXIf`` chunk or ``Raw profile type ...`` text chunk (legacy EXIF) returns False, and so does any
    parse problem, so the caller falls back to PIL.
    """
    try:
        with open(path, "rb") as f:
            if f.read(8) != _PNG_SIGNATURE:
                return False
            while header := f.read(8):
                if len(header) < 8:
                    return False
                length, kind = int.from_bytes(header[:4], "big"), header[4:]
                if kind == b"IEND":
                    return True
                if kind == b"eXIf":
                    return False
                if kind in _PNG_TEXT_CHUNKS:
                    if f.read(min(length, 32)).lower().startswith(b"raw profile type"):
                        return False
                    f.seek(length - min(length, 32) + 4, os.SEEK_CUR)
                else:
                    f.seek(length + 4, os.SEEK_CUR)  # data + CRC
    except OSError:
        return False
    return False


@lru_cache(maxsize=4096)
def _has_nontrivial_exif_orientation(path: str, mtime_ns: int, size: int) -> bool:  # noqa: ARG001
    if _png_has_no_exif(path):
        return False
    try:
        from PIL import Image

        with Image.open(path) as img:
            return get_exif_orientation(img) != 1
    except Exception:
        return False
