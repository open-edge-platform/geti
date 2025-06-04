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

"""Platform state related functions"""

import logging
import os
import shutil
import tarfile
import time
from datetime import datetime

from cli_utils.platform_logs import subprocess_run
from constants.paths import (
    CLUSTER_INFO_DIR,
    INSTALL_LOG_FILE_PATH,
    K3S_BACKUP_RESTORE_PATH,
    K3S_KILLALL_SCRIPT_PATH,
    K3S_VAR_LIB_RANCHER_SERVER,
)

logger = logging.getLogger(__name__)


class InstallationHandlerState:
    def __init__(self):
        self.can_be_aborted = False
        self.already_triggered = False

    def set_abortable(self, can_be_aborted: bool) -> None:
        self.can_be_aborted = can_be_aborted

    def trigger(self) -> bool:
        if self.already_triggered:
            return False
        self.already_triggered = True
        return True

    def clear_trigger(self) -> None:
        self.already_triggered = False

    def reset(self) -> None:
        self.can_be_aborted = True
        self.already_triggered = False


def restart_k3s(sleep_sec: int = 30) -> None:
    """
    Restart k3s
    """
    logger.info("Restarting k3s...")
    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        subprocess_run(["systemctl", "restart", "k3s"], log_file)
    # give k3s time
    time.sleep(sleep_sec)
    logger.info("k3s restarted.")


def save_k3s_state() -> None:
    """
    Save k3s state before upgrade
    """
    logger.info("Saving k3s state...")
    os.makedirs(K3S_BACKUP_RESTORE_PATH, exist_ok=True)
    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        subprocess_run(["systemctl", "stop", "k3s"], log_file)
        subprocess_run(["rm", "-rf", f"{K3S_BACKUP_RESTORE_PATH}/db"], log_file)
        subprocess_run(["rm", "-rf", f"{K3S_BACKUP_RESTORE_PATH}/token"], log_file)
        subprocess_run(["cp", "-a", f"{K3S_VAR_LIB_RANCHER_SERVER}/db", K3S_BACKUP_RESTORE_PATH], log_file)
        subprocess_run(["cp", "-a", f"{K3S_VAR_LIB_RANCHER_SERVER}/token", K3S_BACKUP_RESTORE_PATH], log_file)
    restart_k3s()
    logger.info("k3s state saved.")


def kill_all_k3s() -> None:
    """
    Kill k3s processes
    """
    logger.info("Killing k3s processes...")
    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        subprocess_run(["sh", K3S_KILLALL_SCRIPT_PATH], log_file)
    logger.info("k3s processes killed.")


def restore_k3s_state() -> None:
    """
    Restore k3s state before upgrade
    """
    logger.info("Restoring k3s state...")
    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        subprocess_run(["rm", "-rf", f"{K3S_VAR_LIB_RANCHER_SERVER}/db"], log_file)
        subprocess_run(["mv", f"{K3S_BACKUP_RESTORE_PATH}/db", f"{K3S_VAR_LIB_RANCHER_SERVER}/"], log_file)
        subprocess_run(["mv", f"{K3S_BACKUP_RESTORE_PATH}/token", f"{K3S_VAR_LIB_RANCHER_SERVER}/"], log_file)
    restart_k3s(sleep_sec=60)
    logger.info("k3s state restored.")


def cluster_info_dump(kubeconfig: str, destination: str = CLUSTER_INFO_DIR) -> None:
    """
    Dump cluster info
    """
    output_directory = f"{destination}/{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    logger.info(f"Dumping cluster info into: '{output_directory}'")
    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        subprocess_run(
            [
                "kubectl",
                "cluster-info",
                "dump",
                f"--output-directory={output_directory}",
                "--all-namespaces",
                f"--kubeconfig={kubeconfig}",
            ],
            log_file,
        )
    with tarfile.open(f"{output_directory}.tar.gz", "w:gz") as tar:
        tar.add(output_directory, arcname=os.path.basename(output_directory))
    shutil.rmtree(output_directory)
    logger.info("Cluster info dumped.")
