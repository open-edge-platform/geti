#
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
import cv2 as cv
import numpy as np
import openvino as ov
import pytest
from model_api.adapters.utils import (
    resize_image_with_aspect,
    resize_image_with_aspect_ocv,
)
from openvino.preprocess import PrePostProcessor


@pytest.mark.parametrize(
    "img_shape",
    [(301, 999, 3), (999, 301, 3), (500, 500, 3), (1024, 768, 3), (768, 1024, 3)],
)
def test_resize_image_with_aspect_ocv(img_shape):
    model_h = 1024
    model_w = 1024
    pad_value = 0

    param_node = ov.op.Parameter(ov.Type.f32, ov.Shape([1, model_h, model_w, 3]))
    model = ov.Model(param_node, [param_node])
    ppp = PrePostProcessor(model)
    ppp.input().tensor().set_element_type(ov.Type.u8)
    ppp.input().tensor().set_layout(ov.Layout("NHWC"))
    ppp.input().tensor().set_shape([1, -1, -1, 3])
    ppp.input().preprocess().custom(
        resize_image_with_aspect(
            (model_h, model_w),
            "linear",
            pad_value,
        ),
    )
    ppp.input().preprocess().convert_element_type(ov.Type.f32)
    ov_resize_image_with_aspect = ov.Core().compile_model(ppp.build(), "CPU")

    rng = np.random.default_rng()
    img = rng.integers(0, 255, size=img_shape, dtype=np.uint8)
    ov_results = next(iter(ov_resize_image_with_aspect(img[None]).values()))[0]

    np_results = resize_image_with_aspect_ocv(img, (model_w, model_h))

    assert cv.PSNR(np_results.astype(np.float32), ov_results) > 20.0
