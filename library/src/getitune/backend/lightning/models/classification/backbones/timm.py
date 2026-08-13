# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Timm Backbone Class for getitune classification.

Original papers:
- 'EfficientNetV2: Smaller Models and Faster Training,' https://arxiv.org/abs/2104.00298,
- 'Adversarial Examples Improve Image Recognition,' https://arxiv.org/abs/1911.09665.
"""

from __future__ import annotations

from functools import partial
from typing import Callable, cast

import timm
import torch
from timm.optim import create_optimizer_v2
from torch import nn

from getitune.backend.lightning.models.base import DataInputParams

_TRANSFORMER_PREFIXES = ("vit", "deit", "beit", "swin", "cait", "xcit", "maxvit", "coat", "twins", "pvt")


def _is_transformer_family(model_name: str) -> bool:
    """Check whether a timm model name belongs to a transformer-like family."""
    family = model_name.split("_")[0].split(".")[0].lower()
    return family.startswith(_TRANSFORMER_PREFIXES)


def build_timm_optimizer_fn(model_name: str, learning_rate: float) -> Callable[..., torch.optim.Optimizer]:
    """Build an optimizer factory suited to the given timm model family.

    Transformer-like architectures (ViT, DeiT, Swin, etc.) use AdamW; convolutional
    architectures fall back to SGD with momentum.

    Args:
        model_name: Name of the timm model (as passed to `timm.create_model`).
        learning_rate: Base learning rate for the optimizer.

    Returns:
        A callable (partial of `timm.optim.create_optimizer_v2`) that produces the
        optimizer when called with the model's parameters.
    """
    kwargs = (
        {"opt": "adamw", "lr": learning_rate, "weight_decay": 0.05}
        if _is_transformer_family(model_name)
        else {"opt": "sgd", "lr": learning_rate, "momentum": 0.9, "weight_decay": 1e-4}
    )
    return partial(create_optimizer_v2, **kwargs)


def get_preprocessing_params(backbone_name: str) -> DataInputParams | dict[str, DataInputParams]:
    """Get default preprocessing parameters for the backbone."""
    cfg = timm.get_pretrained_cfg(backbone_name)
    if cfg is None:
        msg = f"Backbone {backbone_name} does not have a default preprocessing configuration."
        raise ValueError(msg)
    return DataInputParams(
        input_size=cast("tuple[int, int]", cfg.input_size[-2:]),
        mean=cast("tuple[float, float, float]", cfg.mean),
        std=cast("tuple[float, float, float]", cfg.std),
    )


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

        self.model = timm.create_model(self.model_name, num_classes=0)

        self.num_head_features = self.model.num_features
        self.num_features = self.model.num_features

    def forward(self, x: torch.Tensor, **kwargs) -> torch.Tensor:
        """Extract the pooled feature embedding using the architecture's own default pooling.

        The backbone is created with ``num_classes=0``, so timm sets the classifier head to
        ``Identity`` and each architecture applies its own default ``global_pool`` before
        returning. The result is a flat ``(B, num_features)`` embedding, not a spatial
        ``(B, C, H, W)`` feature map.

        This is deliberate rather than forced (e.g. via ``global_pool="avg"``): a single
        pooling mode is not universal across timm's 1400+ architectures (some models reject
        ``"avg"``, others override ``forward_head`` incompatibly, or return multiple feature
        branches). Delegating to each model's own default keeps this backbone
        architecture-agnostic.

        Args:
            x: Input image batch, shape ``(B, 3, H, W)``.

        Returns:
            Pooled feature embedding, shape ``(B, num_features)``.
        """
        return self.model(x)
