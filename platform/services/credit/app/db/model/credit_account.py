# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, WriteOnlyMapped, mapped_column, relationship

from db.model import Base
from db.model.balance import AccountBalance
from db.model.custom_types import UnixTimestampInMilliseconds
from db.model.subscription import Subscription
from db.model.transaction import Transactions
from utils.enums import CreditAccountType
from utils.time import get_current_milliseconds_timestamp


class CreditAccount(Base):
    __tablename__ = "CreditAccount"
    subscription_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("Subscription.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[CreditAccountType] = mapped_column(nullable=False)
    renewable_amount: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    created: Mapped[int] = mapped_column(
        UnixTimestampInMilliseconds, default=get_current_milliseconds_timestamp, nullable=False
    )
    updated: Mapped[int] = mapped_column(
        UnixTimestampInMilliseconds,
        default=get_current_milliseconds_timestamp,
        onupdate=get_current_milliseconds_timestamp,
        nullable=False,
    )
    expires: Mapped[int | None] = mapped_column(UnixTimestampInMilliseconds, nullable=True)
    subscription: Mapped[Subscription | None] = relationship(back_populates="credit_accounts")
    transactions: WriteOnlyMapped[Transactions | None] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, order_by="Transactions.created"
    )
    balance_snapshots: WriteOnlyMapped[AccountBalance | None] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, order_by="AccountBalance.id"
    )

    def __repr__(self):
        return (
            f"CreditAccount({self.id=}, {self.subscription_id=}, {self.name=}, {self.type=}, "
            f"{self.renewable_amount=}, {self.created=}, {self.updated=})"
        )


Index(
    "credit_account_subscription_id_idx",
    CreditAccount.subscription_id,
    postgresql_using="btree",
)
