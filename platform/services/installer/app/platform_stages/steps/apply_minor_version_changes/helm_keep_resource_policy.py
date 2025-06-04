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

import logging
import re
import subprocess
from collections import namedtuple

from cli_utils.platform_logs import subprocess_run
from configuration_models.upgrade_config import UpgradeConfig
from constants.paths import INSTALL_LOG_FILE_PATH, K3S_KUBECONFIG_PATH

logger = logging.getLogger(__name__)

# As for those versions, the issue with the pending training arises
# due to the disappearing namespace and flyte workflow CRD.
# We need to explicitly mark and unmark these resources to ensure they are kept intact.
VALID_VERSION_PATTERNS = [r"^2\.0\..*", r"^2\.3\..*", r"^2\.6\..*"]

ResourceToHandle = namedtuple("ResourceToHandle", ["name", "namespace", "type"])  # noqa: PYI024

RESOURCES_TO_HANDLE_VERSION = (
    ResourceToHandle(name="impt-jobs-production", namespace=None, type="namespace"),
    ResourceToHandle(name="flyteworkflows.flyte.lyft.com", namespace=None, type="crd"),
)

RESOURCES_TO_HANDLE_ALWAYS = (
    ResourceToHandle(name="custom-tls", namespace="istio-system", type="secret"),
    ResourceToHandle(name="custom-tls", namespace="istio-system", type="certificate"),
)


def resource_exists(resource: ResourceToHandle) -> bool:
    """Check if a resource exists."""
    check_cmd = [
        "kubectl",
        f"--kubeconfig={K3S_KUBECONFIG_PATH}",
        "get",
        resource.type,
        resource.name,
    ]
    if resource.namespace:
        check_cmd.extend(["-n", resource.namespace])

    result = subprocess.run(check_cmd, capture_output=True, text=True, check=False)  # noqa: S603
    return result.returncode == 0


def add_remove_annotation(resource: ResourceToHandle, operation: str) -> None:
    """
    Add or remove annotation 'helm.sh/resource-policy'
    """
    logger.info(f"{operation} 'helm.sh/resource-policy' annotation to '{resource.type}/{resource.name}'")
    annotate_cmd = [
        "kubectl",
        f"--kubeconfig={K3S_KUBECONFIG_PATH}",
        "annotate",
        resource.type,
        resource.name,
    ]
    if resource.namespace:
        annotate_cmd.extend(["-n", resource.namespace])

    if operation == "add":
        annotate_cmd.extend(["helm.sh/resource-policy=keep"])
    else:
        annotate_cmd.extend(["helm.sh/resource-policy-"])

    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        subprocess_run(
            annotate_cmd,
            log_file,
        )


def modify_helm_keep_resource_policy(config: UpgradeConfig, operation: str) -> None:
    """
    Add or remove 'helm.sh/resource-policy: keep' annotation from annotated objects during upgrade.
    Supported operations: add, remove.
    """

    for resource in RESOURCES_TO_HANDLE_ALWAYS:
        if resource_exists(resource):
            add_remove_annotation(resource, operation)

    if not any(re.match(pattern, config.current_platform_version.value) for pattern in VALID_VERSION_PATTERNS):
        return

    for resource in RESOURCES_TO_HANDLE_VERSION:
        if resource_exists(resource):
            add_remove_annotation(resource, operation)


def add_helm_keep_resource_policy(config: UpgradeConfig) -> None:
    """
    Add 'helm.sh/resource-policy: keep' annotation to annotated objects before upgrade.
    """
    modify_helm_keep_resource_policy(config=config, operation="add")


def remove_helm_keep_resource_policy(config: UpgradeConfig) -> None:
    """
    Remove 'helm.sh/resource-policy: keep' annotation from annotated objects after upgrade.
    """
    modify_helm_keep_resource_policy(config=config, operation="remove")
