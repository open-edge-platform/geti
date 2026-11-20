# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.db.schema import MediaDB, OmeChannelViewDB


class OmeChannelViewRepository:
    """Read and atomically replace display views within a project."""

    def __init__(self, project_id: str, db: Session) -> None:
        self.project_id = project_id
        self.db = db

    def get_by_id(self, media_id: str) -> OmeChannelViewDB | None:
        return self.db.scalar(
            select(OmeChannelViewDB)
            .join(MediaDB, MediaDB.id == OmeChannelViewDB.media_id)
            .where(MediaDB.project_id == self.project_id, OmeChannelViewDB.media_id == media_id)
            .execution_options(populate_existing=True)
        )

    def save(self, media_id: str, settings: list[dict[str, object]]) -> None:
        statement = insert(OmeChannelViewDB).values(media_id=media_id, settings=settings)
        self.db.execute(
            statement.on_conflict_do_update(
                index_elements=[OmeChannelViewDB.media_id],
                set_={"settings": statement.excluded.settings, "updated_at": func.current_timestamp()},
            )
        )
        self.db.flush()
