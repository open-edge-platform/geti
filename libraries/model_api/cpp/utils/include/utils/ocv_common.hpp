// Copyright (C) 2018-2023 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

/**
 * @brief a header file with common samples functionality using OpenCV
 * @file ocv_common.hpp
 */

#pragma once

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <openvino/openvino.hpp>

#include "utils/shared_tensor_allocator.hpp"

static inline ov::Tensor wrapMat2Tensor(const cv::Mat& mat) {
    auto matType = mat.type() & CV_MAT_DEPTH_MASK;
    if (matType != CV_8U && matType != CV_32F) {
        throw std::runtime_error("Unsupported mat type for wrapping");
    }
    bool isMatFloat = matType == CV_32F;

    const size_t channels = mat.channels();
    const size_t height = mat.rows;
    const size_t width = mat.cols;

    const size_t strideH = mat.step.buf[0];
    const size_t strideW = mat.step.buf[1];

    const bool isDense = !isMatFloat ? (strideW == channels && strideH == channels * width) :
        (strideW == channels * sizeof(float) && strideH == channels * width * sizeof(float));
    if (!isDense) {
        throw std::runtime_error("Doesn't support conversion from not dense cv::Mat");
    }
    auto precision = isMatFloat ? ov::element::f32 : ov::element::u8;
    return ov::Tensor(precision, ov::Shape{ 1, height, width, channels }, SharedMatAllocator{mat});
}

static inline ov::Layout getLayoutFromShape(const ov::PartialShape& shape) {
    if (shape.size() == 2) {
        return "NC";
    }
    if (shape.size() == 3) {
        return ov::Interval{1, 4}.contains(shape[0].get_interval()) ? "CHW" :
                                                                      "HWC";
    }
    if (shape.size() == 4) {
        if (ov::Interval{1, 4}.contains(shape[1].get_interval())) {
            return "NCHW";
        }
        if (ov::Interval{1, 4}.contains(shape[3].get_interval())) {
            return "NHWC";
        }
        if (shape[1] == shape[2]) {
            return "NHWC";
        }
        if (shape[2] == shape[3]) {
            return "NCHW";
        }
    }
    throw std::runtime_error("Usupported " + std::to_string(shape.size()) + "D shape");
}

static cv::Scalar string2Scalar(const std::string& string) {
    std::stringstream ss{string};
    std::string item;
    std::vector<double> values;
    values.reserve(3);
    while (getline(ss, item, ' ')) {
        try {
            values.push_back(std::stod(item));
        } catch (const std::invalid_argument&) {
            throw std::runtime_error("Invalid parameter --mean_values or --scale_values is provided.");
        }
    }
    if (values.size() != 3) {
        throw std::runtime_error("InputTransform expects 3 values per channel, but got \"" + string + "\".");
    }
    return cv::Scalar(values[0], values[1], values[2]);
}

class InputTransform {
public:
    InputTransform() : reverseInputChannels(false), isTrivial(true) {}

    InputTransform(bool reverseInputChannels, const std::string& meanValues, const std::string& scaleValues) :
        reverseInputChannels(reverseInputChannels),
        isTrivial(!reverseInputChannels && meanValues.empty() && scaleValues.empty()),
        means(meanValues.empty() ? cv::Scalar(0.0, 0.0, 0.0) : string2Scalar(meanValues)),
        stdScales(scaleValues.empty() ? cv::Scalar(1.0, 1.0, 1.0) : string2Scalar(scaleValues)) {
    }

    void setPrecision(ov::preprocess::PrePostProcessor& ppp, const std::string& tensorName) {
        const auto precision = isTrivial ? ov::element::u8 : ov::element::f32;
        ppp.input(tensorName).tensor().set_element_type(precision);
    }

    cv::Mat operator()(const cv::Mat& inputs) {
        if (isTrivial) { return inputs; }
        cv::Mat result;
        inputs.convertTo(result, CV_32F);
        if (reverseInputChannels) {
            cv::cvtColor(result, result, cv::COLOR_BGR2RGB);
        }
        // TODO: merge the two following lines after OpenCV3 is droppped
        result -= means;
        result /= cv::Mat{stdScales};
        return result;
    }

private:
    bool reverseInputChannels;
    bool isTrivial;
    cv::Scalar means;
    cv::Scalar stdScales;
};
