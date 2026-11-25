# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Instance segmentation tiling works on polygons: tile-size masks for training, RLE ground truth for evaluation."""

from __future__ import annotations

import json

import numpy as np
import polars as pl
import pytest
import torch
from getidata import Dataset
from getidata.export_import import import_dataset
from PIL import Image

from getitune.backend.lightning.tools import tile_merge
from getitune.backend.lightning.tools.tile_merge import InstanceSegTileMerge
from getitune.config.data import TileConfig
from getitune.data.dataset.instance_segmentation import InstanceSegDataset
from getitune.data.dataset.tile import TileDatasetFactory
from getitune.data.entity.sample import PredictionBatch
from getitune.data.utils.structures.mask.mask_util import RLEMasks, polygon_to_bitmap

WIDTH, HEIGHT = 800, 600
POLYGONS = [
    [50, 50, 150, 50, 150, 150, 50, 150],  # inside the top-left tile
    [380, 100, 460, 100, 460, 200, 380, 200],  # straddles the vertical tile edge at x=400
]


@pytest.fixture
def coco_root(tmp_path):
    (tmp_path / "images" / "train").mkdir(parents=True)
    (tmp_path / "annotations").mkdir()
    Image.fromarray(np.full((HEIGHT, WIDTH, 3), 90, dtype=np.uint8)).save(tmp_path / "images" / "train" / "a.png")
    coco = {
        "images": [{"id": 1, "file_name": "a.png", "width": WIDTH, "height": HEIGHT}],
        "categories": [{"id": 1, "name": "thing"}],
        "annotations": [
            {
                "id": i + 1,
                "image_id": 1,
                "category_id": 1,
                "iscrowd": 0,
                "segmentation": [p],
                "bbox": [min(p[0::2]), min(p[1::2]), max(p[0::2]) - min(p[0::2]), max(p[1::2]) - min(p[1::2])],
                "area": 1,
            }
            for i, p in enumerate(POLYGONS)
        ],
    }
    (tmp_path / "annotations" / "instances_train.json").write_text(json.dumps(coco))
    return tmp_path


CFG = TileConfig(
    enable_tiler=True, enable_adaptive_tiling=False, tile_size=(400, 400), overlap=0.0, min_object_ratio_thr=0.3
)


def _as_subset(dataset: Dataset, name: str) -> Dataset:
    df = dataset.df.with_columns(pl.lit(name).cast(dataset.df.schema["subset"]).alias("subset"))
    return Dataset.from_dataframe(df=df, dtype_or_schema=dataset.dtype, schema=dataset.schema)


def test_training_tiles_get_masks_rasterized_at_tile_size(coco_root):
    dataset = TileDatasetFactory.create(InstanceSegDataset(dm_subset=import_dataset(coco_root)), CFG)

    assert dataset.rasterize_polygons
    samples = [dataset._read_dm_item(i) for i in range(len(dataset))]
    assert len(samples) == 2  # training keeps only the tiles that hold an object
    for sample in samples:
        height, width = sample.image.shape[-2:]
        assert tuple(sample.masks.shape[-2:]) == (height, width)  # never image-size masks
        assert len(sample.masks) == len(sample.bboxes) == len(sample.label)
    top_left, top_right = samples
    # the straddling polygon keeps 75% of its area in the right tile and only 25% (< 0.3) in the left one
    assert [int(m.sum()) for m in top_left.masks] == [100 * 100]
    assert [int(m.sum()) for m in top_right.masks] == [60 * 100]


def test_validation_ground_truth_is_rle_and_tiles_carry_no_annotations(coco_root):
    val = _as_subset(import_dataset(coco_root), "VALIDATION")
    dataset = TileDatasetFactory.create(InstanceSegDataset(dm_subset=val), CFG)

    entity = dataset._get_item_impl(0)

    assert isinstance(entity.ori_masks, RLEMasks)
    polygons = np.empty(2, dtype=object)
    polygons[:] = [np.array(p, dtype=np.float32).reshape(-1, 2) for p in POLYGONS]
    assert (entity.ori_masks.to_dense().numpy() == polygon_to_bitmap(polygons, HEIGHT, WIDTH)).all()
    assert len(entity.ori_bboxes) == len(entity.ori_labels) == 2
    assert len(entity.entity_list) == 2  # validation tiles are also limited to the ones that hold an object
    assert all(len(tile.masks) == 0 and len(tile.bboxes) == 0 for tile in entity.entity_list)


def _merge(monkeypatch, max_dense_bytes: int, incremental: bool = False):
    monkeypatch.setattr(tile_merge, "MAX_DENSE_MASK_BYTES", max_dense_bytes)
    cfg = TileConfig(enable_tiler=True, tile_size=(400, 400), iou_threshold=0.5)
    from getidata.fields import TileInfo

    from getitune.data.entity.base import ImageInfo

    def tile_pred(mask_rows, offset):
        mask = torch.zeros(len(mask_rows), 400, 400, dtype=torch.bool)
        for i, (y0, y1, x0, x1) in enumerate(mask_rows):
            mask[i, y0:y1, x0:x1] = True
        boxes = torch.tensor([[x0, y0, x1, y1] for y0, y1, x0, x1 in mask_rows], dtype=torch.float32).reshape(-1, 4)
        info = ImageInfo(img_idx=0, img_shape=(400, 400), ori_shape=(400, 400))
        batch = PredictionBatch(
            images=[torch.zeros(3, 4, 4)],
            imgs_info=[info],
            scores=[torch.tensor([0.9, 0.8][: len(mask_rows)])],
            bboxes=[boxes],
            labels=[torch.zeros(len(mask_rows), dtype=torch.long)],
            masks=[mask],
        )
        return batch, [TileInfo(source_sample_idx=0, x=offset[0], y=offset[1], width=400, height=400)]

    (a, ia), (b, ib) = (
        tile_pred([(10, 60, 20, 90), (300, 340, 300, 380)], (0, 0)),
        tile_pred([(100, 150, 50, 120)], (400, 200)),
    )
    img_info = ImageInfo(img_idx=0, img_shape=(HEIGHT, WIDTH), ori_shape=(HEIGHT, WIDTH))
    merger = InstanceSegTileMerge([img_info], 1, cfg)
    if incremental:
        merger.add(a, ia)
        merger.add(b, ib)
        return merger.finalize()[0]
    return merger.merge([a, b], [ia, ib])[0]


def test_incremental_add_equals_merge(monkeypatch):
    whole = _merge(monkeypatch, max_dense_bytes=10**12)
    incremental = _merge(monkeypatch, max_dense_bytes=10**12, incremental=True)

    assert (incremental.masks == whole.masks).all()
    assert torch.equal(incremental.scores, whole.scores)


def test_merged_masks_are_rle_for_large_images_and_equal_the_dense_result(monkeypatch):
    dense = _merge(monkeypatch, max_dense_bytes=10**12)
    rle = _merge(monkeypatch, max_dense_bytes=1)

    assert not isinstance(dense.masks, RLEMasks)
    assert isinstance(rle.masks, RLEMasks)
    assert len(rle.masks) == len(dense.masks) == 3
    assert (rle.masks.to_dense() == dense.masks.as_subclass(torch.Tensor)).all()
    assert sorted(int(m.sum()) for m in dense.masks) == [40 * 80, 50 * 70, 50 * 70]
    assert any(m[300:350, 450:520].all() for m in dense.masks)  # second tile's instance sits at its (400, 200) offset
