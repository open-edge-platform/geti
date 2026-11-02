# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

import pytest

from app.api.schemas.media import MediaViewAdapter
from app.db.schema import MediaDB
from app.models.media import (
    ImageFormat,
    MediaAdapter,
    MediaType,
    OmeFormat,
    OmeImage,
    OmePlane,
    VideoFormat,
    VideoFrame,
    parse_media_format,
    split_media_file_name,
)


class TestMediaFormat:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("a.ome.tiff", OmeFormat.OME_TIFF),
            ("a.OME.TIF", OmeFormat.OME_TIF),
            ("ome.tiff", OmeFormat.OME_TIFF),
            ("b.tiff", ImageFormat.TIFF),
            ("tiff", ImageFormat.TIFF),
            ("JPG", ImageFormat.JPG),
            ("clip.mp4", VideoFormat.MP4),
            ("archive.zip", None),
        ],
    )
    def test_parse_media_format_prefers_longest_suffix(self, value, expected):
        assert parse_media_format(value) == expected

    @pytest.mark.parametrize(
        "file_name, expected",
        [
            ("plate_A01.ome.tiff", ("plate_A01", "ome.tiff")),
            ("plate.v2.OME.TIF", ("plate.v2", "OME.TIF")),
            ("photo.tiff", ("photo", "tiff")),
            ("archive.tar.gz", ("archive.tar", "gz")),
            ("no_extension", ("no_extension", "")),
            (".ome.tiff", (".ome", "tiff")),
        ],
    )
    def test_split_media_file_name_keeps_compound_extensions(self, file_name, expected):
        assert split_media_file_name(file_name) == expected


def _db_media(**kwargs) -> MediaDB:
    defaults = {
        "id": str(uuid4()),
        "project_id": str(uuid4()),
        "name": "media",
        "width": 48,
        "height": 32,
        "size": 1024,
        "source_id": None,
    }
    return MediaDB(**{**defaults, **kwargs})


class TestLeafMediaParentMapping:
    def test_video_frame_exposes_orm_parent_id_as_video_id(self):
        video_id = str(uuid4())
        db_media = _db_media(type=MediaType.VIDEO_FRAME, format="jpg", parent_id=video_id, frame_index=4)

        video_frame = MediaAdapter.validate_python(db_media)

        assert isinstance(video_frame, VideoFrame)
        assert str(video_frame.video_id) == video_id

    def test_video_frame_view_keeps_video_id_on_the_wire(self):
        video_id = str(uuid4())
        db_media = _db_media(type=MediaType.VIDEO_FRAME, format="jpg", parent_id=video_id, frame_index=4)

        payload = MediaViewAdapter.dump_python(
            MediaViewAdapter.validate_python(MediaAdapter.validate_python(db_media), from_attributes=True),
            mode="json",
        )

        assert payload["video_id"] == video_id
        assert "parent_id" not in payload

    def test_ome_image_exposes_frame_count_as_plane_count(self):
        db_media = _db_media(type=MediaType.OME_IMAGE, format="ome.tiff", frame_count=12)

        ome_image = MediaAdapter.validate_python(db_media)

        assert isinstance(ome_image, OmeImage)
        assert ome_image.plane_count == 12
        assert ome_image.format == OmeFormat.OME_TIFF

    def test_ome_plane_exposes_orm_parent_id_as_ome_image_id(self):
        ome_image_id = str(uuid4())
        db_media = _db_media(
            type=MediaType.OME_PLANE, format="png", parent_id=ome_image_id, frame_index=5, z_index=1, t_index=1
        )

        ome_plane = MediaAdapter.validate_python(db_media)
        payload = MediaViewAdapter.dump_python(
            MediaViewAdapter.validate_python(ome_plane, from_attributes=True), mode="json"
        )

        assert isinstance(ome_plane, OmePlane)
        assert payload["ome_image_id"] == ome_image_id
        assert (payload["z_index"], payload["t_index"]) == (1, 1)
