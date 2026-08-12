# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.api.dependencies import get_dataset_view, get_dataset_view_service, get_project
from app.api.schemas.dataset import DatasetStatisticsView
from app.api.schemas.dataset_item import DatasetItemsWithPagination, DatasetItemView
from app.api.schemas.dataset_view import (
    AssignMediaToDatasetView,
    DatasetViewCreate,
    DatasetViewUpdateName,
    DatasetViewView,
    UnassignMediaFromDatasetView,
)
from app.api.schemas.media import MediaViewAdapter, MediaWithPagination
from app.api.validators import ProjectID, normalize_datetime_to_utc
from app.core.models import Pagination
from app.models import DatasetItemAnnotationStatus, DatasetItemSubset, Project
from app.models.dataset_item import DatasetItemSortBy
from app.models.dataset_view import DatasetView
from app.models.media import MediaSortBy, SortDirection
from app.services import DatasetViewService
from app.services.dataset_service import DatasetItemFilters
from app.services.media_service import MediaFilters

router = APIRouter(prefix="/api/projects/{project_id}/dataset_views", tags=["Dataset Views"])

DEFAULT_DATASET_ITEMS_NUMBER_RETURNED = 10
MAX_DATASET_ITEMS_NUMBER_RETURNED = 100


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Dataset view successfully created", "model": DatasetViewView},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid project ID or request body"},
        status.HTTP_404_NOT_FOUND: {"description": "Project not found"},
        status.HTTP_409_CONFLICT: {"description": "A dataset view with the same name already exists"},
    },
)
def create_dataset_view(
    project: Annotated[Project, Depends(get_project)],
    dataset_view_create: Annotated[DatasetViewCreate, Body()],
    dataset_view_service: Annotated[DatasetViewService, Depends(get_dataset_view_service)],
) -> DatasetViewView:
    """Create a new, named dataset view. The view may be created empty or pre-populated with selected media."""
    dataset_view = dataset_view_service.create_dataset_view(
        project_id=project.id,
        name=dataset_view_create.name,
        media_ids=dataset_view_create.media_ids,
    )
    return DatasetViewView.model_validate(dataset_view, from_attributes=True)


@router.get(
    "",
    response_model=list[DatasetViewView],
    responses={
        status.HTTP_200_OK: {"description": "List of available dataset views"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid project ID"},
        status.HTTP_404_NOT_FOUND: {"description": "Project not found"},
    },
)
def list_dataset_views(
    project: Annotated[Project, Depends(get_project)],
    dataset_view_service: Annotated[DatasetViewService, Depends(get_dataset_view_service)],
) -> list[DatasetViewView]:
    """List the dataset views defined in a project."""
    return [
        DatasetViewView.model_validate(dataset_view, from_attributes=True)
        for dataset_view in dataset_view_service.list_dataset_views(project_id=project.id)
    ]


@router.get(
    "/{dataset_view_id}",
    responses={
        status.HTTP_200_OK: {"description": "Dataset view found", "model": DatasetViewView},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid project or dataset view ID"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or dataset view not found"},
    },
)
def get_dataset_view_details(
    dataset_view: Annotated[DatasetView, Depends(get_dataset_view)],
) -> DatasetViewView:
    """Get information about a specific dataset view."""
    return DatasetViewView.model_validate(dataset_view, from_attributes=True)


@router.patch(
    "/{dataset_view_id}",
    responses={
        status.HTTP_200_OK: {"description": "Dataset view successfully renamed", "model": DatasetViewView},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid project or dataset view ID"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or dataset view not found"},
        status.HTTP_409_CONFLICT: {"description": "A dataset view with the same name already exists"},
    },
)
def rename_dataset_view(
    project: Annotated[Project, Depends(get_project)],
    dataset_view: Annotated[DatasetView, Depends(get_dataset_view)],
    dataset_view_update_name: Annotated[DatasetViewUpdateName, Body(description="Updated dataset view name")],
    dataset_view_service: Annotated[DatasetViewService, Depends(get_dataset_view_service)],
) -> DatasetViewView:
    """Rename a dataset view."""
    updated = dataset_view_service.rename_dataset_view(
        project_id=project.id, dataset_view_id=dataset_view.id, new_name=dataset_view_update_name.name
    )
    return DatasetViewView.model_validate(updated, from_attributes=True)


@router.delete(
    "/{dataset_view_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Dataset view successfully deleted"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid project or dataset view ID"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or dataset view not found"},
    },
)
def delete_dataset_view(
    project: Annotated[Project, Depends(get_project)],
    dataset_view: Annotated[DatasetView, Depends(get_dataset_view)],
    dataset_view_service: Annotated[DatasetViewService, Depends(get_dataset_view_service)],
) -> None:
    """
    Delete a dataset view.

    This operation only removes the view and its item assignments; it does NOT delete the underlying media
    or dataset items, which remain part of the project's main dataset.
    """
    dataset_view_service.delete_dataset_view(project_id=project.id, dataset_view_id=dataset_view.id)


@router.post(
    "/{dataset_view_id}/media:assign",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Media successfully assigned to the dataset view"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid project, dataset view or media ID"},
        status.HTTP_404_NOT_FOUND: {"description": "Project, dataset view or media not found"},
    },
)
def assign_media_to_dataset_view(
    project: Annotated[Project, Depends(get_project)],
    dataset_view: Annotated[DatasetView, Depends(get_dataset_view)],
    assign_media: Annotated[AssignMediaToDatasetView, Body()],
    dataset_view_service: Annotated[DatasetViewService, Depends(get_dataset_view_service)],
) -> None:
    """Assign one or more media items (in bulk) to a dataset view."""
    dataset_view_service.assign_media(
        project_id=project.id, dataset_view_id=dataset_view.id, media_ids=assign_media.media_ids
    )


@router.post(
    "/{dataset_view_id}/media:unassign",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Media successfully unassigned from the dataset view"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid project, dataset view or media ID"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or dataset view not found"},
    },
)
def unassign_media_from_dataset_view(
    project: Annotated[Project, Depends(get_project)],
    dataset_view: Annotated[DatasetView, Depends(get_dataset_view)],
    unassign_media: Annotated[UnassignMediaFromDatasetView, Body()],
    dataset_view_service: Annotated[DatasetViewService, Depends(get_dataset_view_service)],
) -> None:
    """Unassign one or more media items (in bulk) from a dataset view. The media itself is not affected."""
    dataset_view_service.unassign_media(
        project_id=project.id, dataset_view_id=dataset_view.id, media_ids=unassign_media.media_ids
    )


@router.get(
    "/{dataset_view_id}/items",
    responses={
        status.HTTP_200_OK: {
            "description": "List of dataset items assigned to the dataset view, matching the filters",
            "model": DatasetItemsWithPagination,
        },
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid project or dataset view ID"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or dataset view not found"},
    },
)
def filter_dataset_view_items(  # noqa: PLR0913
    project: Annotated[Project, Depends(get_project)],
    dataset_view: Annotated[DatasetView, Depends(get_dataset_view)],
    dataset_view_service: Annotated[DatasetViewService, Depends(get_dataset_view_service)],
    limit: Annotated[int, Query(ge=1, le=MAX_DATASET_ITEMS_NUMBER_RETURNED)] = DEFAULT_DATASET_ITEMS_NUMBER_RETURNED,
    offset: Annotated[int, Query(ge=0, le=2_147_483_647)] = 0,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    annotation_status: Annotated[DatasetItemAnnotationStatus | None, Query()] = None,
    labels: Annotated[list[UUID] | None, Query()] = None,
    subsets: Annotated[list[DatasetItemSubset] | None, Query()] = None,
    sort_by: Annotated[DatasetItemSortBy, Query()] = DatasetItemSortBy.CREATION_DATE,
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.DESC,
) -> DatasetItemsWithPagination:
    """
    List (filter) the dataset items assigned to a dataset view. This endpoint supports pagination and accepts the
    same filtering parameters as the main dataset items listing endpoint.
    """
    start_date = normalize_datetime_to_utc(start_date)
    end_date = normalize_datetime_to_utc(end_date)

    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Start date must be before end date."
        )
    subset_values = [item.value for item in subsets] if subsets else None
    filters = DatasetItemFilters(
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date,
        annotation_status=annotation_status,
        label_ids=labels,
        subsets=subset_values,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    total = dataset_view_service.count_dataset_view_items(
        project_id=project.id, dataset_view_id=dataset_view.id, filters=filters
    )
    dataset_items = dataset_view_service.list_dataset_view_items(
        project_id=project.id, dataset_view_id=dataset_view.id, filters=filters
    )
    return DatasetItemsWithPagination(
        items=[DatasetItemView.model_validate(dataset_item, from_attributes=True) for dataset_item in dataset_items],
        pagination=Pagination(
            limit=limit,
            offset=offset,
            total=total,
            count=len(dataset_items),
        ),
    )


@router.get(
    "/{dataset_view_id}/media",
    responses={
        status.HTTP_200_OK: {
            "description": "List of media assigned to the dataset view, matching the filters",
            "model": MediaWithPagination,
        },
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid project or dataset view ID"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or dataset view not found"},
    },
)
def filter_dataset_view_media(  # noqa: PLR0913
    project: Annotated[Project, Depends(get_project)],
    dataset_view: Annotated[DatasetView, Depends(get_dataset_view)],
    dataset_view_service: Annotated[DatasetViewService, Depends(get_dataset_view_service)],
    limit: Annotated[int, Query(ge=1, le=MAX_DATASET_ITEMS_NUMBER_RETURNED)] = DEFAULT_DATASET_ITEMS_NUMBER_RETURNED,
    offset: Annotated[int, Query(ge=0, le=2_147_483_647)] = 0,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    annotation_status: Annotated[DatasetItemAnnotationStatus | None, Query()] = None,
    labels: Annotated[list[UUID] | None, Query()] = None,
    subsets: Annotated[list[DatasetItemSubset] | None, Query()] = None,
    sort_by: Annotated[MediaSortBy, Query()] = MediaSortBy.UPLOAD_DATE,
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.DESC,
) -> MediaWithPagination:
    """
    List (filter) the media (images and videos) assigned to a dataset view. This endpoint supports pagination
    and accepts the same filtering parameters as the main dataset media listing endpoint. Unlike the
    '/items' endpoint, this one also includes media (e.g. freshly uploaded videos) that do not yet have an
    associated dataset item.
    """
    start_date = normalize_datetime_to_utc(start_date)
    end_date = normalize_datetime_to_utc(end_date)

    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Start date must be before end date."
        )
    subset_values = [item.value for item in subsets] if subsets else None
    filters = MediaFilters(
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date,
        annotation_status=annotation_status,
        label_ids=labels,
        subsets=subset_values,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    total = dataset_view_service.count_dataset_view_media(
        project_id=project.id, dataset_view_id=dataset_view.id, filters=filters
    )
    media_list = dataset_view_service.list_dataset_view_media(
        project_id=project.id, dataset_view_id=dataset_view.id, filters=filters
    )
    return MediaWithPagination(
        items=[MediaViewAdapter.validate_python(media, from_attributes=True) for media in media_list],
        pagination=Pagination(
            limit=limit,
            offset=offset,
            total=total,
            count=len(media_list),
        ),
    )


@router.get(
    "/{dataset_view_id}/statistics",
    responses={
        status.HTTP_200_OK: {"description": "Dataset view statistics retrieved", "model": DatasetStatisticsView},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid project or dataset view ID"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or dataset view not found"},
    },
)
def get_dataset_view_statistics(
    project_id: ProjectID,
    dataset_view: Annotated[DatasetView, Depends(get_dataset_view)],
    dataset_view_service: Annotated[DatasetViewService, Depends(get_dataset_view_service)],
) -> DatasetStatisticsView:
    """Get statistics about the number of media and annotations assigned to a dataset view."""
    dataset_view_statistics = dataset_view_service.get_dataset_view_statistics(
        project_id=project_id, dataset_view_id=dataset_view.id
    )
    return DatasetStatisticsView.model_validate(dataset_view_statistics, from_attributes=True)
