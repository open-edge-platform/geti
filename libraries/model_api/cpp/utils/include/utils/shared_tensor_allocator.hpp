/*
// Copyright (C) 2021-2023 Intel Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
*/

#pragma once

#include <opencv2/core.hpp>
#include <memory_resource>

struct SharedMatAllocator : public std::pmr::memory_resource {
    const cv::Mat mat;

    SharedMatAllocator(const cv::Mat& mat) : mat{mat} {}
    void* do_allocate(size_t bytes, size_t) override {
        return bytes <= mat.rows * mat.step[0] ? mat.data : nullptr;
    }
    void do_deallocate(void*, size_t, size_t) override {}
    bool do_is_equal(const std::pmr::memory_resource& other) const noexcept override {
        return this == &other;
    }
};
