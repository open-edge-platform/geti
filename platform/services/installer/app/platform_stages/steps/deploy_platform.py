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
from kubernetes.client import ApiException

from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.charts import PLATFORM_CHART
from constants.paths import K3S_KUBECONFIG_PATH, PLATFORM_INSTALL_PATH, RESOURCE_VALUES_FILE_NAME
from constants.platform import GPU_PROVIDER_INTEL_MAX, GPU_PROVIDER_NVIDIA, INTEL_EMAIL, PLATFORM_NAMESPACE
from platform_configuration.features import FeatureFlag, get_updated_feature_flags, is_feature_flag_enabled
from platform_configuration.versions import get_target_platform_version, get_target_product_build
from platform_stages.steps.errors import (
    AllocatableResourcesError,
    ChartInstallationError,
    ChartPullError,
    GenerateChartsResourcesError,
    PlatformInstallationError,
    StepsError,
)
from platform_utils.calculate_resource_multiplier import calculate_resource_multiplier
from platform_utils.helm import pull_chart, save_jinja_template, upsert_chart
from platform_utils.k8s import decode_string_b64, get_master_node_allocatable_resources, get_secret_from_namespace
from platform_utils.kube_config_handler import KubernetesConfigHandler
from platform_utils.scale_helm_chart_resources import scale_chart_resources

FULL_VALUES_FILE_NAME = str(os.path.join(PLATFORM_INSTALL_PATH, PLATFORM_CHART.values_file))
FULL_RESOURCES_VALUES_FILE_NAME = str(os.path.join(PLATFORM_INSTALL_PATH, RESOURCE_VALUES_FILE_NAME))

logger = logging.getLogger(__name__)


def _generate_chart_resources() -> None:
    """
    Method used to get allocatable resources from master node.
    Generate charts resources based on available resources.
    """
    logger.info("Calculate multiplier based on resources from node.")
    try:
        available_resources = get_master_node_allocatable_resources()
        multiplier = calculate_resource_multiplier(available_resources)
    except ApiException as ex:
        raise AllocatableResourcesError from ex
    logger.info("Multiplier calculated from allocatable resources.")

    logger.info("Scale chart resources.")
    try:
        scale_chart_resources(
            resource_multiplier=multiplier,
            available_master_resources=available_resources,
            charts_directory=PLATFORM_INSTALL_PATH,
            values_file_output_path=FULL_RESOURCES_VALUES_FILE_NAME,
        )
    except Exception as ex:
        raise GenerateChartsResourcesError from ex
    logger.info("Chart resources generated successfully.")


def _obtain_control_plane_ip(kube_config: str = K3S_KUBECONFIG_PATH) -> str:
    KubernetesConfigHandler(kube_config=kube_config)

    with kubernetes.client.ApiClient() as api_client:
        core_api = kubernetes.client.CoreV1Api(api_client)
        try:
            control_plane_node = core_api.list_node(label_selector="node-role.kubernetes.io/control-plane").items[0]
            control_plane_node_ip = next(
                (address.address for address in control_plane_node.status.addresses if address.type == "InternalIP"),
                None,
            )
            if not control_plane_node_ip:
                raise StepsError(f"IP address not found for node: {control_plane_node.metadata.name}")

            return control_plane_node_ip

        except kubernetes.client.exceptions.ApiException as err:
            logger.exception(err)
            raise StepsError from err


def deploy_platform_chart(config: InstallationConfig | UpgradeConfig, charts_dir: str = PLATFORM_INSTALL_PATH) -> None:
    """
    Method used to deploy platform chart
    """

    updated_feature_flags = get_updated_feature_flags()

    data = {
        "registry": config.image_registry.value,
        "geti_registry": config.geti_image_registry.value,
        "product_build": get_target_product_build(),
        "product_version": get_target_platform_version(),
        "data_folder": config.data_folder.value,
        "intel_email": INTEL_EMAIL,
        "grafana_enabled": config.grafana_enabled.value,
        "min_free_disk_space_gib": config.min_free_disk_space_gib.value,
        "running_on_vm": config.running_on_vm.value,
        "feature_flags_data": yaml.safe_dump(updated_feature_flags),
        "ff_oidc_cidaas": updated_feature_flags.get(FeatureFlag.OIDC_CIDAAS),
        "ff_credit_system": updated_feature_flags.get(FeatureFlag.CREDIT_SYSTEM),
        "ff_support_cors": is_feature_flag_enabled(FeatureFlag.SUPPORT_CORS),
        "ff_ambient_mesh": is_feature_flag_enabled(FeatureFlag.AMBIENT_MESH),
        "ff_manage_users": updated_feature_flags.get(FeatureFlag.MANAGE_USERS),
    }

    if config.gpu_support.value:
        if config.gpu_provider.value == GPU_PROVIDER_NVIDIA:
            gpu_label = "nvidia.com/gpu"
        elif config.gpu_provider.value == GPU_PROVIDER_INTEL_MAX:
            gpu_label = "gpu.intel.com/i915"
        else:
            gpu_label = "gpu.intel.com/xe"
        data["gpu_label"] = gpu_label
        data["gpu_support"] = config.gpu_support.value
        data["render_gid"] = config.render_gid.value

    if isinstance(config, InstallationConfig):
        data["smtp_address"] = config.smtp_address.value
        data["smtp_login"] = config.smtp_username.value
        data["smtp_password"] = config.smtp_password.value
        data["smtp_port"] = config.smtp_port.value
        data["sender_address"] = config.sender_address.value
        data["sender_name"] = config.sender_name.value

        data["k8s_server_address"] = config.master_ip_autodetected.value
    else:
        try:
            smtp_secret = get_secret_from_namespace(name="impt-email-config", namespace=PLATFORM_NAMESPACE)
            data["smtp_address"] = decode_string_b64(smtp_secret.data["smtp_host"])
        except kubernetes.client.exceptions.ApiException:
            logger.warning("SMTP address not found")
        data["k8s_server_address"] = _obtain_control_plane_ip()

    save_jinja_template(
        source_file=PLATFORM_CHART.values_template_file, data=data, destination_file=FULL_VALUES_FILE_NAME
    )

    try:
        chart_version = get_target_product_build() if config.lightweight_installer.value else None
        chart_dir = str(os.path.join(charts_dir, PLATFORM_CHART.directory))
        if chart_version:
            pull_chart(chart_version, chart_dir)
        _generate_chart_resources()
        upsert_chart(
            name=PLATFORM_CHART.name,
            version=chart_version,
            chart_dir=chart_dir,
            namespace=PLATFORM_CHART.namespace,
            values=[FULL_VALUES_FILE_NAME, FULL_RESOURCES_VALUES_FILE_NAME],
            timeout="60m",
        )
    except (ChartInstallationError, ChartPullError) as ex:
        raise PlatformInstallationError from ex
