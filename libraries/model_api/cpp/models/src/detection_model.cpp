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

DetectionModel::DetectionModel(const std::string& modelFile,
                               float confidenceThreshold,
                               bool useAutoResize,
                               const std::vector<std::string>& labels,
                               const std::string& layout)
    : ImageModel(modelFile, useAutoResize, layout),
      labels(labels),
      confidenceThreshold(confidenceThreshold) {}

std::unique_ptr<DetectionModel> DetectionModel::create_model(const std::string& modelFile, std::shared_ptr<InferenceAdapter> adapter, std::string model_type, const ov::AnyMap& configuration) {
    std::shared_ptr<ov::Model> model = ov::Core{}.read_model(modelFile);
    if (model_type.empty()) {
        model_type = model->get_rt_info<std::string>("model_info", "model_type");
    }
    auto confidence_threshold_iter = configuration.find("confidence_threshold");
    float confidence_threshold = 0.5;
    if (confidence_threshold_iter == configuration.end()) {
        confidence_threshold = stof(model->get_rt_info<std::string>("model_info", "confidence_threshold"));
    } else {
        confidence_threshold = confidence_threshold_iter->second.as<float>();
    }
    auto labels_iter = configuration.find("labels");
    std::vector<std::string> labels;
    if (labels_iter == configuration.end()) {
        labels = split(model->get_rt_info<std::string>("model_info", "labels"), ' ');
    } else {
        labels = labels_iter->second.as<std::vector<std::string>>();
    }
    auto layout_iter = configuration.find("layout");
    std::string layout;
    if (layout_iter != configuration.end()) {
        layout = layout_iter->second.as<std::string>();
    }
    auto auto_resize_iter = configuration.find("auto_resize");
    bool auto_resize = false;
    if (auto_resize_iter != configuration.end()) {
        auto_resize = auto_resize_iter->second.as<bool>();
    }
    auto iou_t_iter = configuration.find("iou_t");
    float iou_t = 0.5;
    if (iou_t_iter != configuration.end()) {
        iou_t = iou_t_iter->second.as<bool>();
    }
    auto anchors_iter = configuration.find("anchors");
    std::vector<float> anchors;
    if (anchors_iter != configuration.end()) {
        anchors = anchors_iter->second.as<std::vector<float>>();
    }
    auto masks_iter = configuration.find("masks");
    std::vector<int64_t> masks;
    if (masks_iter != configuration.end()) {
        masks = masks_iter->second.as<std::vector<int64_t>>();
    }

    std::unique_ptr<DetectionModel> detectionModel;
    if (model_type == "centernet") {
    } else if (model_type == "faceboxes") {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelFaceBoxes(modelFile,
                                        confidence_threshold,
                                        auto_resize,
                                        iou_t,
                                        layout));
    } else if (model_type == "retinaface") {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelRetinaFace(modelFile,
                                        confidence_threshold,
                                        auto_resize,
                                        iou_t,
                                        layout));
    } else if (model_type == "retinaface-pytorch") {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelRetinaFacePT(modelFile,
                                            confidence_threshold,
                                            auto_resize,
                                            iou_t,
                                            layout));
    } else if (model_type == "ssd" || model_type == "SSD") {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelSSD(modelFile, confidence_threshold, auto_resize, labels, layout));
    } else if (model_type == "yolo") {
        bool FLAGS_yolo_af = true;  // Use advanced postprocessing/filtering algorithm for YOLO
        detectionModel = std::unique_ptr<DetectionModel>(new ModelYolo(modelFile,
                                    confidence_threshold,
                                    auto_resize,
                                    FLAGS_yolo_af,
                                    iou_t,
                                    labels,
                                    anchors,
                                    masks,
                                    layout));
    } else if (model_type == "yolov3-onnx") {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelYoloV3ONNX(modelFile,
                                        confidence_threshold,
                                        labels,
                                        layout));
    } else if (model_type == "yolox") {
        detectionModel = std::unique_ptr<DetectionModel>(new ModelYoloX(modelFile,
                                    confidence_threshold,
                                    iou_t,
                                    labels,
                                    layout));
    } else {
        throw std::runtime_error{"No model type or invalid model type (-at) provided: " + model_type};
    }

    detectionModel->load(adapter);
    return detectionModel;
}

std::vector<std::string> DetectionModel::loadLabels(const std::string& labelFilename) {
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

std::unique_ptr<DetectionResult> DetectionModel::infer(const ImageInputData& inputData) {
    auto result = ModelBase::infer(static_cast<const InputData&>(inputData));
    return std::unique_ptr<DetectionResult>(static_cast<DetectionResult*>(result.release()));
}
