/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#pragma once
#include <stddef.h>
#include <stdint.h>

#include <map>
#include <memory>
#include <openvino/op/region_yolo.hpp>
#include <openvino/openvino.hpp>
#include <string>
#include <vector>

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
    enum class YoloVersion : size_t { YOLO_V1V2 = 0, YOLO_V3, YOLO_V4, YOLO_V4_TINY, YOLOF };

    ModelYolo(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    ModelYolo(std::shared_ptr<InferenceAdapter>& adapter);

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
    float iou_threshold;
    bool useAdvancedPostprocessing = true;
    bool isObjConf = 1;
    YoloVersion yoloVersion = YoloVersion::YOLO_V3;
    std::vector<float> presetAnchors;
    std::vector<int64_t> presetMasks;
    ov::Layout yoloRegionLayout = "NCHW";
};

class YOLOv5 : public DetectionModelExt {
    // Reimplementation of ultralytics.YOLO
    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void updateModelInfo() override;
    void init_from_config(const ov::AnyMap& top_priority, const ov::AnyMap& mid_priority);
    bool agnostic_nms = false;

public:
    YOLOv5(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    YOLOv5(std::shared_ptr<InferenceAdapter>& adapter);
    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;
    static std::string ModelType;
};

class YOLOv8 : public YOLOv5 {
public:
    // YOLOv5 and YOLOv8 are identical in terms of inference
    YOLOv8(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration) : YOLOv5{model, configuration} {}
    YOLOv8(std::shared_ptr<InferenceAdapter>& adapter) : YOLOv5{adapter} {}
    static std::string ModelType;
};
