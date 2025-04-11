# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Remove project name from transactions

Revision ID: 441aba2876aa
Revises: cd330231b9ab
Create Date: 2024-05-22 14:28:06.072543+00:00

"""

# DO NOT EDIT MANUALLY EXISTING MIGRATIONS.

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "441aba2876aa"
down_revision: str | None = "cd330231b9ab"
branch_labels: str | (Sequence[str] | None) = None
depends_on: str | (Sequence[str] | None) = None


def upgrade() -> None:
    op.drop_column(table_name="Transactions", column_name="project_name")


def downgrade() -> None:
    op.add_column(table_name="Transactions", column=sa.Column("project_name", sa.String(length=36), nullable=True))
