# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Utilities for loading pretrained weights into Lightning model wrappers.

This module provides ``PretrainedWeightsMixin``, a small mixin for model classes
that expose an underlying PyTorch module through ``model`` and define
``pretrained_urls`` keyed by ``model_name``. The mixin resolves the default
pretrained checkpoint when no explicit path is provided and delegates checkpoint
loading to the shared model utility functions.

Concrete model classes may override ``pretrained_key_mapping`` when checkpoint
parameter names differ from the current model implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from torch import nn

    from getitune.types import PathLike


class _SupportsPretrainedWeights(Protocol):
    pretrained_urls: dict[str, str]
    model: nn.Module
    model_name: str

    @property
    def pretrained_key_mapping(self) -> dict[str, str] | None:
        """Mapping used to rename checkpoint keys before loading pretrained weights."""
        ...


class PretrainedWeightsMixin:
    """Mixin that adds pretrained-weight loading support to model classes.

    Classes using this mixin must define ``model``, ``model_name``, and
    ``pretrained_urls``. When no checkpoint path is provided, the default
    checkpoint is selected from ``pretrained_urls`` using ``model_name``.
    """

    @property
    def pretrained_key_mapping(self) -> dict[str, str] | None:
        """Mapping used to rename checkpoint keys before loading pretrained weights."""
        return None

    def load_pretrained(self: _SupportsPretrainedWeights, weights: PathLike | None = None) -> None:
        """Load pretrained weights into the model.

        Args:
            weights (PathLike | None): Path to the pretrained weights file. If None, uses default weights.
        """
        from getitune.backend.lightning.models.utils.utils import load_checkpoint

        if weights is None:
            weights = self.pretrained_urls[self.model_name]

        load_checkpoint(self.model, str(weights), key_mapping=self.pretrained_key_mapping)
