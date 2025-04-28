# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from mlflow_logger import MLFlowLogger
from otx.tools.converter import ConfigConverter
from otx_io import (
    load_trained_model_weights,
    save_exported_model,
    save_openvino_exported_model,
    save_trained_model_weights,
)
from progress_updater import ProgressUpdater, ProgressUpdaterCallback, TrainingStage
from utils import ExportFormat, OTXConfig, force_mlflow_async_logging, logging_elapsed_time

if TYPE_CHECKING:
    from mlflow import MlflowClient
    from mlflow.entities import Run

logger = logging.getLogger("mlflow_job")


@force_mlflow_async_logging()
@logging_elapsed_time(logger=logger)
def train(
    config: OTXConfig,
    client: MlflowClient,
    run: Run,
    dataset_dir: Path,
    work_dir: Path,
    resume: bool = False,
) -> None:
    """Execute OTX model training."""
    otx2_config = config.to_otx2_config(work_dir=work_dir)
    engine, train_kwargs = ConfigConverter.instantiate(
        config=otx2_config,
        work_dir=str(work_dir / "otx-workspace"),
        data_root=str(dataset_dir),
    )
    logger.debug("Engine and train_kwargs instantiated.")

    stage = TrainingStage.TRAINING
    progress_updater = ProgressUpdater(
        client=client,
        run=run,
        stage=stage,
        n_processes=1,
        interval=2.0,
    )

    train_kwargs["resume"] = resume
    train_kwargs["checkpoint"] = load_trained_model_weights(
        client=client,
        run=run,
        work_dir=work_dir,
    )
    logger.debug("Loaded trained model weights.")

    # Add mlflow logger and progress reporter
    train_kwargs["callbacks"] += [ProgressUpdaterCallback(progress_updater=progress_updater)]
    train_kwargs["logger"] = [
        MLFlowLogger(
            tracking_uri=client.tracking_uri,
            run_id=run.info.run_uuid,
            synchronous=False,
        ),
    ]
    logger.debug("Added MLFlow logger and progress reporter.")

    engine.train(**train_kwargs)
    logger.debug("Training completed.")

    if engine.checkpoint is None:
        raise RuntimeError("Cannot get engine.checkpoint.")

    save_trained_model_weights(
        client=client,
        run=run,
        best_checkpoint=Path(engine.checkpoint),
        force_non_xai=False,
    )
    logger.debug("Saved trained model weights.")

    for export_param in config.export_parameters:
        if export_param.export_format == ExportFormat.OPENVINO:
            logger.debug("Exporting model to OPENVINO format.")
            exported_path = engine.export(
                export_format=export_param.to_otx2_export_format(),
                export_precision=export_param.to_otx2_precision(),
                explain=export_param.with_xai,
                export_demo_package=True,
            )
            export_dir = exported_path.parent

            save_openvino_exported_model(
                client=client,
                run=run,
                work_dir=work_dir,
                export_param=export_param,
                exported_path=exported_path,
                export_dir=export_dir,
            )
            logger.debug("OpenVINO model is saved.")
        elif export_param.export_format == ExportFormat.ONNX:
            logger.debug("Exporting model to ONNX format.")
            exported_path = engine.export(
                export_format=export_param.to_otx2_export_format(),
                export_precision=export_param.to_otx2_precision(),
                explain=export_param.with_xai,
                export_demo_package=False,
            )
            export_dir = exported_path.parent

            save_exported_model(
                client=client,
                run=run,
                export_dir=export_dir,
                export_param=export_param,
            )
            logger.debug("ONNX model is saved.")
