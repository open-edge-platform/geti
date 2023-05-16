/*
// Copyright (C) 2020-2023 Intel Corporation
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
#include <stddef.h>
#include <stdint.h>

#include <map>
#include <memory>
#include <string>
#include <vector>

#include <openvino/op/region_yolo.hpp>
#include <openvino/openvino.hpp>

#include "models/detection_model_ext.h"

struct DetectedObject;
struct InferenceResult;
struct ResultBase;

class ModelYolo : public DetectionModelExt {
protected:
    class Region {
    public:
        int num = 0;
        size_t classes = 0;
        int coords = 0;
        std::vector<float> anchors;
        size_t outputWidth = 0;
        size_t outputHeight = 0;

        Region(const std::shared_ptr<ov::op::v0::RegionYolo>& regionYolo);
        Region(size_t classes,
               int coords,
               const std::vector<float>& anchors,
               const std::vector<int64_t>& masks,
               size_t outputWidth,
               size_t outputHeight);
    };

public:
    enum class YoloVersion : size_t { YOLO_V1V2=0, YOLO_V3, YOLO_V4, YOLO_V4_TINY, YOLOF };

    ModelYolo(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    ModelYolo(std::shared_ptr<InferenceAdapter>& adapter);
    using DetectionModelExt::DetectionModelExt;

    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;

protected:
    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;

    void parseYOLOOutput(const std::string& output_name,
                         const ov::Tensor& tensor,
                         const unsigned long resized_im_h,
                         const unsigned long resized_im_w,
                         const unsigned long original_im_h,
                         const unsigned long original_im_w,
                         std::vector<DetectedObject>& objects);

    static int calculateEntryIndex(int entriesNum, int lcoords, size_t lclasses, int location, int entry);
    static double intersectionOverUnion(const DetectedObject& o1, const DetectedObject& o2);

    std::map<std::string, Region> regions;
    float boxIOUThreshold;
    bool useAdvancedPostprocessing = true;
    bool isObjConf = 1;
    YoloVersion yoloVersion = YoloVersion::YOLO_V3;
    std::vector<float> presetAnchors;
    std::vector<int64_t> presetMasks;
    ov::Layout yoloRegionLayout = "NCHW";
};
