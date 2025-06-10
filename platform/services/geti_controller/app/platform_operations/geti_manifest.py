# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os
import re

import yaml
from oras.client import OrasClient
from packaging.version import Version

logger = logging.getLogger(__name__)


def fetch_available_versions(geti_registry: str, platform_version: str) -> list[str]:
    """
    Fetch available versions from the OCI registry using OrasClient.
    Filters and returns only tags with a higher version number than the current platform version.
    """
    try:
        oc = OrasClient(tls_verify=False)
        tags = oc.get_tags(f"{geti_registry}/geti/geti-manifest")
        logger.debug(f"Available Geti versions in the registry: {tags}")

        current_version = Version(re.match(r"^\d+\.\d+\.\d+", platform_version).group())

        higher_versions = []
        for tag in tags:
            match = re.match(r"^\d+\.\d+\.\d+", tag)
            if match:
                tag_version = Version(match.group())
                if tag_version > current_version:
                    higher_versions.append(tag)
        return higher_versions

    except Exception:
        logger.exception(f"Failed to fetch available Geti versions from {geti_registry}")
        raise


def fetch_manifest(geti_registry: str, version: str) -> dict:
    """
    Download the manifest file for a specific version.
    Returns the parsed contents of the manifest as a dictionary.
    """
    try:
        target = f"{geti_registry}/geti/geti-manifest:{version}"
        oc = OrasClient(tls_verify=False)
        response = oc.pull(target=target, outdir="/tmp")  # noqa S108
        manifest_file = response[0]
        logger.debug(f"Downloaded Geti manifest file for version {version}: {manifest_file}")

        with open(manifest_file) as file:
            manifest = next(iter(yaml.safe_load_all(file)))

        os.remove(manifest_file)
        return manifest

    except Exception:
        logger.exception(f"Failed to fetch Geti manifest for version {version} from {geti_registry}")
        raise
