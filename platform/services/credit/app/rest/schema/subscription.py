# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from uuid import UUID

from pydantic import BaseModel, Field

from rest.schema.common import ListModel
from utils.enums import QuotaType


class SubscriptionPayload(BaseModel):
    product_id: UUID


class SubscriptionResponse(BaseModel):
    id: UUID
    organization_id: str
    workspace_id: str
    product_id: UUID
    status: str
    created: int
    updated: int
    next_renewal_date: int | None = None
    previous_renewal_date: int | None = None


class OrgSubscriptionsResponse(ListModel):
    subscriptions: list[SubscriptionResponse]


class SubscriptionQuota(BaseModel):
    id: UUID | None = None  # If org has no subscription quotas - product quota is used, so it might be missing
    organization_id: str
    service_name: str
    quota_name: str
    quota_type: str
    limit: int
    created: int | None = None
    updated: int | None = None


class SubscriptionQuotasResponse(ListModel):
    quotas: list[SubscriptionQuota]


class ProvisioningOrganizationSubscriptionQuota(BaseModel):
    id: UUID
    service_name: str
    quota_name: str
    quota_type: QuotaType
    limit: int = Field(gt=0)
    created: int
    updated: int


class OrganizationSubscriptionQuotaPayload(BaseModel):
    service_name: str
    quota_name: str
    quota_type: QuotaType
    limit: int = Field(gt=0)
