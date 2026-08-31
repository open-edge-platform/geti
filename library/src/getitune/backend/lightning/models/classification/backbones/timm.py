# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Timm Backbone Class for getitune classification.

Original papers:
- 'EfficientNetV2: Smaller Models and Faster Training,' https://arxiv.org/abs/2104.00298,
- 'Adversarial Examples Improve Image Recognition,' https://arxiv.org/abs/1911.09665.
"""

from __future__ import annotations

import timm
import torch
from torch import nn


class TimmBackbone(nn.Module):
    """Timm backbone model.

    Args:
        model_name (str): The name of the model.
            You can find available models at timm.list_models() or timm.list_pretrained().
    """

    def __init__(
        self,
        model_name: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.model_name = model_name

        # `exportable=True` is timm's own knob for export-friendliness: some architectures
        # swap internal ops (e.g. dynamic "same" padding, certain pooling/reshape patterns)
        # for export-safe equivalents when this flag is set. This is the same flag timm's
        # own `onnx_export.py` script always passes, precisely to avoid tracing/decomposition
        # failures like the ones observed with the newer torch.onnx FX-based exporter.
        self.model = timm.create_model(self.model_name, num_classes=0, exportable=True)

        # `num_features` is the backbone's last-block channel count for some architecture
        # families (e.g. MobileNetV3/EfficientNet with a conv_head expansion), which differs
        # from the actual pooled embedding size returned by forward(). `head_hidden_size`
        # (when present) reflects the true classifier input size; fall back to `num_features`
        # for architectures that don't define it.
        num_features = getattr(self.model, "head_hidden_size", self.model.num_features)
        if not isinstance(num_features, int):
            msg = f"Expected int num_features from timm model {model_name!r}, got {type(num_features)}"
            raise TypeError(msg)

        self.num_head_features = num_features
        self.num_features = num_features

    def forward(self, x: torch.Tensor, **kwargs) -> torch.Tensor:
        """Extract the pooled feature embedding using the architecture's own default pooling.

        The backbone is created with ``num_classes=0``, so timm sets the classifier head to
        ``Identity`` and each architecture applies its own default ``global_pool`` before
        returning. The result is a flat ``(B, num_features)`` embedding, not a spatial
        ``(B, C, H, W)`` feature map.

        This is deliberate rather than forced (e.g. via ``global_pool="avg"``): a single
        pooling mode is not universal across timm's 1700+ architectures (some models reject
        ``"avg"``, others override ``forward_head`` incompatibly, or return multiple feature
        branches). Delegating to each model's own default keeps this backbone
        architecture-agnostic.

        Args:
            x: Input image batch, shape ``(B, 3, H, W)``.

        Returns:
            Pooled feature embedding, shape ``(B, num_features)``.
        """
        return self.model(x)
