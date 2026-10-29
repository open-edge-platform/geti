# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import numpy as np
import polars as pl

from getidata import LazyImage, Sample, register_sample
from getidata.fields import ImageInfo, Subset, bbox_field, image_info_field, image_path_field, label_field, subset_field


@register_sample
class YoloSample(Sample):
    """
    Sample class for YOLO format datasets.

    YOLO format stores object detection annotations with bounding boxes
    in cxcywh format (center_x, center_y, width, height) relative
    to image dimensions, with each box having a class label.
    """

    # Basic image information
    image: LazyImage = image_path_field()
    image_info: ImageInfo = image_info_field()

    # Object detection annotations
    bboxes: np.ndarray | None = bbox_field(dtype=pl.Float32(), format="cxcywh")
    labels: np.ndarray | None = label_field(dtype=pl.UInt8(), is_list=True)

    # Dataset organization
    subset: Subset = subset_field()
