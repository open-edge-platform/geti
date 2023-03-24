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
#include <fstream>

#include <opencv2/core.hpp>
#include <openvino/openvino.hpp>

#include <utils/image_utils.h>
#include <utils/ocv_common.hpp>
#include <adapters/inference_adapter.h>

#include "models/input_data.h"
#include "models/internal_model_data.h"

ImageModel::ImageModel(const std::string& modelFile,
                       const std::string& resize_type,
                       bool useAutoResize,
                       const std::string& layout)
    : ModelBase(modelFile, layout),
      useAutoResize(useAutoResize),
      resizeMode(selectResizeMode(resize_type)) {}

RESIZE_MODE ImageModel::selectResizeMode(const std::string& resize_type) {
    RESIZE_MODE resize = RESIZE_FILL;
    if ("crop" == resize_type) {
        throw std::runtime_error("crop resize_type is not implemented");
    } else if ("standard" == resize_type) {
        resize = RESIZE_FILL;
    } else if ("fit_to_window" == resize_type) {
        if (useAutoResize) {
            throw std::runtime_error("useAutoResize supports only standard resize_type");
        }
        resize = RESIZE_KEEP_ASPECT;
    } else if ("fit_to_window_letterbox" == resize_type) {
        if (useAutoResize) {
            throw std::runtime_error("useAutoResize supports only standard resize_type");
        }
        resize = RESIZE_KEEP_ASPECT_LETTERBOX;
    } else {
        throw std::runtime_error("Unknown value for resize_type arg");
    }

    return resize;
}

ImageModel::ImageModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : ModelBase(model, configuration) {
    auto auto_resize_iter = configuration.find("auto_resize");
    if (auto_resize_iter == configuration.end()) {
        if (model->has_rt_info("model_info", "auto_resize")) {
            useAutoResize = model->get_rt_info<bool>("model_info", "auto_resize");
        }
    } else {
        useAutoResize = auto_resize_iter->second.as<bool>();
    }

    auto resize_type_iter = configuration.find("resize_type");
    std::string resize_type = "standard";
    if (resize_type_iter == configuration.end()) {
        if (model->has_rt_info("model_info", "resize_type")) {
            resize_type = model->get_rt_info<std::string>("model_info", "resize_type");
        }
    } else {
        resize_type = resize_type_iter->second.as<std::string>();
    }
    resizeMode = selectResizeMode(resize_type);

    auto labels_iter = configuration.find("labels");
    if (labels_iter == configuration.end()) {
        if (!model->has_rt_info<std::string>("model_info", "labels")) {
            throw std::runtime_error("Configuration or model rt_info should contain labels"); //TODO
        }
        labels = split(model->get_rt_info<std::string>("model_info", "labels"), ' ');
    } else {
        labels = labels_iter->second.as<std::vector<std::string>>();
    }

    if (model->has_rt_info("model_info", "embedded_processing")) {
        embedded_processing = model->get_rt_info<bool>("model_info", "embedded_processing");
    }
}

ImageModel::ImageModel(std::shared_ptr<InferenceAdapter>& adapter)
    : ModelBase(adapter) {
    auto configuration = adapter->getModelConfig();
    auto auto_resize_iter = configuration.find("auto_resize");
    if (auto_resize_iter != configuration.end()) {
        useAutoResize = auto_resize_iter->second.as<bool>();
    }

    auto resize_type_iter = configuration.find("resize_type");
    std::string resize_type = "standard";
    if (resize_type_iter != configuration.end()) {
        resize_type = resize_type_iter->second.as<std::string>();
    }
    resizeMode = selectResizeMode(resize_type);

    auto labels_iter = configuration.find("labels");
    if (labels_iter != configuration.end()) {
        labels = labels_iter->second.as<std::vector<std::string>>();
    }

    auto embedded_processing_iter = configuration.find("embedded_processing");
    if (embedded_processing_iter != configuration.end()) {
        embedded_processing = embedded_processing_iter->second.as<bool>();
    }
}

void ImageModel::updateModelInfo() {
    ModelBase::updateModelInfo();

    model->set_rt_info(useAutoResize, "model_info", "auto_resize");
    model->set_rt_info(formatResizeMode(resizeMode), "model_info", "resize_type");

    if (!labels.empty()) {
        model->set_rt_info(labels, "model_info", "labels");  
    }

    model->set_rt_info(embedded_processing, "model_info", "embedded_processing");
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

std::vector<std::string> ImageModel::loadLabels(const std::string& labelFilename) {
    std::vector<std::string> labelsList;

    /* Read labels (if any) */
    if (!labelFilename.empty()) {
        std::ifstream inputFile(labelFilename);
        if (!inputFile.is_open())
            throw std::runtime_error("Can't open the labels file: " + labelFilename);
        std::string label;
        while (std::getline(inputFile, label)) {
            labelsList.push_back(label);
        }
        if (labelsList.empty())
            throw std::logic_error("File is empty: " + labelFilename);
    }

    return labelsList;
}
