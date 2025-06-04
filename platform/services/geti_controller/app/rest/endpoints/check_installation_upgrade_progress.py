# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import status

from rest.schema.check_installation_upgrade_progress import InstallationUpgradeProgressResponse, OperationStatus
from routers import platform_router

logger = logging.getLogger(__name__)


@platform_router.get(
    path="/check_installation_upgrade_progress",
    response_model=InstallationUpgradeProgressResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully retrieved the installation/upgrade progress.",
            "content": {
                "application/json": {
                    "example": InstallationUpgradeProgressResponse(
                        progress_percentage=42, status=OperationStatus.RUNNING, message="Installation is in progress."
                    )
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected error occurred while checking progress.",
            "content": {
                "application/json": {"example": {"detail": "Failed to retrieve progress due to an internal error."}}
            },
        },
    },
)
def check_installation_upgrade_progress() -> InstallationUpgradeProgressResponse:
    """
    Checks the progress of the current installation or upgrade process.
    """
    logger.debug("GET check_installation_upgrade_progress request received.")

    # stub response
    return InstallationUpgradeProgressResponse(
        progress_percentage=42, status=OperationStatus.RUNNING, message="Installation is in progress."
    )
