# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest
import torch

from getitune.backend.lightning.models.classification.backbones.timm import TimmBackbone


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
