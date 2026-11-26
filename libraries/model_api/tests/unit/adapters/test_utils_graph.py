# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Tests for utils.py graph functions and missing coverage lines."""

from __future__ import annotations

import numpy as np
import openvino as ov
import pytest
from model_api.adapters.utils import (
    Layout,
    crop_resize,
    range_scale_preprocess,
    range_scale_preprocess_graph,
    resize_image,
    resize_image_graph,
    resize_image_letterbox,
    resize_image_letterbox_graph,
    resize_image_with_aspect,
    window_preprocess,
)
from openvino.preprocess import PrePostProcessor

rng = np.random.default_rng(0)


class TestLayoutFromOpenvino:
    def test_from_openvino(self):
        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ppp = PrePostProcessor(model)
        ppp.input().model().set_layout(ov.Layout("NCHW"))
        built = ppp.build()
        inp = built.inputs[0]
        result = Layout.from_openvino(inp)
        assert result == "NCHW"


class TestLayoutParseLayoutsError:
    def test_parse_layouts_invalid(self):
        with pytest.raises(ValueError, match="Can't parse input layout string"):
            Layout.parse_layouts("garbage_without_colon,input0:NCHW")


class TestResizeImageLetterboxGraphValidation:
    def test_pad_value_too_low(self):
        param = ov.op.Parameter(ov.Type.u8, ov.PartialShape([-1, -1, -1, 3]))
        with pytest.raises(RuntimeError, match="pad_value must be in range"):
            resize_image_letterbox_graph(param.output(0), (224, 224), "linear", -1)

    def test_pad_value_too_high(self):
        param = ov.op.Parameter(ov.Type.u8, ov.PartialShape([-1, -1, -1, 3]))
        with pytest.raises(RuntimeError, match="pad_value must be in range"):
            resize_image_letterbox_graph(param.output(0), (224, 224), "linear", 70000)


class TestResizeImageGraphValidation:
    def test_pad_value_too_low(self):
        param = ov.op.Parameter(ov.Type.u8, ov.PartialShape([-1, -1, -1, 3]))
        with pytest.raises(RuntimeError, match="pad_value must be in range"):
            resize_image_graph(
                param.output(0),
                (224, 224),
                keep_aspect_ratio=True,
                interpolation="linear",
                pad_value=-1,
            )

    def test_pad_value_too_high(self):
        param = ov.op.Parameter(ov.Type.u8, ov.PartialShape([-1, -1, -1, 3]))
        with pytest.raises(RuntimeError, match="pad_value must be in range"):
            resize_image_graph(
                param.output(0),
                (224, 224),
                keep_aspect_ratio=True,
                interpolation="linear",
                pad_value=70000,
            )

    def test_non_aspect_ratio(self):
        """Test resize_image_graph with keep_aspect_ratio=False."""
        model_h, model_w = 64, 64
        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, model_h, model_w, 3]))
        model = ov.Model(param, [param])
        ppp = PrePostProcessor(model)
        ppp.input().tensor().set_element_type(ov.Type.u8)
        ppp.input().tensor().set_layout(ov.Layout("NHWC"))
        ppp.input().tensor().set_shape([1, -1, -1, 3])
        ppp.input().preprocess().custom(
            resize_image((model_h, model_w), "linear", 0),
        )
        ppp.input().preprocess().convert_element_type(ov.Type.f32)
        built = ppp.build()
        compiled = ov.Core().compile_model(built, "CPU")

        img = rng.integers(0, 255, (100, 200, 3), dtype=np.uint8)
        result = next(iter(compiled(img[None]).values()))
        assert result.shape == (1, model_h, model_w, 3)


class TestCropResizeGraph:
    def _build_and_run_crop(self, size, img_shape, input_dtype="u8"):
        np_dtype = np.uint8 if input_dtype == "u8" else np.uint16
        ov_type = ov.Type.u8 if input_dtype == "u8" else ov.Type.u16

        # size = (w, h), model shape is (1, h, w, 3) in NHWC
        w, h = size
        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, h, w, 3]))
        model = ov.Model(param, [param])
        ppp = PrePostProcessor(model)
        ppp.input().tensor().set_element_type(ov_type)
        ppp.input().tensor().set_layout(ov.Layout("NHWC"))
        ppp.input().tensor().set_shape([1, -1, -1, 3])
        ppp.input().preprocess().custom(
            crop_resize(size, "linear", 0, input_dtype=input_dtype),
        )
        ppp.input().preprocess().convert_element_type(ov.Type.f32)
        built = ppp.build()
        compiled = ov.Core().compile_model(built, "CPU")

        img = rng.integers(0, 255, img_shape, dtype=np_dtype)
        return next(iter(compiled(img[None]).values()))

    def test_crop_square_tall(self):
        """aspect_ratio == 1, ih > iw path (then_body)."""
        result = self._build_and_run_crop((64, 64), (100, 50, 3))
        assert result.shape == (1, 64, 64, 3)

    def test_crop_square_wide(self):
        """aspect_ratio == 1, iw > ih path (else_body)."""
        result = self._build_and_run_crop((64, 64), (50, 100, 3))
        assert result.shape == (1, 64, 64, 3)

    def test_crop_aspect_less_than_1(self):
        """desired_aspect_ratio < 1 path. size=(w=50, h=100), w/h=0.5"""
        result = self._build_and_run_crop((50, 100), (200, 200, 3))
        assert result.shape == (1, 100, 50, 3)

    def test_crop_aspect_greater_than_1(self):
        """desired_aspect_ratio > 1 path. size=(w=100, h=50), w/h=2.0"""
        result = self._build_and_run_crop((100, 50), (200, 200, 3))
        assert result.shape == (1, 50, 100, 3)


class TestSetupPreprocessingPartials:
    """Test the partial-returning functions (lines 399, 435, 482, 526)."""

    def test_resize_image_returns_callable(self):
        fn = resize_image((224, 224), "linear", 0)
        assert callable(fn)

    def test_resize_image_with_aspect_returns_callable(self):
        fn = resize_image_with_aspect((224, 224), "linear", 0)
        assert callable(fn)

    def test_resize_image_letterbox_returns_callable(self):
        fn = resize_image_letterbox((224, 224), "linear", 128)
        assert callable(fn)

    def test_crop_resize_returns_callable(self):
        fn = crop_resize((224, 224), "linear", 0)
        assert callable(fn)

    def test_window_preprocess_returns_callable(self):
        fn = window_preprocess(128.0, 256.0)
        assert callable(fn)

    def test_range_scale_preprocess_returns_callable(self):
        fn = range_scale_preprocess(1.0, 0.0, 255.0)
        assert callable(fn)


class TestWindowPreprocessGraph:
    def test_window_graph_execution(self):
        """Test window_preprocess through OV model execution."""
        model_h, model_w = 4, 4
        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, model_h, model_w, 3]))
        model = ov.Model(param, [param])
        ppp = PrePostProcessor(model)
        ppp.input().tensor().set_element_type(ov.Type.u16)
        ppp.input().tensor().set_layout(ov.Layout("NHWC"))
        ppp.input().preprocess().custom(
            window_preprocess(500.0, 1000.0),
        )
        built = ppp.build()
        compiled = ov.Core().compile_model(built, "CPU")

        # window: center=500, width=1000 → low=0, high=1000
        img = np.full((1, model_h, model_w, 3), 500, dtype=np.uint16)
        result = next(iter(compiled(img).values()))
        # 500 → (500-0)/1000 = 0.5
        np.testing.assert_allclose(result, 0.5, atol=1e-5)


class TestRangeScalePreprocessGraph:
    def test_range_scale_graph_execution(self):
        """Test range_scale_preprocess through OV model execution."""
        model_h, model_w = 4, 4
        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, model_h, model_w, 3]))
        model = ov.Model(param, [param])
        ppp = PrePostProcessor(model)
        ppp.input().tensor().set_element_type(ov.Type.u8)
        ppp.input().tensor().set_layout(ov.Layout("NHWC"))
        ppp.input().preprocess().custom(
            range_scale_preprocess(2.0, 0.0, 500.0),
        )
        built = ppp.build()
        compiled = ov.Core().compile_model(built, "CPU")

        img = np.full((1, model_h, model_w, 3), 100, dtype=np.uint8)
        result = next(iter(compiled(img).values()))
        # 100 * 2.0 = 200, clamp(200, 0, 500) = 200, (200-0)/500 = 0.4
        np.testing.assert_allclose(result, 0.4, atol=2e-4)

    def test_range_scale_graph_zero_range(self):
        """Test range_scale_preprocess_graph when range == 0."""
        param = ov.op.Parameter(ov.Type.f32, ov.PartialShape([1, 4, 4, 3]))
        node = range_scale_preprocess_graph(
            param.output(0),
            scale_factor=1.0,
            min_value=5.0,
            max_value=5.0,
        )
        assert node is not None
