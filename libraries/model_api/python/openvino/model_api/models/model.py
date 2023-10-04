"""
 Copyright (C) 2020-2023 Intel Corporation

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

import logging as log
import re

from openvino.model_api.adapters.inference_adapter import InferenceAdapter
from openvino.model_api.adapters.onnx_adapter import ONNXRuntimeAdapter
from openvino.model_api.adapters.openvino_adapter import (
    OpenvinoAdapter,
    create_core,
    get_user_config,
)
from openvino.model_api.adapters.ovms_adapter import OVMSAdapter


class WrapperError(Exception):
    """The class for errors occurred in Model API wrappers"""

    def __init__(self, wrapper_name, message):
        super().__init__(f"{wrapper_name}: {message}")


class Model:
    """An abstract model wrapper

    The abstract model wrapper is free from any executor dependencies.
    It sets the `InferenceAdapter` instance with the provided model
    and defines model inputs/outputs.

    Next, it loads the provided configuration variables and sets it as wrapper attributes.
    The keys of the configuration dictionary should be presented in the `parameters` method.

    Also, it decorates the following adapter interface:
        - Loading the model to the device
        - The model reshaping
        - Synchronous model inference
        - Asynchronous model inference

    The `preprocess` and `postprocess` methods must be implemented in a specific inherited wrapper.

    Attributes:
        logger (Logger): instance of the Logger
        inference_adapter (InferenceAdapter): allows working with the specified executor
        inputs (dict): keeps the model inputs names and `Metadata` structure for each one
        outputs (dict): keeps the model outputs names and `Metadata` structure for each one
        model_loaded (bool): a flag whether the model is loaded to device
    """

    __model__ = None  # Abstract wrapper has no name

    def __init__(self, inference_adapter, configuration=dict(), preload=False):
        """Model constructor

        Args:
            inference_adapter (InferenceAdapter): allows working with the specified executor
            configuration (dict, optional): it contains values for parameters accepted by specific
              wrapper (`confidence_threshold`, `labels` etc.) which are set as data attributes
            preload (bool, optional): a flag whether the model is loaded to device while
              initialization. If `preload=False`, the model must be loaded via `load` method before inference

        Raises:
            WrapperError: if the wrapper configuration is incorrect
        """
        self.logger = log.getLogger()
        self.inference_adapter = inference_adapter
        if isinstance(
            self.inference_adapter, ONNXRuntimeAdapter
        ) and self.__model__ not in {
            "Classification",
            "MaskRCNN",
            "SSD",
            "Segmentation",
        }:
            self.raise_error(
                "this type of wrapper only supports OpenVINO and OVMS inference adapters"
            )

        self.inputs = self.inference_adapter.get_input_layers()
        self.outputs = self.inference_adapter.get_output_layers()
        for name, parameter in self.parameters().items():
            self.__setattr__(name, parameter.default_value)
        self._load_config(configuration)
        self.model_loaded = False
        if preload:
            self.load()

    def get_model(self):
        """Returns the ov.Model object stored in the InferenceAdapter.

        Note: valid only for local inference

        Returns:
            ov.Model object
        Raises:
            RuntimeError: in case of remote inference (serving)
        """
        if isinstance(self.inference_adapter, OpenvinoAdapter):
            return self.inference_adapter.get_model()

        raise RuntimeError("get_model() is not supported for remote inference")

    @classmethod
    def get_model_class(cls, name):
        subclasses = [
            subclass for subclass in cls.get_subclasses() if subclass.__model__
        ]
        if cls.__model__:
            subclasses.append(cls)
        for subclass in subclasses:
            if name.lower() == subclass.__model__.lower():
                return subclass
        cls.raise_error(
            'There is no model with name "{}" in list: {}'.format(
                name, ", ".join([subclass.__model__ for subclass in subclasses])
            )
        )

    @classmethod
    def create_model(
        cls,
        model,
        model_type=None,
        configuration={},
        preload=True,
        core=None,
        weights_path="",
        adaptor_parameters={},
        device="AUTO",
        nstreams="1",
        nthreads=None,
        max_num_requests=0,
        precision="FP16",
        download_dir=None,
        cache_dir=None,
    ):
        """
        Create an instance of the Model API model

        Args:
            model (str): model name from OpenVINO Model Zoo, path to model, OVMS URL
            configuration (:obj:`dict`, optional): dictionary of model config with model properties, for example confidence_threshold, labels
            model_type (:obj:`str`, optional): name of model wrapper to create (e.g. "ssd")
            preload (:obj:`bool`, optional): whether to call load_model(). Can be set to false to reshape model before loading
            core (optional): openvino.runtime.Core instance, passed to OpenvinoAdapter
            weights_path (:obj:`str`, optional): path to .bin file with model weights
            adaptor_parameters (:obj:`dict`, optional): parameters of ModelAdaptor
            device (:obj:`str`, optional): name of OpenVINO device (e.g. "CPU, GPU")
            nstreams (:obj:`int`, optional): number of inference streams
            nthreads (:obj:`int`, optional): number of threads to use for inference on CPU
            max_num_requests (:obj:`int`, optional): number of infer requests for asynchronous inference
            precision (:obj:`str`, optional): inference precision (e.g. "FP16")
            download_dir (:obj:`str`, optional): directory where to store downloaded models
            cache_dir (:obj:`str`, optional): directory where to store compiled models to reduce the load time before the inference

        Returns:
            Model objcet
        """
        if isinstance(model, InferenceAdapter):
            inference_adapter = model
        elif isinstance(model, str) and re.compile(
            r"(\w+\.*\-*)*\w+:\d+\/models\/[a-zA-Z0-9._-]+(\:\d+)*"
        ).fullmatch(model):
            inference_adapter = OVMSAdapter(model)
        else:
            if core is None:
                core = create_core()
                plugin_config = get_user_config(device, nstreams, nthreads)
            inference_adapter = OpenvinoAdapter(
                core=core,
                model=model,
                weights_path=weights_path,
                model_parameters=adaptor_parameters,
                device=device,
                plugin_config=plugin_config,
                max_num_requests=max_num_requests,
                precision=precision,
                download_dir=download_dir,
                cache_dir=cache_dir,
            )
        if model_type is None:
            model_type = inference_adapter.get_rt_info(
                ["model_info", "model_type"]
            ).astype(str)
        Model = cls.get_model_class(model_type)
        return Model(inference_adapter, configuration, preload)

    @classmethod
    def get_subclasses(cls):
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(subclass.get_subclasses())
        return all_subclasses

    @classmethod
    def available_wrappers(cls):
        available_classes = [cls] if cls.__model__ else []
        available_classes.extend(cls.get_subclasses())
        return [
            subclass.__model__ for subclass in available_classes if subclass.__model__
        ]

    @classmethod
    def parameters(cls):
        """Defines the description and type of configurable data parameters for the wrapper.

        See `types.py` to find available types of the data parameter. For each parameter
        the type, default value and description must be provided.

        The example of possible data parameter:
            'confidence_threshold': NumericalValue(
                default_value=0.5, description="Threshold value for detection box confidence"
            )

        The method must be implemented in each specific inherited wrapper.

        Returns:
            - the dictionary with defined wrapper data parameters
        """
        parameters = {}
        return parameters

    def _load_config(self, config):
        """Reads the configuration and creates data attributes
           by setting the wrapper parameters with values from configuration.

        Args:
            config (dict): the dictionary with keys to be set as data attributes
              and its values. The example of the config is the following:
              {
                  'confidence_threshold': 0.5,
                  'resize_type': 'fit_to_window',
              }

        Note:
            The config keys should be provided in `parameters` method for each wrapper,
            then the default value of the parameter will be updated. If some key presented
            in the config is not introduced in `parameters`, it will be omitted.

         Raises:
            WrapperError: if the configuration is incorrect
        """
        parameters = self.parameters()
        for name, param in parameters.items():
            try:
                value = param.from_str(
                    self.inference_adapter.get_rt_info(["model_info", name]).astype(str)
                )
                self.__setattr__(name, value)
            except RuntimeError as error:
                missing_rt_info = (
                    "Cannot get runtime attribute. Path to runtime attribute is incorrect."
                    in str(error)
                )
                is_OVMSAdapter = (
                    str(error) == "OVMSAdapter does not support RT info getting"
                )
                if not missing_rt_info and not is_OVMSAdapter:
                    raise

        for name, value in config.items():
            if value is None:
                continue
            if name in parameters:
                errors = parameters[name].validate(value)
                if errors:
                    self.logger.error(f'Error with "{name}" parameter:')
                    for error in errors:
                        self.logger.error(f"\t{error}")
                    self.raise_error("Incorrect user configuration")
                value = parameters[name].get_value(value)
                self.__setattr__(name, value)
            else:
                self.logger.warning(
                    f'The parameter "{name}" not found in {self.__model__} wrapper, will be omitted'
                )

    @classmethod
    def raise_error(cls, message):
        """Raises the WrapperError.

        Args:
            message (str): error message to be shown in the following format:
              "WrapperName: message"
        """
        raise WrapperError(cls.__model__, message)

    def preprocess(self, inputs):
        """Interface for preprocess method.

        Args:
            inputs: raw input data, the data type is defined by wrapper

        Returns:
            - the preprocessed data which is submitted to the model for inference
                and has the following format:
                {
                    'input_layer_name_1': data_1,
                    'input_layer_name_2': data_2,
                    ...
                }
            - the input metadata, which might be used in `postprocess` method
        """
        raise NotImplementedError

    def postprocess(self, outputs, meta):
        """Interface for postprocess method.

        Args:
            outputs (dict): model raw output in the following format:
                {
                    'output_layer_name_1': raw_result_1,
                    'output_layer_name_2': raw_result_2,
                    ...
                }
            meta (dict): the input metadata obtained from `preprocess` method

        Returns:
            - postprocessed data in the format defined by wrapper
        """
        raise NotImplementedError

    def _check_io_number(self, number_of_inputs, number_of_outputs):
        """Checks whether the number of model inputs/outputs is supported.

        Args:
            number_of_inputs (int, Tuple(int)): number of inputs supported by wrapper.
              Use -1 to omit the check
            number_of_outputs (int, Tuple(int)): number of outputs supported by wrapper.
              Use -1 to omit the check

        Raises:
            WrapperError: if the model has unsupported number of inputs/outputs
        """
        if not isinstance(number_of_inputs, tuple):
            if len(self.inputs) != number_of_inputs and number_of_inputs != -1:
                self.raise_error(
                    "Expected {} input blob{}, but {} found: {}".format(
                        number_of_inputs,
                        "s" if number_of_inputs != 1 else "",
                        len(self.inputs),
                        ", ".join(self.inputs),
                    )
                )
        else:
            if not len(self.inputs) in number_of_inputs:
                self.raise_error(
                    "Expected {} or {} input blobs, but {} found: {}".format(
                        ", ".join(str(n) for n in number_of_inputs[:-1]),
                        int(number_of_inputs[-1]),
                        len(self.inputs),
                        ", ".join(self.inputs),
                    )
                )

        if not isinstance(number_of_outputs, tuple):
            if len(self.outputs) != number_of_outputs and number_of_outputs != -1:
                self.raise_error(
                    "Expected {} output blob{}, but {} found: {}".format(
                        number_of_outputs,
                        "s" if number_of_outputs != 1 else "",
                        len(self.outputs),
                        ", ".join(self.outputs),
                    )
                )
        else:
            if not len(self.outputs) in number_of_outputs:
                self.raise_error(
                    "Expected {} or {} output blobs, but {} found: {}".format(
                        ", ".join(str(n) for n in number_of_outputs[:-1]),
                        int(number_of_outputs[-1]),
                        len(self.outputs),
                        ", ".join(self.outputs),
                    )
                )

    def __call__(self, inputs):
        """
        Applies preprocessing, synchronous inference, postprocessing routines while one call.

        Args:
            inputs: raw input data, the data type is defined by wrapper

        Returns:
            - postprocessed data in the format defined by wrapper
        """
        dict_data, input_meta = self.preprocess(inputs)
        raw_result = self.infer_sync(dict_data)
        return self.postprocess(raw_result, input_meta)

    def load(self, force=False):
        if not self.model_loaded or force:
            self.model_loaded = True
            self.inference_adapter.load_model()

    def reshape(self, new_shape):
        if self.model_loaded:
            self.logger.warning(
                f"{self.__model__}: the model already loaded to device, ",
                "should be reloaded after reshaping.",
            )
            self.model_loaded = False
        self.inference_adapter.reshape_model(new_shape)
        self.inputs = self.inference_adapter.get_input_layers()
        self.outputs = self.inference_adapter.get_output_layers()

    def infer_sync(self, dict_data):
        if not self.model_loaded:
            self.raise_error(
                "The model is not loaded to the device. Please, create the wrapper "
                "with preload=True option or call load() method before infer_sync()"
            )
        return self.inference_adapter.infer_sync(dict_data)

    def infer_async_raw(self, dict_data, callback_data):
        if not self.model_loaded:
            self.raise_error(
                "The model is not loaded to the device. Please, create the wrapper "
                "with preload=True option or call load() method before infer_async()"
            )
        self.inference_adapter.infer_async(dict_data, callback_data)

    def infer_async(self, input_data, user_data):
        if not self.model_loaded:
            self.raise_error(
                "The model is not loaded to the device. Please, create the wrapper "
                "with preload=True option or call load() method before infer_async()"
            )
        dict_data, meta = self.preprocess(input_data)
        self.inference_adapter.infer_async(
            dict_data,
            (
                meta,
                self.inference_adapter.get_raw_result,
                self.postprocess,
                self.callback_fn,
                user_data,
            ),
        )

    @staticmethod
    def process_callback(request, callback_data):
        meta, get_result_fn, postprocess_fn, callback_fn, user_data = callback_data
        raw_result = get_result_fn(request)
        result = postprocess_fn(raw_result, meta)
        callback_fn(result, user_data)

    def set_callback(self, callback_fn):
        self.callback_fn = callback_fn
        self.inference_adapter.set_callback(Model.process_callback)

    def is_ready(self):
        return self.inference_adapter.is_ready()

    def await_all(self):
        self.inference_adapter.await_all()

    def await_any(self):
        self.inference_adapter.await_any()

    def log_layers_info(self):
        """Prints the shape, precision and layout for all model inputs/outputs."""
        for name, metadata in self.inputs.items():
            self.logger.info(
                "\tInput layer: {}, shape: {}, precision: {}, layout: {}".format(
                    name, metadata.shape, metadata.precision, metadata.layout
                )
            )
        for name, metadata in self.outputs.items():
            self.logger.info(
                "\tOutput layer: {}, shape: {}, precision: {}, layout: {}".format(
                    name, metadata.shape, metadata.precision, metadata.layout
                )
            )

    def get_model(self):
        model = self.inference_adapter.get_model()
        model.set_rt_info(self.__model__, ["model_info", "model_type"])
        for name in self.parameters():
            model.set_rt_info(getattr(self, name), ["model_info", name])
        return model

    def save(self, xml_path, bin_path="", version="UNSPECIFIED"):
        import openvino.runtime as ov

        ov.serialize(self.get_model(), xml_path, bin_path, version)
