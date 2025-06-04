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
A module containing config classes for installation operation.
"""

import os

from cli_utils.credentials import generate_cookie_secret
from configuration_models.base_config_model import BaseConfig, ConfigurationField
from constants.k3s import MIN_FREE_DISK_SPACE_GIB
from constants.operations import INSTALL
from constants.os import SupportedOS
from constants.paths import K3S_INSTALLATION_MARK_FILEPATH, OFFLINE_TOOLS_DIR
from constants.platform import EXTERNAL_REGISTRY_ADDRESS, PLATFORM_REGISTRY_ADDRESS
from validators.email import is_email_valid
from validators.filepath import is_filepath_valid


class InstallationConfig(BaseConfig):
    """
    A Config model for installation operation.
    """

    @property
    def custom_certificate(self) -> bool:
        """
        Return value specifying whether custom certificate settings were provided.
        """
        return bool(self.tls_cert_file.value) and bool(self.tls_key_file.value)

    def __init__(self) -> None:
        self.offer_k8s_option = ConfigurationField(
            type=bool, required=True, value=os.getenv("PLATFORM_K8S_OPTION") == "true"
        )
        self.kube_config = (
            ConfigurationField(type=str, required=False, validation_callback=is_filepath_valid, trim=True)
            if self.offer_k8s_option.value
            else ConfigurationField(type=str, required=False, value="")
        )
        self.username = ConfigurationField(type=str, required=True)
        self.password = ConfigurationField(type=str, required=True)
        self.data_folder = ConfigurationField(type=str, required=False)
        self.tls_cert_file = ConfigurationField(type=str, required=False)
        self.tls_key_file = ConfigurationField(type=str, required=False)

        # to determine local OS
        self.local_os = ConfigurationField(type=str, required=False, value=SupportedOS.UBUNTU.value)

        # to determine if GPU support should be skipped or not,
        # from the client perspective, GPU is always required.
        _skip_gpu_support = os.getenv("PLATFORM_GPU_REQUIRED") == "false"
        self.gpu_support = ConfigurationField(type=bool, required=False, value=not _skip_gpu_support)

        # To determine if a platform is running on a VM or something else. Can be used  to disable resource intensive
        # components such as horizontal pod autoscaling
        platform_infrastructure_type = os.getenv("PLATFORM_INFRASTRUCTURE_TYPE", "")
        self.running_on_vm = ConfigurationField(
            type=bool, required=False, value=platform_infrastructure_type == "VIRTUAL"
        )

        # parameters which are part of config,
        # but are not provided by user
        self.operation = ConfigurationField(type=str, required=False, value=INSTALL)
        self.password_sha = ConfigurationField(type=str, required=False, value=None)
        self.k3s_installation_mark_filepath = ConfigurationField(
            type=str, required=False, value=K3S_INSTALLATION_MARK_FILEPATH
        )

        # To determine whether the LGTM stack should be installed.
        self.grafana_enabled = ConfigurationField(type=bool, required=False, value=False)

        _authorization_cookie_secret = generate_cookie_secret()
        self.authorization_cookie_secret = ConfigurationField(
            type=str, required=False, value=_authorization_cookie_secret
        )

        # To determine if installation is running on k3s.
        self.running_on_k3s = ConfigurationField(type=bool, required=False, value=True)

        self.min_free_disk_space_gib = ConfigurationField(type=int, required=False, value=MIN_FREE_DISK_SPACE_GIB)

        self.master_ip_autodetected = ConfigurationField(type=str, required=False)

        self.gpu_provider = ConfigurationField(type=str, required=False, value="")

        self.internet_access = ConfigurationField(type=bool, required=False, value=True)

        _tools_in_package = self.tools_in_package()
        self.lightweight_installer = ConfigurationField(type=bool, required=False, value=not _tools_in_package)

        self.image_registry = ConfigurationField(type=str, required=False, value=EXTERNAL_REGISTRY_ADDRESS)

        self.geti_image_registry = ConfigurationField(type=str, required=False, value=PLATFORM_REGISTRY_ADDRESS)

        self.smtp_address = ConfigurationField(type=str, required=False, value="")
        self.smtp_port = ConfigurationField(type=int, required=False, value=0)
        self.smtp_username = ConfigurationField(type=str, required=False, value="")
        self.smtp_password = ConfigurationField(type=str, required=False, value="")
        self.sender_address = ConfigurationField(type=str, required=False, validation_callback=is_email_valid)
        self.sender_name = ConfigurationField(type=str, required=False)

    @staticmethod
    def tools_in_package() -> bool:
        return os.path.isdir(OFFLINE_TOOLS_DIR) and bool(os.listdir(OFFLINE_TOOLS_DIR))
