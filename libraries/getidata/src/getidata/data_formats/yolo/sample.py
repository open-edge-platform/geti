# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import numpy as np
import polars as pl

from getidata import LazyImage, Sample, register_sample
from getidata.fields import (
    ImageInfo,
    Subset,
    bbox_field,
    image_info_field,
    image_path_field,
    label_field,
    polygon_field,
    subset_field,
)


@register_sample
class YoloClsSample(Sample):
    """
    Sample class for Ultralytics YOLO classification format datasets.

    The Ultralytics YOLO classification format follows the ImageNet-style
    folder layout: one directory per subset (train/val/test), each holding
    one subdirectory per class, with the images of that class stored directly
    inside it. There are no annotation files; the class is inferred from the
    folder that contains the image, so each image carries exactly one label.
    """

    # Basic image information
    image: LazyImage = image_path_field()
    image_info: ImageInfo = image_info_field()

    # Single class label per image
    label: int | None = label_field(dtype=pl.UInt16(), is_list=False)

    # Dataset organization
    subset: Subset = subset_field()


@register_sample
class YoloSegSample(Sample):
    """
    Sample class for Ultralytics YOLO instance segmentation format datasets.

    The Ultralytics YOLO segmentation format uses the same directory layout as the
    detection format (images/ and labels/ directories per split, class names in
    data.yaml). What differs is the content of the label files: each row holds a
    class index followed by the normalized (x, y) coordinates of one polygon with
    at least three points, so rows have a variable length of seven or more fields.

    Holes inside objects cannot be represented, as every instance is a single
    polygon.
    """

    # Basic image information
    image: LazyImage = image_path_field()
    image_info: ImageInfo = image_info_field()

    # Instance segmentation annotations
    polygons: np.ndarray | None = polygon_field(dtype=pl.Float32())
    labels: np.ndarray | None = label_field(dtype=pl.UInt16(), is_list=True)

    # Dataset organization
    subset: Subset = subset_field()


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
