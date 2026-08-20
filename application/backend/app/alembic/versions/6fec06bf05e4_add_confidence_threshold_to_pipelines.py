# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""add_confidence_threshold_to_pipelines

Revision ID: 6fec06bf05e4
Revises: 4ff59e636ff0
Create Date: 2026-08-18 14:01:13.960034

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6fec06bf05e4"
down_revision: str | Sequence[str] | None = "4ff59e636ff0"

branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the 'inference' configuration column to the pipelines table."""
    # A server default is required: SQLite rejects a NOT NULL column without one when rows already exist.
    op.add_column("pipelines", sa.Column("inference", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))


def downgrade() -> None:
    """Drop the 'inference' configuration column from the pipelines table."""
    with op.batch_alter_table("pipelines") as batch_op:
        batch_op.drop_column("inference")
