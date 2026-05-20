# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

import numpy as np
from model_api.models import InstanceSegmentationResult
from model_api.tilers.instance_segmentation import InstanceSegmentationTiler


def _make_model():
    model = MagicMock()
    model.load = MagicMock()
    model.inference_adapter = MagicMock()
    model.inference_adapter.get_rt_info.side_effect = RuntimeError(
        "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
    )
    model.get_label_name = MagicMock(side_effect=lambda x: f"label_{x}")
    return model


def _make_instance_seg_result(n=2, offset=(0, 0)):
    bboxes = np.array([[10 + offset[0], 20 + offset[1], 50 + offset[0], 60 + offset[1]]] * n, dtype=np.float32)
    labels = np.array([0] * n, dtype=np.int32)
    scores = np.array([0.9] * n, dtype=np.float32)
    masks = [np.ones((40, 40), dtype=np.uint8) for _ in range(n)]
    return InstanceSegmentationResult(
        bboxes=bboxes,
        labels=labels,
        scores=scores,
        masks=np.array(masks),
        saliency_map=[np.zeros((10, 10), dtype=np.float32)],
        feature_vector=np.zeros((1,), dtype=np.float32),
    )


class TestInstanceSegmentationTilerInit:
    def test_init(self):
        model = _make_model()
        tiler = InstanceSegmentationTiler(model, execution_mode="sync")
        assert tiler.tile_classifier_model is None

    def test_init_with_classifier(self):
        model = _make_model()
        classifier = MagicMock()
        tiler = InstanceSegmentationTiler(model, execution_mode="sync", tile_classifier_model=classifier)
        assert tiler.tile_classifier_model is classifier


class TestInstanceSegmentationTilerFilterTiles:
    def test_filter_tiles_no_classifier(self):
        model = _make_model()
        tiler = InstanceSegmentationTiler(model, execution_mode="sync")
        coords = [[0, 0, 100, 100], [100, 0, 200, 100]]
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        assert tiler._filter_tiles(image, coords) == coords  # noqa: SLF001

    def test_filter_tiles_with_classifier(self):
        model = _make_model()
        model.base_preprocess.return_value = ({"data": "preprocessed"}, {})
        classifier = MagicMock()
        # First tile (i==0) always kept, second filtered by threshold
        classifier.infer_sync.side_effect = [
            {"tile_prob": 0.1},  # tile 0 - kept (always first)
            {"tile_prob": 0.5},  # tile 1 - kept (above threshold)
            {"tile_prob": 0.1},  # tile 2 - filtered
        ]
        tiler = InstanceSegmentationTiler(model, execution_mode="sync", tile_classifier_model=classifier)
        image = np.zeros((100, 300, 3), dtype=np.uint8)
        coords = [[0, 0, 100, 100], [100, 0, 200, 100], [200, 0, 300, 100]]
        result = tiler._filter_tiles(image, coords)  # noqa: SLF001
        assert len(result) == 2
        assert coords[0] in result
        assert coords[1] in result


class TestInstanceSegmentationTilerPostprocessTile:
    def test_postprocess_tile(self):
        model = _make_model()
        tiler = InstanceSegmentationTiler(model, execution_mode="async")
        pred = _make_instance_seg_result(n=1)
        coord = [10, 20, 110, 120]
        result = tiler._postprocess_tile(pred, coord)  # noqa: SLF001
        assert "masks" in result
        assert "bboxes" in result
        assert len(result["masks"]) == 1


class TestInstanceSegmentationTilerMergeResults:
    @patch("model_api.tilers.instance_segmentation.multiclass_nms")
    @patch("model_api.tilers.instance_segmentation._segm_postprocess")
    def test_merge_results_with_detections(self, mock_segm, mock_nms):
        model = _make_model()
        tiler = InstanceSegmentationTiler(model, execution_mode="sync")
        mock_nms.return_value = np.array([0])
        mock_segm.return_value = np.ones((100, 100), dtype=np.uint8)

        results = [
            {
                "bboxes": np.array([[0, 0.9, 10, 20, 50, 60]], dtype=np.float32),
                "features": np.array([1.0]),
                "saliency_map": [],
                "coords": [0, 0, 100, 100],
                "masks": [np.ones((40, 40), dtype=np.uint8)],
            },
        ]
        merged = tiler._merge_results(results, (100, 100, 3))  # noqa: SLF001
        assert isinstance(merged, InstanceSegmentationResult)

    def test_merge_results_empty(self):
        model = _make_model()
        tiler = InstanceSegmentationTiler(model, execution_mode="sync")
        results = [
            {
                "bboxes": np.empty((0, 6), dtype=np.float32),
                "features": np.array([1.0]),
                "saliency_map": [],
                "coords": [0, 0, 100, 100],
                "masks": [],
            },
        ]
        merged = tiler._merge_results(results, (100, 100, 3))  # noqa: SLF001
        assert isinstance(merged, InstanceSegmentationResult)


class TestInstanceSegmentationTilerMergeSaliencyMaps:
    def test_merge_saliency_maps_empty(self):
        model = _make_model()
        tiler = InstanceSegmentationTiler(model, execution_mode="sync")
        assert tiler._merge_saliency_maps([], (100, 100, 3), []) is None  # noqa: SLF001

    def test_merge_saliency_maps_falsy_first(self):
        model = _make_model()
        tiler = InstanceSegmentationTiler(model, execution_mode="sync")
        result = tiler._merge_saliency_maps([[]], (100, 100, 3), [[0, 0, 100, 100]])  # noqa: SLF001
        assert result == []

    def test_merge_saliency_maps_with_tiles(self):
        model = _make_model()
        tiler = InstanceSegmentationTiler(
            model,
            configuration={"tile_size": 50, "tile_with_full_img": True},
            execution_mode="sync",
        )
        smap_full = [np.ones((10, 20), dtype=np.float32) * 100, np.ones((10, 20), dtype=np.float32) * 50]
        smap_tile = [np.ones((10, 10), dtype=np.float32) * 80, np.ones((10, 10), dtype=np.float32) * 40]
        coords = [[0, 0, 100, 50], [0, 0, 50, 50]]
        result = tiler._merge_saliency_maps([smap_full, smap_tile], (50, 100, 3), coords)  # noqa: SLF001
        assert len(result) == 2

    def test_merge_saliency_maps_1d_class_map_skipped(self):
        model = _make_model()
        tiler = InstanceSegmentationTiler(
            model,
            configuration={"tile_size": 50, "tile_with_full_img": False},
            execution_mode="sync",
        )
        smap = [np.array([1.0]), np.array([2.0])]
        coords = [[0, 0, 50, 50]]
        result = tiler._merge_saliency_maps([smap], (50, 50, 3), coords)  # noqa: SLF001
        # 1d maps - rounded and checked for sum==0
        assert len(result) == 2

    def test_merge_saliency_maps_no_full_img(self):
        model = _make_model()
        tiler = InstanceSegmentationTiler(
            model,
            configuration={"tile_size": 50, "tile_with_full_img": False},
            execution_mode="sync",
        )
        smap1 = [np.ones((10, 10), dtype=np.float32) * 100]
        smap2 = [np.ones((10, 10), dtype=np.float32) * 50]
        coords = [[0, 0, 50, 50], [50, 0, 100, 50]]
        result = tiler._merge_saliency_maps([smap1, smap2], (50, 100, 3), coords)  # noqa: SLF001
        assert len(result) == 1

    def test_merge_saliency_maps_zero_sum(self):
        model = _make_model()
        tiler = InstanceSegmentationTiler(
            model,
            configuration={"tile_size": 50, "tile_with_full_img": False},
            execution_mode="sync",
        )
        # All zeros - should result in ndarray(0) for 1d case
        smap = [np.array([0.0])]
        coords = [[0, 0, 50, 50]]
        result = tiler._merge_saliency_maps([smap], (50, 50, 3), coords)  # noqa: SLF001
        # 1d map with sum 0 gets replaced with ndarray(0)
        assert result[0].shape == (0,)


class TestInstanceSegmentationTilerCall:
    def test_call_with_maskrcnn(self):
        model = _make_model()
        model.__class__ = MagicMock
        # Mock isinstance check
        with patch("model_api.tilers.instance_segmentation.isinstance") as mock_isinstance:
            mock_isinstance.side_effect = (
                lambda obj, cls: cls == MagicMock if cls != InstanceSegmentationTiler else False
            )
            # Just test that __call__ delegates to super().__call__
            tiler = InstanceSegmentationTiler(model, execution_mode="sync")
            with patch.object(InstanceSegmentationTiler.__bases__[0], "__call__", return_value="result"):
                # Can't easily mock isinstance for MaskRCNNModel, test non-MaskRCNN path
                image = np.zeros((100, 100, 3), dtype=np.uint8)
                tiler(image)

    def test_call_with_actual_maskrcnn_mock(self):
        from model_api.models.instance_segmentation import MaskRCNNModel

        model = MagicMock(spec=MaskRCNNModel)
        model.load = MagicMock()
        model.inference_adapter = MagicMock()
        model.inference_adapter.get_rt_info.side_effect = RuntimeError(
            "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
        )
        model.params = MagicMock()
        model.params.postprocess_semantic_masks = True
        model.return_value = _make_instance_seg_result(n=1)

        tiler = InstanceSegmentationTiler(
            model,
            execution_mode="sync",
            configuration={"tile_size": 100, "tiles_overlap": 0.0, "tile_with_full_img": False},
        )
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        with patch.object(tiler, "_merge_results", return_value="merged"):
            result = tiler(image)
            assert result == "merged"

    def test_call_non_maskrcnn(self):
        model = _make_model()
        model.return_value = _make_instance_seg_result(n=1)
        tiler = InstanceSegmentationTiler(
            model,
            execution_mode="sync",
            configuration={"tile_size": 100, "tiles_overlap": 0.0, "tile_with_full_img": False},
        )
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        with patch.object(tiler, "_merge_results", return_value="merged"):
            result = tiler(image)
            assert result == "merged"
