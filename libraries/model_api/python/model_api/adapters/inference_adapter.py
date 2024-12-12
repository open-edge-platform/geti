#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations  # TODO: remove when Python3.9 support is dropped

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Metadata:
    names: set[str] = field(default_factory=set)
    shape: list[int] = field(default_factory=list)
    layout: str = ""
    precision: str = ""
    type: str = ""
    meta: dict = field(default_factory=dict)


class InferenceAdapter(ABC):
    """
    An abstract Model Adapter with the following interface:

        - Reading the model from disk or other place
        - Loading the model to the device
        - Accessing the information about inputs/outputs
        - The model reshaping
        - Synchronous model inference
        - Asynchronous model inference
    """

    precisions = ("FP32", "I32", "FP16", "I16", "I8", "U8")

    @abstractmethod
    def __init__(self) -> None:
        """
        An abstract Model Adapter constructor.
        Reads the model from disk or other place.
        """
        self.model: Any

    @abstractmethod
    def load_model(self):
        """Loads the model on the device."""

    @abstractmethod
    def get_model(self):
        """Get the model."""

    @abstractmethod
    def get_input_layers(self):
        """Gets the names of model inputs and for each one creates the Metadata structure,
           which contains the information about the input shape, layout, precision
           in OpenVINO format, meta (optional)

        Returns:
            - the dict containing Metadata for all inputs
        """

    @abstractmethod
    def get_output_layers(self):
        """Gets the names of model outputs and for each one creates the Metadata structure,
           which contains the information about the output shape, layout, precision
           in OpenVINO format, meta (optional)

        Returns:
            - the dict containing Metadata for all outputs
        """

    @abstractmethod
    def reshape_model(self, new_shape: dict):
        """Reshapes the model inputs to fit the new input shape.

        Args:
            - new_shape (dict): the dictionary with inputs names as keys and
                list of new shape as values in the following format:
                {
                    'input_layer_name_1': [1, 128, 128, 3],
                    'input_layer_name_2': [1, 128, 128, 3],
                    ...
                }
        """

    @abstractmethod
    def infer_sync(self, dict_data: dict) -> dict:
        """Performs the synchronous model inference. The infer is a blocking method.

        Args:
            - dict_data: it's submitted to the model for inference and has the following format:
                {
                    'input_layer_name_1': data_1,
                    'input_layer_name_2': data_2,
                    ...
                }

        Returns:
            - raw result (dict) - model raw output in the following format:
                {
                    'output_layer_name_1': raw_result_1,
                    'output_layer_name_2': raw_result_2,
                    ...
                }
        """

    @abstractmethod
    def infer_async(self, dict_data: dict, callback_data: Any):
        """
        Performs the asynchronous model inference and sets
        the callback for inference completion. Also, it should
        define get_raw_result() function, which handles the result
        of inference from the model.

        Args:
            - dict_data: it's submitted to the model for inference and has the following format:
                {
                    'input_layer_name_1': data_1,
                    'input_layer_name_2': data_2,
                    ...
                }
            - callback_data: the data for callback, that will be taken after the model inference is ended
        """

    @abstractmethod
    def get_raw_result(self, infer_result: dict) -> dict:
        """Gets raw results from the internal inference framework representation as a dict.

        Args:
            - infer_result (dict): framework-specific result of inference from the model

        Returns:
            - raw result (dict) - model raw output in the following format:
                {
                    'output_layer_name_1': raw_result_1,
                    'output_layer_name_2': raw_result_2,
                    ...
                }
        """

    @abstractmethod
    def set_callback(self, callback_fn: Callable):
        """
        Sets callback that grabs results of async inference.

        Args:
            callback_fn (Callable): Callback function.
        """

    @abstractmethod
    def is_ready(self) -> bool:
        """In case of asynchronous execution checks if one can submit input data
        to the model for inference, or all infer requests are busy.

        Returns:
            - the boolean flag whether the input data can be
                submitted to the model for inference or not
        """

    @abstractmethod
    def await_all(self):
        """In case of asynchronous execution waits the completion of all
        busy infer requests.
        """

    @abstractmethod
    def await_any(self):
        """In case of asynchronous execution waits the completion of any
        busy infer request until it becomes available for the data submission.
        """

    @abstractmethod
    def get_rt_info(self, path: list[str]) -> Any:
        """
        Returns an attribute stored in model info.

        Args:
            path (list[str]): a sequence of tag names leading to the attribute.

        Returns:
            Any: a value stored under corresponding tag sequence.
        """

    @abstractmethod
    def update_model_info(self, model_info: dict[str, Any]):
        """
        Updates model with the provided model info.  Model info dict can
        also contain nested dicts.

        Args:
            model_info (dict[str, Any]): model info dict to write to the model.
        """

    @abstractmethod
    def save_model(self, path: str, weights_path: str | None, version: str | None):
        """
        Serializes model to the filesystem.

        Args:
            path (str): Path to write the resulting model.
            weights_path (str | None): Optional path to save weights if they are stored separately.
            version (str | None): Optional model version.
        """

    @abstractmethod
    def embed_preprocessing(
        self,
        layout: str,
        resize_mode: str,
        interpolation_mode: str,
        target_shape: tuple[int, ...],
        pad_value: int,
        dtype: type = int,
        brg2rgb: bool = False,
        mean: list[Any] | None = None,
        scale: list[Any] | None = None,
        input_idx: int = 0,
    ):
        """
        Embeds preprocessing into the model if possible with the adapter being used.
        In some cases, this method would just add extra python preprocessing steps
        instaed actuall of embedding it into the model representation.

        Args:
            layout (str): Layout, for instance NCHW.
            resize_mode (str): Resize type to use for preprocessing.
            interpolation_mode (str): Resize interpolation mode.
            target_shape (tuple[int, ...]): Target resize shape.
            pad_value (int): Value to pad with if resize implies padding.
            dtype (type, optional): Input data type for the preprocessing module. Defaults to int.
            bgr2rgb (bool, optional): Defines if we need to swap R and B channels in case of image input.
            Defaults to False.
            mean (list[Any] | None, optional): Mean values to perform input normalization. Defaults to None.
            scale (list[Any] | None, optional): Scale values to perform input normalization. Defaults to None.
            input_idx (int, optional): Index of the model input to apply preprocessing to. Defaults to 0.
        """
