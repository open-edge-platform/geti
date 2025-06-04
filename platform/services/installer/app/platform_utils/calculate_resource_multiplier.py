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

from collections import namedtuple

ResourceThreshold = namedtuple(  # noqa: PYI024
    "ResourceThreshold", ["min_cpu", "max_cpu", "min_memory", "max_memory", "resource_multiplier"]
)


resource_multiplier_thresholds = [
    ResourceThreshold(min_cpu="0", max_cpu="23", min_memory="0Gi", max_memory="47Gi", resource_multiplier=0.7),
    ResourceThreshold(min_cpu="23", max_cpu="inf", min_memory="47Gi", max_memory="inf", resource_multiplier=1.0),
]


def k8s_cpu_to_millicpus(k8s_cpu: str) -> int:
    """convert cpu return from k8s to millicpus"""
    cpu_suffixes = {
        "m": 1000 ** (-1),
    }

    for cpu_suffix, multiplier in cpu_suffixes.items():
        if isinstance(k8s_cpu, str) and cpu_suffix in k8s_cpu:
            return int(int(k8s_cpu.strip(cpu_suffix)) * multiplier / cpu_suffixes["m"])
    # base unit does not have any suffix
    return int(float(k8s_cpu) / cpu_suffixes["m"])


def k8s_memory_to_kibibytes(k8s_memory: str) -> int:
    """convert memory return from k8s to kibibytes"""
    memory_suffixes = {
        "Pi": 1024**5,
        "Ti": 1024**4,
        "Gi": 1024**3,
        "Mi": 1024**2,
        "Ki": 1024,
        "P": 1000**5,
        "T": 1000**4,
        "G": 1000**3,
        "M": 1000**2,
        "K": 1000,
        "k": 1000,
    }

    for memory_suffix, multiplier in memory_suffixes.items():
        if memory_suffix in k8s_memory:
            # compute bytes and divide by 1024 to return kibybytes
            return int(float(k8s_memory.strip(memory_suffix)) * multiplier // 1024)
    raise ValueError(f"Invalid k8s memory value: {k8s_memory}")


def calculate_resource_multiplier(master_node_allocatable_resources: dict) -> float:
    """
    Calculate multiplier based on available resourced in node.
    """
    allocatable_cpu = k8s_cpu_to_millicpus(master_node_allocatable_resources["cpu"])
    allocatable_memory = k8s_memory_to_kibibytes(master_node_allocatable_resources["memory"])
    for threshold in resource_multiplier_thresholds:
        min_cpu = k8s_cpu_to_millicpus(threshold.min_cpu)
        max_cpu = k8s_cpu_to_millicpus(threshold.max_cpu) if threshold.max_cpu != "inf" else float("inf")
        min_memory = k8s_memory_to_kibibytes(threshold.min_memory)
        max_memory = k8s_memory_to_kibibytes(threshold.max_memory) if threshold.max_memory != "inf" else float("inf")
        if threshold.resource_multiplier < 1:
            if min_cpu < allocatable_cpu <= max_cpu or min_memory < allocatable_memory <= max_memory:
                return threshold.resource_multiplier
        elif min_cpu < allocatable_cpu <= max_cpu and min_memory < allocatable_memory <= max_memory:
            return threshold.resource_multiplier

    return 1.0
