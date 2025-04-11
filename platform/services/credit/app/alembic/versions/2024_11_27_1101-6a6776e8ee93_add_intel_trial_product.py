# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Add Intel Trial product

Revision ID: 6a6776e8ee93
Revises: b78cd74b4c84
Create Date: 2024-11-27 11:01:39.767142+00:00

"""

# DO NOT EDIT MANUALLY EXISTING MIGRATIONS.

import os
from collections.abc import Sequence

from alembic import op
from db.model.product import Product, ProductPolicy, ProductQuota
from sqlalchemy.orm import Session
from utils.enums import QuotaType

# revision identifiers, used by Alembic.
revision: str = '6a6776e8ee93'
down_revision: str | None = 'b78cd74b4c84'
branch_labels: str | (Sequence[str] | None) = None
depends_on: str | (Sequence[str] | None) = None


def upgrade() -> None:
    with Session(bind=op.get_bind()) as session:
        internal_product = Product(name="Intel Trial")
        session.add(internal_product)
        session.flush()
        welcoming_credits_policy = ProductPolicy(
            product_id=internal_product.id,
            account_name="Internal Welcoming Credits",
            init_amount=int(os.getenv("INTERNAL_WELCOMING_CREDITS_AMOUNT", "10000")),
            renewable_amount=0,
            expires_in=31 * 24 * 60 * 60 * 1000,  # 31 days in milliseconds
        )
        freemium_credits_policy = ProductPolicy(
            product_id=internal_product.id,
            account_name="Internal Freemium Credits",
            init_amount=0,
            renewable_amount=int(os.getenv("INTERNAL_RENEWABLE_CREDITS_AMOUNT", "10000")),
        )
        default_product_quota_acc_svc = ProductQuota(
            product_id=internal_product.id,
            service_name="account service",
            quota_name="Max number of users per organization",
            quota_type=QuotaType.MAX_USERS_COUNT,
            limit=5,
        )
        default_product_quota_trainings = ProductQuota(
            product_id=internal_product.id,
            service_name="trainings",
            quota_name="Max number of concurrent training jobs",
            quota_type=QuotaType.MAX_TRAINING_JOBS,
            limit=10,
        )
        session.add(welcoming_credits_policy)
        session.add(freemium_credits_policy)
        session.add(default_product_quota_acc_svc)
        session.add(default_product_quota_trainings)
        session.commit()


def downgrade() -> None:
    pass
