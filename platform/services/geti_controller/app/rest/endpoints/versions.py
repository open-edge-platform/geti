# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os

from fastapi import HTTPException, status

from platform_operations.geti_manifest import fetch_available_versions, fetch_manifest
from platform_operations.system_versions import get_system_versions
from rest.schema.versions import PlatformVersion, PlatformVersionsResponse
from routers import platform_router

logger = logging.getLogger(__name__)

GETI_REGISTRY = os.getenv("GETI_REGISTRY")
PLATFORM_VERSION = os.getenv("PLATFORM_VERSION")


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

    try:
        system_versions = get_system_versions()
        upgrade_versions = fetch_available_versions(GETI_REGISTRY, PLATFORM_VERSION)

        # prepare a response with the available upgrade versions
        versions = []
        for version in upgrade_versions:
            manifest = fetch_manifest(GETI_REGISTRY, version)
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

    except Exception:
        logger.exception("Unexpected error occurred while retrieving versions.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform versions.",
        )
