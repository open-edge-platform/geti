#
# Copyright (C) 2020-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import logging as log
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, NoReturn, Type

from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.adapters.onnx_adapter import ONNXRuntimeAdapter
from model_api.adapters.openvino_adapter import (
    OpenvinoAdapter,
    create_core,
    get_user_config,
)
from model_api.adapters.ovms_adapter import OVMSAdapter
from model_api.metrics import PerformanceMetrics
from model_api.models.parameters import ParameterDescriptor

if TYPE_CHECKING:
    from os import PathLike

    from numpy import ndarray


class WrapperError(Exception):
    """The class for errors occurred in Model API wrappers"""

    def __init__(self, wrapper_name, message) -> None:
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
        params (ParameterDescriptor): provides attribute-style access to model parameters
    """

    __model__: str = "Model"
    params = ParameterDescriptor()  # Class-level descriptor

    def __init__(self, inference_adapter: InferenceAdapter, configuration: dict = {}, preload: bool = False) -> None:
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
        self.perf = PerformanceMetrics()
        self.inference_adapter = inference_adapter
        if isinstance(
            self.inference_adapter,
            ONNXRuntimeAdapter,
        ) and self.__model__ not in {
            "Classification",
            "MaskRCNN",
            "SSD",
            "Segmentation",
        }:
            self.raise_error(
                "ONNXRuntimeAdapter is only supported for Classification, MaskRCNN, SSD, and Segmentation wrappers",
            )

        self.inputs = self.inference_adapter.get_input_layers()
        self.outputs = self.inference_adapter.get_output_layers()
        self._parameters_cache: dict | None = None
        self._load_config(configuration)
        self.model_loaded = False
        if preload:
            self.load()
        self.callback_fn = lambda _: None
        # params is now a class-level descriptor, no need to instantiate

    def get_param(self, name: str) -> Any:
        """Gets a parameter value, either from instance attribute (if set by config) or from parameter default.

        Args:
            name (str): parameter name

        Returns:
            Any: parameter value
        """
        if self._parameters_cache is None:
            self._parameters_cache = self.parameters()
        if name in self._parameters_cache:
            if hasattr(self, f"_{name}"):
                return getattr(self, f"_{name}")
            if hasattr(self, name):
                return getattr(self, name)
            return self._parameters_cache[name].default_value
        return self.raise_error(f"Parameter '{name}' not found")

    def get_cached_parameters(self) -> dict[str, Any]:
        """Get cached parameters, initializing cache if needed.

        Returns:
            dict: Dictionary of parameter definitions
        """
        if self._parameters_cache is None:
            self._parameters_cache = self.parameters()
        return self._parameters_cache

    def get_model(self) -> Any:
        """
        Returns underlying adapter-specific model.

        Returns:
            Any: Model object.
        """
        return self.inference_adapter.get_model()

    def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Returns performance metrics of the model.

        Returns:
            PerformanceMetrics: Performance metrics object.
        """
        return self.perf

    @classmethod
    def get_model_class(cls, name: str) -> Type:
        """
        Retrieves a wrapper class by a given wrapper name.

        Args:
            name (str): Wrapper name.

        Returns:
            Type: Model class.
        """
        subclasses = [subclass for subclass in cls.get_subclasses() if subclass.__model__]
        if cls.__model__:
            subclasses.append(cls)
        for subclass in subclasses:
            if name.lower() == subclass.__model__.lower():
                return subclass
        return cls.raise_error(
            f"There is no model with name {name} in list: {', '.join([subclass.__model__ for subclass in subclasses])}",
        )

    @classmethod
    def create_model(
        cls,
        model: str | InferenceAdapter,
        model_type: Any | None = None,
        configuration: dict[str, Any] = {},
        preload: bool = True,
        core: Any | None = None,
        weights_path: PathLike | None = None,
        adaptor_parameters: dict[str, Any] = {},
        device: str = "AUTO",
        nstreams: str = "1",
        nthreads: int | None = None,
        max_num_requests: int = 0,
        precision: str = "FP16",
        download_dir: PathLike | None = None,
        cache_dir: PathLike | None = None,
    ) -> Any:
        """Create an instance of the Model API model

        Args:
            model (str| InferenceAdapter): model name from OpenVINO Model Zoo, path to model, OVMS URL, or an adapter
            configuration (:obj:`dict`, optional): dictionary of model config with model properties, for example
                confidence_threshold, labels
            model_type (:obj:`str`, optional): name of model wrapper to create (e.g. "ssd")
            preload (:obj:`bool`, optional): whether to call load_model(). Can be set to false to reshape model before
                loading.
            core (optional): openvino.Core instance, passed to OpenvinoAdapter
            weights_path (:obj:`str`, optional): path to .bin file with model weights
            adaptor_parameters (:obj:`dict`, optional): parameters of ModelAdaptor
            device (:obj:`str`, optional): name of OpenVINO device (e.g. "CPU, GPU")
            nstreams (:obj:`int`, optional): number of inference streams
            nthreads (:obj:`int`, optional): number of threads to use for inference on CPU
            max_num_requests (:obj:`int`, optional): number of infer requests for asynchronous inference
            precision (:obj:`str`, optional): inference precision (e.g. "FP16")
            download_dir (:obj:`str`, optional): directory where to store downloaded models
            cache_dir (:obj:`str`, optional): directory where to store compiled models to reduce the load time before
                the inference.

        Returns:
            Model object
        """
        inference_adapter: InferenceAdapter
        if isinstance(model, InferenceAdapter):
            inference_adapter = model
        elif isinstance(model, str) and OVMSAdapter.is_ovms_model(model):
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
            try:
                model_type = inference_adapter.get_rt_info(
                    ["model_info", "model_type"],
                ).astype(str)
            except RuntimeError:
                model_type = configuration.get("model_type", cls.detect_model_type(inference_adapter))
        Model = cls.get_model_class(model_type)
        return Model(inference_adapter, configuration, preload)

    @classmethod
    def from_pretrained(
        cls,
        pretrained_model_name_or_path: str,
        *,
        # Hugging Face Hub parameters
        cache_dir: str | PathLike | None = None,
        force_download: bool = False,
        local_files_only: bool = False,
        token: str | bool | None = None,
        revision: str | None = None,
        local_dir: str | PathLike | None = None,
        subfolder: str | None = None,
        repo_type: str = "model",
        filename: str | None = None,
        # create_model parameters
        model_type: Any | None = None,
        configuration: dict[str, Any] = {},
        preload: bool = True,
        core: Any | None = None,
        weights_path: PathLike | None = None,
        adaptor_parameters: dict[str, Any] = {},
        device: str = "AUTO",
        nstreams: str = "1",
        nthreads: int | None = None,
        max_num_requests: int = 0,
        precision: str = "FP16",
    ) -> Any:
        """Load a model from a Hugging Face Hub repository.

        Downloads the model files from the given Hugging Face repository and
        creates a Model API wrapper using :meth:`create_model`.  Supports
        private repositories via *token* authentication and all standard
        Hugging Face download options.

        Args:
            pretrained_model_name_or_path: Hugging Face repository identifier (e.g. `user/model-name`).
            cache_dir: Custom Hugging Face cache directory.
            force_download: Re-download even if the files are cached.
            local_files_only: Only use locally cached files; error if the requested files are not available.
            token: Authentication token for private repos.  `True` reads from the cached HF login.
            revision: Git revision — branch, tag, or full-length commit hash.
            local_dir: Download files into this local directory with their original layout.
            subfolder: Subfolder inside the repository to look for the model.
            repo_type: Repository type (`model`, `dataset`, or `space`).  Defaults to `model`.
            filename: Model API-specific parameter for selecting a specific model file to download (e.g. `model.xml`).
                When omitted the repository is scanned for `xml` / `.onnx` files automatically.
            model_type: name of model wrapper to create (e.g. `ssd`).  Detected automatically when omitted.
            configuration: dictionary of model config with model properties, e.g. confidence_threshold, labels.
            preload: Whether to load the model onto the device immediately.
            core: `openvino.Core` instance, passed to `OpenvinoAdapter`.
            weights_path: explicit path to `.bin` weights file.
            adaptor_parameters: extra parameters for the inference adapter.
            device: OpenVINO device name (e.g. `CPU`, `GPU`, `AUTO`).
            nstreams: Number of inference streams.
            nthreads: Number of CPU threads.
            max_num_requests: Maximum number of asynchronous inference requests.
            precision: Inference precision (e.g. `FP16`).

        Returns:
            A fully initialized Model API wrapper.

        Raises:
            ImportError: If `huggingface_hub` is not installed.
            FileNotFoundError: If no model file is found in the repository.
            huggingface_hub.errors.RepositoryNotFoundError: If the repository does not exist or is not accessible.
            ValueError: If multiple model files are found and *filename* is
                not specified.
        """
        from model_api.utils.hf_hub_helper import download_from_hf

        model_path = download_from_hf(
            repo_id=pretrained_model_name_or_path,
            filename=filename,
            revision=revision,
            token=token,
            cache_dir=cache_dir,
            local_dir=local_dir,
            force_download=force_download,
            local_files_only=local_files_only,
            subfolder=subfolder,
            repo_type=repo_type,
        )

        return cls.create_model(
            model=str(model_path),
            model_type=model_type,
            configuration=configuration,
            preload=preload,
            core=core,
            weights_path=weights_path,
            adaptor_parameters=adaptor_parameters,
            device=device,
            nstreams=nstreams,
            nthreads=nthreads,
            max_num_requests=max_num_requests,
            precision=precision,
        )

    @classmethod
    def detect_model_type(cls, inference_adapter) -> str:
        """Detects model type on available information"""
        input_layers = inference_adapter.get_input_layers()
        output_layers = inference_adapter.get_output_layers()

        # Check for Anomalib model pattern: 1 input and specific output layer names
        if len(input_layers) == 1 and len(output_layers) == 4:
            expected_outputs = {"pred_score", "pred_label", "anomaly_map", "pred_mask"}
            actual_outputs = set(output_layers.keys())
            if expected_outputs == actual_outputs:
                return "AnomalyDetection"

        return "uknown"

    @classmethod
    def get_subclasses(cls) -> list[Any]:
        """Retrieves all the subclasses of the model class given."""
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(subclass.get_subclasses())
        return all_subclasses

    @classmethod
    def available_wrappers(cls) -> list[str]:
        """
        Prepares a list of all discoverable wrapper names
        (including custom ones inherited from the core wrappers).
        """
        available_classes = [cls] if cls.__model__ else []
        available_classes.extend(cls.get_subclasses())
        return [subclass.__model__ for subclass in available_classes if subclass.__model__]

    @classmethod
    def parameters(cls) -> dict[str, Any]:
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
        return {}

    def _load_config(self, config: dict[str, Any]) -> None:
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
                    self.inference_adapter.get_rt_info(["model_info", name]).astype(str),
                )
                self.__setattr__(f"_{name}", value)
            except RuntimeError as error:
                missing_rt_info = "Cannot get runtime attribute. Path to runtime attribute is incorrect." in str(error)
                if not missing_rt_info:
                    raise

        for name, value in config.items():
            if value is None:
                continue
            if name in parameters:
                errors = parameters[name].validate(value)
                if errors:
                    self.logger.error(f'Error with "{name}" parameter:')
                    for _error in errors:
                        self.logger.error(f"\t{_error}")
                    self.raise_error("Incorrect user configuration")
                value = parameters[name].get_value(value)
                self.__setattr__(f"_{name}", value)
            else:
                self.logger.warning(
                    f'The parameter "{name}" not found in {self.__model__} wrapper, will be omitted',
                )

    @classmethod
    def raise_error(cls, message) -> NoReturn:
        """Raises the WrapperError.

        Args:
            message (str): error message to be shown in the following format:
              "WrapperName: message"
        """
        raise WrapperError(cls.__model__, message)

    def base_preprocess(self, inputs):
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

    def preprocess(self, dict_inputs, meta):
        """Interface for preprocess hook.

        Args:
            dict_inputs: preprocessed data
            meta: input metadata

        Returns:
            - the preprocessed data
            - the input metadata
        """
        return dict_inputs, meta

    def postprocess(self, outputs: dict[str, Any], meta: dict[str, Any]):
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

    def _check_io_number(
        self,
        number_of_inputs: int | tuple[int, ...],
        number_of_outputs: int | tuple[int, ...],
    ) -> None:
        """Checks whether the number of model inputs/outputs is supported.

        Args:
            number_of_inputs (int, Tuple(int)): number of inputs supported by wrapper.
              Use -1 to omit the check
            number_of_outputs (int, Tuple(int)): number of outputs supported by wrapper.
              Use -1 to omit the check

        Raises:
            WrapperError: if the model has unsupported number of inputs/outputs
        """
        if isinstance(number_of_inputs, int):
            if len(self.inputs) != number_of_inputs and number_of_inputs != -1:
                self.raise_error(
                    f"Expected {number_of_inputs} input blob {'s' if number_of_inputs != 1 else ''}, "
                    f"but {len(self.inputs)} found: {', '.join(self.inputs)}",
                )
        elif len(self.inputs) not in number_of_inputs:
            self.raise_error(
                f"Expected {', '.join(str(n) for n in number_of_inputs[:-1])} or "
                f"{int(number_of_inputs[-1])} input blobs, but {len(self.inputs)} found: {', '.join(self.inputs)}",
            )

        if isinstance(number_of_outputs, int):
            if len(self.outputs) != number_of_outputs and number_of_outputs != -1:
                self.raise_error(
                    f"Expected {number_of_outputs} output blob {'s' if number_of_outputs != 1 else ''}, "
                    f"but {len(self.outputs)} found: {', '.join(self.outputs)}",
                )
        elif len(self.outputs) not in number_of_outputs:
            self.raise_error(
                f"Expected {', '.join(str(n) for n in number_of_outputs[:-1])} or "
                f"{int(number_of_outputs[-1])} output blobs, "
                f"but {len(self.outputs)} found: {', '.join(self.outputs)}",
            )

    def __call__(self, inputs: ndarray):
        """Applies preprocessing, synchronous inference, postprocessing routines while one call.

        Args:
            inputs: raw input data, the data type is defined by wrapper

        Returns:
            - postprocessed data in the format defined by wrapper
        """
        self.perf.total_time.update()
        self.perf.preprocess_time.update()
        dict_data, input_meta = self.base_preprocess(inputs)
        self.perf.preprocess_time.update()
        self.perf.inference_time.update()
        raw_result = self.infer_sync(dict_data)
        self.perf.inference_time.update()
        self.perf.postprocess_time.update()
        result = self.postprocess(raw_result, input_meta)
        self.perf.postprocess_time.update()
        self.perf.total_time.update()
        return result

    def infer_batch(self, inputs: list) -> list[Any]:
        """Applies preprocessing, asynchronous inference, postprocessing routines to a collection of inputs.

        Args:
            inputs (list): a list of inputs for inference

        Returns:
            list: a list of inference results
        """
        self.await_all()

        completed_results = {}

        @contextmanager
        def tmp_callback():
            old_callback = self.callback_fn

            def batch_infer_callback(result, id):
                completed_results[id] = result

            try:
                self.set_callback(batch_infer_callback)
                yield
            finally:
                self.set_callback(old_callback)

        with tmp_callback():
            for i, input in enumerate(inputs):
                self.infer_async(input, i)
            self.await_all()

        return [completed_results[i] for i in range(len(inputs))]

    def load(self, force: bool = False) -> None:
        """
        Prepares the model to be executed by the inference adapter.

        Args:
            force (bool, optional): Forces the process even if the model is ready. Defaults to False.
        """
        if not self.model_loaded or force:
            self.model_loaded = True
            self.perf.load_time.update()
            self.inference_adapter.load_model()
            self.perf.load_time.update()

    def reshape(self, new_shape: dict):
        """
        Reshapes the model inputs to fit the new input shape.

        Args:
            new_shape (dict): a dictionary with inputs names as keys and
            list of new shape as values in the following format.
        """
        if self.model_loaded:
            self.logger.warning(
                f"{self.__model__}: the model already loaded to device, ",
                "should be reloaded after reshaping.",
            )
            self.model_loaded = False
        self.inference_adapter.reshape_model(new_shape)
        self.inputs = self.inference_adapter.get_input_layers()
        self.outputs = self.inference_adapter.get_output_layers()

    def infer_sync(self, dict_data: dict[str, ndarray]) -> dict[str, ndarray]:
        """
        Performs the synchronous model inference. The infer is a blocking method.
        See InferenceAdapter documentation for details.
        """
        if not self.model_loaded:
            self.raise_error(
                "The model is not loaded to the device. Please, create the wrapper "
                "with preload=True option or call load() method before infer_sync()",
            )
        return self.inference_adapter.infer_sync(dict_data)

    def infer_async_raw(self, dict_data: dict, callback_data: Any):
        """
        Runs asynchronous inference on raw data skipping preprocess() call.

        Args:
            dict_data (dict): data to be passed to the model
            callback_data (Any): data to be passed to the callback alongside with inference results.
        """
        if not self.model_loaded:
            self.raise_error(
                "The model is not loaded to the device. Please, create the wrapper "
                "with preload=True option or call load() method before infer_async()",
            )
        self.inference_adapter.infer_async(dict_data, callback_data)

    def infer_async(self, input_data: dict, user_data: Any):
        """
        Runs asynchronous model inference.

        Args:
            input_data (dict): Input dict containing model input name as keys and data object as values.
            user_data (Any): data to be passed to the callback alongside with inference results.
        """

        if not self.model_loaded:
            self.raise_error(
                "The model is not loaded to the device. Please, create the wrapper "
                "with preload=True option or call load() method before infer_async()",
            )
        total_token = object()
        inference_token = object()
        self.perf.total_time.update(total_token)
        self.perf.preprocess_time.update()
        dict_data, meta = self.base_preprocess(input_data)
        self.perf.preprocess_time.update()
        self.perf.inference_time.update(inference_token)
        self.inference_adapter.infer_async(
            dict_data,
            (
                self,
                meta,
                self.inference_adapter.get_raw_result,
                self.postprocess,
                self.callback_fn,
                user_data,
                total_token,
                inference_token,
            ),
        )

    @staticmethod
    def _process_callback(request, callback_data: Any):
        """
        A wrapper for async inference callback.
        """
        total_token = None
        inference_token = None
        if len(callback_data) >= 8:
            (
                model,
                meta,
                get_result_fn,
                postprocess_fn,
                callback_fn,
                user_data,
                total_token,
                inference_token,
            ) = callback_data
        else:
            model, meta, get_result_fn, postprocess_fn, callback_fn, user_data = callback_data
        raw_result = get_result_fn(request)
        if inference_token is not None:
            model.perf.inference_time.update(inference_token)
        else:
            model.perf.inference_time.update()
        model.perf.postprocess_time.update()
        result = postprocess_fn(raw_result, meta)
        model.perf.postprocess_time.update()
        if total_token is not None:
            model.perf.total_time.update(total_token)
        else:
            model.perf.total_time.update()
        callback_fn(result, user_data)

    def set_callback(self, callback_fn: Callable):
        """
        Sets callback that grabs results of async inference.

        Args:
            callback_fn (Callable): _description_
        """
        self.callback_fn = callback_fn
        self.inference_adapter.set_callback(Model._process_callback)

    def is_ready(self):
        """Checks if model is ready for async inference."""
        return self.inference_adapter.is_ready()

    def await_all(self):
        """Waits for all async inference requests to be completed."""
        self.inference_adapter.await_all()

    def await_any(self):
        """Waits for model to be available for an async infer request."""
        self.inference_adapter.await_any()

    def log_layers_info(self):
        """Prints the shape, precision and layout for all model inputs/outputs."""
        for name, metadata in self.inputs.items():
            self.logger.info(
                f"\tInput layer: {name}, shape: {metadata.shape}, "
                f"precision: {metadata.precision}, layout: {metadata.layout}",
            )
        for name, metadata in self.outputs.items():
            self.logger.info(
                f"\tOutput layer: {name}, shape: {metadata.shape}, "
                f"precision: {metadata.precision}, layout: {metadata.layout}",
            )

    def save(self, path: str, weights_path: str | None = None, version: str | None = None):
        """
        Serializes model to the filesystem. Model format depends in the InferenceAdapter being used.

        Args:
            path (str): Path to write the resulting model.
            weights_path (str | None): Optional path to save weights if they are stored separately.
            version (str | None): Optional model version.
        """
        model_info = {
            "model_type": self.__model__,
        }
        for name in self.parameters():
            value = getattr(self.params, name)
            if value is not None:
                model_info[name] = value

        self.inference_adapter.update_model_info(model_info)
        self.inference_adapter.save_model(path, weights_path, version)
