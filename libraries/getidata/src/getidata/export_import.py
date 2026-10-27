# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Export and import functionality for datasets.

This module provides comprehensive export/import capabilities for getidata datasets,
including support for:
- Parquet format for efficient DataFrame storage
- JSON metadata for schema and categories
- Image export for callable and path-based image fields
- Video support with video metadata serialization
- ZIP archive format for complete dataset packages
- Automatic dtype detection when importing without an explicit ``dtype``
"""

from __future__ import annotations

import json
import logging
import platform
import re
import shutil
import tempfile
from dataclasses import dataclass
from enum import Enum
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import TYPE_CHECKING, Any
from zipfile import ZIP_DEFLATED, ZipFile, is_zipfile

import numpy as np
import polars as pl
from PIL import Image, ImageOps

from getidata.data_formats.base import DataFormat
from getidata.dataset import Dataset, Sample
from getidata.fields.images import ImageCallableField, ImagePathField
from getidata.fields.masks import InstanceMaskCallableField, MaskCallableField
from getidata.fields.videos import MediaPathField, VideoFramePathField
from getidata.format_detection import DATAFRAME_FILE, METADATA_FILE, detect_dataset_format, find_dataset_root
from getidata.schema import Schema

if TYPE_CHECKING:
    from .dataset import DType

log = logging.getLogger(__name__)

# Registry sample classes that can automatically be detected when importing datasets
_sample_registry: set[type[Sample]] = set()


def register_sample(cls: type[Sample]) -> type[Sample]:
    """Register a Sample subclass for automatic dtype detection during import.

    Use this to ensure that custom Sample subclasses defined outside of getidata
    are discoverable by :func:`import_dataset` when ``dtype`` is not provided.
    Can be used as a decorator or called directly.

    Args:
        cls: A Sample subclass to register

    Returns:
        The same class, unmodified (allows use as a decorator)

    Example::

        @register_sample
        class MySample(Sample):
            image: Annotated[np.ndarray, ImageField()]
            label: Annotated[int, ScalarField()]
    """
    # Validate that only proper Sample subclasses (excluding Sample itself)
    # can be registered. This prevents invalid entries that could later cause
    # failures during schema inference.
    if not isinstance(cls, type) or not issubclass(cls, Sample) or cls is Sample:
        raise TypeError(f"register_sample expects a subclass of Sample (excluding Sample itself), got {cls!r}")
    _sample_registry.add(cls)
    return cls


# Constants for export structure
IMAGES_DIR = "images"
VIDEOS_DIR = "videos"
try:
    VERSION = _pkg_version("getidata")
except PackageNotFoundError:
    VERSION = "0.0.0"


class ExportMode(Enum):
    """Export mode for media files (images and videos).

    Attributes:
        SKIP: Don't export media files
        REFERENCE: Keep original absolute paths (not portable, but faster)
        COPY: Copy files to output directory (portable, recommended for sharing)
    """

    SKIP = "skip"
    REFERENCE = "reference"
    COPY = "copy"


# Characters that are illegal in filenames on Windows (and thus unsafe for
# cross-platform datasets).
_WINDOWS_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
# Reserved device names on Windows (case-insensitive, with or without extension)
_WINDOWS_RESERVED_NAMES = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..+)?$", re.IGNORECASE)


def sanitize_filename(name: str, *, cross_platform: bool = True) -> str:
    """Sanitize a filename so it is safe for the current (or all) OS(es).

    When *cross_platform* is ``True`` (the default, used during export) the
    filename is made safe for **all** major operating systems (Windows, macOS,
    Linux).  When ``False``, only the rules of the **current** OS are applied
    (useful during import to fix names that are invalid on the importing
    machine).

    The function replaces illegal characters with underscores, strips trailing
    dots/spaces (Windows limitation), and prefixes reserved Windows device
    names with an underscore.

    Args:
        name: The filename (without directory components) to sanitize.
        cross_platform: If ``True``, apply rules for all OSes. If ``False``,
            only apply rules for the current OS.

    Returns:
        The sanitized filename.
    """
    if not name:
        return name

    current_os = platform.system()  # 'Windows', 'Darwin', 'Linux'

    apply_windows_rules = cross_platform or current_os == "Windows"
    apply_macos_rules = cross_platform or current_os == "Darwin"

    if apply_windows_rules:
        name = _WINDOWS_ILLEGAL_CHARS.sub("_", name)
        name = name.rstrip(". ")
        if _WINDOWS_RESERVED_NAMES.match(name):
            name = f"_{name}"
    else:
        if apply_macos_rules:
            # macOS HFS+ / Finder disallows colons (displayed as '/' in
            # Finder but stored as ':' on disk).
            name = name.replace(":", "_")

        # On Linux and macOS, replace control characters (0x00-0x1f) that
        # cause problems with terminals, shells, and many tools.
        name = re.sub(r"[\x00-\x1f]", "_", name)

    if not name:
        name = "_"

    return name


def _get_image_fields(dataset: Dataset[DType]) -> list[tuple[str, object]]:
    """Extract all image-related fields from the dataset schema.

    Note: MediaPathField is included because it can contain both images and video frames.
    The export logic handles MediaPathField specially by only exporting rows where
    frame_index is None (indicating an image rather than a video frame).
    """
    image_fields = []
    for name, attr_info in dataset.schema.attributes.items():
        if isinstance(
            attr_info.field,
            ImageCallableField | ImagePathField | InstanceMaskCallableField | MaskCallableField | MediaPathField,
        ):
            image_fields.append((name, attr_info.field))
    return image_fields


def _get_video_fields(dataset: Dataset[DType]) -> list[tuple[str, object]]:
    """Extract all video-related fields from the dataset schema."""
    video_fields = []
    for name, attr_info in dataset.schema.attributes.items():
        if isinstance(attr_info.field, (VideoFramePathField, MediaPathField)):
            video_fields.append((name, attr_info.field))
    return video_fields


def _get_field_value(dataset: Dataset[DType], idx: int, field_name: str) -> object:
    """Get the value of a field for a specific row index."""
    if dataset._transforms is None:
        row_df = dataset.df.slice(idx, 1)
    else:
        transforms = dataset._transforms.slice(idx, 1)
        row_df = transforms.apply([field_name])
    return row_df[field_name][0]


def _export_image_path_field(
    value: object,
    field_name: str,
    idx: int,
    output_dir: Path,
) -> str | None:
    """Export an ImagePathField by copying the file from the filesystem.

    The original filename is preserved.  When a name collision occurs
    (e.g. two source images from different directories share the same
    filename) a numeric suffix is appended to disambiguate.
    """
    try:
        source_path = Path(str(value))
        if not source_path.exists():
            log.warning("Image file not found: %s", value)
            return None

        # Preserve the original filename; fall back to index-based naming
        # only when the source has no name at all.
        dest_name = source_path.name if source_path.name else f"{field_name}_{idx:06d}.png"
        dest_name = sanitize_filename(dest_name)
        abs_path = output_dir / dest_name

        # Handle name collisions with a numeric suffix
        counter = 1
        while abs_path.exists():
            stem = source_path.stem if source_path.stem else f"{field_name}_{idx:06d}"
            suffix = source_path.suffix if source_path.suffix else ".png"
            abs_path = output_dir / sanitize_filename(f"{stem}_{counter}{suffix}")
            counter += 1

        rel_path = abs_path.name
        shutil.copy2(source_path, abs_path)
        return str(rel_path)
    except Exception as e:
        log.warning("Failed to copy image from %s: %s", value, e)
        return None


def _array_to_pil_image(img_data: np.ndarray, field_name: str, idx: int) -> Image.Image | None:
    """Convert a numpy array to a PIL Image."""
    if len(img_data.shape) == 2:
        return Image.fromarray(img_data.astype(np.uint8))
    if len(img_data.shape) == 3:
        if img_data.shape[2] == 1:
            return Image.fromarray(img_data[:, :, 0].astype(np.uint8))
        return Image.fromarray(img_data.astype(np.uint8))
    log.warning("Unsupported image shape %s for field %s, idx %d", img_data.shape, field_name, idx)
    return None


def _export_callable_field(
    value: object,
    field_name: str,
    idx: int,
    output_dir: Path,
    is_mask: bool = False,
) -> str | None:
    """Export an ImageCallableField or MaskCallableField by calling it and saving as PNG."""
    if not callable(value):
        return None

    try:
        img_data = value()
    except Exception as e:
        field_type = "mask" if is_mask else "image"
        log.warning("Failed to call %s callable for field %s, idx %d: %s", field_type, field_name, idx, e)
        return None

    if img_data is None:
        return None

    try:
        pil_img = _array_to_pil_image(img_data, field_name, idx)
        if pil_img is None:
            return None

        rel_path = sanitize_filename(f"{field_name}_{idx:06d}.png")
        abs_path = output_dir / rel_path
        pil_img.save(abs_path)
        return str(rel_path)
    except Exception as e:
        field_type = "mask" if is_mask else "image"
        log.warning("Failed to save %s for field %s, idx %d: %s", field_type, field_name, idx, e)
        return None


def _export_field_value(
    value: object,
    field: object,
    field_name: str,
    idx: int,
    output_dir: Path,
) -> str | None:
    """Export a single field value based on field type.

    Args:
        value: The field value to export
        field: The field object (determines export behavior)
        field_name: Name of the field
        idx: Row index
        output_dir: Directory to save the exported file

    Returns:
        Relative path to the exported file, or None if export failed
    """
    if isinstance(field, ImagePathField | MediaPathField):
        # MediaPathField with frame_index=None is treated like ImagePathField
        return _export_image_path_field(value, field_name, idx, output_dir)
    if isinstance(field, ImageCallableField):
        return _export_callable_field(value, field_name, idx, output_dir, is_mask=False)
    if isinstance(field, InstanceMaskCallableField | MaskCallableField):
        return _export_callable_field(value, field_name, idx, output_dir, is_mask=True)
    return None


def _is_video_frame_row(
    dataset: Dataset[DType],
    field_name: str,
    idx: int,
    is_media_path_field: bool,
) -> bool:
    """Check if a row represents a video frame (should be skipped for image export).

    For MediaPathField, rows where frame_index is not None are video frames.

    Args:
        dataset: The dataset
        field_name: Name of the field
        idx: Row index
        is_media_path_field: Whether the field is a MediaPathField

    Returns:
        True if the row is a video frame, False otherwise
    """
    if not is_media_path_field:
        return False

    frame_idx_col = f"{field_name}_frame_index"
    if frame_idx_col not in dataset.df.columns:
        return False

    frame_index = dataset.df[frame_idx_col][idx]
    return frame_index is not None


def _process_field_row(
    dataset: Dataset[DType],
    field_name: str,
    field: object,
    idx: int,
    output_dir: Path,
    is_media_path_field: bool,
) -> str | None:
    """Process a single row for field export.

    Args:
        dataset: The dataset
        field_name: Name of the field
        field: The field object
        idx: Row index
        output_dir: Directory to save the exported file
        is_media_path_field: Whether the field is a MediaPathField

    Returns:
        Relative path if exported successfully, None if row should be skipped
    """
    value = _get_field_value(dataset, idx, field_name)
    if value is None:
        return None

    if _is_video_frame_row(dataset, field_name, idx, is_media_path_field):
        return None

    return _export_field_value(value, field, field_name, idx, output_dir)


def _export_single_field(
    dataset: Dataset[DType],
    field_name: str,
    field: object,
    output_dir: Path,
    ignore_missing_media: bool = False,
) -> dict[int, str]:
    """Export images for a single field across all rows.

    For MediaPathField, only rows where frame_index is None (indicating an image
    not a video frame) are exported.

    Args:
        dataset: The dataset to export from
        field_name: Name of the field to export
        field: The field object
        output_dir: Directory to save images to
        ignore_missing_media: If True, silently skip media that cannot be found or
            generated, instead of raising an error.

    Returns:
        Dictionary mapping row indices to relative paths of exported images

    Raises:
        ValueError: If media is missing and ignore_missing_media is False
    """
    field_paths: dict[int, str] = {}
    is_media_path_field = isinstance(field, MediaPathField)

    for idx in range(len(dataset)):
        # Check if this is a video frame row (should be skipped, not an error)
        if _is_video_frame_row(dataset, field_name, idx, is_media_path_field):
            continue

        rel_path = _process_field_row(dataset, field_name, field, idx, output_dir, is_media_path_field)

        if rel_path is not None:
            field_paths[idx] = rel_path
            continue

        # rel_path is None - check if we should raise an error
        if ignore_missing_media:
            continue

        value = _get_field_value(dataset, idx, field_name)
        if value is None:
            continue

        raise ValueError(
            f"Value was set for field {field_name}, index {idx}, value {value}, but no image could be obtained "
            f"(ImagePathField/MediaPathField) or no image could be generated and saved (Image/MaskCallableField)."
        )

    return field_paths


def _export_images_from_dataset(
    dataset: Dataset[DType],
    output_dir: Path,
    ignore_missing_media: bool = False,
) -> dict[str, dict[int, str]]:
    """
    Export images from callable or path fields in the dataset.

    For ImagePathField: Copies images directly from filesystem (preserving format)
    For ImageCallableField: Saves as PNG (lossless for arrays)
    For InstanceMaskCallableField/MaskCallableField: Saves as PNG (best for masks)

    Args:
        dataset: The dataset to export images from
        output_dir: Directory to save images to
        ignore_missing_media: If True, silently skip media that cannot be found or
            generated, instead of raising an error.

    Returns:
        Dictionary mapping field names to dictionaries of row_idx -> relative path

    Raises:
        ValueError: If media is missing and ignore_missing_media is False
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths: dict[str, dict[int, str]] = {}

    image_fields = _get_image_fields(dataset)
    if not image_fields:
        return image_paths

    for field_name, field in image_fields:
        image_paths[field_name] = _export_single_field(dataset, field_name, field, output_dir, ignore_missing_media)

    return image_paths


def _collect_video_paths_from_fields(
    dataset: Dataset[DType],
    video_fields: list[tuple[str, Any]],
) -> set[str]:
    """Collect all unique video paths from video fields."""
    video_paths: set[str] = set()

    for field_name, field in video_fields:
        if isinstance(field, VideoFramePathField):
            if field_name in dataset.df.columns:
                paths = dataset.df[field_name].drop_nulls().unique().to_list()
                video_paths.update(str(p) for p in paths)
        elif isinstance(field, MediaPathField):
            # For MediaPathField, check if frame_index is set to identify video frames
            frame_idx_col = f"{field_name}_frame_index"
            if field_name in dataset.df.columns and frame_idx_col in dataset.df.columns:
                video_df = dataset.df.filter(pl.col(frame_idx_col).is_not_null())
                if len(video_df) > 0:
                    paths = video_df[field_name].drop_nulls().unique().to_list()
                    video_paths.update(str(p) for p in paths)

    return video_paths


def _copy_video_files(
    video_paths: set[str],
    output_dir: Path,
    ignore_missing_media: bool = False,
) -> dict[str, str]:
    """Copy video files to output directory and return path mapping.

    Args:
        video_paths: Set of video file paths to copy
        output_dir: Directory to copy videos to
        ignore_missing_media: If True, silently skip videos that cannot be found,
            instead of raising an error.

    Returns:
        Dictionary mapping original paths to relative exported paths

    Raises:
        ValueError: If video is missing and ignore_missing_media is False
    """
    video_path_mapping: dict[str, str] = {}

    for video_path in video_paths:
        source_path = Path(video_path)
        if not source_path.exists():
            if ignore_missing_media:
                log.warning("Video file not found: %s", video_path)
                continue
            raise ValueError(f"Video file not found: {video_path}")

        dest_path = output_dir / sanitize_filename(source_path.name)
        # Handle name collisions
        counter = 1
        while dest_path.exists():
            stem = source_path.stem
            suffix = source_path.suffix
            dest_path = output_dir / sanitize_filename(f"{stem}_{counter}{suffix}")
            counter += 1
        shutil.copy2(source_path, dest_path)
        rel_path = dest_path.relative_to(output_dir.parent).as_posix()
        video_path_mapping[video_path] = rel_path

    return video_path_mapping


def _export_videos_from_dataset(
    dataset: Dataset[DType],
    output_dir: Path,
    export_mode: ExportMode = ExportMode.COPY,
    ignore_missing_media: bool = False,
) -> dict[str, str]:
    """
    Export video data from the dataset.

    Modes:
        - ExportMode.REFERENCE: Store original video paths
        - ExportMode.COPY: Copy video files to output directory
        - ExportMode.SKIP: Don't export videos

    Args:
        dataset: The dataset to export
        output_dir: Output directory
        export_mode: How to handle video files
        ignore_missing_media: If True, silently skip videos that cannot be found,
            instead of raising an error.

    Returns:
        Mapping of original paths to exported paths

    Raises:
        ValueError: If video is missing and ignore_missing_media is False
    """
    if export_mode in {ExportMode.REFERENCE, ExportMode.SKIP}:
        # Keep original paths, no copying needed
        return {}

    # Collect all unique video paths
    video_fields = _get_video_fields(dataset)
    video_paths = _collect_video_paths_from_fields(dataset, video_fields)

    if not video_paths:
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)

    if export_mode == ExportMode.COPY:
        return _copy_video_files(video_paths, output_dir, ignore_missing_media)

    return {}


def _setup_work_directory(output_path: Path, as_zip: bool) -> tuple[Path, Path | None, Path]:
    """Setup the working directory for export.

    Returns:
        Tuple of (final_output_path, temp_dir, work_dir)

    Raises:
        FileExistsError: If the output path already exists (directory or zip file)
    """
    if as_zip:
        if output_path.suffix != ".zip":
            if output_path.exists() and not output_path.is_dir():
                raise FileExistsError(
                    f"Output path already exists as a file: '{output_path}'. "
                    "Please remove it or specify a different output path."
                )
            zip_path = output_path / "dataset.zip"
        else:
            zip_path = output_path
        if zip_path.exists():
            raise FileExistsError(
                f"Output file already exists: '{zip_path}'. Please remove it or specify a different output path."
            )
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp())
        return zip_path, temp_dir, temp_dir
    if output_path.exists():
        raise FileExistsError(
            f"Output directory already exists: '{output_path}'. Please remove it or specify a different output path."
        )
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path, None, output_path


def _update_df_with_image_paths(
    df: pl.DataFrame,
    images_paths: dict[str, dict[int, str]],
    media_path_fields: set[str],
) -> pl.DataFrame:
    """Update DataFrame with exported image paths."""
    df_to_export = df.with_row_index("__idx")

    for field_name, path_map in images_paths.items():
        if not path_map:
            continue

        # Create a mapping DataFrame from the exported paths
        mapping_df = pl.DataFrame(
            {"__idx": list(path_map.keys()), "__new_path": list(path_map.values())},
            schema={"__idx": pl.UInt32, "__new_path": pl.String},
        )

        df_to_export = df_to_export.join(mapping_df, on="__idx", how="left")

        if field_name in media_path_fields:
            # For MediaPathField, only update image rows (non-null in
            # path_map); preserve video-frame paths in other rows.
            df_to_export = df_to_export.with_columns(
                pl.coalesce(pl.col("__new_path"), pl.col(field_name)).alias(field_name)
            )
            df_to_export = df_to_export.drop("__new_path")
        else:
            # For all other image fields, drop the old column (may be
            # Object type) and rename the new String column in its place.
            df_to_export = df_to_export.drop(field_name).rename({"__new_path": field_name})

    return df_to_export.drop("__idx")


def _update_df_with_video_paths(
    df: pl.DataFrame,
    video_path_mapping: dict[str, str],
    video_fields: list[tuple[str, Any]],
) -> pl.DataFrame:
    """Update DataFrame with exported video paths."""
    df_to_export = df
    for field_name, _ in video_fields:
        if field_name in df_to_export.columns:
            df_to_export = df_to_export.with_columns(pl.col(field_name).replace(video_path_mapping).alias(field_name))
    return df_to_export


def _write_parquet_and_metadata(
    df_to_export: pl.DataFrame,
    work_dir: Path,
    dataset: Dataset[DType],
    export_media: ExportMode,
    video_path_mapping: dict[str, str],
) -> None:
    """Write parquet file and metadata to the work directory."""
    # Filter out Object columns (like callables) as they can't be serialized to Parquet
    columns_to_export = [col for col, dtype in df_to_export.schema.items() if dtype != pl.Object]
    parquet_path = work_dir / DATAFRAME_FILE
    df_to_export.select(columns_to_export).write_parquet(parquet_path)

    # Track which columns are Object types (excluded from parquet)
    object_columns = [col for col, dtype in df_to_export.schema.items() if dtype == pl.Object]

    # Create metadata
    metadata = {
        "version": VERSION,
        "schema": dataset.schema.to_dict(),
        "object_columns": object_columns,
        "videos": {
            "fields": [name for name, _ in _get_video_fields(dataset)],
            "export_mode": export_media.value,
            "original_paths": {v: k for k, v in video_path_mapping.items()},
        },
    }

    # Write metadata
    metadata_path = work_dir / METADATA_FILE
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)


def _create_zip_archive(output_path: Path, work_dir: Path) -> None:
    """Create a ZIP archive from the work directory."""
    with ZipFile(output_path, "w", ZIP_DEFLATED) as zipf:
        for file_path in work_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(work_dir).as_posix()
                zipf.write(file_path, arcname)


def _save_format_to_dir(
    dataset: Dataset[DType],
    data_format: DataFormat,
    output_dir: str,
    direct_only: bool = False,
) -> None:
    """Save *dataset* in a format-specific layout to *output_dir*."""
    import os

    if data_format == DataFormat.COCO:
        from getidata.data_formats.coco.io import save_coco_dataset
        from getidata.data_formats.coco.sample import CocoSample

        dataset = dataset.convert_to_schema(CocoSample.infer_schema(), direct_only=direct_only)
        save_coco_dataset(
            dataset,
            images_dir_path=os.path.join(output_dir, "images"),
            annotations_path=os.path.join(output_dir, "annotations.json"),
        )
    elif data_format == DataFormat.VOC:
        from getidata.data_formats.voc.io import save_voc_dataset
        from getidata.data_formats.voc.sample import VocSample

        dataset = dataset.convert_to_schema(VocSample.infer_schema(), direct_only=direct_only)
        save_voc_dataset(dataset, root_dir=output_dir)
    elif data_format in (DataFormat.YOLO, DataFormat.YOLO_ULTRALYTICS):
        from getidata.data_formats.yolo.io import save_yolo_dataset
        from getidata.data_formats.yolo.sample import YoloSample

        dataset = dataset.convert_to_schema(YoloSample.infer_schema(), direct_only=direct_only)
        save_yolo_dataset(dataset, root_dir=output_dir, format=data_format)
    else:
        raise ValueError(f"Unsupported data format for export: {data_format}")


def _save_format_dataset(
    dataset: Dataset[DType],
    data_format: DataFormat,
    output_path: str,
    as_zip: bool = False,
    direct_only: bool = False,
) -> None:
    """Export *dataset* in a non-getidata format, optionally as a ZIP archive.

    Raises:
        FileExistsError: If the target output (directory or ZIP archive) already exists.
        ValueError: If *data_format* is not a supported export format.
    """
    _SUPPORTED_EXPORT_FORMATS = {
        DataFormat.COCO,
        DataFormat.VOC,
        DataFormat.YOLO,
        DataFormat.YOLO_ULTRALYTICS,
    }
    if data_format not in _SUPPORTED_EXPORT_FORMATS:
        raise ValueError(f"Unsupported data format for export: {data_format}")

    output_path_obj = Path(output_path)

    if as_zip:
        archive_path = output_path_obj.with_suffix(".zip")
        base = str(archive_path.with_suffix(""))
        if archive_path.exists():
            raise FileExistsError(
                f"Target ZIP archive already exists: '{archive_path}'. "
                "Please remove it or specify a different output path."
            )
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp_dir:
            _save_format_to_dir(dataset, data_format, tmp_dir, direct_only=direct_only)
            shutil.make_archive(base_name=base, format="zip", root_dir=tmp_dir)
    else:
        if output_path_obj.exists():
            raise FileExistsError(
                f"Target output directory already exists: '{output_path_obj}'. "
                "Please remove it or specify a different output path."
            )
        output_path_obj.mkdir(parents=True, exist_ok=True)
        _save_format_to_dir(dataset, data_format, output_path, direct_only=direct_only)


def _load_format_dataset(
    data_format: DataFormat,
    images_dir_path: str | dict[str, str] | None = None,
    annotations_path: str | list[str] | dict[str, str | list[str]] | None = None,
    root_dir: str | None = None,
) -> Dataset:
    """Load a dataset given an explicit *data_format* and format-specific paths."""
    if data_format == DataFormat.COCO:
        from getidata.data_formats.coco.io import load_coco_dataset

        if images_dir_path is None or annotations_path is None:
            raise ValueError("images_dir_path and annotations_path are required for COCO format")

        return load_coco_dataset(
            images_dir_path=images_dir_path,
            annotations_path=annotations_path,
        )
    if data_format == DataFormat.VOC:
        from getidata.data_formats.voc.io import load_voc_dataset

        if root_dir is not None:
            return load_voc_dataset(root_dir=root_dir)
        if images_dir_path is not None:
            annotations_dir = annotations_path if isinstance(annotations_path, str) else None
            return load_voc_dataset(
                images_dir_path=images_dir_path if isinstance(images_dir_path, str) else None,
                annotations_dir_path=annotations_dir,
            )
        raise ValueError("root_dir or images_dir_path is required for VOC format")
    if data_format in (DataFormat.YOLO, DataFormat.YOLO_ULTRALYTICS):
        from getidata.data_formats.yolo.io import load_yolo_dataset

        if root_dir is None:
            raise ValueError("root_dir is required for YOLO format")

        format_hint = "ultralytics" if data_format == DataFormat.YOLO_ULTRALYTICS else "auto"
        return load_yolo_dataset(root_dir=root_dir, format=format_hint)
    raise ValueError(f"Unsupported data format: {data_format}")


def export_dataset(
    dataset: Dataset[DType],
    output_path: str | Path,
    export_media: ExportMode = ExportMode.COPY,
    as_zip: bool = False,
    ignore_missing_media: bool = False,
    direct_only: bool = False,
    data_format: DataFormat | None = None,
) -> None:
    """
    Export a dataset to disk in a structured format.

    By default the dataset is exported in native getidata format with the
    following structure:

    - data.parquet: The DataFrame in Parquet format
    - metadata.json: Schema, categories, image paths, and video metadata
    - images/: Directory containing exported images (if export_media is COPY)
    - videos/: Directory containing exported videos (if export_media is COPY)

    When ``data_format`` is set to a non-getidata format (e.g.
    ``DataFormat.COCO``, ``DataFormat.VOC``, ``DataFormat.YOLO``), the dataset
    is first converted to the target format's schema and then saved using the
    format-specific writer.

    Image format is automatically determined:
    - ImagePathField: Preserves original format (copied directly)
    - ImageCallableField: Saved as PNG (lossless)
    - InstanceMaskCallableField/MaskCallableField: Saved as PNG (best for masks)

    Export modes (only apply to native getidata format):
    - ExportMode.SKIP: Don't export media files. Use this when you don't need
      the media files in the export (e.g., metadata-only export).
    - ExportMode.REFERENCE: Keep original absolute paths in the DataFrame. Use
      this when files should remain in their original locations and you don't
      need a portable dataset. This is faster but the exported dataset will
      break if moved or if original files are deleted.
    - ExportMode.COPY: Copy files to a subdirectory in the output and update
      paths to be relative. This creates a self-contained, portable dataset.
      Recommended for sharing or archiving datasets.

    Args:
        dataset: The dataset to export
        output_path: Path to export to (directory or .zip file)
        export_media: How to handle media (images and videos). Default is
            ExportMode.COPY.
        as_zip: Whether to package everything as a ZIP file
        ignore_missing_media: If True, silently skip media files (images and videos)
            that cannot be found or generated, instead of raising an error.
            Only has an effect when ``export_media`` is ``ExportMode.COPY``;
            otherwise, it is ignored.
        direct_only: If True, only apply converters where all output field types
            match (are a subset of) the input field types. Cross-field-type
            converters (e.g., BBoxField→PolygonField) are skipped.
            :class:`~getidata.converters.base.MediaBridgeConverter`
            subclasses (e.g., MediaPathField→ImagePathField) are always
            allowed regardless of this flag. Only has an
            effect when ``data_format`` is set to a non-getidata format that
            requires schema conversion.
        data_format: Target data format for export. When ``None`` (default),
            exports in native getidata format (parquet + metadata).  Set to
            ``DataFormat.COCO``, ``DataFormat.VOC``, ``DataFormat.YOLO``, etc.
            to convert and save in that format.
    """
    if data_format is not None and data_format != DataFormat.GETIDATA:
        _save_format_dataset(
            dataset,
            data_format=data_format,
            output_path=str(output_path),
            as_zip=as_zip,
            direct_only=direct_only,
        )
        return

    output_path, temp_dir, work_dir = _setup_work_directory(Path(output_path), as_zip)

    try:
        df_to_export = dataset.df
        video_path_mapping: dict[str, str] = {}

        # Export images if requested
        if export_media == ExportMode.COPY:
            images_dir = work_dir / IMAGES_DIR
            images_paths = _export_images_from_dataset(dataset, images_dir, ignore_missing_media)
            media_path_fields = {name for name, f in _get_image_fields(dataset) if isinstance(f, MediaPathField)}
            df_to_export = _update_df_with_image_paths(df_to_export, images_paths, media_path_fields)

        # Export videos
        if export_media == ExportMode.COPY:
            videos_dir = work_dir / VIDEOS_DIR
            video_path_mapping = _export_videos_from_dataset(dataset, videos_dir, export_media, ignore_missing_media)
            if video_path_mapping:
                video_fields = _get_video_fields(dataset)
                df_to_export = _update_df_with_video_paths(df_to_export, video_path_mapping, video_fields)

        # Write parquet and metadata
        _write_parquet_and_metadata(df_to_export, work_dir, dataset, export_media, video_path_mapping)

        # Create ZIP if requested
        if as_zip:
            _create_zip_archive(output_path, work_dir)

    finally:
        # Clean up temporary directory if used
        if as_zip and temp_dir is not None and temp_dir.exists():
            shutil.rmtree(temp_dir)


def import_dataset(
    input_path: str | Path,
    dtype: type[DType] | None = None,
    extract_dir: str | Path | None = None,
    *,
    data_format: DataFormat | None = None,
    images_dir_path: str | dict[str, str] | None = None,
    annotations_path: str | list[str] | dict[str, str | list[str]] | None = None,
    root_dir: str | None = None,
) -> Dataset[DType]:
    """
    Import a dataset from an exported format.

    When ``data_format`` is ``None`` the format is auto-detected from the directory
    contents.  Set ``data_format`` explicitly together with the format-specific path
    arguments when auto-detection is not desired.

    All media paths (images and videos) are resolved relative to the export
    directory.  Images are stored under ``images/`` and videos under ``videos/``,
    so no external root parameter is needed.

    This function automatically detects the dataset format and calls the appropriate
    loader. Supported formats include:

    - **getidata**: Native format with metadata.json and data.parquet files
    - **COCO**: Detected by annotations directory with COCO JSON files, or JSON files
      with 'images' and 'annotations' keys
    - **YOLO**: Detected by data.yaml (Ultralytics), obj.names/obj.data (traditional),
      or images/ and labels/ directories
    - **VOC**: Detected by JPEGImages/, Annotations/, and ImageSets/ directories

    When dtype is None the function tries to automatically determine the correct Sample
    subclass by matching the stored schema against all registered subclasses (discovered
    via the :func:`register_sample` registry). If no match is found, it falls back to
    the base ``Sample`` class.

    Args:
        input_path: Path to the exported dataset (directory or .zip file)
        dtype: Optional Sample class to use for the dataset. When provided,
            the dataset is typed with this class directly. When ``None``,
            automatic dtype detection is attempted (see above). This parameter
            is only used for getidata format datasets.
        extract_dir: Optional directory to extract zip contents to. If not provided,
            the zip will be extracted to a directory next to the zip file with the
            same name (excluding the .zip extension). This parameter is ignored
            when input_path is a directory.
        data_format: When set, skip auto-detection and load using this format
            directly. Requires the appropriate format-specific keyword arguments
            (``images_dir_path``, ``annotations_path``, ``root_dir``).
        images_dir_path: Path to image directory (str) or dict mapping subset
            names to paths. Only used when ``data_format`` is set explicitly.
        annotations_path: Path to annotations file/directory. Only used when
            ``data_format`` is set explicitly.
        root_dir: Root directory for YOLO or VOC format datasets. Only used
            when ``data_format`` is set explicitly.

    Returns:
        The imported Dataset instance

    Raises:
        FileNotFoundError: If required files are missing
        ValueError: If the dataset format is invalid or cannot be detected

    Examples:
        Import a getidata-exported dataset::
            dataset = import_dataset("/path/to/exported_dataset")

        Import a YOLO dataset (auto-detected)::
            dataset = import_dataset("/path/to/yolo_dataset")

        Import a COCO dataset with explicit format::
            dataset = import_dataset(
                "/path/to/coco",
                data_format=DataFormat.COCO,
                images_dir_path="/path/to/images",
                annotations_path="/path/to/annotations.json",
            )
    """
    input_path = Path(input_path)

    if data_format is not None:
        # When an explicit format is provided, use input_path as the default
        # root_dir so that the positional argument is not silently ignored.
        if root_dir is None:
            root_dir = str(input_path)
        return _load_format_dataset(
            data_format=data_format,
            images_dir_path=images_dir_path,
            annotations_path=annotations_path,
            root_dir=root_dir,
        )

    if is_zipfile(input_path):
        if extract_dir is not None:
            extract_dir = Path(extract_dir)
        else:
            # Default: extract to a directory next to the zip with the same name (minus .zip)
            extract_dir = input_path.with_suffix("")

        extract_dir.mkdir(parents=True, exist_ok=True)
        with ZipFile(input_path) as zipf:
            # Validate all zip entries to prevent Zip Slip (path traversal) attacks
            resolved_extract_dir = extract_dir.resolve()
            for member in zipf.namelist():
                member_path = (resolved_extract_dir / member).resolve()
                if not member_path.is_relative_to(resolved_extract_dir):
                    raise ValueError(
                        f"Zip entry '{member}' would extract outside the target directory. "
                        f"This may indicate a malicious archive (Zip Slip attack)."
                    )
            zipf.extractall(extract_dir)

        _sanitize_extracted_files(extract_dir)

        dataset_root = find_dataset_root(extract_dir)
        return _import_dataset_from_dir(dataset_root, dtype)
    return _import_dataset_from_dir(input_path, dtype)


def _sanitize_extracted_files(directory: Path) -> None:
    """Rename files whose names contain characters illegal that might be illegal on certain Operating systems.

    Walks *directory* bottom-up so that files inside subdirectories are
    renamed before their parent directories.  Only the final path component
    (the file/directory name) is sanitized; parent components are left as-is
    because they have already been created by the zip extraction.

    After renaming, any JSON or YAML annotation files within *directory* are
    updated so that references to the old filenames point to the new names.
    """
    # Collect all paths first, then process bottom-up to avoid issues with
    # iterating while renaming.
    all_paths = sorted(directory.rglob("*"), key=lambda p: len(p.parts), reverse=True)

    # Mapping of old path/name strings -> new path/name strings for text-file patching
    rename_map: dict[str, str] = {}
    basename_targets: dict[str, set[str]] = {}

    for path in all_paths:
        sanitized_name = sanitize_filename(path.name)
        if sanitized_name != path.name:
            new_path = path.parent / sanitized_name
            # Handle collisions
            counter = 1
            while new_path.exists() and new_path != path:
                stem, *ext_parts = sanitized_name.rsplit(".", 1)
                suffix = f".{ext_parts[0]}" if ext_parts else ""
                new_path = path.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            if new_path != path:
                log.info("Renaming '%s' -> '%s' (filename sanitization)", path.name, new_path.name)
                old_rel_path = path.relative_to(directory).as_posix()
                new_rel_path = new_path.relative_to(directory).as_posix()
                rename_map[old_rel_path] = new_rel_path
                basename_targets.setdefault(path.name, set()).add(new_path.name)
                path.rename(new_path)

    # Also patch basename-only references where the mapping is unambiguous.
    for old_name, new_names in basename_targets.items():
        if len(new_names) == 1:
            rename_map.setdefault(old_name, next(iter(new_names)))

    # Patch annotation files that may reference the old filenames
    if rename_map:
        _patch_annotation_files(directory, rename_map)


def _patch_annotation_files(directory: Path, rename_map: dict[str, str]) -> None:
    """Update annotation files so they reference the new (sanitized) filenames.

    Handles JSON/YAML/XML/TXT annotation-like files by performing string
    replacement of old path/name references with the new sanitized values.
    """
    annotation_extensions = {".json", ".yaml", ".yml", ".xml", ".txt"}
    # Replace longer keys first so path replacements like "sub1/img:1.jpg" are
    # applied before basename-only replacements like "img:1.jpg".
    replacements = sorted(rename_map.items(), key=lambda item: len(item[0]), reverse=True)

    for ann_path in directory.rglob("*"):
        if not ann_path.is_file() or ann_path.suffix.lower() not in annotation_extensions:
            continue
        try:
            text = ann_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        updated = text
        for old_name, new_name in replacements:
            updated = updated.replace(old_name, new_name)

        if updated != text:
            log.info("Patching annotation file '%s' with sanitized filenames", ann_path)
            ann_path.write_text(updated, encoding="utf-8")


def _load_metadata(input_dir: Path) -> dict:
    """Load and validate metadata file."""
    metadata_path = input_dir / METADATA_FILE
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path) as f:
        metadata = json.load(f)

    if metadata.get("version") != VERSION:
        log.warning(
            "Dataset version %s may not be fully compatible with current version %s",
            metadata.get("version"),
            VERSION,
        )

    return metadata


def _load_dataframe(input_dir: Path) -> pl.DataFrame:
    """Load DataFrame from parquet file."""
    parquet_path = input_dir / DATAFRAME_FILE
    if not parquet_path.exists():
        raise FileNotFoundError(f"DataFrame file not found: {parquet_path}")

    return pl.read_parquet(parquet_path)


@dataclass(frozen=True)
class _ImageFileLoader:
    """Picklable callable that lazily loads an image from *path* on demand.

    Used in place of a locally-defined closure so that datasets containing this
    callable can be passed to ``torch.utils.data.DataLoader`` workers started
    with the ``spawn`` multiprocessing context, which requires every object
    reachable from the ``Dataset`` to be picklable. A closure defined inside a
    function is not picklable by the standard ``pickle`` module, whereas a
    module-level dataclass instance with simple (picklable) attributes is.
    """

    path: Path

    def __call__(self) -> np.ndarray:
        # Apply EXIF orientation so the loaded array matches the image as
        # displayed (consistent with LazyImage).
        with Image.open(self.path) as img:
            return np.array(ImageOps.exif_transpose(img))


def _make_image_loader(path: Path) -> _ImageFileLoader:
    """Create a picklable lazy loader callable for an image path."""
    return _ImageFileLoader(path)


def _build_index_based_lookup(field_name: str, images_base_dir: Path) -> dict[int, Path]:
    """Build a one-time row-index lookup for a field's index-named files.

    Scans ``images_base_dir`` a single time for files matching the
    ``{field_name}_{idx:06d}.*`` naming convention (used by callable fields
    such as generated masks) and returns a mapping from row index to the
    resolved file path.

    This is built once per field rather than re-globbing the directory for
    every row: calling :meth:`Path.glob` inside a per-row loop rescans the
    entire directory on every call, which is O(rows * files) overall and
    becomes prohibitively slow for large datasets (e.g. tens of thousands of
    images can take hours). Building the lookup once is O(files).
    """
    lookup: dict[int, Path] = {}
    prefix = f"{field_name}_"
    # The original per-row glob pattern was `{prefix}{idx:06d}.*`, i.e.
    # literal prefix + literal zero-padded index + literal "." + anything.
    # Match that exact shape here: digits immediately followed by a dot.
    # Using `Path.stem`/`.suffix` instead would mis-parse filenames with
    # extra dots (e.g. "mask_000001.v1.png" strips to stem "mask_000001.v1")
    # and would wrongly accept extension-less files (no "." at all), which
    # the original glob pattern could never match.
    index_pattern = re.compile(r"^(\d+)\.")
    for candidate in sorted(images_base_dir.glob(f"{prefix}*")):
        rest = candidate.name[len(prefix) :]
        match = index_pattern.match(rest)
        if match is None:
            continue
        idx_part = match.group(1)
        idx = int(idx_part)
        # Require the canonical zero-padded (min-width 6) form, so this only
        # recognizes filenames the exporter itself would have produced -
        # exactly matching what the previous per-row `{idx:06d}` glob pattern
        # would (and would not) have matched.
        if f"{idx:06d}" != idx_part:
            continue
        # Keep the first match per index, mirroring the previous
        # `sorted(images_base_dir.glob(pattern))[0]` behavior.
        lookup.setdefault(idx, candidate)
    return lookup


def _resolve_image_file(
    idx: int,
    images_base_dir: Path,
    df_path: str | None = None,
    index_lookup: dict[int, Path] | None = None,
) -> Path | None:
    """Find the exported image file for a given row index.

    Resolution order:
    1. ``index_lookup`` - an O(1) lookup by row index into a mapping built
       once for the whole field by :func:`_build_index_based_lookup` from
       the ``{field_name}_{idx:06d}.*`` naming convention used by callable
       fields (e.g. generated masks), instead of rescanning the directory
       for every row.
    2. The relative path stored in the parquet DataFrame (used by path fields
       that preserve the original filename)
    """
    # 1. Try index-based naming (callable fields always use this)
    if index_lookup is not None:
        match = index_lookup.get(idx)
        if match is not None:
            return match

    # 2. Try the path stored in parquet (original filename preserved by
    #    _export_image_path_field)
    if df_path is not None:
        candidate = images_base_dir / df_path
        if candidate.exists():
            return candidate
        # Try with sanitized filename (handles cross-OS imports, e.g.
        # colons in filenames from Linux on Windows)
        sanitized = sanitize_filename(Path(df_path).name, cross_platform=False)
        if sanitized != Path(df_path).name:
            candidate = images_base_dir / sanitized
            if candidate.exists():
                return candidate

    return None


def _reconstruct_field_values(
    field_name: str,
    field: object,
    images_base_dir: Path,
    num_rows: int,
    df: pl.DataFrame | None = None,
) -> tuple[list[object | None], bool, bool]:
    """
    Reconstruct values for a single image-related field.

    For MediaPathField, only image rows (those exported to images/) are
    reconstructed here.  Video-frame rows are handled by
    ``_reconstruct_video_fields``.

    Returns:
        Tuple of (values list, is_path_field, is_callable_field)
    """
    is_path_field = isinstance(field, ImagePathField | MediaPathField)
    is_callable_field = isinstance(field, ImageCallableField | InstanceMaskCallableField | MaskCallableField)

    if not (is_path_field or is_callable_field):
        return [], False, False

    # Build the index-named-file lookup once per field (a single directory
    # scan) instead of calling `Path.glob` inside the per-row loop below,
    # which would rescan the whole directory for every row (O(rows * files)).
    index_lookup = _build_index_based_lookup(field_name, images_base_dir)

    values: list[object | None] = []
    for idx in range(num_rows):
        # Get the path stored in parquet (if available) for fallback resolution
        df_path: str | None = None
        if df is not None and field_name in df.columns:
            raw = df[field_name][idx]
            if raw is not None:
                df_path = str(raw)

        file_path = _resolve_image_file(idx, images_base_dir, df_path, index_lookup)

        if is_path_field:
            values.append(str(file_path) if file_path is not None else None)
        elif file_path is None:
            values.append(None)
        else:
            values.append(_make_image_loader(file_path))

    return values, is_path_field, is_callable_field


def _update_dataframe_with_field(
    df: pl.DataFrame,
    field_name: str,
    values: list[object | None],
    is_path_field: bool,
    is_media_path_field: bool = False,
) -> pl.DataFrame:
    """Update DataFrame with reconstructed field values.

    For MediaPathField, only non-None values are applied so that video-frame
    rows (which were not exported to images/) keep their existing paths.
    """
    if is_path_field:
        if is_media_path_field and field_name in df.columns:
            # Only overwrite rows where we found an exported image;
            # leave video-frame rows (None in values) untouched.
            new_series = pl.Series(field_name, values, dtype=pl.String())
            return df.with_columns(
                pl.when(new_series.is_not_null()).then(new_series).otherwise(pl.col(field_name)).alias(field_name)
            )
        if field_name in df.columns:
            df = df.drop(field_name)
        return df.with_columns(pl.Series(field_name, values, dtype=pl.String()))
    # Callable fields (e.g. lazy image/mask loaders) must be forced to ``pl.Object()``:
    # letting Polars infer the dtype from a list of callables is unreliable -- e.g. a
    # dataclass-based loader (which exposes named attributes) can be misidentified as a
    # nested struct, raising ``InvalidOperation: nested objects are not allowed``.
    # ``with_columns`` adds the column when absent and replaces it when present, so a
    # single branch handles both cases.
    return df.with_columns(pl.Series(field_name, values, dtype=pl.Object()))


def _reconstruct_image_fields(
    df: pl.DataFrame,
    schema: Schema,
    images_base_dir: Path,
) -> pl.DataFrame:
    """Reconstruct image-related fields from the images directory."""
    if not images_base_dir.exists():
        return df

    for field_name, attr_info in schema.attributes.items():
        field = getattr(attr_info, "field", None)
        if field is None:
            continue

        values, is_path_field, is_callable_field = _reconstruct_field_values(
            field_name, field, images_base_dir, len(df), df=df
        )

        if is_path_field or is_callable_field:
            df = _update_dataframe_with_field(
                df,
                field_name,
                values,
                is_path_field,
                is_media_path_field=isinstance(field, MediaPathField),
            )

    return df


def _add_missing_object_columns(
    df: pl.DataFrame,
    object_columns: list[str],
) -> pl.DataFrame:
    """Add back any object columns that weren't reconstructed from images."""
    for col_name in object_columns:
        if col_name not in df.columns:
            df = df.with_columns(pl.Series(col_name, [None] * len(df), dtype=pl.Object()))
    return df


def _get_registered_samples() -> list[type[Sample]]:
    """Get all Sample subclasses that have been explicitly registered.

    Only returns classes that were registered via :func:`register_sample`.

    Returns:
        List of explicitly registered Sample subclasses
    """
    return list(_sample_registry)


def _match_dtype_from_schema(schema: Schema) -> type[Sample]:
    """Try to match a schema against registered Sample subclasses.

    Compares the serialized schema attributes (including field configurations like
    dtype, semantic, is_list, format, etc.) between the loaded schema and each
    registered Sample subclass's inferred schema. Categories are not compared
    since they may differ between loaded and inferred schemas.

    Args:
        schema: The schema loaded from the dataset metadata

    Returns:
        The matching Sample subclass, or base Sample if no match is found
    """
    schema_dict = schema.to_dict()
    schema_attributes = schema_dict.get("attributes", {})

    for subclass in _get_registered_samples():
        candidate_schema = subclass.infer_schema()
        candidate_dict = candidate_schema.to_dict()
        candidate_attributes = candidate_dict.get("attributes", {})
        if schema_attributes == candidate_attributes:
            return subclass

    return Sample


def _resolve_reconstructed_video_path(path: str | None, input_dir: Path) -> str | None:
    """Resolve a reconstructed video path under *input_dir* for copy-mode imports."""
    if path is None:
        return None
    abs_path = input_dir / path
    if abs_path.exists():
        return str(abs_path)

    # Fallback for archives where extracted filenames were
    # sanitized on this OS (e.g. control chars renamed).
    path_obj = Path(path)
    # Use OS-specific sanitization to mirror _sanitize_extracted_files behavior.
    sanitized_parts = tuple(sanitize_filename(part, cross_platform=False) for part in path_obj.parts)
    if sanitized_parts != path_obj.parts:
        sanitized_abs_path = input_dir.joinpath(*sanitized_parts)
        if sanitized_abs_path.exists():
            return str(sanitized_abs_path)
    return path


def _reconstruct_video_fields(
    df: pl.DataFrame,
    metadata: dict,
    input_dir: Path,
) -> pl.DataFrame:
    """
    Reconstruct video frame fields from exported data.

    For ``copy`` mode, relative paths stored in the parquet are resolved to
    absolute paths under *input_dir*.  For ``reference`` mode the original
    absolute paths are preserved as-is.

    Args:
        df: DataFrame to update
        metadata: Loaded metadata dictionary
        input_dir: Directory containing the exported dataset

    Returns:
        Updated DataFrame with corrected video paths
    """
    videos_info = metadata.get("videos", {})
    if not videos_info:
        return df

    video_fields = videos_info.get("fields", [])
    export_mode = videos_info.get("export_mode", "reference")

    if not video_fields:
        return df

    for field_name in video_fields:
        if field_name not in df.columns:
            continue

        if export_mode == "copy":
            paths = df[field_name].to_list()
            updated_paths = [_resolve_reconstructed_video_path(p, input_dir) for p in paths]
            df = df.with_columns(pl.Series(field_name, updated_paths, dtype=pl.String()))

    return df


def _import_dataset_from_dir(
    input_dir: Path,
    dtype: type[DType] | None = None,
) -> Dataset[DType]:
    """
    Import dataset from a directory.

    Automatically detects the dataset format and delegates to the appropriate
    loader for COCO, YOLO, or native getidata formats.

    Args:
        input_dir: Directory containing the exported dataset
        dtype: Optional Sample class to use (only applies to getidata format)

    Returns:
        The imported Dataset instance

    Raises:
        ValueError: If the dataset format cannot be detected
    """
    # Detect the dataset format and dispatch to appropriate loader
    match detect_dataset_format(input_dir):
        case DataFormat.COCO:
            from getidata.data_formats.coco.io import import_coco_dataset

            return import_coco_dataset(input_dir)
        case DataFormat.YOLO:
            from getidata.data_formats.yolo.io import import_yolo_dataset

            return import_yolo_dataset(input_dir)
        case DataFormat.VOC:
            from getidata.data_formats.voc.io import import_voc_dataset

            return import_voc_dataset(input_dir)
        case DataFormat.GETIDATA:
            return _import_getidata_dataset(input_dir, dtype)
        case _:
            raise ValueError(
                f"Could not detect dataset format in '{input_dir}'. "
                "Expected one of: getidata (metadata.json + data.parquet), "
                "COCO (annotations/*.json with 'images' and 'annotations' keys), "
                "YOLO (data.yaml, obj.names, or images/ + labels/ directories), "
                "or VOC (JPEGImages/ + Annotations/ or ImageSets/ directories)."
            )


def _import_getidata_dataset(
    input_dir: Path,
    dtype: type[DType] | None = None,
) -> Dataset[DType]:
    """Import a native getidata-format dataset from a directory."""
    metadata = _load_metadata(input_dir)
    df = _load_dataframe(input_dir)  # Check DataFrame exists before processing schema
    schema = Schema.from_dict(metadata["schema"])

    object_columns = metadata.get("object_columns", [])
    images_base_dir = input_dir / IMAGES_DIR

    df = _reconstruct_image_fields(df, schema, images_base_dir)
    df = _add_missing_object_columns(df, object_columns)

    # Reconstruct video fields
    df = _reconstruct_video_fields(df, metadata, input_dir)

    if dtype is None:
        dtype = _match_dtype_from_schema(schema)

    return Dataset.from_dataframe(df, dtype, schema=schema)
