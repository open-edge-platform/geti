# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Reading of OME images: storage location, reader protocol and the OME-TIFF implementation."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from xml.etree.ElementTree import Element

import numpy as np
import tifffile
from defusedxml import ElementTree

from app.models.ome import OmeChannel, OmeContainerFormat, OmeImageInfo, OmePyramidLevel

PLANE_AXES = frozenset("YXS")
MICROMETER_UNITS = frozenset({"µm", "um", "micrometer"})


class InvalidOmeImageError(Exception):
    """Raised when a file is not a valid or supported OME image."""


@dataclass(frozen=True)
class MediaStorage:
    """
    Where the bytes of a media live: a single file, or a directory of files with an entrypoint.

    Attributes:
        root: The media file, or the directory containing the media files.
        entrypoint: File to open within `root` for directory-based media; None for single-file media.
    """

    root: Path
    entrypoint: Path | None = None

    @property
    def is_directory(self) -> bool:
        return self.entrypoint is not None

    @property
    def path(self) -> Path:
        """Path of the file to open to read the media."""
        return self.root / self.entrypoint if self.entrypoint is not None else self.root


@dataclass(frozen=True)
class ParsedOmeImage:
    """Result of parsing an OME image: its structure and the verbatim metadata it was derived from."""

    info: OmeImageInfo
    raw_metadata: str


class OmeReader(Protocol):
    """Reads OME images; one implementation per container format (OME-TIFF now, OME-Zarr later)."""

    def parse(self, storage: MediaStorage) -> ParsedOmeImage:
        """Parse the structure of the image. The returned info has an empty channel mapping."""
        ...

    def read_plane(self, storage: MediaStorage, z: int, t: int, channels: Sequence[int], level: int = 0) -> np.ndarray:
        """Read the given channels of a (z, t) plane at a pyramid level, as a (len(channels), H, W) array."""
        ...


def _local_name(element: Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _children(element: Element, name: str) -> list[Element]:
    return [child for child in element if _local_name(child) == name]


def _ome_color_to_hex(value: str | None) -> str | None:
    """Convert an OME color (signed 32-bit RGBA integer) to '#rrggbb'."""
    if value is None:
        return None
    try:
        rgba = int(value) & 0xFFFFFFFF
    except ValueError:
        return None
    return f"#{(rgba >> 24) & 0xFF:02x}{(rgba >> 16) & 0xFF:02x}{(rgba >> 8) & 0xFF:02x}"


def _parse_wavelength_nm(channel: Element) -> float | None:
    value = channel.get("EmissionWavelength")
    if value is None:
        return None
    try:
        wavelength = float(value)
    except ValueError:
        return None
    unit = channel.get("EmissionWavelengthUnit", "nm")
    return wavelength * 1000 if unit in MICROMETER_UNITS else wavelength


def _parse_channels(pixels: Element, size_c: int) -> list[OmeChannel]:
    """Parse channel descriptions, expanding interleaved (multi-sample) channels into one entry per sample."""
    channels: list[OmeChannel] = []
    for element in _children(pixels, "Channel"):
        samples = int(element.get("SamplesPerPixel", "1"))
        name = element.get("Name")
        for sample in range(samples):
            channels.append(
                OmeChannel(
                    index=len(channels),
                    name=f"{name or 'Channel'} {sample}" if samples > 1 else name,
                    color=_ome_color_to_hex(element.get("Color")) if samples == 1 else None,
                    emission_wavelength=_parse_wavelength_nm(element) if samples == 1 else None,
                )
            )
    channels = channels[:size_c]
    channels.extend(OmeChannel(index=index) for index in range(len(channels), size_c))
    return channels


class OmeTiffReader:
    """`OmeReader` for single-file OME-TIFF images (classic or BigTIFF, optionally pyramidal). Uses series 0."""

    series_index = 0

    def parse(self, storage: MediaStorage) -> ParsedOmeImage:
        try:
            with tifffile.TiffFile(storage.path) as tif:
                if not tif.is_ome or not tif.ome_metadata:
                    raise InvalidOmeImageError("The file is not an OME-TIFF image.")
                raw_metadata = tif.ome_metadata
                series = tif.series[self.series_index]
                pixels = self._parse_pixels(raw_metadata)
                info = self._build_info(pixels, series, is_big_tiff=tif.is_bigtiff)
        except InvalidOmeImageError:
            raise
        except Exception as error:
            raise InvalidOmeImageError(f"Unreadable OME-TIFF image: {error}") from error
        return ParsedOmeImage(info=info, raw_metadata=raw_metadata)

    def read_plane(self, storage: MediaStorage, z: int, t: int, channels: Sequence[int], level: int = 0) -> np.ndarray:
        with tifffile.TiffFile(storage.path) as tif:
            series = tif.series[self.series_index]
            if not 0 <= level < len(series.levels):
                raise ValueError(f"Pyramid level {level} does not exist.")
            level_series = series.levels[level]
            axes: str = series.axes
            shape: tuple[int, ...] = level_series.shape
            page_axes = [(axis, size) for axis, size in zip(axes, shape) if axis not in PLANE_AXES]
            samples = shape[axes.index("S")] if "S" in axes else 1
            page_cache: dict[int, np.ndarray] = {}
            result = []
            for channel in channels:
                coordinates = {"Z": z, "T": t, "C": channel // samples}
                page_coordinates = [coordinates.get(axis, 0) for axis, _ in page_axes]
                if any(not 0 <= value < size for value, (_, size) in zip(page_coordinates, page_axes)):
                    raise ValueError(f"Plane (z={z}, t={t}, c={channel}) is out of range.")
                page_index = (
                    int(np.ravel_multi_index(page_coordinates, [size for _, size in page_axes])) if page_axes else 0
                )
                if page_index not in page_cache:
                    page = level_series.pages[page_index]
                    if page is None:
                        raise InvalidOmeImageError(f"Plane (z={z}, t={t}, c={channel}) is missing from the file.")
                    page_cache[page_index] = page.asarray()
                data = page_cache[page_index]
                result.append(data[..., channel % samples] if samples > 1 else data)
        return np.stack(result)

    @staticmethod
    def _parse_pixels(raw_metadata: str) -> Element:
        root = ElementTree.fromstring(raw_metadata)
        images = _children(root, "Image")
        if not images:
            raise InvalidOmeImageError("The OME metadata does not describe any image.")
        pixels = _children(images[OmeTiffReader.series_index], "Pixels")
        if not pixels:
            raise InvalidOmeImageError("The OME metadata does not describe the image pixels.")
        return pixels[0]

    @staticmethod
    def _build_info(pixels: Element, series: tifffile.TiffPageSeries, is_big_tiff: bool) -> OmeImageInfo:
        def size(name: str, required: bool = False) -> int:
            value = pixels.get(name)
            if value is None:
                if required:
                    raise InvalidOmeImageError(f"The OME metadata does not declare {name}.")
                return 1
            return int(value)

        size_x, size_y = size("SizeX", required=True), size("SizeY", required=True)
        size_c = size("SizeC", required=True)
        if not {"Y", "X"}.issubset(series.axes):
            raise InvalidOmeImageError(f"Unsupported image axes '{series.axes}': X and Y are required.")
        levels = series.levels if series.is_pyramidal else []
        pyramid_levels = []
        for index, level in enumerate(levels):
            width, height = level.shape[series.axes.index("X")], level.shape[series.axes.index("Y")]
            pyramid_levels.append(
                OmePyramidLevel(level=index, width=width, height=height, scale=[size_x / width, size_y / height])
            )
        significant_bits = pixels.get("SignificantBits")
        return OmeImageInfo(
            container_format=OmeContainerFormat.OME_TIFF,
            size_x=size_x,
            size_y=size_y,
            size_z=size("SizeZ"),
            size_c=size_c,
            size_t=size("SizeT"),
            dimension_order=pixels.get("DimensionOrder", "XYCZT"),
            pixel_type=pixels.get("Type", str(series.dtype)),
            significant_bits=int(significant_bits) if significant_bits is not None else None,
            series_index=OmeTiffReader.series_index,
            is_big_tiff=is_big_tiff,
            channels=_parse_channels(pixels, size_c),
            channel_mapping=[],
            pyramid_levels=pyramid_levels,
        )
