# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.dataset import DatasetStatistics
from app.models.dataset_item import DatasetItem
from app.models.dataset_view import DatasetView
from app.models.media import Media
from app.services.dataset_service import DatasetItemFilters
from app.services.media_service import MediaFilters

from .base import BaseSessionManagedService


class DatasetViewService(BaseSessionManagedService):
    """
    Service for managing dataset views: named, user-defined subsets of a project's dataset media.

    Design notes:
        - Membership (which media belongs to which view) is tracked at the *media* level (images and videos),
          not at the dataset-item level. This allows a video to be assigned to a view immediately upon upload,
          even before any of its frames have been annotated (and therefore before a dataset item exists for it).
        - Media deletion is always a dataset-wide (not view-scoped) operation, handled by ``MediaService`` /
          the existing ``/dataset/media`` endpoints. Deleting a media item removes it from the project's
          dataset entirely, and it is automatically removed from any view it was assigned to (cascading delete).
          Unassigning a media item from a view, on the other hand, only removes it from that view; the media
          itself, and its membership in other views, is unaffected.
        - Uploading media while a specific view is selected is a two-step client-side operation (handled by the
          UI): (1) upload the media via the regular ``/dataset/media`` endpoint, then (2) assign it to the
          selected view via :meth:`assign_media`.

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
        """
        Assign one or more media items (images or videos) to a dataset view, in bulk.

        Assigning a media item that is already part of the view is a no-op for that item. A media item may be
        assigned to multiple views at the same time.
        """
        raise NotImplementedError

    def unassign_media(self, project_id: UUID, dataset_view_id: UUID, media_ids: list[UUID]) -> None:
        """
        Unassign one or more media items from a dataset view, in bulk.

        This only removes the media items from the given view; the media itself is not deleted and remains
        part of the project's dataset (and any other view it is assigned to).
        """
        raise NotImplementedError

    def count_dataset_view_media(
        self, project_id: UUID, dataset_view_id: UUID, filters: MediaFilters | None = None
    ) -> int:
        """Count the media items (images and videos) assigned to a dataset view, optionally matching filters."""
        raise NotImplementedError

    def list_dataset_view_media(
        self, project_id: UUID, dataset_view_id: UUID, filters: MediaFilters | None = None
    ) -> list[Media]:
        """List (filter) the media items (images and videos) assigned to a dataset view."""
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
