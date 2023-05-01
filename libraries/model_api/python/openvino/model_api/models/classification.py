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

import numpy as np
from openvino.preprocess import PrePostProcessor
from openvino.runtime import Model, Type
from openvino.runtime import opset10 as opset

from .image_model import ImageModel
from .types import BooleanValue, ListValue, NumericalValue, StringValue


class ClassificationModel(ImageModel):
    __model__ = "Classification"

    def __init__(self, inference_adapter, configuration=None, preload=False):
        super().__init__(inference_adapter, configuration, preload=False)
        self._check_io_number(1, (1, 2))
        if self.path_to_labels:
            self.labels = self._load_labels(self.path_to_labels)
        self.out_layer_names = [self._get_output()]
        if self.multilabel:
            self.embedded_processing = True
            if preload:
                self.load()
            return

        addOrFindSoftmaxAndTopkOutputs(self.inference_adapter, self.topk)
        self.embedded_processing = True

        self.out_layer_names = ["indices", "scores"]
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

    def _get_output(self):
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
        return layer_name

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
            }
        )
        return parameters

    def postprocess(self, outputs, meta):
        print(self.multilabel)
        if self.multilabel:
            return self.get_multilabel_predictions(
                outputs[self.out_layer_names[0]].squeeze()
            )
        return self.get_multiclass_predictions(outputs)

    def get_multilabel_predictions(self, logits: np.ndarray):
        logits = sigmoid_numpy(logits)
        scores = []
        indices = []
        for i in range(logits.shape[0]):
            if logits[i] > 0.5:
                indices.append(i)
                scores.append(logits[i])
        labels = [self.labels[i] if self.labels else "" for i in indices]

        return list(zip(indices, labels, scores))

    def get_multiclass_predictions(self, outputs):
        indicesTensor = outputs[self.out_layer_names[0]][0]
        scoresTensor = outputs[self.out_layer_names[1]][0]
        labels = [self.labels[i] if self.labels else "" for i in indicesTensor]
        return list(zip(indicesTensor, labels, scoresTensor))


def addOrFindSoftmaxAndTopkOutputs(inference_adapter, topk):
    nodes = inference_adapter.model.get_ops()
    softmaxNode = None
    for op in nodes:
        if "Softmax" == op.get_type_name():
            softmaxNode = op
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
    inference_adapter.model = Model(
        [indices, scores], inference_adapter.model.get_parameters(), "classification"
    )

    # manually set output tensors name for created topK node
    inference_adapter.model.outputs[0].tensor.set_names({"scores"})
    inference_adapter.model.outputs[1].tensor.set_names({"indices"})

    # set output precisions
    ppp = PrePostProcessor(inference_adapter.model)
    ppp.output("indices").tensor().set_element_type(Type.i32)
    ppp.output("scores").tensor().set_element_type(Type.f32)
    inference_adapter.model = ppp.build()


def sigmoid_numpy(x: np.ndarray):
    return 1.0 / (1.0 + np.exp(-x))
