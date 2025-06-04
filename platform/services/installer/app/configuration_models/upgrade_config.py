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
A module containing config classes for upgrade operation.
"""

import os

from configuration_models.base_config_model import BaseConfig, ConfigurationField
from constants.k3s import MIN_FREE_DISK_SPACE_GIB
from constants.operations import UPGRADE
from constants.os import SupportedOS
from constants.paths import K3S_INSTALLATION_MARK_FILEPATH, K3S_KUBECONFIG_PATH, OFFLINE_TOOLS_DIR
from constants.platform import EXTERNAL_REGISTRY_ADDRESS, INTERNAL_REGISTRY_ADDRESS, PLATFORM_REGISTRY_ADDRESS
from validators.filepath import is_filepath_valid
from validators.path import is_path_valid


class UpgradeConfig(BaseConfig):
    """
    A Config model for upgrade operation.
    """

    @staticmethod
    def tools_in_package() -> bool:
        return os.path.isdir(OFFLINE_TOOLS_DIR) and bool(os.listdir(OFFLINE_TOOLS_DIR))

    @property
    def interactive_mode(self) -> bool:
        """Determines whether config file was used or interactive mode"""
        return self._interactive_mode

    def validate(self) -> None:
        if self.skip_backup.value is False:
            self.backup_location.required = True
            self.backup_location.validation_callback = is_path_valid
        super().validate()

    def __init__(self, interactive_mode: bool) -> None:
        self._interactive_mode = interactive_mode

        self.offer_k8s_option = ConfigurationField(
            type=bool, required=True, value=os.getenv("PLATFORM_K8S_OPTION") == "true"
        )
        self.kube_config = (
            ConfigurationField(type=str, required=True, validation_callback=is_filepath_valid, trim=True)
            if self.offer_k8s_option.value
            else ConfigurationField(type=str, required=False, value=K3S_KUBECONFIG_PATH)
        )
        # set current platform version
        self.current_platform_version = ConfigurationField(type=str, required=False)

        # to determine local OS
        self.local_os = ConfigurationField(type=str, required=False, value=SupportedOS.UBUNTU.value)

        # to determine if GPU support should be skipped or not,
        # from the client perspective, GPU is always required.
        _skip_gpu_support = os.getenv("PLATFORM_GPU_REQUIRED") == "false"
        self.gpu_support = ConfigurationField(type=bool, required=False, value=not _skip_gpu_support)
        self.render_gid = ConfigurationField(type=int, required=False, value=0)

        # parameters which are part of config,
        # but are not provided by user
        self.operation = ConfigurationField(type=str, required=False, value=UPGRADE)

        self.k3s_installation_mark_filepath = ConfigurationField(
            type=str, required=False, value=K3S_INSTALLATION_MARK_FILEPATH
        )

        # To determine if upgrade is running on k3s.
        self.running_on_k3s = ConfigurationField(type=bool, required=False, value=False)
        self.min_free_disk_space_gib = ConfigurationField(type=int, required=False, value=MIN_FREE_DISK_SPACE_GIB)

        self.skip_backup = ConfigurationField(type=bool, required=False)
        self.backup_location = ConfigurationField(type=str, required=False, trim=True)

        # To determine if upgrade should install istio ingressgateway
        self.istio_ingress_gateway = ConfigurationField(type=bool, required=False, value=False)

        self.gpu_provider = ConfigurationField(type=str, required=False, value="")

        # To determine if a platform is running on a VM or something else. Can be used  to disable resource intensive
        # components such as horizontal pod autoscaling
        platform_infrastructure_type = os.getenv("PLATFORM_INFRASTRUCTURE_TYPE", "")
        self.running_on_vm = ConfigurationField(
            type=bool, required=False, value=platform_infrastructure_type == "VIRTUAL"
        )

        self.internet_access = ConfigurationField(type=bool, required=False, value=True)

        _tools_in_package = self.tools_in_package()
        self.lightweight_installer = ConfigurationField(type=bool, required=False, value=not _tools_in_package)

        registry = EXTERNAL_REGISTRY_ADDRESS if not _tools_in_package else INTERNAL_REGISTRY_ADDRESS
        self.image_registry = ConfigurationField(type=str, required=False, value=registry)

        _docker_registry = PLATFORM_REGISTRY_ADDRESS if not _tools_in_package else INTERNAL_REGISTRY_ADDRESS
        self.geti_image_registry = ConfigurationField(type=str, required=False, value=_docker_registry)

        self.data_folder = ConfigurationField(type=str, required=False)
