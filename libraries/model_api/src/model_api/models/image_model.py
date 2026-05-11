#
# Copyright (C) 2020-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import functools
import warnings
from typing import TYPE_CHECKING, Any

import numpy as np

from model_api.adapters.utils import (
    RESIZE_TYPES,
    InputTransform,
    create_intensity_fn,
)
from model_api.adapters.utils import _repeat_single_channel_np as _repeat_single_channel
from model_api.models.model import Model
from model_api.models.parameters import ParameterRegistry

if TYPE_CHECKING:
    from model_api.adapters.inference_adapter import InferenceAdapter


class ImageModel(Model):
    """An abstract wrapper for an image-based model

    The ImageModel has 1 or more inputs with images - 4D tensors with NHWC or NCHW layout.
    It may support additional inputs - 2D tensors.

    The ImageModel implements basic preprocessing for an image provided as model input.
    See `preprocess` description.

    The `postprocess` method must be implemented in a specific inherited wrapper.

    Attributes:
        image_blob_names (List[str]): names of all image-like inputs (4D tensors)
        image_info_blob_names (List[str]): names of all secondary inputs (2D tensors)
        image_blob_name (str): name of the first image input
        nchw_layout (bool): a flag whether the model input layer has NCHW layout
        resize_type (str): the type for image resizing (see `RESIZE_TYPE` for info)
        resize (function): resizing function corresponding to the `resize_type`
        input_transform (InputTransform): instance of the `InputTransform` for image normalization
    """

    __model__ = "ImageModel"

    def __init__(self, inference_adapter: InferenceAdapter, configuration: dict = {}, preload: bool = False) -> None:
        """Image model constructor

        It extends the `Model` constructor.

        Args:
            inference_adapter (InferenceAdapter): allows working with the specified executor
            configuration (dict, optional): it contains values for parameters accepted by specific
              wrapper (`confidence_threshold`, `labels` etc.) which are set as data attributes
            preload (bool, optional): a flag whether the model is loaded to device while
              initialization. If `preload=False`, the model must be loaded via `load` method before inference

        Raises:
            WrapperError: if the wrapper failed to define appropriate inputs for images
        """
        super().__init__(inference_adapter, configuration, preload)
        self.image_blob_names, self.image_info_blob_names = self._get_inputs()
        self.image_blob_name = self.image_blob_names[0]

        self.nchw_layout = self.inputs[self.image_blob_name].layout == "NCHW"
        if self.nchw_layout:
            self.n, self.c, self.h, self.w = self.inputs[self.image_blob_name].shape
        else:
            self.n, self.h, self.w, self.c = self.inputs[self.image_blob_name].shape

        self._is_dynamic = False
        if self.h == -1 or self.w == -1:
            self._is_dynamic = True

        self.resize = RESIZE_TYPES[self.params.resize_type]

        # Infer intensity_max_value from input_dtype when not explicitly set
        intensity_mode = self.params.intensity_mode
        intensity_max_value = self.params.intensity_max_value
        if intensity_max_value is None and intensity_mode == "scale_to_unit":
            _DTYPE_MAX_VALUE = {"u8": 255.0, "u16": 65535.0, "i16": 32767.0, "f32": 1.0}
            intensity_max_value = _DTYPE_MAX_VALUE.get(self.params.input_dtype)

        # Build Python-side intensity function for non-embeddable modes or fallback paths
        _intensity_fn = (
            create_intensity_fn(
                intensity_mode,
                max_value=intensity_max_value,
                window_center=self.params.intensity_window_center,
                window_width=self.params.intensity_window_width,
                percentile_low=self.params.intensity_percentile_low,
                percentile_high=self.params.intensity_percentile_high,
                scale_factor=self.params.intensity_scale_factor,
                min_value=self.params.intensity_min_value,
            )
            if intensity_mode == "percentile"
            else None
        )

        self.input_transform = InputTransform(
            self.params.reverse_input_channels,
            self.params.mean_values,
            self.params.scale_values,
            intensity_fn=_intensity_fn,
        )

        layout = self.inputs[self.image_blob_name].layout
        input_dtype = self.params.input_dtype
        if self.params.embedded_processing:
            self.h, self.w = self.params.orig_height, self.params.orig_width
        elif not self._is_dynamic:
            input_frame_shape = None
            if self.params.input_frame_height and self.params.input_frame_width:
                input_frame_shape = (self.params.input_frame_height, self.params.input_frame_width)
            inference_adapter.embed_preprocessing(
                layout=layout,
                resize_mode=self.params.resize_type,
                interpolation_mode="LINEAR",
                target_shape=(self.w, self.h),
                pad_value=self.params.pad_value,
                brg2rgb=self.params.reverse_input_channels,
                mean=self.params.mean_values,
                scale=self.params.scale_values,
                input_dtype=input_dtype,
                intensity_mode=intensity_mode,
                intensity_max_value=intensity_max_value,
                intensity_window_center=self.params.intensity_window_center,
                intensity_window_width=self.params.intensity_window_width,
                intensity_percentile_low=self.params.intensity_percentile_low,
                intensity_percentile_high=self.params.intensity_percentile_high,
                intensity_scale_factor=self.params.intensity_scale_factor,
                intensity_min_value=self.params.intensity_min_value,
                intensity_repeat_channels=self.params.intensity_repeat_channels,
                input_frame_shape=input_frame_shape,
            )
            self._embedded_processing = True
            self.orig_height, self.orig_width = self.h, self.w

        self._wrap_preprocess_for_backward_compat()

    @classmethod
    def parameters(cls) -> dict[str, Any]:
        parameters = super().parameters()
        parameters.update(
            ParameterRegistry.merge(
                ParameterRegistry.IMAGE_PREPROCESSING,
                ParameterRegistry.IMAGE_RESIZE,
            ),
        )
        return parameters

    def get_label_name(self, label_id: int) -> str:
        """
        Returns a label name by it's index.
        If index is out of range, and auto-generated name is returned.

        Args:
            label_id (int): label index.

        Returns:
            str: label name.
        """
        labels = self.params.labels
        if labels is None:
            return f"#{label_id}"
        if label_id >= len(labels):
            return f"#{label_id}"
        return labels[label_id]

    def _get_inputs(self) -> tuple[list[str], ...]:
        """Defines the model inputs for images and additional info.

        Raises:
            WrapperError: if the wrapper failed to define appropriate inputs for images

        Returns:
            - list of inputs names for images
            - list of inputs names for additional info
        """
        image_blob_names, image_info_blob_names = [], []
        for name, metadata in self.inputs.items():
            if len(metadata.shape) == 4:
                image_blob_names.append(name)
            elif len(metadata.shape) == 2:
                image_info_blob_names.append(name)
            else:
                self.raise_error(
                    "Failed to identify the input for ImageModel: only 2D and 4D input layer supported",
                )
        if not image_blob_names:
            self.raise_error(
                "Failed to identify the input for the image: no 4D input layer found",
            )
        return image_blob_names, image_info_blob_names

    def base_preprocess(self, inputs: np.ndarray) -> list[dict]:
        """Data preprocess method

        It performs basic preprocessing of a single image:
            - Resizes the image to fit the model input size via the defined resize type
            - Normalizes the image: subtracts means, divides by scales, switch channels BGR-RGB
            - Changes the image layout according to the model input layout

        Also, it keeps the size of original image and resized one as `original_shape` and `resized_shape`
        in the metadata dictionary.

        Note:
            It supports only models with single image input. If the model has more image inputs or has
            additional supported inputs, the `preprocess` should be overloaded in a specific wrapper.

        Args:
            inputs (ndarray): a single image as 3D array in HWC layout

        Returns:
            - the preprocessed image in the following format:
                {
                    'input_layer_name': preprocessed_image
                }
            - the input metadata, which might be used in `postprocess` method
        """
        if self.params.embedded_processing:
            dict_inputs, meta = self._preprocess_embedded(inputs)
            dict_inputs, meta = self.preprocess(dict_inputs, meta)
            return [dict_inputs, meta]

        # 0. Expand single-channel to 3 channels if requested
        if self.params.intensity_repeat_channels:
            inputs = _repeat_single_channel(inputs)

        # 1. Resize
        resized_image, meta = self._resize_image(inputs)

        # 2. Transform
        processed_image = self._input_transform(resized_image)

        # 3. Layout
        processed_image = self._change_layout(processed_image)

        # 4. Pack
        dict_inputs = {self.image_blob_name: processed_image}

        # 5. Model-specific preprocess
        dict_inputs, meta = self.preprocess(dict_inputs, meta)

        return [dict_inputs, meta]

    def _preprocess_embedded(self, inputs: np.ndarray) -> tuple[dict, dict]:
        original_shape = inputs.shape
        processed_image = inputs[None]
        if self._is_dynamic:
            h, w, c = inputs.shape
            resized_shape = (w, h, c)
        else:
            resized_shape = (self.w, self.h, self.c)

        return (
            {self.image_blob_name: processed_image},
            {
                "original_shape": original_shape,
                "resized_shape": resized_shape,
            },
        )

    def _resize_image(self, image: np.ndarray) -> tuple[np.ndarray, dict]:
        original_shape = image.shape
        if self._is_dynamic:
            h, w, c = image.shape
            resized_shape = (w, h, c)
            return image, {"original_shape": original_shape, "resized_shape": resized_shape}

        resized_shape = (self.w, self.h, self.c)
        resized_image = self.resize(image, (self.w, self.h), pad_value=self.params.pad_value)
        return resized_image, {"original_shape": original_shape, "resized_shape": resized_shape}

    def _input_transform(self, image: np.ndarray) -> np.ndarray:
        return self.input_transform(image)

    def _wrap_preprocess_for_backward_compat(self) -> None:
        """Wrap preprocess to support legacy single-argument calls."""
        original_preprocess = self.preprocess

        @functools.wraps(original_preprocess)
        def _compat_preprocess(dict_inputs, meta=None):
            if meta is None and isinstance(dict_inputs, np.ndarray):
                warnings.warn(
                    "Calling preprocess(image) with a single numpy array is "
                    "deprecated since model_api v0.4.0 and will be removed in a "
                    "future version. Use base_preprocess(image) or __call__(image) "
                    "instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return self.base_preprocess(dict_inputs)
            return original_preprocess(dict_inputs, meta)

        self.preprocess = _compat_preprocess  # type: ignore[method-assign]

    def preprocess(self, dict_inputs: dict, meta: dict) -> tuple[dict, dict]:
        return dict_inputs, meta

    def _change_layout(self, image: np.ndarray) -> np.ndarray:
        """Changes the input image layout to fit the layout of the model input layer.

        Args:
            inputs (ndarray): a single image as 3D array in HWC layout

        Returns:
            - the image with layout aligned with the model layout
        """
        h, w, c = image.shape if self._is_dynamic else (self.h, self.w, self.c)

        # For fixed models, use the predefined dimensions
        if self.nchw_layout:
            image = image.transpose((2, 0, 1))  # HWC->CHW
            image = image.reshape((1, c, h, w))
        else:
            image = image.reshape((1, h, w, c))

        return image
