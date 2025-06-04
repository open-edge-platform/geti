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
import logging
import subprocess

from cli_utils.platform_logs import subprocess_run
from constants.paths import INSTALL_LOG_FILE_PATH, PLATFORM_INSTALL_PATH
from platform_stages.steps.errors import CreatePlatformDirectoryError

logger = logging.getLogger(__name__)


def create_platform_dir(platform_install_path: str = PLATFORM_INSTALL_PATH) -> None:
    """
    Creates a platform directory for installation purposes
    """

    logger.info(f"Creating platform install path at '{platform_install_path}'")
    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        try:
            subprocess_run(
                [
                    "mkdir",
                    "-p",
                    platform_install_path,
                ],
                log_file,
            )
        except subprocess.CalledProcessError as ex:
            raise CreatePlatformDirectoryError from ex
    logger.info("Platform path created.")
