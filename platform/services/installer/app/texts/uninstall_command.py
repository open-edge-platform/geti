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
Strings that are shown to the user by uninstallation command.
"""


class UninstallCmdTexts:
    """
    Contains strings shown to the user by uninstallation command.
    """

    start_message = "Running platform uninstaller..."
    delete_data_prompt = "Do you want to delete all the platform data, including models, datasets, and users data?"
    loading_config_file_message = "Reading and validating provided configuration file..."
    config_file_validation_failed = "Failed to validate the configuration file: \n - {err_msg}"
    config_file_parsing_failed = "Failed to parse provided configuration file: {error}"
    execution_start_message = "Executing uninstallation..."
    k3s_uninstallation_start = (
        "Uninstalling k3s. Detailed logs can be found in: {platform_logs_path}/k3s_uninstall.log and "
        "{platform_logs_path}/install.log."
    )
    k3s_uninstallation_succeeded = "k3s uninstalled successfully."
    k3s_uninstallation_failed = "k3s uninstallation failed. Look for errors in the log."
    data_folder_removal_failed = "Failed to remove the contents of the data folder."
    data_folder_get_failed = "Failed to get data folder location."
    checks_error_message = "Pre-uninstall checks failed, aborting uninstallation."
    corrupted_deployment_failed = (
        "Your deployment seems to be corrupted. Uninstall kubernetes and delete the data folder manually."
    )


class UninstallCmdConfirmationTexts:
    """
    Texts displayed on final confirmation prompt, before executing uninstallation.
    """

    uninstall_k3s_prompt = "Do you want to uninstall k3s? You will irreversibly lose your k3s deployment."
    uninstall_k3s_data_prompt = (
        "Do you want to uninstall k3s? You will irreversibly lose your k3s deployment, all "
        "the platform data, including models, datasets, and users data."
    )
