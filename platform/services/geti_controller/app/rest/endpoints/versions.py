# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os
import re

import yaml
from fastapi import HTTPException, status
from kubernetes import client, config, stream
from oras.client import OrasClient
from packaging.version import Version

from rest.schema.versions import PlatformVersion, PlatformVersionsResponse
from routers import platform_router

logger = logging.getLogger(__name__)

GETI_REGISTRY = os.getenv("GETI_REGISTRY")
PLATFORM_VERSION = os.getenv("PLATFORM_VERSION")


def get_nvidia_driver_version() -> str | None:
    """
    Retrieve the NVIDIA driver version by executing nvidia-smi in the nvidia-device-plugin-daemonset pod.
    """
    try:
        config.load_incluster_config()
        core_v1 = client.CoreV1Api()
        pods = core_v1.list_namespaced_pod(namespace="kube-system", label_selector="name=nvidia-device-plugin-ds")
        if not pods.items:
            raise Exception("No nvidia-device-plugin-daemonset pod found in kube-system namespace.")
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
        driver_version = response.strip()
        if not driver_version:
            raise Exception("Failed to retrieve NVIDIA driver version.")
        return driver_version
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

    config.load_incluster_config()
    try:
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


def fetch_available_versions() -> list[str]:
    """
    Fetch available versions from the OCI registry using OrasClient.
    Filters and returns only tags with a higher version number than the current platform version.
    """
    try:
        oc = OrasClient(tls_verify=False)
        tags = oc.get_tags(f"{GETI_REGISTRY}/geti/geti-manifest")
        logger.debug(f"Available Geti versions in the registry: {tags}")

        # extract the semver part of the PLATFORM_VERSION
        current_version = Version(re.match(r"^\d+\.\d+\.\d+", PLATFORM_VERSION).group())

        higher_versions = []
        for tag in tags:
            match = re.match(r"^\d+\.\d+\.\d+", tag)
            if match:
                tag_version = Version(match.group())
                if tag_version > current_version:
                    higher_versions.append(tag)
        return higher_versions

    except Exception:
        logger.exception(f"Failed to fetch available Geti versions from {GETI_REGISTRY}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch versions from OCI registry.",
        )


def fetch_manifest(version: str) -> dict:
    """
    Download the manifest file for a specific version.
    Returns the parsed contents of the manifest as a dictionary.
    """
    try:
        target = f"{GETI_REGISTRY}/geti/geti-manifest:{version}"
        oc = OrasClient(tls_verify=False)
        response = oc.pull(target=target, outdir="/tmp")
        manifest_file = response[0]
        logger.info(f"Geti manifest for version {version} downloaded successfully.")
        logger.debug(f"Downloaded manifest file: {manifest_file}")

        # parse the YAML file and return the first document
        with open(manifest_file) as file:
            manifest = next(iter(yaml.safe_load_all(file)))

        os.remove(manifest_file)
        return manifest

    except Exception:
        logger.exception(f"Failed to fetch Geti manifest from {target}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Geti manifest for version {version}.",
        )


@platform_router.get(
    path="/versions",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved the platform versions.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected error occurred while retrieving versions.",
        },
    },
)
def get_versions() -> PlatformVersionsResponse:
    """
    Retrieves the current platform version and available upgrade versions.
    """
    logger.debug("Received GET versions request.")
    system_versions = get_system_versions()
    upgrade_versions = fetch_available_versions()

    # prepare a response with the available upgrade versions
    versions = []
    for version in upgrade_versions:
        manifest = fetch_manifest(version)
        versions.append(
            PlatformVersion(
                version=version,
                k3s_version=manifest.get("k3s_version"),
                nvidia_drivers_version=manifest.get("nvidia_drivers_version"),
                intel_drivers_version=manifest.get("intel_drivers_version"),
                is_current=False,
                is_upgrade_required=manifest.get("is_upgrade_required"),
            )
        )

    # add the current version to the response
    versions.insert(
        0,
        PlatformVersion(
            version=PLATFORM_VERSION,
            k3s_version=system_versions["k3s_version"],
            nvidia_drivers_version=system_versions["nvidia_drivers_version"],
            intel_drivers_version=system_versions["intel_drivers_version"],
            is_current=True,
            is_upgrade_required=False,
        ),
    )

    return PlatformVersionsResponse(versions=versions)
