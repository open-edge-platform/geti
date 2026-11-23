# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import numpy as np
import pytest
from PIL import Image
from sqlalchemy import func, select

from app.db.schema import OmeChannelViewDB
from app.models.media import ImageFormat
from app.models.ome import OmeChannelSettings
from app.services.base import ResourceNotFoundError
from app.services.ome.rendering import OmeRenderingService, parse_channel_override

ASSETS = Path(__file__).parents[2] / "assets" / "ome"


@pytest.fixture
def ingested_rendering(ome_ingest):
    service, project_id = ome_ingest
    media = service.create_ome_image(
        project_id,
        "specimen",
        ImageFormat.OME_TIFF,
        BytesIO((ASSETS / "xyc.ome.tiff").read_bytes()),
        max_size=1024 * 1024,
    )
    return OmeRenderingService(service), project_id, media


def test_persisted_view_changes_default_render_not_training_or_override(ingested_rendering, db_session):
    service, project_id, media = ingested_rendering
    original = service.media_service.get_ome_image_info(project_id, media.id)
    default = service.get_channel_view(project_id, media.id)
    assert default.is_default
    assert db_session.scalar(select(func.count()).select_from(OmeChannelViewDB)) == 0
    before = service.resolve_render(project_id, media.id)
    override = parse_channel_override("0|0:10$FFFFFF")
    explicit = service.resolve_render(project_id, media.id, override=override)
    previous_pixels = service.render(explicit)

    saved = service.set_channel_view(project_id, media.id, parse_channel_override("0|0:10$00FF00"))
    assert not saved.is_default
    db_session.expunge_all()

    assert service.get_channel_view(project_id, media.id) == saved
    assert db_session.scalar(select(func.count()).select_from(OmeChannelViewDB)) == 1
    assert service.media_service.get_ome_image_info(project_id, media.id) == original
    saved_render = service.resolve_render(project_id, media.id)
    assert saved_render.etag != before.etag
    with Image.open(BytesIO(service.render(saved_render))) as image:
        pixels = np.asarray(image)
        assert not pixels[..., [0, 2]].any()
        assert pixels[-1, -1, 1] == 255
    assert service.resolve_render(project_id, media.id, override=override).etag == explicit.etag
    assert service.render(explicit) == previous_pixels

    second = service.set_channel_view(project_id, media.id, OmeChannelSettings(settings=[]))
    assert service.get_channel_view(project_id, media.id) == second
    assert db_session.scalar(select(func.count()).select_from(OmeChannelViewDB)) == 1
    black = service.resolve_render(project_id, media.id)
    with Image.open(BytesIO(service.render(black))) as image:
        np.testing.assert_array_equal(np.asarray(image), np.zeros((media.height, media.width, 3)))


def test_fixture_golden_pixels(ingested_rendering):
    service, project_id, media = ingested_rendering
    view = parse_channel_override("0|0:1535$FF0000,1|100:1635$00FF00,2|200:1735$0000FF")
    selection = service.resolve_render(project_id, media.id, override=view)
    expected_plane = (np.arange(1536).reshape(32, 48) / 1535 * 255).astype(np.uint8)
    expected = np.repeat(expected_plane[..., np.newaxis], 3, axis=2)
    with Image.open(BytesIO(service.render(selection))) as image:
        np.testing.assert_array_equal(np.asarray(image), expected)


def test_saved_view_is_project_scoped(ingested_rendering):
    service, project_id, media = ingested_rendering
    service.set_channel_view(project_id, media.id, parse_channel_override("0|0:10$FFFFFF"))
    with pytest.raises(ResourceNotFoundError):
        service.get_channel_view(uuid4(), media.id)
    with pytest.raises(ResourceNotFoundError):
        service.set_channel_view(uuid4(), media.id, OmeChannelSettings(settings=[]))
    with pytest.raises(ResourceNotFoundError):
        service.resolve_render(uuid4(), media.id)


def test_defaults_and_rendering_leave_media_storage_unchanged(ingested_rendering):
    service, project_id, media = ingested_rendering
    dataset = service.media_service.projects_dir / str(project_id) / "dataset"
    original_files = {path.relative_to(dataset): path.read_bytes() for path in dataset.rglob("*") if path.is_file()}
    service.get_channel_view(project_id, media.id)
    selection = service.resolve_render(project_id, media.id)
    service.render(selection)
    assert {
        path.relative_to(dataset): path.read_bytes() for path in dataset.rglob("*") if path.is_file()
    } == original_files
    assert not any(path.is_dir() for path in dataset.iterdir())


def test_pyramid_level_and_midplane_defaults(ome_ingest):
    media_service, project_id = ome_ingest
    media = media_service.create_ome_image(
        project_id,
        "pyramid",
        ImageFormat.OME_TIFF,
        BytesIO((ASSETS / "pyramidal.ome.tiff").read_bytes()),
        max_size=1024 * 1024,
    )
    service = OmeRenderingService(media_service)
    info = media_service.get_ome_image_info(project_id, media.id)
    level = len(info.pyramid_levels) - 1
    selection = service.resolve_render(project_id, media.id, level=level)
    with Image.open(BytesIO(service.render(selection))) as image:
        assert image.size == (info.pyramid_levels[level]["width"], info.pyramid_levels[level]["height"])


def test_render_companion_archive(ome_ingest, companion_storage):
    media_service, project_id = ome_ingest
    archive = BytesIO()
    with ZipFile(archive, "w") as output:
        for path in companion_storage.root.iterdir():
            output.write(path, path.name)
    archive.seek(0)
    media = media_service.create_ome_image(
        project_id, "companion", ImageFormat.OME_TIFF, archive, archive=True, max_size=1024 * 1024
    )
    service = OmeRenderingService(media_service)
    override = parse_channel_override("0|0:1$FF0000,1|0:1$00FF00")
    selection = service.resolve_render(project_id, media.id, override=override)
    with Image.open(BytesIO(service.render(selection))) as image:
        np.testing.assert_array_equal(np.asarray(image), np.full((4, 5, 3), [0, 255, 0]))
    service.get_channel_view(project_id, media.id)
    assert service.resolve_render(project_id, media.id, override=override).etag == selection.etag
