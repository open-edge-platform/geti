# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for deferring evaluation tile intensity mapping and resize to the device (dataset side)."""

from __future__ import annotations

from typing import cast
from unittest.mock import Mock

import pytest
import torch
from getidata.fields import ImageInfo as DmImageInfo
from getidata.fields import Subset
from torchvision import tv_tensors

from getitune.config.data import IntensityConfig, SubsetConfig
from getitune.data.augmentation.pipeline import CPUAugmentationPipeline
from getitune.data.dataset.tile import TileDetTestDataset
from getitune.data.entity.base import ImageInfo
from getitune.data.entity.sample import DetectionSample
from getitune.data.entity.tile import require_float_tiles
from getitune.types import TaskType

RESIZE = {
    "class_path": "getitune.data.augmentation.transforms.Resize",
    "init_args": {"size": 64, "keep_aspect_ratio": False, "resize_targets": False},
}


def _eval_config(storage_dtype: str, extra: list[dict] | None = None) -> SubsetConfig:
    return SubsetConfig(
        augmentations_cpu=[RESIZE, *(extra or [])],
        intensity=IntensityConfig(storage_dtype=storage_dtype),
    )


def _raw_tile(storage_dtype: str) -> torch.Tensor:
    if storage_dtype == "uint8":
        return torch.randint(0, 256, (3, 40, 40), dtype=torch.uint8)
    return torch.randint(0, 65536, (3, 40, 40), dtype=torch.int32)


def _info(shape: tuple[int, int] = (40, 40)) -> ImageInfo:
    return ImageInfo._wrap(torch.zeros(1), img_idx=0, img_shape=shape, ori_shape=shape)


def _sample(image: torch.Tensor, info: ImageInfo) -> DetectionSample:
    height, width = image.shape[-2:]
    sample = DetectionSample(
        image=tv_tensors.Image(image),
        dm_image_info=DmImageInfo(height=height, width=width),
        bboxes=torch.zeros((0, 4), dtype=torch.float32),
        label=None,
    )
    sample.img_info = info
    return sample


class TestPipelinePredicate:
    def test_intensity_then_resize_is_device_deferrable(self):
        pipeline = CPUAugmentationPipeline.from_config(_eval_config("uint8"))
        assert pipeline.is_intensity_resize_only()

    def test_resize_that_rescales_targets_is_not_deferrable(self):
        resize = {**RESIZE, "init_args": {**RESIZE["init_args"], "resize_targets": True}}
        pipeline = CPUAugmentationPipeline.from_config(SubsetConfig(augmentations_cpu=[resize]))
        assert not pipeline.is_intensity_resize_only()

    def test_extra_cpu_augmentation_is_not_deferrable(self):
        extra = {"class_path": "torchvision.transforms.v2.RandomHorizontalFlip", "init_args": {"p": 0.5}}
        pipeline = CPUAugmentationPipeline.from_config(_eval_config("uint8", extra=[extra]))
        assert not pipeline.is_intensity_resize_only()

    def test_missing_intensity_is_not_deferrable(self):
        config = SubsetConfig(augmentations_cpu=[RESIZE], intensity=cast("IntensityConfig", None))
        pipeline = CPUAugmentationPipeline.from_config(config)
        assert not pipeline.is_intensity_resize_only()


class TestTileDatasetDeferral:
    def _dataset(self, pipeline: CPUAugmentationPipeline) -> TileDetTestDataset:
        mock_item = Mock()
        mock_item.subset = Subset.VALIDATION
        dm_subset = Mock()
        dm_subset.__getitem__ = Mock(return_value=mock_item)
        dm_subset.transform = Mock(return_value=dm_subset)
        dm_subset.dtype = "inmemory"
        dm_subset.__len__ = Mock(return_value=1)

        dataset = Mock()
        dataset.task_type = TaskType.DETECTION
        dataset.dm_subset = dm_subset
        dataset.transforms = pipeline
        dataset.max_refetch = 10
        dataset.to_tv_image = True
        dataset.collate_fn = lambda x: x
        tile_config = Mock(tile_size=(40, 40), overlap=0)
        return TileDetTestDataset(dataset, tile_config, Subset.TESTING)

    def test_deferrable_pipeline_is_exposed_for_the_device(self):
        pipeline = CPUAugmentationPipeline.from_config(_eval_config("uint8"))
        assert self._dataset(pipeline).device_preprocess is pipeline

    def test_raw_integer_tile_is_sent_unchanged(self):
        tile_ds = self._dataset(CPUAugmentationPipeline.from_config(_eval_config("uint8")))

        raw = _raw_tile("uint8")
        out = tile_ds._apply_transforms(_sample(raw.clone(), _info()))

        assert out is not None
        assert out.image.dtype == torch.uint8
        assert torch.equal(out.image, raw)

    def test_float_tile_keeps_the_cpu_path_even_when_deferrable(self):
        # Float storage (e.g. float TIFF) is never scaled on the device, so it must still run on the CPU.
        tile_ds = self._dataset(CPUAugmentationPipeline.from_config(_eval_config("uint8")))

        float_tile = torch.rand(3, 40, 40)
        out = tile_ds._apply_transforms(_sample(float_tile, _info()))

        assert out is not None
        assert out.image.shape[-2:] == (64, 64)

    def test_non_deferrable_pipeline_still_runs_on_worker(self):
        extra = {"class_path": "torchvision.transforms.v2.RandomHorizontalFlip", "init_args": {"p": 0.0}}
        tile_ds = self._dataset(CPUAugmentationPipeline.from_config(_eval_config("uint8", extra=[extra])))

        out = tile_ds._apply_transforms(_sample(_raw_tile("uint8"), _info()))

        assert tile_ds.device_preprocess is None
        assert out is not None
        assert out.image.dtype == torch.float32
        assert out.image.shape[-2:] == (64, 64)


class TestFloatGuard:
    def test_raw_tiles_are_rejected(self):
        with pytest.raises(RuntimeError, match="float"):
            require_float_tiles([[tv_tensors.Image(torch.zeros(3, 8, 8, dtype=torch.uint8))]])

    def test_float_tiles_pass(self):
        require_float_tiles([[tv_tensors.Image(torch.zeros(3, 8, 8))]])
