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

#include "adapters/inference_adapter.h"

struct InferenceConfig;

class OpenVINOInferenceAdapter :public InferenceAdapter
{

public:
    OpenVINOInferenceAdapter() {}

    virtual InferenceOutput infer(const InferenceInput& input) override;
    virtual void loadModel(const std::shared_ptr<const ov::Model>& model, ov::Core& core,
                                                    const std::string& device = "", const ov::AnyMap& compilationConfig = {}) override;
    virtual ov::Shape getInputShape(const std::string& inputName) const override;
    virtual std::vector<std::string> getInputNames() const override;
    virtual std::vector<std::string> getOutputNames() const override;
    virtual const ov::AnyMap& getModelConfig() const override;

protected:
    void initInputsOutputs();

protected:
    //Depends on the implmentation details but we should share the model state in this class
    std::vector<std::string> inputNames;
    std::vector<std::string> outputNames;
    ov::CompiledModel compiledModel;
    ov::InferRequest inferRequest;
    ov::AnyMap modelConfig; // the content of model_info section of rt_info
};
