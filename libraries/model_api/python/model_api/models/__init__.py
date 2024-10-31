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
from .sam_models import SAMDecoder, SAMImageEncoder
from .segmentation import SalientObjectDetectionModel, SegmentationModel
from .ssd import SSD
from .utils import (
    AnomalyResult,
    ClassificationResult,
    Contour,
    DetectedKeypoints,
    Detection,
    DetectionResult,
    DetectionWithLandmarks,
    ImageResultWithSoftPrediction,
    InstanceSegmentationResult,
    OutputTransform,
    PredictedMask,
    SegmentedObject,
    SegmentedObjectWithRects,
    VisualPromptingResult,
    ZSLVisualPromptingResult,
    add_rotated_rects,
    get_contours,
)
from .visual_prompting import Prompt, SAMLearnableVisualPrompter, SAMVisualPrompter
from .yolo import YOLO, YOLOF, YOLOX, YoloV3ONNX, YoloV4, YOLOv5, YOLOv8

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
    "AnomalyDetection",
    "AnomalyResult",
    "ClassificationModel",
    "Contour",
    "DetectionModel",
    "DetectionWithLandmarks",
    "ImageMattingWithBackground",
    "ImageModel",
    "ImageResultWithSoftPrediction",
    "InstanceSegmentationResult",
    "VisualPromptingResult",
    "ZSLVisualPromptingResult",
    "PredictedMask",
    "SAMVisualPrompter",
    "SAMLearnableVisualPrompter",
    "KeypointDetectionModel",
    "TopDownKeypointDetectionPipeline",
    "MaskRCNNModel",
    "Model",
    "OutputTransform",
    "PortraitBackgroundMatting",
    "SalientObjectDetectionModel",
    "SegmentationModel",
    "SSD",
    "VideoBackgroundMatting",
    "YOLO",
    "YoloV3ONNX",
    "YoloV4",
    "YOLOv5",
    "YOLOv8",
    "YOLOF",
    "YOLOX",
    "SAMDecoder",
    "SAMImageEncoder",
    "ClassificationResult",
    "Prompt",
    "Detection",
    "DetectionResult",
    "DetectionWithLandmarks",
    "DetectedKeypoints",
    "classification_models",
    "detection_models",
    "segmentation_models",
    "SegmentedObject",
    "SegmentedObjectWithRects",
    "add_rotated_rects",
    "get_contours",
]
