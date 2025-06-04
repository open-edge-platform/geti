"""Main module of library"""

import functools
from collections import namedtuple

from kubernetes_asyncio import client as kube_client
from kubernetes_asyncio import config as kube_config
from kubernetes_asyncio.client.exceptions import ApiException
from kubernetes_asyncio.config import ConfigException

ClusterResources = namedtuple(  # noqa: PYI024
    "ClusterResources",
    [
        "cpu_available",
        "memory_available",
        "cpu_capacity",
        "memory_capacity",
        "accelerator_type",
        "accelerator_name",
    ],
)

ClusterCapacity = namedtuple("ClusterCapacity", ["cpu_capacity", "memory_capacity", "gpu_capacity"])  # noqa: PYI024


def k8s_cpu_to_millicpus(k8s_cpu: str) -> int:
    """convert cpu return from k8s to millicpus"""
    cpu_suffixes = {
        "P": 1000**5,
        "T": 1000**4,
        "G": 1000**3,
        "M": 1000**2,
        "K": 1000,
        "k": 1000,
        "m": 1000 ** (-1),
        "u": 1000 ** (-2),
        "n": 1000 ** (-3),
        "p": 1000 ** (-4),
    }

    for cpu_suffix, multiplier in cpu_suffixes.items():
        if cpu_suffix in k8s_cpu:
            return int(int(k8s_cpu.strip(cpu_suffix)) * multiplier / cpu_suffixes["m"])
    return int(float(k8s_cpu) / cpu_suffixes["m"])  # base unit does not have any suffix


def k8s_memory_to_kibibytes(k8s_memory: str) -> int:
    """convert memory return from k8s to kibibytes

    :raise ValueError: On failure to parse the provided `k8s_memory` value.
    """
    memory_suffixes = {
        "Pi": 1024**5,
        "Ti": 1024**4,
        "Gi": 1024**3,
        "Mi": 1024**2,
        "Ki": 1024,
        "P": 1000**5,
        "PB": 1000**5,
        "T": 1000**4,
        "TB": 1000**4,
        "G": 1000**3,
        "GB": 1000**3,
        "M": 1000**2,
        "MB": 1000**2,
        "K": 1000,
        "KB": 1000,
        "k": 1000,
    }
    err_msg = f"Invalid k8s memory value: {k8s_memory}"

    for memory_suffix, multiplier in memory_suffixes.items():
        if k8s_memory.endswith(memory_suffix):
            # compute bytes and divide by 1024 to return kibybytes
            try:
                return int(k8s_memory.strip(memory_suffix)) * multiplier // 1024
            except ValueError as err:
                raise ValueError(err_msg) from err
    raise ValueError(err_msg)


def async_cache_last_result(func):  # noqa: ANN001, ANN201
    """
    Decorator that caches first result returned by async function and returns cached value
    for each subsequent call of the decorated function.
    """
    cached_result = None

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        nonlocal cached_result
        if cached_result:
            return cached_result
        result = await func(*args, **kwargs)
        cached_result = result
        return result

    return wrapper


async def _load_kubeconfig(kubeconfig_path: str | None = None):
    """Load proper config file"""
    try:
        if kubeconfig_path:
            await kube_config.load_kube_config(config_file=kubeconfig_path)
        else:
            await kube_config.load_kube_config()
    except (FileNotFoundError, TypeError, ConfigException):
        kube_config.load_incluster_config()


@async_cache_last_result
async def calculate_available_resources_per_node(
    kubeconfig_path: str | None = None,
) -> ClusterResources:
    """Calculate available resources (in milliCpus and kibibytes units) for every node.
    Returns a tuple with following values:
      available_cpus_per_node
      available_memory_per_node
      cpu_capacity_per_node
      memory_capacity_per_node
      gpu_capacity_per_node

    As we do not expect new nodes being added to the cluster during runtime and assume
    that every k8s/platform pod works on master node, result of this function is cached after
    first execution."""
    await _load_kubeconfig(kubeconfig_path=kubeconfig_path)
    async with kube_client.ApiClient() as client:
        core_api = kube_client.CoreV1Api(client)
        nodes = await core_api.list_node()
        pods = await core_api.list_pod_for_all_namespaces()
        cm = await core_api.read_namespaced_config_map(namespace="impt", name="accelerator-configuration")
        configcm = await core_api.read_namespaced_config_map(namespace="impt", name="impt-configuration")

    pods = [pod for pod in pods.items if pod.status.phase == "Running"]

    available_cpus_per_node = []
    cpu_capacity_per_node = []
    available_memory_per_node = []
    memory_capacity_per_node = []
    accelerator_type = cm.data["accelerator_type"]
    accelerator_name = cm.data["accelerator_name"]
    for node in nodes.items:
        node_cpu_capacity = k8s_cpu_to_millicpus(node.status.allocatable["cpu"])
        node_cpu_usage = sum(
            sum(
                k8s_cpu_to_millicpus(container.resources.requests.get("cpu", "0m"))
                for container in pod.spec.containers
                if container.resources.requests
            )
            for pod in pods
            if pod.spec.node_name == node.metadata.name
        )
        available_cpus_per_node.append(node_cpu_capacity - node_cpu_usage)
        cpu_capacity_per_node.append(node_cpu_capacity)

        node_memory_capacity = k8s_memory_to_kibibytes(node.status.allocatable["memory"])
        node_memory_usage = sum(
            sum(
                k8s_memory_to_kibibytes(container.resources.limits.get("memory", "0Ki"))
                for container in pod.spec.containers
                if container.resources.limits
            )
            for pod in pods
            if pod.spec.node_name == node.metadata.name
        )
        available_memory_per_node.append(node_memory_capacity - node_memory_usage)
        memory_capacity_per_node.append(node_memory_capacity)

    return ClusterResources(
        available_cpus_per_node,
        available_memory_per_node,
        cpu_capacity_per_node,
        memory_capacity_per_node,
        accelerator_type,
        accelerator_name,
    )


async def get_resource_capacity_per_node(kubeconfig_path: str | None = None) -> ClusterCapacity:
    """Calculate available capacity (in milliCpus and kibibytes units) for every node.
    Returns a ClusterCapacity tuple with following values:
      cpu_capacity_per_node
      memory_capacity_per_node
      gpu_capacity_per_node
    """
    await _load_kubeconfig(kubeconfig_path=kubeconfig_path)
    async with kube_client.ApiClient() as client:
        core_api = kube_client.CoreV1Api(client)
        nodes = await core_api.list_node()
        label = await get_gpu_node_label(kubeconfig_path=kubeconfig_path)

    cpu_capacity_per_node = [k8s_cpu_to_millicpus(node.status.allocatable["cpu"]) for node in nodes.items]
    memory_capacity_per_node = [k8s_memory_to_kibibytes(node.status.allocatable["memory"]) for node in nodes.items]
    gpu_capacity_per_node = [int(node.status.allocatable.get(label, 0)) for node in nodes.items]

    return ClusterCapacity(
        cpu_capacity=cpu_capacity_per_node, memory_capacity=memory_capacity_per_node, gpu_capacity=gpu_capacity_per_node
    )


async def get_gpu_node_label(kubeconfig_path: str | None = None) -> str:
    """Returns tha node label stored in our configuration"""
    await _load_kubeconfig(kubeconfig_path=kubeconfig_path)
    async with kube_client.ApiClient() as client:
        core_api = kube_client.CoreV1Api(client)
        try:
            cm = await core_api.read_namespaced_config_map(namespace="impt", name="accelerator-configuration")
            label = cm.data["accelerator_name"]
        except ApiException:
            label = "nvidia.com/gpu"  # to preserve backward compatibility
    return label
