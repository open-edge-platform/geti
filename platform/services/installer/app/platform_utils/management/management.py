# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""Platform management functions"""

import logging

import kubernetes
from kubernetes.client.exceptions import ApiException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from configuration_models.upgrade_config import UpgradeConfig
from constants.platform import PLATFORM_NAMESPACE
from platform_utils.kube_config_handler import KubernetesConfigHandler

logger = logging.getLogger(__name__)

STOP_AFTER_ATTEMPT = 25
WAIT_FIXED = 20

SPECIAL_DEPLOYMENTS_NAMES = ["impt-modelmesh-controller"]


class InvalidReplicasAmount(Exception):
    """Invalid replicas exception"""


class PodStillPresent(Exception):
    """Pod still present exception"""


class ConflictException(Exception):
    """Conflict exception"""


def _is_pod_ready(pod: kubernetes.client.V1Pod) -> bool:
    """Check if a pod is ready."""
    ready_condition = next((condition for condition in pod.status.conditions if condition.type == "Ready"), None)
    return ready_condition is not None and ready_condition.status == "True"


@retry(
    retry=retry_if_exception_type(InvalidReplicasAmount),
    stop=stop_after_attempt(STOP_AFTER_ATTEMPT),
    wait=wait_fixed(WAIT_FIXED),
    reraise=True,
)
def _ensure_desired_replicas(
    core_api: kubernetes.client.CoreV1Api,
    obj: kubernetes.client.V1Deployment | kubernetes.client.V1StatefulSet,
    replicas: int,
):
    """Ensure obj has desired replicas."""

    label_selector = ",".join([f"{key}={value}" for key, value in obj.spec.selector.match_labels.items()])
    label_selector_exclude_jobs = f"{label_selector},!job-name"
    pods_list = core_api.list_namespaced_pod(
        namespace=obj.metadata.namespace, label_selector=label_selector_exclude_jobs
    )

    current_replica_count = len(pods_list.items)

    if replicas == 0 and current_replica_count > 0:
        logger.warning(
            f"Mismatch: Desired replicas for '{obj.metadata.name}' is 0, "
            f"but current replica count is {current_replica_count}. Retrying..."
        )
        raise InvalidReplicasAmount(
            f"Desired and current ready replicas for '{obj.metadata.name}' mismatch. "
            f"Desired: '0', current: {current_replica_count}"
        )

    if current_replica_count == 0:
        if replicas > 0:
            logger.warning(
                f"Mismatch: Desired replicas for '{obj.metadata.name}' is {replicas}, but no pods found. Retrying..."
            )
            raise InvalidReplicasAmount(
                f"Desired and current ready replicas for '{obj.metadata.name}' mismatch. "
                f"Desired: 'at least 1', current: {current_replica_count}"
            )
    elif any(pod.status.phase != "Running" or not _is_pod_ready(pod) for pod in pods_list.items):
        logger.warning(f"Mismatch: Some pods for '{obj.metadata.name}' are not running or not yet ready. Retrying...")
        raise InvalidReplicasAmount(
            f"Desired and current ready replicas for '{obj.metadata.name}' mismatch. Desired: 'at least 1', current: 0"
        )


@retry(
    retry=retry_if_exception_type(ConflictException),
    stop=stop_after_attempt(STOP_AFTER_ATTEMPT),
    wait=wait_fixed(WAIT_FIXED),
    reraise=True,
)
def _replace_deployment_with_fetch_retry(
    apps_api: kubernetes.client.AppsV1Api, deployment: kubernetes.client.V1Deployment
) -> None:
    try:
        current_deployment = apps_api.read_namespaced_deployment(
            name=deployment.metadata.name, namespace=deployment.metadata.namespace
        )
        current_deployment.spec = deployment.spec
        apps_api.replace_namespaced_deployment(
            name=deployment.metadata.name, namespace=deployment.metadata.namespace, body=current_deployment
        )
    except ApiException as e:
        if e.status == 409:
            raise ConflictException
        raise


@retry(
    retry=retry_if_exception_type(ConflictException),
    stop=stop_after_attempt(STOP_AFTER_ATTEMPT),
    wait=wait_fixed(WAIT_FIXED),
    reraise=True,
)
def _replace_statefulset_with_fetch_retry(
    apps_api: kubernetes.client.AppsV1Api, statefulset: kubernetes.client.V1StatefulSet
) -> None:
    try:
        current_statefulset = apps_api.read_namespaced_stateful_set(
            name=statefulset.metadata.name, namespace=statefulset.metadata.namespace
        )
        current_statefulset.spec = statefulset.spec
        apps_api.replace_namespaced_stateful_set(
            name=statefulset.metadata.name, namespace=statefulset.metadata.namespace, body=current_statefulset
        )
    except ApiException as e:
        if e.status == 409:
            raise ConflictException
        raise


def _patch_platform(config: UpgradeConfig, replicas: int) -> None:  # noqa: C901, PLR0912
    """Patch Platform by stopping or starting all Platform's pods."""
    KubernetesConfigHandler(kube_config=config.kube_config.value)

    with kubernetes.client.ApiClient() as client:
        # suspend/unsuspend platform cron jobs
        batch_api = kubernetes.client.BatchV1Api(client)
        cron_jobs_list = batch_api.list_namespaced_cron_job(PLATFORM_NAMESPACE)
        cron_jobs: list[kubernetes.client.V1CronJob] = cron_jobs_list.items

        for cron_job in cron_jobs:
            patch = {"op": "replace", "path": "/spec/suspend", "value": not bool(replicas)}
            batch_api.patch_namespaced_cron_job(
                name=cron_job.metadata.name, namespace=cron_job.metadata.namespace, body=[patch]
            )
            logger.debug(f"Cron job: '{cron_job.metadata.name}' patched with: '.spec.suspend={not bool(replicas)}'")

        if replicas == 0:
            remove_platform_workloads_tasks(config)
            remove_redundant_platform_pods(config)

        core_api = kubernetes.client.CoreV1Api(client)
        apps_api = kubernetes.client.AppsV1Api(client)
        deployments = get_ordered_deployments(apps_api=apps_api)

        for deployment in deployments:
            # as we need to remove the init job to be able to create another one,
            # but in case of installation failure, we need to remove the 'kubectl-wait' init container,
            # otherwise, the components won't start due to lack of this init job
            deployment_init_containers: list[kubernetes.client.V1Container] = (
                deployment.spec.template.spec.init_containers
            )
            if replicas == 1 and deployment_init_containers:
                updated_init_containers = [
                    container for container in deployment_init_containers if container.name != "kubectl-wait"
                ]
                deployment.spec.template.spec.init_containers = updated_init_containers

            deployment.spec.replicas = replicas

            _replace_deployment_with_fetch_retry(apps_api=apps_api, deployment=deployment)

            # wait for special deployment, before scaling the rest (only while scaling to 0)
            if deployment.metadata.name in SPECIAL_DEPLOYMENTS_NAMES and replicas == 0:
                _ensure_desired_replicas(core_api=core_api, obj=deployment, replicas=replicas)

        stateful_set_list = apps_api.list_namespaced_stateful_set(PLATFORM_NAMESPACE)
        stateful_sets: list[kubernetes.client.V1StatefulSet] = stateful_set_list.items

        for stateful_set in stateful_sets:
            # as we need to remove the init job to be able to create another one,
            # but in case of installation failure, we need to remove the 'kubectl-wait' init container,
            # otherwise, the components won't start due to lack of this init job
            stateful_set_init_containers: list[kubernetes.client.V1Container] = (
                stateful_set.spec.template.spec.init_containers
            )
            if replicas == 1 and stateful_set_init_containers:
                updated_init_containers = [
                    container for container in stateful_set_init_containers if container.name != "kubectl-wait"
                ]
                stateful_set.spec.template.spec.init_containers = updated_init_containers

            stateful_set.spec.replicas = replicas

            _replace_statefulset_with_fetch_retry(apps_api=apps_api, statefulset=stateful_set)

        for deployment in deployments:
            _ensure_desired_replicas(core_api=core_api, obj=deployment, replicas=replicas)

        for stateful_set in stateful_sets:
            _ensure_desired_replicas(core_api=core_api, obj=stateful_set, replicas=replicas)

        # we need to remove the init job to be able to create another one
        if replicas == 0:
            jobs_list = batch_api.list_job_for_all_namespaces()
            jobs: list[kubernetes.client.V1Job] = jobs_list.items

            try:
                for job in jobs:
                    batch_api.delete_namespaced_job(
                        name=job.metadata.name, namespace=job.metadata.namespace, grace_period_seconds=0
                    )
                logger.info(f"Job: '{job.metadata.name}' removed.")
            except kubernetes.client.exceptions.ApiException:
                pass

        # Delete specified rate limiters and hpa during upgrade
        if replicas == 0:
            delete_hpa(client)
            delete_rate_limiters(client)


def stop_platform(config: UpgradeConfig) -> None:
    """Stop Platform by stopping all Platform's pods."""
    _patch_platform(config=config, replicas=0)


def restore_platform(config: UpgradeConfig) -> None:
    """Restore Platform by starting all Platform's pods."""
    _patch_platform(config=config, replicas=1)


def get_ordered_deployments(apps_api: kubernetes.client.AppsV1Api) -> list[kubernetes.client.V1Deployment]:
    """Get list of deployments in special order, those at the beginning should be scaled first"""

    deployments_list = apps_api.list_namespaced_deployment(PLATFORM_NAMESPACE)

    special_deployments = []
    other_deployments = []

    for deployment in deployments_list.items:
        if deployment.metadata.name in SPECIAL_DEPLOYMENTS_NAMES:
            special_deployments.append(deployment)
        else:
            other_deployments.append(deployment)

    return special_deployments + other_deployments


def delete_hpa(api_client: kubernetes.client.ApiClient) -> None:
    """Delete horizontal pod autoscalers during upgrade"""
    autoscaling_api = kubernetes.client.AutoscalingV2Api(api_client)

    hpa_list: list[kubernetes.client.V2HorizontalPodAutoscaler] = (
        autoscaling_api.list_namespaced_horizontal_pod_autoscaler(namespace=PLATFORM_NAMESPACE).items
    )

    if hpa_list:
        for hpa in hpa_list:
            hpa_name = hpa.metadata.name
            try:
                # Delete horizontal pod autoscalers before upgrade
                autoscaling_api.delete_namespaced_horizontal_pod_autoscaler(
                    name=hpa.metadata.name, namespace=hpa.metadata.namespace
                )
                logger.debug(f"Horizontal pod autoscaler: '{hpa_name}' removed")
            except kubernetes.client.exceptions.ApiException as ex:
                if ex.status == 404:
                    logger.info(f"Horizontal pod autoscaler: '{hpa_name}' not found — skipping")
                    continue
                logger.error(f"Error occurred while removing horizontal pod autoscaler '{hpa_name}': \n{ex}")
                raise


def delete_rate_limiters(api_client: kubernetes.client.ApiClient) -> None:
    """Disable envoy filter rate limiter for component during upgrade"""
    custom_api = kubernetes.client.CustomObjectsApi(api_client)

    group = "networking.istio.io"
    version = "v1alpha3"
    plural = "envoyfilters"

    for envoy_filter_name in (
        "impt-seaweed-fs-rate-limiter",
        "control-plane-account-service-rate-limiter",
        "impt-account-service-rate-limiter",
    ):
        try:
            custom_api.delete_namespaced_custom_object(
                group=group, version=version, namespace=PLATFORM_NAMESPACE, plural=plural, name=envoy_filter_name
            )
            logger.debug(f"Envoy filter: '{envoy_filter_name}' removed")
        except kubernetes.client.exceptions.ApiException as ex:
            if ex.status == 404:
                logger.info(f"Envoy filter: '{envoy_filter_name}' not found — skipping")
                continue
            logger.error(f"Error occurred while removing envoy filter '{envoy_filter_name}': \n{ex}")
            raise


def remove_redundant_platform_pods(config: UpgradeConfig):  # noqa: ANN201
    """Remove redundant platform pods"""

    KubernetesConfigHandler(kube_config=config.kube_config.value)

    with kubernetes.client.ApiClient() as client:
        core_api = kubernetes.client.CoreV1Api(client)
        pods_list = core_api.list_pod_for_all_namespaces()
        pods: list[kubernetes.client.V1Pod] = pods_list.items

        for pod in pods:
            # as after 'stop_platform', daemonsets are still running
            if pod.status.phase != "Running":
                pod_metadata: kubernetes.client.V1ObjectMeta = pod.metadata
                try:
                    core_api.delete_namespaced_pod(name=pod_metadata.name, namespace=pod_metadata.namespace)
                except kubernetes.client.exceptions.ApiException:
                    pass


def remove_platform_workloads_tasks(config: UpgradeConfig):  # noqa: ANN201,C901,PLR0915
    """Cancel running platform workloads"""

    group = "impt.intel.com"
    version = "v1"

    removed_tasks = []

    KubernetesConfigHandler(kube_config=config.kube_config.value)

    patch_finalizer: dict = {
        "metadata": {
            "finalizers": [],
        }
    }

    with kubernetes.client.ApiClient() as client:
        custom_api = kubernetes.client.CustomObjectsApi(client)

        def remove_tasks(task_type: str, tasks: list):
            for task in tasks:
                task_name = task["metadata"]["name"]
                # save task name for future check
                removed_tasks.append(task_name)
                try:
                    # remove finalizer from task
                    custom_api.patch_namespaced_custom_object(
                        body=patch_finalizer,
                        name=task_name,
                        namespace=PLATFORM_NAMESPACE,
                        group=group,
                        plural=task_type,
                        version=version,
                    )
                    # remove task
                    custom_api.delete_namespaced_custom_object(
                        name=task_name,
                        namespace=PLATFORM_NAMESPACE,
                        group=group,
                        plural=task_type,
                        version=version,
                    )
                    logger.info(f"{task_type}/{task_name} removed.")
                except kubernetes.client.exceptions.ApiException:
                    pass

        # Cancel training tasks
        try:
            training_tasks_list = custom_api.list_namespaced_custom_object(
                group=group, namespace=PLATFORM_NAMESPACE, plural="trainingtasks", version=version
            )
            remove_tasks("trainingtasks", training_tasks_list.get("items", []))
        except kubernetes.client.exceptions.ApiException as ex:
            if ex.status == 404:
                logger.info("Training tasks resources not found — skipping")
            else:
                logger.error(f"Error occurred while listing training tasks: \n{ex}")
                raise

        # Cancel inference job tasks
        try:
            inference_job_tasks_list = custom_api.list_namespaced_custom_object(
                group=group, namespace=PLATFORM_NAMESPACE, plural="inferencejobtasks", version=version
            )
            remove_tasks("inferencejobtasks", inference_job_tasks_list.get("items", []))
        except kubernetes.client.exceptions.ApiException as ex:
            if ex.status == 404:
                logger.info("Inference job tasks resources not found — skipping")
            else:
                logger.error(f"Error occurred while listing inference job tasks: \n{ex}")
                raise

        # Remove inference server tasks
        try:
            inference_server_tasks_list = custom_api.list_namespaced_custom_object(
                group=group, namespace=PLATFORM_NAMESPACE, plural="inferenceservertasks", version=version
            )
            remove_tasks("inferenceservertasks", inference_server_tasks_list.get("items", []))
        except kubernetes.client.exceptions.ApiException as ex:
            if ex.status == 404:
                logger.info("Inference server tasks resources not found — skipping")
            else:
                logger.error(f"Error occurred while listing inference server tasks: \n{ex}")
                raise

        if removed_tasks:
            # Wait for platform workloads to stop running
            core_api = kubernetes.client.CoreV1Api(client)

            @retry(
                retry=retry_if_exception_type(PodStillPresent),
                stop=stop_after_attempt(STOP_AFTER_ATTEMPT),
                wait=wait_fixed(WAIT_FIXED),
                reraise=True,
            )
            def are_pods_present():
                pods = core_api.list_namespaced_pod(namespace=PLATFORM_NAMESPACE).items
                pods_names = [pod.metadata.name for pod in pods]
                for task in removed_tasks:
                    for pod_name in pods_names:
                        if task in pod_name:
                            raise PodStillPresent(f"Pod for training: {task} could not be deleted.")

            try:
                are_pods_present()
            except PodStillPresent as err:
                logger.exception(err)
                raise
