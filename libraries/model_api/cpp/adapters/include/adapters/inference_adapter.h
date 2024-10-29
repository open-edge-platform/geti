/*
// Copyright (C) 2021-2024 Intel Corporation
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
#include <functional>
#include <map>
#include <memory>
#include <openvino/openvino.hpp>
#include <string>
#include <vector>

struct InputData;
struct InferenceResult;

using InferenceOutput = std::map<std::string, ov::Tensor>;
using InferenceInput = std::map<std::string, ov::Tensor>;
using CallbackData = std::shared_ptr<ov::AnyMap>;

// The interface doesn't have implementation
class InferenceAdapter {
public:
    virtual ~InferenceAdapter() = default;

    virtual InferenceOutput infer(const InferenceInput& input) = 0;
    virtual void setCallback(std::function<void(ov::InferRequest, CallbackData)> callback) = 0;
    virtual void inferAsync(const InferenceInput& input, CallbackData callback_args) = 0;
    virtual bool isReady() = 0;
    virtual void awaitAll() = 0;
    virtual void awaitAny() = 0;
    virtual size_t getNumAsyncExecutors() const = 0;
    virtual void loadModel(const std::shared_ptr<const ov::Model>& model,
                           ov::Core& core,
                           const std::string& device = "",
                           const ov::AnyMap& compilationConfig = {},
                           size_t max_num_requests = 0) = 0;
    virtual ov::PartialShape getInputShape(const std::string& inputName) const = 0;
    virtual std::vector<std::string> getInputNames() const = 0;
    virtual std::vector<std::string> getOutputNames() const = 0;
    virtual const ov::AnyMap& getModelConfig() const = 0;
};
