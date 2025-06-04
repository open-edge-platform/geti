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
from pathlib import Path

from kubernetes import client
from kubernetes.client.rest import ApiException

from constants.paths import K3S_KUBECONFIG_PATH, PLATFORM_CRDS_PATHS, SIDECAR_ISTIO_CRDS_PATHS
from constants.platform import PLATFORM_NAMESPACE
from platform_stages.steps.errors import CRDPatchingError
from platform_utils.kube_config_handler import KubernetesConfigHandler

logger = logging.getLogger(__name__)

helm_labels = {"app.kubernetes.io/managed-by": "Helm"}
helm_annotations = {"meta.helm.sh/release-namespace": PLATFORM_NAMESPACE, "meta.helm.sh/release-name": "default"}

CRDS_GROUP_NAMES: tuple[str, ...] = (
    "cert-manager.io",
    "flyte.lyft.com",
    "serving.kserve.io",
    "istio.io",
)

GROUP_TO_CHART = dict(zip(CRDS_GROUP_NAMES, PLATFORM_CRDS_PATHS + SIDECAR_ISTIO_CRDS_PATHS))


def _get_release_name(group: str) -> str:
    """
    Get the Helm release name for a given CRD group.

    This function maps a CRD group to its corresponding chart path and returns the Helm release name.
    """
    for group_suffix, chart_path in GROUP_TO_CHART.items():
        if group.endswith(group_suffix):
            # Special case for modelmesh-serving crds
            if group_suffix == "serving.kserve.io":
                return "modelmesh-serving-crds"
            return Path(chart_path).name

    raise ValueError(f"Unexpected CRD group: {group}. This group is not in the predefined CRDS_GROUP_NAMES.")


def _get_crd_by_group_names(
    group_names: tuple[str, ...],
    kube_config: str = K3S_KUBECONFIG_PATH,
) -> list[client.V1CustomResourceDefinition]:
    """
    Retrieve CRDs by their group names.
    """
    KubernetesConfigHandler(kube_config=kube_config)

    with client.ApiClient() as api_client:
        extension_api = client.ApiextensionsV1Api(api_client)
        try:
            crds = extension_api.list_custom_resource_definition()
            filtered_crds = [
                crd for crd in crds.items if any(crd.spec.group.endswith(group_name) for group_name in group_names)
            ]
            logger.info(f"Successfully retrieved {len(filtered_crds)} CRDs for group names: {group_names}")
            return filtered_crds
        except ApiException as api_err:
            logger.error(f"Failed to list custom resource definitions: {api_err}")
            raise


def _update_crds_with_helm_metadata(
    crds: list[client.V1CustomResourceDefinition], kube_config: str = K3S_KUBECONFIG_PATH
) -> None:
    """
    Updates CRDs with Helm metadata.
    """
    KubernetesConfigHandler(kube_config=kube_config)

    with client.ApiClient() as api_client:
        extension_api = client.ApiextensionsV1Api(api_client)
        body = {"metadata": {"labels": helm_labels, "annotations": helm_annotations}}

        logger.info("Starting to patch CRDs with Helm metadata.")
        for crd in crds:
            name = crd.metadata.name
            group = crd.spec.group

            try:
                release_name = _get_release_name(group=group)
                body["metadata"]["annotations"]["meta.helm.sh/release-name"] = release_name

                extension_api.patch_custom_resource_definition(name=name, body=body)
                logger.debug(f"Successfully patched CRD '{name}' with Helm metadata.")
            except ApiException as api_err:
                logger.error(f"Failed to patch custom resource definition {name}: {api_err}")
                raise
            except ValueError as val_err:
                logger.error(f"Failed to get release name for CRD '{name}': {val_err}")
                raise
        logger.info("Finished patching all CRDs with Helm metadata.")


def apply_helm_metadata_to_crds(kube_config: str = K3S_KUBECONFIG_PATH) -> None:
    """
    Patches CRDs with Helm labels and annotations.
    """
    try:
        crds = _get_crd_by_group_names(CRDS_GROUP_NAMES, kube_config=kube_config)
        _update_crds_with_helm_metadata(crds, kube_config=kube_config)
    except ApiException as api_err:
        raise CRDPatchingError from api_err
    except ValueError as val_err:
        raise CRDPatchingError from val_err
