# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Bounding-box coordinate conversions.

Formats:

- ``xyxy``: corners ``(x1, y1, x2, y2)``.
- ``xyah``: center, aspect, height (used by the Kalman filter).
- ``cxcywh``: center, width, height.

All operate on ``(N, 4)`` arrays and round-trip losslessly.
"""

from __future__ import annotations

import numpy as np


def xyxy_to_xyah(boxes: np.ndarray) -> np.ndarray:
    """Convert ``xyxy`` boxes to ``xyah`` form.

    Args:
        boxes: ``(N, 4)`` array in ``[x1, y1, x2, y2]``. Must satisfy
            ``x2 > x1`` and ``y2 > y1`` for every row.

    Returns:
        ``(N, 4)`` array in ``[cx, cy, aspect, height]``.

    Raises:
        ValueError: If any box has zero or negative width or height.
    """
    boxes = np.atleast_2d(np.asarray(boxes, dtype=np.float64))
    width = boxes[:, 2] - boxes[:, 0]
    height = boxes[:, 3] - boxes[:, 1]
    if np.any(width <= 0) or np.any(height <= 0):
        msg = "xyxy_to_xyah requires positive width and height (x2 > x1, y2 > y1)"
        raise ValueError(msg)
    cx = boxes[:, 0] + width / 2.0
    cy = boxes[:, 1] + height / 2.0
    aspect = width / height
    return np.stack([cx, cy, aspect, height], axis=1)


def xyah_to_xyxy(boxes: np.ndarray) -> np.ndarray:
    """Convert ``xyah`` boxes to ``xyxy`` form.

    Args:
        boxes: ``(N, 4)`` array in ``[cx, cy, aspect, height]``.

    Returns:
        ``(N, 4)`` array in ``[x1, y1, x2, y2]``.
    """
    boxes = np.atleast_2d(np.asarray(boxes, dtype=np.float64))
    cx, cy, aspect, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    w = aspect * h
    x1 = cx - w / 2.0
    y1 = cy - h / 2.0
    x2 = cx + w / 2.0
    y2 = cy + h / 2.0
    return np.stack([x1, y1, x2, y2], axis=1)


def xyxy_to_cxcywh(boxes: np.ndarray) -> np.ndarray:
    """Convert ``xyxy`` boxes to ``cxcywh`` form.

    Args:
        boxes: ``(N, 4)`` array in ``[x1, y1, x2, y2]``.

    Returns:
        ``(N, 4)`` array in ``[cx, cy, width, height]``.
    """
    boxes = np.atleast_2d(np.asarray(boxes, dtype=np.float64))
    cx = (boxes[:, 0] + boxes[:, 2]) / 2.0
    cy = (boxes[:, 1] + boxes[:, 3]) / 2.0
    width = boxes[:, 2] - boxes[:, 0]
    height = boxes[:, 3] - boxes[:, 1]
    return np.stack([cx, cy, width, height], axis=1)


def cxcywh_to_xyxy(boxes: np.ndarray) -> np.ndarray:
    """Convert ``cxcywh`` boxes to ``xyxy`` form.

    Args:
        boxes: ``(N, 4)`` array in ``[cx, cy, width, height]``.

    Returns:
        ``(N, 4)`` array in ``[x1, y1, x2, y2]``.
    """
    boxes = np.atleast_2d(np.asarray(boxes, dtype=np.float64))
    cx, cy, w, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    x1 = cx - w / 2.0
    y1 = cy - h / 2.0
    x2 = cx + w / 2.0
    y2 = cy + h / 2.0
    return np.stack([x1, y1, x2, y2], axis=1)
