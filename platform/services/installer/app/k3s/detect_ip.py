# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
A module responsible for getting IP address of kubernetes master node or from local network interfaces.
"""

import logging
from ipaddress import IPv4Address
from typing import cast

import ifaddr
from kubernetes import client

from platform_utils.kube_config_handler import KubernetesConfigHandler

logger = logging.getLogger(__name__)


def get_master_node_ip_address(kubeconfig_path: str) -> str:
    """
    Get IP address of master node
    """
    KubernetesConfigHandler(kube_config=kubeconfig_path)

    with client.ApiClient() as api_client:
        api_instance = client.CoreV1Api(api_client)
        nodes = api_instance.list_node(pretty=True)
        nodes = [node for node in nodes.items if "node-role.kubernetes.io/control-plane" in node.metadata.labels]

        addresses = nodes[0].status.addresses

        return next(i.address for i in addresses if i.type == "InternalIP")


def get_first_public_ip() -> str | None:
    """
    Get first non-local IPv4 machine's network interface address. Return 'None' if no address is found.
    Prefer public ip over private, but private will be used when no public ip's available.
    """
    adapters = ifaddr.get_adapters()
    logger.debug("Getting first public IPv4 machine's network interface address.")
    for adapter in adapters:
        for adapter_ip in adapter.ips:
            if not adapter_ip.is_IPv4:
                continue
            if not IPv4Address(adapter_ip.ip).is_private:
                # for ipv4 it is always a string according to ifaddr docs
                return cast("str", adapter_ip.ip)

    logger.debug("Getting first private IPv4 machine's network interface address.")
    for adapter in adapters:
        for adapter_ip in adapter.ips:
            if not adapter_ip.is_IPv4:
                continue
            if IPv4Address(adapter_ip.ip).is_private and not IPv4Address(adapter_ip.ip).is_loopback:
                # for ipv4 it is always a string according to ifaddr docs
                return cast("str", adapter_ip.ip)
    return None
