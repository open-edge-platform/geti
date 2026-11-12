# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import shutil
from pathlib import Path
from typing import Protocol


class MediaStorageLike(Protocol):
    @property
    def root(self) -> Path: ...

    @property
    def is_directory(self) -> bool: ...


def media_storage_size(storage: MediaStorageLike) -> int:
    """Return payload size in bytes for single-file or directory-backed media."""
    if not storage.is_directory:
        return storage.root.stat().st_size

    return sum(path.stat().st_size for path in storage.root.rglob("*") if path.is_file())


def move_media_storage(source: MediaStorageLike, target: MediaStorageLike) -> None:
    """Move a media payload (file or directory) to a new location."""
    target.root.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source.root), str(target.root))


def delete_media_storage(storage: MediaStorageLike) -> None:
    """Delete a media payload from disk."""
    if storage.is_directory:
        shutil.rmtree(storage.root)
        return
    storage.root.unlink()


def discard_media_storage(storage: MediaStorageLike, source_storage: MediaStorageLike | None) -> None:
    """Remove a failed payload, or restore it to its source location when it was moved."""
    if source_storage is not None:
        move_media_storage(storage, source_storage)
        return
    if storage.root.exists():
        delete_media_storage(storage)
