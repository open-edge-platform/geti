/*
 * Copyright (C) 2025 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "py_utils.hpp"

namespace vision::nanobind::utils {

cv::Mat wrap_np_mat(const nb::ndarray<>& input) {
    if (input.ndim() != 3 || input.shape(2) != 3 || input.dtype() != nb::dtype<uint8_t>()) {
        throw std::runtime_error("Input image should have HWC_8U layout");
    }

    int height = input.shape(0);
    int width = input.shape(1);

    return cv::Mat(height, width, CV_8UC3, input.data());
}

ov::Any py_object_to_any(const nb::object& py_obj, const std::string& property_name) {
    if (nb::isinstance<nb::str>(py_obj)) {
        return ov::Any(std::string(static_cast<nb::str>(py_obj).c_str()));
    } else if (nb::isinstance<nb::float_>(py_obj)) {
        return ov::Any(static_cast<double>(static_cast<nb::float_>(py_obj)));
    } else if (nb::isinstance<nb::int_>(py_obj)) {
        return ov::Any(static_cast<int>(static_cast<nb::int_>(py_obj)));
    } else {
        OPENVINO_THROW("Property \"" + property_name + "\" has unsupported type.");
    }
}

}  // namespace vision::nanobind::utils
