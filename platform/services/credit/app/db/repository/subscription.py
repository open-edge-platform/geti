# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Sequence
from typing import Any, NamedTuple
from uuid import UUID

from sqlalchemy import distinct, func, select, union
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.model.credit_account import CreditAccount
from db.model.product import ProductQuota
from db.model.subscription import Subscription, SubscriptionQuota
from db.model.transaction import Transactions
from db.repository.common import BaseRepository
from utils.enums import CreditAccountType, QuotaType, SubscriptionStatus

logger = logging.getLogger(__name__)


class SubscriptionQuotaFilters(NamedTuple):
    service_name: str | None
    quota_name: str | None
    quota_type: str | None


class SubscriptionRepository(BaseRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_organization(self, organization_id: str) -> Sequence[Subscription]:
        """Returns the organization's subscriptions"""
        return self.session.scalars(select(Subscription).where(Subscription.organization_id == organization_id)).all()

    def get_all_active_subscriptions(self) -> Sequence[Subscription]:
        """Returns all subscriptions in an active state"""
        return self.session.scalars(select(Subscription).where(Subscription.status == SubscriptionStatus.ACTIVE)).all()

    def get_subscription_quotas(
        self, subscription: Subscription, filters: SubscriptionQuotaFilters
    ) -> tuple[int, Sequence[SubscriptionQuota]]:
        def apply_filters(query: Any, model: Any) -> Any:
            if filters.service_name:
                query = query.where(model.service_name == filters.service_name)
            if filters.quota_name:
                query = query.where(model.quota_name == filters.quota_name)
            if filters.quota_type:
                query = query.where(model.quota_type == filters.quota_type)
            return query

        product_quotas = select(ProductQuota.quota_type).where(ProductQuota.product_id == subscription.product_id)
        product_quotas = apply_filters(product_quotas, ProductQuota)

        sub_quotas = select(SubscriptionQuota.quota_type).where(SubscriptionQuota.subscription_id == subscription.id)
        sub_quotas = apply_filters(sub_quotas, SubscriptionQuota)

        stmt = select(SubscriptionQuota).where(SubscriptionQuota.subscription_id == subscription.id)
        stmt = apply_filters(stmt, SubscriptionQuota)

        combined_quotas = union(product_quotas, sub_quotas).subquery()
        subquery = select(func.count(distinct(combined_quotas.c.quota_type)))

        total_matched = self.session.scalar(subquery) or 0
        quotas = self.session.scalars(stmt).all()

        return total_matched, quotas

    def get_subscription_quota_by_type(self, subscription_id: UUID, quota_type: QuotaType) -> SubscriptionQuota | None:
        """Retrieves the subscription quota for a given subscription UUID and quota type."""
        stmt = (
            select(SubscriptionQuota)
            .where(SubscriptionQuota.subscription_id == subscription_id)
            .where(SubscriptionQuota.quota_type == quota_type)
        )
        return self.session.scalars(statement=stmt).one_or_none()

    def get_by_lease_id(self, tx_group_id: str) -> Subscription:
        """Returns subscription basing on provided lease id"""
        stmt = (
            select(Subscription)
            .join(CreditAccount, Subscription.id == CreditAccount.subscription_id)
            .join(Transactions, CreditAccount.id == Transactions.account_id)
        ).where(Transactions.tx_group_id == tx_group_id, CreditAccount.type == CreditAccountType.ASSET)
        return self.session.scalars(stmt).first()

    def create(self, new_subscription: Subscription) -> Subscription:
        self.session.add(new_subscription)
        try:
            self.session.flush()
            self.session.refresh(new_subscription)
            return new_subscription
        except IntegrityError as int_err:
            logger.warning(f"{int_err.params} - {int_err.orig}")
            raise RuntimeError("Subscription creation failed. Check logs for more info/") from int_err

    def get_subscriptions_by_renewal_dates_range(self, renewal_days_list: list[int]) -> Sequence[Subscription]:
        stmt = (
            select(Subscription)
            .filter(Subscription.status == SubscriptionStatus.ACTIVE)
            .filter(Subscription.renewal_day_of_month.in_(renewal_days_list))
        )
        return self.session.scalars(statement=stmt).all()

    def create_subscription_quota(self, subscription_quota: SubscriptionQuota) -> None:
        """Creates a new row in the SubscriptionQuota table"""
        logger.debug(f"Creation of subscription quota called with {repr(subscription_quota)}")

        self.session.add(subscription_quota)
        try:
            self.session.flush()
        except IntegrityError as err:
            logger.error(f"{err.params} - {err.orig}")
            raise RuntimeError("Credit Account creation failed. Check logs for more info:") from err
