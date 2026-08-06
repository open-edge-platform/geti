# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""License API Endpoints"""

from typing import Annotated

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_license_service
from app.api.schemas.license import LicenseAcceptResponse
from app.services.license_service import LicenseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/license", tags=["License"])


@router.post("/accept")
async def accept_license(
    license_service: Annotated[LicenseService, Depends(get_license_service)],
) -> LicenseAcceptResponse:
    """Accept the third-party license terms."""
    try:
        license_service.accept()
    except OSError as exc:
        logger.error("Failed to persist license consent: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not persist license consent due to an internal server error.",
        ) from exc
    return LicenseAcceptResponse(license_accepted=True)
