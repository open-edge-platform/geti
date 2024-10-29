// Copyright (C) 2018-2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

/**
 * @brief a header file with common samples functionality
 * @file args_helper.hpp
 */

#pragma once

#include <map>
#include <opencv2/core/types.hpp>
#include <openvino/openvino.hpp>
#include <set>
#include <string>
#include <vector>

std::vector<std::string> split(const std::string& s, char delim);

std::vector<std::string> parseDevices(const std::string& device_string);

std::map<std::string, int32_t> parseValuePerDevice(const std::set<std::string>& devices,
                                                   const std::string& values_string);

std::map<std::string, ov::Layout> parseLayoutString(const std::string& layout_string);

std::string formatLayouts(const std::map<std::string, ov::Layout>& layouts);

template <typename Type>
Type get_from_any_maps(const std::string& key,
                       const ov::AnyMap& top_priority,
                       const ov::AnyMap& mid_priority,
                       Type low_priority) {
    auto topk_iter = top_priority.find(key);
    if (topk_iter != top_priority.end()) {
        return topk_iter->second.as<Type>();
    }
    topk_iter = mid_priority.find(key);
    if (topk_iter != mid_priority.end()) {
        return topk_iter->second.as<Type>();
    }
    return low_priority;
}

template <>
inline bool get_from_any_maps(const std::string& key,
                              const ov::AnyMap& top_priority,
                              const ov::AnyMap& mid_priority,
                              bool low_priority) {
    auto topk_iter = top_priority.find(key);
    if (topk_iter != top_priority.end()) {
        const std::string& val = topk_iter->second.as<std::string>();
        return val == "True" || val == "YES";
    }
    topk_iter = mid_priority.find(key);
    if (topk_iter != mid_priority.end()) {
        const std::string& val = topk_iter->second.as<std::string>();
        return val == "True" || val == "YES";
    }
    return low_priority;
}
