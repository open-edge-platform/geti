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
import socket

from checks.errors import CheckSkipped, DNSCheckError
from configuration_models.install_config import InstallationConfig
from texts.checks import DNSChecksTexts

logger = logging.getLogger(__name__)


def check_dns_ipv4_handling(config: InstallationConfig) -> None:
    """
    Check that platforms' DNS resolves the IPv4
    Usage: install, upgrade
    """
    if not config.internet_access.value:
        raise CheckSkipped
    try:
        logger.info("Checking IPv4 DNS resolve.")
        logger.debug("Resolving DNS to example.com")
        addr = socket.getaddrinfo("example.com", None, socket.AF_INET)
        if not addr:
            raise DNSCheckError(DNSChecksTexts.dns_ipv4_check_error)
        logger.debug("DNS did resolve to example.com")
    except socket.gaierror as error:
        raise DNSCheckError(DNSChecksTexts.dns_ipv4_check_error) from error
