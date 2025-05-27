# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from pathlib import Path

import requests

DATA_URL_PREFIX = "https://storage.geti.infra-host.com/test-data/e2e-bdd"

logger = logging.getLogger(__name__)


class RemoteFileNotFound(FileNotFoundError):
    """Exception raised when the requested file is not found in the remote archive"""


class RemoteFileNotAccessible(RuntimeError):
    """Exception raised when the requested file is not accessible in the remote archive due to permissions"""


def download_file_from_remote_archive(remote_file_path: Path, local_file_path: Path) -> None:
    """
    Download the requested file from the remote archive.

    :param remote_file_path: Path to the file in the remote archive, relative to the testing base directory
    :param local_file_path: Path to save the file locally
    :raises RemoteFileNotFound: If the requested file is not found in the remote archive
    :raises RemoteFileNotAccessible: If the requested file is not accessible in the remote archive due to permissions
    :raises RuntimeError: If the file download fails for any other reason
    """
    file_url = f"{DATA_URL_PREFIX}/{remote_file_path}"
    logger.info(f"Downloading file from remote archive: {file_url}")

    # Download the file
    response = requests.get(file_url, stream=True, timeout=300, verify=False)  # noqa: S501

    if response.status_code == 404:
        raise RemoteFileNotFound(f"File not found: {file_url}")

    response.raise_for_status()  # Handle other HTTP errors

    local_file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(local_file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
