# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from dependencies import get_session
from rest.schema.credit_accounts import CreditAccountPostPayload
from routers import orgs_router
from service.credit_account import CreditAccountDetails, CreditAccountService
from service.subscription import SubscriptionService
from utils.enums import CreditAccountType, Tags

logger = logging.getLogger(__name__)


@orgs_router.post(
    path="/{organization_id}/credit_accounts",
    tags=[Tags.CREDIT_ACCOUNTS],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Credit account has been successfully created",
            "headers": {
                "location": {"description": "The id of the created credit account", "schema": {"type": "string"}}
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Organization doesn't have any active subscriptions, "
            "so it's forbidden to create a new credit account"
        },
    },
)
def create_credit_account(
    organization_id: str,
    payload: CreditAccountPostPayload,
    db_session: Session = Depends(get_session),
) -> Response:
    """
    Creates a new asset account for the organization's active subscription.
    """
    logger.debug(f"POST credit accounts request for the {organization_id} organization. Received payload: {payload}.")
    active_subscription = SubscriptionService(session=db_session).get_active_subscription(
        organization_id=organization_id
    )
    if not active_subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Organization {organization_id} doesn't have any active subscriptions.",
        )

    details = CreditAccountDetails(
        name=payload.name,
        account_type=CreditAccountType.ASSET,
        init_amount=payload.init_amount,
        renewable_amount=payload.renewable_amount,
        expires=payload.expires,
    )
    new_acc_id = CreditAccountService(session=db_session).create_credit_account(
        details=details, subscription=active_subscription
    )
    logger.debug(f"A new asset account was created with id: {new_acc_id} for organization: {organization_id}")
    location = f"/api/v1/organizations/{organization_id}/credit_accounts/{new_acc_id}"
    return Response(status_code=status.HTTP_201_CREATED, headers={"location": location})
