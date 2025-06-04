# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.
"""Module used to retrieve platform versions"""

import yaml
from kubernetes import client as kube_client
from kubernetes.client.rest import ApiException

from constants.paths import VERSION_YAML_PATH
from constants.platform import PLATFORM_NAMESPACE
from platform_utils.kube_config_handler import KubernetesConfigHandler


def get_current_platform_version(kubeconfig_path: str) -> str:
    """Retrieves current platform version from the impt-versions configmap"""
    KubernetesConfigHandler(kube_config=kubeconfig_path)
    try:
        with kube_client.ApiClient() as client:
            core_api = kube_client.CoreV1Api(client)
            result = core_api.read_namespaced_config_map(f"{PLATFORM_NAMESPACE}-versions", PLATFORM_NAMESPACE)
        return result.data["platformVersion"]
    except ApiException:
        return "unknown version"


def get_target_platform_version() -> str:
    """Retrieves target platform version of the running installer from the config file"""
    with open(VERSION_YAML_PATH) as yaml_file:
        return yaml.safe_load(yaml_file)["product_version"]


def get_target_product_build() -> str:
    """Retrieves target build version of the running installer from the config file"""
    with open(VERSION_YAML_PATH) as yaml_file:
        return yaml.safe_load(yaml_file)["product_build"]
