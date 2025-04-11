# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import grpc

from db.model import Subscription
from dependencies import get_session
from exceptions.custom_exceptions import NoDatabaseResult
from geti_logger_tools.logger_config import initialize_logger
from grpc_interfaces.account_service.client import AccountServiceClient
from service.product import ProductService
from service.subscription import SubscriptionService
from utils.enums import SubscriptionStatus
from utils.time import get_current_day

DEFAULT_PRODUCT_NAME = "Geti Free Tier"

logger = initialize_logger(__name__)


def get_organizations_and_workspaces_ids() -> dict[str, str]:
    """
    Fetches the existing active organizations and their default workspaces using the account service gRPC API client.
    Returns a dictionary containing organization ids as keys and workspace ids as values.
    """
    try:
        with AccountServiceClient(metadata_getter=lambda: ()) as client:
            organizations = client.get_all_organizations()
            org_ids = [org.get("id", "") for org in organizations if org.get("status") == "ACT"]
            logger.info(f"Active organizations from the account service: '{org_ids}'")
            return {org_id: client.get_default_workspace_id(org_id) for org_id in org_ids}

    except grpc.RpcError:
        logger.exception("Can't fetch organizations from the account service.")
        raise


def subscribe_existing_organizations() -> None:
    """
    Subscribes all active organizations to the default Geti Free Tier product
    in case they are missing an active subscription
    """
    orgs_and_workspaces_ids: dict[str, str] = get_organizations_and_workspaces_ids()
    with next(get_session()) as db_session:
        try:
            default_product_id = ProductService(db_session).get_product_by_name(DEFAULT_PRODUCT_NAME).id
        except NoDatabaseResult:
            raise RuntimeError(
                "Couldn't create the default subscription for the existing organizations: default product not found"
            )
        subscription_service = SubscriptionService(db_session)
        for organization_id, workspace_id in orgs_and_workspaces_ids.items():
            org_active_subscription = subscription_service.get_active_subscription(organization_id=organization_id)
            if org_active_subscription:
                logger.info(
                    f"Organization {organization_id} is already subscribed to the product"
                    f" {org_active_subscription.product_id}, skipping."
                )
                continue

            init_subscription = Subscription(
                organization_id=organization_id,
                workspace_id=workspace_id,
                product_id=default_product_id,
                renewal_day_of_month=get_current_day(),
                status=SubscriptionStatus.NEW,
            )
            subscription_service.transition(
                subscription=init_subscription,
                new_status=SubscriptionStatus.ACTIVE,
                organization_id=organization_id,
                _db_session=db_session,
            )
            logger.info(
                f"Organization {organization_id} has been successfully subscribed to the default product "
                f"{DEFAULT_PRODUCT_NAME}"
            )
