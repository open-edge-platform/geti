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

"""
A module containing check functions that are interacting with the Internet.
"""

import logging

import requests

from checks.errors import CheckSkipped
from configuration_models.install_config import InstallationConfig
from texts.checks import InternetConnectionChecksTexts

logger = logging.getLogger(__name__)


def check_internet_connection(config: InstallationConfig) -> None:
    """
    Check that internet is accessible.
    Usage: install, upgrade, uninstall
    """

    try:
        logger.info("Checking Internet access.")
        logger.debug("Sending request to http://example.com...")
        requests.head("http://example.com", allow_redirects=True, timeout=10).raise_for_status()
        logger.debug("Internet is accessible.")
    except requests.RequestException as error:
        logger.debug("Internet is not accessible.")
        config.internet_access.value = False
        raise CheckSkipped(InternetConnectionChecksTexts.internet_connection_check_error) from error
