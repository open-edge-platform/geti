# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus

import requests

from geti_controller.errors import GetiControllerCommunicationError
from platform_configuration.versions import get_target_platform_version

LOCAL_PORT = 9200
SERVICE_PORT = 9200
SERVICE_NAME = "geti-controller"
NAMESPACE = "default"


class OperationStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ROLLING_BACK = "ROLLING_BACK"
    NOT_RUNNING = "NOT_RUNNING"


@dataclass
class InstallationStatus:
    status: str
    progress: int
    message: str


def establish_port_forwarding(kube_config: str) -> subprocess.Popen:
    """
    Establishes port-forwarding to the Geti Controller service.
    """
    port_forward_cmd = [
        "kubectl",
        "--kubeconfig",
        kube_config,
        "port-forward",
        f"svc/{SERVICE_NAME}",
        f"{LOCAL_PORT}:{SERVICE_PORT}",
        "--namespace",
        NAMESPACE,
    ]
    process = subprocess.Popen(port_forward_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: S603
    time.sleep(3)  # wait for port-forwarding to start
    return process


def call_install_endpoint(kube_config: str) -> dict:
    """
    Calls the POST /api/v1/platform/install endpoint of the Geti Controller service
    with port-forwarding.

    Raises:
        GetiControllerCommunicationError: If the response status code is not 200.
    """
    process = establish_port_forwarding(kube_config)

    try:
        url = f"http://localhost:{LOCAL_PORT}/api/v1/platform/install"
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


def get_installation_status(kube_config: str) -> InstallationStatus:
    """
    Fetch the installation progress and status from the Geti Controller endpoint.

    Returns:
        InstallationStatus: An object containing progress percentage, status, and message.
    """
    process = establish_port_forwarding(kube_config)

    try:
        url = f"http://localhost:{LOCAL_PORT}/api/v1/platform/check_installation_upgrade_progress"
        response = requests.get(url, timeout=10)
        data = response.json()
        return InstallationStatus(
            progress=data.get("progress_percentage", 0),
            status=data.get("status", ""),
            message=data.get("message", ""),
        )
    except requests.RequestException as e:
        raise GetiControllerCommunicationError(f"Failed to fetch installation status: {e}")
    finally:
        process.terminate()
        process.wait()
