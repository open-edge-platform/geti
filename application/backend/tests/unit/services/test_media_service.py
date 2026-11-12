# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4

from app.models.media import Image, ImageFormat, MediaType, Video, VideoFormat
from app.services.media_service import MediaService


class TestMediaServicePaths:
    def test_get_media_binary_path_for_image(self, tmp_path):
        service = MediaService(data_dir=tmp_path)
        project_id = uuid4()
        media_id = uuid4()
        image = Image(
            id=media_id,
            type=MediaType.IMAGE,
            project_id=project_id,
            name="sample-image",
            format=ImageFormat.PNG,
            width=100,
            height=50,
            size=123,
            source_id=None,
        )

        path = service.get_media_binary_path(project_id=project_id, media=image)

        assert path == tmp_path / f"projects/{project_id}/dataset/{media_id}.png"

    def test_get_media_binary_path_for_video(self, tmp_path):
        service = MediaService(data_dir=tmp_path)
        project_id = uuid4()
        media_id = uuid4()
        video = Video(
            id=media_id,
            type=MediaType.VIDEO,
            project_id=project_id,
            name="sample-video",
            format=VideoFormat.MP4,
            width=1920,
            height=1080,
            size=321,
            source_id=None,
            fps=30.0,
            frame_count=600,
        )

        path = service.get_media_binary_path(project_id=project_id, media=video)

        assert path == tmp_path / f"projects/{project_id}/dataset/{media_id}.mp4"
