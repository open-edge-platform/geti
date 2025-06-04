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
A module containing functions to check ports availability.
"""

import logging
import socket

from checks.errors import PortsAvailabilityCheckError
from texts.checks import PortsAvailabilityCheckTexts

HOST = "127.0.0.1"
HTTP_PORT = 80
UI_PORT = 443
DOCKER_REGISTRY_PORT = 30000

logger = logging.getLogger(__name__)


def check_required_ports_availability():  # noqa: ANN201
    """
    Check whether required ports are available.
    Usage: install
    """
    ports = [HTTP_PORT, UI_PORT, DOCKER_REGISTRY_PORT]
    logger.info(f"Checking whether required ports {ports} are available.")
    occupied_ports = ", ".join([str(p) for p in ports if not is_port_available(p)])
    if len(occupied_ports) > 0:
        raise PortsAvailabilityCheckError(
            PortsAvailabilityCheckTexts.ports_availability_check_error.format(occupied_ports=occupied_ports)
        )


def is_port_available(port: int) -> bool:
    """
    Check whether provided port is not being used.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5.0)
            result = sock.connect_ex((HOST, port))
            if result != 0:
                logger.debug(f"Port {port} is available.")
            return bool(result)
    except OSError as exc:
        raise PortsAvailabilityCheckError(PortsAvailabilityCheckTexts.check_error) from exc
