# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging

from fastapi import Depends, Response, status
from sqlalchemy.orm import Session

from dependencies import get_session
from routers import internal_router
from service.balance import BalanceService
from utils.enums import Tags

logger = logging.getLogger(__name__)


@internal_router.post(path="/credit_accounts/snapshot", tags=[Tags.INTERNAL], status_code=status.HTTP_201_CREATED)
def calculate_snapshot(db: Session = Depends(get_session)) -> Response:
    """
    Get all non-renewable, active (not expired) asset credit accounts,
    and for each of them calculate and write to the database a balance snapshot, with available and incoming balances.

    Calculation takes the latest account's snapshot value (if available) and incorporates
    transactions created thereafter until the present moment
    """
    balance_service = BalanceService(db)
    balance_service.create_organization_snapshots(_db_session=db)
    return Response(status_code=status.HTTP_201_CREATED)
