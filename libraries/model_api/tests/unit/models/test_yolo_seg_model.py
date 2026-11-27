#
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for YOLOSeg instance-segmentation wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models.model import WrapperError
from model_api.models.result import InstanceSegmentationResult
from model_api.models.yolo_seg import YOLOSeg

rng = np.random.default_rng(42)

_RT_INFO_ERROR = RuntimeError(
    "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
)


@dataclass
class FakeMetadata:
    names: set = field(default_factory=set)
    shape: list = field(default_factory=list)
    layout: str = ""
    precision: str = ""
    type: str = ""
    meta: dict = field(default_factory=dict)


def _make_seg_adapter(
    n_classes: int = 2,
    mask_dim: int = 32,
    n_boxes: int = 100,
    proto_h: int = 160,
    proto_w: int = 160,
):
    det_shape = (1, 4 + n_classes + mask_dim, n_boxes)
    proto_shape = (1, mask_dim, proto_h, proto_w)
    adapter = MagicMock(spec=InferenceAdapter)
    image_meta = FakeMetadata(shape=[1, 3, 640, 640], layout="NCHW")
    adapter.get_input_layers.return_value = {"image": image_meta}
    outputs = {
        "detection": FakeMetadata(shape=list(det_shape), precision="f32"),
        "protos": FakeMetadata(shape=list(proto_shape), precision="f32"),
    }
    adapter.get_output_layers.return_value = outputs
    adapter.get_rt_info.side_effect = _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    return adapter


class TestYOLOSeg:
    def test_init(self):
        adapter = _make_seg_adapter()
        model = YOLOSeg(adapter, configuration={})
        assert model.__model__ == "YOLO-seg"

    def test_init_invalid_output_count(self):
        adapter = MagicMock(spec=InferenceAdapter)
        image_meta = FakeMetadata(shape=[1, 3, 640, 640], layout="NCHW")
        adapter.get_input_layers.return_value = {"image": image_meta}
        adapter.get_output_layers.return_value = {
            "single": FakeMetadata(shape=[1, 10, 10]),
        }
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None
        with pytest.raises(WrapperError):
            YOLOSeg(adapter, configuration={})

    def test_init_invalid_output_shapes(self):
        adapter = MagicMock(spec=InferenceAdapter)
        image_meta = FakeMetadata(shape=[1, 3, 640, 640], layout="NCHW")
        adapter.get_input_layers.return_value = {"image": image_meta}
        adapter.get_output_layers.return_value = {
            "a": FakeMetadata(shape=[1, 10]),
            "b": FakeMetadata(shape=[1, 20]),
        }
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None
        with pytest.raises(WrapperError, match="Expected one rank-3 detection output"):
            YOLOSeg(adapter, configuration={})

    def test_init_invalid_channel_dim(self):
        adapter = MagicMock(spec=InferenceAdapter)
        image_meta = FakeMetadata(shape=[1, 3, 640, 640], layout="NCHW")
        adapter.get_input_layers.return_value = {"image": image_meta}
        det_shape = (1, 4 + 32, 100)
        adapter.get_output_layers.return_value = {
            "detection": FakeMetadata(shape=list(det_shape)),
            "protos": FakeMetadata(shape=[1, 32, 160, 160]),
        }
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None
        with pytest.raises(WrapperError):
            YOLOSeg(adapter, configuration={})

    def test_parameters(self):
        params = YOLOSeg.parameters()
        assert params["pad_value"].default_value == 114
        assert params["resize_type"].default_value == "fit_to_window_letterbox"
        assert params["reverse_input_channels"].default_value is False
        assert params["scale_values"].default_value == [255.0]
        assert params["confidence_threshold"].default_value == pytest.approx(0.25)
        assert params["iou_threshold"].default_value == pytest.approx(0.5)

    def test_postprocess_no_detections(self):
        n_classes = 2
        mask_dim = 32
        n_boxes = 10
        adapter = _make_seg_adapter(
            n_classes=n_classes,
            mask_dim=mask_dim,
            n_boxes=n_boxes,
        )
        model = YOLOSeg(adapter, configuration={"confidence_threshold": 0.9})
        det = np.zeros((1, 4 + n_classes + mask_dim, n_boxes), dtype=np.float32)
        protos = np.zeros((1, mask_dim, 160, 160), dtype=np.float32)
        meta = {"original_shape": (480, 640, 3)}
        result = model.postprocess({"detection": det, "protos": protos}, meta)
        assert isinstance(result, InstanceSegmentationResult)
        assert len(result.bboxes) == 0

    def test_postprocess_with_detection(self):
        n_classes = 2
        mask_dim = 32
        n_boxes = 10
        adapter = _make_seg_adapter(
            n_classes=n_classes,
            mask_dim=mask_dim,
            n_boxes=n_boxes,
        )
        model = YOLOSeg(
            adapter,
            configuration={
                "confidence_threshold": 0.1,
                "labels": ["class_a", "class_b"],
            },
        )
        det = np.zeros((1, 4 + n_classes + mask_dim, n_boxes), dtype=np.float32)
        det[0, 0, 0] = 320.0
        det[0, 1, 0] = 320.0
        det[0, 2, 0] = 100.0
        det[0, 3, 0] = 100.0
        det[0, 4, 0] = 0.9
        protos = rng.uniform(-1, 1, size=(1, mask_dim, 160, 160)).astype(np.float32)
        meta = {
            "original_shape": (480, 640, 3),
            "resized_shape": (640, 640, 3),
        }
        result = model.postprocess({"detection": det, "protos": protos}, meta)
        assert isinstance(result, InstanceSegmentationResult)
        assert len(result.bboxes) >= 1
        assert result.bboxes.shape[1] == 4
        assert result.masks.shape[0] >= 1
        assert result.masks.shape[1] == 480
        assert result.masks.shape[2] == 640
        assert result.masks.dtype == np.uint8

    def test_crop_mask(self):
        # Test full coverage
        masks = np.ones((2, 4, 4), dtype=np.float32)
        boxes = np.array([[0.0, 0.0, 4.0, 4.0], [1.0, 1.0, 3.0, 3.0]])
        result = YOLOSeg.crop_mask(masks, boxes)
        expected = np.array([
            [[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]],
            [[0.0, 0.0, 0.0, 0.0], [0.0, 1.0, 1.0, 0.0], [0.0, 1.0, 1.0, 0.0], [0.0, 0.0, 0.0, 0.0]],
        ])
        np.testing.assert_array_equal(result, expected)

        # Test no overlap
        masks = np.ones((1, 3, 3), dtype=np.float32)
        boxes = np.array([[-1.0, -1.0, 0.0, 0.0]])
        result = YOLOSeg.crop_mask(masks, boxes)
        assert result.sum() == 0

        # Test partial overlap
        masks = np.ones((1, 5, 5), dtype=np.float32)
        boxes = np.array([[2.0, 2.0, 4.0, 4.0]])
        result = YOLOSeg.crop_mask(masks, boxes)
        expected = np.zeros((1, 5, 5))
        expected[0, 2:4, 2:4] = 1
        np.testing.assert_array_equal(result, expected)

    def test_postprocess_multiple_detections(self):
        n_classes = 2
        mask_dim = 32
        n_boxes = 10
        adapter = _make_seg_adapter(
            n_classes=n_classes,
            mask_dim=mask_dim,
            n_boxes=n_boxes,
        )
        model = YOLOSeg(
            adapter,
            configuration={
                "confidence_threshold": 0.1,
                "labels": ["class_a", "class_b"],
            },
        )
        det = np.zeros((1, 4 + n_classes + mask_dim, n_boxes), dtype=np.float32)
        det[0, 0, 0] = 100.0
        det[0, 1, 0] = 100.0
        det[0, 2, 0] = 50.0
        det[0, 3, 0] = 50.0
        det[0, 4, 0] = 0.8

        det[0, 0, 1] = 400.0
        det[0, 1, 1] = 400.0
        det[0, 2, 1] = 80.0
        det[0, 3, 1] = 80.0
        det[0, 4, 1] = 0.6

        protos = rng.uniform(-1, 1, size=(1, mask_dim, 160, 160)).astype(np.float32)
        meta = {
            "original_shape": (480, 640, 3),
            "resized_shape": (640, 640, 3),
        }
        result = model.postprocess({"detection": det, "protos": protos}, meta)
        assert isinstance(result, InstanceSegmentationResult)
        assert len(result.bboxes) >= 1
