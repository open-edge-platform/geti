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
from constants.charts import PV_CHART
from constants.paths import PLATFORM_INSTALL_PATH
from platform_configuration.versions import get_target_product_build
from platform_stages.steps.errors import ChartInstallationError, ChartPullError, PVInstallationError
from platform_utils.helm import pull_chart, upsert_chart


def deploy_pv_chart(config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH) -> None:
    """
    Method used to deploy pv and pvc to mount directory defined by 'data_folder'
    """
    try:
        chart_version = get_target_product_build() if config.lightweight_installer.value else None
        chart_dir = str(os.path.join(charts_dir, PV_CHART.directory))
        if chart_version:
            pull_chart(chart_version, chart_dir)
        upsert_chart(
            name=PV_CHART.name,
            version=chart_version,
            chart_dir=chart_dir,
            sets=f"dataStoragePath={config.data_folder.value}",
            namespace=PV_CHART.namespace,
        )
    except (ChartInstallationError, ChartPullError) as ex:
        raise PVInstallationError from ex
