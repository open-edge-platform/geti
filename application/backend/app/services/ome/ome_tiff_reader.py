# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
from math import prod
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import tifffile
import zarr
from defusedxml.ElementTree import fromstring, tostring
from numpy.typing import NDArray

from app.models import MediaStorage, OmeImageInfo, Region
from app.services.base import InvalidImageError

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

_MAX_SEGMENT_BYTES: int = 64 * 1024 * 1024

_OME_PIXEL_DTYPES: dict[str, str] = {
    "bit": "bool",
    "int8": "int8",
    "int16": "int16",
    "int32": "int32",
    "uint8": "uint8",
    "uint16": "uint16",
    "uint32": "uint32",
    "float": "float32",
    "double": "float64",
    "complex": "complex64",
    "double-complex": "complex128",
}


def _sample_coordinates(
    crop: Region, output_size: tuple[int, int] | None
) -> tuple[NDArray[np.intp], NDArray[np.intp]] | None:
    """Build an optional downsampling grid in level-local coordinates."""
    if output_size is None:
        return None
    width, height = output_size
    if not 0 < width <= crop.width or not 0 < height <= crop.height:
        raise ValueError("OME output size must be positive and no larger than the selected region.")
    return (
        np.linspace(crop.x, crop.x + crop.width - 1, width, dtype=np.intp),
        np.linspace(crop.y, crop.y + crop.height - 1, height, dtype=np.intp),
    )


def _parse_pixels(xml: str | None) -> tuple[Element, Element]:
    """Validate OME-XML and locate the first image's pixel metadata."""
    if not xml:
        raise InvalidImageError("The TIFF does not contain OME-XML.")
    root = fromstring(xml)
    if root.tag.rsplit("}", 1)[-1] != "OME":
        raise InvalidImageError("Expected an OME metadata root.")
    image = root.find("{*}Image")
    pixels = image.find("{*}Pixels") if image is not None else None
    if pixels is None:
        raise InvalidImageError("OME metadata does not contain image pixels.")
    return root, pixels


def _resolve_storage_path(path: Path, storage: MediaStorage) -> Path:
    """Resolve symlinks and reject files outside the authorized media payload."""
    resolved = path.resolve()
    root = storage.root.resolve()
    if not (resolved.is_relative_to(root) if storage.is_directory else resolved == root):
        raise InvalidImageError("OME-TIFF file is outside media storage.")
    return resolved


def _validate_companion_paths(path: Path, root: Element, storage: MediaStorage) -> None:
    """Validate all companion metadata before tifffile discovers any series.

    Directory-backed media may reference files within their resolved storage
    root. Single-file media may reference only themselves. Companion metadata
    is inspected without series discovery, including cyclic references and
    companions without Image/Pixels metadata. UUID self-references do not
    require their recorded filenames to match the current storage path.
    """
    pending = [(path, root)]
    visited = {path}
    while pending:
        current_path, metadata = pending.pop()
        current_uuid = metadata.get("UUID")
        for data in metadata.iter():
            # Match tifffile's suffix-based recognition, not just OME namespaces.
            if not data.tag.endswith("TiffData"):
                continue
            for uuid in data:
                if not uuid.tag.endswith("UUID"):
                    continue
                if current_uuid is not None and uuid.text == current_uuid:
                    continue
                if (filename := uuid.get("FileName")) is None:
                    continue
                companion = _resolve_storage_path(current_path.parent / filename, storage)
                if companion in visited:
                    continue
                visited.add(companion)
                with tifffile.TiffFile(companion, _multifile=False) as tiff:
                    xml = tiff.ome_metadata
                if xml:
                    pending.append((companion, fromstring(xml)))


def _parse_info(tiff: tifffile.TiffFile, xml: str | None, pixels: Element) -> OmeImageInfo:
    """Validate and parse series-zero metadata without decoding image pixels."""
    sizes = {axis: int(pixels.attrib[f"Size{axis}"]) for axis in "XYC"}
    sizes.update({axis: int(pixels.get(f"Size{axis}", "1")) for axis in "ZT"})
    pixel_type = pixels.attrib["Type"]
    dtype = _OME_PIXEL_DTYPES.get(pixel_type)
    if dtype is None:
        raise InvalidImageError(f"Unsupported OME pixel type: {pixel_type!r}.")
    series = tiff.series[0]
    if np.dtype(dtype) != series.dtype.newbyteorder("="):
        raise InvalidImageError(f"OME pixel type {pixel_type!r} does not match TIFF dtype {series.dtype}.")
    actual = dict(zip(series.axes, series.shape))
    for axis, size in sizes.items():
        stored = actual.get(axis, 1)
        if axis == "C":
            stored *= actual.get("S", 1)
        if stored != size:
            raise InvalidImageError(f"OME Size{axis} does not match the TIFF pixels.")
    if not {"X", "Y"}.issubset(actual):
        raise InvalidImageError("TIFF pixels must have X and Y axes.")
    return OmeImageInfo(
        size_x=sizes["X"],
        size_y=sizes["Y"],
        size_c=sizes["C"],
        size_z=sizes["Z"],
        size_t=sizes["T"],
        dimension_order=pixels.attrib["DimensionOrder"],
        pixel_type=pixel_type,
        is_big_tiff=tiff.is_bigtiff,
        raw_metadata=xml,
        channels=_parse_channels(pixels, series.dtype, sizes["C"]),
        pyramid_levels=[
            {
                "level": index,
                "width": level.shape[level.axes.index("X")],
                "height": level.shape[level.axes.index("Y")],
                "scale": [sizes[axis] / level.shape[level.axes.index(axis)] if axis in "XY" else 1 for axis in "XYCZT"],
            }
            for index, level in enumerate(series.levels)
        ],
    )


def _parse_channels(pixels: Element, dtype: np.dtype, size_c: int) -> list[dict[str, object]]:
    """Expand logical channels (including RGB samples) and their declared ranges."""
    minimum, maximum = (0, 1)
    if np.issubdtype(dtype, np.integer):
        limits = np.iinfo(dtype)
        minimum, maximum = int(limits.min), int(limits.max)
        bits = int(pixels.get("SignificantBits", str(limits.bits)))
        if not 0 < bits <= limits.bits:
            raise InvalidImageError("Invalid OME SignificantBits.")
        if minimum == 0:
            maximum = (1 << bits) - 1
        else:
            minimum, maximum = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    channels: list[dict[str, object]] = []
    for channel in pixels.findall("{*}Channel"):
        for _ in range(int(channel.get("SamplesPerPixel", "1"))):
            item: dict[str, object] = {
                "index": len(channels),
                "name": channel.get("Name", f"Channel {len(channels)}"),
                "window": {"min": minimum, "max": maximum, "start": minimum, "end": maximum},
            }
            if "Color" in channel.attrib:
                item["color"] = f"#{(int(channel.attrib['Color']) & 0xFFFFFFFF) >> 8:06x}"
            if "EmissionWavelength" in channel.attrib:
                item["emission_wavelength"] = float(channel.attrib["EmissionWavelength"])
                item["emission_wavelength_unit"] = channel.get("EmissionWavelengthUnit", "nm")
            channels.append(item)
    if channels and len(channels) != size_c:
        raise InvalidImageError("OME channel count does not match SizeC.")
    return channels


class OmeTiffReader:
    """Identify and open single-file or directory-backed OME-TIFF images."""

    def probe(self, storage: MediaStorage) -> bool:
        """Identify OME-TIFF by its contents, not its filename."""
        try:
            path = _resolve_storage_path(storage.effective_path, storage)
            with tifffile.TiffFile(path, _multifile=False) as tiff:
                return bool(tiff.is_ome)
        except (OSError, ValueError, IndexError, InvalidImageError):
            return False

    def open(self, storage: MediaStorage, series: int = 0) -> "OmeTiffImageHandle":
        """Open series zero, translating invalid containers to InvalidImageError.

        Raises:
            ValueError: If a non-default series is requested.
            InvalidImageError: If the file or its OME metadata is invalid.
        """
        if series != 0:
            raise ValueError("Only OME series 0 is supported.")
        tiff = None
        try:
            path = _resolve_storage_path(storage.effective_path, storage)
            tiff = tifffile.TiffFile(path)
            xml = tiff.ome_metadata
            root, pixels = _parse_pixels(xml)
            _validate_companion_paths(path, root, storage)
            if any(f"Size{axis}" not in pixels.attrib for axis in "ZT"):
                # tifffile requires these fields even for singleton dimensions.
                for axis in "ZT":
                    pixels.attrib.setdefault(f"Size{axis}", "1")
                tiff.close()
                tiff = tifffile.TiffFile(path, omexml=tostring(root, encoding="unicode"))
            return OmeTiffImageHandle(tiff, _parse_info(tiff, xml, pixels))
        except Exception as error:
            if tiff is not None:
                tiff.close()
            raise InvalidImageError(f"Cannot open OME-TIFF: {error}") from error


class OmeTiffImageHandle:
    """Own TIFF resources and decode only the requested planes and spatial segments.

    Handles are scoped to one caller and are not intended for concurrent reads.
    """

    def __init__(self, tiff: tifffile.TiffFile, info: OmeImageInfo) -> None:
        self._tiff = tiff
        self.info = info
        self._closed = False

    def read_region(
        self,
        *,
        level: int = 0,
        region: Region | None = None,
        z: int = 0,
        t: int = 0,
        channels: Sequence[int] | None = None,
        output_size: tuple[int, int] | None = None,
    ) -> np.ndarray:
        """Return a level-local region as (C, H, W) in the requested channel order.

        ``output_size=(width, height)`` downsamples on an evenly spaced nearest-pixel
        grid while decoding each intersecting strip or tile at most once.

        Raises:
            ValueError: If the handle is closed or a selection is out of bounds.
            InvalidImageError: If the requested TIFF pixels cannot be decoded.
        """
        if self._closed:
            raise ValueError("The OME-TIFF handle is closed.")
        levels = self._tiff.series[0].levels
        if not 0 <= level < len(levels) or not 0 <= z < self.info.size_z or not 0 <= t < self.info.size_t:
            raise ValueError("OME level, z or t selection is out of range.")
        selected = list(range(self.info.size_c)) if channels is None else list(channels)
        if any(not 0 <= channel < self.info.size_c for channel in selected):
            raise ValueError("OME channel selection is out of range.")
        image = levels[level]
        sizes = dict(zip(image.axes, image.shape))
        crop = region or Region(x=0, y=0, width=sizes["X"], height=sizes["Y"])
        if crop.x + crop.width > sizes["X"] or crop.y + crop.height > sizes["Y"]:
            raise ValueError("OME region extends beyond the selected pyramid level.")
        sample_coordinates = _sample_coordinates(crop, output_size)
        width, height = output_size or (crop.width, crop.height)
        result = np.zeros((len(selected), height, width), dtype=image.dtype)
        if not selected:
            return result
        try:
            pages: dict[tifffile.TiffPage | tifffile.TiffFrame, list[tuple[int, int]]] = {}
            for index, channel in enumerate(selected):
                coordinates = {"Z": z, "T": t, "C": channel // sizes.get("S", 1), "S": channel % sizes.get("S", 1)}
                page = self._get_page(image, coordinates)
                pages.setdefault(page, []).append((index, coordinates["S"]))
            for page, selections in pages.items():
                self._read_page(page, crop, z, selections, result, sample_coordinates)
        except Exception as error:
            raise InvalidImageError(f"Cannot read OME-TIFF pixels: {error}") from error
        return result

    @staticmethod
    def _get_page(
        image: tifffile.TiffPageSeries, coordinates: dict[str, int]
    ) -> tifffile.TiffPage | tifffile.TiffFrame:
        """Locate the page for axis coordinates, excluding axes stored within each page."""
        first_page = image.keyframe
        if first_page is None:
            raise InvalidImageError("OME series has no TIFF keyframe.")
        outer_axes = image.axes[: len(image.axes) - len(first_page.axes)]
        page_index = 0
        for axis, size in zip(outer_axes, image.shape):
            page_index = page_index * size + coordinates.get(axis, 0)
        page = image.pages[page_index]
        if page is None:
            raise InvalidImageError("OME plane references a missing TIFF page.")
        return page

    @staticmethod
    def _read_page(
        page: tifffile.TiffPage | tifffile.TiffFrame,
        crop: Region,
        z: int,
        selections: Sequence[tuple[int, int]],
        output: np.ndarray,
        coordinates: tuple[NDArray[np.intp], NDArray[np.intp]] | None = None,
    ) -> None:
        """Read a bounded page selection through tifffile's Zarr adapter.

        Zarr handles strip/tile selection and sampling, including repeated samples.
        Reject pages with oversized encoded or decoded chunks before pixel access.
        """
        keyframe = page.keyframe
        if keyframe is None or keyframe.dtype is None:
            raise InvalidImageError("OME plane has no TIFF keyframe or pixel dtype.")
        decoded_bytes = prod(keyframe.chunks) * keyframe.dtype.itemsize
        if max(decoded_bytes, max(page.databytecounts, default=0)) > _MAX_SEGMENT_BYTES:
            raise InvalidImageError(f"OME-TIFF segment exceeds the {_MAX_SEGMENT_BYTES}-byte read/decode limit.")
        indices: dict[str, int | slice | NDArray[np.intp]] = {
            "X": slice(crop.x, crop.x + crop.width) if coordinates is None else coordinates[0],
            "Y": slice(crop.y, crop.y + crop.height) if coordinates is None else coordinates[1],
            "Z": z,
            "S": np.asarray([sample for _, sample in selections], dtype=np.intp),
        }
        selection = tuple(indices.get(axis, 0) for axis in keyframe.axes)
        with page.aszarr(maxworkers=1) as store:
            array = zarr.open_array(store, mode="r")
            pixels = np.asarray(array.get_orthogonal_selection(selection))
        axes = [axis for axis in keyframe.axes if axis in "SYX"]
        if "S" not in axes:
            pixels = pixels[np.newaxis]
            axes.insert(0, "S")
        pixels = pixels.transpose(*(axes.index(axis) for axis in "SYX"))
        output[[index for index, _ in selections]] = pixels

    def close(self) -> None:
        """Release all TIFF files, including any opened companion files."""
        if not self._closed:
            self._tiff.close()
            self._closed = True

    def __enter__(self) -> "OmeTiffImageHandle":
        if self._closed:
            raise ValueError("The OME-TIFF handle is closed.")
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
