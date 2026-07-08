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
    @pytest.mark.parametrize(
        "malicious_filename",
        [
            "../../etc/passwd.mp4",
            "../../../etc/cron.d/evil.mp4",
            "/etc/passwd.mp4",
            "a/b/../../../etc/passwd.mp4",
        ],
    )
    async def test_upload_sanitizes_path_traversal_filenames(
        self, tmp_path: Path, fxt_source_media_service: SourceMediaService, malicious_filename: str
    ):
        video_path = await fxt_source_media_service.upload(filename=malicious_filename, file_obj=BytesIO(b"payload"))

        # The stored file must stay confined to source_media_dir; only the final path
        # component of the supplied filename is honored.
        assert video_path.is_relative_to(tmp_path.resolve())
        assert ".." not in video_path.parts
        assert video_path.name == Path(malicious_filename).name

    @pytest.mark.asyncio
    @pytest.mark.parametrize("empty_filename", ["", ".", "..", "../", "a/../"])
    async def test_upload_rejects_filenames_without_a_usable_name(
        self, fxt_source_media_service: SourceMediaService, empty_filename: str
    ):
        with pytest.raises(ValueError, match="Invalid filename"):
            await fxt_source_media_service.upload(filename=empty_filename, file_obj=BytesIO(b"payload"))

    @pytest.mark.asyncio
    async def test_upload_cleans_up_temp_file_on_failure(
        self, tmp_path: Path, fxt_source_media_service: SourceMediaService, monkeypatch: pytest.MonkeyPatch
    ):
        def _boom(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr("shutil.copyfileobj", _boom)

        with pytest.raises(OSError, match="disk full"):
            await fxt_source_media_service.upload(filename="sample.mp4", file_obj=BytesIO(b"data"))

        # The whole per-upload UUID subdirectory should be removed, not just the temp file.
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.asyncio
    async def test_delete_video_removes_upload_subdirectory(
        self, tmp_path: Path, fxt_source_media_service: SourceMediaService
    ):
        video_path = await fxt_source_media_service.upload(filename="sample.mp4", file_obj=BytesIO(b"data"))
        upload_dir = video_path.parent
        assert upload_dir.is_dir()

        fxt_source_media_service.delete_video(str(video_path))

        assert not upload_dir.exists()
        assert list(tmp_path.iterdir()) == []

    def test_delete_video_noop_when_outside_source_media_dir(
        self, tmp_path: Path, fxt_source_media_service: SourceMediaService
    ):
        outside_dir = tmp_path.parent / f"outside-{tmp_path.name}"
        outside_dir.mkdir()
        outside_file = outside_dir / "video.mp4"
        outside_file.write_bytes(b"data")

        fxt_source_media_service.delete_video(str(outside_file))

        assert outside_file.exists()

    def test_delete_video_noop_when_path_is_directly_under_root(
        self, tmp_path: Path, fxt_source_media_service: SourceMediaService
    ):
        root_level_file = tmp_path / "video.mp4"
        root_level_file.write_bytes(b"data")

        fxt_source_media_service.delete_video(str(root_level_file))

        # No UUID subdirectory boundary, so nothing should be removed (avoids ever
        # rmtree-ing the whole source_media_dir root).
        assert root_level_file.exists()

    def test_delete_video_noop_when_path_is_source_media_root_itself(self, tmp_path: Path):
        # Use a nested dir so a buggy implementation can't accidentally delete pytest's temp root.
        source_media_root = tmp_path / "source_media"
        source_media_root.mkdir()

        service = SourceMediaService(source_media_dir=source_media_root)
        service.delete_video(str(source_media_root))

        assert source_media_root.exists()

    @pytest.mark.asyncio
    async def test_delete_video_propagates_oserror(
        self,
        fxt_source_media_service: SourceMediaService,
        monkeypatch: pytest.MonkeyPatch,
    ):
        video_path = await fxt_source_media_service.upload(filename="sample.mp4", file_obj=BytesIO(b"data"))

        def _boom(*args, **kwargs):
            raise OSError("permission denied")

        monkeypatch.setattr("shutil.rmtree", _boom)

        with pytest.raises(OSError, match="permission denied"):
            fxt_source_media_service.delete_video(str(video_path))
