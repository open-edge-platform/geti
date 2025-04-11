"""
Functions for retrieving information about kubernetes cluster
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
import logging
import os

import kubernetes

from service_connection.k8s_client.apis import K8S

logger = logging.getLogger(__name__)


def _dump_pod_logs(pod_name: str, container_name: str | None, namespace: str, directory: str):
    core_v1_api = K8S.get_k8s_api()
    try:
        if container_name:
            pod_logs = core_v1_api.read_namespaced_pod_log(
                name=pod_name, container=container_name, namespace=namespace, _preload_content=True, pretty="true"
            )
        else:
            pod_logs = core_v1_api.read_namespaced_pod_log(
                name=pod_name, namespace=namespace, _preload_content=True, pretty="true"
            )
    except kubernetes.client.ApiException as api_err:
        logger.error(api_err)
        pod_logs = str(api_err)
    pod_logs_dir = os.path.join(directory, namespace, pod_name)
    if not os.path.exists(pod_logs_dir):
        os.makedirs(pod_logs_dir)
    with open(os.path.join(pod_logs_dir, "logs.txt"), "w") as file:
        file.write(pod_logs)


def _dump_appsv1_data(namespace: str) -> list[tuple[str, dict]]:
    apps_v1_api = K8S.get_apps_k8s_api()
    daemon_sets = json.loads(apps_v1_api.list_namespaced_daemon_set(namespace=namespace, _preload_content=False).data)
    deployments = json.loads(apps_v1_api.list_namespaced_deployment(namespace=namespace, _preload_content=False).data)
    replica_sets = json.loads(apps_v1_api.list_namespaced_replica_set(namespace=namespace, _preload_content=False).data)
    stateful_sets = json.loads(
        apps_v1_api.list_namespaced_stateful_set(namespace=namespace, _preload_content=False).data
    )
    return [
        ("daemonsets.json", daemon_sets),
        ("deployments.json", deployments),
        ("replicasets.json", replica_sets),
        ("statefulsets.json", stateful_sets),
    ]


def _dump_corev1_data(namespace: str) -> list[tuple[str, dict]]:
    core_v1_api = K8S.get_k8s_api()
    pods = json.loads(core_v1_api.list_namespaced_pod(namespace=namespace, _preload_content=False).data)
    events = json.loads(core_v1_api.list_namespaced_event(namespace=namespace, _preload_content=False).data)
    services = json.loads(core_v1_api.list_namespaced_service(namespace=namespace, _preload_content=False).data)
    replication_controllers = json.loads(
        core_v1_api.list_namespaced_replication_controller(namespace=namespace, _preload_content=False).data
    )
    config_maps = json.loads(core_v1_api.list_namespaced_config_map(namespace=namespace, _preload_content=False).data)
    return [
        ("pods.json", pods),
        ("events.json", events),
        ("services.json", services),
        ("replication-controllers.json", replication_controllers),
        ("configmaps.json", config_maps),
    ]


def _dump_namespace_data(namespace: str, directory: str):
    if not os.path.exists(os.path.join(directory, namespace)):
        os.makedirs(os.path.join(directory, namespace))
    filenames = _dump_appsv1_data(namespace=namespace) + _dump_corev1_data(namespace=namespace)
    logger.debug(f"Retrieving namespace {namespace} data")
    for file_name, file_data in filenames:
        if file_name == "pods.json":
            for pod in file_data["items"]:
                logger.debug(f"Retrieving default log container for pod {pod['metadata'].get('name')}")
                if pod_annotations := pod["metadata"].get("annotations", {}):
                    default_log_container = pod_annotations.get("kubectl.kubernetes.io/default-container")
                    _dump_pod_logs(
                        pod_name=pod["metadata"]["name"],
                        container_name=default_log_container,
                        namespace=namespace,
                        directory=directory,
                    )
                else:
                    logger.warning(f"Missing pod annotations for pod {pod['metadata'].get('name')}")
                    logger.debug(f"Pod with missing annotations metadata: {pod['metadata']}")
                    continue

        with open(os.path.join(directory, namespace, file_name), "w") as file:
            json.dump(file_data, file, ensure_ascii=False, indent=4)


def _dump_nodes_list(directory: str):
    core_v1_api = K8S.get_k8s_api()
    nodes = json.loads(core_v1_api.list_node(_preload_content=False).data)
    with open(os.path.join(directory, "nodes.json"), "w") as file:
        json.dump(nodes, file, ensure_ascii=False, indent=4)


def create_cluster_info_dump(directory: str):  # noqa: ANN201
    """Returns the path where cluster-info dump is stored."""

    with kubernetes.client.ApiClient() as client:
        core_api = kubernetes.client.CoreV1Api(client)
        v1_namepsace_list = core_api.list_namespace()

    namespaces = [namespace.metadata.name for namespace in v1_namepsace_list.items]
    for namespace in namespaces:
        _dump_namespace_data(namespace=namespace, directory=directory)

    _dump_nodes_list(directory=directory)
