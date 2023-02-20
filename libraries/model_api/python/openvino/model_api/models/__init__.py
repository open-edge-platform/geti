"""
 Copyright (C) 2021-2023 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""


from .background_matting import (
    ImageMattingWithBackground,
    PortraitBackgroundMatting,
    VideoBackgroundMatting,
)
from .bert import BertEmbedding, BertNamedEntityRecognition, BertQuestionAnswering
from .centernet import CenterNet
from .classification import Classification
from .ctpn import CTPN
from .deblurring import Deblurring
from .detection_model import DetectionModel
from .detr import DETR
from .faceboxes import FaceBoxes
from .hpe_associative_embedding import HpeAssociativeEmbedding
from .image_model import ImageModel
from .instance_segmentation import MaskRCNNModel, YolactModel
from .model import Model
from .monodepth import MonoDepthModel
from .nanodet import NanoDet, NanoDetPlus
from .open_pose import OpenPose
from .retinaface import RetinaFace, RetinaFacePyTorch
from .segmentation import SalientObjectDetectionModel, SegmentationModel
from .ssd import SSD
from .ultra_lightweight_face_detection import UltraLightweightFaceDetection
from .utils import (
    RESIZE_TYPES,
    Detection,
    DetectionWithLandmarks,
    InputTransform,
    OutputTransform,
)
from .yolo import YOLO, YOLOF, YOLOX, YoloV3ONNX, YoloV4

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
    "BertEmbedding",
    "BertNamedEntityRecognition",
    "BertQuestionAnswering",
    "CenterNet",
    "Classification",
    "CTPN",
    "Deblurring",
    "DetectionModel",
    "DetectionWithLandmarks",
    "DETR",
    "FaceBoxes",
    "HpeAssociativeEmbedding",
    "ImageMattingWithBackground",
    "ImageModel",
    "InputTransform",
    "MaskRCNNModel",
    "Model",
    "MonoDepthModel",
    "NanoDet",
    "NanoDetPlus",
    "OpenPose",
    "OutputTransform",
    "PortraitBackgroundMatting",
    "RESIZE_TYPES",
    "RetinaFace",
    "RetinaFacePyTorch",
    "SalientObjectDetectionModel",
    "SegmentationModel",
    "SSD",
    "UltraLightweightFaceDetection",
    "VideoBackgroundMatting",
    "YolactModel",
    "YOLO",
    "YoloV3ONNX",
    "YoloV4",
    "YOLOF",
    "YOLOX",
    "Detection",
    "DetectionWithLandmarks",
    "classification_models" "detection_models",
    "segmentation_models",
]
