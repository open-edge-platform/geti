# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, WriteOnlyMapped, mapped_column, relationship

from db.model.balance import BalanceSnapshot
from db.model.custom_types import UnixTimestampInMilliseconds
from utils.enums import SubscriptionStatus
from utils.renewal_date_calculation import get_next_renewal_date, get_prev_renewal_date
from utils.time import get_current_milliseconds_timestamp

from .base import Base

if TYPE_CHECKING:
    from db.model.credit_account import CreditAccount


class Subscription(Base):
    __tablename__ = "Subscription"
    organization_id = mapped_column(String(36), nullable=False)
    workspace_id = mapped_column(String(36), nullable=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("Product.id"), nullable=False)
    renewal_day_of_month = mapped_column(Integer(), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(nullable=False)
    created: Mapped[int] = mapped_column(
        UnixTimestampInMilliseconds, default=get_current_milliseconds_timestamp, nullable=False
    )
    updated: Mapped[int] = mapped_column(
        UnixTimestampInMilliseconds,
        default=get_current_milliseconds_timestamp,
        onupdate=get_current_milliseconds_timestamp,
        nullable=False,
    )
    credit_accounts: Mapped[list["CreditAccount"]] = relationship(
        back_populates="subscription", cascade="all, delete", passive_deletes=True
    )
    quotas: Mapped[list["SubscriptionQuota"]] = relationship(
        back_populates="subscription", cascade="all, delete-orphan", passive_deletes=True
    )
    balance_snapshots: WriteOnlyMapped[BalanceSnapshot | None] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def next_renewal_date(self) -> int:
        """The nearest upcoming renewal date"""
        return get_next_renewal_date(renewal_day=self.renewal_day_of_month)

    @property
    def previous_renewal_date(self) -> int:
        """Start of the current subscription cycle"""
        return get_prev_renewal_date(renewal_day=self.renewal_day_of_month)

    def __repr__(self):
        return (
            f"Subscription({self.id=}, {self.organization_id=}, {self.workspace_id=}, "
            f"{self.product_id=}, {self.renewal_day_of_month=}, {self.status=}, {self.created=}, {self.updated=})"
        )


Index(
    "subscription_organization_id_idx",
    Subscription.organization_id,
    postgresql_using="btree",
)


class SubscriptionQuota(Base):
    __tablename__ = "SubscriptionQuota"
    subscription_id: Mapped[UUID] = mapped_column(ForeignKey("Subscription.id", ondelete="CASCADE"), nullable=False)

    service_name: Mapped[str] = mapped_column(nullable=False)
    quota_name: Mapped[str] = mapped_column(nullable=False)
    quota_type: Mapped[str] = mapped_column(nullable=False)
    limit = mapped_column(BigInteger, nullable=False)
    created: Mapped[int] = mapped_column(
        UnixTimestampInMilliseconds, default=get_current_milliseconds_timestamp, nullable=False
    )
    updated: Mapped[int] = mapped_column(
        UnixTimestampInMilliseconds,
        default=get_current_milliseconds_timestamp,
        onupdate=get_current_milliseconds_timestamp,
        nullable=False,
    )
    subscription: Mapped[Subscription] = relationship(back_populates="quotas")

    def __repr__(self):
        return (
            f"SubscriptionQuota({self.id=}, {self.subscription_id=}, {self.service_name=}, {self.quota_name=}, "
            f"{self.quota_type=}, {self.limit=}, {self.created=}, {self.updated=})"
        )


Index("subscription_quota_subscription_id_idx", SubscriptionQuota.subscription_id, postgresql_using="btree")
