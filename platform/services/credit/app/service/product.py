# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Session

from db.repository.product import ProductRepository
from rest.schema.product import Product, ProductPolicy

if TYPE_CHECKING:
    from db.model import Product as db_Product


class ProductService:
    def __init__(self, session: Session):
        self.product_repository = ProductRepository(session)

    def get_all_products(self, limit: int = 10, skip: int = 0) -> tuple[int, list[Product]]:
        """
        Returns a tuple with the total number of products and the products list, with their assigned credits policies.
        """
        total, db_products = self.product_repository.get_products(skip=skip, limit=limit)
        products = [
            Product(
                id=prod.id,
                name=prod.name,
                product_policies=[
                    ProductPolicy(
                        account_name=pol.account_name,
                        init_amount=pol.init_amount,
                        renewable_amount=pol.renewable_amount,
                        expires_in=pol.expires_in,
                    )
                    for pol in self.product_repository.get_product_policies(prod.id)
                ],
                created=prod.created,
                updated=prod.updated,
            )
            for prod in db_products
        ]
        return total, products

    def get_product_by_id(self, product_id: UUID) -> Product:
        """
        Returns the product with the requested id, with its assigned credits policies.
        """
        prod: db_Product = self.product_repository.get_by_id(product_id)
        return Product(
            id=prod.id,
            name=prod.name,
            product_policies=[
                ProductPolicy(
                    account_name=pol.account_name,
                    init_amount=pol.init_amount,
                    renewable_amount=pol.renewable_amount,
                    expires_in=pol.expires_in,
                )
                for pol in self.product_repository.get_product_policies(prod.id)
            ],
            created=prod.created,
            updated=prod.updated,
        )

    def get_product_by_name(self, product_name: str) -> Product:
        """
        Returns the product with the requested name, with its assigned credits policies.
        """
        prod: db_Product = self.product_repository.get_by_name(product_name)
        return Product(
            id=prod.id,
            name=prod.name,
            product_policies=[
                ProductPolicy(
                    account_name=pol.account_name,
                    init_amount=pol.init_amount,
                    renewable_amount=pol.renewable_amount,
                    expires_in=pol.expires_in,
                )
                for pol in self.product_repository.get_product_policies(prod.id)
            ],
            created=prod.created,
            updated=prod.updated,
        )
