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

import json
import logging
import os
import time
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING

from otx.core.types.export import OTXExportFormatType
from otx.core.types.precision import OTXPrecisionType
from otx.core.types.task import OTXTaskType
from otx.tools.converter import TEMPLATE_ID_DICT, ConfigConverter

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

BASE_MODEL_FILENAME = "model_fp32_xai.pth"


def logging_elapsed_time(logger: logging.Logger, log_level: int = logging.INFO) -> Callable:
    """Decorate a function to log its elapsed time.

    :param logger: Python logger to log the elapsed time.
    :param log_level: Logging level to log the elapsed time.
    """

    def _decorator(func: Callable):
        @wraps(func)
        def _wrapped(*args, **kwargs):
            msg = f"Starting: {func.__name__}"
            logger.log(level=log_level, msg=msg)

            t_start = time.time()
            outputs = func(*args, **kwargs)
            t_elapsed = (time.time() - t_start) * 1e3

            msg = f"Finishing: {func.__name__}, Elapsed time: {t_elapsed:.1f} ms"

            return outputs

        return _wrapped

    return _decorator


def force_mlflow_async_logging() -> Callable:
    """Decorator to set environment variable for asynchronous mlflow logging."""

    def _decorator(func: Callable):
        @wraps(func)
        def _wrapped(*args, **kwargs):
            flag = os.environ.get("MLFLOW_ENABLE_ASYNC_LOGGING", "false").lower() in {"true", "1"}
            if not flag:
                os.environ["MLFLOW_ENABLE_ASYNC_LOGGING"] = "True"
                msg = (
                    "Environment variable MLFLOW_ENABLE_ASYNC_LOGGING should be True. "
                    "If not, you can get a performance degradation from synchronous logging."
                )
                logging.warning(msg)

            return func(*args, **kwargs)

        return _wrapped

    return _decorator


class JobType(str, Enum):
    TRAIN = "train"
    OPTIMIZE_POT = "optimize_pot"


class OptimizationType(str, Enum):
    POT = "POT"


class ExportFormat(str, Enum):
    BASE_FRAMEWORK = "BASE_FRAMEWORK"
    OPENVINO = "OPENVINO"
    ONNX = "ONNX"


class PrecisionType(str, Enum):
    FP32 = "FP32"
    FP16 = "FP16"
    INT8 = "INT8"


@dataclass(frozen=True)
class MLFlowTrackerAccessInfo:
    tracking_uri: str
    experiment_id: str
    run_id: str

    @classmethod
    def from_env_vars(cls) -> MLFlowTrackerAccessInfo:
        return MLFlowTrackerAccessInfo(
            tracking_uri=os.environ["MLFLOW_TRACKING_URI"],
            experiment_id=os.environ["MLFLOW_EXPERIMENT_ID"],
            run_id=os.environ["MLFLOW_RUN_ID"],
        )


@dataclass
class ExportParameter:
    """
    config.json's export_parameters item model.
    """

    export_format: ExportFormat
    precision: PrecisionType = PrecisionType.FP32
    with_xai: bool = False

    def to_mlflow_artifact_fnames(self) -> list[str]:
        fname = "model_"
        precision_name = (
            self.precision.name.lower() + "-pot"
            if self.precision == PrecisionType.INT8
            else self.precision.name.lower()
        )
        fname += precision_name + "_"
        if self.with_xai:
            fname += "xai"
        else:
            fname += "non-xai"

        export_formats = {
            ExportFormat.OPENVINO: [f"{fname}.bin", f"{fname}.xml"],
            ExportFormat.ONNX: [f"{fname}.onnx"],
            ExportFormat.BASE_FRAMEWORK: [f"{fname}.pth"],
        }
        if self.export_format in export_formats:
            return export_formats[self.export_format]

        raise ValueError(f"Unsupported export format {self.export_format}")

    def to_exportable_code_artifact_fname(self) -> str:
        fname = "exportable-code_"
        precision_name = (
            self.precision.name.lower() + "-pot"
            if self.precision == PrecisionType.INT8
            else self.precision.name.lower()
        )
        fname += precision_name + "_"
        if self.with_xai:
            fname += "xai"
        else:
            fname += "non-xai"

        return fname + ".whl"

    def to_otx2_export_format(self) -> OTXExportFormatType:
        if self.export_format == ExportFormat.OPENVINO:
            return OTXExportFormatType.OPENVINO
        if self.export_format == ExportFormat.ONNX:
            return OTXExportFormatType.ONNX

        raise ValueError(self.export_format)

    def to_otx2_precision(self) -> OTXPrecisionType:
        if self.precision == PrecisionType.FP32:
            return OTXPrecisionType.FP32
        if self.precision == PrecisionType.FP16:
            return OTXPrecisionType.FP16

        raise ValueError(self.precision)


def str2bool(value: str | bool) -> bool:
    """Convert given value to boolean."""
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        raise ValueError(value)

    raise TypeError(value)


@dataclass(frozen=True)
class OTXConfig:
    job_type: JobType
    model_template_id: str
    hyper_parameters: dict
    export_parameters: list[ExportParameter]
    optimization_type: OptimizationType | None
    sub_task_type: OTXTaskType | None

    @classmethod
    def from_json_file(cls, config_file_path: Path) -> OTXConfig:
        with open(config_file_path) as fp:
            config: dict = json.load(fp)

        opt_type_name: str | None = config.get("optimization_type")

        if opt_type_name and opt_type_name.upper() == "POT":
            optimization_type = OptimizationType.POT
        else:
            optimization_type = None

        sub_task_type = config.get("sub_task_type")

        if sub_task_type is not None:
            sub_task_type = OTXTaskType(sub_task_type)

        return OTXConfig(
            job_type=JobType(config["job_type"]),
            model_template_id=config["model_template_id"],
            hyper_parameters=config["hyperparameters"],
            export_parameters=[
                ExportParameter(
                    export_format=ExportFormat(cfg["type"].upper()),
                    precision=PrecisionType(cfg["precision"].upper()),
                    with_xai=str2bool(cfg["with_xai"]),
                )
                for cfg in config.get("export_parameters", [])
            ],
            optimization_type=optimization_type,
            sub_task_type=sub_task_type,
        )

    def to_json_file(self, fpath: Path) -> None:
        with fpath.open("w") as fp:
            json.dump(
                {
                    "model_template_id": self.model_template_id,
                    "hyperparameters": self.hyper_parameters,
                },
                fp,
            )

    def to_otx2_config(self, work_dir: Path) -> dict[str, dict]:
        fpath = work_dir / "tmp_config.json"
        self.to_json_file(fpath)

        with self.monkeypatch_cls_task_type(override_cls_task_type=self.sub_task_type):
            otx2_config = ConfigConverter.convert(fpath)

        otx2_config["data"]["data_format"] = "arrow"
        otx2_config["data"]["train_subset"]["subset_name"] = "TRAINING"
        otx2_config["data"]["val_subset"]["subset_name"] = "VALIDATION"
        otx2_config["data"]["test_subset"]["subset_name"] = "TESTING"

        return otx2_config

    @staticmethod
    @contextmanager
    def monkeypatch_cls_task_type(override_cls_task_type: OTXTaskType | None = None) -> Iterator[None]:
        """Monkeypath classification task type which is fixed as `MULTI_CLASS_CLS` in OTX side.

        This should be improved on the OTX side.

        :param override_cls_task_type: Override classification task type if given. Otherwise, do nothing.
        """
        if override_cls_task_type is None:
            yield
            return

        tmp_dict = {}
        for key, value in TEMPLATE_ID_DICT.items():
            if value["task"] == OTXTaskType.MULTI_CLASS_CLS:
                tmp_dict[key] = value

                new_value = deepcopy(value)
                new_value["task"] = override_cls_task_type
                TEMPLATE_ID_DICT[key] = new_value

        yield

        # Revert
        for key, value in tmp_dict.items():
            TEMPLATE_ID_DICT[key] = value
