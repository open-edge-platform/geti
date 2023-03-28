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
#include <utility>
#include <vector>

#include <utils/nms.hpp>

#include "models/detection_model_ext.h"

namespace ov {
class Model;
}  // namespace ov
struct InferenceResult;
struct ResultBase;

class ModelFaceBoxes : public DetectionModelExt {
public:
    static const int INIT_VECTOR_SIZE = 200;

    ModelFaceBoxes(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    ModelFaceBoxes(std::shared_ptr<InferenceAdapter>& adapter);
    using DetectionModelExt::DetectionModelExt;

    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;
    static std::string ModelType;

protected:
    size_t maxProposalsCount = 0;
    const std::vector<float> variance = {0.1f, 0.2f};
    const std::vector<int> steps = {32, 64, 128};
    const std::vector<std::vector<int>> minSizes = {{32, 64, 128}, {256}, {512}};
    std::vector<Anchor> anchors;
    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void priorBoxes(const std::vector<std::pair<size_t, size_t>>& featureMaps);
    void initDefaultParameters(const ov::AnyMap& configuration);
    void updateModelInfo() override;
};
