# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from PIL import Image

from getidata import exif_utils


def test_exif_orientation_check_is_cached_per_file_version(tmp_path, monkeypatch):
    path = tmp_path / "a.jpg"  # JPEG: no PNG chunk scan, PIL is the source of truth
    Image.new("RGB", (4, 4)).save(path)
    exif_utils._has_nontrivial_exif_orientation.cache_clear()

    opened = []
    real_open = Image.open
    monkeypatch.setattr(Image, "open", lambda p, *a, **k: (opened.append(p), real_open(p, *a, **k))[1])

    assert exif_utils.has_nontrivial_exif_orientation(str(path)) is False
    assert exif_utils.has_nontrivial_exif_orientation(str(path)) is False
    assert len(opened) == 1


def test_exif_orientation_check_missing_file_is_false(tmp_path):
    assert exif_utils.has_nontrivial_exif_orientation(str(tmp_path / "missing.png")) is False


def _png_with_orientation(path, orientation):
    exif = Image.Exif()
    exif[exif_utils.EXIF_ORIENTATION_TAG] = orientation
    Image.new("RGB", (4, 4)).save(path, exif=exif)


def test_png_without_exif_is_detected_without_pil(tmp_path, monkeypatch):
    path = tmp_path / "plain.png"
    Image.new("RGB", (4, 4)).save(path)
    exif_utils._has_nontrivial_exif_orientation.cache_clear()
    monkeypatch.setattr(Image, "open", lambda *a, **k: (_ for _ in ()).throw(AssertionError("decoded via PIL")))

    assert exif_utils.has_nontrivial_exif_orientation(str(path)) is False


def test_png_exif_orientation_still_detected(tmp_path):
    exif_utils._has_nontrivial_exif_orientation.cache_clear()
    rotated, upright = tmp_path / "rot.png", tmp_path / "up.png"
    _png_with_orientation(rotated, 6)
    _png_with_orientation(upright, 1)

    assert exif_utils.has_nontrivial_exif_orientation(str(rotated)) is True
    assert exif_utils.has_nontrivial_exif_orientation(str(upright)) is False


def test_corrupt_png_falls_back_to_pil(tmp_path):
    exif_utils._has_nontrivial_exif_orientation.cache_clear()
    path = tmp_path / "bad.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00")

    assert exif_utils.has_nontrivial_exif_orientation(str(path)) is False
