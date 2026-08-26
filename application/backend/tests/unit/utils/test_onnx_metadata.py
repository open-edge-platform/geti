# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import onnx
import pytest
from onnx import TensorProto, helper

from app.utils.onnx_metadata import read_onnx_metadata_attrs


def _write_onnx_model(path: Path, metadata: dict[str, str], num_weights: int = 1) -> Path:
    """Write an ONNX model carrying the given metadata properties, with weights preceding them in the file."""
    weights = helper.make_tensor("weights", TensorProto.FLOAT, [num_weights], [1.0] * num_weights)
    graph = helper.make_graph(
        [helper.make_node("Add", ["input", "weights"], ["output"])],
        "test-graph",
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, [num_weights])],
        [helper.make_tensor_value_info("output", TensorProto.FLOAT, [num_weights])],
        initializer=[weights],
    )
    model = helper.make_model(graph)
    for key, value in metadata.items():
        model.metadata_props.append(onnx.StringStringEntryProto(key=key, value=value))
    onnx.save(model, path)
    return path


class TestReadOnnxMetadataAttrs:
    def test_read_requested_keys(self, tmp_path: Path):
        model_path = _write_onnx_model(
            tmp_path / "model.onnx",
            metadata={
                "model_info confidence_threshold": "0.35",
                "model_info model_type": "ssd",
                "model_info labels": "cat dog",
            },
        )

        attrs = read_onnx_metadata_attrs(model_path, keys=["model_info confidence_threshold", "model_info labels"])

        assert attrs == {"model_info confidence_threshold": "0.35", "model_info labels": "cat dog"}

    def test_missing_keys_are_omitted(self, tmp_path: Path):
        model_path = _write_onnx_model(tmp_path / "model.onnx", metadata={"model_info model_type": "ssd"})

        attrs = read_onnx_metadata_attrs(model_path, keys=["model_info confidence_threshold", "model_info model_type"])

        assert attrs == {"model_info model_type": "ssd"}

    def test_model_without_metadata(self, tmp_path: Path):
        model_path = _write_onnx_model(tmp_path / "model.onnx", metadata={})

        assert read_onnx_metadata_attrs(model_path, keys=["model_info confidence_threshold"]) == {}

    def test_no_requested_keys(self, tmp_path: Path):
        model_path = _write_onnx_model(tmp_path / "model.onnx", metadata={"model_info model_type": "ssd"})

        assert read_onnx_metadata_attrs(model_path, keys=[]) == {}

    def test_metadata_read_without_loading_the_graph(self, tmp_path: Path):
        """A large graph must not affect the read: only the metadata section is decoded."""
        model_path = _write_onnx_model(
            tmp_path / "model.onnx",
            metadata={"model_info confidence_threshold": "0.35"},
            num_weights=1_000_000,
        )
        assert model_path.stat().st_size > 4_000_000

        attrs = read_onnx_metadata_attrs(model_path, keys=["model_info confidence_threshold"])

        assert attrs == {"model_info confidence_threshold": "0.35"}

    def test_matches_the_onnx_library(self, tmp_path: Path):
        metadata = {"model_info confidence_threshold": "0.025", "model_info tile_size": "512"}
        model_path = _write_onnx_model(tmp_path / "model.onnx", metadata=metadata)

        attrs = read_onnx_metadata_attrs(model_path, keys=metadata.keys())

        reference = {prop.key: prop.value for prop in onnx.load(model_path).metadata_props}
        assert attrs == reference

    def test_missing_file(self, tmp_path: Path):
        with pytest.raises(OSError):
            read_onnx_metadata_attrs(tmp_path / "missing.onnx", keys=["model_info confidence_threshold"])

    def test_malformed_file(self, tmp_path: Path):
        model_path = tmp_path / "model.onnx"
        model_path.write_bytes(bytes([0x3F, 0xFF, 0xFF]))  # field 7, unsupported wire type 7

        with pytest.raises(ValueError, match="Unsupported protobuf wire type"):
            read_onnx_metadata_attrs(model_path, keys=["model_info confidence_threshold"])
