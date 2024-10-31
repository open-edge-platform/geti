/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */
#include "models/detection_model_ext.h"

#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "models/image_model.h"
#include "models/input_data.h"
#include "models/results.h"

DetectionModelExt::DetectionModelExt(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : DetectionModel(model, configuration) {
    auto iou_threshold_iter = configuration.find("iou_threshold");
    if (iou_threshold_iter != configuration.end()) {
        iou_threshold = iou_threshold_iter->second.as<float>();
    } else {
        if (model->has_rt_info<std::string>("model_info", "iou_threshold")) {
            iou_threshold = model->get_rt_info<float>("model_info", "iou_threshold");
        }
    }
}

DetectionModelExt::DetectionModelExt(std::shared_ptr<InferenceAdapter>& adapter) : DetectionModel(adapter) {
    const ov::AnyMap& configuration = adapter->getModelConfig();
    auto iou_threshold_iter = configuration.find("iou_threshold");
    if (iou_threshold_iter != configuration.end()) {
        iou_threshold = iou_threshold_iter->second.as<float>();
    }
}

void DetectionModelExt::updateModelInfo() {
    DetectionModel::updateModelInfo();

    model->set_rt_info(iou_threshold, "model_info", "iou_threshold");
}
