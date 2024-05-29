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

#include "models/detection_model.h"
#include "models/detection_model_centernet.h"
#include "models/detection_model_faceboxes.h"
#include "models/detection_model_retinaface.h"
#include "models/detection_model_retinaface_pt.h"
#include "models/detection_model_ssd.h"
#include "models/detection_model_yolo.h"
#include "models/detection_model_yolov3_onnx.h"
#include "models/detection_model_yolox.h"

#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "models/image_model.h"
#include "models/input_data.h"
#include "models/results.h"
#include "utils/slog.hpp"

DetectionModel::DetectionModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : ImageModel(model, configuration) {
    auto confidence_threshold_iter = configuration.find("confidence_threshold");
    if (confidence_threshold_iter == configuration.end()) {
        if (model->has_rt_info("model_info", "confidence_threshold")) {
            confidence_threshold = model->get_rt_info<float>("model_info", "confidence_threshold");
        }
    } else {
        confidence_threshold = confidence_threshold_iter->second.as<float>();
    }
}

DetectionModel::DetectionModel(std::shared_ptr<InferenceAdapter>& adapter, const ov::AnyMap& configuration)
   : ImageModel(adapter, configuration) {
    confidence_threshold = get_from_any_maps("confidence_threshold", configuration, adapter->getModelConfig(), confidence_threshold);
}

void DetectionModel::updateModelInfo() {
    ImageModel::updateModelInfo();

    model->set_rt_info(confidence_threshold, "model_info", "confidence_threshold");
}

std::unique_ptr<DetectionModel> DetectionModel::create_model(const std::string& modelFile,
                                                             const ov::AnyMap& configuration,
                                                             std::string model_type,
                                                             bool preload,
                                                             const std::string& device) {
    auto core = ov::Core();
    std::shared_ptr<ov::Model> model = core.read_model(modelFile);
    if (model_type.empty()) {
        try {
            if (model->has_rt_info("model_info", "model_type") ) {
                model_type = model->get_rt_info<std::string>("model_info", "model_type");
            }
        } catch (const std::exception&) {
            slog::warn << "Model type is not specified in the rt_info, use default model type: " << model_type << slog::endl;
        }
    }

    std::unique_ptr<DetectionModel> detectionModel;
    if (model_type == ModelFaceBoxes::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelFaceBoxes(model, configuration));
    } else if (model_type == ModelRetinaFace::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelRetinaFace(model, configuration));
    } else if (model_type == ModelRetinaFacePT::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelRetinaFacePT(model, configuration));
    } else if (model_type == ModelSSD::ModelType || model_type == "SSD") {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelSSD(model, configuration));
    } else if (model_type == ModelYoloX::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelYoloX(model, configuration));
    } else if (model_type == ModelCenterNet::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelCenterNet(model, configuration));
    } else if (model_type == YOLOv5::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new YOLOv5(model, configuration));
    } else if (model_type == YOLOv8::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new YOLOv8(model, configuration));
    } else {
        throw std::runtime_error("Incorrect or unsupported model_type is provided in the model_info section: " + model_type);
    }

    detectionModel->prepare();
    if (preload) {
        detectionModel->load(core, device);
    }
    return detectionModel;
}

std::unique_ptr<DetectionModel> DetectionModel::create_model(std::shared_ptr<InferenceAdapter>& adapter) {
    const ov::AnyMap& configuration = adapter->getModelConfig();
    auto model_type_iter = configuration.find("model_type");
    std::string model_type;
    if (model_type_iter != configuration.end()) {
        model_type = model_type_iter->second.as<std::string>();
    }

    std::unique_ptr<DetectionModel> detectionModel;
    if (model_type == ModelFaceBoxes::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelFaceBoxes(adapter));
    } else if (model_type == ModelRetinaFace::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelRetinaFace(adapter));
    } else if (model_type == ModelRetinaFacePT::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelRetinaFacePT(adapter));
    } else if (model_type == ModelSSD::ModelType || model_type == "SSD") {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelSSD(adapter));
    } else if (model_type == ModelYoloX::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelYoloX(adapter));
    } else if (model_type == ModelCenterNet::ModelType) {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelCenterNet(adapter));
    } else {
        throw std::runtime_error("Incorrect or unsupported model_type is provided: " + model_type);
    }

    return detectionModel;
}

std::unique_ptr<DetectionResult> DetectionModel::infer(const ImageInputData& inputData) {
    auto result = ImageModel::inferImage(inputData);
    return std::unique_ptr<DetectionResult>(static_cast<DetectionResult*>(result.release()));
}

std::vector<std::unique_ptr<DetectionResult>> DetectionModel::inferBatch(const std::vector<ImageInputData>& inputImgs) {
    auto results = ImageModel::inferBatchImage(inputImgs);
    std::vector<std::unique_ptr<DetectionResult>> detResults;
    detResults.reserve(results.size());
    for (auto& result : results) {
        detResults.emplace_back(static_cast<DetectionResult*>(result.release()));
    }
    return detResults;
}
