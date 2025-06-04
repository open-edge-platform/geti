# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import status

from rest.schema.versions import PlatformVersion, PlatformVersionsResponse
from routers import platform_router

logger = logging.getLogger(__name__)


@platform_router.get(
    path="/versions",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved the platform versions.",
            "content": {
                "application/json": {
                    "example": PlatformVersionsResponse(
                        versions=[
                            PlatformVersion(
                                version="2.9.0",
                                k3s_version="v1.24.10+k3s1",
                                nvidia_drivers_version="470.57.02",
                                intel_drivers_version="1.0.0",
                                is_current=True,
                            ),
                            PlatformVersion(
                                version="2.10.0",
                                k3s_version="v1.25.5+k3s1",
                                nvidia_drivers_version="470.57.02",
                                intel_drivers_version="1.0.0",
                                is_current=False,
                            ),
                            PlatformVersion(
                                version="2.11.0",
                                k3s_version="v1.26.4+k3s1",
                                nvidia_drivers_version="470.57.02",
                                intel_drivers_version="1.0.0",
                                is_current=False,
                            ),
                        ]
                    )
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected error occurred while retrieving versions.",
            "content": {
                "application/json": {"example": {"detail": "Failed to retrieve versions due to an internal error."}}
            },
        },
    },
)
def get_versions() -> PlatformVersionsResponse:
    """
    Retrieves the current platform version and available upgrade versions.
    """
    logger.debug("Received GET versions request.")

    # stub response
    return PlatformVersionsResponse(
        versions=[
            PlatformVersion(
                version="2.9.0",
                k3s_version="v1.24.10+k3s1",
                nvidia_drivers_version="470.57.02",
                intel_drivers_version="1.0.0",
                is_current=True,
            ),
            PlatformVersion(
                version="2.10.0",
                k3s_version="v1.25.5+k3s1",
                nvidia_drivers_version="470.57.02",
                intel_drivers_version="1.0.0",
                is_current=False,
            ),
            PlatformVersion(
                version="2.11.0",
                k3s_version="v1.26.4+k3s1",
                nvidia_drivers_version="470.57.02",
                intel_drivers_version="1.0.0",
                is_current=False,
            ),
        ]
    )
