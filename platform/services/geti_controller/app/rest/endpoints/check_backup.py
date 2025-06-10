# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import HTTPException, status

from platform_operations.backup import is_backup_possible
from rest.schema.check_backup import CheckBackupResponse
from routers import platform_router

logger = logging.getLogger(__name__)


@platform_router.get(
    path="/check_backup",
    response_model=CheckBackupResponse,
    responses={
        status.HTTP_200_OK: {
            "description": "Checks if there is sufficient storage space to perform a backup during a platform upgrade.",
            "content": {"application/json": {"example": CheckBackupResponse(is_backup_possible=True)}},
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "An error occurred while verifying backup possibility.",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to verify backup possibility due to an internal error."}
                }
            },
        },
    },
)
def check_backup_possibility() -> CheckBackupResponse:
    """
    Returns JSON with information about the possibility of performing a backup.
    """
    logger.debug("GET check_backup request received.")

    try:
        backup_possible = is_backup_possible()
        logger.info(f"Backup possible: {backup_possible}")
        return CheckBackupResponse(is_backup_possible=backup_possible)

    except Exception as e:
        logger.exception(f"Error while checking backup possibility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify backup possibility due to an internal error.",
        )
