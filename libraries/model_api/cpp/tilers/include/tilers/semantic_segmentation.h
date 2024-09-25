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

#pragma once
#include <tilers/tiler_base.h>

struct ImageResult;
struct ImageResultWithSoftPrediction;

class SemanticSegmentationTiler : public TilerBase {
public:
    SemanticSegmentationTiler(std::shared_ptr<ImageModel> model, const ov::AnyMap& configuration);
    virtual std::unique_ptr<ImageResultWithSoftPrediction> run(const ImageInputData& inputData);
    virtual ~SemanticSegmentationTiler() = default;

protected:
    virtual std::unique_ptr<ResultBase> postprocess_tile(std::unique_ptr<ResultBase>, const cv::Rect&);
    virtual std::unique_ptr<ResultBase> merge_results(const std::vector<std::unique_ptr<ResultBase>>&, const cv::Size&, const std::vector<cv::Rect>&);

    int blur_strength = -1;
    float soft_threshold = -std::numeric_limits<float>::infinity();
    bool return_soft_prediction = true;
};
