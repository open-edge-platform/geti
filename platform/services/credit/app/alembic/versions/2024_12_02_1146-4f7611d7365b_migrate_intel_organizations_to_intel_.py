# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Migrate Intel organizations to Intel Trial product

Revision ID: 4f7611d7365b
Revises: 6a6776e8ee93
Create Date: 2024-12-02 11:46:20.130698+00:00

"""

# DO NOT EDIT MANUALLY EXISTING MIGRATIONS.

from collections.abc import Sequence

import grpc
import os
from alembic import op
from db.model import Subscription
from db.repository.product import ProductRepository
from grpc_interfaces.account_service.client import AccountServiceClient
from service.subscription import SubscriptionService
from sqlalchemy.orm import Session
from utils.enums import SubscriptionStatus
from utils.time import get_current_day

from geti_logger_tools.logger_config import initialize_logger

logger = initialize_logger(__name__)

# revision identifiers, used by Alembic.
revision: str = "4f7611d7365b"
down_revision: str | None = "6a6776e8ee93"
branch_labels: str | (Sequence[str] | None) = None
depends_on: str | (Sequence[str] | None) = None


def upgrade() -> None:
    """
    Migrates active Intel organization to use Intel Trial product instead of regular Geti Free Tier
    """
    if os.environ.get("TESTING_ENV", False):
        # for integration tests to ignore this migration
        return
    with Session(bind=op.get_bind()) as session:
        intel_org_workspace_mapping: dict[str, str] = _get_intel_orgs_and_workspace_ids()
        subscription_service = SubscriptionService(session=session)
        intel_product = ProductRepository(session=session).get_by_name(product_name="Intel Trial")

        for organization_id, workspace_id in intel_org_workspace_mapping.items():
            current_subscription = subscription_service.get_active_subscription(organization_id=organization_id)
            if current_subscription:
                subscription_service.transition(
                    subscription=current_subscription,
                    new_status=SubscriptionStatus.CANCELLED,
                    organization_id=organization_id,
                    _db_session=session,
                )
            new_subscription = Subscription(
                organization_id=organization_id,
                workspace_id=workspace_id,
                product_id=intel_product.id,
                status=SubscriptionStatus.NEW,
                renewal_day_of_month=get_current_day(),
            )
            subscription_service.transition(
                subscription=new_subscription,
                new_status=SubscriptionStatus.ACTIVE,
                organization_id=organization_id,
                _db_session=session,
            )


def downgrade() -> None:
    pass


def _get_intel_orgs_and_workspace_ids() -> dict[str, str]:
    try:
        with AccountServiceClient(metadata_getter=lambda: ()) as client:
            intel_org_ids = client.get_active_intel_organizations_ids()
            org_workspace_mapping = {}
            for org_id in intel_org_ids:
                workspace_id = client.get_default_workspace_id(org_id)
                org_workspace_mapping[org_id] = workspace_id
            return org_workspace_mapping
    except grpc.RpcError:
        logger.exception("Can't fetch Intel organizations from the account service.")
        raise
