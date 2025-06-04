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
import os

from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.charts import CRDS
from constants.paths import (
    AMBIENT_ISTIO_CRDS_PATHS,
    PLATFORM_CRDS_PATHS,
    PLATFORM_INSTALL_PATH,
    SIDECAR_ISTIO_CRDS_PATHS,
)
from platform_configuration.features import FeatureFlag, is_feature_flag_enabled
from platform_configuration.versions import get_target_product_build
from platform_stages.steps.errors import ChartInstallationError, ChartPullError, CRDsInstallationError
from platform_utils.helm import pull_chart, upsert_chart

logger = logging.getLogger(__name__)


def deploy_crds_chart(config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH) -> None:
    """
    Deploys CRD charts to ensure that the size of the Helm release metadata stored in the Kubernetes Secret
    does not exceed the 1MB limit.

    This method iterates over the charts in the CRDs umbrella chart and deploys each one individually.
    By deploying the charts separately, it helps to avoid the issue where the combined size of the Helm
    release metadata exceeds the Kubernetes Secret size limit.

    Args:
        charts_dir (str): The base directory where the CRD charts are located.
                          Defaults to PLATFORM_INSTALL_PATH.

    Raises:
        CRDsInstallationError: If an error occurs during the installation of any chart.
    """
    crds_charts_paths = PLATFORM_CRDS_PATHS + (
        AMBIENT_ISTIO_CRDS_PATHS if is_feature_flag_enabled(FeatureFlag.AMBIENT_MESH) else SIDECAR_ISTIO_CRDS_PATHS
    )
    chart_version = get_target_product_build() if config.lightweight_installer.value else None
    for chart_path in crds_charts_paths:
        release_name = os.path.basename(chart_path)
        chart_dir = f"{charts_dir}/{chart_path}"
        try:
            logger.info(f"Deploying chart: {release_name} from {chart_dir}")
            if chart_version:
                pull_chart(chart_version, chart_dir)
            upsert_chart(
                name=release_name,
                version=chart_version,
                chart_dir=chart_dir,
                namespace=CRDS.namespace,
            )
            logger.info(f"Successfully deployed chart: {release_name} from {chart_dir}")
        except (ChartInstallationError, ChartPullError) as ex:
            logger.error(f"Failed to deploy chart: {release_name} from {chart_dir}")
            raise CRDsInstallationError from ex
