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
#include <map>
#include <memory>
#include <string>
#include <vector>

#include <utils/nms.hpp>

#include "models/detection_model_ext.h"

namespace ov {
class Model;
}  // namespace ov
struct InferenceResult;
struct ResultBase;

class ModelRetinaFace : public DetectionModelExt {
public:
    static const int LANDMARKS_NUM = 5;
    static const int INIT_VECTOR_SIZE = 200;

    ModelRetinaFace(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    ModelRetinaFace(std::shared_ptr<InferenceAdapter>& adapter);
    using DetectionModelExt::DetectionModelExt;

    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;
    static std::string ModelType;

protected:
    struct AnchorCfgLine {
        int stride;
        std::vector<int> scales;
        int baseSize;
        std::vector<int> ratios;
    };

    bool shouldDetectMasks = false;
    bool shouldDetectLandmarks = false;
    const float maskThreshold = 0.8f;
    float landmarkStd = 1.0f;

    enum OutputType { OUT_BOXES, OUT_SCORES, OUT_LANDMARKS, OUT_MASKSCORES, OUT_MAX };

    std::vector<std::string> separateoutputNames[OUT_MAX];
    const std::vector<AnchorCfgLine> anchorCfg = {
        {32, {32, 16}, 16, {1}}, {16, {8, 4}, 16, {1}}, {8, {2, 1}, 16, {1}}};
    std::map<int, std::vector<Anchor>> anchorsFpn;
    std::vector<std::vector<Anchor>> anchors;

    void generateAnchorsFpn();
    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void initDefaultParameters(const ov::AnyMap& configuration);
    void updateModelInfo() override;
};
