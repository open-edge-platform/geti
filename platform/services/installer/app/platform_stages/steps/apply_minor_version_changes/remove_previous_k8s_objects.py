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
from typing import TYPE_CHECKING

from platform_stages.steps.errors import RemovePreviousK8SObjectsError
from platform_utils.kube_config_handler import KubernetesConfigHandler

if TYPE_CHECKING:
    from collections.abc import Callable

import kubernetes

from constants.paths import K3S_KUBECONFIG_PATH

logger = logging.getLogger(__name__)


def _remove_flyte_secret():
    with kubernetes.client.ApiClient() as api_client:
        core_api = kubernetes.client.CoreV1Api(api_client)
        try:
            core_api.delete_namespaced_secret(name="flyte-pod-webhook", namespace="flyte")
        except kubernetes.client.exceptions.ApiException as ex:
            if ex.status != 404:
                logger.error("Error when accessing the Kubernetes API.", exc_info=True)
                raise RemovePreviousK8SObjectsError from ex


def _remove_modelmesh_webhook_conf():
    with kubernetes.client.ApiClient() as api_client:
        admission_registration_api = kubernetes.client.AdmissionregistrationV1Api(api_client)
        try:
            admission_registration_api.delete_validating_webhook_configuration(name="servingruntime.serving.kserve.io")
        except kubernetes.client.exceptions.ApiException as ex:
            if ex.status != 404:
                logger.error("Error when accessing the Kubernetes API.", exc_info=True)
                raise RemovePreviousK8SObjectsError from ex


def remove_previous_k8s_objects() -> None:
    """
    Remove previous k8s objects during upgrade
    """
    logger.info("Removing previous k8s objects.")
    KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)

    tasks: list[Callable] = [_remove_flyte_secret, _remove_modelmesh_webhook_conf]

    for task in tasks:
        task()
    logger.info("Previous k8s objects removed.")
