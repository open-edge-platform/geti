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
K3S configuration passed during installation
"""

import os

from GPUtil import getGPUs

from constants.k3s import MIN_FREE_DISK_SPACE_GIB


class K3sConfiguration:
    """
    Manager for K3S configuration.
    """

    def __init__(  # noqa: PLR0913
        self,
        version,  # noqa: ANN001
        disable_components: list[str] | None = None,
        kube_apiserver_args: dict[str, str] | None = None,
        kube_controller_manager_args: dict[str, str] | None = None,
        kube_scheduler_args: dict[str, str] | None = None,
        kubelet_args: dict[str, str] | None = None,
        service_node_port_range: str | None = None,
        node_ip: str | None = None,
    ):
        self.version = version
        self.service_node_port_range = service_node_port_range
        self.node_ip = node_ip

        self.default_runtime = None
        nvidia_gpus = getGPUs()
        if nvidia_gpus:
            self.default_runtime = "nvidia"
            self.disable_components = [component for component in (disable_components or []) if component != "runtimes"]
        else:
            self.disable_components = disable_components or []

        if kube_apiserver_args is None:
            self.kube_apiserver_args = {}
        else:
            self.kube_apiserver_args = kube_apiserver_args

        if kube_controller_manager_args is None:
            self.kube_controller_manager_args = {}
        else:
            self.kube_controller_manager_args = kube_controller_manager_args

        if kube_scheduler_args is None:
            self.kube_scheduler_args = {}
        else:
            self.kube_scheduler_args = kube_scheduler_args

        if kubelet_args is None:
            self.kubelet_args = {}
        else:
            self.kubelet_args = kubelet_args

    def to_env_var_dict(self) -> dict:
        """
        Convert configuration to environment variables dict passable to subprocess env.
        """
        install_k3s_exec_big_str = ""
        for component in self.disable_components:
            install_k3s_exec_big_str += f"--disable {component} "

        if self.default_runtime:
            install_k3s_exec_big_str += f"--default-runtime {self.default_runtime} "

        if self.service_node_port_range:
            install_k3s_exec_big_str += f"--service-node-port-range {self.service_node_port_range} "

        if self.node_ip:
            install_k3s_exec_big_str += f"--node-ip={self.node_ip} "

        flags_mapping = {
            "--kube-apiserver-arg": self.kube_apiserver_args,
            "--kube-controller-manager-arg": self.kube_controller_manager_args,
            "--kube-scheduler-arg": self.kube_scheduler_args,
            "--kubelet-arg": self.kubelet_args,
        }

        for flag, args in flags_mapping.items():
            for arg_name, arg_value in args.items():
                install_k3s_exec_big_str += f"{flag}={arg_name}={arg_value} "

        return {
            "INSTALL_K3S_SKIP_DOWNLOAD": "true",
            "INSTALL_K3S_VERSION": self.version,
            "INSTALL_K3S_EXEC": install_k3s_exec_big_str,
        }


k3s_configuration = K3sConfiguration(
    # in case of version update, update also 'kubectl_image' (charts)
    version=os.getenv("PLATFORM_K3S_VERSION", default="v1.31.0+k3s1"),
    disable_components=["traefik", "runtimes"],
    kube_apiserver_args={
        "enable-admission-plugins": "NodeRestriction,ServiceAccount",
        "request-timeout": "5m0s",
        "audit-log-path": "/var/lib/rancher/k3s/server/logs/audit.log",
        "tls-cipher-suites": "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,"
        "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,"
        "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,"
        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,"
        "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,"
        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
        "audit-log-maxbackup": "10",
        "event-ttl": os.getenv("PLATFORM_K3S_EVENT_TTL", default="1h0m0s"),
    },
    kube_controller_manager_args={
        "terminated-pod-gc-threshold": "1000",
        "leader-elect-lease-duration": "30s",
        "leader-elect-renew-deadline": "20s",
        "bind-address": "127.0.0.1",
    },
    kube_scheduler_args={"bind-address": "127.0.0.1"},
    kubelet_args={
        "streaming-connection-idle-timeout": "5m",
        "rotate-server-certificates": "true",
        "eviction-hard": f"imagefs.available<{MIN_FREE_DISK_SPACE_GIB}Gi,memory.available<100Mi,nodefs.available<{MIN_FREE_DISK_SPACE_GIB}Gi,nodefs.inodesFree<5%",  # noqa: E501
        "eviction-minimum-reclaim": "imagefs.available=1Gi,nodefs.available=1Gi",
        "image-gc-low-threshold": "0",
    },
    service_node_port_range="30000-30050",
)
