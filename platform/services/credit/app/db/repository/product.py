# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from db.model.product import Product, ProductPolicy, ProductQuota
from db.repository.common import BaseRepository
from exceptions.custom_exceptions import NoDatabaseResult

logger = logging.getLogger(__name__)


class ProductRepository(BaseRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_products(self, limit: int = 10, skip: int = 0) -> tuple[int, list[Product]]:
        subq = select(func.count()).select_from(Product).correlate(None).scalar_subquery()
        stmt = select(Product, subq.label("total_count")).order_by(Product.name).offset(skip).limit(limit)
        results = self.session.execute(stmt).all()

        total_count = results[0][1] if results else 0
        products = [row[0] for row in results] if results else []
        return total_count, products

    def get_by_id(self, product_id: UUID) -> Product:
        try:
            return self.session.scalars(select(Product).where(Product.id == product_id)).one()
        except NoResultFound:
            raise NoDatabaseResult(f"No product with ID {product_id} found.")

    def get_by_name(self, product_name: str) -> Product:
        try:
            return self.session.scalars(select(Product).where(Product.name == product_name)).one()
        except NoResultFound:
            raise NoDatabaseResult(f"No product with name {product_name} found.")

    def get_product_policies(self, product_id: UUID) -> Sequence[ProductPolicy]:
        result = self.session.scalars(select(ProductPolicy).where(ProductPolicy.product_id == product_id)).all()
        if len(result) == 0:
            raise RuntimeError(f"Product with id {product_id} has no policies defined.")
        return result

    def get_product_quotas(
        self,
        product_id: UUID,
        service_name: str | None = None,
        quota_name: str | None = None,
        quota_type: str | None = None,
    ) -> Sequence[ProductQuota]:
        stmt = select(ProductQuota).where(ProductQuota.product_id == product_id)

        if service_name:
            stmt = stmt.where(ProductQuota.service_name == service_name)
        if quota_name:
            stmt = stmt.where(ProductQuota.quota_name == quota_name)
        if quota_type:
            stmt = stmt.where(ProductQuota.quota_type == quota_type)

        result = self.session.scalars(stmt).all()

        if len(result) == 0:
            raise RuntimeError(f"Product with id {product_id} does not have default product quotas defined.")

        return result
