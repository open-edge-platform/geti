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

from kubernetes import client

from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.charts import MIGRATION_JOB
from constants.paths import MIGRATION_LOG_FILE_PATH, PLATFORM_INSTALL_PATH
from platform_configuration.features import FeatureFlag, is_feature_flag_enabled
from platform_configuration.versions import get_target_product_build
from platform_stages.steps.errors import ChartInstallationError, ChartPullError, MigrationInstallationError
from platform_utils.helm import pull_chart, save_jinja_template, upsert_chart
from platform_utils.k8s import collect_job_logs
from platform_utils.kube_config_handler import KubernetesConfigHandler

logger = logging.getLogger(__name__)
FULL_VALUES_FILE_NAME = str(os.path.join(PLATFORM_INSTALL_PATH, MIGRATION_JOB.values_file))


def deploy_migration_job(config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH) -> None:
    """
    Deploy platform migration job
    """

    data = {
        "registry": config.image_registry.value,
        "geti_registry": config.geti_image_registry.value,
        "product_build": get_target_product_build(),
        "grafana_enabled": config.grafana_enabled.value,
        "ff_ambient_mesh": is_feature_flag_enabled(FeatureFlag.AMBIENT_MESH),
    }

    save_jinja_template(
        source_file=MIGRATION_JOB.values_template_file, data=data, destination_file=FULL_VALUES_FILE_NAME
    )

    logger.info("Running migration.")
    KubernetesConfigHandler(kube_config=config.kube_config.value)
    with client.ApiClient() as api_client:
        v1_api = client.CoreV1Api(api_client)
        try:
            chart_version = get_target_product_build() if config.lightweight_installer.value else None
            chart_dir = str(os.path.join(charts_dir, MIGRATION_JOB.directory))
            if chart_version:
                pull_chart(chart_version, chart_dir)
            upsert_chart(
                name=MIGRATION_JOB.name,
                version=chart_version,
                chart_dir=chart_dir,
                namespace=MIGRATION_JOB.namespace,
                values=[FULL_VALUES_FILE_NAME],
                timeout="5000m",
            )
            logger.info("Migration completed.")
        except (ChartInstallationError, ChartPullError) as ex:
            raise MigrationInstallationError from ex
        finally:
            logger.info(f"Saving migration logs to {MIGRATION_LOG_FILE_PATH}")
            collect_job_logs(
                api=v1_api,
                job_name=MIGRATION_JOB.name,
                namespace=MIGRATION_JOB.namespace,
                log_file=MIGRATION_LOG_FILE_PATH,
            )
