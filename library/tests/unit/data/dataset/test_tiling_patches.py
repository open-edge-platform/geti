# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Regression tests for the instance-mask tiling patch.

Datumaro's upstream ``InstanceMaskTiler`` does not implement ``is_filterable``,
so instance masks are never pruned during tiling while bounding boxes and labels
*are*. That leaves an instance-segmentation tile with ``len(masks) != len(bboxes)
== len(labels)``, which crashes Mask R-CNN training (mask-loss size mismatch /
CUDA assert) and corrupts DETR-style matchers.

``getitune.data.dataset._tiling_patches`` re-registers a filtering mask tiler
that prunes instances whose bounding box does not intersect the tile, mirroring
``BboxTiler`` so masks stay aligned with boxes/labels. These tests lock in that
behaviour.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch
from datumaro.experimental import Dataset
from datumaro.experimental.categories import LabelCategories, MaskCategories
from datumaro.experimental.fields import ImageInfo as DmImageInfo
from datumaro.experimental.fields import Subset
from datumaro.experimental.fields.masks import InstanceMaskField
from datumaro.experimental.filtering.filter_registry import create_filtering_transform
from datumaro.experimental.tiling.tiler_registry import TilerRegistry, TilingConfig, create_tiling_transform
from torchvision import tv_tensors

from getitune.data.dataset._tiling_patches import (
    _FilteringInstanceMaskTiler,
    _instance_intersects_tile,
    patch_instance_mask_tiler,
)
from getitune.data.entity.sample import InstanceSegmentationSample


def _bbox_tiler_keep(x1: int, y1: int, x2: int, y2: int, tx: int, ty: int, tw: int, th: int) -> bool:
    """Reimplementation of datumaro ``BboxTiler``'s keep criterion for reference.

    A box ``(x1, y1, x2, y2)`` is kept for a tile at ``(tx, ty)`` of size
    ``(tw, th)`` iff it intersects the tile rectangle.
    """
    return (x2 > tx) and (x1 < tx + tw) and (y2 > ty) and (y1 < ty + th)


class TestInstanceIntersectsTile:
    """``_instance_intersects_tile`` must mirror ``BboxTiler``'s keep criterion."""

    def _mask_from_box(self, x1: int, y1: int, x2: int, y2: int, h: int = 100, w: int = 100) -> np.ndarray:
        m = np.zeros((h, w), dtype=np.uint8)
        m[y1:y2, x1:x2] = 1
        return m

    def test_empty_mask_is_dropped(self) -> None:
        """An all-zero instance mask has no bounding box and is never kept."""
        assert _instance_intersects_tile(np.zeros((100, 100), dtype=np.uint8), 0, 0, 50, 50) is False

    @pytest.mark.parametrize(
        ("box", "tile"),
        [
            ((10, 10, 40, 40), (0, 0, 50, 50)),  # fully inside
            ((45, 45, 60, 60), (0, 0, 50, 50)),  # straddles bottom-right corner
            ((49, 49, 55, 55), (0, 0, 50, 50)),  # 1px overlap in the tile
            ((60, 60, 90, 90), (50, 50, 50, 50)),  # inside the second tile
            ((50, 10, 70, 30), (0, 0, 50, 50)),  # touches right edge (x1==tile_x2) -> dropped
            ((10, 10, 40, 40), (50, 0, 50, 50)),  # left of the second tile -> dropped
        ],
    )
    def test_matches_bbox_tiler_keep(self, box: tuple, tile: tuple) -> None:
        """The mask-derived keep decision equals the box-based ``BboxTiler`` decision."""
        x1, y1, x2, y2 = box
        tx, ty, tw, th = tile
        mask = self._mask_from_box(x1, y1, x2, y2)
        # The rasterised mask's exclusive bbox equals (x1, y1, x2, y2) for an axis-aligned rectangle.
        expected = _bbox_tiler_keep(x1, y1, x2, y2, tx, ty, tw, th)
        assert _instance_intersects_tile(mask, tx, ty, tw, th) is expected


class TestPatchInstanceMaskTiler:
    """Registration of the filtering mask tiler must be idempotent."""

    def test_patch_registers_filtering_tiler(self) -> None:
        patch_instance_mask_tiler()
        patch_instance_mask_tiler()  # idempotent: a second call is a no-op
        assert TilerRegistry.get_tiler(InstanceMaskField) is _FilteringInstanceMaskTiler


def _make_inst_seg_dataset(specs: list[tuple[int, int, int, int]], labels: list[int], size: int = 200) -> Dataset:
    """Build a single-image instance-segmentation dataset from axis-aligned boxes."""
    ds = Dataset(
        InstanceSegmentationSample,
        categories={
            "label": LabelCategories(labels=tuple(f"c{i}" for i in range(max(labels) + 1))),
            "masks": MaskCategories.generate(4),
        },
    )

    def inst(x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
        m = np.zeros((size, size), dtype=np.uint8)
        m[y1:y2, x1:x2] = 1
        return m

    masks = tv_tensors.Mask(torch.from_numpy(np.stack([inst(*s) for s in specs])))
    bboxes = torch.tensor([list(s) for s in specs], dtype=torch.float32)
    ds.append(
        InstanceSegmentationSample(
            subset=Subset.TRAINING,
            image=tv_tensors.Image(torch.zeros((3, size, size), dtype=torch.uint8)),
            bboxes=bboxes,
            masks=masks,
            label=torch.tensor(labels, dtype=torch.uint8),
            dm_image_info=DmImageInfo(height=size, width=size),
        )
    )
    return ds


class TestTilingKeepsInstanceSegConsistent:
    """End-to-end: after tiling, every tile has matching box/mask/label counts."""

    def test_boundary_instances_stay_aligned(self) -> None:
        patch_instance_mask_tiler()
        # Instances placed to fully-contain, straddle, and sit outside tile boundaries at 100.
        specs = [(10, 10, 40, 40), (90, 90, 110, 110), (150, 20, 180, 60), (95, 150, 140, 190)]
        labels = [0, 1, 2, 0]
        ds = _make_inst_seg_dataset(specs, labels)

        cfg = TilingConfig(tile_height=100, tile_width=100, overlap_x=0.0, overlap_y=0.0)
        tiled = ds.transform(create_tiling_transform(cfg, threshold_drop_ann=0.5), dtype=ds.dtype)
        tiled = tiled.transform(create_filtering_transform(), dtype=ds.dtype)

        assert len(tiled) > 0
        for i in range(len(tiled)):
            item = tiled[i]
            n_boxes = 0 if item.bboxes is None else int(item.bboxes.shape[0])
            n_masks = 0 if item.masks is None else int(item.masks.shape[0])
            n_labels = 0 if item.label is None else int(item.label.shape[0])
            assert n_boxes == n_masks == n_labels, f"tile {i}: boxes={n_boxes} masks={n_masks} labels={n_labels}"
