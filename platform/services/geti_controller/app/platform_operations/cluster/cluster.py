import os
import logging

from kubernetes import client, config
from kubernetes.client import (
    RbacV1Subject,
    V1ClusterRole,
    V1ClusterRoleBinding,
    V1Container,
    V1EnvVar,
    V1EnvVarSource,
    V1Job,
    V1JobSpec,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1PolicyRule,
    V1RoleRef,
    V1SecretKeySelector,
    V1ServiceAccount,
)
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_kube_config() -> None:
    """Load Kubernetes configuration to avoid importing kubernetes lib to other modules"""
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes configuration.")
    except config.ConfigException as e:
        logger.error(f"Failed to load in-cluster configuration: {e}")
        raise


def check_namespace_exists(namespace: str) -> bool:
    """Check if a namespace exists."""
    v1 = client.CoreV1Api()
    try:
        v1.read_namespace(name=namespace)
        logger.info(f"Namespace '{namespace}' exists.")
        return True
    except ApiException as e:
        if e.status == 404:
            logger.error(f"Namespace '{namespace}' does not exist.")
            return False
        logger.error(f"An error occurred while checking namespace: {e}")
        return False


def check_config_map_exists(name: str, namespace: str) -> bool:
    """Check if a ConfigMap exists in the specified namespace."""
    v1 = client.CoreV1Api()
    if not check_namespace_exists(namespace):
        logger.error(f"Cannot check ConfigMap '{name}' because namespace '{namespace}' does not exist.")
        return False

    try:
        v1.read_namespaced_config_map(name=name, namespace=namespace)
        logger.info(f"ConfigMap '{name}' exists in the '{namespace}' namespace.")
        return True
    except ApiException as e:
        if e.status == 404:
            logger.error(f"ConfigMap '{name}' does not exist in the '{namespace}' namespace.")
            return False
        logger.error(f"An error occurred: {e}")
        return False


def create_service_account(name: str, namespace: str) -> V1ServiceAccount:
    """Create a ServiceAccount object."""
    return V1ServiceAccount(metadata=V1ObjectMeta(name=name, namespace=namespace))


def create_cluster_role(name: str) -> V1ClusterRole:
    """Create a ClusterRole object."""
    return V1ClusterRole(
        metadata=V1ObjectMeta(name=name),
        rules=[
            V1PolicyRule(api_groups=["helm.cattle.io"], resources=["helmcharts"], verbs=["create", "update"]),
            V1PolicyRule(api_groups=["batch"], resources=["jobs"], verbs=["list", "watch"]),
        ],
    )


def create_cluster_role_binding(name: str, service_account_name: str, namespace: str) -> V1ClusterRoleBinding:
    """Create a ClusterRoleBinding object."""
    return V1ClusterRoleBinding(
        metadata=V1ObjectMeta(name=name),
        role_ref=V1RoleRef(api_group="rbac.authorization.k8s.io", kind="ClusterRole", name=name),
        subjects=[RbacV1Subject(kind="ServiceAccount", name=service_account_name, namespace=namespace)],
    )


def deploy_service_account(service_account: V1ServiceAccount, namespace: str) -> None:
    """Deploy a ServiceAccount to the specified namespace."""
    v1 = client.CoreV1Api()
    try:
        v1.create_namespaced_service_account(namespace=namespace, body=service_account)
        logger.info(
            f"ServiceAccount '{service_account.metadata.name}' deployed successfully in namespace '{namespace}'."
        )
    except ApiException as e:
        logger.error(f"An error occurred: {e}")


def deploy_cluster_role(cluster_role: V1ClusterRole) -> None:
    """Deploy a ClusterRole."""
    rbac_v1 = client.RbacAuthorizationV1Api()
    try:
        rbac_v1.create_cluster_role(body=cluster_role)
        logger.info(f"ClusterRole '{cluster_role.metadata.name}' deployed successfully.")
    except ApiException as e:
        logger.error(f"An error occurred: {e}")


def deploy_cluster_role_binding(cluster_role_binding: V1ClusterRoleBinding) -> None:
    """Deploy a ClusterRoleBinding."""
    rbac_v1 = client.RbacAuthorizationV1Api()
    try:
        rbac_v1.create_cluster_role_binding(body=cluster_role_binding)
        logger.info(f"ClusterRoleBinding '{cluster_role_binding.metadata.name}' deployed successfully.")
    except ApiException as e:
        logger.error(f"An error occurred: {e}")


def create_job(name: str, image: str, registry: str, manifest_version: str) -> V1Job:
    """Create a Job object."""
    http_proxy = os.getenv("HTTP_PROXY")
    https_proxy = os.getenv("HTTPS_PROXY")
    no_proxy = os.getenv("NO_PROXY") or ""
    container = V1Container(
        name=name,
        image=image,
        image_pull_policy="Always",
        command=["python3"],
        args=["job.py"],
        env=[
            V1EnvVar(name="GETI_REGISTRY", value=registry),
            V1EnvVar(name="GETI_MANIFEST_VERSION", value=manifest_version),
            V1EnvVar(name="GETI_INSTALL_MODE", value="install"),
            V1EnvVar(
                name="DATA_FOLDER",
                value_from=V1EnvVarSource(
                    secret_key_ref=V1SecretKeySelector(name="geti-install-data", key="dataFolder", optional=True)
                ),
            ),
            V1EnvVar(
                name="USERNAME",
                value_from=V1EnvVarSource(
                    secret_key_ref=V1SecretKeySelector(name="geti-install-data", key="login", optional=True)
                ),
            ),
            V1EnvVar(
                name="PASSWORD",
                value_from=V1EnvVarSource(
                    secret_key_ref=V1SecretKeySelector(name="geti-install-data", key="password", optional=True)
                ),
            ),
            V1EnvVar(
                name="PASSWORD_HASH",
                value_from=V1EnvVarSource(
                    secret_key_ref=V1SecretKeySelector(name="geti-install-data", key="passwordHash", optional=True)
                ),
            ),
            V1EnvVar(
                name="PROXY_ENABLED",
                value=str(bool(http_proxy or https_proxy)),
            ),
            V1EnvVar(
                name="HTTPS_PROXY",
                value=https_proxy,
            ),
            V1EnvVar(
                name="HTTP_PROXY",
                value=http_proxy,
            ),
            V1EnvVar(
                name="NO_PROXY",
                value=no_proxy,
            ),
            V1EnvVar(
                name="TLS_CERT",
                value_from=V1EnvVarSource(
                    secret_key_ref=V1SecretKeySelector(name="geti-install-data", key="tlsCert", optional=True)
                ),
            ),
            V1EnvVar(
                name="TLS_KEY",
                value_from=V1EnvVarSource(
                    secret_key_ref=V1SecretKeySelector(name="geti-install-data", key="tlsKey", optional=True)
                ),
            ),
        ],
    )

    pod_spec = V1PodSpec(containers=[container], restart_policy="Never", service_account_name=name)

    pod_template = V1PodTemplateSpec(metadata=V1ObjectMeta(labels={"job": name}), spec=pod_spec)

    job_spec = V1JobSpec(template=pod_template, backoff_limit=0)

    return V1Job(api_version="batch/v1", kind="Job", metadata=V1ObjectMeta(name=name), spec=job_spec)


def deploy_job(job: V1Job, namespace: str) -> None:
    """Deploy a Job to the specified namespace."""
    batch_v1 = client.BatchV1Api()
    try:
        batch_v1.create_namespaced_job(namespace=namespace, body=job)
        logger.info(f"Job '{job.metadata.name}' deployed successfully in namespace '{namespace}'.")
    except ApiException as e:
        logger.error(f"An error occurred: {e}")
