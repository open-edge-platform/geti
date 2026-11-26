# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import shutil
from io import BytesIO
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import numpy as np
import pytest
import tifffile
from getidata.data_formats.base import DataFormat
from getidata.export_import import export_dataset
from PIL import Image
from sqlalchemy import func, select

from app.datumaro_converter import SampleMode
from app.db.schema import (
    DatasetItemDB,
    DatasetItemLabelDB,
    DatasetRevisionDB,
    DatasetViewItemDB,
    MediaDB,
    OmeImageDB,
    ProjectDB,
)
from app.models import (
    DatasetItemAnnotation,
    DatasetItemAnnotationStatus,
    DatasetItemSubset,
    FullImage,
    LabelReference,
    Polygon,
    Rectangle,
    TaskType,
)
from app.models.media import LEAF_MEDIA_TYPES, ImageFormat, MediaType
from app.models.ome import OmeChannelSettings
from app.models.shape import Point
from app.services.base import InvalidImageError, ResourceNotFoundError
from app.services.dataset_revision_service import DatasetRevisionService
from app.services.dataset_service import DatasetService, UnsupportedDatasetMediaError
from app.services.media_service import MediaFilters
from app.services.ome.materialization import _MAX_ROW_BYTES, OME_PROJECTIONS_FILENAME
from app.services.ome.registry import UnsupportedOmeStorageError
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


@pytest.fixture(params=[TaskType.DETECTION, TaskType.INSTANCE_SEGMENTATION, TaskType.CLASSIFICATION])
def ome_training_task(ome_annotation, db_session, fxt_project_service, request):
    service, project, image = ome_annotation
    project_db = db_session.get(ProjectDB, str(project.id))
    project_db.task_type = request.param
    project_db.exclusive_labels = False
    db_session.flush()
    return service, fxt_project_service.get_project_by_id(project.id), image


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
            with pytest.raises(UnsupportedDatasetMediaError, match="requires annotated training") as error:
                fxt_dataset_service.get_dm_dataset(
                    project.id, project.task, annotation_status, sample_mode, dataset_view_id=view_id
                )
            assert str(plane.id) in str(error.value)
            assert "Direct dataset export" in str(error.value)
        else:
            dataset = fxt_dataset_service.get_dm_dataset(
                project.id, project.task, annotation_status, sample_mode, dataset_view_id=view_id
            )
            assert len(dataset) == 0
        get_path.assert_not_called()
    assert fxt_dataset_service.get_dataset_item_by_id(project.id, plane.id).id == plane.id


@pytest.mark.parametrize("failure", ["decode", "scanline"])
@pytest.mark.parametrize(
    "empty_subset", [DatasetItemSubset.TRAINING, DatasetItemSubset.VALIDATION, DatasetItemSubset.TESTING]
)
def test_training_materializes_only_retained_planes(
    ome_training_task, db_session, fxt_label_service, fxt_db_labels, tmp_path, failure, empty_subset
):
    """Discarded empty training planes cannot block valid revisions; retained planes still surface failures."""
    service, project, image = ome_training_task
    dataset_service = DatasetService(fxt_label_service, service, db_session)
    shape = {
        TaskType.DETECTION: Rectangle(x=1, y=2, width=3, height=4),
        TaskType.INSTANCE_SEGMENTATION: Polygon(points=[Point(x=1, y=2), Point(x=4, y=2), Point(x=4, y=6)]),
        TaskType.CLASSIFICATION: FullImage(),
    }[project.task.task_type]
    annotations = [DatasetItemAnnotation(shape=shape, labels=[LabelReference(id=UUID(fxt_db_labels[0].id))])]
    retained_planes = []
    for z, subset in enumerate([DatasetItemSubset.TRAINING, DatasetItemSubset.VALIDATION, DatasetItemSubset.TESTING]):
        plane = dataset_service.register_ome_plane(project.id, image.id, z=z, t=0)
        dataset_service.set_dataset_item_annotations(project, plane.id, annotations, True, None)
        dataset_service.assign_dataset_item_subset(project.id, plane.id, subset)
        retained_planes.append(plane)

    payload = BytesIO()
    tifffile.imwrite(payload, np.zeros((8, 10), dtype=np.uint16), ome=True)
    payload.seek(0)
    broken = service.create_ome_image(project.id, "broken", ImageFormat.OME_TIFF, payload, max_size=1024 * 1024)
    empty_plane = dataset_service.register_ome_plane(project.id, broken.id, z=0, t=0)
    dataset_service.set_dataset_item_annotations(project, empty_plane.id, [], True, None)
    dataset_service.assign_dataset_item_subset(project.id, empty_plane.id, empty_subset)
    if failure == "decode":
        service.get_media_storage(project.id, broken).effective_path.unlink()
        expected_error = UnsupportedOmeStorageError
    else:
        db_session.get(OmeImageDB, str(broken.id)).size_x = _MAX_ROW_BYTES // 3 + 1
        db_session.flush()
        expected_error = InvalidImageError

    workspace = tmp_path / "workspace"
    with patch.object(service, "validate_ome_plane_selection", wraps=service.validate_ome_plane_selection) as validate:
        if empty_subset != DatasetItemSubset.TRAINING:
            with pytest.raises(expected_error):
                dataset_service.get_dm_dataset(
                    project.id,
                    project.task,
                    DatasetItemAnnotationStatus.WITH_ANNOTATIONS,
                    SampleMode.TRAINING,
                    ome_plane_dir=workspace,
                )
            return
        dataset = dataset_service.get_dm_dataset(
            project.id,
            project.task,
            DatasetItemAnnotationStatus.WITH_ANNOTATIONS,
            SampleMode.TRAINING,
            ome_plane_dir=workspace,
        )
    assert {call.args[1] for call in validate.call_args_list} == {image.id}
    assert set(dataset.df["id"]) == {str(plane.id) for plane in retained_planes}
    assert {path.stem for path in workspace.glob("*.png")} == {str(plane.id) for plane in retained_planes}
    assert all(sample.image.path == str(workspace / f"{sample.id}.png") for sample in dataset)
    assert {
        record["media_id"] for record in json.loads((workspace / OME_PROJECTIONS_FILENAME).read_text())["images"]
    } == {str(image.id)}
    revisions = DatasetRevisionService(service.projects_dir.parent, db_session)
    revision_id = revisions.save_revision(
        project.id, dataset, ome_projections_path=workspace / OME_PROJECTIONS_FILENAME
    )
    assert revisions.get_dataset_revision(project.id, revision_id).item_counts.model_dump() == {
        "total": 3,
        "training": 1,
        "validation": 1,
        "testing": 1,
    }


def test_conversion_with_only_discarded_planes_creates_no_artifacts(
    ome_training_task, db_session, fxt_label_service, tmp_path
):
    """An empty converted dataset requires no OME reads, PNGs, or projection sidecar."""
    service, project, image = ome_training_task
    dataset_service = DatasetService(fxt_label_service, service, db_session)
    plane = dataset_service.register_ome_plane(project.id, image.id, z=0, t=0)
    dataset_service.set_dataset_item_annotations(project, plane.id, [], True, None)
    dataset_service.assign_dataset_item_subset(project.id, plane.id, DatasetItemSubset.TRAINING)
    workspace = tmp_path / "workspace"
    with patch.object(service, "validate_ome_plane_selection", side_effect=AssertionError("Discarded plane was read")):
        dataset = dataset_service.get_dm_dataset(
            project.id,
            project.task,
            DatasetItemAnnotationStatus.WITH_ANNOTATIONS,
            SampleMode.TRAINING,
            ome_plane_dir=workspace,
        )
    assert len(dataset) == 0
    assert not workspace.exists()


@pytest.mark.parametrize(
    "projection",
    [
        {"mode": "rgb", "channels": [{"channel": 2, "target": "red"}, {"channel": 0, "target": "blue"}]},
        {"mode": "grayscale", "channel": 1},
    ],
)
@pytest.mark.parametrize("view_scoped", [False, True])
def test_training_revision_materializes_annotated_planes(
    ome_annotation,
    db_session,
    fxt_label_service,
    fxt_db_labels,
    fxt_dataset_view_service,
    tmp_path,
    projection,
    view_scoped,
):
    """Persist only selected annotated planes, retaining pixels and coordinates after source removal."""
    service, project, image = ome_annotation
    dataset_service = DatasetService(fxt_label_service, service, db_session)
    revision_service = DatasetRevisionService(service.projects_dir.parent, db_session)
    db_session.get(OmeImageDB, str(image.id)).channel_projection = projection
    db_session.flush()
    coordinates = [(12, 0), (0, 1), (12, 1)]
    planes = []
    for (z, t), subset in zip(
        coordinates, [DatasetItemSubset.TRAINING, DatasetItemSubset.VALIDATION, DatasetItemSubset.TESTING], strict=True
    ):
        plane = dataset_service.register_ome_plane(project.id, image.id, z=z, t=t)
        dataset_service.set_dataset_item_annotations(project, plane.id, _annotations(fxt_db_labels[0].id), True, None)
        dataset_service.assign_dataset_item_subset(project.id, plane.id, subset)
        planes.append(plane)
    # Registered but unannotated planes must not get PNGs or revision rows.
    dataset_service.register_ome_plane(project.id, image.id, z=1, t=0)
    view_id = None
    if view_scoped:
        view_id = fxt_dataset_view_service.create_dataset_view(project.id, "OME training", [image.id]).id
        payload = BytesIO()
        tifffile.imwrite(payload, np.zeros((8, 10), dtype=np.uint16), ome=True)
        payload.seek(0)
        excluded = service.create_ome_image(project.id, "excluded", ImageFormat.OME_TIFF, payload, max_size=1024 * 1024)
        excluded_plane = dataset_service.register_ome_plane(project.id, excluded.id, z=0, t=0)
        dataset_service.set_dataset_item_annotations(
            project, excluded_plane.id, _annotations(fxt_db_labels[0].id), True, None
        )
    OmeRenderingService(service).set_channel_view(project.id, image.id, OmeChannelSettings(settings=[]))
    workspace = tmp_path / "training-workspace"
    with patch(
        "app.services.ome.rgb_channel_projection.MetadataRgbChannelProjectionStrategy.compute",
        side_effect=AssertionError("Training must not recompute the ingest projection"),
    ):
        dataset = dataset_service.get_dm_dataset(
            project.id,
            project.task,
            DatasetItemAnnotationStatus.WITH_ANNOTATIONS,
            SampleMode.TRAINING,
            dataset_view_id=view_id,
            ome_plane_dir=workspace,
        )
    assert len(list(workspace.glob("*.png"))) == 3
    revision_id = revision_service.save_revision(
        project.id, dataset, dataset_view_id=view_id, ome_projections_path=workspace / OME_PROJECTIONS_FILENAME
    )
    revision_path = service.projects_dir / str(project.id) / "dataset_revisions" / str(revision_id)
    pngs = list((revision_path / "images").glob("*.png"))
    assert len(pngs) == 3
    assert json.loads((revision_path / OME_PROJECTIONS_FILENAME).read_text()) == {
        "format_version": 1,
        "images": [
            {"media_id": str(image.id), "container_format": "ome_tiff", "size_c": 3, "channel_projection": projection}
        ],
    }
    revision = revision_service.get_dataset_revision(project.id, revision_id)
    assert revision.item_counts.model_dump() == {"total": 3, "training": 1, "validation": 1, "testing": 1}
    assert revision.size == sum(path.stat().st_size for path in revision_path.rglob("*") if path.is_file())
    shutil.rmtree(workspace)
    # Saved artifacts must no longer depend on the OME container or current display state.
    storage = service.get_media_storage(project.id, image)
    storage.effective_path.unlink()
    reloaded = revision_service.load_revision(project.id, revision_id)
    assert len(reloaded) == 3
    assert set(reloaded.df["id"]) == {str(plane.id) for plane in planes}
    from getitune.data.dataset.detection import DetectionDataset

    training_dataset = DetectionDataset(reloaded)
    pixels = np.arange(2 * 13 * 3 * 8 * 10, dtype=np.uint16).reshape(2, 13, 3, 8, 10)
    for index, sample in enumerate(reloaded):
        plane = next(plane for plane in planes if str(plane.id) == sample.id)
        assert (sample.image_info.width, sample.image_info.height) == (10, 8)
        np.testing.assert_array_equal(sample.bboxes, [[1, 2, 4, 6]])
        source = (pixels[plane.t_index, plane.z_index].astype(np.float64) / 65535 * 255).astype(np.uint8)
        if projection["mode"] == "rgb":
            expected = np.stack([source[2], np.zeros((8, 10), dtype=np.uint8), source[0]], axis=2)
        else:
            expected = source[1]
        with Image.open(sample.image.path) as png:
            assert png.mode == ("RGB" if projection["mode"] == "rgb" else "L")
            np.testing.assert_array_equal(np.array(png), expected)
        expected_rgb = expected if expected.ndim == 3 else np.repeat(expected[..., np.newaxis], 3, axis=2)
        np.testing.assert_array_equal(sample.image.data, expected_rgb)
        np.testing.assert_allclose(
            training_dataset[index].image.numpy(), expected_rgb.transpose(2, 0, 1) / 255, atol=1e-7
        )
    export_path = tmp_path / "coco-export"
    export_dataset(reloaded, output_path=export_path, data_format=DataFormat.COCO, as_zip=False)
    assert len(list(export_path.rglob("*.png"))) == 3


def test_training_revision_preserves_mixed_parent_projection_policies(
    ome_annotation, db_session, fxt_label_service, fxt_db_labels, tmp_path
):
    """Keep distinct RGB and grayscale ingest policies together in a single revision."""
    service, project, image = ome_annotation
    dataset_service = DatasetService(fxt_label_service, service, db_session)
    payload = BytesIO()
    tifffile.imwrite(payload, np.full((8, 10), 65535, dtype=np.uint16), ome=True)
    payload.seek(0)
    second = service.create_ome_image(project.id, "grayscale", ImageFormat.OME_TIFF, payload, max_size=1024 * 1024)
    db_session.get(OmeImageDB, str(second.id)).channel_projection = {"mode": "grayscale", "channel": 0}
    db_session.flush()
    for parent, z, subset in [
        (image, 0, DatasetItemSubset.TRAINING),
        (image, 1, DatasetItemSubset.VALIDATION),
        (second, 0, DatasetItemSubset.TESTING),
    ]:
        plane = dataset_service.register_ome_plane(project.id, parent.id, z=z, t=0)
        dataset_service.set_dataset_item_annotations(project, plane.id, _annotations(fxt_db_labels[0].id), True, None)
        dataset_service.assign_dataset_item_subset(project.id, plane.id, subset)
    workspace = tmp_path / "workspace"
    dataset = dataset_service.get_dm_dataset(
        project.id,
        project.task,
        DatasetItemAnnotationStatus.WITH_ANNOTATIONS,
        SampleMode.TRAINING,
        ome_plane_dir=workspace,
    )
    revisions = DatasetRevisionService(service.projects_dir.parent, db_session)
    revision_id = revisions.save_revision(
        project.id, dataset, ome_projections_path=workspace / OME_PROJECTIONS_FILENAME
    )
    revision_path = service.projects_dir / str(project.id) / "dataset_revisions" / str(revision_id)
    manifest = json.loads((revision_path / OME_PROJECTIONS_FILENAME).read_text())
    assert {entry["media_id"]: entry["channel_projection"] for entry in manifest["images"]} == {
        str(parent.id): service.get_ome_image_info(project.id, parent.id).channel_projection.model_dump(mode="json")
        for parent in (image, second)
    }
    modes = set()
    for path in (revision_path / "images").glob("*.png"):
        with Image.open(path) as png:
            modes.add(png.mode)
    assert modes == {"RGB", "L"}


@pytest.mark.parametrize("failure", ["export", "sidecar", "database"])
def test_revision_failures_remove_partial_artifacts(
    ome_annotation, db_session, fxt_label_service, fxt_db_labels, tmp_path, monkeypatch, failure
):
    """Remove a failed revision on disk and never persist a success-shaped revision record."""
    service, project, image = ome_annotation
    dataset_service = DatasetService(fxt_label_service, service, db_session)
    for z, subset in enumerate([DatasetItemSubset.TRAINING, DatasetItemSubset.VALIDATION, DatasetItemSubset.TESTING]):
        plane = dataset_service.register_ome_plane(project.id, image.id, z=z, t=0)
        dataset_service.set_dataset_item_annotations(project, plane.id, _annotations(fxt_db_labels[0].id), True, None)
        dataset_service.assign_dataset_item_subset(project.id, plane.id, subset)
    workspace = tmp_path / "workspace"
    dataset = dataset_service.get_dm_dataset(
        project.id,
        project.task,
        DatasetItemAnnotationStatus.WITH_ANNOTATIONS,
        SampleMode.TRAINING,
        ome_plane_dir=workspace,
    )
    revision_id = uuid4()
    monkeypatch.setattr("app.services.dataset_revision_service.uuid4", lambda: revision_id)
    sidecar = workspace / OME_PROJECTIONS_FILENAME
    if failure == "export":

        def fail_export(*, output_path, **kwargs):
            output_path.mkdir(parents=True)
            (output_path / "partial.png").write_bytes(b"partial")
            raise OSError("Export failed")

        monkeypatch.setattr("getidata.export_import.export_dataset", fail_export)
    elif failure == "sidecar":
        sidecar.unlink()
    else:
        monkeypatch.setattr(
            "app.services.dataset_revision_service.DatasetRevisionRepository.save",
            Mock(side_effect=RuntimeError("Database save failed")),
        )
    revisions = DatasetRevisionService(service.projects_dir.parent, db_session)
    with pytest.raises((OSError, RuntimeError)):
        revisions.save_revision(project.id, dataset, ome_projections_path=sidecar)
    revision_path = service.projects_dir / str(project.id) / "dataset_revisions" / str(revision_id)
    assert not revision_path.exists()
    assert db_session.scalar(select(func.count()).select_from(DatasetRevisionDB)) == 0
