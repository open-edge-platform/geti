/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "models/detection_model_yolo.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <openvino/openvino.hpp>
#include <stdexcept>
#include <string>
#include <utility>
#include <utils/common.hpp>
#include <utils/nms.hpp>
#include <utils/slog.hpp>
#include <vector>

#include "models/internal_model_data.h"
#include "models/results.h"

namespace {
const std::vector<float> defaultAnchors[]{
    // YOLOv1v2
    {0.57273f, 0.677385f, 1.87446f, 2.06253f, 3.33843f, 5.47434f, 7.88282f, 3.52778f, 9.77052f, 9.16828f},
    // YOLOv3
    {10.0f,
     13.0f,
     16.0f,
     30.0f,
     33.0f,
     23.0f,
     30.0f,
     61.0f,
     62.0f,
     45.0f,
     59.0f,
     119.0f,
     116.0f,
     90.0f,
     156.0f,
     198.0f,
     373.0f,
     326.0f},
    // YOLOv4
    {12.0f,
     16.0f,
     19.0f,
     36.0f,
     40.0f,
     28.0f,
     36.0f,
     75.0f,
     76.0f,
     55.0f,
     72.0f,
     146.0f,
     142.0f,
     110.0f,
     192.0f,
     243.0f,
     459.0f,
     401.0f},
    // YOLOv4_Tiny
    {10.0f, 14.0f, 23.0f, 27.0f, 37.0f, 58.0f, 81.0f, 82.0f, 135.0f, 169.0f, 344.0f, 319.0f},
    // YOLOF
    {16.0f, 16.0f, 32.0f, 32.0f, 64.0f, 64.0f, 128.0f, 128.0f, 256.0f, 256.0f, 512.0f, 512.0f}};

float sigmoid(float x) noexcept {
    return 1.0f / (1.0f + std::exp(-x));
}

constexpr float identity(float x) noexcept {
    return x;
}
}  // namespace

ModelYolo::ModelYolo(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : DetectionModelExt(model, configuration) {
    auto anchors_iter = configuration.find("anchors");
    if (anchors_iter == configuration.end()) {
        if (model->has_rt_info("model_info", "anchors")) {
            // presetAnchors =
            // model->get_rt_info().at("model_info").as<ov::VariantWrapper<ov::AnyMap>>().get().at("anchors").as<std::vector<float>>();
            presetAnchors = model->get_rt_info<std::vector<float>>("model_info", "anchors");
        }
    } else {
        presetAnchors = anchors_iter->second.as<std::vector<float>>();
    }
    auto masks_iter = configuration.find("masks");
    if (masks_iter == configuration.end()) {
        if (model->has_rt_info("model_info", "masks")) {
            presetMasks = model->get_rt_info<std::vector<int64_t>>("model_info", "masks");
        }
    } else {
        presetMasks = masks_iter->second.as<std::vector<int64_t>>();
    }

    resizeMode = RESIZE_FILL;  // Ignore resize_type for now
}

ModelYolo::ModelYolo(std::shared_ptr<InferenceAdapter>& adapter) : DetectionModelExt(adapter) {
    const ov::AnyMap& configuration = adapter->getModelConfig();
    auto anchors_iter = configuration.find("anchors");
    if (anchors_iter != configuration.end()) {
        presetAnchors = anchors_iter->second.as<std::vector<float>>();
    }
    auto masks_iter = configuration.find("masks");
    if (masks_iter != configuration.end()) {
        presetMasks = masks_iter->second.as<std::vector<int64_t>>();
    }

    resizeMode = RESIZE_FILL;  // Ignore resize_type for now
}

void ModelYolo::prepareInputsOutputs(std::shared_ptr<ov::Model>& model) {
    // --------------------------- Configure input & output -------------------------------------------------
    // --------------------------- Prepare input  ------------------------------------------------------
    if (model->inputs().size() != 1) {
        throw std::logic_error("YOLO model wrapper accepts models that have only 1 input");
    }

    const auto& input = model->input();
    const ov::Shape& inputShape = model->input().get_shape();
    ov::Layout inputLayout = getInputLayout(input);

    if (inputShape[ov::layout::channels_idx(inputLayout)] != 3) {
        throw std::logic_error("Expected 3-channel input");
    }

    ov::preprocess::PrePostProcessor ppp(model);
    inputTransform.setPrecision(ppp, input.get_any_name());
    ppp.input().tensor().set_layout({"NHWC"});

    if (useAutoResize) {
        ppp.input().tensor().set_spatial_dynamic_shape();

        ppp.input()
            .preprocess()
            .convert_element_type(ov::element::f32)
            .resize(ov::preprocess::ResizeAlgorithm::RESIZE_LINEAR);
    }

    ppp.input().model().set_layout(inputLayout);

    //--- Reading image input parameters
    inputNames.push_back(model->input().get_any_name());
    netInputWidth = inputShape[ov::layout::width_idx(inputLayout)];
    netInputHeight = inputShape[ov::layout::height_idx(inputLayout)];

    // --------------------------- Prepare output  -----------------------------------------------------
    const ov::OutputVector& outputs = model->outputs();
    std::map<std::string, ov::Shape> outShapes;
    for (auto& out : outputs) {
        ppp.output(out.get_any_name()).tensor().set_element_type(ov::element::f32);
        if (out.get_shape().size() == 4) {
            if (out.get_shape()[ov::layout::height_idx("NCHW")] != out.get_shape()[ov::layout::width_idx("NCHW")] &&
                out.get_shape()[ov::layout::height_idx("NHWC")] == out.get_shape()[ov::layout::width_idx("NHWC")]) {
                ppp.output(out.get_any_name()).model().set_layout("NHWC");
                // outShapes are saved before ppp.build() thus set yoloRegionLayout as it is in model before ppp.build()
                yoloRegionLayout = "NHWC";
            }
            // yolo-v1-tiny-tf out shape is [1, 21125] thus set layout only for 4 dim tensors
            ppp.output(out.get_any_name()).tensor().set_layout("NCHW");
        }
        outputNames.push_back(out.get_any_name());
        outShapes[out.get_any_name()] = out.get_shape();
    }
    model = ppp.build();

    yoloVersion = YoloVersion::YOLO_V3;
    bool isRegionFound = false;
    for (const auto& op : model->get_ordered_ops()) {
        if (std::string("RegionYolo") == op->get_type_name()) {
            auto regionYolo = std::dynamic_pointer_cast<ov::op::v0::RegionYolo>(op);

            if (regionYolo) {
                if (!regionYolo->get_mask().size()) {
                    yoloVersion = YoloVersion::YOLO_V1V2;
                }

                const auto& opName = op->get_friendly_name();
                for (const auto& out : outputs) {
                    if (out.get_node()->get_friendly_name() == opName ||
                        out.get_node()->get_input_node_ptr(0)->get_friendly_name() == opName) {
                        isRegionFound = true;
                        regions.emplace(out.get_any_name(), Region(regionYolo));
                    }
                }
            }
        }
    }

    if (!isRegionFound) {
        switch (outputNames.size()) {
        case 1:
            yoloVersion = YoloVersion::YOLOF;
            break;
        case 2:
            yoloVersion = YoloVersion::YOLO_V4_TINY;
            break;
        case 3:
            yoloVersion = YoloVersion::YOLO_V4;
            break;
        }

        int num = yoloVersion == YoloVersion::YOLOF ? 6 : 3;
        isObjConf = yoloVersion == YoloVersion::YOLOF ? 0 : 1;
        int i = 0;

        const std::vector<int64_t> defaultMasks[]{// YOLOv1v2
                                                  {},
                                                  // YOLOv3
                                                  {},
                                                  // YOLOv4
                                                  {0, 1, 2, 3, 4, 5, 6, 7, 8},
                                                  // YOLOv4_Tiny
                                                  {1, 2, 3, 3, 4, 5},
                                                  // YOLOF
                                                  {0, 1, 2, 3, 4, 5}};
        auto chosenMasks = presetMasks.size() ? presetMasks : defaultMasks[size_t(yoloVersion)];
        if (chosenMasks.size() != num * outputs.size()) {
            throw std::runtime_error("Invalid size of masks array, got " + std::to_string(presetMasks.size()) +
                                     ", should be " + std::to_string(num * outputs.size()));
        }

        std::sort(outputNames.begin(),
                  outputNames.end(),
                  [&outShapes, this](const std::string& x, const std::string& y) {
                      return outShapes[x][ov::layout::height_idx(yoloRegionLayout)] >
                             outShapes[y][ov::layout::height_idx(yoloRegionLayout)];
                  });

        for (const auto& name : outputNames) {
            const auto& shape = outShapes[name];
            if (shape[ov::layout::channels_idx(yoloRegionLayout)] % num != 0) {
                throw std::logic_error(std::string("Output tensor ") + name + " has wrong channel dimension");
            }
            regions.emplace(
                name,
                Region(shape[ov::layout::channels_idx(yoloRegionLayout)] / num - 4 - (isObjConf ? 1 : 0),
                       4,
                       presetAnchors.size() ? presetAnchors : defaultAnchors[size_t(yoloVersion)],
                       std::vector<int64_t>(chosenMasks.begin() + i * num, chosenMasks.begin() + (i + 1) * num),
                       shape[ov::layout::width_idx(yoloRegionLayout)],
                       shape[ov::layout::height_idx(yoloRegionLayout)]));
            i++;
        }
    } else {
        // Currently externally set anchors and masks are supported only for YoloV4
        if (presetAnchors.size() || presetMasks.size()) {
            slog::warn << "Preset anchors and mask can be set for YoloV4 model only. "
                          "This model is not YoloV4, so these options will be ignored."
                       << slog::endl;
        }
    }
}

std::unique_ptr<ResultBase> ModelYolo::postprocess(InferenceResult& infResult) {
    DetectionResult* result = new DetectionResult(infResult.frameId, infResult.metaData);
    std::vector<DetectedObject> objects;

    // Parsing outputs
    const auto& internalData = infResult.internalModelData->asRef<InternalImageModelData>();

    for (auto& output : infResult.outputsData) {
        this->parseYOLOOutput(output.first,
                              output.second,
                              netInputHeight,
                              netInputWidth,
                              internalData.inputImgHeight,
                              internalData.inputImgWidth,
                              objects);
    }

    if (useAdvancedPostprocessing) {
        // Advanced postprocessing
        // Checking IOU threshold conformance
        // For every i-th object we're finding all objects it intersects with, and comparing confidence
        // If i-th object has greater confidence than all others, we include it into result
        for (const auto& obj1 : objects) {
            bool isGoodResult = true;
            for (const auto& obj2 : objects) {
                if (obj1.labelID == obj2.labelID && obj1.confidence < obj2.confidence &&
                    intersectionOverUnion(obj1, obj2) >= iou_threshold) {  // if obj1 is the same as obj2, condition
                                                                           // expression will evaluate to false anyway
                    isGoodResult = false;
                    break;
                }
            }
            if (isGoodResult) {
                result->objects.push_back(obj1);
            }
        }
    } else {
        // Classic postprocessing
        std::sort(objects.begin(), objects.end(), [](const DetectedObject& x, const DetectedObject& y) {
            return x.confidence > y.confidence;
        });
        for (size_t i = 0; i < objects.size(); ++i) {
            if (objects[i].confidence == 0)
                continue;
            for (size_t j = i + 1; j < objects.size(); ++j)
                if (intersectionOverUnion(objects[i], objects[j]) >= iou_threshold)
                    objects[j].confidence = 0;
            result->objects.push_back(objects[i]);
        }
    }

    return std::unique_ptr<ResultBase>(result);
}

void ModelYolo::parseYOLOOutput(const std::string& output_name,
                                const ov::Tensor& tensor,
                                const unsigned long resized_im_h,
                                const unsigned long resized_im_w,
                                const unsigned long original_im_h,
                                const unsigned long original_im_w,
                                std::vector<DetectedObject>& objects) {
    // --------------------------- Extracting layer parameters -------------------------------------
    auto it = regions.find(output_name);
    if (it == regions.end()) {
        throw std::runtime_error(std::string("Can't find output layer with name ") + output_name);
    }
    auto& region = it->second;

    int sideW = 0;
    int sideH = 0;
    unsigned long scaleH;
    unsigned long scaleW;
    switch (yoloVersion) {
    case YoloVersion::YOLO_V1V2:
        sideH = region.outputHeight;
        sideW = region.outputWidth;
        scaleW = region.outputWidth;
        scaleH = region.outputHeight;
        break;
    case YoloVersion::YOLO_V3:
    case YoloVersion::YOLO_V4:
    case YoloVersion::YOLO_V4_TINY:
    case YoloVersion::YOLOF:
        sideH = static_cast<int>(tensor.get_shape()[ov::layout::height_idx("NCHW")]);
        sideW = static_cast<int>(tensor.get_shape()[ov::layout::width_idx("NCHW")]);
        scaleW = resized_im_w;
        scaleH = resized_im_h;
        break;
    default:
        throw std::runtime_error("Unknown YoloVersion");
    }

    auto entriesNum = sideW * sideH;
    const float* outData = tensor.data<float>();

    auto postprocessRawData = (yoloVersion == YoloVersion::YOLO_V4 || yoloVersion == YoloVersion::YOLO_V4_TINY ||
                               yoloVersion == YoloVersion::YOLOF)
                                  ? sigmoid
                                  : identity;

    // --------------------------- Parsing YOLO Region output -------------------------------------
    for (int i = 0; i < entriesNum; ++i) {
        int row = i / sideW;
        int col = i % sideW;
        for (int n = 0; n < region.num; ++n) {
            //--- Getting region data
            int obj_index = calculateEntryIndex(entriesNum,
                                                region.coords,
                                                region.classes + isObjConf,
                                                n * entriesNum + i,
                                                region.coords);
            int box_index =
                calculateEntryIndex(entriesNum, region.coords, region.classes + isObjConf, n * entriesNum + i, 0);
            float scale = isObjConf ? postprocessRawData(outData[obj_index]) : 1;

            //--- Preliminary check for confidence threshold conformance
            if (scale >= confidence_threshold) {
                //--- Calculating scaled region's coordinates
                float x, y;
                if (yoloVersion == YoloVersion::YOLOF) {
                    x = (static_cast<float>(col) / sideW +
                         outData[box_index + 0 * entriesNum] * region.anchors[2 * n] / scaleW) *
                        original_im_w;
                    y = (static_cast<float>(row) / sideH +
                         outData[box_index + 1 * entriesNum] * region.anchors[2 * n + 1] / scaleH) *
                        original_im_h;
                } else {
                    x = static_cast<float>((col + postprocessRawData(outData[box_index + 0 * entriesNum])) / sideW *
                                           original_im_w);
                    y = static_cast<float>((row + postprocessRawData(outData[box_index + 1 * entriesNum])) / sideH *
                                           original_im_h);
                }
                float height = static_cast<float>(std::exp(outData[box_index + 3 * entriesNum]) *
                                                  region.anchors[2 * n + 1] * original_im_h / scaleH);
                float width = static_cast<float>(std::exp(outData[box_index + 2 * entriesNum]) * region.anchors[2 * n] *
                                                 original_im_w / scaleW);

                DetectedObject obj;
                obj.x = clamp(x - width / 2, 0.f, static_cast<float>(original_im_w));
                obj.y = clamp(y - height / 2, 0.f, static_cast<float>(original_im_h));
                obj.width = clamp(width, 0.f, static_cast<float>(original_im_w - obj.x));
                obj.height = clamp(height, 0.f, static_cast<float>(original_im_h - obj.y));

                for (size_t j = 0; j < region.classes; ++j) {
                    int class_index = calculateEntryIndex(entriesNum,
                                                          region.coords,
                                                          region.classes + isObjConf,
                                                          n * entriesNum + i,
                                                          region.coords + isObjConf + j);
                    float prob = scale * postprocessRawData(outData[class_index]);

                    //--- Checking confidence threshold conformance and adding region to the list
                    if (prob >= confidence_threshold) {
                        obj.confidence = prob;
                        obj.labelID = j;
                        obj.label = getLabelName(obj.labelID);
                        objects.push_back(obj);
                    }
                }
            }
        }
    }
}

int ModelYolo::calculateEntryIndex(int totalCells, int lcoords, size_t lclasses, int location, int entry) {
    int n = location / totalCells;
    int loc = location % totalCells;
    return (n * (lcoords + lclasses) + entry) * totalCells + loc;
}

double ModelYolo::intersectionOverUnion(const DetectedObject& o1, const DetectedObject& o2) {
    double overlappingWidth = fmin(o1.x + o1.width, o2.x + o2.width) - fmax(o1.x, o2.x);
    double overlappingHeight = fmin(o1.y + o1.height, o2.y + o2.height) - fmax(o1.y, o2.y);
    double intersectionArea =
        (overlappingWidth < 0 || overlappingHeight < 0) ? 0 : overlappingHeight * overlappingWidth;
    double unionArea = o1.width * o1.height + o2.width * o2.height - intersectionArea;
    return intersectionArea / unionArea;
}

ModelYolo::Region::Region(const std::shared_ptr<ov::op::v0::RegionYolo>& regionYolo) {
    coords = regionYolo->get_num_coords();
    classes = regionYolo->get_num_classes();
    auto mask = regionYolo->get_mask();
    num = mask.size();

    auto shape = regionYolo->get_input_shape(0);
    outputWidth = shape[3];
    outputHeight = shape[2];

    if (num) {
        // Parsing YoloV3 parameters
        anchors.resize(num * 2);

        for (int i = 0; i < num; ++i) {
            anchors[i * 2] = regionYolo->get_anchors()[mask[i] * 2];
            anchors[i * 2 + 1] = regionYolo->get_anchors()[mask[i] * 2 + 1];
        }
    } else {
        // Parsing YoloV2 parameters
        num = regionYolo->get_num_regions();
        anchors = regionYolo->get_anchors();
        if (anchors.empty()) {
            anchors = defaultAnchors[size_t(YoloVersion::YOLO_V1V2)];
            num = 5;
        }
    }
}

ModelYolo::Region::Region(size_t classes,
                          int coords,
                          const std::vector<float>& anchors,
                          const std::vector<int64_t>& masks,
                          size_t outputWidth,
                          size_t outputHeight)
    : classes(classes),
      coords(coords),
      outputWidth(outputWidth),
      outputHeight(outputHeight) {
    num = masks.size();

    if (anchors.size() == 0 || anchors.size() % 2 != 0) {
        throw std::runtime_error("Explicitly initialized region should have non-empty even-sized regions vector");
    }

    if (num) {
        this->anchors.resize(num * 2);

        for (int i = 0; i < num; ++i) {
            this->anchors[i * 2] = anchors[masks[i] * 2];
            this->anchors[i * 2 + 1] = anchors[masks[i] * 2 + 1];
        }
    } else {
        this->anchors = anchors;
        num = anchors.size() / 2;
    }
}

std::string YOLOv5::ModelType = "YOLOv5";

void YOLOv5::prepareInputsOutputs(std::shared_ptr<ov::Model>& model) {
    const ov::Output<ov::Node>& input = model->input();
    const ov::Shape& in_shape = input.get_partial_shape().get_max_shape();
    if (in_shape.size() != 4) {
        throw std::runtime_error("YOLO: the rank of the input must be 4");
    }
    inputNames.push_back(input.get_any_name());
    const ov::Layout& inputLayout = getInputLayout(input);
    if (!embedded_processing) {
        model = ImageModel::embedProcessing(
            model,
            inputNames[0],
            inputLayout,
            resizeMode,
            interpolationMode,
            ov::Shape{in_shape[ov::layout::width_idx(inputLayout)], in_shape[ov::layout::height_idx(inputLayout)]},
            pad_value,
            reverse_input_channels,
            mean_values,
            scale_values);

        netInputWidth = in_shape[ov::layout::width_idx(inputLayout)];
        netInputHeight = in_shape[ov::layout::height_idx(inputLayout)];

        embedded_processing = true;
    }

    const ov::Output<const ov::Node>& output = model->output();
    if (ov::element::Type_t::f32 != output.get_element_type()) {
        throw std::runtime_error("YOLO: the output must be of precision f32");
    }
    const ov::Shape& out_shape = output.get_partial_shape().get_max_shape();
    if (3 != out_shape.size()) {
        throw std::runtime_error("YOLO: the output must be of rank 3");
    }
    if (!labels.empty() && labels.size() + 4 != out_shape[1]) {
        throw std::runtime_error("YOLO: number of labels must be smaller than out_shape[1] by 4");
    }
}

void YOLOv5::updateModelInfo() {
    DetectionModelExt::updateModelInfo();
    model->set_rt_info(YOLOv5::ModelType, "model_info", "model_type");
    model->set_rt_info(agnostic_nms, "model_info", "agnostic_nms");
    model->set_rt_info(iou_threshold, "model_info", "iou_threshold");
}

void YOLOv5::init_from_config(const ov::AnyMap& top_priority, const ov::AnyMap& mid_priority) {
    pad_value = get_from_any_maps("pad_value", top_priority, mid_priority, 114);
    if (top_priority.find("resize_type") == top_priority.end() &&
        mid_priority.find("resize_type") == mid_priority.end()) {
        interpolationMode = cv::INTER_LINEAR;
        resizeMode = RESIZE_KEEP_ASPECT_LETTERBOX;
    }
    reverse_input_channels = get_from_any_maps("reverse_input_channels", top_priority, mid_priority, true);
    scale_values = get_from_any_maps("scale_values", top_priority, mid_priority, std::vector<float>{255.0f});
    confidence_threshold = get_from_any_maps("confidence_threshold", top_priority, mid_priority, 0.25f);
    agnostic_nms = get_from_any_maps("agnostic_nms", top_priority, mid_priority, agnostic_nms);
    iou_threshold = get_from_any_maps("iou_threshold", top_priority, mid_priority, 0.7f);
}

YOLOv5::YOLOv5(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : DetectionModelExt(model, configuration) {
    init_from_config(configuration, model->get_rt_info<ov::AnyMap>("model_info"));
}

YOLOv5::YOLOv5(std::shared_ptr<InferenceAdapter>& adapter) : DetectionModelExt(adapter) {
    init_from_config(adapter->getModelConfig(), ov::AnyMap{});
}

std::unique_ptr<ResultBase> YOLOv5::postprocess(InferenceResult& infResult) {
    if (1 != infResult.outputsData.size()) {
        throw std::runtime_error("YOLO: expect 1 output");
    }
    const ov::Tensor& detectionsTensor = infResult.getFirstOutputTensor();
    const ov::Shape& out_shape = detectionsTensor.get_shape();
    if (3 != out_shape.size()) {
        throw std::runtime_error("YOLO: the output must be of rank 3");
    }
    if (1 != out_shape[0]) {
        throw std::runtime_error("YOLO: the first dim of the output must be 1");
    }
    size_t num_proposals = out_shape[2];
    std::vector<AnchorLabeled> boxes_with_class;
    std::vector<float> confidences;
    const float* const detections = detectionsTensor.data<float>();
    for (size_t i = 0; i < num_proposals; ++i) {
        float confidence = 0.0f;
        size_t max_id = 0;
        constexpr size_t LABELS_START = 4;
        for (size_t j = LABELS_START; j < out_shape[1]; ++j) {
            if (detections[j * num_proposals + i] > confidence) {
                confidence = detections[j * num_proposals + i];
                max_id = j;
            }
        }
        if (confidence > confidence_threshold) {
            boxes_with_class.emplace_back(detections[0 * num_proposals + i] - detections[2 * num_proposals + i] / 2.0f,
                                          detections[1 * num_proposals + i] - detections[3 * num_proposals + i] / 2.0f,
                                          detections[0 * num_proposals + i] + detections[2 * num_proposals + i] / 2.0f,
                                          detections[1 * num_proposals + i] + detections[3 * num_proposals + i] / 2.0f,
                                          max_id - LABELS_START);
            confidences.push_back(confidence);
        }
    }
    constexpr bool includeBoundaries = false;
    constexpr size_t keep_top_k = 30000;
    std::vector<size_t> keep;
    if (agnostic_nms) {
        keep = nms(boxes_with_class, confidences, iou_threshold, includeBoundaries, keep_top_k);
    } else {
        keep = multiclass_nms(boxes_with_class, confidences, iou_threshold, includeBoundaries, keep_top_k);
    }
    DetectionResult* result = new DetectionResult(infResult.frameId, infResult.metaData);
    auto base = std::unique_ptr<ResultBase>(result);
    const auto& internalData = infResult.internalModelData->asRef<InternalImageModelData>();
    float floatInputImgWidth = float(internalData.inputImgWidth),
          floatInputImgHeight = float(internalData.inputImgHeight);
    float invertedScaleX = floatInputImgWidth / netInputWidth, invertedScaleY = floatInputImgHeight / netInputHeight;
    int padLeft = 0, padTop = 0;
    if (RESIZE_KEEP_ASPECT == resizeMode || RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
        invertedScaleX = invertedScaleY = std::max(invertedScaleX, invertedScaleY);
        if (RESIZE_KEEP_ASPECT_LETTERBOX == resizeMode) {
            padLeft = (netInputWidth - int(std::round(floatInputImgWidth / invertedScaleX))) / 2;
            padTop = (netInputHeight - int(std::round(floatInputImgHeight / invertedScaleY))) / 2;
        }
    }
    for (size_t idx : keep) {
        DetectedObject desc;
        desc.x = clamp(round((boxes_with_class[idx].left - padLeft) * invertedScaleX), 0.f, floatInputImgWidth);
        desc.y = clamp(round((boxes_with_class[idx].top - padTop) * invertedScaleY), 0.f, floatInputImgHeight);
        desc.width =
            clamp(round((boxes_with_class[idx].right - padLeft) * invertedScaleX), 0.f, floatInputImgWidth) - desc.x;
        desc.height =
            clamp(round((boxes_with_class[idx].bottom - padTop) * invertedScaleY), 0.f, floatInputImgHeight) - desc.y;
        desc.confidence = confidences[idx];
        desc.labelID = static_cast<size_t>(boxes_with_class[idx].labelID);
        desc.label = getLabelName(desc.labelID);
        result->objects.push_back(desc);
    }
    return base;
}

std::string YOLOv8::ModelType = "YOLOv8";
