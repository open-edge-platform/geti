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
from unittest.mock import patch

from geti_k8s_tools.calculate_cluster_resources import ClusterCapacity

from policies.resource_manager import ResourceManager


def reset_singletons() -> None:
    ResourceManager._instance = None


@patch("policies.resource_manager.get_resource_capacity_per_node")
def test_refresh_available_resources(mock_get_resource_capacity_per_node, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    cluster_resources = ClusterCapacity(cpu_capacity=[1], memory_capacity=[1], gpu_capacity=[5])
    mock_get_resource_capacity_per_node.return_value = cluster_resources

    assert ResourceManager().gpu_capacity is None

    # Act
    ResourceManager().refresh_available_resources()

    # Assert
    assert ResourceManager().gpu_capacity == [5]


@patch("policies.resource_manager.get_resource_capacity_per_node")
def test_refresh_available_resources_no_gpus(mock_get_resource_capacity_per_node, request) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    cluster_resources = ClusterCapacity(cpu_capacity=[1], memory_capacity=[1], gpu_capacity=[0])
    mock_get_resource_capacity_per_node.return_value = cluster_resources

    assert ResourceManager().gpu_capacity is None

    # Act
    ResourceManager().refresh_available_resources()

    # Assert
    assert ResourceManager().gpu_capacity == [1]
