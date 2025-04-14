# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
