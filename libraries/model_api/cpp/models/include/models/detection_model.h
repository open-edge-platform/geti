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

#include <string>
#include "models/image_model.h"

struct DetectionResult;
struct ImageInputData;
struct InferenceAdatper;

class DetectionModel : public ImageModel {
public:
    DetectionModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    DetectionModel(std::shared_ptr<InferenceAdapter>& adapter, const ov::AnyMap& configuration = {});

    static std::unique_ptr<DetectionModel> create_model(const std::string& modelFile,
                                                        const ov::AnyMap& configuration = {},
                                                        std::string model_type = "",
                                                        bool preload = true,
                                                        const std::string& device = "AUTO");
    static std::unique_ptr<DetectionModel> create_model(std::shared_ptr<InferenceAdapter>& adapter);

    virtual std::unique_ptr<DetectionResult> infer(const ImageInputData& inputData);

protected:
    float confidence_threshold = 0.5f;

    void updateModelInfo() override;
};
