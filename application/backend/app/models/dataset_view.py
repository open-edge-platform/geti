# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from uuid import UUID

from pydantic import model_validator

from app.db.schema import DatasetViewDB
from app.models.base import BaseEntity


class DatasetView(BaseEntity):
    """
    A dataset view is a named, user-defined subset of the media items of a project's dataset.

    Views are independent of each other: the same item may be assigned to multiple views, and unassigning
    an item from a view has no effect on the item itself (it still exists in the project's dataset).

    Attributes:
        id: Unique identifier for the dataset view.
        project_id: Identifier of the project to which the dataset view belongs.
        name: User-assigned name of the dataset view.
        created_at: Timestamp indicating when the dataset view was created.
    """

    id: UUID
    project_id: UUID
    name: str
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_dataset_view(cls, data: object) -> object:
        if isinstance(data, DatasetViewDB):
            return {
                "id": data.id,
                "project_id": data.project_id,
                "name": data.name,
                "created_at": data.created_at,
            }
        return data
