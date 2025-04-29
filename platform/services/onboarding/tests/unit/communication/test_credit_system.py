# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from unittest.mock import MagicMock, patch

import pytest
from grpc_interfaces.credit_system.pb.credit_system_service_pb2 import Product, ProductsList

from communication.credit_system.create_subscription import create_subscription


@pytest.mark.asyncio
@patch("communication.credit_system.create_subscription.CreditSystemClient", autospec=True)
async def test_create_subscription_no_default_product(mock_credits_service_client):
    client = MagicMock()
    mock_credits_service_client.return_value = client
    client.__enter__.return_value = client

    mock_product_response = MagicMock()
    mock_product = MagicMock(id="product-1", name="Not default product")
    mock_product_response.products = [mock_product]

    client.get_all_products.return_value = mock_product_response

    with pytest.raises(RuntimeError):
        await create_subscription("organization_id", "workspace_id", "Not default product")

    client.create_subscription.assert_not_called()


@pytest.mark.asyncio
@patch("communication.credit_system.create_subscription.CreditSystemClient", autospec=True)
async def test_create_subscription_multiple_products(mock_credits_service_client):
    client = MagicMock()
    mock_credits_service_client.return_value = client
    client.__enter__.return_value = client
    mock_product1 = Product(id="product-1", name="Another product", created=12345, updated=12345, product_policies=None)
    mock_product2 = Product(id="product-2", name="Geti Free Tier", created=12345, updated=12345, product_policies=None)
    mock_product_response = ProductsList(products=[mock_product1, mock_product2])
    client.get_all_products.return_value = mock_product_response

    await create_subscription("organization_id", "workspace_id", "Geti Free Tier")

    client.create_subscription.assert_called_once_with(
        organization_id="organization_id", workspace_id="workspace_id", product_id="product-2"
    )
