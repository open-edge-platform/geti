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
A module responsible for K3S uninstallation.
"""

import logging
import os
import shutil
import subprocess

import rich_click as click
from kubernetes import client
from urllib3.exceptions import HTTPError, MaxRetryError

from cli_utils.platform_logs import subprocess_run
from constants.paths import K3S_KUBECONFIG_PATH, K3S_UNINSTALL_LOG_FILE_PATH, K3S_UNINSTALL_SCRIPT_PATH
from constants.platform import DATA_DIRS_REMOVAL_REQUIRED, DATA_STORAGE_VOLUME_NAME
from platform_utils.kube_config_handler import KubernetesConfigHandler
from texts.uninstall_command import UninstallCmdTexts

logger = logging.getLogger(__name__)


class K3SUninstallationError(Exception):
    """
    Raised when K3S uninstallation script fails.
    """


def _get_data_folder_location() -> str:
    """
    Get platform data_folder location.
    """
    KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)
    with client.ApiClient() as kube_client:
        api = client.CoreV1Api(kube_client)
        persistent_volume = api.read_persistent_volume(name=DATA_STORAGE_VOLUME_NAME)

    return persistent_volume.spec.host_path.path


def _remove_platform_data(delete_data: bool, data_folder: str):
    """
    Remove platform's data.
    """
    data_to_be_removed = os.listdir(data_folder) if delete_data else DATA_DIRS_REMOVAL_REQUIRED

    logger.info(f"Removing platform's data under: '{data_folder}'")
    if not delete_data:
        logger.info(f"Removing only removal-required platform's data: '{DATA_DIRS_REMOVAL_REQUIRED}'")

    for data in data_to_be_removed:
        path = f"{data_folder}/{data}"
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            logger.warning(f"Nor file, nor directory found: '{path}' — skipping")
        logger.debug(f"Removed: '{path}'")
    logger.info("Platform's data removed")


def _run_k3s_uninstaller(logs_file_path: str, script_path: str = K3S_UNINSTALL_SCRIPT_PATH):
    """
    Uninstall K3S by running the default uninstallation script and writing execution logs to 'logs_dir'.
    """

    with open(logs_file_path, "w") as log_file:
        subprocess_run(script_path, log_file)


def uninstall_k3s(delete_data: bool, data_folder: str | None = None, logs_file_path: str = K3S_UNINSTALL_LOG_FILE_PATH):  # noqa: ANN201
    """
    Uninstall K3S from the current system. Remove platform's data if requested.
    Write uninstallation logs to 'logs_dir'.
    """
    try:
        if data_folder is None:
            data_folder = _get_data_folder_location()
    except client.exceptions.ApiException as err:
        click.secho(UninstallCmdTexts.data_folder_get_failed, fg="red")
        logger.error(UninstallCmdTexts.data_folder_get_failed)
        logger.error(err)
    except (MaxRetryError, HTTPError) as err:
        click.secho(UninstallCmdTexts.corrupted_deployment_failed, fg="red")
        logger.error(UninstallCmdTexts.corrupted_deployment_failed)
        logger.error(err)

    try:
        _run_k3s_uninstaller(logs_file_path=logs_file_path)
        if not data_folder:
            raise ValueError
        _remove_platform_data(delete_data=delete_data, data_folder=data_folder)
    except (subprocess.CalledProcessError, FileNotFoundError) as ex:
        raise K3SUninstallationError from ex
    except Exception as err:
        click.secho(UninstallCmdTexts.data_folder_removal_failed, fg="red")
        logger.error(UninstallCmdTexts.data_folder_removal_failed)
        logger.error(err)
