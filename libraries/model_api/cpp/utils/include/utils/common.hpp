// Copyright (C) 2018-2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

/**
 * @brief a header file with common samples functionality
 * @file common.hpp
 */

#pragma once

#include <iostream>
#include <openvino/openvino.hpp>
#include <string>
#include <utility>
#include <vector>

#include "utils/slog.hpp"

template <typename T, std::size_t N>
constexpr std::size_t arraySize(const T (&)[N]) noexcept {
    return N;
}

template <typename T>
T clamp(T value, T low, T high) {
    return value < low ? low : (value > high ? high : value);
}

static inline void logBasicModelInfo(const std::shared_ptr<ov::Model>& model) {
    slog::info << "Model name: " << model->get_friendly_name() << slog::endl;

    // Dump information about model inputs/outputs
    ov::OutputVector inputs = model->inputs();
    ov::OutputVector outputs = model->outputs();

    slog::info << "\tInputs: " << slog::endl;
    for (const ov::Output<ov::Node>& input : inputs) {
        const std::string name = input.get_any_name();
        const ov::element::Type type = input.get_element_type();
        const ov::PartialShape shape = input.get_partial_shape();
        const ov::Layout layout = ov::layout::get_layout(input);

        slog::info << "\t\t" << name << ", " << type << ", " << shape << ", " << layout.to_string() << slog::endl;
    }

    slog::info << "\tOutputs: " << slog::endl;
    for (const ov::Output<ov::Node>& output : outputs) {
        const std::string name = output.get_names().size() ? output.get_any_name() : "";
        const ov::element::Type type = output.get_element_type();
        const ov::PartialShape shape = output.get_partial_shape();
        const ov::Layout layout = ov::layout::get_layout(output);

        slog::info << "\t\t" << name << ", " << type << ", " << shape << ", " << layout.to_string() << slog::endl;
    }

    return;
}
