/*
 * Copyright (C) 2020-2024 Intel Corporation
 * SPDX-License-Identifier: Apache-2.0
 */

#include "models/model_base.h"

#include <adapters/openvino_adapter.h>
#include <models/results.h>

#include <openvino/openvino.hpp>
#include <utility>
#include <utils/common.hpp>
#include <utils/ocv_common.hpp>
#include <utils/slog.hpp>

#include "models/input_data.h"
#include "utils/args_helper.hpp"

namespace {
class TmpCallbackSetter {
public:
    ModelBase* model;
    std::function<void(std::unique_ptr<ResultBase>, const ov::AnyMap&)> last_callback;
    TmpCallbackSetter(ModelBase* model_,
                      std::function<void(std::unique_ptr<ResultBase>, const ov::AnyMap&)> tmp_callback,
                      std::function<void(std::unique_ptr<ResultBase>, const ov::AnyMap&)> last_callback_)
        : model(model_),
          last_callback(last_callback_) {
        model->setCallback(tmp_callback);
    }
    ~TmpCallbackSetter() {
        if (last_callback) {
            model->setCallback(last_callback);
        } else {
            model->setCallback([](std::unique_ptr<ResultBase>, const ov::AnyMap&) {});
        }
    }
};
}  // namespace

ModelBase::ModelBase(const std::string& modelFile, const std::string& layout)
    : modelFile(modelFile),
      inputsLayouts(parseLayoutString(layout)) {
    auto core = ov::Core();
    model = core.read_model(modelFile);
}

ModelBase::ModelBase(std::shared_ptr<InferenceAdapter>& adapter, const ov::AnyMap& configuration)
    : inferenceAdapter(adapter) {
    const ov::AnyMap& adapter_configuration = adapter->getModelConfig();

    std::string layout = "";
    layout = get_from_any_maps("layout", configuration, adapter_configuration, layout);
    inputsLayouts = parseLayoutString(layout);

    inputNames = adapter->getInputNames();
    outputNames = adapter->getOutputNames();
}

ModelBase::ModelBase(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration) : model(model) {
    auto layout_iter = configuration.find("layout");
    std::string layout = "";

    if (layout_iter != configuration.end()) {
        layout = layout_iter->second.as<std::string>();
    } else {
        if (model->has_rt_info("model_info", "layout")) {
            layout = model->get_rt_info<std::string>("model_info", "layout");
        }
    }
    inputsLayouts = parseLayoutString(layout);
}

void ModelBase::updateModelInfo() {
    if (!model) {
        throw std::runtime_error("The ov::Model object is not accessible");
    }

    if (!inputsLayouts.empty()) {
        auto layouts = formatLayouts(inputsLayouts);
        model->set_rt_info(layouts, "model_info", "layout");
    }
}

void ModelBase::load(ov::Core& core, const std::string& device, size_t num_infer_requests) {
    if (!inferenceAdapter) {
        inferenceAdapter = std::make_shared<OpenVINOInferenceAdapter>();
    }

    // Update model_info erased by pre/postprocessing
    updateModelInfo();

    inferenceAdapter->loadModel(model, core, device, {}, num_infer_requests);
}

std::shared_ptr<ov::Model> ModelBase::prepare() {
    prepareInputsOutputs(model);
    logBasicModelInfo(model);
    ov::set_batch(model, 1);

    return model;
}

ov::Layout ModelBase::getInputLayout(const ov::Output<ov::Node>& input) {
    ov::Layout layout = ov::layout::get_layout(input);
    if (layout.empty()) {
        if (inputsLayouts.empty()) {
            layout = getLayoutFromShape(input.get_partial_shape());
            slog::warn << "Automatically detected layout '" << layout.to_string() << "' for input '"
                       << input.get_any_name() << "' will be used." << slog::endl;
        } else if (inputsLayouts.size() == 1) {
            layout = inputsLayouts.begin()->second;
        } else {
            layout = inputsLayouts[input.get_any_name()];
        }
    }

    return layout;
}

std::unique_ptr<ResultBase> ModelBase::infer(const InputData& inputData) {
    InferenceInput inputs;
    InferenceResult result;
    auto internalModelData = this->preprocess(inputData, inputs);

    result.outputsData = inferenceAdapter->infer(inputs);
    result.internalModelData = std::move(internalModelData);

    auto retVal = this->postprocess(result);
    *retVal = static_cast<ResultBase&>(result);
    return retVal;
}

std::vector<std::unique_ptr<ResultBase>> ModelBase::inferBatch(
    const std::vector<std::reference_wrapper<const InputData>>& inputData) {
    auto results = std::vector<std::unique_ptr<ResultBase>>(inputData.size());
    auto setter = TmpCallbackSetter(
        this,
        [&](std::unique_ptr<ResultBase> result, const ov::AnyMap& callback_args) {
            size_t id = callback_args.find("id")->second.as<size_t>();
            results[id] = std::move(result);
        },
        lastCallback);
    size_t req_id = 0;
    for (const auto& data : inputData) {
        inferAsync(data, {{"id", req_id++}});
    }
    awaitAll();
    return results;
}

std::vector<std::unique_ptr<ResultBase>> ModelBase::inferBatch(const std::vector<InputData>& inputData) {
    std::vector<std::reference_wrapper<const InputData>> inputRefData;
    inputRefData.reserve(inputData.size());
    for (const auto& item : inputData) {
        inputRefData.push_back(item);
    }
    return inferBatch(inputRefData);
}

void ModelBase::inferAsync(const InputData& inputData, const ov::AnyMap& callback_args) {
    InferenceInput inputs;
    auto internalModelData = this->preprocess(inputData, inputs);
    auto callback_args_ptr = std::make_shared<ov::AnyMap>(callback_args);
    (*callback_args_ptr)["internalModelData"] = std::move(internalModelData);
    inferenceAdapter->inferAsync(inputs, callback_args_ptr);
}

bool ModelBase::isReady() {
    return inferenceAdapter->isReady();
}
void ModelBase::awaitAll() {
    inferenceAdapter->awaitAll();
}
void ModelBase::awaitAny() {
    inferenceAdapter->awaitAny();
}
void ModelBase::setCallback(
    std::function<void(std::unique_ptr<ResultBase>, const ov::AnyMap& callback_args)> callback) {
    lastCallback = callback;
    inferenceAdapter->setCallback([this, callback](ov::InferRequest request, CallbackData args) {
        InferenceResult result;

        InferenceOutput output;
        for (const auto& item : this->getInferenceAdapter()->getOutputNames()) {
            output.emplace(item, request.get_tensor(item));
        }

        result.outputsData = output;
        auto model_data_iter = args->find("internalModelData");
        if (model_data_iter != args->end()) {
            result.internalModelData = std::move(model_data_iter->second.as<std::shared_ptr<InternalModelData>>());
        }
        auto retVal = this->postprocess(result);
        *retVal = static_cast<ResultBase&>(result);
        callback(std::move(retVal), args ? *args : ov::AnyMap());
    });
}

size_t ModelBase::getNumAsyncExecutors() const {
    return inferenceAdapter->getNumAsyncExecutors();
}

std::shared_ptr<ov::Model> ModelBase::getModel() {
    if (!model) {
        throw std::runtime_error(std::string("ov::Model is not accessible for the current model adapter: ") +
                                 typeid(inferenceAdapter).name());
    }

    updateModelInfo();
    return model;
}

std::shared_ptr<InferenceAdapter> ModelBase::getInferenceAdapter() {
    if (!inferenceAdapter) {
        throw std::runtime_error(std::string("Model wasn't loaded"));
    }

    return inferenceAdapter;
}
