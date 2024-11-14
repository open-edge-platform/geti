/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include <models/instance_segmentation.h>
#include <models/results.h>
#include <tilers/instance_segmentation.h>

#include <algorithm>
#include <functional>
#include <opencv2/core.hpp>
#include <utils/nms.hpp>
#include <vector>

#include "utils/common.hpp"

namespace {
class MaskRCNNModelParamsSetter {
public:
    std::shared_ptr<ModelBase> model;
    bool state;
    MaskRCNNModel* model_ptr;
    MaskRCNNModelParamsSetter(std::shared_ptr<ModelBase> model_) : model(model_) {
        model_ptr = static_cast<MaskRCNNModel*>(model.get());
        state = model_ptr->postprocess_semantic_masks;
        model_ptr->postprocess_semantic_masks = false;
    }
    ~MaskRCNNModelParamsSetter() {
        model_ptr->postprocess_semantic_masks = state;
    }
};
}  // namespace

InstanceSegmentationTiler::InstanceSegmentationTiler(std::shared_ptr<ImageModel> _model,
                                                     const ov::AnyMap& configuration,
                                                     ExecutionMode exec_mode)
    : TilerBase(_model, configuration, exec_mode) {
    ov::AnyMap extra_config;
    try {
        auto ov_model = model->getModel();
        extra_config = ov_model->get_rt_info<ov::AnyMap>("model_info");
    } catch (const std::runtime_error&) {
        extra_config = model->getInferenceAdapter()->getModelConfig();
    }

    postprocess_semantic_masks =
        get_from_any_maps("postprocess_semantic_masks", configuration, extra_config, postprocess_semantic_masks);
    max_pred_number = get_from_any_maps("max_pred_number", configuration, extra_config, max_pred_number);
}

std::unique_ptr<InstanceSegmentationResult> InstanceSegmentationTiler::run(const ImageInputData& inputData) {
    auto setter = MaskRCNNModelParamsSetter(model);
    auto result = this->run_impl(inputData);
    return std::unique_ptr<InstanceSegmentationResult>(static_cast<InstanceSegmentationResult*>(result.release()));
}

std::unique_ptr<ResultBase> InstanceSegmentationTiler::postprocess_tile(std::unique_ptr<ResultBase> tile_result,
                                                                        const cv::Rect& coord) {
    auto* iseg_res = static_cast<InstanceSegmentationResult*>(tile_result.get());
    for (auto& det : iseg_res->segmentedObjects) {
        det.x += coord.x;
        det.y += coord.y;
    }

    if (iseg_res->feature_vector) {
        auto tmp_feature_vector =
            ov::Tensor(iseg_res->feature_vector.get_element_type(), iseg_res->feature_vector.get_shape());
        iseg_res->feature_vector.copy_to(tmp_feature_vector);
        iseg_res->feature_vector = tmp_feature_vector;
    }

    return tile_result;
}

std::unique_ptr<ResultBase> InstanceSegmentationTiler::merge_results(
    const std::vector<std::unique_ptr<ResultBase>>& tiles_results,
    const cv::Size& image_size,
    const std::vector<cv::Rect>& tile_coords) {
    auto* result = new InstanceSegmentationResult();
    auto retVal = std::unique_ptr<ResultBase>(result);

    std::vector<AnchorLabeled> all_detections;
    std::vector<std::reference_wrapper<SegmentedObject>> all_detections_ptrs;
    std::vector<float> all_scores;

    for (const auto& result : tiles_results) {
        auto* iseg_res = static_cast<InstanceSegmentationResult*>(result.get());
        for (auto& det : iseg_res->segmentedObjects) {
            all_detections.emplace_back(det.x, det.y, det.x + det.width, det.y + det.height, det.labelID);
            all_scores.push_back(det.confidence);
            all_detections_ptrs.push_back(det);
        }
    }

    auto keep_idx = multiclass_nms(all_detections, all_scores, iou_threshold, false, max_pred_number);

    result->segmentedObjects.reserve(keep_idx.size());
    for (auto idx : keep_idx) {
        if (postprocess_semantic_masks) {
            all_detections_ptrs[idx].get().mask = segm_postprocess(all_detections_ptrs[idx],
                                                                   all_detections_ptrs[idx].get().mask,
                                                                   image_size.height,
                                                                   image_size.width);
        }
        result->segmentedObjects.push_back(all_detections_ptrs[idx]);
    }

    if (tiles_results.size()) {
        auto* iseg_res = static_cast<InstanceSegmentationResult*>(tiles_results.begin()->get());
        if (iseg_res->feature_vector) {
            result->feature_vector =
                ov::Tensor(iseg_res->feature_vector.get_element_type(), iseg_res->feature_vector.get_shape());
        }
    }

    if (result->feature_vector) {
        float* feature_ptr = result->feature_vector.data<float>();
        size_t feature_size = result->feature_vector.get_size();

        std::fill(feature_ptr, feature_ptr + feature_size, 0.f);

        for (const auto& result : tiles_results) {
            auto* iseg_res = static_cast<InstanceSegmentationResult*>(result.get());
            const float* current_feature_ptr = iseg_res->feature_vector.data<float>();

            for (size_t i = 0; i < feature_size; ++i) {
                feature_ptr[i] += current_feature_ptr[i];
            }
        }

        for (size_t i = 0; i < feature_size; ++i) {
            feature_ptr[i] /= tiles_results.size();
        }
    }

    result->saliency_map = merge_saliency_maps(tiles_results, image_size, tile_coords);

    return retVal;
}

std::vector<cv::Mat_<std::uint8_t>> InstanceSegmentationTiler::merge_saliency_maps(
    const std::vector<std::unique_ptr<ResultBase>>& tiles_results,
    const cv::Size& image_size,
    const std::vector<cv::Rect>& tile_coords) {
    std::vector<std::vector<cv::Mat_<std::uint8_t>>> all_saliecy_maps;
    all_saliecy_maps.reserve(tiles_results.size());
    for (const auto& result : tiles_results) {
        auto det_res = static_cast<InstanceSegmentationResult*>(result.get());
        all_saliecy_maps.push_back(det_res->saliency_map);
    }

    std::vector<cv::Mat_<std::uint8_t>> image_saliency_map;
    if (all_saliecy_maps.size()) {
        image_saliency_map = all_saliecy_maps[0];
    }

    if (image_saliency_map.empty()) {
        return image_saliency_map;
    }

    size_t num_classes = image_saliency_map.size();
    std::vector<cv::Mat_<std::uint8_t>> merged_map(num_classes);
    for (auto& map : merged_map) {
        map = cv::Mat_<std::uint8_t>(image_size, 0);
    }

    size_t start_idx = tile_with_full_img ? 1 : 0;
    for (size_t i = start_idx; i < all_saliecy_maps.size(); ++i) {
        for (size_t class_idx = 0; class_idx < num_classes; ++class_idx) {
            auto current_cls_map_mat = all_saliecy_maps[i][class_idx];
            if (current_cls_map_mat.empty()) {
                continue;
            }
            const auto& tile = tile_coords[i];
            cv::Mat tile_map;
            cv::resize(current_cls_map_mat, tile_map, tile.size());
            auto tile_map_merged = cv::Mat(merged_map[class_idx], tile);
            cv::Mat(cv::max(tile_map, tile_map_merged)).copyTo(tile_map_merged);
        }
    }

    for (size_t class_idx = 0; class_idx < num_classes; ++class_idx) {
        auto image_map_cls = tile_with_full_img ? image_saliency_map[class_idx] : cv::Mat_<std::uint8_t>();
        if (image_map_cls.empty()) {
            if (cv::sum(merged_map[class_idx]) == cv::Scalar(0.)) {
                merged_map[class_idx] = cv::Mat_<std::uint8_t>();
            }
        } else {
            cv::resize(image_map_cls, image_map_cls, image_size);
            cv::Mat(cv::max(merged_map[class_idx], image_map_cls)).copyTo(merged_map[class_idx]);
        }
    }

    return merged_map;
}
