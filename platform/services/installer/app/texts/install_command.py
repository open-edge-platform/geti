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
Strings that are shown to the user by installation command.
"""


class InstallCmdTexts:
    """
    Contains strings shown to the user by installation command.
    """

    start_message = "Running platform installer..."
    k8s_prompt = "Do you want to install the platform on an existing Kubernetes?"
    kube_config_prompt = "Path to kubeconfig file (example: /home/my-user/admin.conf)"
    username_help = "Login name (e.g. admin@my-company.com) of the user to be created during the installation"
    password_help = "Password (8 - 200 characters, at least one capital letter, lower letter, digit or symbol)"  # noqa: S105
    checks_error_message = "Pre-installation checks failed, aborting installation."
    execution_start_message = "Executing installation..."
    data_folder_location = "Path to the data storage: "
    selected_username = "Initial user: "
    selected_password = "Password for initial user: "  # noqa: S105
    custom_certificate_prompt = "Do you want to configure your custom SSL certificate?"
    tls_cert_file_help = "Absolute path to the certificate file"
    tls_key_file_help = "Absolute path to the key file"
    k3s_installing = "Installing k3s. Detailed logs can be found in: platform_logs/k3s_install.log."
    k3s_installation_succeeded = "k3s installed successfully. Path to admin kubeconfig: /etc/rancher/k3s/k3s.yaml"
    k3s_installation_failed = "k3s installation failed. Look for errors in the log."
    sys_pkgs_installing = "Installing system packages. Detailed logs can be found in: platform_logs/install.log."
    sys_pkgs_installation_succeeded = "system packages installed successfully."
    sys_pkgs_installation_failed = "system packages installation failed. Look for errors in the log."
    k3s_installation_in_progress = "k3s installation in progress, keyboard interrupt is disabled."
    logs_location_message = "Detailed logs can be found in: platform_logs/install.log"
    installation_start = "Installing platform"
    installation_succeeded = (
        "Platform installed successfully. To access the platform, navigate to https://{platform_address}"
    )
    installation_failed = "Platform installation failed. Look for errors in the log."
    installation_aborted = "Installation aborted. Reverting to the original state..."
    installation_aborted_succeeded = "Successfully reverted to the original state."

    smtp_config_prompt = "Do you want to configure mail server?"
    smtp_address_prompt = "SMTP address (example: smtp.your_server.com)"
    smtp_port_prompt = "SMTP port (default: 587)"
    smtp_username_prompt = "SMTP user name"
    smtp_password_prompt = "SMTP password"  # noqa: S105
    smtp_sender_email_prompt = "Sender's email address: (example: admin@your_server.com)"
    smtp_sender_name_prompt = "Sender's name: (example: Platform Admin)"
    smtp_checking_connection = "Checking connection to SMTP server {address}:{port}... "
    smtp_connection_failed = "Unable to connect to the SMTP server ({address}:{port})"

    grafana_config_prompt = (
        "Do you want to install the Grafana stack (not recommended on setups meeting only the minimum HW requirements)?"
    )
    grafana_no_internet_confirmation_prompt = (
        "Internet access is unavailable. Would you like to proceed with the installation without the Grafana stack?"
    )
    grafana_no_internet_error = (
        "The Grafana stack is currently enabled, but no internet connection is detected. "
        "Please either disable the Grafana stack or connect your machine to the internet."
    )

    loading_config_file_message = "Reading and validating provided configuration file..."
    config_file_validation_failed = "Failed to validate the configuration file: \n - {err_msg}"
    config_file_parsing_failed = "Failed to parse provided configuration file: {error}"


class InstallCmdConfirmationTexts:
    """
    Texts displayed on final confirmation prompt, before executing installation.
    """

    confirm_k3s_message = "k3s single node cluster will be installed on the local machine."
    confirm_cluster_message = "Platform will be installed on Kubernetes cluster indicated in: {kubeconfig}"
    confirm_username_message = "Admin user login name: {username}"
    confirm_data_message = "Path to the data storage: {path}"
    accept_config_prompt = "Is the provided data correct and you want to proceed with the installation?"
    cert_file_message = "Path to the certificate file: {path}"
    key_file_message = "Path to the key file: {path}"
    no_custom_certificate_message = "Custom SSL certificate will not be configured."
    no_custom_domain_message = "Custom domain name will not be configured."
    fqdn_message = "Domain name for the cluster: {name}.{domain}"
    gpu_requirements_warning = (
        "The following unsupported GPU cards have been detected: {gpus}.\n"
        "If you want to install on supported GPU cards only, remove unsupported cards from your machine.\n"
        "Do you want to configure the platform to use all the GPU cards? "
        "If you choose No, the installation will be aborted."
    )

    smtp_config_confirmation_start = "Mail server configuration:"
    smtp_address = "SMTP address: {address}"
    smtp_port = "SMTP port: {port}"
    smtp_username = "SMTP user name: {username}"
    smtp_sender_address = "Sender's email address: {sender_address}"
    smtp_sender_name = "Sender's name: {sender_name}"
    smtp_config_missing = "Mail server will not be configured."

    confirm_grafana_enabled_message = "The Grafana stack will be configured."
    confirm_grafana_disabled_message = "The Grafana stack will not be configured."
