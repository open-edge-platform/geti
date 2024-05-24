/*
// Copyright (C) 2023-2024 Intel Corporation
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

#include <tilers/tiler_base.h>
#include <models/results.h>
#include <models/input_data.h>


TilerBase::TilerBase(const std::shared_ptr<ModelBase>& _model, const ov::AnyMap& configuration) :
    model(_model) {

    ov::AnyMap extra_config;
    try {
        auto ov_model = model->getModel();
        extra_config = ov_model->get_rt_info<ov::AnyMap>("model_info");
    }
    catch (const std::runtime_error&) {
        extra_config = model->getInferenceAdapter()->getModelConfig();
    }

    tile_size = get_from_any_maps("tile_size", configuration, extra_config, tile_size);
    tiles_overlap = get_from_any_maps("tiles_overlap", configuration, extra_config, tiles_overlap);
    iou_threshold = get_from_any_maps("iou_threshold", configuration, extra_config, iou_threshold);
    tile_with_full_img = get_from_any_maps("tile_with_full_img", configuration, extra_config, tile_with_full_img);
}

std::vector<cv::Rect> TilerBase::tile(const cv::Size& image_size) {
    std::vector<cv::Rect> coords;

    size_t tile_step = static_cast<size_t>(tile_size * (1.f - tiles_overlap));
    size_t num_h_tiles = image_size.height / tile_step;
    size_t num_w_tiles = image_size.width / tile_step;

    if (num_h_tiles * tile_step < static_cast<size_t>(image_size.height)) {
        num_h_tiles += 1;
    }

    if (num_w_tiles * tile_step < static_cast<size_t>(image_size.width)) {
        num_w_tiles += 1;
    }

    if (tile_with_full_img) {
        coords.reserve(num_h_tiles * num_w_tiles + 1);
        coords.push_back(cv::Rect(0, 0, image_size.width, image_size.height));
    }
    else {
        coords.reserve(num_h_tiles * num_w_tiles);
    }

    for (size_t i = 0; i < num_w_tiles; ++i) {
        for (size_t j = 0; j < num_h_tiles; ++j) {
            int loc_h = static_cast<int>(j * tile_step);
            int loc_w = static_cast<int>(i * tile_step);

            coords.push_back(cv::Rect(loc_w, loc_h,
                std::min(static_cast<int>(tile_size), image_size.width - loc_w),
                std::min(static_cast<int>(tile_size), image_size.height - loc_h)));
        }
    }
    return coords;
}

std::vector<cv::Rect> TilerBase::filter_tiles(const cv::Mat&, const std::vector<cv::Rect>& coords) {
    return coords;
}

std::unique_ptr<ResultBase> TilerBase::predict_sync(const cv::Mat& image, const std::vector<cv::Rect>& tile_coords) {
    std::vector<std::unique_ptr<ResultBase>> tile_results;

    for (const auto& coord : tile_coords) {
        auto tile_img = crop_tile(image, coord);
        auto tile_prediction = model->infer(ImageInputData(tile_img.clone()));
        auto tile_result = postprocess_tile(std::move(tile_prediction), coord);
        tile_results.push_back(std::move(tile_result));
    }

    return merge_results(tile_results, image.size(), tile_coords);
}

cv::Mat TilerBase::crop_tile(const cv::Mat& image, const cv::Rect& coord) {
    return cv::Mat(image, coord);
}

std::unique_ptr<ResultBase> TilerBase::run(const ImageInputData& inputData) {
    auto& image = inputData.inputImage;
    auto tile_coords = tile(image.size());
    tile_coords = filter_tiles(image, tile_coords);
    return predict_sync(image, tile_coords);
}
