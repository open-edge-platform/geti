/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <tilers/tiler_base.h>

struct DetectionResult;

class DetectionTiler : public TilerBase {
public:
    DetectionTiler(const std::shared_ptr<ImageModel>& model,
                   const ov::AnyMap& configuration,
                   ExecutionMode exec_mode = ExecutionMode::sync);
    virtual ~DetectionTiler() = default;

    virtual std::unique_ptr<DetectionResult> run(const ImageInputData& inputData);

protected:
    virtual std::unique_ptr<ResultBase> postprocess_tile(std::unique_ptr<ResultBase>, const cv::Rect&);
    virtual std::unique_ptr<ResultBase> merge_results(const std::vector<std::unique_ptr<ResultBase>>&,
                                                      const cv::Size&,
                                                      const std::vector<cv::Rect>&);
    ov::Tensor merge_saliency_maps(const std::vector<std::unique_ptr<ResultBase>>&,
                                   const cv::Size&,
                                   const std::vector<cv::Rect>&);

    size_t max_pred_number = 200;
};
