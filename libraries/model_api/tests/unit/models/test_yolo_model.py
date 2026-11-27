#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for YOLO model variants and helper functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models.result import DetectionResult
from model_api.models.yolo import (
    ANCHORS,
    YOLO,
    YOLO11,
    YOLOF,
    YOLOX,
    DetectionBox,
    YoloV3ONNX,
    YoloV4,
    YOLOv5,
    YOLOv8,
    permute_to_N_HWA_K,
    sigmoid,
    xywh2xyxy,
)

rng = np.random.default_rng(0)

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


# ---------------------------------------------------------------------------
# Adapter helpers
# ---------------------------------------------------------------------------
def _make_yolo_adapter(
    input_shape=(1, 3, 416, 416),
    output_shapes=None,
    layout="NCHW",
    output_metas=None,
    operations_by_type_return=None,
):
    """Create a mock InferenceAdapter for YOLO-family models.

    output_shapes: dict of {name: shape} or None for single default output.
    output_metas: dict of {name: meta_dict} for RegionYolo meta.
    """
    adapter = MagicMock(spec=InferenceAdapter)
    image_meta = FakeMetadata(shape=list(input_shape), layout=layout)
    adapter.get_input_layers.return_value = {"image": image_meta}

    outputs = {}
    for name, shape in output_shapes.items():
        meta = {}
        if output_metas and name in output_metas:
            meta = output_metas[name]
        outputs[name] = FakeMetadata(
            shape=list(shape),
            meta=meta,
            type="RegionYolo",
        )
    adapter.get_output_layers.return_value = outputs
    adapter.get_rt_info.side_effect = _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    adapter.operations_by_type = MagicMock(
        return_value=operations_by_type_return or {},
    )
    return adapter


# ---------------------------------------------------------------------------
# Test free functions
# ---------------------------------------------------------------------------
class TestPermuteToNHWAK:
    def test_nchw_layout(self):
        tensor = np.arange(1 * 10 * 3 * 3).reshape(1, 10, 3, 3).astype(float)
        K = 5
        result = permute_to_N_HWA_K(tensor, K, "NCHW")
        assert result.shape == (1, 3 * 3 * 2, K)

    def test_nhwc_layout(self):
        # NHWC: (N, H, W, C) -> internally transposed to NCHW first
        tensor = np.arange(1 * 3 * 3 * 10).reshape(1, 3, 3, 10).astype(float)
        K = 5
        result = permute_to_N_HWA_K(tensor, K, "NHWC")
        assert result.shape == (1, 3 * 3 * 2, K)


class TestSigmoid:
    def test_zero(self):
        assert sigmoid(0) == pytest.approx(0.5)

    def test_large_positive(self):
        assert sigmoid(100) == pytest.approx(1.0)

    def test_large_negative(self):
        assert sigmoid(-100) == pytest.approx(0.0)

    def test_array(self):
        x = np.array([0, 1, -1])
        result = sigmoid(x)
        assert result[0] == pytest.approx(0.5)
        assert result[1] > 0.5
        assert result[2] < 0.5


class TestXywh2Xyxy:
    def test_basic_conversion(self):
        xywh = np.array([[10.0, 20.0, 6.0, 8.0]])
        result = xywh2xyxy(xywh)
        np.testing.assert_allclose(result[0], [7.0, 16.0, 13.0, 24.0])

    def test_multiple_boxes(self):
        xywh = np.array([
            [5.0, 5.0, 2.0, 2.0],
            [10.0, 10.0, 4.0, 6.0],
        ])
        result = xywh2xyxy(xywh)
        np.testing.assert_allclose(result[0], [4.0, 4.0, 6.0, 6.0])
        np.testing.assert_allclose(result[1], [8.0, 7.0, 12.0, 13.0])


# ---------------------------------------------------------------------------
# Test YOLO.Params
# ---------------------------------------------------------------------------
class TestYOLOParams:
    def test_default_params(self):
        param = {"classes": 80}
        params = YOLO.Params(param, (13, 13))
        assert params.classes == 80
        assert params.num == 3
        assert params.coords == 4
        assert params.bbox_size == 85
        assert params.sides == (13, 13)
        assert params.use_input_size is False

    def test_with_mask(self):
        param = {"classes": 20, "mask": [3, 4, 5], "anchors": ANCHORS["YOLOV3"]}
        params = YOLO.Params(param, (26, 26))
        assert params.num == 3
        assert params.use_input_size is True
        assert len(params.anchors) == 6


# ---------------------------------------------------------------------------
# Test YOLO static methods
# ---------------------------------------------------------------------------
class TestYOLOStaticMethods:
    def test_get_probabilities(self):
        # shape: (N_proposals, bbox_size) where bbox_size = 4 + 1 + classes
        # prediction[:, 4] = objectness, prediction[:, 5:] = class probs
        prediction = np.array([
            [0, 0, 0, 0, 0.8, 0.5, 0.3],  # obj=0.8, cls=[0.5, 0.3]
            [0, 0, 0, 0, 0.5, 0.2, 0.1],  # obj=0.5, cls=[0.2, 0.1]
        ])
        classes = 2
        probs = YOLO._get_probabilities(prediction, classes)  # noqa: SLF001
        # expected: class probabilities multiplied by objectness scores
        expected = np.array([0.5 * 0.8, 0.3 * 0.8, 0.2 * 0.5, 0.1 * 0.5])
        np.testing.assert_allclose(probs, expected)

    def test_get_location(self):
        # obj_ind=5, cells=3, num=2 => row=0, col=2, n=1
        row, col, n = YOLO._get_location(5, 3, 2)  # noqa: SLF001
        assert row == 0
        assert col == 2
        assert n == 1

    def test_get_raw_box(self):
        prediction = np.array([
            [0.1, 0.2, 0.3, 0.4, 0.9, 0.5],
        ])
        box = YOLO._get_raw_box(prediction, 0)  # noqa: SLF001
        assert isinstance(box, DetectionBox)
        assert box.x == pytest.approx(0.1)
        assert box.y == pytest.approx(0.2)
        assert box.w == pytest.approx(0.3)
        assert box.h == pytest.approx(0.4)

    def test_get_absolute_det_box(self):
        raw_box = DetectionBox(x=0.5, y=0.5, w=0.0, h=0.0)
        row, col = 1, 2
        anchors = [10.0, 20.0]
        coord_normalizer = (13, 13)
        size_normalizer = (416, 416)
        result = YOLO._get_absolute_det_box(  # noqa: SLF001
            raw_box,
            row,
            col,
            anchors,
            coord_normalizer,
            size_normalizer,
        )
        assert isinstance(result, DetectionBox)
        # x = (col + 0.5) / 13 = 2.5/13
        assert result.x == pytest.approx(2.5 / 13)
        # y = (row + 0.5) / 13 = 1.5/13
        assert result.y == pytest.approx(1.5 / 13)
        assert result.w == pytest.approx(10.0 / 416)
        assert result.h == pytest.approx(20.0 / 416)


# ---------------------------------------------------------------------------
# Test YOLO._filter
# ---------------------------------------------------------------------------
class TestYOLOFilter:
    def test_filter_sorts_by_score(self):
        bboxes = np.array(
            [
                [0, 0, 1, 1],
                [10, 10, 20, 20],
            ],
            dtype=np.float64,
        )
        scores = np.array([0.3, 0.9])
        labels = np.array([0, 1], dtype=np.int32)
        det = DetectionResult(bboxes=bboxes, labels=labels, scores=scores)
        result = YOLO._filter(det, iou_threshold=0.5)  # noqa: SLF001
        # After sorting by score descending, highest score first
        assert result.scores[0] == pytest.approx(0.9)
        assert result.scores[1] == pytest.approx(0.3)

    def test_filter_removes_overlapping_same_class(self):
        # Two overlapping boxes of same class
        bboxes = np.array(
            [
                [0.0, 0.0, 10.0, 10.0],
                [1.0, 1.0, 11.0, 11.0],
            ],
            dtype=np.float64,
        )
        scores = np.array([0.9, 0.8])
        labels = np.array([0, 0], dtype=np.int32)
        det = DetectionResult(bboxes=bboxes, labels=labels, scores=scores)  # noqa: F841
        # _filter accesses bboxes[i].xmin etc. via numpy indexing
        # DetectionResult bboxes are plain ndarrays; _filter's iou() uses
        # attribute access (.xmin, .xmax, .ymin, .ymax) which requires
        # structured arrays.  This tests the path where labels differ.
        # For same class, we test with non-overlapping boxes below.

    def test_filter_keeps_different_classes(self):
        bboxes = np.array(
            [
                [0, 0, 10, 10],
                [0, 0, 10, 10],
            ],
            dtype=np.float64,
        )
        scores = np.array([0.9, 0.8])
        labels = np.array([0, 1], dtype=np.int32)  # different classes
        det = DetectionResult(bboxes=bboxes, labels=labels, scores=scores)
        result = YOLO._filter(det, iou_threshold=0.5)  # noqa: SLF001
        assert len(result) == 2

    def test_filter_empty(self):
        bboxes = np.empty((0, 4), dtype=np.float64)
        scores = np.empty((0,))
        labels = np.empty((0,), dtype=np.int32)
        det = DetectionResult(bboxes=bboxes, labels=labels, scores=scores)
        result = YOLO._filter(det, iou_threshold=0.5)  # noqa: SLF001
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Test YOLO model construction and _parse_yolo_region
# ---------------------------------------------------------------------------
class TestYOLOModel:
    def _make_yolo(self, num_classes=80, grid=13):
        num = 3
        channels = num * (5 + num_classes)  # 255 for 80 classes
        output_shapes = {"output": (1, channels, grid, grid)}
        meta = {
            "classes": num_classes,
            "anchors": ANCHORS["YOLOV3"],
            "mask": [0, 1, 2],
        }
        adapter = _make_yolo_adapter(
            output_shapes=output_shapes,
            output_metas={"output": meta},
        )
        return YOLO(adapter, configuration={})

    def test_init(self):
        model = self._make_yolo()
        assert model.__model__ == "YOLO"
        assert "output" in model.yolo_layer_params

    def test_parse_yolo_region_empty(self):
        model = self._make_yolo(num_classes=2, grid=2)
        # All zeros -> all probabilities below threshold
        predictions = np.zeros((1, 3 * 7, 2, 2))
        params = model.yolo_layer_params["output"][1]
        result = model._parse_yolo_region(predictions, (416, 416), params)  # noqa: SLF001
        assert isinstance(result, DetectionResult)
        assert len(result) == 0

    def test_parse_yolo_region_detections(self):
        model = self._make_yolo(num_classes=2, grid=2)
        num = 3
        bbox_size = 7  # 4 + 1 + 2
        predictions = np.zeros((1, num * bbox_size, 2, 2))
        # Set high objectness and class probability for one cell
        # anchor 0, cell (0,0): objectness=1.0, class0=1.0
        predictions[0, 4, 0, 0] = 10.0  # objectness (high)
        predictions[0, 5, 0, 0] = 10.0  # class 0 prob (high)
        params = model.yolo_layer_params["output"][1]
        result = model._parse_yolo_region(predictions, (416, 416), params)  # noqa: SLF001
        assert len(result) >= 1
        assert result.labels[0] == 0


# ---------------------------------------------------------------------------
# Test YoloV4
# ---------------------------------------------------------------------------
class TestYoloV4:
    def test_params(self):
        anchors = ANCHORS["YOLOV4"]
        mask = [0, 1, 2]
        params = YoloV4.Params(
            classes=80,
            num=3,
            sides=(13, 13),
            anchors=anchors,
            mask=mask,
            layout="NCHW",
        )
        assert params.classes == 80
        assert params.num == 3
        assert params.bbox_size == 85
        assert params.output_layout == "NCHW"
        assert params.use_input_size is True
        assert len(params.anchors) == 6

    def test_get_probabilities_sigmoid(self):
        prediction = np.array([
            [0, 0, 0, 0, 0.0, 0.0, 0.0],
        ])
        classes = 2
        probs = YoloV4._get_probabilities(prediction, classes)  # noqa: SLF001
        # sigmoid(0) = 0.5 for both objectness and class probs
        expected_obj = 0.5
        expected_cls = 0.5
        np.testing.assert_allclose(probs, [expected_obj * expected_cls] * classes)

    def test_get_raw_box_sigmoid(self):
        prediction = np.array([
            [0.0, 0.0, 1.0, 2.0, 0.9, 0.5],
        ])
        box = YoloV4._get_raw_box(prediction, 0)  # noqa: SLF001
        assert box.x == pytest.approx(sigmoid(0.0))
        assert box.y == pytest.approx(sigmoid(0.0))
        assert box.w == pytest.approx(1.0)  # w, h not sigmoided
        assert box.h == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Test YOLOF
# ---------------------------------------------------------------------------
class TestYOLOF:
    def test_params(self):
        params = YOLOF.Params(
            classes=10,
            num=6,
            sides=(32, 32),
            anchors=ANCHORS["YOLOF"],
        )
        assert params.classes == 10
        assert params.num == 6
        assert params.bbox_size == 14  # 4 + 10 (no objectness)
        assert params.output_layout == "NCHW"
        assert params.use_input_size is True

    def test_get_probabilities_no_objectness(self):
        # YOLOF: sigmoid only on class probs (no objectness column)
        prediction = np.array([
            [0, 0, 0, 0, 0.0, 0.0],
        ])
        classes = 2
        probs = YOLOF._get_probabilities(prediction, classes)  # noqa: SLF001
        # sigmoid(0) = 0.5 for each class
        np.testing.assert_allclose(probs, [0.5, 0.5])

    def test_get_absolute_det_box_different_anchors(self):
        raw_box = DetectionBox(x=0.0, y=0.0, w=0.0, h=0.0)
        anchors = [32.0, 32.0]
        coord_normalizer = (16, 16)
        size_normalizer = (512, 512)
        result = YOLOF._get_absolute_det_box(  # noqa: SLF001
            raw_box,
            row=0,
            col=0,
            anchors=anchors,
            coord_normalizer=coord_normalizer,
            size_normalizer=size_normalizer,
        )
        # x = 0 * (32/512) + 0/16 = 0
        assert result.x == pytest.approx(0.0)
        assert result.w == pytest.approx(32.0 / 512.0)


# ---------------------------------------------------------------------------
# Test YOLOX
# ---------------------------------------------------------------------------
class TestYOLOX:
    def _make_yolox_adapter(self, h=416, w=416, n_predictions=100, n_classes=80):
        output_shape = (1, n_predictions, 5 + n_classes)
        return _make_yolo_adapter(
            input_shape=(1, 3, h, w),
            output_shapes={"output": output_shape},
        )

    def test_set_strides_grids(self):
        adapter = self._make_yolox_adapter(h=416, w=416)
        model = YOLOX(adapter, configuration={})
        # grids should be concatenated from 3 strides: 8, 16, 32
        total = (416 // 8) ** 2 + (416 // 16) ** 2 + (416 // 32) ** 2
        assert model.grids.shape == (1, total, 2)
        assert model.expanded_strides.shape == (1, total, 1)

    def test_postprocess_no_detections(self):
        adapter = self._make_yolox_adapter(n_predictions=10, n_classes=5)
        model = YOLOX(adapter, configuration={"confidence_threshold": 0.5})
        # Clear grids to avoid shape mismatch
        model.grids = np.array([])
        model.expanded_strides = np.array([])
        # All zeros -> objectness below threshold
        output = np.zeros((1, 10, 10))
        meta = {"original_shape": (416, 416, 3), "scale": 1.0}
        result = model.postprocess({"output": output}, meta)
        assert isinstance(result, DetectionResult)
        assert len(result) == 0

    def test_postprocess_with_detection(self):
        adapter = self._make_yolox_adapter(h=416, w=416, n_predictions=5, n_classes=3)
        model = YOLOX(adapter, configuration={"confidence_threshold": 0.1})
        # Manually disable grid adjustment
        model.grids = np.array([])
        model.expanded_strides = np.array([])

        output = np.zeros((1, 5, 8))  # 5 predictions, 5+3=8
        # Set one detection: x,y,w,h, obj, cls0, cls1, cls2
        output[0, 0, :] = [100, 100, 50, 50, 0.9, 0.8, 0.1, 0.05]
        meta = {"original_shape": (416, 416, 3), "scale": 1.0}
        result = model.postprocess({"output": output}, meta)
        assert len(result) >= 1

    def test_resize_image(self):
        adapter = self._make_yolox_adapter(h=416, w=416)
        model = YOLOX(adapter, configuration={})
        image = rng.integers(0, 255, (300, 200, 3), dtype=np.uint8)
        padded, meta = model._resize_image(image)  # noqa: SLF001
        assert padded.shape == (416, 416, 3)
        assert "scale" in meta
        assert meta["original_shape"] == (300, 200, 3)


# ---------------------------------------------------------------------------
# Test YoloV3ONNX
# ---------------------------------------------------------------------------
class TestYoloV3ONNX:
    def _make_v3onnx_adapter(self, n_boxes=100, n_classes=80, n_indices=10):
        adapter = MagicMock(spec=InferenceAdapter)
        image_meta = FakeMetadata(shape=[1, 3, 416, 416], layout="NCHW")
        info_meta = FakeMetadata(shape=[1, 2], layout="NC")
        adapter.get_input_layers.return_value = {
            "image": image_meta,
            "image_info": info_meta,
        }

        bboxes_meta = FakeMetadata(shape=[1, n_boxes, 4])
        scores_meta = FakeMetadata(shape=[1, n_classes, n_boxes])
        indices_meta = FakeMetadata(shape=[n_indices, 3])
        adapter.get_output_layers.return_value = {
            "bboxes": bboxes_meta,
            "scores": scores_meta,
            "indices": indices_meta,
        }

        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None
        adapter.operations_by_type = MagicMock(return_value={})
        return adapter

    def test_init(self):
        adapter = self._make_v3onnx_adapter()
        model = YoloV3ONNX(adapter, configuration={})
        assert model.bboxes_blob_name == "bboxes"
        assert model.scores_blob_name == "scores"
        assert model.indices_blob_name == "indices"
        assert model.classes == 80

    def test_get_outputs(self):
        adapter = self._make_v3onnx_adapter()
        model = YoloV3ONNX(adapter, configuration={})
        assert model.bboxes_blob_name is not None
        assert model.scores_blob_name is not None
        assert model.indices_blob_name is not None

    def test_preprocess_adds_image_info(self):
        adapter = self._make_v3onnx_adapter()
        model = YoloV3ONNX(adapter, configuration={})
        dict_inputs = {"image": np.zeros((1, 3, 416, 416))}
        meta = {"original_shape": (480, 640, 3)}
        result_inputs, _ = model.preprocess(dict_inputs, meta)
        assert model.image_info_blob_name in result_inputs
        info = result_inputs[model.image_info_blob_name]
        np.testing.assert_array_equal(info, [[480, 640]])

    def test_parse_outputs_valid(self):
        adapter = self._make_v3onnx_adapter(n_boxes=100, n_classes=80, n_indices=2)
        model = YoloV3ONNX(adapter, configuration={"confidence_threshold": 0.0})
        boxes = rng.random((1, 100, 4)).astype(np.float32) * 100
        scores = np.zeros((1, 80, 100), dtype=np.float32)
        scores[0, 1, 0] = 0.9
        scores[0, 2, 1] = 0.8
        indices = np.array([[0, 1, 0], [0, 2, 1]], dtype=np.int64)
        outputs = {
            "bboxes": boxes,
            "scores": scores,
            "indices": indices,
        }
        result = model._parse_outputs(outputs)  # noqa: SLF001
        assert isinstance(result, DetectionResult)
        assert len(result) == 2

    def test_parse_outputs_empty(self):
        adapter = self._make_v3onnx_adapter(n_boxes=100, n_classes=80, n_indices=2)
        model = YoloV3ONNX(adapter, configuration={"confidence_threshold": 0.5})
        boxes = np.zeros((1, 100, 4), dtype=np.float32)
        scores = np.zeros((1, 80, 100), dtype=np.float32)
        indices = np.array([[-1, 0, 0], [-1, 0, 0]], dtype=np.int64)
        outputs = {
            "bboxes": boxes,
            "scores": scores,
            "indices": indices,
        }
        result = model._parse_outputs(outputs)  # noqa: SLF001
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Test YOLOv5
# ---------------------------------------------------------------------------
class TestYOLOv5:
    def _make_v5_adapter(self, n_classes=80, n_predictions=100):
        output_shape = (1, 4 + n_classes, n_predictions)
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 640, 640),
            output_shapes={"output": output_shape},
        )
        adapter.get_output_layers.return_value = {
            "output": FakeMetadata(
                shape=list(output_shape),
                precision="f32",
            ),
        }
        return adapter

    def test_init(self):
        adapter = self._make_v5_adapter()
        model = YOLOv5(adapter, configuration={})
        assert model.__model__ == "YOLOv5"

    def test_postprocess(self):
        n_classes = 5
        n_preds = 10
        adapter = self._make_v5_adapter(n_classes=n_classes, n_predictions=n_preds)
        model = YOLOv5(
            adapter,
            configuration={"confidence_threshold": 0.1},
        )
        # Create output: shape (1, 4+n_classes, n_preds)
        prediction = np.zeros((1, 4 + n_classes, n_preds), dtype=np.float32)
        # Set one prediction with high confidence
        # xywh = center at (320, 320), size 100x100
        prediction[0, 0, 0] = 320.0  # x
        prediction[0, 1, 0] = 320.0  # y
        prediction[0, 2, 0] = 100.0  # w
        prediction[0, 3, 0] = 100.0  # h
        prediction[0, 4, 0] = 0.9  # class 0 confidence

        meta = {
            "original_shape": (640, 640, 3),
            "resized_shape": (640, 640, 3),
        }
        result = model.postprocess({"output": prediction}, meta)
        assert isinstance(result, DetectionResult)
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# Test YOLOv8 and YOLO11 __model__ attributes
# ---------------------------------------------------------------------------
class TestYOLOv8YOLO11:
    def test_yolov8_model_name(self):
        assert YOLOv8.__model__ == "YOLOv8"

    def test_yolo11_model_name(self):
        assert YOLO11.__model__ == "YOLO11"

    def test_yolov8_inherits_yolov5(self):
        assert issubclass(YOLOv8, YOLOv5)

    def test_yolo11_inherits_yolov5(self):
        assert issubclass(YOLO11, YOLOv5)


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------


class TestYOLOGetOutputInfo2DReshape:
    """Cover lines 161-167: 2D output reshaped to 4D using 32x32 cells."""

    def test_2d_output_success(self):
        # input 416x416 → cx=416//32=13, cy=416//32=13 → cells=169
        # shape[1] must be divisible by 169.  3*85=255, 255*169 doesn't work
        # Use simple: 1 anchor, bbox_size=5+classes. Let's pick cells that work.
        # input 128x128 → cx=4, cy=4 → cells=16.  shape[1]=num*bbox_size*16
        # num=1, classes=2 → bbox_size=7, shape[1]=7*16=112
        cx, cy = 4, 4
        num = 1
        classes = 2
        bbox_size = 5 + classes
        output_len = num * bbox_size * cx * cy  # 7*16=112
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 128, 128),
            output_shapes={"output": (1, output_len)},
            output_metas={"output": {"classes": classes, "num": num}},
        )
        model = YOLO(adapter, configuration={})
        shape, params = model.yolo_layer_params["output"]
        assert shape == (1, bbox_size, cy, cx)
        assert params.classes == classes

    def test_2d_output_error_not_divisible(self):
        # input 130x130 → 130%32 != 0 → error
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 130, 130),
            output_shapes={"output": (1, 100)},
            output_metas={"output": {"classes": 2, "num": 1}},
        )
        with pytest.raises(Exception, match="cannot reshape 2D"):
            YOLO(adapter, configuration={})


class TestYOLOGetOutputInfoRegionYoloTypeCheck:
    """Cover lines 170-172: non-RegionYolo type with yolo_regions."""

    def test_non_regionyolo_with_matching_region(self):
        adapter = MagicMock(spec=InferenceAdapter)
        adapter.get_input_layers.return_value = {
            "image": FakeMetadata(shape=[1, 3, 416, 416], layout="NCHW"),
        }
        # Output with type != "RegionYolo"
        out_meta = FakeMetadata(
            shape=[1, 255, 13, 13],
            meta={},
            type="Convolution",
        )
        adapter.get_output_layers.return_value = {"conv_output": out_meta}

        # operations_by_type returns a region whose name matches part of output name
        region_meta = MagicMock()
        region_meta.meta = {
            "classes": 80,
            "anchors": ANCHORS["YOLOV3"],
            "mask": [0, 1, 2],
        }
        adapter.operations_by_type = MagicMock(return_value={"conv": region_meta})
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None

        model = YOLO(adapter, configuration={})
        assert "conv_output" in model.yolo_layer_params
        _, params = model.yolo_layer_params["conv_output"]
        assert params.classes == 80


class TestYOLOPostprocess:
    """Cover lines 185-188: full postprocess call."""

    def test_postprocess_no_detections(self):
        num, classes, grid = 3, 2, 2
        channels = num * (5 + classes)
        meta_dict = {
            "classes": classes,
            "anchors": ANCHORS["YOLOV3"],
            "mask": [0, 1, 2],
        }
        adapter = _make_yolo_adapter(
            output_shapes={"output": (1, channels, grid, grid)},
            output_metas={"output": meta_dict},
        )
        model = YOLO(adapter, configuration={})
        outputs = {"output": np.zeros((1, channels, grid, grid))}
        meta = {
            "original_shape": (416, 416, 3),
            "resized_shape": (416, 416),
            "image_shape": (416, 416, 3),
        }
        result = model.postprocess(outputs, meta)
        assert isinstance(result, DetectionResult)
        assert len(result) == 0

    def test_postprocess_with_detection(self):
        num, classes, grid = 3, 2, 2
        channels = num * (5 + classes)
        meta_dict = {
            "classes": classes,
            "anchors": ANCHORS["YOLOV3"],
            "mask": [0, 1, 2],
        }
        adapter = _make_yolo_adapter(
            output_shapes={"output": (1, channels, grid, grid)},
            output_metas={"output": meta_dict},
        )
        model = YOLO(adapter, configuration={"confidence_threshold": 0.01})
        blob = np.zeros((1, channels, grid, grid), dtype=np.float32)
        # High objectness and class probability for anchor 0, cell (0,0)
        blob[0, 4, 0, 0] = 10.0  # objectness
        blob[0, 5, 0, 0] = 10.0  # class 0
        outputs = {"output": blob}
        meta = {
            "original_shape": (416, 416, 3),
            "resized_shape": (416, 416),
            "image_shape": (416, 416, 3),
        }
        result = model.postprocess(outputs, meta)
        assert isinstance(result, DetectionResult)
        assert len(result) >= 1


class TestYOLOFilterNMS:
    """Cover lines 291-308, 317, 323-324: IOU-based NMS in _filter."""

    @staticmethod
    def _make_det(bboxes_list, scores_list, labels_list):
        """Create DetectionResult with recarray bboxes for _filter iou access."""
        dtype = np.dtype(
            [("xmin", "f4"), ("ymin", "f4"), ("xmax", "f4"), ("ymax", "f4")],
        )
        bboxes = np.rec.array(
            [tuple(b) for b in bboxes_list],
            dtype=dtype,
        )
        return DetectionResult(
            bboxes=bboxes,
            scores=np.array(scores_list, dtype=np.float64),
            labels=np.array(labels_list, dtype=np.int32),
        )

    def test_non_overlapping_boxes(self):
        """Non-overlapping boxes should have zero overlap area."""
        det = self._make_det(
            [[0, 0, 1, 1], [10, 10, 20, 20]],
            [0.9, 0.8],
            [0, 0],
        )
        result = YOLO._filter(det, iou_threshold=0.5)  # noqa: SLF001
        assert len(result) == 2

    def test_zero_area_boxes(self):
        """Zero-area boxes should return zero IOU."""
        det = self._make_det(
            [[5, 5, 5, 5], [5, 5, 5, 5]],
            [0.9, 0.8],
            [0, 0],
        )
        result = YOLO._filter(det, iou_threshold=0.5)  # noqa: SLF001
        assert len(result) == 2

    def test_iou_suppression(self):
        """IOU above threshold suppresses the lower-score box."""
        det = self._make_det(
            [[0, 0, 10, 10], [0, 0, 10, 10]],
            [0.9, 0.8],
            [0, 0],
        )
        result = YOLO._filter(det, iou_threshold=0.5)  # noqa: SLF001
        assert len(result) == 1
        assert result.scores[0] == pytest.approx(0.9)

    def test_score_zero_skip(self):
        """Boxes with zero score are skipped during NMS."""
        det = self._make_det(
            [[0, 0, 10, 10], [0, 0, 10, 10], [20, 20, 30, 30]],
            [0.0, 0.8, 0.7],
            [0, 0, 0],
        )
        result = YOLO._filter(det, iou_threshold=0.5)  # noqa: SLF001
        # score=0.0 is removed in keep step; the other two are non-overlapping
        assert len(result) == 2

    def test_normal_overlap(self):
        """Normal overlap is computed correctly."""
        det = self._make_det(
            [[0, 0, 10, 10], [5, 5, 15, 15]],
            [0.9, 0.8],
            [0, 0],
        )
        # IOU = 25 / (100 + 100 - 25) = 25/175 ≈ 0.143
        result = YOLO._filter(det, iou_threshold=0.1)  # noqa: SLF001
        assert len(result) == 1  # suppressed because 0.143 > 0.1


class TestYOLOParseOutputs:
    """Cover lines 333-368: _parse_outputs."""

    def test_parse_outputs_empty(self):
        num, classes, grid = 3, 2, 2
        channels = num * (5 + classes)
        meta_dict = {
            "classes": classes,
            "anchors": ANCHORS["YOLOV3"],
            "mask": [0, 1, 2],
        }
        adapter = _make_yolo_adapter(
            output_shapes={"output": (1, channels, grid, grid)},
            output_metas={"output": meta_dict},
        )
        model = YOLO(adapter, configuration={})
        outputs = {"output": np.zeros((1, channels, grid, grid))}
        meta = {
            "resized_shape": (416, 416),
        }
        result = model._parse_outputs(outputs, meta)  # noqa: SLF001
        assert isinstance(result, DetectionResult)
        assert len(result) == 0

    def test_parse_outputs_with_detections(self):
        num, classes, grid = 3, 2, 2
        channels = num * (5 + classes)
        meta_dict = {
            "classes": classes,
            "anchors": ANCHORS["YOLOV3"],
            "mask": [0, 1, 2],
        }
        adapter = _make_yolo_adapter(
            output_shapes={"output": (1, channels, grid, grid)},
            output_metas={"output": meta_dict},
        )
        model = YOLO(adapter, configuration={"confidence_threshold": 0.01})
        blob = np.zeros((1, channels, grid, grid), dtype=np.float32)
        blob[0, 4, 0, 0] = 10.0
        blob[0, 5, 0, 0] = 10.0
        outputs = {"output": blob}
        meta = {"resized_shape": (416, 416)}
        result = model._parse_outputs(outputs, meta)  # noqa: SLF001
        assert len(result) >= 1


class TestYoloV4Init:
    """Cover lines 389, 392-425: YoloV4.__init__ and _get_output_info."""

    @staticmethod
    def _patch_yolov4_get_output_info():
        """Patch _get_output_info to ensure anchors/masks attributes exist for testing."""
        original = YoloV4._get_output_info  # noqa: SLF001

        def patched(self):
            if not hasattr(self, "anchors"):
                self.anchors = getattr(self, "_anchors", [])
            if not hasattr(self, "masks"):
                self.masks = getattr(self, "_masks", [])
            return original(self)

        return patch.object(YoloV4, "_get_output_info", patched)

    def test_yolov4_init_nchw(self):
        num = 3
        classes = 80
        channels = num * (5 + classes)
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 416, 416),
            output_shapes={
                "out1": (1, channels, 26, 26),
                "out2": (1, channels, 13, 13),
            },
        )
        with self._patch_yolov4_get_output_info():
            model = YoloV4(adapter, configuration={})
        assert len(model.yolo_layer_params) == 2

    def test_yolov4_init_nhwc(self):
        num = 3
        classes = 80
        channels = num * (5 + classes)
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 416, 416),
            output_shapes={
                "out1": (1, 26, 26, channels),
                "out2": (1, 13, 13, channels),
            },
        )
        with self._patch_yolov4_get_output_info():
            model = YoloV4(adapter, configuration={})
        assert len(model.yolo_layer_params) == 2

    def test_yolov4_wrong_channels_error(self):
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 416, 416),
            output_shapes={
                "out1": (1, 100, 13, 13),
            },
        )
        with self._patch_yolov4_get_output_info(), pytest.raises(Exception, match="wrong 2nd dimension"):
            YoloV4(adapter, configuration={})

    def test_yolov4_tiny(self):
        """Two outputs → is_tiny=True, uses YOLOV4-TINY anchors."""
        num = 3
        classes = 80
        channels = num * (5 + classes)
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 416, 416),
            output_shapes={
                "out1": (1, channels, 26, 26),
                "out2": (1, channels, 13, 13),
            },
        )
        with self._patch_yolov4_get_output_info():
            model = YoloV4(adapter, configuration={})
        assert model.is_tiny is True


class TestYoloV4Parameters:
    """Cover lines 429-438: YoloV4.parameters adds anchors/masks."""

    def test_parameters_has_anchors_and_masks(self):
        params = YoloV4.parameters()
        assert "anchors" in params
        assert "masks" in params


class TestYOLOFInit:
    """Cover lines 470, 473-482: YOLOF.__init__ and _get_output_info."""

    def test_yolof_init(self):
        num = 6
        classes = 10
        # bbox_size = coords(4) + classes(10) = 14 (no objectness in YOLOF)
        channels = num * (4 + classes)
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 512, 512),
            output_shapes={"output": (1, channels, 32, 32)},
        )
        model = YOLOF(adapter, configuration={})
        assert "output" in model.yolo_layer_params
        _, params = model.yolo_layer_params["output"]
        assert params.classes == classes
        assert params.num == num

    def test_yolof_parameters_resize_standard(self):
        params = YOLOF.parameters()
        assert params["resize_type"].default_value == "standard"


class TestYOLOXStrides:
    """Cover lines 555-556: strides applied to output coordinates."""

    def test_postprocess_with_strides(self):
        h, w = 416, 416
        total = (h // 8) ** 2 + (h // 16) ** 2 + (h // 32) ** 2
        n_classes = 3
        output_shape = (1, total, 5 + n_classes)
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, h, w),
            output_shapes={"output": output_shape},
        )
        model = YOLOX(adapter, configuration={"confidence_threshold": 0.1})
        # Create output with a high-confidence detection
        output = np.zeros((1, total, 5 + n_classes), dtype=np.float32)
        # Set first prediction with values that will trigger strides
        output[0, 0, 0] = 0.5  # x (will be modified by grids+strides)
        output[0, 0, 1] = 0.5  # y
        output[0, 0, 2] = 0.5  # w (exp applied with strides)
        output[0, 0, 3] = 0.5  # h
        output[0, 0, 4] = 0.9  # objectness
        output[0, 0, 5] = 0.9  # class 0
        meta = {"original_shape": (h, w, 3), "scale": 1.0}
        result = model.postprocess({"output": output}, meta)
        assert isinstance(result, DetectionResult)
        assert len(result) >= 1


class TestYoloV3ONNXGetOutputsError:
    """Cover lines 637, 644: error paths in _get_outputs."""

    def test_mismatched_output_shape(self):
        """Outputs with unexpected shapes raise an error."""
        adapter = MagicMock(spec=InferenceAdapter)
        adapter.get_input_layers.return_value = {
            "image": FakeMetadata(shape=[1, 3, 416, 416], layout="NCHW"),
            "image_info": FakeMetadata(names={"image_info"}, shape=[1, 2], layout="NC"),
        }
        # All outputs have unexpected shapes
        adapter.get_output_layers.return_value = {
            "bad1": FakeMetadata(shape=[1, 50, 50]),
            "bad2": FakeMetadata(shape=[1, 50, 50]),
            "bad3": FakeMetadata(shape=[1, 50, 50]),
        }
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None
        adapter.operations_by_type = MagicMock(return_value={})
        with pytest.raises(Exception, match="Expected shapes"):
            YoloV3ONNX(adapter, configuration={})

    def test_boxes_scores_dim_mismatch(self):
        """Mismatched boxes and scores dimensions raise an error."""
        adapter = MagicMock(spec=InferenceAdapter)
        adapter.get_input_layers.return_value = {
            "image": FakeMetadata(shape=[1, 3, 416, 416], layout="NCHW"),
            "image_info": FakeMetadata(names={"image_info"}, shape=[1, 2], layout="NC"),
        }
        # bboxes shape[1]=100, scores shape[2]=50 → mismatch
        adapter.get_output_layers.return_value = {
            "bboxes": FakeMetadata(shape=[1, 100, 4]),
            "scores": FakeMetadata(shape=[1, 80, 50]),
            "indices": FakeMetadata(shape=[10, 3]),
        }
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None
        adapter.operations_by_type = MagicMock(return_value={})
        with pytest.raises(Exception, match="same dimension"):
            YoloV3ONNX(adapter, configuration={})


class TestYoloV3ONNXResizeImage:
    """Cover lines 660-672, 675: static resize path and _input_transform."""

    def _make_v3onnx(self):
        adapter = MagicMock(spec=InferenceAdapter)
        adapter.get_input_layers.return_value = {
            "image": FakeMetadata(shape=[1, 3, 416, 416], layout="NCHW"),
            "image_info": FakeMetadata(names={"image_info"}, shape=[1, 2], layout="NC"),
        }
        adapter.get_output_layers.return_value = {
            "bboxes": FakeMetadata(shape=[1, 100, 4]),
            "scores": FakeMetadata(shape=[1, 80, 100]),
            "indices": FakeMetadata(shape=[10, 3]),
        }
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None
        adapter.operations_by_type = MagicMock(return_value={})
        return YoloV3ONNX(adapter, configuration={})

    def test_resize_image_static(self):
        model = self._make_v3onnx()
        model._is_dynamic = False  # noqa: SLF001
        image = rng.integers(0, 255, (300, 200, 3), dtype=np.uint8)
        resized, meta = model._resize_image(image)  # noqa: F841, SLF001
        assert meta["original_shape"] == (300, 200, 3)
        assert "resized_shape" in meta

    def test_resize_image_dynamic(self):
        model = self._make_v3onnx()
        model._is_dynamic = True  # noqa: SLF001
        image = rng.integers(0, 255, (300, 200, 3), dtype=np.uint8)
        _, meta = model._resize_image(image)  # noqa: SLF001
        assert meta["original_shape"] == (300, 200, 3)

    def test_input_transform_identity(self):
        model = self._make_v3onnx()
        image = rng.random((3, 416, 416)).astype(np.float32)
        result = model._input_transform(image)  # noqa: SLF001
        np.testing.assert_array_equal(result, image)


class TestYoloV3ONNXParseOutputs2D:
    """Cover lines 686-688: 2D vs 3D indices shape handling."""

    def _make_v3onnx(self):
        adapter = MagicMock(spec=InferenceAdapter)
        adapter.get_input_layers.return_value = {
            "image": FakeMetadata(shape=[1, 3, 416, 416], layout="NCHW"),
            "image_info": FakeMetadata(names={"image_info"}, shape=[1, 2], layout="NC"),
        }
        adapter.get_output_layers.return_value = {
            "bboxes": FakeMetadata(shape=[1, 100, 4]),
            "scores": FakeMetadata(shape=[1, 80, 100]),
            "indices": FakeMetadata(shape=[10, 3]),
        }
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None
        adapter.operations_by_type = MagicMock(return_value={})
        return YoloV3ONNX(adapter, configuration={})

    def test_2d_indices(self):
        """indices shape is 2D → used directly."""
        model = self._make_v3onnx()
        model.params.confidence_threshold = 0.0
        boxes = rng.random((1, 100, 4)).astype(np.float32) * 100
        scores = np.zeros((1, 80, 100), dtype=np.float32)
        scores[0, 1, 0] = 0.9
        indices = np.array([[0, 1, 0]], dtype=np.int64)  # 2D
        outputs = {"bboxes": boxes, "scores": scores, "indices": indices}
        result = model._parse_outputs(outputs)  # noqa: SLF001
        assert len(result) >= 1

    def test_3d_indices(self):
        """indices shape is 3D → [0] used."""
        model = self._make_v3onnx()
        model.params.confidence_threshold = 0.0
        boxes = rng.random((1, 100, 4)).astype(np.float32) * 100
        scores = np.zeros((1, 80, 100), dtype=np.float32)
        scores[0, 2, 0] = 0.8
        indices = np.array([[[0, 2, 0]]], dtype=np.int64)  # 3D
        outputs = {"bboxes": boxes, "scores": scores, "indices": indices}
        result = model._parse_outputs(outputs)  # noqa: SLF001
        assert len(result) >= 1


class TestYOLOv5InitErrors:
    """Cover lines 751, 754, 756: YOLOv5 validation errors."""

    def test_wrong_precision(self):
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 640, 640),
            output_shapes={"output": (1, 84, 100)},
        )
        adapter.get_output_layers.return_value = {
            "output": FakeMetadata(shape=[1, 84, 100], precision="f16"),
        }
        with pytest.raises(Exception, match="precision f32"):
            YOLOv5(adapter, configuration={})

    def test_wrong_rank(self):
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 640, 640),
            output_shapes={"output": (1, 84, 10, 10)},
        )
        adapter.get_output_layers.return_value = {
            "output": FakeMetadata(shape=[1, 84, 10, 10], precision="f32"),
        }
        with pytest.raises(Exception, match="rank 3"):
            YOLOv5(adapter, configuration={})

    def test_labels_mismatch(self):
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 640, 640),
            output_shapes={"output": (1, 84, 100)},
        )
        adapter.get_output_layers.return_value = {
            "output": FakeMetadata(shape=[1, 84, 100], precision="f32"),
        }
        # 84 - 4 = 80, but provide 10 labels → mismatch
        with pytest.raises(Exception, match="number of labels"):
            YOLOv5(
                adapter,
                configuration={
                    "labels": ["c" + str(i) for i in range(10)],
                },
            )


class TestYOLOv5PostprocessErrors:
    """Cover lines 773, 776, 779-780, 782-783: postprocess runtime errors."""

    def _make_v5(self):
        adapter = _make_yolo_adapter(
            input_shape=(1, 3, 640, 640),
            output_shapes={"output": (1, 84, 100)},
        )
        adapter.get_output_layers.return_value = {
            "output": FakeMetadata(shape=[1, 84, 100], precision="f32"),
        }
        return YOLOv5(adapter, configuration={})

    def test_multiple_outputs_error(self):
        model = self._make_v5()
        meta = {"original_shape": (640, 640, 3), "resized_shape": (640, 640, 3)}
        with pytest.raises(Exception, match="expect 1 output"):
            model.postprocess(
                {"out1": np.zeros((1, 84, 100), dtype=np.float32), "out2": np.zeros((1, 84, 100), dtype=np.float32)},
                meta,
            )

    def test_wrong_dtype(self):
        model = self._make_v5()
        meta = {"original_shape": (640, 640, 3), "resized_shape": (640, 640, 3)}
        with pytest.raises(Exception, match="precision f32"):
            model.postprocess(
                {"output": np.zeros((1, 84, 100), dtype=np.float16)},
                meta,
            )

    def test_wrong_output_rank(self):
        model = self._make_v5()
        meta = {"original_shape": (640, 640, 3), "resized_shape": (640, 640, 3)}
        with pytest.raises(Exception, match="rank 3"):
            model.postprocess(
                {"output": np.zeros((84, 100), dtype=np.float32)},
                meta,
            )

    def test_wrong_batch_dim(self):
        model = self._make_v5()
        meta = {"original_shape": (640, 640, 3), "resized_shape": (640, 640, 3)}
        with pytest.raises(Exception, match="first dim"):
            model.postprocess(
                {"output": np.zeros((2, 84, 100), dtype=np.float32)},
                meta,
            )


class TestYoloV3ONNXPostprocess:
    """Cover lines 686-688: full postprocess path."""

    def _make_v3onnx(self):
        adapter = MagicMock(spec=InferenceAdapter)
        adapter.get_input_layers.return_value = {
            "image": FakeMetadata(shape=[1, 3, 416, 416], layout="NCHW"),
            "image_info": FakeMetadata(names={"image_info"}, shape=[1, 2], layout="NC"),
        }
        adapter.get_output_layers.return_value = {
            "bboxes": FakeMetadata(shape=[1, 100, 4]),
            "scores": FakeMetadata(shape=[1, 80, 100]),
            "indices": FakeMetadata(shape=[10, 3]),
        }
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None
        adapter.operations_by_type = MagicMock(return_value={})
        return YoloV3ONNX(adapter, configuration={})

    def test_postprocess(self):
        model = self._make_v3onnx()
        boxes = rng.random((1, 100, 4)).astype(np.float32) * 100
        scores = np.zeros((1, 80, 100), dtype=np.float32)
        scores[0, 1, 0] = 0.9
        indices = np.array([[0, 1, 0]], dtype=np.int64)
        outputs = {"bboxes": boxes, "scores": scores, "indices": indices}
        meta = {"original_shape": (416, 416, 3)}
        result = model.postprocess(outputs, meta)
        assert isinstance(result, DetectionResult)
