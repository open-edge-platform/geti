# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.model.custom_types import UnixTimestampInMilliseconds
from utils.time import get_current_milliseconds_timestamp

from .base import Base


class Transactions(Base):
    __tablename__ = "Transactions"
    tx_id = mapped_column(String(36), nullable=False)  # links direct transactions between 2 credit accounts
    tx_group_id = mapped_column(String(36), nullable=True)  # logical identifier to group lease related transactions
    account_id: Mapped[UUID] = mapped_column(ForeignKey("CreditAccount.id", ondelete="CASCADE"), nullable=False)
    debit = mapped_column(Integer, nullable=True)
    credit = mapped_column(Integer, nullable=True)
    created: Mapped[int] = mapped_column(
        UnixTimestampInMilliseconds, default=get_current_milliseconds_timestamp, nullable=False
    )
    project_id = mapped_column(String(36), nullable=True)
    service_name = mapped_column(String(36), nullable=True)
    requests = mapped_column(JSONB, nullable=True)


Index(
    "transactions_created_brin_idx",
    Transactions.created,
    postgresql_using="brin",
    postgresql_with={"pages_per_range": 128},
)

Index(
    "transactions_group_id_idx",
    Transactions.tx_group_id,
    postgresql_using="btree",
)
