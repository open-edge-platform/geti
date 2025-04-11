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

"""This module defines a wrapper for flyte Task decorator that enables multi-container tasks to work"""

import logging
from collections.abc import Callable
from functools import wraps
from time import sleep

import requests
from flytekit import dynamic, task
from flytekitplugins.pod import Pod
from kubernetes.client import V1ConfigMapKeySelector, V1ConfigMapVolumeSource, V1EnvVarSource, V1ObjectFieldSelector
from kubernetes.client.models import (
    V1Capabilities,
    V1ConfigMapEnvSource,
    V1Container,
    V1EmptyDirVolumeSource,
    V1EnvFromSource,
    V1EnvVar,
    V1KeyToPath,
    V1PodSpec,
    V1ResourceRequirements,
    V1SecretVolumeSource,
    V1SecurityContext,
    V1Toleration,
    V1Volume,
    V1VolumeMount,
)

logger = logging.getLogger(__name__)

PRIMARY_CONTAINER_NAME = "flyte-workflow"
BINARY_STORAGE_MOUNT_PATH = "/binary_data"
IE_STORAGE_MOUNT_PATH = "/ie_storage"
LOGGING_VOLUME_NAME = "logging"
LOGGING_MOUNT_PATH = "/mnt/logging_config"
DATA_STORAGE_VOLUME_NAME = "data-storage"
SERVICE_ACCOUNT_NAME = "impt-jobs"
TMP_DIR_VOLUME_NAME = "tmp-dir"
TMP_DIR_MOUNT_PATH = "/tmp"  # noqa: S108 # nosec
AWS_CONFIG_VOLUME_NAME = "aws-client-config"
AWS_CONFIG_MOUNT_PATH = "/home/non-root/.aws"
FLYTE_POD_ANNOTATIONS = {"proxy.istio.io/config": '{ "holdApplicationUntilProxyStarts": true }'}
SPICEDB_TLS_SECRETS_VOLUME_NAME = "tls-secrets"
SPICEDB_TLS_SECRETS_MOUNT_PATH = "/etc/tls-secrets"
TERM_ISTIO_PROXY_URL = "http://127.0.0.1:15020/quitquitquit"


def get_flyte_pod_spec(
    resources: V1ResourceRequirements | None = None,
    node_selector: dict[str, str] | None = None,
    tolerations: list[V1Toleration] | None = None,
) -> V1PodSpec:
    """
    Builds a Flyte pod specification object

    :params resources: Resource requests for Primary container, e.g., cpu, memory, and ephemeral storage.
    """
    return V1PodSpec(
        node_selector=node_selector,
        tolerations=tolerations,
        service_account_name=SERVICE_ACCOUNT_NAME,
        containers=[
            V1Container(
                name=PRIMARY_CONTAINER_NAME,
                resources=resources,
                volume_mounts=[
                    V1VolumeMount(
                        name=DATA_STORAGE_VOLUME_NAME,
                        mount_path=BINARY_STORAGE_MOUNT_PATH,
                        sub_path="binary_data",
                    ),
                    V1VolumeMount(
                        name=DATA_STORAGE_VOLUME_NAME,
                        mount_path=IE_STORAGE_MOUNT_PATH,
                        sub_path="ie_storage",
                    ),
                    V1VolumeMount(
                        name=LOGGING_VOLUME_NAME,
                        read_only=True,
                        mount_path=LOGGING_MOUNT_PATH,
                    ),
                    V1VolumeMount(
                        name=TMP_DIR_VOLUME_NAME,
                        mount_path=TMP_DIR_MOUNT_PATH,
                    ),
                    V1VolumeMount(
                        name=AWS_CONFIG_VOLUME_NAME,
                        mount_path=AWS_CONFIG_MOUNT_PATH,
                    ),
                    V1VolumeMount(
                        name=SPICEDB_TLS_SECRETS_VOLUME_NAME,
                        mount_path=SPICEDB_TLS_SECRETS_MOUNT_PATH,
                    ),
                ],
                env=[
                    V1EnvVar(
                        name="WORKDIR",
                        value=BINARY_STORAGE_MOUNT_PATH,
                    ),
                    V1EnvVar(
                        name="STORAGE_DIR_PATH",
                        value=IE_STORAGE_MOUNT_PATH,
                    ),
                    V1EnvVar(
                        name="OPENTELEMETRY_CONTEXT",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(field_path="metadata.annotations['opentelemetry_context']")
                        ),
                    ),
                    V1EnvVar(
                        name="TASK_NAME",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(field_path="metadata.labels['task-name']")
                        ),
                    ),
                    V1EnvVar(
                        name="REPORT_RESOURCES_CONSUMPTION",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(
                                field_path="metadata.labels['report_resources_consumption']"
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="K8S_POD_NAME",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(
                                field_path="metadata.name",
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="K8S_POD_UID",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(
                                field_path="metadata.uid",
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="OTEL_RESOURCE_ATTRIBUTES",
                        value="service.name=$(TASK_NAME),"
                        "service.instance.id=$(K8S_POD_NAME),"
                        "k8s.pod.uid=$(K8S_POD_UID),"
                        f"k8s.container.name={PRIMARY_CONTAINER_NAME}",
                    ),
                    V1EnvVar(
                        name="SESSION_ORGANIZATION_ID",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(field_path="metadata.annotations['organization_id']")
                        ),
                    ),
                    V1EnvVar(
                        name="SESSION_WORKSPACE_ID",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(field_path="metadata.annotations['workspace_id']")
                        ),
                    ),
                    V1EnvVar(
                        name="JOB_METADATA_ID",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(field_path="metadata.annotations['job_id']")
                        ),
                    ),
                    V1EnvVar(
                        name="JOB_METADATA_TYPE",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(field_path="metadata.annotations['job_type']")
                        ),
                    ),
                    V1EnvVar(
                        name="JOB_METADATA_NAME",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(field_path="metadata.annotations['job_name']")
                        ),
                    ),
                    V1EnvVar(
                        name="JOB_METADATA_AUTHOR",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(field_path="metadata.annotations['job_author']")
                        ),
                    ),
                    V1EnvVar(
                        name="JOB_METADATA_START_TIME",
                        value_from=V1EnvVarSource(
                            field_ref=V1ObjectFieldSelector(field_path="metadata.annotations['job_start_time']")
                        ),
                    ),
                    V1EnvVar(
                        name="MPLCONFIGDIR",
                        value=TMP_DIR_MOUNT_PATH,
                    ),
                    V1EnvVar(
                        name="LOGGING_CONFIG_DIR",
                        value=LOGGING_MOUNT_PATH,
                    ),
                    V1EnvVar(
                        name="KAFKA_TOPIC_PREFIX",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration", key="kafka_topic_prefix"
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="MAX_TRAINING_DATASET_SIZE",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration",
                                key="max_training_dataset_size",
                            )
                        ),
                    ),
                    # dataset ie constants.
                    V1EnvVar(
                        name="MAX_NUMBER_OF_MEDIA_PER_PROJECT",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration",
                                key="max_number_of_media_per_project",
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="MAX_NUMBER_OF_ANNOTATION_VERSIONS_PER_MEDIA",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration",
                                key="max_number_of_annotation_versions_per_media",
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="MAX_NUMBER_OF_DATASET_STORAGES",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration",
                                key="max_number_of_dataset_storages",
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="MAX_NUMBER_OF_PIXELS",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration", key="max_number_of_pixels"
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="MIN_IMAGE_SIZE",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(name="impt-configuration", key="min_image_size")
                        ),
                    ),
                    V1EnvVar(
                        name="MAX_IMAGE_SIZE",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(name="impt-configuration", key="max_image_size")
                        ),
                    ),
                    V1EnvVar(
                        name="MIN_VIDEO_SIZE",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(name="impt-configuration", key="min_video_size")
                        ),
                    ),
                    V1EnvVar(
                        name="MAX_VIDEO_WIDTH",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(name="impt-configuration", key="max_video_width")
                        ),
                    ),
                    V1EnvVar(
                        name="MAX_VIDEO_HEIGHT",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(name="impt-configuration", key="max_video_height")
                        ),
                    ),
                    V1EnvVar(
                        name="MAX_VIDEO_LENGTH",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(name="impt-configuration", key="max_video_length")
                        ),
                    ),
                    V1EnvVar(
                        name="PROJECT_IE_KEY_SOURCE",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration", key="project_ie_key_source"
                            )
                        ),
                    ),
                    # Training job related vars
                    V1EnvVar(
                        name="DEFAULT_TRAINER_VERSION",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-training-config", key="default_trainer_version"
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="DEFAULT_TRAINER_IMAGE_NAME",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-training-config", key="default_trainer_image_name"
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="MLFLOW_SIDECAR_IMAGE_NAME",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-training-config", key="mlflow_sidecar_image_name"
                            )
                        ),
                    ),
                    # For the ease of development
                    V1EnvVar(
                        name="OVERWRITE_RESOURCES_CPU_LIMITS",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration", key="overwrite_resources_cpu_limits", optional=True
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="OVERWRITE_RESOURCES_MEM_LIMITS",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration", key="overwrite_resources_mem_limits", optional=True
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="NUM_MODELS_TO_KEEP_IN_STORAGE",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration", key="num_models_to_keep_in_storage", optional=True
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="SPICEDB_SSL_CERTIFICATES_DIR",
                        value=SPICEDB_TLS_SECRETS_MOUNT_PATH,
                    ),
                ],
                env_from=[
                    V1EnvFromSource(config_map_ref=V1ConfigMapEnvSource(name="impt-feature-flags")),
                ],
                security_context=V1SecurityContext(
                    allow_privilege_escalation=False,
                    read_only_root_filesystem=True,
                    run_as_non_root=True,
                    run_as_user=10001,
                    capabilities=V1Capabilities(drop=["ALL"]),
                ),
            )
        ],
        volumes=[
            V1Volume(
                name=DATA_STORAGE_VOLUME_NAME,
                empty_dir=V1EmptyDirVolumeSource(),
            ),
            V1Volume(
                name=LOGGING_VOLUME_NAME,
                config_map=V1ConfigMapVolumeSource(name="impt-logging-config"),
            ),
            V1Volume(
                name=TMP_DIR_VOLUME_NAME,
                empty_dir=V1EmptyDirVolumeSource(),
            ),
            V1Volume(
                name=AWS_CONFIG_VOLUME_NAME,
                empty_dir=V1EmptyDirVolumeSource(),
            ),
            V1Volume(
                name=SPICEDB_TLS_SECRETS_VOLUME_NAME,
                secret=V1SecretVolumeSource(
                    secret_name="impt-spice-db-tls",  # noqa: S106
                    items=[V1KeyToPath(key="ca.crt", path="ca.crt")],
                ),
            ),
        ],
    )


def _terminate_istio_proxy(n_trials: int = 10, timeout: float = 1.0, sleep_sec: float = 1.0):
    is_terminated = False

    for step in range(1, n_trials + 1):
        try:
            response = requests.post(TERM_ISTIO_PROXY_URL, timeout=timeout)

            if response.status_code == 200:
                is_terminated = True
                break
        except Exception as e:
            logger.warning("[%d/%d] Cannot terminate istio proxy: %s", step, n_trials, e)

        sleep(sleep_sec)

    if not is_terminated:
        logger.error("Cannot terminate istio proxy")


DEFAULT_TASK_CONFIG = Pod(
    pod_spec=get_flyte_pod_spec(),
    primary_container_name=PRIMARY_CONTAINER_NAME,
    annotations=FLYTE_POD_ANNOTATIONS,
)


def flyte_multi_container_task(  # noqa: ANN201
    _function: Callable | None = None,
    task_config: Pod | None = None,
    pod_spec: V1PodSpec | None = None,
    *args,
    **kwargs,
):
    """
    Decorates a Flyte task with proper pod_spec and primary_container name parameters.
    These parameters will allow flyte task to run in multi-container pods.

    :param task_config: Pod definition used in Flyte task.
        If it is `None` (default), use `DEFAULT_TASK_CONFIG`.
        You cannot set this and `pod_spec` to not `None` at the same time.
    :param pod_spec: Pod definition same as `task_config` but it is a component of `flytekitplugins.pod.Pod`.
        If it is not `None`, `flytekitplugins.pod.Pod` will be created with this value and
        default `primary_container_name=PRIMARY_CONTAINER_NAME` and `annotations=FLYTE_POD_ANNOTATIONS`.
        You cannot set this and `task_config` to not `None` at the same time.
    """

    if task_config is not None and pod_spec is not None:
        raise RuntimeError("You cannot define task_config and pod_spec at the same time.")

    if pod_spec is not None:
        task_config = Pod(
            pod_spec=pod_spec,
            primary_container_name=PRIMARY_CONTAINER_NAME,
            annotations=FLYTE_POD_ANNOTATIONS,
        )
    elif task_config is None:
        task_config = DEFAULT_TASK_CONFIG

    def decorator(func: Callable):
        @task(task_config=task_config, *args, **kwargs)
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            finally:
                _terminate_istio_proxy()

        return wrapper

    if _function is not None:
        return decorator(_function)
    return decorator


def flyte_multi_container_dynamic(  # noqa: ANN201
    _function: Callable | None = None,
    task_config: Pod | None = None,
    pod_spec: V1PodSpec | None = None,
    *args,
    **kwargs,
):
    """
    Decorates a Flyte dynamic with proper pod_spec and primary_container name parameters.
    These parameters will allow flyte task to run in multi-container pods.

    :param task_config: Pod definition used in Flyte task.
        If it is `None` (default), use `DEFAULT_TASK_CONFIG`.
        You cannot set this and `pod_spec` to not `None` at the same time.
    :param pod_spec: Pod definition same as `task_config` but it is a component of `flytekitplugins.pod.Pod`.
        If it is not `None`, `flytekitplugins.pod.Pod` will be created with this value and
        default `primary_container_name=PRIMARY_CONTAINER_NAME` and `annotations=FLYTE_POD_ANNOTATIONS`.
        You cannot set this and `task_config` to not `None` at the same time.
    """

    if task_config is not None and pod_spec is not None:
        raise RuntimeError("You cannot define task_config and pod_spec at the same time.")

    if pod_spec is not None:
        task_config = Pod(
            pod_spec=pod_spec,
            primary_container_name=PRIMARY_CONTAINER_NAME,
            annotations=FLYTE_POD_ANNOTATIONS,
        )
    elif task_config is None:
        task_config = DEFAULT_TASK_CONFIG

    def decorator(func: Callable):
        @dynamic(task_config=task_config, *args, **kwargs)
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            finally:
                _terminate_istio_proxy()

        return wrapper

    if _function is not None:
        return decorator(_function)
    return decorator
