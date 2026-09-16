# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""add_dataset_view_id_to_dataset_revisions

Revision ID: 8c41d7b2e905
Revises: 6fec06bf05e4
Create Date: 2026-09-16 09:12:44.115204

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c41d7b2e905"
down_revision: str | Sequence[str] | None = "6fec06bf05e4"

branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the 'dataset_view_id' column to the dataset_revisions table."""
    # SQLite cannot add a column with a foreign key through a plain ALTER TABLE, hence the batch mode.
    with op.batch_alter_table("dataset_revisions") as batch_op:
        batch_op.add_column(sa.Column("dataset_view_id", sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            "fk_dataset_revisions_dataset_view_id",
            "dataset_views",
            ["dataset_view_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Drop the 'dataset_view_id' column from the dataset_revisions table."""
    with op.batch_alter_table("dataset_revisions") as batch_op:
        batch_op.drop_constraint("fk_dataset_revisions_dataset_view_id", type_="foreignkey")
        batch_op.drop_column("dataset_view_id")
