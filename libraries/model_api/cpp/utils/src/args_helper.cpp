// Copyright (C) 2018-2023 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#include "utils/args_helper.hpp"
#include "utils/slog.hpp"

#ifdef _WIN32
#include "w_dirent.hpp"
#else
#include <dirent.h>
#endif

#include <gflags/gflags.h>

#include <sys/stat.h>
#include <map>

#include <algorithm>
#include <cctype>
#include <sstream>

std::vector<std::string> split(const std::string& s, char delim) {
    std::vector<std::string> result;
    std::stringstream ss(s);
    std::string item;

    while (getline(ss, item, delim)) {
        result.push_back(item);
    }
    return result;
}

std::vector<std::string> parseDevices(const std::string& device_string) {
    const std::string::size_type colon_position = device_string.find(":");
    if (colon_position != std::string::npos) {
        std::string device_type = device_string.substr(0, colon_position);
        if (device_type == "HETERO" || device_type == "MULTI") {
            std::string comma_separated_devices = device_string.substr(colon_position + 1);
            std::vector<std::string> devices = split(comma_separated_devices, ',');
            for (auto& device : devices)
                device = device.substr(0, device.find("("));
            return devices;
        }
    }
    return {device_string};
}

// Format: <device1>:<value1>,<device2>:<value2> or just <value>
std::map<std::string, int32_t> parseValuePerDevice(const std::set<std::string>& devices,
                                                   const std::string& values_string) {
    auto values_string_upper = values_string;
    std::transform(values_string_upper.begin(),
                   values_string_upper.end(),
                   values_string_upper.begin(),
                   [](unsigned char c){ return std::toupper(c); });
    std::map<std::string, int32_t> result;
    auto device_value_strings = split(values_string_upper, ',');
    for (const auto& device_value_string : device_value_strings) {
        auto device_value_vec =  split(device_value_string, ':');
        if (device_value_vec.size() == 2) {
            auto it = std::find(devices.begin(), devices.end(), device_value_vec.at(0));
            if (it != devices.end()) {
                result[device_value_vec.at(0)] = std::stoi(device_value_vec.at(1));
            }
        } else if (device_value_vec.size() == 1) {
            uint32_t value = std::stoi(device_value_vec.at(0));
            for (const auto& device : devices) {
                result[device] = value;
            }
        } else if (device_value_vec.size() != 0) {
            throw std::runtime_error("Unknown string format: " + values_string);
        }
    }
    return result;
}

std::map<std::string, ov::Layout> parseLayoutString(const std::string& layout_string) {
    // Parse parameter string like "input0:NCHW,input1:NC" or "NCHW" (applied to all
    // inputs)
    std::map<std::string, ov::Layout> layouts;
    std::string searchStr = (layout_string.find_last_of(':') == std::string::npos && !layout_string.empty() ?
        ":" : "") + layout_string;
    auto colonPos = searchStr.find_last_of(':');
    while (colonPos != std::string::npos) {
        auto startPos = searchStr.find_last_of(',');
        auto inputName = searchStr.substr(startPos + 1, colonPos - startPos - 1);
        auto inputLayout = searchStr.substr(colonPos + 1);
        layouts[inputName] = ov::Layout(inputLayout);
        searchStr.resize(startPos + 1);
        if (searchStr.empty() || searchStr.back() != ',') {
            break;
        }
        searchStr.pop_back();
        colonPos = searchStr.find_last_of(':');
    }
    if (!searchStr.empty()) {
        throw std::invalid_argument("Can't parse input layout string: " + layout_string);
    }
    return layouts;
}
