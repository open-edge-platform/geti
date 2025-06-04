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
A module containing local resources check functions.
"""

import logging
import os
import subprocess
from subprocess import CalledProcessError, TimeoutExpired

import click_spinner
import rich_click as click
from geti_k8s_tools.calculate_cluster_resources import k8s_memory_to_kibibytes
from GPUtil import getGPUs
from packaging import version
from psutil import cpu_count, disk_partitions, disk_usage, virtual_memory

from checks.errors import (
    CheckIgnored,
    CheckSkipped,
    K8SCheckError,
    ResourcesCheckError,
    ResourcesCheckWarning,
    UnsupportedGpuWarning,
)
from cli_utils.checks import CROSS_MARK
from cli_utils.prompts import prompt_for_configuration_value
from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.paths import INSTALL_LOG_FILE_PATH
from constants.platform import (
    GPU_PROVIDER_INTEL_ARC,
    GPU_PROVIDER_INTEL_ARC_A,
    GPU_PROVIDER_INTEL_MAX,
    GPU_PROVIDER_NVIDIA,
)
from k3s.detect_k3s import is_kubernetes_running_on_k3s
from platform_configuration.platform import get_data_folder_path
from platform_utils.kube_config_handler import KubernetesConfigHandler
from texts.checks import K8SChecksTexts, ResourcesChecksTexts
from texts.upgrade_command import UpgradeCmdTexts
from validators.path import is_path_valid

logger = logging.getLogger(__name__)

PLATFORM_CPU_CORES_MIN = int(os.getenv("PLATFORM_CPU_CORES_MIN", "16"))
# Expressed in GB (1000 ** 3)
PLATFORM_MEMORY_MIN = (k8s_memory_to_kibibytes(os.getenv("PLATFORM_MEMORY_MIN", "64GB")) * 1024) // (1000**3)
# Expressed in GB (1000 ** 3)
PLATFORM_DISK_MIN = (k8s_memory_to_kibibytes(os.getenv("PLATFORM_DISK_MIN", "500GB")) * 1024) // (1000**3)
# Expressed in GB (1000 ** 3)
PLATFORM_DISK_THRESHOLD = min(PLATFORM_DISK_MIN, (k8s_memory_to_kibibytes("100GB") * 1024) // (1000**3))

# Expressed in GB (1000 ** 3)
ROOT_DISK_MIN = (k8s_memory_to_kibibytes("40GB") * 1024) // (1000**3)
# We support GPU cards >= 16 GB of memory, here a little bit less not to reject cards that have slightly less
# then 16385 MiB, e.g. Tesla T4 reports 15109MiB
SUPPORTED_GPUS_MEMORY = 15100.0
# https://docs.nvidia.com/deeplearning/cudnn/latest/reference/support-matrix.html#gpu-cuda-toolkit-and-cuda-driver-requirements
SUPPORTED_NVIDIA_DRIVER_VERSION = "525.60.13"


def _bytes_to_gigabytes(bytes_: int) -> float:
    return round(bytes_ / (1000**3), 2)


def _subprocess_run(command: list[str]):
    with open(INSTALL_LOG_FILE_PATH, mode="a+") as log_file:
        process = subprocess.run(  # noqa: S603
            command,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        for line in process.stdout:
            log_file.write(line)
            log_file.flush()

        return process


def check_local_cpu():  # noqa: ANN201
    """
    Check number of available logical CPU cores.
    """
    logger.info("Checking number of CPU cores.")
    cpu = cpu_count(logical=True)
    logger.debug(f"PLATFORM_CPU_CORES_MIN: {PLATFORM_CPU_CORES_MIN}, available logical CPU cores: {cpu}.")

    if cpu < PLATFORM_CPU_CORES_MIN:
        raise ResourcesCheckError(ResourcesChecksTexts.wrong_cpu_amount.format(cpu=cpu, minimal=PLATFORM_CPU_CORES_MIN))


def _check_intel_driver() -> bool:
    """
    Returns true if hwinfo returns the devices that have Driver: "i915" displayed
    """
    try:
        logger.debug("Checking the installed display devices with `hwinfo --display`")
        hwinfo_output = subprocess.check_output(["hwinfo", "--display"], timeout=5).decode("utf-8")  # noqa: S603, S607
        logger.debug(hwinfo_output)
        if ResourcesChecksTexts.intel_gpu_driver_displayed in hwinfo_output:
            logger.debug('hwinfo returned at least one device with Driver: "i915" displayed')
            return True
        return False
    except (CalledProcessError, TimeoutExpired, FileNotFoundError) as err:
        logger.debug(f"Checking the installed display devices failed with {err}")
        return False


def check_local_gpu_driver(gpu_support: bool = True):  # noqa: ANN201
    """
    Check whether GPU driver is installed.
    Skip if 'gpu_support' is set to 'False'.
    """
    if not gpu_support:
        logger.info("PLATFORM_GPU_REQUIRED is set to false, skipping check.")
        raise CheckSkipped

    # First, let's check for the Nvidia driver
    driver_path = "/proc/driver/nvidia/version"
    logger.info("Checking Nvidia GPU driver.")
    logger.debug(f"Looking for driver installed under the path {driver_path}...")
    if not os.path.isfile(driver_path) and not _check_intel_driver():  # now let's check for the Intel driver
        raise ResourcesCheckError(ResourcesChecksTexts.gpu_driver_check_error)
    logger.debug("NVIDIA driver is present.")


def check_gpu_driver_version(config: InstallationConfig | UpgradeConfig) -> None:
    """
    Check GPU driver version
    Skip if 'gpu_support' is set to 'False'.
    """

    if not config.gpu_support.value:
        logger.info("PLATFORM_GPU_REQUIRED is set to false, skipping check.")
        raise CheckSkipped

    logger.info("Checking GPU driver version.")
    if config.gpu_provider.value == GPU_PROVIDER_NVIDIA:
        try:
            nvidia_smi_output = subprocess.check_output(  # noqa: S603
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader,nounits"]  # noqa: S607
            )
            nvidia_driver_versions = nvidia_smi_output.decode("utf-8").strip().split("\n")
            for nvidia_driver_version in nvidia_driver_versions:
                if version.parse(nvidia_driver_version) < version.parse(SUPPORTED_NVIDIA_DRIVER_VERSION):
                    raise ResourcesCheckError(
                        ResourcesChecksTexts.gpu_driver_version_check_error.format(
                            nvidia_driver_version=nvidia_driver_version,
                            supported_nvidia_driver_version=SUPPORTED_NVIDIA_DRIVER_VERSION,
                        )
                    )
        except CalledProcessError as ex:
            raise ResourcesCheckError(ResourcesChecksTexts.gpu_driver_version_check_failure.format(error=ex.stderr))
    else:
        raise CheckSkipped
    logger.debug("GPU driver version matched.")


def _get_intel_gpus() -> str:
    """
    MAX cards:
    Attempt to get Intel GPUs with xpu-smi
    It just returns the output if Max 1100 present in it, empty string otherwise
    For now, we do not have to parse it to get the details of particular cards
    ARC cards:
    We rely on the output of clinfo
    """
    # Only valid for MAX cards
    try:
        logger.debug("Getting the list of Intel GPU with `xpu-smi discovery`")
        xpu_output = subprocess.check_output(["xpu-smi", "discovery"], timeout=5).decode("utf-8")  # noqa: S603, S607
        logger.debug(xpu_output)
        if ResourcesChecksTexts.intel_gpu_no_devices in xpu_output:
            logger.debug("No devices")
            return ""
        if ResourcesChecksTexts.intel_gpu_max_card in xpu_output:
            logger.debug("Max 1100 found")
            return xpu_output
    except (CalledProcessError, TimeoutExpired, FileNotFoundError) as err:
        logger.debug(f"Getting the list of Intel GPU failed with {err}")

    # Only valid for ARC cards
    try:
        command = 'clinfo|grep "' + ResourcesChecksTexts.intel_gpu_arc_device_name + '"|grep Intel'
        logger.debug(f"Getting the list of Intel ARC with {command}")
        clinfo_output = subprocess.check_output(  # noqa: S602
            command,
            stderr=subprocess.STDOUT,
            shell=True,
            timeout=5,
        ).decode("utf-8")
        logger.debug(clinfo_output)
        if ResourcesChecksTexts.intel_gpu_arc_device_name in clinfo_output:
            logger.debug("ARC found")
            return clinfo_output
    except (CalledProcessError, TimeoutExpired, FileNotFoundError) as err:
        logger.debug(f"Getting the list of Intel ARC failed with {err}")

    return ""


def check_local_gpu(config: InstallationConfig):  # noqa: ANN201
    """
    Check GPU card requirements.
    Skip if 'gpu_support' is set to 'False'.
    """
    logger.info("Checking GPU card requirements.")
    if not config.gpu_support.value:
        logger.info("PLATFORM_GPU_REQUIRED is set to false, skipping check.")
        raise CheckSkipped

    logger.info("Checking GPU card requirements.")
    try:
        nvidia_gpus = getGPUs()
    except ValueError as err:
        raise ResourcesCheckWarning(ResourcesChecksTexts.gpu_requirements_check_error) from err

    # If Nvidia not found, let's look for Intel GPU
    # We prefer Intel GPU, so ignoring Nvidia if Intel GPU found
    intel_gpus = _get_intel_gpus()
    if not intel_gpus and not nvidia_gpus:
        raise ResourcesCheckWarning(ResourcesChecksTexts.gpu_requirements_check_error)
    if intel_gpus:
        if ResourcesChecksTexts.intel_gpu_max_card in intel_gpus:
            config.gpu_provider.value = GPU_PROVIDER_INTEL_MAX
        elif ResourcesChecksTexts.intel_gpu_arc_a_card in intel_gpus:
            config.gpu_provider.value = GPU_PROVIDER_INTEL_ARC_A
        else:
            config.gpu_provider.value = GPU_PROVIDER_INTEL_ARC
        logger.info(f"GPU provider: {config.gpu_provider.value}")
    elif nvidia_gpus:
        config.gpu_provider.value = GPU_PROVIDER_NVIDIA
        logger.info(f"GPU provider: {config.gpu_provider.value}")
        found_gpus = [f"{local_gpu.name}, mem={str(local_gpu.memoryTotal)}MiB" for local_gpu in nvidia_gpus]
        logger.debug(f"Found GPUs: {', '.join(found_gpus)}")

        unsupported_gpus = [gpu for gpu in nvidia_gpus if gpu.memoryTotal < SUPPORTED_GPUS_MEMORY]
        if unsupported_gpus:
            unsupported_gpus_str = ", ".join([gpu.name for gpu in unsupported_gpus])
            logger.debug(f"Unsupported GPUs: {unsupported_gpus_str}")
            raise UnsupportedGpuWarning(
                ResourcesChecksTexts.gpu_requirements_check_memory.format(gpus=unsupported_gpus_str)
            )


def check_local_mem():  # noqa: ANN201
    """
    Check size of available memory.
    """
    logger.info("Checking available memory size.")
    mem = _bytes_to_gigabytes(virtual_memory().total)
    logger.debug(f"Memory size requirements: {PLATFORM_MEMORY_MIN} GB, memory available: {mem} GB.")
    if mem < PLATFORM_MEMORY_MIN:
        raise ResourcesCheckWarning(ResourcesChecksTexts.wrong_mem_amount.format(mem=mem, minimal=PLATFORM_MEMORY_MIN))


def check_local_disk():  # noqa: ANN201
    """
    Check number of available disk storage.
    """
    try:
        logger.info("Checking size of available disk space.")
        freedisk = 0
        for part in disk_partitions(all=False):
            usage = disk_usage(part.mountpoint)
            disk = _bytes_to_gigabytes(usage.free)
            freedisk = disk if disk > freedisk else freedisk
        logger.debug(f"Disk space requirements: {PLATFORM_DISK_MIN} GB, disk space available: {freedisk} GB.")
        if freedisk < PLATFORM_DISK_THRESHOLD:
            raise ResourcesCheckError(
                ResourcesChecksTexts.wrong_disk_amount.format(disk=freedisk, minimal=PLATFORM_DISK_THRESHOLD)
            )
        if freedisk < PLATFORM_DISK_MIN:
            raise ResourcesCheckWarning(
                ResourcesChecksTexts.wrong_disk_amount_warning.format(disk=freedisk, minimal=PLATFORM_DISK_MIN)
            )

        logger.info("Checking size of available root disk space.")
        root_usage = disk_usage("/")
        free_space = _bytes_to_gigabytes(root_usage.free)
        logger.debug(f"Root filesystem requirements: {ROOT_DISK_MIN} GB, root disk space available: {free_space} GB.")
        if free_space < ROOT_DISK_MIN:
            raise ResourcesCheckError(
                ResourcesChecksTexts.wrong_root_amount.format(disk=free_space, minimal=ROOT_DISK_MIN)
            )
    except OSError as error:
        raise ResourcesCheckWarning(ResourcesChecksTexts.check_error) from error


def _get_available_storage_for_directory(directory: str) -> int:
    process = _subprocess_run(command=["/bin/sh", "-c", f"df -m {directory} | tail -n1"])
    return int(list(filter(lambda x: x, process.stdout.split(" ")))[3])


def _get_used_storage(data_folder_path: str) -> int:
    process = _subprocess_run(
        command=[
            "/bin/sh",
            "-c",
            "du --max-depth=0 -m "
            f"--exclude='{data_folder_path}/binary_data' "
            f"--exclude='{data_folder_path}/seaweedfs' "
            f"{data_folder_path}",
        ]
    )
    return int(next(iter(filter(lambda x: x, process.stdout.split("\t")))))


def check_upgrade_storage_requirements(  # noqa: ANN201
    config: UpgradeConfig, spinner: click_spinner.Spinner | None = None
):
    """
    Check if environment has minimum amount of storage to perform upgrade.
    """
    config.running_on_k3s.value = is_kubernetes_running_on_k3s(config.kube_config.value)

    if not config.running_on_k3s.value:
        logger.warning("Skipping upgrade storage requirements check.")
        raise CheckSkipped

    KubernetesConfigHandler(kube_config=config.kube_config.value)

    interactive_mode = config.interactive_mode

    if spinner is None:
        raise Exception("spinner is required for this check")

    data_folder_path = get_data_folder_path(kubeconfig=config.kube_config.value)

    available_storage = _get_available_storage_for_directory(directory=data_folder_path)
    used_storage = _get_used_storage(data_folder_path=data_folder_path)

    # required storage = space in data folder + 50 GB to keep the installer, and for kubernetes
    required_storage = used_storage + 50000
    if required_storage > available_storage:
        if not config.running_on_k3s.value or (not interactive_mode and config.skip_backup.value is None):
            raise K8SCheckError(
                K8SChecksTexts.storage_requirements_check_error.format(
                    location=data_folder_path, available_storage=available_storage, required_storage=required_storage
                )
            )

        spinner.stop()

        # if there is no space on the 'data_folder_path'
        # do not exit, but ask user if backup should be skipped
        click.secho(f" {CROSS_MARK}", fg="red")
        click.secho(
            K8SChecksTexts.storage_requirements_check_error.format(
                location=data_folder_path, available_storage=available_storage, required_storage=required_storage
            ),
            fg="red",
            nl=True,
        )

        # ask user if backup should be skipped ('skip_backup')
        if interactive_mode:
            prompt_for_configuration_value(config.skip_backup, UpgradeCmdTexts.skip_backup_prompt)
        if config.skip_backup.value:
            raise CheckIgnored

        if interactive_mode:
            config.backup_location.validation_callback = is_path_valid
            prompt_for_configuration_value(config.backup_location, UpgradeCmdTexts.backup_location_prompt)
        backup_location = config.backup_location.value

        spinner.start()
        click.echo(
            K8SChecksTexts.backup_location_storage_requirements_check_start.format(location=backup_location),
            nl=False,
        )

        # check if 'backup_location' meets disk space requirement
        backup_location_available_storage = _get_available_storage_for_directory(directory=backup_location)
        if used_storage > backup_location_available_storage:
            raise K8SCheckError(
                K8SChecksTexts.storage_requirements_check_error.format(
                    location=backup_location,
                    available_storage=backup_location_available_storage,
                    required_storage=required_storage,
                )
            )
    else:
        # ignore 'skip_backup' and 'backup_location' params if provided by user,
        # in case there is enough space under the data_folder to perform the backup
        config.skip_backup.value = False
        config.backup_location.value = None
