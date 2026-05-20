# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from model_api.models.model import Model, WrapperError


def test_wrapper_error():
    err = WrapperError("TestModel", "something went wrong")
    assert "TestModel" in str(err)
    assert "something went wrong" in str(err)


def test_raise_error():
    with pytest.raises(WrapperError, match="Model: test error"):
        Model.raise_error("test error")


def test_get_subclasses():
    subs = Model.get_subclasses()
    assert len(subs) > 0
    names = [s.__name__ for s in subs]
    assert "ImageModel" in names


def test_available_wrappers():
    wrappers = Model.available_wrappers()
    assert isinstance(wrappers, list)
    assert len(wrappers) > 0
    assert "Model" in wrappers


def test_get_model_class():
    cls = Model.get_model_class("Model")
    assert cls is Model


def test_get_model_class_unknown():
    with pytest.raises(WrapperError):
        Model.get_model_class("NonExistentModel12345")


def test_parameters_base():
    params = Model.parameters()
    assert isinstance(params, dict)


def test_image_model_parameters():
    from model_api.models.image_model import ImageModel

    params = ImageModel.parameters()
    assert "resize_type" in params
    assert "embedded_processing" in params
    assert "mean_values" in params


def test_detection_model_parameters():
    from model_api.models.detection_model import DetectionModel

    params = DetectionModel.parameters()
    assert "confidence_threshold" in params
    assert "labels" in params
    assert "iou_threshold" in params


def test_classification_model_parameters():
    from model_api.models.classification import ClassificationModel

    params = ClassificationModel.parameters()
    assert "topk" in params
    assert "labels" in params


def test_segmentation_model_parameters():
    from model_api.models.segmentation import SegmentationModel

    params = SegmentationModel.parameters()
    assert "blur_strength" in params
    assert "return_soft_prediction" in params


def test_anomaly_model_parameters():
    from model_api.models.anomaly import AnomalyDetection

    params = AnomalyDetection.parameters()
    assert "image_threshold" in params
    assert "task" in params


def test_ssd_parameters():
    from model_api.models.ssd import SSD

    params = SSD.parameters()
    assert "confidence_threshold" in params


def test_mask_rcnn_parameters():
    from model_api.models.instance_segmentation import MaskRCNNModel

    params = MaskRCNNModel.parameters()
    assert "confidence_threshold" in params
    assert "postprocess_semantic_masks" in params


def test_action_classification_parameters():
    from model_api.models.action_classification import ActionClassificationModel

    params = ActionClassificationModel.parameters()
    assert "labels" in params


def test_sam_encoder_parameters():
    from model_api.models.sam_models import SAMImageEncoder

    params = SAMImageEncoder.parameters()
    assert isinstance(params, dict)


def test_keypoint_detection_parameters():
    from model_api.models.keypoint_detection import KeypointDetectionModel

    params = KeypointDetectionModel.parameters()
    assert "labels" in params


def test_yolo_parameters():
    from model_api.models.yolo import YOLO

    params = YOLO.parameters()
    assert "confidence_threshold" in params


def test_yolov5_parameters():
    from model_api.models.yolo import YOLOv5

    params = YOLOv5.parameters()
    assert "confidence_threshold" in params


def test_yolov8_parameters():
    from model_api.models.yolo import YOLOv8

    params = YOLOv8.parameters()
    assert "confidence_threshold" in params


def test_yolo11_parameters():
    from model_api.models.yolo import YOLO11

    params = YOLO11.parameters()
    assert "confidence_threshold" in params


def test_yolox_parameters():
    from model_api.models.yolo import YOLOX

    params = YOLOX.parameters()
    assert "confidence_threshold" in params


def test_yolof_parameters():
    from model_api.models.yolo import YOLOF

    params = YOLOF.parameters()
    assert "confidence_threshold" in params


def test_visual_prompting_parameters():
    from model_api.models.visual_prompting import SAMVisualPrompter

    assert hasattr(SAMVisualPrompter, "__init__")


def test_sam_decoder_parameters():
    from model_api.models.sam_models import SAMDecoder

    params = SAMDecoder.parameters()
    assert isinstance(params, dict)
