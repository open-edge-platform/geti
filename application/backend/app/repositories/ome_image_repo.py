# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.schema import MediaDB, OmeImageDB


class OmeImageRepository:
    """Persist structural OME metadata scoped to a project's media."""

    def __init__(self, project_id: str, db: Session) -> None:
        self.project_id = project_id
        self.db = db

    def get_by_id(self, media_id: str) -> OmeImageDB | None:
        return self.db.scalar(
            select(OmeImageDB)
            .join(MediaDB, MediaDB.id == OmeImageDB.media_id)
            .where(MediaDB.project_id == self.project_id, OmeImageDB.media_id == media_id)
        )

    def save(self, item: OmeImageDB) -> None:
        self.db.add(item)
        self.db.flush()
