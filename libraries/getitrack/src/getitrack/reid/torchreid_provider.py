# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""torchreid appearance-feature provider (native PyTorch backend).

`TorchReIDProvider` wraps torchreid's ``FeatureExtractor`` to embed box crops
with any torchreid model-zoo architecture (e.g. OSNet). torchreid handles the
resize and ImageNet normalisation internally; the provider crops the boxes,
converts BGR to RGB, and L2-normalises the returned descriptors.

No weights are bundled: torchreid downloads ImageNet-pretrained weights for the
chosen ``model_name`` on first use, or loads a ``.pth.tar`` checkpoint when one
is supplied.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import numpy as np

from getitrack.matching.appearance import l2_normalize
from getitrack.reid.base import ReIDProvider
from getitrack.reid.crops import crop_boxes

if TYPE_CHECKING:
    from pathlib import Path


@runtime_checkable
class Descriptors(Protocol):
    """Minimal view of a torch tensor: detachable and convertible to numpy."""

    def detach(self) -> Descriptors:
        """Return a version detached from the autograd graph."""

    def cpu(self) -> Descriptors:
        """Return a version resident on host memory."""

    def numpy(self) -> np.ndarray:
        """Return the underlying array."""


class FeatureExtractorLike(Protocol):
    """Minimal view of torchreid's ``FeatureExtractor``: callable on a crop list."""

    def __call__(self, images: list[np.ndarray]) -> Descriptors:
        """Embed each ``(H, W, 3)`` RGB crop into a ``(N, D)`` descriptor batch."""


class TorchReIDProvider(ReIDProvider):
    """ReID feature provider backed by a native torchreid model.

    torchreid is imported lazily in the constructor.
    """

    def __init__(
        self,
        model_name: str,
        *,
        weights_path: str | Path | None = None,
        device: str = "cpu",
        input_size: tuple[int, int] = (256, 128),
        extractor: FeatureExtractorLike | None = None,
    ) -> None:
        """Initialise the provider.

        Args:
            model_name: torchreid architecture name (e.g. ``osnet_x1_0``).
            weights_path: Optional ``.pth.tar`` checkpoint; torchreid downloads
                ImageNet-pretrained weights when omitted.
            device: torch device to run on (``cpu`` or ``cuda``).
            input_size: Model input ``(height, width)`` in pixels.
            extractor: Pre-built feature extractor to use directly, bypassing the
                torchreid load. Primarily an injection point for testing.
        """
        self._output_dim: int | None = None
        if extractor is not None:
            self._extractor: FeatureExtractorLike = extractor
            return
        # Import torchreid lazily.
        from torchreid.reid.utils import FeatureExtractor

        self._extractor = FeatureExtractor(
            model_name=model_name,
            model_path=str(weights_path) if weights_path is not None else "",
            image_size=input_size,
            device=device,
            verbose=False,
        )

    def extract(self, frame_bgr: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        """Embed each box crop into an L2-normalised descriptor (see `ReIDProvider.extract`)."""
        box_array = np.asarray(boxes, dtype=np.float32).reshape(-1, 4)
        if box_array.shape[0] == 0:
            return np.empty((0, self._output_dim or 0), dtype=np.float32)
        # torchreid's numpy path builds a PIL image per crop and assumes RGB, so
        # flip BGR and make contiguous (PIL rejects the negative-stride view).
        crops_rgb = [np.ascontiguousarray(crop[:, :, ::-1]) for crop in crop_boxes(frame_bgr, box_array)]
        features = np.asarray(self._extractor(crops_rgb).detach().cpu().numpy(), dtype=np.float32)
        self._output_dim = int(features.shape[1])
        return l2_normalize(features)
