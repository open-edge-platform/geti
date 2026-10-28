# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Constants for Pascal VOC format support.
"""

from getidata.fields import Subset

# VOC directory structure
VOC_IMAGES_DIR = "JPEGImages"
VOC_ANNOTATIONS_DIR = "Annotations"
VOC_SEGMENTATION_CLASS_DIR = "SegmentationClass"
VOC_SEGMENTATION_OBJECT_DIR = "SegmentationObject"
VOC_IMAGESETS_DIR = "ImageSets"
VOC_MAIN_DIR = "Main"
VOC_SEGMENTATION_IMAGESETS_DIR = "Segmentation"

# VOC file extensions
VOC_IMAGE_EXT = ".jpg"
VOC_ANNOTATION_EXT = ".xml"
VOC_SEGMENTATION_EXT = ".png"

# VOC label map file
VOC_LABELMAP_FILE = "labelmap.txt"

# Default VOC labels with their colormap indices
VOC_LABELS: tuple[str, ...] = (
    "background",
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
)

# VOC poses
VOC_POSES: tuple[str, ...] = (
    "Unspecified",
    "Left",
    "Right",
    "Frontal",
    "Rear",
)

# VOC body parts (for layout task)
VOC_BODY_PARTS: tuple[str, ...] = (
    "head",
    "hand",
    "foot",
)

# VOC actions (for action task)
VOC_ACTIONS: tuple[str, ...] = (
    "other",
    "jumping",
    "phoning",
    "playinginstrument",
    "reading",
    "ridingbike",
    "ridinghorse",
    "running",
    "takingphoto",
    "usingcomputer",
    "walking",
)

# Mapping from VOC subset file names to Subset enum
VOC_SUBSET_NAME_TO_ENUM: dict[str, Subset] = {
    "train": Subset.TRAINING,
    "trainval": Subset.TRAINING,
    "val": Subset.VALIDATION,
    "test": Subset.TESTING,
}

# Mapping from Subset enum to VOC subset file names
SUBSET_TO_VOC_NAME: dict[Subset, str] = {
    Subset.TRAINING: "train",
    Subset.VALIDATION: "val",
    Subset.TESTING: "test",
    Subset.UNASSIGNED: "train",  # Default to train for unassigned
}
