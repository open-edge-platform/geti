# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Reproject ground truth into the model's padded input canvas.

Detection and instance segmentation both validate with ``resize_targets:
false`` (see ``recipe/_base_/data/{detection,instance_segmentation}.yaml``),
so ground-truth boxes and masks stay in original image coordinates while the
image itself is resized (and, for instance segmentation, letterbox-padded)
to the model's input size. Predictions come out of the model in that input
canvas, so the two need to be brought into the same coordinate space before a
metric can compare them.

This reprojects the ground truth using ``ImageInfo.scale_factor`` and
``ImageInfo.padding`` — the exact values the ``Resize`` augmentation itself
computed and stored — rather than re-deriving a resize formula independently.
That matters because the two tasks' base recipes use different resize
conventions (detection distorts the aspect ratio with no padding; instance
segmentation preserves it and pads bottom-right only), and reading the actual
stored metadata is correct for both without having to special-case either
one, or notice if a future recipe picks a third convention.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
import torch.nn.functional as f

if TYPE_CHECKING:
    from getitune.data.entity.base import ImageInfo


def reproject_boxes_to_input_space(boxes: torch.Tensor, img_info: ImageInfo) -> torch.Tensor:
    """Move xyxy boxes from original image coordinates into the model's input canvas.

    Args:
        boxes: ``(N, 4)`` xyxy boxes in original image coordinates.
        img_info: Carries the ``scale_factor`` and ``padding`` the ``Resize``
            augmentation applied to this sample.

    Returns:
        ``(N, 4)`` boxes in the model's padded input coordinate space.

    Raises:
        ValueError: If ``img_info.scale_factor`` is unset (``None``), e.g.
            after a crop the ``Resize`` transform never ran.
    """
    if boxes.numel() == 0:
        return boxes
    if img_info.scale_factor is None:
        msg = "img_info.scale_factor is None; cannot reproject boxes without a Resize transform having run."
        raise ValueError(msg)

    scale_h, scale_w = img_info.scale_factor
    pad_left, pad_top, _, _ = img_info.padding
    reprojected = boxes.clone()
    reprojected[:, 0::2] = boxes[:, 0::2] * scale_w + pad_left
    reprojected[:, 1::2] = boxes[:, 1::2] * scale_h + pad_top
    return reprojected


def reproject_masks_to_input_space(
    masks: torch.Tensor,
    img_info: ImageInfo,
    input_size: tuple[int, int],
) -> torch.Tensor:
    """Move binary masks from original image coordinates into the model's input canvas.

    Resizes with nearest-neighbor interpolation to preserve binary values,
    then applies the same padding the ``Resize`` augmentation used.

    Args:
        masks: ``(N, ori_h, ori_w)`` binary masks in original image coordinates.
        img_info: Carries the ``scale_factor`` and ``padding`` applied to this sample.
        input_size: ``(H, W)`` of the model's input canvas.

    Returns:
        ``(N, H, W)`` binary masks in the model's padded input coordinate space.

    Raises:
        ValueError: If ``img_info.scale_factor`` is unset (``None``).
    """
    if masks.numel() == 0:
        return torch.zeros((0, *input_size), dtype=torch.bool, device=masks.device)
    if img_info.scale_factor is None:
        msg = "img_info.scale_factor is None; cannot reproject masks without a Resize transform having run."
        raise ValueError(msg)

    scale_h, scale_w = img_info.scale_factor
    pad_left, pad_top, pad_right, pad_bottom = img_info.padding
    ori_h, ori_w = img_info.ori_shape
    new_h, new_w = round(ori_h * scale_h), round(ori_w * scale_w)

    resized = f.interpolate(masks.unsqueeze(1).float(), size=(new_h, new_w), mode="nearest").squeeze(1)
    padded = f.pad(resized, [pad_left, pad_right, pad_top, pad_bottom])
    height, width = input_size
    return padded[:, :height, :width] > 0.5
