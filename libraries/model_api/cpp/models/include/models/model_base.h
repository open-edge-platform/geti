/*
// Copyright (C) 2020-2024 Intel Corporation
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
#include <map>
#include <functional>
#include <memory>
#include <string>
#include <vector>

#include <openvino/openvino.hpp>

#include <utils/args_helper.hpp>
#include <utils/ocv_common.hpp>
#include <adapters/inference_adapter.h>

struct InferenceResult;
struct InputData;
struct InternalModelData;
struct ResultBase;

class ModelBase {
public:
    ModelBase(const std::string& modelFile, const std::string& layout = "");
    ModelBase(std::shared_ptr<InferenceAdapter>& adapter, const ov::AnyMap& configuration = {});
    ModelBase(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);

    virtual ~ModelBase() = default;

    std::shared_ptr<ov::Model> prepare();
    void load(ov::Core& core, const std::string& device, size_t num_infer_requests = 1);
    // Modifying ov::Model doesn't affect the model wrapper
    std::shared_ptr<ov::Model> getModel();
    std::shared_ptr<InferenceAdapter> getInferenceAdapter();

    virtual std::shared_ptr<InternalModelData> preprocess(const InputData& inputData, InferenceInput& input) = 0;
    virtual std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) = 0;
    virtual std::unique_ptr<ResultBase> infer(const InputData& inputData);
    virtual void inferAsync(const InputData& inputData, const ov::AnyMap& callback_args = {});
    virtual std::vector<std::unique_ptr<ResultBase>> inferBatch(const std::vector<std::reference_wrapper<const InputData>>& inputData);
    virtual std::vector<std::unique_ptr<ResultBase>> inferBatch(const std::vector<InputData>& inputData);

    virtual bool isReady();
    virtual void awaitAll();
    virtual void awaitAny();
    virtual void setCallback(std::function<void(std::unique_ptr<ResultBase>, const ov::AnyMap& callback_args)> callback);
    virtual size_t getNumAsyncExecutors() const;

    const std::vector<std::string>& getoutputNames() const {
        return outputNames;
    }
    const std::vector<std::string>& getinputNames() const {
        return inputNames;
    }

protected:
    virtual void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) = 0;
    virtual void updateModelInfo();

    InputTransform inputTransform = InputTransform();

    std::shared_ptr<ov::Model> model;
    std::vector<std::string> inputNames;
    std::vector<std::string> outputNames;
    std::string modelFile;
    std::shared_ptr<InferenceAdapter> inferenceAdapter;
    std::map<std::string, ov::Layout> inputsLayouts;
    ov::Layout getInputLayout(const ov::Output<ov::Node>& input);
    std::function<void(std::unique_ptr<ResultBase>, const ov::AnyMap&)> lastCallback;
};
