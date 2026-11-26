# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

from sqlalchemy import Select, case, exists, func, select
from sqlalchemy.orm import InstrumentedAttribute, aliased

from app.db.schema import DatasetItemDB, DatasetItemLabelDB, MediaDB, OmeImageDB
from app.models import DatasetItemAnnotationStatus, MediaType
from app.models.media import CONTAINER_MEDIA_TYPES


def _apply_date_range_filter(
    stmt: Select,
    date_column: InstrumentedAttribute[datetime],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> Select:
    """Apply an (optional) date range filter to a select statement, on the given date column.

    Args:
        stmt: The base SQLAlchemy select statement.
        date_column: The column to filter on (e.g. ``MediaDB.created_at`` or ``DatasetItemDB.created_at``).
        start_date: If given, only rows with ``date_column >= start_date`` are kept.
        end_date: If given, only rows with ``date_column < end_date`` are kept.

    Returns:
        The select statement with the date range condition(s) applied.
    """
    if start_date:
        stmt = stmt.where(date_column >= start_date)
    if end_date:
        stmt = stmt.where(date_column < end_date)
    return stmt


def _apply_annotation_status_filter(stmt: Select, annotation_status: str | None = None) -> Select:
    """Apply annotation status filter to a select statement."""
    match annotation_status:
        case DatasetItemAnnotationStatus.MISSING_ANNOTATIONS:
            stmt = stmt.where(DatasetItemDB.annotation_data.is_(None))
        case DatasetItemAnnotationStatus.WITH_ANNOTATIONS:
            stmt = stmt.where(DatasetItemDB.annotation_data.isnot(None))
    return stmt


def _apply_annotation_status_filter_with_container_support(
    stmt: Select, annotation_status: str | None = None
) -> Select:
    """Apply annotation status filters across video/frame and OME image/plane hierarchies.

    Containers have no dataset item of their own. They match WITH_ANNOTATIONS if any child is annotated,
    and MISSING_ANNOTATIONS while fewer than their total frame/plane count are annotated.

    Args:
        stmt: The base SQLAlchemy select statement, expected to have ``MediaDB`` as its
              primary entity with an outer join to ``DatasetItemDB``.
        annotation_status: One of ``DatasetItemAnnotationStatus`` values, or ``None``
                           to skip filtering.

    Returns:
        The select statement with the annotation status condition applied.
    """
    if annotation_status == DatasetItemAnnotationStatus.WITH_ANNOTATIONS:
        child_alias = aliased(MediaDB)
        annotated_child_exists = exists(
            select(child_alias.id)
            .join(DatasetItemDB, DatasetItemDB.id == child_alias.id)
            .where(
                child_alias.parent_id == MediaDB.id,
                DatasetItemDB.annotation_data.isnot(None),
            )
            .correlate(MediaDB)
        )
        stmt = stmt.where(
            (MediaDB.type.not_in(CONTAINER_MEDIA_TYPES)) & (DatasetItemDB.annotation_data.isnot(None))
            | (MediaDB.type.in_(CONTAINER_MEDIA_TYPES) & annotated_child_exists)
        )
    elif annotation_status == DatasetItemAnnotationStatus.MISSING_ANNOTATIONS:
        child_alias = aliased(MediaDB)
        annotated_child_count = (
            select(func.count(child_alias.id))
            .join(DatasetItemDB, DatasetItemDB.id == child_alias.id)
            .where(
                child_alias.parent_id == MediaDB.id,
                DatasetItemDB.annotation_data.isnot(None),
            )
            .correlate(MediaDB)
            .scalar_subquery()
        )
        plane_count = (
            select(OmeImageDB.size_z * OmeImageDB.size_t)
            .where(OmeImageDB.media_id == MediaDB.id)
            .correlate(MediaDB)
            .scalar_subquery()
        )
        total_child_count = case((MediaDB.type == MediaType.OME_IMAGE, plane_count), else_=MediaDB.frame_count)
        stmt = stmt.where(
            (MediaDB.type.not_in(CONTAINER_MEDIA_TYPES)) & (DatasetItemDB.annotation_data.is_(None))
            | (MediaDB.type.in_(CONTAINER_MEDIA_TYPES) & (annotated_child_count < total_child_count))
        )
    return stmt


def _apply_label_filter_with_container_support(stmt: Select, label_ids: list[str] | None = None) -> Select:
    """Apply a label filter across video/frame and OME image/plane hierarchies.

    Containers match if any child carries a requested label; images and leaves match their own dataset items.

    Args:
        stmt: The base SQLAlchemy select statement, expected to have ``MediaDB`` as its
              primary entity.
        label_ids: The list of label ids to filter by, or ``None``/empty to skip filtering.

    Returns:
        The select statement with the label condition applied.
    """
    if not label_ids:
        return stmt

    own_label_exists = exists(
        select(DatasetItemLabelDB.dataset_item_id)
        .where(
            DatasetItemLabelDB.dataset_item_id == MediaDB.id,
            DatasetItemLabelDB.label_id.in_(label_ids),
        )
        .correlate(MediaDB)
    )

    child_alias = aliased(MediaDB)
    child_label_exists = exists(
        select(child_alias.id)
        .join(DatasetItemLabelDB, DatasetItemLabelDB.dataset_item_id == child_alias.id)
        .where(
            child_alias.parent_id == MediaDB.id,
            DatasetItemLabelDB.label_id.in_(label_ids),
        )
        .correlate(MediaDB)
    )

    return stmt.where(
        (MediaDB.type.not_in(CONTAINER_MEDIA_TYPES) & own_label_exists)
        | (MediaDB.type.in_(CONTAINER_MEDIA_TYPES) & child_label_exists)
    )


def _apply_subset_filter(stmt: Select, subsets: list[str] | None = None) -> Select:
    """Apply subset filter to a select statement."""
    if subsets:
        stmt = stmt.where(DatasetItemDB.subset.in_(subsets))
    return stmt


def _apply_subset_filter_with_container_support(stmt: Select, subsets: list[str] | None = None) -> Select:
    """Apply a subset filter across video/frame and OME image/plane hierarchies.

    Containers match if any child belongs to a requested subset; images and leaves match their own dataset items.

    Args:
        stmt: The base SQLAlchemy select statement, expected to have ``MediaDB`` as its
              primary entity.
        subsets: The list of subsets to filter by, or ``None``/empty to skip filtering.

    Returns:
        The select statement with the subset condition applied.
    """
    if not subsets:
        return stmt

    own_subset_exists = exists(
        select(DatasetItemDB.id)
        .where(
            DatasetItemDB.id == MediaDB.id,
            DatasetItemDB.subset.in_(subsets),
        )
        .correlate(MediaDB)
    )

    child_alias = aliased(MediaDB)
    child_subset_exists = exists(
        select(child_alias.id)
        .join(DatasetItemDB, DatasetItemDB.id == child_alias.id)
        .where(
            child_alias.parent_id == MediaDB.id,
            DatasetItemDB.subset.in_(subsets),
        )
        .correlate(MediaDB)
    )

    return stmt.where(
        (MediaDB.type.not_in(CONTAINER_MEDIA_TYPES) & own_subset_exists)
        | (MediaDB.type.in_(CONTAINER_MEDIA_TYPES) & child_subset_exists)
    )
