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
from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.paths import INSTALL_LOG_FILE_PATH, INSTALLER_DIR
from platform_stages.steps.errors import ExtractRegistryDataError

logger = logging.getLogger(__name__)


def extract_registry_data(config: InstallationConfig | UpgradeConfig) -> None:
    """
    Extract registry data for installation purposes
    """
    if not config.lightweight_installer.value:
        registry_data_dir = f"{config.data_folder.value}/registry"

        logger.info(f"Creating registry data directory: '{registry_data_dir}'")
        with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            try:
                subprocess_run(
                    ["mkdir", "-p", registry_data_dir],
                    log_file,
                )
            except subprocess.CalledProcessError as ex:
                raise ExtractRegistryDataError from ex
        logger.info("Registry data directory created.")

        logger.info("Extracting registry data...")
        with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            try:
                subprocess_run(
                    [
                        "tar",
                        "-xvf",
                        "registry_data.tar.gz",
                        "--use-compress-program=pigz",
                        "-C",
                        f"{registry_data_dir}",
                    ],
                    log_file,
                    cwd=INSTALLER_DIR,
                )
            except subprocess.CalledProcessError as ex:
                raise ExtractRegistryDataError from ex
        logger.info("Registry data extracted.")
    else:
        logger.info("External registry used, skipping internal registry extract")
