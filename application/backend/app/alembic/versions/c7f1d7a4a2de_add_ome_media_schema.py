# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""add_ome_media_schema

Revision ID: c7f1d7a4a2de
Revises: b7e2d94a1f3c
Create Date: 2026-11-03 13:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7f1d7a4a2de"
down_revision: str | Sequence[str] | None = "b7e2d94a1f3c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index("idx_media_video_id", table_name="media")

    with op.batch_alter_table("media") as batch_op:
        batch_op.alter_column("video_id", new_column_name="parent_id", existing_type=sa.Text())
        batch_op.add_column(sa.Column("z_index", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("t_index", sa.Integer(), nullable=True))

    with op.batch_alter_table("media") as batch_op:
        batch_op.create_unique_constraint("uq_parent_id_frame_index", ["parent_id", "frame_index"])

    op.create_index("idx_media_parent_id", "media", ["parent_id"], unique=False)

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
    """Downgrade schema."""
    bind = op.get_bind()
    ome_image_count = bind.execute(sa.text("SELECT COUNT(*) FROM ome_images")).scalar_one()
    if ome_image_count > 0:
        raise RuntimeError("Cannot downgrade while OME media exists. Remove rows from ome_images first.")

    op.drop_table("ome_channel_views")
    op.drop_table("ome_images")

    op.drop_index("idx_media_parent_id", table_name="media")

    with op.batch_alter_table("media") as batch_op:
        batch_op.drop_column("t_index")
        batch_op.drop_column("z_index")
        batch_op.alter_column("parent_id", new_column_name="video_id", existing_type=sa.Text())

    with op.batch_alter_table("media") as batch_op:
        batch_op.create_unique_constraint("uq_video_id_frame_index", ["video_id", "frame_index"])

    op.create_index("idx_media_video_id", "media", ["video_id"], unique=False)
