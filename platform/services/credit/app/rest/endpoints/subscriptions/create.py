# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from db.model import Subscription
from dependencies import get_session
from rest.schema.subscription import SubscriptionPayload
from routers import orgs_router as router
from service.subscription import SubscriptionService
from utils.enums import SubscriptionStatus, Tags
from utils.time import get_current_day

logger = logging.getLogger(__name__)


# THIS ENDPOINT HAS BEEN TEMPORARILY DISABLED - see CVS-158609


@router.post(
    "/{organization_id}/workspaces/{workspace_id}/subscriptions",
    tags=[Tags.SUBSCRIPTIONS],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Subscription has been successfully created",
            "headers": {
                "location": {"description": "The id of the created subscription", "schema": {"type": "string"}}
            },
        },
        status.HTTP_409_CONFLICT: {"description": "Organization already has a subscription for the requested product"},
    },
)
def create_subscription(
    organization_id: str, workspace_id: str, payload: SubscriptionPayload, db: Session = Depends(get_session)
) -> Response:
    """Creates new subscription within organization for specified product"""

    logger.info(
        f"Create subscription request for the organization {organization_id} and product id {payload.product_id}"
    )
    subscription_service = SubscriptionService(db)
    active_subscription: Subscription | None = subscription_service.get_active_subscription(organization_id)
    if active_subscription:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization {organization_id} already has an active subscription "
            f"for the product {active_subscription.product_id}",
        )

    init_subscription = Subscription(
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_id=payload.product_id,
        status=SubscriptionStatus.NEW,
        renewal_day_of_month=get_current_day(),
    )
    new_subscription_id = subscription_service.transition(
        subscription=init_subscription,
        new_status=SubscriptionStatus.ACTIVE,
        organization_id=organization_id,
        _db_session=db,
    ).id
    logger.info(
        f"Organization {organization_id} has successfully subscribed to the product {init_subscription.product_id},"
        f"new subscription id: {new_subscription_id}"
    )
    location = f"/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/subscriptions/{new_subscription_id}"
    return Response(status_code=status.HTTP_201_CREATED, headers={"location": location})
