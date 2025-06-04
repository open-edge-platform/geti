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
A module containing check functions that are interacting with K8S.
"""

import asyncio
import logging
import os
import re
import time
from functools import lru_cache
from ipaddress import ip_address
from ssl import SSLError
from typing import Any

from geti_k8s_tools.calculate_cluster_resources import (
    ClusterCapacity,
    get_gpu_node_label,
    get_resource_capacity_per_node,
    k8s_cpu_to_millicpus,
    k8s_memory_to_kibibytes,
)
from kubernetes import client as kube_client
from kubernetes.client import CoreV1Api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

from checks.errors import CheckSkipped, K8SCheckError, K8SCheckWarning
from checks.ports import is_port_available
from configuration_models.upgrade_config import UpgradeConfig
from constants.platform import (
    DATA_STORAGE_VOLUME_CLAIM_NAME,
    DATA_STORAGE_VOLUME_NAME,
    GPU_PROVIDER_INTEL_ARC,
    GPU_PROVIDER_INTEL_MAX,
    GPU_PROVIDER_NVIDIA,
)
from platform_utils.kube_config_handler import KubernetesConfigHandler
from texts.checks import K8SChecksTexts

NUMBER_OF_RETRIES = 10
SLEEP_INTERVAL = 5
K8S_API_SERVER_PORT = 6443
SUPPORTED_VERSION_REGEX = r"v{version}.\d+($|\+k3s1)"
SUPPORTED_VERSIONS = [1.25]
RUNNING_ISTIO_INGRESSGATEWAY_POD = None
ISTIO_GATEWAY_CRD_NAME = "istio-gateway"
REQUIRED_ISTIO_VERSION = "1.18.x"
REQUIRED_ISTIO_VERSION_REGEX = r"1\.18\.\d+"
REQUIRED_METRICS_SERVER_VERSION = "v0.6.x"
REQUIRED_METRICS_SERVER_VERSION_REGEX = r"v0\.6\.\d+"
STORAGE_POD_NAME = "available-volume-check"

logger = logging.getLogger(__name__)


def check_k8s_connection(kubeconfig_path: str):  # noqa: ANN201
    """
    Check connection to K8S by listing namespaces in K8S API
    """
    try:
        logger.info("Checking K8S connection with kubectl cluster-info.")
        KubernetesConfigHandler(kube_config=kubeconfig_path)
        with kube_client.ApiClient() as client:
            core_api = kube_client.CoreV1Api(client)
            logger.debug("Listing namespaces in K8S API...")
            result = core_api.list_namespace()
            logger.debug(f"Result: {result}")
    except (
        KeyError,
        SSLError,
        ConnectionRefusedError,
    ) as error:
        raise K8SCheckError(K8SChecksTexts.connection_check_error) from error


@lru_cache
def get_cluster_resource_capacity(kubeconfig_path: str | None = None) -> ClusterCapacity:
    """
    Get resource capacity info (CPU, GPU, memory) for K8S cluster nodes.
    """
    logger.debug("Getting resource capacity info (CPU, GPU, memory) for K8S cluster nodes.")
    return asyncio.run(get_resource_capacity_per_node(kubeconfig_path=kubeconfig_path))


def check_k8s_is_not_installed():  # noqa: ANN201
    """
    Check whether Kubernetes is not installed by inspecting Kubernetes API server port.
    """

    logger.info("Checking whether Kubernetes is not installed...")
    if not is_port_available(K8S_API_SERVER_PORT):
        raise K8SCheckError(K8SChecksTexts.already_installed_k8s_check_error.format(port=K8S_API_SERVER_PORT))


def check_k8s_cpu_requirements(kubeconfig_path: str):  # noqa: ANN201
    """
    Check if all nodes on the cluster have minimum number of CPU cores, as defined by PLATFORM_CPU_CORES_MIN
    environment variable (defaults to 48 cores).
    """
    cpu_requirement = os.environ.get("PLATFORM_CPU_CORES_MIN", "16")
    cpu_requirement_in_millicpus = k8s_cpu_to_millicpus(cpu_requirement)
    available_resources: ClusterCapacity = get_cluster_resource_capacity(kubeconfig_path=kubeconfig_path)
    cpu_capacity_in_cores = ",".join([str(millicpus // 1000) for millicpus in available_resources.cpu_capacity])

    logger.info(
        f"Checking if cluster CPU capacity {available_resources.cpu_capacity} "
        f"is matching {cpu_requirement_in_millicpus} min CPUs requirement."
    )
    logger.debug(f"CPU capacity in cores: {cpu_capacity_in_cores}.")
    if any(cpu_capacity < cpu_requirement_in_millicpus for cpu_capacity in available_resources.cpu_capacity):
        raise K8SCheckError(
            K8SChecksTexts.cpu_requirements_check_error.format(
                cpu_capacity=cpu_capacity_in_cores, cpu_requirement=cpu_requirement
            )
        )


def check_k8s_memory_requirements(kubeconfig_path: str):  # noqa: ANN201
    """
    Check if all nodes on the cluster have minimum amount of memory, as defined by PLATFORM_MEMORY_MIN
    environment variable (defaults to 64 gigabytes).
    """
    mem_requirement = os.environ.get("PLATFORM_MEMORY_MIN", "64GB")
    mem_requirement_in_kibibytes = k8s_memory_to_kibibytes(mem_requirement)
    available_resources: ClusterCapacity = get_cluster_resource_capacity(kubeconfig_path=kubeconfig_path)
    memory_capacity_in_gibibytes = ",".join(
        [f"{kibibytes // 1024**2}Gi" for kibibytes in available_resources.memory_capacity]
    )

    logger.info(
        f"Checking if cluster memory capacity {available_resources.memory_capacity} "
        f"is matching {mem_requirement_in_kibibytes} min memory requirement."
    )
    logger.debug(f"Available memory capacity: {memory_capacity_in_gibibytes}")
    if any(mem_capacity < mem_requirement_in_kibibytes for mem_capacity in available_resources.memory_capacity):
        raise K8SCheckWarning(
            K8SChecksTexts.mem_requirements_check_error.format(
                mem_capacity=memory_capacity_in_gibibytes, mem_requirement=mem_requirement
            )
        )


def _delete_namespaced_pod(name: str, namespace: str, api_instance: CoreV1Api):
    pod_response = api_instance.list_namespaced_pod(namespace=namespace, field_selector=f"metadata.name={name}")
    if pod_response.items:
        api_instance.delete_namespaced_pod(name=name, namespace=namespace)


def check_k8s_gpu_requirements(config: UpgradeConfig):  # noqa: ANN201
    """
    Check if at least one node on the cluster has GPU.
    Skip if 'gpu_support' is set to 'False'.
    """
    if not config.gpu_support.value:
        logger.info("PLATFORM_GPU_REQUIRED is set to false, skipping check.")
        raise CheckSkipped

    available_resources: ClusterCapacity = get_cluster_resource_capacity(kubeconfig_path=config.kube_config.value)
    logger.info(
        f"Checking if cluster GPU capacity {available_resources.gpu_capacity} is matching requirement: GPU required."
    )
    if not any(gpu_capacity > 0 for gpu_capacity in available_resources.gpu_capacity):
        raise K8SCheckWarning(K8SChecksTexts.gpu_requirements_check_error)

    # Let's set gpu_provider according to the configuration, 'nvidia' when setting missing for Geti < 2.0.0
    label = asyncio.run(get_gpu_node_label(kubeconfig_path=config.kube_config.value))
    if label == "nvidia.com/gpu":
        config.gpu_provider.value = GPU_PROVIDER_NVIDIA
    elif label == "gpu.intel.com/i915":
        config.gpu_provider.value = GPU_PROVIDER_INTEL_MAX
    elif label == "gpu.intel.com/xe":
        config.gpu_provider.value = GPU_PROVIDER_INTEL_ARC


def get_k8s_cluster_version(kubeconfig_path: str) -> str:
    """Returns cluster's kubernetes version"""
    KubernetesConfigHandler(kube_config=kubeconfig_path)
    with kube_client.ApiClient() as client:
        version_api = kube_client.VersionApi(client)
        version = version_api.get_code()
        logger.debug(f"Kubernetes cluster version: {version}.")
    return version.git_version


def check_k8s_cluster_version(kubeconfig_path: str):  # noqa: ANN201
    """
    Check if cluster has proper version
    """
    logger.info("Compare k8s git version with list of supported versions and distros.")
    k8s_git_version = get_k8s_cluster_version(kubeconfig_path=kubeconfig_path)
    logger.debug(f"Supported versions: {SUPPORTED_VERSIONS}.")
    for supported_version in SUPPORTED_VERSIONS:
        if re.match(SUPPORTED_VERSION_REGEX.format(version=supported_version), k8s_git_version):
            logger.debug(f"K8s git version {k8s_git_version} matches the requirements.")
            break
    else:
        raise K8SCheckError(K8SChecksTexts.cluster_version_check_error.format(cluster_version=k8s_git_version))


def check_metrics_server_installed(kubeconfig_path: str):  # noqa: ANN201
    """
    Check if metrics-server installed
    """
    logger.info("Checking if metrics-server is installed.")
    KubernetesConfigHandler(kube_config=kubeconfig_path)

    with kube_client.ApiClient() as api_client:
        core_api = kube_client.CoreV1Api(api_client)
        # according to the official installation guide,
        # the "metrics-server" component is consistently installed within the "kube-system" namespace
        metrics_server_pods = core_api.list_pod_for_all_namespaces(label_selector="k8s-app=metrics-server").items

        if not metrics_server_pods:
            raise K8SCheckError(K8SChecksTexts.metrics_server_installation_check_error)

        for pod in metrics_server_pods:
            if pod.status.phase != "Running":
                raise K8SCheckError(K8SChecksTexts.metrics_server_not_running_check_error)


def check_metrics_server_version(kubeconfig_path: str):  # noqa: ANN201
    """
    Check metrics server version
    """
    logger.info("Checking if metrics-server version is correct.")
    try:
        KubernetesConfigHandler(kube_config=kubeconfig_path)

        with kube_client.ApiClient() as api_client:
            core_api = kube_client.CoreV1Api(api_client)

            # according to the official installation guide,
            # the "metrics-server" component is consistently installed within the "kube-system" namespace
            metrics_server_pods = core_api.list_pod_for_all_namespaces(label_selector="k8s-app=metrics-server").items

            metrics_server_pod = metrics_server_pods[-1]

            exec_command = [
                "/metrics-server",
                "--version",
            ]
            logger.debug(f"Executing command: '{' '.join(s for s in exec_command)}'")
            response = stream(
                core_api.connect_get_namespaced_pod_exec,
                name=metrics_server_pod.metadata.name,
                namespace=metrics_server_pod.metadata.namespace,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )
    except ApiException as api_err:
        logger.error("Failed to connect to metrics-server.", exc_info=api_err)
        raise K8SCheckError(K8SChecksTexts.metrics_server_connection_error) from api_err

    metrics_server_version = response.strip()
    logger.debug(f"Output: {response}\nCurrent metrics-server version: {metrics_server_version}")
    logger.debug(f"Required metrics-server version: {REQUIRED_METRICS_SERVER_VERSION}")

    if not re.match(REQUIRED_METRICS_SERVER_VERSION_REGEX, metrics_server_version):
        raise K8SCheckError(
            K8SChecksTexts.metrics_server_version_check_error.format(
                version=metrics_server_version,
            )
        )


def check_istio_ingress_gateway_installation(kubeconfig_path: str):  # noqa: ANN201
    """
    Check if Istio Ingress Gateway is installed and correctly configured
    """
    global RUNNING_ISTIO_INGRESSGATEWAY_POD  # noqa: PLW0603
    istio_namespace = "istio-system"
    iig_component_name = "istio-gateway"
    try:
        KubernetesConfigHandler(kube_config=kubeconfig_path)
        with kube_client.ApiClient() as api_client:
            core_api = kube_client.CoreV1Api(api_client)
            custom_api = kube_client.CustomObjectsApi(api_client)

            logger.info("Checking if Istio Ingress Gateway is installed and configured.")
            RUNNING_ISTIO_INGRESSGATEWAY_POD = _get_running_ingress_gateway_pod(
                core_api, istio_namespace, iig_component_name
            )

            logger.info("Checking if Istio Ingress Gateway service has a valid external IP address.")
            _check_ingress_gateway_service_ip(core_api, istio_namespace, iig_component_name)

            logger.info("Checking if Istio Gateway CRD is configured.")
            _check_istio_gateway_crd(custom_api, istio_namespace)
    except ApiException as api_err:
        logger.error("Failed to connect to istio-gateway.", exc_info=api_err)
        raise K8SCheckError(K8SChecksTexts.istio_ingress_gateway_connection_error) from api_err


def _get_running_ingress_gateway_pod(core_api, istio_namespace, iig_component_name):  # noqa: ANN001
    """
    Check if Istio Ingress Gateway is installed
    """
    pods_list = core_api.list_namespaced_pod(namespace=istio_namespace)
    running_istio_ingressgateway_pods = [
        pod
        for pod in pods_list.items
        if pod.metadata.name.startswith(iig_component_name) and pod.status.phase == "Running"
    ]
    if not running_istio_ingressgateway_pods:
        raise K8SCheckError(K8SChecksTexts.istio_ingress_gateway_installation_check_error)
    return running_istio_ingressgateway_pods[0]


def _check_ingress_gateway_service_ip(core_api, istio_namespace, iig_component_name):  # noqa: ANN001
    """
    Check if Istio Ingress Gateway service has a valid IP address
    """
    istio_svc = core_api.read_namespaced_service(name=iig_component_name, namespace=istio_namespace)
    ingress_info = istio_svc.status.load_balancer.ingress
    external_ip = ingress_info[0].ip if ingress_info else None
    try:
        ip_address(external_ip)
    except ValueError as val_err:
        raise K8SCheckError(K8SChecksTexts.istio_ingress_gateway_ip_configuration_check_error) from val_err


def _check_istio_gateway_crd(custom_api, istio_namespace):  # noqa: ANN001
    """
    Check if Istio Gateway CRD is configured with the right name
    """
    gateways = custom_api.list_namespaced_custom_object(
        group="networking.istio.io",
        version="v1beta1",
        namespace=istio_namespace,
        plural="gateways",
    )
    if not any(gateway["metadata"]["name"] == ISTIO_GATEWAY_CRD_NAME for gateway in gateways["items"]):
        raise K8SCheckError(K8SChecksTexts.istio_gateway_configuration_check_error)


def check_istio_ingress_gateway_version():  # noqa: ANN201
    """
    Check if Istio Ingress Gateway's version is correct
    """
    logger.info("Checking if Istio Ingress Gateway's version is correct.")
    if not RUNNING_ISTIO_INGRESSGATEWAY_POD:
        logger.info("No Istio Ingress Gateway pod was found running, skipping Istio Ingress Gateway version check.")
        raise CheckSkipped

    istio_proxy_container = next(
        container for container in RUNNING_ISTIO_INGRESSGATEWAY_POD.spec.containers if container.name == "istio-proxy"
    )
    version_pattern = re.compile(REQUIRED_ISTIO_VERSION_REGEX)
    image_tag = istio_proxy_container.image.split(":")[-1]
    logger.debug(f"Current Istio Ingress Gateway version: {image_tag}")
    logger.debug(f"Required Istio Ingress Gateway version: {REQUIRED_ISTIO_VERSION}")
    if not version_pattern.match(image_tag):
        raise K8SCheckError(
            K8SChecksTexts.istio_ingress_gateway_version_check_error.format(
                present_istio_version=image_tag,
            )
        )


def _check_if_stale_pod_already_on_platform(pod_name: str, api_instance: kube_client.CoreV1Api, pod_namespace: str):
    try:
        api_instance.read_namespaced_pod(name=pod_name, namespace=pod_namespace)
        api_instance.delete_namespaced_pod(name=pod_name, namespace=pod_namespace)
        for _ in range(60 * 15):
            pod_data = api_instance.read_namespaced_pod(name=pod_name, namespace=pod_namespace)
            if pod_data.status.phase in ["Terminating", "Running"]:
                time.sleep(1)
            else:
                break
        else:
            raise K8SCheckError(f"Pod {pod_name} could not be deleted. Please try deleting it manually.")
    except ApiException as api_err:
        logger.debug(api_err)


def _create_k8s_exec_pod(
    pod_name: str,
    api_instance: kube_client.CoreV1Api,
    pod_namespace: str,
    platform_installed: bool = True,
    exec_image: str | None = None,
):
    volume_mount_path = ""
    if platform_installed and not exec_image:
        volume_mount_path = api_instance.read_persistent_volume(DATA_STORAGE_VOLUME_NAME).spec.host_path.path
        config_cm = api_instance.read_namespaced_config_map(f"{pod_namespace}-configuration", pod_namespace)
        exec_image = (
            f"{config_cm.data['registry_address']}/open-edge-platform/geti/migration-job:{config_cm.data['tag']}"
        )

    pod_manifest: dict[str, Any] = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"name": pod_name, "namespace": pod_namespace, "labels": {"sidecar.istio.io/inject": "false"}},
        "spec": {
            "containers": [
                {
                    "name": pod_name,
                    "image": exec_image,
                    "command": ["sleep", "1h"],
                    "volumeMounts": (
                        [{"name": DATA_STORAGE_VOLUME_NAME, "mountPath": volume_mount_path}]
                        if platform_installed
                        else []
                    ),
                }
            ],
            "volumes": (
                [
                    {
                        "name": DATA_STORAGE_VOLUME_NAME,
                        "persistentVolumeClaim": {"claimName": DATA_STORAGE_VOLUME_CLAIM_NAME},
                    }
                ]
                if platform_installed
                else []
            ),
        },
    }
    _check_if_stale_pod_already_on_platform(pod_name=pod_name, pod_namespace=pod_namespace, api_instance=api_instance)

    pod_data = api_instance.create_namespaced_pod(body=pod_manifest, namespace=pod_namespace)
    for _ in range(60 * 5):
        pod_data = api_instance.read_namespaced_pod(name=pod_name, namespace=pod_namespace)
        if pod_data.status.phase == "Running":
            break
        time.sleep(1)
    else:
        raise K8SCheckError(f"Expected pod status: Running, actual: {pod_data.status.phase}")
