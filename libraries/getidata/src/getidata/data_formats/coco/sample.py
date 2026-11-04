# Copyright (C) 2022-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import numpy as np
import polars as pl

from getidata import LazyImage, Sample, register_sample
from getidata.categories import LabelCategories
from getidata.data_formats.coco.constants import COCO_LABEL_TO_SUPER
from getidata.data_formats.semantics import AREAS, CAPTION_GROUP_IDS, IMAGE_ID, ISCROWD
from getidata.fields import (
    ImageInfo,
    Subset,
    bbox_field,
    bool_field,
    caption_field,
    image_info_field,
    image_path_field,
    keypoints_field,
    label_field,
    numeric_field,
    polygon_field,
    subset_field,
)


@register_sample
class CocoSample(Sample):
    # Basic image information
    image: LazyImage = image_path_field()
    image_info: ImageInfo = image_info_field()

    # Instance annotations (from instances_train/val)
    bboxes: np.ndarray | None = bbox_field(dtype=pl.Float32(), format="xywh")
    polygons: np.ndarray | None = polygon_field(dtype=pl.Float32())
    labels: np.ndarray | None = label_field(dtype=pl.UInt32(), is_list=True)
    areas: np.ndarray | None = numeric_field(dtype=pl.Float32(), is_list=True, semantic=AREAS)
    iscrowd: np.ndarray | None = bool_field(is_list=True, semantic=ISCROWD)

    # Keypoint annotations (from person_keypoints_train/val)
    keypoints: np.ndarray | None = keypoints_field(dtype=pl.Float32())

    # Caption annotations (from captions_train/val)
    captions: np.ndarray | None = caption_field(is_list=True)
    caption_group_ids: np.ndarray | None = numeric_field(dtype=pl.UInt32(), is_list=True, semantic=CAPTION_GROUP_IDS)

    # Dataset organization
    subset: Subset = subset_field()
    image_id: int | None = numeric_field(dtype=pl.Int32(), semantic=IMAGE_ID)


class CocoCategories(LabelCategories):
    # Unified mapping of label -> super-category (preserves COCO order)
    label_to_super: dict[str, str] = COCO_LABEL_TO_SUPER

    """
    Initializes CocoCategories with either default COCO labels or a provided label list.

    If a custom list of labels is provided (e.g., loaded from a COCO JSON file),
    the categories will use that list and preserve its order. Otherwise, it will
    fall back to the default COCO label order defined in COCO_LABEL_TO_SUPER.
    """

    def __init__(self, labels: tuple[str, ...] | list[str] | None = None):
        # Initialize using provided labels or the default mapping order
        provided = tuple(labels) if labels is not None else tuple(self.label_to_super.keys())
        super().__init__(labels=provided)

    def get_labels_by_super_category(self, super_category: str) -> list[str]:
        """
        Get all labels that belong to a specific super category.

        Args:
            super_category: The name of the super category

        Returns:
            List of label names (restricted to this instance's labels) that belong
            to the specified super category
        """
        allowed = set(self.labels)
        return [label for label, sc in self.label_to_super.items() if sc == super_category and label in allowed]
