/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "models/keypoint_detection.h"

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <openvino/openvino.hpp>
#include <string>
#include <vector>

#include "models/input_data.h"
#include "models/internal_model_data.h"
#include "models/results.h"
#include "utils/slog.hpp"

namespace {

void colArgMax(const cv::Mat& src, cv::Mat& dst_locs, cv::Mat& dst_values) {
    dst_locs = cv::Mat::zeros(src.rows, 1, CV_32S);
    dst_values = cv::Mat::zeros(src.rows, 1, CV_32F);

    for (int row = 0; row < src.rows; row++) {
        const float* ptr_row = src.ptr<float>(row);
        int max_val_idx = 0;
        dst_values.at<float>(row) = ptr_row[max_val_idx];
        for (int col = 1; col < src.cols; ++col) {
            if (ptr_row[col] > ptr_row[max_val_idx]) {
                max_val_idx = col;
                dst_locs.at<int>(row) = max_val_idx;
                dst_values.at<float>(row) = ptr_row[col];
            }
        }
    }
}

DetectedKeypoints decode_simcc(const cv::Mat& simcc_x,
                               const cv::Mat& simcc_y,
                               const cv::Point2f& extra_scale = cv::Point2f(1.f, 1.f),
                               float simcc_split_ratio = 2.0f) {
    cv::Mat x_locs, max_val_x;
    colArgMax(simcc_x, x_locs, max_val_x);

    cv::Mat y_locs, max_val_y;
    colArgMax(simcc_y, y_locs, max_val_y);

    std::vector<cv::Point2f> keypoints(x_locs.rows);
    cv::Mat scores = cv::Mat::zeros(x_locs.rows, 1, CV_32F);
    for (int i = 0; i < x_locs.rows; i++) {
        keypoints[i] =
            cv::Point2f(x_locs.at<int>(i) * extra_scale.x, y_locs.at<int>(i) * extra_scale.y) / simcc_split_ratio;
        scores.at<float>(i) = std::min(max_val_x.at<float>(i), max_val_y.at<float>(i));

        if (scores.at<float>(i) <= 0.f) {
            keypoints[i] = cv::Point2f(-1.f, -1.f);
        }
    }

    return {std::move(keypoints), scores};
}

}  // namespace

std::string KeypointDetectionModel::ModelType = "keypoint_detection";

void KeypointDetectionModel::init_from_config(const ov::AnyMap& top_priority, const ov::AnyMap& mid_priority) {
    labels = get_from_any_maps("labels", top_priority, mid_priority, labels);
}

KeypointDetectionModel::KeypointDetectionModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : ImageModel(model, configuration) {
    init_from_config(configuration,
                     model->has_rt_info("model_info") ? model->get_rt_info<ov::AnyMap>("model_info") : ov::AnyMap{});
}

KeypointDetectionModel::KeypointDetectionModel(std::shared_ptr<InferenceAdapter>& adapter,
                                               const ov::AnyMap& configuration)
    : ImageModel(adapter, configuration) {
    init_from_config(configuration, adapter->getModelConfig());
}

std::unique_ptr<KeypointDetectionModel> KeypointDetectionModel::create_model(const std::string& modelFile,
                                                                             const ov::AnyMap& configuration,
                                                                             bool preload,
                                                                             const std::string& device) {
    auto core = ov::Core();
    std::shared_ptr<ov::Model> model = core.read_model(modelFile);

    // Check model_type in the rt_info, ignore configuration
    std::string model_type = KeypointDetectionModel::ModelType;
    try {
        if (model->has_rt_info("model_info", "model_type")) {
            model_type = model->get_rt_info<std::string>("model_info", "model_type");
        }
    } catch (const std::exception&) {
        slog::warn << "Model type is not specified in the rt_info, use default model type: " << model_type
                   << slog::endl;
    }

    if (model_type != KeypointDetectionModel::ModelType) {
        throw std::runtime_error("Incorrect or unsupported model_type is provided in the model_info section: " +
                                 model_type);
    }

    std::unique_ptr<KeypointDetectionModel> kp_detector{new KeypointDetectionModel(model, configuration)};
    kp_detector->prepare();
    if (preload) {
        kp_detector->load(core, device);
    }
    return kp_detector;
}

std::unique_ptr<KeypointDetectionModel> KeypointDetectionModel::create_model(
    std::shared_ptr<InferenceAdapter>& adapter) {
    const ov::AnyMap& configuration = adapter->getModelConfig();
    auto model_type_iter = configuration.find("model_type");
    std::string model_type = KeypointDetectionModel::ModelType;
    if (model_type_iter != configuration.end()) {
        model_type = model_type_iter->second.as<std::string>();
    }

    if (model_type != KeypointDetectionModel::ModelType) {
        throw std::runtime_error("Incorrect or unsupported model_type is provided: " + model_type);
    }

    std::unique_ptr<KeypointDetectionModel> kp_detector{new KeypointDetectionModel(adapter)};
    return kp_detector;
}

void KeypointDetectionModel::updateModelInfo() {
    ImageModel::updateModelInfo();

    model->set_rt_info(KeypointDetectionModel::ModelType, "model_info", "model_type");
    model->set_rt_info(labels, "model_info", "labels");
}

void KeypointDetectionModel::prepareInputsOutputs(std::shared_ptr<ov::Model>& model) {
    // --------------------------- Configure input & output ---------------------------------------------
    // --------------------------- Prepare input  -----------------------------------------------------
    if (model->inputs().size() != 1) {
        throw std::logic_error(KeypointDetectionModel::ModelType +
                               " model wrapper supports topologies with only 1 input");
    }
    const auto& input = model->input();
    inputNames.push_back(input.get_any_name());
    const ov::Layout& inputLayout = getInputLayout(input);
    const ov::Shape& inputShape = input.get_partial_shape().get_max_shape();
    if (inputShape.size() != 4 || inputShape[ov::layout::channels_idx(inputLayout)] != 3) {
        throw std::logic_error("3-channel 4-dimensional model's input is expected");
    }

    if (model->outputs().size() != 2) {
        throw std::logic_error(KeypointDetectionModel::ModelType + " model wrapper supports topologies with 2 outputs");
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
        model = ppp.build();
        embedded_processing = true;
        useAutoResize = true;
        netInputWidth = inputShape[ov::layout::width_idx(inputLayout)];
        netInputHeight = inputShape[ov::layout::height_idx(inputLayout)];
    }

    for (ov::Output<ov::Node>& output : model->outputs()) {
        outputNames.push_back(output.get_any_name());
    }
}

std::unique_ptr<ResultBase> KeypointDetectionModel::postprocess(InferenceResult& infResult) {
    KeypointDetectionResult* result = new KeypointDetectionResult(infResult.frameId, infResult.metaData);

    const ov::Tensor& pred_x_tensor = infResult.outputsData.find(outputNames[0])->second;
    size_t shape_offset = pred_x_tensor.get_shape().size() == 3 ? 1 : 0;
    auto pred_x_mat = cv::Mat(cv::Size(static_cast<int>(pred_x_tensor.get_shape()[shape_offset + 1]),
                                       static_cast<int>(pred_x_tensor.get_shape()[shape_offset])),
                              CV_32F,
                              pred_x_tensor.data(),
                              pred_x_tensor.get_strides()[shape_offset]);

    const ov::Tensor& pred_y_tensor = infResult.outputsData.find(outputNames[1])->second;
    shape_offset = pred_y_tensor.get_shape().size() == 3 ? 1 : 0;
    auto pred_y_mat = cv::Mat(cv::Size(static_cast<int>(pred_y_tensor.get_shape()[shape_offset + 1]),
                                       static_cast<int>(pred_y_tensor.get_shape()[shape_offset])),
                              CV_32F,
                              pred_y_tensor.data(),
                              pred_y_tensor.get_strides()[shape_offset]);

    const auto& image_data = infResult.internalModelData->asRef<InternalImageModelData>();
    float inverted_scale_x = static_cast<float>(image_data.inputImgWidth) / netInputWidth,
          inverted_scale_y = static_cast<float>(image_data.inputImgHeight) / netInputHeight;

    result->poses.emplace_back(decode_simcc(pred_x_mat, pred_y_mat, {inverted_scale_x, inverted_scale_y}));
    return std::unique_ptr<ResultBase>(result);
}

std::unique_ptr<KeypointDetectionResult> KeypointDetectionModel::infer(const ImageInputData& inputData) {
    auto result = ImageModel::inferImage(inputData);
    return std::unique_ptr<KeypointDetectionResult>(static_cast<KeypointDetectionResult*>(result.release()));
}

std::vector<std::unique_ptr<KeypointDetectionResult>> KeypointDetectionModel::inferBatch(
    const std::vector<ImageInputData>& inputImgs) {
    auto results = ImageModel::inferBatchImage(inputImgs);
    std::vector<std::unique_ptr<KeypointDetectionResult>> kpDetResults;
    kpDetResults.reserve(results.size());
    for (auto& result : results) {
        kpDetResults.emplace_back(static_cast<KeypointDetectionResult*>(result.release()));
    }
    return kpDetResults;
}
