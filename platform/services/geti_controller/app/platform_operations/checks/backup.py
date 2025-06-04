# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import subprocess

logger = logging.getLogger(__name__)

DATA_FOLDER_PATH = "/data"  # persistent volume


def _get_available_storage() -> int:
    """
    Get available storage in MB for the specified directory.
    This checks the storage associated with the persistent volume mounted in the Pod.
    """
    process = subprocess.run(  # noqa S603
        ["/bin/sh", "-c", f"df -m {DATA_FOLDER_PATH} | tail -n1"], capture_output=True, text=True, check=True
    )
    available_storage = int(process.stdout.split()[3])
    logger.debug(f"Available storage for {DATA_FOLDER_PATH}: {available_storage} MB")
    return available_storage


def _get_used_storage() -> int:
    """
    Get used storage in MB for the specified data folder.
    This calculates the storage used within the persistent volume.
    """
    process = subprocess.run(  # noqa S603
        [
            "/bin/sh",
            "-c",
            f"du --max-depth=0 -m "
            f"--exclude='{DATA_FOLDER_PATH}/binary_data' "
            f"--exclude='{DATA_FOLDER_PATH}/seaweedfs' "
            f"{DATA_FOLDER_PATH}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    used_storage = int(process.stdout.split("\t")[0])
    logger.debug(f"Used storage for {DATA_FOLDER_PATH}: {used_storage} MB")
    return used_storage


def is_backup_possible() -> bool:
    """
    Checks if there is sufficient storage space on the server to perform a backup.
    The check is performed on the persistent volume mounted in the Pod.
    """
    # Calculate required storage (used storage + 5 GB buffer)
    used_storage = _get_used_storage()
    required_storage = used_storage + 5000
    logger.debug(f"Required storage for backup: {required_storage} MB")

    available_storage = _get_available_storage()

    return required_storage <= available_storage
