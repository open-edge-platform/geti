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
#include <string>
#include <vector>
#include <map>
#include <memory>

#include <openvino/openvino.hpp>

struct InputData;
struct InferenceResult;

using InferenceOutput = std::map<std::string, ov::Tensor>;
using InferenceInput = std::map<std::string, ov::Tensor>;

// Used as interface it should not contain any implementation details.
class InferenceAdapter
{

public:
    InferenceAdapter() {};

    virtual InferenceOutput infer(const InferenceInput& input) = 0;
    virtual void loadModel(const std::shared_ptr<const ov::Model>& model, ov::Core& core,
                                                    const std::string& device, const ov::AnyMap& compilationConfig) = 0;
    virtual ov::Shape getInputShape(const std::string& inputName) const = 0;
};