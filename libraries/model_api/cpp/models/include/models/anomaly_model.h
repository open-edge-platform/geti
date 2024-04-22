/*
  Copyright (C) 2020-2024 Intel Corporation

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
*/

#pragma once
#include "models/image_model.h"

namespace ov {
class Model;
}  // namespace ov
struct AnomalyResult;
struct ImageInputData;

class AnomalyModel : public ImageModel {
public:
    AnomalyModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    AnomalyModel(std::shared_ptr<InferenceAdapter>& adapter, const ov::AnyMap& configuration = {});

    static std::unique_ptr<AnomalyModel> create_model(const std::string& modelFile,
                                                      const ov::AnyMap& configuration = {},
                                                      bool preload = true,
                                                      const std::string& device = "AUTO");
    static std::unique_ptr<AnomalyModel> create_model(std::shared_ptr<InferenceAdapter>& adapter);

    virtual std::unique_ptr<AnomalyResult> infer(const ImageInputData& inputData);
    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;

    friend std::ostream& operator<<(std::ostream& os, std::unique_ptr<AnomalyModel>& model);

    static std::string ModelType;

protected:
    float imageThreshold{0.5f};
    float pixelThreshold{0.5f};
    float normalizationScale{1.0f};
    std::string task = "segmentation";

    void init_from_config(const ov::AnyMap& top_priority, const ov::AnyMap& mid_priority);

    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void updateModelInfo() override;
    cv::Mat normalize(cv::Mat& tensor, float threshold);
    double normalize(double& tensor, float threshold);
    std::vector<cv::Rect> getBoxes(cv::Mat& mask);
};
