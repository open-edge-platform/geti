// Copyright (C) 2018-2024 Intel Corporation
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

    const bool isDense = !isMatFloat
                             ? (strideW == channels && strideH == channels * width)
                             : (strideW == channels * sizeof(float) && strideH == channels * width * sizeof(float));
    if (!isDense) {
        throw std::runtime_error("Doesn't support conversion from not dense cv::Mat");
    }
    auto precision = isMatFloat ? ov::element::f32 : ov::element::u8;
    struct SharedMatAllocator {
        const cv::Mat mat;
        void* allocate(size_t bytes, size_t) {
            return bytes <= mat.rows * mat.step[0] ? mat.data : nullptr;
        }
        void deallocate(void*, size_t, size_t) {}
        bool is_equal(const SharedMatAllocator& other) const noexcept {
            return this == &other;
        }
    };
    return ov::Tensor(precision, ov::Shape{1, height, width, channels}, SharedMatAllocator{mat});
}

struct IntervalCondition {
    using DimType = size_t;
    using IndexType = size_t;
    using ConditionChecker = std::function<bool(IndexType, const ov::PartialShape&)>;

    template <class Cond>
    constexpr IntervalCondition(IndexType i1, IndexType i2, Cond c)
        : impl([=](IndexType i0, const ov::PartialShape& shape) {
              return c(shape[i0].get_max_length(), shape[i1].get_max_length()) &&
                     c(shape[i0].get_max_length(), shape[i2].get_max_length());
          }) {}
    bool operator()(IndexType i0, const ov::PartialShape& shape) const {
        return impl(i0, shape);
    }

private:
    ConditionChecker impl;
};

template <template <class> class Cond, class... Args>
IntervalCondition makeCond(Args&&... args) {
    return IntervalCondition(std::forward<Args>(args)..., Cond<IntervalCondition::DimType>{});
}
using LayoutCondition = std::tuple<size_t /*dim index*/, IntervalCondition, std::string>;

static inline std::tuple<bool, ov::Layout> makeGuesLayoutFrom4DShape(const ov::PartialShape& shape) {
    // at the moment we make assumption about NCHW & NHCW only
    // if hypothetical C value is less than hypothetical H and W - then
    // out assumption is correct and we pick a corresponding layout
    static const std::array<LayoutCondition, 2> hypothesisMatrix{
        {{1, makeCond<std::less_equal>(2, 3), "NCHW"}, {3, makeCond<std::less_equal>(1, 2), "NHWC"}}};
    for (const auto& h : hypothesisMatrix) {
        auto channel_index = std::get<0>(h);
        const auto& cond = std::get<1>(h);
        if (cond(channel_index, shape)) {
            return std::make_tuple(true, ov::Layout{std::get<2>(h)});
        }
    }
    return {false, ov::Layout{}};
}

static inline ov::Layout getLayoutFromShape(const ov::PartialShape& shape) {
    if (shape.size() == 2) {
        return "NC";
    }
    if (shape.size() == 3) {
        if (shape[0] == 1) {
            return "NHW";
        }
        if (shape[2] == 1) {
            return "HWN";
        }
        throw std::runtime_error("Can't guess layout for " + shape.to_string());
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
        bool guesResult = false;
        ov::Layout guessedLayout;
        std::tie(guesResult, guessedLayout) = makeGuesLayoutFrom4DShape(shape);
        if (guesResult) {
            return guessedLayout;
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

    InputTransform(bool reverseInputChannels, const std::string& meanValues, const std::string& scaleValues)
        : reverseInputChannels(reverseInputChannels),
          isTrivial(!reverseInputChannels && meanValues.empty() && scaleValues.empty()),
          means(meanValues.empty() ? cv::Scalar(0.0, 0.0, 0.0) : string2Scalar(meanValues)),
          stdScales(scaleValues.empty() ? cv::Scalar(1.0, 1.0, 1.0) : string2Scalar(scaleValues)) {}

    void setPrecision(ov::preprocess::PrePostProcessor& ppp, const std::string& tensorName) {
        const auto precision = isTrivial ? ov::element::u8 : ov::element::f32;
        ppp.input(tensorName).tensor().set_element_type(precision);
    }

    cv::Mat operator()(const cv::Mat& inputs) {
        if (isTrivial) {
            return inputs;
        }
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

static inline cv::Mat wrap_saliency_map_tensor_to_mat(ov::Tensor& t, size_t shape_shift, size_t class_idx) {
    int ocv_dtype;
    switch (t.get_element_type()) {
    case ov::element::u8:
        ocv_dtype = CV_8U;
        break;
    case ov::element::f32:
        ocv_dtype = CV_32F;
        break;
    default:
        throw std::runtime_error("Unsupported saliency map data type in ov::Tensor to cv::Mat wrapper: " +
                                 t.get_element_type().get_type_name());
    }
    void* t_ptr = static_cast<char*>(t.data()) + class_idx * t.get_strides()[shape_shift];
    auto mat_size =
        cv::Size(static_cast<int>(t.get_shape()[shape_shift + 2]), static_cast<int>(t.get_shape()[shape_shift + 1]));

    return cv::Mat(mat_size, ocv_dtype, t_ptr, t.get_strides()[shape_shift + 1]);
}
