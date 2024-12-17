#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations  # TODO: remove when Python3.9 support is dropped

import re
from typing import Any, Callable

import numpy as np

from .inference_adapter import InferenceAdapter, Metadata
from .utils import Layout, get_rt_info_from_dict


class OVMSAdapter(InferenceAdapter):
    """Inference adapter that allows working with models served by the OpenVINO Model Server"""

    def __init__(self, target_model: str):
        """
        Initializes OVMS adapter.

        Args:
            target_model (str): Model URL. Expected format: <address>:<port>/v2/models/<model_name>[:<model_version>]
        """
        import tritonclient.http as httpclient

        service_url, self.model_name, self.model_version = _parse_model_arg(
            target_model,
        )
        self.client = httpclient.InferenceServerClient(service_url)
        if not self.client.is_model_ready(self.model_name, self.model_version):
            msg = f"Requested model: {self.model_name}, version: {self.model_version} is not accessible"
            raise RuntimeError(msg)

        self.metadata = self.client.get_model_metadata(
            model_name=self.model_name,
            model_version=self.model_version,
        )
        self.inputs = self.get_input_layers()

    def get_input_layers(self) -> dict[str, Metadata]:
        """
        Retrieves information about remote model's inputs.

        Returns:
            dict[str, Metadata]: metadata for each input.
        """
        return {
            meta["name"]: Metadata(
                {meta["name"]},
                meta["shape"],
                Layout.from_shape(meta["shape"]),
                meta["datatype"],
            )
            for meta in self.metadata["inputs"]
        }

    def get_output_layers(self) -> dict[str, Metadata]:
        """
        Retrieves information about remote model's outputs.

        Returns:
            dict[str, Metadata]: metadata for each output.
        """
        return {
            meta["name"]: Metadata(
                {meta["name"]},
                shape=meta["shape"],
                precision=meta["datatype"],
            )
            for meta in self.metadata["outputs"]
        }

    def infer_sync(self, dict_data: dict) -> dict:
        """
        Performs the synchronous model inference. The infer is a blocking method.

        Args:
            dict_data (dict): data for each input layer.

        Returns:
            dict: model raw outputs.
        """
        inputs = _prepare_inputs(dict_data, self.inputs)
        raw_result = self.client.infer(
            model_name=self.model_name,
            model_version=self.model_version,
            inputs=inputs,
        )

        inference_results = {}
        for output in self.metadata["outputs"]:
            inference_results[output["name"]] = raw_result.as_numpy(output["name"])

        return inference_results

    def infer_async(self, dict_data: dict, callback_data: Any):
        """A stub method imitating async inference with a blocking call."""
        inputs = _prepare_inputs(dict_data, self.inputs)
        raw_result = self.client.infer(
            model_name=self.model_name,
            model_version=self.model_version,
            inputs=inputs,
        )
        inference_results = {}
        for output in self.metadata["outputs"]:
            inference_results[output["name"]] = raw_result.as_numpy(output["name"])

        self.callback_fn(inference_results, (lambda x: x, callback_data))

    def set_callback(self, callback_fn: Callable):
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

    def get_raw_result(self, infer_result: dict):
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

    def reshape_model(self, new_shape: dict):
        """OVMS adapter can not modify the remote model. This method raises an exception."""
        msg = "OVMSAdapter does not support model reshaping"
        raise NotImplementedError(msg)

    def get_rt_info(self, path: list[str]) -> Any:
        """Returns an attribute stored in model info."""
        return get_rt_info_from_dict(self.metadata["rt_info"], path)

    def update_model_info(self, model_info: dict[str, Any]):
        """OVMS adapter can not update the source model info. This method raises an exception."""
        msg = "OVMSAdapter does not support updating model info"
        raise NotImplementedError(msg)

    def save_model(self, path: str, weights_path: str | None = None, version: str | None = None):
        """OVMS adapter can not retrieve the source model. This method raises an exception."""
        msg = "OVMSAdapter does not support saving a model"
        raise NotImplementedError(msg)


_triton2np_precision = {
    "INT64": np.int64,
    "UINT64": np.uint64,
    "FLOAT": np.float32,
    "UINT32": np.uint32,
    "INT32": np.int32,
    "HALF": np.float16,
    "INT16": np.int16,
    "INT8": np.int8,
    "UINT8": np.uint8,
    "FP32": np.float32,
}


def _parse_model_arg(target_model: str):
    """Parses OVMS model URL."""
    if not isinstance(target_model, str):
        msg = "target_model must be str"
        raise TypeError(msg)
    # Expected format: <address>:<port>/models/<model_name>[:<model_version>]
    if not re.fullmatch(
        r"(\w+\.*\-*)*\w+:\d+\/v2/models\/[a-zA-Z0-9._-]+(\:\d+)*",
        target_model,
    ):
        msg = "invalid --model option format"
        raise ValueError(msg)
    service_url, _, _, model = target_model.split("/")
    model_spec = model.split(":")
    if len(model_spec) == 1:
        # model version not specified - use latest
        return service_url, model_spec[0], ""
    if len(model_spec) == 2:
        return service_url, model_spec[0], model_spec[1]
    msg = "Invalid target_model format"
    raise ValueError(msg)


def _prepare_inputs(dict_data: dict, inputs_meta: dict[str, Metadata]):
    """Converts raw model inputs into OVMS-specific representation."""
    import tritonclient.http as httpclient

    inputs = []
    for input_name, input_data in dict_data.items():
        if input_name not in inputs_meta:
            msg = "Input data does not match model inputs"
            raise ValueError(msg)
        input_info = inputs_meta[input_name]
        model_precision = _triton2np_precision[input_info.precision]
        if isinstance(input_data, np.ndarray) and input_data.dtype != model_precision:
            input_data = input_data.astype(model_precision)
        elif isinstance(input_data, list):
            input_data = np.array(input_data, dtype=model_precision)

        infer_input = httpclient.InferInput(
            input_name,
            input_data.shape,
            input_info.precision,
        )
        infer_input.set_data_from_numpy(input_data)
        inputs.append(infer_input)
    return inputs
