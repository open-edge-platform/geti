/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "models/detection_model_ssd.h"

#include <algorithm>
#include <map>
#include <openvino/openvino.hpp>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utils/common.hpp>
#include <utils/ocv_common.hpp>
#include <vector>

#include "models/internal_model_data.h"
#include "models/results.h"

namespace {
constexpr char saliency_map_name[]{"saliency_map"};
constexpr char feature_vector_name[]{"feature_vector"};
constexpr float box_area_threshold = 1.0f;

struct NumAndStep {
    size_t detectionsNum, objectSize;
};

NumAndStep fromSingleOutput(const ov::Shape& shape) {
    const ov::Layout& layout("NCHW");
    if (shape.size() != 4) {
        throw std::logic_error("SSD single output must have 4 dimensions, but had " + std::to_string(shape.size()));
    }
    size_t detectionsNum = shape[ov::layout::height_idx(layout)];
    size_t objectSize = shape[ov::layout::width_idx(layout)];
    if (objectSize != 7) {
        throw std::logic_error("SSD single output must have 7 as a last dimension, but had " +
                               std::to_string(objectSize));
    }
    return {detectionsNum, objectSize};
}

NumAndStep fromMultipleOutputs(const ov::Shape& boxesShape) {
    if (boxesShape.size() == 2) {
        ov::Layout boxesLayout = "NC";
        size_t detectionsNum = boxesShape[ov::layout::batch_idx(boxesLayout)];
        size_t objectSize = boxesShape[ov::layout::channels_idx(boxesLayout)];

        if (objectSize != 5) {
            throw std::logic_error("Incorrect 'boxes' output shape, [n][5] shape is required");
        }
        return {detectionsNum, objectSize};
    }
    if (boxesShape.size() == 3) {
        ov::Layout boxesLayout = "CHW";
        size_t detectionsNum = boxesShape[ov::layout::height_idx(boxesLayout)];
        size_t objectSize = boxesShape[ov::layout::width_idx(boxesLayout)];

        if (objectSize != 4 && objectSize != 5) {
            throw std::logic_error("Incorrect 'boxes' output shape, [b][n][{4 or 5}] shape is required");
        }
        return {detectionsNum, objectSize};
    }
    throw std::logic_error("Incorrect number of 'boxes' output dimensions, expected 2 or 3, but had " +
                           std::to_string(boxesShape.size()));
}

std::vector<std::string> filterOutXai(const std::vector<std::string>& names) {
    std::vector<std::string> filtered;
    std::copy_if(names.begin(), names.end(), std::back_inserter(filtered), [](const std::string& name) {
        return name != saliency_map_name && name != feature_vector_name;
    });
    return filtered;
}

float clamp_and_round(float val, float min, float max) {
    return std::round(std::max(min, std::min(max, val)));
}
}  // namespace

std::string ModelSSD::ModelType = "ssd";

std::shared_ptr<InternalModelData> ModelSSD::preprocess(const InputData& inputData, InferenceInput& input) {
    if (inputNames.size() > 1) {
        ov::Tensor info{ov::element::i32, ov::Shape({1, 3})};
        int32_t* data = info.data<int32_t>();
        data[0] = netInputHeight;
        data[1] = netInputWidth;
        data[3] = 1;
        input.emplace(inputNames[1], std::move(info));
    }
    return DetectionModel::preprocess(inputData, input);
}

std::unique_ptr<ResultBase> ModelSSD::postprocess(InferenceResult& infResult) {
    std::unique_ptr<ResultBase> result = filterOutXai(outputNames).size() > 1 ? postprocessMultipleOutputs(infResult)
                                                                              : postprocessSingleOutput(infResult);
    DetectionResult* cls_res = static_cast<DetectionResult*>(result.get());
    auto saliency_map_iter = infResult.outputsData.find(saliency_map_name);
    if (saliency_map_iter != infResult.outputsData.end()) {
        cls_res->saliency_map = std::move(saliency_map_iter->second);
    }
    auto feature_vector_iter = infResult.outputsData.find(feature_vector_name);
    if (feature_vector_iter != infResult.outputsData.end()) {
        cls_res->feature_vector = std::move(feature_vector_iter->second);
    }
    return result;
}

std::unique_ptr<ResultBase> ModelSSD::postprocessSingleOutput(InferenceResult& infResult) {
    const std::vector<std::string> namesWithoutXai = filterOutXai(outputNames);
    assert(namesWithoutXai.size() == 1);
    const ov::Tensor& detectionsTensor = infResult.outputsData[namesWithoutXai[0]];
    NumAndStep numAndStep = fromSingleOutput(detectionsTensor.get_shape());
    const float* detections = detectionsTensor.data<float>();

    DetectionResult* result = new DetectionResult(infResult.frameId, infResult.metaData);
    auto retVal = std::unique_ptr<ResultBase>(result);

    const auto& internalData = infResult.internalModelData->asRef<InternalImageModelData>();
    float floatInputImgWidth = float(internalData.inputImgWidth),
          floatInputImgHeight = float(internalData.inputImgHeight);
    float invertedScaleX = floatInputImgWidth / netInputWidth, invertedScaleY = floatInputImgHeight / netInputHeight;
    int padLeft = 0, padTop = 0;
    if (RESIZE_KEEP_ASPECT == resizeMode || RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
        invertedScaleX = invertedScaleY = std::max(invertedScaleX, invertedScaleY);
        if (RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
            padLeft = (netInputWidth - int(std::round(floatInputImgWidth / invertedScaleX))) / 2;
            padTop = (netInputHeight - int(std::round(floatInputImgHeight / invertedScaleY))) / 2;
        }
    }

    for (size_t i = 0; i < numAndStep.detectionsNum; i++) {
        float image_id = detections[i * numAndStep.objectSize + 0];
        if (image_id < 0) {
            break;
        }

        float confidence = detections[i * numAndStep.objectSize + 2];

        /** Filtering out objects with confidence < confidence_threshold probability **/
        if (confidence > confidence_threshold) {
            DetectedObject desc;

            desc.confidence = confidence;
            desc.labelID = static_cast<size_t>(detections[i * numAndStep.objectSize + 1]);
            desc.label = getLabelName(desc.labelID);
            desc.x =
                clamp(round((detections[i * numAndStep.objectSize + 3] * netInputWidth - padLeft) * invertedScaleX),
                      0.f,
                      floatInputImgWidth);
            desc.y =
                clamp(round((detections[i * numAndStep.objectSize + 4] * netInputHeight - padTop) * invertedScaleY),
                      0.f,
                      floatInputImgHeight);
            desc.width =
                clamp(round((detections[i * numAndStep.objectSize + 5] * netInputWidth - padLeft) * invertedScaleX),
                      0.f,
                      floatInputImgWidth) -
                desc.x;
            desc.height =
                clamp(round((detections[i * numAndStep.objectSize + 6] * netInputHeight - padTop) * invertedScaleY),
                      0.f,
                      floatInputImgHeight) -
                desc.y;
            result->objects.push_back(desc);
        }
    }

    return retVal;
}

std::unique_ptr<ResultBase> ModelSSD::postprocessMultipleOutputs(InferenceResult& infResult) {
    const std::vector<std::string> namesWithoutXai = filterOutXai(outputNames);
    const float* boxes = infResult.outputsData[namesWithoutXai[0]].data<float>();
    NumAndStep numAndStep = fromMultipleOutputs(infResult.outputsData[namesWithoutXai[0]].get_shape());
    const int64_t* labels = infResult.outputsData[namesWithoutXai[1]].data<int64_t>();
    const float* scores =
        namesWithoutXai.size() > 2 ? infResult.outputsData[namesWithoutXai[2]].data<float>() : nullptr;

    DetectionResult* result = new DetectionResult(infResult.frameId, infResult.metaData);
    auto retVal = std::unique_ptr<ResultBase>(result);

    const auto& internalData = infResult.internalModelData->asRef<InternalImageModelData>();
    float floatInputImgWidth = float(internalData.inputImgWidth),
          floatInputImgHeight = float(internalData.inputImgHeight);
    float invertedScaleX = floatInputImgWidth / netInputWidth, invertedScaleY = floatInputImgHeight / netInputHeight;
    int padLeft = 0, padTop = 0;
    if (RESIZE_KEEP_ASPECT == resizeMode || RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
        invertedScaleX = invertedScaleY = std::max(invertedScaleX, invertedScaleY);
        if (RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
            padLeft = (netInputWidth - int(std::round(floatInputImgWidth / invertedScaleX))) / 2;
            padTop = (netInputHeight - int(std::round(floatInputImgHeight / invertedScaleY))) / 2;
        }
    }

    // In models with scores stored in separate output coordinates are normalized to [0,1]
    // In other multiple-outputs models coordinates are normalized to [0,netInputWidth] and [0,netInputHeight]
    float widthScale = scores ? netInputWidth : 1.0f;
    float heightScale = scores ? netInputHeight : 1.0f;

    for (size_t i = 0; i < numAndStep.detectionsNum; i++) {
        float confidence = scores ? scores[i] : boxes[i * numAndStep.objectSize + 4];

        /** Filtering out objects with confidence < confidence_threshold probability **/
        if (confidence > confidence_threshold) {
            DetectedObject desc;

            desc.confidence = confidence;
            desc.labelID = labels[i];
            desc.label = getLabelName(desc.labelID);
            desc.x = clamp_and_round((boxes[i * numAndStep.objectSize] * widthScale - padLeft) * invertedScaleX,
                                     0.f,
                                     floatInputImgWidth);
            desc.y = clamp_and_round((boxes[i * numAndStep.objectSize + 1] * heightScale - padTop) * invertedScaleY,
                                     0.f,
                                     floatInputImgHeight);
            desc.width = clamp_and_round((boxes[i * numAndStep.objectSize + 2] * widthScale - padLeft) * invertedScaleX,
                                         0.f,
                                         floatInputImgWidth) -
                         desc.x;
            desc.height =
                clamp_and_round((boxes[i * numAndStep.objectSize + 3] * heightScale - padTop) * invertedScaleY,
                                0.f,
                                floatInputImgHeight) -
                desc.y;

            if (desc.width * desc.height >= box_area_threshold) {
                result->objects.push_back(desc);
            }
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
                model = ImageModel::embedProcessing(
                    model,
                    inputNames[0],
                    inputLayout,
                    resizeMode,
                    interpolationMode,
                    ov::Shape{shape[ov::layout::width_idx(inputLayout)], shape[ov::layout::height_idx(inputLayout)]},
                    pad_value,
                    reverse_input_channels,
                    mean_values,
                    scale_values);

                netInputWidth = shape[ov::layout::width_idx(inputLayout)];
                netInputHeight = shape[ov::layout::height_idx(inputLayout)];

                useAutoResize = true;  // temporal solution for SSD
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

    fromSingleOutput(output.get_partial_shape().get_max_shape());

    if (!embedded_processing) {
        ov::preprocess::PrePostProcessor ppp(model);
        ppp.output().tensor().set_element_type(ov::element::f32);
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

    fromMultipleOutputs(model->output(outputNames[0]).get_partial_shape().get_max_shape());

    if (!embedded_processing) {
        ov::preprocess::PrePostProcessor ppp(model);

        for (const auto& outName : outputNames) {
            ppp.output(outName).tensor().set_element_type(ov::element::f32);
        }
        model = ppp.build();
    }
}

void ModelSSD::updateModelInfo() {
    DetectionModel::updateModelInfo();

    model->set_rt_info(ModelSSD::ModelType, "model_info", "model_type");
}
