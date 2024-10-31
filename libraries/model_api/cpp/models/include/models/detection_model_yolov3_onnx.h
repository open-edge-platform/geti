/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once

#include <openvino/openvino.hpp>
#include <string>
#include <vector>

#include "models/detection_model.h"

class ModelYoloV3ONNX : public DetectionModel {
public:
    ModelYoloV3ONNX(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    ModelYoloV3ONNX(std::shared_ptr<InferenceAdapter>& adapter);
    using DetectionModel::DetectionModel;

    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;
    std::shared_ptr<InternalModelData> preprocess(const InputData& inputData, InferenceInput& input) override;

protected:
    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void initDefaultParameters(const ov::AnyMap& configuration);

    std::string boxesOutputName;
    std::string scoresOutputName;
    std::string indicesOutputName;
    static const int numberOfClasses = 80;
};
