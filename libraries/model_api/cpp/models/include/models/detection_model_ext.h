/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <stddef.h>

#include <string>
#include <vector>

#include "models/detection_model.h"

struct DetectionResult;
struct ImageInputData;
struct InferenceAdatper;

class DetectionModelExt : public DetectionModel {
public:
    DetectionModelExt(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    DetectionModelExt(std::shared_ptr<InferenceAdapter>& adapter);

protected:
    void updateModelInfo() override;
    float iou_threshold = 0.5f;
};
