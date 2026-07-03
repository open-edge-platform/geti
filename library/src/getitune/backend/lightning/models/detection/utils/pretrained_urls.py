# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Pretrained checkpoint URL registry for detection models.

This module defines mappings from detection model identifiers to their pretrained
checkpoint URLs. The identifiers are used by model builders and recipes to locate
the correct initialization weights for each architecture variant.

All checkpoints are hosted under the Geti weights storage unless a model family
requires a legacy or external URL. Keep keys synchronized with the model names
accepted by the corresponding detection model factories.
"""

from __future__ import annotations

_BASE_STORAGE_URL = "https://storage.geti.intel.com/weights"

ATSS_PRETRAINED_URLS: dict[str, str] = {
    "atss_mobilenetv2": f"{_BASE_STORAGE_URL}/mobilenet_v2-atss.pth",
    "atss_resnext101": f"{_BASE_STORAGE_URL}/resnext101_atss_070623.pth",
}

DFINE_PRETRAINED_URLS: dict[str, str] = {
    "dfine_hgnetv2_n": f"{_BASE_STORAGE_URL}/dfine_n_coco.pth",
    "dfine_hgnetv2_s": f"{_BASE_STORAGE_URL}/dfine_s_coco.pth",
    "dfine_hgnetv2_m": f"{_BASE_STORAGE_URL}/dfine_m_coco.pth",
    "fdffifne_hgnetv2_l": f"{_BASE_STORAGE_URL}/dfine_l_coco.pth",
    "dfine_hgnetv2_x": f"{_BASE_STORAGE_URL}/dfine_x_coco.pth",
}

RTDETR_PRETRAINED_URLS: dict[str, str] = {
    "rtdetr_18": f"{_BASE_STORAGE_URL}/rtdetr_r18vd_5x_coco_objects365_from_paddle.pth",
    "rtdetr_50": f"{_BASE_STORAGE_URL}/rtdetr_r50vd_2x_coco_objects365_from_paddle.pth",
    "rtdetr_101": f"{_BASE_STORAGE_URL}/rtdetr_r101vd_2x_coco_objects365_from_paddle.pth",
}

DEIM_DFINE_PRETRAINED_URLS: dict[str, str] = {
    "deim_dfine_hgnetv2_n": f"{_BASE_STORAGE_URL}/deim_dfine_hgnetv2_n_coco_160e.pth",
    "deim_dfine_hgnetv2_s": f"{_BASE_STORAGE_URL}/deim_dfine_hgnetv2_s_coco_120e.pth",
    "deim_dfine_hgnetv2_m": f"{_BASE_STORAGE_URL}/deim_dfine_hgnetv2_m_coco_90e.pth",
    "deim_dfine_hgnetv2_l": f"{_BASE_STORAGE_URL}/deim_dfine_hgnetv2_l_coco_50e.pth",
    "deim_dfine_hgnetv2_x": f"{_BASE_STORAGE_URL}/deim_dfine_hgnetv2_x_coco_50e.pth",
}

DEIMV2_PRETRAINED_URLS: dict[str, str] = {
    "deimv2_x": f"{_BASE_STORAGE_URL}/deimv2_dinov3_x_coco.pth",
    "deimv2_l": f"{_BASE_STORAGE_URL}/deimv2_dinov3_l_coco.pth",
    "deimv2_m": f"{_BASE_STORAGE_URL}/deimv2_dinov3_m_coco.pth",
    "deimv2_s": f"{_BASE_STORAGE_URL}/deimv2_dinov3_s_coco.pth",
}

RFDETR_PRETRAINED_URLS: dict[str, str] = {
    "rfdetr_nano": f"{_BASE_STORAGE_URL}/rf-detr-nano-2026.pth",
    "rfdetr_small": f"{_BASE_STORAGE_URL}/rf-detr-small-2026.pth",
    "rfdetr_medium": f"{_BASE_STORAGE_URL}/rf-detr-medium-2026.pth",
    "rfdetr_large": f"{_BASE_STORAGE_URL}/rf-detr-large-2026.pth",
}

SSD_PRETRAINED_URLS: dict[str, str] = {
    "ssd_mobilenetv2": f"{_BASE_STORAGE_URL}/mobilenet_v2-2s_ssd-992x736.pth",
}

YOLOX_PRETRAINED_URLS: dict[str, str] = {
    "yolox_tiny": f"{_BASE_STORAGE_URL}/yolox_tiny_8x8.pth",
    "yolox_s": f"{_BASE_STORAGE_URL}/yolox_s_8x8_300e_coco_20211121_095711-4592a793.pth",
    "yolox_l": f"{_BASE_STORAGE_URL}/yolox_l_8x8_300e_coco_20211126_140236-d3bd2b23.pth",
    "yolox_x": f"{_BASE_STORAGE_URL}/yolox_x_8x8_300e_coco_20211126_140254-1ef88d67.pth",
}
