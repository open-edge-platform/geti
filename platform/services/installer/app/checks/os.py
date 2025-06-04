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
A module containing check functions that are interacting with OS.
"""

import logging
import os
import subprocess
from subprocess import CalledProcessError, TimeoutExpired

from checks.errors import CheckSkipped, LocalOSCheckWarning
from configuration_models.install_config import InstallationConfig
from constants.os import RequiredOS, SupportedOS
from texts.checks import LocalOSChecksTexts

logger = logging.getLogger(__name__)


def check_os_version(config: InstallationConfig) -> None:
    """
    Check that OS version matches expected.
    """
    if os.environ.get("PLATFORM_CHECK_OS") == "false":
        logger.info("PLATFORM_CHECK_OS is set to false, skipping OS check.")
        raise CheckSkipped

    local_os = _get_local_os()
    pretty_required_os_list = ", ".join([item.value for item in RequiredOS])
    logger.debug(f"Local OS: {local_os}, required OS: {pretty_required_os_list}.")
    if any(
        item.value in local_os
        for item in (RequiredOS.UBUNTU_20, RequiredOS.UBUNTU_22, RequiredOS.UBUNTU_24, RequiredOS.UBUNTU_25_04)
    ):
        # default value already contain SupportedOS.UBUNTU.value
        pass
    elif RequiredOS.RHEL_9.value in local_os:
        config.local_os.value = SupportedOS.RHEL.value
    else:
        raise LocalOSCheckWarning(
            LocalOSChecksTexts.os_check_warning.format(local_os=local_os, supported_oses=pretty_required_os_list)
        )


def _get_local_os() -> str:
    """
    Attempt to get local OS description.
    """
    try:
        logger.debug("Checking OS version with `grep ^PRETTY /etc/os-release`")
        return (
            subprocess.check_output(["grep", "^PRETTY", "/etc/os-release"], timeout=5)  # noqa: S603, S607
            .decode("utf-8")
            .strip()
            .replace("PRETTY_NAME=", "")
            .replace('"', "")
        )
    except (CalledProcessError, TimeoutExpired, FileNotFoundError):
        return LocalOSChecksTexts.unknown_os_name
