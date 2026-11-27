#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

import logging as log
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from os import PathLike

_HF_IMPORT_ERROR_MSG = (
    "Loading models from Hugging Face Hub requires the 'huggingface_hub' package. "
    "Install it with: uv pip install openvino-model-api[huggingface]"
)

_MODEL_EXTENSIONS = {".xml", ".onnx"}


def find_model_file(directory: Path, filename: str | None = None) -> Path:
    """Find the model file (.xml or .onnx) in a directory.

    When ``filename`` is given the function simply resolves it relative to
    ``directory``.  Otherwise it scans the directory tree for model files
    and applies the following priority:
        1. OpenVINO IR (``.xml``) files — preferred over ONNX.
        2. ONNX (``.onnx``) files — used when no ``.xml`` is found.

    Args:
        directory: Path to the directory containing downloaded model files.
        filename: Optional exact filename (relative to *directory*) to use.

    Returns:
        Path to the discovered model file.

    Raises:
        FileNotFoundError: If no model file is found.
        ValueError: If more than one candidate model file is found and
            ``filename`` was not specified.
    """
    if filename is not None:
        model_path = directory / filename
        if not model_path.is_file():
            msg = f"Specified model file not found: {model_path}"
            raise FileNotFoundError(msg)
        return model_path

    xml_files = sorted(directory.rglob("*.xml"))
    onnx_files = sorted(directory.rglob("*.onnx"))

    if len(xml_files) == 1:
        return xml_files[0]
    if len(xml_files) > 1:
        names = ", ".join(str(f.relative_to(directory)) for f in xml_files)
        msg = (
            f"Multiple OpenVINO IR model files found in the repository: {names}. "
            "Please specify the exact file using the 'filename' parameter, "
            "e.g. Model.from_pretrained('repo_id', filename='model.xml')"
        )
        raise ValueError(msg)

    if len(onnx_files) == 1:
        return onnx_files[0]
    if len(onnx_files) > 1:
        names = ", ".join(str(f.relative_to(directory)) for f in onnx_files)
        msg = (
            f"Multiple ONNX model files found in the repository: {names}. "
            "Please specify the exact file using the 'filename' parameter, "
            "e.g. Model.from_pretrained('repo_id', filename='model.onnx')"
        )
        raise ValueError(msg)

    msg = (
        "No model files (.xml or .onnx) found in the downloaded repository. "
        "Make sure the Hugging Face repository contains an OpenVINO IR (.xml + .bin) "
        "or ONNX (.onnx) model."
    )
    raise FileNotFoundError(msg)


def download_from_hf(
    repo_id: str,
    *,
    filename: str | None = None,
    revision: str | None = None,
    token: str | bool | None = None,
    cache_dir: str | PathLike | None = None,
    local_dir: str | PathLike | None = None,
    force_download: bool = False,
    local_files_only: bool = False,
    subfolder: str | None = None,
    repo_type: str = "model",
) -> Path:
    """Download a model from a Hugging Face Hub repository.

    When *filename* is provided, only that file (and its ``.bin`` companion for
    OpenVINO IR models) is downloaded via ``hf_hub_download``.  Otherwise the
    whole repository is fetched with ``snapshot_download`` filtered to model
    file extensions only (``*.xml``, ``*.bin``, ``*.onnx``).

    Args:
        repo_id: Hugging Face repository identifier (e.g. ``"user/model-name"``).
        filename: Optional specific model file to download.
        revision: Git revision (branch, tag, or commit hash).
        token: Authentication token for private repositories.  Can be a string
            token, ``True`` to read from the cached login, or ``None``/``False``
            for public access.
        cache_dir: Directory for the Hugging Face cache.
        local_dir: Download files into this directory with their original layout.
        force_download: Re-download even if cached.
        local_files_only: Use only cached files; raise an error if not available.
        subfolder: Subfolder within the repository.
        repo_type: Repository type (``"model"``, ``"dataset"``, or ``"space"``).

    Returns:
        Path to the model file (``.xml`` or ``.onnx``).

    Raises:
        ImportError: If ``huggingface_hub`` is not installed.
    """
    try:
        from huggingface_hub import hf_hub_download, snapshot_download
    except ImportError:
        raise ImportError(_HF_IMPORT_ERROR_MSG) from None

    if filename is not None:
        # Download a specific file
        hf_common = {
            "repo_id": repo_id,
            "revision": revision,
            "token": token,
            "cache_dir": cache_dir,
            "local_dir": local_dir,
            "force_download": force_download,
            "local_files_only": local_files_only,
            "repo_type": repo_type,
        }
        if subfolder:
            hf_common["subfolder"] = subfolder

        model_path = Path(hf_hub_download(filename=filename, **hf_common))  # nosec B615

        # For .xml files, also download the companion .bin weights file
        if model_path.suffix == ".xml":
            bin_filename = filename.rsplit(".", 1)[0] + ".bin"
            try:
                hf_hub_download(filename=bin_filename, **hf_common)  # nosec B615
            except (OSError, ValueError):
                log.getLogger(__name__).debug(
                    "No companion .bin file found for %s (model may be self-contained)",
                    filename,
                )

        return model_path

    # Download relevant model files from the whole repository
    snapshot_dir = snapshot_download(
        repo_id=repo_id,
        revision=revision,
        token=token,
        cache_dir=cache_dir,
        local_dir=local_dir,
        force_download=force_download,
        local_files_only=local_files_only,
        repo_type=repo_type,
        allow_patterns=["*.xml", "*.bin", "*.onnx"],
    )
    snapshot_path = Path(snapshot_dir)

    return find_model_file(snapshot_path, filename=None)
