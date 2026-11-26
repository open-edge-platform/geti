#
# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for intensity preprocessing."""

from __future__ import annotations

import numpy as np
import pytest
from model_api.adapters.utils import InputTransform, create_intensity_fn

# ---------------------------------------------------------------------------
# create_intensity_fn factory tests
# ---------------------------------------------------------------------------


class TestCreateIntensityFn:
    def test_none_returns_none(self):
        assert create_intensity_fn("none") is None

    # -- scale_to_unit ---------------------------------------------------------

    def test_scale_to_unit_basic(self):
        fn = create_intensity_fn("scale_to_unit", max_value=255.0)
        img = np.array([0, 128, 255], dtype=np.uint8)
        out = fn(img)
        np.testing.assert_allclose(out, [0.0, 128.0 / 255, 1.0], atol=1e-6)

    def test_scale_to_unit_u16(self):
        fn = create_intensity_fn("scale_to_unit", max_value=65535.0)
        img = np.array([0, 32768, 65535], dtype=np.uint16)
        out = fn(img)
        np.testing.assert_allclose(out, [0.0, 32768.0 / 65535, 1.0], atol=1e-6)

    def test_scale_to_unit_missing_max_raises(self):
        with pytest.raises(ValueError, match="intensity_max_value is required"):
            create_intensity_fn("scale_to_unit")

    # -- window ----------------------------------------------------------------

    def test_window_basic(self):
        fn = create_intensity_fn("window", window_center=100.0, window_width=200.0)
        # low=0, high=200, span=200
        img = np.array([0, 100, 200, 300], dtype=np.float32)
        out = fn(img)
        np.testing.assert_allclose(out, [0.0, 0.5, 1.0, 1.0], atol=1e-6)

    def test_window_clips_below(self):
        fn = create_intensity_fn("window", window_center=100.0, window_width=100.0)
        # low=50, high=150
        img = np.array([0.0], dtype=np.float32)
        out = fn(img)
        np.testing.assert_allclose(out, [0.0])

    def test_window_missing_params_raises(self):
        with pytest.raises(ValueError, match="intensity_window_center"):
            create_intensity_fn("window")
        with pytest.raises(ValueError, match="intensity_window_center"):
            create_intensity_fn("window", window_center=10.0)

    # -- percentile ------------------------------------------------------------

    def test_percentile_basic(self):
        fn = create_intensity_fn("percentile", percentile_low=0.0, percentile_high=100.0)
        rng = np.random.default_rng(42)
        img = rng.integers(0, 255, size=(64, 64), dtype=np.uint8)
        out = fn(img)
        assert out.min() >= 0.0
        assert out.max() <= 1.0
        assert out.dtype == np.float32

    def test_percentile_constant_image(self):
        fn = create_intensity_fn("percentile", percentile_low=1.0, percentile_high=99.0)
        img = np.full((10, 10), 42, dtype=np.uint8)
        out = fn(img)
        np.testing.assert_allclose(out, 0.0)

    # -- range_scale -----------------------------------------------------------

    def test_range_scale_basic(self):
        """range_scale with finite min/max normalises to [0, 1]."""
        fn = create_intensity_fn("range_scale", scale_factor=2.0, min_value=0.0, max_value=500.0)
        img = np.array([0, 100, 300], dtype=np.float32)
        out = fn(img)
        # clamp(x * scale_factor, min, max) - min) / (max - min) → output in [0, 1].
        # clamp(x*2, 0, 500) → [0, 200, 500], then (v-0)/(500-0) → [0, 0.4, 1.0]
        np.testing.assert_allclose(out, [0.0, 0.4, 1.0])

    def test_range_scale_no_max(self):
        fn = create_intensity_fn("range_scale", scale_factor=0.5)
        img = np.array([100.0], dtype=np.float32)
        out = fn(img)
        np.testing.assert_allclose(out, [50.0])

    def test_range_scale_nonzero_min(self):
        """range_scale with nonzero min shifts and normalises."""
        fn = create_intensity_fn("range_scale", scale_factor=1.0, min_value=100.0, max_value=300.0)
        img = np.array([50, 200, 400], dtype=np.float32)
        out = fn(img)
        # clamp(x*1, 100, 300) → [100, 200, 300], then (v-100)/200 → [0.0, 0.5, 1.0]
        np.testing.assert_allclose(out, [0.0, 0.5, 1.0])

    def test_range_scale_min_equals_max(self):
        """When min == max, range_scale clamps without division."""
        fn = create_intensity_fn("range_scale", scale_factor=1.0, min_value=5.0, max_value=5.0)
        img = np.array([1.0, 5.0, 10.0], dtype=np.float32)
        out = fn(img)
        np.testing.assert_allclose(out, [5.0, 5.0, 5.0])

    # -- unknown ---------------------------------------------------------------

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown intensity mode"):
            create_intensity_fn("invalid_mode")


# ---------------------------------------------------------------------------
# InputTransform integration with intensity_fn
# ---------------------------------------------------------------------------


class TestInputTransformIntensity:
    def test_trivial_without_intensity(self):
        t = InputTransform()
        assert t.is_trivial
        img = np.ones((4, 4, 3), dtype=np.uint8) * 100
        np.testing.assert_array_equal(t(img), img)

    def test_not_trivial_with_intensity(self):
        fn = create_intensity_fn("scale_to_unit", max_value=255.0)
        t = InputTransform(intensity_fn=fn)
        assert not t.is_trivial
        img = np.ones((4, 4, 3), dtype=np.uint8) * 255
        out = t(img)
        np.testing.assert_allclose(out, 1.0)

    def test_intensity_before_mean_scale(self):
        """intensity_fn should run before mean/scale normalization."""
        fn = create_intensity_fn("scale_to_unit", max_value=255.0)
        t = InputTransform(
            mean_values=[0.5, 0.5, 0.5],
            scale_values=[0.5, 0.5, 0.5],
            intensity_fn=fn,
        )
        img = np.ones((2, 2, 3), dtype=np.uint8) * 255
        out = t(img)
        # scale_to_unit: 255/255=1.0, then (1.0-0.5)/0.5 = 1.0
        np.testing.assert_allclose(out, 1.0, atol=1e-6)

    def test_intensity_with_bgr2rgb(self):
        fn = create_intensity_fn("scale_to_unit", max_value=255.0)
        t = InputTransform(reverse_input_channels=True, intensity_fn=fn)
        # BGR [0, 0, 255] → after scale [0, 0, 1.0] → after BGR2RGB [1.0, 0, 0]
        img = np.zeros((1, 1, 3), dtype=np.uint8)
        img[0, 0, 2] = 255
        out = t(img)
        np.testing.assert_allclose(out[0, 0], [1.0, 0.0, 0.0], atol=1e-6)


# ---------------------------------------------------------------------------
# Parameter types new intensity parameters validation
# ---------------------------------------------------------------------------


class TestIntensityParameters:
    def test_input_dtype_string_value(self):
        from model_api.models.types import StringValue

        sv = StringValue(default_value="u8", choices=("u8", "f32", "u16", "i16"))
        assert sv.validate("u8") == []
        assert sv.validate("f32") == []
        assert sv.validate("u16") == []
        assert sv.validate("i16") == []
        assert len(sv.validate("i32")) > 0

    def test_intensity_mode_string_value(self):
        from model_api.models.types import StringValue

        sv = StringValue(
            default_value="none",
            choices=("none", "scale_to_unit", "window", "percentile", "range_scale"),
        )
        for mode in ("none", "scale_to_unit", "window", "percentile", "range_scale"):
            assert sv.validate(mode) == []
        assert len(sv.validate("bad")) > 0

    def test_intensity_max_value_none_default(self):
        from model_api.models.types import NumericalValue

        nv = NumericalValue(float, default_value=None, min=0.0)
        assert nv.default_value is None
        assert nv.from_str("None") is None
        assert nv.from_str("255.0") == 255.0

    def test_pad_value_max_65535(self):
        from model_api.models.parameters import ParameterRegistry

        pad = ParameterRegistry.IMAGE_RESIZE["pad_value"]
        assert pad.max == 65535


# ---------------------------------------------------------------------------
# Graph pad constant dtype
# ---------------------------------------------------------------------------


class TestGraphPadDtype:
    def test_letterbox_graph_u8(self):
        """Default u8 pad constant works as before."""
        import openvino as ov
        from model_api.adapters.utils import resize_image_letterbox
        from openvino.preprocess import PrePostProcessor

        model_h, model_w = 224, 224
        param_node = ov.op.Parameter(ov.Type.f32, ov.Shape([1, model_h, model_w, 3]))
        model = ov.Model(param_node, [param_node])
        ppp = PrePostProcessor(model)
        ppp.input().tensor().set_element_type(ov.Type.u8)
        ppp.input().tensor().set_layout(ov.Layout("NHWC"))
        ppp.input().tensor().set_shape([1, -1, -1, 3])
        ppp.input().preprocess().custom(
            resize_image_letterbox((model_h, model_w), "linear", 0, input_dtype="u8"),
        )
        ppp.input().preprocess().convert_element_type(ov.Type.f32)
        built = ppp.build()
        compiled = ov.Core().compile_model(built, "CPU")

        rng = np.random.default_rng(42)
        img = rng.integers(0, 255, size=(100, 200, 3), dtype=np.uint8)
        result = next(iter(compiled(img[None]).values()))
        assert result.shape == (1, model_h, model_w, 3)

    def test_letterbox_graph_u16(self):
        """u16 pad constant works for uint16 input."""
        import openvino as ov
        from model_api.adapters.utils import resize_image_letterbox
        from openvino.preprocess import PrePostProcessor

        model_h, model_w = 224, 224
        param_node = ov.op.Parameter(ov.Type.f32, ov.Shape([1, model_h, model_w, 3]))
        model = ov.Model(param_node, [param_node])
        ppp = PrePostProcessor(model)
        ppp.input().tensor().set_element_type(ov.Type.u16)
        ppp.input().tensor().set_layout(ov.Layout("NHWC"))
        ppp.input().tensor().set_shape([1, -1, -1, 3])
        ppp.input().preprocess().custom(
            resize_image_letterbox((model_h, model_w), "linear", 0, input_dtype="u16"),
        )
        ppp.input().preprocess().convert_element_type(ov.Type.f32)
        built = ppp.build()
        compiled = ov.Core().compile_model(built, "CPU")

        rng = np.random.default_rng(42)
        img = rng.integers(0, 65535, size=(100, 200, 3), dtype=np.uint16)
        result = next(iter(compiled(img[None]).values()))
        assert result.shape == (1, model_h, model_w, 3)

    def test_pad_value_over_255_u16(self):
        """pad_value > 255 is valid for u16 input."""
        import openvino as ov
        from model_api.adapters.utils import resize_image_with_aspect
        from openvino.preprocess import PrePostProcessor

        model_h, model_w = 64, 64
        param_node = ov.op.Parameter(ov.Type.f32, ov.Shape([1, model_h, model_w, 3]))
        model = ov.Model(param_node, [param_node])
        ppp = PrePostProcessor(model)
        ppp.input().tensor().set_element_type(ov.Type.u16)
        ppp.input().tensor().set_layout(ov.Layout("NHWC"))
        ppp.input().tensor().set_shape([1, -1, -1, 3])
        ppp.input().preprocess().custom(
            resize_image_with_aspect((model_h, model_w), "linear", 1000, input_dtype="u16"),
        )
        ppp.input().preprocess().convert_element_type(ov.Type.f32)
        built = ppp.build()
        compiled = ov.Core().compile_model(built, "CPU")

        rng = np.random.default_rng(42)
        img = rng.integers(0, 65535, size=(32, 100, 3), dtype=np.uint16)
        result = next(iter(compiled(img[None]).values()))
        assert result.shape == (1, model_h, model_w, 3)
        # Image is 32x100, aspect-scaled: scale=min(64/100,64/32)=0.64 → ~20x64
        # Padding is at the bottom rows. Check last row (padded).
        assert result[0, -1, 0, 0] == 1000.0


# ---------------------------------------------------------------------------
# Backward compatibility defaults preserve current behavior
# ---------------------------------------------------------------------------


class TestBackwardCompat:
    def test_default_intensity_params(self):
        from model_api.models.parameters import ParameterRegistry

        pp = ParameterRegistry.IMAGE_PREPROCESSING
        assert pp["input_dtype"].default_value == "u8"
        assert pp["intensity_mode"].default_value == "none"
        assert pp["intensity_max_value"].default_value is None
        assert pp["intensity_percentile_low"].default_value == 1.0
        assert pp["intensity_percentile_high"].default_value == 99.0
        assert pp["intensity_scale_factor"].default_value == 1.0
        assert pp["intensity_min_value"].default_value == 0.0

    def test_input_transform_backward_compat(self):
        """InputTransform without intensity_fn behaves exactly as before."""
        t_old = InputTransform(
            reverse_input_channels=True,
            mean_values=[0.485, 0.456, 0.406],
            scale_values=[0.229, 0.224, 0.225],
        )
        t_new = InputTransform(
            reverse_input_channels=True,
            mean_values=[0.485, 0.456, 0.406],
            scale_values=[0.229, 0.224, 0.225],
            intensity_fn=None,
        )
        rng = np.random.default_rng(42)
        img = rng.integers(0, 255, size=(16, 16, 3), dtype=np.uint8)
        np.testing.assert_array_equal(t_old(img), t_new(img))


# ---------------------------------------------------------------------------
# repeat_channels helpers
# ---------------------------------------------------------------------------


class TestRepeatChannels:
    """Tests for _repeat_single_channel helpers (Python-side and OV graph)."""

    def test_hw_to_hwc3(self):
        """HxW grayscale image is expanded to HxWx3."""
        from model_api.models.image_model import _repeat_single_channel

        img = np.arange(12, dtype=np.uint8).reshape(3, 4)
        out = _repeat_single_channel(img)
        assert out.shape == (3, 4, 3)
        np.testing.assert_array_equal(out[:, :, 0], img)
        np.testing.assert_array_equal(out[:, :, 1], img)
        np.testing.assert_array_equal(out[:, :, 2], img)

    def test_hwc1_to_hwc3(self):
        """HxWx1 image is expanded to HxWx3."""
        from model_api.models.image_model import _repeat_single_channel

        img = np.arange(6, dtype=np.uint16).reshape(2, 3, 1)
        out = _repeat_single_channel(img)
        assert out.shape == (2, 3, 3)
        np.testing.assert_array_equal(out[:, :, 0], img[:, :, 0])

    def test_3ch_noop(self):
        """Already 3-channel image passes through unchanged."""
        from model_api.models.image_model import _repeat_single_channel

        img = np.ones((4, 4, 3), dtype=np.float32) * 42.0
        out = _repeat_single_channel(img)
        np.testing.assert_array_equal(out, img)

    def test_utils_repeat_hw(self):
        """utils._repeat_single_channel_np works for HxW input."""
        from model_api.adapters.utils import _repeat_single_channel_np

        img = np.array([[10, 20], [30, 40]], dtype=np.int16)
        out = _repeat_single_channel_np(img)
        assert out.shape == (2, 2, 3)
        np.testing.assert_array_equal(out[:, :, 0], img)

    def test_utils_repeat_3ch_noop(self):
        """utils._repeat_single_channel_np is a no-op for 3ch."""
        from model_api.adapters.utils import _repeat_single_channel_np

        img = np.zeros((2, 2, 3), dtype=np.uint8)
        out = _repeat_single_channel_np(img)
        assert out is img

    def test_ov_graph_repeat(self):
        """OV graph repeat_channels_preprocess tiles 1ch→3ch."""
        import openvino as ov
        from model_api.adapters.utils import repeat_channels_preprocess
        from openvino.preprocess import PrePostProcessor

        model_h, model_w = 4, 4
        param_node = ov.op.Parameter(ov.Type.f32, ov.Shape([1, model_h, model_w, 3]))
        model = ov.Model(param_node, [param_node])
        ppp = PrePostProcessor(model)
        ppp.input().tensor().set_element_type(ov.Type.u8)
        ppp.input().tensor().set_layout(ov.Layout("NHWC"))
        ppp.input().tensor().set_shape([1, model_h, model_w, 1])
        ppp.input().preprocess().custom(repeat_channels_preprocess())
        ppp.input().preprocess().convert_element_type(ov.Type.f32)
        built = ppp.build()
        compiled = ov.Core().compile_model(built, "CPU")

        img = np.arange(16, dtype=np.uint8).reshape(1, 4, 4, 1)
        result = next(iter(compiled(img).values()))
        assert result.shape == (1, model_h, model_w, 3)
        # Each channel should equal the original single channel
        np.testing.assert_array_equal(result[0, :, :, 0], result[0, :, :, 1])
        np.testing.assert_array_equal(result[0, :, :, 0], result[0, :, :, 2])
        np.testing.assert_allclose(result[0, :, :, 0], img[0, :, :, 0].astype(np.float32))

    def test_parameter_default_false(self):
        """intensity_repeat_channels defaults to False."""
        from model_api.models.parameters import ParameterRegistry

        pp = ParameterRegistry.IMAGE_PREPROCESSING
        assert "intensity_repeat_channels" in pp
        assert pp["intensity_repeat_channels"].default_value is False


# ---------------------------------------------------------------------------
# i16 (int16) dtype support
# ---------------------------------------------------------------------------


class TestInt16Support:
    def test_input_dtype_accepts_i16(self):
        """ParameterRegistry accepts i16 as a valid input_dtype."""
        from model_api.models.parameters import ParameterRegistry

        pp = ParameterRegistry.IMAGE_PREPROCESSING
        sv = pp["input_dtype"]
        assert sv.validate("i16") == []

    def test_numpy_dtype_map_has_i16(self):
        from model_api.adapters.utils import _NUMPY_DTYPE_MAP

        assert "i16" in _NUMPY_DTYPE_MAP
        assert _NUMPY_DTYPE_MAP["i16"] is np.int16

    def test_scale_to_unit_i16(self):
        """scale_to_unit works with int16 input."""
        fn = create_intensity_fn("scale_to_unit", max_value=32767.0)
        img = np.array([-1000, 0, 16383, 32767], dtype=np.int16)
        out = fn(img)
        np.testing.assert_allclose(out, img.astype(np.float32) / 32767.0, atol=1e-6)

    def test_ov_graph_i16_element_type(self):
        """OV PrePostProcessor accepts i16 element type."""
        import openvino as ov
        from openvino.preprocess import PrePostProcessor

        model_h, model_w = 4, 4
        param_node = ov.op.Parameter(ov.Type.f32, ov.Shape([1, model_h, model_w, 3]))
        model = ov.Model(param_node, [param_node])
        ppp = PrePostProcessor(model)
        ppp.input().tensor().set_element_type(ov.Type.i16)
        ppp.input().tensor().set_layout(ov.Layout("NHWC"))
        ppp.input().preprocess().convert_element_type(ov.Type.f32)
        built = ppp.build()
        compiled = ov.Core().compile_model(built, "CPU")

        img = np.arange(-24, 24, dtype=np.int16).reshape(1, model_h, model_w, 3)
        result = next(iter(compiled(img).values()))
        np.testing.assert_allclose(result, img.astype(np.float32))
