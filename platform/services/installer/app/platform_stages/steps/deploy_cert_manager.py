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

from kubernetes.client import ApiException

from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.charts import CERT_MANAGER_CHART
from constants.paths import PLATFORM_INSTALL_PATH
from platform_configuration.versions import get_target_product_build
from platform_stages.steps.errors import (
    CertManagerInstallationError,
    ChartInstallationError,
    ChartPullError,
    GetSecretError,
)
from platform_utils.helm import pull_chart, save_jinja_template, upsert_chart
from platform_utils.k8s import get_secret_from_namespace

FULL_VALUES_FILE_NAME = str(os.path.join(PLATFORM_INSTALL_PATH, CERT_MANAGER_CHART.values_file))
SECRET_NAME = "ca-cert"  # noqa: S105


def deploy_cert_manager_chart(
    config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH
) -> None:
    """
    Method used to deploy cert manager chart
    """
    data = {"registry": config.image_registry.value}
    save_jinja_template(
        source_file=CERT_MANAGER_CHART.values_template_file, data=data, destination_file=FULL_VALUES_FILE_NAME
    )
    values_file = [FULL_VALUES_FILE_NAME]
    try:
        chart_version = get_target_product_build() if config.lightweight_installer.value else None
        chart_dir = str(os.path.join(charts_dir, CERT_MANAGER_CHART.directory))
        if chart_version:
            pull_chart(chart_version, chart_dir)
        upsert_chart(
            name=CERT_MANAGER_CHART.name,
            version=chart_version,
            chart_dir=chart_dir,
            namespace=CERT_MANAGER_CHART.namespace,
            values=values_file,
        )
    except (ChartInstallationError, ChartPullError) as ex:
        raise CertManagerInstallationError from ex

    try:
        get_secret_from_namespace(name=SECRET_NAME, namespace=CERT_MANAGER_CHART.namespace)
    except ApiException as ex:
        raise GetSecretError from ex
