# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

import numpy as np
from model_api.models import ImageResultWithSoftPrediction
from model_api.tilers.semantic_segmentation import SemanticSegmentationTiler

rng = np.random.default_rng(0)


def _make_model(num_labels=3):
    model = MagicMock()
    model.load = MagicMock()
    model.inference_adapter = MagicMock()
    model.inference_adapter.get_rt_info.side_effect = RuntimeError(
        "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
    )
    model.params = MagicMock()
    model.params.labels = [f"label_{i}" for i in range(num_labels)]
    return model


def _make_seg_result(h, w, num_classes=3):
    soft = rng.random((h, w, num_classes)).astype(np.float32)
    return ImageResultWithSoftPrediction(
        resultImage=soft.argmax(2),
        soft_prediction=soft,
        saliency_map=np.array([]),
        feature_vector=np.array([]),
    )


class TestSemanticSegmentationTilerPostprocessTile:
    def test_postprocess_tile(self):
        model = _make_model()
        tiler = SemanticSegmentationTiler(model, execution_mode="sync")
        pred = _make_seg_result(50, 50)
        coord = [0, 0, 50, 50]
        result = tiler._postprocess_tile(pred, coord)  # noqa: SLF001
        assert "coord" in result
        assert "masks" in result
        assert result["coord"] == coord
        np.testing.assert_array_equal(result["masks"], pred.soft_prediction)


class TestSemanticSegmentationTilerMergeResults:
    def test_merge_results(self):
        model = _make_model(num_labels=2)
        tiler = SemanticSegmentationTiler(model, execution_mode="sync")

        results = [
            {
                "coord": [0, 0, 50, 50],
                "masks": np.ones((50, 50, 2), dtype=np.float32) * 0.7,
            },
            {
                "coord": [25, 0, 75, 50],
                "masks": np.ones((50, 50, 2), dtype=np.float32) * 0.3,
            },
        ]
        merged = tiler._merge_results(results, (50, 75, 3))  # noqa: SLF001
        assert isinstance(merged, ImageResultWithSoftPrediction)
        assert merged.resultImage.shape == (50, 75)
        assert merged.soft_prediction.shape == (50, 75, 2)

    def test_merge_results_single_tile(self):
        model = _make_model(num_labels=3)
        tiler = SemanticSegmentationTiler(model, execution_mode="sync")
        soft = rng.random((100, 100, 3)).astype(np.float32)
        results = [{"coord": [0, 0, 100, 100], "masks": soft}]
        merged = tiler._merge_results(results, (100, 100, 3))  # noqa: SLF001
        assert isinstance(merged, ImageResultWithSoftPrediction)
        np.testing.assert_array_almost_equal(merged.soft_prediction, soft)


class TestSemanticSegmentationTilerCall:
    def test_call_with_segmentation_model(self):
        from model_api.models.segmentation import SegmentationModel

        model = MagicMock(spec=SegmentationModel)
        model.load = MagicMock()
        model.inference_adapter = MagicMock()
        model.inference_adapter.get_rt_info.side_effect = RuntimeError(
            "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
        )
        model.params = MagicMock()
        model.params.labels = ["a", "b"]
        model.params.return_soft_prediction = False

        seg_result = _make_seg_result(100, 100, num_classes=2)
        model.return_value = seg_result

        tiler = SemanticSegmentationTiler(
            model,
            execution_mode="sync",
            configuration={"tile_size": 100, "tiles_overlap": 0.0, "tile_with_full_img": False},
        )
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        with patch.object(tiler, "_merge_results", return_value="merged"):
            result = tiler(image)
            assert result == "merged"

    def test_call_non_segmentation_model(self):
        model = _make_model(num_labels=2)
        seg_result = _make_seg_result(100, 100, num_classes=2)
        model.return_value = seg_result

        tiler = SemanticSegmentationTiler(
            model,
            execution_mode="sync",
            configuration={"tile_size": 100, "tiles_overlap": 0.0, "tile_with_full_img": False},
        )
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        with patch.object(tiler, "_merge_results", return_value="merged"):
            result = tiler(image)
            assert result == "merged"
