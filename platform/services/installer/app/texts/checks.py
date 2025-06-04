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
Strings that are shown to the user by checks functions.
"""


class InternetConnectionChecksTexts:
    """
    Strings used during Internet Connection checks.
    """

    internet_connection_check_start = "Checking internet connection..."
    internet_connection_check_error = "Cannot connect to the Internet. Check your network and proxy settings."


class DNSChecksTexts:
    """
    Strings used during DNS configuration checks.
    """

    dns_ipv4_config_check = "Checking DNS configuration ..."
    dns_ipv4_check_error = "Didn't receive DNS response for IPv4. Make sure your DNS is able to resolve to IPv4."


class K3SChecksTexts:
    """
    Strings that are shown to the user by k3s checks functions.
    """

    check_k3s_installed_by_installer = "Checking if k3s was installed by platform installer..."
    check_k3s_installed_by_installer_error = "Kubernetes cluster not installed by the platform installer."
    check_k3s_default_config_exists = "Checking if k3s installed on this machine..."
    check_k3s_default_config_exists_error = "k3s default config file not found. Platform not installed on this machine."


class K8SChecksTexts:
    """
    Strings that are shown to the user by K8S checks functions.
    """

    already_installed_k8s_check_start = "Checking if Kubernetes is already installed..."
    already_installed_k8s_check_error = (
        "Port {port} is in use. It seems Kubernetes is already installed on this machine."
    )
    connection_check_start = "Checking connection to Kubernetes..."
    connection_check_error = "Cannot connect to Kubernetes. Ensure that the provided kubeconfig file is valid."
    cluster_version_check_start = "Checking Kubernetes cluster version..."
    cluster_version_check_error = (
        "Not supported Kubernetes cluster version: {cluster_version}. "
        "The list of supported versions can be found in the installation manual."
    )
    cpu_requirements_check_start = "Checking CPU cores available on Kubernetes nodes..."
    cpu_requirements_check_error = "Available CPU cores on nodes: {cpu_capacity}. Min: {cpu_requirement} cores."
    mem_requirements_check_start = "Checking memory available on Kubernetes nodes..."
    mem_requirements_check_error = "Available memory on nodes: {mem_capacity}. Min: {mem_requirement}."
    gpu_requirements_check_start = "Checking if GPU card is present on Kubernetes nodes..."
    gpu_requirements_check_error = (
        "GPU card is not present on none of the nodes. "
        "Ensure that at least one GPU card is present on at least one node."
    )
    storage_requirements_check_start = "Checking if there is enough space to perform the data folder backup..."
    backup_location_storage_requirements_check_start = (
        "Checking if there is enough space under '{location}' to perform the data folder backup..."
    )
    storage_requirements_check_error = (
        "Insufficient storage available under '{location}' to perform the data folder backup. "
        "Available: {available_storage:,} MB, required: {required_storage:,} MB."
    )
    istio_ingress_installed_check_start = "Checking if Istio Ingress Gateway is installed and configured..."
    istio_ingress_version_check_start = "Checking Istio Ingress Gateway version..."
    istio_ingress_gateway_installation_check_error = (
        "Istio Ingress Gateway not found. Deploy supported version on your Kubernetes cluster. "
        "The list of supported versions can be found in the installation manual."
    )
    istio_ingress_gateway_ip_configuration_check_error = (
        "Istio Ingress Gateway configuration error: external IP of the load balancer is invalid or not configured. "
        "Please ensure it is set to a valid IP address."
    )
    istio_gateway_configuration_check_error = (
        "Istio Ingress Gateway configuration error: Gateway CRD not found. "
        "Please ensure the Gateway is configured as specified in the installation manual."
    )
    istio_ingress_gateway_version_check_error = (
        "Not supported Istio Ingress Gateway version: {present_istio_version}. "
        "The list of supported versions can be found in the installation manual."
    )
    istio_ingress_gateway_connection_error = "Failed to connect to Istio Ingress Gateway. Ensure its pod is running."
    metrics_server_installed_check_start = "Checking if metrics-server is installed..."
    metrics_server_version_check_start = "Checking metrics-server version..."
    metrics_server_installation_check_error = (
        "Component metrics-server not found. Deploy supported version on your Kubernetes cluster. "
        "The list of supported versions can be found in the installation manual."
    )
    metrics_server_not_running_check_error = (
        "Component metrics-server found, but not running. Ensure component metrics-server is running."
    )
    metrics_server_version_check_error = (
        "Not supported metrics-server version: {version}. "
        "The list of supported versions can be found in the installation manual."
    )
    metrics_server_connection_error = "Failed to connect to metrics-server. Ensure component metrics-server is running."


class LocalOSChecksTexts:
    """
    Strings used during Local OS checks.
    """

    os_check_start = "Checking local OS..."
    os_check_warning = (
        "Your OS: {local_os}. This application has been validated on: {supported_oses}.\n"
        "The installation may not succeed."
    )
    os_check_error = "Supported local OS: {supported_oses}, your OS: {local_os}."
    unknown_os_name = "UNKNOWN"


# class CurlChecksTexts:
class ToolsChecksTexts:
    """
    Strings used during tools checks.
    """

    req_tools_check_start = "Checking if all required tools are configured..."
    curl_check_inet_connection_error = "curl has no access to the Internet when run with sudo."
    curl_installed_by_snap = (
        "curl has been installed using snap. Uninstall it and install using apt (sudo apt install curl)"
    )


class LocalUserChecksTexts:
    """
    Strings used during Local user checks.
    """

    user_check_start = "Checking local user..."
    user_check_error = (
        "The installer can be run only by a user with root permissions. "
        "Run the installer with 'sudo' as described in the installation manual."
    )


class PlatformCheckTexts:
    """
    Strings used during Platform checks.
    """

    platform_version_check_error = (
        "Installed platform's version: {platform_version}. "
        "Only the following versions can be upgraded using this installer: "
        "{allowed_versions}."
    )
    platform_installed_check_error = "Platform is already installed."
    platform_license_check_start = "Checking the installed platform's license..."
    platform_license_check_missing_pods_error = "Unable to check the license."
    platform_license_check_invalid_license_error = "License is not valid."
    platform_version_check_start = "Checking the installed platform's version..."
    platform_installed_check_start = "Checking if the platform is installed..."
    platform_not_installed_check_error = "Platform is already uninstalled from the cluster."


class PortsAvailabilityCheckTexts:
    """
    Strings used during ports availability checks.
    """

    check_error = "Cannot check required ports."
    ports_availability_check_start = "Checking if all required ports are available..."
    ports_availability_check_error = (
        "It seems that port(s): {occupied_ports} are already in use. Uninstall apps or services that use them."
    )


class ResourcesChecksTexts:
    """
    Strings that are shown to the user by local resources checks functions.
    """

    gpu_driver_check_start = "Checking if GPU driver is installed..."
    gpu_driver_check_error = "GPU card driver not detected."
    gpu_driver_version_check_start = "Checking GPU driver version..."
    gpu_driver_version_check_error = (
        "Nvidia driver version: '{nvidia_driver_version}'. Upgrade it to '{supported_nvidia_driver_version}', or above."
    )
    gpu_driver_version_check_failure = "Nvidia driver version could not be checked: \n{error}"
    gpu_requirements_check_start = "Checking if supported GPU card is present..."
    gpu_requirements_check_error = (
        "GPU card not detected. Ensure that at least one GPU card is installed on this machine."
    )
    gpu_requirements_check_memory = "The following detected GPU cards have less than 16 GB of memory: {gpus}."
    resources_check_cpu = "Checking available CPU cores..."
    resources_check_mem = "Checking available memory..."
    resources_check_disk = "Checking disk space..."
    check_error = "Cannot get the number of resources."
    wrong_cpu_amount = "CPU logical cores available: {cpu}. Min: {minimal} cores."
    wrong_mem_amount = "Memory available: {mem} GB. Min: {minimal} GB."
    wrong_disk_amount = "Available disk space: {disk} GB. Min: {minimal} GB."
    wrong_root_amount = "Available root disk space: {disk} GB. Min: {minimal} GB."
    intel_gpu_driver_displayed = 'Driver: "i915"'
    intel_gpu_no_devices = "No device discovered"
    intel_gpu_max_card = "Data Center GPU Max 1100"
    intel_gpu_arc_device_name = "Device Name"
