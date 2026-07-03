# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Pretrained weight references for instance segmentation models.

This module centralizes the pretrained checkpoint locations used by the
instance segmentation model implementations. Most entries are URLs pointing to
Geti-hosted checkpoint files, while torchvision-backed models may use
torchvision weight enum objects directly.
"""

from torchvision.models.detection.mask_rcnn import MaskRCNN_ResNet50_FPN_V2_Weights

_BASE_STORAGE_URL = "https://storage.geti.intel.com/weights"

MASKRCNN_PRETRAINED_URLS = {
    "maskrcnn_efficientnet_b2b": f"{_BASE_STORAGE_URL}/efficientnet_b2b-mask_rcnn-576x576.pth",
    "maskrcnn_swin_tiny": f"{_BASE_STORAGE_URL}"
    "/mask_rcnn_swin-t-p4-w7_fpn_fp16_ms-crop-3x_coco_20210908_165006-90a4008c.pth",
}

MASKRCNNTV_PRETRAINED_URLS = {
    "maskrcnn_resnet_50": MaskRCNN_ResNet50_FPN_V2_Weights.verify("DEFAULT").url,
}

RFDETR_PRETRAINED_URLS = {
    "rfdetr_seg_n": f"{_BASE_STORAGE_URL}/rf-detr-seg-n-ft.pth",
    "rfdetr_seg_s": f"{_BASE_STORAGE_URL}/rf-detr-seg-s-ft.pth",
    "rfdetr_seg_m": f"{_BASE_STORAGE_URL}/rf-detr-seg-m-ft.pth",
    "rfdetr_seg_l": f"{_BASE_STORAGE_URL}/rf-detr-seg-l-ft.pth",
    "rfdetr_seg_xl": f"{_BASE_STORAGE_URL}/rf-detr-seg-xl-ft.pth",
    "rfdetr_seg_2xl": f"{_BASE_STORAGE_URL}/rf-detr-seg-2xl-ft.pth",
}

RTMDET_PRETRAINED_URLS = {
    "rtmdet_inst_tiny": f"{_BASE_STORAGE_URL}/rtmdet-ins_tiny_8xb32-300e_coco_20221130_151727-ec670f7e.pth"
}
