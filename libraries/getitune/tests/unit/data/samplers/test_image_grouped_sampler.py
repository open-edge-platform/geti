# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import polars as pl

from getitune.data.samplers.image_grouped_sampler import ImageGroupedSampler, tile_source_indices

SOURCE_IDX = np.repeat(np.arange(5), [3, 7, 1, 4, 5])  # 5 images, 20 tiles


def test_every_tile_once_and_grouped_by_image():
    order = list(ImageGroupedSampler(SOURCE_IDX))

    assert sorted(order) == list(range(len(SOURCE_IDX)))
    assert len(ImageGroupedSampler(SOURCE_IDX)) == len(SOURCE_IDX)
    images = SOURCE_IDX[order]
    # each image forms exactly one contiguous run
    assert 1 + np.count_nonzero(images[1:] != images[:-1]) == 5


def test_order_is_reshuffled_between_epochs():
    sampler = ImageGroupedSampler(np.repeat(np.arange(20), 10))

    assert list(sampler) != list(sampler)


def test_ratio_draws_fraction_of_each_image_with_at_least_one_tile():
    sampler = ImageGroupedSampler(SOURCE_IDX, ratio=0.5)
    order = list(sampler)

    assert len(order) == len(sampler) == 2 + 4 + 1 + 2 + 3
    assert len(set(order)) == len(order)
    assert set(SOURCE_IDX[order]) == {0, 1, 2, 3, 4}


def test_tile_source_indices_reads_tile_column_and_handles_untiled_dataset():
    transforms = MagicMock()
    transforms.schema.attributes = {"tile": object()}
    transforms.apply.return_value = pl.DataFrame({"tile": [{"source_sample_idx": 0}, {"source_sample_idx": 2}]})
    tiled = SimpleNamespace(dm_subset=SimpleNamespace(_transforms=transforms))

    assert tile_source_indices(tiled).tolist() == [0, 2]
    transforms.apply.assert_called_once_with(["tile"])
    assert tile_source_indices(SimpleNamespace(dm_subset=SimpleNamespace(_transforms=None))) is None
    transforms.schema.attributes = {}
    assert tile_source_indices(tiled) is None


def test_inner_sampler_draws_are_regrouped_by_image_and_keep_their_multiplicity():
    # A class-balanced draw repeats tiles of rare images many times.
    draws = [0, 0, 0, 5, 5, 10, 11, 2, 0, 5, 19, 1]
    inner = list(draws)

    sampler = ImageGroupedSampler(SOURCE_IDX, inner=inner)
    order = list(sampler)

    assert len(sampler) == len(draws)
    assert sorted(order) == sorted(draws)
    images = SOURCE_IDX[order]
    assert 1 + np.count_nonzero(images[1:] != images[:-1]) == len(set(images.tolist()))
