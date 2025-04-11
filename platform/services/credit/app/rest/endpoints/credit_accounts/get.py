# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from dependencies import get_session
from rest.schema.common import NextPage
from rest.schema.credit_accounts import CreditAccountsResponse
from routers import orgs_router
from service.credit_account import CreditAccountService
from service.subscription import SubscriptionService
from utils.enums import Tags

logger = logging.getLogger(__name__)


@orgs_router.get(
    path="/{organization_id}/credit_accounts",
    tags=[Tags.CREDIT_ACCOUNTS],
    response_model=CreditAccountsResponse,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Organization doesn't have any active credit accounts"}},
)
def get_credit_accounts(
    organization_id: str,
    skip: Annotated[int, Query(ge=0, le=1000)] = 0,
    limit: Annotated[int, Query(ge=0, le=1000)] = 50,
    db_session: Session = Depends(get_session),
) -> CreditAccountsResponse:
    """
    Returns billable credit accounts of the organization ('ASSET' account type, not expired).
    Lease and SaaS provider accounts not included.
    """
    logger.debug(f"Received GET credit accounts request for the {organization_id} organization.")
    active_subscription = SubscriptionService(session=db_session).get_active_subscription(
        organization_id=organization_id
    )

    if not active_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} doesn't have any active credit accounts.",
        )

    total_matched, accounts_list = CreditAccountService(session=db_session).get_organization_accounts(
        subscription=active_subscription,
        skip=skip,
        limit=limit,
    )
    next_page_skip = skip + limit
    next_page = None
    if total_matched > next_page_skip:
        next_page = NextPage(skip=next_page_skip, limit=limit)
    return CreditAccountsResponse(
        credit_accounts=accounts_list,
        total_matched=total_matched,
        next_page=next_page,
    )
