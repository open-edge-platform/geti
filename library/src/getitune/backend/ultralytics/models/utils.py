# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Utility helpers shared by Ultralytics model wrappers."""

from __future__ import annotations

from typing import Callable, cast

import torch
from ultralytics.nn.modules.head import Classify


def multilabel_classify_forward(module: Classify) -> Callable[[torch.Tensor | list[torch.Tensor]], torch.Tensor]:
    """Build a ``Classify`` forward that emits sigmoid scores for inference.

    Training and export modes continue to emit raw logits so BCE loss and
    export-time post-processing remain consistent.
    """

    def forward(x: torch.Tensor | list[torch.Tensor]) -> torch.Tensor:
        if isinstance(x, list):
            x = torch.cat(x, 1)
        x = module.linear(module.drop(module.pool(module.conv(x)).flatten(1)))
        if module.training or module.export:
            return x
        return x.sigmoid()

    return forward


def patch_multilabel_classify_head(model: torch.nn.Module) -> None:
    """Replace each ``Classify`` head's inference softmax with sigmoid.

    This patch is required for multi-label classification because upstream
    YOLO classification checkpoints use softmax semantics by default.
    """
    for module in model.modules():
        if isinstance(module, Classify):
            module.forward = cast("Callable[..., torch.Tensor]", multilabel_classify_forward(module))
