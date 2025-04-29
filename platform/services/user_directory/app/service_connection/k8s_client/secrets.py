"""
Functions for kubernetes secrets management
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from kubernetes.client.rest import ApiException

from service_connection.k8s_client.apis import K8S
from users_handler.validation import convert_from_base_64

from config import K8S_CR_NAMESPACE

logger = logging.getLogger(__name__)


def get_secrets(name: str, secrets_list: list[str], namespace: str = K8S_CR_NAMESPACE) -> dict:
    """
    Returns decoded secrets
    :param name: K8s secret name
    :param secrets_list: list of strings with labels. Example: ['password', 'token']
    :param namespace: namespace to take the secrets from
    :return: dict of demanded secrets, if secret does not exist returns None.
    Example {'password':'intel123', 'token': None}
    """
    if not namespace:
        raise ValueError("Missing namespace value for `get_secrets`")

    k8s_api = K8S.get_k8s_api()
    ret: dict[str, str] = {}
    try:
        secrets = k8s_api.read_namespaced_secret(namespace=namespace, name=name)
    except ApiException as ex:
        logger.info(f"Could not found secret: {name}: {ex}")
        return ret
    for secret in secrets_list:
        if secret in secrets.data:
            ret[secret] = convert_from_base_64(secrets.data[secret])
        else:
            logger.error(f"Key: {secret} does not exist in secrets.data {name}")
    return ret
