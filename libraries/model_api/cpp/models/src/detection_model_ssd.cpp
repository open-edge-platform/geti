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

ModelSSD::ModelSSD(const std::string& modelFile,
                   float confidenceThreshold,
                   const std::string& resize_type,
                   bool useAutoResize,
                   const std::vector<std::string>& labels,
                   const std::string& layout)
    : DetectionModel(modelFile, confidenceThreshold, resize_type, useAutoResize, labels, layout) {}

std::shared_ptr<InternalModelData> ModelSSD::preprocess(const InputData& inputData, InferenceInput& input) {
    if (inputNames.size() > 1) {
        cv::Mat info(cv::Size(1, 3), CV_32SC1);
        info.at<int>(0, 0) = static_cast<float>(netInputHeight);
        info.at<int>(0, 1) = static_cast<float>(netInputWidth);
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
    float floatInputImgWidth = internalData.inputImgWidth,
         floatInputImgHeight = internalData.inputImgHeight;
    float invertedScaleX = floatInputImgWidth / netInputWidth,
          invertedScaleY = floatInputImgHeight / netInputHeight;
    int padLeft = 0, padTop = 0;
    if (RESIZE_KEEP_ASPECT == resizeMode || RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
        invertedScaleX = invertedScaleY = std::max(invertedScaleX, invertedScaleY);
        if (RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
            padLeft = (netInputWidth - floatInputImgWidth / invertedScaleX) / 2;
            padTop = (netInputHeight - floatInputImgHeight / invertedScaleY) / 2;
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
            desc.labelID = static_cast<int>(detections[i * objectSize + 1]);
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

    // In models with scores are stored in separate output, coordinates are normalized to [0,1]
    // In other multiple-outputs models coordinates are normalized to [0,netInputWidth] and [0,netInputHeight]
    float widthScale = static_cast<float>(internalData.inputImgWidth) / (scores ? 1 : netInputWidth);
    float heightScale = static_cast<float>(internalData.inputImgHeight) / (scores ? 1 : netInputHeight);

    for (size_t i = 0; i < detectionsNum; i++) {
        float confidence = scores ? scores[i] : boxes[i * objectSize + 4];

        /** Filtering out objects with confidence < confidence_threshold probability **/
        if (confidence > confidenceThreshold) {
            DetectedObject desc;

            desc.confidence = confidence;
            desc.labelID = static_cast<int>(labels[i]);
            desc.label = getLabelName(desc.labelID);

            desc.x = clamp(boxes[i * objectSize] * widthScale, 0.f, static_cast<float>(internalData.inputImgWidth));
            desc.y =
                clamp(boxes[i * objectSize + 1] * heightScale, 0.f, static_cast<float>(internalData.inputImgHeight));
            desc.width =
                clamp(boxes[i * objectSize + 2] * widthScale, 0.f, static_cast<float>(internalData.inputImgWidth)) -
                desc.x;
            desc.height =
                clamp(boxes[i * objectSize + 3] * heightScale, 0.f, static_cast<float>(internalData.inputImgHeight)) -
                desc.y;

            result->objects.push_back(desc);
        }
    }

    return retVal;
}

void ModelSSD::prepareInputsOutputs(std::shared_ptr<ov::Model>& model) {
    // --------------------------- Configure input & output -------------------------------------------------
    // --------------------------- Prepare input ------------------------------------------------------
    ov::preprocess::PrePostProcessor ppp(model);
    for (const auto& input : model->inputs()) {
        auto inputTensorName = input.get_any_name();
        const ov::Shape& shape = input.get_shape();
        ov::Layout inputLayout = getInputLayout(input);

        if (shape.size() == 4) {  // 1st input contains images
            if (inputNames.empty()) {
                inputNames.push_back(inputTensorName);
            } else {
                inputNames[0] = inputTensorName;
            }

            inputTransform.setPrecision(ppp, inputTensorName);
            ppp.input(inputTensorName).tensor().set_layout({"NHWC"});

            if (useAutoResize) {
                ppp.input(inputTensorName).tensor().set_spatial_dynamic_shape();

                ppp.input(inputTensorName)
                    .preprocess()
                    .convert_element_type(ov::element::f32)
                    .resize(ov::preprocess::ResizeAlgorithm::RESIZE_LINEAR);
            }

            ppp.input(inputTensorName).model().set_layout(inputLayout);

            netInputWidth = shape[ov::layout::width_idx(inputLayout)];
            netInputHeight = shape[ov::layout::height_idx(inputLayout)];
        } else if (shape.size() == 2) {  // 2nd input contains image info
            inputNames.resize(2);
            inputNames[1] = inputTensorName;
            ppp.input(inputTensorName).tensor().set_element_type(ov::element::f32);
        } else {
            throw std::logic_error("Unsupported " + std::to_string(input.get_shape().size()) +
                                   "D "
                                   "input layer '" +
                                   input.get_any_name() +
                                   "'. "
                                   "Only 2D and 4D input layers are supported");
        }
    }
    model = ppp.build();

    // --------------------------- Prepare output  -----------------------------------------------------
    if (model->outputs().size() == 1) {
        prepareSingleOutput(model);
    } else {
        prepareMultipleOutputs(model);
    }
}

void ModelSSD::prepareSingleOutput(std::shared_ptr<ov::Model>& model) {
    const auto& output = model->output();
    outputNames.push_back(output.get_any_name());

    const ov::Shape& shape = output.get_shape();
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
    ov::preprocess::PrePostProcessor ppp(model);
    ppp.output().tensor().set_element_type(ov::element::f32).set_layout(layout);
    model = ppp.build();
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

    ov::preprocess::PrePostProcessor ppp(model);
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

        if (objectSize != 4) {
            throw std::logic_error("Incorrect 'boxes' output shape, [b][n][4] shape is required");
        }
    } else {
        throw std::logic_error("Incorrect number of 'boxes' output dimensions, expected 2 or 3, but had " +
                               std::to_string(boxesShape.size()));
    }

    ppp.output(outputNames[0]).tensor().set_layout(boxesLayout);

    for (const auto& outName : outputNames) {
        ppp.output(outName).tensor().set_element_type(ov::element::f32);
    }
    model = ppp.build();
}
