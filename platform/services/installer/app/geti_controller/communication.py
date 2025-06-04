# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import subprocess
import time
from http import HTTPStatus

import requests

from platform_configuration.versions import get_target_platform_version


class GetiControllerCommunicationError(Exception):
    """Custom exception for errors in Geti Controller communication."""


def call_install_endpoint(kube_config: str) -> dict:
    """
    Calls the POST /api/v1/platform/install endpoint of the Geti Controller service
    with port-forwarding.

    Raises:
        GetiControllerCommunicationError: If the response status code is not 200.
    """
    local_port, service_port = 9200, 9200
    service_name = "geti-controller"
    namespace = "default"

    port_forward_cmd = [
        "kubectl",
        "--kubeconfig",
        kube_config,
        "port-forward",
        f"svc/{service_name}",
        f"{local_port}:{service_port}",
        "--namespace",
        namespace,
    ]
    process = subprocess.Popen(port_forward_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: S603

    try:
        time.sleep(3)  # wait for port-forwarding to establish

        url = f"http://localhost:{local_port}/api/v1/platform/install"
        payload = {"version_number": get_target_platform_version()}
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code != HTTPStatus.OK:
            raise GetiControllerCommunicationError(
                f"Error calling install endpoint: {response.status_code} - {response.text}"
            )
        return response.json()
    except requests.RequestException as e:
        raise GetiControllerCommunicationError(f"Installation request failed: {e}")
    finally:
        process.terminate()
        process.wait()
