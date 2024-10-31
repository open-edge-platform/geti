/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
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
};
