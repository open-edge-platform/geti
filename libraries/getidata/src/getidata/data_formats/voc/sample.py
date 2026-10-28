# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Sample class for Pascal VOC format datasets.
"""

from collections.abc import Callable

import numpy as np
import polars as pl

from getidata import LazyImage, Sample, register_sample
from getidata.categories import LabelCategories
from getidata.data_formats.semantics import DIFFICULT, OCCLUDED, POSE, TRUNCATED
from getidata.data_formats.voc.constants import VOC_LABELS
from getidata.fields import (
    ImageInfo,
    Subset,
    bbox_field,
    bool_field,
    image_info_field,
    image_path_field,
    label_field,
    mask_callable_field,
    string_field,
    subset_field,
)

# Semantic tags for mask fields
CLASS_MASK = "class_mask"
INSTANCE_MASK = "instance_mask"


@register_sample
class VocSample(Sample):
    """
    Sample class for Pascal VOC format datasets.

    Pascal VOC format stores object detection and segmentation annotations
    with bounding boxes in xyxy format (xmin, ymin, xmax, ymax) absolute coordinates,
    along with label names and optional attributes like difficult, truncated, occluded, and pose.

    Segmentation masks are loaded lazily from SegmentationClass/ and SegmentationObject/
    directories when accessed.
    """

    # Basic image information
    image: LazyImage = image_path_field()
    image_info: ImageInfo = image_info_field()

    # Object detection annotations - bboxes in xyxy format for VOC
    bboxes: np.ndarray | None = bbox_field(dtype=pl.Float32(), format="xyxy")
    labels: np.ndarray | None = label_field(dtype=pl.UInt32(), is_list=True)

    # VOC-specific annotation attributes
    difficult: np.ndarray | None = bool_field(is_list=True, semantic=DIFFICULT)
    truncated: np.ndarray | None = bool_field(is_list=True, semantic=TRUNCATED)
    occluded: np.ndarray | None = bool_field(is_list=True, semantic=OCCLUDED)
    pose: np.ndarray | None = string_field(is_list=True, semantic=POSE)

    # Segmentation masks (lazy loaded via callable)
    # Class segmentation mask: 2D array (H, W) with class indices as pixel values
    class_mask: Callable[[], np.ndarray] | None = mask_callable_field(dtype=pl.UInt8(), semantic=CLASS_MASK)
    # Instance segmentation mask: 2D array (H, W) with instance indices as pixel values
    # Shares the same MaskCategories with class_mask to avoid duplicate category definitions
    instance_mask: Callable[[], np.ndarray] | None = mask_callable_field(
        dtype=pl.UInt8(), semantic=INSTANCE_MASK, categories_from="class_mask"
    )

    # Dataset organization
    subset: Subset = subset_field()


class VocCategories(LabelCategories):
    """
    Categories for Pascal VOC datasets.

    Initializes VocCategories with either default VOC labels or a provided label list.
    If a custom list of labels is provided (e.g., loaded from a VOC labelmap file),
    the categories will use that list and preserve its order. Otherwise, it will
    fall back to the default VOC label order.
    """

    def __init__(self, labels: tuple[str, ...] | list[str] | None = None):
        # Initialize using provided labels or the default VOC labels
        provided = tuple(labels) if labels is not None else VOC_LABELS
        super().__init__(labels=provided)

    def get_foreground_labels(self) -> list[str]:
        """
        Get all labels except 'background'.

        Returns:
            List of label names excluding 'background'
        """
        return [label for label in self.labels if label != "background"]
