# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from uuid import UUID

from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from dependencies import get_session
from rest.schema.balance import BalancePayload
from routers import orgs_router
from service.subscription import SubscriptionService
from service.transaction import TransactionService
from utils.enums import Tags

logger = logging.getLogger(__name__)


@orgs_router.put(
    path="/{organization_id}/credit_accounts/{account_id}/balance",
    tags=[Tags.BALANCE],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid request"},
        status.HTTP_403_FORBIDDEN: {
            "description": "Credit account is not active, so it's forbidden to alter its balance"
        },
        status.HTTP_404_NOT_FOUND: {"description": "Organization doesn't have a credit account with the requested id"},
    },
)
def edit_account_balance(
    organization_id: str, account_id: UUID, payload: BalancePayload, db_session: Session = Depends(get_session)
) -> Response:
    """
    Edits balance of a certain credit account by comparing current available balance
    with a balance in the provided payload, and creating a credits transaction covering the difference.
    """
    logger.debug(
        f"Received PUT balance request for the credit account: {account_id}, "
        f"belonging to the {organization_id} organization."
    )
    active_subscription = SubscriptionService(session=db_session).get_active_subscription(
        organization_id=organization_id
    )
    if not active_subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Organization {organization_id} doesn't have any active credit accounts.",
        )

    if account_id not in [acc.id for acc in active_subscription.credit_accounts]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} doesn't have a credit account with id {account_id}.",
        )

    if (not payload.add and not payload.subtract) or (payload.add and payload.subtract):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Either 'add' or 'subtract' value should be provided."
        )

    transactions_svc = TransactionService(session=db_session)

    if payload.add:
        transactions_svc.fill_account(
            receiver_acc_id=account_id, amount=payload.add, _db_session=db_session, organization_id=organization_id
        )
    elif payload.subtract:
        transactions_svc.withdraw_credits(
            account_id=account_id,
            amount=payload.subtract,
            _db_session=db_session,
            subscription=active_subscription,
            organization_id=organization_id,
        )

    return Response(status_code=status.HTTP_200_OK)
