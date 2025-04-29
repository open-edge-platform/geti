# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, Query, status
from sqlalchemy.orm import Session

from dependencies import get_read_only_session
from rest.schema.common import NextPage
from rest.schema.product import ListProductResponse, Product
from routers import products_router as router
from service.product import ProductService
from utils.enums import Tags

logger = logging.getLogger(__name__)


@router.get("", tags=[Tags.PRODUCTS], status_code=status.HTTP_200_OK, response_model=ListProductResponse)
def get_all_products(
    skip: Annotated[int, Query(ge=0, le=50)] = 0,
    limit: Annotated[int, Query(ge=0, le=50)] = 10,
    db: Session = Depends(get_read_only_session),
) -> Any:
    """Returns all available Geti SaaS subscription products"""
    total_matched, products = ProductService(db).get_all_products(skip=skip, limit=limit)
    next_page_skip = skip + limit
    next_page = NextPage(skip=next_page_skip, limit=limit) if total_matched > next_page_skip else None
    return ListProductResponse(
        products=products,
        total_matched=total_matched,
        next_page=next_page,
    )


@router.get("/{product_id}", tags=[Tags.PRODUCTS], status_code=status.HTTP_200_OK, response_model=Product)
def get_product_by_id(product_id: UUID, db: Session = Depends(get_read_only_session)) -> Any:
    """Returns Geti SaaS subscription product with the specified id"""

    return ProductService(db).get_product_by_id(product_id)
