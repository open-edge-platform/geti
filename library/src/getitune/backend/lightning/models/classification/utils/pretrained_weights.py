# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Pretrained-weight loader mixins for classification models.

Each mixin implements ``load_pretrained`` for one download backend and operates on ``self.model.backbone``.
Mix into a model *before* the task base class so the mixin's ``load_pretrained`` overrides the base no-op.
"""

from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast
from urllib.parse import urlparse

from torch.hub import download_url_to_file

from getitune.backend.lightning.models.utils.utils import (
    load_checkpoint,
)

if TYPE_CHECKING:
    from torch import nn

    from getitune.backend.lightning.models.classification.backbones.vision_transformer import (
        VisionTransformerBackbone,
    )
    from getitune.types import PathLike

logger = logging.getLogger(__name__)


class _ClassifierModel(Protocol):
    """A classifier exposing a ``backbone`` submodule."""

    backbone: nn.Module


class _SupportsBackboneWeights(Protocol):
    """Lightning classification model wrapper exposing a classifier backbone."""

    model: _ClassifierModel
    model_name: str


class _ViTClassifierModel(Protocol):
    """A classifier exposing a ViT backbone."""

    backbone: VisionTransformerBackbone


class _SupportsViTBackboneWeights(Protocol):
    """Lightning classification model wrapper exposing a ViT backbone."""

    pretrained_urls: dict[str, str]
    model: _ViTClassifierModel
    model_name: str


class PytorchcvWeightsLoader:
    """Load backbone weights via pytorchcv's model store (EfficientNet)."""

    def load_pretrained(self: _SupportsBackboneWeights, weights: PathLike | None = None) -> None:
        """Download EfficientNet backbone weights into the cache dir."""
        from pytorchcv.models.common.model_store import download_model

        cache_dir = str(Path(weights).parent) if weights is not None else os.environ["PRETRAINED_WEIGHTS_CACHE_DIR"]
        download_model(
            net=self.model.backbone,
            model_name=self.model_name,
            local_model_store_dir_path=cache_dir,
        )
        logger.info("Loaded backbone weights from %s", cache_dir)


class TorchvisionWeightsLoader:
    """Load backbone weights from Torchvision (EfficientNet)."""

    def load_pretrained(self: _SupportsBackboneWeights, weights: PathLike | None = None) -> None:
        """Load weights: a local checkpoint if given, else torchvision's official set."""
        if weights is not None and Path(weights).exists():
            load_checkpoint(self.model.backbone, str(weights))
            return

        from torchvision.models import get_model, get_model_weights

        ref = get_model(name=self.model_name, weights=get_model_weights(self.model_name).verify("DEFAULT"))
        self.model.backbone.features.load_state_dict(ref.features.state_dict())  # pyrefly: ignore[missing-attribute]


class TimmWeightsLoader:
    """Load backbone weights via ``timm.models.load_pretrained``."""

    def load_pretrained(self: _SupportsBackboneWeights, weights: PathLike | None = None) -> None:
        """Load weights: a local checkpoint if given, else timm's pretrained source."""
        timm_model = cast("nn.Module", self.model.backbone.model)  # the nn.Module created by timm.create_model

        if weights is not None and Path(weights).exists():
            load_checkpoint(timm_model, str(weights))
            return

        from timm.models import load_pretrained

        load_pretrained(timm_model, pretrained_cfg=timm_model.pretrained_cfg)  # pyrefly: ignore[bad-argument-type]
        logger.info("Loaded timm pretrained weights for %s", self.model_name)


class VisionTransformerWeightsLoader:
    """Load backbone weights for ViT architecture."""

    def load_pretrained(self: _SupportsViTBackboneWeights, weights: PathLike | None = None) -> None:
        """Load weights: a local checkpoint if given, else torchvision's official set."""
        if weights is not None and Path(weights).exists():
            key_mapping = {
                "backbone.cls_token": "cls_token",
                "backbone.pos_embed": "pos_embed",
                "backbone.patch_embed.projection.weight": "patch_embed.proj.weight",
                "backbone.patch_embed.projection.bias": "patch_embed.proj.bias",
                "backbone.ln1.weight": "norm.weight",
                "backbone.ln1.bias": "norm.bias",
            }

            for i in range(len(self.model.backbone.blocks)):
                # Normalization layers
                key_mapping[f"backbone.layers.{i}.ln1.weight"] = f"blocks.{i}.norm1.weight"
                key_mapping[f"backbone.layers.{i}.ln1.bias"] = f"blocks.{i}.norm1.bias"
                key_mapping[f"backbone.layers.{i}.ln2.weight"] = f"blocks.{i}.norm2.weight"
                key_mapping[f"backbone.layers.{i}.ln2.bias"] = f"blocks.{i}.norm2.bias"

                # Attention blocks
                key_mapping[f"backbone.layers.{i}.attn.qkv.weight"] = f"blocks.{i}.attn.qkv.weight"
                key_mapping[f"backbone.layers.{i}.attn.qkv.bias"] = f"blocks.{i}.attn.qkv.bias"
                key_mapping[f"backbone.layers.{i}.attn.proj.weight"] = f"blocks.{i}.attn.proj.weight"
                key_mapping[f"backbone.layers.{i}.attn.proj.bias"] = f"blocks.{i}.attn.proj.bias"

                # Feed-Forward / MLP blocks
                key_mapping[f"backbone.layers.{i}.ffn.layers.0.0.weight"] = f"blocks.{i}.mlp.fc1.weight"
                key_mapping[f"backbone.layers.{i}.ffn.layers.0.0.bias"] = f"blocks.{i}.mlp.fc1.bias"
                key_mapping[f"backbone.layers.{i}.ffn.layers.1.weight"] = f"blocks.{i}.mlp.fc2.weight"

            load_checkpoint(self.model.backbone, str(weights), key_mapping=key_mapping)
            logger.info("Loaded ViT backbone weights from %s", weights)
            return

        if self.model_name not in self.pretrained_urls:
            warnings.warn(
                "No pretrained weights found for the specified model. Initializing model with random weights.",
                stacklevel=1,
            )
            return

        pretrained_url = self.pretrained_urls[self.model_name]
        logger.info("init weight - %s", pretrained_url)
        parts = urlparse(pretrained_url)
        filename = Path(parts.path).name

        cache_dir = Path(os.environ["PRETRAINED_WEIGHTS_CACHE_DIR"])
        cache_file = cache_dir / filename
        if not Path.exists(cache_file):
            download_url_to_file(pretrained_url, str(cache_file), "", progress=True)
        self.model.backbone.load_checkpoint(checkpoint_path=cache_file)  # pyrefly: ignore[not-callable]
        logger.info("Loaded ViT backbone weights from %s", cache_file)
