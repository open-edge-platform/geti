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

from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.charts import CERT_MANAGER_ISTIO_CSR_CHART
from constants.paths import PLATFORM_INSTALL_PATH
from platform_configuration.features import FeatureFlag, is_feature_flag_enabled
from platform_configuration.versions import get_target_product_build
from platform_stages.steps.errors import CertManagerIstioCSRInstallationError, ChartInstallationError, ChartPullError
from platform_utils.helm import pull_chart, save_jinja_template, upsert_chart

FULL_VALUES_FILE_NAME = str(os.path.join(PLATFORM_INSTALL_PATH, CERT_MANAGER_ISTIO_CSR_CHART.values_file))


def deploy_cert_manager_istio_csr_chart(
    config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH
) -> None:
    """
    Method used to deploy cert manager chart
    """
    ambient_mesh = is_feature_flag_enabled(FeatureFlag.AMBIENT_MESH)
    data = {"registry": config.image_registry.value, "ff_ambient_mesh": ambient_mesh}
    save_jinja_template(
        source_file=CERT_MANAGER_ISTIO_CSR_CHART.values_template_file, data=data, destination_file=FULL_VALUES_FILE_NAME
    )
    values_file = [FULL_VALUES_FILE_NAME]
    try:
        chart_version = get_target_product_build() if config.lightweight_installer.value else None
        chart_dir = str(os.path.join(charts_dir, CERT_MANAGER_ISTIO_CSR_CHART.directory))
        if chart_version:
            pull_chart(chart_version, chart_dir)
        upsert_chart(
            name=CERT_MANAGER_ISTIO_CSR_CHART.name,
            version=chart_version,
            chart_dir=chart_dir,
            namespace=CERT_MANAGER_ISTIO_CSR_CHART.namespace,
            values=values_file,
        )
    except (ChartInstallationError, ChartPullError) as ex:
        raise CertManagerIstioCSRInstallationError from ex
