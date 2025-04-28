# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from __future__ import annotations

import logging
import os
import shutil
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from mlflow_io import download_model_artifact, upload_model_artifact
from utils import BASE_MODEL_FILENAME, ExportFormat

if TYPE_CHECKING:
    from mlflow import MlflowClient
    from mlflow.entities import Run
    from utils import ExportParameter


logger = logging.getLogger(__name__)


def unzip_exportable_code(
    work_dir: Path,
    exported_path: Path,
    dst_dir: Path,
) -> None:
    """Unzip exportable code

    We export the model only exportable code format currently.
    It is due to preventing a duplication model exportation between exportable code and OpenVINO IR format.
    """
    # TODO: This function should be deprecated and it should be improved
    # in upstream to export OPENVINO IR and EXPORTABLE_CODE at the same time
    # This time, we don't have that interface, thus it is inevitable to export as EXPORTABLE_CODE format.
    # Then, unzip the zip file to obtain OPENVINO IR files in it.
    # For example, if we excute `exported_path = engine.export(..., exportable_code=True)`, then
    # exported_path => {exported_model.bin, exported_model.xml, exportable_code.zip}

    with zipfile.ZipFile(exported_path, mode="r") as zfp, TemporaryDirectory(prefix=str(work_dir)) as tmpdir:
        zfp.extractall(tmpdir)
        dirpath = Path(tmpdir)

        shutil.move(dirpath / "model" / "model.xml", dst_dir / "exported_model.xml")
        shutil.move(dirpath / "model" / "model.bin", dst_dir / "exported_model.bin")

    shutil.move(exported_path, dst_dir / exported_path.name)


def save_openvino_exported_model(
    client: MlflowClient,
    run: Run,
    work_dir: Path,
    export_param: ExportParameter,
    exported_path: Path,
    export_dir: Path,
) -> None:
    """Save OpenVINO exported model and exportable code at the same time via MLFlow API."""
    # TODO: This function should be deprecated and it should be improved
    # in upstream to export OPENVINO IR and EXPORTABLE_CODE at the same time
    # This time, we don't have that interface, thus it is inevitable to export as EXPORTABLE_CODE format.
    # Then, unzip the zip file to obtain OPENVINO IR files in it.
    # For example, if we excute `exported_path = engine.export(..., exportable_code=True)`, then
    # exported_path => {exported_model.bin, exported_model.xml, exportable_code.zip}

    unzip_exportable_code(
        work_dir=work_dir,
        exported_path=exported_path,
        dst_dir=export_dir,
    )

    save_exported_model(
        client=client,
        run=run,
        export_dir=export_dir,
        export_param=export_param,
    )


def save_trained_model_weights(
    client: MlflowClient,
    run: Run,
    best_checkpoint: Path,
    force_non_xai: bool = False,
) -> None:
    """Save model trained weights (PyTorch checkpoint) via MLFlow API."""
    filename = BASE_MODEL_FILENAME if not force_non_xai else BASE_MODEL_FILENAME.replace("xai", "non-xai")

    upload_model_artifact(
        client=client,
        run=run,
        src_filepath=best_checkpoint,
        dst_filepath=Path("outputs") / "models" / filename,
    )


def save_exported_model(client: MlflowClient, run: Run, export_dir: Path, export_param: ExportParameter) -> None:
    """Utility function to save exported format according to `ExportParameter`."""
    if export_param.export_format == ExportFormat.OPENVINO:
        src_filepath = export_dir / "exportable_code.zip"
        upload_model_artifact(
            client=client,
            run=run,
            src_filepath=src_filepath,
            dst_filepath=Path("outputs") / "exportable_codes" / export_param.to_exportable_code_artifact_fname(),
        )
        os.remove(src_filepath)

        for src_filename, dst_filename in zip(
            ["exported_model.bin", "exported_model.xml"],
            export_param.to_mlflow_artifact_fnames(),
        ):
            src_filepath = export_dir / src_filename
            upload_model_artifact(
                client=client,
                run=run,
                src_filepath=src_filepath,
                dst_filepath=Path("outputs") / "models" / dst_filename,
            )
            os.remove(src_filepath)

        return

    if export_param.export_format == ExportFormat.ONNX:
        for src_filename, dst_filename in zip(
            ["exported_model.onnx"],
            export_param.to_mlflow_artifact_fnames(),
        ):
            upload_model_artifact(
                client=client,
                run=run,
                src_filepath=export_dir / src_filename,
                dst_filepath=Path("outputs") / "models" / dst_filename,
            )

        return

    raise ValueError(export_param)


def load_trained_model_weights(
    client: MlflowClient,
    run: Run,
    work_dir: Path,
    optimize: bool = False,
) -> Path | None:
    """
    Load the trained model weights from an MLFlow run and save them to the specified working directory.

    Args:
        client (MlflowClient): The MLFlow client used to interact with the MLFlow tracking server.
        run (Run): The MLFlow run object containing the metadata of the run from which to load the model weights.
        work_dir (Path): The directory where the model weights will be saved.
        optimize (bool, optional): A flag indicating whether to load optimized model weights. Defaults to False.

    Returns:
        Path | None: The path to the saved model weights file if successful, otherwise None.
                     For the optimization path, any returned path indicates that the weights have been loaded
                     successfully.
                     For the training path, there is always a single PyTorch-based path.
    """

    mlflow_src_dir = Path("inputs")
    mlflow_src_fnames = ["openvino.bin", "openvino.xml"] if optimize else ["model.pth"]

    file_info_set = {
        os.path.basename(finfo.path)
        for finfo in client.list_artifacts(run_id=run.info.run_id, path=str(mlflow_src_dir))
    }
    logger.info("Received file_info_set=%s", file_info_set)

    if not all(mlflow_src_fname in file_info_set for mlflow_src_fname in mlflow_src_fnames):
        logger.info("Found no model checkpoint. Starting from scratch.")
        return None

    logger.info("Found model checkpoint: %s. Downloading the checkpoint.", mlflow_src_fnames)
    downloaded = []
    for mlflow_src_fname in mlflow_src_fnames:
        downloaded.append(
            download_model_artifact(
                client=client,
                run=run,
                mlflow_src_path=mlflow_src_dir / mlflow_src_fname,
                dst_dir_path=work_dir,
                use_presigned_url=True,
            )
        )

    return downloaded[0]


def _update_configurable_parameters(cur_hp: dict, optimized_hp: dict) -> dict:
    for param_key, param_val in optimized_hp.items():
        splited_param_key = param_key.split(".")

        target = cur_hp
        for val in splited_param_key[:-1]:
            target = target[val]
        target[splited_param_key[-1]] = param_val

    return cur_hp
