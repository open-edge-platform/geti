# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
Platform logs configuration and parsing content of platform_log directory
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

from constants.paths import INSTALL_LOG_FILE_PATH, PLATFORM_LOGS_DIR

logger = logging.getLogger(__name__)

LOG_TO_STDOUT = os.getenv("LOG_TO_STDOUT") == "true"


class UntarFileError(Exception):
    """
    Raised when unable to unpack tar file
    """


def configure_logging():  # noqa: ANN201
    """
    Configure logging handlers for file and stdout.
    """
    file_handler = logging.FileHandler(filename=INSTALL_LOG_FILE_PATH)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler]
    if LOG_TO_STDOUT:
        handlers.append(stdout_handler)
    logging.basicConfig(
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
        handlers=handlers,
    )
    # turn off kubernetes debug logs
    logging.getLogger("kubernetes.client.rest").setLevel(logging.CRITICAL)


def create_logs_dir():  # noqa: ANN201
    """
    Prepare directory for platform logs.
    """
    path_platform_logs = Path(PLATFORM_LOGS_DIR)

    path_platform_logs.mkdir(parents=True, exist_ok=True)

    logs_to_backup = []
    logs_to_backup.extend(path_platform_logs.glob("*.log"))
    logs_to_backup.extend(path_platform_logs.glob("cluster_info"))
    logs_to_backup.extend(path_platform_logs.glob("deployment_files"))
    logs_to_backup = tuple(logs_to_backup)

    if logs_to_backup:
        logger.debug(f"Found existing platform logs: {', '.join(str(log.absolute()) for log in logs_to_backup)}")

        backup_dir = _create_log_backup_dir(path_platform_logs)
        logger.debug(f"Backing up existing platform logs to: {backup_dir.absolute()}.")

        for path in logs_to_backup:
            path.rename(backup_dir / path.name)


def _create_log_backup_dir(base_log_dir: Path) -> Path:
    """Creates a directory for backing up old platform logs.

    :base_log_dir Path: Path to base directory containing platform logs.
    :return Path: Path to the created log backup directory.
    :raise EnvironmentError: On failure to create a unique log backup directory.
    """
    for num in range(1, sys.maxsize):
        try:
            backup_dir = base_log_dir / str(num)
            backup_dir.mkdir(parents=True, exist_ok=False)
            return backup_dir
        except FileExistsError:
            pass

    raise OSError("Failed to create a log backup directory.")


def subprocess_run(command, log_file, env=None, cwd=None):  # noqa: ANN001, ANN201
    """
    Runs the command and outputs to platform logs and/or stdout.
    """
    with subprocess.Popen(  # noqa: S603
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env=env,
        cwd=cwd,
        text=True,
    ) as subp:
        for line in subp.stdout:
            log_file.write(line)
            log_file.flush()
            if LOG_TO_STDOUT:
                print(line, end="")

    if subp.returncode != 0:
        raise subprocess.CalledProcessError(subp.returncode, subp.args)
