"""Tiled item building decodes the source image once and yields the same tiles as per-tile lazy evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np
import pytest
import torch
from getidata import Dataset, LazyImage, Sample
from getidata.data_formats.coco.sample import CocoCategories, CocoSample
from getidata.fields import ImageInfo, Subset

from getitune.config.data import TileConfig
from getitune.data.dataset.base import _ensure_chw_format
from getitune.data.dataset.detection import DetectionDataset
from getitune.data.dataset.tile import TileDatasetFactory

if TYPE_CHECKING:
    from pathlib import Path


def _make_dataset(tmp_path: Path, subset: Subset) -> Dataset:
    rng = np.random.default_rng(0)
    path = tmp_path / "img.png"  # lossless, so the decoded pixels are exactly the random ones
    cv2.imwrite(str(path), rng.integers(0, 255, (700, 900, 3), dtype=np.uint8))
    dataset = Dataset(CocoSample, categories={"labels": CocoCategories(labels=["a"])})
    dataset.append(
        CocoSample(
            image=LazyImage(path),
            image_info=ImageInfo(width=900, height=700),
            image_id=0,
            subset=subset,
            bboxes=np.array([[50, 60, 120, 90], [520, 400, 200, 150]], dtype=np.float32),  # xywh
            labels=np.array([0, 0], dtype=np.uint32),
            polygons=None,
            areas=None,
            iscrowd=None,
            caption_group_ids=None,
            captions=None,
            keypoints=None,
        ),
    )
    return dataset


@pytest.fixture
def fxt_tile_dataset(tmp_path: Path):
    dataset = _make_dataset(tmp_path, Subset.TESTING)
    detection = DetectionDataset(dm_subset=dataset, transforms=None)
    return TileDatasetFactory.create(detection, TileConfig(enable_tiler=True, tile_size=(300, 300)))


def test_get_tiles_matches_per_tile_lazy_evaluation(fxt_tile_dataset) -> None:
    ds = fxt_tile_dataset
    tiles = ds.get_tiles(0)

    # The previous implementation: read every tile's lazy `image` field, then run the same per-tile steps.
    parent = ds.dm_subset.slice(0, 1)
    reference = []
    for tile in parent.transform(ds._tiling_transform, dtype=parent.dtype):
        tile.image = _ensure_chw_format(tile.image)
        object.__setattr__(tile.tile, "source_sample_idx", 0)
        reference.append(ds._apply_transforms(tile))

    assert len(tiles) == len(reference) > 1
    assert all(torch.equal(tile.image, ref.image) for tile, ref in zip(tiles, reference))


def test_get_tiles_decodes_the_source_once(fxt_tile_dataset, mocker) -> None:
    evaluated: list[str] = []
    original = Sample.evaluate_lazy_field

    def counting(self, name: str) -> object:
        evaluated.append(name)
        return original(self, name)

    mocker.patch.object(Sample, "evaluate_lazy_field", counting)
    tiles = fxt_tile_dataset.get_tiles(0)

    assert len(tiles) > 1
    assert evaluated.count("image") == 1
