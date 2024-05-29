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

#include "adapters/openvino_adapter.h"
#include <openvino/openvino.hpp>
#include <utils/slog.hpp>
#include <stdexcept>
#include <vector>

void OpenVINOInferenceAdapter::loadModel(const std::shared_ptr<const ov::Model>& model, ov::Core& core,
                                                            const std::string& device, const ov::AnyMap& compilationConfig, size_t max_num_requests) {
    slog::info << "Loading model to the plugin" << slog::endl;
    ov::AnyMap customCompilationConfig(compilationConfig);
    if (max_num_requests != 1) {
        if (customCompilationConfig.find("PERFORMANCE_HINT") == customCompilationConfig.end()) {
            customCompilationConfig["PERFORMANCE_HINT"] = ov::hint::PerformanceMode::THROUGHPUT;
        }
        if (max_num_requests > 0) {
            if (customCompilationConfig.find("PERFORMANCE_HINT_NUM_REQUESTS") == customCompilationConfig.end()) {
                customCompilationConfig["PERFORMANCE_HINT_NUM_REQUESTS"] = ov::hint::num_requests(max_num_requests);
            }
        }
    }
    else {
        if (customCompilationConfig.find("PERFORMANCE_HINT") == customCompilationConfig.end()) {
            customCompilationConfig["PERFORMANCE_HINT"] = ov::hint::PerformanceMode::LATENCY;
        }
    }

    compiledModel = core.compile_model(model, device, customCompilationConfig);
    asyncQueue = std::make_unique<AsyncInferQueue>(compiledModel, max_num_requests);
    initInputsOutputs();

    if (model->has_rt_info({"model_info"})) {
        modelConfig = model->get_rt_info<ov::AnyMap>("model_info");
    }
}

InferenceOutput OpenVINOInferenceAdapter::infer(const InferenceInput& input) {
    auto request = asyncQueue->operator[](asyncQueue->get_idle_request_id());
    // Fill input blobs
    for (const auto& item : input) {
        request.set_tensor(item.first, item.second);
    }

    // Do inference
    request.infer();

    // Processing output blobs
    InferenceOutput output;
    for (const auto& item : outputNames) {
        output.emplace(item, request.get_tensor(item));
    }

    return output;
}

void OpenVINOInferenceAdapter::inferAsync(const InferenceInput& input, CallbackData callback_args) {
    asyncQueue->start_async(input, callback_args);
}

void OpenVINOInferenceAdapter::setCallback(std::function<void(ov::InferRequest, CallbackData)> callback) {
    asyncQueue->set_custom_callbacks(callback);
}

bool OpenVINOInferenceAdapter::isReady() {
    return asyncQueue->is_ready();
}

void OpenVINOInferenceAdapter::awaitAll() {
    asyncQueue->wait_all();
}

void OpenVINOInferenceAdapter::awaitAny() {
    asyncQueue->get_idle_request_id();
}

size_t OpenVINOInferenceAdapter::getNumAsyncExecutors() const {
    return asyncQueue->size();
}

ov::PartialShape OpenVINOInferenceAdapter::getInputShape(const std::string& inputName) const {
    return compiledModel.input(inputName).get_partial_shape();
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
