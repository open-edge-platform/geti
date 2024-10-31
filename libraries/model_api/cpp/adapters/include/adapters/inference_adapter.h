/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
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
    virtual void infer(const InferenceInput& input, InferenceOutput& output) = 0;
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
    virtual ov::PartialShape getOutputShape(const std::string& inputName) const = 0;
    virtual ov::element::Type_t getInputDatatype(const std::string& inputName) const = 0;
    virtual ov::element::Type_t getOutputDatatype(const std::string& outputName) const = 0;
    virtual std::vector<std::string> getInputNames() const = 0;
    virtual std::vector<std::string> getOutputNames() const = 0;
    virtual const ov::AnyMap& getModelConfig() const = 0;
};
