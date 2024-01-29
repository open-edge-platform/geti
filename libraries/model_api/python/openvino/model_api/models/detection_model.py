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

from .image_model import ImageModel
from .types import ListValue, NumericalValue, StringValue
from .utils import load_labels


class DetectionModel(ImageModel):
    """An abstract wrapper for object detection model

    The DetectionModel must have a single image input.
    It inherits `preprocess` from `ImageModel` wrapper. Also, it defines `_resize_detections` method,
    which should be used in `postprocess`, to clip bounding boxes and resize ones to original image shape.

    The `postprocess` method must be implemented in a specific inherited wrapper.
    """

    def __init__(self, inference_adapter, configuration=dict(), preload=False):
        """Detection Model constructor

        It extends the `ImageModel` construtor.

        Args:
            inference_adapter (InferenceAdapter): allows working with the specified executor
            configuration (dict, optional): it contains values for parameters accepted by specific
              wrapper (`confidence_threshold`, `labels` etc.) which are set as data attributes
            preload (bool, optional): a flag whether the model is loaded to device while
              initialization. If `preload=False`, the model must be loaded via `load` method before inference

        Raises:
            WrapperError: if the model has more than 1 image inputs
        """

        super().__init__(inference_adapter, configuration, preload)

        if not self.image_blob_name:
            self.raise_error(
                "The Wrapper supports only one image input, but {} found".format(
                    len(self.image_blob_names)
                )
            )

        if self.path_to_labels:
            self.labels = load_labels(self.path_to_labels)

    @classmethod
    def parameters(cls):
        parameters = super().parameters()
        parameters.update(
            {
                "confidence_threshold": NumericalValue(
                    default_value=0.5,
                    description="Probability threshold value for bounding box filtering",
                ),
                "labels": ListValue(description="List of class labels"),
                "path_to_labels": StringValue(
                    description="Path to file with labels. Overrides the labels, if they sets via 'labels' parameter"
                ),
            }
        )

        return parameters

    def _resize_detections(self, detections, meta):
        """Resizes detection bounding boxes according to initial image shape.

        It implements image resizing depending on the set `resize_type`(see `ImageModel` for details).
        Next, it applies bounding boxes clipping.

        Args:
            detections (List[Detection]): list of detections with coordinates in normalized form
            meta (dict): the input metadata obtained from `preprocess` method

        Returns:
            - list of detections with resized and clipped coordinates to fit the initial image
        """
        input_img_height, input_img_widht = meta["original_shape"][:2]
        inverted_scale_x = input_img_widht / self.w
        inverted_scale_y = input_img_height / self.h
        pad_left = 0
        pad_top = 0
        if (
            "fit_to_window" == self.resize_type
            or "fit_to_window_letterbox" == self.resize_type
        ):
            inverted_scale_x = inverted_scale_y = max(
                inverted_scale_x, inverted_scale_y
            )
            if "fit_to_window_letterbox" == self.resize_type:
                pad_left = (self.w - round(input_img_widht / inverted_scale_x)) // 2
                pad_top = (self.h - round(input_img_height / inverted_scale_y)) // 2

        for detection in detections:
            detection.xmin = min(
                max(round((detection.xmin * self.w - pad_left) * inverted_scale_x), 0),
                input_img_widht,
            )
            detection.ymin = min(
                max(round((detection.ymin * self.h - pad_top) * inverted_scale_y), 0),
                input_img_height,
            )
            detection.xmax = min(
                max(round((detection.xmax * self.w - pad_left) * inverted_scale_x), 0),
                input_img_widht,
            )
            detection.ymax = min(
                max(round((detection.ymax * self.h - pad_top) * inverted_scale_y), 0),
                input_img_height,
            )
        return detections

    def _add_label_names(self, detections):
        """Adds labels names to detections if they are available

        Args:
            detections (List[Detection]): list of detections with coordinates in normalized form

        Returns:
            - list of detections with label strings
        """
        for detection in detections:
            detection.str_label = self.get_label_name(detection.id)
        return detections
