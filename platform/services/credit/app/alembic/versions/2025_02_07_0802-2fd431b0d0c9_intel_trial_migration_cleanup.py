# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Intel Trial migration cleanup

Revision ID: 2fd431b0d0c9
Revises: 4f7611d7365b
Create Date: 2025-02-07 08:02:16.968937+00:00

"""

# DO NOT EDIT MANUALLY EXISTING MIGRATIONS.

from collections.abc import Sequence

import grpc
import os
import sqlalchemy as sa
from alembic import op
from db.model import Subscription
from db.model.product import Product
from db.repository.product import ProductRepository
from grpc_interfaces.account_service.client import AccountServiceClient
from service.subscription import SubscriptionService
from sqlalchemy.orm import Session
from utils.enums import SubscriptionStatus

from geti_logger_tools.logger_config import initialize_logger

logger = initialize_logger(__name__)


# revision identifiers, used by Alembic.
revision: str = '2fd431b0d0c9'
down_revision: str | None = '4f7611d7365b'
branch_labels: str | (Sequence[str] | None) = None
depends_on: str | (Sequence[str] | None) = None


def _cleanup_internal_subscriptions():
    if os.environ.get("TESTING_ENV", False):
        # for integration tests to ignore this migration
        return

    try:
        with AccountServiceClient(metadata_getter=lambda: ()) as client:
            intel_org_ids = client.get_active_intel_organizations_ids()
    except grpc.RpcError:
        logger.exception("Can't fetch Intel organizations from the account service.")
        raise

    with Session(bind=op.get_bind()) as session:
        subscription_service = SubscriptionService(session=session)
        intel_product: Product = ProductRepository(session=session).get_by_name(product_name="Intel Trial")
        default_product: Product = ProductRepository(session=session).get_by_name(product_name="Geti Free Tier")
        for organization_id in intel_org_ids:
            active_default_subscription: Subscription | None = subscription_service.get_active_product_subscription(
                organization_id=organization_id, product_id=default_product.id
            )
            if active_default_subscription:
                subscription_service.transition(
                    subscription=active_default_subscription,
                    new_status=SubscriptionStatus.CANCELLED,
                    organization_id=organization_id,
                    _db_session=session,
                )
                logger.info(f"Default subscription {active_default_subscription.id} for "
                            f"the organization {organization_id} has been successfully cancelled.")
            internal_subscriptions: Sequence[Subscription] = subscription_service.get_product_subscriptions(
                organization_id=organization_id, product_id=intel_product.id
            )
            logger.info(f"Internal subscription(s) for the organization {organization_id}: {internal_subscriptions}")
            cancelled_internal_subscription: Subscription | None = next(
                (sub for sub in internal_subscriptions if sub.status == SubscriptionStatus.CANCELLED), None
            )
            if cancelled_internal_subscription:
                stmt = sa.delete(Subscription).where(Subscription.id == cancelled_internal_subscription.id)
                session.execute(stmt)
                logger.info(f"Deleted internal subscription {cancelled_internal_subscription.id} "
                            f"for the organization {organization_id}.")


def upgrade() -> None:
    """
    Migration ensuring correct cascade deletions and internal subscriptions handling
    """
    op.drop_constraint('AccountBalance_account_id_fkey', 'AccountBalance', type_='foreignkey')
    op.drop_constraint('AccountBalance_snapshot_id_fkey', 'AccountBalance', type_='foreignkey')
    op.create_foreign_key(None, 'AccountBalance', 'CreditAccount', ['account_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'AccountBalance', 'BalanceSnapshot', ['snapshot_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('BalanceSnapshot_subscription_id_fkey', 'BalanceSnapshot', type_='foreignkey')
    op.create_foreign_key(None, 'BalanceSnapshot', 'Subscription', ['subscription_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('CreditAccount_subscription_id_fkey', 'CreditAccount', type_='foreignkey')
    op.create_foreign_key(None, 'CreditAccount', 'Subscription', ['subscription_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('ProductPolicy_product_id_fkey', 'ProductPolicy', type_='foreignkey')
    op.create_foreign_key(None, 'ProductPolicy', 'Product', ['product_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('ProductQuota_product_id_fkey', 'ProductQuota', type_='foreignkey')
    op.create_foreign_key(None, 'ProductQuota', 'Product', ['product_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('SubscriptionQuota_subscription_id_fkey', 'SubscriptionQuota', type_='foreignkey')
    op.create_foreign_key(None, 'SubscriptionQuota', 'Subscription', ['subscription_id'], ['id'], ondelete='CASCADE')
    op.drop_column('Transactions', 'project_name')

    _cleanup_internal_subscriptions()


def downgrade() -> None:
    op.add_column('Transactions', sa.Column('project_name', sa.VARCHAR(length=36), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'SubscriptionQuota', type_='foreignkey')
    op.create_foreign_key('SubscriptionQuota_subscription_id_fkey', 'SubscriptionQuota', 'Subscription', ['subscription_id'], ['id'])
    op.drop_constraint(None, 'ProductQuota', type_='foreignkey')
    op.create_foreign_key('ProductQuota_product_id_fkey', 'ProductQuota', 'Product', ['product_id'], ['id'])
    op.drop_constraint(None, 'ProductPolicy', type_='foreignkey')
    op.create_foreign_key('ProductPolicy_product_id_fkey', 'ProductPolicy', 'Product', ['product_id'], ['id'])
    op.drop_constraint(None, 'CreditAccount', type_='foreignkey')
    op.create_foreign_key('CreditAccount_subscription_id_fkey', 'CreditAccount', 'Subscription', ['subscription_id'], ['id'])
    op.drop_constraint(None, 'BalanceSnapshot', type_='foreignkey')
    op.create_foreign_key('BalanceSnapshot_subscription_id_fkey', 'BalanceSnapshot', 'Subscription', ['subscription_id'], ['id'])
    op.drop_constraint(None, 'AccountBalance', type_='foreignkey')
    op.drop_constraint(None, 'AccountBalance', type_='foreignkey')
    op.create_foreign_key('AccountBalance_snapshot_id_fkey', 'AccountBalance', 'BalanceSnapshot', ['snapshot_id'], ['id'])
    op.create_foreign_key('AccountBalance_account_id_fkey', 'AccountBalance', 'CreditAccount', ['account_id'], ['id'])
