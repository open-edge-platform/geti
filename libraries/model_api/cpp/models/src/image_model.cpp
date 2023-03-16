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

#include "models/image_model.h"

#include <stdexcept>
#include <vector>

#include <opencv2/core.hpp>
#include <openvino/openvino.hpp>

#include <utils/image_utils.h>
#include <utils/ocv_common.hpp>
#include <adapters/inference_adapter.h>

#include "models/input_data.h"
#include "models/internal_model_data.h"

ImageModel::ImageModel(const std::string& modelFile, const std::string& resize_type, bool useAutoResize, const std::string& layout)
    : ModelBase(modelFile, layout),
      useAutoResize(useAutoResize) {
        if ("crop" == resize_type) {
            throw std::runtime_error("crop resize_type is not implemented");
        } else if ("standard" == resize_type) {
            interpolationMode = cv::INTER_LINEAR;
            resizeMode = RESIZE_FILL;
        } else if ("fit_to_window" == resize_type) {
            if (useAutoResize) {
                throw std::runtime_error("useAutoResize supports only standard resize_type");
            }
            interpolationMode = cv::INTER_LINEAR;
            resizeMode = RESIZE_KEEP_ASPECT;
        } else if ("fit_to_window_letterbox" == resize_type) {
            if (useAutoResize) {
                throw std::runtime_error("useAutoResize supports only standard resize_type");
            }
            interpolationMode = cv::INTER_LINEAR;
            resizeMode = RESIZE_KEEP_ASPECT_LETTERBOX;
        } else {
            throw std::runtime_error("Unknown value for resize_type arg");
        }
    }

std::shared_ptr<InternalModelData> ImageModel::preprocess(const InputData& inputData, InferenceInput& input) {
    const auto& origImg = inputData.asRef<ImageInputData>().inputImage;
    auto img = inputTransform(origImg);

    if (!useAutoResize) {
        // /* Resize and copy data from the image to the input tensor */
        auto tensorShape = inferenceAdapter->getInputShape(inputNames[0]); // first input should be image
        const ov::Layout layout("NHWC");
        const size_t width = tensorShape[ov::layout::width_idx(layout)];
        const size_t height = tensorShape[ov::layout::height_idx(layout)];
        const size_t channels = tensorShape[ov::layout::channels_idx(layout)];
        if (static_cast<size_t>(img.channels()) != channels) {
            throw std::runtime_error("The number of channels for model input and image must match");
        }
        if (channels != 1 && channels != 3) {
            throw std::runtime_error("Unsupported number of channels");
        }
        img = resizeImageExt(img, width, height, resizeMode, interpolationMode);
    }
    input.emplace(inputNames[0], wrapMat2Tensor(img));
    return std::make_shared<InternalImageModelData>(origImg.cols, origImg.rows);
}
