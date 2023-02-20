// Copyright (C) 2018-2023 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

/**
 * @brief a header file with common samples functionality
 * @file args_helper.hpp
 */

#pragma once

#include <map>
#include <set>
#include <string>
#include <vector>

#include <opencv2/core/types.hpp>
#include <openvino/openvino.hpp>

std::vector<std::string> split(const std::string& s, char delim);

std::vector<std::string> parseDevices(const std::string& device_string);

std::map<std::string, int32_t> parseValuePerDevice(const std::set<std::string>& devices,
                                                   const std::string& values_string);

std::map<std::string, ov::Layout> parseLayoutString(const std::string& layout_string);
