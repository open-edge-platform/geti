# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Reimport models from differnt backends for user frendly imports."""

from getitune.backend.lightning.models import (
    ATSS,
    DEIMV2,
    RTDETR,
    SSD,
    YOLOX,
    DEIMDFine,
    DFine,
    RFDETR,
    RFDETRInst,
    EdgeCrafter,
    DinoV2Seg,
    EfficientNet,
    LiteHRNet,
    MaskRCNN,
    MaskRCNNTV,
    MobileNetV3,
    RTMDetInst,
    RTMPose,
    SegNext,
    TimmModel,
    TVModel,
    VisionTransformer,
)
from getitune.backend.openvino.models import (
    OVDetectionModel,
    OVHlabelClassificationModel,
    OVInstanceSegmentationModel,
    OVKeypointDetectionModel,
    OVModel,
    OVMulticlassClassificationModel,
    OVMultilabelClassificationModel,
    OVSegmentationModel,
)

try:
    from getitune.backend.ultralytics.models import (
        UltralyticsDetectionModel,
        UltralyticsInstSegModel,
        UltralyticsMultiClassClsModel,
        UltralyticsMultiLabelClsModel,
        UltralyticsSemanticSegModel,
    )
except ImportError:
    ULTRALYTICS_INSTALLED = False
else:
    ULTRALYTICS_INSTALLED = True

__all__ = [
    # detection
    "ATSS",
    "DEIMV2",
    "RTDETR",
    "SSD",
    "YOLOX",
    "DEIMDFine",
    "DFine",
    "RFDETR",
    "EdgeCrafter",
    # semantic segmentation
    "DinoV2Seg",
    # classification
    "EfficientNet",
    "LiteHRNet",
    # instance segmentation
    "MaskRCNN",
    "MaskRCNNTV",
    "MobileNetV3",
    "OVDetectionModel",
    "OVHlabelClassificationModel",
    "OVInstanceSegmentationModel",
    "OVKeypointDetectionModel",
    "RFDETRInst",
    # OpenVINO models
    "OVModel",
    "OVMulticlassClassificationModel",
    "OVMultilabelClassificationModel",
    "OVSegmentationModel",
    "RTMDetInst",
    "RTMPose",
    "SegNext",
    "TVModel",
    "TimmModel",
    "VisionTransformer",
]

if ULTRALYTICS_INSTALLED == True:
    __all__.extend(
        [
            "UltralyticsDetectionModel",
            "UltralyticsInstSegModel",
            "UltralyticsMultiClassClsModel",
            "UltralyticsMultiLabelClsModel",
            "UltralyticsSemanticSegModel",
        ]
    )
