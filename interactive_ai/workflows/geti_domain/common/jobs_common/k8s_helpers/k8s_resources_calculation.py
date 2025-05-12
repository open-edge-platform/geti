# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""Module containing methods used to work with training resources."""

import asyncio
import logging
import os
import typing
from dataclasses import dataclass

from dataclasses_json import dataclass_json
from geti_k8s_tools import calculate_available_resources_per_node, k8s_cpu_to_millicpus, k8s_memory_to_kibibytes
from iai_core.entities.compiled_dataset_shards import CompiledDatasetShards

logger = logging.getLogger(__name__)

__all__ = ["ComputeResources", "EphemeralStorageResources"]


RESOURCES_MULTIPLIER = 0.9

# Resources configuration per environment type
RESOURCES_CONFIGURATION: dict = {
    "VM": {"requests": {"cpu": "1", "memory": "8GB"}, "limits": {"cpu": "100"}},
    "BM": {
        "requests": {"cpu": "2", "memory": "20GB"},
        "limits": {"cpu": "100", "memory": "50GB"},
    },
}


def shrink_value(value: int) -> int:
    """Shrinks value by RESOURCES_MULTIPLIER and rounds it to the integer."""
    return int(value * RESOURCES_MULTIPLIER)


def round_millicpus_and_shrink(millicpus: float) -> int:
    """Rounds millicpus and shrinks it. For more information about shrinking, see shrink_value method."""
    rounded = max((int(millicpus) // 500) * 500, 500)
    return shrink_value(rounded)


def fill_resources_with_values(
    requests_cpu: str | None,
    requests_memory: str | None,
    limits_cpu: str | None = None,
    limits_memory: str | None = None,
    requests_gpu: str | None = None,
    limits_gpu: str | None = None,
    accelerator_name: str | None = None,
) -> dict:
    """
    Fill resources with values

    :param requests_cpu: request cpu number
    :param requests_memory: request memory number
    :param limits_cpu: limits cpu number
    :param limits_memory: limits memory number
    :param requests_gpu: request gpu number
    :param limits_gpu: limits gpu number
    :param accelerator_name: name of gpu
    :return: resources as dict
    """

    resources: dict = {"requests": {}, "limits": {}}

    _requests_cpu = os.environ.get("OVERWRITE_RESOURCES_CPU_REQUESTS", requests_cpu)
    if _requests_cpu:
        resources["requests"]["cpu"] = f"{k8s_cpu_to_millicpus(_requests_cpu)}m"

    _requests_memory = os.environ.get("OVERWRITE_RESOURCES_MEM_REQUESTS", requests_memory)
    if _requests_memory:
        resources["requests"]["memory"] = f"{k8s_memory_to_kibibytes(_requests_memory)}Ki"

    _requests_gpu = os.environ.get("OVERWRITE_RESOURCES_GPU_REQUESTS", requests_gpu)
    if _requests_gpu:
        resources["requests"][accelerator_name] = _requests_gpu

    _limits_cpu = os.environ.get("OVERWRITE_RESOURCES_CPU_LIMITS", limits_cpu)
    if _limits_cpu:
        resources["limits"]["cpu"] = f"{k8s_cpu_to_millicpus(_limits_cpu)}m"

    _limits_memory = os.environ.get("OVERWRITE_RESOURCES_MEM_LIMITS", limits_memory)
    if _limits_memory:
        resources["limits"]["memory"] = f"{k8s_memory_to_kibibytes(_limits_memory)}Ki"

    _limits_gpu = os.environ.get("OVERWRITE_RESOURCES_GPU_LIMITS", limits_gpu)
    if _limits_gpu:
        resources["limits"][accelerator_name] = _limits_gpu

    logger.info(f"Filled resource requests and limits: {resources}")

    return resources


async def calculate_training_resources() -> tuple[dict, str]:
    """
    Calculate CPU or GPU training resources

    :return: training resources as dict and acceleartor_name
    """

    (
        available_cpu,
        available_memory,
        cpu_capacity,
        memory_capacity,
        accelerator_type,
        accelerator_name,
    ) = await calculate_available_resources_per_node()

    if accelerator_type == "cpu":
        # CPU training task calculation

        limits_cpu = round_millicpus_and_shrink(max(available_cpu))
        requests_cpu = k8s_cpu_to_millicpus(RESOURCES_CONFIGURATION["VM"]["requests"]["cpu"])
        limits_cpu = max(limits_cpu, requests_cpu)

        limits_memory = shrink_value(int(max(available_memory)))
        requests_memory = k8s_memory_to_kibibytes(RESOURCES_CONFIGURATION["VM"]["requests"]["memory"])
        limits_memory = max(limits_memory, requests_memory)

        return (
            fill_resources_with_values(
                requests_cpu=RESOURCES_CONFIGURATION["VM"]["requests"]["cpu"],
                requests_memory=RESOURCES_CONFIGURATION["VM"]["requests"]["memory"],
                limits_memory=f"{limits_memory}Ki",
                limits_cpu=f"{limits_cpu}m",
            ),
            accelerator_name,
        )
    if accelerator_type == "gpu":
        gpu_request = RESOURCES_CONFIGURATION["BM"]["requests"][accelerator_name] = "1"
        gpu_limit = RESOURCES_CONFIGURATION["BM"]["limits"][accelerator_name] = "1"
        # GPU training task calculation
        return (
            fill_resources_with_values(
                requests_cpu=RESOURCES_CONFIGURATION["BM"]["requests"]["cpu"],
                requests_memory=RESOURCES_CONFIGURATION["BM"]["requests"]["memory"],
                limits_memory=RESOURCES_CONFIGURATION["BM"]["limits"]["memory"],
                requests_gpu=gpu_request,
                limits_gpu=gpu_limit,
                accelerator_name=accelerator_name,
            ),
            accelerator_name,
        )

    raise ValueError(f"Unknown accelerator type={accelerator_type}.")


@dataclass_json
@dataclass
class EphemeralStorageResources:
    """Data container for ephemeral storage resource request for training/optimize pods."""

    limits: int
    requests: int
    work_dir_size_limit: int

    @classmethod
    def create_from_compiled_dataset_shards(
        cls,
        compiled_dataset_shards: CompiledDatasetShards,
        ephemeral_storage_limits_scale: float = 1.2,
        ephemeral_storage_safety_margin: int = 512 * 1024 * 1024,  # 512 MiB
        work_dir_safety_margin: int = 10 * 1024 * 1024,  # 10 MiB
    ) -> "EphemeralStorageResources":
        """Get ephemeral storage spec from the dataset shards size

        :param dataset_shards_size: Cumulative size (bytes) of dataset shard files, required to setup
            local ephemeral storage resource requests and limits
        :param ephemeral_storage_limits_scale: Scalar to be multiplied by ephemeral_storage_requests
            to obtain ephemeral_storage_limits. The ephemeral storage limits should be greater than
            the ephemeral storage requests. If the pod exceeds its limits, it will be evicted
            by the orchestrator. This scaler will prevent it as a safety margin.
        :param ephemeral_storage_buffer_size: Integer (bytes) to be added to the storage resource
            for the dataset shard files. This is required for the other storage usages from the pod.
            For example, there are several storage requirements for the downloading pretrained model weights,
            saving the trained model weights, and etc....
        :param work_dir_buffer_size: Integer (bytes) to be added to the work dir size limit
            where the shard files are downloaded. This is also required for the safe running.

        :return: This class instance
        """
        if compiled_dataset_shards.is_null():
            raise ValueError("Cannot create from NullCompiledDatasetShards.")

        dataset_shards_size = compiled_dataset_shards.total_size
        ephemeral_storage_requests = dataset_shards_size + ephemeral_storage_safety_margin
        ephemeral_storage_limits = int(ephemeral_storage_limits_scale * ephemeral_storage_requests)
        work_dir_size_limit = dataset_shards_size + work_dir_safety_margin

        return cls(
            limits=ephemeral_storage_limits,
            requests=ephemeral_storage_requests,
            work_dir_size_limit=work_dir_size_limit,
        )


@dataclass_json
@dataclass
class ComputeResources:
    """Data container for compute resources for training/optimize pods.

    :param cpu_requests: Number of CPU. If None, do not request.
    :param cpu_limits: Number of CPU. If None, do not limit.
    :param mem_requests: Main memory, RAM. If None, do not request.
    :param mem_limits: Main memory, RAM. If None, do not limit.
    :param gpu_requests: Number of GPU. If None, do not request.
    :param gpu_limits: Number of GPU. If None, do not limit.
    :param accelerator_name: Name of accelerator (GPU) resource.
        Typically it is "nvidia.com/gpu"
    """

    cpu_requests: typing.Optional[str]  # noqa: UP007
    cpu_limits: typing.Optional[str]  # noqa: UP007
    memory_requests: typing.Optional[str]  # noqa: UP007
    memory_limits: typing.Optional[str]  # noqa: UP007
    gpu_requests: typing.Optional[str]  # noqa: UP007
    gpu_limits: typing.Optional[str]  # noqa: UP007
    accelerator_name: str

    @classmethod
    def from_node_resources(cls) -> "ComputeResources":
        resources, accelerator_name = asyncio.run(calculate_training_resources())

        return cls(
            cpu_requests=resources["requests"].get("cpu"),
            cpu_limits=resources["limits"].get("cpu"),
            memory_requests=resources["requests"].get("memory"),
            memory_limits=resources["limits"].get("memory"),
            gpu_requests=resources["requests"].get(accelerator_name),
            gpu_limits=resources["limits"].get(accelerator_name),
            accelerator_name=accelerator_name,
        )

    def to_kwargs(self, is_requests: bool) -> dict[str, str]:
        """Return dictionary for keyword arguments of pod spec.

        For example,

        >>> resources = ComputeResources(...)
        >>> resources.to_kwargs(is_requests=True)
            {'cpu': '2000m', 'ephemeral_storage': '538347498', 'nvidia.com/gpu': '1', 'memory': '19531250Ki'}
        >>> resources.to_kwargs(is_requests=True)
            {'ephemeral_storage': '538347498', 'nvidia.com/gpu': '1'}
        """
        results = {}
        suffix = "requests" if is_requests else "limits"

        for prefix in ["cpu", "memory", "gpu"]:
            if (val := getattr(self, f"{prefix}_{suffix}")) is not None:
                key = self.accelerator_name if prefix == "gpu" else prefix
                results[key] = val

        return results
