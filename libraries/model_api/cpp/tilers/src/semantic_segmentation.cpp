/*
// Copyright (C) 2024 Intel Corporation
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


#include <vector>
#include <opencv2/core.hpp>

#include <tilers/semantic_segmentation.h>
#include <models/segmentation_model.h>
#include <models/results.h>
#include "utils/common.hpp"

namespace {
void normalize_soft_prediction(cv::Mat& soft_prediction, const cv::Mat& normalize_factor) {
    float* data = soft_prediction.ptr<float>(0);
    const int num_classes = soft_prediction.channels();
    const size_t step_rows = soft_prediction.step[0] / sizeof(float);
    const size_t step_cols = soft_prediction.step[1] / sizeof(float);

    for (int y = 0; y < soft_prediction.rows; ++y) {
        for (int x = 0; x < soft_prediction.cols; ++x) {
            int weight = normalize_factor.at<int>(y, x);
            if (weight > 0) {
                for (int c = 0; c < num_classes; ++c) {
                    data[y * step_rows + x * step_cols + c] /= weight;
                }
            }
        }
    }
}
}

SemanticSegmentationTiler::SemanticSegmentationTiler(std::shared_ptr<ImageModel> _model, const ov::AnyMap& configuration) :
    TilerBase(_model, configuration) {
    ov::AnyMap extra_config;
    try {
        auto ov_model = model->getModel();
        extra_config = ov_model->get_rt_info<ov::AnyMap>("model_info");
    }
    catch (const std::runtime_error&) {
        extra_config = model->getInferenceAdapter()->getModelConfig();
    }

    blur_strength = get_from_any_maps("blur_strength", configuration, extra_config, blur_strength);
    soft_threshold = get_from_any_maps("soft_threshold", configuration, extra_config, soft_threshold);
    return_soft_prediction = get_from_any_maps("return_soft_prediction", configuration, extra_config, return_soft_prediction);
}

std::unique_ptr<ImageResultWithSoftPrediction> SemanticSegmentationTiler::run(const ImageInputData& inputData) {
    auto result = this->run_impl(inputData);
    return std::unique_ptr<ImageResultWithSoftPrediction>(static_cast<ImageResultWithSoftPrediction*>(result.release()));
}

std::unique_ptr<ResultBase> SemanticSegmentationTiler::postprocess_tile(std::unique_ptr<ResultBase> tile_result, const cv::Rect&) {
    ImageResultWithSoftPrediction* soft = dynamic_cast<ImageResultWithSoftPrediction*>(tile_result.get());
    if (!soft) {
        throw std::runtime_error("SemanticSegmentationTiler requires the underlying model to return ImageResultWithSoftPrediction");
    }
    return tile_result;
}

std::unique_ptr<ResultBase> SemanticSegmentationTiler::merge_results(const std::vector<std::unique_ptr<ResultBase>>& tiles_results,
                                                                     const cv::Size& image_size, const std::vector<cv::Rect>& tile_coords) {
    if (tiles_results.empty()) {
        return std::unique_ptr<ResultBase>(new ImageResultWithSoftPrediction());
    }

    cv::Mat voting_mask(cv::Size(image_size.width, image_size.height), CV_32SC1, cv::Scalar(0));
    auto* sseg_res = static_cast<ImageResultWithSoftPrediction*>(tiles_results[0].get());
    cv::Mat merged_soft_prediction(cv::Size(image_size.width, image_size.height), CV_32FC(sseg_res->soft_prediction.channels()), cv::Scalar(0));

    for (size_t i = 0; i < tiles_results.size(); ++i) {
        auto* sseg_res = static_cast<ImageResultWithSoftPrediction*>(tiles_results[i].get());
        voting_mask(tile_coords[i]) += 1;
        merged_soft_prediction(tile_coords[i]) += sseg_res->soft_prediction;
    }

    normalize_soft_prediction(merged_soft_prediction, voting_mask);

    cv::Mat hard_prediction = create_hard_prediction_from_soft_prediction(merged_soft_prediction, soft_threshold, blur_strength);

    std::unique_ptr<ResultBase> retVal;
    if (return_soft_prediction) {
        auto* result = new ImageResultWithSoftPrediction();
        retVal = std::unique_ptr<ResultBase>(result);
        result->soft_prediction = merged_soft_prediction;
        result->resultImage = hard_prediction;
    }
    else {
        auto* result = new ImageResult();
        retVal = std::unique_ptr<ResultBase>(result);
        result->resultImage = hard_prediction;
    }
    return retVal;
}
