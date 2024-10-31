/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <opencv2/opencv.hpp>
#include <openvino/openvino.hpp>

enum RESIZE_MODE {
    RESIZE_FILL,
    RESIZE_KEEP_ASPECT,
    RESIZE_KEEP_ASPECT_LETTERBOX,
    RESIZE_CROP,
    NO_RESIZE,
};

inline std::string formatResizeMode(RESIZE_MODE mode) {
    switch (mode) {
    case RESIZE_FILL:
        return "standard";
    case RESIZE_KEEP_ASPECT:
        return "fit_to_window";
    case RESIZE_KEEP_ASPECT_LETTERBOX:
        return "fit_to_window_letterbox";
    case RESIZE_CROP:
        return "crop";
    default:
        return "unknown";
    }
}

cv::Mat resizeImageExt(const cv::Mat& mat,
                       int width,
                       int height,
                       RESIZE_MODE resizeMode = RESIZE_FILL,
                       cv::InterpolationFlags interpolationMode = cv::INTER_LINEAR,
                       cv::Rect* roi = nullptr,
                       cv::Scalar BorderConstant = cv::Scalar(0, 0, 0));

ov::preprocess::PostProcessSteps::CustomPostprocessOp createResizeGraph(RESIZE_MODE resizeMode,
                                                                        const ov::Shape& size,
                                                                        const cv::InterpolationFlags interpolationMode,
                                                                        uint8_t pad_value);
