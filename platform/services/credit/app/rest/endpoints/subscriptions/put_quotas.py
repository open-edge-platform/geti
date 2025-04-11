# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from dependencies import get_session
from rest.schema.subscription import OrganizationSubscriptionQuotaPayload, ProvisioningOrganizationSubscriptionQuota
from routers import orgs_router
from service.subscription import SubscriptionService
from utils.enums import Tags

logger = logging.getLogger(__name__)


@orgs_router.put(
    path="/{organization_id}/subscriptions/active/quotas",
    tags=[Tags.QUOTAS],
    response_model=ProvisioningOrganizationSubscriptionQuota,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Organization doesn't have any quotas applied."},
        status.HTTP_400_BAD_REQUEST: {
            "description": """The server cannot process the request due to a malformed request payload. 
            Ensure the request payload is correctly formatted and adheres to the expected schema"""
        },
        status.HTTP_200_OK: {"description": "Subscription quota has been successfully created"},
    },
)
def provisioning_organization_subscription_quota(
    organization_id: str,
    payload: OrganizationSubscriptionQuotaPayload,
    db: Session = Depends(get_session),
) -> Response:
    """
    Creates or updates the row in the SubscriptionQuota for an active subscription for a given organization.
    """
    logger.debug(
        f"Received PUT request to organization quotas for organization id: {organization_id}. "
        f"Received payload: {payload}."
    )

    subscription_service = SubscriptionService(session=db)
    active_subscription = subscription_service.get_active_subscription(organization_id=organization_id)

    if active_subscription is None:
        logger.error(f"Organization {organization_id} doesn't have any active subscription quotas.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} doesn't have any active subscription quotas.",
        )

    quota_lock = f"{organization_id}_{payload.quota_type}"
    return subscription_service.provisioning_organization_subscription_quota(
        _db_session=db,
        subscription=active_subscription,
        quota_lock=quota_lock,
        service_name=payload.service_name,
        quota_name=payload.quota_name,
        quota_type=payload.quota_type,
        limit=payload.limit,
    )
