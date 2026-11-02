# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

import getidata as dm
import numpy as np
import pytest
from PIL import Image as PILImage
from sqlalchemy.orm import Session

from app.datumaro_converter import SampleMode
from app.db.schema import MediaDB, OmeImageDB
from app.models import DatasetItemAnnotation, DatasetItemAnnotationStatus, LabelReference, Project, Rectangle
from app.models.media import LEAF_MEDIA_TYPES, MediaType, OmeFormat, OmeImage
from app.models.ome import ChannelDisplaySetting, RgbTarget
from app.services import DatasetService, OmeService
from app.services.base import ResourceNotFoundError
from app.services.media_service import InvalidImageError, MediaFilters
from app.services.ome.rendering import InvalidChannelSettingsError
from app.services.ome_service import OmePlaneOutOfRangeError
from tests.conftest import ome_pixel_value

# Channels declared out of RGB order: training must map Cy5 to red, GFP to green and DAPI to blue
FLUORESCENCE_CHANNELS = {"Name": ["Cy5", "DAPI", "GFP"], "EmissionWavelength": [670.0, 461.0, 510.0]}


@pytest.fixture
def fxt_project(fxt_db_projects, fxt_db_labels, fxt_project_service, db_session: Session) -> Project:
    db_project = fxt_db_projects[0]
    db_session.add(db_project)
    db_session.flush()
    for label in fxt_db_labels:
        label.project_id = db_project.id
    db_session.add_all(fxt_db_labels)
    db_session.flush()
    return fxt_project_service.get_project_by_id(UUID(db_project.id))


@pytest.fixture
def fxt_ome_image(
    fxt_project: Project, fxt_ome_service: OmeService, fxt_ome_tiff_factory: Callable[..., Path]
) -> OmeImage:
    path = fxt_ome_tiff_factory(size_t=2, size_c=3, size_z=4, channels=FLUORESCENCE_CHANNELS, significant_bits=8)
    return fxt_ome_service.create_ome_image(
        project_id=fxt_project.id, name="plate_A01", ome_format=OmeFormat.OME_TIFF, data=path
    )


def _annotate_plane(
    project: Project, ome_service: OmeService, dataset_service: DatasetService, ome_image: OmeImage, z: int, t: int
) -> UUID:
    """Mirror of the annotation endpoint: lazily create the plane, then annotate its dataset item."""
    plane = ome_service.get_plane(project=project, ome_image=ome_image, z=z, t=t)
    if plane is None:
        plane = ome_service.create_plane(project=project, ome_image=ome_image, z=z, t=t)
        dataset_service.create_dataset_item(project_id=project.id, task=project.task, media=plane, user_reviewed=True)
    label = project.task.labels[0]
    dataset_service.set_dataset_item_annotations(
        project=project,
        dataset_item_id=plane.id,
        annotations=[
            DatasetItemAnnotation(labels=[LabelReference(id=label.id)], shape=Rectangle(x=1, y=1, width=10, height=10))
        ],
        user_reviewed=True,
        prediction_model_id=None,
    )
    return plane.id


class TestOmeImageIngest:
    def test_create_ome_image(
        self, fxt_project, fxt_ome_image, fxt_projects_dir, fxt_ome_tiff_factory, db_session: Session
    ):
        dataset_dir = fxt_projects_dir / str(fxt_project.id) / "dataset"

        assert fxt_ome_image.type == MediaType.OME_IMAGE
        assert fxt_ome_image.plane_count == 8
        assert (fxt_ome_image.width, fxt_ome_image.height) == (48, 32)
        assert (dataset_dir / f"{fxt_ome_image.id}.ome.tiff").is_file()
        assert (dataset_dir / f"{fxt_ome_image.id}-thumb.jpg").is_file()
        # The uploaded file is moved, not copied
        assert not (fxt_projects_dir.parent / "image.ome.tiff").exists()

        db_info = db_session.get(OmeImageDB, str(fxt_ome_image.id))
        assert db_info is not None
        assert (db_info.size_z, db_info.size_c, db_info.size_t) == (4, 3, 2)
        assert "<OME" in (db_info.raw_metadata or "")
        assert [(m["channel"], m["target"]) for m in db_info.channel_mapping] == [
            (0, "red"),
            (2, "green"),
            (1, "blue"),
        ]

    def test_create_ome_image_invalid_file_leaves_no_trace(
        self, fxt_project, fxt_ome_service, fxt_projects_dir, tmp_path
    ):
        source = tmp_path / "broken.ome.tiff"
        source.write_bytes(b"not a tiff")

        with pytest.raises(InvalidImageError):
            fxt_ome_service.create_ome_image(
                project_id=fxt_project.id, name="broken", ome_format=OmeFormat.OME_TIFF, data=source
            )

        # The source file is moved back, nothing is left in the dataset
        assert source.is_file()
        assert list((fxt_projects_dir / str(fxt_project.id) / "dataset").iterdir()) == []

    def test_get_info_of_non_ome_media_raises(self, fxt_project, fxt_ome_service):
        with pytest.raises(ResourceNotFoundError):
            fxt_ome_service.get_info(project_id=fxt_project.id, media_id=fxt_project.id)


class TestOmeChannelViewAndRender:
    def test_default_channel_view(self, fxt_project, fxt_ome_service, fxt_ome_image):
        channel_view = fxt_ome_service.get_channel_view(project_id=fxt_project.id, media_id=fxt_ome_image.id)

        assert channel_view.is_default
        assert [(s.channel, s.target, s.enabled) for s in channel_view.settings] == [
            (0, RgbTarget.RED, True),
            (2, RgbTarget.GREEN, True),
            (1, RgbTarget.BLUE, True),
        ]

    def test_set_channel_view(self, fxt_project, fxt_ome_service, fxt_ome_image):
        settings = [ChannelDisplaySetting(channel=1, target=RgbTarget.GREEN, window_min=0, window_max=100)]

        fxt_ome_service.set_channel_view(project_id=fxt_project.id, media_id=fxt_ome_image.id, settings=settings)
        channel_view = fxt_ome_service.get_channel_view(project_id=fxt_project.id, media_id=fxt_ome_image.id)

        assert not channel_view.is_default
        assert channel_view.settings == settings

    def test_set_invalid_channel_view_raises(self, fxt_project, fxt_ome_service, fxt_ome_image):
        settings = [ChannelDisplaySetting(channel=7, target=RgbTarget.GREEN, window_min=0, window_max=100)]

        with pytest.raises(InvalidChannelSettingsError):
            fxt_ome_service.set_channel_view(project_id=fxt_project.id, media_id=fxt_ome_image.id, settings=settings)

    def test_render_plane_uses_and_invalidates_cache(self, fxt_project, fxt_ome_service, fxt_ome_image):
        settings = [ChannelDisplaySetting(channel=1, target=RgbTarget.GREEN, window_min=0, window_max=200)]
        fxt_ome_service.set_channel_view(project_id=fxt_project.id, media_id=fxt_ome_image.id, settings=settings)

        path, digest = fxt_ome_service.render_plane(project_id=fxt_project.id, media_id=fxt_ome_image.id, z=2, t=1)
        cached_path, cached_digest = fxt_ome_service.render_plane(
            project_id=fxt_project.id, media_id=fxt_ome_image.id, z=2, t=1
        )

        assert (cached_path, cached_digest) == (path, digest)
        rendered = np.asarray(PILImage.open(path))
        expected_green = round(ome_pixel_value(t=1, c=1, z=2) * 255 / 200)
        assert rendered[0, 0].tolist() == [0, expected_green, 0]

        settings[0] = settings[0].model_copy(update={"window_max": 400})
        fxt_ome_service.set_channel_view(project_id=fxt_project.id, media_id=fxt_ome_image.id, settings=settings)
        new_path, new_digest = fxt_ome_service.render_plane(
            project_id=fxt_project.id, media_id=fxt_ome_image.id, z=2, t=1
        )
        assert new_digest != digest
        assert new_path != path

    @pytest.mark.parametrize("z, t, level", [(4, 0, 0), (0, 2, 0), (0, 0, 1)])
    def test_render_plane_out_of_range(self, fxt_project, fxt_ome_service, fxt_ome_image, z, t, level):
        with pytest.raises(OmePlaneOutOfRangeError):
            fxt_ome_service.render_plane(project_id=fxt_project.id, media_id=fxt_ome_image.id, z=z, t=t, level=level)


class TestOmePlaneAnnotation:
    def test_annotating_a_plane_materializes_it_as_a_training_image(
        self, fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, fxt_projects_dir, db_session
    ):
        plane_id = _annotate_plane(fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, z=3, t=1)

        db_plane = db_session.get(MediaDB, str(plane_id))
        assert db_plane is not None
        assert (db_plane.type, db_plane.parent_id) == (MediaType.OME_PLANE, str(fxt_ome_image.id))
        assert (db_plane.z_index, db_plane.t_index, db_plane.frame_index) == (3, 1, 3 + 1 * 4)

        # Rendered with the fixed training mapping over the declared 8-bit range: Cy5->R, GFP->G, DAPI->B
        plane_image = np.asarray(PILImage.open(fxt_projects_dir / str(fxt_project.id) / "dataset" / f"{plane_id}.png"))
        assert plane_image.shape == (32, 48, 3)
        assert plane_image[0, 0].tolist() == [
            ome_pixel_value(t=1, c=0, z=3),
            ome_pixel_value(t=1, c=2, z=3),
            ome_pixel_value(t=1, c=1, z=3),
        ]

    def test_reannotating_a_plane_does_not_duplicate_it(
        self, fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, db_session
    ):
        first = _annotate_plane(fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, z=1, t=0)
        second = _annotate_plane(fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, z=1, t=0)

        assert first == second
        planes = db_session.query(MediaDB).filter(MediaDB.parent_id == str(fxt_ome_image.id)).all()
        assert len(planes) == 1

    def test_planes_are_not_listed_as_media(
        self, fxt_project, fxt_ome_service, fxt_dataset_service, fxt_media_service, fxt_ome_image
    ):
        _annotate_plane(fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, z=0, t=0)
        _annotate_plane(fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, z=2, t=1)

        media = fxt_media_service.list_media(project_id=fxt_project.id, exclude_types=list(LEAF_MEDIA_TYPES))
        count = fxt_media_service.count_media(project=fxt_project, exclude_types=list(LEAF_MEDIA_TYPES))

        assert [m.id for m in media] == [fxt_ome_image.id]
        assert count == 1

    def test_ome_image_annotation_status_follows_its_planes(
        self, fxt_project, fxt_ome_service, fxt_dataset_service, fxt_media_service, fxt_ome_image
    ):
        def _listed(status: DatasetItemAnnotationStatus) -> list[UUID]:
            media = fxt_media_service.list_media(
                project_id=fxt_project.id,
                filters=MediaFilters(annotation_status=status),
                exclude_types=list(LEAF_MEDIA_TYPES),
            )
            return [m.id for m in media]

        assert _listed(DatasetItemAnnotationStatus.WITH_ANNOTATIONS) == []
        _annotate_plane(fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, z=0, t=0)

        assert _listed(DatasetItemAnnotationStatus.WITH_ANNOTATIONS) == [fxt_ome_image.id]
        # Only 1 of the 8 planes is annotated
        assert _listed(DatasetItemAnnotationStatus.MISSING_ANNOTATIONS) == [fxt_ome_image.id]

    def test_list_annotated_planes(self, fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image):
        _annotate_plane(fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, z=2, t=1)
        _annotate_plane(fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, z=1, t=0)

        planes = fxt_ome_service.list_annotated_planes(project=fxt_project, ome_image=fxt_ome_image)

        assert [(p.z_index, p.t_index) for p in planes] == [(1, 0), (2, 1)]

    def test_training_dataset_uses_plane_images(
        self, fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, fxt_projects_dir
    ):
        plane_ids = {
            _annotate_plane(fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, z=z, t=0)
            for z in range(3)
        }

        dataset = fxt_dataset_service.get_dm_dataset(
            project_id=fxt_project.id,
            task=fxt_project.task,
            annotation_status=DatasetItemAnnotationStatus.WITH_ANNOTATIONS,
            sample_mode=SampleMode.TRAINING,
        )

        assert isinstance(dataset, dm.Dataset)
        dataset_dir = fxt_projects_dir / str(fxt_project.id) / "dataset"
        assert {sample.image.path for sample in dataset} == {
            str(dataset_dir / f"{plane_id}.png") for plane_id in plane_ids
        }

    def test_ome_planes_are_not_counted_as_video_frames(
        self, fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image
    ):
        _annotate_plane(fxt_project, fxt_ome_service, fxt_dataset_service, fxt_ome_image, z=0, t=0)

        statistics = fxt_dataset_service.get_dataset_statistics(project_id=fxt_project.id)

        assert statistics.media_counts.video_frames == 0
        assert statistics.annotations_counts.annotated_video_frames == 0

    def test_delete_ome_image_removes_render_cache(
        self, fxt_project, fxt_ome_service, fxt_media_service, fxt_ome_image, fxt_projects_dir
    ):
        fxt_ome_service.render_plane(project_id=fxt_project.id, media_id=fxt_ome_image.id, z=0, t=0)
        cache_dir = OmeService.render_cache_dir(fxt_projects_dir / str(fxt_project.id) / "dataset", fxt_ome_image.id)
        assert cache_dir.is_dir()

        fxt_media_service.delete_media(project=fxt_project, media_id=fxt_ome_image.id)

        assert not cache_dir.exists()
