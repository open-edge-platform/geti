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
"""Module containing common paths variables used in the platform installer"""

import sys
from pathlib import Path

from constants.charts import CRDS
from constants.platform import INTERNAL_REGISTRY_ADDRESS

###
# common
###
SYSTEM_PACKAGES_PATH = f"{getattr(sys, '_MEIPASS', '.')}/system-packages.yaml"
OFFLINE_TOOLS_DIR = "tools"
USR_LOCAL_BIN_PATH = "/usr/local/bin/"
OFFLINE_IMAGES_DIR = "images"
PLATFORM_INSTALL_PATH = "/tmp/impp-install"  # noqa: S108
HELM_BINARY = f"{OFFLINE_TOOLS_DIR}/helm"

###
# k3s related
###
K3S_INSTALLATION_MARK_FILEPATH = "/etc/rancher/k3s/impt_k3s"
K3S_KUBECONFIG_PATH = "/etc/rancher/k3s/k3s.yaml"
K3S_REMOTE_KUBECONFIG_PATH = "/etc/rancher/k3s/k3s-remote.yaml"
K3S_UNINSTALL_SCRIPT_PATH = "/usr/local/bin/k3s-uninstall.sh"
K3S_VAR_LIB_RANCHER = "/var/lib/rancher/k3s"
K3S_VAR_LIB_RANCHER_AGENT = f"{K3S_VAR_LIB_RANCHER}/agent"
K3S_VAR_LIB_RANCHER_SERVER = f"{K3S_VAR_LIB_RANCHER}/server"
K3S_AUDIT_LOG_PATH = f"{K3S_VAR_LIB_RANCHER_SERVER}/logs/audit.log"
K3S_IMAGES_DIR_PATH = f"{K3S_VAR_LIB_RANCHER_AGENT}/images"
CONFIG_TOML_PATH = f"{K3S_VAR_LIB_RANCHER_AGENT}/etc/containerd/config.toml"
CONFIG_TOML_TMPL_PATH = f"{K3S_VAR_LIB_RANCHER_AGENT}/etc/containerd/config.toml.tmpl"
K3S_BACKUP_RESTORE_PATH = f"{K3S_VAR_LIB_RANCHER}/backup"
K3S_KILLALL_SCRIPT_PATH = "/usr/local/bin/k3s-killall.sh"
K3S_OFFLINE_INSTALLATION_FILES_PATH = f"{OFFLINE_TOOLS_DIR}/k3s"

###
# logs related
###
PLATFORM_LOGS_DIR = "platform_logs"
K3S_INSTALL_LOG_FILE_PATH = f"{PLATFORM_LOGS_DIR}/k3s_install.log"
K3S_UNINSTALL_LOG_FILE_PATH = f"{PLATFORM_LOGS_DIR}/k3s_uninstall.log"
INSTALL_LOG_FILE_PATH = f"{PLATFORM_LOGS_DIR}/install.log"
CLUSTER_INFO_DIR = f"{PLATFORM_LOGS_DIR}/cluster_info"
DEPLOYMENTS_FILES_DIR = f"{PLATFORM_LOGS_DIR}/deployment_files"
MIGRATION_LOG_FILE_PATH = f"{PLATFORM_LOGS_DIR}/migration.log"

###
# installation related
###
GETI_CONTROLLER_CHART_PATH = f"{getattr(sys, '_MEIPASS', '.')}/geti_controller_chart"
CHARTS_DIR = "charts"
INSTALLER_DIR = "installer"
REDHAT_PACKAGES_PATH = f"{OFFLINE_TOOLS_DIR}/RedHat"
REDHAT_NVIDIA_PACKAGES_PATH = f"{OFFLINE_TOOLS_DIR}/RedHat/nvidia"
K3S_SELINUX_OFFLINE_INSTALLATION_FILES_PATH = f"{REDHAT_PACKAGES_PATH}/k3s-selinux"
UBUNTU_PACKAGES_PATH = f"{OFFLINE_TOOLS_DIR}/Ubuntu"
UBUNTU_NVIDIA_PACKAGES_PATH = f"{OFFLINE_TOOLS_DIR}/Ubuntu/nvidia"
RESOURCE_VALUES_FILE_NAME = "impt-resource-values.yaml"
DATA_CAN_BE_RESTORED_FLAG = ".can_be_restored.flag"
TEMPLATES_DIR = f"{getattr(sys, '_MEIPASS', '..')}/templates"
VERSION_YAML_PATH = f"{getattr(sys, '_MEIPASS', '.')}/version.yaml"
DATA_FOLDER = "/data"

# TODO remove the paths below when GetiController handles the installtion
PLATFORM_CRDS_PATHS: list[str] = [
    f"{CRDS.directory}/charts/cert-manager-{CRDS.name}",
    f"{CRDS.directory}/charts/flyte-{CRDS.name}",
    f"{CRDS.directory}/charts/modelmesh-serving-{CRDS.name}",
]

SIDECAR_ISTIO_CRDS_PATHS: list[str] = [
    f"{CRDS.directory}/charts/istio-{CRDS.name}",
]

AMBIENT_ISTIO_CRDS_PATHS: list[str] = [
    f"{CRDS.directory}/charts/ambient-istio-{CRDS.name}",
    f"{CRDS.directory}/charts/k8s-gateway-api-{CRDS.name}",
]
CONTAINERD_CERT_DIR = "/etc/containerd/certs.d"
CONTAINERD_CERT_INTERNAL_REGISTRY = f"{CONTAINERD_CERT_DIR}/{INTERNAL_REGISTRY_ADDRESS}"
HOSTS_TOML_PATH = Path(f"{CONTAINERD_CERT_INTERNAL_REGISTRY}/hosts.toml")
CERTIFICATE_FILENAME = "localhost.crt"
KEY_FILENAME = "localhost.key"
INTERNAL_REGISTRY_CERTIFICATES_DIR = "internal-registry-certificates"
