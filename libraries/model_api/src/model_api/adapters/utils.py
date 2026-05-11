#
# Copyright (C) 2020-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import math
from functools import partial
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np
from openvino import Input, Model, Node, Output, OVAny, Type, layout_helpers
from openvino import opset10 as opset
from openvino.utils.decorators import custom_preprocess_function

if TYPE_CHECKING:
    from collections.abc import Callable


# Mapping from input_dtype string to numpy dtype for pad constants in OV graph helpers
_NUMPY_DTYPE_MAP: dict[str, type] = {
    "u8": np.uint8,
    "u16": np.uint16,
    "i16": np.int16,
    "f32": np.float32,
}


class Layout:
    def __init__(self, layout: str = "") -> None:
        self.layout = layout

    @staticmethod
    def from_shape(shape: list[int] | tuple[int, ...]) -> str:
        """Create Layout from given shape"""
        if len(shape) == 2:
            return "NC"
        if len(shape) == 3:
            return "CHW" if shape[0] in range(1, 5) else "HWC"
        if len(shape) == 4:
            return "NCHW" if shape[1] in range(1, 5) else "NHWC"
        if len(shape) == 6:
            return "NSTHWC" if shape[5] in range(1, 5) else "NSCTHW"

        msg = f"Get layout from shape method doesn't support {len(shape)}D shape"
        raise RuntimeError(msg)

    @staticmethod
    def from_openvino(input: Input):
        """Create Layout from openvino input"""
        return layout_helpers.get_layout(input).to_string().strip("[]").replace(",", "")

    @staticmethod
    def from_user_layouts(input_names: set, user_layouts: dict):
        """Create Layout for input based on user info"""
        for input_name in input_names:
            if input_name in user_layouts:
                return user_layouts[input_name]
        return user_layouts.get("", "")

    @staticmethod
    def parse_layouts(layout_string: str) -> dict | None:
        """Parse layout parameter in format "input0:NCHW,input1:NC" or "NCHW" (applied to all inputs)"""
        if not layout_string:
            return None
        search_string = layout_string if layout_string.rfind(":") != -1 else ":" + layout_string
        colon_pos = search_string.rfind(":")
        user_layouts = {}
        while colon_pos != -1:
            start_pos = search_string.rfind(",")
            input_name = search_string[start_pos + 1 : colon_pos]
            input_layout = search_string[colon_pos + 1 :]
            user_layouts[input_name] = input_layout
            search_string = search_string[: start_pos + 1]
            if search_string == "" or search_string[-1] != ",":
                break
            search_string = search_string[:-1]
            colon_pos = search_string.rfind(":")
        if search_string != "":
            raise ValueError("Can't parse input layout string: " + layout_string)
        return user_layouts


def resize_image_letterbox_graph(
    input: Output,
    size: tuple[int, int],
    interpolation: str,
    pad_value: int,
    input_dtype: str = "u8",
) -> Node:
    if not 0 <= pad_value <= 65535:
        msg = "pad_value must be in range [0, 65535]"
        raise RuntimeError(msg)
    w, h = size
    h_axis = 1
    w_axis = 2

    # OV Interpolate requires float input for non-u8 types
    if input_dtype != "u8":
        input = opset.convert(input, destination_type="f32")

    image_shape = opset.shape_of(input, name="shape")
    iw = opset.convert(
        opset.gather(image_shape, opset.constant(w_axis), axis=0),
        destination_type="f32",
    )
    ih = opset.convert(
        opset.gather(image_shape, opset.constant(h_axis), axis=0),
        destination_type="f32",
    )
    w_ratio = opset.divide(opset.constant(w, dtype=Type.f32), iw)
    h_ratio = opset.divide(opset.constant(h, dtype=Type.f32), ih)
    scale = opset.minimum(w_ratio, h_ratio)
    nw = opset.convert(
        opset.round(opset.multiply(iw, scale), "half_to_even"),
        destination_type="i32",
    )
    nh = opset.convert(
        opset.round(opset.multiply(ih, scale), "half_to_even"),
        destination_type="i32",
    )
    new_size = opset.concat([opset.unsqueeze(nh, 0), opset.unsqueeze(nw, 0)], axis=0)
    image = opset.interpolate(
        input,
        new_size,
        scales=np.array([0.0, 0.0], dtype=np.float32),
        axes=[h_axis, w_axis],
        mode=interpolation,
        shape_calculation_mode="sizes",
    )
    dx = opset.divide(
        opset.subtract(opset.constant(w, dtype=np.int32), nw),
        opset.constant(2, dtype=np.int32),
    )
    dy = opset.divide(
        opset.subtract(opset.constant(h, dtype=np.int32), nh),
        opset.constant(2, dtype=np.int32),
    )
    dx_border = opset.subtract(
        opset.subtract(opset.constant(w, dtype=np.int32), nw),
        dx,
    )
    dy_border = opset.subtract(
        opset.subtract(opset.constant(h, dtype=np.int32), nh),
        dy,
    )
    pads_begin = opset.concat(
        [
            opset.constant([0], dtype=np.int32),
            opset.unsqueeze(dy, 0),
            opset.unsqueeze(dx, 0),
            opset.constant([0], dtype=np.int32),
        ],
        axis=0,
    )
    pads_end = opset.concat(
        [
            opset.constant([0], dtype=np.int32),
            opset.unsqueeze(dy_border, 0),
            opset.unsqueeze(dx_border, 0),
            opset.constant([0], dtype=np.int32),
        ],
        axis=0,
    )
    return opset.pad(
        image,
        pads_begin,
        pads_end,
        "constant",
        opset.constant(
            pad_value,
            dtype=np.float32 if input_dtype != "u8" else _NUMPY_DTYPE_MAP.get(input_dtype, np.uint8),
        ),
    )


def crop_resize_graph(input: Output, size: tuple[int, int], input_dtype: str = "u8") -> Node:
    h_axis = 1
    w_axis = 2
    desired_aspect_ratio = size[1] / size[0]  # width / height

    image_shape = opset.shape_of(input, name="shape")
    iw = opset.convert(
        opset.gather(image_shape, opset.constant(w_axis), axis=0),
        destination_type="i32",
    )
    ih = opset.convert(
        opset.gather(image_shape, opset.constant(h_axis), axis=0),
        destination_type="i32",
    )

    if desired_aspect_ratio == 1:
        # then_body
        _np_dtype = _NUMPY_DTYPE_MAP.get(input_dtype, np.uint8)
        image_t = opset.parameter([-1, -1, -1, 3], _np_dtype, "image")
        iw_t = opset.parameter([], np.int32, "iw")
        ih_t = opset.parameter([], np.int32, "ih")
        then_offset = opset.unsqueeze(
            opset.divide(opset.subtract(ih_t, iw_t), opset.constant(2, dtype=np.int32)),
            0,
        )
        then_stop = opset.add(then_offset, iw_t)
        then_cropped_frame = opset.slice(
            image_t,
            start=then_offset,
            stop=then_stop,
            step=[1],
            axes=[h_axis],
        )
        then_body_res_1 = opset.result(then_cropped_frame)
        then_body = Model(
            [then_body_res_1],
            [image_t, iw_t, ih_t],
            "then_body_function",
        )

        # else_body
        image_e = opset.parameter([-1, -1, -1, 3], _np_dtype, "image")
        iw_e = opset.parameter([], np.int32, "iw")
        ih_e = opset.parameter([], np.int32, "ih")
        else_offset = opset.unsqueeze(
            opset.divide(opset.subtract(iw_e, ih_e), opset.constant(2, dtype=np.int32)),
            0,
        )
        else_stop = opset.add(else_offset, ih_e)
        else_cropped_frame = opset.slice(
            image_e,
            start=else_offset,
            stop=else_stop,
            step=[1],
            axes=[w_axis],
        )
        else_body_res_1 = opset.result(else_cropped_frame)
        else_body = Model(
            [else_body_res_1],
            [image_e, iw_e, ih_e],
            "else_body_function",
        )

        # if
        condition = opset.greater(ih, iw)
        if_node = opset.if_op(condition.output(0))
        if_node.set_then_body(then_body)
        if_node.set_else_body(else_body)
        if_node.set_input(input, image_t, image_e)
        if_node.set_input(iw.output(0), iw_t, iw_e)
        if_node.set_input(ih.output(0), ih_t, ih_e)
        cropped_frame = if_node.set_output(then_body_res_1, else_body_res_1)

    elif desired_aspect_ratio < 1:
        new_width = opset.floor(
            opset.multiply(
                opset.convert(ih, destination_type="f32"),
                desired_aspect_ratio,
            ),
        )
        offset = opset.unsqueeze(
            opset.divide(
                opset.subtract(iw, new_width),
                opset.constant(2, dtype=np.int32),
            ),
            0,
        )
        stop = opset.add(offset, new_width)
        cropped_frame = opset.slice(
            input,
            start=offset,
            stop=stop,
            step=[1],
            axes=[w_axis],
        )
    elif desired_aspect_ratio > 1:
        new_hight = opset.floor(
            opset.multiply(
                opset.convert(iw, destination_type="f32"),
                desired_aspect_ratio,
            ),
        )
        offset = opset.unsqueeze(
            opset.divide(
                opset.subtract(ih, new_hight),
                opset.constant(2, dtype=np.int32),
            ),
            0,
        )
        stop = opset.add(offset, new_hight)
        cropped_frame = opset.slice(
            input,
            start=offset,
            stop=stop,
            step=[1],
            axes=[h_axis],
        )

    target_size = list(size)
    target_size.reverse()
    return opset.interpolate(
        cropped_frame,
        target_size,
        scales=np.array([0.0, 0.0], dtype=np.float32),
        axes=[h_axis, w_axis],
        mode="linear",
        shape_calculation_mode="sizes",
    )


def resize_image_graph(
    input: Output,
    size: tuple[int, int],
    keep_aspect_ratio: bool,
    interpolation: str,
    pad_value: int,
    input_dtype: str = "u8",
) -> Node:
    if not 0 <= pad_value <= 65535:
        msg = "pad_value must be in range [0, 65535]"
        raise RuntimeError(msg)
    h_axis = 1
    w_axis = 2
    w, h = size

    # OV Interpolate requires float input for non-u8 types
    if input_dtype != "u8":
        input = opset.convert(input, destination_type="f32")

    target_size = list(size)
    target_size.reverse()

    if not keep_aspect_ratio:
        return opset.interpolate(
            input,
            target_size,
            scales=np.array([0.0, 0.0], dtype=np.float32),
            axes=[h_axis, w_axis],
            mode=interpolation,
            shape_calculation_mode="sizes",
        )
    image_shape = opset.shape_of(input, name="shape")
    iw = opset.convert(
        opset.gather(image_shape, opset.constant(w_axis), axis=0),
        destination_type="f32",
    )
    ih = opset.convert(
        opset.gather(image_shape, opset.constant(h_axis), axis=0),
        destination_type="f32",
    )
    w_ratio = opset.divide(np.float32(w), iw)
    h_ratio = opset.divide(np.float32(h), ih)
    scale = opset.minimum(w_ratio, h_ratio)
    nw = opset.convert(
        opset.round(opset.multiply(iw, scale), "half_to_even"),
        destination_type="i32",
    )
    nh = opset.convert(
        opset.round(opset.multiply(ih, scale), "half_to_even"),
        destination_type="i32",
    )
    new_size = opset.concat([opset.unsqueeze(nh, 0), opset.unsqueeze(nw, 0)], axis=0)
    image = opset.interpolate(
        input,
        new_size,
        scales=np.array([0.0, 0.0], dtype=np.float32),
        axes=[h_axis, w_axis],
        mode=interpolation,
        shape_calculation_mode="sizes",
    )
    dx_border = opset.subtract(opset.constant(w, dtype=np.int32), nw)
    dy_border = opset.subtract(opset.constant(h, dtype=np.int32), nh)
    pads_begin = np.array([0, 0, 0, 0], np.int32)
    pads_end = opset.concat(
        [
            opset.constant([0], dtype=np.int32),
            opset.unsqueeze(dy_border, 0),
            opset.unsqueeze(dx_border, 0),
            opset.constant([0], dtype=np.int32),
        ],
        axis=0,
    )
    return opset.pad(
        image,
        pads_begin,
        pads_end,
        "constant",
        opset.constant(
            pad_value,
            dtype=np.float32 if input_dtype != "u8" else _NUMPY_DTYPE_MAP.get(input_dtype, np.uint8),
        ),
    )


def resize_image(
    size: tuple[int, int],
    interpolation: str,
    pad_value: int,
    input_dtype: str = "u8",
) -> Callable:
    return custom_preprocess_function(
        partial(
            resize_image_graph,
            size=size,
            keep_aspect_ratio=False,
            interpolation=interpolation,
            pad_value=pad_value,
            input_dtype=input_dtype,
        ),
    )


def resize_image_with_aspect(
    size: tuple[int, int],
    interpolation: str,
    pad_value: int,
    input_dtype: str = "u8",
) -> Callable:
    return custom_preprocess_function(
        partial(
            resize_image_graph,
            size=size,
            keep_aspect_ratio=True,
            interpolation=interpolation,
            pad_value=pad_value,
            input_dtype=input_dtype,
        ),
    )


def crop_resize(
    size: tuple[int, int],
    interpolation: str,
    pad_value: int,
    input_dtype: str = "u8",
) -> Callable:
    return custom_preprocess_function(partial(crop_resize_graph, size=size, input_dtype=input_dtype))


def resize_image_letterbox(
    size: tuple[int, int],
    interpolation: str,
    pad_value: int,
    input_dtype: str = "u8",
) -> Callable:
    return custom_preprocess_function(
        partial(
            resize_image_letterbox_graph,
            size=size,
            interpolation=interpolation,
            pad_value=pad_value,
            input_dtype=input_dtype,
        ),
    )


def window_preprocess_graph(
    output: Output,
    *,
    window_center: float,
    window_width: float,
) -> Node:
    """OV graph: window intensity scaling [center-width/2, center+width/2] to [0, 1]."""
    low = window_center - window_width / 2.0
    span = window_width
    return opset.clamp(
        opset.divide(
            opset.subtract(
                opset.convert(output, destination_type="f32"),
                opset.constant(low, dtype=Type.f32),
            ),
            opset.constant(span, dtype=Type.f32),
        ),
        opset.constant(0.0, dtype=Type.f32),
        opset.constant(1.0, dtype=Type.f32),
    )


def window_preprocess(
    window_center: float,
    window_width: float,
) -> Callable:
    """Return an OV custom preprocess function for window intensity scaling."""
    return custom_preprocess_function(
        partial(
            window_preprocess_graph,
            window_center=window_center,
            window_width=window_width,
        ),
    )


def range_scale_preprocess_graph(
    output: Output,
    *,
    scale_factor: float,
    min_value: float,
    max_value: float,
) -> Node:
    """OV graph: range_scale intensity scaling.

    Multiplies by *scale_factor*, clamps to [min_value, max_value], then
    normalises to [0, 1] via ``(clamped - min) / (max - min)``.
    """
    clamped = opset.clamp(
        opset.multiply(
            opset.convert(output, destination_type="f32"),
            opset.constant(scale_factor, dtype=Type.f32),
        ),
        opset.constant(min_value, dtype=Type.f32),
        opset.constant(max_value, dtype=Type.f32),
    )
    range = max_value - min_value
    if range == 0:
        return clamped
    return opset.divide(
        opset.subtract(clamped, opset.constant(min_value, dtype=Type.f32)),
        opset.constant(range, dtype=Type.f32),
    )


def range_scale_preprocess(
    scale_factor: float,
    min_value: float,
    max_value: float,
) -> Callable:
    """Return an OV custom preprocess function for range_scale intensity scaling."""
    return custom_preprocess_function(
        partial(
            range_scale_preprocess_graph,
            scale_factor=scale_factor,
            min_value=min_value,
            max_value=max_value,
        ),
    )


def repeat_channels_preprocess_graph(output: Output) -> Node:
    """OV graph: tile a single-channel tensor to 3 channels along the last axis."""
    return opset.tile(output, opset.constant([1, 1, 1, 3]))


def repeat_channels_preprocess() -> Callable:
    """Return an OV custom preprocess function that repeats 1 channel to 3."""
    return custom_preprocess_function(repeat_channels_preprocess_graph)


def load_parameters_from_onnx(onnx_model: Any) -> dict[str, Any]:
    parameters: dict[str, Any] = {}

    def insert_hierarchical(keys, val, root_dict):
        if len(keys) == 1:
            root_dict[keys[0]] = val
            return
        if keys[0] not in root_dict:
            root_dict[keys[0]] = {}
        insert_hierarchical(keys[1:], val, root_dict[keys[0]])

    for prop in onnx_model.metadata_props:
        keys = prop.key.split()
        if "model_info" in keys:
            insert_hierarchical(keys, prop.value, parameters)

    return parameters


def get_rt_info_from_dict(rt_info_dict: dict[str, Any], path: list[str]) -> OVAny:
    value = rt_info_dict
    try:
        value = rt_info_dict
        for item in path:
            value = value[item]
        return OVAny(value)
    except KeyError:
        msg = "Cannot get runtime attribute. Path to runtime attribute is incorrect."
        raise RuntimeError(msg)


def resize_image_ocv(
    image: np.ndarray,
    size: tuple[int, int],
    keep_aspect_ratio: bool = False,
    is_pad: bool = False,
    pad_value: int = 0,
    interpolation: int = cv2.INTER_LINEAR,
) -> np.ndarray:
    if keep_aspect_ratio:
        h, w = image.shape[:2]
        scale = min(size[1] / h, size[0] / w)
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=interpolation)
        if is_pad:
            nh, nw = image.shape[:2]
            ph, pw = max(0, size[1] - nh), max(0, size[0] - nw)
            image = np.pad(
                image,
                ((0, ph), (0, pw), (0, 0)),
                mode="constant",
                constant_values=pad_value,
            )
        return image
    return cv2.resize(image, size, interpolation=interpolation)


def resize_image_with_aspect_ocv(
    image: np.ndarray,
    size: tuple[int, int],
    interpolation: int = cv2.INTER_LINEAR,
) -> np.ndarray:
    return resize_image_ocv(
        image,
        size,
        keep_aspect_ratio=True,
        is_pad=True,
        pad_value=0,
        interpolation=interpolation,
    )


def resize_image_letterbox_ocv(
    image: np.ndarray,
    size: tuple[int, int],
    interpolation: int = cv2.INTER_LINEAR,
    pad_value: int = 0,
) -> np.ndarray:
    ih, iw = image.shape[0:2]
    w, h = size
    scale = min(w / iw, h / ih)
    nw = round(iw * scale)
    nh = round(ih * scale)
    image = cv2.resize(image, (nw, nh), interpolation=interpolation)
    dx = (w - nw) // 2
    dy = (h - nh) // 2
    return np.pad(
        image,
        ((dy, h - nh - dy), (dx, w - nw - dx), (0, 0)),
        mode="constant",
        constant_values=pad_value,
    )


def crop_resize_ocv(image: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    desired_aspect_ratio = size[1] / size[0]  # width / height
    if desired_aspect_ratio == 1:
        if image.shape[0] > image.shape[1]:
            offset = (image.shape[0] - image.shape[1]) // 2
            cropped_frame = image[offset : image.shape[1] + offset]
        else:
            offset = (image.shape[1] - image.shape[0]) // 2
            cropped_frame = image[:, offset : image.shape[0] + offset]
    elif desired_aspect_ratio < 1:
        new_width = math.floor(image.shape[0] * desired_aspect_ratio)
        offset = (image.shape[1] - new_width) // 2
        cropped_frame = image[:, offset : new_width + offset]
    elif desired_aspect_ratio > 1:
        new_height = math.floor(image.shape[1] / desired_aspect_ratio)
        offset = (image.shape[0] - new_height) // 2
        cropped_frame = image[offset : new_height + offset]

    return cv2.resize(cropped_frame, size)


def setup_python_preprocessing_pipeline(
    layout: str,
    resize_mode: str,
    interpolation_mode: str,
    target_shape: tuple[int, ...],
    pad_value: int,
    dtype: type = int,
    brg2rgb: bool = False,
    mean: list[Any] | None = None,
    scale: list[Any] | None = None,
    input_idx: int = 0,
    intensity_mode: str = "none",
    intensity_max_value: float | None = None,
    intensity_window_center: float | None = None,
    intensity_window_width: float | None = None,
    intensity_percentile_low: float = 1.0,
    intensity_percentile_high: float = 99.0,
    intensity_scale_factor: float = 1.0,
    intensity_min_value: float = 0.0,
    intensity_repeat_channels: bool = False,
):
    """
    Sets up a Python preprocessing pipeline for model adapters.

    Args:
        layout: Target layout for the input (e.g., "NCHW", "NHWC")
        resize_mode: Type of resizing ("crop", "standard", "fit_to_window", "fit_to_window_letterbox")
        interpolation_mode: Interpolation method ("LINEAR", "CUBIC", "NEAREST")
        target_shape: Target shape for resizing
        pad_value: Padding value for letterbox resizing
        dtype: Data type for preprocessing
        brg2rgb: Whether to convert BGR to RGB
        mean: Mean values for normalization
        scale: Scale values for normalization
        input_idx: Input index (unused but kept for compatibility)
        intensity_mode: Intensity scaling mode applied before normalization
        intensity_max_value: Maximum input value for scale_to_unit or range_scale
        intensity_window_center: Window center for window intensity mode
        intensity_window_width: Window width for window intensity mode
        intensity_percentile_low: Lower percentile for percentile intensity mode
        intensity_percentile_high: Upper percentile for percentile intensity mode
        intensity_scale_factor: Scale factor for range_scale intensity mode
        intensity_min_value: Minimum output value for range_scale intensity mode
        intensity_repeat_channels: Whether to repeat single-channel input to 3 channels

    Returns:
        Callable: A preprocessing function that can be applied to input data
    """
    from functools import partial, reduce

    preproc_funcs = [np.squeeze]

    if intensity_repeat_channels:
        preproc_funcs.append(_repeat_single_channel_np)
    if resize_mode != "crop":
        if resize_mode == "fit_to_window_letterbox":
            resize_fn = partial(
                RESIZE_TYPES[resize_mode],
                size=target_shape,
                interpolation=INTERPOLATION_TYPES[interpolation_mode],
                pad_value=pad_value,
            )
        else:
            resize_fn = partial(
                RESIZE_TYPES[resize_mode],
                size=target_shape,
                interpolation=INTERPOLATION_TYPES[interpolation_mode],
            )
    else:
        resize_fn = partial(RESIZE_TYPES[resize_mode], size=target_shape)
    preproc_funcs.append(resize_fn)

    intensity_fn = create_intensity_fn(
        intensity_mode,
        max_value=intensity_max_value,
        window_center=intensity_window_center,
        window_width=intensity_window_width,
        percentile_low=intensity_percentile_low,
        percentile_high=intensity_percentile_high,
        scale_factor=intensity_scale_factor,
        min_value=intensity_min_value,
    )
    input_transform = InputTransform(brg2rgb, mean, scale, intensity_fn=intensity_fn)
    preproc_funcs.extend((input_transform.__call__, partial(change_layout, layout=layout)))

    return reduce(
        lambda f, g: lambda x: f(g(x)),
        reversed(preproc_funcs),
    )


def change_layout(image, layout):
    """Changes the input image layout to fit the layout of the model input layer.

    Args:
        image (ndarray): a single image as 3D array in HWC layout
        layout (str): target layout

    Returns:
        ndarray: the image with layout aligned with the model layout
    """
    if "CHW" in layout:
        image = image.transpose((2, 0, 1))  # HWC->CHW
        image = image.reshape((1, *image.shape))
    return image


RESIZE_TYPES: dict[str, Callable] = {
    "crop": crop_resize_ocv,
    "standard": resize_image_ocv,
    "fit_to_window": resize_image_with_aspect_ocv,
    "fit_to_window_letterbox": resize_image_letterbox_ocv,
}


INTERPOLATION_TYPES: dict[str, int] = {
    "LINEAR": cv2.INTER_LINEAR,
    "CUBIC": cv2.INTER_CUBIC,
    "NEAREST": cv2.INTER_NEAREST,
    "AREA": cv2.INTER_AREA,
}


def _repeat_single_channel_np(image: np.ndarray) -> np.ndarray:
    """Expand a single-channel image to 3 channels by repeating.

    Handles HxW and HxWx1.  Already-3-channel images pass through unchanged.
    """
    if image.ndim == 2:
        return np.repeat(image[:, :, np.newaxis], 3, axis=2)
    if image.ndim == 3 and image.shape[2] == 1:
        return np.repeat(image, 3, axis=2)
    return image


class InputTransform:
    def __init__(
        self,
        reverse_input_channels: bool = False,
        mean_values: list[float] | None = None,
        scale_values: list[float] | None = None,
        intensity_fn: Callable | None = None,
    ):
        self.reverse_input_channels = reverse_input_channels
        self.intensity_fn = intensity_fn
        self.is_trivial = not (reverse_input_channels or mean_values or scale_values or intensity_fn)
        self.means = np.array(mean_values, dtype=np.float32) if mean_values else np.array([0.0, 0.0, 0.0])
        self.std_scales = np.array(scale_values, dtype=np.float32) if scale_values else np.array([1.0, 1.0, 1.0])

    def __call__(self, inputs):
        if self.is_trivial:
            return inputs
        if self.intensity_fn:
            inputs = self.intensity_fn(inputs)
        if self.reverse_input_channels:
            inputs = cv2.cvtColor(inputs, cv2.COLOR_BGR2RGB)
        return (inputs - self.means) / self.std_scales


def create_intensity_fn(
    mode: str,
    *,
    max_value: float | None = None,
    window_center: float | None = None,
    window_width: float | None = None,
    percentile_low: float = 1.0,
    percentile_high: float = 99.0,
    scale_factor: float = 1.0,
    min_value: float = 0.0,
) -> Callable | None:
    """Create a Python-side intensity transform callable for the given mode.

    Returns None for 'none' mode (no transformation).
    """
    if mode == "none":
        return None

    if mode == "scale_to_unit":
        if max_value is None:
            msg = "intensity_max_value is required for scale_to_unit mode"
            raise ValueError(msg)
        mv = float(max_value)

        def _scale_to_unit(img: np.ndarray) -> np.ndarray:
            return img.astype(np.float32) / mv

        return _scale_to_unit

    if mode == "window":
        if window_center is None or window_width is None:
            msg = "intensity_window_center and intensity_window_width are required for window mode"
            raise ValueError(msg)
        low = float(window_center) - float(window_width) / 2.0
        high = float(window_center) + float(window_width) / 2.0
        span = high - low

        def _window(img: np.ndarray) -> np.ndarray:
            return np.clip((img.astype(np.float32) - low) / span, 0.0, 1.0)

        return _window

    if mode == "percentile":

        def _percentile(img: np.ndarray) -> np.ndarray:
            img_f = img.astype(np.float32)
            p_low = np.float32(np.percentile(img, percentile_low))
            p_high = np.float32(np.percentile(img, percentile_high))
            span = p_high - p_low
            if span == 0:
                return np.zeros_like(img, dtype=np.float32)
            return np.clip((img_f - p_low) / span, 0.0, 1.0).astype(np.float32)

        return _percentile

    if mode == "range_scale":
        sf = float(scale_factor)
        min = float(min_value)
        max = float(max_value) if max_value is not None else np.inf

        if np.isfinite(max) and max != min:
            range = max - min

            def _range_scale(img: np.ndarray) -> np.ndarray:
                return (np.clip(img.astype(np.float32) * sf, min, max) - min) / range

        else:

            def _range_scale(img: np.ndarray) -> np.ndarray:
                return np.clip(img.astype(np.float32) * sf, min, max)

        return _range_scale

    msg = f"Unknown intensity mode: {mode}"
    raise ValueError(msg)
