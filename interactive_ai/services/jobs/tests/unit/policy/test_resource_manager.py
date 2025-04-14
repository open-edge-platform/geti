# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
