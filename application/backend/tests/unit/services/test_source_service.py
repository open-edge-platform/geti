# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from uuid import uuid4

import pytest

from app.models import SourceType
from app.models.source import SourceAdapter, VideoFileConfig
from app.services.base import ResourceInUseError, ResourceNotFoundError
from app.services.source_media_service import SourceMediaService
from app.services.source_service import SourceService


@pytest.fixture
def fxt_source_media_service(tmp_path: Path) -> SourceMediaService:
    return SourceMediaService(source_media_dir=tmp_path)


@pytest.fixture
def fxt_source_service(fxt_source_media_service: SourceMediaService) -> SourceService:
    return SourceService(db_session=None, source_media_service=fxt_source_media_service)


def _store_upload(source_media_dir: Path, filename: str) -> Path:
    upload_dir = source_media_dir / str(uuid4())
    upload_dir.mkdir(parents=True)
    upload_path = upload_dir / filename
    upload_path.write_bytes(b"fake-video-bytes")
    return upload_path.resolve()


def _video_file_source(video_path: str):
    return SourceAdapter.validate_python(
        {
            "id": str(uuid4()),
            "name": "video source",
            "source_type": SourceType.VIDEO_FILE,
            "config_data": VideoFileConfig(video_path=video_path),
        }
    )


class TestDeleteUnreferencedMedia:
    def test_deletes_all_unreferenced_copies(
        self, tmp_path: Path, fxt_source_service: SourceService, monkeypatch: pytest.MonkeyPatch
    ):
        first_path = _store_upload(tmp_path, "sample.mp4")
        second_path = _store_upload(tmp_path, "sample.mp4")
        referenced_path = _store_upload(tmp_path, "other.mp4")
        monkeypatch.setattr(fxt_source_service, "list_all", lambda: [_video_file_source(str(referenced_path))])

        deleted_paths = fxt_source_service.delete_unreferenced_media("sample.mp4")

        assert sorted(deleted_paths) == sorted([str(first_path), str(second_path)])
        assert not first_path.parent.exists()
        assert not second_path.parent.exists()
        assert referenced_path.is_file()

    def test_raises_in_use_and_keeps_files_when_referenced(
        self, tmp_path: Path, fxt_source_service: SourceService, monkeypatch: pytest.MonkeyPatch
    ):
        referenced_path = _store_upload(tmp_path, "sample.mp4")
        unreferenced_path = _store_upload(tmp_path, "sample.mp4")
        monkeypatch.setattr(fxt_source_service, "list_all", lambda: [_video_file_source(str(referenced_path))])

        with pytest.raises(ResourceInUseError, match="in use by a video_file source"):
            fxt_source_service.delete_unreferenced_media("sample.mp4")

        assert referenced_path.is_file()
        assert unreferenced_path.is_file()

    def test_detects_equivalent_path_spellings(
        self, fxt_source_service: SourceService, monkeypatch: pytest.MonkeyPatch
    ):
        referenced_path = _store_upload(fxt_source_service._source_media_service._source_media_dir, "sample.mp4")
        # Same location, but spelled with a '..' segment: a raw-string comparison would
        # miss it, a resolved-path comparison must not.
        equivalent_spelling = f"{referenced_path.parent}/../{referenced_path.parent.name}/{referenced_path.name}"
        monkeypatch.setattr(fxt_source_service, "list_all", lambda: [_video_file_source(equivalent_spelling)])

        with pytest.raises(ResourceInUseError, match="in use by a video_file source"):
            fxt_source_service.delete_unreferenced_media("sample.mp4")

        assert referenced_path.is_file()

    def test_restores_uploads_when_reference_appears_concurrently(
        self, fxt_source_service: SourceService, monkeypatch: pytest.MonkeyPatch
    ):
        # First reference check passes; a source committing between the check and the
        # deletion must make the endpoint refuse and restore the quarantined uploads.
        source_media_dir = fxt_source_service._source_media_service._source_media_dir
        sample_path = _store_upload(source_media_dir, "sample.mp4")
        other_path = _store_upload(source_media_dir, "sample.mp4")
        list_all_results = iter([[], [_video_file_source(str(sample_path))]])
        monkeypatch.setattr(fxt_source_service, "list_all", lambda: next(list_all_results))

        with pytest.raises(ResourceInUseError, match="in use by a video_file source"):
            fxt_source_service.delete_unreferenced_media("sample.mp4")

        assert sample_path.is_file()
        assert other_path.is_file()
        assert set(source_media_dir.iterdir()) == {sample_path.parent, other_path.parent}

    def test_raises_not_found_when_upload_disappears(
        self,
        fxt_source_media_service: SourceMediaService,
        fxt_source_service: SourceService,
        monkeypatch: pytest.MonkeyPatch,
    ):
        vanished_path = fxt_source_media_service._source_media_dir / "missing-uuid" / "sample.mp4"
        monkeypatch.setattr(fxt_source_media_service, "find_uploads_by_filename", lambda _filename: [vanished_path])
        monkeypatch.setattr(fxt_source_service, "list_all", list)

        with pytest.raises(ResourceNotFoundError, match="sample.mp4"):
            fxt_source_service.delete_unreferenced_media("sample.mp4")

    def test_raises_not_found_when_no_upload_matches(
        self, tmp_path: Path, fxt_source_service: SourceService, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(fxt_source_service, "list_all", list)

        with pytest.raises(ResourceNotFoundError, match="sample.mp4"):
            fxt_source_service.delete_unreferenced_media("sample.mp4")

    def test_propagates_value_error_for_invalid_filename(
        self, fxt_source_service: SourceService, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(fxt_source_service, "list_all", list)

        with pytest.raises(ValueError, match="Invalid filename"):
            fxt_source_service.delete_unreferenced_media("../sample.mp4")

    def test_raises_not_found_without_media_service(self, tmp_path: Path):
        source_service = SourceService(db_session=None, source_media_service=None)

        with pytest.raises(ResourceNotFoundError, match="sample.mp4"):
            source_service.delete_unreferenced_media("sample.mp4")
