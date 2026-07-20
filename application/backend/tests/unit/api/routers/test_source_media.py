# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import io
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import status

from app.api.dependencies import get_source_media_service
from app.services import SourceMediaService


@pytest.fixture
def fxt_source_media_service(fxt_app) -> Generator[AsyncMock]:
    source_media_service = AsyncMock(spec=SourceMediaService)
    fxt_app.dependency_overrides[get_source_media_service] = lambda: source_media_service
    yield source_media_service
    fxt_app.dependency_overrides.pop(get_source_media_service, None)


class TestSourceMediaEndpoints:
    def test_upload_source_media_success(self, fxt_source_media_service, fxt_client):
        resolved_path = Path("/data/source_media/712750b2-5a82-47ee-8fba-f3dc96cb615d/sample.mp4")
        fxt_source_media_service.upload.return_value = resolved_path

        response = fxt_client.post(
            "/api/sources/media",
            files={"file": ("sample.mp4", io.BytesIO(b"fake-video-bytes"), "video/mp4")},
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"video_path": str(resolved_path)}
        fxt_source_media_service.upload.assert_called_once()
        _, kwargs = fxt_source_media_service.upload.call_args
        assert kwargs["filename"] == "sample.mp4"

    @pytest.mark.parametrize("filename", ["sample.txt", "sample.zip", "sample.jpg", "sample"])
    def test_upload_source_media_unsupported_format(self, fxt_source_media_service, fxt_client, filename):
        response = fxt_client.post(
            "/api/sources/media",
            files={"file": (filename, io.BytesIO(b"not-a-video"), "application/octet-stream")},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        fxt_source_media_service.upload.assert_not_called()

    @pytest.mark.parametrize(
        "extension", ["mp4", "avi", "mov", "mkv", "webm", "flv", "wmv", "m4v", "mpg", "mpeg", "MP4"]
    )
    def test_upload_source_media_accepts_supported_extensions(self, fxt_source_media_service, fxt_client, extension):
        fxt_source_media_service.upload.return_value = Path(f"/data/source_media/uuid/video.{extension}")

        response = fxt_client.post(
            "/api/sources/media",
            files={"file": (f"video.{extension}", io.BytesIO(b"fake-video-bytes"), "application/octet-stream")},
        )

        assert response.status_code == status.HTTP_201_CREATED
        fxt_source_media_service.upload.assert_called_once()
