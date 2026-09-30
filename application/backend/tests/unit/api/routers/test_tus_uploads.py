# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
from collections.abc import Generator
from pathlib import Path
from uuid import UUID

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.api.dependencies import get_tus_upload_service
from app.services.tus_upload_service import TusUploadService

TUS_HEADERS = {"Tus-Resumable": "1.0.0"}


@pytest.fixture
def fxt_tus_service(fxt_app: FastAPI, tmp_path: Path) -> Generator[TusUploadService]:
    service = TusUploadService(uploads_dir=tmp_path / "uploads", max_size=1024, expiration_seconds=3600)
    fxt_app.dependency_overrides[get_tus_upload_service] = lambda: service
    yield service
    fxt_app.dependency_overrides.pop(get_tus_upload_service, None)


def test_create_patch_and_resume_upload(fxt_client: TestClient, fxt_tus_service: TusUploadService) -> None:
    encoded_filename = base64.b64encode(bytearray(b"dataset.zip")).decode("ascii")
    created = fxt_client.post(
        "/api/uploads",
        headers={**TUS_HEADERS, "Upload-Length": "6", "Upload-Metadata": f"filename {encoded_filename}"},
    )

    assert created.status_code == status.HTTP_201_CREATED
    assert created.headers["Tus-Resumable"] == "1.0.0"
    assert created.headers["Upload-Offset"] == "0"
    upload_url = created.headers["Location"]

    first_patch = fxt_client.patch(
        upload_url,
        headers={**TUS_HEADERS, "Upload-Offset": "0", "Content-Type": "application/offset+octet-stream"},
        content=b"abc",
    )
    assert first_patch.status_code == status.HTTP_204_NO_CONTENT
    assert first_patch.headers["Upload-Offset"] == "3"

    resumed = fxt_client.head(upload_url, headers=TUS_HEADERS)
    assert resumed.status_code == status.HTTP_200_OK
    assert resumed.headers["Upload-Offset"] == "3"
    assert resumed.headers["Upload-Length"] == "6"

    second_patch = fxt_client.patch(
        upload_url,
        headers={**TUS_HEADERS, "Upload-Offset": "3", "Content-Type": "application/offset+octet-stream"},
        content=b"def",
    )
    assert second_patch.status_code == status.HTTP_204_NO_CONTENT
    upload_id = UUID(created.headers["Location"].rsplit("/", 1)[-1])
    assert fxt_tus_service.get(upload_id).path.read_bytes() == b"abcdef"


def test_patch_rejects_stale_offset(fxt_client: TestClient, fxt_tus_service: TusUploadService) -> None:
    created = fxt_client.post("/api/uploads", headers={**TUS_HEADERS, "Upload-Length": "2"})
    patch = fxt_client.patch(
        created.headers["Location"],
        headers={**TUS_HEADERS, "Upload-Offset": "1", "Content-Type": "application/offset+octet-stream"},
        content=b"a",
    )

    assert patch.status_code == status.HTTP_409_CONFLICT


def test_tus_requires_supported_protocol_version(fxt_client: TestClient, fxt_tus_service: TusUploadService) -> None:
    response = fxt_client.post("/api/uploads", headers={"Upload-Length": "0"})

    assert response.status_code == status.HTTP_412_PRECONDITION_FAILED
    assert response.headers["Tus-Version"] == "1.0.0"
