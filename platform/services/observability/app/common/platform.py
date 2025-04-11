# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Platform management utilities.
"""

from datetime import datetime

from kubernetes.client.rest import ApiException
from service_connection.k8s_client.apis import K8S

from config import IMPT_CONFIGURATION_CM, K8S_CR_NAMESPACE


def get_installation_datetime() -> datetime:
    """Returns platform installation timestamp."""
    k8s_api = K8S.get_k8s_api()
    try:
        config_map = k8s_api.read_namespaced_config_map(name=IMPT_CONFIGURATION_CM, namespace=K8S_CR_NAMESPACE)
    except ApiException as err:
        raise OSError("Failed to retrieve the platform installation date.") from err

    return config_map.metadata.creation_timestamp
