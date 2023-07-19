/*
// Copyright (C) 2023 Intel Corporation
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

#include <algorithm>
#include <functional>
#include <vector>
#include <opencv2/core.hpp>

#include <tilers/detection.h>
#include <models/results.h>
#include <utils/nms.hpp>


namespace {

cv::Mat non_linear_normalization(cv::Mat& class_map) {
    double min_soft_score, max_soft_score;
    cv::minMaxLoc(class_map, &min_soft_score);
    cv::pow(class_map - min_soft_score, 1.5, class_map);

    cv::minMaxLoc(class_map, &min_soft_score, &max_soft_score);
    class_map = 255.0 / (max_soft_score + 1e-12) * class_map;

    return class_map;
}

}

DetectionTiler::DetectionTiler(std::shared_ptr<ModelBase> _model, const ov::AnyMap& configuration) :
    TilerBase(_model, configuration) {

    ov::AnyMap extra_config;
    try {
        auto ov_model = model->getModel();
        extra_config = ov_model->get_rt_info<ov::AnyMap>("model_info");
    }
    catch (const std::runtime_error&) {
        extra_config = model->getInferenceAdapter()->getModelConfig();
    }

    ov::AnyMap merged_config(configuration);
    merged_config.merge(extra_config);

    auto max_pred_iter = merged_config.find("max_pred_number");
    if (max_pred_iter != merged_config.end()) {
        max_pred_number = max_pred_iter->second.as<size_t>();
    }
}

std::unique_ptr<ResultBase> DetectionTiler::postprocess_tile(std::unique_ptr<ResultBase> tile_result, const cv::Rect& coord) {
    DetectionResult* det_res = static_cast<DetectionResult*>(tile_result.get());
    for (auto& det : det_res->objects) {
        det.x += coord.x;
        det.y += coord.y;
    }

    auto tmp_feature_vector = ov::Tensor(det_res->feature_vector.get_element_type(), det_res->feature_vector.get_shape());
    auto tmp_saliency_map = ov::Tensor(det_res->saliency_map.get_element_type(), det_res->saliency_map.get_shape());

    det_res->feature_vector.copy_to(tmp_feature_vector);
    det_res->feature_vector = tmp_feature_vector;

    det_res->saliency_map.copy_to(tmp_saliency_map);
    det_res->saliency_map = tmp_saliency_map;

    return tile_result;
}

std::unique_ptr<ResultBase> DetectionTiler::merge_results(const std::vector<std::unique_ptr<ResultBase>>& tiles_results, const cv::Size& image_size, const std::vector<cv::Rect>& tile_coords) {
    DetectionResult* result = new DetectionResult();
    auto retVal = std::unique_ptr<ResultBase>(result);

    std::vector<AnchorLabeled> all_detections;
    std::vector<std::reference_wrapper<DetectedObject>> all_detections_refs;
    std::vector<float> all_scores;

    for (const auto& result : tiles_results) {
        DetectionResult* det_res = static_cast<DetectionResult*>(result.get());
        for (auto& det : det_res->objects) {
            all_detections.emplace_back(det.x, det.y, det.x + det.width, det.y + det.height, det.labelID);
            all_scores.push_back(det.confidence);
            all_detections_refs.push_back(det);
        }
    }

    auto keep_idx = multiclass_nms(all_detections, all_scores, 0.45f, false, 200);

    result->objects.reserve(keep_idx.size());
    for (auto idx : keep_idx) {
        result->objects.push_back(all_detections_refs[idx]);
    }

    if (tiles_results.size()) {
        DetectionResult* det_res = static_cast<DetectionResult*>(tiles_results.begin()->get());
        result->feature_vector = ov::Tensor(det_res->feature_vector.get_element_type(), det_res->feature_vector.get_shape());
    }

    float* feature_ptr = result->feature_vector.data<float>();
    size_t feature_size = result->feature_vector.get_size();

    std::fill(feature_ptr, feature_ptr + feature_size, 0.f);

    for (const auto& result : tiles_results) {
        DetectionResult* det_res = static_cast<DetectionResult*>(result.get());
        const float* current_feature_ptr = det_res->feature_vector.data<float>();

        for (size_t i = 0; i < feature_size; ++i) {
            feature_ptr[i] += current_feature_ptr[i];
        }
    }

    for (size_t i = 0; i < feature_size; ++i) {
        feature_ptr[i] /= tiles_results.size();
    }

    result->saliency_map = merge_saliency_maps(tiles_results, image_size, tile_coords);

    return retVal;
}

ov::Tensor DetectionTiler::merge_saliency_maps(const std::vector<std::unique_ptr<ResultBase>>& tiles_results, const cv::Size& image_size, const std::vector<cv::Rect>& tile_coords) {
    std::vector<ov::Tensor> all_saliency_maps;
    all_saliency_maps.reserve(tiles_results.size());
    for (const auto& result : tiles_results) {
        auto det_res = static_cast<DetectionResult*>(result.get());
        all_saliency_maps.push_back(det_res->saliency_map);
    }

    ov::Tensor image_saliency_map;
    if (all_saliency_maps.size()) {
        image_saliency_map = all_saliency_maps[0];
    }

    if (image_saliency_map.get_size() == 1) {
        return image_saliency_map;
    }

    size_t shape_shift = (image_saliency_map.get_shape().size() > 3) ? 1 : 0;
    size_t num_classes = image_saliency_map.get_shape()[shape_shift];
    size_t map_h = image_saliency_map.get_shape()[shape_shift + 1];
    size_t map_w = image_saliency_map.get_shape()[shape_shift + 2];

    float ratio_h = static_cast<float>(map_h) / tile_size;
    float ratio_w = static_cast<float>(map_w) / tile_size;

    size_t image_map_h = static_cast<size_t>(image_size.height * ratio_h);
    size_t image_map_w = static_cast<size_t>(image_size.width * ratio_w);

    std::vector<cv::Mat_<float>> merged_map_mat(num_classes);
    for (auto& class_map : merged_map_mat)  {
        class_map = cv::Mat_<float>(cv::Size(image_map_w, image_map_h));
        class_map = 0.f;
    }
    for (size_t i = 1; i < all_saliency_maps.size(); ++i) {
        for (size_t class_idx = 0; class_idx < num_classes; ++class_idx) {
            auto current_cls_map_mat = wrap_saliency_map_tensor_to_mat(all_saliency_maps[i], shape_shift, class_idx);
            cv::Mat current_cls_map_mat_float;
            current_cls_map_mat.convertTo(current_cls_map_mat_float, CV_32F);

            cv::Rect map_location(static_cast<int>(tile_coords[i].x * ratio_w),
                                  static_cast<int>(tile_coords[i].y * ratio_h),
                                  static_cast<int>(static_cast<int>(tile_coords[i].width + tile_coords[i].x) * ratio_w - static_cast<int>(tile_coords[i].x * ratio_w)),
                                  static_cast<int>(static_cast<int>(tile_coords[i].height + tile_coords[i].y) * ratio_h - static_cast<int>(tile_coords[i].y * ratio_h)));

            if (current_cls_map_mat.rows > map_location.height && map_location.height > 0 && current_cls_map_mat.cols > map_location.width && map_location.width > 0) {
                cv::resize(current_cls_map_mat_float, current_cls_map_mat_float, cv::Size(map_location.width, map_location.height));
            }

            auto class_map_roi = cv::Mat(merged_map_mat[class_idx], map_location);
            for (int row_i = 0; row_i < map_location.height; ++row_i) {
                for (int col_i = 0; col_i < map_location.width; ++col_i) {
                    float merged_mixel = class_map_roi.at<float>(row_i, col_i);
                    if (merged_mixel > 0) {
                        class_map_roi.at<float>(row_i, col_i) = 0.5f * (merged_mixel + current_cls_map_mat_float.at<float>(row_i, col_i));
                    }
                    else {
                        class_map_roi.at<float>(row_i, col_i) = current_cls_map_mat_float.at<float>(row_i, col_i);
                    }
                }
            }
        }
    }

    ov::Tensor merged_map;
    if (shape_shift) {
        merged_map = ov::Tensor(ov::element::Type("u8"), {1, num_classes, image_map_h, image_map_w});
    }
    else {
        merged_map = ov::Tensor(ov::element::Type("u8"), {num_classes, image_map_h, image_map_w});
    }

    for (size_t class_idx = 0; class_idx < num_classes; ++class_idx) {
        auto image_map_cls = wrap_saliency_map_tensor_to_mat(image_saliency_map, shape_shift, class_idx);
        cv::resize(image_map_cls, image_map_cls, cv::Size(image_map_w, image_map_h));
        cv::addWeighted(merged_map_mat[class_idx], 1.0, image_map_cls, 0.5, 0., merged_map_mat[class_idx]);
        merged_map_mat[class_idx] = non_linear_normalization(merged_map_mat[class_idx]);
        auto merged_cls_map_mat = wrap_saliency_map_tensor_to_mat(merged_map, shape_shift, class_idx);
        merged_map_mat[class_idx].convertTo(merged_cls_map_mat, merged_cls_map_mat.type());
    }

    return merged_map;
}
