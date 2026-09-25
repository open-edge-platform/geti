# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import io
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status

from app.api.dependencies import get_source_media_service, get_source_service
from app.services import SourceMediaService, SourceService
from app.services.base import ResourceInUseError, ResourceNotFoundError, ResourceType


@pytest.fixture
def fxt_source_media_service(fxt_app) -> Generator[AsyncMock]:
    source_media_service = AsyncMock(spec=SourceMediaService)
    fxt_app.dependency_overrides[get_source_media_service] = lambda: source_media_service
    yield source_media_service
    fxt_app.dependency_overrides.pop(get_source_media_service, None)


@pytest.fixture
def fxt_source_service(fxt_app) -> Generator[MagicMock]:
    source_service = MagicMock(spec=SourceService)
    fxt_app.dependency_overrides[get_source_service] = lambda: source_service
    yield source_service
    fxt_app.dependency_overrides.pop(get_source_service, None)


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

    def test_delete_source_media_success(self, fxt_source_service, fxt_client):
        deleted_paths = ["/data/source_media/712750b2-5a82-47ee-8fba-f3dc96cb615d/sample.mp4"]
        fxt_source_service.delete_unreferenced_media.return_value = deleted_paths

        response = fxt_client.delete("/api/sources/media/sample.mp4")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"deleted_video_paths": deleted_paths}
        fxt_source_service.delete_unreferenced_media.assert_called_once_with("sample.mp4")

    def test_delete_source_media_not_found(self, fxt_source_service, fxt_client):
        fxt_source_service.delete_unreferenced_media.side_effect = ResourceNotFoundError(
            ResourceType.MEDIA, "sample.mp4"
        )

        response = fxt_client.delete("/api/sources/media/sample.mp4")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_source_media_in_use(self, fxt_source_service, fxt_client):
        fxt_source_service.delete_unreferenced_media.side_effect = ResourceInUseError(
            ResourceType.MEDIA, "sample.mp4", "in use by a video_file source"
        )

        response = fxt_client.delete("/api/sources/media/sample.mp4")

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_delete_source_media_invalid_filename(self, fxt_source_service, fxt_client):
        # Backslash traversal stays a single path segment, so it reaches the route handler
        # and exercises the ValueError -> 400 mapping. Separator-based traversal
        # ("../x", "a/b") is covered by the service-level rejection tests.
        fxt_source_service.delete_unreferenced_media.side_effect = ValueError("Invalid filename: '..\\sample.mp4'")

        response = fxt_client.delete("/api/sources/media/..\\sample.mp4")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
