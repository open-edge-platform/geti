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

from openvino.model_api.adapters.utils import RESIZE_TYPES, InputTransform

from .model import Model
from .types import BooleanValue, ListValue, NumericalValue, StringValue


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

    def __init__(self, inference_adapter, configuration=dict(), preload=False):
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
        self.resize = RESIZE_TYPES[self.resize_type]
        self.input_transform = InputTransform(
            self.reverse_input_channels, self.mean_values, self.scale_values
        )

        layout = self.inputs[self.image_blob_name].layout
        if self.embedded_processing:
            self.h, self.w = self.orig_height, self.orig_width
        else:
            inference_adapter.embed_preprocessing(
                layout=layout,
                resize_mode=self.resize_type,
                interpolation_mode="LINEAR",
                target_shape=(self.w, self.h),
                pad_value=self.pad_value,
                brg2rgb=self.reverse_input_channels,
                mean=self.mean_values,
                scale=self.scale_values,
            )
            self.embedded_processing = True
            self.orig_height, self.orig_width = self.h, self.w

    @classmethod
    def parameters(cls):
        parameters = super().parameters()
        parameters.update(
            {
                "embedded_processing": BooleanValue(
                    description="Flag that pre/postprocessing embedded",
                    default_value=False,
                ),
                "mean_values": ListValue(
                    description="Normalization values, which will be subtracted from image channels for image-input layer during preprocessing",
                    default_value=[],
                ),
                "orig_height": NumericalValue(
                    int, description="Model input height before embedding processing"
                ),
                "orig_width": NumericalValue(
                    int, description="Model input width before embedding processing"
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
                    default_value=False, description="Reverse the input channel order"
                ),
                "scale_values": ListValue(
                    default_value=[],
                    description="Normalization values, which will divide the image channels for image-input layer",
                ),
            }
        )
        return parameters

    def get_label_name(self, label_id):
        if self.labels is None:
            return f"#{label_id}"
        if label_id >= len(self.labels):
            return f"#{label_id}"
        return self.labels[label_id]

    def _get_inputs(self):
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
                    "Failed to identify the input for ImageModel: only 2D and 4D input layer supported"
                )
        if not image_blob_names:
            self.raise_error(
                "Failed to identify the input for the image: no 4D input layer found"
            )
        return image_blob_names, image_info_blob_names

    def preprocess(self, inputs):
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
        return {self.image_blob_name: inputs[None]}, {
            "original_shape": inputs.shape,
            "resized_shape": (self.w, self.h, self.c),
        }

    def _change_layout(self, image):
        """Changes the input image layout to fit the layout of the model input layer.

        Args:
            inputs (ndarray): a single image as 3D array in HWC layout

        Returns:
            - the image with layout aligned with the model layout
        """
        if self.nchw_layout:
            image = image.transpose((2, 0, 1))  # HWC->CHW
            image = image.reshape((1, self.c, self.h, self.w))
        else:
            image = image.reshape((1, self.h, self.w, self.c))
        return image
