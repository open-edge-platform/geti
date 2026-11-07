# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Helper functions for Pascal VOC dataset I/O.
"""

import logging
import shutil
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from xml.etree.ElementTree import Element  # nosec B405 - only used for type hints and writing, not parsing

import numpy as np
from defusedxml import ElementTree

from getidata import Dataset
from getidata.categories import LabelCategories
from getidata.data_formats.base import IMAGE_EXTENSIONS, find_images
from getidata.data_formats.voc.constants import (
    SUBSET_TO_VOC_NAME,
    VOC_ANNOTATIONS_DIR,
    VOC_IMAGES_DIR,
    VOC_IMAGESETS_DIR,
    VOC_LABELMAP_FILE,
    VOC_LABELS,
    VOC_MAIN_DIR,
    VOC_SEGMENTATION_CLASS_DIR,
    VOC_SEGMENTATION_OBJECT_DIR,
    VOC_SUBSET_NAME_TO_ENUM,
)
from getidata.data_formats.voc.sample import VocSample
from getidata.fields import ImageInfo, Subset

logger = logging.getLogger(__name__)


def _get_image_size(image_path: Path) -> tuple[int, int]:
    """Get image dimensions (height, width) using PIL, honoring EXIF orientation."""
    try:
        from PIL import Image

        from getidata.exif_utils import get_exif_orientation, get_oriented_size

        with Image.open(image_path) as img:
            w, h = img.size
            w, h = get_oriented_size(w, h, get_exif_orientation(img))
            return h, w  # height, width
    except Exception as e:
        logger.warning("Failed to read image size from %s: %s", image_path, e)
        return 0, 0


def _find_image_file(images_dir: Path, stem: str) -> Path | None:
    """Find an image file with any supported extension."""
    for candidate in images_dir.glob(f"{stem}.*"):
        if candidate.suffix.lower() in IMAGE_EXTENSIONS:
            return candidate
    return None


def _build_image_index(
    images_dir: Path,
    image_paths: list[str] | None = None,
) -> dict[str, Path]:
    """Build a one-time stem -> path lookup for all images in a directory.

    ``_find_image_file`` calls :meth:`Path.glob` for a single stem, which
    rescans the entire directory every time it's invoked. Calling it once
    per sample (as ``_create_sample_from_annotation`` does for every image in
    the dataset) makes loading an O(images * files) operation, which becomes
    prohibitively slow for large datasets. Building this index once (a single
    directory scan) and reusing it for every sample makes loading O(files).

    ``_find_image_file(images_dir, stem)`` resolves via
    ``images_dir.glob(f"{stem}.*")``, which matches on *any* "." in the
    filename, not just the last one - e.g. "img0001.v1.png" is matched by
    both ``stem="img0001"`` and ``stem="img0001.v1"``. A single ``Path.stem``
    (which only strips the final suffix) would miss the "img0001" case, so
    every filename is registered under *each* prefix ending right before one
    of its "." characters, not just the last.

    Args:
        images_dir: The directory containing image files.
        image_paths: Optional pre-discovered list of image paths. When a
            caller has already scanned the directory (e.g.
            ``_load_voc_simple``), passing the already-resolved paths avoids
            a redundant second filesystem scan.
    """
    index: dict[str, Path] = {}
    if image_paths is not None:
        iterable = image_paths
    else:
        iterable = find_images(str(images_dir))
    for image_path in sorted(iterable):
        path = Path(image_path) if isinstance(image_path, str) else image_path
        name = path.name
        start = 0
        while True:
            dot_pos = name.find(".", start)
            if dot_pos == -1:
                break
            prefix = name[:dot_pos]
            if prefix:
                index.setdefault(prefix, path)
            start = dot_pos + 1
    return index


def _parse_voc_labelmap(labelmap_path: Path) -> list[str]:
    """
    Parse a VOC labelmap file.

    Format: 'name : color (r, g, b) : parts : actions'
    Only the name is extracted.

    Returns:
        List of label names in order.
    """
    labels = []
    with open(labelmap_path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # name : color : parts : actions
            parts = line.split(":")
            if parts:
                name = parts[0].strip()
                if name:
                    labels.append(name)
    return labels


def _parse_voc_labelmap_with_colors(labelmap_path: Path) -> dict[tuple[int, int, int], int]:
    """
    Parse a VOC labelmap file and return RGB-to-index mapping.

    Format: 'name : color (r, g, b) : parts : actions'

    Returns:
        Dictionary mapping (R, G, B) tuples to class indices.
    """
    colormap: dict[tuple[int, int, int], int] = {}
    index = 0
    with open(labelmap_path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # name : color : parts : actions
            parts = line.split(":")
            if len(parts) >= 2:
                color_str = parts[1].strip()
                if color_str:
                    try:
                        rgb = tuple(int(c.strip()) for c in color_str.split(","))
                        if len(rgb) == 3:
                            colormap[rgb] = index
                    except (ValueError, TypeError):
                        pass
            index += 1
    return colormap


def _load_voc_categories(root_path: Path) -> LabelCategories:
    """Load categories from VOC labelmap file or use defaults."""
    labelmap_path = root_path / VOC_LABELMAP_FILE
    if labelmap_path.exists():
        labels = _parse_voc_labelmap(labelmap_path)
        if labels:
            return LabelCategories(labels=tuple(labels))

    # Check for meta file
    meta_file = root_path / "dataset_meta.json"
    if meta_file.exists():
        import json

        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)
            labels = meta.get("labels", [])
            if labels:
                return LabelCategories(labels=tuple(labels))

    # Use default VOC labels
    return LabelCategories(labels=VOC_LABELS)


def _detect_voc_subsets(root_path: Path) -> dict[str, Path]:
    """
    Detect available subsets in a VOC dataset.

    Returns:
        Dictionary mapping subset names to their txt file paths.
    """
    subsets = {}
    imagesets_main = root_path / VOC_IMAGESETS_DIR / VOC_MAIN_DIR

    if imagesets_main.exists():
        for txt_file in imagesets_main.glob("*.txt"):
            subset_name = txt_file.stem
            # Skip label-specific files like 'aeroplane_train.txt'
            if "_" not in subset_name or subset_name in VOC_SUBSET_NAME_TO_ENUM:
                subsets[subset_name] = txt_file

    return subsets


def _detect_classification_label_files(
    root_path: Path,
    subset_names: set[str],
    categories: LabelCategories,
) -> dict[str, dict[str, Path]]:
    """Detect label-specific classification files in ImageSets/Main/.

    VOC classification datasets store per-label files with the naming
    convention ``<label>_<subset>.txt``.  Each line has the format
    ``image_id  1`` (present) or ``image_id -1`` (absent).

    Only files whose label part matches a known category label (excluding
    ``background``) are returned so that arbitrary files are not misinterpreted.

    Returns:
        Nested dict ``{subset_name: {label_name: path}}``.
    """
    imagesets_main = root_path / VOC_IMAGESETS_DIR / VOC_MAIN_DIR
    if not imagesets_main.exists():
        return {}

    # Build a set of valid foreground label names for fast lookup
    valid_labels = {lbl for lbl in categories.labels if lbl != "background"}

    result: dict[str, dict[str, Path]] = {}
    for txt_file in sorted(imagesets_main.glob("*.txt")):
        stem = txt_file.stem
        if "_" not in stem:
            continue  # not a label-specific file

        # Split on the last underscore so labels with underscores work
        label_part, subset_part = stem.rsplit("_", 1)

        if label_part not in valid_labels:
            logger.warning(
                "Skipping classification file %s: label '%s' not in known categories",
                txt_file,
                label_part,
            )
            continue
        if subset_part not in subset_names:
            logger.warning(
                "Skipping classification file %s: subset '%s' not in known subsets",
                txt_file,
                subset_part,
            )
            continue

        result.setdefault(subset_part, {})[label_part] = txt_file

    return result


def _parse_classification_labels(
    label_files: dict[str, Path],
    categories: LabelCategories,
) -> dict[str, list[int]]:
    """Parse label-specific classification files and return per-image label indices.

    Args:
        label_files: Mapping ``{label_name: file_path}`` for one subset.
        categories: The label categories (used to resolve indices).

    Returns:
        Mapping ``{image_id: sorted list of label indices with positive flag}``.
    """
    image_labels: dict[str, list[int]] = defaultdict(list)

    for label_name, file_path in label_files.items():
        try:
            label_idx = categories.labels.index(label_name)
        except ValueError:
            logger.warning(
                "Skipping classification label '%s': not found in categories",
                label_name,
            )
            continue

        with open(file_path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    logger.warning(
                        "Skipping malformed line in %s: expected at least 2 fields, got '%s'",
                        file_path,
                        line,
                    )
                    continue
                image_id = parts[0]
                try:
                    flag = int(parts[1])
                except ValueError:
                    logger.warning(
                        "Skipping line in %s: cannot parse flag as integer: '%s'",
                        file_path,
                        parts[1],
                    )
                    continue
                if flag == 1:
                    image_labels[image_id].append(label_idx)

    # Sort each label list for determinism
    for image_id, labels in image_labels.items():
        labels.sort()

    return dict(image_labels)


def _parse_subset_list(subset_file: Path) -> list[str]:
    """
    Parse a VOC ImageSets subset file.

    Returns:
        List of image IDs in the subset.
    """
    image_ids = []
    with open(subset_file, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            # VOC format can have 'image_id label' for classification
            # We only want the image_id
            parts = line.split()
            if parts:
                image_ids.append(parts[0])
    return image_ids


def _parse_voc_annotation(anno_path: Path, categories: LabelCategories) -> dict:
    """
    Parse a VOC XML annotation file.

    Returns:
        Dictionary with keys: width, height, bboxes, labels, difficult, truncated, occluded, pose
    """
    result = {
        "width": 0,
        "height": 0,
        "bboxes": [],
        "labels": [],
        "difficult": [],
        "truncated": [],
        "occluded": [],
        "pose": [],
    }

    if not anno_path.exists():
        return result

    try:
        tree = ElementTree.parse(anno_path)
        root = tree.getroot()

        # Parse size
        size_elem = root.find("size")
        if size_elem is not None:
            width_elem = size_elem.find("width")
            height_elem = size_elem.find("height")
            if width_elem is not None and width_elem.text:
                result["width"] = int(width_elem.text)
            if height_elem is not None and height_elem.text:
                result["height"] = int(height_elem.text)

        # Parse objects
        # Pre-check: is this a classification-only annotation (no bndbox anywhere)?
        obj_elems = root.findall("object")
        is_classification_only = all(obj.find("bndbox") is None for obj in obj_elems)

        for obj_elem in obj_elems:
            _parse_object_element(obj_elem, result, categories, is_classification_only)

    except ElementTree.ParseError as e:
        logger.warning("Failed to parse VOC annotation %s: %s", anno_path, e)

    return result


def _parse_object_element(
    obj_elem: Element,
    result: dict,
    categories: LabelCategories,
    is_classification_only: bool = False,
) -> None:
    """Parse a single object element from VOC XML.

    Objects without a bounding box are only included when the entire annotation
    is classification-only (no objects have bndbox).  In mixed annotations the
    bbox-less objects are skipped so that bboxes, labels and attribute arrays
    stay aligned.
    """
    # Get label name
    name_elem = obj_elem.find("name")
    if name_elem is None or not name_elem.text:
        return

    label_name = name_elem.text.strip()

    # Get label index from categories
    try:
        label_idx = categories.labels.index(label_name)
    except ValueError:
        logger.warning("Unknown label '%s' in VOC annotation, skipping", label_name)
        return

    # Parse bounding box
    bndbox = obj_elem.find("bndbox")
    if bndbox is not None:
        try:
            xmin = float(bndbox.find("xmin").text)
            ymin = float(bndbox.find("ymin").text)
            xmax = float(bndbox.find("xmax").text)
            ymax = float(bndbox.find("ymax").text)
        except (AttributeError, ValueError, TypeError) as e:
            logger.warning("Invalid bounding box in VOC annotation: %s", e)
            return

        result["bboxes"].append([xmin, ymin, xmax, ymax])
    elif not is_classification_only:
        # In mixed annotations, skip objects without bounding boxes
        # to keep bboxes/labels/attribute arrays aligned
        logger.debug("Skipping object '%s' without bndbox in detection annotation", label_name)
        return

    result["labels"].append(label_idx)

    # Parse attributes
    difficult_elem = obj_elem.find("difficult")
    result["difficult"].append(difficult_elem is not None and difficult_elem.text == "1")

    truncated_elem = obj_elem.find("truncated")
    result["truncated"].append(truncated_elem is not None and truncated_elem.text == "1")

    occluded_elem = obj_elem.find("occluded")
    result["occluded"].append(occluded_elem is not None and occluded_elem.text == "1")

    pose_elem = obj_elem.find("pose")
    result["pose"].append(
        pose_elem.text.strip()
        if (pose_elem is not None and pose_elem.text and pose_elem.text.strip())
        else "Unspecified"
    )


@dataclass(frozen=True)
class _VocMaskLoader:
    """Picklable callable that lazily loads a VOC segmentation mask on demand.

    Used in place of a locally-defined closure so that datasets containing this
    callable can be passed to ``torch.utils.data.DataLoader`` workers started
    with the ``spawn`` multiprocessing context, which requires every object
    reachable from the ``Dataset`` to be picklable. A closure defined inside a
    function is not picklable by the standard ``pickle`` module, whereas a
    module-level dataclass instance with simple (picklable) attributes is.

    Args:
        mask_path: Path to the mask PNG file.
        colormap: Optional RGB-to-index mapping. If provided, RGB masks will be
            converted to index masks.
    """

    mask_path: Path
    colormap: dict[tuple[int, int, int], int] | None = None

    def __call__(self) -> np.ndarray:
        """Load mask from file and convert to numpy array."""
        from PIL import Image as PILImage

        with PILImage.open(self.mask_path) as img:
            mask_rgb = np.array(img, dtype=np.uint8)

        # If no colormap or already indexed, return as-is
        if self.colormap is None or len(mask_rgb.shape) < 3:
            return mask_rgb

        # Convert RGB mask to index mask using colormap
        h, w = mask_rgb.shape[:2]
        index_mask = np.zeros((h, w), dtype=np.uint8)

        # Create a lookup from RGB tuples to indices
        for rgb, idx in self.colormap.items():
            # Find pixels matching this color
            mask = np.all(mask_rgb[:, :, :3] == np.array(rgb), axis=2)
            index_mask[mask] = idx

        return index_mask


def _create_mask_loader(mask_path: Path, colormap: dict[tuple[int, int, int], int] | None = None) -> Callable:
    """Create a lazy loader callable for a segmentation mask.

    Args:
        mask_path: Path to the mask PNG file
        colormap: Optional RGB-to-index mapping. If provided, RGB masks will be
            converted to index masks.
    """
    return _VocMaskLoader(mask_path, colormap)


@dataclass
class VocLoadContext:
    """Context for loading VOC samples, grouping related directory paths."""

    images_dir: Path
    annotations_dir: Path
    categories: LabelCategories
    segmentation_class_dir: Path | None = None
    segmentation_object_dir: Path | None = None
    colormap: dict[tuple[int, int, int], int] | None = None
    images_index: dict[str, Path] | None = None
    # Pre-built stem -> path lookup for ``images_dir`` (see
    # _build_image_index). When set, avoids re-globbing the directory
    # for every sample in _create_sample_from_annotation.


def _create_sample_from_annotation(
    image_id: str,
    ctx: VocLoadContext,
    subset_enum: Subset,
    classification_labels: list[int] | None = None,
) -> VocSample | None:
    """Create a VocSample from image ID and annotation.

    Args:
        image_id: Image stem identifier.
        ctx: Load context with paths and categories.
        subset_enum: Subset assignment for this sample.
        classification_labels: Optional list of label indices obtained from
            ImageSets/Main classification files. When the XML annotation does
            not contain any objects these are used as image-level labels.
    """
    # Find image file: prefer the pre-built index (O(1)) over re-globbing
    # the directory (O(files)) for every sample.
    image_path = ctx.images_index.get(image_id) if ctx.images_index is not None else None
    if image_path is None:
        image_path = _find_image_file(ctx.images_dir, image_id)
    if image_path is None:
        logger.warning("Image not found for ID '%s', skipping", image_id)
        return None

    # Parse annotation
    anno_path = ctx.annotations_dir / f"{image_id}.xml"
    annotation = _parse_voc_annotation(anno_path, ctx.categories)

    # Get image size from annotation or read from image
    height = annotation["height"]
    width = annotation["width"]
    if height == 0 or width == 0:
        height, width = _get_image_size(image_path)

    # Create arrays from XML annotations
    bboxes = np.array(annotation["bboxes"], dtype=np.float32) if annotation["bboxes"] else None
    labels = np.array(annotation["labels"], dtype=np.uint32) if annotation["labels"] else None
    difficult = np.array(annotation["difficult"], dtype=bool) if annotation["difficult"] else None
    truncated = np.array(annotation["truncated"], dtype=bool) if annotation["truncated"] else None
    occluded = np.array(annotation["occluded"], dtype=bool) if annotation["occluded"] else None
    pose = np.array(annotation["pose"], dtype=object) if annotation["pose"] else None

    # If no labels from XML annotations, use classification labels from
    # ImageSets/Main/<label>_<subset>.txt files (image-level classification).
    if labels is None and classification_labels:
        labels = np.array(classification_labels, dtype=np.uint32)

    # Create lazy mask loaders for segmentation masks
    class_mask_loader = _get_mask_loader(ctx.segmentation_class_dir, image_id, ctx.colormap)
    instance_mask_loader = _get_mask_loader(ctx.segmentation_object_dir, image_id, ctx.colormap)

    return VocSample(
        image=str(image_path),
        image_info=ImageInfo(height=height, width=width),
        bboxes=bboxes,
        labels=labels,
        difficult=difficult,
        truncated=truncated,
        occluded=occluded,
        pose=pose,
        class_mask=class_mask_loader,
        instance_mask=instance_mask_loader,
        subset=subset_enum,
    )


def _get_mask_loader(
    mask_dir: Path | None,
    image_id: str,
    colormap: dict[tuple[int, int, int], int] | None,
) -> Callable | None:
    """Get a mask loader for a segmentation mask if it exists."""
    if mask_dir is None:
        return None
    mask_path = mask_dir / f"{image_id}.png"
    if mask_path.exists():
        return _create_mask_loader(mask_path, colormap)
    return None


def _detect_segmentation_dir(root_path: Path, dir_name: str, label: str) -> Path | None:
    """Detect and log a segmentation directory if it exists."""
    seg_dir = root_path / dir_name
    if seg_dir.exists():
        logger.info("[VOC] Found segmentation %s masks at %s", label, seg_dir)
        return seg_dir
    return None


def _load_colormap_if_needed(
    root_path: Path,
    segmentation_class_dir: Path | None,
    segmentation_object_dir: Path | None,
) -> dict[tuple[int, int, int], int] | None:
    """Load colormap for RGB-to-index conversion if labelmap exists and segmentation is present."""
    labelmap_path = root_path / VOC_LABELMAP_FILE
    if not labelmap_path.exists() or (segmentation_class_dir is None and segmentation_object_dir is None):
        return None

    colormap = _parse_voc_labelmap_with_colors(labelmap_path)
    if colormap:
        logger.info("[VOC] Loaded colormap with %d colors for RGB-to-index conversion", len(colormap))
    return colormap


def _load_samples_from_images(ctx: VocLoadContext) -> list[VocSample]:
    """Load samples by scanning all images in the images directory."""
    samples = []
    logger.info("No ImageSets found, loading all images from %s", ctx.images_dir)
    image_files = list(find_images(str(ctx.images_dir)))
    for image_path in image_files:
        image_id = Path(image_path).stem
        sample = _create_sample_from_annotation(image_id, ctx, Subset.UNASSIGNED)
        if sample:
            samples.append(sample)
    return samples


def _load_samples_from_subsets(
    ctx: VocLoadContext,
    subsets: dict[str, Path],
    classification_label_files: dict[str, dict[str, Path]] | None = None,
) -> list[VocSample]:
    """Load samples from ImageSets subset files.

    Args:
        ctx: Load context with paths and categories.
        subsets: Mapping ``{subset_name: path}`` for each subset txt file.
        classification_label_files: Optional nested dict
            ``{subset_name: {label_name: path}}`` from
            :func:`_detect_classification_label_files`.
    """
    samples = []
    for subset_name, subset_file in subsets.items():
        subset_enum = VOC_SUBSET_NAME_TO_ENUM.get(subset_name, Subset.UNASSIGNED)
        image_ids = _parse_subset_list(subset_file)

        # Parse classification labels for this subset (if available)
        cls_labels_map: dict[str, list[int]] = {}
        if classification_label_files and subset_name in classification_label_files:
            cls_labels_map = _parse_classification_labels(
                classification_label_files[subset_name],
                ctx.categories,
            )

        logger.info("[VOC] Loading subset '%s' with %d images", subset_name, len(image_ids))

        for image_id in image_ids:
            sample = _create_sample_from_annotation(
                image_id,
                ctx,
                subset_enum,
                classification_labels=cls_labels_map.get(image_id),
            )
            if sample:
                samples.append(sample)
    return samples


def _load_voc_from_imagesets(root_path: Path, categories: LabelCategories) -> list[VocSample]:
    """Load VOC dataset using ImageSets structure."""
    images_dir = root_path / VOC_IMAGES_DIR
    annotations_dir = root_path / VOC_ANNOTATIONS_DIR

    if not images_dir.exists():
        logger.warning("Images directory not found: %s", images_dir)
        return []

    # Detect segmentation directories
    segmentation_class_dir = _detect_segmentation_dir(root_path, VOC_SEGMENTATION_CLASS_DIR, "class")
    segmentation_object_dir = _detect_segmentation_dir(root_path, VOC_SEGMENTATION_OBJECT_DIR, "object")

    # Load colormap for RGB-to-index conversion if labelmap exists
    colormap = _load_colormap_if_needed(root_path, segmentation_class_dir, segmentation_object_dir)

    # Create load context
    ctx = VocLoadContext(
        images_dir=images_dir,
        annotations_dir=annotations_dir,
        categories=categories,
        segmentation_class_dir=segmentation_class_dir,
        segmentation_object_dir=segmentation_object_dir,
        colormap=colormap,
        images_index=_build_image_index(images_dir),
    )

    subsets = _detect_voc_subsets(root_path)

    if subsets:
        # Detect classification label files
        cls_label_files = _detect_classification_label_files(root_path, set(subsets.keys()), categories)
        return _load_samples_from_subsets(ctx, subsets, cls_label_files)
    return _load_samples_from_images(ctx)


def _load_voc_simple(
    images_dir_path: str,
    annotations_dir_path: str,
    categories: LabelCategories,
) -> list[VocSample]:
    """Load VOC dataset from simple image and annotations directories."""
    samples = []

    images_dir = Path(images_dir_path)
    annotations_dir = Path(annotations_dir_path)

    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    image_files = list(find_images(str(images_dir)))
    # Reuse `_build_image_index` (rather than re-deriving the same mapping
    # inline) so tie-breaking for duplicate stems (e.g. "img0001.jpg" and
    # "img0001.png") stays consistent with `_load_voc_from_imagesets` and
    # with `_find_image_file`'s original "first match wins" behavior. A
    # plain `{stem: path for path in image_files}` dict comprehension would
    # instead silently keep the *last* match.
    # Pass the already-scanned `image_files` so _build_image_index doesn't
    # scan the directory a second time.
    images_index = _build_image_index(images_dir, image_paths=image_files)

    ctx = VocLoadContext(
        images_dir=images_dir,
        annotations_dir=annotations_dir,
        categories=categories,
        images_index=images_index,
    )

    for image_path in image_files:
        image_id = Path(image_path).stem
        sample = _create_sample_from_annotation(image_id, ctx, Subset.UNASSIGNED)
        if sample:
            samples.append(sample)

    return samples


# ============= Export helpers =============


def _create_voc_xml_annotation(
    sample: VocSample,
    image_filename: str,
    categories: LabelCategories,
) -> Element:
    """Create a VOC XML annotation element from a sample."""
    root = Element("annotation")

    # Folder (optional)
    folder_elem = Element("folder")
    folder_elem.text = VOC_IMAGES_DIR
    root.append(folder_elem)

    # Filename
    filename_elem = Element("filename")
    filename_elem.text = image_filename
    root.append(filename_elem)

    # Size
    size_elem = Element("size")
    width_elem = Element("width")
    width_elem.text = str(sample.image_info.width)
    size_elem.append(width_elem)
    height_elem = Element("height")
    height_elem.text = str(sample.image_info.height)
    size_elem.append(height_elem)
    depth_elem = Element("depth")
    depth_elem.text = "3"  # Assume RGB
    size_elem.append(depth_elem)
    root.append(size_elem)

    # Objects
    if sample.bboxes is not None and len(sample.bboxes) > 0:
        for i, bbox in enumerate(sample.bboxes):
            obj_elem = _create_object_element(sample, i, bbox, categories)
            root.append(obj_elem)
    elif sample.labels is not None and len(sample.labels) > 0:
        # Classification-only: labels without bounding boxes
        for i in range(len(sample.labels)):
            obj_elem = _create_object_element(sample, i, None, categories)
            root.append(obj_elem)

    return root


def _create_object_element(
    sample: VocSample,
    idx: int,
    bbox: np.ndarray | None,
    categories: LabelCategories,
) -> Element:
    """Create a single object element for VOC XML."""
    obj_elem = Element("object")

    # Name (label)
    name_elem = Element("name")
    name_elem.text = _get_label_name(sample, idx, categories)
    obj_elem.append(name_elem)

    # Pose
    pose_elem = Element("pose")
    if sample.pose is not None and idx < len(sample.pose):
        pose_elem.text = str(sample.pose[idx])
    else:
        pose_elem.text = "Unspecified"
    obj_elem.append(pose_elem)

    # Boolean attributes
    for attr_name, attr_array in (
        ("truncated", sample.truncated),
        ("difficult", sample.difficult),
        ("occluded", sample.occluded),
    ):
        elem = Element(attr_name)
        elem.text = "1" if attr_array is not None and idx < len(attr_array) and attr_array[idx] else "0"
        obj_elem.append(elem)

    # Bounding box (omitted for classification-only objects)
    if bbox is not None:
        obj_elem.append(_create_bndbox_element(bbox))

    return obj_elem


def _get_label_name(sample: VocSample, idx: int, categories: LabelCategories) -> str:
    """Get the label name for an object at the given index."""
    if sample.labels is None or idx >= len(sample.labels):
        return "unknown"
    label_idx = int(sample.labels[idx])
    if label_idx < len(categories.labels):
        return categories.labels[label_idx]
    return f"unknown_{label_idx}"


def _create_bndbox_element(bbox: np.ndarray) -> Element:
    """Create a bounding box XML element for VOC annotation."""
    bndbox_elem = Element("bndbox")
    for tag, value in zip(("xmin", "ymin", "xmax", "ymax"), bbox):
        child = Element(tag)
        child.text = str(int(value))
        bndbox_elem.append(child)
    return bndbox_elem


def _write_voc_xml(root: Element, output_path: Path) -> None:
    """Write VOC XML annotation to file with pretty formatting."""
    import xml.etree.ElementTree as ET  # nosec B405 - safe for writing XML, not parsing untrusted data

    rough_string = ET.tostring(root, encoding="unicode")

    # Simple indentation without minidom for security
    lines = []
    indent = 0
    for raw_token in rough_string.replace("><", ">\n<").split("\n"):
        token = raw_token.strip()
        if not token:
            continue
        if token.startswith("</"):
            indent -= 1
        lines.append("  " * indent + token)
        if not token.startswith("</") and not token.endswith("/>") and "</" not in token:
            indent += 1

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_labelmap(categories: LabelCategories, output_path: Path) -> None:
    """Write VOC labelmap file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# label:color_rgb:parts:actions\n")
        for label in categories.labels:
            f.write(f"{label}:::\n")


def _get_image_path_from_sample(sample: VocSample) -> Path | None:
    """Extract image path from a VocSample."""
    if hasattr(sample.image, "path"):
        return Path(sample.image.path)
    if isinstance(sample.image, str):
        return Path(sample.image)
    return None


def _get_image_id_from_sample(sample: VocSample, idx: int) -> str:
    """Generate a unique image ID from a sample."""
    image_path = _get_image_path_from_sample(sample)
    if image_path:
        return f"{image_path.stem}_{idx:06d}"
    return f"image_{idx:06d}"


def _process_sample_image(
    sample: VocSample,
    image_id: str,
    images_dir: Path,
    save_images: bool,
) -> str:
    """Process and optionally copy sample image, returning the filename."""
    image_path = _get_image_path_from_sample(sample)

    if save_images and image_path is not None and image_path.exists():
        dst_path = images_dir / f"{image_id}{image_path.suffix}"
        if image_path != dst_path:
            shutil.copy2(image_path, dst_path)
        return dst_path.name
    if image_path is not None:
        return f"{image_id}{image_path.suffix}"
    return f"{image_id}.jpg"


def _process_subset(
    sample_list: list[tuple[str, VocSample]],
    images_dir: Path,
    annotations_dir: Path,
    categories: LabelCategories,
    save_images: bool,
) -> list[str]:
    """Process all samples in a subset, saving images and annotations."""
    image_ids = []
    for image_id, sample in sample_list:
        image_ids.append(image_id)
        image_filename = _process_sample_image(sample, image_id, images_dir, save_images)
        xml_root = _create_voc_xml_annotation(sample, image_filename, categories)
        xml_path = annotations_dir / f"{image_id}.xml"
        _write_voc_xml(xml_root, xml_path)
    return image_ids


def _save_voc_dataset(
    dataset: Dataset[VocSample],
    root_dir: Path,
    save_images: bool = True,
) -> dict[str, Path]:
    """
    Save a VOC dataset to disk.

    Returns:
        Dictionary mapping logical names to written paths.
    """
    written_paths: dict[str, Path] = {}

    # Create directory structure
    images_dir = root_dir / VOC_IMAGES_DIR
    annotations_dir = root_dir / VOC_ANNOTATIONS_DIR
    imagesets_dir = root_dir / VOC_IMAGESETS_DIR / VOC_MAIN_DIR

    images_dir.mkdir(parents=True, exist_ok=True)
    annotations_dir.mkdir(parents=True, exist_ok=True)
    imagesets_dir.mkdir(parents=True, exist_ok=True)

    # Get categories from schema
    label_attr_info = dataset.schema.attributes.get("labels")
    categories = (
        label_attr_info.categories
        if label_attr_info and label_attr_info.categories
        else LabelCategories(labels=VOC_LABELS)
    )

    # Group samples by subset
    samples_by_subset: dict[Subset, list[tuple[str, VocSample]]] = defaultdict(list)
    for idx, sample in enumerate(dataset):
        image_id = _get_image_id_from_sample(sample, idx)
        samples_by_subset[sample.subset].append((image_id, sample))

    # Group by VOC subset name to handle multiple Subset enums mapping to the same name
    samples_by_voc_name: dict[str, list[tuple[str, VocSample]]] = defaultdict(list)
    for subset, sample_list in samples_by_subset.items():
        voc_name = SUBSET_TO_VOC_NAME.get(subset, "train")
        samples_by_voc_name[voc_name].extend(sample_list)

    # Process each VOC subset
    for subset_name, sample_list in samples_by_voc_name.items():
        subset_file = imagesets_dir / f"{subset_name}.txt"

        image_ids = _process_subset(sample_list, images_dir, annotations_dir, categories, save_images)

        # Write ImageSets file
        with open(subset_file, "w", encoding="utf-8") as f:
            for image_id in image_ids:
                f.write(f"{image_id}\n")

        written_paths[f"imageset_{subset_name}"] = subset_file
        logger.info("[VOC] Wrote subset '%s' with %d images", subset_name, len(image_ids))

    # Write labelmap
    labelmap_path = root_dir / VOC_LABELMAP_FILE
    _write_labelmap(categories, labelmap_path)
    written_paths["labelmap"] = labelmap_path

    written_paths["images_dir"] = images_dir
    written_paths["annotations_dir"] = annotations_dir

    return written_paths
