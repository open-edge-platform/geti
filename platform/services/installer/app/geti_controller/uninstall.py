# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import subprocess

from cli_utils.platform_logs import subprocess_run
from configuration_models.install_config import InstallationConfig
from constants.charts import GETI_CONTROLLER_CHART
from constants.paths import HELM_BINARY, INSTALL_LOG_FILE_PATH
from platform_stages.steps.errors import GetiControllerUninstallationError

logger = logging.getLogger(__name__)


def uninstall_geti_controller_chart(config: InstallationConfig) -> None:
    """
    Method used to uninstall Geti Controller chart
    """

    try:
        logger.info(
            f"Uninstalling Geti Controller chart '{GETI_CONTROLLER_CHART.name}' from the namespace "
            f"'{GETI_CONTROLLER_CHART.namespace}'."
        )
        command = [
            HELM_BINARY,
            "uninstall",
            GETI_CONTROLLER_CHART.name,
            f"--namespace={GETI_CONTROLLER_CHART.namespace}",
            "--ignore-not-found",
            f"--kubeconfig={config.kube_config.value}",
        ]
        with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            subprocess_run(command, log_file)
        logger.info("Geti Controller chart uninstalled successfully.")
    except subprocess.CalledProcessError as ex:
        logger.exception("Failed to uninstall Geti Controller chart.")
        raise GetiControllerUninstallationError from ex
