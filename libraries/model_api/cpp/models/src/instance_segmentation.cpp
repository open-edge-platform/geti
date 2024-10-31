/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "models/instance_segmentation.h"

#include <stddef.h>
#include <stdint.h>

#include <fstream>
#include <limits>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <openvino/openvino.hpp>
#include <stdexcept>
#include <string>
#include <vector>

#include "models/input_data.h"
#include "models/internal_model_data.h"
#include "models/results.h"
#include "utils/common.hpp"

namespace {
constexpr char saliency_map_name[]{"saliency_map"};
constexpr char feature_vector_name[]{"feature_vector"};

void append_xai_names(const std::vector<ov::Output<ov::Node>>& outputs, std::vector<std::string>& outputNames) {
    for (const ov::Output<ov::Node>& output : outputs) {
        if (output.get_names().count(saliency_map_name) > 0) {
            outputNames.emplace_back(saliency_map_name);
        } else if (output.get_names().count(feature_vector_name) > 0) {
            outputNames.push_back(feature_vector_name);
        }
    }
}

cv::Rect expand_box(const cv::Rect2f& box, float scale) {
    float w_half = box.width * 0.5f * scale, h_half = box.height * 0.5f * scale;
    const cv::Point2f& center = (box.tl() + box.br()) * 0.5f;
    return {cv::Point(int(center.x - w_half), int(center.y - h_half)),
            cv::Point(int(center.x + w_half), int(center.y + h_half))};
}

std::vector<cv::Mat_<std::uint8_t>> average_and_normalize(const std::vector<std::vector<cv::Mat>>& saliency_maps) {
    std::vector<cv::Mat_<std::uint8_t>> aggregated;
    aggregated.reserve(saliency_maps.size());
    for (const std::vector<cv::Mat>& per_object_maps : saliency_maps) {
        if (per_object_maps.empty()) {
            aggregated.emplace_back();
        } else {
            cv::Mat_<double> saliency_map{per_object_maps.front().size()};
            for (const cv::Mat& per_object_map : per_object_maps) {
                if (saliency_map.size != per_object_map.size) {
                    throw std::runtime_error("saliency_maps must have same size");
                }
                if (per_object_map.channels() != 1) {
                    throw std::runtime_error("saliency_maps must have one channel");
                }
                if (per_object_map.type() != CV_8U) {
                    throw std::runtime_error("saliency_maps must have type CV_8U");
                }
            }
            for (int row = 0; row < saliency_map.rows; ++row) {
                for (int col = 0; col < saliency_map.cols; ++col) {
                    std::uint8_t max_val = 0;
                    for (const cv::Mat& per_object_map : per_object_maps) {
                        max_val = std::max(max_val, per_object_map.at<std::uint8_t>(row, col));
                    }
                    saliency_map.at<double>(row, col) = max_val;
                }
            }
            double min, max;
            cv::minMaxLoc(saliency_map, &min, &max);
            cv::Mat_<std::uint8_t> converted;
            saliency_map.convertTo(converted, CV_8U, 255.0 / (max + 1e-12));
            aggregated.push_back(std::move(converted));
        }
    }
    return aggregated;
}

struct Lbm {
    ov::Tensor labels, boxes, masks;
};

Lbm filterTensors(const std::map<std::string, ov::Tensor>& infResult) {
    Lbm lbm;
    for (const auto& pair : infResult) {
        if (pair.first == saliency_map_name || pair.first == feature_vector_name) {
            continue;
        }
        switch (pair.second.get_shape().size()) {
        case 2:
            lbm.labels = pair.second;
            break;
        case 3:
            lbm.boxes = pair.second;
            break;
        case 4:
            lbm.masks = pair.second;
            break;
        case 0:
            break;
        default:
            throw std::runtime_error("Unexpected result: " + pair.first);
        }
    }
    return lbm;
}
}  // namespace

cv::Mat segm_postprocess(const SegmentedObject& box, const cv::Mat& unpadded, int im_h, int im_w) {
    // Add zero border to prevent upsampling artifacts on segment borders.
    cv::Mat raw_cls_mask;
    cv::copyMakeBorder(unpadded, raw_cls_mask, 1, 1, 1, 1, cv::BORDER_CONSTANT, {0});
    cv::Rect extended_box = expand_box(box, float(raw_cls_mask.cols) / (raw_cls_mask.cols - 2));

    int w = std::max(extended_box.width + 1, 1);
    int h = std::max(extended_box.height + 1, 1);
    int x0 = clamp(extended_box.x, 0, im_w);
    int y0 = clamp(extended_box.y, 0, im_h);
    int x1 = clamp(extended_box.x + extended_box.width + 1, 0, im_w);
    int y1 = clamp(extended_box.y + extended_box.height + 1, 0, im_h);

    cv::Mat resized;
    cv::resize(raw_cls_mask, resized, {w, h});
    cv::Mat im_mask(cv::Size{im_w, im_h}, CV_8UC1, cv::Scalar{0});
    im_mask(cv::Rect{x0, y0, x1 - x0, y1 - y0})
        .setTo(1,
               resized({cv::Point(x0 - extended_box.x, y0 - extended_box.y),
                        cv::Point(x1 - extended_box.x, y1 - extended_box.y)}) > 0.5f);
    return im_mask;
}

std::string MaskRCNNModel::ModelType = "MaskRCNN";

void MaskRCNNModel::init_from_config(const ov::AnyMap& top_priority, const ov::AnyMap& mid_priority) {
    confidence_threshold = get_from_any_maps("confidence_threshold", top_priority, mid_priority, confidence_threshold);
    postprocess_semantic_masks =
        get_from_any_maps("postprocess_semantic_masks", top_priority, mid_priority, postprocess_semantic_masks);
}

MaskRCNNModel::MaskRCNNModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : ImageModel(model, configuration) {
    init_from_config(configuration,
                     model->has_rt_info("model_info") ? model->get_rt_info<ov::AnyMap>("model_info") : ov::AnyMap{});
}

MaskRCNNModel::MaskRCNNModel(std::shared_ptr<InferenceAdapter>& adapter, const ov::AnyMap& configuration)
    : ImageModel(adapter, configuration) {
    init_from_config(configuration, adapter->getModelConfig());
}

std::unique_ptr<MaskRCNNModel> MaskRCNNModel::create_model(const std::string& modelFile,
                                                           const ov::AnyMap& configuration,
                                                           bool preload,
                                                           const std::string& device) {
    auto core = ov::Core();
    std::shared_ptr<ov::Model> model = core.read_model(modelFile);

    // Check model_type in the rt_info, ignore configuration
    std::string model_type = MaskRCNNModel::ModelType;
    try {
        if (model->has_rt_info("model_info", "model_type")) {
            model_type = model->get_rt_info<std::string>("model_info", "model_type");
        }
    } catch (const std::exception&) {
        slog::warn << "Model type is not specified in the rt_info, use default model type: " << model_type
                   << slog::endl;
    }

    if (model_type != MaskRCNNModel::ModelType) {
        throw std::runtime_error("Incorrect or unsupported model_type is provided in the model_info section: " +
                                 model_type);
    }

    std::unique_ptr<MaskRCNNModel> segmentor{new MaskRCNNModel(model, configuration)};
    segmentor->prepare();
    if (preload) {
        segmentor->load(core, device);
    }
    return segmentor;
}

std::unique_ptr<MaskRCNNModel> MaskRCNNModel::create_model(std::shared_ptr<InferenceAdapter>& adapter) {
    const ov::AnyMap& configuration = adapter->getModelConfig();
    auto model_type_iter = configuration.find("model_type");
    std::string model_type = MaskRCNNModel::ModelType;
    if (model_type_iter != configuration.end()) {
        model_type = model_type_iter->second.as<std::string>();
    }

    if (model_type != MaskRCNNModel::ModelType) {
        throw std::runtime_error("Incorrect or unsupported model_type is provided: " + model_type);
    }

    std::unique_ptr<MaskRCNNModel> segmentor{new MaskRCNNModel(adapter)};
    return segmentor;
}

void MaskRCNNModel::updateModelInfo() {
    ImageModel::updateModelInfo();

    model->set_rt_info(MaskRCNNModel::ModelType, "model_info", "model_type");
    model->set_rt_info(confidence_threshold, "model_info", "confidence_threshold");
    model->set_rt_info(postprocess_semantic_masks, "model_info", "postprocess_semantic_masks");
}

void MaskRCNNModel::prepareInputsOutputs(std::shared_ptr<ov::Model>& model) {
    // --------------------------- Configure input & output ---------------------------------------------
    // --------------------------- Prepare input  -----------------------------------------------------
    if (model->inputs().size() != 1) {
        throw std::logic_error("MaskRCNNModel model wrapper supports topologies with only 1 input");
    }
    const auto& input = model->input();
    inputNames.push_back(input.get_any_name());

    const ov::Layout& inputLayout = getInputLayout(input);
    const ov::Shape& inputShape = input.get_partial_shape().get_max_shape();
    if (inputShape.size() != 4 || inputShape[ov::layout::channels_idx(inputLayout)] != 3) {
        throw std::logic_error("3-channel 4-dimensional model's input is expected");
    }

    if (!embedded_processing) {
        model = ImageModel::embedProcessing(
            model,
            inputNames[0],
            inputLayout,
            resizeMode,
            interpolationMode,
            ov::Shape{inputShape[ov::layout::width_idx(inputLayout)], inputShape[ov::layout::height_idx(inputLayout)]},
            pad_value,
            reverse_input_channels,
            mean_values,
            scale_values);

        netInputWidth = inputShape[ov::layout::width_idx(inputLayout)];
        netInputHeight = inputShape[ov::layout::height_idx(inputLayout)];
        useAutoResize = true;  // temporal solution
        embedded_processing = true;
    }

    // --------------------------- Prepare output  -----------------------------------------------------
    struct NameRank {
        std::string name;
        size_t rank;
    };
    std::vector<NameRank> filtered;
    filtered.reserve(3);
    for (ov::Output<ov::Node>& output : model->outputs()) {
        const std::unordered_set<std::string>& out_names = output.get_names();
        if (out_names.find(saliency_map_name) == out_names.end() &&
            out_names.find(feature_vector_name) == out_names.end()) {
            filtered.push_back({output.get_any_name(), output.get_partial_shape().get_max_shape().size()});
        }
    }
    if (filtered.size() != 3 && filtered.size() != 4) {
        throw std::logic_error(std::string{"MaskRCNNModel model wrapper supports topologies with "} +
                               saliency_map_name + ", " + feature_vector_name + " and 3 or 4 other outputs");
    }
    outputNames.resize(3);
    for (const NameRank& name_rank : filtered) {
        switch (name_rank.rank) {
        case 2:
            outputNames[0] = name_rank.name;
            break;
        case 3:
            outputNames[1] = name_rank.name;
            break;
        case 4:
            outputNames[2] = name_rank.name;
            break;
        case 0:
            break;
        default:
            throw std::runtime_error("Unexpected output: " + name_rank.name);
        }
    }
    append_xai_names(model->outputs(), outputNames);
}

std::unique_ptr<ResultBase> MaskRCNNModel::postprocess(InferenceResult& infResult) {
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
    const Lbm& lbm = filterTensors(infResult.outputsData);
    const int64_t* const labels_tensor_ptr = lbm.labels.data<int64_t>();
    const float* const boxes = lbm.boxes.data<float>();
    size_t objectSize = lbm.boxes.get_shape().back();
    float* const masks = lbm.masks.data<float>();
    const cv::Size& masks_size{int(lbm.masks.get_shape()[3]), int(lbm.masks.get_shape()[2])};
    InstanceSegmentationResult* result = new InstanceSegmentationResult(infResult.frameId, infResult.metaData);
    auto retVal = std::unique_ptr<ResultBase>(result);
    std::vector<std::vector<cv::Mat>> saliency_maps;
    bool has_feature_vector_name =
        std::find(outputNames.begin(), outputNames.end(), feature_vector_name) != outputNames.end();
    if (has_feature_vector_name) {
        if (labels.empty()) {
            throw std::runtime_error("Can't get number of classes because labels are empty");
        }
        saliency_maps.resize(labels.size());
    }
    for (size_t i = 0; i < lbm.labels.get_size(); ++i) {
        float confidence = boxes[i * objectSize + 4];
        if (confidence <= confidence_threshold && !has_feature_vector_name) {
            continue;
        }
        SegmentedObject obj;

        obj.confidence = confidence;
        obj.labelID = labels_tensor_ptr[i] + 1;
        if (!labels.empty() && obj.labelID >= labels.size()) {
            continue;
        }
        obj.label = getLabelName(obj.labelID);

        obj.x = clamp(round((boxes[i * objectSize + 0] - padLeft) * invertedScaleX), 0.f, floatInputImgWidth);
        obj.y = clamp(round((boxes[i * objectSize + 1] - padTop) * invertedScaleY), 0.f, floatInputImgHeight);
        obj.width =
            clamp(round((boxes[i * objectSize + 2] - padLeft) * invertedScaleX - obj.x), 0.f, floatInputImgWidth);
        obj.height =
            clamp(round((boxes[i * objectSize + 3] - padTop) * invertedScaleY - obj.y), 0.f, floatInputImgHeight);

        if (obj.height * obj.width <= 1) {
            continue;
        }

        cv::Mat raw_cls_mask{masks_size, CV_32F, masks + masks_size.area() * i};
        cv::Mat resized_mask;
        if (postprocess_semantic_masks || has_feature_vector_name) {
            resized_mask = segm_postprocess(obj, raw_cls_mask, internalData.inputImgHeight, internalData.inputImgWidth);
        } else {
            resized_mask = raw_cls_mask;
        }
        obj.mask = postprocess_semantic_masks ? resized_mask : raw_cls_mask.clone();
        if (confidence > confidence_threshold) {
            result->segmentedObjects.push_back(obj);
        }
        if (has_feature_vector_name && confidence > confidence_threshold) {
            saliency_maps[obj.labelID - 1].push_back(resized_mask);
        }
    }
    result->saliency_map = average_and_normalize(saliency_maps);
    if (has_feature_vector_name) {
        result->feature_vector = std::move(infResult.outputsData[feature_vector_name]);
    }
    return retVal;
}

std::unique_ptr<InstanceSegmentationResult> MaskRCNNModel::infer(const ImageInputData& inputData) {
    auto result = ImageModel::inferImage(inputData);
    return std::unique_ptr<InstanceSegmentationResult>(static_cast<InstanceSegmentationResult*>(result.release()));
}

std::vector<std::unique_ptr<InstanceSegmentationResult>> MaskRCNNModel::inferBatch(
    const std::vector<ImageInputData>& inputImgs) {
    auto results = ImageModel::inferBatchImage(inputImgs);
    std::vector<std::unique_ptr<InstanceSegmentationResult>> isegResults;
    isegResults.reserve(results.size());
    for (auto& result : results) {
        isegResults.emplace_back(static_cast<InstanceSegmentationResult*>(result.release()));
    }
    return isegResults;
}
