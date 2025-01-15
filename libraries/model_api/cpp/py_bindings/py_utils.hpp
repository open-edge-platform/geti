/*
 * Copyright (C) 2025 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <nanobind/ndarray.h>

#include <opencv2/core/core.hpp>
#include <openvino/openvino.hpp>

namespace nb = nanobind;

namespace vision::nanobind::utils {
cv::Mat wrap_np_mat(const nb::ndarray<>& input);
ov::Any py_object_to_any(const nb::object& py_obj, const std::string& property_name);
}  // namespace vision::nanobind::utils
