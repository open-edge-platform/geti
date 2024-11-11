#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import re
from typing import Any

import numpy as np

from .inference_adapter import InferenceAdapter, Metadata
from .utils import Layout


class OVMSAdapter(InferenceAdapter):
    """Class that allows working with models served by the OpenVINO Model Server"""

    def __init__(self, target_model: str):
        """Expected format: <address>:<port>/models/<model_name>[:<model_version>]"""
        import ovmsclient

        service_url, self.model_name, self.model_version = _parse_model_arg(
            target_model,
        )
        self.client = ovmsclient.make_grpc_client(url=service_url)
        _verify_model_available(self.client, self.model_name, self.model_version)

        self.metadata = self.client.get_model_metadata(
            model_name=self.model_name,
            model_version=self.model_version,
        )

    def get_input_layers(self):
        return {
            name: Metadata(
                {name},
                meta["shape"],
                Layout.from_shape(meta["shape"]),
                _tf2ov_precision.get(meta["dtype"], meta["dtype"]),
            )
            for name, meta in self.metadata["inputs"].items()
        }

    def get_output_layers(self):
        return {
            name: Metadata(
                {name},
                shape=meta["shape"],
                precision=_tf2ov_precision.get(meta["dtype"], meta["dtype"]),
            )
            for name, meta in self.metadata["outputs"].items()
        }

    def infer_sync(self, dict_data):
        inputs = _prepare_inputs(dict_data, self.metadata["inputs"])
        raw_result = self.client.predict(
            inputs,
            model_name=self.model_name,
            model_version=self.model_version,
        )
        # For models with single output ovmsclient returns ndarray with results,
        # so the dict must be created to correctly implement interface.
        if isinstance(raw_result, np.ndarray):
            output_name = next(iter(self.metadata["outputs"].keys()))
            return {output_name: raw_result}
        return raw_result

    def infer_async(self, dict_data, callback_data):
        inputs = _prepare_inputs(dict_data, self.metadata["inputs"])
        raw_result = self.client.predict(
            inputs,
            model_name=self.model_name,
            model_version=self.model_version,
        )
        # For models with single output ovmsclient returns ndarray with results,
        # so the dict must be created to correctly implement interface.
        if isinstance(raw_result, np.ndarray):
            output_name = list(self.metadata["outputs"].keys())[0]
            raw_result = {output_name: raw_result}
        self.callback_fn(raw_result, (lambda x: x, callback_data))

    def set_callback(self, callback_fn):
        self.callback_fn = callback_fn

    def is_ready(self):
        return True

    def load_model(self):
        pass

    def get_model(self):
        """Return the reference to the GrpcClient."""
        return self.client

    def await_all(self):
        pass

    def await_any(self):
        pass

    def get_raw_result(self, infer_result):
        pass

    def embed_preprocessing(
        self,
        layout,
        resize_mode: str,
        interpolation_mode,
        target_shape,
        pad_value,
        dtype=type(int),
        brg2rgb=False,
        mean=None,
        scale=None,
        input_idx=0,
    ):
        pass

    def reshape_model(self, new_shape):
        raise NotImplementedError

    def get_rt_info(self, path):
        msg = "OVMSAdapter does not support RT info getting"
        raise NotImplementedError(msg)

    def update_model_info(self, model_info: dict[str, Any]):
        msg = "OVMSAdapter does not support updating model info"
        raise NotImplementedError(msg)

    def save_model(self, path: str, weights_path: str = "", version: str = "UNSPECIFIED"):
        msg = "OVMSAdapter does not support saving a model"
        raise NotImplementedError(msg)


_tf2ov_precision = {
    "DT_INT64": "I64",
    "DT_UINT64": "U64",
    "DT_FLOAT": "FP32",
    "DT_UINT32": "U32",
    "DT_INT32": "I32",
    "DT_HALF": "FP16",
    "DT_INT16": "I16",
    "DT_INT8": "I8",
    "DT_UINT8": "U8",
}


_tf2np_precision = {
    "DT_INT64": np.int64,
    "DT_UINT64": np.uint64,
    "DT_FLOAT": np.float32,
    "DT_UINT32": np.uint32,
    "DT_INT32": np.int32,
    "DT_HALF": np.float16,
    "DT_INT16": np.int16,
    "DT_INT8": np.int8,
    "DT_UINT8": np.uint8,
}


def _parse_model_arg(target_model: str):
    if not isinstance(target_model, str):
        msg = "target_model must be str"
        raise TypeError(msg)
    # Expected format: <address>:<port>/models/<model_name>[:<model_version>]
    if not re.fullmatch(
        r"(\w+\.*\-*)*\w+:\d+\/models\/[a-zA-Z0-9._-]+(\:\d+)*",
        target_model,
    ):
        msg = "invalid --model option format"
        raise ValueError(msg)
    service_url, _, model = target_model.split("/")
    model_spec = model.split(":")
    if len(model_spec) == 1:
        # model version not specified - use latest
        return service_url, model_spec[0], 0
    if len(model_spec) == 2:
        return service_url, model_spec[0], int(model_spec[1])
    msg = "invalid target_model format"
    raise ValueError(msg)


def _verify_model_available(client, model_name, model_version):
    import ovmsclient

    version = "latest" if model_version == 0 else model_version
    try:
        model_status = client.get_model_status(model_name, model_version)
    except ovmsclient.ModelNotFoundError as e:
        msg = f"Requested model: {model_name}, version: {version} has not been found"
        raise RuntimeError(msg) from e
    target_version = max(model_status.keys())
    version_status = model_status[target_version]
    if version_status["state"] != "AVAILABLE" or version_status["error_code"] != 0:
        msg = f"Requested model: {model_name}, version: {version} is not in available state"
        raise RuntimeError(msg)


def _prepare_inputs(dict_data, inputs_meta):
    inputs = {}
    for input_name, input_data in dict_data.items():
        if input_name not in inputs_meta:
            msg = "Input data does not match model inputs"
            raise ValueError(msg)
        input_info = inputs_meta[input_name]
        model_precision = _tf2np_precision[input_info["dtype"]]
        if isinstance(input_data, np.ndarray) and input_data.dtype != model_precision:
            input_data = input_data.astype(model_precision)
        elif isinstance(input_data, list):
            input_data = np.array(input_data, dtype=model_precision)
        inputs[input_name] = input_data
    return inputs
