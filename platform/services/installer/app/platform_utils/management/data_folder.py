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

"""Platform data folder related functions"""

import logging
import os

from cli_utils.platform_logs import subprocess_run
from constants.paths import DATA_CAN_BE_RESTORED_FLAG, INSTALL_LOG_FILE_PATH

logger = logging.getLogger(__name__)


def backup_data_folder(location: str, current_platform_version: str, data_folder: str) -> None:
    """
    Backup data folder

    """
    logger.info("Running data folder backup.")
    backup_location = os.path.join(location, f"backup_data_{current_platform_version}")

    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        # Remove the existing backup directory if it exists and create a new one
        subprocess_run(["rm", "-rf", backup_location], log_file)
        os.makedirs(backup_location, exist_ok=True)

        # Remove all previous backup directories except the current one
        subprocess_run(
            ["bash", "-c", f"export GLOBIGNORE={backup_location}; rm -rf {location}/backup_data*; unset GLOBIGNORE"],
            log_file,
        )

        # Ignore specified directories during backup
        glob_ignore_list = [
            os.path.join(data_folder, "binary_data"),
            backup_location,
            os.path.join(data_folder, "logs"),
            os.path.join(data_folder, "seaweedfs"),
            os.path.join(data_folder, "registry"),
            os.path.join(data_folder, "etcd"),
        ]
        glob_ignore = ":".join(glob_ignore_list)
        subprocess_run(
            [
                "bash",
                "-c",
                f"export GLOBIGNORE={glob_ignore}; cp -a {data_folder}/* {backup_location}/; unset GLOBIGNORE",
            ],
            log_file,
        )

        # Move the registry directory to the backup location if it exists
        registry_dir = os.path.join(data_folder, "registry")
        if os.path.exists(registry_dir):
            subprocess_run(["mv", registry_dir, backup_location], log_file)

        # Should be removed after drop of '2.0.*' version
        subprocess_run(["bash", "-c", f"rm -rf {data_folder}/kafka/*"], log_file)

        # Mark the backup completion for interruption handler
        with open(os.path.join(backup_location, DATA_CAN_BE_RESTORED_FLAG), "w"):
            pass

    logger.info(f"Data folder backup created under: '{backup_location}'")


def restore_data_folder(backup_location: str, data_folder: str) -> None:
    """
    Restore data folder
    """

    logger.info("Restoring data folder backup.")
    if os.path.exists(backup_location):
        with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            # Ignore specified directories during restore
            glob_ignore_list = [
                os.path.join(data_folder, "binary_data"),
                os.path.join(data_folder, "logs"),
                backup_location,
                os.path.join(data_folder, "seaweedfs"),
                os.path.join(data_folder, "etcd"),
            ]
            glob_ignore = ":".join(glob_ignore_list)
            subprocess_run(
                ["bash", "-c", f"export GLOBIGNORE={glob_ignore}; rm -rf {data_folder}/*; unset GLOBIGNORE"], log_file
            )

            # Copy everything from backup location to the data folder, excluding the ignored files
            subprocess_run(["bash", "-c", f"cp -a {backup_location}/* {data_folder}/"], log_file)
    logger.info("Data folder backup restored.")
