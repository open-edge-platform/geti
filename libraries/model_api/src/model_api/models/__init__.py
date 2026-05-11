#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from .action_classification import ActionClassificationModel
from .anomaly import AnomalyDetection
from .classification import ClassificationModel
from .detection_model import DetectionModel
from .image_model import ImageModel
from .instance_segmentation import MaskRCNNModel
from .keypoint_detection import KeypointDetectionModel, TopDownKeypointDetectionPipeline
from .model import Model
from .result import (
    AnomalyResult,
    ClassificationResult,
    Contour,
    DetectedKeypoints,
    DetectionResult,
    ImageResultWithSoftPrediction,
    InstanceSegmentationResult,
    PredictedMask,
    RotatedSegmentationResult,
    VisualPromptingResult,
    ZSLVisualPromptingResult,
)
from .sam_models import SAMDecoder, SAMImageEncoder
from .segmentation import SegmentationModel
from .ssd import SSD
from .utils import (
    OutputTransform,
    ResizeMetadata,
    add_rotated_rects,
    get_contours,
)
from .visual_prompting import Prompt, SAMLearnableVisualPrompter, SAMVisualPrompter
from .yolo import YOLO, YOLO11, YOLOF, YOLOX, YoloV3ONNX, YoloV4, YOLOv5, YOLOv8

classification_models = [
    "resnet-18-pytorch",
    "se-resnext-50",
    "mobilenet-v3-large-1.0-224-tf",
    "efficientnet-b0-pytorch",
]

detection_models = [
    # "face-detection-retail-0044", # resize_type is wrong or missed in model.yml
    "yolo-v4-tf",
    "ssd_mobilenet_v1_fpn_coco",
    "ssdlite_mobilenet_v2",
]

segmentation_models = [
    "fastseg-small",
]


__all__ = [
    "ActionClassificationModel",
    "add_rotated_rects",
    "AnomalyDetection",
    "AnomalyResult",
    "classification_models",
    "ClassificationModel",
    "ClassificationResult",
    "Contour",
    "detection_models",
    "DetectedKeypoints",
    "DetectionModel",
    "DetectionResult",
    "get_contours",
    "ImageModel",
    "ImageResultWithSoftPrediction",
    "InstanceSegmentationResult",
    "KeypointDetectionModel",
    "Label",
    "MaskRCNNModel",
    "Model",
    "OutputTransform",
    "PredictedMask",
    "Prompt",
    "ResizeMetadata",
    "RotatedSegmentationResult",
    "SAMDecoder",
    "SAMImageEncoder",
    "SAMLearnableVisualPrompter",
    "SAMVisualPrompter",
    "SalientObjectDetectionModel",
    "segmentation_models",
    "SegmentationModel",
    "SSD",
    "TopDownKeypointDetectionPipeline",
    "VisualPromptingResult",
    "YOLO",
    "YOLO11",
    "YOLOF",
    "YOLOv3ONNX",
    "YOLOv4",
    "YOLOv5",
    "YOLOv8",
    "YOLOX",
    "ZSLVisualPromptingResult",
    "YoloV3ONNX",
    "YoloV4",
]
