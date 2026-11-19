# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import re
import shutil
from pathlib import Path
from unittest.mock import PropertyMock, patch

import numpy as np
import pytest
import tifffile
from defusedxml.common import EntitiesForbidden

from app.models import MediaStorage, Region
from app.services.media_service import InvalidImageError
from app.services.ome import OmeReaderRegistry, OmeTiffReader

ASSETS = Path(__file__).resolve().parents[3] / "assets" / "ome"


@pytest.fixture
def reader():
    return OmeTiffReader()


@pytest.mark.parametrize("name,size_z,size_t", [("xyc", 1, 1), ("xycz", 2, 1), ("xyczt", 2, 2)])
def test_metadata(reader, name, size_z, size_t):
    with reader.open(MediaStorage(root=ASSETS / f"{name}.ome.tiff")) as handle:
        info = handle.info
        assert (info.size_x, info.size_y, info.size_c, info.size_z, info.size_t) == (48, 32, 3, size_z, size_t)
        assert info.pixel_type == "uint16"
        assert info.raw_metadata.startswith("<?xml")
        assert info.channels[0]["window"] == {"min": 0, "max": 65535, "start": 0, "end": 65535}


@pytest.mark.parametrize("name", ["xyczt", "alternate_order", "pyramidal"])
@pytest.mark.parametrize("z,t", [(0, 0), (1, 0), (0, 1), (1, 1)])
@pytest.mark.parametrize("channels", [None, [2, 0], [1], [1, 1], []])
@pytest.mark.parametrize("crop", [None, Region(x=3, y=2, width=17, height=19)])
def test_plane_and_region_selection(reader, name, z, t, channels, crop):
    with reader.open(MediaStorage(root=ASSETS / f"{name}.ome.tiff")) as handle:
        actual = handle.read_region(z=z, t=t, channels=channels, region=crop)
    y, x = np.indices((32, 48))
    selected = range(3) if channels is None else channels
    expected = np.asarray([t * 10000 + z * 1000 + c * 100 + y * 48 + x for c in selected], dtype=np.uint16)
    expected = expected.reshape(len(selected), 32, 48)
    if crop is not None:
        expected = expected[:, crop.y : crop.y + crop.height, crop.x : crop.x + crop.width]
    np.testing.assert_array_equal(actual, expected)
    assert actual.dtype == np.uint16


@pytest.mark.parametrize("level", [0, 1, 2])
@pytest.mark.parametrize("crop", [None, Region(x=2, y=1, width=7, height=5)])
@pytest.mark.parametrize("z,t", [(0, 0), (1, 1)])
def test_pyramid_levels(reader, level, crop, z, t):
    with reader.open(MediaStorage(root=ASSETS / "pyramidal.ome.tiff")) as handle:
        actual = handle.read_region(level=level, region=crop, z=z, t=t, channels=[2, 0])
        assert handle.info.pyramid_levels[level]["scale"] == [2**level, 2**level, 1, 1, 1]
    y, x = np.indices((32, 48))
    expected = np.asarray([t * 10000 + z * 1000 + c * 100 + y * 48 + x for c in (2, 0)], dtype=np.uint16)
    expected = expected[:, :: 2**level, :: 2**level]
    if crop:
        expected = expected[:, crop.y : crop.y + crop.height, crop.x : crop.x + crop.width]
    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("name", ["rgb", "rgb_planar", "bigtiff", "single_channel"])
def test_samples_bigtiff_and_squeezed_channels(reader, name):
    with reader.open(MediaStorage(root=ASSETS / f"{name}.ome.tiff")) as handle:
        actual = handle.read_region()
        assert handle.info.is_big_tiff == (name == "bigtiff")
        assert actual.shape == (1 if name == "single_channel" else 3, 32, 48)
        assert actual[0, 2, 3] == 99
        if actual.shape[0] == 3:
            assert actual[2, 2, 3] == 299


@pytest.mark.parametrize("compression", ["lzw", "jpeg"])
@pytest.mark.parametrize("crop", [None, Region(x=3, y=2, width=17, height=19)])
def test_compressed_planes_and_regions(reader, compression, crop):
    path = ASSETS / f"{compression}.ome.tiff"
    with tifffile.TiffFile(path) as tiff:
        assert all(page.compression == tifffile.COMPRESSION[compression.upper()] for page in tiff.pages)
        expected = tiff.asarray()[[2, 0]]
    if compression == "lzw":
        y, x = np.indices((32, 48))
        np.testing.assert_array_equal(expected, np.asarray([c * 100 + y * 48 + x for c in (2, 0)], dtype=np.uint16))
    if crop is not None:
        expected = expected[:, crop.y : crop.y + crop.height, crop.x : crop.x + crop.width]
    storage = MediaStorage(root=path)
    assert reader.probe(storage)
    with (
        reader.open(storage) as handle,
        patch.object(tifffile.TiffPageSeries, "asarray", side_effect=AssertionError("eager read")),
    ):
        actual = handle.read_region(channels=[2, 0], region=crop)
    np.testing.assert_array_equal(actual, expected)
    assert actual.dtype == expected.dtype


def test_probe_and_default_registry_use_contents(reader, tmp_path):
    renamed = tmp_path / "image.dat"
    shutil.copyfile(ASSETS / "xyc.ome.tiff", renamed)
    storage = MediaStorage(root=renamed)
    assert reader.probe(storage)
    assert isinstance(OmeReaderRegistry().get_reader(storage), OmeTiffReader)
    for path in (ASSETS / "not_ome.tiff", tmp_path / "missing.ome.tiff", tmp_path):
        assert not reader.probe(MediaStorage(root=path))
    assert OmeReaderRegistry(readers=[])._readers == []


def test_directory_storage(reader, tmp_path):
    shutil.copyfile(ASSETS / "xyc.ome.tiff", tmp_path / "image.tiff")
    storage = MediaStorage(root=tmp_path, entrypoint=Path("image.tiff"))
    assert reader.probe(storage)
    with reader.open(storage) as handle:
        assert handle.read_region().shape == (3, 32, 48)


@pytest.mark.parametrize("name", ["not_ome.tiff", "malformed.ome.tiff"])
def test_reject_invalid_ome(reader, name):
    with pytest.raises(InvalidImageError):
        reader.open(MediaStorage(root=ASSETS / name))


@pytest.mark.parametrize(
    "entity",
    ['<!ENTITY channel "expanded">', '<!ENTITY channel SYSTEM "file:///nonexistent-ome-entity">'],
)
def test_reject_xml_entities(reader, tmp_path, entity):
    path = tmp_path / "entities.ome.tiff"
    shutil.copyfile(ASSETS / "xyc.ome.tiff", path)
    with tifffile.TiffFile(path) as tiff:
        xml = tiff.ome_metadata
    assert xml is not None
    xml = xml.replace("<OME ", f"<!DOCTYPE OME [{entity}]><OME ", 1)
    xml = xml.replace("<Image ", '<Image Name="&channel;" ', 1)
    tifffile.tiffcomment(path, xml)
    with pytest.raises(InvalidImageError) as error:
        reader.open(MediaStorage(root=path))
    assert isinstance(error.value.__cause__, EntitiesForbidden)


@pytest.mark.parametrize("attribute", ["SizeX", "SizeY", "SizeC", "DimensionOrder", "Type"])
def test_required_metadata(reader, tmp_path, attribute):
    path = tmp_path / "invalid.ome.tiff"
    shutil.copyfile(ASSETS / "xyc.ome.tiff", path)
    with tifffile.TiffFile(path) as tiff:
        xml = tiff.ome_metadata
    assert xml is not None
    tifffile.tiffcomment(path, re.sub(rf' {attribute}="[^"]*"', "", xml))
    with pytest.raises(InvalidImageError):
        reader.open(MediaStorage(root=path))


@pytest.mark.parametrize(
    "selection",
    [
        {"z": -1},
        {"z": 2},
        {"t": -1},
        {"t": 2},
        {"level": -1},
        {"level": 3},
        {"channels": [-1]},
        {"channels": [3]},
        {"region": Region(x=47, y=0, width=2, height=1)},
        {"region": Region(x=0, y=31, width=1, height=2)},
    ],
)
def test_selection_bounds(reader, selection):
    with reader.open(MediaStorage(root=ASSETS / "pyramidal.ome.tiff")) as handle, pytest.raises(ValueError):
        handle.read_region(**selection)


def test_nonzero_series_rejected(reader):
    with pytest.raises(ValueError, match="series 0"):
        reader.open(MediaStorage(root=ASSETS / "xyc.ome.tiff"), series=1)


def test_unknown_axes_use_index_zero(reader):
    with reader.open(MediaStorage(root=ASSETS / "xycz.ome.tiff")) as handle:
        with patch.object(tifffile.TiffPageSeries, "axes", new_callable=PropertyMock, return_value="QCYX"):
            actual = handle.read_region(channels=[2])
        assert actual[0, 2, 3] == 299


def test_lazy_crop_does_not_decode_whole_series(reader):
    with reader.open(MediaStorage(root=ASSETS / "pyramidal.ome.tiff")) as handle:
        with (
            patch.object(tifffile.TiffPageSeries, "asarray", side_effect=AssertionError("eager read")),
            patch.object(tifffile.FileHandle, "read", autospec=True, side_effect=tifffile.FileHandle.read) as read,
        ):
            actual = handle.read_region(channels=[0], region=Region(x=1, y=2, width=3, height=4))
        assert actual[0, 0, 0] == 97
        assert read.call_count == 1  # one intersecting tile, not the other five tiles or planes


@pytest.mark.parametrize("planar", [False, True])
@pytest.mark.parametrize("tiled", [False, True])
@pytest.mark.parametrize("channels", [None, [2, 0], [1, 1], [2, 0, 2, 1], []])
@pytest.mark.parametrize("crop", [None, Region(x=3, y=2, width=17, height=19)])
def test_rgb_segments_are_decoded_once(reader, tmp_path, planar, tiled, channels, crop):
    path = tmp_path / "rgb.ome.tiff"
    c, y, x = np.indices((3, 32, 48))
    data = (c * 100 + y * 48 + x).astype(np.uint16)
    tifffile.imwrite(
        path,
        data if planar else data.transpose(1, 2, 0),
        ome=True,
        photometric="rgb",
        planarconfig="separate" if planar else "contig",
        metadata={"axes": "SYX" if planar else "YXS"},
        compression="lzw",
        tile=(16, 16) if tiled else None,
        rowsperstrip=None if tiled else 8,
    )
    selected = list(range(3)) if channels is None else channels
    expected = data[selected]
    if crop is not None:
        expected = expected[:, crop.y : crop.y + crop.height, crop.x : crop.x + crop.width]
    segments_per_sample = (6 if crop is None else 4) if tiled else (4 if crop is None else 3)
    expected_decodes = segments_per_sample * (len(set(selected)) if planar else bool(selected))
    with reader.open(MediaStorage(root=path)) as handle:
        keyframe = handle._tiff.series[0].keyframe
        with (
            patch.object(keyframe, "decode", wraps=keyframe.decode) as decode,
            patch.object(tifffile.FileHandle, "read", autospec=True, side_effect=tifffile.FileHandle.read) as read,
            patch.object(tifffile.TiffPageSeries, "asarray", side_effect=AssertionError("eager read")),
        ):
            actual = handle.read_region(channels=channels, region=crop)
        assert read.call_count == expected_decodes
        assert sum(call.args[0] is not None for call in decode.call_args_list) == expected_decodes
    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("z,t", [(0, 0), (1, 0), (0, 1), (1, 1)])
def test_rgb_selections_are_grouped_across_pages(reader, tmp_path, z, t):
    path = tmp_path / "multichannel_rgb.ome.tiff"
    data = np.arange(2 * 2 * 6 * 32 * 48, dtype=np.uint16).reshape(2, 2, 6, 32, 48)
    tifffile.imwrite(
        path,
        data.reshape(2, 2, 2, 3, 32, 48).transpose(0, 1, 2, 4, 5, 3),
        ome=True,
        photometric="rgb",
        metadata={"axes": "TZCYXS"},
        compression="lzw",
        tile=(16, 16),
    )
    channels = [5, 0, 4, 5, 2]
    with reader.open(MediaStorage(root=path)) as handle:
        with patch.object(tifffile.FileHandle, "read", autospec=True, side_effect=tifffile.FileHandle.read) as read:
            actual = handle.read_region(z=z, t=t, channels=channels, region=Region(x=1, y=2, width=3, height=4))
        assert read.call_count == 2  # one intersecting tile from each page
    np.testing.assert_array_equal(actual, data[t, z, channels, 2:6, 1:4])


@pytest.mark.parametrize("fail", [False, True])
def test_context_manager_cleanup(reader, fail):
    handle = reader.open(MediaStorage(root=ASSETS / "xyc.ome.tiff"))
    try:
        with handle:
            if fail:
                raise RuntimeError("caller failed")
    except RuntimeError:
        assert fail
    assert handle._tiff.filehandle.closed
    handle.close()  # idempotent
    with pytest.raises(ValueError, match="closed"):
        handle.read_region()


def test_failed_open_closes_tiff(reader):
    original_close = tifffile.TiffFile.close
    with (
        patch("app.services.ome.ome_tiff_reader._parse_info", side_effect=ValueError("bad metadata")),
        patch.object(tifffile.TiffFile, "close", autospec=True, side_effect=original_close) as close,
    ):
        with pytest.raises(InvalidImageError):
            reader.open(MediaStorage(root=ASSETS / "xyc.ome.tiff"))
        close.assert_called_once()


def test_pixel_errors_are_translated(reader):
    with (
        reader.open(MediaStorage(root=ASSETS / "xyc.ome.tiff")) as handle,
        patch.object(handle, "_read_page", side_effect=ValueError("broken strip")),
        pytest.raises(InvalidImageError, match="broken strip"),
    ):
        handle.read_region()


def test_omitted_z_t_default_to_one(reader, tmp_path):
    path = tmp_path / "singleton.ome.tiff"
    shutil.copyfile(ASSETS / "xyc.ome.tiff", path)
    with tifffile.TiffFile(path) as tiff:
        xml = tiff.ome_metadata
    assert xml is not None
    xml = xml.replace(' SizeZ="1"', "").replace(' SizeT="1"', "")
    tifffile.tiffcomment(path, xml)
    with reader.open(MediaStorage(root=path)) as handle:
        assert handle.info.size_z == handle.info.size_t == 1
        assert handle.info.raw_metadata == xml
        assert handle.read_region()[2, 2, 3] == 299


@pytest.mark.parametrize(
    "dtype,pixel_type",
    [
        (np.bool_, "bit"),
        (np.int8, "int8"),
        (np.int16, "int16"),
        (np.int32, "int32"),
        (np.uint8, "uint8"),
        (np.uint16, "uint16"),
        (np.uint32, "uint32"),
        (np.float32, "float"),
        (np.float64, "double"),
        (np.complex64, "complex"),
        (np.complex128, "double-complex"),
    ],
)
@pytest.mark.parametrize("byteorder", ["<", ">"])
def test_pixel_types_and_channel_metadata(reader, tmp_path, dtype, pixel_type, byteorder):
    path = tmp_path / "typed.ome.tiff"
    data = np.arange(60).reshape(3, 4, 5).astype(dtype)
    tifffile.imwrite(
        path,
        data,
        ome=True,
        byteorder=byteorder,
        photometric="minisblack",
        metadata={
            "axes": "CYX",
            "Channel": {
                "Name": ["DAPI", "GFP", "Cy5"],
                "Color": [65535, 16711935, -16776961],
                "EmissionWavelength": [461, 509, 670],
            },
        },
    )
    with reader.open(MediaStorage(root=path)) as handle:
        np.testing.assert_array_equal(handle.read_region(), data)
        assert handle.read_region().dtype == dtype
        assert handle.info.pixel_type == pixel_type
        assert handle.info.channels[0]["color"] == "#0000ff"
        assert handle.info.channels[2]["color"] == "#ff0000"
        assert handle.info.channels[0]["name"] == "DAPI"
        assert handle.info.channels[0]["emission_wavelength"] == 461


@pytest.mark.parametrize(
    "dtype,pixel_type,declared_type",
    [
        (np.uint8, "uint8", "uint16"),
        (np.uint16, "uint16", "uint8"),
        (np.uint16, "uint16", "int16"),
        (np.int32, "int32", "float"),
        (np.float32, "float", "double"),
        (np.float64, "double", "float"),
        (np.complex64, "complex", "double-complex"),
        (np.bool_, "bit", "uint8"),
    ],
)
def test_reject_mismatched_pixel_type(reader, tmp_path, dtype, pixel_type, declared_type):
    path = tmp_path / "mismatched.ome.tiff"
    tifffile.imwrite(path, np.zeros((4, 5), dtype=dtype), ome=True, metadata={"axes": "YX"})
    _replace_ome_metadata(path, f'Type="{pixel_type}"', f'Type="{declared_type}"')
    with pytest.raises(InvalidImageError, match="does not match TIFF dtype"):
        reader.open(MediaStorage(root=path))


@pytest.mark.parametrize("pixel_type", ["invalid", "uint64", "float32"])
def test_reject_unsupported_pixel_type(reader, tmp_path, pixel_type):
    path = tmp_path / "unsupported.ome.tiff"
    shutil.copyfile(ASSETS / "xyc.ome.tiff", path)
    _replace_ome_metadata(path, 'Type="uint16"', f'Type="{pixel_type}"')
    with pytest.raises(InvalidImageError, match="Unsupported OME pixel type"):
        reader.open(MediaStorage(root=path))


def test_only_first_series_is_read(reader, tmp_path):
    path = tmp_path / "multiple.ome.tiff"
    with tifffile.TiffWriter(path, ome=True) as writer:
        writer.write(np.zeros((2, 4, 5), dtype=np.uint8), photometric="minisblack", metadata={"axes": "CYX"})
        writer.write(np.ones((3, 8, 9), dtype=np.uint16), photometric="minisblack", metadata={"axes": "CYX"})
    with reader.open(MediaStorage(root=path)) as handle:
        assert handle.info.series_index == 0
        assert handle.read_region().shape == (2, 4, 5)
        assert not handle.read_region().any()


def _replace_ome_metadata(path: Path, old: str, new: str) -> None:
    with tifffile.TiffFile(path) as tiff:
        xml = tiff.ome_metadata
    assert xml is not None
    assert old in xml
    tifffile.tiffcomment(path, xml.replace(old, new))


def test_companion_files_are_reopened_and_closed(reader, companion_storage):
    with reader.open(companion_storage) as handle:
        assert handle.read_region(channels=[1, 0])[:, 0, 0].tolist() == [1, 0]
        files = [tiff.filehandle for tiff in handle._tiff._files.values()]
        assert len(files) == 2
    assert all(file.closed for file in files)


@pytest.mark.parametrize("companion_storage", [8], indirect=True)
def test_companion_filehandles_do_not_accumulate(reader, companion_storage):
    with reader.open(companion_storage) as handle:
        primary = handle._tiff.filehandle
        files = [tiff.filehandle for tiff in handle._tiff._files.values()]
        open_counts = []
        original_open = tifffile.FileHandle.open

        def track_open(filehandle):
            original_open(filehandle)
            open_counts.append(sum(not file.closed for file in files))

        selections = [list(range(8)), list(reversed(range(8))), [3], [6], [3, 3]]
        with patch.object(tifffile.FileHandle, "open", autospec=True, side_effect=track_open):
            for channels in selections:
                actual = handle.read_region(channels=channels, region=Region(x=1, y=1, width=1, height=1))
                assert actual[:, 0, 0].tolist() == channels
                assert [file for file in files if not file.closed] == [primary]
        assert max(open_counts) == 2  # the primary TIFF and at most one reopened companion


def test_preopened_companion_remains_open(reader, companion_storage):
    with reader.open(companion_storage) as handle:
        companion = handle._tiff.series[0].pages[1].parent.filehandle
        companion.open()
        assert handle.read_region(channels=[1])[0, 0, 0] == 1
        assert not companion.closed
        assert not handle._tiff.filehandle.closed
    assert companion.closed


@pytest.mark.parametrize("initially_open", [False, True])
@pytest.mark.parametrize("operation", ["seek", "read", "decode"])
def test_companion_filehandle_ownership_after_failure(reader, companion_storage, initially_open, operation):
    with reader.open(companion_storage) as handle:
        page = handle._tiff.series[0].pages[1]
        companion = page.parent.filehandle
        if initially_open:
            companion.open()
        target = page.keyframe if operation == "decode" else tifffile.FileHandle
        with (
            patch.object(target, operation, side_effect=ValueError("broken segment")),
            pytest.raises(InvalidImageError, match="broken segment"),
        ):
            handle.read_region(channels=[1], region=Region(x=1, y=1, width=1, height=1))
        assert companion.closed is not initially_open
        assert not handle._tiff.filehandle.closed
        assert handle.read_region(channels=[1])[0, 0, 0] == 1
        assert companion.closed is not initially_open


@pytest.mark.parametrize("kind", ["relative", "absolute", "symlink", "symlink_directory"])
@pytest.mark.parametrize("omit_z_t", [False, True])
def test_companion_paths_cannot_escape_storage(reader, companion_storage, tmp_path, kind, omit_z_t):
    root = companion_storage.root
    outside = tmp_path / "outside.ome.tiff"
    shutil.copyfile(root / "part1.ome.tiff", outside)
    if kind == "relative":
        filename = "../outside.ome.tiff"
    elif kind == "absolute":
        filename = str(outside)
    elif kind == "symlink":
        (root / "link.ome.tiff").symlink_to(outside)
        filename = "link.ome.tiff"
    else:
        (root / "linked").symlink_to(tmp_path, target_is_directory=True)
        filename = "linked/outside.ome.tiff"
    path = companion_storage.effective_path
    _replace_ome_metadata(path, 'FileName="part1.ome.tiff"', f'FileName="{filename}"')
    if omit_z_t:
        _replace_ome_metadata(path, ' SizeZ="1" SizeT="1"', "")
    with (
        patch("app.services.ome.ome_tiff_reader.tifffile.TiffFile", wraps=tifffile.TiffFile) as open_tiff,
        patch("app.services.ome.ome_tiff_reader._parse_info", side_effect=AssertionError("series discovery")),
        pytest.raises(InvalidImageError, match="outside media storage"),
    ):
        reader.open(companion_storage)
    open_tiff.assert_called_once_with(path.resolve())


def test_single_file_storage_rejects_sibling_companions(reader, companion_storage):
    with pytest.raises(InvalidImageError, match="outside media storage"):
        reader.open(MediaStorage(root=companion_storage.effective_path))


@pytest.mark.parametrize("renamed", [False, True])
def test_single_file_storage_allows_self_references(reader, companion_storage, renamed):
    path = companion_storage.effective_path
    _replace_ome_metadata(path, "part1.ome.tiff", "part0.ome.tiff")
    _replace_ome_metadata(path, "000000000002", "000000000001")
    if renamed:
        path = path.rename(path.with_name("renamed.ome.tiff"))
    with reader.open(MediaStorage(root=path)) as handle:
        actual = handle.read_region()
        assert actual.shape == (2, 4, 5)
        assert not actual.any()


@pytest.mark.parametrize("absolute", [False, True])
def test_companion_paths_within_storage_are_allowed(reader, companion_storage, absolute):
    root = companion_storage.root
    (root / "nested").mkdir()
    filename = str(root / "part1.ome.tiff") if absolute else "nested/../part1.ome.tiff"
    _replace_ome_metadata(companion_storage.effective_path, 'FileName="part1.ome.tiff"', f'FileName="{filename}"')
    with reader.open(companion_storage) as handle:
        assert handle.read_region(channels=[1, 0])[:, 0, 0].tolist() == [1, 0]


def test_companions_in_subdirectories_are_allowed(reader, companion_storage):
    root = companion_storage.root
    (root / "nested").mkdir()
    companion = root / "nested" / "part1.ome.tiff"
    (root / "part1.ome.tiff").rename(companion)
    _replace_ome_metadata(companion, "part0.ome.tiff", "../part0.ome.tiff")
    _replace_ome_metadata(companion_storage.effective_path, "part1.ome.tiff", "nested/part1.ome.tiff")
    with reader.open(companion_storage) as handle:
        assert handle.read_region(channels=[1, 0])[:, 0, 0].tolist() == [1, 0]


def test_in_root_companion_symlinks_are_allowed(reader, companion_storage):
    (companion_storage.root / "link.ome.tiff").symlink_to(companion_storage.root / "part1.ome.tiff")
    _replace_ome_metadata(companion_storage.effective_path, "part1.ome.tiff", "link.ome.tiff")
    with reader.open(companion_storage) as handle:
        assert handle.read_region(channels=[1, 0])[:, 0, 0].tolist() == [1, 0]


def test_nested_companion_paths_cannot_escape_storage(reader, companion_storage):
    path = companion_storage.root / "part1.ome.tiff"
    _replace_ome_metadata(path, "part1.ome.tiff", "../outside.ome.tiff")
    _replace_ome_metadata(path, ">urn:uuid:00000000-0000-0000-0000-000000000002</UUID>", ">urn:uuid:external</UUID>")
    with pytest.raises(InvalidImageError, match="outside media storage"):
        reader.open(companion_storage)


def test_missing_uuids_do_not_bypass_companion_path_validation(reader, companion_storage):
    path = companion_storage.effective_path
    _replace_ome_metadata(path, ' UUID="urn:uuid:00000000-0000-0000-0000-000000000001"', "")
    _replace_ome_metadata(
        path,
        '<UUID FileName="part1.ome.tiff">urn:uuid:00000000-0000-0000-0000-000000000002</UUID>',
        '<UUID FileName="../outside.ome.tiff"/>',
    )
    with pytest.raises(InvalidImageError, match="outside media storage"):
        reader.open(companion_storage)


@pytest.mark.parametrize("tag", ["TiffData", "OtherTiffData"])
def test_companion_paths_in_other_images_are_validated(reader, companion_storage, tag):
    reference = (
        f'<Image ID="Image:1"><Pixels><{tag}><OtherUUID FileName="../outside.ome.tiff">'
        f"urn:uuid:external</OtherUUID></{tag}></Pixels></Image>"
    )
    _replace_ome_metadata(companion_storage.effective_path, "</OME>", f"{reference}</OME>")
    with pytest.raises(InvalidImageError, match="outside media storage"):
        reader.open(companion_storage)


def test_companion_metadata_can_be_binary_only(reader, companion_storage):
    xml = '<OME xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06"><BinaryOnly/></OME>'
    tifffile.tiffcomment(companion_storage.root / "part1.ome.tiff", xml)
    with reader.open(companion_storage) as handle:
        assert handle.read_region(channels=[1, 0])[:, 0, 0].tolist() == [1, 0]


def test_directory_entrypoint_symlink_cannot_escape_storage(reader, companion_storage, tmp_path):
    outside = tmp_path / "outside.ome.tiff"
    shutil.copyfile(ASSETS / "xyc.ome.tiff", outside)
    (companion_storage.root / "link.ome.tiff").symlink_to(outside)
    storage = MediaStorage(root=companion_storage.root, entrypoint=Path("link.ome.tiff"))
    assert not reader.probe(storage)
    with pytest.raises(InvalidImageError, match="outside media storage"):
        reader.open(storage)


@pytest.mark.parametrize("dtype,minimum,maximum", [(np.uint16, 0, 4095), (np.int16, -2048, 2047)])
def test_significant_bits_define_channel_window(reader, tmp_path, dtype, minimum, maximum):
    path = tmp_path / "significant.ome.tiff"
    tifffile.imwrite(path, np.zeros((4, 5), dtype=dtype), ome=True, metadata={"axes": "YX", "SignificantBits": 12})
    with reader.open(MediaStorage(root=path)) as handle:
        assert handle.info.channels[0]["window"] == {
            "min": minimum,
            "max": maximum,
            "start": minimum,
            "end": maximum,
        }
