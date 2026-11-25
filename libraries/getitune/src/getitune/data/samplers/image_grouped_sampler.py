# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Sampler that keeps the tiles of one source image together."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import torch
from torch.utils.data import Sampler

if TYPE_CHECKING:
    from collections.abc import Iterator

    from getitune.data.dataset.base import VisionDataset


def tile_source_indices(dataset: VisionDataset) -> np.ndarray | None:
    """Return the source image index of every tile of a tiled training dataset, or None if it has no tile column."""
    transforms = getattr(getattr(dataset, "dm_subset", None), "_transforms", None)
    if transforms is None or "tile" not in transforms.schema.attributes:
        return None
    return transforms.apply(["tile"])["tile"].struct.field("source_sample_idx").to_numpy()


class ImageGroupedSampler(Sampler[int]):
    """Yield every tile of one image before moving to the next, in random image and tile order.

    Each tile of a large image is read by cropping the same decoded source. Visiting one image's tiles
    together lets the loader decode it once per worker instead of once per tile; a plain shuffle would
    decode a 20 MP image for every single tile.

    Args:
        source_idx: Source image index of every tile.
        ratio: Fraction of each image's tiles drawn per epoch (``TileConfig.sampling_ratio``).
        inner: A sampler to keep the sampling distribution of (for example class balancing). Its draws are only
            regrouped by image, so every drawn tile is still drawn as often as before.
    """

    def __init__(self, source_idx: np.ndarray, ratio: float = 1.0, inner: Sampler[int] | None = None) -> None:
        self._source_idx = source_idx
        self._inner = inner
        self._ratio = ratio
        order = np.argsort(source_idx, kind="stable")
        _, starts = np.unique(source_idx[order], return_index=True)
        self._groups = [torch.from_numpy(g) for g in np.split(order, starts[1:])]

    def _take(self, size: int) -> int:
        return max(1, math.ceil(size * self._ratio))

    def __len__(self) -> int:
        if self._inner is not None:
            return len(self._inner)
        return sum(self._take(len(g)) for g in self._groups)

    def __iter__(self) -> Iterator[int]:
        if self._inner is not None:
            yield from self._regroup(torch.as_tensor(list(self._inner), dtype=torch.long))
            return
        for i in torch.randperm(len(self._groups)).tolist():
            group = self._groups[i]
            yield from group[torch.randperm(len(group))[: self._take(len(group))]].tolist()

    def _regroup(self, draws: torch.Tensor) -> Iterator[int]:
        """Reorder ``draws`` so the draws of one image are adjacent, with the images in random order."""
        _, image = np.unique(self._source_idx[draws.numpy()], return_inverse=True)
        rank = torch.randperm(int(image.max()) + 1 if len(image) else 0)[torch.from_numpy(image.reshape(-1))]
        yield from draws[torch.argsort(rank, stable=True)].tolist()
