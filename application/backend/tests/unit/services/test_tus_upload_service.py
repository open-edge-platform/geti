# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID

import pytest

import app.services.tus_upload_service as tus_upload_module
from app.services.tus_upload_service import (
    TusUploadConflictError,
    TusUploadInvalidError,
    TusUploadNotFoundError,
    TusUploadService,
)


async def _chunks(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


@pytest.fixture
def tus_service(tmp_path: Path) -> TusUploadService:
    return TusUploadService(uploads_dir=tmp_path / "uploads", max_size=1024, expiration_seconds=3600)


def test_create_upload_decodes_metadata_and_persists(tus_service: TusUploadService) -> None:
    encoded_filename = base64.b64encode(b"image.png").decode("ascii")

    upload = tus_service.create(length=4, metadata_header=f"filename {encoded_filename}")

    assert upload.offset == 0
    assert upload.length == 4
    assert upload.metadata == {"filename": "image.png"}
    assert tus_service.get(upload.id) == upload
    assert upload.path.read_bytes() == b""


@pytest.mark.asyncio
async def test_append_resumes_from_persisted_offset(tus_service: TusUploadService) -> None:
    upload = tus_service.create(length=6, metadata_header=None)
    first_patch = await tus_service.append(upload.id, 0, _chunks(b"abc"))
    resumed_patch = await tus_service.append(upload.id, 3, _chunks(b"def"))

    assert first_patch.offset == 3
    assert resumed_patch.offset == 6
    assert tus_service.get(upload.id).path.read_bytes() == b"abcdef"


@pytest.mark.asyncio
async def test_append_rejects_wrong_offset_and_excess_bytes(tus_service: TusUploadService) -> None:
    upload = tus_service.create(length=2, metadata_header=None)

    with pytest.raises(TusUploadConflictError, match="offset mismatch"):
        await tus_service.append(upload.id, 1, _chunks(b"a"))
    with pytest.raises(TusUploadInvalidError, match="exceeds"):
        await tus_service.append(upload.id, 0, _chunks(b"too long"))

    assert tus_service.get(upload.id).offset == 0


@pytest.mark.asyncio
async def test_claim_requires_completion_and_prevents_reuse(tus_service: TusUploadService) -> None:
    upload = tus_service.create(length=1, metadata_header=None)
    with pytest.raises(TusUploadConflictError, match="incomplete"):
        await tus_service.claim_completed(upload.id)


@pytest.mark.asyncio
async def test_completed_upload_is_single_use(tus_service: TusUploadService) -> None:
    upload = tus_service.create(length=1, metadata_header=None)
    await tus_service.append(upload.id, 0, _chunks(b"x"))

    claimed = await tus_service.claim_completed(UUID(str(upload.id)))
    assert claimed.claimed
    with pytest.raises(TusUploadConflictError, match="already being consumed"):
        await tus_service.claim_completed(upload.id)

    tus_service.release_claim(upload.id)
    assert not tus_service.get(upload.id).claimed
    await tus_service.claim_completed(upload.id)
    tus_service.delete_claimed(upload.id)
    with pytest.raises(TusUploadNotFoundError):
        tus_service.get(upload.id)


@pytest.mark.asyncio
async def test_completed_consumer_result_is_cached(tus_service: TusUploadService) -> None:
    upload = tus_service.create(length=1, metadata_header=None)
    await tus_service.append(upload.id, 0, _chunks(b"x"))
    await tus_service.claim_completed(upload.id)
    result = {"id": "item-id"}

    tus_service.complete_claim(upload.id, "media:project-id", result)

    assert not upload.path.exists()
    assert tus_service.get_consumed_result(upload.id, "media:project-id") == result
    with pytest.raises(TusUploadConflictError, match="different operation"):
        tus_service.get_consumed_result(upload.id, "staged_dataset")


def test_create_rejects_oversize_and_malformed_metadata(tus_service: TusUploadService) -> None:
    with pytest.raises(TusUploadInvalidError, match="exceeds"):
        tus_service.create(length=1025, metadata_header=None)
    with pytest.raises(TusUploadInvalidError, match="base64"):
        tus_service.create(length=1, metadata_header="filename !!!")


def test_cleanup_removes_expired_uploads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [100.0]
    monkeypatch.setattr(tus_upload_module, "time", lambda: clock[0])
    service = TusUploadService(tmp_path / "uploads", max_size=1024, expiration_seconds=10)
    upload = service.create(length=1, metadata_header=None)
    clock[0] = 111.0

    assert service.cleanup_expired() == 1
    with pytest.raises(TusUploadNotFoundError):
        service.get(upload.id)


@pytest.mark.asyncio
async def test_cleanup_does_not_remove_upload_during_patch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [100.0]
    monkeypatch.setattr(tus_upload_module, "time", lambda: clock[0])
    service = TusUploadService(tmp_path / "uploads", max_size=1024, expiration_seconds=10)
    upload = service.create(length=1, metadata_header=None)

    async def patch_body() -> AsyncIterator[bytes]:
        clock[0] = 111.0
        assert service.cleanup_expired() == 0
        yield b"x"

    assert (await service.append(upload.id, 0, patch_body())).offset == 1
    assert service.cleanup_expired() == 1


@pytest.mark.asyncio
async def test_cleanup_does_not_remove_claimed_upload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [100.0]
    monkeypatch.setattr(tus_upload_module, "time", lambda: clock[0])
    service = TusUploadService(tmp_path / "uploads", max_size=1024, expiration_seconds=10)
    upload = service.create(length=0, metadata_header=None)
    await service.claim_completed(upload.id)

    clock[0] = 111.0
    assert service.cleanup_expired() == 0
    restarted_service = TusUploadService(tmp_path / "uploads", max_size=1024, expiration_seconds=10)
    assert restarted_service.cleanup_expired() == 1

    # A separate active claim still finishes successfully even after its expiry deadline.
    clock[0] = 120.0
    upload = service.create(length=0, metadata_header=None)
    await service.claim_completed(upload.id)
    clock[0] = 131.0
    assert service.cleanup_expired() == 0
    service.complete_claim(upload.id, "staged_dataset", {"id": "item-id"})
    assert service.cleanup_expired() == 1
