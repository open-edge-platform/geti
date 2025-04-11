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

import logging
from typing import TYPE_CHECKING

from otx.tools.converter import ConfigConverter

from .otx_io import load_trained_model_weights, save_openvino_exported_model
from .progress_updater import ProgressUpdater, TrainingStage
from .utils import OptimizationType, OTXConfig, PrecisionType, force_mlflow_async_logging, logging_elapsed_time

if TYPE_CHECKING:
    from pathlib import Path

    from mlflow import MlflowClient
    from mlflow.entities import Run

logger = logging.getLogger("mlflow_job")


@force_mlflow_async_logging()
@logging_elapsed_time(logger=logger)
def optimize(
    config: OTXConfig,
    client: MlflowClient,
    run: Run,
    dataset_dir: Path,
    work_dir: Path,
) -> None:
    """Execute OTX model optimize."""
    if config.optimization_type != OptimizationType.POT:
        msg = "OTX2 can only support OptimizationType.POT."
        raise ValueError(msg, config.optimization_type)

    if len(config.export_parameters) != 1:
        msg = "There should be exactly one export parameter."
        raise ValueError(msg, config.export_parameters)

    export_param = next(iter(config.export_parameters))

    if export_param.precision != PrecisionType.INT8 or export_param.with_xai:
        msg = "Invalid export parameter."
        raise ValueError(msg, export_param)

    progress_updater = ProgressUpdater(
        client=client,
        run=run,
        stage=TrainingStage.OPTIMIZATION,
        n_processes=1,
        interval=2.0,
    )
    progress_updater.update_progress(0.0)

    otx2_config = config.to_otx2_config(work_dir=work_dir)
    engine, _ = ConfigConverter.instantiate(
        config=otx2_config,
        work_dir=str(work_dir / "otx-workspace"),
        data_root=str(dataset_dir),
    )

    checkpoint = load_trained_model_weights(client=client, run=run, work_dir=work_dir, optimize=True)
    if checkpoint is None:
        raise RuntimeError("Cannot get checkpoint for optimization.")

    logger.debug("Checkpoint is loaded. Starting optimization.")
    optimized_path = engine.optimize(
        checkpoint=work_dir / "openvino.xml",
        export_demo_package=True,
    )

    logger.debug("Optimization is completed. Saving optimized models.")
    save_openvino_exported_model(
        client=client,
        run=run,
        work_dir=work_dir,
        export_param=export_param,
        exported_path=optimized_path,
        export_dir=optimized_path.parent,
    )

    logger.debug("Optimized model is saved.")
    progress_updater.update_progress(100.0)
