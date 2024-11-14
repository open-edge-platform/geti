/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <tilers/tiler_base.h>

struct ImageResult;
struct ImageResultWithSoftPrediction;

class SemanticSegmentationTiler : public TilerBase {
public:
    SemanticSegmentationTiler(std::shared_ptr<ImageModel> model,
                              const ov::AnyMap& configuration,
                              ExecutionMode exec_mode = ExecutionMode::sync);
    virtual std::unique_ptr<ImageResultWithSoftPrediction> run(const ImageInputData& inputData);
    virtual ~SemanticSegmentationTiler() = default;

protected:
    virtual std::unique_ptr<ResultBase> postprocess_tile(std::unique_ptr<ResultBase>, const cv::Rect&);
    virtual std::unique_ptr<ResultBase> merge_results(const std::vector<std::unique_ptr<ResultBase>>&,
                                                      const cv::Size&,
                                                      const std::vector<cv::Rect>&);

    int blur_strength = -1;
    float soft_threshold = -std::numeric_limits<float>::infinity();
    bool return_soft_prediction = true;
};
