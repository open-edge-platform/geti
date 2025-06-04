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
from constants.paths import CHARTS_DIR, INSTALL_LOG_FILE_PATH, PLATFORM_INSTALL_PATH
from platform_stages.steps.errors import CopyPlatformChartsError

logger = logging.getLogger(__name__)


def copy_platform_charts(
    config: InstallationConfig | UpgradeConfig, charts_dir: str = CHARTS_DIR, destination: str = PLATFORM_INSTALL_PATH
) -> None:
    """
    Copy platform charts for installation purposes
    """

    if not config.lightweight_installer.value:
        logger.info(f"Copying platform charts from '{charts_dir}' to '{destination}'")
        with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            try:
                subprocess_run(
                    ["bash", "-c", f"cp -r {charts_dir}/* {destination}"],
                    log_file,
                )
            except subprocess.CalledProcessError as ex:
                raise CopyPlatformChartsError from ex
        logger.info("Platform charts copied.")
