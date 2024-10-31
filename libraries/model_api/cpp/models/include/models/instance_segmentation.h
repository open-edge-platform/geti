/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <memory>
#include <string>
#include <vector>

#include "models/image_model.h"

namespace ov {
class Model;
}  // namespace ov
struct InferenceResult;
struct ResultBase;
struct InstanceSegmentationResult;
struct ImageInputData;
struct SegmentedObject;

class MaskRCNNModel : public ImageModel {
public:
    MaskRCNNModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    MaskRCNNModel(std::shared_ptr<InferenceAdapter>& adapter, const ov::AnyMap& configuration = {});

    static std::unique_ptr<MaskRCNNModel> create_model(const std::string& modelFile,
                                                       const ov::AnyMap& configuration = {},
                                                       bool preload = true,
                                                       const std::string& device = "AUTO");
    static std::unique_ptr<MaskRCNNModel> create_model(std::shared_ptr<InferenceAdapter>& adapter);

    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;

    virtual std::unique_ptr<InstanceSegmentationResult> infer(const ImageInputData& inputData);
    virtual std::vector<std::unique_ptr<InstanceSegmentationResult>> inferBatch(
        const std::vector<ImageInputData>& inputImgs);
    static std::string ModelType;
    bool postprocess_semantic_masks = true;

protected:
    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void updateModelInfo() override;
    void init_from_config(const ov::AnyMap& top_priority, const ov::AnyMap& mid_priority);
    std::string getLabelName(size_t labelID) {
        return labelID < labels.size() ? labels[labelID] : std::string("Label #") + std::to_string(labelID);
    }

    float confidence_threshold = 0.5f;
};

cv::Mat segm_postprocess(const SegmentedObject& box, const cv::Mat& unpadded, int im_h, int im_w);
