# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from app.models import MediaStorage
from app.services.ome import OmeReaderRegistry, UnsupportedOmeStorageError


class _ReaderAlwaysFalse:
    def probe(self, storage: MediaStorage) -> bool:
        return False

    def open(self, storage: MediaStorage, series: int = 0):
        raise AssertionError("open() should not be called when probe() is False")


class _ReaderForOmeTiff:
    def probe(self, storage: MediaStorage) -> bool:
        return storage.root.suffixes[-2:] == [".ome", ".tiff"]

    def open(self, storage: MediaStorage, series: int = 0):
        raise NotImplementedError


class TestOmeReaderRegistry:
    def test_get_reader_returns_matching_reader(self) -> None:
        matching_reader = _ReaderForOmeTiff()
        registry = OmeReaderRegistry(readers=[_ReaderAlwaysFalse(), matching_reader])

        reader = registry.get_reader(MediaStorage(root=Path("sample.ome.tiff")))

        assert reader is matching_reader

    def test_get_reader_raises_for_unsupported_storage(self) -> None:
        registry = OmeReaderRegistry(readers=[_ReaderAlwaysFalse()])

        with pytest.raises(UnsupportedOmeStorageError):
            registry.get_reader(MediaStorage(root=Path("sample.png")))
