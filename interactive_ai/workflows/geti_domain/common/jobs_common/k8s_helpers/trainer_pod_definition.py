# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""Functions to create trainer pod definition."""

import json
import logging
import os

from flytekit import ContainerTask, PodTemplate, current_context
from kubernetes.client import V1Capabilities, V1PodSpec, V1SecurityContext
from kubernetes.client.models import (
    V1ConfigMapEnvSource,
    V1ConfigMapKeySelector,
    V1Container,
    V1ContainerPort,
    V1EmptyDirVolumeSource,
    V1EnvFromSource,
    V1EnvVar,
    V1EnvVarSource,
    V1LocalObjectReference,
    V1ResourceRequirements,
    V1SecretKeySelector,
    V1Volume,
    V1VolumeMount,
)

from jobs_common.k8s_helpers.k8s_resources_calculation import ComputeResources, EphemeralStorageResources
from jobs_common.k8s_helpers.trainer_image_info import TrainerImageInfo
from jobs_common.tasks.utils.secrets import SECRETS

__all__ = ["create_flyte_container_task"]

from geti_types import Session

logger = logging.getLogger(__name__)


PRIMARY_CONTAINER_NAME = "trainer"
SIDECAR_CONTAINER_NAME = "mlflow-sidecar"


def _create_sidecar_env(
    organization_id: str,
    workspace_id: str,
    project_id: str,
    job_id: str,
    namespace: str,
    role: str = "training_operator",
) -> list[V1EnvVar]:
    identifier_json = json.dumps(
        {
            "organization_id": organization_id,
            "workspace_id": workspace_id,
            "project_id": project_id,
            "job_id": job_id,
        }
    )

    # NOTE: vars below is inherited by the Flyte task who renders this sidecar
    var_s3_host = V1EnvVar(
        name="S3_HOST",
        value=os.environ.get("S3_HOST", ""),
    )
    var_s3_credentials_provider = V1EnvVar(
        name="S3_CREDENTIALS_PROVIDER",
        value=os.environ.get("S3_CREDENTIALS_PROVIDER", "local"),
    )

    return [
        # Identifier JSON
        V1EnvVar(name="IDENTIFIER_JSON", value=identifier_json),
        # Database related env vars
        V1EnvVar(
            name="DATABASE_USERNAME",
            value_from=V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name=f"{namespace}-mongodb",
                    key="jobs-mongodb-username",
                    optional=True,
                )
            ),
        ),
        V1EnvVar(
            name="DATABASE_PASSWORD",
            value_from=V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name=f"{namespace}-mongodb",
                    key="jobs-mongodb-password",
                    optional=True,
                )
            ),
        ),
        # Object storage related env vars
        V1EnvVar(
            name="S3_SECRET_KEY",
            value_from=V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name=f"{namespace}-seaweed-fs",
                    key=f"{role}_secret_key",
                    optional=True,
                )
            ),
        ),
        V1EnvVar(
            name="S3_ACCESS_KEY",
            value_from=V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name=f"{namespace}-seaweed-fs",
                    key=f"{role}_access_key",
                    optional=True,
                )
            ),
        ),
        V1EnvVar(
            name="S3_PRESIGNED_URL_SECRET_KEY",
            value_from=V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name=f"{namespace}-seaweed-fs",
                    key=f"{role}_s3_presigned_url_secret_key",
                    optional=True,
                )
            ),
        ),
        V1EnvVar(
            name="S3_PRESIGNED_URL_ACCESS_KEY",
            value_from=V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name=f"{namespace}-seaweed-fs",
                    key=f"{role}_s3_presigned_url_access_key",
                    optional=True,
                )
            ),
        ),
        var_s3_host,
        var_s3_credentials_provider,
    ]


def create_flyte_container_task(  # noqa: PLR0913
    session: Session,
    project_id: str,
    job_id: str,
    compute_resources: ComputeResources,
    ephemeral_storage_resources: EphemeralStorageResources,
    trainer_image_info: TrainerImageInfo,
    command: list[str],
    container_name: str,
    namespace: str = "impt",
) -> ContainerTask:
    """Create Flyte `ContainerTask` for an arbitrary model trainer.

    :param session: Current session
    :param project_id: Project ID
    :param job_id: Job ID granted by JOB MS
    :param compute_resources: Dataclass for k8s compute resource requests/limits
    :param ephemeral_storage_resources: Dataclass for ephemeral storage requests/limits
    :param trainer_image_info: Dataclass for trainer image selection
    :param command: Bash command executed by the rendered primary container (trainer)
    :param container_name: Container name
    :param namespace: K8s namespace where config maps are retrieved from
    """
    primary_container_image = trainer_image_info.to_primary_image_full_name()
    logger.info(f"Create primary_container_image={primary_container_image}")

    sidecar_container_image = trainer_image_info.to_sidecar_image_full_name()
    logger.info(f"Create sidecar_container_image={sidecar_container_image}")

    env_from = [
        V1EnvFromSource(config_map_ref=V1ConfigMapEnvSource(name=f"{namespace}-feature-flags")),
        V1EnvFromSource(config_map_ref=V1ConfigMapEnvSource(name=f"{namespace}-s3-bucket-names")),
    ]
    sidecar_env = _create_sidecar_env(
        organization_id=str(session.organization_id),
        workspace_id=str(session.workspace_id),
        project_id=project_id,
        job_id=job_id,
        namespace=namespace,
    )

    primary_resources = V1ResourceRequirements(
        requests={
            **compute_resources.to_kwargs(is_requests=True),
            "ephemeral-storage": str(ephemeral_storage_resources.requests),
        },
        limits={
            **compute_resources.to_kwargs(is_requests=False),
            "ephemeral-storage": str(ephemeral_storage_resources.limits),
        },
    )

    secondary_resources = V1ResourceRequirements(
        requests={"cpu": "500m", "memory": "1Gi"},
        limits={"cpu": "1", "memory": "3Gi"},
    )

    logger.info(f"Create primary_resources={primary_resources}")

    accelerator_name = compute_resources.accelerator_name
    # We do not have any RuntimeClass for Intel GPU
    runtime_class_name = "nvidia" if accelerator_name == "nvidia.com/gpu" else None
    logger.info(f"Create runtime_class_name={runtime_class_name}")

    security_context = None
    if trainer_image_info.render_gid != 0:
        security_context = V1SecurityContext(
            run_as_group=trainer_image_info.render_gid,
            allow_privilege_escalation=False,
            read_only_root_filesystem=False,
            run_as_non_root=True,
            run_as_user=10001,
            capabilities=V1Capabilities(drop=["ALL"]),
        )
    role = "flyte_workflows"

    pod_spec = V1PodSpec(
        containers=[
            V1Container(
                name=PRIMARY_CONTAINER_NAME,
                image=primary_container_image,
                env=[
                    V1EnvVar(name="SHARD_FILES_DIR", value="/shard_files"),
                    V1EnvVar(name="MLFLOW_TRACKING_URI", value="http://localhost:5000"),
                    V1EnvVar(name="MLFLOW_EXPERIMENT_ID", value=project_id),
                    V1EnvVar(name="MLFLOW_RUN_ID", value=job_id),
                    V1EnvVar(name="MLFLOW_ENABLE_ASYNC_LOGGING", value="1"),
                    V1EnvVar(name="MODEL_TEMPLATES_DIR", value="/model_templates"),
                    V1EnvVar(name="LOGGING_CONFIG_DIR", value="/mnt/logging_config"),
                    V1EnvVar(name="EXECUTION_ID", value=current_context().execution_id.name),
                    V1EnvVar(name="TASK_ID", value=container_name),
                    V1EnvVar(name="SESSION_ORGANIZATION_ID", value=str(session.organization_id)),
                    V1EnvVar(name="SESSION_WORKSPACE_ID", value=str(session.workspace_id)),
                    V1EnvVar(name="WEIGHTS_URL", value="https://storage.geti.infra-host.com"),
                    V1EnvVar(
                        name="KAFKA_TOPIC_PREFIX",
                        value_from=V1EnvVarSource(
                            config_map_key_ref=V1ConfigMapKeySelector(
                                name="impt-configuration", key="kafka_topic_prefix"
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="KAFKA_USERNAME",
                        value_from=V1EnvVarSource(
                            secret_key_ref=V1SecretKeySelector(name=f"{namespace}-kafka-jaas-flyte", key="user")
                        ),
                    ),
                    V1EnvVar(
                        name="KAFKA_PASSWORD",
                        value_from=V1EnvVarSource(
                            secret_key_ref=V1SecretKeySelector(name=f"{namespace}-kafka-jaas-flyte", key="password")
                        ),
                    ),
                    V1EnvVar(name="MODEL_CACHE_DIR", value="/home/non-root/.cache/torch/hub/checkpoints"),
                    # Object storage related env vars
                    V1EnvVar(
                        name="S3_SECRET_KEY",
                        value_from=V1EnvVarSource(
                            secret_key_ref=V1SecretKeySelector(
                                name=f"{namespace}-seaweed-fs",
                                key=f"{role}_secret_key",
                                optional=True,
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="S3_ACCESS_KEY",
                        value_from=V1EnvVarSource(
                            secret_key_ref=V1SecretKeySelector(
                                name=f"{namespace}-seaweed-fs",
                                key=f"{role}_access_key",
                                optional=True,
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="S3_PRESIGNED_URL_SECRET_KEY",
                        value_from=V1EnvVarSource(
                            secret_key_ref=V1SecretKeySelector(
                                name=f"{namespace}-seaweed-fs",
                                key=f"{role}_s3_presigned_url_secret_key",
                                optional=True,
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="S3_PRESIGNED_URL_ACCESS_KEY",
                        value_from=V1EnvVarSource(
                            secret_key_ref=V1SecretKeySelector(
                                name=f"{namespace}-seaweed-fs",
                                key=f"{role}_s3_presigned_url_access_key",
                                optional=True,
                            )
                        ),
                    ),
                    V1EnvVar(
                        name="S3_HOST",
                        value=os.environ.get("S3_HOST", ""),
                    ),
                    V1EnvVar(
                        name="S3_CREDENTIALS_PROVIDER",
                        value=os.environ.get("S3_CREDENTIALS_PROVIDER", ""),
                    ),
                ],
                resources=primary_resources,
                env_from=env_from,
                volume_mounts=[
                    V1VolumeMount(mount_path="/dev/shm", name="shared-memory"),  # noqa : S108 # nosec: B108
                    V1VolumeMount(mount_path="/shard_files", name="shard-files-dir"),
                ],
                security_context=security_context,
            )
        ],
        init_containers=[
            V1Container(
                command=["run"],
                name=SIDECAR_CONTAINER_NAME,
                image=sidecar_container_image,
                ports=[V1ContainerPort(container_port=5000, name="mlflow-port", protocol="TCP")],
                env=sidecar_env,
                env_from=env_from,
                volume_mounts=[
                    V1VolumeMount(mount_path="/shard_files", name="shard-files-dir"),
                ],
                resources=secondary_resources,
                # restart_policy="Always" means that it is a native sidecar container.
                # See https://kubernetes.io/blog/2023/08/25/native-sidecar-containers/
                restart_policy="Always",
            ),
        ],
        runtime_class_name=runtime_class_name,
        image_pull_secrets=[V1LocalObjectReference(name="regcred")],
        volumes=[
            V1Volume(
                name="shared-memory",
                empty_dir=V1EmptyDirVolumeSource(medium="Memory"),
            ),
            V1Volume(
                name="shard-files-dir",
                empty_dir=V1EmptyDirVolumeSource(size_limit=str(ephemeral_storage_resources.work_dir_size_limit)),
            ),
        ],
    )
    logger.info(f"Create pod_spec={pod_spec}")

    return ContainerTask(
        name=container_name,
        image=primary_container_image,
        command=command,
        pod_template=PodTemplate(
            pod_spec=pod_spec,
            primary_container_name=PRIMARY_CONTAINER_NAME,
            annotations={
                "proxy.istio.io/config": '{ "holdApplicationUntilProxyStarts": true }',
                "karpenter.sh/do-not-disrupt": "true",
            },
        ),
        secret_requests=SECRETS,
    )
