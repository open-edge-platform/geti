# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from io import BytesIO
from pathlib import Path

import pytest

from app.services.source_media_service import SourceMediaService


@pytest.fixture
def fxt_source_media_service(tmp_path: Path) -> SourceMediaService:
    return SourceMediaService(source_media_dir=tmp_path)


class TestSourceMediaService:
    @pytest.mark.asyncio
    async def test_upload_writes_file_and_returns_resolved_path(
        self, tmp_path: Path, fxt_source_media_service: SourceMediaService
    ):
        filename = "sample.mp4"
        content = b"fake-video-bytes"

        video_path = await fxt_source_media_service.upload(filename=filename, file_obj=BytesIO(content))

        assert video_path.name == filename
        assert video_path.is_file()
        assert video_path.read_bytes() == content
        assert video_path.is_absolute()
        assert video_path.parent.parent == tmp_path

    @pytest.mark.asyncio
    async def test_upload_generates_unique_paths_for_same_filename(self, fxt_source_media_service: SourceMediaService):
        first_path = await fxt_source_media_service.upload(filename="sample.mp4", file_obj=BytesIO(b"first"))
        second_path = await fxt_source_media_service.upload(filename="sample.mp4", file_obj=BytesIO(b"second"))

        assert first_path != second_path
        assert first_path.read_bytes() == b"first"
        assert second_path.read_bytes() == b"second"

    @pytest.mark.asyncio
    async def test_upload_cleans_up_temp_file_on_failure(
        self, tmp_path: Path, fxt_source_media_service: SourceMediaService, monkeypatch: pytest.MonkeyPatch
    ):
        def _boom(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr("shutil.copyfileobj", _boom)

        with pytest.raises(OSError, match="disk full"):
            await fxt_source_media_service.upload(filename="sample.mp4", file_obj=BytesIO(b"data"))

        leftovers = list(tmp_path.rglob("*"))
        assert all(not p.is_file() for p in leftovers)
