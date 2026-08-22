# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.schema import DatasetViewDB

from .base import BaseRepository


class DatasetViewRepository(BaseRepository[DatasetViewDB]):
    """Repository for dataset view-related database operations."""

    def __init__(self, project_id: str, db: Session) -> None:
        super().__init__(db, DatasetViewDB)
        self.project_id = project_id

    def list_by_project(self) -> Sequence[DatasetViewDB]:
        """List all dataset views belonging to the repository's project."""
        stmt = select(DatasetViewDB).where(DatasetViewDB.project_id == self.project_id)
        return self.db.scalars(stmt).all()
