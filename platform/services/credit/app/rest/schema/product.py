# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from uuid import UUID

from pydantic import BaseModel

from rest.schema.common import ListModel


class ProductPolicy(BaseModel):
    account_name: str
    init_amount: int
    renewable_amount: int | None = None
    expires_in: int | None = None


class Product(BaseModel):
    id: UUID
    name: str
    product_policies: list[ProductPolicy]
    created: int
    updated: int


class ListProductResponse(ListModel):
    products: list[Product]
