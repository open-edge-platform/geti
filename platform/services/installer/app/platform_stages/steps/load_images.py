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
import glob
import logging
import os
import re
import subprocess
from typing import TextIO

from cli_utils.platform_logs import subprocess_run
from configuration_models.install_config import InstallationConfig
from configuration_models.upgrade_config import UpgradeConfig
from constants.paths import INSTALL_LOG_FILE_PATH, OFFLINE_IMAGES_DIR
from constants.platform import INTERNAL_REGISTRY_ADDRESS
from platform_stages.steps.errors import LoadImagesError, PinImageVersionError

logger = logging.getLogger(__name__)


def load_images(config: InstallationConfig | UpgradeConfig) -> None:
    """
    Load images before internal registry is installed.
    """

    if not config.lightweight_installer.value:
        logger.info(f"Loading images from '{OFFLINE_IMAGES_DIR}'")
        with open(INSTALL_LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            list_of_images = glob.glob(os.path.join(OFFLINE_IMAGES_DIR, "*.tar"))
            for file in list_of_images:
                try:
                    subprocess_run(
                        [
                            "k3s",
                            "ctr",
                            "-n=k8s.io",
                            "image",
                            "import",
                            file,
                        ],
                        log_file,
                    )
                except subprocess.CalledProcessError as ex:
                    raise LoadImagesError from ex
            _pin_images(list_of_images, config, log_file)
        logger.info("Images loaded successfully.")


def _extract_version(pattern: str, image: str) -> str:
    match = re.search(pattern, image)
    if not match:
        raise PinImageVersionError(f"Failed to extract version from image: {image}")
    return match.group(1)


def _run_subprocess(command: list[str], error_message: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, capture_output=True, text=True, check=True)  # noqa: S603
    except subprocess.CalledProcessError as e:
        logger.error(f"{error_message}: {e.stderr}")
        raise PinImageVersionError from e


def _pin_images(list_of_images: list[str], config: InstallationConfig | UpgradeConfig, log_file: TextIO) -> None:
    registry_image = next(os.path.basename(image) for image in list_of_images if "registry" in os.path.basename(image))
    registry_version = _extract_version(r"registry_(\d+\.\d+\.\d+\.\d+)\.tar", registry_image)

    if isinstance(config, UpgradeConfig):
        result = _run_subprocess(["ctr", "-n", "k8s.io", "images", "ls", "-q"], "Failed to list images")

        current_registry_images = [image for image in result.stdout.strip().split("\n") if "registry" in image]
        for image in current_registry_images:
            current_version = _extract_version(r"registry:(\d+\.\d+\.\d+\.\d+)", image)
            if current_version != registry_version:
                unpin_image_cmd = [
                    "ctr",
                    "-n",
                    "k8s.io",
                    "images",
                    "label",
                    image,
                    "io.cri-containerd.pinned=",
                ]
                subprocess_run(unpin_image_cmd, log_file)
                logger.info(f"Unpinned registry image {current_version}")
    label_image_cmd = [
        "ctr",
        "-n",
        "k8s.io",
        "images",
        "label",
        f"{INTERNAL_REGISTRY_ADDRESS}/local-third-party/registry:{registry_version}",
        "io.cri-containerd.pinned=pinned",
    ]
    _run_subprocess(label_image_cmd, "Failed to pin registry image")
    logger.info(f"Registry image {registry_version} pinned successfully")
