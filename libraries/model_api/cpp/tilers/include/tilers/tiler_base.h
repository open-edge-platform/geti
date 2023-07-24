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

#pragma once
#include <map>
#include <memory>
#include <string>
#include <vector>

#include <openvino/openvino.hpp>

#include <utils/args_helper.hpp>
#include <utils/ocv_common.hpp>
#include <models/model_base.h>

struct ImageInputData;
struct ResultBase;


class TilerBase {
public:
    TilerBase(const std::shared_ptr<ModelBase>& model, const ov::AnyMap& configuration);

    virtual ~TilerBase() = default;

    virtual std::unique_ptr<ResultBase> run(const ImageInputData& inputData);

protected:

    std::vector<cv::Rect> tile(const cv::Size&);
    std::vector<cv::Rect> filter_tiles(const cv::Mat&, const std::vector<cv::Rect>&);
    std::unique_ptr<ResultBase> predict_sync(const cv::Mat&, const std::vector<cv::Rect>&);
    cv::Mat crop_tile(const cv::Mat&, const cv::Rect&);
    virtual std::unique_ptr<ResultBase> postprocess_tile(std::unique_ptr<ResultBase>, const cv::Rect&) = 0;
    virtual std::unique_ptr<ResultBase> merge_results(const std::vector<std::unique_ptr<ResultBase>>&, const cv::Size&, const std::vector<cv::Rect>&) = 0;

    std::shared_ptr<ModelBase> model;
    size_t tile_size = 400;
    float tiles_overlap = 0.5f;
};
