# Copyright (C) 2023-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Utility functions for build function."""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

import torch
import torch.nn.functional as f

if TYPE_CHECKING:
    from model_api.tilers import Tiler


def get_default_num_async_infer_requests() -> int:
    """Returns a default number of infer request for OV models."""
    import os

    number_requests = os.cpu_count()
    number_requests = max(1, int(number_requests / 2)) if number_requests is not None else 1
    msg = f"""Set the default number of OpenVINO inference requests to {number_requests}.
            You can specify the value in config."""
    warnings.warn(msg, stacklevel=1)
    return number_requests


def rescale_bboxes_to_original(
    bboxes_data: torch.Tensor,
    img_shape: tuple[int, int],
    ori_shape: tuple[int, int],
    padding: tuple[int, int, int, int],
    scale_factor: tuple[float, float] | None,
) -> torch.Tensor:
    """Rescale predicted bounding boxes from model input coordinates to original image coordinates.

    Handles two preprocessing cases:
    1. Letterbox (aspect-ratio resize + padding): undo padding, then divide by scale_factor, then clamp.
    2. Simple resize (no padding): multiply by ori/img ratio.

    Args:
        bboxes_data: Tensor of shape (N, 4+) with bounding boxes in XYXY format.
        img_shape: (H, W) of the preprocessed model input image.
        ori_shape: (H, W) of the original image.
        padding: (left, top, right, bottom) padding applied during preprocessing.
        scale_factor: (scale_h, scale_w) applied during preprocessing, or None.

    Returns:
        The same tensor with coordinates mapped to ori_shape space.
    """
    img_h, img_w = img_shape
    ori_h, ori_w = ori_shape

    if (img_h, img_w) == (ori_h, ori_w) or bboxes_data.numel() == 0:
        return bboxes_data

    if padding != (0, 0, 0, 0):
        if scale_factor is None:
            msg = (
                "Non-zero padding with scale_factor=None is invalid. "
                "This indicates a preprocessing pipeline bug — padding implies resize, which must set scale_factor."
            )
            raise ValueError(msg)
        # Letterbox: undo padding then undo scale
        pad_left, pad_top = float(padding[0]), float(padding[1])
        scale_h, scale_w = float(scale_factor[0]), float(scale_factor[1])
        bboxes_data[:, 0::2] -= pad_left
        bboxes_data[:, 1::2] -= pad_top
        bboxes_data[:, 0::2] /= scale_w
        bboxes_data[:, 1::2] /= scale_h
        bboxes_data[:, 0::2].clamp_(0, ori_w)
        bboxes_data[:, 1::2].clamp_(0, ori_h)
        return bboxes_data

    # Simple resize (no padding)
    scale_x = ori_w / img_w
    scale_y = ori_h / img_h
    bboxes_data[:, 0::2] *= scale_x
    bboxes_data[:, 1::2] *= scale_y

    return bboxes_data


def rescale_masks_to_original(
    masks: torch.Tensor,
    img_shape: tuple[int, int],
    ori_shape: tuple[int, int],
    padding: tuple[int, int, int, int],
) -> torch.Tensor:
    """Rescale predicted binary masks from model input coordinates to original image coordinates.

    Handles two preprocessing cases:
    1. Letterbox (aspect-ratio resize + padding): crop padding to get content, then resize to ori_shape.
    2. Simple resize (no padding): resize directly to ori_shape.

    Args:
        masks: Tensor of shape (N, img_H, img_W) with binary masks (uint8 0/1).
        img_shape: (H, W) of the preprocessed model input image.
        ori_shape: (H, W) of the original image.
        padding: (left, top, right, bottom) padding applied during preprocessing.

    Returns:
        Tensor of shape (N, ori_H, ori_W) with masks mapped to ori_shape space.
    """
    img_h, img_w = img_shape
    ori_h, ori_w = ori_shape

    if masks.numel() == 0:
        return masks.new_zeros((masks.shape[0], ori_h, ori_w), dtype=masks.dtype)

    if (img_h, img_w) == (ori_h, ori_w):
        return masks

    if padding != (0, 0, 0, 0):
        # Letterbox: crop padding to get the content region, then resize to ori_shape.
        # Computing content dims from img_shape - padding is exact (no rounding issues).
        pad_left, pad_top, pad_right, pad_bottom = padding
        content_h = img_h - pad_top - pad_bottom
        content_w = img_w - pad_left - pad_right
        masks = masks[:, pad_top : pad_top + content_h, pad_left : pad_left + content_w]

    # Resize masks to ori_shape using bilinear interpolation
    # f.interpolate expects (N, C, H, W) input
    masks_4d = masks.unsqueeze(1).float()  # (N, 1, H, W)
    return (f.interpolate(masks_4d, size=(ori_h, ori_w), mode="bilinear", align_corners=False).squeeze(1) > 0.5).to(
        torch.uint8
    )


@contextmanager
def skip_tiler_saliency_merge(tiler: Tiler) -> Iterator[None]:
    """Temporarily disable a ModelAPI ``Tiler``'s per-tile saliency-map merge.

    ``DetectionTiler`` (reused by ``InstanceSegmentationTiler``) can merge per-tile
    saliency maps into the final result via ``_merge_saliency_maps``, but
    ``getitune``'s tiled OpenVINO ``forward_tiles`` implementations never read the
    merged ``saliency_map``/``feature_vector`` (tiled OpenVINO inference does not
    currently expose XAI outputs), so that merge is pure wasted work. For detection
    it is especially costly: ``DetectionTiler._merge_saliency_maps`` merges
    pixel-by-pixel in a pure-Python nested loop with cost
    ``O(num_tiles * num_classes * H * W)``. With the default tiling configuration
    (``tile_size=400``, ``tiles_overlap=0.5``) a single large image can be split
    into hundreds of tiles, making that merge take from many minutes to multiple
    hours -- with no errors and no progress logged, it looks exactly like a hang
    until the job is eventually killed.

    ``model_api`` (>=0.4.7, see ``openvino-model-api`` changelog) exposes a public
    ``Tiler.merge_saliency_maps`` attribute for exactly this purpose. This context
    manager toggles it off for the duration of the tiled inference call and
    restores the previous value afterwards.

    Non-tiled evaluation and PyTorch tiled evaluation are unaffected: the former
    merges a single "tile" (fast early-return in ``_merge_saliency_maps``) and the
    latter (``getitune``'s own ``*TileMerge`` classes) already guard the equivalent
    merge behind ``explain_mode``, which defaults to ``False`` for evaluation.

    Note:
        If tiled OpenVINO explain/XAI support is added in the future, this skip must
        become conditional on whether saliency maps are actually needed.
    """
    original_merge_saliency_maps = tiler.merge_saliency_maps
    tiler.merge_saliency_maps = False
    try:
        yield
    finally:
        tiler.merge_saliency_maps = original_merge_saliency_maps
