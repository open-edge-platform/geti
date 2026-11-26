# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import numpy as np
import pytest
from model_api.adapters.utils import (
    InputTransform,
    Layout,
    _repeat_single_channel_np,
    change_layout,
    create_intensity_fn,
    crop_resize_ocv,
    get_rt_info_from_dict,
    load_parameters_from_onnx,
    resize_image_letterbox_ocv,
    resize_image_ocv,
    resize_image_with_aspect_ocv,
    setup_python_preprocessing_pipeline,
)

# --- Layout ---


def test_layout_init():
    layout = Layout("NCHW")
    assert layout.layout == "NCHW"


def test_layout_from_shape_2d():
    assert Layout.from_shape((1, 3)) == "NC"


def test_layout_from_shape_3d_chw():
    assert Layout.from_shape((3, 224, 224)) == "CHW"


def test_layout_from_shape_3d_hwc():
    assert Layout.from_shape((224, 224, 3)) == "HWC"


def test_layout_from_shape_4d_nchw():
    assert Layout.from_shape((1, 3, 224, 224)) == "NCHW"


def test_layout_from_shape_4d_nhwc():
    assert Layout.from_shape((1, 224, 224, 3)) == "NHWC"


def test_layout_from_shape_unsupported():
    with pytest.raises(RuntimeError, match="doesn't support"):
        Layout.from_shape((1, 2, 3, 4, 5))


def test_layout_from_shape_6d():
    assert Layout.from_shape((1, 2, 3, 4, 5, 3)) == "NSTHWC"


def test_layout_parse_layouts_empty():
    assert Layout.parse_layouts("") is None


def test_layout_parse_layouts_single():
    result = Layout.parse_layouts("NCHW")
    assert result == {"": "NCHW"}


def test_layout_parse_layouts_named():
    result = Layout.parse_layouts("input0:NCHW")
    assert result == {"input0": "NCHW"}


def test_layout_parse_layouts_multiple():
    result = Layout.parse_layouts("input0:NCHW,input1:NC")
    assert result == {"input0": "NCHW", "input1": "NC"}


def test_layout_from_user_layouts():
    layouts = {"input0": "NCHW", "input1": "NC"}
    assert Layout.from_user_layouts({"input0"}, layouts) == "NCHW"
    assert Layout.from_user_layouts({"input1"}, layouts) == "NC"
    assert Layout.from_user_layouts({"unknown"}, layouts) == ""


def test_layout_from_user_layouts_default():
    layouts = {"": "NHWC"}
    assert Layout.from_user_layouts({"unknown"}, layouts) == "NHWC"


# --- resize functions ---


def test_resize_image_ocv_standard():
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    result = resize_image_ocv(img, (50, 50))
    assert result.shape == (50, 50, 3)


def test_resize_image_ocv_keep_aspect():
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    result = resize_image_ocv(img, (50, 50), keep_aspect_ratio=True)
    assert result.shape[1] == 50 or result.shape[0] == 50


def test_resize_image_ocv_keep_aspect_pad():
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    result = resize_image_ocv(img, (100, 100), keep_aspect_ratio=True, is_pad=True, pad_value=128)
    assert result.shape[0] == 100
    assert result.shape[1] == 100


def test_resize_image_with_aspect_ocv():
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    result = resize_image_with_aspect_ocv(img, (50, 50))
    assert result.shape[0] == 50
    assert result.shape[1] == 50


def test_resize_image_letterbox_ocv():
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    result = resize_image_letterbox_ocv(img, (100, 100))
    assert result.shape == (100, 100, 3)


def test_crop_resize_ocv_square():
    img = np.zeros((200, 100, 3), dtype=np.uint8)
    result = crop_resize_ocv(img, (50, 50))
    assert result.shape == (50, 50, 3)


def test_crop_resize_ocv_wider():
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    result = crop_resize_ocv(img, (50, 50))
    assert result.shape == (50, 50, 3)


def test_crop_resize_ocv_tall_aspect():
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    result = crop_resize_ocv(img, (100, 50))  # w/h < 1
    assert result.shape == (50, 100, 3)


def test_crop_resize_ocv_wide_aspect():
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    result = crop_resize_ocv(img, (50, 100))  # w/h > 1
    assert result.shape == (100, 50, 3)


# --- change_layout ---


def test_change_layout_chw():
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    result = change_layout(img, "NCHW")
    assert result.shape == (1, 3, 224, 224)


def test_change_layout_hwc():
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    result = change_layout(img, "NHWC")
    assert result.shape == (224, 224, 3)


# --- _repeat_single_channel_np ---


def test_repeat_single_channel_2d():
    img = np.zeros((10, 10), dtype=np.uint8)
    result = _repeat_single_channel_np(img)
    assert result.shape == (10, 10, 3)


def test_repeat_single_channel_3d_single():
    img = np.zeros((10, 10, 1), dtype=np.uint8)
    result = _repeat_single_channel_np(img)
    assert result.shape == (10, 10, 3)


def test_repeat_single_channel_3d_three():
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    result = _repeat_single_channel_np(img)
    assert result.shape == (10, 10, 3)
    assert result is img  # no copy


# --- InputTransform ---


def test_input_transform_trivial():
    t = InputTransform()
    assert t.is_trivial is True
    img = np.ones((10, 10, 3), dtype=np.float32)
    result = t(img)
    np.testing.assert_array_equal(result, img)


def test_input_transform_with_mean_scale():
    t = InputTransform(mean_values=[0.5, 0.5, 0.5], scale_values=[2.0, 2.0, 2.0])
    assert t.is_trivial is False
    img = np.ones((10, 10, 3), dtype=np.float32)
    result = t(img)
    expected = (img - 0.5) / 2.0
    np.testing.assert_array_almost_equal(result, expected)


def test_input_transform_reverse_channels():
    t = InputTransform(reverse_input_channels=True)
    assert t.is_trivial is False


def test_input_transform_with_intensity_fn():
    def scale_fn(img):
        return img / 255.0

    t = InputTransform(intensity_fn=scale_fn)
    assert t.is_trivial is False
    img = np.full((10, 10, 3), 255.0, dtype=np.float32)
    result = t(img)
    np.testing.assert_array_almost_equal(result, np.ones((10, 10, 3)))


# --- create_intensity_fn ---


def test_create_intensity_fn_none():
    result = create_intensity_fn("none")
    assert result is None


def test_create_intensity_fn_scale_to_unit():
    fn = create_intensity_fn("scale_to_unit", max_value=255.0)
    img = np.full((2, 2), 255, dtype=np.uint8)
    result = fn(img)
    np.testing.assert_array_almost_equal(result, np.ones((2, 2)))


def test_create_intensity_fn_scale_to_unit_no_max():
    with pytest.raises(ValueError, match="intensity_max_value is required"):
        create_intensity_fn("scale_to_unit")


def test_create_intensity_fn_window():
    fn = create_intensity_fn("window", window_center=128.0, window_width=256.0)
    assert fn is not None
    img = np.array([[0, 128, 255]], dtype=np.float32)
    result = fn(img)
    assert result[0, 0] == pytest.approx(0.0)
    assert result[0, 1] == pytest.approx(0.5)


def test_create_intensity_fn_window_missing_params():
    with pytest.raises(ValueError, match="intensity_window_center"):
        create_intensity_fn("window")


def test_create_intensity_fn_percentile():
    fn = create_intensity_fn("percentile", percentile_low=0.0, percentile_high=100.0)
    img = np.array([[0, 50, 100]], dtype=np.float32)
    result = fn(img)
    assert result[0, 0] == pytest.approx(0.0)
    assert result[0, 2] == pytest.approx(1.0)


def test_create_intensity_fn_range_scale():
    fn = create_intensity_fn("range_scale", scale_factor=1.0, min_value=0.0, max_value=100.0)
    img = np.array([[0, 50, 100]], dtype=np.float32)
    result = fn(img)
    assert result[0, 0] == pytest.approx(0.0)
    assert result[0, 2] == pytest.approx(1.0)


def test_create_intensity_fn_range_scale_no_max():
    fn = create_intensity_fn("range_scale", scale_factor=2.0, min_value=0.0)
    assert fn is not None


def test_create_intensity_fn_unknown():
    with pytest.raises(ValueError, match="Unknown intensity mode"):
        create_intensity_fn("unknown_mode")


# --- setup_python_preprocessing_pipeline ---


def test_setup_python_preprocessing_standard():
    fn = setup_python_preprocessing_pipeline(
        layout="NCHW",
        resize_mode="standard",
        interpolation_mode="LINEAR",
        target_shape=(224, 224),
        pad_value=0,
    )
    img = np.zeros((1, 100, 200, 3), dtype=np.uint8)
    result = fn(img)
    assert result.shape[1] == 3  # CHW


def test_setup_python_preprocessing_letterbox():
    fn = setup_python_preprocessing_pipeline(
        layout="NHWC",
        resize_mode="fit_to_window_letterbox",
        interpolation_mode="LINEAR",
        target_shape=(100, 100),
        pad_value=128,
    )
    img = np.zeros((1, 50, 100, 3), dtype=np.uint8)
    result = fn(img)
    assert result.shape[-1] == 3


def test_setup_python_preprocessing_crop():
    fn = setup_python_preprocessing_pipeline(
        layout="NCHW",
        resize_mode="crop",
        interpolation_mode="LINEAR",
        target_shape=(50, 50),
        pad_value=0,
    )
    img = np.zeros((1, 100, 100, 3), dtype=np.uint8)
    result = fn(img)
    assert result.ndim == 4


def test_setup_python_preprocessing_fit_to_window():
    fn = setup_python_preprocessing_pipeline(
        layout="NCHW",
        resize_mode="fit_to_window",
        interpolation_mode="LINEAR",
        target_shape=(100, 100),
        pad_value=0,
    )
    img = np.zeros((1, 50, 100, 3), dtype=np.uint8)
    result = fn(img)
    assert result.ndim == 4


def test_setup_python_preprocessing_with_repeat_channels():
    fn = setup_python_preprocessing_pipeline(
        layout="NCHW",
        resize_mode="standard",
        interpolation_mode="LINEAR",
        target_shape=(50, 50),
        pad_value=0,
        intensity_repeat_channels=True,
    )
    img = np.zeros((1, 100, 100, 1), dtype=np.uint8)
    result = fn(img)
    assert result.shape[1] == 3


# --- load_parameters_from_onnx ---


def test_load_parameters_from_onnx_basic():
    prop1 = SimpleNamespace(key="model_info labels", value="cat dog")
    prop2 = SimpleNamespace(key="other_key data", value="ignored")
    prop3 = SimpleNamespace(key="model_info task", value="detection")
    onnx_model = SimpleNamespace(metadata_props=[prop1, prop2, prop3])
    result = load_parameters_from_onnx(onnx_model)
    assert "model_info" in result
    assert result["model_info"]["labels"] == "cat dog"
    assert result["model_info"]["task"] == "detection"


def test_load_parameters_from_onnx_empty():
    onnx_model = SimpleNamespace(metadata_props=[])
    result = load_parameters_from_onnx(onnx_model)
    assert result == {}


# --- get_rt_info_from_dict ---


def test_get_rt_info_from_dict_success():
    rt_info = {"model_info": {"labels": "cat dog"}}
    result = get_rt_info_from_dict(rt_info, ["model_info", "labels"])
    assert result.astype(str) == "cat dog"


def test_get_rt_info_from_dict_error():
    rt_info = {"model_info": {}}
    with pytest.raises(RuntimeError, match="Cannot get runtime attribute"):
        get_rt_info_from_dict(rt_info, ["model_info", "nonexistent"])
