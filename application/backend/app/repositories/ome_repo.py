# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.schema import MediaDB, OmeChannelViewDB, OmeImageDB


class OmeImageRepository:
    """Repository for the structure of OME images and their display settings, scoped to a project."""

    def __init__(self, project_id: str, db: Session):
        self.project_id = project_id
        self.db = db

    def get_info(self, media_id: str) -> OmeImageDB | None:
        stmt = (
            select(OmeImageDB)
            .join(MediaDB, MediaDB.id == OmeImageDB.media_id)
            .where(OmeImageDB.media_id == media_id, MediaDB.project_id == self.project_id)
        )
        return self.db.scalar(stmt)

    def save_info(self, ome_image: OmeImageDB) -> OmeImageDB:
        ome_image.updated_at = datetime.now(UTC)
        self.db.add(ome_image)
        self.db.flush()
        return ome_image

    def get_channel_view(self, media_id: str) -> OmeChannelViewDB | None:
        stmt = (
            select(OmeChannelViewDB)
            .join(MediaDB, MediaDB.id == OmeChannelViewDB.media_id)
            .where(OmeChannelViewDB.media_id == media_id, MediaDB.project_id == self.project_id)
        )
        return self.db.scalar(stmt)

    def save_channel_view(self, media_id: str, settings: list[dict]) -> OmeChannelViewDB:
        channel_view = self.get_channel_view(media_id)
        if channel_view is None:
            channel_view = OmeChannelViewDB(media_id=media_id)
        channel_view.settings = settings
        channel_view.updated_at = datetime.now(UTC)
        self.db.add(channel_view)
        self.db.flush()
        return channel_view
