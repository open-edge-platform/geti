# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Abstract ReID feature-provider interface.

A `ReIDProvider` turns image crops (one per bounding box) into fixed-length
appearance descriptors. Concrete providers wrap a specific inference backend
(e.g. OpenVINO IR) and share the contract defined here.

The provider is stateless with respect to tracks; it only embeds boxes.
Per-track appearance memory lives in
`getitrack.reid.gallery.AppearanceGallery`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


class ReIDProvider(ABC):
    """Abstract appearance-feature extractor.

    Implementations embed the image region under each bounding box into a
    descriptor vector. Extraction is lazy: only the boxes handed to `extract`
    are cropped and inferred, never the whole frame.
    """

    @abstractmethod
    def extract(self, frame_bgr: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        """Embed each box's image region into an appearance descriptor.

        Args:
            frame_bgr: ``(H, W, 3)`` uint8 image in BGR channel order (the
                OpenCV convention), the frame the boxes were detected in.
            boxes: ``(N, 4)`` float array of ``xyxy`` boxes in absolute pixel
                coordinates of ``frame_bgr``.

        Returns:
            ``(N, D)`` float32 array of L2-normalised descriptors, row-aligned
            with ``boxes``. For an empty ``boxes`` input the result is
            ``(0, D)`` (``D`` may be ``0`` before the feature size is known).
        """
