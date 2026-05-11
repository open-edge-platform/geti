#
# Copyright (C) 2020-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import logging as log
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from os import PathLike

    from numpy import ndarray

try:
    import openvino as ov
    from openvino import (
        AsyncInferQueue,
        Core,
        Dimension,
        OVAny,
        PartialShape,
        Type,
        get_version,
        layout_helpers,
    )
    from openvino.preprocess import ColorFormat, PrePostProcessor

    openvino_absent = False
except ImportError:
    openvino_absent = True

from .inference_adapter import InferenceAdapter, Metadata
from .utils import (
    Layout,
    crop_resize,
    get_rt_info_from_dict,
    load_parameters_from_onnx,
    range_scale_preprocess,
    repeat_channels_preprocess,
    resize_image,
    resize_image_letterbox,
    resize_image_with_aspect,
    setup_python_preprocessing_pipeline,
    window_preprocess,
)


def create_core() -> Core:
    if openvino_absent:
        msg = "The OpenVINO package is not installed"
        raise ImportError(msg)

    log.info("OpenVINO Runtime")
    log.info(f"\tbuild: {get_version()}")
    return Core()


def parse_devices(device_string: str) -> list[str]:
    colon_position = device_string.find(":")
    if colon_position != -1:
        device_type = device_string[:colon_position]
        if device_type == "HETERO" or device_type == "MULTI":
            comma_separated_devices = device_string[colon_position + 1 :]
            devices = comma_separated_devices.split(",")
            for device in devices:
                parenthesis_position = device.find(":")
                if parenthesis_position != -1:
                    device = device[:parenthesis_position]
            return devices
    return [device_string]


def parse_value_per_device(devices: set[str], values_string: str) -> dict[str, int]:
    """Format: <device1>:<value1>,<device2>:<value2> or just <value>"""
    values_string_upper = values_string.upper()
    result = {}
    device_value_strings = values_string_upper.split(",")
    for device_value_string in device_value_strings:
        device_value_list = device_value_string.split(":")
        if len(device_value_list) == 2:
            if device_value_list[0] in devices:
                result[device_value_list[0]] = int(device_value_list[1])
        elif len(device_value_list) == 1 and device_value_list[0] != "":
            for device in devices:
                result[device] = int(device_value_list[0])
        elif device_value_list[0] != "":
            msg = f"Unknown string format: {values_string}"
            raise RuntimeError(msg)
    return result


def get_user_config(
    flags_d: str,
    flags_nstreams: str,
    flags_nthreads: int | None = None,
) -> dict[str, str]:
    config = {}

    devices = set(parse_devices(flags_d))

    device_nstreams = parse_value_per_device(devices, flags_nstreams)
    for device in devices:
        if device == "CPU":  # CPU supports a few special performance-oriented keys
            # limit threading for CPU portion of inference
            if flags_nthreads:
                config["INFERENCE_NUM_THREADS"] = str(flags_nthreads)

            # for CPU execution, more throughput-oriented execution via streams
            config["NUM_STREAMS"] = str(device_nstreams[device]) if device in device_nstreams else "NUM_STREAMS_AUTO"
        elif device == "GPU":
            config["NUM_STREAMS"] = str(device_nstreams[device]) if device in device_nstreams else "NUM_STREAMS_AUTO"
            if "MULTI" in flags_d and "CPU" in devices:
                # multi-device execution with the CPU + GPU performs best with GPU throttling hint,
                # which releases another CPU thread (that is otherwise used by the GPU driver for active polling)
                config["GPU_PLUGIN_THROTTLE"] = "1"
    return config


class OpenvinoAdapter(InferenceAdapter):
    """Works with OpenVINO model"""

    def __init__(
        self,
        core: Core,
        model: str,
        weights_path: PathLike | None = None,
        model_parameters: dict[str, Any] = {},
        device: str = "CPU",
        plugin_config: dict[str, Any] | None = None,
        max_num_requests: int = 0,
        precision: str = "FP16",
        download_dir: PathLike | None = None,
        cache_dir: PathLike | None = None,
    ) -> None:
        """precision, download_dir and cache_dir are ignored if model is a path to a file"""
        self.core = core
        self.model_path = model
        self.device = device
        self.plugin_config = plugin_config
        self.max_num_requests = max_num_requests
        self.model_parameters = model_parameters
        self.model_parameters["input_layouts"] = Layout.parse_layouts(
            self.model_parameters.get("input_layouts", None),
        )
        self.is_onnx_file = False
        self.onnx_metadata = {}
        self.preprocessor = lambda arg: arg
        self.use_python_preprocessing = False

        if isinstance(self.model_path, (str, Path)):
            if Path(self.model_path).suffix == ".onnx" and weights_path:
                log.warning(
                    'For model in ONNX format should set only "model_path" parameter.'
                    'The "weights_path" will be omitted',
                )
            if Path(self.model_path).suffix == ".onnx" and not weights_path:
                try:
                    import onnx
                except ImportError:
                    msg = (
                        "Loading ONNX models requires the 'onnx' package. "
                        "Install it with: uv pip install openvino-model-api[onnx]"
                    )
                    raise ImportError(msg) from None

                self.is_onnx_file = True
                self.onnx_metadata = load_parameters_from_onnx(
                    onnx.load(self.model_path),
                )

        self.model_from_buffer = isinstance(self.model_path, bytes) and isinstance(
            weights_path,
            bytes,
        )
        model_from_file = not self.model_from_buffer and Path(self.model_path).is_file()
        if model_from_file or self.model_from_buffer:
            log.info(
                "Reading model {}".format(
                    "from buffer" if self.model_from_buffer else self.model_path,
                ),
            )
            self.model = core.read_model(self.model_path, weights_path)
            return

        msg = "Model must be bytes or a file"
        raise RuntimeError(msg)

    def reshape_dynamic_inputs(self) -> None:
        """For NPU devices, set static shape if the model has dynamic shapes"""
        for input in self.model.inputs:
            if input.partial_shape.is_dynamic:
                input_name = input.get_any_name()
                shape = get_input_shape(input)
                static_shape = []

                # Detect likely layout for 4D shapes
                is_nchw = False
                if len(shape) == 4 and not isinstance(shape[1], tuple) and shape[1] != -1 and shape[1] <= 4:
                    is_nchw = True

                for i, dim in enumerate(shape):
                    if isinstance(dim, tuple):
                        static_shape.append((dim[0] + dim[1]) // 2)
                    elif dim == -1:
                        if i == 0:
                            static_shape.append(1)
                        elif len(shape) == 4:
                            if is_nchw:
                                if i == 1:
                                    static_shape.append(3)
                                else:
                                    static_shape.append(224)
                            else:
                                if i == 3:
                                    static_shape.append(3)
                                else:
                                    static_shape.append(224)
                        else:
                            static_shape.append(1)
                    else:
                        static_shape.append(dim)

                log.info(
                    f"NPU: Reshaping input '{input_name}' from dynamic {shape} to static {static_shape}",
                )
                self.reshape_model({input_name: static_shape})

    def load_model(self) -> None:
        """Loads the model to the device specified in the constructor"""
        devices = parse_devices(self.device)
        if any("NPU" in dev.upper() for dev in devices) and self.model.is_dynamic():
            self.reshape_dynamic_inputs()

        self.compiled_model = self.core.compile_model(
            self.model,
            self.device,
            self.plugin_config,
        )
        self.async_queue = AsyncInferQueue(self.compiled_model, self.max_num_requests)
        if self.max_num_requests == 0:
            # +1 to use it as a buffer of the pipeline
            self.async_queue = AsyncInferQueue(
                self.compiled_model,
                len(self.async_queue) + 1,
            )

        log.info(
            "The model {} is loaded to {}".format(
                "from buffer" if self.model_from_buffer else self.model_path,
                self.device,
            ),
        )
        self.log_runtime_settings()

    def log_runtime_settings(self) -> None:
        devices = set(parse_devices(self.device))
        if "AUTO" not in devices:
            for device in devices:
                try:
                    nstreams = self.compiled_model.get_property(
                        device + "_THROUGHPUT_STREAMS",
                    )
                    log.info(f"\tDevice: {device}")
                    log.info(f"\t\tNumber of streams: {nstreams}")
                    if device == "CPU":
                        nthreads = self.compiled_model.get_property("CPU_THREADS_NUM")
                        log.info(
                            "\t\tNumber of threads: {}".format(
                                nthreads if int(nthreads) else "AUTO",
                            ),
                        )
                except RuntimeError:
                    pass
        log.info(f"\tNumber of model infer requests: {len(self.async_queue)}")

    def get_input_layers(self) -> dict[str, Metadata]:
        inputs = {}
        for input in self.model.inputs:
            input_shape = get_input_shape(input)
            input_layout = self.get_layout_for_input(input, input_shape)
            inputs[input.get_any_name()] = Metadata(
                input.get_names(),
                input_shape,
                input_layout,
                input.get_element_type().get_type_name(),
            )
        return self._get_meta_from_ngraph(inputs)

    def get_layout_for_input(
        self,
        input: ov.Output,
        shape: list[int] | tuple[int, int, int, int] | None = None,
    ) -> str:
        input_layout = ""
        if self.model_parameters["input_layouts"]:
            input_layout = Layout.from_user_layouts(
                input.get_names(),
                self.model_parameters["input_layouts"],
            )
        if not input_layout:
            if not layout_helpers.get_layout(input).empty:
                input_layout = Layout.from_openvino(input)
            else:
                input_layout = Layout.from_shape(
                    shape if shape is not None else input.shape,
                )
        return input_layout

    def get_output_layers(self) -> dict[str, Metadata]:
        outputs = {}
        for i, output in enumerate(self.model.outputs):
            output_shape = output.partial_shape.get_min_shape() if self.model.is_dynamic() else output.shape

            output_name = output.get_any_name() if output.get_names() else output
            outputs[output_name] = Metadata(
                output.get_names(),
                list(output_shape),
                precision=output.get_element_type().get_type_name(),
            )
        return self._get_meta_from_ngraph(outputs)

    def reshape_model(self, new_shape):
        new_shape = {
            name: PartialShape(
                [(Dimension(dim) if not isinstance(dim, tuple) else Dimension(dim[0], dim[1])) for dim in shape],
            )
            for name, shape in new_shape.items()
        }
        self.model.reshape(new_shape)

    def get_raw_result(self, request: ov.InferRequest) -> dict[str, ndarray]:
        return {key: request.get_tensor(key).data for key in self.get_output_layers()}

    def copy_raw_result(self, request):
        return {key: request.get_tensor(key).data.copy() for key in self.get_output_layers()}

    def infer_sync(self, dict_data: dict[str, ndarray]) -> dict[str, ndarray]:
        if self.use_python_preprocessing:
            for key in dict_data:
                dict_data[key] = self.preprocessor(dict_data[key])
        self.infer_request = self.async_queue[self.async_queue.get_idle_request_id()]
        self.infer_request.infer(dict_data)
        return self.get_raw_result(self.infer_request)

    def infer_async(self, dict_data, callback_data) -> None:
        if self.use_python_preprocessing:
            for key in dict_data:
                dict_data[key] = self.preprocessor(dict_data[key])
        self.async_queue.start_async(dict_data, callback_data)

    def set_callback(self, callback_fn: Callable):
        self.async_queue.set_callback(callback_fn)

    def is_ready(self) -> bool:
        return self.async_queue.is_ready()

    def await_all(self) -> None:
        self.async_queue.wait_all()

    def await_any(self) -> None:
        self.async_queue.get_idle_request_id()

    def _get_meta_from_ngraph(self, layers_info: dict[str, Metadata]) -> dict[str, Metadata]:
        for node in self.model.get_ordered_ops():
            layer_name = node.get_friendly_name()
            if layer_name not in layers_info:
                continue
            layers_info[layer_name].meta = node.get_attributes()
            layers_info[layer_name].type = node.get_type_name()
        return layers_info

    def operations_by_type(self, operation_type):
        layers_info = {}
        for node in self.model.get_ordered_ops():
            if node.get_type_name() == operation_type:
                layer_name = node.get_friendly_name()
                layers_info[layer_name] = Metadata(
                    type=node.get_type_name(),
                    meta=node.get_attributes(),
                )
        return layers_info

    def get_rt_info(self, path: list[str]) -> OVAny:
        """
        Gets an attribute value from OV.model_info structure.

        Args:
            path (list[str]): a suquence of tag names leading to the attribute.

        Returns:
            OVAny: attribute value wrapped into OVAny object.
        """
        if self.is_onnx_file:
            return get_rt_info_from_dict(self.onnx_metadata, path)
        return self.model.get_rt_info(path)

    def embed_preprocessing(  # noqa: C901
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
        input_dtype: str = "u8",
        intensity_mode: str = "none",
        intensity_max_value: float | None = None,
        intensity_window_center: float | None = None,
        intensity_window_width: float | None = None,
        intensity_percentile_low: float = 1.0,
        intensity_percentile_high: float = 99.0,
        intensity_scale_factor: float = 1.0,
        intensity_min_value: float = 0.0,
        intensity_repeat_channels: bool = False,
        input_frame_shape: tuple[int, int] | None = None,
    ) -> None:
        """
        Embeds preprocessing into the model, or sets up Python preprocessing for NPU devices.
        """
        # Check if we should use Python preprocessing for NPU devices
        devices = parse_devices(self.device)
        if any("NPU" in dev.upper() for dev in devices):
            self.preprocessor = setup_python_preprocessing_pipeline(
                layout=layout,
                resize_mode=resize_mode,
                interpolation_mode=interpolation_mode,
                target_shape=target_shape,
                pad_value=pad_value,
                dtype=dtype,
                brg2rgb=brg2rgb,
                mean=mean,
                scale=scale,
                input_idx=input_idx,
                intensity_mode=intensity_mode,
                intensity_max_value=intensity_max_value,
                intensity_window_center=intensity_window_center,
                intensity_window_width=intensity_window_width,
                intensity_percentile_low=intensity_percentile_low,
                intensity_percentile_high=intensity_percentile_high,
                intensity_scale_factor=intensity_scale_factor,
                intensity_min_value=intensity_min_value,
                intensity_repeat_channels=intensity_repeat_channels,
            )
            self.use_python_preprocessing = True
            input_name = self.model.inputs[input_idx].get_any_name()
            if layout == "NCHW":
                static_shape = [1, 3, target_shape[1], target_shape[0]]
            else:
                static_shape = [1, target_shape[1], target_shape[0], 3]
            self.reshape_model({input_name: static_shape})
            return

        ppp = PrePostProcessor(self.model)

        # Map input_dtype string to OV element type (also support legacy int/float dtype arg)
        _DTYPE_TO_OV = {"u8": Type.u8, "f32": Type.f32, "u16": Type.u16, "i16": Type.i16}
        if input_dtype in _DTYPE_TO_OV:
            ppp.input(input_idx).tensor().set_element_type(_DTYPE_TO_OV[input_dtype])
        elif dtype is int:
            ppp.input(input_idx).tensor().set_element_type(Type.u8)
        elif dtype is float:
            ppp.input(input_idx).tensor().set_element_type(Type.f32)

        ppp.input(input_idx).tensor().set_layout(ov.Layout("NHWC"))
        if intensity_repeat_channels:
            ppp.input(input_idx).preprocess().custom(
                repeat_channels_preprocess(),
            )
        else:
            ppp.input(input_idx).tensor().set_color_format(ColorFormat.BGR)

        INTERPOLATION_MODE_MAP = {
            "LINEAR": "linear",
            "CUBIC": "cubic",
            "NEAREST": "nearest",
        }

        RESIZE_MODE_MAP = {
            "crop": crop_resize,
            "standard": resize_image,
            "fit_to_window": resize_image_with_aspect,
            "fit_to_window_letterbox": resize_image_letterbox,
        }

        # Handle resize
        # Use static input shape when input_frame_shape is provided (avoids GPU
        # performance penalty from dynamic shapes).  Fall back to dynamic [-1, -1]
        # when the frame dimensions are unknown.
        if resize_mode and target_shape:
            if resize_mode in RESIZE_MODE_MAP:
                input_channels = 1 if intensity_repeat_channels else 3
                if input_frame_shape is not None:
                    input_shape = [1, input_frame_shape[0], input_frame_shape[1], input_channels]
                else:
                    input_shape = [1, -1, -1, input_channels]
                ppp.input(input_idx).tensor().set_shape(input_shape)
                ppp.input(input_idx).preprocess().custom(
                    RESIZE_MODE_MAP[resize_mode](
                        (target_shape[0], target_shape[1]),
                        INTERPOLATION_MODE_MAP[interpolation_mode],
                        pad_value,
                        input_dtype=input_dtype,
                    ),
                )

            else:
                msg = f"Upsupported resize type in model preprocessing: {resize_mode}"
                raise ValueError(msg)

        # Handle intensity scaling (embedded in OV graph for static modes)
        if intensity_mode == "scale_to_unit" and intensity_max_value is not None:
            ppp.input(input_idx).preprocess().convert_element_type(Type.f32)
            ppp.input(input_idx).preprocess().scale([intensity_max_value])
        elif intensity_mode == "window" and intensity_window_center is not None and intensity_window_width is not None:
            ppp.input(input_idx).preprocess().custom(
                window_preprocess(intensity_window_center, intensity_window_width),
            )
        elif intensity_mode == "range_scale":
            mx = float(intensity_max_value) if intensity_max_value is not None else 1e9
            ppp.input(input_idx).preprocess().custom(
                range_scale_preprocess(float(intensity_scale_factor), float(intensity_min_value), mx),
            )

        # Handle layout
        ppp.input(input_idx).model().set_layout(ov.Layout(layout))

        # Handle color format
        if brg2rgb:
            ppp.input(input_idx).preprocess().convert_color(ColorFormat.RGB)

        # Convert to float before normalization (skip if already done by intensity modes)
        if intensity_mode not in ("scale_to_unit", "window", "range_scale"):
            ppp.input(input_idx).preprocess().convert_element_type(Type.f32)

        if mean:
            ppp.input(input_idx).preprocess().mean(mean)
        if scale:
            ppp.input(input_idx).preprocess().scale(scale)

        self.model = ppp.build()
        self.load_model()

    def get_model(self):
        """Returns the openvino.Model object

        Returns:
            openvino.Model object
        """
        return self.model

    def update_model_info(self, model_info: dict[str, Any]):
        """
        Populates OV IR RT info with the given model info.

        Args:
            model_info (dict[str, Any]): a dict representing the serialized parameters.
        """
        for name in model_info:
            self.model.set_rt_info(model_info[name], ["model_info", name])

    def save_model(self, path: str, weights_path: str | None = None, version: str | None = None):
        """
        Saves OV model as two files: .xml (architecture) and .bin (weights).

        Args:
            path (str): path to save the model files (.xml and .bin).
            weights_path (str, optional): Optional path to save .bin if it differs from .xml path. Defaults to None.
            version (str, optional): Output IR model version (for instance, IR_V10). Defaults to None.
        """
        if weights_path is None:
            weights_path = ""
        if version is None:
            version = "UNSPECIFIED"

        ov.serialize(self.get_model(), path, weights_path, version)


def get_input_shape(input_tensor: ov.Output) -> list[int]:
    def string_to_tuple(string, casting_type=int):
        processed = string.replace(" ", "").replace("(", "").replace(")", "").split(",")
        processed = filter(lambda x: x, processed)
        return tuple(map(casting_type, processed)) if casting_type else tuple(processed)

    if not input_tensor.partial_shape.is_dynamic:
        return list(input_tensor.shape)
    ps = str(input_tensor.partial_shape)
    if ps[0] == "[" and ps[-1] == "]":
        ps = ps[1:-1]
    preprocessed = ps.replace("{", "(").replace("}", ")").replace("?", "-1")
    preprocessed = preprocessed.replace("(", "").replace(")", "")
    if ".." in preprocessed:
        shape_list = []
        for dim in preprocessed.split(","):
            if ".." in dim:
                shape_list.append(string_to_tuple(dim.replace("..", ",")))
            else:
                shape_list.append(int(dim))
        return shape_list
    return list(string_to_tuple(preprocessed))
