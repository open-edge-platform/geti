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
import logging
import os
import shutil
import subprocess
import tarfile

import requests
import yaml
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from checks.resources import GPU_PROVIDER_NVIDIA
from cli_utils.platform_logs import subprocess_run
from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.os import SupportedOS
from constants.paths import (
    INSTALL_LOG_FILE_PATH,
    OFFLINE_TOOLS_DIR,
    REDHAT_NVIDIA_PACKAGES_PATH,
    REDHAT_PACKAGES_PATH,
    SYSTEM_PACKAGES_PATH,
    UBUNTU_NVIDIA_PACKAGES_PATH,
    UBUNTU_PACKAGES_PATH,
)
from platform_stages.steps.errors import DownloadSystemPackagesError, InstallSystemPackagesError

logger = logging.getLogger(__name__)

RETRY_STOP_AFTER_ATTEMPT = 3
RETRY_WAIT_EXPONENTIAL = 2


def _parse_system_packages(os_name: str) -> dict:
    with open(SYSTEM_PACKAGES_PATH) as file:
        data = yaml.safe_load(file)

    system_packages: dict[str, dict] = {}

    # Add the shared key to the system_packages dictionary
    if "shared" in data:
        shared_data = data["shared"]
        system_packages["shared"] = {"packages": []}

        packages = shared_data.get("packages", [])
        for package in packages:
            system_packages["shared"]["packages"].append(
                {
                    "name": package["name"],
                    "destination": package["destination"],
                    "urls": package["urls"],
                }
            )

    # Add the OS-specific key (e.g., ubuntu, redhat, etc.)
    if os_name in data:
        os_data = data[os_name]
        system_packages[os_name] = {"packages": []}

        packages = os_data.get("packages", [])
        for package in packages:
            system_packages[os_name]["packages"].append(
                {
                    "name": package["name"],
                    "destination": package["destination"],
                    "urls": package["urls"],
                }
            )

    return system_packages


@retry(
    retry=retry_if_exception_type(DownloadSystemPackagesError),
    stop=stop_after_attempt(RETRY_STOP_AFTER_ATTEMPT),
    wait=wait_exponential(RETRY_WAIT_EXPONENTIAL),
    reraise=True,
)
def _download_file(url: str, file_name: str):
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logger.info(f"Successfully downloaded {file_name}")
    except requests.exceptions.RequestException as ex:
        logger.error(f"Failed to download {url} after multiple attempts: {ex}")
        raise DownloadSystemPackagesError from ex


def _download_packages(system_packages: dict) -> None:
    for os_key, os_info in system_packages.items():
        for package in os_info["packages"]:
            dest_dir = package["destination"]
            os.makedirs(dest_dir, exist_ok=True)
            for url in package["urls"]:
                file_name = os.path.join(dest_dir, os.path.basename(url))
                logger.info(f"Downloading {url} to {file_name}...")
                _download_file(url, file_name)

                # Extract helm tar.gz archive
                if package["name"] == "helm" and file_name.endswith(".tar.gz"):
                    with tarfile.open(file_name, "r:gz") as tar:
                        member = next((m for m in tar.getmembers() if "linux-amd64/helm" in m.name), None)
                        if member:
                            member.name = os.path.basename(member.name)
                            tar.extract(member, path=OFFLINE_TOOLS_DIR)
                            logger.info(f"Extracted {member.name} to {OFFLINE_TOOLS_DIR}/")
                    shutil.rmtree(file_name, ignore_errors=True)
                    logger.info(f"Removed archive {file_name}")


def _install_packages_from_path_ubuntu(packages_path: str) -> None:
    env = os.environ.copy()
    env.update({"LD_LIBRARY_PATH": "/usr/lib:/usr/local/lib"})

    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        try:
            subprocess_run(
                [
                    "bash",
                    "-c",
                    f"dpkg -i \
                    {os.path.abspath(packages_path)}/*.deb",
                ],
                log_file,
                env=env,
            )
        except subprocess.CalledProcessError as ex:
            raise InstallSystemPackagesError from ex


def _install_packages_from_path_redhat(packages_path: str) -> None:
    with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        try:
            subprocess_run(
                [
                    "bash",
                    "-c",
                    f"dnf install --assumeyes {os.path.abspath(packages_path)}/*.rpm",
                ],
                log_file,
            )
        except subprocess.CalledProcessError as ex:
            raise InstallSystemPackagesError from ex


def install_system_packages(config: InstallationConfig | UpgradeConfig) -> None:
    """
    Install system packages for installation purposes
    """
    logger.info("Downloading system packages...")
    if config.lightweight_installer.value:
        os_name_converted = config.local_os.value.replace(" ", "").lower()
        system_packages = _parse_system_packages(os_name_converted)
        try:
            _download_packages(system_packages)
        except DownloadSystemPackagesError as ex:
            # remove 'tools' dir on failure,
            # to be able to re-run without any side effects
            shutil.rmtree(OFFLINE_TOOLS_DIR)
            raise DownloadSystemPackagesError from ex
        logger.info("System packages downloaded.")
    else:
        logger.info("System packages already present, skipping...")

    logger.info("Installing system packages...")
    if config.local_os.value == SupportedOS.RHEL.value:
        _install_packages_from_path_redhat(packages_path=REDHAT_PACKAGES_PATH)
        if config.gpu_support.value and config.gpu_provider.value == GPU_PROVIDER_NVIDIA:
            _install_packages_from_path_redhat(packages_path=REDHAT_NVIDIA_PACKAGES_PATH)
    else:
        _install_packages_from_path_ubuntu(packages_path=UBUNTU_PACKAGES_PATH)
        if config.gpu_support.value and config.gpu_provider.value == GPU_PROVIDER_NVIDIA:
            _install_packages_from_path_ubuntu(packages_path=UBUNTU_NVIDIA_PACKAGES_PATH)
    logger.info("System packages installed.")
