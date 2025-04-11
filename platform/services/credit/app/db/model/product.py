# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.model.custom_types import UnixTimestampInMilliseconds
from utils.time import get_current_milliseconds_timestamp

from .base import Base


class Product(Base):
    __tablename__ = "Product"
    name = mapped_column(String(36), nullable=False)
    created: Mapped[int] = mapped_column(
        UnixTimestampInMilliseconds, default=get_current_milliseconds_timestamp, nullable=False
    )
    updated: Mapped[int] = mapped_column(
        UnixTimestampInMilliseconds,
        default=get_current_milliseconds_timestamp,
        onupdate=get_current_milliseconds_timestamp,
        nullable=False,
    )
    policies: Mapped[list["ProductPolicy"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", passive_deletes=True
    )
    quotas: Mapped[list["ProductQuota"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self):
        return f"Product({self.id=}, {self.name=}, {self.created=}, {self.updated=})"


Index("product_name_idx", Product.name, postgresql_using="btree")


class ProductPolicy(Base):
    __tablename__ = "ProductPolicy"
    product_id: Mapped[UUID] = mapped_column(ForeignKey("Product.id", ondelete="CASCADE"), nullable=False)
    account_name = mapped_column(String(36), nullable=False)
    init_amount = mapped_column(Integer, nullable=False)
    renewable_amount = mapped_column(Integer, nullable=True)
    expires_in = mapped_column(BigInteger, nullable=True)
    product: Mapped["Product"] = relationship(back_populates="policies")


Index("product_policy_product_id_idx", ProductPolicy.product_id, postgresql_using="btree")


class ProductQuota(Base):
    __tablename__ = "ProductQuota"
    product_id: Mapped[UUID] = mapped_column(ForeignKey("Product.id", ondelete="CASCADE"), nullable=False)
    service_name: Mapped[str] = mapped_column(nullable=False)
    limit = mapped_column(BigInteger, nullable=False)
    quota_name: Mapped[str] = mapped_column(nullable=False)
    quota_type: Mapped[str] = mapped_column(nullable=False)
    product: Mapped["Product"] = relationship(back_populates="quotas")

    def __repr__(self):
        return (
            f"ProductQuota({self.id=}, {self.product_id=}, {self.service_name=}, {self.limit=}, "
            f"{self.quota_name=}, {self.quota_type=})"
        )


Index("product_quota_product_id_idx", ProductQuota.product_id, postgresql_using="btree")
