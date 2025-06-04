# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
Utility functions related to Kubernetes.
"""

import base64
import http
import logging
import time
from collections import namedtuple
from collections.abc import Callable
from datetime import datetime

import pytz
from kubernetes import client, watch
from kubernetes.client import ApiException, BatchV1Api, CoreV1Api, V1Secret
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from constants.paths import K3S_KUBECONFIG_PATH
from platform_stages.steps.errors import FailedJobError, RestartDeploymentError
from platform_utils.kube_config_handler import KubernetesConfigHandler

logger = logging.getLogger(__name__)
STOP_AFTER_ATTEMPT = 5
WAIT_FIXED = 5

Endpoint = namedtuple("Endpoint", ["namespace", "name"])  # noqa: PYI024
ISTIOD = Endpoint(name="istiod", namespace="istio-system")
CERT_MANAGER_WEBHOOK = Endpoint(name="cert-manager-webhook", namespace="cert-manager")
OPA = Endpoint(name="admission-controller", namespace="opa-istio")

REQUIRED_ENDPOINTS = [ISTIOD, CERT_MANAGER_WEBHOOK, OPA]
MASTER_NODE_LABEL = "node-role.kubernetes.io/control-plane"


def decode_string_b64(data: str) -> str:  # noqa: D103
    return base64.b64decode(data).decode("utf-8")


def encode_data_b64(data: bytes) -> str:  # noqa: D103
    return base64.b64encode(data).decode("utf-8")


def ensure_endpoint() -> Callable:
    """Checks whether the endpoint are ready when ip is assigned."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)
            core_v1_api = client.CoreV1Api()
            for endpoint in REQUIRED_ENDPOINTS:
                try:
                    logger.info(f"For endpoint '{endpoint.name}' in namespace '{endpoint.namespace}':")
                    logger.info("Check if ip is properly assigned.")
                    k8s_endpoint = core_v1_api.read_namespaced_endpoints(
                        name=endpoint.name, namespace=endpoint.namespace
                    )

                    subsets = k8s_endpoint.subsets if k8s_endpoint.subsets else []
                    is_endpoint_ready = (
                        len([address.ip for subset in subsets for address in (subset.addresses or [])]) > 0
                    )
                    logger.debug(f"Is endpoint ready: {is_endpoint_ready}")

                    if not is_endpoint_ready:
                        logger.info("Endpoint is not ready (no ip), then deployment needs to be restarted.")
                        logger.debug(f"Endpoints subsets: {subsets}")
                        restart_deployment(endpoint.name, endpoint.namespace)

                except ApiException as api_err:
                    if api_err.status == http.HTTPStatus.NOT_FOUND:
                        # we do not care if endpoint does not exist
                        continue
            return func(*args, **kwargs)

        return wrapper

    return decorator


def restart_deployment(name: str, namespace: str | None = None) -> None:
    """
    Restart Kubernetes Deployment.
    """
    KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)
    v1dep = client.AppsV1Api()
    logger.info(f"Deployment '{name}' is being restarted.")
    try:
        v1dep.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=_get_restarted_at_patch_body(),
        )
    except ApiException as ex:
        raise RestartDeploymentError from ex
    logger.info("Deployment is restarted.")


def _get_restarted_at_patch_body():
    """
    Return patch body used to restart a Deployment now.
    """
    return {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "kubectl.kubernetes.io/restartedAt": datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
                    }
                }
            }
        }
    }


@retry(
    retry=retry_if_exception_type(ApiException),
    stop=stop_after_attempt(STOP_AFTER_ATTEMPT),
    wait=wait_fixed(WAIT_FIXED),
    reraise=True,
)
def disable_automount_service_account_token(name: str = "default", namespace: str = "default") -> None:
    """
    Disable automountServiceAccountToken for selected Service Account.
    """
    KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)
    core_v1_api = client.CoreV1Api()
    logger.info(f"Service account '{name}' will have automount service account token disabled.")
    core_v1_api.patch_namespaced_service_account(
        name=name, namespace=namespace, body={"automountServiceAccountToken": False}
    )
    logger.info("Service account is patched.")


def create_namespace(name: str, labels: dict, annotations: dict) -> None:
    """
    Create namespace with labels and annotations.
    """
    KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)
    core_v1_api = client.CoreV1Api()

    try:
        existing_namespace = core_v1_api.read_namespace(name)
        logger.info(f"Namespace '{name}' already exists. Updating labels.")

        existing_labels = existing_namespace.metadata.labels or {}
        updated_labels = {**existing_labels, **labels}

        existing_annotations = existing_namespace.metadata.annotations or {}
        updated_annotations = {**existing_annotations, **annotations}

        existing_namespace.metadata.labels = updated_labels
        existing_namespace.metadata.annotations = updated_annotations

        core_v1_api.patch_namespace(name, existing_namespace)
        logger.info("Namespace updated with new labels and annotations.")

    except ApiException as ex:
        if ex.status == 404:
            logger.info(f"Creating namespace '{name}' with provided labels and annotations.")
            body = {"metadata": {"name": name, "labels": labels, "annotations": annotations}}
            core_v1_api.create_namespace(body=body)
            logger.info("Namespace created.")
        else:
            logger.error("Error when accessing the Kubernetes API.", exc_info=True)
            raise


@retry(
    retry=retry_if_exception_type(ApiException),
    stop=stop_after_attempt(STOP_AFTER_ATTEMPT),
    wait=wait_fixed(WAIT_FIXED),
    reraise=True,
)
def get_secret_from_namespace(name: str, namespace: str) -> V1Secret:
    """
    Get selected secret from namespace
    """
    logger.info(f"Get secret '{name}' from namespace '{namespace}'.")
    KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)
    core_v1_api = client.CoreV1Api()
    secret = core_v1_api.read_namespaced_secret(name=name, namespace=namespace)
    logger.info("Secret is retrieved.")
    return secret


def get_master_node_allocatable_resources() -> dict:
    """
    Get all allocatable resources for a master node.
    """
    KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)
    core_v1_api = client.CoreV1Api()
    logger.info(f"Get list of nodes based on label {MASTER_NODE_LABEL}.")
    nodes = core_v1_api.list_node(label_selector=MASTER_NODE_LABEL)
    return nodes.items[0].status.allocatable  # there is only 1 node


def collect_job_logs(api: CoreV1Api, job_name: str, namespace: str, log_file: str) -> None:
    """
    Collect logs for the pods associated with the job.
    """
    logger = logging.getLogger(__name__)
    file_handler = logging.FileHandler(log_file)
    logger.addHandler(file_handler)

    pods = api.list_namespaced_pod(namespace=namespace, label_selector=f"app={job_name}")

    for pod in pods.items:
        if job_name in pod.metadata.name:
            try:
                log = api.read_namespaced_pod_log(name=pod.metadata.name, namespace=namespace, container=job_name)
                logger.info(f"Logs for job {pod.metadata.name}:\n{log}")
            except client.exceptions.ApiException as ex:
                logger.error(f"Failed to get logs for job {pod.metadata.name}: {ex}")


def wait_for_job_completion(api: BatchV1Api, job_name: str, namespace: str, timeout: int) -> None:
    """
    Wait for kubernetes job completion
    """
    timeout_seconds = timeout * 60
    w = watch.Watch()
    start_time = time.time()
    for event in w.stream(api.list_namespaced_job, namespace=namespace, timeout_seconds=timeout_seconds):
        job = event["object"]
        if job.metadata.name == job_name:
            if job.status.succeeded is not None and job.status.succeeded > 0:
                logger.info(f"Job '{job_name}' completed successfully.")
                return
            if job.status.failed is not None and job.status.failed > 0:
                logger.error(f"Job '{job_name}' failed.")
                raise FailedJobError(f"Job '{job_name}' did not complete within the timeout period.")
            if time.time() - start_time > timeout_seconds:
                raise TimeoutError(f"Job '{job_name}' did not complete within the timeout period.")
    raise TimeoutError(f"Job '{job_name}' did not complete within the timeout period.")


def delete_job(batch_api: BatchV1Api, namespace: str, job_name: str) -> None:
    """
    Delete a Kubernetes job and its associated pods.
    """

    logger = logging.getLogger(__name__)
    try:
        delete_options = client.V1DeleteOptions(propagation_policy="Foreground")
        batch_api.delete_namespaced_job(name=job_name, namespace=namespace, body=delete_options)
        logger.info(f"Job '{job_name}' deleted successfully.")
    except client.exceptions.ApiException as ex:
        logger.error(f"Failed to delete job '{job_name}': {ex}")
        return
