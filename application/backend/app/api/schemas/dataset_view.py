# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.models import BaseRequiredIDModel


class DatasetViewCreate(BaseModel):
    """Schema for creating a new dataset view."""

    name: str = Field(..., description="Name to assign to the new dataset view")
    media_ids: list[UUID] | None = Field(
        None,
        description="Optional list of media IDs to assign to the view upon creation. "
        "If unspecified, the view is created empty.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Canada signs",
                "media_ids": ["d476573e-d43c-42a6-9327-199a9aa75c33", "bbb782b7-8322-44e8-b6a9-90a5c9ee4bad"],
            }
        }
    }


class DatasetViewUpdateName(BaseModel):
    """Schema for renaming a dataset view."""

    name: str = Field(..., description="New name to assign to the dataset view")

    model_config = {"json_schema_extra": {"example": {"name": "Canada signs (daytime)"}}}


class DatasetViewView(BaseRequiredIDModel):
    """A named, user-defined subset of the media items of a project's dataset."""

    project_id: UUID = Field(..., description="Unique identifier of the project the dataset view belongs to")
    name: str = Field(..., description="Name of the dataset view")
    created_at: datetime = Field(..., description="Timestamp when the dataset view was created")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "63f983fe-f2c7-4054-a0b1-6aab8a355a12",
                "project_id": "7b073838-99d3-42ff-9018-4e901eb047fc",
                "name": "Canada signs",
                "created_at": "2026-01-01T00:00:00Z",
            }
        }
    }


class AssignMediaToDatasetView(BaseModel):
    """Schema for bulk assigning one or more media items to a dataset view."""

    media_ids: list[UUID] = Field(..., description="List of media IDs to assign to the dataset view")

    model_config = {
        "json_schema_extra": {
            "example": {"media_ids": ["d476573e-d43c-42a6-9327-199a9aa75c33", "bbb782b7-8322-44e8-b6a9-90a5c9ee4bad"]}
        }
    }


class UnassignMediaFromDatasetView(BaseModel):
    """Schema for bulk unassigning one or more media items from a dataset view."""

    media_ids: list[UUID] = Field(..., description="List of media IDs to unassign from the dataset view")

    model_config = {
        "json_schema_extra": {
            "example": {"media_ids": ["d476573e-d43c-42a6-9327-199a9aa75c33", "bbb782b7-8322-44e8-b6a9-90a5c9ee4bad"]}
        }
    }
