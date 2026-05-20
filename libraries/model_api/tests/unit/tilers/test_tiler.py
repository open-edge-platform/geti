# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from model_api.tilers.tiler import Tiler


class ConcreteTiler(Tiler):
    """Concrete implementation for testing the abstract Tiler."""

    def _postprocess_tile(self, predictions, coord):
        return {"predictions": predictions, "coord": coord}

    def _merge_results(self, results, shape):
        return results


def _make_model():
    model = MagicMock()
    model.load = MagicMock()
    model.inference_adapter = MagicMock()
    model.inference_adapter.get_rt_info.side_effect = RuntimeError(
        "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
    )
    return model


class TestTilerInit:
    def test_init_defaults(self):
        model = _make_model()
        tiler = ConcreteTiler(model)
        assert tiler.model is model
        assert tiler.execution_mode == "async"
        assert tiler.tile_size == 400
        assert tiler.tiles_overlap == 0.5
        assert tiler.tile_with_full_img is True

    def test_init_sync_mode(self):
        model = _make_model()
        tiler = ConcreteTiler(model, execution_mode="sync")
        assert tiler.execution_mode == "sync"

    def test_init_invalid_mode(self):
        model = _make_model()
        with pytest.raises(ValueError, match="Wrong execution mode"):
            ConcreteTiler(model, execution_mode="invalid")

    def test_init_with_configuration(self):
        model = _make_model()
        tiler = ConcreteTiler(model, configuration={"tile_size": 200, "tiles_overlap": 0.3})
        assert tiler.tile_size == 200
        assert tiler.tiles_overlap == 0.3

    def test_get_model(self):
        model = _make_model()
        tiler = ConcreteTiler(model)
        assert tiler.get_model() is model


class TestTilerParameters:
    def test_parameters_returns_dict(self):
        params = ConcreteTiler.parameters()
        assert "tile_size" in params
        assert "tiles_overlap" in params
        assert "tile_with_full_img" in params


class TestTilerLoadConfig:
    def test_load_config_from_rt_info(self):
        model = _make_model()
        rt_mock = MagicMock()
        rt_mock.astype.return_value = "300"
        model.inference_adapter.get_rt_info.side_effect = None
        model.inference_adapter.get_rt_info.return_value = rt_mock
        ConcreteTiler(model)
        # rt_info values should have been loaded

    def test_load_config_rt_info_missing(self):
        model = _make_model()
        # Default side_effect raises RuntimeError with correct message - should be handled
        tiler = ConcreteTiler(model)
        assert tiler.tile_size == 400  # default

    def test_load_config_rt_info_ovms_error(self):
        model = _make_model()
        model.inference_adapter.get_rt_info.side_effect = RuntimeError(
            "OVMSAdapter does not support RT info getting",
        )
        tiler = ConcreteTiler(model)
        assert tiler.tile_size == 400

    def test_load_config_rt_info_unexpected_error(self):
        model = _make_model()
        model.inference_adapter.get_rt_info.side_effect = RuntimeError("unexpected error")
        with pytest.raises(RuntimeError, match="unexpected error"):
            ConcreteTiler(model)

    def test_load_config_invalid_value(self):
        model = _make_model()
        with pytest.raises(RuntimeError, match="Incorrect user configuration"):
            ConcreteTiler(model, configuration={"tile_size": -5})

    def test_load_config_unknown_param_ignored(self):
        model = _make_model()
        tiler = ConcreteTiler(model, configuration={"unknown_param": 42})
        assert not hasattr(tiler, "unknown_param")

    def test_load_config_none_value_skipped(self):
        model = _make_model()
        tiler = ConcreteTiler(model, configuration={"tile_size": None})
        assert tiler.tile_size == 400


class TestTilerTile:
    def test_tile_with_full_img(self):
        model = _make_model()
        tiler = ConcreteTiler(model, configuration={"tile_size": 100, "tiles_overlap": 0.0, "tile_with_full_img": True})
        image = np.zeros((200, 300, 3), dtype=np.uint8)
        coords = tiler._tile(image)  # noqa: SLF001
        assert coords[0] == [0, 0, 300, 200]
        assert len(coords) > 1

    def test_tile_without_full_img(self):
        model = _make_model()
        tiler = ConcreteTiler(
            model,
            configuration={"tile_size": 100, "tiles_overlap": 0.0, "tile_with_full_img": False},
        )
        image = np.zeros((200, 300, 3), dtype=np.uint8)
        coords = tiler._tile(image)  # noqa: SLF001
        assert coords[0] != [0, 0, 300, 200]

    def test_tile_overlap(self):
        model = _make_model()
        tiler = ConcreteTiler(
            model,
            configuration={"tile_size": 100, "tiles_overlap": 0.5, "tile_with_full_img": False},
        )
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        coords = tiler._tile(image)  # noqa: SLF001
        # With 50% overlap and tile_size=100, step=50
        assert len(coords) > 2

    def test_tile_clamps_to_image_boundary(self):
        model = _make_model()
        tiler = ConcreteTiler(
            model,
            configuration={"tile_size": 150, "tiles_overlap": 0.0, "tile_with_full_img": False},
        )
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        coords = tiler._tile(image)  # noqa: SLF001
        for c in coords:
            assert c[2] <= 200
            assert c[3] <= 100


class TestTilerFilterTiles:
    def test_filter_tiles_returns_unchanged(self):
        model = _make_model()
        tiler = ConcreteTiler(model)
        coords = [[0, 0, 100, 100], [100, 0, 200, 100]]
        image = np.zeros((100, 200, 3))
        assert tiler._filter_tiles(image, coords) == coords  # noqa: SLF001


class TestTilerCropTile:
    def test_crop_tile(self):
        model = _make_model()
        tiler = ConcreteTiler(model)
        image = np.arange(60).reshape(6, 10, 1)
        crop = tiler._crop_tile(image, [2, 1, 5, 4])  # noqa: SLF001
        assert crop.shape == (3, 3, 1)
        np.testing.assert_array_equal(crop, image[1:4, 2:5])


class TestTilerCall:
    def test_call_sync(self):
        model = _make_model()
        model.return_value = "prediction"
        tiler = ConcreteTiler(
            model,
            configuration={"tile_size": 100, "tiles_overlap": 0.0, "tile_with_full_img": False},
            execution_mode="sync",
        )
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        results = tiler(image)
        assert isinstance(results, list)
        assert len(results) > 0

    @patch("model_api.tilers.tiler.AsyncPipeline")
    def test_call_async(self, mock_pipeline_cls):
        model = _make_model()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_pipeline.get_result.return_value = ("pred", {})
        tiler = ConcreteTiler(
            model,
            configuration={"tile_size": 100, "tiles_overlap": 0.0, "tile_with_full_img": False},
            execution_mode="async",
        )
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        results = tiler(image)
        mock_pipeline.await_all.assert_called_once()
        assert isinstance(results, list)


class TestTilerPredictSync:
    def test_predict_sync(self):
        model = _make_model()
        model.return_value = "pred"
        tiler = ConcreteTiler(model, execution_mode="sync")
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        coords = [[0, 0, 100, 100], [100, 0, 200, 100]]
        results = tiler._predict_sync(image, coords)  # noqa: SLF001
        assert len(results) == 2
        assert model.call_count == 2


class TestTilerPredictAsync:
    @patch("model_api.tilers.tiler.AsyncPipeline")
    def test_predict_async(self, mock_pipeline_cls):
        model = _make_model()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_pipeline.get_result.return_value = ("pred", {})
        tiler = ConcreteTiler(model)
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        coords = [[0, 0, 100, 100], [100, 0, 200, 100]]
        results = tiler._predict_async(image, coords)  # noqa: SLF001
        assert mock_pipeline.submit_data.call_count == 2
        mock_pipeline.await_all.assert_called_once()
        assert len(results) == 2
