/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "utils/image_utils.h"

#include <openvino/opsets/opset1.hpp>
#include <openvino/opsets/opset10.hpp>
#include <openvino/opsets/opset4.hpp>

using namespace ov;

namespace {
opset10::Interpolate::InterpolateMode ov2ovInterpolationMode(cv::InterpolationFlags interpolationMode) {
    switch (interpolationMode) {
    case cv::INTER_NEAREST:
        return opset10::Interpolate::InterpolateMode::NEAREST;
        break;
    case cv::INTER_LINEAR:
        return opset10::Interpolate::InterpolateMode::LINEAR;
    case cv::INTER_CUBIC:
        return opset10::Interpolate::InterpolateMode::CUBIC;
    default:
        break;
    }

    return opset10::Interpolate::InterpolateMode::LINEAR;
}

Output<Node> resizeImageGraph(const ov::Output<ov::Node>& input,
                              const ov::Shape& size,
                              bool keep_aspect_ratio,
                              const cv::InterpolationFlags interpolationMode,
                              uint8_t pad_value) {
    const size_t h_axis = 1;
    const size_t w_axis = 2;

    auto mode = ov2ovInterpolationMode(interpolationMode);

    if (size.size() != 2) {
        throw std::logic_error("Size parameter should be 2-dimensional");
    }
    auto w = size.at(0);
    auto h = size.at(1);

    auto sizes = opset10::Constant::create(element::i64, Shape{2}, {h, w});
    auto axes = opset10::Constant::create(element::i64, Shape{2}, {h_axis, w_axis});

    if (!keep_aspect_ratio) {
        auto scales = opset10::Constant::create(element::f32, Shape{2}, {0.0f, 0.0f});
        opset10::Interpolate::InterpolateAttrs attrs;
        attrs.mode = mode;
        attrs.shape_calculation_mode = opset10::Interpolate::ShapeCalcMode::SIZES;

        return std::make_shared<opset10::Interpolate>(input, sizes, scales, axes, attrs);
    }

    auto image_shape = std::make_shared<opset10::ShapeOf>(input);
    auto iw = std::make_shared<opset10::Convert>(
        std::make_shared<opset10::Gather>(image_shape,
                                          opset10::Constant::create(element::i64, Shape{1}, {w_axis}),
                                          opset10::Constant::create(element::i64, Shape{1}, {0})),
        element::f32);
    auto ih = std::make_shared<opset10::Convert>(
        std::make_shared<opset10::Gather>(image_shape,
                                          opset10::Constant::create(element::i64, Shape{1}, {h_axis}),
                                          opset10::Constant::create(element::i64, Shape{1}, {0})),
        element::f32);

    auto w_ratio = std::make_shared<opset10::Divide>(opset10::Constant::create(element::f32, Shape{1}, {float(w)}), iw);
    auto h_ratio = std::make_shared<opset10::Divide>(opset10::Constant::create(element::f32, Shape{1}, {float(h)}), ih);
    auto scale = std::make_shared<opset10::Minimum>(w_ratio, h_ratio);
    auto nw = std::make_shared<opset10::Convert>(std::make_shared<opset10::Multiply>(iw, scale), element::i32);
    auto nh = std::make_shared<opset10::Convert>(std::make_shared<opset10::Multiply>(ih, scale), element::i32);
    auto new_size = std::make_shared<opset10::Concat>(OutputVector{nh, nw}, 0);

    auto scales = opset10::Constant::create(element::f32, Shape{2}, {0.0f, 0.0f});
    opset10::Interpolate::InterpolateAttrs attrs;
    attrs.mode = mode;
    attrs.shape_calculation_mode = opset10::Interpolate::ShapeCalcMode::SIZES;
    auto image = std::make_shared<opset10::Interpolate>(input, new_size, scales, axes, attrs);
    auto dx_border = std::make_shared<opset10::Subtract>(opset10::Constant::create(element::i32, Shape{1}, {w}), nw);
    auto dy_border = std::make_shared<opset10::Subtract>(opset10::Constant::create(element::i32, Shape{1}, {h}), nh);
    auto pads_begin = opset10::Constant::create(element::i32, Shape{4}, {0, 0, 0, 0});
    auto pads_end =
        std::make_shared<opset10::Concat>(OutputVector{opset10::Constant::create(element::i32, Shape{1}, {0}),
                                                       dy_border,
                                                       dx_border,
                                                       opset10::Constant::create(element::i32, Shape{1}, {0})},
                                          0);
    return std::make_shared<opset10::Pad>(image,
                                          pads_begin,
                                          pads_end,
                                          opset10::Constant::create(element::u8, Shape{}, {pad_value}),
                                          ov::op::PadMode::CONSTANT);
}

Output<Node> fitToWindowLetterBoxGraph(const ov::Output<ov::Node>& input,
                                       const ov::Shape& size,
                                       const cv::InterpolationFlags interpolationMode,
                                       uint8_t pad_value) {
    const size_t h_axis = 1;
    const size_t w_axis = 2;

    auto mode = ov2ovInterpolationMode(interpolationMode);

    if (size.size() != 2) {
        throw std::logic_error("Size parameter should be 2-dimensional");
    }
    auto w = size.at(0);
    auto h = size.at(1);
    auto image_shape = std::make_shared<opset10::ShapeOf>(input);
    auto iw = std::make_shared<opset10::Convert>(
        std::make_shared<opset10::Gather>(image_shape,
                                          opset10::Constant::create(element::i64, Shape{1}, {w_axis}),
                                          opset10::Constant::create(element::i64, Shape{1}, {0})),
        element::f32);
    auto ih = std::make_shared<opset10::Convert>(
        std::make_shared<opset10::Gather>(image_shape,
                                          opset10::Constant::create(element::i64, Shape{1}, {h_axis}),
                                          opset10::Constant::create(element::i64, Shape{1}, {0})),
        element::f32);
    auto w_ratio = std::make_shared<opset10::Divide>(opset10::Constant::create(element::f32, Shape{1}, {float(w)}), iw);
    auto h_ratio = std::make_shared<opset10::Divide>(opset10::Constant::create(element::f32, Shape{1}, {float(h)}), ih);
    auto scale = std::make_shared<opset10::Minimum>(w_ratio, h_ratio);
    auto nw = std::make_shared<opset10::Convert>(
        std::make_shared<opset10::Round>(std::make_shared<opset10::Multiply>(iw, scale),
                                         opset10::Round::RoundMode::HALF_TO_EVEN),
        element::i32);
    auto nh = std::make_shared<opset10::Convert>(
        std::make_shared<opset10::Round>(std::make_shared<opset10::Multiply>(ih, scale),
                                         opset10::Round::RoundMode::HALF_TO_EVEN),
        element::i32);
    auto new_size = std::make_shared<opset10::Concat>(OutputVector{nh, nw}, 0);

    auto scales = opset10::Constant::create(element::f32, Shape{2}, {0.0f, 0.0f});
    auto axes = opset10::Constant::create(element::i64, Shape{2}, {h_axis, w_axis});
    opset10::Interpolate::InterpolateAttrs attrs;
    attrs.mode = mode;
    attrs.shape_calculation_mode = opset10::Interpolate::ShapeCalcMode::SIZES;
    auto image = std::make_shared<opset10::Interpolate>(input, new_size, scales, axes, attrs);

    // pad
    auto dx = std::make_shared<opset10::Divide>(
        std::make_shared<opset10::Subtract>(opset10::Constant::create(element::i32, Shape{1}, {w}), nw),
        opset10::Constant::create(element::i32, Shape{1}, {2}));
    auto dy = std::make_shared<opset10::Divide>(
        std::make_shared<opset10::Subtract>(opset10::Constant::create(element::i32, Shape{1}, {h}), nh),
        opset10::Constant::create(element::i32, Shape{1}, {2}));
    auto dx_border = std::make_shared<opset10::Subtract>(
        std::make_shared<opset10::Subtract>(opset10::Constant::create(element::i32, Shape{1}, {w}), nw),
        dx);
    auto dy_border = std::make_shared<opset10::Subtract>(
        std::make_shared<opset10::Subtract>(opset10::Constant::create(element::i32, Shape{1}, {h}), nh),
        dy);
    auto pads_begin =
        std::make_shared<opset10::Concat>(OutputVector{opset10::Constant::create(element::i32, Shape{1}, {0}),
                                                       dy,
                                                       dx,
                                                       opset10::Constant::create(element::i32, Shape{1}, {0})},
                                          0);
    auto pads_end =
        std::make_shared<opset10::Concat>(OutputVector{opset10::Constant::create(element::i32, Shape{1}, {0}),
                                                       dy_border,
                                                       dx_border,
                                                       opset10::Constant::create(element::i32, Shape{1}, {0})},
                                          0);
    return std::make_shared<opset10::Pad>(image,
                                          pads_begin,
                                          pads_end,
                                          opset10::Constant::create(element::u8, Shape{}, {pad_value}),
                                          op::PadMode::CONSTANT);
}

Output<Node> cropResizeGraph(const ov::Output<ov::Node>& input,
                             const ov::Shape& size,
                             const cv::InterpolationFlags interpolationMode) {
    const size_t h_axis = 1;
    const size_t w_axis = 2;
    const auto desired_aspect_ratio = float(size[1]) / size[0];  // width / height
    auto mode = ov2ovInterpolationMode(interpolationMode);

    auto image_shape = std::make_shared<opset10::ShapeOf>(input);
    auto iw = std::make_shared<opset10::Convert>(
        std::make_shared<opset10::Gather>(image_shape,
                                          opset10::Constant::create(element::i64, Shape{1}, {w_axis}),
                                          opset10::Constant::create(element::i64, Shape{1}, {0})),
        element::i32);
    auto ih = std::make_shared<opset10::Convert>(
        std::make_shared<opset10::Gather>(image_shape,
                                          opset10::Constant::create(element::i64, Shape{1}, {h_axis}),
                                          opset10::Constant::create(element::i64, Shape{1}, {0})),
        element::i32);

    Output<Node> cropped_frame;
    if (desired_aspect_ratio == 1) {
        // then_body
        auto image_t = std::make_shared<opset10::Parameter>(element::u8, PartialShape{-1, -1, -1, 3});
        auto iw_t = std::make_shared<opset10::Parameter>(element::i32, PartialShape{});
        auto ih_t = std::make_shared<opset10::Parameter>(element::i32, PartialShape{});
        auto then_offset = std::make_shared<opset10::Unsqueeze>(
            std::make_shared<opset10::Divide>(std::make_shared<opset10::Subtract>(ih_t, iw_t),
                                              opset10::Constant::create(element::i32, Shape{1}, {2})),
            opset10::Constant::create(element::i64, Shape{1}, {0}));
        auto then_stop = std::make_shared<opset10::Add>(then_offset, iw_t);
        auto then_cropped_frame =
            std::make_shared<opset10::Slice>(image_t,
                                             then_offset,
                                             then_stop,
                                             opset10::Constant::create(element::i64, Shape{1}, {1}),
                                             opset10::Constant::create(element::i64, Shape{1}, {h_axis}));
        auto then_body_res_1 = std::make_shared<opset10::Result>(then_cropped_frame);
        auto then_body = std::make_shared<Model>(NodeVector{then_body_res_1}, ParameterVector{image_t, iw_t, ih_t});

        // else_body
        auto image_e = std::make_shared<opset10::Parameter>(element::u8, PartialShape{-1, -1, -1, 3});
        auto iw_e = std::make_shared<opset10::Parameter>(element::i32, PartialShape{});
        auto ih_e = std::make_shared<opset10::Parameter>(element::i32, PartialShape{});
        auto else_offset = std::make_shared<opset10::Unsqueeze>(
            std::make_shared<opset10::Divide>(std::make_shared<opset10::Subtract>(iw_e, ih_e),
                                              opset10::Constant::create(element::i32, Shape{1}, {2})),
            opset10::Constant::create(element::i64, Shape{1}, {0}));
        auto else_stop = std::make_shared<opset10::Add>(else_offset, ih_e);
        auto else_cropped_frame =
            std::make_shared<opset10::Slice>(image_e,
                                             else_offset,
                                             else_stop,
                                             opset10::Constant::create(element::i64, Shape{1}, {1}),
                                             opset10::Constant::create(element::i64, Shape{1}, {w_axis}));
        auto else_body_res_1 = std::make_shared<opset10::Result>(else_cropped_frame);
        auto else_body = std::make_shared<Model>(NodeVector{else_body_res_1}, ParameterVector{image_e, iw_e, ih_e});

        // if operator
        auto condition = std::make_shared<opset10::Greater>(ih, iw);
        auto if_node = std::make_shared<opset10::If>(condition->output(0));
        if_node->set_then_body(then_body);
        if_node->set_else_body(else_body);
        if_node->set_input(input, image_t, image_e);
        if_node->set_input(iw->output(0), iw_t, iw_e);
        if_node->set_input(ih->output(0), ih_t, ih_e);
        cropped_frame = if_node->set_output(then_body_res_1, else_body_res_1);
    } else if (desired_aspect_ratio < 1) {
        auto new_width = std::make_shared<opset10::Floor>(std::make_shared<opset10::Multiply>(
            std::make_shared<opset10::Convert>(ih, element::f32),
            opset10::Constant::create(element::f32, Shape{1}, {desired_aspect_ratio})));
        auto offset = std::make_shared<opset10::Unsqueeze>(
            std::make_shared<opset10::Divide>(std::make_shared<opset10::Subtract>(iw, new_width),
                                              opset10::Constant::create(element::i32, Shape{1}, {2})),
            opset10::Constant::create(element::i64, Shape{1}, {0}));
        auto stop = std::make_shared<opset10::Add>(offset, new_width);
        cropped_frame = std::make_shared<opset10::Slice>(input,
                                                         offset,
                                                         stop,
                                                         opset10::Constant::create(element::i64, Shape{1}, {1}),
                                                         opset10::Constant::create(element::i64, Shape{1}, {w_axis}));
    } else {
        auto new_height = std::make_shared<opset10::Floor>(std::make_shared<opset10::Multiply>(
            std::make_shared<opset10::Convert>(iw, element::f32),
            opset10::Constant::create(element::f32, Shape{1}, {1.0 / desired_aspect_ratio})));
        auto offset = std::make_shared<opset10::Unsqueeze>(
            std::make_shared<opset10::Divide>(std::make_shared<opset10::Subtract>(ih, new_height),
                                              opset10::Constant::create(element::i32, Shape{1}, {2})),
            opset10::Constant::create(element::i64, Shape{1}, {0}));
        auto stop = std::make_shared<opset10::Add>(offset, new_height);
        cropped_frame = std::make_shared<opset10::Slice>(input,
                                                         offset,
                                                         stop,
                                                         opset10::Constant::create(element::i64, Shape{1}, {1}),
                                                         opset10::Constant::create(element::i64, Shape{1}, {h_axis}));
    }

    auto target_size = opset10::Constant::create(element::i64, Shape{2}, {size.at(1), size.at(0)});
    auto axes = opset10::Constant::create(element::i64, Shape{2}, {h_axis, w_axis});
    auto scales = opset10::Constant::create(element::f32, Shape{2}, {1.0f, 1.0f});
    opset10::Interpolate::InterpolateAttrs attrs;
    attrs.mode = mode;
    attrs.shape_calculation_mode = opset10::Interpolate::ShapeCalcMode::SIZES;

    return std::make_shared<opset10::Interpolate>(cropped_frame, target_size, scales, axes, attrs);
}
}  // namespace

cv::Mat resizeImageExt(const cv::Mat& mat,
                       int width,
                       int height,
                       RESIZE_MODE resizeMode,
                       cv::InterpolationFlags interpolationMode,
                       cv::Rect* roi,
                       cv::Scalar BorderConstant) {
    if (width == mat.cols && height == mat.rows) {
        return mat;
    }

    cv::Mat dst;

    switch (resizeMode) {
    case RESIZE_FILL:
    case RESIZE_CROP:  // TODO: hadle crop if not embedded
    {
        cv::resize(mat, dst, cv::Size(width, height), interpolationMode);
        if (roi) {
            *roi = cv::Rect(0, 0, width, height);
        }
        break;
    }
    case RESIZE_KEEP_ASPECT:
    case RESIZE_KEEP_ASPECT_LETTERBOX: {
        double scale = std::min(static_cast<double>(width) / mat.cols, static_cast<double>(height) / mat.rows);
        cv::Mat resizedImage;
        cv::resize(mat,
                   resizedImage,
                   {int(std::round(mat.cols * scale)), int(std::round(mat.rows * scale))},
                   0,
                   0,
                   interpolationMode);

        int dx = resizeMode == RESIZE_KEEP_ASPECT ? 0 : (width - resizedImage.cols) / 2;
        int dy = resizeMode == RESIZE_KEEP_ASPECT ? 0 : (height - resizedImage.rows) / 2;

        cv::copyMakeBorder(resizedImage,
                           dst,
                           dy,
                           height - resizedImage.rows - dy,
                           dx,
                           width - resizedImage.cols - dx,
                           cv::BORDER_CONSTANT,
                           BorderConstant);
        if (roi) {
            *roi = cv::Rect(dx, dy, resizedImage.cols, resizedImage.rows);
        }
        break;
    }
    case NO_RESIZE: {
        dst = mat;
        if (roi) {
            *roi = cv::Rect(0, 0, mat.cols, mat.rows);
        }
        break;
    }
    }
    return dst;
}

preprocess::PostProcessSteps::CustomPostprocessOp createResizeGraph(RESIZE_MODE resizeMode,
                                                                    const Shape& size,
                                                                    const cv::InterpolationFlags interpolationMode,
                                                                    uint8_t pad_value) {
    switch (resizeMode) {
    case RESIZE_FILL:
        return [=](const Output<Node>& node) {
            return resizeImageGraph(node, size, false, interpolationMode, pad_value);
        };
        break;
    case RESIZE_KEEP_ASPECT:
        return [=](const Output<Node>& node) {
            return resizeImageGraph(node, size, true, interpolationMode, pad_value);
        };
        break;
    case RESIZE_KEEP_ASPECT_LETTERBOX:
        return [=](const Output<Node>& node) {
            return fitToWindowLetterBoxGraph(node, size, interpolationMode, pad_value);
        };
        break;
    case RESIZE_CROP:
        return [=](const Output<Node>& node) {
            return cropResizeGraph(node, size, interpolationMode);
        };
        break;
    default:
        throw std::runtime_error("Unsupported resize mode: " + resizeMode);
        break;
    }
}
