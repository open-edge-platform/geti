# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from io import BytesIO
from unittest.mock import patch
from uuid import UUID, uuid4

import numpy as np
import pytest
import tifffile
from PIL import Image
from sqlalchemy import func, select

from app.datumaro_converter import SampleMode
from app.db.schema import DatasetItemDB, DatasetItemLabelDB, DatasetViewItemDB, MediaDB, OmeImageDB
from app.models import DatasetItemAnnotation, DatasetItemAnnotationStatus, DatasetItemSubset, LabelReference, Rectangle
from app.models.media import LEAF_MEDIA_TYPES, ImageFormat, MediaType
from app.models.ome import OmeChannelSettings
from app.services.base import ResourceNotFoundError
from app.services.dataset_service import UnsupportedDatasetMediaError
from app.services.media_service import MediaFilters
from app.services.ome.rendering import OmeRenderingService


@pytest.fixture
def ome_annotation(ome_ingest, db_session, fxt_db_labels, fxt_project_service):
    service, project_id = ome_ingest
    for label in fxt_db_labels:
        label.project_id = str(project_id)
    db_session.add_all(fxt_db_labels)
    db_session.flush()
    payload = BytesIO()
    pixels = np.arange(2 * 13 * 3 * 8 * 10, dtype=np.uint16).reshape(2, 13, 3, 8, 10)
    tifffile.imwrite(payload, pixels, ome=True, metadata={"axes": "TZCYX"}, photometric="minisblack")
    payload.seek(0)
    image = service.create_ome_image(project_id, "specimen", ImageFormat.OME_TIFF, payload, max_size=1024 * 1024)
    return service, fxt_project_service.get_project_by_id(project_id), image


def _annotations(label_id: str) -> list[DatasetItemAnnotation]:
    return [
        DatasetItemAnnotation(
            labels=[LabelReference(id=UUID(label_id))],
            shape=Rectangle(x=1, y=2, width=3, height=4),
        )
    ]


def test_annotate_plane_once_and_reload(ome_annotation, db_session, fxt_db_labels, fxt_dataset_service):
    service, project, image = ome_annotation
    assert service.get_ome_plane(project.id, image.id, z=12, t=0) is None
    assert db_session.scalar(select(func.count()).select_from(DatasetItemDB)) == 0
    annotations = _annotations(fxt_db_labels[0].id)
    first = fxt_dataset_service.register_ome_plane(project.id, image.id, z=12, t=0)
    fxt_dataset_service.set_dataset_item_annotations(project, first.id, annotations, True, None)
    fxt_dataset_service.assign_dataset_item_subset(project.id, first.id, DatasetItemSubset.TRAINING)
    second = fxt_dataset_service.register_ome_plane(project.id, image.id, z=12, t=0)
    assert second.id == first.id
    # Re-registration must not overwrite existing annotations, review state, or subset.
    item = fxt_dataset_service.get_dataset_item_by_id(project.id, first.id)
    assert item.annotation_data == annotations
    assert item.subset == DatasetItemSubset.TRAINING
    assert item.user_reviewed
    fxt_dataset_service.set_dataset_item_annotations(project, second.id, annotations, True, None)
    assert db_session.scalar(select(func.count()).select_from(MediaDB).where(MediaDB.type == "ome_plane")) == 1
    assert db_session.scalar(select(func.count()).select_from(DatasetItemDB)) == 1
    assert db_session.scalar(select(func.count()).select_from(DatasetItemLabelDB)) == 1
    plane = service.get_media_by_id(project.id, first.id)
    assert plane.type == MediaType.OME_PLANE
    assert plane.ome_image_id == image.id
    assert (plane.z_index, plane.t_index) == (12, 0)
    assert "frame_index" not in plane.model_dump()
    assert db_session.get(MediaDB, str(plane.id)).frame_index is None
    assert (plane.width, plane.height, plane.format, plane.size) == (10, 8, "png", 0)
    assert plane.annotation_status.has_annotations
    assert not (service.projects_dir / str(project.id) / "dataset" / f"{plane.id}.png").exists()
    assert service.get_media_by_id(project.id, image.id).annotation_status.has_annotations
    assert service.count_media(project, exclude_types=list(LEAF_MEDIA_TYPES)) == 1
    assert service.list_media_ids(project.id, exclude_types=list(LEAF_MEDIA_TYPES)) == (
        (image.id, MediaType.OME_IMAGE),
    )


@pytest.mark.parametrize(("z", "t"), [(-1, 0), (13, 0), (0, -1), (0, 2)])
def test_invalid_plane_coordinates_do_not_register_rows(ome_annotation, db_session, fxt_dataset_service, z, t):
    _, project, image = ome_annotation
    with pytest.raises(ValueError, match="out of range"):
        fxt_dataset_service.register_ome_plane(project.id, image.id, z=z, t=t)
    assert db_session.scalar(select(func.count()).select_from(DatasetItemDB)) == 0
    assert db_session.scalar(select(func.count()).select_from(MediaDB).where(MediaDB.type == "ome_plane")) == 0


def test_plane_listing_pagination_labels_and_deleted_annotations(ome_annotation, fxt_db_labels, fxt_dataset_service):
    service, project, image = ome_annotation
    annotations = _annotations(fxt_db_labels[0].id)
    for z, t in [(12, 1), (12, 0), (0, 1)]:
        plane = fxt_dataset_service.register_ome_plane(project.id, image.id, z=z, t=t)
        fxt_dataset_service.set_dataset_item_annotations(project, plane.id, annotations, True, None)
    all_planes, total = service.list_annotated_ome_planes(project.id, image.id)
    assert total == 3
    assert [(plane.z_index, plane.t_index) for _, plane in all_planes] == [(12, 0), (0, 1), (12, 1)]
    assert all_planes[0][0].annotation_data == annotations
    page, total = service.list_annotated_ome_planes(project.id, image.id, t=1, limit=1, offset=1)
    assert total == 2
    assert [(plane.z_index, plane.t_index) for _, plane in page] == [(12, 1)]
    assert service.list_annotated_ome_planes(project.id, image.id, z=12)[1] == 2
    plane_id = all_planes[0][1].id
    fxt_dataset_service.delete_dataset_item_annotations(project, plane_id)
    assert fxt_dataset_service.get_dataset_item_by_id(project.id, plane_id).annotation_data is None
    assert service.get_ome_plane(project.id, image.id, z=12, t=0).id == plane_id
    assert service.list_annotated_ome_planes(project.id, image.id)[1] == 2
    fxt_dataset_service.set_dataset_item_annotations(project, plane_id, [], True, None)
    assert service.list_annotated_ome_planes(project.id, image.id)[1] == 3


@pytest.mark.parametrize("selection", [{"z": 13}, {"t": -1}, {"limit": 0}, {"offset": -1}])
def test_invalid_plane_listing_selection(ome_annotation, selection):
    service, project, image = ome_annotation
    with pytest.raises(ValueError):
        service.list_annotated_ome_planes(project.id, image.id, **selection)


def test_plane_registration_is_idempotent_and_coordinates_are_unique(ome_annotation, db_session, fxt_dataset_service):
    service, project, image = ome_annotation
    plane = service.create_ome_plane(project.id, image.id, z=12, t=0)
    assert service.create_ome_plane(project.id, image.id, z=12, t=0).id == plane.id
    next_plane = service.create_ome_plane(project.id, image.id, z=0, t=1)
    assert next_plane.id != plane.id
    assert (next_plane.z_index, next_plane.t_index) == (0, 1)
    assert db_session.get(MediaDB, str(next_plane.id)).frame_index is None
    assert db_session.scalar(select(func.count()).select_from(DatasetItemDB)) == 0
    registered = fxt_dataset_service.register_ome_plane(project.id, image.id, z=12, t=0)
    assert registered.id == plane.id
    assert db_session.scalar(select(func.count()).select_from(DatasetItemDB)) == 1
    assert service.list_annotated_ome_planes(project.id, image.id) == ([], 0)
    assert not service.get_media_by_id(project.id, image.id).annotation_status.has_annotations


def test_plane_thumbnails_are_bounded_stateless_and_use_saved_view(ome_annotation, db_session):
    service, project, image = ome_annotation
    rendering = OmeRenderingService(service)
    dataset_dir = service.projects_dir / str(project.id) / "dataset"
    original_files = {path.name: path.read_bytes() for path in dataset_dir.iterdir()}
    content = rendering.render_thumbnail(project.id, image.id, z=12, t=0)
    with Image.open(BytesIO(content)) as thumbnail:
        assert thumbnail.format == "JPEG"
        assert thumbnail.size == (256, 256)
    assert db_session.scalar(select(func.count()).select_from(DatasetItemDB)) == 0
    assert db_session.scalar(select(func.count()).select_from(MediaDB).where(MediaDB.type == "ome_plane")) == 0
    assert {path.name: path.read_bytes() for path in dataset_dir.iterdir()} == original_files
    rendering.set_channel_view(project.id, image.id, OmeChannelSettings(settings=[]))
    with Image.open(BytesIO(rendering.render_thumbnail(project.id, image.id, z=12, t=0))) as thumbnail:
        assert not np.asarray(thumbnail).any()


def test_ome_parent_filters_and_view_membership(
    ome_annotation, fxt_dataset_service, fxt_dataset_view_service, fxt_db_labels, db_session
):
    service, project, image = ome_annotation
    view_service = fxt_dataset_view_service
    view = view_service.create_dataset_view(project.id, "microscopy", [image.id])
    plane = fxt_dataset_service.register_ome_plane(project.id, image.id, z=12, t=0)
    fxt_dataset_service.set_dataset_item_annotations(project, plane.id, _annotations(fxt_db_labels[0].id), True, None)
    fxt_dataset_service.assign_dataset_item_subset(project.id, plane.id, DatasetItemSubset.TRAINING)
    for filters in [
        MediaFilters(annotation_status=DatasetItemAnnotationStatus.WITH_ANNOTATIONS),
        MediaFilters(annotation_status=DatasetItemAnnotationStatus.MISSING_ANNOTATIONS),
        MediaFilters(label_ids=[UUID(fxt_db_labels[0].id)]),
        MediaFilters(subsets=[DatasetItemSubset.TRAINING]),
    ]:
        assert view_service.count_dataset_view_media(project.id, view.id, filters) == 1
        assert [m.id for m in view_service.list_dataset_view_media(project.id, view.id, filters)] == [image.id]
        assert view_service.list_dataset_view_media_ids(project.id, view.id, filters) == (
            (image.id, MediaType.OME_IMAGE),
        )
        assert service.list_media_ids(project.id, filters, exclude_types=list(LEAF_MEDIA_TYPES)) == (
            (image.id, MediaType.OME_IMAGE),
        )
    assert view_service.count_dataset_view_items(project.id, view.id) == 1
    with pytest.raises(ResourceNotFoundError):
        view_service.assign_media(project.id, view.id, [plane.id])
    # Legacy/direct assignments must not cause leaves to leak into media queries either.
    db_session.add(DatasetViewItemDB(dataset_view_id=str(view.id), media_id=str(plane.id)))
    db_session.flush()
    assert view_service.count_dataset_view_media(project.id, view.id) == 1


def test_parent_deletion_cascades_and_plane_deletion_preserves_parent(
    ome_annotation, db_session, fxt_db_labels, fxt_dataset_service
):
    service, project, image = ome_annotation
    planes = []
    for z in [0, 12]:
        plane = fxt_dataset_service.register_ome_plane(project.id, image.id, z=z, t=0)
        fxt_dataset_service.set_dataset_item_annotations(
            project, plane.id, _annotations(fxt_db_labels[0].id), True, None
        )
        planes.append(plane)
    storage = service.get_media_storage(project.id, image)
    service.delete_media(project, planes[0].id)
    assert storage.root.exists()
    assert db_session.get(MediaDB, str(image.id)) is not None
    service.delete_media(project, image.id)
    db_session.expire_all()
    assert db_session.get(MediaDB, str(image.id)) is None
    assert db_session.get(OmeImageDB, str(image.id)) is None
    assert db_session.get(MediaDB, str(planes[1].id)) is None
    assert db_session.scalar(select(func.count()).select_from(DatasetItemDB)) == 0
    assert db_session.scalar(select(func.count()).select_from(DatasetItemLabelDB)) == 0
    assert not storage.root.exists()


def test_missing_annotation_filter_checks_all_planes(ome_annotation, fxt_dataset_service):
    service, project, image = ome_annotation
    for t in range(2):
        for z in range(13):
            plane = fxt_dataset_service.register_ome_plane(project.id, image.id, z=z, t=t)
            fxt_dataset_service.set_dataset_item_annotations(project, plane.id, [], True, None)
    assert (
        service.count_media(
            project,
            annotation_status=DatasetItemAnnotationStatus.WITH_ANNOTATIONS,
            exclude_types=list(LEAF_MEDIA_TYPES),
        )
        == 1
    )
    assert (
        service.count_media(
            project,
            annotation_status=DatasetItemAnnotationStatus.MISSING_ANNOTATIONS,
            exclude_types=list(LEAF_MEDIA_TYPES),
        )
        == 0
    )
    fxt_dataset_service.delete_dataset_item_annotations(project, plane.id)
    assert (
        service.count_media(
            project,
            annotation_status=DatasetItemAnnotationStatus.MISSING_ANNOTATIONS,
            exclude_types=list(LEAF_MEDIA_TYPES),
        )
        == 1
    )


def test_plane_services_are_project_scoped(ome_annotation, fxt_dataset_service):
    service, _, image = ome_annotation
    other_project_id = uuid4()
    with pytest.raises(ResourceNotFoundError):
        service.get_ome_plane(other_project_id, image.id, z=0, t=0)
    with pytest.raises(ResourceNotFoundError):
        fxt_dataset_service.register_ome_plane(other_project_id, image.id, z=0, t=0)
    with pytest.raises(ResourceNotFoundError):
        service.list_annotated_ome_planes(other_project_id, image.id)
    with pytest.raises(ResourceNotFoundError):
        OmeRenderingService(service).render_thumbnail(other_project_id, image.id, z=0, t=0)


@pytest.mark.parametrize("sample_mode", [SampleMode.TRAINING, SampleMode.IMPORT_EXPORT])
@pytest.mark.parametrize("annotation_status", [None, DatasetItemAnnotationStatus.WITH_ANNOTATIONS])
@pytest.mark.parametrize("annotation_state", ["missing", "empty", "labeled"])
@pytest.mark.parametrize("view_scope", ["project", "included", "excluded"])
def test_dataset_conversion_rejects_selected_virtual_planes(
    ome_annotation,
    fxt_dataset_service,
    fxt_dataset_view_service,
    fxt_db_labels,
    sample_mode,
    annotation_status,
    annotation_state,
    view_scope,
):
    """Reject selected planes before path lookup without blocking views or filters that exclude them."""
    _, project, image = ome_annotation
    plane = fxt_dataset_service.register_ome_plane(project.id, image.id, z=12, t=0)
    if annotation_state != "missing":
        annotations = _annotations(fxt_db_labels[0].id) if annotation_state == "labeled" else []
        fxt_dataset_service.set_dataset_item_annotations(project, plane.id, annotations, True, None)
    view_id = None
    if view_scope != "project":
        view = fxt_dataset_view_service.create_dataset_view(
            project.id, "conversion", [image.id] if view_scope == "included" else []
        )
        view_id = view.id

    selected = view_scope != "excluded" and (annotation_state != "missing" or annotation_status is None)
    with patch.object(fxt_dataset_service._media_service, "get_media_binary_path_by_id") as get_path:
        if selected:
            with pytest.raises(
                UnsupportedDatasetMediaError, match="not supported for training or dataset export"
            ) as error:
                fxt_dataset_service.get_dm_dataset(
                    project.id, project.task, annotation_status, sample_mode, dataset_view_id=view_id
                )
            assert str(plane.id) in str(error.value)
            assert "materialization is not implemented" in str(error.value)
        else:
            dataset = fxt_dataset_service.get_dm_dataset(
                project.id, project.task, annotation_status, sample_mode, dataset_view_id=view_id
            )
            assert len(dataset) == 0
        get_path.assert_not_called()
    assert fxt_dataset_service.get_dataset_item_by_id(project.id, plane.id).id == plane.id
