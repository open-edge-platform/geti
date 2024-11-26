#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import numpy as np

from .detection_model import DetectionModel
from .result_types import DetectionResult

BBOX_AREA_THRESHOLD = 1.0
SALIENCY_MAP_NAME = "saliency_map"
FEATURE_VECTOR_NAME = "feature_vector"


def find_layer_by_name(name, layers):
    suitable_layers = [layer_name for layer_name in layers if name in layer_name]
    if not suitable_layers:
        msg = f'Suitable layer for "{name}" output is not found'
        raise ValueError(msg)

    if len(suitable_layers) > 1:
        msg = f'More than 1 layer matched to "{name}" output'
        raise ValueError(msg)

    return suitable_layers[0]


class SingleOutputParser:
    def __init__(self, all_outputs):
        if len(all_outputs) != 1:
            msg = "Network must have only one output."
            raise ValueError(msg)
        self.output_name, output_data = next(iter(all_outputs.items()))
        last_dim = output_data.shape[-1]
        if last_dim != 7:
            msg = f"The last dimension of the output blob must be equal to 7, got {last_dim} instead."
            raise ValueError(msg)

    def __call__(self, outputs) -> DetectionResult:
        """Parse model outputs.

        Args:
            outputs (dict): Model outputs wrapped in dict.

        Returns:
            DetectionResult: Parsed model outputs.
        """
        bboxes = []
        scores = []
        labels = []
        for _, label, score, xmin, ymin, xmax, ymax in outputs[self.output_name][0][0]:
            bboxes.append((xmin, ymin, xmax, ymax))
            scores.append(score)
            labels.append(label)
        bboxes = np.array(bboxes)
        scores = np.array(scores)
        labels = np.array(labels).astype(np.int32)
        return DetectionResult(
            bboxes=bboxes,
            labels=labels,
            scores=scores,
        )


class MultipleOutputParser:
    def __init__(
        self,
        layers,
        bboxes_layer="bboxes",
        scores_layer="scores",
        labels_layer="labels",
    ):
        self.labels_layer = find_layer_by_name(labels_layer, layers)
        self.scores_layer = find_layer_by_name(scores_layer, layers)
        self.bboxes_layer = find_layer_by_name(bboxes_layer, layers)

    def __call__(self, outputs) -> DetectionResult:
        """Parse model outputs.

        Args:
            outputs (dict): Model outputs wrapped in dict.

        Returns:
            DetectionResult: Parsed model outputs.
        """
        bboxes = np.array(outputs[self.bboxes_layer][0])
        scores = np.array(outputs[self.scores_layer][0])
        labels = np.array(outputs[self.labels_layer][0])
        return DetectionResult(bboxes, scores, labels)


class BoxesLabelsParser:
    def __init__(self, layers, input_size, labels_layer="labels", default_label=0):
        try:
            self.labels_layer = find_layer_by_name(labels_layer, layers)
        except ValueError:
            self.labels_layer = None
            self.default_label = default_label

        self.bboxes_layer = self.find_layer_bboxes_output(layers)
        self.input_size = input_size

    @staticmethod
    def find_layer_bboxes_output(layers):
        filter_outputs = [
            name
            for name, data in layers.items()
            if (len(data.shape) == 2 or len(data.shape) == 3) and data.shape[-1] == 5
        ]
        if not filter_outputs:
            msg = "Suitable output with bounding boxes is not found"
            raise ValueError(msg)
        if len(filter_outputs) > 1:
            msg = "More than 1 candidate for output with bounding boxes."
            raise ValueError(msg)
        return filter_outputs[0]

    def __call__(self, outputs) -> DetectionResult:
        """Parse model outputs.

        Note: Bounding boxes layer from outputs are expected to be in format [xmin, ymin, xmax, ymax, score].

        Args:
            outputs (dict): Model outputs wrapped in dict.

        Returns:
            DetectionResult: Parsed model outputs.
        """
        bboxes = outputs[self.bboxes_layer]
        bboxes = bboxes.squeeze(0)
        scores = bboxes[:, 4]
        bboxes = bboxes[:, :4]
        bboxes[:, 0::2] /= self.input_size[0]
        bboxes[:, 1::2] /= self.input_size[1]
        if self.labels_layer:
            labels = outputs[self.labels_layer]
        else:
            labels = np.full(len(bboxes), self.default_label, dtype=bboxes.dtype)
        labels = labels.squeeze(0)

        return DetectionResult(
            bboxes=bboxes,
            labels=labels,
            scores=scores,
        )


class SSD(DetectionModel):
    __model__ = "SSD"

    def __init__(self, inference_adapter, configuration: dict = {}, preload=False):
        super().__init__(inference_adapter, configuration, preload)
        self.image_info_blob_name = self.image_info_blob_names[0] if len(self.image_info_blob_names) == 1 else None
        self.output_parser = self._get_output_parser(self.image_blob_name)

    def preprocess(self, inputs):
        dict_inputs, meta = super().preprocess(inputs)
        if self.image_info_blob_name:
            dict_inputs[self.image_info_blob_name] = np.array([[self.h, self.w, 1]])
        return dict_inputs, meta

    def postprocess(self, outputs, meta) -> DetectionResult:
        detections = self._parse_outputs(outputs)
        self._resize_detections(detections, meta)
        self._filter_detections(detections, BBOX_AREA_THRESHOLD)
        self._add_label_names(detections)
        detections.saliency_map = outputs.get(SALIENCY_MAP_NAME, np.ndarray(0))
        detections.feature_vector = outputs.get(FEATURE_VECTOR_NAME, np.ndarray(0))
        return detections

    def _get_output_parser(
        self,
        image_blob_name,
        bboxes="bboxes",
        labels="labels",
        scores="scores",
    ):
        try:
            parser = SingleOutputParser(self.outputs)
            self.logger.debug("\tUsing SSD model with single output parser")
            return parser
        except ValueError:
            pass

        try:
            parser = MultipleOutputParser(self.outputs, bboxes, scores, labels)
            self.logger.debug("\tUsing SSD model with multiple output parser")
            return parser
        except ValueError:
            pass

        try:
            parser = BoxesLabelsParser(self.outputs, (self.w, self.h))
            self.logger.debug('\tUsing SSD model with "boxes-labels" output parser')
            return parser
        except ValueError:
            pass
        msg = "Unsupported model outputs"
        raise ValueError(msg)

    def _parse_outputs(self, outputs):
        return self.output_parser(outputs)
