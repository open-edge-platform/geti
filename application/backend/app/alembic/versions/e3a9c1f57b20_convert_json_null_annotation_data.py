# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""convert_json_null_annotation_data_to_sql_null

Revision ID: e3a9c1f57b20
Revises: b7e2d94a1f3c
Create Date: 2026-11-04 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3a9c1f57b20"
down_revision: str | Sequence[str] | None = "b7e2d94a1f3c"

branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace JSON 'null' annotation data, written when annotations were deleted, with SQL NULL."""
    op.execute("UPDATE dataset_items SET annotation_data = NULL WHERE annotation_data = 'null'")


def downgrade() -> None:
    """No-op: SQL NULL and JSON 'null' both deserialize to None, so older versions read the data unchanged."""
