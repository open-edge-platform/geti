# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import MediaStorage


def test_media_storage_file_effective_path() -> None:
    storage = MediaStorage(root=Path("media/sample.png"))

    assert storage.is_directory is False
    assert storage.effective_path == Path("media/sample.png")


def test_media_storage_directory_effective_path() -> None:
    storage = MediaStorage(root=Path("media/folder"), entrypoint=Path("entry.ome.tiff"))

    assert storage.is_directory is True
    assert storage.effective_path == Path("media/folder/entry.ome.tiff")


@pytest.mark.parametrize(
    "entrypoint",
    [
        Path(f"{Path.cwd().anchor}entry.ome"),  # absolute on both POSIX (/entry.ome) and Windows (C:\entry.ome)
        Path("../entry.ome"),
        Path("nested/../entry.ome"),
    ],
)
def test_media_storage_rejects_invalid_entrypoint(entrypoint: Path) -> None:
    with pytest.raises(ValidationError, match="entrypoint must be a relative path inside root"):
        MediaStorage(root=Path("media/folder"), entrypoint=entrypoint)


def test_media_storage_accepts_relative_entrypoint() -> None:
    storage = MediaStorage(root=Path("media/folder"), entrypoint=Path("nested/entry.ome"))

    assert storage.entrypoint == Path("nested/entry.ome")
