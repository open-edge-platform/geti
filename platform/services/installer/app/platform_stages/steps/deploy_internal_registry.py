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
import os
from typing import TYPE_CHECKING

from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from platform_configuration.versions import get_target_product_build

if TYPE_CHECKING:
    from kubernetes.client import V1Secret

import logging
import pathlib
import re
import shutil

from cli_utils.platform_logs import subprocess_run
from constants.charts import INTERNAL_REGISTRY_CHART, ISTIO_GATEWAY_CHART
from constants.paths import (
    CERTIFICATE_FILENAME,
    CONFIG_TOML_PATH,
    CONFIG_TOML_TMPL_PATH,
    CONTAINERD_CERT_DIR,
    CONTAINERD_CERT_INTERNAL_REGISTRY,
    HOSTS_TOML_PATH,
    INSTALL_LOG_FILE_PATH,
    INTERNAL_REGISTRY_CERTIFICATES_DIR,
    KEY_FILENAME,
    PLATFORM_INSTALL_PATH,
)
from constants.platform import INTERNAL_REGISTRY_ADDRESS, PLATFORM_NAMESPACE
from platform_configuration.features import FeatureFlag, is_feature_flag_enabled
from platform_stages.steps.errors import (
    ChartInstallationError,
    ChartPullError,
    ContainerdCertificateCreationError,
    ContainerdConfigurationError,
    InternalRegistryInstallationError,
)
from platform_utils.helm import pull_chart, save_jinja_template, upsert_chart
from platform_utils.k8s import decode_string_b64, get_secret_from_namespace, restart_deployment

logger = logging.getLogger(__name__)


def update_configuration() -> None:
    """
    Function to configure containerd for k3s
    """
    logger.info("Creating k3s 'config.toml.tmpl'.")
    shutil.copyfile(CONFIG_TOML_PATH, CONFIG_TOML_TMPL_PATH)

    logger.info("Modifying k3s 'config.toml.tmpl'.")
    with open(CONFIG_TOML_TMPL_PATH, "r+", encoding="utf-8") as toml_tmpl_file:
        content = toml_tmpl_file.read()
        updated_content = re.sub(
            "\\/var\\/lib\\/rancher\\/k3s\\/agent\\/etc\\/containerd\\/certs\\.d",
            CONTAINERD_CERT_DIR,
            content,
            flags=re.M,
        )
        if content != updated_content:
            toml_tmpl_file.seek(0)
            toml_tmpl_file.truncate()
            toml_tmpl_file.write(updated_content)


def create_certificates(data_folder: str) -> None:
    """
    Function to create certificates for containerd
    """
    internal_registry_secret_name = f"{PLATFORM_NAMESPACE}-internal-registry-ssl"
    logger.info("Removing previous 'host.toml' config.")
    pathlib.Path.unlink(HOSTS_TOML_PATH, missing_ok=True)

    logger.info("Creating internal registry certs directory.")
    cert_directory = pathlib.Path(f"{data_folder}/{INTERNAL_REGISTRY_CERTIFICATES_DIR}")
    pathlib.Path.mkdir(cert_directory, parents=True, exist_ok=True)

    logger.info("Creating new 'host.toml' config.")
    command = f"""
mkdir -p {CONTAINERD_CERT_INTERNAL_REGISTRY}
cat > {HOSTS_TOML_PATH} <<EOL
server = \"https://{INTERNAL_REGISTRY_ADDRESS}\"
[host.\"https://{INTERNAL_REGISTRY_ADDRESS}\"]
  ca = \"{cert_directory}/localhost.crt\"
EOL"""
    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        subprocess_run(["bash", "-c", command], log_file)

    logger.info("Creating tls crt and key locally.")
    internal_registry_certs: V1Secret = get_secret_from_namespace(
        name=internal_registry_secret_name, namespace=PLATFORM_NAMESPACE
    )
    with open(f"{cert_directory}/{CERTIFICATE_FILENAME}", "w") as cert_file:
        cert_file.write(decode_string_b64(internal_registry_certs.data["tls.crt"]))
    with open(f"{cert_directory}/{KEY_FILENAME}", "w") as key_file:
        key_file.write(decode_string_b64(internal_registry_certs.data["tls.key"]))


def deploy_internal_registry(
    config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH
) -> None:
    """
    Method used to deploy cert manager chart
    """
    if not config.lightweight_installer.value:
        full_values_file_name = f"{PLATFORM_INSTALL_PATH}/{INTERNAL_REGISTRY_CHART.values_file}"
        data = {
            "registry": INTERNAL_REGISTRY_ADDRESS,
            "istio_ingress_namespace": ISTIO_GATEWAY_CHART.namespace,
            "ff_ambient_mesh": is_feature_flag_enabled(FeatureFlag.AMBIENT_MESH),
        }
        save_jinja_template(
            source_file=INTERNAL_REGISTRY_CHART.values_template_file, data=data, destination_file=full_values_file_name
        )
        values_file = [full_values_file_name]
        try:
            chart_version = get_target_product_build() if config.lightweight_installer.value else None
            chart_dir = str(os.path.join(charts_dir, INTERNAL_REGISTRY_CHART.directory))
            if chart_version:
                pull_chart(chart_version, chart_dir)
            upsert_chart(
                name=INTERNAL_REGISTRY_CHART.name,
                version=chart_version,
                chart_dir=chart_dir,
                namespace=INTERNAL_REGISTRY_CHART.namespace,
                values=values_file,
            )
        except (ChartInstallationError, ChartPullError) as ex:
            raise InternalRegistryInstallationError from ex

        try:
            update_configuration()
        except Exception as ex:
            raise ContainerdConfigurationError from ex

        try:
            create_certificates(data_folder=config.data_folder.value)
        except Exception as ex:
            raise ContainerdCertificateCreationError from ex

        logger.info("Restarting K3S.")
        with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            subprocess_run(["systemctl", "restart", "k3s"], log_file)

        deployment_name = f"{INTERNAL_REGISTRY_CHART.namespace}-{INTERNAL_REGISTRY_CHART.name}"
        restart_deployment(name=deployment_name, namespace=INTERNAL_REGISTRY_CHART.namespace)
    else:
        logger.info("External registry used, skipping internal registry deploy")
