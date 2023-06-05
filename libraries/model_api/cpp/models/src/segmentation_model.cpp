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

#include "models/segmentation_model.h"

#include <stddef.h>
#include <stdint.h>

#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <openvino/openvino.hpp>

#include "models/internal_model_data.h"
#include "models/input_data.h"
#include "models/results.h"
#include "utils/slog.hpp"

namespace {
cv::Mat create_hard_prediction_from_soft_prediction(const cv::Mat& soft_prediction, float soft_threshold, int blur_strength) {
    cv::Mat soft_prediction_blurred;
    cv::blur(soft_prediction, soft_prediction_blurred, cv::Size{blur_strength, blur_strength});
    assert(soft_prediction_blurred.channels() > 1);
    cv::Mat hard_prediction{cv::Size{soft_prediction_blurred.rows, soft_prediction_blurred.cols}, CV_8UC1};
    for (int i = 0; i < soft_prediction_blurred.rows; ++i) {
        for (int j = 0; j < soft_prediction_blurred.cols; ++j) {
            float max_prob = -std::numeric_limits<float>::infinity();
            uint8_t max_id = 0;
            for (int c = 0; c < soft_prediction_blurred.channels(); ++c) {
                float prob = ((float*)soft_prediction_blurred.ptr(i, j))[c];
                if (prob >= soft_threshold && prob > max_prob) {
                    max_prob = prob;
                    max_id = c;
                }
            }
            hard_prediction.at<uint8_t>(i, j) = max_id;
        }
    }
    return hard_prediction;
}
}

std::string SegmentationModel::ModelType = "Segmentation";

SegmentationModel::SegmentationModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
        : ImageModel(model, configuration) {
    auto blur_strength_iter = configuration.find("blur_strength");
    if (blur_strength_iter == configuration.end()) {
        if (model->has_rt_info("model_info", "blur_strength")) {
            blur_strength = model->get_rt_info<int>("model_info", "blur_strength");
        }
    } else {
        blur_strength = blur_strength_iter->second.as<int>();
    }
    auto soft_threshold_iter = configuration.find("soft_threshold");
    if (soft_threshold_iter == configuration.end()) {
        if (model->has_rt_info("model_info", "soft_threshold")) {
            soft_threshold = model->get_rt_info<float>("model_info", "soft_threshold");
        }
    } else {
        soft_threshold = soft_threshold_iter->second.as<float>();
    }
    auto return_soft_prediction_iter = configuration.find("return_soft_prediction");
    if (return_soft_prediction_iter == configuration.end()) {
        if (model->has_rt_info("model_info", "return_soft_prediction")) {
            std::string val = model->get_rt_info<std::string>("model_info", "return_soft_prediction");
            return_soft_prediction = val == "True" || val == "YES";
        }
    } else {
        std::string val = return_soft_prediction_iter->second.as<std::string>();
        return_soft_prediction = val == "True" || val == "YES";
    }
}

SegmentationModel::SegmentationModel(std::shared_ptr<InferenceAdapter>& adapter)
        : ImageModel(adapter) {
    const ov::AnyMap& configuration = adapter->getModelConfig();
    auto blur_strength_iter = configuration.find("blur_strength");
    if (blur_strength_iter != configuration.end()) {
        blur_strength = blur_strength_iter->second.as<int>();
    }
    auto soft_threshold_iter = configuration.find("soft_threshold");
    if (soft_threshold_iter != configuration.end()) {
        soft_threshold = soft_threshold_iter->second.as<float>();
    }
    auto return_soft_prediction_iter = configuration.find("return_soft_prediction");
    if (return_soft_prediction_iter != configuration.end()) {
        std::string val = return_soft_prediction_iter->second.as<std::string>();
        return_soft_prediction = val == "True" || val == "YES";
    }
}

std::unique_ptr<SegmentationModel> SegmentationModel::create_model(const std::string& modelFile, const ov::AnyMap& configuration, bool preload, const std::string& device) {
    auto core = ov::Core();
    std::shared_ptr<ov::Model> model = core.read_model(modelFile);

    // Check model_type in the rt_info, ignore configuration
    std::string model_type = SegmentationModel::ModelType;
    try {
        if (model->has_rt_info("model_info", "model_type") ) {
            model_type = model->get_rt_info<std::string>("model_info", "model_type");
        }
    } catch (const std::exception&) {
        slog::warn << "Model type is not specified in the rt_info, use default model type: " << model_type << slog::endl;
    }

    if (model_type != SegmentationModel::ModelType) {
        throw std::runtime_error("Incorrect or unsupported model_type is provided in the model_info section: " + model_type);
    }

    std::unique_ptr<SegmentationModel> segmentor{new SegmentationModel(model, configuration)};
    segmentor->prepare();
    if (preload) {
        segmentor->load(core, device);
    }
    return segmentor;
}

std::unique_ptr<SegmentationModel> SegmentationModel::create_model(std::shared_ptr<InferenceAdapter>& adapter) {
    const ov::AnyMap& configuration = adapter->getModelConfig();
    auto model_type_iter = configuration.find("model_type");
    std::string model_type = SegmentationModel::ModelType;
    if (model_type_iter != configuration.end()) {
        model_type = model_type_iter->second.as<std::string>();
    }

    if (model_type != SegmentationModel::ModelType) {
        throw std::runtime_error("Incorrect or unsupported model_type is provided: " + model_type);
    }

    std::unique_ptr<SegmentationModel> segmentor{new SegmentationModel(adapter)};
    return segmentor;
}

void SegmentationModel::updateModelInfo() {
    ImageModel::updateModelInfo();

    model->set_rt_info(SegmentationModel::ModelType, "model_info", "model_type");
    model->set_rt_info(blur_strength, "model_info", "blur_strength");
    model->set_rt_info(soft_threshold, "model_info", "soft_threshold");
    model->set_rt_info(return_soft_prediction, "model_info", "return_soft_prediction");
}

void SegmentationModel::prepareInputsOutputs(std::shared_ptr<ov::Model>& model) {
    // --------------------------- Configure input & output ---------------------------------------------
    // --------------------------- Prepare input  -----------------------------------------------------
    if (model->inputs().size() != 1) {
        throw std::logic_error("Segmentation model wrapper supports topologies with only 1 input");
    }
    const auto& input = model->input();
    inputNames.push_back(input.get_any_name());

    const ov::Layout& inputLayout = getInputLayout(input);
    const ov::Shape& inputShape = input.get_partial_shape().get_max_shape();
    if (inputShape.size() != 4 || inputShape[ov::layout::channels_idx(inputLayout)] != 3) {
        throw std::logic_error("3-channel 4-dimensional model's input is expected");
    }
    if (model->outputs().size() != 1) {
        throw std::logic_error("Segmentation model wrapper supports topologies with only 1 output");
    }

    if (!embedded_processing) {
        model = ImageModel::embedProcessing(model,
                                        inputNames[0],
                                        inputLayout,
                                        resizeMode,
                                        interpolationMode,
                                        ov::Shape{inputShape[ov::layout::width_idx(inputLayout)],
                                                  inputShape[ov::layout::height_idx(inputLayout)]},
                                        pad_value,
                                        reverse_input_channels,
                                        {},
                                        scale_values);

        ov::preprocess::PrePostProcessor ppp = ov::preprocess::PrePostProcessor(model);
        ppp.output().model().set_layout(getLayoutFromShape(model->output().get_partial_shape()));
        ppp.output().tensor().set_element_type(ov::element::f32).set_layout("NCHW");
        model = ppp.build();
        useAutoResize = true; // temporal solution
        embedded_processing = true;
    }

    outputNames.push_back(model->output().get_any_name());
}

std::unique_ptr<ResultBase> SegmentationModel::postprocess(InferenceResult& infResult) {
    const auto& inputImgSize = infResult.internalModelData->asRef<InternalImageModelData>();
    const auto& outTensor = infResult.getFirstOutputTensor();
    const ov::Shape& outputShape = outTensor.get_shape();
    const ov::Layout& outputLayout = getLayoutFromShape(outputShape);
    int outChannels = static_cast<int>(outputShape[ov::layout::channels_idx(outputLayout)]);
    int outHeight = static_cast<int>(outputShape[ov::layout::height_idx(outputLayout)]);
    int outWidth = static_cast<int>(outputShape[ov::layout::width_idx(outputLayout)]);
    if (blur_strength == -1 && soft_threshold == std::numeric_limits<float>::infinity()) {
        ImageResult* result = new ImageResult(infResult.frameId, infResult.metaData);
        const auto& inputImgSize = infResult.internalModelData->asRef<InternalImageModelData>();
        const auto& outTensor = infResult.getFirstOutputTensor();

        result->resultImage = cv::Mat(outHeight, outWidth, CV_8UC1);

        if (outChannels == 1 && outTensor.get_element_type() == ov::element::i32) {
            cv::Mat predictions(outHeight, outWidth, CV_32SC1, outTensor.data<int32_t>());
            predictions.convertTo(result->resultImage, CV_8UC1);
        } else if (outChannels == 1 && outTensor.get_element_type() == ov::element::i64) {
            cv::Mat predictions(outHeight, outWidth, CV_32SC1);
            const auto data = outTensor.data<int64_t>();
            for (size_t i = 0; i < predictions.total(); ++i) {
                reinterpret_cast<int32_t*>(predictions.data)[i] = int32_t(data[i]);
            }
            predictions.convertTo(result->resultImage, CV_8UC1);
        } else if (outTensor.get_element_type() == ov::element::f32) {
            const float* data = outTensor.data<float>();
            for (int rowId = 0; rowId < outHeight; ++rowId) {
                for (int colId = 0; colId < outWidth; ++colId) {
                    int classId = 0;
                    float maxProb = -1.0f;
                    for (int chId = 0; chId < outChannels; ++chId) {
                        float prob = data[chId * outHeight * outWidth + rowId * outWidth + colId];
                        if (prob > maxProb) {
                            classId = chId;
                            maxProb = prob;
                        }
                    }  // nChannels

                    result->resultImage.at<uint8_t>(rowId, colId) = classId;
                }  // width
            }  // height
        }

        cv::resize(result->resultImage,
                result->resultImage,
                cv::Size(inputImgSize.inputImgWidth, inputImgSize.inputImgHeight),
                0,
                0,
                cv::INTER_NEAREST);

        return std::unique_ptr<ResultBase>(result);
    }
    float* data = outTensor.data<float>();
    std::vector<cv::Mat> channels;
    for (size_t c = 0; c < outTensor.get_shape()[1]; ++c) {
        channels.emplace_back(cv::Size{outHeight, outWidth}, CV_32F, data + c * outHeight * outWidth);
    }
    cv::Mat soft_prediction;
    cv::merge(channels, soft_prediction);
    cv::Mat hard_prediction = create_hard_prediction_from_soft_prediction(soft_prediction, soft_threshold, blur_strength);
    cv::resize(hard_prediction, hard_prediction, {inputImgSize.inputImgWidth, inputImgSize.inputImgHeight}, 0.0, 0.0, cv::INTER_NEAREST);
    if (return_soft_prediction) {
        cv::resize(soft_prediction, soft_prediction, {inputImgSize.inputImgWidth, inputImgSize.inputImgHeight}, 0.0, 0.0, cv::INTER_NEAREST);
        ImageResultWithSoftPrediction* result = new ImageResultWithSoftPrediction(infResult.frameId, infResult.metaData);
        result->resultImage = hard_prediction;
        result->soft_prediction = soft_prediction;
        return std::unique_ptr<ResultBase>(result);
    }
    ImageResult* result = new ImageResult(infResult.frameId, infResult.metaData);
    result->resultImage = hard_prediction;
    return std::unique_ptr<ResultBase>(result);
}

std::unique_ptr<ImageResult> SegmentationModel::infer(const ImageInputData& inputData) {
    auto result = ModelBase::infer(static_cast<const InputData&>(inputData));
    return std::unique_ptr<ImageResult>(static_cast<ImageResult*>(result.release()));
}
