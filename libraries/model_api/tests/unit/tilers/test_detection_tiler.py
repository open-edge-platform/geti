# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

import numpy as np
from model_api.models import DetectionResult
from model_api.tilers.detection import DetectionTiler, _non_linear_normalization


def _make_model():
    model = MagicMock()
    model.load = MagicMock()
    model.inference_adapter = MagicMock()
    model.inference_adapter.get_rt_info.side_effect = RuntimeError(
        "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
    )
    model.get_label_name = MagicMock(side_effect=lambda x: f"label_{x}")
    return model


def _make_detection_result(n=2, offset=(0, 0)):
    bboxes = np.array([[10 + offset[0], 20 + offset[1], 50 + offset[0], 60 + offset[1]]] * n, dtype=np.float32)
    labels = np.array([0] * n, dtype=np.int32)
    scores = np.array([0.9] * n, dtype=np.float32)
    return DetectionResult(
        bboxes=bboxes,
        labels=labels,
        scores=scores,
        saliency_map=np.zeros((1,), dtype=np.float32),
        feature_vector=np.zeros((1,), dtype=np.float32),
    )


class TestDetectionTilerInit:
    def test_init(self):
        model = _make_model()
        tiler = DetectionTiler(model, execution_mode="sync")
        assert tiler.max_pred_number == 100
        assert tiler.iou_threshold == 0.45

    def test_parameters_includes_detection_params(self):
        params = DetectionTiler.parameters()
        assert "max_pred_number" in params
        assert "iou_threshold" in params
        assert "tile_size" in params


class TestDetectionTilerPostprocessTile:
    def test_postprocess_tile_async(self):
        model = _make_model()
        tiler = DetectionTiler(model, execution_mode="async")
        pred = _make_detection_result(n=1)
        coord = [10, 20, 110, 120]
        result = tiler._postprocess_tile(pred, coord)  # noqa: SLF001
        assert "bboxes" in result
        assert "saliency_map" in result
        assert "features" in result
        assert "coords" in result
        assert result["coords"] == coord
        # bbox should have offset applied
        assert result["bboxes"].shape[1] == 6

    def test_postprocess_tile_sync_copies_maps(self):
        model = _make_model()
        tiler = DetectionTiler(model, execution_mode="sync")
        pred = _make_detection_result(n=1)
        coord = [0, 0, 100, 100]
        result = tiler._postprocess_tile(pred, coord)  # noqa: SLF001
        assert "saliency_map" in result


class TestDetectionTilerMergeResults:
    @patch("model_api.tilers.detection.multiclass_nms")
    def test_merge_results_with_detections(self, mock_nms):
        model = _make_model()
        tiler = DetectionTiler(model, execution_mode="sync")
        mock_nms.return_value = np.array([0])

        results = [
            {
                "bboxes": np.array([[0, 0.9, 10, 20, 50, 60]], dtype=np.float32),
                "features": np.array([1.0]),
                "saliency_map": np.zeros((1,)),
                "coords": [0, 0, 100, 100],
            },
        ]
        merged = tiler._merge_results(results, (100, 100, 3))  # noqa: SLF001
        assert isinstance(merged, DetectionResult)
        mock_nms.assert_called_once()

    def test_merge_results_empty_detections(self):
        model = _make_model()
        tiler = DetectionTiler(model, execution_mode="sync")
        results = [
            {
                "bboxes": np.empty((0, 6), dtype=np.float32),
                "features": np.array([1.0]),
                "saliency_map": np.zeros((1,)),
                "coords": [0, 0, 100, 100],
            },
        ]
        merged = tiler._merge_results(results, (100, 100, 3))  # noqa: SLF001
        assert isinstance(merged, DetectionResult)
        assert len(merged.bboxes) == 0

    @patch("model_api.tilers.detection.multiclass_nms")
    def test_merge_results_multiple_tiles(self, mock_nms):
        model = _make_model()
        tiler = DetectionTiler(model, execution_mode="sync")
        mock_nms.return_value = np.array([0, 1])

        results = [
            {
                "bboxes": np.array([[0, 0.9, 10, 20, 50, 60]], dtype=np.float32),
                "features": np.array([1.0]),
                "saliency_map": np.zeros((1,)),
                "coords": [0, 0, 100, 100],
            },
            {
                "bboxes": np.array([[1, 0.8, 110, 120, 150, 160]], dtype=np.float32),
                "features": np.array([2.0]),
                "saliency_map": np.zeros((1,)),
                "coords": [100, 100, 200, 200],
            },
        ]
        merged = tiler._merge_results(results, (200, 200, 3))  # noqa: SLF001
        assert isinstance(merged, DetectionResult)


class TestDetectionTilerMergeSaliencyMaps:
    def test_merge_saliency_maps_empty(self):
        model = _make_model()
        tiler = DetectionTiler(model, execution_mode="sync")
        assert tiler._merge_saliency_maps([], (100, 100, 3), []) is None  # noqa: SLF001

    def test_merge_saliency_maps_1d(self):
        model = _make_model()
        tiler = DetectionTiler(model, execution_mode="sync")
        smap = np.array([1.0])
        result = tiler._merge_saliency_maps([smap], (100, 100, 3), [[0, 0, 100, 100]])  # noqa: SLF001
        np.testing.assert_array_equal(result, smap)

    def test_merge_saliency_maps_single_map(self):
        model = _make_model()
        tiler = DetectionTiler(model, execution_mode="sync")
        smap = np.ones((2, 10, 10), dtype=np.float32)
        result = tiler._merge_saliency_maps([smap], (100, 100, 3), [[0, 0, 100, 100]])  # noqa: SLF001
        np.testing.assert_array_equal(result, smap)

    def test_merge_saliency_maps_4d(self):
        model = _make_model()
        tiler = DetectionTiler(
            model,
            configuration={"tile_size": 50, "tile_with_full_img": True},
            execution_mode="sync",
        )
        smap_full = np.ones((1, 2, 5, 5), dtype=np.float32) * 100
        smap_tile = np.ones((1, 2, 5, 5), dtype=np.float32) * 50
        coords = [[0, 0, 100, 100], [0, 0, 50, 50]]
        result = tiler._merge_saliency_maps([smap_full, smap_tile], (100, 100, 3), coords)  # noqa: SLF001
        assert result.shape[0] == 1  # recovered 4d

    def test_merge_saliency_maps_multiple_tiles(self):
        model = _make_model()
        tiler = DetectionTiler(
            model,
            configuration={"tile_size": 50, "tile_with_full_img": False},
            execution_mode="sync",
        )
        smap1 = np.ones((2, 5, 5), dtype=np.float32) * 100
        smap2 = np.ones((2, 5, 5), dtype=np.float32) * 50
        coords = [[0, 0, 50, 50], [50, 0, 100, 50]]
        result = tiler._merge_saliency_maps([smap1, smap2], (50, 100, 3), coords)  # noqa: SLF001
        assert result.dtype == np.uint8

    def test_merge_saliency_maps_with_full_img(self):
        model = _make_model()
        tiler = DetectionTiler(
            model,
            configuration={"tile_size": 50, "tile_with_full_img": True},
            execution_mode="sync",
        )
        smap_full = np.ones((2, 5, 5), dtype=np.float32) * 100
        smap_tile = np.ones((2, 5, 5), dtype=np.float32) * 50
        coords = [[0, 0, 50, 50], [0, 0, 50, 50]]
        result = tiler._merge_saliency_maps([smap_full, smap_tile], (50, 50, 3), coords)  # noqa: SLF001
        assert result is not None

    def test_merge_saliency_maps_resize_and_overlap(self):
        """Covers line 174 (cv.resize) and 182 (overlap averaging)."""
        model = _make_model()
        # tile_size=30, img=40x40
        # ratio = map_h/min(img_h, tile_size) = 20/30 = 0.667
        # coord [0,0,15,15] -> mapped y2-y1 = int(15*0.667)=10, cls_map 20x20 > 10 -> resize
        # Two overlapping tiles trigger line 182 (overlap averaging)
        tiler = DetectionTiler(
            model,
            configuration={"tile_size": 30, "tile_with_full_img": False},
            execution_mode="sync",
        )
        smap1 = np.ones((1, 20, 20), dtype=np.float32) * 100
        smap2 = np.ones((1, 20, 20), dtype=np.float32) * 80
        coords = [[0, 0, 15, 15], [0, 0, 15, 15]]
        result = tiler._merge_saliency_maps([smap1, smap2], (40, 40, 3), coords)  # noqa: SLF001
        assert result is not None
        assert result.dtype == np.uint8


class TestNonLinearNormalization:
    def test_normalization(self):
        smap = np.array([[0.0, 50.0], [100.0, 200.0]])
        result = _non_linear_normalization(smap)
        assert result.max() <= 255
        assert result.min() >= 0

    def test_normalization_constant(self):
        smap = np.ones((3, 3)) * 5.0
        result = _non_linear_normalization(smap)
        # All same value -> after normalization should be 0 (since (x - min)^1.5 = 0)
        np.testing.assert_array_equal(result, np.zeros((3, 3)))
