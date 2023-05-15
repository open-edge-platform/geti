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

#include "models/detection_model_ssd.h"

#include <algorithm>
#include <map>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#include <openvino/openvino.hpp>

#include <utils/common.hpp>
#include <utils/ocv_common.hpp>

#include "models/internal_model_data.h"
#include "models/results.h"

struct InputData;

std::string ModelSSD::ModelType = "ssd";

ModelSSD::ModelSSD(std::shared_ptr<InferenceAdapter>& adapter)
    : DetectionModel(adapter) {
    auto configuration = adapter->getModelConfig();
    auto object_size_iter = configuration.find("object_size");
    if (object_size_iter != configuration.end()) {
        objectSize = object_size_iter->second.as<size_t>();
    }
    auto detections_num_id_iter = configuration.find("detections_num_id");
    if (detections_num_id_iter != configuration.end()) {
        detectionsNumId = detections_num_id_iter->second.as<size_t>();
    }
}

std::shared_ptr<InternalModelData> ModelSSD::preprocess(const InputData& inputData, InferenceInput& input) {
    if (inputNames.size() > 1) {
        cv::Mat info(cv::Size(1, 3), CV_32SC1);
        info.at<int>(0, 0) = netInputHeight;
        info.at<int>(0, 1) = netInputWidth;
        info.at<int>(0, 2) = 1;
        auto allocator = std::make_shared<SharedTensorAllocator>(info);
        ov::Tensor infoInput = ov::Tensor(ov::element::i32, ov::Shape({1, 3}),  ov::Allocator(allocator));

        input.emplace(inputNames[1], infoInput);
    }
    return DetectionModel::preprocess(inputData, input);
}

std::unique_ptr<ResultBase> ModelSSD::postprocess(InferenceResult& infResult) {
    return outputNames.size() > 1 ? postprocessMultipleOutputs(infResult) : postprocessSingleOutput(infResult);
}

std::unique_ptr<ResultBase> ModelSSD::postprocessSingleOutput(InferenceResult& infResult) {
    const ov::Tensor& detectionsTensor = infResult.getFirstOutputTensor();
    size_t detectionsNum = detectionsTensor.get_shape()[detectionsNumId];
    const float* detections = detectionsTensor.data<float>();

    DetectionResult* result = new DetectionResult(infResult.frameId, infResult.metaData);
    auto retVal = std::unique_ptr<ResultBase>(result);

    const auto& internalData = infResult.internalModelData->asRef<InternalImageModelData>();
    float floatInputImgWidth = float(internalData.inputImgWidth),
         floatInputImgHeight = float(internalData.inputImgHeight);
    float invertedScaleX = floatInputImgWidth / netInputWidth,
          invertedScaleY = floatInputImgHeight / netInputHeight;
    int padLeft = 0, padTop = 0;
    if (RESIZE_KEEP_ASPECT == resizeMode || RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
        invertedScaleX = invertedScaleY = std::max(invertedScaleX, invertedScaleY);
        if (RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
            padLeft = (netInputWidth - int(floatInputImgWidth / invertedScaleX)) / 2;
            padTop = (netInputHeight - int(floatInputImgHeight / invertedScaleY)) / 2;
        }
    }

    for (size_t i = 0; i < detectionsNum; i++) {
        float image_id = detections[i * objectSize + 0];
        if (image_id < 0) {
            break;
        }

        float confidence = detections[i * objectSize + 2];

        /** Filtering out objects with confidence < confidence_threshold probability **/
        if (confidence > confidenceThreshold) {
            DetectedObject desc;

            desc.confidence = confidence;
            desc.labelID = static_cast<size_t>(detections[i * objectSize + 1]);
            desc.label = getLabelName(desc.labelID);
            desc.x = clamp(
                round((detections[i * objectSize + 3] * netInputWidth - padLeft) * invertedScaleX),
                0.f,
                floatInputImgWidth);
            desc.y = clamp(
                round((detections[i * objectSize + 4] * netInputHeight - padTop) * invertedScaleY),
                0.f,
                floatInputImgHeight);
            desc.width = clamp(
                round((detections[i * objectSize + 5] * netInputWidth - padLeft) * invertedScaleX - desc.x),
                0.f,
                floatInputImgWidth);
            desc.height = clamp(
                round((detections[i * objectSize + 6] * netInputHeight - padTop) * invertedScaleY - desc.y),
                0.f, floatInputImgHeight);
            result->objects.push_back(desc);
        }
    }

    return retVal;
}

std::unique_ptr<ResultBase> ModelSSD::postprocessMultipleOutputs(InferenceResult& infResult) {
    const float* boxes = infResult.outputsData[outputNames[0]].data<float>();
    size_t detectionsNum = infResult.outputsData[outputNames[0]].get_shape()[detectionsNumId];
    const float* labels = infResult.outputsData[outputNames[1]].data<float>();
    const float* scores = outputNames.size() > 2 ? infResult.outputsData[outputNames[2]].data<float>() : nullptr;

    DetectionResult* result = new DetectionResult(infResult.frameId, infResult.metaData);
    auto retVal = std::unique_ptr<ResultBase>(result);

    const auto& internalData = infResult.internalModelData->asRef<InternalImageModelData>();
    float floatInputImgWidth = float(internalData.inputImgWidth),
         floatInputImgHeight = float(internalData.inputImgHeight);
    float invertedScaleX = floatInputImgWidth / netInputWidth,
          invertedScaleY = floatInputImgHeight / netInputHeight;
    int padLeft = 0, padTop = 0;
    if (RESIZE_KEEP_ASPECT == resizeMode || RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
        invertedScaleX = invertedScaleY = std::max(invertedScaleX, invertedScaleY);
        if (RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
            padLeft = (netInputWidth - int(floatInputImgWidth / invertedScaleX)) / 2;
            padTop = (netInputHeight - int(floatInputImgHeight / invertedScaleY)) / 2;
        }
    }

    // In models with scores stored in separate output coordinates are normalized to [0,1]
    // In other multiple-outputs models coordinates are normalized to [0,netInputWidth] and [0,netInputHeight]
    float widthScale = scores ? netInputWidth : 1.0f;
    float heightScale = scores ? netInputHeight : 1.0f;

    for (size_t i = 0; i < detectionsNum; i++) {
        float confidence = scores ? scores[i] : boxes[i * objectSize + 4];

        /** Filtering out objects with confidence < confidence_threshold probability **/
        if (confidence > confidenceThreshold) {
            DetectedObject desc;

            desc.confidence = confidence;
            desc.labelID = static_cast<int>(labels[i]);
            desc.label = getLabelName(desc.labelID);
            desc.x = clamp(
                round((boxes[i * objectSize] * widthScale - padLeft) * invertedScaleX),
                0.f,
                floatInputImgWidth);
            desc.y = clamp(
                round((boxes[i * objectSize + 1] * heightScale - padTop) * invertedScaleY),
                0.f,
                floatInputImgHeight);
            desc.width = clamp(
                round((boxes[i * objectSize + 2] * widthScale - padLeft) * invertedScaleX - desc.x),
                0.f,
                floatInputImgWidth);
            desc.height = clamp(
                round((boxes[i * objectSize + 3] * heightScale - padTop) * invertedScaleY - desc.y),
                0.f, floatInputImgHeight);
            result->objects.push_back(desc);
        }
    }

    return retVal;
}

void ModelSSD::prepareInputsOutputs(std::shared_ptr<ov::Model>& model) {
    // --------------------------- Configure input & output -------------------------------------------------
    // --------------------------- Prepare input ------------------------------------------------------
    for (const auto& input : model->inputs()) {
        auto inputTensorName = input.get_any_name();
        const ov::Shape& shape = input.get_partial_shape().get_max_shape();
        ov::Layout inputLayout = getInputLayout(input);

        if (shape.size() == 4) {  // 1st input contains images
            if (inputNames.empty()) {
                inputNames.push_back(inputTensorName);
            } else {
                inputNames[0] = inputTensorName;
            }

            if (!embedded_processing) {
                model = ImageModel::embedProcessing(model,
                                        inputNames[0],
                                        inputLayout,
                                        resizeMode,
                                        interpolationMode,
                                        ov::Shape{shape[ov::layout::width_idx(inputLayout)],
                                                  shape[ov::layout::height_idx(inputLayout)]});

                netInputWidth = shape[ov::layout::width_idx(inputLayout)];
                netInputHeight = shape[ov::layout::height_idx(inputLayout)];

                useAutoResize = true; // temporal solution for SSD
                embedded_processing = true;
            }
        } else if (shape.size() == 2) {  // 2nd input contains image info
            inputNames.resize(2);
            inputNames[1] = inputTensorName;
            if (!embedded_processing) {
                ov::preprocess::PrePostProcessor ppp(model);
                ppp.input(inputTensorName).tensor().set_element_type(ov::element::f32);
                model = ppp.build();
            }
        } else {
            throw std::logic_error("Unsupported " + std::to_string(input.get_partial_shape().size()) +
                                   "D "
                                   "input layer '" +
                                   input.get_any_name() +
                                   "'. "
                                   "Only 2D and 4D input layers are supported");
        }
    }

    // --------------------------- Prepare output  -----------------------------------------------------
    if (model->outputs().size() == 1) {
        prepareSingleOutput(model);
    } else {
        prepareMultipleOutputs(model);
    }
    embedded_processing = true;
}

void ModelSSD::prepareSingleOutput(std::shared_ptr<ov::Model>& model) {
    const auto& output = model->output();
    outputNames.push_back(output.get_any_name());

    const ov::Shape& shape = output.get_partial_shape().get_max_shape();
    const ov::Layout& layout("NCHW");
    if (shape.size() != 4) {
        throw std::logic_error("SSD single output must have 4 dimensions, but had " + std::to_string(shape.size()));
    }
    detectionsNumId = ov::layout::height_idx(layout);
    objectSize = shape[ov::layout::width_idx(layout)];
    if (objectSize != 7) {
        throw std::logic_error("SSD single output must have 7 as a last dimension, but had " +
                               std::to_string(objectSize));
    }

    if (!embedded_processing) {
        ov::preprocess::PrePostProcessor ppp(model);
        ppp.output().tensor().set_element_type(ov::element::f32).set_layout(layout);
        model = ppp.build();
    }
}

void ModelSSD::prepareMultipleOutputs(std::shared_ptr<ov::Model>& model) {
    const ov::OutputVector& outputs = model->outputs();
    for (auto& output : outputs) {
        const auto& tensorNames = output.get_names();
        for (const auto& name : tensorNames) {
            if (name.find("boxes") != std::string::npos) {
                outputNames.push_back(name);
                break;
            } else if (name.find("labels") != std::string::npos) {
                outputNames.push_back(name);
                break;
            } else if (name.find("scores") != std::string::npos) {
                outputNames.push_back(name);
                break;
            }
        }
    }
    if (outputNames.size() != 2 && outputNames.size() != 3) {
        throw std::logic_error("SSD model wrapper must have 2 or 3 outputs, but had " +
                               std::to_string(outputNames.size()));
    }
    std::sort(outputNames.begin(), outputNames.end());

    const auto& boxesShape = model->output(outputNames[0]).get_partial_shape().get_max_shape();

    ov::Layout boxesLayout;
    if (boxesShape.size() == 2) {
        boxesLayout = "NC";
        detectionsNumId = ov::layout::batch_idx(boxesLayout);
        objectSize = boxesShape[ov::layout::channels_idx(boxesLayout)];

        if (objectSize != 5) {
            throw std::logic_error("Incorrect 'boxes' output shape, [n][5] shape is required");
        }
    } else if (boxesShape.size() == 3) {
        boxesLayout = "CHW";
        detectionsNumId = ov::layout::height_idx(boxesLayout);
        objectSize = boxesShape[ov::layout::width_idx(boxesLayout)];

        if (objectSize != 4 && objectSize != 5) {
            throw std::logic_error("Incorrect 'boxes' output shape, [b][n][{4 or 5}] shape is required");
        }
    } else {
        throw std::logic_error("Incorrect number of 'boxes' output dimensions, expected 2 or 3, but had " +
                               std::to_string(boxesShape.size()));
    }

    if (!embedded_processing) {
        ov::preprocess::PrePostProcessor ppp(model);
        ppp.output(outputNames[0]).tensor().set_layout(boxesLayout);

        for (const auto& outName : outputNames) {
            ppp.output(outName).tensor().set_element_type(ov::element::f32);
        }
        model = ppp.build();
    }
}

void ModelSSD::updateModelInfo() {
    DetectionModel::updateModelInfo();

    model->set_rt_info(ModelSSD::ModelType, "model_info", "model_type");
    model->set_rt_info(objectSize, "model_info", "object_size");
    model->set_rt_info(detectionsNumId, "model_info", "detections_num_id");
}
