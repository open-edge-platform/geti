# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import errno
import shutil
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import UUID, uuid4
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest
from PIL import Image
from sqlalchemy import func, select

from app.db.schema import DatasetItemDB, MediaDB, OmeImageDB
from app.models import Project
from app.models.media import ImageFormat, MediaType
from app.models.ome import GrayscaleProjection, RgbChannelAssignment, RgbProjection
from app.services.base import InvalidImageError, ResourceNotFoundError
from app.services.media_service import MediaService
from app.services.ome import ChannelMappingStrategy
from app.services.ome.ingest import OmeMediaTooLargeError, create_ingest_thumbnail

ASSETS = Path(__file__).parents[2] / "assets" / "ome"
MAX_SIZE = 10 * 1024 * 1024


@pytest.fixture
def ome_ingest(db_session, fxt_db_projects, tmp_path):
    project = fxt_db_projects[0]
    db_session.add(project)
    db_session.flush()
    return MediaService(tmp_path, db_session=db_session), UUID(project.id)


@pytest.mark.parametrize(
    "filename",
    [
        "xyc.ome.tiff",
        "xycz.ome.tiff",
        "xyczt.ome.tiff",
        "single_channel.ome.tiff",
        "rgb.ome.tiff",
        "rgb_planar.ome.tiff",
        "alternate_order.ome.tiff",
        "pyramidal.ome.tiff",
        "bigtiff.ome.tiff",
        "lzw.ome.tiff",
        "jpeg.ome.tiff",
    ],
)
@pytest.mark.parametrize("stream", [False, True])
def test_ingest_ome_fixture(ome_ingest, db_session, tmp_path, filename, stream):
    service, project_id = ome_ingest
    upload = tmp_path / filename
    shutil.copyfile(ASSETS / filename, upload)
    size = upload.stat().st_size

    media = service.create_ome_image(
        project_id,
        "specimen",
        ImageFormat.OME_TIFF,
        BytesIO(upload.read_bytes()) if stream else upload,
        max_size=MAX_SIZE,
    )

    assert media.type == MediaType.OME_IMAGE
    assert media.size == size
    assert upload.exists() == stream
    row = db_session.get(MediaDB, str(media.id))
    info = db_session.get(OmeImageDB, str(media.id))
    assert row.type == "ome_image"
    assert (row.width, row.height) == (info.size_x, info.size_y)
    assert info.raw_metadata.startswith("<?xml")
    assert info.channel_mapping
    assert info.is_big_tiff == (filename == "bigtiff.ome.tiff")
    assert db_session.scalar(select(func.count()).select_from(DatasetItemDB)) == 0
    with Image.open(service.get_media_thumbnail_path_by_id(project_id, media.id)) as thumbnail:
        assert thumbnail.format == "JPEG"
        assert thumbnail.size == (256, 256)
    assert service.get_media_by_id(project_id, media.id) == media
    assert service.list_media(project_id)[0] == media
    assert (
        service.get_ome_image_info(project_id, media.id).channel_projection.model_dump(mode="json")
        == info.channel_mapping
    )
    with pytest.raises(ResourceNotFoundError):
        service.get_ome_image_info(uuid4(), media.id)


@pytest.mark.parametrize("image_format", [ImageFormat.OME_TIF, ImageFormat.OME_TIFF])
def test_single_file_storage_and_delete(ome_ingest, db_session, image_format):
    service, project_id = ome_ingest
    pixels = (ASSETS / "xyc.ome.tiff").read_bytes()
    media = service.create_ome_image(project_id, "specimen", image_format, BytesIO(pixels), max_size=MAX_SIZE)

    storage = service.get_media_storage(project_id, media)
    thumbnail = service.get_media_thumbnail_path_by_id(project_id, media.id)
    assert not storage.is_directory
    assert storage.root.name == f"{media.id}.{image_format}"
    assert storage.root.read_bytes() == pixels
    assert service.get_media_binary_path_by_id(project_id, media.id) == storage.root
    assert thumbnail.is_file()

    service.delete_media(Mock(spec=Project, id=project_id), media.id)

    assert not storage.root.exists()
    assert not thumbnail.exists()
    assert db_session.get(MediaDB, str(media.id)) is None
    assert db_session.get(OmeImageDB, str(media.id)) is None
    with pytest.raises(ResourceNotFoundError):
        service.get_ome_image_info(project_id, media.id)


def test_get_ome_image_info_reloads_persisted_metadata(ome_ingest, db_session):
    service, project_id = ome_ingest
    media = service.create_ome_image(
        project_id,
        "specimen",
        ImageFormat.OME_TIFF,
        BytesIO((ASSETS / "xyczt.ome.tiff").read_bytes()),
        max_size=MAX_SIZE,
    )
    expected = service.get_ome_image_info(project_id, media.id)
    db_session.flush()
    db_session.expunge_all()
    strategy = Mock(spec=ChannelMappingStrategy)
    strategy.compute.side_effect = AssertionError("Retrieving metadata must not recompute the projection.")
    reloaded_service = MediaService(
        service.projects_dir.parent,
        db_session=db_session,
        channel_mapping_strategy=strategy,
    )

    assert reloaded_service.get_ome_image_info(project_id, media.id) == expected
    strategy.compute.assert_not_called()


def test_get_ome_image_info_unknown_media(ome_ingest):
    service, project_id = ome_ingest
    with pytest.raises(ResourceNotFoundError):
        service.get_ome_image_info(project_id, uuid4())


def test_get_ome_image_info_rejects_regular_image(ome_ingest, db_session):
    service, project_id = ome_ingest
    media = MediaDB(
        id=str(uuid4()),
        project_id=str(project_id),
        type=MediaType.IMAGE,
        name="regular",
        format="png",
        width=5,
        height=4,
        size=1,
    )
    db_session.add(media)
    db_session.flush()

    with pytest.raises(ValueError, match="not an OME image"):
        service.get_ome_image_info(project_id, UUID(media.id))


def test_missing_ome_metadata(ome_ingest, db_session):
    service, project_id = ome_ingest
    media = service.create_ome_image(
        project_id, "specimen", ImageFormat.OME_TIFF, BytesIO((ASSETS / "xyc.ome.tiff").read_bytes()), max_size=MAX_SIZE
    )
    db_session.delete(db_session.get(OmeImageDB, str(media.id)))
    db_session.flush()

    with pytest.raises(ResourceNotFoundError, match="OME image metadata was not found"):
        service.get_ome_image_info(project_id, media.id)
    with pytest.raises(ResourceNotFoundError, match="OME image metadata was not found"):
        service.get_media_storage(project_id, media)


@pytest.mark.parametrize("filename", ["malformed.ome.tiff", "not_ome.tiff"])
@pytest.mark.parametrize("stream", [False, True])
def test_invalid_ome_has_no_orphans(ome_ingest, db_session, tmp_path, filename, stream):
    service, project_id = ome_ingest
    upload = tmp_path / filename
    shutil.copyfile(ASSETS / filename, upload)
    original = upload.read_bytes()
    with pytest.raises(InvalidImageError):
        service.create_ome_image(
            project_id, "invalid", ImageFormat.OME_TIFF, BytesIO(original) if stream else upload, max_size=MAX_SIZE
        )
    assert upload.read_bytes() == original
    assert list((service.projects_dir / str(project_id) / "dataset").iterdir()) == []
    assert db_session.scalar(select(func.count()).select_from(MediaDB)) == 0
    assert db_session.scalar(select(func.count()).select_from(OmeImageDB)) == 0


@pytest.mark.parametrize("failure", ["metadata_save", "thumbnail", "disk_full", "mapping"])
def test_ingest_failure_restores_upload(ome_ingest, db_session, tmp_path, failure):
    service, project_id = ome_ingest
    upload = tmp_path / "upload"
    original = (ASSETS / "xyc.ome.tiff").read_bytes()
    upload.write_bytes(original)
    targets = {
        "metadata_save": "app.repositories.ome_image_repo.OmeImageRepository.save",
        "thumbnail": "PIL.Image.Image.save",
        "disk_full": "PIL.Image.Image.save",
        "mapping": "app.services.ome.rgb_channel_mapping.MetadataRgbChannelMappingStrategy.compute",
    }
    error = OSError(errno.ENOSPC, "disk full") if failure == "disk_full" else RuntimeError("failed")
    expected = OmeMediaTooLargeError if failure == "disk_full" else RuntimeError
    with patch(targets[failure], side_effect=error), pytest.raises(expected):
        service.create_ome_image(project_id, "specimen", ImageFormat.OME_TIFF, upload, max_size=MAX_SIZE)
    if failure == "metadata_save":
        db_session.rollback()
    assert upload.read_bytes() == original
    assert list((service.projects_dir / str(project_id) / "dataset").iterdir()) == []
    assert db_session.scalar(select(func.count()).select_from(MediaDB)) == 0
    assert db_session.scalar(select(func.count()).select_from(OmeImageDB)) == 0


@pytest.mark.parametrize(
    "projection",
    [RgbProjection(channels=(RgbChannelAssignment(channel=0, target="blue"),)), GrayscaleProjection(channel=1)],
)
def test_injected_channel_mapping_strategy(ome_ingest, projection):
    service, project_id = ome_ingest
    pixels = (ASSETS / "xyc.ome.tiff").read_bytes()
    existing_media = service.create_ome_image(
        project_id, "existing", ImageFormat.OME_TIFF, BytesIO(pixels), max_size=MAX_SIZE
    )
    existing_mapping = service.get_ome_image_info(project_id, existing_media.id).channel_projection
    strategy = Mock(spec=ChannelMappingStrategy)
    strategy.compute.return_value = projection
    custom_service = MediaService(
        service.projects_dir.parent,
        db_session=service.db_session,
        channel_mapping_strategy=strategy,
    )
    with patch("app.services.media_service.create_ingest_thumbnail", wraps=create_ingest_thumbnail) as create_thumbnail:
        media = custom_service.create_ome_image(
            project_id, "custom", ImageFormat.OME_TIFF, BytesIO(pixels), max_size=MAX_SIZE
        )
    strategy.compute.assert_called_once()
    assert strategy.compute.call_args.args[0].size_c == 3
    assert create_thumbnail.call_args.args[1] == projection
    assert custom_service.get_ome_image_info(project_id, media.id).channel_projection == projection
    assert custom_service.get_ome_image_info(project_id, existing_media.id).channel_projection == existing_mapping
    assert existing_mapping != projection
    # Reading either image uses persisted mappings rather than rerunning the current strategy.
    strategy.compute.assert_called_once()


def _archive(entries):
    data = BytesIO()
    with ZipFile(data, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in entries:
            archive.writestr(name, content)
    data.seek(0)
    return data


def test_archive_ingest_and_delete(ome_ingest, db_session, tmp_path):
    service, project_id = ome_ingest
    pixels = (ASSETS / "xyc.ome.tiff").read_bytes()
    upload = tmp_path / "upload.zip"
    upload.write_bytes(_archive([("nested/image.ome.tiff", pixels), ("nested/readme.txt", b"provenance")]).getvalue())
    media = service.create_ome_image(project_id, "plate", ImageFormat.OME_TIFF, upload, max_size=MAX_SIZE, archive=True)
    assert upload.exists()
    info = service.get_ome_image_info(project_id, media.id)
    assert info.entrypoint == "nested/image.ome.tiff"
    assert info.files == ["nested/image.ome.tiff", "nested/readme.txt"]
    assert media.size == len(pixels) + len(b"provenance")
    storage = service.get_media_storage(project_id, media)
    assert storage.is_directory
    assert storage.effective_path.read_bytes() == pixels
    with pytest.raises(ValueError, match="directory-backed"):
        service.get_media_binary_path(project_id, media)
    service.delete_media(Mock(spec=Project, id=project_id), media.id)
    assert not storage.root.exists()
    assert db_session.get(OmeImageDB, str(media.id)) is None


def test_companion_archive(ome_ingest, companion_storage):
    service, project_id = ome_ingest
    data = _archive([(path.name, path.read_bytes()) for path in sorted(companion_storage.root.iterdir())])
    media = service.create_ome_image(
        project_id, "companion set", ImageFormat.OME_TIFF, data, max_size=MAX_SIZE, archive=True
    )
    info = service.get_ome_image_info(project_id, media.id)
    assert info.size_c == 2
    assert info.entrypoint == "part0.ome.tiff"
    assert info.files == ["part0.ome.tiff", "part1.ome.tiff"]
    from app.services.ome import OmeTiffReader

    with OmeTiffReader().open(service.get_media_storage(project_id, media)) as handle:
        pixels = handle.read_region()
        assert not pixels[0].any()
        assert (pixels[1] == 1).all()


def test_missing_companion_is_rejected(ome_ingest, companion_storage):
    service, project_id = ome_ingest
    data = _archive([("part0.ome.tiff", companion_storage.effective_path.read_bytes())])
    with pytest.raises(InvalidImageError):
        service.create_ome_image(
            project_id, "missing companion", ImageFormat.OME_TIFF, data, max_size=MAX_SIZE, archive=True
        )
    assert list((service.projects_dir / str(project_id) / "dataset").iterdir()) == []


@pytest.mark.parametrize(
    "entries",
    [
        [("../outside.tiff", b"invalid")],
        [("/absolute.tiff", b"invalid")],
        [("C:/outside.tiff", b"invalid")],
        [("nested\\outside.tiff", b"invalid")],
        [("same.tif", b"1"), ("SAME.tif", b"2")],
        [("parent", b"1"), ("parent/child.tif", b"2")],
        [("not_ome.tiff", b"invalid")],
        [],
    ],
)
def test_invalid_archive_cleanup(ome_ingest, entries):
    service, project_id = ome_ingest
    with pytest.raises(InvalidImageError):
        service.create_ome_image(
            project_id, "invalid", ImageFormat.OME_TIFF, _archive(entries), max_size=MAX_SIZE, archive=True
        )
    assert list((service.projects_dir / str(project_id) / "dataset").iterdir()) == []


def test_archive_symlink_is_rejected(ome_ingest):
    service, project_id = ome_ingest
    link = ZipInfo("link.tiff")
    link.create_system = 3
    link.external_attr = 0o120777 << 16
    with pytest.raises(InvalidImageError, match="unsafe"):
        service.create_ome_image(
            project_id,
            "invalid",
            ImageFormat.OME_TIFF,
            _archive([(link, b"../outside")]),
            max_size=MAX_SIZE,
            archive=True,
        )


@pytest.mark.parametrize("archive", [False, True])
def test_ingest_size_limit(ome_ingest, archive):
    service, project_id = ome_ingest
    pixels = (ASSETS / "xyc.ome.tiff").read_bytes()
    data = _archive([("image.ome.tiff", pixels)]) if archive else BytesIO(pixels)
    if archive:
        assert len(data.getvalue()) < len(pixels) - 1
    with pytest.raises(OmeMediaTooLargeError):
        service.create_ome_image(
            project_id, "large", ImageFormat.OME_TIFF, data, max_size=len(pixels) - 1, archive=archive
        )
    assert list((service.projects_dir / str(project_id) / "dataset").iterdir()) == []


@pytest.mark.parametrize("archive", [False, True])
def test_ingest_at_size_limit(ome_ingest, archive):
    service, project_id = ome_ingest
    pixels = (ASSETS / "xyc.ome.tiff").read_bytes()
    data = _archive([("image.ome.tiff", pixels)]) if archive else BytesIO(pixels)
    media = service.create_ome_image(
        project_id, "exact limit", ImageFormat.OME_TIFF, data, max_size=len(pixels), archive=archive
    )
    assert media.size == len(pixels)


@pytest.mark.parametrize("archive", [False, True])
def test_ingest_limit_is_per_operation(ome_ingest, db_session, archive):
    service, project_id = ome_ingest
    pixels = (ASSETS / "xyc.ome.tiff").read_bytes()
    payload = _archive([("image.ome.tiff", pixels)]).getvalue() if archive else pixels

    first = service.create_ome_image(
        project_id, "first", ImageFormat.OME_TIFF, BytesIO(payload), max_size=len(pixels), archive=archive
    )
    with pytest.raises(OmeMediaTooLargeError):
        service.create_ome_image(
            project_id, "too large", ImageFormat.OME_TIFF, BytesIO(payload), max_size=len(pixels) - 1, archive=archive
        )
    second = service.create_ome_image(
        project_id, "second", ImageFormat.OME_TIFF, BytesIO(payload), max_size=len(pixels), archive=archive
    )

    assert first.size == second.size == len(pixels)
    assert db_session.scalar(select(func.count()).select_from(OmeImageDB)) == 2
    assert {media.id for media in service.list_media(project_id)} == {first.id, second.id}


def test_insufficient_storage(ome_ingest):
    service, project_id = ome_ingest
    with (
        patch("app.services.ome.ingest.shutil.disk_usage") as disk_usage,
        pytest.raises(OmeMediaTooLargeError, match="storage"),
    ):
        disk_usage.return_value.free = 0
        service.create_ome_image(
            project_id,
            "large",
            ImageFormat.OME_TIFF,
            BytesIO((ASSETS / "xyc.ome.tiff").read_bytes()),
            max_size=MAX_SIZE,
        )


@pytest.mark.parametrize("archive", [False, True])
def test_oversized_decoded_segment_restores_upload(ome_ingest, db_session, tmp_path, archive):
    service, project_id = ome_ingest
    upload = tmp_path / "claimed-upload"
    pixels = (ASSETS / "xyc.ome.tiff").read_bytes()
    original = _archive([("image.ome.tiff", pixels)]).getvalue() if archive else pixels
    upload.write_bytes(original)
    with (
        patch("app.services.ome.ome_tiff_reader._MAX_SEGMENT_BYTES", 1),
        pytest.raises(InvalidImageError, match="read/decode limit"),
    ):
        service.create_ome_image(
            project_id, "specimen", ImageFormat.OME_TIFF, upload, max_size=MAX_SIZE, archive=archive
        )

    assert upload.read_bytes() == original
    assert list((service.projects_dir / str(project_id) / "dataset").iterdir()) == []
    assert db_session.scalar(select(func.count()).select_from(MediaDB)) == 0
    assert db_session.scalar(select(func.count()).select_from(OmeImageDB)) == 0


@pytest.mark.parametrize("archive", [False, True])
def test_discard_after_commit_failure_restores_claimed_upload(ome_ingest, tmp_path, archive):
    service, project_id = ome_ingest
    upload = tmp_path / "claimed-upload"
    pixels = (ASSETS / "xyc.ome.tiff").read_bytes()
    original = _archive([("image.ome.tiff", pixels)]).getvalue() if archive else pixels
    upload.write_bytes(original)
    media = service.create_ome_image(
        project_id, "specimen", ImageFormat.OME_TIFF, upload, max_size=MAX_SIZE, archive=archive
    )
    storage = service.get_media_storage(project_id, media)
    service.db_session.rollback()
    service.discard_ome_image(project_id, media.id, storage, upload)
    assert upload.read_bytes() == original
    assert list((service.projects_dir / str(project_id) / "dataset").iterdir()) == []
