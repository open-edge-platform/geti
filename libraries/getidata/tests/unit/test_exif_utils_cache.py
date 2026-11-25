from PIL import Image

from getidata import exif_utils


def test_exif_orientation_check_is_cached_per_file_version(tmp_path, monkeypatch):
    path = tmp_path / "a.png"
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
