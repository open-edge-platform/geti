# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch
from uuid import uuid4

from db.repository.product import Product, ProductPolicy
from service.product import ProductService


@patch("service.product.ProductRepository")
def test_get_all_products(mock_product_repo, request) -> None:
    # Arrange
    session = MagicMock()
    product_repo = MagicMock()
    db_product_1 = Product(id=uuid4(), name="Default product", created=12345, updated=12345)
    db_product_2 = Product(id=uuid4(), name="Another product", created=12345, updated=12345)

    def _get_policies(prod_id):
        return [
            ProductPolicy(account_name="Welcoming", init_amount=1000, renewable_amount=0, expires_in=12345),
            ProductPolicy(account_name="Freemium", init_amount=0, renewable_amount=100),
        ]

    def _get_products(skip, limit):
        return 2, [db_product_1, db_product_2]

    product_repo.get_product_policies.side_effect = _get_policies
    product_repo.get_products.side_effect = _get_products
    mock_product_repo.return_value = product_repo
    product_service = ProductService(session=session)

    # Act
    total, products = product_service.get_all_products()

    # Assert
    assert total == 2 and len(products) == 2
    assert len(products[0].product_policies) == 2 and len(products[1].product_policies) == 2
    assert products[0].name == db_product_1.name and products[1].name == db_product_2.name


@patch("service.product.ProductRepository")
def test_get_product_by_id(mock_product_repo, request) -> None:
    # Arrange
    session = MagicMock()
    product_repo = MagicMock()
    product_id = uuid4()
    db_product = Product(id=product_id, name="Default product", created=12345, updated=12345)

    def _get_policies(prod_id):
        return [
            ProductPolicy(account_name="Welcoming", init_amount=1000, renewable_amount=0, expires_in=12345),
            ProductPolicy(account_name="Freemium", init_amount=0, renewable_amount=100),
        ]

    def _get_by_id(prod_id):
        return db_product

    product_repo.get_product_policies.side_effect = _get_policies
    product_repo.get_by_id.side_effect = _get_by_id
    mock_product_repo.return_value = product_repo
    product_service = ProductService(session=session)

    # Act
    result = product_service.get_product_by_id(product_id=product_id)

    # Assert
    assert result.id == db_product.id and result.name == db_product.name
    assert len(result.product_policies) == 2
