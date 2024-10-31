/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "adapters/openvino_adapter.h"

#include <openvino/openvino.hpp>
#include <stdexcept>
#include <utils/slog.hpp>
#include <vector>

void OpenVINOInferenceAdapter::loadModel(const std::shared_ptr<const ov::Model>& model,
                                         ov::Core& core,
                                         const std::string& device,
                                         const ov::AnyMap& compilationConfig,
                                         size_t max_num_requests) {
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
    } else {
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

void OpenVINOInferenceAdapter::infer(const InferenceInput& input, InferenceOutput& output) {
    auto request = asyncQueue->operator[](asyncQueue->get_idle_request_id());
    for (const auto& [name, tensor] : input) {
        request.set_tensor(name, tensor);
    }
    for (const auto& [name, tensor] : output) {
        request.set_tensor(name, tensor);
    }
    request.infer();
    for (const auto& name : outputNames) {
        output[name] = request.get_tensor(name);
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
ov::PartialShape OpenVINOInferenceAdapter::getOutputShape(const std::string& outputName) const {
    return compiledModel.output(outputName).get_partial_shape();
}

void OpenVINOInferenceAdapter::initInputsOutputs() {
    for (const auto& input : compiledModel.inputs()) {
        inputNames.push_back(input.get_any_name());
    }

    for (const auto& output : compiledModel.outputs()) {
        outputNames.push_back(output.get_any_name());
    }
}
ov::element::Type_t OpenVINOInferenceAdapter::getInputDatatype(const std::string&) const {
    throw std::runtime_error("Not implemented");
}
ov::element::Type_t OpenVINOInferenceAdapter::getOutputDatatype(const std::string&) const {
    throw std::runtime_error("Not implemented");
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
