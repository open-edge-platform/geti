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

#include <memory>
#include <string>
#include <vector>
#include <map>

#include "models/image_model.h"

namespace ov {
class Model;
}  // namespace ov
struct InferenceResult;
struct ClassificationResult;
struct ResultBase;
struct ImageInputData;

struct HierarchicalConfig {
    std::map<std::string, int> label_to_idx;
    std::vector<std::pair<std::string, std::string>> label_tree_edges;
    std::vector<std::vector<std::string>> all_groups;
    std::map<size_t, std::pair<size_t,size_t>> head_idx_to_logits_range;
    size_t num_multiclass_heads;
    size_t num_multilabel_heads;
    size_t num_single_label_classes;

    HierarchicalConfig() = default;
    HierarchicalConfig(const std::string&);
};

class GreedyLabelsResolver {
    public:
        GreedyLabelsResolver() = default;
        GreedyLabelsResolver(const HierarchicalConfig&);

        std::pair<std::vector<std::string>, std::vector<float>> resolve_labels(const std::vector<std::reference_wrapper<std::string>>& labels,
                                                                               const std::vector<float>& scores);
    protected:
        std::map<std::string, int> label_to_idx;
        std::vector<std::pair<std::string, std::string>> label_relations;
        std::vector<std::vector<std::string>> label_groups;

        std::string get_parent(const std::string& label);
        std::vector<std::string> get_predecessors(const std::string& label, const std::vector<std::string>& candidates);
};

class ClassificationModel : public ImageModel {
public:
    ClassificationModel(std::shared_ptr<ov::Model>& model, const ov::AnyMap& configuration);
    ClassificationModel(std::shared_ptr<InferenceAdapter>& adapter);

    static std::unique_ptr<ClassificationModel> create_model(const std::string& modelFile, const ov::AnyMap& configuration = {}, bool preload = true, const std::string& device = "AUTO");
    static std::unique_ptr<ClassificationModel> create_model(std::shared_ptr<InferenceAdapter>& adapter);

    std::unique_ptr<ResultBase> postprocess(InferenceResult& infResult) override;

    virtual std::unique_ptr<ClassificationResult> infer(const ImageInputData& inputData);
    static std::string ModelType;

protected:
    size_t topk = 1;
    bool multilabel = false;
    bool hierarchical = false;
    bool output_raw_scores = false;
    float confidence_threshold = 0.5f;
    std::string hierarchical_json_config;
    HierarchicalConfig hierarchical_config;
    GreedyLabelsResolver resolver;

    void prepareInputsOutputs(std::shared_ptr<ov::Model>& model) override;
    void updateModelInfo() override;
    std::unique_ptr<ResultBase> get_multilabel_predictions(InferenceResult& infResult);
    std::unique_ptr<ResultBase> get_multiclass_predictions(InferenceResult& infResult);
    std::unique_ptr<ResultBase> get_hierarchical_predictions(InferenceResult& infResult);
};
