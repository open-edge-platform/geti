"""
 Copyright (c) 2020-2023 Intel Corporation

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

from typing import Iterable, Union

import cv2
import numpy as np

from .image_model import ImageModel
from .types import BooleanValue, ListValue, NumericalValue, StringValue
from .utils import Contour, ImageResultWithSoftPrediction, load_labels


def create_hard_prediction_from_soft_prediction(
    soft_prediction: np.ndarray, soft_threshold: float, blur_strength: int
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
    else:
        soft_prediction_blurred = cv2.blur(
            soft_prediction, (blur_strength, blur_strength)
        )
        assert len(soft_prediction.shape) == 3
        soft_prediction_blurred[soft_prediction_blurred < soft_threshold] = 0
        return np.argmax(soft_prediction_blurred, axis=2)


class SegmentationModel(ImageModel):
    __model__ = "Segmentation"

    def __init__(self, inference_adapter, configuration=dict(), preload=False):
        super().__init__(inference_adapter, configuration, preload)
        self._check_io_number(1, (1, 2))
        if self.path_to_labels:
            self.labels = load_labels(self.path_to_labels)

        self.output_blob_name = self._get_outputs()

    def _get_outputs(self):
        out_name = ""
        for name, output in self.outputs.items():
            if _feature_vector_name not in output.names:
                if out_name:
                    self.raise_error(
                        f"only {_feature_vector_name} and 1 other output are allowed"
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
                "Unexpected output layer shape {}. Only 4D and 3D output layers are supported".format(
                    layer_shape
                )
            )

        return out_name

    @classmethod
    def parameters(cls):
        parameters = super().parameters()
        parameters.update(
            {
                "labels": ListValue(description="List of class labels"),
                "path_to_labels": StringValue(
                    description="Path to file with labels. Overrides the labels, if they sets via 'labels' parameter"
                ),
                "blur_strength": NumericalValue(
                    value_type=int,
                    description="Blurring kernel size. -1 value means no blurring and no soft_threshold",
                    default_value=-1,
                ),
                "soft_threshold": NumericalValue(
                    value_type=float,
                    description="Probability threshold value for bounding box filtering. inf value means no blurring and no soft_threshold",
                    default_value=float("-inf"),
                ),
                "return_soft_prediction": BooleanValue(
                    description="Return raw resized model prediction in addition to processed one",
                    default_value=True,
                ),
            }
        )
        return parameters

    def postprocess(self, outputs, meta):
        input_image_height = meta["original_shape"][0]
        input_image_width = meta["original_shape"][1]
        predictions = outputs[self.output_blob_name].squeeze()

        if self.out_channels < 2:  # assume the output is already ArgMax'ed
            soft_prediction = predictions.astype(np.uint8)
        else:
            soft_prediction = np.transpose(predictions, axes=(1, 2, 0))

        hard_prediction = create_hard_prediction_from_soft_prediction(
            soft_prediction=soft_prediction,
            soft_threshold=self.soft_threshold,
            blur_strength=self.blur_strength,
        )

        hard_prediction = cv2.resize(
            hard_prediction,
            (input_image_width, input_image_height),
            0,
            0,
            interpolation=cv2.INTER_NEAREST,
        )

        if self.return_soft_prediction:
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
                (
                    _get_activation_map(soft_prediction)
                    if _feature_vector_name in outputs
                    else np.ndarray(0)
                ),
                outputs.get(_feature_vector_name, np.ndarray(0)),
            )
        return hard_prediction

    def get_contours(
        self, hard_prediction: np.ndarray, soft_prediction: np.ndarray
    ) -> list:
        height, width = hard_prediction.shape[:2]
        n_layers = soft_prediction.shape[2]

        if n_layers == 1:
            raise RuntimeError("Cannot get contours from soft prediction with 1 layer")
        combined_contours = []
        for layer_index in range(1, n_layers):  # ignoring background
            label = self.get_label_name(layer_index - 1)
            if len(soft_prediction.shape) == 3:
                current_label_soft_prediction = soft_prediction[:, :, layer_index]
            else:
                current_label_soft_prediction = soft_prediction

            obj_group = hard_prediction == layer_index
            label_index_map = obj_group.astype(np.uint8) * 255

            contours, _hierarchy = cv2.findContours(
                label_index_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
            )

            for contour in contours:
                mask = np.zeros(hard_prediction.shape, dtype=np.uint8)
                cv2.drawContours(
                    mask,
                    np.asarray([contour]),
                    contourIdx=-1,
                    color=1,
                    thickness=-1,
                )
                probability = cv2.mean(current_label_soft_prediction, mask)[0]
                combined_contours.append(Contour(label, probability, contour))

        return combined_contours


class SalientObjectDetectionModel(SegmentationModel):
    __model__ = "Salient_Object_Detection"

    def postprocess(self, outputs, meta):
        input_image_height = meta["original_shape"][0]
        input_image_width = meta["original_shape"][1]
        result = outputs[self.output_blob_name].squeeze()
        result = 1 / (1 + np.exp(-result))
        result = cv2.resize(
            result,
            (input_image_width, input_image_height),
            0,
            0,
            interpolation=cv2.INTER_NEAREST,
        )
        return result


_feature_vector_name = "feature_vector"


def _get_activation_map(features: Union[np.ndarray, Iterable, int, float]):
    """Getter activation_map functions."""
    min_soft_score = np.min(features)
    max_soft_score = np.max(features)
    factor = 255.0 / (max_soft_score - min_soft_score + 1e-12)

    float_act_map = factor * (features - min_soft_score)
    return np.round(float_act_map, out=float_act_map).astype(np.uint8)
