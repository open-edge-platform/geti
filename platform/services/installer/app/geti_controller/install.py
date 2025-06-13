# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os

import yaml

from configuration_models.install_config import InstallationConfig
from constants.charts import GETI_CONTROLLER_CHART
from constants.paths import GETI_CONTROLLER_CHART_PATH
from platform_configuration.versions import get_target_product_build
from geti_controller.errors import GetiControllerInstallationError
from platform_stages.steps.errors import ChartInstallationError
from platform_utils.helm import upsert_chart

logger = logging.getLogger(__name__)


def deploy_geti_controller_chart(config: InstallationConfig, charts_dir: str = GETI_CONTROLLER_CHART_PATH) -> None:
    """
    Method used to deploy Geti Controller chart
    """

    try:
        chart_version = get_target_product_build() if config.lightweight_installer.value else None

        configuration_data = {
            "configuration": {
                "login": config.username.value,
                "passwordHash": config.password_sha.value,
                "dataFolder": config.data_folder.value,
                "tlsCert": "",
                "tlsKey": "",
            },
            "global": {
                "ingress_enabled": False,
                "registry_address": config.geti_image_registry.value,
                "tag": get_target_product_build(),
            },
        }

        if config.tls_cert_file and config.tls_key_file and config.tls_cert_file.value and config.tls_key_file.value:
            with open(config.tls_cert_file.value, "rb") as cert_file:
                configuration_data["configuration"]["tlsCert"] = cert_file.read().decode("utf-8")
            with open(config.tls_key_file.value, "rb") as key_file:
                configuration_data["configuration"]["tlsKey"] = key_file.read().decode("utf-8")

        values_file_path = os.path.join(charts_dir, "controller_values.yaml")
        with open(values_file_path, "w") as values_file:
            yaml.safe_dump(configuration_data, values_file)

        upsert_chart(
            name=GETI_CONTROLLER_CHART.name,
            version=chart_version,
            chart_dir=charts_dir,
            namespace=GETI_CONTROLLER_CHART.namespace,
            values=[values_file_path],
        )
    except ChartInstallationError as ex:
        raise GetiControllerInstallationError from ex
