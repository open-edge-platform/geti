/*
// Copyright (C) 2021-2023 Intel Corporation
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

#include "models/model_base.h"
#include "utils/image_utils.h"

namespace ov {
class InferRequest;
}  // namespace ov
struct InputData;
struct InternalModelData;

class ImageModel : public ModelBase {
public:
    /// Constructor
    /// @param modelFile name of model to load
    /// @param useAutoResize - if true, image is resized by openvino
    /// @param layout - model input layout
    ImageModel(const std::string& modelFile,
               const std::string& resize_type,
               bool useAutoResize,
               const std::string& layout = "");

    ImageModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    ImageModel(std::shared_ptr<InferenceAdapter>& adapter);
    using ModelBase::ModelBase;

    std::shared_ptr<InternalModelData> preprocess(const InputData& inputData, InferenceInput& input) override;
    static std::vector<std::string> loadLabels(const std::string& labelFilename);
    std::shared_ptr<ov::Model> embedProcessing(std::shared_ptr<ov::Model>& model,
                                                    const std::string& inputName,
                                                    const ov::Layout&,
                                                    RESIZE_MODE resize_mode,
                                                    const cv::InterpolationFlags interpolationMode,
                                                    const ov::Shape& targetShape,
                                                    uint8_t pad_value,
                                                    bool brg2rgb,
                                                    const std::vector<float>& mean,
                                                    const std::vector<float>& scale,
                                                    const std::type_info& dtype = typeid(int));

protected:
    RESIZE_MODE selectResizeMode(const std::string& resize_type);
    void updateModelInfo() override;

    std::string getLabelName(size_t labelID) {
        return labelID < labels.size() ? labels[labelID] : std::string("Label #") + std::to_string(labelID);
    }

    std::vector<std::string> labels = {};
    bool useAutoResize = false;
    bool embedded_processing = false; // flag in model_info that pre/postprocessing embedded

    size_t netInputHeight = 0;
    size_t netInputWidth = 0;
    cv::InterpolationFlags interpolationMode = cv::INTER_LINEAR;
    RESIZE_MODE resizeMode = RESIZE_FILL;
    uint8_t pad_value = 0;
    bool reverse_input_channels = false;
    std::vector<float> scale_values;
};
