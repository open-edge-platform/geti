/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "utils/nms.hpp"

#include <vector>

std::vector<size_t> multiclass_nms(const std::vector<AnchorLabeled>& boxes,
                                   const std::vector<float>& scores,
                                   const float iou_threshold,
                                   bool includeBoundaries,
                                   size_t maxNum) {
    std::vector<Anchor> boxes_copy;
    boxes_copy.reserve(boxes.size());

    float max_coord = 0.f;
    for (const auto& box : boxes) {
        max_coord = std::max(max_coord, std::max(box.right, box.bottom));
    }
    for (auto& box : boxes) {
        float offset = box.labelID * max_coord;
        boxes_copy.emplace_back(box.left + offset, box.top + offset, box.right + offset, box.bottom + offset);
    }

    return nms<Anchor>(boxes_copy, scores, iou_threshold, includeBoundaries, maxNum);
}
