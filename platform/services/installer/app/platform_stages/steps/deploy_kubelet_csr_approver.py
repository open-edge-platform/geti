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
from constants.charts import KUBELET_CSR_APPROVER_CHART
from constants.paths import PLATFORM_INSTALL_PATH
from platform_configuration.versions import get_target_product_build
from platform_stages.steps.errors import ChartInstallationError, ChartPullError, KubeletCSRApproverInstallationError
from platform_utils.helm import pull_chart, upsert_chart

FULL_VALUES_FILE_NAME = str(os.path.join(PLATFORM_INSTALL_PATH, KUBELET_CSR_APPROVER_CHART.values_file))


def deploy_kubelet_csr_approver_chart(
    config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH
) -> None:
    """
    Method used to deploy kubelet csr approver chart
    """

    try:
        chart_version = get_target_product_build() if config.lightweight_installer.value else None
        chart_dir = str(os.path.join(charts_dir, KUBELET_CSR_APPROVER_CHART.directory))
        if chart_version:
            pull_chart(chart_version, chart_dir)
        upsert_chart(
            name=KUBELET_CSR_APPROVER_CHART.name,
            version=chart_version,
            chart_dir=chart_dir,
            namespace=KUBELET_CSR_APPROVER_CHART.namespace,
            sets=f"image.registry={config.image_registry.value},image.repository=local-third-party,image.tag=v1.2.2.3"
            if config.image_registry.value
            else None,
        )
    except (ChartInstallationError, ChartPullError) as ex:
        raise KubeletCSRApproverInstallationError from ex
