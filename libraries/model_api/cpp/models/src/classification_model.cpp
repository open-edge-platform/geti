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

#include "models/classification_model.h"

#include <algorithm>
#include <fstream>
#include <iterator>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include <openvino/op/softmax.hpp>
#include <openvino/op/topk.hpp>
#include <openvino/openvino.hpp>

#include <utils/slog.hpp>

#include "models/results.h"
#include "models/input_data.h"

std::string ClassificationModel::ModelType = "Classification";

namespace {
float sigmoid(float x) {
    return 1.0f / (1.0f + exp(-x));
}

void addOrFindSoftmaxAndTopkOutputs(std::shared_ptr<ov::Model>& model, size_t topk) {
    auto nodes = model->get_ops();
    auto softmaxNodeIt = std::find_if(std::begin(nodes), std::end(nodes), [](const std::shared_ptr<ov::Node>& op) {
        return std::string(op->get_type_name()) == "Softmax"; // TODO: it will not work for Vision Transformers, for example
    });

    std::shared_ptr<ov::Node> softmaxNode;
    if (softmaxNodeIt == nodes.end()) {
        auto logitsNode = model->get_output_op(0)->input(0).get_source_output().get_node();
        softmaxNode = std::make_shared<ov::op::v1::Softmax>(logitsNode->output(0), 1);
    } else {
        softmaxNode = *softmaxNodeIt;
    }
    const auto k = std::make_shared<ov::op::v0::Constant>(ov::element::i32, ov::Shape{}, std::vector<size_t>{topk});
    std::shared_ptr<ov::Node> topkNode = std::make_shared<ov::op::v3::TopK>(softmaxNode,
                                                                            k,
                                                                            1,
                                                                            ov::op::v3::TopK::Mode::MAX,
                                                                            ov::op::v3::TopK::SortType::SORT_VALUES);

    auto indices = std::make_shared<ov::op::v0::Result>(topkNode->output(0));
    auto scores = std::make_shared<ov::op::v0::Result>(topkNode->output(1));
    model = std::make_shared<ov::Model>(ov::ResultVector{scores, indices}, model->get_parameters(), "classification");

    // manually set output tensors name for created topK node
    model->outputs()[0].set_names({"indices"});
    model->outputs()[1].set_names({"scores"});

    // set output precisions
    ov::preprocess::PrePostProcessor ppp = ov::preprocess::PrePostProcessor(model);
    ppp.output("indices").tensor().set_element_type(ov::element::i32);
    ppp.output("scores").tensor().set_element_type(ov::element::f32);
    model = ppp.build();
}
}

ClassificationModel::ClassificationModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration)
    : ImageModel(model, configuration) {
    auto topk_iter = configuration.find("topk");
    if (topk_iter == configuration.end()) {
        if (model->has_rt_info("model_info", "topk")) {
            topk = stoi(model->get_rt_info<std::string>("model_info", "topk"));
        }
    } else {
        topk = topk_iter->second.as<size_t>();
    }
    auto multilabel_iter = configuration.find("multilabel");
    if (multilabel_iter == configuration.end()) {
        if (model->has_rt_info("model_info", "multilabel")) {
            std::string val = model->get_rt_info<std::string>("model_info", "multilabel");
            multilabel = val == "True" || val == "YES";
        }
    } else {
        std::string val = multilabel_iter->second.as<std::string>();
        multilabel = val == "True" || val == "YES";
    }
}

ClassificationModel::ClassificationModel(std::shared_ptr<InferenceAdapter>& adapter)
    : ImageModel(adapter) {
    auto configuration = adapter->getModelConfig();
    auto topk_iter = configuration.find("topk");
    if (topk_iter != configuration.end()) {
        topk = topk_iter->second.as<size_t>();
    }
    auto multilabel_iter = configuration.find("multilabel");
    if (multilabel_iter != configuration.end()) {
        std::string val = multilabel_iter->second.as<std::string>();
        multilabel = val == "True" || val == "YES";
    }
}

void ClassificationModel::updateModelInfo() {
    ImageModel::updateModelInfo();

    model->set_rt_info(ClassificationModel::ModelType, "model_info", "model_type");
    model->set_rt_info(topk, "model_info", "topk");
    if (multilabel) {
        model->set_rt_info("True", "model_info", "multilabel");
    } else {
        model->set_rt_info("False", "model_info", "multilabel");
    }
}

std::unique_ptr<ClassificationModel> ClassificationModel::create_model(const std::string& modelFile, const ov::AnyMap& configuration, bool preload) {
    auto core = ov::Core();
    std::shared_ptr<ov::Model> model = core.read_model(modelFile);

    // Check model_type in the rt_info, ignore configuration
    std::string model_type = ClassificationModel::ModelType;
    try {
        if (model->has_rt_info("model_info", "model_type")) {
            model_type = model->get_rt_info<std::string>("model_info", "model_type");
        }
    } catch (const std::exception& e) {
        slog::warn << "Model type is not specified in the rt_info, use default model type: " << model_type << slog::endl;
    }

    if (model_type != ClassificationModel::ModelType) {
        throw ov::Exception("Incorrect or unsupported model_type is provided in the model_info section: " + model_type);
    }

    std::unique_ptr<ClassificationModel> classifier{new ClassificationModel(model, configuration)};
    classifier->prepare();
    if (preload) {
        classifier->load(core);
    }
    return classifier;
}

std::unique_ptr<ClassificationModel> ClassificationModel::create_model(std::shared_ptr<InferenceAdapter>& adapter) {
    auto configuration = adapter->getModelConfig();
    auto model_type_iter = configuration.find("model_type");
    std::string model_type = ClassificationModel::ModelType;
    if (model_type_iter != configuration.end()) {
        model_type = model_type_iter->second.as<std::string>();
    }

    if (model_type != ClassificationModel::ModelType) {
        throw ov::Exception("Incorrect or unsupported model_type is provided: " + model_type);
    }

    std::unique_ptr<ClassificationModel> classifier{new ClassificationModel(adapter)};
    return classifier;
}

std::unique_ptr<ResultBase> ClassificationModel::postprocess(InferenceResult& infResult) {
    if (multilabel) {
        return get_multilabel_predictions(infResult);
    }
    return get_multiclass_predictions(infResult);
}

std::unique_ptr<ResultBase> ClassificationModel::get_multilabel_predictions(InferenceResult& infResult) {
    const ov::Tensor& logitsTensor = infResult.outputsData.find(outputNames[0])->second;
    const float* logitsPtr = logitsTensor.data<float>();

    ClassificationResult* result = new ClassificationResult(infResult.frameId, infResult.metaData);
    auto retVal = std::unique_ptr<ResultBase>(result);

    result->topLabels.reserve(labels.size());
    for (size_t i = 0; i < labels.size(); ++i) {
        float score = sigmoid(logitsPtr[i]);
        if (score > 0.5f) {
            result->topLabels.emplace_back(i, labels[i], score);
        }
    }

    return retVal;
}

std::unique_ptr<ResultBase> ClassificationModel::get_multiclass_predictions(InferenceResult& infResult) {
    const ov::Tensor& indicesTensor = infResult.outputsData.find(outputNames[0])->second;
    const int* indicesPtr = indicesTensor.data<int>();
    const ov::Tensor& scoresTensor = infResult.outputsData.find(outputNames[1])->second;
    const float* scoresPtr = scoresTensor.data<float>();

    ClassificationResult* result = new ClassificationResult(infResult.frameId, infResult.metaData);
    auto retVal = std::unique_ptr<ResultBase>(result);

    result->topLabels.reserve(scoresTensor.get_size());
    for (size_t i = 0; i < scoresTensor.get_size(); ++i) {
        int ind = indicesPtr[i];
        if (ind < 0 || ind >= static_cast<int>(labels.size())) {
            throw std::runtime_error("Invalid index for the class label is found during postprocessing");
        }
        result->topLabels.emplace_back(ind, labels[ind], scoresPtr[i]);
    }

    return retVal;
}

void ClassificationModel::prepareInputsOutputs(std::shared_ptr<ov::Model>& model) {
    // --------------------------- Configure input & output -------------------------------------------------
    // --------------------------- Prepare input  ------------------------------------------------------
    if (model->inputs().size() != 1) {
        throw std::logic_error("Classification model wrapper supports topologies with only 1 input");
    }
    const auto& input = model->input();
    inputNames.push_back(input.get_any_name());

    const ov::Shape& inputShape = input.get_partial_shape().get_max_shape();
    const ov::Layout& inputLayout = getInputLayout(input);

    if (!embedded_processing) {
        model = ImageModel::embedProcessing(model,
                                        inputNames[0],
                                        inputLayout,
                                        resizeMode,
                                        interpolationMode,
                                        ov::Shape{inputShape[ov::layout::width_idx(inputLayout)],
                                                  inputShape[ov::layout::height_idx(inputLayout)]});

        ov::preprocess::PrePostProcessor ppp = ov::preprocess::PrePostProcessor(model);
        ppp.output().tensor().set_element_type(ov::element::f32);
        model = ppp.build();
        useAutoResize = true; // temporal solution for classification
    }

    // --------------------------- Prepare output  -----------------------------------------------------
    if (model->outputs().size() != 1 && model->outputs().size() != 2) {
        throw std::logic_error("Classification model wrapper supports topologies with 1 or 2 outputs");
    }

    if (model->outputs().size() == 1) {
        const ov::Shape& outputShape = model->output().get_partial_shape().get_max_shape();
        if (outputShape.size() != 2 && outputShape.size() != 4) {
            throw std::logic_error("Classification model wrapper supports topologies only with"
                                " 2-dimensional or 4-dimensional output");
        }

        const ov::Layout outputLayout("NCHW");
        if (outputShape.size() == 4 && (outputShape[ov::layout::height_idx(outputLayout)] != 1 ||
                                        outputShape[ov::layout::width_idx(outputLayout)] != 1)) {
            throw std::logic_error("Classification model wrapper supports topologies only"
                                " with 4-dimensional output which has last two dimensions of size 1");
        }

        size_t classesNum = outputShape[ov::layout::channels_idx(outputLayout)];
        if (topk > classesNum) {
            throw std::logic_error("The model provides " + std::to_string(classesNum) + " classes, but " +
                                std::to_string(topk) + " labels are requested to be predicted");
        }
        if (classesNum == labels.size() + 1) {
            labels.insert(labels.begin(), "other");
            slog::warn << "Inserted 'other' label as first." << slog::endl;
        } else if (classesNum != labels.size()) {
            throw std::logic_error("Model's number of classes and parsed labels must match (" +
                                std::to_string(outputShape[1]) + " and " + std::to_string(labels.size()) + ')');
        }
    }

    if (multilabel) {
        outputNames = {model->output().get_any_name()};
        embedded_processing = true;
        return;
    }

    addOrFindSoftmaxAndTopkOutputs(model, topk);
    embedded_processing = true;

    outputNames = {"indices", "scores"};
}

std::unique_ptr<ClassificationResult> ClassificationModel::infer(const ImageInputData& inputData) {
    auto result = ModelBase::infer(static_cast<const InputData&>(inputData));
    return std::unique_ptr<ClassificationResult>(static_cast<ClassificationResult*>(result.release()));
}
