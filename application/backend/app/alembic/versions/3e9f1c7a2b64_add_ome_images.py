# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""add_ome_images

Revision ID: 3e9f1c7a2b64
Revises: b7e2d94a1f3c
Create Date: 2026-11-02 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3e9f1c7a2b64"
down_revision: str | Sequence[str] | None = "b7e2d94a1f3c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# NOTE: only native SQLite ALTER statements are used on 'media'. A batch (copy-and-move) migration would drop the
# original table, which cascades to every dependent row since migrations run with foreign keys enabled.


def upgrade() -> None:
    """Generalize media parent/leaf columns and add OME image tables."""
    # RENAME COLUMN also rewrites the self-referencing foreign key and the unique constraint definition
    op.alter_column("media", "video_id", new_column_name="parent_id")
    op.drop_index("idx_media_video_id", table_name="media")
    op.create_index("idx_media_parent_id", "media", ["parent_id"], unique=False)
    op.add_column("media", sa.Column("z_index", sa.Integer(), nullable=True))
    op.add_column("media", sa.Column("t_index", sa.Integer(), nullable=True))

    op.create_table(
        "ome_images",
        sa.Column("media_id", sa.Text(), nullable=False),
        sa.Column("container_format", sa.String(length=20), nullable=False),
        sa.Column("size_x", sa.Integer(), nullable=False),
        sa.Column("size_y", sa.Integer(), nullable=False),
        sa.Column("size_z", sa.Integer(), nullable=False),
        sa.Column("size_c", sa.Integer(), nullable=False),
        sa.Column("size_t", sa.Integer(), nullable=False),
        sa.Column("dimension_order", sa.String(length=16), nullable=False),
        sa.Column("pixel_type", sa.String(length=20), nullable=False),
        sa.Column("significant_bits", sa.Integer(), nullable=True),
        sa.Column("series_index", sa.Integer(), nullable=False),
        sa.Column("is_big_tiff", sa.Boolean(), nullable=False),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("channel_mapping", sa.JSON(), nullable=False),
        sa.Column("pyramid_levels", sa.JSON(), nullable=False),
        sa.Column("entrypoint", sa.String(length=255), nullable=True),
        sa.Column("files", sa.JSON(), nullable=False),
        sa.Column("raw_metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("media_id"),
    )
    op.create_table(
        "ome_channel_views",
        sa.Column("media_id", sa.Text(), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("media_id"),
    )


def downgrade() -> None:
    """Drop OME image tables and restore the video-only media parent column. Refuses to run if OME media exist."""
    ome_media_count = (
        op.get_bind()
        .execute(sa.text("SELECT COUNT(*) FROM media WHERE type IN ('ome_image', 'ome_plane')"))
        .scalar_one()
    )
    if ome_media_count:
        raise RuntimeError(
            f"Cannot downgrade: {ome_media_count} OME media exist. Delete them before downgrading, they cannot be "
            "represented in the previous schema."
        )
    op.drop_table("ome_channel_views")
    op.drop_table("ome_images")
    op.drop_column("media", "t_index")
    op.drop_column("media", "z_index")
    op.drop_index("idx_media_parent_id", table_name="media")
    op.alter_column("media", "parent_id", new_column_name="video_id")
    op.create_index("idx_media_video_id", "media", ["video_id"], unique=False)
