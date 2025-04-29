# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from dependencies import get_session
from rest.schema.credit_accounts import CreditAccount, CreditAccountPutPayload
from routers import orgs_router
from service.credit_account import CreditAccountService
from service.subscription import SubscriptionService
from utils.enums import Tags

logger = logging.getLogger(__name__)


@orgs_router.put(
    path="/{organization_id}/credit_accounts/{acc_id}",
    tags=[Tags.CREDIT_ACCOUNTS],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Organization doesn't have a credit account with the provided id"},
        status.HTTP_403_FORBIDDEN: {"description": "Organization doesn't have any active credit accounts"},
    },
    response_model=CreditAccount,
)
def update_credit_account(
    organization_id: str, acc_id: UUID, payload: CreditAccountPutPayload, db_session: Session = Depends(get_session)
) -> CreditAccount:
    """
    Updates the credit account of the organization.
    """
    logger.info(f"PUT credit accounts request for the {organization_id} organization.")
    active_subscription = SubscriptionService(session=db_session).get_active_subscription(
        organization_id=organization_id
    )
    if not active_subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Organization {organization_id} doesn't have any active credit accounts.",
        )

    if acc_id not in [acc.id for acc in active_subscription.credit_accounts]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} doesn't have a credit account with id {acc_id}.",
        )

    logger.info(f"Account to update: {acc_id}, received payload: {payload}")

    return CreditAccountService(session=db_session).update_credit_account(
        _db_session=db_session,
        account_id=acc_id,
        organization_id=organization_id,
        name=payload.name,
        renewable_amount=payload.renewable_amount,
        expires=payload.expires,
    )
