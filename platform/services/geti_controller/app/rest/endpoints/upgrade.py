# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import HTTPException, status

from rest.schema.upgrade import UpgradeRequest, UpgradeResponse
from routers import platform_router

logger = logging.getLogger(__name__)


@platform_router.post(
    path="/upgrade",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Upgrade process started successfully.",
            "content": {
                "application/json": {"example": UpgradeResponse(detail="Upgrade to version 2.12.0 has started.")}
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Not enough space to perform backup.",
            "content": {
                "application/json": {
                    "example": {"detail": "Not enough space to perform backup. Required: 10GB, Available: 5GB."}
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "k3s or NVIDIA drivers are outdated.",
            "content": {
                "application/json": {
                    "example": {"detail": "k3s or NVIDIA drivers are outdated and need to be upgraded first."}
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected error occurred while starting the upgrade process.",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to start the upgrade process due to an internal error."}
                }
            },
        },
    },
)
def upgrade_platform(payload: UpgradeRequest) -> UpgradeResponse:
    """
    Starts the upgrade of the platform to the specified version.
    """
    logger.debug(f"POST upgrade request received. Payload: {payload}")

    # Stub responses
    if not payload.version_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Version number is required.",
        )

    logger.info(f"Upgrade to version {payload.version_number} has started.")
    return UpgradeResponse(detail=f"Upgrade to version {payload.version_number} has started.")
