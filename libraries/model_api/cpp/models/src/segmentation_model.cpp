/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "models/segmentation_model.h"

#include <stddef.h>
#include <stdint.h>

#include <fstream>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <openvino/openvino.hpp>
#include <stdexcept>
#include <string>
#include <vector>

#include "models/input_data.h"
#include "models/internal_model_data.h"
#include "models/results.h"
#include "utils/slog.hpp"

namespace {
constexpr char feature_vector_name[]{"feature_vector"};

cv::Mat get_activation_map(const cv::Mat& features) {
    double min_soft_score, max_soft_score;
    cv::minMaxLoc(features, &min_soft_score, &max_soft_score);
    double factor = 255.0 / (max_soft_score - min_soft_score + 1e-12);

    cv::Mat int_act_map;
    features.convertTo(int_act_map, CV_8U, factor, -min_soft_score * factor);
    return int_act_map;
}
}  // namespace

cv::Mat create_hard_prediction_from_soft_prediction(const cv::Mat& soft_prediction,
                                                    float soft_threshold,
                                                    int blur_strength) {
    if (soft_prediction.channels() == 1) {
        return soft_prediction;
    }

    cv::Mat soft_prediction_blurred = soft_prediction.clone();

    bool applyBlurAndSoftThreshold = (blur_strength > -1 && soft_threshold < std::numeric_limits<float>::infinity());
    if (applyBlurAndSoftThreshold) {
        cv::blur(soft_prediction_blurred, soft_prediction_blurred, cv::Size{blur_strength, blur_strength});
    }

    cv::Mat hard_prediction{cv::Size{soft_prediction_blurred.cols, soft_prediction_blurred.rows}, CV_8UC1};
    for (int i = 0; i < soft_prediction_blurred.rows; ++i) {
        for (int j = 0; j < soft_prediction_blurred.cols; ++j) {
            float max_prob = -std::numeric_limits<float>::infinity();
            if (applyBlurAndSoftThreshold) {
                max_prob = soft_threshold;
            }

            uint8_t max_id = 0;
            for (int c = 0; c < soft_prediction_blurred.channels(); ++c) {
                float prob = ((float*)soft_prediction_blurred.ptr(i, j))[c];
                if (prob > max_prob) {
                    max_prob = prob;
                    max_id = c;
                }
            }
            hard_prediction.at<uint8_t>(i, j) = max_id;
        }
    }
    return hard_prediction;
}

std::string SegmentationModel::ModelType = "Segmentation";

void SegmentationModel::init_from_config(const ov::AnyMap& top_priority, const ov::AnyMap& mid_priority) {
    blur_strength = get_from_any_maps("blur_strength", top_priority, mid_priority, blur_strength);
    soft_threshold = get_from_any_maps("soft_threshold", top_priority, mid_priority, soft_threshold);
    return_soft_prediction =
        get_from_any_maps("return_soft_prediction", top_priority, mid_priority, return_soft_prediction);
}

SegmentationModel::SegmentationModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : ImageModel(model, configuration) {
    init_from_config(configuration,
                     model->has_rt_info("model_info") ? model->get_rt_info<ov::AnyMap>("model_info") : ov::AnyMap{});
}

SegmentationModel::SegmentationModel(std::shared_ptr<InferenceAdapter>& adapter, const ov::AnyMap& configuration)
    : ImageModel(adapter, configuration) {
    init_from_config(configuration, adapter->getModelConfig());
}

std::unique_ptr<SegmentationModel> SegmentationModel::create_model(const std::string& modelFile,
                                                                   const ov::AnyMap& configuration,
                                                                   bool preload,
                                                                   const std::string& device) {
    auto core = ov::Core();
    std::shared_ptr<ov::Model> model = core.read_model(modelFile);

    // Check model_type in the rt_info, ignore configuration
    std::string model_type = SegmentationModel::ModelType;
    try {
        if (model->has_rt_info("model_info", "model_type")) {
            model_type = model->get_rt_info<std::string>("model_info", "model_type");
        }
    } catch (const std::exception&) {
        slog::warn << "Model type is not specified in the rt_info, use default model type: " << model_type
                   << slog::endl;
    }

    if (model_type != SegmentationModel::ModelType) {
        throw std::runtime_error("Incorrect or unsupported model_type is provided in the model_info section: " +
                                 model_type);
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
    if (model->outputs().size() > 2) {
        throw std::logic_error("Segmentation model wrapper supports topologies with 1 or 2 outputs");
    }

    std::string out_name;
    for (ov::Output<ov::Node>& output : model->outputs()) {
        const std::unordered_set<std::string>& out_names = output.get_names();
        if (out_names.find(feature_vector_name) == out_names.end()) {
            if (out_name.empty()) {
                out_name = output.get_any_name();
            } else {
                throw std::runtime_error(std::string{"Only "} + feature_vector_name +
                                         " and 1 other output are allowed");
            }
        }
    }
    if (out_name.empty()) {
        throw std::runtime_error("No output containing segmentation masks found");
    }

    if (!embedded_processing) {
        model = ImageModel::embedProcessing(
            model,
            inputNames[0],
            inputLayout,
            resizeMode,
            interpolationMode,
            ov::Shape{inputShape[ov::layout::width_idx(inputLayout)], inputShape[ov::layout::height_idx(inputLayout)]},
            pad_value,
            reverse_input_channels,
            mean_values,
            scale_values);

        ov::preprocess::PrePostProcessor ppp = ov::preprocess::PrePostProcessor(model);
        ov::Layout out_layout = getLayoutFromShape(model->output(out_name).get_partial_shape());
        ppp.output(out_name).model().set_layout(out_layout);
        ppp.output(out_name).tensor().set_element_type(ov::element::f32);
        if (ov::layout::has_channels(out_layout)) {
            ppp.output(out_name).tensor().set_layout("NCHW");
        } else {
            // deeplabv3
            ppp.output(out_name).tensor().set_layout("NHW");
        }
        model = ppp.build();
        useAutoResize = true;  // temporal solution
        embedded_processing = true;
    }

    outputNames.push_back(out_name);
    for (ov::Output<ov::Node>& output : model->outputs()) {
        const std::unordered_set<std::string>& out_names = output.get_names();
        if (out_names.find(feature_vector_name) == out_names.end()) {
            outputNames.emplace_back(feature_vector_name);
            return;
        }
    }
}

std::unique_ptr<ResultBase> SegmentationModel::postprocess(InferenceResult& infResult) {
    const auto& inputImgSize = infResult.internalModelData->asRef<InternalImageModelData>();
    const auto& outputName = outputNames[0] == feature_vector_name ? outputNames[1] : outputNames[0];
    const auto& outTensor = infResult.outputsData[outputName];
    const ov::Shape& outputShape = outTensor.get_shape();
    const ov::Layout& outputLayout = getLayoutFromShape(outputShape);
    size_t outChannels =
        ov::layout::has_channels(outputLayout) ? outputShape[ov::layout::channels_idx(outputLayout)] : 1;
    int outHeight = static_cast<int>(outputShape[ov::layout::height_idx(outputLayout)]);
    int outWidth = static_cast<int>(outputShape[ov::layout::width_idx(outputLayout)]);
    cv::Mat soft_prediction;
    if (outChannels == 1 && outTensor.get_element_type() == ov::element::i32) {
        cv::Mat predictions(outHeight, outWidth, CV_32SC1, outTensor.data<int32_t>());
        predictions.convertTo(soft_prediction, CV_8UC1);
    } else if (outChannels == 1 && outTensor.get_element_type() == ov::element::i64) {
        cv::Mat predictions(outHeight, outWidth, CV_32SC1);
        const auto data = outTensor.data<int64_t>();
        for (size_t i = 0; i < predictions.total(); ++i) {
            reinterpret_cast<int32_t*>(predictions.data)[i] = int32_t(data[i]);
        }
        predictions.convertTo(soft_prediction, CV_8UC1);
    } else if (outTensor.get_element_type() == ov::element::f32) {
        float* data = outTensor.data<float>();
        std::vector<cv::Mat> channels;
        for (size_t c = 0; c < outTensor.get_shape()[1]; ++c) {
            channels.emplace_back(cv::Size{outWidth, outHeight}, CV_32FC1, data + c * outHeight * outWidth);
        }
        cv::merge(channels, soft_prediction);
    }

    cv::Mat hard_prediction =
        create_hard_prediction_from_soft_prediction(soft_prediction, soft_threshold, blur_strength);

    cv::resize(hard_prediction,
               hard_prediction,
               {inputImgSize.inputImgWidth, inputImgSize.inputImgHeight},
               0.0,
               0.0,
               cv::INTER_NEAREST);

    if (return_soft_prediction) {
        ImageResultWithSoftPrediction* result =
            new ImageResultWithSoftPrediction(infResult.frameId, infResult.metaData);
        result->resultImage = hard_prediction;
        cv::resize(soft_prediction,
                   soft_prediction,
                   {inputImgSize.inputImgWidth, inputImgSize.inputImgHeight},
                   0.0,
                   0.0,
                   cv::INTER_NEAREST);
        result->soft_prediction = soft_prediction;
        auto iter = infResult.outputsData.find(feature_vector_name);
        if (infResult.outputsData.end() != iter) {
            result->saliency_map = get_activation_map(soft_prediction);
            result->feature_vector = iter->second;
        }
        return std::unique_ptr<ResultBase>(result);
    }

    ImageResult* result = new ImageResult(infResult.frameId, infResult.metaData);
    result->resultImage = hard_prediction;
    return std::unique_ptr<ResultBase>(result);
}

std::vector<Contour> SegmentationModel::getContours(const ImageResultWithSoftPrediction& imageResult) {
    if (imageResult.soft_prediction.channels() == 1) {
        throw std::runtime_error{"Cannot get contours from soft prediction with 1 layer"};
    }

    std::vector<Contour> combined_contours = {};
    cv::Mat label_index_map;
    cv::Mat current_label_soft_prediction;
    for (int index = 1; index < imageResult.soft_prediction.channels(); index++) {
        cv::extractChannel(imageResult.soft_prediction, current_label_soft_prediction, index);
        cv::inRange(imageResult.resultImage,
                    cv::Scalar(index, index, index),
                    cv::Scalar(index, index, index),
                    label_index_map);
        std::vector<std::vector<cv::Point>> contours;
        cv::findContours(label_index_map, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE);

        std::string label = getLabelName(index - 1);

        for (unsigned int i = 0; i < contours.size(); i++) {
            cv::Mat mask = cv::Mat::zeros(imageResult.resultImage.rows,
                                          imageResult.resultImage.cols,
                                          imageResult.resultImage.type());
            cv::drawContours(mask, contours, i, 255, -1);
            float probability = (float)cv::mean(current_label_soft_prediction, mask)[0];
            combined_contours.push_back({label, probability, contours[i]});
        }
    }

    return combined_contours;
}

std::unique_ptr<ImageResult> SegmentationModel::infer(const ImageInputData& inputData) {
    auto result = ImageModel::inferImage(inputData);
    return std::unique_ptr<ImageResult>(static_cast<ImageResult*>(result.release()));
}

std::vector<std::unique_ptr<ImageResult>> SegmentationModel::inferBatch(const std::vector<ImageInputData>& inputImgs) {
    auto results = ImageModel::inferBatchImage(inputImgs);
    std::vector<std::unique_ptr<ImageResult>> segResults;
    segResults.reserve(results.size());
    for (auto& result : results) {
        segResults.emplace_back(static_cast<ImageResult*>(result.release()));
    }
    return segResults;
}
