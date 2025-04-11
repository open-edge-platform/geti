# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Initial migration

Revision ID: cd330231b9ab
Revises:
Create Date: 2024-05-21 18:49:18.132888+00:00

"""

# DO NOT EDIT MANUALLY EXISTING MIGRATIONS.

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from db.model.custom_types import UnixTimestampInMilliseconds
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "cd330231b9ab"
down_revision: str | None = None
branch_labels: str | (Sequence[str] | None) = None
depends_on: str | (Sequence[str] | None) = None


def upgrade() -> None:  # noqa: D103
    op.create_table(
        "Product",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=36), nullable=False),
        sa.Column("created", UnixTimestampInMilliseconds(), nullable=False),
        sa.Column("updated", UnixTimestampInMilliseconds(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("product_name_idx", "Product", ["name"], unique=False, postgresql_using="btree")

    op.create_table(
        "ProductPolicy",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("account_name", sa.String(length=36), nullable=False),
        sa.Column("init_amount", sa.Integer(), nullable=False),
        sa.Column("renewable_amount", sa.Integer(), nullable=True),
        sa.Column("expires_in", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["Product.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "product_policy_product_id_idx", "ProductPolicy", ["product_id"], unique=False, postgresql_using="btree"
    )

    op.create_table(
        "Subscription",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("renewal_day_of_month", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=9), nullable=False),
        sa.Column("created", UnixTimestampInMilliseconds(), nullable=False),
        sa.Column("updated", UnixTimestampInMilliseconds(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["Product.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "subscription_organization_id_idx", "Subscription", ["organization_id"], unique=False, postgresql_using="btree"
    )

    op.create_table(
        "BalanceSnapshot",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("date", UnixTimestampInMilliseconds(), nullable=False),
        sa.Column("subscription_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["subscription_id"], ["Subscription.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "snapshot_subsc_id_date_idx",
        "BalanceSnapshot",
        ["subscription_id", "date"],
        unique=False,
        postgresql_using="btree",
    )

    op.create_table(
        "CreditAccount",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("subscription_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.Enum("asset", "lease", "saas", name="account_type"), nullable=False),
        sa.Column("renewable_amount", sa.Integer(), nullable=True),
        sa.Column("created", UnixTimestampInMilliseconds(), nullable=False),
        sa.Column("updated", UnixTimestampInMilliseconds(), nullable=False),
        sa.Column("expires", UnixTimestampInMilliseconds(), nullable=True),
        sa.ForeignKeyConstraint(["subscription_id"], ["Subscription.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "credit_account_subscription_id_idx",
        "CreditAccount",
        ["subscription_id"],
        unique=False,
        postgresql_using="btree",
    )

    op.create_table(
        "AccountBalance",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_id", sa.BigInteger(), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("incoming_balance", sa.BigInteger(), nullable=False),
        sa.Column("available_balance", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["CreditAccount.id"]),
        sa.ForeignKeyConstraint(["snapshot_id"], ["BalanceSnapshot.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "Transactions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tx_id", sa.String(length=36), nullable=False),
        sa.Column("tx_group_id", sa.String(length=36), nullable=True),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("debit", sa.Integer(), nullable=True),
        sa.Column("credit", sa.Integer(), nullable=True),
        sa.Column("created", UnixTimestampInMilliseconds(), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("project_name", sa.String(length=36), nullable=True),
        sa.Column("service_name", sa.String(length=36), nullable=True),
        sa.Column("requests", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["CreditAccount.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "transactions_created_brin_idx",
        "Transactions",
        ["created"],
        unique=False,
        postgresql_using="brin",
        postgresql_with={"pages_per_range": 128},
    )
    op.create_index(
        "transactions_group_id_idx", "Transactions", ["tx_group_id"], unique=False, postgresql_using="btree"
    )


def downgrade() -> None:  # noqa: D103
    op.drop_index(
        "transactions_created_brin_idx",
        table_name="Transactions",
        postgresql_using="brin",
        postgresql_with={"pages_per_range": 128},
    )
    op.drop_index("transactions_group_id_idx", table_name="Transactions", postgresql_using="btree")
    op.drop_table("Transactions")
    op.drop_table("AccountBalance")
    op.drop_index("credit_account_subscription_id_idx", table_name="CreditAccount", postgresql_using="btree")
    op.drop_table("CreditAccount")
    op.drop_index("snapshot_subsc_id_date_idx", table_name="BalanceSnapshot", postgresql_using="btree")
    op.drop_table("BalanceSnapshot")
    op.drop_index("subscription_organization_id_idx", table_name="Subscription", postgresql_using="btree")
    op.drop_table("Subscription")
    op.drop_index("product_policy_product_id_idx", table_name="ProductPolicy", postgresql_using="btree")
    op.drop_table("ProductPolicy")
    op.drop_index("product_name_idx", table_name="Product", postgresql_using="btree")
    op.drop_table("Product")
