"""The tile annotation threshold keeps an annotation in a tile only while enough of it stays visible.

A tile that only sees a sliver of a box keeps that box at threshold 0 (any intersection) and drops it at 0.5.
Test semantics keep every tile; validation additionally drops tiles left without annotations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np
import pytest
import torch
from getidata import Dataset, LazyImage
from getidata.categories import Categories, Colormap, LabelCategories, MaskCategories, RgbColor
from getidata.data_formats.coco.sample import CocoCategories, CocoSample
from getidata.fields import ImageInfo, Subset
from torchvision import tv_tensors

from getitune.config.data import TileConfig
from getitune.data.dataset.detection import DetectionDataset
from getitune.data.dataset.instance_segmentation import InstanceSegDataset
from getitune.data.dataset.tile import TileDataset, TileDatasetFactory
from getitune.data.entity.sample import InstanceSegmentationSample

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("threshold", [-0.01, 1.01, float("nan"), float("inf")])
def test_invalid_threshold_is_rejected(threshold: float) -> None:
    with pytest.raises(ValueError, match="drop_annotation_threshold"):
        TileConfig(drop_annotation_threshold=threshold)


@pytest.fixture
def fxt_detection_dataset(tmp_path: Path):
    """One 900x700 image with two boxes: one fully inside a tile, one spanning the tile boundary."""
    path = tmp_path / "img.png"  # lossless: decoded pixels are exactly the written ones
    cv2.imwrite(str(path), np.zeros((700, 900, 3), dtype=np.uint8))
    dataset = Dataset(CocoSample, categories={"labels": CocoCategories(labels=["a"])})
    dataset.append(
        CocoSample(
            image=LazyImage(path),
            image_info=ImageInfo(width=900, height=700),
            image_id=0,
            subset=Subset.TESTING,
            bboxes=np.array(
                [[50, 60, 120.0, 90.0], [520, 400, 200.0, 150.0]],  # xywh: second box spans x 520..720
                dtype=np.float32,
            ),
            labels=np.array([0, 0], dtype=np.uint32),
            polygons=None,
            areas=None,
            iscrowd=None,
            caption_group_ids=None,
            captions=None,
            keypoints=None,
        ),
    )
    return DetectionDataset(dm_subset=dataset, transforms=None)


def _tiles(ds, threshold: float) -> list:
    tile_ds = TileDatasetFactory.create(
        ds, TileConfig(enable_tiler=True, tile_size=(300, 300), drop_annotation_threshold=threshold)
    )
    assert isinstance(tile_ds, TileDataset)
    return tile_ds.get_tiles(0)


def test_threshold_05_drops_slivers_of_boundary_boxes(fxt_detection_dataset) -> None:
    """Test semantics keep every window; the boundary window keeps no annotation at ratio 0.5."""
    tiles = _tiles(fxt_detection_dataset, 0.5)
    assert len(tiles) == 12
    # the window [240..540] sees only 20 px of the [520..720] box (ratio 0.1) -> annotation dropped
    sliver = [t for t in tiles if t.tile.x == 240 and t.tile.y == 240]
    assert len(sliver) == 1
    assert len(sliver[0].bboxes) == 0  # threshold passed -> only the sliver was there
    assert all(t.tile.x != 240 or t.tile.y != 240 or len(t.bboxes) == 0 for t in [tiles[4]])
    assert any(t.tile.x == 480 and t.tile.y == 240 and len(t.bboxes) == 1 for t in tiles)  # full part kept


def test_threshold_0_keeps_any_intersection(fxt_detection_dataset) -> None:
    """At threshold 0 the boundary window keeps its sliver annotation (V3 behaviour before this change)."""
    tiles = _tiles(fxt_detection_dataset, 0.0)
    assert len(tiles) == 12
    sliver = [t for t in tiles if t.tile.x == 240 and t.tile.y == 240]
    assert len(sliver) == 1
    # window [240..540, 240..540]: box [520..720, 400..550] -> visible part (280..300, 160..300)
    assert np.allclose(np.asarray(sliver[0].bboxes), [[280.0, 160.0, 300.0, 300.0]], atol=1e-3)


@pytest.mark.parametrize(("threshold", "expected_labels"), [(0.0, [0, 1]), (0.5, [0])])
def test_instance_segmentation_threshold_keeps_masks_aligned(threshold, expected_labels) -> None:
    masks = torch.zeros(2, 200, 200, dtype=torch.uint8)
    masks[0, 10:40, 10:40] = 1
    masks[1, 90:110, 90:110] = 1
    categories: dict[str, Categories] = {
        "label": LabelCategories(labels=("first", "second")),
        "masks": MaskCategories(
            labels=["background", "instance"],
            colormap=Colormap({0: RgbColor(0, 0, 0), 1: RgbColor(255, 255, 255)}),
        ),
    }
    source = Dataset(InstanceSegmentationSample, categories=categories)
    source.append(
        InstanceSegmentationSample(
            image=tv_tensors.Image(torch.zeros(3, 200, 200, dtype=torch.uint8)),
            label=torch.tensor([0, 1], dtype=torch.uint16),
            bboxes=torch.tensor([[10.0, 10.0, 40.0, 40.0], [90.0, 90.0, 110.0, 110.0]]),
            masks=tv_tensors.Mask(masks),
            dm_image_info=ImageInfo(width=200, height=200),
            subset=Subset.TRAINING,
        )
    )
    dataset = InstanceSegDataset(dm_subset=source, transforms=[])
    tiled = TileDatasetFactory.create(
        dataset, TileConfig(enable_tiler=True, tile_size=(100, 100), overlap=0.0, drop_annotation_threshold=threshold)
    )
    first = next(item for item in tiled.dm_subset if item.tile.x == 0 and item.tile.y == 0)
    assert first.label.tolist() == expected_labels
    assert len(first.bboxes) == len(first.label) == len(first.masks)
    torch.testing.assert_close(first.masks, masks[: len(expected_labels), :100, :100])
