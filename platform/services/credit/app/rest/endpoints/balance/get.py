# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from dependencies import get_session
from rest.schema.balance import BalanceResponse
from routers import orgs_router
from service.balance import BalanceService
from service.subscription import SubscriptionService
from utils.enums import CreditSystemTimeBoundaries, Tags
from utils.time import get_current_milliseconds_timestamp

logger = logging.getLogger(__name__)


@orgs_router.get(
    path="/{organization_id}/balance",
    response_model=BalanceResponse,
    tags=[Tags.BALANCE],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Organization doesn't have any active credit accounts"}},
)
def get_balance(
    organization_id: str,
    date: Annotated[
        int | None,
        Query(
            ge=CreditSystemTimeBoundaries.START.value,
            le=CreditSystemTimeBoundaries.END.value,
            description="Milliseconds timestamp",
        ),
    ] = None,
    db: Session = Depends(get_session),
) -> BalanceResponse:
    """
    The running credit balance of an organization is calculated during the current subscription cycle
    """
    logger.info(f"Received GET balance request for the {organization_id} organization.")
    active_subscription = SubscriptionService(session=db).get_active_subscription(organization_id=organization_id)
    if not active_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} doesn't have any active credit accounts.",
        )

    if date is None:
        date = get_current_milliseconds_timestamp()
    balance_service = BalanceService(session=db)
    return balance_service.get_organization_balance(active_subscription=active_subscription, date=date)
