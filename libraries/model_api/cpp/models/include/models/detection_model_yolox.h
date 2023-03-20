/*
// Copyright (C) 2022-2023 Intel Corporation
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
#include <memory>
#include <string>
#include <vector>

#include <openvino/openvino.hpp>

#include "models/detection_model_ext.h"


class ModelYoloX: public DetectionModelExt {
public:
    ModelYoloX(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    ModelYoloX(std::shared_ptr<InferenceAdapter>& adapter);
    using DetectionModelExt::DetectionModelExt;

    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;
    std::shared_ptr<InternalModelData> preprocess(const InputData& inputData, InferenceInput& input) override;

protected:
    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void setStridesGrids();
    void initDefaultParameters(const ov::AnyMap& configuration);

    double boxIOUThreshold;
    std::vector<std::pair<size_t, size_t>> grids;
    std::vector<size_t> expandedStrides;
    static const size_t numberOfClasses = 80;
};
