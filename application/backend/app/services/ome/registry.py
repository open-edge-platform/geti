# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence

from app.models import MediaStorage

from .protocols import OmeReader


class UnsupportedOmeStorageError(RuntimeError):
    """Raised when no registered OME reader can handle the provided storage."""


class OmeReaderRegistry:
    """Selects an OME reader implementation by probing a media storage."""

    def __init__(self, readers: Sequence[OmeReader] | None = None) -> None:
        self._readers: list[OmeReader] = list(readers or [])

    def register(self, reader: OmeReader) -> None:
        self._readers.append(reader)

    def get_reader(self, storage: MediaStorage) -> OmeReader:
        for reader in self._readers:
            if reader.probe(storage):
                return reader
        raise UnsupportedOmeStorageError(f"No OME reader can handle storage at '{storage.root}'.")
