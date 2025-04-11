# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""
Resource Manager module
"""

import asyncio
import logging

from geti_k8s_tools.calculate_cluster_resources import get_resource_capacity_per_node

from geti_types import Singleton

logger = logging.getLogger(__name__)


class ResourceManager(metaclass=Singleton):
    """
    Resource Manager
    This module obtains information about cluster available resources and provides GPU capacity to clients
    """

    def __init__(self) -> None:
        """
        Initializes resource manager
        """
        self.gpu_capacity: list[int] | None = None

    def refresh_available_resources(self) -> None:
        """
        Fetches information about cluster available resources and gets cluster GPU capacity
        """
        cluster_capacity = asyncio.run(get_resource_capacity_per_node())
        new_gpu_capacity = cluster_capacity.gpu_capacity
        if sum(new_gpu_capacity) == 0:
            logger.warning("No GPUs are found in the cluster, fallback to gpu_capacity = 1")
            new_gpu_capacity = [1]

        if self.gpu_capacity is None:
            logger.info(f"Cluster GPU capacity is {new_gpu_capacity}")
        elif self.gpu_capacity != new_gpu_capacity:
            logger.info(f"Cluster GPU capacity has changed to {new_gpu_capacity}")
        self.gpu_capacity = new_gpu_capacity
