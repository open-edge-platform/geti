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
A module responsible for detecting if kubernetes is running on k3s environment.
"""

from kubernetes import client

from platform_utils.kube_config_handler import KubernetesConfigHandler


def is_kubernetes_running_on_k3s(kubeconfig_path: str) -> bool:
    """
    Check if Kubernetes cluster is running on K3S.
    """
    KubernetesConfigHandler(kube_config=kubeconfig_path)

    with client.ApiClient() as kube_client:
        api_instance = client.CoreV1Api(kube_client)
        k3s_nodes = api_instance.list_node(
            label_selector="node.kubernetes.io/instance-type=k3s",
        )
        return k3s_nodes.items != []
