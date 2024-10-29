/*
// Copyright (C) 2021-2024 Intel Corporation
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

#include <numeric>
#include <vector>

#include "opencv2/core.hpp"

struct Anchor {
    float left;
    float top;
    float right;
    float bottom;

    Anchor() = default;
    Anchor(float _left, float _top, float _right, float _bottom)
        : left(_left),
          top(_top),
          right(_right),
          bottom(_bottom) {}

    float getWidth() const {
        return (right - left) + 1.0f;
    }
    float getHeight() const {
        return (bottom - top) + 1.0f;
    }
    float getXCenter() const {
        return left + (getWidth() - 1.0f) / 2.0f;
    }
    float getYCenter() const {
        return top + (getHeight() - 1.0f) / 2.0f;
    }
};

struct AnchorLabeled : public Anchor {
    int labelID = -1;

    AnchorLabeled() = default;
    AnchorLabeled(float _left, float _top, float _right, float _bottom, int _labelID)
        : Anchor(_left, _top, _right, _bottom),
          labelID(_labelID) {}
};

template <typename Anchor>
std::vector<size_t> nms(const std::vector<Anchor>& boxes,
                        const std::vector<float>& scores,
                        const float thresh,
                        bool includeBoundaries = false,
                        size_t keep_top_k = 0) {
    if (keep_top_k == 0) {
        keep_top_k = boxes.size();
    }
    std::vector<float> areas(boxes.size());
    for (size_t i = 0; i < boxes.size(); ++i) {
        areas[i] =
            (boxes[i].right - boxes[i].left + includeBoundaries) * (boxes[i].bottom - boxes[i].top + includeBoundaries);
    }
    std::vector<int> order(scores.size());
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&scores](int o1, int o2) {
        return scores[o1] > scores[o2];
    });

    size_t ordersNum = 0;
    for (; ordersNum < order.size() && scores[order[ordersNum]] >= 0 && ordersNum < keep_top_k; ordersNum++)
        ;

    std::vector<size_t> keep;
    bool shouldContinue = true;
    for (size_t i = 0; shouldContinue && i < ordersNum; ++i) {
        int idx1 = order[i];
        if (idx1 >= 0) {
            keep.push_back(idx1);
            shouldContinue = false;
            for (size_t j = i + 1; j < ordersNum; ++j) {
                int idx2 = order[j];
                if (idx2 >= 0) {
                    shouldContinue = true;
                    float overlappingWidth = std::fminf(boxes[idx1].right, boxes[idx2].right) -
                                             std::fmaxf(boxes[idx1].left, boxes[idx2].left);
                    float overlappingHeight = std::fminf(boxes[idx1].bottom, boxes[idx2].bottom) -
                                              std::fmaxf(boxes[idx1].top, boxes[idx2].top);
                    float intersection =
                        overlappingWidth > 0 && overlappingHeight > 0 ? overlappingWidth * overlappingHeight : 0;
                    float union_area = areas[idx1] + areas[idx2] - intersection;
                    if (0.0f == union_area || intersection / union_area > thresh) {
                        order[j] = -1;
                    }
                }
            }
        }
    }
    return keep;
}

std::vector<size_t> multiclass_nms(const std::vector<AnchorLabeled>& boxes,
                                   const std::vector<float>& scores,
                                   const float iou_threshold = 0.45f,
                                   bool includeBoundaries = false,
                                   size_t maxNum = 200);
