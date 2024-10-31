/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <memory>
#include <openvino/openvino.hpp>
#include <string>
#include <vector>

#include "models/detection_model_ext.h"

class ModelYoloX : public DetectionModelExt {
public:
    ModelYoloX(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    ModelYoloX(std::shared_ptr<InferenceAdapter>& adapter);
    using DetectionModelExt::DetectionModelExt;

    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;
    std::shared_ptr<InternalModelData> preprocess(const InputData& inputData, InferenceInput& input) override;
    static std::string ModelType;

protected:
    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void setStridesGrids();
    void initDefaultParameters(const ov::AnyMap& configuration);
    void updateModelInfo() override;

    float iou_threshold;
    std::vector<std::pair<size_t, size_t>> grids;
    std::vector<size_t> expandedStrides;
    static const size_t numberOfClasses = 80;
};
