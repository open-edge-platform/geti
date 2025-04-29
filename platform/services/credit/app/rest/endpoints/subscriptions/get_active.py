# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from dependencies import get_read_only_session
from rest.schema.subscription import SubscriptionResponse
from routers import orgs_router as router
from service.subscription import SubscriptionService
from utils.enums import Tags

logger = logging.getLogger(__name__)


@router.get(
    "/{organization_id}/subscriptions/active",
    tags=[Tags.SUBSCRIPTIONS],
    response_model=SubscriptionResponse,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Organization doesn't have any active subscriptions"}},
)
def get_active_subscription(organization_id: str, db: Session = Depends(get_read_only_session)) -> SubscriptionResponse:
    """Returns organization's active subscription"""

    subscription_service = SubscriptionService(session=db)
    active_subscription = subscription_service.get_active_subscription(organization_id)
    if not active_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} doesn't have any active subscriptions.",
        )

    return SubscriptionResponse(
        id=active_subscription.id,
        organization_id=active_subscription.organization_id,
        workspace_id=active_subscription.workspace_id,
        product_id=active_subscription.product_id,
        status=active_subscription.status,
        created=active_subscription.created,
        updated=active_subscription.updated,
        next_renewal_date=active_subscription.next_renewal_date,
        previous_renewal_date=(
            active_subscription.previous_renewal_date
            if active_subscription.previous_renewal_date > active_subscription.updated
            else None
        ),
    )
