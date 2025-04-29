# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Index
from sqlalchemy.orm import Mapped, WriteOnlyMapped, mapped_column, relationship

from db.model.custom_types import UnixTimestampInMilliseconds

from .base import Base


class AccountBalance(Base):
    __tablename__ = "AccountBalance"
    snapshot_id: Mapped[UUID] = mapped_column(ForeignKey("BalanceSnapshot.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("CreditAccount.id", ondelete="CASCADE"), nullable=False)
    incoming_balance = mapped_column(BigInteger, nullable=False)
    available_balance = mapped_column(BigInteger, nullable=False)


class BalanceSnapshot(Base):
    __tablename__ = "BalanceSnapshot"
    date: Mapped[int] = mapped_column(UnixTimestampInMilliseconds, nullable=False)
    subscription_id: Mapped[UUID] = mapped_column(ForeignKey("Subscription.id", ondelete="CASCADE"), nullable=False)
    account_balances: WriteOnlyMapped[AccountBalance | None] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )


Index("snapshot_subsc_id_date_idx", BalanceSnapshot.subscription_id, BalanceSnapshot.date, postgresql_using="btree")
