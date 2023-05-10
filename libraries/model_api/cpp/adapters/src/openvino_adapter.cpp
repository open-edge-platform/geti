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

#include <stdexcept>
#include <vector>

#include "adapters/openvino_adapter.h"

#include <opencv2/core.hpp>
#include <openvino/openvino.hpp>

#include <utils/common.hpp>
#include <utils/config_factory.h>
#include <utils/ocv_common.hpp>
#include <utils/slog.hpp>

void OpenVINOInferenceAdapter::loadModel(const std::shared_ptr<const ov::Model>& model, ov::Core& core,
                                                            const std::string& device, const ov::AnyMap& compilationConfig) {
    slog::info << "Loading model to the plugin" << slog::endl;

    compiledModel = core.compile_model(model, device, compilationConfig);
    inferRequest = compiledModel.create_infer_request();

    initInputsOutputs();

    if (model->has_rt_info({"model_info"})) {
        modelConfig = model->get_rt_info<ov::AnyMap>("model_info");
    }
}

InferenceOutput OpenVINOInferenceAdapter::infer(const InferenceInput& input) {
    // Fill input blobs
    for (const auto& item : input) {
        inferRequest.set_tensor(item.first, item.second);
    }

    // Do inference
    inferRequest.infer();

    // Processing output blobs
    InferenceOutput output;
    for (const auto& item : outputNames) {
        output.emplace(item, inferRequest.get_tensor(item));
    }

    return output;
}

ov::Shape OpenVINOInferenceAdapter::getInputShape(const std::string& inputName) const {
    return compiledModel.input(inputName).get_shape();
}

void OpenVINOInferenceAdapter::initInputsOutputs() {
    for (const auto& input : compiledModel.inputs()) {
        inputNames.push_back(input.get_any_name());
    }

    for (const auto& output : compiledModel.outputs()) {
        outputNames.push_back(output.get_any_name());
    }
}

std::vector<std::string> OpenVINOInferenceAdapter::getInputNames() const {
    return inputNames;
}

std::vector<std::string> OpenVINOInferenceAdapter::getOutputNames() const {
    return outputNames;
}

const ov::AnyMap& OpenVINOInferenceAdapter::getModelConfig() const {
    return modelConfig;
}
