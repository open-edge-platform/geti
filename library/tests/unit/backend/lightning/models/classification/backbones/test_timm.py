# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
import torch
from torch import nn

from getitune.backend.lightning.models.base import DataInputParams
from getitune.backend.lightning.models.classification.backbones.timm import (
    TimmBackbone,
    build_timm_optimizer_fn,
    get_preprocessing_params,
)


class TestBuildTimmOptimizerFn:
    @pytest.mark.parametrize(
        ("model_name", "expected_kwargs"),
        [
            ("vit_base_patch16_224", {"opt": "adamw", "weight_decay": 0.05}),
            ("vit_base_patch16_224.augreg_in21k", {"opt": "adamw", "weight_decay": 0.05}),  # dotted suffix
            ("VIT_base_patch16_224", {"opt": "adamw", "weight_decay": 0.05}),  # case-insensitive
            ("swin_tiny_patch4_window7_224", {"opt": "adamw", "weight_decay": 0.05}),
            ("tf_efficientnetv2_s.in21k", {"opt": "sgd", "momentum": 0.9, "weight_decay": 1e-4}),
            ("resnet50", {"opt": "sgd", "momentum": 0.9, "weight_decay": 1e-4}),
        ],
    )
    def test_selects_expected_optimizer_kwargs(self, model_name, expected_kwargs):
        factory = build_timm_optimizer_fn(model_name=model_name, learning_rate=0.01)
        assert factory.keywords == {"lr": 0.01, **expected_kwargs}  # pyrefly: ignore[missing-attribute]

    def test_factory_produces_working_optimizer(self):
        factory = build_timm_optimizer_fn(model_name="resnet50", learning_rate=0.05)
        optimizer = factory(nn.Linear(4, 2))
        assert isinstance(optimizer, torch.optim.Optimizer)
        assert optimizer.defaults["lr"] == 0.05


@pytest.mark.parametrize(
    ("backbone_name", "expected_input_params"),
    [
        (
            "tf_efficientnetv2_s.in21k",
            DataInputParams(input_size=(300, 300), mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)),
        ),
        ("vit_base_patch16_224", DataInputParams(input_size=(224, 224), mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))),
        (
            "swin_tiny_patch4_window7_224",
            DataInputParams(input_size=(224, 224), mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ),
    ],
)
def test_get_preprocessing_params_returns_expected_values(backbone_name: str, expected_input_params: DataInputParams):
    assert get_preprocessing_params(backbone_name) == expected_input_params


class TestBackbone:
    @pytest.mark.parametrize(
        ("backbone_name", "input_size", "expected_feature_dim"),
        [
            ("tf_efficientnetv2_s.in21k", (244, 244), 1280),
            ("vit_base_patch16_224", (224, 224), 768),
            ("swin_tiny_patch4_window7_224", (224, 224), 768),
        ],
    )
    def test_forward(self, backbone_name: str, input_size: tuple[int, int], expected_feature_dim: int) -> None:
        model = TimmBackbone(model_name=backbone_name)
        assert model(torch.randn(1, 3, input_size[0], input_size[1]))[0].shape == torch.Size([expected_feature_dim])
