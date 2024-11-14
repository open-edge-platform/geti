/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <tilers/tiler_base.h>

struct InstanceSegmentationResult;

class InstanceSegmentationTiler : public TilerBase {
    /*InstanceSegmentationTiler tiler works with MaskRCNNModel model only*/
public:
    InstanceSegmentationTiler(std::shared_ptr<ImageModel> model,
                              const ov::AnyMap& configuration,
                              ExecutionMode exec_mode = ExecutionMode::sync);
    virtual std::unique_ptr<InstanceSegmentationResult> run(const ImageInputData& inputData);
    virtual ~InstanceSegmentationTiler() = default;
    bool postprocess_semantic_masks = true;

protected:
    virtual std::unique_ptr<ResultBase> postprocess_tile(std::unique_ptr<ResultBase>, const cv::Rect&);
    virtual std::unique_ptr<ResultBase> merge_results(const std::vector<std::unique_ptr<ResultBase>>&,
                                                      const cv::Size&,
                                                      const std::vector<cv::Rect>&);

    std::vector<cv::Mat_<std::uint8_t>> merge_saliency_maps(const std::vector<std::unique_ptr<ResultBase>>&,
                                                            const cv::Size&,
                                                            const std::vector<cv::Rect>&);

    size_t max_pred_number = 200;
};
