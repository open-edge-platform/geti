# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from dependencies import get_read_only_session
from rest.schema.common import NextPage
from rest.schema.subscription import SubscriptionQuotasResponse
from routers import orgs_router as router
from service.subscription import SubscriptionQuotaFilters, SubscriptionService
from utils.enums import Tags

logger = logging.getLogger(__name__)


@router.get(
    "/{organization_id}/subscriptions/active/quotas",
    tags=[Tags.QUOTAS],
    response_model=SubscriptionQuotasResponse,
)
def get_current_subscription_quotas(
    organization_id: str,
    service_name: str | None = None,
    quota_name: str | None = None,
    quota_type: str | None = None,
    skip: int = 0,
    limit: int | None = None,
    db: Session = Depends(get_read_only_session),
) -> Any:
    """Returns list of subscription quotas for given organization."""
    filters = SubscriptionQuotaFilters(service_name, quota_name, quota_type)
    total_matched, quotas = SubscriptionService(db).get_current_quotas(organization_id, filters, skip, limit)

    if limit:
        next_page_skip = skip + limit
        next_page = NextPage(skip=next_page_skip, limit=limit) if total_matched > next_page_skip else None
    else:
        next_page = None

    return SubscriptionQuotasResponse(
        quotas=quotas,
        total_matched=total_matched,
        next_page=next_page,
    )
