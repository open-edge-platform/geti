# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
A module containing functions checking Internet connectivity of curl utility.
"""

import logging
import subprocess

from checks.errors import CurlInternetCheckError, SnapCheckError
from texts.checks import ToolsChecksTexts

logger = logging.getLogger(__name__)


def _is_snap_installed():
    """
    Check if snap is installed.
    """
    logger.debug("Checking if snap is installed")
    try:
        subprocess.check_output(["snap", "--version"])  # noqa: S603, S607
        logger.debug("snap is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("snap is not installed.")
        return False


def _check_curl_installed_via_snap():
    logger.debug("Checking if curl is installed by snap.")
    command = "snap list | cut -d ' ' -f 1"
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)  # noqa: S602
        if "curl" in output.decode("utf-8"):
            logger.debug("curl is installed by snap.")
            raise SnapCheckError(ToolsChecksTexts.curl_installed_by_snap)
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        logger.error("Error executing command: %s", error)


def _is_curl_installed():
    """
    Check if curl is installed.
    """
    logger.debug("Checking curl is installed")
    try:
        subprocess.check_output(["curl", "--version"])  # noqa: S603, S607
        logger.debug("curl is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("curl is not installed.")
        return False


def _check_if_curl_has_internet_access():
    """
    Check if curl has internet access.
    """
    try:
        logger.info("Checking if curl has internet access.")
        logger.debug("Sending request to http://example.com...")
        subprocess.check_output(  # noqa: S603
            ["curl", "--head", "--silent", "http://example.com", "--connect-timeout", "5"]  # noqa: S607
        )
        logger.debug("curl has access to Internet.")
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        raise CurlInternetCheckError(ToolsChecksTexts.curl_check_inet_connection_error) from error


def check_tools_configuration():  # noqa: ANN201
    """
    Check all required tools configuration
    Usage: install, upgrade
    """
    if _is_curl_installed() and _is_snap_installed():
        _check_curl_installed_via_snap()
