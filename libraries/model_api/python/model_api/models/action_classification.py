#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from model_api.adapters.utils import RESIZE_TYPES, InputTransform
from model_api.models.result import ClassificationResult, Label

from .model import Model
from .types import BooleanValue, ListValue, NumericalValue, StringValue
from .utils import load_labels

if TYPE_CHECKING:
    from model_api.adapters.inference_adapter import InferenceAdapter


class ActionClassificationModel(Model):
    """A wrapper for an action classification model

    The model given by inference_adapter can have two input formats.
    One is 'NSCTHW' and another one is 'NSTHWC'.
    What each letter means are as below.
    N => batch size / S => number of clips x number of crops / C => number of channels
    T => time / H => height / W => width
    The ActionClassificationModel should gets single input with video - 4D tensors, which means N and S should be 1.

    Video format is different from image format, so OpenVINO PrePostProcessors isn't available.
    For that reason, postprocessing operations such as resize and normalize are conducted in this class.

    Attributes:
        image_blob_names (List[str]): names of all image-like inputs (6D tensors)
        image_blob_name (str): name of the first image input
        resize_type (str): the type for image resizing (see `RESIZE_TYPE` for info)
        resize (function): resizing function corresponding to the `resize_type`
        input_transform (InputTransform): instance of the `InputTransform` for image normalization
    """

    __model__ = "Action Classification"

    def __init__(
        self,
        inference_adapter: InferenceAdapter,
        configuration: dict[str, Any] = {},
        preload: bool = False,
    ) -> None:
        """Action classaification model constructor

        Args:
            inference_adapter (InferenceAdapter): allows working with the specified executor
            configuration (dict, optional): it contains values for parameters accepted by specific
              wrapper (`labels` `mean_values`, etc.) which are set as data attributes
            preload (bool, optional): a flag whether the model is loaded to device while
              initialization. If `preload=False`, the model must be loaded via `load` method before inference

        Raises:
            WrapperError: if the wrapper failed to define appropriate inputs for images
        """
        super().__init__(inference_adapter, configuration, preload)
        self.image_blob_names = self._get_inputs()
        self.image_blob_name = self.image_blob_names[0]
        self.nscthw_layout = "NSCTHW" in self.inputs[self.image_blob_name].layout
        self.labels: list[str]
        self.path_to_labels: str
        self.mean_values: list[int | float]
        self.pad_value: int
        self.resize_type: str
        self.reverse_input_channels: bool
        self.scale_values: list[int | float]

        if self.nscthw_layout:
            self.n, self.s, self.c, self.t, self.h, self.w = self.inputs[self.image_blob_name].shape
        else:
            self.n, self.s, self.t, self.h, self.w, self.c = self.inputs[self.image_blob_name].shape
        self.resize = RESIZE_TYPES[self.resize_type]
        self.input_transform = InputTransform(
            self.reverse_input_channels,
            self.mean_values,
            self.scale_values,
        )
        if self.path_to_labels:
            self.labels = load_labels(self.path_to_labels)

    @property
    def clip_size(self) -> int:
        return self.t

    @classmethod
    def parameters(cls) -> dict[str, Any]:
        parameters = super().parameters()
        parameters.update(
            {
                "labels": ListValue(description="List of class labels"),
                "path_to_labels": StringValue(
                    description="Path to file with labels. Overrides the labels, if they sets via 'labels' parameter",
                ),
                "mean_values": ListValue(
                    description=(
                        "Normalization values, which will be subtracted from image channels "
                        "for image-input layer during preprocessing"
                    ),
                    default_value=[],
                ),
                "pad_value": NumericalValue(
                    int,
                    min=0,
                    max=255,
                    description="Pad value for resize_image_letterbox embedded into a model",
                    default_value=0,
                ),
                "resize_type": StringValue(
                    default_value="standard",
                    choices=tuple(RESIZE_TYPES.keys()),
                    description="Type of input image resizing",
                ),
                "reverse_input_channels": BooleanValue(
                    default_value=False,
                    description="Reverse the input channel order",
                ),
                "scale_values": ListValue(
                    default_value=[],
                    description="Normalization values, which will divide the image channels for image-input layer",
                ),
            },
        )
        return parameters

    def _get_inputs(self) -> list[str]:
        """Defines the model inputs for images and additional info.

        Raises:
            WrapperError: if the wrapper failed to define appropriate inputs for images

        Returns:
            - list of inputs names for images
            - list of inputs names for additional info
        """
        image_blob_names = []
        for name, metadata in self.inputs.items():
            if len(metadata.shape) == 6:
                image_blob_names.append(name)
            else:
                self.raise_error(
                    "Failed to identify the input for ImageModel: only 4D and 6D input layer supported",
                )
        if not image_blob_names:
            self.raise_error(
                "Failed to identify the input for the image: no 6D input layer found",
            )
        return image_blob_names

    def preprocess(
        self,
        inputs: np.ndarray,
    ) -> tuple[dict[str, np.ndarray], dict[str, tuple[int, ...]]]:
        """Data preprocess method

        It performs basic preprocessing of a single video:
            - Resizes the image to fit the model input size via the defined resize type
            - Normalizes the image: subtracts means, divides by scales, switch channels BGR-RGB
            - Changes the image layout according to the model input layout

        Also, it keeps the size of original image and resized one as `original_shape` and `resized_shape`
        in the metadata dictionary.

        Note:
            It supports only models with single image input. If the model has more image inputs or has
            additional supported inputs, the `preprocess` should be overloaded in a specific wrapper.

        Args:
            inputs (ndarray): a single image as 4D array.

        Returns:
            - the preprocessed image in the following format:
                {
                    'input_layer_name': preprocessed_image
                }
            - the input metadata, which might be used in `postprocess` method
        """
        if self.t != -1 and self.t != inputs.shape[0]:
            msg = (
                f"Given model expects ({self.t}, {self.h}, {self.w} ,{self.c}) input shape but current input "
                f"has {inputs.shape} shape. Please fit input shape to model or set dynamic shapes to the model."
            )
            raise RuntimeError(msg)

        meta = {
            "original_shape": inputs.shape,
            "resized_shape": (self.n, self.s, self.c, self.t, self.h, self.w),
        }
        resized_inputs = [self.resize(frame, (self.w, self.h), pad_value=self.pad_value) for frame in inputs]
        np_frames = self._change_layout(
            [self.input_transform(inputs) for inputs in resized_inputs],
        )
        dict_inputs = {self.image_blob_name: np_frames}
        return dict_inputs, meta

    def _change_layout(self, inputs: list[np.ndarray]) -> np.ndarray:
        """Changes the input frame layout to fit the layout of the model input layer.

        Args:
            inputs (ndarray): a single frame as 4D array in HWC layout

        Returns:
            - the frame with layout aligned with the model layout
        """
        np_inputs = np.expand_dims(inputs, axis=(0, 1))  # [1, 1, T, H, W, C]
        if self.nscthw_layout:
            return np_inputs.transpose(0, 1, -1, 2, 3, 4)  # [1, 1, C, T, H, W]
        return np_inputs

    def postprocess(
        self,
        outputs: dict[str, np.ndarray],
        meta: dict[str, Any],
    ) -> ClassificationResult:
        """Post-process."""
        logits = next(iter(outputs.values())).squeeze()
        index = np.argmax(logits)
        return ClassificationResult(
            [Label(int(index), self.labels[index], logits[index])],
            np.ndarray(0),
            np.ndarray(0),
            np.ndarray(0),
        )
