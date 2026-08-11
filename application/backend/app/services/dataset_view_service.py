# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.dataset import DatasetStatistics
from app.models.dataset_item import DatasetItem
from app.models.dataset_view import DatasetView
from app.services.dataset_service import DatasetItemFilters

from .base import BaseSessionManagedService


class DatasetViewService(BaseSessionManagedService):
    """
    Service for managing dataset views: named, user-defined subsets of a project's dataset media.

    NOTE: This is a work-in-progress feature. The API surface (routers, schemas, dependencies) is fully wired up,
    but the business logic is not implemented yet; every method below raises ``NotImplementedError``.
    """

    def __init__(self, db_session: Session | None = None) -> None:
        super().__init__(db_session)

    def create_dataset_view(self, project_id: UUID, name: str, media_ids: list[UUID] | None = None) -> DatasetView:
        """Create a new, named dataset view, optionally pre-populated with the given media items."""
        raise NotImplementedError

    def list_dataset_views(self, project_id: UUID) -> list[DatasetView]:
        """List the dataset views belonging to a project."""
        raise NotImplementedError

    def get_dataset_view_by_id(self, project_id: UUID, dataset_view_id: UUID) -> DatasetView:
        """Get a dataset view by its ID."""
        raise NotImplementedError

    def rename_dataset_view(self, project_id: UUID, dataset_view_id: UUID, new_name: str) -> DatasetView:
        """Rename a dataset view."""
        raise NotImplementedError

    def delete_dataset_view(self, project_id: UUID, dataset_view_id: UUID) -> None:
        """Delete a dataset view. This does not affect the underlying media or dataset items."""
        raise NotImplementedError

    def assign_media(self, project_id: UUID, dataset_view_id: UUID, media_ids: list[UUID]) -> None:
        """Assign one or more media items to a dataset view."""
        raise NotImplementedError

    def unassign_media(self, project_id: UUID, dataset_view_id: UUID, media_ids: list[UUID]) -> None:
        """Unassign one or more media items from a dataset view."""
        raise NotImplementedError

    def count_dataset_view_items(
        self, project_id: UUID, dataset_view_id: UUID, filters: DatasetItemFilters | None = None
    ) -> int:
        """Count the dataset items assigned to a dataset view, optionally matching the given filters."""
        raise NotImplementedError

    def list_dataset_view_items(
        self, project_id: UUID, dataset_view_id: UUID, filters: DatasetItemFilters | None = None
    ) -> list[DatasetItem]:
        """List (filter) the dataset items assigned to a dataset view."""
        raise NotImplementedError

    def get_dataset_view_statistics(self, project_id: UUID, dataset_view_id: UUID) -> DatasetStatistics:
        """Get statistics (media & annotation counts) about the items assigned to a dataset view."""
        raise NotImplementedError
