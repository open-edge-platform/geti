/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <functional>
#include <map>
#include <memory>
#include <queue>
#include <string>
#include <vector>

#include "adapters/inference_adapter.h"
#include "utils/async_infer_queue.hpp"

class OpenVINOInferenceAdapter : public InferenceAdapter {
public:
    OpenVINOInferenceAdapter() = default;

    virtual InferenceOutput infer(const InferenceInput& input) override;
    virtual void infer(const InferenceInput& input, InferenceOutput& output) override;
    virtual void inferAsync(const InferenceInput& input, const CallbackData callback_args) override;
    virtual void setCallback(std::function<void(ov::InferRequest, const CallbackData)> callback);
    virtual bool isReady();
    virtual void awaitAll();
    virtual void awaitAny();
    virtual void loadModel(const std::shared_ptr<const ov::Model>& model,
                           ov::Core& core,
                           const std::string& device = "",
                           const ov::AnyMap& compilationConfig = {},
                           size_t max_num_requests = 1) override;
    virtual size_t getNumAsyncExecutors() const;
    virtual ov::PartialShape getInputShape(const std::string& inputName) const override;
    virtual ov::PartialShape getOutputShape(const std::string& outputName) const override;
    virtual ov::element::Type_t getInputDatatype(const std::string& inputName) const override;
    virtual ov::element::Type_t getOutputDatatype(const std::string& outputName) const override;
    virtual std::vector<std::string> getInputNames() const override;
    virtual std::vector<std::string> getOutputNames() const override;
    virtual const ov::AnyMap& getModelConfig() const override;

protected:
    void initInputsOutputs();

protected:
    // Depends on the implementation details but we should share the model state in this class
    std::vector<std::string> inputNames;
    std::vector<std::string> outputNames;
    ov::CompiledModel compiledModel;
    std::unique_ptr<AsyncInferQueue> asyncQueue;
    ov::AnyMap modelConfig;  // the content of model_info section of rt_info
};
