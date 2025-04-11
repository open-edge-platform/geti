# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from grpc_interfaces.credit_system.client import CreditSystemClient, ProductsList

from geti_logger_tools.logger_config import initialize_logger

logger = initialize_logger(__name__)


async def create_subscription(organization_id: str, workspace_id: str, product_name: str) -> None:
    """
    Activates the organization's subscription for credits.
    """
    with CreditSystemClient(metadata_getter=lambda: ()) as client:
        response: ProductsList = client.get_all_products()
        product_id = next((product.id for product in response.products if product.name == product_name), None)
        if product_id is None:
            raise RuntimeError(
                f"Couldn't create the credits subscription for the organization {organization_id}: "
                f"requested product not found"
            )
        client.create_subscription(organization_id=organization_id, workspace_id=workspace_id, product_id=product_id)


async def fail_subscription(organization_id: str, workspace_id: str, product_name: str) -> None:
    """Rollbacks the credits subscription by changing its status to failed"""
    with CreditSystemClient(metadata_getter=lambda: ()) as client:
        response: ProductsList = client.get_all_products()
        product_id = next((product.id for product in response.products if product.name == product_name), None)
        if product_id is None:
            raise RuntimeError(
                f"Couldn't mark subscription as failed for the organization {organization_id}: "
                f"requested product not found"
            )
        client.fail_subscription(organization_id=organization_id, workspace_id=workspace_id, product_id=product_id)
