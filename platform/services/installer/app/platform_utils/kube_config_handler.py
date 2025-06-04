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

from kubernetes import config

from constants.paths import K3S_KUBECONFIG_PATH


class KubernetesConfigHandler:
    """
    Singleton class to manage the loading and reloading of Kubernetes configuration.

    This class ensures that the Kubernetes configuration is loaded only once
    and provides a mechanism to reload the configuration with a different
    kubeconfig file if necessary.
    """

    _instance = None

    def __new__(cls, kube_config: str = K3S_KUBECONFIG_PATH):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_kube_config(kube_config=kube_config)
        return cls._instance

    @classmethod
    def _load_kube_config(cls, kube_config: str = K3S_KUBECONFIG_PATH):
        config.load_kube_config(config_file=kube_config)
        return config

    @classmethod
    def reload(cls, kube_config: str):
        cls._instance = None
        cls._instance = cls(kube_config)
        return cls._instance
