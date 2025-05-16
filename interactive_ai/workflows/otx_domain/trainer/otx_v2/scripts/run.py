# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from __future__ import annotations

import json
import logging
import os
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import mlflow
from minio_util import download_file
from mlflow_io import AsyncCaller, download_config_file, download_shard_files, log_error, log_full
from optimize import optimize
from train import train
from utils import JobType, MLFlowTrackerAccessInfo, OTXConfig, logging_elapsed_time

if TYPE_CHECKING:
    from mlflow import MlflowClient
    from mlflow.entities import Run

logger = logging.getLogger("mlflow_job")


def download_pretrained_weights(template_id: str) -> None:
    """Download pretrained weights from MinIO and save them to the given directory."""

    logger.info(f"downloading pretrained weights for template_id: {template_id}")

    # get model metadata file
    host_name = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
    bucket_name = os.environ.get("BUCKET_NAME_PRETRAINEDWEIGHTS", "pretrainedweights")
    metadata_path = os.path.join(str(work_dir), "metadata.json")
    download_file(bucket_name, "pretrained_models.json", metadata_path, host_name)

    if not os.path.exists(metadata_path):
        raise RuntimeError(f"Metadata file {metadata_path} does not exist")

    with open(metadata_path) as f:
        metadata = json.load(f)
    # Determine obj_name depending on the config
    obj_names = []
    for model in metadata:
        template_ids = model.get("template_ids")
        if template_ids is not None and isinstance(template_ids, list):
            for id in template_ids:
                if id == template_id:
                    obj_names.append(os.path.basename(model["target"]))
                    logger.info(
                        f"Found pretrained weights for template_id: {template_id},"
                        "target: {os.path.basename(model['target'])}"
                    )
                    break

    if len(obj_names) == 0:
        raise RuntimeError(f"Cannot find matched weights from model metadata for {template_id}")

    model_cache_dir = os.environ.get("MODEL_CACHE_DIR", "/home/non-root/.cache/torch/hub/checkpoints")
    host_name = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
    for obj_name in obj_names:
        file_path = os.path.join(model_cache_dir, obj_name)
        download_file(bucket_name, obj_name, file_path, host_name)
        if file_path.endswith(".zip"):
            with zipfile.ZipFile(file_path) as zip_ref:
                zip_ref.extractall(os.path.dirname(file_path))
            os.remove(file_path)
        logger.info(f"Downloaded pretrained weights: {obj_name} to {file_path}")


@logging_elapsed_time(logger=logger, log_level=logging.INFO)
def execute(client: mlflow.MlflowClient, run: Run, work_dir: Path) -> None:
    """Execute an OTX job by dispatching according to the given job type."""

    config_file_path = download_config_file(client, run)
    shard_files_dir = download_shard_files(run)

    config = OTXConfig.from_json_file(config_file_path=config_file_path)

    job_type = config.job_type
    download_pretrained_weights(config.model_template_id)

    if job_type == JobType.TRAIN:
        logger.debug("Starting training job.")
        train(
            config=config,
            client=client,
            run=run,
            dataset_dir=shard_files_dir,
            work_dir=work_dir,
        )
        logger.debug("Training job completed.")
    elif job_type == JobType.OPTIMIZE_POT:
        logger.debug("Starting POT job.")
        optimize(
            config=config,
            client=client,
            run=run,
            dataset_dir=shard_files_dir,
            work_dir=work_dir,
        )
        logger.debug("POT job completed.")
    else:
        raise ValueError


@logging_elapsed_time(logger=logger, log_level=logging.INFO)
def init_mlflow_client_and_run() -> tuple[MlflowClient, Run]:  # noqa: D103
    logger.debug("Initializing MLFlow client and run.")
    client = mlflow.MlflowClient()
    access_info = MLFlowTrackerAccessInfo.from_env_vars()
    run = client.get_run(run_id=access_info.run_id)
    return client, run


if __name__ == "__main__":
    client = None
    log_file = "otx-full.log"
    # Add File logging handler
    root_logger = logging.getLogger(None)
    root_logger.addHandler(
        logging.FileHandler(
            filename=log_file,
            mode="w",
        )
    )

    with open("primary.pid", "w") as fp:
        pid = os.getpid()
        fp.write(str(pid))
        logger.info(f"Primary PID: {pid}")

    try:
        AsyncCaller().start()

        client, run = init_mlflow_client_and_run()

        with TemporaryDirectory() as tmpdir:
            work_dir = Path(tmpdir)
            logger.debug("Start main execute() process.")
            execute(client=client, run=run, work_dir=work_dir)

        Path("/tmp/training_completed").touch()  # noqa: S108
    except Exception as exception:
        log_error(exception=exception, client=client, run=run)
        raise  # Reraise
    finally:
        root_logger.debug("Start AsyncCaller().close() process.")
        AsyncCaller().close()

        root_logger.debug(
            f"Start log_full() process, log_file exists:{Path(log_file).exists()}, client is not None:{client is not None}."  # noqa: E501
        )
        if client is not None and Path(log_file).exists():
            full_log_text = Path(log_file).read_text()
            log_full(full_log_text=full_log_text, client=client, run=run)
        root_logger.debug("Finished log_full() process.")
