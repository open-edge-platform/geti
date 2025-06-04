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

import kubernetes
import yaml

from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.charts import CONTROL_PLANE_CHART
from constants.paths import PLATFORM_INSTALL_PATH
from constants.platform import PLATFORM_NAMESPACE
from platform_configuration.features import FeatureFlag, get_updated_feature_flags, is_feature_flag_enabled
from platform_configuration.versions import get_target_product_build
from platform_stages.steps.errors import ChartInstallationError, ChartPullError, ControlPlaneInstallationError
from platform_utils.helm import pull_chart, save_jinja_template, upsert_chart
from platform_utils.k8s import decode_string_b64, get_secret_from_namespace

logger = logging.getLogger(__name__)
FULL_VALUES_FILE_NAME = str(os.path.join(PLATFORM_INSTALL_PATH, CONTROL_PLANE_CHART.values_file))


def deploy_control_plane_chart(
    config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH
) -> None:
    """
    Install control_plane chart
    """

    updated_feature_flags = get_updated_feature_flags()

    data = {
        "registry": config.image_registry.value,
        "geti_registry": config.geti_image_registry.value,
        "product_build": get_target_product_build(),
        "running_on_vm": config.running_on_vm.value,
        "ff_user_onboarding": updated_feature_flags.get(FeatureFlag.USER_ONBOARDING),
        "ff_credit_system": updated_feature_flags.get(FeatureFlag.CREDIT_SYSTEM),
        "ff_support_cors": is_feature_flag_enabled(FeatureFlag.SUPPORT_CORS),
        "ff_ambient_mesh": is_feature_flag_enabled(FeatureFlag.AMBIENT_MESH),
        "ff_manage_users": updated_feature_flags.get(FeatureFlag.MANAGE_USERS),
        "ff_manage_users_roles": updated_feature_flags.get("FEATURE_FLAG_MANAGE_USERS_ROLES"),
        "ff_acc_svc_mod": updated_feature_flags.get("FEATURE_FLAG_ACC_SVC_MOD"),
        "feature_flags_data": yaml.safe_dump(updated_feature_flags),
        "ff_req_acc": updated_feature_flags.get("FEATURE_FLAG_REQ_ACCESS"),
    }

    if isinstance(config, InstallationConfig):
        data["user_login"] = config.username.value
        data["user_password"] = config.password.value
        data["smtp_address"] = config.smtp_address.value
        data["smtp_port"] = config.smtp_port.value

    else:
        try:
            smtp_secret = get_secret_from_namespace(name="impt-email-config", namespace=PLATFORM_NAMESPACE)
            data["smtp_address"] = decode_string_b64(smtp_secret.data["smtp_host"])
            data["smtp_port"] = decode_string_b64(smtp_secret.data["smtp_port"])
        except kubernetes.client.exceptions.ApiException:
            logger.warning("SMTP address not found")

    data["login"] = config.username.value
    data["password_hash"] = config.password_sha.value
    data["data_folder"] = config.data_folder.value

    if config.tls_cert_file and config.tls_key_file and config.tls_cert_file.value and config.tls_key_file.value:
        with open(config.tls_cert_file.value, "rb") as cert_file:
            data["tls_cert"] = cert_file.read().decode("utf-8")

        with open(config.tls_key_file.value, "rb") as key_file:
            data["tls_key"] = key_file.read().decode("utf-8")

    save_jinja_template(CONTROL_PLANE_CHART.values_template_file, data, FULL_VALUES_FILE_NAME)

    try:
        chart_version = get_target_product_build() if config.lightweight_installer.value else None
        chart_dir = str(os.path.join(charts_dir, CONTROL_PLANE_CHART.directory))
        if chart_version:
            pull_chart(chart_version, chart_dir)
        upsert_chart(
            name=CONTROL_PLANE_CHART.name,
            version=chart_version,
            chart_dir=chart_dir,
            namespace=CONTROL_PLANE_CHART.namespace,
            values=[FULL_VALUES_FILE_NAME],
        )
    except (ChartInstallationError, ChartPullError) as ex:
        raise ControlPlaneInstallationError from ex
