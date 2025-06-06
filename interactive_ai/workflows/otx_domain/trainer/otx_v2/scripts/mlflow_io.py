# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from __future__ import annotations

import logging
import os
import shutil
import traceback
from functools import partial, wraps
from pathlib import Path
from queue import Queue
from tempfile import TemporaryDirectory
from threading import Thread
from typing import TYPE_CHECKING, ClassVar

import requests
from tqdm import tqdm

from .utils import BASE_MODEL_FILENAME, logging_elapsed_time

if TYPE_CHECKING:
    import io
    from collections.abc import Callable

    from mlflow import MlflowClient
    from mlflow.entities import Run

PRESIGNED_URL_SUFFIX = ".presigned_url"
TIMEOUT = 300.0

logger = logging.getLogger(__name__)


class AsyncCaller:
    """Helper class to execute a function as non-blocking.

    This class is used for live metric logging.
    """

    STOP_SIGN: ClassVar[str] = "__STOP__"
    instance: ClassVar[AsyncCaller | None] = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)

        return cls.instance

    def start(self) -> None:
        self.queue: Queue = Queue()
        self.thread: Thread = Thread(target=self.loop)
        self.thread.start()

    def loop(self) -> None:
        while (item := self.queue.get()) != self.STOP_SIGN:
            item()

    def close(self) -> None:
        self.queue.put(self.STOP_SIGN)
        self.thread.join(timeout=TIMEOUT)

    def put(self, func: Callable, *args, **kwargs) -> None:
        self.queue.put(partial(func, *args, **kwargs))

    @staticmethod
    def async_wrap(func):  # noqa: ANN001, ANN205
        @wraps(func)
        def wrapper(*args, **kwargs):
            async_caller = AsyncCaller()
            if (thread := getattr(async_caller, "thread", None)) is None:
                raise RuntimeError("You should call AsyncCaller().start() first.")

            thread: Thread

            if not thread.is_alive():
                raise RuntimeError("AsyncCaller's thread is not alive.")

            async_caller.put(func, *args, **kwargs)

        return wrapper


def get_shard_files_dir() -> Path:
    """Get shard files directory path from environment variables."""
    return Path(os.environ["SHARD_FILES_DIR"])


@logging_elapsed_time(logger=logger, log_level=logging.INFO)
def download_shard_files(run: Run) -> Path:
    """Download shard files from mlflow.Run.inputs.dataset_inputs."""
    shard_files_dir = get_shard_files_dir()
    msg = f"Shard files directory path: {shard_files_dir}"
    logger.info(msg)

    for inp in tqdm(run.inputs.dataset_inputs, desc="Downloading shard files"):
        fpath = shard_files_dir / inp.dataset.name
        with open(fpath, "wb") as fp:
            try:
                response = requests.get(inp.dataset.source, timeout=10.0, stream=False)
                response.raise_for_status()
                fp.write(response.content)
            finally:
                response.close()

    return Path(shard_files_dir)


@logging_elapsed_time(logger=logger, log_level=logging.INFO)
def download_config_file(client: MlflowClient, run: Run) -> Path:
    """Download the configuration file from MLFlow artifacts."""
    src_path = Path("inputs") / "config.json"
    dst_path = Path(get_shard_files_dir())

    msg = f"Config file path: {dst_path}"
    logger.info(msg)

    fpath = client.download_artifacts(
        run_id=run.info.run_id,
        path=str(src_path),
        dst_path=str(dst_path),
    )
    return Path(fpath)


@logging_elapsed_time(logger=logger, log_level=logging.INFO)
def upload_model_artifact(
    client: MlflowClient,
    run: Run,
    src_filepath: Path,
    dst_filepath: Path,
) -> None:
    """Upload model artifact via MLFlow API."""
    tmp_filepath = src_filepath.parent / dst_filepath.name

    try:
        # NOTE: MlflowClient requires the local filename (src_filepath.name)
        # should be equal to dst_filepath.name
        shutil.move(src=src_filepath, dst=tmp_filepath)

        client.log_artifact(
            run_id=run.info.run_id,
            local_path=str(tmp_filepath),
            artifact_path=str(dst_filepath),
        )
    finally:
        if tmp_filepath.exists():
            shutil.move(src=tmp_filepath, dst=src_filepath)


@logging_elapsed_time(logger=logger, log_level=logging.INFO)
def download_model_artifact(
    client: MlflowClient,
    run: Run,
    mlflow_src_path: Path,
    dst_dir_path: Path,
    use_presigned_url: bool = True,
) -> Path:
    """Download model artifact via MLFlow API."""
    if not dst_dir_path.is_dir():
        msg = f"dst_dir_path={dst_dir_path} should be a directory."
        raise ValueError(msg)

    if use_presigned_url:
        new_dst_path = mlflow_src_path.with_suffix(mlflow_src_path.suffix + PRESIGNED_URL_SUFFIX)
        local_presigned_url_path = client.download_artifacts(
            run_id=run.info.run_id,
            path=str(new_dst_path),
            dst_path=str(dst_dir_path),
        )
        with open(local_presigned_url_path) as fp:
            presigned_url = fp.read()

        local_dst_path = dst_dir_path / mlflow_src_path.name

        with open(local_dst_path, "wb") as fp:
            try:
                response = requests.get(presigned_url, timeout=TIMEOUT, stream=False)
                response.raise_for_status()
                fp.write(response.content)
            finally:
                response.close()
    else:
        local_dst_path = client.download_artifacts(  # type: ignore
            run_id=run.info.run_id,
            path=str(mlflow_src_path),
            dst_path=str(dst_dir_path),
        )

    logger.info("Downloaded model artifact to %s", local_dst_path)
    return Path(local_dst_path)


@AsyncCaller.async_wrap
@logging_elapsed_time(logger=logger, log_level=logging.INFO)
def save_checkpoint(
    client: MlflowClient,
    run: Run,
    model_weights_reader: io.BufferedReader,
    force_non_xai: bool = False,
) -> None:
    """Save the trained base model weight binary file (BASE_FRAMEWORK) via MLFlow artifact APi."""
    filename = BASE_MODEL_FILENAME if not force_non_xai else BASE_MODEL_FILENAME.replace("xai", "non-xai")
    with TemporaryDirectory() as tmpdir:
        local_dir_path = Path(tmpdir)
        local_file_path = local_dir_path / filename

        with local_file_path.open("wb") as fp:
            fp.write(model_weights_reader.read())

        dst_filepath = Path("outputs") / "models" / filename

        upload_model_artifact(
            client=client,
            run=run,
            src_filepath=local_file_path,
            dst_filepath=dst_filepath,
        )


def log_error(exception: Exception, client: MlflowClient, run: Run) -> None:
    """Log exception and traceback into MLFlow artifact."""
    error_dict = {
        "exc_type": exception.__class__.__name__,
        "message": str(exception),
        "traceback": traceback.format_exc(),
    }
    artifact_file = os.path.join("outputs", "logs", "error.json")
    client.log_dict(
        run_id=run.info.run_id,
        dictionary=error_dict,
        artifact_file=artifact_file,
    )


def log_full(full_log_text: str, client: MlflowClient, run: Run) -> None:
    """Log full OTX process into MLFlow artifact."""

    artifact_file = os.path.join("outputs", "logs", "otx-full.log")
    client.log_text(
        run_id=run.info.run_id,
        text=full_log_text,
        artifact_file=artifact_file,
    )
