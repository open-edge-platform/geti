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

"""Module used to retrieve information about platform configuration."""

from typing import TYPE_CHECKING

from kubernetes import client
from kubernetes import client as kube_client
from urllib3.exceptions import HTTPError

from constants.platform import DATA_STORAGE_VOLUME_NAME, PLATFORM_NAMESPACE
from platform_configuration.errors import ConfigurationError
from platform_utils.kube_config_handler import KubernetesConfigHandler

if TYPE_CHECKING:
    from kubernetes.client import V1DeploymentList


DEPLOYMENT_NAME_GRAFANA = f"{PLATFORM_NAMESPACE}-grafana"


def get_data_folder_path(kubeconfig: str) -> str:
    """
    Get data folder path
    """
    KubernetesConfigHandler(kube_config=kubeconfig)
    with kube_client.ApiClient() as api_client:
        api_instance = kube_client.CoreV1Api(api_client)
        return api_instance.read_persistent_volume(DATA_STORAGE_VOLUME_NAME).spec.host_path.path


def is_grafana_installed(kubeconfig_path: str) -> bool:
    """Checks whether the Grafana stack is installed.

    :param kubeconfig_path: Path to kubeconfig.
    :return bool: True if the Grafana stack is installed, otherwise False.
    :raises ConfigurationError: On failure to check that Grafana is installed.
    """
    KubernetesConfigHandler(kube_config=kubeconfig_path)
    with client.ApiClient() as api_client:
        apps_v1_api = client.AppsV1Api(api_client)
        try:
            deployment_list: V1DeploymentList = apps_v1_api.list_namespaced_deployment(PLATFORM_NAMESPACE)
        except HTTPError as err:
            raise ConfigurationError("Failed to list the platform's deployments.") from err

        return any(item.metadata.name == DEPLOYMENT_NAME_GRAFANA for item in deployment_list.items)
