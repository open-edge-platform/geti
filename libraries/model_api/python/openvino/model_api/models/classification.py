"""
 Copyright (c) 2021-2023 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import json

import numpy as np
from openvino.preprocess import PrePostProcessor
from openvino.runtime import Model, Type
from openvino.runtime import opset10 as opset

from .image_model import ImageModel
from .types import BooleanValue, ListValue, NumericalValue, StringValue
from .utils import ClassificationResult


class ClassificationModel(ImageModel):
    __model__ = "Classification"

    def __init__(self, inference_adapter, configuration=dict(), preload=False):
        super().__init__(inference_adapter, configuration, preload=False)
        self._check_io_number(1, (1, 2, 3, 4, 5))
        if self.path_to_labels:
            self.labels = self._load_labels(self.path_to_labels)
        if 1 == len(self.outputs):
            self._verify_signle_output()

        self.raw_scores_name = _raw_scores_name
        if self.hierarchical:
            self.embedded_processing = True
            self.out_layer_names = _get_non_xai_names(self.outputs.keys())
            _append_xai_names(self.outputs.keys(), self.out_layer_names)
            if not self.hierarchical_config:
                self.raise_error("Hierarchical classification config is empty.")
            self.raw_scores_name = self.out_layer_names[0]
            self.hierarchical_info = json.loads(self.hierarchical_config)
            self.labels_resolver = GreedyLabelsResolver(self.hierarchical_info)
            if preload:
                self.load()
            return

        if self.multilabel:
            self.embedded_processing = True
            self.out_layer_names = _get_non_xai_names(self.outputs.keys())
            _append_xai_names(self.outputs.keys(), self.out_layer_names)
            self.raw_scores_name = self.out_layer_names[0]
            if preload:
                self.load()
            return

        try:
            addOrFindSoftmaxAndTopkOutputs(
                self.inference_adapter, self.topk, self.output_raw_scores
            )
            self.embedded_topk = True
            self.out_layer_names = ["indices", "scores"]
            if self.output_raw_scores:
                self.out_layer_names.append(self.raw_scores_name)
        except (RuntimeError, AttributeError):
            self.embedded_topk = False
            self.out_layer_names = _get_non_xai_names(self.outputs.keys())
            self.raw_scores_name = self.out_layer_names[0]

        self.embedded_processing = True

        _append_xai_names(self.outputs.keys(), self.out_layer_names)
        if preload:
            self.load()

    def _load_labels(self, labels_file):
        with open(labels_file, "r") as f:
            labels = []
            for s in f:
                begin_idx = s.find(" ")
                if begin_idx == -1:
                    self.raise_error("The labels file has incorrect format.")
                end_idx = s.find(",")
                labels.append(s[(begin_idx + 1) : end_idx])
        return labels

    def _verify_signle_output(self):
        layer_name = next(iter(self.outputs))
        layer_shape = self.outputs[layer_name].shape

        if len(layer_shape) != 2 and len(layer_shape) != 4:
            self.raise_error(
                "The Classification model wrapper supports topologies only with 2D or 4D output"
            )
        if len(layer_shape) == 4 and (layer_shape[2] != 1 or layer_shape[3] != 1):
            self.raise_error(
                "The Classification model wrapper supports topologies only with 4D "
                "output which has last two dimensions of size 1"
            )
        if self.labels:
            if layer_shape[1] == len(self.labels) + 1:
                self.labels.insert(0, "other")
                self.logger.warning("\tInserted 'other' label as first.")
            if layer_shape[1] > len(self.labels):
                self.raise_error(
                    "Model's number of classes must be greater then "
                    "number of parsed labels ({}, {})".format(
                        layer_shape[1], len(self.labels)
                    )
                )

    @classmethod
    def parameters(cls):
        parameters = super().parameters()
        parameters.update(
            {
                "topk": NumericalValue(
                    value_type=int,
                    default_value=1,
                    min=1,
                    description="Number of most likely labels",
                ),
                "labels": ListValue(description="List of class labels"),
                "path_to_labels": StringValue(
                    description="Path to file with labels. Overrides the labels, if they sets via 'labels' parameter"
                ),
                "multilabel": BooleanValue(
                    default_value=False, description="Predict a set of labels per image"
                ),
                "hierarchical": BooleanValue(
                    default_value=False,
                    description="Predict a hierarchy if labels per image",
                ),
                "hierarchical_config": StringValue(
                    default_value="",
                    description="Extra config for decoding hierarchical predicitons",
                ),
                "confidence_threshold": NumericalValue(
                    default_value=0.5, description="Predict a set of labels per image"
                ),
                "output_raw_scores": BooleanValue(
                    default_value=False,
                    description="Output all scores for multiclass classificaiton",
                ),
            }
        )
        return parameters

    def postprocess(self, outputs, meta):
        if self.multilabel:
            result = self.get_multilabel_predictions(
                outputs[self.out_layer_names[0]].squeeze()
            )
        elif self.hierarchical:
            result = self.get_hierarchical_predictions(
                outputs[self.out_layer_names[0]].squeeze()
            )
        else:
            result = self.get_multiclass_predictions(outputs)

        raw_scores = np.ndarray(0)
        if self.output_raw_scores:
            raw_scores = self.get_all_probs(outputs[self.raw_scores_name])

        return ClassificationResult(
            result,
            outputs.get(_saliency_map_name, np.ndarray(0)),
            outputs.get(_feature_vector_name, np.ndarray(0)),
            raw_scores,
        )

    def get_all_probs(self, logits: np.ndarray):
        if self.multilabel:
            probs = sigmoid_numpy(logits.reshape(-1))
        elif self.hierarchical:
            logits = logits.reshape(-1)
            probs = np.copy(logits)
            cls_heads_info = self.hierarchical_info["cls_heads_info"]
            for i in range(cls_heads_info["num_multiclass_heads"]):
                logits_begin, logits_end = cls_heads_info["head_idx_to_logits_range"][
                    str(i)
                ]
                probs[logits_begin:logits_end] = softmax_numpy(
                    logits[logits_begin:logits_end]
                )

            if cls_heads_info["num_multilabel_classes"]:
                logits_begin = cls_heads_info["num_single_label_classes"]
                probs[logits_begin:] = sigmoid_numpy(logits[logits_begin:])
        else:
            if self.embedded_topk:
                probs = logits.reshape(-1)
            else:
                probs = softmax_numpy(logits.reshape(-1))
        return probs

    def get_hierarchical_predictions(self, logits: np.ndarray):
        predicted_labels = []
        predicted_scores = []
        cls_heads_info = self.hierarchical_info["cls_heads_info"]
        for i in range(cls_heads_info["num_multiclass_heads"]):
            logits_begin, logits_end = cls_heads_info["head_idx_to_logits_range"][
                str(i)
            ]
            head_logits = logits[logits_begin:logits_end]
            head_logits = softmax_numpy(head_logits)
            j = np.argmax(head_logits)
            label_str = cls_heads_info["all_groups"][i][j]
            predicted_labels.append(label_str)
            predicted_scores.append(head_logits[j])

        if cls_heads_info["num_multilabel_classes"]:
            logits_begin = cls_heads_info["num_single_label_classes"]
            head_logits = logits[logits_begin:]
            head_logits = sigmoid_numpy(head_logits)

            for i in range(head_logits.shape[0]):
                if head_logits[i] > self.confidence_threshold:
                    label_str = cls_heads_info["all_groups"][
                        cls_heads_info["num_multiclass_heads"] + i
                    ][0]
                    predicted_labels.append(label_str)
                    predicted_scores.append(head_logits[i])

        predictions = zip(predicted_labels, predicted_scores)
        return self.labels_resolver.resolve_labels(predictions)

    def get_multilabel_predictions(self, logits: np.ndarray):
        logits = sigmoid_numpy(logits)
        scores = []
        indices = []
        for i in range(logits.shape[0]):
            if logits[i] > self.confidence_threshold:
                indices.append(i)
                scores.append(logits[i])
        labels = [self.labels[i] if self.labels else "" for i in indices]

        return list(zip(indices, labels, scores))

    def get_multiclass_predictions(self, outputs):
        if self.embedded_topk:
            indicesTensor = outputs[self.out_layer_names[0]][0]
            scoresTensor = outputs[self.out_layer_names[1]][0]
            labels = [self.labels[i] if self.labels else "" for i in indicesTensor]
        else:
            scoresTensor = softmax_numpy(outputs[self.out_layer_names[0]][0])
            indicesTensor = [np.argmax(scoresTensor)]
            labels = [self.labels[i] if self.labels else "" for i in indicesTensor]
        return list(zip(indicesTensor, labels, scoresTensor))


def addOrFindSoftmaxAndTopkOutputs(inference_adapter, topk, output_raw_scores):
    softmaxNode = None
    for i in range(len(inference_adapter.model.outputs)):
        output_node = (
            inference_adapter.model.get_output_op(i)
            .input(0)
            .get_source_output()
            .get_node()
        )
        if "Softmax" == output_node.get_type_name():
            softmaxNode = output_node
        elif "TopK" == output_node.get_type_name():
            return

    if softmaxNode is None:
        logitsNode = (
            inference_adapter.model.get_output_op(0)
            .input(0)
            .get_source_output()
            .get_node()
        )
        softmaxNode = opset.softmax(logitsNode.output(0), 1)
    k = opset.constant(topk, np.int32)
    topkNode = opset.topk(softmaxNode, k, 1, "max", "value")

    indices = topkNode.output(0)
    scores = topkNode.output(1)
    results_descr = [indices, scores]
    if output_raw_scores:
        raw_scores = softmaxNode.output(0)
        results_descr.append(raw_scores)
    for output in inference_adapter.model.outputs:
        if (
            _saliency_map_name in output.get_names()
            or _feature_vector_name in output.get_names()
        ):
            results_descr.append(output)

    source_rt_info = inference_adapter.get_model().get_rt_info()
    inference_adapter.model = Model(
        results_descr,
        inference_adapter.model.get_parameters(),
        "classification",
    )

    if "model_info" in source_rt_info:
        source_rt_info = source_rt_info["model_info"]
        for k in source_rt_info:
            inference_adapter.model.set_rt_info(source_rt_info[k], ["model_info", k])

    # manually set output tensors name for created topK node
    inference_adapter.model.outputs[0].tensor.set_names({"scores"})
    inference_adapter.model.outputs[1].tensor.set_names({"indices"})
    if output_raw_scores:
        inference_adapter.model.outputs[2].tensor.set_names({_raw_scores_name})

    # set output precisions
    ppp = PrePostProcessor(inference_adapter.model)
    ppp.output("indices").tensor().set_element_type(Type.i32)
    ppp.output("scores").tensor().set_element_type(Type.f32)
    if output_raw_scores:
        ppp.output(_raw_scores_name).tensor().set_element_type(Type.f32)
    inference_adapter.model = ppp.build()


def sigmoid_numpy(x: np.ndarray):
    return 1.0 / (1.0 + np.exp(-x))


def softmax_numpy(x: np.ndarray, eps: float = 1e-9):
    x = np.exp(x - np.max(x))
    return x / (np.sum(x) + eps)


class GreedyLabelsResolver:
    def __init__(self, hierarchical_config) -> None:
        self.label_to_idx = hierarchical_config["cls_heads_info"]["label_to_idx"]
        self.label_relations = hierarchical_config["label_tree_edges"]
        self.label_groups = hierarchical_config["cls_heads_info"]["all_groups"]

    def _get_parent(self, label):
        for child, parent in self.label_relations:
            if label == child:
                return parent

        return None

    def resolve_labels(self, predictions):
        """Resolves hierarchical labels and exclusivity based on a list of ScoredLabels (labels with probability).
        The following two steps are taken:
        - select the most likely label from each label group
        - add it and it's predecessors if they are also most likely labels (greedy approach).
        """

        def get_predecessors(lbl, candidates):
            """Returns all the predecessors of the input label or an empty list if one of the predecessors is not a candidate."""
            predecessors = []
            last_parent = self._get_parent(lbl)
            if last_parent is None:
                return [lbl]

            while last_parent is not None:
                if last_parent not in candidates:
                    return []
                predecessors.append(last_parent)
                last_parent = self._get_parent(last_parent)

            if predecessors:
                predecessors.append(lbl)
            return predecessors

        label_to_prob = {lbl: 0.0 for lbl in self.label_to_idx.keys()}
        for lbl, score in predictions:
            label_to_prob[lbl] = score

        candidates = []
        for g in self.label_groups:
            if len(g) == 1:
                candidates.append(g[0])
            else:
                max_prob = 0.0
                max_label = None
                for lbl in g:
                    if label_to_prob[lbl] > max_prob:
                        max_prob = label_to_prob[lbl]
                        max_label = lbl
                if max_label is not None:
                    candidates.append(max_label)

        output_labels = []
        for lbl in candidates:
            if lbl in output_labels:
                continue
            labels_to_add = get_predecessors(lbl, candidates)
            for new_lbl in labels_to_add:
                if new_lbl not in output_labels:
                    output_labels.append(new_lbl)

        output_predictions = [
            (self.label_to_idx[lbl], lbl, label_to_prob[lbl]) for lbl in output_labels
        ]
        return output_predictions


_saliency_map_name = "saliency_map"
_feature_vector_name = "feature_vector"
_raw_scores_name = "raw_scores"


def _get_non_xai_names(output_names):
    return [
        output_name
        for output_name in output_names
        if _saliency_map_name != output_name or _feature_vector_name == output_name
    ]


def _append_xai_names(outputs, output_names):
    if _saliency_map_name in outputs:
        output_names.append(_saliency_map_name)
    if _feature_vector_name in outputs:
        output_names.append(_feature_vector_name)
