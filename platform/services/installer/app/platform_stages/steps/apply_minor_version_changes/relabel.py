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
import logging
from dataclasses import dataclass

import kubernetes

from constants.paths import K3S_KUBECONFIG_PATH
from constants.platform import PLATFORM_NAMESPACE
from platform_stages.steps.errors import LabelError
from platform_utils.kube_config_handler import KubernetesConfigHandler

logger = logging.getLogger(__name__)


@dataclass
class Object_k8s:
    name: str
    namespace: str
    release_name: str
    release_namespace: str = PLATFORM_NAMESPACE
    group: str = ""
    plural: str = ""
    version: str = ""


SECRETS_TO_PATCH = [
    Object_k8s(name="regcred", namespace="flyte", release_name="internal-registry"),
    Object_k8s(name="regcred", namespace="impt-jobs-production", release_name="internal-registry"),
    Object_k8s(name="impt-kafka-jaas-flyte", namespace="impt-jobs-production", release_name="impt"),
    Object_k8s(name="impt-mongodb", namespace="impt-jobs-production", release_name="impt"),
    Object_k8s(name="impt-spice-db", namespace="impt-jobs-production", release_name="impt"),
    Object_k8s(name="impt-seaweed-fs", namespace="impt-jobs-production", release_name="seaweed-fs"),
]

SERVICEACCOUNTS_TO_PATCH = [
    Object_k8s(name="opa", namespace="opa-istio", release_name="opa", release_namespace="opa-istio"),
]

CONFIGMAPS_TO_PATCH = [
    Object_k8s(name="inject-policy", namespace="opa-istio", release_name="opa", release_namespace="opa-istio"),
]

SERVICES_TO_PATCH = [
    Object_k8s(name="admission-controller", namespace="opa-istio", release_name="opa", release_namespace="opa-istio"),
]

DEPLOYMENTS_TO_PATCH = [
    Object_k8s(name="admission-controller", namespace="opa-istio", release_name="opa", release_namespace="opa-istio"),
]

MUTATING_WEBHOOK_CONFIGURATIONS_TO_PATCH = [
    Object_k8s(name="opa-istio-admission-controller", release_name="opa", release_namespace="opa-istio", namespace=""),
]

CUSTOM_OBJECTS_TO_PATCH = [
    Object_k8s(
        name="opa-tls-certificate",
        namespace="opa-istio",
        release_name="opa",
        release_namespace="opa-istio",
        group="cert-manager.io",
        plural="certificates",
        version="v1",
    ),
    Object_k8s(
        name="ext-authz",
        namespace="istio-system",
        release_name="opa",
        release_namespace="opa-istio",
        group="networking.istio.io",
        plural="envoyfilters",
        version="v1alpha3",
    ),
]


def add_helm_label() -> None:
    """
    Add Helm labels and annotations to target secrets, service accounts,
    config maps, services, deployments, and other Kubernetes objects.
    """

    patch = {
        "labels": {"app.kubernetes.io/managed-by": "Helm"},
        "annotations": {},
    }

    resources_to_patch = {
        "secret": SECRETS_TO_PATCH,
        "service_account": SERVICEACCOUNTS_TO_PATCH,
        "config_map": CONFIGMAPS_TO_PATCH,
        "service": SERVICES_TO_PATCH,
        "deployment": DEPLOYMENTS_TO_PATCH,
        "mutating_webhook_configuration": MUTATING_WEBHOOK_CONFIGURATIONS_TO_PATCH,
    }

    # Iterate over each resource type
    for object_type, resource_list in resources_to_patch.items():
        for resource in resource_list:
            patch["annotations"]["meta.helm.sh/release-name"] = resource.release_name
            patch["annotations"]["meta.helm.sh/release-namespace"] = resource.release_namespace
            _label_k8s_object(resource.namespace, resource.name, patch, object_type=object_type)

    # Handle custom objects (not part of standard Kubernetes types)
    for custom_obj in CUSTOM_OBJECTS_TO_PATCH:
        patch["annotations"]["meta.helm.sh/release-name"] = custom_obj.release_name
        patch["annotations"]["meta.helm.sh/release-namespace"] = custom_obj.release_namespace
        _label_custom_k8s_object(
            custom_obj.namespace,
            custom_obj.name,
            patch,
            group=custom_obj.group,
            plural=custom_obj.plural,
            version=custom_obj.version,
        )


def _label_k8s_object(namespace: str, object_name: str, metadata: dict, object_type: str) -> None:
    logger.info(f"Relabeling {object_type}/{object_name}.")
    KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)

    with kubernetes.client.ApiClient() as api_client:
        try:
            if object_type in ("secret", "service_account", "config_map", "service"):
                core_api = kubernetes.client.CoreV1Api(api_client)
                k8s_object = getattr(core_api, f"read_namespaced_{object_type}")(object_name, namespace)
                patch_function = getattr(core_api, f"patch_namespaced_{object_type}")
            elif object_type in ("deployment",):
                apps_api = kubernetes.client.AppsV1Api(api_client)
                k8s_object = getattr(apps_api, f"read_namespaced_{object_type}")(object_name, namespace)
                patch_function = getattr(apps_api, f"patch_namespaced_{object_type}")
            elif object_type in ("mutating_webhook_configuration",):
                admission_registration_api = kubernetes.client.AdmissionregistrationV1Api(api_client)
                k8s_object = getattr(admission_registration_api, f"read_{object_type}")(object_name)
                patch_function = getattr(admission_registration_api, f"patch_{object_type}")
            else:
                raise LabelError(f"Not supported object_type: {object_type}")

            if k8s_object.metadata.labels is None:
                k8s_object.metadata.labels = {}
            k8s_object.metadata.labels.update(metadata["labels"])

            if k8s_object.metadata.annotations is None:
                k8s_object.metadata.annotations = {}
            k8s_object.metadata.annotations.update(metadata["annotations"])
            if namespace:
                patch_function(object_name, namespace, k8s_object)
            else:
                patch_function(object_name, k8s_object)
        except kubernetes.client.exceptions.ApiException as ex:
            if ex.status == 404:
                pass
            else:
                raise LabelError from ex
    logger.info(f"Object {object_type}/{object_name} relabeled.")


def _label_custom_k8s_object(
    namespace: str, object_name: str, metadata: dict, group: str, plural: str, version: str
) -> None:
    logger.info(f"Relabeling custom_object/{object_name}.")
    KubernetesConfigHandler(kube_config=K3S_KUBECONFIG_PATH)

    with kubernetes.client.ApiClient() as api_client:
        try:
            custom_api = kubernetes.client.CustomObjectsApi(api_client)
            k8s_object = custom_api.get_namespaced_custom_object(
                group=group, plural=plural, version=version, name=object_name, namespace=namespace
            )

            if k8s_object["metadata"].get("labels") is None:
                k8s_object["metadata"]["labels"] = {}
            k8s_object["metadata"]["labels"].update(metadata["labels"])

            if k8s_object["metadata"].get("annotations") is None:
                k8s_object["metadata"]["annotations"] = {}
            k8s_object["metadata"]["annotations"].update(metadata["annotations"])

            custom_api.patch_namespaced_custom_object(
                group=group, plural=plural, version=version, name=object_name, namespace=namespace, body=k8s_object
            )
        except kubernetes.client.exceptions.ApiException as ex:
            if ex.status == 404:
                pass
            else:
                raise LabelError from ex
    logger.info(f"Object custom_object/{object_name} relabeled.")
