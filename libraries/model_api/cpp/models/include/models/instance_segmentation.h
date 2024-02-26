/*
// Copyright (C) 2020-2024 Intel Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writingb  software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
*/

#pragma once
#include <memory>
#include <string>
#include <vector>

#include "models/image_model.h"

namespace ov {
class Model;
}  // namespace ov
struct InferenceResult;
struct ResultBase;
struct InstanceSegmentationResult;
struct ImageInputData;
struct SegmentedObject;

class MaskRCNNModel : public ImageModel {
public:
    MaskRCNNModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    MaskRCNNModel(std::shared_ptr<InferenceAdapter>& adapter);

    static std::unique_ptr<MaskRCNNModel> create_model(const std::string& modelFile, const ov::AnyMap& configuration = {}, bool preload = true, const std::string& device = "AUTO");
    static std::unique_ptr<MaskRCNNModel> create_model(std::shared_ptr<InferenceAdapter>& adapter);

    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;

    virtual std::unique_ptr<InstanceSegmentationResult> infer(const ImageInputData& inputData);
    static std::string ModelType;
    bool postprocess_semantic_masks = true;

protected:
    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void updateModelInfo() override;
    std::string getLabelName(size_t labelID) {
        return labelID < labels.size() ? labels[labelID] : std::string("Label #") + std::to_string(labelID);
    }

    float confidence_threshold = 0.5f;
};

cv::Mat segm_postprocess(const SegmentedObject& box, const cv::Mat& unpadded, int im_h, int im_w);
