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

import cv2
import numpy as np

from .image_model import ImageModel
from .types import BooleanValue, ListValue, NumericalValue, StringValue
from .utils import load_labels


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
    soft_prediction_blurred = cv2.blur(soft_prediction, (blur_strength, blur_strength))
    assert len(soft_prediction.shape) == 3
    soft_prediction_blurred[soft_prediction_blurred < soft_threshold] = 0
    return np.argmax(soft_prediction_blurred, axis=2)


class SegmentationModel(ImageModel):
    __model__ = "Segmentation"

    def __init__(self, inference_adapter, configuration=None, preload=False):
        super().__init__(inference_adapter, configuration, preload)
        self._check_io_number(1, 1)
        if self.path_to_labels:
            self.labels = load_labels(self.path_to_labels)

        self.output_blob_name = self._get_outputs()

    def _get_outputs(self):
        layer_name = next(iter(self.outputs))
        layer_shape = self.outputs[layer_name].shape

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

        return layer_name

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
                    default_value=float("inf"),
                ),
                "return_soft_prediction": BooleanValue(
                    description="Retern raw resized model prediction in addition to processed one",
                    default_value=True,
                ),
            }
        )

        return parameters

    def postprocess(self, outputs, meta):
        if self.blur_strength == -1 and self.soft_threshold == float("inf"):
            predictions = outputs[self.output_blob_name].squeeze()
            input_image_height = meta["original_shape"][0]
            input_image_width = meta["original_shape"][1]

            if self.out_channels < 2:  # assume the output is already ArgMax'ed
                result = predictions.astype(np.uint8)
            else:
                result = np.argmax(predictions, axis=0).astype(np.uint8)

            result = cv2.resize(
                result,
                (input_image_width, input_image_height),
                0,
                0,
                interpolation=cv2.INTER_NEAREST,
            )
            return result
        predictions = outputs[self.output_blob_name].squeeze()
        soft_prediction = np.transpose(predictions, axes=(1, 2, 0))

        hard_prediction = create_hard_prediction_from_soft_prediction(
            soft_prediction=soft_prediction,
            soft_threshold=self.soft_threshold,
            blur_strength=self.blur_strength,
        )
        hard_prediction = cv2.resize(
            hard_prediction,
            meta["original_shape"][1::-1],
            0,
            0,
            interpolation=cv2.INTER_NEAREST,
        )
        if self.return_soft_prediction:
            soft_prediction = cv2.resize(
                soft_prediction,
                meta["original_shape"][1::-1],
                0,
                0,
                interpolation=cv2.INTER_NEAREST,
            )
            return hard_prediction, soft_prediction
        return hard_prediction


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
