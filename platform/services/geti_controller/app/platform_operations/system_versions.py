# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from kubernetes import client, config, stream

logger = logging.getLogger(__name__)


def get_nvidia_driver_version() -> str | None:
    """
    Retrieve the NVIDIA driver version by executing nvidia-smi in the nvidia-device-plugin-daemonset pod.
    """
    try:
        config.load_incluster_config()
        core_v1 = client.CoreV1Api()
        pods = core_v1.list_namespaced_pod(namespace="kube-system", label_selector="name=nvidia-device-plugin-ds")
        if not pods.items:
            logger.warning("No nvidia-device-plugin-daemonset pod found in kube-system namespace.")
            return None
        pod_name = pods.items[0].metadata.name
        exec_command = ["/bin/bash", "-c", "nvidia-smi --query-gpu=driver_version --format=csv,noheader"]
        response = stream.stream(
            core_v1.connect_get_namespaced_pod_exec,
            name=pod_name,
            namespace="kube-system",
            command=exec_command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        logger.debug(f"NVIDIA driver version: {response}")
        return response.strip()
    except Exception as e:
        logger.warning(f"Failed to retrieve NVIDIA driver version: {e}")
        return None


def get_system_versions() -> dict:
    """
    Retrieve the versions of k3s, NVIDIA drivers, and Intel drivers.
    """
    versions = {
        "k3s_version": None,
        "nvidia_drivers_version": None,
        "intel_drivers_version": None,
    }

    try:
        config.load_incluster_config()
        version_info = client.VersionApi().get_code()
        versions["k3s_version"] = version_info.git_version
        logger.debug(f"Retrieved k3s version: {versions['k3s_version']}")
    except Exception as e:
        logger.warning(f"Failed to get k3s version: {e}")

    versions["nvidia_drivers_version"] = get_nvidia_driver_version()

    # if not versions["nvidia_drivers_version"]:
    # try:
    # TODO get intel drivers version
    # except Exception as e:
    #     logger.warning(f"Failed to get Intel driver version: {e}")

    return versions
