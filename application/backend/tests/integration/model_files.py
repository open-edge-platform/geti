# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Helpers to write model files on disk, as the training pipeline would export them."""

from pathlib import Path


def write_openvino_model(variant_dir: Path, confidence_threshold: float | None) -> None:
    """Write a minimal OpenVINO IR model, optionally carrying a confidence threshold in its rt_info."""
    import openvino as ov
    import openvino.opset14 as ops

    variant_dir.mkdir(parents=True, exist_ok=True)
    param = ops.parameter([1, 3], ov.Type.f32, name="input")
    model = ov.Model([ops.relu(param)], [param], name="tiny")  # pyrefly: ignore[no-matching-overload]
    if confidence_threshold is not None:
        model.set_rt_info(str(confidence_threshold), ["model_info", "confidence_threshold"])
    ov.save_model(model, variant_dir / "model.xml", compress_to_fp16=False)


def write_onnx_model(variant_dir: Path, confidence_threshold: float | None) -> None:
    """Write a minimal ONNX model, optionally carrying a confidence threshold in its metadata properties."""
    import onnx
    from onnx import TensorProto, helper

    variant_dir.mkdir(parents=True, exist_ok=True)
    graph = helper.make_graph(
        [helper.make_node("Relu", ["input"], ["output"])],
        "tiny",
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 3])],
        [helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 3])],
    )
    model = helper.make_model(graph)
    if confidence_threshold is not None:
        model.metadata_props.append(
            onnx.StringStringEntryProto(key="model_info confidence_threshold", value=str(confidence_threshold))
        )
    onnx.save(model, variant_dir / "model.onnx")
