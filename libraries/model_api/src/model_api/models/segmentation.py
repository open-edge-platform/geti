#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np

from model_api.models.image_model import ImageModel
from model_api.models.parameters import ParameterRegistry
from model_api.models.result import Contour, ImageResultWithSoftPrediction
from model_api.models.utils import load_labels

if TYPE_CHECKING:
    from collections.abc import Iterable

    from model_api.adapters.inference_adapter import InferenceAdapter


def create_hard_prediction_from_soft_prediction(
    soft_prediction: np.ndarray,
    soft_threshold: float,
    blur_strength: int,
) -> np.ndarray:
    """Creates a hard prediction containing the final label index per pixel.

    Args:
        soft_prediction: Output from segmentation network. Assumes
            floating point values, between 0.0 and 1.0. Can be a
            per-class segmentation
            logits of shape (height, width, num_classes)
        soft_threshold: minimum class confidence for each pixel. The
            higher the value, the more strict the segmentation is
            (usually set to 0.5)
        blur_strength: The higher the value, the smoother the
            segmentation output will be, but less accurate

    Returns:
        Numpy array of the hard prediction
    """
    if blur_strength == -1 or soft_threshold == float("inf"):
        return np.argmax(soft_prediction, axis=2)
    soft_prediction_blurred = cv2.blur(
        soft_prediction,
        (blur_strength, blur_strength),
    )
    assert len(soft_prediction.shape) == 3
    soft_prediction_blurred[soft_prediction_blurred < soft_threshold] = 0
    return np.argmax(soft_prediction_blurred, axis=2)


class SegmentationModel(ImageModel):
    """Segmentation Model.

    Args:
        inference_adapter (InferenceAdapter): Inference adapter
        configuration (dict, optional): Configuration parameters. Defaults to {}.
        preload (bool, optional): Whether to preload the model. Defaults to False.

    Example:
        >>> from model_api.models import SegmentationModel
        >>> import cv2
        >>> model = SegmentationModel.create_model("./path_to_model.xml")
        >>> image = cv2.imread("path_to_image.jpg")
        >>> result = model.predict(image)
        ImageResultWithSoftPrediction(
            ...
        )
    """

    __model__ = "Segmentation"

    def __init__(self, inference_adapter: InferenceAdapter, configuration: dict = {}, preload: bool = False) -> None:
        super().__init__(inference_adapter, configuration, preload)
        self._check_io_number(1, (1, 2))
        if self.params.path_to_labels:
            self._labels = load_labels(self.params.path_to_labels)

        self.output_blob_name = self._get_outputs()

    def _get_outputs(self) -> str:
        out_name = ""
        for name, output in self.outputs.items():
            if _feature_vector_name not in output.names:
                if out_name:
                    self.raise_error(
                        f"only {_feature_vector_name} and 1 other output are allowed",
                    )
                else:
                    out_name = name
        if not out_name:
            self.raise_error("No output containing segmentatation found")
        layer_shape = self.outputs[out_name].shape

        if len(layer_shape) == 3:
            self.out_channels = 0
        elif len(layer_shape) == 4:
            self.out_channels = layer_shape[1]
        else:
            self.raise_error(
                f"Unexpected output layer shape {layer_shape}. Only 4D and 3D output layers are supported",
            )

        return out_name

    @classmethod
    def parameters(cls) -> dict:
        parameters = super().parameters()
        parameters.update(
            ParameterRegistry.merge(
                ParameterRegistry.LABELS,
                ParameterRegistry.SEGMENTATION_POSTPROCESS,
            ),
        )
        return parameters

    def postprocess(self, outputs: dict, meta: dict) -> ImageResultWithSoftPrediction | cv2.Mat:
        input_image_height = meta["original_shape"][0]
        input_image_width = meta["original_shape"][1]
        predictions = outputs[self.output_blob_name].squeeze()

        if self.out_channels < 2:  # assume the output is already ArgMax'ed
            soft_prediction = predictions.astype(np.uint8)
        else:
            soft_prediction = np.transpose(predictions, axes=(1, 2, 0))

        hard_prediction = create_hard_prediction_from_soft_prediction(
            soft_prediction=soft_prediction,
            soft_threshold=self.params.soft_threshold,
            blur_strength=self.params.blur_strength,
        )

        hard_prediction = cv2.resize(
            hard_prediction,
            (input_image_width, input_image_height),
            0,
            0,
            interpolation=cv2.INTER_NEAREST,
        )

        if self.params.return_soft_prediction:
            soft_prediction = cv2.resize(
                soft_prediction,
                (input_image_width, input_image_height),
                0,
                0,
                interpolation=cv2.INTER_NEAREST,
            )

            return ImageResultWithSoftPrediction(
                hard_prediction,
                soft_prediction,
                (_get_activation_map(soft_prediction) if _feature_vector_name in outputs else np.ndarray(0)),
                outputs.get(_feature_vector_name, np.ndarray(0)),
            )
        return hard_prediction

    def get_contours(
        self,
        prediction: ImageResultWithSoftPrediction,
        include_nested_contours: bool = True,
    ) -> list[Contour]:
        """Represents existing masks with contours.

        Args:
            prediction (ImageResultWithSoftPrediction): Input segmentation prediction.
            include_nested_contours (bool, optional): Enables searching for holes in masks. Defaults to True.

        Returns:
            list[Contour]: Contours found.
        """
        n_layers = prediction.soft_prediction.shape[2]

        if n_layers == 1:
            msg = "Cannot get contours from soft prediction with 1 layer"
            raise RuntimeError(msg)

        find_contours_mode = cv2.RETR_CCOMP if include_nested_contours else cv2.RETR_EXTERNAL
        combined_contours = []
        for layer_index in range(1, n_layers):  # ignoring background
            label = self.get_label_name(layer_index - 1)
            if len(prediction.soft_prediction.shape) == 3:
                current_label_soft_prediction = prediction.soft_prediction[
                    :,
                    :,
                    layer_index,
                ]
            else:
                current_label_soft_prediction = prediction.soft_prediction

            obj_group = prediction.resultImage == layer_index
            label_index_map = obj_group.astype(np.uint8) * 255

            contours, hierarchy = cv2.findContours(
                label_index_map,
                find_contours_mode,
                cv2.CHAIN_APPROX_NONE,
            )
            if len(contours):
                hierarchy = hierarchy.squeeze(axis=0)

            for i, contour in enumerate(contours):
                if hierarchy[i][3] >= 0:
                    continue

                mask = np.zeros(prediction.resultImage.shape, dtype=np.uint8)
                cv2.drawContours(mask, contours, contourIdx=i, color=1, thickness=-1)

                children = []
                next_child_idx = hierarchy[i][2]
                while next_child_idx >= 0:
                    children.append(contours[next_child_idx])
                    cv2.drawContours(mask, contours, contourIdx=next_child_idx, color=0, thickness=-1)
                    next_child_idx = hierarchy[next_child_idx][0]

                if current_label_soft_prediction.dtype != np.float32:
                    current_label_soft_prediction = current_label_soft_prediction.astype(np.float32)

                probability = cv2.mean(current_label_soft_prediction, mask)[0]
                combined_contours.append(Contour(label, probability, contour, children))

        return combined_contours


_feature_vector_name = "feature_vector"


def _get_activation_map(features: np.ndarray | Iterable | int | float) -> np.ndarray:
    """Getter activation_map functions."""
    min_soft_score = np.min(features)
    max_soft_score = np.max(features)
    factor = 255.0 / (max_soft_score - min_soft_score + 1e-12)

    float_act_map = factor * (features - min_soft_score)
    return np.round(float_act_map, out=float_act_map).astype(np.uint8)
