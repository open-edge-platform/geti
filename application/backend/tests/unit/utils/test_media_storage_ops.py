# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from app.models import MediaStorage
from app.utils.media_storage_ops import (
    delete_media_storage,
    discard_media_storage,
    media_storage_size,
    move_media_storage,
)


class TestMediaStorage:
    def test_media_storage_size_for_single_file(self, tmp_path):
        binary_path = tmp_path / "single.bin"
        payload = b"abcdef"
        binary_path.write_bytes(payload)

        size = media_storage_size(MediaStorage(root=binary_path))

        assert size == len(payload)

    def test_media_storage_size_for_directory_layout(self, tmp_path):
        root = tmp_path / "ome-layout"
        root.mkdir()
        (root / "image.ome.tiff").write_bytes(b"1234")
        (root / "companion.ome").write_bytes(b"abc")
        nested = root / "nested"
        nested.mkdir()
        (nested / "extra.bin").write_bytes(b"zz")

        size = media_storage_size(MediaStorage(root=root, entrypoint=Path("image.ome.tiff")))

        assert size == 4 + 3 + 2

    def test_move_media_storage_for_file(self, tmp_path):
        source = tmp_path / "upload.part"
        source.write_bytes(b"payload")
        target = tmp_path / "dataset" / "media.jpg"

        move_media_storage(MediaStorage(root=source), MediaStorage(root=target))

        assert not source.exists()
        assert target.read_bytes() == b"payload"

    def test_move_media_storage_for_directory(self, tmp_path):
        source_dir = tmp_path / "upload-dir"
        source_dir.mkdir()
        (source_dir / "entry.ome").write_bytes(b"entry")
        (source_dir / "planes.bin").write_bytes(b"planes")
        target_dir = tmp_path / "dataset" / "media-dir"

        source_storage = MediaStorage(root=source_dir, entrypoint=Path("entry.ome"))
        target_storage = MediaStorage(root=target_dir, entrypoint=Path("entry.ome"))

        move_media_storage(source_storage, target_storage)

        assert not source_dir.exists()
        assert (target_dir / "entry.ome").read_bytes() == b"entry"
        assert (target_dir / "planes.bin").read_bytes() == b"planes"

    def test_discard_media_storage_moves_back_to_source(self, tmp_path):
        source = tmp_path / "upload.part"
        source.write_bytes(b"payload")
        target = tmp_path / "dataset" / "media.bin"
        source_storage = MediaStorage(root=source)
        target_storage = MediaStorage(root=target)
        move_media_storage(source_storage, target_storage)

        discard_media_storage(target_storage, source_storage)

        assert source.read_bytes() == b"payload"
        assert not target.exists()

    def test_discard_media_storage_deletes_target_without_source(self, tmp_path):
        target = tmp_path / "dataset" / "media.bin"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"payload")

        discard_media_storage(MediaStorage(root=target), source_storage=None)

        assert not target.exists()

    def test_delete_media_storage_deletes_directory_layout(self, tmp_path):
        root = tmp_path / "ome-layout"
        root.mkdir()
        (root / "entry.ome").write_text("x")
        (root / "pixels.bin").write_text("y")

        delete_media_storage(MediaStorage(root=root, entrypoint=Path("entry.ome")))

        assert not root.exists()
