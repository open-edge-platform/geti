# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock

import pytest
from model_api.pipelines import AsyncPipeline
from model_api.pipelines.async_pipeline import AsyncPipeline as DirectImport


class TestAsyncPipelineInit:
    def _make_model(self):
        model = MagicMock()
        model.load = MagicMock()
        model.inference_adapter = MagicMock()
        return model

    def test_init_loads_model_and_sets_callback(self):
        model = self._make_model()
        pipeline = AsyncPipeline(model)
        model.load.assert_called_once()
        model.inference_adapter.set_callback.assert_called_once_with(pipeline.callback)
        assert pipeline.completed_results == {}
        assert pipeline.callback_exceptions == []
        assert pipeline.model is model

    def test_direct_import(self):
        assert DirectImport is AsyncPipeline


class TestAsyncPipelineCallback:
    def setup_method(self):
        self.model = MagicMock()
        self.pipeline = AsyncPipeline(self.model)

    def test_callback_stores_result(self):
        request = MagicMock()
        self.model.inference_adapter.copy_raw_result.return_value = "raw"
        callback_args = (42, {"key": "val"}, {"pre": "meta"})
        self.pipeline.callback(request, callback_args)
        assert 42 in self.pipeline.completed_results
        raw, meta, pre = self.pipeline.completed_results[42]
        assert raw == "raw"
        assert meta == {"key": "val"}
        assert pre == {"pre": "meta"}
        self.model.inference_adapter.copy_raw_result.assert_called_once_with(request)

    def test_callback_exception_is_captured(self):
        self.model.inference_adapter.copy_raw_result.side_effect = RuntimeError("fail")
        self.pipeline.callback(MagicMock(), (1, {}, {}))
        assert len(self.pipeline.callback_exceptions) == 1
        assert isinstance(self.pipeline.callback_exceptions[0], RuntimeError)

    def test_callback_bad_args_captured(self):
        self.pipeline.callback(MagicMock(), "not_a_tuple")
        assert len(self.pipeline.callback_exceptions) == 1


class TestAsyncPipelineSubmitData:
    def setup_method(self):
        self.model = MagicMock()
        self.model.base_preprocess.return_value = ("processed", {"pmeta": 1})
        self.pipeline = AsyncPipeline(self.model)

    def test_submit_data(self):
        self.pipeline.submit_data("input", 1, {"m": 2})
        self.model.base_preprocess.assert_called_once_with("input")
        self.model.infer_async_raw.assert_called_once_with(
            "processed",
            (1, {"m": 2}, {"pmeta": 1}),
        )
        assert self.model.perf.preprocess_time.update.call_count == 2
        self.model.perf.inference_time.update.assert_called_once()

    def test_submit_data_default_meta(self):
        self.pipeline.submit_data("input", 5)
        self.model.infer_async_raw.assert_called_once()
        args = self.model.infer_async_raw.call_args[0]
        assert args[1][1] == {}


class TestAsyncPipelineGetRawResult:
    def setup_method(self):
        self.model = MagicMock()
        self.pipeline = AsyncPipeline(self.model)

    def test_get_raw_result_found(self):
        self.pipeline.completed_results[10] = ("raw", "meta", "pre")
        result = self.pipeline.get_raw_result(10)
        assert result == ("raw", "meta", "pre")
        assert 10 not in self.pipeline.completed_results

    def test_get_raw_result_not_found(self):
        assert self.pipeline.get_raw_result(99) is None


class TestAsyncPipelineGetResult:
    def setup_method(self):
        self.model = MagicMock()
        self.model.postprocess.return_value = "postprocessed"
        self.pipeline = AsyncPipeline(self.model)

    def test_get_result_found(self):
        self.pipeline.completed_results[7] = ("raw", {"a": 1}, {"b": 2})
        result = self.pipeline.get_result(7)
        assert result is not None
        post, merged_meta = result
        assert post == "postprocessed"
        assert merged_meta == {"a": 1, "b": 2}
        self.model.postprocess.assert_called_once_with("raw", {"b": 2})
        assert self.model.perf.inference_time.update.call_count == 1
        assert self.model.perf.postprocess_time.update.call_count == 2

    def test_get_result_not_found(self):
        assert self.pipeline.get_result(99) is None

    def test_get_result_meta_merge(self):
        self.pipeline.completed_results[1] = ("raw", {"x": 1, "y": 2}, {"y": 3, "z": 4})
        _, meta = self.pipeline.get_result(1)
        assert meta == {"x": 1, "y": 3, "z": 4}


class TestAsyncPipelineIsReady:
    def test_is_ready(self):
        model = MagicMock()
        model.is_ready.return_value = True
        pipeline = AsyncPipeline(model)
        assert pipeline.is_ready() is True
        model.is_ready.assert_called_once()


class TestAsyncPipelineAwait:
    def setup_method(self):
        self.model = MagicMock()
        self.pipeline = AsyncPipeline(self.model)

    def test_await_all_no_exceptions(self):
        self.pipeline.await_all()
        self.model.await_all.assert_called_once()

    def test_await_all_with_exception(self):
        self.pipeline.callback_exceptions.append(ValueError("err"))
        with pytest.raises(ValueError, match="err"):
            self.pipeline.await_all()

    def test_await_any_no_exceptions(self):
        self.pipeline.await_any()
        self.model.await_any.assert_called_once()

    def test_await_any_with_exception(self):
        self.pipeline.callback_exceptions.append(TypeError("bad"))
        with pytest.raises(TypeError, match="bad"):
            self.pipeline.await_any()
