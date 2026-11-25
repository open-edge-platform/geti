# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import numpy as np
import pycocotools.mask as mask_utils
import pytest
import torch

from getitune.data.utils.structures.mask.mask_util import RLEMasks, crop_to_rle, encode_rle, polygon_to_bitmap


@pytest.mark.parametrize("fill", [0.0, 0.1, 0.5, 1.0])
def test_crop_to_rle_equals_encoding_the_pasted_canvas(fill):
    rng = np.random.default_rng(0)
    height, width = 41, 67
    for _ in range(200):
        h, w = rng.integers(1, 20), rng.integers(1, 30)
        x, y = rng.integers(0, width - w + 1), rng.integers(0, height - h + 1)
        mask = rng.random((h, w)) < fill
        canvas = np.zeros((height, width), dtype=bool)
        canvas[y : y + h, x : x + w] = mask

        rle = crop_to_rle(mask, x, y, (height, width))

        assert rle == encode_rle(torch.from_numpy(canvas))
        assert (mask_utils.decode(mask_utils.frPyObjects(rle, height, width)).astype(bool) == canvas).all()


def test_rle_masks_from_polygons_matches_dense_rasterization_and_selects_instances():
    polygons = np.empty(3, dtype=object)
    polygons[:] = [
        np.array([[2, 2], [10, 2], [10, 8], [2, 8]], dtype=np.float32),
        np.array([[20, 5], [30, 5], [25, 15]], dtype=np.float32),
        np.array([[1, 20], [15, 20], [15, 28], [1, 28]], dtype=np.float32),
    ]

    rles = RLEMasks.from_polygons(polygons, (32, 40))

    assert len(rles) == 3
    assert (rles.to_dense().numpy() == polygon_to_bitmap(polygons, 32, 40)).all()
    assert len(rles[[0, 2]]) == 2
    assert len(rles[torch.tensor([True, False, True])]) == 2
    assert len(rles[1:]) == 2
    assert len(RLEMasks.from_polygons(None, (32, 40))) == 0
    assert RLEMasks.from_polygons(None, (32, 40)).to_dense().shape == (0, 32, 40)


def test_rle_masks_refuses_to_decode_when_dense_would_be_too_large():
    rles = RLEMasks.from_polygons(
        np.array([np.array([[0, 0], [5, 0], [5, 5]], dtype=np.float32)], dtype=object), (100, 100)
    )

    with pytest.raises(MemoryError):
        rles.to_dense(max_bytes=1000)
