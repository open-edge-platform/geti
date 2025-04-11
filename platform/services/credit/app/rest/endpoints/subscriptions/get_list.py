# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from dependencies import get_read_only_session
from rest.schema.common import NextPage
from rest.schema.subscription import OrgSubscriptionsResponse
from routers import orgs_router as router
from service.subscription import SubscriptionService
from utils.enums import Tags

logger = logging.getLogger(__name__)


@router.get("/{organization_id}/subscriptions", tags=[Tags.SUBSCRIPTIONS], response_model=OrgSubscriptionsResponse)
def get_organization_subscriptions(
    organization_id: str,
    skip: Annotated[int, Query(ge=0, le=50)] = 0,
    limit: Annotated[int, Query(ge=0, le=50)] = 10,
    db: Session = Depends(get_read_only_session),
) -> OrgSubscriptionsResponse:
    """Returns all organization's subscriptions"""

    subscription_service = SubscriptionService(session=db)

    total_matched, subscriptions_list = subscription_service.get_all_org_subscriptions(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
    )
    next_page_skip = skip + limit
    next_page = None
    if total_matched > next_page_skip:
        next_page = NextPage(skip=next_page_skip, limit=limit)

    return OrgSubscriptionsResponse(
        subscriptions=subscriptions_list,
        total_matched=total_matched,
        next_page=next_page,
    )
