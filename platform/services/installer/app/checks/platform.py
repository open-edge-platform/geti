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

"""
A module containing check functions that are interacting with Platform.
"""

import logging
import os
import re
from typing import TYPE_CHECKING

from kubernetes import client

from checks.errors import CheckError, CheckSkipped
from constants.platform import PLATFORM_CONFIGURATION_CM_NAME, PLATFORM_NAMESPACE, PLATFORM_VERSION_CM_KEY
from platform_utils.kube_config_handler import KubernetesConfigHandler
from texts.checks import PlatformCheckTexts

if TYPE_CHECKING:
    from kubernetes.client import V1ConfigMap

logger = logging.getLogger(__name__)

SUPPORTED_VERSIONS = ["2.0.0", "2.0.1", "2.0.2", "2.3.0", "2.3.1", "2.3.2", "2.6.0", "2.7.0"]


def check_platform_version(kubeconfig_path: str) -> None:
    """
    Check Platform's version if it's supported.
    Usage: upgrade
    """
    logger.debug("Checking if Geti platform version is correct.")
    is_platform_version_check_enabled = os.getenv("PLATFORM_VERSION_CHECK", "true")
    if is_platform_version_check_enabled.lower() == "false":
        raise CheckSkipped

    KubernetesConfigHandler(kube_config=kubeconfig_path)

    with client.ApiClient() as kube_client:
        api_instance = client.CoreV1Api(kube_client)
        configuration_configmap: V1ConfigMap = api_instance.read_namespaced_config_map(
            name=PLATFORM_CONFIGURATION_CM_NAME, namespace=PLATFORM_NAMESPACE
        )
        platform_version = configuration_configmap.data[PLATFORM_VERSION_CM_KEY]

    if not any(re.search(supported_version, platform_version) for supported_version in SUPPORTED_VERSIONS):
        raise CheckError(
            PlatformCheckTexts.platform_version_check_error.format(
                platform_version=platform_version, allowed_versions=SUPPORTED_VERSIONS
            )
        )


def check_if_platform_installed(kubeconfig_path: str) -> None:
    """
    Throws CheckError if the platform is installed.
    Usage: install
    """
    logger.debug("Checking if Geti platform is installed.")
    is_platform_version_check_enabled = os.getenv("PLATFORM_VERSION_CHECK", "true")
    if is_platform_version_check_enabled.lower() == "false":
        raise CheckSkipped

    KubernetesConfigHandler(kube_config=kubeconfig_path)

    try:
        with client.ApiClient() as kube_client:
            api_instance = client.CoreV1Api(kube_client)
            api_instance.read_namespaced_config_map(name=PLATFORM_CONFIGURATION_CM_NAME, namespace=PLATFORM_NAMESPACE)
            raise CheckError(PlatformCheckTexts.platform_installed_check_error)

    except client.exceptions.ApiException:
        pass
