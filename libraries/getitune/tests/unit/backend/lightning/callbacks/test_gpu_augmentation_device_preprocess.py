# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the GPU callback that converts deferred evaluation tiles to float on the device."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
import torch
from getidata.fields import ImageInfo as DmImageInfo
from getidata.fields.datasets import TileInfo
from torchvision import tv_tensors

from getitune.backend.lightning.callbacks.gpu_augmentation import GPUAugmentationCallback
from getitune.config.data import IntensityConfig, SubsetConfig
from getitune.data.augmentation.pipeline import CPUAugmentationPipeline
from getitune.data.entity.base import ImageInfo
from getitune.data.entity.sample import DetectionSample
from getitune.data.entity.tile import TileBatchData

RESIZE = {
    "class_path": "getitune.data.augmentation.transforms.Resize",
    "init_args": {"size": 64, "keep_aspect_ratio": False, "resize_targets": False},
}


def _eval_config(storage_dtype: str) -> SubsetConfig:
    return SubsetConfig(augmentations_cpu=[RESIZE], intensity=IntensityConfig(storage_dtype=storage_dtype))


def _raw_tile(storage_dtype: str) -> torch.Tensor:
    if storage_dtype == "uint8":
        return torch.randint(0, 256, (3, 40, 40), dtype=torch.uint8)
    return torch.randint(0, 65536, (3, 40, 40), dtype=torch.int32)


def _info(shape: tuple[int, int] = (40, 40)) -> ImageInfo:
    return ImageInfo._wrap(torch.zeros(1), img_idx=0, img_shape=shape, ori_shape=shape)


def _tile_info() -> TileInfo:
    return TileInfo(source_sample_idx=0, x=0, y=0, width=40, height=40)


def _batch(tile: torch.Tensor, info: ImageInfo) -> TileBatchData:
    return TileBatchData(
        batch_size=1,
        batch_tiles=[[tv_tensors.Image(tile)]],
        batch_tile_img_infos=[[info]],
        batch_tile_tile_infos=[[_tile_info()]],
        imgs_info=[info],
    )


class TestDeviceStage:
    @pytest.mark.parametrize("storage_dtype", ["uint8", "uint16"])
    def test_device_stage_matches_cpu_path(self, storage_dtype: str):
        config = _eval_config(storage_dtype)
        raw = _raw_tile(storage_dtype)
        pipeline = CPUAugmentationPipeline.from_config(config)

        cpu_out = pipeline(_sample_for(raw.clone(), _info()))

        callback = GPUAugmentationCallback(test_device_pipeline=pipeline)
        callback.setup(Mock(), Mock(data_input_params=Mock(mean=None, std=None)), "test")
        batch = _batch(raw.clone(), _info())
        callback.on_test_batch_start(Mock(), Mock(), batch, 0)

        assert cpu_out is not None
        assert torch.equal(batch.batch_tiles[0][0], cpu_out.image)
        assert batch.batch_tile_img_infos[0][0].img_shape == cpu_out.img_info.img_shape
        assert batch.batch_tile_img_infos[0][0].bit_depth == cpu_out.img_info.bit_depth

    def test_predict_batch_is_converted(self):
        pipeline = CPUAugmentationPipeline.from_config(_eval_config("uint8"))
        callback = GPUAugmentationCallback(test_device_pipeline=pipeline)
        callback.setup(Mock(), Mock(data_input_params=Mock(mean=None, std=None)), "predict")
        batch = _batch(_raw_tile("uint8"), _info())

        callback.on_predict_batch_start(Mock(), Mock(), batch, 0)

        assert batch.batch_tiles[0][0].is_floating_point()
        assert batch.batch_tiles[0][0].shape[-2:] == (64, 64)

    def test_float_tiles_are_left_unchanged(self):
        pipeline = CPUAugmentationPipeline.from_config(_eval_config("uint8"))
        callback = GPUAugmentationCallback(test_device_pipeline=pipeline)
        callback.setup(Mock(), Mock(data_input_params=Mock(mean=None, std=None)), "test")
        already = torch.rand(3, 64, 64)
        batch = _batch(already.clone(), _info((64, 64)))

        callback.on_test_batch_start(Mock(), Mock(), batch, 0)

        assert torch.equal(batch.batch_tiles[0][0], already)

    def test_no_pipeline_means_no_conversion(self):
        callback = GPUAugmentationCallback()
        callback.setup(Mock(), Mock(data_input_params=Mock(mean=None, std=None)), "test")
        raw = _raw_tile("uint8")
        batch = _batch(raw.clone(), _info())

        callback.on_test_batch_start(Mock(), Mock(), batch, 0)

        assert torch.equal(batch.batch_tiles[0][0], raw)


def _sample_for(image: torch.Tensor, info: ImageInfo) -> DetectionSample:
    height, width = image.shape[-2:]
    sample = DetectionSample(
        image=tv_tensors.Image(image),
        dm_image_info=DmImageInfo(height=height, width=width),
        bboxes=torch.zeros((0, 4), dtype=torch.float32),
        label=None,
    )
    sample.img_info = info
    return sample
