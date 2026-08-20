# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Bounding-box crop extraction shared by ReID providers.

Both the OpenVINO and torch providers embed the image region under each box, so
the clamping rule (keep every crop inside the frame and at least one pixel wide)
lives here once rather than in each provider.
"""

from __future__ import annotations

import numpy as np


def crop_boxes(frame_bgr: np.ndarray, boxes: np.ndarray) -> list[np.ndarray]:
    """Extract the clamped image crop under each ``xyxy`` box.

    Coordinates are floored/ceiled to integer pixels and clamped so the crop
    stays within the frame and is never empty (a degenerate or out-of-bounds box
    yields a 1-pixel crop rather than an error).

    Args:
        frame_bgr: ``(H, W, 3)`` image the boxes were detected in.
        boxes: ``(N, 4)`` ``xyxy`` boxes in absolute pixel coordinates.

    Returns:
        A list of ``N`` crops (views into ``frame_bgr``), one per box, in the
        same channel order as ``frame_bgr`` and of varying size.
    """
    frame_h, frame_w = frame_bgr.shape[:2]
    crops: list[np.ndarray] = []
    for x1, y1, x2, y2 in boxes:
        xi1 = int(np.clip(np.floor(x1), 0, frame_w - 1))
        yi1 = int(np.clip(np.floor(y1), 0, frame_h - 1))
        xi2 = int(np.clip(np.ceil(x2), xi1 + 1, frame_w))
        yi2 = int(np.clip(np.ceil(y2), yi1 + 1, frame_h))
        crops.append(frame_bgr[yi1:yi2, xi1:xi2])
    return crops
