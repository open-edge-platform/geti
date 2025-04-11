# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel as _BaseModel


class BaseModel(_BaseModel):
    output_dir: ClassVar[str]

    @classmethod
    def from_filepath(cls, filepath: str | Path) -> BaseModel:
        filepath = str(filepath) if isinstance(filepath, Path) else filepath
        filename = os.path.basename(filepath).lower()
        filename, ext = os.path.splitext(filename)

        splited = [*filename.split("_"), ext]

        expect_n_fields = len(cls.model_fields)
        actual_n_fields = len(splited)

        if actual_n_fields != expect_n_fields:
            msg = (
                f"Required number of fields should be {actual_n_fields}, "
                f"but the query has {expect_n_fields}. "
                f"The given filename is {os.path.basename(filepath)}"
            )
            raise ValueError(msg)

        return cls(**dict(zip(cls.model_fields.keys(), splited)))

    def to_object_storage_path(self) -> str:
        fname = ""
        for key, value in self.model_dump().items():
            if fname == "" or key == "ext":
                fname += value
            else:
                fname += f"_{value}"

        return os.path.join(self.output_dir, fname)


class ModelArtifact(BaseModel):
    output_dir: ClassVar[str] = os.path.join("outputs", "models")

    prefix: Literal["model"]
    precision: Literal["fp32", "fp16", "int8-nncf", "int8-pot"]
    with_xai: Literal["xai", "non-xai"]
    ext: Literal[".pth", ".xml", ".bin", ".onnx"]


class ExportableCodeArtifact(BaseModel):
    output_dir: ClassVar[str] = os.path.join("outputs", "exportable_codes")

    prefix: Literal["exportable-code"]
    precision: Literal["fp32", "fp16", "int8-nncf", "int8-pot"]
    with_xai: Literal["xai", "non-xai"]
    ext: Literal[".whl"]


class OptimizedConfigArtifact(BaseModel):
    output_dir: ClassVar[str] = os.path.join("outputs", "configurations")

    prefix: Literal["optimized-config"]
    ext: Literal[".json"]


class PerformanceArtifact(BaseModel):
    output_dir: ClassVar[str] = os.path.join("outputs", "models")

    prefix: Literal["performance-json"]
    ext: Literal[".bin"]


class TileClassifierArtifact(BaseModel):
    """This artifact is required only for OTX v1 tiled detection models."""

    output_dir: ClassVar[str] = os.path.join("outputs", "models")

    prefix: Literal["tile-classifier"]
    precision: Literal["fp32", "fp16", "int8-nncf", "int8-pot"]
    with_xai: Literal["xai", "non-xai"]
    ext: Literal[".xml", ".bin", ".onnx"]


class ConfigArtifact(BaseModel):
    """This artifact is required only for OTX v1 tiled detection models."""

    output_dir: ClassVar[str] = os.path.join("outputs", "configurations")

    prefix: Literal["config"]
    precision: Literal["fp32", "fp16", "int8-nncf", "int8-pot"]
    with_xai: Literal["xai", "non-xai"]
    ext: Literal[".json"]


class LabelSchemaArtifact(BaseModel):
    output_dir: ClassVar[str] = os.path.join("outputs", "configurations")

    prefix: Literal["label-schema"]
    ext: Literal[".json"]


class ErrorLogArtifact(BaseModel):
    """This artifact is required for logging errors."""

    output_dir: ClassVar[str] = os.path.join("outputs", "logs")

    prefix: Literal["error"]
    ext: Literal[".json"]


class FullLogArtifact(BaseModel):
    """This artifact is required for logging full OTX process."""

    output_dir: ClassVar[str] = os.path.join("outputs", "logs")

    prefix: Literal["otx-full"]
    ext: Literal[".log"]


class DispatchingError(Exception):
    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(msg)


def dispatch_artifact(filepath: str | Path) -> BaseModel:
    """Dispatch an artifact file to the correct model according to its name."""
    error_stack = []

    for artifact_model in [
        ModelArtifact,
        ExportableCodeArtifact,
        OptimizedConfigArtifact,
        # TODO: Below should be deprecated in the future
        PerformanceArtifact,
        TileClassifierArtifact,
        ConfigArtifact,
        LabelSchemaArtifact,
        ErrorLogArtifact,
        FullLogArtifact,
    ]:
        try:
            return artifact_model.from_filepath(filepath)  # type: ignore[attr-defined]
        except Exception as e:
            error_stack += [e]

    msg = f"{os.path.basename(filepath)} is failed on dispatching. It has not the allowed file name format."
    raise DispatchingError(msg=msg)
