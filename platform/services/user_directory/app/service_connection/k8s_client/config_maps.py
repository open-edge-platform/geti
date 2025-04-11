"""
Functions for kubernetes config maps management
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from kubernetes.client.rest import ApiException

from service_connection.k8s_client.apis import K8S

from config import K8S_CR_NAMESPACE

logger = logging.getLogger(__name__)


def get_config_map(name: str, field_list: list[str] | None = None) -> dict:
    """
    Returns fields from config map
    :param name: K8s config map name
    :param field_list: list of strings with labels. Example: ['password', 'token']
    :return: dict of demanded fields, if field does not exist returns None.
    Example {'password':'intel123', 'token': None}
    :raise: ApiException when config map is not found
    """
    k8s_api = K8S.get_k8s_api()
    ret: dict[str, str] = {}
    try:
        config_map = k8s_api.read_namespaced_config_map(namespace=K8S_CR_NAMESPACE, name=name)
    except ApiException as ex:
        logger.info(f"Could not found configmap: {name}: {ex}")
        return ret

    # return whole cm when field_list is empty
    if field_list is None:
        return config_map.data

    for field in field_list:
        if field in config_map.data:
            ret[field] = config_map.data[field]
        else:
            logger.error(f"Key: {field} does not exist in config_map.data {name}")
    return ret


def update_config_map(name: str, data: dict[str, str]):  # noqa: ANN201
    """
    Update configmap defined by name with parameters from data
    :param name: name of config map to update
    :param data: fields of config map which will be updated
    """
    k8s_api = K8S.get_k8s_api()
    body = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {"name": name, "namespace": K8S_CR_NAMESPACE},
        "data": data,
    }
    return k8s_api.patch_namespaced_config_map(name=name, namespace=K8S_CR_NAMESPACE, body=body)
