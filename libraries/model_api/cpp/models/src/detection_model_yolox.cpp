/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "models/detection_model_yolox.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <openvino/openvino.hpp>
#include <stdexcept>
#include <string>
#include <utility>
#include <utils/common.hpp>
#include <utils/slog.hpp>
#include <vector>

#include "models/input_data.h"
#include "models/internal_model_data.h"
#include "models/results.h"
#include "utils/image_utils.h"
#include "utils/nms.hpp"

std::string ModelYoloX::ModelType = "yolox";

void ModelYoloX::initDefaultParameters(const ov::AnyMap&) {
    resizeMode = RESIZE_KEEP_ASPECT;  // Ignore configuration for now
    useAutoResize = false;
}

ModelYoloX::ModelYoloX(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : DetectionModelExt(model, configuration) {
    initDefaultParameters(configuration);
}

ModelYoloX::ModelYoloX(std::shared_ptr<InferenceAdapter>& adapter) : DetectionModelExt(adapter) {
    const ov::AnyMap& configuration = adapter->getModelConfig();
    initDefaultParameters(configuration);
}

void ModelYoloX::updateModelInfo() {
    DetectionModelExt::updateModelInfo();

    model->set_rt_info(ModelYoloX::ModelType, "model_info", "model_type");
}

void ModelYoloX::prepareInputsOutputs(std::shared_ptr<ov::Model>& model) {
    // --------------------------- Configure input & output -------------------------------------------------
    // --------------------------- Prepare input  ------------------------------------------------------
    const ov::OutputVector& inputs = model->inputs();
    if (inputs.size() != 1) {
        throw std::logic_error("YOLOX model wrapper accepts models that have only 1 input");
    }

    //--- Check image input
    const auto& input = model->input();
    const ov::Shape& inputShape = model->input().get_shape();
    ov::Layout inputLayout = getInputLayout(input);

    if (inputShape.size() != 4 && inputShape[ov::layout::channels_idx(inputLayout)] != 3) {
        throw std::logic_error("Expected 4D image input with 3 channels");
    }

    ov::preprocess::PrePostProcessor ppp(model);
    ppp.input().tensor().set_element_type(ov::element::u8).set_layout({"NHWC"});

    ppp.input().model().set_layout(inputLayout);

    //--- Reading image input parameters
    inputNames.push_back(input.get_any_name());
    netInputWidth = inputShape[ov::layout::width_idx(inputLayout)];
    netInputHeight = inputShape[ov::layout::height_idx(inputLayout)];
    setStridesGrids();

    // --------------------------- Prepare output  -----------------------------------------------------
    if (model->outputs().size() != 1) {
        throw std::logic_error("YoloX model wrapper expects models that have only 1 output");
    }
    const auto& output = model->output();
    outputNames.push_back(output.get_any_name());
    const ov::Shape& shape = output.get_shape();

    if (shape.size() != 3) {
        throw std::logic_error("YOLOX single output must have 3 dimensions, but had " + std::to_string(shape.size()));
    }
    ppp.output().tensor().set_element_type(ov::element::f32);

    model = ppp.build();
}

void ModelYoloX::setStridesGrids() {
    std::vector<size_t> strides = {8, 16, 32};
    std::vector<size_t> hsizes(3);
    std::vector<size_t> wsizes(3);

    for (size_t i = 0; i < strides.size(); ++i) {
        hsizes[i] = netInputHeight / strides[i];
        wsizes[i] = netInputWidth / strides[i];
    }

    for (size_t size_index = 0; size_index < hsizes.size(); ++size_index) {
        for (size_t h_index = 0; h_index < hsizes[size_index]; ++h_index) {
            for (size_t w_index = 0; w_index < wsizes[size_index]; ++w_index) {
                grids.emplace_back(w_index, h_index);
                expandedStrides.push_back(strides[size_index]);
            }
        }
    }
}

std::shared_ptr<InternalModelData> ModelYoloX::preprocess(const InputData& inputData, InferenceInput& input) {
    const auto& origImg = inputData.asRef<ImageInputData>().inputImage;
    float scale =
        std::min(static_cast<float>(netInputWidth) / origImg.cols, static_cast<float>(netInputHeight) / origImg.rows);

    cv::Mat resizedImage = resizeImageExt(origImg,
                                          netInputWidth,
                                          netInputHeight,
                                          resizeMode,
                                          interpolationMode,
                                          nullptr,
                                          cv::Scalar(114, 114, 114));

    input.emplace(inputNames[0], wrapMat2Tensor(resizedImage));
    return std::make_shared<InternalScaleData>(origImg.cols, origImg.rows, scale, scale);
}

std::unique_ptr<ResultBase> ModelYoloX::postprocess(InferenceResult& infResult) {
    // Get metadata about input image shape and scale
    const auto& scale = infResult.internalModelData->asRef<InternalScaleData>();

    // Get output tensor
    const ov::Tensor& output = infResult.outputsData[outputNames[0]];
    const auto& outputShape = output.get_shape();
    float* outputPtr = output.data<float>();

    // Generate detection results
    DetectionResult* result = new DetectionResult(infResult.frameId, infResult.metaData);

    // Update coordinates according to strides
    for (size_t box_index = 0; box_index < expandedStrides.size(); ++box_index) {
        size_t startPos = outputShape[2] * box_index;
        outputPtr[startPos] = (outputPtr[startPos] + grids[box_index].first) * expandedStrides[box_index];
        outputPtr[startPos + 1] = (outputPtr[startPos + 1] + grids[box_index].second) * expandedStrides[box_index];
        outputPtr[startPos + 2] = std::exp(outputPtr[startPos + 2]) * expandedStrides[box_index];
        outputPtr[startPos + 3] = std::exp(outputPtr[startPos + 3]) * expandedStrides[box_index];
    }

    // Filter predictions
    std::vector<Anchor> validBoxes;
    std::vector<float> scores;
    std::vector<size_t> classes;
    for (size_t box_index = 0; box_index < expandedStrides.size(); ++box_index) {
        size_t startPos = outputShape[2] * box_index;
        float score = outputPtr[startPos + 4];
        if (score < confidence_threshold)
            continue;
        float maxClassScore = -1;
        size_t mainClass = 0;
        for (size_t class_index = 0; class_index < numberOfClasses; ++class_index) {
            if (outputPtr[startPos + 5 + class_index] > maxClassScore) {
                maxClassScore = outputPtr[startPos + 5 + class_index];
                mainClass = class_index;
            }
        }

        // Filter by score
        score *= maxClassScore;
        if (score < confidence_threshold)
            continue;

        // Add successful boxes
        scores.push_back(score);
        classes.push_back(mainClass);
        Anchor trueBox = {outputPtr[startPos + 0] - outputPtr[startPos + 2] / 2,
                          outputPtr[startPos + 1] - outputPtr[startPos + 3] / 2,
                          outputPtr[startPos + 0] + outputPtr[startPos + 2] / 2,
                          outputPtr[startPos + 1] + outputPtr[startPos + 3] / 2};
        validBoxes.push_back(Anchor({trueBox.left / scale.scaleX,
                                     trueBox.top / scale.scaleY,
                                     trueBox.right / scale.scaleX,
                                     trueBox.bottom / scale.scaleY}));
    }

    // NMS for valid boxes
    const std::vector<size_t>& keep = nms(validBoxes, scores, iou_threshold, true);
    for (size_t index : keep) {
        // Create new detected box
        DetectedObject obj;
        obj.x = clamp(validBoxes[index].left, 0.f, static_cast<float>(scale.inputImgWidth));
        obj.y = clamp(validBoxes[index].top, 0.f, static_cast<float>(scale.inputImgHeight));
        obj.height =
            clamp(validBoxes[index].bottom - validBoxes[index].top, 0.f, static_cast<float>(scale.inputImgHeight));
        obj.width =
            clamp(validBoxes[index].right - validBoxes[index].left, 0.f, static_cast<float>(scale.inputImgWidth));
        obj.confidence = scores[index];
        obj.labelID = classes[index];
        obj.label = getLabelName(classes[index]);
        result->objects.push_back(obj);
    }

    return std::unique_ptr<ResultBase>(result);
}
