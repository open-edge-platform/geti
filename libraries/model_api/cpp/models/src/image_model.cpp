/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "models/image_model.h"

#include <adapters/inference_adapter.h>
#include <utils/image_utils.h>

#include <fstream>
#include <opencv2/core.hpp>
#include <openvino/openvino.hpp>
#include <stdexcept>
#include <utils/ocv_common.hpp>
#include <vector>

#include "models/input_data.h"
#include "models/internal_model_data.h"
#include "models/results.h"

ImageModel::ImageModel(const std::string& modelFile,
                       const std::string& resize_type,
                       bool useAutoResize,
                       const std::string& layout)
    : ModelBase(modelFile, layout),
      useAutoResize(useAutoResize),
      resizeMode(selectResizeMode(resize_type)) {}

RESIZE_MODE ImageModel::selectResizeMode(const std::string& resize_type) {
    RESIZE_MODE resize = RESIZE_FILL;
    if ("crop" == resize_type) {
        resize = RESIZE_CROP;
    } else if ("standard" == resize_type) {
        resize = RESIZE_FILL;
    } else if ("fit_to_window" == resize_type) {
        resize = RESIZE_KEEP_ASPECT;
    } else if ("fit_to_window_letterbox" == resize_type) {
        resize = RESIZE_KEEP_ASPECT_LETTERBOX;
    } else {
        throw std::runtime_error("Unknown value for resize_type arg");
    }

    return resize;
}

void ImageModel::init_from_config(const ov::AnyMap& top_priority, const ov::AnyMap& mid_priority) {
    useAutoResize = get_from_any_maps("auto_resize", top_priority, mid_priority, useAutoResize);

    std::string resize_type = "standard";
    resize_type = get_from_any_maps("resize_type", top_priority, mid_priority, resize_type);
    resizeMode = selectResizeMode(resize_type);

    labels = get_from_any_maps("labels", top_priority, mid_priority, labels);
    embedded_processing = get_from_any_maps("embedded_processing", top_priority, mid_priority, embedded_processing);
    netInputWidth = get_from_any_maps("orig_width", top_priority, mid_priority, netInputWidth);
    netInputHeight = get_from_any_maps("orig_height", top_priority, mid_priority, netInputHeight);
    int pad_value_int = 0;
    pad_value_int = get_from_any_maps("pad_value", top_priority, mid_priority, pad_value_int);
    if (0 > pad_value_int || 255 < pad_value_int) {
        throw std::runtime_error("pad_value must be in range [0, 255]");
    }
    pad_value = static_cast<uint8_t>(pad_value_int);
    reverse_input_channels =
        get_from_any_maps("reverse_input_channels", top_priority, mid_priority, reverse_input_channels);
    scale_values = get_from_any_maps("scale_values", top_priority, mid_priority, scale_values);
    mean_values = get_from_any_maps("mean_values", top_priority, mid_priority, mean_values);
}

ImageModel::ImageModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : ModelBase(model, configuration) {
    init_from_config(configuration,
                     model->has_rt_info("model_info") ? model->get_rt_info<ov::AnyMap>("model_info") : ov::AnyMap{});
}

ImageModel::ImageModel(std::shared_ptr<InferenceAdapter>& adapter, const ov::AnyMap& configuration)
    : ModelBase(adapter, configuration) {
    init_from_config(configuration, adapter->getModelConfig());
}

std::unique_ptr<ResultBase> ImageModel::inferImage(const ImageInputData& inputData) {
    return ModelBase::infer(static_cast<const InputData&>(inputData));
    ;
}

std::vector<std::unique_ptr<ResultBase>> ImageModel::inferBatchImage(const std::vector<ImageInputData>& inputImgs) {
    std::vector<std::reference_wrapper<const InputData>> inputData;
    inputData.reserve(inputImgs.size());
    for (const auto& img : inputImgs) {
        inputData.push_back(static_cast<const InputData&>(img));
    }
    return ModelBase::inferBatch(inputData);
}

void ImageModel::inferAsync(const ImageInputData& inputData, const ov::AnyMap& callback_args) {
    ModelBase::inferAsync(static_cast<const InputData&>(inputData), callback_args);
}

void ImageModel::updateModelInfo() {
    ModelBase::updateModelInfo();

    model->set_rt_info(useAutoResize, "model_info", "auto_resize");
    model->set_rt_info(formatResizeMode(resizeMode), "model_info", "resize_type");

    if (!labels.empty()) {
        model->set_rt_info(labels, "model_info", "labels");
    }

    model->set_rt_info(embedded_processing, "model_info", "embedded_processing");
    model->set_rt_info(netInputWidth, "model_info", "orig_width");
    model->set_rt_info(netInputHeight, "model_info", "orig_height");
}

std::shared_ptr<ov::Model> ImageModel::embedProcessing(std::shared_ptr<ov::Model>& model,
                                                       const std::string& inputName,
                                                       const ov::Layout& layout,
                                                       const RESIZE_MODE resize_mode,
                                                       const cv::InterpolationFlags interpolationMode,
                                                       const ov::Shape& targetShape,
                                                       uint8_t pad_value,
                                                       bool brg2rgb,
                                                       const std::vector<float>& mean,
                                                       const std::vector<float>& scale,
                                                       const std::type_info& dtype) {
    ov::preprocess::PrePostProcessor ppp(model);

    // Change the input type to the 8-bit image
    if (dtype == typeid(int)) {
        ppp.input(inputName).tensor().set_element_type(ov::element::u8);
    }

    ppp.input(inputName).tensor().set_layout(ov::Layout("NHWC")).set_color_format(ov::preprocess::ColorFormat::BGR);

    if (resize_mode != NO_RESIZE) {
        ppp.input(inputName).tensor().set_spatial_dynamic_shape();
        // Doing resize in u8 is more efficient than FP32 but can lead to slightly different results
        ppp.input(inputName).preprocess().custom(
            createResizeGraph(resize_mode, targetShape, interpolationMode, pad_value));
    }

    ppp.input(inputName).model().set_layout(ov::Layout(layout));

    // Handle color format
    if (brg2rgb) {
        ppp.input(inputName).preprocess().convert_color(ov::preprocess::ColorFormat::RGB);
    }

    ppp.input(inputName).preprocess().convert_element_type(ov::element::f32);

    if (!mean.empty()) {
        ppp.input(inputName).preprocess().mean(mean);
    }
    if (!scale.empty()) {
        ppp.input(inputName).preprocess().scale(scale);
    }

    return ppp.build();
}

std::shared_ptr<InternalModelData> ImageModel::preprocess(const InputData& inputData, InferenceInput& input) {
    const auto& origImg = inputData.asRef<ImageInputData>().inputImage;
    auto img = inputTransform(origImg);

    if (!useAutoResize && !embedded_processing) {
        // Resize and copy data from the image to the input tensor
        auto tensorShape =
            inferenceAdapter->getInputShape(inputNames[0]).get_max_shape();  // first input should be image
        const ov::Layout layout("NHWC");
        const size_t width = tensorShape[ov::layout::width_idx(layout)];
        const size_t height = tensorShape[ov::layout::height_idx(layout)];
        const size_t channels = tensorShape[ov::layout::channels_idx(layout)];
        if (static_cast<size_t>(img.channels()) != channels) {
            throw std::runtime_error("The number of channels for model input: " + std::to_string(channels) +
                                     " and image: " + std::to_string(img.channels()) + " - must match");
        }
        if (channels != 1 && channels != 3) {
            throw std::runtime_error("Unsupported number of channels");
        }
        img = resizeImageExt(img, width, height, resizeMode, interpolationMode);
    }
    input.emplace(inputNames[0], wrapMat2Tensor(img));
    return std::make_shared<InternalImageModelData>(origImg.cols, origImg.rows);
}

std::vector<std::string> ImageModel::loadLabels(const std::string& labelFilename) {
    std::vector<std::string> labelsList;

    /* Read labels (if any) */
    if (!labelFilename.empty()) {
        std::ifstream inputFile(labelFilename);
        if (!inputFile.is_open())
            throw std::runtime_error("Can't open the labels file: " + labelFilename);
        std::string label;
        while (std::getline(inputFile, label)) {
            labelsList.push_back(label);
        }
        if (labelsList.empty())
            throw std::logic_error("File is empty: " + labelFilename);
    }

    return labelsList;
}
