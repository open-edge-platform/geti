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

#include <vector>

#include "utils/nms.hpp"


std::vector<size_t> multiclass_nms(const std::vector<AnchorLabeled>& boxes, const std::vector<float>& scores,
                     const float iou_threshold, bool includeBoundaries, size_t maxNum) {
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
