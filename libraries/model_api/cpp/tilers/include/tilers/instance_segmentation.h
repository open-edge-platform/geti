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

#pragma once
#include <tilers/detection.h>


class InstanceSegmentationTiler : public DetectionTiler {
    /*InstanceSegmentationTiler tiler works with MaskRCNNModel model only*/
public:
    InstanceSegmentationTiler(std::shared_ptr<ModelBase> model, const ov::AnyMap& configuration);
    virtual std::unique_ptr<ResultBase> run(const ImageInputData& inputData);
    virtual ~InstanceSegmentationTiler() = default;
    bool postprocess_semantic_masks = true;

protected:
    virtual std::unique_ptr<ResultBase> postprocess_tile(std::unique_ptr<ResultBase>, const cv::Rect&);
    virtual std::unique_ptr<ResultBase> merge_results(const std::vector<std::unique_ptr<ResultBase>>&, const cv::Size&, const std::vector<cv::Rect>&);

    std::vector<cv::Mat_<std::uint8_t>> merge_saliency_maps(const std::vector<std::unique_ptr<ResultBase>>&, const cv::Size&, const std::vector<cv::Rect>&);
};
