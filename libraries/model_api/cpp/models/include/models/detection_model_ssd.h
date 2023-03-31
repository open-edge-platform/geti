/*
// Copyright (C) 2020-2023 Intel Corporation
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
#include <stddef.h>

#include <memory>
#include <string>
#include <vector>

#include "models/detection_model.h"

namespace ov {
class InferRequest;
class Model;
}  // namespace ov
struct InferenceResult;
struct InputData;
struct InternalModelData;
struct ResultBase;

class ModelSSD : public DetectionModel {
public:
    ModelSSD(std::shared_ptr<InferenceAdapter>& adapter);
    using DetectionModel::DetectionModel;
    std::shared_ptr<InternalModelData> preprocess(const InputData& inputData, InferenceInput& input) override;
    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;
    static std::string ModelType;

protected:
    std::unique_ptr<ResultBase> postprocessSingleOutput(InferenceResult& infResult);
    std::unique_ptr<ResultBase> postprocessMultipleOutputs(InferenceResult& infResult);
    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void prepareSingleOutput(std::shared_ptr<ov::Model>& model);
    void prepareMultipleOutputs(std::shared_ptr<ov::Model>& model);
    void updateModelInfo() override;
    size_t objectSize = 0;
    size_t detectionsNumId = 0;
};
