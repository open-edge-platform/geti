# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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
from constants.charts import ISTIO_ZTUNNEL_CHART
from constants.paths import PLATFORM_INSTALL_PATH
from platform_configuration.features import FeatureFlag, is_feature_flag_enabled
from platform_configuration.versions import get_target_product_build
from platform_stages.steps.errors import ChartInstallationError, ChartPullError, IstioIstiodInstallationError
from platform_utils.helm import pull_chart, save_jinja_template, upsert_chart

FULL_VALUES_FILE_NAME = str(os.path.join(PLATFORM_INSTALL_PATH, ISTIO_ZTUNNEL_CHART.values_file))


def deploy_istio_ztunnel_chart(
    config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH
) -> None:
    """
    Method used to deploy Istio ztunnel chart
    """
    if not is_feature_flag_enabled(FeatureFlag.AMBIENT_MESH):
        return
    data = {"registry": config.image_registry.value}
    save_jinja_template(
        source_file=ISTIO_ZTUNNEL_CHART.values_template_file, data=data, destination_file=FULL_VALUES_FILE_NAME
    )
    values_file = [FULL_VALUES_FILE_NAME]

    try:
        chart_version = get_target_product_build() if config.lightweight_installer.value else None
        chart_dir = str(os.path.join(charts_dir, ISTIO_ZTUNNEL_CHART.directory))
        if chart_version:
            pull_chart(chart_version, chart_dir)
        upsert_chart(
            name=ISTIO_ZTUNNEL_CHART.name,
            version=chart_version,
            chart_dir=chart_dir,
            namespace=ISTIO_ZTUNNEL_CHART.namespace,
            values=values_file,
        )
    except (ChartInstallationError, ChartPullError) as ex:
        raise IstioIstiodInstallationError from ex
